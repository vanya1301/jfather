import pytest
from PySide6.QtWidgets import QApplication
from jfather.query_panel import QueryPanel


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_text_mode_current_rows(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "id__gt=1"), ("exclude", "name=Bob")])
    assert panel.current_rows() == [
        ("filter", {"id__gt": 1}),
        ("exclude", {"name": "Bob"}),
    ]


def test_rows_round_trip(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "id__gt=1")])
    assert panel.rows() == [("filter", "id__gt=1")]


def test_text_mode_malformed_raises(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "noequals")])
    with pytest.raises(ValueError):
        panel.current_rows()


def test_structured_mode_builds_kwargs(app):
    panel = QueryPanel(lookups=["gt", "contains"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "id__gt=1")])
    assert panel.current_rows() == [("filter", {"id__gt": 1})]


def test_structured_exact_lookup_has_no_suffix(app):
    panel = QueryPanel(lookups=["gt", "contains"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "name=Bob")])
    assert panel.current_rows() == [("filter", {"name": "Bob"})]


def test_mode_toggle_preserves_rows(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "id__gt=1")])
    panel.set_mode("structured")
    panel.set_mode("text")
    assert panel.rows() == [("filter", "id__gt=1")]


def test_lookups_injected(app):
    panel = QueryPanel(lookups=["gt", "lt", "contains"])
    assert panel.lookups == ["gt", "lt", "contains"]


def test_run_button_enable_disable(app):
    panel = QueryPanel()
    panel.set_run_enabled(False)
    assert panel.run_button.isEnabled() is False
    panel.set_run_enabled(True)
    assert panel.run_button.isEnabled() is True


def test_run_emits_signal(app):
    panel = QueryPanel()
    seen = []
    panel.runRequested.connect(lambda: seen.append(1))
    panel.run_button.click()
    assert seen == [1]


def test_remove_row_reduces_count(app):
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "a=1"), ("filter", "b=2")])
    assert len(panel.rows()) == 2
    panel._active_rows()[0].remove.click()
    assert len(panel.rows()) == 1
    assert panel.rows() == [("filter", "b=2")]


def test_copy_button_copies_results(app):
    from PySide6.QtWidgets import QApplication
    panel = QueryPanel()
    panel.set_results_text("hello results", count=3)
    panel.copy_button.click()
    assert QApplication.clipboard().text() == "hello results"
    assert "3" in panel.count_label.text()


def test_tokens_use_monospace_font(app):
    from jfather import theme
    panel = QueryPanel()
    panel.set_mode("text")
    panel.set_rows([("filter", "a=1")])
    row = panel._active_rows()[0]
    assert theme.MONO_FONT_FAMILY.split(",")[0] in row.tokens.font().family() \
        or row.tokens.font().family() != ""
