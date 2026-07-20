def overlap_length(a_start, a_end, b_start, b_end):
    """Length of the overlap between two half-open intervals [start, end).

    Returns 0 when the intervals do not overlap (touching endpoints do not
    count, since the intervals are half-open). Each interval is assumed valid
    (start <= end).
    """
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if end > start:
        return end - start
    return 0
