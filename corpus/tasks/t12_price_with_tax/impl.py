def price_with_tax(cents, tax_rate_percent):
    """Return the price in cents including tax, rounded to the nearest cent
    (round half up). tax_rate_percent is an integer percentage (8 means 8%).

    Integer arithmetic ((cents * rate + 50) // 100) keeps the rounding exact and
    avoids binary-float surprises. Raises ValueError if either input is negative.
    """
    if cents < 0 or tax_rate_percent < 0:
        raise ValueError("inputs must be non-negative")
    tax = (cents * tax_rate_percent + 50) // 100
    return cents + tax
