"""
multifeed.py
============
Composes the multiple live feeds into ONE view and exports a combined video:

  * 3rd-person (chase) view of the drone in the 3D world, with the LiDAR hits
    painted RED on the model (exactly "where the LiDAR is hitting");
  * the front-facing camera;
  * the downward camera with the ArUco detection overlay (during the precision
    phases);
  * a top-down LiDAR "radar" mini-map;
  * a telemetry strip (state, altitude, link + compute split status, reflex).

Feeds are rendered with whatever world backend is active (PyBullet TinyRenderer on
Andrey's Mac; the matplotlib projector in the no-PyBullet fallback).
"""

from __future__ import annotations
import os
import time
import numpy as np
import cv2

from config import CONFIG


def _label(img, text, color=(255, 255, 255)):
    cv2.rectangle(img, (0, 0), (len(text) * 9 + 10, 22), (0, 0, 0), -1)
    cv2.putText(img, text, (5, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return img


def _placeholder(w, h, text):
    img = np.full((h, w, 3), 40, np.uint8)
    cv2.putText(img, text, (int(w * 0.12), h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (200, 200, 200), 1, cv2.LINE_AA)
    return img


def _lidar_radar(scan, size=200, rng_max=12.0):
    """Top-down mini radar: LiDAR hits as red dots around the drone (forward = up)."""
    img = np.full((size, size, 3), 25, np.uint8)
    c = size // 2
    for r in (size // 6, size // 3, size // 2 - 4):
        cv2.circle(img, (c, c), r, (60, 60, 60), 1)
    cv2.line(img, (c, c), (c, 8), (90, 90, 90), 1)
    yaw = scan["yaw"]
    cyaw, syaw = np.cos(-yaw + np.pi / 2), np.sin(-yaw + np.pi / 2)
    for d, dirv, hit in zip(scan["distances"], scan["directions"], scan["hit"]):
        if not hit:
            continue
        # bearing of the ray relative to drone heading, projected to top-down
        bearing = np.arctan2(dirv[1], dirv[0]) - yaw
        rr = min(d, rng_max) / rng_max * (size // 2 - 6)
        px = int(c + rr * np.sin(bearing))
        py = int(c - rr * np.cos(bearing))
        col = (0, 0, 255) if d < 3 else (0, 165, 255) if d < 6 else (0, 255, 0)
        cv2.circle(img, (px, py), 2, col, -1)
    cv2.circle(img, (c, c), 4, (255, 255, 255), -1)
    return _label(img, "LiDAR radar")


def compose(down, vis, front, chase, scan, telem_lines, width=1120, height=700):
    from src.vision import draw_detection
    canvas = np.full((height, width, 3), 18, np.uint8)

    chase_r = cv2.resize(chase, (620, 440))
    canvas[10:450, 10:630] = _label(chase_r, "3rd-person + LiDAR (red)")

    front_r = cv2.resize(front, (320, 240))
    canvas[10:250, 650:970] = _label(front_r, "front camera")

    if down is not None:
        shown = draw_detection(down, vis)
        down_r = cv2.resize(shown, (320, 240))
        _label(down_r, "down cam + ArUco")
    else:
        down_r = _placeholder(320, 240, "down cam: standby")
    canvas[260:500, 650:970] = down_r

    radar = _lidar_radar(scan)
    canvas[470:670, 10:210] = radar

    # telemetry strip
    x0, y0 = 230, 480
    cv2.rectangle(canvas, (x0, y0), (width - 10, height - 10), (35, 35, 40), -1)
    cv2.putText(canvas, "TELEMETRY", (x0 + 12, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 1, cv2.LINE_AA)
    for i, line in enumerate(telem_lines):
        cv2.putText(canvas, line, (x0 + 12, y0 + 52 + i * 24), cv2.FONT_HERSHEY_SIMPLEX,
                    0.52, (210, 220, 230), 1, cv2.LINE_AA)
    return canvas


def compose_frame(mission, world, config=CONFIG):
    """Render and compose ONE multi-feed frame (chase+front+down+radar+telemetry)."""
    scan = world.lidar_scan()
    front = world.front_camera()
    chase = world.chase_camera(lidar_points=scan["points"])
    tel = mission.drone.get_telemetry()
    vel = tel["velocity"]
    gnd = float(np.hypot(vel[0], vel[1]))
    dist_goal = float(np.hypot(mission.drone.pos[0] - mission.marker_world[0],
                            mission.drone.pos[1] - mission.marker_world[1]))
    lines = [
        f"state: {mission.state.name}",
        f"t: {mission.t:5.1f}s   alt: {tel['position'][2]:4.1f} m",
        f"SPEED: {gnd:4.2f} m/s  (vert {vel[2]:+4.2f})   to marker: {dist_goal:4.1f} m",
        f"avoidance: {'STEERING' if mission._reflex_active else 'clear'}"
        f"   LiDAR min: {scan['min_distance']:4.1f} m",
        f"onboard: control+ArUco+reflex   ground: planning+logging",
        f"link: {config.link_latency_ms:.0f}ms  {config.link_bandwidth_kbps:.0f}kbps"
        f"  loss {config.link_packet_loss*100:.0f}%",
    ]
    return compose(mission.last_image, mission.last_vision, front, chase, scan, lines)


def run_multifeed(config=CONFIG, seed=None, out_dir=None, max_frames=70, sample_every=18):
    """Run a mission and export a combined multi-feed video. Returns (path, metrics)."""
    import imageio.v2 as imageio
    from src.mission import Mission

    out_dir = out_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), config.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    m = Mission(config=config, seed=seed)
    if m.world is None:
        raise RuntimeError("multifeed needs the 3D world (config.enable_world=True)")
    world = m.world
    frames = []

    def on_step(mission):
        if mission.step_count % sample_every != 0 or len(frames) >= max_frames:
            return
        frames.append(compose_frame(mission, world, config))

    m.run(on_step=on_step)

    return _write_multifeed(frames, out_dir), m.metrics


def _write_multifeed(frames, out_dir, fps=8):
    """Write composed BGR frames to outputs/multifeed_demo.mp4 (GIF fallback)."""
    import imageio.v2 as imageio
    path = os.path.join(out_dir, "multifeed_demo.mp4")
    try:
        with imageio.get_writer(path, fps=fps, codec="libx264", quality=7) as w:
            for fr in frames:
                w.append_data(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    except Exception as exc:
        path = os.path.join(out_dir, "multifeed_demo.gif")
        print(f"  (MP4 failed: {str(exc).splitlines()[0]}; writing GIF)")
        imageio.mimsave(path, [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames], fps=6)
    return path


def run_multifeed_live(config=CONFIG, seed=None, speed=None, save=True, out_dir=None,
                    max_save=320):
    """
    Run a mission and show the combined multi-feed LIVE in a window, paced to REAL
    TIME (so 1 simulated second takes 1 wall-clock second / `speed`), and also save
    the video. This is the live equivalent of run_multifeed(). Returns (path, metrics).
    """
    import matplotlib.pyplot as plt
    from src.mission import Mission

    speed = config.live_speed if speed is None else float(speed)
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), config.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    m = Mission(config=config, seed=seed)
    if m.world is None:
        raise RuntimeError("multifeed needs the 3D world (config.enable_world=True)")
    world = m.world

    fig, ax = plt.subplots(figsize=(11.2, 7.0))
    ax.axis("off")
    fig.tight_layout()
    interval = 1.0 / max(config.live_update_hz, 1e-3)     # min SIM seconds between redraws
    st = {"t0": None, "last": -1e9, "im": None}
    saved = []

    def on_step(mi):
        if st["t0"] is None:
            st["t0"] = time.time()
        # Redraw the window at the configured cadence (in sim time).
        if mi.t - st["last"] >= interval or mi.done:
            st["last"] = mi.t
            frame = compose_frame(mi, world, config)
            if save and len(saved) < max_save:
                saved.append(frame)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if st["im"] is None:
                st["im"] = ax.imshow(rgb)
            else:
                st["im"].set_data(rgb)
            ax.set_title(f"LIVE multi-feed  —  t={mi.t:5.1f}s   x{speed:g} speed   "
                        f"{mi.state.name}", fontsize=11)
            try:
                fig.canvas.draw_idle(); plt.pause(0.001)
            except Exception:
                pass
        # Real-time pacing: never run faster than `speed`x wall-clock time.
        target = st["t0"] + mi.t / max(speed, 1e-6)
        lag = target - time.time()
        if lag > 0:
            time.sleep(min(lag, 0.5))

    plt.show(block=False)
    m.run(on_step=on_step)

    path = None
    if save and saved:
        print("\nSaving multi-feed video...")
        path = _write_multifeed(saved, out_dir, fps=max(6, int(config.live_update_hz)))
    return path, m.metrics
