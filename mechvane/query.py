"""Semantic queries for parts and assemblies: find faces, edges, and holes matching filters.
Avoids expensive body_topology calls by leveraging model.faces and model.edges directly."""

import math
from pathlib import Path
import re

from . import geometry as g
from .links import _links, _occurrences
from .solidcraft import Session


class QueryList(list):
    """A list of query results supporting dict-like access for compatibility."""

    def __init__(self, items, what):
        super().__init__(items)
        self.what = what

    def get(self, key, default=None):
        if key in ("items", self.what):
            return list(self)
        if key == "count":
            return len(self)
        return default

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in ("items", self.what):
                return list(self)
            if key == "count":
                return len(self)
            raise KeyError(key)
        return super().__getitem__(key)


_eval_length = g.eval_length


def _match_num(val, rule):
    if val is None:
        return False
    if isinstance(rule, (int, float)):
        return abs(val - rule) < 1e-3
    if isinstance(rule, (list, tuple)):
        if len(rule) == 2 and isinstance(rule[0], str):
            op, target = rule[0], float(rule[1])
            if op == ">":
                return val > target - 1e-4
            if op == ">=":
                return val >= target - 1e-4
            if op == "<":
                return val < target + 1e-4
            if op == "<=":
                return val <= target + 1e-4
            if op in ("==", "="):
                return abs(val - target) < 1e-3
        elif len(rule) == 2 and isinstance(rule[0], (int, float)) and isinstance(rule[1], (int, float)):
            lo, hi = sorted([float(rule[0]), float(rule[1])])
            return (lo - 1e-4) <= val <= (hi + 1e-4)
    return False


def _parse_normal(n):
    if isinstance(n, str):
        s = n.strip().upper()
        dirs = {
            "+Z": [0.0, 0.0, 1.0], "Z": [0.0, 0.0, 1.0], "-Z": [0.0, 0.0, -1.0],
            "+Y": [0.0, 1.0, 0.0], "Y": [0.0, 1.0, 0.0], "-Y": [0.0, -1.0, 0.0],
            "+X": [1.0, 0.0, 0.0], "X": [1.0, 0.0, 0.0], "-X": [-1.0, 0.0, 0.0],
        }
        if s in dirs:
            return dirs[s]
    if isinstance(n, (list, tuple)) and len(n) == 3:
        return g.unit([float(x) for x in n])
    return None


def _match_normal(n1, n2, tol=1e-3):
    if not n1 or not n2:
        return False
    return g.dot(g.unit(n1), g.unit(n2)) > 1.0 - tol


def _match_near(pt, near_pt, within=1.0):
    if not pt or not near_pt:
        return False
    return g.norm(g.sub(pt, near_pt)) <= (within + 1e-4)


def _match_feature(name, feat_query, tl_map, tl_by_name):
    if not feat_query:
        return True
    s_feat = str(feat_query).strip()
    target_id = None
    if s_feat.lower() in tl_by_name:
        target_id = tl_by_name[s_feat.lower()]
    elif s_feat.isdigit():
        target_id = int(s_feat)
    elif s_feat.startswith("F") and s_feat[1:].isdigit():
        target_id = int(s_feat[1:])

    if target_id is not None:
        if name.startswith(f"F{target_id}:") or f"|F{target_id}:" in name or f":{target_id}:" in name:
            return True
        # Edge name check like F1:+z|F3:side:c1#1
        for part in name.split("|"):
            fn = part.split("~")[0]
            if fn.startswith(f"F{target_id}:"):
                return True
    return s_feat.lower() in name.lower()


def _circumcenter_3pts(p1, p2, p3):
    """Compute circumcenter and radius of circle passing through 3 non-collinear points."""
    v1 = g.sub(p2, p1)
    v2 = g.sub(p3, p1)
    cross_v = g.cross(v1, v2)
    norm_c = g.norm(cross_v)
    if norm_c < 1e-6:
        return None, None
    a = g.norm(g.sub(p3, p2))
    b = g.norm(g.sub(p1, p3))
    c = g.norm(g.sub(p2, p1))
    radius = (a * b * c) / (2.0 * norm_c)
    # Center calculation
    alpha = (a * a * (b * b + c * c - a * a))
    beta = (b * b * (c * c + a * a - b * b))
    gamma = (c * c * (a * a + b * b - c * c))
    total = alpha + beta + gamma
    if abs(total) < 1e-9:
        return None, None
    center = [
        (alpha * p1[i] + beta * p2[i] + gamma * p3[i]) / total
        for i in range(3)
    ]
    return center, radius


