"""
test_vertical_nav.py
====================
End-to-end proof that the sensor-only avoidance works in 3-D: it climbs OVER an
obstacle it can clear, and goes AROUND one too tall to clear -- using only the
LiDAR scan (no map). Each case builds a tiny throwaway world and flies a mission.

  * hedge     : a wide barrier just above cruise height -> the drone HOPS OVER it
                (its altitude rises well above cruise) and delivers, no collision.
  * tall wall : a barrier far too tall to clear -> the drone goes AROUND it (it
                stays near cruise height, swinging sideways) and delivers, no crash.

Run directly:   python tests/test_vertical_nav.py
"""

import os
import sys
import json
import tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src.mission import Mission


def _box(f, name, c, h, vb):
    cx, cy, cz = c; hx, hy, hz = h
    vs = [(cx + sx * hx, cy + sy * hy, cz + sz * hz)
        for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    f.write(f"o {name}\n")
    for v in vs:
        f.write("v %.3f %.3f %.3f\n" % v)

    def i(sx, sy, sz):
        return vb + 1 + ((0 if sx < 0 else 1) * 4 + (0 if sy < 0 else 1) * 2 + (0 if sz < 0 else 1))
    quads = [[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1)], [(-1,-1,1),(-1,1,1),(1,1,1),(1,-1,1)],
            [(-1,-1,-1),(-1,1,-1),(-1,1,1),(-1,-1,1)], [(1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1)],
            [(-1,-1,-1),(-1,-1,1),(1,-1,1),(1,-1,-1)], [(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]]
    for q in quads:
        a, b, c2, d = [i(*p) for p in q]
        f.write(f"f {a} {b} {c2}\nf {a} {c2} {d}\n")
    return vb + 8


def _quad(f, name, cx, cy, z, he, hn, vb):
    f.write(f"o {name}\n")
    for (x, y) in [(cx-he, cy-hn), (cx+he, cy-hn), (cx+he, cy+hn), (cx-he, cy+hn)]:
        f.write("v %.3f %.3f %.3f\n" % (x, y, z))
    f.write(f"f {vb+1} {vb+2} {vb+3}\nf {vb+1} {vb+3} {vb+4}\n")
    return vb + 4


def _build_world(obstacle_half_z, obstacle_half_y=6.0):
    """A world: ground, a barrier across the path at x=20, and a balcony target at x=40."""
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "w.obj"), "w") as f:
        vb = _quad(f, "GROUND", 20, 0, 0.0, 80, 60, 0)
        vb = _box(f, "OBSTACLE", (20, 0, obstacle_half_z), (0.8, obstacle_half_y, obstacle_half_z), vb)
        vb = _box(f, "BALCONY", (40, 0, 7.9), (2, 2, 0.1), vb)
        vb = _quad(f, "MARKER_DROP", 40, 0, 8.02, 0.125, 0.125, vb)
    scene = {"units": "meters", "up_axis": "Z", "scale": 1.0, "obj_file": "w.obj",
            "home": [0, 0, 0], "drone_start": [0, 0, 0], "drop_target": [40, 0, 8],
            "markers": {"drop": {"id": 23, "size": 0.25, "pos": [40, 0, 8]}},
            "solid_objects": ["OBSTACLE", "BALCONY"]}
    json.dump(scene, open(os.path.join(d, "scene.json"), "w"))
    return d


def _fly(world_dir):
    cfg = SimConfig(); cfg.world_dir = world_dir; cfg.use_sample_world = False
    m = Mission(config=cfg, seed=0)
    stats = {"maxalt": 0.0, "ymin": 1e9, "ymax": -1e9}

    def on_step(mi):
        if mi.state.name == "CRUISE_TO_WAYPOINT":
            stats["maxalt"] = max(stats["maxalt"], float(mi.drone.pos[2]))
            stats["ymin"] = min(stats["ymin"], float(mi.drone.pos[1]))
            stats["ymax"] = max(stats["ymax"], float(mi.drone.pos[1]))
    m.run(on_step=on_step)
    return m.metrics, stats, cfg


def test_climbs_over_a_clearable_barrier():
    me, stats, cfg = _fly(_build_world(obstacle_half_z=6.5))   # top 13 m, just above cruise (10)
    assert not me["collision"], f"crashed into {me['collision_object']} instead of climbing over"
    assert me["drop_error_m"] is not None, "never delivered"
    assert stats["maxalt"] > cfg.cruise_altitude_m + 2.0, \
        f"should have climbed well above cruise to clear it (max {stats['maxalt']:.1f} m)"


def test_goes_around_a_too_tall_wall():
    # top 35 m (cannot be cleared), 8 m wide (the drone can sense its edges to go around)
    me, stats, cfg = _fly(_build_world(obstacle_half_z=17.5, obstacle_half_y=4.0))
    assert not me["collision"], f"crashed into {me['collision_object']} instead of going around"
    assert me["drop_error_m"] is not None, "never delivered"
    sideways = max(abs(stats["ymin"]), abs(stats["ymax"]))
    assert sideways > 3.0, f"should have swung sideways to go around (max |y| {sideways:.1f} m)"


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1; print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL VERTICAL-NAV TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
