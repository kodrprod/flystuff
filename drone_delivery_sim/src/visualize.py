"""
visualize.py
============
The live dashboard and the video/GIF exporter.

The dashboard has four panels:
  * top-down map  : home, the building/balcony, the marker and the flight path
  * side view     : altitude vs East distance (shows the balcony at its height)
  * camera view   : the live synthetic camera frame with the detected marker drawn
  * telemetry     : current state, altitude, height-above-marker, offset, battery, wind

It works two ways:
  * LIVE   : an animated window while the mission flies (main.py default).
  * EXPORT : re-renders the logged frames to an MP4 (falls back to GIF) with no
             window needed -- so it also works on a headless machine / CI.

Backend handling for macOS is done in main.py BEFORE pyplot is imported.
"""

from __future__ import annotations
import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from config import CONFIG
from src.vision import draw_detection

_STATE_COLOR = {
    "CRUISE_TO_WAYPOINT": "#2b8cbe", "CLIMB_TO_BALCONY_ALT": "#2b8cbe",
    "SEARCH_MARKER": "#d95f0e", "PRECISION_ALIGN": "#fec44f",
    "DESCEND": "#31a354", "DROP": "#e34a33", "ASCEND": "#756bb1",
    "RETURN_HOME": "#2b8cbe", "LAND": "#636363",
}


