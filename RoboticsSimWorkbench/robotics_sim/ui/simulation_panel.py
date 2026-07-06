"""Simulation Controls dock panel: play / pause, speed (time step), reset.

Drives a :class:`~robotics_sim.scene.Scene` with a ``QTimer`` so stepping is
non-blocking — the 3D view keeps repainting and Play/Pause stays responsive
(a blocking ``for`` loop would freeze the GUI until the sim finished).

Each timer tick advances the scene by its ``dt`` and calls an optional
``redraw`` callback (the command wires this to recompute the doc + refresh the
FreeCAD view). The speed slider sets ``scene.dt`` directly.
"""

from __future__ import annotations

from . import QT_AVAILABLE, QtWidgets, QtCore

# Slider maps integer 1..DT_MAX_MS onto dt = value / 1000 seconds.
DT_MIN_MS = 1      # 0.001 s per step (slow, fine)
DT_MAX_MS = 100    # 0.100 s per step (fast, coarse)
TICK_INTERVAL_MS = 20  # wall-clock ~50 fps; dt controls sim speed, not this


class SimulationPanel(QtWidgets.QWidget if QT_AVAILABLE else object):
    def __init__(self, scene=None):
        if not QT_AVAILABLE:
            return
        super().__init__()
        self.setObjectName("RoboticsSimSimulation")
        self.setWindowTitle("Simulation Controls")
        self._scene = None
        self._redraw = None
        self._logfile = None            # open file handle when logging to disk
        self._log_listener = None       # the callback registered on robot.log
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._build_ui()
        if scene is not None:
            self.bind(scene)

    # ---- construction --------------------------------------------------
    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)

        # Play/Pause + Reset row.
        buttons = QtWidgets.QHBoxLayout()
        self._play_btn = QtWidgets.QPushButton("Play")
        self._play_btn.clicked.connect(self.toggle)
        self._reset_btn = QtWidgets.QPushButton("Reset")
        self._reset_btn.clicked.connect(self.reset)
        buttons.addWidget(self._play_btn)
        buttons.addWidget(self._reset_btn)
        outer.addLayout(buttons)

        # Speed (time step) slider.
        self._speed_label = QtWidgets.QLabel("Speed (dt): 0.010 s/step")
        outer.addWidget(self._speed_label)
        self._speed = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._speed.setMinimum(DT_MIN_MS)
        self._speed.setMaximum(DT_MAX_MS)
        self._speed.setValue(10)  # 0.010 s
        self._speed.valueChanged.connect(self._on_speed)
        outer.addWidget(self._speed)

        # Log-to-file toggle.
        self._logfile_btn = QtWidgets.QPushButton("Log to File…")
        self._logfile_btn.clicked.connect(self._toggle_logfile)
        outer.addWidget(self._logfile_btn)

        # Sim time readout + status.
        self._time_label = QtWidgets.QLabel("t = 0.000 s")
        outer.addWidget(self._time_label)
        self._status = QtWidgets.QLabel("No scene loaded.")
        self._status.setWordWrap(True)
        outer.addWidget(self._status)
        outer.addStretch(1)
        self._set_enabled(False)

    def _set_enabled(self, on):
        for w in (self._play_btn, self._reset_btn, self._speed, self._logfile_btn):
            w.setEnabled(on)

    # ---- binding -------------------------------------------------------
    def bind(self, scene, redraw=None):
        """Attach a Scene (and optional redraw callback) to these controls."""
        if not QT_AVAILABLE:
            return
        self.pause()
        self._scene = scene
        self._redraw = redraw
        if scene is not None:
            self._speed.blockSignals(True)
            self._speed.setValue(int(round(scene.dt * 1000)))
            self._speed.blockSignals(False)
            self._on_speed(self._speed.value())
            self._set_enabled(True)
            self._status.setText("Scene %r ready. Press Play." % scene.name)
            # If a log file is open, follow the new scene's robot.
            if self._logfile is not None and self._log_listener is not None:
                if self._log_listener not in scene.robot.log_listeners:
                    scene.robot.log_listeners.append(self._log_listener)
        self._update_time()

    # ---- controls ------------------------------------------------------
    def toggle(self):
        self.pause() if self._timer.isActive() else self.play()

    def play(self):
        if not QT_AVAILABLE or self._scene is None:
            return
        self._timer.start()
        self._play_btn.setText("Pause")
        self._status.setText("Running…")

    def pause(self):
        if not QT_AVAILABLE:
            return
        self._timer.stop()
        self._play_btn.setText("Play")

    def reset(self):
        if not QT_AVAILABLE or self._scene is None:
            return
        self.pause()
        self._scene.reset()
        self._redraw_view()
        self._update_time()
        self._status.setText("Reset to start.")

    # ---- timer tick ----------------------------------------------------
    def _on_tick(self):
        if self._scene is None:
            self.pause()
            return
        try:
            self._scene.step()
        except Exception as exc:
            self.pause()
            self._status.setText("Step error: %s" % exc)
            return
        self._redraw_view()
        self._update_time()

    def _redraw_view(self):
        if self._redraw is not None:
            try:
                self._redraw()
            except Exception:
                pass

    def _update_time(self):
        t = self._scene.robot.time if self._scene is not None else 0.0
        self._time_label.setText("t = %.3f s" % t)

    def _on_speed(self, value):
        dt = value / 1000.0
        if self._scene is not None:
            self._scene.dt = dt
        self._speed_label.setText("Speed (dt): %.3f s/step" % dt)

    # ---- log to file ---------------------------------------------------
    def _toggle_logfile(self):
        if self._logfile is not None:
            self._close_logfile()
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Log simulation to file", "sim_log.txt", "Text (*.txt *.log)"
        )
        if not path:
            return
        try:
            self._logfile = open(path, "a")
        except Exception as exc:
            self._status.setText("Could not open log file: %s" % exc)
            return

        def listener(value):
            fh = self._logfile
            if fh is None:
                return
            if isinstance(value, dict):
                text = ", ".join("%s=%s" % (k, v) for k, v in value.items())
            else:
                text = str(value)
            try:
                fh.write(text + "\n")
                fh.flush()
            except Exception:
                pass

        self._log_listener = listener
        if self._scene is not None:
            self._scene.robot.log_listeners.append(listener)
        self._logfile_btn.setText("Stop Logging (%s)" % path.split("/")[-1])
        self._status.setText("Logging to %s" % path)

    def _close_logfile(self):
        if self._scene is not None and self._log_listener is not None:
            try:
                self._scene.robot.log_listeners.remove(self._log_listener)
            except ValueError:
                pass
        if self._logfile is not None:
            try:
                self._logfile.close()
            except Exception:
                pass
        self._logfile = None
        self._log_listener = None
        self._logfile_btn.setText("Log to File…")
        self._status.setText("Stopped file logging.")


_PANEL = None


def get_panel(scene=None):
    global _PANEL
    if _PANEL is None:
        _PANEL = SimulationPanel(scene)
    elif scene is not None:
        _PANEL.bind(scene)
    return _PANEL
