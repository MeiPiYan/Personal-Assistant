"""Tests for GraphDataProvider: label extraction + level-1 candidates (plan §6/§8.2)."""

from __future__ import annotations

import struct

import pytest

from src.graph.graph_data import GraphDataProvider, _to_vec, extract_label


def f32_blob(vec) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


class StubDAO:
    """Minimal DAO returning a fixed chunk list."""

    def __init__(self, rows):
        self._rows = rows

    async def get_chunks(self, doc_id=None, limit=5000):
        return [dict(r) for r in self._rows]


# ---------- label extraction ----------

class TestExtractLabel:
    def test_chinese_keyword(self):
        label = extract_label("向量检索是知识库的核心能力，向量检索很快。")
        assert 0 < len(label) <= 12
        assert label != "（空）"

    def test_english_word(self):
        label = extract_label("sqlite vector search is fast")
        assert label.isascii() and len(label) <= 12

    def test_truncation(self):
        label = extract_label("超长关键词没有断词所以整段返回" * 3, max_chars=12)
        assert len(label) <= 12

    def test_empty_fallback(self):
        assert extract_label("") == "（空）"
        assert extract_label(None) == "（空）"

    def test_stopword_not_chosen(self):
        label = extract_label("的 了 是 知识库")
        assert label == "知识库"


# ---------- vector decoding ----------

class TestToVec:
    def test_blob(self):
        assert _to_vec(f32_blob([1.0, 2.0, 3.0])) == [1.0, 2.0, 3.0]

    def test_none_and_bad(self):
        assert _to_vec(None) is None
        assert _to_vec(b"") is None
        assert _to_vec([0.1, 0.2]) == [0.1, 0.2]


# ---------- related chunks ----------

class TestRelated:
    @pytest.fixture
    def dao(self):
        # a=[1,0], b=[0.9,0.1] (cos≈0.99), c=[0,1] (cos=0), d=None
        return StubDAO([
            {"id": 1, "doc_id": 10, "content": "向量检索", "embedding": f32_blob([1.0, 0.0])},
            {"id": 2, "doc_id": 10, "content": "向量数据库", "embedding": f32_blob([0.9, 0.1])},
            {"id": 3, "doc_id": 11, "content": "今天天气", "embedding": f32_blob([0.0, 1.0])},
            {"id": 4, "doc_id": 11, "content": "无向量文本", "embedding": None},
        ])

    @pytest.mark.asyncio
    async def test_related_filters_and_scores(self, dao):
        p = GraphDataProvider(dao, top_k=8, threshold=0.35)
        rel = await p.related_chunks(1)
        ids = [r["chunk_id"] for r in rel]
        assert 2 in ids and 3 not in ids and 4 not in ids and 1 not in ids
        top = rel[0]
        assert top["chunk_id"] == 2 and top["score"] >= 0.9

    @pytest.mark.asyncio
    async def test_top_k_truncates(self, dao):
        p = GraphDataProvider(dao, top_k=1, threshold=0.0)
        rel = await p.related_chunks(1)
        assert len(rel) <= 1

    @pytest.mark.asyncio
    async def test_related_ids(self, dao):
        p = GraphDataProvider(dao, top_k=8, threshold=0.35)
        ids = await p.related_ids(1)
        assert ids == [2]

    @pytest.mark.asyncio
    async def test_missing_node(self, dao):
        p = GraphDataProvider(dao)
        assert await p.related_chunks(999) == []

    @pytest.mark.asyncio
    async def test_node_without_embedding(self, dao):
        p = GraphDataProvider(dao)
        assert await p.related_chunks(4) == []

    @pytest.mark.asyncio
    async def test_get_node_label(self, dao):
        p = GraphDataProvider(dao)
        node = await p.get_node(1)
        assert node["id"] == 1 and node["label"]
        assert await p.get_node(999) is None
