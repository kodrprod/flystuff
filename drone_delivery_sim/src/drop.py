"""
drop.py
=======
Models the servo-triggered payload release and where the snack actually lands.

From a low release height directly above the marker, a dense snack (a chocolate
bar) falls essentially straight down. We add two small, physically-motivated
effects so the landing point is not perfectly ideal:

  * wind drift : during the short free-fall the snack is nudged sideways by the
    wind. A dense object couples only weakly to the wind, so this is small and
    scales with both the wind speed and the fall time (i.e. the release height).
  * release jitter : a tiny random dispersion from the mechanism itself.

The horizontal distance from where the snack lands to the marker centre is THE
key success metric of the whole project, so it is computed and recorded here.
"""

from __future__ import annotations
import numpy as np

from config import CONFIG


class PayloadDrop:
    """The release mechanism + a simple ballistic landing model."""

    def __init__(self, config=CONFIG, rng: np.random.Generator | None = None):
        self.cfg = config
        self.rng = rng if rng is not None else np.random.default_rng(config.seed)
        self.released = False
        self.record = None

    def release(self, telemetry: dict, marker_world: np.ndarray) -> dict:
        """
        Release the snack given the drone's telemetry at the moment of drop.

        telemetry    : drone.get_telemetry() snapshot (position, wind, ...)
        marker_world : the marker centre in local ENU meters (the bullseye)

        Returns a record dict including the landing point and the error (meters)
        from the marker centre.
        """
        cfg = self.cfg
        pos = telemetry["position"]
        wind = telemetry["wind"]
        drop_xy = pos[:2].astype(float)

        # Height of the snack above the balcony floor at release.
        release_height = max(0.0, pos[2] - cfg.balcony_height_m)
        # Time to fall that height under gravity.
        fall_time = np.sqrt(2.0 * release_height / cfg.gravity_mps2) if release_height > 0 else 0.0

        # Sideways drift from wind (weak coupling for a dense object) + jitter.
        wind_drift = wind[:2] * fall_time * cfg.drop_wind_coupling
        jitter = self.rng.normal(0.0, cfg.drop_dispersion_sigma_m, 2)

        landing_xy = drop_xy + wind_drift + jitter
        error = float(np.linalg.norm(landing_xy - marker_world[:2]))

        self.released = True
        self.record = {
            "drop_xy": drop_xy,
            "landing_xy": landing_xy,
            "release_height_m": release_height,
            "fall_time_s": float(fall_time),
            "error_m": error,
            "marker_xy": marker_world[:2].astype(float),
        }
        return self.record
