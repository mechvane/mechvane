"""Design rule checks for parts: wall thickness, hole edge distances, thread engagement
depth, and FDM printability. Operates via the SolidCraft session."""

import math
import re
import warnings

from . import geometry as g, hole_tables
try:
    from . import katalog
except ImportError:
    katalog = None

PROFILES = {
    "fdm_0.4": {
        "name": "FDM 3D-Druck (0.4 mm Düse)",
        "min_wall_thickness": 1.2,        # mm (3 perimeters @ 0.4mm nozzle)
        "hole_edge_distance_factor": 1.5, # >= 1.5 * d from edge to hole center
        "thread_depth_factor": 1.5,       # >= 1.5 * d thread engagement depth
        "min_hole_diameter": 2.0,         # mm
        "max_overhang_angle": 45.0,       # degrees from vertical
        "build_direction": [0, 0, 1],     # unit vector (+Z)
        "check_horizontal_holes": True,   # threshold loaded from katalog
        "check_heat_set_inserts": True,
    },
    "cnc_alu": {
        "name": "CNC Fräsen (Aluminium)",
        "min_wall_thickness": 1.0,        # mm
        "hole_edge_distance_factor": 1.5, # >= 1.5 * d from edge to hole center
        "thread_depth_factor": 1.5,       # >= 1.5 * d thread engagement depth
        "min_hole_diameter": 1.0,         # mm
        "max_overhang_angle": None,       # no overhang constraint
        "check_pocket_corner_radius": True,  # threshold loaded from katalog
        "check_hole_depth_ratio": True,      # threshold loaded from katalog
        "check_undercuts": True,
    },
}

BUILD_DIRECTIONS = {
    "+Z": [0, 0, 1],
    "-Z": [0, 0, -1],
    "+X": [1, 0, 0],
    "-X": [-1, 0, 0],
    "+Y": [0, 1, 0],
    "-Y": [0, -1, 0],
}


def parse_build_direction(val, allow_vector: bool = True) -> list[float]:
    """Parse build_direction from '+Z|-Z|+X|-X|+Y|-Y' or (if allow_vector) a 3D unit vector."""
    if isinstance(val, str):
        key = val.strip().upper()
        if key in BUILD_DIRECTIONS:
            return list(BUILD_DIRECTIONS[key])
        raise ValueError(
            f"invalid build_direction {val!r}, expected one of: {', '.join(BUILD_DIRECTIONS)}"
        )
    if allow_vector and isinstance(val, (list, tuple)) and len(val) == 3:
        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in val):
            n = g.norm(val)
            if n > 1e-9:
                u = [float(x) / n for x in val]
                for vec in BUILD_DIRECTIONS.values():
                    if g.dot(u, vec) > 1.0 - 1e-9:
                        return list(vec)
                return u
    raise ValueError(
        f"invalid build_direction {val!r}, expected one of: {', '.join(BUILD_DIRECTIONS)}"
    )


def _format_build_direction(d: list[float]) -> str:
    for name, vec in BUILD_DIRECTIONS.items():
        if g.dot(d, vec) > 1.0 - 1e-6:
            return f"{name} ({vec})"
    return str([round(x, 4) for x in d])

# ISO metric coarse threads: (nominal_diameter_mm, pitch_mm, tap_drill_diameter_mm)
ISO_METRIC_THREADS = [
    (2.0, 0.4, 1.6),
    (2.5, 0.45, 2.05),
    (3.0, 0.5, 2.5),
    (4.0, 0.7, 3.3),
    (5.0, 0.8, 4.2),
    (6.0, 1.0, 5.0),
    (8.0, 1.25, 6.8),
    (10.0, 1.5, 8.5),
    (12.0, 1.75, 10.2),
    (14.0, 2.0, 12.0),
    (16.0, 2.0, 14.0),
    (20.0, 2.5, 17.5),
]


def match_iso_tap_drill(diameter: float) -> tuple[float, float, float] | None:
    """Find ISO metric thread matching tap drill (Kernloch) diameter within +/-0.15 mm."""
    for nom_d, pitch, tap_drill in ISO_METRIC_THREADS:
        if abs(diameter - tap_drill) <= 0.15:
            return nom_d, pitch, tap_drill
    return None


_KATALOG_RULES_CACHE = None


