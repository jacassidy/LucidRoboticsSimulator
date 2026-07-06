# Phase 1 Build Specification

This is the specification an implementing agent should follow to build the first
working version of Lucid Robotics Simulator. The repository scaffolding
(structure, licensing, docs, submodules) is already in place; source modules
under `RoboticsSimWorkbench/` are stubs to be implemented.

## Role

Expert robotics simulation software architect and senior Python/C++ developer.
Build the first working version as a **FreeCAD Workbench** (not a standalone CAD
app).

## Product goal

A FreeCAD workbench that lets users turn existing FreeCAD CAD geometry into a
programmable articulated robot model. Users can:

1. Select parts in FreeCAD.
2. Group selected parts into named rigid links.
3. Create joints between links.
4. Pick joint axes from geometry.
5. Set joint limits.
6. Move joints with sliders.
7. Save all articulation metadata inside the FreeCAD document.
8. Run Python control scripts against named joints and links.
9. Export the model to URDF and MJCF.
10. Run a demo where a block falls under gravity and a simulated distance sensor
    reports its height above the ground.

## Architecture direction

* **Phase 1** = this FreeCAD workbench.
* **Phase 2** = bridges/export/live integration to MuJoCo (control), Project
  Chrono (multibody dynamics), Bullet (lightweight realtime). Submodules for
  these are already vendored under `third_party/`.
* Design Phase 1 so Phase 2 slots in cleanly. Do **not** overbuild Phase 2 now.

## Required Phase 1 features

1. **Workbench** `RoboticsSimWorkbench` registering toolbar/menu commands:
   Create Link, Create Joint, Edit Joint, Joint Sliders, Run Script, Export URDF,
   Export MJCF, Run Demo. Python implementation preferred.
2. **Link system** — named rigid body from ≥1 selected FreeCAD objects; stores
   name, object refs, optional mass/inertia (placeholder defaults ok), visual +
   collision refs, world transform, parent/child joint refs. Renameable.
   Membership stored in a document-level metadata object; original geometry
   preserved.
3. **Joint system** — types: revolute, prismatic, fixed. Connects parent/child
   link. Stores name, type, parent/child, origin transform, axis, lower/upper
   limit, current position/velocity, optional effort limit. Axis pickable from
   geometry or entered manually. Moving a joint updates the child link transform
   visually. Simple kinematic transforms are acceptable.
4. **Joint sliders** — panel listing revolute/prismatic joints; shows values,
   clamps to limits, updates scene live, resets all to home.
5. **Scripting API** (`robot`): `get_joint`, `set_joint_position`,
   `get_joint_position`, `get_link_pose`, `step(dt)`, `read_sensor`, `log`, plus
   `command_motor(joint, target_position=…/target_velocity=…)`. Script runner
   loads from file/text box, executes with the API, captures output to the
   terminal panel, reports exceptions clearly, and never crashes FreeCAD.
6. **Telemetry panel** (left dock) — link poses, joint positions, sensor
   readings, script logs, sim time. Updates on slider move, script run, demo
   step. Tree/table view is fine.
7. **Terminal panel** (bottom dock) — script output, telemetry logs, errors,
   demo + export status.
8. **Sensor system** — abstraction attachable to links. Implement
   `DistanceSensor` (distance from link/object to ground plane) with name, type,
   attached link, local pose, max range, current reading. Readable via
   `robot.read_sensor(name)`.
9. **Gravity demo** — build/load a scene, add a block above a ground plane, treat
   as a link, add a distance sensor to the ground, run a simple gravity loop
   (`v += g·dt; h += v·dt; clamp at ground`), log height + sensor reading, update
   telemetry + terminal. Ship an example control script that steps and logs.
10. **Metadata persistence** — JSON in a FreeCAD document object/property:
    links, joints, sensors, limits, current positions, export settings.
    Reconstruct the robot model on document open.
11. **URDF export** — robot name, links, joints, types, axes, limits, visual refs
    where practical, placeholder inertials. Structurally valid.
12. **MJCF export** — bodies/links, joints, axes, ranges, simple geoms/mesh refs,
    placeholder inertials. Good enough as a MuJoCo starting point.
13. **Code organization** — the module layout already scaffolded under
    `RoboticsSimWorkbench/`.
14. **UI layout** — center 3D viewport, left telemetry, bottom terminal,
    toolbars/menus. Use FreeCAD dock widgets; do not fight FreeCAD's UI.
15. **Error handling** (graceful, surfaced in terminal / dialogs): no document
    open, no selection, joint-before-links, invalid axis, invalid limits,
    duplicate link/joint names, script errors, export errors.

## Deliverables

Working workbench source; README, install, usage, demo docs (already scaffolded —
extend as implemented); example control script; basic tests; URDF + MJCF export
examples.

## Implementation priority

1. Workbench loads in FreeCAD.
2. Metadata model (links, joints, sensors).
3. Link creation from selection.
4. Joint creation/editing.
5. Sliders update geometry.
6. Scripting API.
7. Telemetry + terminal panels.
8. Falling-block demo.
9. URDF export.
10. MJCF export.
11. Tests + docs.

## Definition of done

A user can install the workbench, activate it, load a CAD model, make a part a
link, add a joint and move it with a slider, run a script that reads/controls the
model, run the falling-block demo, watch telemetry + terminal update, and export
to URDF and MJCF.

## Constraints

Keep v1 simple and working. No standalone CAD app. No over-engineered physics —
simple kinematics + simple demo physics. Keep the architecture clean enough for
MuJoCo/Chrono/Bullet later. **The demo matters more than completeness.** Prefer
readable, maintainable code; comment non-obvious architecture; make assumptions
explicit in the README.
