"""Tests for hybrid retrieval with RRF fusion (P2)."""
import pytest

from src.ai.embedding import HashingEmbeddingBackend
from src.search.hybrid_search import HybridSearcher, rrf_fuse
from src.search.vector_search import VectorStore
from src.storage.database import Database
from src.storage.dao import DAO


@pytest.fixture(autouse=True)
def _reset_singleton():
    Database._instance = None
    Database._db = None
    Database._db_path = "data/assistant.db"
    yield
    Database._instance = None
    Database._db = None


@pytest.fixture
async def db():
    database = Database()
    await database.connect(":memory:")
    yield database
    await database.close()


@pytest.fixture
def store(db):
    return VectorStore(dao=DAO(), backend=HashingEmbeddingBackend(dim=512))


@pytest.fixture
def hybrid(store):
    return HybridSearcher(vector_store=store)


# --------------------------------------------------------------------------- #
# RRF fusion (pure)
# --------------------------------------------------------------------------- #
class TestRRFFuse:
    def test_item_in_both_lists_ranks_highest(self):
        lexical = [{"chunk_id": 1}, {"chunk_id": 2}]
        semantic = [{"chunk_id": 2}, {"chunk_id": 3}]
        fused = rrf_fuse([lexical, semantic], top_k=3)
        # chunk 2 appears in both -> should win.
        assert fused[0]["chunk_id"] == 2
        assert set(fused[0]["sources"]) == {0, 1}

    def test_top_k_limit(self):
        lex = [{"chunk_id": i} for i in range(10)]
        assert len(rrf_fuse([lex], top_k=4)) == 4

    def test_rrf_score_monotonic(self):
        lex = [{"chunk_id": 1}, {"chunk_id": 2}, {"chunk_id": 3}]
        fused = rrf_fuse([lex], top_k=3)
        scores = [f["rrf_score"] for f in fused]
        assert scores == sorted(scores, reverse=True)

    def test_empty_lists(self):
        assert rrf_fuse([[], []], top_k=5) == []

    def test_source_tracking(self):
        lex = [{"chunk_id": 1}]
        sem = [{"chunk_id": 2}]
        fused = rrf_fuse([lex, sem], top_k=5)
        by_id = {f["chunk_id"]: f["sources"] for f in fused}
        assert by_id[1] == [0]
        assert by_id[2] == [1]


# --------------------------------------------------------------------------- #
# HybridSearcher end to end
# --------------------------------------------------------------------------- #
class TestHybridSearcher:
    @pytest.mark.asyncio
    async def test_empty_query(self, hybrid):
        assert await hybrid.search("   ") == []

    @pytest.mark.asyncio
    async def test_finds_indexed_content(self, store, hybrid):
        await store.index_text(
            "sqlite-vec 提供 SQLite 的向量检索能力，用于知识库。", title="vec"
        )
        await store.index_text("今天天气不错，适合出门散步。", title="weather")
        hits = await hybrid.search("向量检索知识库", top_k=5)
        assert hits
        assert any("向量" in h["content"] for h in hits)

    @pytest.mark.asyncio
    async def test_results_have_rrf_fields(self, store, hybrid):
        await store.index_text("混合检索融合BM25与向量。", title="hybrid")
        hits = await hybrid.search("混合检索", top_k=5)
        assert hits
        for h in hits:
            assert "rrf_score" in h
            assert "sources" in h

    @pytest.mark.asyncio
    async def test_build_context_returns_text_and_sources(self, store, hybrid):
        await store.index_text("构建上下文用于RAG注入对话。", title="rag")
        ctx, sources = await hybrid.build_context("RAG 上下文", top_k=3)
        assert isinstance(ctx, str)
        assert isinstance(sources, list)
        if sources:
            assert ctx
            assert "[1]" in ctx

    @pytest.mark.asyncio
    async def test_build_context_empty_when_no_data(self, hybrid):
        ctx, sources = await hybrid.build_context("毫无相关内容", top_k=3)
        assert ctx == ""
        assert sources == []

    @pytest.mark.asyncio
    async def test_lexical_and_semantic_both_considered(self, store, hybrid):
        # Index several docs; ensure the fusion doesn't crash on partial channels.
        for i in range(5):
            await store.index_text(f"文档{i} 主题向量检索 编号{i}", title=f"d{i}")
        hits = await hybrid.search("向量检索", top_k=10)
        assert hits
        # At least some results should carry a source annotation.
        assert all(isinstance(h["sources"], list) for h in hits)
