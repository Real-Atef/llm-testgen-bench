def chunk(items, size):
    """Split items into consecutive chunks of length `size`.

    The final chunk may be shorter than `size`. Raises ValueError if size < 1.
    An empty input yields an empty list.
    """
    if size < 1:
        raise ValueError("size must be >= 1")
    result = []
    for i in range(0, len(items), size):
        result.append(items[i:i + size])
    return result
