import pytest
from jfather import paths

DATA = {"users": [{"name": "Alice"}, {"name": "Bob"}], "n": 5}


def test_resolve_path_root():
    assert paths.resolve_path(DATA, []) is DATA


def test_resolve_path_nested():
    assert paths.resolve_path(DATA, ["users", 1, "name"]) == "Bob"


def test_resolve_path_invalid_raises():
    with pytest.raises((KeyError, IndexError, TypeError)):
        paths.resolve_path(DATA, ["users", 9])
    with pytest.raises((KeyError, IndexError, TypeError)):
        paths.resolve_path(DATA, ["n", "x"])


def test_nearest_valid_path_full():
    assert paths.nearest_valid_path(DATA, ["users", 0, "name"]) == ["users", 0, "name"]


def test_nearest_valid_path_truncates():
    assert paths.nearest_valid_path(DATA, ["users", 9, "name"]) == ["users"]
    assert paths.nearest_valid_path(DATA, ["missing"]) == []


def test_resolve_or_nearest():
    value, valid = paths.resolve_or_nearest(DATA, ["users", 9])
    assert value == DATA["users"]
    assert valid == ["users"]
