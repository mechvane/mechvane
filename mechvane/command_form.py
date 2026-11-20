"""Form fields for any SolidCraft command, made from its input schema (describe_command), for the general
command dialog of the workspace (Ctrl+K, #128).

Each top-level property of the schema becomes one field. The kind follows the JSON schema structure, not
the property name:

    expr    a number or an expression ("w / 2", "30 mm")      number  a plain number or integer
    enum    one value of a fixed list                         bool    a switch
    text    a string                                          list    a name or a list of names
    point   three coordinates (each a number or expression)   json    anything else, typed as JSON

A field that takes edges, faces or bodies carries `pick`, `multi` and `write` (see _pick), so the dialog
can fill it with clicks in the view. A command without a
schema gets one json field for all its parameters, with SolidCraft's one-line parameter text as help
(as SolidCraft's own command box takes `id {json}`).

Which commands the dialog offers: all except EXCEPTED (app commands with no meaning in the workspace),
PROVISIONAL (act only on SolidCraft's hidden window; left out of the count for now) and DEFERRED (not offered
yet; each with its reason). The acceptance test counts the offered ones (tools/acceptance.py).
"""

import re

# Commands that only steer SolidCraft's own window. They are not part of the acceptance count (user 2026-11-16).
EXCEPTED = {
    "panel.": "a panel of SolidCraft's own window",
    "tab.": "a ribbon tab of SolidCraft's own window",
    "ui.": "SolidCraft's own window",
}

# Commands the general dialog does not offer yet. They count as not reachable until their reason is solved.
DEFERRED = {
    "sketch.": "runs in the sketch environment: open a sketch first (Create 2D Sketch, or double-click a sketch)",
    "joint.create": "made with Mechvane's add_joint so the joint can be checked later",
    "joint.edit": "changed with Mechvane's edit_joint so the joint can be checked later",
    "file.": "reads or writes a path, sends to a slicer or uploads: needs a file picker",
    "doc.": "opens or recovers another file: the workspace opens files itself",
    "document.": "metadata and units of the file: needs its own check (Mechvane keeps keys there)",
    "edit.": "SolidCraft's own undo and checkpoints would bypass the workspace's undo list",
    "plugin.": "installs or runs code: needs the user's review of the plugin",
    "library.apply": "reads a library file from a path",
    "library.export": "writes a file",
    "library.inspect": "reads a file from a path",
    "settings.": "SolidCraft's app settings and profiles (files outside the design)",
    "layout.": "SolidCraft's own window layout",
    "diagnostics.": "crash reports, issue reports to SolidCraft's servers, kernel switches",
    "canvas.insert": "reads an image from a path",
    "canvas.decal": "reads an image from a path",
    # Mechvane wraps these with checks of its own: the raw command would skip them
    "timeline.roll_to": "the workspace shows no rolled-back part yet (Mechvane's part_end rolls it only for the agent)",
    "timeline.rollback": "the workspace shows no rolled-back part yet (Mechvane's part_end rolls it only for the agent)",
    "joint.as_built": "Mechvane's adopt_joint keeps the joint checkable",
    "assembly.constraint.create": "its two references are taken with the workspace's own picker (component, face), not as raw references",
    "component.delete": "removes a part from the assembly: Mechvane's joints and bolted connections must follow",
    "component.break_link": "turns a linked part into a copy: Mechvane's links must follow",
    "selection.delete": "deletes through SolidCraft's selection: Mechvane's delete keeps owned sketches and joints",
    "selection.get": "reads SolidCraft's hidden selection, not the workspace's",
    "browser.collapse_all": "acts only on SolidCraft's hidden model browser",
    "browser.expand_all": "acts only on SolidCraft's hidden model browser",
}

# Commands that only act on SolidCraft's hidden window while Mechvane drives it headless: nothing shows in the
# workspace. Not offered, and left out of the acceptance count for now, each with its reason (decision A, user
# 2026-11-19); the audit of 2026-11-30 looks at them again (a workspace connected to the running app, --connect).
PROVISIONAL = {
    "view.": "acts only on SolidCraft's hidden window, not on the workspace's view",
    "render.": "renders in SolidCraft's hidden window; the picture does not reach the workspace",
    "select.": "selects in SolidCraft's hidden window, not in the workspace",
}

