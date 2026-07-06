# Installing RoboticsSimWorkbench into FreeCAD

## Requirements

* **FreeCAD 0.21+** (1.0 recommended). Download: <https://www.freecad.org/>
* Python 3 (bundled with FreeCAD).

## Install as a FreeCAD Mod

FreeCAD discovers workbenches placed in its user `Mod` directory. Copy or symlink
the `RoboticsSimWorkbench/` folder there.

Find your FreeCAD user data directory from the Python console
(`View → Panels → Python console`):

```python
import FreeCAD; print(FreeCAD.getUserAppDataDir())
```

Then place the workbench under `<UserAppDataDir>/Mod/`:

| OS | Typical `Mod` path |
| --- | --- |
| macOS | `~/Library/Application Support/FreeCAD/Mod/` |
| Linux | `~/.local/share/FreeCAD/Mod/` |
| Windows | `%APPDATA%\FreeCAD\Mod\` |

### Symlink (recommended for development)

```bash
# macOS example — adjust to your clone + Mod path
ln -s "$(pwd)/RoboticsSimWorkbench" \
  "$HOME/Library/Application Support/FreeCAD/Mod/RoboticsSimWorkbench"
```

### Copy (simple install)

Copy the `RoboticsSimWorkbench/` directory into the `Mod/` directory above.

## Activate

1. Restart FreeCAD.
2. Open the workbench selector (top toolbar dropdown).
3. Choose **RoboticsSimWorkbench**.
4. Toolbars/menus for links, joints, sliders, scripts, exports, and the demo
   appear.

## Running tests

```bash
cd RoboticsSimWorkbench
python -m pytest robotics_sim/tests
```

> Tests that touch FreeCAD APIs must run inside FreeCAD's Python
> (`freecadcmd`); pure-logic tests run under system Python.

## Troubleshooting

* **Workbench not listed:** confirm the folder is directly under `Mod/` (not
  nested) and contains `InitGui.py`. Restart FreeCAD.
* **Import errors:** check the FreeCAD Report view / Python console for the
  traceback.
