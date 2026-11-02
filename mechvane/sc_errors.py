"""Translation table and explanation helper for SolidCraft error messages.

Translates internal SolidCraft and geometric kernel error messages into clear, actionable
explanations (code, message, hint) for agents and users.
"""

from __future__ import annotations

import json
import re
from typing import Any

ERROR_TABLE: list[dict[str, str]] = [
    {
        "pattern": r"shell boundaries intersect or touch;\s*cavity ownership is ambiguous",
        "code": "lumps_shell_intersect",
        "message": "Bodies or shells intersect or touch ambiguously, so cavity ownership cannot be resolved.",
        "hint": "Check for unintended collisions between parts or separate the touching bodies before boolean operations or drilling.",
    },
    {
        "pattern": r"(?:blend is larger than the neighbouring faces|a fillet larger than the faces next to it|blend would consume a neighbouring face)",
        "code": "blend_too_large",
        "message": "The blend radius is too large for the adjacent faces.",
        "hint": "Reduce the fillet radius (use the largest fitting radius indicated in the error) or check surrounding face dimensions.",
    },
    {
        "pattern": r"(?:chamfer runs past a neighbouring face|chamfer is larger than a corner radius)",
        "code": "chamfer_too_large",
        "message": "The chamfer distance is too large and extends past adjacent faces.",
        "hint": "Reduce the chamfer distance or inspect the surrounding geometry.",
    },
    {
        "pattern": r"where \d+ edges meet:\s*give a point along one edge",
        "code": "blend_meeting_edges",
        "message": "The picked point is at a corner vertex where multiple edges meet.",
        "hint": "Specify a coordinate along the target edge (such as its midpoint) rather than a vertex point.",
    },
    {
        "pattern": r"no edge at \[.*?\]:\s*the nearest edge is",
        "code": "blend_no_edge",
        "message": "No edge was found near the picked coordinate.",
        "hint": "Verify the coordinate or pick an edge point closer to the actual geometry.",
    },
    {
        "pattern": r"(?:fillet|chamfer) size must be positive",
        "code": "blend_non_positive_size",
        "message": "The fillet radius or chamfer distance must be strictly positive.",
        "hint": "Provide a positive non-zero dimension value.",
    },
    {
        "pattern": r"extrude distance is zero",
        "code": "extrude_zero_distance",
        "message": "The extrusion distance is zero.",
        "hint": "Provide a non-zero distance expression or use through_all=True.",
    },
    {
        "pattern": r"no sketch `[^`]+`",
        "code": "missing_sketch",
        "message": "The referenced sketch does not exist in the timeline.",
        "hint": "Ensure the sketch was created and finished earlier in the timeline before this feature.",
    },
    {
        "pattern": r"the profile crosses the revolve axis",
        "code": "revolve_crosses_axis",
        "message": "The sketch profile crosses the axis of revolution.",
        "hint": "Ensure the entire profile lies completely on one side of the revolve axis.",
    },
    {
        "pattern": r"(?:revolve angle is zero|revolve angle must be more than 0)",
        "code": "revolve_angle_invalid",
        "message": "The revolve angle is zero or out of range.",
        "hint": "Specify a positive angle greater than 0 up to 360 degrees.",
    },
    {
        "pattern": r"`position` \[.*?\] is not on a face of a body;\s*pick a point on the face to drill",
        "code": "hole_not_on_face",
        "message": "The hole position does not lie on any body face.",
        "hint": "Choose a position located directly on the surface of the body to drill.",
    },
    {
        "pattern": r"the counterbore must be wider than the hole and shallower than it",
        "code": "hole_counterbore_invalid",
        "message": "The counterbore diameter must exceed the hole diameter and its depth must be shallower than the total hole.",
        "hint": "Increase cb_diameter above diameter and ensure cb_depth is less than depth.",
    },
    {
        "pattern": r"the countersink must be wider than the hole",
        "code": "hole_countersink_invalid",
        "message": "The countersink diameter must be larger than the hole diameter.",
        "hint": "Increase cs_diameter above the hole diameter.",
    },
    {
        "pattern": r"shell thickness must be positive",
        "code": "shell_non_positive_thickness",
        "message": "The shell thickness must be strictly positive.",
        "hint": "Provide a positive thickness expression.",
    },
    {
        "pattern": r"(?:the planes don't enclose a solid|the shell removed everything)",
        "code": "shell_too_thick",
        "message": "The shell thickness is too large for the body, leaving no solid volume.",
        "hint": "Reduce the shell thickness so it is smaller than the body's internal dimensions.",
    },
    {
        "pattern": r"a body cannot be combined with itself",
        "code": "combine_self",
        "message": "A body cannot be combined with itself.",
        "hint": "Select distinct target and tool bodies for the combine operation.",
    },
    {
        "pattern": r"(?:unknown body `|no body `)",
        "code": "unknown_body",
        "message": "A referenced body was not found in the model.",
        "hint": "Check the body name or verify that earlier features created it.",
    },
    {
        "pattern": r"(?:expected a unit-less number, got a length|a count must be a whole number)",
        "code": "pattern_count_unit",
        "message": "A pattern count expression has physical units or is not a whole number.",
        "hint": "Provide a unit-less whole number (e.g. 4 instead of '4 mm').",
    },
    {
        "pattern": r"zero-length line",
        "code": "sketch_zero_line",
        "message": "A sketch line has identical start and end points.",
        "hint": "Ensure the start and end coordinates of the line are distinct.",
    },
    {
        "pattern": r"(?:that would over-constrain the sketch|that conflicts with the sketch)",
        "code": "sketch_overconstrained",
        "message": "The sketch constraint conflicts with existing constraints or fixed points.",
        "hint": "Remove redundant constraints or check for conflicting geometric alignments.",
    },
    {
        "pattern": r"a loft needs 2…50 sections",
        "code": "loft_section_count",
        "message": "A loft feature requires between 2 and 50 cross-section sketches.",
        "hint": "Provide at least two profile sketches in order for the loft feature.",
    },
    {
        "pattern": r"(?:the (?:cut|join|intersect) could not be computed reliably|Boolean retry)",
        "code": "boolean_unreliable",
        "message": "The boolean operation could not be computed reliably by the geometric kernel.",
        "hint": "Where bodies only touch at flush faces, add a slight overlap (e.g. 0.1 mm) or check for zero-thickness contact.",
    },
    {
        "pattern": r"the intersection is empty:\s*nothing of .*? would remain",
        "code": "intersect_empty",
        "message": "The boolean intersection is empty because the shapes do not overlap.",
        "hint": "Ensure the intersecting profile or tool body overlaps the target body volume.",
    },
    {
        "pattern": r"profile has no area",
        "code": "profile_no_area",
        "message": "The sketch profile has zero enclosed area.",
        "hint": "Ensure the sketch curves form a closed loop with non-zero area.",
    },
]


def explain(text: str | Exception, command: str | None = None) -> dict[str, str] | None:
    """Translate a SolidCraft error message into a structured explanation.

    Args:
        text: The error text, exception string, or JSON batch error output.
        command: Optional command id (e.g. 'solid.extrude') if known.

    Returns:
        dict with keys 'code', 'message', 'hint' if recognized, or None if unknown.
    """
    if isinstance(text, Exception):
        text = str(text)
    if not isinstance(text, str):
        return None

    raw = text.strip()
    if not raw:
        return None

    candidates = [raw]

    # Try extracting inner error and command from JSON batch response
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                failed = data.get("failed")
                if isinstance(failed, dict):
                    err_msg = failed.get("error")
                    if isinstance(err_msg, str) and err_msg:
                        candidates.insert(0, err_msg)
                    if not command and failed.get("command"):
                        command = failed.get("command")
        except Exception:
            pass

    for entry in ERROR_TABLE:
        pat = entry["pattern"]
        for cand in candidates:
            if re.search(pat, cand, re.IGNORECASE):
                return {
                    "code": entry["code"],
                    "message": entry["message"],
                    "hint": entry["hint"],
                }

    return None
