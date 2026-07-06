"""UI package: dock panels (telemetry, terminal, joint sliders) and dialogs.

Provides a small Qt shim so panels import the right PySide binding across
FreeCAD versions (PySide2 / PySide6 / PySide). All Qt usage is guarded; if no
binding is available (headless), ``QT_AVAILABLE`` is False and panels are no-ops.
"""

QT_AVAILABLE = True
try:
    from PySide2 import QtWidgets, QtCore, QtGui  # noqa: F401
except Exception:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui  # noqa: F401
    except Exception:
        try:
            from PySide import QtGui as QtWidgets  # very old FreeCAD
            from PySide import QtCore
            from PySide import QtGui
        except Exception:
            QtWidgets = QtCore = QtGui = None
            QT_AVAILABLE = False

__all__ = ["QtWidgets", "QtCore", "QtGui", "QT_AVAILABLE"]