def _is_end_cap(face, feat_id) -> bool:
    """A non-cylindrical face of the feature that closes the hole; counterbore and countersink
    steps (:cbore:, :csink:) are openings, not bottoms."""
    name = face["name"]
    return (name.startswith(f"F{feat_id}:") and not face.get("cylinder")
            and ":cbore:" not in name and ":csink:" not in name)


def _collect_bodies(doc, where):
    s = doc.session
    body_filter = where.get("body") if where else None
    occ_filter = where.get("occurrence") if where else None

    if doc.kind == "assembly":
        occs = _occurrences(s)
        comps = {c["id"]: c for c in s.cmd("component.list").get("components", [])}
        targets = []
        for occ in occs.values():
            occ_name = occ.get("path") or occ["name"]
            if occ_filter and occ_filter not in (occ["name"], occ.get("path")):
                continue
            comp = comps.get(occ["component"])
            if not comp or not comp.get("bodies"):
                continue
            is_first = (comp.get("occurrences") and comp["occurrences"][0]["id"] == occ["id"])
            for b in comp["bodies"]:
                if body_filter and b != body_filter:
                    continue
                world_name = b if is_first else f"{b} ({occ['name']})"
                targets.append({
                    "world_name": world_name,
                    "base_name": b,
                    "occurrence": occ_name,
                    "transform": occ["transform"],
                    "component": occ["component"],
                })
        return targets

    # Part document
    insp = s.cmd("document.inspect", {"measure": False})
    targets = []
    for b in insp.get("bodies", []):
        name = b["name"]
        if body_filter and name != body_filter:
            continue
        targets.append({
            "world_name": name,
            "base_name": name,
            "occurrence": None,
            "transform": None,
        })
    return targets


def _get_timeline_info(session):
    doc_info = session.cmd("document.inspect", {"measure": False})
    tl = doc_info.get("timeline", [])
    tl_map = {f["id"]: f for f in tl if isinstance(f, dict) and "id" in f}
    tl_by_name = {f["name"].lower(): f["id"] for f in tl if isinstance(f, dict) and "name" in f}
    return tl, tl_map, tl_by_name


def _fetch_faces_and_edges(session, bt):
    try:
        faces = session.cmd("model.faces", {"body": bt["world_name"]}).get("faces", [])
    except Exception:
        faces = session.cmd("model.faces", {"body": bt["base_name"]}).get("faces", [])
        if bt.get("transform"):
            faces = [_transform_face(f, bt["transform"]) for f in faces]

    try:
        edges = session.cmd("model.edges", {"body": bt["world_name"]}).get("edges", [])
    except Exception:
        edges = session.cmd("model.edges", {"body": bt["base_name"]}).get("edges", [])
        if bt.get("transform"):
            edges = [_transform_edge(e, bt["transform"]) for e in edges]

    return faces, edges


def _transform_face(f, m):
    f = dict(f)
    if f.get("point"):
        f["point"] = g.apply_point(m, f["point"])
    if f.get("centroid"):
        f["centroid"] = g.apply_point(m, f["centroid"])
    if f.get("plane_normal"):
        f["plane_normal"] = g.unit(g.apply_dir(m, f["plane_normal"]))
    if f.get("cylinder"):
        c = dict(f["cylinder"])
        c["origin"] = g.apply_point(m, c["origin"])
        c["axis"] = g.unit(g.apply_dir(m, c["axis"]))
        f["cylinder"] = c
    return f


def _transform_edge(e, m):
    e = dict(e)
    if e.get("mid"):
        e["mid"] = g.apply_point(m, e["mid"])
    if e.get("start"):
        e["start"] = g.apply_point(m, e["start"])
    if e.get("end"):
        e["end"] = g.apply_point(m, e["end"])
    return e


