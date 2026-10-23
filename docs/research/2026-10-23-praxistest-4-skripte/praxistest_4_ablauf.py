#!/usr/bin/env python3
"""Vollständiger Praxistest 4: 3D-Druck-Elektronikgehäuse mit Unterbaugruppe und Schraubverbindungen.

Ausführen mit:
  PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/praxistest_4_ablauf.py
"""

import os
import shutil
import sys
import time
from pathlib import Path

ws_dir = Path("/tmp/praxis4-ws")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import bolted, design_rules, hole_tables, inplace, links, query, server, standard_parts

ws = Workspace(ws_dir)
server.ws = ws

print("================================================================================")
print("PRAXISTEST 4: 3D-DRUCK-ELEKTRONIKGEHÄUSE")
print("================================================================================")
t0 = time.time()

# -----------------------------------------------------------------------------
# SCHRITT 1: BAUTEILE & UNTERBAUGRUPPE ERSTELLEN
# -----------------------------------------------------------------------------
print("\n--- SCHRITT 1: Bauteile & Unterbaugruppe modellieren ---")

# 1.1 Gehäuseunterteil: 100 x 70 x 35 mm, Wand 2.5 mm, 4 Dome
# Dome an den Positionen [±dx, ±dy], dx = L/2 - 15 mm, dy = W/2 - 15 mm
# Boden bei Z=0..2.5 mm, Kavität Z=2.5..35 mm.
# Dome: Höhe 32.5 mm (Z=2.5..35 mm, schließt bündig mit der Gehäuseoberkante ab).
gehaeuse = ws.new(PART, "gehaeuse_unterteil")
gehaeuse.session.batch([
    {"command": "parameters.add", "params": {"name": "L", "expression": "100 mm"}},
    {"command": "parameters.add", "params": {"name": "W", "expression": "70 mm"}},
    {"command": "parameters.add", "params": {"name": "H", "expression": "35 mm"}},
    {"command": "parameters.add", "params": {"name": "wall", "expression": "2.5 mm"}},
    {"command": "parameters.add", "params": {"name": "dx", "expression": "L/2 - 15 mm"}},
    {"command": "parameters.add", "params": {"name": "dy", "expression": "W/2 - 15 mm"}},
    {"command": "solid.box", "params": {"length": "L", "width": "W", "height": "H", "corner": ["-L/2", "-W/2", 0], "name": "Aussenkoerper"}},
    {"command": "solid.box", "params": {"length": "L - 2*wall", "width": "W - 2*wall", "height": "H - wall + 1 mm", "corner": ["-(L - 2*wall)/2", "-(W - 2*wall)/2", "wall"], "operation": "cut", "name": "Kavitaet"}},
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": "H - wall", "base": ["dx", "dy", "wall"], "operation": "join", "name": "Dom1"}},
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": "H - wall", "base": ["-dx", "dy", "wall"], "operation": "join", "name": "Dom2"}},
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": "H - wall", "base": ["-dx", "-dy", "wall"], "operation": "join", "name": "Dom3"}},
    {"command": "solid.cylinder", "params": {"diameter": 8, "height": "H - wall", "base": ["dx", "-dy", "wall"], "operation": "join", "name": "Dom4"}},
])
gehaeuse.save()
meas_g = server.measure("gehaeuse_unterteil")
print(f"1.1 Gehäuseunterteil gespeichert: Volumen = {meas_g['bodies'][0]['volume_mm3']:.2f} mm³")

# 1.2 Deckel: 100 x 70 x 3 mm
deckel = ws.new(PART, "deckel")
deckel.session.batch([
    {"command": "parameters.add", "params": {"name": "L", "expression": "100 mm"}},
    {"command": "parameters.add", "params": {"name": "W", "expression": "70 mm"}},
    {"command": "parameters.add", "params": {"name": "T", "expression": "3 mm"}},
    {"command": "solid.box", "params": {"length": "L", "width": "W", "height": "T", "corner": ["-L/2", "-W/2", 0], "name": "DeckelKoerper"}},
])
deckel.save()
meas_d = server.measure("deckel")
print(f"1.2 Deckel gespeichert: Volumen = {meas_d['bodies'][0]['volume_mm3']:.2f} mm³")

