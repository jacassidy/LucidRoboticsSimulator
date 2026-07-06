"""EDIT ME — the starting point for building your own simulation.

This file is meant to be opened in VS Code and changed. It builds the built-in
"falling block" scene, but every piece is a small, labelled function so you can
swap in your own CAD geometry, links, sensors and physics to simulate your own
model. Open the **Simulation Controls** panel in the RoboticsSim workbench to
play / pause / reset whatever you define here.

The scene has four editable parts, top to bottom:

    1. build_geometry(doc)  — make the FreeCAD shapes you want to see move.
    2. build_model(...)     — group shapes into links + add sensors.
    3. build_physics(robot) — decide what makes things move (gravity, motors…).
    4. build(...)           — wires 1-3 together into a Scene (rarely changed).

To simulate YOUR robot instead of a falling block:
    * Point build_geometry at your own Part shapes (or return your existing
      object Names and skip creating shapes).
    * In build_model, create one Link per rigid body and list the FreeCAD object
      Names that belong to it. Add joints if the bodies articulate.
    * In build_physics, attach the behaviour you want (see GravityBody, or drive
      joints with robot.command_motor / a control script).

Everything here is guarded so it also runs headless (no FreeCAD) for tests.
"""

from __future__ import annotations

from ..document_model import RobotModel
from ..kinematics import Transform
from ..link_model import Link
from ..robot_api import Robot
from ..scene import Scene
from ..sensor_model import Sensor
from ..simulation import GravityBody

# ---- Tweakables --------------------------------------------------------
# Change these numbers and re-open the panel to see the effect immediately.
BLOCK_START_Z = 500.0   # mm the block starts above the ground
BLOCK_SIZE = 100.0      # mm cube edge length
GROUND_HEIGHT = 0.0     # mm z of the floor the block lands on
DEFAULT_DT = 0.01       # s simulation time step (also the panel's default speed)
LOG_EVERY = 0.1         # s between telemetry lines printed to the terminal


def _get_freecad():
    try:
        import FreeCAD
        return FreeCAD
    except Exception:
        return None


# ---- 1. Geometry -------------------------------------------------------
def build_geometry(doc):
    """Create the FreeCAD shapes for this scene. Return the moving block object.

    Replace the box below with your own geometry, or return an object that
    already exists in ``doc``. Returns ``None`` when FreeCAD is unavailable
    (headless tests), in which case the model falls back to the name below.
    """
    fc = _get_freecad()
    if fc is None or doc is None:
        return None
    try:
        import Part  # noqa: F401  (registers the Part::Box object type)
    except Exception:
        return None

    # Reuse the shapes if they already exist (re-opening the panel must NOT spawn
    # a second block — that is what left a stale cube on the ground). getattr
    # returns the existing object, else we create it once.
    def _box(name):
        obj = getattr(doc, name, None)
        return obj if obj is not None else doc.addObject("Part::Box", name)

    # A big thin slab as the floor, its top face sitting at z = GROUND_HEIGHT.
    ground = _box("DemoGround")
    ground.Length, ground.Width, ground.Height = 2000.0, 2000.0, 10.0
    ground.Placement = fc.Placement(
        fc.Vector(-1000.0, -1000.0, GROUND_HEIGHT - 10.0), fc.Rotation()
    )

    # The cube that will fall. This is the object the link (below) will move.
    # Its placement is reset to the start height on every build.
    block = _box("DemoBlock")
    block.Length = block.Width = block.Height = BLOCK_SIZE
    block.Placement = fc.Placement(
        fc.Vector(-BLOCK_SIZE / 2.0, -BLOCK_SIZE / 2.0, BLOCK_START_Z), fc.Rotation()
    )
    doc.recompute()
    return block


# ---- 2. Model (links + sensors) ---------------------------------------
def build_model(block_object_name="DemoBlock") -> RobotModel:
    """Group geometry into links and add sensors.

    One link ("block") holds the falling cube. It carries a distance sensor that
    reports how far the block is above the ground. Add more Links/Joints/Sensors
    here to describe your own robot.
    """
    model = RobotModel("my_scene")
    model.add_link(
        Link(
            name="block",
            objects=[block_object_name],
            world_transform=Transform.from_translation((0.0, 0.0, BLOCK_START_Z)),
        )
    )
    model.add_sensor(
        Sensor(
            name="block_distance",
            sensor_type="distance",
            attached_link="block",
            max_range=5000.0,
            ground_height=GROUND_HEIGHT,
        )
    )
    return model


# ---- 3. Physics --------------------------------------------------------
def build_physics(robot: Robot, scene: Scene) -> None:
    """Attach whatever makes the scene move, and register how to reset it.

    Here: gravity pulls the "block" link down onto the floor. ``GravityBody``
    keeps its own velocity, so we register a reset hook that zeroes it — that is
    what lets the Reset button drop the block again from the top.

    For an articulated robot you might instead leave this empty and drive joints
    from the sliders / a control script, or call robot.command_motor(...).
    """
    gravity = GravityBody(
        robot, "block", ground_height=GROUND_HEIGHT
    ).attach()
    scene.add_reset(lambda: setattr(gravity, "velocity", 0.0))


# ---- Telemetry print ---------------------------------------------------
def _telemetry_printer():
    """A step hook that prints a telemetry line to the terminal ~every LOG_EVERY.

    This is the "print statement that runs inside the scene": it calls
    ``robot.log(...)`` each step (throttled), and whatever is subscribed to the
    robot's log — the terminal panel and any file logger — receives it live.
    Edit the text here to report whatever your own sim cares about.
    """
    state = {"bucket": -1}

    def _print(scene):
        robot = scene.robot
        bucket = int(robot.time / LOG_EVERY)
        if bucket == state["bucket"]:
            return  # throttle: at most one line per LOG_EVERY of sim time
        state["bucket"] = bucket
        height = robot.read_sensor("block_distance")
        robot.log("t=%.2f s  block_height=%.1f mm" % (robot.time, height))

    return _print


# ---- 4. Assemble (rarely edited) --------------------------------------
def build(doc=None, geometry_sync_factory=None) -> Scene:
    """Wire geometry + model + physics into a runnable :class:`Scene`.

    ``geometry_sync_factory(model)`` is supplied by the GUI so link motion drives
    the CAD objects; it is ``None`` in headless tests. You normally do not need
    to edit this function — change the three builders above instead.
    """
    block = build_geometry(doc)
    model = build_model(block.Name if block is not None else "DemoBlock")
    sync = geometry_sync_factory(model) if geometry_sync_factory else None
    robot = Robot(model, geometry_sync=sync)
    scene = Scene(robot, dt=DEFAULT_DT, name=model.name)
    build_physics(robot, scene)
    scene.add_step_hook(_telemetry_printer())  # live terminal + file logging
    scene.snapshot()  # re-capture "start" now that physics/links are in place
    return scene
