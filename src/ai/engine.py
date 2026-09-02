from __future__ import annotations

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
            config["base_url"] = "https://api.anthropic.com/v1"
        elif provider == "gemini":
            config["api_key"] = self._config.get("ai.providers.gemini.api_key", "")
            config["base_url"] = "https://generativelanguage.googleapis.com/v1beta"
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

    async def chat_stream(self, messages: list[dict], model: str | None = None) -> None:
        import aiohttp

        cfg = self._get_model_config(model)
        api_url = f"{cfg['base_url']}/chat/completions"

        max_tokens = 4096
        temperature = 0.7
        if self._config:
            max_tokens = self._config.get("ai.max_tokens", 4096)
            temperature = self._config.get("ai.temperature", 0.7)

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

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.error.emit(f"API 错误 ({resp.status}): {error_text}")
                        self.response_done.emit(f"[错误: API 返回 {resp.status}]")
                        return

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

                    self.response_done.emit(full)

        except aiohttp.ClientError as e:
            self.error.emit(f"网络错误: {e}")
            self.response_done.emit(f"[网络错误: {e}]")
        except Exception as e:
            self.error.emit(str(e))
            self.response_done.emit(f"[错误: {e}]")

    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        import aiohttp

        cfg = self._get_model_config(model)
        api_url = f"{cfg['base_url']}/chat/completions"

        max_tokens = 4096
        temperature = 0.7
        if self._config:
            max_tokens = self._config.get("ai.max_tokens", 4096)
            temperature = self._config.get("ai.temperature", 0.7)

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
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
