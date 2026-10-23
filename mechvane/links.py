"""Joints and subassemblies across file boundaries.

SolidCraft keeps a linked part's bodies as STEP, so the part's history-based face names do not
reach the assembly, and Update Links can move a joint to another face without a word
(tangency-labs/solidcraft#3330). Until that is fixed upstream, Mechvane records which face of the
part design each joint side sits on, by the part's own stable face name, and checks the joints
against those names after every update.

Because SolidCraft's component.insert_design flattens an assembly file into one rigid multi-body
component and drops its links and joints, Mechvane expands a subassembly into a parent component
in the outer assembly, links each part file under it, recreates the subassembly's joints, and
tracks the subassembly file in the assembly's metadata so update_links can sync structural edits."""

import json
import os
from pathlib import Path
import re
import warnings
import zipfile

from . import METADATA_KEY, read_metadata
from . import geometry as g
from .solidcraft import SolidCraftError

TOL = 1e-4  # mm, and radians for directions


def _base(name):
    return re.sub(r"#\d+$", "", name or "")


def _occurrences(s):
    """{occurrence id: {id, name, component, parent, grounded, transform (world), local_transform}}"""
    comps = s.cmd("component.list")["components"]
    raw, first_of = {}, {}
    for c in comps:
        for o in c.get("occurrences", []):
            raw[o["id"]] = o
            first_of.setdefault(c["id"], o)

    def world_transform(o):
        m = o["transform"]
        cur = o
        while cur.get("parent", 0) != 0 and cur["parent"] in first_of:
            cur = first_of[cur["parent"]]
            m = g.mat_mul(cur["transform"], m)
        return m

    def full_path(o):
        parts = [o["name"]]
        cur = o
        while cur.get("parent", 0) != 0 and cur["parent"] in first_of:
            cur = first_of[cur["parent"]]
            parts.append(cur["name"])
        return "/".join(reversed(parts))

    return {oid: {"id": oid, "name": o["name"], "path": full_path(o), "component": o["component"], "parent": o.get("parent", 0),
                  "grounded": bool(o.get("grounded")), "transform": world_transform(o),
                  "local_transform": o["transform"]}
            for oid, o in raw.items()}


def _links(s):
    return {link["component"]: link for link in s.cmd("component.links").get("links", [])}


def _part_faces(reader):
    faces = []
    for body in reader.tool("inspect_design", {"measure": False, "sketches": False}).get("bodies", []):
        for f in reader.cmd("model.faces", {"body": body["name"]}).get("faces", []):
            faces.append(dict(f, body=body["name"]))
    return faces


def _on_cylinder(f, o, z):
    c = f.get("cylinder")
    return c and g.dist_to_line(o, c["origin"], c["axis"]) < TOL and g.parallel(z, c["axis"], TOL)


def _on_plane(f, o, z):
    n = f.get("plane_normal")
    return n and abs(g.dot(g.unit(n), g.sub(o, f["point"]))) < TOL and g.parallel(z, n, TOL)


def _match(faces, o, z, ref=None):
    """The part face a joint frame (part coordinates) sits on, as an anchor, or None."""
    cyl = [f for f in faces if _on_cylinder(f, o, z)]
    if cyl:
        if ref and ref.get("kind") == "cylinder":
            ref_radius = ref.get("radius")
            ref_axial = ref.get("axial")
            ref_face = ref.get("face")

            def cyl_key(f):
                c = f["cylinder"]
                r_diff = abs(c["radius"] - ref_radius) if ref_radius is not None else 0.0
                cur_axial = g.dot(g.sub(o, c["origin"]), g.unit(c["axis"]))
                ax_diff = abs(cur_axial - ref_axial) if ref_axial is not None else 0.0
                name_match = 0 if (f["name"] == ref_face or _base(f["name"]) == _base(ref_face)) else 1
                return (round(r_diff, 4), round(ax_diff, 4), name_match, f["name"])

            f = min(cyl, key=cyl_key)
        else:
            def cyl_key(f):
                c = f["cylinder"]
                ax_dist = abs(g.dot(g.sub(o, f["centroid"]), g.unit(c["axis"])))
                return (round(ax_dist, 4), f["name"])

            f = min(cyl, key=cyl_key)
        c = f["cylinder"]
        return {"kind": "cylinder", "face": f["name"], "body": f["body"],
                "axial": g.dot(g.sub(o, c["origin"]), g.unit(c["axis"])),
                "radius": round(c["radius"], 6)}
    planes = [f for f in faces if _on_plane(f, o, z)]
    if planes:
        if ref and ref.get("kind") == "plane":
            ref_face = ref.get("face")
            ref_offset = ref.get("offset")

            def plane_key(f):
                cur_offset = g.sub(o, f["centroid"])
                off_diff = g.norm(g.sub(cur_offset, ref_offset)) if ref_offset is not None else 0.0
                name_match = 0 if (f["name"] == ref_face or _base(f["name"]) == _base(ref_face)) else 1
                dist = g.norm(g.sub(o, f["centroid"]))
                return (name_match, round(off_diff, 4), round(dist, 4), f["name"])

            f = min(planes, key=plane_key)
        else:
            f = min(planes, key=lambda f: g.norm(g.sub(o, f["centroid"])))
        return {"kind": "plane", "face": f["name"], "body": f["body"],
                "offset": [round(x, 6) for x in g.sub(o, f["centroid"])]}
    return None


