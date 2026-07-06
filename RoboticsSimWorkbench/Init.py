"""FreeCAD Init.py — loaded for BOTH GUI and console (headless) sessions.

Kept minimal: no GUI imports here. The heavy lifting (workbench registration,
panels) happens in InitGui.py. We just make sure the package directory is
importable so `import robotics_sim` works from the FreeCAD Python console.
"""

import os
import sys

FreeCAD_addon_name = "RoboticsSimWorkbench"


def _locate_addon_dir():
    """Return this addon's directory.

    FreeCAD 1.1 exec's Init.py / InitGui.py without ``__file__`` in the
    namespace, so ``os.path.dirname(__file__)`` raises ``NameError`` and aborts
    the whole file. Fall back to scanning the Mod directories FreeCAD knows
    about for our addon folder.
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
