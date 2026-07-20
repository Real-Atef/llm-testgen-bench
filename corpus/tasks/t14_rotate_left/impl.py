def rotate_left(items, n):
    """Return a new list with elements rotated left by n positions, without
    mutating the input. n may exceed len(items) or be negative (a negative n
    rotates right). An empty list rotates to a fresh empty list.
    """
    length = len(items)
    if length == 0:
        return list(items)
    shift = n
    while shift < 0:
        shift = shift + length
    while shift >= length:
        shift = shift - length
    return items[shift:] + items[:shift]