def _query_faces(doc, targets, where, limit, tl_map, tl_by_name):
    items = []
    want_type = where.get("type") if where else None
    want_normal = _parse_normal(where.get("normal")) if (where and "normal" in where) else None
    want_diam = where.get("diameter") if where else None
    want_area = where.get("area") if where else None
    want_near = where.get("near") if where else None
    within = where.get("within", 1.0) if where else 1.0
    want_feature = where.get("feature") if where else None

    for bt in targets:
        faces, _ = _fetch_faces_and_edges(doc.session, bt)
        for f in faces:
            ftype = "plane" if f.get("plane_normal") else ("cylinder" if f.get("cylinder") else "other")
            if want_type:
                w_t = want_type.lower()
                if w_t in ("plane", "planar") and ftype != "plane":
                    continue
                if w_t in ("cylinder", "cylindrical") and ftype != "cylinder":
                    continue
                if w_t not in ("plane", "planar", "cylinder", "cylindrical") and ftype != w_t:
                    continue

            if want_normal and (ftype != "plane" or not _match_normal(f.get("plane_normal"), want_normal)):
                continue

            cyl = f.get("cylinder")
            diam = (2.0 * cyl["radius"]) if cyl else None
            if want_diam and (diam is None or not _match_num(diam, want_diam)):
                continue

            if want_area and not _match_num(f.get("area"), want_area):
                continue

            pick = f.get("point") or f.get("centroid")
            if want_near and not _match_near(pick, want_near, within):
                continue

            if want_feature and not _match_feature(f["name"], want_feature, tl_map, tl_by_name):
                continue

            item = {
                "name": f["name"],
                "type": ftype,
                "area": round(f["area"], 4) if f.get("area") is not None else None,
                "pick": [round(x, 4) for x in pick] if pick else None,
                "centroid": [round(x, 4) for x in f["centroid"]] if f.get("centroid") else None,
                "body": bt["base_name"],
            }
            if bt["occurrence"]:
                item["occurrence"] = bt["occurrence"]
            if ftype == "plane":
                item["normal"] = [round(x, 4) for x in f["plane_normal"]]
            elif ftype == "cylinder":
                item["radius"] = round(cyl["radius"], 4)
                item["diameter"] = round(diam, 4)
                item["axis"] = [round(x, 4) for x in cyl["axis"]]
                item["origin"] = [round(x, 4) for x in cyl["origin"]]

            items.append(item)
            if len(items) >= limit:
                return items
    return items


def _query_edges(doc, targets, where, limit, tl_map, tl_by_name):
    items = []
    want_edge = where.get("edge") or where.get("type") if where else None
    want_len = where.get("length") if where else None
    want_near = where.get("near") if where else None
    within = where.get("within", 1.0) if where else 1.0
    want_feature = where.get("feature") if where else None

    for bt in targets:
        faces, edges = _fetch_faces_and_edges(doc.session, bt)
        fmap = {f["name"]: f for f in faces}

        for e in edges:
            d_end = g.norm(g.sub(e["end"], e["start"]))
            is_straight = abs(e["length"] - d_end) < 1e-3

            fnames = [fn.split("~")[0] for fn in e["name"].split("|")]
            cyl_f = next((fmap[fn] for fn in fnames if fn in fmap and fmap[fn].get("cylinder")), None)

            radius, diameter, center = None, None, None
            if is_straight:
                etype = "line"
            elif cyl_f:
                etype = "circle"
                cyl = cyl_f["cylinder"]
                axis = g.unit(cyl["axis"])
                radius = cyl["radius"]
                diameter = 2.0 * radius
                center = g.add(cyl["origin"], g.scale(axis, g.dot(g.sub(e["mid"], cyl["origin"]), axis)))
            else:
                c_pt, r = _circumcenter_3pts(e["start"], e["mid"], e["end"])
                if c_pt is not None:
                    etype = "circle"
                    radius = r
                    diameter = 2.0 * r
                    center = c_pt
                else:
                    etype = "other"

            if want_edge:
                w_e = want_edge.lower()
                if w_e in ("circle", "arc") and etype != "circle":
                    continue
                if w_e == "line" and etype != "line":
                    continue

            if want_len and not _match_num(e["length"], want_len):
                continue

            pick = e["mid"]
            if want_near and not _match_near(pick, want_near, within):
                continue

            if want_feature and not _match_feature(e["name"], want_feature, tl_map, tl_by_name):
                continue

            item = {
                "name": e["name"],
                "type": etype,
                "length": round(e["length"], 4),
                "pick": [round(x, 4) for x in pick],
                "body": bt["base_name"],
            }
            if bt["occurrence"]:
                item["occurrence"] = bt["occurrence"]
            if etype == "line":
                item["start"] = [round(x, 4) for x in e["start"]]
                item["end"] = [round(x, 4) for x in e["end"]]
            elif etype == "circle":
                item["radius"] = round(radius, 4)
                item["diameter"] = round(diameter, 4)
                if center:
                    item["center"] = [round(x, 4) for x in center]

            items.append(item)
            if len(items) >= limit:
                return items
    return items


