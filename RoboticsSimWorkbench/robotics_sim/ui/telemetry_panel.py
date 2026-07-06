"""Left-side telemetry dock panel.

Tree view of live robot state: simulation time, link poses, joint positions,
sensor readings. Subscribes to a Robot's telemetry listeners and refreshes on
slider moves, script runs, and demo steps.
"""

from __future__ import annotations

from . import QT_AVAILABLE, QtWidgets

_PANEL = None


def _fmt(x):
    try:
        return "%.4f" % float(x)
    except Exception:
        return str(x)


class TelemetryPanel(QtWidgets.QWidget if QT_AVAILABLE else object):
    def __init__(self):
        if not QT_AVAILABLE:
            return
        super().__init__()
        self.setObjectName("RoboticsSimTelemetry")
        self.setWindowTitle("RoboticsSim Telemetry")
        self._robot = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.time_label = QtWidgets.QLabel("t = 0.000 s")
        layout.addWidget(self.time_label)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Item", "Value"])
        self.tree.setColumnWidth(0, 160)
        layout.addWidget(self.tree)

    def bind(self, robot):
        """Attach to a Robot; refresh on every telemetry notification."""
        if not QT_AVAILABLE or robot is None:
            return
        self._robot = robot
        if self.refresh not in robot.telemetry_listeners:
            robot.telemetry_listeners.append(lambda r: self.refresh())
        self.refresh()

    def refresh(self):
        if not QT_AVAILABLE or self._robot is None:
            return
        snap = self._robot.telemetry_snapshot()
        self.time_label.setText("t = %.3f s" % snap["time"])
        self.tree.clear()

        links = QtWidgets.QTreeWidgetItem(self.tree, ["Links", ""])
        for name, pos in snap["links"].items():
            QtWidgets.QTreeWidgetItem(
                links, [name, "xyz=(%s, %s, %s)" % (_fmt(pos[0]), _fmt(pos[1]), _fmt(pos[2]))]
            )

        joints = QtWidgets.QTreeWidgetItem(self.tree, ["Joints", ""])
        for name, val in snap["joints"].items():
            QtWidgets.QTreeWidgetItem(joints, [name, _fmt(val)])

        sensors = QtWidgets.QTreeWidgetItem(self.tree, ["Sensors", ""])
        for name, val in snap["sensors"].items():
            QtWidgets.QTreeWidgetItem(sensors, [name, _fmt(val)])

        self.tree.expandAll()


def get_panel():
    global _PANEL
    if _PANEL is None:
        _PANEL = TelemetryPanel()
    return _PANEL
