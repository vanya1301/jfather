# jfather UI Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the jfather PySide6 desktop UI with sophisticated typography, a warm dark theme, restructured toolbar, line-number gutter, breadcrumb pills + drill-in hint, sortable/resizable table with nested-cell tooltips, and a streamlined query panel — keeping all existing behavior and tests green.

**Architecture:** Incremental, component-by-component changes to the existing module layout (`app.py` orchestrator + per-widget modules + `theme.py` QSS). Presentation lives in `theme.py` (QSS, object-name selectors) and per-widget constructors. Table sorting is added via a `QSortFilterProxyModel` between `JsonTableModel` and the `QTableView`, with all view↔data index conversions routed through `mapToSource`/`mapFromSource`.

**Tech Stack:** Python 3.12, PySide6 (Qt6), pytest. Run tests with `QT_QPA_PLATFORM=offscreen`.

## Global Constraints

- Python `>=3.12`; PySide6 `>=6.6`; no new runtime dependencies (icons are Unicode glyphs).
- `theme.py` must NOT contain a universal `QWidget {` rule and must NOT contain any `QScrollBar` styling (native scrollbars preserved). Enforced by `tests/test_theme.py`.
- All existing public APIs used by tests must keep working: `MainWindow.shortcut_actions` (keys: close/save/format/run/find), `QueryPanel.rows/set_rows/current_rows/run_button/set_run_enabled`, `Breadcrumb.buttons` text values, `DocumentSidebar` signals + `list`, `JsonTableModel.row_object/set_rows/headerData`.
- Run the full suite with: `QT_QPA_PLATFORM=offscreen uv run pytest -q`.
- Font families (verbatim):
  - UI sans: `"Inter, SF Pro Text, Segoe UI, sans-serif"`
  - Mono: `"Menlo, SF Mono, Consolas, monospace"`
- Fixed copy strings (verbatim):
  - Find placeholder: `Find in file…`
  - Drill-in hint: `Double-click a row or node to focus`
- Commit after every task.

---

### Task 1: Warm dark theme + fonts, remove light theme

**Files:**
- Modify: `jfather/theme.py` (full rewrite)
- Test: `tests/test_theme.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `theme.STYLESHEET` (str), `theme.UI_FONT_FAMILY` (str), `theme.MONO_FONT_FAMILY` (str). `theme.LIGHT_STYLESHEET` is REMOVED.

- [ ] **Step 1: Update the theme tests to dark-only + font constants**

Replace the contents of `tests/test_theme.py` with:

```python
from jfather import theme


def test_no_universal_widget_rule():
    assert "QWidget {" not in theme.STYLESHEET
    assert "QWidget{" not in theme.STYLESHEET


def test_no_scrollbar_styling():
    assert "QScrollBar" not in theme.STYLESHEET


def test_styles_concrete_widgets():
    assert "QPlainTextEdit" in theme.STYLESHEET
    assert "QTableView" in theme.STYLESHEET
    assert "QPushButton" in theme.STYLESHEET


def test_light_theme_removed():
    assert not hasattr(theme, "LIGHT_STYLESHEET")


def test_font_constants_present():
    assert "sans-serif" in theme.UI_FONT_FAMILY
    assert "monospace" in theme.MONO_FONT_FAMILY
```

- [ ] **Step 2: Run the theme tests to verify they fail**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_theme.py -q`
Expected: FAIL (`LIGHT_STYLESHEET` still present / font constants missing).

- [ ] **Step 3: Rewrite `jfather/theme.py`**

Replace the entire file with:

