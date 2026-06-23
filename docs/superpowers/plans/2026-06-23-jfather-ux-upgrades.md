# jfather UX Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-platform shortcuts, a table viewer with tree fallback, a redesigned discoverable query builder, an editor find bar, native scrollbars, and focus/drill-in to the existing jfather app.

**Architecture:** New pure-logic helpers (`paths`, `query.split_key`) stay GUI-free and unit-tested. New Qt widgets/models (`table_model`, `breadcrumb`, `find_bar`) and a rewritten `query_panel` are tested headless with `QT_QPA_PLATFORM=offscreen`. `app.py` wires shortcuts, a stacked table/tree right pane, focus/breadcrumb navigation, and the new query panel.

**Tech Stack:** Python 3.12, PySide6 (Qt6), collection-query>=0.2.0, pytest, uv.

## Global Constraints

- Python `>=3.12`; manage with `uv`; run Qt tests with `QT_QPA_PLATFORM=offscreen`.
- `collection-query>=0.2.0`. `query.available_lookups()` returns the lookup names. Unknown lookups raise `FieldLookupError`, normalized to `ValueError` by `query.run_query`.
- Shortcuts must be cross-platform via Qt portable forms: `QKeySequence.StandardKey` where available, else `"Ctrl+..."` strings (Qt maps `Ctrl`→Cmd on macOS).
- JSON dumps use `ensure_ascii=False`.
- Pure-logic modules (`jsontools`, `query`, `search`, `paths`, `document`) must not import PySide6.
- A "tabular" value is a non-empty `list` whose dict items are at least half of its length.
- Focus state lives in `Document.focus_path` (list of keys/indices; `[]` = whole document); query scope = the focused value; Run is disabled unless the focused value is a `list`.

---

### Task 1: query.split_key helper

**Files:**
- Modify: `jfather/query.py`
- Test: `tests/test_query.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `split_key(key: str, lookups: list[str]) -> tuple[str, str]` returning `(field, lookup)`; lookup is `"exact"` when the last `__`-segment is not a known lookup.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_query.py`:

```python
def test_split_key_with_lookup():
    lookups = query.available_lookups()
    assert query.split_key("id__gt", lookups) == ("id", "gt")


def test_split_key_nested_no_lookup():
    lookups = query.available_lookups()
    assert query.split_key("dept__name", lookups) == ("dept__name", "exact")


def test_split_key_nested_with_lookup():
    lookups = query.available_lookups()
    assert query.split_key("dept__name__contains", lookups) == ("dept__name", "contains")


def test_split_key_plain():
    assert query.split_key("name", query.available_lookups()) == ("name", "exact")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_query.py::test_split_key_with_lookup -v`
Expected: FAIL with `AttributeError: module 'jfather.query' has no attribute 'split_key'`.

- [ ] **Step 3: Write minimal implementation**

Add to `jfather/query.py` (after `parse_tokens`):

```python
def split_key(key, lookups):
    """Split 'field__lookup' into (field, lookup).

    The last '__' segment is treated as a lookup only when it is a known
    lookup name; otherwise the whole key is a (possibly nested) field and the
    lookup is 'exact'.
    """
    parts = key.split("__")
    if len(parts) > 1 and parts[-1] in lookups:
        return "__".join(parts[:-1]), parts[-1]
    return key, "exact"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_query.py -q`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add jfather/query.py tests/test_query.py
git commit -m "feat: add query.split_key for field/lookup parsing"
```

---

### Task 2: paths module (resolve / nearest-valid)

**Files:**
- Create: `jfather/paths.py`
- Test: `tests/test_paths.py`

**Interfaces:**
- Produces:
  - `resolve_path(data, path) -> object` — follow keys/indices; raises `(KeyError, IndexError, TypeError)` if a segment is invalid.
  - `nearest_valid_path(data, path) -> list` — longest prefix of `path` that resolves.
  - `resolve_or_nearest(data, path) -> tuple[object, list]` — `(value, valid_path)` using the nearest valid prefix.

- [ ] **Step 1: Write the failing test**

Create `tests/test_paths.py`:

```python
import pytest
from jfather import paths

DATA = {"users": [{"name": "Alice"}, {"name": "Bob"}], "n": 5}


def test_resolve_path_root():
    assert paths.resolve_path(DATA, []) is DATA


def test_resolve_path_nested():
    assert paths.resolve_path(DATA, ["users", 1, "name"]) == "Bob"


def test_resolve_path_invalid_raises():
    with pytest.raises((KeyError, IndexError, TypeError)):
        paths.resolve_path(DATA, ["users", 9])
    with pytest.raises((KeyError, IndexError, TypeError)):
        paths.resolve_path(DATA, ["n", "x"])


def test_nearest_valid_path_full():
    assert paths.nearest_valid_path(DATA, ["users", 0, "name"]) == ["users", 0, "name"]


def test_nearest_valid_path_truncates():
    assert paths.nearest_valid_path(DATA, ["users", 9, "name"]) == ["users"]
    assert paths.nearest_valid_path(DATA, ["missing"]) == []


