"""Where a failed command went wrong: the edge or face it was aimed at, the features these belong to and
what stands in the way, in one sentence ("Chamfer C1 (5.5 mm) on the edge of Plate between +z and -y at
[30, 0, 10] has Hole1 (bore) 5 mm away at [8, 5, 10]. Largest size that fits: 4.913 mm.").

SolidCraft says what failed, sc_errors says what that means; this module adds where. It reads the model as
it is (faces and edges of every body, two calls per body), so call it with the document in the state the
failed command saw. Faces are named after the feature that made them ("F2:bore:side:1" belongs to
timeline feature 2), which gives the feature names without any topology call.
"""

from __future__ import annotations

import math
import re

from . import geometry as g

_TOL = 1e-6
_FACE_ID = re.compile(r"^F(\d+)(?::(.*))?$")
_POINT_IN_TEXT = re.compile(
    r"\[\s*(-?\d+(?:\.\d+)?)(?:\s*mm)?\s*,\s*(-?\d+(?:\.\d+)?)(?:\s*mm)?\s*,\s*(-?\d+(?:\.\d+)?)(?:\s*mm)?\s*\]")
_FITS = re.compile(r"(?:largest (?:size|radius) that fits is|maximum radius along this edge is)\s*(-?\d+(?:\.\d+)?)\s*mm")
_BLENDS = {"solid.fillet": ("Fillet", "radius"), "solid.chamfer": ("Chamfer", "distance")}


# ---------------------------------------------------------------------------------------------- numbers

def _num(x: float) -> str:
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _pt(p) -> str:
    return "[" + ", ".join(_num(c) for c in p) + "]"


def _r(p):
    return [round(float(c), 3) + 0.0 for c in p]


# ------------------------------------------------------------------------------------------- polylines

def _seg_point(p, a, b):
    """Closest point to p on segment ab, with its parameter 0…1."""
    ab = g.sub(b, a)
    l2 = g.dot(ab, ab)
    t = 0.0 if l2 < 1e-18 else max(0.0, min(1.0, g.dot(g.sub(p, a), ab) / l2))
    return g.add(a, g.scale(ab, t)), t


def _circle(p1, p2, p3):
    """Centre and radius of the circle through three points, or (None, None) when they are in line."""
    a, b = g.sub(p2, p1), g.sub(p3, p1)
    n = g.cross(a, b)
    n2 = g.dot(n, n)
    if n2 < 1e-18:
        return None, None
    to = g.scale(g.add(g.scale(g.cross(n, a), g.dot(b, b)), g.scale(g.cross(b, n), g.dot(a, a))), 1.0 / (2.0 * n2))
    return g.add(p1, to), g.norm(to)


def edge_points(e: dict, n: int = 48, normal=None) -> tuple[list, float | None]:
    """An edge as a polyline, and its radius when it is a circular arc. SolidCraft gives start, mid, end and
    length: a straight edge is exact, an arc is rebuilt through the three points, anything else (ellipse,
    spline) stays a coarse start-mid-end line. A circle that closes in itself (the rim of a hole since SolidCraft
    0.40, before it came in two halves) has mid opposite start: its plane comes from `normal`, the axis of the
    cylinder or the normal of the plane that bounds it."""
    s, m, t = e["start"], e["mid"], e["end"]
    chord = g.norm(g.sub(t, s))
    if abs(e["length"] - chord) < 1e-6 * max(1.0, chord):
        return [s, t], None
    if chord < _TOL:  # closed in itself: a full circle with mid opposite start
        if normal is not None:
            c = g.scale(g.add(s, m), 0.5)
            r = g.norm(g.sub(m, s)) / 2.0
            if r > _TOL and abs(2.0 * math.pi * r - e["length"]) <= 0.02 * e["length"]:
                e1 = g.unit(g.sub(s, c))
                e2 = g.unit(g.cross(normal, e1))
                pts = [g.add(c, g.add(g.scale(e1, r * math.cos(2.0 * math.pi * i / n)),
                                      g.scale(e2, r * math.sin(2.0 * math.pi * i / n)))) for i in range(n + 1)]
                pts[0], pts[-1] = s, t
                return pts, r
        return [s, m, t], None
    c, r = _circle(s, m, t)
    if c is None:
        return [s, m, t], None
    u = g.sub(s, c)
    half = math.acos(max(-1.0, min(1.0, g.dot(u, g.sub(m, c)) / (r * r))))  # mid is halfway along the arc
    if abs(2.0 * half * r - e["length"]) > 0.02 * e["length"]:
        return [s, m, t], None
    e1 = g.unit(u)
    e2 = g.unit(g.cross(g.cross(u, g.sub(m, c)), u))
    pts = [g.add(c, g.add(g.scale(e1, r * math.cos(2.0 * half * i / n)), g.scale(e2, r * math.sin(2.0 * half * i / n))))
           for i in range(n + 1)]
    pts[0], pts[-1] = s, t
    return pts, r


