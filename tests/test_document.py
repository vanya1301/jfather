import pytest
from jfather.document import Document, DocumentManager


def test_document_default_name():
    assert Document().name == "untitled"


def test_document_name_from_path():
    assert Document(path="/tmp/data.json").name == "data.json"


def test_set_text_marks_dirty():
    doc = Document(text="{}")
    assert doc.dirty is False
    doc.set_text("{}")
    assert doc.dirty is False
    doc.set_text('{"a": 1}')
    assert doc.dirty is True


def test_parsed():
    assert Document(text='{"a": 1}').parsed() == {"a": 1}


def test_mark_saved_clears_dirty_and_sets_path():
    doc = Document(text="{}")
    doc.set_text('{"a": 1}')
    doc.mark_saved("/tmp/x.json")
    assert doc.dirty is False
    assert doc.path == "/tmp/x.json"
    assert doc.name == "x.json"


def test_manager_new_sets_active():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    d2 = mgr.new(name="two")
    assert mgr.documents == [d1, d2]
    assert mgr.active is d2


def test_manager_switch():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    mgr.new(name="two")
    assert mgr.switch(0) is d1
    assert mgr.active is d1


def test_manager_open(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"a": 1}')
    mgr = DocumentManager()
    doc = mgr.open(str(f))
    assert doc.text == '{"a": 1}'
    assert doc.name == "data.json"
    assert mgr.active is doc


def test_manager_close_adjusts_active():
    mgr = DocumentManager()
    mgr.new(name="one")
    d2 = mgr.new(name="two")
    mgr.new(name="three")  # active index 2
    mgr.close(2)
    assert mgr.active is d2  # index clamped to 1
    mgr.close(0)
    assert mgr.active is d2  # index shifted to 0
    mgr.close(0)
    assert mgr.active is None


def test_state_isolated_between_documents():
    mgr = DocumentManager()
    d1 = mgr.new(name="one")
    d2 = mgr.new(name="two")
    d1.query_rows.append(("filter", "id__gt=1"))
    assert d2.query_rows == []
