"""Local HTTP server (127.0.0.1) and data collection functions for the Mechvane Web-UI."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, unquote, urlparse
import zipfile

from .. import geometry as g
from .. import bolted, design_rules, hole_tables, install, step_import, links, modeling, query, sc_errors, sc_locate, sketch_rule, speech, standard_parts, tree
from . import agent as agent_mod, selection, sessionlog, sketch_session, webapp
from .. import METADATA_KEY, read_metadata
from ..documents import ASSEMBLY, PART, Workspace, _validate_name
from ..solidcraft import Session
from .mesh import collect_mesh

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_UPLOAD = 64 * 1024 * 1024

_JOINT_PRIO = ("joint_missing", "file_missing", "face_missing", "origin_lost", "moved", "unverifiable", "ok")


def _joint_severity(status: str) -> str:
    if status == "ok":
        return "ok"
    if status in ("moved", "unverifiable"):
        return "warn"
    return "fail"


def _pick_joint_status(entries: list[dict]) -> str:
    if not entries:
        return "ok"
    statuses = {e.get("status", "ok") for e in entries}
    for p in _JOINT_PRIO:
        if p in statuses:
            return p
    return next(iter(statuses))


def collect_about() -> dict:
    """Return package and SolidCraft version info."""
    from .. import __version__, install
    return {
        "mechvane": __version__,
        "solidcraft": install.VERSION,
    }


def collect_version(doc) -> dict:
    """Return file mtime and basic document info."""
    mtime = doc.path.stat().st_mtime
    return {
        "version": mtime,
        "mtime": mtime,
        "name": doc.name,
        "kind": doc.kind,
        "path": str(doc.path),
    }


def collect_tree(ws, doc) -> dict:
    """Return the model browser tree; for assemblies, enrich joints with status from links.check."""
    if doc.kind == PART:
        return tree.part_tree(doc.session, groups=True)

    t = tree.assembly_tree(doc.session, groups=True, base=doc.path.parent)
    checks = links.check(ws, doc)
    by_joint = {}
    for c in checks:
        by_joint.setdefault(c["joint"], []).append(c)

    status_map = {jname: _pick_joint_status(entries) for jname, entries in by_joint.items()}

    def _enrich_occ(occ):
        for j in occ.get("joints", []):
            j["status"] = status_map.get(j["name"], "ok")
            j["severity"] = _joint_severity(j["status"])
        for ch in occ.get("occurrences", []):
            _enrich_occ(ch)

    for occ in t.get("occurrences", []):
        _enrich_occ(occ)

    rels = t.get("groups", {}).get("relations", [])
    for r in rels:
        r["status"] = status_map.get(r["name"], "ok")
        r["severity"] = _joint_severity(r["status"])

    t["joints"] = [
        {
            "name": r["name"],
            "type": r["type"],
            "between": r["between"],
            "status": r["status"],
            "severity": r["severity"],
        }
        for r in rels
    ]
    t["joint_checks"] = checks
    conns = bolted.list_bolted_connections(ws, doc.name).get("connections") or {}
    t["bolted_connections"] = [_bolted_item_dict(cid, c) for cid, c in conns.items()]
    return t


def _match_assembly_face(doc, occ_name: str, origin, z) -> tuple[str | None, str | None]:
    if not occ_name or origin is None or z is None:
        return None, None
    try:
        targets = query._collect_bodies(doc, {"occurrence": occ_name})
        for bt in targets:
            wname = bt["world_name"]
            faces = doc.session.cmd("model.faces", {"body": wname}).get("faces", [])
            for f in faces:
                f.setdefault("body", wname)
            m = links._match(faces, origin, z)
            if m and m.get("face"):
                return wname, m["face"]
    except Exception:
        pass
    return None, None


def _add_selections(doc, findings):
    """Give each finding with a face a `select` item for the SolidCraft app's `select.set`
    ({type: face, body, index, point}), so clicking it in the "Model" mode selects that face."""
    faces = {}

    def body_faces(body):
        if body not in faces:
            try:
                faces[body] = doc.session.cmd("model.faces", {"body": body}).get("faces", [])
            except Exception:
                faces[body] = []
        return faces[body]

    all_bodies = None
    for item in findings:
        loc = item.get("location") or {}
        name = loc.get("assembly_face") or item.get("face")
        if not name:
            continue
        if item.get("body"):
            bodies = [item["body"]]
        else:
            if all_bodies is None:
                try:
                    all_bodies = [b["world_name"] for b in query._collect_bodies(doc, {})]
                except Exception:
                    all_bodies = []
            bodies = all_bodies
        for body in bodies:
            f = next((f for f in body_faces(body) if f.get("name") == name), None)
            if f:
                item["select"] = {"type": "face", "body": body, "index": f["index"],
                                  "point": f.get("point") or f.get("centroid")}
                break


PARAM_KEYS = (
    "name", "expression", "unit", "value", "source", "feature", "sketch",
    "input", "comment", "favorite", "error", "uses", "used_by"
)


def _sketch_param_owners(session) -> dict[str, str]:
    """Map sketch dimension parameter names to the sketch feature that owns each."""
    owners = {}
    try:
        insp = session.cmd("document.inspect", {"measure": False})
        for sk in insp.get("sketches", []):
            name = sk.get("name")
            if not name:
                continue
            try:
                sk_insp = session.cmd("sketch.inspect", {"sketch": name})
                for c in sk_insp.get("constraints", []):
                    p = c.get("param")
                    if p:
                        owners[p] = name
            except Exception:
                pass
    except Exception:
        pass
    return owners


def _is_named_dimension(p: dict) -> bool:
    """Whether a sketch parameter is a named dimension rather than an auto-generated 'd1'."""
    name = p.get("name") or ""
    # In SolidCraft auto-generated dimension parameters are 'd' followed by digits
    if not re.match(r"^d\d+$", name):
        return True
    if p.get("uses") or (p.get("expression") and re.match(r"^[A-Za-z_]\w*$", str(p.get("expression")))):
        return True
    return False


def collect_params(doc) -> dict:
    """The document's parameters for the form: user parameters first, then sketch and feature dimensions."""
    listed = doc.session.cmd("parameters.list", {})
    owners = _sketch_param_owners(doc.session)
    params = []
    for raw in listed.get("parameters", []):
        p = {k: raw.get(k) for k in PARAM_KEYS if k in raw}
        if p.get("source") == "sketch":
            p["sketch"] = owners.get(p.get("name")) or "Sketch"
        params.append(p)

    def sort_key(p):
        src = p.get("source")
        fav = not p.get("favorite")
        if src == "user":
            return (0, fav, p.get("name", ""))
        if src == "sketch":
            sketch_name = p.get("sketch", "")
            named = not _is_named_dimension(p)
            return (1, sketch_name, named, p.get("name", ""))
        feature_name = p.get("feature", "")
        return (2, feature_name, fav, p.get("name", ""))

    params.sort(key=sort_key)
    return {"parameters": params}


def change_params(doc, changes: dict) -> dict:
    """Set several parameters at once (all or nothing in SolidCraft) and save the document."""
    result = doc.session.cmd("parameters.change", {"changes": changes})
    doc.save()
    out = dict(collect_params(doc), changed=result.get("changed", {}))
    if result.get("errors"):
        out["errors"] = result["errors"]
    return out


def _num(v) -> str:
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def _edges_label(params) -> str:
    n = len(params.get("edges") or [])
    return f"{n} edge" + ("" if n == 1 else "s")


# Commands the workspace's own dialogs may send (ADR 0005, 2), each with the label of the step in the
# undo list. Everything else stays with the agent and the expert mode.
def _hole_label(p) -> str:
    # create params carry the type at the top, an edit (the feature's definition) under "hole"
    kind = {"counterbore": "Counterbored hole", "countersink": "Countersunk hole"}.get(
        p.get("type") or (p.get("hole") or {}).get("type"), "Hole")
    size = f"{p['thread']} tapped" if p.get("thread") else f"Ø{_num(p.get('diameter'))}"
    return f"{kind} {size}" + (f", {_num(p['depth'])} deep" if p.get("depth") not in (None, "") else ", through all")


def _op_label(p) -> str:
    return {"cut": "Cut: ", "intersect": "Intersect: ", "new": "New body: ", "new_body": "New body: "}.get(
        p.get("operation"), "")


def _features_label(p) -> str:
    names = [str(f) for f in p.get("features") or []]
    return ", ".join(names[:3]) + (" …" if len(names) > 3 else "") if names else "features"


def _pattern_label(kind):
    def label(p):
        q = p.get("pattern") or p  # an edit carries the values under "pattern"
        n = q.get("count1", q.get("count"))
        n2 = f" x {_num(q['count2'])}" if q.get("count2") else ""
        return f"{kind} pattern of {_features_label(p)}" + (f", {_num(n)}{n2}" if n is not None else "")
    return label


def _sketch_label(p) -> str:
    shapes = p.get("shapes") or []
    counts = [(k, sum(1 for sh in shapes if sh.get("type") == k)) for k in ("rectangle", "circle")]
    what = ", ".join(f"{n} {k}" + ("s" if n > 1 else "") for k, n in counts if n)
    where = p.get("plane") if isinstance(p.get("plane"), str) else "a face"
    return f"Sketch on {where}: {what}"


def sketch_commands(doc, params: dict) -> dict:
    """mechvane.sketch: a sketch on a plane or face with rectangles and circles, each dimensioned
    (size and distance of its corner or centre from the sketch origin), so it is fully defined and its
    sizes are parameters. Runs step by step (the curve ids come from each reply), all or nothing."""
    s = doc.session
    plane = params.get("plane")
    plane = {"face": plane["face"]} if isinstance(plane, dict) and "face" in plane else plane
    if plane not in ("XY", "XZ", "YZ") and not isinstance(plane, dict):
        raise ValueError("plane: XY, XZ, YZ or {face: [x, y, z]}")
    shapes = params.get("shapes") or []
    if not shapes:
        raise ValueError("draw at least one rectangle or circle")
    cp = s.cmd("edit.checkpoint").get("checkpoint")
    try:
        made = s.cmd("sketch.create", sketch_session.create_params(
            plane, project_edges=bool(params.get("project_edges", False))))
        for sh in shapes:
            x, y = sh.get("x", 0), sh.get("y", 0)
            if sh.get("type") == "rectangle":
                w, h = sh.get("w"), sh.get("h")
                fx = lambda v: float(v) if isinstance(v, (int, float)) else 10.0  # noqa: E731
                # connect: false: no automatic coincidence with the origin, the dimensions place it
                r = s.cmd("sketch.rectangle.two_point", {"p0": [fx(x), fx(y)], "p1": [fx(x) + fx(w), fx(y) + fx(h)],
                                                         "connect": False})
                bottom, left, corner = r["sides"]["bottom"], r["sides"]["left"], r["corners"]["bottom_left"]
                dims = [({"entities": [bottom], "type": "length"}, w), ({"entities": [left], "type": "length"}, h),
                        ({"entities": ["origin", corner], "type": "distance_x"}, x),
                        ({"entities": ["origin", corner], "type": "distance_y"}, y)]
            elif sh.get("type") == "circle":
                d = sh.get("d")
                r = s.cmd("sketch.circle.center", {"center": [float(x) if isinstance(x, (int, float)) else 0.0,
                                                              float(y) if isinstance(y, (int, float)) else 0.0],
                                                   "diameter": float(d) if isinstance(d, (int, float)) else 10.0,
                                                   "connect": False})
                circle = r["created"]["curves"][0]
                center = next(pt for pt in r["created"]["points"] if pt.endswith("center"))
                dims = [({"entities": [circle], "type": "diameter"}, d),
                        ({"entities": ["origin", center], "type": "distance_x"}, x),
                        ({"entities": ["origin", center], "type": "distance_y"}, y)]
            else:
                raise ValueError(f"unknown shape: {sh.get('type')}")
            for spec, value in dims:
                # a sketch dimension has no sign (SolidCraft refuses -20): the shape is already drawn on the
                # negative side, so the distance is its size; expressions stay as they are
                if isinstance(value, (int, float)):
                    value = abs(value)
                s.cmd("sketch.dimension", {**spec, "value": value})
        s.cmd("sketch.finish", {})
    except Exception:
        s.cmd("edit.restore_checkpoint", {"checkpoint": cp})
        raise
    s.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
    name = next((f["name"] for f in reversed(_timeline(doc)) if f["type"] == "Sketch"), None)
    return {"results": [{"name": name, "sketch": made.get("sketch")}]}


def sketch_plane(doc, plane) -> dict:
    """The frame of a sketch plane (origin, x_dir, y_dir in world coordinates) without leaving a sketch:
    the dialog draws the shapes on it before anything is made."""
    plane = {"face": plane["face"]} if isinstance(plane, dict) and "face" in plane else plane
    cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
    try:
        doc.session.cmd("sketch.create", sketch_session.create_params(plane, project_edges=False))
        frame = doc.session.cmd("sketch.inspect", {}).get("plane") or {}
    finally:
        doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp})
        try:
            doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
        except Exception:
            pass
    return {k: frame.get(k) for k in ("origin", "x_dir", "y_dir")}


FEATURE_COMMANDS = {
    "mechvane.sketch": _sketch_label,
    "solid.fillet": lambda p: f"Fillet R{_num(p.get('radius'))} on {_edges_label(p)}",
    "solid.chamfer": lambda p: f"Chamfer {_num(p.get('distance'))} on {_edges_label(p)}",
    "solid.hole": _hole_label,
    "solid.pattern.rectangular": _pattern_label("Rectangular"),
    "solid.pattern.circular": _pattern_label("Circular"),
    "solid.mirror": lambda p: f"Mirror {_features_label(p)}",
    "solid.extrude": lambda p: f"{_op_label(p)}Extrude {p.get('sketch', '')}"
                               + (", through all" if (p.get("extent") or p).get("through_all") else
                                  f", {_num((p.get('extent') or p).get('distance'))}"),
    "solid.revolve": lambda p: f"{_op_label(p)}Revolve {p.get('sketch', '')}"
                               + (f", {_num(p['angle'])}" if p.get("angle") is not None else ""),
}


def hole_sizes() -> dict:
    """Metric sizes for the Hole dialog from Mechvane's tables: ISO 273 clearance (close, normal, loose),
    DIN 336 tap drill, DIN 974-1 counterbore (ISO 4762 screw, no washer), DIN 74 countersink."""
    out = {}
    for size in sorted(hole_tables.ISO_273, key=lambda m: float(m[1:])):
        entry = {"clearance": {fit: hole_tables.clearance_hole(size, fit) for fit in ("close", "normal", "loose")},
                 "tap_drill": hole_tables.tap_drill(size), "counterbore": hole_tables.counterbore(size)}
        try:
            entry["countersink"] = hole_tables.countersink(size)
        except (KeyError, ValueError):
            pass
        out[size] = entry
    return {"sizes": out, "sources": {"clearance": "ISO 273", "tap_drill": "DIN 336", "counterbore": "DIN 974-1",
                                      "countersink": "DIN 74-F"}}


