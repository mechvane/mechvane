"""Standard hole and thread dimension tables for Mechvane.

Contains standardized engineering tables and selection logic for:
- ISO 273 clearance hole diameters (fine, medium/normal, coarse/loose)
- DIN 336 / ISO 261 tap drill hole diameters for metric coarse threads
- DIN 974-1 counterbores for ISO 4762 hexagon socket head cap screws (Form N / without washer,
  and adapted with ISO 7089 washer)
- Preferred screw length selection logic based on ISO 4762 preferred series
- Minimum thread engagement depths by material (Bossard table for 8.8, see below)
- Thread runout according to DIN 76-1 and 118 deg drill point depths
"""

import math
import re
from . import standard_parts

# ISO 273:1979 / DIN EN ISO 273:1991: Clearance holes for metric bolts and screws.
# Diameters in mm for series: fine (Reihe 1), medium/normal (Reihe 2), coarse/loose (Reihe 3).
ISO_273 = {
    "M2.5": {"fine": 2.7, "medium": 2.9, "coarse": 3.1},
    "M3":   {"fine": 3.2, "medium": 3.4, "coarse": 3.6},
    "M4":   {"fine": 4.3, "medium": 4.5, "coarse": 4.8},
    "M5":   {"fine": 5.3, "medium": 5.5, "coarse": 5.8},
    "M6":   {"fine": 6.4, "medium": 6.6, "coarse": 7.0},
    "M8":   {"fine": 8.4, "medium": 9.0, "coarse": 10.0},
    "M10":  {"fine": 10.5, "medium": 11.0, "coarse": 12.0},
    "M12":  {"fine": 13.0, "medium": 13.5, "coarse": 14.5},
}

# DIN 336-1:1969-07 / DIN ISO 261: Tap drill hole diameters for metric coarse threads (Regelgewinde).
# Theoretical drill diameter d_drill approx d - P.
DIN_336 = {
    "M2.5": {"pitch": 0.45, "drill": 2.05},
    "M3":   {"pitch": 0.50, "drill": 2.50},
    "M4":   {"pitch": 0.70, "drill": 3.30},
    "M5":   {"pitch": 0.80, "drill": 4.20},
    "M6":   {"pitch": 1.00, "drill": 5.00},
    "M8":   {"pitch": 1.25, "drill": 6.80},
    "M10":  {"pitch": 1.50, "drill": 8.50},
    "M12":  {"pitch": 1.75, "drill": 10.20},
}

# DIN 974-1:2008-02: Counterbores for hexagon socket head cap screws (ISO 4762 / DIN 912).
#
# Series 1 (Form N, without washer under head):
# Counterbore diameter d1 (H13) and depth t1 = k_max + Z (where allowance Z = 0.4 mm for d <= 6,
# Z = 0.6 mm for d > 6).
# Checked 2026-10-20 (without washer, M4-M12): Buehler works standard sheet citing DIN 974-1
# (https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628): t1 = 4.4 / 5.4 / 6.4 / 8.6 /
# 10.6 / 12.6 mm, d1 = 8 / 10 / 11 / 15 / 18 / 20 mm. M3 (6.5 x 3.4) from table site
# (https://www.neue-physik.de/353.9_Senkungen.php). M2.5 d1 = 5.5 mm per Ifanger counterbore catalogue.
# The 5.7 mm for M5 found in some textbooks is not the DIN 974-1 value.
#
# Series 5 (with ISO 7089 plain washer under head):
# Counterbore diameter d1 (H13) per DIN 974-1:2008-02 Table 1 Reihe 5 (Beuth Tabellenbuch Schrauben, S. 17).
# Counterbore depth t = k_max + h_washer + Z per DIN 974-1:2008-02 Table 2 (allowance Z = 0.4 mm for d <= 6,
# Z = 0.6 mm for d > 6; nominal washer thickness h per ISO 7089).
DIN_974_1 = {
    "M2.5": {
        "without_washer": {"diameter": 5.5,  "depth": 2.9},
        "with_washer":    {"diameter": 7.0,  "depth": 3.4},  # Reihe 5: d1=7.0, t=2.5+0.5+0.4=3.4
    },
    "M3": {
        "without_washer": {"diameter": 6.5,  "depth": 3.4},
        "with_washer":    {"diameter": 9.0,  "depth": 3.9},  # Reihe 5: d1=9.0, t=3.0+0.5+0.4=3.9
    },
    "M4": {
        "without_washer": {"diameter": 8.0,  "depth": 4.4},
        "with_washer":    {"diameter": 10.0, "depth": 5.2},  # Reihe 5: d1=10.0, t=4.0+0.8+0.4=5.2
    },
    "M5": {
        "without_washer": {"diameter": 10.0, "depth": 5.4},
        "with_washer":    {"diameter": 13.0, "depth": 6.4},  # Reihe 5: d1=13.0, t=5.0+1.0+0.4=6.4
    },
    "M6": {
        "without_washer": {"diameter": 11.0, "depth": 6.4},
        "with_washer":    {"diameter": 15.0, "depth": 8.0},  # Reihe 5: d1=15.0, t=6.0+1.6+0.4=8.0
    },
    "M8": {
        "without_washer": {"diameter": 15.0, "depth": 8.6},
        "with_washer":    {"diameter": 18.0, "depth": 10.2}, # Reihe 5: d1=18.0, t=8.0+1.6+0.6=10.2
    },
    "M10": {
        "without_washer": {"diameter": 18.0, "depth": 10.6},
        "with_washer":    {"diameter": 24.0, "depth": 12.6}, # Reihe 5: d1=24.0, t=10.0+2.0+0.6=12.6
    },
    "M12": {
        "without_washer": {"diameter": 20.0, "depth": 12.6},
        "with_washer":    {"diameter": 26.0, "depth": 15.1}, # Reihe 5: d1=26.0, t=12.0+2.5+0.6=15.1
    },
}

