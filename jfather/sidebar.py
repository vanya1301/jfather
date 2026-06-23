"""Sidebar listing open documents."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DocumentSidebar(QWidget):
    documentSelected = Signal(int)
    documentCloseRequested = Signal(int)
    newRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._suppress = False
        self.setObjectName("documentSidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list)

        self.new_button = QPushButton("\uff0b New")
        self.new_button.clicked.connect(self.newRequested.emit)
        layout.addWidget(self.new_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self._on_close_clicked)
        layout.addWidget(self.close_button)

        self.setMaximumWidth(240)

    def _on_row_changed(self, row):
        if not self._suppress and row >= 0:
            self.documentSelected.emit(row)

    def _on_close_clicked(self):
        row = self.list.currentRow()
        if row >= 0:
            self.documentCloseRequested.emit(row)

    def refresh(self, manager):
        self._suppress = True
        self.list.clear()
        for doc in manager.documents:
            label = ("\u2022 " if doc.dirty else "") + doc.name
            self.list.addItem(QListWidgetItem(label))
        if 0 <= manager.active_index < len(manager.documents):
            self.list.setCurrentRow(manager.active_index)
        self._suppress = False
