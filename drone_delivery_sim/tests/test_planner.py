"""
test_planner.py
===============
Tests the obstacle-avoiding path planner (src/planner.py) on the sample world,
using the dependency-light numpy backend so it runs anywhere.

  * clear path   : home -> balcony is a straight shot at cruise altitude.
  * around       : a start behind the building is routed AROUND it, and EVERY
                segment of the returned route is collision-free in the grid.
  * over/around  : an obstacle straight ahead at a LOW altitude is avoided (the
                planner routes around it, or climbs over it).
  * endpoints    : the route starts at start and ends at goal.

Run directly:   python tests/test_planner.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src import world as W
from src import planner as P


def _world():
    return W.World(SimConfig(), backend="numpy")


def _segments_clear(grid, wps):
    return all(grid.segment_clear(wps[i], wps[i + 1]) for i in range(len(wps) - 1))


def test_clear_path_is_straight():
    cfg = SimConfig()
    wd = _world()
    r = P.plan_route(wd, (0, 0), (40, 30), cfg, cfg.cruise_altitude_m)
    assert r["ok"], "a clear home->balcony route must be found"
    assert not r["detoured"], "the default home->balcony path should be a straight shot"
    assert len(r["waypoints"]) == 2, "a clear route needs no intermediate waypoints"
    wd.close()


def test_routes_around_building():
    cfg = SimConfig()
    wd = _world()
    # Start behind the (12 m tall) building wall; cruise altitude is below the roof,
    # so the planner MUST go around it.
    r = P.plan_route(wd, (56, 30), (40, 30), cfg, cfg.cruise_altitude_m)
    assert r["ok"] and r["detoured"], "a start behind the building must be routed around"
    aabbs = P.solid_aabbs(wd)
    grid = P.OccupancyGrid(aabbs, cfg, r["altitude"], extra_xy=[(56, 30), (40, 30)])
    assert _segments_clear(grid, r["waypoints"]), "every planned segment must be clear"
    wd.close()


def test_avoids_obstacle_ahead_low():
    cfg = SimConfig()
    wd = _world()
    # The tree (canopy z 5.2-7.8) sits directly between these two points; at 6 m the
    # planner must avoid it (around, or by climbing over).
    r = P.plan_route(wd, (24, -6), (24, 40), cfg, 6.0)
    assert r["ok"] and r["detoured"], "an obstacle dead ahead must be avoided"
    aabbs = P.solid_aabbs(wd)
    grid = P.OccupancyGrid(aabbs, cfg, r["altitude"], extra_xy=[(24, -6), (24, 40)])
    assert _segments_clear(grid, r["waypoints"]), "the avoidance route must be clear"
    wd.close()


def test_route_endpoints_exact():
    cfg = SimConfig()
    wd = _world()
    r = P.plan_route(wd, (56, 30), (40, 30), cfg, cfg.cruise_altitude_m)
    assert np.allclose(r["waypoints"][0], [56, 30]), "route must start at the start"
    assert np.allclose(r["waypoints"][-1], [40, 30]), "route must end at the goal"
    wd.close()


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL PLANNER TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
