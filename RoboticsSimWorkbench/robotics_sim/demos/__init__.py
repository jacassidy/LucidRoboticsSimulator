"""Built-in demos.

The falling-block scene lives in :mod:`scene_template` — the single, editable
entry point users copy to build their own sim (driven by the Simulation Controls
panel). ``build`` returns a runnable :class:`~robotics_sim.scene.Scene`.
"""

from .scene_template import build, build_model

__all__ = ["build", "build_model"]
