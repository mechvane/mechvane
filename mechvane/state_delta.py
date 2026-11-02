"""State delta and warnings for modelling steps.

Computes snapshots of part geometry (bounding box, centre of mass, volume, mass, body count)
and compares before/after states to produce concise delta reports and warnings for modelling agents.
"""

from __future__ import annotations

import math
from typing import Any


def _bbox_equal(b1: dict | None, b2: dict | None, tol: float = 1e-3) -> bool:
    """Return True if two bounding boxes are equal within tolerance."""
    if b1 is None and b2 is None:
        return True
    if b1 is None or b2 is None:
        return False
    min1, max1 = b1.get("min"), b1.get("max")
    min2, max2 = b2.get("min"), b2.get("max")
    if min1 is None or max1 is None or min2 is None or max2 is None:
        return min1 == min2 and max1 == max2
    return all(abs(min1[i] - min2[i]) <= tol and abs(max1[i] - max2[i]) <= tol for i in range(3))


def snapshot(session: Any) -> dict:
    """Take a geometric snapshot of the part in session.

    Returns a dict with:
      - bodies: number of bodies (int)
      - volume_mm3: total volume in mm³ (float, rounded)
      - bbox: union bounding box {"min": [x, y, z], "max": [x, y, z]} or None
      - center_of_mass: volume-weighted centre of mass [x, y, z] or None
      - mass_g: total mass in g if a material is assigned, else None
    """
    s = getattr(session, "session", session)
    bodies = []
    meas = None
    try:
        meas = s.tool("measure", {})
        if isinstance(meas, dict):
            bodies = meas.get("bodies", [])
    except Exception:
        pass

    if not bodies:
        try:
            insp = s.cmd("document.inspect", {"measure": True})
            if isinstance(insp, dict):
                bodies = insp.get("bodies", [])
        except Exception:
            pass

    if not bodies:
        return {
            "bodies": 0,
            "volume_mm3": 0.0,
            "bbox": None,
            "center_of_mass": None,
            "mass_g": None,
        }

    total_vol = 0.0
    for b in bodies:
        total_vol += max(0.0, float(b.get("volume_mm3", 0.0)))
    total_vol = round(total_vol, 2)

    # Union bounding box across all bodies
    valid_bboxes = [b["bbox"] for b in bodies if b.get("bbox") and "min" in b["bbox"] and "max" in b["bbox"]]
    if valid_bboxes:
        min_pt = [round(min(b["min"][i] for b in valid_bboxes), 3) for i in range(3)]
        max_pt = [round(max(b["max"][i] for b in valid_bboxes), 3) for i in range(3)]
        bbox = {"min": min_pt, "max": max_pt}
    else:
        bbox = None

    # Centre of mass (weighted average by body volume)
    if total_vol > 1e-9:
        com_accum = [0.0, 0.0, 0.0]
        for b in bodies:
            v = max(0.0, float(b.get("volume_mm3", 0.0)))
            c = b.get("center_of_mass")
            if c:
                for i in range(3):
                    com_accum[i] += v * c[i]
        com = [round(com_accum[i] / total_vol, 3) for i in range(3)]
    else:
        valid_coms = [b["center_of_mass"] for b in bodies if b.get("center_of_mass")]
        if valid_coms:
            com = [round(sum(c[i] for c in valid_coms) / len(valid_coms), 3) for i in range(3)]
        else:
            com = None

    # Check if a non-default material is assigned
    has_material = any(b.get("material") not in (None, "", "Default") for b in bodies)
    if not has_material and hasattr(session, "metadata"):
        try:
            meta = session.metadata()
            if isinstance(meta, dict) and meta.get("rules", {}).get("material"):
                has_material = True
        except Exception:
            pass

    mass_g = None
    if has_material:
        total_mass = 0.0
        if meas and isinstance(meas.get("total"), dict) and meas["total"].get("mass_g") is not None:
            total_mass = float(meas["total"]["mass_g"])
        else:
            for b in bodies:
                total_mass += float(b.get("mass_g", 0.0))
        mass_g = round(total_mass, 2)

    res: dict[str, Any] = {
        "bodies": len(bodies),
        "volume_mm3": total_vol,
        "bbox": bbox,
        "center_of_mass": com,
    }
    if mass_g is not None:
        res["mass_g"] = mass_g
    return res


