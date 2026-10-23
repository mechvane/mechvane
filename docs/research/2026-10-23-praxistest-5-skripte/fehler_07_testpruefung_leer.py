"""Befund 7: tests/mechvane/check.py Zeilen 949-956 ('screw sits coaxial to hole', Weltkoordinaten) lesen die
Verschiebung mit t[0][3]/t[1][3]. Inventas Transformationen sind Zeilenvektor-Matrizen (Translation in Zeile 3,
siehe geometry.apply_point), t[0][3] ist die homogene Spalte und immer 0: die Pruefung ist leer erfuellt.
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_07_testpruefung_leer.py"""
import shutil, sys
sys.path.insert(0, ".")
from mechvane import links, server
from mechvane.documents import Workspace, PART, ASSEMBLY
shutil.rmtree("/tmp/praxis5-rep7", ignore_errors=True)
ws = Workspace("/tmp/praxis5-rep7"); server.ws = ws
b = ws.new(PART, "block")
server.run("block", [{"command": "solid.box", "params": {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 0],
                                                          "operation": "new", "body_name": "Block", "name": "B"}}])
b.save()
a = ws.new(ASSEMBLY, "asm")
server.insert_part("asm", "block.solidcraft", name="Block", translate=[7, 3, 50], grounded=True)
t = next(iter(links._occurrences(a.session).values()))["transform"]
print("Matrix:", [[round(x, 3) for x in r] for r in t])
print("Translation tatsaechlich (Zeile 3):", t[3][:3], "| was check.py liest, t[0][3], t[1][3]:", t[0][3], t[1][3])
ws.close_all()
