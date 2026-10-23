"""Befund 8: bolted_connection(head="countersunk") schneidet den Senkkegel ueber die Eintrittsflaeche hinaus:
Fuss-Oberkante z=8, die Flaeche F7:csink:base liegt bei z=8.81 und kerbt den benachbarten Staender (y<=20, Senkungsmitte
y=26, Senkradius 5.75). check_design meldet sie (zu Recht) als printability-Ueberhang. Das Skript zeigt Flaeche und Lage.
Benoetigt /tmp/praxis5-ws nach aender_05.py. Lauf: PYTHONPATH=. python3 <dieses Skript>"""
import sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace
ws = Workspace("/tmp/praxis5-ws"); server.ws = ws
ws.open("lagerbock_r.solidcraft")
r = server.check_design("lagerbock_r")
for c in r["checks"]:
    if c["rule"] == "printability" and c["status"] != "ok":
        print(c["message"])
for f in server.find("lagerbock_r", "faces", {"feature": "Hole_M5_CS", "limit": 20}, limit=20)["items"]:
    print(f["name"], f["type"], "normal", f.get("normal"), "area", round(f["area"], 2), "pick", [round(x, 2) for x in f["pick"]])
m = server.measure("lagerbock_r")["bodies"][0]["bbox"]
print("Erwartet: keine Flaeche oberhalb z=8 an der Senkung. Tatsaechlich csink:base bei z=8.81 (pick oben).")
print("Block bbox z:", m["min"][2], "..", m["max"][2], "(Fuss 0..8, Staender 8..46); Senkungsmitte y=26")
ws.close_all()