def diff(before: dict | None, after: dict | None) -> dict:
    """Compare before and after snapshots, returning a concise delta dict with warnings.

    Produces warnings when:
      - A feature had no effect (volume and bounding box unchanged).
      - The part split into multiple bodies (body count rises above 1).
      - A large jump occurred (volume changes by > 50% or bbox grows by > factor 2 in an axis).
    """
    if before is None:
        before = {
            "bodies": 0,
            "volume_mm3": 0.0,
            "bbox": None,
            "center_of_mass": None,
            "mass_g": None,
        }
    if after is None:
        after = {
            "bodies": 0,
            "volume_mm3": 0.0,
            "bbox": None,
            "center_of_mass": None,
            "mass_g": None,
        }

    warnings: list[str] = []

    vol_before = float(before.get("volume_mm3", 0.0))
    vol_after = float(after.get("volume_mm3", 0.0))
    vol_diff = round(vol_after - vol_before, 2)

    bodies_before = int(before.get("bodies", 0))
    bodies_after = int(after.get("bodies", 0))
    bodies_diff = bodies_after - bodies_before

    bbox_before = before.get("bbox")
    bbox_after = after.get("bbox")

    # 1. Feature had no effect: volume and bounding box unchanged
    if vol_before > 0 and bodies_before > 0:
        if abs(vol_diff) < 1e-4 and _bbox_equal(bbox_before, bbox_after) and bodies_after == bodies_before:
            warnings.append("Feature had no effect: volume and bounding box unchanged.")

    # 2. Part split into multiple bodies (body count rises above 1)
    if bodies_after > 1 and bodies_after > bodies_before:
        warnings.append(f"Part split into multiple bodies ({bodies_after} bodies).")

    # 3. Large jump: volume changes by > 50% or bbox grows by > factor 2 in an axis
    if vol_before > 1e-4:
        vol_pct = (abs(vol_after - vol_before) / vol_before) * 100.0
        if vol_pct > 50.0:
            warnings.append(
                f"Large change: volume changed by {vol_pct:.0f}% ({vol_before:.1f} -> {vol_after:.1f} mm³)."
            )

    if bbox_before and bbox_after:
        axis_names = ("X", "Y", "Z")
        for i in range(3):
            dim_before = bbox_before["max"][i] - bbox_before["min"][i]
            dim_after = bbox_after["max"][i] - bbox_after["min"][i]
            if dim_before > 1e-4 and dim_after > 2.0 * dim_before:
                warnings.append(
                    f"Large change: bounding box grew by more than factor 2 along {axis_names[i]} axis "
                    f"({round(dim_before, 2)} -> {round(dim_after, 2)} mm)."
                )

    # Compact reply: values after the step, changes, and "before" only where it moved.
    out: dict[str, Any] = {"bodies": bodies_after, "volume_mm3": round(vol_after, 2)}
    if vol_diff:
        out["volume_change_mm3"] = vol_diff
    if bodies_diff:
        out["bodies_change"] = bodies_diff
    out["bbox"] = bbox_after
    if bbox_before is not None and not _bbox_equal(bbox_before, bbox_after):
        out["bbox_before"] = bbox_before
    out["center_of_mass"] = after.get("center_of_mass")
    com_before = before.get("center_of_mass")
    if com_before is not None and com_before != out["center_of_mass"]:
        out["center_of_mass_before"] = com_before
    if after.get("mass_g") is not None:
        out["mass_g"] = round(float(after["mass_g"]), 2)
        if before.get("mass_g") is not None:
            out["mass_change_g"] = round(float(after["mass_g"]) - float(before["mass_g"]), 2)
    if warnings:
        out["warnings"] = warnings
    return out
