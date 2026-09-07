"""Search panel - web search and local knowledge base search."""

from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QScrollArea, QFrame,
    QListWidget, QListWidgetItem, QSizePolicy,
)

from .styles import ThemeManager
from ..search.web_search import WebSearcher
from ..search.local_search import LocalSearcher
from ..search.related import RelatedSearcher


class SearchPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._ai_engine = None

        # Backend searchers
        self._web_searcher = WebSearcher(max_results=8, extract_content=False)
        self._local_searcher = LocalSearcher()
        self._related_searcher = RelatedSearcher()

        self._setup_ui()
        ThemeManager.register_panel(self)

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self.status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px; padding: 2px 0;"
        )
        self.related_bar.setStyleSheet(
            "QListWidget { background-color: transparent; border: none; }"
            f"QListWidget::item {{"
            f"  background-color: {c.bg_tertiary};"
            f"  color: {c.accent_light};"
            f"  border: 1px solid {c.border};"
            "  border-radius: 12px;"
            "  padding: 4px 12px;"
            "  margin: 2px 4px 2px 0;"
            "}"
            f"QListWidget::item:hover {{"
            f"  background-color: {c.bg_checked};"
            f"  border-color: {c.accent};"
            "}"
        )

    def set_ai_engine(self, engine) -> None:
        """Accept the shared AIEngine (called from MainWindow wiring)."""
        self._ai_engine = engine
        self._related_searcher._ai = engine

    def _setup_ui(self) -> None:
        c = ThemeManager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("搜索")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Search input row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedWidth(80)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)

        self.local_btn = QPushButton("本地")
        self.local_btn.setObjectName("secondaryBtn")
        self.local_btn.setFixedWidth(64)
        self.local_btn.clicked.connect(self._on_local_search)
        search_row.addWidget(self.local_btn)

        self.related_btn = QPushButton("相关")
        self.related_btn.setObjectName("secondaryBtn")
        self.related_btn.setFixedWidth(64)
        self.related_btn.setToolTip("AI 推荐相关搜索")
        self.related_btn.clicked.connect(self._on_related_search)
        search_row.addWidget(self.related_btn)

        layout.addLayout(search_row)

        # Related queries suggestion bar
        self.related_bar = QListWidget()
        self.related_bar.setFixedHeight(0)
        self.related_bar.setMaximumHeight(0)
        self.related_bar.setFlow(QListWidget.LeftToRight)
        self.related_bar.setWrapping(True)
        self.related_bar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.related_bar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.related_bar.setFrameShape(QFrame.NoFrame)
        self.related_bar.setStyleSheet(
            "QListWidget { background-color: transparent; border: none; }"
            f"QListWidget::item {{"
            f"  background-color: {c.bg_tertiary};"
            f"  color: {c.accent_light};"
            f"  border: 1px solid {c.border};"
            "  border-radius: 12px;"
            "  padding: 4px 12px;"
            "  margin: 2px 4px 2px 0;"
            "}"
            f"QListWidget::item:hover {{"
            f"  background-color: {c.bg_checked};"
            f"  border-color: {c.accent};"
            "}"
        )
        self.related_bar.itemClicked.connect(self._on_related_clicked)
        layout.addWidget(self.related_bar)

        # Status label (shown during loading)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px; padding: 2px 0;"
        )
        self.status_label.hide()
        layout.addWidget(self.status_label)

        # Results area
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setFrameShape(QFrame.NoFrame)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(8)
        self.results_area.setWidget(self.results_container)
        layout.addWidget(self.results_area, 1)

        # AI synthesis
        self.synthesis = QTextEdit()
        self.synthesis.setReadOnly(True)
        self.synthesis.setPlaceholderText("AI 综合分析结果将在此显示...")
        self.synthesis.setMaximumHeight(160)
        layout.addWidget(self.synthesis)

    # ── Result display helpers ──────────────────────────────────────

    def _clear_results(self) -> None:
        """Remove all widgets from the results container."""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.status_label.show()

    def _hide_status(self) -> None:
        self.status_label.hide()

    def _show_web_results(self, results) -> None:
        """Render web search results as styled cards."""
        if not results:
            self._add_empty_message("未找到相关网页结果")
            return
        for r in results:
            card = self._make_result_card(
                title=r.title,
                subtitle=r.url,
                body=r.snippet,
            )
            self.results_layout.addWidget(card)

    def _show_local_results(self, data: dict) -> None:
        """Render local search results grouped by source."""
        total = sum(len(v) for v in data.values())
        if total == 0:
            self._add_empty_message("本地知识库中未找到匹配内容")
            return

        section_map = [
            ("messages", "💬 聊天记录"),
            ("diaries", "📝 日记"),
            ("knowledge", "📚 知识库"),
        ]
        for key, label in section_map:
            items = data.get(key, [])
            if not items:
                continue
            section = self._make_section_header(f"{label} ({len(items)})")
            self.results_layout.addWidget(section)
            for item in items:
                text = item.get("content", "") or item.get("title", "") or ""
                sender = item.get("sender", "")
                subtitle = f"来自: {sender}" if sender else ""
                card = self._make_result_card(
                    title=text[:80] + ("…" if len(text) > 80 else ""),
                    subtitle=subtitle,
                    body=text[:300],
                )
                self.results_layout.addWidget(card)

    def _show_related_queries(self, queries: list[str]) -> None:
        """Populate the related-queries suggestion bar."""
        self.related_bar.clear()
        if not queries:
            self.related_bar.setMaximumHeight(0)
            self.related_bar.setFixedHeight(0)
            return
        for q in queries:
            item = QListWidgetItem(q)
            item.setToolTip(f"点击搜索: {q}")
            self.related_bar.addItem(item)
        self.related_bar.setMaximumHeight(60)
        self.related_bar.setFixedHeight(56)

    def _add_empty_message(self, text: str) -> None:
        c = ThemeManager.get_colors()
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color: {c.text_disabled}; font-size: 13px; padding: 30px 0;"
        )
        self.results_layout.addWidget(lbl)

    # ── Widget builders ─────────────────────────────────────────────

    def _make_result_card(self, title: str, subtitle: str = "", body: str = "") -> QFrame:
        """Build a single result card widget."""
        c = ThemeManager.get_colors()
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {c.bg_primary};"
            f"  border: 1px solid {c.border};"
            "  border-radius: 8px;"
            "  padding: 0;"
            "}"
            f"QFrame:hover {{"
            f"  border-color: {c.border_light};"
            "}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(4)

        if title:
            title_lbl = QLabel(title)
            title_lbl.setWordWrap(True)
            title_lbl.setStyleSheet(
                f"color: {c.text_primary}; font-size: 13px; font-weight: 600;"
                "background: transparent; border: none;"
            )
            card_layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setWordWrap(True)
            sub_lbl.setStyleSheet(
                f"color: {c.accent_light}; font-size: 11px;"
                "background: transparent; border: none;"
            )
            card_layout.addWidget(sub_lbl)

        if body:
            body_lbl = QLabel(body)
            body_lbl.setWordWrap(True)
            body_lbl.setStyleSheet(
                f"color: {c.text_secondary}; font-size: 12px;"
                "background: transparent; border: none;"
            )
            card_layout.addWidget(body_lbl)

        return card

    def _make_section_header(self, text: str) -> QLabel:
        c = ThemeManager.get_colors()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {c.text_hover}; font-size: 13px; font-weight: bold;"
            "padding: 6px 0 2px 0;"
            "background: transparent;"
        )
        return lbl

    # ── Async search actions ────────────────────────────────────────

    def _on_search(self) -> None:
        """Web search button / Enter key."""
        query = self.search_input.text().strip()
        if not query:
            return
        self._clear_results()
        self._set_status("正在搜索网络...")
        self.search_btn.setEnabled(False)
        self._set_buttons_busy(True)
        asyncio.ensure_future(self._do_web_search(query))

    def _on_local_search(self) -> None:
        """Local knowledge base search."""
        query = self.search_input.text().strip()
        if not query:
            return
        self._clear_results()
        self._set_status("正在搜索本地知识库...")
        self.local_btn.setEnabled(False)
        self._set_buttons_busy(True)
        asyncio.ensure_future(self._do_local_search(query))

    def _on_related_search(self) -> None:
        """AI-powered related query expansion."""
        query = self.search_input.text().strip()
        if not query:
            return
        if not self._ai_engine:
            self.synthesis.setPlainText("AI 引擎尚未初始化，请先配置 AI 提供者。")
            return
        self._set_status("正在生成相关搜索建议...")
        self.related_btn.setEnabled(False)
        asyncio.ensure_future(self._do_related_search(query))

    def _on_related_clicked(self, item: QListWidgetItem) -> None:
        """A related suggestion was clicked – run a web search for it."""
        text = item.text().strip()
        if text:
            self.search_input.setText(text)
            self._on_search()

    # ── Actual async work ───────────────────────────────────────────

    async def _do_web_search(self, query: str) -> None:
        try:
            results = await self._web_searcher.async_search(query)
            self._show_web_results(results)
            self._hide_status()
        except Exception as e:
            self.synthesis.setPlainText(f"网络搜索出错: {e}")
            self._hide_status()
        finally:
            self.search_btn.setEnabled(True)
            self._set_buttons_busy(False)

    async def _do_local_search(self, query: str) -> None:
        try:
            data = await self._local_searcher.search_all(query)
            self._show_local_results(data)
            self._hide_status()
        except Exception as e:
            self.synthesis.setPlainText(f"本地搜索出错: {e}")
            self._hide_status()
        finally:
            self.local_btn.setEnabled(True)
            self._set_buttons_busy(False)

    async def _do_related_search(self, query: str) -> None:
        try:
            queries = await self._related_searcher.expand(query)
            self._show_related_queries(queries)
            self._hide_status()
        except Exception as e:
            self.synthesis.setPlainText(f"生成相关搜索出错: {e}")
            self._hide_status()
        finally:
            self.related_btn.setEnabled(True)
            self._set_buttons_busy(False)

    # ── UI helpers ──────────────────────────────────────────────────

    def _set_buttons_busy(self, busy: bool) -> None:
        """Disable/enable all action buttons during an async operation."""
        if busy:
            self.search_btn.setEnabled(False)
            self.local_btn.setEnabled(False)
            self.related_btn.setEnabled(False)
            self.search_input.setEnabled(False)
        else:
            self.search_btn.setEnabled(True)
            self.local_btn.setEnabled(True)
            self.related_btn.setEnabled(True)
            self.search_input.setEnabled(True)
