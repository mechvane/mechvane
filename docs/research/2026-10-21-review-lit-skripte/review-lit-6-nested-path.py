import tempfile
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links, inplace

ws = Workspace(tempfile.mkdtemp())
p = ws.new(PART, "p")
p.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0,0,0]})
p.save()
sub1 = ws.new(ASSEMBLY, "sub1")
links.insert(ws, sub1, p.path, name="PartP")
sub1.save()
sub2 = ws.new(ASSEMBLY, "sub2")
links.insert(ws, sub2, sub1.path, name="Sub1A", translate=[0, 0, 0])
links.insert(ws, sub2, sub1.path, name="Sub1B", translate=[50, 0, 0])
sub2.save()
top = ws.new(ASSEMBLY, "top")
links.insert(ws, top, sub2.path, name="Sub2")
top.save()

# Path targeting Sub1B (x=50)
res = inplace.resolve_occurrence(top, "Sub2:1/Sub1B:1/PartP:1")
print("Befund 6 (Mehrstufiger Pfad überspringt Zwischenebene) Bestätigt: resolved =", res["name"], "x =", res["transform"][3][0])
assert res["transform"][3][0] == 0.0  # False result! Should be 50.0!
