"""Qt stylesheet + font constants for jfather (single warm dark theme).

Scoped to concrete widget classes / object names so native scrollbars and
other OS controls render normally (no universal QWidget or QScrollBar rules).
"""

UI_FONT_FAMILY = "Inter, SF Pro Text, Segoe UI, sans-serif"
MONO_FONT_FAMILY = "Menlo, SF Mono, Consolas, monospace"

# Warm-neutral dark palette.
_BG = "#1c1b1a"
_PANEL = "#161514"
_SIDEBAR = "#211f1d"
_BORDER = "#33302c"
_TEXT = "#e6e1da"
_MUTED = "#9a948c"
_ACCENT = "#7aa2f7"
_BTN = "#2c2925"
_BTN_HOVER = "#3a352f"
_BTN_DISABLED_BG = "#242220"
_BTN_DISABLED_FG = "#5b554d"
_SELECTION = "#3a4a6b"

STYLESHEET = f"""
QMainWindow, QToolBar, QStatusBar, QLabel {{
    background: {_BG}; color: {_TEXT};
    font-family: {UI_FONT_FAMILY};
}}
QToolBar {{ border: none; spacing: 10px; padding: 8px 12px; }}
QToolBar::separator {{ background: {_BORDER}; width: 1px; margin: 4px 6px; }}
QStatusBar {{ background: {_PANEL}; color: {_MUTED}; padding: 4px 10px; }}

QPlainTextEdit, QTreeView, QTableView, QListWidget, QLineEdit, QComboBox {{
    background: {_PANEL}; color: {_TEXT};
    border: 1px solid {_BORDER}; border-radius: 8px;
    selection-background-color: {_SELECTION};
    font-family: {UI_FONT_FAMILY};
    padding: 2px;
}}
QLineEdit {{ padding: 6px 10px; }}
QComboBox {{ padding: 4px 8px; }}

QListWidget {{ outline: none; }}
QListWidget::item {{ padding: 7px 10px; border-radius: 6px; }}
QListWidget::item:selected {{ background: {_BTN_HOVER}; color: {_TEXT}; }}

QWidget#documentSidebar {{ background: {_SIDEBAR}; }}

QPushButton {{
    background: {_BTN}; color: {_TEXT}; border: none; border-radius: 8px;
    padding: 7px 14px; font-family: {UI_FONT_FAMILY};
}}
QPushButton:hover {{ background: {_BTN_HOVER}; }}
QPushButton:disabled {{ background: {_BTN_DISABLED_BG}; color: {_BTN_DISABLED_FG}; }}

QPushButton#breadcrumbPill {{
    background: {_BTN}; border-radius: 11px; padding: 4px 12px; color: {_TEXT};
}}
QPushButton#breadcrumbPill:hover {{ background: {_BTN_HOVER}; }}

QLabel#drillHint {{ color: {_MUTED}; font-style: italic; padding: 0 8px; }}

QHeaderView::section {{
    background: {_PANEL}; color: {_TEXT}; border: none;
    border-bottom: 1px solid {_BORDER}; padding: 6px 8px;
}}
"""
