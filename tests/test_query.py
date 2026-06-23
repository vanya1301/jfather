import pytest
from jfather import query

DATA = [
    {"id": 1, "name": "Alice", "dept": {"name": "Eng"}},
    {"id": 2, "name": "Bob", "dept": {"name": "Sales"}},
    {"id": 3, "name": "Cy", "dept": {"name": "Eng"}},
]


def test_coerce_scalar_types():
    assert query.coerce_scalar("5") == 5
    assert query.coerce_scalar("5.5") == 5.5
    assert query.coerce_scalar("true") is True
    assert query.coerce_scalar("false") is False
    assert query.coerce_scalar("null") is None
    assert query.coerce_scalar("hello") == "hello"


def test_coerce_value_list():
    assert query.coerce_value("a,b,c") == ["a", "b", "c"]


def test_coerce_value_range():
    assert query.coerce_value("1..3") == range(1, 3)


def test_parse_token():
    assert query.parse_token("id__gt=1") == ("id__gt", 1)


def test_parse_token_missing_equals():
    with pytest.raises(ValueError):
        query.parse_token("idgt")


def test_parse_tokens_multiple():
    assert query.parse_tokens("id__gt=1 name=Cy") == {"id__gt": 1, "name": "Cy"}


def test_run_query_filter_nested_and_lookup():
    rows = [("filter", {"dept__name": "Eng", "id__gt": 1})]
    assert query.run_query(DATA, rows) == [DATA[2]]


def test_run_query_exclude_chain():
    rows = [("filter", {"dept__name": "Eng"}), ("exclude", {"name": "Cy"})]
    assert query.run_query(DATA, rows) == [DATA[0]]


def test_run_query_in_range():
    data = [{"id": i} for i in range(6)]
    rows = [("filter", {"id__in_range": range(1, 3)})]
    assert query.run_query(data, rows) == [{"id": 1}, {"id": 2}]


def test_run_query_rejects_non_list():
    with pytest.raises(ValueError):
        query.run_query({"a": 1}, [("filter", {"a": 1})])


def test_run_query_rejects_bad_op():
    with pytest.raises(ValueError):
        query.run_query(DATA, [("nope", {"id": 1})])


def test_build_query_end_to_end():
    raw_rows = [("filter", "dept__name=Eng"), ("exclude", "name=Cy")]
    assert query.build_query(DATA, raw_rows) == [DATA[0]]
