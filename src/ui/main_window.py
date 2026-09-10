"""Main window with sidebar navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QPainter, QColor, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QLabel, QButtonGroup,
    QPushButton, QFrame, QSizePolicy, QSpacerItem, QToolButton,
)

from .styles import ThemeManager
from .chat_panel import ChatPanel
from .document_panel import DocumentPanel
from .search_panel import SearchPanel
from .diary_panel import DiaryPanel
from .knowledge_panel import KnowledgePanel
from .settings_panel import SettingsPanel
from .chat_reader_panel import ChatReaderPanel
from .icons import get_nav_icons
from src.storage.dao import DAO


def _make_nav_button(icon: QIcon, label: str, tooltip: str) -> QToolButton:
    """Create a sidebar navigation button with icon above text."""
    btn = QToolButton()
    btn.setIcon(icon)
    btn.setText(label)
    btn.setToolTip(tooltip)
    btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    btn.setIconSize(QSize(22, 22))
    btn.setCheckable(True)
    btn.setFixedWidth(72)
    btn.setMinimumHeight(56)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


class MainWindow(QMainWindow):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(860, 560)

        cfg = app.config if app else None
        w = cfg.get("ui.main_window.width", 960) if cfg else 960
        h = cfg.get("ui.main_window.height", 640) if cfg else 640
        self.resize(w, h)

        self._setup_ui()
        self._setup_status_bar()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(80)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(4, 12, 4, 4)
        sidebar_layout.setSpacing(4)

        # Logo
        title = QLabel("AI")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title)

        sidebar_layout.addSpacing(8)

        # Nav buttons
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QToolButton] = []

        for icon, label, tooltip in get_nav_icons():
            btn = _make_nav_button(icon, label, tooltip)
            self._nav_group.addButton(btn)
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Sidebar version label
        ver = QLabel("v0.1")
        ver.setAlignment(Qt.AlignCenter)
        self._ver_label = ver
        ver.setStyleSheet(f"color: {ThemeManager.color('text_hint')}; font-size: 10px;")
        sidebar_layout.addWidget(ver)

        root_layout.addWidget(sidebar)

        # --- Content ---
        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack)

        # Create panels
        self.chat_panel = ChatPanel(app=self.app)
        self.search_panel = SearchPanel(app=self.app)
        self.doc_panel = DocumentPanel(app=self.app)
        self.reader_panel = ChatReaderPanel(app=self.app)
        self.diary_panel = DiaryPanel(app=self.app)
        self.knowledge_panel = KnowledgePanel(app=self.app)
        self.settings_panel = SettingsPanel(app=self.app)

        self._panels = [
            self.chat_panel,
            self.search_panel,
            self.doc_panel,
            self.reader_panel,
            self.diary_panel,
            self.knowledge_panel,
            self.settings_panel,
        ]

        for panel in self._panels:
            self._stack.addWidget(panel)

        # Wire navigation
        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))

        # Wire settings saved signal to refresh chat panel
        self.settings_panel.settings_saved.connect(self.chat_panel.load_models_from_config)

        root_layout.addWidget(content_widget, 1)

        # Default to chat page
        self._switch_page(0)

        # Initial load of models for chat panel
        self.chat_panel.load_models_from_config()

        # Register main window for theme refresh
        ThemeManager.register_panel(self)

    def _apply_theme(self) -> None:
        """Update main window inline styles when theme changes."""
        c = ThemeManager.get_colors()
        self._ver_label.setStyleSheet(f"color: {c.text_hint}; font-size: 10px;")

    def set_dao(self, dao: DAO) -> None:
        """Pass the DAO instance to panels that need database access."""
        self.chat_panel.set_dao(dao)
        self.diary_panel.set_dao(dao)
        self.knowledge_panel.set_dao(dao)

    def set_backup_manager(self, backup_mgr) -> None:
        """Pass the BackupManager instance to the settings panel."""
        self.settings_panel.set_backup_manager(backup_mgr)

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def _setup_status_bar(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("就绪")

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
