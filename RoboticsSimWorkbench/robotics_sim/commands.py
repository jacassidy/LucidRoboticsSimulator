"""FreeCAD GUI command classes for the RoboticsSim workbench.

Each class follows the FreeCAD command protocol (GetResources / Activated /
IsActive) and is registered with FreeCADGui.addCommand under a ``RoboticsSim_*``
name. This module is only imported inside FreeCAD (InitGui), but every FreeCAD
call is still guarded so import never hard-fails.

Commands share the per-document Robot runtime via freecad_bridge, persist model
changes into the document, and report status/errors to the terminal panel and,
where useful, message boxes.
"""

from __future__ import annotations

import os

from . import freecad_bridge as bridge
from .document_model import DuplicateNameError
from .joint_model import Joint
from .kinematics import Transform
from .link_model import Link
from .exporters import write_urdf, write_mjcf
from .script_runner import run_script
from .ui import terminal_panel, telemetry_panel, joint_slider_panel, simulation_panel, dialogs
from .demos import scene_template
from .demos.demo_control_script import CONTROL_SNIPPET

ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")


def _icon(name):
    path = os.path.join(ICON_DIR, name)
    return path if os.path.exists(path) else ""


def _log(text):
    terminal_panel.log(text)


def _require_doc():
    doc = bridge.active_document()
    if doc is None:
        dialogs.error_box("RoboticsSim", "No FreeCAD document is open.")
        _log("[error] No document open.")
    return doc


def _refresh_ui(robot):
    try:
        telemetry_panel.get_panel().bind(robot)
    except Exception:
        pass
    try:
        joint_slider_panel.get_panel().bind(robot)
    except Exception:
        pass


class _Command:
    """Base with common resource plumbing."""
    name = "RoboticsSim_Base"
    menu_text = "Base"
    tooltip = ""
    icon = ""

    def GetResources(self):
        return {"Pixmap": _icon(self.icon), "MenuText": self.menu_text, "ToolTip": self.tooltip}

    def IsActive(self):
        return bridge.active_document() is not None

    def Activated(self):  # pragma: no cover - overridden
        raise NotImplementedError


class CreateLink(_Command):
    name = "RoboticsSim_CreateLink"
    menu_text = "Create Link"
    tooltip = "Group selected objects into a named rigid link"
    icon = "create_link.svg"

    def Activated(self):
        doc = _require_doc()
        if doc is None:
            return
        gui = bridge.get_gui()
        sel = gui.Selection.getSelection() if gui else []
        if not sel:
            dialogs.error_box("Create Link", "Select one or more objects first.")
            _log("[error] Create Link: nothing selected.")
            return
        name, ok = dialogs.ask_text("Create Link", "Link name:", "link%d" %
                                    (len(bridge.get_robot(doc).model.links) + 1))
        if not ok or not name:
            return
        robot = bridge.get_robot(doc)
        obj_names = [o.Name for o in sel]
        world = Transform.identity()
        first = getattr(doc, obj_names[0], None)
        if first is not None and hasattr(first, "Placement"):
            world = bridge.placement_to_transform(first.Placement)
        try:
            robot.model.add_link(Link(name=name, objects=obj_names, world_transform=world))
        except DuplicateNameError as exc:
            dialogs.error_box("Create Link", exc)
            _log("[error] %s" % exc)
            return
        robot.refresh_kinematics()
        bridge.save_robot(doc)
        _refresh_ui(robot)
        _log("[ok] Created link %r from %s" % (name, ", ".join(obj_names)))


class CreateJoint(_Command):
    name = "RoboticsSim_CreateJoint"
    menu_text = "Create Joint"
    tooltip = "Create a joint connecting two links"
    icon = "create_joint.svg"

    def Activated(self):
        doc = _require_doc()
        if doc is None:
            return
        robot = bridge.get_robot(doc)
        names = list(robot.model.links.keys())
        if len(names) < 2:
            dialogs.error_box("Create Joint", "Need at least two links first.")
            _log("[error] Create Joint: need >= 2 links.")
            return
        dlg = dialogs.JointDialog(names, axis_picker=bridge.axis_from_selection)
        if not dlg.exec_():
            return
        v = dlg.values()
        if v["parent_link"] == v["child_link"]:
            dialogs.error_box("Create Joint", "Parent and child must differ.")
            return
        try:
            joint = Joint(
                name=v["name"], joint_type=v["type"],
                parent_link=v["parent_link"], child_link=v["child_link"],
                axis=v["axis"], lower_limit=v["lower_limit"], upper_limit=v["upper_limit"],
                origin=self._origin(robot, v["parent_link"], v["child_link"]),
            )
            robot.model.add_joint(joint)
        except (DuplicateNameError, ValueError) as exc:
            dialogs.error_box("Create Joint", exc)
            _log("[error] %s" % exc)
            return
        robot.refresh_kinematics()
        bridge.save_robot(doc)
        _refresh_ui(robot)
        _log("[ok] Created %s joint %r (%s -> %s)" %
             (v["type"], v["name"], v["parent_link"], v["child_link"]))

    def _origin(self, robot, parent, child):
        """Child origin relative to parent = parent_world^-1 * child_world.

        Computed in translation only via a cheap approximation for v1: use the
        stored child world minus parent world (identity rotation origin). Good
        enough for kinematic preview; exporters read the same origin.
        """
        p = robot.model.links[parent].world_transform.translation
        c = robot.model.links[child].world_transform.translation
        return Transform.from_translation((c[0] - p[0], c[1] - p[1], c[2] - p[2]))