```python
"""Qt stylesheet + font constants for jfather (single warm dark theme).

Scoped to concrete widget classes / object names so native scrollbars and
other OS controls render normally (no universal QWidget or QScrollBar rules).
"""

UI_FONT_FAMILY = "Inter, SF Pro Text, Segoe UI, sans-serif"
MONO_FONT_FAMILY = "Menlo, SF Mono, Consolas, monospace"

# Warm-neutral dark palette.
_BG = "#1c1b1a"
_PANEL = "#161514"
_SIDEBAR = "#211f1d"
_BORDER = "#33302c"
_TEXT = "#e6e1da"
_MUTED = "#9a948c"
_ACCENT = "#7aa2f7"
_BTN = "#2c2925"
_BTN_HOVER = "#3a352f"
_BTN_DISABLED_BG = "#242220"
_BTN_DISABLED_FG = "#5b554d"
_SELECTION = "#3a4a6b"

STYLESHEET = f"""
QMainWindow, QToolBar, QStatusBar, QLabel {{
    background: {_BG}; color: {_TEXT};
    font-family: {UI_FONT_FAMILY};
}}
QToolBar {{ border: none; spacing: 10px; padding: 8px 12px; }}
QToolBar::separator {{ background: {_BORDER}; width: 1px; margin: 4px 6px; }}
QStatusBar {{ background: {_PANEL}; color: {_MUTED}; padding: 4px 10px; }}

QPlainTextEdit, QTreeView, QTableView, QListWidget, QLineEdit, QComboBox {{
    background: {_PANEL}; color: {_TEXT};
    border: 1px solid {_BORDER}; border-radius: 8px;
    selection-background-color: {_SELECTION};
    font-family: {UI_FONT_FAMILY};
    padding: 2px;
}}
QLineEdit {{ padding: 6px 10px; }}
QComboBox {{ padding: 4px 8px; }}

QListWidget {{ outline: none; }}
QListWidget::item {{ padding: 7px 10px; border-radius: 6px; }}
QListWidget::item:selected {{ background: {_BTN_HOVER}; color: {_TEXT}; }}

QWidget#documentSidebar {{ background: {_SIDEBAR}; }}

QPushButton {{
    background: {_BTN}; color: {_TEXT}; border: none; border-radius: 8px;
    padding: 7px 14px; font-family: {UI_FONT_FAMILY};
}}
QPushButton:hover {{ background: {_BTN_HOVER}; }}
QPushButton:disabled {{ background: {_BTN_DISABLED_BG}; color: {_BTN_DISABLED_FG}; }}

QPushButton#breadcrumbPill {{
    background: {_BTN}; border-radius: 11px; padding: 4px 12px; color: {_TEXT};
}}
QPushButton#breadcrumbPill:hover {{ background: {_BTN_HOVER}; }}

QLabel#drillHint {{ color: {_MUTED}; font-style: italic; padding: 0 8px; }}

QHeaderView::section {{
    background: {_PANEL}; color: {_TEXT}; border: none;
    border-bottom: 1px solid {_BORDER}; padding: 6px 8px;
}}
"""
```

- [ ] **Step 4: Run the theme tests to verify they pass**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_theme.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/theme.py tests/test_theme.py
git commit -m "feat: warm dark theme + font constants, remove light theme"
```

---

### Task 2: Sidebar — distinct background + `+ New` moved to bottom

**Files:**
- Modify: `jfather/sidebar.py`
- Test: `tests/test_sidebar.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `DocumentSidebar` keeps signals `documentSelected/documentCloseRequested/newRequested`, attribute `list`, `new_button`, `close_button`. New: `objectName()` == `"documentSidebar"`; `new_button` is positioned after the list (bottom).

- [ ] **Step 1: Add tests for bottom placement + object name**

Append to `tests/test_sidebar.py`:

```python
def test_has_object_name(app):
    bar = DocumentSidebar()
    assert bar.objectName() == "documentSidebar"


def test_new_button_below_list(app):
    bar = DocumentSidebar()
    layout = bar.layout()
    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    assert widgets.index(bar.list) < widgets.index(bar.new_button)
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_sidebar.py -q`
Expected: FAIL (no object name; `new_button` currently above list).

- [ ] **Step 3: Update `DocumentSidebar.__init__`**

In `jfather/sidebar.py`, replace the body of `__init__` (after `self._suppress = False`) with:

```python
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
```

