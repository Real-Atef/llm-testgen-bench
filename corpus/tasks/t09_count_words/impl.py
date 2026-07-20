def count_words(text):
    """Count whitespace-separated words in text.

    Leading, trailing, and repeated whitespace are handled; a run of whitespace
    separates two words but adds no extra count. Empty or all-whitespace text
    has zero words.
    """
    count = 0
    in_word = False
    for ch in text:
        if ch.isspace():
            in_word = False
        else:
            if not in_word:
                count = count + 1
            in_word = True
    return count
