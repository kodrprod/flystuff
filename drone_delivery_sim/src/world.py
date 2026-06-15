"""
world.py
========
The 3D world layer: geometry, collision, LiDAR ray-casting and camera rendering.

Backends
--------
ONE interface (`World`), TWO interchangeable backends:

  * PyBulletBackend — the PRIMARY backend (project design). PyBullet in DIRECT
    mode + TinyRenderer (pure CPU, headless-friendly, no macOS OpenGL/GUI issues).
    getClosestPoints for collision, rayTestBatch for LiDAR, getCameraImage for the
    camera feeds. This is what Andrey runs on his Mac (PyBullet ships arm64 wheels).

  * NumpyBackend — a dependency-light FALLBACK (only numpy + matplotlib) used
    automatically when PyBullet is not importable. Implements ray-casting
    (Möller–Trumbore) and collision (point-to-triangle distance) directly, and
    renders the camera feeds with a small matplotlib projector. This keeps the
    whole simulation runnable and TESTABLE anywhere (CI, no-PyBullet machines).

Both backends share the same geometry semantics, so collision and LiDAR behave
equivalently; only camera image fidelity differs.

The drone's MOTION is NOT simulated here — the validated flight model in drone.py
drives it. The drone is a KINEMATIC body whose pose we set every tick. This
protects the existing flight/precision behaviour.

Frame: ENU metres (X=East, Y=North, Z=Up).
"""

from __future__ import annotations
import json
import os
import numpy as np

try:
    import pybullet as _pb
    PYBULLET_AVAILABLE = True
except Exception:
    _pb = None
    PYBULLET_AVAILABLE = False


# --------------------------------------------------------------------------- #
#  OBJ loading (custom parser -> reliable per-object identity)                #
# --------------------------------------------------------------------------- #
def parse_obj_objects(path: str):
    """
    Parse a Wavefront OBJ into named objects: ordered dict
    {object_name: (vertices Nx3 float64, faces Mx3 int)}, triangulated, 0-based.
    Parsed ourselves so the `o` object names survive (needed to report WHICH
    object was hit).
    """
    verts_all = []
    faces = {}
    cur = "default"
    faces[cur] = []

    def fan(idxs):
        for i in range(1, len(idxs) - 1):
            yield (idxs[0], idxs[i], idxs[i + 1])

    with open(path, "r") as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts_all.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("o ") or line.startswith("g "):
                cur = line[2:].strip() or cur
                faces.setdefault(cur, [])
            elif line.startswith("f "):
                idxs = []
                for tok in line.split()[1:]:
                    vi = int(tok.split("/")[0])
                    if vi < 0:
                        vi = len(verts_all) + 1 + vi
                    idxs.append(vi - 1)
                faces.setdefault(cur, [])
                for tri in fan(idxs):
                    faces[cur].append(tri)

    verts_all = np.array(verts_all, dtype=np.float64) if verts_all else np.zeros((0, 3))
    objects = {}
    for name, tris in faces.items():
        if not tris:
            continue
        tris = np.array(tris, dtype=np.int64)
        used = np.unique(tris)
        remap = {old: new for new, old in enumerate(used)}
        objects[name] = (verts_all[used], np.vectorize(remap.get)(tris))
    return objects


def axis_rotation(up_axis: str = "Z") -> np.ndarray:
    """3x3 rotation taking the file's axes into ENU (Z-up). Y-up OBJs need a swap."""
    if up_axis.upper() == "Y":
        return np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float64)
    return np.eye(3, dtype=np.float64)


def load_scene(scene_path: str) -> dict:
    with open(scene_path, "r") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  Pure-numpy geometry (no third-party deps): ray cast + point distance       #