def _query_holes(doc, targets, where, limit, tl_map, tl_by_name):
    items = []
    want_diam = where.get("diameter") if where else None
    want_through = where.get("through") if where else None
    want_depth = where.get("depth") if where else None
    want_near = where.get("near") if where else None
    within = where.get("within", 1.0) if where else 1.0
    want_feature = where.get("feature") if where else None

    # Load feature inspection definitions once
    for f in tl_map.values():
        if f.get("type") in ("HoleFeature", "CylinderFeature", "ExtrudeFeature") and "definition" not in f:
            try:
                insp = doc.session.cmd("timeline.inspect", {"feature": f["id"]})
                if isinstance(insp, dict):
                    f["definition"] = insp.get("definition", {})
            except Exception:
                pass

    for bt in targets:
        faces, edges = _fetch_faces_and_edges(doc.session, bt)
        cyl_faces = [f for f in faces if f.get("cylinder")]
        groups = g.group_cylindrical_faces(cyl_faces)

        all_pts = [f["point"] for f in faces if f.get("point")]
        bbox = None
        if all_pts:
            bbox = {
                "min": [min(p[0] for p in all_pts), min(p[1] for p in all_pts), min(p[2] for p in all_pts)],
                "max": [max(p[0] for p in all_pts), max(p[1] for p in all_pts), max(p[2] for p in all_pts)],
            }

        is_hole_list = g.classify_hole_groups(doc.session, bt.get("world_name") or bt.get("base_name"),
                                              groups, tl_map, bbox=bbox,
                                              probe=doc.kind != "assembly")

        for grp, is_hole in zip(groups, is_hole_list):
            if not is_hole:
                continue

            r = grp[0]["cylinder"]["radius"]
            d = 2.0 * r
            axis = g.unit(grp[0]["cylinder"]["axis"])
            p0 = grp[0]["cylinder"]["origin"]
            total_area = sum(f["area"] for f in grp)

            # Look up associated feature id from F{id}:...
            feat_id = None
            for f in grp:
                parts = f["name"].split(":")
                if parts[0].startswith("F") and parts[0][1:].isdigit():
                    feat_id = int(parts[0][1:])
                    break
            feat_info = tl_map.get(feat_id, {})
            feat_name = feat_info.get("name") or (f"Feature{feat_id}" if feat_id else grp[0]["name"])

            # Check matching seam edge length for exact depth
            grp_face_names = {f["name"] for f in grp}
            seam_lens = []
            for e in edges:
                fnames = {fn.split("~")[0] for fn in e["name"].split("|")}
                if fnames and fnames <= grp_face_names:
                    d_end = g.norm(g.sub(e["end"], e["start"]))
                    if abs(e["length"] - d_end) < 1e-3:
                        seam_lens.append(e["length"])

            meas_len = total_area / (2.0 * math.pi * r) if len(grp) >= 2 else total_area / (math.pi * r)
            if seam_lens:
                depth = max(seam_lens)
            elif feat_info.get("definition", {}).get("depth"):
                d_val = _eval_length(doc.session, feat_info["definition"]["depth"], default=meas_len)
                depth = min(d_val, meas_len) if d_val else meas_len
            elif feat_info.get("definition", {}).get("height"):
                h_val = _eval_length(doc.session, feat_info["definition"]["height"], default=meas_len)
                depth = min(h_val, meas_len) if h_val else meas_len
            else:
                depth = meas_len

            # Center along axis
            weighted_t = sum(f["area"] * g.dot(g.sub(f["centroid"], p0), axis) for f in grp) / total_area
            center = g.add(p0, g.scale(axis, weighted_t))

            # Determine whether through hole or blind hole
            is_through = True
            if feat_info.get("type") == "HoleFeature":
                defn = feat_info.get("definition", {})
                if "depth" in defn and "to" not in defn:
                    end_caps = [f for f in faces if _is_end_cap(f, feat_id)] if feat_id is not None else []
                    if end_caps:
                        is_through = False
            elif feat_id is not None:
                end_caps = [f for f in faces if _is_end_cap(f, feat_id)]
                if end_caps:
                    is_through = False

            # Pick point: opening at the top / entry side along axis
            half_d = depth / 2.0
            end1 = g.add(center, g.scale(axis, half_d))
            end2 = g.add(center, g.scale(axis, -half_d))
            pick = end1 if end1[2] >= end2[2] else end2

            if want_diam and not _match_num(d, want_diam):
                continue

            if want_through is not None and bool(want_through) != is_through:
                continue

            if want_depth and not _match_num(depth, want_depth):
                continue

            if want_near and not (_match_near(pick, want_near, within) or _match_near(center, want_near, within)):
                continue

            if want_feature and not _match_feature(grp[0]["name"], want_feature, tl_map, tl_by_name) \
                    and not (feat_name and s_feat_match(feat_name, want_feature)):
                continue

            item = {
                "name": feat_name,
                "type": "hole",
                "diameter": round(d, 4),
                "radius": round(r, 4),
                "axis": [round(x, 4) for x in axis],
                "depth": round(depth, 4),
                "through": is_through,
                "is_through": is_through,
                "pick": [round(x, 4) for x in pick],
                "center": [round(x, 4) for x in center],
                "faces": [f["name"] for f in grp],
                "body": bt["base_name"],
            }
            if bt["occurrence"]:
                item["occurrence"] = bt["occurrence"]

            items.append(item)
            if len(items) >= limit:
                return items
    return items


