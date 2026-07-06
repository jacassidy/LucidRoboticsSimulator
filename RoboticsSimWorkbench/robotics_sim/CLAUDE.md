# CLAUDE.md — robotics_sim package

Module-level map + rules. See repo-root `CLAUDE.md` for the golden architecture
rule (core is FreeCAD-free; glue is guarded).

## Import layers (respect this direction)

```
core (no FreeCAD):
  kinematics  <- link_model, joint_model, sensor_model
  {link,joint,sensor}_model <- document_model
  document_model, kinematics <- robot_api
  robot_api <- simulation, script_runner
  document_model, kinematics <- exporters/{urdf,mjcf}
  * <- demos/falling_block_demo (model half)

glue (guarded FreeCAD/Qt):
  core <- freecad_bridge
  core + ui + demos + freecad_bridge <- commands
  commands + ui <- workbench
  ui/__init__ (Qt shim) <- ui/{telemetry,terminal,joint_slider}_panel, dialogs
```

A core module importing a glue module is a bug.

## File responsibilities

| File | Role |
| ---- | ---- |
| `kinematics.py` | `Transform`, axis-angle, `joint_transform`, `forward_kinematics`, `matrix_to_rpy` |
| `link_model.py` | `Link` container (objects by name, mass/inertia placeholders, world transform) |
| `joint_model.py` | `Joint` container, `JOINT_TYPES`, `MOVABLE_TYPES`, `clamp()` |
| `sensor_model.py` | `Sensor` container + `compute()` (distance-to-ground) |
| `document_model.py` | `RobotModel` (validation, JSON) + FreeCAD doc persistence |
| `robot_api.py` | `Robot` runtime: FK cache, motors, sensors, `step`, logging, telemetry snapshot |
| `simulation.py` | `GravityBody` physics hook + `run_headless` |
| `script_runner.py` | `run_script(code, robot, log)` with stdout capture + error reporting |
| `freecad_bridge.py` | Placement<->Transform, `GeometrySync`, `axis_from_selection`, per-doc `Robot` cache |
| `commands.py` | 8 GUI commands + `register_commands()` + `_show_dock` |
| `workbench.py` | `RoboticsSimWorkbench(Gui.Workbench)` |
| `exporters/` | `export_urdf/write_urdf`, `export_mjcf/write_mjcf` |
| `ui/` | Qt shim + 3 dock panels + dialogs; all no-op when `QT_AVAILABLE` is False |
| `demos/` | falling-block demo + example control snippet |

## Runtime flow

1. A command calls `freecad_bridge.get_robot(doc)` → loads/creates the shared
   `Robot` for that document.
2. Sliders / scripts / demo mutate the `Robot` (joint positions, physics hooks).
3. `Robot.refresh_kinematics()` runs `forward_kinematics` and calls
   `geometry_sync(link, transform)` to move CAD objects.
4. `Robot._notify_telemetry()` refreshes the telemetry panel; `robot.log()` and
   `terminal_panel.log()` feed the terminal.
5. `freecad_bridge.save_robot(doc)` writes JSON back into the document.

## Gotchas

- Sliders are integer widgets mapped onto `[lower, upper]` with `SLIDER_STEPS`.
- Distance sensor returns `-1.0` when beyond `max_range`, else clamped `>= 0`.
- `GeometrySync` captures each object's base placement at construction; rebuild it
  (`GeometrySync(doc, model)`) after adding links or the new link won't move.
- Prismatic limits are lengths (scaled by exporters); revolute limits are radians.
