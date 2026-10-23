"""Praxistest 5, Schritt 2b: Freiheitsgrade, Antrieb um 90 Grad, Bewegungsstudie, Interferenz in Drehstellung.
Lauf (nach bau_02): PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/pruef_04_bewegung.py"""
import json
import sys

sys.path.insert(0, ".")
from mechvane import links, server  # noqa: E402
from mechvane.documents import Workspace  # noqa: E402

ws = Workspace("/tmp/praxis5-ws")
server.ws = ws


def show(label, v, n=1500):
    print(f"--- {label}\n{json.dumps(v, ensure_ascii=False, default=str)[:n]}", flush=True)


def tr(s):
    return {o["name"]: [round(o["transform"][i][3], 3) for i in range(3)] for o in links._occurrences(s).values()
            if o["name"] in ("Welle:1", "Lager608:1", "Lager6000:1")}


def rot(s, name):
    o = next(o for o in links._occurrences(s).values() if o["name"] == name)
    return [[round(x, 3) for x in row] for row in o["transform"]]


asm = ws.open("lagerung.solidcraft")
s = asm.session
show("transforms vor Antrieb", tr(s))
show("Welle Matrix", rot(s, "Welle:1"))
show("check_joints Lager/Welle", [r for r in server.check_joints("lagerung")["joints"]
                                  if r["joint"].startswith(("Welle", "Lager"))], 3000)
jl = s.cmd("joint.list")
show("dof Welle (occurrence 17), conflicts, floating", {"dof": [d for d in jl["dof"] if d["dof"]], "conflicts": jl["conflicts"],
                                                       "floating": jl["floating"]})
# Antrieb 90 Grad
r = s.cmd("joint.drive", {"joint": "Welle_in_608", "value": 90})
show("drive 90", r)
show("Welle Matrix nach 90", rot(s, "Welle:1"))
show("Lager608 nach 90", rot(s, "Lager608:1"))
jv = {j["name"]: j["values"] for j in s.cmd("joint.list")["joints"] if j["name"].startswith("Welle")}
show("Gelenkwerte nach 90", jv)
show("interference bei 90", s.cmd("inspect.interference", {}), 600)
# Auf 0 zurueck, Bewegungsstudie 0..90
s.cmd("joint.drive", {"joint": "Welle_in_608", "value": 0})
r = s.cmd("motion.study", {"name": "Drehung90", "steps": 9, "keys": [{"joint": "Welle_in_608", "points": [[0, 0], [9, 90]]}]})
show("motion.study", r, 600)
try:
    show("motion.interference", s.cmd("motion.interference", {"study": "Drehung90",
         "occurrences": ["Welle:1", "Lager608:1", "Lager6000:1", "BockL:1", "BockR:1", "Platte:1"]}), 1500)
except Exception as e:
    print("FEHLER motion.interference", type(e).__name__, str(e)[:600])
try:
    show("joint.sweep", s.cmd("joint.sweep", {"joint": "Welle_in_608", "from": 0, "to": 90, "step": 30,
         "occurrences": ["Welle:1", "Lager608:1", "Lager6000:1", "BockL:1", "BockR:1", "Platte:1"]}), 1500)
except Exception as e:
    print("FEHLER joint.sweep", type(e).__name__, str(e)[:600])
show("transforms nach Studie (design unveraendert?)", tr(s))
asm.save()
ws.close_all()
