"""Chat message bubble widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout

from ..styles import ThemeManager


class MessageBubble(QFrame):
    """A single chat message bubble.

    Assistant bubbles may carry ``sources`` — a list of retrieved knowledge
    chunks used to ground the answer. When present, a compact "引用来源" block
    is rendered under the message text.
    """

    def __init__(
        self,
        text: str,
        is_user: bool = True,
        sources: list[dict] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.is_user = is_user
        self._text = text
        self._sources = sources or []

        # Allow horizontal shrinking
        self.setMinimumWidth(0)
        self.setMaximumWidth(560)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Content frame
        self._content_frame = QFrame()
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(14, 10, 14, 10)
        content_layout.setSpacing(6)

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

        # Optional source citation block (assistant messages only)
        self._sources_label = None
        if not is_user and self._sources:
            content_layout.addWidget(self._build_sources_label())

        self._apply_theme()

    def _build_sources_label(self) -> QLabel:
        lines = ["📎 引用来源"]
        for i, src in enumerate(self._sources, start=1):
            title = (src.get("title") or src.get("source_path") or "").strip()
            snippet = (src.get("content") or "").strip().replace("\n", " ")
            if len(snippet) > 60:
                snippet = snippet[:60] + "…"
            if title:
                lines.append(f"[{i}] {title}：{snippet}")
            else:
                lines.append(f"[{i}] {snippet}")
        label = QLabel("\n".join(lines))
        label.setWordWrap(True)
        label.setMaximumWidth(500)
        label.setMinimumWidth(0)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._sources_label = label
        return label

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
        if self._sources_label is not None:
            self._sources_label.setStyleSheet(
                f"QLabel {{ color: {c.text_secondary}; font-size: 11px; border: none; }}"
            )
