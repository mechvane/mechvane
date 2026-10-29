"""Mechvane MCP server: parts and assemblies as separate files, Inventor-style browser,
sketch ownership and joint checks across file boundaries. Run: python3 -m mechvane"""

import base64
import functools
import os
from pathlib import Path
import re
import struct

from mcp.server.fastmcp import FastMCP, Image

from . import bolted, design_rules, geometry as g, iso286, katalog, links, query, sketch_rule, standard_parts, tree
from .documents import ASSEMBLY, PART, Workspace

mcp = FastMCP(
    "mechvane",
    instructions=(
        "Inventor-style CAD on SolidCraft. Parts and assemblies are separate .solidcraft files, each open "
        "document has its own SolidCraft session. Build parts with run(document, commands) using SolidCraft "
        "command ids (as the solidcraft MCP batch tool takes them), or generate parametric standard parts "
        "with standard_part (see list_standard_parts); a sketch used by one feature is kept directly before "
        "it. Put parts into an assembly with insert_part, join them with add_joint and change them with "
        "edit_joint or delete_joint (not raw joint.create or joint.edit, so Mechvane can check the joint "
        "later), and after changing a part file call update_links: it reports joints that moved to another "
        "face. Save with save_document."
    ),
)


def _autosave_tool(*args, **kwargs):
    """mcp.tool that, with MECHVANE_AUTOSAVE=1, saves every changed open document after each call.
    The web UI runs the agent's turns with it, so a turn ends with everything on disk."""
    register = _mcp_tool(*args, **kwargs)

    def deco(fn):
        @functools.wraps(fn)
        def wrapped(*a, **k):
            try:
                return fn(*a, **k)
            finally:
                if os.environ.get("MECHVANE_AUTOSAVE") == "1":
                    for doc in list(ws.docs.values()):
                        if doc.dirty():
                            doc.save()
        return register(wrapped)
    return deco


_mcp_tool, mcp.tool = mcp.tool, _autosave_tool
ws = Workspace(os.environ.get("MECHVANE_WORKSPACE") or os.environ.get("INVENTA_WORKSPACE")
               or os.path.join(os.getcwd(), "workspace"))


@mcp.tool()
def new_part(name: str, path: str | None = None, overwrite: bool = False) -> dict:
    """Create and save an empty part file (default <workspace>/<name>.solidcraft).
    Pass overwrite=True to overwrite an existing file on disk."""
    return ws.new(PART, name, path, overwrite=overwrite).info()


@mcp.tool()
def standard_part(norm: str, size: str, length: float | None = None,
                  name: str | None = None, path: str | None = None,
                  overwrite: bool = False) -> dict:
    """Create, save and keep open a parametric standard part file (norms: ISO 4762, ISO 10642, ISO 4017,
    ISO 4032, ISO 7089, Ruthex, DIN 625; length in mm is required for ISO 4762, ISO 10642 and ISO 4017).
    Pass overwrite=True to replace an existing file on disk."""
    return _compact(standard_parts.create(ws, norm, size, length=length, name=name, path=path,
                                          overwrite=overwrite))


@mcp.tool()
def list_standard_parts(norm: str | None = None) -> dict:
    """List supported standard part norms and sizes, or the full dimension table for one norm."""
    return standard_parts.catalog(norm)


@mcp.tool()
def iso_fit(nominal: float, fit: str) -> dict:
    """ISO 286 limits for one tolerance class ('H7', 'k6') or a fit ('H7/k6') at a nominal size in mm.
    A fit reports min/max clearance in µm (negative = interference) and its kind; `katalog` lists
    catalog entries (usage notes, e.g. bearing seats) that mention the classes."""
    out = iso286.fit(nominal, fit) if "/" in fit else iso286.limits(nominal, fit)
    terms = [t.strip() for t in fit.split("/")]
    out["katalog"] = [{"id": e["id"], "aussage": e["aussage"]} for e in katalog.load()
                      if any(re.search(rf"\b{re.escape(t)}\b", e["aussage"]) for t in terms)]
    return out


@mcp.tool()
def new_assembly(name: str, path: str | None = None, overwrite: bool = False) -> dict:
    """Create and save an empty assembly file.
    Pass overwrite=True to overwrite an existing file on disk."""
    return ws.new(ASSEMBLY, name, path, overwrite=overwrite).info()


