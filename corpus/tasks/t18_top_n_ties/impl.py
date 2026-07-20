def top_n(scores, n):
    """Return the n highest scores in descending order. Ties are broken by
    original position (stable), so equal scores keep their input order. If n
    exceeds len(scores), all scores are returned. Raises ValueError if n < 0.
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda p: (-p[1], p[0]))
    result = []
    for i in range(len(indexed)):
        if i < n:
            result.append(indexed[i][1])
    return result