# --------------------------------------------------------------------------- #
def ray_mesh_nearest(origin, direction, V, F, max_range):
    """
    Nearest ray-triangle intersection (Möller–Trumbore), vectorised over all
    triangles for a single ray. Returns (hit, distance, point, face_index).
    """
    if len(F) == 0:
        return False, max_range, None, -1
    A = V[F[:, 0]]; e1 = V[F[:, 1]] - A; e2 = V[F[:, 2]] - A
    d = np.asarray(direction, float)
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-9
    inv = np.zeros_like(det); inv[ok] = 1.0 / det[ok]
    tvec = np.asarray(origin, float) - A
    u = np.einsum("ij,ij->i", tvec, p) * inv
    q = np.cross(tvec, e1)
    v = np.einsum("j,ij->i", d, q) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    valid = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) & (t > 1e-5) & (t <= max_range)
    if not valid.any():
        return False, max_range, None, -1
    ts = np.where(valid, t, np.inf)
    fi = int(np.argmin(ts))
    dist = float(ts[fi])
    return True, dist, np.asarray(origin, float) + d * dist, fi


def point_mesh_distance(point, V, F):
    """
    Unsigned distance from a point to a triangle mesh surface, vectorised over all
    triangles (Ericson's closest-point-on-triangle). Returns (min_dist, face_index).
    """
    if len(F) == 0:
        return np.inf, -1
    P = np.asarray(point, float)
    A = V[F[:, 0]]; B = V[F[:, 1]]; C = V[F[:, 2]]
    ab = B - A; ac = C - A; ap = P - A
    d1 = np.einsum("ij,ij->i", ab, ap); d2 = np.einsum("ij,ij->i", ac, ap)
    bp = P - B; d3 = np.einsum("ij,ij->i", ab, bp); d4 = np.einsum("ij,ij->i", ac, bp)
    cp = P - C; d5 = np.einsum("ij,ij->i", ab, cp); d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    denom = va + vb + vc
    closest = A.copy()
    # vertex/edge/face regions
    m = (d1 <= 0) & (d2 <= 0); closest[m] = A[m]
    m = (d3 >= 0) & (d4 <= d3); closest[m] = B[m]
    m = (d6 >= 0) & (d5 <= d6); closest[m] = C[m]
    denom_e1 = (d1 - d3); denom_e1[denom_e1 == 0] = 1e-12
    vab = d1 / denom_e1
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    closest[m] = A[m] + vab[m, None] * ab[m]
    denom_e2 = (d2 - d6); denom_e2[denom_e2 == 0] = 1e-12
    vac = d2 / denom_e2
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    closest[m] = A[m] + vac[m, None] * ac[m]
    denom_e3 = ((d4 - d3) + (d5 - d6)); denom_e3[denom_e3 == 0] = 1e-12
    vbc = (d4 - d3) / denom_e3
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    closest[m] = B[m] + vbc[m, None] * (C[m] - B[m])
    # interior
    denom_f = denom.copy(); denom_f[denom_f == 0] = 1e-12
    vv = vb / denom_f; ww = vc / denom_f
    interior = ~((d1 <= 0) & (d2 <= 0)) & ~((d3 >= 0) & (d4 <= d3)) & ~((d6 >= 0) & (d5 <= d6)) \
        & ~((vc <= 0) & (d1 >= 0) & (d3 <= 0)) & ~((vb <= 0) & (d2 >= 0) & (d6 <= 0)) \
        & ~((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0))
    closest[interior] = A[interior] + vv[interior, None] * ab[interior] + ww[interior, None] * ac[interior]
    dists = np.linalg.norm(closest - P, axis=1)
    fi = int(np.argmin(dists))
    return float(dists[fi]), fi


def lidar_ray_directions(yaw: float, cfg) -> np.ndarray:
    """Forward fan of unit ray directions in WORLD ENU given the drone yaw."""
    h = np.radians(np.linspace(-cfg.lidar_h_fov_deg / 2, cfg.lidar_h_fov_deg / 2, cfg.lidar_h_rays))
    v = np.radians(np.linspace(-cfg.lidar_v_fov_deg / 2, cfg.lidar_v_fov_deg / 2, cfg.lidar_v_rays))
    dirs = []
    for el in v:
        for az in h:
            ang = yaw + az
            dirs.append((np.cos(el) * np.cos(ang), np.cos(el) * np.sin(ang), np.sin(el)))
    return np.array(dirs, dtype=np.float64)


