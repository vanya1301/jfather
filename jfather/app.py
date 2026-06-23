"""Main application window wiring all components."""

import json
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

from . import jsontools, query, search, theme
from .document import DocumentManager
from .editor import JsonEditor
from .query_panel import QueryPanel
from .search_bar import SearchBar
from .sidebar import DocumentSidebar
from .tree_model import JsonTreeModel, index_for_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("jfather")
        self.resize(1200, 800)
        self._dark = True

        self.manager = DocumentManager()
        self.tree_model = JsonTreeModel({})
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

        self.tree = QTreeView()
        self.tree.setModel(self.tree_model)

        self.search_bar = SearchBar()
        self.search_bar.queryChanged.connect(self._on_search)
        self.search_bar.nextRequested.connect(lambda: self._navigate_search(1))
        self.search_bar.prevRequested.connect(lambda: self._navigate_search(-1))

        tree_pane = QWidget()
        tree_layout = QVBoxLayout(tree_pane)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.addWidget(self.search_bar)
        tree_layout.addWidget(self.tree)

        center_split = QSplitter(Qt.Horizontal)
        center_split.addWidget(self.editor)
        center_split.addWidget(tree_pane)
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
        self.refresh_tree()
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
        self.refresh_tree()

    def refresh_tree(self):
        ok, message, line, col = jsontools.validate(self.editor.text())
        if ok:
            self.tree_model.set_json(jsontools.parse(self.editor.text()))
            self.status_label.setText("Valid JSON")
        else:
            self.status_label.setText(
                f"Invalid JSON: {message} (line {line}, col {col})"
            )

    def current_text(self):
        return self.editor.text()

    # ---- Search ----------------------------------------------------------
    def _on_search(self, term):
        doc = self.manager.active
        if doc is not None:
            doc.search_term = term
        self._search_results = []
        self._search_pos = -1
        if term:
            try:
                data = jsontools.parse(self.editor.text())
            except ValueError:
                data = None
            if data is not None:
                self._search_results = search.search(data, term)
        if self._search_results:
            self._navigate_search(1)
        else:
            self.search_bar.set_count(0, len(self._search_results))

    def _navigate_search(self, step):
        total = len(self._search_results)
        if total == 0:
            self.search_bar.set_count(0, 0)
            return
        self._search_pos = (self._search_pos + step) % total
        path = self._search_results[self._search_pos]
        index = index_for_path(self.tree_model, path)
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

    def toggle_theme(self):
        self._dark = not self._dark
        self.setStyleSheet(theme.STYLESHEET if self._dark else theme.LIGHT_STYLESHEET)

    # ---- Query -----------------------------------------------------------
    def query_target(self):
        selection = self.tree.selectionModel()
        indexes = selection.selectedIndexes() if selection else []
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
        self.query_panel.set_results_text(
            f"{len(results)} result(s)\n\n"
            + json.dumps(results, indent=2, ensure_ascii=False)
        )
        return results


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
