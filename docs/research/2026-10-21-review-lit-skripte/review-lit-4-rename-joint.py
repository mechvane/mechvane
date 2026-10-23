from mechvane import server, links
from mechvane.documents import ASSEMBLY, PART

p1 = server.ws.new(PART, "p1")
p1.session.batch([
    {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0,0,0]}},
    {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [10, 20, 0], "operation": "cut", "name": "Hole"}}
])
p1.save()
p2 = server.ws.new(PART, "p2")
p2.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0,0,0], "name": "Pin"})
p2.save()

asm = server.ws.new(ASSEMBLY, "asm")
links.insert(server.ws, asm, p1.path, name="P1", grounded=True)
links.insert(server.ws, asm, p2.path, name="P2")

jp = {"type": "revolute", "name": "Rev1",
      "a": {"occurrence": "P1:1", "point": [10, 20, 10], "z": [0, 0, 1]},
      "b": {"occurrence": "P2:1", "point": [0, 0, 0], "z": [0, 0, 1]}}
asm.session.cmd("joint.create", jp)
links.record(server.ws, asm, "Rev1", jp)

try:
    server.edit_joint("asm", "Rev1", {"name": "RevRenamed"})
    raise AssertionError("Sollte KeyError werfen")
except KeyError as e:
    print("Befund 4 (edit_joint rename KeyError) Bestätigt:", e)
finally:
    server.ws.close_all()
