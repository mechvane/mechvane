"""One way to run modelling commands in a document, for the agent (MCP `run`) and the user's own
dialogs in the web UI (`/api/feature`): all or nothing, sketch rule, state delta, explained errors."""

import json

from . import links, sc_errors, sc_locate, sketch_rule, state_delta
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
    if doc.kind == PART:
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


def add_joint(ws, doc, params: dict) -> dict:
    """Create a joint via SolidCraft joint.create (`name` required) and record both side anchors
    with links.record so update_links / check_joints can verify it later."""
    if not params.get("name"):
        raise ValueError("give the joint a name")
    resolved = links.resolve_occurrences(doc.session, params)
    r = doc.session.cmd("joint.create", resolved)
    anchors = links.record(ws, doc, resolved["name"], resolved)
    return {"joint": r, "anchors": anchors["sides"]}


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
