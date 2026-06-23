# jfather — UI/UX Upgrades — Design

Date: 2026-06-23
Status: Approved (pending written-spec review)

## Purpose

Improve usability of the existing jfather JSON viewer/editor:

1. Cross-platform keyboard shortcuts for common actions.
2. A table view for tabular data (arrays of objects), with tree fallback.
3. A redesigned, discoverable query builder (structured + smart-text modes).
4. An in-editor find bar (Find shortcut).
5. Native-looking scrollbars.
6. Focus / drill-in: select a nested node to re-root the viewer and query scope.

This builds on the current app: pure-logic modules (`jsontools`, `query`,
`search`, `document`) plus Qt modules (`tree_model`, `editor`, `sidebar`,
`query_panel`, `search_bar`, `app`, `theme`).

## 1. Keyboard Shortcuts (cross-platform)

Implemented as `QAction`s on the main window with `QKeySequence` shortcuts.
The toolbar actions and shortcuts share the same handler methods.

Shortcuts must work on macOS, Windows, and Linux. Use Qt's portable forms so
the platform modifier is applied automatically — `QKeySequence.StandardKey`
where one exists, and `"Ctrl+..."` strings otherwise (Qt maps `Ctrl` to the
Command key on macOS and to the Control key elsewhere).

| Action | Binding | mac / Win+Linux |
| --- | --- | --- |
| Close active document | `QKeySequence.Close` | Cmd+W / Ctrl+W |
| Save active document | `QKeySequence.Save` | Cmd+S / Ctrl+S |
| Format JSON (whole document) | `"Ctrl+Shift+F"` | Cmd+Shift+F / Ctrl+Shift+F |
| Run query | `"Ctrl+Return"` | Cmd+Return / Ctrl+Return |
| Toggle editor find bar | `QKeySequence.Find` | Cmd+F / Ctrl+F |

Display labels in tooltips should use `QKeySequence.toString(NativeText)` so each
platform shows its own modifier names.

## 2. Right Pane: Table with Tree Fallback

### New module `jfather/table_model.py`
- `is_tabular(data) -> bool`: True when `data` is a non-empty `list` whose items
  are mostly dicts (>= half are dicts). Used to decide table vs tree.
- `JsonTableModel(QAbstractTableModel)`:
  - `set_rows(rows: list[dict])` — resets the model.
  - Columns = union of dict keys in first-seen order across rows.
  - `data()` for `DisplayRole`: scalar values → `str(value)` (with `null`,
    `true`/`false` for None/bool); dict/list values → compact JSON
    (`json.dumps(value, ensure_ascii=False)`); missing key → empty string.
  - `headerData()` → column key names (horizontal) and row numbers (vertical).
  - `row_object(row) -> dict` accessor for search/selection use.

### App integration (`app.py`)
- Right pane is laid out top-to-bottom: **breadcrumb bar** (section 7), the
  shared **`SearchBar`**, then a `QStackedWidget` holding the existing
  `QTreeView` and a new `QTableView`.
- A `_refresh_view()` chooses the widget per the **focused node**'s shape (see
  section 7):
  - If `is_tabular(focused_value)` → populate `JsonTableModel`, show table.
  - Else → populate `JsonTreeModel`, show tree.
  - The focused value defaults to the whole parsed document; drilling in
    re-roots it (section 7).
- `_refresh_view()` runs whenever the parsed document changes (debounced sync),
  on document switch, and on focus change.

## 3. Query Builder Redesign

Rewrite `jfather/query_panel.py`. The panel emits normalized rows and the app
runs them; the panel owns mode state and widgets.

### Public interface
- `QueryPanel(get_field_names: callable=None, lookups: list=None)`:
  - `lookups` defaults to `query.available_lookups()`.
  - `get_field_names()` supplies current data keys for autocomplete (the app
    passes a callable returning keys of the current target).
- Signal `runRequested()` (no args).
- `current_rows() -> list[tuple[str, dict]]`: returns `(op, kwargs)` per row,
  built from whichever mode is active. Raises `ValueError` on malformed text
  tokens (message shown by the app).
- `set_rows(rows)` / `rows()` for persistence as `(op, token_text)` pairs so
  per-document state stays a simple serializable form (text mode is the
  canonical storage; switching to structured parses these).
- `set_results_text(str)`.

### Modes (segmented toggle: Structured | Text)
- **Structured**: rows of `[op ▾][field combo (editable + completer)]
  [lookup ▾ from lookups][value line edit][✕ remove]`, plus **+ Condition**.
  `current_rows()` builds `{f"{field}__{lookup}" if lookup!="exact" else field:
  coerced_value}` using `query.coerce_value`.
- **Text**: rows of `[op ▾][token QLineEdit with QCompleter]`. The completer
  suggests field names; once the user types `__` in a token it suggests
  lookups. `current_rows()` uses `query.parse_tokens(text)`.
