"""Simple simulation helpers for v1.

Full rigid-body dynamics is out of scope for Phase 1. This module provides just
enough physics for the falling-block demo: a gravity integrator that drives a
single link's world-transform Z, with a ground floor. It is registered as a
``physics_hook`` on the :class:`Robot` so ``robot.step(dt)`` advances it.

Phase 2 replaces this with live MuJoCo / Chrono / Bullet backends behind the
same "hook that mutates link transforms" contract.
"""

from __future__ import annotations

from typing import Optional

from .kinematics import Transform
from .robot_api import Robot

DEFAULT_GRAVITY = -9810.0  # mm/s^2 (FreeCAD default length unit is mm)


class GravityBody:
    """Integrates one link falling under gravity onto a ground plane."""

    def __init__(
        self,
        robot: Robot,
        link_name: str,
        gravity: float = DEFAULT_GRAVITY,
        ground_height: float = 0.0,
        restitution: float = 0.0,
    ):
        self.robot = robot
        self.link_name = link_name
        self.gravity = gravity
        self.ground_height = ground_height
        self.restitution = restitution
        self.velocity = 0.0

    def _link(self):
        return self.robot.model.links[self.link_name]

    def step(self, dt: float) -> None:
        link = self._link()
        tf = link.world_transform
        x, y, z = tf.translation
        self.velocity += self.gravity * dt
        z += self.velocity * dt
        if z <= self.ground_height:
            z = self.ground_height
            # bounce with restitution (0 = rest on floor)
            self.velocity = -self.velocity * self.restitution
            if abs(self.velocity) < 1e-6:
                self.velocity = 0.0
        link.world_transform = Transform(tf.rotation, (x, y, z))

    def attach(self) -> "GravityBody":
        self.robot.physics_hooks.append(self.step)
        return self


def run_headless(robot: Robot, steps: int, dt: float = 0.01,
                 sensor_name: Optional[str] = None):
    """Utility: run `steps` sim steps, return list of (time, sensor_reading)."""
    out = []
    for _ in range(steps):
        robot.step(dt)
        reading = robot.read_sensor(sensor_name) if sensor_name else None
        out.append((robot.time, reading))
    return out
