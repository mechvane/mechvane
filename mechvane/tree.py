"""The model browser, Inventor style: a part's features with their sketches under them and
the end-of-part marker; an assembly's occurrences with their joints under each of them."""

from pathlib import Path

from . import read_metadata
from .sketch_rule import consumers, is_work_feature, owners, timeline


def part_tree(s, groups=False):
    """With groups, the same ownership also as Fusion-style folders: every sketch and work
    feature once, with the feature it belongs to (or what shares it)."""
    insp = timeline(s)
    tl = insp["timeline"]
    marker = insp.get("marker")
    end = len(tl) if marker is None else marker
    cons = consumers(s, tl)
    owned = owners(cons)
    by_feature = {}
    for sketch, feature in owned.items():
        by_feature.setdefault(feature, []).append(sketch)
    kinds = {f["name"]: f for f in tl}

    def with_children(n):
        children = [with_children(node(kinds[sk])) for sk in by_feature.get(n["name"], [])]
        if children:
            n["children"] = children
        return n

    def node(f):
        n = {"name": f["name"], "type": f["type"]}
        for key in ("suppressed", "rolled_back"):
            if f.get(key):
                n[key] = True
        if f.get("error"):
            n["error"] = f["error"]
        return n

    items = []
    for i, f in enumerate(tl):
        if i == end:
            items.append({"type": "EndOfPart"})
        if f["name"] in owned:
            continue
        items.append(with_children(node(f)))
    if end >= len(tl):
        items.append({"type": "EndOfPart"})
    out = {"kind": "part", "name": insp.get("name"), "bodies": [b["name"] for b in insp.get("bodies", [])],
           "features": items}
    if groups:
        def entry(f):
            users = cons.get(f["name"], [])
            use = {"owner": users[0]} if len(users) == 1 else {"shared_by": users} if users else {"unused": True}
            return dict(node(f), **use)
        out["groups"] = {"sketches": [entry(f) for f in tl if f["type"] == "Sketch"],
                         "work_features": [entry(f) for f in tl if is_work_feature(f)]}
    return out


def assembly_tree(s, groups=False):
    comps = s.cmd("component.list")["components"]
    by_id = {c["id"]: c for c in comps}
    root = next(c for c in comps if c["parent"] is None)
    links = {link["component"]: link for link in s.cmd("component.links").get("links", [])}
    joints = s.cmd("joint.list").get("joints", [])
    meta = read_metadata(s.cmd("document.metadata").get("metadata"))
    subs = {}
    for k, info in (meta.get("subassemblies") or {}).items():
        subs[info.get("component")] = info
        subs[k] = info
    names, parent_occ = {}, {}
    first_occ = {c["id"]: c["occurrences"][0]["name"] for c in comps if c.get("occurrences")}
    for c in comps:
        for o in c.get("occurrences", []) + c.get("children", []):
            names[o["id"]] = o["name"]
            if o.get("parent", 0) != 0 and o["parent"] in first_occ:
                parent_occ[o["id"]] = first_occ[o["parent"]]

    def occ_node(o):
        comp = by_id.get(o["component"], {})
        n = {"name": o["name"], "grounded": bool(o.get("grounded"))}
        link = links.get(o["component"])
        sub = subs.get(o["component"]) or subs.get(comp.get("name"))
        if link:
            n["file"] = link.get("path")
            if not link.get("found", True):
                n["file_missing"] = True
        elif sub and sub.get("file"):
            n["file"] = sub.get("path") or Path(sub["file"]).name
            if not Path(sub["file"]).is_file():
                n["file_missing"] = True
        mine = []
        for j in joints:
            if o["id"] in (j["a"], j["b"]):
                partner = j["b"] if j["a"] == o["id"] else j["a"]
                entry = {"name": j["name"], "type": j["type"], "with": names.get(partner, partner)}
                if j.get("suppressed"):
                    entry["suppressed"] = True
                mine.append(entry)
        if mine:
            n["joints"] = mine
        children = comp.get("children", [])
        if children or sub:
            n["occurrences"] = [occ_node(ch) for ch in children]
        return n

    feat_nodes = []
    root_feats = root.get("features", [])
    if root_feats:
        tl_map = {f["name"]: f for f in timeline(s).get("timeline", [])}
        for f in root_feats:
            if isinstance(f, dict):
                feat_nodes.append(f)
            elif f in tl_map:
                tf = tl_map[f]
                n = {"name": tf["name"], "type": tf["type"]}
                for key in ("suppressed", "rolled_back"):
                    if tf.get(key):
                        n[key] = True
                if tf.get("error"):
                    n["error"] = tf["error"]
                feat_nodes.append(n)
            else:
                feat_nodes.append({"name": str(f), "type": "Feature"})

    out = {"kind": "assembly", "name": root["name"],
           "occurrences": [occ_node(o) for o in root.get("children", [])],
           "assembly_features": feat_nodes}
    if groups:
        rels = []
        for j in joints:
            r = {"name": j["name"], "type": j["type"], "between": [names.get(j["a"], j["a"]), names.get(j["b"], j["b"])]}
            if parent_occ.get(j["a"]) and parent_occ.get(j["a"]) == parent_occ.get(j["b"]):
                r["owner"] = parent_occ[j["a"]]
            if j.get("suppressed"):
                r["suppressed"] = True
            rels.append(r)
        out["groups"] = {"relations": rels}
    return out


