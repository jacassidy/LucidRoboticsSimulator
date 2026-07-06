# Simulation Controls + editable Scene

## Why This Exists
Users need to play/pause/reset the sim and adjust speed from the GUI, and need a
clear code entry point to build a sim for their own model (not just the built-in
demo).

## Current Decision
- `robotics_sim/scene.py` — core, FreeCAD-free `Scene` = Robot + `dt` + snapshot/
  reset. `snapshot()` captures link world-transforms + joint positions; `reset()`
  restores them, runs registered reset hooks (for hidden physics state like a
  GravityBody's velocity), and rewinds `robot.time`. Unit-testable headless.
- `robotics_sim/demos/scene_template.py` — THE user-editable file. Four labelled
  builders: `build_geometry(doc)`, `build_model(...)`, `build_physics(robot,scene)`,
  `build(doc, geometry_sync_factory)`. Users swap geometry/links/physics here to
  simulate their own model. Guarded so it runs headless.
- `robotics_sim/ui/simulation_panel.py` — QTimer-driven dock (Play/Pause, speed
  slider = `scene.dt`, Reset, time readout). Non-blocking: each tick calls
  `scene.step()` + a `redraw` callback. Singleton `get_panel()`, QT-guarded.
- `commands.SimulationControls` (`RoboticsSim_SimControls`, icon
  `sim_controls.svg`) builds the scene via `scene_template.build`, passing
  `geometry_sync_factory=lambda m: bridge.GeometrySync(doc, m)`, stores robot in
  `bridge._RUNTIMES`, binds the panel. `IsActive()` returns True (can create its
  own doc). Registered in `ALL_COMMANDS`.

## How To Extend
- New physics/behaviour: edit `build_physics`; register a reset hook via
  `scene.add_reset(...)` for any state not in link transforms / joint positions.
- Speed slider range: `DT_MIN_MS`/`DT_MAX_MS` in simulation_panel.py (dt = ms/1000).

## Live output wiring (important)
- Robot steps do NOT reach the terminal on their own. `commands._tee_terminal`
  appends a `robot.log_listeners` callback that writes to `terminal_panel.log`
  (once per robot, guarded by `robot._terminal_teed`). Without it the terminal
  only shows one-time command lines.
- `scene_template._telemetry_printer()` is the per-step "print" (registered via
  `scene.add_step_hook`). It calls `robot.log(...)` throttled to `LOG_EVERY`
  (0.1 s sim time). Everything subscribed to `robot.log` — terminal + optional
  file logger — receives it live.
- File logging: the panel's "Log to File…" button opens a file and appends a
  `robot.log_listeners` callback; re-attaches to the new robot on `bind`.
- `Scene.on_step` hooks run inside `Scene.step()` (after `robot.step`).

## One-scene-per-doc (no duplicate blocks)
- `commands._SCENES[doc.Name]` caches the Scene; `_open_simulation(rebuild,
  create_doc)` reuses it. Toolbar command = rebuild+create_doc True; workbench
  `Activated` = both False (open by default, no empty doc, no dup geometry).
- `scene_template.build_geometry` reuses existing `DemoGround`/`DemoBlock` via
  `getattr(doc, name, None)` instead of always `addObject` — re-opening the panel
  used to spawn a second block that sat orphaned on the ground.

## Gotchas
- Old `RunDemo` steps in a blocking for-loop — the new panel uses a QTimer so the
  UI stays live. Don't reintroduce a blocking loop for interactive control.
- `Scene` calls `robot._motors.clear()` and internal `_update_sensors`/
  `_notify_telemetry` on reset — mirrors `Robot.reset()` but ALSO restores the
  free-falling link transform (which `Robot.reset()` does not).
- Rebuild GeometrySync against the *new* model (the factory does this) or the
  block won't move.

## Single code path (RunDemo retired)
- The old `RunDemo` command + `demos/falling_block_demo.py` + `run_demo.svg` are
  DELETED. All block-building goes through `demos/scene_template.build` /
  `build_model`. `demos/__init__` exports `build`, `build_model`.
  `demo_control_script._run_standalone` uses `scene_template.build_model`.
- `commands.ALL_COMMANDS` is now 7 (no RunDemo). Removed dead `_qt_app`/`_sleep`
  helpers and `import time` from commands.py.
- If you need a headless scripted run, use `scene_template.build(...)` + step the
  Scene, or `Robot(build_model())` + `GravityBody(...).attach()`.

## Last Updated
2026-07-06
