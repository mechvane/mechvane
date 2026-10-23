#!/usr/bin/env python3
"""Befund 4: Falsche Gelenkausrichtung (Schraube um 180° verkehrt herum) bei bolted_connection mit counterbore=True und Muster.
In inventa/bolted.py (Zeile 881) wird beim Erzeugen des ScrewJoints starr 'flip': True übergeben:
    screw_jp = {
        "type": "rigid",
        "name": screw_jname,
        "flip": True,
        "a": {"occurrence": screw_target_occ, "circle": p_screw_bearing},
        "b": {"occurrence": inst_screw, "circle": p_screw_bearing},
    }

Da p_screw_bearing genau der Mittelpunkt der Senkstufen-Kreiskante ist und SolidCraft
Zylinder in zwei Halbkreise (:side:0 und :side:1) teilt, deren lokale Z-Achsen entgegengesetzt sind,
wählt SolidCraft an manchen Instanzen eines Musters (z. B. Instanz 4 bei 2x2 Rechteckmuster)
die andere Halbkreis-Kante mit umgekehrter Z-Achse (fa_z = -1.0 statt +1.0).
Durch das starre 'flip': True wird diese Schraube um 180° verkehrt herum (Kopf nach unten bzw.
Schaft nach oben) eingebaut.
inspect.interference meldet daraufhin eine schwere Kollision (Interferenzvolumen > 150 mm³),
weil die verkehrt herum stehende Schraube in die Platte ragt.

In tests/mechvane/check.py wurde das Rechteckmuster nur mit counterbore=False getestet,
weshalb dieser Fehler dort bisher unentdeckt blieb.

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/04_bolted_counterbore_pattern_screw_flip_bug.py
"""
import os
import shutil
import sys
from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, links

def main():
    tmp_path = "/tmp/praxis-test-repro-04"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    ws = Workspace(tmp_path)
    try:
        p1 = ws.new(PART, "p1", overwrite=True)
        p1.session.cmd("solid.box", {
            "length": 80, "width": 80, "height": 10,
            "corner": [-40, -40, 0], "operation": "new", "body_name": "Plate1", "name": "Box1"
        })
        p1.save()

        p2 = ws.new(PART, "p2", overwrite=True)
        p2.session.cmd("solid.box", {
            "length": 80, "width": 80, "height": 8,
            "corner": [-40, -40, 0], "operation": "new", "body_name": "Plate2", "name": "Box2"
        })
        p2.save()

        asm = ws.new(ASSEMBLY, "asm_flip", overwrite=True)
        links.insert(ws, asm, p1.path, name="Plate1", grounded=True)
        links.insert(ws, asm, p2.path, name="Plate2", translate=[0, 0, -8], grounded=True)
        asm.save()

        rect_pat = {"type": "rectangular", "count": [2, 2], "spacing": [30, 30], "directions": [[1, 0, 0], [0, 1, 0]]}
        res = bolted.bolted_connection(
            ws, "asm_flip",
            placement={"position": [-15, -15, 10], "direction": [0, 0, -1]},
            size="M5",
            counterbore=True,
            pattern=rect_pat,
        )

        joints = asm.session.cmd("joint.list")["joints"]
        screw_joints = [j for j in joints if "ScrewJoint" in j["name"]]
        z_dirs = [j["frame_a"]["z"][2] for j in screw_joints]
        print(f"Z-Richtungen der Schraubengelenke (frame_a.z): {z_dirs}")

        interf = asm.session.cmd("inspect.interference")
        print(f"inspect.interference count: {interf.get('count')}")
        for it in interf.get("interferences", []):
            print(f"  Kollision zwischen {it['a']} und {it['b']}: Vol = {it['volume_mm3']:.2f} mm³")

        # Prüfe ob Schraube 4 verkehrt ausgerichtet ist und kollidiert
        assert len(set(round(z, 2) for z in z_dirs)) > 1, f"Erwartete inkonsistente Z-Orientierung nicht aufgetreten: {z_dirs}"
        assert interf.get("count", 0) > 0, "Erwartete Kollision durch verkehrt eingebaute Schraube nicht aufgetreten"
        print("Erfolgreich reproduziert: Instanz 4 ist invertiert und verursacht Kollision!")
    finally:
        ws.close_all()

if __name__ == "__main__":
    main()
