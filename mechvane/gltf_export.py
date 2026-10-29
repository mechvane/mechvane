"""Export a part or assembly as glTF 2.0 with its appearance (ADR 0004).

Meshes come from the web UI's export (one per body, world coordinates, B-rep face per triangle); the look
of each body from SolidCraft: an appearance assigned to the body, else the default look of its material;
faces with an appearance of their own (assigned by a point) get it too.
Colour and PBR (metallic, roughness, IOR) map to pbrMetallicRoughness and KHR_materials_ior. Normals are
written per B-rep face, so edges between faces stay sharp. Units: metres, Y up, as glTF wants.
"""
import base64
import json
import re
import struct
from pathlib import Path

from .ui.mesh import collect_mesh

# Built-in SolidCraft materials without a PBR look that are metals
METALS = {"Steel", "Stainless Steel", "Aluminum", "Brass", "Copper", "Titanium", "Cast Iron"}


def _linear(hex_color: str) -> list[float]:
    """sRGB "#rrggbb" to linear RGB, as glTF's baseColorFactor expects."""
    out = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def _look(material: str | None, appearance: dict | None) -> dict:
    """glTF material for a body from its appearance (or its material's default look)."""
    appearance = appearance or {}
    color = appearance.get("color") or "#b4b8bc"
    if isinstance(color, list):
        color = "#%02x%02x%02x" % tuple(int(c) for c in color[:3])
    pbr = appearance.get("pbr") or {}
    metal = material in METALS
    m = {"name": appearance.get("name") or material or "Default",
         "pbrMetallicRoughness": {"baseColorFactor": [*_linear(color), float(appearance.get("opacity", 1.0))],
                                  "metallicFactor": float(pbr.get("metallic", 1.0 if metal else 0.0)),
                                  "roughnessFactor": float(pbr.get("roughness", 0.35 if metal else 0.5))}}
    if "dielectric_ior" in pbr:
        m["extensions"] = {"KHR_materials_ior": {"ior": float(pbr["dielectric_ior"])}}
    if m["pbrMetallicRoughness"]["baseColorFactor"][3] < 1.0:
        m["alphaMode"] = "BLEND"
    return m


