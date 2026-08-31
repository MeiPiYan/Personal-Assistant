from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QObject


class AIEngine(QObject):
    """Unified AI engine supporting multiple providers via LiteLLM."""

    response_token = Signal(str)
    response_done = Signal(str)
    error = Signal(str)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self._config = config
        self._default_model = "openai/gpt-4o"
        self._provider = None

        if config:
            self._default_model = config.get("ai.default_model", "openai/gpt-4o")

    def set_model(self, model: str) -> None:
        self._default_model = model

    def _get_model_string(self, model: str | None = None) -> str:
        m = model or self._default_model
        if "/" not in m:
            provider = self._config.get("ai.default_provider", "openai") if self._config else "openai"
            m = f"{provider}/{m}"
        return m

    def _get_api_kwargs(self, model: str) -> dict:
        kwargs = {}
        if not self._config:
            return kwargs

        if model.startswith("openai/"):
            api_key = self._config.get("ai.providers.openai.api_key")
            base_url = self._config.get("ai.providers.openai.base_url")
            if api_key:
                kwargs["api_key"] = api_key
            if base_url:
                kwargs["base_url"] = base_url
        elif model.startswith("anthropic/"):
            api_key = self._config.get("ai.providers.anthropic.api_key")
            if api_key:
                kwargs["api_key"] = api_key
        elif model.startswith("ollama/"):
            base_url = self._config.get("ai.providers.ollama.base_url", "http://localhost:11434")
            kwargs["api_base"] = f"{base_url}/v1"
            kwargs["api_key"] = "not-needed"
        elif model.startswith("custom/"):
            base_url = self._config.get("ai.providers.custom.base_url")
            api_key = self._config.get("ai.providers.custom.api_key", "")
            if base_url:
                kwargs["base_url"] = base_url
            kwargs["api_key"] = api_key or "not-needed"

        return kwargs

    async def chat_stream(self, messages: list[dict], model: str | None = None) -> None:
        import litellm

        model_str = self._get_model_string(model)
        kwargs = self._get_api_kwargs(model_str)

        max_tokens = 4096
        temperature = 0.7
        if self._config:
            max_tokens = self._config.get("ai.max_tokens", 4096)
            temperature = self._config.get("ai.temperature", 0.7)

        try:
            response = await litellm.acompletion(
                model=model_str,
                messages=messages,
                stream=True,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
            full = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full += token
                    self.response_token.emit(token)
            self.response_done.emit(full)
        except Exception as e:
            self.error.emit(str(e))
            self.response_done.emit(f"[错误: {e}]")

    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        import litellm

        model_str = self._get_model_string(model)
        kwargs = self._get_api_kwargs(model_str)

        max_tokens = 4096
        temperature = 0.7
        if self._config:
            max_tokens = self._config.get("ai.max_tokens", 4096)
            temperature = self._config.get("ai.temperature", 0.7)

        response = await litellm.acompletion(
            model=model_str,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content
