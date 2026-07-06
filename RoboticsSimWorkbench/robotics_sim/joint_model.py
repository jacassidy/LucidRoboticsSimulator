"""Joint data model.

A Joint connects a parent link to a child link. Plain data container (no FreeCAD
dependency) for JSON persistence and headless testing.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .kinematics import Transform

REVOLUTE = "revolute"
PRISMATIC = "prismatic"
FIXED = "fixed"

JOINT_TYPES = (REVOLUTE, PRISMATIC, FIXED)
MOVABLE_TYPES = (REVOLUTE, PRISMATIC)


class Joint:
    def __init__(
        self,
        name: str,
        joint_type: str,
        parent_link: str,
        child_link: str,
        origin: Optional[Transform] = None,
        axis: Sequence[float] = (0.0, 0.0, 1.0),
        lower_limit: float = -3.14159265,
        upper_limit: float = 3.14159265,
        position: float = 0.0,
        velocity: float = 0.0,
        effort_limit: Optional[float] = None,
    ):
        if joint_type not in JOINT_TYPES:
            raise ValueError(
                "Invalid joint type %r; expected one of %r" % (joint_type, JOINT_TYPES)
            )
        self.name = name
        self.type = joint_type
        self.parent_link = parent_link
        self.child_link = child_link
        self.origin: Transform = origin or Transform.identity()
        self.axis = tuple(float(a) for a in axis)
        self.lower_limit = float(lower_limit)
        self.upper_limit = float(upper_limit)
        self.position = float(position)
        self.velocity = float(velocity)
        self.effort_limit = effort_limit

    @property
    def is_movable(self) -> bool:
        return self.type in MOVABLE_TYPES

    def clamp(self, value: float) -> float:
        """Clamp a target value to [lower, upper] for movable joints."""
        if not self.is_movable:
            return 0.0
        lo, hi = self.lower_limit, self.upper_limit
        if lo > hi:  # tolerate swapped limits
            lo, hi = hi, lo
        return max(lo, min(hi, value))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "parent_link": self.parent_link,
            "child_link": self.child_link,
            "origin": self.origin.to_dict(),
            "axis": list(self.axis),
            "lower_limit": self.lower_limit,
            "upper_limit": self.upper_limit,
            "position": self.position,
            "velocity": self.velocity,
            "effort_limit": self.effort_limit,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Joint":
        return cls(
            name=d["name"],
            joint_type=d["type"],
            parent_link=d["parent_link"],
            child_link=d["child_link"],
            origin=Transform.from_dict(d.get("origin") or {}),
            axis=d.get("axis", (0.0, 0.0, 1.0)),
            lower_limit=d.get("lower_limit", -3.14159265),
            upper_limit=d.get("upper_limit", 3.14159265),
            position=d.get("position", 0.0),
            velocity=d.get("velocity", 0.0),
            effort_limit=d.get("effort_limit"),
        )

    def __repr__(self) -> str:  # pragma: no cover
        return "Joint(%r, %s, %s->%s)" % (
            self.name, self.type, self.parent_link, self.child_link,
        )
