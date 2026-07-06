"""Joint sliders dock panel.

Lists all movable (revolute/prismatic) joints with a slider + numeric readout
each. Moving a slider sets the joint position on the shared Robot, which updates
the CAD scene live. Includes a "Reset to Home" button that zeroes all joints.

Sliders are integer widgets, so joint values are mapped onto a fixed integer
resolution across [lower, upper].
"""

from __future__ import annotations

from . import QT_AVAILABLE, QtWidgets, QtCore

SLIDER_STEPS = 1000


class JointSliderPanel(QtWidgets.QWidget if QT_AVAILABLE else object):
    def __init__(self, robot=None):
        if not QT_AVAILABLE:
            return
        super().__init__()
        self.setObjectName("RoboticsSimJointSliders")
        self.setWindowTitle("Joint Sliders")
        self._robot = None
        self._rows = {}  # joint_name -> (slider, label)
        self._outer = QtWidgets.QVBoxLayout(self)
        self._build_static()
        if robot is not None:
            self.bind(robot)

    def _build_static(self):
        reset = QtWidgets.QPushButton("Reset to Home (all zero)")
        reset.clicked.connect(self._reset)
        self._outer.addWidget(reset)
        self._form_host = QtWidgets.QWidget()
        self._form = QtWidgets.QFormLayout(self._form_host)
        self._outer.addWidget(self._form_host)
        self._outer.addStretch(1)

    def bind(self, robot):
        self._robot = robot
        self.rebuild()

    def rebuild(self):
        if not QT_AVAILABLE or self._robot is None:
            return
        # Clear existing rows.
        while self._form.rowCount():
            self._form.removeRow(0)
        self._rows.clear()

        for joint in self._robot.model.movable_joints():
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(SLIDER_STEPS)
            value_label = QtWidgets.QLabel("0.000")
            slider.setValue(self._to_slider(joint, joint.position))
            value_label.setText("%.3f" % joint.position)

            def make_cb(jname):
                return lambda v: self._on_slider(jname, v)

            slider.valueChanged.connect(make_cb(joint.name))
            container = QtWidgets.QWidget()
            hl = QtWidgets.QHBoxLayout(container)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.addWidget(slider)
            hl.addWidget(value_label)
            self._form.addRow("%s (%s)" % (joint.name, joint.type), container)
            self._rows[joint.name] = (slider, value_label)

    def _to_slider(self, joint, value):
        lo, hi = joint.lower_limit, joint.upper_limit
        if hi <= lo:
            return 0
        frac = (value - lo) / (hi - lo)
        return int(max(0, min(SLIDER_STEPS, round(frac * SLIDER_STEPS))))

    def _from_slider(self, joint, slider_val):
        lo, hi = joint.lower_limit, joint.upper_limit
        return lo + (slider_val / float(SLIDER_STEPS)) * (hi - lo)

    def _on_slider(self, joint_name, slider_val):
        if self._robot is None:
            return
        joint = self._robot.model.joints.get(joint_name)
        if joint is None:
            return
        value = self._from_slider(joint, slider_val)
        self._robot.set_joint_position(joint_name, value)
        _, label = self._rows[joint_name]
        label.setText("%.3f" % self._robot.get_joint_position(joint_name))

    def _reset(self):
        if self._robot is None:
            return
        self._robot.reset()
        for name, (slider, label) in self._rows.items():
            joint = self._robot.model.joints[name]
            slider.blockSignals(True)
            slider.setValue(self._to_slider(joint, 0.0))
            slider.blockSignals(False)
            label.setText("0.000")


_PANEL = None


def get_panel(robot=None):
    global _PANEL
    if _PANEL is None:
        _PANEL = JointSliderPanel(robot)
    elif robot is not None:
        _PANEL.bind(robot)
    return _PANEL
