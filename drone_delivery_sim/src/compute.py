"""
compute.py
==========
Models the real ONBOARD vs GROUND compute split and the link between them.

Why this exists
---------------
On the real drone, a tiny flight controller + a Raspberry Pi can only do so much,
and they talk to a separate ground computer (Andrey's laptop) over a radio link
that has latency, limited bandwidth and packet loss. Some work MUST be local
(the control loop can't wait for a round-trip); heavier work is offloaded to the
ground. This module makes that split real:

  * ONBOARD (low-latency, must be local): flight control, state estimation,
    reading the sensors, the down-camera ArUco detection + the precision PID loop,
    and the LiDAR safety reflex.
  * GROUND (heavier, latency-tolerant): dispatch ("tap a button"), mission/҂path
    planning, heavy front-camera & LiDAR map processing, logging, dashboards,
    video export.

`run_compute_split()` runs the mission with this split. With `processes=True` the
onboard and ground halves run in SEPARATE OS PROCESSES that exchange only
serialized messages through the simulated `Link` — so the split is real, not
cosmetic. `processes=False` runs the same message flow in one process (fast,
deterministic) for tests and CI.

A `ComputeBudget` models the Pi's limited compute: each onboard task costs some
milliseconds; if the per-tick total exceeds the budget (e.g. because a heavy task
was mis-assigned onboard) it is flagged — demonstrating WHY heavy work is offloaded.
"""

from __future__ import annotations
import multiprocessing as mp
import numpy as np

from config import CONFIG
from src.link import Link

# Simulated per-tick cost of each task (milliseconds) and where it runs.
ONBOARD_TASKS = {
    "flight_control": 0.4,
    "state_estimation": 0.8,
    "read_sensors": 0.6,
    "aruco_down_camera": 3.0,     # light classical CV a Pi can do
    "precision_pid": 0.3,
    "lidar_reflex": 0.9,
}
GROUND_TASKS = {
    "dispatch": 1.0,
    "path_planning": 12.0,
    "front_camera_mapping": 22.0,  # heavy -> must be on the ground
    "lidar_map_processing": 9.0,
    "logging": 1.0,
    "video_export": 40.0,
}

# Approximate message sizes (bytes).
TELEMETRY_BYTES = 200
DOWNSAMPLED_FRAME_BYTES = 8 * 1024      # a small JPEG thumbnail of a feed
FULL_FRAME_BYTES = 320 * 240 * 3        # a full RGB frame (won't fit at full rate)


class ComputeBudget:
    """Tracks the onboard per-tick compute budget and flags overflows."""

    def __init__(self, budget_ms):
        self.budget_ms = budget_ms
        self.max_used_ms = 0.0
        self.overflows = 0
        self.samples = 0

    def tick(self, used_ms):
        self.samples += 1
        self.max_used_ms = max(self.max_used_ms, used_ms)
        over = used_ms > self.budget_ms
        if over:
            self.overflows += 1
        return over

    def as_dict(self):
        return {"budget_ms": self.budget_ms, "max_used_ms": round(self.max_used_ms, 2),
                "overflows": self.overflows, "samples": self.samples}


def onboard_tick_cost_ms(mislocate_heavy=False):
    cost = sum(ONBOARD_TASKS.values())
    if mislocate_heavy:                 # someone wrongly ran a ground task onboard
        cost += GROUND_TASKS["front_camera_mapping"]
    return cost


def _compact_telemetry(m):
    t = m.drone.get_telemetry()
    return {"t": round(m.t, 2), "state": m.state.name,
            "pos": [round(float(x), 2) for x in t["position"]],
            "battery": round(t["battery_pct"], 1)}


# --------------------------------------------------------------------------- #
#  Single-process mode (deterministic; used by tests)                         #
# --------------------------------------------------------------------------- #
def _run_single(config, seed, stream_full_res, mislocate_heavy, sensor_every=5):
    from src.mission import Mission
    rng = np.random.default_rng((seed or config.seed) + 4242)
    up = Link(config.link_latency_ms, config.link_bandwidth_kbps, config.link_packet_loss, rng)
    budget = ComputeBudget(config.onboard_budget_ms_per_tick)
    ground_received = {"telemetry": 0, "frames": 0}

    m = Mission(config=config, seed=seed)

    def on_step(mission):
        t = mission.t
        budget.tick(onboard_tick_cost_ms(mislocate_heavy))            # onboard compute
        up.send(("telemetry", _compact_telemetry(mission)), TELEMETRY_BYTES, t)  # uplink
        if mission.step_count % sensor_every == 0:                    # a sensor frame
            size = FULL_FRAME_BYTES if stream_full_res else DOWNSAMPLED_FRAME_BYTES
            up.send(("frame", mission.step_count), size, t)
        for kind, _payload in up.poll(t):                            # ground consumes
            ground_received["telemetry" if kind == "telemetry" else "frames"] += 1

    m.run(on_step=on_step)
    up.poll(m.t + config.link_latency_ms / 1000.0 + 0.1)        # drain final in-flight msgs
    return {
        "metrics": m.metrics, "processes": False,
        "link": up.stats.as_dict(), "budget": budget.as_dict(),
        "ground_received": ground_received,
        "task_location": {"onboard": list(ONBOARD_TASKS), "ground": list(GROUND_TASKS)},
    }


