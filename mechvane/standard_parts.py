"""Procedural standard parts generator for Mechvane.

Generates standard parts as standalone Mechvane part documents (.solidcraft) using named
parameters (parameters.add) and sketches/features that obey Mechvane's sketch ownership rule.
Threads are modeled at nominal diameter d with a cosmetic ThreadFeature."""

import math
from pathlib import Path

from . import sketch_rule
from .documents import PART

# ISO 4762 (DIN EN ISO 4762, formerly DIN 912): Hexagon socket head cap screws, product grade A.
# Coarse thread pitch P per ISO 261 / ISO 724.
# Dimensions in mm: d (thread nominal), P (pitch), dk (head diameter max), k (head height max),
# s (socket across flats nom), t (socket depth min), b_ref (reference thread length 2*d + 12).
# Preferred commercial lengths per size from ISO 4762 Table 2.
ISO_4762 = {
    "M2.5": {"d": 2.5, "P": 0.45, "dk": 4.5, "k": 2.5, "s": 2.0, "t": 1.1, "b_ref": 17.0,
             "preferred_lengths": (4, 5, 6, 8, 10, 12, 16, 20, 25)},
    "M3":   {"d": 3.0, "P": 0.50, "dk": 5.5, "k": 3.0, "s": 2.5, "t": 1.3, "b_ref": 18.0,
             "preferred_lengths": (5, 6, 8, 10, 12, 16, 20, 25, 30)},
    "M4":   {"d": 4.0, "P": 0.70, "dk": 7.0, "k": 4.0, "s": 3.0, "t": 2.0, "b_ref": 20.0,
             "preferred_lengths": (6, 8, 10, 12, 16, 20, 25, 30, 35, 40)},
    "M5":   {"d": 5.0, "P": 0.80, "dk": 8.5, "k": 5.0, "s": 4.0, "t": 2.5, "b_ref": 22.0,
             "preferred_lengths": (8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50)},
    "M6":   {"d": 6.0, "P": 1.00, "dk": 10.0, "k": 6.0, "s": 5.0, "t": 3.0, "b_ref": 24.0,
             "preferred_lengths": (10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60)},
    "M8":   {"d": 8.0, "P": 1.25, "dk": 13.0, "k": 8.0, "s": 6.0, "t": 4.0, "b_ref": 28.0,
             "preferred_lengths": (12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80)},
    "M10":  {"d": 10.0, "P": 1.50, "dk": 16.0, "k": 10.0, "s": 8.0, "t": 5.0, "b_ref": 32.0,
             "preferred_lengths": (16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100)},
    "M12":  {"d": 12.0, "P": 1.75, "dk": 18.0, "k": 12.0, "s": 10.0, "t": 6.0, "b_ref": 36.0,
             "preferred_lengths": (20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120)},
}

# ISO 10642 (DIN EN ISO 10642, formerly DIN 7991): Hexagon socket countersunk head screws.
# Dimensions in mm: d (thread nominal), P (pitch), dk (head diameter theoretical max),
# k (head height max), s (socket width across flats nom), t (socket depth min),
# b_ref (reference thread length).
# Verified against Westfield Fasteners (https://www.westfieldfasteners.co.uk/Standards/ScrewBolt-SHCsk-M.pdf)
# and Reyher TI 2019 (https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf).
ISO_10642 = {
    "M3":   {"d": 3.0,  "P": 0.50, "dk": 6.72,  "k": 1.86, "s": 2.0, "t": 1.1, "b_ref": 18.0,
             "preferred_lengths": (6, 8, 10, 12, 16, 20, 25, 30)},
    "M4":   {"d": 4.0,  "P": 0.70, "dk": 8.96,  "k": 2.48, "s": 2.5, "t": 1.5, "b_ref": 20.0,
             "preferred_lengths": (8, 10, 12, 16, 20, 25, 30, 35, 40)},
    "M5":   {"d": 5.0,  "P": 0.80, "dk": 11.20, "k": 3.10, "s": 3.0, "t": 1.9, "b_ref": 22.0,
             "preferred_lengths": (8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50)},
    "M6":   {"d": 6.0,  "P": 1.00, "dk": 13.44, "k": 3.72, "s": 4.0, "t": 2.2, "b_ref": 24.0,
             "preferred_lengths": (10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60)},
    "M8":   {"d": 8.0,  "P": 1.25, "dk": 17.92, "k": 4.96, "s": 5.0, "t": 3.0, "b_ref": 28.0,
             "preferred_lengths": (12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80)},
    "M10":  {"d": 10.0, "P": 1.50, "dk": 22.40, "k": 6.20, "s": 6.0, "t": 3.6, "b_ref": 32.0,
             "preferred_lengths": (16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100)},
    "M12":  {"d": 12.0, "P": 1.75, "dk": 26.88, "k": 7.44, "s": 8.0, "t": 4.3, "b_ref": 36.0,
             "preferred_lengths": (20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120)},
}

