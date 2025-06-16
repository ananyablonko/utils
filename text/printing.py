import black
from typing import Any

def prettify(obj):
    return black.format_str(str(obj), mode=black.Mode(line_length=120))


def shorten(s: Any, m=250) -> str:
    s = str(s)
    return s if len(s) < m else (s[:(m // 2)] + '...' + s[-(m // 2):])