- [ ] **Step 4: Run to verify pass (sidebar + still-passing existing)**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_sidebar.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/sidebar.py tests/test_sidebar.py
git commit -m "feat: sidebar warm bg + New button at bottom"
```

---

### Task 3: Editor — line-number gutter

**Files:**
- Modify: `jfather/editor.py`
- Test: `tests/test_editor.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `JsonEditor.line_number_area_width() -> int` (> 0), `JsonEditor.line_number_area` (a `LineNumberArea` widget). All existing methods (`text/set_text/find_matches/find_next/clear_find`) unchanged.

- [ ] **Step 1: Add gutter tests**

Append to `tests/test_editor.py` (keep existing imports; add `QApplication` fixture if not present — check the file and reuse its fixture):

```python
def test_line_number_area_width_positive(app):
    from jfather.editor import JsonEditor
    ed = JsonEditor()
    ed.set_text("{\n  \"a\": 1\n}")
    assert ed.line_number_area_width() > 0


def test_line_number_area_widget_exists(app):
    from jfather.editor import JsonEditor
    ed = JsonEditor()
    assert ed.line_number_area is not None
```

If `tests/test_editor.py` has no `app` fixture, add at the top after imports:

```python
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_editor.py -q`
Expected: FAIL (`line_number_area` / `line_number_area_width` missing).

- [ ] **Step 3: Implement the gutter**

In `jfather/editor.py`, update imports and add the gutter. Change the import lines to include the needed symbols:

```python
from PySide6.QtCore import QRect, QRegularExpression, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
```

Add this class above `class JsonEditor`:

```python
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.paint_line_numbers(event)
```

In `JsonEditor.__init__`, after `self.setFont(font)` and before `self.setLineWrapMode(...)`, insert:

```python
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)
```

Add these methods to `JsonEditor` (e.g. after `clear_find`):

```python
    def line_number_area_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#161514"))
        painter.setPen(QColor("#5b554d"))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        width = self.line_number_area.width() - 6
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    0, int(top), width, self.fontMetrics().height(),
                    Qt.AlignRight, str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            number += 1
```

- [ ] **Step 4: Run editor tests**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_editor.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/editor.py tests/test_editor.py
git commit -m "feat: editor line-number gutter"
```

---

### Task 4: Find bar — placeholder text + polish

**Files:**
- Modify: `jfather/find_bar.py`
- Test: `tests/test_find_bar.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `FindBar.input.placeholderText() == "Find in file…"`. Signals/attrs unchanged.

- [ ] **Step 1: Add placeholder test**

