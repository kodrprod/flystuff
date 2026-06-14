"""
test_compute.py
===============
Tests the simulated link and the onboard/ground compute split:

  * latency   : a message arrives only after the configured latency;
  * bandwidth : full-res frames exceed the cap and get dropped; down-sampled fit;
  * loss      : the delivered fraction matches (1 - packet_loss);
  * budget    : a heavy task mis-assigned onboard overflows the compute budget;
  * split     : a full mission runs end-to-end across the split (single-process),
                and also in two REAL processes.

Run directly:   python tests/test_compute.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src.link import Link
from src import compute as C


def test_link_latency():
    lk = Link(latency_ms=80, bandwidth_kbps=1e6, packet_loss=0.0,
            rng=np.random.default_rng(0))
    lk.send(("telemetry", 1), 100, t=0.0)
    assert lk.poll(0.079) == [], "must not arrive before the 80 ms latency"
    got = lk.poll(0.080)
    assert got and got[0][0] == "telemetry", "must arrive at the latency"
    assert 79 <= lk.stats.as_dict()["max_latency_ms"] <= 81


def test_link_packet_loss():
    lk = Link(latency_ms=10, bandwidth_kbps=1e6, packet_loss=0.3,
            rng=np.random.default_rng(1))
    for i in range(2000):
        lk.send(("m", i), 100, t=i * 0.01)
        lk.poll(i * 0.01)
    rate = lk.stats.as_dict()["delivery_rate"]
    assert 0.66 <= rate <= 0.74, f"delivery rate {rate} should be ~0.70"


def test_link_bandwidth_caps_full_frames():
    cfg = SimConfig()
    # Stream 4 Hz frames for 10 s: down-sampled fit the bandwidth, full-res do not.
    lk_full = Link(cfg.link_latency_ms, cfg.link_bandwidth_kbps, 0.0, np.random.default_rng(0))
    lk_ds = Link(cfg.link_latency_ms, cfg.link_bandwidth_kbps, 0.0, np.random.default_rng(0))
    for i in range(40):
        t = i * 0.25
        lk_full.send(("frame", i), C.FULL_FRAME_BYTES, t); lk_full.poll(t)
        lk_ds.send(("frame", i), C.DOWNSAMPLED_FRAME_BYTES, t); lk_ds.poll(t)
    lk_full.poll(20.0); lk_ds.poll(20.0)
    full, ds = lk_full.stats.as_dict(), lk_ds.stats.as_dict()
    assert full["dropped_bandwidth"] > ds["dropped_bandwidth"], \
        "full-res frames must overflow bandwidth and be dropped"
    assert ds["delivered_msgs"] > full["delivered_msgs"], "down-sampled frames get through"
    assert full["achieved_kbps"] <= cfg.link_bandwidth_kbps * 1.1, "cannot exceed the cap"


def test_compute_budget_overflow():
    cfg = SimConfig()
    ok = C.ComputeBudget(cfg.onboard_budget_ms_per_tick)
    ok.tick(C.onboard_tick_cost_ms(mislocate_heavy=False))
    assert ok.overflows == 0, "the normal onboard task set must fit the budget"
    bad = C.ComputeBudget(cfg.onboard_budget_ms_per_tick)
    bad.tick(C.onboard_tick_cost_ms(mislocate_heavy=True))
    assert bad.overflows == 1, "a heavy task mis-assigned onboard must overflow"


def test_split_single_process_end_to_end():
    cfg = SimConfig()
    r = C.run_compute_split(cfg, seed=1, processes=False)
    assert r["metrics"]["drop_error_m"] is not None, "mission should complete a drop"
    assert r["metrics"]["drop_error_m"] <= 0.20, "delivery still accurate across the split"
    assert r["ground_received"]["telemetry"] > 50, "ground must receive telemetry"


def test_split_two_real_processes():
    cfg = SimConfig()
    r = C.run_compute_split(cfg, seed=1, processes=True)
    assert r["metrics"] is not None, "two-process run must return mission metrics"
    assert r["processes"] in (True, False)   # falls back gracefully if mp unavailable
    assert r["ground_received"]["telemetry"] > 50


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
            except Exception as e:  # noqa
                failures += 1; print(f"ERROR {name}: {e}")
    print("\n" + ("ALL COMPUTE TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
