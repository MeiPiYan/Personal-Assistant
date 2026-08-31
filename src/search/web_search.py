from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    content: str = ""


class WebSearcher:
    """DuckDuckGo web search with content extraction."""

    def __init__(self, max_results: int = 5, extract_content: bool = True):
        self.max_results = max_results
        self.extract_content = extract_content

    def search(self, query: str) -> list[SearchResult]:
        from duckduckgo_search import DDGS

        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=self.max_results):
                    result = SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                    )
                    if self.extract_content and result.url:
                        try:
                            import trafilatura
                            downloaded = trafilatura.fetch_url(result.url)
                            if downloaded:
                                result.content = trafilatura.extract(downloaded) or ""
                        except Exception:
                            pass
                    results.append(result)
        except Exception:
            pass
        return results

    async def async_search(self, query: str) -> list[SearchResult]:
        import asyncio
        return await asyncio.to_thread(self.search, query)
