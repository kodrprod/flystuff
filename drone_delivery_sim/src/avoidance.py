"""
avoidance.py
============
Sensor-only reactive obstacle avoidance — the realistic kind.

The drone is NOT allowed to know what the world looks like. This navigator works
from a single realistic input: a **LiDAR distance scan** (produced by
`world.horizontal_scan`, which ray-casts the sensor against the world and returns
only distances — exactly what a real spinning LiDAR gives), plus the direction the
drone WANTS to go, derived from its own noisy GPS. No object positions, no map,
no peeking at the true geometry.

Method — a local potential field (steer-to-clearest), blended with the goal:

  * Every LiDAR return closer than `avoid_range_m` pushes the drone AWAY from that
    bearing, harder the closer it is. Summed up, this is a repulsion vector that
    keeps real clearance from walls AND corners (a corner off to the side still
    pushes, which pure "follow the gap" misses).
  * That repulsion is added to the goal-seeking velocity.
  * If the push is nearly opposite the goal (the drone is pointed straight at a
    wall with the goal behind it), a tangential "slide" is added so it follows the
    wall around instead of stalling head-on.
  * Speed eases off the closer things get; the final command is speed-limited.

Pure numpy on arrays (no world access), so it is trivially unit-testable and uses
nothing but the sensor reading it is handed.
"""

from __future__ import annotations
import numpy as np


def wrap(a):
    """Wrap angle(s) to (-pi, pi]."""
    return (np.asarray(a, dtype=float) + np.pi) % (2.0 * np.pi) - np.pi


def repulse(goal_vel, bearings, clear, cfg):
    """
    Bend a goal-seeking velocity around obstacles using only a LiDAR scan, AND slow
    down as obstacles loom ahead so there is always time to turn/stop.

    goal_vel : desired 2-D velocity toward the goal (m/s)
    bearings : world bearing of each LiDAR ray (radians, 1-D array)
    clear    : open distance along each ray (metres, 1-D array)
    cfg      : config (avoid_range_m, avoid_gain, lidar_reflex_stop_m,
            avoid_brake_decel_mps2, avoid_min_speed_mps, avoid_fwd_cone_deg,
            max_horizontal_speed_mps)

    Returns (velocity_2d, active: bool). active=False => open air, unchanged.
    """
    goal_vel = np.asarray(goal_vel, float)
    bearings = np.asarray(bearings, float)
    clear = np.asarray(clear, float)
    speed = float(np.linalg.norm(goal_vel))
    if speed < 1e-6:
        return goal_vel, False

    R = float(cfg.avoid_range_m)
    stop = float(cfg.lidar_reflex_stop_m)
    vmax = float(cfg.max_horizontal_speed_mps)
    vmin = float(getattr(cfg, "avoid_min_speed_mps", 0.6))
    decel = float(getattr(cfg, "avoid_brake_decel_mps2", 2.0))
    cone = np.radians(float(getattr(cfg, "avoid_fwd_cone_deg", 55.0)))

    gdir = goal_vel / speed
    gbear = float(np.arctan2(gdir[1], gdir[0]))

    # --- Proactive braking: cap speed to what we could shed before the nearest
    # obstacle in the direction we're heading (v = sqrt(2*a*d)). ---
    fwd = np.abs(wrap(bearings - gbear)) < cone
    fwd_clear = float(clear[fwd].min()) if np.any(fwd) else float(clear.min())
    v_brake = float(np.sqrt(2.0 * decel * max(fwd_clear - stop, 0.0)))
    v_cap = min(speed, v_brake)                       # never above what the goal asked
    braking = v_cap < speed - 1e-3

    near = clear < R
    if not braking and not np.any(near):
        return goal_vel, False                        # open air -> unchanged

    if braking:                                       # keep creeping so it can slide past
        v_cap = max(v_cap, vmin)
    base = gdir * v_cap                                # slowed goal-seeking velocity
    v = base

    if np.any(near):
        b = bearings[near]
        d = clear[near]
        w = np.clip((R - d) / R, 0.0, 1.0) ** 2       # 0 at the edge -> 1 touching
        toward = np.stack([np.cos(b), np.sin(b)], axis=1)
        rep = -(toward * w[:, None]).sum(axis=0)      # summed push AWAY from hits
        if np.linalg.norm(rep) > 1e-9:
            v = base + rep * v_cap * cfg.avoid_gain
            # Deadlock breaker: push nearly opposite the goal (pointed at a wall) ->
            # add a tangential slide toward whichever side faces the goal.
            nr = rep / np.linalg.norm(rep)
            if float(gdir @ nr) < -0.3:
                perp = np.array([-nr[1], nr[0]])
                if perp @ gdir < 0:
                    perp = -perp
                v = v + perp * max(v_cap, vmin) * cfg.avoid_gain

    # Respect the horizontal speed limit, and keep a minimum creep when avoiding.
    m = float(np.linalg.norm(v))
    if m > vmax:
        v = v / m * vmax
    elif 1e-6 < m < vmin:
        v = v / m * vmin
    return v, True


