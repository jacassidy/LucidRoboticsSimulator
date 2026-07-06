# Lucid Robotics Simulator

**Open-source robotics learning environment, built as a FreeCAD workbench.**

Lucid Robotics Simulator helps students learn robotics by turning existing
FreeCAD CAD geometry into a *programmable, articulated robot model* — with
joints, sensors, telemetry, scripting, and physics — all inside FreeCAD.

The long-term vision is the "VS Code of simulated robotics": a development
environment where the simulator/CAD scene is central, telemetry sits on the
left, a terminal/scripting panel sits on the bottom, and users write control
code that drives articulated CAD models using simulated sensors, motors, and
physics.

> **Status:** Scaffolding only. This repository is set up and ready for
> implementation. Source files under `RoboticsSimWorkbench/` are stubs that
> raise `NotImplementedError`. See [the build spec](#build-spec) below.

---

## Why a FreeCAD workbench first?

Phase 1 deliberately does **not** build a standalone CAD application. Instead it
ships as a FreeCAD **workbench** so we can reuse FreeCAD's mature CAD kernel,
document model, and 3D viewport, and focus on proving the core robotics
workflow: geometry → links → joints → sensors → scripting → export.

Later phases add live physics bridges (MuJoCo, Project Chrono, Bullet) and,
if the workbench becomes limiting, a standalone app shell.

---

## What it will do (Phase 1)

Once implemented, users will be able to:

1. Select parts in FreeCAD and group them into named rigid **links**.
2. Create **joints** (revolute / prismatic / fixed) between links.
3. Pick joint axes from geometry, set limits.
4. Move joints with **sliders** and see the CAD scene update live.
5. Save all articulation metadata **inside the FreeCAD document**.
6. Run **Python control scripts** against named joints, links, and sensors.
7. Export the model to **URDF** and **MJCF**.
8. Run a built-in **falling-block demo** where a block falls under gravity and a
   simulated distance sensor reports its height above the ground.

### UI layout

* **Center:** FreeCAD 3D viewport / simulator scene
* **Left:** telemetry panel (link poses, joint positions, sensor readings, sim time)
* **Bottom:** terminal / script-output panel
* **Toolbars / menus:** create links, joints, sliders, run scripts, exports, demo

---

## Repository layout

```text
LucidRoboticsSim/
  RoboticsSimWorkbench/        FreeCAD workbench (Phase 1 target)
    Init.py                    Non-GUI init hook
    InitGui.py                 GUI init hook (registers the workbench)
    robotics_sim/
      workbench.py             Workbench class, toolbars, menus
      commands.py              FreeCAD command classes
      document_model.py        Document-level metadata (JSON persistence)
      link_model.py            Link data model
      joint_model.py           Joint data model
      sensor_model.py          Sensor abstraction + DistanceSensor
      robot_api.py             Scripting API for control scripts
      kinematics.py            Kinematic transform engine
      simulation.py            Simple sim loop + demo physics + motor model
      exporters/
        urdf_exporter.py       URDF export
        mjcf_exporter.py       MJCF (MuJoCo) export
      ui/
        telemetry_panel.py     Left dock
        terminal_panel.py      Bottom dock
        joint_slider_panel.py  Joint sliders
        dialogs.py             Create/edit dialogs
      demos/
        falling_block_demo.py  Gravity + distance-sensor demo
        demo_control_script.py Example control script
      tests/                   Unit tests
    README.md                  Workbench-specific readme
    INSTALL.md                 Install into FreeCAD
  third_party/                 Phase 2 sim engines (git submodules)
    mujoco/                    MuJoCo   (MJCF target + live bridge)
    bullet3/                   Bullet   (realtime interaction)
    chrono/                    Project Chrono (multibody dynamics)
  docs/                        Project + agent-facing docs
  LICENSE                      AGPLv3-or-later
  TRADEMARKS.md                Name / logo / branding policy
  CONTRIBUTING.md              Contribution terms (AGPLv3 + patent grant)
  THIRD_PARTY.md               Vendored dependencies + their licenses
```

---

## Getting the code

```bash
git clone https://github.com/<org>/LucidRoboticsSim.git
cd LucidRoboticsSim
# Phase 2 sim engines are optional and large; only fetch if you need them:
git submodule update --init --depth 1 third_party/mujoco
```

Installing the workbench into FreeCAD is documented in
[`RoboticsSimWorkbench/INSTALL.md`](RoboticsSimWorkbench/INSTALL.md).

---

## Current limitations (Phase 1 scope)

* Kinematics only — no full rigid-body dynamics inside FreeCAD.
* Demo physics is a simple integrator (`v += g·dt; h += v·dt`).
* Mass / inertia use placeholder defaults.
* One sensor type: `DistanceSensor` (to ground plane).
* URDF/MJCF exports are structurally valid, not geometry-perfect.

---

## Phase 2 roadmap

* Live **MuJoCo** bridge (robotics / control)
* Live **Project Chrono** bridge (mechanical / multibody dynamics)
* **Bullet** realtime interaction mode
* Better collision geometry generation
* Better mass / inertia computation
* Richer motor models
* Camera, IMU, and contact sensors
* Plugin system for internally designed components
* Richer terminal
* Project-level robotics workspace
* Standalone app shell if the FreeCAD workbench becomes limiting

---

## Build spec

The full Phase 1 build specification an implementing agent should follow lives in
[`docs/BUILD_SPEC.md`](docs/BUILD_SPEC.md).

---

## License

Licensed under **AGPLv3-or-later** — see [`LICENSE`](LICENSE). Anyone may use,
study, modify, and redistribute the software; modified **and network-hosted**
versions must also provide corresponding source under the same license.

The project **name, logo, and branding are not** covered by that grant — see
[`TRADEMARKS.md`](TRADEMARKS.md). Forks may redistribute the code, but may not
present themselves as the official project or use the official trademarks
without permission.

Contributing? See [`CONTRIBUTING.md`](CONTRIBUTING.md).
