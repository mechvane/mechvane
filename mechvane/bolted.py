"""Bolted connection generator for Mechvane (through-hole bolted connections across files).

Automates multi-part hole drilling, standard part generation (ISO 4762 screw, ISO 7089 washers,
ISO 4032 nut), assembly insertion and joint creation with CAD constraints.
"""

import math
from pathlib import Path
import shutil
import tempfile

from . import geometry as g
from . import hole_tables
from . import links
from . import sketch_rule
from . import standard_parts
from .documents import ASSEMBLY, PART
from .solidcraft import SolidCraftError


def _ensure_standard_part(ws, norm: str, size: str, length: float | None = None) -> Path:
    """Ensure a standard part exists in `ws`, creating it via standard_parts if needed."""
    sp = standard_parts.spec(norm, size, length)
    desig = sp["standard"]["designation"].replace(" ", "_")
    expected_std = sp["standard"]

    p = ws._path(desig, None)
    if desig in ws.docs or p.is_file():
        doc = ws.docs.get(desig) or ws.open(p)
        meta = doc.metadata().get("standard")
        if (meta and meta.get("norm") == expected_std["norm"]
                and meta.get("size") == expected_std["size"]
                and meta.get("dimensions") == expected_std.get("dimensions")):
            return doc.path
        if desig in ws.docs:
            ws.close(desig)
        # The file on disk no longer matches the standard: rebuild it in place.
        res = standard_parts.create(ws, norm, size, length=length, overwrite=True)
        return Path(res["path"])

    res = standard_parts.create(ws, norm, size, length=length)
    return Path(res["path"])


def _find_live_doc(ws, doc, fpath: Path):
    """Find the live Document instance corresponding to `fpath`."""
    target = fpath.resolve()
    if target == doc.path.resolve():
        return doc
    for d in ws.docs.values():
        if d.path.resolve() == target:
            return d
    return None


def _backup_files(paths) -> tuple[Path, dict]:
    """Copy existing files into a fresh temp dir; return (dir, {original: copy})."""
    backup_dir = Path(tempfile.mkdtemp(prefix="anker-bolted-"))
    copies = {}
    for i, fpath in enumerate(dict.fromkeys(Path(x).resolve() for x in paths)):
        if fpath.exists():
            dst = backup_dir / f"{i}_{fpath.name}"
            shutil.copy2(fpath, dst)
            copies[fpath] = dst
    return backup_dir, copies


def _restore_backup(ws, doc, copies: dict) -> None:
    """Restore backed-up files and reopen them in their live sessions."""
    # 1. Restore all files on disk first so sessions reload restored contents
    for fpath, src in copies.items():
        shutil.copy2(src, fpath)
    # 2. Reopen live sessions (parts first, assembly last)
    doc_resolved = doc.path.resolve()
    part_paths = [p for p in copies if p.resolve() != doc_resolved]
    reopen_order = part_paths + ([p for p in copies if p.resolve() == doc_resolved])
    for fpath in reopen_order:
        live = _find_live_doc(ws, doc, fpath)
        if live is not None:
            try:
                live.session.tool("open", {"path": str(fpath)})
            except Exception:
                pass
    # 3. Synchronize link geometry in the assembly session
    try:
        doc.session.cmd("component.update_links")
    except Exception:
        pass


def _unique_feature_name(s, base: str, extra_used: set | None = None) -> str:
    """Return a unique feature name in a part session's timeline."""
    tl = sketch_rule.timeline(s).get("timeline", [])
    used = {f.get("name") for f in tl if isinstance(f, dict)}
    if extra_used:
        used |= set(extra_used)
    if base not in used:
        return base
    k = 2
    while f"{base}_{k}" in used:
        k += 1
    return f"{base}_{k}"


def _rotate_vector_around_axis(v: list[float], u: list[float], ang: float) -> list[float]:
    """Rotate 3D vector v around unit axis vector u by angle ang (radians) via Rodrigues formula."""
    c = math.cos(ang)
    s = math.sin(ang)
    u_dot_v = g.dot(u, v)
    u_cross_v = g.cross(u, v)
    return [
        v[i] * c + u_cross_v[i] * s + u[i] * u_dot_v * (1.0 - c)
        for i in range(3)
    ]


