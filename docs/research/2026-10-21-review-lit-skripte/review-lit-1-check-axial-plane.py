import tempfile
from mechvane.documents import Workspace, ASSEMBLY, PART
from mechvane import links

ws = Workspace(tempfile.mkdtemp())
p1 = ws.new(PART, "p1")
p1.session.batch([
    {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0,0,0]}},
    {"command": "solid.cylinder", "params": {"diameter": 6, "height": 20, "base": [20, 20, 0], "operation": "cut", "name": "Hole"}}
])
p1.save()
p2 = ws.new(PART, "p2")
p2.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0,0,0], "name": "Pin"})
p2.save()

asm = ws.new(ASSEMBLY, "asm")
links.insert(ws, asm, p1.path, name="P1", grounded=True)
links.insert(ws, asm, p2.path, name="P2")

jp = {"type": "rigid", "name": "PinInHole",
      "a": {"occurrence": "P1:1", "circle": [20, 20, 20]},
      "b": {"occurrence": "P2:1", "circle": [0, 0, 0]}}
asm.session.cmd("joint.create", jp)
entry = links.record(ws, asm, "PinInHole", jp)
assert entry["sides"]["a"]["axial"] == -20.0

# 1. Zylinder: Simuliere Gelenkverschiebung entlang Zylinderachse von z=20 auf z=0 (20 mm axialer Versatz)
orig_frames = links._frames
def mock_frames_cyl(s):
    f = orig_frames(s)
    if "PinInHole" in f:
        f["PinInHole"]["a"] = (f["PinInHole"]["a"][0], [20.0, 20.0, 0.0], f["PinInHole"]["a"][2])
    return f
links._frames = mock_frames_cyl

rep_cyl = links.check(ws, asm)
print("Befund 1a (Zylinder axial) Bestätigt: status =", rep_cyl[0]["status"])
assert rep_cyl[0]["status"] == "ok"

# 2. Ebene: Gelenk auf ebener Fläche mit Versatz zum Centroid
links._frames = orig_frames  # Restore
base = ws.new(PART, "base_p")
base.session.cmd("solid.box", {"length": 100, "width": 100, "height": 10, "corner": [0,0,0]})
base.save()
top_p = ws.new(PART, "top_p")
top_p.session.cmd("solid.box", {"length": 20, "width": 20, "height": 10, "corner": [0,0,0]})
top_p.save()

p_asm = ws.new(ASSEMBLY, "p_asm")
links.insert(ws, p_asm, base.path, name="Base", grounded=True)
links.insert(ws, p_asm, top_p.path, name="Top")

jp2 = {"type": "rigid", "name": "JPlane",
       "a": {"occurrence": "Base:1", "point": [20, 20, 10], "z": [0, 0, 1]},
       "b": {"occurrence": "Top:1", "point": [10, 10, 0], "z": [0, 0, -1]}}
p_asm.session.cmd("joint.create", jp2)
entry2 = links.record(ws, p_asm, "JPlane", jp2)
assert entry2["sides"]["a"]["offset"] == [-30.0, -30.0, 0.0]

# Verschiebe Rahmen um 40 mm auf derselben Deckfläche nach [60, 60, 10]
def mock_frames_plane(s):
    f = orig_frames(s)
    if "JPlane" in f:
        f["JPlane"]["a"] = (f["JPlane"]["a"][0], [60.0, 60.0, 10.0], f["JPlane"]["a"][2])
    return f
links._frames = mock_frames_plane

rep_plane = links.check(ws, p_asm)
print("Befund 1b (Ebene In-Plane) Bestätigt: status =", rep_plane[0]["status"])
assert rep_plane[0]["status"] == "ok"
