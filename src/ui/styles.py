"""Theme stylesheets for the AI Assistant."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    """Named semantic colors for building theme-aware inline stylesheets."""

    # Backgrounds
    bg_deep: str          # app deep background
    bg_primary: str       # sidebar, card backgrounds
    bg_secondary: str     # card bg, hover states
    bg_tertiary: str      # input fields, text areas
    bg_darker: str        # drop zone, recessed areas
    bg_checked: str       # checked/selected toggle bg

    # Borders
    border: str           # standard borders
    border_light: str     # lighter borders (card hover)
    border_focus: str     # focused border / accent border
    divider: str          # divider lines

    # Accent
    accent: str           # primary accent
    accent_hover: str     # accent hover state
    accent_pressed: str   # accent pressed state
    accent_light: str     # accent for light-on-dark text

    # Text
    text_primary: str     # bright text on dark / dark text on light
    text_input: str       # input field text color
    text_content: str     # body/content text
    text_secondary: str   # muted labels
    text_tertiary: str    # even more muted (QQ labels etc.)
    text_disabled: str    # disabled text, placeholder hints
    text_hint: str        # very muted hint text (version label)
    text_hover: str       # hover state text
    text_accent: str      # accent-colored text (titles)
    text_tags: str        # tags text color

    # Status
    success: str
    error: str
    warning: str

    # Button secondary
    btn_secondary_bg: str
    btn_secondary_text: str
    btn_secondary_border: str
    btn_secondary_hover_bg: str
    btn_secondary_hover_text: str


DARK_COLORS = ThemeColors(
    # Backgrounds
    bg_deep="#0f0f17",
    bg_primary="#161622",
    bg_secondary="#1e1e32",
    bg_tertiary="#1a1a2e",
    bg_darker="#12121e",
    bg_checked="#2a2a48",

    # Borders
    border="#2a2a3e",
    border_light="#3a3a5e",
    border_focus="#4f46e5",
    divider="#2a2a3e",

    # Accent
    accent="#4f46e5",
    accent_hover="#5b54e8",
    accent_pressed="#4338ca",
    accent_light="#818cf8",

    # Text
    text_primary="#e0e0e0",
    text_input="#d0d0e0",
    text_content="#c8c8e0",
    text_secondary="#8888a0",
    text_tertiary="#aaaacc",
    text_disabled="#555570",
    text_hint="#444460",
    text_hover="#b0b0c8",
    text_accent="#a8a8d0",
    text_tags="#6666a0",

    # Status
    success="#4caf50",
    error="#f44336",
    warning="#ff9800",

    # Button secondary
    btn_secondary_bg="#3a3a5c",
    btn_secondary_text="#a0a0c0",
    btn_secondary_border="#555580",
    btn_secondary_hover_bg="#5050a0",
    btn_secondary_hover_text="#ffffff",
)


LIGHT_COLORS = ThemeColors(
    # Backgrounds
    bg_deep="#f0f0f0",
    bg_primary="#ffffff",
    bg_secondary="#f5f5f5",
    bg_tertiary="#ffffff",
    bg_darker="#e8e8f0",
    bg_checked="#eef2ff",

    # Borders
    border="#d0d0d0",
    border_light="#c0c0c0",
    border_focus="#4f46e5",
    divider="#e0e0e0",

    # Accent
    accent="#4f46e5",
    accent_hover="#5b54e8",
    accent_pressed="#4338ca",
    accent_light="#6366f1",

    # Text
    text_primary="#333333",
    text_input="#333333",
    text_content="#444444",
    text_secondary="#888888",
    text_tertiary="#999999",
    text_disabled="#aaaaaa",
    text_hint="#999999",
    text_hover="#555555",
    text_accent="#4444aa",
    text_tags="#777777",

    # Status
    success="#4caf50",
    error="#f44336",
    warning="#ff9800",

    # Button secondary
    btn_secondary_bg="#e5e5e5",
    btn_secondary_text="#555555",
    btn_secondary_border="#d0d0d0",
    btn_secondary_hover_bg="#f5f5f5",
    btn_secondary_hover_text="#333333",
)


DARK_THEME = """
/* === Global === */
* {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0f0f17;
}

