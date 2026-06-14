"""
dispatch.py
===========
The ground / dispatch station. In the real system the friend taps a button in an
app and the app sends three things: their GPS location, the balcony marker ID,
and the balcony height above ground. The dispatch station turns that request into
a concrete flight mission.

This module models exactly that hand-off:

    DeliveryRequest  -->  build_mission()  -->  MissionPlan

The MissionPlan is what mission.py executes. Keeping this separate mirrors the
real architecture (app -> dispatch -> drone) and means the drone never needs to
know about app payloads, only about a clean plan.
"""

from __future__ import annotations
from dataclasses import dataclass

from config import CONFIG
from src.geo import global_to_local, local_to_global


@dataclass
class DeliveryRequest:
    """What the friend's app sends when they tap 'send me a snack'."""
    friend_lat: float          # the friend's GPS latitude
    friend_lon: float          # the friend's GPS longitude
    balcony_marker_id: int     # the ArUco ID printed on their balcony
    balcony_height_m: float    # how high the balcony floor is above ground
    snack: str = "chocolate bar"


@dataclass
class MissionPlan:
    """A concrete, drone-ready flight plan produced by the dispatch station."""
    # Where home (the launch station) is.
    home_lat: float
    home_lon: float
    home_alt_m: float
    # The target, expressed in the local ENU meters frame used everywhere.
    target_east_m: float
    target_north_m: float
    balcony_height_m: float
    marker_id: int
    marker_size_m: float
    # Altitudes (meters above home ground).
    cruise_altitude_m: float
    search_altitude_m: float       # absolute altitude to search/align at
    release_altitude_m: float      # absolute altitude to release the snack at
    return_altitude_m: float
    snack: str

    @property
    def target_xy(self):
        return (self.target_east_m, self.target_north_m)

    @property
    def home_xy(self):
        return (0.0, 0.0)


def build_mission(request: DeliveryRequest, config=CONFIG) -> MissionPlan:
    """Convert an app DeliveryRequest into a concrete MissionPlan."""
    # Convert the friend's GPS into our local meters frame relative to home.
    local = global_to_local(
        request.friend_lat, request.friend_lon, config.home_alt_m,
        config.home_lat, config.home_lon, config.home_alt_m)

    return MissionPlan(
        home_lat=config.home_lat,
        home_lon=config.home_lon,
        home_alt_m=config.home_alt_m,
        target_east_m=float(local[0]),
        target_north_m=float(local[1]),
        balcony_height_m=request.balcony_height_m,
        marker_id=request.balcony_marker_id,
        marker_size_m=config.marker_size_m,
        cruise_altitude_m=config.cruise_altitude_m,
        search_altitude_m=request.balcony_height_m + config.search_alt_above_balcony_m,
        release_altitude_m=request.balcony_height_m + config.release_height_above_balcony_m,
        return_altitude_m=config.return_altitude_m,
        snack=request.snack,
    )


def request_from_config(config=CONFIG) -> DeliveryRequest:
    """
    Build the default DeliveryRequest that reproduces the scenario in config.py.
    (Round-trips the configured local target back into a GPS coordinate so the
    whole app -> dispatch -> drone path is exercised honestly.)
    """
    lat, lon, _ = local_to_global(
        config.target_east_m, config.target_north_m, 0.0,
        config.home_lat, config.home_lon, config.home_alt_m)
    return DeliveryRequest(
        friend_lat=lat,
        friend_lon=lon,
        balcony_marker_id=config.marker_id,
        balcony_height_m=config.balcony_height_m,
    )
