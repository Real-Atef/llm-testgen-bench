def compare_semver(a, b):
    """Compare two 'MAJOR.MINOR.PATCH' version strings (numeric only).

    Returns -1 if a < b, 1 if a > b, and 0 if equal, comparing each component
    numerically (so '1.10.0' > '1.9.0'). Raises ValueError if either string does
    not have exactly three integer components. Both strings are fully validated
    before any comparison, so an invalid component is rejected even when an
    earlier component already decides the order.
    """
    def parse(v):
        parts = v.split(".")
        if len(parts) != 3:
            raise ValueError("expected MAJOR.MINOR.PATCH")
        return [int(p) for p in parts]  # int() raises ValueError on non-integers

    pa = parse(a)
    pb = parse(b)
    for i in range(3):
        if pa[i] < pb[i]:
            return -1
        if pa[i] > pb[i]:
            return 1
    return 0