def _frames(s):
    """{joint name: {"a": (occurrence, origin, z), "b": ...}} in world coordinates."""
    out = {}
    for j in s.cmd("joint.list").get("joints", []):
        out[j["name"]] = {side: (j[side], j[f"frame_{side}"]["origin"], j[f"frame_{side}"]["z"])
                          if j.get(f"frame_{side}") else (j[side], None, None) for side in ("a", "b")}
    return out


def _to_part(occ, origin, z):
    inv = g.invert_rigid(occ["transform"])
    return g.apply_point(inv, origin), g.apply_dir(inv, z)


def record(ws, doc, joint, create_params=None):
    """Remember, for each side of `joint` on a linked part, the part face it sits on."""
    s = doc.session
    occs, links, frames = _occurrences(s), _links(s), _frames(s)
    if joint not in frames:
        raise KeyError(f"no joint {joint!r}")
    entry = {"sides": {}}
    if create_params is not None:
        entry["create"] = create_params
    for side, (occ_id, origin, z) in frames[joint].items():
        occ = occs.get(occ_id)
        link = links.get(occ["component"]) if occ else None
        if not link or origin is None:
            continue
        reader = ws.reader(link["file"])
        try:
            o, d = _to_part(occ, origin, z)
            anchor = _match(_part_faces(reader), o, d)
        finally:
            reader.close()
        entry["sides"][side] = dict(anchor or {"kind": "unknown"}, occurrence=occ["name"], file=link["file"])
    meta = doc.metadata()
    meta.setdefault("joints", {})
    old = meta["joints"].get(joint, {})
    if create_params is None and "create" in old:
        entry["create"] = old["create"]
    meta["joints"][joint] = entry
    doc.set_metadata(meta)
    return entry


def forget(doc, joint):
    """Drop what was recorded about `joint`."""
    meta = doc.metadata()
    if meta.get("joints", {}).pop(joint, None) is not None:
        doc.set_metadata(meta)


def check(ws, doc):
    """Compare every recorded joint side with its part face as the part design is now."""
    s = doc.session
    occs, frames = _occurrences(s), _frames(s)
    by_occ_name = {o["name"]: o for o in occs.values()}
    meta = doc.metadata()
    readers, faces = {}, {}
    report = []
    try:
        for joint, entry in meta.get("joints", {}).items():
            for side, anchor in entry.get("sides", {}).items():
                item = {"joint": joint, "side": side, "occurrence": anchor["occurrence"], "face": anchor.get("face")}
                if joint not in frames:
                    report.append(dict(item, status="joint_missing"))
                    continue
                if anchor["kind"] == "unknown":
                    report.append(dict(item, status="unverifiable"))
                    continue
                file = anchor["file"]
                if not Path(file).is_file():
                    report.append(dict(item, status="file_missing"))
                    continue
                if file not in faces:
                    try:
                        readers[file] = ws.reader(file)
                        faces[file] = _part_faces(readers[file])
                    except Exception:
                        faces[file] = None
                        report.append(dict(item, status="file_missing"))
                        continue
                if faces[file] is None:
                    report.append(dict(item, status="file_missing"))
                    continue
                named = [f for f in faces[file] if f["name"] == anchor["face"]] or \
                        [f for f in faces[file] if _base(f["name"]) == _base(anchor["face"])]
                if not named:
                    report.append(dict(item, status="face_missing"))
                    continue
                occ = by_occ_name.get(anchor["occurrence"])
                _, origin, z = frames[joint][side]
                if origin is None or occ is None:
                    report.append(dict(item, status="origin_lost"))
                    continue
                o, d = _to_part(occ, origin, z)
                test = _on_cylinder if anchor["kind"] == "cylinder" else _on_plane
                found = _match(faces[file], o, d, ref=anchor)
                if anchor["kind"] == "cylinder":
                    def _cyl_axial_ok(f):
                        if anchor.get("axial") is None:
                            return True
                        c = f["cylinder"]
                        cur_axial = g.dot(g.sub(o, c["origin"]), g.unit(c["axis"]))
                        return abs(cur_axial - anchor["axial"]) < TOL
                    ok = any(test(f, o, d) and _cyl_axial_ok(f) for f in named)
                else:
                    def _plane_offset_ok(f):
                        if anchor.get("offset") is None:
                            return True
                        cur_offset = g.sub(o, f["centroid"])
                        return g.norm(g.sub(cur_offset, anchor["offset"])) < TOL
                    face_matches = found is not None and (
                        found["face"] in {f["name"] for f in named} or _base(found["face"]) == _base(anchor["face"])
                    )
                    ok = any(test(f, o, d) and _plane_offset_ok(f) for f in named) and face_matches
                report.append(dict(item, status="ok" if ok else "moved",
                                   now_on=found["face"] if found else None))
    finally:
        for r in readers.values():
            r.close()
    return report