class EditJoint(_Command):
    name = "RoboticsSim_EditJoint"
    menu_text = "Edit Joint"
    tooltip = "Edit an existing joint's axis and limits"
    icon = "edit_joint.svg"

    def Activated(self):
        doc = _require_doc()
        if doc is None:
            return
        robot = bridge.get_robot(doc)
        if not robot.model.joints:
            dialogs.error_box("Edit Joint", "No joints to edit.")
            return
        jnames = list(robot.model.joints.keys())
        jname, ok = dialogs.ask_text("Edit Joint", "Joint name (%s):" % ", ".join(jnames),
                                     jnames[0])
        if not ok or jname not in robot.model.joints:
            if ok:
                dialogs.error_box("Edit Joint", "No such joint: %r" % jname)
            return
        existing = robot.model.joints[jname]
        dlg = dialogs.JointDialog(list(robot.model.links.keys()),
                                  axis_picker=bridge.axis_from_selection, existing=existing)
        if not dlg.exec_():
            return
        v = dlg.values()
        existing.type = v["type"]
        existing.axis = tuple(v["axis"])
        existing.lower_limit = v["lower_limit"]
        existing.upper_limit = v["upper_limit"]
        existing.position = existing.clamp(existing.position)
        robot.refresh_kinematics()
        bridge.save_robot(doc)
        _refresh_ui(robot)
        _log("[ok] Edited joint %r" % jname)


class JointSliders(_Command):
    name = "RoboticsSim_JointSliders"
    menu_text = "Joint Sliders"
    tooltip = "Open the joint sliders panel"
    icon = "sliders.svg"

    def Activated(self):
        doc = _require_doc()
        if doc is None:
            return
        robot = bridge.get_robot(doc)
        panel = joint_slider_panel.get_panel(robot)
        panel.rebuild()
        _show_dock(panel, "Joint Sliders", area="right")
        _log("[ok] Joint sliders opened (%d movable joints)." %
             len(robot.model.movable_joints()))


class RunScript(_Command):
    name = "RoboticsSim_RunScript"
    menu_text = "Run Script"
    tooltip = "Run a Python control script against the robot"
    icon = "run_script.svg"

    def Activated(self):
        doc = _require_doc()
        if doc is None:
            return
        robot = bridge.get_robot(doc)
        # Mirror robot.log into the terminal.
        if _log not in robot.log_listeners:
            robot.log_listeners.append(lambda v: _log(_fmt_log(v)))
        _refresh_ui(robot)

        def on_run(code):
            _log("[script] running…")
            run_script(code, robot, log=_log)
            bridge.save_robot(doc)
            _refresh_ui(robot)

        dlg = dialogs.ScriptDialog(on_run, initial_code=CONTROL_SNIPPET.strip())
        dlg.exec_()


class ExportURDF(_Command):
    name = "RoboticsSim_ExportURDF"
    menu_text = "Export URDF"
    tooltip = "Export the robot to a URDF file"
    icon = "export_urdf.svg"

    def Activated(self):
        _export(self, write_urdf, "URDF", "*.urdf")


class ExportMJCF(_Command):
    name = "RoboticsSim_ExportMJCF"
    menu_text = "Export MJCF"
    tooltip = "Export the robot to a MuJoCo MJCF file"
    icon = "export_mjcf.svg"

    def Activated(self):
        _export(self, write_mjcf, "MJCF", "*.xml")


class SimulationControls(_Command):
    name = "RoboticsSim_SimControls"
    menu_text = "Simulation Controls"
    tooltip = "Open play / pause / speed / reset controls for the scene"
    icon = "sim_controls.svg"

    # Can spin up its own scene, so it is active even before a document exists.
    def IsActive(self):
        return True

    def Activated(self):
        # Explicit user click -> rebuild the scene from scene_template (picks up
        # any edits the user made to that file).
        _open_simulation(rebuild=True, create_doc=True)


# Cached scene per document so re-opening the panel / switching workbenches does
# not spawn duplicate geometry or reset a running sim.
_SCENES = {}


