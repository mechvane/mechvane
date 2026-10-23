import tempfile, os
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links
from mechvane.solidcraft import SolidCraftError

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
asm.save()

os.remove(p1.path)

try:
    links.check(ws, asm)
    raise AssertionError("Sollte abstürzen")
except SolidCraftError as e:
    print("Befund 8 (Missing file crash) Bestätigt:", e)
