#!/usr/bin/env python3
"""Befund 6: Falschalarm in check_design bei inneren Absätzen/Stufen (hole_edge_distance).
In inventa/design_rules.py misst _check_body den Randabstand einer Bohrung zu allen parallelen
Planarflächen des Körpers:
    side_faces = [f for f in faces if f.get("plane_normal") and abs(g.dot(f["plane_normal"], axis)) < 0.1]
    dist = abs(g.dot(g.sub(c, sf["point"]), n))

Bei einem gestuften Bauteil (z. B. Lagerbock mit Grundflansch bis X=-45 und zentralem Turm ab X=-25)
bildet die vertikale Seitenwand des Turms eine Planarfläche mit Normale +X / -X.
_check_body behandelt diese innere Übergangswand wie eine Außenkante:
Liegt eine Flanschbohrung bei X=-32, beträgt der Abstand zur Turmwand abs(-32 - (-25)) = 7.0 mm.
check_design meldet daraufhin fälschlich 'fail' (7.0 mm < 9.9 mm gefordert für M6),
obwohl die eigentliche Außenkante bei X=-45 liegt und der reale Randabstand 13.0 mm >= 9.9 mm beträgt.

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/06_falschalarm_check_design_innere_stufen.py
"""
import os
import shutil
import sys
from mechvane.documents import Workspace, PART
from mechvane import design_rules

def main():
    tmp_path = "/tmp/praxis-test-repro-06"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    ws = Workspace(tmp_path)
    try:
        p = ws.new(PART, "p_gestuft", overwrite=True)
        # Flansch: 90 mm breit (X: -45..45), 60 mm tief, 14 mm hoch
        # Turm: 50 mm breit (X: -25..25), 24 mm tief, 40 mm hoch ab Z=14
        p.session.batch([
            {"command": "solid.box", "params": {"length": 90, "width": 60, "height": 14, "corner": [-45, -30, 0], "name": "Flansch"}},
            {"command": "solid.box", "params": {"length": 50, "width": 24, "height": 40, "corner": [-25, -12, 14], "operation": "join", "name": "Turm"}},
            # Flanschbohrung M6 (Ø 6.6 mm) bei X=-32, Y=-20 (Außenrand bei X=-45 -> Randabstand 13.0 mm)
            {"command": "solid.hole", "params": {"position": [-32, -20, 14], "direction": [0, 0, -1], "diameter": 6.6, "depth": 14, "name": "Bohrung_M6"}}
        ])

        res = design_rules.check(p.session, profile="fdm_0.4")
        edge_rule = res["rules"]["hole_edge_distance"]

        print(f"check_design hole_edge_distance: {edge_rule['status']}")
        for f in edge_rule["findings"]:
            print(f"  Befund: {f['message']}")

        # Prüfe ob der Falschalarm auftritt (innerer Absatz als Rand gewertet)
        step_findings = [f for f in edge_rule["findings"] if f["status"] == "fail" and f["value"] == 7.0]
        assert len(step_findings) > 0, "Erwarteter Falschalarm an der inneren Stufenfläche trat nicht auf"
        print("Erfolgreich reproduziert: Innere Turmwand (X=-25) wurde fälschlich als freier Rand bewertet!")
    finally:
        ws.close_all()

if __name__ == "__main__":
    main()
