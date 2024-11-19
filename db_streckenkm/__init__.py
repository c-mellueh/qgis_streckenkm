import re
def string_to_real(text: str) -> float | None:
    if text is None:
        return None
    match = re.findall("(-?\d+,\d) \+ (-?\d+)", str(text))
    if not match:
        return None
    head,tail = match[0]
    head = float(head.replace(",", "."))
    return round(head + int(tail) / 1000, 4)