def first_non_empty(values):
    """Return the first value that is not None and not empty after stripping
    whitespace. Returns None if there is no such value.

    Values are returned unchanged (not stripped). None entries are skipped.
    """
    for v in values:
        if v is not None and len(v.strip()) > 0:
            return v
    return None
