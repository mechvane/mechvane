"""The user's selection in the web UI, in the names Mechvane and the agent work with (ADR 0003, 3).

The SolidCraft app reports a selection as {type, body, index, point}: `point` is where the user
clicked. resolve() adds the face's Mechvane name, its type and normal, the centroid ("in the middle")
and the feature that made it. In an assembly the bodies' faces carry only names of the embedded copy,
so the face is matched in the linked part file instead and named there.
"""

import re

from .. import links, query
from ..documents import ASSEMBLY

MAX_ITEMS = 16


def _feature_names(s) -> dict[int, str]:
    return {f["id"]: f["name"] for f in s.cmd("document.inspect", {"measure": False}).get("timeline", [])}


def _feature_of(face_name, features) -> str | None:
    m = re.match(r"F(\d+):", face_name or "")
    return features.get(int(m.group(1))) if m else None


def _face_info(f, features) -> dict:
    out = {"name": f.get("name"), "surface": f.get("type") or ("cylinder" if f.get("cylinder") else
                                                              "plane" if f.get("plane_normal") else None),
           "centroid": f.get("centroid"), "feature": _feature_of(f.get("name"), features)}
    if f.get("plane_normal"):
        out["normal"] = f["plane_normal"]
    if f.get("cylinder"):
        out["radius"] = round(f["cylinder"]["radius"], 6)
        out["axis"] = f["cylinder"]["axis"]
    if f.get("area") is not None:
        out["area"] = f["area"]
    return {k: v for k, v in out.items() if v is not None}


def _part_face(ws, doc, body, f, click):
    """The face in the linked part file behind assembly body `body`, as {part, occurrence, face info}."""
    target = next((t for t in query._collect_bodies(doc, {}) if t["world_name"] == body), None)
    link = links._links(doc.session).get(target["component"]) if target else None
    if not link:
        return None
    path = ws._path(None, link["file"])
    reader = ws.reader(path)
    try:
        faces = links._part_faces(reader)
        features = _feature_names(reader)
    finally:
        reader.close()
    occ = {"transform": target["transform"]}
    z = f.get("plane_normal") or (f.get("cylinder") or {}).get("axis")
    o = click or f.get("point") or f.get("centroid")
    if o is None or z is None:
        return None
    o_part, z_part = links._to_part(occ, o, z)
    m = links._match(faces, o_part, z_part)
    if not m:
        return None
    pf = next((x for x in faces if x["name"] == m["face"]), None)
    info = _face_info(pf, features) if pf else {"name": m["face"]}
    return {"part": path.name, "occurrence": target["occurrence"],
            "click_in_part": [round(x, 4) for x in o_part], **info}


def resolve(ws, doc, items) -> list[dict]:
    """The selection items of the app, each with the names and geometry above."""
    s = doc.session
    features = _feature_names(s)
    faces, edges, out = {}, {}, []
    for it in (items or [])[:MAX_ITEMS]:
        kind, body, index, click = it.get("type"), it.get("body"), it.get("index"), it.get("point")
        entry = {"kind": kind, "body": body}
        if click is not None:
            entry["click"] = [round(x, 4) for x in click]
        try:
            if kind == "face":
                if body not in faces:
                    faces[body] = {f["index"]: f for f in s.cmd("model.faces", {"body": body}).get("faces", [])}
                f = faces[body].get(index)
                if f:
                    if doc.kind == ASSEMBLY:
                        entry.update(_part_face(ws, doc, body, f, click) or {"assembly_face": f.get("name")})
                    else:
                        entry.update(_face_info(f, features))
            elif kind == "edge":
                if body not in edges:
                    edges[body] = {e["index"]: e for e in s.cmd("model.edges", {"body": body}).get("edges", [])}
                e = edges[body].get(index)
                if e:
                    entry.update({k: e[k] for k in ("midpoint", "length", "name") if e.get(k) is not None})
                    if e.get("ends"):
                        entry["ends"] = e["ends"]
        except Exception as ex:  # an item that can't be resolved stays as the app gave it
            entry["error"] = str(ex)[:200]
        out.append(entry)
    return out