QWidget {
    background-color: #0f0f17;
    color: #e0e0e0;
}

/* === Sidebar === */
#sidebar {
    background-color: #161622;
    border-right: 1px solid #2a2a3e;
}

#sidebar QPushButton,
#sidebar QToolButton {
    background-color: transparent;
    color: #8888a0;
    border: none;
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
    font-size: 11px;
    min-height: 36px;
}

#sidebar QPushButton:hover,
#sidebar QToolButton:hover {
    background-color: #1e1e32;
    color: #b0b0c8;
}

#sidebar QPushButton:checked,
#sidebar QToolButton:checked {
    background-color: #2a2a48;
    color: #818cf8;
}

#sidebar QToolButton::icon {
    padding-bottom: 2px;
}

#sidebarTitle {
    color: #818cf8;
    font-size: 15px;
    font-weight: bold;
    padding: 6px 0;
}

/* === Content Area === */
#contentArea {
    background-color: #0f0f17;
}

/* === Input Fields === */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 6px 12px;
    selection-background-color: #4f46e5;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #4f46e5;
}

QLineEdit {
    min-height: 20px;
}

/* === Buttons === */
QPushButton {
    background-color: #4f46e5;
    color: white;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 20px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #5b54e8;
}

QPushButton:pressed {
    background-color: #4338ca;
}

QPushButton:disabled {
    background-color: #2a2a3e;
    color: #555570;
}

QPushButton#secondaryBtn {
    background-color: #1e1e32;
    color: #b0b0c8;
    border: 1px solid #2a2a3e;
}

QPushButton#secondaryBtn:hover {
    background-color: #2a2a48;
    border-color: #4f46e5;
}

QPushButton#dangerBtn {
    background-color: #dc2626;
}

QPushButton#dangerBtn:hover {
    background-color: #ef4444;
}

/* === Combo Box === */
QComboBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #4f46e5;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3e;
    selection-background-color: #2a2a48;
    border-radius: 8px;
    padding: 4px;
}

/* === Spin Box === */
QSpinBox, QDoubleSpinBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 6px 12px;
    /* 17 + 12 padding + 2 border + 3 intrinsic spin metrics = 34px, matches QLineEdit */
    min-height: 17px;
    selection-background-color: #4f46e5;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #4f46e5;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #4f46e5;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    border: none;
    border-left: 1px solid #2a2a3e;
    border-top-right-radius: 8px;
    width: 20px;
    background-color: transparent;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    border: none;
    border-left: 1px solid #2a2a3e;
    border-bottom-right-radius: 8px;
    width: 20px;
    background-color: transparent;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #2a2a48;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #8888a0;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8888a0;
}

QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {
    border-bottom-color: #818cf8;
}

QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {
    border-top-color: #818cf8;
}

/* === Table === */
QTableWidget {
    background-color: #161622;
    alternate-background-color: #1a1a2e;
    color: #c8c8e0;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    gridline-color: #2a2a3e;
    selection-background-color: #2a2a48;
    selection-color: #e0e0e0;
}

QTableWidget::item {
    padding: 4px 8px;
}

QTableWidget::item:selected {
    background-color: #2a2a48;
}

QHeaderView {
    background-color: #161622;
    border: none;
}

QHeaderView::section {
    background-color: #1e1e32;
    color: #8888a0;
    border: none;
    border-bottom: 1px solid #2a2a3e;
    border-right: 1px solid #2a2a3e;
    padding: 6px 8px;
    font-weight: bold;
}

QTableCornerButton::section {
    background-color: #1e1e32;
    border: none;
}

/* === Scroll Bar === */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #2a2a3e;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3a3a5e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background-color: #2a2a3e;
    border-radius: 4px;
    min-width: 30px;
}

/* === Group Box === */
QGroupBox {
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #b0b0c8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* === CheckBox === */
QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #2a2a3e;
    background-color: #1a1a2e;
}

QCheckBox::indicator:checked {
    background-color: #4f46e5;
    border-color: #4f46e5;
}

/* === RadioButton === */
QRadioButton {
    spacing: 8px;
    color: #e0e0e0;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 10px;
    border: 2px solid #2a2a3e;
    background-color: #1a1a2e;
}

