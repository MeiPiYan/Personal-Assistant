from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout


class MessageBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)

        content = QLabel(text)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content.setMaximumWidth(480)
        content.setMinimumWidth(60)

        if is_user:
            bg = "#4f46e5"
            color = "white"
            align = Qt.AlignRight
            layout.addStretch()
            layout.addWidget(content)
        else:
            bg = "#374151"
            color = "#e5e7eb"
            align = Qt.AlignLeft
            layout.addWidget(content)
            layout.addStretch()

        content.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 14px;
                line-height: 1.4;
            }}
        """)
