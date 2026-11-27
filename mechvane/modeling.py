"""One way to run modelling commands in a document, for the agent (MCP `run`) and for
plugins and tools: all or nothing, sketch rule, state delta, explained errors."""

import json
import math

from . import geometry as g, links, sc_errors, sc_locate, sketch_rule, state_delta
from .documents import PART


def compact(v):
    """Leave out what a reply repeats without telling anything: nulls, empty lists, timings."""
    if isinstance(v, dict):
        return {k: compact(x) for k, x in v.items() if k != "ms" and x is not None and x != [] and x != {}}
    if isinstance(v, list):
        return [compact(x) for x in v]
    return v


def _restore(session, cp, forget=True):
    try:
        session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": forget} if forget else {"checkpoint": cp})
    except Exception:
        pass


def run_commands(doc, commands: list[dict], verbose: bool = False) -> dict:
    """Run SolidCraft commands ([{command, params}]) in a document, all or nothing. In a part, owned
    sketches are then moved directly before their feature and a state delta is returned. A failed
    command leaves the document as it was and raises RuntimeError with an explanation when known."""
    cp = None
    snap_before = None
    failing_before = set()
    if doc.kind == PART:
        try:
            cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        except Exception:
            cp = None
        try:
            failing_before = set(_failing(doc.session.cmd("document.inspect", {"measure": False})))
        except Exception:
            pass
        try:
            snap_before = state_delta.snapshot(doc.session)
        except Exception:
            snap_before = None
    try:
        result = doc.session.batch(commands)
    except Exception as e:
        location = _locate_failure(doc, commands, e, cp) if doc.kind == PART else None
        if cp is not None:
            _restore(doc.session, cp)
        sc_errors.reraise(e, location)

    out = {"results": result.get("results", result) if isinstance(result, dict) else result}
    if not verbose:
        out["results"] = compact(out["results"])
    if doc.kind == PART and not getattr(doc, "window", False):
        # not in the user's window: enforce moves every sketch of the design, also the ones the user placed (#181)
        try:
            out["sketch_rule"] = sketch_rule.enforce(doc.session)
        except Exception as e:
            if cp is not None:
                _restore(doc.session, cp, forget=False)
            raise RuntimeError(f"sketch rule failed, rolled back batch: {e}") from e
        if snap_before is not None:
            try:
                out["delta"] = state_delta.diff(snap_before, state_delta.snapshot(doc.session))
            except Exception:
                pass
        try:
            insp = doc.session.cmd("document.inspect")
            broken = _feature_errors(doc.session, insp, failing_before)
            if broken:
                out["feature_errors"] = broken
                out.setdefault("warnings", []).append(
                    f"{', '.join(b['feature'] for b in broken)} fail(s) after this change and is left out of the "
                    "model (see feature_errors): fix it, or take the change back.")
            still = sorted(failing_before & set(_failing(insp)))
            if still:
                out.setdefault("warnings", []).append(f"Still failing from before: {', '.join(still)}.")
            marker = insp.get("marker")
            tl = insp.get("timeline", [])
            if marker is not None and marker < len(tl):
                rolled_back = [f["name"] for f in tl[marker:]]
                first_rolled = rolled_back[0] if rolled_back else "?"
                msg = (
                    f"Part end is not at the end (position {marker} of {len(tl)}, "
                    f"before {first_rolled!r}); {len(rolled_back)} feature(s) rolled back. "
                    f"Call part_end({doc.name!r}) to roll to the end."
                )
                out.setdefault("warnings", []).append(msg)
                if "delta" in out and isinstance(out["delta"], dict):
                    out["delta"].setdefault("warnings", []).append(msg)
                out["part_end"] = {
                    "position": marker,
                    "total_features": len(tl),
                    "rolled_back": rolled_back,
                }
        except Exception:
            pass
    if cp is not None:
        _restore(doc.session, cp)
    return out


_REPLAYABLE = ("solid.", "sketch.", "parameters.", "construct.", "timeline.")


