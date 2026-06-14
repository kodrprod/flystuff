"""
planner.py
==========
Global path planning so the drone NAVIGATES AROUND obstacles instead of flying a
straight line into them.

Why this exists
---------------
Before this, the cruise/return legs flew a dead-straight line to the target and the
only obstacle handling was the onboard LiDAR *reflex*, which can merely HALT the
drone (it cannot route around anything). So if you moved DRONE_START so that a tree
or a building wall sat between the start and the balcony, the drone would stall at —
or crash into — the obstacle. This module fixes that: it plans a clear path.

How it works (matches the real onboard/ground split)
-----------------------------------------------------
Path planning is a GROUND-station task (see compute.py's GROUND_TASKS), run once up
front from the world map — exactly like a real delivery drone where the laptop plans
the route and the Pi just flies it while the local reflex guards against surprises.

  1. Build a 2-D occupancy grid from the world's SOLID objects, considered at the
     flight altitude: an object only blocks cells if its height span reaches the
     altitude the drone will fly at (so the drone is allowed to fly OVER low things
     like a tree, and must go AROUND tall things like a building).
  2. Inflate every obstacle by the drone radius + a safety margin (configurable),
     so the planned path keeps real clearance.
  3. A* search (8-connected, no corner-cutting) finds the shortest free path.
  4. ADAPTIVE ALTITUDE: if no path exists at the base cruise altitude, the planner
     raises the altitude in steps and replans — i.e. it will fly *over* an obstacle
     if going around is impossible, preferring the lowest altitude that works.
  5. The grid path is smoothed by line-of-sight "string pulling" into a short list
     of waypoints the mission flies through.

Everything is deterministic (no RNG), in the project ENU metres frame.
"""

from __future__ import annotations
import heapq
import numpy as np


# --------------------------------------------------------------------------- #
#  Obstacle geometry                                                          #
# --------------------------------------------------------------------------- #
def solid_aabbs(world) -> dict:
    """{name: (min_xyz, max_xyz)} for every SOLID object in the world."""
    out = {}
    for name in getattr(world, "solid_names", []):
        if name in world.objects and len(world.objects[name][1]):
            V = world.objects[name][0]
            out[name] = (V.min(0), V.max(0))
    return out


class OccupancyGrid:
    """A 2-D obstacle grid of the world as seen at one flight altitude."""

    def __init__(self, aabbs, cfg, altitude, extra_xy=(), cell=0.6, pad=8.0,
                inflation=None, max_cells=420):
        self.cfg = cfg
        self.altitude = float(altitude)
        # Vertical clearance: an object is "in the way" at this altitude if the
        # drone sphere (radius + margin) plus a small buffer would touch its z-span.
        vclear = cfg.drone_radius_m + cfg.collision_margin_m + 0.4
        # Horizontal clearance kept from every obstacle. The extra `nav_clearance_m`
        # buffer absorbs the GPS bias the cruise leg flies on (a few metres), so the
        # *actually flown* path keeps real distance even though it is GPS-guided.
        self.inflation = float(inflation if inflation is not None
                            else cfg.drone_radius_m + cfg.collision_margin_m
                            + getattr(cfg, "nav_clearance_m", 0.6))

        # Which obstacles block at THIS altitude (xy AABBs only).
        self.blockers = []
        all_xy = [np.asarray(p, float)[:2] for p in extra_xy]
        for _name, (lo, hi) in aabbs.items():
            all_xy.append(lo[:2]); all_xy.append(hi[:2])
            if (lo[2] - vclear) <= self.altitude <= (hi[2] + vclear):
                self.blockers.append((lo[:2].astype(float), hi[:2].astype(float)))

        # Grid bounds cover all obstacles + the start/goal, with padding.
        pts = np.array(all_xy) if all_xy else np.zeros((1, 2))
        self.xmin, self.ymin = (pts.min(0) - pad)
        xmax, ymax = (pts.max(0) + pad)

        # Choose a cell size that keeps the grid within max_cells per axis.
        span = max(xmax - self.xmin, ymax - self.ymin, 1.0)
        self.cell = max(cell, span / max_cells)
        self.nx = int(np.ceil((xmax - self.xmin) / self.cell)) + 1
        self.ny = int(np.ceil((ymax - self.ymin) / self.cell)) + 1

        # Block cells whose centre is within `inflation` of any obstacle AABB
        # (point-to-rectangle distance -> nicely rounded corners).
        cx = self.xmin + (np.arange(self.nx) + 0.5) * self.cell
        cy = self.ymin + (np.arange(self.ny) + 0.5) * self.cell
        XX, YY = np.meshgrid(cx, cy)                       # shape (ny, nx)
        self.blocked = np.zeros((self.ny, self.nx), dtype=bool)
        for lo, hi in self.blockers:
            dx = np.maximum.reduce([lo[0] - XX, np.zeros_like(XX), XX - hi[0]])
            dy = np.maximum.reduce([lo[1] - YY, np.zeros_like(YY), YY - hi[1]])
            self.blocked |= (dx * dx + dy * dy) <= (self.inflation ** 2)

    # -- index <-> world helpers -------------------------------------------- #
    def cell_of(self, x, y):
        i = int(np.clip(np.floor((x - self.xmin) / self.cell), 0, self.nx - 1))
        j = int(np.clip(np.floor((y - self.ymin) / self.cell), 0, self.ny - 1))
        return i, j

    def center(self, i, j):
        return (self.xmin + (i + 0.5) * self.cell, self.ymin + (j + 0.5) * self.cell)

    def free(self, i, j) -> bool:
        return 0 <= i < self.nx and 0 <= j < self.ny and not self.blocked[j, i]

    def nearest_free(self, i, j, max_ring=40):
        """Nearest free cell to (i, j) by expanding rings (handles a blocked start/goal)."""
        if self.free(i, j):
            return (i, j)
        for r in range(1, max_ring + 1):
            best = None; best_d = None
            for di in range(-r, r + 1):
                for dj in (-r, r) if abs(di) != r else range(-r, r + 1):
                    ci, cj = i + di, j + dj
                    if self.free(ci, cj):
                        d = di * di + dj * dj
                        if best_d is None or d < best_d:
                            best_d, best = d, (ci, cj)
            if best is not None:
                return best
        return None

    def segment_clear(self, p0, p1) -> bool:
        """True if the straight segment p0->p1 stays in free cells (for smoothing)."""
        p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
        dist = float(np.linalg.norm(p1 - p0))
        n = max(2, int(dist / (self.cell * 0.5)) + 1)
        for t in np.linspace(0.0, 1.0, n):
            x, y = p0 + (p1 - p0) * t
            if not self.free(*self.cell_of(x, y)):
                return False
        return True


