def dedupe(items):
    """Return a new list with duplicates removed, preserving first-seen order.
    The input list is not mutated. Equality (not hashing) decides duplicates, so
    the elements need not be hashable.
    """
    seen = []
    result = []
    for x in items:
        is_new = True
        for s in seen:
            if s == x:
                is_new = False
        if is_new:
            seen.append(x)
            result.append(x)
    return result