# ISO 4017 (DIN EN ISO 4017, supersedes DIN 933): Hexagon head screws, fully threaded, product grade A.
# Coarse thread pitch P per ISO 261 / ISO 724.
# Dimensions in mm: d (thread nominal), P (pitch), s (width across flats nom=max),
# k (head height nom), e (width across corners min, product grade A).
# Verified against Westfield Fasteners (https://www.westfieldfasteners.co.uk/Standards/ScrewBolt-HexHd4017-M-THRfull.pdf)
# and Fasten.it (https://www.fasten.it/en/norms/norm/din_en_iso_4017).
ISO_4017 = {
    "M3":  {"d": 3.0,  "P": 0.50, "s": 5.5,  "k": 2.0, "e": 6.01,
            "preferred_lengths": (5, 6, 8, 10, 12, 16, 20, 25, 30)},
    "M4":  {"d": 4.0,  "P": 0.70, "s": 7.0,  "k": 2.8, "e": 7.66,
            "preferred_lengths": (6, 8, 10, 12, 16, 20, 25, 30, 35, 40)},
    "M5":  {"d": 5.0,  "P": 0.80, "s": 8.0,  "k": 3.5, "e": 8.79,
            "preferred_lengths": (8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50)},
    "M6":  {"d": 6.0,  "P": 1.00, "s": 10.0, "k": 4.0, "e": 11.05,
            "preferred_lengths": (10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60)},
    "M8":  {"d": 8.0,  "P": 1.25, "s": 13.0, "k": 5.3, "e": 14.38,
            "preferred_lengths": (12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80)},
    "M10": {"d": 10.0, "P": 1.50, "s": 16.0, "k": 6.4, "e": 17.77,
            "preferred_lengths": (16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100)},
}

# ISO 4032 (DIN EN ISO 4032, supersedes DIN 934): Hexagon regular nuts, style 1, product grades A/B.
# Coarse thread pitch P per ISO 261 / ISO 724.
# Dimensions in mm: d (thread nominal), P (pitch), s (width across flats max), m (nut height max).
ISO_4032 = {
    "M2.5": {"d": 2.5, "P": 0.45, "s": 5.0, "m": 2.0},
    "M3":   {"d": 3.0, "P": 0.50, "s": 5.5, "m": 2.4},
    "M4":   {"d": 4.0, "P": 0.70, "s": 7.0, "m": 3.2},
    "M5":   {"d": 5.0, "P": 0.80, "s": 8.0, "m": 4.7},
    "M6":   {"d": 6.0, "P": 1.00, "s": 10.0, "m": 5.2},
    "M8":   {"d": 8.0, "P": 1.25, "s": 13.0, "m": 6.8},
    "M10":  {"d": 10.0, "P": 1.50, "s": 16.0, "m": 8.4},
    "M12":  {"d": 12.0, "P": 1.75, "s": 18.0, "m": 10.8},
}

# ISO 7089 (DIN EN ISO 7089, supersedes DIN 125-1): Plain washers, normal series, product grade A, 200 HV.
# Dimensions in mm: d (nominal thread size), d1 (clearance hole diameter min/nom),
# d2 (outside diameter max/nom), h (nominal thickness).
ISO_7089 = {
    "M2.5": {"d": 2.5, "d1": 2.7, "d2": 6.0, "h": 0.5},
    "M3":   {"d": 3.0, "d1": 3.2, "d2": 7.0, "h": 0.5},
    "M4":   {"d": 4.0, "d1": 4.3, "d2": 9.0, "h": 0.8},
    "M5":   {"d": 5.0, "d1": 5.3, "d2": 10.0, "h": 1.0},
    "M6":   {"d": 6.0, "d1": 6.4, "d2": 12.0, "h": 1.6},
    "M8":   {"d": 8.0, "d1": 8.4, "d2": 16.0, "h": 1.6},
    "M10":  {"d": 10.0, "d1": 10.5, "d2": 20.0, "h": 2.0},
    "M12":  {"d": 12.0, "d1": 13.0, "d2": 24.0, "h": 2.5},
}

