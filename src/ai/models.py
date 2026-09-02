"""Shared model configurations for all providers."""

# Provider display names
PROVIDER_NAMES = {
    "openai": "OpenAI",
    "deepseek": "DeepSeek",
    "siliconflow": "SiliconFlow",
    "anthropic": "Anthropic",
    "gemini": "Google Gemini",
    "groq": "Groq",
    "ollama": "Ollama (本地)",
    "custom": "自定义",
}

# Cloud providers list (for UI ordering)
CLOUD_PROVIDERS = ["openai", "deepseek", "siliconflow", "anthropic", "gemini", "groq"]

# Models for each provider (name, display_name, is_default)
PROVIDER_MODELS = {
    "openai": [
        ("gpt-4o", "GPT-4o (推荐)", True),
        ("gpt-4o-mini", "GPT-4o Mini (性价比)", False),
        ("gpt-4-turbo", "GPT-4 Turbo", False),
        ("o1-preview", "o1-preview (推理)", False),
        ("o1-mini", "o1-mini (轻量推理)", False),
    ],
    "deepseek": [
        ("deepseek-chat", "DeepSeek V3 (推荐)", True),
        ("deepseek-coder", "DeepSeek Coder (代码)", False),
        ("deepseek-reasoner", "DeepSeek R1 (推理)", False),
    ],
    "siliconflow": [
        ("deepseek-ai/DeepSeek-V3", "DeepSeek V3 (推荐)", True),
        ("Qwen/Qwen2.5-72B-Instruct", "Qwen 2.5 72B", False),
        ("Pro/deepseek-ai/DeepSeek-V3", "DeepSeek V3 Pro", False),
        ("deepseek-ai/DeepSeek-R1", "DeepSeek R1", False),
        ("THUDM/glm-4-9b-chat", "GLM-4 9B (轻量)", False),
    ],
    "anthropic": [
        ("claude-sonnet-4-20250514", "Claude Sonnet 4 (推荐)", True),
        ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku (快速)", False),
        ("claude-3-opus-20240229", "Claude 3 Opus (最强)", False),
    ],
    "gemini": [
        ("gemini-2.0-flash", "Gemini 2.0 Flash (推荐)", True),
        ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite (轻量)", False),
        ("gemini-1.5-pro", "Gemini 1.5 Pro", False),
        ("gemini-1.5-flash", "Gemini 1.5 Flash", False),
    ],
    "groq": [
        ("llama-3.3-70b-versatile", "Llama 3.3 70B (推荐)", True),
        ("llama-3.1-8b-instant", "Llama 3.1 8B (快速)", False),
        ("gemma2-9b-it", "Gemma 2 9B", False),
        ("mixtral-8x7b-32768", "Mixtral 8x7B", False),
    ],
    "ollama": [
        ("llama3.1", "Llama 3.1 (推荐)", True),
        ("llama3.1:8b", "Llama 3.1 8B (轻量)", False),
        ("llama3.1:70b", "Llama 3.1 70B (强力)", False),
        ("qwen2.5", "Qwen 2.5", False),
        ("mistral", "Mistral", False),
        ("codellama", "CodeLlama (代码)", False),
        ("deepseek-coder-v2", "DeepSeek Coder V2", False),
    ],
}


def get_model_display_name(provider: str, model_id: str) -> str:
    """Get display name for a model."""
    models = PROVIDER_MODELS.get(provider, [])
    for model_name, display_name, _ in models:
        if model_name == model_id:
            return display_name
    return model_id


def get_default_model(provider: str) -> str:
    """Get the default model for a provider."""
    models = PROVIDER_MODELS.get(provider, [])
    for model_name, _, is_default in models:
        if is_default:
            return model_name
    return models[0][0] if models else ""


def get_all_model_strings() -> list[str]:
    """Get all models in provider/model format for the chat panel."""
    result = []
    for provider in CLOUD_PROVIDERS:
        models = PROVIDER_MODELS.get(provider, [])
        for model_name, _, _ in models[:3]:  # Top 3 per provider
            result.append(f"{provider}/{model_name}")
    # Add ollama
    for model_name, _, _ in PROVIDER_MODELS.get("ollama", [])[:2]:
        result.append(f"ollama/{model_name}")
    return result


def get_provider_models_for_combo(provider: str) -> list[str]:
    """Get model IDs for a provider's combo box."""
    models = PROVIDER_MODELS.get(provider, [])
    return [model_name for model_name, _, _ in models]
