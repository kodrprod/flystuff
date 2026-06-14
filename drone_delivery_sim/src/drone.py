"""
drone.py
========
The SIMULATED drone: a simple but honest flight-physics model PLUS a
command interface that deliberately mimics MAVSDK / MAVLink.

Why mimic MAVSDK?
-----------------
In the real system a tiny flight controller (STM32 / "Arduino-class") stabilises
the motors and executes movement commands, while a companion computer
(Raspberry Pi) runs the vision. The companion talks to the flight controller
with MAVLink-style commands like arm(), takeoff(), goto(), set_velocity_body().

By giving this simulated drone the SAME method names, the higher-level code
(mission.py, control.py, vision.py) never needs to know whether it is driving a
simulation or a real drone. To go to real hardware later you replace ONLY this
file with a thin MAVSDK wrapper (see "Where this goes next" in the README).

Public "flight controller API" (these are the methods you would also find on a
real MAVSDK vehicle object):

    arm()                         -> power up motors, allow flight
    disarm()                      -> stop motors (only when essentially landed)
    takeoff(target_alt)           -> climb straight up to an altitude
    goto_local(x, y, z)           -> fly to a local ENU position (autopilot holds it)
    goto_global(lat, lon, alt)    -> same, but given a GPS coordinate
    set_velocity_body(vx,vy,vz,yaw_rate) -> velocity control (used for precision)
    land()                        -> descend to the ground beneath the drone
    actuate_servo(release=True)   -> trigger the payload-release servo
    get_telemetry()               -> dict of current vehicle state

Coordinate frame is the project-wide LOCAL ENU meters frame (see config.py).
"""

from __future__ import annotations
import numpy as np

from config import CONFIG


class WindField:
    """
    Environmental wind = a steady base vector + smoothly-varying turbulence.

    Turbulence is modelled as a first-order auto-regressive ("red noise") process
    so gusts are correlated in time (realistic) rather than white jitter. Both the
    base wind and the gusts are amplified close to the building wall to emulate
    rotor wash and eddies, which is exactly where precision matters most.
    """

    def __init__(self, config=CONFIG, rng: np.random.Generator | None = None):
        self.cfg = config
        self.rng = rng if rng is not None else np.random.default_rng(config.seed)
        base = config.wind_base_mps
        self.base = np.array([base[0], base[1], 0.0], dtype=np.float64)
        self._gust = np.zeros(3, dtype=np.float64)
        # AR(1) coefficient: 0.9 -> gusts persist ~0.5 s at 20 Hz.
        self._a = 0.9
        # Scale so the stationary std-dev of the gust equals the configured value.
        self._b = config.wind_turbulence_mps * np.sqrt(1.0 - self._a ** 2)

    def _building_factor(self, pos: np.ndarray) -> float:
        """1.0 far from the balcony, ramping up to the multiplier at the wall."""
        bx, by = self.cfg.target_east_m, self.cfg.target_north_m
        dist = np.hypot(pos[0] - bx, pos[1] - by)
        r = self.cfg.wind_building_radius_m
        if dist >= r:
            return 1.0
        ramp = 1.0 - dist / r                      # 0 at edge, 1 at the wall
        return 1.0 + (self.cfg.wind_building_multiplier - 1.0) * ramp

    def velocity(self, pos: np.ndarray) -> np.ndarray:
        """Return the instantaneous wind velocity vector (m/s) at a position."""
        # Advance the gust process. Vertical gusts are weaker than horizontal.
        noise = self.rng.normal(0.0, 1.0, 3)
        noise[2] *= 0.4
        self._gust = self._a * self._gust + self._b * noise
        factor = self._building_factor(pos)
        # Base wind is partly disturbed near the wall; gusts are strongly amplified.
        return self.base * (0.6 + 0.4 * factor) + self._gust * factor


