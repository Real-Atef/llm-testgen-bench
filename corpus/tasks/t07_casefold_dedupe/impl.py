def casefold_dedupe(words):
    """Remove case-insensitive duplicates, keeping the first occurrence in its
    original form. Comparison uses str.casefold(), so 'STRASSE', 'strasse' and
    'straße' all collide.
    """
    keys = []
    result = []
    for w in words:
        key = w.casefold()
        found = False
        for k in keys:
            if k == key:
                found = True
        if not found:
            keys.append(key)
            result.append(w)
    return result