# Commands the dialog offers, but runs through Mechvane's own handler instead of the raw command: the handler
# keeps what Mechvane records (owned sketches, joint records, links) and refuses what would break the design.
# Each id needs its handler in ui/server.py (ROUTES); a routed id without one is refused, never run raw.
# value: True when a preview cannot be taken back (it changes Mechvane's own records, not only SolidCraft's).
ROUTED = {
    "timeline.edit": False,
    "timeline.delete": True,
    "timeline.rename": True,
    "joint.delete": True,
    "assembly.constraint.edit": True,
    "component.update_links": True,
}


def routed(command: str) -> bool:
    return command in ROUTED


def no_preview(command: str) -> bool:
    """A routed command that changes Mechvane's records, or one that writes a file."""
    return bool(ROUTED.get(command)) or (FILE_COMMANDS.get(command) or ("", "", ()))[1] == "write"


# Commands that read or write a file, offered with a file choice in the project folder (#128): the field that
# takes the path, read (the file must exist there) or write, and the file types. Design files are never written.
# A command that writes has no preview (the preview would write the file). The server resolves the name inside
# the project folder and refuses anything else; SolidCraft's session allows only that folder, too.
FILE_COMMANDS = {
    "parameters.import": ("path", "read", (".csv", ".json")),
    "inspect.compare_picture": ("reference", "read", (".png", ".jpg", ".jpeg")),
    "pointcloud.insert": ("path", "read", (".ply", ".xyz", ".pts")),
    "file.insert_mesh": ("path", "read", (".stl", ".obj", ".3mf", ".ply", ".glb", ".gltf")),
    "canvas.insert": ("path", "read", (".png", ".jpg", ".jpeg")),
    "canvas.decal": ("path", "read", (".png", ".jpg", ".jpeg")),
    "library.inspect": ("path", "read", (".json",)),
    "library.apply": ("path", "read", (".json",)),
    "parameters.export": ("path", "write", (".csv", ".json")),
    "assembly.bom": ("path", "write", (".csv", ".json")),
    "motion.export": ("path", "write", (".csv", ".json")),
    "motion.export_animation": ("path", "write", (".gif",)),
    "sheet.export_bend_table": ("path", "write", (".csv", ".json")),
    "sheet.export_dxf": ("path", "write", (".dxf",)),
    "timeline.export_script": ("path", "write", (".json",)),
    "file.export": ("path", "write", (".step", ".stp", ".stl", ".3mf", ".obj", ".glb")),
    "file.export_step": ("path", "write", (".step", ".stp")),
    "file.export_stl": ("path", "write", (".stl",)),
    "file.export_3mf": ("path", "write", (".3mf",)),
    "file.export_obj": ("path", "write", (".obj",)),
    "file.save_mesh": ("path", "write", (".stl", ".3mf")),
    "library.export": ("path", "write", (".json",)),
}


# Parameters of a file command the dialog does not take: they would start another program (a slicer) or
# write somewhere else than the chosen file.
FILE_REFUSED_PARAMS = {
    "file.save_mesh": ("slicer", "single_instance"),
    "library.export": ("overwrite",),  # the dialog asks before overwriting instead
}
# file.export: the formats it may write (not urdf, which writes meshes beside the file, nor json, the design)
EXPORT_FORMATS = ("stl", "stla", "obj", "step", "3mf", "3mf-tagged", "glb")


def file_command(command: str) -> tuple[str, str, tuple] | None:
    """(field, read|write, file types) for a command offered with a file choice, or None."""
    return FILE_COMMANDS.get(command)


def _match(command: str, table: dict) -> str | None:
    for key, reason in table.items():
        if command == key or (key.endswith(".") and command.startswith(key)):
            return reason
    return None


# Commands that model a body: in Mechvane they belong in a part file. In an assembly SolidCraft would add the
# body to the assembly or change the embedded copy of a linked part, which the next update_links overwrites.
PART_ONLY = ("solid.", "surface.", "sheet.", "plastic.", "body.", "mesh.", "frame.")
PART_REASON = "features are added in a part; open the part file"


def part_only(command: str) -> bool:
    return command.startswith(PART_ONLY)


def excepted(command: str) -> str | None:
    """Why a command is outside the acceptance list, or None."""
    return _match(command, EXCEPTED)


def provisional(command: str) -> str | None:
    """Why a command is left out of the acceptance count for now (PROVISIONAL), or None. It is not offered."""
    return _match(command, PROVISIONAL)


