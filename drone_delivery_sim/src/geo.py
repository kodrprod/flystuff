"""
geo.py
======
Tiny helpers to convert between GPS latitude/longitude and the LOCAL
meters frame (East/North/Up) used by the rest of the simulation.

We use the simple "equirectangular" / flat-earth approximation around the
home point. Over the small distances in a hobby drone flight (tens to a few
hundred meters) the error from this approximation is millimetric, so it is
perfectly adequate and keeps the math transparent.

    east  (meters) = (lon - home_lon) * meters_per_deg_lon
    north (meters) = (lat - home_lat) * meters_per_deg_lat
"""

import numpy as np

# Mean Earth radius based constants.
_METERS_PER_DEG_LAT = 111_320.0  # ~constant everywhere


def meters_per_deg_lon(latitude_deg: float) -> float:
    """Meters per degree of longitude shrinks as you move away from the equator."""
    return 111_320.0 * np.cos(np.radians(latitude_deg))


def global_to_local(lat: float, lon: float, alt: float,
                    home_lat: float, home_lon: float, home_alt: float) -> np.ndarray:
    """
    Convert an absolute GPS fix (lat, lon, alt) into LOCAL meters (East, North, Up)
    relative to the home station.
    """
    east = (lon - home_lon) * meters_per_deg_lon(home_lat)
    north = (lat - home_lat) * _METERS_PER_DEG_LAT
    up = alt - home_alt
    return np.array([east, north, up], dtype=np.float64)


def local_to_global(east: float, north: float, up: float,
                    home_lat: float, home_lon: float, home_alt: float):
    """
    Convert LOCAL meters (East, North, Up) back into an absolute GPS fix.
    Returns (lat, lon, alt).
    """
    lat = home_lat + north / _METERS_PER_DEG_LAT
    lon = home_lon + east / meters_per_deg_lon(home_lat)
    alt = home_alt + up
    return lat, lon, alt
