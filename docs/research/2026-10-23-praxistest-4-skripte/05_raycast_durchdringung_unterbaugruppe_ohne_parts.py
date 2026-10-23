#!/usr/bin/env python3
"""Befund 5: Raycast in Baugruppe mit innenliegender Elektronik erfordert zwingend 'parts'.

Befindet sich eine Unterbaugruppe (Platine + Bolzen) im Inneren eines Gehäuses,
durchdringt der Raycast von bolted_connection ohne Einschränkung alle Bauteile
entlang der Achse (Deckel -> Gehäuse-Dom -> Platine -> Bolzen).

Die akkumulierte Klemmlänge übersteigt die Maximallänge der Schraubennorm (z. B. 30 mm
für ISO 4762 M3), sodass der Assistent mit ValueError abbricht. Zudem wird der Dom
des Gehäuses vor der Platine gelistet, weil der Dom bis Z=35 mm reicht.

Erst durch explizite Angabe von parts=['Deckel:1', 'Gehaeuse:1'] kann die Verschraubung
korrekt auf Deckel und Gehäusedom begrenzt werden.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/05_raycast_durchdringung_unterbaugruppe_ohne_parts.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, links

ws_dir = Path("/tmp/praxis4-repro-5")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)

# 1. Gehäuse mit Dom Z=0..35
gehaeuse = ws.new(PART, "gehaeuse")
gehaeuse.session.batch([
    {"command": "solid.box", "params": {"length": 100, "width": 70, "height": 35, "corner": [-50, -35, 0], "name": "Box"}},
    {"command": "solid.box", "params": {"length": 95, "width": 65, "height": 33, "corner": [-47.5, -32.5, 2.5], "operation": "cut", "name": "Pocket"}},
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": 32.5, "base": [35, 20, 2.5], "operation": "join", "name": "Dom"}},
])
gehaeuse.save()

# 2. Platine Z=20..21.6
platine = ws.new(PART, "platine")
platine.session.cmd("solid.box", {"length": 80, "width": 50, "height": 1.6, "corner": [-40, -25, 0], "name": "Platine"})
platine.save()

# 3. Deckel Z=35..38
deckel = ws.new(PART, "deckel")
deckel.session.cmd("solid.box", {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Deckel"})
deckel.save()

# 4. Baugruppe
asm = ws.new(ASSEMBLY, "asm")
links.insert(ws, asm, gehaeuse.path, name="Gehaeuse", grounded=True)
links.insert(ws, asm, platine.path, name="Platine", translate=[0, 0, 20], grounded=False)
links.insert(ws, asm, deckel.path, name="Deckel", translate=[0, 0, 35], grounded=False)
asm.save()

# 1. Aufruf ohne parts: Schlägt fehl wegen Durchdringung aller 3 Bauteile
try:
    bolted.preview_bolted_connection(
        ws, "asm",
        placement={"position": [35, 20, 38], "direction": [0, 0, -1]},
        size="M3",
        use_insert=True,
        counterbore=False,
    )
    print("FEHLER: Aufruf ohne parts hätte fehlschlagen müssen!")
    exit(1)
except ValueError as e:
    print("Erwarteter Fehler ohne 'parts':")
    print(f"  ValueError: {e}")
    assert "penetrated parts" in str(e)
    assert "use 'parts' to restrict" in str(e)

# 2. Aufruf mit parts=['Deckel:1', 'Gehaeuse:1']: Funktioniert einwandfrei
prev_filtered = bolted.preview_bolted_connection(
    ws, "asm",
    placement={"position": [35, 20, 38], "direction": [0, 0, -1]},
    size="M3",
    use_insert=True,
    counterbore=False,
    parts=["Deckel:1", "Gehaeuse:1"],
)
print("Erfolgreiche Vorschau mit parts=['Deckel:1', 'Gehaeuse:1']:")
print(f"  Gewählte Schraubenlänge: {prev_filtered['selected_screw_length']} mm, Teile: {[p['occurrence'] for p in prev_filtered['parts']]}")
assert prev_filtered["selected_screw_length"] == 8.0

print("Befund 5 erfolgreich verifiziert: 'parts'-Restriktion bei Innenbauteilen zwingend erforderlich!")
