"""
setup_positions.py
==================
Manual setup mode: see and adjust WHERE the drone starts and WHERE it drops.

Use this when marker detection isn't enough, or you just want to place things by
hand. It shows the world as a WIREFRAME (so the points are visible even when they
are inside a building), draws the current DRONE_START and DROP_TARGET as bright
glowing stars ON TOP of everything, lets you orbit around to look, lets you type
new positions, and saves them back to world/scene.json.

Run it:
    python setup_positions.py            # interactive (opens a 3D window if it can)
    python setup_positions.py --no-gui   # no window: saves orbit images you open
    python setup_positions.py --demo      # just render the orbit montage and exit

A normal mission afterwards uses the positions you saved.
"""

from __future__ import annotations
import argparse
import json
import os
import sys

import numpy as np


def _try_gui_backend():
    import matplotlib
    for b in ("MacOSX", "TkAgg", "QtAgg"):
        try:
            matplotlib.use(b)
            return b
        except Exception:
            continue
    matplotlib.use("Agg")
    return "Agg"


def _edges_from_objects(objects):
    """Unique undirected edges (P0, P1) across all objects, for a wireframe."""
    segs = []
    for name, (V, F) in objects.items():
        if len(F) == 0:
            continue
        for tri in F:
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                segs.append((tuple(np.round(V[a], 3)), tuple(np.round(V[b], 3))))
    seen = set(); out = []
    for p0, p1 in segs:
        key = (p0, p1) if p0 <= p1 else (p1, p0)
        if key not in seen:
            seen.add(key); out.append((np.array(p0), np.array(p1)))
    return out


def _draw_axes(ax, world, start, drop, azim, elev, title):
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    ax.clear()
    edges = world._setup_edges
    lc = Line3DCollection(edges, colors=(0.1, 0.7, 0.9, 0.5), linewidths=0.5)
    ax.add_collection3d(lc)
    ax.scatter(*start, s=320, c="#39FF14", marker="*", edgecolors="k",
            depthshade=False, zorder=10, label="DRONE_START")
    ax.scatter(*drop, s=320, c="#FF2DAA", marker="*", edgecolors="k",
            depthshade=False, zorder=10, label="DROP_TARGET")
    allv = np.vstack([np.array(start), np.array(drop)]
                    + [e[0] for e in edges[::20]] + [e[1] for e in edges[::20]])
    lo = allv.min(0); hi = allv.max(0); mid = (lo + hi) / 2; rng = (hi - lo).max() / 2 + 1
    ax.set_xlim(mid[0]-rng, mid[0]+rng); ax.set_ylim(mid[1]-rng, mid[1]+rng)
    ax.set_zlim(0, max(hi[2], 2))
    ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)"); ax.set_zlabel("Up (m)")
    ax.view_init(elev=elev, azim=azim); ax.set_title(title, fontsize=9)
    ax.legend(loc="upper right", fontsize=7)


def render_montage(world, start, drop, out_path):
    """Headless 'orbit': four wireframe views from different angles + glowing points."""
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(11, 8))
    for i, (az, el) in enumerate([(45, 25), (135, 25), (225, 35), (-60, 60)]):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        _draw_axes(ax, world, start, drop, az, el, f"orbit view  az={az} el={el}")
    fig.suptitle("Setup — wireframe world with DRONE_START (green) and DROP_TARGET (pink)",
                fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=90)
    plt.close(fig)
    return out_path


def interactive_window(world, start, drop):
    """Open an orbitable 3D wireframe window (mouse-drag to rotate). Blocks."""
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")
    _draw_axes(ax, world, start, drop, 45, 25,
            "Drag to orbit. Close the window to return to the menu.")
    plt.show()


def save_scene(scene_path, scene, start, drop):
    scene = dict(scene)
    scene["drone_start"] = [round(float(x), 3) for x in start]
    scene["drop_target"] = [round(float(x), 3) for x in drop]
    scene.setdefault("markers", {})
    if "start" in scene["markers"]:
        scene["markers"]["start"]["pos"] = scene["drone_start"]
    if "drop" in scene["markers"]:
        scene["markers"]["drop"]["pos"] = scene["drop_target"]
    scene["home"] = scene["drone_start"]
    with open(scene_path, "w") as f:
        json.dump(scene, f, indent=2)


def _ask_xyz(label, current):
    raw = input(f"  new {label} as 'x y z' (blank = keep {np.round(current,2).tolist()}): ").strip()
    if not raw:
        return current
    try:
        vals = [float(v) for v in raw.replace(",", " ").split()]
        if len(vals) == 3:
            return np.array(vals)
    except ValueError:
        pass
    print("  (couldn't parse three numbers; keeping current)")
    return current


def main():
    parser = argparse.ArgumentParser(description="Manual drone start/drop setup")
    parser.add_argument("--no-gui", action="store_true", help="no window; save orbit images")
    parser.add_argument("--demo", action="store_true", help="render the montage and exit")
    args = parser.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    backend = "Agg" if (args.no_gui or args.demo) else _try_gui_backend()
    from config import CONFIG
    from src.world import World

    world = World(CONFIG, backend="numpy")     # numpy backend -> works without PyBullet
    world._setup_edges = _edges_from_objects(world.objects)
    start = world.drone_start.copy()
    drop = world.drop_target.copy()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    montage = os.path.join(out_dir, "setup_view.png")

    if args.demo:
        render_montage(world, start, drop, montage)
        print(f"Saved orbit montage to {montage}")
        print(f"DRONE_START={np.round(start,2).tolist()}  DROP_TARGET={np.round(drop,2).tolist()}")
        return

    print("\n=== Drone position setup ===")
    while True:
        print(f"\nDRONE_START = {np.round(start,2).tolist()}    DROP_TARGET = {np.round(drop,2).tolist()}")
        if backend != "Agg":
            print("Opening 3D window (drag to orbit; close it to continue)...")
            try:
                interactive_window(world, start, drop)
            except Exception as e:
                print(f"(GUI failed: {e}; saving images instead)")
                print("Saved:", render_montage(world, start, drop, montage))
        else:
            print("Saved orbit views to:", render_montage(world, start, drop, montage))
        print("\nMenu:  [s] set start   [d] set drop   [w] save   [q] quit")
        choice = input("> ").strip().lower()
        if choice == "s":
            start = _ask_xyz("DRONE_START", start)
        elif choice == "d":
            drop = _ask_xyz("DROP_TARGET", drop)
        elif choice == "w":
            save_scene(world.scene_path, world.scene, start, drop)
            print(f"  saved to {world.scene_path}")
        elif choice == "q":
            print("Done.")
            break


if __name__ == "__main__":
    main()
