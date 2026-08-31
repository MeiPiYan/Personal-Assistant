from __future__ import annotations

from .base import AIProvider


class CustomProvider(AIProvider):
    """Any OpenAI-compatible endpoint."""

    def __init__(self, base_url: str, api_key: str = "not-needed"):
        self.base_url = base_url
        self.api_key = api_key

    async def chat(self, messages: list[dict], model: str = None, **kwargs) -> str:
        import litellm
        response = await litellm.acompletion(
            model=f"openai/{model or 'default'}",
            messages=messages,
            base_url=self.base_url,
            api_key=self.api_key,
        )
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], model: str = None, **kwargs):
        import litellm
        response = await litellm.acompletion(
            model=f"openai/{model or 'default'}",
            messages=messages,
            stream=True,
            base_url=self.base_url,
            api_key=self.api_key,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