def resolve_occurrences(s, params):
    """Allow `"Sub:1/Plate:1"` occurrence references in joint params by resolving to the child occurrence name."""
    out = dict(params)
    comps = None
    for side in ("a", "b"):
        occ_ref = out.get(side, {}).get("occurrence") if isinstance(out.get(side), dict) else None
        if isinstance(occ_ref, str) and "/" in occ_ref:
            parts = [p.strip() for p in occ_ref.split("/") if p.strip()]
            parent_ref, leaf = parts[-2], parts[-1]
            if comps is None:
                comps = {c["id"]: c for c in s.cmd("component.list")["components"]}
            p_comp = next((c for c in comps.values()
                           if c["name"] == parent_ref or any(o["name"] == parent_ref for o in c.get("occurrences", []))), None)
            if not p_comp:
                raise ValueError(f"unknown subassembly {parent_ref!r} in occurrence path {occ_ref!r}")
            children = [o["name"] for o in p_comp.get("children", [])]
            p_name = p_comp["name"]
            prefixed = f"{p_name}_{leaf}"
            if leaf in children:
                resolved_leaf = leaf
            elif prefixed in children:
                resolved_leaf = prefixed
            else:
                candidates = [c for c in children if c in (leaf, prefixed) or
                              c.split(":")[0] in (leaf, prefixed)]
                if len(candidates) == 1:
                    resolved_leaf = candidates[0]
                elif len(candidates) > 1:
                    raise ValueError(f"ambiguous occurrence {leaf!r} in subassembly {parent_ref!r}: {candidates}")
                else:
                    raise ValueError(f"occurrence {leaf!r} not found in subassembly {parent_ref!r}")
            out[side] = dict(out[side], occurrence=resolved_leaf)
    return out


def _is_assembly(ws, p):
    try:
        with zipfile.ZipFile(p) as zf:
            d = json.loads(zf.read("document.json"))
        kind = read_metadata(d.get("metadata")).get("kind")
        return kind == "assembly" if kind else bool(d.get("links"))
    except Exception:  # noqa: BLE001
        r = ws.reader(p)
        try:
            kind = read_metadata(r.cmd("document.metadata").get("metadata")).get("kind")
            return kind == "assembly" if kind else bool(r.cmd("component.links").get("links"))
        finally:
            r.close()


def _unique_comp_name(s, want, prefix=None):
    used = {c["name"] for c in s.cmd("component.list")["components"]}
    if want not in used:
        return want
    if prefix and f"{prefix}_{want}" not in used:
        return f"{prefix}_{want}"
    k = 2
    while f"{want}_{k}" in used:
        k += 1
    return f"{want}_{k}"


def _joint_state(j, u_occs):
    return {
        "type": j["type"],
        "a": u_occs.get(j["a"], {}).get("name", j["a"]),
        "b": u_occs.get(j["b"], {}).get("name", j["b"]),
        "flip": bool(j.get("flip", False)),
        "offset": round(j.get("offset", 0.0), 6),
        "suppressed": bool(j.get("suppressed", False)),
        "values": [round(v["value"], 6) for v in j.get("values", [])],
    }


