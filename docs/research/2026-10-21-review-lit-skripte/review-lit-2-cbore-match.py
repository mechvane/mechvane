import tempfile
from mechvane.documents import Workspace, PART
from mechvane import links

ws = Workspace(tempfile.mkdtemp())
p = ws.new(PART, "p")
p.session.batch([
    {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0,0,0]}},
    {"command": "solid.hole", "params": {"position": [20, 20, 20], "direction": [0, 0, -1], "diameter": 6, "type": "counterbore", "cb_diameter": 12, "cb_depth": 5, "name": "CBore"}}
])
p.save()
reader = ws.reader(p.path)
faces = links._part_faces(reader)
reader.close()

# The counterbore entrance is at [20, 20, 20] (diameter 12, counterbore face F2:cbore:side:0/1)
# The through bore is at [20, 20, 0..15] (diameter 6, bore face F2:bore:side:0/1)
m = links._match(faces, [20, 20, 20], [0, 0, 1])
print("Befund 2 (Senkungs-Zuordnung) Bestätigt: match at z=20 =", m["face"])
assert "bore" in m["face"] and "cbore" not in m["face"]
