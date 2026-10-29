"""The Mechvane logo as a showcase assembly for rendering: a complete welded steel M on a steel back
plate, the V in two metals on thin spacers, fastened with two M3 cap screws. Writes one OBJ per body plus
materials.json for tools/render_logo_blender.py.

    python3 tools/build_logo_showcase.py [folder]   (default workspace/logo_showcase)
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mechvane import bolted, links  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402
from mechvane.ui.mesh import collect_mesh  # noqa: E402

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "workspace" / "logo_showcase"
shutil.rmtree(folder, ignore_errors=True)
folder.mkdir(parents=True)
ws = Workspace(folder)

V_Z = 18          # V plate sits on 2 mm spacers on top of the M (which ends at z 16)
V_T = 2.5         # V plate thickness
SCREWS = ((31, 73.5), (69, 73.5))


def rect(name, p0, p1, offset=None, plane="XY"):
    params = {"plane": plane, "name": name}
    if offset is not None:
        params["offset"] = offset
    return [{"command": "sketch.create", "params": params},
            {"command": "sketch.rectangle.two_point", "params": {"p0": p0, "p1": p1}},
            {"command": "sketch.finish", "params": {}}]


# Outline of the complete M (legs and the middle V), as in the logo
M_OUTLINE = [[21, 22], [21, 78], [38, 78], [50, 64], [62, 78], [79, 78], [79, 22], [65, 22], [65, 61.5],
             [50, 44], [35, 61.5], [35, 22]]


def m_profile():
    """The M joined onto the plate, 10 mm high: rounded upright corners, chamfered outer top edges."""
    return [
        {"command": "sketch.create", "params": {"plane": "XY", "offset": 6, "name": "MSketch"}},
        {"command": "sketch.line", "params": {"points": M_OUTLINE, "closed": True}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "MSketch", "distance": 10, "operation": "join", "name": "M"}},
        {"command": "solid.fillet", "params": {"edges": [[21, 22, 11], [35, 22, 11], [65, 22, 11], [79, 22, 11],
                                                         [21, 78, 11], [79, 78, 11]],
                                               "radius": 2.5, "name": "MCorners"}},
        {"command": "solid.chamfer", "params": {"edges": [[21, 50, 16], [79, 50, 16], [28, 22, 16], [72, 22, 16]],
                                                "distance": 0.8, "name": "MChamfer"}},
        # fillet welds (concave) all round where the M meets the plate: outer sides, feet, inner sides of the
        # legs, both edges of the middle V and the top edges
        {"command": "solid.fillet", "params": {"edges": [[21, 50, 6], [79, 50, 6], [28, 22, 6], [72, 22, 6],
                                                         [35, 42, 6], [65, 42, 6], [42.5, 52.75, 6], [57.5, 52.75, 6],
                                                         [44, 71, 6], [56, 71, 6], [29.5, 78, 6], [70.5, 78, 6]],
                                               "radius": 2.0, "name": "Welds"}},
    ]


try:
    # Back plate and M: steel, welded, powder-coated
    m = ws.new(PART, "logo_m")
    m.session.batch(
        rect("PlateSketch", [0, 0], [100, 100])
        + [{"command": "solid.extrude", "params": {"sketch": "PlateSketch", "distance": 6, "name": "Plate",
                                                   "body_name": "Plate"}},
           {"command": "solid.fillet", "params": {"edges": [[0, 0, 3], [100, 0, 3], [100, 100, 3], [0, 100, 3]],
                                                  "radius": 23, "name": "PlateCorners"}}]
        + m_profile())
    m.save()

    # Spacer: Ø8 × 2 mm washer-like disc
    sp = ws.new(PART, "spacer")
    sp.session.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "SpacerSketch"}},
        {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 4}},
        {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 1.7}},
        {"command": "sketch.finish", "params": {}},
        # pre-drilled: the bolt assistant then drills only V and M (drilling a shifted spacer failed)
        {"command": "solid.extrude", "params": {"sketch": "SpacerSketch", "distance": 2, "name": "Spacer",
                                                "body_name": "Spacer", "profiles": [{"point": [3, 0]}]}},
        {"command": "solid.chamfer", "params": {"edges": [[4, 0, 2], [4, 0, 0]], "distance": 0.3, "name": "SpacerEdge"}},
    ])
    sp.save()

    # V: two halves, one body each
    v = ws.new(PART, "logo_v")
    v.session.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "VLeftSketch"}},
        {"command": "sketch.line", "params": {"points": [[21, 78], [38, 78], [50, 64], [50, 44]], "closed": True}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "VLeftSketch", "distance": V_T, "name": "VLeft", "body_name": "VLeft"}},
        {"command": "sketch.create", "params": {"plane": "XY", "name": "VRightSketch"}},
        {"command": "sketch.line", "params": {"points": [[79, 78], [62, 78], [50, 64], [50, 44]], "closed": True}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "VRightSketch", "distance": V_T, "operation": "new",
                                                "name": "VRight", "body_name": "VRight"}},
    ])
    v.save()

    asm = ws.new(ASSEMBLY, "logo_showcase")
    links.insert(ws, asm, m.path, name="M", grounded=True)
    for i, (x, y) in enumerate(SCREWS, 1):
        links.insert(ws, asm, sp.path, name=f"Spacer{i}", translate=[x, y, 16], grounded=True)
    links.insert(ws, asm, v.path, name="V", translate=[0, 0, V_Z], grounded=True)
    asm.save()
    # Countersunk screws from the front through V and spacer into tapped blind holes in the M
    for x, y in SCREWS:
        r = bolted.bolted_connection(ws, "logo_showcase", placement={"position": [x, y, V_Z + V_T], "direction": [0, 0, -1]},
                                     size="M3", connection_type="blind", head="countersunk")
        print("bolt", x, {k: r.get(k) for k in ("screw", "parts", "warnings") if k in r})
    asm = ws.get("logo_showcase")
    asm.save()

    # One OBJ per body in world coordinates (the web UI's mesh, B-rep faces kept apart for crisp edges)
    out = folder / "render"
    out.mkdir()
    bodies = collect_mesh(asm)["bodies"]
    for b in bodies:
        pos, idx = b["positions"], b["indices"]
        with open(out / f"{b['name']}.obj", "w") as f:
            f.write(f"o {b['name']}\n")
            for i in range(0, len(pos), 3):
                f.write(f"v {pos[i]:.5f} {pos[i + 1]:.5f} {pos[i + 2]:.5f}\n")
            fids = b.get("face_ids") or []
            last = None
            for t in range(len(idx) // 3):
                if fids and fids[t] != last:
                    last = fids[t]
                    f.write(f"g face{last}\n")
                f.write(f"f {idx[t * 3] + 1} {idx[t * 3 + 1] + 1} {idx[t * 3 + 2] + 1}\n")
    print("bodies:", [b["name"] for b in bodies])
    for view in ("iso",):
        asm.session.tool("screenshot", {"view": view, "width": 1200, "height": 900, "grid": False,
                                        "path": str(folder / f"showcase-{view}.png")})
finally:
    ws.close_all()
