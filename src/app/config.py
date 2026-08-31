from __future__ import annotations

import sys
from pathlib import Path

import yaml


class Config:
    _instance = None
    _data: dict = {}

    def __new__(cls) -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: str | Path | None = None) -> None:
        if path is None:
            path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        path = Path(path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = self._defaults()

    def _defaults(self) -> dict:
        return {
            "ai": {
                "default_provider": "openai",
                "default_model": "gpt-4o",
                "max_tokens": 4096,
                "temperature": 0.7,
                "providers": {
                    "openai": {"api_key": "", "base_url": None},
                    "anthropic": {"api_key": ""},
                    "ollama": {"base_url": "http://localhost:11434", "model": "llama3.1"},
                    "custom": {"base_url": "", "api_key": "", "model": ""},
                },
            },
            "chat_reader": {
                "wechat": {"enabled": False, "poll_interval": 5, "auto_summary": True},
                "qq": {"enabled": False, "napcat_url": "http://127.0.0.1:3000", "poll_interval": 5},
            },
            "search": {"provider": "duckduckgo", "max_results": 5, "content_extraction": True},
            "ui": {
                "theme": "dark",
                "floating_ball": {"enabled": True, "size": 48, "opacity": 0.85},
                "main_window": {"width": 900, "height": 650},
            },
            "storage": {"db_path": "data/assistant.db"},
        }

    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def set(self, key: str, value) -> None:
        keys = key.split(".")
        d = self._data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def save(self, path: str | Path | None = None) -> None:
        if path is None:
            path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)

    @property
    def data(self) -> dict:
        return self._data
