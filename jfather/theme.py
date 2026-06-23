"""Qt stylesheets for jfather, scoped to keep native scrollbars."""

STYLESHEET = """
QMainWindow, QToolBar, QStatusBar, QLabel { background: #1a1b26; color: #c0caf5; }
QToolBar { border: none; spacing: 6px; padding: 4px; }
QStatusBar { background: #1f2335; }
QPlainTextEdit, QTreeView, QTableView, QListWidget, QLineEdit, QComboBox {
    background: #16161e; color: #c0caf5; border: 1px solid #2a2e42;
    border-radius: 6px; selection-background-color: #364a82;
}
QPushButton {
    background: #2a2e42; color: #c0caf5; border: none; border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { background: #3b4261; }
QPushButton:disabled { background: #20222e; color: #565a6e; }
QHeaderView::section { background: #1f2335; color: #c0caf5; border: none; padding: 4px; }
"""

LIGHT_STYLESHEET = """
QMainWindow, QToolBar, QStatusBar, QLabel { background: #f5f5f7; color: #1d1d1f; }
QToolBar { border: none; spacing: 6px; padding: 4px; }
QStatusBar { background: #ececf0; }
QPlainTextEdit, QTreeView, QTableView, QListWidget, QLineEdit, QComboBox {
    background: #ffffff; color: #1d1d1f; border: 1px solid #d2d2d7;
    border-radius: 6px; selection-background-color: #b3d4fc;
}
QPushButton {
    background: #e8e8ed; color: #1d1d1f; border: none; border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { background: #dcdce1; }
QPushButton:disabled { background: #f0f0f2; color: #b0b0b5; }
QHeaderView::section { background: #ececf0; color: #1d1d1f; border: none; padding: 4px; }
"""
