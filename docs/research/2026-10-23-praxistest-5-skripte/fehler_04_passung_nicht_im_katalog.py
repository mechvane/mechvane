"""Befund 5: Keine ISO-286-Passungen (H7/k6/h6) im Katalog: weder fit= bei Bohrungen noch in standard_part/list_standard_parts.
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_04_passung_nicht_im_katalog.py"""
import sys
sys.path.insert(0, ".")
from mechvane import hole_tables, standard_parts
for fit in ("H7", "k6", "h6", "normal"):
    try:
        print(fit, "->", hole_tables.normalize_fit(fit))
    except Exception as e:
        print(fit, "->", type(e).__name__, e)
cat = standard_parts.catalog("DIN 625")
print("DIN 625 Eintrag 608:", cat["sizes"]["608"], "(keine Toleranz-/Passungsangabe fuer Sitz oder Welle)")
print("Schluessel DIN 625:", sorted(cat), "| Schluessel Zeile:", sorted(cat["sizes"]["608"]))
