"""Dark theme stylesheet for the AI Assistant."""

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

#sidebar QPushButton {
    background-color: transparent;
    color: #8888a0;
    border: none;
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
    font-size: 11px;
    min-height: 36px;
}

#sidebar QPushButton:hover {
    background-color: #1e1e32;
    color: #b0b0c8;
}

#sidebar QPushButton:checked {
    background-color: #2a2a48;
    color: #818cf8;
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
    padding: 8px 12px;
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
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
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


class ThemeManager:
    _current = "dark"

    @classmethod
    def apply(cls, theme_name: str = "dark") -> None:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(DARK_THEME)
        cls._current = theme_name

    @classmethod
    def toggle(cls) -> None:
        new = "light" if cls._current == "dark" else "dark"
        cls.apply(new)

    @classmethod
    def current(cls) -> str:
        return cls._current
