"""Bottom terminal / script-output dock panel.

Shows script output, telemetry logs, errors, demo/export status. Not a full
shell in v1 — a read-only append-only text view with a clear button. A module
singleton lets any command write to it via :func:`log`.
"""

from __future__ import annotations

from . import QT_AVAILABLE, QtWidgets

_PANEL = None


class TerminalPanel(QtWidgets.QWidget if QT_AVAILABLE else object):
    def __init__(self):
        if not QT_AVAILABLE:
            return
        super().__init__()
        self.setObjectName("RoboticsSimTerminal")
        self.setWindowTitle("RoboticsSim Terminal")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("Terminal / Output"))
        bar.addStretch(1)
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        bar.addWidget(clear_btn)
        layout.addLayout(bar)

        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(5000)
        try:
            font = self.output.font()
            font.setFamily("Menlo, Consolas, monospace")
            self.output.setFont(font)
        except Exception:
            pass
        layout.addWidget(self.output)

    def append(self, text: str):
        if not QT_AVAILABLE:
            print(text)
            return
        for line in str(text).splitlines() or [""]:
            self.output.appendPlainText(line)

    def clear(self):
        if QT_AVAILABLE:
            self.output.clear()


def get_panel():
    global _PANEL
    if _PANEL is None:
        _PANEL = TerminalPanel()
    return _PANEL


def log(text: str):
    """Module-level convenience so any command can write to the terminal."""
    try:
        get_panel().append(text)
    except Exception:
        print(text)