# Heat-set threaded inserts for 3D printing: Ruthex / CNC Kitchen standard metric brass inserts.
# Source: ruthex GmbH datasheet RX series (checked 2026-10-20, https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf):
# d1, L and hole d3 as listed; minimum hole depth L + 1 mm per the drawing.
# Dimensions in mm: d (thread nominal), P (pitch), D (outer diameter D1 over knurls),
# L (insert length), d_hole (recommended mounting hole diameter), min_depth (minimum hole depth L + 1).
RUTHEX_INSERTS = {
    "M2.5": {"code": "RX-M2.5x5.7", "d": 2.5, "P": 0.45, "D": 4.6, "L": 5.7, "d_hole": 4.0, "min_depth": 6.7},
    "M3":   {"code": "RX-M3x5.7",   "d": 3.0, "P": 0.50, "D": 4.6, "L": 5.7, "d_hole": 4.0, "min_depth": 6.7},
    "M4":   {"code": "RX-M4x8.1",   "d": 4.0, "P": 0.70, "D": 6.3, "L": 8.1, "d_hole": 5.6, "min_depth": 9.1},
    "M5":   {"code": "RX-M5x9.5",   "d": 5.0, "P": 0.80, "D": 7.1, "L": 9.5, "d_hole": 6.4, "min_depth": 10.5},
}

# Single-row deep groove ball bearings (miniature series 62 and series 60, ISO 15 / DIN 625-1).
# Dimensions in mm: d (bore diameter), D (outer diameter), B (width), r (minimum chamfer r1,2).
# Sources: SKF online catalog (checked 2026-10-23):
# 623: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-623
# 624: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-624
# 625: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-625
# 626: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-626
# 627: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-627
# 608: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-608
# 609: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-609
# 6000: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6000
# 6001: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6001
# 6002: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6002
# 6003: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6003
# 6004: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6004
# 6005: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-6005
BEARINGS_6000 = {
    "623":  {"d": 3.0, "D": 10.0, "B": 4.0, "r": 0.15},
    "624":  {"d": 4.0, "D": 13.0, "B": 5.0, "r": 0.2},
    "625":  {"d": 5.0, "D": 16.0, "B": 5.0, "r": 0.3},
    "626":  {"d": 6.0, "D": 19.0, "B": 6.0, "r": 0.3},
    "627":  {"d": 7.0, "D": 22.0, "B": 7.0, "r": 0.3},
    "608":  {"d": 8.0, "D": 22.0, "B": 7.0, "r": 0.3},
    "609":  {"d": 9.0, "D": 24.0, "B": 7.0, "r": 0.3},
    "6000": {"d": 10.0, "D": 26.0, "B": 8.0, "r": 0.3},
    "6001": {"d": 12.0, "D": 28.0, "B": 8.0, "r": 0.3},
    "6002": {"d": 15.0, "D": 32.0, "B": 9.0, "r": 0.3},
    "6003": {"d": 17.0, "D": 35.0, "B": 10.0, "r": 0.3},
    "6004": {"d": 20.0, "D": 42.0, "B": 12.0, "r": 0.6},
    "6005": {"d": 25.0, "D": 47.0, "B": 12.0, "r": 0.6},
}

NORMS = {
    "ISO 4762": {
        "name": "Hexagon socket head cap screw (Zylinderschraube mit Innensechskant)",
        "aliases": ("iso 4762", "iso4762", "din 912", "din912", "shcs", "socket_head_cap_screw"),
        "table": ISO_4762,
        "has_length": True,
    },
    "ISO 10642": {
        "name": "Hexagon socket countersunk head screw (Senkschraube mit Innensechskant)",
        "aliases": ("iso 10642", "iso10642", "din 7991", "din7991", "countersunk", "senkschraube"),
        "table": ISO_10642,
        "has_length": True,
    },
    "ISO 4017": {
        "name": "Hexagon head screw, fully threaded (Sechskantschraube mit Gewinde bis Kopf)",
        "aliases": ("iso 4017", "iso4017", "din 933", "din933", "hex_screw", "hex_bolt", "sechskantschraube"),
        "table": ISO_4017,
        "has_length": True,
    },
    "ISO 4032": {
        "name": "Hexagon regular nut, style 1 (Sechskantmutter Typ 1)",
        "aliases": ("iso 4032", "iso4032", "din 934", "din934", "hex_nut", "nut"),
        "table": ISO_4032,
        "has_length": False,
    },
    "ISO 7089": {
        "name": "Plain washer, normal series, 200 HV (Scheibe, normale Reihe)",
        "aliases": ("iso 7089", "iso7089", "din 125", "din125", "washer"),
        "table": ISO_7089,
        "has_length": False,
    },
    "Ruthex": {
        "name": "Heat-set threaded insert for 3D printing (Gewindeeinsatz zum Einschmelzen)",
        "aliases": ("ruthex", "heat_insert", "heat_set_insert", "insert", "gewindeeinsatz", "einschmelzgewinde"),
        "table": RUTHEX_INSERTS,
        "has_length": False,
    },
    "DIN 625": {
        "name": "Deep groove ball bearing, 6000 series (Rillenkugellager 6000er-Reihe, ISO 15)",
        "aliases": ("din 625", "din625", "din 625-1", "iso 15", "iso15", "6000", "bearing", "kugellager"),
        "table": BEARINGS_6000,
        "has_length": False,
    },
}


