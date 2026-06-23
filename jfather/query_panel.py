"""Collection-query builder panel with structured and text modes."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import query


class _TextRow(QWidget):
    def __init__(self, op="filter", text="", field_names=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.op = QComboBox()
        self.op.addItems(["filter", "exclude"])
        self.op.setCurrentText(op)
        self.tokens = QLineEdit(text)
        self.tokens.setPlaceholderText("field__lookup=value  field2=value2")
        if field_names:
            completer = QCompleter(list(field_names))
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.tokens.setCompleter(completer)
        layout.addWidget(self.op)
        layout.addWidget(self.tokens)

    def as_text(self):
        return (self.op.currentText(), self.tokens.text())


class _StructuredRow(QWidget):
    def __init__(self, op="filter", field="", lookup="exact", value="",
                 field_names=None, lookups=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.op = QComboBox()
        self.op.addItems(["filter", "exclude"])
        self.op.setCurrentText(op)
        self.field = QComboBox()
        self.field.setEditable(True)
        if field_names:
            self.field.addItems(list(field_names))
        self.field.setCurrentText(field)
        self.lookup = QComboBox()
        self.lookup.addItems(["exact"] + list(lookups or []))
        self.lookup.setCurrentText(lookup)
        self.value = QLineEdit(value)
        self.value.setPlaceholderText("value")
        layout.addWidget(self.op)
        layout.addWidget(self.field)
        layout.addWidget(self.lookup)
        layout.addWidget(self.value)

    def _key(self):
        field = self.field.currentText().strip()
        lookup = self.lookup.currentText()
        return field if lookup == "exact" else f"{field}__{lookup}"

    def as_text(self):
        return (self.op.currentText(), f"{self._key()}={self.value.text()}")

    def as_kwargs(self):
        return (self.op.currentText(),
                {self._key(): query.coerce_value(self.value.text())})


class QueryPanel(QWidget):
    runRequested = Signal()

    def __init__(self, get_field_names=None, lookups=None, parent=None):
        super().__init__(parent)
        self._get_field_names = get_field_names or (lambda: [])
        self.lookups = (
            list(lookups) if lookups is not None else query.available_lookups()
        )
        self._mode = "structured"
        self._text_rows = []
        self._structured_rows = []

        layout = QVBoxLayout(self)

        toggle = QHBoxLayout()
        self.structured_button = QPushButton("Structured")
        self.structured_button.setCheckable(True)
        self.structured_button.setChecked(True)
        self.structured_button.clicked.connect(lambda: self.set_mode("structured"))
        self.text_button = QPushButton("Text")
        self.text_button.setCheckable(True)
        self.text_button.clicked.connect(lambda: self.set_mode("text"))
        toggle.addWidget(self.structured_button)
        toggle.addWidget(self.text_button)
        toggle.addStretch()
        layout.addLayout(toggle)

        self.stack = QStackedWidget()
        self._structured_page = QWidget()
        self._structured_layout = QVBoxLayout(self._structured_page)
        self._structured_layout.setContentsMargins(0, 0, 0, 0)
        self._text_page = QWidget()
        self._text_layout = QVBoxLayout(self._text_page)
        self._text_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self._structured_page)
        self.stack.addWidget(self._text_page)
        layout.addWidget(self.stack)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("+ Condition")
        self.add_button.clicked.connect(self._on_add)
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.runRequested.emit)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)

        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        layout.addWidget(self.results)

        self.set_rows([("filter", "")])

    # ---- mode ----
    def mode(self):
        return self._mode

    def set_mode(self, mode):
        if mode not in ("structured", "text"):
            return
        rows = self.rows()
        self._mode = mode
        self.structured_button.setChecked(mode == "structured")
        self.text_button.setChecked(mode == "text")
        self.stack.setCurrentIndex(0 if mode == "structured" else 1)
        self._populate(rows)

    # ---- row management ----
    def _clear_layout(self, layout, holder):
        holder.clear()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _populate(self, rows):
        field_names = self._get_field_names()
        if self._mode == "structured":
            self._clear_layout(self._structured_layout, self._structured_rows)
            for op, text in rows:
                for token in (text.split() or [""]):
                    field, lookup, value = self._parse_token_for_structured(token)
                    row = _StructuredRow(op, field, lookup, value,
                                         field_names, self.lookups)
                    self._structured_rows.append(row)
                    self._structured_layout.addWidget(row)
            if not self._structured_rows:
                self._add_structured_row(field_names)
        else:
            self._clear_layout(self._text_layout, self._text_rows)
            for op, text in rows:
                row = _TextRow(op, text, field_names)
                self._text_rows.append(row)
                self._text_layout.addWidget(row)
            if not self._text_rows:
                self._add_text_row(field_names)

    def _parse_token_for_structured(self, token):
        if "=" not in token:
            return (token.strip(), "exact", "")
        key, _, value = token.partition("=")
        field, lookup = query.split_key(key.strip(), self.lookups)
        return (field, lookup, value.strip())

    def _add_text_row(self, field_names):
        row = _TextRow("filter", "", field_names)
        self._text_rows.append(row)
        self._text_layout.addWidget(row)

    def _add_structured_row(self, field_names):
        row = _StructuredRow("filter", "", "exact", "", field_names, self.lookups)
        self._structured_rows.append(row)
        self._structured_layout.addWidget(row)

    def _on_add(self):
        field_names = self._get_field_names()
        if self._mode == "structured":
            self._add_structured_row(field_names)
        else:
            self._add_text_row(field_names)

    # ---- data access ----
    def _active_rows(self):
        return self._structured_rows if self._mode == "structured" else self._text_rows

    def rows(self):
        return [row.as_text() for row in self._active_rows()]

    def set_rows(self, rows):
        rows = list(rows) if rows else [("filter", "")]
        self._populate(rows)

    def current_rows(self):
        result = []
        if self._mode == "structured":
            for row in self._structured_rows:
                result.append(row.as_kwargs())
        else:
            for row in self._text_rows:
                op, text = row.as_text()
                result.append((op, query.parse_tokens(text)))
        return result

    def set_results_text(self, text):
        self.results.setPlainText(text)

    def set_run_enabled(self, enabled):
        self.run_button.setEnabled(enabled)
