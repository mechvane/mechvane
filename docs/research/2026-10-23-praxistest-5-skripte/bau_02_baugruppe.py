"""Praxistest 5, Schritt 1b: Baugruppe, Lager, Gelenke, Verschraubungen.
Lauf (nach bau_01): PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/bau_02_baugruppe.py"""
import json
import sys

sys.path.insert(0, ".")
from mechvane import bolted, links, server  # noqa: E402
from mechvane.documents import Workspace, ASSEMBLY  # noqa: E402

ws = Workspace("/tmp/praxis5-ws")
server.ws = ws


def show(label, v, n=900):
    print(f"--- {label}\n{json.dumps(v, ensure_ascii=False)[:n]}")


for n in ("grundplatte", "lagerbock_l", "lagerbock_r", "welle", "lager_608", "lager_6000"):
    ws.open(f"{n}.solidcraft")
asm = ws.new(ASSEMBLY, "lagerung", overwrite=True)
P = "{}.solidcraft".format
server.insert_part("lagerung", P("grundplatte"), name="Platte", grounded=True)
server.insert_part("lagerung", P("lagerbock_l"), name="BockL", grounded=True)
server.insert_part("lagerung", P("lagerbock_r"), name="BockR", grounded=True)
server.insert_part("lagerung", P("lager_608"), name="Lager608", translate=[25, 0, 24], rotate={"axis": [0, 1, 0], "angle": 90})
server.insert_part("lagerung", P("lager_6000"), name="Lager6000", translate=[108, 0, 24], rotate={"axis": [0, 1, 0], "angle": 90})
server.insert_part("lagerung", P("welle"), name="Welle", translate=[0, 0, 24])
for o in links._occurrences(asm.session).values():
    print(o["name"], [round(o["transform"][i][3], 3) for i in range(3)])

# --- Verschraubungen: Block L zwei Zylinderkopf, Block R eine Zylinderkopf + eine Senkkopf ---
bc = {}
for tag, x, y, head in (("L1", 26, -26, "cap"), ("L2", 26, 26, "cap"), ("R1", 114, -26, "cap"), ("R2", 114, 26, "countersunk")):
    pl = {"position": [x, y, 8], "direction": [0, 0, -1]}
    show("preview " + tag, server.preview_bolted_connection("lagerung", pl, "M5", head=head), 700)
    bc[tag] = server.bolted_connection("lagerung", pl, "M5", head=head, name=f"Schr{tag}")
    show("bolted " + tag, bc[tag], 600)

# --- Lager in den Sitz (starr) und Welle in die Lager (Drehgelenk bzw. Zylindergelenk) ---
J = [
    {"type": "rigid", "name": "Lager608_im_Bock", "flip": True,
     "a": {"occurrence": "BockL:1", "circle": [32, 0, 35]}, "b": {"occurrence": "Lager608:1", "circle": [32, 0, 35]}},
    {"type": "rigid", "name": "Lager6000_im_Bock", "flip": True,
     "a": {"occurrence": "BockR:1", "circle": [108, 0, 37]}, "b": {"occurrence": "Lager6000:1", "circle": [108, 0, 37]}},
    {"type": "revolute", "name": "Welle_in_608", "flip": True,
     "a": {"occurrence": "Lager608:1", "circle": [32, 0, 28]}, "b": {"occurrence": "Welle:1", "circle": [31.9, 0, 28]}},
    {"type": "cylindrical", "name": "Welle_in_6000", "flip": True,
     "a": {"occurrence": "Lager6000:1", "circle": [108, 0, 29]}, "b": {"occurrence": "Welle:1", "circle": [108.1, 0, 29]}},
]
for jp in J:
    try:
        show("add_joint " + jp["name"], server.add_joint("lagerung", jp), 700)
    except Exception as e:
        print("FEHLER add_joint", jp["name"], type(e).__name__, str(e)[:700])
asm.save()
ws.close_all()
