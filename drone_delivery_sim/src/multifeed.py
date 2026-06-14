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
        scan = world.lidar_scan()
        front = world.front_camera()
        chase = world.chase_camera(lidar_points=scan["points"])
        tel = mission.drone.get_telemetry()
        lines = [
            f"state: {mission.state.name}",
            f"t: {mission.t:5.1f}s   alt: {tel['position'][2]:4.1f} m",
            f"reflex: {'ACTIVE (holding)' if mission._reflex_active else 'clear'}"
            f"   LiDAR min: {scan['min_distance']:4.1f} m",
            f"onboard: control+ArUco+reflex   ground: planning+logging",
            f"link: {config.link_latency_ms:.0f}ms  {config.link_bandwidth_kbps:.0f}kbps"
            f"  loss {config.link_packet_loss*100:.0f}%",
        ]
        frames.append(compose(mission.last_image, mission.last_vision, front, chase, scan, lines))

    m.run(on_step=on_step)

    path = os.path.join(out_dir, "multifeed_demo.mp4")
    try:
        with imageio.get_writer(path, fps=8, codec="libx264", quality=7) as w:
            for fr in frames:
                w.append_data(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    except Exception as exc:
        path = os.path.join(out_dir, "multifeed_demo.gif")
        print(f"  (MP4 failed: {str(exc).splitlines()[0]}; writing GIF)")
        imageio.mimsave(path, [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames], fps=6)
    return path, m.metrics