Append to `tests/test_find_bar.py` (reuse the file's existing `app` fixture; if none, add the standard fixture as in Task 3 Step 1):

```python
def test_placeholder_text(app):
    from jfather.find_bar import FindBar
    bar = FindBar()
    assert bar.input.placeholderText() == "Find in file\u2026"
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_find_bar.py -q`
Expected: FAIL (placeholder is currently `"Find…"`).

- [ ] **Step 3: Update placeholder + spacing**

In `jfather/find_bar.py`, change:

```python
        self.input.setPlaceholderText("Find\u2026")
```
to:
```python
        self.input.setPlaceholderText("Find in file\u2026")
```

And change the layout margins line:
```python
        layout.setContentsMargins(0, 0, 0, 0)
```
to:
```python
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
```

- [ ] **Step 4: Run to verify pass**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_find_bar.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/find_bar.py tests/test_find_bar.py
git commit -m "feat: find bar 'Find in file' placeholder + spacing"
```

---

### Task 5: Breadcrumb pills + drill-in hint

**Files:**
- Modify: `jfather/breadcrumb.py`
- Test: `tests/test_breadcrumb.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `Breadcrumb` crumb buttons get `objectName "breadcrumbPill"` (button TEXT values UNCHANGED — `["root", ...]`). New: `Breadcrumb.hint` (a `QLabel` with objectName `"drillHint"`, text `"Double-click a row or node to focus"`) shown only when path is empty (`set_path([])`), hidden otherwise.

- [ ] **Step 1: Add hint + pill tests**

Append to `tests/test_breadcrumb.py`:

```python
def test_crumbs_are_pills(app):
    bar = Breadcrumb()
    bar.set_path(["users"])
    assert all(b.objectName() == "breadcrumbPill" for b in bar.buttons)


def test_hint_visible_only_at_root(app):
    bar = Breadcrumb()
    bar.show()
    bar.set_path([])
    assert bar.hint.text() == "Double-click a row or node to focus"
    assert bar.hint.isVisible() is True
    bar.set_path(["users"])
    assert bar.hint.isVisible() is False
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_breadcrumb.py -q`
Expected: FAIL (`hint` missing; no object name).

- [ ] **Step 3: Update `Breadcrumb`**

In `jfather/breadcrumb.py`, update imports to include `QLabel` (already imported). In `__init__`, after `self.buttons = []` add:

```python
        self.hint = QLabel("Double-click a row or node to focus")
        self.hint.setObjectName("drillHint")
        self.hint.hide()
```

In `_clear`, do NOT delete `self.hint` (it is re-added each render). Keep `_clear` removing only the items it added; since `set_path` rebuilds the layout, re-add the hint each time. Replace `set_path` with:

```python
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
```

Note: `_clear` calls `widget.deleteLater()` on every child including the previously-added `hint`. To avoid deleting `hint`, change `_clear` to skip it:

```python
    def _clear(self):
        self.buttons = []
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self.hint:
                widget.deleteLater()
```

(`self.hint` must be created before the first `set_path` call — it already is, since `__init__` creates it before calling `self.set_path([])`.)

- [ ] **Step 4: Run breadcrumb tests**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_breadcrumb.py -q`
Expected: PASS (including pre-existing text assertions `["root", ...]`).

- [ ] **Step 5: Commit**

```bash
git add jfather/breadcrumb.py tests/test_breadcrumb.py
git commit -m "feat: breadcrumb pills + drill-in hint"
```

---

### Task 6: Table model — compact nested display + tooltip JSON + mono font

**Files:**
- Modify: `jfather/table_model.py`
- Test: `tests/test_table_model.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `JsonTableModel.data(index, Qt.DisplayRole)` returns compact summaries for nested values: dict -> `"{…} N keys"`, list -> `"[…] N items"`. `data(index, Qt.ToolTipRole)` returns pretty-printed JSON (indent=2) for nested values, else `None`. Scalars unchanged.

- [ ] **Step 1: Update nested-rendering test + add tooltip test**

In `tests/test_table_model.py`, replace `test_cell_scalar_and_nested_rendering` with:

```python
def test_cell_scalar_and_nested_rendering():
    model = JsonTableModel([{"a": 1, "b": {"x": 2}, "c": [1, 2, 3]}])
    a = model.index(0, 0, QModelIndex())
    b = model.index(0, 1, QModelIndex())
    c = model.index(0, 2, QModelIndex())
    assert model.data(a, Qt.DisplayRole) == "1"
    assert model.data(b, Qt.DisplayRole) == "{\u2026} 1 key"
    assert model.data(c, Qt.DisplayRole) == "[\u2026] 3 items"


def test_nested_cell_tooltip_is_pretty_json():
    model = JsonTableModel([{"b": {"x": 2}}])
    b = model.index(0, 0, QModelIndex())
    tip = model.data(b, Qt.ToolTipRole)
    assert tip == '{\n  "x": 2\n}'


def test_scalar_cell_has_no_tooltip():
    model = JsonTableModel([{"a": 1}])
    a = model.index(0, 0, QModelIndex())
    assert model.data(a, Qt.ToolTipRole) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_table_model.py -q`
Expected: FAIL (display still full JSON; no ToolTipRole handling).

- [ ] **Step 3: Update `table_model.py`**

Replace `_cell_text` with two helpers:

```python
def _cell_display(value):
    if isinstance(value, dict):
        n = len(value)
        return f"{{\u2026}} {n} key" + ("" if n == 1 else "s")
    if isinstance(value, list):
        n = len(value)
        return f"[\u2026] {n} item" + ("" if n == 1 else "s")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _cell_tooltip(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return None
```

Replace the `data` method with:

```python
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._rows[index.row()]
        if isinstance(item, dict):
            key = self._columns[index.column()]
            value = item[key] if key in item else None
            present = key in item
        else:
            value = item if index.column() == 0 else None
            present = index.column() == 0
        if role == Qt.DisplayRole:
            if not present:
                return ""
            return _cell_display(value)
        if role == Qt.ToolTipRole:
            if not present:
                return None
            return _cell_tooltip(value)
        return None
```

- [ ] **Step 4: Run table model tests**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_table_model.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add jfather/table_model.py tests/test_table_model.py
git commit -m "feat: compact nested table cells with JSON tooltips"
```

---

### Task 7: Table view — sortable/resizable via proxy, with correct row mapping

**Files:**
- Modify: `jfather/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `JsonTableModel` (Task 6), `theme` (Task 1).
- Produces: `MainWindow.table_proxy` (a `QSortFilterProxyModel` whose source is `self.table_model`). `self.table.model()` is the proxy. All table row reads/writes map through the proxy. Existing behavior preserved: `test_table_search_selects_row`, `test_focus_drills_into_nested_array`, `test_table_view_for_array_of_objects`.

- [ ] **Step 1: Add a sort behavior test**

Append to `tests/test_app.py`:

```python
def test_table_sort_keeps_source_mapping(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 2}, {"id": 1}, {"id": 3}]))
    win.sync_from_editor()
    # sort ascending by column 0
    win.table.sortByColumn(0, Qt.AscendingOrder)
    # search should still select the correct source row via proxy mapping
    win.search_bar.input.setText("3")
    assert win.search_bar.count_label.text() == "1/1"
    src_row = win.table_proxy.mapToSource(win.table.currentIndex()).row()
    assert win.table_model.row_object(src_row) == {"id": 3}
```

Ensure `Qt` is imported in the test file; add at top if missing:

```python
from PySide6.QtCore import Qt
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py::test_table_sort_keeps_source_mapping -q`
Expected: FAIL (`table_proxy` missing).

- [ ] **Step 3: Wire the proxy in `_build_ui`**

In `jfather/app.py`, add to the imports from `PySide6.QtCore`:

```python
from PySide6.QtCore import Qt, QSortFilterProxyModel, QTimer
```

In `_build_ui`, replace:

```python
        self.table = QTableView()
        self.table.setModel(self.table_model)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
```

with:

```python
        self.table_proxy = QSortFilterProxyModel()
        self.table_proxy.setSourceModel(self.table_model)
        self.table = QTableView()
        self.table.setModel(self.table_proxy)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
```

- [ ] **Step 4: Map proxy↔source in row handlers**

Replace `_on_table_double_clicked` with:

```python
    def _on_table_double_clicked(self, index):
        source_index = self.table_proxy.mapToSource(index)
        doc = self.manager.active
        base = list(doc.focus_path) if doc is not None else []
        self.focus_path(base + [source_index.row()])
```

In `_on_search`, the table branch builds results by source row; keep iterating source rows but it must check the source model. Replace the table branch:

```python
            if self.view_stack.currentWidget() is self.table:
                self._search_results = [
                    [row]
                    for row in range(self.table_model.rowCount())
                    if search.search(self.table_model.row_object(row), term)
                ]
```

(unchanged — results store SOURCE rows). Then in `_navigate_search`, the table branch must map the source row to a proxy index before selecting. Replace its table branch:

```python
        if self.view_stack.currentWidget() is self.table:
            source_index = self.table_model.index(target[0], 0)
            index = self.table_proxy.mapFromSource(source_index)
            self.table.setCurrentIndex(index)
            self.table.scrollTo(index)
```

- [ ] **Step 5: Update `_refresh_view` (model already set on proxy)**

`_refresh_view` calls `self.table_model.set_rows(value)` — this stays the same (proxy observes the source). No change needed there. Verify by reading the method; if it references `self.table.setModel`, leave as proxy.

- [ ] **Step 6: Run the app tests**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py -q`
Expected: PASS (new sort test + all existing table/search tests).

- [ ] **Step 7: Commit**

```bash
git add jfather/app.py tests/test_app.py
git commit -m "feat: sortable/resizable table via proxy with source row mapping"
```

---

### Task 8: Query panel — per-row remove, copy button, count label, mono tokens

**Files:**
- Modify: `jfather/query_panel.py`
- Test: `tests/test_query_panel.py`

**Interfaces:**
- Consumes: `theme.MONO_FONT_FAMILY` (Task 1).
- Produces: `QueryPanel.copy_button` (QPushButton), `QueryPanel.count_label` (QLabel), `QueryPanel.set_results_text(text, count=None)` updates count label when `count` given; each row widget has a `remove` button removing that row. Existing API (`rows/set_rows/current_rows/run_button/set_run_enabled/runRequested`) preserved.

- [ ] **Step 1: Add tests for remove + copy + count**

Append to `tests/test_query_panel.py`:

```python
def test_remove_row_reduces_count(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "a=1"), ("filter", "b=2")])
    assert len(panel.rows()) == 2
    panel._active_rows()[0].remove.click()
    assert len(panel.rows()) == 1
    assert panel.rows() == [("filter", "b=2")]


