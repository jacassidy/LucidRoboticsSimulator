"""Robot scripting API — the object exposed to user control scripts as ``robot``.

Wraps a :class:`RobotModel` with runtime state: current joint positions, forward
kinematics, sensor evaluation, motor controllers, simulation time, and logging.

The same Robot instance is shared by the joint sliders, the telemetry panel, the
script runner, and the demo, so any of them can drive it and all observe the
result. FreeCAD is optional: pass a ``geometry_sync`` callback to move CAD
objects when link transforms change; without it the API is fully headless.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from .document_model import RobotModel
from .kinematics import Transform, forward_kinematics


class MotorCommand:
    """A simple motor setpoint: position control or velocity control."""

    def __init__(self, target_position=None, target_velocity=None, max_speed=2.0):
        self.target_position = target_position
        self.target_velocity = target_velocity
        self.max_speed = max_speed  # units/sec cap for position control


class Robot:
    def __init__(self, model: RobotModel, geometry_sync: Optional[Callable] = None):
        self.model = model
        self.time = 0.0
        self._motors: Dict[str, MotorCommand] = {}
        self._link_world: Dict[str, Transform] = {}
        # Callbacks(dt) run each step — used by the demo to apply gravity.
        self.physics_hooks: List[Callable[[float], None]] = []
        # Observers.
        self.log_listeners: List[Callable[[object], None]] = []
        self.telemetry_listeners: List[Callable[["Robot"], None]] = []
        # geometry_sync(link_name, Transform) moves the CAD object(s).
        self.geometry_sync = geometry_sync
        self.log_buffer: List[str] = []
        self.refresh_kinematics()

    # ---- kinematics ----------------------------------------------------
    def refresh_kinematics(self) -> None:
        self._link_world = forward_kinematics(
            list(self.model.links.values()),
            list(self.model.joints.values()),
            self.model.joint_values(),
        )
        if self.geometry_sync:
            for name, tf in self._link_world.items():
                try:
                    self.geometry_sync(name, tf)
                except Exception as exc:  # never let CAD sync kill a sim step
                    self.log("geometry_sync error on %s: %s" % (name, exc))

    # ---- joint access --------------------------------------------------
    def get_joint(self, name: str):
        if name not in self.model.joints:
            raise KeyError("No such joint: %r" % name)
        return self.model.joints[name]

    def set_joint_position(self, name: str, value: float) -> float:
        joint = self.get_joint(name)
        joint.position = joint.clamp(float(value))
        self.refresh_kinematics()
        return joint.position

    def get_joint_position(self, name: str) -> float:
        return self.get_joint(name).position

    def get_link_pose(self, name: str) -> Transform:
        if name not in self._link_world:
            raise KeyError("No such link: %r" % name)
        return self._link_world[name]

    # ---- motors --------------------------------------------------------
    def command_motor(self, name, target_position=None, target_velocity=None, max_speed=2.0):
        self.get_joint(name)  # validate
        self._motors[name] = MotorCommand(target_position, target_velocity, max_speed)

    def _apply_motors(self, dt: float) -> None:
        for name, cmd in self._motors.items():
            joint = self.model.joints.get(name)
            if joint is None or not joint.is_movable:
                continue
            if cmd.target_velocity is not None:
                joint.velocity = cmd.target_velocity
                joint.position = joint.clamp(joint.position + cmd.target_velocity * dt)
            elif cmd.target_position is not None:
                target = joint.clamp(cmd.target_position)
                delta = target - joint.position
                step = cmd.max_speed * dt
                if abs(delta) <= step:
                    joint.position = target
                    joint.velocity = 0.0
                else:
                    move = step if delta > 0 else -step
                    joint.position = joint.clamp(joint.position + move)
                    joint.velocity = move / dt if dt else 0.0

    # ---- sensors -------------------------------------------------------
    def read_sensor(self, name: str) -> float:
        if name not in self.model.sensors:
            raise KeyError("No such sensor: %r" % name)
        sensor = self.model.sensors[name]
        link_world = self._link_world.get(sensor.attached_link, Transform.identity())
        return sensor.compute(link_world)

    def _update_sensors(self) -> None:
        for name in self.model.sensors:
            try:
                self.read_sensor(name)
            except Exception as exc:
                self.log("sensor %s error: %s" % (name, exc))

    # ---- stepping ------------------------------------------------------
    def step(self, dt: float = 0.01) -> float:
        self._apply_motors(dt)
        for hook in list(self.physics_hooks):
            try:
                hook(dt)
            except Exception as exc:
                self.log("physics hook error: %s" % exc)
        self.refresh_kinematics()
        self._update_sensors()
        self.time += dt
        self._notify_telemetry()
        return self.time

    def reset(self) -> None:
        self.time = 0.0
        self._motors.clear()
        for j in self.model.joints.values():
            j.position = 0.0
            j.velocity = 0.0
        self.refresh_kinematics()
        self._update_sensors()
        self._notify_telemetry()

    # ---- logging / telemetry ------------------------------------------
    def log(self, value) -> None:
        if isinstance(value, dict):
            text = ", ".join("%s=%s" % (k, v) for k, v in value.items())
        else:
            text = str(value)
        self.log_buffer.append(text)
        for cb in list(self.log_listeners):
            try:
                cb(value)
            except Exception:
                pass

    def _notify_telemetry(self) -> None:
        for cb in list(self.telemetry_listeners):
            try:
                cb(self)
            except Exception:
                pass

    def telemetry_snapshot(self) -> dict:
        return {
            "time": self.time,
            "joints": {n: j.position for n, j in self.model.joints.items()},
            "links": {n: tf.translation for n, tf in self._link_world.items()},
            "sensors": {n: s.reading for n, s in self.model.sensors.items()},
        }
