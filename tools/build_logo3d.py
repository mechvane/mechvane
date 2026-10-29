"""The Mechvane logo as a 3D assembly: the M (rounded plate and both legs) as one body, the V (two
halves, one body each for the two oranges) fastened with two M3 cap screws into blind holes.

    python3 tools/build_logo3d.py [folder]   (default workspace/logo; renders logo3d-iso.png and -top.png there)
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mechvane import bolted, links  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "workspace" / "logo"
shutil.rmtree(folder, ignore_errors=True)
folder.mkdir(parents=True)
ws = Workspace(folder)


def sketch_rect(name, p0, p1, plane="XY", offset=None):
    params = {"plane": plane, "name": name}
    if offset is not None:
        params["offset"] = offset
    return [{"command": "sketch.create", "params": params},
            {"command": "sketch.rectangle.two_point", "params": {"p0": p0, "p1": p1}},
            {"command": "sketch.finish", "params": {}}]


try:
    # M: plate 100 x 100 x 6 with r23 corners, legs 14 x 56, 10 mm high, one body
    m = ws.new(PART, "logo_m")
    m.session.batch(
        sketch_rect("PlateSketch", [0, 0], [100, 100])
        + [{"command": "solid.extrude", "params": {"sketch": "PlateSketch", "distance": 6, "name": "Plate",
                                                   "body_name": "M"}},
           {"command": "solid.fillet", "params": {"edges": [[0, 0, 3], [100, 0, 3], [100, 100, 3], [0, 100, 3]],
                                                  "radius": 23, "name": "PlateCorners"}}]
        + sketch_rect("LegLeftSketch", [21, 22], [35, 78], offset=6)
        + [{"command": "solid.extrude", "params": {"sketch": "LegLeftSketch", "distance": 10, "operation": "join",
                                                   "name": "LegLeft"}}]
        + sketch_rect("LegRightSketch", [65, 22], [79, 78], offset=6)
        + [{"command": "solid.extrude", "params": {"sketch": "LegRightSketch", "distance": 10, "operation": "join",
                                                   "name": "LegRight"}}])
    m.session.cmd("appearance.assign", {"bodies": ["M"], "color": "#24384f"})
    for color, x0, x1 in (("#f2f6fa", 21, 35), ("#c9d4e0", 65, 79)):
        cx = (x0 + x1) / 2
        m.session.cmd("appearance.assign", {"faces": [[cx, 50, 16], [x0, 50, 11], [x1, 50, 11], [cx, 22, 11], [cx, 78, 11]],
                                            "body": "M", "color": color})
    m.save()

    # V: the folded strip of the logo as a 4 mm plate
    v = ws.new(PART, "logo_v")
    # two halves meeting at the fold, one body each, so each gets its own orange like the logo
    v.session.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "VLeftSketch"}},
        {"command": "sketch.line", "params": {"points": [[21, 78], [38, 78], [50, 64], [50, 44]], "closed": True}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "VLeftSketch", "distance": 4, "name": "VLeft", "body_name": "VLeft"}},
        {"command": "sketch.create", "params": {"plane": "XY", "name": "VRightSketch"}},
        {"command": "sketch.line", "params": {"points": [[79, 78], [62, 78], [50, 64], [50, 44]], "closed": True}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "VRightSketch", "distance": 4, "operation": "new",
                                                "name": "VRight", "body_name": "VRight"}},
        {"command": "appearance.assign", "params": {"bodies": ["VLeft"], "color": "#ffad45"}},
        {"command": "appearance.assign", "params": {"bodies": ["VRight"], "color": "#d26a0c"}},
    ])
    v.save()

    asm = ws.new(ASSEMBLY, "mechvane_logo")
    links.insert(ws, asm, m.path, name="M", grounded=True)
    links.insert(ws, asm, v.path, name="V", translate=[0, 0, 16], grounded=True)
    asm.save()
    for x in (31, 69):
        r = bolted.bolted_connection(ws, "mechvane_logo", placement={"position": [x, 73.5, 20], "direction": [0, 0, -1]},
                                     size="M3", connection_type="blind")
        print("bolt", x, {k: r.get(k) for k in ("id", "screw", "parts", "warnings") if k in r})
    asm = ws.get("mechvane_logo")
    asm.save()
    insp = asm.session.cmd("document.inspect", {"measure": False})
    print("bodies:", [b["name"] for b in insp.get("bodies", [])])
    print("check:", [c["status"] for c in links.check(ws, asm)])
    for view in ("iso", "top"):
        asm.session.tool("screenshot", {"view": view, "width": 1200, "height": 900, "grid": False,
                                        "path": str(folder / f"logo3d-{view}.png")})
finally:
    ws.close_all()