def _fmt_num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:g}"


def resolve_norm(norm: str) -> str:
    """Return the canonical norm key for `norm` (or an alias), or raise ValueError."""
    key = (norm or "").strip().lower().replace("-", " ").replace("_", " ")
    compact = key.replace(" ", "")
    for canon, info in NORMS.items():
        aliases = {a.replace("-", " ").replace("_", " ") for a in info["aliases"]}
        compacts = {a.replace(" ", "") for a in aliases}
        if key in aliases or compact in compacts or key == canon.lower():
            return canon
    avail = ", ".join(NORMS)
    raise ValueError(f"unknown standard {norm!r} (available: {avail})")


def _normalize_size(canon: str, size: str, length: float | None):
    raw = (size or "").strip().replace(",", ".")
    if canon == "DIN 625":
        s = raw.upper().removeprefix("DIN 625").removeprefix("ISO 15").strip()
        if s not in BEARINGS_6000:
            raise ValueError(f"unknown bearing size {size!r} for {canon} (available: {', '.join(BEARINGS_6000)})")
        if length is not None:
            raise ValueError(f"{canon} bearings have fixed width B and do not take a length")
        return s, None

    s = raw.upper()
    if s.startswith("RX-"):
        s = s[3:]
    if "X" in s:
        head, tail = s.split("X", 1)
        s = head.strip()
        try:
            parsed_len = float(tail.strip())
        except ValueError as e:
            raise ValueError(f"invalid size/length specification {size!r}") from e
        if length is None:
            length = parsed_len
        elif abs(float(length) - parsed_len) > 1e-6:
            raise ValueError(f"conflicting lengths in size {size!r} and length={length}")
    if not s.startswith("M"):
        s = "M" + s
    try:
        s = f"M{_fmt_num(float(s[1:]))}"
    except ValueError:
        pass

    table = NORMS[canon]["table"]
    if s not in table:
        raise ValueError(f"unknown size {size!r} for {canon} (available: {', '.join(table)})")

    if canon in ("ISO 4762", "ISO 10642", "ISO 4017"):
        if length is None or not isinstance(length, (int, float)) or not math.isfinite(length) or length <= 0:
            raise ValueError(f"{canon} requires a positive length in mm")
        return s, float(length)

    if canon == "Ruthex" and length is not None:
        if abs(float(length) - table[s]["L"]) > 1e-6:
            raise ValueError(f"Ruthex {s} has fixed length L = {table[s]['L']} mm")
        return s, None

    if length is not None:
        raise ValueError(f"{canon} has fixed table dimensions and does not take a length")
    return s, None


def _param(name: str, val_mm: float, comment: str = "") -> dict:
    p = {"name": name, "expression": f"{_fmt_num(val_mm)} mm"}
    if comment:
        p["comment"] = comment
    return {"command": "parameters.add", "params": p}


def _circle_extrude(sketch_name: str, feat_name: str, r_init: float, diam_expr: str, dist_expr: str,
                    op: str = "new", direction: str = "positive", body_name: str | None = None) -> list[dict]:
    ext = {"sketch": sketch_name, "distance": dist_expr, "direction": direction, "operation": op, "name": feat_name}
    if body_name:
        ext["body_name"] = body_name
    return [
        {"command": "sketch.create", "params": {"plane": "XY", "name": sketch_name}},
        {"command": "sketch.draw.dimensioned", "params": {
            "command": "sketch.circle.center",
            "params": {"center": [0, 0], "radius": r_init},
            "dimensions": {"diameter": diam_expr},
        }},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": ext},
    ]


