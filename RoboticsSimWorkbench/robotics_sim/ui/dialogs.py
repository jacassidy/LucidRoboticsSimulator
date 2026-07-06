"""Modal dialogs: create joint, edit joint, run script.

Kept intentionally small. Each dialog returns plain values; commands.py wires
them to the document model. All Qt usage guarded via the ui shim.
"""

from __future__ import annotations

from . import QT_AVAILABLE, QtWidgets

from ..joint_model import JOINT_TYPES, REVOLUTE


def error_box(title, message):
    if QT_AVAILABLE:
        QtWidgets.QMessageBox.critical(None, title, str(message))
    else:
        print("[ERROR] %s: %s" % (title, message))


def info_box(title, message):
    if QT_AVAILABLE:
        QtWidgets.QMessageBox.information(None, title, str(message))
    else:
        print("[INFO] %s: %s" % (title, message))


def ask_text(title, label, default=""):
    if not QT_AVAILABLE:
        return default, True
    text, ok = QtWidgets.QInputDialog.getText(None, title, label, text=default)
    return text, ok


class JointDialog(QtWidgets.QDialog if QT_AVAILABLE else object):
    """Create/edit a joint. Returns a dict of field values via `values()`."""

    def __init__(self, link_names, axis_picker=None, existing=None):
        if not QT_AVAILABLE:
            return
        super().__init__()
        self.setWindowTitle("Edit Joint" if existing else "Create Joint")
        self._axis_picker = axis_picker
        form = QtWidgets.QFormLayout(self)

        self.name = QtWidgets.QLineEdit(existing.name if existing else "joint")
        form.addRow("Name", self.name)

        self.type = QtWidgets.QComboBox()
        self.type.addItems(list(JOINT_TYPES))
        if existing:
            self.type.setCurrentText(existing.type)
        else:
            self.type.setCurrentText(REVOLUTE)
        form.addRow("Type", self.type)

        self.parent = QtWidgets.QComboBox()
        self.parent.addItems(link_names)
        self.child = QtWidgets.QComboBox()
        self.child.addItems(link_names)
        if existing:
            self.parent.setCurrentText(existing.parent_link)
            self.child.setCurrentText(existing.child_link)
        elif len(link_names) > 1:
            self.child.setCurrentIndex(1)
        form.addRow("Parent link", self.parent)
        form.addRow("Child link", self.child)

        ax = existing.axis if existing else (0.0, 0.0, 1.0)
        self.ax_x = QtWidgets.QDoubleSpinBox(); self.ax_x.setRange(-1e6, 1e6); self.ax_x.setDecimals(4); self.ax_x.setValue(ax[0])
        self.ax_y = QtWidgets.QDoubleSpinBox(); self.ax_y.setRange(-1e6, 1e6); self.ax_y.setDecimals(4); self.ax_y.setValue(ax[1])
        self.ax_z = QtWidgets.QDoubleSpinBox(); self.ax_z.setRange(-1e6, 1e6); self.ax_z.setDecimals(4); self.ax_z.setValue(ax[2])
        axis_row = QtWidgets.QHBoxLayout()
        for w in (self.ax_x, self.ax_y, self.ax_z):
            axis_row.addWidget(w)
        pick = QtWidgets.QPushButton("Pick from selection")
        pick.clicked.connect(self._pick_axis)
        axis_row.addWidget(pick)
        axis_host = QtWidgets.QWidget(); axis_host.setLayout(axis_row)
        form.addRow("Axis", axis_host)

        self.lower = QtWidgets.QDoubleSpinBox(); self.lower.setRange(-1e6, 1e6); self.lower.setDecimals(4)
        self.upper = QtWidgets.QDoubleSpinBox(); self.upper.setRange(-1e6, 1e6); self.upper.setDecimals(4)
        self.lower.setValue(existing.lower_limit if existing else -3.1416)
        self.upper.setValue(existing.upper_limit if existing else 3.1416)
        form.addRow("Lower limit", self.lower)
        form.addRow("Upper limit", self.upper)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _pick_axis(self):
        if self._axis_picker is None:
            return
        axis = self._axis_picker()
        if axis is None:
            error_box("Pick Axis", "Select a straight edge (or 2 vertices) first.")
            return
        self.ax_x.setValue(axis[0]); self.ax_y.setValue(axis[1]); self.ax_z.setValue(axis[2])

    def values(self):
        return {
            "name": self.name.text().strip(),
            "type": self.type.currentText(),
            "parent_link": self.parent.currentText(),
            "child_link": self.child.currentText(),
            "axis": (self.ax_x.value(), self.ax_y.value(), self.ax_z.value()),
            "lower_limit": self.lower.value(),
            "upper_limit": self.upper.value(),
        }


class ScriptDialog(QtWidgets.QDialog if QT_AVAILABLE else object):
    """Editor for a control script + Load File / Run buttons.

    ``on_run(code_text)`` is invoked with the editor contents.
    """

    def __init__(self, on_run, initial_code=""):
        if not QT_AVAILABLE:
            return
        super().__init__()
        self.setWindowTitle("Run Control Script")
        self.resize(640, 480)
        self._on_run = on_run
        layout = QtWidgets.QVBoxLayout(self)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setPlainText(initial_code)
        try:
            font = self.editor.font(); font.setFamily("Menlo, Consolas, monospace")
            self.editor.setFont(font)
        except Exception:
            pass
        layout.addWidget(self.editor)

        bar = QtWidgets.QHBoxLayout()
        load = QtWidgets.QPushButton("Load File…")
        load.clicked.connect(self._load)
        run = QtWidgets.QPushButton("Run")
        run.clicked.connect(self._run)
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(self.accept)
        bar.addWidget(load); bar.addStretch(1); bar.addWidget(run); bar.addWidget(close)
        layout.addLayout(bar)

    def _load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open script", "", "Python (*.py)")
        if path:
            with open(path) as fh:
                self.editor.setPlainText(fh.read())

    def _run(self):
        self._on_run(self.editor.toPlainText())
