"""Document-level robot metadata model + FreeCAD persistence.

:class:`RobotModel` is a pure-Python container holding all links, joints, and
sensors plus export settings. It (de)serializes to JSON, which is what gets
stored inside the FreeCAD document so the robot survives save/reload.

Persistence strategy: a single hidden ``App::FeaturePython`` document object
named ``RoboticsSimData`` carries a ``String`` property ``Metadata`` holding the
JSON blob. FreeCAD calls are isolated in :func:`load_from_document` /
:func:`save_to_document` and guarded so this module imports fine headless.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from .joint_model import Joint, MOVABLE_TYPES
from .link_model import Link
from .sensor_model import Sensor

METADATA_OBJECT_NAME = "RoboticsSimData"
METADATA_PROPERTY = "Metadata"
SCHEMA_VERSION = 1


class DuplicateNameError(ValueError):
    pass


class RobotModel:
    def __init__(self, name: str = "robot"):
        self.name = name
        self.links: Dict[str, Link] = {}
        self.joints: Dict[str, Joint] = {}
        self.sensors: Dict[str, Sensor] = {}
        self.export_settings: dict = {
            "urdf_mesh_dir": "meshes",
            "mjcf_mesh_dir": "meshes",
            "length_scale": 0.001,  # FreeCAD mm -> meters for exporters
        }

    # ---- mutation with validation -------------------------------------
    def add_link(self, link: Link) -> Link:
        if link.name in self.links:
            raise DuplicateNameError("Link %r already exists." % link.name)
        self.links[link.name] = link
        return link

    def add_joint(self, joint: Joint) -> Joint:
        if joint.name in self.joints:
            raise DuplicateNameError("Joint %r already exists." % joint.name)
        if joint.parent_link not in self.links:
            raise ValueError("Parent link %r does not exist." % joint.parent_link)
        if joint.child_link not in self.links:
            raise ValueError("Child link %r does not exist." % joint.child_link)
        self.joints[joint.name] = joint
        # Maintain link back-references.
        self.links[joint.parent_link].child_joints.append(joint.name)
        self.links[joint.child_link].parent_joint = joint.name
        return joint

    def add_sensor(self, sensor: Sensor) -> Sensor:
        if sensor.name in self.sensors:
            raise DuplicateNameError("Sensor %r already exists." % sensor.name)
        if sensor.attached_link not in self.links:
            raise ValueError("Sensor link %r does not exist." % sensor.attached_link)
        self.sensors[sensor.name] = sensor
        return sensor

    def rename_link(self, old: str, new: str) -> None:
        if old not in self.links:
            raise ValueError("No such link %r" % old)
        if new in self.links:
            raise DuplicateNameError("Link %r already exists." % new)
        link = self.links.pop(old)
        link.name = new
        self.links[new] = link
        for j in self.joints.values():
            if j.parent_link == old:
                j.parent_link = new
            if j.child_link == old:
                j.child_link = new
        for s in self.sensors.values():
            if s.attached_link == old:
                s.attached_link = new

    def movable_joints(self) -> List[Joint]:
        return [j for j in self.joints.values() if j.type in MOVABLE_TYPES]

    def joint_values(self) -> Dict[str, float]:
        return {name: j.position for name, j in self.joints.items()}

    # ---- serialization -------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "name": self.name,
            "links": [l.to_dict() for l in self.links.values()],
            "joints": [j.to_dict() for j in self.joints.values()],
            "sensors": [s.to_dict() for s in self.sensors.values()],
            "export_settings": self.export_settings,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "RobotModel":
        model = cls(d.get("name", "robot"))
        model.export_settings.update(d.get("export_settings") or {})
        for ld in d.get("links", []):
            model.links[ld["name"]] = Link.from_dict(ld)
        for jd in d.get("joints", []):
            model.joints[jd["name"]] = Joint.from_dict(jd)
        for sd in d.get("sensors", []):
            model.sensors[sd["name"]] = Sensor.from_dict(sd)
        return model

    @classmethod
    def from_json(cls, text: str) -> "RobotModel":
        return cls.from_dict(json.loads(text))


# ---------------------------------------------------------------------------
# FreeCAD persistence — guarded so the module imports without FreeCAD.
# ---------------------------------------------------------------------------
def _get_freecad():
    try:
        import FreeCAD  # noqa: F401
        return FreeCAD
    except Exception:
        return None


def get_metadata_object(doc):
    """Return the hidden metadata object in `doc`, or None."""
    if doc is None:
        return None
    return getattr(doc, METADATA_OBJECT_NAME, None) or _find_by_name(doc, METADATA_OBJECT_NAME)


def _find_by_name(doc, name):
    for obj in getattr(doc, "Objects", []):
        if obj.Name == name:
            return obj
    return None


def ensure_metadata_object(doc):
    """Create the metadata carrier object if missing; return it."""
    obj = get_metadata_object(doc)
    if obj is not None:
        return obj
    obj = doc.addObject("App::FeaturePython", METADATA_OBJECT_NAME)
    obj.addProperty("App::PropertyString", METADATA_PROPERTY, "RoboticsSim",
                    "Serialized robot metadata (JSON)")
    setattr(obj, METADATA_PROPERTY, "{}")
    try:
        obj.ViewObject.Visibility = False
    except Exception:
        pass
    return obj


def save_to_document(model: RobotModel, doc) -> None:
    """Persist model JSON into the FreeCAD document."""
    if doc is None:
        raise RuntimeError("No FreeCAD document to save into.")
    obj = ensure_metadata_object(doc)
    setattr(obj, METADATA_PROPERTY, model.to_json())
    try:
        doc.recompute()
    except Exception:
        pass


def load_from_document(doc) -> RobotModel:
    """Reconstruct a RobotModel from the document, or a fresh empty model."""
    obj = get_metadata_object(doc)
    if obj is None:
        name = getattr(doc, "Name", "robot") if doc is not None else "robot"
        return RobotModel(name)
    text = getattr(obj, METADATA_PROPERTY, "") or "{}"
    try:
        data = json.loads(text)
    except Exception:
        data = {}
    if not data:
        name = getattr(doc, "Name", "robot") if doc is not None else "robot"
        return RobotModel(name)
    return RobotModel.from_dict(data)
