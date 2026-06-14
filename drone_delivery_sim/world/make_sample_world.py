"""
make_sample_world.py
=====================
Procedurally generate a simple-but-non-trivial 3D world so the whole simulation
is runnable and testable WITHOUT Blender. Andrey later replaces this with his own
Blender export (see export_from_blender.py and the README).

It writes three files into this `world/` folder:
  * sample_world.obj   — the geometry (ground, building, balcony + railing, a tree
                         obstacle, and two flat marker decals)
  * sample_world.mtl   — simple colours for the objects
  * scene.json         — the AUTHORITATIVE positions the simulator reads:
                         home, DRONE_START, DROP_TARGET, marker ids/sizes, and
                         which named objects are SOLID (count as collisions).

Everything is authored directly in the project's ENU metres frame
(X=East, Y=North, Z=Up, 1 unit = 1 m), so no axis/scale conversion is needed for
the sample world. (Blender exports DO need conversion — handled in world.py.)

Pure standard library: no third-party dependencies, so it always runs.
"""

from __future__ import annotations
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


class ObjBuilder:
    """Minimal Wavefront OBJ writer with named objects (groups)."""

    def __init__(self):
        self.vertices = []          # list of (x, y, z)
        self.objects = []           # list of (name, material, [face tuples])

    def _add_vertex(self, x, y, z) -> int:
        self.vertices.append((x, y, z))
        return len(self.vertices)    # OBJ indices are 1-based

    def add_box(self, name, center, half, material="wall"):
        """Axis-aligned box: center (cx,cy,cz), half-extents (hx,hy,hz)."""
        cx, cy, cz = center
        hx, hy, hz = half
        idx = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    idx.append(self._add_vertex(cx + sx * hx, cy + sy * hy, cz + sz * hz))
        # idx order: (sx,sy,sz) with sz fastest. Build the 12 triangles.
        def v(sx, sy, sz):
            i = ((0 if sx < 0 else 1) * 4 + (0 if sy < 0 else 1) * 2 + (0 if sz < 0 else 1))
            return idx[i]
        quads = [
            [v(-1,-1,-1), v(1,-1,-1), v(1,1,-1), v(-1,1,-1)],   # bottom z-
            [v(-1,-1, 1), v(-1,1, 1), v(1,1, 1), v(1,-1, 1)],   # top z+
            [v(-1,-1,-1), v(-1,1,-1), v(-1,1,1), v(-1,-1,1)],   # x-
            [v(1,-1,-1), v(1,-1,1), v(1,1,1), v(1,1,-1)],       # x+
            [v(-1,-1,-1), v(-1,-1,1), v(1,-1,1), v(1,-1,-1)],   # y-
            [v(-1,1,-1), v(1,1,-1), v(1,1,1), v(-1,1,1)],       # y+
        ]
        faces = []
        for q in quads:
            faces.append((q[0], q[1], q[2]))
            faces.append((q[0], q[2], q[3]))
        self.objects.append((name, material, faces))

    def add_quad(self, name, center, half_e, half_n, z, material="marker"):
        """A flat horizontal quad (a decal) at height z, extent half_e x half_n."""
        cx, cy = center
        a = self._add_vertex(cx - half_e, cy - half_n, z)
        b = self._add_vertex(cx + half_e, cy - half_n, z)
        c = self._add_vertex(cx + half_e, cy + half_n, z)
        d = self._add_vertex(cx - half_e, cy + half_n, z)
        self.objects.append((name, material, [(a, b, c), (a, c, d)]))

    def write(self, obj_path, mtl_path):
        mtl_name = os.path.basename(mtl_path)
        with open(obj_path, "w") as f:
            f.write("# Procedural sample world (ENU metres, Z up)\n")
            f.write(f"mtllib {mtl_name}\n")
            for (x, y, z) in self.vertices:
                f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            for (name, material, faces) in self.objects:
                f.write(f"o {name}\n")
                f.write(f"usemtl {material}\n")
                for (a, b, c) in faces:
                    f.write(f"f {a} {b} {c}\n")


MATERIALS = {
    # name: (r, g, b)
    "ground": (0.55, 0.60, 0.52),
    "wall":   (0.72, 0.72, 0.74),
    "balcony": (0.66, 0.60, 0.52),
    "railing": (0.45, 0.45, 0.48),
    "trunk":  (0.40, 0.27, 0.16),
    "leaves": (0.25, 0.50, 0.23),
    "marker": (0.95, 0.95, 0.95),
    "marker_start": (0.20, 0.45, 0.90),
}


def write_mtl(mtl_path):
    with open(mtl_path, "w") as f:
        for name, (r, g, b) in MATERIALS.items():
            f.write(f"newmtl {name}\n")
            f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
            f.write("Ka 0.1 0.1 0.1\nKs 0.0 0.0 0.0\nd 1.0\nillum 1\n\n")


