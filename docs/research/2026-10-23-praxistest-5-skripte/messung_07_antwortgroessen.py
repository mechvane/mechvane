"""Antwortgroessen und Laufzeiten (Zeichen JSON) von update_links / check_joints / finish_edit-artigem Bericht.
Benoetigt /tmp/praxis5-ws. Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/messung_07_antwortgroessen.py"""
import json, sys, time
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace
ws = Workspace("/tmp/praxis5-ws"); server.ws = ws
ws.open("lagerung.solidcraft")
for lab, fn in (("check_joints", lambda: server.check_joints("lagerung")),
                ("update_links(repair=False)", lambda: server.update_links("lagerung")),
                ("measure(lagerung)", lambda: server.measure("lagerung")),
                ("browser(lagerung)", lambda: server.browser("lagerung"))):
    t = time.time(); r = fn()
    j = json.dumps(r, default=str)
    extra = ""
    if "joints" in r:
        extra = f", davon {sum(1 for x in r['joints'] if x['status'] == 'ok')}/{len(r['joints'])} Eintraege 'ok'"
    print(f"{lab}: {len(j)} Zeichen{extra}, {time.time()-t:.1f}s")
ws.close_all()
