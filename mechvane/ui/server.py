"""Local HTTP server (127.0.0.1) and data collection functions for the Mechvane Web-UI."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, unquote, urlparse
import zipfile

from .. import design_rules, hole_tables, links, modeling, query, sketch_rule, speech, tree
from . import agent as agent_mod, selection, sessionlog, webapp
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


PARAM_KEYS = ("name", "expression", "unit", "value", "source", "feature", "input", "comment", "favorite", "error")


def collect_params(doc) -> dict:
    """The document's parameters for the form: user parameters first, then feature dimensions."""
    listed = doc.session.cmd("parameters.list", {})
    params = [{k: p.get(k) for k in PARAM_KEYS if k in p} for p in listed.get("parameters", [])]
    params.sort(key=lambda p: (p.get("source") != "user", not p.get("favorite")))
    return {"parameters": params}


def change_params(doc, changes: dict) -> dict:
    """Set several parameters at once (all or nothing in SolidCraft) and save the document."""
    result = doc.session.cmd("parameters.change", {"changes": changes})
    doc.save()
    return dict(collect_params(doc), changed=result.get("changed", {}))


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
        made = s.cmd("sketch.create", {"plane": plane})
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
        doc.session.cmd("sketch.create", {"plane": plane})
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


def sketches(doc) -> dict:
    """The part's sketches for Extrude and Revolve (oldest first), with what already uses each."""
    if doc.kind != PART:
        return {"sketches": []}
    used = sketch_rule.consumers(doc.session)
    return {"sketches": [{"name": f["name"], "used_by": sorted(used.get(f["name"]) or [])}
                         for f in _timeline(doc) if f["type"] == "Sketch"]}


def _timeline(doc) -> list[dict]:
    return doc.session.cmd("document.inspect", {"measure": False}).get("timeline", [])


def _errors(doc) -> dict:
    return {f["name"]: f["error"] for f in _timeline(doc) if f.get("error")}


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
    return {"name": name, "type": info.get("type"), "dialog": EDITABLE[info["type"]][0],
            "definition": info.get("definition") or {}, "before": before, "feature_names": names}


def delete_feature(srv, doc, name: str) -> dict:
    """Delete a feature from the model browser, with the sketch it owns (as the agent's delete_feature)."""
    if doc.kind != PART:
        raise PermissionError("features are deleted in a part")
    if name not in {f["name"] for f in _timeline(doc)}:
        raise KeyError(name)

    def apply():
        failing_before = _errors(doc)
        out = sketch_rule.delete_with_owned(doc.session, name)
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        out["failing"] = {k: v for k, v in _errors(doc).items() if k not in failing_before}
        return out

    out = srv.agent.hand_step(f"Delete {name} in {doc.name}", apply)
    return {"done": f"Deleted {', '.join(out['deleted'])}", **out}


def run_feature(srv, doc, command: str, params: dict, preview: bool, tmp_dir, edit: str | None = None) -> dict:
    """Run one dialog command in the open part. preview: run it, return the mesh, take it back
    (nothing saved). Otherwise run, save, and record the step for Undo. With edit (a feature name) the
    feature is changed in place (timeline.edit) instead of a new one added."""
    if command not in FEATURE_COMMANDS:
        raise PermissionError(f"command not available in the workspace: {command}")
    if doc.kind != PART:
        raise PermissionError("features are added in a part; open the part file")
    commands = [{"command": command, "params": params}]
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
        commands = [{"command": "timeline.edit", "params": {"feature": edit, "set": set_}}]
    if preview:
        failing_before = _errors(doc) if edit else {}
        cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        try:
            out = modeling.run_commands(doc, commands)
            new = {k: v for k, v in _errors(doc).items() if k not in failing_before} if edit else {}
            if new:
                raise RuntimeError("; ".join(f"{k}: {v}" for k, v in new.items()))
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
                raise RuntimeError("; ".join(f"{k}: {v}" for k, v in new.items()))
            doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
        doc.save()
        srv.mtime = doc.path.stat().st_mtime
        return out

    label = f"{FEATURE_COMMANDS[command](params)} in {doc.name}"
    if edit:
        label = f"Edit {edit}: {label}"
    out = srv.agent.hand_step(label, apply)
    return {"done": label, "delta": out.get("delta"), "results": out.get("results")}


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

    def do_POST(self):
        path = urlparse(self.path).path
        srv: UIServer = self.server  # type: ignore[assignment]
        self._t0, self._req_body = time.time(), None
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
            if srv.agent_busy() and path.startswith(("/api/file/", "/api/open/", "/api/new", "/api/params", "/api/rules",
                                                     "/api/feature")):
                self._send_json(409, {"error": "the agent is working on the files; wait or stop it"})
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
                        self._send_json(400, {"error": modeling.short_error(e), "detail": str(e)})
                        return
                self._send_json(200, result)
                return
            if path == "/api/feature/delete":
                try:
                    name = self._json_body().get("name")
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
                        result = delete_feature(srv, doc, name)
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
        url = urlparse(self.path)
        path = url.path
        srv: UIServer = self.server  # type: ignore[assignment]
        self._t0, self._req_body = time.time(), None
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
            if path == "/newpart.js":
                self._send_static("newpart.js", "application/javascript; charset=utf-8")
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
            if path == "/api/files":
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    names = sorted(srv.files())
                    doc_name = srv.file_path.name
                self._send_json(200, {"document": doc_name, "files": names})
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
            srv.stops_with_window = opener(url, srv.shutdown) == "window"
        threading.Thread(target=open_ui, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
