"""Knowledge base panel."""
from __future__ import annotations

import asyncio

from src.ui.tasks import spawn_ui
import json as _json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QScrollArea, QComboBox, QFrame,
)

from .base_panel import ThemedPanel
from .styles import ThemeManager
from src.storage.dao import DAO
from src.storage.models import KnowledgeItem


class KnowledgePanel(ThemedPanel):
    # Emitted when the user asks to explore a search-result chunk in the graph.
    graph_enter_requested = Signal(int)

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._dao: DAO | None = None
        self._vector_store = None  # lazily built once the DAO is ready
        self._setup_ui()

    # -- Public setter (called after DB init) ---------------------------------

    def set_dao(self, dao: DAO) -> None:
        self._dao = dao
        self._init_vector_store()
        spawn_ui(self._load_browse())

    def set_vector_store(self, store) -> None:
        """Use a shared vector store (built once by MainWindow) instead of a
        private one, so the embedding backend is not instantiated twice."""
        if store is not None:
            self._vector_store = store

    def _init_vector_store(self) -> None:
        """Build the vector store used to index/search knowledge (P0).

        Kept lazy and non-fatal: if the embedding backend cannot be created,
        the panel keeps working with the lexical (FTS/LIKE) path only.
        """
        if self._vector_store is not None:
            return
        try:
            from src.search.vector_search import VectorStore

            self._vector_store = VectorStore(dao=self._dao)
        except Exception:
            self._vector_store = None

    # -- Theme refresh ---------------------------------------------------------

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self._status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )

    # -- UI Setup -------------------------------------------------------------

    def _setup_ui(self) -> None:
        c = ThemeManager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("知识库")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Add item row
        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("标题...")
        add_row.addWidget(self.title_input, 1)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "技术", "工作", "生活", "学习", "其他"])
        self.category_combo.setFixedWidth(88)
        add_row.addWidget(self.category_combo)

        self.add_btn = QPushButton("添加")
        self.add_btn.setFixedWidth(64)
        self.add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.add_btn)

        layout.addLayout(add_row)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("粘贴要保存的内容...")
        self.content_input.setMaximumHeight(100)
        layout.addWidget(self.content_input)

        # Tags row
        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("标签 (逗号分隔)")
        tags_row.addWidget(self.tags_input, 1)
        self.source_url_input = QLineEdit()
        self.source_url_input.setPlaceholderText("来源 URL (可选)")
        tags_row.addWidget(self.source_url_input, 1)
        layout.addLayout(tags_row)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识库...")
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedWidth(64)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)

        self.clear_search_btn = QPushButton("清空")
        self.clear_search_btn.setObjectName("secondaryBtn")
        self.clear_search_btn.setFixedWidth(64)
        self.clear_search_btn.clicked.connect(self._on_clear_search)
        search_row.addWidget(self.clear_search_btn)

        layout.addLayout(search_row)

        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        layout.addWidget(self._status_label)

        # Keep public reference
        self.status_label = self._status_label

        # Browse area
        self.browse_area = QScrollArea()
        self.browse_area.setWidgetResizable(True)
        self.browse_area.setFrameShape(QFrame.NoFrame)
        self.browse_container = QWidget()
        self.browse_layout = QVBoxLayout(self.browse_container)
        self.browse_layout.setAlignment(Qt.AlignTop)
        self.browse_area.setWidget(self.browse_container)
        layout.addWidget(self.browse_area, 1)

    # -- Actions --------------------------------------------------------------

    def _on_add(self) -> None:
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        if not content:
            self._show_status("内容不能为空")
            return
        if self._dao is None:
            self._show_status("数据库未就绪")
            return

        category = self.category_combo.currentText()
        if category == "全部":
            category = ""

        tags_raw = self.tags_input.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

        source_url = self.source_url_input.text().strip()

        item = KnowledgeItem(
            title=title or content[:30],
            content=content,
            source_url=source_url,
            source_type="manual",
            category=category,
            tags=tags,
        )
        spawn_ui(self._save_knowledge(item))

    async def _save_knowledge(self, item: KnowledgeItem) -> None:
        try:
            row_id = await self._dao.insert_knowledge(item)
            # Build the vector index entry for semantic search (P0).
            # Non-fatal: a failure here must not block saving the item.
            indexed = False
            if self._vector_store is not None:
                try:
                    res = await self._vector_store.index_knowledge_item(item)
                    indexed = res.get("chunks", 0) > 0
                except Exception:
                    indexed = False
            self.title_input.clear()
            self.content_input.clear()
            self.tags_input.clear()
            self.source_url_input.clear()
            suffix = "，已建立向量索引" if indexed else ""
            self._show_status(f"已添加 (id={row_id}){suffix}")
            await self._load_browse()
        except Exception as e:
            self._show_status(f"添加失败: {e}")

    def _on_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            self._on_clear_search()
            return
        if self._dao is None:
            self._show_status("数据库未就绪")
            return
        spawn_ui(self._do_search(query))

    async def _do_search(self, query: str) -> None:
        try:
            results = None
            mode = "关键词"
            # Prefer semantic (vector) search when available (P0).
            if self._vector_store is not None:
                try:
                    hits = await self._vector_store.search(query, top_k=20)
                    if hits:
                        results = self._hits_to_items(hits)
                        mode = "语义"
                except Exception:
                    results = None
            # Fall back to lexical search (FTS + LIKE).
            if results is None:
                try:
                    results = await self._dao.search_knowledge(query)
                except Exception:
                    all_items = await self._dao.get_knowledge(limit=100)
                    results = [
                        item for item in all_items
                        if query.lower() in (
                            item.get("title", "") + item.get("content", "") + item.get("tags", "")
                        ).lower()
                    ]
            self._populate_browse(results)
            self._show_status(f"{mode}搜索到 {len(results)} 条结果")
        except Exception as e:
            self._show_status(f"搜索失败: {e}")

    @staticmethod
    def _hits_to_items(hits: list[dict]) -> list[dict]:
        """Shape vector hits into the dict form the browse cards expect."""
        items = []
        for h in hits:
            items.append({
                "title": "",
                "content": h.get("content", ""),
                "category": "",
                "tags": "",
                "source_url": "",
                "created_at": "",
                "_score": h.get("score"),
                "_chunk_id": h.get("chunk_id"),
            })
        return items

    def _on_clear_search(self) -> None:
        self.search_input.clear()
        spawn_ui(self._load_browse())

    async def _load_browse(self, limit: int = 30) -> None:
        if self._dao is None:
            return
        try:
            items = await self._dao.get_knowledge(limit=limit)
            self._populate_browse(items)
        except Exception as e:
            self._show_status(f"加载失败: {e}")

    def _populate_browse(self, items: list[dict]) -> None:
        c = ThemeManager.get_colors()
        # Clear existing
        while self.browse_layout.count():
            child = self.browse_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            placeholder = QLabel("暂无知识条目")
            placeholder.setStyleSheet(
                f"color: {c.text_disabled}; padding: 12px;"
            )
            self.browse_layout.addWidget(placeholder)
            return

        for row in items:
            card = self._make_browse_card(row)
            self.browse_layout.addWidget(card)

    def _make_browse_card(self, row: dict) -> QFrame:
        c = ThemeManager.get_colors()
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {c.bg_secondary}; border-radius: 6px; padding: 8px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(4)

        # Title + category
        title = row.get("title", "")
        category = row.get("category", "")
        category_badge = f"  [{category}]" if category else ""
        title_label = QLabel(f"{title}{category_badge}")
        title_label.setStyleSheet(
            f"color: {c.text_accent}; font-size: 14px; font-weight: bold;"
        )
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)

        # Meta line: date + source
        meta_parts: list[str] = []
        created = row.get("created_at", "")
        if created:
            meta_parts.append(created[:16] if len(created) > 16 else created)
        source_url = row.get("source_url", "")
        if source_url:
            meta_parts.append(f"来源: {source_url[:50]}")
        meta_text = "  ".join(meta_parts)
        if meta_text:
            meta_label = QLabel(meta_text)
            meta_label.setStyleSheet(
                f"color: {c.text_secondary}; font-size: 11px;"
            )
            meta_label.setWordWrap(True)
            card_layout.addWidget(meta_label)

        # Content preview
        content = row.get("content", "")
        preview = content[:300] + ("..." if len(content) > 300 else "")
        content_label = QLabel(preview)
        content_label.setWordWrap(True)
        content_label.setStyleSheet(
            f"color: {c.text_content}; font-size: 13px; padding: 2px 0;"
        )
        card_layout.addWidget(content_label)

        # Tags
        tags_raw = row.get("tags", "")
        if tags_raw:
            try:
                tags = _json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
                if tags:
                    tags_label = QLabel(" | ".join(tags))
                    tags_label.setStyleSheet(
                        f"color: {c.text_tags}; font-size: 11px;"
                    )
                    card_layout.addWidget(tags_label)
            except Exception:
                pass

        # Graph entry (G-P0): vector search hits carry their chunk id.
        chunk_id = row.get("_chunk_id")
        if chunk_id is not None:
            graph_btn = QPushButton("在图谱中探索")
            graph_btn.setObjectName("secondaryBtn")
            graph_btn.setFixedWidth(110)
            graph_btn.clicked.connect(
                lambda checked=False, cid=chunk_id: self.graph_enter_requested.emit(cid)
            )
            card_layout.addWidget(graph_btn)

        return card

    # -- Helpers ---------------------------------------------------------------

    def focus_content(self, content: str, title: str = "") -> None:
        """Show a single source chunk as a card (graph double-click navigation)."""
        item = {
            "title": title or "图谱来源",
            "content": content or "",
            "category": "",
            "tags": "",
            "source_url": "",
            "created_at": "",
        }
        self._populate_browse([item])
        self._show_status("已定位图谱节点的来源内容")

    def _show_status(self, text: str) -> None:
        self.status_label.setText(text)
