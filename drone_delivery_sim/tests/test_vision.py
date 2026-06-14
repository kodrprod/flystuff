"""
test_vision.py
==============
Tests the REAL computer-vision stage against the synthetic camera:

  * renders the marker at several offsets/altitudes and asserts the detector
    returns the correct ID and recovers the pose within a stated tolerance;
  * asserts it fails gracefully when the marker is absent or too far away.

Run directly (no pytest needed):   python tests/test_vision.py
Or with pytest:                    python -m pytest tests/test_vision.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SimConfig
from src.camera_sim import CameraSim
from src.vision import Vision

# Tolerances (chosen from the measured behaviour of the honest pinhole loop).
HEIGHT_REL_TOL = 0.10      # recovered height within 10% of truth
OFFSET_ABS_TOL = 0.12      # recovered horizontal offset within 12 cm
FRAMES_PER_POSE = 8        # average a few frames to be robust to per-frame noise


def _measure(cam, vis, cfg, height, off_e, off_n, n=FRAMES_PER_POSE):
    """Render n frames at a pose and return averaged detection stats."""
    mE, mN, bh = cfg.marker_east_m, cfg.marker_north_m, cfg.balcony_height_m
    pos = np.array([mE + off_e, mN + off_n, bh + height])
    hs, es, ns, found = [], [], [], 0
    ids_seen = set()
    for _ in range(n):
        r = vis.detect(cam.render(pos))
        if r["target_found"]:
            found += 1
            hs.append(r["height"]); es.append(r["offset_east"]); ns.append(r["offset_north"])
            ids_seen.update(r["ids"])
    return found, ids_seen, (np.mean(hs) if hs else None,
                            np.mean(es) if es else None,
                            np.mean(ns) if ns else None)


def test_detection_and_pose_accuracy():
    cfg = SimConfig(seed=11)
    cam = CameraSim(cfg, rng=np.random.default_rng(11))
    vis = Vision(cfg)

    # (height_above_marker, east_offset, north_offset)
    poses = [(1.3, 0.0, 0.0), (2.0, 0.4, -0.3), (3.0, -0.5, 0.6),
            (4.0, 0.0, 0.0), (4.0, 1.0, 0.8)]
    for h, oe, on in poses:
        found, ids, (h_est, e_est, n_est) = _measure(cam, vis, cfg, h, oe, on)
        assert found >= FRAMES_PER_POSE - 1, f"detection unreliable at h={h}, off=({oe},{on})"
        assert ids == {cfg.marker_id}, f"wrong id(s) {ids} at h={h}"
        # Expected: vision returns the marker offset RELATIVE to the drone, i.e.
        # (-oe, -on); and the height above the marker.
        assert abs(h_est - h) <= HEIGHT_REL_TOL * h, f"height {h_est:.3f} vs {h}"
        assert abs(e_est - (-oe)) <= OFFSET_ABS_TOL, f"east {e_est:.3f} vs {-oe}"
        assert abs(n_est - (-on)) <= OFFSET_ABS_TOL, f"north {n_est:.3f} vs {-on}"


def test_fails_when_marker_too_far():
    cfg = SimConfig(seed=12)
    cam = CameraSim(cfg, rng=np.random.default_rng(12))
    vis = Vision(cfg)
    # Far above the marker -> too few pixels -> must NOT claim a detection.
    found, _ids, _ = _measure(cfg and cam, vis, cfg, height=18.0, off_e=0.0, off_n=0.0)
    assert found == 0, "marker should be undetectable from 18 m up"


def test_fails_when_marker_out_of_frame():
    cfg = SimConfig(seed=13)
    cam = CameraSim(cfg, rng=np.random.default_rng(13))
    vis = Vision(cfg)
    # At 4 m altitude the footprint is ~2.5 m; a 6 m offset is off-frame.
    found, _ids, _ = _measure(cam, vis, cfg, height=4.0, off_e=6.0, off_n=0.0)
    assert found == 0, "marker 6 m off-axis should not be detected"


def test_blank_image_returns_nothing():
    cfg = SimConfig(seed=14)
    vis = Vision(cfg)
    rng = np.random.default_rng(14)
    blank = rng.integers(60, 160, (cfg.image_height, cfg.image_width, 3), dtype=np.uint8)
    r = vis.detect(blank)
    assert not r["target_found"], "must not hallucinate a marker in pure noise"


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL  {name}: {e}")
    print("\n" + ("ALL VISION TESTS PASSED" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
