"""
config.py
=========
ALL tunable knobs for the simulation live here, in one place, with comments.

Coordinate convention used everywhere in this project
-----------------------------------------------------
We use a LOCAL coordinate frame measured in METERS, with the origin (0, 0, 0)
at the home/launch station on the ground:

    X = East   (meters, + is East)
    Y = North  (meters, + is North)
    Z = Up     (meters, + is up / altitude above the ground at home)

Angles (yaw) are in radians, 0 = facing East, increasing counter-clockwise.

Andrey: to change the scenario, edit the numbers below and re-run.
The most fun ones to change are `balcony_height_m`, `wind_base_mps`,
`wind_turbulence_mps`, and `gps_horizontal_sigma_m`.
"""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class SimConfig:
    # ----- Random seed (controls all noise so runs are repeatable) -----
    seed: int = 7

    # ----- Simulation timing -----
    dt: float = 0.05                 # physics timestep in seconds (20 Hz)
    max_mission_seconds: float = 180 # global failsafe: give up after this long

    # ----- Home / launch station (real-world GPS of the ground station) -----
    home_lat: float = 48.137400      # degrees
    home_lon: float = 11.575500      # degrees
    home_alt_m: float = 0.0          # ground altitude reference at home

    # ----- The delivery target (the friend's balcony) -----
    # The balcony's horizontal position expressed in LOCAL meters from home.
    # (dispatch.py also shows how this maps to/from GPS lat/lon.)
    target_east_m: float = 40.0      # how far East of home the balcony is
    target_north_m: float = 30.0     # how far North of home the balcony is
    balcony_height_m: float = 8.0    # height of the balcony floor above ground
    # The balcony is modelled as a flat rectangle (the floor) at this height.
    balcony_width_m: float = 3.0     # East-West extent of the balcony floor
    balcony_depth_m: float = 2.0     # North-South extent of the balcony floor

    # ----- The ArUco marker taped flat on the balcony floor, facing up -----
    marker_id: int = 23              # which marker ID is printed/taped down
    marker_dict: str = "DICT_4X4_50" # OpenCV ArUco dictionary name
    marker_size_m: float = 0.25      # physical side length of the printed square
    # The marker sits at the balcony centre by default:
    marker_east_m: float = 40.0
    marker_north_m: float = 30.0

    # ----- Flight altitudes (all in meters above home ground) -----
    # Cruise ABOVE the balcony floor so the drone approaches over the top of the
    # (now solid) balcony and descends onto it -- it must never fly up through the
    # balcony slab. Keep cruise_altitude > balcony_height.
    cruise_altitude_m: float = 10.0      # GPS cruise height on the way over
    search_alt_above_balcony_m: float = 4.0   # hover this high above the floor to search
    release_height_above_balcony_m: float = 1.3  # drop from this high above the floor
    return_altitude_m: float = 15.0      # climb to this safe height to fly home

    # ----- Drone flight performance limits -----
    max_horizontal_speed_mps: float = 4.0
    max_climb_rate_mps: float = 2.0
    max_descent_rate_mps: float = 1.2
    max_accel_mps2: float = 4.0          # first-order responsiveness limit
    position_ctrl_gain: float = 0.9      # autopilot's built-in goto P-gain

    # ----- Battery model (tracked, but does not fail the mission by default) -----
    battery_start_pct: float = 100.0
    battery_hover_drain_pct_per_s: float = 0.05
    battery_throttle_drain_pct_per_s: float = 0.04  # extra, scaled by effort

    # ----- Wind & turbulence -----
    # Base steady wind vector (East, North) in m/s. The drone must fight this
    # (its integral term cancels the steady part; gusts are the residual battle).
    # Kept comfortably below the drone's control authority so precision is
    # achievable -- raise these to make the mission harder.
    wind_base_mps: tuple = (1.3, 0.6)
    wind_turbulence_mps: float = 0.18    # std-dev of gusty turbulence
    # Wind/turbulence is WORSE near the building wall (rotor wash / eddies):
    wind_building_multiplier: float = 2.0   # peak multiplier at the wall
    wind_building_radius_m: float = 8.0     # within this horizontal radius of
    #                                         the balcony, wind/turbulence ramps up

    # ----- Sensor noise -----
    # Real GPS error is dominated by a slowly-varying BIAS (multipath / atmosphere)
    # of a few meters that persists across a flight, plus smaller jitter. We model
    # it that way: a constant per-flight bias + white noise. The bias is exactly
    # why a GPS-only drop misses by a few meters and the vision stage is needed.
    gps_bias_sigma_m: float = 1.5        # std-dev of the constant per-flight bias
    gps_horizontal_sigma_m: float = 0.8  # std-dev of the fast GPS jitter
    gps_vertical_sigma_m: float = 4.0    # vertical jitter (worse than horizontal)
    rangefinder_sigma_m: float = 0.03    # downward ToF: small, trustworthy noise
    rangefinder_max_range_m: float = 40.0
    barometer_sigma_m: float = 0.4       # baro noise
    barometer_drift_mps: float = 0.08    # slow drift => NOT trusted for final descent

    # ----- Camera intrinsics (SHARED by the renderer and the detector) -----
    # A simple pinhole model. cx, cy default to the image centre below.
    image_width: int = 640
    image_height: int = 480
    focal_length_px: float = 500.0       # ~65 deg horizontal field of view
    # principal point is set in __post_init__ to the image centre.
    cx: float = field(default=None)
    cy: float = field(default=None)
    camera_blur_sigma: float = 0.7       # mild lens/motion blur
    camera_noise_sigma: float = 4.0      # sensor noise (0-255 scale)
    camera_tilt_deg: float = 0.8         # small residual gimbal tilt (deg) for realism
    vision_max_reproj_px: float = 8.0    # reject pose solutions worse than this

    # ----- Control (PID) gains -----
    # Horizontal centring controller (drives marker offset -> 0).
    # Output is a velocity command (m/s) from a position error (m).
    # The integral term must have enough authority to fully cancel the steady
    # wind near the wall (~1.8 m/s), otherwise the drone parks downwind.
    horiz_kp: float = 1.2
    horiz_ki: float = 0.5
    horiz_kd: float = 0.35
    horiz_i_limit: float = 5.0           # anti-windup clamp (ki*limit = 2.5 m/s authority)
    # Vertical descent controller (drives height-above-marker -> target).
    vert_kp: float = 1.0
    vert_ki: float = 0.15
    vert_kd: float = 0.20
    vert_i_limit: float = 1.5

    # ----- Mission tolerances -----
    cruise_arrival_tol_m: float = 1.0    # "close enough" by GPS (estimate) to climb
    # GPS-chase controller (cruise / return / land) gains. A mild integral cancels
    # the steady wind so the only residual error is the (irreducible) GPS bias.
    gps_chase_ki: float = 0.3
    gps_chase_i_limit: float = 5.0
    return_success_tol_m: float = 6.0    # GPS-only home landing realistic tolerance
    align_tol_m: float = 0.15            # must centre within this before descending
    drop_tol_m: float = 0.09             # must be this centred (and steady) to drop
    descend_abort_tol_m: float = 0.70    # offset grows past this -> climb & re-search
    home_arrival_tol_m: float = 1.0      # "back home" horizontal tolerance
    search_pattern_step_m: float = 1.3   # spacing of the expanding search spiral
    search_speed_mps: float = 2.5        # how fast to fly the search/climb (> peak wind)
    align_settle_steps: int = 8          # consecutive in-tolerance steps before descend
    drop_settle_steps: int = 10          # consecutive in-tolerance steps before drop

    # ----- Payload drop physics -----
    gravity_mps2: float = 9.81
    drop_wind_coupling: float = 0.03     # dense snack barely couples to wind in free-fall
    drop_dispersion_sigma_m: float = 0.03  # tiny release jitter

    # ===================================================================== #
    #  3D WORLD UPGRADE KNOBS (PyBullet world, collision, LiDAR, link, ...)  #
    # ===================================================================== #

    # ----- World source -----
    enable_world: bool = True            # load the 3D world (collision + sensing)
    use_sample_world: bool = True        # True = bundled procedural world;
    #                                      False = load Andrey's Blender export
    world_dir: str = "world"             # folder holding scene.json + the .obj
    world_scene_file: str = "scene.json" # the scene description to load
    world_backend: str = "auto"          # "auto" | "pybullet" | "trimesh"
    #   auto = use PyBullet if installed (Andrey's Mac), else the trimesh fallback.

    # ----- Drone body / collision -----
    drone_radius_m: float = 0.22         # collision sphere approximating the airframe
    collision_margin_m: float = 0.08     # a near-touch within this also counts
    takeoff_clearance_m: float = 0.6     # collision checks start once above this AGL
    #   (so sitting on the launch pad / landing at home is never a "crash")

    # ----- Navigation: sensor-only obstacle avoidance (the realistic default) -----
    # The drone steers around obstacles using ONLY a LiDAR distance scan + its noisy
    # GPS goal direction -- it has NO knowledge of the world layout (src/avoidance.py).
    avoid_range_m: float = 4.0           # a LiDAR return closer than this pushes the
    #                                      drone away from it (steer-around distance).
    avoid_gain: float = 1.6              # how hard obstacles push (bigger = wider berth).
    avoid_fov_deg: float = 360.0         # LiDAR sweep used for navigation (360 = full).
    avoid_rays: int = 36                 # number of rays in that sweep.

    # ----- OPTIONAL: map-based global route planner (NOT realistic) -----
    # Off by default. When True, the drone is GIVEN the world map and plans an A*
    # route around obstacles up front (src/planner.py). Useful for comparison, but
    # it "cheats" -- a real drone wouldn't have the map. The sensor-only avoidance
    # above still runs on top of it.
    enable_path_planning: bool = False
    nav_clearance_m: float = 1.5         # planner's horizontal obstacle inflation
    nav_max_climb_m: float = 14.0        # planner: how high it may climb to go OVER
    waypoint_tol_m: float = 2.5          # planner: intermediate-waypoint reached tol

    # ----- LiDAR / depth sensor -----
    lidar_range_m: float = 12.0          # max ray distance
    lidar_h_fov_deg: float = 120.0       # horizontal fan width (forward)
    lidar_h_rays: int = 24               # rays across the horizontal fan
    lidar_v_fov_deg: float = 40.0        # vertical fan width
    lidar_v_rays: int = 7                # rays across the vertical fan
    lidar_reflex_stop_m: float = 2.0     # last-resort: halt if something is right ahead
    lidar_noise_m: float = 0.02          # range noise
    enable_lidar_reflex: bool = True     # master switch for onboard LiDAR avoidance

    # ----- Front-facing camera -----
    front_cam_width: int = 320
    front_cam_height: int = 240
    front_cam_fov_deg: float = 70.0
    front_cam_near_m: float = 0.05
    front_cam_far_m: float = 60.0

    # ----- 3rd-person chase camera -----
    chase_cam_width: int = 480
    chase_cam_height: int = 360
    chase_cam_fov_deg: float = 60.0
    chase_cam_back_m: float = 6.0        # how far behind the drone
    chase_cam_up_m: float = 3.0          # how far above the drone

    # ----- Onboard / ground compute split + simulated link -----
    link_latency_ms: float = 80.0        # one-way latency applied to every message
    link_bandwidth_kbps: float = 800.0   # uplink+downlink cap (kilobits/sec)
    link_packet_loss: float = 0.02       # fraction of messages dropped
    onboard_budget_ms_per_tick: float = 8.0  # compute the Pi has per control tick
    #   Tasks (mis)assigned onboard that exceed this are flagged as over-budget.

    # ----- Manual setup mode (wireframe + glowing points) -----
    setup_render_width: int = 720
    setup_render_height: int = 540
    setup_orbit_azimuth_deg: float = 45.0
    setup_orbit_elevation_deg: float = 25.0

    # ----- Live view (the on-screen window while the mission flies) -----
    live_speed: float = 1.0              # playback speed of the LIVE window.
    #   1.0 = real time (1 simulated second takes 1 wall-clock second) so you can
    #   actually watch each phase; 2.0 = twice as fast, 0.5 = slow motion.
    live_update_hz: float = 10.0         # how many times/second the live window redraws
    live_feeds: bool = False             # default live window also shows the 3rd-person
    #                                      + front camera feeds (needs the 3D world)

    # ----- Output -----
    output_dir: str = "outputs"
    video_filename: str = "mission_demo.mp4"
    gif_filename: str = "mission_demo.gif"
    video_fps: int = 18
    video_every_n_steps: int = 10        # record every Nth sim step into the video

    def __post_init__(self):
        if self.cx is None:
            self.cx = self.image_width / 2.0
        if self.cy is None:
            self.cy = self.image_height / 2.0

    # --- Convenience derived values (computed, not stored) ---
    @property
    def camera_matrix(self) -> np.ndarray:
        """The 3x3 pinhole intrinsics matrix K, shared by renderer & detector."""
        return np.array(
            [[self.focal_length_px, 0.0, self.cx],
             [0.0, self.focal_length_px, self.cy],
             [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )

    @property
    def dist_coeffs(self) -> np.ndarray:
        """Lens distortion. Zero = ideal pinhole (kept simple & honest)."""
        return np.zeros((5, 1), dtype=np.float64)

    @property
    def marker_world(self) -> np.ndarray:
        """Marker centre position in local meters (East, North, Up)."""
        return np.array(
            [self.marker_east_m, self.marker_north_m, self.balcony_height_m],
            dtype=np.float64,
        )

    @property
    def target_world(self) -> np.ndarray:
        """Balcony target position in local meters (East, North, Up)."""
        return np.array(
            [self.target_east_m, self.target_north_m, self.balcony_height_m],
            dtype=np.float64,
        )

    @property
    def search_altitude_m(self) -> float:
        """Absolute altitude (above home ground) used while searching/aligning."""
        return self.balcony_height_m + self.search_alt_above_balcony_m

    @property
    def release_altitude_m(self) -> float:
        """Absolute altitude (above home ground) at which the snack is released."""
        return self.balcony_height_m + self.release_height_above_balcony_m


# The single default configuration object the whole program reads.
CONFIG = SimConfig()
