# jfather JSON Viewer/Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A fast, modern PySide6 desktop app to view/edit multiple large JSON documents with formatting, escaping, tree visualization, search, and collection-query querying.

**Architecture:** Pure-logic modules (`jsontools`, `query`, `search`, `document`) are GUI-free and fully unit-tested. Qt modules (`tree_model`, `editor`, `sidebar`, `app`) build the UI on top. `DocumentManager` holds N documents, each with isolated state; the active document drives the editor, lazy tree, search, and query panel.

**Tech Stack:** Python 3.12, PySide6 (Qt6), `collection-query`, `pytest`, managed by `uv`.

## Global Constraints

- Python `>=3.12`, dependency management via `uv`.
- Dependencies: `collection-query>=0.1.0` (already present), add `pyside6`; dev: `pytest`.
- Package name: `jfather` (a real package directory `jfather/`).
- Qt headless tests run with env `QT_QPA_PLATFORM=offscreen`.
- collection-query facts: `ListQuery(list)`; `.filter(**kw)` / `.exclude(**kw)` return a new `ListQuery`; unknown field/lookup returns `[]` (no raise); `__` denotes nested access and lookups (`in`, `not`, `in_range`, `lt`, `lte`, `gt`, `gte`, `startswith`, `endswith`, `contains`).
- JSON dumps use `ensure_ascii=False`.

---

### Task 1: Project scaffolding & dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `jfather/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `jfather` package importable; `pytest` runnable.

- [ ] **Step 1: Add deps**

Edit `pyproject.toml` to:

```toml
[project]
name = "jfather"
version = "0.1.0"
description = "Desktop viewer/editor for large JSON with collection-query"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "collection-query>=0.1.0",
    "pyside6>=6.6",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["jfather"]
```

- [ ] **Step 2: Create package + test init files**

Create `jfather/__init__.py`:

```python
"""jfather: desktop viewer/editor for large JSON."""

__version__ = "0.1.0"
```

Create empty `tests/__init__.py` (no content).

Create `tests/conftest.py`:

```python
import os

# Ensure Qt can run headless during tests.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
```

- [ ] **Step 3: Sync and verify**

Run: `uv sync`
Expected: resolves and installs PySide6 + pytest, exit 0.

Run: `uv run python -c "import jfather, PySide6; print(jfather.__version__)"`
Expected: prints `0.1.0`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock jfather/__init__.py tests/__init__.py tests/conftest.py
git commit -m "chore: scaffold jfather package and deps"
```

---

### Task 2: jsontools module (format, minify, escape, unescape, validate)

**Files:**
- Create: `jfather/jsontools.py`
- Test: `tests/test_jsontools.py`

**Interfaces:**
- Produces:
  - `parse(text: str) -> object` (raises `json.JSONDecodeError`)
  - `validate(text: str) -> tuple[bool, str | None, int | None, int | None]` → `(ok, message, line, col)`
  - `format_json(text: str, indent: int = 2) -> str`
  - `minify_json(text: str) -> str`
  - `escape_string(raw: str) -> str` (returns JSON string literal *with* surrounding quotes)
  - `unescape_string(literal: str) -> str`

- [ ] **Step 1: Write the failing test**

Create `tests/test_jsontools.py`:

```python
import json
import pytest
from jfather import jsontools


def test_parse_valid():
    assert jsontools.parse('{"a": 1}') == {"a": 1}


def test_validate_ok():
    ok, msg, line, col = jsontools.validate('{"a": 1}')
    assert ok is True and msg is None


def test_validate_error_reports_position():
    ok, msg, line, col = jsontools.validate('{"a": }')
    assert ok is False
    assert isinstance(msg, str) and msg
    assert line == 1 and col is not None


def test_format_json_indents():
    assert jsontools.format_json('{"a":1}', indent=2) == '{\n  "a": 1\n}'


def test_format_preserves_unicode():
    assert jsontools.format_json('{"a":"\u00e9"}') == '{\n  "a": "\u00e9"\n}'


def test_minify_json():
    assert jsontools.minify_json('{\n  "a": 1\n}') == '{"a":1}'


def test_escape_string_wraps_and_escapes():
    assert jsontools.escape_string('he said "hi"\n') == '"he said \\"hi\\"\\n"'


def test_unescape_string_with_quotes():
    assert jsontools.unescape_string('"he said \\"hi\\"\\n"') == 'he said "hi"\n'


def test_unescape_string_without_quotes():
    assert jsontools.unescape_string('a\\tb') == 'a\tb'


def test_roundtrip_escape_unescape():
    raw = 'line1\nline2\t"quoted"'
    assert jsontools.unescape_string(jsontools.escape_string(raw)) == raw
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_jsontools.py -v`
Expected: FAIL with `ModuleNotFoundError` / `AttributeError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/jsontools.py`:

```python
"""Pure JSON utility functions used across jfather."""

import json


def parse(text):
    """Parse JSON text into a Python object. Raises json.JSONDecodeError."""
    return json.loads(text)