def _recreate_sub_joint(ws, doc, j, u_meta, occ_map, occs, t_sub, sub_name, preferred_name=None):
    s = doc.session
    top_a_id, top_b_id = occ_map.get(j["a"]), occ_map.get(j["b"])
    if top_a_id not in occs or top_b_id not in occs:
        return None, None
    top_a, top_b = occs[top_a_id]["name"], occs[top_b_id]["name"]
    existing = {x["name"] for x in s.cmd("joint.list").get("joints", [])}
    base = preferred_name or j["name"]
    jname = base if base not in existing else f"{sub_name}_{j['name']}"
    k = 2
    while jname in existing:
        jname = f"{sub_name}_{j['name']}_{k}"
        k += 1
    u_entry = (u_meta.get("joints") or {}).get(j["name"], {})
    u_create = u_entry.get("create") or {}
    params = {"type": j["type"], "name": jname, "flip": bool(j.get("flip", False)), "offset": j.get("offset", 0.0)}
    if "angle" in u_create:
        params["angle"] = u_create["angle"]
    if j.get("values"):
        params["values"] = [v["value"] for v in j["values"]]
    if any(v.get("limits") is not None for v in j.get("values", [])):
        params["limits"] = [v.get("limits") for v in j["values"]]
    links_map = _links(s)
    for side, occ_id, occ_name in (("a", top_a_id, top_a), ("b", top_b_id, top_b)):
        frame = j.get(f"frame_{side}")
        if not frame:
            return None, None
        world_origin = g.apply_point(t_sub, frame["origin"])
        world_z = g.apply_dir(t_sub, frame["z"])
        u_side_c = u_create.get(side) if isinstance(u_create.get(side), dict) else {}
        key = next((k for k in ("circle", "face", "edge", "point") if k in u_side_c), None)
        if key is None:
            kind = (u_entry.get("sides") or {}).get(side, {}).get("kind")
            key = {"cylinder": "circle", "plane": "face", "unknown": "point"}.get(kind)
        if key is None:
            link = links_map.get(occs[occ_id]["component"])
            if link:
                reader = ws.reader(link["file"])
                try:
                    o, d = _to_part(occs[occ_id], world_origin, world_z)
                    m = _match(_part_faces(reader), o, d)
                finally:
                    reader.close()
                key = "circle" if m and m["kind"] == "cylinder" else "face" if m and m["kind"] == "plane" else "point"
            else:
                key = "point"
        side_params = {"occurrence": occ_name, key: world_origin}
        if key == "point":
            side_params["z"] = world_z
        params[side] = side_params
    try:
        s.cmd("joint.create", params)
    except SolidCraftError:
        s.cmd("joint.as_built", {"type": j["type"], "name": jname, "a": top_a, "b": top_b})
    if j.get("suppressed"):
        s.cmd("joint.edit", {"joint": jname, "suppressed": True})
    entry = record(ws, doc, jname, params)
    if u_entry.get("sides"):
        meta = doc.metadata()
        for side, occ_name in (("a", top_a), ("b", top_b)):
            if side in u_entry["sides"] and u_entry["sides"][side].get("face"):
                entry["sides"][side] = dict(u_entry["sides"][side], occurrence=occ_name)
        meta["joints"][jname] = entry
        doc.set_metadata(meta)
    return jname, entry


def _move_params(occ, translate=None, rotate=None):
    """occurrence.move parameters for placing an occurrence with optional translation and rotation."""
    params = {"occurrence": occ, "space": "local"}
    if not rotate:
        if translate:
            params["translate"] = list(translate)
        return params

    if isinstance(rotate, (list, tuple)) and len(rotate) in (4, 16):
        if len(rotate) == 16:
            mat = [list(rotate[i * 4:(i + 1) * 4]) for i in range(4)]
        else:
            mat = [list(r) for r in rotate]
        if translate:
            mat[3][:3] = list(translate[:3])
        mp = g.move_params(mat)
        mp["occurrence"] = occ
        return mp

    if isinstance(rotate, dict):
        if "matrix" in rotate:
            m = rotate["matrix"]
            if len(m) == 16:
                mat = [list(m[i * 4:(i + 1) * 4]) for i in range(4)]
            else:
                mat = [list(r) for r in m]
            if translate:
                mat[3][:3] = list(translate[:3])
            mp = g.move_params(mat)
            mp["occurrence"] = occ
            return mp
        axis = rotate.get("axis", [0, 0, 1])
        angle = rotate.get("angle", 0)
        origin = rotate.get("origin")
    elif isinstance(rotate, (list, tuple)):
        axis = rotate[0]
        angle = rotate[1]
        origin = rotate[2] if len(rotate) > 2 else None
    else:
        raise ValueError(f"unsupported rotate specification: {rotate!r}")

    if translate:
        params["translate"] = list(translate)
    params["axis"] = list(axis)
    if isinstance(angle, (int, float)):
        params["angle"] = f"{angle} deg"
    else:
        params["angle"] = str(angle)
    if origin is not None:
        params["origin"] = list(origin)
    return params


def insert(ws, doc, part_path, name=None, translate=None, rotate=None, grounded=False, parent=None):
    """Place a part or subassembly file in an assembly. A subassembly becomes a parent component
    whose parts are linked underneath it and whose joints are recreated in the outer assembly."""
    s = doc.session
    p = ws._path(None, part_path)
    if not p.is_file():
        raise SolidCraftError(f"{p}: file not found")
    if p.resolve() == doc.path.resolve():
        raise SolidCraftError(f"{p}: a design can't be linked into itself")
    if not _is_assembly(ws, p):
        params = {"path": str(p)}
        if name:
            params["name"] = name
        if translate and not rotate:
            params["translate"] = translate
        if parent:
            params["parent"] = parent
        r = s.cmd("component.insert_design", params)
        occ = r.get("occurrence")
        if occ is not None and rotate:
            s.cmd("occurrence.move", _move_params(occ, translate=translate, rotate=rotate))
        if grounded and occ is not None:
            s.cmd("occurrence.ground", {"occurrence": occ, "grounded": True})
        return r
    return _insert_subassembly(ws, doc, p, name=name, translate=translate, rotate=rotate, grounded=grounded, parent=parent)


