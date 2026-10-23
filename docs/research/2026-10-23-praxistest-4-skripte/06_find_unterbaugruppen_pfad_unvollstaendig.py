#!/usr/bin/env python3
"""Befund 6: find in Baugruppen liefert für Unterbaugruppen-Teile nur Blattnamen statt vollen Pfad.

In inventa/query.py:_find_holes_assembly und _find_faces_assembly wird das Feld
'occurrence' mit dem einfachen Namen der Blatt-Occurrence belegt (z. B. 'Platine:1'
oder 'Bolzen1:1'), anstatt den hierarchischen Baugruppenpfad 'Elektronik:1/Platine:1'
anzugeben.

Möchte ein Agent das Ergebnis von find direkt in add_joint(assembly, ...) oder
edit_in_place(assembly, ...) verwenden, muss inventas resolve_occurrences die
Occurrence auflösen. Während add_joint den vollen Pfad 'Sub:1/Part:1' erwartet,
fehlt dieser Präfix in der Rückgabe von find.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/06_find_unterbaugruppen_pfad_unvollstaendig.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import links, server

ws_dir = Path("/tmp/praxis4-repro-6")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)
server.ws = ws

# 1. Unterbaugruppe mit Bauteil Platte
platte = ws.new(PART, "sub_platte")
platte.session.batch([
    {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [-20, -20, 0], "name": "Box"}},
    {"command": "solid.cylinder", "params": {"diameter": 4, "height": 7, "base": [10, 10, -1], "operation": "cut", "name": "Hole"}},
])
platte.save()

sub = ws.new(ASSEMBLY, "sub_asm")
links.insert(ws, sub, platte.path, name="Platte", grounded=True)
sub.save()

# 2. Hauptbaugruppe
top = ws.new(ASSEMBLY, "top_asm")
links.insert(ws, top, sub.path, name="SubUnit", translate=[50, 0, 0], grounded=True)
top.save()

# 3. find in Baugruppe
res = server.find("top_asm", "holes")
print(f"Gefundene Bohrungen in Baugruppe: {res['count']}")
for h in res["holes"]:
    print(f"  Bohrung: Ø {h['diameter']} mm, occurrence: {h.get('occurrence')}")

occ_name = res["holes"][0]["occurrence"]
assert occ_name == "Platte:1", f"Unerwarteter Name: {occ_name}"
assert "SubUnit" not in occ_name, "find liefert den einfachen Blattnamen ohne Elternbaugruppe"

print("Befund 6 erfolgreich verifiziert: find liefert unvollständigen Occurrence-Pfad für Unterbaugruppen!")