# DIN 74 Form F: Countersinks for countersunk head screws DIN 7991 / ISO 10642 (90 deg).
# Not DIN EN ISO 15065, whose diameters are smaller (e.g. M5 10.4 mm).
# Countersink diameter d2 (H13) and nominal countersink depth t.
# Checked 2026-10-23 against Neue Physik (https://www.neue-physik.de/353.9_Senkungen.php)
# and Schraube & Mutter Bohrtabelle (https://schraube-mutter.de/bohrtabelle-fuer-senkschrauben/).
DIN_74_F = {
    "M3":  {"diameter": 6.9,  "angle": 90.0, "depth": 1.8},
    "M4":  {"diameter": 9.2,  "angle": 90.0, "depth": 2.3},
    "M5":  {"diameter": 11.5, "angle": 90.0, "depth": 3.0},
    "M6":  {"diameter": 13.7, "angle": 90.0, "depth": 3.6},
    "M8":  {"diameter": 18.3, "angle": 90.0, "depth": 4.6},
    "M10": {"diameter": 22.7, "angle": 90.0, "depth": 5.9},
    "M12": {"diameter": 27.2, "angle": 90.0, "depth": 6.9},
}

_FIT_MAP = {
    "close": ("close", "fine"),
    "fine": ("close", "fine"),
    "f": ("close", "fine"),
    "normal": ("normal", "medium"),
    "medium": ("normal", "medium"),
    "m": ("normal", "medium"),
    "loose": ("loose", "coarse"),
    "coarse": ("loose", "coarse"),
    "c": ("loose", "coarse"),
}


def normalize_fit(fit: str | None) -> tuple[str, str]:
    """Normalize fit string to (solidcraft_fit, iso273_key). Raises ValueError on unknown fit."""
    raw = (fit or "normal").strip().lower()
    if raw not in _FIT_MAP:
        avail = "close (fine), normal (medium), loose (coarse)"
        hint = "; ISO 286 classes like H7 are for fitted bores, see iso_fit" if re.fullmatch(r"[a-z]{1,2}\d{1,2}", raw) else ""
        raise ValueError(f"unknown fit {fit!r} (available: {avail}){hint}")
    return _FIT_MAP[raw]


def normalize_size(size: str) -> str:
    """Normalize a thread size string (e.g. 'm5', 'M5', '5', '5.0') to canonical 'M5'."""
    raw = (size or "").strip().replace(",", ".").upper()
    if raw.startswith("M"):
        raw = raw[1:].strip()
    try:
        val = float(raw)
        canonical = f"M{int(val)}" if val.is_integer() else f"M{val:g}"
    except ValueError as err:
        raise ValueError(f"invalid thread size specification: {size!r}") from err
    if canonical not in ISO_273:
        avail = ", ".join(ISO_273)
        raise ValueError(f"unsupported thread size {size!r} (available: {avail})")
    return canonical


def clearance_hole(size: str, fit: str = "normal") -> float:
    """Return ISO 273 clearance hole diameter for `size` and `fit` ('close'/'fine', 'normal'/'medium', 'loose'/'coarse')."""
    canon_size = normalize_size(size)
    _, iso_key = normalize_fit(fit)
    return ISO_273[canon_size][iso_key]


