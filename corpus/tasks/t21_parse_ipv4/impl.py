def is_valid_ipv4(s):
    """Return True if s is a valid dotted-decimal IPv4 address, else False.

    Requires exactly four parts separated by '.', each a run of ASCII digits in
    the range 0-255 with no leading zeros (except '0' itself), and no signs or
    whitespace.
    """
    parts = s.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if len(part) == 0:
            return False
        if not part.isascii() or not part.isdigit():
            return False
        if len(part) > 1 and part[0] == "0":
            return False
        value = int(part)
        if value < 0 or value > 255:
            return False
    return True
