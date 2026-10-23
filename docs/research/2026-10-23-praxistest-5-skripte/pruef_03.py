"""Praxistest 5, Schritt 2: Pruefungen (check_design, find, check_joints, Interferenz, Freiheitsgrade, Antrieb).
Lauf (nach bau_02): PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/pruef_03.py"""
import json
import sys

sys.path.insert(0, ".")
from mechvane import links, server  # noqa: E402
from mechvane.documents import Workspace  # noqa: E402

ws = Workspace("/tmp/praxis5-ws")
server.ws = ws


def show(label, v, n=1500):
    print(f"--- {label}\n{json.dumps(v, ensure_ascii=False, default=str)[:n]}", flush=True)


asm = ws.open("lagerung.solidcraft")
s = asm.session
for n in ("grundplatte", "lagerbock_l", "lagerbock_r", "welle", "lager_608", "lager_6000"):
    ws.open(f"{n}.solidcraft")

show("browser", server.browser("lagerung")["text"], 3000)
show("measure assembly", server.measure("lagerung"), 3500)
show("check_joints", server.check_joints("lagerung"), 3000)
jl = s.cmd("joint.list")
show("joint.list dof/conflicts/floating", {k: jl.get(k) for k in ("dof", "degrees_of_freedom", "conflicts", "floating")}, 800)
for j in jl["joints"]:
    if j["name"] in ("Welle_in_608", "Welle_in_6000", "Lager608_im_Bock", "Lager6000_im_Bock"):
        show("joint " + j["name"], j, 900)
show("interference", s.cmd("inspect.interference", {}), 3000)

for n in ("grundplatte", "lagerbock_l", "lagerbock_r", "welle"):
    for prof in ("fdm_0.4", "cnc_alu"):
        r = server.check_design(n, prof)
        show(f"check_design {n} {prof}", {k: v for k, v in r.items() if k != "checks"} if False else r, 2500)
for n in ("lagerbock_l", "lagerbock_r"):
    show(f"find holes {n}", server.find(n, "holes"), 1800)
show("find holes asm Ø22 diameter", server.find("lagerung", "holes", {"diameter": [21.9, 26.1]}), 1800)
ws.close_all()
