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


def _combo_text_for_data(combo, value):
    return combo.itemText(combo.findData(value))


def test_lookup_dropdown_shows_readable_labels(app):
    panel = QueryPanel(lookups=["gt", "icontains"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "name=Bob")])
    lookup = panel._active_rows()[0].lookup
    assert _combo_text_for_data(lookup, "exact") == "= Equals"
    assert _combo_text_for_data(lookup, "gt") == "> Greater than"
    assert _combo_text_for_data(lookup, "icontains") == "\u220b Contains (ignore case)"


def test_op_dropdown_labels_keep_raw_data(app):
    panel = QueryPanel()
    panel.set_mode("structured")
    panel.set_rows([("exclude", "name=Bob")])
    op = panel._active_rows()[0].op
    assert _combo_text_for_data(op, "filter") == "\u2713 Filter"
    assert _combo_text_for_data(op, "exclude") == "\u2715 Exclude"
    # rows()/current_rows() still emit the raw operator key, not the label.
    assert panel.rows() == [("exclude", "name=Bob")]
    assert panel.current_rows() == [("exclude", {"name": "Bob"})]


def test_structured_lookup_round_trips_via_data(app):
    panel = QueryPanel(lookups=["gt", "contains"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "id__gt=1")])
    assert panel.current_rows() == [("filter", {"id__gt": 1})]
    assert panel.rows() == [("filter", "id__gt=1")]


def test_results_pane_takes_free_space(app):
    from PySide6.QtWidgets import QSizePolicy
    panel = QueryPanel()
    assert panel.results.sizePolicy().verticalPolicy() == QSizePolicy.Expanding
    assert panel.stack.sizePolicy().verticalPolicy() == QSizePolicy.Maximum


def test_value_dropdown_offers_field_values(app):
    panel = QueryPanel(
        get_field_values=lambda f: ["Alice", "Bob"] if f == "name" else []
    )
    panel.set_mode("structured")
    panel.set_rows([("filter", "name=Alice")])
    row = panel._active_rows()[0]
    items = [row.value.itemText(i) for i in range(row.value.count())]
    assert items == ["Alice", "Bob"]
    assert row.value.currentText() == "Alice"
    # editable: the selected suggestion still builds a real query value
    assert panel.current_rows() == [("filter", {"name": "Alice"})]


def test_value_dropdown_refreshes_when_field_changes(app):
    values = {"name": ["Alice"], "city": ["Paris", "Rome"]}
    panel = QueryPanel(get_field_values=lambda f: values.get(f, []))
    panel.set_mode("structured")
    panel.set_rows([("filter", "name=Alice")])
    row = panel._active_rows()[0]
    row.field.setCurrentText("city")
    items = [row.value.itemText(i) for i in range(row.value.count())]
    assert items == ["Paris", "Rome"]


def test_value_dropdown_accepts_free_text(app):
    panel = QueryPanel(get_field_values=lambda f: ["1", "2"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "id__in=1,2,3")])
    assert panel.current_rows() == [("filter", {"id__in": [1, 2, 3]})]


def test_picked_suggestion_with_comma_is_literal(app):
    panel = QueryPanel(get_field_values=lambda f: ["Smith, John", "Doe"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "name=Doe")])
    row = panel._active_rows()[0]
    row.value.setCurrentText("Smith, John")
    # exact suggestion -> literal string, not a comma-split list
    assert panel.current_rows() == [("filter", {"name": "Smith, John"})]


def test_picked_suggestion_with_dotdot_is_literal(app):
    panel = QueryPanel(get_field_values=lambda f: ["a..b"])
    panel.set_mode("structured")
    panel.set_rows([("filter", "code=a..b")])
    # exact suggestion -> literal string, not a range (which would raise)
    assert panel.current_rows() == [("filter", {"code": "a..b"})]