def _point_polyline(p, pts):
    best = (math.inf, None)
    for a, b in zip(pts, pts[1:]):
        q, _ = _seg_point(p, a, b)
        d = g.norm(g.sub(p, q))
        if d < best[0]:
            best = (d, q)
    return best


# ----------------------------------------------------------------------------------------------- model

def edge_faces(edge_name: str, face_names) -> tuple[str, str] | None:
    """The two faces of an edge named "<face A>|<face B>" (a seam may end in "~1"). Face names can contain
    "|" themselves (a blend between two faces), so every split is tried against the known faces."""
    name = re.sub(r"~\d+$", "", edge_name)
    pos = name.find("|")
    while pos >= 0:
        a, b = name[:pos], name[pos + 1:]
        if a in face_names and b in face_names:
            return a, b
        pos = name.find("|", pos + 1)
    return None


class Model:
    """Faces and edges of all bodies with the names of their features."""

    def __init__(self, session):
        insp = session.cmd("document.inspect", {"measure": False})
        self.features = {f["id"]: f["name"] for f in insp.get("timeline", []) if isinstance(f, dict) and "id" in f}
        self.faces: list[dict] = []
        self.edges: list[dict] = []
        self.by_name: dict = {}
        for body in insp.get("bodies", []):
            try:
                faces = session.cmd("model.faces", {"body": body["name"]}).get("faces", [])
                edges = session.cmd("model.edges", {"body": body["name"]}).get("edges", [])
            except Exception:
                continue
            names = {f["name"] for f in faces}
            by_name = {}
            for f in faces:
                f = dict(f, body=body["name"], edges=[])
                by_name[f["name"]] = f
                self.by_name[(body["name"], f["name"])] = f
                self.faces.append(f)
            for e in edges:
                ef = edge_faces(e["name"], names) or ()
                normal = None  # plane of a circle that closes in itself: from a cylinder or a plane next to it
                for fn in ef:
                    fc = by_name[fn]
                    normal = (fc.get("cylinder") or {}).get("axis") or fc.get("plane_normal") or normal
                pts, radius = edge_points(e, normal=normal)
                e = dict(e, body=body["name"], pts=pts, radius=radius, faces=ef)
                for fn in e["faces"]:
                    by_name[fn]["edges"].append(e)
                self.edges.append(e)

    # names ---------------------------------------------------------------------------------------------

    @staticmethod
    def feature_id(face_name: str) -> int | None:
        m = _FACE_ID.match(face_name)
        return int(m.group(1)) if m else None

    def feature_of(self, face_name: str) -> str | None:
        return self.features.get(self.feature_id(face_name))

    @staticmethod
    def side(face_name: str) -> str:
        """The part of a face name that tells the face from its feature's other faces: "+z", "bore", "blend"."""
        m = _FACE_ID.match(face_name)
        tag = (m.group(2) or "") if m else face_name
        tag = re.split(r":F\d+", tag)[0]  # a blend names the faces it joins after its own tag
        return re.sub(r"(?::side)?[:#]\d+$", "", tag) or "face"

    def face_label(self, face_name: str) -> str:
        feat = self.feature_of(face_name)
        return f"{feat} ({self.side(face_name)})" if feat else face_name

    def edge_label(self, e: dict) -> str:
        if len(e["faces"]) != 2:
            return f"edge {e['name']}"
        a, b = e["faces"]
        fa, fb = self.feature_of(a), self.feature_of(b)
        if fa and fa == fb:
            sa, sb = self.side(a), self.side(b)
            return f"the edge of {fa} between {sa} and {sb}" if sa != sb else f"the edge of {fa} on its {sa} face"
        return f"the edge between {self.face_label(a)} and {self.face_label(b)}"

    def edge_features(self, e: dict) -> list[str]:
        return _unique(self.feature_of(f) for f in e["faces"])

    # nearest -------------------------------------------------------------------------------------------

    def nearest_edge(self, p):
        best = (math.inf, None, None)
        for e in self.edges:
            d, q = _point_polyline(p, e["pts"])
            if d < best[0]:
                best = (d, e, q)
        return best

    def edges_at(self, p, tol=1e-4):
        return [e for e in self.edges if min(g.norm(g.sub(p, e["start"])), g.norm(g.sub(p, e["end"]))) < tol]

    def _face_distance(self, f, p):
        """(distance, nearest point on the face, exact?) of a point to a bounded face."""
        boundary = min((_point_polyline(p, e["pts"]) for e in f["edges"]), default=(math.inf, None))
        n = f.get("plane_normal")
        if n and f.get("point"):
            h = g.dot(g.sub(p, f["point"]), n)
            q = g.sub(p, g.scale(n, h))
            if _inside_planar(f, q):
                return abs(h), q, True
            return boundary[0], boundary[1], True
        cyl = f.get("cylinder")
        if cyl and f["edges"]:
            a = g.unit(cyl["axis"])
            ts = [g.dot(g.sub(x, cyl["origin"]), a) for e in f["edges"] for x in e["pts"]]
            t = g.dot(g.sub(p, cyl["origin"]), a)
            radial = g.sub(g.sub(p, cyl["origin"]), g.scale(a, t))
            if g.norm(radial) > _TOL:
                foot = g.add(cyl["origin"], g.scale(a, max(min(ts), min(max(ts), t))))
                q = g.add(foot, g.scale(g.unit(radial), cyl["radius"]))
                # a cylinder comes as two half faces: the half whose own point is on the same side
                if g.dot(g.sub(f.get("point") or q, foot), radial) >= 0:
                    return g.norm(g.sub(p, q)), q, True
            return boundary[0], boundary[1], True
        ref = f.get("point") or f.get("centroid")
        if boundary[1] is not None and (ref is None or boundary[0] <= g.norm(g.sub(p, ref))):
            return boundary[0], boundary[1], False
        return (g.norm(g.sub(p, ref)), ref, False) if ref else (math.inf, None, False)

    def nearest_face(self, p):
        best = (math.inf, None, None, False)
        for f in self.faces:
            d, q, exact = self._face_distance(f, p)
            if d < best[0] - 1e-9:
                best = (d, f, q, exact)
        return best

    def face_by_name(self, name: str):
        return next((f for f in self.faces if f["name"] == name), None)


