#!/usr/bin/env python3
"""Befund 3: check_design ignoriert zylindrische Dom-Außenwände bei Wandstärken- und Randabstandsprüfung.

In inventa/design_rules.py:_check_body filtert side_faces strikt nach Planarflächen:
  side_faces = [f for f in faces if f.get('plane_normal') and ...]
Zylindrische Außenflächen (wie die Mantelwand eines Schraubdoms) haben keine
plane_normal und werden vollständig ignoriert.

Ist ein Dom viel zu dünnwandig konstruiert (z. B. Dom Ø 4.8 mm mit Bohrung Ø 4.0 mm,
reale Wandstärke nur 0.40 mm statt der geforderten 1.20 mm für fdm_0.4), meldet
check_design dennoch fälschlich 'ok': Es fällt auf die Bounding-Box der Bodenplatte
(15.0 mm) zurück und behauptet: 'Wall thickness to edge is 13.00 mm >= 1.20 mm'.

Ausführen: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/03_wandstaerkenpruefung_ignoriert_zylindrische_domwand.py
"""

import shutil
from pathlib import Path

from mechvane.documents import Workspace, PART
from mechvane import design_rules

ws_dir = Path("/tmp/praxis4-repro-3")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)

part = ws.new(PART, "duennwandiger_dom")
part.session.batch([
    {"command": "solid.box", "params": {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Boden"}},
    # Dom mit Außen-Ø 4.8 mm (Radius 2.4 mm)
    {"command": "solid.cylinder", "params": {"diameter": 4.8, "height": 15, "base": [35, 20, 3], "operation": "join", "name": "Dom"}},
    # Bohrung mit Ø 4.0 mm (Radius 2.0 mm) -> Reale Wandstärke des Doms = 2.4 - 2.0 = 0.4 mm!
    # Gefordert für FDM 0.4 mm Düse: mindestens 1.20 mm Wandstärke!
    {"command": "solid.hole", "params": {"position": [35, 20, 18], "direction": [0, 0, -1], "diameter": 4.0, "depth": 10, "name": "Bohrung"}},
])
part.save()

chk = design_rules.check(part.session, profile="fdm_0.4")
wall_rule = chk["rules"]["min_wall_thickness"]
print("check_design min_wall_thickness status:", wall_rule["status"])
for f in wall_rule["findings"]:
    print(f"  Befund: {f['status']} - {f['message']}")

# Trotz unzulässiger 0.4 mm Domwand meldet check_design status=ok (Falsch-Positiv):
assert wall_rule["status"] == "ok", "check_design sollte fälschlich ok melden"
hole_findings = [f for f in wall_rule["findings"] if "F3:bore" in f["location"]["face"]]
assert any(f["value"] > 10.0 for f in hole_findings), "check_design hat Wandstärke zur fernen Bounding-Box statt zur Domwand gemessen"

print("Befund 3 erfolgreich verifiziert: Zylindrische Dom-Wandstärken werden komplett ignoriert!")
