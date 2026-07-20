def last_index_of(items, target):
    """Return the index of the last occurrence of target in items, or -1.

    An empty list, or a target that is absent, yields -1.
    """
    if len(items) == 0:
        return -1
    result = -1
    for i in range(len(items)):
        if items[i] == target:
            result = i
    return result