def test_copy_button_copies_results(app):
    from PySide6.QtWidgets import QApplication
    panel = QueryPanel()
    panel.set_results_text("hello results", count=3)
    panel.copy_button.click()
    assert QApplication.clipboard().text() == "hello results"
    assert "3" in panel.count_label.text()


def test_tokens_use_monospace_font(app):
    from jfather import theme
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "a=1")])
    row = panel._active_rows()[0]
    assert theme.MONO_FONT_FAMILY.split(",")[0] in row.tokens.font().family() \
        or row.tokens.font().family() != ""
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_query_panel.py -q`
Expected: FAIL (`remove` / `copy_button` / `count_label` missing).

- [ ] **Step 3: Add remove buttons to row widgets**

In `jfather/query_panel.py`, import the font tooling at top:

```python
from PySide6.QtGui import QFont
from . import query, theme
```

In `_TextRow.__init__`, after creating `self.tokens` and before the `layout.addWidget` calls, add:

```python
        mono = QFont()
        mono.setFamily(theme.MONO_FONT_FAMILY.split(",")[0].strip())
        mono.setStyleHint(QFont.Monospace)
        self.tokens.setFont(mono)
        self.remove = QPushButton("\u2212")
        self.remove.setFixedWidth(32)
```

and change the widget-add block to include the remove button last:

```python
        layout.addWidget(self.op)
        layout.addWidget(self.tokens)
        layout.addWidget(self.remove)
