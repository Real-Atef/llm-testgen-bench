import unicodedata


def visible_length(s):
    """Count visible characters, ignoring Unicode combining marks.

    A combining mark (non-zero combining class, e.g. a combining accent) does
    not add to the count, so 'e' + U+0301 counts as one, matching the
    precomposed 'é'. Empty string is 0.
    """
    count = 0
    for ch in s:
        if unicodedata.combining(ch) == 0:
            count = count + 1
    return count
