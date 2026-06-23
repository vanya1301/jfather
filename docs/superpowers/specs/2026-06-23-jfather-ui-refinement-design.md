# jfather UI Refinement — Design

Date: 2026-06-23
Status: Approved (pending written-spec review)

## Goal

Refine the jfather desktop UI (PySide6/Qt) from its current functional layout
into a more open, sophisticated, discoverable interface. Keep the existing
3-panel architecture (Documents | Editor | Viewer) and all current behavior;
change presentation, typography, spacing, and a handful of interaction
affordances.

## Key Decisions (locked)

1. **Icons**: Unicode/emoji glyphs only — no bundled SVG assets, no new
   dependencies. Glyphs are embedded in action/button text.
2. **Typography**: Two font families establish hierarchy.
   - **Sans-serif** for all UI chrome/labels (window title, toolbar, document
     list, breadcrumbs, search boxes, query labels, status bar).
   - **Monospace** strictly for JSON content: raw editor, query results, table
     **cell data**, and free-text query tokens.
3. **Palette**: Single warm-neutral dark theme. Clean blue interactive accent;
   warmth carried by neutrals.
4. **Light theme removed**: `LIGHT_STYLESHEET` deleted; theme toggle removed
   from the toolbar entirely (no dead UI). SETTINGS group = Close only.
5. **Table interactions**: native sort (proxy model), interactive column
   resize, native tooltip (`Qt.ToolTipRole`) for nested-data cell previews.
6. **Constraint**: native OS controls retained — no `QScrollBar` styling, no
   universal `QWidget {…}` rule (enforced by `test_theme.py`).

## Typography Plan

- Define font constants in `theme.py`:
  - `UI_FONT_FAMILY = "Inter, SF Pro Text, Segoe UI, sans-serif"` (applied via
    QSS to chrome widgets; Qt picks the first available family).
  - `MONO_FONT_FAMILY = "Menlo, SF Mono, Consolas, monospace"`.
- QSS targets sans-serif on: `QToolBar`, `QStatusBar`, `QLabel`,
  `QListWidget`, `QComboBox`, `QLineEdit`, `QPushButton`, `QHeaderView`,
  `QTreeView`.
- Monospace applied explicitly to: `JsonEditor` (already), query results
  `QPlainTextEdit`, `QTableView` (cells), and the free-text query token
  `QLineEdit` (`_TextRow.tokens`). Set via `setFont(QFont(MONO...))` on those
  widgets so QSS family rules don't override them.

## Color Palette (warm dark)

| Role | Value |
|------|-------|
| Window background | `#1c1b1a` |
| Panel / editor / view bg | `#161514` |
| Sidebar bg (distinct, warmer) | `#211f1d` |
| Border | `#33302c` |
| Text | `#e6e1da` |
| Muted text (hints, counts) | `#9a948c` |
| Accent (keys, links, focus) | `#7aa2f7` |
| Accent hover | `#8fb3ff` |
| Button bg | `#2c2925` |
| Button hover | `#3a352f` |
| Button disabled bg/text | `#242220` / `#5b554d` |
| Strings (highlighter) | `#9ece6a` |
| Numbers (highlighter) | `#e0af68` |
| Literals (highlighter) | `#bb9af7` |
| Selection | `#3a4a6b` |
| Find match highlight | `#5f5f00` (kept) |

Spacing: increase container margins/padding broadly (toolbar padding,
panel content margins from 0 → ~8–12px, list/row padding, button padding)
to reduce density.

## Component Changes

### A. Main Toolbar (`app.py::_build_toolbar`)
- `toolButtonStyle = ToolButtonTextBesideIcon` look achieved via glyph-prefixed
  text labels (since icons are glyphs).
- Three groups with separators:
  - **FILE**: `📄 New`, `📂 Open`, `💾 Save`
  - **TRANSFORM**: `✨ Format`, `🗜 Minify`, `⤷ Escape`, `⤶ Unescape`
  - **SETTINGS** (pushed far right via expanding spacer): `✕ Close`
- Save/Close/Format/Run/Find keep their existing `QKeySequence` shortcuts
  (`shortcut_actions` dict and its test must stay intact). `Run` stays bound to
  the query panel; it remains a registered shortcut action even though it is
  not a visible toolbar button group item.
- Far-right alignment via an empty expanding `QWidget` spacer inserted before
  the SETTINGS group.

### B. Document Sidebar (`sidebar.py`)
- Distinct warm background via an object name (`#documentSidebar`) targeted in
  QSS (avoids universal `QWidget` rule).
- Move the prominent `+` (New) button to the **bottom** of the sidebar; keep
  the Close button. Order top→bottom: list (stretch) → `+ New` → `Close`.
- Keep all existing signals/behavior; `test_sidebar.py` must stay green
  (list population, dirty marker `• `, active row, selection signal).

### C. Editor Pane (`editor.py`)
- Add a **line-number gutter** using the standard `QPlainTextEdit`
  line-number-area pattern:
  - New `LineNumberArea(QWidget)` painting widget.
  - `JsonEditor` overrides `resizeEvent`, connects `blockCountChanged`,
    `updateRequest`, paints numbers in monospace, muted color, right-aligned.
  - `line_number_area_width()` based on digit count.
