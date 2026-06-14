"""
vision.py
=========
The REAL classical-computer-vision stage. NO machine learning, NO neural nets.

This module runs the actual OpenCV ArUco detector on a real (rendered) image and
recovers the marker's pose with solvePnP. It is the single piece of the whole
project that is meant to transfer UNCHANGED to real hardware: feed it a frame
from a Raspberry Pi camera instead of a frame from camera_sim.py and it behaves
identically.

Strict boundary: this module receives ONLY an image (plus the static, known
camera intrinsics, marker size, dictionary and target ID from config). It has NO
access to the drone's true state. Everything it returns is inferred from pixels.

OpenCV API compatibility
------------------------
OpenCV >= 4.7 uses cv2.aruco.ArucoDetector + detector.detectMarkers() and
cv2.aruco.generateImageMarker(); older versions use the free function
cv2.aruco.detectMarkers() and cv2.aruco.drawMarker(). We detect which is present
at runtime and use whichever exists, so the same code runs on either.
"""

from __future__ import annotations
import numpy as np
import cv2

from config import CONFIG

# Does this OpenCV expose the modern (>=4.7) ArUco object API?
_HAS_NEW_API = hasattr(cv2.aruco, "ArucoDetector")
# Does it expose the modern marker-image generator?
_HAS_GENERATE_IMAGE = hasattr(cv2.aruco, "generateImageMarker")


def get_aruco_dictionary(name: str = CONFIG.marker_dict):
    """Return the predefined ArUco dictionary object for a name like 'DICT_4X4_50'."""
    dict_id = getattr(cv2.aruco, name)
    return cv2.aruco.getPredefinedDictionary(dict_id)


def generate_marker_image(dictionary, marker_id: int, side_px: int) -> np.ndarray:
    """Render the canonical (flat, front-on) bitmap of a marker. API-version aware."""
    if _HAS_GENERATE_IMAGE:
        return cv2.aruco.generateImageMarker(dictionary, marker_id, side_px)
    # Legacy fallback (OpenCV < 4.7).
    return cv2.aruco.drawMarker(dictionary, marker_id, side_px)


def _make_detector(dictionary):
    """Build whatever detector object/closure this OpenCV version supports."""
    if _HAS_NEW_API:
        params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, params)
        return lambda gray: detector.detectMarkers(gray)
    # Legacy free-function form.
    params = cv2.aruco.DetectorParameters_create()
    return lambda gray: cv2.aruco.detectMarkers(gray, dictionary, parameters=params)


class Vision:
    """
    Detects the target ArUco marker in a camera frame and estimates its pose.

    The camera is treated as down-looking and (gimbal-)stabilised to near-nadir,
    so the marker's position in the camera frame maps directly to an East/North
    offset and a height. Residual tilt is kept tiny by config, and the height is
    additionally cross-checked against the ToF rangefinder in the controller.
    """

    def __init__(self, config=CONFIG):
        self.cfg = config
        self.dictionary = get_aruco_dictionary(config.marker_dict)
        self._detect = _make_detector(self.dictionary)
        self.K = config.camera_matrix
        self.dist = config.dist_coeffs
        s = config.marker_size_m
        # Object points of the marker corners in the MARKER frame (centre origin,
        # X right, Y up, Z out of the plane). Order = top-left, top-right,
        # bottom-right, bottom-left, matching the detector's corner output.
        self.obj_points = np.array([
            [-s / 2,  s / 2, 0.0],
            [ s / 2,  s / 2, 0.0],
            [ s / 2, -s / 2, 0.0],
            [-s / 2, -s / 2, 0.0],
        ], dtype=np.float64)

    def detect(self, image: np.ndarray) -> dict:
        """
        Run detection + pose estimation on a single frame.

        Returns a dict:
            detected        : any marker found at all
            target_found    : our configured marker_id was found
            ids             : list of all detected ids
            offset_east     : marker East offset from the drone (m)  [target only]
            offset_north    : marker North offset from the drone (m) [target only]
            horizontal_offset : sqrt(east^2 + north^2) (m)
            height          : estimated height of camera above the marker (m)
            corners         : 4x2 image corners of the target marker (for drawing)
            rvec, tvec      : raw solvePnP pose of the marker in the camera frame
            reproj_error_px : mean reprojection error (a quality measure)
            confidence      : 0..1 confidence derived from reprojection error
        """
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        corners, ids, _rejected = self._detect(gray)

        result = {
            "detected": ids is not None and len(ids) > 0,
            "target_found": False,
            "ids": [] if ids is None else [int(i) for i in ids.flatten()],
            "offset_east": None, "offset_north": None, "horizontal_offset": None,
            "height": None, "corners": None,
            "rvec": None, "tvec": None,
            "reproj_error_px": None, "confidence": 0.0,
        }
        if ids is None:
            return result

        ids_flat = ids.flatten()
        match = np.where(ids_flat == self.cfg.marker_id)[0]
        if len(match) == 0:
            return result  # other markers seen, but not OUR snack-drop marker

        idx = int(match[0])
        img_corners = corners[idx].reshape(4, 2).astype(np.float64)

        ok, rvec, tvec = cv2.solvePnP(
            self.obj_points, img_corners, self.K, self.dist,
            flags=cv2.SOLVEPNP_IPPE_SQUARE)
        if not ok:
            return result

        tvec = tvec.reshape(3)

        # Reject degenerate / flipped pose solutions. The perfectly fronto-parallel
        # planar case is ambiguous and solvePnP can return a non-finite or
        # behind-camera result; the reprojection error then blows up. We require a
        # finite, in-front pose with a small reprojection error before trusting it.
        if not np.all(np.isfinite(tvec)) or tvec[2] <= 0.05:
            return result
        proj, _ = cv2.projectPoints(self.obj_points, rvec, tvec, self.K, self.dist)
        reproj_err = float(np.mean(np.linalg.norm(proj.reshape(4, 2) - img_corners, axis=1)))
        if not np.isfinite(reproj_err) or reproj_err > self.cfg.vision_max_reproj_px:
            return result

        # Map the camera-frame marker position to the world ENU offset of the
        # marker relative to the drone (camera X = East, camera Y = South).
        offset_east = float(tvec[0])
        offset_north = float(-tvec[1])
        height = float(tvec[2])  # distance along the optical axis ~ height above marker
        confidence = float(np.clip(1.0 - reproj_err / 5.0, 0.0, 1.0))

        result.update({
            "target_found": True,
            "offset_east": offset_east,
            "offset_north": offset_north,
            "horizontal_offset": float(np.hypot(offset_east, offset_north)),
            "height": height,
            "corners": img_corners,
            "rvec": rvec, "tvec": tvec,
            "reproj_error_px": reproj_err,
            "confidence": confidence,
        })
        return result


def draw_detection(image: np.ndarray, result: dict) -> np.ndarray:
    """Return a copy of the image with the detected marker outline + axes drawn."""
    out = image.copy() if image.ndim == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if result.get("target_found") and result.get("corners") is not None:
        c = result["corners"].astype(int)
        cv2.polylines(out, [c.reshape(-1, 1, 2)], True, (0, 255, 0), 2)
        centre = c.mean(axis=0).astype(int)
        cv2.circle(out, tuple(centre), 4, (0, 0, 255), -1)
        try:
            cv2.drawFrameAxes(out, CONFIG.camera_matrix, CONFIG.dist_coeffs,
                            result["rvec"], result["tvec"], CONFIG.marker_size_m * 0.5)
        except Exception:
            pass  # drawFrameAxes is cosmetic; never let it break the run
    return out