def _inside_planar(f: dict, q) -> bool:
    """Whether a point in the plane of a planar face lies inside its boundary (even-odd rule over all
    boundary edges, so holes count as outside)."""
    n = f["plane_normal"]
    ref = [1.0, 0.0, 0.0] if abs(n[0]) < 0.9 else [0.0, 1.0, 0.0]
    u = g.unit(g.cross(n, ref))
    v = g.cross(n, u)
    # a direction no model edge is likely to follow, so the ray does not run along a boundary
    x0, y0 = g.dot(q, u), g.dot(q, v)
    dx, dy = math.cos(0.7391), math.sin(0.7391)
    crossings = 0
    for e in f["edges"]:
        for a, b in zip(e["pts"], e["pts"][1:]):
            ax, ay, bx, by = g.dot(a, u) - x0, g.dot(a, v) - y0, g.dot(b, u) - x0, g.dot(b, v) - y0
            sa, sb = ax * dy - ay * dx, bx * dy - by * dx  # side of each end relative to the ray's line
            if (sa > 0) == (sb > 0):
                continue
            w = sa / (sa - sb)
            if (ax + w * (bx - ax)) * dx + (ay + w * (by - ay)) * dy > 0:
                crossings += 1
    return crossings % 2 == 1


def _unique(items) -> list:
    out = []
    for x in items:
        if x is not None and x not in out:
            out.append(x)
    return out


