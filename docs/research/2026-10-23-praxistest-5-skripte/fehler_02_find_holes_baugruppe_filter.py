"""Befund 2 und 3: find(holes) in einer Baugruppe mit diameter-Filter liefert 0 Treffer; 'through' ist bei
durchgehenden Bohrungen aus bolted_connection false.
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_02_find_holes_baugruppe_filter.py"""
import shutil, sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace, PART, ASSEMBLY
shutil.rmtree("/tmp/praxis5-rep2", ignore_errors=True)
ws = Workspace("/tmp/praxis5-rep2"); server.ws = ws
b = ws.new(PART, "block")
server.run("block", [{"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0],
                                                          "operation": "new", "body_name": "Block", "name": "B"}},
                     {"command": "solid.hole", "params": {"position": [20, 20, 10], "diameter": 8, "name": "Loch"}}])
b.save()
a = ws.new(ASSEMBLY, "asm")
server.insert_part("asm", "block.solidcraft", name="Block", grounded=True)
for lab, doc, where in (("Bauteil ohne Filter", "block", None), ("Bauteil diameter [7,9]", "block", {"diameter": [7, 9]}),
                        ("Baugruppe ohne Filter", "asm", None), ("Baugruppe diameter [7,9]", "asm", {"diameter": [7, 9]}),
                        ("Baugruppe diameter 8", "asm", {"diameter": 8})):
    r = server.find(doc, "holes", where)
    print(f"{lab}: count={r['count']}", [(h['diameter'], h['through']) for h in r["items"]])
print("Erwartet: Baugruppe mit Filter ebenfalls 1 Treffer; Bohrung geht durch (z 0..10), through muss true sein")
# 'through' bei Verschraubungsbohrung
b2 = ws.new(PART, "block2")
server.run("block2", [{"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0],
                                                           "operation": "new", "body_name": "Block2", "name": "B"}}])
b2.save()
server.insert_part("asm", "block2.solidcraft", name="Block2", translate=[0, 0, -10], grounded=True)
server.bolted_connection("asm", {"position": [5, 5, 10], "direction": [0, 0, -1]}, "M5", counterbore=True, name="S")
for h in server.find("block", "holes", {"feature": "Hole_M5_CB"})["items"]:
    print("block:", h["name"], "Ø", h["diameter"], "depth", h["depth"], "through", h["through"])
print("Block ist 10 mm dick; die Bohrung Ø5.5 mündet unten aus (Tiefe 10 gesamt), through sollte true sein")
ws.close_all()
