"""Tests for the three-level graph state machine (plan §5)."""

from __future__ import annotations

import pytest

from src.graph.graph_state import GraphState, GraphStateMachine


def provider_factory(mapping: dict):
    async def provider(node_id: int) -> list[int]:
        return list(mapping.get(node_id, []))
    return provider


# ---------- invariants ----------

class TestInvariants:
    def test_initial_state_t1(self):
        m = GraphStateMachine(related_provider=provider_factory({}))
        st = m.state
        assert st is None

    @pytest.mark.asyncio
    async def test_t1_exactly_one_current_no_previous(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2, 3]}))
        st = await m.enter_from_search(1)
        assert st.current == 1
        assert st.previous is None
        assert st.related == [2, 3]
        assert st.invariants_ok()

    def test_level_of(self):
        st = GraphState(current=1, previous=9, related=[2, 3])
        assert st.level_of(1) == 0
        assert st.level_of(9) == -1
        assert st.level_of(2) == 1
        assert st.level_of(99) is None


# ---------- transitions ----------

class TestTransitions:
    @pytest.mark.asyncio
    async def test_t2_select_related(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2, 3], 2: [4, 5]}))
        await m.enter_from_search(1)
        st = await m.select(2)
        assert st.current == 2
        assert st.previous == 1
        assert st.related == [4, 5]

    @pytest.mark.asyncio
    async def test_t3_go_back(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2], 2: [3]}))
        await m.enter_from_search(1)
        await m.select(2)          # current=2, previous=1
        st = await m.select(1)     # click red -1 level: go back
        assert st.current == 1
        assert st.previous == 2
        # provider of 1 is [2] but 2 is excluded (old current)
        assert 2 not in st.related

    @pytest.mark.asyncio
    async def test_t4_select_current_noop(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2]}))
        st0 = await m.enter_from_search(1)
        st1 = await m.select(1)
        assert st1 is st0

    @pytest.mark.asyncio
    async def test_t5_empty_related_allowed(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [], 2: []}))
        await m.enter_from_search(1)
        st = await m.select(2) if 2 in m.state.related else None
        # 1 has no related, so select a fresh focus directly via enter_from_search path
        st = await m.enter_from_search(2)
        assert st.current == 2
        assert st.related == []

    @pytest.mark.asyncio
    async def test_t6_enter_does_not_change_state(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2]}))
        st0 = await m.enter_from_search(1)
        before = (st0.current, st0.previous, list(st0.related))
        assert m.enter(2) == 2
        st1 = m.state
        after = (st1.current, st1.previous, list(st1.related))
        assert before == after


# ---------- boundary cases (plan §5.3) ----------

class TestBoundaries:
    @pytest.mark.asyncio
    async def test_related_excludes_self(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [1, 2]}))
        st = await m.enter_from_search(1)
        assert 1 not in st.related

    @pytest.mark.asyncio
    async def test_related_excludes_previous(self):
        # 2's provider returns 1 (the old current) — must be excluded
        m = GraphStateMachine(related_provider=provider_factory({1: [2], 2: [1, 3]}))
        await m.enter_from_search(1)
        st = await m.select(2)
        assert st.current == 2
        assert 1 not in st.related
        assert st.related == [3]

    @pytest.mark.asyncio
    async def test_dedup_related(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2, 2, 3]}))
        st = await m.enter_from_search(1)
        assert st.related == [2, 3]

    @pytest.mark.asyncio
    async def test_select_unrelated_becomes_focus(self):
        m = GraphStateMachine(related_provider=provider_factory({1: [2], 5: [6]}))
        await m.enter_from_search(1)
        st = await m.select(5)  # not in related: treated as fresh focus
        assert st.current == 5
        assert st.previous == 1

    @pytest.mark.asyncio
    async def test_select_before_init_raises(self):
        m = GraphStateMachine()
        with pytest.raises(RuntimeError):
            await m.select(1)