def _failing(insp: dict) -> dict:
    return {f["name"]: f["error"] for f in insp.get("timeline", []) if isinstance(f, dict) and f.get("error")}


def _failed_step(e) -> dict | None:
    """The `failed` entry ({command, error, index}) of a batch reply inside an error text."""
    text = str(e)
    # the reply starts a line; an explanation before it may hold braces of its own
    start = 0 if text.lstrip().startswith("{") else text.find("\n{") + 1
    if start == 0 and not text.lstrip().startswith("{"):
        return None
    try:
        reply = json.JSONDecoder().raw_decode(text[start:])[0]
        failed = reply.get("failed")
    except (ValueError, AttributeError):
        return None
    if not (isinstance(failed, dict) and isinstance(failed.get("error"), str)):
        return None
    return dict(failed, completed=reply.get("completed"))


def _locate_failure(doc, commands: list[dict], e, cp) -> dict | None:
    """Where the failed step of a batch went wrong. The batch is rolled back, so the steps before the
    failed one are run again to look at the model it saw, then taken back."""
    failed = _failed_step(e)
    try:
        index = int(failed.get("index", 0))
        step = commands[index]
        command = step.get("command") or ""
    except (AttributeError, IndexError, TypeError, ValueError):
        return None
    if command.startswith("sketch.") or (index > 0 and cp is None):
        return None
    if index > 0 and failed.get("completed") == 0:
        return None  # refused when the batch was checked, before any step ran: nothing to look at
    # only modelling steps are run a second time: never a save, an import or an export
    if any(not str(c.get("command", "")).startswith(_REPLAYABLE) for c in commands[:index]):
        return None
    try:
        if index > 0:
            doc.session.batch(commands[:index])
        return sc_locate.locate(doc.session, command, step.get("params") or {}, failed["error"])
    except Exception:
        return None
    finally:
        if index > 0:
            _restore(doc.session, cp, forget=False)


def _feature_errors(session, insp: dict, failing_before: set) -> list[dict]:
    """Features that fail now and did not before the batch (an edit before them took away what they
    need), each with explanation and place."""
    new = {name: err for name, err in _failing(insp).items() if name not in failing_before}
    if not new:
        return []
    try:
        model = sc_locate.Model(session)
    except Exception:
        model = None
    out = []
    for name, err in new.items():
        entry = {"feature": name, "error": err}
        exp = sc_errors.explain(err)
        if exp is not None:
            entry.update(message=exp["message"], hint=exp["hint"])
        location = sc_locate.locate_feature(session, name, err, model=model) if model is not None else None
        if location:
            entry.update(where=location["text"], location=sc_locate.brief(location))
        out.append(entry)
    return out


def error_place(e) -> dict | None:
    """The place found for an error raised by run_commands ({text, at, features, kind, …}), or None."""
    return getattr(e, "location", None)


def short_error(e) -> str:
    """One readable line for a dialog: Mechvane's explanation (when known) and SolidCraft's own words,
    which often name the size that would fit, without the raw batch reply."""
    text = str(e)
    head = text.partition("\n")[0]
    inner = (_failed_step(e) or {}).get("error")
    if inner:
        inner = inner.split(": ", 1)[1] if inner.startswith("not supported yet: ") else inner
        inner = inner[:1].upper() + inner[1:]
    if head.lstrip().startswith("{") or head.startswith("Where: "):  # no explanation: SolidCraft's words lead
        return inner or head
    if not inner:
        return head
    # SolidCraft's words are concrete (sizes that fit); the general hint in brackets can go
    message = head[:head.rfind(" (")] if head.endswith(")") and " (" in head else head
    return f"{message} SolidCraft: {inner}"


def _transform_delta(m_before, m_after, ref_point=None) -> tuple[float, float]:
    """Translation distance (mm) of `ref_point` (default: origin) and rotation angle (degrees)
    between two 4x4 row-vector transforms."""
    if ref_point is None:
        dist = g.norm(g.sub(m_after[3][:3], m_before[3][:3]))
    else:
        dist = g.norm(g.sub(g.apply_point(m_after, ref_point), g.apply_point(m_before, ref_point)))
    trace = sum(m_before[i][j] * m_after[i][j] for i in range(3) for j in range(3))
    cos_a = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    return dist, math.degrees(math.acos(cos_a))


