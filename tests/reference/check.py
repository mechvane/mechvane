#!/usr/bin/env python3
"""Reference part corpus: rebuilds each <part>.build.json with solidcraft-cli, walks its
parameters and compares the results with values computed by hand below.

Usage: python3 tests/reference/check.py [part ...]   (needs solidcraft-cli on PATH)
Exit code 0 when every check passes, 1 otherwise."""

import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
REL = 2e-4  # volume tolerance: SolidCraft measures a tessellation (seen: up to 2e-5)
ABS = 2e-3  # mm, for positions, centres of mass and bounding boxes


def inspect():
    return {"command": "document.inspect", "params": {"measure": True}}


def change(**params):
    return [{"command": "parameters.change", "params": {"name": k, "expression": v}} for k, v in params.items()]


def rr_area(a, b, r):
    """Area of an a x b rectangle with corner radius r."""
    return a * b - (4 - math.pi) * r * r


# --- flange 60 x 60 x 8, 4 x 6.6 on bolt circle 45, 1 mm top chamfer -----------------------

def flange_volume(A=60, T=8, n=4, dh=6.6, c=1):
    chamfer = 4 * A * c * c / 2 - 4 * c ** 3 / 3  # four mitred prisms, corner overlaps counted once
    return A * A * T - chamfer - n * math.pi * (dh / 2) ** 2 * T


def flange():
    walk = [inspect()] + change(n="6") + [inspect()] + change(T="10 mm") + [inspect()] \
        + change(n="4", T="8 mm") + [inspect()]
    return walk, [
        ("default", 0, "volume", flange_volume()),
        ("default", 0, "bbox", [[-30, -30, 0], [30, 30, 8]]),
        ("n=6", 2, "volume", flange_volume(n=6)),
        ("n=6, T=10", 4, "volume", flange_volume(n=6, T=10)),
        ("n=6, T=10", 4, "bbox", [[-30, -30, 0], [30, 30, 10]]),
        ("back", 7, "volume", flange_volume()),
    ]


# --- 3D-print enclosure 80 x 50 x 30, R5, wall 2, open top, 4 ring bosses ---------------------

def enclosure(L=80, W=50, H=30, wall=2, r=5, hb=20, do=7, di=3):
    outer = rr_area(L, W, r) * H
    inner = rr_area(L - 2 * wall, W - 2 * wall, r - wall) * (H - wall)
    boss = 4 * math.pi * ((do / 2) ** 2 - (di / 2) ** 2) * (hb - wall)
    v = outer - inner + boss
    zc = (outer * H / 2 - inner * (wall + (H - wall) / 2) + boss * (wall + (hb - wall) / 2)) / v
    return v, zc


def gehaeuse():
    walk = [inspect()] + change(L="120 mm") + [inspect()] + change(hb="28 mm", wall="3 mm") + [inspect()] \
        + change(L="80 mm", hb="20 mm", wall="2 mm") + [inspect()]
    checks = []
    for label, at, kw in (("default", 0, {}), ("L=120", 2, {"L": 120}),
                          ("L=120, hb=28, wall=3", 5, {"L": 120, "hb": 28, "wall": 3}), ("back", 9, {})):
        v, zc = enclosure(**kw)
        checks += [(label, at, "volume", v), (label, at, "com_z", zc)]
    return walk, checks


# --- sheet metal bracket: base 60 x 40, flange 30 (outer), t 2, R 2, K 0.44, 2 x M6 ----------

def bracket(B=60, La=40, Lb=30, t=2, R=2, K=0.44, dh=6.6, holes=2):
    ba = math.pi / 2 * (R + K * t)  # bend allowance
    flat = (La - R - t) + (Lb - R - t) + ba
    bend = math.pi / 4 * ((R + t) ** 2 - R ** 2) * B
    v = (La - R - t) * B * t + (Lb - R - t) * B * t + bend - holes * math.pi * (dh / 2) ** 2 * t
    return v, ba, flat


def blechwinkel():
    walk = [inspect(), {"command": "sheet.flat_pattern", "params": {}}] + change(Lb="50 mm") + [inspect()] \
        + change(Lb="30 mm") + [inspect()]
    v, ba, flat = bracket()
    return walk, [
        ("default", 0, "volume", v),
        ("default", 0, "bbox", [[-30, -20, 0], [30, 20, 30]]),
        ("bend allowance", 1, "allowance", ba),
        ("flat length", 1, "flat_length", flat),
        ("Lb=50", 3, "volume", bracket(Lb=50)[0]),
        ("back", 5, "volume", v),
    ]


