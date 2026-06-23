import json
import pytest
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
    results = win.run_query([("filter", "id__gt=1")])
    assert results == [{"id": 2}, {"id": 3}]


def test_query_target_falls_back_to_root(app):
    win = MainWindow()
    win.editor.set_text(json.dumps([{"id": 1}]))
    win.sync_from_editor()
    assert win.query_target() == [{"id": 1}]


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
