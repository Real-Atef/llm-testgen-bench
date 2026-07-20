def paginate(items, page, per_page):
    """Return the slice of items for a 1-indexed page.

    page and per_page must be >= 1. Pages beyond the data yield an empty list.
    Raises ValueError if page < 1 or per_page < 1.
    """
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]
