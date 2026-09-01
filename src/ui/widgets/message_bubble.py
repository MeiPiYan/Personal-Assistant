"""Chat message bubble widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QFont


class MessageBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Bubble content
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(14, 10, 14, 10)
        content_layout.setSpacing(0)

        content = QLabel(text)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content.setMaximumWidth(520)
        content.setMinimumWidth(40)

        if is_user:
            bg = "#4f46e5"
            color = "#ffffff"
            layout.addStretch()
            layout.addWidget(content_frame)
            content_frame.setStyleSheet(
                f"QFrame {{ background-color: {bg}; border-radius: 16px; }}"
            )
        else:
            bg = "#1e1e32"
            color = "#d0d0e0"
            layout.addWidget(content_frame)
            layout.addStretch()
            content_frame.setStyleSheet(
                f"QFrame {{ background-color: {bg}; border-radius: 16px; }}"
            )

        content.setStyleSheet(f"color: {color}; font-size: 14px; border: none;")
        content_layout.addWidget(content)
