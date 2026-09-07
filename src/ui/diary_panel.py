"""Diary panel - notes with AI assistance."""

from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QLineEdit, QFrame,
)

from .styles import ThemeManager
from src.storage.dao import DAO
from src.storage.models import DiaryEntry


class DiaryPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._dao: DAO | None = None
        self._ai_engine = None
        self._setup_ui()
        ThemeManager.register_panel(self)

    # -- Public setter (called after DB init) ---------------------------------

    def set_dao(self, dao: DAO) -> None:
        self._dao = dao
        asyncio.ensure_future(self._load_history())

    def set_ai_engine(self, engine) -> None:
        self._ai_engine = engine

    # -- Theme refresh ---------------------------------------------------------

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self._status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        self._divider.setStyleSheet(
            f"background-color: {c.divider}; max-height: 1px;"
        )
        self._history_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )

    # -- UI Setup -------------------------------------------------------------

    def _setup_ui(self) -> None:
        c = ThemeManager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("日记 / 笔记")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Entry input
        self.entry_input = QTextEdit()
        self.entry_input.setPlaceholderText("记录今天的事项、想法、感受...")
        self.entry_input.setMaximumHeight(140)
        layout.addWidget(self.entry_input)

        # Mood / Tags row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        self.mood_input = QLineEdit()
        self.mood_input.setPlaceholderText("心情 (如: 开心, 平静)")
        self.mood_input.setFixedWidth(160)
        meta_row.addWidget(self.mood_input)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("标签 (逗号分隔)")
        meta_row.addWidget(self.tags_input, 1)
        layout.addLayout(meta_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)

        self.ai_assist_btn = QPushButton("AI 润色")
        self.ai_assist_btn.setObjectName("secondaryBtn")
        self.ai_assist_btn.clicked.connect(self._on_ai_assist)
        btn_row.addWidget(self.ai_assist_btn)

        btn_row.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        btn_row.addWidget(self._status_label)

        layout.addLayout(btn_row)

        # Divider
        self._divider = QFrame()
        self._divider.setFrameShape(QFrame.HLine)
        self._divider.setStyleSheet(
            f"background-color: {c.divider}; max-height: 1px;"
        )
        layout.addWidget(self._divider)

        # History
        self._history_label = QLabel("历史记录")
        self._history_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        layout.addWidget(self._history_label)

        filter_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("按标签或内容筛选...")
        filter_row.addWidget(self.filter_input, 1)
        self.filter_btn = QPushButton("筛选")
        self.filter_btn.setObjectName("secondaryBtn")
        self.filter_btn.setFixedWidth(64)
        self.filter_btn.clicked.connect(self._on_filter)
        filter_row.addWidget(self.filter_btn)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.setFixedWidth(64)
        self.refresh_btn.clicked.connect(lambda: asyncio.ensure_future(self._load_history()))
        filter_row.addWidget(self.refresh_btn)
        layout.addLayout(filter_row)

        self.history_area = QScrollArea()
        self.history_area.setWidgetResizable(True)
        self.history_area.setFrameShape(QFrame.NoFrame)
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.history_area.setWidget(self.history_container)
        layout.addWidget(self.history_area, 1)

        # Keep a reference to status_label for helpers
        self.status_label = self._status_label

    # -- Actions --------------------------------------------------------------

    def _on_save(self) -> None:
        content = self.entry_input.toPlainText().strip()
        if not content:
            return
        if self._dao is None:
            self._show_status("数据库未就绪")
            return

        mood = self.mood_input.text().strip()
        tags_raw = self.tags_input.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

        entry = DiaryEntry(content=content, mood=mood, tags=tags)
        asyncio.ensure_future(self._save_entry(entry))

    async def _save_entry(self, entry: DiaryEntry) -> None:
        try:
            row_id = await self._dao.insert_diary(entry)
            self.entry_input.clear()
            self.mood_input.clear()
            self.tags_input.clear()
            self._show_status(f"已保存 (id={row_id})")
            await self._load_history()
        except Exception as e:
            self._show_status(f"保存失败: {e}")

    def _on_ai_assist(self) -> None:
        content = self.entry_input.toPlainText().strip()
        if not content:
            return
        if self._ai_engine is None:
            self._show_status("AI 引擎未就绪")
            return

        self.ai_assist_btn.setEnabled(False)
        self.ai_assist_btn.setText("润色中...")
        asyncio.ensure_future(self._do_ai_assist(content))

    async def _do_ai_assist(self, original_text: str) -> None:
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个温柔的日记助手。请帮助用户润色和优化他们的日记内容，"
                        "保持原意但使表达更流畅、优美。直接返回润色后的文本，不要加额外说明。"
                    ),
                },
                {"role": "user", "content": original_text},
            ]
            result = await self._ai_engine.chat(messages)
            if result:
                self.entry_input.setPlainText(result)
                self._show_status("AI 润色完成")
            else:
                self._show_status("AI 未返回内容")
        except Exception as e:
            self._show_status(f"AI 润色失败: {e}")
        finally:
            self.ai_assist_btn.setEnabled(True)
            self.ai_assist_btn.setText("AI 润色")

    def _on_filter(self) -> None:
        query = self.filter_input.text().strip()
        if not query:
            asyncio.ensure_future(self._load_history())
            return
        if self._dao is None:
            return
        asyncio.ensure_future(self._search_history(query))

    # -- History --------------------------------------------------------------

    async def _load_history(self, limit: int = 30) -> None:
        if self._dao is None:
            return
        try:
            entries = await self._dao.get_diaries(limit=limit)
            self._populate_history(entries)
        except Exception as e:
            self._show_status(f"加载历史失败: {e}")

    async def _search_history(self, query: str) -> None:
        if self._dao is None:
            return
        try:
            # Try FTS search first; fall back to local filter
            try:
                entries = await self._dao.search_diaries(query)
            except Exception:
                all_entries = await self._dao.get_diaries(limit=100)
                entries = [
                    e for e in all_entries
                    if query.lower() in (e.get("content", "") + e.get("tags", "")).lower()
                ]
            self._populate_history(entries)
            self._show_status(f"筛选到 {len(entries)} 条")
        except Exception as e:
            self._show_status(f"搜索失败: {e}")

    def _populate_history(self, entries: list[dict]) -> None:
        c = ThemeManager.get_colors()
        # Clear existing
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not entries:
            placeholder = QLabel("暂无记录")
            placeholder.setStyleSheet(
                f"color: {c.text_disabled}; padding: 12px;"
            )
            self.history_layout.addWidget(placeholder)
            return

        for row in entries:
            card = self._make_history_card(row)
            self.history_layout.addWidget(card)

    def _make_history_card(self, row: dict) -> QFrame:
        c = ThemeManager.get_colors()
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {c.bg_secondary}; border-radius: 6px; padding: 8px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(4)

        # Meta line: date + mood + tags
        meta_parts: list[str] = []
        created = row.get("created_at", "")
        if created:
            # Format: take first 16 chars "2024-01-15 14:30" style
            meta_parts.append(created[:16] if len(created) > 16 else created)
        mood = row.get("mood", "")
        if mood:
            meta_parts.append(f"😊 {mood}")
        tags_raw = row.get("tags", "")
        if tags_raw:
            try:
                import json as _json
                tags = _json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
                if tags:
                    meta_parts.append(" | ".join(tags))
            except Exception:
                meta_parts.append(tags_raw)

        meta_label = QLabel("  ".join(meta_parts))
        meta_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        meta_label.setWordWrap(True)
        card_layout.addWidget(meta_label)

        # Content preview
        content = row.get("content", "")
        preview = content[:200] + ("..." if len(content) > 200 else "")
        content_label = QLabel(preview)
        content_label.setWordWrap(True)
        content_label.setStyleSheet(
            f"color: {c.text_content}; font-size: 13px; padding: 2px 0;"
        )
        card_layout.addWidget(content_label)

        return card

    # -- Helpers ---------------------------------------------------------------

    def _show_status(self, text: str) -> None:
        self.status_label.setText(text)
