"""Drag-and-drop file upload area."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from ..styles import ThemeManager


class FileDropWidget(QFrame):
    """Drag-and-drop file upload area."""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setMaximumHeight(110)

        layout = QVBoxLayout(self)
        self._label = QLabel("📄  拖拽文件到此处  (PDF / Word / TXT / MD)")
        self._label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label)

        self._apply_theme()

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {c.border};
                border-radius: 12px;
                background-color: {c.bg_darker};
            }}
            QFrame:hover {{
                border-color: {c.accent};
            }}
        """)
        self._label.setStyleSheet(f"color: {c.text_disabled}; font-size: 13px; border: none;")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                files.append(path)
        if files:
            self.files_dropped.emit(files)
