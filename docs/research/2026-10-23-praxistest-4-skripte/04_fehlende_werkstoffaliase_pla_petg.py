#!/usr/bin/env python3
"""Befund 4: blind_material='PLA' (und andere 3D-Druck-Werkstoffe) wird mit ValueError abgewiesen.

In inventa/hole_tables.py:_MATERIAL_ALIASES sind für Kunststoffe nur 'plastic' und
'kunststoff' hinterlegt. Der im 3D-Druck weitestverbreitete Standardwerkstoff PLA
(sowie PETG, ABS, ASA) wird nicht als Alias erkannt.

Ein Aufruf mit blind_material='PLA' bricht mit ValueError ab, obwohl inventa
über das Fertigungsprofil fdm_0.4 und Ruthex-Normteile explizit für 3D-Druck
ausgelegt ist.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/04_fehlende_werkstoffaliase_pla_petg.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, links

ws_dir = Path("/tmp/praxis4-repro-4")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)

deckel = ws.new(PART, "deckel")
deckel.session.cmd("solid.box", {"length": 50, "width": 50, "height": 4, "corner": [-25, -25, 0], "name": "Deckel"})
deckel.save()

basis = ws.new(PART, "basis")
basis.session.cmd("solid.box", {"length": 50, "width": 50, "height": 20, "corner": [-25, -25, 0], "name": "Basis"})
basis.save()

asm = ws.new(ASSEMBLY, "asm")
links.insert(ws, asm, basis.path, name="Basis", grounded=True)
links.insert(ws, asm, deckel.path, name="Deckel", translate=[0, 0, 20], grounded=False)
asm.save()

# 1. Versuch mit PLA: Schlägt fehl
try:
    bolted.preview_bolted_connection(
        ws, "asm",
        placement={"position": [10, 10, 24], "direction": [0, 0, -1]},
        size="M3",
        connection_type="blind",
        blind_material="PLA",
        counterbore=False,
    )
    print("FEHLER: PLA hätte abgewiesen werden müssen!")
    exit(1)
except ValueError as e:
    print("Erwarteter Fehler bei blind_material='PLA':")
    print(f"  ValueError: {e}")
    assert "unsupported blind material 'PLA'" in str(e)
    assert "plastic" in str(e)

# 2. Gegenprobe mit 'plastic': Funktioniert
prev_plastic = bolted.preview_bolted_connection(
    ws, "asm",
    placement={"position": [10, 10, 24], "direction": [0, 0, -1]},
    size="M3",
    connection_type="blind",
    blind_material="plastic",
    counterbore=False,
)
print(f"Gegenprobe mit blind_material='plastic' erfolgreich:")
print(f"  Gewindetiefe: {prev_plastic['parts'][1]['thread_depth']} mm, Bohrertiefe: {prev_plastic['parts'][1]['drill_depth']} mm")

print("Befund 4 erfolgreich verifiziert: 3D-Druck-Aliase (PLA) fehlen!")