def _insert_subassembly(ws, doc, p, name=None, translate=None, rotate=None, grounded=False, parent=None):
    s = doc.session
    reader = ws.reader(p)
    try:
        u_comps = {c["id"]: c for c in reader.cmd("component.list")["components"]}
        u_root = next(c for c in u_comps.values() if c["parent"] is None)
        u_links = {l["component"]: l for l in reader.cmd("component.links").get("links", [])}
        u_joints = reader.cmd("joint.list").get("joints", [])
        u_meta = read_metadata(reader.cmd("document.metadata").get("metadata"))
        u_occs = _occurrences(reader)
    finally:
        reader.close()

    sub_name = _unique_comp_name(s, name or u_root["name"] or p.stem)
    made = s.cmd("component.create", {"name": sub_name, "parent": parent or "root", "activate": False})
    sub_comp, sub_occ_id = made["component"], made["occurrence"]
    if translate or rotate:
        s.cmd("occurrence.move", _move_params(sub_occ_id, translate=translate, rotate=rotate))
    if grounded:
        s.cmd("occurrence.ground", {"occurrence": sub_occ_id, "grounded": True})

    comp_map, occ_map = {}, {}

    def walk(u_parent, target_parent):
        for uo in u_parent.get("children", []):
            uc = u_comps[uo["component"]]
            if uo["component"] in u_links:
                link = u_links[uo["component"]]
                if uo["component"] in comp_map:
                    ins = s.cmd("occurrence.copy", {"component": comp_map[uo["component"]], "parent": target_parent})
                else:
                    cname = _unique_comp_name(s, uc["name"], prefix=sub_name)
                    ins = s.cmd("component.insert_design", {"path": link["file"], "name": cname, "parent": target_parent})
                    comp_map[uo["component"]] = ins["component"]
                child_occ = ins["occurrence"]
                if not g.same_mat(uo["transform"], g.IDENTITY):
                    s.cmd("occurrence.move", dict(g.move_params(uo["transform"]), occurrence=child_occ))
                occ_map[uo["id"]] = child_occ
            elif uc.get("children"):
                cname = _unique_comp_name(s, uc["name"], prefix=sub_name)
                nested = s.cmd("component.create", {"name": cname, "parent": target_parent, "activate": False})
                if not g.same_mat(uo["transform"], g.IDENTITY):
                    s.cmd("occurrence.move", dict(g.move_params(uo["transform"]), occurrence=nested["occurrence"]))
                occ_map[uo["id"]] = nested["occurrence"]
                walk(uc, nested["component"])

    walk(u_root, sub_comp)
    occs = _occurrences(s)
    t_sub = occs[sub_occ_id]["transform"]
    leaf_u_ids = [uid for uid, uo in u_occs.items() if uo["component"] in u_links and uid in occ_map]

    for uid in leaf_u_ids:
        s.cmd("occurrence.ground", {"occurrence": occ_map[uid], "grounded": True})

    joints_info = {}
    for j in u_joints:
        jname, _ = _recreate_sub_joint(ws, doc, j, u_meta, occ_map, occs, t_sub, sub_name)
        if jname:
            joints_info[j["name"]] = {"name": jname, "state": _joint_state(j, u_occs)}

    keep_grounded = set()
    if grounded and leaf_u_ids:
        keep_grounded = {uid for uid in leaf_u_ids if u_occs[uid]["grounded"]} or {leaf_u_ids[0]}
    for uid in leaf_u_ids:
        if uid not in keep_grounded:
            s.cmd("occurrence.ground", {"occurrence": occ_map[uid], "grounded": False})
    if joints_info:
        s.cmd("joint.solve")

    occs = _occurrences(s)
    parts_info = {}
    for uid in leaf_u_ids:
        uo = u_occs[uid]
        top_o = occs[occ_map[uid]]
        parts_info[uo["name"]] = {
            "occurrence": top_o["name"],
            "component": top_o["component"],
            "file": u_links[uo["component"]]["file"],
            "transform": uo["transform"],
        }

    rel_path = os.path.relpath(p, doc.path.parent).replace("\\", "/")
    meta = doc.metadata()
    meta.setdefault("subassemblies", {})[sub_name] = {
        "component": sub_comp,
        "occurrence": occs[sub_occ_id]["name"],
        "file": str(p),
        "path": rel_path,
        "parts": parts_info,
        "joints": joints_info,
    }
    doc.set_metadata(meta)
    return {
        "component": sub_comp,
        "occurrence": sub_occ_id,
        "occurrence_name": occs[sub_occ_id]["name"],
        "name": sub_name,
        "kind": "subassembly",
        "path": rel_path,
        "parts": [v["occurrence"] for v in parts_info.values()],
        "joints": [v["name"] for v in joints_info.values()],
    }


