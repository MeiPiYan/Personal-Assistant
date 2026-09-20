"""Bubble node graphics item (plan §4/§8).

Levels and colors: 0=green (current), -1=red (previous), 1=blue (related).
Interaction: hover (with debounce) or click emits ``nodeActivated``;
double-click emits ``nodeDoubleClicked``.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem

LEVEL_COLORS = {
    0: QColor("#34A853"),   # green — current
    -1: QColor("#EA4335"),  # red — previous
    1: QColor("#4285F4"),   # blue — related
}
LEVEL_RADII = {0: 46.0, -1: 36.0, 1: 30.0}


class GraphNodeItem(QGraphicsEllipseItem):
    """A knowledge bubble; ``level`` drives color and size."""

    nodeActivated = Signal(int)          # hover-debounced or clicked selection
    nodeDoubleClicked = Signal(int)      # enter/NavigationRequest

    def __init__(self, node_id: int, label: str, level: int,
                 hover_debounce_ms: int = 250, parent=None):
        r = LEVEL_RADII.get(level, 30.0)
        super().__init__(-r, -r, 2 * r, 2 * r, parent)
        self.node_id = node_id
        self.level = level
        self.radius = r

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(max(0, int(hover_debounce_ms)))
        self._hover_timer.timeout.connect(lambda: self.nodeActivated.emit(self.node_id))

        color = LEVEL_COLORS.get(level, QColor("#888888"))
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(130), 2))
        self.setZValue(2)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)

        self._text = QGraphicsSimpleTextItem(label, self)
        font = QFont()
        font.setPointSizeF(10.5 if level == 0 else 9.5)
        self._text.setFont(font)
        metrics = QFontMetricsF(font)
        max_w = 2 * r * 0.82
        label_fit = label
        while metrics.horizontalAdvance(label_fit) > max_w and len(label_fit) > 2:
            label_fit = label_fit[:-2] + "…"
        self._text.setText(label_fit)
        tw = self._text.boundingRect().width()
        th = self._text.boundingRect().height()
        self._text.setPos(-tw / 2, -th / 2)
        self._text.setBrush(QBrush(QColor("#FFFFFF")))
        self._text.setZValue(3)

    def set_level(self, level: int) -> None:
        self.level = level
        r = LEVEL_RADII.get(level, 30.0)
        self.radius = r
        self.setRect(-r, -r, 2 * r, 2 * r)
        color = LEVEL_COLORS.get(level, QColor("#888888"))
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(130), 2))

    # ---- events ------------------------------------------------------ #
    def hoverEnterEvent(self, event) -> None:
        self._hover_timer.start()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hover_timer.stop()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self._hover_timer.stop()
        if event.button() == Qt.LeftButton:
            self.nodeActivated.emit(self.node_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.nodeDoubleClicked.emit(self.node_id)
        super().mouseDoubleClickEvent(event)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addEllipse(self.rect())
        return path