- Find bar (`find_bar.py`): placeholder → `"Find in file…"`. Visual polish via
  QSS (rounded, padded). Sliding animation is optional polish; functional
  show/hide preserved (tests rely on visibility toggling, not animation).

### D. Viewer Pane (breadcrumb + table)
- **Breadcrumb pills** (`breadcrumb.py`): style crumb buttons as pills
  (object-name `#breadcrumbPill` QSS: rounded bg, padding, hover). Root crumb
  gets a `⌂` glyph; array indices show `[n]`. Separator stays `›`.
- **Drill-in hint**: a muted `QLabel` (`#drillHint`) appended after the crumbs
  reading `"Double-click a row or node to focus"`. Shown only when not yet
  focused (path empty) to avoid clutter; hidden once the user has drilled in.
- **Interactive table** (`app.py` table setup + `table_model.py`):
  - Wrap `JsonTableModel` in a `QSortFilterProxyModel`; the `QTableView` uses
    the proxy. `setSortingEnabled(True)` → native sort arrows.
  - Search/navigation code that maps rows must map through the proxy
    (`mapToSource`/`mapFromSource`) so `test_table_search_selects_row` and
    drill-in (`_on_table_double_clicked`) still resolve the correct source row.
  - Header: `setSectionsMovable(True)`, interactive resize, sensible default
    column width / stretch last section.
  - Nested cells: `table_model` adds `Qt.ToolTipRole` returning pretty-printed
    JSON for dict/list cells; display text becomes compact
    `{…} N keys` / `[…] N items`. (`_cell_text` split into display vs tooltip.)
    - Note: `test_table_model.py` currently asserts `_cell_text` output for
      nested values returns compact JSON; those assertions will be updated to
      the new compact-summary display, with tooltip JSON checked separately.

### E. Query Panel & Results (`query_panel.py`)
- **Per-row remove**: each `_TextRow`/`_StructuredRow` gets a `−` button that
  removes that row (progressive disclosure). The global add button becomes a
  compact `+`. Run button keeps glyph `▶ Run`.
- Mode toggle buttons (`Structured`/`Text`) keep behavior; restyled as a
  segmented control via QSS.
- Free-text token `QLineEdit` forced to monospace font.
- **Results quick copy**: a `⧉ Copy` button next to a result-count label in the
  results header row. Copies the results JSON to the clipboard.
- **Status bar total**: after a query runs, `app.py` sets the status bar to show
  total matched item count (e.g. `"12 match(es)"`). The query results pane keeps
  its own count + JSON.

## Files Touched

- `jfather/theme.py` — rewrite: warm dark palette, font constants, expanded
  QSS (object-name selectors for sidebar/pills/hint), remove `LIGHT_STYLESHEET`.
- `jfather/app.py` — toolbar groups + spacer, remove `toggle_theme`/`_dark`
  light branch, proxy model wiring + row mapping, drill-hint visibility, query
  status-bar total, monospace on results.
- `jfather/sidebar.py` — `+` button to bottom, object name.
- `jfather/editor.py` — line-number gutter.
- `jfather/find_bar.py` — placeholder text, object name.
- `jfather/breadcrumb.py` — pill styling/object names, root glyph, drill hint
  label (hint may live in `app.py` adjacent to breadcrumb — final placement
  decided in implementation; hint text is fixed).
- `jfather/query_panel.py` — per-row remove, copy button, count label, mono
  tokens, segmented toggle object names.
- `jfather/table_model.py` — `ToolTipRole`, compact nested display.

## Testing

- Keep all 18 existing test files green. Specific adjustments required:
  - `test_theme.py`: stop referencing `LIGHT_STYLESHEET` (loop over dark only);
    keep the no-`QWidget {`, no-`QScrollBar`, concrete-widget assertions.
  - `test_table_model.py`: update nested-cell display assertions to the compact
    summary; add a `ToolTipRole` assertion returning full JSON.
  - `app`/`search` tests touching table rows: ensure proxy mapping keeps them
    passing (update where they read `currentIndex().row()` if proxy reorders;
    default proxy is unsorted/identity so order is preserved unless sorted).
- New tests:
  - Editor exposes `line_number_area_width()` > 0 and widget present.
  - Sidebar `+ New` button is the last interactive widget (bottom placement).
  - Query panel: removing a row reduces row count; copy populates clipboard;
    count label updates.
  - Breadcrumb/app: drill hint text present and hidden after focus.
  - App: status bar shows match count after `run_query`.

## Out of Scope / YAGNI

- No custom popover widget (native tooltip only).
- No SVG/icon-font assets.
- No light theme or alternate themes.
- No scrollbar restyling (native preserved).
- No find-bar slide animation if it risks test fragility (functional toggle is
  sufficient; animation is optional polish).

## Risks

- **Proxy model row mapping** is the highest-risk change — search navigation,
  drill-in, and table search tests all index rows. Mitigation: thread all
  view→data index conversions through `mapToSource`/`mapFromSource`.
- **Font availability**: Inter/SF Pro may be absent; QSS family fallback list
  ensures graceful degradation to system sans-serif.