```

In `_StructuredRow.__init__`, before the `layout.addWidget` calls add:

```python
        self.remove = QPushButton("\u2212")
        self.remove.setFixedWidth(32)
```

and append it after `self.value`:

```python
        layout.addWidget(self.op)
        layout.addWidget(self.field)
        layout.addWidget(self.lookup)
        layout.addWidget(self.value)
        layout.addWidget(self.remove)
```

- [ ] **Step 4: Wire row removal + add copy/count UI in `QueryPanel`**

In `QueryPanel.__init__`, change the `buttons` row block and results block. Replace:

```python
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
```

with:

```python
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
        layout.addWidget(self.results)
```

Add `QLabel` to the widget imports at the top of the file:

```python
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
```

Connect remove signals when rows are created. In both `_add_text_row` and `_add_structured_row`, after appending the row, connect:

```python
        row.remove.clicked.connect(lambda _=False, r=row: self._remove_row(r))
```

Also connect in `_populate` for each created row. Simplest: centralize by connecting inside `_add_text_row`/`_add_structured_row` AND in the `_populate` loops. To avoid duplication, add a helper and call it wherever a row is constructed:

```python
    def _register_row(self, row):
        row.remove.clicked.connect(lambda _=False, r=row: self._remove_row(r))
```

In `_populate`, after `self._structured_rows.append(row)` add `self._register_row(row)`; after `self._text_rows.append(row)` add `self._register_row(row)`. In `_add_text_row` and `_add_structured_row`, after the append add `self._register_row(row)`.

Add the removal + copy methods:

```python
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
```

- [ ] **Step 5: Update `set_results_text` to accept count**

Replace:

```python
    def set_results_text(self, text):
        self.results.setPlainText(text)
