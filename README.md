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
- In-editor **"Find in file…"** bar; data **search** across the active tree or
  table.
- Cross-platform shortcuts: Close (Ctrl/Cmd+W), Save (Ctrl/Cmd+S),
  Format (Ctrl/Cmd+Shift+F), Run query (Ctrl/Cmd+Return), Find (Ctrl/Cmd+F).

## Test

```bash
QT_QPA_PLATFORM=offscreen uv run pytest -v
```
