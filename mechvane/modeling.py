"""One way to run modelling commands in a document, for the agent (MCP `run`) and the user's own
dialogs in the web UI (`/api/feature`): all or nothing, sketch rule, state delta, explained errors."""

import json

from . import sc_errors, sketch_rule, state_delta
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
    if doc.kind == PART:
        try:
            cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        except Exception:
            cp = None
        try:
            snap_before = state_delta.snapshot(doc.session)
        except Exception:
            snap_before = None
    try:
        result = doc.session.batch(commands)
    except Exception as e:
        if cp is not None:
            _restore(doc.session, cp)
        sc_errors.reraise(e)

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


def short_error(e) -> str:
    """One readable line for a dialog: Mechvane's explanation (when known) and SolidCraft's own words,
    which often name the size that would fit, without the raw batch reply."""
    text = str(e)
    head, _, rest = text.partition("\n")
    raw = text if head.lstrip().startswith("{") else rest
    inner = None
    try:
        failed = json.loads(raw).get("failed") or {}
        inner = failed.get("error")
    except (ValueError, AttributeError):
        pass
    if inner:
        inner = inner.split(": ", 1)[1] if inner.startswith("not supported yet: ") else inner
        inner = inner[:1].upper() + inner[1:]
    if head.lstrip().startswith("{"):
        return inner or head
    if not inner:
        return head
    # SolidCraft's words are concrete (sizes that fit); the general hint in brackets can go
    message = head[:head.rfind(" (")] if head.endswith(")") and " (" in head else head
    return f"{message} SolidCraft: {inner}"