def _sync_subassemblies(ws, doc):
    meta = doc.metadata()
    subs = meta.get("subassemblies")
    if not subs:
        return []
    s = doc.session
    comps = {c["id"]: c for c in s.cmd("component.list")["components"]}
    comps_by_name = {c["name"]: c for c in comps.values()}
    occs = _occurrences(s)
    occs_by_name = {o["name"]: o for o in occs.values()}
    out = []
    meta_changed = False

    for sub_name, sub_info in list(subs.items()):
        comp = comps.get(sub_info.get("component")) or comps_by_name.get(sub_name)
        if comp is None:
            del subs[sub_name]
            meta_changed = True
            continue
        file = Path(sub_info["file"])
        if not file.is_file():
            out.append({"subassembly": sub_name, "occurrence": sub_info.get("occurrence"), "file": str(file),
                        "status": "file_missing", "added": [], "removed": [], "moved": []})
            continue
        reader = ws.reader(file)
        try:
            u_comps = {c["id"]: c for c in reader.cmd("component.list")["components"]}
            u_links = {l["component"]: l for l in reader.cmd("component.links").get("links", [])}
            u_joints = reader.cmd("joint.list").get("joints", [])
            u_meta = read_metadata(reader.cmd("document.metadata").get("metadata"))
            u_occs = _occurrences(reader)
        finally:
            reader.close()

        u_parts = {uo["name"]: uo for uo in u_occs.values() if uo["component"] in u_links}
        old_parts = sub_info.setdefault("parts", {})
        old_joints = sub_info.setdefault("joints", {})

        # Rigid frame of the subassembly's contents inside `comp` (in case outer joints moved it).
        t_frame = g.IDENTITY
        for u_oname, p_old in old_parts.items():
            if u_oname in u_parts and p_old["occurrence"] in occs_by_name and g.same_mat(u_parts[u_oname]["transform"], p_old["transform"]):
                t_frame = g.mat_mul(occs_by_name[p_old["occurrence"]]["local_transform"], g.invert_rigid(p_old["transform"]))
                break
        else:
            for p_old in old_parts.values():
                if p_old["occurrence"] in occs_by_name:
                    t_frame = g.mat_mul(occs_by_name[p_old["occurrence"]]["local_transform"], g.invert_rigid(p_old["transform"]))
                    break

        sub_occ = occs_by_name.get(sub_info.get("occurrence")) or next((o for o in occs.values() if o["component"] == comp["id"]), None)
        t_sub_world = g.mat_mul(sub_occ["transform"], t_frame) if sub_occ else t_frame

        added, removed, moved = [], [], []
        joints_changed = False

        # 1. Delete removed or modified subassembly joints first so old joints cannot pull moved
        # parts back during component.insert_design.
        u_joints_by_name = {j["name"]: j for j in u_joints}
        changed_joints = []
        for u_jname in list(old_joints):
            j_old = old_joints[u_jname]
            j_now = u_joints_by_name.get(u_jname)
            if j_now is None or j_old.get("state") != _joint_state(j_now, u_occs):
                try:
                    s.cmd("joint.delete", {"joint": j_old["name"]})
                except SolidCraftError:
                    pass
                forget(doc, j_old["name"])
                if j_now is None:
                    old_joints.pop(u_jname, None)
                joints_changed = True
                meta_changed = True
        for j in u_joints:
            j_old = old_joints.get(j["name"])
            if j_old is None or j_old.get("state") != _joint_state(j, u_occs):
                changed_joints.append((j, j_old["name"] if j_old else None))

        # 2. Removed parts in the subassembly file
        for u_oname in list(old_parts):
            if u_oname not in u_parts:
                p_old = old_parts.pop(u_oname)
                if not any(other["component"] == p_old["component"] for other in old_parts.values()):
                    try:
                        s.cmd("component.delete", {"component": p_old["component"]})
                    except SolidCraftError:
                        pass
                removed.append(p_old["occurrence"])
                meta_changed = True

        # 3. Added parts first (insert_design refreshes the session), then move added/moved parts
        to_move = []
        for u_oname, uo in u_parts.items():
            link = u_links[uo["component"]]
            if u_oname not in old_parts:
                cname = _unique_comp_name(s, u_comps[uo["component"]]["name"], prefix=sub_name)
                ins = s.cmd("component.insert_design", {"path": link["file"], "name": cname, "parent": comp["id"]})
                child_occ = ins["occurrence"]
                target_local = g.mat_mul(t_frame, uo["transform"])
                if not g.same_mat(target_local, g.IDENTITY):
                    to_move.append((child_occ, target_local))
                occs = _occurrences(s)
                top_o = occs[child_occ]
                old_parts[u_oname] = {
                    "occurrence": top_o["name"],
                    "component": top_o["component"],
                    "file": link["file"],
                    "transform": uo["transform"],
                }
                added.append(top_o["name"])
                meta_changed = True
            else:
                p_old = old_parts[u_oname]
                if not g.same_mat(uo["transform"], p_old["transform"]):
                    occs_by_name = {o["name"]: o for o in _occurrences(s).values()}
                    if p_old["occurrence"] in occs_by_name:
                        to_move.append((occs_by_name[p_old["occurrence"]]["id"], g.mat_mul(t_frame, uo["transform"])))
                    p_old["transform"] = uo["transform"]
                    moved.append(p_old["occurrence"])
                    meta_changed = True
        occs = _occurrences(s)
        for oid, target_local in to_move:
            was_gr = occs.get(oid, {}).get("grounded", False)
            if was_gr:
                s.cmd("occurrence.ground", {"occurrence": oid, "grounded": False})
            s.cmd("occurrence.move", dict(g.move_params(target_local), occurrence=oid))
            if was_gr:
                s.cmd("occurrence.ground", {"occurrence": oid, "grounded": True})

        # 4. Recreate added or modified joints in the subassembly file
        occs = _occurrences(s)
        occs_by_name = {o["name"]: o for o in occs.values()}
        occ_map = {uo["id"]: occs_by_name[old_parts[u_oname]["occurrence"]]["id"]
                   for u_oname, uo in u_parts.items() if u_oname in old_parts and old_parts[u_oname]["occurrence"] in occs_by_name}
        for j, pref in changed_joints:
            was_grounded = {oid: occs[oid]["grounded"] for oid in occ_map.values() if oid in occs}
            for oid, gr in was_grounded.items():
                if not gr:
                    s.cmd("occurrence.ground", {"occurrence": oid, "grounded": True})
            occs = _occurrences(s)
            jname, _ = _recreate_sub_joint(ws, doc, j, u_meta, occ_map, occs, t_sub_world, sub_name, preferred_name=pref)
            for oid, gr in was_grounded.items():
                if not gr:
                    s.cmd("occurrence.ground", {"occurrence": oid, "grounded": False})
            if jname:
                old_joints[j["name"]] = {"name": jname, "state": _joint_state(j, u_occs)}
                joints_changed = True
                meta_changed = True

        if added or removed or moved or joints_changed:
            if s.cmd("joint.list").get("joints"):
                s.cmd("joint.solve")
        out.append({
            "subassembly": sub_name,
            "occurrence": sub_info.get("occurrence"),
            "file": str(file),
            "status": "updated" if (added or removed or moved or joints_changed) else "unchanged",
            "added": added,
            "removed": removed,
            "moved": moved,
        })

    if meta_changed:
        fresh = doc.metadata()
        fresh["subassemblies"] = subs
        doc.set_metadata(fresh)
    return out