@mcp.tool()
def open_document(path: str, name: str | None = None) -> dict:
    """Open a part or assembly file (paths relative to the workspace)."""
    return ws.open(path, name).info()


@mcp.tool()
def list_documents() -> dict:
    """The open documents and the workspace folder."""
    return {"workspace": str(ws.root), "documents": [d.info() for d in ws.docs.values()]}


@mcp.tool()
def save_document(document: str) -> dict:
    """Save a document to its file."""
    doc = ws.get(document)
    doc.save()
    return doc.info()


@mcp.tool()
def close_document(document: str, discard: bool = False) -> dict:
    """Close an open document without saving. If the document has unsaved changes,
    raises an error unless discard=True."""
    doc = ws.docs.get(document) or ws.get(document)  # no reload check: closing is how to drop a stale copy
    is_dirty = doc.session.cmd("document.inspect").get("dirty", False)
    if is_dirty and not discard:
        raise ValueError(
            f"document {document!r} has unsaved changes; call save_document({document!r}) first or pass discard=True"
        )
    ws.close(document)
    return {"closed": document}


def _compact(v):
    """Leave out what a reply repeats without telling anything: nulls, empty lists, timings."""
    if isinstance(v, dict):
        return {k: _compact(x) for k, x in v.items() if k != "ms" and x is not None and x != [] and x != {}}
    if isinstance(v, list):
        return [_compact(x) for x in v]
    return v


@mcp.tool()
def run(document: str, commands: list[dict], verbose: bool = False) -> dict:
    """Run SolidCraft commands ([{command, params}]) in a document, all or nothing. In a part, owned
    sketches are then moved directly before their feature. The reply leaves out empty fields and
    timings unless verbose."""
    doc = ws.get(document)
    cp = None
    if doc.kind == PART:
        try:
            cp = doc.session.cmd("edit.checkpoint").get("checkpoint")
        except Exception:
            cp = None
    try:
        result = doc.session.batch(commands)
    except Exception:
        if cp is not None:
            try:
                doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
            except Exception:
                pass
        raise

    out = {"results": result.get("results", result) if isinstance(result, dict) else result}
    if not verbose:
        out["results"] = _compact(out["results"])
    if doc.kind == PART:
        try:
            out["sketch_rule"] = sketch_rule.enforce(doc.session)
        except Exception as e:
            if cp is not None:
                try:
                    doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp})
                except Exception:
                    pass
            raise RuntimeError(f"sketch rule failed, rolled back batch: {e}") from e
    if cp is not None:
        try:
            doc.session.cmd("edit.restore_checkpoint", {"checkpoint": cp, "forget": True})
        except Exception:
            pass
    return out


@mcp.tool()
def browser(document: str, groups: bool = False) -> dict:
    """The model browser, Inventor style: a part's features with their sketches and the end-of-part
    marker, or an assembly's parts with their joints under each part. groups=true adds the same
    items as folders (sketches, work features, relations), each with what it belongs to."""
    doc = ws.get(document)
    t = tree.part_tree(doc.session, groups) if doc.kind == PART else tree.assembly_tree(doc.session, groups, base=doc.path.parent)
    return {"text": tree.render(t), "tree": t}


@mcp.tool()
def delete_feature(document: str, feature: str, keep_sketch: bool = False) -> dict:
    """Delete a part feature. Its own sketch (and that sketch's own work plane) goes with it unless
    keep_sketch; whatever something else still needs is kept and listed under `kept`."""
    doc = ws.get(document, PART)
    if keep_sketch:
        return {"deleted": [feature], "kept": [], "result": doc.session.cmd("timeline.delete", {"features": [feature]})}
    return sketch_rule.delete_with_owned(doc.session, feature)


@mcp.tool()
def insert_part(assembly: str, part_path: str, name: str | None = None, translate: list[float] | None = None,
                rotate: dict | list | None = None, grounded: bool = False) -> dict:
    """Place a part or subassembly file in an assembly. A part is linked directly; a subassembly
    is expanded into a parent component with its linked parts and joints underneath.
    rotate can be {axis: [x,y,z], angle: deg, origin?: [x,y,z]}, [axis, angle], or a 4x4 matrix."""
    doc = ws.get(assembly, ASSEMBLY)
    return links.insert(ws, doc, part_path, name=name, translate=translate, rotate=rotate, grounded=grounded)


