def sum_cents(amounts):
    """Sum a list of dollar amounts (floats) and return the total in integer
    cents, rounding each amount to the nearest cent (round half up).

    Converting each amount to cents *before* summing avoids the classic
    floating-point accumulation error of summing dollars and multiplying later.
    An empty list totals 0.
    """
    total = 0
    for a in amounts:
        if a >= 0:
            cents = int(a * 100 + 0.5)
        else:
            cents = -int(-a * 100 + 0.5)
        total = total + cents
    return total
