"""Example control script for the RoboticsSim script panel.

Paste this into the Run Script dialog (or Load File it) AFTER opening the
Simulation Controls panel so the ``block_distance`` sensor exists. The script
runner injects a ``robot`` object into the namespace.

You can also run this file directly in a headless Python to see the API in
action (it builds the scene model itself in that case).
"""

# --- The snippet the workbench runs (robot is injected) --------------------
CONTROL_SNIPPET = """
for i in range(100):
    robot.step(0.01)
    height = robot.read_sensor("block_distance")
    robot.log({
        "time": robot.time,
        "block_height": height,
    })
"""


def _run_standalone():
    """Headless demo of the same API, for `python demo_control_script.py`."""
    from robotics_sim.demos.scene_template import build_model
    from robotics_sim.robot_api import Robot
    from robotics_sim.simulation import GravityBody

    robot = Robot(build_model())
    GravityBody(robot, "block").attach()
    for _ in range(100):
        robot.step(0.01)
        height = robot.read_sensor("block_distance")
        robot.log({"time": round(robot.time, 3), "block_height": round(height, 2)})
    print("Final height:", robot.read_sensor("block_distance"))


if __name__ == "__main__":
    import os
    import sys

    # Allow running from inside the package dir.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    _run_standalone()
