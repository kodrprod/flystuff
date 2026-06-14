"""
main.py
=======
Run ONE complete snack-delivery mission end-to-end and save a demo video.

Beginner usage (just run it):

    python main.py

What you will see:
  * A dashboard window opens (on macOS) and animates the whole flight: the drone
    leaves home, cruises to the building on GPS, climbs above the balcony,
    searches for and locks onto the ArUco marker with the real camera+vision,
    descends, drops the snack, then flies home and lands.
  * In the terminal: the mission state changes and a final results summary.
  * A video file (outputs/mission_demo.mp4, or a .gif fallback) you can re-watch.

Useful options:
    python main.py --headless     # no window, just compute + save the video
    python main.py --seed 12       # try a different random scenario
    python main.py --no-video      # skip the video export (fastest)

Change the SCENARIO (balcony height, wind, marker, etc.) by editing config.py.
"""

from __future__ import annotations
import argparse
import os
import sys
import time


def _require_dependencies() -> None:
    """Fail early with a friendly, copy-pasteable message if any third-party
    package is missing -- instead of a confusing deep ImportError traceback
    (e.g. "No module named 'cv2'") coming out of some inner module."""
    import importlib.util
    required = {
        "numpy": "numpy",
        "cv2": "opencv-contrib-python",
        "matplotlib": "matplotlib",
        "imageio": "imageio",
    }
    missing = [pip_name for module, pip_name in required.items()
               if importlib.util.find_spec(module) is None]
    if not missing:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    bar = "=" * 66
    print(bar)
    print(" Missing required Python package(s): " + ", ".join(missing))
    print(bar)
    print("This simulation needs a few libraries that aren't installed yet.")
    print("")
    print("Easiest fix on a Mac -- create the project's private environment")
    print("and install everything from requirements.txt:")
    print("")
    print(f'    cd "{here}"')
    print("    python3 -m venv .venv")
    print("    source .venv/bin/activate")
    print("    pip install -r requirements.txt")
    print("")
    print("Then run the simulation again:")
    print("")
    print("    source .venv/bin/activate")
    print("    python main.py")
    print("")
    print("(Or just double-click setup_mac.command in Finder.)")
    print(bar)
    sys.exit(1)


_require_dependencies()

import matplotlib

from config import CONFIG


def choose_backend(want_live: bool) -> str:
    """Pick a matplotlib backend. MUST run before pyplot is imported."""
    if not want_live:
        matplotlib.use("Agg")
        return "Agg"
    # Prefer the native macOS backend, then common cross-platform GUI backends.
    for backend in ("MacOSX", "TkAgg", "QtAgg"):
        try:
            matplotlib.use(backend)
            return backend
        except Exception:
            continue
    matplotlib.use("Agg")  # no GUI available -> headless
    return "Agg"


def print_summary(mission):
    m = mission.metrics
    print("\n" + "=" * 58)
    print(" MISSION RESULTS")
    print("=" * 58)
    def fmt(v, unit="", scale=1.0, nd=2):
        return "—" if v is None else f"{v*scale:.{nd}f}{unit}"
    print(f"  Outcome              : {'SUCCESS' if m['success'] else 'see notes below'}")
    print(f"  Snack drop error     : {fmt(m['drop_error_m'],' cm',100,1)}   (target <= 20 cm)")
    print(f"  GPS-only would miss  : {fmt(m['gps_only_error_m'],' m')}   <- why we need vision")
    print(f"  Release height       : {fmt(m['drop_height_m'],' m')} above the balcony floor")
    print(f"  Returned home within : {fmt(m['return_error_m'],' m')}   (GPS landing)")
    print(f"  Battery used         : {fmt(m['battery_used_pct'],' %')}")
    print(f"  Flight time          : {fmt(m['duration_s'],' s')}")
    if m["fail_reason"]:
        print(f"  Note                 : {m['fail_reason']}")
    print("=" * 58)


