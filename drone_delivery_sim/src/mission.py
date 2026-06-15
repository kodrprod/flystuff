"""
mission.py
==========
The mission state machine: the "brain" that flies one full snack-delivery from
the home station to the balcony and back. It wires together the drone (backend),
the sensors, the synthetic camera, the real vision, the PID controllers and the
payload drop.

State flow (each transition is logged):

    IDLE -> ARM -> TAKEOFF -> CRUISE_TO_WAYPOINT (noisy GPS)
         -> CLIMB_TO_BALCONY_ALT -> SEARCH_MARKER -> PRECISION_ALIGN
         -> DESCEND -> DROP -> ASCEND -> RETURN_HOME -> LAND -> DONE

Design notes that mirror the real hardware:
  * CRUISE and RETURN use ONLY the noisy GPS, so the drone arrives within a few
    meters -- not good enough to hit a balcony. That GPS-only error is recorded.
  * From SEARCH onward, the horizontal solution comes from VISION only.
  * Coarse altitude (cruise/climb/return) uses the barometer; the PRECISION
    descent uses the trustworthy ToF rangefinder fused with the vision height,
    exactly because baro/GPS altitude are unreliable.
  * Failsafes: marker lost while aligning/descending -> hover, then re-search;
    offset grows too large while descending -> stop and re-align; global timeout
    -> return home.

The class exposes step() (advance one tick) and run() (loop to completion). A
per-step callback lets the visualiser hook in for the live dashboard / video.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
import numpy as np

from config import CONFIG
from src.drone import Drone
from src.sensors import Sensors
from src.camera_sim import CameraSim
from src.vision import Vision
from src.control import HorizontalController, VerticalController
from src.drop import PayloadDrop
from src.dispatch import MissionPlan, request_from_config, build_mission
from src import planner
from src import avoidance

try:
    from src.world import World
except Exception:       # world layer is optional; the core sim still runs without it
    World = None


class MissionState(Enum):
    IDLE = 0
    ARM = 1
    TAKEOFF = 2
    CRUISE_TO_WAYPOINT = 3
    CLIMB_TO_BALCONY_ALT = 4
    SEARCH_MARKER = 5
    PRECISION_ALIGN = 6
    DESCEND = 7
    DROP = 8
    ASCEND = 9
    RETURN_HOME = 10
    LAND = 11
    DONE = 12
    FAILED = 13


# Vision is only run during the precision phases (matching real hardware, where
# the companion computer's camera pipeline is only active for the final approach).
# This also keeps the simulation fast during the long GPS cruise/return legs.
def _empty_vision() -> dict:
    return {
        "detected": False, "target_found": False, "ids": [],
        "offset_east": None, "offset_north": None, "horizontal_offset": None,
        "height": None, "corners": None, "rvec": None, "tvec": None,
        "reproj_error_px": None, "confidence": 0.0,
    }


def _config_from_scene(config, scene):
    """
    Override the scenario fields in `config` from the loaded scene (DROP_TARGET +
    marker). For the bundled sample world these already equal the defaults, so the
    returned config is identical; for a Blender world it retargets the mission.
    """
    drop = scene.get("drop_target")
    if not drop:
        return config
    md = scene.get("markers", {}).get("drop", {})
    return dataclasses.replace(
        config,
        target_east_m=float(drop[0]), target_north_m=float(drop[1]),
        balcony_height_m=float(drop[2]),
        marker_east_m=float(drop[0]), marker_north_m=float(drop[1]),
        marker_id=int(md.get("id", config.marker_id)),
        marker_size_m=float(md.get("size", config.marker_size_m)),
    )


def _expanding_square(step: float, max_radius: float, cap: int = 80):
    """Generate (dx, dy) offsets tracing an expanding square spiral."""
    pts = [(0.0, 0.0)]
    x = y = 0.0
    dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    di = 0
    leg = 1
    while len(pts) < cap and np.hypot(x, y) < max_radius + step:
        for _ in range(2):
            dx, dy = dirs[di % 4]
            for _ in range(leg):
                x += dx * step
                y += dy * step
                pts.append((x, y))
            di += 1
        leg += 1
    return pts


class Mission:
    # The states in which the camera/vision pipeline runs.
    _VISION_PHASES = (MissionState.SEARCH_MARKER, MissionState.PRECISION_ALIGN,
                    MissionState.DESCEND)

    def __init__(self, plan: MissionPlan | None = None, config=CONFIG,
                seed: int | None = None, log_frames: bool = False):
        seed = config.seed if seed is None else seed
        self.rng = np.random.default_rng(seed)

        # --- 3D world FIRST (collision + sensing). Its OWN rng means it never
        # perturbs the validated sensor/camera random streams (so no regression). ---
        self.world = None
        if config.enable_world and World is not None:
            try:
                self.world = World(config, rng=np.random.default_rng(seed + 991))
            except Exception as exc:
                print(f"[mission] world disabled ({exc})")
                self.world = None

        # When a world is loaded, the scene's DROP_TARGET + START + marker drive the
        # configuration so a custom Blender world delivers to the right place. For
        # the bundled sample world these already equal the defaults (no change).
        self.cfg = _config_from_scene(config, self.world.scene) if self.world is not None else config
        config = self.cfg
        self.home_xy = (self.world.drone_start[:2].copy() if self.world is not None
                        else np.array([0.0, 0.0]))
        start_pos = self.world.drone_start.copy() if self.world is not None else None

        self.plan = plan if plan is not None else build_mission(request_from_config(config), config)
        # Subsystems (all share one rng for repeatability).
        self.drone = Drone(config, rng=self.rng, start_pos=start_pos)
        # The altitude the drone launches from. Often 0 (ground), but it can be high
        # when DRONE_START sits on a balcony/rooftop in a custom model -- everything
        # below (takeoff clearance, landing, collision arming) is measured RELATIVE
        # to this so launching from an elevated pad is not treated as a crash.
        self._start_z = float(self.drone.pos[2])
        self.sensors = Sensors(self.drone, config, rng=self.rng)
        self.camera = CameraSim(config, rng=self.rng)
        self.vision = Vision(config)
        self.horiz = HorizontalController(config)
        self.vert = VerticalController(config)
        self.payload = PayloadDrop(config, rng=self.rng)

        # The drop bullseye comes from the SCENE (DROP_TARGET) when a world is
        # loaded, so the renderer and drop model stay self-consistent with it.
        if self.world is not None:
            self.marker_world = self.world.drop_target.copy()
        else:
            self.marker_world = np.array(
                [config.marker_east_m, config.marker_north_m, self.plan.balcony_height_m])
        self._has_climbed = False        # collision checks start after takeoff clearance
        self._heading = 0.0              # travel heading (for front cam + LiDAR + reflex)
        self._reflex_active = False      # LiDAR reflex currently halting forward motion
        self._reflex_events = 0          # how many ticks the reflex intervened
        self._overfly_events = 0         # ticks the vertical (climb-to-clear) avoidance acted
        self._overfly_extra = 0.0        # sticky extra climb (m) held over a low obstacle

        # ---- Obstacle-avoiding route planning (a GROUND-station task) ----------
        # Plan a collision-free path for the cruise (start -> balcony) and the
        # return (balcony -> home) legs, so the drone NAVIGATES AROUND obstacles
        # instead of flying a straight line into them. The onboard LiDAR reflex
        # stays on as the last-resort local safety net.
        target_xy = np.array([self.plan.target_east_m, self.plan.target_north_m])
        start_xy = (self.world.drone_start[:2].copy() if self.world is not None
                    else np.array([0.0, 0.0]))
        # Cruise/return altitudes must clear the launch pad: if the drone starts up
        # high (on a balcony), make sure it still climbs ABOVE the start, not into it.
        self.nav_alt = max(self.plan.cruise_altitude_m,
                        self._start_z + config.takeoff_clearance_m + 2.0)
        self.return_alt = max(self.plan.return_altitude_m,
                            self._start_z + config.takeoff_clearance_m + 2.0)
        self.cruise_path = [start_xy.copy(), target_xy.copy()]
        self.return_path = [target_xy.copy(), np.array(self.home_xy)]
        self.nav_info = {"cruise": None, "return": None}
        if self.world is not None and getattr(config, "enable_path_planning", True):
            cr = planner.plan_route(self.world, start_xy, target_xy, config,
                                    self.plan.cruise_altitude_m)
            self.cruise_path = cr["waypoints"]
            self.nav_alt = cr["altitude"]
            self.nav_info["cruise"] = cr
            rr = planner.plan_route(self.world, target_xy, self.home_xy, config,
                                    self.plan.return_altitude_m)
            self.return_path = rr["waypoints"]
            self.return_alt = rr["altitude"]
            self.nav_info["return"] = rr
        # Waypoints to actually fly (the first point is where the drone already is).
        self._cruise_wps = list(self.cruise_path[1:]) or [target_xy.copy()]
        self._return_wps = list(self.return_path[1:]) or [np.array(self.home_xy)]
        self._cruise_idx = 0
        self._return_idx = 0

        # Runtime state
        self.state = MissionState.IDLE
        self._prev_state = None
        self.t = 0.0
        self.step_count = 0
        self.done = False

        # Logs / outputs
        self.trajectory = []        # list of true (x, y, z)
        self.state_log = []         # (t, state name) on each transition
        self.history = []           # compact per-step telemetry for plots
        self.last_image = None
        self.last_vision = None
        self.log_frames = log_frames
        self.frames = []            # rendered camera frames (only if log_frames)

        # Metrics
        self.metrics = {
            "gps_only_error_m": None,    # how far GPS-alone would miss the marker
            "drop_error_m": None,        # actual vision-guided landing error
            "drop_height_m": None,
            "return_error_m": None,
            "battery_used_pct": None,
            "success": False,
            "fail_reason": None,
            "duration_s": None,
            # Collision (3D world) outcome:
            "collision": False,
            "collision_object": None,
            "collision_pos": None,
            "collision_time_s": None,
            "world_backend": (self.world.backend_name if self.world is not None else None),
            "reflex_events": 0,
            "overfly_events": 0,         # ticks the vertical climb-to-clear avoidance acted
            # Navigation (obstacle-avoiding planner) outcome:
            "nav_planned": self.nav_info["cruise"] is not None,
            "nav_cruise_detour": (self.nav_info["cruise"]["detoured"]
                                if self.nav_info["cruise"] else False),
            "nav_cruise_alt": float(self.nav_alt),
            "nav_waypoints": len(self.cruise_path),
        }

        # Per-state helpers
        self._settle = 0
        self._lost = 0
        self._search_wps = _expanding_square(
            config.search_pattern_step_m, max_radius=6.5)
        self._search_idx = 0
        self._search_dwell = 0
        self._gps_filt = None        # EMA of the noisy GPS used for chase/arrival
        self._gps_int = None         # integral term of the GPS-chase controller
        self._realign_pending = False
        self._timed_out = False
        # EMA-filtered vision measurements (reduce per-frame noise).
        self._f_e = self._f_n = self._f_h = None

    # ------------------------------------------------------------------ #
    #  Small helpers                                                     #
    # ------------------------------------------------------------------ #
    def _transition(self, new_state: MissionState, reason: str = ""):
        self.state = new_state
        self.state_log.append((round(self.t, 2), new_state.name, reason))
        # Reset per-state helpers on entry.
        self._settle = 0
        self._lost = 0
        self._search_dwell = 0
        self._gps_filt = None        # rebuild the GPS estimate fresh each phase
        self._gps_int = None
        # Reset the controllers (and their wind-cancelling integral) only on a
        # fresh acquisition; keep them running across align <-> descend so the
        # integral that cancels the steady wind is not thrown away each time.
        if new_state == MissionState.SEARCH_MARKER:
            self.horiz.reset()
            self.vert.reset()
            self._f_e = self._f_n = self._f_h = None
            self._search_idx = 0

    def _filter_vision(self, vis):
        """Exponentially smooth the vision offset/height to tame per-frame noise."""
        a = 0.5
        if vis["target_found"]:
            e, n, h = vis["offset_east"], vis["offset_north"], vis["height"]
            if self._f_e is None:
                self._f_e, self._f_n, self._f_h = e, n, h
            else:
                self._f_e = a * e + (1 - a) * self._f_e
                self._f_n = a * n + (1 - a) * self._f_n
                self._f_h = a * h + (1 - a) * self._f_h

    def _fused_height(self, vis) -> float:
        """
        Fuse the ToF rangefinder with the vision height for the precision descent.
        The rangefinder is trusted when it agrees with vision (i.e. the drone is
        genuinely above the balcony floor); otherwise vision is used.
        """
        rf = self.sensors.read_rangefinder()
        vh = self._f_h if self._f_h is not None else (vis["height"] if vis["target_found"] else None)
        if rf is not None and vh is not None and abs(rf - vh) < 1.5:
            return rf
        return vh if vh is not None else (rf if rf is not None else 0.0)

    def _sensor_avoidance(self, pos, v_goal):
        """
        SENSOR-ONLY reactive steering. Redirect the GPS-goal velocity around
        obstacles using ONLY a 360-degree LiDAR scan -- the drone never sees the map.
        Returns a (possibly) redirected 2-D velocity; open air -> unchanged.
        """
        cfg = self.cfg
        if float(np.linalg.norm(v_goal)) < 1e-6:
            return v_goal
        # A 360-degree LiDAR distance scan -- the ONLY spatial input the navigator
        # gets. It never sees object positions, just these ranges.
        scan = self.world.horizontal_scan(pos, heading=0.0,
                                        fov_deg=cfg.avoid_fov_deg,
                                        n_rays=cfg.avoid_rays)
        v, active = avoidance.repulse(v_goal, scan["bearings"], scan["clear"], cfg)
        if active:
            self._reflex_active = True
            self._reflex_events += 1
            self.metrics["reflex_events"] = self._reflex_events
        return v

    def _hold_over_target_gps(self):
        """
        Vision-lost fallback for the precision phases: HOLD position over the balcony
        (the GPS goal) at the current altitude, using GPS, instead of cutting throttle
        and letting the wind shove the drone into the railing/wall. Holding (rather
        than climbing) keeps the descent progress so re-acquisition is quick and the
        drone doesn't oscillate. A real drone falls back to GPS/IMU hold when the
        camera loses its target; this models that.
        """
        alt = self.sensors.read_barometer()        # stay at the current altitude
        self._fly_horizontal_via_gps(
            self.plan.target_east_m, self.plan.target_north_m,
            self.cfg.search_speed_mps, alt)

    def _fly_horizontal_via_gps(self, tx, ty, speed, alt_target, use_rangefinder=False):
        """
        Velocity-chase a horizontal target using ONLY noisy GPS, smoothed with an
        EMA (a stand-in for the autopilot's position filter). Returns the smoothed
        horizontal distance to the target so arrival tests are not fooled by the
        instantaneous GPS jitter.
        """
        cfg = self.cfg
        gps = self.sensors.read_gps()
        gxy = gps["local"][:2]
        if self._gps_filt is None:
            self._gps_filt = gxy.copy()
            self._gps_int = np.zeros(2)
        else:
            self._gps_filt = 0.85 * self._gps_filt + 0.15 * gxy
        err = np.array([tx - self._gps_filt[0], ty - self._gps_filt[1]])
        # Mild integral so the steady wind is cancelled; the residual is the
        # irreducible GPS bias (which is the whole point of the cruise/return).
        self._gps_int = np.clip(self._gps_int + err * cfg.dt,
                                -cfg.gps_chase_i_limit, cfg.gps_chase_i_limit)
        v = cfg.position_ctrl_gain * err + cfg.gps_chase_ki * self._gps_int
        sp = np.linalg.norm(v)
        if sp > speed:
            v = v / sp * speed

        # --- Onboard SENSOR-ONLY reactive obstacle avoidance ---
        # The drone steers around obstacles it sees with its LiDAR, knowing nothing
        # about the world layout (the realistic constraint). This is local/onboard --
        # a round-trip to the ground station would be too slow. Open paths pass
        # through unchanged. It runs only on the long transit legs (cruise / return);
        # the precision phases run their own down-camera vision PID right next to the
        # balcony, where steering would fight the very target we're delivering onto.
        self._reflex_active = False
        if sp > 0.2:
            self._heading = float(np.arctan2(v[1], v[0]))
            transit = self.state in (MissionState.CRUISE_TO_WAYPOINT,
                                    MissionState.RETURN_HOME)
            if transit and self.world is not None and cfg.enable_lidar_reflex:
                v = self._sensor_avoidance(self.drone.pos, v)
                if np.linalg.norm(v) > 0.2:
                    self._heading = float(np.arctan2(v[1], v[0]))

        # --- Onboard SENSOR-ONLY VERTICAL avoidance ---
        # The horizontal scan above is blind to a treetop sitting just BELOW the
        # flight altitude, so the drone would skim over and clip it. Here it also
        # looks ahead-and-down and lifts the altitude target to keep clearance over
        # such a low obstacle (tall ones reaching the flight level are steered
        # around by the horizontal layer). The needed climb is held with a slow
        # decay -- "sticky" -- so a single clear frame (the probe momentarily loses
        # a rounded treetop) does not drop the drone back onto it mid-fly-over.
        # Transit legs only, like the steering.
        transit_alt = self.state in (MissionState.CRUISE_TO_WAYPOINT,
                                    MissionState.RETURN_HOME)
        need_extra = 0.0
        if (sp > 0.2 and self.world is not None and cfg.enable_lidar_reflex
                and transit_alt):
            top = self.world.overfly_clearance(self.drone.pos, self._heading,
                                            look_ahead_m=cfg.avoid_overfly_lookahead_m)
            if top is not None:
                clear_alt = (top + cfg.drone_radius_m + cfg.collision_margin_m
                            + cfg.avoid_vertical_clearance_m)
                need_extra = max(0.0, clear_alt - alt_target)
        self._overfly_extra = max(0.96 * self._overfly_extra, need_extra)
        if self._overfly_extra > 0.05 and transit_alt:
            alt_target = alt_target + min(self._overfly_extra, cfg.avoid_climb_cap_m)
            self._reflex_active = True
            self._overfly_events += 1
            self.metrics["overfly_events"] = self._overfly_events

        # Altitude hold: coarse phases use the barometer; landing uses rangefinder.
        if use_rangefinder:
            rf = self.sensors.read_rangefinder()
            alt = rf if rf is not None else self.sensors.read_barometer()
        else:
            alt = self.sensors.read_barometer()
        vz = np.clip(cfg.position_ctrl_gain * (alt_target - alt),
                    -cfg.max_descent_rate_mps, cfg.max_climb_rate_mps)
        self.drone.set_velocity_body(float(v[0]), float(v[1]), float(vz), 0.0)
        return float(np.hypot(err[0], err[1]))

    # ------------------------------------------------------------------ #
    #  Main step                                                         #
    # ------------------------------------------------------------------ #
    def step(self):
        cfg = self.cfg
        dt = cfg.dt

        # --- Perception: render what the camera sees and run REAL vision on it ---
        # Only active in the precision phases (see note above _empty_vision).
        true_pos = self.drone.pos.copy()
        if self.state in self._VISION_PHASES:
            image = self.camera.render(true_pos)
            vis = self.vision.detect(image)
        else:
            image, vis = None, _empty_vision()
        self.last_image = image
        self.last_vision = vis
        self._filter_vision(vis)
        if self.log_frames and self.step_count % cfg.video_every_n_steps == 0:
            tel = self.drone.get_telemetry()
            self.frames.append({
                "image": image, "vis": vis, "state": self.state.name,
                "pos": true_pos.copy(), "t": self.t,
                "battery": tel["battery_pct"], "wind": tel["wind"].copy(),
                "velocity": tel["velocity"].copy(), "reflex": self._reflex_active,
                "height_above_marker": self.drone.height_above_surface(),
                "traj_len": len(self.trajectory),
            })

        # --- Global timeout failsafe ---
        if (self.t > cfg.max_mission_seconds and not self._timed_out
                and self.state not in (MissionState.RETURN_HOME, MissionState.LAND,
                                        MissionState.DONE, MissionState.DROP,
                                        MissionState.ASCEND)):
            self._timed_out = True
            self.metrics["fail_reason"] = "timeout"
            self._transition(MissionState.ASCEND, "global timeout -> abort home")

        s = self.state

        # ---------------- IDLE / ARM / TAKEOFF ----------------
        if s == MissionState.IDLE:
            self._transition(MissionState.ARM)

        elif s == MissionState.ARM:
            self.drone.arm()
            # Anchor the climb to the launch spot ONCE, then hold it. (Re-issuing
            # takeoff() every tick would re-anchor to the wind-drifted position --
            # i.e. no horizontal hold -- letting the drone blow sideways into
            # whatever is next to the launch pad while it climbs.)
            self._launch_xy = self.drone.pos[:2].copy()
            self._transition(MissionState.TAKEOFF)
            self.drone.takeoff(self.nav_alt)

        elif s == MissionState.TAKEOFF:
            # Hold the launch x,y against the wind while climbing (do NOT re-call
            # takeoff(), which would reset the hold to the current drifted point).
            self.drone.goto_local(self._launch_xy[0], self._launch_xy[1], self.nav_alt)
            if self.drone.pos[2] >= self.nav_alt - 0.2:
                self._transition(MissionState.CRUISE_TO_WAYPOINT)

        # ---------------- CRUISE (GPS only, following the planned route) -------
        elif s == MissionState.CRUISE_TO_WAYPOINT:
            wp = self._cruise_wps[self._cruise_idx]
            is_last = self._cruise_idx >= len(self._cruise_wps) - 1
            tol = cfg.cruise_arrival_tol_m if is_last else cfg.waypoint_tol_m
            err = self._fly_horizontal_via_gps(
                wp[0], wp[1], cfg.max_horizontal_speed_mps, self.nav_alt)
            if err < tol:
                if is_last:
                    self._settle += 1
                    if self._settle >= 5:
                        # Record what a GPS-only drop would miss by (true dist to marker).
                        self.metrics["gps_only_error_m"] = float(
                            np.hypot(true_pos[0] - self.marker_world[0],
                                    true_pos[1] - self.marker_world[1]))
                        self._transition(MissionState.CLIMB_TO_BALCONY_ALT)
                else:
                    self._cruise_idx += 1
                    self._settle = 0
            else:
                self._settle = 0

        # ---------------- CLIMB to search altitude ----------------
        elif s == MissionState.CLIMB_TO_BALCONY_ALT:
            self._fly_horizontal_via_gps(
                self.plan.target_east_m, self.plan.target_north_m,
                cfg.search_speed_mps, self.plan.search_altitude_m)
            if self.sensors.read_barometer() >= self.plan.search_altitude_m - 0.25:
                self._transition(MissionState.SEARCH_MARKER)

        # ---------------- SEARCH for the marker (vision acquires) ----------------
        elif s == MissionState.SEARCH_MARKER:
            if vis["target_found"] and vis["confidence"] > 0.5:
                self._settle += 1
                # Hover in place while confirming acquisition.
                self.drone.set_velocity_body(0.0, 0.0, 0.0, 0.0)
                if self._settle >= 3:
                    self._transition(MissionState.PRECISION_ALIGN, "marker acquired")
            else:
                self._settle = 0
                # Fly the expanding-square search pattern around the cruise target.
                dx, dy = self._search_wps[min(self._search_idx, len(self._search_wps) - 1)]
                tx = self.plan.target_east_m + dx
                ty = self.plan.target_north_m + dy
                err = self._fly_horizontal_via_gps(
                    tx, ty, cfg.search_speed_mps, self.plan.search_altitude_m)
                # Advance to the next search point once reached or after a dwell.
                self._search_dwell += 1
                if err < 0.6 or self._search_dwell > 24:
                    self._search_idx += 1
                    self._search_dwell = 0
                if self._search_idx >= len(self._search_wps):
                    self.metrics["fail_reason"] = "marker not found"
                    self._transition(MissionState.ASCEND, "search exhausted -> home")

        # ---------------- PRECISION ALIGN (vision) ----------------
        elif s == MissionState.PRECISION_ALIGN:
            if not vis["target_found"]:
                self._lost += 1
                self._hold_over_target_gps()      # GPS-hold (don't drift on the wind)
                if self._lost > 25:
                    self._transition(MissionState.SEARCH_MARKER, "lost during align")
            else:
                self._lost = 0
                v_e, v_n = self.horiz.update(self._f_e, self._f_n, dt)
                # Hold the search altitude with the rangefinder while centring.
                rf = self.sensors.read_rangefinder()
                target_h = cfg.search_alt_above_balcony_m
                cur_h = rf if rf is not None else self._f_h
                vz = float(np.clip(cfg.position_ctrl_gain * (target_h - cur_h),
                                -cfg.max_descent_rate_mps, cfg.max_climb_rate_mps))
                self.drone.set_velocity_body(v_e, v_n, vz, 0.0)
                offset = np.hypot(self._f_e, self._f_n)
                if offset < cfg.align_tol_m:
                    self._settle += 1
                    if self._settle >= cfg.align_settle_steps:
                        self._transition(MissionState.DESCEND, "centred -> descend")
                else:
                    self._settle = 0

        # ---------------- DESCEND (vision + rangefinder) ----------------
        elif s == MissionState.DESCEND:
            if not vis["target_found"]:
                self._lost += 1
                self._hold_over_target_gps()      # climb to safe alt + GPS-hold, no drift
                if self._lost > 25:
                    self._transition(MissionState.SEARCH_MARKER, "marker lost in descent")
            else:
                self._lost = 0
                offset = np.hypot(self._f_e, self._f_n)
                if offset > cfg.descend_abort_tol_m:
                    self._transition(MissionState.PRECISION_ALIGN, "offset grew -> re-align")
                else:
                    v_e, v_n = self.horiz.update(self._f_e, self._f_n, dt)
                    height = self._fused_height(vis)
                    target = cfg.release_height_above_balcony_m
                    vz = self.vert.update(height, target, dt)
                    self.drone.set_velocity_body(v_e, v_n, vz, 0.0)
                    if abs(height - target) < 0.12 and offset < cfg.drop_tol_m:
                        self._settle += 1
                        if self._settle >= cfg.drop_settle_steps:
                            self._transition(MissionState.DROP, "aligned & at height")
                    else:
                        self._settle = 0

        # ---------------- DROP ----------------
        elif s == MissionState.DROP:
            self.drone.set_velocity_body(0.0, 0.0, 0.0, 0.0)
            self.drone.actuate_servo(True)
            rec = self.payload.release(self.drone.get_telemetry(), self.marker_world)
            self.metrics["drop_error_m"] = rec["error_m"]
            self.metrics["drop_height_m"] = rec["release_height_m"]
            self._transition(MissionState.ASCEND, f"released ({rec['error_m']*100:.0f} cm)")

        # ---------------- ASCEND back to safe altitude ----------------
        elif s == MissionState.ASCEND:
            # Hold a FIXED anchor (the target) while climbing -- do NOT chase the
            # moving current position, or wind would push the drone away.
            self._fly_horizontal_via_gps(
                self.plan.target_east_m, self.plan.target_north_m,
                cfg.search_speed_mps, self.return_alt)
            if self.sensors.read_barometer() >= self.return_alt - 0.3:
                self._transition(MissionState.RETURN_HOME)

        # ---------------- RETURN HOME (GPS, following the planned route) -------
        elif s == MissionState.RETURN_HOME:
            wp = self._return_wps[self._return_idx]
            is_last = self._return_idx >= len(self._return_wps) - 1
            tol = cfg.home_arrival_tol_m if is_last else cfg.waypoint_tol_m
            err = self._fly_horizontal_via_gps(
                wp[0], wp[1], cfg.max_horizontal_speed_mps, self.return_alt)
            if err < tol:
                if is_last:
                    self._transition(MissionState.LAND)
                else:
                    self._return_idx += 1

        # ---------------- LAND ----------------
        elif s == MissionState.LAND:
            # Descend back to the launch height (the pad may be elevated, e.g. a
            # balcony) -- not all the way to z=0, which would fly through the pad.
            self._fly_horizontal_via_gps(self.home_xy[0], self.home_xy[1],
                                        cfg.search_speed_mps, self._start_z,
                                        use_rangefinder=True)
            rf = self.sensors.read_rangefinder()
            if (rf is not None and rf < 0.15) or self.drone.pos[2] <= self._start_z + 0.12:
                self.metrics["return_error_m"] = self._home_dist()
                self._finish()
                return  # finished; do not step physics further this tick

        elif s in (MissionState.DONE, MissionState.FAILED):
            self.done = True
            return

        # --- Advance physics and bookkeeping ---
        self.drone.step(dt)
        self.t += dt
        self.step_count += 1
        self.trajectory.append(self.drone.pos.copy())

        # --- 3D world: sync the kinematic body and check for a crash ---
        if self.world is not None:
            # The world body faces the travel heading so the front camera / LiDAR
            # look where the drone is going (flight control still uses yaw=0).
            self.world.set_drone_pose(self.drone.pos, self._heading)
            # "Climbed" = risen clear ABOVE the launch pad (which may itself be high
            # up, e.g. a balcony). Until then, resting on/just above the pad is fine.
            if self.drone.pos[2] > self._start_z + cfg.takeoff_clearance_m:
                self._has_climbed = True
            if self._collision_active():
                collided, obj, pt, gap = self.world.check_collision()
                if collided:
                    self._fail_collision(obj, pt, gap)
                    self._log_step(vis)
                    return

        self._log_step(vis)

    def _home_dist(self) -> float:
        return float(np.hypot(self.drone.pos[0] - self.home_xy[0],
                            self.drone.pos[1] - self.home_xy[1]))

    def _collision_active(self) -> bool:
        """
        Collisions count only AFTER takeoff clearance and BEFORE the final home
        landing. Ground/launch-pad contact at the start and end is allowed.
        """
        return (self._has_climbed
                and self.state not in (MissionState.LAND, MissionState.DONE,
                                        MissionState.FAILED))

    def _fail_collision(self, obj, pt, gap):
        """Record a crash and end the flight as FAILED."""
        self.metrics["collision"] = True
        self.metrics["collision_object"] = obj
        self.metrics["collision_pos"] = (None if pt is None else np.asarray(pt).tolist())
        self.metrics["collision_time_s"] = float(self.t)
        self.metrics["fail_reason"] = f"collision with {obj}"
        self.metrics["battery_used_pct"] = float(self.cfg.battery_start_pct - self.drone.battery_pct)
        self.metrics["duration_s"] = float(self.t)
        self.metrics["success"] = False
        if self.metrics["return_error_m"] is None:
            self.metrics["return_error_m"] = self._home_dist()
        self.state = MissionState.FAILED
        self.state_log.append((round(self.t, 2), "FAILED", f"collision with {obj}"))
        self.done = True

    def _log_step(self, vis):
        tel = self.drone.get_telemetry()
        self.history.append({
            "t": self.t,
            "state": self.state.name,
            "pos": tel["position"].copy(),
            "battery": tel["battery_pct"],
            "wind": tel["wind"].copy(),
            "height_above_marker_true": self.drone.height_above_surface(),
            "vision_offset": (None if not vis["target_found"]
                            else np.hypot(vis["offset_east"], vis["offset_north"])),
        })

    def _finish(self):
        # Land the drone and disarm cleanly (settle onto the launch pad height,
        # which may be elevated for a balcony/rooftop start).
        self.drone.pos[2] = self._start_z
        self.drone.vel[:] = 0.0
        try:
            self.drone.disarm()
        except Exception:
            pass
        b = self.drone.battery_pct
        self.metrics["battery_used_pct"] = float(self.cfg.battery_start_pct - b)
        self.metrics["duration_s"] = float(self.t)
        # Success = snack dropped accurately AND drone returned home.
        de = self.metrics["drop_error_m"]
        re = self.metrics["return_error_m"]
        self.metrics["success"] = bool(
            de is not None and de <= 0.20
            and re is not None and re <= self.cfg.return_success_tol_m
            and self.metrics["fail_reason"] is None)
        self.state = MissionState.DONE if self.metrics["success"] or de is not None else MissionState.FAILED
        self.state_log.append((round(self.t, 2), self.state.name, "mission end"))
        self.done = True

    # ------------------------------------------------------------------ #
    def run(self, on_step=None, max_steps: int | None = None):
        """Run to completion. on_step(mission) is called after each tick."""
        if max_steps is None:
            max_steps = int(self.cfg.max_mission_seconds / self.cfg.dt) + 200
        while not self.done and self.step_count < max_steps:
            self.step()
            if on_step is not None:
                on_step(self)
        if not self.done:  # safety: ran out of steps
            self.metrics["fail_reason"] = self.metrics["fail_reason"] or "step limit"
            if self.metrics["return_error_m"] is None:
                self.metrics["return_error_m"] = self._home_dist()
            self._finish()
        return self.metrics
