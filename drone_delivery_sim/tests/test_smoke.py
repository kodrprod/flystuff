"""
test_smoke.py
=============
Fast sanity checks:
  * every module imports cleanly;
  * a short run executes with no exceptions and the state machine advances;
  * a full run can export a demo video/GIF file (the file really appears).

Run directly:   python tests/test_smoke.py
Or with pytest: python -m pytest tests/test_smoke.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# matplotlib must use a non-GUI backend inside tests.
import matplotlib
matplotlib.use("Agg")


def test_all_imports():
    import config                       # noqa: F401
    from src import geo, drone, sensors, camera_sim, vision  # noqa: F401
    from src import control, dispatch, drop, mission, visualize  # noqa: F401


def test_short_run_no_exceptions():
    from config import CONFIG
    from src.mission import Mission, MissionState
    m = Mission(config=CONFIG, seed=2)
    for _ in range(60):           # ~3 s of flight
        m.step()
        if m.done:
            break
    # It should have armed and be doing *something* (not stuck in IDLE).
    assert m.state != MissionState.IDLE
    assert m.step_count > 0
    assert m.drone.armed or m.done


def test_video_export_creates_file():
    from config import CONFIG
    from src.mission import Mission
    from src.visualize import export_video
    m = Mission(config=CONFIG, seed=2, log_frames=True)
    m.run()
    assert m.metrics["drop_error_m"] is not None, "mission should complete a drop"
    out_dir = tempfile.mkdtemp(prefix="dronesim_smoke_")
    path = export_video(m, CONFIG, out_dir=out_dir)
    assert os.path.exists(path) and os.path.getsize(path) > 0, "no video/GIF written"
    print(f"  smoke video written: {path} ({os.path.getsize(path)//1024} KB)")


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except Exception as e:  # noqa: BLE001
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL SMOKE TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
