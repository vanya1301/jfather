import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from jfather.find_bar import FindBar


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_text_emits_query(app):
    bar = FindBar()
    seen = []
    bar.queryChanged.connect(seen.append)
    bar.input.setText("abc")
    assert seen[-1] == "abc"


def test_buttons_emit_signals(app):
    bar = FindBar()
    nexts, prevs, closed = [], [], []
    bar.nextRequested.connect(lambda: nexts.append(1))
    bar.prevRequested.connect(lambda: prevs.append(1))
    bar.closed.connect(lambda: closed.append(1))
    bar.next_button.click()
    bar.prev_button.click()
    bar.close_button.click()
    assert nexts == [1] and prevs == [1] and closed == [1]


def test_escape_emits_closed(app):
    bar = FindBar()
    closed = []
    bar.closed.connect(lambda: closed.append(1))
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
    bar.input.keyPressEvent(event)
    assert closed == [1]


def test_enter_and_shift_enter(app):
    bar = FindBar()
    nexts, prevs = [], []
    bar.nextRequested.connect(lambda: nexts.append(1))
    bar.prevRequested.connect(lambda: prevs.append(1))
    bar.input.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier))
    bar.input.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.ShiftModifier))
    assert nexts == [1] and prevs == [1]


def test_set_count(app):
    bar = FindBar()
    bar.set_count(2, 5)
    assert bar.count_label.text() == "2/5"