class Dashboard:
    """A reusable 4-panel figure that can be updated frame by frame."""

    def __init__(self, config=CONFIG, plan=None, use_agg=False):
        self.cfg = config
        self.plan = plan
        if use_agg:
            # A standalone Agg figure: reliable pixel export on ANY display backend.
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            self.fig = Figure(figsize=(12.5, 6.6), dpi=90)
            FigureCanvasAgg(self.fig)
        else:
            self.fig = plt.figure(figsize=(12.5, 6.6))
        gs = self.fig.add_gridspec(2, 2, width_ratios=[1.15, 1.0],
                                height_ratios=[1.0, 1.0],
                                hspace=0.32, wspace=0.22,
                                left=0.06, right=0.975, top=0.92, bottom=0.08)
        self.ax_top = self.fig.add_subplot(gs[0, 0])
        self.ax_side = self.fig.add_subplot(gs[1, 0])
        self.ax_cam = self.fig.add_subplot(gs[0, 1])
        self.ax_info = self.fig.add_subplot(gs[1, 1])
        self.fig.suptitle("Autonomous Snack-Delivery Drone — Mission Dashboard",
                        fontsize=13, fontweight="bold")

    # ------------------------------------------------------------------ #
    def update(self, view: dict):
        cfg = self.cfg
        tE, tN = cfg.target_east_m, cfg.target_north_m
        bh = cfg.balcony_height_m
        mE, mN = cfg.marker_east_m, cfg.marker_north_m
        traj = view["traj"]

        # ---------------- Top-down map ----------------
        ax = self.ax_top
        ax.clear()
        ax.set_title("Top-down map (East–North)", fontsize=10)
        ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)")
        # Balcony footprint.
        ax.add_patch(Rectangle((tE - cfg.balcony_width_m / 2, tN - cfg.balcony_depth_m / 2),
                            cfg.balcony_width_m, cfg.balcony_depth_m,
                            facecolor="#fde0dd", edgecolor="#c51b8a", lw=1.2, zorder=2))
        ax.plot(0, 0, "ks", ms=9, zorder=5); ax.annotate("HOME", (0, 0),
                textcoords="offset points", xytext=(6, 6), fontsize=8)
        ax.plot(mE, mN, "x", color="#c51b8a", ms=11, mew=2.5, zorder=6)
        ax.annotate("marker", (mE, mN), textcoords="offset points", xytext=(6, -12), fontsize=8)
        # Planned obstacle-avoiding route (dashed) the drone follows.
        for key, col, lbl in (("cruise_path", "#31a354", "planned route"),
                            ("return_path", "#9e9ac8", None)):
            path = view.get(key)
            if path is not None and len(path) > 1:
                pp = np.array([np.asarray(q)[:2] for q in path])
                ax.plot(pp[:, 0], pp[:, 1], "--", color=col, lw=1.5, zorder=2.5,
                        dashes=(4, 3), label=lbl)
                ax.plot(pp[1:-1, 0], pp[1:-1, 1], ".", color=col, ms=7, zorder=2.6)
        if len(traj) > 1:
            t = np.array(traj)
            ax.plot(t[:, 0], t[:, 1], "-", color="#3182bd", lw=1.4, zorder=3,
                    label="flown")
        p = view["pos"]
        ax.plot(p[0], p[1], "o", color=_STATE_COLOR.get(view["state"], "#000"),
                ms=10, zorder=7, markeredgecolor="k")
        home = view.get("home_xy")
        if home is not None:
            ax.plot(home[0], home[1], "ks", ms=7, zorder=5)
        # Fit the view to everything that matters (home may be far from the marker).
        xs = [0, tE, p[0]] + ([home[0]] if home is not None else [])
        ys = [0, tN, p[1]] + ([home[1]] if home is not None else [])
        for key in ("cruise_path", "return_path"):
            for q in (view.get(key) or []):
                xs.append(np.asarray(q)[0]); ys.append(np.asarray(q)[1])
        ax.set_xlim(min(xs) - 6, max(xs) + 8); ax.set_ylim(min(ys) - 6, max(ys) + 8)
        ax.set_aspect("equal", adjustable="box")
        ax.legend(loc="upper left", fontsize=7, framealpha=0.7)
        ax.grid(True, alpha=0.3)

        # ---------------- Side view ----------------
        ax = self.ax_side
        ax.clear()
        ax.set_title("Side view (altitude vs East)", fontsize=10)
        ax.set_xlabel("East (m)"); ax.set_ylabel("Altitude (m)")
        ax.axhspan(-1, 0, facecolor="#d9d9d9", zorder=1)  # ground
        # Building block up to the balcony height + the balcony platform.
        ax.add_patch(Rectangle((tE - 1.2, 0), 2.4, bh, facecolor="#bdbdbd",
                            edgecolor="#737373", zorder=2))
        ax.plot([tE - cfg.balcony_width_m / 2, tE + cfg.balcony_width_m / 2], [bh, bh],
                color="#c51b8a", lw=3, zorder=4)
        ax.plot(mE, bh, "x", color="#c51b8a", ms=10, mew=2.5, zorder=5)
        if len(traj) > 1:
            t = np.array(traj)
            ax.plot(t[:, 0], t[:, 2], "-", color="#3182bd", lw=1.4, zorder=3)
        ax.plot(p[0], p[2], "o", color=_STATE_COLOR.get(view["state"], "#000"),
                ms=10, zorder=6, markeredgecolor="k")
        xlo = min(-6, p[0] - 4, (view["home_xy"][0] - 4) if view.get("home_xy") is not None else -6)
        ax.set_xlim(xlo, max(tE + 8, p[0] + 4))
        nav_alt = view.get("nav_alt") or cfg.return_altitude_m
        ax.set_ylim(-1, max(cfg.return_altitude_m + 2, bh + 6, nav_alt + 2))
        ax.grid(True, alpha=0.3)

        # ---------------- Camera view ----------------
        ax = self.ax_cam
        ax.clear()
        ax.set_title("Downward camera + ArUco detection", fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
        img = view["image"]
        if img is not None:
            shown = draw_detection(img, view["vis"])
            ax.imshow(cv2.cvtColor(shown, cv2.COLOR_BGR2RGB))
        else:
            ph = np.full((cfg.image_height, cfg.image_width, 3), 40, np.uint8)
            ax.imshow(ph)
            ax.text(0.5, 0.5, "VISION STANDBY\n(GPS phase)", color="w",
                    ha="center", va="center", transform=ax.transAxes, fontsize=12)

        # ---------------- Telemetry ----------------
        ax = self.ax_info
        ax.clear(); ax.axis("off")
        v = view["vis"]
        off = (None if not v["target_found"]
            else np.hypot(v["offset_east"], v["offset_north"]))
        wind = view["wind"]
        vel = np.asarray(view.get("velocity", np.zeros(3)))
        gnd_speed = float(np.hypot(vel[0], vel[1]))
        v_speed = float(vel[2])
        # Distance to the active goal (marker on the way out, home on the way back).
        goal = (view.get("home_xy") if view["state"] in ("RETURN_HOME", "LAND")
                else view.get("marker_xy"))
        dist_goal = (None if goal is None
                    else float(np.hypot(p[0] - goal[0], p[1] - goal[1])))
        climb = "▲ climb" if v_speed > 0.15 else "▼ descend" if v_speed < -0.15 else "— hold"
        avoiding = view.get("reflex", False)
        lines = [
            ("STATE", view["state"]),
            ("mission time", f"{view['t']:5.1f} s"),
            ("SPEED (ground)", f"{gnd_speed:4.2f} m/s"),
            ("  vertical", f"{v_speed:+4.2f} m/s  {climb}"),
            ("altitude (AGL)", f"{p[2]:5.2f} m"),
            ("height above marker", f"{view['height_above_marker']:5.2f} m"),
            ("distance to goal", "—" if dist_goal is None else f"{dist_goal:5.1f} m"),
            ("vision offset to marker", "—" if off is None else f"{off*100:5.1f} cm"),
            ("obstacle avoidance", "STEERING ↩" if avoiding else "clear"),
            ("battery", f"{view['battery']:5.1f} %"),
            ("wind now", f"{np.hypot(wind[0], wind[1]):4.2f} m/s"),
        ]
        if view.get("nav_detour"):
            lines.append(("route", f"avoiding obstacles @ {view.get('nav_alt', 0):.0f} m"))
        if view.get("drop_error") is not None:
            lines.append(("DROP landing error", f"{view['drop_error']*100:.1f} cm"))
        if view.get("gps_only_error") is not None:
            lines.append(("(GPS-only would miss by)", f"{view['gps_only_error']:.2f} m"))
        y = 0.97
        ax.text(0.0, y, "TELEMETRY", fontsize=11, fontweight="bold", transform=ax.transAxes)
        # Adaptive spacing so every line fits no matter how many are shown.
        step = min(0.083, 0.90 / (len(lines) + 1))
        y -= step
        fs = 9.0 if step >= 0.07 else 8.2
        for label, val in lines:
            highlight = label in ("STATE", "DROP landing error", "SPEED (ground)")
            color = _STATE_COLOR.get(view["state"], "#000") if label == "STATE" else (
                "#d95f0e" if (label == "obstacle avoidance" and avoiding) else "#222")
            weight = "bold" if highlight else "normal"
            ax.text(0.0, y, f"{label}", fontsize=fs, color="#555", transform=ax.transAxes)
            ax.text(0.60, y, f"{val}", fontsize=fs, color=color, fontweight=weight,
                    transform=ax.transAxes)
            y -= step


def _nav_view(mission) -> dict:
    """The planned route + current goal, shared by the live and exported views."""
    return {
        "cruise_path": [np.asarray(p) for p in getattr(mission, "cruise_path", [])],
        "return_path": [np.asarray(p) for p in getattr(mission, "return_path", [])],
        "nav_alt": getattr(mission, "nav_alt", None),
        "nav_detour": mission.metrics.get("nav_cruise_detour", False),
        "home_xy": np.asarray(getattr(mission, "home_xy", (0.0, 0.0))),
        "marker_xy": np.asarray(mission.marker_world[:2]),
    }


def _view_from_frame(mission, frame: dict) -> dict:
    traj = mission.trajectory[:frame["traj_len"] + 1]
    drop_err = mission.metrics.get("drop_error_m") if frame["state"] in (
        "DROP", "ASCEND", "RETURN_HOME", "LAND", "DONE") else None
    vel = frame.get("velocity", np.zeros(3))
    view = {
        "traj": traj, "pos": frame["pos"], "state": frame["state"], "t": frame["t"],
        "image": frame["image"], "vis": frame["vis"], "battery": frame["battery"],
        "wind": frame["wind"], "velocity": vel, "reflex": frame.get("reflex", False),
        "height_above_marker": frame["height_above_marker"],
        "drop_error": drop_err,
        "gps_only_error": mission.metrics.get("gps_only_error_m"),
    }
    view.update(_nav_view(mission))
    return view


def view_from_mission(mission) -> dict:
    """Build a live dashboard view dict from the current mission state."""
    tel = mission.drone.get_telemetry()
    drop_err = mission.metrics.get("drop_error_m")
    view = {
        "traj": list(mission.trajectory), "pos": mission.drone.pos.copy(),
        "state": mission.state.name, "t": mission.t,
        "image": mission.last_image, "vis": mission.last_vision,
        "battery": tel["battery_pct"], "wind": tel["wind"],
        "velocity": tel["velocity"], "reflex": getattr(mission, "_reflex_active", False),
        "height_above_marker": mission.drone.height_above_surface(),
        "drop_error": drop_err,
        "gps_only_error": mission.metrics.get("gps_only_error_m"),
    }
    view.update(_nav_view(mission))
    return view


def _figure_to_rgb(fig) -> np.ndarray:
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    return buf[:, :, :3].copy()


def export_video(mission, config=CONFIG, out_dir=None):
    """
    Render the mission's logged frames into a dashboard movie. Tries MP4 first
    (needs imageio-ffmpeg); falls back to an animated GIF. Returns the path written.
    """
    import imageio.v2 as imageio

    out_dir = out_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    config.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    if not mission.frames:
        raise RuntimeError("No frames logged — run the mission with log_frames=True")

    # Cap the number of rendered dashboard frames (keeps export fast). We always
    # keep the frames evenly spaced so the whole flight is represented.
    frames = mission.frames
    max_frames = 240
    if len(frames) > max_frames:
        idx = np.linspace(0, len(frames) - 1, max_frames).round().astype(int)
        frames = [frames[i] for i in idx]

    dash = Dashboard(config, plan=mission.plan, use_agg=True)
    rgb_frames = []
    for frame in frames:
        dash.update(_view_from_frame(mission, frame))
        rgb_frames.append(_figure_to_rgb(dash.fig))
    try:
        plt.close(dash.fig)
    except Exception:
        pass

    mp4_path = os.path.join(out_dir, config.video_filename)
    gif_path = os.path.join(out_dir, config.gif_filename)
    try:
        # Default macro_block_size pads frame dims to a multiple of 16 so libx264
        # (which needs even dimensions) is always happy.
        with imageio.get_writer(mp4_path, fps=config.video_fps,
                                codec="libx264", quality=8) as w:
            for fr in rgb_frames:
                w.append_data(fr)
        return mp4_path
    except Exception as exc:  # ffmpeg missing / codec issue -> GIF fallback
        # Remove the empty/partial MP4 the failed attempt may have left behind.
        if os.path.exists(mp4_path) and os.path.getsize(mp4_path) == 0:
            try:
                os.remove(mp4_path)
            except OSError:
                pass
        print(f"  (MP4 export unavailable: {str(exc).splitlines()[0]}; writing GIF instead)")
        imageio.mimsave(gif_path, rgb_frames, fps=min(config.video_fps, 15))
        return gif_path
