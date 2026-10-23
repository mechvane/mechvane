"""ISO 286-1 limits and fits for nominal sizes up to 500 mm.

Tables are ISO 286-1 standard tolerance grades (IT5-IT11) and the fundamental
deviations of the common shaft letters, in micrometres per nominal size range.
Hole deviations follow the ISO 286-1 rules: A-H mirror the shaft (EI = -es),
JS is symmetric, K/M/N (up to IT8) and P (up to IT7) use ES = -ei + delta.
Values verified against the sources in docs/research/2026-10-23-iso286-tabellen.md.
"""

import re

# Upper bounds of the nominal size ranges (mm); a range includes its upper bound.
RANGES = (3, 6, 10, 18, 30, 50, 80, 120, 180, 250, 315, 400, 500)

IT = {
    5: (4, 5, 6, 8, 9, 11, 13, 15, 18, 20, 23, 25, 27),
    6: (6, 8, 9, 11, 13, 16, 19, 22, 25, 29, 32, 36, 40),
    7: (10, 12, 15, 18, 21, 25, 30, 35, 40, 46, 52, 57, 63),
    8: (14, 18, 22, 27, 33, 39, 46, 54, 63, 72, 81, 89, 97),
    9: (25, 30, 36, 43, 52, 62, 74, 87, 100, 115, 130, 140, 155),
    10: (40, 48, 58, 70, 84, 100, 120, 140, 160, 185, 210, 230, 250),
    11: (60, 75, 90, 110, 130, 160, 190, 220, 250, 290, 320, 360, 400),
}

# Upper deviation es of shafts d-h (micrometres).
SHAFT_ES = {
    "d": (-20, -30, -40, -50, -65, -80, -100, -120, -145, -170, -190, -210, -230),
    "e": (-14, -20, -25, -32, -40, -50, -60, -72, -85, -100, -110, -125, -135),
    "f": (-6, -10, -13, -16, -20, -25, -30, -36, -43, -50, -56, -62, -68),
    "g": (-2, -4, -5, -6, -7, -9, -10, -12, -14, -15, -17, -18, -20),
    "h": (0,) * 13,
}

# Lower deviation ei of shafts k-p (micrometres); k applies to IT4-IT7, else 0.
SHAFT_EI = {
    "k": (0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4, 5),
    "m": (2, 4, 6, 7, 8, 9, 11, 13, 15, 17, 20, 21, 23),
    "n": (4, 8, 10, 12, 15, 17, 20, 23, 27, 31, 34, 37, 40),
    "p": (6, 12, 15, 18, 22, 26, 32, 37, 43, 50, 56, 62, 68),
}

HOLE_MAX_GRADE = {"K": 8, "M": 8, "N": 8, "P": 7}


def _range_index(nominal: float) -> int:
    if not 0 < nominal <= RANGES[-1]:
        raise ValueError(f"nominal size {nominal} mm outside ISO 286 table range (0, {RANGES[-1]}]")
    return next(i for i, upper in enumerate(RANGES) if nominal <= upper)


def _parse(tolerance: str) -> tuple[str, int]:
    m = re.fullmatch(r"\s*(js|JS|[a-zA-Z])\s*(\d{1,2})\s*", tolerance or "")
    if not m:
        raise ValueError(f"invalid tolerance class {tolerance!r} (e.g. 'H7', 'k6', 'JS9')")
    return m.group(1), int(m.group(2))


def _it(grade: int, i: int) -> int:
    if grade not in IT:
        raise ValueError(f"tolerance grade IT{grade} not supported (available: IT5-IT11)")
    return IT[grade][i]


def _js_half(it: int) -> float:
    # ISO 286-1: for IT7-IT11 an odd IT value is replaced by the next lower even value.
    return float(it // 2) if it % 2 else it / 2


def deviations(nominal: float, tolerance: str) -> tuple[int | float, int | float]:
    """Return (lower, upper) deviation in micrometres for e.g. 'H7' or 'k6' at `nominal` mm."""
    letter, grade = _parse(tolerance)
    i = _range_index(nominal)
    it = _it(grade, i)
    if letter in ("js", "JS"):
        half = _js_half(it) if grade >= 7 else it / 2
        return -half, half
    if letter.islower():
        if letter in SHAFT_ES:
            es = SHAFT_ES[letter][i]
            return es - it, es
        if letter in SHAFT_EI:
            ei = SHAFT_EI[letter][i]
            if letter == "k" and not 4 <= grade <= 7:
                ei = 0
            return ei, ei + it
    else:
        low = letter.lower()
        if low in SHAFT_ES:
            ei = -SHAFT_ES[low][i]
            return ei, ei + it
        if letter in HOLE_MAX_GRADE:
            if grade > HOLE_MAX_GRADE[letter]:
                raise ValueError(f"{letter}{grade} not supported (up to {letter}{HOLE_MAX_GRADE[letter]})")
            delta = 0 if i == 0 else it - _it(grade - 1, i)
            es = -SHAFT_EI[low][i] + delta
            return es - it, es
    raise ValueError(f"tolerance letter {letter!r} not supported "
                     f"(holes: D E F G H JS K M N P, shafts: d e f g h js k m n p)")


def limits(nominal: float, tolerance: str) -> dict:
    """Limit deviations (µm) and limit sizes (mm) of one tolerance class."""
    lower, upper = deviations(nominal, tolerance)
    return {
        "tolerance": tolerance.strip(),
        "nominal": nominal,
        "lower_um": lower,
        "upper_um": upper,
        "min_mm": round(nominal + lower / 1000, 4),
        "max_mm": round(nominal + upper / 1000, 4),
    }


def fit(nominal: float, fit_spec: str) -> dict:
    """Evaluate a hole/shaft fit such as 'H7/k6': limits and clearance range (negative = interference)."""
    parts = [p.strip() for p in (fit_spec or "").split("/")]
    if len(parts) != 2 or not parts[0][:1].isupper() or not parts[1][:1].islower():
        raise ValueError(f"invalid fit {fit_spec!r} (hole/shaft, e.g. 'H7/k6')")
    hole, shaft = limits(nominal, parts[0]), limits(nominal, parts[1])
    max_cl = hole["upper_um"] - shaft["lower_um"]
    min_cl = hole["lower_um"] - shaft["upper_um"]
    kind = "clearance" if min_cl >= 0 else ("interference" if max_cl <= 0 else "transition")
    return {
        "fit": f"{parts[0]}/{parts[1]}",
        "nominal": nominal,
        "hole": hole,
        "shaft": shaft,
        "max_clearance_um": max_cl,
        "min_clearance_um": min_cl,
        "kind": kind,
    }
