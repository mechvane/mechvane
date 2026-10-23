"""In-place editing of parts within an assembly: open part files by occurrence,
track transforms between assembly and part coordinate systems, and update linked assemblies."""

from pathlib import Path

from . import geometry as g
from .documents import ASSEMBLY
from .links import _links, _occurrences, update_links


def _match_name(cand_name: str, query: str, parent_comp_name: str | None = None) -> bool:
    """Match candidate occurrence or component name against query.
    Rules (Finding 9):
    1. Exact match: cand_name == query
    2. Name with ':<n>': cand_name.split(':')[0] == query if query has no ':',
       or exact instance index match if query has ':<n>'.
    3. '<Component>_<Name>': cand_name == f"{parent_comp_name}_{query}"
       or cand_name.split(':')[0] == f"{parent_comp_name}_{query}" (with matching index).
    No delimiterless prefix match (e.g. 'Plate' must not match 'PlateWasher:1')."""
    if cand_name == query:
        return True
    c_base, _, c_idx = cand_name.partition(":")
    q_base, _, q_idx = query.partition(":")
    if q_idx:
        if c_idx != q_idx:
            return False
        if c_base == q_base:
            return True
        if parent_comp_name and c_base == f"{parent_comp_name}_{q_base}":
            return True
        return False
    if c_base == q_base:
        return True
    if parent_comp_name and c_base == f"{parent_comp_name}_{q_base}":
        return True
    return False


def resolve_occurrence(doc, occurrence: str | int) -> dict:
    """Resolve an occurrence identifier in an assembly (e.g. 'Plate:1', 'Sub:1/Plate:1', 'Sub_Plate:1',
    or component/occurrence id) to its occurrence record and backing file path.
    Returns: {'id': int, 'name': str, 'component': int, 'transform': 4x4, 'file': str}"""
    if doc.kind != ASSEMBLY:
        raise ValueError(f"{doc.name!r} is a {doc.kind}, not an assembly")

    occs = _occurrences(doc.session)
    by_name = {o["name"]: o for o in occs.values()}
    lmap = _links(doc.session)
    meta = doc.metadata()
    subs = meta.get("subassemblies") or {}

    def _file_for(occ):
        link = lmap.get(occ["component"])
        if link and link.get("file"):
            return link["file"]
        for sinfo in subs.values():
            for pinfo in sinfo.get("parts", {}).values():
                if pinfo.get("occurrence") == occ["name"] or pinfo.get("component") == occ["component"]:
                    if pinfo.get("file"):
                        return pinfo["file"]
            if sinfo.get("component") == occ["component"] or sinfo.get("occurrence") == occ["name"]:
                if sinfo.get("file"):
                    return sinfo["file"]
        return None

    # Case 1: Occurrence specified as path (e.g. "Sub:1/Plate:1" or "Sub/Plate" or "Sub2:1/Sub1B:1/PartP:1")
    if "/" in str(occurrence):
        parts = [p.strip() for p in str(occurrence).split("/") if p.strip()]
        if len(parts) >= 2:
            comps = {c["id"]: c for c in doc.session.cmd("component.list")["components"]}
            root = next((c for c in comps.values() if c.get("parent") is None or c["id"] == 0), None)
            curr = root
            matched_ch = None
            found_by_walk = True
            for seg in parts:
                children = curr.get("children", []) if curr else []
                matches = [ch for ch in children if _match_name(ch["name"], seg, curr.get("name") if curr else None)]
                if len(matches) > 1:
                    raise ValueError(f"ambiguous occurrence segment {seg!r} in path {occurrence!r}: multiple matches {[m['name'] for m in matches]}")
                if len(matches) == 1:
                    matched_ch = matches[0]
                    curr = comps.get(matched_ch["component"])
                else:
                    found_by_walk = False
                    break

            if found_by_walk and matched_ch:
                occ = by_name.get(matched_ch["name"]) or occs.get(matched_ch["id"])
                if occ:
                    f = _file_for(occ)
                    if f:
                        return {
                            "id": occ["id"],
                            "name": occ["name"],
                            "component": occ["component"],
                            "transform": occ["transform"],
                            "file": f,
                        }

            # Fallback for subassembly metadata matching
            parent_ref, leaf = parts[0], parts[-1]
            sinfo = None
            for sname, info in subs.items():
                if _match_name(sname, parent_ref) or _match_name(info.get("occurrence", ""), parent_ref):
                    sinfo = info
                    break
            if sinfo and sinfo.get("parts"):
                sparts = sinfo["parts"]
                matches = [p for k, p in sparts.items() if _match_name(k, leaf, sinfo.get("name")) or _match_name(p.get("occurrence", ""), leaf, sinfo.get("name"))]
                if len(matches) > 1:
                    raise ValueError(f"ambiguous leaf {leaf!r} in subassembly {parent_ref!r}")
                if len(matches) == 1:
                    target_pinfo = matches[0]
                    occ = by_name.get(target_pinfo["occurrence"])
                    if occ:
                        return {
                            "id": occ["id"],
                            "name": occ["name"],
                            "component": occ["component"],
                            "transform": occ["transform"],
                            "file": target_pinfo["file"],
                        }

    # Case 2: Direct occurrence name, id or component prefix
    occ = None
    if isinstance(occurrence, int) or str(occurrence).isdigit():
        occ = occs.get(int(occurrence))
    elif occurrence in by_name:
        occ = by_name[occurrence]
    else:
        matches = [o for o in occs.values() if _match_name(o["name"], str(occurrence), None)]
        if len(matches) > 1:
            raise ValueError(f"ambiguous occurrence {occurrence!r}: multiple matches {[m['name'] for m in matches]}")
        if len(matches) == 1:
            occ = matches[0]

    # Check if occurrence matches a part in subassemblies metadata
    if not occ:
        sub_matches = []
        for sinfo in subs.values():
            sparts = sinfo.get("parts", {})
            for k, p in sparts.items():
                if _match_name(k, str(occurrence), sinfo.get("name")) or _match_name(p.get("occurrence", ""), str(occurrence), sinfo.get("name")):
                    sub_matches.append((p, sinfo))
        if len(sub_matches) > 1:
            raise ValueError(f"ambiguous occurrence {occurrence!r} in subassemblies: multiple matches")
        if len(sub_matches) == 1:
            target_pinfo, _ = sub_matches[0]
            if target_pinfo["occurrence"] in by_name:
                occ = by_name[target_pinfo["occurrence"]]
                return {
                    "id": occ["id"],
                    "name": occ["name"],
                    "component": occ["component"],
                    "transform": occ["transform"],
                    "file": target_pinfo["file"],
                }

    if occ:
        f = _file_for(occ)
        if f:
            return {
                "id": occ["id"],
                "name": occ["name"],
                "component": occ["component"],
                "transform": occ["transform"],
                "file": f,
            }

    raise ValueError(f"occurrence {occurrence!r} not found or not backed by a file in assembly {doc.name!r}")


