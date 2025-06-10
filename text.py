import black
from typing import Any
import re
import unicodedata


# for hebrew textbook parsing
NIQQUD = r'[\u0591-\u05C7]'
HEBREW = r'[\u0590-\u05FF]'
REVERSED_NIQQUD = r'[\u05bc\u05c2\u05b9]'
SHIN = r'\u05e9'
PATTERNS = [
    (re.compile(fr'({NIQQUD})\s+({HEBREW})'), r'\1\2'),
    (re.compile(fr'({REVERSED_NIQQUD})({HEBREW})'), r'\2\1'),
    (re.compile(r' +'), r' '),
]

def clean_hebrew(text: str) -> str:
    for pat, rep in PATTERNS:
        text = pat.sub(rep, text)
    return unicodedata.normalize("NFC", text).strip()


def prettify(obj):
    return black.format_str(str(obj), mode=black.Mode(line_length=120))


def shorten(s: Any, m=250) -> str:
    s = str(s)
    return s if len(s) < m else (s[:(m // 2)] + '...' + s[-(m // 2):])