def s_feat_match(name, query):
    return str(query).lower() in name.lower()


def find(document_or_doc, what: str, where: dict | None = None, limit: int = 50, ws=None):
    """Find faces, edges or holes in a part or assembly matching filters in `where`."""
    doc = getattr(document_or_doc, "session", None)
    if doc is not None:
        target_doc = document_or_doc
    elif ws is not None:
        target_doc = ws.get(document_or_doc)
    else:
        raise ValueError("provide a Document instance or Workspace")

    what = what.lower().strip()
    if what not in ("faces", "edges", "holes"):
        raise ValueError(f"unknown query type {what!r}, must be 'faces', 'edges', or 'holes'")

    where = where or {}
    targets = _collect_bodies(target_doc, where)
    tl, tl_map, tl_by_name = _get_timeline_info(target_doc.session)

    if what == "faces":
        res = _query_faces(target_doc, targets, where, limit, tl_map, tl_by_name)
    elif what == "edges":
        res = _query_edges(target_doc, targets, where, limit, tl_map, tl_by_name)
    elif target_doc.kind == "assembly":
        res = _assembly_holes(target_doc, targets, where, limit)
    else:
        res = _query_holes(target_doc, targets, where, limit, tl_map, tl_by_name)

    return QueryList(res, what)


class _PartView:
    """Minimal part document over a read-only session, for hole queries."""
    kind = "part"

    def __init__(self, session):
        self.session = session


def _assembly_holes(doc, targets, where, limit):
    """Holes of an assembly: queried in each linked part file, where the hole features live
    (the assembly timeline only knows the insert features), then moved into world coordinates."""
    part_where = {k: v for k, v in where.items() if k not in ("near", "within", "occurrence", "body")}
    links_by_comp = _links(doc.session)
    readers = {}
    items = []
    # Bodies without a direct link (parts inside subassemblies) keep the in-assembly query.
    unlinked = [bt for bt in targets if bt.get("component") not in links_by_comp]
    if unlinked:
        _, tl_map, tl_by_name = _get_timeline_info(doc.session)
        items.extend(_query_holes(doc, unlinked, where, limit, tl_map, tl_by_name))
    seen = set()
    try:
        for bt in targets:
            link = links_by_comp.get(bt.get("component"))
            if not link or bt["occurrence"] in seen:
                continue
            seen.add(bt["occurrence"])
            path = Path(link["file"])
            if path not in readers:
                r = Session(allow_paths=[path.parent])
                readers[path] = r
                r.tool("open", {"path": str(path)})
            view = _PartView(readers[path])
            # The assembly names linked bodies after the file, so take all bodies of the part.
            part_targets = _collect_bodies(view, {})
            _, tl_map, tl_by_name = _get_timeline_info(view.session)
            m = bt["transform"]
            for h in _query_holes(view, part_targets, part_where, 10_000, tl_map, tl_by_name):
                h = dict(h)
                h["pick"] = [round(x, 4) for x in g.apply_point(m, h["pick"])]
                h["center"] = [round(x, 4) for x in g.apply_point(m, h["center"])]
                h["axis"] = [round(x, 4) for x in g.unit(g.apply_dir(m, h["axis"]))]
                if h["body"] == bt["base_name"]:
                    h["body"] = bt["world_name"]
                h["occurrence"] = bt["occurrence"]
                near = where.get("near")
                within = where.get("within", 1.0)
                if near and not (_match_near(h["pick"], near, within) or _match_near(h["center"], near, within)):
                    continue
                items.append(h)
                if len(items) >= limit:
                    return items
    finally:
        for r in readers.values():
            r.close()
    return items