def _load_katalog_verfahrensregeln() -> dict:
    """Load manufacturing rules and parameters from the knowledge catalog (katalog/)."""
    # Fallback defaults in case katalog module or catalog files are unavailable (e.g. Pyodide in browser)
    max_hh = 6.0
    src_hh = "https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/"
    ruthex_specs = {
        "M2":   {"d_hole": 3.2, "min_depth": 5.0, "L": 4.0, "code": "RX-M2x4"},
        "M2.5": {"d_hole": 4.0, "min_depth": 6.7, "L": 5.7, "code": "RX-M2.5x5.7"},
        "M3":   {"d_hole": 4.0, "min_depth": 6.7, "L": 5.7, "code": "RX-M3x5.7"},
        "M4":   {"d_hole": 5.6, "min_depth": 9.1, "L": 8.1, "code": "RX-M4x8.1"},
        "M5":   {"d_hole": 6.4, "min_depth": 10.5, "L": 9.5, "code": "RX-M5x9.5"},
        "M6":   {"d_hole": 8.0, "min_depth": 13.7, "L": 12.7, "code": "RX-M6x12.7"},
        "M8":   {"d_hole": 10.0, "min_depth": 13.7, "L": 12.7, "code": "RX-M8x12.7"},
    }
    src_ruthex = "https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen"
    min_corner_r = 1.5
    src_pcr = "https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/"
    max_hdr = 10.0
    src_hdr = "https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/"
    src_uc = "https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/"

    if katalog is not None:
        try:
            entries = katalog.load()
            # 1. Horizontal hole max diameter (FDM)
            e_hh = katalog.get_entry("fdm_liegende_bohrungen_tropfenform", eintraege=entries)
            if e_hh:
                for w in e_hh.get("werte", []):
                    if "grenzdurchmesser" in w.get("name", "").lower():
                        max_hh = float(w["wert"])
                        break
                if e_hh.get("quellen"):
                    src_hh = e_hh["quellen"][0].get("url", src_hh)

            # 2. Ruthex heat-set insert specs (FDM)
            e_ruthex = katalog.get_entry("gewindeeinsaetze_3ddruck_ruthex", eintraege=entries)
            if e_ruthex:
                if e_ruthex.get("quellen"):
                    src_ruthex = e_ruthex["quellen"][0].get("url", src_ruthex)
                werte_map = {w.get("name", ""): w.get("wert") for w in e_ruthex.get("werte", []) if isinstance(w, dict)}
                parsed_specs = {}
                for size in e_ruthex.get("geltungsbereich", {}).get("groesse", []):
                    d_hole = werte_map.get(f"{size} Vorlochbohrung")
                    min_depth = werte_map.get(f"{size} Mindestbohrungstiefe")
                    L = None
                    code = None
                    for k, v in werte_map.items():
                        if k.startswith(f"{size} Länge") and "short" not in k.lower():
                            L = v
                            parts = k.split()
                            if len(parts) >= 3 and parts[2].startswith("RX-"):
                                code = parts[2]
                            break
                    if d_hole is not None and min_depth is not None:
                        parsed_specs[size] = {
                            "d_hole": float(d_hole),
                            "min_depth": float(min_depth),
                            "L": float(L) if L is not None else float(min_depth - 1.0),
                            "code": code or f"RX-{size}",
                        }
                if parsed_specs:
                    ruthex_specs = parsed_specs

            # 3. Pocket corner radius (CNC)
            e_pcr = katalog.get_entry("innenradius_vertikale_kanten_hubs", eintraege=entries)
            if e_pcr:
                for w in e_pcr.get("werte", []):
                    if "mindest-eckenradius" in w.get("name", "").lower() or "mindest-innenradius standard" in w.get("name", "").lower():
                        min_corner_r = float(w["wert"])
                        break
                if e_pcr.get("quellen"):
                    src_pcr = e_pcr["quellen"][0].get("url", src_pcr)

            # 4. Hole depth ratio (CNC)
            e_hdr = katalog.get_entry("bohrungstiefe_fraesen_hubs", eintraege=entries)
            if e_hdr:
                for w in e_hdr.get("werte", []):
                    if "typisch machbare" in w.get("name", "").lower():
                        max_hdr = float(w["wert"])
                        break
                if e_hdr.get("quellen"):
                    src_hdr = e_hdr["quellen"][0].get("url", src_hdr)

            # 5. Undercuts (CNC)
            e_uc = katalog.get_entry("hinterschnitte_fraesen_hubs", eintraege=entries)
            if e_uc and e_uc.get("quellen"):
                src_uc = e_uc["quellen"][0].get("url", src_uc)
        except FileNotFoundError:
            pass
        except Exception as exc:
            warnings.warn(f"Failed to load design rules from katalog: {exc}", stacklevel=2)

    return {
        "max_horizontal_hole_diameter": max_hh,
        "src_horizontal_hole": src_hh,
        "ruthex_specs": ruthex_specs,
        "src_ruthex": src_ruthex,
        "min_pocket_corner_radius": min_corner_r,
        "src_pocket_corner_radius": src_pcr,
        "max_hole_depth_factor": max_hdr,
        "src_hole_depth_ratio": src_hdr,
        "src_undercut": src_uc,
    }


def get_katalog_verfahrensregeln(reload: bool = False) -> dict:
    global _KATALOG_RULES_CACHE
    if _KATALOG_RULES_CACHE is None or reload:
        _KATALOG_RULES_CACHE = _load_katalog_verfahrensregeln()
    return _KATALOG_RULES_CACHE


def _get_cfg(profile: str | dict, build_direction: str | list[float] | None = None) -> dict:
    kt = get_katalog_verfahrensregeln()
    if isinstance(profile, str):
        if profile not in PROFILES:
            raise ValueError(f"unknown profile {profile!r}, available: {', '.join(PROFILES)}")
        base = dict(PROFILES[profile])
    elif isinstance(profile, dict):
        base = dict(PROFILES.get("fdm_0.4", {}))
        base.update(profile)
    else:
        raise TypeError(f"profile must be str or dict, got {type(profile).__name__}")
    if base.get("check_horizontal_holes") and "max_horizontal_hole_diameter" not in base:
        base["max_horizontal_hole_diameter"] = kt["max_horizontal_hole_diameter"]
    if base.get("check_pocket_corner_radius") and "min_pocket_corner_radius" not in base:
        base["min_pocket_corner_radius"] = kt["min_pocket_corner_radius"]
    if base.get("check_hole_depth_ratio") and "max_hole_depth_factor" not in base:
        base["max_hole_depth_factor"] = kt["max_hole_depth_factor"]
    if build_direction is not None:
        base["build_direction"] = parse_build_direction(build_direction)
    elif base.get("build_direction") is not None:
        base["build_direction"] = parse_build_direction(base["build_direction"])
    else:
        base["build_direction"] = [0, 0, 1]
    return base


_eval_length = g.eval_length