def to_part_coords(point: list[float], transform: list[list[float]]) -> list[float]:
    """Convert a 3D point [x, y, z] from assembly coordinates to part coordinates."""
    if not isinstance(point, (list, tuple)) or len(point) != 3 or not all(isinstance(x, (int, float)) for x in point):
        raise ValueError(f"point must be a 3D coordinate [x, y, z], got {point!r}")
    inv = g.invert_rigid(transform)
    return g.apply_point(inv, point)


def to_assembly_coords(point: list[float], transform: list[list[float]]) -> list[float]:
    """Convert a 3D point [x, y, z] from part coordinates to assembly coordinates."""
    return g.apply_point(transform, point)


def edit_in_place(ws, assembly: str, occurrence: str, point: list[float] | None = None) -> dict:
    """Open the part file behind an occurrence in an assembly for editing. If the document is already
    open, returns the existing document. Returns document name and the occurrence transform."""
    asm_doc = ws.get(assembly, ASSEMBLY)
    target = resolve_occurrence(asm_doc, occurrence)
    target_path = Path(target["file"]).resolve()

    part_doc = None
    for d in ws.docs.values():
        if d.path.resolve() == target_path:
            part_doc = d
            break
    if part_doc is None:
        name = target_path.stem
        if name in ws.docs and ws.docs[name].path.resolve() != target_path:
            k = 2
            while f"{target_path.stem}_{k}" in ws.docs:
                k += 1
            name = f"{target_path.stem}_{k}"
        part_doc = ws.open(target_path, name=name)

    transform = target["transform"]
    inv = g.invert_rigid(transform)
    out = {
        "document": part_doc.name,
        "path": str(part_doc.path),
        "kind": part_doc.kind,
        "occurrence": target["name"],
        "transform": transform,
        "inverse_transform": inv,
    }
    if point is not None:
        out["point_in_part"] = g.apply_point(inv, point)
    return out


