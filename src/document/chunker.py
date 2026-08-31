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
