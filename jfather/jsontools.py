"""Pure JSON utility functions used across jfather."""

import json


def parse(text):
    """Parse JSON text into a Python object. Raises json.JSONDecodeError."""
    return json.loads(text)


def validate(text):
    """Return (ok, message, line, col). On success message/line/col are None."""
    try:
        json.loads(text)
        return (True, None, None, None)
    except json.JSONDecodeError as exc:
        return (False, exc.msg, exc.lineno, exc.colno)


def format_json(text, indent=2):
    """Pretty-print JSON text with the given indent."""
    return json.dumps(json.loads(text), indent=indent, ensure_ascii=False)


def minify_json(text):
    """Return the most compact JSON representation."""
    return json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False)


def escape_string(raw):
    """Return a JSON string literal (with surrounding quotes) representing raw."""
    return json.dumps(raw, ensure_ascii=False)


def unescape_string(literal):
    """Decode a JSON string literal back to its raw value.

    Accepts the literal with or without surrounding double quotes.
    """
    literal = literal.strip()
    if literal.startswith('"') and literal.endswith('"') and len(literal) >= 2:
        return json.loads(literal)
    return json.loads('"' + literal + '"')
