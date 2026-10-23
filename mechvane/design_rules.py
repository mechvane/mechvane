"""Design rule checks for parts: wall thickness, hole edge distances, thread engagement
depth, and FDM printability. Operates via the SolidCraft session."""

import math

from . import geometry as g

PROFILES = {
    "fdm_0.4": {
        "name": "FDM 3D-Druck (0.4 mm Düse)",
        "min_wall_thickness": 1.2,        # mm (3 perimeters @ 0.4mm nozzle)
        "hole_edge_distance_factor": 1.5, # >= 1.5 * d from edge to hole center
        "thread_depth_factor": 1.5,       # >= 1.5 * d thread engagement depth
        "min_hole_diameter": 2.0,         # mm
        "max_overhang_angle": 45.0,       # degrees from vertical
    },
    "cnc_alu": {
        "name": "CNC Fräsen (Aluminium)",
        "min_wall_thickness": 1.0,        # mm
        "hole_edge_distance_factor": 1.5, # >= 1.5 * d from edge to hole center
        "thread_depth_factor": 1.5,       # >= 1.5 * d thread engagement depth
        "min_hole_diameter": 1.0,         # mm
        "max_overhang_angle": None,       # no overhang constraint
    },
}

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


def _get_cfg(profile: str | dict) -> dict:
    if isinstance(profile, str):
        if profile not in PROFILES:
            raise ValueError(f"unknown profile {profile!r}, available: {', '.join(PROFILES)}")
        return dict(PROFILES[profile])
    if isinstance(profile, dict):
        base = dict(PROFILES.get("fdm_0.4", {}))
        base.update(profile)
        return base
    raise TypeError(f"profile must be str or dict, got {type(profile).__name__}")


_eval_length = g.eval_length


def _extract_holes(session, body_name: str, faces: list[dict], bbox: dict,
                   timeline_map: dict, threads: list[dict]) -> tuple[list[dict], list[dict]]:
    """Group cylindrical faces sharing an axis and radius into logical holes and external cylinders."""
    cyl_faces = [f for f in faces if f.get("cylinder")]
    groups = g.group_cylindrical_faces(cyl_faces)
    is_hole_list = g.classify_hole_groups(session, body_name, groups, timeline_map, threads, bbox)

    holes = []
    ext_cylinders = []
    for grp, is_hole in zip(groups, is_hole_list):
        r = grp[0]["cylinder"]["radius"]
        d = 2.0 * r
        axis = g.unit(grp[0]["cylinder"]["axis"])
        p0 = grp[0]["cylinder"]["origin"]
        total_area = sum(f["area"] for f in grp)
        length = total_area / (2.0 * math.pi * r) if len(grp) >= 2 else total_area / (math.pi * r)

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
                end_caps = [f for f in faces if f["name"].startswith(f"F{feat_id}:") and not f.get("cylinder")] if feat_id is not None else []
                if end_caps:
                    is_blind = True
        elif feat_id is not None:
            # End cap faces belonging to this feature
            end_caps = [f for f in faces if f["name"].startswith(f"F{feat_id}:") and not f.get("cylinder")]
            if end_caps:
                is_blind = True

        # Thread match
        matched_thread = None
        for th in threads:
            if th.get("internal") and g.dist_to_line(th["axis_point"], p0, axis) < 0.05:
                matched_thread = th
                break

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
            "thread": matched_thread,
        })
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
        hole_edges = [e for e in edges if any(fn in e.get("name", "").split("|") for fn in h["faces"])]
        if hole_edges:
            hole_pts = [e["start"] for e in hole_edges] + [e["end"] for e in hole_edges]
            t_h_min = min(g.dot(pt, axis) for pt in hole_pts)
            t_h_max = max(g.dot(pt, axis) for pt in hole_pts)
        else:
            c_proj = g.dot(c, axis)
            L = h.get("length", 0.0)
            t_h_min = c_proj - L / 2.0
            t_h_max = c_proj + L / 2.0

        side_faces = [f for f in faces if f.get("plane_normal") and abs(g.dot(f["plane_normal"], axis)) < 0.1]
        dist_faces = []
        for sf in side_faces:
            n = sf["plane_normal"]
            v_to_plane = g.sub(sf["point"], c)
            signed_dist = g.dot(v_to_plane, n)
            # Face normal must point outward from the hole, not inward as in interior steps/pockets
            if signed_dist < -1e-4:
                continue

            f_edges = [e for e in edges if sf["name"] in e.get("name", "").split("|")]
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
            ec_edges = [e for e in edges if any(fn in e.get("name", "").split("|") for fn in ec["faces"])]
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
                dist = d_axes - ec["radius"] + r
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
        if min_dist < req_edge - 1e-4:
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
            ec_edges = [e for e in edges if any(fn in e.get("name", "").split("|") for fn in ec["faces"])]
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
                                f"({thread_factor:.1f} × d for {thread_spec})"),
                    "value": round(act_depth, 4),
                    "threshold": round(req_depth, 4),
                })
            else:
                rules["thread_depth"]["findings"].append({
                    "status": "ok",
                    "location": {"point": h["representative_point"], "face": h["faces"][0]},
                    "message": (f"Thread engagement depth {act_depth:.1f} mm >= {req_depth:.1f} mm "
                                f"({thread_factor:.1f} × d for {thread_spec})"),
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
        z_min = bbox["min"][2]
        sin_limit = math.sin(math.radians(max_oh))
        for f in faces:
            n = f.get("plane_normal")
            if not n or n[2] >= -0.01:
                continue
            # Build plate check
            if n[2] <= -0.99 and abs(f["centroid"][2] - z_min) < 0.05:
                continue

            # Downward face above print bed
            if n[2] < -sin_limit:
                rules["printability"]["status"] = "fail"
                rules["printability"]["findings"].append({
                    "status": "fail",
                    "location": {"point": f["centroid"], "face": f["name"]},
                    "message": (f"Unsupported overhang on face {f['name']} (normal {n}, centroid {f['centroid']}) "
                                f"exceeds {max_oh:.0f}° limit"),
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

    return rules


def check(session_or_doc, profile: str | dict = "fdm_0.4") -> dict:
    """Check a part against design rules using the open SolidCraft session."""
    session = getattr(session_or_doc, "session", session_or_doc)
    cfg = _get_cfg(profile)
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

    if verdict == "ok":
        summary = f"Design check ({profile_name}): OK - all rules passed"
    elif verdict == "fail":
        summary = f"Design check ({profile_name}): FAIL - failed rules: {', '.join(failed_rules)}"
    else:
        summary = f"Design check ({profile_name}): WARN - warnings in: {', '.join(warn_rules)}"

    return {
        "status": verdict,
        "verdict": verdict,
        "profile": profile_name,
        "rules": all_rules,
        "checks": flat_checks,
        "summary": summary,
    }
