"""Befund 1: check_design wertet die AUSSEN-Zylinder einer gedrehten Welle als Bohrungen (Fehlalarm).
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_01_check_design_welle.py
Erwartet: ok (eine Welle hat keine Bohrungen). Tatsaechlich: fail mit 'hole Ø ...' auf Zylinder-Aussenflaechen."""
import shutil, sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace, PART
shutil.rmtree("/tmp/praxis5-rep1", ignore_errors=True)
ws = Workspace("/tmp/praxis5-rep1"); server.ws = ws
ws.new(PART, "welle")
server.run("welle", [
    {"command": "sketch.create", "params": {"plane": "XZ", "name": "P"}},
    {"command": "sketch.line", "params": {"closed": True, "points": [[0, 0], [0, 4], [20, 4], [20, 6], [60, 6], [60, 0]]}},
    {"command": "sketch.finish", "params": {}},
    {"command": "solid.revolve", "params": {"sketch": "P", "axis": "X", "operation": "new", "body_name": "Welle", "name": "R"}}])
r = server.check_design("welle")
print("revolve Welle Ø8/Ø12:", r["verdict"], "|", r["summary"])
for c in r["checks"]:
    if c["status"] != "ok":
        print("  ", c["rule"], c["status"], c["message"], c["location"]["face"])
ws.new(PART, "zyl")
server.run("zyl", [{"command": "solid.cylinder", "params": {"diameter": 12, "height": 60, "base": [30, 30, 0], "name": "Z"}}])
r = server.check_design("zyl")
print("solid.cylinder Ø12 (Vollzylinder):", r["verdict"], "|", r["summary"])
ws.close_all()
