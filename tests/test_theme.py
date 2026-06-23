from jfather import theme


def test_no_universal_widget_rule():
    assert "QWidget {" not in theme.STYLESHEET
    assert "QWidget{" not in theme.STYLESHEET


def test_no_scrollbar_styling():
    assert "QScrollBar" not in theme.STYLESHEET


def test_styles_concrete_widgets():
    assert "QPlainTextEdit" in theme.STYLESHEET
    assert "QTableView" in theme.STYLESHEET
    assert "QPushButton" in theme.STYLESHEET


def test_light_theme_removed():
    assert not hasattr(theme, "LIGHT_STYLESHEET")


def test_font_constants_present():
    assert "sans-serif" in theme.UI_FONT_FAMILY
    assert "monospace" in theme.MONO_FONT_FAMILY