def _hex_extrude(sketch_name: str, feat_name: str, r_init: float, rad_expr: str, dist_expr: str,
                 plane_offset: str | None = None, op: str = "new", direction: str = "positive",
                 body_name: str | None = None) -> list[dict]:
    sk_params = {"plane": "XY", "name": sketch_name}
    if plane_offset is not None:
        sk_params["offset"] = plane_offset
    ext = {"sketch": sketch_name, "distance": dist_expr, "direction": direction, "operation": op, "name": feat_name}
    if body_name:
        ext["body_name"] = body_name
    return [
        {"command": "sketch.create", "params": sk_params},
        {"command": "sketch.draw.dimensioned", "params": {
            "command": "sketch.polygon.circumscribed",
            "params": {"center": [0, 0], "radius": r_init, "sides": 6},
            "dimensions": {"radius": rad_expr},
        }},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": ext},
    ]


def spec(norm: str, size: str, length: float | None = None) -> dict:
    """Validate and build the full specification and SolidCraft command list for a standard part."""
    canon = resolve_norm(norm)
    norm_size, norm_len = _normalize_size(canon, size, length)
    row = dict(NORMS[canon]["table"][norm_size])
    warnings = []

    if canon == "ISO 4762":
        d, P, dk, k, s, t = row["d"], row["P"], row["dk"], row["k"], row["s"], row["t"]
        pref = row["preferred_lengths"]
        is_pref = any(abs(norm_len - p) < 1e-6 for p in pref)
        if not is_pref:
            pref_str = ", ".join(_fmt_num(p) for p in pref)
            warnings.append(
                f"length {_fmt_num(norm_len)} mm is not a preferred length for ISO 4762 {norm_size} "
                f"(preferred: {pref_str} mm)"
            )
        designation = f"ISO 4762 {norm_size}x{_fmt_num(norm_len)}"
        dims = {"d": d, "P": P, "dk": dk, "k": k, "s": s, "t": t, "l": norm_len, "b": min(norm_len, row["b_ref"])}
        cmds = [
            _param("d", d, "nominal thread diameter"),
            _param("P", P, "coarse thread pitch"),
            _param("dk", dk, "head diameter"),
            _param("k", k, "head height"),
            _param("s", s, "socket width across flats"),
            _param("t", t, "socket depth"),
            _param("l", norm_len, "nominal screw length"),
            {"command": "parameters.add", "params": {
                "name": "b", "expression": "min(l, 2 * d + 12 mm)", "comment": "thread length"}},
        ]
        cmds += _circle_extrude("HeadSketch", "Head", dk / 2, "dk", "k", op="new", direction="positive", body_name="Screw")
        cmds += _circle_extrude("ShankSketch", "Shank", d / 2, "d", "l", op="join", direction="negative")
        cmds += _hex_extrude("SocketSketch", "Socket", s / 2, "s / 2", "t", plane_offset="k", op="cut", direction="negative")
        cmds.append({"command": "solid.thread", "params": {
            "face": [d / 2, 0, -norm_len / 2],
            "designation": f"{norm_size}x{_fmt_num(P)}",
            "name": "Thread",
        }})
        meta = {
            "norm": canon,
            "size": norm_size,
            "length": norm_len,
            "preferred_length": is_pref,
            "designation": designation,
            "dimensions": dims,
        }
        if warnings:
            meta["warning"] = warnings[0]
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    if canon == "ISO 10642":
        d, P, dk, k, s, t = row["d"], row["P"], row["dk"], row["k"], row["s"], row["t"]
        if norm_len <= k + 1e-4:
            raise ValueError(
                f"screw length {_fmt_num(norm_len)} mm must be greater than head height k = {_fmt_num(k)} mm for ISO 10642 {norm_size}"
            )
        pref = row["preferred_lengths"]
        is_pref = any(abs(norm_len - p) < 1e-6 for p in pref)
        if not is_pref:
            pref_str = ", ".join(_fmt_num(p) for p in pref)
            warnings.append(
                f"length {_fmt_num(norm_len)} mm is not a preferred length for ISO 10642 {norm_size} "
                f"(preferred: {pref_str} mm)"
            )
        designation = f"ISO 10642 {norm_size}x{_fmt_num(norm_len)}"
        dims = {"d": d, "P": P, "dk": dk, "k": k, "s": s, "t": t, "l": norm_len, "b": min(norm_len, row["b_ref"])}
        cmds = [
            _param("d", d, "nominal thread diameter"),
            _param("P", P, "coarse thread pitch"),
            _param("dk", dk, "head diameter"),
            _param("k", k, "head height"),
            _param("s", s, "socket width across flats"),
            _param("t", t, "socket depth"),
            _param("l", norm_len, "nominal screw length"),
            {"command": "parameters.add", "params": {
                "name": "b", "expression": "min(l, 2 * d + 12 mm)", "comment": "thread length"}},
            # Head: 90 deg conical head per revolve on XZ plane from z=0 (dk) to z=-k (d)
            {"command": "sketch.create", "params": {"plane": "XZ", "name": "HeadSketch"}},
            {"command": "sketch.line", "params": {
                "points": [[0, 0], ["dk / 2", 0], ["d / 2", "k"], [0, "k"]],
                "closed": True,
            }},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.revolve", "params": {
                "sketch": "HeadSketch", "axis": "Z", "operation": "new", "body_name": "Screw", "name": "Head",
            }},
        ]
        # Shank: cylindrical shank from z=-k downwards by l - k
        cmds += [
            {"command": "sketch.create", "params": {"plane": "XY", "offset": "-k", "name": "ShankSketch"}},
            {"command": "sketch.draw.dimensioned", "params": {
                "command": "sketch.circle.center",
                "params": {"center": [0, 0], "radius": d / 2},
                "dimensions": {"diameter": "d"},
            }},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {
                "sketch": "ShankSketch", "distance": "l - k", "operation": "join", "direction": "negative", "name": "Shank",
            }},
        ]
        # Hex socket: hexagonal cut from top face z=0 downwards by t
        cmds += [
            {"command": "sketch.create", "params": {"plane": "XY", "offset": "0 mm", "name": "SocketSketch"}},
            {"command": "sketch.draw.dimensioned", "params": {
                "command": "sketch.polygon.circumscribed",
                "params": {"center": [0, 0], "radius": s / 2, "sides": 6},
                "dimensions": {"radius": "s / 2"},
            }},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {
                "sketch": "SocketSketch", "distance": "t", "operation": "cut", "direction": "negative", "name": "Socket",
            }},
        ]
        cmds.append({"command": "solid.thread", "params": {
            "face": [d / 2, 0, -(k + (norm_len - k) / 2)],
            "designation": f"{norm_size}x{_fmt_num(P)}",
            "name": "Thread",
        }})
        meta = {
            "norm": canon,
            "size": norm_size,
            "length": norm_len,
            "preferred_length": is_pref,
            "designation": designation,
            "dimensions": dims,
        }
        if warnings:
            meta["warning"] = warnings[0]
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    if canon == "ISO 4017":
        d, P, s, k, e = row["d"], row["P"], row["s"], row["k"], row["e"]
        pref = row["preferred_lengths"]
        is_pref = any(abs(norm_len - p) < 1e-6 for p in pref)
        if not is_pref:
            pref_str = ", ".join(_fmt_num(p) for p in pref)
            warnings.append(
                f"length {_fmt_num(norm_len)} mm is not a preferred length for ISO 4017 {norm_size} "
                f"(preferred: {pref_str} mm)"
            )
        designation = f"ISO 4017 {norm_size}x{_fmt_num(norm_len)}"
        dims = {"d": d, "P": P, "s": s, "k": k, "e": e, "l": norm_len}
        cmds = [
            _param("d", d, "nominal thread diameter"),
            _param("P", P, "coarse thread pitch"),
            _param("s", s, "width across flats"),
            _param("k", k, "head height"),
            _param("e", e, "width across corners"),
            _param("l", norm_len, "nominal screw length"),
        ]
        cmds += _hex_extrude("HeadSketch", "Head", s / 2, "s / 2", "k", op="new", direction="positive", body_name="Screw")
        cmds += _circle_extrude("ShankSketch", "Shank", d / 2, "d", "l", op="join", direction="negative")
        cmds.append({"command": "solid.thread", "params": {
            "face": [d / 2, 0, -norm_len / 2],
            "designation": f"{norm_size}x{_fmt_num(P)}",
            "name": "Thread",
        }})
        meta = {
            "norm": canon,
            "size": norm_size,
            "length": norm_len,
            "preferred_length": is_pref,
            "designation": designation,
            "dimensions": dims,
        }
        if warnings:
            meta["warning"] = warnings[0]
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    if canon == "ISO 4032":
        d, P, s, m = row["d"], row["P"], row["s"], row["m"]
        designation = f"ISO 4032 {norm_size}"
        dims = {"d": d, "P": P, "s": s, "m": m}
        cmds = [
            _param("d", d, "nominal thread diameter"),
            _param("P", P, "coarse thread pitch"),
            _param("s", s, "width across flats"),
            _param("m_nut", m, "nut height m (ISO 4032); 'm' is reserved for meter in SolidCraft"),
        ]
        cmds += _hex_extrude("HexSketch", "HexBody", s / 2, "s / 2", "m_nut", op="new", body_name="Nut")
        cmds += _circle_extrude("BoreSketch", "Bore", d / 2, "d", "m_nut", op="cut")
        cmds.append({"command": "solid.thread", "params": {
            "face": [d / 2, 0, m / 2],
            "designation": f"{norm_size}x{_fmt_num(P)}",
            "name": "Thread",
        }})
        meta = {"norm": canon, "size": norm_size, "designation": designation, "dimensions": dims}
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    if canon == "ISO 7089":
        d, d1, d2, h = row["d"], row["d1"], row["d2"], row["h"]
        designation = f"ISO 7089 {norm_size}"
        dims = {"d": d, "d1": d1, "d2": d2, "h": h}
        cmds = [
            _param("d1", d1, "clearance hole diameter"),
            _param("d2", d2, "outer diameter"),
            _param("h", h, "washer thickness"),
        ]
        cmds += _circle_extrude("OuterSketch", "Disk", d2 / 2, "d2", "h", op="new", body_name="Washer")
        cmds += _circle_extrude("BoreSketch", "Bore", d1 / 2, "d1", "h", op="cut")
        meta = {"norm": canon, "size": norm_size, "designation": designation, "dimensions": dims}
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    if canon == "Ruthex":
        d, P, D, L = row["d"], row["P"], row["D"], row["L"]
        d_hole, min_depth = row["d_hole"], row["min_depth"]
        designation = f"Ruthex {row['code']}"
        dims = {"d": d, "P": P, "D": D, "L": L}
        hole = {"diameter": d_hole, "min_depth": min_depth}
        cmds = [
            _param("d", d, "nominal internal thread diameter"),
            _param("P", P, "coarse thread pitch"),
            _param("D", D, "outer diameter over knurls"),
            _param("L", L, "insert length"),
            _param("d_hole", d_hole, "recommended mounting hole diameter in 3D print"),
        ]
        cmds += _circle_extrude("OuterSketch", "Sleeve", D / 2, "D", "L", op="new", body_name="Insert")
        cmds += _circle_extrude("BoreSketch", "Bore", d / 2, "d", "L", op="cut")
        cmds.append({"command": "solid.thread", "params": {
            "face": [d / 2, 0, L / 2],
            "designation": f"{norm_size}x{_fmt_num(P)}",
            "name": "Thread",
        }})
        meta = {
            "norm": canon,
            "size": norm_size,
            "designation": designation,
            "dimensions": dims,
            "mounting_hole": hole,
        }
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    if canon == "DIN 625":
        d, D, B = row["d"], row["D"], row["B"]
        r = row.get("r")
        designation = f"DIN 625 {norm_size}"
        dims = {"d": d, "D": D, "B": B}
        if r is not None:
            dims["r"] = r
        cmds = [
            _param("d", d, "bore diameter"),
            _param("D", D, "outer diameter"),
            _param("B", B, "bearing width"),
        ]
        if r is not None:
            cmds.append(_param("r", r, "minimum chamfer dimension"))
        cmds += _circle_extrude("OuterSketch", "Ring", D / 2, "D", "B", op="new", body_name="Bearing")
        cmds += _circle_extrude("BoreSketch", "Bore", d / 2, "d", "B", op="cut")
        meta = {"norm": canon, "size": norm_size, "designation": designation, "dimensions": dims}
        return {"standard": meta, "commands": cmds, "warnings": warnings}

    raise ValueError(f"unsupported standard {canon!r}")