def _extract_holes(session, body_name: str, faces: list[dict], bbox: dict,
                   timeline_map: dict, threads: list[dict]) -> tuple[list[dict], list[dict]]:
    """Group cylindrical faces sharing an axis and radius into logical holes and external cylinders."""
    cyl_faces = [f for f in faces if f.get("cylinder")]
    feat_cyl_faces = {}
    for f in cyl_faces:
        parts = f["name"].split(":")
        fid = parts[0] if parts[0].startswith("F") and parts[0][1:].isdigit() else None
        feat_cyl_faces.setdefault(fid, []).append(f)

    groups = []
    for f_list in feat_cyl_faces.values():
        groups.extend(g.group_cylindrical_faces(f_list))

    is_hole_list = g.classify_hole_groups(session, body_name, groups, timeline_map, threads, bbox)

    holes = []
    ext_cylinders = []
    for grp, is_hole in zip(groups, is_hole_list):
        r = grp[0]["cylinder"]["radius"]
        d = 2.0 * r
        axis = g.unit(grp[0]["cylinder"]["axis"])
        p0 = grp[0]["cylinder"]["origin"]
        total_area = sum(f["area"] for f in grp)
        length = g.cylinder_group_length(grp)

        # Center along axis
        weighted_t = sum(f["area"] * g.dot(g.sub(f["centroid"], p0), axis) for f in grp) / total_area
        center = g.add(p0, g.scale(axis, weighted_t))
        rep_pt = grp[0].get("point") or grp[0].get("centroid") or center

        if not is_hole:
            ext_cylinders.append({
                "faces": [f["name"] for f in grp],
                "representative_point": rep_pt,
                "radius": r,
                "diameter": d,
                "axis": axis,
                "origin": p0,
                "center": center,
                "length": length,
            })
            continue

        # Associated feature id from face name F{id}:...
        feat_id = None
        for f in grp:
            parts = f["name"].split(":")
            if parts[0].startswith("F") and parts[0][1:].isdigit():
                feat_id = int(parts[0][1:])
                break
        feat_info = timeline_map.get(feat_id, {})

        # Blind hole check
        is_blind = False
        if feat_info.get("type") == "HoleFeature":
            defn = feat_info.get("definition", {})
            if "depth" in defn and "to" not in defn:
                # the floor of a counterbore or countersink is no hole bottom
                end_caps = [f for f in faces if f["name"].startswith(f"F{feat_id}:") and not f.get("cylinder")
                            and ":cbore:" not in f["name"] and ":csink:" not in f["name"]] if feat_id is not None else []
                if end_caps:
                    is_blind = True
        elif feat_id is not None:
            # End cap faces belonging to this feature
            end_caps = [f for f in faces if f["name"].startswith(f"F{feat_id}:") and not f.get("cylinder")]
            if end_caps:
                is_blind = True

        holes.append({
            "faces": [f["name"] for f in grp],
            "representative_point": grp[0]["point"],
            "radius": r,
            "diameter": d,
            "axis": axis,
            "center": center,
            "length": length,
            "feature": feat_info,
            "is_blind": is_blind,
            "thread": None,
        })

    # Thread match: internal threads matched by collinearity and axial overlap.
    # Each thread is assigned to at most one hole, matching highest axial overlap first.
    candidates = []
    for h_idx, h in enumerate(holes):
        h_axis = h["axis"]
        h_center = h["center"]
        h_L = h.get("length", 0.0)
        c_proj = g.dot(h_center, h_axis)
        h_t_min = c_proj - h_L / 2.0
        h_t_max = c_proj + h_L / 2.0
        for th_idx, th in enumerate(threads):
            if not th.get("internal"):
                continue
            th_axis = th.get("axis")
            if th_axis and not g.parallel(th_axis, h_axis, tol=1e-3):
                continue
            if g.dist_to_line(th["axis_point"], h_center, h_axis) >= 0.05:
                continue
            t_axis = g.unit(th_axis) if th_axis else h_axis
            th_start_pt = g.add(th["axis_point"], g.scale(t_axis, th.get("start", 0.0)))
            th_end_pt = g.add(th["axis_point"], g.scale(t_axis, th.get("end", 0.0)))
            t_th_start = g.dot(th_start_pt, h_axis)
            t_th_end = g.dot(th_end_pt, h_axis)
            th_t_min = min(t_th_start, t_th_end)
            th_t_max = max(t_th_start, t_th_end)
            overlap = min(h_t_max, th_t_max) - max(h_t_min, th_t_min)
            axial_dist = abs((th_t_min + th_t_max) / 2.0 - c_proj)
            if overlap > -0.05:
                candidates.append((overlap, -axial_dist, h_idx, th_idx))

    used_holes = set()
    used_threads = set()
    for overlap, neg_dist, h_idx, th_idx in sorted(candidates, reverse=True):
        if h_idx not in used_holes and th_idx not in used_threads:
            holes[h_idx]["thread"] = threads[th_idx]
            used_holes.add(h_idx)
            used_threads.add(th_idx)

    return holes, ext_cylinders


