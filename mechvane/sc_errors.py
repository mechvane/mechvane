"""Translation table and explanation helper for SolidCraft error messages.

Translates internal SolidCraft and geometric kernel error messages into clear, actionable
explanations (code, message, hint) for agents and users.
"""

from __future__ import annotations

import functools
import json
import re
from typing import Any, Callable

ERROR_TABLE: list[dict[str, str]] = [
    {
        "pattern": r"shell boundaries intersect or touch;\s*cavity ownership is ambiguous",
        "code": "lumps_shell_intersect",
        "message": "Bodies or shells intersect or touch ambiguously, so cavity ownership cannot be resolved.",
        "hint": "Check for unintended collisions between parts or separate the touching bodies before boolean operations or drilling.",
    },
    {
        "pattern": r"(?:blend is larger than the neighbouring faces|the fillet is larger than the faces beside its edges allow|would cut through the material behind it into the hollow|a fillet larger than the faces next to it|blend would consume a neighbouring face|the rounds would leave openings in the surface|blend is larger than a corner radius|blend is taller than the walls)",
        "code": "blend_too_large",
        "message": "The fillet or chamfer is too large for the faces next to the edge.",
        "hint": "Make it smaller: SolidCraft names the largest size that fits, or check the faces around the edge.",
    },
    {
        "pattern": r"(?:chamfer runs past a neighbouring face|chamfer is larger than a corner radius|too large for this chamfer)",
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
    {
        "pattern": r"offset: only bodies with planes, cylinders, cones, spheres and tori(?:\s*\(a face at (?P<face>\[.*?\])\))?",
        "code": "offset_unsupported_surface",
        "message": "Offset and shell only support analytic surfaces (planes, cylinders, cones, spheres, tori); the face at {face} is an unsupported freeform surface.",
        "hint": "Freeform surfaces from loft, sweep, fillet or STEP import block offset and shell before SolidCraft 0.40 (#745, fixed there) and in some cases still (#10884); update SolidCraft, hollow or offset using primitive cuts, or rebuild without freeform faces.",
    },
    {
        "pattern": r"offset: not supported yet: the move is larger than a wall or step is thick \(faces would cross\)",
        "code": "offset_faces_cross",
        "message": "The offset or shell distance exceeds the wall or step thickness, causing offsetting faces to intersect.",
        "hint": "Choose a smaller offset distance or shell thickness that does not exceed the local wall thickness.",
    },
    {
        "pattern": r"offset: not supported yet: the move is larger than a rim or ledge near (?P<point>\[.*?\]) is wide \(a face would turn inside out\)",
        "code": "offset_rim_too_narrow",
        "message": "The offset distance near {point} is wider than an adjacent rim or ledge, which would invert the face.",
        "hint": "Reduce the offset distance or widen the rim or ledge geometry around {point}.",
    },
    {
        "pattern": r"offset: an edge vanishes \(the offset is too large\)",
        "code": "offset_edge_vanishes",
        "message": "An edge collapses completely because the requested offset or shell distance is too large.",
        "hint": "Reduce the offset distance or shell thickness so edges do not vanish.",
    },
    {
        "pattern": r"offset: the neutral plane is parallel to the pull direction",
        "code": "draft_pull_parallel",
        "message": "The neutral plane is parallel to the draft pull direction.",
        "hint": "Select a neutral plane or face that is perpendicular or angled relative to the pull direction.",
    },
    {
        "pattern": r"a thin extrude needs 1…1000 sketch curves \(`curves`\)",
        "code": "extrude_curves_missing",
        "message": "No sketch curves were selected or found for the thin extrude.",
        "hint": "Specify `curves` with the curve IDs to follow or ensure the sketch contains drawn curves.",
    },
    {
        "pattern": r"no curve `(?P<curve>[^`]+)` in the sketch",
        "code": "curve_not_in_sketch",
        "message": "The curve `{curve}` was not found in the referenced sketch.",
        "hint": "Verify the curve ID in the sketch timeline or re-inspect the sketch's created curves.",
    },
    {
        "pattern": r"`side: two_sides` needs `thickness2` \(the thickness outside\)",
        "code": "thin_two_sides_missing_thickness",
        "message": "Thin extrude with two-sided wall thickness is missing the second thickness parameter.",
        "hint": "Provide `thickness2` for the outer wall thickness or change `side` to inside, outside or center.",
    },
    {
        "pattern": r"(?P<sketch>[^` ]+) has no closed profiles",
        "code": "sketch_no_closed_profiles",
        "message": "The sketch `{sketch}` has no closed profiles to extrude or revolve.",
        "hint": "Close the sketch contour by connecting endpoints, or use thin extrude (thin=True) with a thickness.",
    },
    {
        "pattern": r"profile loop is not closed",
        "code": "profile_loop_not_closed",
        "message": "The profile curves do not form a closed loop.",
        "hint": "Connect the endpoints of the sketch profile or use thin extrude for open curves.",
    },
    {
        "pattern": r"the curves are not connected end to end",
        "code": "curves_not_connected",
        "message": "The sketch curves do not form a continuous chain connected end to end.",
        "hint": "Ensure the endpoints of successive curves match within tolerance without gaps or branches.",
    },
    {
        "pattern": r"revolve axis has no direction",
        "code": "revolve_axis_no_direction",
        "message": "The revolve axis has zero length or no defined direction vector.",
        "hint": "Provide a non-zero axis vector, a valid origin axis, or a straight sketch line.",
    },
    {
        "pattern": r"`axis` must be a sketch line id, x, y \(sketch axes\), X, Y, Z, a construction axis",
        "code": "revolve_axis_param_invalid",
        "message": "The revolve axis specification is invalid or unrecognized.",
        "hint": "Specify `axis` as an origin axis ('X', 'Y', 'Z'), sketch line id, construction axis, or {origin, dir}.",
    },
    {
        "pattern": r"every loft section must have the same number of holes",
        "code": "loft_holes_count_mismatch",
        "message": "Loft cross sections have differing numbers of internal holes or loops.",
        "hint": "Ensure every section sketch has the exact same number of inner hole profiles.",
    },
    {
        "pattern": r"loft sections (?P<sec1>\d+) and (?P<sec2>\d+) lie in the same plane \(no volume between them\)",
        "code": "loft_same_plane",
        "message": "Loft sections {sec1} and {sec2} lie in the same geometric plane, leaving no volume between them.",
        "hint": "Place successive loft sections on separate parallel or angled work planes spaced along the loft direction.",
    },
    {
        "pattern": r"a path segment has no direction",
        "code": "sweep_path_no_direction",
        "message": "A segment of the sweep path has zero length or undefined tangent direction.",
        "hint": "Check the sweep path curve definitions for zero-length segments or degenerate arcs.",
    },
    {
        "pattern": r"box needs a positive size in x, y and z",
        "code": "primitive_box_dimensions",
        "message": "The box primitive dimensions must all be strictly positive.",
        "hint": "Ensure length, width, and height are all positive numbers or evaluate to positive lengths.",
    },
    {
        "pattern": r"radius must be positive",
        "code": "primitive_radius_non_positive",
        "message": "The cylinder or cone radius must be strictly positive.",
        "hint": "Provide a positive non-zero value for radius or diameter.",
    },
    {
        "pattern": r"torus needs major > minor > 0",
        "code": "primitive_torus_radii",
        "message": "The torus major radius must be strictly greater than the minor radius, and both must be positive.",
        "hint": "Ensure major > minor > 0 for the torus dimensions.",
    },
    {
        "pattern": r"unknown hole type `(?P<type>[^`]+)`",
        "code": "hole_type_unknown",
        "message": "The hole type `{type}` is unknown or unsupported.",
        "hint": "Use a valid hole type: simple, drilled, counterbore, or countersink.",
    },
    {
        "pattern": r"the reference edges are parallel",
        "code": "hole_reference_edges_parallel",
        "message": "The hole reference edges are parallel and cannot establish a 2D coordinate fix on the face.",
        "hint": "Pick two non-parallel intersecting or crossing straight edges on the face.",
    },
    {
        "pattern": r"the reference distances put the hole's centre off its face",
        "code": "hole_reference_off_face",
        "message": "The reference edge distances position the hole center outside the boundary of the selected face.",
        "hint": "Adjust the reference edge distances so the drilled hole falls within the face perimeter.",
    },
    {
        "pattern": r"that chamfer angle runs past the other face",
        "code": "chamfer_angle_past_face",
        "message": "The chamfer angle creates a cut extending past the adjacent face.",
        "hint": "Reduce the chamfer angle or distance, or use an equal-distance 45-degree chamfer.",
    },
    {
        "pattern": r"`features` must list features to copy",
        "code": "pattern_features_missing",
        "message": "No seed features were specified to replicate in the pattern.",
        "hint": "Provide a list of feature names or IDs in `features`, or use `bodies` for a body pattern.",
    },
    {
        "pattern": r"no feature `(?P<feature>[^`]+)`",
        "code": "pattern_feature_not_found",
        "message": "The feature `{feature}` referenced as a pattern seed does not exist in the timeline.",
        "hint": "Check the feature name or verify that it occurs earlier in the design history.",
    },
    {
        "pattern": r"`(?P<plane>[^`]+)` is reserved for an origin plane \(XY, XZ, YZ, Top, Front, Right\); give the construction plane another name",
        "code": "plane_name_reserved",
        "message": "The plane name `{plane}` is reserved for a default origin plane.",
        "hint": "Choose a distinct custom name for the construction plane, such as 'OffsetPlane1'.",
    },
    {
        "pattern": r"there is already a parameter `(?P<param>[^`]+)`",
        "code": "param_already_exists",
        "message": "A parameter named `{param}` already exists in the document.",
        "hint": "Use a different parameter name, reference the existing parameter, or edit it via parameters.change.",
    },
    {
        "pattern": r"circular reference:\s*(?P<path>.+)",
        "code": "param_circular_reference",
        "message": "Parameter expression contains a circular reference: {path}.",
        "hint": "Remove the cyclical parameter dependency so each parameter evaluates to a defined value.",
    },
    {
        "pattern": r"division by zero",
        "code": "expr_division_by_zero",
        "message": "The parameter expression attempted a division by zero.",
        "hint": "Ensure the divisor expression evaluates to a non-zero value.",
    },
    {
        "pattern": r"cannot (?:add|subtract) (?:a |an )?(?P<dim1>[a-z_]+) and (?:a |an )?(?P<dim2>[a-z_]+)",
        "code": "expr_incompatible_units",
        "message": "Cannot add or subtract values with incompatible physical dimensions ({dim1} and {dim2}).",
        "hint": "Ensure both operands have compatible units (e.g. both lengths or both angles).",
    },
    {
        "pattern": r"sketch is too large \(at most \d+ points or curves\)",
        "code": "sketch_too_large",
        "message": "The sketch exceeds the entity limit (maximum 20,000 points or curves).",
        "hint": "Simplify complex drawings (e.g. imported DXF/SVG contours) or split the geometry across multiple sketches.",
    },
    {
        "pattern": r"unknown sketch entity `(?P<entity>[^`]+)`",
        "code": "sketch_unknown_entity",
        "message": "The sketch entity `{entity}` was not found in the active sketch.",
        "hint": "Verify the point or curve identifier against the current sketch definition.",
    },
    {
        "pattern": r"shell is not closed",
        "code": "step_shell_not_closed",
        "message": "The imported STEP solid shell is open and does not enclose a sealed watertight volume.",
        "hint": "Check the source CAD model for missing faces or unstitched surface boundaries before exporting STEP.",
    },
    {
        "pattern": r"shell is not manifold",
        "code": "step_shell_not_manifold",
        "message": "The imported STEP geometry has non-manifold edges or vertices where more than two faces meet.",
        "hint": "Repair self-intersections and non-manifold boundaries in the CAD authoring software.",
    },
    {
        "pattern": r"STEP import: no bodies \((?P<reason>[^)]+)\)",
        "code": "step_no_bodies",
        "message": "The STEP file contained no valid solid bodies ({reason}).",
        "hint": "Ensure the STEP file contains solid 3D B-Rep entities (AP203/AP214/AP242 models) rather than wireframes or empty assemblies.",
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
            m = re.search(pat, cand, re.IGNORECASE)
            if m:
                msg = entry["message"]
                hint = entry["hint"]
                gd = m.groupdict()
                if gd:
                    subs = {k: (v if v is not None else "") for k, v in gd.items()}
                    if entry["code"] == "offset_unsupported_surface" and not subs.get("face"):
                        msg = "Offset and shell only support analytic surfaces (planes, cylinders, cones, spheres, tori); the body has an unsupported freeform surface."
                    try:
                        msg = msg.format(**subs)
                    except (KeyError, IndexError, ValueError):
                        pass
                    try:
                        hint = hint.format(**subs)
                    except (KeyError, IndexError, ValueError):
                        pass
                return {
                    "code": entry["code"],
                    "message": msg,
                    "hint": hint,
                }

    return None


class ExplainedError(RuntimeError):
    """A SolidCraft error with what Mechvane can add to it: `explanation` ({code, message, hint} or None)
    and `location` (see sc_locate.locate, or None). The text reads: explanation, "Where: …", SolidCraft's
    reply."""

    def __init__(self, text: str, explanation: dict | None = None, location: dict | None = None):
        super().__init__(text)
        self.explanation = explanation
        self.location = location


def reraise(e: Exception, location: dict | None = None):
    """Re-raise e with explanation and hint when explain() recognises it and with the place when one was
    found (ExplainedError, a RuntimeError), else unchanged."""
    exp = explain(e)
    if exp is None and not location:
        raise e
    lines = []
    if exp is not None:
        lines.append(f"{exp['message']} ({exp['hint']})")
    if location:
        lines.append(f"Where: {location['text']}")
    # RuntimeError, not type(e): not every exception class takes a single message argument.
    raise ExplainedError("\n".join(lines + [str(e)]), exp, location) from e


def explained(fn: Callable) -> Callable:
    """Decorator for tools: SolidCraft errors raised by fn come back with explanation and hint."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            reraise(exc)

    return wrapper
