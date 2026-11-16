"""Bill of materials (BOM) generator and CSV exporter for Mechvane assemblies.

Provides structured and flat bill of materials with part designation, count, file,
assigned material, mass, and norm/size for standard parts.
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

from . import files_on_disk, read_metadata
from .documents import ASSEMBLY, Workspace
from .solidcraft import SolidCraftError


def _resolve_path(base_dir: Path, file_str: str) -> Path:
    p = Path(file_str)
    if not p.is_absolute():
        return (base_dir / p).resolve()
    return p.resolve()


def _rel_file_str(p: Path | None, base_dir: Path) -> str:
    if p is None:
        return ""
    try:
        return os.path.relpath(p, base_dir).replace("\\", "/")
    except ValueError:
        return str(p)


def _get_part_cache_info(ws: Workspace, file_path: Path, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    canon_key = str(file_path.resolve())
    if canon_key in cache:
        return cache[canon_key]

    target_p = file_path.resolve()
    open_doc = next((d for d in ws.docs.values() if d.path.resolve() == target_p), None)

    def unusable(why: str) -> dict[str, Any]:
        # a part file that is gone or unreadable is a row of its own, not the end of the whole list (review 2026-11-16)
        info = {"benennung": f"{file_path.stem} ({why})", "werkstoff": None, "masse": None, "norm": None,
                "groesse": None, "length": None, "std": None, "problem": why}
        cache[canon_key] = info
        return info

    if open_doc is not None:
        meta = open_doc.metadata()
        meas = open_doc.session.tool("measure", {})
        doc_name = open_doc.name
    elif not target_p.is_file():
        return unusable("file missing")
    else:
        try:
            reader = ws.reader(file_path)
            try:
                raw_meta = reader.cmd("document.metadata").get("metadata")
                meta = files_on_disk(read_metadata(raw_meta), file_path.parent)
                meas = reader.tool("measure", {})
                insp = reader.cmd("document.inspect")
                doc_name = insp.get("name") or file_path.stem
            finally:
                reader.close()
        except SolidCraftError:
            return unusable("unreadable")

    bodies = meas.get("bodies", [])
    materials = {b.get("material") for b in bodies} - {None, "Default"}
    if materials:
        material = ", ".join(sorted(materials))
    elif meta.get("rules", {}).get("material"):
        material = meta["rules"]["material"]
    else:
        material = None

    total_mass = sum(float(b.get("mass_g") or 0.0) for b in bodies)
    masse = round(total_mass, 2) if bodies else 0.0

    std = meta.get("standard")
    if std and isinstance(std, dict):
        norm = std.get("norm")
        groesse = std.get("size")
        length = std.get("length")
        designation = std.get("designation")
        benennung = designation or doc_name or file_path.stem
    else:
        norm = None
        groesse = None
        length = None
        benennung = meta.get("description") or meta.get("benennung") or doc_name or file_path.stem

    info = {
        "benennung": benennung,
        "werkstoff": material,
        "masse": masse,
        "norm": norm,
        "groesse": groesse,
        "length": length,
        "std": std,
    }
    cache[canon_key] = info
    return info


def _get_subassembly_info(
    ws: Workspace,
    sub_file: Path,
    sub_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    target_p = sub_file.resolve()
    canon_key = str(target_p)
    if canon_key in sub_cache:
        return sub_cache[canon_key]

    open_doc = next((d for d in ws.docs.values() if d.path.resolve() == target_p), None)
    if open_doc is not None:
        meta = open_doc.metadata()
        doc_name = open_doc.name
    elif target_p.is_file():
        reader = ws.reader(target_p)
        try:
            raw_meta = reader.cmd("document.metadata").get("metadata")
            meta = files_on_disk(read_metadata(raw_meta), target_p.parent)
            insp = reader.cmd("document.inspect")
            doc_name = insp.get("name") or target_p.stem
        finally:
            reader.close()
    else:
        meta = {}
        doc_name = target_p.stem

    benennung = meta.get("description") or meta.get("benennung") or doc_name or target_p.stem
    info = {
        "benennung": benennung,
        "subassemblies": meta.get("subassemblies") or {},
        "dir": target_p.parent,
    }
    sub_cache[canon_key] = info
    return info


def _make_row(
    pos: int | str,
    benennung: str,
    count: int,
    rel_datei: str,
    werkstoff: str | None,
    masse: float,
    norm: str | None = None,
    groesse: str | None = None,
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "position": pos,
        "item": pos,
        "benennung": benennung,
        "name": benennung,
        "description": benennung,
        "anzahl": count,
        "count": count,
        "quantity": count,
        "datei": rel_datei,
        "file": rel_datei,
        "werkstoff": werkstoff,
        "material": werkstoff,
        "masse": masse,
        "mass": masse,
        "mass_g": masse,
        "single_mass": masse,
        "total_mass": round(masse * count, 2) if masse is not None else None,
        "norm": norm,
        "groesse": groesse,
        "size": groesse,
    }
    if children is not None:
        row["children"] = children
    return row


def _cell(v: Any) -> str:
    """A text cell that a spreadsheet must not run as a formula: a leading = + - @ (or tab, return) gets an apostrophe
    (CSV injection: a part description can come from a downloaded file)."""
    t = str(v)
    return "'" + t if t[:1] in ("=", "+", "-", "@", "\t", "\r") else t


def _write_csv_row(writer: Any, r: dict[str, Any]) -> None:
    pos = str(r.get("position", ""))
    name = _cell(r.get("benennung", "") or "")
    count = str(r.get("anzahl", "") or "")
    file_ = _cell(r.get("datei", "") or "")
    mat = _cell(r.get("werkstoff", "") or "")
    masse = r.get("masse")
    masse_str = f"{masse:.2f}" if isinstance(masse, (int, float)) else ("" if masse is None else str(masse))
    norm = _cell(r.get("norm", "") or "")
    size = _cell(r.get("groesse", "") or "")
    writer.writerow([pos, name, count, file_, mat, masse_str, norm, size])
    for ch in r.get("children", []):
        _write_csv_row(writer, ch)


def export_csv(rows: list[dict[str, Any]], path: Path) -> None:
    """Export BOM rows to a semicolon-separated UTF-8 CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Position", "Benennung", "Anzahl", "Datei", "Werkstoff", "Masse", "Norm", "Größe"])
        for r in rows:
            _write_csv_row(writer, r)


