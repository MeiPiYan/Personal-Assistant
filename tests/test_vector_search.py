"""Tests for the vector knowledge base service (P0)."""
import pytest

from src.ai.embedding import HashingEmbeddingBackend
from src.document.chunker import SemanticChunker
from src.search.vector_search import VectorStore
from src.storage.database import Database
from src.storage.dao import DAO


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the Database singleton so each test gets a clean in-memory DB."""
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
    # Offline hashing backend keeps the test hermetic (no model download).
    return VectorStore(dao=DAO(), backend=HashingEmbeddingBackend(dim=512))


# --------------------------------------------------------------------------- #
# SemanticChunker
# --------------------------------------------------------------------------- #
class TestSemanticChunker:
    def test_short_text_single_chunk(self):
        assert SemanticChunker(chunk_tokens=400).chunk("很短的一段话。") == [
            "很短的一段话。"
        ]

    def test_long_text_is_split(self):
        chunks = SemanticChunker(chunk_tokens=50, overlap_tokens=10).chunk(
            "句子。" * 200
        )
        assert len(chunks) > 1
        assert all(chunks)

    def test_empty_returns_empty(self):
        assert SemanticChunker().chunk("") == []

    def test_cjk_token_estimate_is_char_like(self):
        # 10 CJK chars should estimate ~10 tokens, not ~3 (the old English rule).
        assert SemanticChunker.estimate_tokens("一二三四五六七八九十") >= 10


# --------------------------------------------------------------------------- #
# Vector knowledge base
# --------------------------------------------------------------------------- #
class TestVectorKnowledgeBase:
    @pytest.mark.asyncio
    async def test_tables_created(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
            "('documents','chunks','chunks_fts')"
        )
        names = {r[0] for r in await cursor.fetchall()}
        assert {"documents", "chunks", "chunks_fts"} <= names

    @pytest.mark.asyncio
    async def test_index_creates_chunks_and_vectors(self, store):
        res = await store.index_text(
            "向量检索让知识库更聪明。深度学习改变了搜索方式。", title="t"
        )
        assert res["chunks"] >= 1
        assert await store.dao.count_chunks(res["doc_id"]) == res["chunks"]
        rows = await store.dao.get_chunks(res["doc_id"])
        assert rows
        assert all(row["embedding"] for row in rows)

    @pytest.mark.asyncio
    async def test_search_ranks_relevant_first(self, store):
        await store.index_text(
            "向量检索与知识库改造方案，使用sqlite-vec和bge模型。", title="vector"
        )
        await store.index_text("今天中午吃了西红柿炒鸡蛋，味道不错。", title="food")
        hits = await store.search("向量检索知识库", top_k=5)
        assert hits
        assert "向量" in hits[0]["content"]

    @pytest.mark.asyncio
    async def test_dedupe_by_content_hash(self, store):
        text = "重复的内容应该被去重。"
        first = await store.index_text(text, title="a")
        second = await store.index_text(text, title="b")
        assert second.get("deduped") is True
        assert second["doc_id"] == first["doc_id"]

    @pytest.mark.asyncio
    async def test_delete_document_cascades(self, store):
        res = await store.index_text("待删除文档内容。", title="del")
        await store.dao.delete_document(res["doc_id"])
        assert await store.dao.count_chunks(res["doc_id"]) == 0

    @pytest.mark.asyncio
    async def test_fts_keyword_channel_populated(self, store):
        await store.index_text("关键词通道测试uniqueKeyword。", title="f")
        rows = await store.dao.search_chunks_fts("uniqueKeyword", limit=5)
        assert isinstance(rows, list)

    @pytest.mark.asyncio
    async def test_knowledge_item_indexing(self, store):
        from src.storage.models import KnowledgeItem

        item = KnowledgeItem(title="AI", content="人工智能与机器学习", tags=["ai"])
        res = await store.index_knowledge_item(item)
        assert res["doc_id"] > 0
        assert res["chunks"] >= 1

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self, store):
        assert await store.search("   ") == []
