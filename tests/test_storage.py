"""Tests for storage layer: Database, DAO, and data models."""
import asyncio
import json

import pytest

from src.storage.models import ChatMessage, ChatSummary, DiaryEntry, KnowledgeItem
from src.storage.database import Database
from src.storage.dao import DAO


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset Database singleton before each test so we get a fresh instance."""
    Database._instance = None
    Database._db = None
    Database._db_path = "data/assistant.db"
    yield
    # Cleanup after test
    Database._instance = None
    Database._db = None


@pytest.fixture
async def db():
    """Provide a connected in-memory Database."""
    database = Database()
    await database.connect(":memory:")
    yield database
    await database.close()


@pytest.fixture
async def dao(db):
    """Provide a DAO backed by an in-memory database."""
    # DAO creates its own Database() reference, which will be the singleton
    return DAO()


# ===========================================================================
# Data Models
# ===========================================================================

class TestChatMessage:
    def test_defaults(self):
        msg = ChatMessage(platform="wechat", sender="Alice", content="Hi")
        assert msg.platform == "wechat"
        assert msg.sender == "Alice"
        assert msg.content == "Hi"
        assert msg.group_name == ""
        assert msg.msg_type == "text"
        assert msg.raw_data == ""
        assert msg.created_at is not None

    def test_custom_fields(self):
        msg = ChatMessage(
            platform="qq",
            sender="Bob",
            content="Hello",
            group_name="Dev",
            msg_type="image",
            raw_data='{"key":"val"}',
        )
        assert msg.group_name == "Dev"
        assert msg.msg_type == "image"
        assert msg.raw_data == '{"key":"val"}'


class TestDiaryEntry:
    def test_defaults(self):
        entry = DiaryEntry(content="Today was good")
        assert entry.content == "Today was good"
        assert entry.summary == ""
        assert entry.tags == []
        assert entry.mood == ""
        assert entry.id is None

    def test_with_tags(self):
        entry = DiaryEntry(content="Note", tags=["work", "urgent"], mood="happy")
        assert entry.tags == ["work", "urgent"]
        assert entry.mood == "happy"


class TestKnowledgeItem:
    def test_defaults(self):
        item = KnowledgeItem(title="T", content="C")
        assert item.title == "T"
        assert item.content == "C"
        assert item.source_url == ""
        assert item.source_type == "manual"
        assert item.tags == []

    def test_custom_source(self):
        item = KnowledgeItem(
            title="Doc",
            content="Text",
            source_url="https://example.com",
            source_type="url",
            category="docs",
            tags=["python"],
        )
        assert item.source_url == "https://example.com"
        assert item.category == "docs"


class TestChatSummary:
    def test_defaults(self):
        s = ChatSummary(platform="wechat", chat_identifier="c1", summary="sum")
        assert s.message_count == 0
        assert s.categories == {}


# ===========================================================================
# Database
# ===========================================================================

class TestDatabase:
    @pytest.mark.asyncio
    async def test_connect_creates_connection(self, db):
        assert db.connection is not None

    @pytest.mark.asyncio
    async def test_table_chat_messages_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_table_diary_entries_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='diary_entries'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_table_knowledge_items_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_items'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_table_chat_history_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_fts_messages_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_fts_knowledge_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_fts'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_fts_diary_exists(self, db):
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='diary_fts'"
        )
        row = await cursor.fetchone()
        assert row is not None

    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        a = Database()
        b = Database()
        assert a is b

    @pytest.mark.asyncio
    async def test_close_sets_connection_none(self, db):
        await db.close()
        assert db.connection is None

    @pytest.mark.asyncio
    async def test_close_when_already_closed(self):
        d = Database()
        # _db is None before connect; close should not raise
        await d.close()
        assert d.connection is None


# ===========================================================================
# DAO
# ===========================================================================

class TestDAOChatMessages:
    @pytest.mark.asyncio
    async def test_insert_and_get_message(self, dao, db):
        msg = ChatMessage(platform="wechat", sender="Alice", content="Hello world")
        row_id = await dao.insert_message(msg)
        assert row_id is not None
        assert row_id >= 1

        messages = await dao.get_messages(platform="wechat")
        assert len(messages) == 1
        assert messages[0]["sender"] == "Alice"
        assert messages[0]["content"] == "Hello world"
        assert messages[0]["platform"] == "wechat"

    @pytest.mark.asyncio
    async def test_get_messages_all_platforms(self, dao, db):
        await dao.insert_message(ChatMessage(platform="wechat", sender="A", content="msg1"))
        await dao.insert_message(ChatMessage(platform="qq", sender="B", content="msg2"))

        all_msgs = await dao.get_messages()
        assert len(all_msgs) == 2

    @pytest.mark.asyncio
    async def test_get_messages_platform_filter(self, dao, db):
        await dao.insert_message(ChatMessage(platform="wechat", sender="A", content="msg1"))
        await dao.insert_message(ChatMessage(platform="qq", sender="B", content="msg2"))
        await dao.insert_message(ChatMessage(platform="wechat", sender="C", content="msg3"))

        wechat_msgs = await dao.get_messages(platform="wechat")
        assert len(wechat_msgs) == 2

    @pytest.mark.asyncio
    async def test_get_messages_limit(self, dao, db):
        for i in range(10):
            await dao.insert_message(ChatMessage(platform="wechat", sender="A", content=f"msg{i}"))

        limited = await dao.get_messages(limit=3)
        assert len(limited) == 3

    @pytest.mark.asyncio
    async def test_insert_message_with_optional_fields(self, dao, db):
        msg = ChatMessage(
            platform="qq",
            sender="Bob",
            content="pic",
            group_name="Friends",
            msg_type="image",
            raw_data='{"url":"http://img.test"}',
        )
        row_id = await dao.insert_message(msg)
        messages = await dao.get_messages()
        assert len(messages) == 1
        assert messages[0]["group_name"] == "Friends"
        assert messages[0]["msg_type"] == "image"

    @pytest.mark.asyncio
    async def test_search_messages_via_fts(self, dao, db):
        """insert_message keeps messages_fts in sync, so search works directly."""
        msg = ChatMessage(platform="wechat", sender="Alice", content="Python is great")
        await dao.insert_message(msg)

        results = await dao.search_messages("Python")
        assert len(results) == 1
        assert results[0]["content"] == "Python is great"

    @pytest.mark.asyncio
    async def test_search_messages_no_match(self, dao, db):
        msg = ChatMessage(platform="wechat", sender="Alice", content="Hello")
        await dao.insert_message(msg)

        results = await dao.search_messages("nonexistent")
        assert len(results) == 0


class TestDAODiary:
    @pytest.mark.asyncio
    async def test_insert_and_get_diary(self, dao, db):
        entry = DiaryEntry(content="Today I coded", tags=["coding"], mood="productive")
        row_id = await dao.insert_diary(entry)
        assert row_id >= 1

        diaries = await dao.get_diaries()
        assert len(diaries) == 1
        assert diaries[0]["content"] == "Today I coded"
        assert diaries[0]["mood"] == "productive"
        # tags stored as JSON string
        tags = json.loads(diaries[0]["tags"])
        assert tags == ["coding"]

    @pytest.mark.asyncio
    async def test_get_diaries_limit(self, dao, db):
        for i in range(5):
            await dao.insert_diary(DiaryEntry(content=f"Day {i}"))

        limited = await dao.get_diaries(limit=2)
        assert len(limited) == 2

    @pytest.mark.asyncio
    async def test_search_diaries_via_fts(self, dao, db):
        entry = DiaryEntry(content="Machine learning is fascinating")
        await dao.insert_diary(entry)

        results = await dao.search_diaries("machine")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_diaries_no_match(self, dao, db):
        entry = DiaryEntry(content="Rainy day")
        await dao.insert_diary(entry)

        results = await dao.search_diaries("sunny")
        assert len(results) == 0


class TestDAOKnowledge:
    @pytest.mark.asyncio
    async def test_insert_and_get_knowledge(self, dao, db):
        item = KnowledgeItem(
            title="Python Tips",
            content="Use list comprehensions",
            source_url="https://docs.python.org",
            source_type="url",
            category="programming",
            tags=["python", "tips"],
        )
        row_id = await dao.insert_knowledge(item)
        assert row_id >= 1

        items = await dao.get_knowledge()
        assert len(items) == 1
        assert items[0]["title"] == "Python Tips"
        assert items[0]["source_type"] == "url"
        tags = json.loads(items[0]["tags"])
        assert tags == ["python", "tips"]

    @pytest.mark.asyncio
    async def test_get_knowledge_limit(self, dao, db):
        for i in range(8):
            await dao.insert_knowledge(KnowledgeItem(title=f"Item {i}", content=f"Content {i}"))

        limited = await dao.get_knowledge(limit=5)
        assert len(limited) == 5

    @pytest.mark.asyncio
    async def test_search_knowledge_via_fts(self, dao, db):
        item = KnowledgeItem(title="Rust Book", content="Ownership and borrowing")
        await dao.insert_knowledge(item)

        results = await dao.search_knowledge("ownership")
        assert len(results) == 1
        assert results[0]["title"] == "Rust Book"

    @pytest.mark.asyncio
    async def test_search_knowledge_no_match(self, dao, db):
        item = KnowledgeItem(title="Cooking", content="Pasta recipe")
        await dao.insert_knowledge(item)

        results = await dao.search_knowledge("quantum physics")
        assert len(results) == 0
