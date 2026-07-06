# CLAUDE.md — LucidRoboticsSim (repo root)

Guidance for AI agents working in this repository. Keep it accurate as the code
evolves.

## What this is

Lucid Robotics Simulator — Phase 1 is a **FreeCAD workbench**
(`RoboticsSimWorkbench/`) that turns FreeCAD CAD geometry into a programmable
articulated robot: links, joints, sensors, telemetry, a Python scripting API,
simple physics, and URDF/MJCF export. Long-term goal: "the VS Code of simulated
robotics." Phase 2 adds live MuJoCo / Chrono / Bullet bridges.

Full spec: `docs/BUILD_SPEC.md`. Workbench details: `RoboticsSimWorkbench/README.md`.

## Golden architecture rule

**The core has no FreeCAD dependency.** These modules must import and run under
plain CPython so they stay unit-testable headless:

- `robotics_sim/kinematics.py`, `link_model.py`, `joint_model.py`,
  `sensor_model.py`, `document_model.py` (data half), `robot_api.py`,
  `simulation.py`, `scene.py`, `script_runner.py`, `exporters/*`.

All FreeCAD / Qt access is isolated and **guarded** (try/except import) in:

- `freecad_bridge.py`, `commands.py`, `workbench.py`, `ui/*`, and the FreeCAD
  scene-building half of `demos/scene_template.py`.

Never `import FreeCAD` at module top level in a core module. If you need it, add
it behind a helper in `freecad_bridge.py`.

## Conventions

- **Units:** FreeCAD documents default to **millimetres**; gravity default is
  `-9810 mm/s²`. Exporters scale to metres via
  `RobotModel.export_settings['length_scale']` (default `0.001`).
- **References by name:** links store FreeCAD object **Names** (strings), not live
  handles, so metadata survives save/reload.
- **Persistence:** the whole model serializes to JSON stored on a hidden
  `App::FeaturePython` object (`RoboticsSimData`) inside the document. Round-trip
  goes through `RobotModel.to_dict/from_dict`.
- **Transforms:** use the pure-Python `kinematics.Transform` (rotation 3x3 +
  translation). Convert to/from `FreeCAD.Placement` only in `freecad_bridge`.
- **Shared runtime:** one `Robot` per document, cached in
  `freecad_bridge._RUNTIMES`; sliders, telemetry, scripts, and the demo all share
  it so changes propagate.

## Testing

```bash
cd RoboticsSimWorkbench
python3 -m unittest discover -s robotics_sim/tests -v   # 23 tests, no FreeCAD
```

Add a headless test for any new core logic. GUI/FreeCAD paths are exercised
manually in FreeCAD (see INSTALL.md verify steps).

## When adding features

- New joint type → extend `joint_model.JOINT_TYPES`, `kinematics.joint_transform`,
  and both exporters.
- New sensor type → add a `type` to `sensor_model` + a `compute` branch (or a
  registry); expose via `robot.read_sensor`.
- New command → add a `_Command` subclass in `commands.py`, append to
  `ALL_COMMANDS`, add an icon in `resources/icons/`.
- New Phase 2 bridge → new module under `robotics_sim/` that consumes a
  `RobotModel` (reuse the exporters) or drives `Robot` via a `physics_hook`.

## Don't

- Don't overbuild Phase 2 now (no live MuJoCo/Chrono/Bullet yet — just export).
- Don't add heavy runtime deps; Phase 1 uses only the stdlib + FreeCAD's bundled
  Python/Qt.
- Don't put physics into FreeCAD beyond the simple demo integrator.
