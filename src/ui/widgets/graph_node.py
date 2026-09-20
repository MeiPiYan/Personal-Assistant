"""Bubble node graphics item (plan §4/§8).

Levels and colors: 0=green (current), -1=red (previous), 1=blue (related).
Interaction: hover (with debounce) or click emits ``nodeActivated``;
double-click emits ``nodeDoubleClicked``.

Implementation note: inherits ``QGraphicsObject`` (QObject + QGraphicsItem)
so Qt signals and ``QTimer`` parenting work correctly — the previous
``QGraphicsEllipseItem`` base is not a QObject, which made the class crash at
construction time. The ellipse is drawn manually in ``paint`` because
``QGraphicsObject`` has no built-in shape rendering.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsSimpleTextItem

LEVEL_COLORS = {
    0: QColor("#34A853"),   # green — current
    -1: QColor("#EA4335"),  # red — previous
    1: QColor("#4285F4"),   # blue — related
}
LEVEL_RADII = {0: 46.0, -1: 36.0, 1: 30.0}

_PEN_WIDTH = 2.0


class GraphNodeItem(QGraphicsObject):
    """A knowledge bubble; ``level`` drives color and size."""

    nodeActivated = Signal(int)          # hover-debounced or clicked selection
    nodeDoubleClicked = Signal(int)      # enter/NavigationRequest

    def __init__(self, node_id: int, label: str, level: int,
                 hover_debounce_ms: int = 250, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.level = level
        self.radius = LEVEL_RADII.get(level, 30.0)

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(max(0, int(hover_debounce_ms)))
        self._hover_timer.timeout.connect(lambda: self.nodeActivated.emit(self.node_id))

        self.setZValue(2)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)

        self._text = QGraphicsSimpleTextItem(label, self)
        font = QFont()
        font.setPointSizeF(10.5 if level == 0 else 9.5)
        self._text.setFont(font)
        metrics = QFontMetricsF(font)
        max_w = 2 * self.radius * 0.82
        label_fit = label
        while metrics.horizontalAdvance(label_fit) > max_w and len(label_fit) > 2:
            label_fit = label_fit[:-2] + "…"
        self._text.setText(label_fit)
        tw = self._text.boundingRect().width()
        th = self._text.boundingRect().height()
        self._text.setPos(-tw / 2, -th / 2)
        self._text.setZValue(3)

    # ---- QGraphicsObject interface -------------------------------------- #
    def boundingRect(self) -> QRectF:
        r = self.radius + _PEN_WIDTH
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter, option, widget=None) -> None:
        color = LEVEL_COLORS.get(self.level, QColor("#888888"))
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(130), _PEN_WIDTH))
        r = self.radius
        painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        r = self.radius
        path.addEllipse(QRectF(-r, -r, 2 * r, 2 * r))
        return path

    def set_level(self, level: int) -> None:
        self.prepareGeometryChange()
        self.level = level
        self.radius = LEVEL_RADII.get(level, 30.0)
        self.update()

    # ---- events ---------------------------------------------------------- #
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
