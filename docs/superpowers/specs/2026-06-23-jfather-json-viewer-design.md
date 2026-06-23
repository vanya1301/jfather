# jfather — JSON Viewer/Editor with Collection Query — Design

Date: 2026-06-23
Status: Approved (pending written-spec review)

## Purpose

A simple, fast, modern desktop app to view and edit large JSON objects. Core
features: multi-document workspace, formatting, escaping/unescaping, tree
visualization, search, and querying with the
[`collection-query`](https://pypi.org/project/collection-query/) library
(Django-style `filter`/`exclude` syntax).

## Constraints & Assumptions

- Python 3.12, managed by `uv`. `collection-query` already a dependency.
- Target data: arrays of objects, files up to ~50MB.
- Data is loaded fully into memory; the tree renders lazily for performance.
- `collection-query` operates on the in-memory list of dicts directly.

## Stack

- **PySide6 (Qt6)** for a native, fast, modern UI.
- Modern flat theme via Qt stylesheet, with dark/light toggle.
- Single main window.

## Module Structure (small, focused units)

| Module | Responsibility | Depends on |
| --- | --- | --- |
| `main.py` | Launcher: `from jfather.app import run; run()` | `jfather.app` |
| `jfather/app.py` | Main window, toolbar/menus, splitter layout, theme, wiring | all below |
| `jfather/document.py` | `Document` (text, parsed data, path, dirty, per-doc search/query state) + `DocumentManager` (open/new/close/switch, active doc) | `jsontools` |
| `jfather/sidebar.py` | Left sidebar widget listing open documents; select/close/new; dirty markers | Qt, `document` |
| `jfather/editor.py` | Editor pane: JSON text editor + JSON syntax highlighter | Qt |
| `jfather/tree_model.py` | Lazy `QAbstractItemModel` for the tree (builds children on expand) | Qt |
| `jfather/query.py` | Wraps `ListQuery`; parses query tokens → `filter`/`exclude` kwargs; runs them | `collection_query` |
| `jfather/jsontools.py` | Pure functions: format, minify, escape, unescape, validate | stdlib `json` |
| `jfather/search.py` | Search/iterate tree nodes by key/value, return match positions | none |

GUI wiring is kept thin so logic modules are unit-testable without a display.

## Layout (single window)

- **Toolbar**: New, Open, Save, Format, Minify, Escape, Unescape, theme toggle.
- **Far left — Document sidebar**: vertical list of open JSON documents
  (name/filename), with a dirty marker (•) on unsaved docs, a per-item close
  button, and a "New" action. Clicking an item makes it the active document.
- **Center**: horizontal splitter.
  - **Left**: syntax-highlighted JSON text editor (raw edit, format, escape).
  - **Right**: interactive `QTreeView` (expand/collapse, type icons, inline edit).
  - The two panes sync: editing text reparses and rebuilds the tree (debounced);
    editing a tree value writes back into the text.
- **Right pane top**: search box — find-as-you-type over keys+values, next/prev,
  live match count, highlighting.
- **Bottom dock (collapsible)**: Query panel.
  - Chained rows of `key=value` tokens, each row toggled filter or exclude.
  - Field-name autocomplete sourced from the data's keys.
  - "Run" executes against the target array; results show in a results tree with
    a count, and can be exported/saved.
- **Status bar**: valid/invalid indicator, file size, node count, cursor position.

## Feature Behaviors

### Multi-document workspace
- Multiple JSON documents can be open at once; the sidebar lists them all.
- "New" creates an empty document; "Open" can add one or more files as new docs.
- Each document keeps its own state: text, parsed data, file path, dirty flag,
  tree expansion, search state, and query rows. Switching documents restores that
  state; it does not leak between documents.
- Closing a document with unsaved changes prompts to save/discard/cancel.
- Save / Save As act on the active document.

### Formatting
- Pretty-print with configurable indent (default 2 spaces) or minify.
- Operates on the whole document, or the current selection if there is one.

### Escaping / Unescaping
- **Escape**: convert selected text into a JSON-safe string literal.
- **Unescape**: convert a JSON string literal back to its raw content. Handles
  the common "stringified JSON embedded inside JSON" case.

### Visualization (tree)
- Lazy node creation: only build children of a node when it is expanded → handles
  ~50MB smoothly.
- Type-based icons/colors: object, array, string, number, bool, null.
- Collapsed container nodes show child counts.
- Expand-all / collapse-all actions.

### Search
- Matches both keys and values.
- Highlights matches, jump to next/previous, live count.

### Query (collection-query)
- **Target**: the array at the currently selected tree node; if no node is
  selected and the root is an array, use the root array.
- Tokens like `department__name=Engineering` and `id__gt=3` map to
  `ListQuery(target).filter(...)` / `.exclude(...)`, chaining rows in order.
- Value coercion: each token value is parsed as int, then float, then bool
  (`true`/`false`), then null, else kept as string.
- Supported lookups (from the library): `in`, `not`, `in_range`, `lt`, `lte`,
  `gt`, `gte`, `startswith`, `endswith`, `contains`, plus exact and nested
  (`a__b`) access.

## Error Handling

- **Invalid JSON**: editor underlines/marks the error line; status bar shows the
  parse error message; tree keeps its last valid state rather than crashing.
- **Query errors** (unknown field/lookup): inline message in the query panel; no
  crash; results cleared.
- **Token value coercion**: best-effort as above; never raises to the user.

## Testing

`pytest` unit tests for the pure-logic modules:

- `jsontools`: format, minify, escape, unescape, validate (valid + invalid input).
- `query`: token parsing → kwargs; running filter/exclude/chains against sample
  data; value coercion; nested fields; error cases.
- `tree_model`: lazy child building; node counts; types.
- `search`: key and value matches; ordering of results.
- `document`: `DocumentManager` open/new/close/switch; active-doc tracking; dirty
  flag transitions; per-document state isolation.

GUI assembly in `app.py` is intentionally thin and not unit-tested.

## Out of Scope (YAGNI)

- Streaming/100MB+ files, JSON Schema validation, diffing, plugins, remote/URL
  loading, drag-to-reorder sidebar, session persistence across restarts. Can be
  added later if needed.