```

with:

```python
    def set_results_text(self, text, count=None):
        self.results.setPlainText(text)
        if count is not None:
            self.count_label.setText(f"{count} result" + ("" if count == 1 else "s"))
```

- [ ] **Step 6: Run query panel tests**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_query_panel.py -q`
Expected: PASS (new + all existing).

- [ ] **Step 7: Commit**

```bash
git add jfather/query_panel.py tests/test_query_panel.py
git commit -m "feat: query panel per-row remove, copy button, result count, mono tokens"
```

---

### Task 9: Toolbar restructure + remove theme toggle + query status total + monospace editors

**Files:**
- Modify: `jfather/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: Tasks 1, 8.
- Produces: `MainWindow` no longer has `toggle_theme`/`_dark`. `run_query` updates the status bar with match count and calls `query_panel.set_results_text(text, count=len(results))`. Toolbar shows glyph-labelled FILE/TRANSFORM/SETTINGS groups; `shortcut_actions` dict unchanged (keys close/save/format/run/find).

- [ ] **Step 1: Add status-bar count + no-toggle tests**

Append to `tests/test_app.py`:

```python
def test_run_query_sets_status_count(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]))
    win.sync_from_editor()
    win.query_panel.set_mode("text")
    win.query_panel.set_rows([("filter", "id__gt=1")])
    win.run_query()
    assert "2" in win.status_label.text()
    assert "match" in win.status_label.text().lower()


def test_theme_toggle_removed(app):
    win = MainWindow()
    assert not hasattr(win, "toggle_theme")
```

- [ ] **Step 2: Run to verify failure**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py::test_run_query_sets_status_count tests/test_app.py::test_theme_toggle_removed -q`
Expected: FAIL (`toggle_theme` still present; status not set).

- [ ] **Step 3: Remove theme state + light branch**

In `jfather/app.py` `__init__`, delete the line `self._dark = True`. Change:

```python
        self.setStyleSheet(theme.STYLESHEET)
```
(keep — single theme). Delete the entire `toggle_theme` method:

```python
    def toggle_theme(self):
        self._dark = not self._dark
        self.setStyleSheet(theme.STYLESHEET if self._dark else theme.LIGHT_STYLESHEET)
```

- [ ] **Step 4: Rebuild the toolbar with glyph groups + far-right SETTINGS**

Replace `_build_toolbar` with:

```python
    def _build_toolbar(self):
        bar = QToolBar()
        bar.setMovable(False)
        self.addToolBar(bar)

        # FILE group
        bar.addAction("\U0001F4C4 New", self.new_document)
        bar.addAction("\U0001F4C2 Open", self.open_file)
        self._save_action = bar.addAction("\U0001F4BE Save", self.save_file)
        bar.addSeparator()

        # TRANSFORM group
        self._format_action = bar.addAction("\u2728 Format", self.apply_format)
        bar.addAction("\U0001F5DC Minify", self.apply_minify)
        bar.addAction("\u2937 Escape", self.apply_escape)
        bar.addAction("\u2936 Unescape", self.apply_unescape)

        # spacer pushes SETTINGS group to the far right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bar.addWidget(spacer)

        # SETTINGS group
        bar.addSeparator()
        self._close_action = bar.addAction("\u2715 Close", self._close_active_document)

        # Hidden shortcut actions (keep keyboard bindings + tests intact)
        self.shortcut_actions = {}
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
            action.triggered.connect(lambda _checked=False, h=handler: h())
            self.addAction(action)
            self.shortcut_actions[name] = action
```