# 1.3 Platine: 80 x 50 x 1.6 mm mit 4 Bohrungen bei (±35, ±20)
platine = ws.new(PART, "platine")
platine.session.batch([
    {"command": "solid.box", "params": {"length": 80, "width": 50, "height": 1.6, "corner": [-40, -25, 0], "name": "PlatinenKoerper"}},
    {"command": "solid.cylinder", "params": {"diameter": 3.4, "height": 3.6, "base": [35, 20, -1], "operation": "cut", "name": "Loch1"}},
    {"command": "solid.cylinder", "params": {"diameter": 3.4, "height": 3.6, "base": [-35, 20, -1], "operation": "cut", "name": "Loch2"}},
    {"command": "solid.cylinder", "params": {"diameter": 3.4, "height": 3.6, "base": [-35, -20, -1], "operation": "cut", "name": "Loch3"}},
    {"command": "solid.cylinder", "params": {"diameter": 3.4, "height": 3.6, "base": [35, -20, -1], "operation": "cut", "name": "Loch4"}},
])
platine.save()
meas_p = server.measure("platine")
print(f"1.3 Platine gespeichert: Volumen = {meas_p['bodies'][0]['volume_mm3']:.2f} mm³")

# 1.4 Abstandsbolzen: Ø 6 mm, Höhe 10 mm, Kernbohrung Ø 3.4 mm
bolzen = ws.new(PART, "abstandsbolzen")
bolzen.session.batch([
    {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [0, 0, 0], "operation": "new", "name": "BolzenKoerper"}},
    {"command": "solid.cylinder", "params": {"diameter": 3.4, "height": 12, "base": [0, 0, -1], "operation": "cut", "name": "Durchgang"}},
])
bolzen.save()
meas_b = server.measure("abstandsbolzen")
print(f"1.4 Abstandsbolzen gespeichert: Volumen = {meas_b['bodies'][0]['volume_mm3']:.2f} mm³")

# 1.5 Unterbaugruppe: Platine + 4 Bolzen
sub = ws.new(ASSEMBLY, "platine_unterbaugruppe")
links.insert(ws, sub, platine.path, name="Platine", grounded=True)
links.insert(ws, sub, bolzen.path, name="Bolzen1", translate=[35, 20, -10], grounded=False)
links.insert(ws, sub, bolzen.path, name="Bolzen2", translate=[-35, 20, -10], grounded=False)
links.insert(ws, sub, bolzen.path, name="Bolzen3", translate=[-35, -20, -10], grounded=False)
links.insert(ws, sub, bolzen.path, name="Bolzen4", translate=[35, -20, -10], grounded=False)

sub.session.cmd("joint.create", {"type": "rigid", "name": "Bolzen1Joint", "a": {"occurrence": "Platine:1", "circle": [35, 20, 0]}, "b": {"occurrence": "Bolzen1:1", "circle": [35, 20, 0]}})
links.record(ws, sub, "Bolzen1Joint")
sub.session.cmd("joint.create", {"type": "rigid", "name": "Bolzen2Joint", "a": {"occurrence": "Platine:1", "circle": [-35, 20, 0]}, "b": {"occurrence": "Bolzen2:1", "circle": [-35, 20, 0]}})
links.record(ws, sub, "Bolzen2Joint")
sub.session.cmd("joint.create", {"type": "rigid", "name": "Bolzen3Joint", "a": {"occurrence": "Platine:1", "circle": [-35, -20, 0]}, "b": {"occurrence": "Bolzen3:1", "circle": [-35, -20, 0]}})
links.record(ws, sub, "Bolzen3Joint")
sub.session.cmd("joint.create", {"type": "rigid", "name": "Bolzen4Joint", "a": {"occurrence": "Platine:1", "circle": [35, -20, 0]}, "b": {"occurrence": "Bolzen4:1", "circle": [35, -20, 0]}})
links.record(ws, sub, "Bolzen4Joint")
sub.save()
print("1.5 Unterbaugruppe gespeichert (Platine + 4 Bolzen mit 4 starren Gelenken)")

# 1.6 Hauptbaugruppe
main_asm = ws.new(ASSEMBLY, "elektronikgehaeuse")
links.insert(ws, main_asm, gehaeuse.path, name="Gehaeuse", grounded=True)
links.insert(ws, main_asm, sub.path, name="Elektronik", translate=[0, 0, 15], grounded=False)
links.insert(ws, main_asm, deckel.path, name="Deckel", translate=[0, 0, 35], grounded=False)

# Unterbaugruppe per add_joint auf die Dome setzen (an die unberührte Zylinderfläche von Dom1 bei Z=2.5)
j_sub = server.add_joint("elektronikgehaeuse", {
    "type": "rigid",
    "name": "ElektronikAufDome",
    "a": {"occurrence": "Gehaeuse:1", "circle": [35, 20, 2.5]},
    "b": {"occurrence": "Elektronik:1/Bolzen1:1", "circle": [35, 20, 5]},
})
server.save_document("elektronikgehaeuse")
print(f"1.6 Hauptbaugruppe erstellt, Unterbaugruppe per add_joint auf Dom gesetzt (Verankerung: {j_sub['anchors']['a']['face']})")

