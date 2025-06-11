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


def navigate(json: dict, path: list[str | int]) -> str | None:
    current = json
    err_msg = f"Invalid Path.\n{path=}"
    for key in path:
        match (current, key):
            case (list() as seq, int() as idx) if not isinstance(key, bool):
                if idx < 0 or idx >= len(seq):
                    raise IndexError(f"{err_msg}\nIndex out of range.\nlength={len(seq)}\nindex={idx}")
                current = seq[idx]
            case (dict() as mapping, str() as field):
                if field not in mapping:
                    raise KeyError(f"{err_msg}\nField {field} does not exist.\nfields={list(mapping.keys())}")
                current = mapping[field]
            case (list() as seq, str() as field):
                raise TypeError(f"{err_msg}\nCannot index list with a string.\nlist={seq}\nstring={field}")
            case (dict() as mapping, int() as idx) if not isinstance(key, bool):
                raise TypeError(f"{err_msg}\nCannot index object with an integer.\nobject={mapping}\ninteger={idx}")
            case _:
                raise ValueError(f"{err_msg}\nKeys may only be strings or integer indices!")
    return str(current)