def _face_at(body, point, tol=1e-2):
    """B-rep face id of the triangle of body that contains point (mm), or None."""
    pos, idx, fids = body["positions"], body["indices"], body.get("face_ids") or []
    for t in range(len(idx) // 3):
        a, b, c = (pos[idx[t * 3 + k] * 3:idx[t * 3 + k] * 3 + 3] for k in range(3))
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        w = [point[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        nn = sum(x * x for x in n)
        if nn < 1e-18 or abs(sum(w[i] * n[i] for i in range(3))) / nn ** 0.5 > tol:
            continue
        # barycentric coordinates of the point in the triangle
        uu, uv, vv = (sum(x * y for x, y in zip(p, q)) for p, q in ((u, u), (u, v), (v, v)))
        wu, wv = sum(x * y for x, y in zip(w, u)), sum(x * y for x, y in zip(w, v))
        den = uv * uv - uu * vv
        s_ = (uv * wv - vv * wu) / den
        t_ = (uv * wu - uu * wv) / den
        if s_ >= -1e-6 and t_ >= -1e-6 and s_ + t_ <= 1 + 1e-6:
            return fids[t] if t < len(fids) else 0
    return None


def _face_looks(session, bodies) -> dict:
    """{(body, face id): glTF material} from appearances assigned to faces by a point."""
    by_name = {b["name"]: b for b in bodies}
    out = {}
    for f in (session.cmd("appearance.list", {}) or {}).get("faces", []) or []:
        body = by_name.get(f.get("body"))
        fid = _face_at(body, f.get("point") or []) if body else None
        if fid is not None:
            out[(body["name"], fid)] = _look(None, f.get("appearance"))
    return out


def _body_looks(session, names) -> dict:
    """{body: glTF material} from the body appearances and materials of the open design."""
    assigned = (session.cmd("appearance.list", {}) or {}).get("bodies", {}) or {}
    materials = {b["name"]: b.get("material") for b in session.tool("measure", {}).get("bodies", [])}
    cache = {}
    looks = {}
    for name in names:
        mat = materials.get(name)
        app = assigned.get(name)
        if app is None and mat:
            if mat not in cache:
                try:
                    cache[mat] = session.cmd("material.inspect", {"material": mat}).get("appearance")
                except Exception:  # noqa: BLE001 - an unknown material keeps the neutral look
                    cache[mat] = None
            app = cache[mat]
        looks[name] = _look(mat, app)
    return looks


def _faces_split(body):
    """One vertex per (vertex, B-rep face), normals averaged within each face; triangles carry their face."""
    pos, idx, fids = body["positions"], body["indices"], body.get("face_ids") or []
    key, out_pos, out_nrm, tris = {}, [], [], []
    for t in range(len(idx) // 3):
        v = [idx[t * 3 + k] for k in range(3)]
        p = [pos[i * 3:i * 3 + 3] for i in v]
        u = [p[1][k] - p[0][k] for k in range(3)]
        w = [p[2][k] - p[0][k] for k in range(3)]
        n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        f = fids[t] if t < len(fids) else 0
        tri = []
        for i in v:
            j = key.setdefault((i, f), len(out_pos))
            if j == len(out_pos):
                out_pos.append(pos[i * 3:i * 3 + 3])
                out_nrm.append([0.0, 0.0, 0.0])
            out_nrm[j] = [out_nrm[j][k] + n[k] for k in range(3)]
            tri.append(j)
        tris.append((tri, f))
    unit = lambda v: [x / ((sum(y * y for y in v) ** 0.5) or 1.0) for x in v]  # noqa: E731
    return out_pos, [unit(n) for n in out_nrm], tris


def _part_looks(session) -> tuple[dict, list]:
    """Looks of a part's own bodies and its face appearances (part coordinates)."""
    names = [b["name"] for b in session.cmd("document.inspect", {"measure": False}).get("bodies", [])]
    faces = (session.cmd("appearance.list", {}) or {}).get("faces", []) or []
    return _body_looks(session, names), faces


def _assembly_looks(ws, doc, bodies) -> tuple[dict, dict]:
    """Looks for an assembly's bodies from the part files they come from: SolidCraft keeps appearances and
    materials in the parts, the assembly session does not see them."""
    from . import geometry as g, links, query
    lmap = links._links(doc.session)
    by_name = {b["name"]: b for b in bodies}
    looks, face_looks, cache = {}, {}, {}
    for t in query._collect_bodies(doc, None):
        link = lmap.get(t.get("component"))
        body = by_name.get(t["world_name"])
        if not link or body is None:
            continue
        if link["file"] not in cache:
            reader = ws.reader(link["file"])
            try:
                cache[link["file"]] = _part_looks(reader)
            finally:
                reader.close()
        part_looks, part_faces = cache[link["file"]]
        base = re.sub(r" \(\d+\)$", "", t["base_name"])
        looks[t["world_name"]] = part_looks.get(base) or _look(None, None)
        for f in part_faces:
            if re.sub(r" \(\d+\)$", "", f.get("body", "")) != base:
                continue
            point = g.apply_point(t["transform"], f["point"]) if t.get("transform") else f["point"]
            fid = _face_at(body, point)
            if fid is not None:
                face_looks[(t["world_name"], fid)] = _look(None, f.get("appearance"))
    return looks, face_looks


def export_gltf(doc, path, ws=None) -> dict:
    """Write doc (part or assembly) as glTF 2.0 with one mesh and one material per body. For an assembly
    pass its workspace ws, so the looks come from the part files."""
    bodies = [b for b in collect_mesh(doc).get("bodies", []) if b.get("positions")]
    if ws is not None and getattr(doc, "kind", None) == "assembly":
        looks, face_looks = _assembly_looks(ws, doc, bodies)
        for b in bodies:
            looks.setdefault(b["name"], _look(None, None))
    else:
        looks = _body_looks(doc.session, [b["name"] for b in bodies])
        face_looks = _face_looks(doc.session, bodies)
    gltf = {"asset": {"version": "2.0", "generator": "Mechvane"}, "scene": 0, "scenes": [{"nodes": []}],
            "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": []}
    blob = bytearray()
    mat_index = {}

    def view(data: bytes, target: int) -> int:
        while len(blob) % 4:
            blob.append(0)
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)
        return len(gltf["bufferViews"]) - 1

    def accessor(values, fmt, kind, target, component=5126, minmax=False):
        acc = {"bufferView": view(b"".join(struct.pack("<" + fmt, *x) for x in values), target),
               "componentType": component, "count": len(values) * (3 if kind == "SCALAR" else 1), "type": kind}
        if minmax:
            acc["min"] = [min(x[i] for x in values) for i in range(3)]
            acc["max"] = [max(x[i] for x in values) for i in range(3)]
        gltf["accessors"].append(acc)
        return len(gltf["accessors"]) - 1

    for b in bodies:
        pos, nrm, tris = _faces_split(b)
        to_gltf = lambda p: (p[0] / 1000, p[2] / 1000, -p[1] / 1000)  # noqa: E731  mm, Z up -> m, Y up
        attrs = {"POSITION": accessor([to_gltf(p) for p in pos], "3f", "VEC3", 34962, minmax=True),
                 "NORMAL": accessor([(n[0], n[2], -n[1]) for n in nrm], "3f", "VEC3", 34962)}
        groups = {}
        for tri, f in tris:
            look = face_looks.get((b["name"], f), looks[b["name"]])
            key = json.dumps(look, sort_keys=True)
            if key not in mat_index:
                gltf["materials"].append(look)
                mat_index[key] = len(gltf["materials"]) - 1
            groups.setdefault(mat_index[key], []).append(tri)
        prims = [{"attributes": attrs, "indices": accessor(ts, "3I", "SCALAR", 34963, component=5125), "material": m}
                 for m, ts in groups.items()]
        gltf["meshes"].append({"name": b["name"], "primitives": prims})
        gltf["nodes"].append({"name": b["name"], "mesh": len(gltf["meshes"]) - 1})
        gltf["scenes"][0]["nodes"].append(len(gltf["nodes"]) - 1)
    if any("extensions" in m for m in gltf["materials"]):
        gltf["extensionsUsed"] = ["KHR_materials_ior"]
    gltf["buffers"] = [{"byteLength": len(blob),
                        "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(blob)).decode()}]
    Path(path).write_text(json.dumps(gltf), encoding="utf-8")
    return {"path": str(path), "bodies": len(bodies), "materials": [m["name"] for m in gltf["materials"]]}
