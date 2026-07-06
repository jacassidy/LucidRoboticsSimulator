# RoboticsSimWorkbench

A **FreeCAD workbench** that turns existing FreeCAD CAD geometry into a
programmable, articulated robot model — with links, joints, sensors, live
telemetry, a scripting API, simple physics, and URDF/MJCF export.

This is **Phase 1** of the Lucid Robotics Simulator ("the VS Code of simulated
robotics"). See the repository root [`README.md`](../README.md) for the project
vision and [`docs/BUILD_SPEC.md`](../docs/BUILD_SPEC.md) for the full spec.

---

## What it does

- **Links** — group one or more selected FreeCAD objects into a named rigid body.
- **Joints** — connect two links with a `revolute`, `prismatic`, or `fixed`
  joint; pick the axis from geometry or type it in; set limits.
- **Joint sliders** — a dock panel that moves joints live and updates the CAD
  scene, with a one-click reset to home.
- **Scripting API** — drive named joints/links/sensors from Python
  (`robot.set_joint_position(...)`, `robot.read_sensor(...)`, `robot.step(dt)`…).
- **Telemetry panel** (left) — live tree of link poses, joint values, sensor
  readings, and simulation time.
- **Terminal panel** (bottom) — script output, logs, errors, export/demo status.
- **Distance sensor** — measures height above a ground plane.
- **Falling-block demo** — a block falls under gravity while a distance sensor
  reports its height; telemetry + terminal update live.
- **Export** — write structurally valid **URDF** and **MJCF** (MuJoCo) files.
- **Persistence** — all robot metadata is stored as JSON inside the FreeCAD
  document, so it saves and reloads with your `.FCStd` file.

## Why a FreeCAD workbench first?

Phase 1 reuses FreeCAD's mature CAD kernel, document model, and 3D viewport
instead of building a standalone app. That lets us prove the core workflow —
*geometry → links → joints → sensors → scripting → export* — fast. Later phases
add live physics bridges (MuJoCo, Chrono, Bullet) and, if needed, a standalone
shell.

## Install

See [`INSTALL.md`](INSTALL.md). In short: symlink or copy this
`RoboticsSimWorkbench/` folder into your FreeCAD `Mod/` directory and restart
FreeCAD, then pick **RoboticsSim** from the workbench selector.

## Usage

### 1. Create a link
1. In FreeCAD, select one or more objects in the tree or 3D view.
2. **RoboticsSim → Create Link**, enter a name.
   The objects become one rigid body; membership is stored in the document.

### 2. Create a joint
1. Make at least two links.
2. **RoboticsSim → Create Joint**. Choose type, parent link, child link.
3. Set the **axis**: type `x y z`, or select a straight edge (or two vertices)
   and click **Pick from selection**.
4. Set lower/upper limits. **OK**.

### 3. Move joints with sliders
**RoboticsSim → Joint Sliders** opens the slider panel (right dock). Drag a
slider — the child link moves live in the 3D view. **Reset to Home** zeroes all
joints.

### 4. Run a control script
**RoboticsSim → Run Script** opens an editor pre-filled with the example script.
Edit or **Load File…**, then **Run**. Output appears in the bottom terminal.
The injected `robot` object exposes:

```python
robot.get_joint("name")
robot.set_joint_position("name", value)
robot.get_joint_position("name")
robot.get_link_pose("link_name")          # returns a Transform
robot.step(dt)                            # advance sim + motors + sensors
robot.read_sensor("sensor_name")
robot.log(value_or_dict)
robot.command_motor("name", target_position=v)   # or target_velocity=v
robot.time                                # current sim time (s)
```

### 5. Run the falling-block demo
**RoboticsSim → Run Demo** builds a ground plane + a block, treats the block as a
link, attaches a `block_distance` sensor, and drops the block under gravity.
Watch the telemetry (left) and terminal (bottom) update. After it runs you can
open **Run Script** and run the example to keep driving the same block.

### 6. Export URDF / MJCF
**RoboticsSim → Export URDF** or **Export MJCF**, choose a path. Example outputs
live in [`../resources/examples/`](../resources/examples/).

## Architecture (for contributors)

```
robotics_sim/
  kinematics.py       # pure-Python Transform + forward kinematics (no FreeCAD)
  link_model.py       # Link data container
  joint_model.py      # Joint data container + types
  sensor_model.py     # Sensor container + DistanceSensor compute
  document_model.py   # RobotModel + JSON <-> FreeCAD document persistence
  robot_api.py        # Robot: runtime state, motors, sensors, stepping, logging
  simulation.py       # simple gravity integrator (falling-block physics)
  script_runner.py    # safe-ish exec of user scripts with `robot` injected
  freecad_bridge.py   # Transform<->Placement, geometry sync, axis pick, runtime
  commands.py         # FreeCAD GUI command classes
  workbench.py        # Gui.Workbench definition
  exporters/          # urdf_exporter.py, mjcf_exporter.py
  ui/                 # telemetry_panel, terminal_panel, joint_slider_panel, dialogs
  demos/              # falling_block_demo, demo_control_script
  tests/              # headless unittest suite (no FreeCAD required)
```

**Design rule:** the *core* (kinematics, models, exporters, robot_api,
simulation) has **no FreeCAD dependency** so it runs and tests headless. All
FreeCAD/Qt access is isolated in `freecad_bridge`, `commands`, `workbench`, and
`ui/`, and is guarded so imports never hard-fail.

## Running the tests

```bash
cd RoboticsSimWorkbench
python3 -m unittest discover -s robotics_sim/tests -v
```

No FreeCAD needed — 23 tests cover kinematics, the document model, the sim, and
both exporters.

## Current limitations (v1)

- Kinematics only; no real rigid-body dynamics inside FreeCAD (demo physics is a
  simple gravity integrator).
- Mass/inertia are placeholder defaults; exporters emit placeholder inertials.
- Visual/collision geometry is exported as a mesh *reference* (`meshes/<obj>.stl`)
  or a placeholder box — meshes are **not** auto-exported yet.
- Joint origins are computed from stored link world translations (translation
  only); complex nested rotations may need manual origin tuning.
- The script runner is **not** a security sandbox — run only scripts you trust.
- One sensor type (`distance`).

## Phase 2 roadmap

- Live **MuJoCo** bridge (control/robotics)
- Live **Project Chrono** bridge (multibody dynamics)
- **Bullet** realtime interaction mode
- Better collision geometry generation + automatic mesh export
- Real mass/inertia computation from FreeCAD solids
- Richer motor models
- Camera / IMU / contact sensors
- Plugin system for internally designed components
- Richer terminal (input, history)
- Project-level robotics workspace
- Standalone app shell if the workbench becomes limiting
