"""Spoken CAD requests, cleaned up before they reach the agent (ADR 0003, section 4).

Speech recognition writes what it heard: "eine Fase eins mal fünfundvierzig Grad", "Em sechs",
"Phase". normalize() turns German number words into numbers and fixes the terms and units a
mechanical engineer means ("eine Fase 1 × 45°", "M6"), and maps names spoken as words onto the names
in the open model ("countersink near wall" -> "CountersinkNearWall"). Numbers and units are read here
in code, not guessed by the model. Glossary: docs/research/2026-10-28-abgleich-baugruppe-glossar.md.
"""

import difflib
import re

UNITS = {"null": 0, "ein": 1, "eins": 1, "eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6,
         "sieben": 7, "acht": 8, "neun": 9}
TEENS = {"zehn": 10, "elf": 11, "zwölf": 12, "dreizehn": 13, "vierzehn": 14, "fünfzehn": 15, "sechzehn": 16,
         "siebzehn": 17, "achtzehn": 18, "neunzehn": 19}
TENS = {"zwanzig": 20, "dreißig": 30, "vierzig": 40, "fünfzig": 50, "sechzig": 60, "siebzig": 70,
        "achtzig": 80, "neunzig": 90}

# Terms speech recognition gets wrong in a CAD context (glossary column "Verwechslungsgefahr")
TERMS = [
    (r"\bPhasen?\b", lambda m: "Fasen" if m.group(0).endswith("n") else "Fase"),
    (r"\bFilet\b", "Fillet"), (r"\b(?:Tsch|Sch)ämfer\b", "Chamfer"),
    (r"\bKlangloch\b", "Langloch"), (r"\bBemessung\b", "Bemaßung"),
    (r"\bSenkbohrung\b", "Senkung"),
    (r"\bMillimetern?\b", "mm"), (r"\bZentimetern?\b", "cm"),
]


def _number(word: str) -> int | None:
    """A German number word up to 999 ("fünfundvierzig", "hundertzwanzig"), or None."""
    w = word.lower()
    if w in UNITS and w != "eine":
        return UNITS[w]
    if w in TEENS:
        return TEENS[w]
    if w in TENS:
        return TENS[w]
    m = re.fullmatch(r"(\w*?)hundert(?:und)?(\w*)", w)
    if m:
        h = 1 if m.group(1) in ("", "ein", "eins") else UNITS.get(m.group(1))
        rest = m.group(2)
        r = 0 if not rest else _number(rest)
        return None if h is None or r is None else h * 100 + r
    m = re.fullmatch(r"(\w+?)und(\w+)", w)
    if m and m.group(2) in TENS and m.group(1) in UNITS:
        return UNITS[m.group(1)] + TENS[m.group(2)]
    return None


def _numbers(text: str) -> str:
    """Number words to digits; "Komma" between numbers makes a decimal: "eins Komma fünf" -> "1.5"."""
    out = []
    for tok in re.split(r"(\s+)", text):
        n = _number(tok.strip(".,;:!?")) if tok.strip() else None
        # "eine Fase" stays an article; "eins"/"ein" before mal/Komma/units count as numbers
        if n is not None and tok.lower().strip(".,;:!?") != "ein":
            out.append(tok.lower().replace(tok.strip(".,;:!?").lower(), str(n)))
        else:
            out.append(tok)
    s = "".join(out)
    s = re.sub(r"\b(\d+)\s+Komma\s+(\d+)\b", r"\1.\2", s, flags=re.I)
    s = re.sub(r"\b(\d+),(\d+)\b", r"\1.\2", s)
    s = re.sub(r"\bein\s+(?=(?:mal|×|Komma|mm|Grad)\b)", "1 ", s, flags=re.I)
    return s


def _units(s: str) -> str:
    s = re.sub(r"(\d)\s*(?:mal|x|\*)\s*(\d)", r"\1 × \2", s, flags=re.I)
    s = re.sub(r"(\d)\s*Grad\b", r"\1°", s, flags=re.I)
    # Thread and radius designations: "Em sechs" / "M 6" -> "M6", "Er zwei" / "R 2" -> "R2"
    s = re.sub(r"\b(?:Em|M)\s*(\d+(?:\.\d+)?)\b", r"M\1", s)
    s = re.sub(r"\b(?:Er|R)\s+(\d+(?:\.\d+)?)\b", r"R\1", s)
    return s


def _names(s: str, names) -> str:
    """Words that run together into one of the model's names ("countersink near wall")."""
    keys = {re.sub(r"[^0-9a-zäöüß]", "", n.lower()): n for n in names if n and len(n) > 3}
    if not keys:
        return s
    words = s.split()
    out, i = [], 0
    while i < len(words):
        best = None
        spans = []
        for j in range(min(len(words), i + 5), i, -1):
            # numbers and units never belong to a name
            if any(re.search(r"\d|^(mm|cm|°|×)$", w) for w in words[i:j]):
                continue
            cand = re.sub(r"[^0-9a-zäöüß]", "", "".join(words[i:j]).lower())
            if len(cand) >= 4 and not (j - i == 1 and cand not in keys):
                spans.append((j, cand))
        # an exact run of words first; a near miss only when it is about as long as the name
        for j, cand in spans:
            if cand in keys:
                best = (j, keys[cand])
                break
        if best is None:
            for j, cand in spans:
                close = [k for k in difflib.get_close_matches(cand, keys, n=3, cutoff=0.88) if abs(len(k) - len(cand)) <= 1]
                if close:
                    best = (j, keys[close[0]])
                    break
        if best:
            out.append(best[1])
            i = best[0]
        else:
            out.append(words[i])
            i += 1
    return " ".join(out)


def normalize(text: str, names=()) -> str:
    s = text.strip()
    for pat, rep in TERMS:
        s = re.sub(pat, rep, s, flags=re.I)
    s = _numbers(s)
    s = _units(s)
    s = _names(s, names)
    return re.sub(r"\s+", " ", s).strip()
