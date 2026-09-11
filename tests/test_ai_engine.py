"""Tests for the AI engine: request builders, response parsers, SSE readers."""
import json
from unittest.mock import MagicMock

import pytest

from src.ai.engine import AIEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _AsyncBytes:
    """Minimal async-iterable stand-in for aiohttp resp.content."""

    def __init__(self, lines: list[bytes]):
        self._lines = lines

    def __aiter__(self):
        self._iter = iter(self._lines)
        return self

    async def __anext__(self) -> bytes:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class FakeResp:
    def __init__(self, lines: list[bytes]):
        self.content = _AsyncBytes(lines)


def make_config(mapping: dict) -> MagicMock:
    """Config stand-in whose .get() reads from a flat-key dict."""
    cfg = MagicMock()
    cfg.get = lambda key, default=None: mapping.get(key, default)
    return cfg


@pytest.fixture
def engine() -> AIEngine:
    return AIEngine(config=None)


@pytest.fixture
def tokens() -> list[str]:
    collected = []
    e = AIEngine(config=None)
    e.response_token.connect(collected.append)
    e._tokens = collected
    return e


# ===========================================================================
# Config routing
# ===========================================================================

class TestGetModelConfig:
    def test_no_config_returns_defaults(self, engine):
        cfg = engine._get_model_config("deepseek/deepseek-chat")
        assert cfg["provider"] == "deepseek"
        assert cfg["model"] == "deepseek-chat"
        assert cfg["api_key"] == ""

    def test_model_without_provider_uses_default(self):
        engine = AIEngine(config=make_config({"ai.default_provider": "groq"}))
        cfg = engine._get_model_config("llama-3")
        assert cfg["provider"] == "groq"
        assert cfg["model"] == "llama-3"

    def test_deepseek_key_routing(self):
        engine = AIEngine(config=make_config({
            "ai.default_provider": "deepseek",
            "ai.providers.deepseek.api_key": "sk-test",
        }))
        cfg = engine._get_model_config("deepseek/deepseek-chat")
        assert cfg["api_key"] == "sk-test"
        assert cfg["base_url"] == "https://api.deepseek.com/v1"

    def test_anthropic_base_url(self):
        engine = AIEngine(config=make_config({
            "ai.providers.anthropic.api_key": "ak-test",
        }))
        cfg = engine._get_model_config("anthropic/claude-3")
        assert cfg["base_url"] == "https://api.anthropic.com"

    def test_ollama_needs_no_key(self):
        engine = AIEngine(config=make_config({
            "ai.providers.ollama.base_url": "http://localhost:11434",
        }))
        cfg = engine._get_model_config("ollama/llama3.1")
        assert cfg["api_key"] == "not-needed"
        assert cfg["base_url"] == "http://localhost:11434/v1"

    def test_default_model_from_config(self):
        engine = AIEngine(config=make_config({
            "ai.default_provider": "openai",
            "ai.default_model": "gpt-4o",
        }))
        assert engine._default_model == "openai/gpt-4o"


# ===========================================================================
# Request builders
# ===========================================================================

class TestAnthropicBuilder:
    def test_system_message_extracted(self):
        payload = AIEngine._build_anthropic_payload(
            [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello"},
            ],
            "claude-3", 1024, 0.5, stream=False,
        )
        assert payload["system"] == "You are helpful."
        assert payload["messages"] == [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        assert payload["model"] == "claude-3"
        assert payload["max_tokens"] == 1024
        assert payload["temperature"] == 0.5
        assert payload["stream"] is False

    def test_headers_carry_key(self):
        headers = AIEngine._build_anthropic_headers("ak-test")
        assert headers["x-api-key"] == "ak-test"
        assert "anthropic-version" in headers

    def test_no_system_key_when_absent(self):
        payload = AIEngine._build_anthropic_payload(
            [{"role": "user", "content": "Hi"}], "m", 10, 0.7, stream=False
        )
        assert "system" not in payload


class TestGeminiBuilder:
    def test_url_has_no_key(self):
        url = AIEngine._build_gemini_url("https://generativelanguage.googleapis.com",
                                         "gemini-pro", stream=False)
        assert "key=" not in url
        assert url.endswith(":generateContent")

    def test_stream_url_uses_sse(self):
        url = AIEngine._build_gemini_url("https://x.com", "gemini-pro", stream=True)
        assert "streamGenerateContent?alt=sse" in url

    def test_key_in_header_not_url(self):
        headers = AIEngine._build_gemini_headers("gk-secret")
        assert headers["x-goog-api-key"] == "gk-secret"

    def test_payload_roles_and_system(self):
        payload = AIEngine._build_gemini_payload(
            [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello"},
            ],
            temperature=0.3,
        )
        assert payload["systemInstruction"] == {"parts": [{"text": "Be brief."}]}
        assert payload["contents"][0] == {"role": "user", "parts": [{"text": "Hi"}]}
        assert payload["contents"][1]["role"] == "model"
        assert payload["generationConfig"] == {"temperature": 0.3}


# ===========================================================================
# Response parsers
# ===========================================================================

class TestResponseParsers:
    def test_parse_anthropic(self):
        result = {"content": [
            {"type": "text", "text": "Hello "},
            {"type": "tool_use", "id": "t1"},
            {"type": "text", "text": "world"},
        ]}
        assert AIEngine._parse_anthropic_response(result) == "Hello world"

    def test_parse_gemini(self):
        result = {"candidates": [
            {"content": {"parts": [{"text": "Hi"}, {"text": " there"}]}}
        ]}
        assert AIEngine._parse_gemini_response(result) == "Hi there"

    def test_parse_gemini_empty_candidates(self):
        assert AIEngine._parse_gemini_response({"candidates": []}) == ""


# ===========================================================================
# SSE stream readers
# ===========================================================================

class TestStreamReaders:
    @pytest.mark.asyncio
    async def test_openai_stream_emits_tokens(self, tokens):
        lines = [
            b'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n',
            b"data: [DONE]\n\n",
        ]
        full = await tokens._read_openai_stream(FakeResp(lines))
        assert full == "Hello"
        assert tokens._tokens == ["Hel", "lo"]

    @pytest.mark.asyncio
    async def test_anthropic_stream_emits_tokens(self, tokens):
        events = [
            {"type": "content_block_delta", "delta": {"text": "你"}},
            {"type": "content_block_delta", "delta": {"text": "好"}},
            {"type": "message_stop"},
        ]
        lines = [f"data: {json.dumps(e)}\n\n".encode("utf-8") for e in events]
        full = await tokens._read_anthropic_stream(FakeResp(lines))
        assert full == "你好"
        assert tokens._tokens == ["你", "好"]

    @pytest.mark.asyncio
    async def test_gemini_stream_emits_tokens(self, tokens):
        events = [
            {"candidates": [{"content": {"parts": [{"text": "早上"}]}}]},
            {"candidates": [{"content": {"parts": [{"text": "好"}]}}]},
        ]
        lines = [f"data: {json.dumps(e)}\n\n".encode("utf-8") for e in events]
        full = await tokens._read_gemini_stream(FakeResp(lines))
        assert full == "早上好"
        assert tokens._tokens == ["早上", "好"]

    @pytest.mark.asyncio
    async def test_malformed_lines_skipped(self, tokens):
        lines = [
            b"data: not-json\n\n",
            b"\n",
            b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\n',
        ]
        full = await tokens._read_openai_stream(FakeResp(lines))
        assert full == "ok"
