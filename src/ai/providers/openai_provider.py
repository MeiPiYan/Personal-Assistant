from __future__ import annotations

from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI provider via LiteLLM."""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    async def chat(self, messages: list[dict], model: str = "gpt-4o", **kwargs) -> str:
        import litellm
        call_kwargs = {}
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        if self.base_url:
            call_kwargs["base_url"] = self.base_url

        response = await litellm.acompletion(
            model=f"openai/{model}", messages=messages, **call_kwargs
        )
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], model: str = "gpt-4o", **kwargs):
        import litellm
        call_kwargs = {}
        if self.api_key:
            call_kwargs["api_key"] = self.api_key
        if self.base_url:
            call_kwargs["base_url"] = self.base_url

        response = await litellm.acompletion(
            model=f"openai/{model}", messages=messages, stream=True, **call_kwargs
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
