"""Knowledge catalog for engineering rules, standards, and manufacturing parameters.

Loads, validates, and queries domain knowledge entries stored as individual JSON files.
See docs/adr/0002-wissenskatalog-format.md.
"""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_DIR = REPO_ROOT / "katalog" / "eintraege"

VALID_HERKUNFT = {
    "norm_sekundaer",
    "hersteller",
    "lehrbuch",
    "handbuch",
    "versuch",
    "erfahrung",
    "hypothese",
}

VALID_HAERTE = {"fehler", "hinweis"}

VALID_PRUEFSTATUS = {"automatisch", "von_hand", "offen", "nicht_belegt"}

VALID_BEZIEHUNG_TYP = {"widerspricht", "leitet_ab", "ersetzt", "gilt_fuer"}

REQUIRED_GELTUNGSBEREICH_KEYS = {
    "werkstoff",
    "verfahren",
    "feature",
    "groesse",
    "festigkeitsklasse",
}

REQUIRED_TOP_LEVEL_KEYS = {
    "id",
    "aussage",
    "werte",
    "geltungsbereich",
    "herkunft",
    "quellen",
    "begruendung",
    "ausnahmen",
    "haerte",
    "pruefstatus",
    "beziehungen",
}


def validate(eintrag: Dict[str, Any]) -> bool:
    """Validate a catalog entry dictionary against the catalog schema.

    Raises:
        ValueError: If any field is missing, invalid, or malformed.

    Returns:
        True if the entry is valid.
    """
    if not isinstance(eintrag, dict):
        raise ValueError(f"Entry must be a dictionary, got {type(eintrag).__name__}")

    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(eintrag.keys())
    if missing_keys:
        raise ValueError(f"Missing required top-level keys: {sorted(missing_keys)}")

    entry_id = eintrag.get("id")
    if not isinstance(entry_id, str) or not re.match(r"^[a-z0-9_-]+$", entry_id):
        raise ValueError(
            f"Invalid 'id': must be non-empty lowercase alphanumeric string with '-' or '_', got {entry_id!r}"
        )

    aussage = eintrag.get("aussage")
    if not isinstance(aussage, str) or not aussage.strip():
        raise ValueError(f"Entry '{entry_id}': 'aussage' must be a non-empty string")

    werte = eintrag.get("werte")
    if not isinstance(werte, list):
        raise ValueError(f"Entry '{entry_id}': 'werte' must be a list")
    for i, w in enumerate(werte):
        if not isinstance(w, dict):
            raise ValueError(f"Entry '{entry_id}': werte[{i}] must be an object")
        if not isinstance(w.get("name"), str) or not w["name"].strip():
            raise ValueError(f"Entry '{entry_id}': werte[{i}] missing non-empty 'name'")
        if not isinstance(w.get("einheit"), str):
            raise ValueError(f"Entry '{entry_id}': werte[{i}] 'einheit' must be a string")
        has_wert = "wert" in w
        has_bereich = "bereich" in w
        if not (has_wert or has_bereich):
            raise ValueError(f"Entry '{entry_id}': werte[{i}] must have 'wert' or 'bereich'")
        if has_wert and not isinstance(w["wert"], (int, float, str)):
            raise ValueError(f"Entry '{entry_id}': werte[{i}] 'wert' must be number or string")
        if has_bereich:
            if not isinstance(w["bereich"], list) or len(w["bereich"]) == 0:
                raise ValueError(f"Entry '{entry_id}': werte[{i}] 'bereich' must be a non-empty list")
            if not all(isinstance(x, (int, float, str)) for x in w["bereich"]):
                raise ValueError(f"Entry '{entry_id}': werte[{i}] 'bereich' items must be number or string")

    geltungsbereich = eintrag.get("geltungsbereich")
    if not isinstance(geltungsbereich, dict):
        raise ValueError(f"Entry '{entry_id}': 'geltungsbereich' must be an object")
    missing_gb = REQUIRED_GELTUNGSBEREICH_KEYS - set(geltungsbereich.keys())
    if missing_gb:
        raise ValueError(f"Entry '{entry_id}': 'geltungsbereich' missing keys {sorted(missing_gb)}")
    for k in REQUIRED_GELTUNGSBEREICH_KEYS:
        val = geltungsbereich[k]
        if not isinstance(val, list) or not all(isinstance(item, str) for item in val):
            raise ValueError(f"Entry '{entry_id}': geltungsbereich['{k}'] must be a list of strings")

    herkunft = eintrag.get("herkunft")
    if herkunft not in VALID_HERKUNFT:
        raise ValueError(
            f"Entry '{entry_id}': invalid 'herkunft' {herkunft!r}, expected one of {sorted(VALID_HERKUNFT)}"
        )

    quellen = eintrag.get("quellen")
    if not isinstance(quellen, list):
        raise ValueError(f"Entry '{entry_id}': 'quellen' must be a list")
    for i, q in enumerate(quellen):
        if not isinstance(q, dict):
            raise ValueError(f"Entry '{entry_id}': quellen[{i}] must be an object")
        for q_key in ("url", "stelle", "zitat", "abgerufen"):
            if not isinstance(q.get(q_key), str):
                raise ValueError(f"Entry '{entry_id}': quellen[{i}] '{q_key}' must be a string")

    begruendung = eintrag.get("begruendung")
    if not isinstance(begruendung, str):
        raise ValueError(f"Entry '{entry_id}': 'begruendung' must be a string")

    ausnahmen = eintrag.get("ausnahmen")
    if not isinstance(ausnahmen, str):
        raise ValueError(f"Entry '{entry_id}': 'ausnahmen' must be a string")

    haerte = eintrag.get("haerte")
    if haerte not in VALID_HAERTE:
        raise ValueError(
            f"Entry '{entry_id}': invalid 'haerte' {haerte!r}, expected one of {sorted(VALID_HAERTE)}"
        )

    pruefstatus = eintrag.get("pruefstatus")
    if pruefstatus not in VALID_PRUEFSTATUS:
        raise ValueError(
            f"Entry '{entry_id}': invalid 'pruefstatus' {pruefstatus!r}, expected one of {sorted(VALID_PRUEFSTATUS)}"
        )

    beziehungen = eintrag.get("beziehungen")
    if not isinstance(beziehungen, list):
        raise ValueError(f"Entry '{entry_id}': 'beziehungen' must be a list")
    for i, b in enumerate(beziehungen):
        if not isinstance(b, dict):
            raise ValueError(f"Entry '{entry_id}': beziehungen[{i}] must be an object")
        b_typ = b.get("typ")
        if b_typ not in VALID_BEZIEHUNG_TYP:
            raise ValueError(
                f"Entry '{entry_id}': beziehungen[{i}] invalid 'typ' {b_typ!r}, expected one of {sorted(VALID_BEZIEHUNG_TYP)}"
            )
        b_ziel = b.get("ziel")
        if not isinstance(b_ziel, str) or not b_ziel.strip():
            raise ValueError(f"Entry '{entry_id}': beziehungen[{i}] missing non-empty 'ziel'")

    return True


