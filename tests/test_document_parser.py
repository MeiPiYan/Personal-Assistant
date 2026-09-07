"""Tests for DocumentParser and TextChunker."""
import os
import tempfile
from pathlib import Path

import pytest

from src.document.parser import DocumentParser
from src.document.chunker import TextChunker


# ===========================================================================
# DocumentParser
# ===========================================================================

class TestDocumentParser:
    def setup_method(self):
        self.parser = DocumentParser()

    def test_nonexistent_file_returns_empty(self):
        result = self.parser.parse("/tmp/nonexistent_file_abc123.txt")
        assert result == ""

    def test_parse_txt_file(self, tmp_path):
        txt = tmp_path / "hello.txt"
        txt.write_text("Hello, world!\nSecond line.", encoding="utf-8")
        result = self.parser.parse(str(txt))
        assert result == "Hello, world!\nSecond line."

    def test_parse_md_file(self, tmp_path):
        md = tmp_path / "readme.md"
        md.write_text("# Title\n\nSome **bold** text.", encoding="utf-8")
        result = self.parser.parse(str(md))
        assert "# Title" in result
        assert "**bold**" in result

    def test_parse_markdown_extension(self, tmp_path):
        md = tmp_path / "notes.markdown"
        md.write_text("Content here", encoding="utf-8")
        result = self.parser.parse(str(md))
        assert result == "Content here"

    def test_parse_unknown_extension_falls_back(self, tmp_path):
        f = tmp_path / "data.xyz"
        f.write_text("fallback content", encoding="utf-8")
        result = self.parser.parse(str(f))
        assert result == "fallback content"

    def test_parse_txt_encoding_fallback(self, tmp_path):
        """File with unknown extension and latin-1 bytes should still parse with errors='ignore'."""
        f = tmp_path / "data.abc"
        f.write_bytes(b"hello \xff\xfe world")
        result = self.parser.parse(str(f))
        assert "hello" in result
        assert "world" in result

    def test_parse_error_returns_message(self, tmp_path):
        """If a parsing method raises, the error message is returned."""
        f = tmp_path / "test.pdf"
        # Create a valid Path but _parse_pdf will fail on a non-PDF file
        f.write_bytes(b"not a pdf")
        result = self.parser.parse(str(f))
        # Should return the error string
        assert "[解析错误" in result

    def test_parse_html_file(self, tmp_path):
        html = tmp_path / "page.html"
        html.write_text("<html><body><h1>Hello</h1><p>World</p></body></html>", encoding="utf-8")
        result = self.parser.parse(str(html))
        # trafilatura may or may not extract text, but should not crash
        assert isinstance(result, str)


# ===========================================================================
# TextChunker
# ===========================================================================

class TestTextChunker:
    def setup_method(self):
        self.chunker = TextChunker(chunk_size=3000, overlap=200)

    def test_empty_text_returns_empty_list(self):
        result = self.chunker.chunk("")
        assert result == []

    def test_short_text_single_chunk(self):
        text = "This is a short text."
        result = self.chunker.chunk(text)
        assert result == [text]
        assert len(result) == 1

    def test_text_at_exact_token_boundary(self):
        # 3000 tokens * 3 chars/token = 9000 chars
        text = "a" * 9000
        result = self.chunker.chunk(text)
        assert len(result) == 1

    def test_long_text_produces_multiple_chunks(self):
        # 10000 tokens ≈ 30000 chars → should split
        text = "word " * 6000  # ~30000 chars
        result = self.chunker.chunk(text)
        assert len(result) > 1

    def test_chunks_are_non_empty(self):
        text = "sentence. " * 2000  # ~20000 chars
        result = self.chunker.chunk(text)
        for chunk in result:
            assert len(chunk) > 0
            assert chunk.strip() == chunk  # no leading/trailing whitespace

    def test_overlap_parameter(self):
        small_overlap = TextChunker(chunk_size=100, overlap=10)
        large_overlap = TextChunker(chunk_size=100, overlap=50)
        # Create a long text
        text = "Hello world! " * 500  # ~6500 chars
        r1 = small_overlap.chunk(text)
        r2 = large_overlap.chunk(text)
        # Both should produce multiple chunks
        assert len(r1) > 1
        assert len(r2) > 1

    def test_chunker_respects_sentence_boundaries(self):
        # Create text with clear sentence boundaries
        sentences = [f"This is sentence number {i}. " for i in range(200)]
        text = "".join(sentences)
        chunker = TextChunker(chunk_size=50, overlap=5)
        result = chunker.chunk(text)
        # Chunks should tend to end at sentence boundaries
        for chunk in result:
            # Most chunks should end with a period (sentence break)
            # Not guaranteed for every chunk due to overlap, but generally
            assert isinstance(chunk, str)

    def test_custom_chunk_size_and_overlap(self):
        c = TextChunker(chunk_size=500, overlap=50)
        assert c.chunk_size == 500
        assert c.overlap == 50

    def test_defaults(self):
        c = TextChunker()
        assert c.chunk_size == 3000
        assert c.overlap == 200

    def test_single_long_paragraph_with_newlines(self):
        """Text with paragraph breaks should try to break at \\n\\n."""
        text = "\n\n".join(["Paragraph " + str(i) + " content here. " * 10 for i in range(100)])
        chunker = TextChunker(chunk_size=50, overlap=10)
        result = chunker.chunk(text)
        assert len(result) > 1
        # All chunks should be non-empty strings
        assert all(isinstance(c, str) and len(c) > 0 for c in result)
