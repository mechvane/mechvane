"""Sketch ownership, Inventor style: a sketch used by exactly one feature belongs to it and
sits directly before it in the history. Work features (construction planes, axes, points) used
by exactly one sketch or feature belong to it the same way. Shared ones stay rows of their own.
Uses are read from the feature definitions; deleting checks timeline.dependents as well, for uses
a definition does not show (projections inside a sketch)."""


from .solidcraft import SolidCraftError


def timeline(s):
    return s.tool("inspect_design", {"measure": False, "sketches": False})


def is_work_feature(f):
    return f["type"].startswith("Construction")


def references(definition, ids):
    """Names of the sketches and work features a feature definition (timeline.inspect, or a sketch's
    links from sketch.inspect) refers to: sketches by id ("sketch": 2), work features by name
    ({"type": "construction" or "plane", "name": "WP1"}; origin planes are filtered out later)."""
    out = set()

    def walk(v):
        if isinstance(v, dict):
            # A work feature by name (up to 0.21) or by feature id ("feature": 1, since 0.25)
            if v.get("type") in ("construction", "plane", "axis", "point") and ("name" in v or "id" in v or "feature" in v):
                out.add(v["name"] if "name" in v else ids.get(v.get("id", v.get("feature"))))
            for k, x in v.items():
                if k in ("sketch", "path_sketch") and isinstance(x, int):
                    out.add(ids.get(x))
                elif k in ("sketch", "path_sketch") and isinstance(x, str) and x in ids.values():
                    out.add(x)
                elif k == "sketches" and isinstance(x, list):
                    for sk in x:
                        if isinstance(sk, int):
                            out.add(ids.get(sk))
                        elif isinstance(sk, str) and sk in ids.values():
                            out.add(sk)
                        else:
                            walk(sk)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(definition)
    out.discard(None)
    return out


def consumers(s, tl=None):
    """{sketch or work feature: [names of what uses it directly]} for the whole history, read from
    the feature definitions, so suppressed and rolled-back users count too."""
    tl = tl if tl is not None else timeline(s)["timeline"]
    ids = {f["id"]: f["name"] for f in tl}
    out = {f["name"]: [] for f in tl if f["type"] == "Sketch" or is_work_feature(f)}
    for f in tl:
        defn = s.cmd("timeline.inspect", {"feature": f["id"]}).get("definition", {})
        if f["type"] == "Sketch":  # projections live in the sketch itself
            try:
                defn = [defn, s.cmd("sketch.inspect", {"sketch": f["id"]}).get("links", [])]
            except SolidCraftError:  # not evaluated (rolled back, suppressed): its projections are unknown
                pass
        for ref in sorted(references(defn, ids) - {f["name"]}):
            if ref in out:
                out[ref].append(f["name"])
    return out


def owners(cons):
    """{sketch or work feature: its owner} for those with exactly one direct user."""
    return {sk: users[0] for sk, users in cons.items() if len(users) == 1}


def owned_by(own, feature):
    """Everything `feature` owns, directly or through its sketch, nearest first."""
    out = [x for x, o in own.items() if o == feature]
    for x in list(out):
        out += owned_by(own, x)
    return out


def enforce(s):
    """Move everything owned directly before its owner: a feature's own sketches and work features
    stand as one block right before it, a sketch's own work plane right before the sketch.
    Returns what was moved and what SolidCraft refused to move."""
    moved, refused = [], []
    for _ in range(200):
        tl = timeline(s)["timeline"]
        index = {f["name"]: i for i, f in enumerate(tl)}
        own = owners(consumers(s, tl))
        todo = None
        for item, owner in own.items():
            if item in refused:
                continue
            i, j = index[item], index[owner]
            block = set(owned_by(own, owner))
            if i < j and all(f["name"] in block for f in tl[i + 1:j]):
                continue
            todo = (item, owner, j - 1 if i < j else j)
            break
        if todo is None:
            return {"moved": moved, "refused": refused}
        item, owner, position = todo
        try:
            s.cmd("timeline.reorder", {"feature": item, "position": position})
            moved.append({"sketch": item, "before": owner})
        except Exception:  # noqa: BLE001 - SolidCraft refuses moves that would break a feature
            refused.append(item)
    raise RuntimeError("sketch rule did not settle")


def delete_with_owned(s, feature):
    """Delete `feature` and what it owns, nearest first. An owned item something else still needs
    (a use the ownership rule cannot see) is kept."""
    owned = owned_by(owners(consumers(s)), feature)
    s.cmd("timeline.delete", {"features": [feature]})
    deleted, kept = [feature], []
    for item in owned:
        d = s.cmd("timeline.dependents", {"feature": item})
        if set(d.get("deleted_with_it", []) + d.get("would_fail", [])) - set(deleted):
            kept.append(item)
        else:
            s.cmd("timeline.delete", {"features": [item]})
            deleted.append(item)
    return {"deleted": deleted, "kept": kept}
