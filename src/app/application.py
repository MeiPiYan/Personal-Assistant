from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
)

from .config import Config
from src.ui.icons import tray_icon


class AppSignals(QObject):
    """Global application signals."""
    show_main_window = Signal()
    hide_main_window = Signal()
    quit_app = Signal()


class Application:
    def __init__(self):
        self.config = Config()
        self.config.load()

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("AI Assistant")

        self.signals = AppSignals()
        self._tray: QSystemTrayIcon | None = None
        self._main_window = None
        self._floating_ball = None

    def setup_tray(self) -> None:
        self._tray = QSystemTrayIcon(self.app)
        # Use custom tray icon from the icon module
        self._tray.setIcon(tray_icon())
        self._tray.setToolTip("AI Assistant")

        menu = QMenu()
        show_action = QAction("显示主窗口", menu)
        show_action.triggered.connect(lambda: self.signals.show_main_window.emit())
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.signals.show_main_window.emit()

    def _quit(self) -> None:
        self.signals.quit_app.emit()
        self.app.quit()

    def set_main_window(self, window) -> None:
        self._main_window = window

    def set_floating_ball(self, ball) -> None:
        self._floating_ball = ball

    def run(self) -> int:
        self.setup_tray()
        return self.app.exec()