class Drone:
    """A simulated multirotor with a MAVSDK-style command interface."""

    def __init__(self, config=CONFIG, rng: np.random.Generator | None = None,
                start_pos: np.ndarray | None = None):
        self.cfg = config
        self.rng = rng if rng is not None else np.random.default_rng(config.seed)
        self.wind = WindField(config, self.rng)

        # --- Vehicle state ---
        self.pos = np.array([0.0, 0.0, 0.0]) if start_pos is None else np.array(start_pos, float)
        self.vel = np.zeros(3, dtype=np.float64)   # airframe velocity (m/s)
        self.yaw = 0.0                             # radians, 0 = East
        self.battery_pct = config.battery_start_pct
        self.armed = False
        self.servo_released = False
        self.t = 0.0                               # seconds since construction
        self.last_wind = np.zeros(3)

        # --- Control mode / setpoints (set by the command methods) ---
        self._mode = "idle"                        # idle|position|velocity|land
        self._pos_setpoint = self.pos.copy()
        self._vel_setpoint = np.zeros(3)           # body-frame velocity command
        self._vel_yaw_rate = 0.0

    # ------------------------------------------------------------------ #
    #  MAVSDK-style command interface                                    #
    # ------------------------------------------------------------------ #
    def arm(self) -> None:
        """Power up the motors. Must be called before takeoff."""
        self.armed = True
        self._mode = "position"
        self._pos_setpoint = self.pos.copy()

    def disarm(self) -> None:
        """Stop the motors. Only allowed when essentially on the ground."""
        if self.pos[2] > 0.2:
            raise RuntimeError("Refusing to disarm while airborne (z=%.2f m)" % self.pos[2])
        self.armed = False
        self._mode = "idle"
        self.vel[:] = 0.0

    def takeoff(self, target_alt: float) -> None:
        """Climb vertically to `target_alt` (meters above home ground)."""
        if not self.armed:
            raise RuntimeError("Cannot take off before arm()")
        self._mode = "position"
        self._pos_setpoint = np.array([self.pos[0], self.pos[1], target_alt])

    def goto_local(self, x: float, y: float, z: float) -> None:
        """Fly to a LOCAL ENU position; the autopilot holds it against wind."""
        self._mode = "position"
        self._pos_setpoint = np.array([x, y, z], dtype=np.float64)

    def goto_global(self, lat: float, lon: float, alt: float) -> None:
        """Fly to a GPS coordinate (converted to the local frame via geo.py)."""
        from src.geo import global_to_local
        local = global_to_local(lat, lon, alt,
                                self.cfg.home_lat, self.cfg.home_lon, self.cfg.home_alt_m)
        self.goto_local(local[0], local[1], local[2])

    def set_velocity_body(self, vx: float, vy: float, vz: float, yaw_rate: float = 0.0) -> None:
        """
        Velocity control in the BODY frame (forward/left/up), used for the
        precision phases. With yaw held at 0 the body frame aligns with ENU.
        """
        self._mode = "velocity"
        self._vel_setpoint = np.array([vx, vy, vz], dtype=np.float64)
        self._vel_yaw_rate = yaw_rate

    def land(self) -> None:
        """Descend straight down to the ground beneath the drone."""
        self._mode = "land"
        self._pos_setpoint = np.array([self.pos[0], self.pos[1], 0.0])

    def actuate_servo(self, release: bool = True) -> None:
        """Trigger (or reset) the payload-release servo. Telemetry exposes the state."""
        self.servo_released = release

    def get_telemetry(self) -> dict:
        """Snapshot of everything a companion computer could read from MAVLink."""
        return {
            "time": self.t,
            "position": self.pos.copy(),          # local ENU meters (ground truth)
            "velocity": (self.vel + self.last_wind).copy(),  # ground velocity
            "yaw": self.yaw,
            "battery_pct": self.battery_pct,
            "armed": self.armed,
            "mode": self._mode,
            "servo_released": self.servo_released,
            "wind": self.last_wind.copy(),
        }

    # ------------------------------------------------------------------ #
    #  Physics                                                           #
    # ------------------------------------------------------------------ #
    def _commanded_velocity(self) -> np.ndarray:
        """Work out the target airframe velocity for the current mode."""
        cfg = self.cfg
        if self._mode in ("position", "land"):
            error = self._pos_setpoint - self.pos
            v = cfg.position_ctrl_gain * error
        elif self._mode == "velocity":
            # Rotate body-frame command into the world ENU frame by yaw.
            c, s = np.cos(self.yaw), np.sin(self.yaw)
            vx, vy, vz = self._vel_setpoint
            v = np.array([vx * c - vy * s, vx * s + vy * c, vz])
        else:  # idle
            v = np.zeros(3)
        return v

    def _clamp_velocity(self, v: np.ndarray) -> np.ndarray:
        """Apply horizontal speed, climb and descent limits."""
        cfg = self.cfg
        horiz = v[:2]
        speed = np.linalg.norm(horiz)
        if speed > cfg.max_horizontal_speed_mps:
            horiz = horiz / speed * cfg.max_horizontal_speed_mps
        vz = np.clip(v[2], -cfg.max_descent_rate_mps, cfg.max_climb_rate_mps)
        return np.array([horiz[0], horiz[1], vz])

    def step(self, dt: float | None = None) -> None:
        """Advance the simulation by one timestep."""
        cfg = self.cfg
        dt = cfg.dt if dt is None else dt
        self.t += dt

        if not self.armed and self._mode == "idle":
            self.last_wind = np.zeros(3)
            return

        # 1. Desired airframe velocity for this control mode.
        v_cmd = self._clamp_velocity(self._commanded_velocity())

        # 2. First-order response: accelerate toward the command, accel-limited.
        dv = v_cmd - self.vel
        dv_mag = np.linalg.norm(dv)
        max_dv = cfg.max_accel_mps2 * dt
        if dv_mag > max_dv:
            dv = dv / dv_mag * max_dv
        self.vel = self.vel + dv

        # 3. Yaw integrates its commanded rate (usually zero here).
        if self._mode == "velocity":
            self.yaw += self._vel_yaw_rate * dt

        # 4. External disturbance: wind pushes the airframe over the ground.
        wind = self.wind.velocity(self.pos)
        self.last_wind = wind
        self.pos = self.pos + (self.vel + wind) * dt

        # 5. The ground is a hard floor.
        if self.pos[2] < 0.0:
            self.pos[2] = 0.0
            if self.vel[2] < 0.0:
                self.vel[2] = 0.0

        # 6. Battery drain: a hover baseline plus a term scaled by control effort.
        effort = abs(self.vel[2]) + 0.3 * np.linalg.norm(self.vel[:2])
        drain = (cfg.battery_hover_drain_pct_per_s
                + cfg.battery_throttle_drain_pct_per_s * effort) * dt
        self.battery_pct = max(0.0, self.battery_pct - drain)

    # Convenience used by sensors / mission (ground-truth height above floor).
    def height_above_surface(self) -> float:
        """True height of the drone above whatever surface is directly below it."""
        cfg = self.cfg
        x, y, z = self.pos
        on_balcony = (abs(x - cfg.target_east_m) <= cfg.balcony_width_m / 2 and
                    abs(y - cfg.target_north_m) <= cfg.balcony_depth_m / 2)
        surface = cfg.balcony_height_m if (on_balcony and z >= cfg.balcony_height_m) else 0.0
        return z - surface
