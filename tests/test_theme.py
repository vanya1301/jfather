from jfather import theme


def test_no_universal_widget_rule():
    for sheet in (theme.STYLESHEET, theme.LIGHT_STYLESHEET):
        assert "QWidget {" not in sheet
        assert "QWidget{" not in sheet


def test_no_scrollbar_styling():
    for sheet in (theme.STYLESHEET, theme.LIGHT_STYLESHEET):
        assert "QScrollBar" not in sheet


def test_styles_concrete_widgets():
    assert "QPlainTextEdit" in theme.STYLESHEET
    assert "QTableView" in theme.STYLESHEET
    assert "QPushButton" in theme.STYLESHEET
