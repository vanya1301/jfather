"""Resolve key/index paths into parsed JSON structures."""


def _step(node, key):
    if isinstance(node, dict):
        return node[key]
    if isinstance(node, list):
        if not isinstance(key, int):
            raise TypeError(f"List index must be int, got {key!r}")
        return node[key]
    raise TypeError(f"Cannot index into {type(node).__name__}")


def resolve_path(data, path):
    """Follow path (keys/indices) into data. Raises on an invalid segment."""
    node = data
    for key in path:
        node = _step(node, key)
    return node


def nearest_valid_path(data, path):
    """Return the longest prefix of path that resolves within data."""
    valid = []
    node = data
    for key in path:
        try:
            node = _step(node, key)
        except (KeyError, IndexError, TypeError):
            break
        valid.append(key)
    return valid


def resolve_or_nearest(data, path):
    """Return (value, valid_path) using the nearest valid prefix of path."""
    valid = nearest_valid_path(data, path)
    return resolve_path(data, valid), valid
