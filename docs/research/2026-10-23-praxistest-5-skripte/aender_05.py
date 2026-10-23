"""Praxistest 5, Schritt 3: Aenderung (Absatz Ø10 -> Ø12, Lagerabstand +20 mm, Platte 160 lang), update_links(repair).
Lauf (nach bau_01, bau_02): PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/aender_05.py"""
import json
import sys
import time

sys.path.insert(0, ".")
from mechvane import links, server  # noqa: E402
from mechvane.documents import Workspace  # noqa: E402

ws = Workspace("/tmp/praxis5-ws")
server.ws = ws


def show(label, v, n=1800):
    print(f"--- {label}\n{json.dumps(v, ensure_ascii=False, default=str)[:n]}", flush=True)


def step(label, fn, n=1800):
    t = time.time()
    try:
        r = fn()
        show(f"{label} ({time.time() - t:.1f}s)", r, n)
        return r
    except Exception as e:
        print(f"--- FEHLER {label}: {type(e).__name__}: {str(e)[:1200]}", flush=True)


def interf(name="lagerung"):
    r = ws.get(name).session.cmd("inspect.interference", {})
    return {"count": r["count"], "pairs": [(i.get("a"), i.get("b"), i.get("volume_mm3")) for i in r["interferences"]]}


def bc_status(rep):
    return [(b.get("id"), b.get("status"), b.get("shifted_by")) for b in rep.get("bolted_connections", [])]


for n in ("grundplatte", "lagerbock_l", "lagerbock_r", "welle", "lager_608", "lager_6000"):
    ws.open(f"{n}.solidcraft")
asm = ws.open("lagerung.solidcraft")
s = asm.session

step("vorher check_joints", lambda: [r["status"] for r in server.check_joints("lagerung")["joints"]], 600)
step("vorher volumen", lambda: {n: [round(b["volume_mm3"], 1) for b in server.measure(n)["bodies"]]
                                for n in ("grundplatte", "lagerbock_r", "welle")})


def edit(occ, params_changes):
    r = server.edit_in_place("lagerung", occ)
    doc = r["document"] if "document" in r else r.get("name")
    server.run(doc, [{"command": "parameters.change", "params": p} for p in params_changes])
    return doc


# 1) Grundplatte laenger
doc = edit("Platte:1", [{"name": "L_pl", "expression": "160 mm"}])
step("finish_edit grundplatte", lambda: (lambda r: {"chars": len(json.dumps(r, default=str)), "warnings": [w for a in r["assemblies"].values() for w in a["update"]["warnings"]], "joints_nicht_ok": [(j["joint"], j["side"], j["status"]) for a in r["assemblies"].values() for j in a["joints"] if j["status"] != "ok"]})(server.finish_edit(doc)), 2500)
# 2) Welle: Absatz Ø12, rechter Teil +20
doc = edit("Welle:1", [{"name": "D_col", "expression": "12 mm"}, {"name": "x_r", "expression": "128 mm"}])
step("finish_edit welle", lambda: (lambda r: {"chars": len(json.dumps(r, default=str)), "warnings": [w for a in r["assemblies"].values() for w in a["update"]["warnings"]], "joints_nicht_ok": [(j["joint"], j["side"], j["status"]) for a in r["assemblies"].values() for j in a["joints"] if j["status"] != "ok"]})(server.finish_edit(doc)), 2500)
# 3) Lagerbock R +20
doc = edit("BockR:1", [{"name": "x_s", "expression": "128 mm"}])
step("finish_edit lagerbock_r", lambda: (lambda r: {"chars": len(json.dumps(r, default=str)), "warnings": [w for a in r["assemblies"].values() for w in a["update"]["warnings"]], "joints_nicht_ok": [(j["joint"], j["side"], j["status"]) for a in r["assemblies"].values() for j in a["joints"] if j["status"] != "ok"]})(server.finish_edit(doc)), 3500)

rep = step("update_links (repair=False)", lambda: server.update_links("lagerung"), 300)
if rep:
    show("bolted (repair=False)", bc_status(rep))
    show("joints != ok (repair=False)", [(j["joint"], j["side"], j["status"]) for j in rep.get("joints", []) if j["status"] != "ok"])
rep = step("update_links (repair=True)", lambda: server.update_links("lagerung", repair=True), 300)
if rep:
    show("bolted_connections", bc_status(rep))
    show("warnings", rep.get("warnings"), 1500)
step("check_joints", lambda: [(r["joint"], r["side"], r["status"]) for r in server.check_joints("lagerung")["joints"]
                              if r["status"] != "ok"] or "alle ok", 1500)
step("joint.list dof/conflicts", lambda: {"dof": [d for d in s.cmd("joint.list")["dof"] if d["dof"]],
                                          "conflicts": s.cmd("joint.list")["conflicts"]})
step("list_bolted_connections", lambda: [(b.get("id"), b.get("parts") or b.get("components")) for b in
                                         server.list_bolted_connections("lagerung").get("connections", {}).values()], 1500)
step("interference nach Aenderung", interf)
step("measure Teile", lambda: {n: [(round(b["volume_mm3"], 1), b["bbox"]["min"], b["bbox"]["max"]) for b in server.measure(n)["bodies"]]
                               for n in ("grundplatte", "lagerbock_r", "welle")}, 2500)
step("Gelenke Position Lager6000/Welle", lambda: [(j["name"], j["frame_a"]["origin"], j["frame_b"]["origin"]) for j in s.cmd("joint.list")["joints"]
                                                  if j["name"] in ("Lager6000_im_Bock", "Welle_in_6000", "Welle_in_608")], 1500)
step("drive 90", lambda: s.cmd("joint.drive", {"joint": "Welle_in_608", "value": 90, "quiet": True}), 800)
step("interference bei 90 Grad", interf)
s.cmd("joint.drive", {"joint": "Welle_in_608", "value": 0, "quiet": True})
asm.save()
# speichern/schliessen/oeffnen
ws.close_all()
asm = ws.open("lagerung.solidcraft")
step("nach Neuoeffnen check_joints", lambda: sorted({r["status"] for r in server.check_joints("lagerung")["joints"]}))
step("nach Neuoeffnen update_links", lambda: (lambda r: {"warnings": r.get("warnings"), "bolted": bc_status(r)})(server.update_links("lagerung")), 2500)
step("nach Neuoeffnen interference", interf)
ws.close_all()