# Features a dialog can open again from the model browser: type → (dialog, the command that made it)
EDITABLE = {
    "FilletFeature": ("fillet", "solid.fillet"),
    "ChamferFeature": ("chamfer", "solid.chamfer"),
    "HoleFeature": ("hole", "solid.hole"),
    "RectangularPatternFeature": ("rectangular", "solid.pattern.rectangular"),
    "CircularPatternFeature": ("circular", "solid.pattern.circular"),
    "MirrorFeature": ("mirror", "solid.mirror"),
    "ExtrudeFeature": ("extrude", "solid.extrude"),
    "RevolveFeature": ("revolve", "solid.revolve"),
}


CURVE_KEYS = ("id", "type", "start_at", "end_at", "center_at", "radius", "construction")


def sketch_shapes(session, name: str) -> dict:
    """What the workspace draws of a sketch outside the sketch environment (unused sketches, the profiles to
    click in Extrude and Revolve): its plane, curves in sketch coordinates and the closed regions, each with the
    curve ids of its outline and of its holes (index as solid.extrude's profiles)."""
    try:
        insp = session.cmd("sketch.inspect", {"sketch": name})
    except Exception:
        return {"profiles": [], "plane": None, "curves": []}
    profiles = [{"index": p["index"], "area": round(p["area_mm2"], 1), "curves": p["curves"],
                 "holes": len(p.get("holes") or []), "hole_loops": p.get("holes") or []}
                for p in insp.get("profiles", [])]
    curves = [{k: c[k] for k in CURVE_KEYS if k in c} for c in insp.get("curves", [])]
    return {"profiles": profiles, "plane": insp.get("plane"), "curves": curves}


def sketches(doc) -> dict:
    """The part's sketches for Extrude and Revolve (oldest first), with what already uses each."""
    if doc.kind != PART:
        return {"sketches": []}
    used = sketch_rule.consumers(doc.session)
    try:
        insp = doc.session.cmd("document.inspect", {"measure": False, "sketches": True})
        vis_map = {sk["name"]: sk.get("visible", True) for sk in insp.get("sketches", [])}
        tl = insp.get("timeline", [])
    except (RuntimeError, KeyError, AttributeError):
        vis_map = {}
        tl = _timeline(doc)
    out = []
    for f in tl:
        if f["type"] != "Sketch":
            continue
        name = f["name"]
        vis = vis_map.get(name, not bool(used.get(name)))
        out.append({"name": name, "visible": vis, "used_by": sorted(used.get(name) or []), **sketch_shapes(doc.session, name)})
    return {"sketches": out}


def _timeline(doc) -> list[dict]:
    return doc.session.cmd("document.inspect", {"measure": False}).get("timeline", [])


def _errors(doc) -> dict:
    return {f["name"]: f["error"] for f in _timeline(doc) if f.get("error")}


def _broken_by_edit(new: dict, out: dict) -> Exception:
    """The error for an edit that leaves later features failing: each with the place where it fails."""
    found = {b["feature"]: b for b in out.get("feature_errors") or []}
    first = next((found[k] for k in new if found.get(k, {}).get("where")), None)
    text = "; ".join(f"{k} would fail: {found.get(k, {}).get('where') or v}" for k, v in new.items())
    location = dict(first["location"], text=text, kind="feature") if first else None
    return sc_errors.ExplainedError(text, None, location)


def is_centred_hole(doc, definition: dict) -> bool:
    """Whether a hole feature was placed with 'Middle of face' (centred_hole_commands):
    it references a sketch that has either an axis construction line for centering between
    opposite edges, or a circular/arc edge for concentric placement."""
    points = definition.get("points")
    sketch_ref = points.get("sketch") if isinstance(points, dict) else definition.get("sketch")
    if not sketch_ref:
        return False
    try:
        sk = doc.session.cmd("sketch.inspect", {"sketch": sketch_ref})
    except Exception:
        return False
    name = sk.get("name", "")
    if name.startswith("Hole centre"):
        return True
    has_axis = any(c.get("id") == "axis" and c.get("construction") for c in sk.get("curves", []))
    if has_axis and any(k.get("type") == "midpoint" for k in sk.get("constraints", [])):
        return True
    has_arc = any(c.get("type") == "arc" for c in sk.get("curves", []))
    has_c = any(p.get("id") == "c" for p in sk.get("points", []))
    if has_arc and has_c:
        return True
    return False


def feature_for_edit(doc, name: str, tmp_dir) -> dict:
    """What a dialog needs to edit a feature, Inventor style: its values, and the model as it was just
    before the feature (the edges a fillet consumed can be picked again there)."""
    if doc.kind != PART:
        raise PermissionError("features are edited in a part")
    timeline = _timeline(doc)
    at = next((i for i, f in enumerate(timeline) if f["name"] == name), None)
    if at is None:
        raise KeyError(name)
    if timeline[at]["type"] not in EDITABLE:
        raise PermissionError(f"{name} ({timeline[at]['type']}) cannot be edited in the workspace yet; "
                              "use File → Open in SolidCraft")
    info = doc.session.cmd("timeline.inspect", {"feature": name})
    cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
    try:
        doc.session.cmd("timeline.roll_to", {"position": at})
        before = collect_mesh(doc, tmp_dir=tmp_dir)
    finally:
        doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp})
        try:
            doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
        except Exception:
            pass
    # patterns and mirrors name their features by id: the dialog shows and sends names
    names = {str(f["id"]): f["name"] for f in timeline}
    # the type from the timeline: timeline.inspect's `type` is "chamfer" since SolidCraft 0.30 ("ChamferFeature"
    # moved to `type_name`), the timeline keeps the class name
    kind = timeline[at]["type"]
    defn = info.get("definition") or {}
    if kind == "HoleFeature" and is_centred_hole(doc, defn):
        defn["centre"] = True
    return {"name": name, "type": kind, "dialog": EDITABLE[kind][0],
            "definition": defn, "before": before, "feature_names": names}


def delete_feature(srv, doc, name: str, keep_sketch: bool = False) -> dict:
    """Delete a feature from the model browser, with the sketch it owns (as the agent's delete_feature).
    When keep_sketch is True, only the feature is deleted and its consumed sketch is kept."""
    if doc.kind != PART:
        raise PermissionError("features are deleted in a part")
    if name not in {f["name"] for f in _timeline(doc)}:
        raise KeyError(name)

    def apply():
        failing_before = _errors(doc)
        if keep_sketch:
            doc.session.cmd("timeline.delete", {"features": [name]})
            out = {"deleted": [name], "kept": []}
        else:
            out = sketch_rule.delete_with_owned(doc.session, name)
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        out["failing"] = {k: v for k, v in _errors(doc).items() if k not in failing_before}
        return out

    out = srv.agent.hand_step(f"Delete {name} in {doc.name}", apply)
    return {"done": f"Deleted {', '.join(out['deleted'])}", **out}


def rename_feature(srv, doc, feature: str, name: str) -> dict:
    """Rename a feature or sketch from the model browser (as the agent's rename_feature)."""
    if doc.kind != PART:
        raise PermissionError("features are renamed in a part")
    name = (name or "").strip()
    if not name or len(name) > 128:
        raise ValueError("`name` must be 1…128 characters")
    tl = _timeline(doc)
    existing = {f["name"] for f in tl}
    if feature not in existing:
        raise KeyError(feature)
    if name in existing and name != feature:
        raise ValueError(f"another feature is called `{name}`")

    def apply():
        r = doc.session.cmd("timeline.rename", {"feature": feature, "name": name})
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        return r

    out = srv.agent.hand_step(f"Rename {feature} to {name} in {doc.name}", apply)
    return {"done": f"Renamed {feature} to {name}", "feature": feature, "name": name, "result": out}
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
    to it. params: the hole's, with position on the face and direction into it (the dialog's), plus centre: true."""
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


def run_feature(srv, doc, command: str, params: dict, preview: bool, tmp_dir, edit: str | None = None) -> dict:
    """Run one dialog command in the open part. preview: run it, return the mesh, take it back
    (nothing saved). Otherwise run, save, and record the step for Undo. With edit (a feature name) the
    feature is changed in place (timeline.edit) instead of a new one added."""
    if command not in FEATURE_COMMANDS:
        raise PermissionError(f"command not available in the workspace: {command}")
    if doc.kind != PART:
        raise PermissionError("features are added in a part; open the part file")
    commands = [{"command": command, "params": params}]
    if command == "solid.hole" and params.get("centre") and edit is None:
        commands = centred_hole_commands(doc, params)
    if command == "mechvane.sketch":
        if preview or edit is not None:
            raise PermissionError("a sketch is drawn in the dialog and made with OK")

        def apply_sketch():
            out = sketch_commands(doc, params)
            doc.save()
            srv.mtime = doc.path.stat().st_mtime
            return out

        out = srv.agent.hand_step(f"{_sketch_label(params)} in {doc.name}", apply_sketch)
        return {"done": f"{_sketch_label(params)}", "results": out["results"]}
    if edit is not None:
        kind = next((f["type"] for f in _timeline(doc) if f["name"] == edit), None)
        if kind is None:
            raise KeyError(edit)
        if EDITABLE.get(kind, (None, None))[1] != command:
            raise PermissionError(f"{edit} ({kind}) is not edited with {command}")
        set_ = dict(params)
        # the dialog sends feature and sketch names, the definition keeps ids (a sketch only as id)
        ids = {f["name"]: f["id"] for f in _timeline(doc)}
        if isinstance(set_.get("features"), list):
            set_["features"] = [ids.get(f, f) for f in set_["features"]]
        if isinstance(set_.get("sketch"), str) and set_["sketch"] in ids:
            set_["sketch"] = ids[set_["sketch"]]
        if command == "solid.hole":
            set_.pop("centre", None)
            # SolidCraft takes no null for references (#111): "no references" is an empty list
            if "references" in set_ and set_["references"] is None:
                set_["references"] = []
            try:
                insp = doc.session.cmd("timeline.inspect", {"feature": edit})
                if is_centred_hole(doc, insp.get("definition") or {}):
                    set_.pop("position", None)
                    set_.pop("references", None)
                    set_.pop("direction", None)
            except Exception:
                pass
        commands = [{"command": "timeline.edit", "params": {"feature": edit, "set": set_}}]
    if preview:
        failing_before = _errors(doc) if edit else {}
        cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        try:
            out = modeling.run_commands(doc, commands)
            new = {k: v for k, v in _errors(doc).items() if k not in failing_before} if edit else {}
            if new:
                raise _broken_by_edit(new, out)
            return {"preview": True, "delta": out.get("delta"), "mesh": collect_mesh(doc, tmp_dir=tmp_dir)}
        finally:
            # back to the checkpoint (forget alone would drop it without going back), then drop it
            doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp})
            try:
                doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
            except Exception:
                pass

    def apply():
        failing_before = _errors(doc) if edit else {}
        cp = doc.session.cmd("edit.checkpoint").get("checkpoint") if edit else None
        out = modeling.run_commands(doc, commands)
        if edit:
            # an edit that leaves a feature failing is refused: back to how it was, nothing saved
            new = {k: v for k, v in _errors(doc).items() if k not in failing_before}
            if new:
                doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp})
                raise _broken_by_edit(new, out)
            doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        return out

    label = f"{FEATURE_COMMANDS[command](params)} in {doc.name}"
    if edit:
        label = f"Edit {edit}: {label}"
    out = srv.agent.hand_step(label, apply)
    return {"done": label, "delta": out.get("delta"), "results": out.get("results")}


def _vec3_or_zero(val, xyz_fallback) -> list[float]:
    """Parse a 3D vector from [x, y, z], {x, y, z}, or three separate scalars."""
    if isinstance(val, (list, tuple)):
        if len(val) != 3:
            raise ValueError("expected a 3-element vector [x, y, z]")
        return [float(val[0]), float(val[1]), float(val[2])]
    if isinstance(val, dict):
        return [float(val.get("x", 0.0)), float(val.get("y", 0.0)), float(val.get("z", 0.0))]
    if val is None:
        return [float(c if c not in (None, "") else 0.0) for c in xyz_fallback]
    raise ValueError("expected [x, y, z] or {x, y, z}")


def _euler_xyz_matrix(rx_deg: float, ry_deg: float, rz_deg: float):
    """4x4 row-vector rotation matrix for extrinsic X -> Y -> Z Euler angles in degrees."""
    rx, ry, rz = math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    mx = [[1.0, 0.0, 0.0, 0.0], [0.0, cx, sx, 0.0], [0.0, -sx, cx, 0.0], [0.0, 0.0, 0.0, 1.0]]
    my = [[cy, 0.0, -sy, 0.0], [0.0, 1.0, 0.0, 0.0], [sy, 0.0, cy, 0.0], [0.0, 0.0, 0.0, 1.0]]
    mz = [[cz, sz, 0.0, 0.0], [-sz, cz, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    return g.mat_mul(mz, g.mat_mul(my, mx))


def _parse_optional_bool(val):
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        low = val.strip().lower()
        if low in ("true", "yes", "1"):
            return True
        if low in ("false", "no", "0"):
            return False
    raise ValueError("grounded must be true, false, or empty")


def assembly_insert(srv, doc, body: dict) -> dict:
    """Place a part or subassembly file into the open assembly via links.insert (shared undo list)."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    raw_path = body.get("part_path") or body.get("file") or body.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("file is required")
    p = Path(raw_path.strip())
    part_path = str(p if p.is_absolute() else (srv.folder_path / p))

    raw_name = body.get("name")
    if raw_name is not None and not isinstance(raw_name, str):
        raise ValueError("name must be a string")
    name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None

    t_vec = _vec3_or_zero(body.get("translate"), (body.get("tx"), body.get("ty"), body.get("tz")))
    translate = t_vec if any(abs(c) > 1e-12 for c in t_vec) else None

    rot_in = body.get("rotate")
    if isinstance(rot_in, dict) and "axis" in rot_in:
        rotate = rot_in
    elif isinstance(rot_in, (list, tuple)) and len(rot_in) in (2, 4, 16) and (
        len(rot_in) != 2 or not all(isinstance(x, (int, float)) for x in rot_in)
    ):
        rotate = rot_in
    else:
        r_vec = _vec3_or_zero(rot_in, (body.get("rx"), body.get("ry"), body.get("rz")))
        rotate = _euler_xyz_matrix(*r_vec) if any(abs(c) > 1e-12 for c in r_vec) else None

    grounded = _parse_optional_bool(body.get("grounded"))

    def apply():
        out = links.insert(srv.ws, doc, part_path, name=name, translate=translate, rotate=rotate, grounded=grounded)
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        return out

    label_name = name or Path(part_path).stem
    out = srv.agent.hand_step(f"Place {label_name} in {doc.name}", apply)
    comp_name = out.get("name") or out.get("occurrence_name") or label_name
    resp = dict(out)
    resp.setdefault("name", comp_name)
    resp["done"] = f"Placed {comp_name}"
    return resp


