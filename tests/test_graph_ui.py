"""Smoke tests for the graph UI layer (G-P0 regression guards).

These cover the paths the state/data-layer tests cannot reach: constructing
the bubble widget (Qt signals + hover timer require a real QObject base), and
rebuilding the panel scene from a stubbed state machine. Runs offscreen.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_node_constructs_with_timer_and_signals(qapp):
    """GraphNodeItem must be a real QObject: Signal + QTimer parenting work."""
    from src.ui.widgets.graph_node import GraphNodeItem

    item = GraphNodeItem(1, "测试节点标签", 0, hover_debounce_ms=10)
    assert item.radius > 0
    assert item._hover_timer.isSingleShot()
    assert item._hover_timer.interval() == 10

    activated, double_clicked = [], []
    item.nodeActivated.connect(lambda nid: activated.append(nid))
    item.nodeDoubleClicked.connect(lambda nid: double_clicked.append(nid))
    item.nodeActivated.emit(1)
    item.nodeDoubleClicked.emit(1)
    assert activated == [1]
    assert double_clicked == [1]


def test_node_set_level_updates_geometry(qapp):
    from src.ui.widgets.graph_node import GraphNodeItem, LEVEL_RADII

    item = GraphNodeItem(2, "标签", 1)
    item.set_level(0)
    assert item.level == 0
    assert item.radius == LEVEL_RADII[0]
    br = item.boundingRect()
    assert br.width() >= 2 * item.radius


@pytest.mark.asyncio
async def test_panel_rebuild_populates_scene(qapp):
    """Rebuild from a stub machine/provider must add nodes and edges."""
    from src.ui.graph_panel import GraphPanel

    panel = GraphPanel(app=None)

    class _State:
        current = 1
        previous = None
        related = [2, 3]

    class _Machine:
        state = _State()

    class _Provider:
        async def get_node(self, nid):
            return {"id": nid, "doc_id": 1, "content": f"内容{nid}", "label": f"节点{nid}"}

    panel._machine = _Machine()
    panel._provider = _Provider()

    await panel._rebuild()
    assert set(panel._nodes) == {1, 2, 3}
    assert len(panel._edges) == 2
    # Labels came through the provider and got cached.
    assert panel._label_cache[2] == "节点2"


@pytest.mark.asyncio
async def test_activation_coalesces_rapid_requests(qapp):
    """Rapid activations must not queue one rebuild per node (no re-entry)."""
    from src.ui.graph_panel import GraphPanel

    panel = GraphPanel(app=None)
    calls: list[int] = []

    class _State:
        current = 1
        previous = None
        related: list[int] = []

    class _Machine:
        state = _State()

        async def select(self, nid):
            import asyncio as _a

            calls.append(nid)
            self.state.current = nid
            await _a.sleep(0)  # yield so a second activation could interleave

    class _Provider:
        async def get_node(self, nid):
            return {"id": nid, "content": "", "label": str(nid)}

    panel._machine = _Machine()
    panel._provider = _Provider()

    panel._on_node_activated(1)
    panel._on_node_activated(2)  # first task in flight -> becomes pending
    panel._on_node_activated(3)  # overwrites pending -> only the latest survives
    assert panel._activation_task is not None
    await panel._activation_task
    assert calls[0] == 1
    assert calls[-1] == 3
    assert len(calls) == 2  # coalesced, not three rebuilds
    assert panel._activation_task is None
