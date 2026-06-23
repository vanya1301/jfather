"""Breadcrumb bar showing and navigating the focus path."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class Breadcrumb(QWidget):
    pathChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = []
        self.buttons = []
        self.hint = QLabel("Double-click a row or node to focus")
        self.hint.setObjectName("drillHint")
        self.hint.hide()
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(2)
        self.set_path([])

    def path(self):
        return list(self._path)

    def _clear(self):
        self.buttons = []
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self.hint:
                widget.deleteLater()

    def set_path(self, path):
        self._path = list(path)
        self._clear()
        crumbs = [("root", [])]
        prefix = []
        for key in self._path:
            prefix = prefix + [key]
            label = f"[{key}]" if isinstance(key, int) else str(key)
            crumbs.append((label, list(prefix)))
        for position, (label, target) in enumerate(crumbs):
            if position > 0:
                self._layout.addWidget(QLabel("\u203a"))
            button = QPushButton(label)
            button.setObjectName("breadcrumbPill")
            button.setFlat(True)
            button.clicked.connect(
                lambda _checked=False, t=target: self.pathChanged.emit(t)
            )
            self.buttons.append(button)
            self._layout.addWidget(button)
        self.hint.setVisible(len(self._path) == 0)
        self._layout.addWidget(self.hint)
        self._layout.addStretch()