# --------------------------------------------------------------------------- #
#  A* over the grid                                                           #
# --------------------------------------------------------------------------- #
_NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)]
_SQRT2 = float(np.sqrt(2.0))


def astar(grid: OccupancyGrid, start, goal):
    """Return a list of (i, j) cells from start to goal, or None if unreachable."""
    if not grid.free(*start) or not grid.free(*goal):
        return None
    gx, gy = goal
    def h(i, j):
        return float(np.hypot(i - gx, j - gy))
    open_heap = [(h(*start), 0.0, start)]
    came = {}
    gscore = {start: 0.0}
    closed = set()
    while open_heap:
        _f, g, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]; path.append(cur)
            return path[::-1]
        if cur in closed:
            continue
        closed.add(cur)
        ci, cj = cur
        for di, dj in _NEIGHBORS:
            ni, nj = ci + di, cj + dj
            if not grid.free(ni, nj):
                continue
            if di and dj:  # no diagonal corner-cutting through a blocked cell
                if not (grid.free(ci + di, cj) and grid.free(ci, cj + dj)):
                    continue
            step = _SQRT2 if (di and dj) else 1.0
            ng = g + step
            nb = (ni, nj)
            if ng < gscore.get(nb, np.inf):
                gscore[nb] = ng
                came[nb] = cur
                heapq.heappush(open_heap, (ng + h(ni, nj), ng, nb))
    return None


def _smooth(grid: OccupancyGrid, pts):
    """Line-of-sight 'string pulling': keep only waypoints we must turn at."""
    if len(pts) <= 2:
        return pts
    out = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1 and not grid.segment_clear(pts[i], pts[j]):
            j -= 1
        out.append(pts[j])
        i = j
    return out


# --------------------------------------------------------------------------- #
#  Public entry point                                                         #
# --------------------------------------------------------------------------- #
def plan_route(world, start_xy, goal_xy, cfg, base_alt,
            max_extra_climb=None, alt_step=2.0):
    """
    Plan a clear horizontal route from start_xy to goal_xy.

    Returns a dict:
      waypoints  : list of (x, y) np arrays, start_xy .. goal_xy (>= 2 points)
      altitude   : the flight altitude the route is valid at (>= base_alt)
      ok         : True if a collision-free route was found
      detoured   : True if the route is not a straight shot at base_alt
                (i.e. the planner actually had to avoid something)
      reason     : short human-readable note
    """
    start_xy = np.asarray(start_xy, float)[:2]
    goal_xy = np.asarray(goal_xy, float)[:2]
    aabbs = solid_aabbs(world)
    if max_extra_climb is None:
        max_extra_climb = getattr(cfg, "nav_max_climb_m", 14.0)

    n_steps = int(round(max_extra_climb / alt_step)) + 1
    for k in range(n_steps):
        alt = float(base_alt) + k * alt_step
        grid = OccupancyGrid(aabbs, cfg, alt, extra_xy=[start_xy, goal_xy])
        s = grid.nearest_free(*grid.cell_of(*start_xy))
        g = grid.nearest_free(*grid.cell_of(*goal_xy))
        if s is None or g is None:
            continue
        cells = astar(grid, s, g)
        if cells is None:
            continue
        pts = [np.array(grid.center(i, j)) for (i, j) in cells]
        pts[0] = start_xy.copy()
        pts[-1] = goal_xy.copy()
        pts = _smooth(grid, pts)
        detoured = (k > 0) or (len(pts) > 2) or (not grid.segment_clear(start_xy, goal_xy))
        reason = ("straight (clear)" if not detoured
                else f"routed around obstacles at {alt:.0f} m"
                if k == 0 else f"climbed to {alt:.0f} m to clear obstacles")
        return {"waypoints": pts, "altitude": alt, "ok": True,
                "detoured": detoured, "reason": reason}

    # No route at any altitude tried -> fall back to a straight line (the onboard
    # reflex remains the last line of defence). Surfaced so callers can warn.
    return {"waypoints": [start_xy.copy(), goal_xy.copy()], "altitude": float(base_alt),
            "ok": False, "detoured": False,
            "reason": "no clear route found — flying direct (reflex only)"}
