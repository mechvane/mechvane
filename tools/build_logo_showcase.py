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
from mechvane import bolted, gltf_export, links  # noqa: E402
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


REPO = Path(__file__).resolve().parents[1]
LOOKS = json.loads((REPO / "tools" / "logo_looks.json").read_text())["looks"]
LIBRARY = REPO / "katalog" / "werkstoffe.solidcraft-library.json"


def srgb_hex(linear):
    """Linear RGB (as in logo_looks.json) to the sRGB "#rrggbb" SolidCraft takes."""
    out = [(12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055) for c in linear]
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02x}" for c in out)


def look(name):
    """SolidCraft appearance params from a look of logo_looks.json (colour and PBR; anisotropy and coat
    have no place in SolidCraft and stay in the Blender route)."""
    p = LOOKS[name]
    return {"color": srgb_hex(p["base_color"]),
            "pbr": {"metallic": p.get("base_metalness", 0.0), "roughness": max(0.045, p.get("specular_roughness", 0.5)),
                    "dielectric_ior": 1.5}}


def library_material(doc, name, bodies):
    """Assign a material of the catalog library (katalog/werkstoffe.solidcraft-library.json) to bodies."""
    target = Path(doc.path).parent / LIBRARY.name
    if not target.exists():
        shutil.copyfile(LIBRARY, target)
    entry = next(e for e in json.loads(LIBRARY.read_text())["entries"]
                 if e["definition"]["kind"] == "material" and e["definition"]["value"]["name"] == name)
    doc.session.cmd("library.apply", {"path": str(target), "entry": entry["id"], "revision": entry["revision"],
                                      "targets": {"bodies": bodies}})


def inside(pt, poly):
    """Point in polygon (even-odd)."""
    x, y, c = pt[0], pt[1], False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def m_face_points():
    """A point on each upright side of the M (mid height) and on the weld fillet at its foot."""
    sides, welds = [], []
    for (x1, y1), (x2, y2) in zip(M_OUTLINE, M_OUTLINE[1:] + M_OUTLINE[:1]):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        nx, ny = (y2 - y1) / length, -(x2 - x1) / length
        if inside([mx + 0.1 * nx, my + 0.1 * ny], M_OUTLINE):
            nx, ny = -nx, -ny                      # outward
        sides.append([mx, my, 11])
        d = 2.0 - 2.0 * 0.5 ** 0.5                 # r 2 fillet, its middle at 45°
        welds.append([mx + d * nx, my + d * ny, 6 + d])
    return sides, welds


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
    # steel, powder-coated: plate navy, the M light grey, the welds bare metal
    library_material(m, "S235JR", ["Plate"])
    m.session.cmd("appearance.assign", dict(bodies=["Plate"], **look("coat_dark")))
    sides, welds = m_face_points()
    m.session.cmd("appearance.assign", dict(faces=sides + [[28, 40, 16], [72, 40, 16], [50, 52, 16]], body="Plate",
                                            **look("coat_light")))
    m.session.cmd("appearance.assign", dict(faces=welds, body="Plate", **look("weld")))
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
    library_material(sp, "1.4301 (X5CrNi18-10)", ["Spacer"])
    sp.session.cmd("appearance.assign", dict(bodies=["Spacer"], **look("steel_brushed")))
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
    library_material(v, "CuZn39Pb3 (CW614N)", ["VLeft"])
    v.session.cmd("material.assign", {"bodies": ["VRight"], "material": "Copper"})
    v.session.cmd("appearance.assign", dict(bodies=["VLeft"], **look("brass_brushed")))
    v.session.cmd("appearance.assign", dict(bodies=["VRight"], **look("copper_polished")))
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
    # the screws: black oxide
    screw = ws.get("ISO_10642_M3x6") if "ISO_10642_M3x6" in ws.docs else ws.open("ISO_10642_M3x6.solidcraft")
    screw_body = screw.session.cmd("document.inspect", {"measure": False})["bodies"][0]["name"]
    screw.session.cmd("appearance.assign", dict(bodies=[screw_body], **look("black_oxide")))
    screw.save()
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
    # the same model with its SolidCraft looks, through Mechvane's general glTF export
    print("gltf:", gltf_export.export_gltf(asm, folder / "logo_showcase.gltf", ws=ws))
    for view in ("iso",):
        asm.session.tool("screenshot", {"view": view, "width": 1200, "height": 900, "grid": False,
                                        "path": str(folder / f"showcase-{view}.png")})
finally:
    ws.close_all()