def _concat_solids(objects, solid_names):
    """Concatenate solid objects into (V, F, face_object_name)."""
    Vs, Fs, names = [], [], []
    off = 0
    for n in solid_names:
        if n not in objects:
            continue
        V, F = objects[n]
        if len(F) == 0:
            continue
        Vs.append(V); Fs.append(F + off); names += [n] * len(F); off += len(V)
    if not Vs:
        return np.zeros((0, 3)), np.zeros((0, 3), int), np.array([])
    return np.vstack(Vs), np.vstack(Fs), np.array(names)


# --------------------------------------------------------------------------- #
#  Backends                                                                   #
# --------------------------------------------------------------------------- #
class _NumpyBackend:
    """Pure-numpy geometry + matplotlib camera feeds (the no-PyBullet fallback)."""

    def __init__(self, objects, solid_names, cfg, rng):
        self.cfg = cfg
        self.objects = objects               # name -> (V, F)
        self.Vc, self.Fc, self.face_object = _concat_solids(objects, solid_names)
        # Per-object AABBs: a cheap, conservative "inside a solid" test so a drone
        # that is buried in geometry counts as a collision even though its unsigned
        # surface distance would be large. (PyBullet's signed contact handles this
        # natively; this is the numpy fallback's equivalent.)
        self.solid_aabbs = []
        for n in solid_names:
            if n in objects and len(objects[n][1]):
                V = objects[n][0]
                self.solid_aabbs.append((n, V.min(0), V.max(0)))
        self.drone_pos = np.zeros(3)
        self.drone_yaw = 0.0

    def set_drone_pose(self, pos, yaw):
        self.drone_pos = np.asarray(pos, float)
        self.drone_yaw = float(yaw)

    def closest_obstacle(self, point, radius):
        P = np.asarray(point, float)
        thresh = radius + self.cfg.collision_margin_m
        # Broad phase over per-object AABBs (cheap). Catches "inside a solid", and
        # lets us skip the expensive per-triangle test when the drone is far from
        # all geometry (the common case on the cruise/return legs).
        best_aabb, best_name = np.inf, None
        for name, lo, hi in self.solid_aabbs:
            c = np.clip(P, lo, hi)
            d = float(np.linalg.norm(P - c))
            if d <= 1e-9:
                return 0.0, name, P            # inside the box -> penetrating
            if d < best_aabb:
                best_aabb, best_name = d, name
        # AABB distance is a lower bound on the true surface distance, so if even
        # the nearest box is comfortably outside the collision band, we are clear.
        if best_aabb > thresh + 0.4:
            return best_aabb + radius, best_name, None
        # Narrow phase: exact unsigned surface distance.
        d, fi = point_mesh_distance(P, self.Vc, self.Fc)
        name = self.face_object[fi] if fi >= 0 else None
        return d, name, None

    def raycast(self, origins, directions, max_range):
        out = []
        for o, d in zip(np.atleast_2d(origins), np.atleast_2d(directions)):
            hit, dist, pt, fi = ray_mesh_nearest(o, d, self.Vc, self.Fc, max_range)
            obj = self.face_object[fi] if (hit and fi >= 0) else None
            out.append({"hit": hit, "distance": dist, "point": pt, "object": obj})
        return out

    def render_camera(self, eye, target, up, fov_deg, w, h, lidar_points=None,
                    wireframe=False, extra_points=None):
        return render_world_matplotlib(self.objects, eye, target, up, fov_deg, w, h,
                                    drone_pos=self.drone_pos, lidar_points=lidar_points,
                                    wireframe=wireframe, extra_points=extra_points)

    def close(self):
        pass