def finish_edit(ws, part: str, update: bool = True) -> dict:
    """Save an edited part document and run update_links (repair=false) in all assemblies that link it,
    including unopened intermediate subassemblies, and persist updated assemblies to disk."""
    part_doc = None
    if part in ws.docs:
        part_doc = ws.docs[part]
    else:
        for d in ws.docs.values():
            if d.name == part or d.path.stem == part or str(d.path) == part or d.path.name == part:
                part_doc = d
                break
    if part_doc is None:
        raise KeyError(f"no open document {part!r}")

    part_doc.save()

    assemblies_updated = {}
    all_warnings = []

    if update:
        target_path = part_doc.path.resolve()
        opened_temp = []
        try:
            # Discover all assemblies (open or intermediate subassemblies) linking the part
            affected_docs = {}
            queue = [d for d in list(ws.docs.values()) if d.kind == ASSEMBLY]
            seen_paths = {d.path.resolve() for d in queue}

            while queue:
                curr_doc = queue.pop(0)
                curr_path = curr_doc.path.resolve()
                uses_target = False
                for link in _links(curr_doc.session).values():
                    if link.get("file") and Path(link["file"]).resolve() == target_path:
                        uses_target = True
                        break

                subs = curr_doc.metadata().get("subassemblies", {})
                for sinfo in subs.values():
                    s_file_str = sinfo.get("file", "")
                    if not s_file_str:
                        continue
                    s_file = Path(s_file_str).resolve()
                    parts_files = [Path(p["file"]).resolve() for p in sinfo.get("parts", {}).values() if p.get("file")]
                    if s_file == target_path or target_path in parts_files:
                        uses_target = True
                        if s_file != target_path and s_file not in seen_paths and s_file.is_file():
                            seen_paths.add(s_file)
                            existing = next((d for d in ws.docs.values() if d.path.resolve() == s_file), None)
                            if existing:
                                sub_doc = existing
                            else:
                                name = s_file.stem
                                if name in ws.docs:
                                    k = 2
                                    while f"{s_file.stem}_{k}" in ws.docs:
                                        k += 1
                                    name = f"{s_file.stem}_{k}"
                                sub_doc = ws.open(s_file, name=name)
                                opened_temp.append(sub_doc)
                            queue.append(sub_doc)
                            affected_docs[s_file] = sub_doc

                if uses_target:
                    affected_docs[curr_path] = curr_doc

            # Build dependency graph: child subassembly must update before parent assembly
            deps = {}
            for p, d in affected_docs.items():
                child_deps = set()
                for link in _links(d.session).values():
                    if link.get("file"):
                        lp = Path(link["file"]).resolve()
                        if lp in affected_docs and lp != p:
                            child_deps.add(lp)
                for sinfo in d.metadata().get("subassemblies", {}).values():
                    if sinfo.get("file"):
                        sp = Path(sinfo["file"]).resolve()
                        if sp in affected_docs and sp != p:
                            child_deps.add(sp)
                deps[p] = child_deps

            # Topological sort: child subassemblies first, then parents
            sorted_docs = []
            remaining = dict(deps)
            while remaining:
                ready = [p for p, d_set in remaining.items() if not (d_set & remaining.keys())]
                if not ready:
                    ready = list(remaining.keys())
                for p in ready:
                    sorted_docs.append(affected_docs[p])
                    del remaining[p]

            for asm_doc in sorted_docs:
                rep = update_links(ws, asm_doc, repair_moved=False)
                asm_doc.save()
                assemblies_updated[asm_doc.name] = rep
                for w in rep.get("warnings", []):
                    all_warnings.append(dict(w, assembly=asm_doc.name))
        finally:
            for d in opened_temp:
                if d.name in ws.docs:
                    ws.close(d.name)

    return {
        "saved": str(part_doc.path),
        "part": part_doc.name,
        "updated": bool(update),
        "assemblies": assemblies_updated,
        "warnings": all_warnings,
    }
