# Contributing to Lucid Robotics Simulator

Thanks for your interest in contributing! This document explains the legal terms
your contributions are made under, and the basics of how to contribute.

## Licensing of contributions

Lucid Robotics Simulator is licensed under **AGPLv3-or-later**. By submitting a
contribution (code, documentation, assets, or any other material) to this
project, **you agree that:**

1. **License grant.** Your contribution is provided under the
   **GNU Affero General Public License, version 3 or (at your option) any later
   version** (AGPLv3-or-later), the same license as the project.

2. **You have the right to contribute it.** The contribution is your original
   work, or you otherwise have the right to submit it under AGPLv3-or-later, and
   its submission does not violate any third party's rights.

3. **Patent grant.** You grant to the project and to recipients of the software
   a perpetual, worldwide, non-exclusive, royalty-free, irrevocable patent
   license to make, have made, use, offer to sell, sell, import, and otherwise
   transfer your contribution, where such license applies only to those patent
   claims licensable by you that are necessarily infringed by your contribution
   alone or by combination of your contribution with the project. (This mirrors
   the patent provisions of AGPLv3 / GPLv3.)

4. **No obligation to use.** The project is under no obligation to accept or use
   any contribution.

### Sign-off (Developer Certificate of Origin)

Please sign off your commits to certify the above. Add a `Signed-off-by` line
using `git commit -s`:

```text
Signed-off-by: Your Name <your.email@example.com>
```

This indicates your agreement to the
[Developer Certificate of Origin](https://developercertificate.org/) and to the
terms in this document.

## Trademarks

Contributing code does **not** grant you any rights to the project's name, logo,
or branding. See [`TRADEMARKS.md`](TRADEMARKS.md).

## How to contribute

1. Open an issue to discuss significant changes before starting.
2. Fork the repository and create a feature branch.
3. Follow the code organization in [`README.md`](README.md) and the build spec
   in [`docs/BUILD_SPEC.md`](docs/BUILD_SPEC.md).
4. Include tests where practical (`RoboticsSimWorkbench/robotics_sim/tests/`).
5. Sign off your commits (`git commit -s`) and open a pull request.

## Third-party code

Do not paste code from incompatible-licensed sources. Vendored dependencies live
under `third_party/` as git submodules and keep their own licenses — see
[`THIRD_PARTY.md`](THIRD_PARTY.md).
