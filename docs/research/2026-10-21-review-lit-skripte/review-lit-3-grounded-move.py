import tempfile
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links
from mechvane.solidcraft import SolidCraftError

ws = Workspace(tempfile.mkdtemp())
plate = ws.new(PART, "wall")
plate.session.batch([
    {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 6, "corner": [0, 0, 0]}},
])
plate.save()

sub = ws.new(ASSEMBLY, "sub_u")
links.insert(ws, sub, plate.path, name="Plate", translate=[10, 0, 0], grounded=True)
sub.save()
top = ws.new(ASSEMBLY, "top_u")
links.insert(ws, top, sub.path, name="Sub", rotate={"axis": [1, 0, 0], "angle": 90}, grounded=True)
sub.session.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": False})
sub.session.cmd("occurrence.move", {"occurrence": "Plate:1", "translate": [20, 0, 0]})
sub.session.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": True})
sub.save()
try:
    links.update_links(ws, top)
    raise AssertionError("Sollte abstürzen")
except SolidCraftError as e:
    print("Befund 3 (Grounded move crash) Bestätigt:", e)
