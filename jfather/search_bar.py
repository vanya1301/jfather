"""Search bar for navigating tree matches."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class SearchBar(QWidget):
    queryChanged = Signal(str)
    nextRequested = Signal()
    prevRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search keys and values\u2026")
        self.input.textChanged.connect(self.queryChanged.emit)

        self.count_label = QLabel("0/0")

        self.prev_button = QPushButton("\u2191")
        self.prev_button.setFixedWidth(32)
        self.prev_button.clicked.connect(self.prevRequested.emit)

        self.next_button = QPushButton("\u2193")
        self.next_button.setFixedWidth(32)
        self.next_button.clicked.connect(self.nextRequested.emit)

        layout.addWidget(self.input)
        layout.addWidget(self.count_label)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)

    def set_count(self, current, total):
        self.count_label.setText(f"{current}/{total}")