def tap_drill(size: str) -> float:
    """Return DIN 336 tap drill hole diameter for metric coarse thread `size`."""
    canon_size = normalize_size(size)
    return DIN_336[canon_size]["drill"]


def counterbore(size: str, with_washer: bool = False) -> dict:
    """Return DIN 974-1 counterbore dimensions {'diameter': float, 'depth': float} for ISO 4762."""
    canon_size = normalize_size(size)
    key = "with_washer" if with_washer else "without_washer"
    return dict(DIN_974_1[canon_size][key])


def countersink(size: str) -> dict:
    """Return DIN 74 Form F 90 deg countersink dimensions {'diameter': float, 'angle': float, 'depth': float}."""
    canon_size = normalize_size(size)
    if canon_size not in DIN_74_F:
        avail = ", ".join(DIN_74_F)
        raise ValueError(f"unsupported thread size {size!r} for countersink (available: {avail})")
    return dict(DIN_74_F[canon_size])


def preferred_screw_length(size: str, req_length: float, norm: str = "ISO 4762") -> float:
    """Select the smallest commercial preferred length >= req_length for `norm` `size`."""
    canon_size = normalize_size(size)
    norm_canon = standard_parts.resolve_norm(norm)
    pref_list = standard_parts.NORMS[norm_canon]["table"][canon_size]["preferred_lengths"]
    for p in pref_list:
        if p >= req_length - 1e-6:
            return float(p)
    max_len = pref_list[-1]
    raise ValueError(
        f"required screw length {req_length:.1f} mm exceeds maximum preferred length "
        f"{max_len} mm for {norm_canon} {canon_size}"
    )


# Minimum thread engagement depths by material group, factor times nominal diameter d, for property
# class 8.8 and coarse thread. Checked 2026-10-20 against the Bossard table where it has a row.
MATERIAL_ENGAGEMENT_DEPTHS = {
    "steel": {
        "factor": 1.0,
        "source": "Bossard, Technische Information Einschraubtiefe 01/2025, Tabelle 8.8 Regelgewinde (https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf): S235, Rm > 360",
        "verified": True,
    },
    "cast_iron": {
        "factor": 1.0,
        "source": "Bossard, Technische Information Einschraubtiefe 01/2025, Tabelle 8.8 Regelgewinde (https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf): GJL 250, Rm > 220",
        "verified": True,
    },
    "alu": {
        "factor": 2.0,
        "source": "Bossard, Technische Information Einschraubtiefe 01/2025, Tabelle 8.8 Regelgewinde (https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf): AlMg3 F18 (softest aluminium row), used when the alloy is unknown",
        "verified": True,
    },
    "alu_cast": {
        "factor": 2.0,
        "source": "no online source checked for aluminium casting alloys; 2.0 d as for soft aluminium",
        "verified": False,
        "note": "UNVERIFIED",
    },
    "alu_wrought": {
        "factor": 1.4,
        "source": "Bossard, Technische Information Einschraubtiefe 01/2025, Tabelle 8.8 Regelgewinde (https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf): AlMgSi1 F32 / AlMg4,5Mn F28, Rm > 330",
        "verified": True,
    },
    "brass": {
        "factor": 1.2,
        "source": "Roloff-Matek Maschinenelemente (Kupferlegierungen / Messing CuZn39Pb3)",
        "verified": False,
        "note": "UNVERIFIED: Richtwert Literatur, abhängig von Legierung und Härte",
    },
    "plastic": {
        "factor": 2.5,
        "source": "VDI 2230 Richtwert für Thermoplaste (Direktverschraubung)",
        "verified": False,
        "note": "UNVERIFIED: Im 3D-Druck unzuverlässig; stattdessen use_insert=True (Ruthex) verwenden",
    },
}

