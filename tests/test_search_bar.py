import pytest
from PySide6.QtWidgets import QApplication
from jfather.search_bar import SearchBar


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_text_changed_emits_query(app):
    bar = SearchBar()
    seen = []
    bar.queryChanged.connect(seen.append)
    bar.input.setText("abc")
    assert seen[-1] == "abc"


def test_next_prev_signals(app):
    bar = SearchBar()
    nexts, prevs = [], []
    bar.nextRequested.connect(lambda: nexts.append(1))
    bar.prevRequested.connect(lambda: prevs.append(1))
    bar.next_button.click()
    bar.prev_button.click()
    assert nexts == [1] and prevs == [1]


def test_set_count_updates_label(app):
    bar = SearchBar()
    bar.set_count(2, 5)
    assert bar.count_label.text() == "2/5"
    bar.set_count(0, 0)
    assert bar.count_label.text() == "0/0"