def _match_subassembly_meta(
    comp_id: Any,
    comp: dict[str, Any] | None,
    doc_subs_by_comp: dict[Any, tuple[str, dict[str, Any]]],
    doc_subs_by_name: dict[str, dict[str, Any]],
    parent_subs: dict[str, dict[str, Any]],
    parent_dir: Path,
    parent_prefixes: list[str],
    assembly_dir: Path,
) -> tuple[dict[str, Any] | None, Path, str | None]:
    """Locate subassembly metadata entry, its base directory, and its local key."""
    if comp_id in doc_subs_by_comp:
        key, info = doc_subs_by_comp[comp_id]
        return info, assembly_dir, key
    comp_name = comp.get("name") if comp else None
    if comp_name and comp_name in doc_subs_by_name:
        return doc_subs_by_name[comp_name], assembly_dir, comp_name

    if comp_name and parent_subs:
        candidates = [comp_name]
        for pref in parent_prefixes:
            if pref and comp_name.startswith(f"{pref}_"):
                local = comp_name[len(pref) + 1:]
                candidates.append(local)
                stripped = re.sub(r"_\d+$", "", local)
                if stripped != local:
                    candidates.append(stripped)
        for cand in candidates:
            if cand in parent_subs:
                return parent_subs[cand], parent_dir, cand

    return None, assembly_dir, None


def _resolve_sub_file(
    sub_info: dict[str, Any] | None,
    base_dir: Path,
    comp_id: Any,
    links_map: dict[Any, dict[str, Any]],
) -> Path | None:
    sub_file: Path | None = None
    if sub_info:
        if sub_info.get("file"):
            sub_file = Path(sub_info["file"])
        elif sub_info.get("path"):
            sub_file = base_dir / sub_info["path"]
    elif comp_id in links_map:
        sub_file = Path(links_map[comp_id]["file"])

    if sub_file is None:
        return None
    if not sub_file.is_absolute():
        return (base_dir / sub_file).resolve()
    return sub_file.resolve()


