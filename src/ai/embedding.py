"""Embedding backends for the vector knowledge base (P0).

This module provides a small, dependency-light abstraction over text embedding
providers. It is intentionally tolerant: when no ML runtime or network is
available it falls back to a deterministic, pure-python feature-hashing
embedding so the rest of the system (indexing + retrieval) still works.

Design goals (P0):
- No hard dependency on torch / sentence-transformers at import time (lazy).
- Offline-friendly default so tests and degraded environments keep working.
- A single ``create_embedding_backend`` factory driven by a plain dict config.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
from abc import ABC, abstractmethod


def normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector. Returns the input unchanged if norm is 0."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two (possibly un-normalized) vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


class EmbeddingBackend(ABC):
    """Abstract text embedding backend."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Vector dimension produced by this backend."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend/model identifier."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning one vector per input text."""

    async def embed_one(self, text: str) -> list[float]:
        vecs = await self.embed([text])
        return vecs[0] if vecs else []


class HashingEmbeddingBackend(EmbeddingBackend):
    """Deterministic, dependency-free feature-hashing embedding.

    Uses word tokens plus character n-grams (CJK-friendly) hashed into a fixed
    dimensionality with a signed hash trick, then L2-normalized. This is not a
    semantic model, but it gives a stable, offline, zero-install representation
    so indexing/retrieval wiring can be developed and tested end-to-end. It is
    also the automatic fallback when no real embedding model is configured.
    """

    def __init__(self, dim: int = 512, ngram: int = 2):
        self._dim = max(8, int(dim))
        self._ngram = max(1, int(ngram))
        self._name = f"hashing-{self._dim}"

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return self._name

    def _tokens(self, text: str) -> list[str]:
        text = (text or "").lower()
        tokens: list[str] = []
        for word in text.split():
            tokens.append(word)
        compact = "".join(text.split())
        n = self._ngram
        for i in range(len(compact) - n + 1):
            tokens.append(compact[i : i + n])
        return tokens

    def _embed_sync(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for tok in self._tokens(text):
            digest = hashlib.md5(tok.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if (digest[4] & 1) else -1.0
            vec[idx] += sign
        return normalize(vec)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_sync(t) for t in texts]


class LocalSentenceTransformerBackend(EmbeddingBackend):
    """Local embedding model via ``sentence-transformers`` (lazy import).

    Recommended default model for Chinese personal-assistant use is
    ``BAAI/bge-small-zh-v1.5`` (512-dim, ~100MB, CPU-friendly). Inference runs
    in a thread pool so it never blocks the qasync event loop.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        dim: int = 512,
        device: str | None = None,
    ):
        self._model_name = model_name
        self._dim = int(dim)
        self._device = device
        self._model = None  # lazy

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"local:{self._model_name}"

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy

            self._model = SentenceTransformer(self._model_name, device=self._device)
        return self._model

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        embeddings = model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        )
        return [list(map(float, row)) for row in embeddings]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # CPU-bound: offload to a worker thread to keep the UI loop responsive.
        return await asyncio.to_thread(self._embed_sync, texts)


class OpenAICompatEmbeddingBackend(EmbeddingBackend):
    """OpenAI-compatible ``/embeddings`` endpoint (SiliconFlow, etc.)."""

    def __init__(
        self,
        base_url: str = "https://api.siliconflow.cn/v1",
        api_key: str = "",
        model: str = "BAAI/bge-m3",
        dim: int = 1024,
        timeout: int = 30,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._dim = int(dim)
        self._timeout = timeout

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"openai-compat:{self._model}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        import aiohttp  # lazy

        url = f"{self._base_url}/embeddings"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {"model": self._model, "input": texts}
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise RuntimeError(f"embedding API error {resp.status}: {data}")
        items = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
        return [normalize(list(map(float, it["embedding"]))) for it in items]


class OllamaEmbeddingBackend(EmbeddingBackend):
    """Local embeddings via an Ollama server (``/api/embed``)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "bge-m3",
        dim: int = 1024,
        timeout: int = 60,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dim = int(dim)
        self._timeout = timeout

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"ollama:{self._model}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        import aiohttp  # lazy

        url = f"{self._base_url}/api/embed"
        payload = {"model": self._model, "input": texts}
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise RuntimeError(f"ollama embed error {resp.status}: {data}")
        embeddings = data.get("embeddings")
        if embeddings is None:
            raise RuntimeError(f"unexpected ollama response: {data}")
        return [normalize(list(map(float, vec))) for vec in embeddings]


def create_embedding_backend(cfg: dict | None = None) -> EmbeddingBackend:
    """Build an embedding backend from a plain config dict.

    Recognized keys: ``provider``, ``model``, ``dim``, ``base_url``, ``api_key``,
    ``device``. Unknown/missing providers fall back to the offline hashing
    backend so the system never hard-fails on configuration.
    """
    cfg = cfg or {}
    provider = str(cfg.get("provider") or "hashing").lower()
    model = cfg.get("model")
    dim = int(cfg.get("dim") or 512)

    if provider in ("hashing", "hash", "builtin", "none", ""):
        return HashingEmbeddingBackend(dim=dim)
    if provider in ("local", "sentence-transformers", "sentence_transformers", "st", "bge"):
        return LocalSentenceTransformerBackend(
            model_name=model or "BAAI/bge-small-zh-v1.5",
            dim=dim,
            device=cfg.get("device"),
        )
    if provider == "ollama":
        return OllamaEmbeddingBackend(
            base_url=cfg.get("base_url") or "http://localhost:11434",
            model=model or "bge-m3",
            dim=dim,
        )
    if provider in ("openai", "siliconflow", "openai-compatible", "openai_compatible"):
        return OpenAICompatEmbeddingBackend(
            base_url=cfg.get("base_url") or "https://api.siliconflow.cn/v1",
            api_key=cfg.get("api_key") or "",
            model=model or "BAAI/bge-m3",
            dim=dim,
        )
    # Unknown provider: degrade gracefully rather than crash.
    return HashingEmbeddingBackend(dim=dim)