@mcp.tool()
def add_joint(assembly: str, params: dict) -> dict:
    """Create a joint (params as SolidCraft joint.create takes them, `name` required) and record which
    part face each side sits on, so update_links can check it later."""
    if not params.get("name"):
        raise ValueError("give the joint a name")
    doc = ws.get(assembly, ASSEMBLY)
    params = links.resolve_occurrences(doc.session, params)
    r = doc.session.cmd("joint.create", params)
    anchors = links.record(ws, doc, params["name"], params)
    return {"joint": r, "anchors": anchors["sides"]}


@mcp.tool()
def edit_joint(assembly: str, joint: str, params: dict) -> dict:
    """Change a joint (params as SolidCraft joint.edit takes them, e.g. flip, offset, a, b) and record
    its part faces again."""
    doc = ws.get(assembly, ASSEMBLY)
    params = links.resolve_occurrences(doc.session, params)
    new_name = params.get("name", joint)
    r = doc.session.cmd("joint.edit", dict(params, joint=joint))
    if new_name != joint:
        meta = doc.metadata()
        joints_meta = meta.get("joints", {})
        if joint in joints_meta:
            old_data = joints_meta.pop(joint)
            if "create" in old_data and isinstance(old_data["create"], dict):
                old_data["create"] = dict(old_data["create"], name=new_name)
            joints_meta[new_name] = old_data
            doc.set_metadata(meta)
    return {"joint": r, "anchors": links.record(ws, doc, new_name)["sides"]}


@mcp.tool()
def delete_joint(assembly: str, joint: str) -> dict:
    """Delete a joint and what Mechvane recorded about it."""
    doc = ws.get(assembly, ASSEMBLY)
    doc.session.cmd("joint.delete", {"joint": joint})
    links.forget(doc, joint)
    return {"deleted": joint}


@mcp.tool()
def adopt_joint(assembly: str, joint: str) -> dict:
    """Start checking a joint that was not made with add_joint (made in the app or with raw
    joint.create). update_links reports it when it moves; repair needs add_joint's parameters."""
    doc = ws.get(assembly, ASSEMBLY)
    return {"anchors": links.record(ws, doc, joint)["sides"]}


@mcp.tool()
def update_links(assembly: str, repair: bool = False) -> dict:
    """Read the linked part files again, check every joint made with add_joint against its part face,
    and check every bolted connection against its geometric anchor. `warnings` lists joints and bolted
    connections that moved or whose anchor is lost; repair=true repairs moved joints and rebuilds moved
    bolted connections at their new anchor position."""
    return links.update_links(ws, ws.get(assembly, ASSEMBLY), repair_moved=repair)


@mcp.tool()
def repair_joint(assembly: str, joint: str) -> dict:
    """Put a moved or broken joint back on its recorded part face."""
    doc = ws.get(assembly, ASSEMBLY)
    after = links.repair(ws, doc, joint)
    st = after[0]["status"] if after else "ok"
    return {"joint": joint, "status": st, "report": after}


@mcp.tool()
def check_joints(assembly: str) -> dict:
    """Check every recorded joint against its part face without updating links."""
    return {"joints": links.check(ws, ws.get(assembly, ASSEMBLY))}


