"""Streaming text widget for AI responses."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextEdit


class StreamingTextWidget(QTextEdit):
    """Displays streaming AI response token by token."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setFrameShape(QTextEdit.NoFrame)
        self.setPlaceholderText("AI 正在思考...")
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #d0d0e0;
                border-top: 1px solid #2a2a3e;
                padding: 12px 20px;
                font-size: 14px;
            }
        """)

    def append_text(self, token: str) -> None:
        self.moveCursor(self.textCursor().End)
        self.insertPlainText(token)

    def clear(self) -> None:
        super().clear()
