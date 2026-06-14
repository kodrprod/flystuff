"""
camera_sim.py
=============
A synthetic DOWNWARD camera. Given the drone's pose, it renders a realistic
640x480 image of the ArUco marker lying on the balcony floor, EXACTLY as a real
down-facing camera would see it.

Why this matters: the marker's apparent size shrinks with height and shifts with
horizontal offset according to a real pinhole-camera projection. The intrinsics
(focal length, principal point) are SHARED with vision.py via config.py, so when
vision.py later runs solvePnP on this image and recovers a height, that height is
geometrically honest -- it genuinely comes from the pixels, not from cheating.

Pipeline per frame:
  1. Build the camera extrinsics for a near-nadir (down-looking) view.
  2. Project the four corners of the printed marker "paper" into the image with
     cv2.projectPoints (the same K used by the detector).
  3. Warp the canonical marker bitmap onto those four points (cv2.warpPerspective).
  4. Composite over a textured background and add blur, noise and brightness
     variation so detection is realistic rather than trivially perfect.

Realism knobs (blur, noise, tilt, background) all live in config.py.
"""

from __future__ import annotations
import numpy as np
import cv2

from config import CONFIG
from src.vision import get_aruco_dictionary, generate_marker_image


def _rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float64)


def _rot_y(b):
    c, s = np.cos(b), np.sin(b)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float64)


class CameraSim:
    """Renders synthetic downward-camera frames of the balcony marker."""

    # Nadir world->camera rotation: camera looks straight down.
    #   camera X = world East, camera Y = world South, camera Z = world Down.
    _R_NADIR = np.array([[1.0, 0.0, 0.0],
                        [0.0, -1.0, 0.0],
                        [0.0, 0.0, -1.0]], dtype=np.float64)

    def __init__(self, config=CONFIG, rng: np.random.Generator | None = None):
        self.cfg = config
        self.rng = rng if rng is not None else np.random.default_rng(config.seed)
        self.K = config.camera_matrix
        self.dist = config.dist_coeffs
        self.W, self.H = config.image_width, config.image_height

        # Build the marker bitmap once: NxN code + a white "paper" quiet zone.
        N = 240
        self.pad = int(N * 0.25)
        dictionary = get_aruco_dictionary(config.marker_dict)
        marker = generate_marker_image(dictionary, config.marker_id, N)  # NxN, 0/255
        T = N + 2 * self.pad
        paper = np.full((T, T), 255, dtype=np.uint8)
        paper[self.pad:self.pad + N, self.pad:self.pad + N] = marker
        self.bitmap = cv2.cvtColor(paper, cv2.COLOR_GRAY2BGR)
        self.T = T

        # Source corners of the FULL paper bitmap (top-left, top-right, BR, BL).
        self.src_corners = np.array([[0, 0], [T - 1, 0], [T - 1, T - 1], [0, T - 1]],
                                    dtype=np.float64)

        # World corners of that paper square (side scaled by the quiet zone),
        # lying flat on the balcony, axis-aligned to East/North.
        L = config.marker_size_m * (T / N)
        half = L / 2.0
        mE, mN, bh = config.marker_east_m, config.marker_north_m, config.balcony_height_m
        self.world_corners = np.array([
            [mE - half, mN + half, bh],   # NW  -> bitmap top-left
            [mE + half, mN + half, bh],   # NE  -> bitmap top-right
            [mE + half, mN - half, bh],   # SE  -> bitmap bottom-right
            [mE - half, mN - half, bh],   # SW  -> bitmap bottom-left
        ], dtype=np.float64)

        self._background = self._make_background()

    # ------------------------------------------------------------------ #
    def _make_background(self) -> np.ndarray:
        """A low-frequency textured backdrop (concrete-ish), not a plain colour."""
        small = self.rng.integers(80, 150, (self.H // 40, self.W // 40, 3), dtype=np.uint8)
        bg = cv2.resize(small, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        # Gentle diagonal brightness gradient for extra realism.
        gx = np.linspace(-12, 12, self.W)
        gy = np.linspace(-12, 12, self.H)
        grad = (gx[None, :] + gy[:, None]).astype(np.float64)
        bg = np.clip(bg.astype(np.float64) + grad[..., None], 0, 255).astype(np.uint8)
        return bg

    def _extrinsics(self, cam_pos: np.ndarray):
        """Return (rvec, tvec, R) for a near-nadir camera at cam_pos."""
        cfg = self.cfg
        if cfg.camera_tilt_deg > 0:
            amp = np.radians(cfg.camera_tilt_deg)
            a = self.rng.uniform(-amp, amp)
            b = self.rng.uniform(-amp, amp)
            R = _rot_x(a) @ _rot_y(b) @ self._R_NADIR
        else:
            R = self._R_NADIR
        tvec = -R @ cam_pos
        rvec, _ = cv2.Rodrigues(R)
        return rvec, tvec.reshape(3, 1), R

    def render(self, cam_pos: np.ndarray) -> np.ndarray:
        """Render the downward-camera frame for a drone at `cam_pos` (ENU meters)."""
        cam_pos = np.asarray(cam_pos, dtype=np.float64)
        img = self._background.copy()

        rvec, tvec, R = self._extrinsics(cam_pos)

        # Reject if any marker corner is not in front of the camera.
        cam_pts = (R @ (self.world_corners - cam_pos).T).T
        if np.any(cam_pts[:, 2] <= 0.05):
            return self._finish(img)

        dst, _ = cv2.projectPoints(self.world_corners, rvec, tvec, self.K, self.dist)
        dst = dst.reshape(4, 2)

        # If the marker projects entirely outside the frame, render background only.
        if not self._bbox_intersects(dst):
            return self._finish(img)

        Hmat, _ = cv2.findHomography(self.src_corners, dst)
        if Hmat is None:
            return self._finish(img)

        warped = cv2.warpPerspective(self.bitmap, Hmat, (self.W, self.H),
                                    flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        mask = cv2.warpPerspective(np.full((self.T, self.T), 255, np.uint8), Hmat,
                                    (self.W, self.H), flags=cv2.INTER_NEAREST)
        m = mask > 127
        img[m] = warped[m]
        return self._finish(img)

    def _bbox_intersects(self, dst: np.ndarray) -> bool:
        x0, y0 = dst.min(axis=0)
        x1, y1 = dst.max(axis=0)
        return not (x1 < 0 or y1 < 0 or x0 > self.W or y0 > self.H)

    def _finish(self, img: np.ndarray) -> np.ndarray:
        """Apply blur, brightness variation and sensor noise to a rendered frame."""
        cfg = self.cfg
        if cfg.camera_blur_sigma > 0:
            img = cv2.GaussianBlur(img, (0, 0), cfg.camera_blur_sigma)
        bright = self.rng.uniform(0.9, 1.08)
        out = img.astype(np.float64) * bright
        if cfg.camera_noise_sigma > 0:
            out += self.rng.normal(0.0, cfg.camera_noise_sigma, out.shape)
        return np.clip(out, 0, 255).astype(np.uint8)
