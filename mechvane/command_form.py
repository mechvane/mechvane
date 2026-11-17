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

Which commands the dialog offers: all except EXCEPTED (app commands with no meaning in the workspace) and
DEFERRED (not offered yet; each with its reason). The acceptance test counts the offered ones (tools/acceptance.py).
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
    "sketch.": "runs inside the sketch environment, which has its own undo (second step of #128)",
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
    "timeline.edit": "changed in the feature dialogs, which refuse an edit that breaks a later feature",
    "timeline.delete": "deleted from the model browser, which takes the feature's own sketch along",
    "timeline.rename": "renamed from the model browser, which keeps names unique",
    "timeline.roll_to": "Mechvane's part_end rolls the part and back",
    "timeline.rollback": "Mechvane's part_end rolls the part and back",
    "joint.delete": "Mechvane's delete_joint also drops what Mechvane keeps about the joint",
    "joint.as_built": "Mechvane's adopt_joint keeps the joint checkable",
    "assembly.constraint.": "Mechvane's add_constraint and edit_constraint keep the rule checkable",
    "component.update_links": "Mechvane's update_links reports joints that moved to another face",
    "component.delete": "removes a part from the assembly: Mechvane's joints and bolted connections must follow",
    "component.break_link": "turns a linked part into a copy: Mechvane's links must follow",
    "selection.delete": "deletes through SolidCraft's selection: Mechvane's delete keeps owned sketches and joints",
    # These only act on SolidCraft's hidden window: nothing shows in the workspace (user to decide: excepted?)
    "view.": "acts only on SolidCraft's hidden window, not on the workspace's view",
    "render.": "renders in SolidCraft's hidden window; the picture does not reach the workspace yet",
    "select.": "selects in SolidCraft's hidden window, not in the workspace",
    "selection.get": "reads SolidCraft's hidden selection, not the workspace's",
    "browser.collapse_all": "acts only on SolidCraft's hidden model browser",
    "browser.expand_all": "acts only on SolidCraft's hidden model browser",
}


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


def deferred(command: str) -> str | None:
    """Why the dialog does not offer a command yet, or None."""
    return _match(command, DEFERRED)


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


def why_not(command: str, fm: dict | None = None) -> str | None:
    """Why the general dialog does not offer a command (excepted, deferred, a file path), or None."""
    reason = excepted(command) or deferred(command)
    if reason is None and fm is not None and file_field(fm):
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
