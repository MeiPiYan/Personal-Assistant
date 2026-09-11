from __future__ import annotations

import asyncio
import json
from PySide6.QtCore import Qt, Signal, QObject


class AIEngine(QObject):
    """Unified AI engine supporting multiple providers via aiohttp."""

    response_token = Signal(str)
    response_done = Signal(str)
    error = Signal(str)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self._config = config
        self._default_model = "deepseek/deepseek-chat"
        self._provider = None

        if config:
            provider = config.get("ai.default_provider", "deepseek")
            model = config.get("ai.default_model", "deepseek-chat")
            self._default_model = f"{provider}/{model}"

    def set_model(self, model: str) -> None:
        self._default_model = model

    def _get_model_config(self, model: str | None = None) -> dict:
        """Get API config for the given model."""
        m = model or self._default_model

        # Parse provider/model
        if "/" in m:
            provider, model_name = m.split("/", 1)
        else:
            provider = self._config.get("ai.default_provider", "deepseek") if self._config else "deepseek"
            model_name = m

        config = {
            "provider": provider,
            "model": model_name,
            "api_key": "",
            "base_url": "",
        }

        if not self._config:
            return config

        # Get provider-specific config
        if provider == "openai":
            config["api_key"] = self._config.get("ai.providers.openai.api_key", "")
            base_url = self._config.get("ai.providers.openai.base_url")
            config["base_url"] = base_url or "https://api.openai.com/v1"
        elif provider == "deepseek":
            config["api_key"] = self._config.get("ai.providers.deepseek.api_key", "")
            config["base_url"] = "https://api.deepseek.com/v1"
        elif provider == "siliconflow":
            config["api_key"] = self._config.get("ai.providers.siliconflow.api_key", "")
            config["base_url"] = "https://api.siliconflow.cn/v1"
        elif provider == "anthropic":
            config["api_key"] = self._config.get("ai.providers.anthropic.api_key", "")
            config["base_url"] = "https://api.anthropic.com"
        elif provider == "gemini":
            config["api_key"] = self._config.get("ai.providers.gemini.api_key", "")
            config["base_url"] = "https://generativelanguage.googleapis.com"
        elif provider == "groq":
            config["api_key"] = self._config.get("ai.providers.groq.api_key", "")
            config["base_url"] = "https://api.groq.com/openai/v1"
        elif provider == "ollama":
            base_url = self._config.get("ai.providers.ollama.base_url", "http://localhost:11434")
            config["base_url"] = f"{base_url}/v1"
            config["api_key"] = "not-needed"
        elif provider == "custom":
            config["base_url"] = self._config.get("ai.providers.custom.base_url", "")
            config["api_key"] = self._config.get("ai.providers.custom.api_key", "")

        return config

    # ── Provider-specific request builders ───────────────────────────

    @staticmethod
    def _is_native_provider(provider: str) -> bool:
        """Anthropic and Gemini use non-OpenAI APIs."""
        return provider in ("anthropic", "gemini")

    @staticmethod
    def _build_anthropic_headers(api_key: str) -> dict:
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_anthropic_payload(
        messages: list[dict], model: str, max_tokens: int, temperature: float, stream: bool
    ) -> dict:
        """Build Anthropic Messages API payload. System message is extracted separately."""
        system_text = ""
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
            "stream": stream,
        }
        if system_text:
            payload["system"] = system_text
        return payload

    @staticmethod
    def _build_gemini_headers(api_key: str) -> dict:
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

    @staticmethod
    def _build_gemini_url(base_url: str, model: str, stream: bool) -> str:
        action = "streamGenerateContent?alt=sse" if stream else "generateContent"
        return f"{base_url}/v1beta/models/{model}:{action}"

    @staticmethod
    def _build_gemini_payload(
        messages: list[dict], temperature: float
    ) -> dict:
        """Build Gemini generateContent payload."""
        contents = []
        system_text = ""

        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}],
                })

        payload: dict = {"contents": contents, "generationConfig": {"temperature": temperature}}
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        return payload

    # ── Provider-specific response parsers ───────────────────────────

    @staticmethod
    def _parse_anthropic_response(result: dict) -> str:
        """Extract text from Anthropic Messages API response."""
        content_blocks = result.get("content", [])
        return "".join(block.get("text", "") for block in content_blocks if block.get("type") == "text")

    @staticmethod
    def _parse_gemini_response(result: dict) -> str:
        """Extract text from Gemini generateContent response."""
        candidates = result.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts)

    # ── Streaming helpers ────────────────────────────────────────────

    async def _read_anthropic_stream(self, resp) -> str:
        """Read Anthropic SSE stream, emitting tokens as they arrive. Returns full text."""
        full = ""
        async for line in resp.content:
            line_str = line.decode("utf-8").strip()
            if not line_str or not line_str.startswith("data:"):
                continue
            data_str = line_str[5:].strip()
            if not data_str:
                continue
            try:
                event = json.loads(data_str)
                if event.get("type") == "content_block_delta":
                    text = event.get("delta", {}).get("text", "")
                    if text:
                        full += text
                        self.response_token.emit(text)
            except json.JSONDecodeError:
                continue
        return full

    async def _read_gemini_stream(self, resp) -> str:
        """Read Gemini SSE stream (alt=sse format), emitting tokens as they arrive."""
        full = ""
        async for line in resp.content:
            line_str = line.decode("utf-8").strip()
            if not line_str or not line_str.startswith("data:"):
                continue
            data_str = line_str[5:].strip()
            if not data_str:
                continue
            try:
                event = json.loads(data_str)
                candidates = event.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        text = part.get("text", "")
                        if text:
                            full += text
                            self.response_token.emit(text)
            except json.JSONDecodeError:
                continue
        return full

    # ── Main API methods ─────────────────────────────────────────────

    async def chat_stream(self, messages: list[dict], model: str | None = None) -> None:
        import aiohttp

        cfg = self._get_model_config(model)
        provider = cfg["provider"]
        max_tokens = 4096
        temperature = 0.7
        if self._config:
            max_tokens = self._config.get("ai.max_tokens", 4096)
            temperature = self._config.get("ai.temperature", 0.7)

        try:
            if provider == "anthropic":
                api_url = f"{cfg['base_url']}/v1/messages"
                headers = self._build_anthropic_headers(cfg["api_key"])
                payload = self._build_anthropic_payload(
                    messages, cfg["model"], max_tokens, temperature, stream=True
                )
            elif provider == "gemini":
                api_url = self._build_gemini_url(cfg["base_url"], cfg["model"], stream=True)
                headers = self._build_gemini_headers(cfg["api_key"])
                payload = self._build_gemini_payload(messages, temperature)
            else:
                # OpenAI-compatible providers
                api_url = f"{cfg['base_url']}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": cfg["model"],
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.error.emit(f"API 错误 ({resp.status}): {error_text}")
                        self.response_done.emit(f"[错误: API 返回 {resp.status}]")
                        return

                    if provider == "anthropic":
                        full = await self._read_anthropic_stream(resp)
                    elif provider == "gemini":
                        full = await self._read_gemini_stream(resp)
                    else:
                        full = await self._read_openai_stream(resp)

                    self.response_done.emit(full)

        except aiohttp.ClientError as e:
            self.error.emit(f"网络错误: {e}")
            self.response_done.emit(f"[网络错误: {e}]")
        except asyncio.TimeoutError:
            self.error.emit("请求超时 (120s)")
            self.response_done.emit("[错误: 请求超时]")
        except Exception as e:
            self.error.emit(str(e))
            self.response_done.emit(f"[错误: {e}]")

    async def _read_openai_stream(self, resp) -> str:
        """Read OpenAI-compatible SSE stream, emitting tokens as they arrive."""
        full = ""
        async for line in resp.content:
            line_str = line.decode("utf-8").strip()
            if not line_str or not line_str.startswith("data:"):
                continue
            data_str = line_str[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        full += content
                        self.response_token.emit(content)
            except json.JSONDecodeError:
                continue
        return full

    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        import aiohttp

        cfg = self._get_model_config(model)
        provider = cfg["provider"]
        max_tokens = 4096
        temperature = 0.7
        if self._config:
            max_tokens = self._config.get("ai.max_tokens", 4096)
            temperature = self._config.get("ai.temperature", 0.7)

        try:
            if provider == "anthropic":
                api_url = f"{cfg['base_url']}/v1/messages"
                headers = self._build_anthropic_headers(cfg["api_key"])
                payload = self._build_anthropic_payload(
                    messages, cfg["model"], max_tokens, temperature, stream=False
                )
            elif provider == "gemini":
                api_url = self._build_gemini_url(cfg["base_url"], cfg["model"], stream=False)
                headers = self._build_gemini_headers(cfg["api_key"])
                payload = self._build_gemini_payload(messages, temperature)
            else:
                api_url = f"{cfg['base_url']}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": cfg["model"],
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False,
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise RuntimeError(f"API 返回 {resp.status}: {error_text}")

                    result = await resp.json()

                    if provider == "anthropic":
                        return self._parse_anthropic_response(result)
                    elif provider == "gemini":
                        return self._parse_gemini_response(result)
                    else:
                        return result["choices"][0]["message"]["content"]

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络错误: {e}") from e
        except asyncio.TimeoutError as e:
            raise RuntimeError("请求超时 (120s)") from e
