"""Collection-query builder panel."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _QueryRow(QWidget):
    def __init__(self, op="filter", text="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.op = QComboBox()
        self.op.addItems(["filter", "exclude"])
        self.op.setCurrentText(op)
        self.tokens = QLineEdit(text)
        self.tokens.setPlaceholderText("field__lookup=value  field2=value2")
        layout.addWidget(self.op)
        layout.addWidget(self.tokens)

    def value(self):
        return (self.op.currentText(), self.tokens.text())


class QueryPanel(QWidget):
    runRequested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        layout = QVBoxLayout(self)

        self._rows_layout = QVBoxLayout()
        layout.addLayout(self._rows_layout)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("+ Condition")
        self.add_button.clicked.connect(lambda: self.add_row())
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self._on_run)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)

        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        layout.addWidget(self.results)

        self.add_row()

    def add_row(self, op="filter", text=""):
        row = _QueryRow(op, text)
        self._rows.append(row)
        self._rows_layout.addWidget(row)

    def set_rows(self, rows):
        for row in self._rows:
            row.setParent(None)
        self._rows = []
        for op, text in rows:
            self.add_row(op, text)
        if not self._rows:
            self.add_row()

    def rows(self):
        return [row.value() for row in self._rows]

    def set_results_text(self, text):
        self.results.setPlainText(text)

    def _on_run(self):
        self.runRequested.emit(self.rows())
