from __future__ import annotations


class TextChunker:
    """Token-aware text chunking for large documents."""

    def __init__(self, chunk_size: int = 3000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Approximate token count (1 token ≈ 4 chars for English, ~2 chars for Chinese)
        approx_tokens = len(text) // 3
        if approx_tokens <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size * 3  # Convert tokens to chars approx
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                for sep in ["\n\n", "\n", "。", ".", "！", "!", "？", "?"]:
                    last = chunk.rfind(sep)
                    if last > len(chunk) * 0.5:
                        chunk = chunk[: last + len(sep)]
                        end = start + len(chunk)
                        break

            chunks.append(chunk.strip())
            start = end - self.overlap * 3

        return [c for c in chunks if c]


class SemanticChunker:
    """Chinese-aware, token-approximate chunker for the vector knowledge base.

    Unlike :class:`TextChunker` (which assumes ~1 token per 3 chars, tuned for
    English), this estimates CJK text as roughly one token per character, so the
    configured ``chunk_tokens`` maps to a realistic embedding window. For
    bge-small-zh-v1.5 (512-token limit) the recommended range is 300-500.
    """

    # Sentence / paragraph separators, longest-first so boundaries prefer them.
    DEFAULT_SEPARATORS = (
        "\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ",
    )

    def __init__(self, chunk_tokens: int = 400, overlap_tokens: int = 60):
        self.chunk_tokens = max(32, int(chunk_tokens))
        self.overlap_tokens = max(0, int(overlap_tokens))

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Approximate token count: CJK ≈ 1/char, other ≈ 1/4 chars."""
        if not text:
            return 0
        cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
        other = len(text) - cjk
        return int(cjk + other / 4) + 1

    def chunk(self, text: str) -> list[str]:
        text = (text or "").strip()
        if not text:
            return []
        if self.estimate_tokens(text) <= self.chunk_tokens:
            return [text]

        chunks: list[str] = []
        n = len(text)
        start = 0
        while start < n:
            # CJK is ~1 char/token, so the token budget doubles as a char budget.
            end = min(n, start + self.chunk_tokens)
            if end < n:
                window = text[start:end]
                best_idx = -1
                best_len = 0
                for sep in self.DEFAULT_SEPARATORS:
                    idx = window.rfind(sep)
                    if idx > best_idx:
                        best_idx = idx
                        best_len = len(sep)
                # Only honor a separator if it appears past the first 40%.
                if best_idx > len(window) * 0.4:
                    end = start + best_idx + best_len
            piece = text[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= n:
                break
            start = max(end - self.overlap_tokens, start + 1)
        return chunks