def _occurrence_midpoints(session, occs: dict | list) -> dict[int, list[float]]:
    """Local bounding-box midpoint (in each occurrence's coordinate frame) for the given occurrences.
    Returns {occ_id: [x, y, z]} for occurrences that have measured body geometry."""
    try:
        comps = {c["id"]: c for c in session.cmd("component.list").get("components", [])}
        bodies = {
            b["name"]: b["bbox"]
            for b in session.cmd("document.inspect", {"measure": True}).get("bodies", [])
            if b.get("bbox") and "min" in b["bbox"] and "max" in b["bbox"]
        }
    except Exception:
        return {}
    if not comps or not bodies:
        return {}

    cache: dict[int, dict | None] = {}

    def _local_bbox(comp_id: int, seen: set[int]) -> dict | None:
        if comp_id in cache:
            return cache[comp_id]
        if comp_id in seen:
            return None
        comp = comps.get(comp_id)
        if not comp:
            return None
        next_seen = seen | {comp_id}
        pts = []
        for b_name in comp.get("bodies", []):
            bb = bodies.get(b_name)
            if bb is not None:
                pts.extend((bb["min"], bb["max"]))
        for ch in comp.get("children", []):
            ch_bb = _local_bbox(ch["component"], next_seen)
            if ch_bb is not None:
                lo, hi = ch_bb["min"], ch_bb["max"]
                m_ch = ch["transform"]
                pts.extend(
                    g.apply_point(m_ch, [x, y, z])
                    for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])
                )
        res = {"min": [min(p[i] for p in pts) for i in range(3)],
               "max": [max(p[i] for p in pts) for i in range(3)]} if pts else None
        cache[comp_id] = res
        return res

    occ_list = occs.values() if isinstance(occs, dict) else occs
    out = {}
    for o in occ_list:
        bb = _local_bbox(o["component"], set())
        if bb is not None:
            out[o["id"]] = [(a + b) / 2.0 for a, b in zip(bb["min"], bb["max"])]
    return out


def adopt_joint(ws, doc, joint: str) -> dict:
    """Record both side anchors of an existing joint so update_links / check_joints can verify it."""
    return {"anchors": links.record(ws, doc, joint)["sides"]}


def add_joint(ws, doc, params: dict, as_built: bool = False) -> dict:
    """Create a joint via SolidCraft joint.create (or joint.as_built when as_built=True, `name` required)
    and record both side anchors with links.record so update_links / check_joints can verify it later."""
    if not params.get("name"):
        raise ValueError("give the joint a name")
    resolved = links.resolve_occurrences(doc.session, params)
    if as_built:
        ab_params = dict(resolved)
        # Allow joint.create-style {"occurrence": ..., "face": ...} dicts by unwrapping to OccurrenceKey.
        for side in ("b", "a"):
            if isinstance(ab_params.get(side), dict) and "occurrence" in ab_params[side]:
                if "at" not in ab_params and any(k != "occurrence" for k in ab_params[side]):
                    ab_params["at"] = ab_params[side]
                ab_params[side] = ab_params[side]["occurrence"]
        r = doc.session.cmd("joint.as_built", ab_params)
        return {"joint": r, **adopt_joint(ws, doc, ab_params["name"])}

    occs_before = links._occurrences(doc.session)
    r = doc.session.cmd("joint.create", resolved)
    anchors = links.record(ws, doc, resolved["name"], resolved)
    out = {"joint": r, "anchors": anchors["sides"]}

    joints = doc.session.cmd("joint.list").get("joints", [])
    jid = r.get("joint") if isinstance(r, dict) else None
    j = next((x for x in joints if (jid is not None and x.get("id") == jid) or x.get("name") == resolved["name"]), None)
    if j is not None and j.get("b") in occs_before:
        occs_after = links._occurrences(doc.session)
        occ_b = occs_after.get(j["b"])
        if occ_b is not None:
            m_before = occs_before[j["b"]]["transform"]
            m_after = occ_b["transform"]
            if not g.same_mat(m_before, m_after, tol=1e-9):
                mids = _occurrence_midpoints(doc.session, [occ_b])
                dist, angle_deg = _transform_delta(m_before, m_after, ref_point=mids.get(occ_b["id"]))
                if dist > 1e-3 or angle_deg > 1e-2:
                    out["warnings"] = [
                        f"{occ_b['name']} moved by {dist:.3f} mm and rotated by {angle_deg:.2f}°; "
                        f"pass as_built=True if parts are already positioned and should stay in place."
                    ]
    return out


