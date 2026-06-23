import json
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from jfather.app import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_starts_with_one_document(app):
    win = MainWindow()
    assert len(win.manager.documents) == 1


def test_new_document_adds_and_activates(app):
    win = MainWindow()
    win.new_document()
    assert len(win.manager.documents) == 2
    assert win.manager.active_index == 1


def test_apply_format(app):
    win = MainWindow()
    win.editor.set_text('{"a":1}')
    win.apply_format()
    assert win.current_text() == '{\n  "a": 1\n}'


def test_apply_minify(app):
    win = MainWindow()
    win.editor.set_text('{\n  "a": 1\n}')
    win.apply_minify()
    assert win.current_text() == '{"a":1}'


def test_run_query_on_root_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]))
    win.sync_from_editor()
    win.query_panel.set_mode("text")
    win.query_panel.set_rows([("filter", "id__gt=1")])
    results = win.run_query()
    assert results == [{"id": 2}, {"id": 3}]


def test_focused_value_defaults_to_root(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}]))
    win.sync_from_editor()
    assert win.focused_value() == [{"id": 1}]


def test_search_finds_and_selects_match(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"user": {"name": "Alice"}}))
    win.sync_from_editor()
    win.search_bar.input.setText("Alice")
    assert win.search_bar.count_label.text() == "1/1"
    assert win.tree.currentIndex().isValid()


def test_search_no_match_shows_zero(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"a": 1}))
    win.sync_from_editor()
    win.search_bar.input.setText("zzz")
    assert win.search_bar.count_label.text() == "0/0"


def test_shortcuts_registered(app):
    from PySide6.QtGui import QKeySequence
    win = MainWindow()
    seqs = {name: act.shortcut() for name, act in win.shortcut_actions.items()}
    assert seqs["save"] == QKeySequence(QKeySequence.Save)
    assert seqs["close"] == QKeySequence(QKeySequence.Close)
    assert seqs["find"] == QKeySequence(QKeySequence.Find)
    assert seqs["format"] == QKeySequence("Ctrl+Shift+F")
    assert seqs["run"] == QKeySequence("Ctrl+Return")


def test_toggle_find_shows_and_hides(app):
    win = MainWindow()
    win.show()
    assert win.find_bar.isVisible() is False
    win.toggle_find()
    assert win.find_bar.isVisible() is True
    win._close_find()
    assert win.find_bar.isVisible() is False


def test_find_counts_and_navigates(app):
    win = MainWindow()
    win.show()
    win.editor.set_text("X X X")
    win.toggle_find()
    win._find("X")
    assert win.find_bar.count_label.text().endswith("/3")


def test_table_view_for_array_of_objects(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}, {"id": 2}]))
    win.sync_from_editor()
    assert win.view_stack.currentWidget() is win.table
    assert win.table_model.rowCount() == 2


def test_tree_view_for_object(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"a": 1}))
    win.sync_from_editor()
    assert win.view_stack.currentWidget() is win.tree


def test_focus_drills_into_nested_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"users": [{"id": 1}, {"id": 2}]}))
    win.sync_from_editor()
    win.focus_path(["users"])
    assert win.focused_value() == [{"id": 1}, {"id": 2}]
    assert win.view_stack.currentWidget() is win.table


def test_query_runs_against_focused_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"users": [{"id": 1}, {"id": 2}, {"id": 3}]}))
    win.sync_from_editor()
    win.focus_path(["users"])
    win.query_panel.set_mode("text")
    win.query_panel.set_rows([("filter", "id__gt=1")])
    results = win.run_query()
    assert results == [{"id": 2}, {"id": 3}]


def test_query_disabled_when_focus_not_array(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"a": {"b": 1}}))
    win.sync_from_editor()
    win.focus_path(["a"])
    assert win.query_panel.run_button.isEnabled() is False


def test_stale_focus_path_heals(app):
    win = MainWindow()
    win.editor.set_text(json.dumps({"users": [{"id": 1}]}))
    win.sync_from_editor()
    win.focus_path(["users", 5])
    assert win.focused_value() == [{"id": 1}]
    assert win.manager.active.focus_path == ["users"]


def test_table_search_selects_row(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"name": "Alice"}, {"name": "Bob"}]))
    win.sync_from_editor()
    win.search_bar.input.setText("Bob")
    assert win.table.currentIndex().row() == 1
    assert win.search_bar.count_label.text() == "1/1"


def test_table_sort_keeps_source_mapping(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 2}, {"id": 1}, {"id": 3}]))
    win.sync_from_editor()
    win.table.sortByColumn(0, Qt.AscendingOrder)
    win.search_bar.input.setText("1")
    assert win.search_bar.count_label.text() == "1/1"
    current = win.table.currentIndex()
    src_row = win.table_proxy.mapToSource(current).row()
    assert win.table_model.row_object(src_row) == {"id": 1}
    assert current.row() == 0          # proxy row (sorted position)
    assert src_row == 1                # source row (insertion position) — differs, proving mapping


def test_table_uses_monospace_font(app):
    from jfather import theme
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}]))
    win.sync_from_editor()
    fam = theme.MONO_FONT_FAMILY.split(",")[0].strip()
    assert win.table.font().family() == fam


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