_MATERIAL_ALIASES = {
    "steel": "steel",
    "stahl": "steel",
    "st": "steel",
    "cast_iron": "cast_iron",
    "castiron": "cast_iron",
    "grauguss": "cast_iron",
    "guss": "cast_iron",
    "gg": "cast_iron",
    "alu": "alu",
    "aluminum": "alu",
    "aluminium": "alu",
    "alu_cast": "alu_cast",
    "aluguss": "alu_cast",
    "alu_guss": "alu_cast",
    "alu_wrought": "alu_wrought",
    "aluknet": "alu_wrought",
    "alu_knet": "alu_wrought",
    "brass": "brass",
    "messing": "brass",
    "plastic": "plastic",
    "kunststoff": "plastic",
    # Materials of the catalog library (tools/katalog_to_solidcraft.py) by their SolidCraft name.
    # Aluminium only counts as alu_wrought where Rm reaches the Bossard row (Rm > 330 MPa): 7075 T6;
    # 6060/6082 T6 and 5083 H111 stay below it and take the soft-aluminium value. Stainless steels have
    # no checked row and are left out.
    "s235jr": "steel",
    "s355j2": "steel",
    "c45_+qt": "steel",
    "42crmo4_+qt": "steel",
    "en_gjl_250": "cast_iron",
    "en_aw_6060_t6": "alu",
    "en_aw_6082_t6": "alu",
    "en_aw_5083_h111": "alu",
    "en_aw_7075_t6": "alu_wrought",
    "cuzn39pb3_(cw614n)": "brass",
}


def normalize_material(material: str | None) -> str:
    """Normalize a material string to canonical key in MATERIAL_ENGAGEMENT_DEPTHS."""
    raw = (material or "steel").strip().lower().replace("-", "_").replace(" ", "_")
    canon = _MATERIAL_ALIASES.get(raw, raw)
    if canon not in MATERIAL_ENGAGEMENT_DEPTHS:
        avail = ", ".join(MATERIAL_ENGAGEMENT_DEPTHS)
        if raw in ("pla", "petg", "abs", "asa"):
            raise ValueError(
                f"unsupported blind material {material!r}: direct metric threads in 3D-printed plastics "
                f"({raw.upper()}) have no verified thread engagement depth; recommend heat-set inserts "
                f"(use_insert=True) or thread-forming screws instead (available: {avail})"
            )
        raise ValueError(f"unsupported blind material {material!r} (available: {avail})")
    return canon


def thread_engagement_depth(size: str, material: str = "steel") -> float:
    """Return minimum thread engagement depth s_einschraub in mm for `size` and `material`."""
    canon_size = normalize_size(size)
    canon_mat = normalize_material(material)
    d = standard_parts.ISO_4762[canon_size]["d"]
    factor = MATERIAL_ENGAGEMENT_DEPTHS[canon_mat]["factor"]
    return round(factor * d, 2)


def thread_runout(size: str) -> float:
    """Return standard thread runout length (Gewindeauslauf a nach DIN 76-1 Form A, approx 4 * P)."""
    canon_size = normalize_size(size)
    pitch = DIN_336[canon_size]["pitch"]
    return round(4.0 * pitch, 2)


def drill_point_depth(size: str, tip_angle_deg: float = 118.0) -> float:
    """Return depth of conical drill point (Bohrspitze) for tap drill of `size` (mm)."""
    canon_size = normalize_size(size)
    drill_d = DIN_336[canon_size]["drill"]
    half_angle_rad = math.radians(tip_angle_deg / 2.0)
    return round((drill_d / 2.0) / math.tan(half_angle_rad), 3)


def blind_hole_depths(size: str, material: str = "steel", screw_engagement: float | None = None) -> dict:
    """Calculate thread depth, drill depth and tap drill diameter for a blind tapped hole."""
    canon_size = normalize_size(size)
    canon_mat = normalize_material(material)
    min_eng = thread_engagement_depth(canon_size, canon_mat)
    thread_depth = max(min_eng, float(screw_engagement)) if screw_engagement is not None else min_eng
    runout = thread_runout(canon_size)
    drill_depth = round(thread_depth + runout, 2)
    point_depth = drill_point_depth(canon_size, 118.0)
    total_depth = round(drill_depth + point_depth, 2)
    mat_info = MATERIAL_ENGAGEMENT_DEPTHS[canon_mat]

    return {
        "material": canon_mat,
        "factor": mat_info["factor"],
        "min_engagement": min_eng,
        "thread_depth": round(thread_depth, 2),
        "runout": runout,
        "drill_depth": drill_depth,
        "point_depth": point_depth,
        "total_depth": total_depth,
        "tap_drill": DIN_336[canon_size]["drill"],
        "tip_angle": "118 deg",
        "verified": mat_info["verified"],
        "source": mat_info["source"],
    }


__all__ = [
    "ISO_273",
    "DIN_336",
    "DIN_974_1",
    "MATERIAL_ENGAGEMENT_DEPTHS",
    "normalize_size",
    "normalize_fit",
    "normalize_material",
    "clearance_hole",
    "tap_drill",
    "counterbore",
    "preferred_screw_length",
    "thread_engagement_depth",
    "thread_runout",
    "drill_point_depth",
    "blind_hole_depths",
]
