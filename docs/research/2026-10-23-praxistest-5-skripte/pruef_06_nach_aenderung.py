"""Praxistest 5: Zustand nach aender_05.py: wo liegen Bohrungen und Schrauben?
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/pruef_06_nach_aenderung.py"""
import json, sys
sys.path.insert(0, ".")
from mechvane import links, server
from mechvane.documents import Workspace
ws = Workspace("/tmp/praxis5-ws"); server.ws = ws
for n in ("grundplatte", "lagerbock_r", "lagerbock_l"):
    ws.open(f"{n}.solidcraft")
asm = ws.open("lagerung.solidcraft")
for n in ("grundplatte", "lagerbock_r"):
    print(n, sorted({(h["name"], h["diameter"], tuple(round(c, 1) for c in h["pick"])) for h in server.find(n, "holes")["items"]}))
for o in links._occurrences(asm.session).values():
    if o["name"].startswith(("SchrR", "SchrL")) and o["name"].endswith("Screw:1"):
        print(o["name"], "pos (Zeile 3 der Matrix):", [round(x, 2) for x in o["transform"][3][:3]])
r = server.list_bolted_connections("lagerung")
print(type(r), json.dumps(r, default=str)[:1500])
ws.close_all()
