"""Falling-block + distance-sensor demo.

Proves the end-to-end workflow: geometry in FreeCAD, a link, a sensor, a gravity
sim loop, live telemetry, and terminal logs.

Two entry points:
- :func:`build_demo_model` builds the RobotModel (+ optional FreeCAD geometry).
- :func:`run_falling_block_demo` steps the sim, logging height + sensor reading.

The model half is FreeCAD-independent so the physics can be tested headless.
"""

from __future__ import annotations

from ..document_model import RobotModel
from ..kinematics import Transform
from ..link_model import Link
from ..robot_api import Robot
from ..sensor_model import Sensor
from ..simulation import GravityBody

BLOCK_START_Z = 500.0   # mm above ground
BLOCK_SIZE = 100.0      # mm cube
GROUND_HEIGHT = 0.0


def _get_freecad():
    try:
        import FreeCAD
        return FreeCAD
    except Exception:
        return None


def build_scene(doc):
    """Create ground plane + block in a FreeCAD document. Returns block object.

    No-op-safe: returns None if FreeCAD/Part is unavailable.
    """
    fc = _get_freecad()
    if fc is None or doc is None:
        return None
    try:
        import Part
    except Exception:
        return None

    # Ground: thin large box centered at origin, top at z=0.
    ground = doc.addObject("Part::Box", "DemoGround")
    ground.Length = 2000.0
    ground.Width = 2000.0
    ground.Height = 10.0
    ground.Placement = fc.Placement(fc.Vector(-1000.0, -1000.0, -10.0), fc.Rotation())

    block = doc.addObject("Part::Box", "DemoBlock")
    block.Length = BLOCK_SIZE
    block.Width = BLOCK_SIZE
    block.Height = BLOCK_SIZE
    block.Placement = fc.Placement(
        fc.Vector(-BLOCK_SIZE / 2.0, -BLOCK_SIZE / 2.0, BLOCK_START_Z), fc.Rotation()
    )
    doc.recompute()
    return block


def build_demo_model(block_object_name="DemoBlock") -> RobotModel:
    """Build the demo RobotModel: one link (the block) + a distance sensor."""
    model = RobotModel("falling_block_demo")
    link = Link(
        name="block",
        objects=[block_object_name],
        world_transform=Transform.from_translation((0.0, 0.0, BLOCK_START_Z)),
    )
    model.add_link(link)
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


def run_falling_block_demo(steps=200, dt=0.01, doc=None, geometry_sync=None,
                           log=None, robot=None, on_step=None):
    """Run the gravity demo. Returns the Robot and a list of log rows.

    `log` is a callback(str). If a FreeCAD doc is given and no robot supplied,
    the scene is built and geometry synced live.

    `on_step` is an optional callback(robot, row) invoked after each sim step.
    The GUI uses it to redraw the 3D view and pace the loop to wall-clock time so
    the block is seen falling in real time (otherwise all steps run instantly and
    only the final frame is visible).
    """
    fc = _get_freecad()
    block_obj = None
    if doc is not None and fc is not None:
        block_obj = build_scene(doc)

    if robot is None:
        model = build_demo_model(block_obj.Name if block_obj is not None else "DemoBlock")
        robot = Robot(model, geometry_sync=geometry_sync)

    gravity = GravityBody(robot, "block", ground_height=GROUND_HEIGHT).attach()

    rows = []
    _emit(log, "Falling block demo: start (steps=%d, dt=%.3f)" % (steps, dt))
    for _ in range(steps):
        robot.step(dt)
        height = robot.read_sensor("block_distance")
        row = {"time": round(robot.time, 4), "block_height": round(height, 3)}
        rows.append(row)
        _emit(log, "t=%.2f  height=%.2f mm" % (robot.time, height))
        if on_step is not None:
            try:
                on_step(robot, row)
            except Exception:
                pass
        if height <= 0.0 and gravity.velocity == 0.0:
            _emit(log, "Block landed at t=%.2f s" % robot.time)
            break
    _emit(log, "Falling block demo: done")
    return robot, rows


def _emit(log, text):
    if log:
        try:
            log(text)
            return
        except Exception:
            pass
    print(text)
