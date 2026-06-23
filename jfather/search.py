"""Search keys and values within a parsed JSON object, returning paths."""


def search(data, term, *, keys=True, values=True, case_sensitive=False):
    """Return depth-first list of paths where a key or value matches term."""
    needle = term if case_sensitive else term.lower()

    def matches(text):
        text = str(text)
        if not case_sensitive:
            text = text.lower()
        return needle in text

    results = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if keys and matches(key):
                    results.append(path + [key])
                walk(value, path + [key])
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, path + [index])
        else:
            if values and matches(node):
                results.append(path)

    walk(data, [])
    return results
