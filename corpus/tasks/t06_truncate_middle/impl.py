def truncate_middle(s, max_len):
    """Truncate s to at most max_len characters, inserting '...' in the middle.

    If len(s) <= max_len the string is returned unchanged. Otherwise the result
    is exactly max_len characters: a left slice, '...', and a right slice, with
    the left slice getting the extra character when the kept length is odd.
    Requires max_len >= 5; raises ValueError otherwise.
    """
    if max_len < 5:
        raise ValueError("max_len must be >= 5")
    if len(s) <= max_len:
        return s
    keep = max_len - 3
    left = (keep + 1) // 2
    right = keep - left
    return s[:left] + "..." + s[len(s) - right:]
