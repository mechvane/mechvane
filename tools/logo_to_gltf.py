"""Write the logo showcase as glTF 2.0 with its looks, for route B of the ADR 0004 probe.

    python3 tools/logo_to_gltf.py [render-folder]   (default workspace/logo_showcase/render)

Reads the OBJ files of tools/build_logo_showcase.py and tools/logo_looks.json (OpenPBR parameters) and writes
logo.gltf (buffer embedded) next to them. OpenPBR maps to glTF like this: base_color, base_metalness and
specular_roughness to pbrMetallicRoughness, coat_weight/coat_roughness to KHR_materials_clearcoat,
specular_anisotropy to KHR_materials_anisotropy. Positions are written in Blender units (1 = 100 mm) with
glTF's Y up, so Blender's importer puts the model exactly where the direct route does. Normals per B-rep
face keep edges sharp; tangents and UVs run along Blender Y, the brushing direction of the direct route.
"""
import base64
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
folder = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "workspace" / "logo_showcase" / "render"
spec = json.loads((REPO / "tools" / "logo_looks.json").read_text())
SCALE = 0.01


def read_obj(path):
    """Vertices and triangles, each triangle with the B-rep face (OBJ group) it belongs to."""
    verts, tris, group = [], [], None
    for line in path.read_text().splitlines():
        if line.startswith("v "):
            verts.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("g "):
            group = line[2:].strip()
        elif line.startswith("f "):
            tris.append(([int(x.split("/")[0]) - 1 for x in line.split()[1:4]], group))
    return verts, tris


def unit(v):
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]


def tri_normal(v, t):
    a, b, c = (v[i] for i in t)
    u = [b[k] - a[k] for k in range(3)]
    w = [c[k] - a[k] for k in range(3)]
    return [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]


def split_by_face(v, tris):
    """One vertex per (vertex, B-rep face), normals averaged within the face only, so edges between faces
    stay sharp; tangent along Blender Y (the brushing direction), made perpendicular to the normal."""
    key_to_new, pos, nrm, tri_out = {}, [], [], []
    for t, g in tris:
        n = tri_normal(v, t)
        new = []
        for i in t:
            k = (i, g)
            if k not in key_to_new:
                key_to_new[k] = len(pos)
                pos.append(v[i])
                nrm.append([0.0, 0.0, 0.0])
            j = key_to_new[k]
            nrm[j] = [nrm[j][d] + n[d] for d in range(3)]
            new.append(j)
        tri_out.append((new, g))
    nrm = [unit(n) for n in nrm]
    tan = []
    for n in nrm:
        d = [0.0, 1.0, 0.0]
        dot = sum(d[k] * n[k] for k in range(3))
        t = [d[k] - dot * n[k] for k in range(3)]
        if sum(x * x for x in t) < 1e-6:
            t = [1.0, 0.0, 0.0]
        tan.append(unit(t))
    return pos, nrm, tan, tri_out


def plate_look(v, t):
    """Same rule as the direct route: weld on slanted faces at the foot, light above the plate, dark below."""
    a, b, c = (v[i] for i in t)
    n = tri_normal(v, t)
    length = sum(x * x for x in n) ** 0.5 or 1.0
    nz = abs(n[2] / length)
    cz = (a[2] + b[2] + c[2]) / 3
    if 6.0 < cz < 8.2 and 0.15 < nz < 0.97:
        return "weld"
    return "coat_light" if cz > 6.3 else "coat_dark"


def material(name, p):
    m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": [*p["base_color"], 1.0],
                                               "metallicFactor": p.get("base_metalness", 0.0),
                                               "roughnessFactor": p.get("specular_roughness", 0.3)}}
    ext = {}
    if p.get("coat_weight"):
        ext["KHR_materials_clearcoat"] = {"clearcoatFactor": p["coat_weight"],
                                          "clearcoatRoughnessFactor": p.get("coat_roughness", 0.03)}
    if p.get("specular_anisotropy"):
        ext["KHR_materials_anisotropy"] = {"anisotropyStrength": p["specular_anisotropy"], "anisotropyRotation": 0.0}
    if ext:
        m["extensions"] = ext
    return m


looks = spec["looks"]
names = list(looks)
gltf = {"asset": {"version": "2.0", "generator": "Mechvane tools/logo_to_gltf.py"},
        "extensionsUsed": ["KHR_materials_clearcoat", "KHR_materials_anisotropy"],
        "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "accessors": [], "bufferViews": [],
        "materials": [material(k, v) for k, v in looks.items()]}
blob = bytearray()


def add_view(data: bytes, target):
    while len(blob) % 4:
        blob.append(0)
    gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
    blob.extend(data)
    return len(gltf["bufferViews"]) - 1


def to_gltf(p):
    return (p[0], p[2], -p[1])   # Blender Z up -> glTF Y up


def accessor(values, fmt, kind, target, minmax=False):
    view = add_view(b"".join(struct.pack("<" + fmt, *x) for x in values), target)
    acc = {"bufferView": view, "componentType": 5126, "count": len(values), "type": kind}
    if minmax:
        acc["min"] = [min(x[i] for x in values) for i in range(3)]
        acc["max"] = [max(x[i] for x in values) for i in range(3)]
    gltf["accessors"].append(acc)
    return len(gltf["accessors"]) - 1


for obj in sorted(folder.glob("*.obj")):
    v, tris = read_obj(obj)
    pos_b, nrm_b, tan_b, tris = split_by_face(v, tris)
    groups = {}
    for t, _ in tris:
        look = plate_look(pos_b, t) if obj.stem in ("Plate", "M") else spec["bodies"].get(obj.stem, "steel_brushed")
        groups.setdefault(look, []).append(t)
    attrs = {
        "POSITION": accessor([[c * SCALE for c in to_gltf(p)] for p in pos_b], "3f", "VEC3", 34962, minmax=True),
        "NORMAL": accessor([to_gltf(n) for n in nrm_b], "3f", "VEC3", 34962),
        "TANGENT": accessor([[*to_gltf(t), 1.0] for t in tan_b], "4f", "VEC4", 34962),
        # U runs along the brushing direction (Blender Y), so a UV-based tangent agrees with TANGENT
        "TEXCOORD_0": accessor([[p[1] * SCALE, p[0] * SCALE] for p in pos_b], "2f", "VEC2", 34962),
    }
    prims = []
    for look, ts in groups.items():
        iview = add_view(b"".join(struct.pack("<3I", *t) for t in ts), 34963)
        gltf["accessors"].append({"bufferView": iview, "componentType": 5125, "count": 3 * len(ts), "type": "SCALAR"})
        prims.append({"attributes": attrs, "indices": len(gltf["accessors"]) - 1, "material": names.index(look)})
    gltf["meshes"].append({"name": obj.stem, "primitives": prims})
    gltf["nodes"].append({"name": obj.stem, "mesh": len(gltf["meshes"]) - 1})
    gltf["scenes"][0]["nodes"].append(len(gltf["nodes"]) - 1)

gltf["buffers"] = [{"byteLength": len(blob),
                    "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(blob)).decode()}]
(folder / "logo.gltf").write_text(json.dumps(gltf))
print("wrote", folder / "logo.gltf", len(gltf["meshes"]), "meshes,", len(blob), "bytes")