# ------------------------------------------------------------------------------------------------ picks

def _as_point(session, v):
    if isinstance(v, (list, tuple)) and len(v) == 3 and not any(isinstance(c, (list, tuple, dict)) for c in v):
        try:
            return [c if isinstance(c, (int, float)) else g.eval_length(session, c, default=math.nan) for c in v]
        except Exception:
            return None
    return None


def _points(session, value) -> list:
    """The pick points in a parameter: one point or a list of points; names and other values are skipped."""
    p = _as_point(session, value)
    if p is not None:
        return [] if any(math.isnan(c) for c in p) else [p]
    if isinstance(value, (list, tuple)):
        return [q for item in value for q in _points(session, item)]
    return []


def _shares_vertex(a: dict, b: dict) -> bool:
    return any(g.norm(g.sub(x, y)) < 1e-6 for x in (a["start"], a["end"]) for y in (b["start"], b["end"]))


def _project(p, pts):
    """Closest point of a polyline to p: (point, segment index, whether it is an end of the polyline)."""
    best = (math.inf, None, 0, False)
    last = len(pts) - 2
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        q, s = _seg_point(p, a, b)
        d = g.norm(g.sub(p, q))
        if d < best[0]:
            best = (d, q, i, (i == 0 and s <= 1e-9) or (i == last and s >= 1.0 - 1e-9))
    return best[1], best[2], best[3]


def _into_face(f: dict, q, t):
    """The direction in face f that leaves an edge through q (tangent t) at a right angle, into the face."""
    n = f.get("plane_normal")
    if n:
        d = g.cross(n, t)
        if g.norm(d) < 0.5:
            return None
        d = g.unit(d)
        for sign in (1.0, -1.0):
            if _inside_planar(f, g.add(q, g.scale(d, sign * 1e-3))):
                return g.scale(d, sign)
        return None
    cyl = f.get("cylinder")
    if cyl:
        a = g.unit(cyl["axis"])
        d = g.sub(a, g.scale(t, g.dot(a, t)))
        if g.norm(d) < 0.5:  # the edge runs along the cylinder: its side direction is not one line
            return None
        d = g.unit(d)
        ts = [g.dot(g.sub(x, q), a) for e in f["edges"] for x in e["pts"]]
        if not ts:
            return None
        return d if sum(ts) / len(ts) > 0 else g.scale(d, -1.0)
    return None


def _critical_size(kind: str, alpha: float, beta: float, c: float) -> float:
    """The blend size from which a point is cut away. The point sits in the cross-section of the edge at
    alpha along one face and beta along the other (c = cosine of the angle between the faces there). A
    chamfer takes the triangle alpha + beta < size. A fillet of radius r touches the faces r·cot(h) from
    the edge (h = half the angle) and takes what lies between the edge and its arc."""
    if kind == "chamfer":
        return alpha + beta
    h = math.acos(max(-1.0, min(1.0, c))) / 2.0
    sin_h, cot_h = math.sin(h), math.cos(h) / math.sin(h)
    reach = max(alpha, beta) / cot_h  # from this radius on, the point lies between the tangent points
    w2 = alpha * alpha + beta * beta + 2.0 * alpha * beta * c
    along = (alpha + beta) * (1.0 + c) / (2.0 * math.cos(h))  # the point along the bisector
    disc = (along / sin_h) ** 2 - cot_h * cot_h * w2
    if disc <= 1e-12 * max(1.0, w2):  # on a face (or never inside the arc): reached at the tangent point
        return reach
    s1 = (along / sin_h - math.sqrt(disc)) / (cot_h * cot_h)
    s2 = (along / sin_h + math.sqrt(disc)) / (cot_h * cot_h)
    # inside the arc (kept) for radii between s1 and s2
    return reach if (reach <= s1 + 1e-9 or reach >= s2) else s2


