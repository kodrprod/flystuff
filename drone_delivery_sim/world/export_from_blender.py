"""
export_from_blender.py
======================
Run this INSIDE Blender (Scripting tab) to export your world for the simulator.
It writes `world_blender.obj` (+ .mtl) and `scene.json` into this project's
`world/` folder, reading the authoritative drone-start and drop positions from two
Empties you place in the scene.

============================  HOW TO USE  ===================================
In Blender, ONE TIME, set real-world scale:
  1. Scene Properties (the printer icon) -> Units -> Unit System = "Metric",
     Unit Scale = 1.000. Now 1 Blender unit = 1 metre.

Build your world to scale (building, balcony, obstacles...). Then:
  2. Add an Empty named exactly  DRONE_START  at the spot the drone launches from
     (Add -> Empty -> Plain Axes, then rename it in the top-right Outliner).
  3. Add an Empty named exactly  DROP_TARGET  at the spot the snack should land
     (e.g. on the balcony floor).
  4. (Optional, for looks) add two image-textured planes for the ArUco markers.
  5. Open the Scripting tab, click "Open", choose THIS file, and edit the two
     lines marked EDIT ME below if your project folder is elsewhere. Then press
     the ▶ "Run Script" button.

It prints the files it wrote. Back in Terminal, run the simulator with
`use_sample_world = False` in config.py (or `python main.py --world blender`).
=============================================================================

Naming convention the exporter uses:
  * Mesh objects named starting with "MARKER" or "GROUND" are NOT collidable.
  * Every other mesh object IS a solid obstacle (touching it = crash).
"""

import json
import os

try:
    import bpy
    from mathutils import Vector
except Exception:  # not running inside Blender
    bpy = None

# ----------------------------- EDIT ME -------------------------------------- #
# Where this project's world/ folder lives. If you opened this script from the
# project, the default below (the script's own folder) is already correct.
PROJECT_WORLD_DIR = os.path.dirname(os.path.abspath(__file__)) \
    if "__file__" in globals() else "/path/to/drone_delivery_sim/world"
DROP_MARKER_ID = 23
START_MARKER_ID = 7
MARKER_SIZE_M = 0.25
# ---------------------------------------------------------------------------- #


def _empty_world_pos(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise RuntimeError(f"Could not find an Empty named '{name}'. Add one (see header).")
    w = ob.matrix_world.translation
    return [round(w.x, 4), round(w.y, 4), round(w.z, 4)]


def export():
    if bpy is None:
        raise SystemExit("This script must be run from inside Blender (Scripting tab).")

    os.makedirs(PROJECT_WORLD_DIR, exist_ok=True)
    obj_path = os.path.join(PROJECT_WORLD_DIR, "world_blender.obj")

    # Verify metric scale (warn loudly if not 1.0).
    us = bpy.context.scene.unit_settings
    if us.system != "METRIC" or abs(us.scale_length - 1.0) > 1e-6:
        print(f"WARNING: Unit System='{us.system}', Unit Scale={us.scale_length}. "
            f"Set Metric + 1.0 so 1 unit = 1 m (see header).")

    # Export OBJ in Blender's native Z-up coordinates (so it matches the Empties).
    try:  # Blender 4.x
        bpy.ops.wm.obj_export(filepath=obj_path, up_axis="Z", forward_axis="Y",
                            export_materials=True, export_selected_objects=False,
                            export_triangulated_mesh=True)
    except Exception:  # Blender 3.x fallback
        bpy.ops.export_scene.obj(filepath=obj_path, axis_up="Z", axis_forward="Y",
                                use_materials=True, use_triangles=True)

    # Solid objects: every mesh except those named MARKER* / GROUND*.
    solids = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        up = ob.name.upper()
        if up.startswith("MARKER") or up.startswith("GROUND"):
            continue
        solids.append(ob.name)

    drop = _empty_world_pos("DROP_TARGET")
    start = _empty_world_pos("DRONE_START")
    scene = {
        "units": "meters", "up_axis": "Z", "scale": 1.0,
        "obj_file": os.path.basename(obj_path),
        "home": start,
        "drone_start": start,
        "drop_target": drop,
        "markers": {
            "drop":  {"id": DROP_MARKER_ID,  "size": MARKER_SIZE_M, "pos": drop},
            "start": {"id": START_MARKER_ID, "size": MARKER_SIZE_M, "pos": start},
        },
        "solid_objects": solids,
        "note": "Exported from Blender.",
    }
    scene_path = os.path.join(PROJECT_WORLD_DIR, "scene.json")
    with open(scene_path, "w") as f:
        json.dump(scene, f, indent=2)

    print("Exported:")
    print("  ", obj_path)
    print("  ", scene_path)
    print(f"  DRONE_START = {start}   DROP_TARGET = {drop}")
    print(f"  {len(solids)} solid object(s): {solids}")
    print("Now set use_sample_world=False in config.py and run the simulator.")


if __name__ == "__main__":
    export()
