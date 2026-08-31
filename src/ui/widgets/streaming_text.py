from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextEdit


class StreamingTextWidget(QTextEdit):
    """Displays streaming AI response token by token."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self.setPlaceholderText("AI 正在思考...")
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)

    def append_text(self, token: str) -> None:
        self.moveCursor(self.textCursor().End)
        self.insertPlainText(token)

    def clear(self) -> None:
        super().clear()