def test_resolve_or_nearest():
    value, valid = paths.resolve_or_nearest(DATA, ["users", 9])
    assert value == DATA["users"]
    assert valid == ["users"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paths.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'jfather.paths'`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/paths.py`:

```python
"""Resolve key/index paths into parsed JSON structures."""


def _step(node, key):
    if isinstance(node, dict):
        return node[key]
    if isinstance(node, list):
        if not isinstance(key, int):
            raise TypeError(f"List index must be int, got {key!r}")
        return node[key]
    raise TypeError(f"Cannot index into {type(node).__name__}")


def resolve_path(data, path):
    """Follow path (keys/indices) into data. Raises on an invalid segment."""
    node = data
    for key in path:
        node = _step(node, key)
    return node


def nearest_valid_path(data, path):
    """Return the longest prefix of path that resolves within data."""
    valid = []
    node = data
    for key in path:
        try:
            node = _step(node, key)
        except (KeyError, IndexError, TypeError):
            break
        valid.append(key)
    return valid


def resolve_or_nearest(data, path):
    """Return (value, valid_path) using the nearest valid prefix of path."""
    valid = nearest_valid_path(data, path)
    return resolve_path(data, valid), valid
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_paths.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/paths.py tests/test_paths.py
git commit -m "feat: add paths module for focus path resolution"
```

---

### Task 3: Document.focus_path

**Files:**
- Modify: `jfather/document.py`
- Test: `tests/test_document.py`

**Interfaces:**
- Produces: `Document.focus_path: list` (defaults to `[]`, per-document state).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_document.py`:

```python
def test_document_focus_path_defaults_empty():
    assert Document().focus_path == []


def test_focus_path_isolated_between_documents():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    d2 = mgr.new(name="two")
    d1.focus_path.append("users")
    assert d2.focus_path == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_document.py::test_document_focus_path_defaults_empty -v`
Expected: FAIL with `AttributeError: 'Document' object has no attribute 'focus_path'`.

- [ ] **Step 3: Write minimal implementation**

In `jfather/document.py`, in `Document.__init__`, add `focus_path` next to the other per-document state:

```python
        self.query_rows = []
        self.search_term = ""
        self.expanded_paths = set()
        self.focus_path = []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_document.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/document.py tests/test_document.py
git commit -m "feat: add Document.focus_path for drill-in state"
```

---

### Task 4: table_model (is_tabular + JsonTableModel + tree path_for_index)

**Files:**
- Create: `jfather/table_model.py`
- Modify: `jfather/tree_model.py` (add `path_for_index`)
- Test: `tests/test_table_model.py`, `tests/test_tree_model.py`

**Interfaces:**
- Produces:
  - `is_tabular(data) -> bool`.
  - `JsonTableModel(rows=None)` with `set_rows(rows)`, `row_object(row) -> object`, columns = union of dict keys in first-seen order; cells render scalars as text and dict/list as compact JSON; non-dict rows render in column 0.
  - `tree_model.path_for_index(index) -> list` — absolute path (keys/indices) from the model root to the node at `index`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_table_model.py`:

```python
from PySide6.QtCore import QModelIndex, Qt
from jfather.table_model import JsonTableModel, is_tabular


def test_is_tabular_true_for_list_of_dicts():
    assert is_tabular([{"a": 1}, {"a": 2}]) is True


def test_is_tabular_half_dicts():
    assert is_tabular([{"a": 1}, 5]) is True  # 1 of 2 is a dict


def test_is_tabular_false_cases():
    assert is_tabular([]) is False
    assert is_tabular({"a": 1}) is False
    assert is_tabular([1, 2, 3]) is False


def test_columns_are_union_in_first_seen_order():
    model = JsonTableModel([{"b": 1, "a": 2}, {"a": 3, "c": 4}])
    assert model.columnCount() == 3
    headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(3)]
    assert headers == ["b", "a", "c"]


def test_cell_scalar_and_nested_rendering():
    model = JsonTableModel([{"a": 1, "b": {"x": 2}}])
    a = model.index(0, 0, QModelIndex())
    b = model.index(0, 1, QModelIndex())
    assert model.data(a, Qt.DisplayRole) == "1"
    assert model.data(b, Qt.DisplayRole) == '{"x": 2}'


def test_missing_key_is_empty():
    model = JsonTableModel([{"a": 1}, {"b": 2}])
    cell = model.index(0, 1, QModelIndex())  # row 0 has no "b"
    assert model.data(cell, Qt.DisplayRole) == ""


def test_row_object():
    rows = [{"a": 1}, {"a": 2}]
    model = JsonTableModel(rows)
    assert model.row_object(1) == {"a": 2}


def test_set_rows_resets():
    model = JsonTableModel([{"a": 1}])
    model.set_rows([{"x": 1}, {"x": 2}])
    assert model.rowCount() == 2
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "x"
```

Append to `tests/test_tree_model.py`:

```python
def test_path_for_index_nested():
    from jfather.tree_model import path_for_index
    model = JsonTreeModel({"users": [{"name": "Bob"}]})
    users = model.index(0, 0, QModelIndex())
    first = model.index(0, 0, users)
    name = model.index(0, 0, first)
    assert path_for_index(name) == ["users", 0, "name"]


def test_path_for_index_invalid_is_empty():
    from PySide6.QtCore import QModelIndex
    from jfather.tree_model import path_for_index
    assert path_for_index(QModelIndex()) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_table_model.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'jfather.table_model'`.

- [ ] **Step 3: Write minimal implementations**

Create `jfather/table_model.py`:

```python
"""Qt table model for arrays of JSON objects."""

import json

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


def is_tabular(data):
    """True when data is a non-empty list whose items are >= half dicts."""
    if not isinstance(data, list) or not data:
        return False
    dict_count = sum(1 for item in data if isinstance(item, dict))
    return dict_count * 2 >= len(data)


def _cell_text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class JsonTableModel(QAbstractTableModel):
    """Rows = objects; columns = union of their keys (first-seen order)."""

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self._rows = []
        self._columns = []
        if rows is not None:
            self.set_rows(rows)

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = list(rows)
        columns = []
        seen = set()
        for item in self._rows:
            if isinstance(item, dict):
                for key in item.keys():
                    if key not in seen:
                        seen.add(key)
                        columns.append(key)
        self._columns = columns
        self.endResetModel()

    def row_object(self, row):
        return self._rows[row]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        item = self._rows[index.row()]
        if isinstance(item, dict):
            key = self._columns[index.column()]
            if key in item:
                return _cell_text(item[key])
            return ""
        return _cell_text(item) if index.column() == 0 else ""

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
            return None
        return section
```

Add to `jfather/tree_model.py` (after `index_for_path`):

```python
def path_for_index(index):
    """Return the absolute path (keys/indices) for a tree index's node."""
    if not index.isValid():
        return []
    path = []
    node = index.internalPointer()
    while node is not None and node.parent is not None:
        path.append(node.key)
        node = node.parent
    path.reverse()
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_table_model.py tests/test_tree_model.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/table_model.py jfather/tree_model.py tests/test_table_model.py tests/test_tree_model.py
git commit -m "feat: add JSON table model and tree path_for_index"
```

---

### Task 5: breadcrumb widget

**Files:**
- Create: `jfather/breadcrumb.py`
- Test: `tests/test_breadcrumb.py`

**Interfaces:**
- Produces: `Breadcrumb(QWidget)` with signal `pathChanged(list)`, methods `set_path(path)` and `path() -> list`. Renders a `root` crumb plus one per path segment; list indices shown as `[i]`. Clicking a crumb emits the corresponding prefix (`root` → `[]`). Exposes `buttons` (list of the crumb `QPushButton`s) for wiring/tests.

- [ ] **Step 1: Write the failing test**

Create `tests/test_breadcrumb.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication
from jfather.breadcrumb import Breadcrumb


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_root_only(app):
    bar = Breadcrumb()
    bar.set_path([])
    assert [b.text() for b in bar.buttons] == ["root"]


def test_renders_crumbs_with_index_labels(app):
    bar = Breadcrumb()
    bar.set_path(["users", 0, "name"])
    assert [b.text() for b in bar.buttons] == ["root", "users", "[0]", "name"]


def test_click_emits_prefix(app):
    bar = Breadcrumb()
    bar.set_path(["users", 0, "name"])
    seen = []
    bar.pathChanged.connect(seen.append)
    bar.buttons[2].click()  # the "[0]" crumb
    assert seen[-1] == ["users", 0]


def test_click_root_emits_empty(app):
    bar = Breadcrumb()
    bar.set_path(["users"])
    seen = []
    bar.pathChanged.connect(seen.append)
    bar.buttons[0].click()
    assert seen[-1] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_breadcrumb.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'jfather.breadcrumb'`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/breadcrumb.py`:

```python
"""Breadcrumb bar showing and navigating the focus path."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class Breadcrumb(QWidget):
    pathChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = []
        self.buttons = []
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
            if widget is not None:
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
            button.setFlat(True)
            button.clicked.connect(
                lambda _checked=False, t=target: self.pathChanged.emit(t)
            )
            self.buttons.append(button)
            self._layout.addWidget(button)
        self._layout.addStretch()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_breadcrumb.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/breadcrumb.py tests/test_breadcrumb.py
git commit -m "feat: add breadcrumb navigation widget"
```

---

### Task 6: find_bar widget

**Files:**
- Create: `jfather/find_bar.py`
- Test: `tests/test_find_bar.py`

**Interfaces:**
- Produces: `FindBar(QWidget)` with `input` (a `QLineEdit`), `count_label`, `prev_button`, `next_button`, `close_button`; signals `queryChanged(str)`, `nextRequested()`, `prevRequested()`, `closed()`; method `set_count(current, total)`. Esc in the input emits `closed`; Enter emits `nextRequested`; Shift+Enter emits `prevRequested`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_find_bar.py`:

```python
import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from jfather.find_bar import FindBar


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_text_emits_query(app):
    bar = FindBar()
    seen = []
    bar.queryChanged.connect(seen.append)
    bar.input.setText("abc")
    assert seen[-1] == "abc"


def test_buttons_emit_signals(app):
    bar = FindBar()
    nexts, prevs, closed = [], [], []
    bar.nextRequested.connect(lambda: nexts.append(1))
    bar.prevRequested.connect(lambda: prevs.append(1))
    bar.closed.connect(lambda: closed.append(1))
    bar.next_button.click()
    bar.prev_button.click()
    bar.close_button.click()
    assert nexts == [1] and prevs == [1] and closed == [1]


def test_escape_emits_closed(app):
    bar = FindBar()
    closed = []
    bar.closed.connect(lambda: closed.append(1))
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
    bar.input.keyPressEvent(event)
    assert closed == [1]


def test_enter_and_shift_enter(app):
    bar = FindBar()
    nexts, prevs = [], []
    bar.nextRequested.connect(lambda: nexts.append(1))
    bar.prevRequested.connect(lambda: prevs.append(1))
    bar.input.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
    bar.input.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.ShiftModifier))
    assert nexts == [1] and prevs == [1]


def test_set_count(app):
    bar = FindBar()
    bar.set_count(2, 5)
    assert bar.count_label.text() == "2/5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_find_bar.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'jfather.find_bar'`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/find_bar.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_find_bar.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/find_bar.py tests/test_find_bar.py
git commit -m "feat: add editor find bar widget"
```

---

### Task 7: editor find support

**Files:**
- Modify: `jfather/editor.py`
- Test: `tests/test_editor.py`

**Interfaces:**
- Consumes: nothing new.
- Produces on `JsonEditor`:
  - `find_matches(term: str) -> int` — highlights all matches, resets active index, returns match count.
  - `find_next(forward: bool = True) -> int` — moves selection to next/previous match (wrap-around), returns 1-based active index (0 if none).
  - `clear_find() -> None` — removes highlights and resets state.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_editor.py`:

```python
def test_find_matches_counts(app):
    editor = JsonEditor()
    editor.set_text("aXbXcX")
    assert editor.find_matches("X") == 3
    assert len(editor.extraSelections()) == 3


def test_find_matches_empty_term(app):
    editor = JsonEditor()
    editor.set_text("aXb")
    assert editor.find_matches("") == 0
    assert editor.extraSelections() == []


def test_find_next_wraps(app):
    editor = JsonEditor()
    editor.set_text("X X X")
    editor.find_matches("X")
    assert editor.find_next() == 1
    assert editor.find_next() == 2
    assert editor.find_next() == 3
    assert editor.find_next() == 1  # wraps


def test_clear_find(app):
    editor = JsonEditor()
    editor.set_text("aXb")
    editor.find_matches("X")
    editor.clear_find()
    assert editor.extraSelections() == []
    assert editor.find_next() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_editor.py::test_find_matches_counts -v`
Expected: FAIL with `AttributeError: 'JsonEditor' object has no attribute 'find_matches'`.

- [ ] **Step 3: Write minimal implementation**

In `jfather/editor.py`, update imports:

```python
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit
```

In `JsonEditor.__init__`, after `self.highlighter = ...`, initialize find state:

```python
        self.highlighter = JsonHighlighter(self.document())
        self._match_cursors = []
        self._find_index = -1
        self._match_format = QTextCharFormat()
        self._match_format.setBackground(QColor("#5f5f00"))
```

Add methods to `JsonEditor`:

```python
    def find_matches(self, term):
        self._match_cursors = []
        self._find_index = -1
        selections = []
        if term:
            document = self.document()
            cursor = QTextCursor(document)
            while True:
                cursor = document.find(term, cursor)
                if cursor.isNull():
                    break
                self._match_cursors.append(QTextCursor(cursor))
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = self._match_format
                selections.append(selection)
        self.setExtraSelections(selections)
        return len(self._match_cursors)

    def find_next(self, forward=True):
        if not self._match_cursors:
            return 0
        step = 1 if forward else -1
        self._find_index = (self._find_index + step) % len(self._match_cursors)
        self.setTextCursor(self._match_cursors[self._find_index])
        return self._find_index + 1

    def clear_find(self):
        self._match_cursors = []
        self._find_index = -1
        self.setExtraSelections([])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_editor.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/editor.py tests/test_editor.py
git commit -m "feat: add find/highlight support to JSON editor"
```

---

### Task 8: query_panel rewrite (structured + text modes)

**Files:**
- Rewrite: `jfather/query_panel.py`
- Test: `tests/test_query_panel.py` (replace contents)

**Interfaces:**
- Consumes: `jfather.query` (`available_lookups`, `parse_tokens`, `coerce_value`, `split_key`).
- Produces `QueryPanel(get_field_names=None, lookups=None, parent=None)`:
  - Signal `runRequested()` (no args).
  - `current_rows() -> list[tuple[str, dict]]` — `(op, kwargs)` from the active mode. Raises `ValueError` on malformed text tokens.
  - `rows() -> list[tuple[str, str]]` / `set_rows(rows)` — persistence as `(op, token_text)`.
  - `set_results_text(text)`.
  - `set_run_enabled(enabled: bool)` — enables/disables the Run button.
  - `set_mode(mode: str)` where mode in `{"structured", "text"}`; `mode() -> str`.
  - `run_button` attribute (a `QPushButton`).

- [ ] **Step 1: Write the failing test**

Replace the contents of `tests/test_query_panel.py` with:

```python
import pytest
from PySide6.QtWidgets import QApplication
from jfather.query_panel import QueryPanel


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_text_mode_current_rows(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "id__gt=1"), ("exclude", "name=Bob")])
    assert panel.current_rows() == [
        ("filter", {"id__gt": 1}),
        ("exclude", {"name": "Bob"}),
    ]


def test_rows_round_trip(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "id__gt=1")])
    assert panel.rows() == [("filter", "id__gt=1")]


def test_text_mode_malformed_raises(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "noequals")])
    with pytest.raises(ValueError):
        panel.current_rows()


def test_structured_mode_builds_kwargs(app):
    panel = QueryPanel(lookups=["gt", "contains"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "id__gt=1")])
    assert panel.current_rows() == [("filter", {"id__gt": 1})]


def test_structured_exact_lookup_has_no_suffix(app):
    panel = QueryPanel(lookups=["gt", "contains"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "name=Bob")])
    assert panel.current_rows() == [("filter", {"name": "Bob"})]


def test_mode_toggle_preserves_rows(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "id__gt=1")])
    panel.set_mode("structured")
    panel.set_mode("text")
    assert panel.rows() == [("filter", "id__gt=1")]


def test_lookups_injected(app):
    panel = QueryPanel(lookups=["gt", "lt", "contains"])
    assert panel.lookups == ["gt", "lt", "contains"]


def test_run_button_enable_disable(app):
    panel = QueryPanel()
    panel.set_run_enabled(False)
    assert panel.run_button.isEnabled() is False
    panel.set_run_enabled(True)
    assert panel.run_button.isEnabled() is True


def test_run_emits_signal(app):
    panel = QueryPanel()
    seen = []
    panel.runRequested.connect(lambda: seen.append(1))
    panel.run_button.click()
    assert seen == [1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_query_panel.py -q`
Expected: FAIL (e.g. `TypeError`/`AttributeError` for `set_mode`).

- [ ] **Step 3: Write minimal implementation**

Replace `jfather/query_panel.py` with:

```python
"""Collection-query builder panel with structured and text modes."""

from PySide6.QtCore import Signal
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
            completer = QCompleter(field_names)
            completer.setCaseSensitivity(False)
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
            self.field.addItems(field_names)
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

    def as_text(self):
        field = self.field.currentText().strip()
        lookup = self.lookup.currentText()
        key = field if lookup == "exact" else f"{field}__{lookup}"
        return (self.op.currentText(), f"{key}={self.value.text()}")

    def as_kwargs(self):
        field = self.field.currentText().strip()
        lookup = self.lookup.currentText()
        key = field if lookup == "exact" else f"{field}__{lookup}"
        return (self.op.currentText(), {key: query.coerce_value(self.value.text())})


class QueryPanel(QWidget):
    runRequested = Signal()

    def __init__(self, get_field_names=None, lookups=None, parent=None):
        super().__init__(parent)
        self._get_field_names = get_field_names or (lambda: [])
        self.lookups = list(lookups) if lookups is not None else query.available_lookups()
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_query_panel.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/query_panel.py tests/test_query_panel.py
git commit -m "feat: redesign query panel with structured and text modes"
```

---

### Task 9: theme rewrite (scoped styles, native scrollbars)

**Files:**
- Rewrite: `jfather/theme.py`
- Test: `tests/test_theme.py`

**Interfaces:**
- Produces: `theme.STYLESHEET: str`, `theme.LIGHT_STYLESHEET: str` — scoped to concrete widget classes, with no universal `QWidget` rule and no `QScrollBar` rule (so native scrollbars render).

- [ ] **Step 1: Write the failing test**

Create `tests/test_theme.py`:

```python
from jfather import theme


def test_no_universal_widget_rule():
    for sheet in (theme.STYLESHEET, theme.LIGHT_STYLESHEET):
        assert "QWidget {" not in sheet
        assert "QWidget{" not in sheet


def test_no_scrollbar_styling():
    for sheet in (theme.STYLESHEET, theme.LIGHT_STYLESHEET):
        assert "QScrollBar" not in sheet


def test_styles_concrete_widgets():
    assert "QPlainTextEdit" in theme.STYLESHEET
    assert "QTableView" in theme.STYLESHEET
    assert "QPushButton" in theme.STYLESHEET
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_theme.py -q`
Expected: FAIL (current `STYLESHEET` contains `QWidget {`).

- [ ] **Step 3: Write minimal implementation**

Replace `jfather/theme.py` with:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_theme.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/theme.py tests/test_theme.py
git commit -m "feat: scope theme styles so native scrollbars render"
```

---

### Task 10: app — cross-platform shortcuts + find bar wiring

**Files:**
- Modify: `jfather/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `find_bar.FindBar`, `JsonEditor.find_matches/find_next/clear_find`.
- Produces on `MainWindow`:
  - `actions: dict[str, QAction]` with keys `"close"`, `"save"`, `"format"`, `"run"`, `"find"` carrying the portable shortcuts.
  - `find_bar` (a `FindBar`), `toggle_find()`, `_find(term)`, `_find_step(forward)`, `_close_find()`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
from PySide6.QtGui import QKeySequence


def test_shortcuts_registered(app):
    win = MainWindow()
    seqs = {name: act.shortcut() for name, act in win.actions.items()}
    assert seqs["save"] == QKeySequence(QKeySequence.Save)
    assert seqs["close"] == QKeySequence(QKeySequence.Close)
    assert seqs["find"] == QKeySequence(QKeySequence.Find)
    assert seqs["format"] == QKeySequence("Ctrl+Shift+F")
    assert seqs["run"] == QKeySequence("Ctrl+Return")


def test_toggle_find_shows_and_hides(app):
    win = MainWindow()
    assert win.find_bar.isVisible() is False
    win.toggle_find()
    assert win.find_bar.isVisible() is True
    win._close_find()
    assert win.find_bar.isVisible() is False


def test_find_counts_and_navigates(app):
    win = MainWindow()
    win.editor.set_text("X X X")
    win.toggle_find()
    win._find("X")
    assert win.find_bar.count_label.text().endswith("/3")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py::test_shortcuts_registered -v`
Expected: FAIL with `AttributeError: 'MainWindow' object has no attribute 'actions'`.

- [ ] **Step 3: Write minimal implementation**

In `jfather/app.py` update imports:

```python
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QTimer
from .find_bar import FindBar
```

(Keep the existing widget imports.)

In `_build_ui`, wrap the editor with the find bar. Replace the editor creation
and its placement in `center_split` so the editor pane is a vertical container:

```python
        self.editor = JsonEditor()

        self.find_bar = FindBar()
        self.find_bar.hide()
        self.find_bar.queryChanged.connect(self._find)
        self.find_bar.nextRequested.connect(lambda: self._find_step(True))
        self.find_bar.prevRequested.connect(lambda: self._find_step(False))
        self.find_bar.closed.connect(self._close_find)

        editor_pane = QWidget()
        editor_layout = QVBoxLayout(editor_pane)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.find_bar)
        editor_layout.addWidget(self.editor)
```

Then in `center_split` add `editor_pane` instead of `self.editor`:

```python
        center_split = QSplitter(Qt.Horizontal)
        center_split.addWidget(editor_pane)
        center_split.addWidget(tree_pane)
        center_split.setSizes([600, 600])
```

Replace `_build_toolbar` with a version that also builds shortcut actions:

```python
    def _build_toolbar(self):
        bar = QToolBar()
        self.addToolBar(bar)
        bar.addAction("New", self.new_document)
        bar.addAction("Open", self.open_file)
        bar.addSeparator()
        bar.addAction("Minify", self.apply_minify)
        bar.addAction("Escape", self.apply_escape)
        bar.addAction("Unescape", self.apply_unescape)
        bar.addSeparator()
        bar.addAction("Theme", self.toggle_theme)

        self.actions = {}
        specs = [
            ("close", QKeySequence(QKeySequence.Close), self._close_active_document),
            ("save", QKeySequence(QKeySequence.Save), self.save_file),
            ("format", QKeySequence("Ctrl+Shift+F"), self.apply_format),
            ("run", QKeySequence("Ctrl+Return"), self.run_query),
            ("find", QKeySequence(QKeySequence.Find), self.toggle_find),
        ]
        for name, sequence, handler in specs:
            action = QAction(name.capitalize(), self)
            action.setShortcut(sequence)
            action.triggered.connect(handler)
            self.addAction(action)
            bar.addAction(action)
            self.actions[name] = action
```

Add a helper to close the active document via shortcut, and the find handlers:

```python
    def _close_active_document(self):
        if self.manager.active is not None:
            self._on_doc_close(self.manager.active_index)

    # ---- Editor find -----------------------------------------------------
    def toggle_find(self):
        if self.find_bar.isVisible():
            self._close_find()
        else:
            self.find_bar.show()
            self.find_bar.input.setFocus()
            self.find_bar.input.selectAll()
            self._find(self.find_bar.input.text())

    def _find(self, term):
        total = self.editor.find_matches(term)
        current = self.editor.find_next(True) if total else 0
        self.find_bar.set_count(current, total)

    def _find_step(self, forward):
        current = self.editor.find_next(forward)
        total = len(self.editor._match_cursors)
        self.find_bar.set_count(current, total)

    def _close_find(self):
        self.editor.clear_find()
        self.find_bar.hide()
        self.editor.setFocus()
```

Note: `run_query` is currently defined as `run_query(self, raw_rows)`. The `run`
action calls it with no argument; Task 11 changes `run_query` to take no
argument. Until then, give `run_query` a default so this task's tests pass:
change its signature to `def run_query(self, raw_rows=None):` and, at the top of
the method, `if raw_rows is None: raw_rows = self.query_panel.rows()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/app.py tests/test_app.py
git commit -m "feat: add cross-platform shortcuts and editor find bar wiring"
```

---

### Task 11: app — stacked table/tree pane, focus/breadcrumb, routing, search, query scope

**Files:**
- Modify: `jfather/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `table_model.JsonTableModel/is_tabular`, `breadcrumb.Breadcrumb`, `paths.resolve_or_nearest`, `tree_model.path_for_index`, `query_panel.QueryPanel` new API.
- Produces on `MainWindow`:
  - `table` (`QTableView`), `table_model` (`JsonTableModel`), `view_stack` (`QStackedWidget`), `breadcrumb` (`Breadcrumb`).
  - `focused_value() -> object | None`.
  - `_refresh_view()` replaces `refresh_tree`; routes table vs tree, updates breadcrumb, enables/disables query.
  - `focus_path(path)` setter applying a new focus path to the active doc.
  - `run_query()` takes no argument; uses `query_panel.current_rows()` and `focused_value()`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
def test_table_view_for_array_of_objects(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}, {"id": 2}]))
    win.sync_from_editor()
    assert win.view_stack.currentWidget() is win.table
    assert win.table_model.rowCount() == 2


def test_tree_view_for_object(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"a": 1}))
    win.sync_from_editor()
    assert win.view_stack.currentWidget() is win.tree


def test_focus_drills_into_nested_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"users": [{"id": 1}, {"id": 2}]}))
    win.sync_from_editor()
    win.focus_path(["users"])
    assert win.focused_value() == [{"id": 1}, {"id": 2}]
    assert win.view_stack.currentWidget() is win.table


def test_query_runs_against_focused_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"users": [{"id": 1}, {"id": 2}, {"id": 3}]}))
    win.sync_from_editor()
    win.focus_path(["users"])
    win.query_panel.set_mode("text")
    win.query_panel.set_rows([("filter", "id__gt=1")])
    results = win.run_query()
    assert results == [{"id": 2}, {"id": 3}]


def test_query_disabled_when_focus_not_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"a": {"b": 1}}))
    win.sync_from_editor()
    win.focus_path(["a"])
    assert win.query_panel.run_button.isEnabled() is False


def test_stale_focus_path_heals(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"users": [{"id": 1}]}))
    win.sync_from_editor()
    win.focus_path(["users", 5])
    assert win.focused_value() == [{"id": 1}]
    assert win.manager.active.focus_path == ["users"]


def test_table_search_selects_row(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"name": "Alice"}, {"name": "Bob"}]))
    win.sync_from_editor()
    win.search_bar.input.setText("Bob")
    assert win.table.currentIndex().row() == 1
    assert win.search_bar.count_label.text() == "1/1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py::test_table_view_for_array_of_objects -v`
Expected: FAIL with `AttributeError: 'MainWindow' object has no attribute 'view_stack'`.

- [ ] **Step 3: Write minimal implementation**

Update imports in `jfather/app.py`:

```python
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from . import jsontools, paths, query, search, theme
from .breadcrumb import Breadcrumb
from .table_model import JsonTableModel, is_tabular
from .tree_model import JsonTreeModel, index_for_path, path_for_index
```

In `__init__`, add the table model next to the tree model:

```python
        self.tree_model = JsonTreeModel({})
        self.table_model = JsonTableModel([])
```

In `_build_ui`, replace the right-pane construction (the `self.tree`,
`self.search_bar`, `tree_pane` block) with a breadcrumb + search + stacked view:

```python
        self.tree = QTreeView()
        self.tree.setModel(self.tree_model)
        self.tree.doubleClicked.connect(self._on_tree_double_clicked)

        self.table = QTableView()
        self.table.setModel(self.table_model)
        self.table.doubleClicked.connect(self._on_table_double_clicked)

        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.tree)
        self.view_stack.addWidget(self.table)

        self.breadcrumb = Breadcrumb()
        self.breadcrumb.pathChanged.connect(self.focus_path)

        self.search_bar = SearchBar()
        self.search_bar.queryChanged.connect(self._on_search)
        self.search_bar.nextRequested.connect(lambda: self._navigate_search(1))
        self.search_bar.prevRequested.connect(lambda: self._navigate_search(-1))

        tree_pane = QWidget()
        tree_layout = QVBoxLayout(tree_pane)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.addWidget(self.breadcrumb)
        tree_layout.addWidget(self.search_bar)
        tree_layout.addWidget(self.view_stack)
```

Change the `QueryPanel` construction to inject field names and wire the no-arg
run signal:

```python
        self.query_panel = QueryPanel(get_field_names=self._field_names)
        self.query_panel.runRequested.connect(self.run_query)
```

Add the field-name helper:

```python
    def _field_names(self):
        value = self.focused_value()
        names = []
        seen = set()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for key in item.keys():
                        if key not in seen:
                            seen.add(key)
                            names.append(key)
        elif isinstance(value, dict):
            names = list(value.keys())
        return names
```

Replace `refresh_tree` with `_refresh_view`, and point `sync_from_editor` and
`_load_active_into_views` at it. Add focus methods:

```python
    def sync_from_editor(self):
        self._refresh_view()

    def focused_value(self):
        try:
            data = jsontools.parse(self.editor.text())
        except ValueError:
            return None
        doc = self.manager.active
        path = doc.focus_path if doc is not None else []
        value, valid = paths.resolve_or_nearest(data, path)
        if doc is not None and valid != path:
            doc.focus_path = valid
        return value

    def focus_path(self, path):
        doc = self.manager.active
        if doc is not None:
            doc.focus_path = list(path)
        self._refresh_view()

    def _refresh_view(self):
        ok, message, line, col = jsontools.validate(self.editor.text())
        if not ok:
            self.status_label.setText(
                f"Invalid JSON: {message} (line {line}, col {col})"
            )
            return
        self.status_label.setText("Valid JSON")
        value = self.focused_value()
        doc = self.manager.active
        self.breadcrumb.set_path(doc.focus_path if doc is not None else [])
        if is_tabular(value):
            self.table_model.set_rows(value)
            self.view_stack.setCurrentWidget(self.table)
        else:
            self.tree_model.set_json(value if value is not None else {})
            self.view_stack.setCurrentWidget(self.tree)
        is_array = isinstance(value, list)
        self.query_panel.set_run_enabled(is_array)
        if not is_array:
            self.query_panel.set_results_text("Focus an array to query.")

    def _on_tree_double_clicked(self, index):
        node = index.internalPointer()
        if node is None or not node.is_container:
            return
        rel = path_for_index(index)
        doc = self.manager.active
        base = list(doc.focus_path) if doc is not None else []
        self.focus_path(base + rel)

    def _on_table_double_clicked(self, index):
        doc = self.manager.active
        base = list(doc.focus_path) if doc is not None else []
        self.focus_path(base + [index.row()])
```

Replace the search handlers so they work for whichever view is active:

```python
    def _on_search(self, term):
        doc = self.manager.active
        if doc is not None:
            doc.search_term = term
        self._search_results = []
        self._search_pos = -1
        value = self.focused_value()
        if term and value is not None:
            if self.view_stack.currentWidget() is self.table:
                self._search_results = [
                    [r] for r in range(self.table_model.rowCount())
                    if search.search(self.table_model.row_object(r), term)
                ]
            else:
                self._search_results = search.search(value, term)
        if self._search_results:
            self._navigate_search(1)
        else:
            self.search_bar.set_count(0, 0)

    def _navigate_search(self, step):
        total = len(self._search_results)
        if total == 0:
            self.search_bar.set_count(0, 0)
            return
        self._search_pos = (self._search_pos + step) % total
        target = self._search_results[self._search_pos]
        if self.view_stack.currentWidget() is self.table:
            row = target[0]
            idx = self.table_model.index(row, 0)
            self.table.setCurrentIndex(idx)
            self.table.scrollTo(idx)
        else:
            idx = index_for_path(self.tree_model, target)
            if idx.isValid():
                self.tree.setCurrentIndex(idx)
                self.tree.scrollTo(idx)
        self.search_bar.set_count(self._search_pos + 1, total)
```

Replace `query_target`/`run_query` with focus-based versions:

```python
    def run_query(self):
        value = self.focused_value()
        if not isinstance(value, list):
            self.query_panel.set_results_text("Focus an array to query.")
            return []
        try:
            rows = self.query_panel.current_rows()
            results = query.run_query(value, rows)
        except (ValueError, TypeError) as exc:
            self.query_panel.set_results_text(f"Query error: {exc}")
            return []
        self.query_panel.set_results_text(
            f"{len(results)} result(s)\n\n"
            + json.dumps(results, indent=2, ensure_ascii=False)
        )
        return results
```

Remove the now-unused `query_target` method and the old `refresh_tree` method.
In `run_query` from Task 10, the `raw_rows=None` shim is no longer needed —
this no-argument version replaces it. Update the `run` action handler reference
(it already points at `self.run_query`).

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/app.py tests/test_app.py
git commit -m "feat: stacked table/tree pane with focus, breadcrumb, and scoped query"
```

---

### Task 12: full suite + manual smoke + README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run the full suite**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest -q`
Expected: ALL tests pass.

- [ ] **Step 2: Manual smoke (skip if no display)**

Run: `uv run python main.py`
Expected: editor + breadcrumb + right pane. Loading an array-of-objects shows a
table; double-clicking a row or tree node drills in (breadcrumb updates);
clicking a breadcrumb navigates back; the query panel toggles Structured/Text
and runs against the focused array (disabled with a hint when not an array);
Cmd/Ctrl+F opens the find bar; Cmd/Ctrl+S/W/Shift+F/Return work; scrollbars look
native. Close the window.

- [ ] **Step 3: Update README**

In `README.md`, replace the `## Features` section with:

```markdown
## Features

- Multiple documents via the left sidebar (New / Open / Close, dirty markers).
- Dual-pane: syntax-highlighted text editor + data viewer.
- Viewer shows a **table** for arrays of objects and a **tree** otherwise.
- **Focus / drill-in**: double-click a node or table row to re-root the viewer
  and query scope; a breadcrumb navigates back.
- Format, Minify, Escape, Unescape (selection-aware).
- **Query builder** with Structured (field / lookup / value dropdowns) and Text
  (tokens with autocomplete) modes; runs against the focused array.
- In-editor **Find** bar.
- Cross-platform shortcuts: Close (Ctrl/Cmd+W), Save (Ctrl/Cmd+S),
  Format (Ctrl/Cmd+Shift+F), Run query (Ctrl/Cmd+Return), Find (Ctrl/Cmd+F).
- Requires `collection-query>=0.2.0`.
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document table view, focus, query modes, and shortcuts"
```

---

## Self-Review Notes

- **Spec coverage:** shortcuts cross-platform (Task 10); table viewer + fallback (Tasks 4, 11); query redesign + lookup discoverability (Task 8, structured lookup dropdown + text completer); editor find (Tasks 6, 7, 10); native scrollbars (Task 9); focus/drill-in + breadcrumb + query scope (Tasks 2, 3, 5, 11); table search (Task 11).
- **Type consistency:** `current_rows()`→`(op, kwargs)` consumed by `run_query`; `rows()`/`set_rows`→`(op, text)`; `set_run_enabled`, `set_mode`, `set_results_text` used consistently; `path_for_index`/`index_for_path`/`resolve_or_nearest` signatures match call sites; `focus_path` is both a `Document` attribute and a `MainWindow` setter method (distinct scopes — attribute on the document, method on the window).
- **Note:** Task 10 temporarily shims `run_query(raw_rows=None)`; Task 11 replaces it with the no-arg focus-based version. Both leave the suite green at their commit.
