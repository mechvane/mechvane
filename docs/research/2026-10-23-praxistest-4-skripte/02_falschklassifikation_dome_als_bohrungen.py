#!/usr/bin/env python3
"""Befund 2: classify_hole_groups stuft zylindrische Dome fälschlich als Bohrungen ein.

In inventa/geometry.py:classify_hole_groups wird eine kleine Prüfkugel (r=0.05 mm)
leicht innerhalb der Zylinderfläche platziert und inspect.interference aufgerufen.
Da SolidCraft bei vollständig eingeschlossenen Körpern ohne Grenzflächenkollision
0 Interferenzen meldet, schließt geometry.py fälschlich auf 'kein Material' und
markiert jeden massiven zylindrischen Dom als 'hole'.

In der Folge liefert find(..., 'holes') massive Dome als Bohrungen, und
check_design wendet Bohrungsregeln auf Außendome an.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/02_falschklassifikation_dome_als_bohrungen.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART
from mechvane import design_rules, geometry as g, server

ws_dir = Path("/tmp/praxis4-repro-2")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)
server.ws = ws

part = ws.new(PART, "teil_mit_dom")
part.session.batch([
    {"command": "solid.box", "params": {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Boden"}},
    # Massiver Dom (Zylinder mit operation=join, kein cut!)
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": 20, "base": [35, 20, 3], "operation": "join", "name": "Schraubdom"}},
    # Echte Bohrung im Dom (Ø 4.0 mm, Ruthex-Aufnahme)
    {"command": "solid.hole", "params": {"position": [35, 20, 23], "direction": [0, 0, -1], "diameter": 4.0, "depth": 10, "name": "RuthexLoch"}},
])
part.save()

# 1. Test über server.find("holes")
holes = server.find("teil_mit_dom", "holes")
print(f"Gefundene Bohrungen in find: {holes['count']}")
for h in holes["holes"]:
    print(f"  Ø {h['diameter']} mm, Zentrum: {h['center']}, Flächen: {h['faces']}")

# Der massive Dom (Ø 8.0 mm) wird fälschlich als Bohrung gelistet:
diameters = [h["diameter"] for h in holes["holes"]]
assert 8.0 in diameters, "Dom Ø 8.0 mm sollte im aktuellen Code als Bohrung erscheinen"
assert 4.0 in diameters, "Echtes Loch Ø 4.0 mm sollte als Bohrung erscheinen"

# 2. Test über check_design
chk = design_rules.check(part.session, profile="fdm_0.4")
edge_findings = chk["rules"]["hole_edge_distance"]["findings"]
print(f"check_design Befunde für Lochrandabstand: {len(edge_findings)}")
for f in edge_findings:
    print(f"  Status: {f['status']}, Meldung: {f['message']}")

dom_findings = [f for f in edge_findings if "Ø 8.0 mm" in f["message"]]
assert len(dom_findings) > 0, "check_design sollte den massiven Dom Ø 8.0 mm als Bohrung geprüft haben"

print("Befund 2 erfolgreich verifiziert: Dom wird als Bohrung fehlklassifiziert!")
