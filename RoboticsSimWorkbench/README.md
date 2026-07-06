# RoboticsSimWorkbench

The FreeCAD workbench that powers Lucid Robotics Simulator (Phase 1).

> **Status:** scaffolding. Source modules are stubs that raise
> `NotImplementedError`. This document describes intended behavior for the
> implementing agent and future users.

## What it does

Turns existing FreeCAD CAD geometry into a programmable, articulated robot model:
named links, joints with limits, sliders, a Python scripting API, simulated
sensors, telemetry + terminal panels, a falling-block demo, and URDF/MJCF export.

## Install

See [`INSTALL.md`](INSTALL.md).

## Commands (toolbar / menu)

| Command | Purpose |
| --- | --- |
| Create Link | Group selected FreeCAD objects into a named rigid link |
| Create Joint | Connect two links with a revolute/prismatic/fixed joint |
| Edit Joint | Change axis, limits, origin |
| Joint Sliders | Open the slider panel to move movable joints live |
| Run Script | Load/run a Python control script against the robot API |
| Export URDF | Export the model to URDF |
| Export MJCF | Export the model to MJCF (MuJoCo) |
| Run Demo | Run the built-in falling-block gravity + distance-sensor demo |

## Scripting API (intended surface)

```python
robot.get_joint("joint_name")
robot.set_joint_position("joint_name", value)
robot.get_joint_position("joint_name")
robot.get_link_pose("link_name")
robot.step(dt)
robot.read_sensor("sensor_name")
robot.log(value_or_dict)
robot.command_motor("joint_name", target_position=value)
robot.command_motor("joint_name", target_velocity=value)
```

## Example control script

```python
for i in range(100):
    robot.step(0.01)
    height = robot.read_sensor("block_distance")
    robot.log({"time": robot.time, "block_height": height})
```

## Demo

Run **Run Demo**: a block is placed above a ground plane, treated as a link, with
a distance sensor to the ground. A simple gravity loop drops it; telemetry
(left) and terminal (bottom) update as it falls.

## Persistence

All robot metadata (links, joints, sensors, limits, current joint positions,
export settings) is stored as JSON inside the FreeCAD document, and reconstructed
on document open.

See the top-level [`README.md`](../README.md) for the full feature list,
limitations, and Phase 2 roadmap.
