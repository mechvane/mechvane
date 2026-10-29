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
# "Phase" is a chamfer ("Fase") only where a size or an edge is in the sentence: "in dieser Phase des
# Entwurfs" stays as it is
CHAMFER_CONTEXT = re.compile(r"\d|\b(?:mal|Grad|Kante|Kanten|Ecke|Ecken|mm|Millimeter|eins|zwei|drei|vier|fünf|"
                             r"sechs|sieben|acht|neun|zehn|halb)\b", re.I)
TERMS = [
    (r"\bPhasen?\b", lambda m: (("Fasen" if m.group(0).endswith("n") else "Fase")
                                 if CHAMFER_CONTEXT.search(m.string) else m.group(0))),
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


def _halves(text: str) -> str:
    """ "einhalb" -> 0.5, "zweieinhalb" / "eineinhalb" -> 2.5 / 1.5."""
    def half(m):
        whole = m.group(1).lower()
        if not whole:
            return "0.5"
        n = 1 if whole in ("ein", "eins") else _number(whole)
        return m.group(0) if n is None else f"{n}.5"
    return re.sub(r"\b(\w*?)einhalb\b", half, text, flags=re.I)


def _numbers(text: str) -> str:
    """Number words to digits; "Komma" between numbers makes a decimal: "eins Komma fünf" -> "1.5"."""
    text = _halves(text)
    out = []
    for tok in re.split(r"(\s+)", text):
        n = _number(tok.strip(".,;:!?")) if tok.strip() else None
        # "eine Fase" stays an article; "eins"/"ein" before mal/Komma/units count as numbers
        if n is not None and tok.lower().strip(".,;:!?") != "ein":
            out.append(tok.lower().replace(tok.strip(".,;:!?").lower(), str(n)))
        else:
            out.append(tok)
    s = "".join(out)
    s = re.sub(r"\bein\s+(?=(?:mal|×|Komma|mm|Grad)\b)", "1 ", s, flags=re.I)
    s = re.sub(r"\b(\d+)\s+Komma\s+(\d+)\b", r"\1.\2", s, flags=re.I)
    s = re.sub(r"\b(\d+),(\d+)\b", r"\1.\2", s)
    return s


def _units(s: str) -> str:
    s = re.sub(r"(\d)\s*(?:mal|x|\*)\s*(\d)", r"\1 × \2", s, flags=re.I)
    s = re.sub(r"(\d)\s*Grad\b", r"\1°", s, flags=re.I)
    s = re.sub(r"(\d)\s*Prozent\b", r"\1 %", s, flags=re.I)
    s = re.sub(r"\bDurchmesser\s+(\d+(?:\.\d+)?)", r"Ø\1", s, flags=re.I)
    # Thread and radius designations: "Em sechs" / "m sechs" / "M 6" -> "M6", "Er zwei" / "R 2" -> "R2";
    # a lowercase "er" only where the sentence is about rounding ("dann bohrt er 5 Löcher" stays)
    s = re.sub(r"\b(?:em|m)\s*(\d+(?:\.\d+)?)\b", r"M\1", s, flags=re.I)
    radius = re.compile(r"\b(?:Er|R)\s+(\d+(?:\.\d+)?)\b" if not re.search(r"rund|radius|fillet", s, re.I)
                        else r"\b(?:er|r)\s+(\d+(?:\.\d+)?)\b", 0 if not re.search(r"rund|radius|fillet", s, re.I) else re.I)
    s = radius.sub(r"R\1", s)
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
            # units never belong to a name; a number only when the whole run is exactly a name ("hole 1")
            if any(re.search(r"^(mm|cm|°|×|%)$", w) for w in words[i:j]):
                continue
            cand = re.sub(r"[^0-9a-zäöüß]", "", "".join(words[i:j]).lower())
            if any(re.search(r"\d", w) for w in words[i:j]):
                if cand in keys and not re.fullmatch(r"\d+", cand):
                    spans.append((j, cand))
                continue
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
