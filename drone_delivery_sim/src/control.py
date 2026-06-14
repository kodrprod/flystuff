"""
control.py
==========
The flight controllers that turn "where is the marker relative to me" into
velocity commands for the drone. These are classic PID controllers.

Two jobs:
  * HorizontalController : drives the horizontal offset to the marker -> 0
    (keeps the drone centred directly above the marker).
  * VerticalController   : drives the height-above-marker -> a target release
    height (the controlled descent).

All gains live in config.py so they can be tuned in one place. The output of
these controllers is a velocity command that is fed to
drone.set_velocity_body(vx, vy, vz). Because we never command yaw, the body
frame stays aligned with East/North, so vx == East velocity, vy == North.
"""

from __future__ import annotations
import numpy as np

from config import CONFIG


class PID:
    """A minimal PID controller with integral anti-windup and output clamping."""

    def __init__(self, kp, ki, kd, i_limit, out_limit=None):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.i_limit = i_limit
        self.out_limit = out_limit
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.prev_error = None

    def update(self, error: float, dt: float) -> float:
        # Integral term with anti-windup clamp.
        self.integral = float(np.clip(self.integral + error * dt,
                                    -self.i_limit, self.i_limit))
        # Derivative term (0 on the first sample).
        deriv = 0.0 if self.prev_error is None else (error - self.prev_error) / dt
        self.prev_error = error
        out = self.kp * error + self.ki * self.integral + self.kd * deriv
        if self.out_limit is not None:
            out = float(np.clip(out, -self.out_limit, self.out_limit))
        return out


class HorizontalController:
    """
    Centres the drone over the marker. Input is the marker's offset relative to
    the drone (East, North), in meters, as recovered by vision. Output is an
    (East, North) velocity command. Driving the offset to zero parks the drone
    directly above the marker.
    """

    def __init__(self, config=CONFIG):
        self.cfg = config
        lim = config.max_horizontal_speed_mps
        self.pid_e = PID(config.horiz_kp, config.horiz_ki, config.horiz_kd,
                        config.horiz_i_limit, out_limit=lim)
        self.pid_n = PID(config.horiz_kp, config.horiz_ki, config.horiz_kd,
                        config.horiz_i_limit, out_limit=lim)

    def reset(self):
        self.pid_e.reset()
        self.pid_n.reset()

    def update(self, offset_east: float, offset_north: float, dt: float):
        """Return (v_east, v_north) velocity command in m/s."""
        v_e = self.pid_e.update(offset_east, dt)
        v_n = self.pid_n.update(offset_north, dt)
        return v_e, v_n


class VerticalController:
    """
    Controls the descent. Input is the current (fused) height above the marker
    and the target release height. Output is a vertical velocity command
    (negative = descend).
    """

    def __init__(self, config=CONFIG):
        self.cfg = config
        lim = max(config.max_climb_rate_mps, config.max_descent_rate_mps)
        self.pid = PID(config.vert_kp, config.vert_ki, config.vert_kd,
                    config.vert_i_limit, out_limit=lim)

    def reset(self):
        self.pid.reset()

    def update(self, height: float, target_height: float, dt: float) -> float:
        """Return v_z in m/s (negative descends toward the target height)."""
        error = target_height - height       # too high -> negative -> descend
        return self.pid.update(error, dt)
