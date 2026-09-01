"""Drag-and-drop file upload area."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class FileDropWidget(QFrame):
    """Drag-and-drop file upload area."""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setMaximumHeight(110)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #2a2a3e;
                border-radius: 12px;
                background-color: #12121e;
            }
            QFrame:hover {
                border-color: #4f46e5;
            }
        """)
        layout = QVBoxLayout(self)
        label = QLabel("📄  拖拽文件到此处  (PDF / Word / TXT / MD)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #555570; font-size: 13px; border: none;")
        layout.addWidget(label)

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
