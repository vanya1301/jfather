"""Collection-query builder panel with structured and text modes."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import query, theme

# Human-readable, symbol-prefixed labels shown in the operator dropdown.
# Combo *data* keeps the raw value ("filter"/"exclude") used to build queries.
OP_LABELS = {
    "filter": "\u2713 Filter",
    "exclude": "\u2715 Exclude",
}

# Human-readable, symbol-prefixed labels shown in the lookup dropdown.
# Combo *data* keeps the raw lookup key ("gt", "icontains", ...) so query
# building and persistence are unchanged.
LOOKUP_LABELS = {
    "exact": "= Equals",
    "iexact": "\u2248 Equals (ignore case)",
    "contains": "\u220b Contains",
    "icontains": "\u220b Contains (ignore case)",
    "startswith": "^ Starts with",
    "istartswith": "^ Starts with (ignore case)",
    "endswith": "$ Ends with",
    "iendswith": "$ Ends with (ignore case)",
    "regex": ".* Matches regex",
    "iregex": ".* Matches regex (ignore case)",
    "gt": "> Greater than",
    "gte": "\u2265 Greater than or equal",
    "lt": "< Less than",
    "lte": "\u2264 Less than or equal",
    "not": "\u2260 Not equal",
    "in": "\u2208 In list",
    "in_range": "\u2194 In range",
    "exists": "\u2203 Exists",
    "isnull": "\u2205 Is null",
}


# Extra popup width beyond the longest label: item padding + check indicator
# + scrollbar, so readable labels are never clipped.
_POPUP_PADDING_PX = 64


def _lookup_label(key):
    """Readable label for a lookup key, falling back to the raw key."""
    return LOOKUP_LABELS.get(key, key)


def _select_data(combo, value):
    """Select the combo entry whose data == value (index 0 if not found)."""
    index = combo.findData(value)
    combo.setCurrentIndex(index if index >= 0 else 0)


def _fit_popup_to_contents(combo):
    """Widen the dropdown popup so long labels are not clipped/elided."""
    view = combo.view()
    view.setTextElideMode(Qt.ElideNone)
    metrics = combo.fontMetrics()
    longest = max(
        (combo.itemText(i) for i in range(combo.count())),
        key=len,
        default="",
    )
    view.setMinimumWidth(metrics.horizontalAdvance(longest) + _POPUP_PADDING_PX)


class _TextRow(QWidget):
    def __init__(self, op="filter", text="", field_names=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.op = QComboBox()
        for value in ("filter", "exclude"):
            self.op.addItem(OP_LABELS[value], value)
        _select_data(self.op, op)
        _fit_popup_to_contents(self.op)
        self.tokens = QLineEdit(text)
        self.tokens.setPlaceholderText("field__lookup=value  field2=value2")
        if field_names:
            completer = QCompleter(list(field_names))
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.tokens.setCompleter(completer)
        mono = QFont()
        mono.setFamily(theme.MONO_FONT_FAMILY.split(",")[0].strip())
        mono.setStyleHint(QFont.Monospace)
        self.tokens.setFont(mono)
        self.remove = QPushButton("\u2212")
        self.remove.setFixedWidth(32)
        layout.addWidget(self.op)
        layout.addWidget(self.tokens)
        layout.addWidget(self.remove)

    def as_text(self):
        return (self.op.currentData(), self.tokens.text())


class _StructuredRow(QWidget):
    def __init__(self, op="filter", field="", lookup="exact", value="",
                 field_names=None, lookups=None, get_field_values=None,
                 parent=None):
        super().__init__(parent)
        self._get_field_values = get_field_values or (lambda field: [])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.op = QComboBox()
        for op_value in ("filter", "exclude"):
            self.op.addItem(OP_LABELS[op_value], op_value)
        _select_data(self.op, op)
        _fit_popup_to_contents(self.op)
        self.field = QComboBox()
        self.field.setEditable(True)
        if field_names:
            self.field.addItems(list(field_names))
        self.field.setCurrentText(field)
        _fit_popup_to_contents(self.field)
        self.lookup = QComboBox()
        for lookup_value in ["exact"] + list(lookups or []):
            self.lookup.addItem(_lookup_label(lookup_value), lookup_value)
        _select_data(self.lookup, lookup)
        _fit_popup_to_contents(self.lookup)
        # Editable combo: suggests distinct values seen in the focused list for
        # the chosen field, while still accepting free text (lists, ranges).
        self.value = QComboBox()
        self.value.setEditable(True)
        self.value.setInsertPolicy(QComboBox.NoInsert)
        self.value.lineEdit().setPlaceholderText("value")
        self._reload_values()
        self.value.setCurrentText(value)
        self.field.currentTextChanged.connect(self._reload_values)
        self.remove = QPushButton("\u2212")
        self.remove.setFixedWidth(32)
        layout.addWidget(self.op)
        layout.addWidget(self.field)
        layout.addWidget(self.lookup)
        layout.addWidget(self.value)
        layout.addWidget(self.remove)

    def _reload_values(self, *_):
        """Repopulate value suggestions for the current field, keeping text."""
        current = self.value.currentText()
        self.value.blockSignals(True)
        self.value.clear()
        for candidate in self._get_field_values(self.field.currentText().strip()):
            self.value.addItem(candidate)
        self.value.setCurrentText(current)
        self.value.blockSignals(False)
        _fit_popup_to_contents(self.value)

    def _key(self):
        field = self.field.currentText().strip()
        lookup = self.lookup.currentData()
        return field if lookup == "exact" else f"{field}__{lookup}"

    def _coerced_value(self):
        """A picked suggestion is a literal scalar; free text may be a list/range.

        Suggestions come from real cell values, so a comma or ``..`` in them is
        data, not token syntax. Only fall back to list/range parsing for text
        the user typed that does not match a suggestion.
        """
        text = self.value.currentText()
        if self.value.findText(text) >= 0:
            return query.coerce_scalar(text)
        return query.coerce_value(text)

    def as_text(self):
        return (self.op.currentData(), f"{self._key()}={self.value.currentText()}")

    def as_kwargs(self):
        return (self.op.currentData(), {self._key(): self._coerced_value()})


class QueryPanel(QWidget):
    runRequested = Signal()

    def __init__(self, get_field_names=None, get_field_values=None,
                 lookups=None, parent=None):
        super().__init__(parent)
        self._get_field_names = get_field_names or (lambda: [])
        self._get_field_values = get_field_values or (lambda field: [])
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
        # The condition builder keeps its natural height; extra vertical space
        # from the splitter goes to the results pane, not the row editor.
        self.stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout.addWidget(self.stack)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("\uff0b")
        self.add_button.setFixedWidth(36)
        self.add_button.clicked.connect(self._on_add)
        self.run_button = QPushButton("\u25b6 Run")
        self.run_button.clicked.connect(self.runRequested.emit)
        buttons.addWidget(self.add_button)
        buttons.addStretch()
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)

        results_header = QHBoxLayout()
        self.count_label = QLabel("0 results")
        self.copy_button = QPushButton("\u29c9 Copy")
        self.copy_button.clicked.connect(self._copy_results)
        results_header.addWidget(self.count_label)
        results_header.addStretch()
        results_header.addWidget(self.copy_button)
        layout.addLayout(results_header)

        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        mono = QFont()
        mono.setFamily(theme.MONO_FONT_FAMILY.split(",")[0].strip())
        mono.setStyleHint(QFont.Monospace)
        self.results.setFont(mono)
        self.results.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.results, 1)

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
                                         field_names, self.lookups,
                                         self._get_field_values)
                    self._structured_rows.append(row)
                    self._register_row(row)
                    self._structured_layout.addWidget(row)
            if not self._structured_rows:
                self._add_structured_row(field_names)
        else:
            self._clear_layout(self._text_layout, self._text_rows)
            for op, text in rows:
                row = _TextRow(op, text, field_names)
                self._text_rows.append(row)
                self._register_row(row)
                self._text_layout.addWidget(row)
            if not self._text_rows:
                self._add_text_row(field_names)

    def _parse_token_for_structured(self, token):
        if "=" not in token:
            return (token.strip(), "exact", "")
        key, _, value = token.partition("=")
        field, lookup = query.split_key(key.strip(), self.lookups)
        return (field, lookup, value.strip())

    def _register_row(self, row):
        row.remove.clicked.connect(lambda _=False, r=row: self._remove_row(r))

    def _remove_row(self, row):
        for holder, layout in (
            (self._structured_rows, self._structured_layout),
            (self._text_rows, self._text_layout),
        ):
            if row in holder:
                holder.remove(row)
                layout.removeWidget(row)
                row.deleteLater()
                return

    def _copy_results(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.results.toPlainText())

    def _add_text_row(self, field_names):
        row = _TextRow("filter", "", field_names)
        self._text_rows.append(row)
        self._register_row(row)
        self._text_layout.addWidget(row)

    def _add_structured_row(self, field_names):
        row = _StructuredRow("filter", "", "exact", "", field_names,
                             self.lookups, self._get_field_values)
        self._structured_rows.append(row)
        self._register_row(row)
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

    def set_results_text(self, text, count=None):
        self.results.setPlainText(text)
        if count is not None:
            self.count_label.setText(f"{count} result" + ("" if count == 1 else "s"))

    def set_run_enabled(self, enabled):
        self.run_button.setEnabled(enabled)
