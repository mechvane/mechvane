"""Befund 2: find(holes) in der Baugruppe 'lagerung' liefert die Lagersitze (Ø22/Ø26, Senkbohrung) nicht,
im Bauteil ja. Benoetigt /tmp/praxis5-ws aus bau_01_bauteile.py und bau_02_baugruppe.py.
Lauf: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-5-skripte/fehler_05_find_holes_baugruppe_lagersitz.py"""
import sys
sys.path.insert(0, ".")
from mechvane import server
from mechvane.documents import Workspace
ws = Workspace("/tmp/praxis5-ws"); server.ws = ws
ws.open("lagerbock_l.solidcraft"); ws.open("lagerung.solidcraft")
def show(lab, r):
    print(f"{lab}: count={r['count']}", sorted({(h['diameter'], h.get('through')) for h in r['items']}))
show("Bauteil lagerbock_l, ohne Filter", server.find("lagerbock_l", "holes"))
show("Bauteil lagerbock_l, diameter [21.9,22.1]", server.find("lagerbock_l", "holes", {"diameter": [21.9, 22.1]}))
show("Baugruppe, ohne Filter", server.find("lagerung", "holes"))
show("Baugruppe, diameter [21.9,22.1]", server.find("lagerung", "holes", {"diameter": [21.9, 22.1]}))
show("Baugruppe, occurrence BockL:1", server.find("lagerung", "holes", {"occurrence": "BockL:1"}))
show("Baugruppe faces Ø22 cylinder", server.find("lagerung", "faces", {"type": "cylinder", "diameter": [21.9, 22.1]}))
ws.close_all()