def _tee_terminal(robot):
    """Mirror robot.log(...) into the terminal panel, exactly once per robot."""
    if getattr(robot, "_terminal_teed", False):
        return
    robot.log_listeners.append(lambda v: _log(_fmt_log(v)))
    robot._terminal_teed = True


def _make_redraw(doc):
    gui = bridge.get_gui()

    def redraw():
        try:
            doc.recompute()
        except Exception:
            pass
        if gui is not None:
            try:
                gui.updateGui()
            except Exception:
                pass

    return redraw


def _open_simulation(rebuild=False, create_doc=True):
    """Open the Simulation Controls panel bound to the document's scene.

    ``rebuild`` forces a fresh scene from scene_template; otherwise a cached
    scene is reused. ``create_doc`` allows creating an empty document when none
    is open (True for the toolbar command, False for workbench auto-open).
    """
    fc = bridge.get_freecad()
    if fc is None:
        _log("[error] FreeCAD not available.")
        return

    _show_dock(terminal_panel.get_panel(), "RoboticsSim Terminal", area="bottom")
    _show_dock(telemetry_panel.get_panel(), "RoboticsSim Telemetry", area="left")
    panel = simulation_panel.get_panel()

    doc = bridge.active_document()
    if doc is None and create_doc:
        doc = fc.newDocument("RoboticsSimScene")
    if doc is None:
        # No document to build against — just surface the (empty) controls.
        _show_dock(panel, "Simulation Controls", area="right")
        return

    scene = _SCENES.get(doc.Name)
    if scene is None or rebuild:
        scene = scene_template.build(
            doc=doc,
            geometry_sync_factory=lambda model: bridge.GeometrySync(doc, model),
        )
        _SCENES[doc.Name] = scene
        bridge._RUNTIMES[doc.Name] = scene.robot
        _tee_terminal(scene.robot)
        _log("[ok] Scene %r built. Press Play." % scene.name)

    try:
        fc.Gui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass

    panel.bind(scene, redraw=_make_redraw(doc))
    _show_dock(panel, "Simulation Controls", area="right")
    _refresh_ui(scene.robot)


# ---- helpers -----------------------------------------------------------
def _fmt_log(v):
    if isinstance(v, dict):
        return ", ".join("%s=%s" % (k, val) for k, val in v.items())
    return str(v)


def _export(cmd, writer, label, pattern):
    doc = _require_doc()
    if doc is None:
        return
    robot = bridge.get_robot(doc)
    if not robot.model.links:
        dialogs.error_box("Export %s" % label, "No links to export.")
        _log("[error] Export %s: model is empty." % label)
        return
    from .ui import QT_AVAILABLE, QtWidgets
    if QT_AVAILABLE:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Export %s" % label, "%s_%s" % (robot.model.name, label.lower()), pattern
        )
    else:
        path = "%s.%s" % (robot.model.name, "urdf" if label == "URDF" else "xml")
    if not path:
        return
    try:
        writer(robot.model, path)
    except Exception as exc:
        dialogs.error_box("Export %s" % label, exc)
        _log("[error] Export %s failed: %s" % (label, exc))
        return
    _log("[ok] Exported %s -> %s" % (label, path))


def _show_dock(widget, title, area="right"):
    """Wrap a widget in a QDockWidget and add it to the FreeCAD main window."""
    from .ui import QT_AVAILABLE, QtWidgets, QtCore
    if not QT_AVAILABLE:
        return
    gui = bridge.get_gui()
    if gui is None:
        return
    mw = gui.getMainWindow()
    existing = mw.findChild(QtWidgets.QDockWidget, title)
    if existing is not None:
        existing.setWidget(widget)
        existing.show()
        return existing
    dock = QtWidgets.QDockWidget(title, mw)
    dock.setObjectName(title)
    dock.setWidget(widget)
    areas = {
        "left": QtCore.Qt.LeftDockWidgetArea,
        "right": QtCore.Qt.RightDockWidgetArea,
        "bottom": QtCore.Qt.BottomDockWidgetArea,
    }
    mw.addDockWidget(areas.get(area, QtCore.Qt.RightDockWidgetArea), dock)
    return dock


# Ordered list used by the workbench + registration.
ALL_COMMANDS = [
    CreateLink, CreateJoint, EditJoint, JointSliders,
    SimulationControls, RunScript, ExportURDF, ExportMJCF,
]


def register_commands():
    """Register every command with FreeCADGui. Safe to call once at GUI init."""
    gui = bridge.get_gui()
    if gui is None:
        return []
    names = []
    for cls in ALL_COMMANDS:
        try:
            gui.addCommand(cls.name, cls())
            names.append(cls.name)
        except Exception as exc:
            print("RoboticsSim: failed to register %s: %s" % (cls.name, exc))
    return names