def expected_volume(norm: str, size: str, length: float | None = None) -> float:
    """Analytical volume (mm³) computed from the standard table dimensions."""
    st = spec(norm, size, length)["standard"]
    canon = st["norm"]
    dims = st["dimensions"]
    if canon == "ISO 4762":
        head = math.pi * (dims["dk"] / 2) ** 2 * dims["k"]
        shank = math.pi * (dims["d"] / 2) ** 2 * dims["l"]
        socket = (math.sqrt(3) / 2) * dims["s"] ** 2 * dims["t"]
        return head + shank - socket
    if canon == "ISO 10642":
        R = dims["dk"] / 2
        r = dims["d"] / 2
        head = (math.pi * dims["k"] / 3.0) * (R**2 + R * r + r**2)
        shank = math.pi * r**2 * (dims["l"] - dims["k"])
        socket = (math.sqrt(3) / 2) * dims["s"] ** 2 * dims["t"]
        return head + shank - socket
    if canon == "ISO 4017":
        head = (math.sqrt(3) / 2) * dims["s"] ** 2 * dims["k"]
        shank = math.pi * (dims["d"] / 2) ** 2 * dims["l"]
        return head + shank
    if canon == "ISO 4032":
        hex_area = (math.sqrt(3) / 2) * dims["s"] ** 2
        bore_area = math.pi * (dims["d"] / 2) ** 2
        return (hex_area - bore_area) * dims["m"]
    if canon == "ISO 7089":
        return math.pi * ((dims["d2"] / 2) ** 2 - (dims["d1"] / 2) ** 2) * dims["h"]
    if canon == "Ruthex":
        return math.pi * ((dims["D"] / 2) ** 2 - (dims["d"] / 2) ** 2) * dims["L"]
    if canon == "DIN 625":
        return math.pi * ((dims["D"] / 2) ** 2 - (dims["d"] / 2) ** 2) * dims["B"]
    raise ValueError(canon)


