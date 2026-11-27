"""Mechvane MCP server: parts and assemblies as separate files, Inventor-style browser,
sketch ownership and joint checks across file boundaries. Run: python3 -m mechvane"""

import base64
import functools
import io
import os
from pathlib import Path
import re
import struct

from mcp.server.fastmcp import FastMCP, Image

from . import bom, bolted, design_rules, step_import, modeling, geometry as g, iso286, katalog, links, query, sc_errors, sketch_rule, standard_parts, state_delta, tree
from .documents import ASSEMBLY, PART, Workspace, check_windows_writable, reload_windows

mcp = FastMCP(
    "mechvane",
    instructions=(
        "Inventor-style CAD on SolidCraft. Parts and assemblies are separate .solidcraft files, each open "
        "document has its own SolidCraft session. Build parts with run(document, commands) using SolidCraft "
        "command ids (as the solidcraft MCP batch tool takes them), which in parts also returns a state "
        "delta and warnings after each step; or generate parametric standard parts "
        "with standard_part (see list_standard_parts); a sketch used by one feature is kept directly before "
        "it. Keep the design intent: when a request names a relation (in the middle of a face, 10 mm from an "
        "edge, flush, concentric, equal, symmetric), build it as sketch constraints on projected edges "
        "(sketch.project, sketch.constraint.midpoint, dimensions to the projected line), never as computed "
        "coordinates, so it still holds when the part changes. Put parts into an assembly with insert_part, join them with add_joint "
        "(pass as_built=True when parts are already positioned so they stay where they are) and change them with "
        "edit_joint or delete_joint (not raw joint.create, joint.as_built or joint.edit, so Mechvane can check the joint "
        "later); for a rule between faces (mate, flush, concentric, angle ...) use add_constraint and edit_constraint, and after changing a part file call update_links: it reports joints that moved to another "
        "face. Save with save_document. To inspect or repair a part before a feature, roll there with "
        "part_end(document, before=feature) and back with part_end(document). For holes and screws use bolted_connection; "
        "check a part with check_design (pass material, or assign one in SolidCraft; values carry their sources); "
        "export with export_gltf for Blender or the web; visually inspect with verify_view (when adding a feature in a "
        "new place, after errors, or before finishing; not after every step). Lengths in mm."
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
                        if not getattr(doc, "window", False) and doc.dirty():  # the user saves the window's design
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
@sc_errors.explained
def import_step(source: str, name: str | None = None, path: str | None = None, overwrite: bool = False,
                up: str = "z", split: bool = False) -> dict:
    """Make a part or assembly file from a STEP (or IGES, FreeCAD, Rhino) file and keep it open: a fixed body without
    history, e.g. a bought-in part to insert into an assembly with insert_part, or a part to measure and
    check. source is absolute or relative to the project folder; up="y" turns a file with Y up so that Y
    becomes Z. When split=True, a file with multiple bodies is imported as an assembly with individual part files
    for each body. Returns the document info and bodies/parts with volume and bounding box."""
    return step_import.import_step(ws, source, name=name, path=path, overwrite=overwrite, up=up, split=split)


@mcp.tool()
@sc_errors.explained
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
    out["katalog"] = [{"id": e["id"], "aussage": e["aussage"]} for e in katalog.load(include_private=False)
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
def connect_window(name: str = "window", address: str = "auto") -> dict:
    """Work on the design open in the running SolidCraft window, as document `name` (the other tools take it as
    `document`). address "auto" finds the window (several windows: give "127.0.0.1:PORT"). The design is the
    user's: new_part, open_document and save_document never replace or save it, the user saves in the app.
    Mechvane's changes show in the window; close_document only disconnects."""
    return ws.connect_window(name, address).info()


@mcp.tool()
def list_documents() -> dict:
    """The open documents and the workspace folder."""
    return {"workspace": str(ws.root), "documents": [d.info() for d in ws.docs.values()]}


@mcp.tool()
def save_document(document: str) -> dict:
    """Save a document to its file. A part rolled back with part_end is saved as it is, marker included
    (as in Inventor)."""
    doc = ws.get(document)
    doc.save()
    return doc.info()


@mcp.tool()
def part_end(document: str, before: str | None = None) -> dict:
    """Move the end-of-part marker before a feature, or to the end of the history (before=None).
    Returns position, features behind (suppressed), current volume and bounding box."""
    doc = ws.get(document, PART)
    insp = doc.session.cmd("document.inspect")
    tl = insp.get("timeline", [])
    if before is None:
        doc.session.cmd("timeline.roll_to", {})
        pos = len(tl)
        behind = []
    else:
        idx = None
        for i, f in enumerate(tl):
            if f.get("name") == before or str(f.get("id")) == str(before):
                idx = i
                break
        if idx is None:
            raise ValueError(f"feature {before!r} not found in {document!r}")
        doc.session.cmd("timeline.roll_to", {"position": idx})
        pos = idx
        behind = [f["name"] for f in tl[idx:]]

    snap = state_delta.snapshot(doc.session)
    return {
        "document": document,
        "position": pos,
        "total_features": len(tl),
        "before": before,
        "rolled_back": behind,
        "volume_mm3": snap.get("volume_mm3", 0.0),
        "bbox": snap.get("bbox"),
        "bodies": snap.get("bodies", 0),
    }


@mcp.tool()
def close_document(document: str, discard: bool = False) -> dict:
    """Close an open document without saving. If the document has unsaved changes,
    raises an error unless discard=True."""
    doc = ws.docs.get(document) or ws.get(document)  # no reload check: closing is how to drop a stale copy
    if getattr(doc, "window", False):
        ws.close(document)  # the user's design stays open in the app
        return {"closed": document, "note": "disconnected; the design stays open in the window"}
    is_dirty = doc.session.cmd("document.inspect").get("dirty", False)
    if is_dirty and not discard:
        raise ValueError(
            f"document {document!r} has unsaved changes; call save_document({document!r}) first or pass discard=True"
        )
    ws.close(document)
    return {"closed": document}


_compact = modeling.compact


# The design in the window is the user's: only commands that model, query or check it pass (a positive list, so a
# command added in a later SolidCraft release stays refused until it is looked at). Batch steps that name a tool
# (save, open, new_design, export, undo ...) and anything that reads or writes files are refused (#181 review).
WINDOW_ALLOWED = ("solid.", "sketch.", "construct.", "surface.", "timeline.", "inspect.", "appearance.", "material.",
                  "sheet.", "plastic.", "model.", "body.", "face.", "mesh.", "expr.", "parameters.", "joint.", "contact.",
                  "occurrence.", "assembly.", "explode.", "note.", "motion.", "component.")
WINDOW_REFUSED = ("sketch.insert_dxf", "sketch.insert_svg", "sketch.export_dxf", "sketch.export_svg", "sheet.export_dxf",
                  "sheet.export_bend_table", "parameters.export", "parameters.import", "motion.export",
                  "component.insert_design", "component.replace_with_link", "component.extract", "component.relink",
                  "component.paste_from_design", "component.edit_in_place", "component.finish_edit",
                  "component.update_links", "component.break_link", "timeline.export_script", "assembly.bom")
WINDOW_DOCUMENT_READS = ("document.inspect", "document.metadata", "document.list", "document.revision")
WINDOW_TOOL_STEPS = ("set_parameter", "measure", "inspect_design", "list_commands", "describe_command")
_FILE_KEYS = ("file", "files", "dir", "folder", "directory", "filename")
_FILE_VALUE = re.compile(r"[/\\]|^~|\.(sc|solidcraft|step|stp|stl|3mf|obj|dxf|svg|json|png|jpe?g|gif|csv|txt|pdf|urdf|glb|gltf|wasm|zip)$",
                         re.IGNORECASE)  # a feature name such as "Profil.v2" is not a file (#190)


def _file_param(params):
    """A parameter that names a file or folder: a key such as `file`/`dir`, or a `path`/`out` string that looks
    like one (`solid.sweep` and the like take a geometric `path`, which is not a file)."""
    if isinstance(params, dict):
        for k, v in params.items():
            if k.lower() in _FILE_KEYS and v not in (None, "", [], {}):
                return k
            if k.lower() in ("path", "paths", "out", "output") and isinstance(v, str) and _FILE_VALUE.search(v):
                return k
            hit = _file_param(v)
            if hit:
                return hit
    elif isinstance(params, list):
        for v in params:
            hit = _file_param(v)
            if hit:
                return hit
    return None


def _window_refusal(name, params):
    if not isinstance(name, str) or not name:
        return f"{name!r} is not a command name"
    if name == "execute":  # a batch step that wraps one command
        inner = params if isinstance(params, dict) else {}
        return _window_refusal(inner.get("command"), inner.get("params"))
    if "." not in name:
        if name not in WINDOW_TOOL_STEPS:
            return f"the batch step {name!r} could replace, save or export the user's design"
    elif name in WINDOW_DOCUMENT_READS:
        pass
    elif not name.startswith(WINDOW_ALLOWED) or name.startswith(WINDOW_REFUSED):
        return f"{name!r} could replace, save or close the user's design, or reach files"
    key = _file_param(params)
    if key:
        return f"{name!r} names a file or folder ({key!r})"
    return None


def _window_guard(doc, commands):
    if not getattr(doc, "window", False):
        return
    for c in commands:
        if isinstance(c, str):
            name, params = c, None
        elif isinstance(c, dict):
            name, params = c.get("command"), c.get("params")
        else:
            name, params = c, None
        why = _window_refusal(name, params)
        if why:
            raise ValueError(f"refused on {doc.name!r}, the design in the open SolidCraft window: {why} "
                             "(the user saves, opens and exports in the app)")


def _save_steps_guard(doc, commands):
    """A batch step that saves to a file a connected SolidCraft window shows goes through the same check as
    save_document: never over unsaved work in the window (#190)."""
    targets = []
    for c in commands:
        if not isinstance(c, dict):
            continue
        name, params = c.get("command"), c.get("params") or {}
        if name == "execute" and isinstance(params, dict):
            name, params = params.get("command"), params.get("params") or {}
        if name in ("save", "file.save", "file.save_as", "component.extract"):
            path = params.get("path") if isinstance(params, dict) else None
            target = Path(path) if path else (getattr(doc, "path", None) if name != "component.extract" else None)
            if target is not None and not getattr(doc, "window", False):
                own = getattr(doc, "path", None)
                if own is not None and Path(target).resolve() == Path(own).resolve():
                    cur = doc.disk_mtime()
                    if doc.mtime is not None and cur is not None and cur != doc.mtime:
                        raise ValueError(f"{Path(own).name} changed on disk since {doc.name!r} was loaded here "
                                         "(saved in the SolidCraft app?): close_document it and open it again")
                check_windows_writable(target)
                targets.append(target)
    return targets


@mcp.tool()
def run(document: str, commands: list[dict], verbose: bool = False) -> dict:
    """Run SolidCraft commands ([{command, params}]) in a document, all or nothing. In a part, owned
    sketches are then moved directly before their feature, and a delta report (volume, bounding box,
    body count and warnings) is returned. The reply leaves out empty fields and timings unless verbose.
    A failed step leaves the document as it was; its error has a line "Where: …" naming the edge or face
    it was aimed at, the feature in the way with distance and point, and the largest size that fits. A
    change that makes a later feature fail succeeds and lists that feature in feature_errors (with
    where): fix it or take the change back before going on."""
    doc = ws.get(document)
    _window_guard(doc, commands)
    written = _save_steps_guard(doc, commands)
    try:
        return modeling.run_commands(doc, commands, verbose)
    finally:
        # also after a failed batch: a save step before the failing one has written its file, and the rollback only
        # resets the session. As save_document does, a window showing the file follows it (#190, review #193)
        for target in written:
            if Path(target).exists():
                reload_windows(target)
                if Path(target).resolve() == Path(doc.path).resolve():
                    doc.mtime = doc.disk_mtime()


@mcp.tool()
def browser(document: str, groups: bool = False) -> dict:
    """The model browser, Inventor style: a part's features with their sketches and the end-of-part
    marker, or an assembly's parts with their joints under each part. groups=true adds the same
    items as folders (sketches, work features, relations), each with what it belongs to."""
    doc = ws.get(document)
    t = tree.part_tree(doc.session, groups) if doc.kind == PART else tree.assembly_tree(doc.session, groups, base=doc.base_dir)
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
@sc_errors.explained
def rename_feature(document: str, feature: str, name: str) -> dict:
    """Rename a part feature or sketch in the timeline. The new name must be 1…128 characters
    and unique among features."""
    name = (name or "").strip()
    if not name or len(name) > 128:
        raise ValueError("name must be 1…128 characters")
    doc = ws.get(document, PART)
    tl = sketch_rule.timeline(doc.session)["timeline"]
    existing = {f["name"] for f in tl}
    if feature not in existing:
        raise KeyError(f"feature {feature!r} not found in {document}")
    if name in existing and name != feature:
        raise ValueError(f"another feature is called {name!r}")
    r = doc.session.cmd("timeline.rename", {"feature": feature, "name": name})
    for other in ws.file_docs():
        if other.kind == ASSEMBLY:
            meta = other.metadata()
            conns = meta.get("bolted_connections", {})
            changed = False
            for c in conns.values():
                for p in c.get("parts", []):
                    try:
                        p_file = Path(p.get("file", "")).resolve()
                        if p_file == doc.path.resolve():
                            if p.get("hole_feature") == feature:
                                p["hole_feature"] = name
                                changed = True
                            if "hole_features" in p and feature in p["hole_features"]:
                                p["hole_features"] = [name if f == feature else f for f in p["hole_features"]]
                                changed = True
                    except Exception:
                        pass
            if changed:
                other.set_metadata(meta)
                other.save()
    return {"feature": feature, "name": name, "result": r}


@mcp.tool()
@sc_errors.explained
def insert_part(assembly: str, part_path: str, name: str | None = None, translate: list[float] | None = None,
                rotate: dict | list | None = None, grounded: bool | None = None) -> dict:
    """Place a part or subassembly file in an assembly. A part is linked directly; a subassembly
    is expanded into a parent component with its linked parts and joints underneath.
    rotate can be {axis: [x,y,z], angle: deg, origin?: [x,y,z]}, [axis, angle], or a 4x4 matrix.
    If grounded is None, the part or subassembly parent is grounded if the assembly has no components yet,
    otherwise not."""
    doc = ws.get(assembly, ASSEMBLY)
    return links.insert(ws, doc, part_path, name=name, translate=translate, rotate=rotate, grounded=grounded)


@mcp.tool()
@sc_errors.explained
def add_joint(assembly: str, params: dict, as_built: bool = False) -> dict:
    """Create a joint (params as SolidCraft joint.create takes them, `name` required) and record which
    part face each side sits on, so update_links can check it later.
    With as_built=True (joint.as_built: type, a, b as occurrence names, optional at, name required), joins
    parts where they already sit without moving or rotating them."""
    doc = ws.get(assembly, ASSEMBLY)
    return modeling.add_joint(ws, doc, params, as_built=as_built)


@mcp.tool()
@sc_errors.explained
def edit_joint(assembly: str, joint: str, params: dict) -> dict:
    """Change a joint (params as SolidCraft joint.edit takes them, e.g. flip, offset, a, b) and record
    its part faces again."""
    doc = ws.get(assembly, ASSEMBLY)
    return modeling.edit_joint(ws, doc, joint, params)


@mcp.tool()
@sc_errors.explained
def add_constraint(assembly: str, params: dict) -> dict:
    """Constrain two parts by a rule between a reference on each (params as SolidCraft
    assembly.constraint.create takes them: type mate, flush, distance, concentric, insert, parallel,
    perpendicular, angle, tangent or point_on_axis; a and b as joint origins, e.g. {occurrence, face: [x,y,z]}
    for a plane or {occurrence, circle: [x,y,z]} for a round face; offset, angle, flip, name). b moves.
    Mechvane records the part faces like a joint's, so update_links checks and repairs it; delete it with
    delete_joint."""
    doc = ws.get(assembly, ASSEMBLY)
    return modeling.add_constraint(ws, doc, params)


@mcp.tool()
@sc_errors.explained
def edit_constraint(assembly: str, constraint: str, params: dict) -> dict:
    """Change a constraint's rule, gap (offset), angle, flip, name or suppression (as SolidCraft
    assembly.constraint.edit takes them) and record its part faces again. For other references delete it
    and add a new one."""
    doc = ws.get(assembly, ASSEMBLY)
    return modeling.edit_constraint(ws, doc, constraint, params)


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
    return modeling.adopt_joint(ws, doc, joint)


@mcp.tool()
@sc_errors.explained
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
@sc_errors.explained
def check_parameters(document: str, set: dict) -> dict:
    """Try parameter values on an open document and put the design back (SolidCraft's check_parameters, #108).
    `set` maps parameter names to values ("A": 70, "dh": "8 mm"); at least one. Nothing is kept: the document is
    unchanged afterwards (`restored`: true). Returns `measure` (bodies with volume, bbox, mass; `total`, `body_count`),
    `cylinders` (axis, origin, radius of every cylindrical face: where the holes are), `errors`, `parameter_errors`
    and `warnings`. A variant that cannot be built comes back with `body_count` 0 or fewer/more bodies than the
    base, not always with an error: compare against a run that sets one parameter to its current value."""
    return ws.get(document).session.tool("check_parameters", {"set": set})


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
@sc_errors.explained
def bill_of_materials(assembly: str, path: str | None = None, flat: bool = False) -> dict:
    """Bill of materials (BOM) for an assembly: position, designation, count, file, material (if assigned),
    mass, standard and size for standard parts. With flat=True dissolves subassemblies into their parts;
    with flat=False (default) lists subassemblies as their own rows with nested children.
    If path is given, exports the BOM as a semicolon-separated UTF-8 CSV file."""
    return bom.bill_of_materials(ws, assembly, path=path, flat=flat)


@mcp.tool()
def list_commands(document: str, filter: str | None = None) -> dict:
    """SolidCraft's command catalog with parameter docs; filter matches id, label, tab and panel."""
    r = ws.get(document).session.tool("list_commands", {"filter": filter} if filter else {})
    return r if isinstance(r, dict) else {"commands": r}


@mcp.tool()
def command(document: str, command: str, params: dict | None = None) -> dict:
    """Run one SolidCraft command in a document (queries such as joint.list or document.inspect)."""
    doc = ws.get(document)
    _window_guard(doc, [{"command": command, "params": params}])
    r = doc.session.cmd(command, params or {})
    return r if isinstance(r, dict) else {"result": r}


def _save_or_return_png(raw: bytes, path: str | None, ws: Workspace = ws):
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


def _bounding_box_info(doc) -> tuple[str | None, list[float], list[float]]:
    """Size text, min and max of all bodies; the text is None when the box is not known (no wrong "0 × 0 × 0 mm")."""
    try:
        meas = measure(doc.name)
        bodies = meas.get("bodies", []) if isinstance(meas, dict) else []
        valid_bboxes = [b["bbox"] for b in bodies if b.get("bbox") and "min" in b["bbox"] and "max" in b["bbox"]]
        if valid_bboxes:
            min_pt = [min(b["min"][i] for b in valid_bboxes) for i in range(3)]
            max_pt = [max(b["max"][i] for b in valid_bboxes) for i in range(3)]
            dx = round(max_pt[0] - min_pt[0], 2)
            dy = round(max_pt[1] - min_pt[1], 2)
            dz = round(max_pt[2] - min_pt[2], 2)
            return f"{dx:g} × {dy:g} × {dz:g} mm", min_pt, max_pt
    except Exception:
        pass
    return None, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]


def _bounding_box_str(doc) -> str | None:
    return _bounding_box_info(doc)[0]


def _view_font(size: int = 14, bold: bool = False):
    from PIL import ImageFont
    paths = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "DejaVuSans-Bold.ttf",
            "arialbd.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "DejaVuSans.ttf",
            "arial.ttf",
        ]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


@mcp.tool()
def screenshot(document: str, view: str = "iso", path: str | None = None):
    """Render a document headless (views: iso, front, top, right, …).
    If path is given, saves the PNG file under this path (relative to the workspace,
    not outside) and returns path, size in bytes and image dimensions instead of the image."""
    doc = ws.get(document)
    r = doc.session.tool("screenshot", _shot_args(doc, view))
    raw = base64.b64decode(r["images"][0]["image"])
    return _save_or_return_png(raw, path, ws)


_WINDOW_VIEWS = {"iso": "view.isometric", "front": "view.front", "top": "view.top", "right": "view.right",
                 "left": "view.left", "back": "view.back", "bottom": "view.bottom", "home": "view.home"}


def _shot_args(doc, view):
    """Screenshot arguments. In the window: a render of the model, not the app's chrome, after turning the app's
    camera to `view` and fitting it (a named view alone keeps the app's zoom; SolidCraft 0.43 cannot read the
    camera back to restore it, and neither leaves an undo entry, checked live 2026-11-24)."""
    if not getattr(doc, "window", False):
        return {"view": view}
    cmd = _WINDOW_VIEWS.get(view)
    if cmd is None:
        return {"view": view, "source": "model"}  # a named view saved with view.save
    doc.session.cmd(cmd)
    doc.session.cmd("view.fit")
    return {"source": "model"}


@mcp.tool()
def verify_view(document: str, section: dict | None = None, path: str | None = None):
    """Render a 2x2 visual verification image (Iso, Front, Top, Section) of the document.
    Each quadrant shows its view label and bounding box dimensions in mm.
    If path is given, saves the PNG file under this path (relative to the workspace,
    not outside) and returns path, size in bytes and image dimensions instead of the image."""
    from PIL import Image as PILImage, ImageDraw

    doc = ws.get(document)
    bbox_str, min_pt, max_pt = _bounding_box_info(doc)

    views = [
        ("iso", "Iso"),
        ("front", "Front"),
        ("top", "Top"),
    ]
    raw_images = []
    for v, lbl in views:
        r = doc.session.tool("screenshot", _shot_args(doc, v))
        raw_images.append((base64.b64decode(r["images"][0]["image"]), lbl))

    # Section view: cut through the middle of the bounding box (normal X by default)
    # or user-specified plane/offset/at.
    mid_x = (min_pt[0] + max_pt[0]) / 2.0
    mid_y = (min_pt[1] + max_pt[1]) / 2.0
    mid_z = (min_pt[2] + max_pt[2]) / 2.0

    sec_lbl = "Section"
    if section:
        sec_params = dict(section)
        sec_view = sec_params.pop("view", None)
        plane_u = str(sec_params.get("plane", "")).upper()
        if not sec_view:
            if plane_u == "XZ":
                sec_view = "front"
            elif plane_u == "XY":
                sec_view = "top"
            else:
                sec_view = "right"
        if "at" not in sec_params and "offset" not in sec_params:
            if plane_u == "YZ":
                sec_params["at"] = round(mid_x, 4)
            elif plane_u == "XZ":
                sec_params["at"] = round(mid_y, 4)
            elif plane_u == "XY":
                sec_params["at"] = round(mid_z, 4)
    else:
        sec_params = {"plane": "YZ", "at": round(mid_x, 4)}
        sec_view = "right"

    try:
        if getattr(doc, "window", False) and not section:
            # a section of our own would replace and then clear one the user set in the window (#181)
            raise ValueError("no unasked section in the window")
        doc.session.cmd("inspect.section", sec_params)
        try:
            r = doc.session.tool("screenshot", _shot_args(doc, sec_view))
            raw_images.append((base64.b64decode(r["images"][0]["image"]), sec_lbl))
        finally:
            try:
                doc.session.cmd("inspect.section", {"clear": True})
            except Exception:
                pass
    except Exception:
        # Fallback to plain right view if inspect.section fails
        r = doc.session.tool("screenshot", _shot_args(doc, "right"))
        raw_images.append((base64.b64decode(r["images"][0]["image"]), "Right"))

    pil_images = [PILImage.open(io.BytesIO(raw)).convert("RGB") for raw, _ in raw_images]
    w, h = pil_images[0].size
    combined = PILImage.new("RGB", (2 * w, 2 * h), "white")
    combined.paste(pil_images[0], (0, 0))
    combined.paste(pil_images[1], (w, 0))
    combined.paste(pil_images[2], (0, h))
    combined.paste(pil_images[3], (w, h))

    draw = ImageDraw.Draw(combined)
    f_bold = _view_font(18, bold=True)
    f_reg = _view_font(15, bold=False)

    coords = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for (col, row), (_, lbl) in zip(coords, raw_images):
        x0, y0 = col * w, row * h
        # Label badge at top-left
        tb = draw.textbbox((0, 0), lbl, font=f_bold)
        lw, lh = tb[2] - tb[0], tb[3] - tb[1]
        draw.rectangle([x0 + 16, y0 + 16, x0 + 16 + lw + 16, y0 + 16 + lh + 12], fill=(30, 30, 30))
        draw.text((x0 + 24, y0 + 20), lbl, fill=(255, 255, 255), font=f_bold)

        # Bounding box badge at bottom (left out when the size is not known)
        if bbox_str:
            dim_text = f"Size: {bbox_str}"
            tb2 = draw.textbbox((0, 0), dim_text, font=f_reg)
            dw, dh = tb2[2] - tb2[0], tb2[3] - tb2[1]
            draw.rectangle([x0 + 16, y0 + h - dh - 24, x0 + 16 + dw + 16, y0 + h - 14], fill=(30, 30, 30))
            draw.text((x0 + 24, y0 + h - dh - 20), dim_text, fill=(255, 255, 255), font=f_reg)

    # Dividers between panels
    draw.line([(w, 0), (w, 2 * h)], fill=(180, 180, 180), width=2)
    draw.line([(0, h), (2 * w, h)], fill=(180, 180, 180), width=2)

    buf = io.BytesIO()
    combined.save(buf, format="PNG")
    raw = buf.getvalue()
    return _save_or_return_png(raw, path, ws)


@mcp.tool()
def export_gltf(document: str, path: str) -> dict:
    """Write a part or assembly as glTF 2.0 with its appearance (colour, metallic, roughness, IOR per body),
    for Blender, three.js and other viewers (ADR 0004). `path` is relative to the workspace or absolute."""
    from .gltf_export import export_gltf as _export
    doc = ws.get(document)
    target = Path(path)
    if not target.is_absolute():
        target = ws.root / target
    return _export(doc, target, ws=ws)


@mcp.tool()
def check_design(document: str, profile: str | None = None, build_direction: str = "+Z",
                 material: str | None = None, remember: bool = False) -> dict:
    """Check a part against design rules (wall thickness, hole edge distance, thread depth, printability).
    `profile` defaults to the one saved in the part file, else fdm_0.4.
    `build_direction` selects the print direction ('+Z', '-Z', '+X', '-X', '+Y', '-Y'; default '+Z').
    `material` (steel, cast_iron, alu, alu_wrought, alu_cast, brass, ...) sets the thread engagement depth
    from the same table as bolted_connection; without it the material saved in the part file applies,
    then the material assigned to the bodies (SolidCraft material.assign), else the profile's 1.5 × d.
    `remember=True` saves the given profile and material in the part file (the review page shows and
    uses them too)."""
    vec = design_rules.parse_build_direction(build_direction, allow_vector=False)
    doc = ws.get(document, PART)
    if remember:
        design_rules.save_rules(doc, profile=profile, material=material)
    return design_rules.check(doc, profile=profile, build_direction=vec, material=material)


@mcp.tool()
@sc_errors.explained
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
@sc_errors.explained
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
@sc_errors.explained
def edit_in_place(assembly: str, occurrence: str, point: list[float] | None = None) -> dict:
    """Open the part file behind an occurrence (including subassemblies like 'Sub:1/Plate:1') for
    in-place editing. If already open, returns the existing document. Returns document name and the
    occurrence transformation for converting coordinates. If point is given, converts it to part coordinates."""
    return inplace.edit_in_place(ws, assembly, occurrence, point=point)


@mcp.tool()
@sc_errors.explained
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

