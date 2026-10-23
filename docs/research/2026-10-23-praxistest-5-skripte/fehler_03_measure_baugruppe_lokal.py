"""Befund 4: measure(assembly) liefert bbox/Schwerpunkt in Bauteilkoordinaten, nicht in Weltkoordinaten
(Doku: 'bounding box of every body'; find() liefert in Baugruppen Weltkoordinaten).
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_03_measure_baugruppe_lokal.py"""
import shutil, sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace, PART, ASSEMBLY
shutil.rmtree("/tmp/praxis5-rep3", ignore_errors=True)
ws = Workspace("/tmp/praxis5-rep3"); server.ws = ws
b = ws.new(PART, "block")
server.run("block", [{"command": "solid.box", "params": {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 0],
                                                          "operation": "new", "body_name": "Block", "name": "B"}}])
b.save()
ws.new(ASSEMBLY, "asm")
server.insert_part("asm", "block.solidcraft", name="Block", translate=[100, 0, 50], grounded=True)
m = server.measure("asm")["bodies"][0]
print("measure(asm) bbox:", m["bbox"], "CoM:", m["center_of_mass"])
print("find faces (Welt):", [f["pick"] for f in server.find("asm", "faces", {"normal": "+Z"})["items"]])
print("Erwartet bbox min [100,0,50] max [110,10,60]")
ws.close_all()