- Switching modes converts current content: structured→text renders tokens;
  text→structured parses tokens into field/lookup/value (best-effort; tokens
  that don't parse into a single field/lookup stay as a raw text row).

### Discoverability
- Structured mode's lookup dropdown always shows the full lookup list.
- A small "?" help affordance lists lookups with one-line descriptions
  (static text from the spec's known lookups).

## 4. Editor Find Bar (Find shortcut)

### New module `jfather/find_bar.py`
- `FindBar(QWidget)`: `input` QLineEdit, `count_label`, prev/next buttons,
  close button.
- Signals: `queryChanged(str)`, `nextRequested()`, `prevRequested()`,
  `closed()`.
- Key handling: Enter → `nextRequested`, Shift+Enter → `prevRequested`,
  Esc → `closed`.

### Editor integration (`editor.py` / `app.py`)
- `JsonEditor` gains find support that does not pollute pure logic:
  - `find_matches(term) -> int`: highlights all occurrences using
    `QTextEdit.ExtraSelection`, returns match count, resets the active index.
  - `find_next(forward=True)`: moves the cursor/selection to the next/previous
    match (wrap-around) and returns the 1-based active index (0 if none).
  - `clear_find()`: removes highlights.
- App shows/hides the `FindBar` over the editor (the Find shortcut toggles). The bar drives
  `find_matches`/`find_next`; count label shows `active/total`. Esc hides the
  bar and calls `clear_find()`, refocusing the editor.

## 5. Native-Looking Scrollbars

Current `theme.py` styles `QWidget { ... }` globally, which forces Qt to draw
non-native scrollbars. Rework both stylesheets to:
- Scope rules to concrete classes: `QMainWindow`, `QPlainTextEdit`,
  `QTreeView`, `QTableView`, `QListWidget`, `QLineEdit`, `QComboBox`,
  `QPushButton`, `QToolBar`, `QHeaderView::section`, `QStatusBar`, `QLabel`.
- Do **not** style `QScrollBar`, `QAbstractScrollArea` corners, or apply a
  universal `QWidget` background, so macOS native overlay scrollbars render.
- Keep the dark/light palettes visually equivalent to today.

## 6. Search With Table View

The shared `SearchBar` works against the active right-pane view:
- **Tree mode** (unchanged): `search.search` → paths → `index_for_path` →
  select/scroll tree node; next/prev; count.
- **Table mode**: scan rows via `JsonTableModel.row_object`; a row matches if
  the search term appears in any of its values (reusing `search.search` on the
  row object, or a row-level substring match). Collect matching row indices;
  next/prev selects and scrolls to each; count shows `active/total`.
- The app routes search to the tree or table path based on which stacked widget
  is visible.

## 7. Focus / Drill-In (re-root viewer + query scope)

The user can drill into a nested container so it becomes both the displayed
object and the query scope.

### State
- `Document` gains `focus_path: list` (keys/indices from the document root to the
  focused node); empty list means "whole document". Per-document, restored on
  switch.
- The app resolves `focus_path` against the parsed document to get the focused
  value. If the path no longer resolves (e.g. after an edit), it falls back to
  the nearest valid ancestor, down to the root.

### Trigger & navigation
- **Double-click** a container node (object or array) in the tree or a table row
  re-roots the viewer to that node (appends to `focus_path`). Double-clicking a
  scalar leaf does nothing.
- A **breadcrumb bar** (`jfather/breadcrumb.py`, a `Breadcrumb(QWidget)` with a
  `pathChanged(list)` signal and `set_path(list)`) sits above the search bar and
  shows `root > users > 0 > address`. Clicking a crumb sets `focus_path` to that
  prefix. The leading `root` crumb resets to the whole document.

### Effect
- `_refresh_view()` renders the focused value (table if tabular, else tree).
- **Query scope = the focused value.** The existing per-selection target rule is
  replaced by focus:
  - If the focused value is a `list` → it is the query target; Run is enabled.
  - If it is not a list → the query Run action is disabled and the results pane
    shows "Focus an array to query." Drilling into / breadcrumbing to an array
    re-enables it.
- Table search and tree search operate within the focused value.

### Breadcrumb labels
- Keys shown as-is; list indices shown as `[i]`. Root shown as `root`.

## Error Handling

- Malformed query text tokens or unknown lookups: caught in the app's run-query
  handler (existing `ValueError` path, now including `query.parse_tokens` and
  `FieldLookupError`→`ValueError`), shown in the results pane; no crash.
- Non-tabular or invalid data: table simply isn't used (tree fallback); invalid
  JSON keeps last valid view, status bar shows the parse error (existing
  behavior).

## Testing

- `table_model`: `is_tabular` (list of dicts yes; scalars/object/empty no);
  column union ordering; scalar vs nested-JSON cell rendering; `row_object`;
  reset via `set_rows`.
- `query_panel`: structured rows → `(op, kwargs)`; text rows → `(op, kwargs)`
  via `parse_tokens`; `exact` lookup omits the `__suffix`; lookups list
  populated from injected list; mode toggle round-trips rows; malformed text
  raises `ValueError`.
- `find_bar`: `queryChanged` on text; next/prev/closed signals; `set_count`
  label format.
- `editor`: `find_matches` returns correct count and adds highlights;
  `find_next` advances index with wrap; `clear_find` removes highlights.
- `app`: the five shortcuts are registered with the expected portable key
  sequences; right pane switches table↔tree by data shape; table search selects
  a matching row; run-query still returns results; format shortcut formats.
- focus: `focus_path` resolution (valid path, stale path → nearest ancestor,
  root); double-click on a container appends to the path; breadcrumb click sets
  a prefix; query disabled when focused value is not a list and enabled when it
  is; `Breadcrumb.set_path` renders crumbs and `pathChanged` emits the prefix.

## Out of Scope (YAGNI)

- Find-and-replace in the editor, column sorting/resizing persistence, query
  history, saved queries, OR/`Q` logic (pending upstream collection-query
  support).

## Affected Files

- New: `jfather/table_model.py`, `jfather/find_bar.py`, `jfather/breadcrumb.py`.
- Rewrite: `jfather/query_panel.py`, `jfather/theme.py`.
- Modify: `jfather/app.py` (shortcuts, stacked right pane + view routing,
  find-bar wiring, table search, focus/breadcrumb), `jfather/editor.py` (find
  support), `jfather/document.py` (`focus_path`).
- Tests: new `test_table_model.py`, `test_find_bar.py`, `test_breadcrumb.py`;
  updated `test_query_panel.py`, `test_app.py`, `test_editor.py`,
  `test_document.py`.
