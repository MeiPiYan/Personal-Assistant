"""Programmatic icon generation for the AI Assistant.

Provides QIcon objects for all application icons, drawn via QPainter when
SVG loading is unavailable.  Icons use the application's color palette so
they match both dark and light themes.
"""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import Qt, QRect, QPointF, QLineF, QSize
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QPolygonF, QPainterPath,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

# ---------------------------------------------------------------------------
# Color palette (matches dark theme)
# ---------------------------------------------------------------------------
_COLOR_NORMAL = QColor(176, 176, 200)     # #b0b0c8  muted gray-blue
_COLOR_HOVER = QColor(196, 196, 220)      # #c4c4dc  slightly brighter
_COLOR_ACTIVE = QColor(129, 140, 248)     # #818cf8  indigo accent
_COLOR_TRAY = QColor(79, 70, 229)         # #4f46e5  primary brand
_SIZE = 24  # base icon size in px


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pixmap_base(size: int = _SIZE, fill: QColor | None = None) -> QPixmap:
    """Create a transparent pixmap of *size* x *size*."""
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0) if fill is None else fill)
    return pm


def _load_svg_icon(name: str) -> QIcon | None:
    """Try to load an SVG from assets/icons/<name>.svg."""
    svg = _ICONS_DIR / f"{name}.svg"
    if svg.exists():
        icon = QIcon(str(svg))
        if not icon.isNull():
            return icon
    return None


# ---------------------------------------------------------------------------
# Individual icon painters
# ---------------------------------------------------------------------------

def _paint_chat(p: QPainter, size: int, color: QColor) -> None:
    """Speech bubble with two text lines."""
    s = size / 24.0  # scale factor
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    # Bubble body
    p.drawRoundedRect(QRect(int(4*s), int(3*s), int(16*s), int(13*s)), 3*s, 3*s)
    # Tail
    tail = QPolygonF([
        QPointF(7*s, 16*s), QPointF(5*s, 21*s), QPointF(13*s, 16*s),
    ])
    p.setPen(pen)
    p.drawPolygon(tail)
    # Text lines
    thin = QPen(color, 1.2 * s, Qt.SolidLine, Qt.RoundCap)
    p.setPen(thin)
    p.drawLine(QLineF(8*s, 8*s, 16*s, 8*s))
    p.drawLine(QLineF(8*s, 11.5*s, 13*s, 11.5*s))


def _paint_search(p: QPainter, size: int, color: QColor) -> None:
    """Magnifying glass."""
    s = size / 24.0
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QRectF(3*s, 3*s, 13*s, 13*s))
    p.drawLine(QLineF(13*s, 13*s, 19.5*s, 19.5*s))


def _paint_document(p: QPainter, size: int, color: QColor) -> None:
    """Page with folded corner and text lines."""
    s = size / 24.0
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    # Page outline
    path = QPainterPath()
    path.moveTo(5*s, 2*s)
    path.lineTo(14*s, 2*s)
    path.lineTo(19*s, 7*s)
    path.lineTo(19*s, 22*s)
    path.lineTo(5*s, 22*s)
    path.closeSubpath()
    p.drawPath(path)
    # Fold line
    p.drawLine(QLineF(14*s, 2*s, 14*s, 7*s))
    p.drawLine(QLineF(14*s, 7*s, 19*s, 7*s))
    # Text lines
    thin = QPen(color, 1.2 * s, Qt.SolidLine, Qt.RoundCap)
    p.setPen(thin)
    p.drawLine(QLineF(8*s, 11*s, 16*s, 11*s))
    p.drawLine(QLineF(8*s, 14.5*s, 14*s, 14.5*s))
    p.drawLine(QLineF(8*s, 18*s, 12*s, 18*s))


def _paint_monitor(p: QPainter, size: int, color: QColor) -> None:
    """Screen with stand — monitoring icon."""
    s = size / 24.0
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    # Screen
    p.drawRoundedRect(QRectF(2*s, 3*s, 20*s, 13*s), 1.5*s, 1.5*s)
    # Stand
    p.drawLine(QLineF(12*s, 16*s, 12*s, 20*s))
    p.drawLine(QLineF(8*s, 20.5*s, 16*s, 20.5*s))
    # Play triangle in center (monitoring / active)
    p.setBrush(QBrush(color))
    tri = QPolygonF([
        QPointF(10.5*s, 7.5*s),
        QPointF(10.5*s, 13.5*s),
        QPointF(15*s, 10.5*s),
    ])
    p.drawPolygon(tri)
    p.setBrush(Qt.NoBrush)


def _paint_diary(p: QPainter, size: int, color: QColor) -> None:
    """Open notebook."""
    s = size / 24.0
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    # Left page
    p.drawRoundedRect(QRectF(2*s, 2*s, 10*s, 20*s), 1*s, 1*s)
    # Right page
    p.drawRoundedRect(QRectF(12*s, 2*s, 10*s, 20*s), 1*s, 1*s)
    # Spine
    p.drawLine(QLineF(12*s, 2*s, 12*s, 22*s))
    # Lines on left page
    thin = QPen(color, 1.0 * s, Qt.SolidLine, Qt.RoundCap)
    p.setPen(thin)
    for y in [7*s, 10*s, 13*s, 16*s]:
        p.drawLine(QLineF(4*s, y, 10*s, y))
    # Lines on right page
    for y in [7*s, 10*s, 13*s]:
        p.drawLine(QLineF(14*s, y, 20*s, y))


