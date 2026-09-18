"""Tests for the vector knowledge base backfill service (P1)."""
import pytest

from src.ai.embedding import HashingEmbeddingBackend
from src.search.backfill import BackfillService
from src.search.vector_search import VectorStore
from src.storage.database import Database
from src.storage.dao import DAO
from src.storage.models import DiaryEntry, KnowledgeItem


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
def dao(db):
    return DAO()


@pytest.fixture
def service(dao):
    store = VectorStore(dao=dao, backend=HashingEmbeddingBackend(dim=512))
    return BackfillService(dao=dao, vector_store=store)


class TestBackfillKnowledge:
    @pytest.mark.asyncio
    async def test_backfill_indexes_existing_items(self, dao, service):
        for i in range(3):
            await dao.insert_knowledge(
                KnowledgeItem(title=f"标题{i}", content=f"内容向量检索{i}", tags=["t"])
            )
        report = await service.backfill_knowledge()
        assert report["total"] == 3
        assert report["indexed"] == 3
        assert report["failed"] == 0
        assert await dao.count_chunks() >= 3

    @pytest.mark.asyncio
    async def test_backfill_is_idempotent(self, dao, service):
        await dao.insert_knowledge(KnowledgeItem(title="a", content="重复内容去重"))
        first = await service.backfill_knowledge()
        second = await service.backfill_knowledge()
        assert first["indexed"] == 1
        # Second run must not create duplicate documents.
        assert second["deduped"] == 1
        assert second["indexed"] == 0
        assert await dao.count_chunks() == first["indexed"]

    @pytest.mark.asyncio
    async def test_backfill_empty(self, service):
        report = await service.backfill_knowledge()
        assert report == {"total": 0, "indexed": 0, "deduped": 0, "failed": 0}

    @pytest.mark.asyncio
    async def test_progress_callback(self, dao, service):
        for i in range(4):
            await dao.insert_knowledge(KnowledgeItem(title=f"t{i}", content=f"内容{i}"))
        seen = []
        await service.backfill_knowledge(batch_size=2, on_progress=lambda d, t: seen.append((d, t)))
        assert seen[-1] == (4, 4)


class TestBackfillDiaries:
    @pytest.mark.asyncio
    async def test_backfill_diaries(self, dao, service):
        await dao.insert_diary(DiaryEntry(content="今天研究了向量检索。", tags=[]))
        await dao.insert_diary(DiaryEntry(content="明天继续做知识库。", tags=[]))
        report = await service.backfill_diaries()
        assert report["indexed"] == 2
        assert report["failed"] == 0


class TestBackfillAll:
    @pytest.mark.asyncio
    async def test_backfill_all(self, dao, service):
        await dao.insert_knowledge(KnowledgeItem(title="k", content="知识内容"))
        await dao.insert_diary(DiaryEntry(content="日记内容", tags=[]))
        report = await service.backfill_all()
        assert report["knowledge"]["indexed"] == 1
        assert report["diary"]["indexed"] == 1