# 1.7 Bolted Connection: Ruthex M3 Rechteckmuster
# Versuch mit counterbore=True dokumentieren (Befund 1)
try:
    bolted.bolted_connection(
        ws, "elektronikgehaeuse",
        placement={"position": [-35, -20, 38], "direction": [0, 0, -1]},
        size="M3",
        use_insert=True,
        counterbore=True,
        pattern={"type": "rectangular", "count": [2, 2], "spacing": [70, 40]},
        parts=["Deckel:1", "Gehaeuse:1"],
    )
except ValueError as e:
    print(f"  [Hinweis Befund 1] counterbore=True bei 3 mm Deckel wie erwartet abgewiesen: {e}")

# Ausführung mit counterbore=False
res_bolt = bolted.bolted_connection(
    ws, "elektronikgehaeuse",
    placement={"position": [-35, -20, 38], "direction": [0, 0, -1]},
    size="M3",
    use_insert=True,
    counterbore=False,
    pattern={"type": "rectangular", "count": [2, 2], "spacing": [70, 40]},
    parts=["Deckel:1", "Gehaeuse:1"],
)
server.save_document("elektronikgehaeuse")
print(f"1.7 bolted_connection M3 Ruthex angelegt: {res_bolt['id']}, Schraubenlänge {res_bolt['screw_length']} mm, 4 Einsätze")

# Prüfung Schritt 1: Interferenz & Gelenke
interf_1 = main_asm.session.cmd("inspect.interference")
ruthex_interf = [it for it in interf_1.get("interferences", []) if "Insert" in it["a"] or "Insert" in it["b"]]
other_interf = [it for it in interf_1.get("interferences", []) if it not in ruthex_interf]
print(f"1.8 Interferenz-Prüfung Schritt 1: {len(ruthex_interf)} gewollte Ruthex-Einschmelzungen, {len(other_interf)} ungewollte Kollisionen")
for it in ruthex_interf:
    print(f"    Gewollte Interferenz: {it['a']} <-> {it['b']}, Volumen = {it['volume_mm3']:.2f} mm³")

chk_j_1 = server.check_joints("elektronikgehaeuse")
print(f"1.9 Gelenke-Prüfung Schritt 1: {len(chk_j_1['joints'])} Gelenke, alle ok: {all(j['status'] == 'ok' for j in chk_j_1['joints'])}")

# Speichern, schließen und neu öffnen
server.save_document("elektronikgehaeuse")
server.close_document("elektronikgehaeuse")
server.open_document("elektronikgehaeuse.solidcraft")
chk_j_reopen = server.check_joints("elektronikgehaeuse")
conns_reopen = server.list_bolted_connections("elektronikgehaeuse")
print(f"1.10 Nach Speichern/Schließen/Öffnen: {len(chk_j_reopen['joints'])} Gelenke ok, {conns_reopen['count']} Verschraubung(en) persistent")

# -----------------------------------------------------------------------------
# SCHRITT 2: CHECK_DESIGN & FIND AN ALLEN BAUTEILEN
# -----------------------------------------------------------------------------
print("\n--- SCHRITT 2: check_design und find an allen Bauteilen ---")

parts_to_check = ["gehaeuse_unterteil", "deckel", "platine", "abstandsbolzen"]
for p in parts_to_check:
    res_cd = server.check_design(p, profile="fdm_0.4")
    print(f"2.1 check_design('{p}'): verdict = {res_cd['verdict']}")
    for rname, rdata in res_cd["rules"].items():
        if rdata["status"] != "ok":
            for f in rdata["findings"]:
                if f["status"] != "ok":
                    print(f"    Regel {rname} [{f['status']}]: {f['message']}")

print("\n2.2 Semantische Abfragen (find):")
f_domes = server.find("gehaeuse_unterteil", "faces", where={"type": "cylinder"})
print(f"  Gehäuseunterteil zylindrische Flächen (Dome/Bohrungen): {f_domes['count']} Flächen gefunden")
f_holes_g = server.find("gehaeuse_unterteil", "holes")
print(f"  Gehäuseunterteil Bohrungen laut find: {f_holes_g['count']} (Hinweis Befund 2: Außendome als Bohrungen gelistet)")
for h in f_holes_g["holes"]:
    print(f"    Bohrung/Dom Ø {h['diameter']:.1f} mm bei {h['center']}")