class _PyBulletBackend:
    """PyBullet DIRECT + TinyRenderer backend (primary; used on Andrey's Mac)."""

    def __init__(self, objects, solid_names, cfg, rng):
        self.cfg = cfg
        self.p = _pb
        self.objects = objects
        self.cid = self.p.connect(self.p.DIRECT)
        self.p.setGravity(0, 0, 0, physicsClientId=self.cid)
        self.body_name = {}
        self.solid_ids = []
        for name, (V, F) in objects.items():
            if len(F) == 0:
                continue
            is_solid = name in solid_names
            col = (self.p.createCollisionShape(self.p.GEOM_MESH, vertices=V.tolist(),
                    indices=F.flatten().tolist(), physicsClientId=self.cid) if is_solid else -1)
            vis = self.p.createVisualShape(self.p.GEOM_MESH, vertices=V.tolist(),
                    indices=F.flatten().tolist(), rgbaColor=_color_for(name),
                    physicsClientId=self.cid)
            body = self.p.createMultiBody(baseMass=0, baseCollisionShapeIndex=col,
                    baseVisualShapeIndex=vis, physicsClientId=self.cid)
            self.body_name[body] = name
            if is_solid:
                self.solid_ids.append(body)
        dcol = self.p.createCollisionShape(self.p.GEOM_SPHERE, radius=cfg.drone_radius_m,
                                        physicsClientId=self.cid)
        dvis = self.p.createVisualShape(self.p.GEOM_SPHERE, radius=cfg.drone_radius_m,
                                        rgbaColor=[0.1, 0.1, 0.1, 1], physicsClientId=self.cid)
        self.drone_id = self.p.createMultiBody(baseMass=0, baseCollisionShapeIndex=dcol,
                                            baseVisualShapeIndex=dvis, physicsClientId=self.cid)
        self.drone_pos = np.zeros(3)
        self.drone_yaw = 0.0

    def set_drone_pose(self, pos, yaw):
        self.drone_pos = np.asarray(pos, float)
        self.drone_yaw = float(yaw)
        q = self.p.getQuaternionFromEuler([0, 0, yaw])
        self.p.resetBasePositionAndOrientation(self.drone_id, pos.tolist(), q,
                                            physicsClientId=self.cid)

    def closest_obstacle(self, point, radius):
        best = (np.inf, None, None)
        for bid in self.solid_ids:
            cps = self.p.getClosestPoints(self.drone_id, bid, distance=10.0,
                                        physicsClientId=self.cid)
            for c in cps:
                d = c[8] + radius   # contactDistance (surface-surface) + r => to centre
                if d < best[0]:
                    best = (d, self.body_name[bid], np.array(c[6]))
        return best

    def raycast(self, origins, directions, max_range):
        origins = np.atleast_2d(origins).astype(np.float64)
        directions = np.atleast_2d(directions).astype(np.float64)
        res = self.p.rayTestBatch(origins.tolist(), (origins + directions * max_range).tolist(),
                                physicsClientId=self.cid)
        out = []
        for r in res:
            obj_id, _link, frac, hitpos, _n = r
            if obj_id >= 0 and obj_id in self.body_name:
                out.append({"hit": True, "distance": float(frac * max_range),
                            "point": np.array(hitpos), "object": self.body_name[obj_id]})
            else:
                out.append({"hit": False, "distance": max_range, "point": None, "object": None})
        return out

    def render_camera(self, eye, target, up, fov_deg, w, h, lidar_points=None,
                    wireframe=False, extra_points=None):
        view = self.p.computeViewMatrix(list(eye), list(target), list(up))
        proj = self.p.computeProjectionMatrixFOV(fov_deg, w / h, 0.05, 80.0)
        _, _, rgba, _, _ = self.p.getCameraImage(w, h, view, proj,
                            renderer=self.p.ER_TINY_RENDERER, physicsClientId=self.cid)
        rgb = np.reshape(np.array(rgba, dtype=np.uint8), (h, w, 4))[:, :, :3]
        img = np.ascontiguousarray(rgb[:, :, ::-1])  # BGR
        # Overlay LiDAR hits / glowing points (cheap, keeps both backends consistent).
        if (lidar_points is not None) or extra_points:
            img = _overlay_points(img, eye, target, up, fov_deg, w, h, lidar_points, extra_points)
        return img

    def close(self):
        try:
            self.p.disconnect(physicsClientId=self.cid)
        except Exception:
            pass