def _create_params(s, joint, entry):
    """joint.create parameters for an adopted joint, read back from the joint as it is: each side
    picked where its frame sits (round ends as a circle pick, plane anchors as a face pick or point)."""
    live = next(j for j in s.cmd("joint.list").get("joints", []) if j["name"] == joint)
    occs = _occurrences(s)
    params = {"type": live["type"], "name": joint}
    for side in ("a", "b"):
        s_anchor = entry["sides"].get(side, {})
        if s_anchor.get("kind") == "plane":
            off = s_anchor.get("offset")
            if off is not None and g.norm(off) > TOL:
                params[side] = {"occurrence": occs[live[side]]["name"], "point": live[f"frame_{side}"]["origin"],
                                "z": live[f"frame_{side}"]["z"]}
                continue
            key = "face"
        else:
            key = "circle"
        params[side] = {"occurrence": occs[live[side]]["name"], key: live[f"frame_{side}"]["origin"]}
    return params


def repair(ws, doc, joint):
    """Put a moved joint back on its recorded part face (cylinders and planes): recreate the joint
    with that side picked on the named face, then record and check it again."""
    s = doc.session
    meta = doc.metadata()
    entry = meta.get("joints", {}).get(joint)
    if not entry:
        raise ValueError(f"{joint!r} is not recorded (add_joint or adopt_joint it first)")
    params = dict(entry["create"]) if "create" in entry else _create_params(s, joint, entry)
    occs = {o["name"]: o for o in _occurrences(s).values()}
    frames = _frames(s)[joint]
    # Picks given in world coordinates went stale when the solver moved the parts: pick every
    # side again where its frame is now (for a round end that is its centre, which joint.create
    # takes as a circle pick).
    for side in ("a", "b"):
        if isinstance(params.get(side), dict):
            for key in ("face", "circle", "point"):
                if isinstance(params[side].get(key), list) and frames[side][1] is not None:
                    params[side] = dict(params[side], **{key: frames[side][1]})
    repair_warnings = []
    for side, anchor in entry["sides"].items():
        if anchor["kind"] not in ("cylinder", "plane"):
            continue
        if not Path(anchor["file"]).is_file():
            raise FileNotFoundError(f"{joint}: file {anchor['file']} not found")
        reader = ws.reader(anchor["file"])
        try:
            faces = _part_faces(reader)
        finally:
            reader.close()
        named = [f for f in faces if f["name"] == anchor["face"]] or \
                [f for f in faces if _base(f["name"]) == _base(anchor["face"])]
        if not named:
            raise ValueError(f"{joint}: face {anchor['face']} is gone from {anchor['file']}")
        if anchor["kind"] == "cylinder":
            c = named[0]["cylinder"]
            # The recorded end of the named round face: its centre on the axis.
            local = g.add(c["origin"], g.scale(g.unit(c["axis"]), anchor["axial"]))
            world = g.apply_point(occs[anchor["occurrence"]]["transform"], local)
            side_params = {k: v for k, v in params[side].items() if k not in ("face", "circle", "point")} \
                if isinstance(params[side], dict) else {}
            side_params.update({"occurrence": anchor["occurrence"], "circle": world})
            params[side] = side_params
        elif anchor["kind"] == "plane":
            f = named[0]
            n = g.unit(f["plane_normal"])
            c = f["centroid"]
            has_offset = anchor.get("offset") is not None
            if has_offset:
                off = anchor["offset"]
                off_proj = g.sub(off, g.scale(n, g.dot(off, n)))
                local = g.add(c, off_proj)
            else:
                local = c
                msg = f"{joint}: legacy plane anchor has no offset, repairing at centroid"
                repair_warnings.append({"joint": joint, "side": side, "warning": msg, "status": "repaired_at_centroid"})
                warnings.warn(msg, UserWarning, stacklevel=2)
            world = g.apply_point(occs[anchor["occurrence"]]["transform"], local)
            world_z = g.apply_dir(occs[anchor["occurrence"]]["transform"], n)
            side_params = {k: v for k, v in params[side].items() if k not in ("face", "circle", "point", "z")} \
                if isinstance(params[side], dict) else {}
            if has_offset and g.norm(anchor["offset"]) > TOL:
                side_params.update({"occurrence": anchor["occurrence"], "point": world, "z": world_z})
            elif isinstance(params.get(side), dict) and "point" in params[side]:
                side_params.update({"occurrence": anchor["occurrence"], "point": world, "z": world_z})
            else:
                side_params.update({"occurrence": anchor["occurrence"], "face": world})
            params[side] = side_params
    # Settings changed with joint.edit after add_joint live only in the joint: carry them over.
    live = next(j for j in s.cmd("joint.list").get("joints", []) if j["name"] == joint)
    params.update({k: live[k] for k in ("flip", "offset", "angle") if k in live})
    if any(v.get("limits") is not None for v in live.get("values", [])):
        params["limits"] = [v.get("limits") for v in live["values"]]
    if live.get("values"):
        params["values"] = [v["value"] for v in live["values"]]
    s.cmd("joint.delete", {"joint": joint})
    s.cmd("joint.create", params)
    if live.get("suppressed"):
        s.cmd("joint.edit", {"joint": joint, "suppressed": True})
    record(ws, doc, joint, params)
    res = [r for r in check(ws, doc) if r["joint"] == joint]
    if repair_warnings:
        for r in res:
            r["warnings"] = repair_warnings
    return res


