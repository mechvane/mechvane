#!/usr/bin/env python3
"""Befund 7: Bolted-Connection-Bohrungen sind numerisch statisch; Gehäuseänderung führt zu Abriss und 'face_missing'.

Wird ein Gehäuse mit parametrischen Domen (z. B. dx = L/2 - 15 mm) nachträglich per
edit_in_place verlängert (L: 100 -> 110 mm), wandern die Dome im CAD-Modell mit
(x: 35 -> 40 mm).

Die zuvor von bolted_connection erzeugten Bohrungsfeatures (Hole_Ruthex_M3_*)
wurden jedoch mit absoluten Koordinaten (loc_pos = [35.0, 20.0, ...]) in die
Bauteildatei geschrieben.

Nach der Parameteränderung verbleiben die Bohrungen bei x = 35 mm und schneiden
durch den Boden statt durch den Dom. Die Stirnfläche des Doms wird zerstört, und
darauf sitzende Gelenke (z. B. der Unterbaugruppe oder Schrauben) melden
beim update_links:
  status: face_missing bzw. origin_lost.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/07_bolted_connection_bohrungen_nicht_parametrisch_abriss.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, links, server

ws_dir = Path("/tmp/praxis4-repro-7")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)
server.ws = ws

# 1. Gehäuse mit parametrischem Dom dx = L/2 - 15 mm
gehaeuse = ws.new(PART, "gehaeuse")
gehaeuse.session.batch([
    {"command": "parameters.add", "params": {"name": "L", "expression": "100 mm"}},
    {"command": "parameters.add", "params": {"name": "dx", "expression": "L/2 - 15 mm"}},
    {"command": "solid.box", "params": {"length": "L", "width": 70, "height": 35, "corner": ["-L/2", -35, 0], "name": "Box"}},
    {"command": "solid.box", "params": {"length": "L - 5 mm", "width": 65, "height": 33, "corner": ["-(L - 5 mm)/2", -32.5, 2.5], "operation": "cut", "name": "Pocket"}},
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": 32.5, "base": ["dx", 20, 2.5], "operation": "join", "name": "Dom"}},
])
gehaeuse.save()

# 2. Deckel
deckel = ws.new(PART, "deckel")
deckel.session.cmd("solid.box", {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Deckel"})
deckel.save()

# 3. Baugruppe
asm = ws.new(ASSEMBLY, "asm")
links.insert(ws, asm, gehaeuse.path, name="Gehaeuse", grounded=True)
links.insert(ws, asm, deckel.path, name="Deckel", translate=[0, 0, 35], grounded=False)
asm.save()

# 4. bolted_connection anlegen (bei x = 35 mm)
res = bolted.bolted_connection(
    ws, "asm",
    placement={"position": [35, 20, 38], "direction": [0, 0, -1]},
    size="M3",
    use_insert=True,
    counterbore=False,
    parts=["Deckel:1", "Gehaeuse:1"],
)
asm.save()
print("Bolted connection angelegt bei x=35 mm, Joint:", res["joints"])

# 5. Gehäuse per edit_in_place verlängern (L: 100 -> 110 mm -> Dom wandert nach x=40 mm)
eip = server.edit_in_place("asm", "Gehaeuse:1")
part_g = ws.get(eip["document"], PART)
part_g.session.cmd("parameters.change", {"name": "L", "expression": "110 mm"})
fed = server.finish_edit(eip["document"], update=True)

print(f"finish_edit Warnungen nach L=110 mm:")
for w in fed["assemblies"]["asm"]["warnings"]:
    print(f"  Gelenk {w['joint']}: status = {w['status']}, face = {w.get('face')}")

statuses = [w["status"] for w in fed["assemblies"]["asm"]["warnings"]]
assert any(s in ("face_missing", "origin_lost", "moved") for s in statuses)

print("Befund 7 erfolgreich verifiziert: Statische Bohrungskoordinaten führen bei Bauteiländerung zu Gelenkabrisse!")
