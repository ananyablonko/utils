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