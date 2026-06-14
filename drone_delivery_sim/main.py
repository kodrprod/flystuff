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
import sys
import time
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
    if m.get("nav_planned"):
        route = (f"avoided obstacles (climb to {m['nav_cruise_alt']:.0f} m / "
                f"{m['nav_waypoints']} waypoints)" if m.get("nav_cruise_detour")
                else "clear straight path")
        print(f"  Navigation           : {route}")
    if m.get("collision"):
        print(f"  COLLISION            : hit {m['collision_object']} at "
            f"{fmt(m['collision_time_s'],' s')}")
    if m["fail_reason"]:
        print(f"  Note                 : {m['fail_reason']}")
    print("=" * 58)


def main():
    parser = argparse.ArgumentParser(description="Autonomous snack-delivery drone simulation")
    parser.add_argument("--headless", action="store_true", help="no window; just save the video")
    parser.add_argument("--no-video", action="store_true", help="skip video export")
    parser.add_argument("--seed", type=int, default=CONFIG.seed, help="random seed / scenario")
    parser.add_argument("--setup", action="store_true", help="manual start/drop position setup")
    parser.add_argument("--multifeed", action="store_true",
                        help="export the combined multi-feed video (3rd-person+LiDAR+cameras)")
    parser.add_argument("--split", action="store_true",
                        help="run the onboard/ground compute split in two real processes")
    parser.add_argument("--single-process", action="store_true",
                        help="run the compute split in one process (fast)")
    parser.add_argument("--world", choices=["sample", "blender", "custom"], default=None,
                        help="which world to load (overrides config.use_sample_world)")
    parser.add_argument("--feeds", action="store_true",
                        help="LIVE multi-feed window (3rd-person + LiDAR + cameras), real time")
    parser.add_argument("--speed", type=float, default=None,
                        help="live playback speed (1.0 = real time; 0.5 = slow-mo; 2 = 2x)")
    parser.add_argument("--import-obj", metavar="PATH", default=None,
                        help="import any .obj model as the world, then exit (see README)")
    args = parser.parse_args()

    # Import a custom 3D model and exit (sets up the world's scene.json for it).
    if args.import_obj:
        from world import import_model
        import_model.import_model(args.import_obj)
        return

    if args.speed is not None:
        CONFIG.live_speed = args.speed

    if args.world == "sample":
        # Force-rebuild the bundled sample world so it overrides any imported/Blender
        # scene.json that may be the currently active world.
        import importlib.util, os as _os
        wdir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), CONFIG.world_dir)
        spec = importlib.util.spec_from_file_location(
            "make_sample_world", _os.path.join(wdir, "make_sample_world.py"))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.build(CONFIG)
        CONFIG.use_sample_world = True
        CONFIG.world_scene_file = "scene.json"
    elif args.world is not None:
        CONFIG.use_sample_world = False
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

    # ---- LIVE multi-feed window (3rd-person + LiDAR + cameras), paced to real time.
    if args.feeds or CONFIG.live_feeds:
        from src import multifeed as mf
        if not live:
            print("(no display available — rendering the multi-feed video headless)")
            path, metrics = mf.run_multifeed(CONFIG, seed=args.seed)
        else:
            print(f"Flying mission with the LIVE multi-feed window "
                f"(real time x{CONFIG.live_speed:g})...\n")
            path, metrics = mf.run_multifeed_live(CONFIG, seed=args.seed)
        d = metrics.get("drop_error_m")
        print(f"\nDrop: {d*100:.1f} cm   collision: {metrics['collision']}" if d else
            f"\nMission ended: {metrics['fail_reason']}")
        if path:
            print(f"Saved multi-feed video to: {path}")
        if live:
            print("\nClose the window to exit.")
            plt.ioff(); plt.show()
        return

    print("Flying mission...\n")

    mission = Mission(config=CONFIG, seed=args.seed, log_frames=not args.no_video)

    # How often the live window redraws, expressed in sim steps, and the wall-clock
    # time each sim second should take (real-time pacing so you can watch each phase).
    update_every = max(1, int(round((1.0 / max(CONFIG.live_update_hz, 1e-3)) / CONFIG.dt)))
    pace = {"t0": None}

    last_state = [None]
    def on_step(m):
        if m.state.name != last_state[0]:
            last_state[0] = m.state.name
            print(f"  t={m.t:6.1f}s   {m.state.name}")
        if live and m.step_count % update_every == 0:
            dash.update(vz.view_from_mission(m))
            plt.pause(0.001)
            # Real-time pacing: hold each frame so 1 sim second ~= 1 wall second.
            if pace["t0"] is None:
                pace["t0"] = time.time()
            target = pace["t0"] + m.t / max(CONFIG.live_speed, 1e-6)
            lag = target - time.time()
            if lag > 0:
                time.sleep(min(lag, 0.5))

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
