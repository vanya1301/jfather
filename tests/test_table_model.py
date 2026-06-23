from PySide6.QtCore import QModelIndex, Qt
from jfather.table_model import JsonTableModel, is_tabular


def test_is_tabular_true_for_list_of_dicts():
    assert is_tabular([{"a": 1}, {"a": 2}]) is True


def test_is_tabular_half_dicts():
    assert is_tabular([{"a": 1}, 5]) is True  # 1 of 2 is a dict


def test_is_tabular_false_cases():
    assert is_tabular([]) is False
    assert is_tabular({"a": 1}) is False
    assert is_tabular([1, 2, 3]) is False


def test_columns_are_union_in_first_seen_order():
    model = JsonTableModel([{"b": 1, "a": 2}, {"a": 3, "c": 4}])
    assert model.columnCount() == 3
    headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(3)]
    assert headers == ["b", "a", "c"]


def test_cell_scalar_and_nested_rendering():
    model = JsonTableModel([{"a": 1, "b": {"x": 2}, "c": [1, 2, 3]}])
    a = model.index(0, 0, QModelIndex())
    b = model.index(0, 1, QModelIndex())
    c = model.index(0, 2, QModelIndex())
    assert model.data(a, Qt.DisplayRole) == "1"
    assert model.data(b, Qt.DisplayRole) == "{\u2026} 1 key"
    assert model.data(c, Qt.DisplayRole) == "[\u2026] 3 items"


def test_nested_cell_tooltip_is_pretty_json():
    model = JsonTableModel([{"b": {"x": 2}}])
    b = model.index(0, 0, QModelIndex())
    tip = model.data(b, Qt.ToolTipRole)
    assert tip == '{\n  "x": 2\n}'


def test_scalar_cell_has_no_tooltip():
    model = JsonTableModel([{"a": 1}])
    a = model.index(0, 0, QModelIndex())
    assert model.data(a, Qt.ToolTipRole) is None


def test_missing_key_is_empty():
    model = JsonTableModel([{"a": 1}, {"b": 2}])
    cell = model.index(0, 1, QModelIndex())  # row 0 has no "b"
    assert model.data(cell, Qt.DisplayRole) == ""


def test_row_object():
    rows = [{"a": 1}, {"a": 2}]
    model = JsonTableModel(rows)
    assert model.row_object(1) == {"a": 2}


def test_set_rows_resets():
    model = JsonTableModel([{"a": 1}])
    model.set_rows([{"x": 1}, {"x": 2}])
    assert model.rowCount() == 2
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "x"
