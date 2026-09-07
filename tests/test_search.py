"""Tests for LocalSearcher and WebSearcher."""
import json
from unittest.mock import patch, MagicMock

import pytest

from src.storage.database import Database
from src.search.local_search import LocalSearcher
from src.search.web_search import WebSearcher, SearchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset Database singleton before each test."""
    Database._instance = None
    Database._db = None
    Database._db_path = "data/assistant.db"
    yield
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
def searcher():
    """Provide a LocalSearcher (will use singleton DB after setup)."""
    return LocalSearcher()


# ===========================================================================
# SearchResult dataclass
# ===========================================================================

class TestSearchResult:
    def test_creation(self):
        r = SearchResult(title="T", url="https://x.com", snippet="S")
        assert r.title == "T"
        assert r.url == "https://x.com"
        assert r.snippet == "S"
        assert r.content == ""

    def test_with_content(self):
        r = SearchResult(title="T", url="U", snippet="S", content="full text")
        assert r.content == "full text"


# ===========================================================================
# LocalSearcher
# ===========================================================================

class TestLocalSearcher:
    @pytest.mark.asyncio
    async def test_search_messages_returns_list(self, db, searcher):
        results = await searcher.search_messages("test")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_messages_empty_db(self, db, searcher):
        results = await searcher.search_messages("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_messages_with_data(self, db, searcher):
        """Insert a message into chat_messages AND messages_fts, then search."""
        cursor = await db.connection.execute(
            "INSERT INTO chat_messages (platform, sender, content) VALUES (?, ?, ?)",
            ("wechat", "Alice", "Python is fun"),
        )
        row_id = cursor.lastrowid
        await db.connection.execute(
            "INSERT INTO messages_fts(rowid, content, sender) VALUES (?, ?, ?)",
            (row_id, "Python is fun", "Alice"),
        )
        await db.connection.commit()

        results = await searcher.search_messages("Python")
        assert len(results) == 1
        assert results[0]["content"] == "Python is fun"

    @pytest.mark.asyncio
    async def test_search_messages_no_match(self, db, searcher):
        cursor = await db.connection.execute(
            "INSERT INTO chat_messages (platform, sender, content) VALUES (?, ?, ?)",
            ("wechat", "Bob", "Hello there"),
        )
        row_id = cursor.lastrowid
        await db.connection.execute(
            "INSERT INTO messages_fts(rowid, content, sender) VALUES (?, ?, ?)",
            (row_id, "Hello there", "Bob"),
        )
        await db.connection.commit()

        results = await searcher.search_messages("quantum")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_messages_limit(self, db, searcher):
        for i in range(10):
            cursor = await db.connection.execute(
                "INSERT INTO chat_messages (platform, sender, content) VALUES (?, ?, ?)",
                ("wechat", "User", f"Message {i} about testing"),
            )
            rid = cursor.lastrowid
            await db.connection.execute(
                "INSERT INTO messages_fts(rowid, content, sender) VALUES (?, ?, ?)",
                (rid, f"Message {i} about testing", "User"),
            )
        await db.connection.commit()

        results = await searcher.search_messages("testing", limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_diaries(self, db, searcher):
        cursor = await db.connection.execute(
            "INSERT INTO diary_entries (content, summary, tags) VALUES (?, ?, ?)",
            ("Great day today", "summary", '["happy"]'),
        )
        rid = cursor.lastrowid
        await db.connection.execute(
            "INSERT INTO diary_fts(rowid, content, summary, tags) VALUES (?, ?, ?, ?)",
            (rid, "Great day today", "summary", "happy"),
        )
        await db.connection.commit()

        results = await searcher.search_diaries("Great")
        assert len(results) == 1
        assert results[0]["content"] == "Great day today"

    @pytest.mark.asyncio
    async def test_search_knowledge(self, db, searcher):
        cursor = await db.connection.execute(
            "INSERT INTO knowledge_items (title, content, source_type) VALUES (?, ?, ?)",
            ("AI Notes", "Deep learning overview", "manual"),
        )
        rid = cursor.lastrowid
        await db.connection.execute(
            "INSERT INTO knowledge_fts(rowid, title, content, tags) VALUES (?, ?, ?, ?)",
            (rid, "AI Notes", "Deep learning overview", ""),
        )
        await db.connection.commit()

        results = await searcher.search_knowledge("learning")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_all(self, db, searcher):
        # Insert one message
        cursor = await db.connection.execute(
            "INSERT INTO chat_messages (platform, sender, content) VALUES (?, ?, ?)",
            ("wechat", "A", "Test search_all"),
        )
        rid = cursor.lastrowid
        await db.connection.execute(
            "INSERT INTO messages_fts(rowid, content, sender) VALUES (?, ?, ?)",
            (rid, "Test search_all", "A"),
        )
        await db.connection.commit()

        results = await searcher.search_all("search_all")
        assert "messages" in results
        assert "diaries" in results
        assert "knowledge" in results
        assert len(results["messages"]) == 1
        assert len(results["diaries"]) == 0

    @pytest.mark.asyncio
    async def test_search_handles_exception_gracefully(self, db, searcher):
        """If FTS table is missing or query is bad, return empty list."""
        # Bad FTS query syntax should be caught
        results = await searcher.search_messages("NEAR(invalid)")
        assert isinstance(results, list)


# ===========================================================================
# WebSearcher
# ===========================================================================

class TestWebSearcher:
    def test_init_defaults(self):
        ws = WebSearcher()
        assert ws.max_results == 5
        assert ws.extract_content is True

    def test_init_custom(self):
        ws = WebSearcher(max_results=10, extract_content=False)
        assert ws.max_results == 10
        assert ws.extract_content is False

    @patch("duckduckgo_search.DDGS")
    def test_search_basic(self, mock_ddgs_cls):
        """Test search with mocked DuckDuckGo results."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Snippet 2"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        ws = WebSearcher(max_results=2, extract_content=False)
        results = ws.search("test query")

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example.com/1"
        assert results[0].snippet == "Snippet 1"
        assert results[1].title == "Result 2"

    @patch("duckduckgo_search.DDGS")
    def test_search_empty_results(self, mock_ddgs_cls):
        """Test search returns empty list when DDGS returns nothing."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_cls.return_value = mock_ddgs

        ws = WebSearcher()
        results = ws.search("no results query")
        assert results == []

    @patch("duckduckgo_search.DDGS")
    def test_search_ddgs_exception(self, mock_ddgs_cls):
        """Test search handles DDGS exception gracefully."""
        mock_ddgs_cls.side_effect = Exception("Network error")

        ws = WebSearcher()
        results = ws.search("query")
        assert results == []

    @patch("duckduckgo_search.DDGS")
    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    def test_search_with_content_extraction(self, mock_extract, mock_fetch, mock_ddgs_cls):
        """Test that content extraction is attempted when enabled."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Page", "href": "https://example.com", "body": "snippet"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        mock_fetch.return_value = "<html>content</html>"
        mock_extract.return_value = "Extracted content"

        ws = WebSearcher(extract_content=True)
        results = ws.search("test")

        assert len(results) == 1
        assert results[0].content == "Extracted content"
        mock_fetch.assert_called_once_with("https://example.com")

    @patch("duckduckgo_search.DDGS")
    @patch("trafilatura.fetch_url")
    def test_search_content_extraction_failure(self, mock_fetch, mock_ddgs_cls):
        """Test that content extraction failure doesn't crash the search."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Page", "href": "https://example.com", "body": "snippet"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        mock_fetch.side_effect = Exception("Timeout")

        ws = WebSearcher(extract_content=True)
        results = ws.search("test")

        assert len(results) == 1
        assert results[0].content == ""  # empty due to extraction failure

    @patch("duckduckgo_search.DDGS")
    def test_search_missing_fields(self, mock_ddgs_cls):
        """Test that missing fields in DDGS results are handled."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [{}]  # empty dict
        mock_ddgs_cls.return_value = mock_ddgs

        ws = WebSearcher(extract_content=False)
        results = ws.search("test")

        assert len(results) == 1
        assert results[0].title == ""
        assert results[0].url == ""
        assert results[0].snippet == ""

    @patch("duckduckgo_search.DDGS")
    def test_search_no_content_extraction_when_disabled(self, mock_ddgs_cls):
        """When extract_content=False, content should stay empty."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "T", "href": "https://example.com", "body": "S"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        ws = WebSearcher(extract_content=False)
        results = ws.search("test")
        assert results[0].content == ""

    @pytest.mark.asyncio
    async def test_async_search(self):
        """Test that async_search wraps the sync search correctly."""
        ws = WebSearcher(extract_content=False)
        with patch.object(ws, "search", return_value=[
            SearchResult(title="T", url="U", snippet="S")
        ]) as mock_search:
            results = await ws.async_search("test")
            assert len(results) == 1
            mock_search.assert_called_once_with("test")