def build(config=None):
    """
    Build the sample world. Positions are taken from `config` when supplied so the
    world matches the simulation scenario (balcony location/height, marker, home).
    """
    # Lazy import so this script also runs standalone without the package on path.
    if config is None:
        try:
            from config import CONFIG as config
        except Exception:
            config = None

    # Scenario positions (fall back to sensible defaults if config is absent).
    tE = getattr(config, "target_east_m", 40.0)
    tN = getattr(config, "target_north_m", 30.0)
    bh = getattr(config, "balcony_height_m", 8.0)
    bw = getattr(config, "balcony_width_m", 3.0)
    bd = getattr(config, "balcony_depth_m", 2.0)
    msize = getattr(config, "marker_size_m", 0.25)
    drop_id = getattr(config, "marker_id", 23)

    ob = ObjBuilder()

    # Ground: a large flat plane covering home -> target with margin.
    ob.add_quad("GROUND", (tE / 2, tN / 2), 45.0, 45.0, 0.0, material="ground")

    # The marker sits on a TERRACE whose back wall (the building) is set well back
    # from the marker. This matters: the GPS cruise/search phases can be off by a
    # few metres (the GPS bias), so the building must be far enough behind the
    # marker that a GPS-positioned drone never reaches it -- only the precise
    # vision-guided descent brings the drone right over the marker. (On a real
    # tight balcony you would likewise keep a vision-only standoff from the wall.)
    standoff = 5.0                       # building wall this far behind the marker
    xf = tE + standoff                   # building (east) face
    x_front = tE - 3.5                   # terrace open front edge (toward home)
    terr_cx = (x_front + xf) / 2
    terr_he = (xf - x_front) / 2
    terr_hn = max(bd / 2 + 1.0, 2.0)     # terrace half-depth (N-S)

    ob.add_box("BUILDING", (xf + 1.5, tN, 6.0), (1.5, terr_hn + 2.0, 6.0), material="wall")
    ob.add_box("BALCONY", (terr_cx, tN, bh - 0.1), (terr_he, terr_hn, 0.1), material="balcony")

    # Railing on the three OPEN edges (not the wall side), ~1 m tall. The drone
    # hovers ABOVE the terrace and releases; it must not touch these.
    rh, rt = 0.5, 0.05
    ob.add_box("RAILING_FRONT", (x_front, tN, bh + rh), (rt, terr_hn, rh), material="railing")
    ob.add_box("RAILING_LEFT",  (terr_cx, tN - terr_hn, bh + rh), (terr_he, rt, rh), material="railing")
    ob.add_box("RAILING_RIGHT", (terr_cx, tN + terr_hn, bh + rh), (terr_he, rt, rh), material="railing")

    # A tree obstacle between home and the balcony, OFFSET from the straight
    # cruise line so the nominal mission clears it, but close enough for the
    # LiDAR to see and for the collision/reflex tests to fly head-on at it.
    ox, oy = 24.0, 12.0
    ob.add_box("OBSTACLE_TREE_TRUNK", (ox, oy, 3.0), (0.25, 0.25, 3.0), material="trunk")
    ob.add_box("OBSTACLE_TREE_CANOPY", (ox, oy, 6.5), (1.3, 1.3, 1.3), material="leaves")

    # Marker decals (flat). These are the VISUAL/representation; the authoritative
    # positions are the empties in scene.json. The honest down-camera ArUco
    # pipeline renders the DROP marker from this world position.
    ob.add_quad("MARKER_DROP", (tE, tN), msize / 2, msize / 2, bh + 0.02, material="marker")
    ob.add_quad("MARKER_START", (0.0, 0.0), msize / 2, msize / 2, 0.03, material="marker_start")

    obj_path = os.path.join(HERE, "sample_world.obj")
    mtl_path = os.path.join(HERE, "sample_world.mtl")
    ob.write(obj_path, mtl_path)
    write_mtl(mtl_path)

    scene = {
        "units": "meters",
        "up_axis": "Z",
        "scale": 1.0,
        "obj_file": "sample_world.obj",
        "home": [0.0, 0.0, 0.0],
        "drone_start": [0.0, 0.0, 0.0],
        "drop_target": [float(tE), float(tN), float(bh)],
        "markers": {
            "drop":  {"id": int(drop_id), "size": float(msize), "pos": [float(tE), float(tN), float(bh)]},
            "start": {"id": 7,            "size": float(msize), "pos": [0.0, 0.0, 0.0]},
        },
        # Objects whose CONTACT counts as a crash (ground & flat markers excluded).
        "solid_objects": [
            "BUILDING", "BALCONY", "RAILING_FRONT", "RAILING_LEFT", "RAILING_RIGHT",
            "OBSTACLE_TREE_TRUNK", "OBSTACLE_TREE_CANOPY",
        ],
        "note": "Procedural sample world. Replace with your Blender export for the real world.",
    }
    scene_path = os.path.join(HERE, "scene.json")
    with open(scene_path, "w") as f:
        json.dump(scene, f, indent=2)

    return obj_path, mtl_path, scene_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(HERE))  # project root, for `config`
    obj, mtl, scene = build()
    nv = sum(1 for _ in open(obj) if _.startswith("v "))
    nf = sum(1 for _ in open(obj) if _.startswith("f "))
    print(f"Wrote {os.path.basename(obj)}  ({nv} vertices, {nf} triangles)")
    print(f"Wrote {os.path.basename(mtl)}")
    print(f"Wrote {os.path.basename(scene)}")
