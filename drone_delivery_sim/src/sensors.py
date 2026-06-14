"""
sensors.py
==========
Simulated noisy sensors. These are the ONLY position cues the cruise phase has
before the camera takes over. Their imperfections are the whole reason the
vision stage exists:

  * GPS  : good to only a few meters horizontally and worse vertically. Fine for
           "fly to roughly the right building", useless for "hit the balcony".
  * ToF rangefinder : a downward laser/Time-of-Flight distance to the surface
           directly below. Small, trustworthy noise and a maximum range. This is
           a primary height source during the precision descent.
  * Barometer : an altitude estimate that slowly drifts, included specifically
           to demonstrate why it is NOT trusted for the final descent.

Each sensor reads the drone's TRUE state and corrupts it. The drone object is
passed in so the ground truth never leaks anywhere it shouldn't.
"""

from __future__ import annotations
import numpy as np

from config import CONFIG
from src.geo import local_to_global


class Sensors:
    def __init__(self, drone, config=CONFIG, rng: np.random.Generator | None = None):
        self.drone = drone
        self.cfg = config
        self.rng = rng if rng is not None else np.random.default_rng(config.seed)
        self._baro_drift = 0.0   # accumulates a slow random walk
        # Constant per-flight GPS bias (multipath / atmosphere). This is the part
        # the cruise CANNOT average away, so it sets the GPS-only miss distance.
        self.gps_bias = np.array([
            self.rng.normal(0.0, config.gps_bias_sigma_m),
            self.rng.normal(0.0, config.gps_bias_sigma_m),
            self.rng.normal(0.0, 2.0 * config.gps_bias_sigma_m),
        ])

    def read_gps(self) -> dict:
        """
        Noisy GPS fix. Returns BOTH the absolute lat/lon/alt and the equivalent
        noisy LOCAL ENU position (the cruise controller uses the local form).
        """
        true_pos = self.drone.pos
        noise = np.array([
            self.rng.normal(0.0, self.cfg.gps_horizontal_sigma_m),
            self.rng.normal(0.0, self.cfg.gps_horizontal_sigma_m),
            self.rng.normal(0.0, self.cfg.gps_vertical_sigma_m),
        ])
        noisy_local = true_pos + self.gps_bias + noise
        lat, lon, alt = local_to_global(
            noisy_local[0], noisy_local[1], noisy_local[2],
            self.cfg.home_lat, self.cfg.home_lon, self.cfg.home_alt_m)
        return {
            "local": noisy_local,            # (East, North, Up) meters, noisy
            "lat": lat, "lon": lon, "alt": alt,
            "horizontal_sigma_m": self.cfg.gps_horizontal_sigma_m,
        }

    def read_rangefinder(self) -> float | None:
        """
        Downward ToF distance to the surface directly below the drone.
        Accounts for the elevated balcony: above the balcony floor the surface is
        the balcony; elsewhere it is the ground. Returns None if beyond max range.
        """
        true_height = self.drone.height_above_surface()
        if true_height > self.cfg.rangefinder_max_range_m:
            return None
        reading = true_height + self.rng.normal(0.0, self.cfg.rangefinder_sigma_m)
        return max(0.0, reading)

    def read_barometer(self) -> float:
        """
        Barometric altitude (meters above home). Includes a slow random-walk drift
        plus noise, so it disagrees with the rangefinder over time -> not trusted
        for the final descent.
        """
        self._baro_drift += self.rng.normal(0.0, self.cfg.barometer_drift_mps * self.cfg.dt)
        return self.drone.pos[2] + self._baro_drift + self.rng.normal(0.0, self.cfg.barometer_sigma_m)
