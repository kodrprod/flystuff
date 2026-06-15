"""
test_avoidance.py
=================
Unit tests for the SENSOR-ONLY reactive navigator (src/avoidance.py).

These prove the avoidance logic uses nothing but a LiDAR distance scan + a goal
direction (no map): each test hands `repulse()` a hand-built scan and checks it
steers sensibly.

  * open air        : every ray clear -> velocity unchanged.
  * wall on a side  : pushes away from that side.
  * wall dead ahead : with the goal behind it, steers sideways (doesn't stall).

Run directly:   python tests/test_avoidance.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src import avoidance


def _scan(n=36, fill=None):
    """A blank 360-degree scan (all rays at max range) -> bearings, clear."""
    cfg = SimConfig()
    bearings = np.radians(np.linspace(0, 360, n, endpoint=False))
    clear = np.full(n, cfg.lidar_range_m if fill is None else fill, float)
    return bearings, clear


def test_open_air_unchanged():
    cfg = SimConfig()
    bearings, clear = _scan()
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])     # heading East
    v, active = avoidance.repulse(goal, bearings, clear, cfg)
    assert not active, "open air must not trigger avoidance"
    assert np.allclose(v, goal), "velocity must be unchanged in open air"


def test_obstacle_on_the_right_pushes_left():
    cfg = SimConfig()
    bearings, clear = _scan()
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])     # heading East (+x)
    # Put a close return to the SOUTH (right of an East-bound drone): bearing -90.
    south = int(np.argmin(np.abs(avoidance.wrap(bearings - np.radians(-90)))))
    clear[south] = 1.0
    v, active = avoidance.repulse(goal, bearings, clear, cfg)
    assert active, "a close obstacle must trigger avoidance"
    assert v[1] > 1e-3, "must steer NORTH (away from the southern obstacle)"


def test_wall_ahead_steers_sideways():
    cfg = SimConfig()
    bearings, clear = _scan()
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])     # wants to go East
    # A wall straight ahead (a fan of close returns around East / bearing 0).
    ahead = np.abs(avoidance.wrap(bearings - 0.0)) < np.radians(35)
    clear[ahead] = 1.2
    v, active = avoidance.repulse(goal, bearings, clear, cfg)
    assert active, "a wall ahead must trigger avoidance"
    assert abs(v[1]) > 0.3, "must develop a sideways (tangential) component to slip past"


def _scan3d(level_clear, up_clear, down_clear=12.0, n=16):
    """Synthetic 3-D scan heading East: ring (el=0) + forward up/down rays at az=0."""
    cfg = SimConfig()
    az, el, clear = [], [], []
    for a in np.radians(np.linspace(0, 360, n, endpoint=False)):
        az.append(a); el.append(0.0)
        ahead = abs(avoidance.wrap(np.array([a]))[0]) < np.radians(40)  # near East (0)
        clear.append(level_clear if ahead else cfg.lidar_range_m)
    for e in (45.0, 70.0):
        az.append(0.0); el.append(np.radians(e)); clear.append(up_clear)
    az.append(0.0); el.append(np.radians(-30.0)); clear.append(down_clear)
    return np.array(az), np.array(el), np.array(clear)


def test_climbs_over_when_open_above():
    cfg = SimConfig()
    az, el, clear = _scan3d(level_clear=1.5, up_clear=cfg.lidar_range_m)   # tree: blocked ahead, open above
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])
    rate, active = avoidance.vertical_avoid(goal, az, el, clear, cfg, ground_clear=10.0)
    assert active and rate > 0.0, "should climb over an obstacle that is open above"


def test_no_climb_when_blocked_above():
    cfg = SimConfig()
    az, el, clear = _scan3d(level_clear=1.5, up_clear=1.5, down_clear=1.5)  # building: blocked all round
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])
    rate, active = avoidance.vertical_avoid(goal, az, el, clear, cfg, ground_clear=10.0)
    assert not active and rate == 0.0, "a wall blocked above must be gone around, not climbed"


def test_ducks_under_when_open_below():
    cfg = SimConfig()
    az, el, clear = _scan3d(level_clear=1.5, up_clear=1.5, down_clear=cfg.lidar_range_m)  # overhang
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])
    rate, active = avoidance.vertical_avoid(goal, az, el, clear, cfg, ground_clear=15.0)
    assert active and rate < 0.0, "should duck under when blocked above but open below with ground room"


def test_no_vertical_when_path_clear():
    cfg = SimConfig()
    az, el, clear = _scan3d(level_clear=cfg.lidar_range_m, up_clear=cfg.lidar_range_m)
    goal = np.array([cfg.max_horizontal_speed_mps, 0.0])
    rate, active = avoidance.vertical_avoid(goal, az, el, clear, cfg, ground_clear=10.0)
    assert not active and rate == 0.0, "open path -> no vertical maneuver"


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL AVOIDANCE TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
