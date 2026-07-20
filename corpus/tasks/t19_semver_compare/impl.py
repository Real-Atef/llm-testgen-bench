def compare_semver(a, b):
    """Compare two 'MAJOR.MINOR.PATCH' version strings (numeric only).

    Returns -1 if a < b, 1 if a > b, and 0 if equal, comparing each component
    numerically (so '1.10.0' > '1.9.0'). Raises ValueError if either string does
    not have exactly three integer components.
    """
    pa = a.split(".")
    pb = b.split(".")
    if len(pa) != 3 or len(pb) != 3:
        raise ValueError("expected MAJOR.MINOR.PATCH")
    for i in range(3):
        x = int(pa[i])
        y = int(pb[i])
        if x < y:
            return -1
        if x > y:
            return 1
    return 0
