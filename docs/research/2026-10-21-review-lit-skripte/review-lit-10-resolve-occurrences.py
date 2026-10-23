import tempfile
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links

ws = Workspace(tempfile.mkdtemp())
p = ws.new(PART, "p")
p.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0,0,0]})
p.save()

top = ws.new(ASSEMBLY, "top")
links.insert(ws, top, p.path, name="Plate")

sub = ws.new(ASSEMBLY, "sub")
links.insert(ws, sub, p.path, name="Plate")
sub.save()
links.insert(ws, top, sub.path, name="Sub")

resolved = links.resolve_occurrences(top.session, {"b": {"occurrence": "Sub:1/Plate"}})
print("Befund 10 (resolve_occurrences verliert Präfix) Bestätigt: resolved =", resolved["b"]["occurrence"])
assert resolved["b"]["occurrence"] == "Plate"  # Statt Sub_Plate:1!
