"""Three-level bubble state machine (pure logic, no UI dependencies).

Levels (see 知识图谱气泡可视化规划书.md §3/§5):
- level 0  : current selection, exactly one at any time
- level -1 : previous level-0 node, 0 or 1
- level 1  : related next-level nodes, 0..n

Transitions (plan §5.2):
- T1 enter_from_search(node) : search entry
- T2 select(x) with x in related
- T3 select(previous)        : go back
- T4 select(current)         : no-op
- T6 enter(x)                : double-click navigation does NOT change state
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GraphState:
    """Snapshot of the three-level bubble state."""

    current: int
    previous: int | None = None
    related: list[int] = field(default_factory=list)

    def invariants_ok(self) -> bool:
        """Core invariants (plan §2): exactly one 0-level, at most one -1."""
        return self.current is not None

    def level_of(self, node_id: int) -> int | None:
        if node_id == self.current:
            return 0
        if node_id is not None and node_id == self.previous:
            return -1
        if node_id in self.related:
            return 1
        return None


class GraphStateMachine:
    """Manages GraphState transitions with a pluggable related-nodes provider.

    ``related_provider`` must be an async callable ``(node_id) -> list[int]``
    returning candidate related node ids (already threshold-filtered). The
    machine itself applies the self/previous exclusion rules (plan §5.3).
    """

    def __init__(self, related_provider=None):
        self._related_provider = related_provider
        self._state: GraphState | None = None

    # ------------------------------------------------------------------
    @property
    def state(self) -> GraphState | None:
        return self._state

    async def enter_from_search(self, node_id: int) -> GraphState:
        """T1: enter the graph from a search result."""
        related = await self._compute_related(node_id, exclude=())
        self._state = GraphState(current=node_id, previous=None, related=related)
        return self._state

    async def select(self, node_id: int) -> GraphState:
        """T2/T3/T4: select a bubble (hover debounce or click)."""
        st = self._state
        if st is None:
            raise RuntimeError("GraphStateMachine not initialised; call enter_from_search first")
        if node_id == st.current:
            return st  # T4: no-op
        if node_id == st.previous:
            # T3: go back — previous becomes current, current becomes previous
            new_related = await self._compute_related(node_id, exclude=(st.current,))
            st = GraphState(current=node_id, previous=st.current, related=new_related)
            self._state = st
            return st
        if node_id in st.related:
            # T2: level-1 becomes new level-0; old current becomes level -1
            new_related = await self._compute_related(node_id, exclude=(st.current,))
            st = GraphState(current=node_id, previous=st.current, related=new_related)
            self._state = st
            return st
        # selecting an unrelated node: treat as a fresh focus (T2 variant)
        new_related = await self._compute_related(node_id, exclude=(st.current,))
        st = GraphState(current=node_id, previous=st.current, related=new_related)
        self._state = st
        return st

    def enter(self, node_id: int) -> int:
        """T6: double-click navigation — returns node_id, does NOT change state."""
        return node_id

    # ------------------------------------------------------------------
    async def _compute_related(self, node_id: int, exclude: tuple) -> list[int]:
        if self._related_provider is None:
            return []
        raw = self._related_provider(node_id)
        if hasattr(raw, "__await__"):
            raw = await raw
        out: list[int] = []
        for rid in raw or []:
            if rid == node_id or rid in exclude:
                continue
            if rid in out:
                continue
            out.append(rid)
        return out
