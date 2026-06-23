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