@mcp.tool()
def measure(document: str) -> dict:
    """Volume (mm³), area (mm²), centre of mass and bounding box of every body."""
    keep = ("name", "volume_mm3", "area_mm2", "center_of_mass", "bbox", "faces", "edges", "visible")
    doc = ws.get(document)
    bodies = doc.session.cmd("document.inspect", {"measure": True}).get("bodies", [])
    out = [{k: b[k] for k in keep if k in b} for b in bodies]
    if doc.kind == ASSEMBLY:
        # SolidCraft reports assembly bodies in part coordinates; move them into world coordinates.
        placed = {t["world_name"]: t for t in query._collect_bodies(doc, None)}
        for b in out:
            t = placed.get(b["name"])
            if not t or not t["transform"]:
                continue
            b["occurrence"] = t["occurrence"]
            m = t["transform"]
            if b.get("center_of_mass"):
                b["center_of_mass"] = g.apply_point(m, b["center_of_mass"])
            if b.get("bbox"):
                lo, hi = b["bbox"]["min"], b["bbox"]["max"]
                corners = [g.apply_point(m, [x, y, z]) for x in (lo[0], hi[0])
                           for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
                b["bbox"] = {"min": [min(c[i] for c in corners) for i in range(3)],
                             "max": [max(c[i] for c in corners) for i in range(3)]}
    return {"bodies": out}


@mcp.tool()
def list_commands(document: str, filter: str | None = None) -> dict:
    """SolidCraft's command catalog with parameter docs; filter matches id, label, tab and panel."""
    r = ws.get(document).session.tool("list_commands", {"filter": filter} if filter else {})
    return r if isinstance(r, dict) else {"commands": r}


@mcp.tool()
def command(document: str, command: str, params: dict | None = None) -> dict:
    """Run one SolidCraft command in a document (queries such as joint.list or document.inspect)."""
    r = ws.get(document).session.cmd(command, params or {})
    return r if isinstance(r, dict) else {"result": r}


@mcp.tool()
def screenshot(document: str, view: str = "iso", path: str | None = None):
    """Render a document headless (views: iso, front, top, right, …).
    If path is given, saves the PNG file under this path (relative to the workspace,
    not outside) and returns path, size in bytes and image dimensions instead of the image."""
    r = ws.get(document).session.tool("screenshot", {"view": view})
    raw = base64.b64decode(r["images"][0]["image"])
    if path is None:
        return Image(data=raw, format="png")
    if not path or not path.strip():
        raise ValueError("give a non-empty file path")
    p = Path(path)
    target = (ws.root / p).resolve() if not p.is_absolute() else p.resolve()
    try:
        rel = target.relative_to(ws.root)
    except ValueError:
        raise ValueError(f"path {path!r} is outside workspace {ws.root}")
    if target.suffix.lower() != ".png":
        raise ValueError(f"screenshot path must end with .png, got {path!r}")
    if target.is_dir():
        raise ValueError(f"path {path!r} is a directory")
    if target.exists():
        with open(target, "rb") as f:
            header = f.read(8)
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"cannot overwrite non-PNG file {path!r} with screenshot")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    width, height = 0, 0
    if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
        width, height = struct.unpack(">II", raw[16:24])
    return {
        "path": str(target),
        "rel_path": str(rel),
        "size": len(raw),
        "bytes": len(raw),
        "width": width,
        "height": height,
        "dimensions": [width, height],
    }


@mcp.tool()
def check_design(document: str, profile: str = "fdm_0.4", build_direction: str = "+Z",
                 material: str | None = None) -> dict:
    """Check a part against design rules (wall thickness, hole edge distance, thread depth, printability).
    `build_direction` selects the print direction ('+Z', '-Z', '+X', '-X', '+Y', '-Y'; default '+Z').
    `material` (steel, cast_iron, alu, alu_wrought, alu_cast, brass, ...) sets the thread engagement depth
    from the same table as bolted_connection; without it the material assigned to the bodies
    (SolidCraft material.assign) applies, else the profile's 1.5 × d."""
    vec = design_rules.parse_build_direction(build_direction, allow_vector=False)
    doc = ws.get(document, PART)
    return design_rules.check(doc.session, profile=profile, build_direction=vec, material=material)