# --------------------------------------------------------------------------- #
#  World facade                                                               #
# --------------------------------------------------------------------------- #
class World:
    """Loads a scene + OBJ and exposes collision / LiDAR / camera over a backend."""

    def __init__(self, config, rng=None, scene_path=None, backend=None):
        self.cfg = config
        self.rng = rng if rng is not None else np.random.default_rng(config.seed)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wdir = os.path.join(root, config.world_dir)
        self.scene_path = scene_path or os.path.join(wdir, config.world_scene_file)
        # Auto-generate the bundled sample world if it is missing (so the sim always
        # has something to load out of the box). A Blender export is never clobbered.
        if not os.path.exists(self.scene_path) and config.use_sample_world:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "make_sample_world", os.path.join(wdir, "make_sample_world.py"))
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            mod.build(config)
        self.scene = load_scene(self.scene_path)

        obj_path = os.path.join(wdir, self.scene.get("obj_file", "sample_world.obj"))
        R = axis_rotation(self.scene.get("up_axis", "Z"))
        scale = float(self.scene.get("scale", 1.0))
        raw = parse_obj_objects(obj_path)
        self.objects = {n: ((V @ R.T) * scale, F) for n, (V, F) in raw.items()}
        self.solid_names = self.scene.get("solid_objects", [])

        self.drone_start = np.array(self.scene["drone_start"], float)
        self.drop_target = np.array(self.scene["drop_target"], float)
        self.home = np.array(self.scene.get("home", [0, 0, 0]), float)
        self.markers = self.scene.get("markers", {})

        choice = (backend or config.world_backend).lower()
        if choice in ("auto",):
            choice = "pybullet" if PYBULLET_AVAILABLE else "numpy"
        if choice == "pybullet" and not PYBULLET_AVAILABLE:
            choice = "numpy"
        if choice in ("trimesh", "cpu"):
            choice = "numpy"
        self.backend_name = choice
        BK = _PyBulletBackend if choice == "pybullet" else _NumpyBackend
        self.backend = BK(self.objects, self.solid_names, config, self.rng)

    def set_drone_pose(self, pos, yaw=0.0):
        self.backend.set_drone_pose(np.asarray(pos, float), float(yaw))

    def check_collision(self):
        """Return (collided, object_name, point, surface_gap_m)."""
        r = self.cfg.drone_radius_m
        d_center, name, pt = self.backend.closest_obstacle(self.backend.drone_pos, r)
        surface_gap = d_center - r
        return (surface_gap <= self.cfg.collision_margin_m), name, pt, surface_gap

    def lidar_scan(self, pos=None, yaw=None):
        cfg = self.cfg
        pos = self.backend.drone_pos if pos is None else np.asarray(pos, float)
        yaw = self.backend.drone_yaw if yaw is None else float(yaw)
        dirs = lidar_ray_directions(yaw, cfg)
        hits = self.backend.raycast(np.tile(pos, (len(dirs), 1)), dirs, cfg.lidar_range_m)
        dists = np.array([h["distance"] for h in hits], float)
        if cfg.lidar_noise_m > 0:
            dists = np.clip(dists + self.rng.normal(0, cfg.lidar_noise_m, len(dists)), 0, cfg.lidar_range_m)
        hitmask = np.array([h["hit"] for h in hits])
        return {"directions": dirs, "distances": dists, "points": [h["point"] for h in hits],
                "objects": [h["object"] for h in hits], "hit": hitmask, "origin": pos, "yaw": yaw,
                "min_distance": float(dists[hitmask].min()) if hitmask.any() else cfg.lidar_range_m}

    def forward_clear_distance(self, pos=None, yaw=None):
        scan = self.lidar_scan(pos, yaw)
        yaw = scan["yaw"]; fwd = np.array([np.cos(yaw), np.sin(yaw), 0.0])
        best = self.cfg.lidar_range_m
        for d, dirv, hit in zip(scan["distances"], scan["directions"], scan["hit"]):
            if hit and np.dot(dirv, fwd) > 0.82:
                best = min(best, d)
        return best

    def horizontal_scan(self, pos=None, heading=0.0, fov_deg=None, n_rays=None,
                        max_range=None):
        """
        Realistic forward LiDAR for NAVIGATION: a single HORIZONTAL fan of distance
        rays centred on the travel heading, at the drone's current altitude. Returns
        the world bearing + open distance of each ray. This is the ONLY spatial input
        the sensor-only navigator (src/avoidance.py) is allowed to use — it never
        sees object positions, just these distances, exactly like a real LiDAR.
        """
        cfg = self.cfg
        pos = self.backend.drone_pos if pos is None else np.asarray(pos, float)
        fov = cfg.lidar_h_fov_deg if fov_deg is None else float(fov_deg)
        n = cfg.lidar_h_rays if n_rays is None else int(n_rays)
        mr = cfg.lidar_range_m if max_range is None else float(max_range)
        if fov >= 359.9:        # full sweep: evenly spaced, no duplicated endpoint
            bearings = float(heading) + np.radians(np.linspace(0.0, 360.0, n, endpoint=False))
        else:
            bearings = float(heading) + np.radians(np.linspace(-fov / 2, fov / 2, n))
        dirs = np.stack([np.cos(bearings), np.sin(bearings), np.zeros(n)], axis=1)
        hits = self.backend.raycast(np.tile(pos, (n, 1)), dirs, mr)
        dists = np.array([h["distance"] for h in hits], float)
        hit = np.array([h["hit"] for h in hits])
        if cfg.lidar_noise_m > 0:
            dists = np.clip(dists + self.rng.normal(0, cfg.lidar_noise_m, n), 0, mr)
        clear = np.where(hit, dists, mr)
        return {"bearings": bearings, "clear": clear, "dists": dists, "hit": hit,
                "origin": pos, "heading": float(heading)}

    def elevation_fan(self, pos=None, goal_bearing=0.0, n_el=None, max_range=None):
        """
        The VERTICAL part of the 3-D LiDAR: a forward fan, around the travel/goal
        bearing, angled UP (can I clear it by going over?), slightly DOWN (am I high
        enough above its top, with body margin?), and steeply DOWN (room to duck
        under?). Cast on demand (only when the horizontal ring says something is
        ahead), so open-air cruise stays cheap. Distances only -- no map.
        """
        cfg = self.cfg
        pos = self.backend.drone_pos if pos is None else np.asarray(pos, float)
        mr = cfg.lidar_range_m if max_range is None else float(max_range)
        n_el = cfg.avoid_el_rays if n_el is None else int(n_el)
        az_off = np.radians(np.linspace(-40.0, 40.0, 5))
        el_up = np.radians(np.linspace(25.0, 80.0, max(1, n_el)))        # over
        el_margin = np.radians([-6.0, -12.0])                            # body clearance
        el_duck = np.radians([-30.0, -55.0])                            # under
        el_ang = np.concatenate([el_up, el_margin, el_duck])
        fa, fe = np.meshgrid(az_off, el_ang)
        az = float(goal_bearing) + fa.ravel()
        el = fe.ravel()
        dirs = np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], axis=1)
        hits = self.backend.raycast(np.tile(pos, (len(az), 1)), dirs, mr)
        dists = np.array([h["distance"] for h in hits], float)
        hit = np.array([h["hit"] for h in hits])
        if cfg.lidar_noise_m > 0:
            dists = np.clip(dists + self.rng.normal(0, cfg.lidar_noise_m, len(az)), 0, mr)
        clear = np.where(hit, dists, mr)
        return {"az": az, "el": el, "clear": clear, "origin": pos}

    def ring_scan(self, pos=None, n_rays=24, max_range=None):
        """
        A horizontal 360-degree distance probe around the drone (at its altitude).
        Used by the reactive obstacle-avoidance layer to steer around things on ANY
        side (the forward-only reflex/LiDAR can't see a wall the drone drifts into
        sideways). Returns per-ray directions, distances and hit flags.
        """
        pos = self.backend.drone_pos if pos is None else np.asarray(pos, float)
        mr = self.cfg.lidar_range_m if max_range is None else float(max_range)
        ang = np.linspace(0.0, 2.0 * np.pi, n_rays, endpoint=False)
        dirs = np.stack([np.cos(ang), np.sin(ang), np.zeros(n_rays)], axis=1)
        hits = self.backend.raycast(np.tile(pos, (n_rays, 1)), dirs, mr)
        dists = np.array([h["distance"] for h in hits], float)
        return {"dirs": dirs, "dists": dists,
                "hit": np.array([h["hit"] for h in hits]),
                "points": [h["point"] for h in hits], "origin": pos}

    def reflex_distance(self, pos, heading, half_angle_deg=18.0, n=5):
        """
        CHEAP forward obstacle probe (a few rays) along the travel heading — used
        by the onboard safety reflex every tick. Much lighter than a full scan.
        """
        a = np.radians(np.linspace(-half_angle_deg, half_angle_deg, n))
        dirs = np.array([[np.cos(heading + da), np.sin(heading + da), 0.0] for da in a])
        hits = self.backend.raycast(np.tile(np.asarray(pos, float), (n, 1)), dirs,
                                    self.cfg.lidar_range_m)
        return min(h["distance"] for h in hits)

    def render_camera(self, eye, target, up=(0, 0, 1), fov_deg=70.0, w=320, h=240,
                    lidar_points=None, wireframe=False, extra_points=None):
        return self.backend.render_camera(np.asarray(eye, float), np.asarray(target, float),
                    np.asarray(up, float), fov_deg, w, h, lidar_points=lidar_points,
                    wireframe=wireframe, extra_points=extra_points)

    def front_camera(self):
        cfg = self.cfg
        pos = self.backend.drone_pos; yaw = self.backend.drone_yaw
        fwd = np.array([np.cos(yaw), np.sin(yaw), 0.0])
        return self.render_camera(pos + fwd * (cfg.drone_radius_m + 0.05), pos + fwd * 5.0,
                    (0, 0, 1), cfg.front_cam_fov_deg, cfg.front_cam_width, cfg.front_cam_height)

    def chase_camera(self, lidar_points=None):
        cfg = self.cfg
        pos = self.backend.drone_pos; yaw = self.backend.drone_yaw
        back = np.array([np.cos(yaw), np.sin(yaw), 0.0])
        eye = pos - back * cfg.chase_cam_back_m + np.array([0, 0, cfg.chase_cam_up_m])
        return self.render_camera(eye, pos, (0, 0, 1), cfg.chase_cam_fov_deg,
                    cfg.chase_cam_width, cfg.chase_cam_height, lidar_points=lidar_points)

    def close(self):
        self.backend.close()


