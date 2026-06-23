"""Qt stylesheets for jfather (flat modern dark/light)."""

STYLESHEET = """
QWidget { background: #1a1b26; color: #c0caf5; font-size: 13px; }
QPlainTextEdit, QTreeView, QListWidget, QLineEdit {
    background: #16161e; border: 1px solid #2a2e42; border-radius: 6px;
    selection-background-color: #364a82;
}
QPushButton {
    background: #2a2e42; border: none; border-radius: 6px; padding: 6px 12px;
}
QPushButton:hover { background: #3b4261; }
QToolBar { background: #1a1b26; border: none; spacing: 6px; padding: 4px; }
QHeaderView::section { background: #1f2335; border: none; padding: 4px; }
QStatusBar { background: #1f2335; }
"""

LIGHT_STYLESHEET = """
QWidget { background: #f5f5f7; color: #1d1d1f; font-size: 13px; }
QPlainTextEdit, QTreeView, QListWidget, QLineEdit {
    background: #ffffff; border: 1px solid #d2d2d7; border-radius: 6px;
    selection-background-color: #b3d4fc;
}
QPushButton {
    background: #e8e8ed; border: none; border-radius: 6px; padding: 6px 12px;
}
QPushButton:hover { background: #dcdce1; }
QToolBar { background: #f5f5f7; border: none; spacing: 6px; padding: 4px; }
QHeaderView::section { background: #ececf0; border: none; padding: 4px; }
QStatusBar { background: #ececf0; }
"""