def main():
    parser = argparse.ArgumentParser(description="Autonomous snack-delivery drone simulation")
    parser.add_argument("--headless", action="store_true", help="no window; just save the video")
    parser.add_argument("--no-video", action="store_true", help="skip video export")
    parser.add_argument("--seed", type=int, default=CONFIG.seed, help="random seed / scenario")
    parser.add_argument("--setup", action="store_true", help="manual start/drop position setup")
    parser.add_argument("--multifeed", "--feeds", action="store_true", dest="multifeed",
                        help="export the combined multi-feed video (3rd-person+LiDAR+cameras)")
    parser.add_argument("--split", action="store_true",
                        help="run the onboard/ground compute split in two real processes")
    parser.add_argument("--single-process", action="store_true",
                        help="run the compute split in one process (fast)")
    parser.add_argument("--world", choices=["sample", "blender"], default=None,
                        help="which world to load (overrides config.use_sample_world)")
    args = parser.parse_args()

    if args.world is not None:
        CONFIG.use_sample_world = (args.world == "sample")
        CONFIG.world_scene_file = "scene.json"

    # ---- Alternate modes (exit after) ----
    if args.setup:
        import setup_positions
        sys.argv = [sys.argv[0]] + (["--no-gui"] if args.headless else [])
        return setup_positions.main()

    if args.multifeed:
        from src import multifeed as mf
        print("Rendering the multi-feed demo (this runs a full mission)...")
        path, metrics = mf.run_multifeed(CONFIG, seed=args.seed)
        d = metrics["drop_error_m"]
        print(f"Drop: {d*100:.1f} cm   collision: {metrics['collision']}" if d else
            f"Mission ended: {metrics['fail_reason']}")
        print(f"Saved multi-feed video to: {path}")
        return

    if args.split or args.single_process:
        from src import compute as C
        processes = not args.single_process
        print(f"Running onboard/ground compute split ({'two processes' if processes else 'single process'})...")
        r = C.run_compute_split(CONFIG, seed=args.seed, processes=processes)
        m = r["metrics"]; lk = r["link"]; bg = r["budget"]
        print("\n=== COMPUTE SPLIT ===")
        print(f"  onboard tasks : {', '.join(r['task_location']['onboard'])}")
        print(f"  ground tasks  : {', '.join(r['task_location']['ground'])}")
        print(f"  link          : latency {lk['max_latency_ms']:.0f} ms, "
            f"attempted {lk['attempted_kbps']:.0f} kbps -> achieved {lk['achieved_kbps']:.0f} kbps, "
            f"loss {100*(1-lk['delivery_rate']):.0f}%")
        print(f"  bandwidth drops: {lk['dropped_bandwidth']}   loss drops: {lk['dropped_loss']}")
        print(f"  onboard budget : {bg['max_used_ms']:.1f}/{bg['budget_ms']:.1f} ms per tick, "
            f"overflows {bg['overflows']}")
        print(f"  ground received: {r['ground_received']['telemetry']} telemetry, "
            f"{r['ground_received']['frames']} frames")
        if m:
            print(f"  delivery       : drop {m['drop_error_m']*100:.1f} cm, collision {m['collision']}"
                if m['drop_error_m'] else f"  delivery: {m['fail_reason']}")
        return

    backend = choose_backend(want_live=not args.headless)
    live = backend != "Agg"

    # Import AFTER the backend is chosen.
    import matplotlib.pyplot as plt
    from src.mission import Mission
    from src import visualize as vz

    print(f"matplotlib backend: {backend}  ({'live window' if live else 'headless'})")
    print(f"Scenario: balcony {CONFIG.balcony_height_m:.0f} m up, marker id {CONFIG.marker_id}, "
        f"wind ~{(CONFIG.wind_base_mps[0]**2+CONFIG.wind_base_mps[1]**2)**0.5:.1f} m/s, seed {args.seed}")
    print("Flying mission...\n")

    mission = Mission(config=CONFIG, seed=args.seed, log_frames=not args.no_video)

    last_state = [None]
    def on_step(m):
        if m.state.name != last_state[0]:
            last_state[0] = m.state.name
            print(f"  t={m.t:6.1f}s   {m.state.name}")
        if live and m.step_count % (CONFIG.video_every_n_steps * 2) == 0:
            dash.update(vz.view_from_mission(m))
            plt.pause(0.001)

    t0 = time.time()
    if live:
        dash = vz.Dashboard(CONFIG, plan=mission.plan)
        plt.show(block=False)
        mission.run(on_step=on_step)
        dash.update(vz.view_from_mission(mission))
        plt.pause(0.8)
    else:
        mission.run(on_step=on_step)
    print(f"\n(simulated {mission.t:.0f}s of flight in {time.time()-t0:.1f}s of compute)")

    print_summary(mission)

    if not args.no_video:
        print("\nRendering demo video...")
        path = vz.export_video(mission, CONFIG)
        print(f"Saved demo to: {path}")

    if live:
        print("\nClose the window to exit.")
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    main()
