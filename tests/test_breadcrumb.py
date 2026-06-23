import pytest
from PySide6.QtWidgets import QApplication
from jfather.breadcrumb import Breadcrumb


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_root_only(app):
    bar = Breadcrumb()
    bar.set_path([])
    assert [b.text() for b in bar.buttons] == ["root"]


def test_renders_crumbs_with_index_labels(app):
    bar = Breadcrumb()
    bar.set_path(["users", 0, "name"])
    assert [b.text() for b in bar.buttons] == ["root", "users", "[0]", "name"]


def test_click_emits_prefix(app):
    bar = Breadcrumb()
    bar.set_path(["users", 0, "name"])
    seen = []
    bar.pathChanged.connect(seen.append)
    bar.buttons[2].click()  # the "[0]" crumb
    assert seen[-1] == ["users", 0]


def test_click_root_emits_empty(app):
    bar = Breadcrumb()
    bar.set_path(["users"])
    seen = []
    bar.pathChanged.connect(seen.append)
    bar.buttons[0].click()
    assert seen[-1] == []
