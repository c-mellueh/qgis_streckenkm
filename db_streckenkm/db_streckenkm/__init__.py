import re
def string_to_real(text: str) -> float | None:
    if text is None:
        return None
    head, tail = re.findall("(-?\d+,\d) \+ (-?\d+)", text)[0]
    head = float(head.replace(",", "."))
    return round(head + int(tail) / 1000, 4)