def render(tree):
    """Plain-text browser, as the Inventor model browser would show it."""
    lines = [f"{tree['name']} ({'Bauteil' if tree['kind'] == 'part' else 'Baugruppe'})"]
    if tree["kind"] == "part":
        for n in tree["features"]:
            if n["type"] == "EndOfPart":
                lines.append("  ── Bauteilende ──")
                continue
            _lines(lines, n, 1)
        if tree["bodies"]:
            lines.append("  Körper: " + ", ".join(tree["bodies"]))
    else:
        for o in tree["occurrences"]:
            _occ_lines(lines, o, 1)
        for f in tree.get("assembly_features", []):
            _lines(lines, f if isinstance(f, dict) else {"name": str(f), "type": "Feature"}, 1)
    g = tree.get("groups")
    if g:
        titles = {"sketches": "Skizzen", "work_features": "Arbeitselemente", "relations": "Beziehungen"}
        for key, rows in g.items():
            lines.append(f"  [{titles[key]}]")
            for r in rows:
                if "between" in r:
                    where = " ↔ ".join(r["between"]) + (f" (→ {r['owner']})" if "owner" in r else "")
                elif "owner" in r:
                    where = "→ " + r["owner"]
                else:
                    where = "geteilt: " + ", ".join(r["shared_by"]) if "shared_by" in r else "unbenutzt"
                lines.append(f"    {_label(r)} {where}")
    return "\n".join(lines)


def _occ_lines(lines, o, depth):
    pad = "  " * depth
    extra = []
    if o["grounded"]:
        extra.append("fest")
    if o.get("file"):
        extra.append(o["file"] + (" FEHLT" if o.get("file_missing") else ""))
    lines.append(f"{pad}{o['name']}" + (f" ({', '.join(extra)})" if extra else ""))
    for j in o.get("joints", []):
        lines.append(f"{pad}  ◆ {j['name']} [{j['type']}] → {j['with']}" + (" (unterdrückt)" if j.get("suppressed") else ""))
    for ch in o.get("occurrences", []):
        _occ_lines(lines, ch, depth + 1)


def _lines(lines, n, depth):
    lines.append("  " * depth + _label(n))
    for c in n.get("children", []):
        _lines(lines, c, depth + 1)


def _label(n):
    flags = [k for k in ("suppressed", "rolled_back") if n.get(k)]
    text = f"{n['name']} [{n['type']}]"
    if flags:
        text += " (" + ", ".join({"suppressed": "unterdrückt", "rolled_back": "nach Bauteilende"}[f] for f in flags) + ")"
    if n.get("error"):
        text += f" FEHLER: {n['error']}"
    return text
