"""Read SolidCraft 3MF-tagged exports and map face indices to B-rep face names."""

import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
FT_NS = "https://github.com/bherbruck/solidcraft/formats/3mf-face-tags/2026/10"


def parse_3mf(path_or_file) -> list[dict]:
    """Parse a 3MF (with optional face tags) into a list of body mesh dicts."""
    with zipfile.ZipFile(path_or_file) as zf:
        xml_bytes = zf.read("3D/3dmodel.model")
    root = ET.fromstring(xml_bytes)
    ft_face_attr = f"{{{FT_NS}}}face"
    ft_faces_attr = f"{{{FT_NS}}}faces"

    bodies = []
    for obj in root.findall(f".//{{{CORE_NS}}}object"):
        mesh_el = obj.find(f"{{{CORE_NS}}}mesh")
        if mesh_el is None:
            continue
        name = obj.attrib.get("name") or f"Object{obj.attrib.get('id', '')}"
        positions = []
        verts_el = mesh_el.find(f"{{{CORE_NS}}}vertices")
        if verts_el is not None:
            for v in verts_el.findall(f"{{{CORE_NS}}}vertex"):
                positions.extend((float(v.attrib["x"]), float(v.attrib["y"]), float(v.attrib["z"])))
        indices = []
        face_ids = []
        tris_el = mesh_el.find(f"{{{CORE_NS}}}triangles")
        if tris_el is not None:
            for t in tris_el.findall(f"{{{CORE_NS}}}triangle"):
                indices.extend((int(t.attrib["v1"]), int(t.attrib["v2"]), int(t.attrib["v3"])))
                face_ids.append(int(t.attrib.get(ft_face_attr, 0)))
        body = {
            "name": name,
            "positions": positions,
            "indices": indices,
            "face_ids": face_ids,
        }
        if ft_faces_attr in obj.attrib:
            body["face_count"] = int(obj.attrib[ft_faces_attr])
        bodies.append(body)
    return bodies


def _allowed_export_dir(doc_or_session, tmp_dir=None) -> Path:
    if tmp_dir is not None:
        return Path(tmp_dir)
    session = getattr(doc_or_session, "session", doc_or_session)
    args = getattr(getattr(session, "_p", None), "args", None) or []
    allowed = [Path(args[i + 1]) for i, a in enumerate(args[:-1]) if a == "--allow-path"]
    temp = Path(tempfile.gettempdir()).resolve()
    for p in allowed:
        if p.resolve() == temp or temp in p.resolve().parents:
            return p
    if hasattr(doc_or_session, "path") and doc_or_session.path:
        return Path(doc_or_session.path).parent
    if allowed:
        return allowed[0]
    return temp


def _body_faces(session, body_name: str) -> list[dict]:
    try:
        raw = session.cmd("model.faces", {"body": body_name}).get("faces", [])
    except Exception:
        base = body_name.split(" (")[0]
        raw = session.cmd("model.faces", {"body": base}).get("faces", []) if base != body_name else []
    return [{"index": int(f["index"]), "name": f["name"]} for f in sorted(raw, key=lambda x: x["index"])]


def collect_mesh(doc_or_session, tmp_dir=None) -> dict:
    """Export the open design as 3mf-tagged and attach B-rep face names per body."""
    session = getattr(doc_or_session, "session", doc_or_session)
    export_dir = _allowed_export_dir(doc_or_session, tmp_dir=tmp_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="ui1-", suffix=".3mf", dir=str(export_dir))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        session.tool("export", {"path": str(tmp_path), "format": "3mf-tagged"})
        raw_bodies = parse_3mf(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    bodies = []
    for b in raw_bodies:
        faces = _body_faces(session, b["name"])
        bodies.append({
            "name": b["name"],
            "positions": b["positions"],
            "indices": b["indices"],
            "face_ids": b["face_ids"],
            "faces": faces,
        })
    return {"bodies": bodies}


export_mesh = collect_mesh
