from __future__ import annotations

import asyncio
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import QWidget


class FloatingBall(QWidget):
    """48px draggable always-on-top floating overlay."""

    clicked = Signal()
    right_clicked = Signal(QPoint)

    def __init__(self, size: int = 48, opacity: float = 0.85, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(size, size)
        self.setWindowOpacity(opacity)

        self._size = size
        self._drag_pos = QPoint()
        self._is_dragging = False
        self._pulse_angle = 0.0

        # Pulse animation timer for visual feedback
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_timer.start(50)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = QPoint(self._size // 2, self._size // 2)
        radius = self._size // 2 - 2

        # Outer glow pulse
        import math
        pulse = (math.sin(self._pulse_angle) + 1) / 2
        glow_color = QColor(99, 102, 241, int(40 + 30 * pulse))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(center, radius + 2, radius + 2)

        # Main circle
        painter.setBrush(QBrush(QColor(99, 102, 241, 220)))
        painter.setPen(QPen(QColor(129, 140, 248, 180), 1.5))
        painter.drawEllipse(center, radius, radius)

        # "AI" text
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", int(self._size * 0.3), QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "AI")

    def _pulse_tick(self) -> None:
        import math
        self._pulse_angle += 0.1
        if self._pulse_angle > 2 * math.pi:
            self._pulse_angle -= 2 * math.pi
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            self._is_dragging = False
            event.accept()
        elif event.button() == Qt.RightButton:
            self.right_clicked.emit(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            if (new_pos - self.pos()).manhattanLength() > 5:
                self._is_dragging = True
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and not self._is_dragging:
            self.clicked.emit()
        event.accept()
