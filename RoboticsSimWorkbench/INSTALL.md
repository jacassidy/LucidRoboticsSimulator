# Installing RoboticsSimWorkbench into FreeCAD

## Requirements

- **FreeCAD 0.21+** (1.0 recommended). Download: <https://www.freecad.org/>
- FreeCAD's bundled Python (3.8+) with PySide2/PySide6 — ships with FreeCAD.
- No third-party Python packages are required for Phase 1.

## Find your FreeCAD `Mod` directory

The workbench installs as an addon in FreeCAD's user `Mod` folder:

| OS       | Typical path |
| -------- | ------------ |
| macOS    | `~/Library/Application Support/FreeCAD/Mod/` |
| Linux    | `~/.local/share/FreeCAD/Mod/` (or `~/.FreeCAD/Mod/`) |
| Windows  | `%APPDATA%\FreeCAD\Mod\` |

You can confirm the exact path from FreeCAD's Python console:

```python
import FreeCAD
print(FreeCAD.getUserAppDataDir())   # Mod/ lives inside this directory
```

## Install (symlink — recommended for development)

Symlinking keeps the addon in sync with this git checkout.

**macOS / Linux:**
```bash
# from the repository root
ln -s "$(pwd)/RoboticsSimWorkbench" \
  "$HOME/Library/Application Support/FreeCAD/Mod/RoboticsSimWorkbench"   # macOS
# or, on Linux:
ln -s "$(pwd)/RoboticsSimWorkbench" \
  "$HOME/.local/share/FreeCAD/Mod/RoboticsSimWorkbench"
```

**Windows (PowerShell, as admin):**
```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\FreeCAD\Mod\RoboticsSimWorkbench" `
  -Target "C:\path\to\repo\RoboticsSimWorkbench"
```

## Install (copy)

If you prefer not to symlink, copy the whole `RoboticsSimWorkbench/` folder into
the `Mod/` directory. It must contain `Init.py` and `InitGui.py` at its top level:

```
Mod/RoboticsSimWorkbench/
  Init.py
  InitGui.py
  robotics_sim/...
```

## Activate

1. Restart FreeCAD.
2. Open the **workbench selector** (the dropdown in the toolbar).
3. Choose **RoboticsSim**.
4. The **Telemetry** dock appears on the left and the **Terminal** dock on the
   bottom; a **RoboticsSim** toolbar/menu appears with the commands.

## Verify

- **RoboticsSim → Simulation Controls** (opens automatically) should build a
  ground + block. Press **Play** to drop the block; heights log to the bottom
  terminal while telemetry updates on the left. **Reset** returns it to the top.
- The headless test suite should pass without FreeCAD:

  ```bash
  cd RoboticsSimWorkbench
  python3 -m unittest discover -s robotics_sim/tests -v
  ```

## Troubleshooting

- **Workbench not listed:** confirm `Init.py`/`InitGui.py` are at the top of the
  installed folder (not nested one level too deep). Check the Report View for a
  `RoboticsSim: failed to register workbench` message.
- **Icons missing:** harmless — commands still work; icons live in
  `resources/icons/`.
- **No PySide:** the panels need FreeCAD's Qt bindings (PySide2/6). They ship
  with FreeCAD; if you launched a stripped Python, use FreeCAD's own.
- **Import errors in the console:** run `import robotics_sim` in FreeCAD's Python
  console to see the traceback; the core imports without FreeCAD, so most issues
  are path-related.
