"""Befund 6: motion.interference meldet Kollisionen (clear: false) fuer sich nur beruehrende, koaxiale Teile
(volume_mm3 0.0, depth <= 0.08 mm), waehrend inspect.interference am selben Modell count 0 liefert.
Benoetigt /tmp/praxis5-ws (bau_01, bau_02, optional aender_05).
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_06_motion_interference_fehlalarm.py"""
import sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace
ws = Workspace("/tmp/praxis5-ws"); server.ws = ws
asm = ws.open("lagerung.solidcraft"); s = asm.session
occ = ["Welle:1", "Lager608:1", "Lager6000:1", "BockL:1", "BockR:1", "Platte:1"]
r = s.cmd("inspect.interference", {"bodies": ["Welle", "Bearing", "Bearing (2)", "lagerbock_l", "lagerbock_r", "Grundplatte"]})
print("inspect.interference count:", r["count"])
s.cmd("motion.study", {"name": "Drehung90", "steps": 9, "keys": [{"joint": "Welle_in_608", "points": [[0, 0], [9, 90]]}]})
m = s.cmd("motion.interference", {"study": "Drehung90", "occurrences": occ})
print("motion.interference clear:", m["clear"], "truncated:", m.get("truncated"), "checked_to:", m.get("checked_to"), "samples:", m["samples"], "pairs:", m["pairs"])
for c in m["collisions"]:
    print("  ", c["a"], c["b"], "depth_mm", round(c["depth_mm"], 3), "volume_mm3", c["volume_mm3"], "steps", c["steps"])
ws.close_all()
