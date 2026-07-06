"""FreeCAD glue: convert between our Transform and FreeCAD Placement, sync CAD
geometry to link transforms, read axes from selected geometry, and manage a
shared per-document Robot runtime.

Everything that touches ``FreeCAD``/``FreeCADGui`` lives here (and in commands/
ui) so the core package stays importable headless. All FreeCAD access is guarded.
"""

from __future__ import annotations

import math
from typing import Optional

from .document_model import RobotModel, load_from_document, save_to_document
from .kinematics import Transform
from .robot_api import Robot


def get_freecad():
    try:
        import FreeCAD
        return FreeCAD
    except Exception:
        return None


def get_gui():
    try:
        import FreeCADGui
        return FreeCADGui
    except Exception:
        return None


def active_document():
    fc = get_freecad()
    return fc.ActiveDocument if fc else None


# ---- Transform <-> Placement ------------------------------------------
def transform_to_placement(tf: Transform):
    """Build a FreeCAD.Placement from our Transform (returns None headless)."""
    fc = get_freecad()
    if fc is None:
        return None
    r = tf.rotation
    mat = fc.Matrix(
        r[0][0], r[0][1], r[0][2], tf.translation[0],
        r[1][0], r[1][1], r[1][2], tf.translation[1],
        r[2][0], r[2][1], r[2][2], tf.translation[2],
        0, 0, 0, 1,
    )
    return fc.Placement(mat)


def placement_to_transform(placement) -> Transform:
    """Build our Transform from a FreeCAD.Placement."""
    m = placement.Matrix
    rot = [
        [m.A11, m.A12, m.A13],
        [m.A21, m.A22, m.A23],
        [m.A31, m.A32, m.A33],
    ]
    return Transform(rot, (m.A14, m.A24, m.A34))


# ---- geometry sync -----------------------------------------------------
class GeometrySync:
    """Callable that moves a link's member objects to match its world transform.

    Records each object's *base* placement (captured at construction, relative to
    the link's initial world transform) so joint motion is applied on top of the
    object's original position rather than snapping everything to the origin.
    """

    def __init__(self, doc, model: RobotModel):
        self.doc = doc
        self.model = model
        self._base = {}      # obj_name -> base placement (captured at construction)
        self._initial = {}   # link_name -> link world Placement at construction
        self._capture()

    def _capture(self):
        for link in self.model.links.values():
            # Snapshot each link's initial world transform ONCE. Reading it live
            # in __call__ is wrong: physics hooks mutate link.world_transform, so
            # link_initial would track world and the object's motion would cancel.
            self._initial[link.name] = transform_to_placement(link.world_transform)
            for obj_name in link.objects:
                obj = getattr(self.doc, obj_name, None)
                if obj is not None and hasattr(obj, "Placement"):
                    self._base[obj_name] = obj.Placement

    def __call__(self, link_name: str, world: Transform):
        fc = get_freecad()
        if fc is None:
            return
        link = self.model.links.get(link_name)
        if link is None:
            return
        world_pl = transform_to_placement(world)
        link_initial = self._initial.get(link_name)
        if link_initial is None:
            link_initial = transform_to_placement(link.world_transform)
        for obj_name in link.objects:
            obj = getattr(self.doc, obj_name, None)
            if obj is None or not hasattr(obj, "Placement"):
                continue
            base = self._base.get(obj_name, obj.Placement)
            # new = world * (link_initial^-1 * base)
            rel = link_initial.inverse().multiply(base)
            obj.Placement = world_pl.multiply(rel)


# ---- axis from selection ----------------------------------------------
def axis_from_selection():
    """Try to derive a unit axis vector from the current GUI selection.

    Supports selecting a linear Edge (uses its direction) or two vertices.
    Returns a (x, y, z) tuple or None if nothing usable is selected.
    """
    gui = get_gui()
    if gui is None:
        return None
    sel = gui.Selection.getSelectionEx()
    for s in sel:
        for sub in getattr(s, "SubObjects", []):
            try:
                if hasattr(sub, "Curve") and hasattr(sub, "Vertexes") and len(sub.Vertexes) == 2:
                    p1 = sub.Vertexes[0].Point
                    p2 = sub.Vertexes[1].Point
                    v = (p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)
                    n = math.sqrt(sum(c * c for c in v))
                    if n > 1e-9:
                        return (v[0] / n, v[1] / n, v[2] / n)
            except Exception:
                continue
    return None


# ---- shared per-document runtime --------------------------------------
_RUNTIMES = {}  # doc.Name -> Robot


def get_robot(doc=None, rebuild: bool = False) -> Optional[Robot]:
    """Return (creating if needed) the shared Robot bound to `doc`."""
    doc = doc or active_document()
    if doc is None:
        return None
    key = doc.Name
    if rebuild or key not in _RUNTIMES:
        model = load_from_document(doc)
        sync = GeometrySync(doc, model)
        _RUNTIMES[key] = Robot(model, geometry_sync=sync)
    return _RUNTIMES[key]


def save_robot(doc=None) -> None:
    doc = doc or active_document()
    robot = _RUNTIMES.get(doc.Name) if doc else None
    if robot is not None:
        save_to_document(robot.model, doc)


def forget_robot(doc_name: str) -> None:
    _RUNTIMES.pop(doc_name, None)