@mcp.tool()
def bolted_connection(
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
    """Create a complete bolted connection across files: drills holes in each pierced component,
    generates standard parts (ISO 4762 cap screw or ISO 10642 countersunk screw, ISO 7089 washers, ISO 4032 nut),
    inserts them into the assembly and constrains them with rigid coaxial joints. Supports optional circular and rectangular patterns.
    Optionally restrict connected parts to `parts` (occurrence names in ray order).
    `head` selects screw head geometry: 'cap' (standard DIN 974-1 counterbore, default) or 'countersunk' (ISO 10642 flush 90° countersink)."""
    return bolted.bolted_connection(
        ws,
        assembly=assembly,
        placement=placement,
        size=size,
        fasteners=fasteners,
        fit=fit,
        counterbore=counterbore,
        connection_type=connection_type,
        blind_material=blind_material,
        use_insert=use_insert,
        name=name,
        pattern=pattern,
        parts=parts,
        head=head,
    )


@mcp.tool()
def preview_bolted_connection(
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
    """Preview a bolted connection: calculate grip length, hole parameters and required screw length
    without modifying any files. Supports optional circular and rectangular patterns.
    Optionally restrict connected parts to `parts` (occurrence names in ray order).
    `head` selects screw head geometry: 'cap' (default) or 'countersunk'."""
    return bolted.preview_bolted_connection(
        ws,
        assembly=assembly,
        placement=placement,
        size=size,
        fasteners=fasteners,
        fit=fit,
        counterbore=counterbore,
        connection_type=connection_type,
        blind_material=blind_material,
        use_insert=use_insert,
        pattern=pattern,
        parts=parts,
        head=head,
    )


@mcp.tool()
def list_bolted_connections(assembly: str) -> dict:
    """List all bolted connections recorded in an assembly."""
    return bolted.list_bolted_connections(ws, assembly=assembly)


@mcp.tool()
def delete_bolted_connection(assembly: str, id: str) -> dict:
    """Delete a bolted connection from an assembly: removes fastener parts, joints and hole features
    from penetrated components, then saves the assembly and components."""
    return bolted.delete_bolted_connection(ws, assembly=assembly, id=id)


@mcp.tool()
def edit_bolted_connection(
    assembly: str,
    id: str,
    size: str | None = None,
    fasteners: dict | None = None,
    fit: str | None = None,
    counterbore: bool | None = None,
    connection_type: str | None = None,
    blind_material: str | None = None,
    use_insert: bool | None = None,
    pattern: dict | None = None,
    placement: dict | None = None,
    parts: list[str] | None = None,
    head: str | None = None,
    changes: dict | None = None,
) -> dict:
    """Edit an existing bolted connection in an assembly by applying changes (e.g. size, length,
    counterbore, fit, parts, head: 'cap' | 'countersunk'). Implemented as delete and recreate with the same positions;
    restores old state on error."""
    all_changes = {}
    if changes:
        all_changes.update(changes)
    for k, v in [
        ("size", size), ("fasteners", fasteners), ("fit", fit),
        ("counterbore", counterbore), ("connection_type", connection_type),
        ("blind_material", blind_material), ("use_insert", use_insert),
        ("pattern", pattern), ("placement", placement), ("parts", parts),
        ("head", head),
    ]:
        if v is not None:
            all_changes[k] = v
    return bolted.edit_bolted_connection(ws, assembly, id, **all_changes)


@mcp.tool()
def find(document: str, what: str, where: dict | None = None, limit: int = 50) -> dict:
    """Find faces, edges or holes in a part or assembly matching filters in `where`."""
    doc = ws.get(document)
    items = query.find(doc, what, where=where, limit=limit, ws=ws)
    return {"items": list(items), what: list(items), "count": len(items)}


def main():
    try:
        mcp.run()
    finally:
        ws.close_all()


from . import inplace


@mcp.tool()
def edit_in_place(assembly: str, occurrence: str, point: list[float] | None = None) -> dict:
    """Open the part file behind an occurrence (including subassemblies like 'Sub:1/Plate:1') for
    in-place editing. If already open, returns the existing document. Returns document name and the
    occurrence transformation for converting coordinates. If point is given, converts it to part coordinates."""
    return inplace.edit_in_place(ws, assembly, occurrence, point=point)


@mcp.tool()
def finish_edit(part: str, update: bool = True) -> dict:
    """Save an edited part document and run update_links (repair=false) in all open assemblies that link it,
    returning their reports with any joint warnings visible."""
    return inplace.finish_edit(ws, part, update=update)


@mcp.tool()
def to_part_coords(assembly: str, occurrence: str, point: list[float]) -> dict:
    """Convert a 3D point [x, y, z] from assembly coordinates into the local coordinates of an occurrence."""
    if not isinstance(point, (list, tuple)) or len(point) != 3 or not all(isinstance(x, (int, float)) for x in point):
        raise ValueError(f"point must be a 3D coordinate [x, y, z], got {point!r}")
    doc = ws.get(assembly, ASSEMBLY)
    target = inplace.resolve_occurrence(doc, occurrence)
    return {
        "point": inplace.to_part_coords(point, target["transform"]),
        "occurrence": target["name"],
        "assembly": doc.name,
    }