# --- hinge: base plate grounded, lid on a revolute joint along X through (0, 0, 3) -------------

def lid_com(deg):
    a = math.radians(deg)
    y, z = 20, -1.5  # lid centre of mass relative to the hinge axis at 0 deg
    return [0, y * math.cos(a) - z * math.sin(a), 3 + y * math.sin(a) + z * math.cos(a)]


def scharnier():
    props = {"command": "occurrence.properties", "params": {"occurrence": "Lid:1"}}
    walk = [props]
    for deg in (45, 90, 0):
        walk += [{"command": "joint.drive", "params": {"joint": "Hinge", "value": deg}}, props]
    walk += [{"command": "contact.create", "params": {"occurrences": ["Base:1", "Lid:1"], "name": "Plates"}},
             {"command": "contact.enable_sets", "params": {}},
             {"command": "joint.drive", "params": {"joint": "Hinge", "value": 270}},
             {"command": "joint.drive", "params": {"joint": "Hinge", "value": 210}},
             {"command": "inspect.interference", "params": {}}]
    return walk, [
        ("0 deg", 0, "occ_com", lid_com(0)),
        ("45 deg", 2, "occ_com", lid_com(45)),
        ("90 deg", 4, "occ_com", lid_com(90)),
        ("back to 0", 6, "occ_com", lid_com(0)),
        ("opening stops on contact at 180 deg", 9, "joint_value", (180.0, 0.05)),
        # the lid lies on the base at 180 deg: a drive further must not move it into the base
        ("drive past contact moves nothing", 10, "moved", False),
        # the stop lands up to ~0.01 deg past contact: a sliver of overlap (seen 6.8 mm3) is fine
        ("overlap at the contact stop below 10 mm3", 11, "interference_volume", (0.0, 10.0)),
    ]


# --- welle: stepped shaft 3 diameters, groove, chamfer --------------------------------------

def shaft_volume(d1=16, L1=20, d2=24, L2=30, d3=18, L3=20, bg=1.5, tg=0.8, c=1.0):
    """Volume of turned shaft: sum of 3 cylinders minus retaining ring groove minus end chamfer cone frustum.

    1. Sum of cylinders:
       V_cyl = sum(pi * (di/2)^2 * Li) for i in {1, 2, 3}
    2. Retaining ring groove on cylinder 1 (outer radius r1 = d1/2, depth tg, width bg):
       Groove is an annular cut from r_in = r1 - tg to r_out = r1:
       V_groove = pi * (r1^2 - (r1 - tg)^2) * bg
    3. 45-degree chamfer at the end x = 0 (distance c along axis and radius):
       The chamfer removes an annular wedge around the cylinder face.
       By Pappus's centroid theorem, a right triangle of legs c, c has area A = c^2 / 2
       and radial centroid r_bar = r1 - c/3:
       V_chamfer = 2 * pi * r_bar * A = pi * c^2 * (r1 - c/3).
       Equivalently: cylinder pi*r1^2*c minus cone frustum pi/3*c*(r1^2 + r1*(r1-c) + (r1-c)^2).
    """
    v_cyl = math.pi * (d1 / 2) ** 2 * L1 + math.pi * (d2 / 2) ** 2 * L2 + math.pi * (d3 / 2) ** 2 * L3
    r1 = d1 / 2
    v_groove = math.pi * (r1 ** 2 - (r1 - tg) ** 2) * bg
    v_chamfer = math.pi * c ** 2 * (r1 - c / 3)
    return v_cyl - v_groove - v_chamfer