def bill_of_materials(
    ws: Workspace,
    assembly: str,
    path: str | Path | None = None,
    flat: bool = False,
) -> dict[str, Any]:
    """Generate bill of materials (BOM) for an assembly document.

    Args:
        ws: Active Mechvane workspace.
        assembly: Document name or path of the assembly.
        path: Optional path for semicolon-separated UTF-8 CSV output inside workspace.
        flat: If True, subassemblies are dissolved into constituent leaf parts.
              If False (default), subassemblies appear as rows with nested children.

    Returns:
        Dictionary with assembly name, flat flag, rows list (with bom alias),
        count, and optional path.
    """
    try:
        doc = ws.get(assembly, ASSEMBLY)
    except KeyError:
        doc = ws.open(assembly)
        if doc.kind != ASSEMBLY:
            kind = doc.kind
            ws.close(doc.name)
            raise ValueError(f"{assembly!r} is a {kind}, not a {ASSEMBLY}")

    s = doc.session
    comps = s.cmd("component.list")["components"]
    by_id = {c["id"]: c for c in comps}
    root = next(c for c in comps if c["parent"] is None)
    links_list = s.cmd("component.links").get("links", [])
    links_map = {l["component"]: l for l in links_list}
    meta = doc.metadata()
    subs_meta = meta.get("subassemblies") or {}
    doc_subs_by_comp: dict[Any, tuple[str, dict[str, Any]]] = {}
    doc_subs_by_name: dict[str, dict[str, Any]] = {}
    for k, info in subs_meta.items():
        if info.get("component") is not None:
            doc_subs_by_comp[info["component"]] = (k, info)
        doc_subs_by_name[k] = info

    part_cache: dict[str, dict[str, Any]] = {}
    sub_cache: dict[str, dict[str, Any]] = {}
    assembly_dir = doc.path.parent

    if flat:
        leaf_counts: dict[str, dict[str, Any]] = {}
        first_seen_order: list[str] = []

        def walk_flat(comp_occurrences: list[dict[str, Any]]) -> None:
            for o in comp_occurrences:
                comp_id = o.get("component")
                c = by_id.get(comp_id)
                is_sub = comp_id not in links_map and (
                    comp_id in doc_subs_by_comp
                    or (c is not None and c.get("name") in doc_subs_by_name)
                    or (c is not None and bool(c.get("children")))
                )
                if is_sub:
                    if c and c.get("children"):
                        walk_flat(c["children"])
                else:
                    link = links_map.get(comp_id)
                    if link:
                        p = _resolve_path(assembly_dir, link["file"])
                        canon_key = str(p.resolve())
                        if canon_key not in leaf_counts:
                            leaf_counts[canon_key] = {"path": p, "count": 0}
                            first_seen_order.append(canon_key)
                        leaf_counts[canon_key]["count"] += 1

        walk_flat(root.get("children", []))

        rows: list[dict[str, Any]] = []
        for i, canon_key in enumerate(first_seen_order):
            entry = leaf_counts[canon_key]
            p = entry["path"]
            item_count = entry["count"]
            info = _get_part_cache_info(ws, p, part_cache)
            rel_datei = _rel_file_str(p, assembly_dir)
            rows.append(
                _make_row(
                    pos=i + 1,
                    benennung=info["benennung"],
                    count=item_count,
                    rel_datei=rel_datei,
                    werkstoff=info["werkstoff"],
                    masse=info["masse"],
                    norm=info["norm"],
                    groesse=info["groesse"],
                )
            )

    else:
        def build_structured(
            comp_occurrences: list[dict[str, Any]],
            parent_subs: dict[str, dict[str, Any]],
            parent_dir: Path,
            parent_prefixes: list[str],
            pos_prefix: str = "",
        ) -> list[dict[str, Any]]:
            grouped: dict[str, dict[str, Any]] = {}
            seen_order: list[str] = []

            for o in comp_occurrences:
                comp_id = o.get("component")
                c = by_id.get(comp_id)
                sub_info, sub_base_dir, sub_key = _match_subassembly_meta(
                    comp_id, c, doc_subs_by_comp, doc_subs_by_name,
                    parent_subs, parent_dir, parent_prefixes, assembly_dir,
                )
                is_sub = comp_id not in links_map and (
                    sub_info is not None
                    or (c is not None and bool(c.get("children")))
                )

                if is_sub:
                    sub_file = _resolve_sub_file(sub_info, sub_base_dir, comp_id, links_map)
                    if sub_file is not None:
                        sinfo = _get_subassembly_info(ws, sub_file, sub_cache)
                        sub_name = sinfo["benennung"]
                        child_subs = sinfo["subassemblies"]
                        child_dir = sinfo["dir"]
                        canon_key = f"sub:{sub_file.resolve()}"
                    else:
                        sub_name = (c.get("name") if c else None) or o.get("name") or ""
                        child_subs = {}
                        child_dir = parent_dir
                        canon_key = f"sub_comp:{comp_id}"

                    if canon_key not in grouped:
                        next_prefixes: list[str] = []
                        if c and c.get("name"):
                            next_prefixes.append(c["name"])
                        if sub_key and sub_key not in next_prefixes:
                            next_prefixes.append(sub_key)
                        grouped[canon_key] = {
                            "is_sub": True,
                            "file": sub_file,
                            "name": sub_name,
                            "comp": c,
                            "child_subs": child_subs,
                            "child_dir": child_dir,
                            "child_prefixes": next_prefixes,
                            "count": 0,
                        }
                        seen_order.append(canon_key)
                    grouped[canon_key]["count"] += 1
                else:
                    link = links_map.get(comp_id)
                    if link:
                        p = _resolve_path(assembly_dir, link["file"])
                        canon_key = f"part:{p.resolve()}"
                        if canon_key not in grouped:
                            grouped[canon_key] = {
                                "is_sub": False,
                                "file": p,
                                "count": 0,
                            }
                            seen_order.append(canon_key)
                        grouped[canon_key]["count"] += 1

            result_rows: list[dict[str, Any]] = []
            for i, canon_key in enumerate(seen_order):
                entry = grouped[canon_key]
                pos: int | str = f"{pos_prefix}.{i + 1}" if pos_prefix else (i + 1)

                if not entry["is_sub"]:
                    p = entry["file"]
                    item_count = entry["count"]
                    info = _get_part_cache_info(ws, p, part_cache)
                    rel_datei = _rel_file_str(p, assembly_dir)
                    result_rows.append(
                        _make_row(
                            pos=pos,
                            benennung=info["benennung"],
                            count=item_count,
                            rel_datei=rel_datei,
                            werkstoff=info["werkstoff"],
                            masse=info["masse"],
                            norm=info["norm"],
                            groesse=info["groesse"],
                        )
                    )
                else:
                    c = entry["comp"]
                    child_rows = build_structured(
                        c.get("children", []) if c else [],
                        parent_subs=entry["child_subs"],
                        parent_dir=entry["child_dir"],
                        parent_prefixes=entry["child_prefixes"],
                        pos_prefix=str(pos),
                    )
                    sub_total_mass = sum(
                        float(ch.get("total_mass") or 0.0) for ch in child_rows
                    )
                    sub_mass = round(sub_total_mass, 2)
                    sub_rel = _rel_file_str(entry["file"], assembly_dir)
                    result_rows.append(
                        _make_row(
                            pos=pos,
                            benennung=entry["name"],
                            count=entry["count"],
                            rel_datei=sub_rel,
                            werkstoff=None,
                            masse=sub_mass,
                            norm=None,
                            groesse=None,
                            children=child_rows,
                        )
                    )
            return result_rows

        rows = build_structured(
            root.get("children", []),
            parent_subs=subs_meta,
            parent_dir=assembly_dir,
            parent_prefixes=[],
            pos_prefix="",
        )

    out: dict[str, Any] = {
        "assembly": doc.name,
        "flat": flat,
        "rows": rows,
        "bom": rows,
        "count": len(rows),
    }

    if path is not None:
        if not str(path).strip():
            raise ValueError("give a non-empty file path")
        p_target = Path(path)
        ws_root = ws.root.resolve()
        target = (ws_root / p_target).resolve() if not p_target.is_absolute() else p_target.resolve()
        try:
            rel = target.relative_to(ws_root)
        except ValueError:
            raise ValueError(f"path {path!r} is outside workspace {ws.root}")
        if target.suffix.lower() != ".csv":
            raise ValueError(f"BOM CSV path must end with .csv, got {path!r}")
        if target.is_dir():
            raise ValueError(f"path {path!r} is a directory")
        export_csv(rows, target)
        out["path"] = str(target)
        out["rel_path"] = rel.as_posix()

    return out
