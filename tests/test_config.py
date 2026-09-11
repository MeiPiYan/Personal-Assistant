"""Tests for Config class."""
import pytest
import yaml
from pathlib import Path

from src.app.config import Config


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset Config singleton before each test."""
    Config._instance = None
    Config._data = {}
    yield
    Config._instance = None
    Config._data = {}


@pytest.fixture
def config():
    """Provide a fresh Config instance with defaults loaded."""
    cfg = Config()
    cfg._data = cfg._defaults()
    return cfg


# ===========================================================================
# Singleton
# ===========================================================================

class TestConfigSingleton:
    def test_singleton_behavior(self):
        a = Config()
        b = Config()
        assert a is b

    def test_singleton_persists_data(self):
        a = Config()
        a._data = {"key": "value"}
        b = Config()
        assert b._data.get("key") == "value"


# ===========================================================================
# get
# ===========================================================================

class TestConfigGet:
    def test_simple_key(self, config):
        assert config.get("ai.default_provider") == "deepseek"

    def test_nested_key(self, config):
        assert config.get("ai.providers.openai.api_key") == ""

    def test_missing_key_returns_default(self, config):
        assert config.get("nonexistent.key", "fallback") == "fallback"

    def test_missing_key_no_default(self, config):
        assert config.get("nonexistent.key") is None

    def test_partial_path_returns_dict(self, config):
        val = config.get("ai")
        assert isinstance(val, dict)
        assert "default_provider" in val

    def test_intermediate_missing_returns_default(self, config):
        assert config.get("ai.nonexistent_section.key", "x") == "x"

    def test_numeric_value(self, config):
        assert config.get("ai.max_tokens") == 4096

    def test_float_value(self, config):
        assert config.get("ai.temperature") == 0.7

    def test_bool_value(self, config):
        assert config.get("chat_reader.wechat.enabled") is False

    def test_list_value(self, config):
        val = config.get("search")
        assert isinstance(val, dict)

    def test_single_segment_key(self, config):
        val = config.get("search")
        assert isinstance(val, dict)


# ===========================================================================
# set
# ===========================================================================

class TestConfigSet:
    def test_set_simple_key(self, config):
        config.set("ai.default_provider", "anthropic")
        assert config.get("ai.default_provider") == "anthropic"

    def test_set_creates_nested_path(self, config):
        config.set("new.nested.key", "value")
        assert config.get("new.nested.key") == "value"

    def test_set_overwrite(self, config):
        config.set("ai.max_tokens", 8192)
        assert config.get("ai.max_tokens") == 8192

    def test_set_various_types(self, config):
        config.set("test.int", 42)
        config.set("test.str", "hello")
        config.set("test.bool", True)
        config.set("test.list", [1, 2, 3])

        assert config.get("test.int") == 42
        assert config.get("test.str") == "hello"
        assert config.get("test.bool") is True
        assert config.get("test.list") == [1, 2, 3]


# ===========================================================================
# data property
# ===========================================================================

class TestDataProperty:
    def test_data_returns_dict(self, config):
        assert isinstance(config.data, dict)

    def test_data_shares_reference(self, config):
        config.data["custom"] = "value"
        assert config.get("custom") == "value"


# ===========================================================================
# defaults
# ===========================================================================

class TestDefaults:
    def test_has_all_top_level_sections(self, config):
        d = config._defaults()
        assert "ai" in d
        assert "chat_reader" in d
        assert "search" in d
        assert "ui" in d
        assert "storage" in d

    def test_ai_defaults(self, config):
        d = config._defaults()
        assert d["ai"]["default_provider"] == "deepseek"
        assert d["ai"]["default_model"] == "deepseek-chat"
        assert d["ai"]["max_tokens"] == 4096
        assert d["ai"]["temperature"] == 0.7

    def test_ui_defaults(self, config):
        d = config._defaults()
        assert d["ui"]["theme"] == "dark"
        assert d["ui"]["floating_ball"]["enabled"] is True
        assert d["ui"]["main_window"]["width"] == 900

    def test_search_defaults(self, config):
        d = config._defaults()
        assert d["search"]["provider"] == "duckduckgo"
        assert d["search"]["max_results"] == 5


# ===========================================================================
# load
# ===========================================================================

class TestConfigLoad:
    def test_load_from_yaml_file(self, config, tmp_path):
        yaml_file = tmp_path / "test_config.yaml"
        yaml_file.write_text(
            yaml.dump({"ai": {"default_provider": "deepseek"}, "custom": {"key": 123}}),
            encoding="utf-8",
        )
        config.load(str(yaml_file))
        assert config.get("ai.default_provider") == "deepseek"
        assert config.get("custom.key") == 123

    def test_load_nonexistent_file_uses_defaults(self, config):
        config.load("/tmp/nonexistent_config_file.yaml")
        # Should fall back to defaults
        assert config.get("ai.default_provider") == "deepseek"

    def test_load_none_uses_default_path(self, config, monkeypatch):
        """load(None) looks for config/settings.yaml relative to the module."""
        # Just verify it doesn't crash; the default path likely doesn't exist in test env
        config.load(None)
        # If the file doesn't exist, defaults are used
        assert "ai" in config.data


# ===========================================================================
# save
# ===========================================================================

class TestConfigSave:
    def test_save_creates_file(self, config, tmp_path):
        save_path = tmp_path / "sub" / "saved.yaml"
        config.set("test_key", "test_value")
        config.save(str(save_path))
        assert save_path.exists()

        with open(save_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["test_key"] == "test_value"

    def test_save_preserves_all_data(self, config, tmp_path):
        config.set("a.b.c", 1)
        config.set("x.y", "hello")
        save_path = tmp_path / "full.yaml"
        config.save(str(save_path))

        cfg2 = Config()
        cfg2._data = {}
        cfg2.load(str(save_path))
        assert cfg2.get("a.b.c") == 1
        assert cfg2.get("x.y") == "hello"
