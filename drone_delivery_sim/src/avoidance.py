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
    Bend a goal-seeking velocity around obstacles using only a LiDAR scan.

    goal_vel : desired 2-D velocity toward the goal (m/s)
    bearings : world bearing of each LiDAR ray (radians, 1-D array)
    clear    : open distance along each ray (metres, 1-D array)
    cfg      : config (avoid_range_m, avoid_gain, lidar_reflex_stop_m,
            search_speed_mps, max_horizontal_speed_mps)

    Returns (velocity_2d, active: bool). active=False => open air, unchanged.
    """
    goal_vel = np.asarray(goal_vel, float)
    bearings = np.asarray(bearings, float)
    clear = np.asarray(clear, float)
    speed = float(np.linalg.norm(goal_vel))
    R = cfg.avoid_range_m

    near = clear < R
    if speed < 1e-6 or not np.any(near):
        return goal_vel, False

    b = bearings[near]
    d = clear[near]
    w = np.clip((R - d) / R, 0.0, 1.0) ** 2                 # 0 at the edge -> 1 touching
    toward = np.stack([np.cos(b), np.sin(b)], axis=1)        # unit vec toward each hit
    rep = -(toward * w[:, None]).sum(axis=0)                 # summed push AWAY from hits
    if np.linalg.norm(rep) < 1e-9:
        return goal_vel, False

    v = goal_vel + rep * speed * cfg.avoid_gain

    # Deadlock breaker: if the push is nearly opposite the goal (pointed straight at
    # a wall), add a tangential slide toward whichever side faces the goal.
    ng = goal_vel / (speed + 1e-9)
    nr = rep / (np.linalg.norm(rep) + 1e-9)
    if float(ng @ nr) < -0.3:
        perp = np.array([-nr[1], nr[0]])
        if perp @ ng < 0:
            perp = -perp
        v = v + perp * speed * cfg.avoid_gain

    # Very close ahead -> ease off the throttle (don't barrel in).
    if float(d.min()) < cfg.lidar_reflex_stop_m:
        m = np.linalg.norm(v)
        if m > 1e-9:
            v = v / m * min(m, cfg.search_speed_mps * 0.6)

    # Respect the horizontal speed limit.
    m = np.linalg.norm(v)
    if m > cfg.max_horizontal_speed_mps:
        v = v / m * cfg.max_horizontal_speed_mps
    return v, True