QRadioButton::indicator:hover {
    border-color: #4f46e5;
}

QRadioButton::indicator:checked {
    border: 2px solid #4f46e5;
    background-color: #4f46e5;
    image: url(none);
}

QRadioButton::indicator:checked {
    background-color: qradialgradient(
        cx: 0.5, cy: 0.5,
        radius: 0.4,
        fx: 0.5, fy: 0.5,
        stop: 0 #ffffff,
        stop: 0.8 #ffffff,
        stop: 0.81 #4f46e5,
        stop: 1 #4f46e5
    );
    border-color: #4f46e5;
}

/* === Status Bar === */
QStatusBar {
    background-color: #161622;
    color: #6c7086;
    border-top: 1px solid #2a2a3e;
    font-size: 12px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #2a2a3e;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* === ToolTip === */
QToolTip {
    background-color: #1e1e32;
    color: #e0e0e0;
    border: 1px solid #2a2a3e;
    border-radius: 6px;
    padding: 6px 10px;
}
"""


LIGHT_THEME = """
/* === Global === */
* {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #f0f0f0;
}

QWidget {
    background-color: #f0f0f0;
    color: #333333;
}

/* === Sidebar === */
#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}

#sidebar QPushButton,
#sidebar QToolButton {
    background-color: transparent;
    color: #888888;
    border: none;
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
    font-size: 11px;
    min-height: 36px;
}

#sidebar QPushButton:hover,
#sidebar QToolButton:hover {
    background-color: #f0f0f5;
    color: #555555;
}

#sidebar QPushButton:checked,
#sidebar QToolButton:checked {
    background-color: #eef2ff;
    color: #4f46e5;
}

#sidebarTitle {
    color: #4f46e5;
    font-size: 15px;
    font-weight: bold;
    padding: 6px 0;
}

/* === Content Area === */
#contentArea {
    background-color: #f0f0f0;
}

/* === Input Fields === */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 6px 12px;
    selection-background-color: #4f46e5;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #4f46e5;
}

QLineEdit {
    min-height: 20px;
}

/* === Buttons === */
QPushButton {
    background-color: #4f46e5;
    color: white;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 20px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #5b54e8;
}

QPushButton:pressed {
    background-color: #4338ca;
}

QPushButton:disabled {
    background-color: #e5e5e5;
    color: #aaaaaa;
}

QPushButton#secondaryBtn {
    background-color: #ffffff;
    color: #555555;
    border: 1px solid #d0d0d0;
}

QPushButton#secondaryBtn:hover {
    background-color: #f5f5f5;
    border-color: #4f46e5;
}

QPushButton#dangerBtn {
    background-color: #dc2626;
}

QPushButton#dangerBtn:hover {
    background-color: #ef4444;
}

/* === Combo Box === */
QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #4f46e5;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    selection-background-color: #eef2ff;
    border-radius: 8px;
    padding: 4px;
}

/* === Spin Box === */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 6px 12px;
    /* 17 + 12 padding + 2 border + 3 intrinsic spin metrics = 34px, matches QLineEdit */
    min-height: 17px;
    selection-background-color: #4f46e5;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #4f46e5;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #4f46e5;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    border: none;
    border-left: 1px solid #d0d0d0;
    border-top-right-radius: 8px;
    width: 20px;
    background-color: transparent;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    border: none;
    border-left: 1px solid #d0d0d0;
    border-bottom-right-radius: 8px;
    width: 20px;
    background-color: transparent;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #f0f0f5;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #888888;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #888888;
}

QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {
    border-bottom-color: #4f46e5;
}

QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {
    border-top-color: #4f46e5;
}

/* === Table === */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f5f5f5;
    color: #444444;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    gridline-color: #e0e0e0;
    selection-background-color: #eef2ff;
    selection-color: #333333;
}

QTableWidget::item {
    padding: 4px 8px;
}

QTableWidget::item:selected {
    background-color: #eef2ff;
}

QHeaderView {
    background-color: #ffffff;
    border: none;
}

QHeaderView::section {
    background-color: #f5f5f5;
    color: #888888;
    border: none;
    border-bottom: 1px solid #d0d0d0;
    border-right: 1px solid #e0e0e0;
    padding: 6px 8px;
    font-weight: bold;
}