def _check_body(session, body: dict, timeline_map: dict, threads: list[dict], cfg: dict) -> dict:
    faces = session.cmd("model.faces", {"body": body["name"]}).get("faces", [])
    try:
        edges = session.cmd("model.edges", {"body": body["name"]}).get("edges", [])
    except Exception:
        edges = []
    bbox = body["bbox"]
    holes, ext_cyls = _extract_holes(session, body["name"], faces, bbox, timeline_map, threads)

    rules = {
        "min_wall_thickness": {"status": "ok", "findings": []},
        "hole_edge_distance": {"status": "ok", "findings": []},
        "thread_depth": {"status": "ok", "findings": []},
        "printability": {"status": "ok", "findings": []},
        "countersink_clearance": {"status": "ok", "findings": []},
        "horizontal_hole": {"status": "ok", "findings": []},
        "heat_set_insert": {"status": "ok", "findings": []},
        "pocket_corner_radius": {"status": "ok", "findings": []},
        "hole_depth_ratio": {"status": "ok", "findings": []},
        "undercut": {"status": "ok", "findings": []},
    }

    # A countersink tool only leaves its flat top face (`csink:base`) when it cut material above
    # the entry face, i.e. it notched a neighbouring wall (SolidCraft cuts the cone past the entry).
    for f in faces:
        if f.get("name", "").split("#")[0].endswith(":csink:base"):
            rules["countersink_clearance"]["status"] = "fail"
            rules["countersink_clearance"]["findings"].append({
                "status": "fail",
                "location": {"point": f.get("point") or f.get("centroid"), "face": f["name"]},
                "message": (f"Countersink cuts into material above its entry face (face {f['name']}): "
                            "a neighbouring wall is notched, move the hole away or use a counterbore"),
            })

    min_wall = cfg["min_wall_thickness"]
    edge_factor = cfg["hole_edge_distance_factor"]

    # 1. Hole edge distance and wall thickness to boundaries
    for h in holes:
        c, r, d, axis = h["center"], h["radius"], h["diameter"], h["axis"]

        # Axial range of the hole along its cylinder axis
        hole_edges = [e for e in edges if any(g.edge_touches(e.get("name", ""), fn) for fn in h["faces"])]
        if hole_edges:
            hole_pts = [e["start"] for e in hole_edges] + [e["end"] for e in hole_edges]
            t_h_min = min(g.dot(pt, axis) for pt in hole_pts)
            t_h_max = max(g.dot(pt, axis) for pt in hole_pts)
        else:
            c_proj = g.dot(c, axis)
            L = h.get("length", 0.0)
            t_h_min = c_proj - L / 2.0
            t_h_max = c_proj + L / 2.0
        h["t_range"] = (t_h_min, t_h_max)

        side_faces = [f for f in faces if f.get("plane_normal") and abs(g.dot(f["plane_normal"], axis)) < 0.1]
        dist_faces = []
        for sf in side_faces:
            n = sf["plane_normal"]
            v_to_plane = g.sub(sf["point"], c)
            signed_dist = g.dot(v_to_plane, n)
            # Face normal must point outward from the hole, not inward as in interior steps/pockets
            if signed_dist < -1e-4:
                continue

            f_edges = [e for e in edges if g.edge_touches(e.get("name", ""), sf["name"])]
            if f_edges:
                sf_pts = [e["start"] for e in f_edges] + [e["end"] for e in f_edges]
                t_sf_min = min(g.dot(pt, axis) for pt in sf_pts)
                t_sf_max = max(g.dot(pt, axis) for pt in sf_pts)
                # Face must actually overlap the hole along the hole axis
                overlap = min(t_sf_max, t_h_max) - max(t_sf_min, t_h_min)
                if overlap < 1e-3:
                    continue

                # Face must cover the hole in the transverse direction perpendicular to axis and normal
                u_trans = g.unit(g.cross(axis, n))
                u_hole = g.dot(c, u_trans)
                u_sf_min = min(g.dot(pt, u_trans) for pt in sf_pts)
                u_sf_max = max(g.dot(pt, u_trans) for pt in sf_pts)
                if u_hole < u_sf_min - r - 1e-4 or u_hole > u_sf_max + r + 1e-4:
                    continue

            dist = abs(signed_dist)
            dist_faces.append((dist, sf["name"]))

        # Non-coaxial external cylindrical walls contribute to edge distance
        for ec in ext_cyls:
            if not g.parallel(axis, ec["axis"], tol=1e-3):
                continue
            d_axes = g.dist_to_line(c, ec["origin"], ec["axis"])
            if d_axes < 0.05:
                # Coaxial cylinder (Dom): handled in wall thickness check below
                continue
            ec_edges = [e for e in edges if any(g.edge_touches(e.get("name", ""), fn) for fn in ec["faces"])]
            if ec_edges:
                ec_pts = [e["start"] for e in ec_edges] + [e["end"] for e in ec_edges]
                t_ec_min = min(g.dot(pt, axis) for pt in ec_pts)
                t_ec_max = max(g.dot(pt, axis) for pt in ec_pts)
            else:
                c_proj = g.dot(ec["center"], axis)
                L = ec.get("length", 0.0)
                t_ec_min = c_proj - L / 2.0
                t_ec_max = c_proj + L / 2.0
            overlap = min(t_ec_max, t_h_max) - max(t_ec_min, t_h_min)
            if overlap < 1e-3:
                continue

            if d_axes + r <= ec["radius"] + 1e-4:
                dist = ec["radius"] - d_axes
            else:
                dist = d_axes - ec["radius"]
            dist_faces.append((dist, ec["faces"][0]))

        # Distance to bounding box only along lateral axes orthogonal to cylinder axis
        d_box = []
        for i in (0, 1, 2):
            if abs(axis[i]) < 0.5:
                d_box.append(min(abs(c[i] - bbox["min"][i]), abs(c[i] - bbox["max"][i])))
        dist_bbox = min(d_box) if d_box else float("inf")

        if dist_faces:
            min_dist, nearest_face = min(dist_faces, key=lambda x: x[0])
            min_dist = min(min_dist, dist_bbox)
        else:
            min_dist, nearest_face = dist_bbox, "bbox"

        req_edge = edge_factor * d
        if any(":cbore:" in fn for fn in h["faces"]):
            pass  # a counterbore is the head recess of its bore: the bore's own edge distance and the wall count
        elif min_dist < req_edge - 1e-4:
            rules["hole_edge_distance"]["status"] = "fail"
            rules["hole_edge_distance"]["findings"].append({
                "status": "fail",
                "location": {"point": h["representative_point"], "face": h["faces"][0]},
                "message": (f"Hole edge distance {min_dist:.2f} mm < {req_edge:.2f} mm "
                            f"({edge_factor:.1f} × d for Ø {d:.1f} mm) to face {nearest_face}"),
                "value": round(min_dist, 4),
                "threshold": round(req_edge, 4),
            })
        else:
            rules["hole_edge_distance"]["findings"].append({
                "status": "ok",
                "location": {"point": h["representative_point"], "face": h["faces"][0]},
                "message": (f"Hole edge distance {min_dist:.2f} mm >= {req_edge:.2f} mm "
                            f"({edge_factor:.1f} × d for Ø {d:.1f} mm)"),
                "value": round(min_dist, 4),
                "threshold": round(req_edge, 4),
            })

        w_edge = max(0.0, min_dist - r)
        w_face = nearest_face

        # Wall thickness check for hollow cylinders (Dom: R_outer - r_inner) and nearest external cylinder walls
        for ec in ext_cyls:
            if not g.parallel(axis, ec["axis"], tol=1e-3):
                continue
            d_axes = g.dist_to_line(c, ec["origin"], ec["axis"])
            ec_edges = [e for e in edges if any(g.edge_touches(e.get("name", ""), fn) for fn in ec["faces"])]
            if ec_edges:
                ec_pts = [e["start"] for e in ec_edges] + [e["end"] for e in ec_edges]
                t_ec_min = min(g.dot(pt, axis) for pt in ec_pts)
                t_ec_max = max(g.dot(pt, axis) for pt in ec_pts)
            else:
                c_proj = g.dot(ec["center"], axis)
                L = ec.get("length", 0.0)
                t_ec_min = c_proj - L / 2.0
                t_ec_max = c_proj + L / 2.0
            overlap = min(t_ec_max, t_h_max) - max(t_ec_min, t_h_min)
            if overlap < 1e-3:
                continue

            if d_axes < 0.05:
                # Coaxial hollow cylinder / Dom: wall = R_outer - r_inner
                w_cyl = max(0.0, ec["radius"] - r)
            elif d_axes + r <= ec["radius"] + 1e-4:
                w_cyl = max(0.0, ec["radius"] - d_axes - r)
            else:
                w_cyl = max(0.0, d_axes - ec["radius"] - r)

            if w_cyl < w_edge:
                w_edge = w_cyl
                w_face = ec["faces"][0]

        if w_edge < min_wall - 1e-4:
            rules["min_wall_thickness"]["status"] = "fail"
            rules["min_wall_thickness"]["findings"].append({
                "status": "fail",
                "location": {"point": h["representative_point"], "face": h["faces"][0]},
                "message": (f"Wall thickness to edge is {w_edge:.2f} mm < {min_wall:.2f} mm "
                            f"for hole Ø {d:.1f} mm"),
                "value": round(w_edge, 4),
                "threshold": round(min_wall, 4),
            })
        else:
            rules["min_wall_thickness"]["findings"].append({
                "status": "ok",
                "location": {"point": h["representative_point"], "face": h["faces"][0]},
                "message": f"Wall thickness to edge is {w_edge:.2f} mm >= {min_wall:.2f} mm",
                "value": round(w_edge, 4),
                "threshold": round(min_wall, 4),
            })

    # Wall thickness between adjacent holes
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            h1, h2 = holes[i], holes[j]
            if g.parallel(h1["axis"], h2["axis"], tol=1e-3):
                # Coaxial holes (e.g. counterbore and bore of the same stepped hole) are not adjacent holes
                if g.dist_to_line(h1["center"], h2["center"], h1["axis"]) < 0.05:
                    continue
                # Holes that do not overlap along their axis (e.g. blind holes from opposite sides)
                # are separated by material along the axis, not by a wall between them
                if "t_range" in h1 and "t_range" in h2:
                    sign = 1.0 if g.dot(h1["axis"], h2["axis"]) > 0 else -1.0
                    r2 = sorted(sign * t for t in h2["t_range"])
                    if min(h1["t_range"][1], r2[1]) - max(h1["t_range"][0], r2[0]) < 1e-3:
                        continue
                delta = g.sub(h1["center"], h2["center"])
                proj_dist = g.norm(g.sub(delta, g.scale(h1["axis"], g.dot(delta, h1["axis"]))))
                w_between = proj_dist - (h1["radius"] + h2["radius"])
                if w_between < min_wall - 1e-4:
                    rules["min_wall_thickness"]["status"] = "fail"
                    rules["min_wall_thickness"]["findings"].append({
                        "status": "fail",
                        "location": {"point": h1["representative_point"], "face": h1["faces"][0]},
                        "message": (f"Wall thickness between holes is {w_between:.2f} mm < {min_wall:.2f} mm "
                                    f"({h1['faces'][0]} to {h2['faces'][0]})"),
                        "value": round(w_between, 4),
                        "threshold": round(min_wall, 4),
                    })

    # Minimum body dimensions
    b_dims = [bbox["max"][k] - bbox["min"][k] for k in range(3)]
    min_dim = min(b_dims)
    if min_dim < min_wall - 1e-4:
        rules["min_wall_thickness"]["status"] = "fail"
        rules["min_wall_thickness"]["findings"].append({
            "status": "fail",
            "location": {"point": body.get("center_of_mass", bbox["min"]), "body": body["name"]},
            "message": f"Body minimum dimension {min_dim:.2f} mm < {min_wall:.2f} mm",
            "value": round(min_dim, 4),
            "threshold": round(min_wall, 4),
        })

    # 2. Thread engagement depth
    thread_factor = cfg["thread_depth_factor"]
    for h in holes:
        # Counterbores are bolt head recesses, never threaded
        if any(":cbore:" in fn for fn in h["faces"]):
            continue
        th = h["thread"]
        feat_defn = h["feature"].get("definition", {})
        # Clearance holes (e.g. ISO 273 clearance) carry fasteners through, never internal threads
        if "clearance" in feat_defn:
            continue
        thread_spec = th.get("designation") if th else feat_defn.get("thread")

        nom_d = None
        if thread_spec:
            if thread_spec.upper().startswith("M"):
                try:
                    nom_d = float(thread_spec[1:].split("X")[0].split("x")[0])
                except ValueError:
                    pass
        if not nom_d and (h["is_blind"] or h["thread"] or feat_defn.get("thread")):
            matched = match_iso_tap_drill(h["diameter"])
            if matched:
                nom_d, pitch, tap_drill = matched
                thread_spec = f"M{nom_d:.0f} tap drill (Kernloch Ø {tap_drill:.1f} mm)"

        if nom_d:
            req_depth = thread_factor * nom_d
            if th:
                act_depth = abs(th["end"] - th["start"])
            else:
                depth_val = _eval_length(session, feat_defn.get("depth"), default=h["length"])
                act_depth = min(depth_val, h["length"]) if depth_val else h["length"]
            if act_depth < req_depth - 1e-4:
                rules["thread_depth"]["status"] = "fail"
                rules["thread_depth"]["findings"].append({
                    "status": "fail",
                    "location": {"point": h["representative_point"], "face": h["faces"][0]},
                    "message": (f"Thread engagement depth {act_depth:.1f} mm < {req_depth:.1f} mm "
                                f"({thread_factor:.1f} × d for {thread_spec}{cfg.get('thread_depth_basis', '')})"),
                    "value": round(act_depth, 4),
                    "threshold": round(req_depth, 4),
                })
            else:
                rules["thread_depth"]["findings"].append({
                    "status": "ok",
                    "location": {"point": h["representative_point"], "face": h["faces"][0]},
                    "message": (f"Thread engagement depth {act_depth:.1f} mm >= {req_depth:.1f} mm "
                                f"({thread_factor:.1f} × d for {thread_spec}{cfg.get('thread_depth_basis', '')})"),
                    "value": round(act_depth, 4),
                    "threshold": round(req_depth, 4),
                })
        elif h["is_blind"]:
            req_depth = thread_factor * h["diameter"]
            depth_val = _eval_length(session, feat_defn.get("depth"), default=h["length"])
            act_depth = min(depth_val, h["length"]) if depth_val else h["length"]
            if act_depth < req_depth - 1e-4:
                if rules["thread_depth"]["status"] != "fail":
                    rules["thread_depth"]["status"] = "warn"
                rules["thread_depth"]["findings"].append({
                    "status": "warn",
                    "location": {"point": h["representative_point"], "face": h["faces"][0]},
                    "message": (f"Blind hole depth {act_depth:.1f} mm < {req_depth:.1f} mm "
                                f"({thread_factor:.1f} × d if intended for threaded fasteners)"),
                    "value": round(act_depth, 4),
                    "threshold": round(req_depth, 4),
                })

    # 3. Printability (FDM overhangs and small holes)
    max_oh = cfg.get("max_overhang_angle")
    if max_oh is not None:
        d = g.unit(cfg.get("build_direction") or [0, 0, 1])
        dir_label = _format_build_direction(d)
        lo, hi = bbox["min"], bbox["max"]
        corners = [[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        h_min = min(g.dot(c, d) for c in corners)
        sin_limit = math.sin(math.radians(max_oh))
        for f in faces:
            n = f.get("plane_normal")
            if not n:
                continue
            nd = g.dot(n, d)
            if nd >= -0.01:
                continue
            # Build plate check
            if nd <= -0.99 and abs(g.dot(f["centroid"], d) - h_min) < 0.05:
                continue

            # Downward face above print bed
            if nd < -sin_limit:
                rules["printability"]["status"] = "fail"
                rules["printability"]["findings"].append({
                    "status": "fail",
                    "location": {"point": f["centroid"], "face": f["name"]},
                    "message": (f"Unsupported overhang on face {f['name']} (normal {n}, centroid {f['centroid']}) "
                                f"exceeds {max_oh:.0f}° limit in build direction {dir_label}"),
                })

    min_hole_d = cfg.get("min_hole_diameter", 0)
    for h in holes:
        if h["diameter"] < min_hole_d - 1e-4:
            if rules["printability"]["status"] != "fail":
                rules["printability"]["status"] = "warn"
            rules["printability"]["findings"].append({
                "status": "warn",
                "location": {"point": h["representative_point"], "face": h["faces"][0]},
                "message": (f"Hole diameter {h['diameter']:.1f} mm < {min_hole_d:.1f} mm "
                            f"(FDM minimum hole diameter for 0.4 mm nozzle)"),
                "value": round(h["diameter"], 4),
                "threshold": round(min_hole_d, 4),
            })

    kt_vals = get_katalog_verfahrensregeln()

    # 4. FDM horizontal holes: check for unsupported horizontal-axis holes > max_horizontal_hole_diameter
    max_horiz_d = cfg.get("max_horizontal_hole_diameter")
    src_hh = kt_vals["src_horizontal_hole"]
    if max_horiz_d is not None:
        d_build = g.unit(cfg.get("build_direction") or [0, 0, 1])
        for h in holes:
            if abs(g.dot(h["axis"], d_build)) < 0.1:
                if h["diameter"] > max_horiz_d + 1e-4:
                    if rules["horizontal_hole"]["status"] != "fail":
                        rules["horizontal_hole"]["status"] = "warn"
                    rules["horizontal_hole"]["findings"].append({
                        "status": "warn",
                        "location": {"point": h["representative_point"], "face": h["faces"][0]},
                        "message": (f"Horizontal hole Ø {h['diameter']:.1f} mm > {max_horiz_d:.1f} mm: "
                                    "needs support or a teardrop/diamond profile to avoid bridging sag (Hubs FDM guide)"),
                        "value": round(h["diameter"], 4),
                        "threshold": round(max_horiz_d, 4),
                        "source": src_hh,
                    })

    # 5. FDM heat-set inserts (Ruthex RX series / CNC Kitchen)
    if cfg.get("check_heat_set_inserts"):
        RUTHEX_SPECS = kt_vals["ruthex_specs"]
        src_ruthex = kt_vals["src_ruthex"]
        for h in holes:
            if any(":cbore:" in fn for fn in h["faces"]):
                continue
            feat = h.get("feature") or {}
            feat_defn = feat.get("definition", {})
            if "clearance" in feat_defn:
                continue

            feat_name = feat.get("name", "")

            # Only check if the hole is explicitly designated as an insert
            insert_marker = None
            if feat_defn.get("insert"):
                insert_marker = feat_defn.get("insert")
            elif feat_defn.get("hole_type") == "insert":
                insert_marker = True
            elif feat_defn.get("use_insert"):
                insert_marker = True
            elif feat_defn.get("insert_norm"):
                insert_marker = feat_defn.get("insert_norm")
            elif feat.get("insert"):
                insert_marker = feat.get("insert")
            elif feat.get("use_insert"):
                insert_marker = True
            elif h.get("insert") or h.get("use_insert"):
                insert_marker = h.get("insert") or True
            elif re.search(r"(?:^|[_ -])(insert|ruthex|gewindeeinsatz|einschmelz)(?:[_ -]|$)", feat_name, re.IGNORECASE):
                insert_marker = feat_name
            elif cfg.get("insert_holes") or cfg.get("inserts"):
                ins_cfg = cfg.get("insert_holes") or cfg.get("inserts")
                if isinstance(ins_cfg, (list, tuple, set)):
                    if feat_name in ins_cfg or any(fn in ins_cfg for fn in h["faces"]):
                        insert_marker = True
                elif ins_cfg is True:
                    insert_marker = True

            if not insert_marker:
                continue

            # Determine M-size for this insert
            m_size = None
            if isinstance(insert_marker, str):
                m_match = re.search(r"(?:^|[^a-zA-Z0-9])(M\d+(?:\.\d+)?)(?:[^a-zA-Z0-9]|$)", insert_marker, re.IGNORECASE)
                if m_match and m_match.group(1).upper() in RUTHEX_SPECS:
                    m_size = m_match.group(1).upper()

            if not m_size:
                th = h["thread"]
                thread_spec = th.get("designation") if th else feat_defn.get("thread")
                if thread_spec and thread_spec.upper().startswith("M"):
                    m_part = thread_spec.upper().split("X")[0].split("-")[0].strip()
                    if m_part in RUTHEX_SPECS:
                        m_size = m_part

            if not m_size:
                m_match = re.search(r"(?:^|[^a-zA-Z0-9])(M\d+(?:\.\d+)?)(?:[^a-zA-Z0-9]|$)", feat_name, re.IGNORECASE)
                if m_match and m_match.group(1).upper() in RUTHEX_SPECS:
                    m_size = m_match.group(1).upper()

            if not m_size:
                # Try matching by mounting hole diameter in RUTHEX_SPECS
                for sz, sp in RUTHEX_SPECS.items():
                    if abs(h["diameter"] - sp["d_hole"]) < 0.2:
                        m_size = sz
                        break

            if not m_size:
                continue

            depth_val = _eval_length(session, feat_defn.get("depth"), default=h["length"])
            act_depth = min(depth_val, h["length"]) if depth_val else h["length"]
            spec = RUTHEX_SPECS[m_size]

            if h["diameter"] < spec["d_hole"] - 0.2:
                rules["heat_set_insert"]["status"] = "fail"
                rules["heat_set_insert"]["findings"].append({
                    "status": "fail",
                    "location": {"point": h["representative_point"], "face": h["faces"][0]},
                    "message": (f"Hole Ø {h['diameter']:.1f} mm is too small for {m_size} heat-set insert: "
                                f"ruthex {spec['code']} requires hole Ø {spec['d_hole']:.1f} mm"),
                    "value": round(h["diameter"], 4),
                    "threshold": round(spec["d_hole"], 4),
                    "source": src_ruthex,
                })
            elif h["is_blind"] and act_depth < spec["min_depth"] - 1e-4:
                rules["heat_set_insert"]["status"] = "fail"
                rules["heat_set_insert"]["findings"].append({
                    "status": "fail",
                    "location": {"point": h["representative_point"], "face": h["faces"][0]},
                    "message": (f"Blind hole depth {act_depth:.1f} mm < {spec['min_depth']:.1f} mm for {m_size} "
                                f"heat-set insert (ruthex {spec['code']} requires L={spec['L']:.1f} mm + 1 mm clearance)"),
                    "value": round(act_depth, 4),
                    "threshold": round(spec["min_depth"], 4),
                    "source": src_ruthex,
                })

    # 6. CNC pocket corner radius: check vertical internal/concave pocket corners
    min_corner_r = cfg.get("min_pocket_corner_radius")
    src_pcr = kt_vals["src_pocket_corner_radius"]
    if min_corner_r is not None:
        tool_dir = g.unit(cfg.get("build_direction") or [0, 0, 1])
        f_map = {f["name"]: f for f in faces}

        for f in faces:
            if f.get("cylinder") and g.blend_parts(f.get("name", "")) is not None:
                axis = f["cylinder"]["axis"]
                if abs(g.dot(axis, tool_dir)) > 0.9:
                    touch_names = g.blend_parts(f["name"]) or []
                    is_concave = False
                    if len(touch_names) >= 2 and touch_names[0] in f_map and touch_names[1] in f_map:
                        f1, f2 = f_map[touch_names[0]], f_map[touch_names[1]]
                        n1, n2 = f1.get("plane_normal"), f2.get("plane_normal")
                        c1 = f1.get("centroid") or f1.get("point")
                        c2 = f2.get("centroid") or f2.get("point")
                        if n1 and n2 and c1 and c2:
                            if abs(g.dot(n1, tool_dir)) < 0.1 and abs(g.dot(n2, tool_dir)) < 0.1:
                                p0 = f["cylinder"]["origin"]
                                d1 = g.dot(g.sub(p0, c1), n1)
                                d2 = g.dot(g.sub(p0, c2), n2)
                                if d1 > 0.05 and d2 > 0.05:
                                    is_concave = True
                    if not is_concave:
                        continue

                    r_blend = f["cylinder"]["radius"]
                    if r_blend < min_corner_r - 1e-4:
                        rules["pocket_corner_radius"]["status"] = "fail"
                        rules["pocket_corner_radius"]["findings"].append({
                            "status": "fail",
                            "location": {"point": f.get("point") or f.get("centroid"), "face": f["name"]},
                            "message": (f"Internal pocket corner radius {r_blend:.2f} mm < {min_corner_r:.2f} mm: "
                                        "smaller than common CNC milling cutter radius (Hubs CNC guide)"),
                            "value": round(r_blend, 4),
                            "threshold": round(min_corner_r, 4),
                            "source": src_pcr,
                        })

        for e in edges:
            p1, p2 = e["start"], e["end"]
            edge_vec = g.sub(p2, p1)
            edge_len = g.norm(edge_vec)
            if edge_len > 0.5:
                e_u = g.scale(edge_vec, 1.0 / edge_len)
                if abs(g.dot(e_u, tool_dir)) > 0.9:
                    t = e.get("touches", [])
                    if not t and "|" in e.get("name", ""):
                        t = e["name"].split("|")
                    if len(t) >= 2 and t[0] in f_map and t[1] in f_map:
                        f1, f2 = f_map[t[0]], f_map[t[1]]
                        n1, n2 = f1.get("plane_normal"), f2.get("plane_normal")
                        if n1 and n2:
                            if abs(g.dot(n1, tool_dir)) < 0.1 and abs(g.dot(n2, tool_dir)) < 0.1:
                                mid = g.scale(g.add(p1, p2), 0.5)
                                c1 = f1.get("centroid") or f1.get("point")
                                c2 = f2.get("centroid") or f2.get("point")
                                v1 = g.sub(c1, mid)
                                v2 = g.sub(c2, mid)
                                if g.dot(v1, n2) > 0.1 and g.dot(v2, n1) > 0.1:
                                    rules["pocket_corner_radius"]["status"] = "fail"
                                    rules["pocket_corner_radius"]["findings"].append({
                                        "status": "fail",
                                        "location": {"point": mid, "edge": e.get("name")},
                                        "message": (f"Sharp vertical inside corner at {e.get('name', 'edge')} (radius 0 mm < {min_corner_r:.2f} mm): "
                                                    "CNC end mills cannot cut sharp 90° internal corners; add a fillet or relief (Hubs CNC guide)"),
                                        "value": 0.0,
                                        "threshold": round(min_corner_r, 4),
                                        "source": src_pcr,
                                    })

    # 7. CNC hole depth-to-diameter ratio (twist drill depth limit)
    max_depth_factor = cfg.get("max_hole_depth_factor")
    src_hdr = kt_vals["src_hole_depth_ratio"]
    if max_depth_factor is not None:
        for h in holes:
            if any(":cbore:" in fn for fn in h["faces"]):
                continue
            feat_defn = h["feature"].get("definition", {})
            depth_val = _eval_length(session, feat_defn.get("depth"), default=h["length"])
            act_depth = min(depth_val, h["length"]) if depth_val else h["length"]
            if h["diameter"] > 1e-4:
                ratio = act_depth / h["diameter"]
                if ratio > max_depth_factor + 1e-4:
                    if rules["hole_depth_ratio"]["status"] != "fail":
                        rules["hole_depth_ratio"]["status"] = "warn"
                    rules["hole_depth_ratio"]["findings"].append({
                        "status": "warn",
                        "location": {"point": h["representative_point"], "face": h["faces"][0]},
                        "message": (f"Hole depth-to-diameter ratio {ratio:.1f} > {max_depth_factor:.1f} "
                                    f"(depth {act_depth:.1f} mm for Ø {h['diameter']:.1f} mm exceeds standard twist drill ratio 10 × d, Hubs CNC guide)"),
                        "value": round(ratio, 4),
                        "threshold": round(max_depth_factor, 4),
                        "source": src_hdr,
                    })

    # 8. CNC undercuts (downward-facing surfaces above part bottom not reachable from tool direction)
    if cfg.get("check_undercuts"):
        tool_dir = g.unit(cfg.get("build_direction") or [0, 0, 1])
        src_uc = kt_vals["src_undercut"]
        lo, hi = bbox["min"], bbox["max"]
        corners = [[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        min_h = min(g.dot(c, tool_dir) for c in corners)
        hole_faces = {fn for h in holes for fn in h["faces"]}
        for f in faces:
            if f["name"] in hole_faces or any(k in f.get("name", "") for k in (":bore:", ":cbore:", ":csink:")):
                continue
            n = f.get("plane_normal")
            if n and g.dot(n, tool_dir) < -0.1:
                pt = f.get("centroid") or f.get("point")
                if pt and g.dot(pt, tool_dir) > min_h + 0.1:
                    if rules["undercut"]["status"] != "fail":
                        rules["undercut"]["status"] = "warn"
                    rules["undercut"]["findings"].append({
                        "status": "warn",
                        "location": {"point": pt, "face": f["name"]},
                        "message": (f"Possible undercut on face {f['name']} (normal {n}, centroid {pt}): "
                                    "downward surface is not directly accessible from above in 3-axis CNC milling (Hubs CNC guide)"),
                        "source": src_uc,
                    })

    return rules


def body_material(session) -> str | None:
    """The material assigned to the part's bodies in SolidCraft (material.assign), as a key of the
    engagement table; None when unassigned (Default), mixed or not in the table."""
    # only the measure tool reports the material; document.inspect leaves it out
    bodies = session.tool("measure", {}).get("bodies", [])
    names = {b.get("material") for b in bodies} - {None, "Default"}
    if len(names) != 1:
        return None
    try:
        return hole_tables.normalize_material(names.pop())
    except ValueError:
        return None


def saved_rules(doc) -> dict:
    """Profile and material saved in the part file (save_rules), {} for none or a bare session."""
    if not hasattr(doc, "metadata"):
        return {}
    return dict(doc.metadata().get("rules") or {})


def save_rules(doc, profile: str | None = None, material: str | None = None) -> dict:
    """Save the profile and material for the design rules in the part file's metadata and save the file.

    An empty material clears it (the bodies' SolidCraft material applies again)."""
    rules = saved_rules(doc)
    if profile is not None:
        _get_cfg(profile)  # unknown profile: ValueError, nothing saved
        rules["profile"] = profile
    if material is not None:
        if material:
            rules["material"] = hole_tables.normalize_material(material)
        else:
            rules.pop("material", None)
    meta = doc.metadata()
    meta["rules"] = rules
    doc.set_metadata(meta)
    doc.save()
    return rules


def check(session_or_doc, profile: str | dict | None = None,
          build_direction: str | list[float] | None = None, material: str | None = None) -> dict:
    """Check a part against design rules using the open SolidCraft session.

    profile: without it the profile saved in the part file (save_rules) applies, else fdm_0.4.
    material: the part's material (steel, cast_iron, alu, alu_wrought, brass, ...): the thread depth
    then follows the engagement table in hole_tables instead of the profile's flat factor. Without it
    the material saved in the part file applies, then the material assigned to the bodies in
    SolidCraft, if the table knows it."""
    session = getattr(session_or_doc, "session", session_or_doc)
    saved = saved_rules(session_or_doc)
    if profile is None:
        profile = saved.get("profile") or "fdm_0.4"
    cfg = _get_cfg(profile, build_direction=build_direction)
    material_source = "argument" if material else None
    if not material and saved.get("material"):
        material, material_source = saved["material"], "saved"
    if not material:
        material = body_material(session)
        material_source = "body" if material else None
    if material:
        mat = hole_tables.normalize_material(material)
        entry = hole_tables.MATERIAL_ENGAGEMENT_DEPTHS[mat]
        cfg["thread_depth_factor"] = entry["factor"]
        cfg["thread_depth_basis"] = f" in {mat}" + ("" if entry.get("verified") else ", unverified value")
    profile_name = profile if isinstance(profile, str) else cfg.get("name", "custom")

    doc_info = session.cmd("document.inspect", {"measure": True})
    bodies = doc_info.get("bodies", [])
    timeline = doc_info.get("timeline", [])
    threads = session.cmd("model.threads").get("threads", [])

    tl_map = {f["id"]: f for f in timeline if isinstance(f, dict) and "id" in f}
    for f in tl_map.values():
        if f.get("type") in ("HoleFeature", "CylinderFeature", "ExtrudeFeature") and not f.get("definition"):
            try:
                insp = session.cmd("timeline.inspect", {"feature": f["id"]})
                if isinstance(insp, dict):
                    f["definition"] = insp.get("definition", {})
            except Exception:
                pass

    all_rules = {
        "min_wall_thickness": {"status": "ok", "findings": []},
        "hole_edge_distance": {"status": "ok", "findings": []},
        "thread_depth": {"status": "ok", "findings": []},
        "printability": {"status": "ok", "findings": []},
        "countersink_clearance": {"status": "ok", "findings": []},
        "horizontal_hole": {"status": "ok", "findings": []},
        "heat_set_insert": {"status": "ok", "findings": []},
        "pocket_corner_radius": {"status": "ok", "findings": []},
        "hole_depth_ratio": {"status": "ok", "findings": []},
        "undercut": {"status": "ok", "findings": []},
    }

    for body in bodies:
        b_rules = _check_body(session, body, tl_map, threads, cfg)
        for r_name, r_data in b_rules.items():
            all_rules[r_name]["findings"].extend(r_data["findings"])
            if r_data["status"] == "fail":
                all_rules[r_name]["status"] = "fail"
            elif r_data["status"] == "warn" and all_rules[r_name]["status"] != "fail":
                all_rules[r_name]["status"] = "warn"

    flat_checks = []
    for r_name, r_data in all_rules.items():
        for f in r_data["findings"]:
            flat_checks.append(dict(f, rule=r_name))

    has_fail = any(r["status"] == "fail" for r in all_rules.values())
    has_warn = any(r["status"] == "warn" for r in all_rules.values())
    verdict = "fail" if has_fail else ("warn" if has_warn else "ok")

    failed_rules = [k for k, v in all_rules.items() if v["status"] == "fail"]
    warn_rules = [k for k, v in all_rules.items() if v["status"] == "warn"]

    if not bodies:
        # nothing to check is no pass
        verdict = "warn"
        summary = f"Design check ({profile_name}): WARN - the part has no solid bodies"
    elif verdict == "ok":
        summary = f"Design check ({profile_name}): OK - all rules passed"
    elif verdict == "fail":
        summary = f"Design check ({profile_name}): FAIL - failed rules: {', '.join(failed_rules)}"
    else:
        summary = f"Design check ({profile_name}): WARN - warnings in: {', '.join(warn_rules)}"

    return {
        "status": verdict,
        "verdict": verdict,
        "profile": profile_name,
        "material": material,
        "material_source": material_source,
        "rules": all_rules,
        "checks": flat_checks,
        "summary": summary,
    }
