#!/usr/bin/env python3
"""Befund 5: Boolean Refusal bei edit_bolted_connection nach edit_in_place und Sacklochbohrung mit 118° Bohrspitze.
Wenn ein Bauteil sowohl Durchgangsverschraubungen (z. B. M6 Grundplatte) als auch eine
Sacklochverschraubung mit Bohrspitze (118 deg, z. B. M5 Deckel) enthält, und das Bauteil
per edit_in_place parametrisch geändert wird (z. B. tower_h von 40 auf 45 mm):
Führt ein anschließendes edit_bolted_connection (M6 -> M8) zu einem internen Boolean-Abbruch
des SolidCraft-Kerns:
    SolidCraftError: the cut could not be computed reliably: it would change the body away from the tool,
    at (-16.699, 4.041, 33.973) (outside the tool's region).

Die Koordinate (-16.699, 4.041, 33.973) liegt exakt an der kegeligen Bohrspitze des Sacklochs M5
(F8:bore:side:2#1), weit abseits des M8-Bohrwerkzeugs (bei X=-32, Y=-20, Z=14).
Die B-Rep-Topologieüberprüfung des Kerns verweigert den Schnitt an der Sacklochspitze.

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/05_edit_bolted_connection_nach_sackloch_boolean_refusal.py
"""
import os
import shutil
import sys
from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, inplace, links

def main():
    tmp_path = "/tmp/praxis-test-repro-05"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    ws = Workspace(tmp_path)
    try:
        # Grundplatte
        gp = ws.new(PART, "p_gp", overwrite=True)
        gp.session.cmd("solid.box", {"length": 120, "width": 80, "height": 10, "corner": [-60, -40, 0], "name": "Box"})
        gp.save()

        # Lagerbock mit Turm und Lagerbohrung
        lb = ws.new(PART, "p_lb", overwrite=True)
        lb.session.batch([
            {"command": "parameters.add", "params": {"name": "tower_h", "expression": "40 mm"}},
            {"command": "solid.box", "params": {"length": 90, "width": 60, "height": 14, "corner": [-45, -30, 0], "name": "Base"}},
            {"command": "solid.box", "params": {"length": 50, "width": 24, "height": "tower_h", "corner": [-25, -12, 14], "operation": "join", "name": "Tower"}},
            {"command": "solid.cylinder", "params": {"diameter": 22, "height": 28, "base": [0, -14, 34], "axis": [0, 1, 0], "operation": "cut", "name": "Bore"}}
        ])
        lb.save()

        # Deckel
        dk = ws.new(PART, "p_dk", overwrite=True)
        dk.session.cmd("solid.box", {"length": 50, "width": 8, "height": 40, "corner": [-25, -20, 14], "name": "DeckelBox"})
        dk.save()

        # Baugruppe
        asm = ws.new(ASSEMBLY, "p_asm", overwrite=True)
        links.insert(ws, asm, gp.path, name="Grundplatte", grounded=True)
        links.insert(ws, asm, lb.path, name="Lagerbock", translate=[0, 0, 10], grounded=True)
        links.insert(ws, asm, dk.path, name="Deckel", translate=[0, 0, 10], grounded=True)
        asm.save()

        # M6 Durchgangsverbindung 2x2
        pat4 = {"type": "rectangular", "count": [2, 2], "spacing": [64, 40], "directions": [[1, 0, 0], [0, 1, 0]]}
        bolted.bolted_connection(
            ws, "p_asm",
            placement={"position": [-32, -20, 24], "direction": [0, 0, -1]},
            size="M6",
            counterbore=False,
            pattern=pat4,
            name="M6_Base"
        )

        # M5 Sacklochverbindung 2x1
        pat2 = {"type": "rectangular", "count": [2, 1], "spacing": [32, 0], "directions": [[1, 0, 0], [0, 0, 1]]}
        bolted.bolted_connection(
            ws, "p_asm",
            placement={"position": [-16, -20, 44], "direction": [0, 1, 0]},
            size="M5",
            connection_type="blind",
            blind_material="alu",
            pattern=pat2,
            counterbore=False,
            name="M5_Deckel"
        )

        # Edit in place: tower_h von 40 auf 45 mm
        eip = inplace.edit_in_place(ws, "p_asm", "Lagerbock:1")
        lb_doc = ws.docs[eip["document"]]
        lb_doc.session.cmd("parameters.change", {"name": "tower_h", "expression": "45 mm"})
        inplace.finish_edit(ws, eip["document"])

        # Edit bolted connection M6 -> M8
        try:
            bolted.edit_bolted_connection(ws, "p_asm", "M6_Base", size="M8")
            print("Unerwartet erfolgreich!")
            sys.exit(1)
        except Exception as e:
            print("Erfolgreich reproduziert:")
            print(f"  Typ: {type(e).__name__}")
            print(f"  Nachricht: {e}")
            assert "the cut could not be computed reliably" in str(e)
            assert "outside the tool's region" in str(e)
            print("Erfolgreich belegt: SolidCraft Boolean Refusal an der Sacklochspitze während edit_bolted_connection.")
    finally:
        ws.close_all()

if __name__ == "__main__":
    main()