def welle():
    walk = [inspect()] \
        + change(d1="18 mm", L1="25 mm") + [inspect()] \
        + change(d2="28 mm", L2="35 mm") + [inspect()] \
        + change(d3="20 mm", L3="25 mm") + [inspect()] \
        + change(d1="16 mm", L1="20 mm", d2="24 mm", L2="30 mm", d3="18 mm", L3="20 mm") + [inspect()]
    return walk, [
        ("default", 0, "volume", shaft_volume()),
        ("default", 0, "bbox_len", 70.0),
        ("default", 0, "bbox", [[0, -12, -12], [70, 12, 12]]),
        ("d1=18, L1=25", 3, "volume", shaft_volume(d1=18, L1=25)),
        ("d1=18, L1=25", 3, "bbox_len", 75.0),
        ("d1=18, L1=25", 3, "bbox", [[0, -12, -12], [75, 12, 12]]),
        ("d2=28, L2=35", 6, "volume", shaft_volume(d1=18, L1=25, d2=28, L2=35)),
        ("d2=28, L2=35", 6, "bbox_len", 80.0),
        ("d2=28, L2=35", 6, "bbox", [[0, -14, -14], [80, 14, 14]]),
        ("d3=20, L3=25", 9, "volume", shaft_volume(d1=18, L1=25, d2=28, L2=35, d3=20, L3=25)),
        ("d3=20, L3=25", 9, "bbox_len", 85.0),
        ("d3=20, L3=25", 9, "bbox", [[0, -14, -14], [85, 14, 14]]),
        ("back", 16, "volume", shaft_volume()),
        ("back", 16, "bbox_len", 70.0),
        ("back", 16, "bbox", [[0, -12, -12], [70, 12, 12]]),
    ]


# --- rohrhalter: swept clamp arch with 2 counterbore mounting holes --------------------------

def rohrhalter_volume(R=40, Lf=25, t=4, W=24, dh=6.6, dcb=11, tcb=2):
    """Volume of pipe bracket: swept strap profile along line-arc-line path minus 2 counterbore holes.

    1. Swept strap body:
       Path consists of two straight flanges of length Lf and a semicircle of radius R:
       L_path = 2 * Lf + pi * R.
       Cross-sectional profile is a rectangle of thickness t and width W: A = W * t.
       By Pappus's centroid theorem, the swept volume along a planar centerline curve is:
       V_sweep = L_path * A = (2 * Lf + pi * R) * W * t.
    2. Counterbore mounting holes:
       Each hole consists of two coaxial cylinders:
       - Counterbore cavity: diameter dcb, depth tcb -> V_cb = pi * (dcb / 2)^2 * tcb
       - Through hole drill: diameter dh, depth (t - tcb) -> V_drill = pi * (dh / 2)^2 * (t - tcb)
       V_hole = V_cb + V_drill.
    Total volume: V = V_sweep - 2 * V_hole.
    """
    v_sweep = (2 * Lf + math.pi * R) * W * t
    v_hole = math.pi * (dcb / 2) ** 2 * tcb + math.pi * (dh / 2) ** 2 * (t - tcb)
    return v_sweep - 2 * v_hole


def rohrhalter():
    walk = [inspect()] \
        + change(R="50 mm") + [inspect()] \
        + change(W="30 mm", Lf="30 mm") + [inspect()] \
        + change(R="40 mm", W="24 mm", Lf="25 mm") + [inspect()]
    return walk, [
        ("default", 0, "volume", rohrhalter_volume()),
        ("default", 0, "bbox_len", 2 * (40 + 25)),
        ("R=50", 2, "volume", rohrhalter_volume(R=50)),
        ("R=50", 2, "bbox_len", 2 * (50 + 25)),
        ("R=50, W=30, Lf=30", 5, "volume", rohrhalter_volume(R=50, W=30, Lf=30)),
        ("R=50, W=30, Lf=30", 5, "bbox_len", 2 * (50 + 30)),
        ("back", 9, "volume", rohrhalter_volume()),
        ("back", 9, "bbox_len", 2 * (40 + 25)),
    ]


# --- rippenplatte: plate with patterned ribs, center plane mirror, internal fillets ----------

def rippenplatte_volume(Lh=60, W=60, T=10, br=8, Lr=50, hr=15, n=2, r=2):
    """Volume of ribbed plate: base plate + 2*n ribs + internal fillets at rib-plate transitions.

    1. Base plate:
       Length is 2 * Lh (mirrored across YZ plane), width W, thickness T:
       V_base = 2 * Lh * W * T.
    2. Ribs unfilleted (exact):
       Each rib is a rectangular prism of br * Lr * hr.
       With n ribs per half, total ribs across the mirrored plate is 2 * n:
       V_ribs = 2 * n * br * Lr * hr.
       Unfilleted volume: V_unfilleted = V_base + V_ribs.
    3. Fillet weld transition (internal fillet quadrant):
       At the base of each rib, on both left and right sides along length Lr, an internal fillet
       fills the 90-degree corner with material.
       Cross-sectional area of corner square r * r minus quarter circle pi * r^2 / 4:
       A_fillet = r^2 * (1 - pi / 4).
       Each rib has 2 such fillet lines of length Lr:
       V_rib_fillets = 2 * A_fillet * Lr = 2 * r^2 * (1 - pi / 4) * Lr.
       For 2 * n ribs total:
       Delta_V_fillets = 4 * n * r^2 * (1 - pi / 4) * Lr.
    Total volume: V = V_unfilleted + Delta_V_fillets.
    """
    v_base = 2 * Lh * W * T
    v_ribs = 2 * n * br * Lr * hr
    v_fillets = 4 * n * r ** 2 * (1 - math.pi / 4) * Lr
    return v_base + v_ribs + v_fillets


