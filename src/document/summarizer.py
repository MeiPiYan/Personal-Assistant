from __future__ import annotations


class DocumentSummarizer:
    """Hierarchical document summarization via AI."""

    def __init__(self, ai_engine=None):
        self._ai = ai_engine

    async def summarize(self, text: str, model: str = None) -> str:
        if not self._ai:
            return "[AI engine not connected]"

        from .chunker import TextChunker
        chunker = TextChunker()
        chunks = chunker.chunk(text)

        if len(chunks) == 1:
            return await self._summarize_single(chunks[0], model)

        # Step 1: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = await self._summarize_single(
                f"[文档第 {i+1}/{len(chunks)} 部分]\n{chunk}", model
            )
            chunk_summaries.append(summary)

        # Step 2: Merge summaries
        merged = "\n\n".join(
            f"## 第 {i+1} 部分摘要\n{s}" for i, s in enumerate(chunk_summaries)
        )
        return await self._merge_summaries(merged, model)

    async def _summarize_single(self, text: str, model: str = None) -> str:
        messages = [
            {"role": "system", "content": "你是一个专业的文档总结助手。请对以下内容进行精炼的摘要，保留关键信息和要点。"},
            {"role": "user", "content": f"请总结以下内容：\n\n{text}"},
        ]
        return await self._ai.chat(messages, model)

    async def _merge_summaries(self, merged_text: str, model: str = None) -> str:
        messages = [
            {"role": "system", "content": "你是一个专业的文档总结助手。请将以下多个部分的摘要合并为一份完整的、结构化的总结报告。"},
            {"role": "user", "content": f"请合并以下摘要：\n\n{merged_text}"},
        ]
        return await self._ai.chat(messages, model)