def expected_bbox(norm: str, size: str, length: float | None = None) -> list[list[float]]:
    """Analytical bounding box [[xmin, ymin, zmin], [xmax, ymax, zmax]] (mm)."""
    st = spec(norm, size, length)["standard"]
    canon = st["norm"]
    dims = st["dimensions"]
    if canon == "ISO 4762":
        r = dims["dk"] / 2
        return [[-r, -r, -dims["l"]], [r, r, dims["k"]]]
    if canon == "ISO 10642":
        r = dims["dk"] / 2
        return [[-r, -r, -dims["l"]], [r, r, 0.0]]
    if canon == "ISO 4017":
        rx = dims["s"] / math.sqrt(3)
        ry = dims["s"] / 2
        return [[-rx, -ry, -dims["l"]], [rx, ry, dims["k"]]]
    if canon == "ISO 4032":
        rx = dims["s"] / math.sqrt(3)
        ry = dims["s"] / 2
        return [[-rx, -ry, 0.0], [rx, ry, dims["m"]]]
    if canon == "ISO 7089":
        r = dims["d2"] / 2
        return [[-r, -r, 0.0], [r, r, dims["h"]]]
    if canon == "Ruthex":
        r = dims["D"] / 2
        return [[-r, -r, 0.0], [r, r, dims["L"]]]
    if canon == "DIN 625":
        r = dims["D"] / 2
        return [[-r, -r, 0.0], [r, r, dims["B"]]]
    raise ValueError(canon)