def deferred(command: str) -> str | None:
    """Why the dialog does not offer a command yet, or None. A routed command is offered (it has a handler)."""
    return None if command in ROUTED or command in FILE_COMMANDS else _match(command, DEFERRED)


FILE_FIELDS = re.compile(r"\.(sc|solidcraft|json|csv|png|jpe?g|ply|xyz|pts|hdr|dxf|svg|glb|gltf|step|stl|3mf|obj|zip)\b"
                         r"|\b(PNG|JPEG|HDR|CSV|DXF)\b|\bfiles?\b|\bfolder\b|destination|saved design|a design\b|\bwrite", re.I)
FILE_REASON = "reads or writes a file outside the design: needs a file picker"


def file_field(fm: dict) -> str | None:
    """The name of a field that takes a file path (path, from_design, reference ...), or None. The general
    dialog does not offer such commands yet: a path typed into a form could read or write anywhere."""
    for f in fm.get("fields", []):
        if f["kind"] in ("text", "json") and f["name"] in ("path", "from_design", "reference", "dir", "file") \
                and FILE_FIELDS.search(f.get("description") or ""):
            return f["name"]
    if fm.get("raw") and re.search(r"(^|[;\s])(path|reference|from_design)\??:", fm.get("help") or "") \
            and FILE_FIELDS.search(fm.get("help") or ""):
        return "path"
    return None


# The sketch environment (#128): while a sketch is open the dialog offers sketch.* (and changing a dimension's
# parameter) and runs them in the sketch session, one undo step each in the sketch's own undo; opening and
# closing sketches stay with the workspace, and the model waits until the sketch is finished.
SKETCH_LIFECYCLE = {"sketch.create", "sketch.edit", "sketch.finish", "sketch.finish_auto_constrain", "sketch.cancel"}
SKETCH_ALSO = {"parameters.change"}
SKETCH_LIFECYCLE_REASON = "the workspace opens and finishes sketches itself (Finish Sketch, Esc to cancel)"
SKETCH_OPEN_REASON = "a sketch is open: finish it first (Finish Sketch), the model waits until then"
SKETCH_3D = {
    "sketch.line3d",
    "sketch.arc3d",
    "sketch.point3d",
    "sketch.spline3d",
    "sketch.move3d",
    "sketch.include_3d",
}
SKETCH_3D_HINT = "3D sketch command: switch the sketch to 3D first (sketch.options with sketch_3d: true)."


def in_sketch_command(command: str) -> bool:
    """A command the sketch session runs (it refuses the rest)."""
    return (command.startswith("sketch.") and command not in SKETCH_LIFECYCLE) or command in SKETCH_ALSO


def why_not(command: str, fm: dict | None = None, in_sketch: bool = False) -> str | None:
    """Why the general dialog does not offer a command (excepted, deferred, a file path), or None. in_sketch:
    a sketch is open, so only the sketch environment's commands are offered."""
    if in_sketch:
        if command in SKETCH_LIFECYCLE:
            return SKETCH_LIFECYCLE_REASON
        if not in_sketch_command(command):
            return SKETCH_OPEN_REASON
        reason = excepted(command)
        if reason is None and fm is not None and file_field(fm):
            reason = FILE_REASON
        return reason
    reason = excepted(command) or provisional(command) or deferred(command)
    if reason is None and fm is not None and command not in FILE_COMMANDS and file_field(fm):
        reason = FILE_REASON
    return reason


def offered(command: str, fm: dict | None = None) -> bool:
    return why_not(command, fm) is None


def _resolve(node, defs: dict, seen=()) -> tuple[dict, str]:
    """Follow $ref (and a single-branch allOf) to the node; returns it with the last $defs name on the way."""
    name = ""
    while isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            key = ref[len("#/$defs/"):]
            if key in seen or key not in defs:
                return {}, name
            seen = seen + (key,)
            name = key
            merged = dict(defs[key])
            if node.get("description") and not merged.get("description"):
                merged["description"] = node["description"]
            node = merged
            continue
        all_of = node.get("allOf")
        if isinstance(all_of, list) and len(all_of) == 1:
            rest = {k: v for k, v in node.items() if k != "allOf"}
            node = dict(all_of[0], **rest)
            continue
        return node, name
    return {}, name


def _types(node: dict) -> set:
    t = node.get("type")
    return set(t) if isinstance(t, list) else ({t} if t else set())