def _paint_knowledge(p: QPainter, size: int, color: QColor) -> None:
    """Lightbulb icon."""
    s = size / 24.0
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    # Bulb
    p.drawEllipse(QRectF(6*s, 2*s, 12*s, 12*s))
    # Base
    p.drawRoundedRect(QRectF(8.5*s, 14*s, 7*s, 3*s), 1*s, 1*s)
    # Base lines
    thin = QPen(color, 1.2 * s, Qt.SolidLine, Qt.RoundCap)
    p.setPen(thin)
    p.drawLine(QLineF(9.5*s, 18.5*s, 14.5*s, 18.5*s))
    p.drawLine(QLineF(10*s, 20.5*s, 14*s, 20.5*s))
    # Filament
    glow_pen = QPen(color, 1.0 * s, Qt.SolidLine, Qt.RoundCap)
    p.setPen(glow_pen)
    p.drawLine(QLineF(10*s, 10*s, 12*s, 7*s))
    p.drawLine(QLineF(12*s, 7*s, 14*s, 10*s))
    # Rays
    ray_pen = QPen(color, 1.0 * s, Qt.SolidLine, Qt.RoundCap)
    p.setPen(ray_pen)
    p.drawLine(QLineF(12*s, 0.5*s, 12*s, 1*s))
    p.drawLine(QLineF(3*s, 8*s, 4.5*s, 8*s))
    p.drawLine(QLineF(19.5*s, 8*s, 21*s, 8*s))
    p.drawLine(QLineF(5*s, 3*s, 6*s, 4*s))
    p.drawLine(QLineF(18*s, 4*s, 19*s, 3*s))


def _paint_settings(p: QPainter, size: int, color: QColor) -> None:
    """Gear / cog icon."""
    s = size / 24.0
    pen = QPen(color, 1.5 * s, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    # Inner circle
    p.drawEllipse(QRectF(8.5*s, 8.5*s, 7*s, 7*s))
    # Outer gear teeth (8 lines radiating outward)
    cx, cy = 12*s, 12*s
    outer_r = 10*s
    inner_r = 7*s
    for i in range(8):
        angle = i * math.pi / 4
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        # Perpendicular offset for tooth width
        dx = 1.5 * s * math.cos(angle + math.pi / 2)
        dy = 1.5 * s * math.sin(angle + math.pi / 2)
        tooth = QPolygonF([
            QPointF(x1 - dx, y1 - dy),
            QPointF(x2 - dx, y2 - dy),
            QPointF(x2 + dx, y2 + dy),
            QPointF(x1 + dx, y1 + dy),
        ])
        p.setBrush(QBrush(color))
        p.drawPolygon(tooth)
        p.setBrush(Qt.NoBrush)


def _paint_tray(p: QPainter, size: int, color: QColor) -> None:
    """App logo for system tray — rounded square with 'AI' text."""
    s = size / 64.0
    # Filled rounded rect
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))
    p.drawRoundedRect(QRectF(2*s, 2*s, 60*s, 60*s), 14*s, 14*s)
    # "AI" text
    p.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", int(28 * s), QFont.Bold)
    p.setFont(font)
    p.drawText(QRectF(0, 0, 64*s, 64*s), Qt.AlignCenter, "AI")


# ---------------------------------------------------------------------------
# Paint dispatch table
# ---------------------------------------------------------------------------
_PAINTERS = {
    "chat": _paint_chat,
    "search": _paint_search,
    "document": _paint_document,
    "monitor": _paint_monitor,
    "diary": _paint_diary,
    "knowledge": _paint_knowledge,
    "settings": _paint_settings,
    "tray": _paint_tray,
}

# Navigation mapping: icon_name -> (label, tooltip)
NAV_ICONS: list[tuple[str, str, str]] = [
    ("chat",     "对话", "AI 对话"),
    ("search",   "搜索", "网络 / 本地搜索"),
    ("document", "文档", "文档解析与总结"),
    ("monitor",  "监控", "聊天消息监控"),
    ("diary",    "日记", "日记与笔记"),
    ("knowledge","知识", "知识库"),
    ("settings", "设置", "应用设置"),
]


def get_icon(
    name: str,
    color: QColor | None = None,
    size: int = _SIZE,
) -> QIcon:
    """Return a QIcon for *name*.

    Strategy:
    1. Try loading assets/icons/<name>.svg (works if QtSvg plugin present).
    2. Fall back to QPainter-drawn pixmap.
    """
    if color is None:
        color = _COLOR_NORMAL

    # Attempt SVG load first
    svg_icon = _load_svg_icon(name)
    if svg_icon is not None:
        return svg_icon

    # QPainter fallback
    painter_fn = _PAINTERS.get(name)
    if painter_fn is None:
        # Unknown icon – return a plain dot
        pm = _pixmap_base(size)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(color))
        p.drawEllipse(QRectF(6, 6, 12, 12))
        p.end()
        return QIcon(pm)

    actual_size = 64 if name == "tray" else size
    pm = _pixmap_base(actual_size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    painter_fn(p, actual_size, color)
    p.end()
    return QIcon(pm)


def get_nav_icons(color: QColor | None = None) -> list[tuple[QIcon, str, str]]:
    """Return list of (QIcon, label, tooltip) for sidebar navigation."""
    return [
        (get_icon(name, color=color), label, tip)
        for name, label, tip in NAV_ICONS
    ]


def tray_icon(color: QColor | None = None) -> QIcon:
    """Return the application tray icon."""
    return get_icon("tray", color=color, size=64)
