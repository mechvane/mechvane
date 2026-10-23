#!/usr/bin/env python3
"""Befund 1: bolted_connection mit counterbore=True schlägt bei Standard-Deckeldicke (3 mm) fehl.

In 3D-Druck-Gehäusen sind 3 mm Deckel Standard. DIN 974-1 Reihe 1 fordert jedoch
für M3 eine Senktiefe von 3.4 mm (bzw. 3.9 mm mit Scheibe) und für M4 4.4 mm.
inventa bricht mit ValueError ab, da keine Teilsenkung oder Senkkopf (ISO 10642)
unterstützt wird.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/01_senkung_tiefe_ueberschreitet_deckeldicke.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, links

ws_dir = Path("/tmp/praxis4-repro-1")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)

# 1. Deckel 3 mm
deckel = ws.new(PART, "deckel")
deckel.session.cmd("solid.box", {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Deckel"})
deckel.save()

# 2. Gehäuseunterteil 15 mm
gehaeuse = ws.new(PART, "gehaeuse")
gehaeuse.session.cmd("solid.box", {"length": 100, "width": 70, "height": 15, "corner": [-50, -35, 0], "name": "Gehaeuse"})
gehaeuse.save()

# 3. Baugruppe
asm = ws.new(ASSEMBLY, "asm")
links.insert(ws, asm, gehaeuse.path, name="Gehaeuse", grounded=True)
links.insert(ws, asm, deckel.path, name="Deckel", translate=[0, 0, 15], grounded=False)
asm.save()

# Versuch: bolted_connection mit counterbore=True
try:
    bolted.preview_bolted_connection(
        ws, "asm",
        placement={"position": [35, 20, 18], "direction": [0, 0, -1]},
        size="M3",
        use_insert=True,
        counterbore=True,
    )
    print("FEHLER: preview_bolted_connection hätte fehlschlagen müssen!")
    exit(1)
except ValueError as e:
    print("Erwarteter Fehler erfolgreich reproduziert:")
    print(f"  ValueError: {e}")
    assert "counterbore depth (3.4 mm) exceeds or equals top plate thickness (3.0 mm)" in str(e)
    print("Befund 1 erfolgreich verifiziert!")