f_holes_p = server.find("platine", "holes")
print(f"  Platine Bohrungen: {f_holes_p['count']} Bohrungen Ø 3.4 mm gefunden")

f_asm_holes = server.find("elektronikgehaeuse", "holes")
print(f"  Hauptbaugruppe Bohrungen gesamt: {f_asm_holes['count']} Bohrungen in Baugruppe identifiziert")

# -----------------------------------------------------------------------------
# SCHRITT 3: ÄNDERUNG, EDIT_IN_PLACE, BOLTED EDIT & DELETE
# -----------------------------------------------------------------------------
print("\n--- SCHRITT 3: Änderung Gehäuse +10 mm, edit_bolted_connection, delete & neu ---")

# 3.1 Vor Änderung: Position messen
occs_pre = links._occurrences(ws.get("elektronikgehaeuse", ASSEMBLY).session)
b1_x_pre = occs_pre[next(k for k, v in occs_pre.items() if v["name"] == "Bolzen1:1")]["transform"][3][0]
print(f"3.1 Vor Änderung: X-Position Bolzen1 = {b1_x_pre:.2f} mm")

# 3.2 edit_in_place
eip = server.edit_in_place("elektronikgehaeuse", "Gehaeuse:1")
print(f"3.2 edit_in_place geöffnet: Dokument '{eip['document']}'")

# Gehäuse um 10 mm verlängern (L: 100 mm -> 110 mm)
part_g = ws.get(eip["document"], PART)
part_g.session.cmd("parameters.change", {"name": "L", "expression": "110 mm"})

# 3.3 finish_edit
fed = server.finish_edit(eip["document"], update=True)
print(f"3.3 finish_edit ausgeführt, update_links aufgerufen (Warnungen: {len(fed['warnings'])})")
for w in fed["warnings"]:
    print(f"    Warnung {w['joint']}: status = {w['status']}, face = {w.get('face')}")

# update_links mit repair=True repariert verschobene Gelenke der Baugruppe
upd = server.update_links("elektronikgehaeuse", repair=True)
print(f"3.3b server.update_links(repair=True) ausgeführt: Repariert: {[x['joint'] for x in upd.get('repaired', [])]}")
chk_after_upd = server.check_joints("elektronikgehaeuse")
print(f"     Gelenke nach Reparatur: {len(chk_after_upd['joints'])} Gelenke geprüft")

# 3.4 Prüfung: Unterbaugruppe muss gefolgt sein
occs_post = links._occurrences(ws.get("elektronikgehaeuse", ASSEMBLY).session)
b1_x_post = occs_post[next(k for k, v in occs_post.items() if v["name"] == "Bolzen1:1")]["transform"][3][0]
print(f"3.4 Nach Verlängerung L=110 mm: X-Position Bolzen1 = {b1_x_post:.2f} mm (Verschiebung: +{b1_x_post - b1_x_pre:.2f} mm)")
assert abs(b1_x_post - 40.0) < 0.1, f"Bolzen1 sollte bei X=40.0 sein, ist bei {b1_x_post}"

# 3.5 edit_bolted_connection M3 -> M4
print("\n3.5 Ändern der Verschraubung M3 -> M4 (inklusive Anpassung der Koordinaten an L=110 mm):")
edit_res = bolted.edit_bolted_connection(
    ws, "elektronikgehaeuse", res_bolt["id"],
    size="M4",
    pattern={"type": "rectangular", "count": [2, 2], "spacing": [80, 40]},
    placement={"position": [-40, -20, 38], "direction": [0, 0, -1]},
)
server.save_document("elektronikgehaeuse")
print(f"    edit_bolted_connection erfolgreich: Größe {edit_res['size']}, Aufnahmebohrung Ø {edit_res['mounting_hole_diameter']} mm, Tiefe {edit_res['mounting_hole_depth']} mm")
assert edit_res["size"] == "M4"
assert edit_res["mounting_hole_diameter"] == 5.6
assert edit_res["mounting_hole_depth"] == 9.1

interf_m4 = ws.get("elektronikgehaeuse", ASSEMBLY).session.cmd("inspect.interference")
print(f"    Interferenzen bei M4: {interf_m4.get('count', 0)} (4 gewollte Ruthex M4 Einschmelzungen)")

