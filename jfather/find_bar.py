"""In-editor find bar."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class _FindInput(QLineEdit):
    escapePressed = Signal()
    findNext = Signal()
    findPrev = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.escapePressed.emit()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.findPrev.emit()
            else:
                self.findNext.emit()
            return
        super().keyPressEvent(event)


class FindBar(QWidget):
    queryChanged = Signal(str)
    nextRequested = Signal()
    prevRequested = Signal()
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = _FindInput()
        self.input.setPlaceholderText("Find\u2026")
        self.input.textChanged.connect(self.queryChanged.emit)
        self.input.escapePressed.connect(self.closed.emit)
        self.input.findNext.connect(self.nextRequested.emit)
        self.input.findPrev.connect(self.prevRequested.emit)

        self.count_label = QLabel("0/0")
        self.prev_button = QPushButton("\u2191")
        self.prev_button.setFixedWidth(32)
        self.prev_button.clicked.connect(self.prevRequested.emit)
        self.next_button = QPushButton("\u2193")
        self.next_button.setFixedWidth(32)
        self.next_button.clicked.connect(self.nextRequested.emit)
        self.close_button = QPushButton("\u2715")
        self.close_button.setFixedWidth(32)
        self.close_button.clicked.connect(self.closed.emit)

        for widget in (
            self.input,
            self.count_label,
            self.prev_button,
            self.next_button,
            self.close_button,
        ):
            layout.addWidget(widget)

    def set_count(self, current, total):
        self.count_label.setText(f"{current}/{total}")
