#!/usr/bin/env python3
"""Befund 3: Fehlende Bauteil-Einschränkung in bolted_connection (Durchschuss auf darunterliegende Bauteile).
bolted_connection bietet keinen Parameter (z. B. 'parts' oder 'occurrences'), um festzulegen,
welche Bauteile verbunden werden sollen. Die Durchdringungsanalyse (_find_penetrations) sammelt
stumpf alle vom Strahl geschnittenen Bauteile in der Baugruppe.

Bei einer typischen Stapelung (Deckel auf Lagerbock auf Grundplatte):
Wird der Deckel von oben mit einer Sackloch-Verschraubung am Lagerbock befestigt (direction=[0, 0, -1]),
schneidet der Strahl Deckel, Lagerbock UND die darunterliegende Grundplatte.
bolted_connection interpretiert die Grundplatte als unterstes Sackloch-Bauteil und Deckel + Lagerbock
zusammen als Klemmlänge (50 mm), was die maximale Schraubenlänge überschreitet
(ValueError: required screw length 54.6 mm exceeds maximum preferred length 50 mm for ISO 4762 M5)
und im Erfolgsfall die Bohrung komplett durch den Lagerbock hindurch in die Grundplatte schneiden würde,
obwohl der Deckel nur am Lagerbock verschraubt werden sollte.

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/03_bolted_connection_keine_bauteilbegrenzung_durchschuss.py
"""
import os
import shutil
import sys
from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, links

def main():
    tmp_path = "/tmp/praxis-test-repro-03"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    ws = Workspace(tmp_path)
    try:
        gp = ws.new(PART, "p_grundplatte", overwrite=True)
        gp.session.cmd("solid.box", {"length": 120, "width": 80, "height": 10, "corner": [-60, -40, 0], "name": "Box"})
        gp.save()

        lb = ws.new(PART, "p_lagerbock", overwrite=True)
        lb.session.cmd("solid.box", {"length": 60, "width": 40, "height": 40, "corner": [-30, -20, 0], "name": "Box"})
        lb.save()

        dk = ws.new(PART, "p_deckel", overwrite=True)
        dk.session.cmd("solid.box", {"length": 60, "width": 40, "height": 10, "corner": [-30, -20, 0], "name": "Box"})
        dk.save()

        asm = ws.new(ASSEMBLY, "p_asm", overwrite=True)
        links.insert(ws, asm, gp.path, name="Grundplatte", grounded=True)
        links.insert(ws, asm, lb.path, name="Lagerbock", translate=[0, 0, 10], grounded=True)
        links.insert(ws, asm, dk.path, name="Deckel", translate=[0, 0, 50], grounded=True)
        asm.save()

        try:
            bolted.preview_bolted_connection(
                ws, "p_asm",
                placement={"position": [-15, 0, 60], "direction": [0, 0, -1]},
                size="M5",
                connection_type="blind",
                blind_material="alu"
            )
            print("Unerwartet erfolgreich!")
            sys.exit(1)
        except ValueError as e:
            print("Erfolgreich reproduziert:")
            print(f"  Typ: {type(e).__name__}")
            print(f"  Nachricht: {e}")
            assert "exceeds maximum preferred length" in str(e)
            pen = bolted._find_penetrations(ws, asm, [-15, 0, 60], [0, 0, -1])
            penetrated_names = [p["occurrence"]["name"] for p in pen]
            print(f"  Penetrierte Bauteile durch den Strahl: {penetrated_names}")
            assert penetrated_names == ["Deckel:1", "Lagerbock:1", "Grundplatte:1"]
            print("Erfolgreich belegt: Grundplatte wird ungewollt mitgeschnitten/als Sackloch interpretiert.")
    finally:
        ws.close_all()

if __name__ == "__main__":
    main()
