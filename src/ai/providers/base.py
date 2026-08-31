from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract base for AI providers."""

    @abstractmethod
    async def chat(self, messages: list[dict], model: str = None, **kwargs) -> str:
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], model: str = None, **kwargs):
        ...