def create(ws, norm: str, size: str, length: float | None = None,
           name: str | None = None, path: str | None = None,
           overwrite: bool = False) -> dict:
    """Create, parameterize, save and keep open a standard part document in `ws`."""
    sp = spec(norm, size, length)
    std_meta = sp["standard"]
    doc_name = name or (Path(path).stem if path else std_meta["designation"].replace(" ", "_"))
    doc = ws.new(PART, doc_name, path, overwrite=overwrite)
    try:
        doc.session.batch(sp["commands"])
        sr = sketch_rule.enforce(doc.session)
        doc.set_metadata({"kind": PART, "format": 1, "standard": std_meta})
        doc.save()
    except Exception:
        ws.close(doc_name)
        raise
    out = dict(doc.info(), standard=std_meta, sketch_rule=sr)
    if sp["warnings"]:
        out["warnings"] = sp["warnings"]
    return out


def catalog(norm: str | None = None) -> dict:
    """List supported standard part norms, or the full dimension table for one norm."""
    if norm is None:
        return {
            "norms": [
                {
                    "norm": canon,
                    "name": info["name"],
                    "aliases": list(info["aliases"]),
                    "sizes": list(info["table"].keys()),
                    "has_length": info["has_length"],
                }
                for canon, info in NORMS.items()
            ]
        }
    canon = resolve_norm(norm)
    info = NORMS[canon]
    sizes = {}
    for sz, row in info["table"].items():
        entry = dict(row)
        if "preferred_lengths" in entry:
            entry["preferred_lengths"] = list(entry["preferred_lengths"])
        sizes[sz] = entry
    return {
        "norm": canon,
        "name": info["name"],
        "aliases": list(info["aliases"]),
        "has_length": info["has_length"],
        "sizes": sizes,
    }
