#!/usr/bin/env python3
"""Befund 2: Falschalarm und negative Wandstärke in check_design bei horizontalen Bohrungen (Achse entlang Y oder X).
In inventa/design_rules.py berechnet _check_body:
    dx = min(abs(c[0] - bbox["min"][0]), abs(c[0] - bbox["max"][0]))
    dy = min(abs(c[1] - bbox["min"][1]), abs(c[1] - bbox["max"][1]))
    min_dist_box = min(dx, dy)
    min_dist_face = min([d for d, _ in dist_faces]) if dist_faces else min_dist_box
    e_edge = min(min_dist_box, min_dist_face)

Liegt die Bohrungsachse entlang Y (z. B. eine Ø22-Lagerbohrung durch einen 20 mm dicken Lagerbock),
ist dy der Abstand entlang der Bohrungsachse zu den Durchdringungsflächen (z. B. 10 mm).
min_dist_box wählt dy = 10 mm, und w_edge = e_edge - r wird 10.0 - 11.0 = -1.0 mm!
check_design meldet daraufhin fälschlich 'fail' mit negativer Wandstärke (-1.0 mm)
und zu kleinem Randabstand, obwohl die seitlichen Wandstärken in X und Z völlig ausreichend sind (> 10 mm).

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/02_falschalarm_check_design_horizontale_bohrung.py
"""
import os
import shutil
import sys
from mechvane.documents import Workspace, PART
from mechvane import design_rules

def main():
    tmp_path = "/tmp/praxis-test-repro-02"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    ws = Workspace(tmp_path)
    try:
        p = ws.new(PART, "lagerbock_horiz", overwrite=True)
        # Quader: 80 mm in X (-40..40), 20 mm in Y (0..20), 60 mm in Z (0..60)
        p.session.cmd("solid.box", {
            "length": 80, "width": 20, "height": 60,
            "corner": [-40, 0, 0], "operation": "new", "name": "Basis"
        })
        # Durchgangsbohrung Ø22 entlang Y, zentriert bei X=0, Z=35 (Wandabstand in X: 40-11=29 mm, in Z: 25-11=14 mm oben, 35-11=24 mm unten)
        p.session.cmd("solid.cylinder", {
            "diameter": 22, "height": 24, "base": [0, -2, 35],
            "axis": [0, 1, 0], "operation": "cut", "name": "Lagerbohrung"
        })

        res = design_rules.check(p.session, profile="fdm_0.4")
        wall_res = res["rules"]["min_wall_thickness"]
        edge_res = res["rules"]["hole_edge_distance"]

        print("Ergebnis check_design:")
        print(f"  min_wall_thickness Status: {wall_res['status']}")
        for f in wall_res["findings"]:
            print(f"    {f['message']}")
        print(f"  hole_edge_distance Status: {edge_res['status']}")
        for f in edge_res["findings"]:
            print(f"    {f['message']}")

        # Prüfe ob der Falschalarm auftritt (negative Wandstärke)
        neg_findings = [f for f in wall_res["findings"] if f["value"] < 0]
        assert len(neg_findings) > 0, "Erwarteter Falschalarm mit negativer Wandstärke trat nicht auf"
        assert wall_res["status"] == "fail"
        print("Erfolgreich reproduziert: negative Wandstärke gemeldet wegen Achsenannahme Z!")
    finally:
        ws.close_all()

if __name__ == "__main__":
    main()
