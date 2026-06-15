"""
test_world.py
=============
Tests the 3D world layer (collision, LiDAR, reflex, scale) on the sample world,
using the dependency-light numpy backend so it runs anywhere.

  * scale       : a 1 m reference cube imports as 1.0 m.
  * collision   : flying into the tree IS detected; a clear path is NOT.
  * reflex      : with the LiDAR reflex on, the drone halts before contact.
  * reflex 3D   : the reflex also catches obstacles the drone is climbing /
                  descending INTO (overhead canopy), while NOT tripping on
                  structure it merely passes over.
  * lidar       : ray ranges to known geometry match within tolerance.

Run directly:   python tests/test_world.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src import world as W


def _world():
    return W.World(SimConfig(), backend="numpy")


def _fly_straight(world, cfg, start, direction, reflex):
    """Mimic the mission's straight-line motion + onboard reflex; return outcome."""
    direction = np.asarray(direction, float)
    direction = direction / np.linalg.norm(direction)
    heading = float(np.arctan2(direction[1], direction[0]))
    pos = np.asarray(start, float).copy()
    min_fwd = np.inf
    for _ in range(300):
        world.set_drone_pose(pos, heading)
        collided, name, _pt, _gap = world.check_collision()
        if collided:
            return True, pos, min_fwd, name
        fd = world.reflex_distance(pos, heading)
        min_fwd = min(min_fwd, fd)
        step = direction * 0.1
        if reflex and fd < cfg.lidar_reflex_stop_m:
            step = step * 0.0
        pos = pos + step
    return False, pos, min_fwd, None


def test_scale_one_metre_cube():
    cube = "/tmp/_cube1m.obj"
    with open(cube, "w") as f:
        f.write("o CUBE\n")
        for sx in (0, 1):
            for sy in (0, 1):
                for sz in (0, 1):
                    f.write(f"v {sx} {sy} {sz}\n")
        f.write("f 1 2 4\nf 1 4 3\nf 5 6 8\nf 5 8 7\n")
    V, F = W.parse_obj_objects(cube)["CUBE"]
    size = V.max(0) - V.min(0)
    assert np.allclose(size, 1.0, atol=1e-6), f"1 m cube imported as {size}"


def test_collision_into_tree_detected():
    cfg = SimConfig()
    wd = _world()
    collided, pos, _mf, name = _fly_straight(wd, cfg, (15, 12, 6.0), (1, 0, 0), reflex=False)
    assert collided, "flying straight into the tree should be detected as a collision"
    assert pos[0] <= 23.0, f"collision should be at the tree (~x22.7), got x={pos[0]:.2f}"
    wd.close()


def test_clear_path_no_false_collision():
    cfg = SimConfig()
    wd = _world()
    # Fly North over open ground far from any structure.
    collided, _pos, _mf, _n = _fly_straight(wd, cfg, (5, -5, 6.0), (0, 1, 0), reflex=False)
    assert not collided, "an open-air path must not trigger a collision"
    wd.close()


def test_reflex_halts_before_contact():
    cfg = SimConfig()
    wd = _world()
    collided, pos, min_fwd, _n = _fly_straight(wd, cfg, (15, 12, 6.0), (1, 0, 0), reflex=True)
    assert not collided, "with the reflex ON the drone must NOT crash into the tree"
    assert pos[0] < 22.0, f"reflex should stop short of the tree, stopped at x={pos[0]:.2f}"
    assert min_fwd >= cfg.lidar_reflex_stop_m - 0.5, "reflex held roughly at the stop distance"
    wd.close()


def _climb_straight_up(world, cfg, start, aimed):
    """Climb straight up with the onboard reflex. `aimed` probes the true 3-D
    travel direction (the fix); otherwise it uses the old horizontal-only fan."""
    pos = np.asarray(start, float).copy()
    for _ in range(400):
        world.set_drone_pose(pos, 0.0)
        collided, name, _pt, _gap = world.check_collision()
        if collided:
            return True, pos
        fd = (world.reflex_distance(pos, 0.0, climb=1.0, speed=0.1) if aimed
            else world.reflex_distance(pos, 0.0))   # old: flat horizontal fan
        step = np.array([0.0, 0.0, 0.1])
        if fd < cfg.lidar_reflex_stop_m:
            step = step * 0.0
        pos = pos + step
    return False, pos


def test_reflex_halts_climb_into_overhead_canopy():
    """Regression: the reflex must catch obstacles the drone is climbing INTO
    (a tree canopy overhead), not just ones that are level and off to the side.
    The canopy underside sits at ~5.2 m; starting under it (clear of the trunk)
    and climbing, the aimed reflex must hold short while the old horizontal-only
    fan -- which never looks up -- flies straight into it."""
    cfg = SimConfig()
    wd = _world()
    collided, pos = _climb_straight_up(wd, cfg, (23.0, 11.0, 3.0), aimed=True)
    assert not collided, "aimed reflex must stop the climb before the canopy"
    assert pos[2] < 5.0, f"should hold below the canopy underside, got z={pos[2]:.2f}"
    crashed, _ = _climb_straight_up(wd, cfg, (23.0, 11.0, 3.0), aimed=False)
    assert crashed, "a horizontal-only probe should miss the overhead canopy (the bug)"
    wd.close()


def test_reflex_sweep_is_one_sided_toward_travel():
    """The elevation sweep reaches only toward the travel direction: climbing
    over a slab stays clear (no false stop on structure flown over), while
    descending toward the same slab detects it."""
    cfg = SimConfig()
    wd = _world()
    pos = np.array([40.0, 30.0, 9.5])          # ~1.5 m above the balcony slab
    heading = np.radians(180)                  # face away from the building
    clear_up = wd.reflex_distance(pos, heading, climb=1.0, speed=0.5)    # climbing
    sees_down = wd.reflex_distance(pos, heading, climb=-1.0, speed=0.5)  # descending
    assert clear_up >= cfg.lidar_reflex_stop_m, \
        f"climbing over a slab must not trip the reflex, got {clear_up:.2f} m"
    assert sees_down < cfg.lidar_reflex_stop_m, \
        f"descending toward the slab must detect it, got {sees_down:.2f} m"
    wd.close()


def test_lidar_ranges():
    wd = _world()
    # From x=19 facing East, the tree canopy face is at x~22.7 (half-extent 1.3).
    wd.set_drone_pose(np.array([19.0, 12.0, 6.0]), 0.0)
    fd = wd.forward_clear_distance()
    assert 3.2 <= fd <= 4.2, f"expected ~3.7 m to the tree, got {fd:.2f}"
    # Open direction -> max range.
    wd.set_drone_pose(np.array([5.0, 5.0, 6.0]), np.pi / 2)
    assert wd.forward_clear_distance() >= wd.cfg.lidar_range_m - 0.3, "open sky should be max range"
    wd.close()


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL WORLD TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