def load(path: Optional[Union[str, Path]] = None, validate_entries: bool = True) -> List[Dict[str, Any]]:
    """Load catalog entries from a file or directory.

    Args:
        path: File or directory path. Defaults to katalog/eintraege.
        validate_entries: Whether to validate loaded entries against the schema.

    Returns:
        List of entry dictionaries.
    """
    if path is None:
        target = DEFAULT_CATALOG_DIR
    else:
        target = Path(path)

    if not target.exists():
        raise FileNotFoundError(f"Catalog path not found: {target}")

    files: List[Path] = []
    if target.is_file():
        files = [target]
    else:
        for p in sorted(target.rglob("*.json")):
            if p.name == "schema.json":
                continue
            files.append(p)

    entries: List[Dict[str, Any]] = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        if validate_entries:
            validate(data)
        entries.append(data)

    return entries


def _normalize_size(size_str: str) -> str:
    """Normalize fastener or hole size strings for exact comparison."""
    return re.sub(r"\s+", "", size_str).upper()


def _build_searchable_text(entry: Dict[str, Any]) -> str:
    """Build a comprehensive plaintext representation of an entry for text search."""
    pieces = [
        entry.get("id", ""),
        entry.get("id", "").replace("_", " "),
        entry.get("aussage", ""),
        entry.get("begruendung", ""),
        entry.get("ausnahmen", ""),
    ]

    gb = entry.get("geltungsbereich", {})
    for key in ("werkstoff", "verfahren", "feature", "groesse", "festigkeitsklasse"):
        pieces.extend(gb.get(key, []))

    for w in entry.get("werte", []):
        pieces.append(w.get("name", ""))
        if "wert" in w:
            pieces.append(str(w["wert"]))
        if "bereich" in w:
            pieces.extend(str(x) for x in w["bereich"])
        pieces.append(w.get("einheit", ""))

    for q in entry.get("quellen", []):
        pieces.append(q.get("stelle", ""))
        pieces.append(q.get("zitat", ""))

    raw = " ".join(pieces).lower()
    return raw + " " + raw.replace("ß", "ss")


