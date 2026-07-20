def group_by_parity(numbers):
    """Group integers into 'even' and 'odd' buckets, preserving the input order
    within each bucket and only creating a bucket when it is first needed.

    Returns a dict mapping the group name to a list of the numbers in that
    group. An empty input returns an empty dict.
    """
    groups = {}
    order = []
    for x in numbers:
        if x % 2 == 0:
            name = "even"
        else:
            name = "odd"
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(x)
    result = {}
    for name in order:
        result[name] = groups[name]
    return result