def edit_joint(ws, doc, joint: str, params: dict) -> dict:
    """Change a joint via SolidCraft joint.edit and record its updated side anchors."""
    resolved = links.resolve_occurrences(doc.session, params)
    new_name = resolved.get("name", joint)
    meta = doc.metadata()
    joints_meta = meta.get("joints", {})
    old_data = joints_meta.get(joint) if isinstance(joints_meta.get(joint), dict) else {}
    old_create = dict(old_data["create"]) if isinstance(old_data.get("create"), dict) else None
    edit_cmd = dict(resolved, joint=joint)
    if ("a" in resolved or "b" in resolved) and "angle" not in resolved and old_create and "angle" in old_create:
        edit_cmd["angle"] = old_create["angle"]
    r = doc.session.cmd("joint.edit", edit_cmd)
    if new_name != joint and joint in joints_meta:
        joints_meta.pop(joint)
        joints_meta[new_name] = old_data
        doc.set_metadata(meta)
    if old_create is not None:
        old_create["name"] = new_name
        for k in ("type", "a", "b", "flip", "offset", "angle", "limits", "values"):
            if k in edit_cmd:
                old_create[k] = edit_cmd[k]
    return {"joint": r, "anchors": links.record(ws, doc, new_name, old_create)["sides"]}


# Assembly constraints (SolidCraft assembly.constraint.create, #88): a rule between a reference on each part
# (mate, flush, distance, concentric, insert, parallel, perpendicular, angle, tangent, point_on_axis).
# SolidCraft keeps each one as a joint of the kind it needs, so links.record and check_joints follow it like
# a joint; links.repair recreates it through assembly.constraint.create.
CONSTRAINT_TYPES = ("mate", "flush", "distance", "concentric", "insert", "parallel", "perpendicular", "angle",
                    "tangent", "point_on_axis")


def add_constraint(ws, doc, params: dict) -> dict:
    """Create a constraint via SolidCraft assembly.constraint.create and record both side anchors."""
    resolved = links.resolve_occurrences(doc.session, params)
    r = doc.session.cmd("assembly.constraint.create", resolved)
    name = r.get("name") or resolved.get("name")
    anchors = links.record(ws, doc, name, dict(resolved, name=name, constraint=True))
    return {"constraint": r, "name": name, "anchors": anchors["sides"]}


def edit_constraint(ws, doc, constraint: str, params: dict) -> dict:
    """Change a constraint's rule, gap, angle, facing, name or suppression (assembly.constraint.edit) and record
    its anchors again. Its references stay; to pick new ones, delete it and add a new one."""
    meta = doc.metadata()
    joints_meta = meta.get("joints", {})
    old_data = joints_meta.get(constraint) if isinstance(joints_meta.get(constraint), dict) else {}
    old_create = dict(old_data["create"]) if isinstance(old_data.get("create"), dict) else None
    r = doc.session.cmd("assembly.constraint.edit", dict(params, constraint=constraint))
    new_name = params.get("name", constraint)
    if new_name != constraint and constraint in joints_meta:
        joints_meta[new_name] = joints_meta.pop(constraint)
        doc.set_metadata(meta)
    if old_create is not None:
        old_create["name"] = new_name
        for k in ("type", "offset", "angle", "flip"):
            if k in params:
                old_create[k] = params[k]
    return {"constraint": r, "name": new_name, "anchors": links.record(ws, doc, new_name, old_create)["sides"]}


