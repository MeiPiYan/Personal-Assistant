"""Knowledge graph panel: bubble canvas with three-level exploration (G-P0).

Interaction (plan §4): click (or hover-debounce) a blue level-1 bubble — or
the red level -1 to go back — to make it the new green level-0; double-click
any bubble to emit a navigation request. Rendering via QGraphicsView.
"""

from __future__ import annotations

import asyncio

from src.ui.logging import logger
from src.ui.tasks import spawn_ui
import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsScene, QGraphicsView,
)

from .styles import ThemeManager
from .widgets.graph_node import GraphNodeItem
from .widgets.graph_edge import GraphEdgeItem


class GraphPanel(QWidget):
    """Three-level knowledge bubble graph."""

    node_double_clicked = Signal(int)

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._dao = None
        self._provider = None
        self._machine = None
        self._nodes: dict[int, GraphNodeItem] = {}
        self._edges: list[GraphEdgeItem] = []
        self._label_cache: dict[int, str] = {}
        self._activation_task: asyncio.Task | None = None
        self._pending_node: int | None = None
        self._setup_ui()
        ThemeManager.register_panel(self)

    # ------------------------------------------------------------------ #
    # wiring
    # ------------------------------------------------------------------ #
    def set_dao(self, dao) -> None:
        self._dao = dao
        try:
            from ..graph.graph_data import GraphDataProvider
            from ..graph.graph_state import GraphStateMachine

            cfg = self._graph_cfg()
            self._provider = GraphDataProvider(
                dao, top_k=cfg["level1_top_k"], threshold=cfg["similarity_threshold"]
            )
            self._machine = GraphStateMachine(
                related_provider=self._provider.related_ids
            )
        except Exception as e:
            logger.warning(f"[GraphPanel] init failed: {e}")
            self._provider = None
            self._machine = None

    def _graph_cfg(self) -> dict:
        defaults = {
            "level1_top_k": 8,
            "similarity_threshold": 0.35,
            "hover_debounce_ms": 250,
            "anim_duration_ms": 300,
        }
        try:
            cfg = self.app.config.get("ai.graph", {}) if self.app else {}
            if isinstance(cfg, dict):
                defaults.update({k: v for k, v in cfg.items() if k in defaults})
        except Exception:
            pass
        return defaults

    async def enter_from_search(self, chunk_id: int) -> None:
        """T1 entry: focus the graph on a search-result chunk."""
        if self._machine is None:
            return
        await self._machine.enter_from_search(chunk_id)
        await self._rebuild()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(16, 10, 16, 8)
        title = QLabel("知识图谱")
        title.setObjectName("panelTitle")
        top.addWidget(title)
        top.addStretch()
        self._legend = QLabel(
            "🟢 当前选中  🔴 上一步  🔵 关联知识 — 单击/悬停切换选中，双击打开来源"
        )
        top.addWidget(self._legend)
        layout.addLayout(top)

        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene, self)
        self._view.setRenderHint(QPainter.Antialiasing, True)
        self._view.setDragMode(QGraphicsView.ScrollHandDrag)
        self._view.setBackgroundBrush(self._bg_brush())
        layout.addWidget(self._view, 1)

        self._empty_hint = QLabel(
            "暂无图谱数据：请先在知识库/文档中建立索引，然后从检索结果进入图谱"
        )
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setVisible(False)
        layout.addWidget(self._empty_hint)

    def _bg_brush(self):
        try:
            c = ThemeManager.get_colors()
            return QBrush(QColor(c.bg_primary))
        except Exception:
            return QBrush(QColor("#FFFFFF"))

    def _apply_theme(self) -> None:
        self._view.setBackgroundBrush(self._bg_brush())

    # ------------------------------------------------------------------ #
    # graph (re)building (async: labels come from the data provider)
    # ------------------------------------------------------------------ #
    async def _rebuild(self) -> None:
        st = self._machine.state if self._machine else None
        self._clear_items()
        if st is None:
            self._empty_hint.setVisible(True)
            return

        ids = [st.current] + ([st.previous] if st.previous is not None else []) + list(st.related)
        for nid in ids:
            if nid not in self._label_cache:
                node = await self._provider.get_node(nid) if self._provider else None
                self._label_cache[nid] = (node or {}).get("label", f"#{nid}")

        cur = GraphNodeItem(st.current, self._label_cache[st.current], 0,
                            hover_debounce_ms=self._cfg_hover())
        cur.setPos(0, 0)
        self._nodes[st.current] = cur

        if st.previous is not None:
            prev = GraphNodeItem(st.previous, self._label_cache[st.previous], -1,
                                 hover_debounce_ms=self._cfg_hover())
            prev.setPos(-170, 0)
            self._nodes[st.previous] = prev
            self._edges.append(GraphEdgeItem(cur, prev, score=0.8, emphasized=True))

        n = len(st.related)
        for i, rid in enumerate(st.related):
            child = GraphNodeItem(rid, self._label_cache[rid], 1,
                                  hover_debounce_ms=self._cfg_hover())
            angle = 2 * math.pi * i / max(n, 1) - math.pi / 2
            child.setPos(150 * math.cos(angle), 150 * math.sin(angle))
            self._nodes[rid] = child
            self._edges.append(GraphEdgeItem(cur, child, score=0.5))

        for node in self._nodes.values():
            node.nodeActivated.connect(self._on_node_activated)
            node.nodeDoubleClicked.connect(self._on_node_double_clicked)
            self._scene.addItem(node)
        for e in self._edges:
            e.update_position()
            self._scene.addItem(e)

        self._empty_hint.setVisible(len(self._nodes) <= 1 and st.previous is None)
        self._view.fitInView(self._scene.itemsBoundingRect().adjusted(-60, -60, 60, 60),
                             Qt.KeepAspectRatio)

    def _cfg_hover(self) -> int:
        try:
            return int(self._graph_cfg().get("hover_debounce_ms", 250))
        except Exception:
            return 250

    # ------------------------------------------------------------------ #
    # interaction handlers
    # ------------------------------------------------------------------ #
    def _on_node_activated(self, node_id: int) -> None:
        if self._machine is None:
            return
        # Re-entrancy guard: rapid hover/click across several nodes coalesces
        # into the latest request instead of queueing one rebuild per node.
        if self._activation_task is not None and not self._activation_task.done():
            self._pending_node = node_id
            return
        self._pending_node = None
        self._activation_task = spawn_ui(self._run_activation(node_id))

    async def _run_activation(self, node_id: int) -> None:
        try:
            nid = node_id
            while True:
                await self._machine.select(nid)
                await self._rebuild()
                if self._pending_node is None:
                    break
                nid = self._pending_node
                self._pending_node = None
        except Exception as e:
            logger.warning(f"[GraphPanel] activation failed: {e}")
        finally:
            self._activation_task = None

    def _on_node_double_clicked(self, node_id: int) -> None:
        self.node_double_clicked.emit(node_id)

    def _clear_items(self) -> None:
        for e in self._edges:
            if e.scene() is self._scene:
                self._scene.removeItem(e)
        for n in self._nodes.values():
            if n.scene() is self._scene:
                self._scene.removeItem(n)
        self._edges.clear()
        self._nodes.clear()