def _generate_pattern_rays(p0: list[float], dir_w: list[float], pattern: dict | None) -> list[tuple[list[float], list[float]]]:
    """Generate (position, direction) rays for each instance in a pattern starting from (p0, dir_w)."""
    if not pattern:
        return [(list(p0), list(dir_w))]

    p_type = (pattern.get("type") or "").strip().lower()
    if p_type in ("circular", "circle"):
        count = int(pattern.get("count", 1))
        if count < 1:
            raise ValueError(f"pattern count must be >= 1, got {count}")
        axis_pt = [float(x) for x in pattern.get("axis_point", [0.0, 0.0, 0.0])]
        axis = [float(x) for x in pattern.get("axis", [0.0, 0.0, 1.0])]
        if g.norm(axis) < 1e-6:
            raise ValueError("pattern axis cannot be zero vector")
        u = g.unit(axis)
        total_angle_deg = float(pattern.get("angle", 360.0))

        rays = []
        for k in range(count):
            if count == 1:
                ang = 0.0
            elif abs(total_angle_deg - 360.0) < 1e-4:
                ang = k * (2.0 * math.pi / count)
            else:
                ang = math.radians(k * (total_angle_deg / (count - 1)))
            v = [p0[i] - axis_pt[i] for i in range(3)]
            v_rot = _rotate_vector_around_axis(v, u, ang)
            pk = [axis_pt[i] + v_rot[i] for i in range(3)]
            dk = g.unit(_rotate_vector_around_axis(dir_w, u, ang))
            rays.append((pk, dk))
        return rays

    if p_type in ("rectangular", "grid"):
        count = pattern.get("count", [1, 1])
        if isinstance(count, int):
            count = [count, 1]
        nx, ny = int(count[0]), int(count[1])
        if nx < 1 or ny < 1:
            raise ValueError(f"rectangular pattern count must be >= 1 in both directions, got {count}")
        spacing = pattern.get("spacing", [0.0, 0.0])
        if isinstance(spacing, (int, float)):
            spacing = [float(spacing), float(spacing)]
        dx, dy = float(spacing[0]), float(spacing[1])
        dirs = pattern.get("directions", [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        dir1, dir2 = dirs[0], dirs[1]
        if g.norm(dir1) < 1e-6 or g.norm(dir2) < 1e-6:
            raise ValueError("rectangular pattern directions cannot be zero vector")
        u1, u2 = g.unit(dir1), g.unit(dir2)

        rays = []
        for ix in range(nx):
            for iy in range(ny):
                offset = g.add(g.scale(u1, ix * dx), g.scale(u2, iy * dy))
                pk = g.add(p0, offset)
                rays.append((pk, list(dir_w)))
        return rays

    raise ValueError(f"unsupported pattern type: {pattern.get('type')!r} (must be 'circular' or 'rectangular')")


def _rotation_to_dir(target_dir: list[float]) -> dict | None:
    """Compute rotation dict for links.insert to align default axis [0, 0, -1] with target_dir."""
    u = [0.0, 0.0, -1.0]
    v = g.unit(target_dir)
    dot = g.dot(u, v)
    if dot > 0.999999:
        return None
    if dot < -0.999999:
        return {"axis": [1.0, 0.0, 0.0], "angle": 180.0}
    axis = g.unit(g.cross(u, v))
    angle = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
    return {"axis": axis, "angle": angle}


def _parse_placement(ws_or_doc, doc_or_placement, placement: dict | None = None) -> tuple[list[float], list[float]]:
    """Extract world ray origin (position) and unit direction from `placement`."""
    if placement is None:
        doc = ws_or_doc
        placement = doc_or_placement
        from .documents import Workspace
        ws = Workspace(doc.path.parent)
    else:
        ws = ws_or_doc
        doc = doc_or_placement

    p_type = placement.get("type")
    if p_type is None:
        p_type = "point" if "position" in placement else "concentric"

    if p_type in ("point", "linear"):
        pos = placement.get("position")
        if not pos or len(pos) != 3:
            raise ValueError("placement 'position' must be a 3D coordinate [x, y, z]")
        pos = [float(x) for x in pos]
        d = placement.get("direction")
        if d:
            if len(d) != 3 or g.norm(d) < 1e-6:
                raise ValueError("placement 'direction' must be a non-zero 3D vector")
            dir_w = g.unit([float(x) for x in d])
        else:
            dir_w = [0.0, 0.0, -1.0]
        return pos, dir_w

    if p_type in ("concentric", "hole"):
        occ_name = placement.get("occurrence")
        if not occ_name:
            raise ValueError("concentric/hole placement requires 'occurrence'")
        s = doc.session
        occs = {o["name"]: o for o in links._occurrences(s).values()}
        if occ_name not in occs:
            raise ValueError(f"occurrence {occ_name!r} not found in assembly")
        occ = occs[occ_name]
        lmap = links._links(s)
        link = lmap.get(occ["component"])
        if not link:
            raise ValueError(f"occurrence {occ_name!r} has no linked part file")
        reader = ws.reader(link["file"])
        try:
            faces = links._part_faces(reader)
            binfo = reader.cmd("document.inspect", {"measure": True}).get("bodies", [])
            edges_by_body = {}
            for b in binfo:
                edges_by_body[b["name"]] = reader.cmd("model.edges", {"body": b["name"]}).get("edges", [])
        finally:
            reader.close()

        cyls = [f for f in faces if f.get("cylinder")]
        if not cyls:
            raise ValueError(f"no cylindrical hole found in {occ_name!r}")

        want_face = placement.get("face")
        selected_cyl = None
        if want_face:
            for f in cyls:
                if f["name"] == want_face:
                    selected_cyl = f
                    break
            if not selected_cyl:
                raise ValueError(f"cylindrical face {want_face!r} not found in {occ_name!r}")
        else:
            # Filter internal hole cylinders
            hole_cyls = [
                f for f in cyls
                if any(k in f.get("name", "").lower() for k in (":bore:", ":cut:", "hole"))
            ]
            if hole_cyls:
                selected_cyl = hole_cyls[0]
            elif len(cyls) > 1:
                # If multiple cylinders and no name tag, pick the one with smaller radius (inner hole vs outer pin/boss)
                selected_cyl = min(cyls, key=lambda f: f["cylinder"]["radius"])
            else:
                selected_cyl = cyls[0]

        c = selected_cyl["cylinder"]
        axis_w = g.unit(g.apply_dir(occ["transform"], c["axis"]))
        orig_w = g.apply_point(occ["transform"], c["origin"])

        req_d = placement.get("direction")
        if req_d:
            if len(req_d) != 3 or g.norm(req_d) < 1e-6:
                raise ValueError("placement 'direction' must be a non-zero 3D vector")
            dir_req = g.unit([float(x) for x in req_d])
            if g.dot(axis_w, dir_req) < 0:
                axis_w = g.scale(axis_w, -1.0)
        else:
            if axis_w[2] > 1e-4:
                axis_w = g.scale(axis_w, -1.0)

        # Ensure orig_w is at the entrance of selected_cyl along axis_w
        b_name = selected_cyl.get("body")
        cyl_edges = [e for e in edges_by_body.get(b_name, []) if selected_cyl["name"] in e["name"].split("|")]
        if cyl_edges:
            cyl_pts = [e["start"] for e in cyl_edges] + [e["end"] for e in cyl_edges]
            cyl_pts_w = [g.apply_point(occ["transform"], pt) for pt in cyl_pts]
            projs = [g.dot(g.sub(pw, orig_w), axis_w) for pw in cyl_pts_w]
            orig_w = g.add(orig_w, g.scale(axis_w, min(projs)))

        return orig_w, axis_w

    raise ValueError(f"unsupported placement type: {p_type!r}")


def _edge_polyline(e: dict, normal: list[float], segments: int = 16) -> list[list[float]]:
    """Points along an edge: [start, end] for a line, sampled points for an arc or full circle."""
    a, m, b = e["start"], e.get("mid"), e["end"]
    if m is None:
        return [a, b]
    if g.norm(g.sub(a, b)) < 1e-9:
        # Full circle: start == end, mid is the opposite point
        center = g.scale(g.add(a, m), 0.5)
        sweep = 2 * math.pi
        w = g.unit(normal)
    else:
        ab, am = g.sub(b, a), g.sub(m, a)
        n = g.cross(ab, am)
        nn = g.dot(n, n)
        if nn < 1e-12 * max(g.dot(ab, ab), 1e-12) ** 2:
            return [a, b]  # straight
        center = g.add(a, g.scale(g.add(g.scale(g.cross(n, ab), g.dot(am, am)),
                                        g.scale(g.cross(am, n), g.dot(ab, ab))), 1 / (2 * nn)))
        w = g.unit(n)
        sweep = None
    u = g.unit(g.sub(a, center))
    v = g.cross(w, u)
    r = g.norm(g.sub(a, center))
    if sweep is None:
        def ang(p):
            d = g.sub(p, center)
            t = math.atan2(g.dot(d, v), g.dot(d, u))
            return t if t > 1e-12 else t + 2 * math.pi
        # Sweep from start to end the way round that passes mid
        sweep = ang(b)
        if ang(m) > sweep:
            sweep -= 2 * math.pi
    pts = []
    for i in range(segments + 1):
        t = sweep * i / segments
        pts.append(g.add(center, g.add(g.scale(u, r * math.cos(t)), g.scale(v, r * math.sin(t)))))
    return pts


def _edge_loops(f_edges: list[dict], tol: float = 1e-4) -> list[list[dict]]:
    """Group a face's edges into closed loops by chaining shared end points."""
    left = list(f_edges)
    loops = []
    while left:
        loop = [left.pop(0)]
        start, cur = loop[0]["start"], loop[0]["end"]
        while g.norm(g.sub(cur, start)) > tol:
            nxt = next((e for e in left if g.norm(g.sub(e["start"], cur)) <= tol
                        or g.norm(g.sub(e["end"], cur)) <= tol), None)
            if nxt is None:
                break
            left.remove(nxt)
            loop.append(nxt)
            cur = nxt["end"] if g.norm(g.sub(nxt["start"], cur)) <= tol else nxt["start"]
        loops.append(loop)
    return loops


def _point_in_face(x_loc: list[float], f: dict, f_edges: list[dict], cyl_faces: dict | None = None) -> bool:
    """Check if point x_loc lies within the outer boundary of planar face f (arcs as polylines).
    Inner loops are ignored on purpose: a bolt through an existing hole still penetrates the part."""
    if not f_edges:
        return True
    n = f.get("plane_normal")
    if not n:
        return True
    abs_n = [abs(x) for x in n]
    drop = abs_n.index(max(abs_n))
    i1, i2 = [i for i in (0, 1, 2) if i != drop]

    def area(polylines):
        pts = [p for pl in polylines for p in pl]
        return ((max(p[i1] for p in pts) - min(p[i1] for p in pts))
                * (max(p[i2] for p in pts) - min(p[i2] for p in pts)))

    loops = [[_edge_polyline(e, n) for e in loop] for loop in _edge_loops(f_edges)]
    outer = max(loops, key=area)
    pts = [p for pl in outer for p in pl]
    margin = 1e-3
    for i in range(3):
        if not (min(p[i] for p in pts) - margin <= x_loc[i] <= max(p[i] for p in pts) + margin):
            return False

    # Even-odd ray crossing over the outer loop
    px, py = x_loc[i1], x_loc[i2]
    crossings = 0
    for pl in outer:
        for p, q in zip(pl, pl[1:]):
            x1, y1 = p[i1], p[i2]
            x2, y2 = q[i1], q[i2]
            if (y1 <= py < y2) or (y2 <= py < y1):
                x_int = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
                if x_int >= px - 1e-6:
                    crossings += 1
    return (crossings % 2) == 1


def _find_penetrations(ws, doc, p0: list[float], dir_w: list[float]) -> list[dict]:
    """Find all linked part occurrences penetrated by ray p0 + s * dir_w, sorted along the ray."""
    s = doc.session
    occs = links._occurrences(s)
    lmap = links._links(s)

    penetrated = []
    for oid, occ in occs.items():
        if occ["component"] not in lmap:
            continue
        link = lmap[occ["component"]]
        reader = ws.reader(link["file"])
        try:
            faces = links._part_faces(reader)
            cyl_faces = {f["name"]: f for f in faces if f.get("cylinder")}
            binfo = reader.cmd("document.inspect", {"measure": True}).get("bodies", [])
            edges_by_body = {}
            for b in binfo:
                edges_by_body[b["name"]] = reader.cmd("model.edges", {"body": b["name"]}).get("edges", [])
        finally:
            reader.close()

        t_occ = occ["transform"]
        t_inv = g.invert_rigid(t_occ)

        hits = []
        for f in faces:
            norm_loc = f.get("plane_normal")
            pt_loc = f.get("point")
            if not norm_loc or not pt_loc:
                continue
            norm_w = g.unit(g.apply_dir(t_occ, norm_loc))
            pt_w = g.apply_point(t_occ, pt_loc)
            denom = g.dot(dir_w, norm_w)
            if abs(denom) < 1e-6:
                continue
            s_val = g.dot(g.sub(pt_w, p0), norm_w) / denom
            if s_val < -1e-4:
                continue
            x_w = g.add(p0, g.scale(dir_w, s_val))
            x_loc = g.apply_point(t_inv, x_w)

            b_name = f.get("body")
            body_edges = edges_by_body.get(b_name, [])
            f_edges = [e for e in body_edges if f["name"] in e["name"].split("|")]
            if not _point_in_face(x_loc, f, f_edges, cyl_faces):
                continue
            hits.append((s_val, denom, f["name"], x_w, x_loc))

        hits.sort(key=lambda h: h[0])
        if len(hits) >= 2:
            entry = hits[0]
            exit_pt = hits[-1]
            thickness = exit_pt[0] - entry[0]
            if thickness > 1e-3:
                penetrated.append({
                    "occurrence": occ,
                    "file": link["file"],
                    "s_entry": entry[0],
                    "s_exit": exit_pt[0],
                    "thickness": thickness,
                    "entry_world": entry[3],
                    "exit_world": exit_pt[3],
                    "entry_loc": entry[4],
                    "exit_loc": exit_pt[4],
                    "entry_face": entry[2],
                    "exit_face": exit_pt[2],
                })

    penetrated.sort(key=lambda p: p["s_entry"])
    return penetrated


def _matches_part_name(occ_name: str, part_query: str) -> bool:
    """Check if occurrence name matches part_query (allowing with or without instance suffix ':n')."""
    if occ_name == part_query:
        return True
    c_base, _, c_idx = occ_name.partition(":")
    q_base, _, q_idx = part_query.partition(":")
    if q_idx:
        return (c_base == q_base and c_idx == q_idx) or (c_base == part_query or occ_name == part_query)
    return c_base == q_base


def _filter_penetrations_by_parts(penetrations: list[dict], parts: list[str]) -> list[dict]:
    """Filter penetrations to only the specified occurrence names in ray order, ending after the last named part."""
    if not parts:
        return penetrations
    filtered = []
    pen_idx = 0
    for part_name in parts:
        matched = None
        while pen_idx < len(penetrations):
            cand = penetrations[pen_idx]
            pen_idx += 1
            if _matches_part_name(cand["occurrence"]["name"], part_name):
                matched = cand
                break
        if matched is None:
            all_names = [p["occurrence"]["name"] for p in penetrations]
            raise ValueError(
                f"specified part {part_name!r} not penetrated by placement ray in expected order (penetrated: {all_names})"
            )
        filtered.append(matched)
    return filtered


def _determine_anchor(ws, doc, ray_pos: list[float], ray_dir: list[float], penetrations: list[dict]) -> dict:
    """Determine geometric anchor for a bolted connection instance.
    Priority 1: Coaxial cylindrical face (boss/dome or pre-existing hole) in carrier/penetrated part.
    Priority 2: Entry face of topmost part with edge distances / local offset in part coordinates."""
    # Priority 1: Check penetrated parts for a coaxial cylinder (carrier part penetrations[-1] first)
    check_order = [penetrations[-1]] + penetrations[:-1] if penetrations else []
    for pen in check_order:
        occ = pen["occurrence"]
        t_occ = occ["transform"]
        t_inv = g.invert_rigid(t_occ)
        p_loc = g.apply_point(t_inv, ray_pos)
        d_loc = g.unit(g.apply_dir(t_inv, ray_dir))

        reader = ws.reader(pen["file"])
        try:
            faces = links._part_faces(reader)
        finally:
            reader.close()

        cyl_matches = []
        for f in faces:
            c = f.get("cylinder")
            if not c:
                continue
            c_axis = g.unit(c["axis"])
            if not g.parallel(d_loc, c_axis, 1e-4):
                continue
            dist = g.dist_to_line(p_loc, c["origin"], c_axis)
            if dist < 1e-3:
                cyl_matches.append(f)

        if cyl_matches:
            hole_cyls = [
                f for f in cyl_matches
                if any(k in f.get("name", "").lower() for k in (":bore:", ":cut:", "hole"))
            ]
            if hole_cyls:
                selected_cyl = hole_cyls[0]
            elif len(cyl_matches) > 1:
                selected_cyl = min(cyl_matches, key=lambda f: f["cylinder"]["radius"])
            else:
                selected_cyl = cyl_matches[0]

            c = selected_cyl["cylinder"]
            c_axis = g.unit(c["axis"])
            axial = g.dot(g.sub(p_loc, c["origin"]), c_axis)
            dir_sign = 1 if g.dot(d_loc, c_axis) > 0 else -1

            return {
                "type": "concentric",
                "kind": "cylinder",
                "occurrence": occ["name"],
                "file": str(pen["file"]),
                "face": selected_cyl["name"],
                "body": selected_cyl.get("body"),
                "axial": round(axial, 6),
                "radius": round(c["radius"], 6),
                "dir_sign": dir_sign,
                "recorded_pos": [round(x, 6) for x in ray_pos],
                "recorded_dir": [round(x, 6) for x in ray_dir],
                "recorded_pos_local": [round(x, 6) for x in p_loc],
                "recorded_dir_local": [round(x, 6) for x in d_loc],
            }

    # Priority 2: Entry face of topmost part + distance to two edges / local offset
    top_pen = penetrations[0]
    occ = top_pen["occurrence"]
    t_occ = occ["transform"]
    t_inv = g.invert_rigid(t_occ)
    p_loc = top_pen.get("entry_loc") or g.apply_point(t_inv, ray_pos)
    d_loc = g.unit(g.apply_dir(t_inv, ray_dir))

    reader = ws.reader(top_pen["file"])
    try:
        faces = links._part_faces(reader)
        binfo = reader.cmd("document.inspect", {"measure": True}).get("bodies", [])
        edges_by_body = {}
        for b in binfo:
            edges_by_body[b["name"]] = reader.cmd("model.edges", {"body": b["name"]}).get("edges", [])
    finally:
        reader.close()

    entry_face_name = top_pen.get("entry_face")
    named = [fc for fc in faces if fc["name"] == entry_face_name] or \
            [fc for fc in faces if links._base(fc["name"]) == links._base(entry_face_name)]
    f = named[0] if named else None
    if not f and faces:
        for fc in faces:
            n = fc.get("plane_normal")
            if n and abs(g.dot(g.unit(n), g.sub(p_loc, fc["point"]))) < 1e-3 and g.parallel(d_loc, n, 1e-4):
                f = fc
                entry_face_name = fc["name"]
                break

    b_name = f.get("body") if f else None
    body_edges = edges_by_body.get(b_name, [])
    f_edges = [e for e in body_edges if entry_face_name and (entry_face_name in e["name"].split("|") or links._base(entry_face_name) in [links._base(x) for x in e["name"].split("|")])]
    n = g.unit(f.get("plane_normal", [0, 0, 1])) if f else [0, 0, 1]
    abs_n = [abs(x) for x in n]
    w_axis = abs_n.index(max(abs_n))
    u_axis, v_axis = [i for i in (0, 1, 2) if i != w_axis]

    anchor_data = {
        "type": "offset",
        "kind": "plane",
        "occurrence": occ["name"],
        "file": str(top_pen["file"]),
        "face": entry_face_name or (f["name"] if f else None),
        "body": b_name,
        "plane_normal": [round(x, 6) for x in n],
        "local_pos": [round(x, 6) for x in p_loc],
        "local_dir": [round(x, 6) for x in d_loc],
        "offset": [round(x, 6) for x in g.sub(p_loc, f.get("centroid", p_loc))] if f else [0, 0, 0],
        "recorded_pos": [round(x, 6) for x in ray_pos],
        "recorded_dir": [round(x, 6) for x in ray_dir],
    }

    if f_edges:
        pts = [e["start"] for e in f_edges] + [e["end"] for e in f_edges]
        u_min = min(pt[u_axis] for pt in pts)
        u_max = max(pt[u_axis] for pt in pts)
        v_min = min(pt[v_axis] for pt in pts)
        v_max = max(pt[v_axis] for pt in pts)

        if abs(p_loc[u_axis] - u_min) <= abs(p_loc[u_axis] - u_max):
            ref_u = "min"
            offset_u = p_loc[u_axis] - u_min
        else:
            ref_u = "max"
            offset_u = p_loc[u_axis] - u_max

        if abs(p_loc[v_axis] - v_min) <= abs(p_loc[v_axis] - v_max):
            ref_v = "min"
            offset_v = p_loc[v_axis] - v_min
        else:
            ref_v = "max"
            offset_v = p_loc[v_axis] - v_max

        anchor_data.update({
            "axes": [u_axis, v_axis, w_axis],
            "ref_u": ref_u,
            "offset_u": round(offset_u, 6),
            "ref_v": ref_v,
            "offset_v": round(offset_v, 6),
        })

    return anchor_data


def _resolve_anchor(ws, doc, anchor: dict) -> tuple[str, list[float] | None, list[float] | None]:
    """Resolve an anchor's current world position and direction in `doc`.
    Returns (status, world_pos, world_dir) where status is 'ok' or 'anchor_lost'."""
    occs = {o["name"]: o for o in links._occurrences(doc.session).values()}
    occ_name = anchor.get("occurrence")
    if not occ_name or occ_name not in occs:
        return "anchor_lost", None, None
    occ = occs[occ_name]

    fpath = Path(anchor.get("file", ""))
    if not fpath.is_file():
        return "anchor_lost", None, None

    try:
        reader = ws.reader(str(fpath))
        try:
            faces = links._part_faces(reader)
            binfo = reader.cmd("document.inspect", {"measure": True}).get("bodies", [])
            edges_by_body = {b["name"]: reader.cmd("model.edges", {"body": b["name"]}).get("edges", []) for b in binfo}
        finally:
            reader.close()
    except Exception:
        return "anchor_lost", None, None

    face_name = anchor.get("face")
    named = [fc for fc in faces if fc["name"] == face_name] or \
            [fc for fc in faces if links._base(fc["name"]) == links._base(face_name)]
    if not named:
        return "anchor_lost", None, None
    f = named[0]

    kind = anchor.get("kind")
    if kind == "cylinder":
        c = f.get("cylinder")
        if not c:
            return "anchor_lost", None, None
        t_occ = occ["transform"]
        c_axis = g.unit(c["axis"])
        # Work in part coordinates so the anchor follows its occurrence when that moves or turns.
        # Anchors recorded before 2026-10-27 only have world values; read them in the current frame.
        t_inv = g.invert_rigid(t_occ)
        rec_pos = anchor.get("recorded_pos_local") or g.apply_point(t_inv, anchor.get("recorded_pos"))
        rec_dir = anchor.get("recorded_dir_local") or g.apply_dir(t_inv, anchor.get("recorded_dir", [0, 0, -1]))

        # Project the recorded point onto the (possibly moved) cylinder axis, keeping its height
        proj_dist = g.dot(g.sub(rec_pos, c["origin"]), c_axis)
        new_p_world = g.apply_point(t_occ, g.add(c["origin"], g.scale(c_axis, proj_dist)))
        new_d_loc = c_axis if g.dot(c_axis, rec_dir) >= 0 else g.scale(c_axis, -1.0)
        new_d_world = g.unit(g.apply_dir(t_occ, new_d_loc))

        return "ok", new_p_world, new_d_world

    if kind == "plane":
        if "axes" in anchor and "ref_u" in anchor and "ref_v" in anchor:
            u_axis, v_axis, w_axis = anchor["axes"]
            b_edges = edges_by_body.get(f.get("body"), [])
            f_edges = [e for e in b_edges if f["name"] in e["name"].split("|") or links._base(f["name"]) in [links._base(x) for x in e["name"].split("|")]]
            if f_edges:
                pts = [e["start"] for e in f_edges] + [e["end"] for e in f_edges]
                u_min = min(pt[u_axis] for pt in pts)
                u_max = max(pt[u_axis] for pt in pts)
                v_min = min(pt[v_axis] for pt in pts)
                v_max = max(pt[v_axis] for pt in pts)
                new_u = u_min + anchor["offset_u"] if anchor["ref_u"] == "min" else u_max + anchor["offset_u"]
                new_v = v_min + anchor["offset_v"] if anchor["ref_v"] == "min" else v_max + anchor["offset_v"]
                n = g.unit(f.get("plane_normal", [0, 0, 1]))
                pt0 = f.get("point", [0, 0, 0])
                if abs(n[w_axis]) > 1e-4:
                    new_w = pt0[w_axis] - (n[u_axis] * (new_u - pt0[u_axis]) + n[v_axis] * (new_v - pt0[v_axis])) / n[w_axis]
                else:
                    new_w = pt0[w_axis]
                p_loc = [0.0, 0.0, 0.0]
                p_loc[u_axis] = new_u
                p_loc[v_axis] = new_v
                p_loc[w_axis] = new_w
                p_world = g.apply_point(occ["transform"], p_loc)
                loc_dir = anchor.get("local_dir", [0, 0, -1])
                d_world = g.unit(g.apply_dir(occ["transform"], loc_dir))
                return "ok", p_world, d_world
        p_loc = anchor.get("local_pos")
        if p_loc:
            p_world = g.apply_point(occ["transform"], p_loc)
            loc_dir = anchor.get("local_dir", [0, 0, -1])
            d_world = g.unit(g.apply_dir(occ["transform"], loc_dir))
            return "ok", p_world, d_world
        return "anchor_lost", None, None

    return "anchor_lost", None, None


def _check_anchor_movement(anchor: dict, new_pos: list[float], new_dir: list[float]) -> tuple[bool, list[float]]:
    """Check if anchor has moved by more than 1e-3 mm in position or axis."""
    rec_pos = anchor.get("recorded_pos")
    rec_dir = anchor.get("recorded_dir")
    if not rec_pos or not rec_dir:
        return False, [0.0, 0.0, 0.0]
    shift = g.sub(new_pos, rec_pos)
    shift_len = g.norm(shift)
    dir_diff = g.norm(g.sub(new_dir, rec_dir))
    if shift_len > 1e-3 or dir_diff > 1e-3:
        return True, [round(x, 6) for x in shift]
    return False, [0.0, 0.0, 0.0]


def preview_bolted_connection(
    ws,
    assembly: str,
    placement: dict,
    size: str,
    fasteners: dict | None = None,
    fit: str = "normal",
    counterbore: bool = True,
    connection_type: str = "through",
    blind_material: str | None = None,
    use_insert: bool = False,
    pattern: dict | None = None,
    parts: list[str] | None = None,
    head: str = "cap",
) -> dict:
    """Analyze geometry, grip length, fastener stack and hole dimensions without modifying files."""
    doc = ws.get(assembly, ASSEMBLY)
    canon_size = hole_tables.normalize_size(size)
    sc_fit, _ = hole_tables.normalize_fit(fit)
    fasteners = fasteners or {}
    conn_type = (connection_type or "through").strip().lower()
    if conn_type not in ("through", "blind", "insert"):
        raise ValueError(f"unsupported connection_type {connection_type!r} (must be 'through', 'blind' or 'insert')")

    head_norm = (head or "cap").strip().lower()
    if head_norm not in ("cap", "countersunk"):
        raise ValueError(f"unsupported head {head!r} (must be 'cap' or 'countersunk')")
    is_countersunk = (head_norm == "countersunk")

    is_insert = use_insert or (conn_type == "insert")
    is_blind = (conn_type == "blind") and not is_insert

    washer_head = bool(fasteners.get("washer_head", False)) if not is_countersunk else False
    washer_nut = bool(fasteners.get("washer_nut", True)) if (not is_blind and not is_insert) else False
    length_override = fasteners.get("length_override")

    p0, dir_w = _parse_placement(ws, doc, placement)
    rays = _generate_pattern_rays(p0, dir_w, pattern)

    penetrated = _find_penetrations(ws, doc, rays[0][0], rays[0][1])
    if parts:
        penetrated = _filter_penetrations_by_parts(penetrated, parts)
    if not penetrated:
        raise ValueError("placement ray does not intersect any parts in assembly")
    if len(penetrated) < 2:
        raise ValueError("bolted connection requires at least 2 stacked plates")

    # Reject duplicate part file in the stack (Finding 8)
    seen_files = set()
    for p in penetrated:
        fpath = Path(p["file"]).resolve()
        if fpath in seen_files:
            raise ValueError(
                f"cannot create bolted connection through duplicate part file {fpath.name!r}; "
                f"each connected plate must be a distinct part file"
            )
        seen_files.add(fpath)

    # Validate all pattern positions for uniform penetration
    for k in range(1, len(rays)):
        pk, dk = rays[k]
        pen_k = _find_penetrations(ws, doc, pk, dk)
        if parts:
            pen_k = _filter_penetrations_by_parts(pen_k, parts)
        if len(pen_k) != len(penetrated):
            raise ValueError(
                f"pattern position {k} at {pk} intersects {len(pen_k)} part(s), "
                f"expected {len(penetrated)} as at start position"
            )
        for idx in range(len(penetrated)):
            p0_part = penetrated[idx]
            pk_part = pen_k[idx]
            if pk_part["occurrence"]["name"] != p0_part["occurrence"]["name"] or pk_part["file"] != p0_part["file"]:
                raise ValueError(
                    f"pattern position {k} intersects different parts ({pk_part['occurrence']['name']}) "
                    f"than start position ({p0_part['occurrence']['name']})"
                )
            if abs(pk_part["thickness"] - p0_part["thickness"]) > 1e-3:
                raise ValueError(
                    f"pattern position {k} has plate thickness {pk_part['thickness']:.2f} mm in "
                    f"{pk_part['occurrence']['name']}, expected {p0_part['thickness']:.2f} mm"
                )

    total_thickness = sum(p["thickness"] for p in penetrated)
    clamped_thickness = sum(p["thickness"] for p in penetrated[:-1]) if (is_blind or is_insert) else total_thickness

    screw_norm = "ISO 10642" if is_countersunk else "ISO 4762"
    cb_depth = 0.0
    cb_diam = 0.0
    cs_diam = 0.0
    cs_depth = 0.0
    cs_angle = 90.0

    if is_countersunk:
        if canon_size not in standard_parts.ISO_10642:
            avail = ", ".join(standard_parts.ISO_10642)
            raise ValueError(f"unsupported size {canon_size!r} for ISO 10642 (available: {avail})")
        k_max = standard_parts.ISO_10642[canon_size]["k"]
        top_thickness = penetrated[0]["thickness"]
        if top_thickness < k_max - 1e-4:
            raise ValueError(
                f"top plate thickness ({top_thickness:.1f} mm) is smaller than head height "
                f"k = {k_max:.2f} mm for ISO 10642 {canon_size}"
            )
        counterbore = False
        cb_depth = 0.0
        cb_diam = 0.0
        cs_info = hole_tables.countersink(canon_size)
        cs_diam = cs_info["diameter"]
        cs_depth = cs_info["depth"]
        cs_angle = cs_info["angle"]
    elif counterbore:
        cb_dims = hole_tables.counterbore(canon_size, with_washer=washer_head)
        cb_diam = cb_dims["diameter"]
        cb_depth = cb_dims["depth"]
        top_thickness = penetrated[0]["thickness"]
        if cb_depth >= top_thickness - 1e-4:
            raise ValueError(
                f"counterbore depth ({cb_depth:.1f} mm) exceeds or equals top plate thickness ({top_thickness:.1f} mm); "
                f"use counterbore=False to place screw head on top of the plate without counterbore"
            )

    h_head_w = standard_parts.ISO_7089[canon_size]["h"] if washer_head else 0.0
    grip_length = clamped_thickness - cb_depth + h_head_w

    blind_info = None
    insert_info = None

    if is_blind:
        mat = hole_tables.normalize_material(blind_material)
        min_eng = hole_tables.thread_engagement_depth(canon_size, mat)
        req_length = grip_length + min_eng
        if length_override is not None:
            screw_length = float(length_override)
            if screw_length < req_length - 1e-4:
                raise ValueError(
                    f"length_override ({screw_length:.1f} mm) is less than required screw length ({req_length:.1f} mm) "
                    f"for minimum thread engagement ({min_eng:.1f} mm)"
                )
        else:
            try:
                screw_length = hole_tables.preferred_screw_length(canon_size, req_length, norm=screw_norm)
            except ValueError as e:
                if parts is None:
                    pen_names = [p["occurrence"]["name"] for p in penetrated]
                    raise ValueError(
                        f"{e}; penetrated parts: {pen_names}; use 'parts' to restrict bolted connection to specific occurrences"
                    ) from None
                raise

        actual_eng = screw_length - grip_length
        blind_info = hole_tables.blind_hole_depths(canon_size, material=mat, screw_engagement=actual_eng)

        last_thickness = penetrated[-1]["thickness"]
        if blind_info["total_depth"] > last_thickness + 1e-4:
            raise ValueError(
                f"drill total depth including tip ({blind_info['total_depth']:.1f} mm) exceeds bottom plate thickness ({last_thickness:.1f} mm)"
            )
    elif is_insert:
        r_spec = standard_parts.spec("Ruthex", canon_size)["standard"]
        m_hole = r_spec["mounting_hole"]
        L_insert = r_spec["dimensions"]["L"]
        req_length = grip_length + L_insert - 1.0
        if length_override is not None:
            screw_length = float(length_override)
            if screw_length < req_length - 1e-4:
                raise ValueError(
                    f"length_override ({screw_length:.1f} mm) is less than required screw length ({req_length:.1f} mm)"
                )
        else:
            try:
                screw_length = hole_tables.preferred_screw_length(canon_size, req_length, norm=screw_norm)
            except ValueError as e:
                if parts is None:
                    pen_names = [p["occurrence"]["name"] for p in penetrated]
                    raise ValueError(
                        f"{e}; penetrated parts: {pen_names}; use 'parts' to restrict bolted connection to specific occurrences"
                    ) from None
                raise

        penetration_in_hole = screw_length - grip_length
        if penetration_in_hole > m_hole["min_depth"] + 1e-4:
            raise ValueError(
                f"screw length {screw_length:.1f} mm penetrates {penetration_in_hole:.2f} mm into insert hole, "
                f"exceeding mounting hole depth ({m_hole['min_depth']:.1f} mm)"
            )

        insert_info = {
            "norm": "Ruthex",
            "designation": r_spec["designation"],
            "mounting_hole_diameter": m_hole["diameter"],
            "mounting_hole_depth": m_hole["min_depth"],
            "insert_length": L_insert,
        }
        last_thickness = penetrated[-1]["thickness"]
        if m_hole["min_depth"] > last_thickness + 1e-4:
            raise ValueError(
                f"Ruthex mounting hole depth ({m_hole['min_depth']:.1f} mm) exceeds bottom plate thickness ({last_thickness:.1f} mm)"
            )
    else:
        h_nut_w = standard_parts.ISO_7089[canon_size]["h"] if washer_nut else 0.0
        m_nut = standard_parts.ISO_4032[canon_size]["m"]
        P = standard_parts.ISO_10642[canon_size]["P"] if is_countersunk else standard_parts.ISO_4762[canon_size]["P"]
        protrusion = 1.5 * P
        req_length = grip_length + h_nut_w + m_nut + protrusion
        if length_override is not None:
            screw_length = float(length_override)
            if screw_length < req_length - 1e-4:
                raise ValueError(
                    f"length_override ({screw_length:.1f} mm) is less than required screw length ({req_length:.1f} mm)"
                )
        else:
            try:
                screw_length = hole_tables.preferred_screw_length(canon_size, req_length, norm=screw_norm)
            except ValueError as e:
                if parts is None:
                    pen_names = [p["occurrence"]["name"] for p in penetrated]
                    raise ValueError(
                        f"{e}; penetrated parts: {pen_names}; use 'parts' to restrict bolted connection to specific occurrences"
                    ) from None
                raise

    clearance_d = hole_tables.clearance_hole(canon_size, sc_fit)

    parts_preview = []
    num_parts = len(penetrated)
    for idx, p in enumerate(penetrated):
        is_top = (idx == 0)
        is_last = (idx == num_parts - 1)
        if is_last and is_blind:
            parts_preview.append({
                "occurrence": p["occurrence"]["name"],
                "thickness": round(p["thickness"], 4),
                "hole_type": "blind",
                "thread": canon_size,
                "tap_drill": blind_info["tap_drill"],
                "min_engagement": blind_info["min_engagement"],
                "thread_depth": blind_info["thread_depth"],
                "runout": blind_info["runout"],
                "drill_depth": blind_info["drill_depth"],
                "tip_angle": blind_info["tip_angle"],
                "material": blind_info["material"],
            })
        elif is_last and is_insert:
            parts_preview.append({
                "occurrence": p["occurrence"]["name"],
                "thickness": round(p["thickness"], 4),
                "hole_type": "insert",
                "insert_norm": "Ruthex",
                "insert_designation": insert_info["designation"],
                "mounting_hole_diameter": insert_info["mounting_hole_diameter"],
                "mounting_hole_depth": insert_info["mounting_hole_depth"],
            })
        else:
            hole_info = {
                "occurrence": p["occurrence"]["name"],
                "thickness": round(p["thickness"], 4),
                "clearance_diameter": clearance_d,
                "has_counterbore": is_top and counterbore,
                "has_countersink": is_top and is_countersunk,
            }
            if is_top and counterbore:
                hole_info["cb_diameter"] = cb_diam
                hole_info["cb_depth"] = cb_depth
            if is_top and is_countersunk:
                hole_info["cs_diameter"] = cs_diam
                hole_info["cs_depth"] = cs_depth
                hole_info["cs_angle"] = cs_angle
            parts_preview.append(hole_info)

    out = {
        "head": head_norm,
        "size": canon_size,
        "fit": sc_fit,
        "clearance_diameter": clearance_d,
        "stack_thickness": round(clamped_thickness, 4),
        "total_thickness": round(total_thickness, 4),
        "grip_length": round(grip_length, 4),
        "required_length": round(req_length, 4),
        "selected_screw_length": screw_length,
        "screw_norm": screw_norm,
        "washer_head": washer_head,
        "washer_nut": washer_nut,
        "nut_norm": "ISO 4032" if (not is_blind and not is_insert) else None,
        "counterbore": counterbore,
        "cb_diameter": cb_diam if counterbore else None,
        "cb_depth": cb_depth if counterbore else None,
        "countersink": is_countersunk,
        "cs_diameter": cs_diam if is_countersunk else None,
        "cs_depth": cs_depth if is_countersunk else None,
        "cs_angle": cs_angle if is_countersunk else None,
        "connection_type": "insert" if is_insert else ("blind" if is_blind else "through"),
        "use_insert": is_insert,
        "parts": parts_preview,
        "pattern": pattern,
        "count": len(rays),
        "instances_count": len(rays),
        "positions": [r[0] for r in rays],
    }
    if is_blind:
        out["blind_material"] = blind_info["material"]
        out["thread_depth"] = blind_info["thread_depth"]
        out["drill_depth"] = blind_info["drill_depth"]
        out["tap_drill"] = blind_info["tap_drill"]
    elif is_insert:
        out["insert_norm"] = insert_info["norm"]
        out["insert_designation"] = insert_info["designation"]
        out["mounting_hole_diameter"] = insert_info["mounting_hole_diameter"]
        out["mounting_hole_depth"] = insert_info["mounting_hole_depth"]

    return out


def bolted_connection(
    ws,
    assembly: str,
    placement: dict,
    size: str,
    fasteners: dict | None = None,
    fit: str = "normal",
    counterbore: bool = True,
    connection_type: str = "through",
    blind_material: str | None = None,
    use_insert: bool = False,
    name: str | None = None,
    pattern: dict | None = None,
    parts: list[str] | None = None,
    head: str = "cap",
) -> dict:
    """Execute a complete bolted connection across files: drill holes, create standard parts,
    insert into assembly, and connect with joints. Supports optional circular and rectangular patterns.
    Rolls back automatically on failure."""
    prev = preview_bolted_connection(
        ws, assembly, placement, size, fasteners=fasteners, fit=fit,
        counterbore=counterbore, connection_type=connection_type,
        blind_material=blind_material, use_insert=use_insert,
        pattern=pattern, parts=parts, head=head,
    )

    doc = ws.get(assembly, ASSEMBLY)
    s = doc.session
    canon_size = prev["size"]
    sc_fit = prev["fit"]
    head_norm = prev.get("head", "cap")
    screw_norm = prev.get("screw_norm", "ISO 4762")
    screw_length = prev["selected_screw_length"]
    washer_head = prev["washer_head"]
    washer_nut = prev["washer_nut"]
    effective_type = prev["connection_type"]

    p0, dir_w = _parse_placement(ws, doc, placement)
    rays = _generate_pattern_rays(p0, dir_w, pattern)
    N = len(rays)

    all_penetrations = [_find_penetrations(ws, doc, r[0], r[1]) for r in rays]
    if parts:
        all_penetrations = [_filter_penetrations_by_parts(pen, parts) for pen in all_penetrations]
    if len(all_penetrations[0]) < 2:
        raise ValueError("bolted connection requires at least 2 stacked plates")

    # Determine anchor for each instance before drilling holes into component files
    anchors = []
    for k in range(N):
        pen_k = all_penetrations[k]
        anchor_k = _determine_anchor(ws, doc, rays[k][0], rays[k][1], pen_k)
        anchors.append(anchor_k)

    stored_pattern = None
    if pattern:
        stored_pattern = dict(pattern)
        t_occ = None
        if anchors and anchors[0].get("occurrence"):
            occs = {o["name"]: o for o in links._occurrences(doc.session).values()}
            occ_a = occs.get(anchors[0]["occurrence"])
            if occ_a:
                t_occ = occ_a.get("transform")
        if t_occ:
            t_inv = g.invert_rigid(t_occ)
            pat_type = (stored_pattern.get("type") or "").strip().lower()
            if pat_type in ("circular", "circle"):
                axis_w = stored_pattern.get("axis", [0.0, 0.0, 1.0])
                axis_loc = g.unit(g.apply_dir(t_inv, axis_w))
                stored_pattern["axis_local"] = [round(x, 6) for x in axis_loc]

                axis_pt_w = stored_pattern.get("axis_point", [0.0, 0.0, 0.0])
                axis_pt_loc = g.apply_point(t_inv, axis_pt_w)
                stored_pattern["axis_point_local"] = [round(x, 6) for x in axis_pt_loc]
            elif pat_type in ("rectangular", "grid"):
                dirs_w = stored_pattern.get("directions", [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                dirs_loc = [g.unit(g.apply_dir(t_inv, d)) for d in dirs_w]
                stored_pattern["directions_local"] = [[round(x, 6) for x in d] for d in dirs_loc]
                if "direction" in stored_pattern:
                    dir_loc = g.unit(g.apply_dir(t_inv, stored_pattern["direction"]))
                    stored_pattern["direction_local"] = [round(x, 6) for x in dir_loc]
            elif pat_type in ("linear", "line"):
                if "direction" in stored_pattern:
                    dir_loc = g.unit(g.apply_dir(t_inv, stored_pattern.get("direction", [1.0, 0.0, 0.0])))
                    stored_pattern["direction_local"] = [round(x, 6) for x in dir_loc]
                if "directions" in stored_pattern:
                    dirs_loc = [g.unit(g.apply_dir(t_inv, d)) for d in stored_pattern["directions"]]
                    stored_pattern["directions_local"] = [[round(x, 6) for x in d] for d in dirs_loc]

        if anchors:
            anchors[0]["pattern"] = dict(stored_pattern)

    # Back up the assembly and every pierced part file for rollback
    backup_dir, backup = _backup_files([doc.path] + [p["file"] for p in all_penetrations[0]])

    try:
        # Step 1: Write holes into each component file
        parts_meta = []
        num_plates = len(all_penetrations[0])
        for idx in range(num_plates):
            occ = all_penetrations[0][idx]["occurrence"]
            file_path = all_penetrations[0][idx]["file"]
            part_name = Path(file_path).stem
            part_doc = ws.docs.get(part_name) or ws.open(file_path)

            t_occ = occ["transform"]
            t_inv = g.invert_rigid(t_occ)

            created_hole_feats = []
            is_top = (idx == 0)
            is_last = (idx == num_plates - 1)

            for k in range(N):
                p_k = all_penetrations[k][idx]
                ray_dir_w = rays[k][1]
                loc_pos = g.apply_point(t_inv, p_k["entry_world"])
                loc_dir = g.unit(g.apply_dir(t_inv, ray_dir_w))

                if is_last and effective_type == "blind":
                    p_prev = prev["parts"][idx]
                    base_feat = f"Hole_{canon_size}_Blind_{k+1}" if N > 1 else f"Hole_{canon_size}_Blind"
                    feat_name = _unique_feature_name(part_doc.session, base_feat, extra_used=set(created_hole_feats))
                    hole_params = {
                        "position": loc_pos,
                        "direction": loc_dir,
                        "diameter": p_prev["tap_drill"],
                        "thread": canon_size,
                        "type": "drilled",
                        "tip_angle": "118 deg",
                        "depth": p_prev["drill_depth"],
                        "name": feat_name,
                    }
                elif is_last and effective_type == "insert":
                    p_prev = prev["parts"][idx]
                    base_feat = f"Hole_Ruthex_{canon_size}_{k+1}" if N > 1 else f"Hole_Ruthex_{canon_size}"
                    feat_name = _unique_feature_name(part_doc.session, base_feat, extra_used=set(created_hole_feats))
                    hole_params = {
                        "position": loc_pos,
                        "direction": loc_dir,
                        "diameter": p_prev["mounting_hole_diameter"],
                        "depth": p_prev["mounting_hole_depth"],
                        "name": feat_name,
                    }
                else:
                    suffix = f"_{k+1}" if N > 1 else ""
                    if is_top and prev.get("countersink"):
                        base_feat = f"Hole_{canon_size}_CS{suffix}"
                    elif is_top and counterbore:
                        base_feat = f"Hole_{canon_size}_CB{suffix}"
                    else:
                        base_feat = f"Hole_{canon_size}{suffix}"
                    feat_name = _unique_feature_name(part_doc.session, base_feat, extra_used=set(created_hole_feats))
                    hole_params = {
                        "position": loc_pos,
                        "direction": loc_dir,
                        "clearance": canon_size,
                        "fit": sc_fit,
                        "name": feat_name,
                    }
                    if not (is_top and prev.get("countersink")):
                        hole_params["depth"] = p_k["thickness"]
                    if is_top and prev.get("countersink"):
                        hole_params["type"] = "countersink"
                        hole_params["cs_diameter"] = prev["cs_diameter"]
                        hole_params["cs_angle"] = prev["cs_angle"]
                    elif is_top and counterbore:
                        hole_params["type"] = "counterbore"
                        hole_params["cb_diameter"] = prev["cb_diameter"]
                        hole_params["cb_depth"] = prev["cb_depth"]

                part_doc.session.cmd("solid.hole", hole_params)
                created_hole_feats.append(feat_name)

            sketch_rule.enforce(part_doc.session)
            part_doc.save()
            parts_meta.append({
                "occurrence": occ["name"],
                "hole_feature": created_hole_feats[0],
                "hole_features": created_hole_feats,
                "file": str(file_path),
            })

        # Reload modified component geometry in the assembly
        s.cmd("component.update_links")

        # Step 2: Ensure standard parts
        screw_path = _ensure_standard_part(ws, screw_norm, canon_size, length=screw_length)
        washer_path = _ensure_standard_part(ws, "ISO 7089", canon_size) if washer_head else None
        nut_washer_path = _ensure_standard_part(ws, "ISO 7089", canon_size) if washer_nut else None
        nut_path = _ensure_standard_part(ws, "ISO 4032", canon_size) if effective_type == "through" else None
        insert_path = _ensure_standard_part(ws, "Ruthex", canon_size) if effective_type == "insert" else None

        # Step 3: Insert fasteners into assembly
        meta = doc.metadata()
        conns = meta.setdefault("bolted_connections", {})
        existing_joints = {j["name"] for j in s.cmd("joint.list").get("joints", [])}
        meta_joints = set(meta.get("joints", {}).keys())
        used_joints = existing_joints | meta_joints

        if name:
            conn_id = name
            prefix = name
        else:
            k_idx = 1
            while (f"bolted_conn_{k_idx}" in conns
                   or f"Bolted_{k_idx}_ScrewJoint" in used_joints
                   or f"Bolted_{k_idx}_1_ScrewJoint" in used_joints
                   or (k_idx == 1 and "Bolted_ScrewJoint" in used_joints)):
                k_idx += 1
            conn_id = f"bolted_conn_{k_idx}"
            prefix = f"Bolted_{k_idx}" if (k_idx > 1 or "Bolted_ScrewJoint" in used_joints) else "Bolted"

        cb_offset = (prev.get("cb_depth") or 0.0) if prev.get("counterbore") else 0.0

        all_created_joints = []
        all_created_components = []
        all_screw_occs = []
        all_washers = []
        all_nut_occs = []
        all_insert_occs = []
        instances_meta = []

        for k in range(N):
            top_p_k = all_penetrations[k][0]
            last_p_k = all_penetrations[k][-1]
            dir_k = rays[k][1]
            inst_prefix = f"{prefix}_{k+1}" if N > 1 else prefix

            p_screw_bearing = g.add(top_p_k["entry_world"], g.scale(dir_k, cb_offset))
            fastener_rot = _rotation_to_dir(dir_k)

            inst_joints = []
            inst_washers = []
            inst_screw = None
            inst_nut = None
            inst_insert = None

            # Insert (if 3D-print variant)
            if effective_type == "insert" and insert_path:
                ins_cname = links._unique_comp_name(s, f"{inst_prefix}_Insert")
                p_ins_bearing = last_p_k["entry_world"]
                ins_ruthex = links.insert(ws, doc, str(insert_path), name=ins_cname, translate=p_ins_bearing, rotate=fastener_rot)
                all_created_components.append(ins_ruthex["component"])
                r_occs = links._occurrences(s)
                inst_insert = r_occs[ins_ruthex["occurrence"]]["name"]
                all_insert_occs.append(inst_insert)

                ins_jname = f"{inst_prefix}_InsertJoint"
                ins_jp = {
                    "type": "rigid",
                    "name": ins_jname,
                    "flip": True,
                    "a": {"occurrence": last_p_k["occurrence"]["name"], "circle": p_ins_bearing},
                    "b": {"occurrence": inst_insert, "circle": p_ins_bearing},
                }
                s.cmd("joint.create", ins_jp)
                links.record(ws, doc, ins_jname, ins_jp)
                inst_joints.append(ins_jname)
                all_created_joints.append(ins_jname)

            # Head Washer (if any)
            head_washer_occ = None
            if washer_head and washer_path:
                w_cname = links._unique_comp_name(s, f"{inst_prefix}_HeadWasher")
                ins_hw = links.insert(ws, doc, str(washer_path), name=w_cname, translate=p_screw_bearing, rotate=fastener_rot)
                all_created_components.append(ins_hw["component"])
                hw_occs = links._occurrences(s)
                head_washer_occ = hw_occs[ins_hw["occurrence"]]["name"]
                inst_washers.append(head_washer_occ)
                all_washers.append(head_washer_occ)

                hw_jname = f"{inst_prefix}_HeadWasherJoint"
                hw_jp = {
                    "type": "rigid",
                    "name": hw_jname,
                    "flip": True,
                    "a": {"occurrence": top_p_k["occurrence"]["name"], "circle": p_screw_bearing},
                    "b": {"occurrence": head_washer_occ, "circle": p_screw_bearing},
                }
                s.cmd("joint.create", hw_jp)
                links.record(ws, doc, hw_jname, hw_jp)
                inst_joints.append(hw_jname)
                all_created_joints.append(hw_jname)
                p_screw_bearing = g.add(p_screw_bearing, g.scale(dir_k, -standard_parts.ISO_7089[canon_size]["h"]))

            # Screw
            screw_cname = links._unique_comp_name(s, f"{inst_prefix}_Screw")
            ins_screw = links.insert(ws, doc, str(screw_path), name=screw_cname, translate=p_screw_bearing, rotate=fastener_rot)
            all_created_components.append(ins_screw["component"])
            screw_occs = links._occurrences(s)
            inst_screw = screw_occs[ins_screw["occurrence"]]["name"]
            all_screw_occs.append(inst_screw)

            screw_jname = f"{inst_prefix}_ScrewJoint"
            if prev.get("countersink"):
                screw_target_occ = top_p_k["occurrence"]["name"]
                screw_jp = {
                    "type": "rigid",
                    "name": screw_jname,
                    "a": {"occurrence": screw_target_occ, "point": p_screw_bearing, "z": g.scale(dir_k, -1.0)},
                    "b": {"occurrence": inst_screw, "point": p_screw_bearing, "z": g.scale(dir_k, -1.0)},
                }
                s.cmd("joint.create", screw_jp)

                # Verify screw shank orientation in world coordinates: shank extends along dir_k
                occs_now = {o["name"]: o for o in links._occurrences(s).values()}
                if inst_screw in occs_now:
                    shank_w = g.unit(g.apply_dir(occs_now[inst_screw]["transform"], [0.0, 0.0, -1.0]))
                    if g.dot(shank_w, dir_k) < 0.5:
                        needed_flip = not screw_jp.get("flip", False)
                        s.cmd("joint.edit", {"joint": screw_jname, "flip": needed_flip})
                        screw_jp["flip"] = needed_flip

                links.record(ws, doc, screw_jname, screw_jp)
                inst_joints.append(screw_jname)
                all_created_joints.append(screw_jname)
            else:
                screw_target_occ = head_washer_occ if head_washer_occ else top_p_k["occurrence"]["name"]
                screw_jp = {
                    "type": "rigid",
                    "name": screw_jname,
                    "flip": True,
                    "a": {"occurrence": screw_target_occ, "circle": p_screw_bearing},
                    "b": {"occurrence": inst_screw, "circle": p_screw_bearing},
                }
                s.cmd("joint.create", screw_jp)

                # Determine alignment from the actual axis of the chosen joint reference against ray direction
                joints_list = s.cmd("joint.list").get("joints", [])
                created_j = next((j for j in joints_list if j.get("name") == screw_jname), None)
                if created_j and "frame_a" in created_j and "z" in created_j["frame_a"]:
                    fa_z = created_j["frame_a"]["z"]
                    needed_flip = (g.dot(fa_z, dir_k) < 0)
                    if screw_jp["flip"] != needed_flip:
                        s.cmd("joint.edit", {"joint": screw_jname, "flip": needed_flip})
                        screw_jp["flip"] = needed_flip

                # Verify screw shank orientation in world coordinates: shank extends along dir_k
                occs_now = links._occurrences(s)
                if inst_screw in occs_now:
                    shank_w = g.unit(g.apply_dir(occs_now[inst_screw]["transform"], [0.0, 0.0, -1.0]))
                    if g.dot(shank_w, dir_k) < 0.5:
                        needed_flip = not screw_jp["flip"]
                        s.cmd("joint.edit", {"joint": screw_jname, "flip": needed_flip})
                        screw_jp["flip"] = needed_flip

                links.record(ws, doc, screw_jname, screw_jp)
                inst_joints.append(screw_jname)
                all_created_joints.append(screw_jname)

            # Exit face of last plate (only for through connection)
            if effective_type == "through":
                p_exit = last_p_k["exit_world"]

                nut_washer_occ = None
                p_nut_bearing = p_exit
                if washer_nut and nut_washer_path:
                    nw_cname = links._unique_comp_name(s, f"{inst_prefix}_Washer")
                    h_w = standard_parts.ISO_7089[canon_size]["h"]
                    p_washer_init = g.add(p_exit, g.scale(dir_k, h_w))
                    ins_nw = links.insert(ws, doc, str(nut_washer_path), name=nw_cname, translate=p_washer_init, rotate=fastener_rot)
                    all_created_components.append(ins_nw["component"])
                    nw_occs = links._occurrences(s)
                    nut_washer_occ = nw_occs[ins_nw["occurrence"]]["name"]
                    inst_washers.append(nut_washer_occ)
                    all_washers.append(nut_washer_occ)

                    nw_jname = f"{inst_prefix}_WasherJoint"
                    nw_jp = {
                        "type": "rigid",
                        "name": nw_jname,
                        "flip": False,
                        "a": {"occurrence": last_p_k["occurrence"]["name"], "circle": p_exit},
                        "b": {"occurrence": nut_washer_occ, "circle": p_exit},
                    }
                    s.cmd("joint.create", nw_jp)
                    links.record(ws, doc, nw_jname, nw_jp)
                    inst_joints.append(nw_jname)
                    all_created_joints.append(nw_jname)
                    p_nut_bearing = p_washer_init

                # Nut
                nut_cname = links._unique_comp_name(s, f"{inst_prefix}_Nut")
                m_nut = standard_parts.ISO_4032[canon_size]["m"]
                p_nut_init = g.add(p_nut_bearing, g.scale(dir_k, m_nut))
                ins_nut = links.insert(ws, doc, str(nut_path), name=nut_cname, translate=p_nut_init, rotate=fastener_rot)
                all_created_components.append(ins_nut["component"])
                n_occs = links._occurrences(s)
                inst_nut = n_occs[ins_nut["occurrence"]]["name"]
                all_nut_occs.append(inst_nut)

                nut_jname = f"{inst_prefix}_NutJoint"
                nut_target_occ = nut_washer_occ if nut_washer_occ else last_p_k["occurrence"]["name"]
                nut_jp = {
                    "type": "rigid",
                    "name": nut_jname,
                    "flip": False,
                    "a": {"occurrence": nut_target_occ, "circle": p_nut_bearing},
                    "b": {"occurrence": inst_nut, "circle": p_nut_bearing},
                }
                s.cmd("joint.create", nut_jp)
                links.record(ws, doc, nut_jname, nut_jp)
                inst_joints.append(nut_jname)
                all_created_joints.append(nut_jname)

            instances_meta.append({
                "index": k,
                "position": rays[k][0],
                "direction": rays[k][1],
                "anchor": anchors[k] if k < len(anchors) else None,
                "screw": inst_screw,
                "washers": inst_washers,
                "nut": inst_nut,
                "insert": inst_insert,
                "joints": inst_joints,
            })

        # Step 4: Update links & check joints
        links_res = links.update_links(ws, doc, repair_moved=True)

        # Step 5: Store metadata in assembly document
        conn_record = {
            "id": conn_id,
            "anchor": anchors[0] if anchors else None,
            "anchors": anchors,
            "parameters": {
                "placement": placement,
                "pattern": stored_pattern,
                "size": canon_size,
                "fasteners": fasteners,
                "fit": fit,
                "counterbore": counterbore,
                "connection_type": connection_type,
                "blind_material": blind_material,
                "use_insert": use_insert,
                "name": name,
                "parts": parts,
                "head": head_norm,
            },
            "size": canon_size,
            "head": head_norm,
            "type": effective_type,
            "screw": all_screw_occs[0] if all_screw_occs else None,
            "screws": all_screw_occs,
            "screw_norm": screw_norm,
            "screw_length": screw_length,
            "grip_length": prev["grip_length"],
            "washers": all_washers,
            "washer_head": washer_head,
            "washer_nut": washer_nut,
            "nut": all_nut_occs[0] if all_nut_occs else None,
            "nuts": all_nut_occs,
            "insert": all_insert_occs[0] if all_insert_occs else None,
            "inserts": all_insert_occs,
            "parts": parts_meta,
            "joints": all_created_joints,
            "components": all_created_components,
            "pattern": stored_pattern,
            "count": N,
            "instances": instances_meta,
            "countersink": prev.get("countersink", False),
            "cs_diameter": prev.get("cs_diameter"),
            "cs_depth": prev.get("cs_depth"),
            "cs_angle": prev.get("cs_angle"),
        }
        if effective_type == "blind":
            conn_record["blind_material"] = prev.get("blind_material")
            conn_record["thread_depth"] = prev.get("thread_depth")
            conn_record["drill_depth"] = prev.get("drill_depth")
        elif effective_type == "insert":
            conn_record["insert_norm"] = prev.get("insert_norm")
            conn_record["mounting_hole_diameter"] = prev.get("mounting_hole_diameter")
            conn_record["mounting_hole_depth"] = prev.get("mounting_hole_depth")

        curr_meta = doc.metadata()
        curr_meta.setdefault("bolted_connections", {})[conn_id] = conn_record
        doc.set_metadata(curr_meta)
        doc.save()

        return dict(conn_record, warnings=links_res.get("warnings", []))

    except Exception:
        _restore_backup(ws, doc, backup)
        raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def list_bolted_connections(ws, assembly: str) -> dict:
    """List all bolted connections recorded in `assembly`."""
    doc = ws.get(assembly, ASSEMBLY)
    conns = doc.metadata().get("bolted_connections", {})
    return {
        "connections": dict(conns),
        "count": len(conns),
    }


def delete_bolted_connection(ws, assembly: str, id: str) -> dict:
    """Delete a bolted connection from an assembly: removes fastener parts, joints and hole features
    from penetrated components, then saves the assembly and components."""
    doc = ws.get(assembly, ASSEMBLY)
    s = doc.session
    meta = doc.metadata()
    conns = meta.get("bolted_connections", {})
    if id not in conns:
        raise KeyError(f"no bolted connection {id!r} in assembly {assembly!r}")
    conn = conns[id]

    removed_joints = []
    removed_components = []
    removed_holes = {}

    # 1. Delete joints
    for j in conn.get("joints", []):
        try:
            s.cmd("joint.delete", {"joint": j})
            removed_joints.append(j)
        except Exception:
            pass
        links.forget(doc, j)

    # 2. Delete fastener components
    comps_to_delete = set(conn.get("components", []))
    fastener_occs = set()
    for key in ("screw", "nut", "insert"):
        if conn.get(key):
            fastener_occs.add(conn[key])
    for key in ("screws", "nuts", "inserts", "washers"):
        for item in conn.get(key, []):
            if item:
                fastener_occs.add(item)
    for inst in conn.get("instances", []):
        for key in ("screw", "nut", "insert"):
            if inst.get(key):
                fastener_occs.add(inst[key])
        for w in inst.get("washers", []):
            if w:
                fastener_occs.add(w)

    current_comps = s.cmd("component.list")["components"]
    for c in current_comps:
        if c["id"] == 0:
            continue
        c_occs = {o["name"] for o in c.get("occurrences", [])}
        if c["id"] in comps_to_delete or c["name"] in comps_to_delete or bool(c_occs & fastener_occs):
            try:
                s.cmd("component.break_link", {"component": c["id"]})
            except Exception:
                pass
            try:
                s.cmd("component.delete", {"component": c["id"]})
                removed_components.append(c["name"])
            except Exception:
                pass

    # 3. Delete hole features in component files
    for p_info in conn.get("parts", []):
        fpath = Path(p_info["file"])
        part_name = fpath.stem
        part_doc = ws.docs.get(part_name) or ws.open(fpath)
        feats = list(p_info.get("hole_features", []))
        if not feats and "hole_feature" in p_info:
            feats = [p_info["hole_feature"]]
        deleted_for_part = []
        for feat in reversed(feats):
            try:
                sketch_rule.delete_with_owned(part_doc.session, feat)
                deleted_for_part.append(feat)
            except Exception:
                try:
                    part_doc.session.cmd("timeline.delete", {"features": [feat]})
                    deleted_for_part.append(feat)
                except Exception:
                    pass
        if deleted_for_part:
            sketch_rule.enforce(part_doc.session)
            part_doc.save()
            removed_holes[part_name] = deleted_for_part

    # 4. Update links in assembly
    s.cmd("component.update_links")

    # 5. Clean up metadata
    curr_meta = doc.metadata()
    curr_meta.get("bolted_connections", {}).pop(id, None)
    doc.set_metadata(curr_meta)
    doc.save()

    return {
        "id": id,
        "deleted": id,
        "removed_joints": removed_joints,
        "removed_components": removed_components,
        "removed_holes": removed_holes,
    }


def edit_bolted_connection(ws, assembly: str, id: str, **changes) -> dict:
    """Edit an existing bolted connection by applying changes (e.g. size, length, fit, counterbore).
    Implemented as delete + recreate with the same positions; old state is fully restored on error."""
    doc = ws.get(assembly, ASSEMBLY)
    meta = doc.metadata()
    conns = meta.get("bolted_connections", {})
    if id not in conns:
        raise KeyError(f"no bolted connection {id!r} in assembly {assembly!r}")
    old_conn = conns[id]

    old_params = dict(old_conn.get("parameters", {}))
    if not old_params:
        old_params = {
            "placement": old_conn.get("placement"),
            "pattern": old_conn.get("pattern"),
            "size": old_conn.get("size"),
            "fasteners": {
                "washer_head": old_conn.get("washer_head"),
                "washer_nut": old_conn.get("washer_nut"),
            },
            "fit": old_conn.get("fit", "normal"),
            "counterbore": bool(old_conn.get("counterbore")),
            "connection_type": old_conn.get("type", "through"),
            "blind_material": old_conn.get("blind_material"),
            "use_insert": (old_conn.get("type") == "insert"),
            "name": id,
            "parts": old_conn.get("parameters", {}).get("parts"),
            "head": old_conn.get("head", "cap"),
        }
    if "head" not in old_params:
        old_params["head"] = old_conn.get("head", "cap")

    new_params = dict(old_params)
    for k, v in changes.items():
        if k == "fasteners" and isinstance(v, dict):
            m_fasteners = dict(old_params.get("fasteners") or {})
            m_fasteners.update(v)
            new_params["fasteners"] = m_fasteners
        else:
            new_params[k] = v
    new_params["name"] = id

    # Pre-validate size / fit / material / head if provided
    if "size" in new_params and new_params["size"]:
        hole_tables.normalize_size(new_params["size"])
    if "fit" in new_params and new_params["fit"]:
        hole_tables.normalize_fit(new_params["fit"])
    if "head" in new_params and new_params["head"]:
        h_val = (new_params["head"] or "cap").strip().lower()
        if h_val not in ("cap", "countersunk"):
            raise ValueError(f"unsupported head {new_params['head']!r} (must be 'cap' or 'countersunk')")
    if new_params.get("connection_type") == "blind" and new_params.get("blind_material"):
        hole_tables.normalize_material(new_params["blind_material"])

    # Back up the assembly and the affected part files for rollback
    backup_dir, backup = _backup_files(
        [doc.path] + [p_info["file"] for p_info in old_conn.get("parts", [])])
    try:
        # 1. Delete old connection
        delete_bolted_connection(ws, assembly, id)

        # 2. Recreate with new_params
        new_conn = bolted_connection(ws, assembly, **new_params)
        return new_conn
    except Exception:
        _restore_backup(ws, doc, backup)
        raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def check_and_update_bolted_connections(ws, doc, repair: bool = False) -> list[dict]:
    """Check every recorded bolted connection in `doc` against its anchor.
    If an anchor has moved (> 1e-3 mm), rebuilds it via edit_bolted_connection when repair=True.
    When repair=False, reports 'moved' without modifying files.
    Lost anchors are reported as 'anchor_lost' without guessing.
    Returns: [{'id': id, 'status': 'ok'|'moved'|'moved_repaired'|'anchor_lost'|'failed',
               'shifted_by': [dx, dy, dz], 'error'?: str}]"""
    meta = doc.metadata()
    conns = meta.get("bolted_connections", {})
    results = []

    for conn_id in sorted(list(conns.keys())):
        curr_meta = doc.metadata().get("bolted_connections", {})
        if conn_id not in curr_meta:
            continue
        conn_meta = curr_meta[conn_id]

        anchor = conn_meta.get("anchor")
        if not anchor and conn_meta.get("instances"):
            anchor = conn_meta["instances"][0].get("anchor")

        if not anchor:
            results.append({
                "id": conn_id,
                "status": "ok",
                "shifted_by": [0.0, 0.0, 0.0],
            })
            continue

        st, new_pos, new_dir = _resolve_anchor(ws, doc, anchor)
        if st != "ok":
            results.append({
                "id": conn_id,
                "status": "anchor_lost",
                "shifted_by": [0.0, 0.0, 0.0],
            })
            continue

        has_moved, shifted_by = _check_anchor_movement(anchor, new_pos, new_dir)

        occs = {o["name"]: o for o in links._occurrences(doc.session).values()}
        anchor_occ = occs.get(anchor.get("occurrence"))
        t_occ = anchor_occ.get("transform") if anchor_occ else None

        old_params = dict(conn_meta.get("parameters", {}))
        pattern_params = None
        if old_params.get("pattern"):
            pattern_params = dict(old_params["pattern"])
        elif conn_meta.get("pattern"):
            pattern_params = dict(conn_meta["pattern"])
        elif anchor.get("pattern"):
            pattern_params = dict(anchor["pattern"])

        # Check if pattern has local recorded values from anchor if missing in pattern_params
        if pattern_params and anchor.get("pattern"):
            for lk in ("axis_local", "axis_point_local", "directions_local", "direction_local"):
                if lk in anchor["pattern"] and lk not in pattern_params:
                    pattern_params[lk] = anchor["pattern"][lk]

        pattern_changed = False
        if pattern_params and t_occ:
            p_type = (pattern_params.get("type") or "").strip().lower()
            if p_type in ("circular", "circle"):
                if "axis_local" in pattern_params:
                    cur_axis = g.unit(g.apply_dir(t_occ, pattern_params["axis_local"]))
                    if g.norm(g.sub(cur_axis, pattern_params.get("axis", [0, 0, 1]))) > 1e-3:
                        pattern_changed = True
                if "axis_point_local" in pattern_params:
                    cur_ap = g.apply_point(t_occ, pattern_params["axis_point_local"])
                    if g.norm(g.sub(cur_ap, pattern_params.get("axis_point", [0, 0, 0]))) > 1e-3:
                        pattern_changed = True
            elif p_type in ("rectangular", "grid", "linear", "line"):
                if "directions_local" in pattern_params:
                    cur_dirs = [g.unit(g.apply_dir(t_occ, d)) for d in pattern_params["directions_local"]]
                    old_dirs = pattern_params.get("directions", [])
                    if any(g.norm(g.sub(cd, od)) > 1e-3 for cd, od in zip(cur_dirs, old_dirs)):
                        pattern_changed = True
                if "direction_local" in pattern_params:
                    cur_d = g.unit(g.apply_dir(t_occ, pattern_params["direction_local"]))
                    if g.norm(g.sub(cur_d, pattern_params.get("direction", [1, 0, 0]))) > 1e-3:
                        pattern_changed = True

        if not has_moved and not pattern_changed:
            results.append({
                "id": conn_id,
                "status": "ok",
                "shifted_by": [0.0, 0.0, 0.0],
            })
            continue

        if not repair:
            results.append({
                "id": conn_id,
                "status": "moved",
                "shifted_by": shifted_by,
            })
            continue

        try:
            old_placement = dict(old_params.get("placement") or {})
            new_placement = dict(old_placement)
            new_placement["position"] = [round(x, 6) for x in new_pos]
            new_placement["direction"] = [round(x, 6) for x in new_dir]
            new_placement["type"] = "point"

            if pattern_params:
                p_type = (pattern_params.get("type") or "").strip().lower()
                if p_type in ("circular", "circle"):
                    if t_occ and ("axis_local" in pattern_params or "axis_point_local" in pattern_params):
                        if "axis_local" in pattern_params:
                            new_axis = g.unit(g.apply_dir(t_occ, pattern_params["axis_local"]))
                            pattern_params["axis"] = [round(x, 6) for x in new_axis]
                        if "axis_point_local" in pattern_params:
                            new_ap = g.apply_point(t_occ, pattern_params["axis_point_local"])
                            pattern_params["axis_point"] = [round(x, 6) for x in new_ap]
                        elif "axis_point" in pattern_params:
                            old_ap = pattern_params["axis_point"]
                            pattern_params["axis_point"] = [
                                round(old_ap[i] + shifted_by[i], 6) for i in range(3)
                            ]
                    else:
                        # Legacy behavior: axis remains unchanged, axis_point is shifted by shifted_by
                        if "axis_point" in pattern_params:
                            old_ap = pattern_params["axis_point"]
                            pattern_params["axis_point"] = [
                                round(old_ap[i] + shifted_by[i], 6) for i in range(3)
                            ]
                elif p_type in ("rectangular", "grid"):
                    if t_occ and ("directions_local" in pattern_params or "direction_local" in pattern_params):
                        if "directions_local" in pattern_params:
                            new_dirs = [g.unit(g.apply_dir(t_occ, d)) for d in pattern_params["directions_local"]]
                            pattern_params["directions"] = [[round(x, 6) for x in d] for d in new_dirs]
                        if "direction_local" in pattern_params:
                            new_d = g.unit(g.apply_dir(t_occ, pattern_params["direction_local"]))
                            pattern_params["direction"] = [round(x, 6) for x in new_d]
                    # Legacy behavior: directions unchanged
                elif p_type in ("linear", "line"):
                    if t_occ and ("direction_local" in pattern_params or "directions_local" in pattern_params):
                        if "direction_local" in pattern_params:
                            new_d = g.unit(g.apply_dir(t_occ, pattern_params["direction_local"]))
                            pattern_params["direction"] = [round(x, 6) for x in new_d]
                        if "directions_local" in pattern_params:
                            new_dirs = [g.unit(g.apply_dir(t_occ, d)) for d in pattern_params["directions_local"]]
                            pattern_params["directions"] = [[round(x, 6) for x in d] for d in new_dirs]
                    # Legacy behavior: directions unchanged

            edit_bolted_connection(
                ws,
                doc.name,
                conn_id,
                placement=new_placement,
                pattern=pattern_params,
            )
            results.append({
                "id": conn_id,
                "status": "moved_repaired",
                "shifted_by": shifted_by,
            })
        except Exception as e:
            results.append({
                "id": conn_id,
                "status": "failed",
                "shifted_by": shifted_by,
                "error": str(e),
            })

    return results


__all__ = [
    "preview_bolted_connection",
    "bolted_connection",
    "list_bolted_connections",
    "delete_bolted_connection",
    "edit_bolted_connection",
    "check_and_update_bolted_connections",
]