def _circle_from_edge(e: dict):
    """If edge e is a circle or circular arc, return (radius, center, edge). Otherwise None."""
    a, m, b = e.get("start"), e.get("mid"), e.get("end")
    if not (a and m and b and "length" in e):
        return None
    length = e["length"]
    chord = g.norm(g.sub(b, a))
    if abs(chord - length) < 1e-6:
        return None  # straight line
    if chord < 1e-5:
        # Full closed circle where start and end coincide; mid is opposite to start
        center = g.scale(g.add(a, m), 0.5)
        radius = g.norm(g.sub(m, center))
        if radius > 1e-4 and abs(2.0 * math.pi * radius - length) / max(length, 1e-6) < 0.05:
            return (radius, center, e)
        return None
    v1 = g.sub(m, a)
    v2 = g.sub(b, a)
    w = g.cross(v1, v2)
    w2 = g.dot(w, w)
    if w2 < 1e-12:
        return None
    term1 = g.scale(g.cross(v2, w), g.dot(v1, v1))
    term2 = g.scale(g.cross(w, v1), g.dot(v2, v2))
    offset = g.scale(g.add(term1, term2), 1.0 / (2.0 * w2))
    center = g.add(a, offset)
    radius = g.norm(offset)
    if radius < 1e-4:
        return None
    ua = g.scale(g.sub(a, center), 1.0 / radius)
    um = g.scale(g.sub(m, center), 1.0 / radius)
    ub = g.scale(g.sub(b, center), 1.0 / radius)
    cos_am = max(-1.0, min(1.0, g.dot(ua, um)))
    cos_mb = max(-1.0, min(1.0, g.dot(um, ub)))
    angle = math.acos(cos_am) + math.acos(cos_mb)
    arc_len = radius * angle
    if abs(arc_len - length) / max(length, 1e-6) < 0.05:
        return (radius, center, e)
    return None