def rippenplatte():
    walk = [inspect()] \
        + change(n="3") + [inspect()] \
        + change(hr="20 mm") + [inspect()] \
        + change(n="2", hr="15 mm") + [inspect()]
    return walk, [
        ("default", 0, "volume", rippenplatte_volume()),
        ("default", 0, "bbox", [[-60, 0, 0], [60, 60, 25]]),
        ("n=3", 2, "volume", rippenplatte_volume(n=3)),
        ("n=3", 2, "bbox", [[-60, 0, 0], [60, 60, 25]]),
        ("n=3, hr=20", 4, "volume", rippenplatte_volume(n=3, hr=20)),
        ("n=3, hr=20", 4, "bbox", [[-60, 0, 0], [60, 60, 30]]),
        ("back", 7, "volume", rippenplatte_volume()),
        ("back", 7, "bbox", [[-60, 0, 0], [60, 60, 25]]),
    ]


PARTS = {
    "flansch": flange,
    "gehaeuse": gehaeuse,
    "blechwinkel": blechwinkel,
    "scharnier": scharnier,
    "welle": welle,
    "rohrhalter": rohrhalter,
    "rippenplatte": rippenplatte,
}


def value_of(kind, result):
    if kind in ("volume", "com_z", "bbox", "bbox_len"):
        body = result["bodies"][0]
        return {"volume": body["volume_mm3"], "com_z": body["center_of_mass"][2],
                "bbox": [body["bbox"]["min"], body["bbox"]["max"]],
                "bbox_len": body["bbox"]["max"][0] - body["bbox"]["min"][0]}[kind]
    if kind == "allowance":
        return result["bends"][0]["allowance"]
    if kind == "flat_length":
        return max(result["flat_size_mm"])
    if kind == "occ_com":
        return result["bodies"][0]["center_of_mass"]
    if kind == "joint_value":
        return result["values"][0]["value"]
    if kind == "moved":
        return result["moved"]
    if kind == "interference_volume":
        return sum(i["volume_mm3"] for i in result["interferences"])
    raise KeyError(kind)


def matches(kind, actual, expected):
    if kind == "volume":
        return abs(actual - expected) <= REL * abs(expected)
    if kind == "joint_value":
        return abs(actual - expected[0]) <= expected[1]
    if kind == "interference_volume":
        return expected[0] <= actual <= expected[1]
    if kind == "moved":
        return actual == expected
    flat = lambda x: [v for row in x for v in row] if isinstance(x[0], list) else x
    if isinstance(expected, (int, float)):
        return abs(actual - expected) <= ABS
    return all(abs(a - e) <= ABS for a, e in zip(flat(actual), flat(expected)))


def run(part):
    cli = os.environ.get("SOLIDCRAFT_CLI", "solidcraft-cli")
    build = json.loads((HERE / f"{part}.build.json").read_text(encoding="utf-8"))["commands"]
    walk, checks = PARTS[part]()
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "script.json"
        script.write_text(json.dumps({"commands": build + walk}), encoding="utf-8")
        done = subprocess.run([cli, "run", str(script), "--results", "--quiet"],
                              capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        print(f"{part}: BUILD FAILED\n{done.stderr[-2000:]}")
        return False
    results = json.loads(done.stdout)[len(build):]
    ok = True
    for label, at, kind, expected in checks:
        actual = value_of(kind, results[at])
        good = matches(kind, actual, expected)
        ok &= good
        print(f"{part:12} {'ok  ' if good else 'FAIL'} {label}: {kind} = {fmt(actual)} (expected {fmt(expected)})")
    return ok


def fmt(x):
    if isinstance(x, float):
        return f"{x:.4f}"
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(fmt(v) for v in x) + "]"
    return str(x)


if __name__ == "__main__":
    parts = sys.argv[1:] or list(PARTS)
    results = [run(p) for p in parts]
    sys.exit(0 if all(results) else 1)
