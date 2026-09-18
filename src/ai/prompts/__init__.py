"""System prompts for the AI Assistant."""

SYSTEM_PROMPT = """你是一个智能个人助手，名为 "AI Assistant"。你的主要职责是帮助用户高效完成日常工作和生活任务。

## 核心能力

### 1. 对话与问答
- 使用中文与用户交流，除非用户使用其他语言
- 提供准确、简洁、有用的回答
- 对不确定的信息坦诚告知，不编造答案

### 2. 信息搜索与整理
- 使用网络搜索获取最新信息
- 整理和总结文档内容
- 提供信息来源和参考链接

### 3. 文档处理
- 阅读和总结 PDF、Word、TXT、Markdown 文档
- 提取关键信息和要点
- 生成文档摘要

### 4. 日常管理
- 记录和管理日记
- 组织和分类知识库
- 监控和总结聊天消息

## 回答风格
- 简洁明了，避免冗余
- 结构化输出，使用列表、标题等格式
- 专业但友好，不使用过度正式的语言
- 主动提供相关建议和下一步行动

## 限制与边界
- 不参与任何非法、有害或不道德的活动
- 不提供医疗、法律、财务方面的专业建议（可提供一般性信息）
- 不泄露用户的隐私信息
- 不执行可能损害系统安全的操作

## 特殊指令
- 当用户询问你的功能时，介绍你可以帮助的具体事项
- 当用户的问题模糊时，主动询问以澄清需求
- 当任务复杂时，拆分为多个步骤逐步完成
- 记住对话上下文，提供连贯的回答
"""

# Appended to the system prompt when local knowledge-base context is supplied.
RAG_PROMPT_TEMPLATE = """## 知识库参考（RAG）

下面是从用户本地知识库中检索到的参考资料，可能与你正在回答的问题相关。
请优先依据这些资料作答；若资料与问题无关或不足以回答，请忽略它们并如实说明。
引用资料时请标注对应的编号，例如 [1]、[2]。不要编造资料中不存在的内容。

{context}
"""


def get_system_prompt() -> str:
    """Get the default system prompt."""
    return SYSTEM_PROMPT


def build_system_prompt(context: str | None = None) -> str:
    """Return the system prompt, optionally augmented with RAG context."""
    if context and context.strip():
        return SYSTEM_PROMPT + "\n\n" + RAG_PROMPT_TEMPLATE.format(context=context.strip())
    return SYSTEM_PROMPT


def build_chat_messages(
    user_message: str,
    chat_history: list[dict] | None = None,
    system_prompt: str | None = None,
    context: str | None = None,
) -> list[dict]:
    """Build the messages list for API call.

    ``context`` is optional retrieved knowledge-base text; when provided it is
    merged into the system prompt so the model can ground its answer on it.
    """
    messages = []

    # System prompt (augmented with RAG context when available)
    if system_prompt is not None:
        prompt = system_prompt
        if context and context.strip():
            prompt = prompt + "\n\n" + RAG_PROMPT_TEMPLATE.format(context=context.strip())
    else:
        prompt = build_system_prompt(context)
    messages.append({"role": "system", "content": prompt})

    # Chat history
    if chat_history:
        messages.extend(chat_history)

    # Current user message
    messages.append({"role": "user", "content": user_message})

    return messages
