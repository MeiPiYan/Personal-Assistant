"""Streaming text widget for AI responses."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextEdit

from ..styles import ThemeManager


class StreamingTextWidget(QTextEdit):
    """Displays streaming AI response token by token."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setFrameShape(QTextEdit.NoFrame)
        self.setPlaceholderText("AI 正在思考...")
        self._apply_theme()

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c.bg_tertiary};
                color: {c.text_input};
                border-top: 1px solid {c.border};
                padding: 12px 20px;
                font-size: 14px;
            }}
        """)

    def append_text(self, token: str) -> None:
        self.moveCursor(self.textCursor().End)
        self.insertPlainText(token)

    def clear(self) -> None:
        super().clear()
