"""Praxistest 5, Schritt 1a: Bauteile (Welle, Lagerböcke, Grundplatte, Lager) im Workspace /tmp/praxis5-ws.
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/bau_01_bauteile.py
Welt: Wellenachse = X bei y=0, z=24; Plattenoberkante z=0, Platte z -8..0."""
import json
import shutil
import sys

sys.path.insert(0, ".")
from mechvane import server, standard_parts  # noqa: E402
from mechvane.documents import Workspace, PART  # noqa: E402

WS = "/tmp/praxis5-ws"
shutil.rmtree(WS, ignore_errors=True)
ws = Workspace(WS)
server.ws = ws


def P(n, v, c=""):
    return {"command": "parameters.add", "params": {"name": n, "expression": v, "comment": c}}


# --- Welle (Revolve um X, Profil auf XZ): Ø8 Zapfen | Ø10 Absatz | Ø12 Mitte | Ø10 Zapfen ---
w = ws.new(PART, "welle")
cmds = [
    P("x_a", "10 mm"), P("x_b1", "32 mm"), P("x_c1", "50 mm"), P("x_r", "108 mm"), P("x_e", "x_r + 22 mm"),
    P("D_col", "10 mm", "Absatz links, Schritt 3: 12 mm"), P("D_mid", "12 mm"), P("D_j1", "8 mm"), P("D_j2", "10 mm"),
    {"command": "sketch.create", "params": {"plane": "XZ", "name": "WellenProfil"}},
    {"command": "sketch.line", "params": {"closed": True, "points": [
        ["x_a", 0], ["x_a", "D_j1 / 2"], ["x_b1", "D_j1 / 2"], ["x_b1", "D_col / 2"], ["x_c1", "D_col / 2"],
        ["x_c1", "D_mid / 2"], ["x_r", "D_mid / 2"], ["x_r", "D_j2 / 2"], ["x_e", "D_j2 / 2"], ["x_e", 0]]}},
    {"command": "sketch.finish", "params": {}},
    {"command": "solid.revolve", "params": {"sketch": "WellenProfil", "axis": "X", "operation": "new",
                                            "body_name": "Welle", "name": "Wellenkoerper"}},
]
r = server.run("welle", cmds)
print("welle", json.dumps(r)[:600])
print(json.dumps(server.measure("welle")))
w.save()

# --- Grundplatte ---
pl = ws.new(PART, "grundplatte")
r = server.run("grundplatte", [
    P("L_pl", "140 mm"), P("B_pl", "70 mm"), P("T_pl", "8 mm"),
    {"command": "solid.box", "params": {"length": "L_pl", "width": "B_pl", "height": "T_pl", "corner": [0, -35, -8],
                                         "operation": "new", "body_name": "Grundplatte", "name": "Platte"}}])
pl.save()


# --- Lagerböcke: Fuß 20 x 64 x 8, Ständer 12 x 40 x 38, Lagersitz als Senkbohrung (Sitz D, Tiefe, Rest d_through) ---
def bock(name, x_up, seat_D, seat_depth, d_through, toward):
    """x_up = Innenfläche des Ständers (Lager öffnet sich zur Wellenmitte); toward = -1 (Sitz in -X) oder +1."""
    d = ws.new(PART, name)
    xs = x_up - 12 if toward < 0 else x_up
    xf = xs - 4
    cmds = [
        P("x_s", f"{xs} mm", "Ständer Beginn x"), P("x_f", "x_s + 12 mm" if toward < 0 else "x_s", "Innenfläche des Ständers"),
        P("z_ax", "24 mm", "Achshöhe"), P("D_sitz", f"{seat_D} mm", "Lagersitz"),
        P("t_sitz", f"{seat_depth} mm"), P("d_rest", f"{d_through} mm"),
        {"command": "solid.box", "params": {"length": 20, "width": 64, "height": 8, "corner": ["x_s - 4 mm", -32, 0],
                                             "operation": "new", "body_name": name, "name": "Fuss"}},
        {"command": "solid.box", "params": {"length": 12, "width": 40, "height": 38, "corner": ["x_s", -20, 8],
                                             "operation": "join", "name": "Staender"}},
    ]
    face_x = x_up
    cmds.append({"command": "solid.hole", "params": {
        "position": ["x_f", 0, "z_ax"], "direction": [toward, 0, 0], "type": "counterbore",
        "diameter": "d_rest", "cb_diameter": "D_sitz", "cb_depth": "t_sitz", "name": "Lagersitz"}})
    r = server.run(name, cmds)
    d.save()
    return r


r = bock("lagerbock_l", 32, 22, 7, 18, -1)   # 608: D22 B7, Ständer x 20..32, Sitz x 25..32
print("bock_l", json.dumps(r)[:500])
r = bock("lagerbock_r", 108, 26, 8, 20, +1)  # 6000: D26 B8, Ständer x 108..120, Sitz x 108..116
print("bock_r", json.dumps(r)[:500])
for n in ("lagerbock_l", "lagerbock_r", "grundplatte"):
    print(n, json.dumps(server.measure(n)))

# --- Lager als Normteile ---
for size in ("608", "6000"):
    print(json.dumps(server.standard_part("DIN 625", size, name=f"lager_{size}"))[:400])
    print(json.dumps(server.measure(f"lager_{size}")))
ws.close_all()
