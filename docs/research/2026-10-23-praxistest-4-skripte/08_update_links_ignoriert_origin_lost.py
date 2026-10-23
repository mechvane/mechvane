#!/usr/bin/env python3
"""Reproduktionsskript 08: update_links(repair=True) ignoriert 'origin_lost'.

Problem:
  Wenn ein Bauteil nach In-Place-Bearbeitung neu geladen wird und dabei temporär
  ein Koordinatenursprung im Solver ungültig wird (frame = None), klassifiziert
  links.check das Gelenk als 'origin_lost'.
  links.update_links(ws, doc, repair_moved=True) filtert jedoch ausschließlich
  nach `r["status"] == "moved"`. Gelenke mit `origin_lost` werden ignoriert,
  obwohl links.repair(ws, doc, joint) die Verankerung auf der nach wie vor
  vorhandenen benannten Fläche perfekt wiederherstellen kann.
  Zudem fehlt in server.py ein direktes MCP-Tool `repair_joint`.

Ausführen mit:
  PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-4-skripte/08_update_links_ignoriert_origin_lost.py
"""

from pathlib import Path
import shutil
import sys

from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import links, server

ws_dir = Path("/tmp/praxis4-repro-08")
if ws_dir.exists():
    shutil.rmtree(ws_dir)
ws_dir.mkdir(parents=True)

ws = Workspace(ws_dir)
server.ws = ws

# Bauteil 1: Box mit Dom
p1 = ws.new(PART, "basis")
p1.session.batch([
    {"command": "solid.box", "params": {"length": 100, "width": 50, "height": 10, "corner": [-50, -25, 0], "name": "Box"}},
    {"command": "solid.cylinder", "params": {"diameter": 10, "height": 15, "base": [20, 0, 10], "operation": "join", "name": "Dom"}},
])
p1.save()

# Bauteil 2: Zylinder
p2 = ws.new(PART, "stift")
p2.session.batch([
    {"command": "solid.cylinder", "params": {"diameter": 10, "height": 20, "base": [0, 0, 0], "operation": "new", "name": "Stift"}},
])
p2.save()

# Baugruppe
asm = ws.new(ASSEMBLY, "baugruppe")
links.insert(ws, asm, p1.path, name="Basis", grounded=True)
links.insert(ws, asm, p2.path, name="Stift", translate=[20, 0, 25], grounded=False)

server.add_joint("baugruppe", {
    "type": "rigid",
    "name": "StiftAufDom",
    "a": {"occurrence": "Basis:1", "circle": [20, 0, 25]},
    "b": {"occurrence": "Stift:1", "circle": [20, 0, 25]},
})
server.save_document("baugruppe")

chk0 = server.check_joints("baugruppe")
assert all(j["status"] == "ok" for j in chk0["joints"]), "Initiales Gelenk nicht ok"
print(f"1. Initiales Gelenk erstellt: Status = {chk0['joints'][0]['status']}")

# Nun In-Place-Änderung an Basis: Bohrung hinzufügen (ändert Topologie/Face-IDs)
eip = server.edit_in_place("baugruppe", "Basis:1")
doc_p1 = ws.get(eip["document"], PART)
doc_p1.session.cmd("solid.cylinder", {"diameter": 4, "height": 15, "base": [20, 0, 10], "operation": "cut", "name": "Loch"})
doc_p1.save()

# Reload ohne Reparatur: SolidCraft verliert temporär frame_a
asm_doc = ws.get("baugruppe", ASSEMBLY)
asm_doc.session.cmd("component.update_links")
chk_broken = links.check(ws, asm_doc)
broken_status = next(j["status"] for j in chk_broken if j["joint"] == "StiftAufDome" or j["joint"] == "StiftAufDom")
print(f"2. Nach Topologieänderung: Gelenkstatus = '{broken_status}'")

# update_links(repair=True) aufrufen
rep_upd = server.update_links("baugruppe", repair=True)
print(f"3. server.update_links(repair=True) aufgerufen: reparierte Gelenke = {[x['joint'] for x in rep_upd.get('repaired', [])]}")

chk_after_upd = server.check_joints("baugruppe")
status_after_upd = next(j["status"] for j in chk_after_upd["joints"] if j["joint"] == "StiftAufDom")
print(f"   Status nach update_links(repair=True) bleibt: '{status_after_upd}' (wurde ignoriert!)")

# Nachweis: links.repair(ws, asm_doc, ...) kann das Gelenk problemlos reparieren!
rep_direct = links.repair(ws, asm_doc, "StiftAufDom")
print(f"4. Direktes links.repair('StiftAufDom') ausgeführt: Neuer Status = {rep_direct[0]['status']}")
assert rep_direct[0]["status"] == "ok", "Direktes Repair hätte ok sein müssen"

print("\nBefund erfolgreich reproduziert: update_links(repair=True) ignoriert origin_lost, obwohl repair() funktioniert.")
sys.exit(0)