# --------------------------------------------------------------------------- #
#  Rendering helpers                                                          #
# --------------------------------------------------------------------------- #
def _color_for(name: str):
    name = name.upper()
    table = [("GROUND", (0.55, 0.60, 0.52)), ("BUILDING", (0.72, 0.72, 0.74)),
            ("BALCONY", (0.66, 0.60, 0.52)), ("RAIL", (0.45, 0.45, 0.48)),
            ("TRUNK", (0.40, 0.27, 0.16)), ("CANOPY", (0.25, 0.50, 0.23)),
            ("MARKER_START", (0.20, 0.45, 0.90)), ("MARKER", (0.95, 0.95, 0.95))]
    for key, c in table:
        if key in name:
            return [c[0], c[1], c[2], 1.0]
    return [0.6, 0.6, 0.62, 1.0]


def _project(P, eye, r, u, f, focal, w, h):
    rel = np.atleast_2d(P) - eye
    xc = rel @ r; yc = rel @ u; zc = rel @ f
    px = w / 2 + focal * xc / np.where(np.abs(zc) < 1e-6, 1e-6, zc)
    py = h / 2 - focal * yc / np.where(np.abs(zc) < 1e-6, 1e-6, zc)
    return px, py, zc


def _basis(eye, target, up):
    f = np.asarray(target, float) - np.asarray(eye, float); f /= (np.linalg.norm(f) + 1e-9)
    r = np.cross(f, up); r /= (np.linalg.norm(r) + 1e-9)
    u = np.cross(r, f)
    return f, r, u


