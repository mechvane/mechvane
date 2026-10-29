"""Small vector helpers. SolidCraft transforms are 4x4, row-vector convention:
world = [x, y, z, 1] · M, translation in the last row."""

import math
import warnings

IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def add(a, b):
    return [a[i] + b[i] for i in range(3)]


def scale(a, s):
    return [x * s for x in a]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return [x / n for x in a] if n else a


def apply_point(m, p):
    return [sum(p[j] * m[j][i] for j in range(3)) + m[3][i] for i in range(3)]


def apply_dir(m, d):
    return [sum(d[j] * m[j][i] for j in range(3)) for i in range(3)]


def mat_mul(parent, child):
    """Combined transform (local -> child -> parent) in SolidCraft's 4x4 layout."""
    return [[sum(parent[k][r] * child[c][k] for k in range(4)) for r in range(4)] for c in range(4)]


def invert_rigid(m):
    """Inverse of a rotation + translation (row-vector convention)."""
    r = [[m[j][i] for j in range(3)] for i in range(3)]  # transpose of the rotation
    t = m[3][:3]
    ti = [-sum(t[j] * r[j][i] for j in range(3)) for i in range(3)]
    return [r[0] + [0.0], r[1] + [0.0], r[2] + [0.0], ti + [1.0]]


def same_mat(a, b, tol=1e-6):
    return all(abs(a[c][r] - b[c][r]) < tol for c in range(4) for r in range(4))


def move_params(m):
    """occurrence.move parameters that set an occurrence's local transform to `m`."""
    t = m[3][:3]
    cos_a = max(-1.0, min(1.0, (m[0][0] + m[1][1] + m[2][2] - 1.0) / 2.0))
    angle = math.acos(cos_a)
    out = {"translate": t, "space": "local", "base_transform": IDENTITY}
    if abs(angle) < 1e-12:
        return out
    if abs(math.pi - angle) < 1e-6:
        k = [math.sqrt(max(0.0, (m[i][i] + 1.0) / 2.0)) for i in range(3)]
        i = max(range(3), key=lambda i: k[i])
        for j in range(3):
            if j != i and m[i][j] + m[j][i] < 0:
                k[j] = -k[j]
        axis = k
    else:
        axis = [m[1][2] - m[2][1], m[2][0] - m[0][2], m[0][1] - m[1][0]]
    return dict(out, axis=axis, angle=angle)


def dist_to_line(p, origin, axis):
    a = unit(axis)
    d = sub(p, origin)
    return norm(sub(d, scale(a, dot(d, a))))


def parallel(a, b, tol=1e-6):
    return norm(cross(unit(a), unit(b))) < tol


