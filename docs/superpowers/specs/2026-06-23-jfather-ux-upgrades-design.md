# jfather — UI/UX Upgrades — Design

Date: 2026-06-23
Status: Approved (pending written-spec review)

## Purpose

Improve usability of the existing jfather JSON viewer/editor:

1. Keyboard shortcuts for common actions.
2. A table view for tabular data (arrays of objects), with tree fallback.
3. A redesigned, discoverable query builder (structured + smart-text modes).
4. An in-editor find bar (Cmd+F).
5. Native-looking (macOS) scrollbars.

This builds on the current app: pure-logic modules (`jsontools`, `query`,
`search`, `document`) plus Qt modules (`tree_model`, `editor`, `sidebar`,
`query_panel`, `search_bar`, `app`, `theme`).

## 1. Keyboard Shortcuts

Implemented as `QAction`s on the main window with `QKeySequence` shortcuts.
The toolbar actions and shortcuts share the same handler methods.

| Shortcut | Action |
| --- | --- |
| `Cmd+W` | Close the active document (uses existing unsaved-changes prompt) |
| `Cmd+S` | Save the active document |
| `Cmd+Shift+F` | Format JSON (whole document) |
| `Cmd+Return` (Enter) | Run the current query |
| `Cmd+F` | Toggle the editor find bar and focus the editor's find input |

Use `QKeySequence` portable forms (e.g. `QKeySequence.Save`,
`"Ctrl+W"` which maps to Cmd on macOS, `"Ctrl+Shift+F"`, `"Ctrl+Return"`,
`QKeySequence.Find`).

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
- Right pane becomes a `QStackedWidget` holding the existing `QTreeView` and a
  new `QTableView`, plus the existing `SearchBar` on top (shared).
- A `_refresh_view()` chooses the widget per the active query target's shape:
  - If `is_tabular(parsed_target)` → populate `JsonTableModel`, show table.
  - Else → populate `JsonTreeModel`, show tree.
  - "Target" follows the existing rule: selected array node, else root if it's a
    list, else the whole parsed doc for the tree.
- `_refresh_view()` runs whenever the parsed document changes (debounced sync)
  and on document switch.

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

## 4. Editor Find Bar (Cmd+F)

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
- App shows/hides the `FindBar` over the editor (Cmd+F toggles). The bar drives
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
- `app`: the four shortcuts + Cmd+F are registered with the expected key
  sequences; right pane switches table↔tree by data shape; table search selects
  a matching row; run-query still returns results; format shortcut formats.

## Out of Scope (YAGNI)

- Find-and-replace in the editor, column sorting/resizing persistence, nested
  drill-down from table cells, query history, saved queries, OR/`Q` logic
  (pending upstream collection-query support).

## Affected Files

- New: `jfather/table_model.py`, `jfather/find_bar.py`.
- Rewrite: `jfather/query_panel.py`, `jfather/theme.py`.
- Modify: `jfather/app.py` (shortcuts, stacked right pane + view routing,
  find-bar wiring, table search), `jfather/editor.py` (find support).
- Tests: new `test_table_model.py`, `test_find_bar.py`; updated
  `test_query_panel.py`, `test_app.py`, `test_editor.py`.
