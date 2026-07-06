"""Pure-Python kinematics: transforms and forward kinematics.

This module deliberately has NO FreeCAD dependency so it can be unit-tested
headless and reused by the exporters and the simulation loop. Transforms are
represented by a small :class:`Transform` (translation + 3x3 rotation matrix)
implemented with plain Python lists — no numpy required.

Phase 2 note: if/when numpy or FreeCAD.Base.Matrix become guaranteed, this can
be swapped for a faster backend behind the same Transform API.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

Vec3 = Tuple[float, float, float]
Mat3 = List[List[float]]


def _identity3() -> Mat3:
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def _matmul3(a: Mat3, b: Mat3) -> Mat3:
    return [
        [sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def _matvec3(m: Mat3, v: Sequence[float]) -> Vec3:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def normalize(v: Sequence[float]) -> Vec3:
    """Return a unit vector; raises ValueError on a zero-length axis."""
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n < 1e-12:
        raise ValueError("Cannot normalize a zero-length vector (invalid axis).")
    return (v[0] / n, v[1] / n, v[2] / n)


def rotation_from_axis_angle(axis: Sequence[float], angle: float) -> Mat3:
    """Rodrigues' rotation formula. `angle` in radians."""
    x, y, z = normalize(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1.0 - c
    return [
        [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
        [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
    ]


def matrix_to_rpy(m: Mat3) -> Vec3:
    """Extract fixed-axis roll-pitch-yaw (XYZ) from a rotation matrix.

    Used by exporters (URDF origin rpy). Returns radians (roll, pitch, yaw).
    """
    sy = -m[2][0]
    sy = max(-1.0, min(1.0, sy))
    pitch = math.asin(sy)
    if abs(sy) < 0.99999:
        roll = math.atan2(m[2][1], m[2][2])
        yaw = math.atan2(m[1][0], m[0][0])
    else:  # gimbal lock
        roll = math.atan2(-m[1][2], m[1][1])
        yaw = 0.0
    return (roll, pitch, yaw)


class Transform:
    """Rigid transform: rotation (3x3) then translation (3-vector)."""

    __slots__ = ("rotation", "translation")

    def __init__(self, rotation: Mat3 = None, translation: Sequence[float] = None):
        self.rotation: Mat3 = rotation if rotation is not None else _identity3()
        self.translation: Vec3 = (
            tuple(translation) if translation is not None else (0.0, 0.0, 0.0)
        )

    @classmethod
    def identity(cls) -> "Transform":
        return cls()

    @classmethod
    def from_translation(cls, t: Sequence[float]) -> "Transform":
        return cls(_identity3(), tuple(t))

    def compose(self, other: "Transform") -> "Transform":
        """Return self * other (apply `other` first, then self)."""
        r = _matmul3(self.rotation, other.rotation)
        t_rot = _matvec3(self.rotation, other.translation)
        t = (
            t_rot[0] + self.translation[0],
            t_rot[1] + self.translation[1],
            t_rot[2] + self.translation[2],
        )
        return Transform(r, t)

    def apply_point(self, p: Sequence[float]) -> Vec3:
        rp = _matvec3(self.rotation, p)
        return (
            rp[0] + self.translation[0],
            rp[1] + self.translation[1],
            rp[2] + self.translation[2],
        )

    def rpy(self) -> Vec3:
        return matrix_to_rpy(self.rotation)

    def to_dict(self) -> dict:
        return {"rotation": self.rotation, "translation": list(self.translation)}

    @classmethod
    def from_dict(cls, d: dict) -> "Transform":
        if not d:
            return cls.identity()
        return cls(d.get("rotation"), d.get("translation"))

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return "Transform(t=%r)" % (self.translation,)


def joint_transform(joint_type: str, axis: Sequence[float], value: float) -> Transform:
    """Local motion transform produced by a joint at position `value`.

    revolute  -> rotation about axis by `value` radians
    prismatic -> translation along axis by `value` (document units)
    fixed     -> identity
    """
    jt = (joint_type or "fixed").lower()
    if jt == "revolute":
        return Transform(rotation_from_axis_angle(axis, value))
    if jt == "prismatic":
        u = normalize(axis)
        return Transform.from_translation((u[0] * value, u[1] * value, u[2] * value))
    return Transform.identity()


def _attr(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name)


def _has(obj, name) -> bool:
    if isinstance(obj, dict):
        return name in obj
    return hasattr(obj, name)


def build_joint_graph(joints) -> Tuple[Dict[str, list], Dict[str, str]]:
    """Return (children_by_link, parent_joint_name_by_link)."""
    children: Dict[str, list] = {}
    parent_joint: Dict[str, str] = {}
    for j in joints:
        parent = _attr(j, "parent_link")
        child = _attr(j, "child_link")
        children.setdefault(parent, []).append(j)
        parent_joint[child] = _attr(j, "name")
    return children, parent_joint


def forward_kinematics(links, joints, joint_values: Dict[str, float]) -> Dict[str, Transform]:
    """Compute world transform for every link by walking the joint tree.

    Root links (no parent joint) keep their stored ``world_transform`` (or
    identity). Cycles and orphans are guarded against.
    """
    link_names = [_attr(l, "name") for l in links]
    link_by_name = {_attr(l, "name"): l for l in links}
    children, parent_joint = build_joint_graph(joints)

    def base_transform(link) -> Transform:
        wt = _attr(link, "world_transform") if _has(link, "world_transform") else None
        if isinstance(wt, Transform):
            return wt
        if isinstance(wt, dict):
            return Transform.from_dict(wt)
        return Transform.identity()

    world: Dict[str, Transform] = {}
    roots = [n for n in link_names if n not in parent_joint]
    visited = set()

    stack = [(r, base_transform(link_by_name[r])) for r in roots]
    while stack:
        name, world_tf = stack.pop()
        if name in visited:
            continue
        visited.add(name)
        world[name] = world_tf
        for joint in children.get(name, []):
            child = _attr(joint, "child_link")
            if child not in link_by_name:
                continue
            origin = _attr(joint, "origin")
            origin_tf = (
                origin if isinstance(origin, Transform) else Transform.from_dict(origin or {})
            )
            val = joint_values.get(_attr(joint, "name"), 0.0) or 0.0
            motion = joint_transform(
                _attr(joint, "type"), _attr(joint, "axis") or (0, 0, 1), val
            )
            child_world = world_tf.compose(origin_tf).compose(motion)
            stack.append((child, child_world))

    for name in link_names:
        if name not in world:
            world[name] = base_transform(link_by_name[name])
    return world
