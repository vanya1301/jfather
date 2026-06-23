import pytest
from PySide6.QtWidgets import QApplication
from jfather.query_panel import QueryPanel


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_add_and_read_rows(app):
    panel = QueryPanel()
    panel.set_rows([("filter", "id__gt=1"), ("exclude", "name=Bob")])
    assert panel.rows() == [("filter", "id__gt=1"), ("exclude", "name=Bob")]


def test_run_emits_rows(app):
    panel = QueryPanel()
    panel.set_rows([("filter", "id__gt=1")])
    seen = []
    panel.runRequested.connect(seen.append)
    panel.run_button.click()
    assert seen == [[("filter", "id__gt=1")]]
