# Third-Party Dependencies

Lucid Robotics Simulator is **AGPLv3-or-later**. The components below are
external projects it integrates with. They are **not** covered by this project's
license — each keeps its own license, listed below.

## Runtime host (not vendored)

| Project | Role | License | Notes |
| --- | --- | --- | --- |
| [FreeCAD](https://github.com/FreeCAD/FreeCAD) | Host CAD application the workbench runs inside | LGPL-2.1-or-later | Installed by the user; not bundled in this repo. See `RoboticsSimWorkbench/INSTALL.md`. |

## Vendored submodules (`third_party/`)

Added as **git submodules**, fetched only when you run
`git submodule update --init <path>`. They support Phase 2 physics bridges and
serve as reference targets for the URDF/MJCF exporters.

| Submodule | Path | Role | License |
| --- | --- | --- | --- |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | `third_party/mujoco` | MJCF export target + Phase 2 live bridge | Apache-2.0 |
| [Bullet3](https://github.com/bulletphysics/bullet3) | `third_party/bullet3` | Phase 2 realtime interaction | zlib |
| [Project Chrono](https://github.com/projectchrono/chrono) | `third_party/chrono` | Phase 2 multibody dynamics | BSD-3-Clause |

### License compatibility note

MuJoCo (Apache-2.0), Bullet (zlib), and Chrono (BSD-3-Clause) are permissive and
compatible with combination under AGPLv3-or-later. FreeCAD is LGPL; the workbench
loads into FreeCAD as a Python addon at runtime rather than statically linking.
Keep each submodule's `LICENSE` intact and do not copy their source into this
project's AGPL tree.

## Fetching submodules

```bash
# all of them (large):
git submodule update --init --recursive --depth 1
# or just one:
git submodule update --init --depth 1 third_party/mujoco
```
