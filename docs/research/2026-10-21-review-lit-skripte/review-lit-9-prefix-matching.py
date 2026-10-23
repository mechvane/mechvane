import tempfile
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links, inplace

ws = Workspace(tempfile.mkdtemp())
p1 = ws.new(PART, "plate_washer")
p1.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0,0,0]})
p1.save()

p2 = ws.new(PART, "plate")
p2.session.cmd("solid.box", {"length": 20, "width": 20, "height": 10, "corner": [0,0,0]})
p2.save()

sub = ws.new(ASSEMBLY, "sub")
links.insert(ws, sub, p1.path, name="PlateWasher")
links.insert(ws, sub, p2.path, name="Plate")
sub.save()

top = ws.new(ASSEMBLY, "top")
top.session.cmd("component.create", {"name": "Sub", "parent": "root", "activate": False})
links.insert(ws, top, p1.path, name="PlateWasher", parent=1)
links.insert(ws, top, p2.path, name="Plate", parent=1)

res = inplace.resolve_occurrence(top, "Sub/Plate")
print("Befund 9 (Präfixmatch wählt PlateWasher statt Plate) Bestätigt: res =", res["name"])
assert res["name"] == "PlateWasher:1"