def centred_hole_commands(doc, params: dict) -> list[dict]:
    """A hole in the middle of the clicked planar face that stays there (design intent rule): on a face with
    two opposite straight edges, a sketch with a construction line between their midpoints; on a circular face
    (cylinder, flange, ring), a sketch with the largest circular edge projected and the hole centre concentric
    to it. params: the hole's (solid.hole), with position on the face and direction into it, plus centre: true."""
    pos, direction = params.get("position"), params.get("direction")
    if not (isinstance(pos, list) and len(pos) == 3 and isinstance(direction, list) and len(direction) == 3):
        raise ValueError("a centred hole needs a clicked face (position and direction)")
    pos, n = [float(c) for c in pos], g.unit([-float(c) for c in direction])
    face, body, face_edges = None, None, []
    for b in doc.session.cmd("document.inspect").get("bodies", []):
        name = b.get("name") if isinstance(b, dict) else b
        for f in doc.session.cmd("model.faces", {"body": name}).get("faces", []):
            pn = f.get("plane_normal")
            if pn and g.dot(g.unit(pn), n) > 0.999 and abs(g.dot(g.sub(pos, f["point"]), n)) < 1e-4:
                edges = [e for e in doc.session.cmd("model.edges", {"body": name}).get("edges", [])
                         if g.edge_touches(e["name"], f["name"])]
                if edges:
                    pts = [e[k] for e in edges for k in ("start", "end")]
                    lo = [min(p[i] for p in pts) - 1e-4 for i in range(3)]
                    hi = [max(p[i] for p in pts) + 1e-4 for i in range(3)]
                    for e in edges:
                        circ = _circle_from_edge(e)
                        if circ:
                            r_c, c_c, _ = circ
                            for i in range(3):
                                span = r_c * math.sqrt(max(0.0, 1.0 - n[i] ** 2))
                                lo[i] = min(lo[i], c_c[i] - span - 1e-4)
                                hi[i] = max(hi[i], c_c[i] + span + 1e-4)
                    if all(lo[i] <= pos[i] <= hi[i] for i in range(3)):
                        face, body, face_edges = f, name, edges
                        break
        if face:
            break
    if face is None:
        raise ValueError("no planar face at the clicked point")

    names = {f.get("name") for f in doc.session.cmd("document.inspect").get("timeline", [])}
    k = 1
    while f"Hole centre {k}" in names:
        k += 1
    sketch = f"Hole centre {k}"
    hole = {key: v for key, v in params.items() if key not in ("centre", "position", "references")}
    hole.update({"sketch": sketch, "points": ["c"]})

    lines = [e for e in face_edges if abs(g.norm(g.sub(e["end"], e["start"])) - e["length"]) < 1e-6]
    best = None
    for i, a in enumerate(lines):
        da = g.unit(g.sub(a["end"], a["start"]))
        for b in lines[i + 1:]:
            db = g.unit(g.sub(b["end"], b["start"]))
            if abs(abs(g.dot(da, db)) - 1) < 1e-6:
                gap = g.norm(g.sub(g.sub(b["mid"], a["mid"]), g.scale(da, g.dot(g.sub(b["mid"], a["mid"]), da))))
                if gap > 1e-6 and (best is None or a["length"] + b["length"] > best[0]):
                    best = (a["length"] + b["length"], a, b, da)
    if best is not None:
        _, ea, eb, xd = best
        yd = g.cross(n, xd)
        origin = g.add(pos, g.scale(n, -g.dot(g.sub(pos, face["point"]), n)))
        uv = lambda q: [round(g.dot(g.sub(q, origin), xd), 6), round(g.dot(g.sub(q, origin), yd), 6)]
        ma, mb = uv(ea["mid"]), uv(eb["mid"])
        mid = [(ma[0] + mb[0]) / 2, (ma[1] + mb[1]) / 2]
        return [
            {"command": "sketch.create", "params": {"plane": {"origin": origin, "x_dir": xd, "y_dir": yd}, "name": sketch}},
            {"command": "sketch.project", "params": {"refs": [{"edge": ea["mid"], "body": body}, {"edge": eb["mid"], "body": body}]}},
            {"command": "sketch.line", "params": {"points": [ma, mb], "ids": ["axis"]}},
            {"command": "sketch.construction", "params": {"curves": ["axis"]}},
            {"command": "sketch.constraint.midpoint", "params": {"point": "axis.start", "line": "l1"}},
            {"command": "sketch.constraint.midpoint", "params": {"point": "axis.end", "line": "l2"}},
            {"command": "sketch.point", "params": {"point": mid, "id": "c", "connect": False}},
            {"command": "sketch.constraint.midpoint", "params": {"point": "c", "line": "axis"}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.hole", "params": hole},
        ]

    circles = [_circle_from_edge(e) for e in face_edges]
    circles = [c for c in circles if c is not None]
    if circles:
        # Largest circular edge of the face (the outer edge on a ring)
        best_circ = max(circles, key=lambda c: (round(c[0], 6), round(c[2]["length"], 6), c[2]["name"]))
        circ_radius, circ_center, circ_edge = best_circ
        xd = g.unit(g.sub(circ_edge["mid"], circ_center))
        yd = g.cross(n, xd)
        origin = g.add(pos, g.scale(n, -g.dot(g.sub(pos, face["point"]), n)))
        uv = lambda q: [round(g.dot(g.sub(q, origin), xd), 6), round(g.dot(g.sub(q, origin), yd), 6)]
        mid = uv(circ_center)
        return [
            {"command": "sketch.create", "params": {"plane": {"origin": origin, "x_dir": xd, "y_dir": yd}, "name": sketch}},
            {"command": "sketch.project", "params": {"refs": [{"edge": circ_edge["mid"], "body": body}]}},
            {"command": "sketch.point", "params": {"point": mid, "id": "c", "connect": False}},
            {"command": "sketch.constraint.concentric", "params": {"a": "a1", "b": "c"}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.hole", "params": hole},
        ]

    raise ValueError("the middle of this face needs two opposite straight edges or a circular edge")
