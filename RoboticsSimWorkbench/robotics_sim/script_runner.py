"""Safe-ish execution of user control scripts.

Runs a code string with ``robot`` (and a ``log`` shortcut) injected, captures
stdout/print output, and reports exceptions as text instead of crashing FreeCAD.
Not a security sandbox — v1 assumes the user runs their own scripts.
"""

from __future__ import annotations

import io
import traceback
from contextlib import redirect_stdout


def run_script(code: str, robot, log=None) -> bool:
    """Execute `code` with `robot` in scope. Returns True on success.

    All printed output and any traceback are routed to `log` (a callback taking
    a string) and also mirrored onto the robot's log buffer if present.
    """
    def emit(text):
        for line in str(text).rstrip("\n").splitlines() or [""]:
            if log:
                try:
                    log(line)
                    continue
                except Exception:
                    pass
            print(line)

    namespace = {
        "robot": robot,
        "log": (robot.log if robot is not None else print),
        "__name__": "__control_script__",
    }
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(compile(code, "<control_script>", "exec"), namespace)
        out = buffer.getvalue()
        if out:
            emit(out)
        emit("[script] finished OK")
        return True
    except Exception:
        out = buffer.getvalue()
        if out:
            emit(out)
        emit("[script] ERROR:")
        emit(traceback.format_exc())
        return False
