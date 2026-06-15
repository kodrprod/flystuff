"""
test_navigation.py
==================
End-to-end proof that the drone NAVIGATES around obstacles using ONLY its sensors
(LiDAR + noisy GPS, no map) instead of crashing into / stalling against them when
the launch point is moved behind something.

Each case relocates DRONE_START in the loaded scene and flies a full mission with
the realistic sensor-only avoidance (config default). The drone must reach the
balcony and deliver WITHOUT a collision — the exact failure ("bumps into the tree
/ the wall") the avoidance was added to fix.

Run directly:   python tests/test_navigation.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src import world as W
from src.mission import Mission


def _run_from(start_xy, seed=0):
    """Fly a full mission with DRONE_START relocated to start_xy."""
    orig = W.World.__init__

    def patched(self, *a, **k):
        orig(self, *a, **k)
        self.drone_start = np.array([start_xy[0], start_xy[1], 0.0])
        self.home = self.drone_start.copy()

    W.World.__init__ = patched
    try:
        m = Mission(config=SimConfig(), seed=seed)
        m.run()
        return m.metrics
    finally:
        W.World.__init__ = orig


def test_start_behind_building_navigates():
    me = _run_from((56, 30))           # far side of the building wall
    assert not me["collision"], f"crashed into {me['collision_object']}"
    assert me["reflex_events"] > 0, "sensor avoidance should engage to get around the wall"
    assert me["drop_error_m"] is not None, "the snack was never delivered"


def test_start_east_of_building_navigates():
    me = _run_from((55, 30))
    assert not me["collision"], f"crashed into {me['collision_object']}"
    assert me["drop_error_m"] is not None and me["drop_error_m"] <= 0.25


def test_various_relocated_starts_no_crash():
    starts = [(40, -15), (24, -8), (60, 60), (-10, 40), (40, -25), (-8, 30), (48, 8)]
    crashes = []
    for s in starts:
        me = _run_from(s)
        if me["collision"]:
            crashes.append((s, me["collision_object"]))
    assert not crashes, f"these relocated starts crashed: {crashes}"


def test_default_start_still_succeeds():
    me = _run_from((0, 0))
    assert me["success"], f"default mission regressed: {me['fail_reason']}"


def _build_low_obstacle_world(top_z=9.7):
    """Write a tiny world: open ground + a LOW wall straddling the straight cruise
    line, whose top sits just below the cruise altitude. Returns the world dir."""
    import json
    import tempfile
    from world.make_sample_world import ObjBuilder, write_mtl
    d = tempfile.mkdtemp(prefix="lowobs_")
    ob = ObjBuilder()
    ob.add_quad("GROUND", (15, 0), 30, 30, 0.0, material="ground")
    ob.add_box("LOWWALL", (15.0, 0.0, top_z / 2), (1.2, 4.0, top_z / 2), material="wall")
    ob.add_quad("MARKER_DROP", (30, 0), 0.125, 0.125, 9.02, material="marker")
    ob.write(os.path.join(d, "w.obj"), os.path.join(d, "w.mtl"))
    write_mtl(os.path.join(d, "w.mtl"))
    scene = {
        "units": "meters", "up_axis": "Z", "scale": 1.0, "obj_file": "w.obj",
        "home": [0, 0, 0], "drone_start": [0, 0, 0], "drop_target": [30, 0, 9],
        "markers": {"drop": {"id": 23, "size": 0.25, "pos": [30, 0, 9]},
                    "start": {"id": 7, "size": 0.25, "pos": [0, 0, 0]}},
        "solid_objects": ["LOWWALL"],
    }
    json.dump(scene, open(os.path.join(d, "scene.json"), "w"), indent=2)
    return d


def test_climbs_over_low_obstacle_instead_of_clipping_it():
    """The horizontal LiDAR fan is blind to a wall whose top sits just BELOW the
    cruise altitude, so the drone would skim over and clip it. The sensor-only
    VERTICAL avoidance must climb just enough to clear it. Control: with the climb
    disabled (cap 0) the very same flight clips the wall."""
    import dataclasses
    d = _build_low_obstacle_world(top_z=9.7)

    def fly(climb_cap):
        cfg = dataclasses.replace(SimConfig(), world_dir=d, use_sample_world=False,
                                enable_path_planning=False, avoid_climb_cap_m=climb_cap)
        m = Mission(config=cfg, seed=3)
        for _ in range(400):           # enough to cruise over the wall
            m.step()
            if m.done:
                break
        return m.metrics

    off = fly(0.0)                      # vertical climb disabled -> blind skim
    on = fly(6.0)                       # vertical climb enabled
    assert off["collision"], "control: without the climb the drone should clip the low wall"
    assert not on["collision"], f"the over-fly must clear the low wall, hit {on['collision_object']}"
    assert on["overfly_events"] > 0, "the vertical avoidance should have engaged"


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL NAVIGATION TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