def _format_update_links_message(checked_joints: list[str], moved_joints: list[str],
                                 repaired: list[dict], updated_comps: list[str],
                                 warnings: list[dict]) -> str:
    n_checked = len(checked_joints)
    parts = [f"{n_checked} joint{'s' if n_checked != 1 else ''} checked"]
    if moved_joints:
        parts.append(f"moved: {', '.join(moved_joints)}")
    if repaired:
        ok_rep = [r["joint"] for r in repaired if r.get("status") != "failed"]
        bad_rep = [r["joint"] for r in repaired if r.get("status") == "failed"]
        if ok_rep:
            parts.append(f"repaired: {', '.join(ok_rep)}")
        if bad_rep:
            parts.append(f"repair failed: {', '.join(bad_rep)}")
    other_warn = sorted({w["joint"] for w in warnings if w.get("joint") and w.get("status") not in ("moved", "origin_lost")})
    if other_warn:
        parts.append(f"attention: {', '.join(other_warn)}")
    blocked = [w for w in warnings if w.get("status") == "link_blocked"]
    if blocked:
        # SolidCraft refused to read these parts again (a feature fails): their old bodies stay in the assembly
        names = ", ".join(f"{w['component']}" + (f" ({w['feature']} fails)" if w.get("feature") else "") for w in blocked)
        parts.append(f"not updated: {names}")
    if updated_comps:
        parts.append(f"updated {', '.join(updated_comps)}")
    return "; ".join(parts)


def assembly_update_links(srv, doc, repair: bool = False) -> dict:
    """Reload linked files and check recorded joints via links.update_links (shared undo list)."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")

    def apply():
        out = links.update_links(srv.ws, doc, repair_moved=repair)
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        return out

    label = f"{'Repair links' if repair else 'Update links'} in {doc.name}"
    out = srv.agent.hand_step(label, apply)
    report = out.get("joints") or []
    checked_joints = sorted({r["joint"] for r in report if r.get("joint")})
    moved_joints = sorted({r["joint"] for r in report if r.get("status") in ("moved", "origin_lost") and r.get("joint")})
    repaired = out.get("repaired") or []
    updated_comps = (out.get("update") or {}).get("updated") or []
    warnings = out.get("warnings") or []
    msg = _format_update_links_message(checked_joints, moved_joints, repaired, updated_comps, warnings)
    return dict(
        out,
        joint_count=len(checked_joints),
        checked_joints=checked_joints,
        moved_joints=moved_joints,
        message=msg,
        done=msg,
    )


JOINT_TYPES = ("rigid", "revolute", "slider", "cylindrical", "ball")


def _known_occurrences(doc) -> dict[str, str]:
    """Map every valid occurrence name or path in the assembly to its canonical path."""
    raw_occs = links._occurrences(doc.session)
    out: dict[str, str] = {}
    for o in raw_occs.values():
        path = o["path"]
        out[path] = path
        if o.get("name"):
            out.setdefault(o["name"], path)
    return out


def _resolve_canonical_occurrence(doc, occ: str, known: dict[str, str]) -> str:
    if occ in known:
        return known[occ]
    if f"{occ}:1" in known:
        return known[f"{occ}:1"]
    if "/" in occ:
        try:
            resolved = links.resolve_occurrences(doc.session, {"a": {"occurrence": occ}})["a"]["occurrence"]
        except ValueError:
            resolved = None
        if resolved and resolved in known:
            return known[resolved]
    valid = sorted(set(known.values()))
    raise ValueError(
        f"unknown component occurrence {occ!r}; choose from {', '.join(valid) if valid else 'none'}"
    )


def collect_assembly_context(ws, doc) -> dict:
    """Occurrences, world-body -> occurrence map, and existing joints for the Joint dialog."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    raw_occs = links._occurrences(doc.session)
    occurrences = [
        {
            "id": o["id"],
            "name": o["name"],
            "path": o["path"],
            "component": o["component"],
            "grounded": bool(o["grounded"]),
        }
        for o in raw_occs.values()
    ]
    by_id = {oid: o["path"] for oid, o in raw_occs.items()}
    body_occurrences = {
        b["world_name"]: b["occurrence"]
        for b in query._collect_bodies(doc, {})
        if b.get("world_name") and b.get("occurrence")
    }
    meta_joints = (doc.metadata() or {}).get("joints", {})
    jlist = doc.session.cmd("joint.list", {})
    try:
        jinsp = {
            j.get("name"): j
            for j in (doc.session.cmd("joint.inspect", {}).get("joints") or [])
            if isinstance(j, dict) and j.get("name")
        }
    except Exception:
        jinsp = {}
    joints = []
    for j in jlist.get("joints") or []:
        jname = j.get("name") or ""
        m = meta_joints.get(jname) or {}
        insp = jinsp.get(jname) or {}
        angle = insp.get("angle")
        if angle is None:
            angle = next((v.get("value") for v in (j.get("values") or []) if v.get("name") == "angle"), None)
        if angle is None and isinstance(m.get("create"), dict):
            angle = m["create"].get("angle", 0.0)
        if isinstance(angle, (int, float)):
            angle = round(float(angle), 6)
        joints.append({
            "name": jname,
            "type": j.get("type") or "rigid",
            "constraint": j.get("constraint"),
            "occurrence_a": by_id.get(j.get("a")) or (insp.get("a") or {}).get("path") or "",
            "occurrence_b": by_id.get(j.get("b")) or (insp.get("b") or {}).get("path") or "",
            "flip": bool(j.get("flip")),
            "offset": j.get("offset", 0.0),
            "angle": 0.0 if angle is None else angle,
            "frame_a": j.get("frame_a"),
            "frame_b": j.get("frame_b"),
            "anchors": m.get("sides") or {},
        })
    return {
        "occurrences": occurrences,
        "body_occurrences": body_occurrences,
        "joints": joints,
    }


def _vec3_numbers(val, field: str) -> list[float]:
    if not isinstance(val, (list, tuple)) or len(val) != 3:
        raise ValueError(f"{field} must be a list of three numbers [x, y, z]")
    out = []
    for c in val:
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(float(c)):
            raise ValueError(f"{field} must be a list of three numbers [x, y, z]")
        out.append(float(c))
    return out


def _validate_frame(val) -> dict:
    if not isinstance(val, dict) or "origin" not in val:
        raise ValueError("frame must be an object with origin: [x, y, z]")
    out = {"origin": _vec3_numbers(val.get("origin"), "frame.origin")}
    if val.get("z") is not None:
        out["z"] = _vec3_numbers(val.get("z"), "frame.z")
    if val.get("x") is not None:
        out["x"] = _vec3_numbers(val.get("x"), "frame.x")
    return out


def _joint_side_arg(raw, doc=None, known: dict[str, str] | None = None) -> tuple[dict, str]:
    if not isinstance(raw, dict):
        raise ValueError("joint side a and b must be objects")
    occ = raw.get("occurrence")
    if not isinstance(occ, str) or not occ.strip():
        raise ValueError("choose a component occurrence for each side")
    occ = occ.strip()
    if known is not None and doc is not None:
        canonical_occ = _resolve_canonical_occurrence(doc, occ, known)
    else:
        canonical_occ = occ
    out: dict = {"occurrence": occ}
    for k in ("face", "point", "z", "circle", "edge"):
        if raw.get(k) is not None:
            out[k] = _vec3_numbers(raw[k], k)
    if raw.get("plane") is not None:
        if raw["plane"] not in ("XY", "XZ", "YZ"):
            raise ValueError("plane must be 'XY', 'XZ', or 'YZ'")
        out["plane"] = raw["plane"]
    if raw.get("axis") is not None:
        if raw["axis"] not in ("X", "Y", "Z"):
            raise ValueError("axis must be 'X', 'Y', or 'Z'")
        out["axis"] = raw["axis"]
    if raw.get("frame") is not None:
        out["frame"] = _validate_frame(raw["frame"])
    if not any(k in out for k in ("face", "point", "circle", "edge", "plane", "axis", "frame")):
        raise ValueError(f"choose a face, edge, or origin on {out['occurrence']}")
    return out, canonical_occ


def _optional_scalar(val, field: str = "value") -> float | None:
    if val is None:
        return None
    if isinstance(val, bool):
        raise ValueError(f"{field} must be a number")
    if isinstance(val, (int, float)):
        f = float(val)
        if not math.isfinite(f):
            raise ValueError(f"{field} must be a finite number")
        return f
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            f = float(s.replace(",", "."))
        except ValueError as e:
            raise ValueError(f"{field} must be a number, got {val!r}") from e
        if not math.isfinite(f):
            raise ValueError(f"{field} must be a finite number")
        return f
    raise ValueError(f"{field} must be a number")


def _next_joint_name(doc, jtype: str) -> str:
    existing = {j.get("name") for j in (doc.session.cmd("joint.list", {}).get("joints") or []) if j.get("name")}
    existing.update(((doc.metadata() or {}).get("joints") or {}).keys())
    prefix = jtype.capitalize()
    idx = 1
    while f"{prefix}{idx}" in existing:
        idx += 1
    return f"{prefix}{idx}"


