"""Semi-transparent edge between bubbles (plan §1.2/§8.1).

Opacity maps to similarity: the stronger the relation, the more solid the line.
"""

from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsLineItem

from .graph_node import GraphNodeItem


class GraphEdgeItem(QGraphicsLineItem):
    """Line between two nodes; source/target are GraphNodeItem instances."""

    def __init__(self, source: GraphNodeItem, target: GraphNodeItem, score: float = 0.5,
                 emphasized: bool = False, parent=None):
        super().__init__(parent)
        self.source = source
        self.target = target
        self.score = float(score)
        self.emphasized = emphasized  # the 0 <-> -1 "came from" line
        self.setZValue(1)
        self.update_position()

    def update_position(self) -> None:
        self.setLine(QLineF(self.source.pos(), self.target.pos()))
        base = 0.25 + 0.35 * min(max(self.score, 0.0), 1.0)
        if self.emphasized:
            base = min(base + 0.3, 0.95)
        color = QColor("#9AA0A6")
        color.setAlphaF(base)
        width = 2.2 if self.emphasized else 1.4
        self.setPen(QPen(color, width))