# 3.6 delete_bolted_connection
print("\n3.6 Löschen der Verschraubung M4:")
del_res = bolted.delete_bolted_connection(ws, "elektronikgehaeuse", res_bolt["id"])
server.save_document("elektronikgehaeuse")
print(f"    delete_bolted_connection erfolgreich: {del_res['deleted']} entfernt, gelöschte Gelenke: {len(del_res['removed_joints'])}, gelöschte Bohrungen: {del_res['removed_holes']}")

# 3.7 Neuanlage ohne Einsätze: Sacklochverschraubung
print("\n3.7 Neuanlage Sacklochverschraubung:")
# Test mit PLA (Befund 4)
try:
    bolted.bolted_connection(
        ws, "elektronikgehaeuse",
        placement={"position": [-40, -20, 38], "direction": [0, 0, -1]},
        size="M3",
        connection_type="blind",
        blind_material="PLA",
        counterbore=False,
        pattern={"type": "rectangular", "count": [2, 2], "spacing": [80, 40]},
        parts=["Deckel:1", "Gehaeuse:1"],
    )
except ValueError as e:
    print(f"    [Hinweis Befund 4] blind_material='PLA' abgewiesen: {e}")

# Ausführung mit 'plastic'
res_blind = bolted.bolted_connection(
    ws, "elektronikgehaeuse",
    placement={"position": [-40, -20, 38], "direction": [0, 0, -1]},
    size="M3",
    connection_type="blind",
    blind_material="plastic",
    counterbore=False,
    pattern={"type": "rectangular", "count": [2, 2], "spacing": [80, 40]},
    parts=["Deckel:1", "Gehaeuse:1"],
)
server.save_document("elektronikgehaeuse")
print(f"    Sacklochverschraubung (plastic) angelegt: Typ {res_blind['type']}, Schraubenlänge {res_blind['screw_length']} mm, Sacklochtiefe {res_blind.get('drill_depth')} mm")

# -----------------------------------------------------------------------------
# SCHRITT 4: ENDPRÜFUNG, INTERFERENZ, GELENKE & PERSISTENZ
# -----------------------------------------------------------------------------
print("\n--- SCHRITT 4: Endprüfung, Interferenz, Gelenke & Persistenz ---")

interf_final = ws.get("elektronikgehaeuse", ASSEMBLY).session.cmd("inspect.interference")
print(f"4.1 Endprüfung Interferenz: count = {interf_final.get('count', 0)}")
chk_j_final = server.check_joints("elektronikgehaeuse")
print(f"4.2 Endprüfung Gelenke vor Reparatur: {len(chk_j_final['joints'])} Gelenke, alle ok: {all(j['status'] == 'ok' for j in chk_j_final['joints'])}")

# Wenn ein Gelenk nach Neuanlage der Sacklochbohrungen 'origin_lost' hat (Befund 8):
broken = [j for j in chk_j_final["joints"] if j["status"] != "ok"]
if broken:
    print(f"    [Hinweis Befund 8] Gelenke mit status != 'ok': {[b['joint'] + ' (' + b['status'] + ')' for b in broken]}")
    for b in broken:
        rep_j = links.repair(ws, ws.get("elektronikgehaeuse", ASSEMBLY), b["joint"])
        print(f"    Gelenk '{b['joint']}' per links.repair repariert: status = {rep_j[0]['status']}")

chk_j_repaired = server.check_joints("elektronikgehaeuse")
print(f"4.2b Gelenke nach gezielter Reparatur: alle ok: {all(j['status'] == 'ok' for j in chk_j_repaired['joints'])}")

# Speichern, schließen und erneut öffnen
server.save_document("elektronikgehaeuse")
server.close_document("elektronikgehaeuse")
opened = server.open_document("elektronikgehaeuse.solidcraft")
chk_j_end = server.check_joints("elektronikgehaeuse")
conns_end = server.list_bolted_connections("elektronikgehaeuse")

print(f"4.3 Nach save_document/close/open: {conns_end['count']} Verschraubung(en), {len(chk_j_end['joints'])} Gelenke intakt")
assert conns_end["count"] == 1
assert all(j["status"] == "ok" for j in chk_j_end["joints"])

# Screenshot headless speichern
try:
    shot = server.screenshot("elektronikgehaeuse", view="iso", path="/tmp/praxis4-ws/elektronikgehaeuse.png")
    print(f"4.4 Screenshot headless erzeugt: {shot.get('path')} ({shot.get('bytes')} Bytes)")
except Exception as e:
    print(f"4.4 Screenshot nicht möglich: {e}")

dt = time.time() - t0
print(f"\nPraxistest 4 erfolgreich in {dt:.1f} Sekunden abgeschlossen!")
print("================================================================================")
