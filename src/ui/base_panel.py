"""Themed base classes (U-P1).

Panels inheriting :class:`ThemedPanel` (or :class:`ThemedMainWindow`) are
registered with :class:`~src.ui.styles.ThemeManager` at construction time, so
theme switches refresh them automatically. Subclasses keep their own
``_apply_theme`` implementation; only the registration boilerplate moves here.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QWidget

from .styles import ThemeManager


class ThemedPanel(QWidget):
    """QWidget that registers itself with ThemeManager."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ThemeManager.register_panel(self)


class ThemedMainWindow(QMainWindow):
    """QMainWindow that registers itself with ThemeManager."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ThemeManager.register_panel(self)
