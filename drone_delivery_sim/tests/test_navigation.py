"""
test_navigation.py
==================
End-to-end proof that the drone now NAVIGATES around obstacles instead of crashing
into / stalling against them when the launch point is moved behind something.

Each case relocates DRONE_START in the loaded scene and flies a full mission. The
drone must reach the balcony and deliver WITHOUT a collision — the exact failure
("bumps into the tree / the wall") the obstacle avoidance was added to fix.

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
    assert me["nav_cruise_detour"], "the route should detour around the building"
    assert me["drop_error_m"] is not None, "the snack was never delivered"


def test_start_east_of_building_navigates():
    me = _run_from((55, 30))
    assert not me["collision"], f"crashed into {me['collision_object']}"
    assert me["drop_error_m"] is not None and me["drop_error_m"] <= 0.25


def test_various_relocated_starts_no_crash():
    starts = [(40, -15), (24, -8), (60, 60), (-10, 40), (40, -25), (-8, 30)]
    crashes = []
    for s in starts:
        me = _run_from(s)
        if me["collision"]:
            crashes.append((s, me["collision_object"]))
    assert not crashes, f"these relocated starts crashed: {crashes}"


def test_default_start_still_succeeds():
    me = _run_from((0, 0))
    assert me["success"], f"default mission regressed: {me['fail_reason']}"
    assert not me["nav_cruise_detour"], "default home->balcony should stay a straight path"


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
