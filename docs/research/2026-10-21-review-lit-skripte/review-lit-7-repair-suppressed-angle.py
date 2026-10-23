import tempfile
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links

ws = Workspace(tempfile.mkdtemp())
p1 = ws.new(PART, "p1")
p1.session.batch([
    {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0,0,0]}},
    {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [10, 20, 0], "operation": "cut", "name": "Hole"}}
])
p1.save()
p2 = ws.new(PART, "p2")
p2.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0,0,0], "name": "Pin"})
p2.save()

asm = ws.new(ASSEMBLY, "asm")
links.insert(ws, asm, p1.path, name="P1", grounded=True)
links.insert(ws, asm, p2.path, name="P2")

jp = {"type": "revolute", "name": "Rev1",
      "a": {"occurrence": "P1:1", "circle": [10, 20, 10]},
      "b": {"occurrence": "P2:1", "circle": [0, 0, 0]}}
asm.session.cmd("joint.create", jp)
links.record(ws, asm, "Rev1", jp)

asm.session.cmd("joint.edit", {"joint": "Rev1", "suppressed": True})

p1.session.cmd("timeline.roll_to", {"position": 1})
p1.session.cmd("solid.cylinder", {"diameter": 6, "height": 10, "base": [0, 20, 0], "operation": "cut", "name": "Hole0"})
p1.session.cmd("timeline.roll_to", {})
p1.save()

links.update_links(ws, asm, repair_moved=True)
repaired_j = asm.session.cmd("joint.list")["joints"][0]
print("Befund 7 (Repair verliert suppressed) Bestätigt: suppressed =", repaired_j["suppressed"])
assert repaired_j["suppressed"] is False
