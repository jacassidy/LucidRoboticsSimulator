"""Scene = a runnable simulation: a Robot + a default time step + reset support.

This is the object the Simulation Controls panel drives (play / pause / speed /
reset). It is deliberately FreeCAD-free so scenes can be built and stepped in a
plain-CPython unit test.

A :class:`Scene` snapshots the initial link transforms and joint positions when
it is created, so :meth:`reset` can restore the exact starting state. Physics
objects that carry hidden state (e.g. a falling body's velocity) register a
reset callback via :meth:`add_reset`.

Typical use (see ``demos/scene_template.py`` for a fully worked example)::

    robot = Robot(model, geometry_sync=sync)
    gravity = GravityBody(robot, "block").attach()
    scene = Scene(robot, dt=0.01, name="falling_block")
    scene.add_reset(lambda: setattr(gravity, "velocity", 0.0))
    scene.step()    # advance one dt
    scene.reset()   # back to the start
"""

from __future__ import annotations

from typing import Callable, List

from .robot_api import Robot


class Scene:
    """A robot plus everything needed to play, pause, step and reset it."""

    def __init__(self, robot: Robot, dt: float = 0.01, name: str = "scene"):
        self.robot = robot
        self.dt = float(dt)
        self.name = name
        self._reset_hooks: List[Callable[[], None]] = []
        # Callbacks(scene) run after every step — used to log telemetry live.
        self.on_step: List[Callable[["Scene"], None]] = []
        self._snapshot: dict = {}
        self.snapshot()

    # ---- reset support -------------------------------------------------
    def add_reset(self, fn: Callable[[], None]) -> None:
        """Register a callback run on :meth:`reset` (restore physics state)."""
        self._reset_hooks.append(fn)

    def add_step_hook(self, fn: Callable[["Scene"], None]) -> None:
        """Register a callback(scene) run after each :meth:`step`."""
        self.on_step.append(fn)

    def snapshot(self) -> None:
        """Capture the current state as the point :meth:`reset` returns to.

        Call again after you have arranged the scene the way you want "start" to
        look (the constructor already calls it once).
        """
        self._snapshot = {
            "links": {
                name: link.world_transform
                for name, link in self.robot.model.links.items()
            },
            "joints": {
                name: joint.position
                for name, joint in self.robot.model.joints.items()
            },
        }

    def reset(self) -> None:
        """Restore the snapshotted start state and rewind sim time to zero."""
        for name, tf in self._snapshot.get("links", {}).items():
            link = self.robot.model.links.get(name)
            if link is not None:
                link.world_transform = tf
        for name, pos in self._snapshot.get("joints", {}).items():
            joint = self.robot.model.joints.get(name)
            if joint is not None:
                joint.position = pos
                joint.velocity = 0.0
        for fn in list(self._reset_hooks):
            try:
                fn()
            except Exception as exc:  # never let one bad hook block reset
                self.robot.log("scene reset hook error: %s" % exc)
        self.robot.time = 0.0
        self.robot._motors.clear()
        self.robot.refresh_kinematics()
        self.robot._update_sensors()
        self.robot._notify_telemetry()

    # ---- stepping ------------------------------------------------------
    def step(self, dt: float = None) -> float:
        """Advance the sim by ``dt`` (defaults to :attr:`dt`). Returns new time."""
        t = self.robot.step(self.dt if dt is None else dt)
        for fn in list(self.on_step):
            try:
                fn(self)
            except Exception as exc:
                self.robot.log("scene step hook error: %s" % exc)
        return t
