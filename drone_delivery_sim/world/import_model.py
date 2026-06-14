"""
import_model.py
================
Bring YOUR OWN 3D model into the simulator — no Blender required.

You already have a model as a Wavefront **.obj** file (most 3D tools, including
Blender, SketchUp, Tinkercad, Fusion, and almost every "export to OBJ" button,
can produce one). Point this script at it and it becomes the world the drone
flies in:

    python world/import_model.py  /path/to/my_model.obj

What it does:
  * copies your model into the project's `world/` folder,
  * works out which parts are SOLID (everything counts as a solid obstacle EXCEPT
    objects whose name starts with `GROUND` or `MARKER` — same rule as the Blender
    exporter), so the drone can crash into / navigate around them,
  * writes `world/scene.json` (the active world the simulator loads) with sensible
    starter DRONE_START / DROP_TARGET positions.

Then place the start / landing spots exactly where you want and fly:

    python setup_positions.py      # drag to orbit, type coordinates, save  (you already use this)
    python main.py                 # fly your model, with obstacle-avoiding navigation
    python main.py --feeds         # ...with the live multi-feed window

Units: the simulator works in METRES (1 OBJ unit = 1 metre). If your model came
out sideways, it is probably Y-up — re-run with `--y-up`. Scale with `--scale`.
Go back to the built-in demo world any time with `python main.py --world sample`.
"""

from __future__ import annotations
import argparse
import json
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # project root, so `src` / `config` import


def _is_solid(name: str) -> bool:
    up = name.upper()
    return not (up.startswith("GROUND") or up.startswith("MARKER"))


def import_model(obj_path, up_axis="Z", scale=1.0, drop_id=23, start_id=7,
                marker_size=0.25, dest_name="custom_world.obj"):
    """Copy `obj_path` into world/ and write scene.json so it becomes the world."""
    from src.world import parse_obj_objects, axis_rotation

    obj_path = os.path.abspath(os.path.expanduser(obj_path))
    if not os.path.exists(obj_path):
        raise SystemExit(f"No such file: {obj_path}")

    raw = parse_obj_objects(obj_path)
    if not raw:
        raise SystemExit(
            "No named mesh objects found in the OBJ. Export it with object/group "
            "names (the 'o' lines) so obstacles can be identified individually.")

    # Geometry in the simulator's ENU metres frame, for bounds + sensible defaults.
    R = axis_rotation(up_axis)
    objs = {n: ((V @ R.T) * float(scale), F) for n, (V, F) in raw.items() if len(F)}
    allV = np.vstack([V for V, _ in objs.values()])
    lo = allV.min(0); hi = allV.max(0)
    solids = [n for n in objs if _is_solid(n)]

    # Copy the model into world/ so scene.json's relative obj_file resolves.
    dest = os.path.join(HERE, dest_name)
    if os.path.abspath(dest) != obj_path:
        shutil.copyfile(obj_path, dest)

    # Starter positions: launch just outside the model footprint on the ground;
    # drop at the model's centre, at its top height. You then refine these with
    # `python setup_positions.py` (which writes back to this same scene.json).
    cx, cy = float((lo[0] + hi[0]) / 2), float((lo[1] + hi[1]) / 2)
    start = [float(lo[0] - 3.0), cy, float(lo[2])]
    drop = [cx, cy, float(hi[2])]

    scene = {
        "units": "meters", "up_axis": up_axis.upper(), "scale": float(scale),
        "obj_file": dest_name,
        "home": start, "drone_start": start, "drop_target": drop,
        "markers": {
            "drop":  {"id": int(drop_id),  "size": float(marker_size), "pos": drop},
            "start": {"id": int(start_id), "size": float(marker_size), "pos": start},
        },
        "solid_objects": solids,
        "note": f"Imported from {os.path.basename(obj_path)} via import_model.py.",
    }
    scene_path = os.path.join(HERE, "scene.json")
    with open(scene_path, "w") as f:
        json.dump(scene, f, indent=2)

    span = hi - lo
    print(f"Imported '{os.path.basename(obj_path)}'  ->  {dest}")
    print(f"  {len(objs)} object(s); {len(solids)} solid: "
        f"{', '.join(solids[:8])}{' ...' if len(solids) > 8 else ''}")
    print(f"  model size  : {span[0]:.1f} x {span[1]:.1f} x {span[2]:.1f} m "
        f"(East x North x Up)")
    print(f"  DRONE_START : {[round(v,2) for v in start]}   (a starter guess)")
    print(f"  DROP_TARGET : {[round(v,2) for v in drop]}    (a starter guess)")
    print(f"  wrote {scene_path}")
    print("\nNext:")
    print("  1) python setup_positions.py    # place the start / landing spots, then save")
    print("  2) python main.py               # fly it (obstacle-avoiding navigation is on)")
    print("     python main.py --feeds       # ...with the live multi-feed window")
    print("  (back to the demo world: python main.py --world sample)")
    return scene_path


def main():
    ap = argparse.ArgumentParser(description="Import your own .obj model as the world")
    ap.add_argument("obj", help="path to your model's .obj file")
    ap.add_argument("--y-up", action="store_true",
                    help="the model is Y-up (rotate it to the simulator's Z-up)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiply all coordinates by this (use if not modelled in metres)")
    ap.add_argument("--marker-size", type=float, default=0.25, help="ArUco marker side (m)")
    args = ap.parse_args()
    import_model(args.obj, up_axis=("Y" if args.y_up else "Z"),
                scale=args.scale, marker_size=args.marker_size)


if __name__ == "__main__":
    main()
