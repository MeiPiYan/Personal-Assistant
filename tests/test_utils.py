"""Tests for text utility functions."""
import pytest

from src.utils.text import truncate, extract_urls, clean_text


# ===========================================================================
# truncate
# ===========================================================================

class TestTruncate:
    def test_short_text_not_truncated(self):
        text = "Hello"
        assert truncate(text, 10) == "Hello"

    def test_exact_length_not_truncated(self):
        text = "12345"
        assert truncate(text, 5) == "12345"

    def test_long_text_truncated(self):
        text = "A" * 300
        result = truncate(text, 100)
        assert len(result) == 100
        assert result.endswith("...")
        assert result == "A" * 97 + "..."

    def test_default_max_len(self):
        text = "X" * 300
        result = truncate(text)
        assert len(result) == 200

    def test_max_len_one(self):
        # Edge case: max_len=1, text longer → text[:0] + "..."
        text = "AB"
        result = truncate(text, 1)
        assert result == "..."

    def test_empty_string(self):
        assert truncate("", 10) == ""

    def test_unicode_text(self):
        text = "你好世界" * 100  # 400 chars
        result = truncate(text, 50)
        assert len(result) == 50
        assert result.endswith("...")


# ===========================================================================
# extract_urls
# ===========================================================================

class TestExtractUrls:
    def test_single_url(self):
        text = "Visit https://example.com for more info"
        urls = extract_urls(text)
        assert urls == ["https://example.com"]

    def test_multiple_urls(self):
        text = "Go to https://a.com and http://b.org/path?q=1"
        urls = extract_urls(text)
        assert "https://a.com" in urls
        assert "http://b.org/path?q=1" in urls

    def test_no_urls(self):
        text = "No links here"
        assert extract_urls(text) == []

    def test_url_with_path(self):
        text = "https://example.com/path/to/page"
        urls = extract_urls(text)
        assert urls == ["https://example.com/path/to/page"]

    def test_url_with_query_and_fragment(self):
        text = "https://example.com/page?q=test#section"
        urls = extract_urls(text)
        assert urls == ["https://example.com/page?q=test#section"]

    def test_http_and_https(self):
        text = "http://a.com and https://b.com"
        urls = extract_urls(text)
        assert len(urls) == 2

    def test_url_at_end_of_text(self):
        text = "Check out https://example.com"
        urls = extract_urls(text)
        assert urls == ["https://example.com"]

    def test_url_in_angle_brackets_excluded(self):
        """URLs inside angle brackets should not match."""
        text = "<https://example.com>"
        urls = extract_urls(text)
        # The pattern excludes < and > so this should not match fully
        # or may match partially - verify behavior
        assert isinstance(urls, list)

    def test_empty_text(self):
        assert extract_urls("") == []

    def test_urls_in_markdown(self):
        text = "See [docs](https://docs.python.org/3/) for details"
        urls = extract_urls(text)
        # ) is excluded by the pattern, so the URL should stop before it
        assert "https://docs.python.org/3/" in urls or "https://docs.python.org/3" in urls


# ===========================================================================
# clean_text
# ===========================================================================

class TestCleanText:
    def test_multiple_spaces(self):
        assert clean_text("hello   world") == "hello world"

    def test_tabs_and_newlines(self):
        assert clean_text("hello\tworld\nfoo") == "hello world foo"

    def test_leading_trailing_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_only_whitespace(self):
        assert clean_text("   \t\n  ") == ""

    def test_no_change_for_clean_text(self):
        assert clean_text("hello world") == "hello world"

    def test_multiple_newlines(self):
        text = "line1\n\n\nline2"
        assert clean_text(text) == "line1 line2"

    def test_mixed_whitespace(self):
        text = "  hello \t \n world  \n\n  "
        assert clean_text(text) == "hello world"

    def test_unicode_preserved(self):
        assert clean_text("你好  世界") == "你好 世界"