def _branches(node: dict, defs: dict, seen=()) -> tuple[list[dict], bool]:
    """The alternatives of a node without its null branch, and whether null is allowed."""
    nullable = False
    alts = node.get("anyOf") or node.get("oneOf")
    if not isinstance(alts, list):
        t = _types(node)
        if "null" in t and len(t) > 1:
            rest = sorted(t - {"null"})
            return [dict(node, type=rest[0] if len(rest) == 1 else rest)], True
        return [node], False
    out = []
    for a in alts:
        a, _ = _resolve(a, defs, seen)
        if _types(a) == {"null"}:
            nullable = True
            continue
        sub, sub_null = _branches(a, defs, seen)
        out.extend(sub)
        nullable = nullable or sub_null
    return out, nullable


def _scalar(node: dict) -> str | None:
    """number, string, boolean, enum or None for a single (non-union) node."""
    if isinstance(node.get("enum"), list) or "const" in node:
        return "enum"
    t = _types(node) - {"null"}
    if t <= {"number", "integer"} and t:
        return "number"
    if t == {"boolean"}:
        return "bool"
    if t == {"string"}:
        return "string"
    if t == {"number", "string"} or t == {"integer", "string"}:
        return "expr"
    return None


def _is_numberlike(node: dict, defs: dict) -> bool:
    branches, _ = _branches(node, defs)
    kinds = {_scalar(b) for b in branches}
    return bool(kinds & {"number", "expr"}) and kinds <= {"number", "string", "expr"}


def _is_point(branches: list[dict], defs: dict) -> bool:
    """[x, y, z] or {x, y, z}, each number-like."""
    seen_shape = False
    for b in branches:
        t = _types(b)
        if t == {"array"}:
            items, _ = _resolve(b.get("items") or {}, defs)
            if b.get("minItems") != 3 or b.get("maxItems") != 3 or not _is_numberlike(items, defs):
                return False
            seen_shape = True
        elif t == {"object"}:
            props = b.get("properties") or {}
            if set(props) != {"x", "y", "z"} or not all(_is_numberlike(_resolve(p, defs)[0], defs) for p in props.values()):
                return False
            seen_shape = True
        else:
            return False
    return seen_shape


def _is_namelist(branches: list[dict], defs: dict) -> bool:
    """A name, or a list of names."""
    for b in branches:
        t = _types(b)
        if t == {"string"} and "enum" not in b:
            continue
        if t == {"array"}:
            items, _ = _resolve(b.get("items") or {}, defs)
            if _types(items) == {"string"} and "enum" not in items:
                continue
        return False
    return any(_types(b) == {"array"} for b in branches)


def _words(name: str, def_name: str) -> str:
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", f"{name} {def_name}").replace("_", " ").lower()


def _accepts_point(node: dict, defs: dict) -> bool:
    """A branch of node is [x, y, z] (each number-like)."""
    branches, _ = _branches(node, defs)
    for b in branches:
        if _types(b) == {"array"} and b.get("minItems") == 3 and b.get("maxItems") == 3 \
                and _is_numberlike(_resolve(b.get("items") or {}, defs)[0], defs):
            return True
    return False


def _keyed_point(node: dict, defs: dict, key: str) -> bool:
    """A branch of node is the object {key: [x, y, z]} (GeoRef's {"face": ...}, {"edge": ...})."""
    branches, _ = _branches(node, defs)
    for b in branches:
        props = b.get("properties") or {}
        if _types(b) == {"object"} and b.get("required") == [key] and key in props \
                and _accepts_point(_resolve(props[key], defs)[0], defs):
            return True
    return False


GEOMETRY = {"edges": (r"\bedges?\b", "edge"), "faces": (r"\bfaces?\b", "face")}
BODY_FIELD = re.compile(r"^(body|bodies|target_body|target_bodies|tool_body|tool_bodies)$")


