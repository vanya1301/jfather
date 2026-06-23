from PySide6.QtCore import QModelIndex, Qt
from jfather.tree_model import JsonTreeModel, index_for_path


def test_index_for_path_top_level():
    model = JsonTreeModel({"a": 1, "b": 2})
    idx = index_for_path(model, ["b"])
    assert idx.isValid()
    assert model.data(idx, Qt.DisplayRole) == "b"


def test_index_for_path_nested():
    model = JsonTreeModel({"outer": {"inner": 42}})
    idx = index_for_path(model, ["outer", "inner"])
    assert idx.isValid()
    assert model.data(model.index(idx.row(), 1, idx.parent()), Qt.DisplayRole) == "42"


def test_index_for_path_into_list():
    model = JsonTreeModel({"items": [{"name": "x"}, {"name": "y"}]})
    idx = index_for_path(model, ["items", 1, "name"])
    assert idx.isValid()
    assert model.data(idx, Qt.DisplayRole) == "name"


def test_index_for_path_missing_returns_invalid():
    model = JsonTreeModel({"a": 1})
    assert index_for_path(model, ["nope"]) == QModelIndex()
    assert index_for_path(model, ["a", "deeper"]) == QModelIndex()
