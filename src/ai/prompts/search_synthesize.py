"""Search result synthesis prompts."""

SEARCH_SYNTHESIS_SYSTEM = """你是一个搜索结果分析助手。根据提供的搜索结果，综合分析并给出：
1. 对问题的直接回答
2. 关键信息点
3. 信息来源"""

SEARCH_SYNTHESIS_USER = """搜索问题: {query}

搜索结果:
{results}

请综合分析以上搜索结果，给出回答。"""