def validate(text):
    """Return (ok, message, line, col). On success message/line/col are None."""
    try:
        json.loads(text)
        return (True, None, None, None)
    except json.JSONDecodeError as exc:
        return (False, exc.msg, exc.lineno, exc.colno)


def format_json(text, indent=2):
    """Pretty-print JSON text with the given indent."""
    return json.dumps(json.loads(text), indent=indent, ensure_ascii=False)


def minify_json(text):
    """Return the most compact JSON representation."""
    return json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False)


def escape_string(raw):
    """Return a JSON string literal (with surrounding quotes) representing raw."""
    return json.dumps(raw, ensure_ascii=False)


def unescape_string(literal):
    """Decode a JSON string literal back to its raw value.

    Accepts the literal with or without surrounding double quotes.
    """
    literal = literal.strip()
    if literal.startswith('"') and literal.endswith('"') and len(literal) >= 2:
        return json.loads(literal)
    return json.loads('"' + literal + '"')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_jsontools.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add jfather/jsontools.py tests/test_jsontools.py
git commit -m "feat: add jsontools (format/minify/escape/unescape/validate)"
```

---

### Task 3: query module (token parsing + collection-query execution)

**Files:**
- Create: `jfather/query.py`
- Test: `tests/test_query.py`

**Interfaces:**
- Consumes: `collection_query.ListQuery`.
- Produces:
  - `coerce_scalar(s: str) -> object` (int/float/bool/None/str)
  - `coerce_value(token: str) -> object` (scalar, or `list` for `a,b,c`, or `range` for `lo..hi`)
  - `parse_token(token: str) -> tuple[str, object]` (raises `ValueError` if no `=`)
  - `parse_tokens(text: str) -> dict` (whitespace-separated tokens)
  - `run_query(data: list, rows: list[tuple[str, dict]]) -> list` where row op is `"filter"` or `"exclude"` (raises `ValueError` if data not a list or bad op)
  - `build_query(data: list, raw_rows: list[tuple[str, str]]) -> list`

- [ ] **Step 1: Write the failing test**

Create `tests/test_query.py`:

```python
import pytest
from jfather import query

DATA = [
    {"id": 1, "name": "Alice", "dept": {"name": "Eng"}},
    {"id": 2, "name": "Bob", "dept": {"name": "Sales"}},
    {"id": 3, "name": "Cy", "dept": {"name": "Eng"}},
]


def test_coerce_scalar_types():
    assert query.coerce_scalar("5") == 5
    assert query.coerce_scalar("5.5") == 5.5
    assert query.coerce_scalar("true") is True
    assert query.coerce_scalar("false") is False
    assert query.coerce_scalar("null") is None
    assert query.coerce_scalar("hello") == "hello"


def test_coerce_value_list():
    assert query.coerce_value("a,b,c") == ["a", "b", "c"]


def test_coerce_value_range():
    assert query.coerce_value("1..3") == range(1, 3)


def test_parse_token():
    assert query.parse_token("id__gt=1") == ("id__gt", 1)


def test_parse_token_missing_equals():
    with pytest.raises(ValueError):
        query.parse_token("idgt")


def test_parse_tokens_multiple():
    assert query.parse_tokens("id__gt=1 name=Cy") == {"id__gt": 1, "name": "Cy"}


def test_run_query_filter_nested_and_lookup():
    rows = [("filter", {"dept__name": "Eng", "id__gt": 1})]
    assert query.run_query(DATA, rows) == [DATA[2]]


def test_run_query_exclude_chain():
    rows = [("filter", {"dept__name": "Eng"}), ("exclude", {"name": "Cy"})]
    assert query.run_query(DATA, rows) == [DATA[0]]


def test_run_query_in_range():
    data = [{"id": i} for i in range(6)]
    rows = [("filter", {"id__in_range": range(1, 3)})]
    assert query.run_query(data, rows) == [{"id": 1}, {"id": 2}]


def test_run_query_rejects_non_list():
    with pytest.raises(ValueError):
        query.run_query({"a": 1}, [("filter", {"a": 1})])


def test_run_query_rejects_bad_op():
    with pytest.raises(ValueError):
        query.run_query(DATA, [("nope", {"id": 1})])