def blend_neighbours(model: Model, e: dict, kind: str = "fillet") -> list[dict]:
    """What a fillet or chamfer on an edge can run into, tightest first: the other edges of the two faces
    beside it and of the faces at its ends, each with the blend size from which it is reached (`size`),
    its distance from the edge and the point. An edge of another feature (a hole, a pocket, a rib) is
    `foreign`: it was made after the edge's own faces, so it is something set into them, not just where
    an older face ends. Edges that only lie beyond an end of the edge are no neighbours."""
    if len(e["faces"]) != 2:
        return []
    beside = list(e["faces"])
    ends = {f for o in model.edges if o is not e and o["body"] == e["body"] and _shares_vertex(o, e)
            for f in o["faces"]} - set(beside)
    own = set(model.edge_features(e))
    newest = max((model.feature_id(f) or 0 for f in beside), default=0)
    fa, fb = (model.by_name[(e["body"], f)] for f in beside)
    frames: dict = {}

    def frame(i):
        if i not in frames:
            a, b = e["pts"][i], e["pts"][i + 1]
            t, q = g.unit(g.sub(b, a)), g.scale(g.add(a, b), 0.5)
            da, db = _into_face(fa, q, t), _into_face(fb, q, t)
            frames[i] = (t, da, db) if da and db and abs(g.dot(da, db)) < 0.999 else (t, None, None)
        return frames[i]

    out = []
    for o in model.edges:
        if o is e or o["body"] != e["body"] or _shares_vertex(o, e):
            continue
        on = [f for f in o["faces"] if f in beside] + [f for f in o["faces"] if f in ends]
        if not on:
            continue
        pts = o["pts"]
        if len(pts) == 2:
            pts = [g.add(pts[0], g.scale(g.sub(pts[1], pts[0]), k / 16.0)) for k in range(17)]
        best = None
        for x in pts:
            q, i, at_end = _project(x, e["pts"])
            w = g.sub(x, q)
            dist = g.norm(w)
            t, da, db = frame(i)
            if at_end and abs(g.dot(w, t)) > 0.02 * dist + 1e-6:
                continue  # beyond the end of the edge, not beside it
            if da is None:
                size, exact = dist, False
            else:
                c = g.dot(da, db)
                wa, wb = g.dot(w, da), g.dot(w, db)
                alpha, beta = (wa - c * wb) / (1.0 - c * c), (wb - c * wa) / (1.0 - c * c)
                if alpha < -1e-6 or beta < -1e-6:
                    continue  # outside the corner the blend fills
                size, exact = _critical_size(kind, max(alpha, 0.0), max(beta, 0.0), c), True
            if best is None or size < best[0]:
                best = (size, dist, x, q, exact)
        if best is None:
            continue
        other = [f for f in o["faces"] if f not in beside and f not in ends] or [f for f in o["faces"] if f not in beside]
        face = next((f for f in other if model.feature_of(f) not in own), other[0] if other else on[0])
        out.append({"edge": o, "size": best[0], "distance": best[1], "at": best[2], "on_edge": best[3],
                    "exact": best[4], "face": face, "across": on[0],
                    "foreign": model.feature_of(face) not in own and (model.feature_id(face) or 0) > newest})
    # at the same size the face beside the edge tells more than one at its end
    out.sort(key=lambda c: (round(c["size"], 6), c["across"] not in beside))
    return out


def end_rounds(model: Model, e: dict) -> list[dict]:
    """Rounds (cylindrical faces) that an edge runs into at its ends, smallest first."""
    faces = {f for o in model.edges if o is not e and o["body"] == e["body"] and _shares_vertex(o, e)
             for f in o["faces"]} - set(e["faces"])
    rounds = [model.by_name[(e["body"], f)] for f in faces]
    return sorted((f for f in rounds if f.get("cylinder")), key=lambda f: f["cylinder"]["radius"])


# ----------------------------------------------------------------------------------------------- locate

def _picked_edge(model: Model, p) -> tuple[dict, dict] | None:
    d, e, q = model.nearest_edge(p)
    if e is None:
        return None
    info = {"kind": "edge", "pick": _r(p), "name": e["name"], "label": model.edge_label(e),
            "features": model.edge_features(e), "distance": round(d, 3)}
    if e["radius"] is not None:
        info["radius"] = round(e["radius"], 3)
    return info, e


