import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from mcpclient import Session

S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(S, "out")
os.makedirs(OUT, exist_ok=True)
s = Session(["solidcraft-cli", "mcp", "--allow-path", OUT], os.path.join(OUT, "session.log"))


def show(label, res, n=500):
    err, out, ms, size = res
    print(f"\n== {label}: isError={err} {ms:.0f} ms {size} B\n{out[:n]}")
    return err, out


def vol():
    err, out = show("measure", s.tool("measure", {}), 0)
    t = json.loads(out)["total"]
    b = json.loads(out)["bodies"][0]
    print(f"   volume={t['volume_mm3']:.3f} faces={t['faces']} com={[round(c, 4) for c in b['center_of_mass']]}")
    return t["volume_mm3"]


build = [
    {"command": "parameters.add", "params": {"name": "A", "expression": "60 mm"}},
    {"command": "parameters.add", "params": {"name": "T", "expression": "8 mm"}},
    {"command": "parameters.add", "params": {"name": "bcd", "expression": "45 mm"}},
    {"command": "parameters.add", "params": {"name": "dh", "expression": "6.6 mm"}},
    {"command": "parameters.add", "params": {"name": "n", "expression": "4", "unit": ""}},
    {"command": "sketch.create", "params": {"plane": "XY", "name": "PlateSketch"}},
    {"command": "sketch.draw.dimensioned", "params": {"command": "sketch.rectangle.center",
        "params": {"center": [0, 0], "corner": [30, 30]}, "dimensions": {"width": "A", "height": "A"}}},
    {"command": "sketch.finish", "params": {}},
    {"command": "solid.extrude", "params": {"distance": "T", "name": "Plate"}},
    {"command": "solid.chamfer", "params": {"edges": [[0, 30, 8], [0, -30, 8], [30, 0, 8], [-30, 0, 8]],
                                            "distance": 1, "name": "TopChamfer"}},
    {"command": "solid.cylinder", "params": {"diameter": "dh", "height": "T + 2",
        "base": ["bcd/2 * cos(45 deg)", "bcd/2 * sin(45 deg)", -1], "operation": "cut", "name": "BoltHole"}},
    {"command": "solid.pattern.circular", "params": {"features": ["BoltHole"], "axis": "Z", "count": "n",
                                                      "name": "BoltHoles"}},
]
show("build (1 batch)", s.tool("batch", {"commands": build, "verbose": False, "timings": True}), 0)
v0 = vol()
expected = 60 * 60 * 8 - (4 * 60 * 0.5 - 4 / 3) - 4 * math.pi * 3.3 ** 2 * 8
print(f"   expected={expected:.3f} diff={(v0 - expected) / expected * 100:.4f} %")

err, topo = show("body_topology Body1", s.tool("body_topology", {"body": "Body1"}), 0)
open(os.path.join(OUT, "topology.json"), "w").write(topo)
t = json.loads(topo)
print("   topology keys:", list(t.keys()), "faces:", len(t.get("faces", [])), "edges:", len(t.get("edges", [])))
for f in t.get("faces", [])[:20]:
    print("   face", {k: f.get(k) for k in ("index", "name", "normal", "area", "cylinder")})

r = 45 / 2 / math.sqrt(2)
p = [r + 3.3, r, 4]
for sel in ({"type": "face", "point": p}, {"face": {"point": p}}, {"type": "face", "body": "Body1", "point": p},
            {"type": "face", "body": "Body1", "index": 10}):
    show(f"measure items {json.dumps(sel)}", s.tool("measure", {"items": [sel]}), 400)

# Section + screenshot through a hole
show("section", s.tool("execute", {"command": "inspect.section",
     "params": {"plane": {"origin": [0, 0, 0], "normal": [-1, 1, 0]}}}), 300)
show("screenshot section", s.tool("screenshot", {"source": "model", "width": 640, "height": 480,
     "camera": {"target": [0, 0, 4], "yaw": -math.pi / 4 + math.pi, "pitch": 0.5, "distance": 110}},
     png=os.path.join(OUT, "flange_section.png")), 200)
show("section clear", s.tool("execute", {"command": "inspect.section", "params": {"clear": True}}), 200)

# Parameter changes
for name, val in (("bcd", "40 mm"), ("n", "6"), ("T", "10 mm")):
    show(f"set {name}={val}", s.tool("set_parameter", {"name": name, "value": val}), 300)
    vol()
show("screenshot n6 T10", s.tool("screenshot", {"source": "model", "view": "iso", "width": 640, "height": 480},
                                  png=os.path.join(OUT, "flange_n6_iso.png")), 200)
show("chamfer too large after T change?", s.tool("set_parameter", {"name": "T", "value": "0.8 mm"}), 800)
show("inspect after T=0.8", s.tool("inspect_design", {"measure": False, "sketches": False}), 0)
show("revert", s.tool("batch", {"commands": [
    {"command": "parameters.change", "params": {"name": n, "expression": e}}
    for n, e in (("bcd", "45 mm"), ("n", "4"), ("T", "8 mm"))]}), 0)
v1 = vol()
print("   back to original:", abs(v1 - v0) < 1e-6)

show("export step", s.tool("export", {"path": os.path.join(OUT, "flansch.step")}), 200)
show("export 3mf", s.tool("export", {"path": os.path.join(OUT, "flansch.3mf")}), 200)
show("save", s.tool("save", {"path": os.path.join(OUT, "flansch.solidcraft")}), 200)
show("export outside allowed path", s.tool("export", {"path": "/root/flansch.step"}), 300)

# Variant: the same holes with the hole command and ISO 273 clearance
show("new_design", s.tool("new_design", {"name": "flansch-hole"}), 100)
var = build[:10] + [
    {"command": "solid.hole", "params": {"position": [r, r, 8], "clearance": "M6", "name": "BoltHole"}},
    {"command": "solid.pattern.circular", "params": {"features": ["BoltHole"], "axis": "Z", "count": "n",
                                                      "name": "BoltHoles"}},
]
show("variant hole clearance M6", s.tool("batch", {"commands": var, "verbose": False}), 600)
vol()
show("timeline.inspect BoltHole", s.tool("execute", {"command": "timeline.inspect", "params": {"feature": "BoltHole"}}), 1500)
print("\nSTDERR:", s.close()[-500:])
