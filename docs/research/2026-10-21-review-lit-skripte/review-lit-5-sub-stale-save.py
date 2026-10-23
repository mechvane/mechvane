import tempfile, os
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links, inplace

ws = Workspace(tempfile.mkdtemp())
plate = ws.new(PART, "p_plate")
plate.session.batch([
    {"command": "parameters.add", "params": {"name": "w", "expression": "40 mm"}},
    {"command": "solid.box", "params": {"length": 60, "width": "w", "height": 5, "corner": [0, 0, 0]}}
])
plate.save()

sub = ws.new(ASSEMBLY, "p_sub")
links.insert(ws, sub, plate.path, name="Plate", translate=[0, 0, 0])
sub.save()

top = ws.new(ASSEMBLY, "p_top")
links.insert(ws, top, sub.path, name="Sub", translate=[10, 0, 0])
top.save()

# Close all except top
ws.close("p_plate")
ws.close("p_sub")

eip = inplace.edit_in_place(ws, "p_top", "Sub:1/Plate:1")
pdoc = ws.get("p_plate")
pdoc.session.cmd("parameters.change", {"name": "w", "expression": "80 mm"})

fin = inplace.finish_edit(ws, "p_plate")

reader = ws.reader(sub.path)
bbox = reader.tool("inspect_design", {"measure": True})["bodies"][0]["bbox"]
reader.close()

# sub.solidcraft on disk was not updated (width remains 40 mm)
print("Befund 5 (Zwischenbaugruppe auf Disk nicht aktualisiert) Bestätigt: bbox =", bbox)
assert bbox["max"][1] == 40.0
