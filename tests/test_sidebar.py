import pytest
from PySide6.QtWidgets import QApplication
from jfather.document import DocumentManager
from jfather.sidebar import DocumentSidebar


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_refresh_lists_documents(app):
    mgr = DocumentManager()
    mgr.new(name="one")
    mgr.new(name="two")
    bar = DocumentSidebar()
    bar.refresh(mgr)
    assert bar.list.count() == 2
    assert bar.list.item(1).text() == "two"


def test_dirty_marker(app):
    mgr = DocumentManager()
    doc = mgr.new(name="one")
    doc.dirty = True
    bar = DocumentSidebar()
    bar.refresh(mgr)
    assert bar.list.item(0).text().startswith("\u2022 ")


def test_active_row_selected(app):
    mgr = DocumentManager()
    mgr.new(name="one")
    mgr.new(name="two")
    mgr.switch(0)
    bar = DocumentSidebar()
    bar.refresh(mgr)
    assert bar.list.currentRow() == 0


def test_selection_emits_signal(app):
    mgr = DocumentManager()
    mgr.new(name="one")
    mgr.new(name="two")
    bar = DocumentSidebar()
    bar.refresh(mgr)
    seen = []
    bar.documentSelected.connect(seen.append)
    bar.list.setCurrentRow(1)
    assert seen[-1] == 1
