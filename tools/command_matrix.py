#!/usr/bin/env python3
"""command_matrix.py - Query SolidCraft commands and schemas, classify parameters, and build matrix.

Queries a headless SolidCraft session for all commands and their parameter schemas,
classifies each parameter into UI input widget types (Zahl/Ausdruck, Auswahlliste (enum),
Schalter, Text, Auswahl in der Ansicht, or unklar) using schema-type-first rules derived
directly from the JSON Schema and `$defs`, and writes the result matrix to
`build/befehlsmatrix.json` by default.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mechvane.solidcraft import Session


def _norm_type(node: dict) -> str | list | None:
    """Normalize JSON Schema `type` by stripping `null`."""
    t = node.get("type")
    if isinstance(t, list):
        nn = [x for x in t if x != "null"]
        return nn[0] if len(nn) == 1 else (nn or None)
    return t


def _extract_enums(obj: dict) -> list | None:
    """Return explicit enum/const options from a schema node if present."""
    if not isinstance(obj, dict):
        return None
    if obj.get("enum"):
        return obj["enum"]
    if "oneOf" in obj:
        vals = []
        for branch in obj["oneOf"]:
            if not isinstance(branch, dict):
                return None
            if "const" in branch:
                vals.append(branch["const"])
            elif "enum" in branch:
                vals.extend(branch["enum"])
            else:
                return None
        if vals:
            return vals
    return None


def _is_choice_pattern(pattern: str | None) -> bool:
    """Return True if a regex pattern encodes a finite anchored keyword choice (e.g. csv|json)."""
    if not pattern or not pattern.startswith("^") or "[^" in pattern:
        return False
    # Finite alternation (`a|b|c`) or short anchored char-class choice (`^[gG][123]$`)
    if "|" in pattern:
        return True
    return len(pattern) <= 24 and bool(re.fullmatch(r"\^(\[[A-Za-z0-9]+\])+\$", pattern))


def _unwrap_node(node: dict, defs: dict, seen: set[str] | None = None) -> tuple[dict, list[str], str]:
    """Resolve `$ref` and single-branch nullable `anyOf` wrappers, collecting ref names and description."""
    if not isinstance(node, dict):
        return {}, [], ""
    seen = set(seen or ())
    refs: list[str] = []
    descs: list[str] = []
    cur = node

    for _ in range(8):
        if cur.get("description"):
            descs.append(cur["description"].strip())

        if "$ref" in cur:
            rname = cur["$ref"].split("/")[-1]
            if rname in seen or rname not in defs:
                refs.append(rname)
                break
            seen.add(rname)
            refs.append(rname)
            cur = defs[rname]
            continue

        if "anyOf" in cur:
            non_null = [v for v in cur["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
            if len(non_null) == 1:
                cur = non_null[0]
                continue
        break

    if cur.get("description") and cur["description"].strip() not in descs:
        descs.append(cur["description"].strip())
    return cur, refs, descs[0] if descs else ""


def resolve_type_info(pdef: dict, defs: dict) -> tuple[str | None, str | list | None, list | None, str, str | None]:
    """Resolve reference name, normalized schema type, enum options, description, and array item ref."""
    node, refs, desc = _unwrap_node(pdef, defs)
    ref_name = refs[-1] if refs else None

    ptype = _norm_type(node)
    if not ptype and "anyOf" in node:
        non_null = [v for v in node["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
        vtypes = []
        for branch in non_null:
            bnode, _, _ = _unwrap_node(branch, defs)
            bt = _norm_type(bnode)
            if isinstance(bt, list):
                vtypes.extend(bt)
            elif bt:
                vtypes.append(bt)
        if vtypes and len(vtypes) >= len(non_null):
            uniq = list(dict.fromkeys(vtypes))
            ptype = uniq[0] if len(uniq) == 1 else uniq

    enums = _extract_enums(pdef) or _extract_enums(node)
    if not enums and "anyOf" in node:
        for branch in node["anyOf"]:
            if isinstance(branch, dict) and branch.get("type") != "null":
                enums = _extract_enums(branch)
                if enums:
                    break

    items_node = node.get("items") or {}
    items_ref = None
    if isinstance(items_node, dict) and "$ref" in items_node:
        items_ref = items_node["$ref"].split("/")[-1]
    elif isinstance(items_node, dict) and "anyOf" in items_node:
        for branch in items_node["anyOf"]:
            if isinstance(branch, dict) and "$ref" in branch:
                items_ref = branch["$ref"].split("/")[-1]
                break

    return ref_name, ptype, enums, desc, items_ref


def _is_numeric_scalar(node: dict, defs: dict) -> bool:
    """Return True if a schema node is a pure number/integer or a numeric expression union."""
    unwrapped, _, desc = _unwrap_node(node, defs)
    t = _norm_type(unwrapped)
    if t in ("number", "integer"):
        return True
    if "anyOf" in unwrapped:
        non_null = [v for v in unwrapped["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
        if non_null and all(
            _norm_type(_unwrap_node(b, defs)[0]) in ("number", "integer", "string") for b in non_null
        ):
            return _is_expression_union(unwrapped, non_null, desc)
    if isinstance(t, list) and set(t) <= {"number", "integer", "string"}:
        return _is_expression_union(unwrapped, [], desc)
    return False


def _is_expression_union(node: dict, branches: list[dict], desc: str) -> bool:
    """Distinguish numeric-expression unions (`LengthExpr`, `AngleExpr`) from ID-or-name selectors."""
    dl = desc.lower()
    if any(w in dl for w in ("by id", "id or name", "by name or id", "by id or", "or its name", "or name")):
        return False
    if any(w in dl for w in ("expression", "radians", "degrees", "unitless", "length", "angle", "timeline position")):
        return True
    for b in [node] + branches:
        if b.get("format") in ("double", "float") or "exclusiveMaximum" in b or "exclusiveMinimum" in b:
            return True
    return False


def _is_numeric_vector_or_point(node: dict, defs: dict, depth: int = 0) -> bool:
    """Return True when a schema node structurally represents numbers, points, vectors, or matrices."""
    if depth > 4:
        return False
    unwrapped, _, _ = _unwrap_node(node, defs)
    if _is_numeric_scalar(unwrapped, defs):
        return True

    t = _norm_type(unwrapped)
    if t == "object" and isinstance(unwrapped.get("properties"), dict):
        keys = set(unwrapped["properties"].keys())
        if keys in ({"x", "y"}, {"x", "y", "z"}) and all(
            _is_numeric_scalar(v, defs) for v in unwrapped["properties"].values()
        ):
            return True
        return False

    if t == "array" and isinstance(unwrapped.get("items"), dict):
        it_node, _, _ = _unwrap_node(unwrapped["items"], defs)
        # Integer arrays in SolidCraft schemas are ID/index paths (`OccurrencePath`, `FolderIds`, `profiles_3d`), not vectors.
        if _norm_type(it_node) == "integer":
            return False
        return _is_numeric_vector_or_point(unwrapped["items"], defs, depth + 1)

    if "anyOf" in unwrapped:
        non_null = [v for v in unwrapped["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
        if not non_null:
            return False
        # Allow axis shorthand like `^[XYZxyz]$` alongside Point3 (`AxisDir`).
        non_axis = [
            b for b in non_null
            if not (_norm_type(b) == "string" and "XYZ" in b.get("pattern", ""))
        ]
        return bool(non_axis) and all(
            _is_numeric_vector_or_point(b, defs, depth + 1) for b in non_axis
        )

    return False


# Object property names that indicate a CAD geometry/entity selection rather than a settings/camera struct.
_CAD_PICK_KEYS = {
    "edge", "edges", "face", "faces", "body", "bodies", "vertex", "on_edge", "point", "points",
    "curve", "curves", "sketch", "occurrence", "path", "axis", "plane", "snap", "at", "ref",
    "midpoint", "a", "b", "origin", "normal", "x_dir", "y_dir", "x", "y", "z", "dir", "frame",
    "corner", "end", "on", "circle", "components", "index", "fixed", "name", "id", "type", "angle",
    "height", "segments", "direction", "kind", "width", "diameter", "wall", "outer_radius",
    "corner_radius", "flange", "web", "thickness", "root_radius", "toe_radius",
    "associations", "loops", "offset_boundaries", "construct_point",
}
_NON_PICK_KEYS = {
    "fov", "pitch", "yaw", "roll", "distance", "target", "up", "azimuth_deg", "elevation_deg",
    "roughness", "metallic", "dielectric_ior", "ior", "weight", "exposure_ev", "tone_map",
    "backdrop", "background", "expected_sha256", "base_color_srgb", "roughness_linear",
    "zone", "collapsed", "column_width", "command", "params", "bold", "italic", "font",
    "letter_spacing", "line_spacing", "author", "license", "source", "generation", "serial",
    "session", "u", "v", "subject_extent_mm", "by_look", "query", "search",
}


_GEOM_SIGNAL_KEYS = {
    "body", "bodies", "face", "faces", "edge", "edges", "vertex", "on_edge", "point", "points",
    "curve", "curves", "sketch", "occurrence", "path", "axis", "plane", "snap", "at", "ref",
    "midpoint", "a", "b", "origin", "normal", "x_dir", "y_dir", "frame", "corner", "circle",
    "components", "kind", "construct_point",
}


def _extract_object_key_sets(node: dict, defs: dict, depth: int = 0) -> list[set[str]]:
    """Collect property-key sets from object schemas and `anyOf` object branches."""
    if depth > 4:
        return []
    unwrapped, _, _ = _unwrap_node(node, defs)
    key_sets: list[set[str]] = []
    if isinstance(unwrapped.get("properties"), dict) and unwrapped["properties"]:
        key_sets.append(set(unwrapped["properties"].keys()))
    for key in ("anyOf", "oneOf"):
        if key in unwrapped:
            for branch in unwrapped[key]:
                if isinstance(branch, dict) and branch.get("type") != "null":
                    key_sets.extend(_extract_object_key_sets(branch, defs, depth + 1))
    if _norm_type(unwrapped) == "array" and isinstance(unwrapped.get("items"), dict):
        key_sets.extend(_extract_object_key_sets(unwrapped["items"], defs, depth + 1))
    return key_sets


def _infer_selection_detail_from_text(text: str, pname: str) -> str:
    """Map entity descriptions/hints onto one of the six CAD selection sub-categories."""
    pl = pname.lower()
    if pl in ("profile", "profiles", "profiles_3d"):
        return "Profil"
    if pl in ("sketch", "sketches", "path_sketch", "profile_sketch"):
        return "Skizze"
    if pl in ("edge", "edges", "curve", "curve2", "curves", "bends", "rails", "line", "lines"):
        return "Kanten"
    if pl in ("face", "faces", "to_face", "seed_face", "draft_face"):
        return "Flächen"
    if pl in ("body", "bodies", "participants", "targets", "target_bodies", "tool_body", "base_body", "face_body", "tools"):
        return "Körper"
    if pl in ("feature", "features", "component", "components", "joint", "joints"):
        return "Feature"
    if pl in ("through", "base", "plane", "axis"):
        return "Geometrie"

    tl = f"{text} {pname}".lower()
    if "profile" in tl or "cam's outline" in tl or "built-in profile" in tl:
        return "Profil"
    if "sketch" in tl and any(w in tl for w in ("sketch's feature id", "which sketch", "the sketch", "a sketch", "sketches")):
        if not any(w in tl for w in ("curve", "point", "line", "edge", "operand", "plane")):
            return "Skizze"
    if any(w in tl for w in ("edge", "curve", "bend", "loop", "rail", "corner", "line", "strand", "chain")):
        if not any(w in tl for w in ("plane", "axis", "face")) or any(w in tl for w in ("an edge", "the edges", "curve", "bend", "rail", "sketch line")):
            return "Kanten"
    if any(w in tl for w in ("face", "faces")) and not any(w in tl for w in ("plane", "axis", "placement", "occurrence")):
        return "Flächen"
    if any(w in tl for w in ("body", "bodies")) and not any(w in tl for w in ("face", "edge", "point", "occurrence", "target")):
        return "Körper"
    if any(w in tl for w in ("feature", "component", "joint", "study", "contact", "exploded view", "canvas", "folder", "group")):
        if not any(w in tl for w in ("joint origin", "occurrence", "placement", "axis", "plane")):
            return "Feature"
    return "Geometrie"


def _classify_structured_selection(node: dict, defs: dict, pname: str, desc: str) -> str | None:
    """Classify structured object/array/union CAD selection schemas without hardcoded `$defs` lists."""
    unwrapped, _, udesc = _unwrap_node(node, defs)
    full_desc = f"{desc} {udesc}".strip()
    dl = full_desc.lower()

    # Integer ID/index arrays (e.g. OccurrencePath, PlacementPath, FolderIds, profiles_3d)
    if _norm_type(unwrapped) == "array" and isinstance(unwrapped.get("items"), dict):
        it_node, _, it_desc = _unwrap_node(unwrapped["items"], defs)
        if _norm_type(it_node) == "integer":
            return _infer_selection_detail_from_text(f"{full_desc} {it_desc}", pname)
        if _norm_type(it_node) == "array" and "occurrence" in dl:
            return "Geometrie"

    # Mixed id/name + integer/string arrays (e.g. FeatureList, JointList, ComponentList, IdList, ShownItems, MovedEntries)
    if _norm_type(unwrapped) == "array" and isinstance(unwrapped.get("items"), dict):
        _, it_type, _, it_desc, _ = resolve_type_info(unwrapped["items"], defs)
        if isinstance(it_type, list) and set(it_type) <= {"number", "integer", "string"}:
            return _infer_selection_detail_from_text(f"{full_desc} {it_desc}", pname)

    # Single-or-array ID/name entity reference unions (e.g. FeatureKeys, FeatureSelection, NOT plain StringList)
    if "anyOf" in unwrapped:
        non_null = [v for v in unwrapped["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
        has_array = any(_norm_type(_unwrap_node(b, defs)[0]) == "array" for b in non_null)
        _, union_type, _, _, _ = resolve_type_info(unwrapped, defs)
        has_numeric_id = any(
            x in ("integer", "number")
            for x in (union_type if isinstance(union_type, list) else [union_type])
        ) or any(
            bool(set(it_t if isinstance(it_t, list) else [it_t]) & {"integer", "number"})
            for b in non_null
            if isinstance(b.get("items"), dict)
            for it_t in [resolve_type_info(b["items"], defs)[1]]
            if it_t
        )
        if has_array and has_numeric_id:
            if any(w in dl for w in ("feature", "component", "joint", "sketch", "occurrence", "body", "bodies")):
                return _infer_selection_detail_from_text(full_desc, pname)
        # Union of string | untyped object explicitly describing a CAD pick (`JointOrigin`, `OriginAxis`, `OriginPlane`)
        if len(non_null) == 2 and {_norm_type(b) for b in non_null} == {"string", "object"}:
            if any(w in dl for w in ("joint origin", "an axis to sit on", "a plane to sit on")):
                return "Geometrie"

    key_sets = _extract_object_key_sets(unwrapped, defs)
    if not key_sets:
        return None

    all_keys = set().union(*key_sets)
    if (all_keys & _NON_PICK_KEYS) or not (all_keys & _GEOM_SIGNAL_KEYS):
        return None
    # Special compound objects that carry numeric dimensions/edits rather than pure picks
    if "vertex" in all_keys and "distance" in all_keys:
        return None  # SetbackParam
    if "angle" in all_keys and "axis" in all_keys and "position" in all_keys:
        return None  # MoveTo
    if "height" in all_keys and "width" in all_keys and "kind" not in all_keys:
        return None  # OuterSize

    # All property keys must stay within CAD pick/profile keys
    if all_keys <= _CAD_PICK_KEYS:
        return _infer_selection_detail_from_text(full_desc, pname)
    return None


def _classify_ambiguous_scalar_or_string(
    pname: str, ptype: str | list | None, node: dict, defs: dict, desc: str
) -> tuple[str, str | None]:
    """Use schema description and parameter name ONLY when the schema type is ambiguous.

    Ambiguous types are:
    - `number|string` / `integer|string`: either a numeric expression or an ID-or-name reference.
    - `string` / `string|string[]` / `array<string>`: either free text/path/new-name or an entity ID/name.
    """
    dl = desc.lower()
    pl = pname.lower()

    # Case A: number|string or integer|string (never matched by parameter name before schema!)
    if isinstance(ptype, list) and set(ptype) <= {"number", "integer", "string"}:
        non_null = [v for v in node.get("anyOf", []) if isinstance(v, dict) and v.get("type") != "null"]
        if _is_expression_union(node, non_null, desc):
            return "Zahl/Ausdruck", None
        if any(w in dl for w in ("sketch", "feature", "component", "joint", "study", "contact", "exploded view", "canvas", "occurrence", "group", "folder", "item key", "view")):
            # Exclude configuration table rows (`config.row.name` = row name or id)
            if "configuration row" in dl or "the row, by name" in dl:
                return "Text", None
            return "Auswahl in der Ansicht", _infer_selection_detail_from_text(desc, pname)
        if pl in ("sketch", "feature", "component", "joint", "study", "set", "view", "canvas"):
            return "Auswahl in der Ansicht", _infer_selection_detail_from_text(desc, pname)
        return "Text", None

    # Case B: string, string|string[], or array<string> (NEVER Zahl/Ausdruck!)
    # Check non-entity text/path/new-name/keyword roles first.
    if pl in (
        "name", "new_name", "body_name", "body_names", "dir", "data", "text", "text_expression",
        "font", "layer", "comment", "format", "unit", "units", "setup", "rule", "family",
        "size", "if_redundant", "mode", "align", "type", "command", "expression", "formula",
        "expected_sha256", "material", "appearance", "folder", "layers", "rename", "key", "keys",
    ):
        # Exception: `config.column.feature` etc. have pl == "feature"; `sketch.text.path` is a curve id.
        return "Text", None

    if pl == "path":
        if "curve id" in dl:
            return "Auswahl in der Ansicht", "Kanten"
        return "Text", None

    # Check if schema description clearly indicates selecting existing CAD entities by ID or name.
    if any(w in dl for w in ("new sketch's name", "new body's name", "new name", "file to ", "folder", "saved render setup", "saved view")):
        return "Text", None

    if pl in ("point", "datum", "origin") and any(w in dl for w in ("by id", "point id", "point reference", "joint origin")):
        return "Auswahl in der Ansicht", "Geometrie"
    if any(w in dl for w in ("sketch", "sketches")) and pl in ("sketch", "sketches"):
        return "Auswahl in der Ansicht", "Skizze"
    if any(w in dl for w in ("curve", "curves", "sketch line", "rail", "bends")) or pl in ("curve", "curve2", "curves", "line", "lines", "bends"):
        if "by id" in dl or "curve" in dl or "line" in dl:
            return "Auswahl in der Ansicht", "Kanten"
    if any(w in dl for w in ("body", "bodies")) and pl in ("body", "bodies", "participants", "targets", "target_bodies", "tool_body", "base_body", "face_body", "tools", "against", "a", "b"):
        return "Auswahl in der Ansicht", "Körper"
    if pl in ("feature", "features", "component", "components", "joint", "joints", "constraint", "dimension") and any(w in dl for w in ("feature", "component", "joint", "constraint", "dimension")):
        return "Auswahl in der Ansicht", "Feature"
    if pl in ("entities", "entity") and any(w in dl for w in ("point", "curve", "entity")):
        return "Auswahl in der Ansicht", "Kanten"
    if pl in ("a", "b") and "corner" in dl:
        return "Auswahl in der Ansicht", "Kanten"
    if pl in ("axis",) and "revolve" in dl:
        return "Auswahl in der Ansicht", "Geometrie"
    if pl == "view" and any(w in dl for w in ("rename", "delete")):
        return "Text", None

    return "Text", None


def classify_parameter(cmd_id: str, pname: str, pdef: dict, defs: dict) -> tuple[str, str | None]:
    """Classify a command parameter into a UI input field type, strictly Schema-Type first.

    Rules (documented for issue #77):
    1. Untyped `serde_json::Value` (no `type`, `$ref`, `anyOf`, `oneOf`, `enum`, `properties`, `items`)
       -> `unklar` (never guessed from parameter name).
    2. Boolean (`type == "boolean"`, after unwrapping `null` / `$ref`) -> `Schalter`.
    3. Explicit enum / `oneOf(const)` / finite-choice anchored regex `pattern` / boolean+enum union
       -> `Auswahlliste (enum)`.
    4. Numeric scalars (`number`, `integer`), numeric expressions (`LengthExpr`, `AngleExpr`, ...),
       and numeric point/vector/matrix schemas (`Point2`, `Point3`, `WorldPoint`, `AxisDir`, ...)
       -> `Zahl/Ausdruck` (applied uniformly regardless of parameter name).
    5. Structured CAD selection objects/arrays/unions (derived from schema `properties`/`anyOf`/`items`,
       e.g. `EdgeRef`, `FaceRef`, `ToolFace`, `AxisLine`, `PlaneOrFace`, `Profiles`, `OccurrencePath`)
       -> `Auswahl in der Ansicht` (`Skizze`, `Profil`, `Kanten`, `Flächen`, `Körper`, `Feature`, `Geometrie`).
    6. Complex objects (`Camera`, `LightPatch`, `PbrParameters`, `TextEdit`, `MoveTo`, `SetbackParam`)
       and nested/polymorphic arrays (`ThenSteps`, `JointLimits`, `RuledFar`, `exclude_pairs`) -> `unklar`.
    7. Ambiguous scalar/list types (`string`, `string|string[]`, `array<string>`, `number|string`,
       `integer|string`): use schema description and parameter name as hints; `string` is never
       classified as `Zahl/Ausdruck`.
    """
    node, _, desc = _unwrap_node(pdef, defs)
    _, ptype, enums, _, _ = resolve_type_info(pdef, defs)

    # Rule 1: Untyped Value -> unklar (Type before Name!)
    if not any(k in node for k in ("type", "$ref", "anyOf", "oneOf", "enum", "properties", "items")):
        return "unklar", None

    # Rule 2: Boolean -> Schalter
    if ptype == "boolean":
        return "Schalter", None

    # Rule 3: Explicit Enum / finite-choice regex / boolean+enum union -> Auswahlliste (enum)
    if enums:
        return "Auswahlliste (enum)", None
    if ptype == "string" and _is_choice_pattern(node.get("pattern")):
        return "Auswahlliste (enum)", None
    if "anyOf" in node:
        non_null = [v for v in node["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
        if non_null and all(
            _norm_type(b) == "boolean"
            or _extract_enums(b)
            or (_norm_type(b) == "string" and _is_choice_pattern(b.get("pattern")))
            for b in non_null
        ):
            return "Auswahlliste (enum)", None

    # Rule 4: Pure numeric scalars, expressions, points/vectors/matrices -> Zahl/Ausdruck
    if _is_numeric_vector_or_point(node, defs):
        return "Zahl/Ausdruck", None

    # Rule 5: Structured CAD selection objects / unions / occurrence paths -> Auswahl in der Ansicht
    sel_detail = _classify_structured_selection(node, defs, pname, desc)
    if sel_detail is not None:
        return "Auswahl in der Ansicht", sel_detail

    # Rule 6: Non-selection objects & complex arrays/unions -> unklar
    if ptype == "object":
        return "unklar", None
    if ptype == "array":
        items_node = node.get("items")
        if isinstance(items_node, dict):
            it_unwrapped, _, _ = _unwrap_node(items_node, defs)
            it_type = _norm_type(it_unwrapped)
            if it_type == "string":
                return _classify_ambiguous_scalar_or_string(pname, "string", node, defs, desc)
            if isinstance(it_type, list) and set(it_type) <= {"number", "integer", "string"}:
                return _classify_ambiguous_scalar_or_string(pname, it_type, node, defs, desc)
        return "unklar", None

    # Rule 7: Ambiguous scalar/list types (`string`, `string|string[]`, `number|string`, `integer|string`)
    if ptype == "string" or (isinstance(ptype, list) and set(ptype) <= {"number", "integer", "string"}):
        return _classify_ambiguous_scalar_or_string(pname, ptype, node, defs, desc)

    # Multi-branch unions such as `StringList` (`string | array<string>`)
    if "anyOf" in node:
        non_null = [v for v in node["anyOf"] if isinstance(v, dict) and v.get("type") != "null"]
        is_str_list = bool(non_null) and all(
            _norm_type(b) == "string"
            or (_norm_type(b) == "array" and isinstance(b.get("items"), dict) and _norm_type(b["items"]) == "string")
            for b in non_null
        )
        if is_str_list:
            return _classify_ambiguous_scalar_or_string(pname, "string", node, defs, desc)

    return "unklar", None


def analyze_catalog(session: Session, per_command_timeout: float = 30.0) -> dict:
    """Analyze all SolidCraft commands via list_commands and describe_command.

    Catches errors and timeouts per command so a single failing schema query does not abort the run.
    """
    raw_cmds = session.tool("list_commands", timeout=per_command_timeout)
    if not isinstance(raw_cmds, list):
        raw_cmds = raw_cmds.get("commands", [])

    commands_out, unklar_list, errors = [], [], []
    commands_with_schema = total_parameters = 0
    classification_counts, view_detail_counts = Counter(), Counter()
    domain_total_counts, domain_schema_counts = Counter(), Counter()

    for c in raw_cmds:
        cmd_id = c["id"]
        domain = cmd_id.split(".")[0]
        domain_total_counts[domain] += 1
        try:
            d = session.tool("describe_command", {"id": cmd_id}, timeout=per_command_timeout)
        except Exception as exc:
            err_msg = str(exc)
            errors.append({"command": cmd_id, "error": err_msg})
            commands_out.append({
                "id": cmd_id, "bereich": domain, "domain": domain,
                "label": c.get("label", cmd_id), "has_schema": False,
                "error": err_msg, "parameters": [],
            })
            continue

        inp = d.get("input") if isinstance(d, dict) else None
        has_schema = isinstance(inp, dict)
        cmd_entry = {
            "id": cmd_id, "bereich": domain, "domain": domain,
            "label": c.get("label", cmd_id), "has_schema": has_schema, "parameters": [],
        }

        if has_schema:
            commands_with_schema += 1
            domain_schema_counts[domain] += 1
            defs, required_props = inp.get("$defs", {}), set(inp.get("required", []))
            for pname, pdef in inp.get("properties", {}).items():
                total_parameters += 1
                ref_name, ptype, enums, desc, _ = resolve_type_info(pdef, defs)
                cat, detail = classify_parameter(cmd_id, pname, pdef, defs)
                classification_counts[cat] += 1
                if detail:
                    view_detail_counts[detail] += 1
                typ_str = ref_name or (ptype if isinstance(ptype, str) else ("|".join(ptype) if isinstance(ptype, list) else "any"))
                cmd_entry["parameters"].append({
                    "name": pname, "typ": typ_str, "type": typ_str,
                    "pflicht": pname in required_props, "required": pname in required_props,
                    "vorgabe": pdef.get("default"), "default": pdef.get("default"),
                    "einstufung": f"Auswahl in der Ansicht ({detail})" if detail else cat,
                    "classification": cat, "view_selection": detail,
                    "beschreibung": desc, "description": desc,
                })
                if cat == "unklar":
                    unklar_list.append({"command": cmd_id, "parameter": pname, "schema_snippet": pdef, "description": desc})

        commands_out.append(cmd_entry)

    unklar_count = classification_counts["unklar"]
    anteil_unklar = (unklar_count / total_parameters * 100.0) if total_parameters > 0 else 0.0
    summary = {
        "befehle_gesamt": len(raw_cmds),
        "befehle_mit_schema": commands_with_schema,
        "befehle_ohne_schema": len(raw_cmds) - commands_with_schema,
        "anzahl_fehler": len(errors),
        "fehler": errors,
        "parameter_gesamt": total_parameters,
        "anteil_unklar_prozent": round(anteil_unklar, 1),
        "anzahl_unklar": unklar_count,
        "klassifizierung": dict(classification_counts),
        "auswahl_ansicht_detail": dict(view_detail_counts),
        "befehle_je_bereich_gesamt": dict(sorted(domain_total_counts.items())),
        "befehle_je_bereich_mit_schema": dict(sorted(domain_schema_counts.items())),
        "unklar_faelle": unklar_list,
    }
    return {"summary": summary, "commands": commands_out}


def main():
    root_dir = Path(__file__).resolve().parent.parent
    default_out = root_dir / "build" / "befehlsmatrix.json"
    parser = argparse.ArgumentParser(description="Analyze SolidCraft command schemas and classify parameters.")
    parser.add_argument("--out", type=Path, default=default_out, help="Output JSON path (default: build/befehlsmatrix.json)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-command timeout in seconds (default: 30.0)")
    args = parser.parse_args()

    out_path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        print(f"Warnung: überschreibe bestehende Datei {out_path}", file=sys.stderr)

    print("Starte SolidCraft-Sitzung und lese Befehlskatalog...")
    with Session() as session:
        data = analyze_catalog(session, per_command_timeout=args.timeout)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    summary = data["summary"]
    print(f"\nMatrix geschrieben nach: {out_path}")
    print("\n" + "=" * 60 + "\nÜBERSICHT: BEFEHLE JE BEREICH\n" + "=" * 60)
    all_domains = sorted(set(summary["befehle_je_bereich_gesamt"]) | set(summary["befehle_je_bereich_mit_schema"]))
    print(f"{'Bereich':20} | {'Gesamt':8} | {'Mit Schema':10} | {'Anteil Schema':12}\n" + "-" * 60)
    for dom in all_domains:
        tot = summary["befehle_je_bereich_gesamt"].get(dom, 0)
        sch = summary["befehle_je_bereich_mit_schema"].get(dom, 0)
        print(f"{dom:20} | {tot:8} | {sch:10} | {(sch / tot * 100.0 if tot else 0.0):11.1f}%")

    print("\n" + "=" * 60 + "\nÜBERSICHT: PARAMETER JE EINSTUFUNG\n" + "=" * 60)
    total_p = summary["parameter_gesamt"]
    for cat, cnt in sorted(summary["klassifizierung"].items(), key=lambda x: x[1], reverse=True):
        print(f"{cat:35} | {cnt:5} | {(cnt / total_p * 100.0 if total_p else 0.0):5.1f}%")
    print("\n  Detail 'Auswahl in der Ansicht':")
    for det, cnt in sorted(summary["auswahl_ansicht_detail"].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {det:25} | {cnt:5} | {(cnt / total_p * 100.0 if total_p else 0.0):5.1f}%")

    print("\n" + "=" * 60 + "\nERGEBNIS DER PRÜFUNG:\n" + "=" * 60)
    print(f"Befehle gesamt: {summary['befehle_mit_schema']} (mit Schema; {summary['befehle_gesamt']} im Gesamtkatalog)")
    print(f"Parameter gesamt: {summary['parameter_gesamt']}")
    print(f"Anteil „unklar“: {summary['anteil_unklar_prozent']}% ({summary['anzahl_unklar']} von {summary['parameter_gesamt']})")
    print(f"Fehler bei describe_command: {summary['anzahl_fehler']}")


if __name__ == "__main__":
    main()
