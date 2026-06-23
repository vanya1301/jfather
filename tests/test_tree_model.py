from PySide6.QtCore import QModelIndex, Qt
from jfather.tree_model import JsonNode, JsonTreeModel, type_name


def test_type_name():
    assert type_name({}) == "object"
    assert type_name([]) == "array"
    assert type_name("s") == "string"
    assert type_name(1) == "number"
    assert type_name(1.5) == "number"
    assert type_name(True) == "boolean"
    assert type_name(None) == "null"


def test_node_child_count_without_building():
    node = JsonNode("root", {"a": 1, "b": 2})
    assert node.child_count() == 2
    assert node._children is None  # not built yet


def test_node_children_lazy_build():
    node = JsonNode("root", [10, 20])
    children = node.children()
    assert [c.key for c in children] == [0, 1]
    assert [c.value for c in children] == [10, 20]


def test_node_leaf_has_no_children():
    assert JsonNode("k", 5).child_count() == 0
    assert JsonNode("k", 5).is_container is False


def test_model_rowcount_and_data():
    model = JsonTreeModel({"a": 1})
    assert model.rowCount(QModelIndex()) == 1
    idx_key = model.index(0, 0, QModelIndex())
    idx_val = model.index(0, 1, QModelIndex())
    idx_type = model.index(0, 2, QModelIndex())
    assert model.data(idx_key, Qt.DisplayRole) == "a"
    assert model.data(idx_val, Qt.DisplayRole) == "1"
    assert model.data(idx_type, Qt.DisplayRole) == "number"


def test_model_nested_parent_child():
    model = JsonTreeModel({"outer": {"inner": 1}})
    outer = model.index(0, 0, QModelIndex())
    assert model.rowCount(outer) == 1
    inner = model.index(0, 0, outer)
    assert model.data(inner, Qt.DisplayRole) == "inner"
    assert model.parent(inner) == outer


def test_model_container_value_summary():
    model = JsonTreeModel({"a": [1, 2, 3]})
    val = model.index(0, 1, QModelIndex())
    assert model.data(val, Qt.DisplayRole) == "[3 items]"


def test_set_json_resets():
    model = JsonTreeModel({"a": 1})
    model.set_json([1, 2])
    assert model.rowCount(QModelIndex()) == 2


def test_path_for_index_nested():
    from jfather.tree_model import path_for_index
    model = JsonTreeModel({"users": [{"name": "Bob"}]})
    users = model.index(0, 0, QModelIndex())
    first = model.index(0, 0, users)
    name = model.index(0, 0, first)
    assert path_for_index(name) == ["users", 0, "name"]


def test_path_for_index_invalid_is_empty():
    from jfather.tree_model import path_for_index
    assert path_for_index(QModelIndex()) == []
