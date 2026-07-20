def parse_query(qs):
    """Parse a URL query string like 'a=1&b=2&a=3' into a dict.

    Later duplicate keys overwrite earlier ones. A key with no '=' maps to the
    empty string. Empty pairs from leading, trailing, or doubled '&' are
    skipped. A single leading '?' is ignored. Values are not URL-decoded, and
    only the first '=' in a pair splits key from value.
    """
    if qs.startswith("?"):
        qs = qs[1:]
    result = {}
    for pair in qs.split("&"):
        if pair == "":
            continue
        if "=" in pair:
            idx = pair.index("=")
            key = pair[:idx]
            value = pair[idx + 1:]
        else:
            key = pair
            value = ""
        result[key] = value
    return result
