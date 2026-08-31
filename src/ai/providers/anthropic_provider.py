from __future__ import annotations

from .base import AIProvider


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider via LiteLLM."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    async def chat(self, messages: list[dict], model: str = "claude-sonnet-4-20250514", **kwargs) -> str:
        import litellm
        call_kwargs = {}
        if self.api_key:
            call_kwargs["api_key"] = self.api_key

        response = await litellm.acompletion(
            model=f"anthropic/{model}", messages=messages, **call_kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], model: str = "claude-sonnet-4-20250514", **kwargs):
        import litellm
        call_kwargs = {}
        if self.api_key:
            call_kwargs["api_key"] = self.api_key

        response = await litellm.acompletion(
            model=f"anthropic/{model}", messages=messages, stream=True, **call_kwargs
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
