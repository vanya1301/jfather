from jfather import search

DATA = {
    "user": {"name": "Alice", "role": "admin"},
    "items": [{"name": "apple"}, {"name": "banana"}],
}


def test_search_matches_values():
    assert search.search(DATA, "alice") == [["user", "name"]]


def test_search_matches_keys():
    paths = search.search(DATA, "role")
    assert ["user", "role"] in paths


def test_search_case_sensitive():
    assert search.search(DATA, "alice", case_sensitive=True) == []
    assert search.search(DATA, "Alice", case_sensitive=True) == [["user", "name"]]


def test_search_values_only():
    paths = search.search(DATA, "name", keys=False, values=True)
    assert paths == []


def test_search_into_list():
    paths = search.search(DATA, "banana")
    assert paths == [["items", 1, "name"]]


def test_search_depth_first_order():
    data = {"a": "x", "b": "x"}
    assert search.search(data, "x") == [["a"], ["b"]]
