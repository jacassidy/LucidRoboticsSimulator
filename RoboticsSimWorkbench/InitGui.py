"""FreeCAD InitGui.py — loaded only in GUI sessions.

Registers the RoboticsSim workbench with FreeCAD so it appears in the workbench
selector. Import errors are printed rather than raised so a broken load never
takes down FreeCAD's whole GUI init.
"""

import os
import sys

FreeCAD_addon_name = "RoboticsSimWorkbench"


def _locate_addon_dir():
    """Return this addon's directory even when ``__file__`` is undefined.

    FreeCAD 1.1 exec's InitGui.py without ``__file__`` in the namespace, so the
    naive ``os.path.dirname(__file__)`` raises ``NameError`` and the workbench
    never registers. Fall back to scanning FreeCAD's known Mod directories.
    """
    try:
        return os.path.dirname(__file__)
    except NameError:
        pass
    import FreeCAD
    bases = [
        FreeCAD.getUserAppDataDir(),
        FreeCAD.getResourceDir(),
        FreeCAD.getHomePath(),
    ]
    for base in bases:
        candidate = os.path.join(base, "Mod", "RoboticsSimWorkbench")
        if os.path.isdir(candidate):
            return candidate
    return None


_THIS_DIR = _locate_addon_dir()
if _THIS_DIR and _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import FreeCADGui as Gui

# Register the real workbench directly. FreeCAD attaches its C++ ``__Workbench__``
# to the exact instance passed to ``addWorkbench``; wrapping it in a second
# loader object and delegating to a separate inner instance breaks
# ``self.appendToolbar`` (the inner instance was never registered).
try:
    from robotics_sim.workbench import RoboticsSimWorkbench
    Gui.addWorkbench(RoboticsSimWorkbench())
except Exception as exc:  # pragma: no cover
    import traceback
    print("RoboticsSim: failed to register workbench:", exc)
    traceback.print_exc()
