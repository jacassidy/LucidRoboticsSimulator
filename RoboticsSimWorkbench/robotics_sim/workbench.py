"""The RoboticsSim FreeCAD workbench definition.

Registers the command set into a toolbar + menu and opens the dock panels
(telemetry left, terminal bottom) when the workbench is first activated.

This module is imported by InitGui.py inside FreeCAD. ``Gui.Workbench`` is only
available in the GUI; a plain fallback base keeps import from exploding if this
file is ever imported headless.
"""

from __future__ import annotations

import os

try:
    import FreeCADGui as Gui
    _Base = Gui.Workbench
except Exception:  # headless / import-time safety
    Gui = None
    _Base = object

ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")


class RoboticsSimWorkbench(_Base):
    MenuText = "RoboticsSim"
    ToolTip = "Turn FreeCAD geometry into a programmable articulated robot"
    Icon = os.path.join(ICON_DIR, "workbench.svg")

    def Initialize(self):
        """Called once when the workbench is first activated."""
        from . import commands
        names = commands.register_commands()
        self.appendToolbar("RoboticsSim", names)
        self.appendMenu("RoboticsSim", names)

    def Activated(self):
        """Open the dock panels (incl. Simulation Controls) on switching in."""
        try:
            from .ui import terminal_panel
            from .commands import _open_simulation
            # Open controls by default. create_doc=False: don't spawn an empty
            # document just for switching workbenches; rebuild=False: reuse a
            # scene already built for the open document (no duplicate geometry).
            _open_simulation(rebuild=False, create_doc=False)
            terminal_panel.log("RoboticsSim workbench activated.")
        except Exception as exc:
            print("RoboticsSim activate error:", exc)

    def Deactivated(self):
        pass

    def GetClassName(self):
        # Tells FreeCAD this is a Python workbench.
        return "Gui::PythonWorkbench"
