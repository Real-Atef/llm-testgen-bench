def split_amount(total_cents, n):
    """Split total_cents into n integer parts that sum exactly to total_cents.

    The remainder is distributed one cent at a time to the first parts, so the
    parts differ by at most one and their sum is always total_cents. Works for
    negative totals (floor division spreads the remainder consistently).
    Raises ValueError if n < 1.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    base = total_cents // n
    remainder = total_cents - base * n
    parts = []
    for i in range(n):
        if i < remainder:
            parts.append(base + 1)
        else:
            parts.append(base)
    return parts
