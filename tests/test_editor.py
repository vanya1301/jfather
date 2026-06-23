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
