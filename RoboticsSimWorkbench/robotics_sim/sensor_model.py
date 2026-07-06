"""Sensor data model + built-in simulated sensors.

v1 ships one sensor type: DistanceSensor, measuring the distance from an
attached link (plus a local offset) down to a ground plane. The compute logic is
pure Python (no FreeCAD) so it can run inside the demo loop and be unit-tested.

Phase 2: camera / IMU / contact sensors plug in via the same Sensor container +
a registry of compute functions keyed by ``type``.
"""

from __future__ import annotations

from typing import Optional

from .kinematics import Transform

DISTANCE = "distance"
SENSOR_TYPES = (DISTANCE,)


class Sensor:
    def __init__(
        self,
        name: str,
        sensor_type: str,
        attached_link: str,
        local_pose: Optional[Transform] = None,
        max_range: float = 1000.0,
        ground_height: float = 0.0,
        reading: float = 0.0,
    ):
        if sensor_type not in SENSOR_TYPES:
            raise ValueError(
                "Invalid sensor type %r; expected one of %r" % (sensor_type, SENSOR_TYPES)
            )
        self.name = name
        self.type = sensor_type
        self.attached_link = attached_link
        self.local_pose: Transform = local_pose or Transform.identity()
        self.max_range = float(max_range)
        # Ground plane Z used by the distance sensor.
        self.ground_height = float(ground_height)
        self.reading = float(reading)

    def compute(self, link_world: Transform) -> float:
        """Compute the reading given the attached link's world transform.

        For DISTANCE: world Z of the sensor origin minus ground height, clamped
        to [0, max_range]. -1.0 means out of range (beyond max_range).
        """
        if self.type == DISTANCE:
            sensor_world = link_world.compose(self.local_pose)
            z = sensor_world.translation[2]
            dist = z - self.ground_height
            if dist < 0.0:
                dist = 0.0
            if dist > self.max_range:
                self.reading = -1.0
                return self.reading
            self.reading = dist
            return dist
        return self.reading

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "attached_link": self.attached_link,
            "local_pose": self.local_pose.to_dict(),
            "max_range": self.max_range,
            "ground_height": self.ground_height,
            "reading": self.reading,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Sensor":
        return cls(
            name=d["name"],
            sensor_type=d["type"],
            attached_link=d["attached_link"],
            local_pose=Transform.from_dict(d.get("local_pose") or {}),
            max_range=d.get("max_range", 1000.0),
            ground_height=d.get("ground_height", 0.0),
            reading=d.get("reading", 0.0),
        )

    def __repr__(self) -> str:  # pragma: no cover
        return "Sensor(%r, %s, on=%s)" % (self.name, self.type, self.attached_link)