def _pick(name: str, def_name: str, node: dict, branches: list[dict], defs: dict, kind: str) -> dict | None:
    """How the dialog fills a field from a click in the view, or None: {pick: edges|faces|bodies, multi, write}.
    What is picked comes from the field and $defs names only (not the description, which names faces and edges
    in many fields that take something else); how it is written comes from the schema: write "point" ([x, y, z]),
    "key:face"/"key:edge" ({"face": [x, y, z]}) or "name" (a body name); multi when a branch is a list of them
    (then the list is written)."""
    if kind in ("text", "list"):
        if not BODY_FIELD.match(name):
            return None
        return {"pick": "bodies", "multi": kind == "list", "write": "name"}
    if kind != "json":
        return None
    words = _words(name, def_name)
    target = next((t for t, (pattern, _) in GEOMETRY.items() if re.search(pattern, words)), None)
    if target is None:
        return None
    key = GEOMETRY[target][1]

    def write_of(n):
        n, _ = _resolve(n, defs)
        if _accepts_point(n, defs):
            return "point"
        if _keyed_point(n, defs, key):
            return f"key:{key}"
        return None

    multi = None
    for b in branches:
        if _types(b) == {"array"} and b.get("items") is not None:
            w = write_of(b["items"])
            if w:
                multi = w
    if multi:
        return {"pick": target, "multi": True, "write": multi}
    single = write_of(node)
    return {"pick": target, "multi": False, "write": single} if single else None


def field(name: str, node: dict, defs: dict, required: bool) -> dict:
    """One form field for a top-level property."""
    node, def_name = _resolve(node, defs)
    description = (node.get("description") or "").strip()
    branches, nullable = _branches(node, defs)
    out = {"name": name, "required": required and not nullable, "description": description}
    if "default" in node and node["default"] is not None:
        out["default"] = node["default"]
    kinds = {_scalar(b) for b in branches}
    if len(branches) == 1 and kinds == {"enum"}:
        b = branches[0]
        out.update(kind="enum", options=list(b["enum"]) if "enum" in b else [b["const"]])
    elif kinds == {"bool"}:
        out["kind"] = "bool"
    elif kinds == {"number"}:
        out["kind"] = "number"
        if any(_types(b) == {"integer"} for b in branches):
            out["integer"] = True
    elif kinds and kinds <= {"number", "string", "expr"} and ("number" in kinds or "expr" in kinds) \
            and all("enum" not in b for b in branches):
        out["kind"] = "expr"
    elif kinds == {"string"} and len(branches) == 1:
        out["kind"] = "text"
    elif _is_point(branches, defs):
        out["kind"] = "point"
    elif _is_namelist(branches, defs):
        out["kind"] = "list"
    else:
        out["kind"] = "json"
    pick = _pick(name, def_name, node, branches, defs, out["kind"])
    if pick:
        out.update(pick)
    return out


def form(describe: dict, row: dict | None = None) -> dict:
    """The dialog for one command: its describe_command answer (and optionally its list_commands row,
    for the tab and panel) → {id, label, help, description, fields, raw}. raw: no schema, one json field."""
    row = row or {}
    cid = describe.get("id") or row.get("id")
    out = {"id": cid, "label": describe.get("label") or row.get("label") or cid, "help": describe.get("params") or row.get("params") or "",
           "tab": row.get("tab"), "panel": row.get("panel")}
    schema = describe.get("input")
    if not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict):
        if isinstance(schema, dict) and schema.get("type") == "object" and not schema.get("properties") \
                and schema.get("additionalProperties") is False:
            return dict(out, description=(schema.get("description") or "").strip(), fields=[], raw=False)
        return dict(out, description="", fields=[{"name": "", "kind": "json", "required": False,
                                                  "description": out["help"]}], raw=True)
    defs = schema.get("$defs") or {}
    required = set(schema.get("required") or [])
    fields = [field(name, node, defs, name in required) for name, node in schema["properties"].items()]
    fc = FILE_COMMANDS.get(cid)
    if fc:
        # the path field becomes a file choice in the project folder (the server fills `choices`)
        fields = [dict(f, kind="text", file={"mode": fc[1], "types": list(fc[2])}) if f["name"] == fc[0] else f
                  for f in fields]
    return dict(out, description=(schema.get("description") or "").strip(), fields=fields, raw=False)


def to_params(fm: dict, values: dict) -> dict:
    """Turn the dialog's values ({field name: value as the form holds it}) into command params. Used by the
    server to check a form submission the same way the dialog builds it, and by the tests."""
    if fm.get("raw"):
        v = values.get("", {})
        if not isinstance(v, dict):
            raise ValueError("the parameters must be a JSON object")
        return v
    params = {}
    for f in fm["fields"]:
        if f["name"] not in values:
            continue
        v = values[f["name"]]
        if v is None or v == "" or v == []:
            continue
        params[f["name"]] = v
    missing = [f["name"] for f in fm["fields"] if f["required"] and f["name"] not in params]
    if missing:
        raise ValueError(f"required: {', '.join(missing)}")
    return params
