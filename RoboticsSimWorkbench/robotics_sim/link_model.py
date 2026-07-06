"""Link data model.

A Link is a rigid body composed of one or more FreeCAD objects. This class is a
plain data container (no FreeCAD dependency) so it can be serialized to JSON and
tested headless. FreeCAD object references are stored by *name* (the object's
``Name`` in its document), not by live object handles, so metadata survives
save/reload.
"""

from __future__ import annotations

from typing import List, Optional

from .kinematics import Transform

# Placeholder inertial defaults for v1 (units follow the FreeCAD document).
DEFAULT_MASS = 1.0
# Unit diagonal inertia tensor [ixx, ixy, ixz, iyy, iyz, izz].
DEFAULT_INERTIA = [1.0, 0.0, 0.0, 1.0, 0.0, 1.0]


class Link:
    def __init__(
        self,
        name: str,
        objects: Optional[List[str]] = None,
        mass: float = DEFAULT_MASS,
        inertia: Optional[List[float]] = None,
        visual_refs: Optional[List[str]] = None,
        collision_refs: Optional[List[str]] = None,
        world_transform: Optional[Transform] = None,
        parent_joint: Optional[str] = None,
        child_joints: Optional[List[str]] = None,
    ):
        self.name = name
        # FreeCAD object Names that make up this rigid body.
        self.objects: List[str] = list(objects or [])
        self.mass = mass
        self.inertia = list(inertia) if inertia is not None else list(DEFAULT_INERTIA)
        # Default visual/collision geometry = the member objects.
        self.visual_refs: List[str] = list(visual_refs) if visual_refs is not None else list(self.objects)
        self.collision_refs: List[str] = (
            list(collision_refs) if collision_refs is not None else list(self.objects)
        )
        self.world_transform: Transform = world_transform or Transform.identity()
        self.parent_joint = parent_joint
        self.child_joints: List[str] = list(child_joints or [])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "objects": list(self.objects),
            "mass": self.mass,
            "inertia": list(self.inertia),
            "visual_refs": list(self.visual_refs),
            "collision_refs": list(self.collision_refs),
            "world_transform": self.world_transform.to_dict(),
            "parent_joint": self.parent_joint,
            "child_joints": list(self.child_joints),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Link":
        return cls(
            name=d["name"],
            objects=d.get("objects"),
            mass=d.get("mass", DEFAULT_MASS),
            inertia=d.get("inertia"),
            visual_refs=d.get("visual_refs"),
            collision_refs=d.get("collision_refs"),
            world_transform=Transform.from_dict(d.get("world_transform") or {}),
            parent_joint=d.get("parent_joint"),
            child_joints=d.get("child_joints"),
        )

    def __repr__(self) -> str:  # pragma: no cover
        return "Link(%r, objects=%r)" % (self.name, self.objects)
