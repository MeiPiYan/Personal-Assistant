from __future__ import annotations

import qdarktheme


class ThemeManager:
    _current = "dark"

    @classmethod
    def apply(cls, theme_name: str = "dark") -> None:
        qdarktheme.setup_theme(theme_name)
        cls._current = theme_name

    @classmethod
    def toggle(cls) -> None:
        new = "light" if cls._current == "dark" else "dark"
        cls.apply(new)

    @classmethod
    def current(cls) -> str:
        return cls._current
