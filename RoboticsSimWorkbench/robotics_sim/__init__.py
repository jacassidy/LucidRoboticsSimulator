"""RoboticsSim — FreeCAD workbench for turning CAD geometry into programmable
articulated robots.

The subpackage is split into a FreeCAD-independent core (kinematics, data
models, exporters, robot API, simulation) and FreeCAD-facing glue (workbench,
commands, ui, freecad_bridge). The core imports and tests fine headless; the
glue is only imported inside FreeCAD.
"""

from .kinematics import Transform, forward_kinematics
from .link_model import Link
from .joint_model import Joint, REVOLUTE, PRISMATIC, FIXED
from .sensor_model import Sensor, DISTANCE
from .document_model import RobotModel
from .robot_api import Robot

__version__ = "0.1.0"

__all__ = [
    "Transform",
    "forward_kinematics",
    "Link",
    "Joint",
    "REVOLUTE",
    "PRISMATIC",
    "FIXED",
    "Sensor",
    "DISTANCE",
    "RobotModel",
    "Robot",
    "__version__",
]
