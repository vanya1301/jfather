import pytest
from PySide6.QtWidgets import QApplication
from jfather.editor import JsonEditor, JsonHighlighter


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_editor_set_and_get_text(app):
    editor = JsonEditor()
    editor.set_text('{"a": 1}')
    assert editor.text() == '{"a": 1}'


def test_editor_has_highlighter(app):
    editor = JsonEditor()
    assert isinstance(editor.highlighter, JsonHighlighter)


def test_set_text_is_idempotent_noop_when_same(app):
    editor = JsonEditor()
    editor.set_text("{}")
    editor.set_text("{}")
    assert editor.text() == "{}"


def test_find_matches_counts(app):
    editor = JsonEditor()
    editor.set_text("aXbXcX")
    assert editor.find_matches("X") == 3
    assert len(editor.extraSelections()) == 3


def test_find_matches_empty_term(app):
    editor = JsonEditor()
    editor.set_text("aXb")
    assert editor.find_matches("") == 0
    assert editor.extraSelections() == []


def test_find_next_wraps(app):
    editor = JsonEditor()
    editor.set_text("X X X")
    editor.find_matches("X")
    assert editor.find_next() == 1
    assert editor.find_next() == 2
    assert editor.find_next() == 3
    assert editor.find_next() == 1  # wraps


def test_clear_find(app):
    editor = JsonEditor()
    editor.set_text("aXb")
    editor.find_matches("X")
    editor.clear_find()
    assert editor.extraSelections() == []
    assert editor.find_next() == 0


def test_line_number_area_width_positive(app):
    from jfather.editor import JsonEditor
    ed = JsonEditor()
    ed.set_text("{\n  \"a\": 1\n}")
    assert ed.line_number_area_width() > 0


def test_line_number_area_widget_exists(app):
    from jfather.editor import JsonEditor
    ed = JsonEditor()
    assert ed.line_number_area is not None