def test_build_query_end_to_end():
    raw_rows = [("filter", "dept__name=Eng"), ("exclude", "name=Cy")]
    assert query.build_query(DATA, raw_rows) == [DATA[0]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_query.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/query.py`:

```python
"""Parse query-bar tokens and run collection-query against list data."""

from collection_query import ListQuery

_VALID_OPS = ("filter", "exclude")


def coerce_scalar(s):
    """Coerce a string token value to int, float, bool, None, or str."""
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def coerce_value(token):
    """Coerce a token value to a scalar, list (a,b,c) or range (lo..hi)."""
    if ".." in token:
        lo, _, hi = token.partition("..")
        return range(int(lo), int(hi))
    if "," in token:
        return [coerce_scalar(part.strip()) for part in token.split(",")]
    return coerce_scalar(token)


def parse_token(token):
    """Parse 'field__lookup=value' into (key, coerced_value)."""
    if "=" not in token:
        raise ValueError(f"Invalid token (missing '='): {token!r}")
    key, _, value = token.partition("=")
    key = key.strip()
    if not key:
        raise ValueError(f"Empty field name in token: {token!r}")
    return key, coerce_value(value.strip())


def parse_tokens(text):
    """Parse whitespace-separated tokens into a kwargs dict."""
    return dict(parse_token(tok) for tok in text.split())


def run_query(data, rows):
    """Run filter/exclude rows against list data and return the result list.

    rows: list of (op, kwargs) where op is 'filter' or 'exclude'.
    """
    if not isinstance(data, list):
        raise ValueError("Query target must be a JSON array (list).")
    result = ListQuery(data)
    for op, kwargs in rows:
        if op not in _VALID_OPS:
            raise ValueError(f"Unknown query op: {op!r}")
        result = getattr(result, op)(**kwargs)
    return list(result)


def build_query(data, raw_rows):
    """Run query rows given as (op, token_text) strings."""
    rows = [(op, parse_tokens(text)) for op, text in raw_rows]
    return run_query(data, rows)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_query.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/query.py tests/test_query.py
git commit -m "feat: add collection-query token parsing and execution"
```

---

### Task 4: search module

**Files:**
- Create: `jfather/search.py`
- Test: `tests/test_search.py`

**Interfaces:**
- Produces:
  - `search(data, term, *, keys=True, values=True, case_sensitive=False) -> list[list]`
    returns depth-first list of paths; each path is a list of dict-keys/list-indices.
    A matched dict key yields the path ending in that key; a matched leaf value
    yields the path to that leaf.

- [ ] **Step 1: Write the failing test**

Create `tests/test_search.py`:

```python
from jfather import search

DATA = {
    "user": {"name": "Alice", "role": "admin"},
    "items": [{"name": "apple"}, {"name": "banana"}],
}


def test_search_matches_values():
    assert search.search(DATA, "alice") == [["user", "name"]]


def test_search_matches_keys():
    paths = search.search(DATA, "role")
    assert ["user", "role"] in paths


def test_search_case_sensitive():
    assert search.search(DATA, "alice", case_sensitive=True) == []
    assert search.search(DATA, "Alice", case_sensitive=True) == [["user", "name"]]


def test_search_values_only():
    paths = search.search(DATA, "name", keys=False, values=True)
    assert paths == []


def test_search_into_list():
    paths = search.search(DATA, "banana")
    assert paths == [["items", 1, "name"]]


def test_search_depth_first_order():
    data = {"a": "x", "b": "x"}
    assert search.search(data, "x") == [["a"], ["b"]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_search.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/search.py`:

```python
"""Search keys and values within a parsed JSON object, returning paths."""


def search(data, term, *, keys=True, values=True, case_sensitive=False):
    """Return depth-first list of paths where a key or value matches term."""
    needle = term if case_sensitive else term.lower()

    def matches(text):
        text = str(text)
        if not case_sensitive:
            text = text.lower()
        return needle in text

    results = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if keys and matches(key):
                    results.append(path + [key])
                walk(value, path + [key])
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, path + [index])
        else:
            if values and matches(node):
                results.append(path)

    walk(data, [])
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_search.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/search.py tests/test_search.py
git commit -m "feat: add key/value search returning paths"
```

---

### Task 5: document module (Document + DocumentManager)

**Files:**
- Create: `jfather/document.py`
- Test: `tests/test_document.py`

**Interfaces:**
- Consumes: `jfather.jsontools.parse`.
- Produces:
  - `Document(text="", path=None, name=None)` with attributes:
    `text`, `path`, `name`, `dirty`, `query_rows: list`, `search_term: str`,
    `expanded_paths: set`.
    - `set_text(text) -> None` (sets `dirty=True` if changed)
    - `parsed() -> object` (raises `json.JSONDecodeError`)
    - `mark_saved(path=None) -> None`
  - `DocumentManager()` with:
    - `documents: list[Document]`, `active_index: int`, `active -> Document | None`
    - `new(text="", name=None) -> Document`
    - `open(path) -> Document`
    - `close(index) -> Document | None`
    - `switch(index) -> Document | None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_document.py`:

```python
import pytest
from jfather.document import Document, DocumentManager


def test_document_default_name():
    assert Document().name == "untitled"


def test_document_name_from_path():
    assert Document(path="/tmp/data.json").name == "data.json"


def test_set_text_marks_dirty():
    doc = Document(text="{}")
    assert doc.dirty is False
    doc.set_text("{}")
    assert doc.dirty is False
    doc.set_text('{"a": 1}')
    assert doc.dirty is True


def test_parsed():
    assert Document(text='{"a": 1}').parsed() == {"a": 1}


def test_mark_saved_clears_dirty_and_sets_path():
    doc = Document(text="{}")
    doc.set_text('{"a": 1}')
    doc.mark_saved("/tmp/x.json")
    assert doc.dirty is False
    assert doc.path == "/tmp/x.json"
    assert doc.name == "x.json"


def test_manager_new_sets_active():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    d2 = mgr.new(name="two")
    assert mgr.documents == [d1, d2]
    assert mgr.active is d2


def test_manager_switch():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    mgr.new(name="two")
    assert mgr.switch(0) is d1
    assert mgr.active is d1


def test_manager_open(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"a": 1}')
    mgr = DocumentManager()
    doc = mgr.open(str(f))
    assert doc.text == '{"a": 1}'
    assert doc.name == "data.json"
    assert mgr.active is doc


def test_manager_close_adjusts_active():
    mgr = DocumentManager()
    mgr.new(name="one")
    d2 = mgr.new(name="two")
    mgr.new(name="three")  # active index 2
    mgr.close(2)
    assert mgr.active is d2  # index clamped to 1
    mgr.close(0)
    assert mgr.active is d2  # index shifted to 0
    mgr.close(0)
    assert mgr.active is None


def test_state_isolated_between_documents():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    d2 = mgr.new(name="two")
    d1.query_rows.append(("filter", "id__gt=1"))
    assert d2.query_rows == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_document.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/document.py`:

```python
"""Document model and multi-document manager."""

import os

from . import jsontools


class Document:
    """A single JSON document with its own isolated UI state."""

    def __init__(self, text="", path=None, name=None):
        self.text = text
        self.path = path
        self.name = name or (os.path.basename(path) if path else "untitled")
        self.dirty = False
        self.query_rows = []
        self.search_term = ""
        self.expanded_paths = set()

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self.dirty = True

    def parsed(self):
        """Parse this document's text. Raises json.JSONDecodeError."""
        return jsontools.parse(self.text)

    def mark_saved(self, path=None):
        if path is not None:
            self.path = path
            self.name = os.path.basename(path)
        self.dirty = False


class DocumentManager:
    """Holds the list of open documents and the active selection."""

    def __init__(self):
        self.documents = []
        self.active_index = -1

    @property
    def active(self):
        if 0 <= self.active_index < len(self.documents):
            return self.documents[self.active_index]
        return None

    def new(self, text="", name=None):
        doc = Document(text=text, name=name)
        self.documents.append(doc)
        self.active_index = len(self.documents) - 1
        return doc

    def open(self, path):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        doc = Document(text=text, path=path)
        self.documents.append(doc)
        self.active_index = len(self.documents) - 1
        return doc

    def switch(self, index):
        if 0 <= index < len(self.documents):
            self.active_index = index
        return self.active

    def close(self, index):
        if not (0 <= index < len(self.documents)):
            return self.active
        del self.documents[index]
        if not self.documents:
            self.active_index = -1
        elif index < self.active_index:
            self.active_index -= 1
        elif self.active_index >= len(self.documents):
            self.active_index = len(self.documents) - 1
        return self.active
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_document.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/document.py tests/test_document.py
git commit -m "feat: add Document and DocumentManager"
```

---

### Task 6: tree_model (lazy QAbstractItemModel)

**Files:**
- Create: `jfather/tree_model.py`
- Test: `tests/test_tree_model.py`

**Interfaces:**
- Consumes: PySide6 `QAbstractItemModel`.
- Produces:
  - `JsonNode(key, value, parent=None, row=0)` with `is_container`, `child_count() -> int`, `children() -> list[JsonNode]` (lazy).
  - `type_name(value) -> str` → one of `object`, `array`, `string`, `number`, `boolean`, `null`.
  - `JsonTreeModel(data=None)` with `set_json(data) -> None`, columns `["Key","Value","Type"]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tree_model.py`:

```python
from PySide6.QtCore import QModelIndex, Qt
from jfather.tree_model import JsonNode, JsonTreeModel, type_name


def test_type_name():
    assert type_name({}) == "object"
    assert type_name([]) == "array"
    assert type_name("s") == "string"
    assert type_name(1) == "number"
    assert type_name(1.5) == "number"
    assert type_name(True) == "boolean"
    assert type_name(None) == "null"


def test_node_child_count_without_building():
    node = JsonNode("root", {"a": 1, "b": 2})
    assert node.child_count() == 2
    assert node._children is None  # not built yet


def test_node_children_lazy_build():
    node = JsonNode("root", [10, 20])
    children = node.children()
    assert [c.key for c in children] == [0, 1]
    assert [c.value for c in children] == [10, 20]


def test_node_leaf_has_no_children():
    assert JsonNode("k", 5).child_count() == 0
    assert JsonNode("k", 5).is_container is False


def test_model_rowcount_and_data():
    model = JsonTreeModel({"a": 1})
    assert model.rowCount(QModelIndex()) == 1
    idx_key = model.index(0, 0, QModelIndex())
    idx_val = model.index(0, 1, QModelIndex())
    idx_type = model.index(0, 2, QModelIndex())
    assert model.data(idx_key, Qt.DisplayRole) == "a"
    assert model.data(idx_val, Qt.DisplayRole) == "1"
    assert model.data(idx_type, Qt.DisplayRole) == "number"


def test_model_nested_parent_child():
    model = JsonTreeModel({"outer": {"inner": 1}})
    outer = model.index(0, 0, QModelIndex())
    assert model.rowCount(outer) == 1
    inner = model.index(0, 0, outer)
    assert model.data(inner, Qt.DisplayRole) == "inner"
    assert model.parent(inner) == outer


def test_model_container_value_summary():
    model = JsonTreeModel({"a": [1, 2, 3]})
    val = model.index(0, 1, QModelIndex())
    assert model.data(val, Qt.DisplayRole) == "[3 items]"


def test_set_json_resets():
    model = JsonTreeModel({"a": 1})
    model.set_json([1, 2])
    assert model.rowCount(QModelIndex()) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_tree_model.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/tree_model.py`:

```python
"""Lazy Qt tree model exposing a parsed JSON object."""

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


def type_name(value):
    """Return the JSON type name for a Python value."""
    if isinstance(value, bool):
        return "boolean"
    if value is None:
        return "null"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return "string"


class JsonNode:
    """A node wrapping a key/value; children are built lazily."""

    def __init__(self, key, value, parent=None, row=0):
        self.key = key
        self.value = value
        self.parent = parent
        self.row = row
        self._children = None

    @property
    def is_container(self):
        return isinstance(self.value, (dict, list))

    def child_count(self):
        if isinstance(self.value, dict):
            return len(self.value)
        if isinstance(self.value, list):
            return len(self.value)
        return 0

    def children(self):
        if self._children is None:
            self._children = []
            if isinstance(self.value, dict):
                for row, (key, value) in enumerate(self.value.items()):
                    self._children.append(JsonNode(key, value, self, row))
            elif isinstance(self.value, list):
                for row, value in enumerate(self.value):
                    self._children.append(JsonNode(row, value, self, row))
        return self._children


def _value_text(value):
    if isinstance(value, dict):
        return "{%d items}" % len(value)
    if isinstance(value, list):
        return "[%d items]" % len(value)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class JsonTreeModel(QAbstractItemModel):
    """Read/display model over a parsed JSON object."""

    HEADERS = ["Key", "Value", "Type"]

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._root = JsonNode("root", data if data is not None else {})

    def set_json(self, data):
        self.beginResetModel()
        self._root = JsonNode("root", data if data is not None else {})
        self.endResetModel()

    def _node(self, index):
        if index.isValid():
            return index.internalPointer()
        return self._root

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        children = self._node(parent).children()
        if 0 <= row < len(children):
            return self.createIndex(row, column, children[row])
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        parent = index.internalPointer().parent
        if parent is None or parent is self._root:
            return QModelIndex()
        return self.createIndex(parent.row, 0, parent)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        return self._node(parent).child_count()

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def hasChildren(self, parent=QModelIndex()):
        return self._node(parent).child_count() > 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        node = index.internalPointer()
        column = index.column()
        if column == 0:
            return str(node.key)
        if column == 1:
            return _value_text(node.value)
        if column == 2:
            return type_name(node.value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_tree_model.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/tree_model.py tests/test_tree_model.py
git commit -m "feat: add lazy JSON tree model"
```

---

### Task 7: editor (text edit + JSON syntax highlighter)

**Files:**
- Create: `jfather/editor.py`
- Test: `tests/test_editor.py`

**Interfaces:**
- Consumes: PySide6 widgets.
- Produces:
  - `JsonHighlighter(document)` — `QSyntaxHighlighter` coloring JSON tokens.
  - `JsonEditor(QPlainTextEdit)` with `text() -> str`, `set_text(str) -> None`
    (does not emit a change signal while setting), signal `textChangedDebounced` not required;
    expose `toPlainText`/`setPlainText` defaults plus a monospace font.

- [ ] **Step 1: Write the failing test**

Create `tests/test_editor.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication
from jfather.editor import JsonEditor, JsonHighlighter


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_editor_set_and_get_text(app):
    editor = JsonEditor()
    editor.set_text('{"a": 1}')
    assert editor.text() == '{"a": 1}'


def test_editor_has_highlighter(app):
    editor = JsonEditor()
    assert isinstance(editor.highlighter, JsonHighlighter)


def test_set_text_is_idempotent_noop_when_same(app):
    editor = JsonEditor()
    editor.set_text("{}")
    editor.set_text("{}")
    assert editor.text() == "{}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_editor.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/editor.py`:

```python
"""JSON text editor with syntax highlighting."""

import re

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import QPlainTextEdit


def _fmt(color, bold=False):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Bold)
    return fmt


class JsonHighlighter(QSyntaxHighlighter):
    """Minimal JSON syntax highlighter."""

    def __init__(self, document):
        super().__init__(document)
        self._rules = [
            (QRegularExpression(r'"(\\.|[^"\\])*"\s*:'), _fmt("#7aa2f7", bold=True)),
            (QRegularExpression(r'"(\\.|[^"\\])*"'), _fmt("#9ece6a")),
            (QRegularExpression(r"\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b"), _fmt("#ff9e64")),
            (QRegularExpression(r"\b(true|false|null)\b"), _fmt("#bb9af7")),
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                # For key rule, don't recolor the trailing colon/space.
                matched = match.captured()
                if matched.rstrip().endswith(":"):
                    length = len(matched.rstrip()) - len(matched) + length
                self.setFormat(start, length, fmt)


class JsonEditor(QPlainTextEdit):
    """Plain-text JSON editor with monospace font and highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font = QFont("Menlo")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(12)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = JsonHighlighter(self.document())

    def text(self):
        return self.toPlainText()

    def set_text(self, text):
        if text != self.toPlainText():
            self.setPlainText(text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_editor.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/editor.py tests/test_editor.py
git commit -m "feat: add JSON text editor with syntax highlighting"
```

---

### Task 8: sidebar (document list widget)

**Files:**
- Create: `jfather/sidebar.py`
- Test: `tests/test_sidebar.py`

**Interfaces:**
- Consumes: PySide6 widgets, `jfather.document.DocumentManager`.
- Produces:
  - `DocumentSidebar(QWidget)`:
    - signals: `documentSelected(int)`, `documentCloseRequested(int)`, `newRequested()`
    - `refresh(manager: DocumentManager) -> None` rebuilds the list; unsaved docs show a leading `• `; active row is selected.

- [ ] **Step 1: Write the failing test**

Create `tests/test_sidebar.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication
from jfather.document import DocumentManager
from jfather.sidebar import DocumentSidebar


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_refresh_lists_documents(app):
    mgr = DocumentManager()
    mgr.new(name="one")
    mgr.new(name="two")
    bar = DocumentSidebar()
    bar.refresh(mgr)
    assert bar.list.count() == 2
    assert bar.list.item(1).text() == "two"


def test_dirty_marker(app):
    mgr = DocumentManager()
    doc = mgr.new(name="one")
    doc.dirty = True
    bar = DocumentSidebar()
    bar.refresh(mgr)
    assert bar.list.item(0).text().startswith("\u2022 ")


def test_active_row_selected(app):
    mgr = DocumentManager()
    mgr.new(name="one")
    mgr.new(name="two")
    mgr.switch(0)
    bar = DocumentSidebar()
    bar.refresh(mgr)
    assert bar.list.currentRow() == 0


def test_selection_emits_signal(app):
    mgr = DocumentManager()
    mgr.new(name="one")
    mgr.new(name="two")
    bar = DocumentSidebar()
    bar.refresh(mgr)
    seen = []
    bar.documentSelected.connect(seen.append)
    bar.list.setCurrentRow(1)
    assert seen[-1] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_sidebar.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/sidebar.py`:

```python
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.new_button = QPushButton("+ New")
        self.new_button.clicked.connect(self.newRequested.emit)
        layout.addWidget(self.new_button)

        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self._on_close_clicked)
        layout.addWidget(self.close_button)

        self.setMaximumWidth(220)

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_sidebar.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/sidebar.py tests/test_sidebar.py
git commit -m "feat: add document sidebar widget"
```

---

### Task 9: query panel widget

**Files:**
- Create: `jfather/query_panel.py`
- Test: `tests/test_query_panel.py`

**Interfaces:**
- Consumes: PySide6 widgets, `jfather.query`.
- Produces:
  - `QueryPanel(QWidget)`:
    - signal `runRequested(list)` emitting `raw_rows` = list of `(op, text)`.
    - `add_row(op="filter", text="") -> None`, `rows() -> list[tuple[str,str]]`,
      `set_rows(rows) -> None`, `set_results_text(str) -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_query_panel.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication
from jfather.query_panel import QueryPanel


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_add_and_read_rows(app):
    panel = QueryPanel()
    panel.set_rows([("filter", "id__gt=1"), ("exclude", "name=Bob")])
    assert panel.rows() == [("filter", "id__gt=1"), ("exclude", "name=Bob")]


def test_run_emits_rows(app):
    panel = QueryPanel()
    panel.set_rows([("filter", "id__gt=1")])
    seen = []
    panel.runRequested.connect(seen.append)
    panel.run_button.click()
    assert seen == [[("filter", "id__gt=1")]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_query_panel.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/query_panel.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_query_panel.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/query_panel.py tests/test_query_panel.py
git commit -m "feat: add collection-query builder panel"
```

---

### Task 10: app main window (wiring + theme) and launcher

**Files:**
- Create: `jfather/theme.py`
- Create: `jfather/app.py`
- Modify: `main.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: all prior modules.
- Produces:
  - `theme.STYLESHEET: str` (dark) and `theme.LIGHT_STYLESHEET: str`.
  - `MainWindow(QMainWindow)` with methods used by tests:
    `new_document()`, `current_text() -> str`, `apply_format()`, `apply_minify()`,
    `refresh_tree()`, `run_query(raw_rows)`, `query_target() -> object`.
  - `run() -> int` launching the app.

- [ ] **Step 1: Write the failing test**

Create `tests/test_app.py`:

```python
import json
import pytest
from PySide6.QtWidgets import QApplication
from jfather.app import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_starts_with_one_document(app):
    win = MainWindow()
    assert len(win.manager.documents) == 1


def test_new_document_adds_and_activates(app):
    win = MainWindow()
    win.new_document()
    assert len(win.manager.documents) == 2
    assert win.manager.active_index == 1


def test_apply_format(app):
    win = MainWindow()
    win.editor.set_text('{"a":1}')
    win.apply_format()
    assert win.current_text() == '{\n  "a": 1\n}'


def test_apply_minify(app):
    win = MainWindow()
    win.editor.set_text('{\n  "a": 1\n}')
    win.apply_minify()
    assert win.current_text() == '{"a":1}'


def test_run_query_on_root_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]))
    win.sync_from_editor()
    results = win.run_query([("filter", "id__gt=1")])
    assert results == [{"id": 2}, {"id": 3}]


