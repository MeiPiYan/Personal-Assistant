from __future__ import annotations

from .base import AIProvider


class OllamaProvider(AIProvider):
    """Local Ollama provider via LiteLLM."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def chat(self, messages: list[dict], model: str = "llama3.1", **kwargs) -> str:
        import litellm
        response = await litellm.acompletion(
            model=f"ollama/{model}",
            messages=messages,
            api_base=f"{self.base_url}/v1",
            api_key="not-needed",
        )
        return response.choices[0].message.content

    async def chat_stream(self, messages: list[dict], model: str = "llama3.1", **kwargs):
        import litellm
        response = await litellm.acompletion(
            model=f"ollama/{model}",
            messages=messages,
            stream=True,
            api_base=f"{self.base_url}/v1",
            api_key="not-needed",
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