# --------------------------------------------------------------------------- #
#  Two-process mode (real OS processes over a Link)                           #
# --------------------------------------------------------------------------- #
def _onboard_process(q_up, q_down, config, seed, stream_full_res, mislocate_heavy, sensor_every=5):
    """Runs on the 'drone'. Streams telemetry/frames up; obeys an abort downlink."""
    from src.mission import Mission, MissionState
    budget = ComputeBudget(config.onboard_budget_ms_per_tick)
    m = Mission(config=config, seed=seed)

    def on_step(mission):
        budget.tick(onboard_tick_cost_ms(mislocate_heavy))
        # Every message is (sent_sim_t, size_bytes, payload) — the ground applies
        # the Link model in sim time.
        q_up.put((mission.t, TELEMETRY_BYTES, ("telemetry", _compact_telemetry(mission))))
        if mission.step_count % sensor_every == 0:
            size = FULL_FRAME_BYTES if stream_full_res else DOWNSAMPLED_FRAME_BYTES
            q_up.put((mission.t, size, ("frame", mission.step_count)))
        if not q_down.empty():
            try:
                if q_down.get_nowait() == "abort":
                    mission._transition(MissionState.ASCEND, "ground abort")
            except Exception:
                pass

    m.run(on_step=on_step)
    q_up.put((m.t, TELEMETRY_BYTES, ("done", {"metrics": m.metrics, "budget": budget.as_dict()})))


def _run_multiprocess(config, seed, stream_full_res, mislocate_heavy, timeout_s=60):
    # Use the platform default start method (fork on Linux, spawn on macOS).
    q_up = mp.Queue()
    q_down = mp.Queue()
    proc = mp.Process(target=_onboard_process,
                    args=(q_up, q_down, config, seed, stream_full_res, mislocate_heavy))
    proc.start()

    # Ground station: owns the uplink Link, consumes messages, logs.
    rng = np.random.default_rng((seed or config.seed) + 4242)
    up = Link(config.link_latency_ms, config.link_bandwidth_kbps, config.link_packet_loss, rng)
    ground_received = {"telemetry": 0, "frames": 0}
    result = {"metrics": None, "budget": None}
    latest_t = 0.0
    import queue as _q
    while True:
        try:
            sent_t, size, payload = q_up.get(timeout=timeout_s)
        except _q.Empty:
            break
        latest_t = max(latest_t, sent_t)
        kind = payload[0]
        if kind == "done":
            result["metrics"] = payload[1]["metrics"]
            result["budget"] = payload[1]["budget"]
            for k, _p in up.poll(latest_t + config.link_latency_ms / 1000.0 + 0.1):
                ground_received["telemetry" if k == "telemetry" else "frames"] += 1
            break
        up.send(payload, size, sent_t)
        for k, _p in up.poll(latest_t):
            ground_received["telemetry" if k == "telemetry" else "frames"] += 1
    proc.join(timeout=10)
    if proc.is_alive():
        proc.terminate()
    return {
        "metrics": result["metrics"], "processes": True,
        "link": up.stats.as_dict(), "budget": result["budget"],
        "ground_received": ground_received,
        "task_location": {"onboard": list(ONBOARD_TASKS), "ground": list(GROUND_TASKS)},
    }


def run_compute_split(config=CONFIG, seed=None, processes=True, stream_full_res=False,
                    mislocate_heavy=False):
    """
    Run a mission with the onboard/ground compute split + simulated link.

    processes        : True = real two-process split; False = single-process (fast).
    stream_full_res  : try to stream FULL-res frames uplink (exceeds bandwidth ->
                    the link drops them, demonstrating why we down-sample).
    mislocate_heavy  : (mis)assign a heavy ground task onboard -> budget overflow.
    """
    if processes:
        try:
            return _run_multiprocess(config, seed, stream_full_res, mislocate_heavy)
        except Exception as exc:
            print(f"[compute] multiprocessing unavailable ({exc}); using single-process")
    return _run_single(config, seed, stream_full_res, mislocate_heavy)
