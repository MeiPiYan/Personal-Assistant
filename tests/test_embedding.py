"""Tests for the embedding backends (P0 vector knowledge base)."""
import math

import pytest

from src.ai.embedding import (
    HashingEmbeddingBackend,
    LocalSentenceTransformerBackend,
    OllamaEmbeddingBackend,
    OpenAICompatEmbeddingBackend,
    cosine_similarity,
    create_embedding_backend,
    normalize,
)


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def test_normalize_unit_length():
    v = normalize([3.0, 4.0])
    assert abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-9


def test_normalize_zero_vector_unchanged():
    assert normalize([0.0, 0.0]) == [0.0, 0.0]


def test_cosine_similarity_identical():
    v = normalize([1.0, 2.0, 3.0])
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal():
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_similarity_mismatched_length():
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


# --------------------------------------------------------------------------- #
# Hashing (offline default) backend
# --------------------------------------------------------------------------- #
class TestHashingBackend:
    def test_dim(self):
        assert HashingEmbeddingBackend(dim=128).dim == 128

    def test_name(self):
        assert HashingEmbeddingBackend(dim=64).name == "hashing-64"

    @pytest.mark.asyncio
    async def test_embed_shape_and_norm(self):
        backend = HashingEmbeddingBackend(dim=64)
        vecs = await backend.embed(["你好世界", "hello world"])
        assert len(vecs) == 2
        assert all(len(v) == 64 for v in vecs)
        for v in vecs:
            assert abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-6

    @pytest.mark.asyncio
    async def test_deterministic(self):
        backend = HashingEmbeddingBackend(dim=64)
        assert await backend.embed_one("稳定性测试") == await backend.embed_one(
            "稳定性测试"
        )

    @pytest.mark.asyncio
    async def test_similar_text_scores_higher(self):
        backend = HashingEmbeddingBackend(dim=512)
        base = await backend.embed_one("向量检索与知识库")
        near = await backend.embed_one("向量检索与知识库系统")
        far = await backend.embed_one("今天天气很好")
        assert cosine_similarity(base, near) >= cosine_similarity(base, far)

    @pytest.mark.asyncio
    async def test_empty_input(self):
        assert await HashingEmbeddingBackend(dim=32).embed([]) == []


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
class TestFactory:
    def test_default_is_hashing(self):
        backend = create_embedding_backend({})
        assert isinstance(backend, HashingEmbeddingBackend)
        assert backend.dim == 512

    def test_unknown_provider_falls_back(self):
        backend = create_embedding_backend({"provider": "does-not-exist"})
        assert isinstance(backend, HashingEmbeddingBackend)

    def test_local_backend_is_lazy(self):
        backend = create_embedding_backend({"provider": "local", "dim": 512})
        assert isinstance(backend, LocalSentenceTransformerBackend)
        assert backend.dim == 512

    def test_ollama_backend(self):
        backend = create_embedding_backend({"provider": "ollama", "dim": 1024})
        assert isinstance(backend, OllamaEmbeddingBackend)
        assert backend.dim == 1024

    def test_openai_compat_backend(self):
        backend = create_embedding_backend(
            {"provider": "siliconflow", "model": "BAAI/bge-m3", "dim": 1024}
        )
        assert isinstance(backend, OpenAICompatEmbeddingBackend)
        assert backend.dim == 1024
