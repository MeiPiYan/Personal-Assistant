from __future__ import annotations


class RelatedSearcher:
    """AI-generated related topic expansion."""

    def __init__(self, ai_engine=None):
        self._ai = ai_engine

    async def expand(self, topic: str, model: str = None) -> list[str]:
        if not self._ai:
            return []

        messages = [
            {"role": "system", "content": (
                "你是一个搜索助手。给定一个主题，生成 3-5 个相关的搜索查询建议，"
                "帮助用户深入探索该主题。每行一个查询，不要编号。"
            )},
            {"role": "user", "content": f"主题: {topic}"},
        ]
        result = await self._ai.chat(messages, model)
        return [line.strip().lstrip("0123456789.、- ") for line in result.strip().split("\n") if line.strip()]