def update_links(ws, doc, repair_moved=False):
    """Sync subassemblies and update linked parts, then check every recorded joint (and repair moved ones if asked).
    After joints, checks bolted connections against their anchors and repairs moved ones if asked."""
    subs = _sync_subassemblies(ws, doc)
    result = doc.session.cmd("component.update_links")
    report = check(ws, doc)
    repaired = []
    repair_warnings = []
    if repair_moved:
        for joint in sorted({r["joint"] for r in report if r["status"] in ("moved", "origin_lost")}):
            try:
                after = repair(ws, doc, joint)
                w = [item["warnings"] for item in after if "warnings" in item]
                flat_w = [x for sub in w for x in sub]
                st = after[0]["status"] if after else "ok"
                repaired_item = {"joint": joint, "status": st, "after": after}
                if flat_w:
                    repaired_item["warnings"] = flat_w
                    repair_warnings.extend(flat_w)
                repaired.append(repaired_item)
            except Exception as e:
                repaired.append({"joint": joint, "status": "failed", "error": str(e)})
        if repaired:
            report = check(ws, doc)

    # Bolted connections check (and repair if repair_moved)
    from . import bolted
    bolted_report = bolted.check_and_update_bolted_connections(ws, doc, repair=repair_moved)
    if any(b.get("status") == "moved_repaired" for b in bolted_report):
        report = check(ws, doc)

    bolted_warnings = [
        {"joint": None, "connection": b["id"], "status": b["status"], "shifted_by": b.get("shifted_by")}
        for b in bolted_report if b.get("status") not in ("ok", "moved_repaired")
    ]

    all_warnings = [r for r in report if r["status"] not in ("ok", "unverifiable")] + repair_warnings + bolted_warnings
    return {"update": result, "subassemblies": subs, "joints": report, "repaired": repaired,
            "bolted_connections": bolted_report, "warnings": all_warnings}


__all__ = ["insert", "record", "forget", "check", "repair", "update_links", "resolve_occurrences", "METADATA_KEY"]