def _overlay_points(img, eye, target, up, fov_deg, w, h, lidar_points, extra_points):
    """Draw red LiDAR hits and glowing star points onto an existing BGR image."""
    import cv2
    eye = np.asarray(eye, float)
    f, r, u = _basis(eye, target, up)
    focal = (w / 2) / np.tan(np.radians(fov_deg) / 2)
    if lidar_points is not None:
        pts = [p for p in lidar_points if p is not None]
        if pts:
            px, py, zc = _project(np.array(pts), eye, r, u, f, focal, w, h)
            for x, y, z in zip(px, py, zc):
                if z > 0.05 and 0 <= x < w and 0 <= y < h:
                    cv2.circle(img, (int(x), int(y)), 3, (0, 0, 255), -1)
    if extra_points:
        for (P, col, _label) in extra_points:
            px, py, zc = _project(P, eye, r, u, f, focal, w, h)
            if zc[0] > 0.05:
                bgr = (int(col[2] * 255), int(col[1] * 255), int(col[0] * 255))
                cv2.drawMarker(img, (int(px[0]), int(py[0])), bgr, cv2.MARKER_STAR, 22, 2)
    return img


def render_world_matplotlib(objects, eye, target, up, fov_deg, w, h,
                            drone_pos=None, lidar_points=None, wireframe=False,
                            extra_points=None):
    """
    Painter's-algorithm renderer (matplotlib/Agg). Projects triangles with a
    pinhole camera, depth-sorts and fills them. Good enough for the 3rd-person /
    front feeds and the wireframe setup view without PyBullet. Returns HxWx3 BGR.
    `objects` is {name: (V, F)}.
    """
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.collections import PolyCollection

    eye = np.asarray(eye, float)
    f, r, u = _basis(eye, target, up)
    focal = (w / 2) / np.tan(np.radians(fov_deg) / 2)
    light = np.array([0.3, 0.2, 1.0]); light /= np.linalg.norm(light)

    polys, colors, depths = [], [], []
    for name, (V, F) in objects.items():
        if len(F) == 0:
            continue
        base = np.array(_color_for(name)[:3])
        px, py, zc = _project(V, eye, r, u, f, focal, w, h)
        for tri in F:
            z3 = zc[tri]
            if np.any(z3 <= 0.05):
                continue
            n = np.cross(V[tri[1]] - V[tri[0]], V[tri[2]] - V[tri[0]])
            nn = np.linalg.norm(n)
            shade = 0.55 + 0.45 * abs(np.dot(n / nn, light)) if nn > 1e-9 else 0.7
            polys.append(np.column_stack([px[tri], py[tri]]))
            colors.append(np.clip(base * shade, 0, 1))
            depths.append(z3.mean())

    fig = Figure(figsize=(w / 100, h / 100), dpi=100); FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis("off")
    ax.set_facecolor((0.75, 0.85, 0.95))
    if polys:
        order = np.argsort(depths)[::-1]
        pc = PolyCollection([polys[i] for i in order],
                            facecolors=("none" if wireframe else [colors[i] for i in order]),
                            edgecolors=((0.1, 0.7, 0.9) if wireframe else "k"),
                            linewidths=(0.7 if wireframe else 0.2))
        ax.add_collection(pc)
    if lidar_points is not None:
        pts = [p for p in lidar_points if p is not None]
        if pts:
            px, py, zc = _project(np.array(pts), eye, r, u, f, focal, w, h)
            m = zc > 0.05
            ax.scatter(px[m], py[m], s=12, c="red", marker="o", zorder=5)
    if extra_points:
        for (P, col, _label) in extra_points:
            px, py, zc = _project(P, eye, r, u, f, focal, w, h)
            if zc[0] > 0.05:
                ax.scatter([px[0]], [py[0]], s=260, c=[col], marker="*",
                        edgecolors="white", linewidths=1.5, zorder=10)
    if drone_pos is not None:
        px, py, zc = _project(drone_pos, eye, r, u, f, focal, w, h)
        if zc[0] > 0.05:
            ax.scatter([px[0]], [py[0]], s=110, c="black", marker="o", zorder=8)
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    return np.ascontiguousarray(buf[:, :, ::-1])