Add `QSizePolicy` to the `PySide6.QtWidgets` imports in `app.py`:

```python
    QSizePolicy,
```

(insert alphabetically near `QSplitter`).

- [ ] **Step 5: Status-bar match count in `run_query`**

Replace the success tail of `run_query`:

```python
        self.query_panel.set_results_text(
            f"{len(results)} result(s)\n\n"
            + json.dumps(results, indent=2, ensure_ascii=False)
        )
        return results
```

with:

```python
        self.query_panel.set_results_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            count=len(results),
        )
        self.status_label.setText(f"{len(results)} match(es)")
        return results
```

- [ ] **Step 6: Make the raw editor + force monospace already in place**

`JsonEditor` already uses Menlo monospace — no change. Confirm no `toggle_theme` references remain anywhere:

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_app.py -q`
Expected: PASS.

- [ ] **Step 7: Run the FULL suite**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest -q`
Expected: PASS (all files).

- [ ] **Step 8: Commit**

```bash
git add jfather/app.py tests/test_app.py
git commit -m "feat: grouped glyph toolbar, remove theme toggle, query status count"
```

---

### Task 10: Manual smoke + README/docs touch-up

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: README reflects single dark theme (no light toggle) and new affordances.

- [ ] **Step 1: Launch the app for a manual smoke check**

Run: `uv run python main.py`
Verify visually: warm dark theme, grouped toolbar with Close at far right, sidebar `+ New` at bottom with distinct bg, editor line numbers, "Find in file…" bar (Cmd/Ctrl+F), breadcrumb pills + drill hint at root, sortable table + nested-cell tooltips, query panel per-row `−` / `＋` / `▶ Run` / `⧉ Copy` + result count, status bar match count after a query. Close the window.

- [ ] **Step 2: Update README features list**

In `README.md`, change the line:

```
- Format, Minify, Escape, Unescape (selection-aware).
```
and the theme-related expectations to reflect: single warm dark theme (no light toggle), line-number gutter, sortable/resizable table with nested-cell JSON tooltips, query result Copy button and status-bar match count. (Edit prose to match; remove any mention of a light/theme toggle if present.)

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for refined UI (single dark theme, new affordances)"
```

---

## Self-Review

**Spec coverage:**
- Typography (sans chrome / mono content) → Task 1 (constants+QSS), Task 8 (mono tokens+results), editor already mono. ✓
- Increased spacing/padding → Task 1 (QSS), Task 2/4 (margins). ✓
- Warm palette → Task 1. ✓
- Toolbar FILE/TRANSFORM/SETTINGS groups + far-right + separators → Task 9. ✓
- Sidebar distinct bg + bottom `+` → Task 2. ✓
- Editor line numbers → Task 3. Find placeholder → Task 4. ✓
- Breadcrumb pills + drill hint → Task 5. ✓
- Table sort/resize + nested tooltip → Tasks 6 & 7. ✓
- Query streamlined +/- + copy + status total → Tasks 8 & 9. ✓
- Native scrollbars preserved → enforced by Task 1 test. ✓
- Light theme + toggle removed → Tasks 1 & 9. ✓

**Placeholder scan:** No TBD/TODO; all code shown. ✓

**Type/name consistency:** `set_results_text(text, count=None)` defined in Task 8, called with `count=` in Task 9. `table_proxy` defined Task 7, used in mapping. `remove`/`copy_button`/`count_label` defined Task 8, tested same task. `line_number_area`/`line_number_area_width` defined+tested Task 3. `objectName "documentSidebar"` matches QSS `QWidget#documentSidebar` (Task 1↔2); `breadcrumbPill`/`drillHint` match QSS (Task 1↔5). ✓
```
