"""Chat message bubble widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout

from ..styles import ThemeManager


class MessageBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self._text = text

        # Allow horizontal shrinking
        self.setMinimumWidth(0)
        self.setMaximumWidth(560)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Content frame
        self._content_frame = QFrame()
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(14, 10, 14, 10)
        content_layout.setSpacing(0)

        self._label = QLabel(text)
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._label.setMaximumWidth(500)
        self._label.setMinimumWidth(0)

        if is_user:
            layout.addStretch()
            layout.addWidget(self._content_frame)
        else:
            layout.addWidget(self._content_frame)
            layout.addStretch()

        content_layout.addWidget(self._label)
        self._apply_theme()

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        if self.is_user:
            bg = c.accent
            color = "#ffffff"
        else:
            bg = c.bg_secondary
            color = c.text_input
        self._content_frame.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: 16px; }}"
        )
        self._label.setStyleSheet(
            f"QLabel {{ color: {color}; font-size: 14px; border: none; }}"
        )