def _picked_face(model: Model, p) -> tuple[dict, dict] | None:
    d, f, q, exact = model.nearest_face(p)
    if f is None:
        return None
    info = {"kind": "face", "pick": _r(p), "name": f["name"], "label": model.face_label(f["name"]),
            "features": _unique([model.feature_of(f["name"])]), "distance": round(d, 3)}
    if q is not None:
        info["nearest_point"] = _r(q)
    if not exact:
        info["approximate"] = True
    return info, f


def _locate_blend(model: Model, session, command: str, params: dict, error: str, out: dict) -> str | None:
    word, size_key = _BLENDS[command]
    points = _points(session, params.get("edges"))
    if not points:
        return None
    name = params.get("name")
    subject = f"{word} {name}" if name else word
    size = params.get(size_key)
    requested = g.eval_length(session, size, default=math.nan) if size is not None else math.nan
    if not math.isnan(requested):
        out["requested"] = round(requested, 3)
        subject += f" ({_num(requested)} mm)"
    fits = _FITS.search(error)
    if fits:
        out["fits"] = float(fits.group(1))

    m = re.search(r"no edge at", error)
    if m:
        p = points[0]
        for q in _points(session, [[float(x) for x in t] for t in _POINT_IN_TEXT.findall(error)]):
            p = min(points, key=lambda c: g.norm(g.sub(c, q)))
        info, e = _picked_edge(model, p)
        out.update(at=_r(p), nearest=dict(info, mid=_r(e["mid"])), features=info["features"])
        return (f"{subject}: nothing at {_pt(p)}. The nearest edge is {info['label']}, {_num(info['distance'])} mm away; "
                f"pick it at its midpoint {_pt(e['mid'])}.")

    meet = re.search(r"where (\d+) edges meet", error)
    if meet:
        # a corner, or a point just as near to several edges (the middle of a narrow face)
        p = points[0]
        for q in [[float(x) for x in m3] for m3 in _POINT_IN_TEXT.findall(error)]:
            p = min(points, key=lambda c: g.norm(g.sub(c, q)))
        ranked = sorted(((_point_polyline(p, e["pts"])[0], i, e) for i, e in enumerate(model.edges)), key=lambda c: c[:2])
        meeting = [e for _, _, e in ranked[:int(meet.group(1))]]
        if not meeting:
            return None
        out.update(at=_r(p), edges=[{"name": e["name"], "label": model.edge_label(e), "mid": _r(e["mid"])} for e in meeting],
                   features=_unique(f for e in meeting for f in model.edge_features(e)))
        listed = "; ".join(f"{model.edge_label(e)} at {_pt(e['mid'])}" for e in meeting)
        what = "is a corner" if ranked[0][0] < 1e-3 else f"is as near to one edge as to the other ({_num(ranked[0][0])} mm)"
        return f"{subject}: {_pt(p)} {what}. Pick the edge you mean at its midpoint: {listed}."

    # a size that does not fit: of all picked edges, tell about the one that is tightest
    kind = word.lower()
    corner = "corner radius" in error
    worst = None
    picked = []
    for p in points:
        found = _picked_edge(model, p)
        if found is None:
            continue
        info, e = found
        picked.append(info)
        near = blend_neighbours(model, e, kind)
        cands = [("neighbour", c["size"], c) for c in near]
        if e["radius"] is not None:
            cands.append(("arc", e["radius"], None))
        if corner:
            cands += [("round", f["cylinder"]["radius"], f) for f in end_rounds(model, e)]
        # at the same size: what SolidCraft's message speaks of first
        cands.sort(key=lambda c: (round(c[1], 6), (c[0] == "neighbour") if corner else (c[0] != "neighbour")))
        if not math.isnan(requested):
            cands = [c for c in cands if c[1] <= requested * 1.05]
        tight = cands[0][1] if cands else math.inf
        if worst is None or tight < worst[0]:
            worst = (tight, info, cands)
    if worst is None:
        return None
    _, info, cands = worst
    out.update(at=info["pick"], picked=picked, features=list(info["features"]))
    text = f"{subject} on {info['label']} at {_pt(info['pick'])}"
    estimate = None
    if not cands:
        text += "."
    elif cands[0][0] == "arc":
        estimate = cands[0][1]
        text += f": that edge is an arc of radius {_num(estimate)} mm, the size has to stay below it."
    elif cands[0][0] == "round":
        f = cands[0][2]
        estimate = cands[0][1]
        out["obstacle"] = {"feature": model.feature_of(f["name"]), "face": f["name"], "label": model.face_label(f["name"]),
                           "radius": round(estimate, 3), "foreign": True}
        out["features"] = _unique(out["features"] + [out["obstacle"]["feature"]])
        text += (f" ends at {model.face_label(f['name'])}, a round of radius {_num(estimate)} mm: "
                 f"the size has to stay below that radius.")
    else:
        first = cands[0][2]
        estimate = first["size"] if first["exact"] else None
        out["obstacle"] = _obstacle(model, first)
        if first["foreign"]:
            text += f" has {model.face_label(first['face'])} {_num(first['distance'])} mm away at {_pt(first['at'])}."
        else:
            text += (f": {model.face_label(first['across'])} is only {_num(first['distance'])} mm wide there "
                     f"(next edge at {_pt(first['at'])}).")
        also = next((c[2] for c in cands[1:] if c[0] == "neighbour" and c[2]["foreign"]
                     and model.feature_of(c[2]["face"]) != model.feature_of(first["face"])), None)
        if also is not None:
            out["also_near"] = _obstacle(model, also)
            text += f" {model.face_label(also['face'])} is {_num(also['distance'])} mm away at {_pt(also['at'])}."
        out["features"] = _unique(out["features"] + [o["feature"] for o in (out.get("obstacle"), out.get("also_near")) if o])
    obstacle = out.get("obstacle")
    if "fits" in out:
        text += f" Largest size that fits: {_num(out['fits'])} mm."
    elif estimate is not None:
        out["fits_estimate"] = round(estimate, 3)
        if cands[0][0] == "neighbour":
            text += f" About {_num(estimate)} mm would still fit (estimate)."
    if obstacle and obstacle.get("foreign") and "distance" in obstacle and ("fits" in out or estimate is not None):
        text += f" Stay below it, or move {obstacle['feature']}."
    return text


