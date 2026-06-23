"""Main application window wiring all components."""

import json
import sys

from PySide6.QtCore import Qt, QSortFilterProxyModel, QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
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
from .document import DocumentManager
from .editor import JsonEditor
from .find_bar import FindBar
from .query_panel import QueryPanel
from .search_bar import SearchBar
from .sidebar import DocumentSidebar
from .table_model import JsonTableModel, is_tabular
from .tree_model import JsonTreeModel, index_for_path, path_for_index


_MISSING = object()


def _scalar_text(value):
    """Render a scalar as the token text the query parser coerces back."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _flatten_keys(obj, prefix="", depth=0, max_depth=5):
    """Yield `field` and nested `parent__child` paths for a dict's keys.

    Mirrors collection-query's `__` traversal: only descends into nested dicts
    (not lists), so suggested paths are queryable. `max_depth` caps only the
    *suggestions*; deeper paths typed by hand are still resolved and queried.
    """
    paths = []
    if not isinstance(obj, dict):
        return paths
    for key, value in obj.items():
        path = f"{prefix}__{key}" if prefix else str(key)
        paths.append(path)
        if isinstance(value, dict) and depth < max_depth:
            paths.extend(_flatten_keys(value, path, depth + 1, max_depth))
    return paths


def _resolve_path(item, path):
    """Walk a `__`-split field path through nested dicts; `_MISSING` if absent."""
    current = item
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return _MISSING
    return current


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("jfather")
        self.resize(1200, 800)

        self.manager = DocumentManager()
        self.tree_model = JsonTreeModel({})
        self.table_model = JsonTableModel([])
        self._search_results = []
        self._search_pos = -1

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

        self.tree = QTreeView()
        self.tree.setModel(self.tree_model)
        self.tree.doubleClicked.connect(self._on_tree_double_clicked)

        self.table_proxy = QSortFilterProxyModel()
        self.table_proxy.setSourceModel(self.table_model)
        self.table = QTableView()
        self.table.setModel(self.table_proxy)
        self.table.setSortingEnabled(True)
        # Start unsorted (identity proxy mapping); user can sort interactively.
        self.table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.table_proxy.sort(-1)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        # Render cell DATA monospace while keeping column HEADERS sans-serif.
        # A widget-level stylesheet is required here because the app-wide
        # stylesheet sets a font-family on QTableView, which overrides setFont().
        mono = QFont()
        mono.setFamily(theme.MONO_FONT_FAMILY.split(",")[0].strip())
        mono.setStyleHint(QFont.Monospace)
        self.table.setFont(mono)
        self.table.setStyleSheet(
            f"QTableView {{ font-family: {theme.MONO_FONT_FAMILY}; }}"
            f"QHeaderView::section {{ font-family: {theme.UI_FONT_FAMILY}; }}"
        )

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

        center_split = QSplitter(Qt.Horizontal)
        center_split.addWidget(editor_pane)
        center_split.addWidget(tree_pane)
        center_split.setSizes([600, 600])

        self.query_panel = QueryPanel(
            get_field_names=self._field_names,
            get_field_values=self._field_values,
        )
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

    # ---- Document lifecycle ---------------------------------------------
    def new_document(self):
        self._store_active_state()
        self.manager.new()
        self._load_active_into_views()
        self._refresh_sidebar()

    def open_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not paths:
            return
        self._store_active_state()
        for path in paths:
            self.manager.open(path)
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
        self._refresh_view()
        self.search_bar.input.setText(doc.search_term)

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
        self._refresh_view()

    def _field_names(self):
        """Field names for the focused data, including nested `a__b` paths."""
        value = self.focused_value()
        if isinstance(value, list):
            items = [item for item in value if isinstance(item, dict)]
        elif isinstance(value, dict):
            items = [value]
        else:
            items = []
        names = []
        seen = set()
        for item in items:
            for path in _flatten_keys(item):
                if path not in seen:
                    seen.add(path)
                    names.append(path)
        return names

    def _field_values(self, field, limit=200):
        """Distinct scalar values for `field` (incl. nested paths) in the array."""
        value = self.focused_value()
        if not field or not isinstance(value, list):
            return []
        path = field.split("__")
        out = []
        seen = set()
        for item in value:
            cell = _resolve_path(item, path)
            if cell is _MISSING or isinstance(cell, (dict, list)):
                continue
            text = _scalar_text(cell)
            if text not in seen:
                seen.add(text)
                out.append(text)
            if len(out) >= limit:
                break
        return out

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
        source_index = self.table_proxy.mapToSource(index)
        doc = self.manager.active
        base = list(doc.focus_path) if doc is not None else []
        self.focus_path(base + [source_index.row()])

    def current_text(self):
        return self.editor.text()

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

    # ---- Search ----------------------------------------------------------
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
                    [row]
                    for row in range(self.table_model.rowCount())
                    if search.search(self.table_model.row_object(row), term)
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
            source_index = self.table_model.index(target[0], 0)
            index = self.table_proxy.mapFromSource(source_index)
            self.table.setCurrentIndex(index)
            self.table.scrollTo(index)
        else:
            index = index_for_path(self.tree_model, target)
            if index.isValid():
                self.tree.setCurrentIndex(index)
                self.tree.scrollTo(index)
        self.search_bar.set_count(self._search_pos + 1, total)

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

    # ---- Query -----------------------------------------------------------
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
            json.dumps(results, indent=2, ensure_ascii=False),
            count=len(results),
        )
        self.status_label.setText(f"{len(results)} match(es)")
        return results


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
