def sort_by_key(items, key_index):
    """Return a new list sorted ascending by element[key_index], without
    mutating the input list. Ties preserve their original order (stable), which
    a hand-written insertion sort with a strict '>' comparison guarantees.
    """
    result = list(items)
    n = len(result)
    for i in range(1, n):
        j = i
        while j > 0 and result[j - 1][key_index] > result[j][key_index]:
            result[j - 1], result[j] = result[j], result[j - 1]
            j = j - 1
    return result