def _obstacle(model: Model, c: dict) -> dict:
    out = {"feature": model.feature_of(c["face"]), "face": c["face"], "label": model.face_label(c["face"]),
           "distance": round(c["distance"], 3), "at": _r(c["at"]), "foreign": c["foreign"]}
    if c["exact"]:
        out["reached_from"] = round(c["size"], 3)
    return out


def _locate_hole(model: Model, session, params: dict, error: str, out: dict) -> str | None:
    points = _points(session, params.get("position")) or _points(session, params.get("at"))
    if not points:
        return None
    p = points[0]
    found = _picked_face(model, p)
    if found is None:
        return None
    info, face = found
    name = params.get("name")
    if "not on a face" not in error:
        # the position is fine and the cut failed: say what the hole meets on its face
        diameter = g.eval_length(session, params.get("diameter"), default=math.nan)
        rim = min(((_point_polyline(p, e["pts"]), e) for e in face["edges"]), key=lambda c: c[0][0], default=None)
        if info["distance"] > 0.5 or rim is None or math.isnan(diameter) or rim[0][0] >= diameter / 2.0:
            return None
        (d, q), e = rim
        other = next((f for f in e["faces"] if f != face["name"]), face["name"])
        out.update(at=_r(p), picked=[info], features=_unique(info["features"] + [model.feature_of(other)]),
                   obstacle={"feature": model.feature_of(other), "face": other, "label": model.face_label(other),
                             "distance": round(d, 3), "at": _r(q), "foreign": model.feature_of(other) not in info["features"]})
        return (f"{'Hole ' + name if name else 'Hole'} (Ø{_num(diameter)}) at {_pt(p)} on {info['label']}: its centre is "
                f"{_num(d)} mm from {model.edge_label(e)} at {_pt(q)}, less than its radius, so the hole cuts through "
                f"that edge into {model.face_label(other)}.")
    out.update(at=_r(p), nearest=info, features=info["features"])
    text = (f"{'Hole ' + name if name else 'Hole'}: {_pt(p)} is {_num(info['distance'])} mm from the nearest face, "
            f"{info['label']}")
    if info.get("nearest_point"):
        text += f"; the nearest point on it is {_pt(info['nearest_point'])}"
    return text + "."