def eval_length(session, val, default=0.0):
    """Evaluate an expression or parameter into a float length in mm."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val_str = val.strip()
        if session:
            try:
                res = session.cmd("expr.evaluate", {"expression": val_str})
                if isinstance(res, dict) and res.get("ok") and "value" in res:
                    return float(res["value"])
            except Exception:
                pass
        try:
            return float(val_str)
        except ValueError:
            pass
    return default


_eval_length = eval_length


def group_cylindrical_faces(cyl_faces: list[dict]) -> list[list[dict]]:
    """Group cylindrical faces sharing an axis line and radius into logical cylinder groups."""
    groups = []
    used = set()
    for i, f1 in enumerate(cyl_faces):
        if i in used:
            continue
        c1 = f1["cylinder"]
        grp = [f1]
        used.add(i)
        for j, f2 in enumerate(cyl_faces):
            if j in used:
                continue
            c2 = f2["cylinder"]
            if (parallel(c1["axis"], c2["axis"], tol=1e-3)
                    and dist_to_line(c1["origin"], c2["origin"], c2["axis"]) < 0.05
                    and abs(c1["radius"] - c2["radius"]) < 0.05):
                grp.append(f2)
                used.add(j)
        groups.append(grp)
    return groups


def classify_hole_groups(session, body_name: str, groups: list[list[dict]],
                         timeline_map: dict, threads: list[dict] = None,
                         bbox: dict = None, probe: bool = True) -> list[bool]:
    """Determine for each cylindrical face group whether it is an internal hole (material outside,
    surface normal pointing to axis) versus an external boss / pin / standoff wall (material inside,
    surface normal pointing away from axis)."""
    is_hole = [False] * len(groups)
    ambiguous = []

    for idx, grp in enumerate(groups):
        feat_id = None
        for f in grp:
            parts = f["name"].split(":")
            if parts[0].startswith("F") and parts[0][1:].isdigit():
                feat_id = int(parts[0][1:])
                break
        feat_info = timeline_map.get(feat_id, {})

        # Ignore edge fillets, chamfers and blend faces
        if feat_info.get("type") in ("FilletFeature", "ChamferFeature") or any(":blend:" in f["name"] for f in grp):
            is_hole[idx] = False
            continue

        # Features with explicit hole semantics
        op = feat_info.get("definition", {}).get("operation") or feat_info.get("operation")
        if feat_info.get("type") == "HoleFeature" or op == "cut":
            is_hole[idx] = True
            continue
        if any(":bore:" in f["name"] or ":cut:" in f["name"] for f in grp):
            is_hole[idx] = True
            continue
        if any("hole" in f.get("name", "").lower() for f in grp):
            is_hole[idx] = True
            continue

        p0 = grp[0]["cylinder"]["origin"]
        axis = unit(grp[0]["cylinder"]["axis"])
        if threads and any(th.get("internal") for th in threads if dist_to_line(th["axis_point"], p0, axis) < 0.05):
            is_hole[idx] = True
            continue

        # Check if face normal is directly provided by SolidCraft (normal pointing to axis = hole)
        face_normal = grp[0].get("normal") or grp[0].get("plane_normal")
        if face_normal:
            pt_surf = grp[0].get("point") or grp[0].get("centroid")
            if pt_surf:
                t = dot(sub(pt_surf, p0), axis)
                p_axis = add(p0, scale(axis, t))
                rad_vec = sub(pt_surf, p_axis)
                if dot(face_normal, rad_vec) < -1e-4:
                    is_hole[idx] = True
                    continue
                elif dot(face_normal, rad_vec) > 1e-4:
                    is_hole[idx] = False
                    continue

        ambiguous.append((idx, feat_info, op))

    handled = set()
    # Probe cuts need an editable body, so only part sessions can probe (an assembly
    # session reports "no body to cut" for every probe).
    if probe and ambiguous and session and body_name:
        cp = None
        try:
            probe_cmds = []
            probe_indices = []
            for idx, feat_info, op in ambiguous:
                grp = groups[idx]
                c = grp[0]["cylinder"]
                r = c["radius"]
                axis = unit(c["axis"])
                p0 = c["origin"]
                pt_surf = grp[0].get("point")
                if not pt_surf:
                    continue
                t = dot(sub(pt_surf, p0), axis)
                p_axis = add(p0, scale(axis, t))
                rad_vec = sub(pt_surf, p_axis)
                d_rad = norm(rad_vec)
                if d_rad < 1e-4:
                    continue
                rad_u = scale(rad_vec, 1.0 / d_rad)
                # Probe point just outside the cylinder radius (material side check).
                # If there is material outside the cylinder (cut changes body), it is an internal hole.
                # If there is no material outside (air, cut changes nothing), it is an external boss/pin.
                delta = min(0.1, 0.05 * r)
                probe_pt = add(pt_surf, scale(rad_u, delta))
                probe_r = min(0.04, 0.4 * delta)
                bname = f"_probe_cut_{idx}"
                probe_cmds.append({
                    "command": "solid.sphere",
                    "params": {"center": probe_pt, "radius": probe_r, "operation": "cut",
                               "name": bname}
                })
                probe_indices.append(idx)

            if probe_cmds:
                cp = session.cmd("edit.checkpoint", {})
                try:
                    # One probe at a time: a cut that misses the body fails, which means air
                    # outside the cylinder (boss), and must not hide the other probes' results.
                    for idx, cmd in zip(probe_indices, probe_cmds):
                        try:
                            cmd_res = session.cmd(cmd["command"], cmd["params"])
                        except Exception as e:
                            if "no body to cut" not in str(e):
                                raise
                            is_hole[idx] = False
                            handled.add(idx)
                        else:
                            # Probes only run in part sessions, so a cut that changes nothing hit air.
                            changed = cmd_res.get("changed_bodies", []) if isinstance(cmd_res, dict) else []
                            is_hole[idx] = bool(changed)
                            handled.add(idx)
                finally:
                    if cp and isinstance(cp, dict) and "checkpoint" in cp:
                        session.cmd("edit.restore_checkpoint", {"checkpoint": cp["checkpoint"]})
        except Exception as e:
            warnings.warn(f"classify_hole_groups: probe failed ({e}); falling back to geometric heuristics",
                          UserWarning, stacklevel=2)

    # Fallback for any group not handled by probe
    for idx, feat_info, op in ambiguous:
        if idx not in handled:
            grp = groups[idx]
            c = grp[0]["cylinder"]
            r = c["radius"]
            axis = unit(c["axis"])
            p0 = c["origin"]

            larger_coaxial = False
            smaller_coaxial = False
            for other_idx, other_grp in enumerate(groups):
                if other_idx == idx:
                    continue
                other_c = other_grp[0]["cylinder"]
                if (parallel(axis, other_c["axis"], tol=1e-3)
                        and dist_to_line(p0, other_c["origin"], other_c["axis"]) < 0.05):
                    if other_c["radius"] > r + 1e-3:
                        larger_coaxial = True
                    elif other_c["radius"] < r - 1e-3:
                        smaller_coaxial = True

            if larger_coaxial:
                # Inside another cylinder on the same axis (e.g. standoff bore inside standoff boss)
                is_hole[idx] = True
            elif smaller_coaxial:
                # Outside another cylinder on the same axis (e.g. standoff boss outside standoff bore)
                is_hole[idx] = False
            elif op in ("join", "new_body", "new"):
                # Attached pin / boss without inner bore
                is_hole[idx] = False
            elif bbox:
                min_b, max_b = bbox["min"], bbox["max"]
                if (min_b[0] + r < p0[0] < max_b[0] - r and min_b[1] + r < p0[1] < max_b[1] - r):
                    is_hole[idx] = True

    return is_hole


def edge_touches(edge_name: str, face_name: str) -> bool:
    """Whether an edge named "<face A>|<face B>" borders face_name. Face names can themselves contain "|"
    (a chamfer or fillet between two faces: "F2:blend:F1:+x|F1:+z"), so splitting the edge name at "|"
    is not enough."""
    return (edge_name == face_name or edge_name.startswith(face_name + "|") or edge_name.endswith("|" + face_name)
            or face_name in edge_name.split("|"))