QTableCornerButton::section {
    background-color: #f5f5f5;
    border: none;
}

/* === Scroll Bar === */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #c8c8c8;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background-color: #c8c8c8;
    border-radius: 4px;
    min-width: 30px;
}

/* === Group Box === */
QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #555555;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* === CheckBox === */
QCheckBox {
    spacing: 8px;
    color: #333333;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #d0d0d0;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #4f46e5;
    border-color: #4f46e5;
}

/* === RadioButton === */
QRadioButton {
    spacing: 8px;
    color: #333333;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 10px;
    border: 2px solid #d0d0d0;
    background-color: #ffffff;
}

QRadioButton::indicator:hover {
    border-color: #4f46e5;
}

QRadioButton::indicator:checked {
    border: 2px solid #4f46e5;
    background-color: #4f46e5;
    image: url(none);
}

QRadioButton::indicator:checked {
    background-color: qradialgradient(
        cx: 0.5, cy: 0.5,
        radius: 0.4,
        fx: 0.5, fy: 0.5,
        stop: 0 #ffffff,
        stop: 0.8 #ffffff,
        stop: 0.81 #4f46e5,
        stop: 1 #4f46e5
    );
    border-color: #4f46e5;
}

/* === Status Bar === */
QStatusBar {
    background-color: #ffffff;
    color: #888888;
    border-top: 1px solid #e0e0e0;
    font-size: 12px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #d0d0d0;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* === ToolTip === */
QToolTip {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 6px 10px;
}
"""


THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


class ThemeManager:
    _current = "dark"
    _config = None
    _panels: list = []  # weak references to panels that have _apply_theme()

    # -- Color access ----------------------------------------------------------

    @classmethod
    def get_colors(cls) -> ThemeColors:
        """Return the ThemeColors instance for the current theme."""
        return DARK_COLORS if cls._current == "dark" else LIGHT_COLORS

    @classmethod
    def color(cls, name: str) -> str:
        """Quick access: ThemeManager.color('bg_primary')."""
        c = cls.get_colors()
        val = getattr(c, name, None)
        if val is None:
            raise AttributeError(f"ThemeColors has no attribute '{name}'")
        return val

    # -- Panel registration ----------------------------------------------------

    @classmethod
    def register_panel(cls, panel) -> None:
        """Register a panel that supports _apply_theme()."""
        cls._panels.append(panel)

    @classmethod
    def unregister_panel(cls, panel) -> None:
        try:
            cls._panels.remove(panel)
        except ValueError:
            pass

    # -- Theme switching -------------------------------------------------------

    @classmethod
    def apply(cls, theme_name: str = "dark") -> None:
        from PySide6.QtWidgets import QApplication
        theme = THEMES.get(theme_name, DARK_THEME)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme)
        cls._current = theme_name
        cls._refresh_all_panels()

    @classmethod
    def toggle(cls) -> None:
        new = "light" if cls._current == "dark" else "dark"
        cls.apply(new)
        cls._save_preference(new)

    @classmethod
    def current(cls) -> str:
        return cls._current

    @classmethod
    def _refresh_all_panels(cls) -> None:
        """Call _apply_theme() on every registered panel."""
        dead = []
        for ref in cls._panels:
            # Support both weak references and direct references
            panel = ref() if callable(ref) else ref
            if panel is None or not hasattr(panel, "_apply_theme"):
                dead.append(ref)
                continue
            try:
                panel._apply_theme()
            except Exception:
                pass
        for d in dead:
            try:
                cls._panels.remove(d)
            except ValueError:
                pass

    # -- Config persistence ----------------------------------------------------

    @classmethod
    def set_config(cls, config) -> None:
        """Store config reference for saving theme preference."""
        cls._config = config

    @classmethod
    def _save_preference(cls, theme_name: str) -> None:
        if cls._config:
            cls._config.set("ui.theme", theme_name)
            cls._config.save()

    @classmethod
    def load_from_config(cls, config) -> str:
        """Load saved theme preference from config and apply it. Returns theme name."""
        cls._config = config
        theme = config.get("ui.theme", "dark")
        if theme not in THEMES:
            theme = "dark"
        cls.apply(theme)
        return theme