def _locate_generic(model: Model, session, params: dict, error: str, out: dict) -> str | None:
    """What the picks in the parameters and the points in SolidCraft's message lie on."""
    picked, parts = [], []
    for key, finder in (("edges", _picked_edge), ("edge", _picked_edge), ("faces", _picked_face),
                        ("face", _picked_face), ("position", _picked_face), ("at", _picked_face)):
        value = params.get(key)
        for name in ([value] if isinstance(value, str) else value if isinstance(value, list) else []):
            f = model.face_by_name(name) if isinstance(name, str) and key.startswith("face") else None
            if f is not None:
                picked.append({"kind": "face", "name": f["name"], "label": model.face_label(f["name"]),
                               "features": _unique([model.feature_of(f["name"])])})
        for p in _points(session, value):
            found = finder(model, p)
            if found is not None and found[0]["distance"] <= 1.0:
                picked.append(found[0])
    mentioned = []
    for t in _POINT_IN_TEXT.findall(error):
        p = [float(x) for x in t]
        found = _picked_face(model, p)
        if found is not None and found[0]["distance"] <= 0.5:
            mentioned.append(found[0])
            parts.append(f"{_pt(p)} in SolidCraft's message is on {found[0]['label']}")
    if not picked and not mentioned:
        return None
    if picked:
        out["picked"] = picked
        out["at"] = picked[0].get("pick") or out.get("at")
        labels = _unique(("face " if i["kind"] == "face" else "") + i["label"] for i in picked)
        parts.insert(0, "Aimed at " + ", ".join(labels[:4]) + (" …" if len(labels) > 4 else ""))
    if mentioned:
        out["mentioned"] = mentioned
        out.setdefault("at", mentioned[0]["pick"])
    if out.get("at") is None:
        out.pop("at", None)
    out["features"] = _unique(f for i in picked + mentioned for f in i["features"])
    return "; ".join(parts) + "."


def locate(session, command: str | None, params: dict | None, error: str, model: Model | None = None) -> dict | None:
    """Where a failed command went wrong, or None when nothing can be said. The document must be in the
    state the command saw. Returns {"text": one sentence, "at": [x, y, z], "features": [names], "kind"} with
    the details the sentence was made from (picked, obstacle, nearest, fits, requested). kind "blend" and
    "hole" sentences stand on their own, "picks" only names what the command was aimed at."""
    if not isinstance(params, dict) or not isinstance(error, str):
        return None
    try:
        model = model or Model(session)
        if not model.edges:
            return None
        out: dict = {}
        text = None
        kind = "blend" if command in _BLENDS else "hole" if command == "solid.hole" else "picks"
        if kind == "blend":
            text = _locate_blend(model, session, command, params, error, out)
        elif kind == "hole":
            text = _locate_hole(model, session, params, error, out)
        if text is None:
            out, kind = {}, "picks"
            text = _locate_generic(model, session, params, error, out)
        if text is None:
            return None
        out["kind"] = kind
        if params.get("name") and params["name"] not in out.get("features", []):
            out["feature"] = params["name"]
        return dict(out, text=text)
    except Exception:
        return None  # the location is a help, never a second error


# feature types as timeline.inspect names them → the command whose parameters their definition holds
def command_of(feature_type: str) -> str:
    return "solid." + (feature_type or "").lower().removesuffix("feature")


def locate_feature(session, name: str, error: str, model: Model | None = None) -> dict | None:
    """Where a feature already in the timeline fails (after an edit before it). The model is the one
    without the failed feature's effect, which is what the feature saw when it is the last one."""
    try:
        info = session.cmd("timeline.inspect", {"feature": name})
        definition = dict(info.get("definition") or {}, name=name)
        return locate(session, command_of(info.get("type") or ""), definition, error, model=model)
    except Exception:
        return None


def brief(location: dict | None) -> dict | None:
    """A location without the parts that only repeat the sentence (for replies an agent reads)."""
    if not location:
        return None
    return {k: v for k, v in location.items() if k in ("at", "features", "obstacle", "fits", "fits_estimate", "nearest", "edges")}