def query(
    werkstoff: Optional[str] = None,
    verfahren: Optional[str] = None,
    feature: Optional[str] = None,
    groesse: Optional[str] = None,
    festigkeitsklasse: Optional[str] = None,
    text: Optional[str] = None,
    eintraege: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Filter catalog entries by material, manufacturing method, feature, size, and text.

    Filtering rules:
    - werkstoff: Case-insensitive substring match against geltungsbereich['werkstoff'].
    - verfahren: Case-insensitive substring match against geltungsbereich['verfahren'].
    - feature: Case-insensitive substring match against geltungsbereich['feature'].
    - groesse: Exact match (case-insensitive, normalized whitespace) against geltungsbereich['groesse'].
    - festigkeitsklasse: Case-insensitive match against geltungsbereich['festigkeitsklasse'].
    - text: Case-insensitive substring or all-terms match across searchable text fields.

    Args:
        werkstoff: Material filter (e.g. 'Alu', 'Aluminium', 'Stahl').
        verfahren: Process filter (e.g. 'Fräsen', 'CNC-Fräsen', 'Kleben').
        feature: Feature filter (e.g. 'Tasche', 'Sackloch', 'Gleitlager').
        groesse: Exact size filter (e.g. 'M8', 'M3').
        festigkeitsklasse: Strength class filter (e.g. '8.8', 'A2-70').
        text: Free-text search terms (e.g. 'Anziehdrehmoment', 'Einpressmaß iglidur').
        eintraege: Optional pre-loaded entries list. Defaults to load().

    Returns:
        List of matching entry dictionaries.
    """
    if eintraege is None:
        eintraege = load()

    results: List[Dict[str, Any]] = []

    for entry in eintraege:
        gb = entry.get("geltungsbereich", {})

        if werkstoff is not None:
            w_sub = werkstoff.strip().lower()
            entry_werkstoffe = [m.lower() for m in gb.get("werkstoff", [])]
            if not any(w_sub in m for m in entry_werkstoffe):
                continue

        if verfahren is not None:
            v_sub = verfahren.strip().lower()
            entry_verfahren = [v.lower() for v in gb.get("verfahren", [])]
            if not any(v_sub in v for v in entry_verfahren):
                continue

        if feature is not None:
            f_sub = feature.strip().lower()
            entry_features = [f.lower() for f in gb.get("feature", [])]
            if not any(f_sub in f for f in entry_features):
                continue

        if groesse is not None:
            g_norm = _normalize_size(groesse)
            entry_groessen = [_normalize_size(g) for g in gb.get("groesse", [])]
            if g_norm not in entry_groessen:
                continue

        if festigkeitsklasse is not None:
            fk_norm = festigkeitsklasse.strip().lower()
            entry_fks = [fk.strip().lower() for fk in gb.get("festigkeitsklasse", [])]
            if not any(fk_norm == fk or fk_norm in fk for fk in entry_fks):
                continue

        if text is not None:
            query_str = text.strip().lower()
            if query_str:
                haystack = _build_searchable_text(entry)
                tokens = query_str.split()
                tokens_ss = [t.replace("ß", "ss") for t in tokens]
                matches_phrase = (query_str in haystack) or (query_str.replace("ß", "ss") in haystack)
                matches_all_tokens = all((t in haystack or t_ss in haystack) for t, t_ss in zip(tokens, tokens_ss))
                if not (matches_phrase or matches_all_tokens):
                    continue

        results.append(entry)

    return results


def get_entry(entry_id: str, eintraege: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single catalog entry by its unique ID."""
    if eintraege is None:
        eintraege = load()
    for entry in eintraege:
        if entry.get("id") == entry_id:
            return entry
    return None