def vertical_clearances(goal_vel, az, el, clear, cfg):
    """
    From a 3-D LiDAR scan, return the open distances that decide a vertical maneuver,
    all measured along the goal bearing:

      fwd   : at the drone's height (incl. a slightly-down ray, so "clear" means the
            body — not just the centre — is above the obstacle's top)
      over  : a ~40-deg up-forward ray (can a climb get over the top from here?)
      ceil  : steep-up rays (is the sky above open, i.e. can we keep climbing?)
      under : steep-down rays (is there room to drop below it?)
    """
    goal_vel = np.asarray(goal_vel, float)
    az = np.asarray(az, float); el = np.asarray(el, float); clear = np.asarray(clear, float)
    gaz = float(np.arctan2(goal_vel[1], goal_vel[0]))
    cone = np.radians(float(cfg.avoid_fwd_cone_deg))
    ahead = np.abs(wrap(az - gaz)) < cone
    mr = float(cfg.lidar_range_m)

    def _min(mask):
        return float(clear[mask].min()) if np.any(mask) else mr

    fwd = _min(ahead & (el < np.radians(6.0)) & (el > np.radians(-14.0)))
    over = _min(ahead & (el > np.radians(33.0)) & (el < np.radians(52.0)))
    ceil = _min(ahead & (el > np.radians(65.0)))
    under = _min(ahead & (el < np.radians(-25.0)))
    return fwd, over, ceil, under


def vertical_avoid(goal_vel, az, el, clear, cfg, ground_clear=None):
    """
    Stateless single-shot vertical decision (used by the unit tests and as a
    fallback): climb OVER if blocked ahead but open above; duck UNDER if blocked
    above but open below with ground room; otherwise 0 (steer around).
    Returns (vertical_rate, active).
    """
    if not bool(getattr(cfg, "avoid_vertical", True)):
        return 0.0, False
    if float(np.linalg.norm(np.asarray(goal_vel, float))) < 1e-6:
        return 0.0, False
    fwd, over, ceil, under = vertical_clearances(goal_vel, az, el, clear, cfg)
    trig = float(cfg.avoid_climb_trigger_m)
    need = float(cfg.avoid_climb_clear_m)
    # "Can clear it" = the up-forward ray reaches (near) OPEN SKY over the top, not
    # merely travels a few metres up a tall face.
    sky = 0.8 * float(cfg.lidar_range_m)
    if fwd >= trig:
        return 0.0, False
    rate = float(cfg.avoid_climb_rate_mps) * float(np.clip((trig - fwd) / trig, 0.35, 1.0))
    if over > sky and ceil > need:
        return +rate, True
    if (under > sky and ground_clear is not None
            and ground_clear > need + float(cfg.avoid_ground_margin_m)):
        return -rate, True
    return 0.0, False
