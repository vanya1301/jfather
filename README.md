# jfather

A fast, modern desktop app to view and edit large JSON, with formatting,
escaping, tree visualization, search, and collection-query querying.

## Run

```bash
uv sync
uv run python main.py
```

## Features

- Single warm **dark theme** with native scrollbars (no light/theme toggle).
- Grouped glyph **toolbar** (FILE / TRANSFORM / SETTINGS, with Close at the far
  right).
- Multiple documents via the left sidebar (with a distinct background and a
  bottom **+ New** button; New / Open / Close, dirty markers).
- Dual-pane: syntax-highlighted text editor with a **line-number gutter** +
  data viewer.
- Viewer shows a **table** for arrays of objects and a **tree** otherwise. The
  table is **sortable** and **resizable**, with monospace cells and JSON
  tooltips on nested cells.
- **Focus / drill-in**: double-click a node or table row to re-root the viewer
  and query scope; **breadcrumb pills** navigate back, with a drill-in hint at
  the root.
- Format, Minify, Escape, Unescape (selection-aware).
- **Query builder** with Structured (field / lookup / value dropdowns) and Text
  (tokens with autocomplete) modes; runs against the focused array (Run is
  disabled with a hint until the focused value is an array). Lists: `a,b,c`.
  Ranges: `lo..hi`.
  - Requires `collection-query>=0.2.0`. Supported lookups include `contains`,
    `startswith`, `endswith`, `in`, `in_range`, `lt`/`lte`/`gt`/`gte`, `not`,
    `exists`, `isnull`, `regex`, and case-insensitive variants (`icontains`,
    `istartswith`, `iendswith`, `iexact`, `iregex`).
  - Unknown lookups report a clear error in the results pane instead of
    silently returning nothing.
  - Per-row remove (**−**) / add (**＋**) controls, a **Copy** button for the
    results, and a result **count**; the status bar shows the match count after
    a query runs.
  - The structured **value** field suggests distinct values seen in the focused
    array for the chosen field (still accepts free text for lists/ranges).
  - Syntax-highlighted query **results**.

### Nested queries

Queries always run against the **focused array**, and you can reach into nested
data two ways:

- **Nested field paths** with `__` (double underscore). Segments are walked as
  dict keys; the last segment is a lookup only if it is a known lookup name.
  The field box is editable and also **suggests nested paths** (e.g.
  `address__city`, `address__geo__lat`):

  ```text
  address__city=Paris
  address__city__icontains=par
  address__geo__lat__gte=48
  ```

- **Drill-in scoping**: double-click a node or table row to re-root the viewer
  (and the query scope) onto a nested array, then query its items. Breadcrumb
  pills navigate back. For `{"users": [ … ]}`, drill into `users` to query the
  user objects.

Combining conditions: multiple **Filter** rows are AND-ed; **Exclude** rows
remove matches; there is no OR/grouped boolean logic — use `in` (e.g.
`status__in=active,pending`) or run separate queries for OR-like needs.
- In-editor **"Find in file…"** bar; data **search** across the active tree or
  table.
- Cross-platform shortcuts: Close (Ctrl/Cmd+W), Save (Ctrl/Cmd+S),
  Format (Ctrl/Cmd+Shift+F), Run query (Ctrl/Cmd+Return), Find (Ctrl/Cmd+F).

## Test

```bash
QT_QPA_PLATFORM=offscreen uv run pytest -v
```
