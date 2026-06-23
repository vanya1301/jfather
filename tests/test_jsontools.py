import json
import pytest
from jfather import jsontools


def test_parse_valid():
    assert jsontools.parse('{"a": 1}') == {"a": 1}


def test_validate_ok():
    ok, msg, line, col = jsontools.validate('{"a": 1}')
    assert ok is True and msg is None


def test_validate_error_reports_position():
    ok, msg, line, col = jsontools.validate('{"a": }')
    assert ok is False
    assert isinstance(msg, str) and msg
    assert line == 1 and col is not None


def test_format_json_indents():
    assert jsontools.format_json('{"a":1}', indent=2) == '{\n  "a": 1\n}'


def test_format_preserves_unicode():
    assert jsontools.format_json('{"a":"\u00e9"}') == '{\n  "a": "\u00e9"\n}'


def test_minify_json():
    assert jsontools.minify_json('{\n  "a": 1\n}') == '{"a":1}'


def test_escape_string_wraps_and_escapes():
    assert jsontools.escape_string('he said "hi"\n') == '"he said \\"hi\\"\\n"'


def test_unescape_string_with_quotes():
    assert jsontools.unescape_string('"he said \\"hi\\"\\n"') == 'he said "hi"\n'


def test_unescape_string_without_quotes():
    assert jsontools.unescape_string('a\\tb') == 'a\tb'


def test_roundtrip_escape_unescape():
    raw = 'line1\nline2\t"quoted"'
    assert jsontools.unescape_string(jsontools.escape_string(raw)) == raw