def test_query_target_falls_back_to_root(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}]))
    win.sync_from_editor()
    assert win.query_target() == [{"id": 1}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `jfather/theme.py`:

```python
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
```

Create `jfather/app.py`:

```python
"""Main application window wiring all components."""

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from . import jsontools, query, theme
from .document import DocumentManager
from .editor import JsonEditor
from .query_panel import QueryPanel
from .sidebar import DocumentSidebar
from .tree_model import JsonTreeModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("jfather")
        self.resize(1200, 800)
        self._dark = True

        self.manager = DocumentManager()
        self.tree_model = JsonTreeModel({})

        self._build_ui()
        self._build_toolbar()
        self.setStyleSheet(theme.STYLESHEET)

        self.manager.new()
        self._load_active_into_views()
        self._refresh_sidebar()

        self._debounce = QTimer(self)
        self._debounce.setInterval(300)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self.sync_from_editor)
        self.editor.textChanged.connect(self._on_editor_changed)

    # ---- UI construction -------------------------------------------------
    def _build_ui(self):
        self.sidebar = DocumentSidebar()
        self.sidebar.documentSelected.connect(self._on_doc_selected)
        self.sidebar.documentCloseRequested.connect(self._on_doc_close)
        self.sidebar.newRequested.connect(self.new_document)

        self.editor = JsonEditor()

        self.tree = QTreeView()
        self.tree.setModel(self.tree_model)
        self.tree.clicked.connect(lambda *_: None)

        center_split = QSplitter(Qt.Horizontal)
        center_split.addWidget(self.editor)
        center_split.addWidget(self.tree)
        center_split.setSizes([600, 600])

        self.query_panel = QueryPanel()
        self.query_panel.runRequested.connect(self.run_query)

        right_split = QSplitter(Qt.Vertical)
        right_split.addWidget(center_split)
        right_split.addWidget(self.query_panel)
        right_split.setSizes([600, 200])

        outer = QSplitter(Qt.Horizontal)
        outer.addWidget(self.sidebar)
        outer.addWidget(right_split)
        outer.setSizes([200, 1000])

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(outer)
        self.setCentralWidget(container)

        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)

    def _build_toolbar(self):
        bar = QToolBar()
        self.addToolBar(bar)
        bar.addAction("New", self.new_document)
        bar.addAction("Open", self.open_file)
        bar.addAction("Save", self.save_file)
        bar.addSeparator()
        bar.addAction("Format", self.apply_format)
        bar.addAction("Minify", self.apply_minify)
        bar.addAction("Escape", self.apply_escape)
        bar.addAction("Unescape", self.apply_unescape)
        bar.addSeparator()
        bar.addAction("Theme", self.toggle_theme)

    # ---- Document lifecycle ---------------------------------------------
    def new_document(self):
        self.manager.new()
        self._load_active_into_views()
        self._refresh_sidebar()

    def open_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        for path in paths:
            self.manager.open(path)
        if paths:
            self._load_active_into_views()
            self._refresh_sidebar()

    def save_file(self):
        doc = self.manager.active
        if doc is None:
            return
        doc.set_text(self.editor.text())
        path = doc.path
        if path is None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save JSON", doc.name, "JSON Files (*.json)"
            )
            if not path:
                return
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(doc.text)
        doc.mark_saved(path)
        self._refresh_sidebar()

    def _on_doc_selected(self, index):
        self._store_active_state()
        self.manager.switch(index)
        self._load_active_into_views()

    def _on_doc_close(self, index):
        doc = self.manager.documents[index]
        if doc.dirty:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                f"Save changes to {doc.name}?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if answer == QMessageBox.Cancel:
                return
            if answer == QMessageBox.Save:
                self.manager.switch(index)
                self.save_file()
        self.manager.close(index)
        if self.manager.active is None:
            self.manager.new()
        self._load_active_into_views()
        self._refresh_sidebar()

    # ---- View sync -------------------------------------------------------
    def _store_active_state(self):
        doc = self.manager.active
        if doc is not None:
            doc.set_text(self.editor.text())
            doc.query_rows = self.query_panel.rows()

    def _load_active_into_views(self):
        doc = self.manager.active
        if doc is None:
            return
        self.editor.set_text(doc.text)
        self.query_panel.set_rows(doc.query_rows)
        self.refresh_tree()

    def _refresh_sidebar(self):
        self.sidebar.refresh(self.manager)

    def _on_editor_changed(self):
        doc = self.manager.active
        if doc is not None:
            was_dirty = doc.dirty
            doc.set_text(self.editor.text())
            if doc.dirty != was_dirty:
                self._refresh_sidebar()
        self._debounce.start()

    def sync_from_editor(self):
        self.refresh_tree()

    def refresh_tree(self):
        ok, message, line, col = jsontools.validate(self.editor.text())
        if ok:
            self.tree_model.set_json(jsontools.parse(self.editor.text()))
            self.status_label.setText("Valid JSON")
        else:
            self.status_label.setText(f"Invalid JSON: {message} (line {line}, col {col})")

    def current_text(self):
        return self.editor.text()

    # ---- Tools -----------------------------------------------------------
    def apply_format(self):
        try:
            self.editor.set_text(jsontools.format_json(self.editor.text()))
        except ValueError as exc:
            self.status_label.setText(f"Cannot format: {exc}")

    def apply_minify(self):
        try:
            self.editor.set_text(jsontools.minify_json(self.editor.text()))
        except ValueError as exc:
            self.status_label.setText(f"Cannot minify: {exc}")

    def apply_escape(self):
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(jsontools.escape_string(selected))

    def apply_unescape(self):
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            try:
                cursor.insertText(jsontools.unescape_string(selected))
            except ValueError as exc:
                self.status_label.setText(f"Cannot unescape: {exc}")

    def toggle_theme(self):
        self._dark = not self._dark
        self.setStyleSheet(theme.STYLESHEET if self._dark else theme.LIGHT_STYLESHEET)

    # ---- Query -----------------------------------------------------------
    def query_target(self):
        indexes = self.tree.selectionModel().selectedIndexes() if self.tree.selectionModel() else []
        for index in indexes:
            node = index.internalPointer()
            if node is not None and isinstance(node.value, list):
                return node.value
        try:
            data = jsontools.parse(self.editor.text())
        except ValueError:
            return None
        return data if isinstance(data, list) else None

    def run_query(self, raw_rows):
        target = self.query_target()
        if not isinstance(target, list):
            self.query_panel.set_results_text("Query target must be a JSON array.")
            return []
        try:
            results = query.build_query(target, raw_rows)
        except (ValueError, TypeError) as exc:
            self.query_panel.set_results_text(f"Query error: {exc}")
            return []
        import json

        self.query_panel.set_results_text(
            f"{len(results)} result(s)\n\n" + json.dumps(results, indent=2, ensure_ascii=False)
        )
        return results


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
```

Modify `main.py`:

```python
from jfather.app import run


def main():
    raise SystemExit(run())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/theme.py jfather/app.py main.py tests/test_app.py
git commit -m "feat: wire main window, theme, and launcher"
```

---

### Task 11: Full suite + manual smoke + README

**Files:**
- Modify: `README.md`

**Interfaces:** none.

- [ ] **Step 1: Run the full test suite**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest -v`
Expected: ALL tests pass.

- [ ] **Step 2: Manual smoke launch (skip if no display)**

Run: `uv run python main.py`
Expected: window opens with sidebar, editor, tree, and query panel; loading a JSON file populates the tree; Format/Minify/Escape work; a query like `id__gt=1` returns results. Close the window.

- [ ] **Step 3: Write README usage**

Replace `README.md` with:

```markdown
# jfather

A fast, modern desktop app to view and edit large JSON, with formatting,
escaping, tree visualization, search, and collection-query querying.

## Run

```bash
uv sync
uv run python main.py
```

## Features

- Multiple documents via the left sidebar (New / Open / Close, dirty markers).
- Dual-pane: syntax-highlighted text editor + lazy tree view.
- Format, Minify, Escape, Unescape (selection-aware).
- Query the selected array (or root array) with collection-query syntax, e.g.
  `field__lookup=value` tokens with filter/exclude rows. Lists: `a,b,c`.
  Ranges: `lo..hi`.

## Test

```bash
QT_QPA_PLATFORM=offscreen uv run pytest -v
```
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add jfather README"
```

---

## Self-Review Notes

- **Spec coverage:** multi-document (Tasks 5, 8, 10), formatting (2, 10), escaping (2, 10), visualization/tree (6, 10), search module (4; UI wiring is light — search box integration is covered by the `search` module and can be surfaced in the tree pane during Task 10 polish if desired), query (3, 9, 10), error handling (validate in 2, query guards in 3/10), theme (10), testing (every task).
- **Note:** The search *box UI* in the right pane is not wired as its own task; the `search` module is complete and tested. If interactive in-tree highlighting is required, add a follow-up task wiring `search.search` to tree selection. Flagged here rather than silently dropped.
- **Type consistency:** `set_json` (tree_model), `set_text`/`text` (editor), `build_query`/`run_query` (query), `refresh`/`rows`/`set_rows` used consistently across producers and consumers.