def assembly_add_joint(srv, doc, body: dict) -> dict:
    """Create a joint via modeling.add_joint (which uses links.record) on the shared undo list."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    known = _known_occurrences(doc)
    if len(set(known.values())) < 2:
        raise ValueError("place at least two components before creating a joint")
    jtype = str(body.get("type") or "rigid").strip().lower()
    if jtype not in JOINT_TYPES:
        raise ValueError(f"unsupported joint type {jtype!r}; choose from {', '.join(JOINT_TYPES)}")
    side_a, occ_a = _joint_side_arg(body.get("a"), doc, known)
    side_b, occ_b = _joint_side_arg(body.get("b"), doc, known)
    if occ_a == occ_b:
        raise ValueError("a joint must connect two different component occurrences")
    raw_name = body.get("name")
    if raw_name is not None and not isinstance(raw_name, str):
        raise ValueError("name must be a string")
    name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else _next_joint_name(doc, jtype)
    params: dict = {"name": name, "type": jtype, "a": side_a, "b": side_b}
    if "flip" in body and body["flip"] is not None:
        if not isinstance(body["flip"], bool):
            raise ValueError("flip must be a boolean")
        params["flip"] = body["flip"]
    offset = _optional_scalar(body.get("offset"), "offset")
    if offset is not None:
        params["offset"] = offset
    angle = _optional_scalar(body.get("angle"), "angle")
    if angle is not None:
        params["angle"] = angle

    def apply():
        cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        meta_before = doc.metadata()
        try:
            out = modeling.add_joint(srv.ws, doc, params)
            doc.save()
            srv.mtime = doc.path.stat().st_mtime
            return out
        except BaseException:
            if cp is not None:
                modeling._restore(doc.session, cp, forget=False)
                modeling._restore(doc.session, cp, forget=True)
            try:
                doc.set_metadata(meta_before)
            except Exception:
                pass
            raise
        else:
            if cp is not None:
                modeling._restore(doc.session, cp, forget=True)

    out = srv.agent.hand_step(f"Joint {name} ({jtype}) in {doc.name}", apply)
    conflicts = (out.get("joint") or {}).get("conflicts") or []
    done = f"Added {jtype} joint {name}"
    if conflicts:
        done += f" ({len(conflicts)} conflict{'s' if len(conflicts) != 1 else ''})"
    return dict(out, name=name, type=jtype, conflicts=conflicts, done=done)


def _assembly_step(srv, doc, label: str, fn):
    """Run fn() on the shared undo list; on an error the session and the joint records go back."""
    def apply():
        cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        meta_before = doc.metadata()
        try:
            out = fn()
            doc.save()
            srv.mtime = doc.path.stat().st_mtime
        except BaseException:
            if cp is not None:
                modeling._restore(doc.session, cp, forget=False)
                modeling._restore(doc.session, cp, forget=True)
            try:
                doc.set_metadata(meta_before)
            except Exception:
                pass
            raise
        if cp is not None:
            modeling._restore(doc.session, cp, forget=True)
        return out
    return srv.agent.hand_step(label, apply)


def _constraint_type(raw) -> str:
    ctype = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if ctype not in modeling.CONSTRAINT_TYPES:
        raise ValueError(f"unsupported constraint type {raw!r}; choose from {', '.join(modeling.CONSTRAINT_TYPES)}")
    return ctype


def _constraint_values(body: dict, params: dict, ctype: str | None, editing: bool = False):
    """flip, offset and angle from the request; a new constraint needs a gap for distance and an angle for angle,
    an edit keeps its gap (assembly.constraint.edit) but needs an angle to change to angle."""
    if "flip" in body and body["flip"] is not None:
        if not isinstance(body["flip"], bool):
            raise ValueError("flip must be a boolean")
        params["flip"] = body["flip"]
    offset = _optional_scalar(body.get("offset"), "offset")
    if offset is not None:
        params["offset"] = offset
    angle = _optional_scalar(body.get("angle"), "angle")
    if angle is not None:
        params["angle"] = angle
    if ctype == "distance" and "offset" not in params and not editing:
        raise ValueError("a distance constraint needs an offset")
    if ctype == "angle" and "angle" not in params:
        raise ValueError("an angle constraint needs an angle")


def assembly_add_constraint(srv, doc, body: dict) -> dict:
    """Constrain two components (Inventor's Constrain, SolidCraft assembly.constraint.create) via
    modeling.add_constraint, which records the part faces like a joint's."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    known = _known_occurrences(doc)
    if len(set(known.values())) < 2:
        raise ValueError("place at least two components before adding a constraint")
    ctype = _constraint_type(body.get("type") or "mate")
    side_a, occ_a = _joint_side_arg(body.get("a"), doc, known)
    side_b, occ_b = _joint_side_arg(body.get("b"), doc, known)
    if occ_a == occ_b:
        raise ValueError("a constraint must connect two different component occurrences")
    raw_name = body.get("name")
    if raw_name is not None and not isinstance(raw_name, str):
        raise ValueError("name must be a string")
    # without a name SolidCraft names it by the rule and the first free number (Mate1, PointOnAxis1)
    name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None
    params: dict = {"type": ctype, "a": side_a, "b": side_b}
    if name:
        params["name"] = name
    _constraint_values(body, params, ctype)
    out = _assembly_step(srv, doc, f"Constraint {name or ctype} in {doc.name}",
                         lambda: modeling.add_constraint(srv.ws, doc, params))
    name = out.get("name") or name
    conflicts = (out.get("constraint") or {}).get("conflicts") or []
    done = f"Added {ctype} constraint {name}"
    if conflicts:
        done += f" ({len(conflicts)} conflict{'s' if len(conflicts) != 1 else ''})"
    return dict(out, name=name, type=ctype, conflicts=conflicts, done=done)


def assembly_edit_constraint(srv, doc, body: dict) -> dict:
    """Change a constraint's rule, gap, angle, flip or name (assembly.constraint.edit); its references stay."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    cname = body.get("constraint") or body.get("joint")
    if not isinstance(cname, str) or not cname.strip():
        raise ValueError("constraint name is required")
    cname = cname.strip()
    live = next((j for j in (doc.session.cmd("joint.list", {}).get("joints") or []) if j.get("name") == cname), None)
    if live is None or not live.get("constraint"):
        raise ValueError(f"unknown constraint {cname!r}")
    if body.get("a") is not None or body.get("b") is not None:
        raise ValueError("a constraint keeps its references: delete it and add a new one to pick other faces")
    params: dict = {}
    raw_name = body.get("name")
    if raw_name is not None and not isinstance(raw_name, str):
        raise ValueError("name must be a string")
    if isinstance(raw_name, str) and raw_name.strip() and raw_name.strip() != cname:
        params["name"] = raw_name.strip()
    ctype = None
    if body.get("type") is not None:
        ctype = _constraint_type(body["type"])
        if ctype != live.get("constraint"):
            params["type"] = ctype
    _constraint_values(body, params, ctype if ctype and ctype != live.get("constraint") else None, editing=True)
    if not params:
        raise ValueError("nothing to change on the constraint")
    out = _assembly_step(srv, doc, f"Edit constraint {cname} in {doc.name}",
                         lambda: modeling.edit_constraint(srv.ws, doc, cname, params))
    new_name = params.get("name", cname)
    return dict(out, name=new_name, done=f"Updated constraint {new_name}")


def assembly_place_standard(srv, doc, body: dict) -> dict:
    """Place Standard Part (#88 step 3, Inventor's Place from Content Center): make the parametric standard part
    file in the open folder (standard_parts.create, as the MCP tool standard_part does) unless a file of that
    designation is already there, then place it like Place (links.insert) on the shared undo list. Undo takes the
    component out again; the part file stays in the folder for the next use."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    norm = body.get("norm")
    size = body.get("size")
    if not isinstance(norm, str) or not norm.strip() or not isinstance(size, str) or not size.strip():
        raise ValueError("norm and size are required")
    length = body.get("length")
    if length in ("", None):
        length = None
    elif isinstance(length, bool):
        raise ValueError("length must be a number")
    else:
        length = _bolted_float(length, "length")
    sp = standard_parts.spec(norm.strip(), size.strip(), length)  # ValueError for an unknown norm, size or length
    designation = sp["standard"]["designation"]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", designation).strip("_")
    part_path = srv.folder_path / f"{stem}.solidcraft"
    t_vec = _vec3_or_zero(body.get("translate"), (body.get("tx"), body.get("ty"), body.get("tz")))
    translate = t_vec if any(abs(c) > 1e-12 for c in t_vec) else None
    grounded = _parse_optional_bool(body.get("grounded"))
    created = not part_path.exists()

    def apply():
        if created:
            standard_parts.create(srv.ws, norm.strip(), size.strip(), length=length, name=stem, path=str(part_path))
            srv.ws.close(stem)
        out = links.insert(srv.ws, doc, str(part_path), translate=translate, grounded=grounded)
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        return out

    out = srv.agent.hand_step(f"Place {designation} in {doc.name}", apply)
    comp = out.get("name") or out.get("occurrence_name") or stem
    return dict(out, name=comp, designation=designation, file=part_path.name, created=created,
                done=f"Placed {designation}" + (" (new part file)" if created else ""))


def assembly_delete_joint(srv, doc, body: dict) -> dict:
    """Delete a joint or constraint and what Mechvane recorded about it (MCP delete_joint), on the shared undo list."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    name = body.get("joint") or body.get("constraint")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("joint name is required")
    name = name.strip()
    if not any(j.get("name") == name for j in (doc.session.cmd("joint.list", {}).get("joints") or [])):
        raise ValueError(f"unknown joint {name!r}")

    def fn():
        doc.session.cmd("joint.delete", {"joint": name})
        links.forget(doc, name)
        return {"deleted": name}
    out = _assembly_step(srv, doc, f"Delete {name} in {doc.name}", fn)
    return dict(out, done=f"Deleted {name}")


def assembly_edit_joint(srv, doc, body: dict) -> dict:
    """Edit an existing joint via modeling.edit_joint on the shared undo list."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    joint = body.get("joint")
    if not isinstance(joint, str) or not joint.strip():
        raise ValueError("joint name is required")
    joint = joint.strip()
    known = _known_occurrences(doc)
    raw_occs = links._occurrences(doc.session)
    by_id = {oid: o["path"] for oid, o in raw_occs.items()}
    existing_joint = next((j for j in (doc.session.cmd("joint.list", {}).get("joints") or []) if j.get("name") == joint), None)
    if existing_joint is None:
        raise ValueError(f"unknown joint {joint!r}")
    cur_a = by_id.get(existing_joint.get("a"), "")
    cur_b = by_id.get(existing_joint.get("b"), "")
    params: dict = {}
    raw_name = body.get("name")
    if raw_name is not None and not isinstance(raw_name, str):
        raise ValueError("name must be a string")
    if isinstance(raw_name, str) and raw_name.strip():
        params["name"] = raw_name.strip()
    if body.get("type") is not None:
        jtype = str(body["type"]).strip().lower()
        if jtype not in JOINT_TYPES:
            raise ValueError(f"unsupported joint type {jtype!r}; choose from {', '.join(JOINT_TYPES)}")
        params["type"] = jtype
    if body.get("a") is not None:
        params["a"], cur_a = _joint_side_arg(body["a"], doc, known)
    if body.get("b") is not None:
        params["b"], cur_b = _joint_side_arg(body["b"], doc, known)
    if cur_a and cur_b and cur_a == cur_b:
        raise ValueError("a joint must connect two different component occurrences")
    if "flip" in body and body["flip"] is not None:
        if not isinstance(body["flip"], bool):
            raise ValueError("flip must be a boolean")
        params["flip"] = body["flip"]
    offset = _optional_scalar(body.get("offset"), "offset")
    if offset is not None:
        params["offset"] = offset
    angle = _optional_scalar(body.get("angle"), "angle")
    if angle is not None:
        params["angle"] = angle
    if not params:
        raise ValueError("nothing to change on the joint")

    def apply():
        cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        meta_before = doc.metadata()
        try:
            out = modeling.edit_joint(srv.ws, doc, joint, params)
            doc.save()
            srv.mtime = doc.path.stat().st_mtime
            return out
        except BaseException:
            if cp is not None:
                modeling._restore(doc.session, cp, forget=False)
                modeling._restore(doc.session, cp, forget=True)
            try:
                doc.set_metadata(meta_before)
            except Exception:
                pass
            raise
        else:
            if cp is not None:
                modeling._restore(doc.session, cp, forget=True)

    out = srv.agent.hand_step(f"Edit joint {joint} in {doc.name}", apply)
    new_name = params.get("name", joint)
    conflicts = (out.get("joint") or {}).get("conflicts") or []
    done = f"Updated joint {new_name}"
    if conflicts:
        done += f" ({len(conflicts)} conflict{'s' if len(conflicts) != 1 else ''})"
    return dict(out, name=new_name, conflicts=conflicts, done=done)


def collect_standard_parts(norm: str | None = None) -> dict:
    """Return the standard parts catalog plus bolted-connection options."""
    data = standard_parts.catalog(norm)
    if norm is None:
        data["bolted_norms"] = ["ISO 4762", "ISO 10642"]
        data["bolted_details"] = {
            n: standard_parts.catalog(n) for n in data["bolted_norms"]
        }
        # every norm's sizes and preferred lengths, for Place Standard Part
        data["details"] = {n["norm"]: standard_parts.catalog(n["norm"]) for n in data["norms"]}
        data["materials"] = list(hole_tables.MATERIAL_ENGAGEMENT_DEPTHS)
        data["fits"] = ["close", "normal", "loose"]
    return data


def _close_linked_docs(srv, keep_name: str):
    """Close cached linked documents so subsequent edits or Undo reload cleanly from disk."""
    for k in list(srv.ws.docs):
        if k != keep_name:
            try:
                srv.ws.close(k)
            except Exception:
                pass


class _BoltedNotFoundError(KeyError):
    """Raised when a requested bolted connection id does not exist in the assembly."""


def _bolted_float(val, field: str) -> float:
    if isinstance(val, bool) or val is None or (isinstance(val, str) and not val.strip()):
        raise ValueError(f"{field} must be a number, got {val!r}")
    try:
        num = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number, got {val!r}") from None
    if not math.isfinite(num):
        raise ValueError(f"{field} must be a finite number, got {val!r}")
    return num


def _bolted_validate_options(
    size: str,
    head: str,
    conn_type: str,
    fit: str = "normal",
    blind_material: str | None = None,
) -> str:
    canon_size = hole_tables.normalize_size(size)
    hole_tables.normalize_fit(fit)
    ct = (conn_type or "through").strip().lower()
    if ct not in ("through", "blind", "insert"):
        raise ValueError(f"unsupported connection_type {conn_type!r} (must be 'through', 'blind' or 'insert')")
    if head == "countersunk" and canon_size not in standard_parts.ISO_10642:
        avail = ", ".join(standard_parts.ISO_10642)
        raise ValueError(f"unsupported thread size {size!r} for ISO 10642 (available: {avail})")
    if ct == "insert" and canon_size not in standard_parts.RUTHEX_INSERTS:
        avail = ", ".join(standard_parts.RUTHEX_INSERTS)
        raise ValueError(f"unsupported thread size {size!r} for Ruthex insert (available: {avail})")
    if ct == "blind" and blind_material:
        hole_tables.normalize_material(blind_material)
    return canon_size


def _bolted_head_from_body(body: dict, default_head: str = "cap") -> str:
    head = body.get("head")
    if isinstance(head, str) and head.strip():
        h = head.strip().lower()
        if h in ("cap", "countersunk"):
            return h
        raise ValueError(f"unsupported screw head {head!r}")
    norm = body.get("screw_norm")
    if isinstance(norm, str) and norm.strip():
        canon = standard_parts.resolve_norm(norm)
        if canon == "ISO 10642":
            return "countersunk"
        if canon == "ISO 4762":
            return "cap"
        raise ValueError(f"unsupported screw norm {norm!r}; use ISO 4762 or ISO 10642")
    return default_head


def _bolted_placement_from_body(body: dict) -> dict:
    p = body.get("placement")
    if isinstance(p, dict):
        pl = dict(p)
        if pl.get("type") in (None, "point", "linear") and "position" not in pl and "point" in pl:
            pl["position"] = pl.pop("point")
            pl.setdefault("type", "point")
        if "position" in pl:
            pos = pl["position"]
            if not isinstance(pos, (list, tuple)) or len(pos) != 3:
                raise ValueError("placement 'position' must be a 3D coordinate [x, y, z]")
            pl["position"] = [_bolted_float(pos[0], "x"), _bolted_float(pos[1], "y"), _bolted_float(pos[2], "z")]
        if pl.get("direction") is not None:
            d = pl["direction"]
            if not isinstance(d, (list, tuple)) or len(d) != 3:
                raise ValueError("placement 'direction' must be a 3D vector [dx, dy, dz]")
            pl["direction"] = [_bolted_float(d[0], "dx"), _bolted_float(d[1], "dy"), _bolted_float(d[2], "dz")]
    else:
        if not all(k in body for k in ("x", "y", "z")):
            raise ValueError("placement or x/y/z coordinates required")
        pt = [_bolted_float(body["x"], "x"), _bolted_float(body["y"], "y"), _bolted_float(body["z"], "z")]
        direction = body.get("direction")
        if direction is None and all(k in body for k in ("dx", "dy", "dz")):
            direction = [_bolted_float(body["dx"], "dx"), _bolted_float(body["dy"], "dy"), _bolted_float(body["dz"], "dz")]
        pl = {"type": "point", "position": pt}
        if direction is not None:
            if not isinstance(direction, (list, tuple)) or len(direction) != 3:
                raise ValueError("direction must be a 3D vector [dx, dy, dz]")
            pl["direction"] = [_bolted_float(direction[0], "dx"), _bolted_float(direction[1], "dy"), _bolted_float(direction[2], "dz")]
    if body.get("flip") and isinstance(pl.get("direction"), (list, tuple)) and len(pl["direction"]) == 3:
        pl["direction"] = [-float(v) for v in pl["direction"]]
    return pl


def _bolted_fasteners_from_body(
    body: dict,
    head: str,
    conn_type: str,
    old_fasteners: dict | None = None,
    old_head: str | None = None,
    old_conn_type: str | None = None,
) -> dict:
    fast = dict(old_fasteners or {})
    body_fast = body.get("fasteners") if isinstance(body.get("fasteners"), dict) else {}
    if body_fast:
        fast.update(body_fast)
    has_washer_head = "washer_head" in body or "washer_head" in body_fast
    has_washer_nut = "washer_nut" in body or "washer_nut" in body_fast
    if head == "countersunk":
        fast["washer_head"] = False
    elif has_washer_head:
        fast["washer_head"] = bool(body["washer_head"] if "washer_head" in body else body_fast["washer_head"])
    elif "washer_head" not in fast or (old_head is not None and head != old_head):
        fast["washer_head"] = (head == "cap")
    if conn_type != "through":
        fast["washer_nut"] = False
    elif has_washer_nut:
        fast["washer_nut"] = bool(body["washer_nut"] if "washer_nut" in body else body_fast["washer_nut"])
    elif "washer_nut" not in fast or (old_conn_type is not None and conn_type != old_conn_type):
        fast["washer_nut"] = (conn_type == "through")
    len_keys = ("length_override", "screw_length", "length")
    has_len = any(k in body for k in len_keys) or any(k in body_fast for k in len_keys)
    if has_len:
        len_raw = next(
            (body[k] for k in len_keys if k in body),
            next((body_fast[k] for k in len_keys if k in body_fast), None),
        )
        if len_raw in (None, "", "auto"):
            fast["length_override"] = None
        else:
            val = _bolted_float(len_raw, "length")
            if val <= 0:
                raise ValueError(f"length must be a positive number, got {len_raw!r}")
            fast["length_override"] = val
    return fast


def _bolted_item_dict(cid: str, c: dict) -> dict:
    params = c.get("parameters") or {}
    fast = params.get("fasteners") or {}
    head = c.get("head") or params.get("head") or ("countersunk" if c.get("screw_norm") == "ISO 10642" else "cap")
    conn_type = c.get("type") or params.get("connection_type") or "through"
    cb_raw = c["counterbore"] if "counterbore" in c else params.get("counterbore", head == "cap")
    wh_raw = c["washer_head"] if "washer_head" in c else fast.get("washer_head", head == "cap")
    wn_raw = c["washer_nut"] if "washer_nut" in c else fast.get("washer_nut", conn_type == "through")
    return {
        "id": cid,
        "name": c.get("name") or params.get("name") or cid,
        "size": c.get("size") or params.get("size"),
        "head": head,
        "screw_norm": c.get("screw_norm") or ("ISO 10642" if head == "countersunk" else "ISO 4762"),
        "screw_length": c.get("screw_length"),
        "type": conn_type,
        "fit": c.get("fit") or params.get("fit") or "normal",
        "counterbore": bool(cb_raw) and head == "cap",
        "washer_head": bool(wh_raw) and head == "cap",
        "washer_nut": bool(wn_raw) and conn_type == "through",
        "blind_material": c.get("blind_material") or params.get("blind_material"),
        "parts": [p.get("occurrence") for p in c.get("parts", []) if p.get("occurrence")],
        "count": len(c.get("instances", [])) or 1,
        "parameters": params,
        "placement": c.get("placement") or params.get("placement"),
        "instances": c.get("instances") or [],
    }


def assembly_bolted_list(srv, doc) -> dict:
    """List bolted connections recorded in the active assembly."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    data = bolted.list_bolted_connections(srv.ws, doc.name)
    conns = data.get("connections") or {}
    items = [_bolted_item_dict(cid, c) for cid, c in conns.items()]
    return {"connections": conns, "items": items, "count": len(conns)}


def _bolted_preview_geometry(ws, doc, prev: dict, placement: dict) -> dict:
    """Attach axis/direction and standard fastener envelope dims for 3D UI preview rendering."""
    p0, dir_w = bolted._parse_placement(ws, doc, placement)
    rays = bolted._generate_pattern_rays(p0, dir_w, prev.get("pattern"))
    sz = prev["size"]
    screw_norm = prev["screw_norm"]
    screw_row = standard_parts.ISO_10642[sz] if screw_norm == "ISO 10642" else standard_parts.ISO_4762[sz]
    nut_row = standard_parts.ISO_4032[sz]
    washer_row = standard_parts.ISO_7089[sz]
    direction = [round(float(v), 6) for v in rays[0][1]]
    return {
        "origin": [round(float(v), 4) for v in rays[0][0]],
        "direction": direction,
        "points": [[round(float(v), 4) for v in r[0]] for r in rays],
        "dims": {
            "d": screw_row["d"],
            "dk": screw_row["dk"],
            "k": screw_row["k"],
            "nut_m": nut_row["m"],
            "nut_s": nut_row["s"],
            "washer_d2": washer_row["d2"],
            "washer_h": washer_row["h"],
        },
    }


def assembly_bolted_preview(srv, doc, body: dict) -> dict:
    """Preview a new or edited bolted connection without modifying any files."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    edit_id = body.get("edit_id") or body.get("id")
    old_conn = {}
    old_params = {}
    parts = body.get("parts")
    if edit_id:
        conns = bolted.list_bolted_connections(srv.ws, doc.name).get("connections") or {}
        if edit_id not in conns:
            raise _BoltedNotFoundError(f"no bolted connection {edit_id!r} in assembly {doc.name!r}")
        old_conn = conns[edit_id]
        old_params = dict(old_conn.get("parameters") or {})
        if not parts:
            # Restrict ray-casting to the connected plates so existing fastener occurrences do not block the preview.
            parts = [p["occurrence"] for p in old_conn.get("parts", []) if p.get("occurrence")]

    if any(k in body for k in ("placement", "x", "y", "z")):
        placement = _bolted_placement_from_body(body)
    else:
        saved_pl = old_params.get("placement") or old_conn.get("placement")
        if saved_pl is None:
            raise ValueError("placement or x/y/z coordinates required")
        placement = dict(saved_pl)

    default_head = old_params.get("head") or ("countersunk" if old_conn.get("screw_norm") == "ISO 10642" else "cap")
    old_conn_type = str(old_params.get("connection_type") or old_conn.get("type") or "through")
    head = _bolted_head_from_body(body, default_head=default_head)
    size = str(body.get("size") or old_params.get("size") or "M6")
    conn_type = str(body.get("connection_type") or old_params.get("connection_type") or "through")
    use_insert = bool(body.get("use_insert") if "use_insert" in body else (conn_type == "insert"))
    fit = str(body.get("fit") or old_params.get("fit") or "normal")
    if "counterbore" in body:
        counterbore = bool(body["counterbore"]) and head == "cap"
    elif edit_id and head != default_head:
        counterbore = (head == "cap")
    else:
        counterbore = bool(old_params.get("counterbore", head == "cap")) and head == "cap"
    blind_material = body.get("blind_material") if "blind_material" in body else old_params.get("blind_material")
    _bolted_validate_options(size, head, conn_type, fit, blind_material)
    fasteners = _bolted_fasteners_from_body(
        body,
        head,
        conn_type,
        old_params.get("fasteners"),
        old_head=default_head if edit_id else None,
        old_conn_type=old_conn_type if edit_id else None,
    )
    pattern = body.get("pattern") if "pattern" in body else old_params.get("pattern")

    out = bolted.preview_bolted_connection(
        srv.ws,
        doc.name,
        placement,
        size,
        fasteners=fasteners,
        fit=fit,
        counterbore=counterbore,
        connection_type=conn_type,
        blind_material=blind_material,
        use_insert=use_insert,
        pattern=pattern,
        parts=parts,
        head=head,
    )
    out.update(_bolted_preview_geometry(srv.ws, doc, out, placement))
    return out


def assembly_bolted_create(srv, doc, body: dict) -> dict:
    """Create a bolted connection via bolted.bolted_connection (recorded on shared undo list)."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    placement = _bolted_placement_from_body(body)
    head = _bolted_head_from_body(body)
    size = str(body.get("size") or "M6")
    conn_type = str(body.get("connection_type") or "through")
    use_insert = bool(body.get("use_insert") if "use_insert" in body else (conn_type == "insert"))
    fit = str(body.get("fit") or "normal")
    if "counterbore" in body:
        counterbore = bool(body["counterbore"]) and head == "cap"
    else:
        counterbore = (head == "cap")
    blind_material = body.get("blind_material")
    _bolted_validate_options(size, head, conn_type, fit, blind_material)
    fasteners = _bolted_fasteners_from_body(body, head, conn_type)
    name = (body.get("name") or "").strip() or None
    pattern = body.get("pattern")
    parts = body.get("parts")

    def apply():
        out = bolted.bolted_connection(
            srv.ws,
            doc.name,
            placement,
            size,
            fasteners=fasteners,
            fit=fit,
            counterbore=counterbore,
            connection_type=conn_type,
            blind_material=blind_material,
            use_insert=use_insert,
            name=name,
            pattern=pattern,
            parts=parts,
            head=head,
        )
        _close_linked_docs(srv, doc.name)
        srv.mtime = doc.path.stat().st_mtime
        return out

    label = f"Bolted connection {size} in {doc.name}"
    out = srv.agent.hand_step(label, apply)
    msg = f"Created {out.get('screw_norm', '')} {out.get('size', size)} x {out.get('screw_length', '')}".strip()
    return dict(out, message=msg, done=msg)


def assembly_bolted_edit(srv, doc, body: dict) -> dict:
    """Edit an existing bolted connection via bolted.edit_bolted_connection (shared undo list)."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    conn_id = (body.get("id") or "").strip()
    if not conn_id:
        raise ValueError("id of bolted connection is required")
    conns = bolted.list_bolted_connections(srv.ws, doc.name).get("connections") or {}
    if conn_id not in conns:
        raise _BoltedNotFoundError(f"no bolted connection {conn_id!r} in assembly {doc.name!r}")
    old_conn = conns[conn_id]
    old_params = dict(old_conn.get("parameters") or {})
    default_head = old_params.get("head") or ("countersunk" if old_conn.get("screw_norm") == "ISO 10642" else "cap")
    old_conn_type = str(old_params.get("connection_type") or old_conn.get("type") or "through")

    changes = {}
    if any(k in body for k in ("placement", "x", "y", "z")):
        changes["placement"] = _bolted_placement_from_body(body)
    if "head" in body or "screw_norm" in body:
        changes["head"] = _bolted_head_from_body(body, default_head=default_head)
    head = changes.get("head", default_head)
    if "size" in body and body["size"]:
        changes["size"] = str(body["size"])
    if "fit" in body and body["fit"]:
        changes["fit"] = str(body["fit"])
    conn_type = str(body.get("connection_type") or old_conn_type)
    if "connection_type" in body:
        changes["connection_type"] = conn_type
        changes["use_insert"] = (conn_type == "insert")
    elif "use_insert" in body:
        changes["use_insert"] = bool(body["use_insert"])
    if "blind_material" in body:
        changes["blind_material"] = body["blind_material"]
    if "counterbore" in body:
        changes["counterbore"] = bool(body["counterbore"]) and head == "cap"
    elif head == "countersunk":
        changes["counterbore"] = False
    elif head != default_head:
        changes["counterbore"] = (head == "cap")
    if "pattern" in body:
        changes["pattern"] = body["pattern"]
    if "parts" in body:
        changes["parts"] = body["parts"]
    eff_size = changes.get("size") or old_params.get("size") or old_conn.get("size") or "M6"
    eff_fit = changes.get("fit") or old_params.get("fit") or old_conn.get("fit") or "normal"
    eff_mat = changes.get("blind_material") if "blind_material" in changes else old_params.get("blind_material")
    _bolted_validate_options(str(eff_size), head, conn_type, str(eff_fit), eff_mat)
    fast_keys = ("fasteners", "washer_head", "washer_nut", "length_override", "screw_length", "length")
    if any(k in body for k in fast_keys) or "head" in changes or "connection_type" in changes:
        changes["fasteners"] = _bolted_fasteners_from_body(
            body,
            head,
            conn_type,
            old_params.get("fasteners"),
            old_head=default_head,
            old_conn_type=old_conn_type,
        )

    def apply():
        out = bolted.edit_bolted_connection(srv.ws, doc.name, conn_id, **changes)
        _close_linked_docs(srv, doc.name)
        srv.mtime = doc.path.stat().st_mtime
        return out

    label = f"Edit bolted connection {conn_id} in {doc.name}"
    out = srv.agent.hand_step(label, apply)
    msg = f"Updated {conn_id}: {out.get('screw_norm', '')} {out.get('size', '')} x {out.get('screw_length', '')}".strip()
    return dict(out, message=msg, done=msg)


def assembly_bolted_delete(srv, doc, body: dict) -> dict:
    """Delete a bolted connection via bolted.delete_bolted_connection (shared undo list)."""
    if doc.kind != ASSEMBLY:
        raise ValueError("open an assembly, not a part")
    conn_id = (body.get("id") or "").strip()
    if not conn_id:
        raise ValueError("id of bolted connection is required")
    conns = bolted.list_bolted_connections(srv.ws, doc.name).get("connections") or {}
    if conn_id not in conns:
        raise _BoltedNotFoundError(f"no bolted connection {conn_id!r} in assembly {doc.name!r}")

    def apply():
        out = bolted.delete_bolted_connection(srv.ws, doc.name, conn_id)
        _close_linked_docs(srv, doc.name)
        srv.mtime = doc.path.stat().st_mtime
        return out

    label = f"Delete bolted connection {conn_id} in {doc.name}"
    out = srv.agent.hand_step(label, apply)
    msg = f"Deleted bolted connection {conn_id}"
    return dict(out, message=msg, done=msg)


def model_names(doc) -> list[str]:
    """Names a user may say about the open document: features, bodies, parameters, occurrences."""
    s = doc.session
    insp = s.cmd("document.inspect", {"measure": False})
    names = [f["name"] for f in insp.get("timeline", [])] + [b["name"] for b in insp.get("bodies", [])]
    names += [p.get("name") for p in insp.get("parameters", []) if isinstance(p, dict)]
    if doc.kind == ASSEMBLY:
        names += [o["name"] for o in links._occurrences(s).values()]
    return sorted({n for n in names if n})


def _joint_summary(joint_checks) -> str:
    bad = sorted({j["joint"] for j in joint_checks if j.get("status") != "ok"})
    if not joint_checks:
        return "Assembly: no joints recorded by Mechvane"
    if bad:
        return f"Joint check: {len(bad)} joint(s) need attention: {', '.join(bad)}"
    return f"Joint check: all {len({j['joint'] for j in joint_checks})} joints ok"


def collect_findings(ws, doc, profile: str | None = None, material: str | None = None) -> dict:
    """Collect design rule findings for a part, joint link findings for an assembly.

    Design rules are part rules (like check_design): on an assembly they would treat screws and
    plates as one printed body."""
    dr = design_rules.check(doc, profile=profile, material=material) if doc.kind == PART else {}
    findings = []

    for c in dr.get("checks", []):
        loc = dict(c.get("location") or {})
        face = loc.get("face")
        point = loc.get("point")
        status = c.get("status", "ok")
        item = {
            "source": "design_rules",
            "rule": c.get("rule", "design_rule"),
            "status": status,
            "severity": status,
            "message": c.get("message", ""),
            "location": loc,
            "face": face,
            "faces": [face] if face else [],
            "point": point,
        }
        if loc.get("body"):
            item["body"] = loc["body"]
        for k in ("value", "threshold"):
            if k in c:
                item[k] = c[k]
        findings.append(item)

    joint_checks = []
    if doc.kind == ASSEMBLY:
        joint_checks = links.check(ws, doc)
        frames = links._frames(doc.session)
        for jc in joint_checks:
            jname = jc["joint"]
            side = jc["side"]
            occ = jc.get("occurrence")
            face = jc.get("face")
            st = jc.get("status", "ok")
            sev = _joint_severity(st)
            _, origin, z = frames.get(jname, {}).get(side, (None, None, None))
            asm_body, asm_face = _match_assembly_face(doc, occ, origin, z)
            face_list = [f for f in (face, asm_face) if f]
            if st == "ok":
                msg = f"Joint {jname} (side {side} on {occ}): ok ({face or 'verified'})"
            elif st == "moved":
                msg = f"Joint {jname} (side {side} on {occ}): moved from {face} to {jc.get('now_on') or '?'}"
            else:
                msg = f"Joint {jname} (side {side} on {occ}): {st}"
            loc = {"point": origin, "face": face}
            if asm_face:
                loc["assembly_face"] = asm_face
            if asm_body:
                loc["body"] = asm_body
            item = {
                "source": "links",
                "rule": "joint_check",
                "joint": jname,
                "side": side,
                "occurrence": occ,
                "status": st,
                "severity": sev,
                "message": msg,
                "location": loc,
                "face": face or asm_face,
                "faces": face_list,
                "point": origin,
            }
            if asm_body:
                item["body"] = asm_body
            findings.append(item)

    _add_selections(doc, findings)
    order = {"fail": 0, "warn": 1, "ok": 2}
    findings.sort(key=lambda x: (order.get(x.get("severity", "ok"), 3), 1 if x.get("rule") == "printability" else 0))

    # the design check can warn without a finding of its own (a part without bodies)
    has_fail = any(f["severity"] == "fail" for f in findings) or dr.get("verdict") == "fail"
    has_warn = any(f["severity"] == "warn" for f in findings) or dr.get("verdict") == "warn"
    verdict = "fail" if has_fail else ("warn" if has_warn else "ok")

    return {
        "status": verdict,
        "verdict": verdict,
        "profile": dr.get("profile", profile),
        "material": dr.get("material", material),
        "material_source": dr.get("material_source"),
        # choices for the Check page's profile and material selectors
        "profiles": {k: v["name"] for k, v in design_rules.PROFILES.items()},
        "materials": list(hole_tables.MATERIAL_ENGAGEMENT_DEPTHS),
        "summary": dr.get("summary") or _joint_summary(joint_checks),
        "findings": findings,
        "checks": findings,
        "rules": dr.get("rules", {}),
        "joints": joint_checks,
    }


def _resolve_workspace_root(file_path: Path) -> Path:
    env_ws = os.environ.get("MECHVANE_WORKSPACE") or os.environ.get("INVENTA_WORKSPACE")
    if env_ws:
        cand = Path(env_ws).resolve()
        try:
            file_path.relative_to(cand)
            return cand
        except ValueError:
            pass
    return file_path.parent


def detect_kind(p: Path, ws: Workspace | None = None) -> str:
    try:
        with zipfile.ZipFile(p) as zf:
            d = json.loads(zf.read("document.json"))
        meta_kind = read_metadata(d.get("metadata")).get("kind")
        if meta_kind in (PART, ASSEMBLY):
            return meta_kind
        return ASSEMBLY if d.get("links") else PART
    except Exception:
        if ws is not None:
            try:
                r = ws.reader(p)
                try:
                    kind = read_metadata(r.cmd("document.metadata").get("metadata")).get("kind")
                    if kind in (PART, ASSEMBLY):
                        return kind
                    return ASSEMBLY if r.cmd("component.links").get("links") else PART
                finally:
                    r.close()
            except Exception:
                pass
        return PART


RECENT_FOLDERS_FILE = "recent_folders.json"


def load_recent_folders() -> list[str]:
    """Return recently used project folder paths (at most 5, newest first), filtering missing paths."""
    p = install.CACHE / RECENT_FOLDERS_FILE
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            res = []
            for item in data:
                if isinstance(item, str):
                    try:
                        resolved = str(Path(item).expanduser().resolve())
                        if Path(resolved).is_dir() and resolved not in res:
                            res.append(resolved)
                    except Exception:
                        pass
            return res[:5]
    except Exception:
        pass
    return []


def add_recent_folder(folder: str | Path):
    """Add a folder path to the top of recently used folders (persisted in install.CACHE)."""
    try:
        resolved = str(Path(folder).expanduser().resolve())
        if not Path(resolved).is_dir():
            return
        current = load_recent_folders()
        if resolved in current:
            current.remove(resolved)
        current.insert(0, resolved)
        current = current[:5]
        install.CACHE.mkdir(parents=True, exist_ok=True)
        (install.CACHE / RECENT_FOLDERS_FILE).write_text(json.dumps(current, indent=2), encoding="utf-8")
    except Exception:
        pass


def _folder_counts(p: Path) -> tuple[int, int]:
    """Count non-hidden .solidcraft and STEP/IGES files in directory p."""
    sc_count = 0
    step_count = 0
    try:
        for entry in p.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.is_file():
                suf = entry.suffix.lower()
                if suf == ".solidcraft":
                    sc_count += 1
                elif suf in step_import.SUFFIXES:
                    step_count += 1
    except (PermissionError, OSError):
        pass
    return sc_count, step_count


def _get_roots() -> list[dict]:
    """Return root directories (drives on Windows, / on POSIX, plus Home)."""
    roots = []
    try:
        home = Path.home().resolve()
        roots.append({"name": f"Home ({home.name})", "path": str(home)})
    except Exception:
        pass

    if sys.platform == "win32":
        import string
        drives = []
        try:
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:\\")
                bitmask >>= 1
        except Exception:
            for letter in string.ascii_uppercase:
                p = Path(f"{letter}:\\")
                if p.exists():
                    drives.append(f"{letter}:\\")
        for d in drives:
            roots.append({"name": d, "path": d})
    else:
        roots.append({"name": "/", "path": "/"})
    return roots


class UIServer(ThreadingHTTPServer):
    """ThreadingHTTPServer holding a locked Workspace and open Document."""

    # On Windows SO_REUSEADDR lets a second server bind the same port silently
    allow_reuse_address = sys.platform != "win32"
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, path):
        self.lock = threading.Lock()
        self.path = Path(path).resolve()
        if not self.path.exists():
            raise FileNotFoundError(f"path not found: {self.path}")
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="ui1-"))  # the system temp folder (not /tmp on Windows)
        self._kind_cache = {}
        # True once an app window owns this server: closing it stops Mechvane (the UI says so)
        self.stops_with_window = False
        # Inventor's "Autoproject edges for sketch creation" (default on)
        self.auto_project = True

        if self.path.is_dir():
            self.is_folder = True
            self.folder_path = self.path
            self.file_path = None
            self.doc = None
            self.doc_name = None
            self.mtime = None
            ws_root = self.folder_path
            self.ws = Workspace(ws_root)
            self.ws.session = lambda: Session(allow_paths=[self.ws.root, self.tmp_dir])
            try:
                super().__init__(server_address, RequestHandlerClass)
            except Exception:
                self.ws.close_all()
                shutil.rmtree(self.tmp_dir, ignore_errors=True)
                raise
            add_recent_folder(self.folder_path)
        elif self.path.is_file():
            self.is_folder = False
            self.file_path = self.path
            self.folder_path = self.file_path.parent
            ws_root = _resolve_workspace_root(self.file_path)
            self.ws = Workspace(ws_root)
            self.ws.session = lambda: Session(allow_paths=[self.ws.root, self.tmp_dir])
            try:
                self.doc = self.ws.open(self.file_path)
                self.doc_name = self.doc.name
                self.mtime = self.file_path.stat().st_mtime
                super().__init__(server_address, RequestHandlerClass)
            except Exception:
                self.ws.close_all()
                shutil.rmtree(self.tmp_dir, ignore_errors=True)
                raise
            add_recent_folder(self.folder_path)
        else:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
            raise FileNotFoundError(f"not a file or directory: {self.path}")

    @property
    def agent(self) -> "agent_mod.AgentTurns":
        """The chat with the user's agent (ADR 0003), started on first use."""
        if getattr(self, "_agent", None) is None:
            self._agent = agent_mod.AgentTurns(self.ws.root, on_files_changed=self._files_changed)
        return self._agent

    def agent_busy(self) -> bool:
        return getattr(self, "_agent", None) is not None and self._agent.busy

    def _files_changed(self):
        with self.lock:
            for k in list(self.ws.docs):
                try:
                    self.ws.close(k)
                except Exception:
                    pass
            self.doc = None
            self.mtime = None  # ensure_current opens the document again

    def _get_kind(self, p: Path) -> str:
        mtime = p.stat().st_mtime
        key = (p.name, mtime)
        cached = self._kind_cache.get(key)
        if cached is not None:
            return cached
        k = detect_kind(p, self.ws)
        self._kind_cache[key] = k
        return k

    def ensure_current(self):
        if self.file_path is None:
            return None
        cur = self.file_path.stat().st_mtime
        if cur != self.mtime:
            if self.doc_name in self.ws.docs:
                self.ws.close(self.doc_name)
            self.doc = self.ws.open(self.file_path)
            self.doc_name = self.doc.name
            self.mtime = cur
        return self.doc

    def files(self) -> dict:
        """Files the "Model" mode may load and save, by name: the open document and, for an
        assembly, its linked part files."""
        if self.file_path is None:
            return {}
        out = {self.file_path.name: self.file_path}
        doc = self.ensure_current()
        if doc and doc.kind == ASSEMBLY:
            for link in links._links(doc.session).values():
                p = Path(link.get("file") or "")
                if not p.is_absolute() and self.folder_path:
                    p = self.folder_path / p
                if p.is_file():
                    out.setdefault(p.name, p.resolve())
        return out

    def placeable_parts(self) -> list[str]:
        """Sorted .solidcraft designs in this document's folder, excluding the open file itself."""
        if self.file_path is None or not self.folder_path.is_dir():
            return []
        self_name = self.file_path.name
        parts = []
        for p in sorted(self.folder_path.iterdir(), key=lambda x: x.name):
            if p.is_file() and p.name.endswith(".solidcraft") and not p.name.startswith(".") and p.name != self_name:
                if self._get_kind(p) in (PART, ASSEMBLY):
                    parts.append(p.name)
        return parts

    def save(self, name: str, data: bytes) -> dict:
        """Write a file saved in the web app, reload the document and check it again."""
        if self.file_path is None:
            raise KeyError(name)
        target = self.files().get(name)
        if target is None:
            raise KeyError(name)
        tmp = target.with_name(f".{target.name}.upload")
        tmp.write_bytes(data)
        os.replace(tmp, target)
        if target != self.file_path:
            # A linked part changed: reopen the assembly so update_links reads it again.
            self.mtime = None
        doc = self.ensure_current()
        out = {"saved": name, "bytes": len(data), "findings": collect_findings(self.ws, doc)}
        if doc.kind == ASSEMBLY:
            out["update_links"] = links.update_links(self.ws, doc)
        return out

    def list_documents(self) -> list[dict]:
        if not self.is_folder:
            kind = self.doc.kind if self.doc else self._get_kind(self.file_path)
            return [{"name": self.file_path.name, "kind": kind}]
        docs = []
        for p in sorted(self.folder_path.iterdir(), key=lambda x: x.name):
            if p.is_file() and p.name.endswith(".solidcraft") and not p.name.startswith("."):
                docs.append({"name": p.name, "kind": self._get_kind(p)})
        return docs

    def project(self) -> dict:
        return {
            "folder": self.folder_path.name,
            "current": self.file_path.name if self.file_path else None,
            "documents": self.list_documents(),
            "mode": "folder" if self.is_folder else "file",
            # files File -> Import STEP... can make a part from
            "step_files": sorted(p.name for p in self.folder_path.iterdir()
                                 if p.is_file() and p.suffix.lower() in step_import.SUFFIXES) if self.is_folder else [],
        }

    def open_document(self, name: str) -> dict:
        valid_docs = {d["name"] for d in self.list_documents()}
        if name not in valid_docs:
            raise KeyError(name)
        target = (self.folder_path / name if self.is_folder else self.file_path).resolve()
        if not target.is_file():
            raise KeyError(name)
        if self.doc_name and self.doc_name in self.ws.docs:
            self.ws.close(self.doc_name)
        self.file_path = target
        self.doc = self.ws.open(target)
        self.doc_name = self.doc.name
        self.mtime = target.stat().st_mtime
        return {"document": self.file_path.name, "files": sorted(self.files())}

    def new_document(self, name: str) -> dict:
        if not self.is_folder:
            raise NotADirectoryError("new document only supported in folder mode")
        _validate_name(name)
        stem = name[:-11] if name.endswith(".solidcraft") else name
        _validate_name(stem)
        target = self.folder_path / f"{stem}.solidcraft"
        if target.exists():
            raise FileExistsError(f"document {target.name!r} already exists")
        doc = self.ws.new(PART, stem)
        if self.doc_name and self.doc_name in self.ws.docs:
            self.ws.close(self.doc_name)
        self.file_path = target
        self.doc = doc
        self.doc_name = doc.name
        self.mtime = target.stat().st_mtime
        return {"document": self.file_path.name, "files": sorted(self.files())}

    def import_step_document(self, file: str, split: bool = False) -> dict:
        """File -> Import STEP...: a part or assembly file from a STEP file in the project folder or from an external path,
        opened as the document."""
        if not self.is_folder:
            raise NotADirectoryError("importing is only supported in folder mode")
        src = Path(file).expanduser()
        if src.is_absolute():
            if not src.is_file():
                raise FileNotFoundError(f"no such file: {file}")
            if src.suffix.lower() not in step_import.SUFFIXES:
                raise ValueError(f"not a STEP or IGES file: {src.name}")
        else:
            if file not in self.project()["step_files"]:
                raise KeyError(file)
            src = self.folder_path / file
        stem = src.stem
        _validate_name(stem)
        target = self.folder_path / f"{stem}.solidcraft"
        if target.exists():
            raise FileExistsError(f"document {stem + '.solidcraft'!r} already exists")
        res = step_import.import_step(self.ws, src, name=stem, split=split)
        doc = self.ws.get(res["name"], ASSEMBLY if split else PART)
        if self.doc_name and self.doc_name in self.ws.docs and self.doc_name != doc.name:
            self.ws.close(self.doc_name)
        self.file_path = Path(res["path"])
        self.doc = doc
        self.doc_name = doc.name
        self.mtime = self.file_path.stat().st_mtime
        return {"document": self.file_path.name, "files": sorted(self.files()), "bodies": res.get("bodies", []),
                "parts": res.get("parts"), "warnings": res.get("warnings", [])}

    def open_project(self, target: str | Path) -> dict:
        """File -> Open folder...: switch the project folder, closing open documents and saving unsaved ones."""
        p = Path(target).expanduser().resolve()
        if p.is_file():
            p = p.parent
        if not p.is_dir():
            raise NotADirectoryError(f"not a directory: {p}")

        if getattr(self, "_agent", None) is not None:
            self._agent.close()
            self._agent = None

        for d in list(self.ws.docs.values()):
            try:
                if d.dirty():
                    d.save()
            except Exception:
                pass
        self.ws.close_all()

        self.path = p
        self.is_folder = True
        self.folder_path = p
        self.file_path = None
        self.doc = None
        self.doc_name = None
        self.mtime = None
        self._kind_cache.clear()
        self.ws = Workspace(p)
        self.ws.session = lambda: Session(allow_paths=[self.ws.root, self.tmp_dir])
        add_recent_folder(p)
        return self.project()

    def list_folders(self, req_path: str = "") -> dict:
        """List drives/roots, recent folders, subfolders with CAD file counts, and STEP files."""
        if req_path and req_path.strip():
            cur = Path(req_path.strip()).expanduser()
            if not cur.is_dir():
                if cur.is_file():
                    cur = cur.parent
                else:
                    cur = self.folder_path if self.folder_path and self.folder_path.is_dir() else Path.home()
        else:
            cur = self.folder_path if self.folder_path and self.folder_path.is_dir() else Path.home()

        try:
            cur = cur.resolve()
        except Exception:
            cur = Path.home().resolve()

        parent = str(cur.parent.resolve()) if cur.parent != cur else None

        recent_paths = load_recent_folders()
        recent = []
        for rp in recent_paths:
            try:
                p = Path(rp)
                if p.is_dir():
                    sc_count, step_count = _folder_counts(p)
                    recent.append({
                        "name": p.name or str(p),
                        "path": str(p),
                        "solidcraft_count": sc_count,
                        "step_count": step_count,
                    })
            except Exception:
                pass

        subfolders = []
        step_files = []
        try:
            for entry in cur.iterdir():
                if entry.name.startswith("."):
                    continue
                try:
                    if entry.is_dir():
                        sc_count, step_count = _folder_counts(entry)
                        subfolders.append({
                            "name": entry.name,
                            "path": str(entry.resolve()),
                            "solidcraft_count": sc_count,
                            "step_count": step_count,
                        })
                    elif entry.is_file() and entry.suffix.lower() in step_import.SUFFIXES:
                        step_files.append({
                            "name": entry.name,
                            "path": str(entry.resolve()),
                        })
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass

        subfolders.sort(key=lambda x: x["name"].lower())
        step_files.sort(key=lambda x: x["name"].lower())

        return {
            "current": str(cur),
            "parent": parent,
            "roots": _get_roots(),
            "recent": recent,
            "folders": subfolders,
            "step_files": step_files,
        }

    def server_close(self):
        try:
            super().server_close()
        finally:
            if getattr(self, "_agent", None) is not None:
                self._agent.close()
            with self.lock:
                self.ws.close_all()
                shutil.rmtree(self.tmp_dir, ignore_errors=True)


class UIRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    # polled every few seconds: in the session log only when they fail
    QUIET = ("/api/version", "/api/history", "/api/agent/events", "/api/log", "/api/project", "/api/files")

    def _log_api(self, status: int, payload: dict):
        url = urlparse(self.path)
        if not url.path.startswith("/api/") or (status < 400 and url.path in self.QUIET):
            return
        entry = {"method": self.command, "path": url.path + (f"?{url.query}" if url.query else ""), "status": status,
                 "ms": round((time.time() - getattr(self, "_t0", time.time())) * 1000)}
        if getattr(self, "_req_body", None) is not None:
            entry["body"] = self._req_body
        if isinstance(payload, dict):
            if payload.get("error"):
                entry["error"] = payload["error"]
            for k in ("done", "summary", "delta", "undone", "redone", "failing", "deleted"):
                if payload.get(k) not in (None, "", [], {}):
                    entry[k] = payload[k]
            if isinstance(payload.get("bodies"), list):
                entry["bodies"] = len(payload["bodies"])
            if isinstance(payload.get("findings"), list):
                entry["findings"] = len(payload["findings"])
        sessionlog.log("api", **entry)

    def _send_json(self, status: int, payload: dict):
        self._log_api(status, payload)
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def _check_security(self) -> bool:
        """Validate Host and Origin headers to guard against DNS rebinding and CSRF (issue #62)."""
        server_port = self.server.server_address[1]
        allowed_hosts = {
            f"127.0.0.1:{server_port}",
            f"localhost:{server_port}",
            f"[::1]:{server_port}",
        }
        if server_port == 80:
            allowed_hosts.update({"127.0.0.1", "localhost", "[::1]"})

        host = (self.headers.get("Host") or "").strip().lower()
        if not host or host not in allowed_hosts:
            self.close_connection = True
            self._send_json(403, {"error": f"forbidden host: {host or 'missing'}"})
            return False

        if self.command in ("POST", "PUT", "DELETE", "PATCH"):
            origin = self.headers.get("Origin")
            if origin is not None:
                origin_clean = origin.strip().lower()
                allowed_origins = {f"http://{h}" for h in allowed_hosts}
                if origin_clean not in allowed_origins:
                    self.close_connection = True
                    self._send_json(403, {"error": f"forbidden origin: {origin}"})
                    return False

            path = urlparse(self.path).path
            ct = self.headers.get("Content-Type") or ""
            media_type = ct.split(";")[0].strip().lower()
            if path.startswith("/api/file/"):
                if media_type not in ("application/octet-stream", "application/json"):
                    self.close_connection = True
                    self._send_json(403, {"error": f"unsupported content-type: {ct or 'missing'}"})
                    return False
            else:
                if media_type != "application/json":
                    self.close_connection = True
                    self._send_json(403, {"error": f"unsupported content-type: {ct or 'missing'}"})
                    return False

        self._security_checked = True
        return True

    def parse_request(self):
        if not super().parse_request():
            return False
        self._t0, self._req_body = time.time(), None
        if not self._check_security():
            return False
        return True

    def do_PUT(self):
        if not getattr(self, "_security_checked", False) and not self._check_security():
            return
        self._send_json(405, {"error": "method not allowed"})

    def do_DELETE(self):
        if not getattr(self, "_security_checked", False) and not self._check_security():
            return
        self._send_json(405, {"error": "method not allowed"})

    def _send_static(self, filename: str, content_type: str | None = None):
        root = STATIC_DIR.resolve()
        target = (root / unquote(filename)).resolve()
        if (root not in target.parents and target != root) or not target.is_file():
            self._send_json(404, {"error": f"file not found: {filename}"})
            return
        if content_type is None:
            content_type = "text/plain; charset=utf-8" if target.name == "LICENSE" else webapp.mime(target)
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str, cache: str = "no-store"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def _send_webapp(self, rel: str):
        target = webapp.resolve(rel)
        if target is None:
            self._send_json(404, {"error": f"not in the SolidCraft web build: {rel}"})
            return
        self._send_bytes(target.read_bytes(), webapp.mime(target), cache="no-cache")

    def _json_body(self, limit: int = 65536):
        length = int(self.headers.get("Content-Length") or 0)
        if length < 0 or length > limit:
            raise ValueError("invalid content length")
        if not length:
            return {}
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(body, dict):
            raise ValueError("expected a JSON object")
        self._req_body = body
        return body

    def _agent_post(self, srv, path):
        try:
            body = self._json_body()
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
            return
        turns = srv.agent
        if path == "/api/agent/send":
            text = body.get("text")
            if not isinstance(text, str) or not text.strip():
                self._send_json(400, {"error": "text required"})
                return
            doc = srv.file_path.name if srv.file_path else None
            try:
                sender = "developer" if body.get("from") == "developer" else "user"
                turn = turns.send(text.strip(), body.get("selection"), doc, sender=sender)
            except RuntimeError as e:
                self._send_json(409, {"error": str(e)})
                return
            self._send_json(200, {"turn": turn})
        elif path == "/api/agent/stop":
            self._send_json(200, {"stopping": turns.stop()})
        elif path in ("/api/agent/undo", "/api/agent/redo"):
            try:
                out = turns.undo(force=bool(body.get("force"))) if path.endswith("undo") else turns.redo()
            except LookupError as e:
                self._send_json(404, {"error": str(e)})
                return
            except (PermissionError, RuntimeError) as e:
                self._send_json(409, {"error": str(e)})
                return
            self._send_json(200, out)
        else:
            self._send_json(404, {"error": f"not found: {path}"})

    def _sketch_post(self, srv, action: str):
        """The sketch environment (sketch_session.py): begin, cmd, undo, finish, cancel, auto_project."""
        try:
            body = self._json_body() if action in ("begin", "cmd", "auto_project") else {}
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
            return
        with srv.lock:
            if action == "auto_project":
                val = body.get("value")
                if val is None:
                    val = body.get("project_edges", body.get("auto_project"))
                srv.auto_project = (not getattr(srv, "auto_project", True)) if val is None else bool(val)
                self._send_json(200, {"auto_project": srv.auto_project})
                return
            ss = getattr(srv, "sketch", None)
            try:
                if action == "begin":
                    if ss is not None:
                        raise sketch_session.SketchError(f"sketch {ss.name} is open: finish or cancel it first")
                    doc = srv.ensure_current()
                    if doc is None:
                        raise sketch_session.SketchError("no document open")
                    if doc.kind != PART:
                        raise PermissionError("sketches are drawn in a part; open the part file")
                    proj = body.get("project_edges")
                    if proj is None:
                        proj = body.get("auto_project")
                    if proj is None:
                        proj = getattr(srv, "auto_project", True)
                    srv.sketch = sketch_session.SketchSession.begin(
                        doc, srv.agent, plane=body.get("plane"), edit=body.get("edit"),
                        project_edges=bool(proj))
                    self._send_json(200, {**srv.sketch.state(), "auto_project": getattr(srv, "auto_project", True)})
                    return
                if ss is None:
                    raise sketch_session.SketchError("no sketch is open")
                if action == "cmd":
                    out = ss.command(body.get("command"), body.get("params") or {})
                elif action == "undo":
                    out = ss.undo_last()
                elif action in ("finish", "cancel"):
                    srv.sketch = None
                    out = ss.finish() if action == "finish" else ss.cancel()
                    srv.mtime = ss.doc.path.stat().st_mtime
                else:
                    self._send_json(404, {"error": f"unknown sketch action: {action}"})
                    return
            except sketch_session.SketchError as e:
                self._send_json(409, {"error": str(e)})
                return
            except agent_mod.Busy as e:
                self._send_json(409, {"error": str(e)})
                return
            except PermissionError as e:
                self._send_json(403, {"error": str(e)})
                return
            except Exception as e:  # SolidCraft refused it: the sketch is as it was
                resp = {"error": modeling.short_error(e), "detail": str(e)}
                exp = sc_errors.explain(e)
                if exp is not None:
                    resp.update(explanation=exp["message"], hint=exp["hint"])
                self._send_json(400, resp)
                return
        self._send_json(200, out)

    def do_POST(self):
        if not getattr(self, "_security_checked", False) and not self._check_security():
            return
        path = urlparse(self.path).path
        srv: UIServer = self.server  # type: ignore[assignment]
        self._t0, self._req_body = time.time(), None
        if path == "/api/closing":
            # the page goes away (window closed or reloaded): see _watch_closing
            srv.closing_at = time.time()
            self._send_json(200, {"ok": True})
            return
        srv.last_seen = time.time()
        try:
            if path == "/api/log":
                # what the browser reports for the session log: errors, dialogs, the status line
                try:
                    events = self._json_body(limit=262144).get("events") or []
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                for ev in events[:200]:
                    if isinstance(ev, dict):
                        data = {k: v for k, v in ev.items() if k not in ("t", "kind", "event")}
                        sessionlog.log("browser", event=ev.get("kind"), **data)
                self._send_json(200, {"logged": len(events)})
                return
            if path.startswith("/api/agent/"):
                self._agent_post(srv, path)
                return
            if path == "/api/quit":
                # Quit button in the UI: answer first, then stop serving (shutdown waits for the loop)
                self._send_json(200, {"stopped": True})
                threading.Thread(target=srv.shutdown, daemon=True).start()
                return
            if path == "/api/speech":
                try:
                    text = self._json_body().get("text")
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                if not isinstance(text, str):
                    self._send_json(400, {"error": "text required"})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    names = model_names(doc) if doc else []
                self._send_json(200, {"text": speech.normalize(text, names)})
                return
            if path == "/api/resolve_selection":
                try:
                    items = self._json_body().get("items") or []
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    self._send_json(200, {"selection": selection.resolve(srv.ws, doc, items)})
                return
            if path.startswith("/api/sketch/"):
                self._sketch_post(srv, path[len("/api/sketch/"):])
                return
            if srv.agent_busy() and path.startswith(("/api/file/", "/api/open/", "/api/project/open", "/api/new", "/api/import_step", "/api/params", "/api/rules",
                                                     "/api/feature", "/api/assembly/", "/api/visibility")):
                self._send_json(409, {"error": "the agent is working on the files; wait or stop it"})
                return
            if path in (
                "/api/assembly/insert",
                "/api/assembly/update_links",
                "/api/assembly/joint",
                "/api/assembly/joint/edit",
                "/api/assembly/constraint",
                "/api/assembly/joint/delete",
                "/api/assembly/standard",
                "/api/assembly/constraint/edit",
                "/api/assembly/bolted",
                "/api/assembly/bolted/preview",
                "/api/assembly/bolted/create",
                "/api/assembly/bolted/edit",
                "/api/assembly/bolted/delete",
            ):
                try:
                    raw_len = int(self.headers.get("Content-Length") or "0")
                    body = self._json_body() if raw_len else {}
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(400, {"error": "open an assembly first"})
                        return
                    if doc.kind != ASSEMBLY:
                        self._send_json(400, {"error": "open an assembly, not a part"})
                        return
                    try:
                        if path == "/api/assembly/insert":
                            result = assembly_insert(srv, doc, body)
                        elif path == "/api/assembly/joint":
                            result = assembly_add_joint(srv, doc, body)
                        elif path == "/api/assembly/joint/edit":
                            result = assembly_edit_joint(srv, doc, body)
                        elif path == "/api/assembly/standard":
                            result = assembly_place_standard(srv, doc, body)
                        elif path == "/api/assembly/joint/delete":
                            result = assembly_delete_joint(srv, doc, body)
                        elif path == "/api/assembly/constraint":
                            result = assembly_add_constraint(srv, doc, body)
                        elif path == "/api/assembly/constraint/edit":
                            result = assembly_edit_constraint(srv, doc, body)
                        elif path == "/api/assembly/update_links":
                            result = assembly_update_links(srv, doc, repair=bool(body.get("repair")))
                        elif path == "/api/assembly/bolted/preview":
                            result = assembly_bolted_preview(srv, doc, body)
                        elif path in ("/api/assembly/bolted", "/api/assembly/bolted/create"):
                            result = assembly_bolted_create(srv, doc, body)
                        elif path == "/api/assembly/bolted/edit":
                            result = assembly_bolted_edit(srv, doc, body)
                        else:
                            result = assembly_bolted_delete(srv, doc, body)
                    except agent_mod.Busy as e:
                        self._send_json(409, {"error": str(e)})
                        return
                    except _BoltedNotFoundError as e:
                        self._send_json(404, {"error": str(e)})
                        return
                    except Exception as e:
                        self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                        return
                self._send_json(200, result)
                return
            if path == "/api/params":
                try:
                    changes = self._json_body().get("changes")
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                if not isinstance(changes, dict) or not changes or not all(
                        isinstance(k, str) and isinstance(v, (str, int, float)) for k, v in changes.items()):
                    self._send_json(400, {"error": "changes: {name: expression, ...} required"})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    label = f"Parameters in {doc.name}: " + ", ".join(f"{k} = {v}" for k, v in changes.items())
                    try:
                        result = srv.agent.hand_step(label[:80], lambda: change_params(
                            doc, {k: str(v) for k, v in changes.items()}))
                        srv.mtime = doc.path.stat().st_mtime
                    except agent_mod.Busy as e:
                        self._send_json(409, {"error": str(e)})
                        return
                    except Exception as e:  # a bad expression: SolidCraft changed nothing
                        self._send_json(400, {"error": str(e)})
                        return
                self._send_json(200, result)
                return
            if path == "/api/feature":
                try:
                    body = self._json_body()
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                command, params = body.get("command"), body.get("params")
                if not isinstance(command, str) or not isinstance(params, dict):
                    self._send_json(400, {"error": "command and params required"})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    if command == "timeline.rename":
                        feature = params.get("feature")
                        name = params.get("name")
                        if not isinstance(feature, str) or not feature:
                            self._send_json(400, {"error": "feature required"})
                            return
                        if not isinstance(name, str) or not name.strip():
                            self._send_json(400, {"error": "name required"})
                            return
                        try:
                            result = rename_feature(srv, doc, feature, name)
                        except KeyError:
                            self._send_json(404, {"error": f"feature not found: {feature}"})
                            return
                        except PermissionError as e:
                            self._send_json(403, {"error": str(e)})
                            return
                        except ValueError as e:
                            self._send_json(400, {"error": str(e)})
                            return
                        except agent_mod.Busy as e:
                            self._send_json(409, {"error": str(e)})
                            return
                        except Exception as e:
                            self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                            return
                        self._send_json(200, result)
                        return
                    try:
                        result = run_feature(srv, doc, command, params, bool(body.get("preview")), srv.tmp_dir,
                                             edit=body.get("edit") if isinstance(body.get("edit"), str) else None)
                    except KeyError as e:
                        self._send_json(404, {"error": f"feature not found: {e.args[0]}"})
                        return
                    except PermissionError as e:
                        self._send_json(403, {"error": str(e)})
                        return
                    except agent_mod.Busy as e:
                        self._send_json(409, {"error": str(e)})
                        return
                    except Exception as e:  # SolidCraft refused it: the part is as it was
                        resp = {"error": modeling.short_error(e), "detail": str(e)}
                        exp = sc_errors.explain(e)
                        if exp is not None:
                            resp["explanation"] = exp["message"]
                            resp["hint"] = exp["hint"]
                        place = modeling.error_place(e)
                        if place:
                            resp["where"] = place["text"]
                            resp["location"] = dict(sc_locate.brief(place), kind=place.get("kind"))
                        self._send_json(400, resp)
                        return
                self._send_json(200, result)
                return
            if path == "/api/feature/delete":
                try:
                    payload = self._json_body()
                    name = payload.get("name")
                    keep_sketch = bool(payload.get("keep_sketch", False))
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                if not isinstance(name, str) or not name:
                    self._send_json(400, {"error": "name required"})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    try:
                        result = delete_feature(srv, doc, name, keep_sketch=keep_sketch)
                    except KeyError:
                        self._send_json(404, {"error": f"feature not found: {name}"})
                        return
                    except PermissionError as e:
                        self._send_json(403, {"error": str(e)})
                        return
                    except agent_mod.Busy as e:
                        self._send_json(409, {"error": str(e)})
                        return
                    except Exception as e:
                        self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                        return
                self._send_json(200, result)
                return
            if path == "/api/feature/rename":
                try:
                    body = self._json_body()
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                feature = body.get("feature") or body.get("old")
                name = body.get("name") or body.get("new")
                if not isinstance(feature, str) or not feature:
                    self._send_json(400, {"error": "feature required"})
                    return
                if not isinstance(name, str) or not name.strip():
                    self._send_json(400, {"error": "name required"})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    try:
                        result = rename_feature(srv, doc, feature, name)
                    except KeyError:
                        self._send_json(404, {"error": f"feature not found: {feature}"})
                        return
                    except PermissionError as e:
                        self._send_json(403, {"error": str(e)})
                        return
                    except ValueError as e:
                        self._send_json(400, {"error": str(e)})
                        return
                    except agent_mod.Busy as e:
                        self._send_json(409, {"error": str(e)})
                        return
                    except Exception as e:
                        self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                        return
                self._send_json(200, result)
                return
            if path == "/api/visibility":
                try:
                    body = self._json_body()
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                items = body.get("items")
                if items is None and "item" in body:
                    items = [body["item"]]
                if not isinstance(items, list) or not items:
                    self._send_json(400, {"error": "items list required"})
                    return
                vis_val = body.get("visible")
                if vis_val is None:
                    visible = True
                elif isinstance(vis_val, str):
                    visible = vis_val.lower() not in ("false", "0", "no")
                else:
                    visible = bool(vis_val)
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    try:
                        doc.session.cmd("browser.visibility", {"items": [str(it) for it in items], "visible": visible})
                        doc.save()
                        srv.mtime = doc.path.stat().st_mtime
                    except Exception as e:
                        self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                        return
                self._send_json(200, {"ok": True, "items": items, "visible": visible})
                return
            if path == "/api/rules":
                try:
                    body = self._json_body()
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None or doc.kind != PART:
                        self._send_json(409, {"error": "no part open"})
                        return
                    try:
                        design_rules.save_rules(doc, profile=body.get("profile") or None,
                                                material=body.get("material", None))
                        data = collect_findings(srv.ws, doc)
                    except ValueError as e:  # unknown profile or material: nothing saved
                        self._send_json(400, {"error": str(e)})
                        return
                self._send_json(200, data)
                return
            if path.startswith("/api/open/"):
                name = unquote(path[len("/api/open/"):])
                if not name:
                    self._send_json(404, {"error": "document name required"})
                    return
                with srv.lock:
                    try:
                        result = srv.open_document(name)
                    except KeyError:
                        self._send_json(404, {"error": f"document not found: {name}"})
                        return
                self._send_json(200, result)
                return

            if path == "/api/project/open":
                try:
                    body = self._json_body()
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                folder_str = str((body or {}).get("folder") or (body or {}).get("path") or "").strip()
                if not folder_str:
                    self._send_json(400, {"error": "folder path required"})
                    return
                if srv.agent_busy():
                    self._send_json(409, {"error": "agent is busy with a turn: wait for it to finish"})
                    return
                target = Path(folder_str).expanduser()
                if target.is_file():
                    target = target.parent
                try:
                    target = target.resolve()
                except Exception:
                    pass
                if not target.is_dir():
                    self._send_json(404, {"error": f"folder not found: {target}"})
                    return
                with srv.lock:
                    try:
                        result = srv.open_project(target)
                    except Exception as e:
                        self._send_json(400, {"error": str(e)})
                        return
                self._send_json(200, result)
                return

            if path == "/api/import_step":
                try:
                    body = self._json_body()
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                with srv.lock:
                    try:
                        file_val = str((body or {}).get("file") or "")
                        split_val = bool((body or {}).get("split"))
                        result = srv.import_step_document(file_val, split=split_val)
                    except KeyError as e:
                        self._send_json(404, {"error": f"no such STEP file: {e.args[0]}"})
                        return
                    except FileNotFoundError as e:
                        self._send_json(404, {"error": str(e)})
                        return
                    except FileExistsError as e:
                        self._send_json(409, {"error": str(e)})
                        return
                    except (NotADirectoryError, ValueError) as e:
                        self._send_json(400, {"error": str(e)})
                        return
                    except Exception as e:  # SolidCraft could not read the file
                        self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                        return
                self._send_json(200, result)
                return
            if path == "/api/new":
                if not srv.is_folder:
                    self._send_json(404, {"error": "new document only supported in folder mode"})
                    return
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0 or length > 65536:
                    self._send_json(400, {"error": "invalid content length"})
                    return
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    self._send_json(400, {"error": "invalid JSON body"})
                    return
                name = body.get("name") if isinstance(body, dict) else None
                if not name or not isinstance(name, str) or not name.strip():
                    self._send_json(400, {"error": "document name cannot be empty"})
                    return
                with srv.lock:
                    try:
                        result = srv.new_document(name.strip())
                    except ValueError as e:
                        self._send_json(400, {"error": str(e)})
                        return
                    except FileExistsError as e:
                        self._send_json(409, {"error": str(e)})
                        return
                self._send_json(200, result)
                return

            if path.startswith("/api/file/"):
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0 or length > MAX_UPLOAD:
                    self._send_json(413, {"error": f"expected 1 to {MAX_UPLOAD} bytes"})
                    return
                data = self.rfile.read(length)
                with srv.lock:
                    try:
                        result = srv.save(unquote(path[len("/api/file/"):]), data)
                    except KeyError:
                        self._send_json(404, {"error": "not a file of this document"})
                        return
                self._send_json(200, result)
                return

            self._send_json(404, {"error": f"unknown endpoint: {path}"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_GET(self):
        if not getattr(self, "_security_checked", False) and not self._check_security():
            return
        url = urlparse(self.path)
        path = url.path
        srv: UIServer = self.server  # type: ignore[assignment]
        self._t0, self._req_body = time.time(), None
        srv.last_seen = time.time()
        try:
            if path == "/api/agent/events":
                try:
                    since = int((parse_qs(url.query).get("since") or ["0"])[0])
                except ValueError:
                    since = 0
                self._send_json(200, srv.agent.events_since(max(0, since)))
                return
            if path in ("/", "/index.html"):
                self._send_static("index.html", "text/html; charset=utf-8")
                return
            if path == "/app.js":
                self._send_static("app.js", "application/javascript; charset=utf-8")
                return
            if path == "/chat.js":
                self._send_static("chat.js", "application/javascript; charset=utf-8")
                return
            if path == "/viewtools.js":
                self._send_static("viewtools.js", "application/javascript; charset=utf-8")
                return
            if path == "/request.js":
                self._send_static("request.js", "application/javascript; charset=utf-8")
                return
            if path == "/features.js":
                self._send_static("features.js", "application/javascript; charset=utf-8")
                return
            if path == "/sketchgeom.js":
                self._send_static("sketchgeom.js", "application/javascript; charset=utf-8")
                return
            if path == "/sketcher.js":
                self._send_static("sketcher.js", "application/javascript; charset=utf-8")
                return
            if path == "/newpart.js":
                self._send_static("newpart.js", "application/javascript; charset=utf-8")
                return
            if path == "/folder.js":
                self._send_static("folder.js", "application/javascript; charset=utf-8")
                return
            if path == "/style.css":
                self._send_static("style.css", "text/css; charset=utf-8")
                return
            if path in ("/model", "/model.html"):
                self._send_static("model.html", "text/html; charset=utf-8")
                return
            if path in ("/favicon.ico", "/logo.svg"):
                self._send_static(path.lstrip("/"))
                return
            if path.startswith("/vendor/"):
                self._send_static(path.lstrip("/"))
                return
            if path.startswith("/static/"):
                self._send_static(path[len("/static/"):])
                return
            if path.startswith("/sc/"):
                self._send_webapp(path[len("/sc/"):])
                return
            if path == "/api/project":
                with srv.lock:
                    data = srv.project()
                self._send_json(200, data)
                return
            if path == "/api/folders" or path.startswith("/api/folders?"):
                req_path = (parse_qs(url.query).get("path") or [""])[0]
                with srv.lock:
                    data = srv.list_folders(req_path)
                self._send_json(200, data)
                return
            if path == "/api/files":
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    names = sorted(srv.files())
                    parts = srv.placeable_parts()
                    doc_name = srv.file_path.name
                self._send_json(200, {"document": doc_name, "files": names, "parts": parts})
                return
            if path.startswith("/api/file/"):
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    target = srv.files().get(unquote(path[len("/api/file/"):]))
                if target is None:
                    self._send_json(404, {"error": "not a file of this document"})
                    return
                self._send_bytes(target.read_bytes(), "application/octet-stream")
                return

            if path == "/api/about":
                # root: which file or folder this server shows (only on 127.0.0.1), so a second
                # `mechvane ui` for the same folder opens a window here instead of a second server
                self._send_json(200, dict(collect_about(), root=str(srv.path), stops_with_window=srv.stops_with_window))
                return

            if path == "/api/params":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_params(doc)
                self._send_json(200, data)
                return

            if path == "/api/version":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_version(doc)
                self._send_json(200, data)
                return

            if path == "/api/feature":
                name = (parse_qs(url.query).get("name") or [""])[0]
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    try:
                        data = feature_for_edit(doc, name, srv.tmp_dir)
                    except KeyError:
                        self._send_json(404, {"error": f"feature not found: {name}"})
                        return
                    except PermissionError as e:
                        self._send_json(403, {"error": str(e)})
                        return
                self._send_json(200, data)
                return

            if path == "/api/sketch_plane":
                q = parse_qs(url.query)
                face = (q.get("face") or [""])[0]
                plane = {"face": [float(c) for c in face.split(",")]} if face else (q.get("plane") or ["XY"])[0]
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None or doc.kind != PART:
                        self._send_json(409, {"error": "no part open"})
                        return
                    try:
                        data = sketch_plane(doc, plane)
                    except Exception as e:
                        self._send_json(400, {"error": modeling.short_error(e)})
                        return
                self._send_json(200, data)
                return

            if path == "/api/sketch/state":
                with srv.lock:
                    ss = getattr(srv, "sketch", None)
                    auto_proj = getattr(srv, "auto_project", True)
                    if ss is None:
                        self._send_json(200, {"active": False, "auto_project": auto_proj})
                    else:
                        self._send_json(200, {"active": True, "auto_project": auto_proj, **ss.state()})
                return
            if path == "/api/sketches":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = sketches(doc)
                self._send_json(200, data)
                return

            if path == "/api/hole_sizes":
                self._send_json(200, hole_sizes())
                return

            if path == "/api/standard_parts":
                norm = (parse_qs(url.query).get("norm") or [None])[0]
                try:
                    data = collect_standard_parts(norm)
                except ValueError as e:
                    self._send_json(400, {"error": str(e)})
                    return
                self._send_json(200, data)
                return

            if path == "/api/assembly/bolted":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(400, {"error": "open an assembly first"})
                        return
                    if doc.kind != ASSEMBLY:
                        self._send_json(400, {"error": "open an assembly, not a part"})
                        return
                    data = assembly_bolted_list(srv, doc)
                self._send_json(200, data)
                return

            if path == "/api/history":
                self._send_json(200, srv.agent.history())
                return

            if path == "/api/mesh":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_mesh(doc, tmp_dir=srv.tmp_dir)
                self._send_json(200, data)
                return

            if path == "/api/tree":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_tree(srv.ws, doc)
                self._send_json(200, data)
                return

            if path == "/api/assembly/context":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    if doc.kind != ASSEMBLY:
                        self._send_json(400, {"error": "open an assembly, not a part"})
                        return
                    data = collect_assembly_context(srv.ws, doc)
                self._send_json(200, data)
                return

            if path == "/api/findings":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    q = parse_qs(url.query)
                    # without a choice in the request the part's saved profile and material apply
                    profile = (q.get("profile") or [None])[0] or None
                    material = (q.get("material") or [None])[0] or None
                    try:
                        data = collect_findings(srv.ws, doc, profile=profile, material=material)
                    except ValueError as e:  # unknown profile or material
                        self._send_json(400, {"error": str(e)})
                        return
                self._send_json(200, data)
                return

            self._send_json(404, {"error": f"unknown endpoint: {path}"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def create_server(path, port: int = 8765, host: str = "127.0.0.1") -> UIServer:
    """Create a UIServer bound to host:port for the given .solidcraft file or project folder."""
    return UIServer((host, port), UIRequestHandler, path)


def _running_ui(port: int) -> str | None:
    """The file or folder a Mechvane UI on 127.0.0.1:<port> shows, or None (none there, or another program)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/about", timeout=2) as r:
            return json.loads(r.read()).get("root")
    except Exception:
        return None


def run_server(path, port: int = 8765, opener=None):
    """Run the UI server on 127.0.0.1:<port> until interrupted.

    A busy port falls back to a free one, unless a Mechvane UI for the same file or folder already
    listens there: then only opener(url) runs (a second click on the start menu entry opens a window,
    not a second server). opener(url, stop) is called once the server listens; stop() ends the server
    (used when the app window is closed)."""
    try:
        srv = create_server(path, port=port, host="127.0.0.1")
    except OSError:
        if not port:
            raise
        running = _running_ui(port)
        if running and Path(running).resolve() == Path(path).resolve():
            url = f"http://127.0.0.1:{port}/"
            print(f"Mechvane UI already running at {url}", flush=True)
            if opener:
                opener(url, lambda: None)
            return
        srv = create_server(path, port=0, host="127.0.0.1")
    actual_port = srv.server_address[1]
    target_name = srv.folder_path.name if srv.is_folder else srv.file_path.name
    url = f"http://127.0.0.1:{actual_port}/"
    try:
        from importlib.metadata import version as _version
        mv = _version("mechvane")
    except Exception:
        mv = "dev"
    # remote debugging finds the port and the project here (tools/remote_debug.py)
    sessionlog.log("ui_start", port=actual_port, path=str(srv.path), mechvane=mv, pid=os.getpid())
    print(f"Mechvane UI running at {url} ({target_name})", flush=True)
    if opener:
        def open_ui():
            mode = opener(url, srv.shutdown)
            srv.stops_with_window = mode == "window"
            # a window handed to an app window that was already open closes the same way: the page says
            # "closing" (seen on the Surface 2026-11-06: a second instance kept its Python and solidcraft-cli
            # running after all windows were closed); only the instance that opened Chrome closes its windows
            if mode in ("window", "handoff"):
                threading.Thread(target=_watch_closing, args=(srv,), daemon=True).start()
        threading.Thread(target=open_ui, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        sessionlog.log("ui_stop", port=actual_port)
        srv.server_close()
        if srv.stops_with_window:
            from . import appwindow
            appwindow.close_windows()  # Chrome keeps the window's process alive in the background on Windows


CLOSING_GRACE_S = 8


def _watch_closing(srv):
    """Stop the server when its app window was closed. The browser process cannot tell (Chrome keeps running in
    the background on Windows after its last window closed), so the page says "closing" when it goes away; a
    reload asks again within seconds, a closed window does not."""
    while True:
        time.sleep(2)
        closing = getattr(srv, "closing_at", None)
        if closing and time.time() - closing > CLOSING_GRACE_S and getattr(srv, "last_seen", 0) <= closing:
            sessionlog.log("ui_window_closed")
            srv.shutdown()
            return
