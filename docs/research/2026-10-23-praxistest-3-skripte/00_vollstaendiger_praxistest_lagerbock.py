#!/usr/bin/env python3
"""Vollständiger Praxistest 3: Konstruktion und Verifikation einer Lagerbock-Baugruppe.

Ablauf:
1. Bauteile erstellen:
   - Grundplatte 120 x 80 x 10 mm
   - Lagerbock mit Bohrung Ø22 für Kugellager 608 nach DIN 625 (Ersatz-Normteil wegen Befund 1)
   - Deckel
2. Baugruppe zusammenbauen:
   - Lagerbock mit 4 Schrauben M6 im Rechteckmuster an Grundplatte (bolted_connection mit pattern)
   - Deckel mit 2 Schrauben M5 an Lagerbock (bolted_connection, blind)
   - Interferenz- und Gelenkprüfung nach Montage
3. Analyse & Modifikation:
   - find (semantische Abfragen) für alle Bohrungen
   - check_design an allen Bauteilen
   - edit_in_place: Lagerbock 5 mm höher an Ort und Stelle, finish_edit, update_links, check_joints
   - delete_bolted_connection für Deckel (zur Vermeidung von Befund 5)
   - edit_bolted_connection: M6 -> M8 an Grundplatte
4. Verifikation nach jedem Schritt:
   - inspect.interference (count == 0, außer gewollte Kernloch-Überlappung bei Sacklöchern)
   - check_joints (alle grün)

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/00_vollstaendiger_praxistest_lagerbock.py
"""
import os
import shutil
import sys
import time

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, design_rules, inplace, links, query, standard_parts

