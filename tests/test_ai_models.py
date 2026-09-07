"""Tests for AI model registry and utility functions."""
import pytest

from src.ai.models import (
    PROVIDER_NAMES,
    PROVIDER_MODELS,
    CLOUD_PROVIDERS,
    get_model_display_name,
    get_default_model,
    get_all_model_strings,
    get_provider_models_for_combo,
)


# ===========================================================================
# Constants
# ===========================================================================

class TestProviderNames:
    def test_known_providers_have_display_names(self):
        for provider in CLOUD_PROVIDERS:
            assert provider in PROVIDER_NAMES
            assert isinstance(PROVIDER_NAMES[provider], str)
            assert len(PROVIDER_NAMES[provider]) > 0

    def test_ollama_in_provider_names(self):
        assert "ollama" in PROVIDER_NAMES

    def test_custom_in_provider_names(self):
        assert "custom" in PROVIDER_NAMES


class TestProviderModels:
    def test_all_cloud_providers_have_models(self):
        for provider in CLOUD_PROVIDERS:
            assert provider in PROVIDER_MODELS
            assert len(PROVIDER_MODELS[provider]) > 0

    def test_ollama_has_models(self):
        assert "ollama" in PROVIDER_MODELS
        assert len(PROVIDER_MODELS["ollama"]) > 0

    def test_each_model_tuple_has_three_elements(self):
        for provider, models in PROVIDER_MODELS.items():
            for model_tuple in models:
                assert len(model_tuple) == 3, f"Model tuple in {provider} has wrong length"

    def test_each_provider_has_exactly_one_default(self):
        for provider, models in PROVIDER_MODELS.items():
            defaults = [m for m in models if m[2] is True]
            assert len(defaults) == 1, f"{provider} should have exactly 1 default, got {len(defaults)}"

    def test_model_names_are_nonempty_strings(self):
        for provider, models in PROVIDER_MODELS.items():
            for model_name, display_name, is_default in models:
                assert isinstance(model_name, str) and len(model_name) > 0
                assert isinstance(display_name, str) and len(display_name) > 0


class TestCloudProviders:
    def test_is_list(self):
        assert isinstance(CLOUD_PROVIDERS, list)

    def test_contains_openai(self):
        assert "openai" in CLOUD_PROVIDERS

    def test_does_not_contain_ollama(self):
        # ollama is local, not cloud
        assert "ollama" not in CLOUD_PROVIDERS


# ===========================================================================
# get_model_display_name
# ===========================================================================

class TestGetModelDisplayName:
    def test_known_model(self):
        name = get_model_display_name("openai", "gpt-4o")
        assert name == "GPT-4o (推荐)"

    def test_known_model_deepseek(self):
        name = get_model_display_name("deepseek", "deepseek-chat")
        assert name == "DeepSeek V3 (推荐)"

    def test_unknown_model_returns_id(self):
        name = get_model_display_name("openai", "unknown-model-xyz")
        assert name == "unknown-model-xyz"

    def test_unknown_provider_returns_id(self):
        name = get_model_display_name("nonexistent_provider", "some-model")
        assert name == "some-model"

    def test_empty_provider(self):
        name = get_model_display_name("", "model")
        assert name == "model"

    def test_empty_model(self):
        name = get_model_display_name("openai", "")
        assert name == ""

    def test_all_providers_have_default_model_name(self):
        for provider, models in PROVIDER_MODELS.items():
            for model_name, _, _ in models:
                result = get_model_display_name(provider, model_name)
                assert result != model_name or len(model_name) == 0, (
                    f"Model {provider}/{model_name} has no display name"
                )


# ===========================================================================
# get_default_model
# ===========================================================================

class TestGetDefaultModel:
    def test_openai_default(self):
        assert get_default_model("openai") == "gpt-4o"

    def test_deepseek_default(self):
        assert get_default_model("deepseek") == "deepseek-chat"

    def test_anthropic_default(self):
        default = get_default_model("anthropic")
        assert default == "claude-sonnet-4-20250514"

    def test_gemini_default(self):
        assert get_default_model("gemini") == "gemini-2.0-flash"

    def test_groq_default(self):
        assert get_default_model("groq") == "llama-3.3-70b-versatile"

    def test_siliconflow_default(self):
        assert get_default_model("siliconflow") == "deepseek-ai/DeepSeek-V3"

    def test_ollama_default(self):
        assert get_default_model("ollama") == "llama3.1"

    def test_unknown_provider_returns_first_model(self):
        # Unknown provider returns empty string since PROVIDER_MODELS.get returns []
        result = get_default_model("nonexistent")
        assert result == ""

    def test_all_cloud_providers_have_default(self):
        for provider in CLOUD_PROVIDERS:
            default = get_default_model(provider)
            assert default != "", f"{provider} has no default model"


# ===========================================================================
# get_all_model_strings
# ===========================================================================

class TestGetAllModelStrings:
    def test_returns_list(self):
        result = get_all_model_strings()
        assert isinstance(result, list)

    def test_format_is_provider_model(self):
        result = get_all_model_strings()
        for model_str in result:
            # Format is "provider/model_id" — model_id may itself contain '/' (e.g. siliconflow/deepseek-ai/DeepSeek-V3)
            first_slash = model_str.find("/")
            assert first_slash > 0, f"Model string '{model_str}' missing provider prefix"
            provider = model_str[:first_slash]
            model_id = model_str[first_slash + 1:]
            assert provider, f"Empty provider in '{model_str}'"
            assert model_id, f"Empty model_id in '{model_str}'"

    def test_first_is_openai_default(self):
        result = get_all_model_strings()
        assert result[0] == "openai/gpt-4o"

    def test_includes_ollama(self):
        result = get_all_model_strings()
        ollama_models = [m for m in result if m.startswith("ollama/")]
        assert len(ollama_models) > 0

    def test_top_3_per_cloud_provider(self):
        result = get_all_model_strings()
        for provider in CLOUD_PROVIDERS:
            provider_models = [m for m in result if m.startswith(f"{provider}/")]
            assert len(provider_models) == 3, (
                f"{provider} should have top 3 models, got {len(provider_models)}"
            )

    def test_ollama_has_2_models(self):
        result = get_all_model_strings()
        ollama_models = [m for m in result if m.startswith("ollama/")]
        assert len(ollama_models) == 2

    def test_total_count(self):
        """6 cloud providers * 3 models + 2 ollama = 20"""
        result = get_all_model_strings()
        assert len(result) == 20


# ===========================================================================
# get_provider_models_for_combo
# ===========================================================================

class TestGetProviderModelsForCombo:
    def test_openai_models(self):
        models = get_provider_models_for_combo("openai")
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models
        assert len(models) == 5

    def test_unknown_provider(self):
        models = get_provider_models_for_combo("nonexistent")
        assert models == []

    def test_returns_model_ids_only(self):
        models = get_provider_models_for_combo("deepseek")
        for m in models:
            assert isinstance(m, str)
            # Should not contain display names with parentheses
            assert "(" not in m

    def test_all_providers(self):
        for provider in PROVIDER_MODELS:
            models = get_provider_models_for_combo(provider)
            assert len(models) > 0
