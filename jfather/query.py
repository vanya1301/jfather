"""Parse query-bar tokens and run collection-query against list data."""

from collection_query import ListQuery

_VALID_OPS = ("filter", "exclude")


def coerce_scalar(s):
    """Coerce a string token value to int, float, bool, None, or str."""
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def coerce_value(token):
    """Coerce a token value to a scalar, list (a,b,c) or range (lo..hi)."""
    if ".." in token:
        lo, _, hi = token.partition("..")
        return range(int(lo), int(hi))
    if "," in token:
        return [coerce_scalar(part.strip()) for part in token.split(",")]
    return coerce_scalar(token)


def parse_token(token):
    """Parse 'field__lookup=value' into (key, coerced_value)."""
    if "=" not in token:
        raise ValueError(f"Invalid token (missing '='): {token!r}")
    key, _, value = token.partition("=")
    key = key.strip()
    if not key:
        raise ValueError(f"Empty field name in token: {token!r}")
    return key, coerce_value(value.strip())


def parse_tokens(text):
    """Parse whitespace-separated tokens into a kwargs dict."""
    return dict(parse_token(tok) for tok in text.split())


def run_query(data, rows):
    """Run filter/exclude rows against list data and return the result list.

    rows: list of (op, kwargs) where op is 'filter' or 'exclude'.
    """
    if not isinstance(data, list):
        raise ValueError("Query target must be a JSON array (list).")
    result = ListQuery(data)
    for op, kwargs in rows:
        if op not in _VALID_OPS:
            raise ValueError(f"Unknown query op: {op!r}")
        result = getattr(result, op)(**kwargs)
    return list(result)


def build_query(data, raw_rows):
    """Run query rows given as (op, token_text) strings."""
    rows = [(op, parse_tokens(text)) for op, text in raw_rows]
    return run_query(data, rows)