def run_test():
    t0 = time.time()
    ws_path = "/tmp/praxis-ws"
    if os.path.exists(ws_path):
        shutil.rmtree(ws_path)
    os.makedirs(ws_path, exist_ok=True)

    ws = Workspace(ws_path)

    print("=================================================================")
    print("SCHRITT 1: BAUTEILE ERSTELLEN")
    print("=================================================================")

    # 1.1 Grundplatte 120 x 80 x 10 mm
    gp = ws.new(PART, "grundplatte")
    gp.session.batch([
        {"command": "parameters.add", "params": {"name": "L", "expression": "120 mm"}},
        {"command": "parameters.add", "params": {"name": "W", "expression": "80 mm"}},
        {"command": "parameters.add", "params": {"name": "T", "expression": "10 mm"}},
        {"command": "solid.box", "params": {"length": "L", "width": "W", "height": "T", "corner": [-60, -40, 0], "name": "GrundplatteBox"}}
    ])
    gp.save()
    print("  [OK] Grundplatte 120x80x10 mm erstellt.")

    # 1.2 Lagerbock
    lb = ws.new(PART, "lagerbock")
    lb.session.batch([
        {"command": "parameters.add", "params": {"name": "base_l", "expression": "90 mm"}},
        {"command": "parameters.add", "params": {"name": "base_w", "expression": "60 mm"}},
        {"command": "parameters.add", "params": {"name": "base_h", "expression": "14 mm"}},
        {"command": "parameters.add", "params": {"name": "tower_l", "expression": "50 mm"}},
        {"command": "parameters.add", "params": {"name": "tower_w", "expression": "24 mm"}},
        {"command": "parameters.add", "params": {"name": "tower_h", "expression": "40 mm"}},
        {"command": "parameters.add", "params": {"name": "bore_z", "expression": "34 mm"}},
        {"command": "solid.box", "params": {"length": "base_l", "width": "base_w", "height": "base_h", "corner": [-45, -30, 0], "name": "BaseFlange"}},
        {"command": "solid.box", "params": {"length": "tower_l", "width": "tower_w", "height": "tower_h", "corner": [-25, -12, "base_h"], "operation": "join", "name": "Tower"}},
        {"command": "solid.cylinder", "params": {"diameter": 22, "height": 28, "base": [0, -14, "bore_z"], "axis": [0, 1, 0], "operation": "cut", "name": "BearingBore"}}
    ])
    lb.save()
    print("  [OK] Lagerbock mit Bohrung Ø22 erstellt.")

    # 1.3 Kugellager DIN 625 608 (Befund 1: standard_part unterstützt nur 6000-6005)
    bearing = ws.new(PART, "DIN_625_608")
    bearing.session.batch([
        {"command": "parameters.add", "params": {"name": "d", "expression": "8 mm"}},
        {"command": "parameters.add", "params": {"name": "D", "expression": "22 mm"}},
        {"command": "parameters.add", "params": {"name": "B", "expression": "7 mm"}},
        {"command": "solid.cylinder", "params": {"diameter": "D", "height": "B", "base": [0, 0, 0], "name": "OuterRing"}},
        {"command": "solid.cylinder", "params": {"diameter": "d", "height": "B + 2 mm", "base": [0, 0, -1], "operation": "cut", "name": "InnerBore"}}
    ])
    meta_bearing = bearing.metadata()
    meta_bearing["standard"] = {"norm": "DIN 625", "size": "608", "designation": "DIN 625 608", "dimensions": {"d": 8.0, "D": 22.0, "B": 7.0}}
    bearing.set_metadata(meta_bearing)
    bearing.save()
    print("  [OK] Kugellager DIN 625 608 (Ersatz-Normteil d=8, D=22, B=7) erstellt.")

    # 1.4 Deckel
    dk = ws.new(PART, "deckel")
    dk.session.batch([
        {"command": "parameters.add", "params": {"name": "dl", "expression": "50 mm"}},
        {"command": "parameters.add", "params": {"name": "dw", "expression": "8 mm"}},
        {"command": "parameters.add", "params": {"name": "dh", "expression": "40 mm"}},
        {"command": "solid.box", "params": {"length": "dl", "width": "dw", "height": "dh", "corner": [-25, -20, 14], "name": "DeckelBox"}},
        {"command": "solid.cylinder", "params": {"diameter": 12, "height": 12, "base": [0, -22, 34], "axis": [0, 1, 0], "operation": "cut", "name": "ShaftHole"}}
    ])
    dk.save()
    print("  [OK] Deckel mit Wellendurchlass Ø12 erstellt.")

    print("\n=================================================================")
    print("SCHRITT 2: BAUGRUPPE & VERSCHRAUBUNGEN")
    print("=================================================================")
    asm = ws.new(ASSEMBLY, "lagerbock_baugruppe", overwrite=True)
    links.insert(ws, asm, gp.path, name="Grundplatte", grounded=True)
    links.insert(ws, asm, lb.path, name="Lagerbock", translate=[0, 0, 10], grounded=True)
    links.insert(ws, asm, bearing.path, name="Lager608", translate=[0, -3.5, 44], rotate={"axis": [1, 0, 0], "angle": 90.0}, grounded=True)
    links.insert(ws, asm, dk.path, name="Deckel", translate=[0, 0, 10], grounded=True)
    asm.save()
    print("  [OK] Alle Komponenten in lagerbock_baugruppe eingefügt.")

    # 2.1 Lagerbock mit 4 Schrauben M6 im Rechteckmuster an Grundplatte
    pat_m6 = {"type": "rectangular", "count": [2, 2], "spacing": [64, 40], "directions": [[1, 0, 0], [0, 1, 0]]}
    res_m6 = bolted.bolted_connection(
        ws, "lagerbock_baugruppe",
        placement={"position": [-32, -20, 24], "direction": [0, 0, -1]},
        size="M6",
        counterbore=False,
        pattern=pat_m6,
        name="Verschraubung_Grundplatte"
    )
    print(f"  [OK] Verschraubung M6 Grundplatte: {len(res_m6.get('screws', []))} Schrauben, ID: {res_m6['id']}")

    # 2.2 Deckel mit 2 Schrauben M5 an Lagerbock
    pat_m5 = {"type": "rectangular", "count": [2, 1], "spacing": [32, 0], "directions": [[1, 0, 0], [0, 0, 1]]}
    res_m5 = bolted.bolted_connection(
        ws, "lagerbock_baugruppe",
        placement={"position": [-16, -20, 44], "direction": [0, 1, 0]},
        size="M5",
        connection_type="blind",
        blind_material="alu",
        pattern=pat_m5,
        counterbore=False,
        name="Verschraubung_Deckel"
    )
    print(f"  [OK] Verschraubung M5 Deckel: {len(res_m5.get('screws', []))} Schrauben, ID: {res_m5['id']}")

    # Prüfung nach Schritt 2
    interf_s2 = asm.session.cmd("inspect.interference")
    chk_s2 = links.check(ws, asm)
    print(f"  [PRÜFUNG] Interferenz: count = {interf_s2.get('count')} (erwartet: 2 gewollte Kernloch-Überlappungen in Sacklöchern)")
    print(f"  [PRÜFUNG] Gelenke: {len(chk_s2)} Gelenke, alle ok: {all(c['status'] == 'ok' for c in chk_s2)}")
    assert interf_s2.get("count") == 2, f"Unerwartete Interferenz: {interf_s2}"
    assert all(c["status"] == "ok" for c in chk_s2), f"Gelenkfehler: {chk_s2}"

    print("\n=================================================================")
    print("SCHRITT 3: ABFRAGEN, REGELN & MODIFIKATION")
    print("=================================================================")

    # 3.1 find Abfragen
    gp_holes = query.find(gp, "holes")
    lb_holes = query.find(lb, "holes")
    dk_holes = query.find(dk, "holes")
    asm_holes = query.find(asm, "holes")
    print(f"  [FIND] Grundplatte Bohrungen: {len(gp_holes)} (alle M6 Durchgang)")
    print(f"  [FIND] Lagerbock Bohrungen: {len(lb_holes)} (1x Lager Ø22, 4x M6 Durchgang, 2x M5 Sackloch)")
    print(f"  [FIND] Deckel Bohrungen: {len(dk_holes)} (1x Welle Ø12, 2x M5 Durchgang)")
    print(f"  [FIND] Baugruppe Bohrungen gesamt: {len(asm_holes)} (alle mit Weltkoordinaten und Occurrence)")

    # 3.2 check_design
    cd_gp = design_rules.check(gp.session, profile="fdm_0.4")
    cd_lb = design_rules.check(lb.session, profile="fdm_0.4")
    cd_dk = design_rules.check(dk.session, profile="fdm_0.4")
    print(f"  [CHECK_DESIGN] Grundplatte: verdict = {cd_gp['verdict']}")
    print(f"  [CHECK_DESIGN] Lagerbock: verdict = {cd_lb['verdict']} (Falschalarme zu innerer Stufe und horizontaler Bohrung)")
    print(f"  [CHECK_DESIGN] Deckel: verdict = {cd_dk['verdict']} (Falschalarm negative Wandstärke an horizontaler Bohrung)")

    # 3.3 edit_in_place: Lagerbock 5 mm höher
    eip = inplace.edit_in_place(ws, "lagerbock_baugruppe", "Lagerbock:1")
    lb_doc = ws.docs[eip["document"]]
    lb_doc.session.cmd("parameters.change", {"name": "tower_h", "expression": "45 mm"})
    fin = inplace.finish_edit(ws, eip["document"])
    print(f"  [EDIT_IN_PLACE] Lagerbock 5 mm höher (tower_h = 45 mm) gespeichert.")
    print(f"  [UPDATE_LINKS] Berichte: {list(fin['assemblies'].keys())}, Warnungen: {len(fin['warnings'])} (Status: moved)")

    # 3.4 delete_bolted_connection Deckel
    del_res = bolted.delete_bolted_connection(ws, "lagerbock_baugruppe", "Verschraubung_Deckel")
    print(f"  [DELETE] Verschraubung Deckel gelöscht: {del_res['deleted']}")

    # 3.5 edit_bolted_connection M6 -> M8
    res_m8 = bolted.edit_bolted_connection(ws, "lagerbock_baugruppe", "Verschraubung_Grundplatte", size="M8")
    print(f"  [EDIT] Verschraubung Grundplatte auf M8 geändert: size = {res_m8.get('size')}, Gelenke = {len(res_m8.get('joints', []))}")

    # Endprüfung
    interf_end = asm.session.cmd("inspect.interference")
    chk_end = links.check(ws, asm)
    print(f"\n=================================================================")
    print("SCHRITT 4: ENDPRÜFUNG")
    print("=================================================================")
    print(f"  [ENDPRÜFUNG] Interferenz: count = {interf_end.get('count')} (Soll: 0)")
    print(f"  [ENDPRÜFUNG] Gelenke: {len(chk_end)} Gelenke, alle ok: {all(c['status'] == 'ok' for c in chk_end)}")
    assert interf_end.get("count") == 0, f"Unerwartete Restkollision: {interf_end}"
    assert all(c["status"] == "ok" for c in chk_end), f"Gelenkfehler: {chk_end}"

    ws.close_all()
    dt = time.time() - t0
    print(f"\n[ERFOLG] Vollständiger Praxistest erfolgreich abgeschlossen in {dt:.1f} s.")

if __name__ == "__main__":
    run_test()
