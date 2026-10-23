"""check_design aller Teile nach der Aenderung (Kurzfassung). Benoetigt /tmp/praxis5-ws nach aender_05.py."""
import sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace
ws = Workspace("/tmp/praxis5-ws"); server.ws = ws
for n in ("grundplatte", "lagerbock_l", "lagerbock_r", "welle"):
    ws.open(f"{n}.solidcraft")
    r = server.check_design(n)
    print(n, r["verdict"], {k: v["status"] for k, v in r["rules"].items()})
    for c in r["checks"]:
        if c["status"] != "ok":
            print("   ", c["rule"], c["message"], c["location"].get("face"))
ws.close_all()
