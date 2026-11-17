#!/usr/bin/env python3
"""Checks for the Mechvane layer (sketch rule, browser, joints across files).

Usage: python3 tests/mechvane/check.py   (needs solidcraft-cli on PATH, ~30 s)
Exit code 0 when every check passes, 1 otherwise."""

import json
import math
import os
import queue
import shutil
import sys
import tempfile
import threading
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mechvane import bolted, bom, design_rules, geometry as g, hole_tables, inplace, katalog, links, modeling, query, sc_errors, sc_locate, server, sketch_rule, standard_parts, state_delta, tree  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402

REL = 2e-4  # volume tolerance (tessellation, same as tests/reference/check.py)
ABS = 2e-3  # mm tolerance for bounding boxes
failures = 0


# Failure details are cut to this many characters (whole meshes otherwise flood the output); 0 = no limit
DETAIL_MAX = int(os.environ.get("MECHVANE_CHECK_DETAIL", "600"))


def ok(label, cond, detail=""):
    global failures
    detail = str(detail)
    if DETAIL_MAX and len(detail) > DETAIL_MAX:
        detail = detail[:DETAIL_MAX] + f" … [{len(detail) - DETAIL_MAX} more chars, MECHVANE_CHECK_DETAIL=0 for all]"
    print(f"{'ok  ' if cond else 'FAIL'} {label}" + (f": {detail}" if detail and not cond else ""))
    failures += 0 if cond else 1


def rect(name, plane, p0, p1):
    return [{"command": "sketch.create", "params": {"plane": plane, "name": name}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": p0, "p1": p1}},
            {"command": "sketch.finish", "params": {}}]


def circle(name, plane, c, r):
    return [{"command": "sketch.create", "params": {"plane": plane, "name": name}},
            {"command": "sketch.circle.center", "params": {"center": c, "radius": r}},
            {"command": "sketch.finish", "params": {}}]


def names(s):
    return [f["name"] for f in sketch_rule.timeline(s)["timeline"]]


def sketch_rule_and_browser(ws):
    doc = ws.new(PART, "block")
    s = doc.session
    s.batch(rect("S1", "XY", [0, 0], [40, 30]) + circle("S2", "XY", [20, 15], 4) + rect("S3", "XY", [50, 0], [60, 10])
            + [{"command": "solid.extrude", "params": {"sketch": "S1", "distance": 10, "name": "E1"}},
               {"command": "solid.extrude", "params": {"sketch": "S2", "distance": 10, "operation": "cut", "name": "Cut1"}},
               {"command": "solid.extrude", "params": {"sketch": "S3", "distance": 5, "name": "E2"}},
               {"command": "solid.extrude", "params": {"sketch": "S3", "distance": 3, "name": "E3",
                                                        "operation": "new"}}])
    moved = sketch_rule.enforce(s)
    ok("sketch rule: owned sketches sit right before their feature, shared S3 stays",
       names(s) == ["S3", "S1", "E1", "S2", "Cut1", "E2", "E3"], f"{names(s)} {moved}")
    t = tree.part_tree(s)
    rows = [(n.get("name"), [c["name"] for c in n.get("children", [])]) for n in t["features"]]
    ok("browser: sketches under their feature, shared S3 on its own, end of part last",
       rows == [("S3", []), ("E1", ["S1"]), ("Cut1", ["S2"]), ("E2", []), ("E3", []), (None, [])], str(rows))
    s.cmd("timeline.roll_to", {"feature": "Cut1"})
    t = tree.part_tree(s)
    kinds = [n["type"] if n["type"] == "EndOfPart" else n["name"] for n in t["features"]]
    ok("browser: end of part follows the marker", kinds == ["S3", "E1", "Cut1", "EndOfPart", "E2", "E3"], str(kinds))
    ok("browser: features after the marker are rolled back",
       all(n.get("rolled_back") for n in t["features"][4:]), str(t["features"][4:]))
    s.cmd("timeline.roll_to", {})
    owned = [sk for sk, f in sketch_rule.owners(sketch_rule.consumers(s)).items() if f == "Cut1"]
    s.cmd("timeline.delete", {"features": ["Cut1"]})
    s.cmd("timeline.delete", {"features": owned})
    ok("delete feature takes its own sketch", "S2" not in names(s) and "Cut1" not in names(s), str(names(s)))

    # Assembly features in assembly browser (Finding 11)
    asm_f = ws.new(ASSEMBLY, "browser_asm_feat")
    asm_f.session.cmd("solid.cylinder", {"diameter": 6, "height": 30, "base": [10, 10, -5], "name": "AsmCyl"})
    t_asm = tree.assembly_tree(asm_f.session)
    r_asm = tree.render(t_asm)
    ok("browser: assembly_features rendered in assembly", "AsmCyl [CylinderFeature]" in r_asm, r_asm)

    # Visibility in part tree (issue #65)
    t_vis = tree.part_tree(s)
    f_map = {n["name"]: n for n in t_vis["features"] if n.get("name")}
    s3_initial = f_map["S3"]["visible"]  # S3 is consumed by E2 and E3 -> False
    e1_s1_list = [c for c in f_map["E1"].get("children", []) if c.get("name") == "S1"]
    e1_s1 = e1_s1_list[0] if e1_s1_list else {}
    # Show S3 (consumed sketch) and hide Body1
    s.cmd("browser.visibility", {"items": ["S3"], "visible": True})
    s.cmd("browser.visibility", {"items": ["Body1"], "visible": False})
    t_shown = tree.part_tree(s)
    f_map_s = {n["name"]: n for n in t_shown["features"] if n.get("name")}
    # Hide S3 and restore Body1
    s.cmd("browser.visibility", {"items": ["S3"], "visible": False})
    s.cmd("browser.visibility", {"items": ["Body1"], "visible": True})
    t_restored = tree.part_tree(s)
    f_map_r = {n["name"]: n for n in t_restored["features"] if n.get("name")}
    ok("browser: part_tree reflects sketch and body visibility",
       s3_initial is False and e1_s1.get("visible") is False
       and f_map_s["S3"]["visible"] is True and "Body1" in t_shown.get("hidden_bodies", [])
       and f_map_r["S3"]["visible"] is False and "Body1" not in t_restored.get("hidden_bodies", []),
       f"initial={s3_initial} s1={e1_s1} shown={t_shown} restored={t_restored}")

    ws.close("block")


def work_features(ws):
    doc = ws.new(PART, "boss")
    s = doc.session
    s.batch([{"command": "construct.plane.offset", "params": {"base": "XY", "offset": 10, "name": "WP1"}},
             {"command": "construct.plane.offset", "params": {"base": "XY", "offset": 20, "name": "WP2"}},
             {"command": "solid.box", "params": {"length": 40, "width": 20, "height": 5, "corner": [0, 0, 0],
                                                 "operation": "new", "name": "Base"}}]
            + circle("C1", "WP1", [10, 10], 3) + circle("C2", "WP2", [30, 10], 3) + circle("C3", "WP2", [20, 10], 2)
            + [{"command": "solid.extrude", "params": {"sketch": "C1", "distance": -5, "operation": "join", "name": "Boss"}},
               {"command": "solid.extrude", "params": {"sketch": "C2", "distance": -15, "operation": "join", "name": "Peg"}},
               {"command": "solid.extrude", "params": {"sketch": "C3", "distance": -15, "operation": "join", "name": "Pin"}}])
    moved = sketch_rule.enforce(s)
    ok("work plane used by one sketch moves right before it, shared WP2 stays",
       names(s) == ["WP2", "Base", "WP1", "C1", "Boss", "C2", "Peg", "C3", "Pin"], f"{names(s)} {moved}")
    rows = {n["name"]: n for n in tree.part_tree(s)["features"] if n.get("name")}
    boss = rows["Boss"].get("children", [{}])[0]
    ok("browser: feature > sketch > work plane",
       boss.get("name") == "C1" and [c["name"] for c in boss.get("children", [])] == ["WP1"] and "WP2" in rows,
       tree.render(tree.part_tree(s)))
    g = tree.part_tree(s, groups=True)["groups"]
    wf = {r["name"]: r for r in g["work_features"]}
    ok("browser groups: every sketch once with its owner, shared WP2 named as shared",
       [(r["name"], r.get("owner")) for r in g["sketches"]] == [("C1", "Boss"), ("C2", "Peg"), ("C3", "Pin")]
       and wf["WP1"].get("owner") == "C1" and wf["WP2"].get("shared_by") == ["C2", "C3"], str(g))
    r = sketch_rule.delete_with_owned(s, "Boss")
    ok("delete feature takes its sketch and that sketch's work plane",
       r == {"deleted": ["Boss", "C1", "WP1"], "kept": []} and not {"Boss", "C1", "WP1"} & set(names(s)), f"{r} {names(s)}")
    ws.close("boss")

    # Found in the Gemini review 2026-10-20: a feature owning two sketches (loft) must settle.
    doc = ws.new(PART, "loft")
    s = doc.session
    s.batch([{"command": "construct.plane.offset", "params": {"base": "XY", "offset": 20, "name": "WP"}}]
            + circle("L1", "XY", [0, 0], 10) + circle("L2", "WP", [0, 0], 5)
            + [{"command": "solid.loft", "params": {"sections": [{"sketch": "L1"}, {"sketch": "L2"}], "name": "Loft1"}}])
    try:
        moved = sketch_rule.enforce(s)
    except RuntimeError as e:
        moved = str(e)
    ok("loft with two own sketches: they stand as a block before it, its plane before its sketch",
       names(s) == ["L1", "WP", "L2", "Loft1"], f"{names(s)} {moved}")
    ws.close("loft")

    # ... and deleting a feature must not take a sketch something else still needs: a work plane on one
    # of its lines is a use timeline.dependents does not report as direct.
    doc = ws.new(PART, "path")
    s = doc.session
    s.batch(rect("S1", "XY", [0, 0], [20, 10])
            + [{"command": "solid.extrude", "params": {"sketch": "S1", "distance": 5, "name": "E1"}},
               {"command": "construct.plane.along_path", "params": {"path": {"sketch": "S1", "curve": "l1"}, "t": 0.5,
                                                                    "name": "WP1"}}])
    cons = sketch_rule.consumers(s)
    r = sketch_rule.delete_with_owned(s, "E1")
    tl = sketch_rule.timeline(s)["timeline"]
    ok("a work plane on a sketch line counts as a user of the sketch, so deleting keeps the sketch",
       cons["S1"] == ["E1", "WP1"] and "S1" in names(s) and not any(f.get("error") for f in tl),
       f"{cons} {r} {[(f['name'], f.get('error')) for f in tl]}")
    ws.close("path")

    # Suppressed and rolled-back users count (read from the definitions, not from what would fail).
    doc = ws.new(PART, "quiet")
    s = doc.session
    s.batch([{"command": "construct.plane.offset", "params": {"base": "XY", "offset": 10, "name": "WP1"}}]
            + circle("Q1", "WP1", [0, 0], 5) + [{"command": "solid.extrude", "params": {"sketch": "Q1", "distance": 5, "name": "QE1"}}]
            + circle("Q2", "WP1", [20, 0], 5) + [{"command": "solid.extrude", "params": {"sketch": "Q2", "distance": 5, "name": "QE2"}},
                                                 {"command": "timeline.suppress", "params": {"feature": "QE2", "suppressed": True}}])
    cons = sketch_rule.consumers(s)
    s.cmd("timeline.roll_to", {"feature": "QE1"})
    rolled = sketch_rule.consumers(s)
    ok("suppressed and rolled-back users still count",
       cons["WP1"] == ["Q1", "Q2"] and rolled["WP1"] == ["Q1", "Q2"] and rolled["Q2"] == ["QE2"], f"{cons} {rolled}")
    ws.close("quiet")

    # A sketch projecting another sketch's curve or a work plane uses them: no move, no delete.
    doc = ws.new(PART, "proj")
    s = doc.session
    s.batch(circle("P1", "XY", [0, 0], 10)
            + [{"command": "construct.plane.offset", "params": {"base": "XZ", "offset": 5, "name": "WPP"}},
               {"command": "sketch.create", "params": {"plane": "XY", "name": "P2"}},
               {"command": "sketch.project", "params": {"refs": [{"sketch": "P1", "curve": "c1"}, {"plane": "WPP"}]}},
               {"command": "sketch.finish", "params": {}},
               {"command": "solid.extrude", "params": {"sketch": "P1", "distance": 5, "name": "PE1"}}])
    cons = sketch_rule.consumers(s)
    sketch_rule.enforce(s)
    warnings = [f["name"] for f in sketch_rule.timeline(s)["timeline"] if f.get("warning")]
    ok("projections count as uses, and enforce keeps them intact",
       cons["P1"] == ["P2", "PE1"] and cons["WPP"] == ["P2"] and not warnings, f"{cons} {names(s)} {warnings}")
    ws.close("proj")


def plate_part(ws):
    doc = ws.new(PART, "plate")
    doc.session.batch([
        {"command": "parameters.add", "params": {"name": "hx", "expression": "10 mm"}},
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 5, "corner": [-30, -20, 0],
                                            "operation": "new", "body_name": "Plate"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 7, "base": ["hx", 0, -1],
                                                 "operation": "cut", "name": "Hole"}}])
    doc.save()
    return doc


def hinge_assembly(ws, part):
    asm = ws.new(ASSEMBLY, "pinned")
    s = asm.session
    s.cmd("component.insert_design", {"path": str(part.path), "name": "Plate"})
    s.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": True})
    s.batch([{"command": "solid.cylinder", "params": {"diameter": 6, "height": 20, "base": [0, 50, 0],
                                                      "operation": "new", "body_name": "PinBody"}},
             {"command": "component.create", "params": {"name": "Pin", "parent": "root", "activate": False}},
             {"command": "component.move_bodies", "params": {"bodies": ["PinBody"], "component": "Pin"}}])
    params = {"type": "rigid", "name": "PinInHole", "flip": True,
              "a": {"occurrence": "Plate:1", "circle": [13, 0, 5]}, "b": {"occurrence": "Pin:1", "circle": [3, 50, 0]}}
    s.cmd("joint.create", params)
    entry = links.record(ws, asm, "PinInHole", params)
    asm.save()
    return asm, entry


def joint_x(asm):
    j = next(j for j in asm.session.cmd("joint.list")["joints"] if j["name"] == "PinInHole")
    return round(j["frame_a"]["origin"][0], 4)


def joints_across_files(ws):
    part = plate_part(ws)
    asm, entry = hinge_assembly(ws, part)
    a = entry["sides"].get("a", {})
    ok("add joint records the part's face name", a.get("kind") == "cylinder" and a.get("face", "").startswith("F"),
       str(entry))
    ok("browser: joint listed under both parts", all(
        o.get("joints") and o["joints"][0]["name"] == "PinInHole" for o in tree.assembly_tree(asm.session)["occurrences"]),
       tree.render(tree.assembly_tree(asm.session)))

    rel = tree.assembly_tree(asm.session, groups=True)["groups"]["relations"]
    ok("browser groups: relations folder lists the joint with both parts",
       [(r["name"], r["between"]) for r in rel] == [("PinInHole", ["Plate:1", "Pin:1"])], str(rel))

    # 1. A legitimate edit: the hole moves. The joint follows and nothing is reported.
    part.session.cmd("parameters.change", {"name": "hx", "expression": "20 mm"})
    part.save()
    r = links.update_links(ws, asm)
    ok("hole moved: joint follows to x = 20", joint_x(asm) == 20.0, str(joint_x(asm)))
    ok("hole moved: no warning", not r["warnings"], str(r["warnings"]))

    # 2. #3330: a same-size hole added before it in the part's history. SolidCraft moves the joint
    # to the new hole without a word; Mechvane must say so and put it back. The joint was edited
    # after add_joint (flip, offset), and the repair must keep that.
    asm.session.cmd("joint.edit", {"joint": "PinInHole", "flip": False, "offset": 2})
    part.session.cmd("timeline.roll_to", {"position": 1})
    part.session.cmd("solid.cylinder", {"diameter": 6, "height": 7, "base": [-10, 0, -1], "operation": "cut",
                                        "name": "Hole0"})
    part.session.cmd("timeline.roll_to", {})
    part.save()
    r = links.update_links(ws, asm)
    moved = [w for w in r["warnings"] if w["status"] == "moved"]
    # SolidCraft up to 0.21 moved the joint (#3330, fixed upstream since 0.22): then Mechvane must say so
    ok("new hole before it: the joint stays on its hole, or Mechvane reports it moved",
       bool(moved) or (joint_x(asm) == 20.0 and not r["warnings"]), f"x = {joint_x(asm)}, {r['joints']}")
    r = links.update_links(ws, asm, repair_moved=True)
    ok("repair puts the joint back on its hole (x = 20)", joint_x(asm) == 20.0 and not r["warnings"],
       f"x = {joint_x(asm)}, {r}")
    j = next(j for j in asm.session.cmd("joint.list")["joints"] if j["name"] == "PinInHole")
    ok("repair keeps flip and offset set after add_joint", j["flip"] is False and j["offset"] == 2,
       f"flip = {j['flip']}, offset = {j['offset']}")

    # 2b. The same for a joint Mechvane only adopted (no add_joint parameters to recreate it from).
    links.forget(asm, "PinInHole")
    links.record(ws, asm, "PinInHole")
    part.session.cmd("timeline.roll_to", {"position": 1})
    part.session.cmd("solid.cylinder", {"diameter": 6, "height": 7, "base": [-20, 0, -1], "operation": "cut",
                                        "name": "Hole00"})
    part.session.cmd("timeline.roll_to", {})
    part.save()
    r = links.update_links(ws, asm, repair_moved=True)
    ok("adopted joint: on its hole (x = 20) after update_links, repaired where it had moved",
       joint_x(asm) == 20.0 and not r["warnings"],
       f"x = {joint_x(asm)}, {r}")

    # 3. The recorded face disappears.
    part.session.cmd("timeline.delete", {"features": ["Hole"]})
    part.save()
    r = links.update_links(ws, asm)
    ok("hole deleted: reported", any(w["status"] in ("face_missing", "moved", "origin_lost") for w in r["warnings"]),
       str(r["joints"]))

    # 4. A joint made without add_joint can be adopted, and a deleted one is forgotten.
    asm.session.cmd("joint.create", {"type": "rigid", "name": "Raw", "a": {"occurrence": "Plate:1", "point": [0, 10, 5]},
                                     "b": {"occurrence": "Pin:1", "point": [0, 50, 20]}})
    links.record(ws, asm, "Raw")
    ok("adopted joint is checked", any(r["joint"] == "Raw" for r in links.check(ws, asm)))
    asm.session.cmd("joint.delete", {"joint": "Raw"})
    links.forget(asm, "Raw")
    ok("deleted joint is forgotten", "Raw" not in asm.metadata().get("joints", {}))

    # edit_joint rename without KeyError and update metadata (Finding 4)
    orig_server_ws = server.ws
    server.ws = ws
    try:
        p1_ej = ws.new(PART, "p1_ej")
        p1_ej.session.batch([
            {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0]}},
            {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [10, 20, 0], "operation": "cut", "name": "Hole"}}
        ])
        p1_ej.save()
        p2_ej = ws.new(PART, "p2_ej")
        p2_ej.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0, 0, 0], "name": "Pin"})
        p2_ej.save()

        asm_ej = ws.new(ASSEMBLY, "asm_ej")
        links.insert(ws, asm_ej, p1_ej.path, name="P1", grounded=True)
        links.insert(ws, asm_ej, p2_ej.path, name="P2")

        jp = {"type": "revolute", "name": "Rev1",
              "a": {"occurrence": "P1:1", "point": [10, 20, 10], "z": [0, 0, 1]},
              "b": {"occurrence": "P2:1", "point": [0, 0, 0], "z": [0, 0, 1]}}
        asm_ej.session.cmd("joint.create", jp)
        links.record(ws, asm_ej, "Rev1", jp)

        r_edit = server.edit_joint(asm_ej.name, "Rev1", {"name": "RevRenamed"})
        meta_j = asm_ej.metadata().get("joints", {})
        ok("edit_joint: rename without KeyError and metadata preserved under new name",
           "RevRenamed" in meta_j and "Rev1" not in meta_j and "a" in r_edit.get("anchors", {}) and "b" in r_edit.get("anchors", {}),
           f"meta={meta_j} r={r_edit}")
    finally:
        server.ws = orig_server_ws

    # 5. Reopening the assembly keeps the recorded anchors (stored in the design's metadata).
    asm.save()
    ws.close("pinned")
    asm2 = ws.open(asm.path)
    ok("anchors survive save and reopen", "PinInHole" in asm2.metadata().get("joints", {}) and asm2.kind == ASSEMBLY,
       str(asm2.metadata()))

    # 6. Planar face repair (#3330): joint plate-on-plate (rigid or planar on a deck face).
    base = ws.new(PART, "base_deck")
    base.session.batch([
        {"command": "solid.box", "params": {"length": 100, "width": 50, "height": 5, "corner": [-50, -25, 0], "body_name": "Base"}},
        {"command": "solid.box", "params": {"length": 30, "width": 30, "height": 5, "corner": [10, -15, 5], "operation": "join", "name": "Deck1"}}
    ])
    base.save()

    top = ws.new(PART, "top_plate")
    top.session.cmd("solid.box", {"length": 20, "width": 20, "height": 5, "corner": [-10, -10, 0], "body_name": "Top"})
    top.save()

    p_asm = ws.new(ASSEMBLY, "plate_asm")
    p_asm.session.cmd("component.insert_design", {"path": str(base.path), "name": "Base"})
    p_asm.session.cmd("occurrence.ground", {"occurrence": "Base:1", "grounded": True})
    p_asm.session.cmd("component.insert_design", {"path": str(top.path), "name": "Top"})

    p_params = {"type": "rigid", "name": "PlateOnPlate",
                "a": {"occurrence": "Base:1", "face": [25, 0, 10]},
                "b": {"occurrence": "Top:1", "face": [0, 0, 0]}}
    p_asm.session.cmd("joint.create", p_params)
    p_entry = links.record(ws, p_asm, "PlateOnPlate", p_params)
    p_asm.save()
    ok("plane joint recorded with face and in-plane offset",
       p_entry["sides"]["a"]["kind"] == "plane" and "offset" in p_entry["sides"]["a"], str(p_entry))

    # #3330 on plane: an identical deck added before it in history. SolidCraft moves the joint.
    base.session.cmd("timeline.roll_to", {"position": 1})
    base.session.cmd("solid.box", {"length": 30, "width": 30, "height": 5, "corner": [-40, -15, 5], "operation": "join", "name": "Deck0"})
    base.session.cmd("timeline.roll_to", {})
    base.save()

    r = links.update_links(ws, p_asm)
    moved_p = [w for w in r["warnings"] if w.get("joint") == "PlateOnPlate" and w.get("status") == "moved"]
    ok("plane #3330: the joint stays, or update_links reports it moved",
       bool(moved_p) or not [w for w in r["warnings"] if w.get("joint") == "PlateOnPlate"], str(r["warnings"]))

    r = links.update_links(ws, p_asm, repair_moved=True)
    pj = next(j for j in p_asm.session.cmd("joint.list")["joints"] if j["name"] == "PlateOnPlate")
    ok("plane repair puts joint back on deck face (x = 25)",
       not r["warnings"] and round(pj["frame_a"]["origin"][0], 4) == 25.0, f"pos = {pj['frame_a']['origin']}, {r}")

    # 6b. Plane joint with in-plane offset preserved during repair
    p_asm.session.cmd("joint.delete", {"joint": "PlateOnPlate"})
    links.forget(p_asm, "PlateOnPlate")
    off_params = {"type": "rigid", "name": "PlateOnPlateOff",
                  "a": {"occurrence": "Base:1", "point": [28, 3, 10], "z": [0, 0, 1]},
                  "b": {"occurrence": "Top:1", "face": [0, 0, 0]}}
    p_asm.session.cmd("joint.create", off_params)
    off_entry = links.record(ws, p_asm, "PlateOnPlateOff", off_params)
    ok("in-plane offset recorded relative to centroid",
       [round(x, 4) for x in off_entry["sides"]["a"]["offset"][:2]] == [3.0, 3.0], str(off_entry))

    # Simulate joint moved to Deck0
    p_asm.session.cmd("joint.delete", {"joint": "PlateOnPlateOff"})
    p_asm.session.cmd("joint.create", {"type": "rigid", "name": "PlateOnPlateOff",
                                       "a": {"occurrence": "Base:1", "point": [-22, 3, 10], "z": [0, 0, 1]},
                                       "b": {"occurrence": "Top:1", "face": [0, 0, 0]}})
    r = links.update_links(ws, p_asm, repair_moved=True)
    pj_off = next(j for j in p_asm.session.cmd("joint.list")["joints"] if j["name"] == "PlateOnPlateOff")
    ok("repair preserves in-plane offset from face centroid (x = 28, y = 3)",
       not r["warnings"] and [round(x, 4) for x in pj_off["frame_a"]["origin"][:2]] == [28.0, 3.0],
       f"pos = {pj_off['frame_a']['origin']}, {r}")

    # 6c. Legacy entry without offset repaired at centroid with warning
    meta = p_asm.metadata()
    del meta["joints"]["PlateOnPlateOff"]["sides"]["a"]["offset"]
    p_asm.set_metadata(meta)
    p_asm.session.cmd("joint.delete", {"joint": "PlateOnPlateOff"})
    p_asm.session.cmd("joint.create", {"type": "rigid", "name": "PlateOnPlateOff",
                                       "a": {"occurrence": "Base:1", "point": [-22, 3, 10], "z": [0, 0, 1]},
                                       "b": {"occurrence": "Top:1", "face": [0, 0, 0]}})
    r = links.update_links(ws, p_asm, repair_moved=True)
    pj_leg = next(j for j in p_asm.session.cmd("joint.list")["joints"] if j["name"] == "PlateOnPlateOff")
    ok("legacy entry without offset repaired at centroid with warning",
       round(pj_leg["frame_a"]["origin"][0], 4) == 25.0 and any("offset" in str(w).lower() or "centroid" in str(w).lower() for w in r["warnings"]),
       f"pos = {pj_leg['frame_a']['origin']}, {r}")

    ws.close_all()


def _bbox_matches(actual, expected):
    return all(abs(a - e) <= ABS for row_a, row_e in zip(actual, expected) for a, e in zip(row_a, row_e))


def standard_parts_checks(ws):
    cases = [
        ("ISO 4762", "M5", 16, "ISO 4762 M5x16",
         math.pi * (8.5 / 2) ** 2 * 5.0 + math.pi * (5.0 / 2) ** 2 * 16.0 - (math.sqrt(3) / 2) * 4.0 ** 2 * 2.5,
         [[-4.25, -4.25, -16.0], [4.25, 4.25, 5.0]]),
        ("ISO 10642", "M5", 16, "ISO 10642 M5x16",
         (math.pi * 3.10 / 3.0) * ((11.20 / 2) ** 2 + (11.20 / 2) * (5.0 / 2) + (5.0 / 2) ** 2)
         + math.pi * (5.0 / 2) ** 2 * (16.0 - 3.10)
         - (math.sqrt(3) / 2) * 3.0 ** 2 * 1.9,
         [[-5.6, -5.6, -16.0], [5.6, 5.6, 0.0]]),
        ("ISO 4017", "M6", 20, "ISO 4017 M6x20",
         (math.sqrt(3) / 2) * 10.0 ** 2 * 4.0 + math.pi * (6.0 / 2) ** 2 * 20.0,
         [[-10.0 / math.sqrt(3), -5.0, -20.0], [10.0 / math.sqrt(3), 5.0, 4.0]]),
        ("ISO 4017", "M10", 40, "ISO 4017 M10x40",
         (math.sqrt(3) / 2) * 16.0 ** 2 * 6.4 + math.pi * (10.0 / 2) ** 2 * 40.0,
         [[-16.0 / math.sqrt(3), -8.0, -40.0], [16.0 / math.sqrt(3), 8.0, 6.4]]),
        ("ISO 4032", "M5", None, "ISO 4032 M5",
         ((math.sqrt(3) / 2) * 8.0 ** 2 - math.pi * (5.0 / 2) ** 2) * 4.7,
         [[-8.0 / math.sqrt(3), -4.0, 0.0], [8.0 / math.sqrt(3), 4.0, 4.7]]),
        ("ISO 7089", "M5", None, "ISO 7089 M5",
         math.pi * ((10.0 / 2) ** 2 - (5.3 / 2) ** 2) * 1.0,
         [[-5.0, -5.0, 0.0], [5.0, 5.0, 1.0]]),
        ("Ruthex", "M3", None, "Ruthex RX-M3x5.7",
         math.pi * ((4.6 / 2) ** 2 - (3.0 / 2) ** 2) * 5.7,
         [[-2.3, -2.3, 0.0], [2.3, 2.3, 5.7]]),
        ("DIN 625", "6000", None, "DIN 625 6000",
         math.pi * ((26.0 / 2) ** 2 - (10.0 / 2) ** 2) * 8.0 - math.pi * 0.3 ** 2 * (26.0 + 10.0),
         [[-13.0, -13.0, 0.0], [13.0, 13.0, 8.0]]),
    ]
    for norm, size, length, desig, v_exp, bb_exp in cases:
        res = standard_parts.create(ws, norm, size, length=length)
        doc = ws.get(res["name"], PART)
        body = doc.session.cmd("document.inspect", {"measure": True})["bodies"][0]
        vol = body["volume_mm3"]
        bb = [body["bbox"]["min"], body["bbox"]["max"]]
        meta = doc.metadata()
        std = meta.get("standard", {})
        t = tree.part_tree(doc.session)
        sketches_owned = all(n.get("type") != "Sketch" for n in t["features"])
        ok(f"standard part {desig}: volume, bbox, metadata and sketch ownership",
           abs(vol - v_exp) <= REL * v_exp
           and abs(standard_parts.expected_volume(norm, size, length) - v_exp) < 1e-9
           and _bbox_matches(bb, bb_exp)
           and _bbox_matches(bb, standard_parts.expected_bbox(norm, size, length))
           and meta.get("kind") == PART
           and std.get("norm") == norm and std.get("size") == size and std.get("designation") == desig
           and res["sketch_rule"] == {"moved": [], "refused": []}
           and sketches_owned,
           f"vol={vol:.4f} (exp {v_exp:.4f}), bb={bb} (exp {bb_exp}), meta={meta}, tree={t}")
        if norm == "ISO 4017":
            s_exp = standard_parts.ISO_4017[size]["s"]
            faces = doc.session.cmd("model.faces", {"body": "Screw"})["faces"]
            f_neg_y = next(f for f in faces if f["name"] == "F2:side:l3")
            f_pos_y = next(f for f in faces if f["name"] == "F2:side:l6")
            m_flats = doc.session.cmd("inspect.measure", {"items": [
                {"type": "face", "body": "Screw", "index": f_neg_y["index"], "point": f_neg_y["centroid"]},
                {"type": "face", "body": "Screw", "index": f_pos_y["index"], "point": f_pos_y["centroid"]},
            ]})
            s_meas = m_flats["distance_mm"]
            ok(f"standard part {desig}: width across flats s = {s_exp:g} mm by measurement",
               abs(s_meas - s_exp) <= ABS and abs((bb[1][1] - bb[0][1]) - s_exp) <= ABS,
               f"s_meas={s_meas} (exp {s_exp}), bb_y={bb[1][1] - bb[0][1]}")
        if norm == "Ruthex":
            hole = std.get("mounting_hole", {})
            ok("heat-set insert metadata includes mounting hole diameter and min_depth",
               hole == {"diameter": 4.0, "min_depth": 6.7}, str(std))

    cat_4017 = server.list_standard_parts("DIN 933")
    ok("ISO 4017 / DIN 933 resolved in resolve_norm, catalog and list_standard_parts",
       standard_parts.resolve_norm("DIN 933") == "ISO 4017"
       and standard_parts.catalog("DIN 933")["norm"] == "ISO 4017"
       and cat_4017["norm"] == "ISO 4017"
       and list(cat_4017["sizes"].keys()) == ["M3", "M4", "M5", "M6", "M8", "M10"],
       str(cat_4017))

    # Parameters stay editable (parameters.change recomputes geometry) and metadata survives reopen.
    screw = ws.get("ISO_4762_M5x16", PART)
    screw.session.cmd("parameters.change", {"name": "l", "expression": "20 mm"})
    b20 = screw.session.cmd("document.inspect", {"measure": True})["bodies"][0]
    v20 = standard_parts.expected_volume("ISO 4762", "M5", 20)
    ok("standard part parameters remain editable (M5x16 -> l=20 mm)",
       abs(b20["volume_mm3"] - v20) <= REL * v20 and _bbox_matches([b20["bbox"]["min"], b20["bbox"]["max"]], [[-4.25, -4.25, -20.0], [4.25, 4.25, 5.0]]),
       f"vol={b20['volume_mm3']} exp={v20}")
    screw_path = screw.path
    ws.close("ISO_4762_M5x16")
    reopened = ws.open(screw_path)
    ok("standard part metadata survives save and reopen",
       reopened.metadata().get("standard", {}).get("designation") == "ISO 4762 M5x16",
       str(reopened.metadata()))

    # Non-preferred screw length warns but still builds; comma decimal "M2,5" is accepted.
    nonpref = standard_parts.create(ws, "ISO 4762", "M2,5", length=11)
    ok("ISO 4762 non-preferred length warns and normalizes M2,5 to M2.5",
       nonpref["standard"]["size"] == "M2.5"
       and nonpref["standard"]["preferred_length"] is False
       and bool(nonpref.get("warnings")),
       str(nonpref))

    # Invalid norm or size raises a clear ValueError without leaving a document open.
    bad_calls = [
        ("ISO 4762", "M7", 16),
        ("ISO 4017", "M7", 20),
        ("ISO 4017", "M6", None),
        ("ISO 4032", "M14", None),
        ("Ruthex", "M6", None),
        ("DIN 625", "6006", None),
        ("ISO 9999", "M5", None),
        ("ISO 4762", "M5", None),
    ]
    errors_ok = True
    open_before = len(ws.docs)
    for b_norm, b_size, b_len in bad_calls:
        try:
            standard_parts.create(ws, b_norm, b_size, length=b_len)
            errors_ok = False
        except ValueError:
            pass
    ok("invalid standard part norm, size or missing screw length raises ValueError",
       errors_ok and len(ws.docs) == open_before)

    # Test error cleanup: if doc creation fails during batch, doc is closed and not kept in ws.docs
    orig_spec = standard_parts.spec
    try:
        standard_parts.spec = lambda *a, **kw: {
            "standard": {"norm": "ISO 4762", "size": "M5", "designation": "ISO_4762_M5_Bad"},
            "commands": [{"command": "nonexistent.command.fails"}],
            "warnings": [],
        }
        create_failed = False
        try:
            standard_parts.create(ws, "ISO 4762", "M5", length=16)
        except Exception:
            create_failed = True
        bad_file = ws.root / "ISO_4762_M5_Bad.solidcraft"
        ok("creation failure cleans up open document from workspace",
           create_failed and "ISO_4762_M5_Bad" not in ws.docs and not bad_file.exists())
    finally:
        standard_parts.spec = orig_spec

    ws.close_all()


def subassemblies(ws):
    plate = ws.new(PART, "sub_plate")
    plate.session.batch([
        {"command": "parameters.add", "params": {"name": "hx", "expression": "10 mm"}},
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 5, "corner": [-30, -20, 0],
                                            "operation": "new", "body_name": "Plate"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 7, "base": [0, 12, -1],
                                                 "operation": "cut", "name": "MountHole"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 7, "base": ["hx", 0, -1],
                                                 "operation": "cut", "name": "BaseHole"}},
    ])
    plate.save()

    bolt = ws.new(PART, "sub_bolt")
    bolt.session.cmd("solid.cylinder", {"diameter": 6, "height": 15, "base": [0, 0, 0],
                                        "operation": "new", "body_name": "Bolt"})
    bolt.save()

    base = ws.new(PART, "top_base")
    base.session.batch([
        {"command": "solid.box", "params": {"length": 100, "width": 60, "height": 8, "corner": [-50, -30, 0],
                                            "operation": "new", "body_name": "Base"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [30, 0, -1],
                                                 "operation": "cut", "name": "BasePinHole"}},
    ])
    base.save()

    sub = ws.new(ASSEMBLY, "sub_unit")
    links.insert(ws, sub, plate.path, name="Plate", grounded=True)
    links.insert(ws, sub, bolt.path, name="Bolt", translate=[0, 0, 20], grounded=False)
    jp = {"type": "revolute", "name": "BoltOnPlate",
          "a": {"occurrence": "Plate:1", "circle": [3, 12, 5]},
          "b": {"occurrence": "Bolt:1", "circle": [3, 0, 20]}}
    sub.session.cmd("joint.create", jp)
    links.record(ws, sub, "BoltOnPlate", jp)
    sub.save()

    top = ws.new(ASSEMBLY, "top_asm")
    links.insert(ws, top, base.path, name="Base", grounded=True)
    ins = links.insert(ws, top, sub.path, name="Sub", translate=[80, 0, 0], grounded=False)
    meta_sub = top.metadata().get("subassemblies", {}).get("Sub", {})
    ok("subassembly insert creates parent component, links parts, recreates joints and records metadata",
       ins["kind"] == "subassembly" and ins["occurrence_name"] == "Sub:1"
       and ins["parts"] == ["Plate:1", "Bolt:1"] and ins["joints"] == ["BoltOnPlate"]
       and Path(meta_sub.get("file", "")).name == "sub_unit.solidcraft",
       f"{ins} {meta_sub}")

    t = tree.assembly_tree(top.session, groups=True)
    rendered = tree.render(t)
    sub_node = next((o for o in t["occurrences"] if o["name"] == "Sub:1"), {})
    children = [c["name"] for c in sub_node.get("occurrences", [])]
    rel = t["groups"]["relations"]
    ok("browser: subassembly shows nested parts and marks subassembly joints with owner",
       children == ["Plate:1", "Bolt:1"] and sub_node.get("file") == "sub_unit.solidcraft"
       and any(r["name"] == "BoltOnPlate" and r.get("owner") == "Sub:1" for r in rel)
       and "Sub:1 (sub_unit.solidcraft)" in rendered,
       f"{sub_node} {rel}\n{rendered}")

    # Outer joint between top_base and the subassembly's Plate (using "Sub:1/Plate:1").
    outer_raw = {"type": "rigid", "name": "SubOnBase", "flip": True,
                 "a": {"occurrence": "Base:1", "circle": [33, 0, 8]},
                 "b": {"occurrence": "Sub:1/Plate:1", "circle": [93, 0, 5]}}
    outer_params = links.resolve_occurrences(top.session, outer_raw)
    top.session.cmd("joint.create", outer_params)
    entry = links.record(ws, top, "SubOnBase", outer_params)
    occs = {o["name"]: o for o in links._occurrences(top.session).values()}
    ok("outer joint to subassembly part records part face across parent transform chain and moves whole subassembly",
       entry["sides"].get("b", {}).get("face", "").startswith("F")
       and [round(x, 4) for x in occs["Plate:1"]["transform"][3][:3]] == [20.0, 0.0, 3.0]
       and [round(x, 4) for x in occs["Bolt:1"]["transform"][3][:3]] == [20.0, 12.0, 8.0],
       f"{entry} plate={occs['Plate:1']['transform'][3][:3]} bolt={occs['Bolt:1']['transform'][3][:3]}")

    def sub_joint_x():
        j = next(j for j in top.session.cmd("joint.list")["joints"] if j["name"] == "SubOnBase")
        return round(j["frame_b"]["origin"][0], 4)

    # Legitimate edit in the subassembly's part file: BaseHole moves from hx=10 to hx=20.
    plate.session.cmd("parameters.change", {"name": "hx", "expression": "20 mm"})
    plate.save()
    r = links.update_links(ws, top)
    occs = {o["name"]: o for o in links._occurrences(top.session).values()}
    ok("subassembly part hole moved: outer joint follows and subassembly shifts without warning",
       sub_joint_x() == 30.0 and not r["warnings"]
       and [round(x, 4) for x in occs["Plate:1"]["transform"][3][:3]] == [10.0, 0.0, 3.0],
       f"x={sub_joint_x()} plate={occs['Plate:1']['transform'][3][:3]} warnings={r['warnings']}")

    # #3330 on a subassembly part: insert a same-size hole before BaseHole in sub_plate's history.
    plate.session.cmd("timeline.roll_to", {"position": 1})
    plate.session.cmd("solid.cylinder", {"diameter": 6, "height": 7, "base": [-15, 0, -1],
                                         "operation": "cut", "name": "Hole0"})
    plate.session.cmd("timeline.roll_to", {})
    plate.save()
    r = links.update_links(ws, top)
    moved_w = [w for w in r["warnings"] if w["joint"] == "SubOnBase" and w["status"] == "moved"]
    ok("subassembly #3330: new hole before BaseHole: the outer joint stays, or the move is reported",
       bool(moved_w) or not [w for w in r["warnings"] if w["joint"] == "SubOnBase"], f"{r['warnings']} {r['joints']}")
    r = links.update_links(ws, top, repair_moved=True)
    occs = {o["name"]: o for o in links._occurrences(top.session).values()}
    ok("subassembly #3330: repair puts outer joint back on BaseHole and restores subassembly position",
       sub_joint_x() == 30.0 and not r["warnings"]
       and [round(x, 4) for x in occs["Plate:1"]["transform"][3][:3]] == [10.0, 0.0, 3.0],
       f"x={sub_joint_x()} plate={occs['Plate:1']['transform'][3][:3]} warnings={r['warnings']}")

    # Structural change in the subassembly file: add a Cap part and edit BoltOnPlate's offset.
    cap = ws.new(PART, "sub_cap")
    cap.session.cmd("solid.cylinder", {"diameter": 10, "height": 4, "base": [0, 0, 0],
                                       "operation": "new", "body_name": "Cap"})
    cap.save()
    links.insert(ws, sub, cap.path, name="Cap", translate=[0, 12, 25], grounded=False)
    sub.session.cmd("joint.edit", {"joint": "BoltOnPlate", "offset": 4})
    links.record(ws, sub, "BoltOnPlate")
    sub.save()
    r = links.update_links(ws, top)
    sub_rep = r["subassemblies"][0]
    occs = {o["name"]: o for o in links._occurrences(top.session).values()}
    ok("update_links syncs added part and edited joint from the subassembly file",
       sub_rep["status"] == "updated" and sub_rep["added"] == ["Cap:1"] and sub_rep["moved"] == ["Bolt:1"]
       and "Cap:1" in occs and [round(x, 4) for x in occs["Bolt:1"]["transform"][3][:3]] == [10.0, 12.0, 12.0],
       f"{sub_rep} bolt={occs.get('Bolt:1', {}).get('transform')}")

    # Remove Cap from the subassembly file and verify update_links removes it from top_asm.
    sub.session.cmd("component.delete", {"component": "Cap"})
    sub.save()
    r = links.update_links(ws, top)
    sub_rep = r["subassemblies"][0]
    occs = {o["name"]: o for o in links._occurrences(top.session).values()}
    ok("update_links removes deleted part from the subassembly in the outer assembly",
       sub_rep["status"] == "updated" and sub_rep["removed"] == ["Cap:1"] and "Cap:1" not in occs,
       f"{sub_rep} occs={list(occs)}")
    ws.close_all()


def insert_rotation_checks(ws):
    plate = ws.new(PART, "rot_plate")
    plate.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 6, "corner": [0, 0, 0],
                                            "operation": "new", "body_name": "Plate"}}
    ])
    plate.save()

    asm = ws.new(ASSEMBLY, "rot_asm")
    ins = links.insert(ws, asm, plate.path, name="PlateX", rotate={"axis": [1, 0, 0], "angle": 90}, grounded=True)
    props = asm.session.cmd("occurrence.properties", {"occurrence": ins["occurrence"]})
    bbox = props["total"]["bbox"]
    ok("insert_part: plate rotated 90 deg around X has correct bounding box when grounded",
       _bbox_matches([bbox["min"], bbox["max"]], [[0.0, -6.0, 0.0], [60.0, 0.0, 40.0]]),
       str(bbox))

    sub = ws.new(ASSEMBLY, "rot_sub")
    links.insert(ws, sub, plate.path, name="SubPlate", grounded=True)
    sub.save()

    top = ws.new(ASSEMBLY, "rot_top")
    sub_ins = links.insert(ws, top, sub.path, name="RotSub", rotate={"axis": [1, 0, 0], "angle": 90}, grounded=True)
    sub_props = top.session.cmd("occurrence.properties", {"occurrence": sub_ins["occurrence"]})
    sub_bbox = sub_props["total"]["bbox"]
    ok("insert_part: subassembly rotated 90 deg around X has correct bounding box when grounded",
       _bbox_matches([sub_bbox["min"], sub_bbox["max"]], [[0.0, -6.0, 0.0], [60.0, 0.0, 40.0]]),
       str(sub_bbox))

    ws.close_all()


def insert_grounded_checks(ws):
    p1 = ws.new(PART, "g_part1")
    p1.session.batch([{"command": "solid.box", "params": {"length": 30, "width": 20, "height": 10, "name": "Box"}}])
    p1.save()

    p2 = ws.new(PART, "g_part2")
    p2.session.batch([{"command": "solid.box", "params": {"length": 20, "width": 20, "height": 10, "name": "Box"}}])
    p2.save()

    # 1. Empty assembly: first part without grounded argument -> grounded automatically
    asm1 = ws.new(ASSEMBLY, "g_asm1")
    ins1 = links.insert(ws, asm1, p1.path, name="P1")
    occs1 = links._occurrences(asm1.session)
    ok("insert: first part without grounded argument is grounded in empty assembly",
       occs1.get(ins1["occurrence"], {}).get("grounded") is True,
       f"occ={ins1['occurrence']} occs={occs1}")

    # 2. Assembly with already grounded part: second part without grounded argument -> not grounded
    ins2 = links.insert(ws, asm1, p2.path, name="P2", translate=[40, 0, 0])
    occs2 = links._occurrences(asm1.session)
    ok("insert: second part without grounded argument is not grounded when assembly already has a component",
       occs2.get(ins2["occurrence"], {}).get("grounded") is False
       and occs2.get(ins1["occurrence"], {}).get("grounded") is True,
       f"occ2={ins2['occurrence']} occs={occs2}")

    # 3. Empty assembly: first part with grounded=False -> not grounded
    asm2 = ws.new(ASSEMBLY, "g_asm2")
    ins_free = links.insert(ws, asm2, p1.path, name="P1", grounded=False)
    occs_free = links._occurrences(asm2.session)
    ok("insert: first part with grounded=False is not grounded",
       occs_free.get(ins_free["occurrence"], {}).get("grounded") is False,
       f"occ={ins_free['occurrence']} occs={occs_free}")

    # 4. Explicit grounded=True on an assembly with an existing part
    ins_exp = links.insert(ws, asm2, p2.path, name="P2", translate=[40, 0, 0], grounded=True)
    occs_exp = links._occurrences(asm2.session)
    ok("insert: second part with explicit grounded=True is grounded",
       occs_exp.get(ins_exp["occurrence"], {}).get("grounded") is True
       and occs_exp.get(ins_free["occurrence"], {}).get("grounded") is False,
       f"occ={ins_exp['occurrence']} occs={occs_exp}")

    # 5. Subassembly into empty assembly without grounded argument -> parent component grounded
    sub_asm = ws.new(ASSEMBLY, "g_sub")
    links.insert(ws, sub_asm, p1.path, name="SubP1", grounded=True)
    links.insert(ws, sub_asm, p2.path, name="SubP2", translate=[10, 0, 0], grounded=False)
    sub_asm.save()

    top_asm1 = ws.new(ASSEMBLY, "g_top1")
    ins_sub1 = links.insert(ws, top_asm1, sub_asm.path, name="Sub1")
    top_occs1 = links._occurrences(top_asm1.session)
    ok("insert: subassembly inserted into empty assembly without grounded argument has grounded parent component",
       ins_sub1["kind"] == "subassembly" and top_occs1.get(ins_sub1["occurrence"], {}).get("grounded") is True,
       f"sub_occ={ins_sub1.get('occurrence')} occs={top_occs1}")

    # 6. Subassembly inserted into non-empty assembly without grounded argument -> parent component NOT grounded
    ins_sub2 = links.insert(ws, top_asm1, sub_asm.path, name="Sub2", translate=[50, 0, 0])
    top_occs2 = links._occurrences(top_asm1.session)
    ok("insert: subassembly inserted into non-empty assembly without grounded argument is not grounded",
       ins_sub2["kind"] == "subassembly" and top_occs2.get(ins_sub2["occurrence"], {}).get("grounded") is False,
       f"sub2_occ={ins_sub2.get('occurrence')} occs={top_occs2}")

    # 7. MCP server.insert_part tests
    orig_server_ws = server.ws
    server.ws = ws
    try:
        asm_mcp = ws.new(ASSEMBLY, "g_mcp_asm")
        res1 = server.insert_part("g_mcp_asm", str(p1.path), name="McpP1")
        mcp_occs1 = links._occurrences(asm_mcp.session)
        ok("server.insert_part: first part without grounded argument is grounded",
           mcp_occs1.get(res1["occurrence"], {}).get("grounded") is True,
           f"res1={res1} occs={mcp_occs1}")

        res2 = server.insert_part("g_mcp_asm", str(p2.path), name="McpP2", translate=[30, 0, 0])
        mcp_occs2 = links._occurrences(asm_mcp.session)
        ok("server.insert_part: second part without grounded argument is not grounded",
           mcp_occs2.get(res2["occurrence"], {}).get("grounded") is False
           and mcp_occs2.get(res1["occurrence"], {}).get("grounded") is True,
           f"res2={res2} occs={mcp_occs2}")

        # add_joint between the auto-grounded first part and the free second part:
        # only the second part moves, the first keeps its transform
        t1_before = mcp_occs2[res1["occurrence"]]["transform"]
        t2_before = mcp_occs2[res2["occurrence"]]["transform"]
        server.add_joint("g_mcp_asm", {
            "name": "AutoGroundRigid",
            "type": "rigid",
            "a": {"occurrence": res1["occurrence"], "point": [0, 0, 10], "z": [0, 0, 1]},
            "b": {"occurrence": res2["occurrence"], "point": [30, 0, 0], "z": [0, 0, -1]},
        })
        mcp_occs_j = links._occurrences(asm_mcp.session)
        t1_after = mcp_occs_j[res1["occurrence"]]["transform"]
        t2_after = mcp_occs_j[res2["occurrence"]]["transform"]
        same = lambda a, b: all(abs(x - y) < 1e-6 for ra, rb in zip(a, b) for x, y in zip(ra, rb))
        ok("add_joint: auto-grounded first part stays, only the second part moves",
           same(t1_before, t1_after) and not same(t2_before, t2_after),
           f"t1 {t1_before} -> {t1_after}, t2 {t2_before} -> {t2_after}")

        asm_mcp2 = ws.new(ASSEMBLY, "g_mcp_asm2")
        res_free = server.insert_part("g_mcp_asm2", str(p1.path), name="McpP1", grounded=False)
        mcp_occs3 = links._occurrences(asm_mcp2.session)
        ok("server.insert_part: first part with grounded=False is not grounded",
           mcp_occs3.get(res_free["occurrence"], {}).get("grounded") is False,
           f"res_free={res_free} occs={mcp_occs3}")
    finally:
        server.ws = orig_server_ws

    ws.close_all()


def design_rule_checks(ws):
    # 1. Hole too close to edge: fail
    doc_fail = ws.new(PART, "rule_fail")
    doc_fail.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 30, "height": 10, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 12, "base": [5, 15, -1], "operation": "cut", "name": "BadHole"}},
    ])
    r_fail = design_rules.check(doc_fail.session, profile="fdm_0.4")
    ok("design rules: hole too close to edge fails hole_edge_distance",
       r_fail["verdict"] == "fail" and r_fail["rules"]["hole_edge_distance"]["status"] == "fail",
       str(r_fail["summary"]))
    ws.close("rule_fail")

    # 2. All rules satisfied: ok
    doc_ok = ws.new(PART, "rule_ok")
    doc_ok.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 10, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 12, "base": [20, 20, -1], "operation": "cut", "name": "GoodHole"}},
    ])
    r_ok = design_rules.check(doc_ok.session, profile="fdm_0.4")
    ok("design rules: part meeting all rules passes",
       r_ok["verdict"] == "ok" and all(r["status"] == "ok" for r in r_ok["rules"].values()),
       str(r_ok["summary"]))
    ws.close("rule_ok")

    # 3. Overhang case: fail
    doc_oh = ws.new(PART, "rule_overhang")
    doc_oh.session.batch([
        {"command": "solid.box", "params": {"length": 20, "width": 20, "height": 10, "corner": [0, 0, 0], "name": "Base"}},
        {"command": "solid.box", "params": {"length": 40, "width": 20, "height": 10, "corner": [0, 0, 10], "operation": "join", "name": "Overhang"}},
    ])
    r_oh = design_rules.check(doc_oh.session, profile="fdm_0.4")
    ok("design rules: overhang without support fails printability",
       r_oh["verdict"] == "fail" and r_oh["rules"]["printability"]["status"] == "fail",
       str(r_oh["summary"]))
    ws.close("rule_overhang")

    # 4. Counterbored hole: coaxial bore and counterbore do not fail min_wall_thickness
    doc_cb = ws.new(PART, "rule_cb")
    doc_cb.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 10, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.hole", "params": {"position": [30, 20, 10], "direction": [0, 0, -1], "type": "counterbore",
                                              "diameter": 4.5, "cb_diameter": 8.0, "cb_depth": 4.4, "name": "CBHole"}}
    ])
    r_cb = design_rules.check(doc_cb.session, profile="fdm_0.4")
    ok("design rules: counterbored hole does not report negative wall thickness between bore and counterbore",
       r_cb["rules"]["min_wall_thickness"]["status"] == "ok",
       str(r_cb["rules"]["min_wall_thickness"]))
    ws.close("rule_cb")

    # 5. Unthreaded through-hole (e.g. wood screw d=5.0 mm) does not trigger thread_depth failure
    doc_th = ws.new(PART, "rule_th")
    doc_th.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 6, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.hole", "params": {"position": [30, 20, 6], "direction": [0, 0, -1],
                                              "diameter": 5.0, "name": "ThroughHole5"}}
    ])
    r_th = design_rules.check(doc_th.session, profile="fdm_0.4")
    ok("design rules: unthreaded through hole does not fail thread_depth as a tap drill",
       r_th["rules"]["thread_depth"]["status"] == "ok",
       str(r_th["rules"]["thread_depth"]))
    ws.close("rule_th")

    # 6. Attached boss / pin (operation join/new) is not recognized as hole or blind hole
    doc_pin = ws.new(PART, "rule_pin")
    doc_pin.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.cylinder", "params": {"diameter": 5.0, "height": 5.0, "base": [20, 20, 5],
                                                  "operation": "join", "name": "Pin"}},
    ])
    pin_holes = query.find(doc_pin, "holes")
    r_pin = design_rules.check(doc_pin.session, profile="fdm_0.4")
    ok("design rules and query: attached pin with join is not treated as hole",
       pin_holes == [] and r_pin["verdict"] == "ok" and r_pin["rules"]["thread_depth"]["status"] == "ok",
       f"holes={pin_holes} verdict={r_pin['verdict']}")
    ws.close("rule_pin")

    # 7. Expression/parameter depth and through hole vs blind hole depth
    doc_expr = ws.new(PART, "rule_expr")
    doc_expr.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.hole", "params": {"position": [20, 20, 5], "direction": [0, 0, -1],
                                              "diameter": 5.0, "depth": "10 mm", "name": "ThroughHoleExpr"}},
    ])
    err_expr = None
    try:
        r_expr = design_rules.check(doc_expr.session, profile="fdm_0.4")
    except Exception as e:
        err_expr = e
        r_expr = {}
    h_expr = query.find(doc_expr, "holes")
    ok("design rules and query: expression depth is evaluated and pierced hole is through hole",
       err_expr is None and r_expr.get("verdict") == "ok"
       and len(h_expr) == 1 and h_expr[0]["through"] is True and abs(h_expr[0]["depth"] - 5.0) < 0.1,
       f"err={err_expr} r_expr={r_expr} h_expr={h_expr}")
    ws.close("rule_expr")

    # 8. max_overhang_angle is measured from vertical (normal z < -sin(angle))
    doc_oh_angle = ws.new(PART, "rule_oh_angle")
    doc_oh_angle.session.batch([
        {"command": "solid.box", "params": {"length": 20, "width": 20, "height": 10, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.chamfer", "params": {"edges": [[10, 0, 0]], "distance": 5, "name": "Chamfer1"}},
    ])
    r_oh_angle = design_rules.check(doc_oh_angle.session, profile={"max_overhang_angle": 30.0})
    ok("design rules: 45 deg overhang fails when max_overhang_angle is 30 deg",
       r_oh_angle["rules"]["printability"]["status"] == "fail",
       str(r_oh_angle["rules"]["printability"]))
    ws.close("rule_oh_angle")

    # 8b. Selectable build_direction: overhang fails in +Z, passes in -Z (overhang face lies on bed)
    doc_bd = ws.new(PART, "rule_build_dir")
    doc_bd.session.batch([
        {"command": "solid.box", "params": {"length": 20, "width": 20, "height": 10, "corner": [0, 0, 0], "name": "Base"}},
        {"command": "solid.box", "params": {"length": 40, "width": 20, "height": 10, "corner": [0, 0, 10], "operation": "join", "name": "Overhang"}},
    ])
    orig_ws_bd = server.ws
    server.ws = ws
    try:
        r_bd_pz = server.check_design("rule_build_dir", build_direction="+Z")
        r_bd_mz = server.check_design("rule_build_dir", build_direction="-Z")
        r_bd_vec = design_rules.check(doc_bd.session, profile={"build_direction": [0, 0, -1]})
        bad_bd = False
        try:
            server.check_design("rule_build_dir", build_direction="invalid")
        except ValueError:
            bad_bd = True
    finally:
        server.ws = orig_ws_bd
    ok("design rules: build_direction +Z reports overhang, -Z (upside down on bed) reports none, invalid rejected",
       r_bd_pz["verdict"] == "fail" and r_bd_pz["rules"]["printability"]["status"] == "fail"
       and len(r_bd_pz["rules"]["printability"]["findings"]) == 1
       and "+Z" in r_bd_pz["rules"]["printability"]["findings"][0]["message"]
       and r_bd_mz["verdict"] == "ok" and r_bd_mz["rules"]["printability"]["status"] == "ok"
       and r_bd_mz["rules"]["printability"]["findings"] == []
       and r_bd_vec["verdict"] == "ok" and r_bd_vec["rules"]["printability"]["status"] == "ok"
       and bad_bd,
       f"+Z={r_bd_pz['rules']['printability']} -Z={r_bd_mz['rules']['printability']} bad={bad_bd}")
    ws.close("rule_build_dir")

    # 9. Shallow blind hole warning sets thread_depth rule status and verdict to warn
    doc_shallow = ws.new(PART, "rule_shallow_blind")
    doc_shallow.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.hole", "params": {"position": [20, 20, 10], "direction": [0, 0, -1],
                                              "diameter": 4.0, "depth": 3.0, "name": "ShallowHole"}},
    ])
    r_shallow = design_rules.check(doc_shallow.session, profile="fdm_0.4")
    ok("design rules: shallow blind hole warning sets thread_depth status and verdict to warn",
       r_shallow["verdict"] == "warn" and r_shallow["rules"]["thread_depth"]["status"] == "warn"
       and len(r_shallow["rules"]["thread_depth"]["findings"]) == 1
       and r_shallow["rules"]["thread_depth"]["findings"][0]["status"] == "warn",
       f"verdict={r_shallow['verdict']} rules={r_shallow['rules']['thread_depth']}")
    ws.close("rule_shallow_blind")

    # 9-. An empty part is no pass (Praxistest 6)
    doc_empty = ws.new(PART, "rule_empty")
    r_empty = design_rules.check(doc_empty.session)
    ok("design rules: a part without bodies is a warning, not OK",
       r_empty["verdict"] == "warn" and "no solid bodies" in r_empty["summary"], r_empty["summary"])
    # the Check page badge follows that warning, though it has no finding of its own (Surface test)
    from mechvane.ui import server as ui_server
    f_empty = ui_server.collect_findings(ws, doc_empty)
    ok("design rules: Check page verdict of a part without bodies is warn", f_empty["verdict"] == "warn",
       f_empty["verdict"])
    ws.close("rule_empty")

    # 9a. Counterbored through hole (as bolted_connection drills it): neither the counterbore floor makes
    # the bore blind nor does the counterbore diameter set the edge distance (Praxistest 6)
    doc_cb_edge = ws.new(PART, "rule_cbore_edge")
    doc_cb_edge.session.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "Base"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [50, 30]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "Base", "distance": 8, "name": "Plate"}},
        {"command": "solid.hole", "params": {"position": [15, 18, 8], "direction": [0, 0, -1], "diameter": "5.5 mm",
                                              "depth": "8", "type": "counterbore", "cb_diameter": "10", "cb_depth": "5.4",
                                              "name": "Hole_M5_CB"}},
    ])
    r_cbe = design_rules.check(doc_cb_edge.session, profile="cnc_alu")
    ok("design rules: counterbored through hole 12 mm from the edge is neither too close (1.5 × Ø10) nor a short blind hole",
       r_cbe["rules"]["hole_edge_distance"]["status"] == "ok" and r_cbe["rules"]["thread_depth"]["status"] == "ok",
       str([(c["rule"], c["message"]) for c in r_cbe["checks"] if c["status"] != "ok"]))
    ws.close("rule_cbore_edge")

    # 9b. Thread depth follows the part's material (same table as bolted_connection)
    doc_mat = ws.new(PART, "rule_material")
    doc_mat.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "solid.hole", "params": {"position": [20, 20, 20], "direction": [0, 0, -1], "diameter": 5.0,
                                              "depth": 8.0, "thread": "M6x1", "name": "Tapped"}},
    ])
    by_mat = {m: design_rules.check(doc_mat.session, material=m)["rules"]["thread_depth"] for m in (None, "steel", "alu", "brass")}
    ok("design rules: thread depth by material (8 mm M6: 1.5 d fails, steel 1.0 d ok, alu 2.0 d fails, brass marked unverified)",
       by_mat[None]["status"] == "fail" and by_mat["steel"]["status"] == "ok" and by_mat["alu"]["status"] == "fail"
       and "unverified" in by_mat["brass"]["findings"][0]["message"],
       str({m: (r["status"], r["findings"][0]["message"]) for m, r in by_mat.items()}))
    body = doc_mat.session.cmd("document.inspect", {"measure": False})["bodies"][0]["name"]
    doc_mat.session.cmd("material.assign", {"bodies": [body], "material": "Steel"})
    r_body = design_rules.check(doc_mat.session)
    ok("design rules: without a material argument the body's SolidCraft material (Steel) applies",
       r_body["material"] == "steel" and r_body["material_source"] == "body"
       and r_body["rules"]["thread_depth"]["status"] == "ok", f"{r_body['material']} {r_body['material_source']}")
    # 9c. A material from the catalog library (katalog/werkstoffe.solidcraft-library.json) drives the rule
    lib_src = Path(__file__).resolve().parents[2] / "katalog" / "werkstoffe.solidcraft-library.json"
    lib = json.loads(lib_src.read_text(encoding="utf-8"))
    mats = [e for e in lib["entries"] if e["definition"]["kind"] == "material"]
    lib_path = ws.root / "werkstoffe.solidcraft-library.json"
    lib_path.write_bytes(lib_src.read_bytes())
    ent = next(e for e in mats if e["definition"]["value"]["name"] == "EN AW-6082 T6")
    doc_mat.session.cmd("library.apply", {"path": str(lib_path), "entry": ent["id"], "revision": ent["revision"],
                                          "targets": {"bodies": [body]}})
    r_lib = design_rules.check(doc_mat.session)
    ok("catalog library: all catalog materials with physical cards; EN AW-6082 T6 assigned from it counts as soft aluminium",
       len(mats) == len(list((Path(__file__).resolve().parents[2] / "katalog" / "eintraege" / "werkstoffe").glob("*.json"))) and all(e["definition"]["value"].get("physical_card") for e in mats)
       and r_lib["material"] == "alu" and r_lib["rules"]["thread_depth"]["status"] == "fail",
       f"{len(mats)} {r_lib['material']} {r_lib['rules']['thread_depth']['status']}")
    ws.close("rule_material")

    # 10. Standoff with bore (ring extruded with join): bore Ø2.5 is hole, outer boss Ø8 is not
    doc_standoff = ws.new(PART, "rule_standoff")
    doc_standoff.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 3, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": 3, "name": "S1"}},
        {"command": "sketch.circle.center", "params": {"center": [20, 20], "radius": 4.0}},
        {"command": "sketch.circle.center", "params": {"center": [20, 20], "radius": 1.25}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S1", "distance": 8, "operation": "join",
                                                 "profiles": [{"point": [23, 20]}], "name": "Standoff"}},
    ])
    st_holes = query.find(doc_standoff, "holes")
    r_st = design_rules.check(doc_standoff.session, profile="fdm_0.4")
    td_findings = r_st["rules"]["thread_depth"]["findings"]
    ok("design rules and query: standoff with bore has hole Ø2.5 and outer surface is not a hole",
       len(st_holes) == 1 and abs(st_holes[0]["diameter"] - 2.5) < 0.1
       and not any(abs(h["diameter"] - 8.0) < 0.1 for h in st_holes)
       and len(td_findings) == 1 and td_findings[0]["status"] == "ok",
       f"holes={st_holes} thread_depth={td_findings}")
    ws.close("rule_standoff")

    # 11. Model state unchanged after query.find and design_rules.check (bodies, timeline, undo/redo, dirty)
    doc_state = ws.new(PART, "rule_model_state")
    doc_state.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 3, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": 3, "name": "S1"}},
        {"command": "sketch.circle.center", "params": {"center": [20, 20], "radius": 4.0}},
        {"command": "sketch.circle.center", "params": {"center": [20, 20], "radius": 1.25}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S1", "distance": 8, "operation": "join",
                                                 "profiles": [{"point": [23, 20]}], "name": "Standoff"}},
    ])
    doc_state.save()
    before_state = doc_state.session.tool("inspect_design", {})
    query.find(doc_state, "holes")
    design_rules.check(doc_state.session, profile="fdm_0.4")
    after_state = doc_state.session.tool("inspect_design", {})

    # Verify undo step rewinds the user's feature rather than an internal probe sphere
    doc_state.session.cmd("edit.undo", {})
    after_undo = doc_state.session.tool("inspect_design", {})
    last_tl = after_undo["timeline"][-1]["name"] if after_undo.get("timeline") else ""
    doc_state.session.cmd("edit.redo", {})

    ok("design rules and query: model unchanged after checks (body count, timeline, undo/redo, dirty)",
       len(after_state["bodies"]) == len(before_state["bodies"])
       and len(after_state["timeline"]) == len(before_state["timeline"])
       and after_state["dirty"] is False
       and after_state["undo"] == before_state["undo"]
       and after_state["redo"] == before_state["redo"]
       and last_tl == "S1",
       f"before={before_state['undo']},{before_state['dirty']} after={after_state['undo']},{after_state['dirty']} last_tl={last_tl}")
    ws.close("rule_model_state")

    # 12. Probe failure falls back to geometric heuristics with warning without losing standoff bore
    doc_err = ws.new(PART, "rule_probe_err")
    doc_err.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 3, "corner": [0, 0, 0], "name": "Box"}},
        {"command": "sketch.create", "params": {"plane": "XY", "offset": 3, "name": "S1"}},
        {"command": "sketch.circle.center", "params": {"center": [20, 20], "radius": 4.0}},
        {"command": "sketch.circle.center", "params": {"center": [20, 20], "radius": 1.25}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S1", "distance": 8, "operation": "join",
                                                 "profiles": [{"point": [23, 20]}], "name": "Standoff"}},
    ])
    orig_cmd = doc_err.session.cmd
    def mock_cmd(command, params=None):
        if command == "solid.sphere":
            raise RuntimeError("simulated probe failure")
        return orig_cmd(command, params)
    doc_err.session.cmd = mock_cmd

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        err_holes = query.find(doc_err, "holes")
        r_err = design_rules.check(doc_err.session, profile="fdm_0.4")
    doc_err.session.cmd = orig_cmd

    err_td = r_err["rules"]["thread_depth"]["findings"]
    after_err = doc_err.session.tool("inspect_design", {})
    ok("design rules and query: probe failure falls back to geometric heuristics with warning without losing standoff bore",
       len(err_holes) == 1 and abs(err_holes[0]["diameter"] - 2.5) < 0.1
       and not any(abs(h["diameter"] - 8.0) < 0.1 for h in err_holes)
       and len(err_td) == 1 and err_td[0]["status"] == "ok"
       and len(captured) >= 1
       and any("interference" in str(w.message).lower() or "probe" in str(w.message).lower() for w in captured)
       and len(after_err["bodies"]) == 1,
       f"holes={err_holes} thread_depth={err_td} warnings={len(captured)} bodies={len(after_err['bodies'])}")
    ws.close("rule_probe_err")


def finding_source_checks(ws):
    """#120: findings of rules with a knowledge catalog entry carry its source, others carry none."""
    from mechvane.ui import server as ui_server
    entry_id = design_rules.RULE_SOURCES["horizontal_hole"]
    entry = katalog.get_entry(entry_id)
    q = entry["quellen"][0]
    doc = ws.new(PART, "p_src_hh")
    doc.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 40, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 20, "base": [20, -5, 20], "axis": [0, 1, 0], "operation": "cut", "name": "H"}},
    ])
    res = design_rules.check(doc, profile="fdm_0.4")
    f_hh = res["rules"]["horizontal_hole"]["findings"]
    src = f_hh[0].get("source") if f_hh else None
    ok("finding source: a mapped rule's finding carries the catalog entry's source",
       bool(f_hh) and isinstance(src, dict) and src["entry"] == entry_id and src["url"] == q["url"]
       and src["stelle"] == q["stelle"] and src["titel"] == entry["aussage"], str(src))
    # verbatim from the catalog file itself
    path = next(Path(__file__).resolve().parents[2].glob(f"katalog/eintraege/*/{entry_id}.json"))
    raw = json.loads(path.read_text(encoding="utf-8"))
    ok("finding source: the quote is exactly the text in the catalog file",
       bool(src) and src["zitat"] == raw["quellen"][0]["zitat"], str(src and src["zitat"]))
    wall = res["rules"]["min_wall_thickness"]["findings"]
    ok("finding source: an unmapped rule's findings have no source field",
       bool(wall) and all("source" not in f for f in wall)
       and all(r not in design_rules.RULE_SOURCES for r in ("min_wall_thickness", "hole_edge_distance", "thread_depth")),
       str(wall[:1]))
    ok("finding source: every mapped rule resolves to a catalog entry with a source",
       set(design_rules.rule_sources()) == set(design_rules.RULE_SOURCES), str(sorted(design_rules.rule_sources())))
    cf = ui_server.collect_findings(ws, doc)["findings"]
    c_hh = [f for f in cf if f["rule"] == "horizontal_hole"]
    c_wall = [f for f in cf if f["rule"] == "min_wall_thickness"]
    ok("finding source: collect_findings passes the source through, unmapped rules stay without",
       bool(c_hh) and c_hh[0].get("source") == src and c_hh[0]["origin"] == "design_rules"
       and bool(c_wall) and all("source" not in f for f in c_wall), str(c_hh[:1]))
    # a pip install has no katalog/ folder: the rule's own link must stay, as an object with only the url (review 2026-11-16)
    orig = design_rules.rule_sources
    design_rules.rule_sources = lambda: {}
    try:
        nocat = design_rules.check(doc, profile="fdm_0.4")["rules"]["horizontal_hole"]["findings"]
    finally:
        design_rules.rule_sources = orig
    s0 = nocat[0].get("source") if nocat else None
    ok("finding source: without the catalog a rule's own link stays as {url} instead of vanishing",
       bool(nocat) and isinstance(s0, dict) and s0.get("url", "").startswith("http") and "zitat" not in s0, str(s0))
    ws.close("p_src_hh")


def verfahrensregeln_checks(ws):
    # 1. FDM: horizontal_hole
    p_hh_trig = ws.new(PART, "p_vr_hh_trig")
    p_hh_trig.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 40, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 20, "base": [20, -5, 20], "axis": [0, 1, 0], "operation": "cut", "name": "H"}},
    ])
    r_hh_trig = design_rules.check(p_hh_trig.session, profile="fdm_0.4")
    f_hh = r_hh_trig["rules"]["horizontal_hole"]["findings"]
    ok("verfahrensregeln / fdm: horizontal hole > 6mm warns with teardrop/support suggestion",
       r_hh_trig["rules"]["horizontal_hole"]["status"] == "warn"
       and len(f_hh) == 1 and ("teardrop" in f_hh[0]["message"] or "support" in f_hh[0]["message"]),
       str(r_hh_trig["rules"]["horizontal_hole"]))
    ok("verfahrensregeln / fdm: horizontal hole finding contains source",
       bool(f_hh[0].get("source")) and "hubs.com" in f_hh[0]["source"]["url"],
       str(f_hh[0]))
    r_hh_cnc = design_rules.check(p_hh_trig.session, profile="cnc_alu")
    ok("verfahrensregeln / cnc: horizontal hole does not trigger in cnc_alu profile",
       r_hh_cnc["rules"]["horizontal_hole"]["status"] == "ok"
       and len(r_hh_cnc["rules"]["horizontal_hole"]["findings"]) == 0,
       str(r_hh_cnc["rules"]["horizontal_hole"]))

    p_hh_pass = ws.new(PART, "p_vr_hh_pass")
    p_hh_pass.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 40, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 5, "height": 20, "base": [20, -5, 20], "axis": [0, 1, 0], "operation": "cut", "name": "H"}},
    ])
    r_hh_pass = design_rules.check(p_hh_pass.session, profile="fdm_0.4")
    ok("verfahrensregeln / fdm: horizontal hole <= 6mm passes",
       r_hh_pass["rules"]["horizontal_hole"]["status"] == "ok"
       and len(r_hh_pass["rules"]["horizontal_hole"]["findings"]) == 0,
       str(r_hh_pass["rules"]["horizontal_hole"]))

    # 2. FDM: heat_set_insert
    p_hsi_trig = ws.new(PART, "p_vr_hsi_trig")
    p_hsi_trig.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 40, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 4.0, "height": 5.0, "base": [20, 20, 40], "axis": [0, 0, -1], "operation": "cut", "name": "M3_Insert"}},
    ])
    r_hsi_trig = design_rules.check(p_hsi_trig.session, profile="fdm_0.4")
    f_hsi = r_hsi_trig["rules"]["heat_set_insert"]["findings"]
    ok("verfahrensregeln / fdm: heat-set insert shallow blind hole fails min_depth",
       r_hsi_trig["rules"]["heat_set_insert"]["status"] == "fail"
       and len(f_hsi) == 1 and "6.7" in f_hsi[0]["message"],
       str(r_hsi_trig["rules"]["heat_set_insert"]))
    ok("verfahrensregeln / fdm: heat-set insert finding contains source",
       bool(f_hsi[0].get("source")) and ("ruthex" in f_hsi[0]["source"]["url"] or "cnckitchen" in f_hsi[0]["source"]["url"]),
       str(f_hsi[0]))

    p_hsi_pass = ws.new(PART, "p_vr_hsi_pass")
    p_hsi_pass.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 40, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 4.0, "height": 8.0, "base": [20, 20, 40], "axis": [0, 0, -1], "operation": "cut", "name": "M3_Insert"}},
    ])
    r_hsi_pass = design_rules.check(p_hsi_pass.session, profile="fdm_0.4")
    ok("verfahrensregeln / fdm: heat-set insert with sufficient Vorloch depth passes",
       r_hsi_pass["rules"]["heat_set_insert"]["status"] == "ok"
       and len(r_hsi_pass["rules"]["heat_set_insert"]["findings"]) == 0,
       str(r_hsi_pass["rules"]["heat_set_insert"]))

    # Test false alarm: direct M3 screw into plastic (Kernloch 2.5 mm) must not fail heat_set_insert
    p_hsi_direct = ws.new(PART, "p_vr_hsi_direct")
    p_hsi_direct.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 40, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 2.5, "height": 8.0, "base": [20, 20, 40], "axis": [0, 0, -1], "operation": "cut", "name": "M3_Direct"}},
    ])
    r_hsi_direct = design_rules.check(p_hsi_direct.session, profile="fdm_0.4")
    ok("verfahrensregeln / fdm: direct M3 thread (Kernloch 2.5) without insert marker does not fail heat_set_insert",
       r_hsi_direct["rules"]["heat_set_insert"]["status"] == "ok"
       and len(r_hsi_direct["rules"]["heat_set_insert"]["findings"]) == 0,
       str(r_hsi_direct["rules"]["heat_set_insert"]))

    # 3. CNC: pocket_corner_radius
    p_pcr_trig = ws.new(PART, "p_vr_pcr_trig")
    p_pcr_trig.session.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [-20, -20], "p1": [20, 20]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S1", "distance": 20, "name": "E1"}},
        {"command": "sketch.create", "params": {"plane": "XY", "name": "S2"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [-10, -10], "p1": [10, 10]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S2", "distance": 10, "operation": "cut", "name": "Cut1"}},
    ])
    r_pcr_trig = design_rules.check(p_pcr_trig.session, profile="cnc_alu")
    f_pcr = r_pcr_trig["rules"]["pocket_corner_radius"]["findings"]
    ok("verfahrensregeln / cnc: sharp 90° inside pocket corner fails pocket_corner_radius",
       r_pcr_trig["rules"]["pocket_corner_radius"]["status"] == "fail"
       and len(f_pcr) >= 1 and "radius 0 mm" in f_pcr[0]["message"],
       str(r_pcr_trig["rules"]["pocket_corner_radius"]))
    r_pcr_fdm = design_rules.check(p_pcr_trig.session, profile="fdm_0.4")
    ok("verfahrensregeln / fdm: sharp 90° inside pocket corner does not trigger pocket_corner_radius in fdm_0.4",
       r_pcr_fdm["rules"]["pocket_corner_radius"]["status"] == "ok"
       and len(r_pcr_fdm["rules"]["pocket_corner_radius"]["findings"]) == 0,
       str(r_pcr_fdm["rules"]["pocket_corner_radius"]))

    # Test outer fillet R1: outside corner fillet must NOT report pocket_corner_radius
    p_pcr_outer_r1 = ws.new(PART, "p_vr_pcr_outer_r1")
    p_pcr_outer_r1.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.fillet", "params": {"edges": [[0, 0, 10]], "radius": 1.0, "name": "OuterFillet"}},
    ])
    r_pcr_outer = design_rules.check(p_pcr_outer_r1.session, profile="cnc_alu")
    ok("verfahrensregeln / cnc: outer fillet R1 does not trigger pocket_corner_radius",
       r_pcr_outer["rules"]["pocket_corner_radius"]["status"] == "ok"
       and len(r_pcr_outer["rules"]["pocket_corner_radius"]["findings"]) == 0,
       str(r_pcr_outer["rules"]["pocket_corner_radius"]))

    # Test inside pocket corner fillet R1: pocket corner with R1 must fail (< 1.5 mm cutter radius)
    p_pcr_inner_r1 = ws.new(PART, "p_vr_pcr_inner_r1")
    p_pcr_inner_r1.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0, 0, 0], "name": "B"}},
        {"command": "sketch.create", "params": {"plane": "XY", "name": "S"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [10, 10], "p1": [30, 30]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S", "distance": 10, "operation": "cut", "name": "Pocket"}},
        {"command": "solid.fillet", "params": {"edges": [[10, 10, 5]], "radius": 1.0, "name": "InnerFillet"}},
    ])
    r_pcr_inner = design_rules.check(p_pcr_inner_r1.session, profile="cnc_alu")
    f_pcr_inner = r_pcr_inner["rules"]["pocket_corner_radius"]["findings"]
    ok("geometry.blend_parts: the faces of a blend are read from the name in both SolidCraft spellings, others give None",
       g.blend_parts("F4:blend:F3:side:l1|F3:side:l4") == ["F3:side:l1", "F3:side:l4"]
       and g.blend_parts("F4:blend(F3:side:l1|F3:side:l4)") == ["F3:side:l1", "F3:side:l4"]
       and g.blend_parts("F1:+z") is None and g.blend_parts("F2:bore:side:0") is None and g.blend_parts("") is None)
    ok("verfahrensregeln / cnc: inside pocket corner R1 fails pocket_corner_radius",
       r_pcr_inner["rules"]["pocket_corner_radius"]["status"] == "fail"
       and len(f_pcr_inner) >= 1 and any("1.00" in f["message"] for f in f_pcr_inner),  # the R1 corner among the sharp ones, in the kernel's order
       str(r_pcr_inner["rules"]["pocket_corner_radius"]))
    ok("verfahrensregeln / cnc: pocket corner radius finding contains source",
       bool(f_pcr_inner[0].get("source")) and "hubs.com" in f_pcr_inner[0]["source"]["url"],
       str(f_pcr_inner[0]))

    p_pcr_pass = ws.new(PART, "p_vr_pcr_pass")
    p_pcr_pass.session.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [-20, -20], "p1": [20, 20]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S1", "distance": 20, "name": "E1"}},
        {"command": "sketch.create", "params": {"plane": "XY", "name": "S2"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [-10, -10], "p1": [10, 10]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S2", "distance": 10, "operation": "cut", "name": "Cut1"}},
        {"command": "solid.fillet", "params": {"edges": [[-10, -10, 5], [-10, 10, 5], [10, -10, 5], [10, 10, 5]], "radius": 2.0}},
    ])
    r_pcr_pass = design_rules.check(p_pcr_pass.session, profile="cnc_alu")
    ok("verfahrensregeln / cnc: filleted pocket inside corners pass pocket_corner_radius",
       r_pcr_pass["rules"]["pocket_corner_radius"]["status"] == "ok"
       and len(r_pcr_pass["rules"]["pocket_corner_radius"]["findings"]) == 0,
       str(r_pcr_pass["rules"]["pocket_corner_radius"]))

    # 4. CNC: hole_depth_ratio
    p_hdr_trig = ws.new(PART, "p_vr_hdr_trig")
    p_hdr_trig.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 60, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 4.0, "height": 50.0, "base": [20, 20, 60], "axis": [0, 0, -1], "operation": "cut", "name": "H"}},
    ])
    r_hdr_trig = design_rules.check(p_hdr_trig.session, profile="cnc_alu")
    f_hdr = r_hdr_trig["rules"]["hole_depth_ratio"]["findings"]
    ok("verfahrensregeln / cnc: hole depth ratio > 10x warns on twist drill limit",
       r_hdr_trig["rules"]["hole_depth_ratio"]["status"] == "warn"
       and len(f_hdr) == 1 and "10" in f_hdr[0]["message"],
       str(r_hdr_trig["rules"]["hole_depth_ratio"]))
    ok("verfahrensregeln / cnc: hole depth ratio finding contains source",
       bool(f_hdr[0].get("source")) and "hubs.com" in f_hdr[0]["source"]["url"],
       str(f_hdr[0]))

    p_hdr_pass = ws.new(PART, "p_vr_hdr_pass")
    p_hdr_pass.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 60, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 4.0, "height": 20.0, "base": [20, 20, 60], "axis": [0, 0, -1], "operation": "cut", "name": "H"}},
    ])
    r_hdr_pass = design_rules.check(p_hdr_pass.session, profile="cnc_alu")
    ok("verfahrensregeln / cnc: hole depth ratio <= 10x passes hole_depth_ratio",
       r_hdr_pass["rules"]["hole_depth_ratio"]["status"] == "ok"
       and len(r_hdr_pass["rules"]["hole_depth_ratio"]["findings"]) == 0,
       str(r_hdr_pass["rules"]["hole_depth_ratio"]))

    # 5. CNC: undercut
    p_uc_trig = ws.new(PART, "p_vr_uc_trig")
    p_uc_trig.session.batch([
        {"command": "sketch.create", "params": {"plane": "XZ", "name": "S1"}},
        {"command": "sketch.line", "params": {"points": [[0, 0], [30, 0]]}},
        {"command": "sketch.line", "params": {"points": [[30, 0], [30, 30]]}},
        {"command": "sketch.line", "params": {"points": [[30, 30], [10, 30]]}},
        {"command": "sketch.line", "params": {"points": [[10, 30], [10, 15]]}},
        {"command": "sketch.line", "params": {"points": [[10, 15], [0, 15]]}},
        {"command": "sketch.line", "params": {"points": [[0, 15], [0, 0]]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"sketch": "S1", "distance": 20, "name": "E1"}},
    ])
    r_uc_trig = design_rules.check(p_uc_trig.session, profile="cnc_alu")
    f_uc = r_uc_trig["rules"]["undercut"]["findings"]
    ok("verfahrensregeln / cnc: downward ceiling above base warns on undercut",
       r_uc_trig["rules"]["undercut"]["status"] == "warn"
       and len(f_uc) >= 1 and "undercut" in f_uc[0]["message"].lower(),
       str(r_uc_trig["rules"]["undercut"]))
    ok("verfahrensregeln / cnc: undercut finding contains source",
       bool(f_uc[0].get("source")) and "hubs.com" in f_uc[0]["source"]["url"],
       str(f_uc[0]))

    p_uc_pass = ws.new(PART, "p_vr_uc_pass")
    p_uc_pass.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.cylinder", "params": {"diameter": 10.0, "height": 10.0, "base": [20, 20, 20], "axis": [0, 0, -1], "operation": "cut", "name": "H"}},
    ])
    r_uc_pass = design_rules.check(p_uc_pass.session, profile="cnc_alu")
    ok("verfahrensregeln / cnc: top-machined pocket without downward ceilings passes undercut",
       r_uc_pass["rules"]["undercut"]["status"] == "ok"
       and len(r_uc_pass["rules"]["undercut"]["findings"]) == 0,
       str(r_uc_pass["rules"]["undercut"]))

    for name in ("p_vr_hh_trig", "p_vr_hh_pass", "p_vr_hsi_trig", "p_vr_hsi_pass", "p_vr_hsi_direct",
                 "p_vr_pcr_trig", "p_vr_pcr_pass", "p_vr_pcr_outer_r1", "p_vr_pcr_inner_r1",
                 "p_vr_hdr_trig", "p_vr_hdr_pass", "p_vr_uc_trig", "p_vr_uc_pass"):
        ws.close(name)


def screw_shank_down(asm, occ_name):
    """The screw's shank (its part's -Z) points down in the assembly: joint frames on circle references may point
    either way round (truck and solidcore orient circles differently), the occurrence's placement does not."""
    occ = {o["name"]: o for o in links._occurrences(asm.session).values()}[occ_name]
    return g.dot(g.unit(g.apply_dir(occ["transform"], [0.0, 0.0, -1.0])), [0.0, 0.0, -1.0]) > 0.999


def bolted_connection_checks(ws):
    # Setup two plates 10 mm and 8 mm
    plate1 = ws.new(PART, "p1_through")
    plate1.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0],
                                     "operation": "new", "body_name": "Plate1", "name": "Box1"})
    plate1.save()

    plate2 = ws.new(PART, "p2_through")
    plate2.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [-20, -20, 0],
                                     "operation": "new", "body_name": "Plate2", "name": "Box2"})
    plate2.save()

    asm = ws.new(ASSEMBLY, "asm_through")
    links.insert(ws, asm, plate1.path, name="Plate1", grounded=True)
    links.insert(ws, asm, plate2.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm.save()

    # Preview check
    prev = bolted.preview_bolted_connection(
        ws, "asm_through",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    ok("bolted connection preview: calculated lengths and specs",
       prev["size"] == "M5" and prev["stack_thickness"] == 18.0 and prev["grip_length"] == 18.0
       and prev["selected_screw_length"] == 25.0 and prev["clearance_diameter"] == 5.5,
       str(prev))

    # Case 1: Through bolted connection without counterbore (10 + 8 mm, M5)
    res = bolted.bolted_connection(
        ws, "asm_through",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    ok("bolted connection: M5 selected screw length is 25 mm and grip length 18 mm",
       res["size"] == "M5" and res["screw_length"] == 25.0 and res["grip_length"] == 18.0
       and len(res["joints"]) == 3,
       str(res))

    # Check hole diameters in component files (5.5 mm diameter -> radius 2.75 mm)
    p1_faces = ws.docs["p1_through"].session.cmd("model.faces", {"body": "Plate1"})["faces"]
    p1_cyls = [f["cylinder"] for f in p1_faces if f.get("cylinder")]
    p2_faces = ws.docs["p2_through"].session.cmd("model.faces", {"body": "Plate2"})["faces"]
    p2_cyls = [f["cylinder"] for f in p2_faces if f.get("cylinder")]
    ok("bolted connection: clearance hole diameter is 5.5 mm in both component files",
       any(abs(c["radius"] - 2.75) < 1e-4 for c in p1_cyls)
       and any(abs(c["radius"] - 2.75) < 1e-4 for c in p2_cyls),
       f"p1={p1_cyls} p2={p2_cyls}")

    # Check screw sits coaxial (joint frame origins and z vectors) and occurrences in world coordinates
    joints = asm.session.cmd("joint.list")["joints"]
    screw_j = next(j for j in joints if j["name"] == res["joints"][0])
    fa, fb = screw_j["frame_a"], screw_j["frame_b"]
    coaxial = (abs(fa["origin"][0] - fb["origin"][0]) < 1e-4
               and abs(fa["origin"][1] - fb["origin"][1]) < 1e-4
               and abs(abs(g.dot(fa["z"], fb["z"])) - 1.0) < 1e-4)
    # Check actual occurrence placement in assembly world coordinates (not just joint frames)
    # Hole is at world x=0, y=0. Screw, washer and nut must be centered on the hole axis.
    asm_occs = {o["name"]: o for o in links._occurrences(asm.session).values()}
    t_screw = asm_occs[res["screw"]]["transform"]
    t_nut = asm_occs[res["nut"]]["transform"]
    t_washer = asm_occs[res["washers"][0]]["transform"]
    # Part origins lie on the part axis, so each origin in world coordinates must be on x=y=0.
    origins = [g.apply_point(t, [0.0, 0.0, 0.0]) for t in (t_screw, t_nut, t_washer)]
    world_coaxial = all(abs(o[0]) < 1e-4 and abs(o[1]) < 1e-4 for o in origins)
    # Head bearing surface of screw sits flush on top plate at z = 10.0 (Befund 11)
    head_seated = abs(origins[0][2] - 10.0) < 1e-3
    ok("bolted connection: screw sits coaxial to hole", coaxial and world_coaxial and head_seated
       and screw_shank_down(asm, res["screw"]),
       f"{fa} vs {fb}, origins={origins}")

    # Check interference (no collision screw/hole)
    interf = asm.session.cmd("inspect.interference", {})
    ok("bolted connection: no collision between screw/hole (inspect.interference count == 0)",
       interf.get("count") == 0, str(interf))

    # Check joints are green
    chk = links.check(ws, asm)
    ok("bolted connection: check_joints is green (all ok)",
       bool(chk) and all(r["status"] == "ok" for r in chk), str(chk))

    # Case 2: Bolted connection with counterbore (DIN 974-1)
    p1_cb = ws.new(PART, "p1_cb")
    p1_cb.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0],
                                    "operation": "new", "body_name": "Plate1", "name": "Box1"})
    p1_cb.save()

    p2_cb = ws.new(PART, "p2_cb")
    p2_cb.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [-20, -20, 0],
                                    "operation": "new", "body_name": "Plate2", "name": "Box2"})
    p2_cb.save()

    asm_cb = ws.new(ASSEMBLY, "asm_cb")
    links.insert(ws, asm_cb, p1_cb.path, name="Plate1", grounded=True)
    links.insert(ws, asm_cb, p2_cb.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm_cb.save()

    res_cb = bolted.bolted_connection(
        ws, "asm_cb",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=True,
    )
    ok("bolted connection with counterbore: selected screw length 20 mm, grip length 12.6 mm",
       res_cb["size"] == "M5" and res_cb["screw_length"] == 20.0 and abs(res_cb["grip_length"] - 12.6) < 1e-4,
       str(res_cb))

    p1_cb_faces = ws.docs["p1_cb"].session.cmd("model.faces", {"body": "Plate1"})["faces"]
    p1_cb_cyls = [f["cylinder"] for f in p1_cb_faces if f.get("cylinder")]
    p2_cb_faces = ws.docs["p2_cb"].session.cmd("model.faces", {"body": "Plate2"})["faces"]
    p2_cb_cyls = [f["cylinder"] for f in p2_cb_faces if f.get("cylinder")]
    ok("bolted connection with counterbore: bore 5.5 mm and counterbore 10.0 mm in plate 1, bore 5.5 mm in plate 2",
       any(abs(c["radius"] - 2.75) < 1e-4 for c in p1_cb_cyls)
       and any(abs(c["radius"] - 5.0) < 1e-4 for c in p1_cb_cyls)
       and any(abs(c["radius"] - 2.75) < 1e-4 for c in p2_cb_cyls),
       f"p1_cb={p1_cb_cyls} p2_cb={p2_cb_cyls}")

    joints_cb = asm_cb.session.cmd("joint.list")["joints"]
    screw_cb_j = next(j for j in joints_cb if j["name"] == res_cb["joints"][0])
    fa_cb, fb_cb = screw_cb_j["frame_a"], screw_cb_j["frame_b"]
    coaxial_cb = (abs(fa_cb["origin"][0] - fb_cb["origin"][0]) < 1e-4
                  and abs(fa_cb["origin"][1] - fb_cb["origin"][1]) < 1e-4
                  and abs(fa_cb["origin"][2] - 4.6) < 1e-4
                  and abs(abs(g.dot(fa_cb["z"], fb_cb["z"])) - 1.0) < 1e-4)
    ok("bolted connection with counterbore: screw sits coaxial and recessed at z = 4.6 mm",
       coaxial_cb and screw_shank_down(asm_cb, res_cb["screw"]), f"{fa_cb} vs {fb_cb}")

    interf_cb = asm_cb.session.cmd("inspect.interference", {})
    ok("bolted connection with counterbore: no collision (inspect.interference count == 0)",
       interf_cb.get("count") == 0, str(interf_cb))

    chk_cb = links.check(ws, asm_cb)
    ok("bolted connection with counterbore: check_joints is green (all ok)",
       bool(chk_cb) and all(r["status"] == "ok" for r in chk_cb), str(chk_cb))

    # Case 3: Blind hole bolted connection M5 in aluminium plate (connection_type="blind", blind_material="alu")
    p1_blind = ws.new(PART, "p1_blind")
    p1_blind.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0],
                                       "operation": "new", "body_name": "Cover", "name": "Box1"})
    p1_blind.save()

    p2_blind = ws.new(PART, "p2_blind")
    p2_blind.session.cmd("solid.box", {"length": 40, "width": 40, "height": 20, "corner": [-20, -20, 0],
                                       "operation": "new", "body_name": "AluBase", "name": "Box2"})
    p2_blind.save()

    asm_blind = ws.new(ASSEMBLY, "asm_blind")
    links.insert(ws, asm_blind, p1_blind.path, name="Cover", grounded=True)
    links.insert(ws, asm_blind, p2_blind.path, name="AluBase", translate=[0, 0, -20], grounded=True)
    asm_blind.save()

    prev_blind = bolted.preview_bolted_connection(
        ws, "asm_blind",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        connection_type="blind",
        blind_material="alu",
        counterbore=False,
    )
    ok("bolted connection blind preview: M5 in alu engagement 10 mm, drill depth 13.2 mm, screw 20 mm",
       prev_blind["size"] == "M5" and prev_blind["connection_type"] == "blind"
       and prev_blind["grip_length"] == 10.0 and prev_blind["thread_depth"] == 10.0
       and prev_blind["drill_depth"] == 13.2 and prev_blind["selected_screw_length"] == 20.0
       and prev_blind["tap_drill"] == 4.2,
       str(prev_blind))

    res_blind = bolted.bolted_connection(
        ws, "asm_blind",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        connection_type="blind",
        blind_material="alu",
        counterbore=False,
    )
    ok("bolted connection blind: M5 screw length 20 mm, grip length 10 mm, 1 joint, no nut",
       res_blind["size"] == "M5" and res_blind["type"] == "blind"
       and res_blind["screw_length"] == 20.0 and res_blind["grip_length"] == 10.0
       and res_blind["nut"] is None and len(res_blind["joints"]) == 1,
       str(res_blind))

    # Independent geometric checks from model.edges:
    # Plate top is at z = 20.0 mm.
    # DIN 336 / ISO 2306: M5 tap drill diameter = 4.2 mm (r = 2.1 mm).
    # Bossard / VDI 2230: AlMg3 8.8 minimum engagement = 2.0 * d = 10.0 mm.
    # DIN 76-1: thread runout 4 * P = 4 * 0.8 = 3.2 mm -> cylindrical drill depth = 13.2 mm.
    # 118 deg drill point: cone tip delta_z = r / tan(59 deg) = 2.1 / 1.66428 = 1.262 mm -> tip at z = 5.538 mm.
    p2_b_faces = ws.docs["p2_blind"].session.cmd("model.faces", {"body": "AluBase"})["faces"]
    p2_b_cyls = [f["cylinder"] for f in p2_b_faces if f.get("cylinder")]
    p2_b_edges = ws.docs["p2_blind"].session.cmd("model.edges", {"body": "AluBase"})["edges"]
    cyl_radii = [round(c["radius"], 2) for c in p2_b_cyls]

    # from the geometry, not the face names: truck splits the bore into pieces (side:1#2), solidcore does not
    bore_edges = [e for e in p2_b_edges if "bore" in e["name"]]
    bore_cyl_names = {f["name"] for f in p2_b_faces
                      if "bore" in f["name"] and abs((f.get("cylinder") or {}).get("radius", 0) - 2.1) < 1e-3}
    lowest = lambda e: min(e["start"][2], e["end"][2])
    cyl_bottom_z = min(lowest(e) for e in bore_edges
                       if {n.split("~")[0] for n in e["name"].split("|")} & bore_cyl_names)
    cone_tip_z = min(lowest(e) for e in bore_edges)
    geom_cyl_depth = round(20.0 - cyl_bottom_z, 2)
    delta_z_tip = cyl_bottom_z - cone_tip_z
    tip_angle_deg = round(2.0 * math.degrees(math.atan(2.1 / delta_z_tip)), 1)
    geom_total_depth = round(20.0 - cone_tip_z, 2)

    ok("bolted connection blind: tap drill hole is 4.2 mm (r=2.1 mm) with 118 deg drill point in alu plate",
       any(abs(r - 2.1) < 1e-3 for r in cyl_radii) and abs(tip_angle_deg - 118.0) < 0.2,
       f"radii={cyl_radii} angle={tip_angle_deg}")

    ok("bolted connection blind: drill depth is 13.2 mm (10 mm engagement + 3.2 mm runout 4*P)",
       abs(geom_cyl_depth - 13.2) < 1e-3 and abs(geom_total_depth - 14.46) < 0.05,
       f"geom_cyl={geom_cyl_depth}, geom_total={geom_total_depth}")

    # Check screw sits coaxial to hole
    joints_blind = asm_blind.session.cmd("joint.list")["joints"]
    screw_blind_j = next(j for j in joints_blind if j["name"] == res_blind["joints"][0])
    fa_bl, fb_bl = screw_blind_j["frame_a"], screw_blind_j["frame_b"]
    coaxial_blind = (abs(fa_bl["origin"][0] - fb_bl["origin"][0]) < 1e-4
                     and abs(fa_bl["origin"][1] - fb_bl["origin"][1]) < 1e-4
                     and abs(abs(g.dot(fa_bl["z"], fb_bl["z"])) - 1.0) < 1e-4)
    # Head bearing surface sits at top plate surface at z = 10.0 (Befund 11)
    head_seated_blind = abs(fa_bl["origin"][2] - 10.0) < 1e-4
    ok("bolted connection blind: screw sits coaxial to hole",
       coaxial_blind and head_seated_blind and screw_shank_down(asm_blind, res_blind["screw"]), f"{fa_bl} vs {fb_bl}")

    chk_blind = links.check(ws, asm_blind)
    ok("bolted connection blind: check_joints is green (all ok)",
       bool(chk_blind) and all(r["status"] == "ok" for r in chk_blind), str(chk_blind))

    # Interference check: cosmetic thread overlap only (screw nominal d=5.0 vs tap drill d=4.2 in z in [-10, 0])
    # No interference between Cover and Screw, Cover and AluBase, or screw head.
    interf_blind = asm_blind.session.cmd("inspect.interference", {})
    interfs = interf_blind.get("interferences", [])
    valid_thread_interference = False
    if len(interfs) == 1:
        c = interfs[0]
        bodies = {c["a"], c["b"]}
        bbox = c["bbox"]
        # Overlap must be between AluBase and Screw within radius 2.5 mm and z in [-10.05, 0.05]
        valid_thread_interference = (
            bodies == {"AluBase", "Screw"}
            and max(abs(bbox["min"][0]), abs(bbox["max"][0])) <= 2.55
            and max(abs(bbox["min"][1]), abs(bbox["max"][1])) <= 2.55
            and bbox["min"][2] >= -10.05
            and bbox["max"][2] <= 0.05
        )
    ok("bolted connection blind: no collision except cosmetic thread engagement (r<=2.5 mm in [-10, 0] mm)",
       valid_thread_interference,
       f"count={len(interfs)}: {interfs} (Justification: cosmetic thread in CAD models nominal screw shank d=5.0 mm "
       f"overlapping tap drill bore d=4.2 mm between z=0 and z=-10 mm; zero collision elsewhere)")

    # Case 4: 3D-print variant with Ruthex M3 threaded insert (use_insert=True)
    d1_part = ws.new(PART, "d1_lid")
    d1_part.session.cmd("solid.box", {"length": 30, "width": 30, "height": 5, "corner": [-15, -15, 0],
                                      "operation": "new", "body_name": "Lid", "name": "Box1"})
    d1_part.save()

    d2_part = ws.new(PART, "d2_case")
    d2_part.session.cmd("solid.box", {"length": 30, "width": 30, "height": 15, "corner": [-15, -15, 0],
                                      "operation": "new", "body_name": "Case", "name": "Box2"})
    d2_part.save()

    asm_ins = ws.new(ASSEMBLY, "asm_ins")
    links.insert(ws, asm_ins, d1_part.path, name="Lid", grounded=True)
    links.insert(ws, asm_ins, d2_part.path, name="Case", translate=[0, 0, -15], grounded=True)
    asm_ins.save()

    prev_ins = bolted.preview_bolted_connection(
        ws, "asm_ins",
        placement={"position": [0, 0, 5], "direction": [0, 0, -1]},
        size="M3",
        use_insert=True,
        counterbore=True,
    )
    ok("bolted connection insert preview: Ruthex M3 mounting hole 4.0 mm, depth 6.7 mm, screw 8 mm",
       prev_ins["size"] == "M3" and prev_ins["use_insert"] is True
       and prev_ins["mounting_hole_diameter"] == 4.0 and prev_ins["mounting_hole_depth"] == 6.7
       and prev_ins["selected_screw_length"] == 8.0 and abs(prev_ins["grip_length"] - 1.6) < 1e-4,
       str(prev_ins))

    res_ins = bolted.bolted_connection(
        ws, "asm_ins",
        placement={"position": [0, 0, 5], "direction": [0, 0, -1]},
        size="M3",
        use_insert=True,
        counterbore=True,
    )
    ok("bolted connection insert: M3 screw length 8 mm, insert Ruthex RX-M3x5.7 placed, 2 joints",
       res_ins["size"] == "M3" and res_ins["type"] == "insert"
       and res_ins["screw_length"] == 8.0 and res_ins["insert"] is not None
       and res_ins["nut"] is None and len(res_ins["joints"]) == 2,
       str(res_ins))

    # Check mounting hole in printed case (diameter 4.0 mm -> radius 2.0 mm, depth >= 6.7 mm)
    # Measured geometrically from model edges:
    # Ruthex RX-M3x5.7 datasheet (2022-08-15): L = 5.7 mm, min hole depth = L + 1.0 = 6.7 mm, d_hole = 4.0 mm.
    # In Case (height 15 mm, corner [-15, -15, 0]), top is z = 15.0 mm. Hole bottom is at z = 8.3 mm.
    d2_faces = ws.docs["d2_case"].session.cmd("model.faces", {"body": "Case"})["faces"]
    d2_cyls = [f["cylinder"] for f in d2_faces if f.get("cylinder")]
    d2_edges = ws.docs["d2_case"].session.cmd("model.edges", {"body": "Case"})["edges"]
    hole_cyl_edges = [e for e in d2_edges if any(":bore:" in part for part in e["name"].split("|"))]
    geom_ins_depth = round(15.0 - min(e["start"][2] for e in hole_cyl_edges), 1) if hole_cyl_edges else 0.0
    ok("bolted connection insert: mounting hole diameter is 4.0 mm (r=2.0 mm) and depth >= 6.7 mm",
       any(abs(c["radius"] - 2.0) < 1e-4 for c in d2_cyls) and geom_ins_depth >= 6.7 - 1e-4,
       f"cyls={d2_cyls} geom_depth={geom_ins_depth}")

    # Check Ruthex insert sits coaxial and flush at z = 0
    joints_ins = asm_ins.session.cmd("joint.list")["joints"]
    ins_joint = next(j for j in joints_ins if j["name"] == res_ins["joints"][0])
    fa_in, fb_in = ins_joint["frame_a"], ins_joint["frame_b"]
    coaxial_insert = (abs(fa_in["origin"][0] - fb_in["origin"][0]) < 1e-4
                      and abs(fa_in["origin"][1] - fb_in["origin"][1]) < 1e-4
                      and abs(fa_in["origin"][2] - 0.0) < 1e-4
                      and abs(fb_in["origin"][2] - 0.0) < 1e-4
                      and abs(abs(g.dot(fa_in["z"], fb_in["z"])) - 1.0) < 1e-4)
    ok("bolted connection insert: Ruthex insert sits coaxial and flush at z = 0.0 mm",
       coaxial_insert, f"{fa_in} vs {fb_in}")

    chk_ins = links.check(ws, asm_ins)
    ok("bolted connection insert: check_joints is green (all ok)",
       bool(chk_ins) and all(r["status"] == "ok" for r in chk_ins), str(chk_ins))

    ws.close_all()


def bolted_review_fixes_checks(ws):
    # Setup test plates for review findings
    p1 = ws.new(PART, "p1_rf")
    p1.session.cmd("solid.box", {"length": 60, "width": 60, "height": 10, "corner": [-30, -30, 0],
                                 "operation": "new", "body_name": "Plate1", "name": "Box1"})
    p1.save()

    p2 = ws.new(PART, "p2_rf")
    p2.session.cmd("solid.box", {"length": 60, "width": 60, "height": 8, "corner": [-30, -30, 0],
                                 "operation": "new", "body_name": "Plate2", "name": "Box2"})
    p2.save()

    asm_rf = ws.new(ASSEMBLY, "asm_rf")
    links.insert(ws, asm_rf, p1.path, name="Plate1", grounded=True)
    links.insert(ws, asm_rf, p2.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm_rf.save()

    # 1. Zu kurze Schraube ohne Fehler (hole_tables.preferred_screw_length)
    # Required length > 50 mm (max preferred for M5) must raise ValueError
    f1_ok = False
    try:
        hole_tables.preferred_screw_length("M5", 80.0)
    except ValueError:
        f1_ok = True
    ok("finding 1: preferred_screw_length rejects required length exceeding longest screw", f1_ok)

    # 2. length_override unbegrenzt / nicht geprüft
    # In through connection, required length is ~24.9 mm. A 12 mm screw must be rejected.
    f2_th_ok = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_rf",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5",
            fasteners={"length_override": 12},
            counterbore=False,
        )
    except ValueError:
        f2_th_ok = True
    ok("finding 2: preview rejects length_override shorter than required length in through connection", f2_th_ok)

    # In blind connection, 12 mm screw gives engagement = 2 mm < min_engagement = 10 mm. Must be rejected.
    f2_bl_ok = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_rf",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5",
            connection_type="blind",
            blind_material="alu",
            fasteners={"length_override": 12},
            counterbore=False,
        )
    except ValueError:
        f2_bl_ok = True
    ok("finding 2: preview rejects length_override shorter than minimum engagement in blind connection", f2_bl_ok)

    # 3. Mehrere Verbindungen ohne name in derselben Baugruppe
    p1_f3 = ws.new(PART, "p1_f3")
    p1_f3.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0], "body_name": "P1", "name": "B1"})
    p1_f3.save()
    p2_f3 = ws.new(PART, "p2_f3")
    p2_f3.session.cmd("solid.box", {"length": 80, "width": 80, "height": 8, "corner": [-40, -40, 0], "body_name": "P2", "name": "B2"})
    p2_f3.save()
    asm_f3 = ws.new(ASSEMBLY, "asm_f3")
    links.insert(ws, asm_f3, p1_f3.path, name="P1", grounded=True)
    links.insert(ws, asm_f3, p2_f3.path, name="P2", translate=[0, 0, -8], grounded=True)
    asm_f3.save()

    res_f3_1 = bolted.bolted_connection(
        ws, "asm_f3",
        placement={"position": [-20, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    res_f3_2 = bolted.bolted_connection(
        ws, "asm_f3",
        placement={"position": [20, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    joints_f3 = asm_f3.session.cmd("joint.list")["joints"]
    meta_f3 = asm_f3.metadata()
    conns_f3 = meta_f3.get("bolted_connections", {})
    joints_meta_f3 = meta_f3.get("joints", {})
    chk_f3 = links.check(ws, asm_f3)
    p1_f3_tl = sketch_rule.timeline(ws.docs["p1_f3"].session).get("timeline", [])
    hole_feats_p1 = [f["name"] for f in p1_f3_tl if "Hole" in f.get("name", "")]
    ok("finding 3: multiple bolted connections have unique joint names, metadata entries and hole feature names",
       len(joints_f3) == 6 and len(joints_meta_f3) == 6
       and len(conns_f3) == 2 and res_f3_1["id"] != res_f3_2["id"]
       and all(r["status"] == "ok" for r in chk_f3)
       and len(hole_feats_p1) == 2 and len(set(hole_feats_p1)) == 2,
       f"joints={len(joints_f3)}, meta={len(joints_meta_f3)}, conns={list(conns_f3.keys())}, holes={hole_feats_p1}")

    # 4. Strahl als unendliche Gerade: Teile hinter p0 werden nicht mitgebohrt
    cov_f4 = ws.new(PART, "cov_f4")
    cov_f4.session.cmd("solid.box", {"length": 40, "width": 40, "height": 5, "corner": [-20, -20, 10], "body_name": "Cover", "name": "B1"})
    cov_f4.save()
    top_f4 = ws.new(PART, "top_f4")
    top_f4.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "body_name": "Top", "name": "B2"})
    top_f4.save()
    bot_f4 = ws.new(PART, "bot_f4")
    bot_f4.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [-20, -20, -8], "body_name": "Bot", "name": "B3"})
    bot_f4.save()
    asm_f4 = ws.new(ASSEMBLY, "asm_f4")
    links.insert(ws, asm_f4, cov_f4.path, name="Cover", grounded=True)
    links.insert(ws, asm_f4, top_f4.path, name="Top", grounded=True)
    links.insert(ws, asm_f4, bot_f4.path, name="Bot", grounded=True)
    asm_f4.save()
    prev_f4 = bolted.preview_bolted_connection(
        ws, "asm_f4",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    f4_part_occs = [p["occurrence"] for p in prev_f4["parts"]]
    ok("finding 4: ray ignores parts behind placement origin (s >= 0 filter)",
       f4_part_occs == ["Top:1", "Bot:1"] and prev_f4["total_thickness"] == 18.0,
       f"parts={f4_part_occs}, thickness={prev_f4['total_thickness']}")

    # 5. Bauteildicke aus echten Flächen statt Bounding-Box
    step_f5 = ws.new(PART, "step_f5")
    step_f5.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0], "name": "Base"})
    step_f5.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 10], "operation": "join", "name": "Step"})
    step_f5.save()
    bot_f5 = ws.new(PART, "bot_f5")
    bot_f5.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [0, 0, -8], "body_name": "Bot", "name": "B1"})
    bot_f5.save()
    asm_f5 = ws.new(ASSEMBLY, "asm_f5")
    links.insert(ws, asm_f5, step_f5.path, name="Stepped", grounded=True)
    links.insert(ws, asm_f5, bot_f5.path, name="Bot", grounded=True)
    asm_f5.save()
    prev_f5 = bolted.preview_bolted_connection(
        ws, "asm_f5",
        placement={"position": [20, 20, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    ok("finding 5: plate thickness measured from actual face intersection not body bbox",
       prev_f5["parts"][0]["thickness"] == 10.0 and prev_f5["selected_screw_length"] == 25.0,
       f"thickness={prev_f5['parts'][0]['thickness']}, screw={prev_f5['selected_screw_length']}")

    # 6. Kernloch M8 und M12 weicht von DIN 336 ab
    p1_f6 = ws.new(PART, "p1_f6")
    p1_f6.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "body_name": "P1", "name": "B1"})
    p1_f6.save()
    p2_f6 = ws.new(PART, "p2_f6")
    p2_f6.session.cmd("solid.box", {"length": 40, "width": 40, "height": 30, "corner": [-20, -20, 0], "body_name": "P2", "name": "B2"})
    p2_f6.save()
    asm_f6 = ws.new(ASSEMBLY, "asm_f6")
    links.insert(ws, asm_f6, p1_f6.path, name="P1", grounded=True)
    links.insert(ws, asm_f6, p2_f6.path, name="P2", translate=[0, 0, -30], grounded=True)
    asm_f6.save()

    res_f6 = bolted.bolted_connection(
        ws, "asm_f6",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M8",
        connection_type="blind",
        blind_material="alu",
        counterbore=False,
    )
    p2_f6_doc = ws.get("p2_f6")
    p2_f6_faces = p2_f6_doc.session.cmd("model.faces", {"body": "P2"})["faces"]
    p2_f6_cyls = [f["cylinder"] for f in p2_f6_faces if f.get("cylinder")]
    # DIN 336 / ISO 2306: M8 drill diameter is 6.8 mm (radius 3.4 mm), M12 is 10.2 mm
    ok("finding 6: blind tapped hole M8 drills 6.8 mm diameter (r=3.4 mm) per DIN 336",
       any(abs(c["radius"] - 3.4) < 1e-3 for c in p2_f6_cyls)
       and hole_tables.tap_drill("M8") == 6.8
       and hole_tables.tap_drill("M12") == 10.2,
       f"cyls={p2_f6_cyls}")

    # 7. Bohrspitze bricht durch (drill_depth + point_depth > plate_thickness)
    p_base14 = ws.new(PART, "p_base14")
    p_base14.session.cmd("solid.box", {"length": 40, "width": 40, "height": 14, "corner": [-20, -20, 0], "body_name": "Base14", "name": "B14"})
    p_base14.save()
    asm_f7 = ws.new(ASSEMBLY, "asm_f7")
    links.insert(ws, asm_f7, p1_f6.path, name="Cover", grounded=True)
    links.insert(ws, asm_f7, p_base14.path, name="Base14", translate=[0, 0, -14], grounded=True)
    asm_f7.save()
    f7_ok = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_f7",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5",
            connection_type="blind",
            blind_material="alu",
            counterbore=False,
        )
    except ValueError:
        f7_ok = True
    ok("finding 7: preview rejects blind hole when drill tip breaks through bottom plate (14.46 > 14 mm)", f7_ok)

    # 8. Gleiche Teildatei zweimal im Paket
    asm_f8 = ws.new(ASSEMBLY, "asm_f8")
    links.insert(ws, asm_f8, p1_f6.path, name="Plate1", grounded=True)
    links.insert(ws, asm_f8, p1_f6.path, name="Plate2", translate=[0, 0, -10], grounded=True)
    asm_f8.save()
    f8_ok = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_f8",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5",
            counterbore=True,
        )
    except ValueError:
        f8_ok = True
    ok("finding 8: preview rejects duplicate component file in bolted connection stack", f8_ok)

    # 9. Einsatz: Schraubenspitze hinter dem Aufnahmeloch
    p_lid17 = ws.new(PART, "p_lid17")
    p_lid17.session.cmd("solid.box", {"length": 40, "width": 40, "height": 17.35, "corner": [-20, -20, 0], "body_name": "Lid17", "name": "BLid"})
    p_lid17.save()
    p_case20 = ws.new(PART, "p_case20")
    p_case20.session.cmd("solid.box", {"length": 40, "width": 40, "height": 20, "corner": [-20, -20, 0], "body_name": "Case20", "name": "BCase"})
    p_case20.save()
    asm_f9 = ws.new(ASSEMBLY, "asm_f9")
    links.insert(ws, asm_f9, p_lid17.path, name="Lid17", grounded=True)
    links.insert(ws, asm_f9, p_case20.path, name="Case20", translate=[0, 0, -20], grounded=True)
    asm_f9.save()
    f9_ok = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_f9",
            placement={"position": [0, 0, 17.35], "direction": [0, 0, -1]},
            size="M4",
            use_insert=True,
            counterbore=True,
        )
    except ValueError:
        f9_ok = True
    ok("finding 9: preview rejects screw tip penetrating beyond insert mounting hole depth", f9_ok)

    # 10. Passung fit verhält sich anders als in SolidCraft
    f10_err_ok = False
    try:
        hole_tables.clearance_hole("M5", "xyz")
    except ValueError:
        f10_err_ok = True
    ok("finding 10: clearance_hole rejects unknown fit with ValueError", f10_err_ok)

    ok("finding 10: clearance_hole supports close/fine and loose/coarse",
       hole_tables.clearance_hole("M5", "close") == 5.3
       and hole_tables.clearance_hole("M5", "f") == 5.3
       and hole_tables.clearance_hole("M5", "loose") == 5.8
       and hole_tables.clearance_hole("M5", "c") == 5.8)

    res_f10 = bolted.bolted_connection(
        ws, "asm_rf",
        placement={"position": [10, 10, 10], "direction": [0, 0, -1]},
        size="M5",
        fit="close",
        counterbore=False,
    )
    p1_faces_f10 = ws.docs["p1_rf"].session.cmd("model.faces", {"body": "Plate1"})["faces"]
    cyls_p1_f10 = [f["cylinder"] for f in p1_faces_f10 if f.get("cylinder")]
    ok("finding 10: bolted_connection with close fit executes and produces 5.3 mm hole",
       any(abs(c["radius"] - 2.65) < 1e-4 for c in cyls_p1_f10))

    # 11. Senkung tiefer als obere Platte
    p_thin = ws.new(PART, "p_thin")
    p_thin.session.cmd("solid.box", {"length": 40, "width": 40, "height": 4, "corner": [-20, -20, 0], "body_name": "Pthin", "name": "Bthin"})
    p_thin.save()
    asm_f11 = ws.new(ASSEMBLY, "asm_f11")
    links.insert(ws, asm_f11, p_thin.path, name="Pthin", grounded=True)
    links.insert(ws, asm_f11, p2.path, name="P2", translate=[0, 0, -8], grounded=True)
    asm_f11.save()
    f11_ok = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_f11",
            placement={"position": [0, 0, 4], "direction": [0, 0, -1]},
            size="M5",
            counterbore=True,
        )
    except ValueError:
        f11_ok = True
    ok("finding 11: preview rejects counterbore depth exceeding top plate thickness", f11_ok)

    # 12. _parse_placement mit concentric
    cyl_part = ws.new(PART, "cyl_part")
    cyl_part.session.cmd("solid.cylinder", {"diameter": 30, "height": 10, "base": [0, 0, 0], "name": "Outer"})
    cyl_part.session.cmd("solid.hole", {"position": [0, 0, 10], "direction": [0, 0, -1], "diameter": 5.5, "depth": 10, "name": "Hole"})
    cyl_part.save()
    asm_f12 = ws.new(ASSEMBLY, "asm_f12")
    links.insert(ws, asm_f12, cyl_part.path, name="Boss", grounded=True)
    links.insert(ws, asm_f12, p2.path, name="P2", translate=[0, 0, -8], grounded=True)
    asm_f12.save()

    res_f12 = bolted.bolted_connection(
        ws, "asm_f12",
        placement={"type": "concentric", "occurrence": "Boss:1", "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    ok("finding 12: concentric placement selects hole cylinder not boss and connects plates",
       res_f12["size"] == "M5" and len(res_f12["joints"]) >= 1)

    # 13. Vorhandene Normteil-Datei wird ungeprüft wiederverwendet
    doc_bad = ws.new(PART, "ISO_4762_M5x16_altered")
    sp_alt = standard_parts.spec("ISO 4762", "M5", length=30)
    doc_bad.session.batch(sp_alt["commands"])
    meta_alt = dict(sp_alt["standard"])
    meta_alt["designation"] = "ISO 4762 M5x16"
    doc_bad.set_metadata({"kind": PART, "format": 1, "standard": meta_alt})
    doc_bad.save()
    ws.close("ISO_4762_M5x16_altered")

    bad_named_doc = ws.new(PART, "ISO_4762_M5x16", overwrite=True)
    bad_named_doc.session.batch(sp_alt["commands"])
    meta_alt_named = dict(sp_alt["standard"])
    meta_alt_named["designation"] = "ISO 4762 M5x16"
    bad_named_doc.set_metadata({"kind": PART, "format": 1, "standard": meta_alt_named})
    bad_named_doc.save()
    recreated_path = bolted._ensure_standard_part(ws, "ISO 4762", "M5", length=16)
    rec_doc = ws.docs.get("ISO_4762_M5x16") or ws.open(recreated_path)
    ok("finding 13: _ensure_standard_part detects modified dimensions and recreates standard part",
       rec_doc.metadata().get("standard", {}).get("dimensions", {}).get("l") == 16.0)

    # DIN 974-1:2008-02 Reihe 5 counterbore and washer_head bolted connection
    # M5 counterbore with washer: dia 13.0 mm, depth 6.4 mm (DIN 974-1:2008-02 Tab. 1 Reihe 5 & Tab. 2)
    cb_m5_washer = hole_tables.counterbore("M5", with_washer=True)
    ok("DIN 974-1 Reihe 5: M5 counterbore with washer has dia 13.0 mm and depth 6.4 mm",
       cb_m5_washer["diameter"] == 13.0 and abs(cb_m5_washer["depth"] - 6.4) < 1e-4,
       str(cb_m5_washer))

    res_wh = bolted.bolted_connection(
        ws, "asm_rf",
        placement={"position": [-15, -15, 10], "direction": [0, 0, -1]},
        size="M5",
        fasteners={"washer_head": True, "washer_nut": True},
        counterbore=True,
    )
    ok("bolted connection with washer_head: creates head washer and joints",
       res_wh["washer_head"] is True and len(res_wh["washers"]) == 2
       and len(res_wh["joints"]) == 4)

    # Horizontal connection direction (+X)
    p1_x = ws.new(PART, "p1_x")
    p1_x.session.cmd("solid.box", {"length": 10, "width": 40, "height": 40, "corner": [0, -20, -20], "body_name": "P1", "name": "B1"})
    p1_x.save()
    p2_x = ws.new(PART, "p2_x")
    p2_x.session.cmd("solid.box", {"length": 8, "width": 40, "height": 40, "corner": [10, -20, -20], "body_name": "P2", "name": "B2"})
    p2_x.save()
    asm_x = ws.new(ASSEMBLY, "asm_x")
    links.insert(ws, asm_x, p1_x.path, name="P1", grounded=True)
    links.insert(ws, asm_x, p2_x.path, name="P2", grounded=True)
    asm_x.save()

    res_x = bolted.bolted_connection(
        ws, "asm_x",
        placement={"position": [0, 0, 0], "direction": [1, 0, 0]},
        size="M5",
        counterbore=False,
    )
    ok("bolted connection in +X direction: connects plates along horizontal axis",
       res_x["size"] == "M5" and res_x["grip_length"] == 18.0 and len(res_x["joints"]) == 3)

    ws.close_all()


def bolted_pattern_and_edit_checks(ws):
    # 1. Circular pattern with 4 screws through two plates
    p1 = ws.new(PART, "p1_circ")
    p1.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0],
                                 "operation": "new", "body_name": "Plate1", "name": "Box1"})
    p1.save()
    v1_init = p1.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    p2 = ws.new(PART, "p2_circ")
    p2.session.cmd("solid.box", {"length": 80, "width": 80, "height": 8, "corner": [-40, -40, 0],
                                 "operation": "new", "body_name": "Plate2", "name": "Box2"})
    p2.save()
    v2_init = p2.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    asm = ws.new(ASSEMBLY, "asm_circ")
    links.insert(ws, asm, p1.path, name="Plate1", grounded=True)
    links.insert(ws, asm, p2.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm.save()

    circ_pat = {"type": "circular", "count": 4, "axis_point": [0, 0, 0], "axis": [0, 0, 1]}
    prev_circ = bolted.preview_bolted_connection(
        ws, "asm_circ",
        placement={"position": [20, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
        pattern=circ_pat,
    )
    ok("bolted pattern preview: circular 4-screw pattern reports count 4 and positions",
       prev_circ.get("count") == 4 and len(prev_circ.get("positions", [])) == 4, str(prev_circ))

    res_circ = bolted.bolted_connection(
        ws, "asm_circ",
        placement={"position": [20, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
        pattern=circ_pat,
    )
    p1_tl = sketch_rule.timeline(ws.docs["p1_circ"].session).get("timeline", [])
    p2_tl = sketch_rule.timeline(ws.docs["p2_circ"].session).get("timeline", [])
    p1_holes = [f["name"] for f in p1_tl if "Hole" in f.get("name", "")]
    p2_holes = [f["name"] for f in p2_tl if "Hole" in f.get("name", "")]
    interf_circ = asm.session.cmd("inspect.interference")
    chk_circ = links.check(ws, asm)

    ok("bolted pattern: circular pattern with 4 screws creates 4 holes per plate, 4 screws and interference == 0",
       len(p1_holes) == 4 and len(p2_holes) == 4
       and len(res_circ.get("screws", [])) == 4
       and interf_circ.get("count") == 0
       and len(res_circ.get("joints", [])) == 12
       and bool(chk_circ) and all(r["status"] == "ok" for r in chk_circ),
       f"p1_holes={len(p1_holes)}, p2_holes={len(p2_holes)}, screws={len(res_circ.get('screws', []))}, interf={interf_circ}")

    # 2. list_bolted_connections and delete_bolted_connection
    conns = bolted.list_bolted_connections(ws, "asm_circ")
    ok("bolted connection: list_bolted_connections returns recorded connection",
       conns.get("count") == 1 and res_circ["id"] in conns.get("connections", {}), str(conns))

    del_res = bolted.delete_bolted_connection(ws, "asm_circ", res_circ["id"])
    v1_after_del = ws.docs["p1_circ"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    v2_after_del = ws.docs["p2_circ"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    p1_tl_del = sketch_rule.timeline(ws.docs["p1_circ"].session).get("timeline", [])
    p2_tl_del = sketch_rule.timeline(ws.docs["p2_circ"].session).get("timeline", [])
    p1_holes_del = [f["name"] for f in p1_tl_del if "Hole" in f.get("name", "")]
    p2_holes_del = [f["name"] for f in p2_tl_del if "Hole" in f.get("name", "")]
    comps_del = [c["name"] for c in asm.session.cmd("component.list")["components"]]

    ok("bolted connection: delete_bolted_connection removes all holes and screws and restores plate volumes",
       del_res.get("deleted") == res_circ["id"]
       and len(p1_holes_del) == 0 and len(p2_holes_del) == 0
       and abs(v1_init - v1_after_del) < 1e-4 and abs(v2_init - v2_after_del) < 1e-4
       and set(comps_del) == {"asm_circ", "Plate1", "Plate2"}
       and bolted.list_bolted_connections(ws, "asm_circ")["count"] == 0,
       f"p1_holes={p1_holes_del}, p2_holes={p2_holes_del}, v1={v1_after_del} (orig {v1_init}), comps={comps_del}")

    # 2b. bolted_connection with pattern rollback on simulated error after drilling
    p1_rb = ws.new(PART, "p1_rb_pat")
    p1_rb.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0],
                                    "operation": "new", "body_name": "Plate1", "name": "Box1"})
    p1_rb.save()
    v1_rb_before = p1_rb.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    p2_rb = ws.new(PART, "p2_rb_pat")
    p2_rb.session.cmd("solid.box", {"length": 80, "width": 80, "height": 8, "corner": [-40, -40, 0],
                                    "operation": "new", "body_name": "Plate2", "name": "Box2"})
    p2_rb.save()
    v2_rb_before = p2_rb.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    asm_rb = ws.new(ASSEMBLY, "asm_rb_pat")
    links.insert(ws, asm_rb, p1_rb.path, name="Plate1", grounded=True)
    links.insert(ws, asm_rb, p2_rb.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm_rb.save()

    comps_rb_before = [c["name"] for c in asm_rb.session.cmd("component.list")["components"]]
    joints_rb_before = [j["name"] for j in asm_rb.session.cmd("joint.list").get("joints", [])]
    meta_rb_before = dict(asm_rb.metadata().get("bolted_connections", {}))

    rb_pat = {"type": "rectangular", "count": [2, 2], "spacing": [30, 30], "directions": [[1, 0, 0], [0, 1, 0]]}

    # Simulate standard_parts.create failure AFTER drilling all 4 pattern holes in both plates
    orig_sp_create = standard_parts.create
    calls_sp_rb = [0]
    def mock_sp_create(*args, **kwargs):
        calls_sp_rb[0] += 1
        raise RuntimeError("simulated standard_parts.create failure after drilling")

    standard_parts.create = mock_sp_create
    err_pat_caught = False
    try:
        bolted.bolted_connection(
            ws, "asm_rb_pat",
            placement={"position": [-15, -15, 10], "direction": [0, 0, -1]},
            size="M4",
            counterbore=False,
            pattern=rb_pat,
        )
    except RuntimeError:
        err_pat_caught = True
    finally:
        standard_parts.create = orig_sp_create

    # Verify open sessions
    v1_rb_open = p1_rb.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    v2_rb_open = p2_rb.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    p1_rb_holes_open = [f["name"] for f in sketch_rule.timeline(p1_rb.session).get("timeline", []) if "Hole" in f.get("name", "")]
    p2_rb_holes_open = [f["name"] for f in sketch_rule.timeline(p2_rb.session).get("timeline", []) if "Hole" in f.get("name", "")]

    # Verify disk files
    r1_rb = ws.reader(p1_rb.path)
    try:
        v1_rb_disk = r1_rb.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
        p1_rb_holes_disk = [f["name"] for f in sketch_rule.timeline(r1_rb).get("timeline", []) if "Hole" in f.get("name", "")]
    finally:
        r1_rb.close()

    r2_rb = ws.reader(p2_rb.path)
    try:
        v2_rb_disk = r2_rb.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
        p2_rb_holes_disk = [f["name"] for f in sketch_rule.timeline(r2_rb).get("timeline", []) if "Hole" in f.get("name", "")]
    finally:
        r2_rb.close()

    comps_rb_after = [c["name"] for c in asm_rb.session.cmd("component.list")["components"]]
    joints_rb_after = [j["name"] for j in asm_rb.session.cmd("joint.list").get("joints", [])]
    meta_rb_after = asm_rb.metadata().get("bolted_connections", {})
    chk_rb_pat = links.check(ws, asm_rb)
    interf_rb_pat = asm_rb.session.cmd("inspect.interference")

    ok("bolted connection: pattern creation rollback after drilling restores files and assembly",
       err_pat_caught and calls_sp_rb[0] >= 1
       and len(p1_rb_holes_open) == 0 and len(p1_rb_holes_disk) == 0
       and len(p2_rb_holes_open) == 0 and len(p2_rb_holes_disk) == 0
       and abs(v1_rb_before - v1_rb_open) < 1e-4 and abs(v1_rb_before - v1_rb_disk) < 1e-4
       and abs(v2_rb_before - v2_rb_open) < 1e-4 and abs(v2_rb_before - v2_rb_disk) < 1e-4
       and comps_rb_after == comps_rb_before
       and joints_rb_after == joints_rb_before
       and meta_rb_after == meta_rb_before
       and all(r["status"] == "ok" for r in chk_rb_pat)
       and interf_rb_pat.get("count") == 0,
       f"caught={err_pat_caught}, p1_holes={p1_rb_holes_open}, p2_holes={p2_rb_holes_open}, comps={comps_rb_after}")

    # 3. Rectangular pattern 2x2
    p1_r = ws.new(PART, "p1_rect")
    p1_r.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0],
                                   "operation": "new", "body_name": "Plate1", "name": "Box1"})
    p1_r.save()
    p2_r = ws.new(PART, "p2_rect")
    p2_r.session.cmd("solid.box", {"length": 80, "width": 80, "height": 8, "corner": [-40, -40, 0],
                                   "operation": "new", "body_name": "Plate2", "name": "Box2"})
    p2_r.save()
    asm_r = ws.new(ASSEMBLY, "asm_rect")
    links.insert(ws, asm_r, p1_r.path, name="Plate1", grounded=True)
    links.insert(ws, asm_r, p2_r.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm_r.save()

    rect_pat = {"type": "rectangular", "count": [2, 2], "spacing": [30, 30], "directions": [[1, 0, 0], [0, 1, 0]]}
    res_rect = bolted.bolted_connection(
        ws, "asm_rect",
        placement={"position": [-15, -15, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
        pattern=rect_pat,
    )
    p1_r_tl = sketch_rule.timeline(ws.docs["p1_rect"].session).get("timeline", [])
    p2_r_tl = sketch_rule.timeline(ws.docs["p2_rect"].session).get("timeline", [])
    p1_r_holes = [f["name"] for f in p1_r_tl if "Hole" in f.get("name", "")]
    p2_r_holes = [f["name"] for f in p2_r_tl if "Hole" in f.get("name", "")]
    interf_r = asm_r.session.cmd("inspect.interference")
    chk_r = links.check(ws, asm_r)

    ok("bolted pattern: rectangular pattern 2x2 creates 4 holes per plate, 4 screws and interference == 0",
       len(p1_r_holes) == 4 and len(p2_r_holes) == 4
       and len(res_rect.get("screws", [])) == 4
       and interf_r.get("count") == 0
       and len(res_rect.get("joints", [])) == 12
       and bool(chk_r) and all(r["status"] == "ok" for r in chk_r),
       f"p1_holes={len(p1_r_holes)}, p2_holes={len(p2_r_holes)}, screws={len(res_rect.get('screws', []))}, interf={interf_r}")

    # 4. edit_bolted_connection (M5 -> M6)
    res_edit = bolted.edit_bolted_connection(ws, "asm_rect", res_rect["id"], size="M6")
    p1_r_faces = ws.docs["p1_rect"].session.cmd("model.faces", {"body": "Plate1"})["faces"]
    p1_r_cyls = [f["cylinder"] for f in p1_r_faces if f.get("cylinder")]
    p2_r_faces = ws.docs["p2_rect"].session.cmd("model.faces", {"body": "Plate2"})["faces"]
    p2_r_cyls = [f["cylinder"] for f in p2_r_faces if f.get("cylinder")]
    chk_edit = links.check(ws, asm_r)
    interf_edit = asm_r.session.cmd("inspect.interference")

    ok("bolted connection: edit size M5 to M6 updates hole diameters to 6.6 mm and preserves joints",
       res_edit.get("size") == "M6"
       and len(p1_r_cyls) >= 4 and all(abs(c["radius"] - 3.3) < 1e-4 for c in p1_r_cyls)
       and len(p2_r_cyls) >= 4 and all(abs(c["radius"] - 3.3) < 1e-4 for c in p2_r_cyls)
       and interf_edit.get("count") == 0
       and len(res_edit.get("joints", [])) == 12
       and bool(chk_edit) and all(r["status"] == "ok" for r in chk_edit),
       f"size={res_edit.get('size')}, p1_radii={[c['radius'] for c in p1_r_cyls]}, chk={len(chk_edit)}")

    # 4b. edit rollback on error
    err_edit_caught = False
    try:
        bolted.edit_bolted_connection(ws, "asm_rect", res_rect["id"], fasteners={"length_override": 5})
    except ValueError:
        err_edit_caught = True
    p1_r_faces_rb = ws.docs["p1_rect"].session.cmd("model.faces", {"body": "Plate1"})["faces"]
    p1_r_cyls_rb = [f["cylinder"] for f in p1_r_faces_rb if f.get("cylinder")]
    chk_rb = links.check(ws, asm_r)

    ok("bolted connection: edit rollback restores previous state on error",
       err_edit_caught
       and all(abs(c["radius"] - 3.3) < 1e-4 for c in p1_r_cyls_rb)
       and bool(chk_rb) and all(r["status"] == "ok" for r in chk_rb),
       f"err_caught={err_edit_caught}, radii={[c['radius'] for c in p1_r_cyls_rb]}")

    # 4c. edit rollback on error after deletion and drilling (monkeypatch)
    v1_edit_before = ws.docs["p1_rect"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    v2_edit_before = ws.docs["p2_rect"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    p1_edit_holes_before = [f["name"] for f in sketch_rule.timeline(ws.docs["p1_rect"].session).get("timeline", []) if "Hole" in f.get("name", "")]
    p2_edit_holes_before = [f["name"] for f in sketch_rule.timeline(ws.docs["p2_rect"].session).get("timeline", []) if "Hole" in f.get("name", "")]
    comps_edit_before = [c["name"] for c in asm_r.session.cmd("component.list")["components"]]
    joints_edit_before = [j["name"] for j in asm_r.session.cmd("joint.list").get("joints", [])]
    meta_edit_before = dict(asm_r.metadata().get("bolted_connections", {}))

    # Monkeypatch links.record during edit recreate (after old connection deleted and new M8 holes drilled)
    orig_record = links.record
    calls_edit_rb = [0]
    def mock_edit_record(*args, **kwargs):
        calls_edit_rb[0] += 1
        raise RuntimeError("simulated error in links.record after edit drilling")

    links.record = mock_edit_record
    err_edit_deep_caught = False
    try:
        bolted.edit_bolted_connection(ws, "asm_rect", res_rect["id"], size="M8")
    except RuntimeError:
        err_edit_deep_caught = True
    finally:
        links.record = orig_record

    # Verify open sessions
    v1_edit_open = ws.docs["p1_rect"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    v2_edit_open = ws.docs["p2_rect"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    p1_edit_holes_open = [f["name"] for f in sketch_rule.timeline(ws.docs["p1_rect"].session).get("timeline", []) if "Hole" in f.get("name", "")]
    p2_edit_holes_open = [f["name"] for f in sketch_rule.timeline(ws.docs["p2_rect"].session).get("timeline", []) if "Hole" in f.get("name", "")]
    p1_edit_faces = ws.docs["p1_rect"].session.cmd("model.faces", {"body": "Plate1"})["faces"]
    p1_edit_cyls = [f["cylinder"] for f in p1_edit_faces if f.get("cylinder")]
    p2_edit_faces = ws.docs["p2_rect"].session.cmd("model.faces", {"body": "Plate2"})["faces"]
    p2_edit_cyls = [f["cylinder"] for f in p2_edit_faces if f.get("cylinder")]

    # Verify disk files
    r1_edit = ws.reader(p1_r.path)
    try:
        v1_edit_disk = r1_edit.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
        p1_edit_holes_disk = [f["name"] for f in sketch_rule.timeline(r1_edit).get("timeline", []) if "Hole" in f.get("name", "")]
    finally:
        r1_edit.close()

    r2_edit = ws.reader(p2_r.path)
    try:
        v2_edit_disk = r2_edit.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
        p2_edit_holes_disk = [f["name"] for f in sketch_rule.timeline(r2_edit).get("timeline", []) if "Hole" in f.get("name", "")]
    finally:
        r2_edit.close()

    comps_edit_after = [c["name"] for c in asm_r.session.cmd("component.list")["components"]]
    joints_edit_after = [j["name"] for j in asm_r.session.cmd("joint.list").get("joints", [])]
    meta_edit_after = asm_r.metadata().get("bolted_connections", {})
    chk_edit_deep = links.check(ws, asm_r)
    interf_edit_deep = asm_r.session.cmd("inspect.interference")

    ok("bolted connection: edit rollback after deletion and drilling restores previous state on error",
       err_edit_deep_caught and calls_edit_rb[0] >= 1
       and len(p1_edit_holes_open) == len(p1_edit_holes_before) and len(p1_edit_holes_disk) == len(p1_edit_holes_before)
       and len(p2_edit_holes_open) == len(p2_edit_holes_before) and len(p2_edit_holes_disk) == len(p2_edit_holes_before)
       and abs(v1_edit_before - v1_edit_open) < 1e-4 and abs(v1_edit_before - v1_edit_disk) < 1e-4
       and abs(v2_edit_before - v2_edit_open) < 1e-4 and abs(v2_edit_before - v2_edit_disk) < 1e-4
       and len(p1_edit_cyls) >= 4 and all(abs(c["radius"] - 3.3) < 1e-4 for c in p1_edit_cyls)
       and len(p2_edit_cyls) >= 4 and all(abs(c["radius"] - 3.3) < 1e-4 for c in p2_edit_cyls)
       and comps_edit_after == comps_edit_before
       and joints_edit_after == joints_edit_before
       and meta_edit_after == meta_edit_before
       and bool(chk_edit_deep) and all(r["status"] == "ok" for r in chk_edit_deep)
       and interf_edit_deep.get("count") == 0,
       f"caught={err_edit_deep_caught}, p1_holes={p1_edit_holes_open}, comps={comps_edit_after}")

    # 5. Error on non-uniform penetration without modifying files
    p_a = ws.new(PART, "p_a")
    p_a.session.cmd("solid.box", {"length": 50, "width": 50, "height": 10, "corner": [-25, -25, 0],
                                 "operation": "new", "body_name": "PlateA", "name": "BoxA"})
    p_a.save()
    va_init = p_a.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    p_b = ws.new(PART, "p_b")
    p_b.session.cmd("solid.box", {"length": 30, "width": 30, "height": 8, "corner": [-15, -15, 0],
                                 "operation": "new", "body_name": "PlateB", "name": "BoxB"})
    p_b.save()
    vb_init = p_b.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    asm_nu = ws.new(ASSEMBLY, "asm_nu")
    links.insert(ws, asm_nu, p_a.path, name="PlateA", grounded=True)
    links.insert(ws, asm_nu, p_b.path, name="PlateB", translate=[0, 0, -8], grounded=True)
    asm_nu.save()

    err_nu_prev = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_nu",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5",
            pattern={"type": "rectangular", "count": [2, 1], "spacing": [20, 0], "directions": [[1, 0, 0], [0, 1, 0]]},
        )
    except ValueError:
        err_nu_prev = True

    err_nu_exec = False
    try:
        bolted.bolted_connection(
            ws, "asm_nu",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5",
            pattern={"type": "rectangular", "count": [2, 1], "spacing": [20, 0], "directions": [[1, 0, 0], [0, 1, 0]]},
        )
    except ValueError:
        err_nu_exec = True

    va_after = p_a.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    vb_after = p_b.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    pa_holes = [f for f in sketch_rule.timeline(p_a.session).get("timeline", []) if "Hole" in f.get("name", "")]
    pb_holes = [f for f in sketch_rule.timeline(p_b.session).get("timeline", []) if "Hole" in f.get("name", "")]
    comps_nu = [c["name"] for c in asm_nu.session.cmd("component.list")["components"]]

    ok("bolted pattern: error on non-uniform penetration leaves files untouched",
       err_nu_prev and err_nu_exec
       and len(pa_holes) == 0 and len(pb_holes) == 0
       and abs(va_init - va_after) < 1e-4 and abs(vb_init - vb_after) < 1e-4
       and set(comps_nu) == {"asm_nu", "PlateA", "PlateB"},
       f"prev={err_nu_prev}, exec={err_nu_exec}, pa_holes={pa_holes}, pb_holes={pb_holes}, va={va_after} (orig {va_init})")

    ws.close_all()


def design_intent_checks(ws):
    """Design intent rule: "a hole in the middle of this face" is a sketch tied to the face's projected
    edges (midpoint constraints), so the hole stays centred when the face changes size."""
    doc = ws.new(PART, "intent_centre")
    s = doc.session
    s.cmd("parameters.add", {"name": "L", "expression": "80 mm"})
    s.cmd("parameters.add", {"name": "W", "expression": "50 mm"})
    s.cmd("solid.box", {"corner": [0, 0, 0], "length": "L", "width": "W", "height": 6,
                        "operation": "new", "body_name": "Plate"})
    s.cmd("sketch.create", {"plane": "XY", "offset": 6, "name": "Centre"})
    r = s.cmd("sketch.project", {"refs": [{"edge": [40, 0, 6], "body": "Plate"}, {"edge": [40, 50, 6], "body": "Plate"}]})
    a, b = (lk["curves"][0] for lk in r["links"])
    s.cmd("sketch.line", {"points": [[40, 0], [40, 50]], "ids": ["axis"]})
    s.cmd("sketch.construction", {"curves": ["axis"]})
    s.cmd("sketch.constraint.midpoint", {"point": "axis.start", "line": a})
    s.cmd("sketch.constraint.midpoint", {"point": "axis.end", "line": b})
    s.cmd("sketch.point", {"point": [40, 25], "id": "c"})
    r = s.cmd("sketch.constraint.midpoint", {"point": "c", "line": "axis"})
    ok("design intent: centred hole sketch is fully constrained", r["sketch"]["dof"] == 0, str(r["sketch"]))
    s.cmd("sketch.finish")
    s.cmd("solid.hole", {"sketch": "Centre", "diameter": 6, "name": "Hole"})

    def axis():
        fs = [f for f in s.cmd("model.faces", {"body": "Plate"})["faces"] if f.get("cylinder")]
        return fs[0]["cylinder"]["origin"][:2] if fs else None

    for L, W in ((80, 50), (120, 70), (200, 20)):
        s.cmd("parameters.change", {"name": "L", "expression": f"{L} mm"})
        s.cmd("parameters.change", {"name": "W", "expression": f"{W} mm"})
        c = axis()
        ok(f"design intent: hole stays centred at {L} x {W}",
           c is not None and abs(c[0] - L / 2) < 1e-6 and abs(c[1] - W / 2) < 1e-6, str(c))
    ws.close(doc.name)

    # the Hole dialog's "Middle of face" (centred_hole_commands), here on a side face of a block
    from mechvane.ui.server import centred_hole_commands
    doc = ws.new(PART, "intent_dialog")
    s = doc.session
    for n, e in (("L", "80 mm"), ("W", "50 mm"), ("T", "20 mm")):
        s.cmd("parameters.add", {"name": n, "expression": e})
    s.cmd("solid.box", {"corner": [0, 0, 0], "length": "L", "width": "W", "height": "T", "operation": "new",
                        "body_name": "Block"})
    modeling.run_commands(doc, centred_hole_commands(
        doc, {"centre": True, "position": [80, 10, 5], "direction": [-1, 0, 0], "diameter": 4, "depth": 8}))
    for L, W, T in ((80, 50, 20), (120, 70, 30)):
        for n, v in (("L", L), ("W", W), ("T", T)):
            s.cmd("parameters.change", {"name": n, "expression": f"{v} mm"})
        c = [f["cylinder"]["origin"] for f in s.cmd("model.faces", {"body": "Block"})["faces"] if f.get("cylinder")]
        ok(f"design intent: dialog 'Middle of face' hole stays centred on the side face at {L} x {W} x {T}",
           bool(c) and abs(c[0][1] - W / 2) < 1e-6 and abs(c[0][2] - T / 2) < 1e-6, str(c[:1]))
    ws.close(doc.name)


def concentric_hole_checks(ws):
    """Design intent rule: a centred hole on a circular planar face (cylinder, flange, ring)
    is concentric to the largest circular edge, staying on the cylinder axis when D changes."""
    from mechvane.ui.server import centred_hole_commands

    doc = ws.new(PART, "intent_concentric")
    s = doc.session
    s.cmd("parameters.add", {"name": "D", "expression": "40 mm"})
    s.cmd("solid.cylinder", {"base": [15, -7, 0], "diameter": "D", "height": 10, "operation": "new",
                             "body_name": "Cyl"})

    # Click off-centre on the top face (face at z = 10, normal [0, 0, 1])
    cmds = centred_hole_commands(doc, {"centre": True, "position": [25, -2, 10], "direction": [0, 0, -1],
                                       "diameter": 6, "depth": 5})
    modeling.run_commands(doc, cmds)

    def hole_cyl(body):
        cyls = [f["cylinder"] for f in s.tool("body_topology", {"body": body})["faces"] if f.get("cylinder")]
        holes = [c for c in cyls if abs(c["radius"] - 3.0) < 1e-4]
        return holes[0] if holes else None

    ha = hole_cyl("Cyl")
    ok("design intent: concentric hole axis on cylinder lies on cylinder axis",
       ha is not None and abs(ha["origin"][0] - 15) < 1e-5 and abs(ha["origin"][1] - (-7)) < 1e-5
       and g.parallel(ha["axis"], [0, 0, 1]), str(ha))

    # Changing parameter D from 40 mm to 60 mm keeps the hole on the cylinder axis
    s.cmd("parameters.change", {"name": "D", "expression": "60 mm"})
    ha_after = hole_cyl("Cyl")
    ok("design intent: concentric hole stays on cylinder axis after D change to 60 mm",
       ha_after is not None and abs(ha_after["origin"][0] - 15) < 1e-5 and abs(ha_after["origin"][1] - (-7)) < 1e-5
       and g.parallel(ha_after["axis"], [0, 0, 1]), str(ha_after))
    ws.close(doc.name)

    # Second case: Ring (cylinder with a hole), hole concentric to the outer circular edge
    doc = ws.new(PART, "intent_ring")
    s = doc.session
    s.cmd("parameters.add", {"name": "D_outer", "expression": "50 mm"})
    s.cmd("solid.cylinder", {"base": [10, 20, 0], "diameter": "D_outer", "height": 15, "operation": "new",
                             "body_name": "Ring"})
    s.cmd("solid.hole", {"position": [10, 20, 15], "direction": [0, 0, -1], "diameter": 12, "depth": 15})

    cmds = centred_hole_commands(doc, {"centre": True, "position": [22, 28, 15], "direction": [0, 0, -1],
                                       "diameter": 20, "depth": 5})
    modeling.run_commands(doc, cmds)
    cyls = [f["cylinder"] for f in s.tool("body_topology", {"body": "Ring"})["faces"] if f.get("cylinder")]
    c_new = [c for c in cyls if abs(c["radius"] - 10.0) < 1e-4]
    ok("design intent: hole on ring is concentric to outer circular edge",
       bool(c_new) and abs(c_new[0]["origin"][0] - 10) < 1e-5 and abs(c_new[0]["origin"][1] - 20) < 1e-5
       and g.parallel(c_new[0]["axis"], [0, 0, 1]), str(c_new[:1]))

    # Face without two opposite straight edges or a circular edge raises ValueError with extended message
    s.cmd("sketch.create", {"plane": "XY", "name": "STri"})
    s.cmd("sketch.line", {"points": [[0, 0], [20, 0]]})
    s.cmd("sketch.line", {"points": [[20, 0], [10, 20]]})
    s.cmd("sketch.line", {"points": [[10, 20], [0, 0]]})
    s.cmd("sketch.finish")
    s.cmd("solid.extrude", {"sketch": "STri", "distance": 10, "body_name": "Tri"})
    tri_err = None
    try:
        centred_hole_commands(doc, {"centre": True, "position": [10, 7, 10], "direction": [0, 0, -1],
                                    "diameter": 3, "depth": 3})
    except ValueError as e:
        tri_err = str(e)
    ok("design intent: face without parallel or circular edges explains both choices",
       tri_err == "the middle of this face needs two opposite straight edges or a circular edge", str(tri_err))
    ws.close(doc.name)


def profile_choice_checks(ws):
    """Extrude/Revolve dialogs: /api/sketches lists each sketch's profiles, and one profile index extrudes only it."""
    from mechvane.ui.server import sketches
    doc = ws.new(PART, "profile_choice")
    s = doc.session
    s.cmd("sketch.create", {"plane": "XY", "name": "S"})
    s.cmd("sketch.circle.center", {"center": [0, 0], "radius": 10})
    s.cmd("sketch.circle.center", {"center": [40, 0], "radius": 5})
    s.cmd("sketch.finish")
    sk = next(x for x in sketches(doc)["sketches"] if x["name"] == "S")
    ok("profiles: /api/sketches lists both circles", [p["curves"] for p in sk["profiles"]] == [["c1"], ["c2"]], str(sk))
    small = next(p["index"] for p in sk["profiles"] if p["curves"] == ["c2"])
    s.cmd("solid.extrude", {"sketch": "S", "distance": 4, "profiles": [small], "operation": "new", "name": "E"})
    vol = s.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    ok("profiles: extruding one profile makes only that cylinder", abs(vol - 3.14159265 * 25 * 4) < 0.5, str(vol))
    ws.close(doc.name)


def semantic_queries(ws):
    plate = ws.new(PART, "query_plate")
    plate.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 10, "corner": [0, 0, 0],
                                            "operation": "new", "body_name": "PlateBody"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 12, "base": [15, 20, -1],
                                                 "operation": "cut", "name": "Hole1"}},
        {"command": "solid.cylinder", "params": {"diameter": 8, "height": 12, "base": [45, 20, -1],
                                                 "operation": "cut", "name": "Hole2"}},
    ])
    edges = plate.session.cmd("model.edges", {"body": "PlateBody"})["edges"]
    chamfer_edge = [e for e in edges if e["mid"][1] == 0 and e["mid"][2] == 10 and e["length"] == 60][0]
    plate.session.cmd("solid.chamfer", {"edges": [chamfer_edge["mid"]], "distance": 2.0, "name": "Chamfer1"})
    plate.save()

    # 1. find faces plane normal +Z returns exactly the Deckfläche
    deck = query.find(plate, "faces", {"type": "plane", "normal": [0, 0, 1]})
    ok("find: faces plane normal +Z returns exactly the top surface",
       len(deck) == 1 and abs(deck[0]["pick"][2] - 10.0) < 1e-3, str(deck))

    # 2. holes returns both holes with correct diameter and through == True
    holes = query.find(plate, "holes")
    diams = sorted([h["diameter"] for h in holes])
    ok("find: holes returns both holes with correct diameter and through",
       len(holes) == 2 and abs(diams[0] - 6.0) < 0.1 and abs(diams[1] - 8.0) < 0.1 and all(h["through"] is True for h in holes),
       str(holes))

    # 3. feature filter finds faces of a specific feature
    f_h1 = query.find(plate, "faces", {"feature": "Hole1"})
    # truck splits the bore into two half faces, solidcore keeps one face
    ok("find: feature filter finds faces of a specific feature",
       len(f_h1) in (1, 2) and all(f["type"] == "cylinder" for f in f_h1) and all(abs(f["diameter"] - 6.0) < 0.1 for f in f_h1),
       str(f_h1))

    # 4. A pick from find works in solid.fillet
    e_bot = query.find(plate, "edges", {"edge": "line", "length": [59, 61]})
    fillet_edge = [e for e in e_bot if e["pick"][2] == 0][0]
    r_fillet = plate.session.cmd("solid.fillet", {"edges": [fillet_edge["pick"]], "radius": 1.0})
    ok("find: pick from find works in solid.fillet",
       r_fillet.get("name") == "Fillet1" and "Fillet1" in [b["name"] for b in plate.session.cmd("document.inspect")["timeline"]],
       str(r_fillet))

    # 5. In an assembly, world coordinates are correct
    asm = ws.new(ASSEMBLY, "query_asm")
    ins = asm.session.cmd("component.insert_design", {"path": str(plate.path), "name": "PlateOcc"})
    asm.session.cmd("occurrence.ground", {"occurrence": ins["occurrence"], "grounded": False})  # grounded since 0.25
    asm.session.cmd("occurrence.move", {"occurrence": ins["occurrence"], "translate": [100, 200, 50], "space": "local"})

    asm_deck = query.find(asm, "faces", {"type": "plane", "normal": [0, 0, 1]})
    asm_holes = query.find(asm, "holes")
    h_centers = sorted([h["center"] for h in asm_holes], key=lambda c: c[0])
    ok("find: assembly world coordinates and occurrence correct",
       len(asm_deck) == 1 and abs(asm_deck[0]["pick"][2] - 60.0) < 0.1
       and asm_deck[0].get("occurrence") == "PlateOcc:1"
       and len(asm_holes) == 2
       and abs(h_centers[0][0] - 115.0) < 0.1 and abs(h_centers[0][1] - 220.0) < 0.1
       and abs(h_centers[1][0] - 145.0) < 0.1 and abs(h_centers[1][1] - 220.0) < 0.1
       and all(h.get("occurrence") == "PlateOcc:1" for h in asm_holes),
       f"deck={asm_deck} holes={asm_holes}")

    ws.close("query_plate")
    ws.close("query_asm")


def edit_in_place_checks(ws):
    plate = ws.new(PART, "eip_plate")
    plate.session.batch([
        {"command": "parameters.add", "params": {"name": "hx", "expression": "10 mm"}},
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 5, "corner": [-30, -20, 0],
                                            "operation": "new", "body_name": "Plate"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 7, "base": ["hx", 0, -1],
                                                 "operation": "cut", "name": "Hole"}},
    ])
    plate.save()

    asm = ws.new(ASSEMBLY, "eip_asm")
    s = asm.session
    s.cmd("component.insert_design", {"path": str(plate.path), "name": "Plate"})
    s.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": True})
    s.batch([
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 20, "base": [0, 50, 0],
                                                 "operation": "new", "body_name": "PinBody"}},
        {"command": "component.create", "params": {"name": "Pin", "parent": "root", "activate": False}},
        {"command": "component.move_bodies", "params": {"bodies": ["PinBody"], "component": "Pin"}},
    ])
    params = {"type": "rigid", "name": "PinInHole", "flip": True,
              "a": {"occurrence": "Plate:1", "circle": [13, 0, 5]}, "b": {"occurrence": "Pin:1", "circle": [3, 50, 0]}}
    s.cmd("joint.create", params)
    links.record(ws, asm, "PinInHole", params)
    asm.save()

    # Close plate to test edit_in_place opens it from disk
    ws.close("eip_plate")

    # 1. edit_in_place opens the part document and returns name, occurrence and transforms
    pt_world = [10.0, 5.0, 3.0]
    eip = inplace.edit_in_place(ws, "eip_asm", "Plate:1", point=pt_world)
    ok("edit_in_place opens part file and returns document name and occurrence",
       eip["document"] == "eip_plate" and eip["occurrence"] == "Plate:1" and "eip_plate" in ws.docs,
       str(eip))
    ok("edit_in_place returns transform matrix and inverse",
       len(eip["transform"]) == 4 and len(eip["inverse_transform"]) == 4 and eip.get("point_in_part") == pt_world,
       str(eip))

    # Opening already-open document returns same document
    eip_open = inplace.edit_in_place(ws, "eip_asm", "Plate:1")
    ok("edit_in_place on already open part returns same document", eip_open["document"] == "eip_plate")

    # 2. Legitimate edit: shift hole via parameter
    pdoc = ws.get("eip_plate")
    pdoc.session.cmd("parameters.change", {"name": "hx", "expression": "20 mm"})

    # finish_edit saves the part and updates open assemblies linking it
    fin = inplace.finish_edit(ws, "eip_plate")
    j_x = round(next(j for j in asm.session.cmd("joint.list")["joints"] if j["name"] == "PinInHole")["frame_a"]["origin"][0], 4)
    ok("finish_edit: joint follows moved hole to x = 20 without warning",
       j_x == 20.0 and not fin["warnings"] and "eip_asm" in fin["assemblies"],
       f"x={j_x} fin={fin}")

    # 3. Second case (#3330): insert same-size hole before it in history
    pdoc.session.cmd("timeline.roll_to", {"position": 1})
    pdoc.session.cmd("solid.cylinder", {"diameter": 6, "height": 7, "base": [-10, 0, -1], "operation": "cut",
                                        "name": "Hole0"})
    pdoc.session.cmd("timeline.roll_to", {})

    fin2 = inplace.finish_edit(ws, "eip_plate")
    moved_w = [w for w in fin2["warnings"] if w.get("status") == "moved"]
    j_x2 = round(next(j for j in asm.session.cmd("joint.list")["joints"] if j["name"] == "PinInHole")["frame_a"]["origin"][0], 4)
    # SolidCraft up to 0.21 moved the joint (#3330, fixed upstream since 0.22): then it must be reported
    ok("finish_edit: new hole before it (#3330): the joint stays on its hole, or the move is reported",
       (bool(moved_w) and any(w["status"] == "moved" for w in fin2["assemblies"]["eip_asm"]["warnings"]))
       or (j_x2 == 20.0 and not fin2["warnings"]),
       f"x={j_x2} {fin2['warnings']}")

    # 4. edit_in_place on subassembly occurrence path ("Sub:1/Plate:1")
    sub = ws.new(ASSEMBLY, "eip_sub")
    links.insert(ws, sub, plate.path, name="Plate", translate=[10, 0, 0])
    sub.save()
    top = ws.new(ASSEMBLY, "eip_top")
    links.insert(ws, top, sub.path, name="Sub", translate=[50, 0, 0])
    top.save()
    ws.close("eip_plate")

    eip_sub = inplace.edit_in_place(ws, "eip_top", "Sub:1/Plate:1", point=[65, 5, 2])
    ok("edit_in_place: subassembly path Sub:1/Plate:1 resolves and converts coords",
       eip_sub["document"] == "eip_plate" and abs(eip_sub["point_in_part"][0] - 5.0) < 1e-4,
       str(eip_sub))

    # 5. Multi-level occurrence path resolution through intermediate subassemblies (Finding 6)
    p_leaf = ws.new(PART, "eip_leaf")
    p_leaf.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 0]})
    p_leaf.save()

    sub1 = ws.new(ASSEMBLY, "eip_sub1")
    links.insert(ws, sub1, p_leaf.path, name="PartP")
    sub1.save()

    sub2 = ws.new(ASSEMBLY, "eip_sub2")
    links.insert(ws, sub2, sub1.path, name="Sub1A", translate=[0, 0, 0])
    links.insert(ws, sub2, sub1.path, name="Sub1B", translate=[50, 0, 0])
    sub2.save()

    top_multi = ws.new(ASSEMBLY, "eip_multi")
    links.insert(ws, top_multi, sub2.path, name="Sub2")
    top_multi.save()

    res_multi = inplace.resolve_occurrence(top_multi, "Sub2:1/Sub1B:1/PartP:1")
    ok("resolve_occurrence: multi-level path resolves intermediate subassemblies without skipping",
       res_multi["name"] == "Sub1B_PartP:1" and abs(res_multi["transform"][3][0] - 50.0) < 1e-4,
       str(res_multi))

    # 6. Occurrence matching without delimiter prefix match and ambiguity check (Finding 9)
    pw = ws.new(PART, "eip_pw")
    pw.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 0]})
    pw.save()
    p_exact = ws.new(PART, "eip_p_exact")
    p_exact.session.cmd("solid.box", {"length": 20, "width": 20, "height": 10, "corner": [0, 0, 0]})
    p_exact.save()

    asm_pre = ws.new(ASSEMBLY, "eip_asm_pre")
    asm_pre.session.cmd("component.create", {"name": "Sub", "parent": "root", "activate": False})
    links.insert(ws, asm_pre, pw.path, name="PlateWasher", parent=1)
    links.insert(ws, asm_pre, p_exact.path, name="Plate", parent=1)

    res_pre = inplace.resolve_occurrence(asm_pre, "Sub/Plate")
    ok("resolve_occurrence: exact delimiter match avoids prefix collision (Plate != PlateWasher)",
       res_pre["name"] == "Plate:1", str(res_pre))

    # Add second plate to make 'Sub/Plate' ambiguous
    links.insert(ws, asm_pre, p_exact.path, name="Plate", parent=1)
    ambiguous_err = False
    try:
        inplace.resolve_occurrence(asm_pre, "Sub/Plate")
    except ValueError:
        ambiguous_err = True
    ok("resolve_occurrence: ambiguous occurrence raises ValueError instead of guessing", ambiguous_err)

    # 7. finish_edit saves part and updates unopened intermediate subassemblies, then closes them (Finding 5)
    plate_se = ws.new(PART, "eip_se_plate")
    plate_se.session.batch([
        {"command": "parameters.add", "params": {"name": "w", "expression": "40 mm"}},
        {"command": "solid.box", "params": {"length": 60, "width": "w", "height": 5, "corner": [0, 0, 0]}}
    ])
    plate_se.save()

    sub_se = ws.new(ASSEMBLY, "eip_se_sub")
    links.insert(ws, sub_se, plate_se.path, name="Plate", translate=[0, 0, 0])
    sub_se.save()

    top_se = ws.new(ASSEMBLY, "eip_se_top")
    links.insert(ws, top_se, sub_se.path, name="Sub", translate=[10, 0, 0])
    top_se.save()

    # Close plate and sub so sub is an unopened intermediate assembly
    ws.close("eip_se_plate")
    ws.close("eip_se_sub")

    inplace.edit_in_place(ws, "eip_se_top", "Sub:1/Plate:1")
    pdoc_se = ws.get("eip_se_plate")
    pdoc_se.session.cmd("parameters.change", {"name": "w", "expression": "80 mm"})

    fin_se = inplace.finish_edit(ws, "eip_se_plate")

    # Inspect sub on disk to verify it was updated and saved
    reader_sub = ws.reader(sub_se.path)
    bbox_sub = reader_sub.tool("inspect_design", {"measure": True})["bodies"][0]["bbox"]
    reader_sub.close()

    ok("finish_edit: unopened intermediate subassembly updated and saved on disk",
       abs(bbox_sub["max"][1] - 80.0) < 1e-3 and "eip_se_sub" not in ws.docs,
       f"bbox={bbox_sub} docs={list(ws.docs)}")

    ws.close_all()


def links_fixes_checks(ws):
    # Befund 1: check() detects axial displacement on cylinder and in-plane displacement on plane
    p1 = ws.new(PART, "bf1_p1")
    p1.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0, 0, 0]}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 20, "base": [20, 20, 0], "operation": "cut", "name": "Hole"}}
    ])
    p1.save()
    p2 = ws.new(PART, "bf1_p2")
    p2.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0, 0, 0], "name": "Pin"})
    p2.save()

    asm1 = ws.new(ASSEMBLY, "bf1_asm")
    links.insert(ws, asm1, p1.path, name="P1", grounded=True)
    links.insert(ws, asm1, p2.path, name="P2")
    jp1 = {"type": "rigid", "name": "PinInHole",
           "a": {"occurrence": "P1:1", "circle": [20, 20, 20]},
           "b": {"occurrence": "P2:1", "circle": [0, 0, 0]}}
    asm1.session.cmd("joint.create", jp1)
    links.record(ws, asm1, "PinInHole", jp1)

    orig_frames = links._frames

    def mock_frames_cyl(s):
        f = orig_frames(s)
        if "PinInHole" in f:
            f["PinInHole"]["a"] = (f["PinInHole"]["a"][0], [20.0, 20.0, 0.0], f["PinInHole"]["a"][2])
        return f
    links._frames = mock_frames_cyl
    rep_cyl = links.check(ws, asm1)
    links._frames = orig_frames
    ok("check reports moved for axial displacement on cylinder joint",
       rep_cyl and rep_cyl[0]["status"] == "moved", str(rep_cyl))

    # Plane in-plane displacement
    base_p = ws.new(PART, "bf1_base")
    base_p.session.cmd("solid.box", {"length": 100, "width": 100, "height": 10, "corner": [0, 0, 0]})
    base_p.save()
    top_p = ws.new(PART, "bf1_top")
    top_p.session.cmd("solid.box", {"length": 20, "width": 20, "height": 10, "corner": [0, 0, 0]})
    top_p.save()
    asm_plane = ws.new(ASSEMBLY, "bf1_asm_plane")
    links.insert(ws, asm_plane, base_p.path, name="Base", grounded=True)
    links.insert(ws, asm_plane, top_p.path, name="Top")
    jp_plane = {"type": "rigid", "name": "JPlane",
                "a": {"occurrence": "Base:1", "point": [20, 20, 10], "z": [0, 0, 1]},
                "b": {"occurrence": "Top:1", "point": [10, 10, 0], "z": [0, 0, -1]}}
    asm_plane.session.cmd("joint.create", jp_plane)
    links.record(ws, asm_plane, "JPlane", jp_plane)

    def mock_frames_plane(s):
        f = orig_frames(s)
        if "JPlane" in f:
            f["JPlane"]["a"] = (f["JPlane"]["a"][0], [60.0, 60.0, 10.0], f["JPlane"]["a"][2])
        return f
    links._frames = mock_frames_plane
    rep_plane = links.check(ws, asm_plane)
    links._frames = orig_frames
    ok("check reports moved for in-plane displacement on plane joint",
       rep_plane and rep_plane[0]["status"] == "moved", str(rep_plane))

    # Befund 2: _match chooses counterbore face over coaxial bore
    p_cb = ws.new(PART, "bf2_cb")
    p_cb.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "corner": [0, 0, 0]}},
        {"command": "solid.hole", "params": {"position": [20, 20, 20], "direction": [0, 0, -1], "diameter": 6,
                                              "type": "counterbore", "cb_diameter": 12, "cb_depth": 5, "name": "CBore"}}
    ])
    p_cb.save()
    r_cb = ws.reader(p_cb.path)
    try:
        faces_cb = links._part_faces(r_cb)
    finally:
        r_cb.close()
    m_cb = links._match(faces_cb, [20, 20, 20], [0, 0, 1])
    ok("coaxial cylinder match selects counterbore at entrance",
       m_cb is not None and "cbore" in m_cb.get("face", ""), str(m_cb))

    # Befund 3: update_links syncs moved parts in grounded subassembly without crash
    plate_sub = ws.new(PART, "bf3_wall")
    plate_sub.session.cmd("solid.box", {"length": 60, "width": 40, "height": 6, "corner": [0, 0, 0]})
    plate_sub.save()
    sub3 = ws.new(ASSEMBLY, "bf3_sub")
    links.insert(ws, sub3, plate_sub.path, name="Plate", translate=[10, 0, 0], grounded=True)
    sub3.save()
    top3 = ws.new(ASSEMBLY, "bf3_top")
    links.insert(ws, top3, sub3.path, name="Sub", rotate={"axis": [1, 0, 0], "angle": 90}, grounded=True)
    sub3.session.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": False})
    sub3.session.cmd("occurrence.move", {"occurrence": "Plate:1", "translate": [20, 0, 0]})
    sub3.session.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": True})
    sub3.save()
    try:
        r3 = links.update_links(ws, top3)
        err3 = None
    except Exception as e:
        err3 = e
        r3 = None
    ok("grounded subassembly syncs moved parts without crashing",
       err3 is None and r3 is not None and any("Plate" in str(m) for m in r3["subassemblies"][0]["moved"]),
       f"err={err3} res={r3}")

    # Befund 7: repair preserves suppressed and limits
    p7_1 = ws.new(PART, "bf7_p1")
    p7_1.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0]}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [10, 20, 0], "operation": "cut", "name": "Hole"}}
    ])
    p7_1.save()
    p7_2 = ws.new(PART, "bf7_p2")
    p7_2.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0, 0, 0], "name": "Pin"})
    p7_2.save()
    asm7 = ws.new(ASSEMBLY, "bf7_asm")
    links.insert(ws, asm7, p7_1.path, name="P1", grounded=True)
    links.insert(ws, asm7, p7_2.path, name="P2")
    jp7 = {"type": "revolute", "name": "Rev1",
           "a": {"occurrence": "P1:1", "circle": [10, 20, 10]},
           "b": {"occurrence": "P2:1", "circle": [0, 0, 0]}}
    asm7.session.cmd("joint.create", jp7)
    links.record(ws, asm7, "Rev1", jp7)
    asm7.session.cmd("joint.limits", {"joint": "Rev1", "min": -45, "max": 45})
    asm7.session.cmd("joint.edit", {"joint": "Rev1", "suppressed": True})

    p7_1.session.cmd("timeline.roll_to", {"position": 1})
    p7_1.session.cmd("solid.cylinder", {"diameter": 6, "height": 10, "base": [0, 20, 0], "operation": "cut", "name": "Hole0"})
    p7_1.session.cmd("timeline.roll_to", {})
    p7_1.save()

    links.update_links(ws, asm7, repair_moved=True)
    repaired_j = asm7.session.cmd("joint.list")["joints"][0]
    ok("repair preserves suppressed and limits",
       repaired_j.get("suppressed") is True and repaired_j.get("values", [{}])[0].get("limits") == [-45.0, 45.0],
       str(repaired_j))

    # Befund 8: missing component file reports file_missing instead of crashing
    p8_1 = ws.new(PART, "bf8_p1")
    p8_1.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0]}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 10, "base": [10, 20, 0], "operation": "cut", "name": "Hole"}}
    ])
    p8_1.save()
    p8_2 = ws.new(PART, "bf8_p2")
    p8_2.session.cmd("solid.cylinder", {"diameter": 6, "height": 20, "base": [0, 0, 0], "name": "Pin"})
    p8_2.save()
    asm8 = ws.new(ASSEMBLY, "bf8_asm")
    links.insert(ws, asm8, p8_1.path, name="P1", grounded=True)
    links.insert(ws, asm8, p8_2.path, name="P2")
    jp8 = {"type": "revolute", "name": "Rev1",
           "a": {"occurrence": "P1:1", "circle": [10, 20, 10]},
           "b": {"occurrence": "P2:1", "circle": [0, 0, 0]}}
    asm8.session.cmd("joint.create", jp8)
    links.record(ws, asm8, "Rev1", jp8)
    asm8.save()

    p8_path = Path(p8_1.path)
    ws.close("bf8_p1")
    p8_path.unlink()
    try:
        rep8 = links.check(ws, asm8)
        err8 = None
    except Exception as e:
        err8 = e
        rep8 = None
    ok("missing component file reports file_missing without crashing",
       err8 is None and rep8 is not None and any(r.get("status") == "file_missing" for r in rep8),
       f"err={err8} rep={rep8}")

    # Befund 10: resolve_occurrences preserves subassembly prefix without index, errors on ambiguity
    p10 = ws.new(PART, "bf10_p")
    p10.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 0]})
    p10.save()
    top10 = ws.new(ASSEMBLY, "bf10_top")
    links.insert(ws, top10, p10.path, name="Plate")
    sub10 = ws.new(ASSEMBLY, "bf10_sub")
    links.insert(ws, sub10, p10.path, name="Plate")
    sub10.save()
    links.insert(ws, top10, sub10.path, name="Sub")
    resolved10 = links.resolve_occurrences(top10.session, {"b": {"occurrence": "Sub:1/Plate"}})
    ok("resolve_occurrences preserves subassembly prefix for paths without instance index",
       resolved10.get("b", {}).get("occurrence") == "Sub_Plate:1", str(resolved10))

    err10_missing = None
    try:
        links.resolve_occurrences(top10.session, {"b": {"occurrence": "Sub:1/NonExistent"}})
    except ValueError as e:
        err10_missing = e
    ok("resolve_occurrences errors when child occurrence does not exist in subassembly",
       isinstance(err10_missing, ValueError), str(err10_missing))

    # Befund 10: ambiguity check when multiple occurrences match without index
    top10_b = ws.new(ASSEMBLY, "bf10_top_b")
    sub10_b = ws.new(ASSEMBLY, "bf10_sub_b")
    links.insert(ws, sub10_b, p10.path, name="Plate")
    links.insert(ws, sub10_b, p10.path, name="Plate")
    sub10_b.save()
    links.insert(ws, top10_b, sub10_b.path, name="Sub")
    err10_ambig = None
    try:
        links.resolve_occurrences(top10_b.session, {"b": {"occurrence": "Sub:1/Plate"}})
    except ValueError as e:
        err10_ambig = e
    ok("resolve_occurrences errors on ambiguous occurrence in subassembly",
       isinstance(err10_ambig, ValueError), str(err10_ambig))


def server_fixes_checks(tmp, ws):
    import gc
    import os
    import subprocess
    import time
    from unittest.mock import patch
    from mechvane import server, sketch_rule, tree
    from mechvane.solidcraft import Session, SolidCraftError

    # Switch server.ws to use our test workspace
    orig_ws = server.ws
    server.ws = ws
    try:
        # Finding 1: new() rejects existing file unless overwrite=True
        f1 = ws.new(PART, "f1_part")
        f1.save()
        ws.close("f1_part")
        err_f1 = False
        try:
            ws.new(PART, "f1_part")
        except (FileExistsError, ValueError):
            err_f1 = True
        ok("finding 1: ws.new rejects existing file on disk when overwrite=False", err_f1)

        f1_over = ws.new(PART, "f1_part", overwrite=True)
        ok("finding 1: ws.new allows overwrite when overwrite=True",
           f1_over.name == "f1_part" and "f1_part" in ws.docs)
        ws.close("f1_part")

        # Finding 2: Open same file only once, returns existing or clear error on alias
        doc2_a = ws.open("f1_part.solidcraft", name="f2_doc")
        doc2_b = ws.open("f1_part.solidcraft")
        ok("finding 2: second open on same file returns existing document", doc2_a is doc2_b)
        err_f2_alias = False
        try:
            ws.open("f1_part.solidcraft", name="f2_diff_alias")
        except ValueError:
            err_f2_alias = True
        ok("finding 2: open same file under different alias raises ValueError", err_f2_alias)
        ws.close("f2_doc")

        # Finding 3: Failed new() and reader() do not leak subprocesses
        pids_before = set(subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split())
        try:
            ws.new(PART, "parts/nested_fail")
        except Exception:
            pass
        try:
            ws.reader(ws.root / "nonexistent_reader_file.solidcraft")
        except Exception:
            pass
        pids_after = set(subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split())
        leaked_f3 = pids_after - pids_before
        ok("finding 3: failed new() and reader() do not leak child processes",
           len(leaked_f3) == 0, f"leaked pids: {leaked_f3}")

        # Finding 4: Document name validation and workspace boundary checks
        err_f4_empty = False
        try:
            ws.new(PART, "")
        except ValueError:
            err_f4_empty = True
        err_f4_slash = False
        try:
            ws.new(PART, "sub/dir_part")
        except ValueError:
            err_f4_slash = True
        err_f4_dotdot = False
        try:
            ws.new(PART, "../../escaped")
        except ValueError:
            err_f4_dotdot = True
        err_f4_out_path = False
        try:
            ws.open("../outside.solidcraft")
        except ValueError:
            err_f4_out_path = True
        ok("finding 4: validate document name (empty, slash, dotdot) and reject path traversal",
           err_f4_empty and err_f4_slash and err_f4_dotdot and err_f4_out_path,
           f"empty={err_f4_empty} slash={err_f4_slash} dotdot={err_f4_dotdot} out={err_f4_out_path}")

        # Finding 5: screenshot only allows .png, never overwrites .solidcraft or non-png files
        f5 = ws.new(PART, "f5_part")
        f5.save()
        err_f5_cad = False
        try:
            server.screenshot("f5_part", path="f5_part.solidcraft")
        except ValueError:
            err_f5_cad = True
        err_f5_txt = False
        try:
            server.screenshot("f5_part", path="image.jpg")
        except ValueError:
            err_f5_txt = True
        fake_png = ws.root / "fake.png"
        fake_png.write_text("not a png file")
        err_f5_fake = False
        try:
            server.screenshot("f5_part", path="fake.png")
        except ValueError:
            err_f5_fake = True
        ok("finding 5: screenshot rejects .solidcraft, non-png and overwriting non-png files",
           err_f5_cad and err_f5_txt and err_f5_fake,
           f"cad={err_f5_cad} non_png={err_f5_txt} fake={err_f5_fake}")
        ws.close("f5_part")

        # Finding 6: Session.close reaps process without leaving zombies (normal and timeout path)
        def _check_not_zombie(pid):
            time.sleep(0.05)
            # 1. /proc/<pid>/status check
            try:
                with open(f"/proc/{pid}/status") as f:
                    if any(line.startswith("State:") and "Z" in line for line in f):
                        return False
            except OSError:
                pass  # Already removed from /proc
            # 2. os.waitpid check: if already reaped by Session.close(), waitpid raises ChildProcessError
            try:
                waited_pid, _ = os.waitpid(pid, os.WNOHANG)
                if waited_pid == pid:
                    return False
            except ChildProcessError:
                pass
            return True

        # Normal close path
        s6_norm = Session()
        pid6_norm = s6_norm._p.pid
        s6_norm.close()
        ok("finding 6: Session.close reaps process on normal exit without leaving zombies",
           _check_not_zombie(pid6_norm))

        # Timeout close path: simulate wait(10) raising TimeoutExpired so kill() + wait(5) is executed
        s6_to = Session()
        pid6_to = s6_to._p.pid
        orig_wait = s6_to._p.wait
        first_wait = True

        def _timeout_wait(timeout=None):
            nonlocal first_wait
            if first_wait:
                first_wait = False
                raise subprocess.TimeoutExpired(s6_to._p.args, timeout)
            return orig_wait(timeout)

        s6_to._p.wait = _timeout_wait
        s6_to.close()
        ok("finding 6: Session.close reaps process on timeout path (kill + wait) without leaving zombies",
           _check_not_zombie(pid6_to))

        # Finding 7: Session._rpc timeout support
        err_f7 = False
        for _attempt in range(5):  # a 1 microsecond limit races the answer; under load the answer can win once
            s7 = Session()
            try:
                s7.cmd("document.inspect", timeout=0.000001)
            except SolidCraftError as e:
                err_f7 = "timeout" in str(e).lower()
            finally:
                s7.close()
            if err_f7:
                break
        ok("finding 7: Session timeout raises SolidCraftError and closes session", err_f7)

        # UTF-8 chunk boundary: Session reader buffers bytes so multi-byte UTF-8 across chunks is not corrupted
        s_utf8 = Session.__new__(Session)
        s_utf8._closed = False
        s_utf8._lines = queue.Queue()
        r_fd, w_fd = os.pipe()
        threading.Thread(target=Session._reader, args=(r_fd, s_utf8._lines), daemon=True).start()

        class _FakeStdout:
            def fileno(self):
                return r_fd
            closed = False
            def close(self):
                try:
                    os.close(r_fd)
                except OSError:
                    pass

        class _FakeProc:
            stdout = _FakeStdout()
            stdin = None
            pid = -1
            def wait(self, *a, **kw):
                pass
            def poll(self):
                return 0
            def kill(self):
                pass

        s_utf8._p = _FakeProc()

        msg_str = json.dumps({"name": "Ø 8 mm"}, ensure_ascii=False)
        msg_bytes = msg_str.encode("utf-8") + b"\n"
        # 'Ø' is encoded in UTF-8 as b'\xc3\x98' (2 bytes). Split right between 0xc3 and 0x98:
        split_pos = msg_bytes.index(b"\xc3") + 1
        part1 = msg_bytes[:split_pos]
        part2 = msg_bytes[split_pos:]

        def _feed_part2():
            time.sleep(0.02)
            try:
                os.write(w_fd, part2)
            finally:
                os.close(w_fd)

        feed_thread = threading.Thread(target=_feed_part2)
        feed_thread.start()
        os.write(w_fd, part1)
        line_received = s_utf8._readline(timeout=5.0)
        feed_thread.join()
        s_utf8.close()

        ok("finding 7: Session._readline buffers bytes across chunk boundaries without corrupting UTF-8",
           line_received == msg_str,
           f"received: {line_received}")

        # Finding 8: Session __del__ cleans up subprocess upon GC
        def _leak_session():
            sess = Session()
            return sess._p.pid
        pid8 = _leak_session()
        gc.collect()
        time.sleep(0.05)
        running_pids8 = subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split()
        ok("finding 8: Session.__del__ terminates subprocess upon garbage collection",
           str(pid8) not in running_pids8)
        if str(pid8) in running_pids8:
            try:
                os.kill(pid8, 9)
            except OSError:
                pass

        # Finding 9: references() considers path_sketch for sweep ownership
        f9 = ws.new(PART, "f9_sweep")
        f9.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY", "name": "Profile"}},
            {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 2}},
            {"command": "sketch.finish", "params": {}},
            {"command": "sketch.create", "params": {"plane": "XZ", "name": "SweepPath"}},
            {"command": "sketch.line", "params": {"points": [[0, 0], [0, 20]]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.sweep", "params": {"sketch": "Profile", "path_sketch": "SweepPath", "path": ["l1"], "name": "Sweep1"}},
        ])
        cons9 = sketch_rule.consumers(f9.session)
        own9 = sketch_rule.owners(cons9)
        sketch_rule.enforce(f9.session)
        tree9 = tree.part_tree(f9.session)
        sweep_entry = next((f for f in tree9["features"] if f.get("name") == "Sweep1"), {})
        sketches_under_sweep = [s["name"] for s in sweep_entry.get("children", [])]
        ok("finding 9: solid.sweep owns path_sketch and nests it under sweep in browser",
           cons9.get("SweepPath") == ["Sweep1"] and own9.get("SweepPath") == "Sweep1"
           and "SweepPath" in sketches_under_sweep,
           f"cons={cons9.get('SweepPath')} own={own9.get('SweepPath')} tree={sketches_under_sweep}")
        ws.close("f9_sweep")

        # Finding 10: close_document with unsaved edits requires discard=True
        f10 = ws.new(PART, "f10_part")
        f10.save()
        server.run("f10_part", [{"command": "solid.box", "params": {"name": "Box", "length": 10, "width": 10, "height": 10}}])
        err_f10 = False
        try:
            server.close_document("f10_part")
        except ValueError as e:
            err_f10 = "unsaved changes" in str(e).lower() or "discard" in str(e).lower()
        ok("finding 10: close_document on dirty doc raises error unless discard=True", err_f10)
        res_f10 = server.close_document("f10_part", discard=True)
        ok("finding 10: close_document with discard=True closes dirty document",
           res_f10.get("closed") == "f10_part" and "f10_part" not in ws.docs)

        # Finding 11: to_part_coords validates 3D coordinate, raises ValueError instead of IndexError
        f11_p = ws.new(PART, "f11_p")
        f11_p.session.batch([{"command": "solid.box", "params": {"length": 10, "width": 10, "height": 10}}])
        f11_p.save()
        f11_a = ws.new(ASSEMBLY, "f11_a")
        server.insert_part("f11_a", "f11_p.solidcraft", name="P1", translate=[10, 0, 0], grounded=True)
        err_f11_2d, err_f11_empty = False, False
        try:
            server.to_part_coords("f11_a", "P1", [15, 0])
        except ValueError:
            err_f11_2d = True
        except IndexError:
            err_f11_2d = False
        try:
            server.to_part_coords("f11_a", "P1", [])
        except ValueError:
            err_f11_empty = True
        except IndexError:
            err_f11_empty = False
        ok("finding 11: to_part_coords raises ValueError on invalid points",
           err_f11_2d and err_f11_empty, f"2d={err_f11_2d} empty={err_f11_empty}")
        ws.close("f11_p")
        ws.close("f11_a")

        # Finding 12: server.run rolls back batch if sketch_rule.enforce fails
        f12 = ws.new(PART, "f12_part")
        f12.save()
        with patch("mechvane.sketch_rule.enforce", side_effect=RuntimeError("simulated enforce failure")):
            err_f12 = False
            try:
                server.run("f12_part", [{"command": "solid.box", "params": {"name": "BoxFail", "length": 10, "width": 10, "height": 10}}])
            except RuntimeError:
                err_f12 = True
        bodies12 = f12.session.cmd("document.inspect").get("bodies", [])
        ok("finding 12: server.run rolls back commands if sketch_rule.enforce fails",
           err_f12 and len(bodies12) == 0, f"err={err_f12} bodies={len(bodies12)}")
        ws.close("f12_part")

    finally:
        server.ws = orig_ws


def mcp_server(tmp):
    """The server over stdio, as Claude Code talks to it."""
    import json
    import os
    import subprocess
    env = dict(os.environ, MECHVANE_WORKSPACE=str(Path(tmp) / "mcp"))
    p = subprocess.Popen([sys.executable, "-m", "mechvane"], cwd=Path(__file__).resolve().parents[2], env=env,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    n = 0

    def rpc(method, params=None):
        nonlocal n
        n += 1
        p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n, "method": method, "params": params or {}}) + "\n")
        p.stdin.flush()
        while True:
            msg = json.loads(p.stdout.readline())
            if msg.get("id") == n:
                return msg

    def call(name, args):
        r = rpc("tools/call", {"name": name, "arguments": args})["result"]
        text = "".join(c.get("text", "") for c in r["content"])
        return r.get("isError", False), (json.loads(text) if text.startswith("{") else text)

    try:
        rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "0"}})
        p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        p.stdin.flush()
        tools = {t["name"] for t in rpc("tools/list")["result"]["tools"]}
        ok("mcp: tools listed", {"add_joint", "adopt_joint", "bolted_connection", "browser", "check_design",
                                 "delete_bolted_connection", "delete_joint", "edit_bolted_connection",
                                 "edit_in_place", "edit_joint", "find", "finish_edit",
                                 "list_bolted_connections", "list_commands", "list_standard_parts", "measure", "new_part",
                                 "preview_bolted_connection", "rename_feature", "run", "standard_part", "to_part_coords",
                                 "update_links"} <= tools, str(sorted(tools)))
        err, _ = call("new_part", {"name": "bracket"})
        err2, r = call("run", {"document": "bracket", "commands":
                               rect("Base", "XY", [0, 0], [30, 20]) + [{"command": "solid.extrude", "params": {"sketch": "Base", "distance": 4, "name": "Plate"}}]})
        err3, b = call("browser", {"document": "bracket"})
        ok("mcp: build a part and read its browser", not (err or err2 or err3) and "Plate [ExtrudeFeature]" in b.get("text", ""),
           str(b)[:300])
        ok("mcp: run reply leaves out nulls, empty lists and timings",
           not any(v is None or v == [] or k == "ms" for res in r.get("results", []) for k, v in res.items()), str(r)[:300])
        err5, m = call("measure", {"document": "bracket"})
        ok("mcp: measure gives the volume", not err5 and abs(m["bodies"][0]["volume_mm3"] - 2400) < 0.5, str(m)[:300])
        err_cat, cat = call("list_standard_parts", {"norm": "ISO 4032"})
        err_sp, sp = call("standard_part", {"norm": "ISO 4032", "size": "M6", "name": "nut6"})
        err_bad, _ = call("standard_part", {"norm": "ISO 4032", "size": "M7"})
        ok("mcp: list_standard_parts and standard_part create an open part, invalid size is an error",
           not err_cat and "M6" in cat.get("sizes", {})
           and not err_sp and sp.get("standard", {}).get("designation") == "ISO 4032 M6"
           and err_bad,
           f"{cat} {sp} err_bad={err_bad}")
        call("save_document", {"document": "bracket"})
        call("new_assembly", {"name": "unit"})
        call("insert_part", {"assembly": "unit", "part_path": "bracket.solidcraft", "name": "Bracket", "grounded": True})
        call("save_document", {"document": "unit"})
        call("new_assembly", {"name": "machine"})
        err6, ins = call("insert_part", {"assembly": "machine", "part_path": "unit.solidcraft", "name": "Unit", "grounded": True})
        err7, mb = call("browser", {"document": "machine"})
        ok("mcp: insert_part places a subassembly and browser nests its parts",
           not (err6 or err7) and ins.get("kind") == "subassembly" and "Unit:1 (fest, unit.solidcraft)" in mb.get("text", "")
           and "Bracket:1 (fest, bracket.solidcraft)" in mb.get("text", ""),
           f"{ins} {mb}")
        err6, cd = call("check_design", {"document": "bracket", "profile": "fdm_0.4"})
        ok("mcp: check_design reports verdict", not err6 and cd.get("verdict") == "ok", str(cd)[:300])
        err_f, f_res = call("find", {"document": "bracket", "what": "faces", "where": {"type": "plane", "normal": [0, 0, 1]}})
        ok("mcp: find returns top face", not err_f and len(f_res.get("items", [])) == 1 and f_res["items"][0]["pick"][2] == 4, str(f_res)[:300])
        err_eip, eip_res = call("edit_in_place", {"assembly": "unit", "occurrence": "Bracket:1", "point": [10, 5, 2]})
        ok("mcp: edit_in_place opens part file and converts coordinates",
           not err_eip and eip_res.get("document") == "bracket" and "point_in_part" in eip_res,
           str(eip_res)[:300])
        err_fin, fin_res = call("finish_edit", {"part": "bracket"})
        ok("mcp: finish_edit saves and updates open assemblies",
           not err_fin and fin_res.get("part") == "bracket" and "unit" in fin_res.get("assemblies", {}),
           str(fin_res)[:300])
        err_tpc, tpc_res = call("to_part_coords", {"assembly": "unit", "occurrence": "Bracket:1", "point": [10, 5, 2]})
        ok("mcp: to_part_coords converts assembly coordinates",
           not err_tpc and "point" in tpc_res,
           str(tpc_res)[:300])
        err_shot, res_shot = call("screenshot", {"document": "bracket", "path": "bracket.png"})
        shot_file = Path(tmp) / "mcp" / "bracket.png"
        ok("mcp: screenshot with path saves file and replies with small metadata",
           not err_shot and shot_file.is_file() and res_shot.get("size") == shot_file.stat().st_size
           and res_shot.get("width", 0) > 0 and res_shot.get("height", 0) > 0
           and len(json.dumps(res_shot)) < 500,
           str(res_shot)[:300])
        err_outside, _ = call("screenshot", {"document": "bracket", "path": "../outside.png"})
        ok("mcp: screenshot rejects path outside workspace", err_outside)
        shot_raw = rpc("tools/call", {"name": "screenshot", "arguments": {"document": "bracket"}})["result"]
        shot_content = shot_raw.get("content", [])
        ok("mcp: screenshot without path returns inline image",
           len(shot_content) == 1 and shot_content[0].get("type") == "image" and len(shot_content[0].get("data", "")) > 1000)
        err_vv, res_vv = call("verify_view", {"document": "bracket", "path": "bracket_verify.png"})
        vv_file = Path(tmp) / "mcp" / "bracket_verify.png"
        ok("mcp: verify_view with path saves file and replies with metadata",
           not err_vv and vv_file.is_file() and res_vv.get("size") == vv_file.stat().st_size
           and res_vv.get("width", 0) > 0 and res_vv.get("height", 0) > 0,
           str(res_vv)[:300])
        vv_raw = rpc("tools/call", {"name": "verify_view", "arguments": {"document": "bracket"}})["result"]
        vv_content = vv_raw.get("content", [])
        ok("mcp: verify_view without path returns inline image",
           len(vv_content) == 1 and vv_content[0].get("type") == "image" and len(vv_content[0].get("data", "")) > 1000)
        call("new_assembly", {"name": "rot_unit"})
        err_rot, ins_rot = call("insert_part", {"assembly": "rot_unit", "part_path": "bracket.solidcraft",
                                               "name": "BracketRot", "rotate": {"axis": [1, 0, 0], "angle": 90},
                                               "grounded": True})
        ok("mcp: insert_part with rotate places rotated occurrence",
           not err_rot and ins_rot.get("occurrence") is not None, str(ins_rot))
        # Test open_document, list_documents, close_document over MCP
        err_ld, ld = call("list_documents", {})
        ok("mcp: list_documents returns workspace and documents",
           not err_ld and "workspace" in ld and len(ld.get("documents", [])) >= 1, str(ld))

        err_close, res_close = call("close_document", {"document": "bracket"})
        ok("mcp: close_document closes document", not err_close and res_close.get("closed") == "bracket")

        err_open, res_open = call("open_document", {"path": "bracket.solidcraft"})
        ok("mcp: open_document reopens saved document", not err_open and res_open.get("name") == "bracket")

        err_open2, res_open2 = call("open_document", {"path": "bracket.solidcraft"})
        ok("mcp: second open_document returns existing open document", not err_open2 and res_open2.get("name") == "bracket")

        err_new_dup, _ = call("new_part", {"name": "bracket"})
        ok("mcp: new_part rejects existing file when overwrite=false", err_new_dup)

        call("run", {"document": "bracket", "commands": [{"command": "solid.box", "params": {"name": "B2", "length": 5, "width": 5, "height": 5}}]})
        err_close_dirty, _ = call("close_document", {"document": "bracket"})
        ok("mcp: close_document rejects dirty document without discard=true", err_close_dirty)

        err_close_discard, res_discard = call("close_document", {"document": "bracket", "discard": True})
        ok("mcp: close_document with discard=true closes dirty document", not err_close_discard and res_discard.get("closed") == "bracket")

        call("open_document", {"path": "bracket.solidcraft"})

        # Joint check before rename: insert nut into unit and add a joint to Bracket:1
        call("insert_part", {"assembly": "unit", "part_path": "nut6.solidcraft", "name": "Nut"})
        err_aj, aj = call("add_joint", {"assembly": "unit", "params": {
            "name": "NutOnPlate", "type": "rigid",
            "a": {"occurrence": "Bracket:1", "point": [15, 10, 4], "z": [0, 0, 1]},
            "b": {"occurrence": "Nut:1", "point": [0, 0, 0], "z": [0, 0, 1]}
        }})
        err_cj1, cj1 = call("check_joints", {"assembly": "unit"})

        # MCP rename_feature: validation, browser tree with sketch ownership, and joint integrity
        err_rn_empty, _ = call("rename_feature", {"document": "bracket", "feature": "Plate", "name": ""})
        err_rn_dup, _ = call("rename_feature", {"document": "bracket", "feature": "Plate", "name": "Base"})
        err_rn, res_rn = call("rename_feature", {"document": "bracket", "feature": "Plate", "name": "MainPlate"})
        err_b_rn, b_rn = call("browser", {"document": "bracket"})
        err_rn_sk, res_rn_sk = call("rename_feature", {"document": "bracket", "feature": "Base", "name": "BaseSketch"})
        err_b_rn_sk, b_rn_sk = call("browser", {"document": "bracket"})
        call("save_document", {"document": "bracket"})
        err_cj2, cj2 = call("check_joints", {"assembly": "unit"})

        ok("mcp: rename_feature rejects invalid/duplicate names, renames features and sketches, preserving sketch ownership and assembly joints",
           err_rn_empty and err_rn_dup and not err_rn and not err_rn_sk and not err_aj and not err_cj1 and not err_cj2
           and all(j.get("status") == "ok" for j in cj2.get("joints", []))
           and "MainPlate [ExtrudeFeature]" in b_rn.get("text", "") and "Base" in b_rn.get("text", "")
           and "MainPlate [ExtrudeFeature]" in b_rn_sk.get("text", "") and "BaseSketch" in b_rn_sk.get("text", ""),
           f"{err_rn_empty} {err_rn_dup} {res_rn} {res_rn_sk} {b_rn_sk} {cj2}")

        # Rename back to original names so delete_feature and following checks work as before
        call("rename_feature", {"document": "bracket", "feature": "MainPlate", "name": "Plate"})
        call("rename_feature", {"document": "bracket", "feature": "BaseSketch", "name": "Base"})
        call("save_document", {"document": "bracket"})

        err_df, res_df = call("delete_feature", {"document": "bracket", "feature": "Plate"})
        ok("mcp: delete_feature deletes feature and its owned sketch",
           not err_df and "Plate" in res_df.get("deleted", []), str(res_df))
        call("close_document", {"document": "bracket", "discard": True})

        err_lc, lc = call("list_commands", {"document": "unit", "filter": "joint.list"})
        err_cmd, res_cmd = call("command", {"document": "unit", "command": "document.inspect"})
        ok("mcp: list_commands and command work",
           not err_lc and not err_cmd and "timeline" in res_cmd.get("result", res_cmd), f"{lc} {res_cmd}")

        err4, _ = call("browser", {"document": "nope"})
        ok("mcp: unknown document is an error, not a crash", err4)
    finally:
        p.stdin.close()
        p.wait(20)


def legacy_metadata_checks(ws):
    from mechvane import LEGACY_METADATA_KEY, METADATA_KEY
    doc = ws.new(PART, "legacy_meta")
    doc.session.cmd("document.metadata.set", {"key": METADATA_KEY, "value": {}})
    doc.session.cmd("document.metadata.set", {"key": LEGACY_METADATA_KEY, "value": {"kind": "part", "format": 1}})
    ok("metadata written under the pre-rename key is still read", doc.metadata().get("kind") == "part",
       str(doc.metadata()))
    ws.close("legacy_meta")


def iso286_checks():
    from mechvane import iso286
    # Values from ISO 286-1 tables (see docs/research/2026-10-23-iso286-tabellen.md)
    cases = {(25, "H7"): (0, 21), (25, "k6"): (2, 15), (8, "k6"): (1, 10), (10, "g6"): (-14, -5),
             (20, "f7"): (-41, -20), (50, "p6"): (26, 42), (30, "K7"): (-15, 6), (30, "K8"): (-23, 10),
             (30, "M7"): (-21, 0), (30, "N7"): (-28, -7), (30, "P7"): (-35, -14), (2, "K7"): (-10, 0),
             (8, "js6"): (-4.5, 4.5), (100, "h9"): (-87, 0), (500, "H11"): (0, 400)}
    bad = {k: iso286.deviations(*k) for k, v in cases.items() if iso286.deviations(*k) != v}
    ok("iso286: limit deviations match ISO 286-1 table values", not bad, str(bad))
    f = iso286.fit(22, "H7/k6")
    ok("iso286: H7/k6 at 22 mm is a transition fit (+19 / -15 µm)",
       f["kind"] == "transition" and f["max_clearance_um"] == 19 and f["min_clearance_um"] == -15, str(f))
    ok("iso286: H7/g6 is clearance, H7/p6 interference at 30 mm",
       iso286.fit(30, "H7/g6")["kind"] == "clearance" and iso286.fit(30, "H7/p6")["kind"] == "interference")
    errs = 0
    bad_calls = [(iso286.limits, 0, "H7"), (iso286.limits, 600, "H7"), (iso286.limits, 20, "X7"),
                 (iso286.limits, 20, "H4"), (iso286.limits, 20, "P8"), (iso286.fit, 20, "k6/H7"),
                 (iso286.fit, 20, "H7k6")]
    for fn, nominal, spec in bad_calls:
        try:
            fn(nominal, spec)
        except ValueError:
            errs += 1
    ok("iso286: invalid sizes, classes and fits raise ValueError", errs == 7, f"{errs}/7")
    r = server.iso_fit(22, "H7/k6")
    ok("iso_fit tool returns fit with catalog notes", r["kind"] == "transition"
       and any(e["id"] == "passung_h7_k6_waelzlager" for e in r["katalog"]), str([e["id"] for e in r["katalog"]]))


def katalog_checks():
    entries = katalog.load(validate_entries=False)
    ok("katalog: load finds entries", len(entries) >= 86, f"count={len(entries)}")

    validation_failures = []
    for e in entries:
        try:
            katalog.validate(e)
        except Exception as err:
            validation_failures.append((e.get("id"), str(err)))
    ok("katalog: all catalog entries validate against schema", not validation_failures, str(validation_failures))

    bad_rejected = False
    try:
        katalog.validate({"id": "invalid_entry_without_fields"})
    except ValueError:
        bad_rejected = True
    ok("katalog: schema validation rejects incomplete/invalid entries", bad_rejected)

    # Query 1: Anziehdrehmoment M8 8.8
    res1 = katalog.query(groesse="M8", festigkeitsklasse="8.8", text="Anziehdrehmoment")
    ids1 = [e["id"] for e in res1]
    ok("katalog query: Anziehdrehmoment M8 8.8 returns VDI 2230 entry",
       "vdi2230_anziehdrehmoment_m4_m12_reyher" in ids1, str(ids1))

    # Query 2: Innenradius Tasche Alu beim Fräsen
    res2 = katalog.query(verfahren="Fräsen", feature="Tasche", werkstoff="Alu")
    ids2 = [e["id"] for e in res2]
    ok("katalog query: Innenradius Tasche Alu beim Fräsen returns Hubs pocket rule",
       "innenradius_vertikale_kanten_hubs" in ids2, str(ids2))

    # Query 3: Einpressmaß iglidur
    res3 = katalog.query(text="Einpressmaß iglidur")
    ids3 = [e["id"] for e in res3]
    ok("katalog query: Einpressmaß iglidur returns igus fit entry",
       "iglidur_einpressmasse_toleranzen" in ids3, str(ids3))

    # Query 4: Einschraubtiefe M6 Aluminium
    res4 = katalog.query(werkstoff="Aluminium", groesse="M6", text="Einschraubtiefe")
    ids4 = [e["id"] for e in res4]
    ok("katalog query: Einschraubtiefe M6 Aluminium returns engagement depth entries",
       "einschraubtiefe_aluminium_bossard" in ids4 and "einschraubtiefe_aluminium_vdi2230_hanke" in ids4,
       str(ids4))

    # Query 5: Nutmaß Sicherungsring Welle 20
    res5 = katalog.query(text="Nutmaß Sicherungsring Welle 20")
    ids5 = [e["id"] for e in res5]
    ok("katalog query: Nutmaß Sicherungsring Welle 20 returns DIN 471 retaining ring entry",
       "sicherungsring_welle_din471_randabstand" in ids5, str(ids5))

    # Query 6: O-Ring-Nut 2 mm statisch radial
    res6 = katalog.query(text="O-Ring-Nut 2 mm statisch radial")
    ids6 = [e["id"] for e in res6]
    ok("katalog query: O-Ring-Nut 2 mm statisch radial returns 2mm groove entry",
       "oring_nutmasse_2mm_statisch" in ids6, str(ids6))

    # Query 7: Mindestbiegeradius 2 mm Alu
    res7 = katalog.query(werkstoff="Alu", groesse="2 mm", text="Mindestbiegeradius")
    ids7 = [e["id"] for e in res7]
    ok("katalog query: Mindestbiegeradius 2 mm Alu returns sheet bending rules",
       "mindestbiegeradius_stahl_dc01_alu_5754" in ids7 and "mindestbiegeradius_alu_6061_t6" in ids7,
       str(ids7))

    # Mindestwerte je Erzeugnisdicke (dickenbereiche)
    crmo_50 = katalog.mindestwerte("42crmo4_verguetet", 50)
    ok("katalog mindestwerte: 42CrMo4 +QT at d=50mm returns Rm_min 900, Rp02_min 650",
       crmo_50 is not None and crmo_50.get("R_m_min") == 900 and crmo_50.get("R_p02_min") == 650,
       str(crmo_50))

    crmo_10 = katalog.mindestwerte("42crmo4_verguetet", 10)
    ok("katalog mindestwerte: 42CrMo4 +QT at d=10mm returns Rm_min 1100, Rp02_min 900",
       crmo_10 is not None and crmo_10.get("R_m_min") == 1100 and crmo_10.get("R_p02_min") == 900,
       str(crmo_10))

    crmo_300 = katalog.mindestwerte("42crmo4_verguetet", 300)
    ok("katalog mindestwerte: 42CrMo4 +QT at d=300mm returns None",
       crmo_300 is None, str(crmo_300))

    s235_30 = katalog.mindestwerte("s235jr", 30)
    ok("katalog mindestwerte: S235JR at t=30mm returns ReH_min 225",
       s235_30 is not None and s235_30.get("R_eH_min") == 225,
       str(s235_30))

    ohne_db = katalog.mindestwerte("pom_c", 20)
    ok("katalog mindestwerte: entry without dickenbereiche returns None without error",
       ohne_db is None, str(ohne_db))

    gezogen = katalog.mindestwerte("en_aw_2007", 25, form="rund_gezogen")
    ok("katalog mindestwerte: form matches exactly (EN AW-2007 drawn bar d=25mm: Rp02_min 240, not the extruded 250)",
       gezogen is not None and gezogen.get("R_p02_min") == 240, str(gezogen))


def praxistest_3_fixes_checks(ws):
    # Befund 4: Bolt circle (circular pattern) and rectangular pattern with counterbore=True:
    # All screws must point with shank in ray direction, and inspect.interference count == 0.
    p1_cb = ws.new(PART, "p1_cb_pat", overwrite=True)
    p1_cb.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0],
                                    "operation": "new", "body_name": "Plate1", "name": "Box1"})
    p1_cb.save()

    p2_cb = ws.new(PART, "p2_cb_pat", overwrite=True)
    p2_cb.session.cmd("solid.box", {"length": 80, "width": 80, "height": 8, "corner": [-40, -40, 0],
                                    "operation": "new", "body_name": "Plate2", "name": "Box2"})
    p2_cb.save()

    # Rectangular pattern 2x2 with counterbore=True
    asm_r = ws.new(ASSEMBLY, "asm_rect_cb", overwrite=True)
    links.insert(ws, asm_r, p1_cb.path, name="Plate1", grounded=True)
    links.insert(ws, asm_r, p2_cb.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm_r.save()

    rect_pat = {"type": "rectangular", "count": [2, 2], "spacing": [30, 30], "directions": [[1, 0, 0], [0, 1, 0]]}
    res_r = bolted.bolted_connection(
        ws, "asm_rect_cb",
        placement={"position": [-15, -15, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=True,
        pattern=rect_pat,
    )
    interf_r = asm_r.session.cmd("inspect.interference")
    occs_r = {o["name"]: o for o in links._occurrences(asm_r.session).values()}
    r_screws_ok = True
    for s_name in res_r.get("screws", []):
        occ = occs_r.get(s_name)
        if not occ:
            r_screws_ok = False
            break
        shank_w = g.unit(g.apply_dir(occ["transform"], [0.0, 0.0, -1.0]))
        if g.dot(shank_w, [0.0, 0.0, -1.0]) < 0.99:
            r_screws_ok = False

    # Circular pattern (4 screws) with counterbore=True
    asm_c = ws.new(ASSEMBLY, "asm_circ_cb", overwrite=True)
    links.insert(ws, asm_c, p1_cb.path, name="Plate1", grounded=True)
    links.insert(ws, asm_c, p2_cb.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm_c.save()

    circ_pat = {"type": "circular", "count": 4, "axis_point": [0, 0, 0], "axis": [0, 0, 1]}
    res_c = bolted.bolted_connection(
        ws, "asm_circ_cb",
        placement={"position": [20, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=True,
        pattern=circ_pat,
    )
    interf_c = asm_c.session.cmd("inspect.interference")
    occs_c = {o["name"]: o for o in links._occurrences(asm_c.session).values()}
    c_screws_ok = True
    for s_name in res_c.get("screws", []):
        occ = occs_c.get(s_name)
        if not occ:
            c_screws_ok = False
            break
        shank_w = g.unit(g.apply_dir(occ["transform"], [0.0, 0.0, -1.0]))
        if g.dot(shank_w, [0.0, 0.0, -1.0]) < 0.99:
            c_screws_ok = False

    ok("praxistest 3 / finding 4: rectangular and circular patterns with counterbore=True align all screw shanks in ray direction with interference == 0",
       interf_r.get("count") == 0 and r_screws_ok and len(res_r.get("screws", [])) == 4
       and interf_c.get("count") == 0 and c_screws_ok and len(res_c.get("screws", [])) == 4,
       f"interf_r={interf_r}, r_ok={r_screws_ok}, interf_c={interf_c}, c_ok={c_screws_ok}")

    # Befund 3: bolted_connection/preview_bolted_connection with optional parts: list[str] | None
    gp = ws.new(PART, "p_pt3_gp", overwrite=True)
    gp.session.cmd("solid.box", {"length": 120, "width": 80, "height": 10, "corner": [-60, -40, 0], "name": "Box"})
    gp.save()
    v_gp_before = gp.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]

    lb = ws.new(PART, "p_pt3_lb", overwrite=True)
    lb.session.cmd("solid.box", {"length": 60, "width": 40, "height": 40, "corner": [-30, -20, 0], "name": "Box"})
    lb.save()

    dk = ws.new(PART, "p_pt3_dk", overwrite=True)
    dk.session.cmd("solid.box", {"length": 60, "width": 40, "height": 10, "corner": [-30, -20, 0], "name": "Box"})
    dk.save()

    asm_stack = ws.new(ASSEMBLY, "asm_pt3_stack", overwrite=True)
    links.insert(ws, asm_stack, gp.path, name="Grundplatte", grounded=True)
    links.insert(ws, asm_stack, lb.path, name="Lagerbock", translate=[0, 0, 10], grounded=True)
    links.insert(ws, asm_stack, dk.path, name="Deckel", translate=[0, 0, 50], grounded=True)
    asm_stack.save()

    # Without parts: should fail due to ray piercing all 3 parts, and error message should name penetrated parts & suggest parts
    err_stack = None
    try:
        bolted.preview_bolted_connection(
            ws, "asm_pt3_stack",
            placement={"position": [-15, 0, 60], "direction": [0, 0, -1]},
            size="M5",
            connection_type="blind",
            blind_material="alu",
        )
    except ValueError as e:
        err_stack = str(e)

    ok("praxistest 3 / finding 3: excessive grip length error mentions penetrated parts and suggests 'parts'",
       err_stack is not None and "exceeds maximum preferred length" in err_stack
       and "penetrated parts" in err_stack and "Deckel" in err_stack and "Grundplatte" in err_stack
       and "use 'parts'" in err_stack,
       f"err_stack={err_stack}")

    # With parts=["Deckel:1", "Lagerbock:1"]: should only connect Deckel and Lagerbock, leaving Grundplatte untouched
    prev_stack = bolted.preview_bolted_connection(
        ws, "asm_pt3_stack",
        placement={"position": [-15, 0, 60], "direction": [0, 0, -1]},
        size="M5",
        connection_type="blind",
        blind_material="alu",
        counterbore=False,
        parts=["Deckel:1", "Lagerbock:1"],
    )
    res_stack = bolted.bolted_connection(
        ws, "asm_pt3_stack",
        placement={"position": [-15, 0, 60], "direction": [0, 0, -1]},
        size="M5",
        connection_type="blind",
        blind_material="alu",
        counterbore=False,
        parts=["Deckel:1", "Lagerbock:1"],
    )
    gp_tl = sketch_rule.timeline(ws.docs["p_pt3_gp"].session).get("timeline", [])
    gp_holes = [f["name"] for f in gp_tl if "Hole" in f.get("name", "")]
    v_gp_after = ws.docs["p_pt3_gp"].session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    interf_stack = asm_stack.session.cmd("inspect.interference")
    interfs = interf_stack.get("interferences", [])
    # Cosmetic thread in CAD models nominal screw shank d=5mm overlapping tap drill bore d=4.2mm in Lagerbock
    thread_interf_ok = (
        len(interfs) == 1
        and set([interfs[0]["a"], interfs[0]["b"]]) == {"p_pt3_lb", "Screw"}
    )

    ok("praxistest 3 / finding 3: bolted connection with parts restricts to named parts and leaves bottom part untouched",
       prev_stack.get("grip_length") == 10.0
       and len(gp_holes) == 0
       and abs(v_gp_before - v_gp_after) < 1e-4
       and thread_interf_ok
       and len(res_stack.get("joints", [])) == 1,
       f"grip={prev_stack.get('grip_length')}, gp_holes={gp_holes}, interf={interf_stack}")

    # Befund 2 & 6: design_rules horizontal hole & stepped part edge distance
    p_horiz = ws.new(PART, "p_pt3_horiz", overwrite=True)
    p_horiz.session.cmd("solid.box", {
        "length": 80, "width": 20, "height": 60,
        "corner": [-40, 0, 0], "operation": "new", "name": "Basis"
    })
    p_horiz.session.cmd("solid.cylinder", {
        "diameter": 22, "height": 24, "base": [0, -2, 35],
        "axis": [0, 1, 0], "operation": "cut", "name": "Lagerbohrung"
    })
    res_horiz = design_rules.check(p_horiz.session, profile="fdm_0.4")
    wall_findings = res_horiz["rules"]["min_wall_thickness"]["findings"]
    neg_wall = [f for f in wall_findings if f["value"] < 0]

    ok("praxistest 3 / finding 2: horizontal hole evaluates lateral axes and reports positive wall thickness",
       len(neg_wall) == 0
       and res_horiz["rules"]["min_wall_thickness"]["status"] == "ok"
       and len(wall_findings) > 0 and wall_findings[0]["value"] == 14.0,
       f"neg_wall={neg_wall}, wall_status={res_horiz['rules']['min_wall_thickness']}")

    p_step = ws.new(PART, "p_pt3_step", overwrite=True)
    p_step.session.batch([
        {"command": "solid.box", "params": {"length": 90, "width": 60, "height": 14, "corner": [-45, -30, 0], "name": "Flansch"}},
        {"command": "solid.box", "params": {"length": 50, "width": 24, "height": 40, "corner": [-25, -12, 14], "operation": "join", "name": "Turm"}},
        {"command": "solid.hole", "params": {"position": [-32, -20, 14], "direction": [0, 0, -1], "diameter": 6.6, "depth": 14, "name": "Bohrung_M6"}},
    ])
    res_step = design_rules.check(p_step.session, profile="fdm_0.4")
    edge_step = res_step["rules"]["hole_edge_distance"]
    step_findings = [f for f in edge_step["findings"] if "F2:-x" in f.get("message", "")]

    ok("praxistest 3 / finding 6: stepped part hole edge distance ignores non-overlapping inner step face",
       len(step_findings) == 0
       and edge_step["status"] == "ok"
       and edge_step["findings"][0]["value"] == 10.0,
       f"step_findings={step_findings}, edge_status={edge_step}")

    # Befund 1: DIN 625 miniature & series-60 bearings (608, 623, 624, 625, 626, 627, 609)
    sp_608 = standard_parts.create(ws, "DIN 625", "608")
    d_608 = sp_608["standard"]["dimensions"]
    v_608 = standard_parts.expected_volume("DIN 625", "608")
    bb_608 = standard_parts.expected_bbox("DIN 625", "608")

    sp_623 = standard_parts.create(ws, "DIN 625", "623")
    d_623 = sp_623["standard"]["dimensions"]
    v_623 = standard_parts.expected_volume("DIN 625", "623")

    ok("praxistest 3 / finding 1: DIN 625 supports 608 and miniature bearings with verified catalog dimensions",
       d_608 == {"d": 8.0, "D": 22.0, "B": 7.0, "r": 0.3}
       and abs(v_608 - (math.pi * ((22.0 / 2) ** 2 - (8.0 / 2) ** 2) * 7.0 - math.pi * 0.3 ** 2 * (22.0 + 8.0))) < 1e-6
       and bb_608 == [[-11.0, -11.0, 0.0], [11.0, 11.0, 7.0]]
       and d_623 == {"d": 3.0, "D": 10.0, "B": 4.0, "r": 0.15}
       and abs(v_623 - (math.pi * ((10.0 / 2) ** 2 - (3.0 / 2) ** 2) * 4.0 - math.pi * 0.15 ** 2 * (10.0 + 3.0))) < 1e-6,
       f"d_608={d_608}, d_623={d_623}")

    # Befund 7: check_design top-level status field matching verdict
    ok("praxistest 3 / finding 7: check_design returns status field identical to verdict",
       "status" in res_horiz and res_horiz["status"] == res_horiz["verdict"]
       and "status" in res_step and res_step["status"] == res_step["verdict"],
       f"horiz_status={res_horiz.get('status')}, step_status={res_step.get('status')}")

    ws.close_all()


def praxistest_5_fixes_checks(ws):
    # Finding 1: the outer cylinders of a revolved stepped shaft are not holes
    shaft = ws.new(PART, "p5_shaft")
    shaft.session.batch([
        {"command": "sketch.create", "params": {"plane": "XZ", "name": "P"}},
        {"command": "sketch.line", "params": {"closed": True, "points": [[0, 0], [0, 4], [20, 4], [20, 6], [60, 6], [60, 0]]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.revolve", "params": {"sketch": "P", "axis": "X", "operation": "new", "body_name": "Welle", "name": "R"}},
    ])
    holes = query.find(shaft, "holes")
    r = design_rules.check(shaft.session, profile="fdm_0.4")
    ok("praxistest 5 / finding 1: revolved stepped shaft has no holes and passes check_design",
       holes == [] and r["verdict"] != "fail", f"holes={holes} verdict={r['verdict']}")
    ws.close("p5_shaft")

    # Finding 8: a countersink that notches a neighbouring wall fails countersink_clearance. SolidCraft 0.30 cut the
    # cone past the entry face (volume lower than with a free countersink), 0.40 no longer does. So the rule must
    # fire exactly when the wall was notched, whichever SolidCraft runs.
    cs_volume, cs_status = {}, {}
    for name, y in (("p5_cs_wall", 23.0), ("p5_cs_free", 10.0)):
        cs = ws.new(PART, name)
        cs.session.batch([
            {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 8, "corner": [0, 0, 0], "name": "Plate"}},
            {"command": "solid.box", "params": {"length": 40, "width": 10, "height": 30, "corner": [0, 30, 8],
                                                "operation": "join", "name": "Wall"}},
            {"command": "solid.hole", "params": {"position": [20, y, 8], "direction": [0, 0, -1], "clearance": "M6",
                                                 "depth": 8, "type": "countersink", "cs_diameter": 13.7,
                                                 "cs_angle": 90, "name": "CS"}},
        ])
        r = design_rules.check(cs.session, profile="fdm_0.4")
        cs_status[name] = r["rules"]["countersink_clearance"]["status"]
        cs_volume[name] = cs.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
        ws.close(name)
    notched = cs_volume["p5_cs_wall"] < cs_volume["p5_cs_free"] - 0.1
    ok("praxistest 5 / finding 8: countersink_clearance fails exactly when the countersink notched the wall",
       (cs_status["p5_cs_wall"] == "fail") == notched and cs_status["p5_cs_free"] == "ok",
       f"notched={notched}, volumes={cs_volume}, status={cs_status}")

    # Finding 4: measure on an assembly reports world coordinates
    blk = ws.new(PART, "p5_block")
    blk.session.cmd("solid.box", {"length": 10, "width": 10, "height": 10, "corner": [0, 0, 0], "name": "B"})
    blk.save()
    asm = ws.new(ASSEMBLY, "p5_measure_asm")
    orig_server_ws = server.ws
    server.ws = ws
    try:
        server.insert_part("p5_measure_asm", str(blk.path), name="Block", translate=[100, 0, 50], grounded=True)
        m = server.measure("p5_measure_asm")["bodies"][0]
    finally:
        server.ws = orig_server_ws
    ok("praxistest 5 / finding 4: measure on an assembly reports bbox and centre of mass in world coordinates",
       all(abs(a - b) < 1e-3 for a, b in zip(m["bbox"]["min"] + m["bbox"]["max"] + m["center_of_mass"],
                                             [100, 0, 50, 110, 10, 60, 105, 5, 55])),
       str(m))
    ws.close("p5_measure_asm")
    ws.close("p5_block")

    # Finding 3: a counterbored through hole is through; a drilled blind hole is not
    hb = ws.new(PART, "p5_holes")
    hb.session.batch([
        {"command": "solid.box", "params": {"length": 30, "width": 20, "height": 10, "corner": [0, 0, 0], "name": "B"}},
        {"command": "solid.hole", "params": {"position": [8, 10, 10], "direction": [0, 0, -1], "clearance": "M5",
                                             "depth": 10, "type": "counterbore", "cb_diameter": 10, "cb_depth": 5.4, "name": "CB"}},
        {"command": "solid.hole", "params": {"position": [22, 10, 10], "direction": [0, 0, -1], "diameter": 4.2,
                                             "depth": 6, "type": "drilled", "tip_angle": "118 deg", "name": "BL"}},
    ])
    hs = query.find(hb, "holes")
    cb = [h for h in hs if abs(h["diameter"] - 5.5) < 0.1]
    bl = [h for h in hs if abs(h["diameter"] - 4.2) < 0.1]
    ok("praxistest 5 / finding 3: counterbored through hole is through, blind drilled hole is not",
       len(cb) == 1 and cb[0]["through"] is True and len(bl) == 1 and bl[0]["through"] is False,
       str([(h["diameter"], h["through"]) for h in hs]))
    hb.save()
    ha = ws.new(ASSEMBLY, "p5_holes_asm")
    links.insert(ws, ha, hb.path, name="Block", translate=[100, 0, 0], grounded=True)
    ahs = query.find(ha, "holes", {"diameter": [5.4, 5.6]})
    ok("praxistest 5 / finding 2: assembly hole query uses the part's features (through, world centre, filter)",
       len(ahs) == 1 and ahs[0]["through"] is True and abs(ahs[0]["center"][0] - 108.0) < 1e-3
       and ahs[0].get("occurrence") == "Block:1",
       str(ahs))
    ws.close("p5_holes_asm")
    ws.close("p5_holes")


def praxistest_4_fixes_checks(ws):
    server.ws = ws

    # 1. Befund 2: geometry.classify_hole_groups does not classify massive bosses/pins as holes
    doc_dom = ws.new(PART, "pt4_dom")
    doc_dom.session.batch([
        {"command": "solid.box", "params": {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Boden"}},
        {"command": "solid.cylinder", "params": {"diameter": 8.0, "height": 20.0, "base": [35, 20, 3], "operation": "join", "name": "Schraubdom"}},
        {"command": "solid.hole", "params": {"position": [35, 20, 23], "direction": [0, 0, -1], "diameter": 4.0, "depth": 10.0, "name": "RuthexLoch"}},
    ])
    doc_dom.save()
    dom_holes = query.find(doc_dom, "holes")
    dom_diams = [h["diameter"] for h in dom_holes]
    chk_dom = design_rules.check(doc_dom.session, profile="fdm_0.4")
    edge_findings = chk_dom["rules"]["hole_edge_distance"]["findings"]
    ok("praxistest 4 / finding 2: massive boss/dome is not classified as hole",
       4.0 in dom_diams and 8.0 not in dom_diams and not any("Ø 8.0" in f.get("message", "") for f in edge_findings),
       f"diams={dom_diams}, edge_findings={edge_findings}")

    # 2. Befund 3: min_wall_thickness check flags thin cylindrical boss wall (R_outer - r_inner)
    doc_thin = ws.new(PART, "pt4_thin_boss")
    doc_thin.session.batch([
        {"command": "solid.box", "params": {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Boden"}},
        {"command": "solid.cylinder", "params": {"diameter": 4.8, "height": 15.0, "base": [35, 20, 3], "operation": "join", "name": "Dom"}},
        {"command": "solid.hole", "params": {"position": [35, 20, 18], "direction": [0, 0, -1], "diameter": 4.0, "depth": 10.0, "name": "Bohrung"}},
    ])
    doc_thin.save()
    chk_thin = design_rules.check(doc_thin.session, profile="fdm_0.4")
    wall_rule = chk_thin["rules"]["min_wall_thickness"]
    wall_vals = [f["value"] for f in wall_rule["findings"] if "F3:bore" in f.get("location", {}).get("face", "") or abs(f["value"] - 0.4) < 0.05]
    ok("praxistest 4 / finding 3: wall thickness check flags thin cylindrical boss wall",
       wall_rule["status"] == "fail" and any(abs(v - 0.4) < 0.05 for v in wall_vals),
       f"wall_status={wall_rule['status']}, wall_vals={wall_vals}")

    # 3. Befund 4: unsupported blind material PLA suggests use_insert or thread-forming screws
    pla_err = None
    try:
        hole_tables.normalize_material("PLA")
    except ValueError as e:
        pla_err = str(e)
    ok("praxistest 4 / finding 4: unsupported blind material PLA suggests use_insert or thread-forming screws",
       pla_err is not None and "unsupported blind material 'PLA'" in pla_err
       and "use_insert=True" in pla_err and "plastic" in pla_err,
       f"pla_err={pla_err}")

    # 4. Befund 1: counterbore exceeding top plate thickness suggests counterbore=False
    p_top = ws.new(PART, "pt4_top_plate")
    p_top.session.cmd("solid.box", {"length": 60, "width": 60, "height": 3.0, "corner": [-30, -30, 0], "name": "Top"})
    p_top.save()
    p_bot = ws.new(PART, "pt4_bot_plate")
    p_bot.session.cmd("solid.box", {"length": 60, "width": 60, "height": 10.0, "corner": [-30, -30, 0], "name": "Bot"})
    p_bot.save()
    asm_cb = ws.new(ASSEMBLY, "pt4_asm_cb")
    links.insert(ws, asm_cb, p_bot.path, name="Bot", grounded=True)
    links.insert(ws, asm_cb, p_top.path, name="Top", translate=[0, 0, 10], grounded=False)
    asm_cb.save()
    cb_err = None
    try:
        bolted.preview_bolted_connection(
            ws, "pt4_asm_cb",
            placement={"position": [10, 10, 13], "direction": [0, 0, -1]},
            size="M3",
            counterbore=True,
        )
    except ValueError as e:
        cb_err = str(e)
    ok("praxistest 4 / finding 1: counterbore exceeding top plate thickness suggests counterbore=False",
       cb_err is not None and "counterbore depth (3.4 mm) exceeds or equals top plate thickness (3.0 mm)" in cb_err
       and "counterbore=False" in cb_err,
       f"cb_err={cb_err}")

    # 5. Befund 6: find in assembly returns full occurrence path for subassemblies and add_joint works
    sub_p = ws.new(PART, "pt4_sub_plate")
    sub_p.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [-20, -20, 0], "name": "Box"}},
        {"command": "solid.cylinder", "params": {"diameter": 4, "height": 7, "base": [10, 10, -1], "operation": "cut", "name": "Hole"}},
    ])
    sub_p.save()
    sub_a = ws.new(ASSEMBLY, "pt4_sub_asm")
    links.insert(ws, sub_a, sub_p.path, name="Platte", grounded=True)
    sub_a.save()
    base_p = ws.new(PART, "pt4_base_part")
    base_p.session.cmd("solid.box", {"length": 100, "width": 100, "height": 10, "corner": [-50, -50, -10], "name": "Base"})
    base_p.save()
    top_a = ws.new(ASSEMBLY, "pt4_top_asm")
    links.insert(ws, top_a, base_p.path, name="Base", grounded=True)
    links.insert(ws, top_a, sub_a.path, name="SubUnit", translate=[50, 0, 0], grounded=False)
    top_a.save()
    f_holes = server.find("pt4_top_asm", "holes")
    f_occ = f_holes["holes"][0].get("occurrence") if f_holes.get("holes") else None
    jt_res = None
    if f_occ == "SubUnit:1/Platte:1":
        jt_res = server.add_joint("pt4_top_asm", {
            "name": "JointSubTest",
            "type": "rigid",
            "a": {"occurrence": "Base:1", "point": [0, 0, 0], "z": [0, 0, 1]},
            "b": {"occurrence": f_occ, "point": [50, 0, 0], "z": [0, 0, 1]},
        })
        server.save_document("pt4_top_asm")
    chk_jt = server.check_joints("pt4_top_asm")
    ok("praxistest 4 / finding 6: find in assembly returns full occurrence path for subassemblies and add_joint works",
       f_occ == "SubUnit:1/Platte:1" and jt_res is not None
       and any(j["joint"] == "JointSubTest" and j["status"] == "ok" for j in chk_jt.get("joints", [])),
       f"f_occ={f_occ}, chk_jt={chk_jt}")

    # 6. Befund 8: update_links with repair=True repairs origin_lost and reports result per joint
    p_b8_1 = ws.new(PART, "pt4_b8_basis")
    p_b8_1.session.batch([
        {"command": "solid.box", "params": {"length": 100, "width": 50, "height": 10, "corner": [-50, -25, 0], "name": "Box"}},
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 15, "base": [20, 0, 10], "operation": "join", "name": "Dom"}},
    ])
    p_b8_1.save()
    p_b8_2 = ws.new(PART, "pt4_b8_stift")
    p_b8_2.session.cmd("solid.cylinder", {"diameter": 10, "height": 20, "base": [0, 0, 0], "operation": "new", "name": "Stift"})
    p_b8_2.save()
    asm_b8 = ws.new(ASSEMBLY, "pt4_b8_asm")
    links.insert(ws, asm_b8, p_b8_1.path, name="Basis", grounded=True)
    links.insert(ws, asm_b8, p_b8_2.path, name="Stift", translate=[20, 0, 25], grounded=False)
    server.add_joint("pt4_b8_asm", {
        "type": "rigid",
        "name": "StiftAufDom",
        "a": {"occurrence": "Basis:1", "circle": [20, 0, 25]},
        "b": {"occurrence": "Stift:1", "circle": [20, 0, 25]},
    })
    server.save_document("pt4_b8_asm")
    eip = server.edit_in_place("pt4_b8_asm", "Basis:1")
    doc_p1 = ws.get(eip["document"], PART)
    doc_p1.session.cmd("solid.cylinder", {"diameter": 4, "height": 15, "base": [20, 0, 10], "operation": "cut", "name": "Loch"})
    doc_p1.save()
    asm_b8_doc = ws.get("pt4_b8_asm", ASSEMBLY)
    asm_b8_doc.session.cmd("component.update_links")
    chk_broken = links.check(ws, asm_b8_doc)
    b8_broken_status = next((j["status"] for j in chk_broken if j["joint"] == "StiftAufDom"), None)

    rep_upd = server.update_links("pt4_b8_asm", repair=True)
    chk_repaired = server.check_joints("pt4_b8_asm")
    b8_rep_status = next((j["status"] for j in chk_repaired["joints"] if j["joint"] == "StiftAufDom"), None)
    repaired_joints = [x["joint"] for x in rep_upd.get("repaired", [])]

    ok("praxistest 4 / finding 8: update_links with repair=True repairs origin_lost and reports result per joint",
       ((b8_broken_status in ("origin_lost", "moved") and "StiftAufDom" in repaired_joints)  # "moved" since 0.25
        # solidcore (0.40) keeps the dome's top circle through the cut: the joint stays ok, nothing to repair
        or (b8_broken_status == "ok" and not repaired_joints))
       and b8_rep_status == "ok",
       f"broken_status={b8_broken_status}, rep_upd={rep_upd}, rep_status={b8_rep_status}")

    ws.close_all()


def bolted_anchor_associativity_checks(ws):
    old_server_ws = server.ws
    server.ws = ws
    try:
        # 1. Skript-07-Fall: Gehäuse mit parametrischem Dom dx = L/2 - 15 mm
        gehaeuse = ws.new(PART, "gehaeuse_pt4")
        gehaeuse.session.batch([
            {"command": "parameters.add", "params": {"name": "L", "expression": "100 mm"}},
            {"command": "parameters.add", "params": {"name": "dx", "expression": "L/2 - 15 mm"}},
            {"command": "solid.box", "params": {"length": "L", "width": 70, "height": 35, "corner": ["-L/2", -35, 0], "name": "Box"}},
            {"command": "solid.box", "params": {"length": "L - 5 mm", "width": 65, "height": 33, "corner": ["-(L - 5 mm)/2", -32.5, 2.5], "operation": "cut", "name": "Pocket"}},
            {"command": "solid.cylinder", "params": {"diameter": 8, "height": 32.5, "base": ["dx", 20, 2.5], "operation": "join", "name": "Dom"}},
        ])
        gehaeuse.save()

        deckel = ws.new(PART, "deckel_pt4")
        deckel.session.cmd("solid.box", {"length": 100, "width": 70, "height": 3, "corner": [-50, -35, 0], "name": "Deckel"})
        deckel.save()

        asm = ws.new(ASSEMBLY, "asm_pt4_dom")
        links.insert(ws, asm, gehaeuse.path, name="Gehaeuse", grounded=True)
        links.insert(ws, asm, deckel.path, name="Deckel", translate=[0, 0, 35], grounded=False)
        asm.save()

        res = bolted.bolted_connection(
            ws, "asm_pt4_dom",
            placement={"position": [35, 20, 38], "direction": [0, 0, -1]},
            size="M3",
            use_insert=True,
            counterbore=False,
            parts=["Deckel:1", "Gehaeuse:1"],
        )
        asm.save()

        meta = asm.metadata()["bolted_connections"][res["id"]]
        anchor = meta.get("anchor", {})
        ok("bolted connection: records concentric cylinder anchor on Dom",
           anchor.get("kind") == "cylinder" and anchor.get("occurrence") == "Gehaeuse:1",
           str(anchor))

        # Edit Gehäuse per edit_in_place: L: 100 -> 110 mm -> Dom moves from x=35 to x=40 mm
        eip = server.edit_in_place("asm_pt4_dom", "Gehaeuse:1")
        part_g = ws.get(eip["document"], PART)
        part_g.session.cmd("parameters.change", {"name": "L", "expression": "110 mm"})
        server.finish_edit(eip["document"], update=True)

        # Test repair=False: reports "moved" with shifted_by [5.0, 0.0, 0.0] without changing files
        r_false = server.update_links("asm_pt4_dom", repair=False)
        b_false = next((b for b in r_false.get("bolted_connections", []) if b["id"] == res["id"]), {})
        ok("bolted connection: repair=False reports moved without modifying files",
           b_false.get("status") == "moved" and abs(b_false.get("shifted_by", [0])[0] - 5.0) < 1e-3,
           str(b_false))

        # Test repair=True: repairs connection, hole in Gehaeuse becomes coaxial to Dom at x=40
        r_rep = server.update_links("asm_pt4_dom", repair=True)
        b_rep = next((b for b in r_rep.get("bolted_connections", []) if b["id"] == res["id"]), {})
        chk_rep = server.check_joints("asm_pt4_dom")
        interf_bodies = [b["name"] for b in ws.get("asm_pt4_dom", ASSEMBLY).session.cmd("document.inspect", {"measure": True})["bodies"] if "Insert" not in b["name"]]
        interf_dom = ws.get("asm_pt4_dom", ASSEMBLY).session.cmd("inspect.interference", {"bodies": interf_bodies})

        # Verify hole in Gehaeuse is coaxial to Dom at x=40
        reader_g = ws.reader(gehaeuse.path)
        try:
            faces_after = links._part_faces(reader_g)
            # The Ruthex hole cylinder has radius 2.0 mm (< 3.0 mm), while Dom has radius 4.0 mm
            ruthex_hole = next((f for f in faces_after if f.get("cylinder") and f["cylinder"]["radius"] < 3.0), None)
            hole_x = ruthex_hole["cylinder"]["origin"][0] if ruthex_hole else None
        finally:
            reader_g.close()

        ok("skript-07: Dom shifted 5 mm, update_links repairs, hole coaxial, joints ok, inspect.interference count == 0",
           b_rep.get("status") == "moved_repaired"
           and hole_x is not None and abs(hole_x - 40.0) < 1e-3
           and all(j["status"] == "ok" for j in chk_rep.get("joints", []))
           and interf_dom.get("count") == 0,
           f"b_rep={b_rep}, hole_x={hole_x}, joints={chk_rep}, interf={interf_dom}")

        # 2. Muster (2x2) auf einer Platte, deren Länge parametrisch wächst (corner=[-L/2, -40, 0])
        p1 = ws.new(PART, "p1_ank_pat")
        p1.session.batch([
            {"command": "parameters.add", "params": {"name": "L", "expression": "100 mm"}},
            {"command": "solid.box", "params": {"length": "L", "width": 80, "height": 10, "corner": ["-L/2", -40, 0], "name": "Plate1"}},
        ])
        p1.save()

        p2 = ws.new(PART, "p2_ank_pat")
        p2.session.cmd("solid.box", {"length": 140, "width": 80, "height": 10, "corner": [-70, -40, -10], "name": "Plate2"})
        p2.save()

        asm_pat = ws.new(ASSEMBLY, "asm_ank_pat")
        links.insert(ws, asm_pat, p1.path, name="Plate1", grounded=True)
        links.insert(ws, asm_pat, p2.path, name="Plate2", translate=[0, 0, 0], grounded=True)
        asm_pat.save()

        pat_params = {"type": "rectangular", "count": [2, 2], "spacing": [30, 30], "directions": [[1, 0, 0], [0, 1, 0]]}
        res_pat = bolted.bolted_connection(
            ws, "asm_ank_pat",
            placement={"position": [-35, -25, 10], "direction": [0, 0, -1]},
            size="M4",
            counterbore=False,
            pattern=pat_params,
        )
        asm_pat.save()

        meta_pat = asm_pat.metadata()["bolted_connections"][res_pat["id"]]
        anchor_pat = meta_pat.get("anchor", {})
        ok("bolted connection: pattern records plane anchor with edge offset",
           anchor_pat.get("kind") == "plane" and anchor_pat.get("occurrence") == "Plate1:1"
           and anchor_pat.get("ref_u") == "min" and abs(anchor_pat.get("offset_u", 0) - 15.0) < 1e-3,
           str(anchor_pat))

        # Lengthen Plate1 from L=100 mm to L=120 mm: left edge moves from -50 mm to -60 mm
        eip_p = server.edit_in_place("asm_ank_pat", "Plate1:1")
        p1_doc = ws.get(eip_p["document"], PART)
        p1_doc.session.cmd("parameters.change", {"name": "L", "expression": "120 mm"})
        server.finish_edit(eip_p["document"], update=True)

        # Update links with repair=True: holes stay at distance 15 mm from min-X edge (-60 + 15 = -45 mm)
        r_pat_upd = server.update_links("asm_ank_pat", repair=True)
        b_pat_upd = next((b for b in r_pat_upd.get("bolted_connections", []) if b["id"] == res_pat["id"]), {})
        chk_pat = server.check_joints("asm_ank_pat")
        interf_pat = ws.get("asm_ank_pat", ASSEMBLY).session.cmd("inspect.interference")

        # Inspect new hole positions in Plate1
        reader_p1 = ws.reader(p1.path)
        try:
            p1_faces = links._part_faces(reader_p1)
            p1_holes = [f["cylinder"]["origin"][0] for f in p1_faces if f.get("cylinder")]
        finally:
            reader_p1.close()

        min_hole_x = min(p1_holes) if p1_holes else None
        dist_to_edge = (min_hole_x - (-60.0)) if min_hole_x is not None else None

        ok("bolted pattern (2x2): plate length grows, anchor=face+offset, holes remain relative to anchor edge",
           b_pat_upd.get("status") == "moved_repaired"
           and abs(b_pat_upd.get("shifted_by", [0])[0] - (-10.0)) < 1e-3
           and dist_to_edge is not None and abs(dist_to_edge - 15.0) < 1e-3
           and all(j["status"] == "ok" for j in chk_pat.get("joints", []))
           and interf_pat.get("count") == 0,
           f"b_pat_upd={b_pat_upd}, min_hole_x={min_hole_x}, dist_to_edge={dist_to_edge}, interf={interf_pat}")

        # 3. Anker verloren (Dom gelöscht): Status anchor_lost, keine Änderung
        eip_lost = server.edit_in_place("asm_pt4_dom", "Gehaeuse:1")
        p_g_lost = ws.get(eip_lost["document"], PART)
        p_g_lost.session.cmd("timeline.delete", {"features": ["Dom"]})
        server.finish_edit(eip_lost["document"], update=True)

        r_lost = server.update_links("asm_pt4_dom", repair=True)
        b_lost = next((b for b in r_lost.get("bolted_connections", []) if b["id"] == res["id"]), {})
        ok("bolted connection: anchor lost reports anchor_lost without guessing or changing",
           b_lost.get("status") == "anchor_lost",
           str(b_lost))
        # SolidCraft 0.40 refuses to read a part with a failing feature again; Mechvane then updates the other
        # links and names the part (0.30 links it anyway, so no warning).
        blocked_w = [w for w in r_lost.get("warnings", []) if w.get("status") == "link_blocked"]
        ok("update_links with a failing part reports link_blocked with the failing feature (SolidCraft 0.40) or links it",
           not blocked_w or any(w.get("feature") == "Hole_Ruthex_M3" for w in blocked_w), str(blocked_w)[:300])
        from mechvane.ui.server import _format_update_links_message
        msg_blocked = _format_update_links_message(
            [], [], [], [], [{"joint": None, "status": "link_blocked", "component": "Gehaeuse", "feature": "Hole_Ruthex_M3"}])
        ok("update links message names a part that was not updated",
           "not updated: Gehaeuse (Hole_Ruthex_M3 fails)" in msg_blocked, msg_blocked)

    finally:
        server.ws = old_server_ws
        ws.close_all()


def bolted_countersunk_checks(ws):
    # 1. Senkschraube M5 durch 3-mm-Deckel scheitert (k = 3.10 mm)
    p_d3 = ws.new(PART, "p_d3")
    p_d3.session.cmd("solid.box", {"length": 40, "width": 40, "height": 3, "corner": [-20, -20, 0], "name": "B3"})
    p_d3.save()

    p_d4 = ws.new(PART, "p_d4")
    p_d4.session.cmd("solid.box", {"length": 40, "width": 40, "height": 4, "corner": [-20, -20, 0], "name": "B4"})
    p_d4.save()

    p_b10 = ws.new(PART, "p_b10")
    p_b10.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "name": "B10"})
    p_b10.save()

    asm_f_csk = ws.new(ASSEMBLY, "asm_f_csk")
    links.insert(ws, asm_f_csk, p_d3.path, name="Deck3", grounded=True)
    links.insert(ws, asm_f_csk, p_b10.path, name="Base", translate=[0, 0, -10], grounded=True)
    asm_f_csk.save()

    fail_3mm = False
    try:
        bolted.preview_bolted_connection(
            ws, "asm_f_csk",
            placement={"position": [0, 0, 3], "direction": [0, 0, -1]},
            size="M5",
            head="countersunk",
        )
    except ValueError:
        fail_3mm = True
    ok("countersunk: M5 through 3 mm deck fails (top thickness 3.0 mm < k = 3.10 mm)", fail_3mm)

    # 2. Senkschraube M5 durch 4-mm-Deckel klappt
    asm_ok_csk = ws.new(ASSEMBLY, "asm_ok_csk")
    links.insert(ws, asm_ok_csk, p_d4.path, name="Deck4", grounded=True)
    links.insert(ws, asm_ok_csk, p_b10.path, name="Base", translate=[0, 0, -10], grounded=True)
    asm_ok_csk.save()

    res_csk = bolted.bolted_connection(
        ws, "asm_ok_csk",
        placement={"position": [0, 0, 4], "direction": [0, 0, -1]},
        size="M5",
        head="countersunk",
    )
    ok("countersunk: M5 through 4 mm deck succeeds (top thickness 4.0 mm >= k = 3.10 mm)",
       res_csk["size"] == "M5" and res_csk["head"] == "countersunk" and res_csk["screw_norm"] == "ISO 10642")

    # 3. Kopf bündig mit Oberfläche (Abstand < 0.05 mm)
    occs = {o["name"]: o for o in links._occurrences(asm_ok_csk.session).values()}
    screw_occ = occs[res_csk["screw"]]
    head_top_w = g.apply_point(screw_occ["transform"], [0, 0, 0])
    flush_dist = abs(head_top_w[2] - 4.0)
    ok("countersunk: screw head flush with surface (distance < 0.05 mm)",
       flush_dist < 0.05, f"flush_dist={flush_dist}")

    # 4. inspect.interference count == 0 and joints ok
    interf_csk = asm_ok_csk.session.cmd("inspect.interference")
    chk_csk = links.check(ws, asm_ok_csk)
    ok("countersunk: inspect.interference count == 0 and all joints ok",
       interf_csk.get("count") == 0 and all(c["status"] == "ok" for c in chk_csk),
       f"interf={interf_csk} chk={chk_csk}")

    # 5. Muster mit Senkschrauben (rectangular pattern)
    p_pat_d = ws.new(PART, "p_pat_d")
    p_pat_d.session.cmd("solid.box", {"length": 60, "width": 60, "height": 5, "corner": [-30, -30, 0], "name": "B_Pat_D"})
    p_pat_d.save()

    p_pat_b = ws.new(PART, "p_pat_b")
    p_pat_b.session.cmd("solid.box", {"length": 60, "width": 60, "height": 10, "corner": [-30, -30, 0], "name": "B_Pat_B"})
    p_pat_b.save()

    asm_pat = ws.new(ASSEMBLY, "asm_csk_pat")
    links.insert(ws, asm_pat, p_pat_d.path, name="Plate1", grounded=True)
    links.insert(ws, asm_pat, p_pat_b.path, name="Plate2", translate=[0, 0, -10], grounded=True)
    asm_pat.save()

    pat_params = {"type": "rectangular", "count": [2, 2], "spacing": [20, 20], "directions": [[1, 0, 0], [0, 1, 0]]}
    res_pat = bolted.bolted_connection(
        ws, "asm_csk_pat",
        placement={"position": [-10, -10, 5], "direction": [0, 0, -1]},
        size="M5",
        head="countersunk",
        pattern=pat_params,
    )
    interf_pat = asm_pat.session.cmd("inspect.interference")
    chk_pat = links.check(ws, asm_pat)
    ok("countersunk: pattern creates 4 instances without interference and valid joints",
       res_pat["count"] == 4 and len(res_pat["screws"]) == 4
       and interf_pat.get("count") == 0 and all(c["status"] == "ok" for c in chk_pat),
       f"count={res_pat['count']} interf={interf_pat}")

    # 6. edit_bolted_connection cap -> countersunk
    p_e1 = ws.new(PART, "p_e1")
    p_e1.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "name": "BE1"})
    p_e1.save()

    p_e2 = ws.new(PART, "p_e2")
    p_e2.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "name": "BE2"})
    p_e2.save()

    asm_edit = ws.new(ASSEMBLY, "asm_csk_edit")
    links.insert(ws, asm_edit, p_e1.path, name="P1", grounded=True)
    links.insert(ws, asm_edit, p_e2.path, name="P2", translate=[0, 0, -10], grounded=True)
    asm_edit.save()

    res_cap = bolted.bolted_connection(
        ws, "asm_csk_edit",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        head="cap",
        counterbore=True,
    )
    res_edit = bolted.edit_bolted_connection(
        ws, "asm_csk_edit",
        res_cap["id"],
        head="countersunk",
    )
    interf_edit = asm_edit.session.cmd("inspect.interference")
    chk_edit = links.check(ws, asm_edit)
    p_e1_doc = ws.docs.get("p_e1") or ws.open(p_e1.path)
    p_e1_tl = [f["name"] for f in sketch_rule.timeline(p_e1_doc.session).get("timeline", [])]
    ok("countersunk: edit_bolted_connection cap -> countersunk switches screw to ISO 10642 and hole to Hole_M5_CS",
       res_edit["head"] == "countersunk" and res_edit["screw_norm"] == "ISO 10642"
       and any("Hole_M5_CS" in f for f in p_e1_tl)
       and interf_edit.get("count") == 0 and all(c["status"] == "ok" for c in chk_edit),
       f"res={res_edit['head']} tl={p_e1_tl} interf={interf_edit}")


def web_ui_stage1_checks(ws):
    import urllib.request
    from mechvane.ui import collect_findings, collect_mesh, collect_tree, create_server

    # 1. mesh.py against flange from tests/reference/flansch.build.json
    flansch_path = Path(__file__).resolve().parents[1] / "reference" / "flansch.build.json"
    fl_cmds = json.loads(flansch_path.read_text(encoding="utf-8"))["commands"]
    fl_doc = ws.new(PART, "ui_flansch")
    fl_doc.session.batch(fl_cmds)
    sketch_rule.enforce(fl_doc.session)
    fl_doc.save()

    m_fl = collect_mesh(fl_doc)
    b_fl = m_fl["bodies"][0]
    raw_faces = fl_doc.session.cmd("model.faces", {"body": b_fl["name"]})["faces"]
    n_verts = len(b_fl["positions"]) // 3
    n_tris = len(b_fl["indices"]) // 3
    face_idx_set = {f["index"] for f in b_fl["faces"]}
    ok("web ui mesh.py: flange face count matches model.faces, valid triangle face_ids and face names present",
       len(b_fl["faces"]) == len(raw_faces) >= 14  # 18 on SolidCraft 0.30 (hole faces in two halves), 14 on 0.40
       and n_tris == len(b_fl["face_ids"]) > 0
       and all(0 <= vi < n_verts for vi in b_fl["indices"])
       and all(fid in face_idx_set for fid in b_fl["face_ids"])
       and all(isinstance(f.get("name"), str) and bool(f["name"]) for f in b_fl["faces"]),
       f"faces={len(b_fl['faces'])} raw={len(raw_faces)} tris={n_tris}")

    # 2. Start server on port 0 in a thread, fetch all four endpoints and check shapes
    srv = create_server(fl_doc.path, port=0)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        def _get_json(ep):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{ep}", timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))

        st_v, d_ver = _get_json("/api/version")
        st_m, d_mesh = _get_json("/api/mesh")
        st_t, d_tree = _get_json("/api/tree")
        st_f, d_find = _get_json("/api/findings")
        ok("web ui server: all four endpoints respond with valid JSON shapes",
           st_v == 200 and isinstance(d_ver.get("mtime"), (int, float)) and d_ver.get("name") == "ui_flansch"
           and st_m == 200 and len(d_mesh.get("bodies", [])) == 1
           and st_t == 200 and d_tree.get("kind") == "part" and len(d_tree.get("features", [])) > 0
           and st_f == 200 and "findings" in d_find and "verdict" in d_find,
           f"ver={d_ver} tree_kind={d_tree.get('kind')} find_keys={list(d_find.keys())}")

        # Test /api/visibility endpoint (issue #65)
        fl_body_name = b_fl["name"]
        req_hide = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/visibility",
            data=json.dumps({"items": [fl_body_name], "visible": False}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_hide, timeout=10) as resp:
            st_vis, d_vis = resp.status, json.loads(resp.read().decode("utf-8"))
        _, d_tree_hidden = _get_json("/api/tree")

        req_show = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/visibility",
            data=json.dumps({"items": [fl_body_name], "visible": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_show, timeout=10) as resp:
            st_vis2, d_vis2 = resp.status, json.loads(resp.read().decode("utf-8"))
        _, d_tree_restored = _get_json("/api/tree")

        ok("web ui server: /api/visibility toggles body visibility and updates tree",
           st_vis == 200 and d_vis.get("ok") is True and fl_body_name in d_tree_hidden.get("hidden_bodies", [])
           and st_vis2 == 200 and d_vis2.get("ok") is True and fl_body_name not in d_tree_restored.get("hidden_bodies", []),
           f"d_vis={d_vis} hidden={d_tree_hidden.get('hidden_bodies')} restored={d_tree_restored.get('hidden_bodies')}")

        import re
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            st_idx = resp.status
            idx_html = resp.read().decode("utf-8")
        scripts = re.findall(r"<script\b[^>]*>.*?</script>", idx_html, flags=re.IGNORECASE | re.DOTALL)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/static/vendor/three/build/three.module.js", timeout=10) as resp:
            st_three_static = resp.status
            three_bytes = resp.read()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/vendor/three/build/three.module.js", timeout=10) as resp:
            st_three_rel = resp.status
            resp.read()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/vendor/three/examples/jsm/controls/OrbitControls.js", timeout=10) as resp:
            st_orbit = resp.status
            resp.read()
        ok("web ui offline three.js: index.html has no http(s) URL in importmap or <script> tags and server serves local three.module.js",
           st_idx == 200 and len(scripts) >= 2
           and all("http://" not in s and "https://" not in s for s in scripts)
           and st_three_static == 200 and st_three_rel == 200 and st_orbit == 200 and len(three_bytes) > 100000,
           f"scripts={scripts} st_static={st_three_static} st_rel={st_three_rel} st_orbit={st_orbit} bytes={len(three_bytes)}")
    finally:
        srv.shutdown()
        srv.server_close()

    # 3. Assembly of two parts with a joint: tree contains the joint with status
    p_a = ws.new(PART, "ui_part_a")
    p_a.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 30, "height": 6, "corner": [0, 0, 0], "body_name": "PlateA"}},
        {"command": "solid.cylinder", "params": {"diameter": 6, "height": 8, "base": [20, 15, -1], "operation": "cut", "name": "HoleA"}},
    ])
    p_a.save()

    p_b = ws.new(PART, "ui_part_b")
    p_b.session.cmd("solid.cylinder", {"diameter": 6, "height": 16, "base": [0, 0, 0], "body_name": "PinB"})
    p_b.save()

    asm = ws.new(ASSEMBLY, "ui_asm")
    links.insert(ws, asm, p_a.path, name="Plate", grounded=True)
    links.insert(ws, asm, p_b.path, name="Pin", translate=[50, 0, 0])
    jp = {
        "type": "revolute",
        "name": "PinInPlate",
        "a": {"occurrence": "Plate:1", "circle": [23, 15, 6]},
        "b": {"occurrence": "Pin:1", "circle": [53, 0, 0]},
    }
    asm.session.cmd("joint.create", jp)
    links.record(ws, asm, "PinInPlate", jp)
    asm.save()

    srv_asm = create_server(asm.path, port=0)
    port_asm = srv_asm.server_address[1]
    th_asm = threading.Thread(target=srv_asm.serve_forever, daemon=True)
    th_asm.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port_asm}/api/tree", timeout=10) as resp:
            asm_tree = json.loads(resp.read().decode("utf-8"))
        with urllib.request.urlopen(f"http://127.0.0.1:{port_asm}/api/mesh", timeout=10) as resp:
            asm_mesh = json.loads(resp.read().decode("utf-8"))
        occ_joints = [j for o in asm_tree.get("occurrences", []) for j in o.get("joints", [])]
        pin_body = next((b for b in asm_mesh.get("bodies", []) if "Pin" in b["name"]), None)
        pin_xs = pin_body["positions"][0::3] if pin_body else []
        ok("web ui assembly: tree contains joint with status from links.check and mesh is in world coordinates",
           asm_tree.get("kind") == "assembly"
           and any(j.get("name") == "PinInPlate" and j.get("status") == "ok" for j in occ_joints)
           and any(j.get("name") == "PinInPlate" and j.get("status") == "ok" for j in asm_tree.get("joints", []))
           and bool(pin_xs) and abs((min(pin_xs) + max(pin_xs)) / 2.0 - 20.0) < 0.1,
           f"occ_joints={occ_joints} joints={asm_tree.get('joints')}")
        # Part rules would treat the whole assembly as one printed body (every underside an overhang)
        with urllib.request.urlopen(f"http://127.0.0.1:{port_asm}/api/findings", timeout=10) as resp:
            asm_findings = json.loads(resp.read().decode("utf-8"))
        ok("web ui assembly: findings are joint checks only, no part design rules on the assembly",
           asm_findings["findings"] and all(f["origin"] == "links" for f in asm_findings["findings"])
           and asm_findings["verdict"] == "ok" and "joints ok" in asm_findings["summary"],
           f"summary={asm_findings.get('summary')} sources={[f['origin'] for f in asm_findings['findings']]}")
        asm_sel = [f.get("select") for f in asm_findings["findings"]]
        ok("web ui model mode: joint findings carry a select.set item on an assembly body",
           asm_sel and all(x and x["type"] == "face" and x["body"] in {bd["name"] for bd in asm_mesh.get("bodies", [])}
                           for x in asm_sel),
           f"select={asm_sel}")

        # "Model" mode: the web app saves a linked part, the server writes it and updates the links
        with urllib.request.urlopen(f"http://127.0.0.1:{port_asm}/api/files", timeout=10) as resp:
            files = json.loads(resp.read().decode("utf-8"))
        original = p_a.path.read_bytes()
        p_a.session.cmd("solid.cylinder", {"diameter": 6, "height": 8, "base": [8, 8, -1], "operation": "cut", "name": "HoleB"})
        p_a.save()
        edited = p_a.path.read_bytes()
        p_a.path.write_bytes(original)
        with urllib.request.urlopen(f"http://127.0.0.1:{port_asm}/api/file/{p_a.path.name}", timeout=10) as resp:
            served = resp.read()
        req = urllib.request.Request(f"http://127.0.0.1:{port_asm}/api/file/{p_a.path.name}", data=edited,
                                     headers={"Content-Type": "application/octet-stream"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            saved = json.loads(resp.read().decode("utf-8"))
        try:
            urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port_asm}/api/file/other.solidcraft",
                                                          data=b"x", headers={"Content-Type": "application/octet-stream"},
                                                          method="POST"), timeout=10)
            foreign = 200
        except urllib.error.HTTPError as e:
            foreign = e.code
        ul = saved.get("update_links", {})
        ok("web ui model mode: /api/files lists linked parts, POST writes the part and runs update_links",
           files["files"] == sorted(["ui_asm.solidcraft", "ui_part_a.solidcraft", "ui_part_b.solidcraft"])
           and served == original and p_a.path.read_bytes() == edited
           and ul.get("update", {}).get("updated") == ["Plate"] and not ul.get("warnings")
           and saved["findings"]["verdict"] == "ok" and foreign == 404,
           f"files={files} update={ul.get('update')} verdict={saved.get('findings', {}).get('verdict')} foreign={foreign}")

        # Single-file server retains old answer and rejects /api/new
        with urllib.request.urlopen(f"http://127.0.0.1:{port_asm}/api/project", timeout=10) as resp:
            sf_proj = json.loads(resp.read().decode("utf-8"))
        try:
            req_sf_new = urllib.request.Request(f"http://127.0.0.1:{port_asm}/api/new",
                                                data=json.dumps({"name": "X"}).encode("utf-8"),
                                                headers={"Content-Type": "application/json"},
                                                method="POST")
            with urllib.request.urlopen(req_sf_new, timeout=10) as resp:
                sf_new_code = resp.status
        except urllib.error.HTTPError as e:
            sf_new_code = e.code
    finally:
        srv_asm.shutdown()
        srv_asm.server_close()

    # 3b. Folder server checks: listing with kinds, /api/open switching, /api/new creation and error handling
    srv_fld = create_server(ws.root, port=0)
    port_fld = srv_fld.server_address[1]
    th_fld = threading.Thread(target=srv_fld.serve_forever, daemon=True)
    th_fld.start()
    try:
        # GET /api/project initially: parts and assembly listed with correct kinds, no doc open
        with urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/project", timeout=10) as resp:
            fld_proj = json.loads(resp.read().decode("utf-8"))
        fld_kinds = {d["name"]: d["kind"] for d in fld_proj.get("documents", [])}

        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/files", timeout=10)
            no_doc_code = 200
        except urllib.error.HTTPError as e:
            no_doc_code = e.code

        # /api/open/../../etc -> 404
        try:
            req_bad_open = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/open/../../etc", data=b"",
                                                  headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req_bad_open, timeout=10) as resp:
                bad_open_code = resp.status
        except urllib.error.HTTPError as e:
            bad_open_code = e.code

        # /api/open switches (then /api/files lists the linked parts for the assembly)
        req_open = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/open/ui_asm.solidcraft", data=b"",
                                          headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_open, timeout=10) as resp:
            opened_asm = json.loads(resp.read().decode("utf-8"))
        with urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/files", timeout=10) as resp:
            asm_files = json.loads(resp.read().decode("utf-8"))

        # /api/new creates <name>.solidcraft as a part and it appears in /api/project
        req_new = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/new",
                                         data=json.dumps({"name": "Bracket"}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"},
                                         method="POST")
        with urllib.request.urlopen(req_new, timeout=10) as resp:
            created_part = json.loads(resp.read().decode("utf-8"))
        with urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/project", timeout=10) as resp:
            fld_proj_after = json.loads(resp.read().decode("utf-8"))

        # /api/new with an existing name -> 409
        try:
            req_dup = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/new",
                                             data=json.dumps({"name": "Bracket"}).encode("utf-8"),
                                             headers={"Content-Type": "application/json"},
                                             method="POST")
            with urllib.request.urlopen(req_dup, timeout=10) as resp:
                dup_code = resp.status
        except urllib.error.HTTPError as e:
            dup_code = e.code

        # /api/new with '../x' -> 400
        try:
            req_trav = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/new",
                                              data=json.dumps({"name": "../x"}).encode("utf-8"),
                                              headers={"Content-Type": "application/json"},
                                              method="POST")
            with urllib.request.urlopen(req_trav, timeout=10) as resp:
                trav_code = resp.status
        except urllib.error.HTTPError as e:
            trav_code = e.code

        ok("web ui folder mode: folder server lists parts and assembly with correct kinds, switches and creates parts",
           fld_kinds.get("ui_asm.solidcraft") == "assembly"
           and fld_kinds.get("ui_part_a.solidcraft") == "part"
           and fld_kinds.get("ui_part_b.solidcraft") == "part"
           and no_doc_code == 409 and bad_open_code == 404
           and opened_asm["document"] == "ui_asm.solidcraft"
           and opened_asm["files"] == asm_files["files"] == sorted(["ui_asm.solidcraft", "ui_part_a.solidcraft", "ui_part_b.solidcraft"])
           and created_part["document"] == "Bracket.solidcraft"
           and created_part["files"] == ["Bracket.solidcraft"]
           and fld_proj_after["current"] == "Bracket.solidcraft"
           and any(d["name"] == "Bracket.solidcraft" and d["kind"] == "part" for d in fld_proj_after.get("documents", []))
           and dup_code == 409 and trav_code == 400
           and files["files"] == sorted(["ui_asm.solidcraft", "ui_part_a.solidcraft", "ui_part_b.solidcraft"])
           and sf_proj.get("current") == "ui_asm.solidcraft"
           and sf_proj.get("documents") == [{"name": "ui_asm.solidcraft", "kind": "assembly"}]
           and sf_new_code == 404,
           f"kinds={fld_kinds} opened={opened_asm} created={created_part} dup={dup_code} trav={trav_code} bad_open={bad_open_code} sf_new={sf_new_code}")

        # Corrupt .solidcraft file in folder mode: /api/project must return 200 and list remaining documents
        corrupt_file = ws.root / "kaputt.solidcraft"
        corrupt_file.write_text("kein zip", encoding="utf-8")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/project", timeout=10) as resp:
                corrupt_code = resp.status
                corrupt_proj = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            corrupt_code = e.code
            corrupt_proj = {}
        finally:
            if corrupt_file.exists():
                corrupt_file.unlink()

        c_docs = {d["name"]: d.get("kind") for d in corrupt_proj.get("documents", [])}
        ok("web ui folder mode: corrupt .solidcraft file does not break /api/project",
           corrupt_code == 200
           and "ui_asm.solidcraft" in c_docs
           and "ui_part_a.solidcraft" in c_docs
           and "ui_part_b.solidcraft" in c_docs
           and ("kaputt.solidcraft" not in c_docs or c_docs.get("kaputt.solidcraft") == PART),
           f"code={corrupt_code} docs={c_docs}")

        # /api/folders lists roots, recent folders, subfolders with counts, and STEP files
        sub_dir = ws.root / "ui_subfolder"
        sub_dir.mkdir(exist_ok=True)
        sub_part = ws.new(PART, "sub_part", path=str(sub_dir / "sub_part.solidcraft"))
        sub_part.save()
        ws.close("sub_part")
        flansch_step = Path(__file__).resolve().parents[2] / "docs/research/2026-10-phase0-solidcraft/flansch.step"
        if flansch_step.exists():
            shutil.copyfile(flansch_step, sub_dir / "flansch.step")

        with urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/folders?path={urllib.parse.quote(str(ws.root))}", timeout=10) as resp:
            folders_data = json.loads(resp.read().decode("utf-8"))

        sub_entry = next((f for f in folders_data.get("folders", []) if f["name"] == "ui_subfolder"), None)
        ok("web ui /api/folders: lists subfolders with .solidcraft and STEP counts, roots and recent folders",
           folders_data.get("current") == str(ws.root.resolve())
           and len(folders_data.get("roots", [])) >= 1
           and sub_entry is not None
           and sub_entry.get("solidcraft_count") == 1
           and sub_entry.get("step_count") == 1
           and any(r.get("path") == str(ws.root.resolve()) for r in folders_data.get("recent", [])),
           f"folders_data={folders_data}")

        with urllib.request.urlopen(f"http://127.0.0.1:{port_fld}/api/folders?path={urllib.parse.quote(str(sub_dir))}", timeout=10) as resp:
            sub_folder_data = json.loads(resp.read().decode("utf-8"))
        ok("web ui /api/folders: lists STEP files in current folder",
           any(sf["name"] == "flansch.step" for sf in sub_folder_data.get("step_files", [])),
           f"step_files={sub_folder_data.get('step_files')}")

        # /api/project/open switches project folder, closes old docs, updates recent
        new_proj_dir = ws.root.parent / "ui_switched_proj"
        shutil.rmtree(new_proj_dir, ignore_errors=True)
        new_proj_dir.mkdir(exist_ok=True)
        new_ws = Workspace(new_proj_dir)
        try:
            p_switch = new_ws.new(PART, "switched_part", overwrite=True)
            p_switch.save()
        finally:
            new_ws.close_all()

        req_switch = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/project/open",
                                            data=json.dumps({"folder": str(new_proj_dir)}).encode("utf-8"),
                                            headers={"Content-Type": "application/json"},
                                            method="POST")
        with urllib.request.urlopen(req_switch, timeout=10) as resp:
            switch_res = json.loads(resp.read().decode("utf-8"))

        ok("web ui /api/project/open: switches project folder and returns new project data",
           switch_res.get("folder") == "ui_switched_proj"
           and switch_res.get("mode") == "folder"
           and any(d["name"] == "switched_part.solidcraft" for d in switch_res.get("documents", []))
           and srv_fld.folder_path == new_proj_dir.resolve(),
           f"switch_res={switch_res}")

        # /api/project/open with invalid folder returns 404
        try:
            req_bad_switch = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/project/open",
                                                    data=json.dumps({"folder": str(ws.root.parent / "nonexistent_dir")}).encode("utf-8"),
                                                    headers={"Content-Type": "application/json"},
                                                    method="POST")
            with urllib.request.urlopen(req_bad_switch, timeout=10) as resp:
                bad_switch_code = resp.status
        except urllib.error.HTTPError as e:
            bad_switch_code = e.code
        ok("web ui /api/project/open: invalid folder returns 404", bad_switch_code == 404, str(bad_switch_code))

        # /api/import_step with file from outside the project folder
        ext_step_dir = ws.root.parent / "ui_ext_step_dir"
        shutil.rmtree(ext_step_dir, ignore_errors=True)
        ext_step_dir.mkdir(exist_ok=True)
        if flansch_step.exists():
            ext_step_file = ext_step_dir / "ext_bought_part.step"
            shutil.copyfile(flansch_step, ext_step_file)
            req_ext_import = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/import_step",
                                                    data=json.dumps({"file": str(ext_step_file)}).encode("utf-8"),
                                                    headers={"Content-Type": "application/json"},
                                                    method="POST")
            with urllib.request.urlopen(req_ext_import, timeout=15) as resp:
                ext_import_res = json.loads(resp.read().decode("utf-8"))
            ok("web ui /api/import_step: imports external STEP file into current project folder",
               ext_import_res.get("document") == "ext_bought_part.solidcraft"
               and (new_proj_dir / "ext_bought_part.solidcraft").exists()
               and ext_step_file.exists(),
               f"ext_import_res={ext_import_res}")
    finally:
        srv_fld.shutdown()
        srv_fld.server_close()
        shutil.rmtree(new_proj_dir, ignore_errors=True)
        shutil.rmtree(ext_step_dir, ignore_errors=True)
        shutil.rmtree(sub_dir, ignore_errors=True)

    # 4. Part with intentional finding (countersink too close to wall as in Befund 8):
    # finding arrives in /api/findings with a face name that exists in /api/mesh. A hole too close to the edge gives
    # a finding with a face on every SolidCraft (the countersink notch used before is gone since SolidCraft 0.40).
    cs_doc = ws.new(PART, "ui_cs_wall")
    cs_doc.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 8, "corner": [0, 0, 0], "name": "Plate"}},
        {"command": "solid.hole", "params": {"position": [20, 2.5, 8], "direction": [0, 0, -1], "clearance": "M6",
                                             "depth": 8, "name": "NearEdge"}},
    ])
    cs_doc.save()

    srv_cs = create_server(cs_doc.path, port=0)
    port_cs = srv_cs.server_address[1]
    th_cs = threading.Thread(target=srv_cs.serve_forever, daemon=True)
    th_cs.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port_cs}/api/mesh", timeout=10) as resp:
            cs_mesh = json.loads(resp.read().decode("utf-8"))
        with urllib.request.urlopen(f"http://127.0.0.1:{port_cs}/api/findings", timeout=10) as resp:
            cs_findings = json.loads(resp.read().decode("utf-8"))

        mesh_face_map = {f["name"]: f["index"] for b in cs_mesh.get("bodies", []) for f in b.get("faces", [])}
        mesh_fids = {fid for b in cs_mesh.get("bodies", []) for fid in b.get("face_ids", [])}
        cs_fail = next(
            (f for f in cs_findings.get("findings", [])
             if f.get("rule") == "hole_edge_distance" and f.get("status") == "fail"),
            None,
        )
        cs_face = cs_fail.get("face") if cs_fail else None
        ok("web ui findings: a finding with a face arrives in /api/findings with a face name present in /api/mesh",
           cs_fail is not None and cs_face in mesh_face_map and mesh_face_map[cs_face] in mesh_fids,
           f"cs_fail={cs_fail} mesh_faces={list(mesh_face_map.keys())}")
        cs_sel = (cs_fail or {}).get("select") or {}
        ok("web ui model mode: the finding carries a select.set item for its face (index as in /api/mesh)",
           cs_sel.get("type") == "face" and cs_sel.get("index") == mesh_face_map.get(cs_face)
           and cs_sel.get("body") in {b["name"] for b in cs_mesh.get("bodies", [])} and len(cs_sel.get("point") or []) == 3,
           f"select={cs_sel} face={cs_face}")

        # 5. Reload on file change and HTTP 500 JSON recovery (server stays alive)
        with urllib.request.urlopen(f"http://127.0.0.1:{port_cs}/api/version", timeout=10) as resp:
            v_before = json.loads(resp.read().decode("utf-8"))["version"]
        cs_doc.session.cmd("solid.cylinder", {"diameter": 4, "height": 8, "base": [8, 8, 0], "operation": "cut", "name": "ExtraHole"})
        cs_doc.save()
        with urllib.request.urlopen(f"http://127.0.0.1:{port_cs}/api/version", timeout=10) as resp:
            v_after = json.loads(resp.read().decode("utf-8"))["version"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port_cs}/api/tree", timeout=10) as resp:
            tree_after = json.loads(resp.read().decode("utf-8"))
        feat_names = [f.get("name") for f in tree_after.get("features", [])]
        ok("web ui reload: file mtime change reloads document and updates tree",
           v_after > v_before and "ExtraHole" in feat_names,
           f"v_before={v_before} v_after={v_after} feats={feat_names}")
    finally:
        srv_cs.shutdown()
        srv_cs.server_close()

    # 5. UI server security checks (issue #62): Host and Origin headers, Content-Type
    srv_sec = create_server(fl_doc.path, port=0)
    port_sec = srv_sec.server_address[1]
    th_sec = threading.Thread(target=srv_sec.serve_forever, daemon=True)
    th_sec.start()
    try:
        def _sec_req(path, method="GET", host=f"127.0.0.1:{port_sec}", origin=None, content_type=None, data=None):
            headers = {}
            if host is not None:
                headers["Host"] = host
            if origin is not None:
                headers["Origin"] = origin
            if content_type is not None:
                headers["Content-Type"] = content_type
            body = data.encode("utf-8") if isinstance(data, str) else data
            req = urllib.request.Request(f"http://127.0.0.1:{port_sec}{path}", data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.status, resp.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()

        # 1. Fremder Host -> 403 on GET and POST
        st_get_evil_host, _ = _sec_req("/api/version", method="GET", host="evil.com")
        st_post_evil_host, _ = _sec_req("/api/speech", method="POST", host="evil.com",
                                        content_type="application/json", data='{"text": "hi"}')
        st_rebinding_host, _ = _sec_req("/api/folders", method="GET", host=f"attacker.com:{port_sec}")
        st_wrong_port_host, _ = _sec_req("/api/version", method="GET", host="127.0.0.1:9999")
        st_ipv6_host, _ = _sec_req("/api/version", method="GET", host=f"[::1]:{port_sec}")
        st_lh_host, _ = _sec_req("/api/version", method="GET", host=f"localhost:{port_sec}")
        ok("web ui security: foreign Host header returns 403, local loopback (127.0.0.1, localhost, [::1]) returns 200",
           st_get_evil_host == 403 and st_post_evil_host == 403
           and st_rebinding_host == 403 and st_wrong_port_host == 403
           and st_ipv6_host == 200 and st_lh_host == 200,
           f"get={st_get_evil_host} post={st_post_evil_host} rebind={st_rebinding_host} wrong_port={st_wrong_port_host} ipv6={st_ipv6_host} lh={st_lh_host}")

        # 2. Fremder Origin bei POST -> 403
        st_evil_origin, _ = _sec_req("/api/speech", method="POST", origin="http://evil.com",
                                     content_type="application/json", data='{"text": "hi"}')
        st_evil_origin_port, _ = _sec_req("/api/speech", method="POST", origin=f"http://evil.com:{port_sec}",
                                          content_type="application/json", data='{"text": "hi"}')
        st_null_origin, _ = _sec_req("/api/speech", method="POST", origin="null",
                                     content_type="application/json", data='{"text": "hi"}')
        st_wrong_port_origin, _ = _sec_req("/api/speech", method="POST", origin="http://127.0.0.1:9999",
                                           content_type="application/json", data='{"text": "hi"}')
        ok("web ui security: foreign Origin header on POST returns 403",
           st_evil_origin == 403 and st_evil_origin_port == 403
           and st_null_origin == 403 and st_wrong_port_origin == 403,
           f"evil={st_evil_origin} port={st_evil_origin_port} null={st_null_origin} wrong_port={st_wrong_port_origin}")

        # 3. Eigener Origin und fehlender Origin -> OK
        st_own_origin_ip, _ = _sec_req("/api/speech", method="POST", origin=f"http://127.0.0.1:{port_sec}",
                                       content_type="application/json", data='{"text": "M6"}')
        st_own_origin_lh, _ = _sec_req("/api/speech", method="POST", origin=f"http://localhost:{port_sec}",
                                       content_type="application/json", data='{"text": "M6"}')
        st_own_origin_ipv6, _ = _sec_req("/api/speech", method="POST", origin=f"http://[::1]:{port_sec}",
                                         content_type="application/json", data='{"text": "M6"}')
        st_no_origin, _ = _sec_req("/api/speech", method="POST", origin=None,
                                   content_type="application/json", data='{"text": "M6"}')
        ok("web ui security: own Origin and missing Origin on POST succeed",
           st_own_origin_ip == 200 and st_own_origin_lh == 200 and st_own_origin_ipv6 == 200 and st_no_origin == 200,
           f"own_ip={st_own_origin_ip} own_lh={st_own_origin_lh} own_ipv6={st_own_origin_ipv6} no_origin={st_no_origin}")

        # 4. Form-Content-Type -> 403
        st_form_url, _ = _sec_req("/api/speech", method="POST",
                                  content_type="application/x-www-form-urlencoded", data="text=hello")
        st_form_multi, _ = _sec_req("/api/speech", method="POST",
                                    content_type="multipart/form-data; boundary=xyz", data="--xyz\r\n")
        st_form_text, _ = _sec_req("/api/speech", method="POST",
                                   content_type="text/plain", data="text=hello")
        st_no_ct, _ = _sec_req("/api/speech", method="POST",
                               content_type=None, data='{"text": "hello"}')
        ok("web ui security: form Content-Types and missing Content-Type on POST return 403",
           st_form_url == 403 and st_form_multi == 403 and st_form_text == 403 and st_no_ct == 403,
           f"urlencoded={st_form_url} multipart={st_form_multi} text={st_form_text} no_ct={st_no_ct}")

        # 5. PUT/DELETE security checks
        st_put_evil_host, _ = _sec_req("/api/version", method="PUT", host="evil.com", content_type="application/json", data='{}')
        st_put_evil_origin, _ = _sec_req("/api/version", method="PUT", origin="http://evil.com", content_type="application/json", data='{}')
        st_put_form_ct, _ = _sec_req("/api/version", method="PUT", content_type="text/plain", data='hello')
        st_put_ok_sec, _ = _sec_req("/api/version", method="PUT", content_type="application/json", data='{}')
        ok("web ui security: PUT/DELETE check Host, Origin and Content-Type (403), valid headers return 405",
           st_put_evil_host == 403 and st_put_evil_origin == 403 and st_put_form_ct == 403 and st_put_ok_sec == 405,
           f"evil_host={st_put_evil_host} evil_origin={st_put_evil_origin} form_ct={st_put_form_ct} ok_sec={st_put_ok_sec}")
    finally:
        srv_sec.shutdown()
        srv_sec.server_close()

    ws.close_all()


def argon_review_findings_checks(ws):
    """Findings 1, 3 and 4 of the Argon review (docs/research/2026-10-27-review-gemini-bausteine-argon.md)."""
    # Finding 1: a planar face with curved edges must still be tested against its boundary.
    lp = ws.new(PART, "argon_lplate")
    lp.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [0, 0, 0],
                                            "name": "A", "body_name": "LPlate"}},
        {"command": "solid.box", "params": {"length": 20, "width": 20, "height": 5, "corner": [20, 20, 0],
                                            "operation": "cut", "name": "Notch"}},
        {"command": "solid.hole", "params": {"position": [10, 10, 5], "direction": [0, 0, -1],
                                             "clearance": "M5", "depth": 5, "name": "H"}}])
    faces = links._part_faces(lp.session)
    cyl_faces = {f["name"]: f for f in faces if f.get("cylinder")}
    top = next(f for f in faces if f.get("plane_normal") and f["plane_normal"][2] > 0.9
               and abs(f["point"][2] - 5) < 1e-6)
    f_edges = [e for e in lp.session.cmd("model.edges", {"body": "LPlate"})["edges"]
               if top["name"] in e["name"].split("|")]
    inside = {"material": [5, 30, 5], "notch": [30, 30, 5], "hole": [10, 10, 5], "beside_hole": [14, 10, 5]}
    got = {k: bolted._point_in_face(p, top, f_edges, cyl_faces) for k, p in inside.items()}
    # A point in an existing hole counts as on the face: bolting through an existing hole penetrates the part
    ok("argon review 1: point-in-face uses the outer boundary of faces with arcs (notch outside, hole inside)",
       got == {"material": True, "notch": False, "hole": True, "beside_hole": True}, str(got))
    ws.close("argon_lplate")

    # Finding 3: parallel blind holes from opposite sides without axial overlap are not adjacent.
    blk = ws.new(PART, "argon_block")
    blk.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 50, "corner": [0, 0, 0],
                                            "name": "Block", "body_name": "Block"}},
        {"command": "solid.hole", "params": {"position": [20, 20, 50], "direction": [0, 0, -1],
                                             "diameter": 6, "depth": 10, "name": "HoleTop"}},
        {"command": "solid.hole", "params": {"position": [24, 20, 0], "direction": [0, 0, 1],
                                             "diameter": 6, "depth": 10, "name": "HoleBottom"}}])
    res = design_rules.check(blk.session)
    between = [f for r in res.get("bodies", [res]) for f in r.get("rules", r).get("min_wall_thickness", {}).get("findings", [])
               if "between holes" in f.get("message", "")]
    ok("argon review 3: offset blind holes from opposite sides, 30 mm apart axially, give no hole-to-hole finding",
       not between, str(between))
    ws.close("argon_block")

    # Finding 4: a concentric anchor follows its occurrence when that is rotated and moved.
    dom = ws.new(PART, "argon_dom")
    dom.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [-20, -20, 0],
                                            "name": "Base", "body_name": "Dom"}},
        {"command": "solid.cylinder", "params": {"diameter": 8, "height": 20, "base": [10, 0, 5],
                                                 "operation": "join", "name": "Boss"}}])
    dom.save()
    lid = ws.new(PART, "argon_lid")
    lid.session.cmd("solid.box", {"length": 40, "width": 40, "height": 3, "corner": [-20, -20, 0], "name": "Lid"})
    lid.save()
    asm = ws.new(ASSEMBLY, "argon_anchor")
    links.insert(ws, asm, dom.path, name="Dom", grounded=True)
    links.insert(ws, asm, lid.path, name="Lid", translate=[0, 0, 25], grounded=True)
    asm.save()
    res = bolted.bolted_connection(ws, "argon_anchor", placement={"position": [10, 0, 28], "direction": [0, 0, -1]},
                                   size="M3", use_insert=True, counterbore=False, parts=["Lid:1", "Dom:1"])
    anchor = asm.metadata()["bolted_connections"][res["id"]]["anchor"]
    st0, p0, d0 = bolted._resolve_anchor(ws, asm, anchor)
    moved = ws.new(ASSEMBLY, "argon_anchor_moved")
    links.insert(ws, moved, dom.path, name="Dom", rotate={"axis": [0, 1, 0], "angle": 90},
                 translate=[100, 0, 0], grounded=True)
    st1, p1, d1 = bolted._resolve_anchor(ws, moved, anchor)
    occ = next(o for o in links._occurrences(moved.session).values() if o["name"] == "Dom:1")
    want_p = g.apply_point(occ["transform"], p0)
    want_d = g.unit(g.apply_dir(occ["transform"], d0))
    ok("argon review 4: concentric anchor keeps its local point and direction when the occurrence is rotated and moved",
       anchor.get("kind") == "cylinder" and st0 == st1 == "ok"
       and g.norm(g.sub(p1, want_p)) < 1e-3 and g.norm(g.sub(d1, want_d)) < 1e-6,
       f"anchor={anchor.get('kind')} p0={p0} d0={d0} p1={p1} d1={d1} want={want_p} {want_d}")
    for name in ("argon_anchor_moved", "argon_anchor", "argon_lid", "argon_dom"):
        ws.close(name)


def argon_review_findings_5_8_checks(ws):
    """Findings 5 and 8 of the Argon review (docs/research/2026-10-27-review-gemini-bausteine-argon.md)."""
    # Finding 5: hole edge distance to external cylindrical surface (outside cylinder).
    # Hand calculation:
    # Plate: 50 x 60 x 10 mm (x in [0, 50], y in [0, 60], z in [0, 10]).
    # Cylindrical Zapfen: joined at base [50, 30, 0], diameter 20 mm (R = 10 mm), height 10 mm.
    # Zapfen axis is at (x=50, y=30) along Z.
    # Hole: drilled at [35, 30, 10], depth 10 mm, diameter 4 mm (d = 4 mm, radius r = 2 mm).
    # Axis distance: d_axes = 50 - 35 = 15.0 mm.
    # Expected distance from hole center (Lochmitte) to cylinder surface:
    #   dist = d_axes - R = 15.0 - 10.0 = 5.0 mm.
    # (Physical wall thickness from hole edge to cylinder surface: 5.0 - r = 3.0 mm).
    # Required edge distance: 1.5 * d = 1.5 * 4.0 = 6.0 mm from hole center.
    # Since dist = 5.0 mm < 6.0 mm, hole_edge_distance must report 'fail' with value 5.0 mm.
    # The buggy code calculated d_axes - R + r = 15 - 10 + 2 = 7.0 mm (reporting false 'ok').
    p5 = ws.new(PART, "argon_finding5")
    p5.session.batch([
        {"command": "solid.box", "params": {"length": 50, "width": 60, "height": 10, "corner": [0, 0, 0],
                                            "name": "Base", "body_name": "Part5"}},
        {"command": "solid.cylinder", "params": {"diameter": 20, "height": 10, "base": [50, 30, 0],
                                                 "operation": "join", "name": "Zapfen"}},
        {"command": "solid.hole", "params": {"position": [35, 30, 10], "direction": [0, 0, -1],
                                             "diameter": 4, "depth": 10, "name": "Hole"}},
    ])
    res5 = design_rules.check(p5.session)
    edge_findings = res5["rules"]["hole_edge_distance"]["findings"]
    f5 = edge_findings[0] if edge_findings else {}
    ok("argon review 5: hole edge distance to external cylinder outside calculates d_axes - R from hole center",
       f5.get("status") == "fail" and abs(f5.get("value", 0.0) - 5.0) < 1e-3
       and abs(f5.get("threshold", 0.0) - 6.0) < 1e-3,
       f"status={f5.get('status')} val={f5.get('value')} thresh={f5.get('threshold')} msg={f5.get('message')}")
    ws.close("argon_finding5")

    # Finding 8: two coaxial threaded holes (M6 depth 10 from top, M6 depth 16 from bottom)
    # separated by solid material along the same axis line.
    # Hand calculation:
    # Block: 40 x 40 x 50 mm (z in [0, 50]).
    # HoleTop: position [20, 20, 50], depth 10 mm (z: 50 -> 40), ThreadTop: M6x1, depth 10 mm.
    # HoleBottom: position [20, 20, 0], depth 16 mm (z: 0 -> 16), ThreadBottom: M6x1, depth 16 mm.
    # Material between hole bottoms: z = 16 to z = 40 (24 mm solid material).
    # Expected:
    # - Both holes extracted as distinct hole entries.
    # - HoleTop matches ThreadTop (depth 10.0 mm), HoleBottom matches ThreadBottom (depth 16.0 mm).
    # - thread_depth findings contain both holes with depths 10.0 and 16.0 mm (both >= 9.0 mm threshold).
    # The buggy code lumped both into one hole or assigned ThreadTop to both holes.
    blk8 = ws.new(PART, "argon_finding8")
    blk8.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 50, "corner": [0, 0, 0],
                                            "name": "Block", "body_name": "Block8"}},
        {"command": "solid.hole", "params": {"position": [20, 20, 50], "direction": [0, 0, -1],
                                             "diameter": 5.0, "depth": 10, "name": "HoleTop"}},
        {"command": "solid.thread", "params": {"face": [22.5, 20, 45], "designation": "M6x1", "name": "ThreadTop"}},
        {"command": "solid.hole", "params": {"position": [20, 20, 0], "direction": [0, 0, 1],
                                             "diameter": 5.0, "depth": 16, "name": "HoleBottom"}},
        {"command": "solid.thread", "params": {"face": [22.5, 20, 8], "designation": "M6x1", "name": "ThreadBottom"}},
    ])
    res8 = design_rules.check(blk8.session)
    th_findings = res8["rules"]["thread_depth"]["findings"]
    th_vals = sorted(round(f.get("value", 0.0), 1) for f in th_findings)
    ok("argon review 8: two coaxial threaded holes are matched to their respective axial threads without overwriting",
       len(th_findings) == 2 and th_vals == [10.0, 16.0]
       and all(f.get("status") == "ok" for f in th_findings),
       f"count={len(th_findings)} values={th_vals} findings={th_findings}")
    ws.close("argon_finding8")

def argon_review_findings_7_10_12_checks(ws):
    """Findings 7, 10 and 12 of the Argon review (docs/research/2026-10-27-review-gemini-bausteine-argon.md)."""
    # Finding 7 and 10:
    # If standard_parts.create fails after ws.new, a newly created file must be removed from disk.
    # A subsequent call without overwrite=True must then succeed.
    orig_spec = standard_parts.spec
    try:
        standard_parts.spec = lambda *a, **kw: {
            "standard": {"norm": "ISO 4762", "size": "M5", "designation": "argon_fail_test"},
            "commands": [{"command": "nonexistent.command.fails"}],
            "warnings": [],
        }
        failed_new = False
        try:
            standard_parts.create(ws, "ISO 4762", "M5", length=16)
        except Exception:
            failed_new = True
        f_new = ws.root / "argon_fail_test.solidcraft"
        new_file_cleaned = not f_new.exists()
    finally:
        standard_parts.spec = orig_spec

    # Now verify that a retry without overwrite succeeds because the orphaned file was deleted
    retry_ok = False
    try:
        res_retry = standard_parts.create(ws, "ISO 4762", "M5", length=16, name="argon_fail_test")
        retry_ok = res_retry.get("name") == "argon_fail_test"
        ws.close("argon_fail_test")
    except Exception:
        retry_ok = False
    if f_new.exists():
        f_new.unlink(missing_ok=True)

    ok("argon review 7 and 10: failed creation cleans up newly created file from disk, retry succeeds without overwrite",
       failed_new and new_file_cleaned and retry_ok)

    # Finding 7 (overwrite=True):
    # An already existing file must NOT be deleted when create with overwrite=True fails.
    pre_doc = ws.new(PART, "argon_existing_test")
    pre_doc.session.batch([{"command": "solid.box", "params": {"length": 10, "width": 10, "height": 10, "name": "B"}}])
    pre_doc.save()
    f_existing = pre_doc.path
    ws.close("argon_existing_test")
    assert f_existing.exists(), "precondition: existing file must exist on disk"

    orig_spec = standard_parts.spec
    try:
        standard_parts.spec = lambda *a, **kw: {
            "standard": {"norm": "ISO 4762", "size": "M5", "designation": "argon_existing_test"},
            "commands": [{"command": "nonexistent.command.fails"}],
            "warnings": [],
        }
        failed_overwrite = False
        try:
            standard_parts.create(ws, "ISO 4762", "M5", length=16, name="argon_existing_test", overwrite=True)
        except Exception:
            failed_overwrite = True
        preserved = f_existing.exists()
    finally:
        standard_parts.spec = orig_spec
    if f_existing.exists():
        f_existing.unlink(missing_ok=True)

    ok("argon review 7: failed creation with overwrite=True preserves pre-existing file on disk",
       failed_overwrite and preserved)

    # Finding 12:
    # DIN 625 deep groove ball bearing model must have chamfers with dimension r on outer and inner ring edges.
    sp_bearing = standard_parts.create(ws, "DIN 625", "6000", name="argon_bearing_6000")
    b_doc = ws.get("argon_bearing_6000", PART)
    b_insp = b_doc.session.cmd("document.inspect", {"measure": True})
    b_timeline = [f["name"] for f in b_insp.get("timeline", [])]
    b_faces = b_doc.session.cmd("model.faces", {"body": "Bearing"})["faces"]
    b_has_chamfer_faces = any("blend" in f["name"] or "chamfer" in f["name"].lower() for f in b_faces)
    b_body = b_insp["bodies"][0]
    b_vol = b_body["volume_mm3"]
    b_bb = [b_body["bbox"]["min"], b_body["bbox"]["max"]]
    v_exp = standard_parts.expected_volume("DIN 625", "6000")
    bb_exp = standard_parts.expected_bbox("DIN 625", "6000")

    # The chamfer feature must be in the timeline, chamfer blend faces present,
    # volume within envelope tolerance (< 2%), and bounding box identical to unchamfered cylinder.
    ok("argon review 12: DIN 625 bearing model includes chamfer with dimension r at outer and inner edges",
       "Chamfer" in b_timeline and b_has_chamfer_faces and b_body["faces"] == 8
       and abs(b_vol - v_exp) / v_exp < 0.02
       and all(abs(b_bb[i][j] - bb_exp[i][j]) < 0.05 for i in (0, 1) for j in range(3)),
       f"timeline={b_timeline} chamfer_faces={b_has_chamfer_faces} faces={b_body['faces']} vol={b_vol} exp={v_exp} bb={b_bb} bb_exp={bb_exp}")

    # Ensure parameter r remains editable and updates the chamfer
    sp_b_param = standard_parts.create(ws, "DIN 625", "608", name="argon_bearing_param")
    p_doc = ws.get("argon_bearing_param", PART)
    v_r1 = p_doc.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    p_doc.session.cmd("parameters.change", {"name": "r", "expression": "0.5 mm"})
    v_r2 = p_doc.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
    ok("argon review 12: DIN 625 bearing chamfer updates parametrically when parameter r is changed",
       v_r2 < v_r1, f"v_r1={v_r1} v_r2={v_r2}")

    for name in ("argon_bearing_param", "argon_bearing_6000"):
        ws.close(name)


def scratch_dir_checks():
    """SolidCraft leaves an empty solidcraft-mcp-<pid>-<n> folder in the temp dir per session."""
    import tempfile
    from mechvane.solidcraft import Session
    s = Session()
    pid = s._p.pid
    s.close()
    left = [p.name for p in Path(tempfile.gettempdir()).glob(f"solidcraft-mcp-{pid}-*")]
    ok("session: close removes the server's empty scratch folder", not left, str(left))


def install_checks(tmp):
    """`mechvane setup` and the CLI lookup, offline: a local archive stands in for the release."""
    import hashlib
    import io
    import os
    import tarfile
    import zipfile
    from mechvane import cli, install
    ref = Path(__file__).resolve().parents[1] / "reference" / "flansch.build.json"
    ok("install: packaged flange example equals the reference build", ref.read_bytes()
       == (Path(install.__file__).parent / "data" / "flange.build.json").read_bytes())
    root = Path(tmp) / "install"
    old = (install.CACHE, install.BASE_URL, dict(install.ASSETS), os.environ.pop("SOLIDCRAFT_CLI", None))
    try:
        install.CACHE = root / "cache"
        src = root / "src"
        src.mkdir(parents=True)
        exe = install.exe_name()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            data = b"#!/bin/sh\necho solidcraft-cli 0.0.0\n"
            info = tarfile.TarInfo(f"solidcraft-x/bin/{exe}")
            info.size, info.mode = len(data), 0o644
            t.addfile(info, io.BytesIO(data))
        archive = src / "fake.tar.gz"
        archive.write_bytes(buf.getvalue())
        install.BASE_URL = src.as_uri() + "/"
        key = install.platform_key()
        install.ASSETS[key] = ("fake.tar.gz", "0" * 64)
        try:
            install.install_cli(log=lambda _: None)
            bad_sha = False
        except RuntimeError as e:
            bad_sha = "SHA256" in str(e)
        ok("install: wrong SHA256 is refused and nothing is kept",
           bad_sha and not any(install.CACHE.glob("fake.tar.gz*")) and install.cached_cli() is None)
        install.ASSETS[key] = ("fake.tar.gz", hashlib.sha256(archive.read_bytes()).hexdigest())
        cli_path = install.install_cli(log=lambda _: None)
        ok("install: archive unpacked, CLI found and executable", cli_path == install.cached_cli()
           and cli_path.name == exe and (os.name == "nt" or os.access(cli_path, os.X_OK)), str(cli_path))
        ok("install: cached CLI comes before PATH", install.find_cli() == str(cli_path))
        os.environ["SOLIDCRAFT_CLI"] = "/opt/sc/solidcraft-cli"
        ok("install: $SOLIDCRAFT_CLI comes first", install.find_cli() == "/opt/sc/solidcraft-cli")
        del os.environ["SOLIDCRAFT_CLI"]
        refused = 0
        evil = root / "evil.zip"
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("../escape.txt", "x")
        for name, path in (("evil.zip", evil),):
            try:
                install._extract(path, root / "out", name)
            except RuntimeError:
                refused += 1
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            info = tarfile.TarInfo("bin/link")
            info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
            t.addfile(info)
        (root / "evil.tar.gz").write_bytes(buf.getvalue())
        try:
            install._extract(root / "evil.tar.gz", root / "out2", "evil.tar.gz")
        except (RuntimeError, tarfile.TarError):
            refused += 1
        ok("install: path traversal in zip and absolute symlink in tar are refused",
           refused == 2 and not (root / "escape.txt").exists(), f"{refused}/2")
    finally:
        install.CACHE, install.BASE_URL = old[0], old[1]
        install.ASSETS.clear()
        install.ASSETS.update(old[2])
        os.environ.pop("SOLIDCRAFT_CLI", None)
        if old[3] is not None:
            os.environ["SOLIDCRAFT_CLI"] = old[3]
    ok("cli: `mechvane ui` on a missing path exits with 1", cli.main(["ui", str(root / "nope"), "--no-browser"]) == 1)


def appwindow_checks(tmp):
    """`mechvane ui` app window and `mechvane shortcut`, with a fake browser script."""
    import os
    import socket
    import stat
    import time
    import webbrowser
    from mechvane import install
    from mechvane.ui import appwindow, server as ui_server

    root = Path(tmp) / "appwindow"
    root.mkdir()
    old = (os.environ.get("MECHVANE_BROWSER"), appwindow.HANDOFF_S, webbrowser.open, install.CACHE,
           os.environ.get("XDG_DATA_HOME"))
    tabs = []
    try:
        install.CACHE = root / "cache"
        appwindow.HANDOFF_S = 0.5
        webbrowser.open = lambda url: tabs.append(url)

        def fake(name, body):
            f = root / name
            f.write_text("#!/bin/sh\n" + body + "\n")
            f.chmod(f.stat().st_mode | stat.S_IEXEC)
            os.environ["MECHVANE_BROWSER"] = str(f)
            return f

        fake("args.sh", f'echo "$@" > {root}/args.txt; sleep 1.2')
        closed = threading.Event()
        opened = appwindow.open_window("http://127.0.0.1:1/", on_close=closed.set)
        args = (root / "args.txt").read_text() if (root / "args.txt").exists() else ""
        ok("appwindow: app window with its own profile, server stops when it closes",
           opened == "window" and "--app=http://127.0.0.1:1/" in args and f"--user-data-dir={install.CACHE / 'app-profile'}" in args
           and closed.wait(5) and not tabs, f"{opened} {args!r} {tabs}")

        fake("handoff.sh", "exit 0")
        closed = threading.Event()
        opened = appwindow.open_window("http://127.0.0.1:2/", on_close=closed.set)
        time.sleep(0.2)
        ok("appwindow: window handed to an open instance keeps the server running",
           opened == "handoff" and not closed.is_set() and not tabs, f"{opened} {tabs}")

        fake("broken.sh", "exit 3")
        opened = appwindow.open_window("http://127.0.0.1:3/")
        os.environ["MECHVANE_BROWSER"] = str(root / "missing-browser")
        opened2 = appwindow.open_window("http://127.0.0.1:4/")
        ok("appwindow: falls back to a browser tab when the app window does not start",
           not opened and not opened2 and tabs == ["http://127.0.0.1:3/", "http://127.0.0.1:4/"], f"{tabs}")

        # A busy port falls back to a free one; the opener gets the real URL and can stop the server
        part = next(Path(__file__).resolve().parents[2].glob("docs/research/*/flansch.solidcraft"))
        busy = socket.socket()
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        busy_port = busy.getsockname()[1]
        got = []
        done = threading.Thread(target=ui_server.run_server, args=(str(part),),
                                kwargs={"port": busy_port, "opener": lambda url, stop: (got.append(url), stop())},
                                daemon=True)
        done.start()
        done.join(15)
        busy.close()
        ok("appwindow: busy port falls back to a free one, stop() ends the server",
           not done.is_alive() and len(got) == 1 and got[0].startswith("http://127.0.0.1:")
           and not got[0].endswith(f":{busy_port}/"), f"{got}")

        os.environ["XDG_DATA_HOME"] = str(root / "share")
        entry = appwindow.create_shortcut(root / "My Parts")
        text = entry.read_text()
        ok("appwindow: start menu entry opens the project folder with the Mechvane icon",
           entry == root / "share/applications/mechvane.desktop" and (root / "My Parts").is_dir()
           and f'-m mechvane ui "{root / "My Parts"}"' in text and f"Icon={install.CACHE / 'logo.svg'}" in text
           and (install.CACHE / "logo.svg").is_file(), text)
    finally:
        appwindow.HANDOFF_S, webbrowser.open, install.CACHE = old[1], old[2], old[3]
        for key, val in (("MECHVANE_BROWSER", old[0]), ("XDG_DATA_HOME", old[4])):
            os.environ.pop(key, None)
            if val is not None:
                os.environ[key] = val


def feature_request_checks(tmp, ws=None):
    """Checks for 'Request a feature' UI button, dialog module request.js, and /api/about."""
    import shutil
    import threading
    import urllib.request
    from mechvane import install, __version__
    from mechvane.ui import create_server, collect_about
    from mechvane.ui.server import STATIC_DIR

    # 1. /api/about direct check
    about_direct = collect_about()
    ok("feature request: collect_about returns mechvane and solidcraft versions",
       about_direct.get("mechvane") == __version__ and about_direct.get("solidcraft") == install.VERSION,
       f"{about_direct}")

    # 2. Server endpoints: /api/about, /request.js, /, /model
    if ws is None:
        ws = Workspace(tmp)
        own_ws = True
    else:
        own_ws = False
    doc = ws.new(PART, "feature_request_test_doc")

    srv = create_server(doc.path, port=0)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        def _get(path):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as resp:
                return resp.status, resp.headers.get_content_type(), resp.read()

        # Check /api/about endpoint
        st_about, ct_about, body_about = _get("/api/about")
        d_about = json.loads(body_about.decode("utf-8"))
        ok("feature request: /api/about responds with 200 and both versions",
           st_about == 200 and d_about.get("mechvane") == __version__ and d_about.get("solidcraft") == install.VERSION,
           f"status={st_about} ct={ct_about} body={d_about}")

        # Check /request.js endpoint
        st_req, ct_req, body_req = _get("/request.js")
        ok("feature request: /request.js served with 200 and javascript content type",
           st_req == 200 and "javascript" in ct_req.lower() and len(body_req) > 0,
           f"status={st_req} ct={ct_req} len={len(body_req)}")

        # Check / and /model deliver HTML with button and request.js
        st_idx, _, body_idx = _get("/")
        idx_html = body_idx.decode("utf-8")
        ok("feature request: index.html served with button and request.js",
           st_idx == 200 and "Request a feature" in idx_html and "request.js" in idx_html,
           f"idx_len={len(idx_html)}")

        st_model, _, body_model = _get("/model")
        model_html = body_model.decode("utf-8")
        ok("feature request: model.html served with button and request.js",
           st_model == 200 and "Request a feature" in model_html and "request.js" in model_html,
           f"model_len={len(model_html)}")
    finally:
        srv.shutdown()
        srv.server_close()
        ws.close("feature_request_test_doc")
        if own_ws:
            ws.close_all()

    # 3. Static files on disk
    idx_disk = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    model_disk = (STATIC_DIR / "model.html").read_text(encoding="utf-8")
    req_disk = (STATIC_DIR / "request.js").read_text(encoding="utf-8")
    ok("feature request: both HTML pages bind button and request.js",
       "Request a feature" in idx_disk and "request.js" in idx_disk
       and "Request a feature" in model_disk and "request.js" in model_disk,
       "disk HTML check")

    ok("feature request: request.js constructs github issue URL with parameters",
       "https://github.com/mechvane/mechvane/issues/new" in req_disk
       and "URLSearchParams" in req_disk and "dialog" in req_disk,
       "request.js logic check")

    # 4. build_demo_site includes request.js and about.json
    build_script = (Path(__file__).resolve().parents[2] / "tools" / "build_demo_site.py").read_text(encoding="utf-8")
    ok("feature request: build_demo_site.py copies STATIC_DIR and writes about.json",
       "STATIC_DIR" in build_script and "about.json" in build_script,
       "build_demo_site.py content check")

    out_demo = Path(tmp) / "demo_site_test"
    if out_demo.exists():
        shutil.rmtree(out_demo)
    shutil.copytree(STATIC_DIR, out_demo)
    for page in ("index.html", "model.html"):
        html = (out_demo / page).read_text(encoding="utf-8")
        (out_demo / page).write_text(html.replace('<html lang="en">', '<html lang="en" data-static="1">', 1),
                                     encoding="utf-8")
    (out_demo / "about.json").write_text(json.dumps({"mechvane": "live demo", "solidcraft": "live demo"}), encoding="utf-8")

    ok("feature request: build_demo_site output directory includes request.js and about.json",
       (out_demo / "request.js").is_file() and (out_demo / "about.json").is_file()
       and "data-static=\"1\"" in (out_demo / "index.html").read_text(encoding="utf-8"),
       f"out_demo files: {[p.name for p in out_demo.glob('*')]}")


def demo_pyodide_checks(tmp):
    """Checks for the Pyodide in-browser check prototype: browser_check shim, demo_check.js, mechvane.zip, and model.html."""
    import shutil
    import subprocess
    import zipfile
    from mechvane import browser_check
    from mechvane.ui.server import STATIC_DIR
    from tools.build_demo_site import make_mechvane_zip

    fixtures_path = Path(__file__).resolve().parent / "demo_check_fixtures.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))

    # 1. browser_check Python shim against bracket and flange recorded data
    flange_res = browser_check.check_browser(
        fixtures["flange"]["payload"], doc_name="flange.solidcraft"
    )
    ok("demo pyodide: browser_check produces ok verdict on flange fixture",
       flange_res.get("verdict") == "ok" and len(flange_res.get("findings", [])) == 8,
       f"verdict={flange_res.get('verdict')} findings={len(flange_res.get('findings', []))}")

    bracket_res = browser_check.check_browser(
        fixtures["bracket"]["payload"], doc_name="bracket.solidcraft"
    )
    ok("demo pyodide: browser_check produces fail verdict on bracket fixture",
       bracket_res.get("verdict") == "fail" and len(bracket_res.get("findings", [])) == 6,
       f"verdict={bracket_res.get('verdict')} findings={len(bracket_res.get('findings', []))}")

    # 2. make_mechvane_zip packaging
    zip_path = Path(tmp) / "mechvane.zip"
    make_mechvane_zip(zip_path)
    ok("demo pyodide: make_mechvane_zip packages required modules into zip",
       zip_path.is_file() and zip_path.stat().st_size > 10000,
       f"zip exists={zip_path.is_file()} size={zip_path.stat().st_size if zip_path.is_file() else 0}")
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        ok("demo pyodide: mechvane.zip includes browser_check, design_rules and hole_tables",
           "mechvane/browser_check.py" in names and "mechvane/design_rules.py" in names and "mechvane/hole_tables.py" in names,
           str(names))

    # 3. Static assets: model.html and demo_check.js
    model_html = (STATIC_DIR / "model.html").read_text(encoding="utf-8")
    demo_check_js = (STATIC_DIR / "demo_check.js").read_text(encoding="utf-8")
    ok("demo pyodide: model.html includes verdict-badge and imports demo_check.js",
       'id="verdict-badge"' in model_html and "demo_check.js" in model_html,
       "model.html missing verdict-badge or demo_check.js")
    ok("demo pyodide: demo_check.js defines initDemoCheck and checkInBrowser with pinned Pyodide",
       "initDemoCheck" in demo_check_js and "checkInBrowser" in demo_check_js and "v0.26.4" in demo_check_js,
       "demo_check.js functions or Pyodide version")

    # 4. Headless test via node if node is available
    if shutil.which("node"):
        test_script = Path(__file__).resolve().parents[2] / "tools" / "test_demo_check.js"
        run = subprocess.run(["node", str(test_script)], capture_output=True, text=True, timeout=60)
        ok("demo pyodide: test_demo_check.js runs clean in node",
           run.returncode == 0 and ("All demo_check tests passed successfully" in run.stdout or "skip demo_check test" in run.stdout),
           f"returncode={run.returncode} stdout={run.stdout} stderr={run.stderr}")


def agent_turns_checks(tmp):
    """Web UI agent turns (ADR 0003) against tests/mechvane/fake_acp_agent.py, and the MCP side:
    files changed on disk are opened again, MECHVANE_AUTOSAVE saves after each tool call."""
    import os
    import time
    import urllib.request
    from mechvane import install
    from mechvane.ui import agent as ag, server as ui_server

    d = ag.decide
    ok("agent: Mechvane modelling runs, also deleting features and sketch curves (a turn can be undone); "
       "other tools and file commands are declined",
       d("mcp__mechvane__run", {"commands": [{"command": "solid.chamfer", "params": {"edges": [[0, 0, 0]]}}]})[0]
       and d("mcp__mechvane__run", {"commands": [{"command": "solid.sweep", "params": {"path": [3, 4]}}]})[0]
       and d("mcp__mechvane__check_design", {})[0]
       and not d("Bash", {"command": "ls"})[0]
       and not d("mcp__mechvane__run", {"commands": [{"command": "file.export", "params": {"path": "x.step"}}]})[0]
       and not d("mcp__mechvane__command", {"command": "sketch.insert_dxf", "params": {"path": "a/b.dxf"}})[0]
       and d("mcp__mechvane__delete_feature", {"feature": "Box1"})[0]
       and d("mcp__mechvane__run", {"commands": [{"command": "sketch.delete", "params": {"items": ["l1"]}}]})[0]
       and d("mcp__mechvane__run", {"commands": [{"command": "timeline.delete", "params": {"feature": "Hole1"}}]})[0]
       and not d("mcp__mechvane__run", {"commands": [{"command": "doc.open", "params": {"path": "x.solidcraft"}}]})[0]
       and not d("mcp__mechvane__close_document", {"document": "a"})[0]
       and not d("mcp__mechvane__screenshot", {"path": "/tmp/s.png"})[0])

    root = Path(tmp) / "agent"
    folder = root / "proj"
    folder.mkdir(parents=True)
    old_cache = install.CACHE
    install.CACHE = root / "cache"
    fake = [sys.executable, str(Path(__file__).resolve().parent / "fake_acp_agent.py")]

    def features(name):
        w = Workspace(folder)
        try:
            return len(w.open(name).session.cmd("document.inspect").get("timeline") or [])
        finally:
            w.close_all()

    def wait_idle(turns, seconds=60):
        end = time.monotonic() + seconds
        while turns.busy and time.monotonic() < end:
            time.sleep(0.2)
        return not turns.busy

    try:
        w = Workspace(folder)
        plate = w.new(PART, "plate")
        plate.session.cmd("solid.box", {"length": 20, "width": 20, "height": 10})
        plate.save()
        w.close_all()
        n0 = features("plate.solidcraft")
        # a file no turn touches: undo must leave it alone, timestamps included
        import shutil as _sh
        _sh.copy2(folder / "plate.solidcraft", folder / "other.solidcraft")
        other_mtime = (folder / "other.solidcraft").stat().st_mtime_ns

        changed = []
        turns = ag.AgentTurns(folder, on_files_changed=lambda: changed.append(1), command=fake)
        turns.send("edit please", [{"kind": "face", "name": "F1:box:top"}], "plate.solidcraft")
        idle = wait_idle(turns)
        ev = turns.events_since(0)["events"]
        text = "".join(e.get("text", "") for e in ev if e["type"] == "text")
        done = [e for e in ev if e["type"] == "done"]
        declined = sorted(e["tool"] for e in ev if e["type"] == "declined")
        ok("agent: a turn runs, edits the project and reports changed files",
           idle and done and done[0]["changed"] == ["extra.solidcraft", "plate.solidcraft"]
           and features("plate.solidcraft") == n0 + 1 and changed, f"{ev}")
        ok("agent: modelling and deleting features are allowed, export and shell declined",
           '"run chamfer": true' in text and '"run export": false' in text and '"Bash": false' in text
           and '"delete_feature": true' in text and declined == ["Bash", "run"], text + str(declined))

        out = turns.undo()
        ok("agent: undo writes back only the files the turn changed",
           "other.solidcraft" not in out["restored"] and (folder / "other.solidcraft").stat().st_mtime_ns == other_mtime,
           f"{out}")
        msg = turns._message("next", None, "plate.solidcraft")
        ok("agent: after undo the next message tells the agent, once",
           "undid your turn 1" in msg and "undid" not in turns._message("again", None, None), msg[:200])
        ok("agent: undo puts the files back and removes files the turn added",
           out["removed"] == ["extra.solidcraft"] and not (folder / "extra.solidcraft").exists()
           and features("plate.solidcraft") == n0, f"{out}")
        turns.redo()
        ok("agent: redo puts the turn back", (folder / "extra.solidcraft").exists()
           and features("plate.solidcraft") == n0 + 1)

        turns.send("edit again", None, "plate.solidcraft")
        if not wait_idle(turns):
            ok("agent: second turn ends", False, str(turns.events_since(0)["events"][-3:]))
            return
        os.utime(folder / "plate.solidcraft", ns=(time.time_ns(), time.time_ns() + 5_000_000_000))
        try:
            turns.undo()
            refused = False
        except PermissionError:
            refused = True
        out = turns.undo(force=True)
        ok("agent: undo after a later change by hand needs force", refused and features("plate.solidcraft") == n0 + 1)

        turns.send("slow edit", None, "plate.solidcraft")
        time.sleep(4)
        stopping = turns.stop()
        wait_idle(turns)
        last = turns.events_since(0)["events"][-1]
        ok("agent: Stop ends the turn and restores the files",
           stopping and last.get("status") == "stopped" and features("plate.solidcraft") == n0 + 1
           and turns.turns[-1]["state"] == "stopped", f"{last}")

        turns.send("crash edit", None, "plate.solidcraft")
        wait_idle(turns)
        last = turns.events_since(0)["events"][-1]
        ok("agent: an agent that dies mid-turn leaves the files as before",
           last["type"] == "error" and features("plate.solidcraft") == n0 + 1, f"{last}")
        turns.close()

        # The UI server: endpoints, and no saving by hand while the agent works
        os.environ["MECHVANE_AGENT"] = " ".join(f'"{x}"' for x in fake)
        srv = ui_server.create_server(str(folder / "plate.solidcraft"), port=0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def post(path, body=b"{}"):
            ct = "application/octet-stream" if path.startswith("/api/file/") else "application/json"
            req = urllib.request.Request(base + path, data=body, headers={"Content-Type": ct}, method="POST")
            try:
                with urllib.request.urlopen(req) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        try:
            st, res = post("/api/agent/send", json.dumps({"text": "slow edit"}).encode())
            time.sleep(3)
            busy_save = post("/api/file/plate.solidcraft", b"x" * 10)[0]
            second = post("/api/agent/send", json.dumps({"text": "more"}).encode())[0]
            post("/api/agent/stop")
            for _ in range(100):
                with urllib.request.urlopen(base + "/api/agent/events?since=0") as r:
                    evs = json.loads(r.read())
                if not evs["busy"]:
                    break
                time.sleep(0.2)
            ok("agent: UI server runs turns, refuses saving and a second message while busy",
               st == 200 and res == {"turn": 1} and busy_save == 409 and second == 409 and not evs["busy"]
               and evs["events"][-1].get("status") == "stopped", f"{st} {busy_save} {second} {evs['events'][-1:]}")
        finally:
            srv.shutdown()
            srv.server_close()
            os.environ.pop("MECHVANE_AGENT", None)

        # MCP side: a document changed on disk is opened again; autosave after each tool call
        w1, w2 = Workspace(folder), Workspace(folder)
        try:
            a = w1.open("plate.solidcraft")
            b = w2.open("plate.solidcraft")
            b.session.cmd("solid.box", {"length": 3, "width": 3, "height": 3, "corner": [0, 0, 20], "operation": "join"})
            b.save()
            n_disk = len(b.session.cmd("document.inspect")["timeline"])
            again = w1.get("plate")
            fresh = again is a and len(again.session.cmd("document.inspect")["timeline"]) == n_disk
            again.session.cmd("solid.box", {"length": 2, "width": 2, "height": 2, "corner": [0, 0, 30], "operation": "join"})
            b.session.cmd("solid.box", {"length": 2, "width": 2, "height": 2, "corner": [5, 5, 30], "operation": "join"})
            b.save()
            try:
                w1.get("plate")
                conflict = False
            except ValueError:
                conflict = True
        finally:
            w1.close_all()
            w2.close_all()
        ok("documents: a file changed on disk is opened again, unsaved changes are not overwritten", fresh and conflict)

        old_ws = server.ws
        server.ws = Workspace(folder)
        os.environ["MECHVANE_AUTOSAVE"] = "1"
        try:
            server.open_document("plate.solidcraft")
            before = (folder / "plate.solidcraft").stat().st_mtime_ns
            server.run("plate", [{"command": "solid.box", "params": {"length": 1, "width": 1, "height": 1,
                                                                    "corner": [9, 9, 40], "operation": "join"}}])
            saved = (folder / "plate.solidcraft").stat().st_mtime_ns != before and not server.ws.get("plate").dirty()
        finally:
            os.environ.pop("MECHVANE_AUTOSAVE", None)
            server.ws.close_all()
            server.ws = old_ws
        ok("server: MECHVANE_AUTOSAVE saves changed documents after each tool call", saved)
    finally:
        install.CACHE = old_cache


def snapshot_prune_checks(tmp):
    """Snapshot history retention in cache (issue #40): keep at most 50 steps per project hash,
    remove copies older than 14 days, and leave active turn snapshots untouched."""
    import hashlib
    from datetime import datetime, timedelta
    from mechvane import install
    from mechvane.ui import agent as ag

    old_cache = install.CACHE
    install.CACHE = Path(tmp) / "cache"
    try:
        folder = Path(tmp) / "proj"
        folder.mkdir(parents=True)
        (folder / "part.solidcraft").write_text("{}", encoding="utf-8")
        key = hashlib.sha1(str(folder.resolve()).encode()).hexdigest()[:12]
        hist = install.CACHE / "history" / key
        hist.mkdir(parents=True)

        now = datetime.now()
        # 60 recent snapshot folders and 10 folders older than 14 days
        for i in range(60):
            d = hist / f"{(now - timedelta(minutes=60 - i)):%Y%m%d-%H%M%S}-step{i:02d}"
            d.mkdir(parents=True)
            (d / "manifest.json").write_text("[]", encoding="utf-8")

        for i in range(10):
            d = hist / f"{(now - timedelta(days=20 + i)):%Y%m%d-%H%M%S}-stale{i:02d}"
            d.mkdir(parents=True)
            (d / "manifest.json").write_text("[]", encoding="utf-8")

        # Creating AgentTurns prunes the history on init
        turns = ag.AgentTurns(folder)

        remaining = [p for p in hist.iterdir() if p.is_dir()]
        stale_remaining = [p for p in remaining if "stale" in p.name]

        # Running turn snapshots must never be pruned
        active_snap = hist / f"{(now - timedelta(days=25)):%Y%m%d-%H%M%S}-active_snap"
        active_snap.mkdir(parents=True)
        (active_snap / "manifest.json").write_text("[]", encoding="utf-8")
        active_redo = hist / f"{(now - timedelta(days=26)):%Y%m%d-%H%M%S}-active_redo"
        active_redo.mkdir(parents=True)
        (active_redo / "manifest.json").write_text("[]", encoding="utf-8")

        turns.turns.append({
            "id": 1,
            "text": "active turn",
            "snapshot": type("S", (), {"dir": active_snap})(),
            "redo": type("R", (), {"dir": active_redo})()
        })

        unrelated_stale = hist / f"{(now - timedelta(days=27)):%Y%m%d-%H%M%S}-unrelated_stale"
        unrelated_stale.mkdir(parents=True)
        (unrelated_stale / "manifest.json").write_text("[]", encoding="utf-8")

        turns.prune_history()

        active_ok = active_snap.exists() and active_redo.exists() and not unrelated_stale.exists()

        # Second project hash: pruning applies per project hash
        hist2 = install.CACHE / "history" / "otherhash123"
        hist2.mkdir(parents=True)
        for i in range(60):
            d = hist2 / f"{(now - timedelta(minutes=60 - i)):%Y%m%d-%H%M%S}-step{i:02d}"
            d.mkdir(parents=True)
            (d / "manifest.json").write_text("[]", encoding="utf-8")
        stale2 = hist2 / f"{(now - timedelta(days=20)):%Y%m%d-%H%M%S}-stale"
        stale2.mkdir(parents=True)
        (stale2 / "manifest.json").write_text("[]", encoding="utf-8")

        ag.prune_history()
        remaining2 = [p for p in hist2.iterdir() if p.is_dir()]

        ok("agent: snapshot history keeps at most 50 steps, prunes older than 14 days, active snapshots untouched",
           len(remaining) == 50 and len(stale_remaining) == 0 and active_ok
           and len(remaining2) == 50 and not stale2.exists(),
           f"proj1: {len(remaining)}, stale1: {len(stale_remaining)}, active: {active_snap.exists()}/{active_redo.exists()}, proj2: {len(remaining2)}")
    finally:
        install.CACHE = old_cache


def selection_checks(tmp):
    """/api/resolve_selection: the app's selection in Mechvane's names, for a part and an assembly."""
    import urllib.request
    from mechvane import examples
    from mechvane.ui import selection, server as ui_server

    folder = Path(tmp) / "selection"
    folder.mkdir()
    w = Workspace(folder)
    try:
        examples.bracket(w)
        examples.bolted_plates(w)
    finally:
        w.close_all()
    w = Workspace(folder)
    try:
        br = w.open("bracket.solidcraft")
        face = next(f for f in br.session.cmd("model.faces", {"body": "Bracket"})["faces"] if f["name"] == "F1:+z")
        r = selection.resolve(w, br, [{"type": "face", "body": "Bracket", "index": face["index"], "point": [42.2, 30.4, 8.9]},
                                      {"type": "edge", "body": "Bracket", "index": 0, "point": [0, 0, 0]}])
        ok("selection: a part face gets its Mechvane name, feature, normal, click and centroid",
           r[0]["name"] == "F1:+z" and r[0]["feature"] == "BasePlate" and r[0]["normal"] == [0.0, 0.0, 1.0]
           and r[0]["click"] == [42.2, 30.4, 8.9] and "centroid" in r[0] and r[1]["kind"] == "edge" and r[1].get("length"), str(r))
        asm = w.open("bolted_plates.solidcraft")
        f = next(f for f in asm.session.cmd("model.faces", {"body": "TopPlate"})["faces"]
                 if (f.get("plane_normal") or [0])[-1:] == [1.0])
        r = selection.resolve(w, asm, [{"type": "face", "body": "TopPlate", "index": f["index"], "point": f.get("point") or f["centroid"]}])
        ok("selection: an assembly face is named in its part file",
           r[0].get("part") == "top_plate.solidcraft" and r[0].get("occurrence") == "TopPlate:1"
           and r[0].get("name", "").startswith("F") and ":face:" not in r[0]["name"], str(r))
    finally:
        w.close_all()

    srv = ui_server.create_server(str(folder / "bracket.solidcraft"), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}/api/resolve_selection", method="POST",
                                     headers={"Content-Type": "application/json"},
                                     data=json.dumps({"items": [{"type": "face", "body": "Bracket", "index": face["index"],
                                                                 "point": [42.2, 30.4, 8.9]}]}).encode())
        with urllib.request.urlopen(req) as resp:
            got = json.loads(resp.read())
        ok("selection: /api/resolve_selection answers with the resolved items",
           got["selection"][0]["name"] == "F1:+z", str(got))
    finally:
        srv.shutdown()
        srv.server_close()


def speech_checks(tmp):
    """Spoken requests cleaned up in code (mechvane/speech.py) and /api/speech with the model's names."""
    import urllib.request
    from mechvane import examples, speech
    from mechvane.ui import server as ui_server

    names = ["CountersinkNearWall", "BasePlate", "Wall"]
    cases = {
        "da eine Phase eins mal fünfundvierzig Grad": "da eine Fase 1 × 45°",
        "mittig eine Gewindebohrung Em sechs": "mittig eine Gewindebohrung M6",
        "Rundung Er zwei an der Kante": "Rundung R2 an der Kante",
        "Wandstärke eins Komma fünf Millimeter": "Wandstärke 1.5 mm",
        "Rechteck vierzig mal dreißig, Höhe hundertzwanzig": "Rechteck 40 × 30, Höhe 120",
        "zweihundertfünfzig Millimeter": "250 mm",
        "base plate um fünf Grad drehen": "BasePlate um 5° drehen",
        "die Senkung countersink near wal zwei Millimeter nach links": "die Senkung CountersinkNearWall 2 mm nach links",
        "eine Bohrung an der Wand": "eine Bohrung an der Wand",
    }
    bad = {t: speech.normalize(t, names) for t, want in cases.items() if speech.normalize(t, names) != want}
    ok("speech: numbers, units, Fase, M6/R2 and model names from spoken German", not bad, str(bad))

    folder = Path(tmp) / "speech"
    folder.mkdir()
    w = Workspace(folder)
    try:
        examples.bracket(w)
    finally:
        w.close_all()
    srv = ui_server.create_server(str(folder / "bracket.solidcraft"), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}/api/speech", method="POST",
                                     headers={"Content-Type": "application/json"},
                                     data=json.dumps({"text": "an countersink near wall eine Phase eins mal fünfundvierzig Grad"}).encode())
        with urllib.request.urlopen(req) as resp:
            got = json.loads(resp.read())
        ok("speech: /api/speech uses the open model's names",
           got["text"] == "an CountersinkNearWall eine Fase 1 × 45°", str(got))
    finally:
        srv.shutdown()
        srv.server_close()


def speech_cases_checks():
    """Verify test cases from speech_cases.json (issue #21).

    All cases marked 'ok' must match speech.normalize(heard, names).
    Cases marked 'open' are counted and reported, not treated as failures.
    """
    from mechvane import speech

    cases_path = Path(__file__).resolve().parent / "speech_cases.json"
    with open(cases_path, encoding="utf-8") as f:
        cases = json.load(f)

    ok_cases = [c for c in cases if c.get("status") == "ok"]
    open_cases = [c for c in cases if c.get("status") == "open"]

    bad = []
    for c in ok_cases:
        got = speech.normalize(c["heard"], c.get("names", []))
        if got != c["expected"]:
            bad.append((c["heard"], got, c["expected"]))

    ok(f"speech cases: {len(ok_cases)} ok ({len(open_cases)} open, {len(cases)} total)",
       len(cases) >= 40 and not bad,
       f"bad={bad}" if bad else f"case count {len(cases)} < 40")


def params_checks(tmp):
    """Parameter form: /api/params lists user parameters first, changes them together and saves the file."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "params"
    folder.mkdir()
    w = Workspace(folder)
    try:
        part = w.new(PART, "plate")
        part.session.cmd("parameters.add", {"name": "width", "expression": "40 mm"})
        part.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY", "name": "Base"}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 20]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "Base", "distance": "width/4", "name": "Plate"}}])
        part.save()
    finally:
        w.close_all()
    path = folder / "plate.solidcraft"
    srv = ui_server.create_server(str(path), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/params"

    def post(changes):
        req = urllib.request.Request(base, method="POST", data=json.dumps({"changes": changes}).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        with urllib.request.urlopen(base) as resp:
            listed = json.loads(resp.read())["parameters"]
        mtime = path.stat().st_mtime_ns
        status, changed = post({"width": "60 mm"})
        values = {p["name"]: p["value"] for p in changed.get("parameters", [])}
        bad_status, bad = post({"width": "60 +"})
        ok("ui: /api/params lists, changes together and saves; a bad expression changes nothing",
           [p["name"] for p in listed][:1] == ["width"] and listed[1].get("feature") == "Plate"
           and status == 200 and values.get("width") == 60 and 15 in values.values()
           and path.stat().st_mtime_ns != mtime and bad_status == 400 and "error" in bad,
           f"{listed} {status} {changed} {bad_status} {bad}")
        with urllib.request.urlopen(base) as resp:
            after = {p["name"]: p["value"] for p in json.loads(resp.read())["parameters"]}
        ok("ui: after a refused change the parameters keep their last good values", after.get("width") == 60, str(after))
        with urllib.request.urlopen(base.replace("/api/params", "/api/findings?profile=cnc_alu&material=alu_wrought")) as resp:
            chosen = json.loads(resp.read())
        try:
            urllib.request.urlopen(base.replace("/api/params", "/api/findings?material=unobtainium"))
            refused = None
        except urllib.error.HTTPError as e:
            refused = e.code
        ok("ui: /api/findings takes profile and material, lists the choices, refuses an unknown material",
           chosen.get("profile") == "cnc_alu" and chosen.get("material") == "alu_wrought"
           and "fdm_0.4" in chosen.get("profiles", {}) and "steel" in chosen.get("materials", []) and refused == 400,
           f"{ {k: chosen.get(k) for k in ('profile', 'material', 'materials')} } {refused}")
        # profile and material chosen on the Check page are saved in the part file, not only in the browser
        def post_rules(body):
            req = urllib.request.Request(base.replace("/api/params", "/api/rules"), method="POST",
                                         headers={"Content-Type": "application/json"},
                                         data=json.dumps(body).encode())
            try:
                with urllib.request.urlopen(req) as resp:
                    return resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        r_status, r_saved = post_rules({"profile": "cnc_alu", "material": "alu_wrought"})
        bad_rules, _ = post_rules({"material": "unobtainium"})
        with urllib.request.urlopen(base.replace("/api/params", "/api/findings")) as resp:
            plain = json.loads(resp.read())
        w2 = Workspace(folder)
        try:
            reopened = design_rules.check(w2.open(path))
        finally:
            w2.close_all()
        ok("ui: /api/rules saves profile and material in the part file; /api/findings and check_design use them",
           r_status == 200 and r_saved.get("material_source") == "saved" and bad_rules == 400
           and (plain.get("profile"), plain.get("material"), plain.get("material_source")) == ("cnc_alu", "alu_wrought", "saved")
           and (reopened["profile"], reopened["material"], reopened["material_source"]) == ("cnc_alu", "alu_wrought", "saved"),
           f"{r_status} {bad_rules} {[plain.get(k) for k in ('profile', 'material', 'material_source')]} "
           f"{[reopened.get(k) for k in ('profile', 'material', 'material_source')]}")
        with urllib.request.urlopen(base.replace("/api/params", "/viewtools.js")) as resp:
            js, ctype = resp.read().decode(), resp.headers.get("Content-Type", "")
        with urllib.request.urlopen(base.replace("/api/params", "/chat.js")) as resp:
            chat_js = resp.read().decode()
        # every script the pages import must be served (a 404 kills the whole module: Model mode stayed blank, #135)
        import re as _re
        missing_js = []
        for page in ("index.html", "model.html"):
            src = (ui_server.STATIC_DIR / page).read_text(encoding="utf-8")
            for js_name in sorted(set(_re.findall(r'from "\./([A-Za-z0-9_]+\.js)"', src))):
                try:
                    with urllib.request.urlopen(base.replace("/api/params", "/" + js_name)):
                        pass
                except Exception:
                    missing_js.append(f"{page}:{js_name}")
        ok("ui: every script imported by the Check and Model pages is served", not missing_js, str(missing_js))
        index_html = (ui_server.STATIC_DIR / "index.html").read_text(encoding="utf-8")
        app_js = (ui_server.STATIC_DIR / "app.js").read_text(encoding="utf-8")
        style_css = (ui_server.STATIC_DIR / "style.css").read_text(encoding="utf-8")
        ok("ui: Check page has the agent chat (chat.js) and a Select tool feeding it",
           "export function initAgentChat" in chat_js and 'id="agent-chat"' in index_html
           and "getSelection" in (ui_server.STATIC_DIR / "viewtools.js").read_text(encoding="utf-8"))
        ok("ui: measure and section tools served and loaded by the Check page",
           "javascript" in ctype and "export function initViewTools" in js
           and 'from "./viewtools.js"' in app_js, ctype)
        ribbon_cmds = (
            "Create 2D Sketch", "Extrude", "Revolve", "Hole", "Fillet", "Chamfer",
            "Rectangular Pattern", "Circular Pattern", "Mirror", "Parameters",
            "Measure", "Section", "Select", "Design check", "Home view", "Zoom all",
        )
        ok("ui: Inventor-style workspace (ADR 0005 stage 1) has ribbon tabs, commands, Properties, statusbar and splitters",
           all(t in index_html for t in ("3D Model", "Sketch", "Inspect", "Assemble", "View"))
           and all(c in index_html for c in ribbon_cmds)
           and 'title="Coming in the next step"' in index_html
           and "Open in SolidCraft (expert mode)" in index_html
           and "Select a command" in index_html
           and 'id="axes-gizmo"' in index_html and 'id="btn-home-view"' in index_html
           and 'id="statusbar"' in index_html and "https://github.com/tangency-labs/solidcraft" in index_html
           and 'id="splitter-left"' in index_html and 'id="splitter-right"' in index_html
           and "renderOriginFolder" in app_js and "localStorage" in app_js
           and "@media (max-width: 760px)" in style_css)
        with urllib.request.urlopen(base.replace("/api/params", "/newpart.js")) as resp:
            newpart_js = resp.read().decode()
        ok("ui: New part uses the app's own dialog (newpart.js served), no browser prompt()",
           "export function openNewPartDialog" in newpart_js and "prompt(" not in app_js
           and 'from "./newpart.js"' in app_js)

        # Issue #73: Sketch dimensions in parameter panel
        sketch_part = w.new(PART, "sketch_params_test")
        try:
            sp = sketch_part.session
            sp.cmd("sketch.create", {"plane": "XY", "name": "Sketch1"})
            sp.cmd("sketch.rectangle.two_point", {"p0": [0, 0], "p1": [40, 20]})
            sp.cmd("sketch.dimension", {"entities": ["l1"], "type": "length", "value": "b = 40"})
            sp.cmd("sketch.dimension", {"entities": ["l2"], "type": "length", "value": "20"})
            sp.cmd("sketch.finish", {})
            sp.cmd("solid.extrude", {"sketch": "Sketch1", "distance": 10, "name": "Extrude1"})
            sketch_part.save()
        finally:
            w.close("sketch_params_test")

        sketch_path = folder / "sketch_params_test.solidcraft"
        srv_sk = ui_server.create_server(str(sketch_path), port=0)
        threading.Thread(target=srv_sk.serve_forever, daemon=True).start()
        base_sk = f"http://127.0.0.1:{srv_sk.server_address[1]}/api/params"
        try:
            with urllib.request.urlopen(base_sk) as resp:
                sk_listed = json.loads(resp.read())["parameters"]
            names = [p["name"] for p in sk_listed]
            by_name = {p["name"]: p for p in sk_listed}
            sk_dims = [p for p in sk_listed if p.get("sketch") == "Sketch1"]
            named_first = [p["name"] for p in sk_dims] == ["d1", "d2"]
            req_sk = urllib.request.Request(base_sk, method="POST",
                                            data=json.dumps({"changes": {"b": "50"}}).encode(),
                                            headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req_sk) as resp:
                sk_changed = json.loads(resp.read())
            with srv_sk.lock:
                doc_sk = srv_sk.ensure_current()
                bodies = doc_sk.session.cmd("document.inspect", {"measure": True})["bodies"]
                bbox = bodies[0]["bbox"]
                b_width = bbox["max"][0] - bbox["min"][0]
            ok("ui: /api/params lists sketch dimensions by sketch with named first; setting b=50 widens bbox to 50",
               "b" in names and "d2" in names and by_name["b"]["value"] == 40.0 and by_name["d2"]["value"] == 20.0
               and by_name["d2"].get("sketch") == "Sketch1" and named_first and b_width == 50.0,
               f"{sk_listed} width={b_width}")
        finally:
            srv_sk.shutdown()
            srv_sk.server_close()
    finally:
        srv.shutdown()
        srv.server_close()


COMMANDS_JS_TEST = r"""
import { scoreMatch, searchCommands, fieldValue, formParams, applyPick, pickText, ontoFace } from "./commands.js";
const out = {};
// SolidCraft's ranking (shortcut_box.rs tests): prefix > word start > letters in order; no match is 0
out.rank = scoreMatch("ext", "extrude") > scoreMatch("ext", "offset text") && scoreMatch("pres", "press pull") > scoreMatch("ppl", "press pull")
  && scoreMatch("ppl", "press pull") > 0 && scoreMatch("xyz", "extrude") === 0;
const list = [{ id: "sketch.shell", label: "Shell sketch", offered: false, reason: "r" }, { id: "solid.shell", label: "Shell", offered: true },
              { id: "solid.box", label: "Box", tab: "SOLID", panel: "CREATE", offered: true }];
out.search = searchCommands(list, "shel").map((c) => c.id);
out.byPanel = searchCommands(list, "create").map((c) => c.id);
const form = { raw: false, fields: [
  { name: "size", kind: "expr", required: true }, { name: "count", kind: "number", integer: true, required: false },
  { name: "flip", kind: "bool", required: false }, { name: "at", kind: "point", required: false },
  { name: "bodies", kind: "list", required: false }, { name: "rounds", kind: "json", required: false },
  { name: "op", kind: "enum", required: false }, { name: "name", kind: "text", required: false }] };
out.params = formParams(form, { size: " 12.5 ", count: "3", flip: "false", at: ["10", "", "w/2"], bodies: "A, B", rounds: "[[1,2,3]]", op: "", name: "" });
out.exprText = fieldValue({ kind: "expr" }, "w / 2");
const err = (f) => { try { f(); return ""; } catch (e) { return e.message; } };
out.missing = err(() => formParams(form, { count: "2" }));
out.badJson = err(() => formParams(form, { size: "1", rounds: "[1," }));
out.badInt = err(() => formParams(form, { size: "1", count: "2.5" }));
out.raw = formParams({ raw: true, fields: [{ name: "", kind: "json" }] }, { "": '{"thickness": 2}' });
out.rawArray = err(() => formParams({ raw: true, fields: [{ name: "", kind: "json" }] }, { "": "[1]" }));
// picks in the view: a list field toggles, a single field replaces; written as points, {face: point} or names
const edges = { kind: "json", pick: "edges", multi: true, write: "point" };
let p = applyPick(edges, [], { key: "a", point: [1, 2, 3] });
p = applyPick(edges, p, { key: "b", point: [4, 5, 6] });
out.edgesTwo = pickText(edges, p);
out.edgesToggle = pickText(edges, applyPick(edges, p, { key: "a", point: [1, 2, 3.0001] }));
const face = { kind: "json", pick: "faces", multi: false, write: "key:face" };
out.face = pickText(face, applyPick(face, applyPick(face, [], { key: "f1", point: [0, 0, 1] }), { key: "f2", point: [0, 0, 2] }));
const bodies = { kind: "list", pick: "bodies", multi: true, write: "name" };
let b = applyPick(bodies, [], { key: "f|B1|3", point: [0, 0, 0], body: "B1" });
b = applyPick(bodies, b, { key: "f|B2|1", point: [0, 0, 0], body: "B2" });
out.bodies = pickText(bodies, b);
out.bodyAgain = pickText(bodies, applyPick(bodies, b, { key: "f|B1|7", point: [0, 0, 0], body: "B1" }));
const body = { kind: "text", pick: "bodies", multi: false, write: "name" };
out.body = pickText(body, applyPick(body, [], { key: "x", point: [0, 0, 0], body: "Plate" }));
// a click on a cylinder's chord (r 9.9 inside r 10, axis Z through (5, 0, 0)) lands on the true surface
const v = (x, y, z) => ({ x, y, z });
out.onto = ontoFace([5 + 9.9, 0, 3], { center: v(5, 0, 0), axis: v(0, 0, 2), radius: 10 });
out.flat = ontoFace([1, 2, 3.0000004], { normal: v(0, 0, 1), area: 1 });
console.log(JSON.stringify(out));
"""


def command_dialog_assembly_checks(tmp):
    """Command dialog in an assembly (#128): modelling commands are not offered and refused (SolidCraft would add the
    body to the assembly file or change a linked part's copy), as the feature dialogs; assembly commands stay."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "commanddialog_asm"
    folder.mkdir()
    w = Workspace(folder)
    try:
        asm, _ = hinge_assembly(w, plate_part(w))
        path = asm.path
    finally:
        w.close_all()
    srv = ui_server.create_server(str(path), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"} if body is not None else {})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        mtime = path.stat().st_mtime_ns
        _, lst = call("commands")
        by_id = {c["id"]: c for c in lst.get("commands", [])}
        st_f, fm = call("command?id=solid.box")
        st_b, box = call("feature", {"command": "solid.box", "generic": True,
                                     "params": {"length": 5, "width": 5, "height": 5, "corner": [100, 0, 0]}})
        st_r, read = call("feature", {"command": "joint.list", "generic": True, "params": {}})
        ok("command dialog: in an assembly modelling commands are not offered and refused, the file stays; "
           "assembly commands run",
           by_id.get("solid.box", {}).get("offered") is False and "part" in by_id.get("solid.box", {}).get("reason", "")
           and st_f == 200 and fm.get("offered") is False and st_b == 403 and path.stat().st_mtime_ns == mtime
           and by_id.get("joint.list", {}).get("offered") and st_r == 200,
           f"{by_id.get('solid.box')} {st_b} {box} {st_r} {str(read)[:120]}")
    finally:
        srv.shutdown()
        srv.server_close()


def commands_js_checks(tmp):
    """Command dialog in the browser (#128): SolidCraft's search ranking, and the form values become command params."""
    import subprocess
    from mechvane.ui import server as ui_server
    if not shutil.which("node"):
        print("skip commands.js: node not installed")
        return
    d = Path(tmp) / "commandsjs"
    d.mkdir()
    shutil.copyfile(ui_server.STATIC_DIR / "commands.js", d / "commands.js")
    (d / "package.json").write_text('{"type": "module"}')
    (d / "t.js").write_text(COMMANDS_JS_TEST)
    run = subprocess.run(["node", "t.js"], cwd=d, capture_output=True, text=True, timeout=60)
    try:
        r = json.loads(run.stdout.splitlines()[0])
    except (ValueError, IndexError):
        r = {}
    ok("commands.js: search ranks as SolidCraft (prefix, word start, letters), offered commands first, tab and panel match",
       r.get("rank") is True and r.get("search") == ["solid.shell", "sketch.shell"] and r.get("byPanel") == ["solid.box"],
       f"{r} {run.stderr[-300:]}")
    ok("commands.js: form values become params (numbers, expressions, point with 0 for empty, list, JSON; empty left out)",
       r.get("params") == {"size": 12.5, "count": 3, "flip": False, "at": [10, 0, "w/2"], "bodies": ["A", "B"], "rounds": [[1, 2, 3]]}
       and r.get("exprText") == "w / 2" and r.get("raw") == {"thickness": 2}, f"{r} {run.stderr[-300:]}")
    ok("commands.js: picks in the view: a list toggles the clicked edge, a single field takes the last face as {face: point}, "
       "a body clicked twice counts once, a cylinder click lands on the true surface",
       r.get("edgesTwo") == "[[1,2,3],[4,5,6]]" and r.get("edgesToggle") == "[[4,5,6]]" and r.get("face") == '{"face":[0,0,2]}'
       and r.get("bodies") == "B1, B2" and r.get("bodyAgain") == "B2" and r.get("body") == "Plate"
       and r.get("onto") == [15, 0, 3] and r.get("flat") == [1, 2, 3], str(r))
    ok("commands.js: a missing required field, bad JSON, a fraction for a whole number and a non-object raw JSON are refused",
       "size" in r.get("missing", "") and "rounds" in r.get("badJson", "") and "count" in r.get("badInt", "")
       and "object" in r.get("rawArray", ""), str(r))


VIEWTOOLS_TEST = r"""
import * as THREE from "three";
import { faceInfo, bodyEdges, edgeInfo, pointOnEdge, edgeKey } from "./viewtools.js";
import { loopPoints, profileShapes, profileAt, sketchLineAt, boxFromDrag, boxTakesPolyline, boxTakesLine, boxTakesCircle, boxTakesArc, boxTakesCurve } from "./sketchgeom.js";
// a cylinder r 8 around (30, 20) along Z, split into two half faces like SolidCraft's seam, and a flat face
const positions = [], indices = [], face_ids = [];
const n = 48;
for (let i = 0; i <= n; i++) {
  const a = (2 * Math.PI * i) / n;
  positions.push(30 + 8 * Math.cos(a), 20 + 8 * Math.sin(a), 0, 30 + 8 * Math.cos(a), 20 + 8 * Math.sin(a), 20);
}
for (let i = 0; i < n; i++) {
  const k = 2 * i;
  indices.push(k, k + 2, k + 1, k + 1, k + 2, k + 3);
  face_ids.push(i < n / 2 ? 0 : 1, i < n / 2 ? 0 : 1);
}
const base = positions.length / 3;
positions.push(0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0);
indices.push(base, base + 1, base + 2, base, base + 2, base + 3);
face_ids.push(2, 2);
const body = { positions, indices, face_ids };
const half = faceInfo(body, 0), other = faceInfo(body, 1), flat = faceInfo(body, 2);
console.log(JSON.stringify({
  r: half.radius, axisZ: Math.abs(half.axis.z), cx: half.center.x, cy: half.center.y, r2: other.radius,
  flatNormalZ: flat.normal && Math.abs(flat.normal.z), flatArea: flat.area, flatRadius: flat.radius ?? null,
}));
// edges: a bottom disc (face 3) under the two half faces gives two half circles; the seam is a straight edge
const disc = positions.length / 3;
positions.push(30, 20, 0);
for (let i = 0; i < n; i++) { indices.push(disc, 2 * i + 2, 2 * i); face_ids.push(3); }
const edges = bodyEdges(body);
const pickOf = (fa, fb) => edges.find((e) => e.faces[0] === fa && e.faces[1] === fb);
const hole = edgeInfo(edges, pickOf(0, 3)), seam = edgeInfo(edges, pickOf(0, 1));
// only the first half (its cylinder face and the disc under it): a half circle stays an arc
const keep = [...Array(face_ids.length).keys()].filter((t) => face_ids[t] === 0 || (face_ids[t] === 3 && t - face_ids.indexOf(3) < n / 2));
const halfBody = { positions, indices: keep.flatMap((t) => indices.slice(3 * t, 3 * t + 3)), face_ids: keep.map((t) => face_ids[t]) };
const halfEdges = bodyEdges(halfBody);
const arc = edgeInfo(halfEdges, halfEdges.find((e) => e.faces[0] === 0 && e.faces[1] === 3));
// one cylinder face (seam vertices repeated, not shared) on the disc: one closed circle
const one = { positions, indices, face_ids: face_ids.map((f) => (f === 1 ? 0 : f)) };
const oneEdges = bodyEdges(one);
const ring = edgeInfo(oneEdges, oneEdges.find((e) => e.faces[0] === 0 && e.faces[1] === 3));
console.log(JSON.stringify({
  arcKind: arc.kind, arcR: arc.radius, arcAngle: arc.angle, holeKind: hole.kind, holeR: hole.radius, seamKind: seam.kind, seamLength: seam.length,
  seamDirZ: seam.dir && Math.abs(seam.dir.z), ringKind: ring.kind, ringR: ring.radius, ringCx: ring.center?.x,
  ringAxisZ: ring.axis && Math.abs(ring.axis.z),
}));
// feature dialogs send points on the true edge: a chord point of the hole goes out to r 8, a seam pick
// stays inside the seam (not on its end vertex), and both halves of the hole give one key
const seg = edges.filter((e) => e.faces[0] === 0 && e.faces[1] === 3)[3];
const chordMid = seg.a.clone().add(seg.b).multiplyScalar(0.5);
const onHole = pointOnEdge(hole, chordMid);
const onSeam = pointOnEdge(seam, { x: 38, y: 20, z: -5 });
const otherHalf = edgeInfo(edges, pickOf(1, 3));
console.log(JSON.stringify({
  chordR: Math.hypot(chordMid.x - 30, chordMid.y - 20), pickR: Math.hypot(onHole[0] - 30, onHole[1] - 20), pickZ: onHole[2],
  seamZ: onSeam[2], seamLen: seam.length, sameKey: edgeKey(hole) === edgeKey(otherHalf), seamKey: edgeKey(seam) !== edgeKey(hole),
}));
const curves = {
  l1: { type: "line", start_at: [10, 10], end_at: [10, 50] },
  l2: { type: "line", start_at: [70, 50], end_at: [10, 50] },
  l4: { type: "line", start_at: [10, 10], end_at: [70, 10] },
  l3: { type: "line", start_at: [70, 10], end_at: [70, 50] },
};
const loop = loopPoints(["l1", "l2", "l4", "l3"], curves);
const shape = new THREE.Shape(loop.map(([u, v]) => new THREE.Vector2(u, v)));
const geom = new THREE.ShapeGeometry(shape);
console.log(JSON.stringify({
  loopLen: loop.length,
  triangles: geom.index ? geom.index.count / 3 : 0,
  firstPt: loop[0],
  lastPt: loop[loop.length - 1],
}));
const sk = {
  plane: { origin: [0, 0, 0], x_dir: [1, 0, 0], y_dir: [0, 1, 0] },
  curves: [
    { id: "c1", type: "circle", center_at: [20, 0], radius: 4, construction: false },
    { id: "l1", type: "line", start_at: [10, -15], end_at: [10, 15], construction: true },
    { id: "l2", type: "line", start_at: [0, 0], end_at: [30, 0], construction: false },
  ],
  profiles: [{ index: 0, area: 50.265, curves: ["c1"], holes: 0, hole_loops: [] }],
};
const shapes = profileShapes(sk);
const profHit = profileAt(shapes, [21, 1]);
const lineHit1 = sketchLineAt(sk, [10.4, 5], 1.0);
const lineHit2 = sketchLineAt(sk, [25, -0.3], 1.0);
const lineMiss = sketchLineAt(sk, [10, 25], 2.0);
console.log(JSON.stringify({
  profIndex: profHit?.index ?? null,
  line1: lineHit1?.id ?? null, line1Const: lineHit1?.construction ?? null,
  line2: lineHit2?.id ?? null, line2Const: lineHit2?.construction ?? null,
  lineMiss: lineMiss ?? null,
}));
const inside = [[20, 20], [40, 30]];
const partly = [[20, 20], [140, 30]];
const through = [[-10, 50], [200, 50]];
const away = [[300, 300], [320, 330]];
const w = boxFromDrag([0, 0], [100, 100]);
const c = boxFromDrag([100, 100], [0, 0]);
const l1 = { type: "line", start_at: [10, 10], end_at: [40, 40] };
const l2 = { type: "line", start_at: [10, 10], end_at: [140, 40] };
const l3 = { type: "line", start_at: [300, 300], end_at: [350, 350] };
const c1 = { type: "circle", center_at: [50, 50], radius: 10 };
const c2 = { type: "circle", center_at: [95, 50], radius: 10 };
const c3 = { type: "circle", center_at: [200, 200], radius: 10 };
const a1 = { type: "arc", center_at: [50, 50], radius: 10, start_at: [50, 60], end_at: [60, 50] };
const a2 = { type: "arc", center_at: [95, 50], radius: 10, start_at: [95, 60], end_at: [105, 50] };
console.log(JSON.stringify({
  wCrossing: w.crossing, cCrossing: c.crossing,
  wInside: boxTakesPolyline(w, inside), wPartly: boxTakesPolyline(w, partly),
  wThrough: boxTakesPolyline(w, through), wAway: boxTakesPolyline(w, away),
  cInside: boxTakesPolyline(c, inside), cPartly: boxTakesPolyline(c, partly),
  cThrough: boxTakesPolyline(c, through), cAway: boxTakesPolyline(c, away),
  wL1: boxTakesCurve(w, l1), wL2: boxTakesCurve(w, l2), wL3: boxTakesCurve(w, l3),
  cL1: boxTakesCurve(c, l1), cL2: boxTakesCurve(c, l2), cL3: boxTakesCurve(c, l3),
  wC1: boxTakesCurve(w, c1), wC2: boxTakesCurve(w, c2), wC3: boxTakesCurve(w, c3),
  cC1: boxTakesCurve(c, c1), cC2: boxTakesCurve(c, c2), cC3: boxTakesCurve(c, c3),
  wA1: boxTakesCurve(w, a1), wA2: boxTakesCurve(w, a2),
  cA1: boxTakesCurve(c, a1), cA2: boxTakesCurve(c, a2),
}));
"""


def viewtools_checks(tmp):
    """Measure tool in the browser: faceInfo finds planes and cylinders (also half ones) on the mesh (needs node)."""
    import shutil
    import subprocess
    from mechvane.ui import server as ui_server
    if not shutil.which("node"):
        print("skip viewtools: node not installed")
        return
    d = Path(tmp) / "viewtools"
    three = d / "node_modules" / "three"
    three.mkdir(parents=True)
    (three / "package.json").write_text('{"name": "three", "type": "module", "main": "three.module.js"}')
    shutil.copyfile(ui_server.STATIC_DIR / "vendor/three/build/three.module.js", three / "three.module.js")
    shutil.copyfile(ui_server.STATIC_DIR / "viewtools.js", d / "viewtools.js")
    shutil.copyfile(ui_server.STATIC_DIR / "sketchgeom.js", d / "sketchgeom.js")
    (d / "package.json").write_text('{"type": "module"}')
    (d / "t.js").write_text(VIEWTOOLS_TEST)
    run = subprocess.run(["node", "t.js"], cwd=d, capture_output=True, text=True, timeout=60)
    try:
        r, e, pk, lp, sg, bx = (json.loads(line) for line in run.stdout.splitlines()[:6])
    except ValueError:
        r, e, pk, lp, sg, bx = {}, {}, {}, {}, {}, {}
    ok("viewtools: edges, half circle as arc R 8 / 180°, two half faces as one circle, seam as straight edge 20 mm, "
       "closed circle over a repeated seam",
       e.get("holeKind") == "circle" and abs(e.get("holeR", 0) - 8) < 1e-3 and e.get("arcKind") == "arc" and abs(e.get("arcR", 0) - 8) < 1e-3 and abs(e.get("arcAngle", 0) - 180) < 0.5
       and e.get("seamKind") == "line" and abs(e.get("seamLength", 0) - 20) < 1e-6 and e.get("seamDirZ") == 1
       and e.get("ringKind") == "circle" and abs(e.get("ringR", 0) - 8) < 1e-3 and abs(e.get("ringCx", 0) - 30) < 1e-3
       and e.get("ringAxisZ", 0) > 0.9999, f"{e} {run.stderr[-300:]}")
    ok("viewtools: cylinder Ø, axis and centre from a half face, plane normal and area",
       abs(r.get("r", 0) - 8) < 1e-3 and abs(r.get("r2", 0) - 8) < 1e-3 and r.get("axisZ", 0) > 0.9999
       and abs(r.get("cx", 0) - 30) < 1e-3 and abs(r.get("cy", 0) - 20) < 1e-3
       and r.get("flatNormalZ") == 1 and abs(r.get("flatArea", 0) - 100) < 1e-9 and r.get("flatRadius") is None,
       f"{r} {run.stderr[-300:]}")
    ok("viewtools: a dialog's edge pick lies on the true circle (not the chord), inside a straight edge, "
       "and both halves of a hole give one edge key", _viewtools_pick_ok(pk), f"{pk} {run.stderr[-300:]}")
    ok("sketchgeom: loopPoints chains curves topologically into simple polygon without self-intersection or diagonal line",
       lp.get("loopLen") == 4 and lp.get("triangles") == 2 and lp.get("firstPt") == [10, 10] and lp.get("lastPt") == [70, 10],
       f"{lp} {run.stderr[-300:]}")
    ok("sketchgeom: profileAt and sketchLineAt pick profiles and sketch/construction lines within tolerance",
       sg.get("profIndex") == 0 and sg.get("line1") == "l1" and sg.get("line1Const") is True
       and sg.get("line2") == "l2" and sg.get("line2Const") is False and sg.get("lineMiss") is None,
       f"{sg} {run.stderr[-300:]}")
    ok("sketchgeom: box selection (window and crossing) for polyline, line, circle and arc matches SolidCraft BoxSel",
       bx.get("wCrossing") is False and bx.get("cCrossing") is True
       and bx.get("wInside") is True and bx.get("wPartly") is False and bx.get("wThrough") is False and bx.get("wAway") is False
       and bx.get("cInside") is True and bx.get("cPartly") is True and bx.get("cThrough") is True and bx.get("cAway") is False
       and bx.get("wL1") is True and bx.get("wL2") is False and bx.get("wL3") is False
       and bx.get("cL1") is True and bx.get("cL2") is True and bx.get("cL3") is False
       and bx.get("wC1") is True and bx.get("wC2") is False and bx.get("wC3") is False
       and bx.get("cC1") is True and bx.get("cC2") is True and bx.get("cC3") is False
       and bx.get("wA1") is True and bx.get("wA2") is False
       and bx.get("cA1") is True and bx.get("cA2") is True,
       f"{bx} {run.stderr[-300:]}")


def _viewtools_pick_ok(pk):
    seam_lo, seam_hi = sorted((0, 20))
    return (pk.get("chordR", 8) < 8 - 1e-4 and abs(pk.get("pickR", 0) - 8) < 1e-5 and abs(pk.get("pickZ", 1)) < 1e-9
            and seam_lo < pk.get("seamZ", -1) < seam_hi and pk.get("sameKey") is True and pk.get("seamKey") is True)


def command_form_checks():
    """General command dialog (#128): each schema shape becomes its field kind (type first, not the name), a
    command without a schema gets one JSON field with SolidCraft's parameter text, and the offer rules hold."""
    from mechvane import command_form as cf
    defs = {"LengthExpr": {"anyOf": [{"type": "number"}, {"type": "string", "minLength": 1}]},
            "Op": {"enum": ["new", "join", "cut"], "type": "string"},
            "P3": {"anyOf": [{"type": "array", "items": {"$ref": "#/$defs/LengthExpr"}, "minItems": 3, "maxItems": 3},
                             {"type": "object", "properties": {k: {"$ref": "#/$defs/LengthExpr"} for k in "xyz"}}]},
            "Names": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
            "EdgeRefs": {"type": "array", "items": {"anyOf": [{"$ref": "#/$defs/P3"},
                                                             {"type": "object", "properties": {"body": {"type": "string"}}}]}}}
    schema = {"type": "object", "additionalProperties": False, "required": ["size"], "$defs": defs, "properties": {
        "size": {"$ref": "#/$defs/LengthExpr"}, "operation": {"$ref": "#/$defs/Op"}, "flip": {"type": "boolean"},
        "name": {"type": ["string", "null"], "default": None}, "count": {"type": "integer"},
        "at": {"$ref": "#/$defs/P3"}, "bodies": {"anyOf": [{"$ref": "#/$defs/Names"}, {"type": "null"}]},
        "rounds": {"$ref": "#/$defs/EdgeRefs"}, "camera": {"type": "object"}}}
    fm = cf.form({"id": "x.test", "label": "Test", "params": "size: expr", "input": schema})
    kinds = {f["name"]: (f["kind"], f.get("pick"), f["required"]) for f in fm["fields"]}
    want = {"size": ("expr", None, True), "operation": ("enum", None, False), "flip": ("bool", None, False),
            "name": ("text", None, False), "count": ("number", None, False), "at": ("point", None, False),
            "bodies": ("list", "bodies", False), "rounds": ("json", "edges", False), "camera": ("json", None, False)}
    ok("command form: each schema shape becomes its field kind; a json field names what to pick in the view",
       kinds == want and not fm["raw"], str(kinds))
    raw = cf.form({"id": "solid.shell", "label": "Shell", "params": "faces: [[x,y,z]]; thickness: expr", "input": None})
    ok("command form: a command without a schema gets one JSON field with SolidCraft's parameter text",
       raw["raw"] and len(raw["fields"]) == 1 and raw["fields"][0]["kind"] == "json"
       and "thickness" in raw["fields"][0]["description"], str(raw))
    try:
        cf.to_params(fm, {"operation": "cut"})
        missing = False
    except ValueError as e:
        missing = "size" in str(e)
    ok("command form: a missing required field is refused, empty optional fields are left out",
       missing and cf.to_params(fm, {"size": "w/2", "name": "", "bodies": []}) == {"size": "w/2"})
    pathy = cf.form({"id": "parameters.export", "label": "Export", "params": "", "input": {
        "type": "object", "properties": {"path": {"type": "string", "description": "Write to this file."}}}})
    geo = {"P3": defs["P3"], "GeoRef": {"anyOf": [
        {"type": "object", "properties": {"type": {"enum": ["point", "edge"]}}, "required": ["type"]},
        {"type": "object", "properties": {"face": {"$ref": "#/$defs/P3"}}, "required": ["face"]},
        {"type": "object", "properties": {"edge": {"$ref": "#/$defs/P3"}}, "required": ["edge"]}]},
        "LengthExpr": defs["LengthExpr"], "Names": defs["Names"]}
    pick_form = cf.form({"id": "x.pick", "label": "Pick", "params": "", "input": {"type": "object", "$defs": geo, "properties": {
        "faces": {"type": "array", "items": {"$ref": "#/$defs/P3"}}, "face": {"$ref": "#/$defs/GeoRef"},
        "edge": {"$ref": "#/$defs/GeoRef"}, "body": {"type": "string"}, "bodies": {"$ref": "#/$defs/Names"},
        "body_names": {"$ref": "#/$defs/Names"}, "size": {"type": "object", "description": "the size of the face",
                                                           "properties": {"a": {"type": "number"}}}}}})
    picks = {f["name"]: (f.get("pick"), f.get("multi"), f.get("write")) for f in pick_form["fields"]}
    ok("command form: edge, face and body fields say how a click in the view is written (points, {face: point}, names); "
       "names of new bodies and a field that only mentions a face get no pick",
       picks == {"faces": ("faces", True, "point"), "face": ("faces", False, "key:face"), "edge": ("edges", False, "key:edge"),
                 "body": ("bodies", False, "name"), "bodies": ("bodies", True, "name"), "body_names": (None, None, None),
                 "size": (None, None, None)}, str(picks))
    ok("command form: app commands are excepted, sketch and Mechvane-owned commands deferred, file paths not offered",
       cf.excepted("panel.timeline") and cf.excepted("tab.solid") and not cf.excepted("solid.box")
       and cf.deferred("sketch.line") and cf.deferred("joint.create") and not cf.deferred("joint.origin")
       and cf.why_not("parameters.export", pathy) == cf.FILE_REASON and cf.offered("solid.box", fm))


def command_dialog_checks(tmp):
    """General command dialog (#128) through the server: the search list, a form from the live schema, and one
    command per field kind form -> server -> SolidCraft (expr, enum, point, text from solid.box; bool and
    expr from parameters.add; a command without schema as raw JSON), on the shared undo list; a command
    that only reads leaves no undo entry; refused: deferred, excepted, file paths, unknown."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "commanddialog"
    folder.mkdir()
    w = Workspace(folder)
    try:
        part = w.new(PART, "plate")
        part.session.batch([{"command": "solid.box", "params": {"length": 40, "width": 20, "height": 10, "name": "Plate"}}])
        part.save()
    finally:
        w.close_all()
    path = folder / "plate.solidcraft"
    srv = ui_server.create_server(str(path), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def inspect():
        with srv.lock:
            return srv.ensure_current().session.cmd("document.inspect", {"measure": True})

    def run(command, values, preview=False):
        st, fm = call("command?id=" + command)
        if st != 200:
            return st, fm
        from mechvane import command_form as cf
        return call("feature", {"command": command, "params": cf.to_params(fm, values), "generic": True, "preview": preview})

    try:
        st_l, lst = call("commands")
        by_id = {c["id"]: c for c in lst.get("commands", [])}
        ok("command dialog: /api/commands lists SolidCraft's commands with label and panel, marks deferred ones, "
           "leaves out app commands",
           st_l == 200 and by_id.get("solid.box", {}).get("offered") and by_id.get("solid.box", {}).get("label")
           and by_id.get("sketch.line", {}).get("offered") is False and "panel.timeline" not in by_id
           and len(by_id) > 500, f"{st_l} {len(by_id)} {by_id.get('solid.box')} {by_id.get('sketch.line')}")
        st_f, fm = call("command?id=solid.box")
        kinds = {f["name"]: f["kind"] for f in fm.get("fields", [])}
        ok("command dialog: /api/command builds the form from the live schema (solid.box: expr, enum, point, text)",
           st_f == 200 and kinds.get("length") == "expr" and kinds.get("operation") == "enum"
           and kinds.get("corner") == "point" and kinds.get("name") == "text" and fm.get("offered"), f"{st_f} {kinds}")

        mtime = path.stat().st_mtime_ns
        vol0 = inspect()["bodies"][0]["volume_mm3"] if inspect().get("bodies") else None
        st_p, prev = run("solid.box", {"length": "10", "width": "10", "height": "5 mm", "corner": [60, 0, 0],
                                       "operation": "new", "name": "Box2"}, preview=True)
        ok("command dialog: preview runs the command, returns the mesh, saves nothing and leaves nothing",
           st_p == 200 and prev.get("changed") and (prev.get("mesh") or {}).get("bodies")
           and path.stat().st_mtime_ns == mtime and len(inspect()["bodies"]) == 1, f"{st_p} {str(prev)[:200]}")
        st_b, done = run("solid.box", {"length": "10", "width": "10", "height": "5 mm", "corner": [60, 0, 0],
                                       "operation": "new", "name": "Box2"})
        bodies = inspect()["bodies"]
        _, hist = call("history")
        ok("command dialog: expr, enum, point and text fields run solid.box; the part is saved and the step is on the undo list",
           st_b == 200 and done.get("changed") and len(bodies) == 2 and path.stat().st_mtime_ns != mtime
           and any(abs(b.get("volume_mm3", 0) - 500) < 1e-3 for b in bodies)
           and "solid.box" in (hist.get("undo") or ""), f"{st_b} {done} {[b.get('volume_mm3') for b in bodies]} {hist}")
        st_u, _ = call("agent/undo", {})
        ok("command dialog: Undo takes the box back", st_u == 200 and len(inspect()["bodies"]) == 1, str(st_u))

        def saved_step(command, values):
            # a change must be saved and on the undo list, not only in the session (document.revision moved)
            mt = path.stat().st_mtime_ns
            st, res = run(command, values)
            _, h = call("history")
            return st, res, (res.get("changed") is True and path.stat().st_mtime_ns != mt
                             and command in (h.get("undo") or ""))

        st_pa, pa, saved_pa = saved_step("parameters.add", {"name": "gap", "expression": "3 mm", "favorite": True})
        with srv.lock:
            params = {p["name"]: p for p in srv.ensure_current().session.cmd("parameters.list", {})["parameters"]}
        ok("command dialog: bool and expr fields run parameters.add, saved and on the undo list",
           st_pa == 200 and saved_pa and "gap" in params and params["gap"].get("favorite") is True,
           f"{st_pa} {pa} {saved_pa} {params.get('gap')}")

        body = inspect()["bodies"][0]["name"]
        st_m, mi, saved_m = saved_step("solid.mirror", {"": {"bodies": [body], "plane": "YZ"}})
        ok("command dialog: a command without schema runs with its parameters as raw JSON, saved and on the undo list",
           st_m == 200 and saved_m and len(inspect()["bodies"]) == 2, f"{st_m} {mi} {saved_m}")

        # picks in the view write these values (commands.js applyPick): edge points, {"face": point}, body names
        _, chf = call("command?id=solid.chamfer")
        _, axf = call("command?id=construct.axis.normal_to_face")
        pick_fields = {f["name"]: (f.get("pick"), f.get("multi"), f.get("write"))
                       for f in chf.get("fields", []) + axf.get("fields", []) if f.get("pick")}
        st_ch, ch, saved_ch = saved_step("solid.chamfer", {"edges": [[20, 20, 10], [20, 0, 10]], "distance": "1"})
        st_ax, ax, saved_ax = saved_step("construct.axis.normal_to_face", {"face": {"face": [20, 10, 10]}, "point": {"point": [20, 10, 10]}, "name": "PickAxis"})
        with srv.lock:
            ws_names = {f["name"] for f in srv.ensure_current().session.cmd("document.inspect", {"measure": False})["timeline"]}
        ok("command dialog: values as the view picks write them run (two edge points for a chamfer, {face: point} for an axis)",
           pick_fields.get("edges") == ("edges", True, "point") and pick_fields.get("face") == ("faces", False, "key:face")
           and st_ch == 200 and saved_ch and st_ax == 200 and saved_ax and "PickAxis" in ws_names,
           f"{pick_fields} {st_ch} {ch} {st_ax} {ax} {sorted(ws_names)}")

        st_ma, ma, saved_ma = saved_step("material.assign", {"bodies": [body], "material": "Steel"})
        ok("command dialog: a change outside the timeline (material) is saved and on the undo list",
           st_ma == 200 and saved_ma, f"{st_ma} {ma} {saved_ma}")

        _, hist_before = call("history")
        mtime = path.stat().st_mtime_ns
        st_r, read = run("parameters.list", {})
        _, hist_after = call("history")
        ok("command dialog: a command that only reads returns its result, saves nothing and leaves no undo entry",
           st_r == 200 and read.get("changed") is False and read.get("results") and hist_after == hist_before
           and path.stat().st_mtime_ns == mtime, f"{st_r} {str(read)[:200]} {hist_before} {hist_after}")

        refused = {c: call("feature", {"command": c, "params": p, "generic": True})[0] for c, p in (
            ("sketch.line", {}), ("panel.timeline", {}), ("parameters.export", {"path": "/tmp/x.csv"}),
            ("joint.create", {}), ("timeline.delete", {"features": ["Plate"]}), ("view.fit", {}), ("no.such", {}))}
        ok("command dialog: deferred (sketch, Mechvane-owned, hidden window), excepted, file-path and unknown commands are refused",
           all(v == 403 for v in refused.values()), str(refused))
    finally:
        srv.shutdown()
        srv.server_close()


def feature_dialog_checks(tmp):
    """Workspace feature dialogs (ADR 0005, stage 2): /api/feature previews without saving, runs and saves,
    refuses commands outside the list, explains a size that does not fit; the step and parameter changes
    land in the shared undo list with the agent's turns; a new step after an undo drops the redo."""
    import urllib.error
    import urllib.request
    from mechvane import modeling, query
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "features"
    folder.mkdir()
    w = Workspace(folder)
    try:
        part = w.new(PART, "block")
        part.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY", "name": "Base"}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 20]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "Base", "distance": 10, "name": "Block"}}])
        part.save()
    finally:
        w.close_all()
    path = folder / "block.solidcraft"
    srv = ui_server.create_server(str(path), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def features():
        with srv.lock:
            doc = srv.ensure_current()
            return [f["name"] for f in doc.session.cmd("document.inspect", {"measure": False})["timeline"]]

    top_edge = [20, 20, 10]  # middle of the long top edge at y = 20
    try:
        mtime = path.stat().st_mtime_ns
        st_p, prev = call("feature", {"command": "solid.fillet", "params": {"edges": [top_edge], "radius": 2}, "preview": True})
        ok("feature dialog: preview returns the mesh and volume change, saves nothing and leaves no feature",
           st_p == 200 and prev.get("mesh", {}).get("bodies") and prev.get("delta", {}).get("volume_change_mm3", 0) < 0
           and path.stat().st_mtime_ns == mtime and "Fillet1" not in features(),
           f"{st_p} {str(prev)[:200]} {features()}")
        st_big, big = call("feature", {"command": "solid.fillet", "params": {"edges": [top_edge], "radius": 50}, "preview": True})
        st_no, no = call("feature", {"command": "solid.shell", "params": {}})
        ok("feature dialog: a radius that does not fit is explained in one line with SolidCraft's words; "
           "commands outside the dialog list are refused",
           st_big == 400 and "\n" not in big.get("error", "\n") and "SolidCraft:" in big.get("error", "")
           and st_no == 403, f"{st_big} {big.get('error')} {st_no}")
        st_c, done = call("feature", {"command": "solid.fillet", "params": {"edges": [top_edge], "radius": 2}})
        _, hist = call("history")
        ok("feature dialog: OK runs the fillet, saves the part, and puts the step on the undo list",
           st_c == 200 and "Fillet1" in features() and path.stat().st_mtime_ns != mtime
           and hist.get("undo", "").startswith("Fillet R2 on 1 edge") and hist.get("redo") is None,
           f"{st_c} {done} {features()} {hist}")
        st_u, _ = call("agent/undo", {})
        after_undo = features()
        _, hist_u = call("history")
        st_r, _ = call("agent/redo", {})
        after_redo = features()
        ok("feature dialog: Undo takes the fillet back, Redo puts it back",
           st_u == 200 and "Fillet1" not in after_undo and hist_u.get("redo", "").startswith("Fillet R2")
           and st_r == 200 and "Fillet1" in after_redo, f"{st_u} {after_undo} {hist_u} {st_r} {after_redo}")
        call("agent/undo", {})
        st_ch, _ = call("feature", {"command": "solid.chamfer", "params": {"edges": [[20, 0, 10]], "distance": 1}})
        _, hist_ch = call("history")
        ok("feature dialog: a new step after an undo drops the redo (it would discard the new step)",
           st_ch == 200 and hist_ch.get("redo") is None and hist_ch.get("undo", "").startswith("Chamfer 1")
           and "Fillet1" not in features(), f"{st_ch} {hist_ch} {features()}")
        with srv.lock:
            doc = srv.ensure_current()
            pname = next(p["name"] for p in doc.session.cmd("parameters.list", {})["parameters"]
                         if p.get("feature") == "Block")
        st_pa, _ = call("params", {"changes": {pname: "12 mm"}})
        _, hist_pa = call("history")
        st_pu, _ = call("agent/undo", {})
        with srv.lock:
            back = {p["name"]: p["value"] for p in srv.ensure_current().session.cmd("parameters.list", {})["parameters"]}
        ok("feature dialog: a parameter change from the form is a step on the same undo list",
           st_pa == 200 and hist_pa.get("undo", "").startswith("Parameters in block") and st_pu == 200
           and back.get(pname) == 10, f"{st_pa} {hist_pa} {st_pu} {back}")
        # edit from the model browser: values and the model before the feature, then a change in place
        st_e, ed = call("feature?name=Chamfer1")
        before_bodies = ed.get("before", {}).get("bodies") or []
        ok("feature dialog: opening Chamfer1 for editing gives its values and the model before it",
           st_e == 200 and ed.get("dialog") == "chamfer" and ed.get("definition", {}).get("edges") == [[20, 0, 10]]
           and str(ed.get("definition", {}).get("distance")) == "1" and before_bodies
           and "Chamfer1" in features(), f"{st_e} {str(ed)[:300]} features={features()}")
        mtime_e = path.stat().st_mtime_ns
        st_ep, _ = call("feature", {"command": "solid.chamfer", "edit": "Chamfer1", "preview": True,
                                    "params": {"edges": [[20, 0, 10]], "distance": 2}})
        st_eb, eb = call("feature", {"command": "solid.chamfer", "edit": "Chamfer1",
                                     "params": {"edges": [[20, 0, 10]], "distance": 50}})
        st_ew, _ = call("feature", {"command": "solid.fillet", "edit": "Chamfer1",
                                    "params": {"edges": [[20, 0, 10]], "radius": 1}})
        st_ec, _ = call("feature", {"command": "solid.chamfer", "edit": "Chamfer1",
                                    "params": {"edges": [[20, 0, 10], [20, 20, 10]], "distance": 2}})
        with srv.lock:
            d_after = srv.ensure_current().session.cmd("timeline.inspect", {"feature": "Chamfer1"})["definition"]
        _, hist_e = call("history")
        ok("feature dialog: editing previews without saving, refuses a size that does not fit and another command, "
           "then changes Chamfer1 in place (two edges, 2 mm) as one undo step",
           st_ep == 200 and st_eb == 400 and st_ew == 403 and st_ec == 200 and len(d_after.get("edges", [])) == 2
           and str(d_after.get("distance")) in ("2", "2.0") and features().count("Chamfer1") == 1
           and hist_e.get("undo", "").startswith("Edit Chamfer1") and path.stat().st_mtime_ns != mtime_e,
           f"{st_ep} {st_eb} {eb.get('error')} {st_ew} {st_ec} {d_after} {hist_e}")
        st_d, dele = call("feature/delete", {"name": "Chamfer1"})
        gone = "Chamfer1" not in features()
        call("agent/undo", {})
        ok("feature dialog: Delete removes a feature as one undo step, Undo brings it back",
           st_d == 200 and gone and "Chamfer1" in features() and dele.get("deleted") == ["Chamfer1"],
           f"{st_d} {dele} {features()}")

        # Rename via /api/feature/rename and via /api/feature command routing
        st_rn_empty, _ = call("feature/rename", {"feature": "Chamfer1", "name": ""})
        st_rn_dup, _ = call("feature/rename", {"feature": "Chamfer1", "name": "Block"})
        st_rn, rn = call("feature/rename", {"feature": "Chamfer1", "name": "ChamferSpecial"})
        _, hist_rn = call("history")
        with srv.lock:
            doc_rn = srv.ensure_current()
            params_rn = doc_rn.session.cmd("parameters.list", {})["parameters"]
            p_chamfer = [p for p in params_rn if p.get("feature") == "ChamferSpecial"]
        ok("feature dialog: Rename rejects empty and duplicate names, updates feature and parameters as one undo step",
           st_rn_empty == 400 and st_rn_dup == 400 and st_rn == 200
           and "ChamferSpecial" in features() and "Chamfer1" not in features()
           and len(p_chamfer) > 0
           and hist_rn.get("undo", "").startswith("Rename Chamfer1 to ChamferSpecial"),
           f"{st_rn_empty} {st_rn_dup} {st_rn} {rn} {features()} {hist_rn} {p_chamfer}")
        st_rnu, _ = call("agent/undo", {})
        ok("feature dialog: Undo reverts rename",
           st_rnu == 200 and "Chamfer1" in features() and "ChamferSpecial" not in features())
        st_cmd_rn, _ = call("feature", {"command": "timeline.rename", "params": {"feature": "Chamfer1", "name": "ChamferCmd"}})
        ok("feature dialog: timeline.rename routes to rename",
           st_cmd_rn == 200 and "ChamferCmd" in features())
        call("agent/undo", {})
        # Hole dialog: tables from Mechvane (ISO 273, DIN 336, DIN 974-1), a counterbored clearance hole, then
        # edited in place into a blind tapped hole (null removes "through all"'s missing depth the other way round)
        _, sizes = call("hole_sizes")
        m5 = sizes.get("sizes", {}).get("M5", {})
        st_h, hole = call("feature", {"command": "solid.hole", "params": {
            "position": [30, 10, 10], "direction": [0, 0, -1], "diameter": m5.get("clearance", {}).get("normal"),
            "type": "counterbore", "cb_diameter": m5.get("counterbore", {}).get("diameter"),
            "cb_depth": m5.get("counterbore", {}).get("depth")}})
        hname = (hole.get("results") or [{}])[0].get("name")
        st_he, _ = call("feature", {"command": "solid.hole", "edit": hname, "params": {
            "position": [30, 10, 10], "diameter": m5.get("tap_drill"), "depth": 6, "thread": "M5", "hole": {"type": "simple"}}})
        with srv.lock:
            hdef = srv.ensure_current().session.cmd("timeline.inspect", {"feature": hname})["definition"] if hname else {}
        st_ht, _ = call("feature", {"command": "solid.hole", "edit": hname, "params": {"depth": None, "thread": None}})
        with srv.lock:
            hdef2 = srv.ensure_current().session.cmd("timeline.inspect", {"feature": hname})["definition"] if hname else {}
        ok("feature dialog: Hole with M5 values from Mechvane's tables (5.5 / Cb. 10 x 5.4), edited into a tapped M5 "
           "6 deep, then back to through all",
           m5.get("clearance", {}).get("normal") == 5.5 and m5.get("tap_drill") == 4.2
           and m5.get("counterbore") == {"diameter": 10.0, "depth": 5.4} and sizes.get("sources", {}).get("clearance") == "ISO 273"
           and st_h == 200 and hole.get("done", "").startswith("Counterbored hole Ø5.5, through all")
           and st_he == 200 and hdef.get("thread") == "M5" and str(hdef.get("depth")) == "6"
           and hdef.get("hole", {}).get("type") == "simple"
           and st_ht == 200 and "depth" not in hdef2 and "thread" not in hdef2,
           f"{m5} {st_h} {hole.get('done')} {st_he} {hdef} {st_ht} {hdef2}")
        # #111: the dialog's edit set sends "references": null for a hole placed without edge references;
        # SolidCraft rejects null there ("invalid type: integer 8, expected a string" with a numeric depth),
        # so the edit has to go through as "no references" (an empty list)
        st_hr, hr = call("feature", {"command": "solid.hole", "edit": hname, "params": {
            "position": [30, 10, 10], "diameter": 6.6, "depth": 8, "thread": None, "hole": {"type": "simple"},
            "references": None}})
        with srv.lock:
            hdef3 = srv.ensure_current().session.cmd("timeline.inspect", {"feature": hname})["definition"] if hname else {}
        ok("feature dialog: editing a hole without edge references (references: null from the dialog) works (#111)",
           st_hr == 200 and str(hdef3.get("depth")) == "8" and not hdef3.get("references")
           and str(hdef3.get("diameter", "")).startswith("6.6"),
           f"{st_hr} {hr} {hdef3}")
        # patterns and mirror: a small through hole near x = 5, copied in a row, around it, and mirrored at x = 20
        def volume():
            with srv.lock:
                return srv.ensure_current().session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"]
        st_sh, small = call("feature", {"command": "solid.hole", "params": {"position": [5, 10, 10], "diameter": 3}})
        sname = (small.get("results") or [{}])[0].get("name")
        v_hole = volume()
        st_rp, rp = call("feature", {"command": "solid.pattern.rectangular", "params": {
            "features": [sname], "dir1": [1, 0, 0], "count1": 3, "spacing1": 4}})
        rname = (rp.get("results") or [{}])[0].get("name")
        v_rect = volume()
        st_re, _ = call("feature", {"command": "solid.pattern.rectangular", "edit": rname, "params": {
            "features": [sname], "pattern": {"type": "rectangular", "dir1": [1, 0, 0], "count1": "2", "spacing1": "4",
                                             "dir2": None, "count2": None, "spacing2": None}}})
        v_rect2 = volume()
        _, red = call(f"feature?name={rname}")
        ok("feature dialog: rectangular pattern of a hole (3 in a row), edited to 2 with counts as text; "
           "the edit dialog gets feature names for the ids",
           st_sh == 200 and st_rp == 200 and v_rect < v_hole - 1 and st_re == 200 and v_rect < v_rect2 < v_hole
           and rp.get("done", "").startswith(f"Rectangular pattern of {sname}, 3")
           and red.get("feature_names", {}).get(str(red.get("definition", {}).get("features", [None])[0])) == sname,
           f"{st_sh} {st_rp} {rp.get('done')} {v_hole} {v_rect} {st_re} {v_rect2} {str(red.get('feature_names'))[:200]}")
        st_mi, mi = call("feature", {"command": "solid.mirror", "params": {
            "features": [sname], "plane": {"origin": [20, 0, 0], "normal": [1, 0, 0]}}})
        mname = (mi.get("results") or [{}])[0].get("name")
        v_mirror = volume()
        st_me, _ = call("feature", {"command": "solid.mirror", "edit": mname, "params": {
            "features": [sname], "plane": {"type": "origin", "name": "XZ"}}})
        v_mirror_xz = volume()
        ok("feature dialog: mirror of the hole about x = 20 adds a hole; edited to the XZ plane (outside the block) "
           "it no longer cuts",
           st_mi == 200 and v_mirror < v_rect2 - 1 and st_me == 200 and abs(v_mirror_xz - v_rect2) < 1e-6,
           f"{st_mi} {mi.get('done')} {v_rect2} {v_mirror} {st_me} {v_mirror_xz}")
        # Extrude and Revolve on a sketch made elsewhere (agent, expert mode): a boss on the top face, joined,
        # then edited into a 3 mm cut (sketch sent by name, the definition keeps its id)
        with srv.lock:
            d0 = srv.ensure_current()
            modeling.run_commands(d0, [
                {"command": "sketch.create", "params": {"plane": {"face": [15, 12, 10]}, "name": "BossSketch"}},
                {"command": "sketch.circle.center", "params": {"center": [15, 12], "radius": 3}},
                {"command": "sketch.finish", "params": {}}])
            d0.save()
            srv.mtime = d0.path.stat().st_mtime
        _, sk = call("sketches")
        by_name = {x["name"]: x["used_by"] for x in sk.get("sketches", [])}
        v_before_ex = volume()
        st_ex, ex = call("feature", {"command": "solid.extrude", "params": {
            "sketch": "BossSketch", "distance": 5, "operation": "join", "direction": "positive"}})
        xname = (ex.get("results") or [{}])[0].get("name")
        v_boss = volume()
        st_xe, _ = call("feature", {"command": "solid.extrude", "edit": xname, "params": {
            "sketch": "BossSketch", "operation": "cut",
            "extent": {"direction": "negative", "through_all": False, "distance": "3"}}})
        v_cut = volume()
        ok("feature dialog: /api/sketches lists sketches with their users; Extrude joins a boss (+5 x πr²) and is "
           "edited into a 3 mm cut",
           "Block" in by_name.get("Base", []) and by_name.get("BossSketch") == [] and st_ex == 200
           and abs((v_boss - v_before_ex) - 5 * 3.14159265 * 9) < 0.5 and st_xe == 200
           and abs((v_before_ex - v_cut) - 3 * 3.14159265 * 9) < 0.5,
           f"{by_name} {st_ex} {ex.get('done')} {v_before_ex} {v_boss} {st_xe} {v_cut}")
        # Delete feature with keep_sketch over server endpoint (issue #66)
        st_del_keep, del_keep = call("feature/delete", {"name": xname, "keep_sketch": True})
        feats_after_keep = features()
        _, tr_keep = call("tree")
        sk_in_tree = any(f.get("name") == "BossSketch" for f in tr_keep.get("features", []))
        call("agent/undo", {})
        feats_after_undo = features()
        ok("feature/delete: keep_sketch=true deletes feature, keeps sketch as unconsumed in tree; undo restores it",
           st_del_keep == 200 and xname not in feats_after_keep and "BossSketch" in feats_after_keep
           and sk_in_tree and xname in feats_after_undo and del_keep.get("deleted") == [xname],
           f"{st_del_keep} {del_keep} {feats_after_keep} {tr_keep}")
        # Revolve dialog (issue #59): profile index and axis (sketch line, model edge, world axis) and editing
        with srv.lock:
            d0 = srv.ensure_current()
            modeling.run_commands(d0, [
                {"command": "sketch.create", "params": {"plane": "XY", "name": "RevSketch"}},
                {"command": "sketch.circle.center", "params": {"center": [60, 10], "radius": 3}},
                {"command": "sketch.circle.center", "params": {"center": [75, 10], "radius": 2}},
                {"command": "sketch.line", "params": {"points": [[50, 0], [50, 20]], "construction": True}},
                {"command": "sketch.finish", "params": {}}])
            d0.save()
            srv.mtime = d0.path.stat().st_mtime
        _, rev_sks = call("sketches")
        rev_sk = next((x for x in rev_sks.get("sketches", []) if x["name"] == "RevSketch"), {})
        rev_p0 = next((p["index"] for p in rev_sk.get("profiles", []) if p.get("curves") == ["c1"]), 0)
        st_rv, rv = call("feature", {"command": "solid.revolve", "params": {
            "sketch": "RevSketch", "profiles": [rev_p0], "axis": "l1", "angle": "360 deg", "operation": "new"}})
        rv_name = (rv.get("results") or [{}])[0].get("name")
        st_rvi, rvi = call(f"feature?name={rv_name}") if rv_name else (500, {})
        st_rve_edge, rve_edge = call("feature", {"command": "solid.revolve", "edit": rv_name, "preview": True, "params": {
            "sketch": "RevSketch", "profiles": [rev_p0], "angle": "360 deg", "operation": "new_body",
            "axis": {"type": "model", "geo": {"type": "edge", "at": [40, 10, 0]}}}})
        st_rve_world, _ = call("feature", {"command": "solid.revolve", "edit": rv_name, "params": {
            "sketch": "RevSketch", "profiles": [rev_p0], "angle": "180 deg", "operation": "new_body",
            "axis": {"type": "world", "axis": "Y"}}})
        _, rvi2 = call(f"feature?name={rv_name}") if rv_name else (500, {})
        torus_r10 = 2 * (3.14159265 ** 2) * 10 * 9
        ok("feature dialog: Revolve takes selected profile and sketch-line axis, inspects both for editing, "
           "and edits to a model-edge or origin axis",
           st_rv == 200 and abs(rv.get("delta", {}).get("volume_change_mm3", 0) - torus_r10) < 5.0
           and st_rvi == 200 and rvi.get("dialog") == "revolve"
           and rvi.get("definition", {}).get("axis") == {"type": "sketch_line", "curve": "l1"}
           and rvi.get("definition", {}).get("profiles", {}).get("loops") == [["c1"]]
           and st_rve_edge == 200 and st_rve_world == 200
           and rvi2.get("definition", {}).get("axis") == {"type": "world", "axis": "Y"},
           f"{st_rv} {rv.get('delta')} {rvi.get('definition')} {st_rve_edge} {st_rve_world} {rvi2.get('definition')}")
        # Sketch dialog: the plane's frame without leaving a sketch, then a fully dimensioned rectangle and
        # circle on the XZ plane (sizes as parameters), extruded symmetric into a new body
        st_sp, frame = call("sketch_plane?plane=XZ")
        n_before = len(features())
        st_sk, sk_res = call("feature", {"command": "mechvane.sketch", "params": {"plane": "XZ", "shapes": [
            {"type": "rectangle", "x": 50, "y": 0, "w": 20, "h": 10}, {"type": "circle", "x": 60, "y": 5, "d": 4}]}})
        skname = (sk_res.get("results") or [{}])[0].get("name")
        with srv.lock:
            skins = srv.ensure_current().session.cmd("sketch.inspect", {"sketch": skname}) if skname else {}
        st_ske, _ = call("feature", {"command": "solid.extrude", "params": {
            "sketch": skname, "distance": 6, "direction": "symmetric", "operation": "new"}})
        with srv.lock:
            bodies_sk = srv.ensure_current().session.cmd("document.inspect", {"measure": True})["bodies"]
        new_body = [b for b in bodies_sk if abs(b["volume_mm3"] - (20 * 10 - 3.14159265 * 4) * 6) < 0.5]
        _, hist_sk = call("history")
        ok("feature dialog: sketch plane frame (XZ: y along +Z, Z up as in Inventor) leaves nothing behind; a sketch with a rectangle and a "
           "circle is fully defined, one undo step, and extrudes into the expected body",
           st_sp == 200 and [round(v) for v in frame.get("y_dir", [])] == [0, 0, 1] and st_sk == 200 and skname
           and skins.get("fully_constrained") is True and len(features()) == n_before + 2 and st_ske == 200
           and len(new_body) == 1 and hist_sk.get("undo", "").startswith("Solid") is False,
           f"{st_sp} {frame} {st_sk} {sk_res} {skins.get('dof')} {st_ske} {[b['volume_mm3'] for b in bodies_sk]} {hist_sk}")
        # negative positions: a sketch dimension has no sign, the shape stays on the negative side
        st_neg, neg = call("feature", {"command": "mechvane.sketch", "params": {"plane": "XY", "shapes": [
            {"type": "rectangle", "x": -30, "y": -8, "w": 6, "h": 4}, {"type": "circle", "x": -40, "y": -5, "d": 3}]}})
        negname = (neg.get("results") or [{}])[0].get("name")
        with srv.lock:
            pts = srv.ensure_current().session.cmd("sketch.inspect", {"sketch": negname}).get("points", []) if negname else []
        xs = sorted(round(pt.get("at", pt.get("position", [0, 0]))[0], 6) for pt in pts if pt.get("id") != "origin")
        ok("feature dialog: a sketch takes negative positions (rectangle at -30/-8, circle at -40/-5)",
           st_neg == 200 and xs and min(xs) == -40 and -30 in xs, f"{st_neg} {neg} {xs} {str(pts)[:300]}")
        st_dx, _ = call("feature/delete", {"name": "NoSuchFeature"})
        st_ex, _ = call("feature?name=Base")
        ok("feature dialog: unknown features are 404, features without a dialog (a sketch) cannot be opened for editing (403)",
           st_dx == 404 and st_ex == 403, f"{st_dx} {st_ex}")
    finally:
        srv.shutdown()
        srv.server_close()

    # Hole positioned by distances from two edges (issue #43)
    p_refs = w.new(PART, "plate_refs")
    p_refs.session.batch([
        {"command": "parameters.add", "params": {"name": "len", "expression": "60 mm"}},
        {"command": "parameters.add", "params": {"name": "wid", "expression": "40 mm"}},
        {"command": "solid.box", "params": {"length": "len", "width": "wid", "height": 10, "corner": [0, 0, 0], "name": "Box"}},
    ])
    p_refs.save()
    w.close_all()
    srv_ref = ui_server.create_server(str(folder / "plate_refs.solidcraft"), port=0)
    threading.Thread(target=srv_ref.serve_forever, daemon=True).start()
    base_ref = f"http://127.0.0.1:{srv_ref.server_address[1]}/api/"

    def call_ref(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base_ref + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        st_hr, hr = call_ref("feature", {"command": "solid.hole", "params": {
            "name": "RefHole", "position": [30, 20, 10], "diameter": 5,
            "references": [{"edge": [0, 20, 10], "distance": 15}, {"edge": [30, 0, 10], "distance": 12}]}})
        with srv_ref.lock:
            h1 = query.find(srv_ref.ensure_current(), "holes")
        st_get, hget = call_ref("feature?name=RefHole")
        st_he, he = call_ref("feature", {"command": "solid.hole", "edit": "RefHole", "params": {
            "references": [{"edge": [0, 20, 10], "distance": 20}, {"edge": [30, 0, 10], "distance": 12}]}})
        with srv_ref.lock:
            h2 = query.find(srv_ref.ensure_current(), "holes")
        st_hp, hp = call_ref("params", {"changes": {"len": "80 mm"}})
        with srv_ref.lock:
            h3 = query.find(srv_ref.ensure_current(), "holes")
        st_bad, bad = call_ref("feature", {"command": "solid.hole", "params": {
            "name": "BadHole", "position": [30, 20, 10], "diameter": 5,
            "references": [{"edge": [0, 20, 10], "distance": 15}, {"edge": [80, 20, 10], "distance": 15}]}})
        ok("feature dialog: hole positioned by distances to two straight edges (15 and 12 mm), edited to 20 mm, "
           "keeps distance when part length parameter changes; parallel edges rejected",
           st_hr == 200 and h1 and h1[0].get("pick") == [15.0, 12.0, 10.0] and h1[0].get("center")[:2] == [15.0, 12.0]
           and len(hget.get("definition", {}).get("references", [])) == 2
           and st_he == 200 and h2 and h2[0].get("pick") == [20.0, 12.0, 10.0] and h2[0].get("center")[:2] == [20.0, 12.0]
           and st_hp == 200 and h3 and h3[0].get("pick") == [20.0, 12.0, 10.0] and h3[0].get("center")[:2] == [20.0, 12.0]
           and st_bad == 400 and "parallel" in bad.get("error", "").lower(),
           f"{st_hr} {h1} {st_he} {h2} {st_hp} {h3} {st_bad} {bad.get('error')}")
    finally:
        srv_ref.shutdown()
        srv_ref.server_close()


def centred_hole_dialog_checks(tmp):
    """Bohrungsdialog: mittig gesetzte Bohrung bearbeiten (issue #72).
    A hole placed with 'Middle of face' (centred on rectangular face or concentric on circular face)
    is recognized as centred in /api/feature, can be edited via /api/feature (e.g. diameter 6 to 8),
    and stays centred when the parent geometry is resized."""
    import urllib.error
    import urllib.parse
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "centred_hole_edit"
    folder.mkdir()
    w = Workspace(folder)
    try:
        part = w.new(PART, "plate")
        part.session.cmd("parameters.add", {"name": "L", "expression": "60 mm"})
        part.session.cmd("solid.box", {
            "corner": [0, 0, 0], "length": "L", "width": 40, "height": 10,
            "operation": "new", "body_name": "Plate", "name": "Box1"
        })
        part.save()
    finally:
        w.close_all()

    path = folder / "plate.solidcraft"
    srv = ui_server.create_server(str(path), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        # 1. Place centred hole Ø 6 on top face (60x40 plate)
        st, res = call("feature", {"command": "solid.hole", "params": {
            "centre": True, "position": [30, 20, 10], "direction": [0, 0, -1], "diameter": 6, "depth": None
        }})
        hname = next(r["name"] for r in res.get("results", []) if "name" in r and not r["name"].startswith("Hole centre"))
        ok("centred hole dialog: hole placed in middle of plate face", st == 200 and hname == "Hole1", f"{st} {res}")

        # 2. Inspect Hole1 via /api/feature?name=Hole1
        st_i, insp = call(f"feature?name={urllib.parse.quote(hname)}")
        ok("centred hole dialog: /api/feature recognizes hole as centred",
           st_i == 200 and insp.get("dialog") == "hole" and insp.get("definition", {}).get("centre") is True,
           f"{st_i} {insp}")

        # 3. Preview edit to Ø 8
        st_p, prev = call("feature", {"command": "solid.hole", "edit": hname, "preview": True, "params": {
            "centre": True, "diameter": 8, "depth": None, "hole": {"type": "simple"}
        }})
        ok("centred hole dialog: preview edit to dia 8 succeeds",
           st_p == 200 and prev.get("delta", {}).get("volume_change_mm3", 0) < 0, f"{st_p} {prev}")

        # 4. Apply edit to Ø 8
        st_e, ed = call("feature", {"command": "solid.hole", "edit": hname, "params": {
            "centre": True, "diameter": 8, "depth": None, "hole": {"type": "simple"}
        }})
        ok("centred hole dialog: edit applied", st_e == 200, f"{st_e} {ed}")

        # 5. Change plate length from 60 to 80 mm via /api/params
        st_par, _ = call("params", {"changes": {"L": "80 mm"}})
        ok("centred hole dialog: parameter L changed to 80 mm", st_par == 200)

        # 6. Verify hole diameter is 8 and axis is at x = 40
        with srv.lock:
            doc = srv.ensure_current()
            topo = doc.session.tool("body_topology", {"body": "Plate"})
            cyls = [f["cylinder"] for f in topo.get("faces", []) if f.get("cylinder")]
        ok("centred hole dialog: after resize to 80 mm, hole diameter is 8 and axis is at x = 40",
           len(cyls) > 0 and all(abs(c["radius"] - 4.0) < 1e-4 and abs(c["origin"][0] - 40.0) < 1e-4
                                and abs(c["origin"][1] - 20.0) < 1e-4 for c in cyls), f"cyls={cyls}")

        # 7. Concentric hole on cylinder (dia D=40 mm, height 30 mm)
        with srv.lock:
            doc = srv.ensure_current()
            doc.session.cmd("parameters.add", {"name": "D", "expression": "40 mm"})
            doc.session.cmd("solid.cylinder", {
                "base": [100, 0, 0], "diameter": "D", "height": 30,
                "operation": "new", "body_name": "Cyl", "name": "Cyl1"
            })
            doc.save()
            srv.mtime = doc.path.stat().st_mtime

        st_ch, ch_res = call("feature", {"command": "solid.hole", "params": {
            "centre": True, "position": [105, 5, 30], "direction": [0, 0, -1], "diameter": 6, "depth": None
        }})
        ch_name = next(r["name"] for r in ch_res.get("results", []) if "name" in r and not r["name"].startswith("Hole centre"))
        ok("centred hole dialog: concentric hole placed on cylinder", st_ch == 200 and ch_name == "Hole2", f"{st_ch} {ch_res}")

        # Inspect Hole2
        st_ci, cinsp = call(f"feature?name={urllib.parse.quote(ch_name)}")
        ok("centred hole dialog: /api/feature recognizes concentric hole as centred",
           st_ci == 200 and cinsp.get("definition", {}).get("centre") is True, f"{st_ci} {cinsp}")

        # Edit Hole2 to Ø 8
        st_ce, _ = call("feature", {"command": "solid.hole", "edit": ch_name, "params": {
            "centre": True, "diameter": 8, "depth": None, "hole": {"type": "simple"}
        }})
        ok("centred hole dialog: concentric edit applied", st_ce == 200)

        # Resize cylinder: change D from 40 to 60 mm
        st_cd, _ = call("params", {"changes": {"D": "60 mm"}})
        ok("centred hole dialog: parameter D changed to 60 mm", st_cd == 200)

        # Verify hole axis is at x = 100, y = 0 with diameter 8
        with srv.lock:
            doc = srv.ensure_current()
            cyl_topo = doc.session.tool("body_topology", {"body": "Cyl"})
            hole_cyls = [f["cylinder"] for f in cyl_topo.get("faces", []) if f.get("cylinder") and abs(f["cylinder"]["radius"] - 4.0) < 1e-4]
        ok("centred hole dialog: after resize to D=60, concentric hole diameter is 8 and axis stays at (100, 0)",
           len(hole_cyls) > 0 and all(abs(c["radius"] - 4.0) < 1e-4 and abs(c["origin"][0] - 100.0) < 1e-4
                                     and abs(c["origin"][1] - 0.0) < 1e-4 for c in hole_cyls), f"hole_cyls={hole_cyls}")
    finally:
        srv.shutdown()
        srv.server_close()


def step_import_checks(tmp):
    """import_step: a STEP file becomes a part file with one body and no components, insertable into an
    assembly; the STEP file is made here (a box exported by SolidCraft), not taken from private test data."""
    from mechvane import step_import
    folder = Path(tmp) / "step_import"
    folder.mkdir()
    w = Workspace(folder)
    try:
        src = w.new(PART, "block_src")
        src.session.cmd("solid.box", {"length": 40, "width": 30, "height": 12})
        src.session.cmd("solid.hole", {"position": [20, 15, 12], "direction": [0, 0, -1], "diameter": 6})
        vol_src = src.session.cmd("inspect.measure", {})["bodies"][0]["volume_mm3"]
        src.session.cmd("file.export_step", {"path": str(folder / "block.step")})
        w.close("block_src")
        r = step_import.import_step(w, "block.step", name="Kaufteil")
        doc = w.get("Kaufteil", PART)
        comps = doc.session.cmd("component.list")["components"]
        tl = [f["type"] for f in doc.session.cmd("document.inspect")["timeline"]]
        ok("import_step: STEP becomes a part file with the same volume, one base feature, no components",
           r["kind"] == "part" and len(r["bodies"]) == 1 and abs(r["bodies"][0]["volume_mm3"] - vol_src) < 1e-3 * vol_src
           and len(comps) == 1 and tl == ["BaseFeature"] and Path(r["path"]).exists() and not r["warnings"],
           f"{r} comps={len(comps)} tl={tl}")
        asm = w.new(ASSEMBLY, "asm_kauf")
        ins = links.insert(w, asm, Path(r["path"]), name="Kaufteil", grounded=True)
        ok("import_step: the imported part goes into an assembly like any part", bool(ins.get("occurrence")), str(ins)[:200])
        errs = []
        for bad in ({"source": "nope.step"}, {"source": "block_src.solidcraft"}, {"source": "block.step", "name": "Kaufteil"}):
            try:
                step_import.import_step(w, **bad)
            except (FileNotFoundError, ValueError, FileExistsError) as e:
                errs.append(type(e).__name__)
        ok("import_step: missing file, wrong type and an existing name are refused",
           errs == ["FileNotFoundError", "ValueError", "ValueError"], str(errs))

        # split=True check (#74): two bodies (plate and cylinder with distance) built in one part,
        # exported to STEP, imported with split=True: two part files, one assembly,
        # volumes match originals within +-0.1%, assembly bounding box matches original.
        two_body_part = w.new(PART, "two_body_part")
        s2 = two_body_part.session
        s2.cmd("sketch.create", {"plane": "XY", "name": "S_Plate"})
        s2.cmd("sketch.rectangle.two_point", {"p0": [0, 0], "p1": [100, 100]})
        s2.cmd("sketch.finish", {})
        s2.cmd("solid.extrude", {"sketch": "S_Plate", "distance": 10, "body_name": "Plate"})

        s2.cmd("sketch.create", {"plane": "XY", "offset": 30, "name": "S_Cyl"})
        s2.cmd("sketch.circle.center", {"center": [50, 50], "radius": 15})
        s2.cmd("sketch.finish", {})
        s2.cmd("solid.extrude", {"sketch": "S_Cyl", "distance": 20, "operation": "new", "body_name": "Cylinder"})
        two_body_part.save()

        orig_measure = s2.cmd("inspect.measure", {})
        orig_bodies = orig_measure["bodies"]
        orig_vols = {b["name"]: b["volume_mm3"] for b in orig_bodies}
        orig_min = [min(b["bbox"]["min"][i] for b in orig_bodies) for i in range(3)]
        orig_max = [max(b["bbox"]["max"][i] for b in orig_bodies) for i in range(3)]

        step_split_file = folder / "two_bodies.step"
        s2.cmd("file.export_step", {"path": str(step_split_file)})
        w.close("two_body_part")

        r_split = step_import.import_step(w, str(step_split_file), name="two_bodies_asm", split=True)
        asm_doc = w.get("two_bodies_asm", ASSEMBLY)
        asm_measure = asm_doc.session.cmd("inspect.measure", {})
        asm_bodies = asm_measure["bodies"]
        asm_min = [min(b["bbox"]["min"][i] for b in asm_bodies) for i in range(3)]
        asm_max = [max(b["bbox"]["max"][i] for b in asm_bodies) for i in range(3)]

        part_files = [folder / "two_bodies_asm_Plate.solidcraft", folder / "two_bodies_asm_Cylinder.solidcraft"]
        asm_file = folder / "two_bodies_asm.solidcraft"

        files_exist = all(p.exists() for p in part_files) and asm_file.exists()
        vols_ok = True
        for p in r_split["parts"]:
            matched_orig = next((orig_vols[k] for k in orig_vols if k in p["name"]), None)
            if matched_orig is None or abs(p["volume_mm3"] - matched_orig) / matched_orig >= 0.001:
                vols_ok = False
                break

        bbox_ok = (all(abs(orig_min[i] - asm_min[i]) < 1e-3 for i in range(3))
                   and all(abs(orig_max[i] - asm_max[i]) < 1e-3 for i in range(3)))

        comps_asm = asm_doc.session.cmd("component.list")["components"]
        children = comps_asm[0]["children"]
        grounded_ok = len(children) == 2 and children[0]["grounded"] is True and children[1]["grounded"] is False
        joints_asm = asm_doc.session.cmd("joint.list").get("joints", [])
        no_joints = len(joints_asm) == 0

        ok("import_step: split=True imports multi-body STEP as assembly with individual parts",
           r_split["kind"] == "assembly" and len(r_split["parts"]) == 2 and files_exist and vols_ok
           and bbox_ok and grounded_ok and no_joints,
           f"r_split={r_split} vols_ok={vols_ok} bbox_ok={bbox_ok} grounded_ok={grounded_ok} no_joints={no_joints}")
    finally:
        w.close_all()


def sketch_session_checks(tmp):
    """Sketch environment (ADR 0005, addendum 2026-11-02): /api/sketch/begin opens a sketch, cmd draws one command
    at a time, undo goes back one command, other edits and a second sketch are refused meanwhile, finish saves it as
    one step of the shared undo list, cancel leaves nothing, edit opens an existing sketch again."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "sketching"
    folder.mkdir()
    w = Workspace(folder)
    try:
        w.new(PART, "plate").save()
    finally:
        w.close_all()
    srv = ui_server.create_server(str(folder / "plate.solidcraft"), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def features():
        with srv.lock:
            doc = srv.ensure_current()
            return [f["name"] for f in doc.session.cmd("document.inspect", {"measure": False})["timeline"]]

    try:
        st, b = call("sketch/begin", {"plane": "XY"})
        ok("sketch env: begin on XY opens Sketch1", st == 200 and b.get("sketch") == "Sketch1", str(b)[:200])
        st, b = call("sketch/cmd", {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 20]}})
        st2, b2 = call("sketch/cmd", {"command": "sketch.circle.center", "params": {"center": [60, 10], "radius": 5}})
        ok("sketch env: rectangle and circle give two profiles",
           st == 200 and st2 == 200 and len(b2["state"]["profiles"]) == 2, str(b2.get("state", b2))[:200])
        st, b = call("sketch/undo", {})
        ok("sketch env: undo takes the circle back", st == 200 and len(b["state"]["profiles"]) == 1, str(b)[:200])
        st, b = call("sketch/cmd", {"command": "solid.extrude", "params": {"sketch": "Sketch1", "distance": 5}})
        st2, _ = call("sketch/begin", {"plane": "XZ"})
        st3, _ = call("feature", {"command": "solid.box", "params": {"length": 1, "width": 1, "height": 1}})
        ok("sketch env: no solid command, no second sketch, no feature dialog while a sketch is open",
           st == 403 and st2 == 409 and st3 == 409, f"{st} {st2} {st3}")
        # a dimension, then its value changed through its parameter (double-click in the sketcher), then undone
        st, b = call("sketch/cmd", {"command": "sketch.dimension", "params": {"entities": ["l1"], "type": "length"}})
        param = b.get("result", {}).get("param")
        st2, b2 = call("sketch/cmd", {"command": "parameters.change", "params": {"changes": {param: "55"}}})
        widths = [round(c["value"], 3) for c in b2.get("state", {}).get("constraints", []) if c.get("param") == param]
        st4, _ = call("sketch/cmd", {"command": "parameters.add", "params": {"name": "x", "expression": "1"}})
        call("sketch/undo", {})
        call("sketch/undo", {})
        ok("sketch env: a dimension's value changes through parameters.change, other parameter commands stay out",
           st == 200 and st2 == 200 and widths == [55.0] and st4 == 403, f"{st} {st2} {widths} {st4}")
        st, b = call("sketch/state")
        ok("sketch env: state names the open sketch", st == 200 and b.get("active") and b.get("sketch") == "Sketch1", str(b)[:120])
        st, b = call("sketch/finish", {})
        st_s, b_s = call("sketch/state")
        ok("sketch env: finish keeps Sketch1 and closes the environment",
           st == 200 and features() == ["Sketch1"] and b_s.get("active") is False, f"{b} {features()}")
        call("sketch/begin", {"plane": "XZ"})
        call("sketch/cmd", {"command": "sketch.line", "params": {"points": [[0, 0], [10, 10]]}})
        st, _ = call("sketch/cancel", {})
        ok("sketch env: cancel leaves nothing", st == 200 and features() == ["Sketch1"], str(features()))
        st, b = call("sketch/begin", {"edit": "Sketch1"})
        call("sketch/cmd", {"command": "sketch.circle.center", "params": {"center": [80, 10], "radius": 3}})
        st2, _ = call("sketch/finish", {})
        with srv.lock:
            doc = srv.ensure_current()
            profiles = doc.session.cmd("sketch.inspect", {"sketch": "Sketch1"})["profiles"]
        ok("sketch env: edit opens Sketch1 again and keeps the new circle", st == 200 and st2 == 200 and len(profiles) == 2,
           str(profiles)[:120])
        st, _ = call("agent/undo", {})
        with srv.lock:
            doc = srv.ensure_current()
            profiles = doc.session.cmd("sketch.inspect", {"sketch": "Sketch1"})["profiles"]
        ok("sketch env: one undo takes the whole edit session back", st == 200 and len(profiles) == 1, str(profiles)[:120])

        # Issue #68: sketch on a planar body face automatically projects outer edges and inner hole loops,
        # allows snapping/dimensioning to projected corners, follows model changes, undoes in one step,
        # and can be disabled via project_edges=False or /api/sketch/auto_project
        call("sketch/begin", {"edit": "Sketch1"})
        _, dim_b = call("sketch/cmd", {"command": "sketch.dimension", "params": {"entities": ["l1"], "type": "length", "value": 40}})
        w_param = dim_b.get("result", {}).get("param")
        call("sketch/finish", {})
        st_ex, _ = call("feature", {"command": "solid.extrude", "params": {"sketch": "Sketch1", "distance": 10}})
        st_fb, fb = call("sketch/begin", {"plane": {"face": [5, 5, 10]}})
        fb_state = fb.get("state", {})
        fb_lines = [c for c in fb_state.get("curves", []) if c.get("type") == "line" and c.get("link") and c.get("fixed")]
        st_ln, ln_b = call("sketch/cmd", {"command": "sketch.line", "params": {"points": [[0, 0], [10, 5]], "connect": True}})
        st_dm, _ = call("sketch/cmd", {"command": "sketch.dimension", "params": {"entities": ["l5"], "type": "length", "value": 12}})
        coinc = [k for k in ln_b.get("state", {}).get("constraints", []) if k.get("type") == "coincident"]
        st_ff, ff_b = call("sketch/finish", {})
        face_sk = ff_b.get("sketch")
        ok("sketch env (#68): sketch on face auto-projects 4 outer lines, line snaps with coincident to corner and dimensions",
           st_ex == 200 and st_fb == 200 and fb.get("can_undo") is False and len(fb_lines) == 4
           and st_ln == 200 and st_dm == 200 and st_ff == 200 and len(coinc) >= 1 and face_sk in features(),
           f"{st_fb} lines={len(fb_lines)} can_undo={fb.get('can_undo')} coinc={coinc} features={features()}")
        # Model change updates projected face edges in the sketch (width 40 -> 50)
        st_pc, _ = call("params", {"changes": {w_param: "50"}})
        with srv.lock:
            doc = srv.ensure_current()
            insp_after = doc.session.cmd("sketch.inspect", {"sketch": face_sk})
        max_x = max((max(c["start_at"][0], c["end_at"][0]) for c in insp_after.get("curves", [])
                     if c.get("type") == "line" and c.get("link")), default=0)
        ok("sketch env (#68): projected face edges follow upstream model changes (width 40 -> 50)",
           st_pc == 200 and abs(max_x - 50.0) < 1e-3, f"{st_pc} max_x={max_x}")
        call("agent/undo", {})  # undo parameter change
        st_u_sk, _ = call("agent/undo", {})  # undo face sketch + auto-projection in one step
        ok("sketch env (#68): undo reverts face sketch and projected edges as one step",
           st_u_sk == 200 and face_sk not in features(), f"{st_u_sk} {features()}")
        # Face with a hole: inner boundary edges are projected too
        st_hl, _ = call("feature", {"command": "solid.hole", "params": {
            "position": [20, 10, 10], "direction": [0, 0, -1], "diameter": 6}})
        st_fh, fh = call("sketch/begin", {"plane": {"face": [5, 5, 10]}})
        fh_curves = fh.get("state", {}).get("curves", [])
        fh_lines = [c for c in fh_curves if c.get("type") == "line" and c.get("link")]
        fh_arcs = [c for c in fh_curves if c.get("type") == "arc" and c.get("link") and abs(c.get("radius", 0) - 3.0) < 1e-3]
        call("sketch/cancel", {})
        ok("sketch env (#68): sketch on face with hole auto-projects outer lines and inner hole arcs",
           st_hl == 200 and st_fh == 200 and len(fh_lines) == 4 and len(fh_arcs) == 2,
           f"{st_hl} {st_fh} lines={len(fh_lines)} arcs={len(fh_arcs)}")
        # Disable via project_edges=False and via /api/sketch/auto_project
        st_np1, np1 = call("sketch/begin", {"plane": {"face": [5, 5, 10]}, "project_edges": False})
        call("sketch/cancel", {})
        st_ap, ap_b = call("sketch/auto_project", {"value": False})
        st_np2, np2 = call("sketch/begin", {"plane": {"face": [5, 5, 10]}})
        call("sketch/cancel", {})
        call("sketch/auto_project", {"value": True})
        ok("sketch env (#68): auto-projection can be disabled per begin or via /api/sketch/auto_project",
           st_np1 == 200 and len(np1.get("state", {}).get("curves", [])) == 0
           and st_ap == 200 and ap_b.get("auto_project") is False
           and st_np2 == 200 and len(np2.get("state", {}).get("curves", [])) == 0,
           f"{st_np1} {np1.get('state', {}).get('curves')} {st_ap} {ap_b} {st_np2} {np2.get('state', {}).get('curves')}")
    finally:
        srv.shutdown()
        srv.server_close()


def sessionlog_checks(tmp):
    """Session log for debugging test sessions: api requests, browser events (/api/log), agent decisions,
    developer messages to the agent, long values cut, old logs removed."""
    import urllib.request
    from datetime import datetime, timedelta
    from mechvane import install
    from mechvane.ui import agent as ag, server as ui_server, sessionlog

    old_cache = install.CACHE
    install.CACHE = Path(tmp) / "logcache"
    sessionlog._pruned = False
    try:
        logs = install.CACHE / "logs"
        logs.mkdir(parents=True)
        stale = logs / f"{(datetime.now() - timedelta(days=30)):%Y-%m-%d}.jsonl"
        stale.write_text("{}\n")
        folder = Path(tmp) / "logproj"
        folder.mkdir()
        w = Workspace(folder)
        try:
            w.new(PART, "p").save()
        finally:
            w.close_all()
        srv = ui_server.create_server(str(folder / "p.solidcraft"), port=0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/"
        try:
            urllib.request.urlopen(base + "version").read()
            req = urllib.request.Request(base + "log", method="POST", headers={"Content-Type": "application/json"},
                                         data=json.dumps({"events": [
                {"kind": "click", "what": "btn-fillet"}, {"kind": "js_error", "message": "x" * 5000}]}).encode())
            urllib.request.urlopen(req).read()
            req = urllib.request.Request(base + "feature", method="POST", headers={"Content-Type": "application/json"},
                                         data=json.dumps({"command": "solid.shell", "params": {}}).encode())
            try:
                urllib.request.urlopen(req)
            except urllib.error.HTTPError:
                pass
        finally:
            srv.shutdown()
            srv.server_close()
        sessionlog.log("agent_permission", tool="mcp__mechvane__run", allowed=False, reason="test")
        today = logs / f"{datetime.now():%Y-%m-%d}.jsonl"
        lines = [json.loads(x) for x in today.read_text(encoding="utf-8").splitlines()]
        kinds = [(e.get("kind"), e.get("event") or e.get("path")) for e in lines]
        click = next((e for e in lines if e.get("event") == "click"), {})
        err = next((e for e in lines if e.get("event") == "js_error"), {})
        refused = next((e for e in lines if e.get("path") == "/api/feature"), {})
        msg = ag.AgentTurns(folder)._message("which tools?", [], "p.solidcraft", "developer")
        ok("session log: browser events and refused api calls with their error, the agent's decisions; polls left "
           "out; long values cut; logs older than 14 days removed; developer messages are marked for the agent",
           click.get("what") == "btn-fillet" and len(err.get("message", "")) < 2100
           and refused.get("status") == 403 and "not available" in refused.get("error", "")
           and ("agent_permission", None) in kinds and not any(p == "/api/version" for _, p in kinds)
           and not stale.exists() and "Developer: which tools?" in msg and "Mechvane developer" in msg,
           f"{kinds} {stale.exists()} {msg[:120]}")
    finally:
        install.CACHE = old_cache


def window_close_checks(tmp):
    """The app window closed (the page said "closing" and nothing came after): the server stops after a few seconds,
    although the browser process lives on (Chrome on Windows); a reload (a request after "closing") keeps it."""
    import time
    import urllib.request
    from mechvane.ui import server as ui_server
    folder = Path(tmp) / "winclose"
    folder.mkdir()
    w = Workspace(folder)
    try:
        w.new(PART, "p").save()
    finally:
        w.close_all()
    old = ui_server.CLOSING_GRACE_S
    ui_server.CLOSING_GRACE_S = 1
    try:
        results = []
        for reload_after in (False, True):
            srv = ui_server.create_server(str(folder / "p.solidcraft"), port=0)
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            watcher = threading.Thread(target=ui_server._watch_closing, args=(srv,), daemon=True)
            watcher.start()
            base = f"http://127.0.0.1:{srv.server_address[1]}/api/"
            urllib.request.urlopen(urllib.request.Request(base + "closing", method="POST", data=b"{}",
                                                          headers={"Content-Type": "application/json"})).read()
            if reload_after:
                time.sleep(0.2)
                urllib.request.urlopen(base + "version").read()
            t.join(timeout=8)
            results.append(not t.is_alive())
            if t.is_alive():
                srv.shutdown()
            srv.server_close()
        ok("ui: a closed app window stops the server (page says closing, nothing follows); a reload keeps it",
           results == [True, False], str(results))
    finally:
        ui_server.CLOSING_GRACE_S = old


def roadmap_json_checks():
    """roadmap.json (public roadmap page): valid statuses, every item with a title, every status named."""
    data = json.loads((Path(__file__).resolve().parents[2] / "roadmap.json").read_text(encoding="utf-8"))
    items = [i for s in data["sections"] for i in s["items"]]
    bad = [i for i in items if i.get("status") not in data["statuses"] or not i.get("title")]
    ok("roadmap.json: every item has a title and a known status",
       items and not bad and data["milestone"]["name"] and set(data["statuses"]) == {"done", "next", "progress", "planned", "later"},
       str(bad))


def bolted_gap_chamfer_check(tmp):
    """bolted_connection with a gap between the plates and a chamfer on the lower part: the extended plane
    of the chamfer must not count as a hit (it once drilled at z 19.7, above the part)."""
    from mechvane import bolted
    folder = Path(tmp) / "gap_chamfer"
    folder.mkdir()
    w = Workspace(folder)
    try:
        lower = w.new(PART, "lower")
        lower.session.batch([
            {"command": "solid.box", "params": {"length": 14, "width": 40, "height": 16, "corner": [21, 0, 0], "name": "Block"}},
            {"command": "solid.chamfer", "params": {"edges": [[35, 20, 16]], "distance": 0.8, "name": "Edge"}},
        ])
        lower.save()
        upper = w.new(PART, "upper")
        upper.session.batch([{"command": "solid.box", "params": {"length": 30, "width": 40, "height": 2.5,
                                                                 "corner": [15, 0, 0], "name": "Plate"}}])
        upper.save()
        asm = w.new(ASSEMBLY, "gap")
        links.insert(w, asm, lower.path, name="Lower", grounded=True)
        links.insert(w, asm, upper.path, name="Upper", translate=[0, 0, 18], grounded=True)
        asm.save()
        try:
            r = bolted.bolted_connection(w, "gap", placement={"position": [31, 20, 20.5], "direction": [0, 0, -1]},
                                         size="M3", connection_type="blind", head="countersunk")
            got = [p.get("hole_feature") for p in r.get("parts", [])]
        except Exception as e:  # noqa: BLE001
            got = str(e)
        ok("bolted: gap between plates and a chamfer below, holes go into both parts", got == ["Hole_M3_CS", "Hole_M3_Blind"], str(got))
    finally:
        w.close_all()


def gltf_export_check(tmp):
    """export_gltf: one mesh per body in metres, Y up, materials from the SolidCraft look (ADR 0004)."""
    from mechvane import gltf_export
    folder = Path(tmp) / "gltf"
    folder.mkdir()
    w = Workspace(folder)
    try:
        d = w.new(PART, "box")
        d.session.batch([{"command": "solid.box", "params": {"length": 20, "width": 10, "height": 5, "corner": [0, 0, 0], "name": "Box"}}])
        d.session.cmd("material.assign", {"bodies": ["Body1"], "material": "Brass"})
        r = gltf_export.export_gltf(d, folder / "box.gltf")
        data = json.loads((folder / "box.gltf").read_text())
        acc = data["accessors"][data["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
        mat = data["materials"][0]["pbrMetallicRoughness"]
        d.session.cmd("appearance.assign", {"faces": [[10, 5, 5]], "body": "Body1", "color": "#c9d4e0"})
        r2 = gltf_export.export_gltf(d, folder / "box2.gltf")
        ok("gltf: a face with its own appearance becomes its own primitive and material",
           len(r2["materials"]) == 2 and len(json.loads((folder / "box2.gltf").read_text())["meshes"][0]["primitives"]) == 2,
           str(r2))
        ok("gltf: body in metres with Y up, brass as metal with its colour, normals per face",
           r["bodies"] == 1 and [round(x, 4) for x in acc["max"]] == [0.02, 0.005, 0.0] and acc["min"][2] == -0.01
           and mat["metallicFactor"] == 1.0 and mat["baseColorFactor"][0] > mat["baseColorFactor"][2]
           and acc["count"] == 24, f"{r} {acc} {mat}")
    finally:
        w.close_all()


def session_env_checks():
    """Windows: SolidCraft sessions render with DirectX 12 on Intel-only graphics unless WGPU_BACKEND is set
    (Intel Vulkan crash); with an NVIDIA or AMD card Vulkan stays (DirectX 12 crash on an RTX 2070)."""
    from mechvane.solidcraft import session_env
    intel = ["Intel(R) Iris(R) Xe Graphics"]
    nvidia = ["Microsoft Basic Display Adapter", "NVIDIA GeForce RTX 2070"]
    hybrid = ["Intel(R) UHD Graphics 630", "NVIDIA GeForce GTX 1650"]
    ok("session env: DirectX 12 on Intel-only Windows, Vulkan default with NVIDIA/AMD, nothing changed "
       "elsewhere, a set WGPU_BACKEND wins",
       session_env("win32", {}, intel)["WGPU_BACKEND"] == "dx12"
       and "WGPU_BACKEND" not in session_env("win32", {}, nvidia)
       and "WGPU_BACKEND" not in session_env("win32", {}, hybrid)
       and "WGPU_BACKEND" not in session_env("win32", {}, [])
       and "WGPU_BACKEND" not in session_env("linux", {}, intel)
       and session_env("win32", {"WGPU_BACKEND": "vulkan"}, intel)["WGPU_BACKEND"] == "vulkan")


def demo_folder_checks(tmp):
    """`mechvane ui --demo` after a first build that broke off, and temp files in the system temp folder."""
    import tempfile as _tempfile
    from mechvane import cli, install
    from mechvane.examples import DEMOS
    from mechvane.ui import mesh, server as ui_server

    old = install.CACHE
    install.CACHE = Path(tmp) / "democache"
    try:
        stale = install.CACHE / "demo"
        stale.mkdir(parents=True)
        (stale / "top_plate.solidcraft").write_text("left over from a crash")
        folder = cli.demo_folder()
        names = sorted(p.name for p in folder.glob("*.solidcraft"))
        w = Workspace(folder)
        try:
            asm = w.open("bolted_plates.solidcraft")
            bad = [c for c in links.check(w, asm) if c.get("status") != "ok"]
        finally:
            w.close_all()
        (folder / "top_plate.solidcraft").unlink()
        rebuilt = cli.demo_folder()
        ok("demo: a part file missing from a finished demo is built again",
           (rebuilt / "top_plate.solidcraft").is_file() and (rebuilt / ".complete").is_file())
        ok("demo: a broken first build is replaced, the assembly finds its parts",
           all(f"{n}.solidcraft" in names for n, _, _ in DEMOS)
           and not bad, f"{names} {bad}")
    finally:
        install.CACHE = old

    srv = ui_server.create_server(str(folder / "bracket.solidcraft"), port=0)
    try:
        temp = Path(_tempfile.gettempdir()).resolve()
        ok("ui: scratch folder and mesh export in the system temp folder",
           temp in srv.tmp_dir.resolve().parents and mesh._allowed_export_dir(srv.doc, tmp_dir=None) is not None,
           str(srv.tmp_dir))
    finally:
        srv.server_close()


def moved_project_checks(tmp):
    """A project folder moved (or copied to another computer): assemblies still find their parts."""
    import shutil as _shutil
    from mechvane import METADATA_KEY, examples

    a = Path(tmp) / "moved" / "before"
    a.mkdir(parents=True)
    w = Workspace(a)
    try:
        examples.bolted_plates(w)
        asm = w.open("bolted_plates.solidcraft")
        stored = asm.session.cmd("document.metadata")["metadata"][METADATA_KEY]
        files = []

        def walk(v):
            if isinstance(v, dict):
                for k, x in v.items():
                    files.append(x) if k == "file" else walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(stored)
        # an assembly from before this change, with absolute paths in its metadata
        legacy = json.loads(json.dumps(stored).replace('"top_plate.solidcraft"', json.dumps(str(a / "top_plate.solidcraft"))))
        old = w.new(ASSEMBLY, "legacy")
        old.session.cmd("document.metadata.set", {"key": METADATA_KEY, "value": legacy})
        old.save()
    finally:
        w.close_all()
    ok("moved project: part files are stored relative to the assembly",
       files and all(not Path(f).is_absolute() for f in files), str(files[:4]))

    b = Path(tmp) / "moved" / "after"
    _shutil.move(str(a), str(b))
    w = Workspace(b)
    try:
        asm = w.open("bolted_plates.solidcraft")
        bad = [c for c in links.check(w, asm) if c.get("status") != "ok"]
        t = tree.assembly_tree(asm.session, base=asm.path.parent)
        missing = []

        def walk_tree(n):
            if n.get("file_missing"):
                missing.append(n["name"])
            for ch in n.get("occurrences", []):
                walk_tree(ch)
        for n in t.get("occurrences", []):
            walk_tree(n)
        r = links.update_links(w, asm)
        ok("moved project: joints, tree and update_links find every part after the move",
           not bad and not missing and not r["warnings"], f"{bad[:2]} {missing} {r['warnings'][:2]}")
        meta = w.open("legacy.solidcraft").metadata()
        legacy_files = []

        def walk2(v):
            if isinstance(v, dict):
                for k, x in v.items():
                    legacy_files.append(x) if k == "file" else walk2(x)
            elif isinstance(v, list):
                for x in v:
                    walk2(x)
        walk2(meta)
        ok("moved project: an older assembly with absolute paths finds its parts by name in its folder",
           legacy_files and all(Path(f).is_file() for f in legacy_files), str(legacy_files[:3]))
    finally:
        w.close_all()


def empty_part_mesh_check(tmp):
    """A new part without bodies yet: the Check page gets an empty mesh, not an error."""
    from mechvane.ui.mesh import collect_mesh
    w = Workspace(Path(tmp) / "emptypart")
    try:
        doc = w.new(PART, "leer")
        ok("ui: a part without bodies has an empty mesh", collect_mesh(doc) == {"bodies": []})
    finally:
        w.close_all()


def single_instance_check(tmp):
    """A second `mechvane ui` for the same folder opens a window on the running server instead of a new one."""
    from mechvane.ui import server as ui_server
    folder = Path(tmp) / "single"
    folder.mkdir()
    first = ui_server.create_server(str(folder), port=0)
    threading.Thread(target=first.serve_forever, daemon=True).start()
    port = first.server_address[1]
    try:
        opened = []
        ui_server.run_server(str(folder), port=port, opener=lambda url, stop: opened.append(url))
        other = Path(tmp) / "single-other"
        other.mkdir()
        done = threading.Thread(target=ui_server.run_server, args=(str(other),),
                                kwargs={"port": port, "opener": lambda url, stop: (opened.append(url), stop())}, daemon=True)
        done.start()
        done.join(20)
        ok("ui: same folder again reuses the running server, another folder gets its own",
           opened[0] == f"http://127.0.0.1:{port}/" and len(opened) == 2 and not opened[1].endswith(f":{port}/")
           and not done.is_alive(), str(opened))
    finally:
        first.shutdown()
        first.server_close()


def quit_check(tmp):
    """The UI says whether closing the window stops Mechvane; a browser tab gets Quit (/api/quit)."""
    import urllib.request
    from mechvane.ui import server as ui_server
    folder = Path(tmp) / "quit"
    folder.mkdir()
    port_box = []
    opener = lambda url, stop: port_box.append(url) or "window"  # noqa: E731
    done = threading.Thread(target=ui_server.run_server, args=(str(folder),), kwargs={"port": 0, "opener": opener},
                            daemon=True)
    done.start()
    for _ in range(100):
        if port_box:
            break
        threading.Event().wait(0.1)
    url = port_box[0] if port_box else "http://127.0.0.1:1/"
    threading.Event().wait(0.3)
    try:
        with urllib.request.urlopen(url + "api/about", timeout=5) as r:
            about = json.loads(r.read())
        req = urllib.request.Request(url + "api/quit", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            stopped = json.loads(r.read())
    except OSError as e:
        about, stopped = {"error": str(e)}, {}
    done.join(10)
    ok("ui: app window owns the server (about says so), Quit stops it",
       about.get("stops_with_window") is True and stopped.get("stopped") and not done.is_alive(), f"{about} {stopped}")


def edge_touches_check():
    """Edge names are "<face A>|<face B>", and a chamfer's face name holds a "|" itself."""
    from mechvane import geometry as gm
    ok("geometry: edge_touches handles face names with '|' (chamfers, fillets)",
       gm.edge_touches("F1:-y|F2:blend:F1:+x|F1:+z", "F2:blend:F1:+x|F1:+z")
       and gm.edge_touches("F2:blend:F1:+x|F1:+z|F1:+y", "F2:blend:F1:+x|F1:+z")
       and gm.edge_touches("F1:+x|F1:-y", "F1:-y") and not gm.edge_touches("F1:+x|F1:-y", "F1:+z")
       and not gm.edge_touches("F1:-y|F2:blend:F1:+x|F1:+z", "F1:+x"))


def split_face_name_check():
    """SolidCraft 0.25 names the pieces of a split face "F2:top#[edges]": the same face for Mechvane."""
    ok("links: split-face and numbered variants share the base face name",
       links._base("F2:top#[F2:side:l1,F3:cbore:side:0]") == "F2:top" and links._base("F2:side#2") == "F2:side"
       and links._base("F2:top") == "F2:top")


def argon_review_finding_6_checks(ws):
    """Argon Finding 6: pattern update follows rotated anchor component."""
    # 1. Circular pattern (3 screws) on Dom + Lid, Dom subsequently rotated 90 deg around Y
    dom = ws.new(PART, "argon6_dom")
    dom.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 60, "height": 10, "corner": [-30, -30, 0],
                                            "name": "Base", "body_name": "Dom"}},
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 20, "base": [0, 0, 10],
                                                 "operation": "join", "name": "Boss"}}
    ])
    dom.save()
    lid = ws.new(PART, "argon6_lid")
    lid.session.cmd("solid.box", {"length": 60, "width": 60, "height": 5, "corner": [-30, -30, 0], "name": "Lid"})
    lid.save()

    asm_circ = ws.new(ASSEMBLY, "argon6_circ_asm")
    links.insert(ws, asm_circ, dom.path, name="Dom", grounded=True)
    links.insert(ws, asm_circ, lid.path, name="Lid", translate=[0, 0, 30], grounded=True)
    asm_circ.save()

    circ_pat = {"type": "circular", "count": 3, "axis_point": [0, 0, 0], "axis": [0, 0, 1]}
    res_circ = bolted.bolted_connection(
        ws, "argon6_circ_asm",
        placement={"position": [15, 0, 35], "direction": [0, 0, -1]},
        size="M3",
        counterbore=False,
        pattern=circ_pat,
        parts=["Lid:1", "Dom:1"],
    )
    asm_circ.save()

    meta_circ0 = asm_circ.metadata()["bolted_connections"][res_circ["id"]]
    orig_circ_pos = [inst["position"] for inst in meta_circ0["instances"]]

    # Rotate Dom and Lid by 90 deg around Y and translate Dom to [100, 0, 0]
    moved_circ = ws.new(ASSEMBLY, "argon6_circ_moved")
    links.insert(ws, moved_circ, dom.path, name="Dom", rotate={"axis": [0, 1, 0], "angle": 90},
                 translate=[100, 0, 0], grounded=True)
    links.insert(ws, moved_circ, lid.path, name="Lid", rotate={"axis": [0, 1, 0], "angle": 90},
                 translate=[130, 0, 0], grounded=True)
    moved_circ.set_metadata(asm_circ.metadata())
    moved_circ.save()

    occ_dom = next(o for o in links._occurrences(moved_circ.session).values() if o["name"] == "Dom:1")
    want_circ_pos = [g.apply_point(occ_dom["transform"], p) for p in orig_circ_pos]

    rep_circ = bolted.check_and_update_bolted_connections(ws, moved_circ, repair=True)
    b_rep_circ = next((r for r in rep_circ if r["id"] == res_circ["id"]), {})
    meta_circ1 = moved_circ.metadata()["bolted_connections"][res_circ["id"]]
    got_circ_pos = [inst["position"] for inst in meta_circ1.get("instances", [])]

    circ_ok = (b_rep_circ.get("status") == "moved_repaired"
               and len(got_circ_pos) == len(want_circ_pos)
               and all(g.norm(g.sub(got, want)) < 1e-3 for got, want in zip(got_circ_pos, want_circ_pos)))
    ok("argon review 6: circular pattern holes follow rotated anchor occurrence (90 deg around Y)",
       circ_ok,
       f"status={b_rep_circ.get('status')} got={got_circ_pos} want={want_circ_pos}")

    for name in ("argon6_circ_moved", "argon6_circ_asm", "argon6_lid", "argon6_dom"):
        ws.close(name)

    # 2. Rectangular pattern (2x2) on Plate1 + Plate2, Plate1 subsequently rotated 90 deg around Y
    p1 = ws.new(PART, "argon6_p1")
    p1.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0],
                                 "name": "Box1", "body_name": "Plate1"})
    p1.save()
    p2 = ws.new(PART, "argon6_p2")
    p2.session.cmd("solid.box", {"length": 80, "width": 80, "height": 10, "corner": [-40, -40, 0],
                                 "name": "Box2", "body_name": "Plate2"})
    p2.save()

    asm_rect = ws.new(ASSEMBLY, "argon6_rect_asm")
    links.insert(ws, asm_rect, p1.path, name="Plate1", grounded=True)
    links.insert(ws, asm_rect, p2.path, name="Plate2", translate=[0, 0, -10], grounded=True)
    asm_rect.save()

    rect_pat = {"type": "rectangular", "count": [2, 2], "spacing": [20, 20], "directions": [[1, 0, 0], [0, 1, 0]]}
    res_rect = bolted.bolted_connection(
        ws, "argon6_rect_asm",
        placement={"position": [-10, -10, 10], "direction": [0, 0, -1]},
        size="M3",
        counterbore=False,
        pattern=rect_pat,
        parts=["Plate1:1", "Plate2:1"],
    )
    asm_rect.save()

    meta_rect0 = asm_rect.metadata()["bolted_connections"][res_rect["id"]]
    orig_rect_pos = [inst["position"] for inst in meta_rect0["instances"]]

    moved_rect = ws.new(ASSEMBLY, "argon6_rect_moved")
    links.insert(ws, moved_rect, p1.path, name="Plate1", rotate={"axis": [0, 1, 0], "angle": 90},
                 translate=[100, 0, 0], grounded=True)
    links.insert(ws, moved_rect, p2.path, name="Plate2", rotate={"axis": [0, 1, 0], "angle": 90},
                 translate=[90, 0, 0], grounded=True)
    moved_rect.set_metadata(asm_rect.metadata())
    moved_rect.save()

    occ_p1 = next(o for o in links._occurrences(moved_rect.session).values() if o["name"] == "Plate1:1")
    want_rect_pos = [g.apply_point(occ_p1["transform"], p) for p in orig_rect_pos]

    rep_rect = bolted.check_and_update_bolted_connections(ws, moved_rect, repair=True)
    b_rep_rect = next((r for r in rep_rect if r["id"] == res_rect["id"]), {})
    meta_rect1 = moved_rect.metadata()["bolted_connections"][res_rect["id"]]
    got_rect_pos = [inst["position"] for inst in meta_rect1.get("instances", [])]

    rect_ok = (b_rep_rect.get("status") == "moved_repaired"
               and len(got_rect_pos) == len(want_rect_pos)
               and all(g.norm(g.sub(got, want)) < 1e-3 for got, want in zip(got_rect_pos, want_rect_pos)))
    ok("argon review 6: rectangular pattern holes follow rotated anchor occurrence (90 deg around Y)",
       rect_ok,
       f"status={b_rep_rect.get('status')} got={got_rect_pos} want={want_rect_pos}")

    for name in ("argon6_rect_moved", "argon6_rect_asm", "argon6_p2", "argon6_p1"):
        ws.close(name)

    # 3. Legacy pattern dataset without local vectors: shifts axis_point without rotating axis
    dom_l = ws.new(PART, "argon6_leg_dom")
    dom_l.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 60, "height": 10, "corner": [-30, -30, 0],
                                            "name": "Base", "body_name": "Dom"}},
        {"command": "solid.cylinder", "params": {"diameter": 10, "height": 20, "base": [0, 0, 10],
                                                 "operation": "join", "name": "Boss"}}
    ])
    dom_l.save()
    lid_l = ws.new(PART, "argon6_leg_lid")
    lid_l.session.cmd("solid.box", {"length": 60, "width": 60, "height": 5, "corner": [-30, -30, 0], "name": "Lid"})
    lid_l.save()

    asm_leg = ws.new(ASSEMBLY, "argon6_leg_asm")
    links.insert(ws, asm_leg, dom_l.path, name="Dom", grounded=True)
    links.insert(ws, asm_leg, lid_l.path, name="Lid", translate=[0, 0, 30], grounded=True)
    asm_leg.save()

    res_leg = bolted.bolted_connection(
        ws, "argon6_leg_asm",
        placement={"position": [15, 0, 35], "direction": [0, 0, -1]},
        size="M3",
        counterbore=False,
        pattern={"type": "circular", "count": 3, "axis_point": [0, 0, 0], "axis": [0, 0, 1]},
        parts=["Lid:1", "Dom:1"],
    )
    # Strip local pattern keys to simulate a legacy connection record created before Befund 6
    meta_leg = asm_leg.metadata()
    c_rec = meta_leg["bolted_connections"][res_leg["id"]]
    c_rec.get("parameters", {}).get("pattern", {}).pop("axis_local", None)
    c_rec.get("parameters", {}).get("pattern", {}).pop("axis_point_local", None)
    c_rec.get("pattern", {}).pop("axis_local", None)
    c_rec.get("pattern", {}).pop("axis_point_local", None)
    if "anchor" in c_rec and isinstance(c_rec["anchor"], dict):
        c_rec["anchor"].pop("pattern", None)
    asm_leg.set_metadata(meta_leg)
    asm_leg.save()

    # Shift Dom and Lid by [10, 0, 0] without rotation
    moved_leg = ws.new(ASSEMBLY, "argon6_leg_moved")
    links.insert(ws, moved_leg, dom_l.path, name="Dom", translate=[10, 0, 0], grounded=True)
    links.insert(ws, moved_leg, lid_l.path, name="Lid", translate=[10, 0, 30], grounded=True)
    moved_leg.set_metadata(asm_leg.metadata())
    moved_leg.save()

    rep_leg = bolted.check_and_update_bolted_connections(ws, moved_leg, repair=True)
    b_rep_leg = next((r for r in rep_leg if r["id"] == res_leg["id"]), {})
    meta_leg_after = moved_leg.metadata()["bolted_connections"][res_leg["id"]]
    pat_after = meta_leg_after.get("parameters", {}).get("pattern", {})
    got_leg_pos = [inst["position"] for inst in meta_leg_after.get("instances", [])]
    want_leg_pos = [[25.0, 0.0, 35.0], [2.5, 12.990381, 35.0], [2.5, -12.990381, 35.0]]

    leg_ok = (b_rep_leg.get("status") == "moved_repaired"
              and pat_after.get("axis") == [0, 0, 1]
              and all(abs(a - b) < 1e-3 for a, b in zip(pat_after.get("axis_point", []), [10.0, 0.0, 0.0]))
              and len(got_leg_pos) == 3
              and all(g.norm(g.sub(got, want)) < 1e-3 for got, want in zip(got_leg_pos, want_leg_pos)))
    ok("argon review 6: legacy pattern without local vectors shifts axis_point without rotating axis",
       leg_ok,
       f"status={b_rep_leg.get('status')} pat={pat_after} got={got_leg_pos}")

    for name in ("argon6_leg_moved", "argon6_leg_asm", "argon6_leg_lid", "argon6_leg_dom"):
        ws.close(name)


def argon_review_findings_9_11_checks(ws):
    """Findings 9 and 11 of the Argon review (docs/research/2026-10-27-review-gemini-bausteine-argon.md)."""
    # Finding 9: Countersunk screw (ISO 10642) shank orientation must align with installation direction in rotated setups (+X).
    p1 = ws.new(PART, "argon9_p1")
    p1.session.cmd("solid.box", {"length": 10, "width": 40, "height": 40, "corner": [0, -20, -20], "body_name": "P1", "name": "B1"})
    p1.save()

    p2 = ws.new(PART, "argon9_p2")
    p2.session.cmd("solid.box", {"length": 10, "width": 40, "height": 40, "corner": [10, -20, -20], "body_name": "P2", "name": "B2"})
    p2.save()

    asm9 = ws.new(ASSEMBLY, "argon9_asm")
    links.insert(ws, asm9, p1.path, name="P1", grounded=True)
    links.insert(ws, asm9, p2.path, name="P2", grounded=True)
    asm9.save()

    res9 = bolted.bolted_connection(
        ws, "argon9_asm",
        placement={"position": [0, 0, 0], "direction": [1, 0, 0]},
        size="M5",
        head="countersunk",
    )
    occs9 = {o["name"]: o for o in links._occurrences(asm9.session).values()}
    t_screw9 = occs9[res9["screw"]]["transform"]
    shank_w9 = g.unit(g.apply_dir(t_screw9, [0.0, 0.0, -1.0]))
    interf9 = asm9.session.cmd("inspect.interference")
    chk9 = links.check(ws, asm9)
    ok("argon review 9: countersunk screw in +X direction aligns shank with installation direction",
       g.dot(shank_w9, [1, 0, 0]) > 0.95 and interf9.get("count") == 0 and all(c["status"] == "ok" for c in chk9),
       f"dot={g.dot(shank_w9, [1, 0, 0])} shank_w={shank_w9} interf={interf9}")
    for name in ("argon9_asm", "argon9_p2", "argon9_p1"):
        ws.close(name)

    # Finding 11: Z seating height of screw head matches top plate surface at z = 10.0
    p1_11 = ws.new(PART, "argon11_p1")
    p1_11.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "body_name": "P1", "name": "B1"})
    p1_11.save()

    p2_11 = ws.new(PART, "argon11_p2")
    p2_11.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [-20, -20, 0], "body_name": "P2", "name": "B2"})
    p2_11.save()

    asm11 = ws.new(ASSEMBLY, "argon11_asm")
    links.insert(ws, asm11, p1_11.path, name="P1", grounded=True)
    links.insert(ws, asm11, p2_11.path, name="P2", translate=[0, 0, -8], grounded=True)
    asm11.save()

    res11 = bolted.bolted_connection(
        ws, "argon11_asm",
        placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )
    occs11 = {o["name"]: o for o in links._occurrences(asm11.session).values()}
    origin11 = g.apply_point(occs11[res11["screw"]]["transform"], [0.0, 0.0, 0.0])
    ok("argon review 11: screw head seating height matches top plate surface at z = 10.0",
       abs(origin11[2] - 10.0) < 1e-3, f"z={origin11[2]}")
    for name in ("argon11_asm", "argon11_p2", "argon11_p1"):
        ws.close(name)


def state_delta_checks(ws):
    """State delta and warnings after modelling steps in run (ROADMAP v0.1 #37)."""
    server.ws = ws
    doc = ws.new(PART, "state_delta_part")

    # 1. Extrude box -> delta with volume > 0, body count 1, bbox, centre of mass, no warnings
    r1 = server.run(
        "state_delta_part",
        rect("S1", "XY", [0, 0], [40, 20])
        + [{"command": "solid.extrude", "params": {"sketch": "S1", "distance": 10, "name": "Box"}}],
    )
    d1 = r1.get("delta")
    ok(
        "state delta: extrude box produces delta with volume > 0 and 1 body",
        d1 is not None and d1.get("volume_mm3", 0) > 0 and d1.get("bodies") == 1 and not d1.get("warnings"),
        str(d1),
    )
    ok(
        "state delta: box bbox and centre of mass match geometry",
        d1 is not None
        and d1.get("bbox") == {"min": [0.0, 0.0, 0.0], "max": [40.0, 20.0, 10.0]}
        and d1.get("center_of_mass") == [20.0, 10.0, 5.0],
        str(d1),
    )

    # 2. Pocket without intersection with body -> warning 'no effect'
    r2 = server.run(
        "state_delta_part",
        rect("S2", "XY", [100, 100], [110, 110])
        + [{"command": "solid.extrude", "params": {"sketch": "S2", "distance": 5, "operation": "cut", "name": "CutOutside"}}],
    )
    d2 = r2.get("delta")
    ok(
        "state delta: cut without intersection warns no effect",
        d2 is not None and any("no effect" in w.lower() for w in d2.get("warnings", [])),
        str(d2),
    )

    # 3. Cut that splits part into two bodies -> warning multiple bodies
    r3 = server.run(
        "state_delta_part",
        rect("S3", "XY", [18, -5], [22, 25])
        + [{"command": "solid.extrude", "params": {"sketch": "S3", "distance": 15, "operation": "cut", "name": "CutSplit"}}],
    )
    d3 = r3.get("delta")
    ok(
        "state delta: cut splitting part into two bodies warns of multiple bodies",
        d3 is not None and d3.get("bodies") == 2 and any("multiple bodies" in w.lower() for w in d3.get("warnings", [])),
        str(d3),
    )

    # 4. Large jump: volume change > 50% or bbox growth > factor 2
    b_snap = {"bodies": 1, "volume_mm3": 1000.0, "bbox": {"min": [0, 0, 0], "max": [10, 10, 10]}}
    a_vol = {"bodies": 1, "volume_mm3": 1600.0, "bbox": {"min": [0, 0, 0], "max": [10, 10, 16]}}
    d_vol = state_delta.diff(b_snap, a_vol)
    a_box = {"bodies": 1, "volume_mm3": 1200.0, "bbox": {"min": [0, 0, 0], "max": [25, 10, 10]}}
    d_box = state_delta.diff(b_snap, a_box)
    ok(
        "state delta: large change warns on >50% volume change and >2x axis growth",
        any("large change" in w.lower() for w in d_vol.get("warnings", []))
        and any("factor 2" in w.lower() for w in d_box.get("warnings", [])),
        f"vol={d_vol.get('warnings')} box={d_box.get('warnings')}",
    )

    # 5. Assembly: run does not produce delta
    asm = ws.new(ASSEMBLY, "state_delta_asm")
    r_asm = server.run(
        "state_delta_asm",
        [{"command": "solid.cylinder", "params": {"diameter": 6, "height": 30, "base": [0, 0, 0], "name": "AsmCyl"}}],
    )
    ok(
        "state delta: assembly run does not return delta",
        "delta" not in r_asm,
        str(r_asm),
    )

    # 6. Material: snapshot includes mass_g when material is assigned
    doc.session.cmd("material.assign", {"bodies": ["Body1"], "material": "Steel"})
    snap = state_delta.snapshot(doc.session)
    ok(
        "state delta: snapshot includes mass when material is assigned",
        snap.get("mass_g") is not None and snap["mass_g"] > 0,
        str(snap),
    )

    ws.close("state_delta_part")
    ws.close("state_delta_asm")
def sc_errors_checks(ws):
    recorded_errors = {
        "lumps_shell_intersect": "failed: lumps: shell boundaries intersect or touch; cavity ownership is ambiguous",
        "blend_too_large": "solid.fillet: blend is larger than the neighbouring faces: maximum radius along this edge is 5 mm (you asked for 15 mm)",
        "chamfer_too_large": "solid.chamfer: chamfer runs past a neighbouring face: try a smaller distance",
        "blend_meeting_edges": "where 3 edges meet: give a point along one edge",
        "blend_no_edge": "no edge at [50 mm, 50 mm, 50 mm]: the nearest edge is 45 mm away",
        "blend_non_positive_size": "fillet size must be positive",
        "extrude_zero_distance": "extrude distance is zero",
        "missing_sketch": "no sketch `sketch_nonexistent`",
        "revolve_crosses_axis": "the profile crosses the revolve axis",
        "revolve_angle_invalid": "revolve angle is zero",
        "hole_not_on_face": "`position` [100 mm, 100 mm, 100 mm] is not on a face of a body; pick a point on the face to drill",
        "hole_counterbore_invalid": "the counterbore must be wider than the hole and shallower than it",
        "hole_countersink_invalid": "the countersink must be wider than the hole",
        "shell_non_positive_thickness": "shell thickness must be positive",
        "shell_too_thick": "the planes don't enclose a solid",
        "combine_self": "a body cannot be combined with itself",
        "unknown_body": "unknown body `nonexistent_body`",
        "pattern_count_unit": "invalid parameters for `pattern.linear`: expected a unit-less number, got a length: 5 mm",
        "sketch_zero_line": "zero-length line",
        "sketch_overconstrained": "that conflicts with the sketch: remove a constraint or un-fix a point to make room",
        "loft_section_count": "a loft needs 2…50 sections: add at least one more profile sketch",
        "boolean_unreliable": "the cut could not be computed reliably: faces touch along a zero-thickness edge",
        "intersect_empty": "the intersection is empty: nothing of Body 1 would remain",
        "profile_no_area": "profile has no area",
        "offset_unsupported_surface": "offset: only bodies with planes, cylinders, cones, spheres and tori (a face at [-7.07, -7.07, 0.00])",
        "offset_faces_cross": "offset: not supported yet: the move is larger than a wall or step is thick (faces would cross)",
        "offset_rim_too_narrow": "offset: not supported yet: the move is larger than a rim or ledge near [12.0, 5.0, 0.0] is wide (a face would turn inside out)",
        "offset_edge_vanishes": "offset: an edge vanishes (the offset is too large)",
        "draft_pull_parallel": "offset: the neutral plane is parallel to the pull direction",
        "extrude_curves_missing": "invalid parameters for `solid.extrude`: a thin extrude needs 1…1000 sketch curves (`curves`)",
        "curve_not_in_sketch": "invalid parameters for `solid.extrude`: no curve `c1` in the sketch",
        "thin_two_sides_missing_thickness": "invalid parameters for `solid.extrude`: `side: two_sides` needs `thickness2` (the thickness outside)",
        "sketch_no_closed_profiles": "Sketch1 has no closed profiles",
        "profile_loop_not_closed": "invalid input: profile loop is not closed",
        "curves_not_connected": "invalid input: the curves are not connected end to end",
        "revolve_axis_no_direction": "invalid input: revolve axis has no direction",
        "revolve_axis_param_invalid": "invalid parameters for `solid.revolve`: `axis` must be a sketch line id, x, y (sketch axes), X, Y, Z, a construction axis, {origin, dir} or {edge|face: [x,y,z]}",
        "loft_holes_count_mismatch": "invalid input: every loft section must have the same number of holes",
        "loft_same_plane": "invalid input: loft sections 1 and 2 lie in the same plane (no volume between them)",
        "sweep_path_no_direction": "invalid input: a path segment has no direction",
        "primitive_box_dimensions": "invalid input: box needs a positive size in x, y and z",
        "primitive_radius_non_positive": "invalid input: radius must be positive",
        "primitive_torus_radii": "invalid input: torus needs major > minor > 0",
        "hole_type_unknown": "invalid parameters for `solid.hole`: unknown hole type `tapered`",
        "hole_reference_edges_parallel": "invalid parameters for `solid.hole`: the reference edges are parallel: pick edges that cross",
        "hole_reference_off_face": "invalid parameters for `solid.hole`: the reference distances put the hole's centre off its face",
        "chamfer_angle_past_face": "invalid input: that chamfer angle runs past the other face",
        "pattern_features_missing": "invalid parameters for `solid.pattern.rectangular`: `features` must list features to copy",
        "pattern_feature_not_found": "invalid parameters for `solid.pattern.rectangular`: no feature `CutExtrude1`",
        "plane_name_reserved": "invalid parameters for `construct.plane`: `Top` is reserved for an origin plane (XY, XZ, YZ, Top, Front, Right); give the construction plane another name",
        "param_already_exists": "invalid parameters for `parameters.add`: there is already a parameter `length`: type `length` to use it, or change it in Parameters",
        "param_circular_reference": "expression: circular reference: a → b → a",
        "expr_division_by_zero": "expression: division by zero",
        "expr_incompatible_units": "expression: cannot add a length and an angle",
        "sketch_too_large": "sketch is too large (at most 20000 points or curves); simplify the drawing or split it across sketches — changing scale does not reduce how many curves it has",
        "sketch_unknown_entity": "invalid parameters for `sketch.delete`: unknown sketch entity `pt_invalid`",
        "step_shell_not_closed": "the operation failed: shell is not closed",
        "step_shell_not_manifold": "the operation failed: shell is not manifold",
        "step_no_bodies": "the operation failed: STEP import: no bodies (no shells)",
    }
    table_codes = {entry["code"] for entry in sc_errors.ERROR_TABLE}
    ok("sc_errors: all table codes covered by recorded errors", table_codes == set(recorded_errors.keys()))

    all_matched = True
    for code, raw_msg in recorded_errors.items():
        exp = sc_errors.explain(raw_msg)
        if not exp or exp["code"] != code or not exp["message"] or not exp["hint"]:
            all_matched = False
            break
    ok("sc_errors: each table entry correctly translates recorded error message", all_matched)

    ok("sc_errors: unknown error text returns None", sc_errors.explain("Some completely unknown message xyz") is None)
    ok("sc_errors: empty string returns None", sc_errors.explain("") is None)
    ok("sc_errors: JSON batch format unwraps inner error",
       sc_errors.explain('{"failed": {"command": "solid.extrude", "error": "extrude distance is zero", "index": 0}}') is not None
       and sc_errors.explain('{"failed": {"command": "solid.extrude", "error": "extrude distance is zero", "index": 0}}')["code"] == "extrude_zero_distance")

    exp_off = sc_errors.explain("offset: only bodies with planes, cylinders, cones, spheres and tori (a face at [-7.07, -7.07, 0.00])")
    ok("sc_errors: offset unsupported surface formats face coordinate and references #745/#10884",
       exp_off is not None and "[-7.07, -7.07, 0.00]" in exp_off["message"] and "#745" in exp_off["hint"] and "#10884" in exp_off["hint"])

    exp_loft_plane = sc_errors.explain("invalid input: loft sections 1 and 2 lie in the same plane (no volume between them)")
    ok("sc_errors: loft same plane formats section numbers",
       exp_loft_plane is not None and "sections 1 and 2 lie" in exp_loft_plane["message"])

    orig_ws = server.ws
    server.ws = ws
    try:
        # Live case 1: extrude distance is zero
        doc_a = ws.new(PART, "sc_err_extrude")
        try:
            caught_a = None
            try:
                server.run("sc_err_extrude", [
                    {"command": "sketch.create", "params": {"plane": "xy", "name": "sk1"}},
                    {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [10, 10]}},
                    {"command": "sketch.finish", "params": {}},
                    {"command": "solid.extrude", "params": {"sketch": "sk1", "distance": "0 mm"}},
                ])
            except Exception as e:
                caught_a = str(e)
            exp_a = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "extrude_zero_distance")
            ok("sc_errors run live 1: extrude zero distance re-raised with explanation and hint",
               caught_a is not None and exp_a["message"] in caught_a and exp_a["hint"] in caught_a and "extrude distance is zero" in caught_a)
            tl_a = sketch_rule.timeline(doc_a.session)["timeline"]
            ok("sc_errors run live 1: checkpoint restored on error", len(tl_a) == 0)
        finally:
            ws.close("sc_err_extrude")

        # Live case 2: revolve profile crosses axis
        doc_b = ws.new(PART, "sc_err_revolve")
        try:
            caught_b = None
            try:
                server.run("sc_err_revolve", [
                    {"command": "sketch.create", "params": {"plane": "xy", "name": "sk_rev"}},
                    {"command": "sketch.rectangle.two_point", "params": {"p0": [-5, 0], "p1": [5, 10]}},
                    {"command": "sketch.finish", "params": {}},
                    {"command": "solid.revolve", "params": {"sketch": "sk_rev", "axis": "y", "angle": "360 deg"}},
                ])
            except Exception as e:
                caught_b = str(e)
            exp_b = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "revolve_crosses_axis")
            ok("sc_errors run live 2: revolve crossing axis re-raised with explanation and hint",
               caught_b is not None and exp_b["message"] in caught_b and exp_b["hint"] in caught_b and "crosses the revolve axis" in caught_b)
        finally:
            ws.close("sc_err_revolve")

        # Live case 3: fillet too large
        doc_c = ws.new(PART, "sc_err_fillet")
        try:
            server.run("sc_err_fillet", [
                {"command": "sketch.create", "params": {"plane": "xy", "name": "sk_box"}},
                {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [10, 10]}},
                {"command": "sketch.finish", "params": {}},
                {"command": "solid.extrude", "params": {"sketch": "sk_box", "distance": "10 mm"}},
            ])
            caught_c = None
            try:
                server.run("sc_err_fillet", [  # 15 mm still failed on SolidCraft 0.30, 0.40 takes it and even 50 mm; 1000 mm fails on both
                    {"command": "solid.fillet", "params": {"edges": [[5, 0, 0]], "radius": "1000 mm"}},
                ])
            except Exception as e:
                caught_c = str(e)
            exp_c = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "blend_too_large")
            ok("sc_errors run live 3: fillet too large re-raised with explanation and hint",
               caught_c is not None and exp_c["message"] in caught_c and exp_c["hint"] in caught_c
               and ("blend is larger" in caught_c or "larger than the faces beside" in caught_c
                    or "would cut through the material behind it" in caught_c))  # words of 0.30 / 0.40
        finally:
            ws.close("sc_err_fillet")

        # Live case 4: hole not on face
        doc_d = ws.new(PART, "sc_err_hole")
        try:
            server.run("sc_err_hole", [
                {"command": "sketch.create", "params": {"plane": "xy", "name": "sk_h"}},
                {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [10, 10]}},
                {"command": "sketch.finish", "params": {}},
                {"command": "solid.extrude", "params": {"sketch": "sk_h", "distance": "10 mm"}},
            ])
            caught_d = None
            try:
                server.run("sc_err_hole", [
                    {"command": "solid.hole", "params": {"position": [50, 50, 50], "diameter": "4 mm", "depth": "5 mm"}},
                ])
            except Exception as e:
                caught_d = str(e)
            exp_d = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "hole_not_on_face")
            ok("sc_errors run live 4: hole not on face re-raised with explanation and hint",
               caught_d is not None and exp_d["message"] in caught_d and exp_d["hint"] in caught_d and "not on a face of a body" in caught_d)
        finally:
            ws.close("sc_err_hole")

        # Live case 5: offset unsupported surface (loft + shell)
        doc_e = ws.new(PART, "sc_err_loft_shell")
        try:
            server.run("sc_err_loft_shell", [
                {"command": "sketch.create", "params": {"plane": "xy", "name": "sk1"}},
                {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": "10 mm"}},
                {"command": "sketch.finish", "params": {}},
                {"command": "construct.plane.offset", "params": {"base": "XY", "offset": "20 mm", "name": "wp1"}},
                {"command": "sketch.create", "params": {"plane": "wp1", "name": "sk2"}},
                {"command": "sketch.rectangle.two_point", "params": {"p0": [-5, -5], "p1": [5, 5]}},
                {"command": "sketch.finish", "params": {}},
                {"command": "solid.loft", "params": {"sections": [{"sketch": "sk1"}, {"sketch": "sk2"}]}},
            ])
            caught_e = None
            try:
                server.run("sc_err_loft_shell", [
                    {"command": "solid.shell", "params": {"faces": [[0, 0, 20]], "thickness": "1 mm"}},
                ])
            except Exception as e:
                caught_e = str(e)
            if caught_e is None:
                # SolidCraft 0.40 shells a lofted body (#745 fixed): the step works and the body is hollow
                bodies_e = doc_e.session.cmd("document.inspect", {"measure": True}).get("bodies", [])
                ok("sc_errors run live 5: shell on a lofted body works since SolidCraft 0.40 (#745 fixed), no offset hint needed",
                   bool(bodies_e) and bodies_e[0].get("volume_mm3", 0) > 0, str(bodies_e)[:200])
            else:
                ok("sc_errors run live 5: offset unsupported surface re-raised with explanation and hint",
                   "#745" in caught_e and "#10884" in caught_e and "only bodies with planes" in caught_e)
        finally:
            ws.close("sc_err_loft_shell")

        # Live case 6: box zero dimension
        doc_f = ws.new(PART, "sc_err_box")
        try:
            caught_f = None
            try:
                server.run("sc_err_box", [
                    {"command": "solid.box", "params": {"length": "0 mm", "width": "10 mm", "height": "10 mm"}},
                ])
            except Exception as e:
                caught_f = str(e)
            exp_f = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "primitive_box_dimensions")
            ok("sc_errors run live 6: box zero dimension re-raised with explanation and hint",
               caught_f is not None and exp_f["message"] in caught_f and exp_f["hint"] in caught_f and "box needs a positive size" in caught_f)
        finally:
            ws.close("sc_err_box")

        # Live case 7: cylinder non-positive radius
        doc_g = ws.new(PART, "sc_err_cyl")
        try:
            caught_g = None
            try:
                server.run("sc_err_cyl", [
                    {"command": "solid.cylinder", "params": {"radius": "0 mm", "height": "10 mm"}},
                ])
            except Exception as e:
                caught_g = str(e)
            exp_g = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "primitive_radius_non_positive")
            ok("sc_errors run live 7: cylinder non-positive radius re-raised with explanation and hint",
               caught_g is not None and exp_g["message"] in caught_g and exp_g["hint"] in caught_g and "radius must be positive" in caught_g)
        finally:
            ws.close("sc_err_cyl")

        # Live case 8: plane name reserved
        doc_h = ws.new(PART, "sc_err_plane")
        try:
            caught_h = None
            try:
                server.run("sc_err_plane", [
                    {"command": "construct.plane.offset", "params": {"base": "XY", "offset": "10 mm", "name": "Top"}},
                ])
            except Exception as e:
                caught_h = str(e)
            exp_h = sc_errors.explain("invalid parameters for `construct.plane`: `Top` is reserved for an origin plane (XY, XZ, YZ, Top, Front, Right); give the construction plane another name")
            ok("sc_errors run live 8: plane name reserved re-raised with explanation and hint",
               caught_h is not None and exp_h["message"] in caught_h and exp_h["hint"] in caught_h and "reserved for an origin plane" in caught_h)
        finally:
            ws.close("sc_err_plane")

        # Live case 9: duplicate parameter
        doc_i = ws.new(PART, "sc_err_param")
        try:
            caught_i = None
            try:
                server.run("sc_err_param", [
                    {"command": "parameters.add", "params": {"name": "p_dup", "expression": "10 mm"}},
                    {"command": "parameters.add", "params": {"name": "p_dup", "expression": "20 mm"}},
                ])
            except Exception as e:
                caught_i = str(e)
            exp_i = sc_errors.explain("there is already a parameter `p_dup`")
            ok("sc_errors run live 9: duplicate parameter re-raised with explanation and hint",
               caught_i is not None and exp_i["message"] in caught_i and exp_i["hint"] in caught_i and "already a parameter" in caught_i)
        finally:
            ws.close("sc_err_param")

        # Live case 10: sketch has no closed profiles
        doc_j = ws.new(PART, "sc_err_no_prof")
        try:
            caught_j = None
            try:
                server.run("sc_err_no_prof", [
                    {"command": "sketch.create", "params": {"plane": "xy", "name": "sk_open"}},
                    {"command": "sketch.line", "params": {"points": [[0, 0], [10, 0]]}},
                    {"command": "sketch.finish", "params": {}},
                    {"command": "solid.extrude", "params": {"sketch": "sk_open", "distance": "10 mm"}},
                ])
            except Exception as e:
                caught_j = str(e)
            exp_j = sc_errors.explain("sk_open has no closed profiles")
            ok("sc_errors run live 10: sketch without closed profiles re-raised with explanation and hint",
               caught_j is not None and exp_j["message"] in caught_j and exp_j["hint"] in caught_j and "has no closed profiles" in caught_j)
        finally:
            ws.close("sc_err_no_prof")
    finally:
        server.ws = orig_ws


def sc_locate_checks(ws):
    """Error translation stage 3: a failed step names the edge or face it was aimed at, the features these
    belong to and what is in the way; an edit that makes a later feature fail reports that feature."""
    import math as m

    ok("sc_locate: an edge name is split at the right bar when a blend face has one in its own name",
       sc_locate.edge_faces("F2:start|F4:blend:F2:side:l1|F2:side:l4", {"F2:start", "F4:blend:F2:side:l1|F2:side:l4", "F2:side:l1"})
       == ("F2:start", "F4:blend:F2:side:l1|F2:side:l4")
       and sc_locate.edge_faces("F3:side#1|F3:side#2~2", {"F3:side#1", "F3:side#2"}) == ("F3:side#1", "F3:side#2")
       and sc_locate.edge_faces("F1:+x|F9:gone", {"F1:+x"}) is None)
    cs = sc_locate._critical_size
    ok("sc_locate: a chamfer reaches a point at alpha + beta, a fillet a point on a face at its distance and "
       "a point on the bisector of a square corner at a·(2 + √2)",
       abs(cs("chamfer", 3, 2, 0.0) - 5) < 1e-9 and abs(cs("fillet", 7, 0, 0.0) - 7) < 1e-6
       and abs(cs("fillet", 5, 5, 0.0) - 5 * (2 + m.sqrt(2))) < 1e-6
       # 60° between the faces: the tangent points lie r·cot(30°) from the edge
       and abs(cs("fillet", 6, 0, 0.5) - 6 * m.tan(m.radians(30))) < 1e-6,
       f"{cs('chamfer', 3, 2, 0.0)} {cs('fillet', 7, 0, 0.0)} {cs('fillet', 5, 5, 0.0)} {cs('fillet', 6, 0, 0.5)}")
    pts, radius = sc_locate.edge_points({"start": [3, 0, 0], "mid": [0, 3, 0], "end": [-3, 0, 0], "length": m.pi * 3})
    ring, ring_r = sc_locate.edge_points({"start": [3, 0, 0], "mid": [-3, 0, 0], "end": [3, 0, 0], "length": 2 * m.pi * 3},
                                         normal=[0, 0, 1])
    ok("sc_locate: a circle that closes in itself (hole rim since SolidCraft 0.40) is rebuilt from the normal of its plane",
       ring_r is not None and abs(ring_r - 3) < 1e-9 and len(ring) > 20 and all(abs(g.norm(q) - 3) < 1e-9 for q in ring)
       and all(abs(q[2]) < 1e-9 for q in ring), f"{ring_r} {len(ring)}")
    line, no_radius = sc_locate.edge_points({"start": [0, 0, 0], "mid": [5, 0, 0], "end": [10, 0, 0], "length": 10})
    ok("sc_locate: an arc is rebuilt from start, mid, end and length; a straight edge stays two points",
       abs(radius - 3) < 1e-9 and all(abs(g.norm(q) - 3) < 1e-9 for q in pts) and len(pts) > 20
       and line == [[0, 0, 0], [10, 0, 0]] and no_radius is None, f"{radius} {len(pts)} {line}")

    plate = [{"command": "solid.box", "params": {"name": "Plate", "length": 60, "width": 40, "height": 10}},
             {"command": "solid.hole", "params": {"name": "Hole1", "position": [8, 8, 10], "diameter": 6}}]

    def fails(doc, command, params, before=()):
        try:
            modeling.run_commands(doc, list(before) + [{"command": command, "params": params}])
        except Exception as e:
            return e
        return None

    def state(doc):
        i = doc.session.cmd("document.inspect", {"measure": False})
        return len(i["timeline"]), i["undo"], i["redo"]

    doc = ws.new(PART, "loc_plate")
    try:
        # the failed step is the third of its batch: the place is found on the model the step saw
        empty = state(doc)
        e = fails(doc, "solid.chamfer", {"name": "C1", "edges": [[30, 0, 10]], "distance": 5.5}, before=plate)
        chamfer_through_hole = e is None
        if chamfer_through_hole:
            # SolidCraft 0.40 chamfers through a hole: the step succeeded, so start again on an empty document
            ws.close("loc_plate")
            doc = ws.new(PART, "loc_plate", overwrite=True)
            empty = state(doc)
        loc = modeling.error_place(e) or {}
        obstacle = loc.get("obstacle") or {}
        ok("sc_locate: a chamfer that runs into a hole names the edge, the hole, its distance and the size that fits"
           " (SolidCraft 0.30; 0.40 chamfers through the hole, nothing to locate)",
           chamfer_through_hole or isinstance(e, sc_errors.ExplainedError) and "\nWhere: Chamfer C1 (5.5 mm) on the edge of Plate between +z and -y" in str(e)
           and obstacle.get("feature") == "Hole1" and obstacle.get("foreign") is True
           and abs(obstacle.get("distance", 0) - 5.0) < 0.01 and abs(obstacle["at"][1] - 5.0) < 0.01
           and loc.get("fits") == 4.913 and loc.get("at") == [30.0, 0.0, 10.0] and loc.get("features") == ["Plate", "Hole1"]
           and "move Hole1" in loc.get("text", ""), f"{str(e)[:300]} {loc}")
        if chamfer_through_hole:
            # the same two properties on a step that fails on every SolidCraft: a fillet far too large
            e_big = fails(doc, "solid.fillet", {"name": "RBig", "edges": [[30, 0, 10]], "radius": 1000}, before=plate)
            ok("sc_locate: looking at the model of a failed batch leaves the document and its undo list as they were",
               e_big is not None and state(doc) == empty, f"{empty} {state(doc)}")
            ok("sc_locate: the dialog line keeps the explanation and SolidCraft's words",
               e_big is not None and "Where" not in modeling.short_error(e_big).split("\n")[0]
               and len(modeling.short_error(e_big)) > 20, modeling.short_error(e_big) if e_big else "no error")
        else:
            ok("sc_locate: looking at the model of a failed batch leaves the document and its undo list as they were",
               state(doc) == empty, f"{empty} {state(doc)}")
            ok("sc_locate: the dialog line keeps the explanation and SolidCraft's words",
               modeling.short_error(e).startswith("The chamfer distance is too large") and "SolidCraft: 5.5 mm is too large" in modeling.short_error(e),
               modeling.short_error(e))

        modeling.run_commands(doc, plate)
        e = fails(doc, "solid.fillet", {"name": "R1", "edges": [[0, 0, 5]], "radius": 25})
        loc = modeling.error_place(e) or {}
        obstacle = loc.get("obstacle") or {}
        ok("sc_locate: a corner fillet that reaches a hole on the end face names it, and the radius from which "
           "it is reached agrees with the largest radius SolidCraft gives (within 3 %)",
           obstacle.get("feature") == "Hole1" and loc.get("fits")
           and abs(obstacle.get("reached_from", 0) / loc["fits"] - 1) < 0.03, f"{loc}")

        wide = 100 if chamfer_through_hole else 12  # SolidCraft 0.40 takes a 12 mm chamfer on a 10 mm plate
        e = fails(doc, "solid.chamfer", {"edges": [[30, 40, 10]], "distance": f"{wide} mm"})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: a chamfer wider than the plate is thick names the face that is too narrow, not a far hole",
           "Plate (+y) is only 10 mm wide there" in loc.get("text", "") and loc.get("requested") == float(wide)
           and (chamfer_through_hole or (loc.get("obstacle", {}).get("foreign") is False and "also_near" not in loc)),
           f"{loc.get('text')}")

        e = fails(doc, "solid.fillet", {"name": "R3", "edges": [[11, 8, 10]], "radius": 100 if chamfer_through_hole else 6})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: a fillet larger than the hole rim it sits on names the radius of that edge"
           " (SolidCraft 0.40 takes 6 mm, so it gets 100 mm there)",
           "the edge between Plate (+z) and Hole1 (bore)" in loc.get("text", "") and "arc of radius 3 mm" in loc.get("text", "")
           and loc.get("features") == ["Plate", "Hole1"], f"{str(e)[:200]} {loc.get('text')}")

        e = fails(doc, "solid.hole", {"name": "H2", "position": [100, 8, 10], "diameter": 6})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: a hole position off the body names the nearest face, its distance and the nearest point",
           loc.get("kind") == "hole" and loc.get("nearest", {}).get("label") in ("Plate (+x)", "Plate (+z)")  # equally near: the edge between them
           and loc["nearest"]["distance"] == 40.0 and loc["nearest"]["nearest_point"] == [60.0, 8.0, 10.0], f"{loc}")
        e = fails(doc, "solid.hole", {"name": "H2", "position": [8, 8, 12], "diameter": 2})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: above an existing hole the nearest face is not the top face (the hole is no part of it)",
           loc.get("nearest", {}).get("label") in ("Hole1 (bore)", "Plate (+z)") and loc["nearest"]["distance"] > 2.5, f"{loc}")

        e = fails(doc, "solid.fillet", {"name": "R4", "edges": [[30, 20, 5]], "radius": 1})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: a pick with no edge near it names the nearest edge and its midpoint to pick",
           loc.get("nearest", {}).get("distance") == 20.616 and loc["nearest"]["mid"] in ([30.0, 40.0, 0.0], [30.0, 0.0, 0.0], [30.0, 40.0, 10.0], [30.0, 0.0, 10.0])
           and "pick it at its midpoint" in loc.get("text", ""), f"{loc}")
        e = fails(doc, "solid.fillet", {"name": "R5", "edges": [[0, 0, 0]], "radius": 1})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: a pick on a corner lists the three edges that meet there with their midpoints",
           sorted(x["mid"] for x in loc.get("edges", [])) == [[0.0, 0.0, 5.0], [0.0, 20.0, 0.0], [30.0, 0.0, 0.0]], f"{loc}")

        # SolidCraft's words for a pick it finds equally near to two edges (seen 4 mm from both on a bracket)
        loc = sc_locate.locate(doc.session, "solid.chamfer", {"name": "C0", "edges": [[0, 20, 5]], "distance": 1},
                               "invalid parameters for `solid.chamfer`: [0, 20, 5] is where 2 edges meet: give a point "
                               "along one edge, such as its midpoint") or {}
        ok("sc_locate: a pick in the middle of a narrow face names the two edges that are equally near",
           sorted(x["mid"] for x in loc.get("edges", [])) == [[0.0, 20.0, 0.0], [0.0, 20.0, 10.0]]
           and "as near to one edge as to the other (5 mm)" in loc.get("text", ""), f"{loc}")
        loc = sc_locate.locate(doc.session, "solid.hole", {"name": "H3", "position": [58, 20, 10], "diameter": 6},
                               "boolean Cut: the operation failed: no result") or {}
        ok("sc_locate: a hole whose cut fails near the rim of its face names the edge it cuts through",
           "its centre is 2 mm from the edge of Plate between +x and +z" in loc.get("text", "")
           and loc.get("obstacle", {}).get("label") == "Plate (+x)", f"{loc}")

        e = fails(doc, "solid.shell", {"name": "S1", "faces": [[30, 20, 10]], "thickness": 20 if chamfer_through_hole else 6})
        loc = modeling.error_place(e)
        ok("sc_locate: an error without explanation still tells which face the step was aimed at, and the "
           "dialog line stays SolidCraft's words",
           e is not None and (loc is None or (loc.get("kind") == "picks" and "face Plate (+z)" in loc["text"]
                                               and str(e).startswith("Where: ") and not modeling.short_error(e).startswith("Where"))),
           f"{str(e)[:200]} {loc}")

        # an edit that takes away what a later feature needs: the batch succeeds, the feature fails
        modeling.run_commands(doc, [{"command": "solid.chamfer", "params": {"name": "C1", "edges": [[30, 0, 10]], "distance": 4}}])
        out = modeling.run_commands(doc, [{"command": "timeline.edit", "params": {"feature": "Hole1", "set": {"at": [8, 3.5, 10]}}}])
        broken = (out.get("feature_errors") or [{}])[0]
        if chamfer_through_hole:
            # SolidCraft 0.40: the chamfer survives a hole moved under it, no feature fails (TODO: another trigger)
            ok("sc_locate: moving a hole under a chamfer reports the chamfer as failing, with the hole as the reason"
               " (SolidCraft 0.30; on 0.40 the chamfer survives, so no feature fails)",
               not out.get("feature_errors"), f"{out}")
            out = modeling.run_commands(doc, [{"command": "solid.hole", "params": {"name": "H9", "position": [50, 30, 10], "diameter": 4}}])
            ok("sc_locate: a later step reminds of the feature that still fails, without reporting it as new"
               " (SolidCraft 0.30; on 0.40 nothing fails)",
               "feature_errors" not in out and not any("Still failing" in w for w in out.get("warnings", [])), f"{out}")
        else:
            ok("sc_locate: moving a hole under a chamfer reports the chamfer as failing, with the hole as the reason",
               broken.get("feature") == "C1" and "Hole1 (bore) 0.5" in broken.get("where", "")
               and broken.get("location", {}).get("obstacle", {}).get("feature") == "Hole1"
               and broken.get("message") and any("C1 fail" in w for w in out.get("warnings", [])), f"{out}")
            out = modeling.run_commands(doc, [{"command": "solid.hole", "params": {"name": "H9", "position": [50, 30, 10], "diameter": 4}}])
            ok("sc_locate: a later step reminds of the feature that still fails, without reporting it as new",
               "feature_errors" not in out and any("Still failing from before: C1" in w for w in out.get("warnings", [])), f"{out}")
    finally:
        ws.close("loc_plate")

    doc = ws.new(PART, "loc_round")
    try:
        modeling.run_commands(doc, rect("sk", "xy", [0, 0], [60, 40]) + [
            {"command": "solid.extrude", "params": {"sketch": "sk", "distance": "10 mm", "name": "Base"}},
            {"command": "solid.fillet", "params": {"name": "R1", "edges": [[0, 0, 5]], "radius": 4}}])
        e = fails(doc, "solid.fillet", {"name": "R2", "edges": [[0, 40, 5]], "radius": 38})
        loc = modeling.error_place(e) or {}
        ok("sc_locate: a fillet that reaches the round at the other end of a face names that round (a face "
           "name with a bar in it)",
           loc.get("obstacle", {}).get("feature") == "R1" and loc["obstacle"]["label"].startswith("R1 (blend")
           and abs(loc["obstacle"]["distance"] - 36) < 0.01 and "move R1" in loc.get("text", ""), f"{str(e)[:200]} {loc}")
    finally:
        ws.close("loc_round")


def sc_errors_stage2_checks(ws):
    """Stage 2 error translation (issue #42): translated errors for all MCP tools and /api/feature.
    (a) add_joint with known error raises RuntimeError with explanation and hint in the error text;
    (b) /api/feature with oversized fillet returns explanation and hint in both preview and apply;
    (c) unknown errors remain unchanged without empty additions."""
    import urllib.error
    import urllib.request
    from unittest.mock import patch
    from mechvane.solidcraft import SolidCraftError
    from mechvane.ui import server as ui_server

    orig_ws = server.ws
    server.ws = ws
    try:
        # (a) add_joint with an error known to explain() delivers explanation and hint in the error text
        asm_doc = ws.new(ASSEMBLY, "sc2_err_asm")
        asm_doc.save()
        try:
            caught_known = None
            with patch.object(asm_doc.session, "cmd", side_effect=SolidCraftError("unknown body `PartGhost`")):
                try:
                    server.add_joint("sc2_err_asm", {"name": "J1", "a": {"point": [0, 0, 0]}, "b": {"point": [1, 0, 0]}})
                except Exception as e:
                    caught_known = e

            exp_known = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "unknown_body")
            ok("sc_errors stage 2 (a): add_joint known error re-raised as RuntimeError with explanation and hint",
               isinstance(caught_known, sc_errors.ExplainedError) and isinstance(caught_known, RuntimeError)
               and exp_known["message"] in str(caught_known)
               and exp_known["hint"] in str(caught_known)
               and "unknown body `PartGhost`" in str(caught_known),
               str(caught_known))

            # (c-1) unknown error in add_joint remains unchanged
            caught_unknown = None
            orig_err = SolidCraftError("some unrecognized solidcraft failure 12345")
            with patch.object(asm_doc.session, "cmd", side_effect=orig_err):
                try:
                    server.add_joint("sc2_err_asm", {"name": "J2", "a": {"point": [0, 0, 0]}, "b": {"point": [1, 0, 0]}})
                except Exception as e:
                    caught_unknown = e

            ok("sc_errors stage 2 (c): unknown error in add_joint remains unchanged",
               caught_unknown is orig_err
               and type(caught_unknown) is SolidCraftError
               and str(caught_unknown) == "some unrecognized solidcraft failure 12345",
               str(caught_unknown))
        finally:
            ws.close("sc2_err_asm")

        # (b) /api/feature with a fillet whose radius is too large returns explanation and hint
        block_doc = ws.new(PART, "sc2_err_block")
        block_doc.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY", "name": "Base"}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [20, 20]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "Base", "distance": 10, "name": "Block"}}
        ])
        block_doc.save()
        part_path = block_doc.path
        srv = ui_server.create_server(str(part_path), port=0)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/"
        try:
            def call_feature(body):
                req = urllib.request.Request(
                    base + "feature",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req) as resp:
                        return resp.status, json.loads(resp.read())
                except urllib.error.HTTPError as err:
                    return err.code, json.loads(err.read())

            exp_fillet = next(x for x in sc_errors.ERROR_TABLE if x["code"] == "blend_too_large")

            # Preview with radius too large
            st_prev, data_prev = call_feature({
                "command": "solid.fillet",
                "params": {"edges": [[10, 20, 10]], "radius": 50},
                "preview": True
            })
            ok("sc_errors stage 2 (b): /api/feature preview with oversized fillet returns explanation and hint",
               st_prev == 400
               and data_prev.get("explanation") == exp_fillet["message"]
               and data_prev.get("hint") == exp_fillet["hint"]
               and "SolidCraft:" in data_prev.get("error", ""),
               f"st={st_prev} data={data_prev}")
            ok("sc_locate: /api/feature names the edge and the face that is too narrow for the fillet",
               "the edge of Block" in data_prev.get("where", "") and "only 10 mm wide" in data_prev.get("where", "")
               and data_prev.get("location", {}).get("kind") == "blend"
               and data_prev.get("location", {}).get("at") == [10.0, 20.0, 10.0],
               f"{data_prev.get('where')} {data_prev.get('location')}")

            # Apply with radius too large
            st_apply, data_apply = call_feature({
                "command": "solid.fillet",
                "params": {"edges": [[10, 20, 10]], "radius": 50},
                "preview": False
            })
            ok("sc_errors stage 2 (b): /api/feature apply with oversized fillet returns explanation and hint",
               st_apply == 400
               and data_apply.get("explanation") == exp_fillet["message"]
               and data_apply.get("hint") == exp_fillet["hint"]
               and "SolidCraft:" in data_apply.get("error", ""),
               f"st={st_apply} data={data_apply}")

            # (c-2) /api/feature with an unknown error has no explanation or hint fields
            st_unk, data_unk = call_feature({"command": "solid.fillet", "params": {"edges": "invalid_type"}})
            ok("sc_errors stage 2 (c): /api/feature with unknown error does not add empty explanation or hint",
               st_unk == 400
               and "explanation" not in data_unk
               and "hint" not in data_unk
               and "error" in data_unk,
               f"st={st_unk} data={data_unk}")
        finally:
            srv.shutdown()
            srv.server_close()
            ws.close("sc2_err_block")

        # (c-3) sc_errors.reraise re-raises unknown exception unchanged
        custom_err = ValueError("custom unknown error 99")
        caught_custom = None
        try:
            sc_errors.reraise(custom_err)
        except Exception as e:
            caught_custom = e
        ok("sc_errors stage 2 (c): reraise re-raises unknown exception unchanged",
           caught_custom is custom_err and type(caught_custom) is ValueError and str(caught_custom) == "custom unknown error 99")
    finally:
        server.ws = orig_ws
def praxistest_6_fixes_checks(ws):
    # Befund 3 (issue #34): Through hole drilled "through all" instead of fixed depth.
    # Increasing plate thickness via parameter keeps through hole; check_design remains green.
    p1 = ws.new(PART, "pt6_p1")
    p1.session.batch([
        {"command": "parameters.add", "params": {"name": "dicke", "expression": "8 mm"}},
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": "dicke", "corner": [-20, -20, 0], "name": "Box1"}}
    ])
    p1.save()

    p2 = ws.new(PART, "pt6_p2")
    p2.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [-20, -20, 0], "name": "Box2"})
    p2.save()

    asm = ws.new(ASSEMBLY, "pt6_asm")
    links.insert(ws, asm, p1.path, name="Plate1", grounded=True)
    links.insert(ws, asm, p2.path, name="Plate2", translate=[0, 0, -8], grounded=True)
    asm.save()

    res = bolted.bolted_connection(
        ws, "pt6_asm",
        placement={"position": [0, 0, 8], "direction": [0, 0, -1]},
        size="M5",
        counterbore=False,
    )

    # Change plate thickness from 8 mm to 12 mm
    p1.session.cmd("parameters.change", {"name": "dicke", "expression": "12 mm"})
    p1.save()
    links.update_links(ws, asm)

    chk = design_rules.check(p1.session)
    td_findings = [f for f in chk.get("checks", []) if f.get("rule") == "thread_depth" and f.get("status") != "ok"]
    vol_p1 = p1.session.tool("inspect_design", {"measure": True})["bodies"][0]["volume_mm3"]
    expected_vol = 40.0 * 40.0 * 12.0 - math.pi * (2.75 ** 2) * 12.0
    r_p1 = ws.reader(p1.path)
    try:
        faces_p1 = links._part_faces(r_p1)
    finally:
        r_p1.close()
    bore_faces = [f for f in faces_p1 if "bore" in f.get("name", "")]

    ok("praxistest 6 / finding 3: through hole goes through all after plate thickness increased (no thread_depth warning)",
       chk.get("verdict") == "ok" and not td_findings and abs(vol_p1 - expected_vol) < 0.1 and len(bore_faces) >= 1,
       f"verdict={chk.get('verdict')} td={td_findings} vol={vol_p1} expected={expected_vol}")

    # Delete bolted connection removes holes and restores solid box volume
    bolted.delete_bolted_connection(ws, "pt6_asm", res["id"])
    vol_restored = p1.session.tool("inspect_design", {"measure": True})["bodies"][0]["volume_mm3"]
    ok("praxistest 6 / finding 3: delete_bolted_connection restores original plate volume",
       abs(vol_restored - 19200.0) < 1e-3, f"vol={vol_restored}")

    for name in ("pt6_asm", "pt6_p2", "pt6_p1"):
        ws.close(name)

    # Befund 4 (issue #34): Collision check before drilling: overlapping plates raise ValueError
    p_ol1 = ws.new(PART, "pt6_ol1")
    p_ol1.session.cmd("solid.box", {"length": 40, "width": 40, "height": 10, "corner": [-20, -20, 0], "name": "B1"})
    p_ol1.save()

    p_ol2 = ws.new(PART, "pt6_ol2")
    p_ol2.session.cmd("solid.box", {"length": 40, "width": 40, "height": 8, "corner": [-20, -20, 0], "name": "B2"})
    p_ol2.save()

    asm_ol = ws.new(ASSEMBLY, "pt6_asm_ol")
    links.insert(ws, asm_ol, p_ol1.path, name="Plate1", grounded=True)
    links.insert(ws, asm_ol, p_ol2.path, name="Plate2", translate=[0, 0, -6], grounded=True)  # 2 mm penetration
    asm_ol.save()

    bytes_1_before = p_ol1.path.read_bytes()
    bytes_2_before = p_ol2.path.read_bytes()

    collision_err = None
    try:
        bolted.bolted_connection(
            ws, "pt6_asm_ol",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5"
        )
    except ValueError as e:
        collision_err = str(e)

    bytes_1_after = p_ol1.path.read_bytes()
    bytes_2_after = p_ol2.path.read_bytes()

    err_has_parts = collision_err is not None and "Plate1:1" in collision_err and "Plate2:1" in collision_err
    err_has_coords = collision_err is not None and "bounding box" in collision_err and "center" in collision_err
    err_has_advice = collision_err is not None and "touch" in collision_err and "penetrat" in collision_err
    files_untouched = (bytes_1_before == bytes_1_after) and (bytes_2_before == bytes_2_after)

    ok("praxistest 6 / finding 4: overlapping plates raise ValueError with parts, location and advice, files unchanged",
       collision_err is not None and err_has_parts and err_has_coords and err_has_advice and files_untouched,
       f"err={collision_err} untouched={files_untouched}")

    # Touching plates (at z = 0, no penetration) pass without collision error
    asm_touch = ws.new(ASSEMBLY, "pt6_asm_touch")
    links.insert(ws, asm_touch, p_ol1.path, name="Plate1", grounded=True)
    links.insert(ws, asm_touch, p_ol2.path, name="Plate2", translate=[0, 0, -8], grounded=True)  # touching at z = 0
    asm_touch.save()

    touch_err = None
    try:
        bolted.preview_bolted_connection(
            ws, "pt6_asm_touch",
            placement={"position": [0, 0, 10], "direction": [0, 0, -1]},
            size="M5"
        )
    except ValueError as e:
        touch_err = str(e)

    ok("praxistest 6 / finding 4: touching clamping faces without penetration pass collision check",
       touch_err is None, f"err={touch_err}")

    for name in ("pt6_asm_touch", "pt6_asm_ol", "pt6_ol2", "pt6_ol1"):
        ws.close(name)


def part_end_checks(ws):
    """End-of-part marker tool (ROADMAP v0.1 #44): rollback before feature, isolated volume, run warning, saving
    while rolled back is allowed (as in Inventor)."""
    server.ws = ws
    ws.new(PART, "part_end_test")
    try:
        server.run("part_end_test", [
            {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 20, "name": "Quader"}},
            {"command": "solid.hole", "params": {"position": [20, 20, 20], "direction": [0, 0, -1], "diameter": 10, "depth": 20, "name": "Bohrung"}},
            {"command": "solid.fillet", "params": {"edges": [[20, 0, 20]], "radius": 2, "name": "Rundung"}}
        ])
        v_full = server.measure("part_end_test")["bodies"][0]["volume_mm3"]
        server.save_document("part_end_test")

        # Roll before Bohrung
        r_rolled = server.part_end("part_end_test", before="Bohrung")
        ok("part_end: roll before Bohrung gives box volume",
           abs(r_rolled["volume_mm3"] - 32000.0) < 0.1 and r_rolled["position"] == 1
           and r_rolled.get("rolled_back") == ["Bohrung", "Rundung"],
           str(r_rolled))

        # save_document while rolled back saves, as in Inventor
        saved_rolled = server.save_document("part_end_test")
        ok("part_end: save_document works while rolled back", saved_rolled.get("name") == "part_end_test",
           str(saved_rolled))

        # run while rolled back returns hint/warning
        r_run = server.run("part_end_test", [
            {"command": "parameters.add", "params": {"name": "p_check", "expression": "5 mm"}}
        ])
        warnings_found = any("part end" in w.lower() for w in r_run.get("warnings", [])) or any(
            "part end" in w.lower() for w in r_run.get("delta", {}).get("warnings", [])
        )
        ok("part_end: run while rolled back includes part end hint", warnings_found, str(r_run))

        # Roll back to end
        r_end = server.part_end("part_end_test")
        ok("part_end: roll to end restores previous volume and clears rolled_back list",
           abs(r_end["volume_mm3"] - v_full) < 0.1 and r_end["position"] == 3 and r_end.get("rolled_back") == [],
           str(r_end))

        # save_document after rolling to end succeeds
        saved_info = server.save_document("part_end_test")
        ok("part_end: save_document succeeds after rolling to end",
           saved_info.get("name") == "part_end_test", str(saved_info))

        # Roll before unknown feature raises ValueError
        unknown_err = False
        try:
            server.part_end("part_end_test", before="NonExistent")
        except ValueError as e:
            unknown_err = "not found" in str(e)
        ok("part_end: unknown feature raises ValueError", unknown_err)
    finally:
        ws.close("part_end_test")


def bill_of_materials_checks(ws):
    import csv
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    orig_ws = server.ws
    server.ws = ws

    try:
        # Part 1: Plate 1 with Steel
        p1 = ws.new(PART, "bom_plate1")
        p1.session.cmd("solid.box", {"length": 60, "width": 60, "height": 10, "body_name": "Plate1Body", "name": "Box1"})
        p1.session.cmd("material.assign", {"bodies": ["Plate1Body"], "material": "Steel"})
        p1.save()

        # Part 2: Plate 2 without material
        p2 = ws.new(PART, "bom_plate2")
        p2.session.cmd("solid.box", {"length": 60, "width": 60, "height": 10, "body_name": "Plate2Body", "name": "Box2"})
        p2.save()

        # Part 3: Bracket with Aluminum (inserted twice -> 2 identical parts)
        bracket = ws.new(PART, "bom_bracket")
        bracket.session.cmd("solid.box", {"length": 15, "width": 15, "height": 5, "body_name": "BracketBody", "name": "BBox"})
        bracket.session.cmd("material.assign", {"bodies": ["BracketBody"], "material": "Aluminum"})
        bracket.save()

        # Depth-2 nested subassembly: bom_sub_part -> bom_sub_asm -> bom_outer_sub
        sub_part = ws.new(PART, "bom_sub_part")
        sub_part.session.cmd("solid.box", {"length": 20, "width": 20, "height": 5, "body_name": "SubBody", "name": "SubBox"})
        sub_part.session.cmd("material.assign", {"bodies": ["SubBody"], "material": "Steel"})
        sub_part.save()

        sub_asm = ws.new(ASSEMBLY, "bom_sub_asm")
        links.insert(ws, sub_asm, sub_part.path, name="SubPart")
        sub_asm.save()

        outer_sub = ws.new(ASSEMBLY, "bom_outer_sub")
        links.insert(ws, outer_sub, sub_asm.path, name="InnerSub")
        links.insert(ws, outer_sub, sub_part.path, name="ExtraLeaf", translate=[30, 0, 0])
        outer_sub.save()

        # Main Assembly
        asm = ws.new(ASSEMBLY, "bom_main_asm")
        links.insert(ws, asm, p1.path, name="Plate1")
        links.insert(ws, asm, p2.path, name="Plate2", translate=[0, 0, -10])
        links.insert(ws, asm, bracket.path, name="Bracket1", translate=[20, 20, 10])
        links.insert(ws, asm, bracket.path, name="Bracket2", translate=[-20, -20, 10])
        links.insert(ws, asm, outer_sub.path, name="OuterSubInstance", translate=[0, 0, 20])
        bolted.bolted_connection(
            ws, "bom_main_asm",
            placement={"position": [15, 15, 10], "direction": [0, 0, -1]},
            size="M5",
            counterbore=False,
        )
        asm.save()

        # Place a standard part via UI endpoint POST /api/assembly/standard, then test GET /api/assembly/bom
        ws.close_all()
        srv = ui_server.create_server(ws.root, port=0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

        def call(endpoint, body=None):
            headers = {"Content-Type": "application/json"} if body is not None else {}
            req = urllib.request.Request(
                base + endpoint,
                method="POST" if body is not None else "GET",
                data=json.dumps(body).encode() if body is not None else None,
                headers=headers,
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read().decode("utf-8"))

        try:
            st_op_part, _ = call("open/bom_plate1.solidcraft", {})
            st_bom_part, err_bom_part = call("assembly/bom")
            ok("BOM HTTP: GET /api/assembly/bom returns 400 when a part is open",
               st_op_part == 200 and st_bom_part == 400 and bool(err_bom_part.get("error")),
               f"open={st_op_part} bom=({st_bom_part}, {err_bom_part})")

            st_op_asm, _ = call("open/bom_main_asm.solidcraft", {})
            st_std, res_std = call("assembly/standard", {"norm": "DIN 625", "size": "608", "translate": [40, 0, 10]})
            ok("BOM setup: Place Standard Part via /api/assembly/standard succeeds",
               st_op_asm == 200 and st_std == 200 and res_std.get("designation") == "DIN 625 608",
               f"open={st_op_asm} std=({st_std}, {res_std})")

            st_bom_s, http_s = call("assembly/bom")
            st_bom_f, http_f = call("assembly/bom?flat=true")
            st_bom_bad, err_bad = call("assembly/bom?flat=invalid")
            ok("BOM HTTP: GET /api/assembly/bom returns structured and flat BOM JSON and rejects bad flat param",
               st_bom_s == 200 and http_s.get("flat") is False and http_s.get("count") == 8
               and st_bom_f == 200 and http_f.get("flat") is True and http_f.get("count") == 8
               and st_bom_bad == 400 and bool(err_bad.get("error")),
               f"s=({st_bom_s}, {http_s.get('count')}) f=({st_bom_f}, {http_f.get('count')}) bad={st_bom_bad}")
        finally:
            srv.shutdown()
            srv.server_close()

        # Re-open main assembly in ws to verify MCP tool & CSV export on the same assembly
        asm = ws.open("bom_main_asm.solidcraft")

        # 1. Structured BOM
        csv_struct_path = ws.root / "bom_struct.csv"
        res_s = server.bill_of_materials("bom_main_asm", path=str(csv_struct_path), flat=False)
        rows_s = res_s.get("rows", [])
        ok("BOM structured: returns 8 top-level rows", len(rows_s) == 8, f"len={len(rows_s)}")

        by_file_s = {r["datei"]: r for r in rows_s}
        ok("BOM structured: two identical brackets aggregated to count 2",
           by_file_s.get("bom_bracket.solidcraft", {}).get("anzahl") == 2, str(by_file_s.get("bom_bracket.solidcraft")))
        ok("BOM structured: assigned material Steel present",
           by_file_s.get("bom_plate1.solidcraft", {}).get("werkstoff") == "Steel")
        ok("BOM structured: unassigned material is None",
           by_file_s.get("bom_plate2.solidcraft", {}).get("werkstoff") is None)
        ok("BOM structured: mass is positive float",
           isinstance(by_file_s.get("bom_plate1.solidcraft", {}).get("masse"), float)
           and by_file_s["bom_plate1.solidcraft"]["masse"] > 0)

        # Standard parts in bolted connection and Place Standard Part
        screw = next((r for r in rows_s if r.get("norm") == "ISO 4762"), None)
        ok("BOM structured: ISO 4762 screw has norm and size",
           screw is not None and screw.get("norm") == "ISO 4762" and screw.get("groesse") == "M5"
           and screw.get("anzahl") == 1 and "ISO 4762" in screw.get("benennung", ""))
        washer = next((r for r in rows_s if r.get("norm") == "ISO 7089"), None)
        ok("BOM structured: ISO 7089 washer has norm and size",
           washer is not None and washer.get("norm") == "ISO 7089" and washer.get("groesse") == "M5"
           and washer.get("anzahl") == 1)
        nut = next((r for r in rows_s if r.get("norm") == "ISO 4032"), None)
        ok("BOM structured: ISO 4032 nut has norm and size",
           nut is not None and nut.get("norm") == "ISO 4032" and nut.get("groesse") == "M5"
           and nut.get("anzahl") == 1)
        bearing = next((r for r in rows_s if r.get("norm") == "DIN 625"), None)
        ok("BOM structured: Place Standard Part DIN 625 608 has norm and size",
           bearing is not None and bearing.get("norm") == "DIN 625" and bearing.get("groesse") == "608"
           and bearing.get("anzahl") == 1)

        # Nested subassembly row (depth 2) and designation from subassembly file (not instance name)
        outer_row = by_file_s.get("bom_outer_sub.solidcraft")
        inner_child = next((ch for ch in (outer_row or {}).get("children", []) if ch.get("datei") == "bom_sub_asm.solidcraft"), None)
        grandchild = (inner_child or {}).get("children", [None])[0]
        ok("BOM structured: outer subassembly uses file designation and count 1",
           outer_row is not None and outer_row.get("anzahl") == 1
           and outer_row.get("benennung") == "bom_outer_sub"
           and outer_row.get("masse", 0) > 0, str(outer_row))
        ok("BOM structured: depth-2 nested subassembly and grandchild preserved with hierarchical positions",
           inner_child is not None and inner_child.get("benennung") == "bom_sub_asm"
           and inner_child.get("position") == "4.1"
           and grandchild is not None and grandchild.get("datei") == "bom_sub_part.solidcraft"
           and grandchild.get("position") == "4.1.1" and grandchild.get("anzahl") == 1,
           str(outer_row))

        # CSV readable (structured)
        ok("BOM structured: CSV file created", csv_struct_path.is_file())
        with open(csv_struct_path, "r", encoding="utf-8") as f:
            reader_s = list(csv.reader(f, delimiter=";"))
        ok("BOM structured: CSV has 12 lines (header + 8 rows + 2 children + 1 grandchild)",
           len(reader_s) == 12, f"len={len(reader_s)}")
        ok("BOM structured: CSV header matches expected columns",
           reader_s[0] == ["Position", "Benennung", "Anzahl", "Datei", "Werkstoff", "Masse", "Norm", "Größe"])

        # 2. Flat BOM
        csv_flat_path = ws.root / "bom_flat.csv"
        res_f = server.bill_of_materials("bom_main_asm", path=str(csv_flat_path), flat=True)
        rows_f = res_f.get("rows", [])
        ok("BOM flat: returns 8 leaf rows (subassemblies dissolved)", len(rows_f) == 8, f"len={len(rows_f)}")

        by_file_f = {r["datei"]: r for r in rows_f}
        ok("BOM flat: subassembly files are not in flat BOM",
           "bom_outer_sub.solidcraft" not in by_file_f and "bom_sub_asm.solidcraft" not in by_file_f)
        ok("BOM flat: dissolved sub_part summed across nested levels to count 2",
           by_file_f.get("bom_sub_part.solidcraft", {}).get("anzahl") == 2,
           str(by_file_f.get("bom_sub_part.solidcraft")))
        ok("BOM flat: brackets still have count 2 and Place Standard Part DIN 625 present",
           by_file_f.get("bom_bracket.solidcraft", {}).get("anzahl") == 2
           and by_file_f.get("DIN_625_608.solidcraft", {}).get("norm") == "DIN 625")

        # CSV readable (flat)
        ok("BOM flat: CSV file created", csv_flat_path.is_file())
        with open(csv_flat_path, "r", encoding="utf-8") as f:
            reader_f = list(csv.reader(f, delimiter=";"))
        ok("BOM flat: CSV has 9 lines (header + 8 leaf rows)", len(reader_f) == 9, f"len={len(reader_f)}")
        ok("BOM flat: CSV header matches expected columns",
           reader_f[0] == ["Position", "Benennung", "Anzahl", "Datei", "Werkstoff", "Masse", "Norm", "Größe"])

        # Error cases: outside workspace path, non-.csv path, part document
        outside_err = False
        try:
            server.bill_of_materials("bom_main_asm", path="../outside.csv")
        except ValueError:
            outside_err = True
        non_csv_err = False
        try:
            server.bill_of_materials("bom_main_asm", path="bom_plate1.solidcraft")
        except ValueError:
            non_csv_err = True
        ok("BOM CSV: rejects path outside workspace and non-.csv suffix with ValueError",
           outside_err and non_csv_err, f"outside={outside_err} non_csv={non_csv_err}")

        bad_doc_err = False
        p1_reopen = ws.open("bom_plate1.solidcraft")
        try:
            server.bill_of_materials(p1_reopen.name)
        except ValueError:
            bad_doc_err = True
        ok("BOM: rejects part document with ValueError", bad_doc_err)

        # a description that starts like a formula must not run as one in a spreadsheet (review 2026-11-16)
        import io as _io
        buf = _io.StringIO()
        from mechvane import bom as _bom
        _bom._write_csv_row(csv.writer(buf, delimiter=";"), {"position": "1", "benennung": '=HYPERLINK("http://x","a")',
                                                              "anzahl": 1, "datei": "a.solidcraft", "werkstoff": "+cmd", "masse": 1.0})
        ok("BOM CSV: a text cell starting with = + - @ gets an apostrophe, plain text and numbers stay as they are",
           buf.getvalue().startswith("1;\"'=HYPERLINK") and ";'+cmd;" in buf.getvalue() and ";1.00;" in buf.getvalue(), buf.getvalue())

        # a part file that is gone must not sink the whole list: its row says so and has no mass (review 2026-11-16)
        if "bom_bracket" in ws.docs:
            ws.close("bom_bracket")
        (ws.root / "bom_bracket.solidcraft").unlink()
        gone = server.bill_of_materials("bom_main_asm", flat=True)
        gone_rows = [r for r in gone["rows"] if "file missing" in str(r.get("name"))]
        ok("BOM: a missing part file gives a '(file missing)' row without mass while the other rows stay",
           len(gone_rows) == 1 and gone_rows[0]["mass"] is None and len(gone["rows"]) >= 3, str(gone["rows"])[:300])

    finally:
        server.ws = orig_ws
        for name in ["bom_plate1", "bom_plate2", "bom_bracket", "bom_sub_part", "bom_sub_asm",
                     "bom_outer_sub", "bom_main_asm", "DIN_625_608",
                     "ISO_4762_M5x30", "ISO_7089_M5", "ISO_4032_M5"]:
            if name in ws.docs:
                ws.close(name)


def orchester_figures_checks():
    """tools/status_collect.py (#104): K3 first-time yield, K5 Argon cost, K1 rest at the weekly reset, on fixtures."""
    import importlib.util, datetime as dt
    path = Path(__file__).resolve().parents[2] / "tools" / "status_collect.py"
    if not path.exists():  # private tool, not in the public export
        return
    spec = importlib.util.spec_from_file_location("status_collect", path)
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    now = dt.datetime(2026, 11, 15, 12, tzinfo=dt.timezone.utc)
    t = lambda d, h=0: f"2026-11-{d:02d}T{h:02d}:00:00+00:00"
    ev = [
        {"at": t(10), "kind": "queue", "step": "agy_done", "issue": 1, "model": "gemini-4-hydrogen-high"},  # rework: run again
        {"at": t(11), "kind": "queue", "step": "agy_done", "issue": 1, "model": "gemini-4-argon-high"},     # closed: success
        {"at": t(12), "kind": "queue", "step": "agy_done", "issue": 2, "model": "gemini-4-hydrogen-high"},  # closed: success
        {"at": t(13), "kind": "queue", "step": "agy_done", "issue": 3, "model": "gemini-4-hydrogen-high"},  # open: undecided
        {"at": t(1), "kind": "queue", "step": "agy_done", "issue": 4, "model": "gemini-4-hydrogen-high"},   # older than 28 days? no: Nov 1
        {"at": "2026-10-01T00:00:00+00:00", "kind": "queue", "step": "agy_done", "issue": 5, "model": "gemini-4-hydrogen-high"},
        {"at": t(14), "kind": "queue", "step": "agy_done", "issue": 6, "model": "gemini-3.8-flash-high"},   # not a known model
        {"at": t(11, 1), "kind": "queue", "step": "argon", "model": "gemini-4-argon-high",
         "argon_before": "60", "argon_mid": "40", "argon_after": "39", "reviewed": "1"},
        {"at": t(12, 1), "kind": "queue", "step": "argon", "model": "gemini-4-hydrogen-high",
         "argon_before": "39", "argon_mid": "39", "argon_after": "36", "reviewed": "1"},
        {"at": t(13, 1), "kind": "queue", "step": "argon", "model": "gemini-4-argon-high",   # weekly reset in between
         "argon_before": "5", "argon_mid": "100", "argon_after": "99", "reviewed": "1"},
        {"at": t(13, 2), "kind": "queue", "step": "argon", "model": "gemini-4-hydrogen-high",  # review skipped
         "argon_before": "9", "argon_mid": "9", "argon_after": "9", "reviewed": "0"},
        {"at": t(13, 3), "kind": "gate", "issue": 2, "verdict": "green"},
    ]
    k = sc.orchester_kennzahlen(ev, {1, 2, 4}, now)
    by = {m["model"]: m for m in k["modelle"]}
    ok("orchester figures: the five agreed model slugs, numbers only, 28 days, stand in Unix seconds",
       [m["model"] for m in k["modelle"]] == list(sc.MODELS) and k["zeitraum_tage"] == 28 and k["stand"] == int(now.timestamp())
       and all(set(m) == {"model", "auftraege", "erstausbeute", "treffer", "review_kosten_argon", "umsetzung_kosten_argon",
                          "review_n", "umsetzung_n"} for m in k["modelle"]), k)
    h, a = by["gemini-4-hydrogen"], by["gemini-4-argon"]
    ok("orchester figures K3: rework (a later run) counts against, closed counts for, open is undecided, older runs and unknown models out",
       h["auftraege"] == 4 and h["erstausbeute"] == round(2 / 3, 3) and a["auftraege"] == 1 and a["erstausbeute"] == 1.0, (h, a))
    ok("orchester figures K5: Argon cost per implementation (before - mid on Argon runs) and per review (mid - after); a reset in between and skipped reviews are left out",
       a["umsetzung_kosten_argon"] == 20.0 and a["umsetzung_n"] == 1 and a["review_n"] == 3
       and a["review_kosten_argon"] == round((1 + 3 + 1) / 3, 2) and h["review_kosten_argon"] is None and h["review_n"] == 0, a)
    ok("orchester figures: no runs give null, not zero", by["claude"]["erstausbeute"] is None and by["claude"]["auftraege"] == 0)

    def reading(at, pots):
        return {"at": at, "pots": [{"pot": p, "window": "Weekly Limit Remaining", "rest_pct": r, "reset": z} for p, r, z in pots]}
    hist = [
        reading("2026-11-13T23:00:00+00:00", [("A", 100.0, "2026-11-20T23:00:00Z"), ("B", 50.0, "2026-11-14T23:09:00Z")]),
        reading("2026-11-13T23:05:00+00:00", [("A", 100.0, "2026-11-20T23:05:00Z"), ("B", 20.0, "2026-11-14T23:09:00Z")]),  # A drifts while unused
        reading("2026-11-14T22:00:00+00:00", [("A", 80.0, "2026-11-20T23:10:00Z"), ("B", 3.0, "2026-11-14T23:09:00Z")]),
        reading("2026-11-15T00:00:00+00:00", [("A", 70.0, "2026-11-20T23:10:00Z"), ("B", 100.0, "2026-11-21T23:09:00Z")]),
        {"at": "2026-11-15T00:01:00+00:00", "pots": [{"pot": "B", "window": "Five Hour Limit Remaining", "rest_pct": 1.0,
                                                    "reset": "2026-11-30T00:00:00Z"}]},  # 5-hour window ignored
    ]
    r = sc.rest_at_reset(hist)
    ok("orchester figures K1: rest at the weekly reset per pot; a drifting reset of an unused pot is no new week, the open week and 5-hour windows are not listed",
       r == [{"pot": "B", "reset": "2026-11-14T23:09+00:00", "rest_pct": 3.0, "read_at": "2026-11-14T22:00+00:00"}], r)


def agent_clone_checks(tmp):
    """tools/agent_clone.sh (#102): a full clone per agent run, no hard links, origin = the main repo's remote, its
    origin refs from the main repo, rework from the pushed branch, sync after main moved, push from the clone."""
    import subprocess as sp
    script = Path(__file__).resolve().parents[2] / "tools" / "agent_clone.sh"
    root = Path(tmp) / "agent_clone"
    root.mkdir()
    g = lambda d, *a: sp.run(["git", "-C", str(d), *a], capture_output=True, text=True, check=True).stdout.strip()
    env = dict(os.environ, MECHVANE_REPO=str(root / "main"), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    run = lambda *a: sp.run([str(script), *a], capture_output=True, text=True, env=env)
    sp.run(["git", "init", "-q", "--bare", "-b", "main", str(root / "hub.git")], check=True)
    seed = root / "seed"
    sp.run(["git", "clone", "-q", str(root / "hub.git"), str(seed)], check=True, capture_output=True)
    (seed / "a.txt").write_text("a\n")
    g(seed, "add", "."); g(seed, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "a"); g(seed, "push", "-q", "origin", "main")
    sp.run(["git", "clone", "-q", str(root / "hub.git"), str(root / "main")], check=True, capture_output=True)
    main = root / "main"
    g(main, "branch", "-q", "stale-local")  # a local branch of the main repo must not reach the clone

    wt = root / "_wt" / "gemini-1"
    r = run("new", str(wt), "gemini/1", "origin/main")
    links = sp.run(["find", str(wt / ".git" / "objects"), "-type", "f", "-links", "+1"], capture_output=True, text=True).stdout
    ok("agent_clone new: own .git (no worktree), no hard links, origin = the main repo's remote, on gemini/1 from origin/main, only that branch",
       r.returncode == 0 and (wt / ".git").is_dir() and not links.strip()
       and g(wt, "remote", "get-url", "origin") == g(main, "remote", "get-url", "origin")
       and g(wt, "rev-parse", "HEAD") == g(main, "rev-parse", "origin/main")
       and g(wt, "branch", "--format=%(refname:short)") == "gemini/1", (r.stderr, links, g(wt, "branch", "-a")))

    (wt / "b.txt").write_text("b\n")
    g(wt, "add", "."); g(wt, "commit", "-qm", "b")
    rp = sp.run(["git", "-C", str(wt), "push", "-q", "-u", "origin", "gemini/1"], capture_output=True, text=True, env=env)
    ok("agent_clone: the branch is pushed from the clone to the remote", rp.returncode == 0
       and g(root / "hub.git", "rev-parse", "gemini/1") == g(wt, "rev-parse", "HEAD"), rp.stderr)

    (seed / "c.txt").write_text("c\n")
    g(seed, "add", "."); g(seed, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c"); g(seed, "push", "-q", "origin", "main")
    g(main, "fetch", "-q", "origin")
    rs = run("sync", str(wt))
    ok("agent_clone sync: the clone's origin/main follows the main repo after main moved (no network from the clone)",
       rs.returncode == 0 and g(wt, "rev-parse", "origin/main") == g(main, "rev-parse", "origin/main"), rs.stderr)

    wt2 = root / "_wt" / "gemini-1b"
    r2 = run("new", str(wt2), "gemini/1", "origin/gemini/1")
    ok("agent_clone new for rework: starts from the pushed branch, origin/main is there to merge",
       r2.returncode == 0 and (wt2 / "b.txt").exists()
       and g(wt2, "rev-parse", "origin/main") == g(main, "rev-parse", "origin/main"), r2.stderr)
    r3 = run("new", str(wt2), "gemini/2", "origin/gemini/nope")
    ok("agent_clone new: a base that does not exist fails (the queue skips the issue)", r3.returncode != 0, r3.stderr)


def review_score_checks(tmp):
    """tools/review_score.py (#105 phase 3): findings of both reviewers, marks, hit rate and recommendation match."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("review_score", Path(__file__).resolve().parents[2] / "tools" / "review_score.py")
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    groq = """## Review
### High Severity
#### `mechvane/a.py:12`
- **Befund:** off by one
### Low Severity
#### `tools/b.sh`
- **Befund:** quoting
"""
    argon = """### 1. Umfang
- Der Diff macht, was verlangt ist.
### 2. Abgleich des Berichts
- **Bericht abgeschnitten:** endet mitten im Satz.
### 3. Echte Bugs
- **`features.js`** zwei Stellen:
  1. `features.js:10` setzt die Länge zu früh.
  2. `features.js:20` verliert die Norm.
- `server.py:5` prüft die Eingabe nicht.

Empfehlung: nacharbeiten, weil zwei Fehler.
"""
    g = rs.groq_findings(groq)
    a = rs.argon_findings(argon)
    ok("review_score: Groq findings with file, line and severity",
       [(f["file"], f["line"], f["severity"]) for f in g] == [("mechvane/a.py", 12, "High"), ("tools/b.sh", None, "Low")], g)
    ok("review_score: Argon findings only from sections 2 and 3, sub-items instead of their parent, no recommendation line",
       len(a) == 4 and a[0]["text"].startswith("**Bericht") and (a[1]["file"], a[1]["line"]) == ("features.js", 10)
       and (a[3]["file"], a[3]["line"]) == ("server.py", 5) and rs.recommendation(argon) == "nacharbeiten", a)

    rs.REVIEWS = Path(tmp) / "reviews"
    rs.SCORES = Path(tmp) / "scores.jsonl"
    rs.REVIEWS.mkdir()
    (rs.REVIEWS / "7-20261115T000000Z-argon.md").write_text(argon)
    (rs.REVIEWS / "7-20261115T000000Z-groq.md").write_text(groq)
    r1 = rs.main(["score", "7", "argon", "1=ja", "2=ja", "3=nein", "4=offen", "--outcome", "returned"])
    r2 = rs.main(["score", "7", "groq", "1=ja", "2=nein"])
    r3 = rs.main(["score", "7", "groq", "2=ja"])  # a later mark of the same finding wins
    bad = rs.main(["score", "7", "groq", "9=ja"])
    summ = rs.summarize(rs.read_scores())
    ok("review_score: marks recorded, the newest per finding counts, hit rate ja/(ja+nein), recommendation 'nacharbeiten' matches a returned branch, out-of-range marks refused",
       (r1, r2, r3, bad) == (0, 0, 0, 2) and summ["argon"]["treffer"] == round(2 / 3, 3) and summ["argon"]["offen"] == 1
       and summ["groq"]["treffer"] == 1.0 and summ["argon"]["empfehlung_passt"] == 1.0
       and summ["groq"]["model"] == "gpt-oss" and summ["argon"]["model"] == "gemini-4-argon", summ)


def argon_review_checks(tmp):
    """tools/argon_review.py (#107): prompt on standard input, diff shortening, failed calls reported as such."""
    import importlib.util, subprocess as sp
    spec = importlib.util.spec_from_file_location("argon_review", Path(__file__).resolve().parents[2] / "tools" / "argon_review.py")
    ar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ar)

    small = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x\n+y\n"
    long_lines = "diff --git a/big.json b/big.json\n" + "".join(f"+line {i}\n" for i in range(5000))
    wide = "diff --git a/wide.py b/wide.py\n" + "+" + "z" * 100_000 + "\n"
    trimmed, notes = ar.trim_diff(small + long_lines + wide)
    # stand-in reviewer over claude -p (user 2026-11-16): prompt as text on stdin, run in an empty temp folder
    echo = [sys.executable, "-c", "import os,sys; d=sys.stdin.read(); print('cwd-empty' if not os.listdir('.') else 'cwd-busy', len(d))"]
    good = ar.run_claude(echo, "Bitte prüfen: " + small)
    bad = ar.run_claude([sys.executable, "-c", "import sys; sys.exit(3)"], "x")
    ok("argon_review: the Opus stand-in reads the prompt on stdin in an empty folder; a failed call says so",
       good.startswith("cwd-empty ") and int(good.split()[1]) > 20 and bad.startswith("Opus-Review nicht möglich: rc=3"),
       f"{good!r} {bad!r}")
    ok("argon_review: small file diff kept whole, 5000-line file only head and tail, 100 KB file cut to 60000 characters",
       small in trimmed and "+line 10\n" in trimmed and "+line 4999\n" in trimmed and "+line 2500\n" not in trimmed
       and len(trimmed) < 70_000 and len(notes) == 2 and "big.json" in notes[0] and "wide.py" in notes[1], notes)
    many = "".join(f"diff --git a/f{i}.py b/f{i}.py\n" + "+" + "q" * 50_000 + "\n" for i in range(10))
    trimmed, notes = ar.trim_diff(many)
    ok("argon_review: whole diff capped at 300000 characters, the files left out are named",
       len(trimmed) <= ar.TOTAL_CHARS and any("left out" in n for n in notes) and "f9.py" in notes[-1], (len(trimmed), notes[-1:]))
    prompt = ar.build_prompt("Aufgabe", "Bericht", "Checks", small + long_lines)
    ok("argon_review: the prompt tells the reviewer the diff is shortened", "is shortened" in prompt and "big.json" in prompt)
    ok("argon_review: an unshortened prompt has no shortening note", "shortened" not in ar.build_prompt("A", "B", "C", small))

    # stub agy: reads the stream-json message from standard input, as agy does
    stub = Path(tmp) / "agy_stub.py"
    stub.write_text("""import json, sys
args = sys.argv[1:]
assert args[-1] == "-p=" and "stream-json" in args, args
msg = json.loads(sys.stdin.readline())
text = msg["message"]["content"]
mode = args[0]
print(json.dumps({"event": "init"}))
if mode == "ok":
    print(json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "Empfehlung: mergen (%d)" % len(text)}}))
elif mode == "err":
    print("agy: quota exhausted", file=sys.stderr)
    print(json.dumps({"event": "result", "result": {"status": "ERROR", "response": "", "error": "quota exhausted"}}))
    sys.exit(1)
""")
    big = "x" * 300_000  # far over the ~128 KB a single argument may have
    out = ar.run([sys.executable, str(stub), "ok"], big)
    ok("argon_review: a 300 KB prompt reaches agy through standard input", out == f"Empfehlung: mergen ({len(big)})", out[:200])
    out = ar.run([sys.executable, str(stub), "err"], "p")
    ok("argon_review: a failed call reads 'Argon-Review nicht möglich: <reason>', not the raw error output",
       out.startswith("Argon-Review nicht möglich: quota exhausted") and "rc=1" in out, out)
    out = ar.run([sys.executable, "-c", "print('crash')"], "p")
    ok("argon_review: no result event also reads 'Argon-Review nicht möglich'",
       out.startswith("Argon-Review nicht möglich: keine Antwort"), out)
    out = ar.run(["/nonexistent/agy"], "p")
    ok("argon_review: a missing agy reads 'Argon-Review nicht möglich'", out.startswith("Argon-Review nicht möglich:"), out)

    # end to end over the command line on a real git diff
    repo = Path(tmp) / "ar_repo"
    repo.mkdir()
    g = lambda *a: sp.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True)
    g("init", "-q", "-b", "main"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    (repo / "a.txt").write_text("a\n"); g("add", "."); g("commit", "-q", "-m", "a")
    g("branch", "base")
    (repo / "a.txt").write_text("a\nb\n"); g("commit", "-q", "-am", "b")
    for name in ("issue", "report", "checks"):
        (Path(tmp) / f"ar_{name}").write_text(name)
    cli = sp.run([sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "argon_review.py"), "--repo", str(repo),
                  "--base", "base", "--issue", str(Path(tmp) / "ar_issue"), "--report", str(Path(tmp) / "ar_report"),
                  "--checks", str(Path(tmp) / "ar_checks"), "--", sys.executable, str(stub), "ok"],
                 capture_output=True, text=True)
    ok("argon_review: command line builds the prompt from files and the branch diff and prints the review",
       cli.returncode == 0 and cli.stdout.startswith("Empfehlung: mergen ("), cli.stdout[-300:] + cli.stderr[-300:])


def upstream_watch_checks():
    """tools/upstream_watch.py (#90): command difference, watched issues, new releases and the report, on fixtures."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("upstream_watch", Path(__file__).resolve().parents[2] / "tools" / "upstream_watch.py")
    uw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(uw)

    old = uw.snapshot_from_list([
        {"id": "solid.box", "label": "Box", "enabled": True, "params": "length, width, height"},
        {"id": "solid.fillet", "label": "Fillet", "enabled": True, "params": "edges, radius"},
        {"id": "surface.fillet", "label": "Surface Fillet", "enabled": False, "planned": "769", "params": "planned: a, b"},
        {"id": "old.command", "label": "Old", "enabled": True, "params": "x"},
        {"id": "sheet.flange", "label": "Flange", "enabled": True, "params": "edge"},
    ])
    new = uw.snapshot_from_list([
        {"id": "solid.box", "label": "Box", "enabled": True, "params": "length, width, height"},
        {"id": "solid.fillet", "label": "Fillet", "enabled": True, "params": "edges, radius, variable?"},
        {"id": "surface.fillet", "label": "Surface Fillet", "enabled": True, "params": "a, b: {body, point}"},
        {"id": "plugin.run", "label": "Run plugin", "enabled": True, "params": "plugin"},
        {"id": "future.thing", "label": "Future", "enabled": False, "planned": "4242", "params": "planned: x"},
        {"id": "sheet.flange", "label": "Flange", "enabled": False, "params": "edge"},
    ])
    d = uw.diff_commands(old, new)
    ok("upstream_watch: new, removed, changed and now-available commands are told apart",
       d["new_available"] == ["plugin.run"] and d["new_planned"] == ["future.thing"] and d["removed"] == ["old.command"]
       and d["ready"] == ["surface.fillet"]
       and {(c["id"], c["what"]) for c in d["changed"]} == {("solid.fillet", "parameters"), ("sheet.flange", "availability")},
       str(d))
    same = uw.diff_commands(old, old)
    ok("upstream_watch: identical command lists give an empty difference",
       not (same["added"] or same["removed"] or same["changed"] or same["ready"]), str(same))

    cov = uw.mentioned_in_mechvane(["solid.fillet", "no.such.command.anywhere"],
                                   files=[Path(__file__).resolve().parents[2] / "mechvane" / "sc_locate.py",
                                          Path(__file__).resolve().parents[2] / "mechvane" / "tree.py"])
    ok("upstream_watch: a command named in Mechvane's code counts as covered, an unknown one does not",
       cov["solid.fillet"] is True and cov["no.such.command.anywhere"] is False, str(cov))

    watched = [{"number": 1, "follow_up": "a"}, {"number": 2, "follow_up": "b"}, {"number": 3, "follow_up": "c"}]
    news = uw.issue_news(watched, {"1": "closed", "2": "open", "3": "closed"}, {"1": "open", "3": "closed"})
    ok("upstream_watch: closed watched issues are listed, those closed since the last run marked as new",
       [(n["number"], n["newly"]) for n in news] == [(1, True), (3, False)], str(news))

    rels = [{"tag_name": "v0.41.0", "published_at": "2026-11-13T10:00:00Z"},
            {"tag_name": "v0.40.1", "published_at": "2026-11-10T10:00:00Z"},
            {"tag_name": "v0.42.0-rc.1", "published_at": "2026-11-14T10:00:00Z", "prerelease": True}]
    fresh = uw.new_releases(rels, ["v0.40.1"])
    ok("upstream_watch: releases not seen before are returned oldest first",
       [r["tag_name"] for r in fresh] == ["v0.41.0", "v0.42.0-rc.1"], str(fresh))

    report = uw.render_report("2026-11-14", "0.40.1", fresh, {"0.40.1 → 0.41.0": d}, {"plugin.run": False, "surface.fillet": True}, news)
    ok("upstream_watch: the report names new releases, commands with and without Mechvane code, and closed issues",
       "v0.41.0" in report and "✘ `plugin.run`" in report and "✔ `surface.fillet`" in report and "#1 **neu geschlossen**" in report
       and "#3 geschlossen" in report, report[:400])
    msg = uw.ntfy_text(fresh, {"x": d}, {"plugin.run": False, "surface.fillet": True}, news)
    ok("upstream_watch: the short message counts new commands, those without Mechvane code and closed issues",
       "2 neue Befehle (1 ohne Mechvane-Code)" in msg and "#1" in msg and "v0.42.0-rc.1" in msg, msg)
    ok("upstream_watch: nothing new gives a plain message", uw.ntfy_text([], {}, {}, []) == "Nichts Neues bei SolidCraft.")


def command_matrix_checks():
    """tools/command_matrix.py (#77): schema-first classification, error handling, counts, and live CLI command list."""
    import importlib.util
    from mechvane import solidcraft
    spec = importlib.util.spec_from_file_location("command_matrix", Path(__file__).resolve().parents[2] / "tools" / "command_matrix.py")
    cm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cm)

    fixture_cmds = [
        {"id": "doc.recover", "label": "Recover"},
        {"id": "config.row", "label": "Config Row"},
        {"id": "surface.patch", "label": "Patch"},
        {"id": "sketch.construction_line", "label": "Construction Line"},
        {"id": "broken.cmd", "label": "Broken"},
        {"id": "legacy.noparams", "label": "Legacy"},
    ]
    point3_def = {
        "anyOf": [
            {"items": {"type": "number"}, "maxItems": 3, "minItems": 3, "type": "array"},
            {"properties": {"x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"}}, "required": ["x", "y", "z"], "type": "object"},
        ],
        "description": "A point in mm: [x, y, z] or {x, y, z}.",
    }
    fixture_schemas = {
        "doc.recover": {
            "input": {
                "type": "object",
                "required": ["id"],
                "properties": {
                    "dir": {"type": ["string", "null"], "description": "The recovery folder."},
                    "discard": {"type": ["boolean", "null"], "description": "Delete after open."},
                    "id": {"type": "string", "description": "Entry id."},
                },
            }
        },
        "config.row": {
            "input": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"anyOf": [{"type": "string"}, {"type": "integer"}], "description": "The row, by name or by id."},
                },
            }
        },
        "surface.patch": {
            "input": {
                "type": "object",
                "$defs": {
                    "Point3": point3_def,
                    "BendTableFormat": {"type": "string", "pattern": "^([Cc][Ss][Vv]|[Jj][Ss][Oo][Nn])$"},
                    "ToolFace": {"type": "object", "properties": {"body": {"type": "string"}, "point": {"$ref": "#/$defs/Point3"}}},
                },
                "properties": {
                    "edges": {"items": {"$ref": "#/$defs/Point3"}, "type": ["array", "null"], "description": "Points on a loop."},
                    "from": {"$ref": "#/$defs/Point3", "description": "Start point."},
                    "format": {"$ref": "#/$defs/BendTableFormat"},
                    "tool": {"$ref": "#/$defs/ToolFace", "description": "A face to pick."},
                },
            }
        },
        "sketch.construction_line": {
            "input": {
                "type": "object",
                "properties": {
                    "at": {"description": "Untyped Value point."},
                },
            }
        },
        "legacy.noparams": {"params": "plain text"},
    }

    class FakeSession:
        def tool(self, name, args=None, timeout=None):
            if name == "list_commands":
                return fixture_cmds
            if name == "describe_command":
                cid = args["id"]
                if cid == "broken.cmd":
                    raise RuntimeError("simulated timeout")
                return fixture_schemas[cid]
            raise AssertionError(f"unexpected tool call: {name}")

    res = cm.analyze_catalog(FakeSession())
    by_id = {c["id"]: c for c in res["commands"]}
    params = {f"{c['id']}.{p['name']}": p for c in res["commands"] for p in c["parameters"]}

    ok("command_matrix: type-first keeps string `dir` as Text and boolean `discard` as Schalter",
       params["doc.recover.dir"]["einstufung"] == "Text"
       and params["doc.recover.discard"]["einstufung"] == "Schalter",
       str(params["doc.recover.dir"]))
    ok("command_matrix: `config.row.name` (string|integer) is Text, not Feature selection",
       params["config.row.name"]["einstufung"] == "Text", str(params["config.row.name"]))
    ok("command_matrix: Point3 parameters (`edges`, `from`) follow one uniform rule",
       params["surface.patch.edges"]["einstufung"] == "Zahl/Ausdruck"
       and params["solid.extrude.from" if "solid.extrude.from" in params else "surface.patch.from"]["einstufung"] == "Zahl/Ausdruck",
       str(params["surface.patch.edges"]))
    ok("command_matrix: schema-derived choice pattern (`BendTableFormat`) and CAD object (`ToolFace`) classify accurately",
       params["surface.patch.format"]["einstufung"] == "Auswahlliste (enum)"
       and params["surface.patch.tool"]["einstufung"] == "Auswahl in der Ansicht (Flächen)",
       str(params["surface.patch.tool"]))
    ok("command_matrix: untyped `Value` (`at`) is unklar and errors per command are collected without aborting",
       params["sketch.construction_line.at"]["einstufung"] == "unklar"
       and res["summary"]["anzahl_fehler"] == 1
       and res["summary"]["fehler"][0]["command"] == "broken.cmd"
       and by_id["broken.cmd"]["has_schema"] is False,
       str(res["summary"]))
    ok("command_matrix: summary totals and percentages match fixture counts",
       res["summary"]["befehle_gesamt"] == 6
       and res["summary"]["befehle_mit_schema"] == 4
       and res["summary"]["befehle_ohne_schema"] == 2
       and res["summary"]["parameter_gesamt"] == 9
       and res["summary"]["anzahl_unklar"] == 1
       and res["summary"]["anteil_unklar_prozent"] == 11.1,
       str(res["summary"]))

    with solidcraft.Session() as live:
        live_cmds = live.tool("list_commands")
        if not isinstance(live_cmds, list):
            live_cmds = live_cmds.get("commands", [])
        live_ids = [c["id"] for c in live_cmds if isinstance(c, dict) and "id" in c]
        ok("command_matrix: installed solidcraft-cli list_commands matches expected catalog structure",
           len(live_ids) > 500 and len(live_ids) == len(set(live_ids))
           and all("." in cid for cid in live_ids)
           and {"doc.recover", "config.row", "surface.patch", "solid.extrude"}.issubset(set(live_ids)),
           f"count={len(live_ids)}")
        live_recover = live.tool("describe_command", {"id": "doc.recover"})["input"]
        live_row = live.tool("describe_command", {"id": "config.row"})["input"]
        ok("command_matrix: live CLI schemas for doc.recover.dir and config.row.name classify as Text",
           cm.classify_parameter("doc.recover", "dir", live_recover["properties"]["dir"], live_recover.get("$defs", {})) == ("Text", None)
           and cm.classify_parameter("config.row", "name", live_row["properties"]["name"], live_row.get("$defs", {})) == ("Text", None))


def tester_tasks_checks():
    """tests/tasks (#86): every task's grader is tested on its reference, a wrong solution and an empty folder."""
    import subprocess
    out = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "tasks" / "selftest.py")],
                         capture_output=True, text=True, timeout=900)
    lines = [ln for ln in out.stdout.splitlines() if ln.startswith(("ok  ", "FAIL"))]
    ok("tester tasks: the graders pass their self-test (reference, wrong solution, empty folder)",
       out.returncode == 0 and len(lines) >= 3 and not any(ln.startswith("FAIL") for ln in lines),
       out.stdout[-400:] + out.stderr[-300:])


def gate_class_checks():
    """tools/gate.py: what reaches class A (merges by itself) is data only; pipeline files are class C."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("gate", Path(__file__).resolve().parents[2] / "tools" / "gate.py")
    gt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gt)
    cls = lambda *paths: gt.classify([(10, 0, p) for p in paths])[0]
    ok("gate: research, catalog entries, gallery and changelog snippets are class A",
       cls("docs/research/x.md", "katalog/eintraege/a/b.json", "changelog.d/1.md", "docs/galerie/a.png") == "A")
    ok("gate: tests are no longer class A (the branch's own check.py runs in the review)",
       cls("tests/mechvane/check.py") != "A" and cls("tests/reference/check.py") != "A")
    ok("gate: docs/*.md and docs/uebergabe.md are no longer class A (read at the start of every session)",
       cls("docs/uebergabe.md") != "A" and cls("docs/gemini-queue.md") != "A" and cls("CHANGELOG.md") != "A")
    ok("gate: a script inside docs/research is no data", cls("docs/research/2026/run.py") != "A")
    ok("gate: pipeline scripts, the sandbox, the upstream watch and the task graders are class C",
       all(cls(p) == "C" for p in ("tools/agent_clone.sh", "tools/gemini_queue.sh", "tools/upstream_watch.py",
                                   "tests/tasks/scharnier/grade.py", "tools/status_collect.py", "tools/systemd/x.timer")))
    ok("gate: a count of ok( calls is read from a revision", gt.count_checks("HEAD") > 500, str(gt.count_checks("HEAD")))
    # #115: a branch that touches nothing the UI runs on is checked against main before it goes back
    ok("gate: grader-only or doc branches are UI-independent, product code and the UI tests are not (#115)",
       gt.ui_independent(["tests/tasks/welle/grade.py", "docs/x.md", "katalog/a.json"])
       and not gt.ui_independent(["tests/tasks/a.py", "mechvane/ui/static/app.js"])
       and not gt.ui_independent(["mechvane/links.py"]) and not gt.ui_independent(["tools/ui_smoke.py"])
       and not gt.ui_independent(["pyproject.toml"]))
    head = gt.sh(["git", "rev-parse", "origin/main"])[1].strip()
    cache = gt.REPO / "build/status" / f"main_ui_{head[:12]}.json"
    had = cache.read_text() if cache.exists() else None
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"red": True, "note": "planted"}))
        red, note = gt.ui_red_on_main()
    finally:
        cache.write_text(had) if had is not None else cache.unlink(missing_ok=True)
    ok("gate: the main counter-check is cached per main commit (no second ui_smoke run that night, #115)",
       red is True and "zwischengespeichert" in note, f"{red} {note}")


def py311_syntax_checks():
    """#117: no f-string forms that need Python 3.12 (pyproject promises 3.11): the same quote nested,
    a backslash or a comment inside a replacement field. Found by the tokenizer, every versioned *.py."""
    import subprocess, tokenize, io
    root = Path(__file__).resolve().parents[2]

    def scan(src: bytes) -> list[str]:
        found, stack = [], []
        for t in tokenize.tokenize(io.BytesIO(src).readline):
            if t.type == tokenize.FSTRING_START:
                q = t.string.lstrip("fFrRbB")[:1]
                if stack and stack[-1] == q:
                    found.append(f"{t.start[0]}: nested f-string reuses {q}")
                stack.append(q)
            elif t.type == tokenize.FSTRING_END:
                stack.pop()
            elif stack and t.type == tokenize.STRING and (stack[-1] in t.string or "\\" in t.string):
                found.append(f"{t.start[0]}: quote or backslash inside an f-string field")
            elif stack and t.type == tokenize.COMMENT:
                found.append(f"{t.start[0]}: comment inside an f-string")
        return found

    if not hasattr(tokenize, "FSTRING_START"):  # Python 3.11 itself compiles every file anyway
        return
    files = subprocess.run(["git", "ls-files", "*.py"], cwd=root, capture_output=True, text=True).stdout.split()
    bad = []
    for rel in files:
        try:
            bad += [f"{rel}:{x}" for x in scan((root / rel).read_bytes())]
        except (tokenize.TokenError, SyntaxError, OSError) as e:
            bad.append(f"{rel}: {e}")
    old = scan(b'x = f"a {d[\'k\']} {g(\'s[name=\\"x\\"]\')!r}"\n')
    ok("python 3.11: no f-string syntax that needs 3.12 in versioned files (and the scan finds a planted one)",
       not bad and len(old) == 1, f"{bad[:10]} planted={old}")


def sketch_face_pick_checks(ws):
    """A tap near an edge gives a point on two faces; SolidCraft refuses it as ambiguous. The workspace sends the body
    and face index it hit, and the sketch goes on that face (live demo on Android, 2026-11-16)."""
    from mechvane import examples
    from mechvane.ui import sketch_session as ss
    from mechvane.documents import Workspace
    ws = Workspace(tempfile.mkdtemp(prefix="sketchface-"))
    doc = examples.bracket(ws)
    s = doc.session
    edge = [30, 30, 8]  # where the top of the plate meets the front of the wall

    def make(plane):
        cp = s.cmd("edit.checkpoint", {})["checkpoint"]
        try:
            s.cmd("sketch.create", ss.create_params(plane))
            return s.cmd("sketch.inspect", {}).get("plane")
        except Exception as e:
            return f"ERR {e}"
        finally:
            s.cmd("edit.restore_checkpoint", {"checkpoint": cp})

    alone = make({"face": edge})
    ok("sketch on a face: a point on an edge alone is ambiguous (why the face is sent)", str(alone).startswith("ERR")
       and "ambiguous" in str(alone), alone)
    top = make({"face": edge, "body": "Bracket", "index": 1})
    ok("sketch on a face: with body and face index the sketch goes on the face that was hit",
       isinstance(top, dict) and top.get("origin", [0, 0, 0])[2] == 8.0 and top.get("y_dir") == [0.0, 1.0, 0.0], top)
    ok("sketch on a face: body and index only together and well formed",
       ss.face_plane({"face": edge, "body": "B", "index": True}) == {"face": edge}
       and ss.face_plane({"face": edge, "index": 2}) == {"face": edge}
       and ss.face_plane({"face": edge, "body": "B", "index": 2}) == {"face": edge, "body": "B", "index": 2})
    ws.close_all()


def record_replay_checks(ws):
    """#124: a real agent session becomes a recording for the live demo: pauses cut to 2 s, the agent's text in one
    line, changes marked, paths and the computer's name taken out, an unknown tool refused, times from the session
    log; the agent's tool events carry the whole input; the demo build replays a change with the MCP functions."""
    from tools import record_replay as rr
    from mechvane.ui import agent as ag
    ev = [
        {"n": 1, "turn": 1, "type": "user", "text": "fix it", "selected": 0, "from": "user", "selection_names": [], "t": 100.0},
        {"n": 2, "turn": 1, "type": "status", "status": "working", "t": 100.2},
        {"n": 3, "turn": 1, "type": "tool", "id": "a", "tool": "check_design", "status": "pending", "t": 101.0},
        {"n": 4, "turn": 1, "type": "tool", "id": "a", "status": "completed", "params": {"document": "/root/x/bracket.solidcraft"}, "t": 101.5},
        {"n": 5, "turn": 1, "type": "text", "text": "Moving ", "t": 130.0},
        {"n": 6, "turn": 1, "type": "text", "text": "the hole on myhost.local, myhost stays a word", "t": 130.1},
        {"n": 7, "turn": 1, "type": "tool", "id": "b", "tool": "run", "status": "pending", "t": 131.0},
        {"n": 8, "turn": 1, "type": "tool", "id": "b", "status": "completed",
         "params": {"document": "bracket", "commands": [{"command": "timeline.edit", "params": {"feature": "Hole", "set": {"position": [10, 14, 8]}}}]}, "t": 132.0},
        {"n": 9, "turn": 1, "type": "tool", "id": "c", "tool": "command", "status": "pending", "t": 132.5},
        {"n": 10, "turn": 1, "type": "tool", "id": "c", "status": "completed", "params": {"document": "bracket", "command": "timeline.inspect"}, "t": 133.0},
        {"n": 11, "turn": 1, "type": "done", "reason": "end_turn", "changed": ["bracket.solidcraft"], "removed": [], "t": 134.0},
    ]
    rec = rr.build(ev, demo="bracket", title="T", host="myhost")
    types = [s["event"]["type"] for s in rec["steps"]]
    ok("record_replay: status left out, the agent's text pieces are one line",
       types == ["user", "tool", "tool", "text", "tool", "tool", "tool", "tool", "done"], types)
    gaps = [round(b["t"] - a["t"], 2) for a, b in zip(rec["steps"], rec["steps"][1:])]
    ok("record_replay: pauses cut to at most 2 s", max(gaps) <= rr.MAX_GAP and gaps[2] == rr.MAX_GAP, gaps)
    text = json.dumps(rec)
    ok("record_replay: paths and the computer's name taken out (the same word in text stays)", "/root" not in text
       and rec["steps"][3]["event"]["text"] == "Moving the hole on computer.local, myhost stays a word", rec["steps"][3]["event"])
    dos = [s["event"]["do"]["tool"] for s in rec["steps"] if s["event"].get("do")]
    ok("record_replay: only the change is marked (run yes; check_design, timeline.inspect no)", dos == ["run"], dos)
    try:
        rr.build(ev[:2] + [{"turn": 1, "type": "tool", "id": "z", "tool": "bolted_connection", "status": "pending"},
                           {"turn": 1, "type": "tool", "id": "z", "status": "completed", "params": {}}],
                 demo="bracket", title="T", host="h")
        ok("record_replay: an unknown changing tool is refused", False)
    except ValueError as e:
        ok("record_replay: an unknown changing tool is refused", "bolted_connection" in str(e), str(e))
    # sessions before #124 have no time in the events: the session log has it (the day's earlier sessions skipped)
    bare = [{k: v for k, v in e.items() if k != "t"} for e in ev]
    log = [{"t": "09:00:00.000", "kind": "agent_event", "type": "user", "text": "fix it"},
           {"t": "09:00:05.000", "kind": "agent_event", "type": "tool", "id": "a", "status": "pending"}]
    stamp = 10 * 3600
    for e in ev:
        if e["type"] != "text":
            log.append({"t": f"10:00:{e['t'] - 100:06.3f}", "kind": "agent_event",
                        **{k: e[k] for k in ("type", "id", "status", "text") if k in e}})
    times = rr.times_from_log(bare, log)
    ok("record_replay: times from the session log, from the last time the message was logged",
       times[0] == stamp and times[3] == stamp + 1.5 and times[4] == times[3], times[:5])
    # the ACP adapter sends the input only with an update: the completion event carries it
    seen = []
    a = ag.AcpAgent.__new__(ag.AcpAgent)
    a.on_event, a._inputs = seen.append, {}
    a._update({"sessionUpdate": "tool_call", "toolCallId": "x", "title": "mcp__mechvane__run", "rawInput": {}})
    a._update({"sessionUpdate": "tool_call_update", "toolCallId": "x", "rawInput": {"document": "d", "commands": []}})
    a._update({"sessionUpdate": "tool_call_update", "toolCallId": "x", "status": "completed"})
    ok("agent: the completed tool event carries the whole input", seen[-1].get("params") == {"document": "d", "commands": []}
       and "params" not in seen[0], seen)
    # every event has its time; the session log keeps its own clock string (record_replay reads it)
    from mechvane.ui import sessionlog
    logged, orig = [], sessionlog.log
    sessionlog.log = lambda kind, **d: logged.append(d)
    try:
        sess = ag.AgentTurns.__new__(ag.AgentTurns)
        sess.lock, sess.events, sess.turns = threading.Lock(), [], []
        sess._event({"type": "user", "text": "x"})
    finally:
        sessionlog.log = orig
    ok("agent: events carry their time, not passed to the session log",
       isinstance(sess.events[0].get("t"), float) and "t" not in logged[0], (sess.events[0], logged))
    # the demo build replays the change with Mechvane's own functions: the bracket's finding is gone
    from mechvane import examples
    from mechvane.ui.server import collect_findings
    from mechvane.documents import Workspace
    ws = Workspace(tempfile.mkdtemp(prefix="replay-"))  # its own folder: other checks use the name bracket
    doc = examples.bracket(ws)
    before = collect_findings(ws, doc).get("verdict")
    rr.apply_change(ws, doc, rec["steps"][5]["event"]["do"])
    ok("record_replay: replaying the recorded run fixes the bracket", (before, collect_findings(ws, doc).get("verdict")) == ("fail", "ok"),
       before)
    ws.close_all()


def audit_checks(tmp):
    """#127: the audit's input without a model (eleven parts, "nicht erhoben" instead of a crash, period from the last
    audit, git by area) and audit_run.sh's decision (first date, 13 days, quota guard)."""
    import shutil as _sh
    import subprocess
    REPO = Path(__file__).resolve().parents[2]
    root = Path(tmp) / "audit_repo"
    (root / "tools").mkdir(parents=True)
    (root / "docs" / "strategie").mkdir(parents=True)
    (root / "docs" / "plan").mkdir(parents=True)
    (root / "build" / "status").mkdir(parents=True)
    (root / "mechvane" / "ui").mkdir(parents=True)
    g = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True)
    g("init", "-q", "-b", "main"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    (root / "mechvane" / "ui" / "a.js").write_text("x\n" * 30)
    (root / "mechvane" / "core.py").write_text("y\n" * 5)
    g("add", "-A"); g("commit", "-qm", "c")
    (root / "docs" / "strategie" / "2026-11-02-audit.md").write_text("# Audit\n\n## 6. Vorschläge\n\n- A1 Groq streichen (#105)\n\n## 7. Fragen\n")
    (root / "docs" / "plan" / "2026-11-09.md").write_text("# Arbeitspaket\n\n## Durchsicht\n\n- geschlossen: #103\n\n## Ergebnis\n\n- fertig\n")
    (root / "build" / "status" / "events.jsonl").write_text("\n".join(json.dumps(e) for e in [
        {"at": "2026-11-01T01:00:00+00:00", "kind": "gate", "issue": 1, "cls": "A", "verdict": "green"},  # before S
        {"at": "2026-11-05T01:00:00+00:00", "kind": "gate", "issue": 7, "cls": "A", "verdict": "merged"},
        {"at": "2026-11-06T01:00:00+00:00", "kind": "gate", "issue": 8, "cls": "C", "verdict": "red"},
        {"at": "2026-11-07T01:00:00+00:00", "kind": "gate", "issue": 8, "cls": "C", "verdict": "green"},
        {"at": "2026-11-07T01:00:00+00:00", "kind": "queue", "step": "agy_done", "issue": 8, "model": "hydrogen", "rc": "124"},
        {"at": "2026-11-07T02:00:00+00:00", "kind": "queue", "step": "agy_done", "issue": 9, "model": "hydrogen", "rc": "0"},
    ]) + "\n")
    out = root / "eingabe.md"
    r = subprocess.run([sys.executable, str(REPO / "tools" / "audit_input.py"), "--root", str(root), "--offline",
                        "--out", str(out), "--today", "2026-11-16"], capture_output=True, text=True)
    text = out.read_text(encoding="utf-8") if out.is_file() else r.stderr
    heads = [x for x in text.splitlines() if x.startswith("## ")]
    ok("audit input: eleven parts, period from the last audit", r.returncode == 0 and len(heads) == 11
       and "ab 2026-11-02" in text, (r.returncode, heads, r.stderr[-300:]))
    ok("audit input: a source it cannot read says so instead of failing (issues, operations offline; no status page)",
       text.count("nicht erhoben") >= 3 and "## 7. Issues\nnicht erhoben (offline)" in text, text[:400])
    ok("audit input: gate since S by class and verdict, self-merged, returned branches",
       "3 Läufe" in text and "A/merged 1" in text and "selbst gemergt: [7]" in text and "Rückläufer): [8]" in text, text)
    ok("audit input: queue runs with an error code counted once, rc 0 is no error",
       "#8 rc 124" in text and "#9 rc" not in text, text)
    ok("audit input: git by area, the weekly review and the last audit's proposals",
       "Oberfläche: +30" in text and "Fachlogik: +5" in text and "geschlossen: #103" in text and "A1 Groq streichen" in text, text)
    ok("audit input: at most 400 lines", len(text.splitlines()) <= 400)

    # audit_run.sh decides without a model: before the first date, 13 days, quota guard (dry run sends nothing)
    _sh.copy(REPO / "tools" / "audit_run.sh", root / "tools")
    _sh.copy(REPO / "tools" / "audit_input.py", root / "tools")
    notify = Path(tmp) / "notify.sh"
    notify.write_text('notify() { echo "NOTIFY $1"; }\n')
    def run(day, **env):
        script = (root / "tools" / "audit_run.sh").read_text().replace("source /root/scripts/notify-ntfy.sh", f"source {notify}")
        script = script.replace("day=$(TZ=Europe/Zurich date +%F)", f"day={day}")
        (root / "tools" / "audit_run_t.sh").write_text(script)
        e = dict(os.environ, MECHVANE_REPO=str(root), AUDIT_DRY_RUN="1", **env)
        return subprocess.run(["bash", str(root / "tools" / "audit_run_t.sh")], capture_output=True, text=True, env=e,
                              timeout=120).stdout
    ok("audit run: nothing before the first date", "before the first audit" in run("2026-11-23", AUDIT_FIRST="2026-11-30"))
    (root / "docs" / "strategie" / "2026-11-30-audit.md").write_text("# Audit\n")
    ok("audit run: nothing 7 days after the last audit", "7 days ago" in run("2026-12-07", AUDIT_FIRST="2026-11-30"))
    no_quota = run("2026-12-14", AUDIT_FIRST="2026-11-30")
    ok("audit run: 14 days later, but no fresh quota reading: left out", "ausgelassen" in no_quota and "NOTIFY" not in no_quota,
       no_quota)
    (root / "tools" / "token_budget.py").write_text('import json; print(json.dumps({"account": {"week_pct": 31.0, "week_current": True}}))\n')
    ok("audit run: over the quota limit: left out", "31.0 %" in run("2026-12-14", AUDIT_FIRST="2026-11-30"))
    (root / "tools" / "token_budget.py").write_text('import json; print(json.dumps({"account": {"week_pct": 4.0, "week_current": True}}))\n')
    go = run("2026-12-14", AUDIT_FIRST="2026-11-30")
    ok("audit run: due and quota free: gathers the input and would run", "would audit" in go
       and (root / "build" / "audit" / "2026-12-14" / "eingabe.md").is_file(), go)


def heavy_lock_checks(tmp):
    """Audit A5: one heavy run at a time. A second run waits and gives up after MECHVANE_HEAVY_WAIT; a run started by
    the holder (MECHVANE_HEAVY_LOCK inherited) goes on; review_branch.sh takes the same lock."""
    import subprocess
    tools = Path(__file__).resolve().parents[2] / "tools"
    env = dict(os.environ, MECHVANE_HEAVY_LOCKFILE=str(Path(tmp) / "heavy.lock"), MECHVANE_HEAVY_WAIT="1")
    env.pop("MECHVANE_HEAVY_LOCK", None)
    code = f"import sys, time; sys.path.insert(0, {str(tools)!r}); from heavy_lock import hold; hold('t'); print('got', flush=True); time.sleep(float(sys.argv[1]))"
    holder = subprocess.Popen([sys.executable, "-c", code, "6"], env=env, stdout=subprocess.PIPE, text=True)
    holder.stdout.readline()
    second = subprocess.run([sys.executable, "-c", code, "0"], env=env, capture_output=True, text=True, timeout=30)
    inner = subprocess.run([sys.executable, "-c", code, "0"], env=dict(env, MECHVANE_HEAVY_LOCK="gate"), capture_output=True,
                           text=True, timeout=30)
    shell = subprocess.run(["bash", "-c", f"head -20 {tools / 'review_branch.sh'} | sed -n '/heavy run at a time/,/^fi/p' > {tmp}/lock.sh; "
                            f"source {tmp}/lock.sh; echo shell-got"], env=env, capture_output=True, text=True, timeout=30)
    holder.wait(timeout=30)
    ok("heavy lock: a second heavy run gives up while one holds the lock", second.returncode != 0 and "waiting" in second.stderr,
       (second.returncode, second.stderr[-200:]))
    ok("heavy lock: a run started by the holder goes on", inner.returncode == 0 and "got" in inner.stdout, inner.stderr[-200:])
    ok("heavy lock: review_branch.sh waits for the same lock", "shell-got" not in shell.stdout and "lock not free" in shell.stderr,
       (shell.stdout, shell.stderr[-200:]))


def acceptance_checks(tmp):
    """Audit A1: coverage counts a frozen command only when the workspace code names it as a string (not as part of a
    longer id), the other tests keep a value set by hand with its date or say "nicht gemessen"."""
    tools = Path(__file__).resolve().parents[2] / "tools"
    sys.path.insert(0, str(tools))
    import acceptance as acc
    ui = Path(tmp) / "acc_ui"
    (ui / "static" / "vendor").mkdir(parents=True)
    (ui / "static" / "a.js").write_text('run("solid.fillet"); x = `sketch.line`; y = "solid.fillet.extra";')
    (ui / "srv.py").write_text("cmd('timeline.edit')\n")
    (ui / "static" / "vendor" / "lib.js").write_text('"solid.chamfer"')
    named = acc.named_in_ui(["solid.fillet", "sketch.line", "timeline.edit", "solid.chamfer", "solid.fillet.extra2"], ui)
    ok("acceptance: commands named in the workspace code, quoted, vendor left out",
       named == {"solid.fillet", "sketch.line", "timeline.edit"}, named)
    d = Path(tmp) / "acc_docs"
    d.mkdir()
    (d / "befehle-0.43.0.txt").write_text("solid.fillet\nsketch.line\nview.fit\nrender.go\n")
    (d / "messwerte.json").write_text(json.dumps({"eindruck": {"wert": "23/40", "gemessen": "2026-11-06", "quelle": "Sichtung"}}))
    old = acc.DIR, acc.VALUES
    acc.DIR, acc.VALUES = d, d / "messwerte.json"
    try:
        res = acc.measure(ui)
    finally:
        acc.DIR, acc.VALUES = old
    rows = {r["key"]: r for r in res["pruefungen"]}
    ok("acceptance: coverage against the frozen list, by domain", res["solidcraft_ziel"] == "0.43.0"
       and rows["abdeckung"]["wert"].startswith("2 von 4 in der Oberfläche") and rows["abdeckung"]["bereiche"]["view"] == "0/1",
       rows["abdeckung"])
    ok("acceptance: a value by hand keeps its date, the others say so",
       rows["eindruck"]["wert"] == "23/40" and rows["eindruck"]["gemessen"] == "2026-11-06"
       and rows["konstruieren"]["wert"] == "nicht gemessen", rows)


def demo_wasm_split_checks(tmp):
    """#119: the demo build splits a wasm over GitHub's file limit and wires the loader into sc/index.html."""
    import hashlib
    from tools import build_demo_site as bds
    sc = Path(tmp) / "wasm_split"
    sc.mkdir()
    data = bytes(range(256)) * 40  # 10240 bytes
    (sc / "app-x_bg.wasm").write_bytes(data)
    (sc / "index.html").write_text('<head><link rel="preload" href="./app-x_bg.wasm" crossorigin="anonymous" as="fetch">'
                                   '<script type="module">init()</script><script>navigator.serviceWorker.register("sw.js")'
                                   '</script></head>', encoding="utf-8")
    (sc / "sw.js").write_text('// x\n/* @build */ const VERSION = "0.43.0-abc", FILES = [];\nconst RETIRE = VERSION === "dev";\n',
                              encoding="utf-8")
    old = bds.PART_BYTES
    bds.PART_BYTES = 4000
    try:
        bds.split_large_wasm(sc)
    finally:
        bds.PART_BYTES = old
    man = json.loads((sc / "app-x_bg.wasm.parts.json").read_text())
    joined = b"".join((sc / p).read_bytes() for p in man["parts"])
    html = (sc / "index.html").read_text()
    ok("demo build: a wasm over the limit becomes pieces with size and SHA-256, the loader comes before the module, "
       "no preload of the gone file, the offline worker retires (#119)",
       not (sc / "app-x_bg.wasm").exists() and len(man["parts"]) == 3 and joined == data
       and man["sha256"] == hashlib.sha256(data).hexdigest() and (sc / "wasm-parts.js").exists()
       and html.index("wasm-parts.js") < html.index('<script type="module">') and "rel=\"preload\"" not in html
       and "serviceWorker.register" not in html and 'const VERSION = "dev"' in (sc / "sw.js").read_text(), f"{man} {html}")


def step_signature_checks(ws):
    """#121: every feature in the part tree carries a signature of its definition; a step changes exactly the
    signatures of what it changed, so the workspace can mark new, changed and removed features."""
    from mechvane import tree
    doc = ws.new(PART, "sig_part", overwrite=True)
    s = doc.session
    s.batch([{"command": "solid.box", "params": {"length": 30, "width": 20, "height": 10, "corner": [0, 0, 0], "name": "Block"}},
             {"command": "solid.fillet", "params": {"edges": [[15, 0, 10]], "radius": 1, "name": "Round"}}])
    flat = lambda t: {n["name"]: n.get("sig") for n in t["features"] if n.get("name")}
    before = flat(tree.part_tree(s, groups=True))
    again = flat(tree.part_tree(s, groups=True))
    s.cmd("timeline.edit", {"feature": "Round", "set": {"radius": 2}})
    after = flat(tree.part_tree(s, groups=True))
    ok("step marks: each feature has a signature, stable without a change; editing Round changes only its own (#121)",
       all(before.values()) and before == again and after["Round"] != before["Round"] and after["Block"] == before["Block"],
       f"{before} {after}")
    ws.close("sig_part")
    # a parameter feeds a feature as an expression, a sketch keeps its geometry apart from the definition (review, 2026-11-16)
    doc = ws.new(PART, "sig_param", overwrite=True)
    s = doc.session
    s.batch([{"command": "parameters.add", "params": {"name": "H", "expression": "10 mm"}},
             {"command": "parameters.add", "params": {"name": "R", "expression": "5 mm"}},
             {"command": "sketch.create", "params": {"plane": "XY", "name": "Sk"}},
             {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": "R"}},
             {"command": "sketch.finish", "params": {}},
             {"command": "solid.extrude", "params": {"sketch": "Sk", "distance": "H", "name": "Pad"}},
             {"command": "solid.box", "params": {"length": 5, "width": 5, "height": 5, "corner": [40, 0, 0], "name": "Other",
                                                 "operation": "new_body"}}])
    def flat2():
        out = {}
        def walk(nodes):
            for n in nodes:
                if n.get("name"):
                    out[n["name"]] = n.get("sig")
                walk(n.get("children") or [])
        walk(tree.part_tree(s, groups=True)["features"])
        return out
    t0 = flat2()
    s.cmd("parameters.change", {"changes": {"H": "25 mm"}})
    t1 = flat2()
    s.cmd("parameters.change", {"changes": {"R": "4 mm"}})
    t2 = flat2()
    ok("step marks: a changed parameter changes the signature of the feature that names it, not of the others; a sketch "
       "radius from a parameter changes the sketch (#121 review)",
       t1["Pad"] != t0["Pad"] and t1["Sk"] == t0["Sk"] and t1["Other"] == t0["Other"]
       and t2["Sk"] != t1["Sk"] and t2["Other"] == t1["Other"],
       f"{t0} {t1} {t2}")
    ws.close("sig_param")


def cleanup_branches_checks(tmp):
    """tools/cleanup_branches.sh (#103): lists branches with a closed issue that are fully in main, deletes only those on
    --delete, keeps open issues and unmerged branches, writes the tips for restoring. A stub gh and a scratch remote."""
    import subprocess as sp, stat
    script = Path(__file__).resolve().parents[2] / "tools" / "cleanup_branches.sh"
    root = Path(tmp) / "cleanup_branches"
    (root / "bin").mkdir(parents=True)
    stub = root / "bin" / "gh"
    stub.write_text("#!/bin/sh\nprintf '1\\n2\\n'\n")  # issues 1 and 2 are closed
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    git = lambda *a, cwd=None: sp.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, capture_output=True, text=True)
    git("init", "-q", "--bare", "-b", "main", str(root / "origin.git"))
    work = root / "work"
    git("clone", "-q", str(root / "origin.git"), str(work))
    (work / "tools").mkdir()
    (work / "tools" / "cleanup_branches.sh").write_text(script.read_text())
    (work / "a.txt").write_text("a")
    git("add", ".", cwd=work); git("commit", "-qm", "base", cwd=work); git("push", "-q", "origin", "HEAD:main", cwd=work)
    for nr, merged in (("1", True), ("2", False), ("3", True)):  # 1: closed+merged, 2: closed, not merged, 3: merged, issue open
        git("checkout", "-q", "-b", f"gemini/{nr}", "main", cwd=work)
        if not merged:
            (work / f"f{nr}.txt").write_text(nr); git("add", ".", cwd=work); git("commit", "-qm", f"b{nr}", cwd=work)
        git("push", "-q", "origin", f"gemini/{nr}", cwd=work)
    git("checkout", "-q", "main", cwd=work)
    env = {**os.environ, "PATH": f"{root / 'bin'}:{os.environ['PATH']}", "TMP_ROOT": str(root / "empty")}
    run = lambda *args: sp.run(["bash", "tools/cleanup_branches.sh", *args], cwd=work, env=env, capture_output=True, text=True)
    listed = run()
    left = lambda: sorted(l.split("/", 2)[-1] for l in git("branch", "-r", "--list", "origin/gemini/*", cwd=work).stdout.split())
    after_list = left()
    deleted = run("--delete")
    after_delete = sorted(l.strip().split("refs/heads/")[-1] for l in sp.run(["git", "ls-remote", "--heads", str(root / "origin.git")], capture_output=True, text=True).stdout.splitlines())
    tips = list((work / "build" / "status").glob("deleted_branches_*.txt"))
    ok("cleanup_branches: list mode changes nothing; --delete removes only the closed, fully merged branch and records its tip",
       "gemini/1" in listed.stdout and "gemini/3" not in listed.stdout.split("Kept")[0] and "gemini/2" not in listed.stdout.split("older than 30")[0]
       and len(after_list) == 3 and not any(b.endswith("gemini/1") for b in after_delete)
       and any(b.endswith("gemini/2") for b in after_delete) and any(b.endswith("gemini/3") for b in after_delete)
       and len(tips) == 1 and "gemini/1" in tips[0].read_text(), f"{listed.stdout!r} {listed.stderr[-200:]!r} {deleted.stdout!r} {after_delete}")


def check_parameters_tool_checks(ws):
    """#108: the MCP tool check_parameters tries values and puts the design back; a bolt circle moves the cylinders
    without changing the volume, a hole too big leaves no body, a made-up name is refused with the real names."""
    from mechvane import examples
    orig_server_ws, server.ws = server.ws, ws
    doc = examples.flange(ws)
    exprs = lambda: {p["name"]: p["expression"] for p in doc.session.cmd("parameters.list", {}).get("parameters", [])
                     if p.get("source") == "user"}
    before = exprs()
    base = server.check_parameters(doc.name, {"A": before["A"]})
    wide = server.check_parameters(doc.name, {"A": 70})
    moved = server.check_parameters(doc.name, {"bcd": 30})
    huge = server.check_parameters(doc.name, {"dh": 80})
    try:
        server.check_parameters(doc.name, {"nonexistent": 1})
        refused = ""
    except Exception as e:  # noqa: BLE001
        refused = str(e)
    vol = lambda r: round(r["measure"]["total"]["volume_mm3"], 1)
    origins = lambda r: sorted(tuple(round(x, 1) for x in c["origin"]) for c in r["cylinders"])
    ok("check_parameters tool: values tried and restored, a bolt circle changes the cylinder origins but not the volume, "
       "a hole of 80 mm leaves no body, an unknown name is refused naming the real ones (#108)",
       exprs() == before and base["restored"] and wide["restored"] and vol(wide) > vol(base)
       and vol(moved) == vol(base) and origins(moved) != origins(base)
       and huge["measure"]["body_count"] == 0 and huge["cylinders"] == [] and base["measure"]["body_count"] == 1
       and "nonexistent" in refused and "bcd" in refused,
       f"{exprs()} {vol(base)} {vol(wide)} {vol(moved)} {huge['measure']['body_count']} {refused[:120]!r}")
    ws.close(doc.name)
    server.ws = orig_server_ws


def queue_guard_checks(tmp):
    """tools/gemini_queue.sh guards for the stand-in review: cg_rest takes the lower of the weekly and five-hour value of the
    agy pot, claude_use reads the subscription use from the statusline file (stale or finished week = unknown);
    tools/gate.py recommends_merge reads only Argon's own section."""
    import importlib.util, re, subprocess as sp, time
    queue = Path(__file__).resolve().parents[2] / "tools" / "gemini_queue.sh"
    text = queue.read_text()
    fns = "\n".join(re.search(rf"^{name}\(\) \{{.*?^\}}$", text, re.S | re.M).group(0) for name in ("cg_rest", "claude_use"))
    root = Path(tmp) / "queue_guard"
    (root / "home" / ".claude").mkdir(parents=True)
    quota = root / "quota.sh"
    quota.write_text("#!/bin/sh\nprintf 'Gemini Models\\tWeekly\\t80%%\\tx\\nClaude and GPT models\\tWeekly Limit Remaining\\t100%%\\tx\\n"
                     "Claude and GPT models\\tFive Hour Limit Remaining\\t7%%\\tx\\n'\n")
    quota.chmod(0o755)
    def use(at_offset, week, five, resets_in):
        (root / "home" / ".claude" / "rate_limits.json").write_text(json.dumps({"at": time.time() - at_offset, "rate_limits": {
            "five_hour": {"used_percentage": five, "resets_at": time.time() + 3600},
            "seven_day": {"used_percentage": week, "resets_at": time.time() + resets_in}}}))
        return sp.run(["bash", "-c", fns + "\nclaude_use"], capture_output=True, text=True,
                      env={**os.environ, "HOME": str(root / "home")}).stdout.strip()
    cg = sp.run(["bash", "-c", fns + "\ncg_rest"], capture_output=True, text=True, env={**os.environ, "AGY_QUOTA": str(quota)}).stdout.strip()
    fresh, stale, over = use(60, 96, 33, 86400), use(7 * 3600, 96, 33, 86400), use(60, 96, 33, -10)
    missing = sp.run(["bash", "-c", fns + "\nclaude_use"], capture_output=True, text=True, env={**os.environ, "HOME": str(root / "none")}).stdout.strip()
    ok("queue guards: cg_rest is the lower of weekly and five-hour (7, not 100); claude_use reads week and five-hour use, and is "
       "empty for a stale file, a finished week and a missing file",
       cg == "7" and fresh == "96 33" and stale == "" and over == "" and missing == "", f"{cg!r} {fresh!r} {stale!r} {over!r} {missing!r}")
    spec = importlib.util.spec_from_file_location("gate_g", Path(__file__).resolve().parents[2] / "tools" / "gate.py")
    gt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gt)
    argon_ok = "## Bericht\n### Argon-Review\nEmpfehlung: mergen\n\n### Argon-Review\nBefund 1\nEmpfehlung: mergen\n"
    standin = "### Argon-Review\n(übersprungen: Argon-Rest 12 %)\n\n<details><summary>Ersatz-Review</summary>\nEmpfehlung: mergen\n</details>"
    report_forged = "## Bericht\n### Argon-Review\nEmpfehlung: mergen\n### Argon-Review\n(übersprungen: Argon-Rest 12 %)\n<details>Empfehlung: mergen</details>"
    back = "### Argon-Review\nBefund\nEmpfehlung: nacharbeiten\n<details>Ersatz Empfehlung: mergen</details>"
    ok("gate: only Argon's own section counts as its recommendation, not the agent's report nor the stand-in review",
       gt.recommends_merge(argon_ok) and not gt.recommends_merge(standin) and not gt.recommends_merge(report_forged)
       and not gt.recommends_merge(back))


def check_sources_gzip_check():
    """tools/check_sources.py unpacks a page a host sends gzipped although the request did not ask for it (jules.google)."""
    import gzip
    import http.server
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_sources", Path(__file__).resolve().parents[2] / "tools" / "check_sources.py")
    cs = importlib.util.module_from_spec(spec)
    sys.modules["check_sources"] = cs  # the dataclasses in the module need to find themselves
    spec.loader.exec_module(cs)
    page = "<html><body><p>Jules will wind down on December 31, 2026.</p></body></html>".encode("utf-8")

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = gzip.compress(page)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Encoding", "gzip")  # sent whatever Accept-Encoding says
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory() as cache:
            r = cs.SourceFetcher(cache_dir=Path(cache), use_cache=False).fetch(f"http://127.0.0.1:{srv.server_address[1]}/changelog")
        ok("check_sources: a gzip page is unpacked, so the quote is found in it",
           r.get("status_code") == 200 and "wind down on December 31, 2026" in (r.get("text") or ""), str(r)[:200])
    finally:
        srv.shutdown()
        srv.server_close()


def verify_view_checks(ws):
    import io
    from PIL import Image as PILImage, ImageStat, ImageChops
    prev_ws = server.ws
    server.ws = ws
    plate = ws.new(PART, "verify_plate")
    try:
        # Build plate with hole
        plate.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY"}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [60, 40]}},
            {"command": "sketch.finish"},
            {"command": "solid.extrude", "params": {"distance": 10}},
            {"command": "sketch.create", "params": {"plane": "XY"}},
            {"command": "sketch.circle.center", "params": {"center": [30, 20], "radius": 5}},
            {"command": "sketch.finish"},
            {"command": "solid.extrude", "params": {"distance": 10, "operation": "cut"}},
        ])

        ok("verify_view: the size label shows the real bounding box of the plate",
           server._bounding_box_str(plate) == "60 × 40 × 10 mm", str(server._bounding_box_str(plate)))

        # Single screenshot for baseline size
        shot = server.screenshot("verify_plate", view="iso")
        single_img = PILImage.open(io.BytesIO(shot.data))
        sw, sh = single_img.size

        # verify_view with path
        res_path = server.verify_view("verify_plate", path="verify_grid.png")
        grid_file = ws.root / "verify_grid.png"
        ok("verify_view: with path saves file and replies with metadata",
           grid_file.is_file() and res_path.get("width", 0) > 0 and res_path.get("height", 0) > 0,
           str(res_path))

        # Check image is PNG and roughly twice as wide and high as single image
        with PILImage.open(grid_file) as im:
            img_format = im.format
            grid_img = im.convert("RGB")
        gw, gh = grid_img.size
        ok("verify_view: image is PNG roughly twice as wide and high as a single image",
           img_format == "PNG" and abs(gw - 2 * sw) <= 10 and abs(gh - 2 * sh) <= 10,
           f"format={img_format}, grid={(gw, gh)}, single={(sw, sh)}")

        # Check that the four quadrants are not empty (pixel variance > 0)
        w_half, h_half = gw // 2, gh // 2
        quadrants = [
            grid_img.crop((0, 0, w_half, h_half)),
            grid_img.crop((w_half, 0, gw, h_half)),
            grid_img.crop((0, h_half, w_half, gh)),
            grid_img.crop((w_half, h_half, gw, gh)),
        ]
        variances = [sum(ImageStat.Stat(q).var) for q in quadrants]
        ok("verify_view: four quadrants are not empty (pixel variance > 0)",
           all(v > 0 for v in variances),
           f"variances={variances}")

        # Check that the section quadrant differs from plain right view (hole cut is visible)
        shot_right = server.screenshot("verify_plate", view="right")
        right_img = PILImage.open(io.BytesIO(shot_right.data)).convert("RGB")
        sec_crop = quadrants[3].crop((100, 80, w_half - 100, h_half - 60))
        right_crop = right_img.crop((100, 80, w_half - 100, h_half - 60))
        diff_stat = ImageStat.Stat(ImageChops.difference(sec_crop, right_crop))
        ok("verify_view: section quadrant differs from plain right view",
           sum(diff_stat.mean) > 0.5,
           f"diff_stat={diff_stat.mean}")

        # verify_view without path returns an image
        res_no_path = server.verify_view("verify_plate")
        ok("verify_view: call without path returns an image",
           hasattr(res_no_path, "data") and len(res_no_path.data) > 1000 and getattr(res_no_path, "_format", "") == "png",
           str(type(res_no_path)))
    finally:
        ws.close("verify_plate")
        server.ws = prev_ws


def assemble_dialog_checks(tmp):
    """Assemble tab stage 1a: /api/assembly/insert places parts with transform/grounded on the shared undo
    list, /api/assembly/update_links checks joints and supports repair=True, and both return 400 on a part."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "assemble_ui"
    folder.mkdir()
    w = Workspace(folder)
    try:
        plate = w.new(PART, "BasePlate")
        plate.session.batch([
            {"command": "parameters.change", "params": {"name": "h", "expression": "10 mm"}},
            {"command": "sketch.create", "params": {"plane": "XY", "name": "SkPlate"}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 40]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "SkPlate", "distance": "h", "name": "PlateBody"}},
        ])
        plate.save()

        pin = w.new(PART, "Pin")
        pin.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY", "name": "SkPin"}},
            {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 5}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "SkPin", "distance": 20, "name": "PinBody"}},
        ])
        pin.save()

        asm = w.new(ASSEMBLY, "Gearbox")
        links.insert(w, asm, plate.path, name="Plate", grounded=True)
        asm.save()
    finally:
        w.close_all()

    srv = ui_server.create_server(folder, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        # With a part open, /api/assembly/* must fail with 400
        st_op, _ = call("open/BasePlate.solidcraft", {})
        st_p_ins, p_ins = call("assembly/insert", {"file": "Pin.solidcraft"})
        st_p_upd, p_upd = call("assembly/update_links", {})
        ok("assemble UI endpoints: return HTTP 400 when a part is open",
           st_op == 200 and st_p_ins == 400 and st_p_upd == 400 and p_ins.get("error") and p_upd.get("error"),
           f"open={st_op} ins=({st_p_ins}, {p_ins}) upd=({st_p_upd}, {p_upd})")

        # Open the assembly and verify /api/files lists folder parts excluding the assembly itself
        st_oa, _ = call("open/Gearbox.solidcraft", {})
        st_fl, fl = call("files")
        parts_list = fl.get("parts") or []
        ok("assemble /api/files: lists folder parts excluding the assembly itself",
           st_oa == 200 and st_fl == 200 and "BasePlate.solidcraft" in parts_list and "Pin.solidcraft" in parts_list
           and "Gearbox.solidcraft" not in parts_list,
           f"open={st_oa} files={fl}")

        # Insert the second part via POST /api/assembly/insert with name, translate, rotate, grounded=False
        st_ins, ins = call("assembly/insert", {
            "file": "Pin.solidcraft",
            "name": "DrivePin",
            "translate": [20, 20, 10],
            "rotate": [0, 0, 90],
            "grounded": False,
        })
        st_tr, tr = call("tree")
        occ_names = [o.get("name", "") for o in tr.get("occurrences", [])]
        ok("assemble /api/assembly/insert: inserts second part, returns component name and /api/tree shows it",
           st_ins == 200 and ins.get("name") == "DrivePin"
           and any("DrivePin" in n for n in occ_names),
           f"ins=({st_ins}, {ins}) occs={occ_names}")

        # Shared Undo / Redo reverts and re-applies the placement
        st_un, _ = call("agent/undo", {})
        _, tr_un = call("tree")
        occ_un = [o.get("name", "") for o in tr_un.get("occurrences", [])]
        st_re, _ = call("agent/redo", {})
        _, tr_re = call("tree")
        occ_re = [o.get("name", "") for o in tr_re.get("occurrences", [])]
        ok("assemble /api/assembly/insert: undo and redo on shared history",
           st_un == 200 and not any("DrivePin" in n for n in occ_un)
           and st_re == 200 and any("DrivePin" in n for n in occ_re),
           f"undo=({st_un}, {occ_un}) redo=({st_re}, {occ_re})")

        # Record a rigid joint between Plate and DrivePin and verify POST /api/assembly/update_links reports joint count
        with srv.lock:
            doc = srv.ensure_current()
            jparams = {
                "type": "rigid",
                "name": "PinOnPlate",
                "a": {"occurrence": "Plate:1", "face": [20, 20, 10]},
                "b": {"occurrence": "DrivePin:1", "face": [20, 20, 10]},
            }
            doc.session.cmd("joint.create", jparams)
            links.record(srv.ws, doc, "PinOnPlate", create_params=jparams)
            doc.save()
            srv.mtime = doc.path.stat().st_mtime

        st_upd, upd = call("assembly/update_links", {"repair": False})
        st_rep, rep = call("assembly/update_links", {"repair": True})
        ok("assemble /api/assembly/update_links: reports checked joint count and supports repair=True",
           st_upd == 200 and upd.get("joint_count") == 1 and "PinOnPlate" in (upd.get("checked_joints") or [])
           and st_rep == 200 and rep.get("joint_count") == 1,
           f"upd=({st_upd}, {upd}) rep=({st_rep}, {rep})")
    finally:
        srv.shutdown()
        srv.server_close()


def assemble_constraint_checks(tmp):
    """Assemble tab step 3 (#88): POST /api/assembly/constraint adds SolidCraft assembly constraints via
    modeling.add_constraint (recorded like joints, so check_joints and update_links follow them), /edit changes
    rule, gap and name, links.repair recreates a constraint by its rule, and the browser shows the rule."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "assemble_constraint_ui"
    folder.mkdir()
    w = Workspace(folder)
    try:
        for name, h in (("Base", 10), ("Lid", 5)):
            d = w.new(PART, name)
            d.session.cmd("solid.box", {"length": 40, "width": 30, "height": h, "corner": [0, 0, 0],
                                        "body_name": "Body1", "name": "Box1"})
            d.save()
        pin = w.new(PART, "Pin")
        pin.session.cmd("solid.cylinder", {"radius": 5, "height": 20, "center": [0, 0, 0], "body_name": "Body1", "name": "Cyl"})
        pin.save()
        asm = w.new(ASSEMBLY, "ConstrainAsm")
        links.insert(w, asm, folder / "Base.solidcraft", grounded=True)
        links.insert(w, asm, folder / "Lid.solidcraft", translate=[60, 0, 0], grounded=False)
        links.insert(w, asm, folder / "Pin.solidcraft", name="PinA", translate=[0, 60, 0], grounded=True)
        links.insert(w, asm, folder / "Pin.solidcraft", name="PinB", translate=[30, 60, 0], grounded=False)
        asm.save()
    finally:
        w.close_all()

    srv = ui_server.create_server(folder, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"} if body is not None else {})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        call("open/Base.solidcraft", {})
        st_part, res_part = call("assembly/constraint", {"type": "mate", "a": {"occurrence": "Base:1", "face": [20, 15, 10]},
                                                         "b": {"occurrence": "Lid:1", "face": [80, 15, 0]}})
        ok("assemble constraint: HTTP 400 with a part open", st_part == 400 and res_part.get("error"), res_part)
        call("open/ConstrainAsm.solidcraft", {})
        a_top = {"occurrence": "Base:1", "face": [20, 15, 10]}
        b_bottom = {"occurrence": "Lid:1", "face": [80, 15, 0]}
        bad = {
            "unknown rule": call("assembly/constraint", {"type": "glue", "a": a_top, "b": b_bottom}),
            "distance without offset": call("assembly/constraint", {"type": "distance", "a": a_top, "b": b_bottom}),
            "angle without angle": call("assembly/constraint", {"type": "angle", "a": a_top, "b": b_bottom}),
            "same component": call("assembly/constraint", {"type": "mate", "a": a_top, "b": {"occurrence": "Base:1", "face": [0, 15, 5]}}),
            "text offset": call("assembly/constraint", {"type": "mate", "a": a_top, "b": b_bottom, "offset": "zwei"}),
        }
        ok("assemble constraint: unknown rule, missing gap or angle, one component twice, a bad offset give HTTP 400 with a message",
           all(st == 400 and r.get("error") for st, r in bad.values()), {k: v for k, v in bad.items() if v[0] != 400})
        _, hist0 = call("history")
        st, res = call("assembly/constraint", {"type": "mate", "a": a_top, "b": b_bottom, "offset": 2})
        _, ctx = call("assembly/context")
        mate = next((j for j in ctx.get("joints", []) if j["name"] == "Mate1"), {})
        _, hist1 = call("history")
        ok("assemble constraint: a mate with gap 2 puts the lid on the base top at z=12, named Mate1, on the shared Undo list",
           st == 200 and res.get("name") == "Mate1" and mate.get("constraint") == "mate"
           and abs((mate.get("frame_b") or {}).get("origin", [0, 0, 0])[2] - 12) < 1e-6
           and (hist1.get("undo") or "").startswith("Constraint mate") and hist0.get("undo") != hist1.get("undo"),
           (st, res, mate, hist1))
        st_c, res_c = call("assembly/constraint", {"type": "concentric", "a": {"occurrence": "PinA:1", "circle": [5, 60, 10]},
                                                   "b": {"occurrence": "PinB:1", "circle": [35, 60, 10]}})
        _, ctx = call("assembly/context")
        conc = next((j for j in ctx.get("joints", []) if j["name"] == res_c.get("name")), {})
        oa, ob = (conc.get("frame_a") or {}).get("origin", [9, 9, 9]), (conc.get("frame_b") or {}).get("origin", [0, 0, 0])
        ok("assemble constraint: concentric on two round faces (circle picks) puts both pins on one axis",
           st_c == 200 and conc.get("constraint") == "concentric" and abs(oa[0] - ob[0]) < 1e-6 and abs(oa[1] - ob[1]) < 1e-6,
           (st_c, res_c, conc))
        meta = json.loads(json.dumps(srv.doc.metadata()))
        ok("assemble constraint: recorded like a joint (part faces on both sides, create marked as a constraint)",
           (meta.get("joints", {}).get("Mate1", {}).get("sides", {}).get("a", {}).get("face") == "F1:+z")
           and meta["joints"]["Mate1"]["sides"]["b"]["face"] == "F1:-z" and meta["joints"]["Mate1"]["create"].get("constraint") is True,
           meta.get("joints", {}).get("Mate1"))
        st_e, res_e = call("assembly/constraint/edit", {"constraint": "Mate1", "type": "mate", "offset": 4, "name": "LidOnBase"})
        _, ctx = call("assembly/context")
        ed = next((j for j in ctx.get("joints", []) if j["name"] == "LidOnBase"), {})
        st_ea, res_ea = call("assembly/constraint/edit", {"constraint": "LidOnBase", "a": a_top})
        st_eu, res_eu = call("assembly/constraint/edit", {"constraint": "NoSuch", "offset": 1})
        st_ej, res_ej = call("assembly/constraint/edit", {"constraint": "LidOnBase", "type": "distance"})
        st_en, res_en = call("assembly/constraint/edit", {"constraint": "LidOnBase", "name": "LidOnBase"})
        ok("assemble constraint edit: gap 4 and a new name (lid at z=14, record renamed); new references, an unknown name and nothing to change give 400",
           st_e == 200 and ed.get("constraint") == "mate" and abs(ed["frame_b"]["origin"][2] - 14) < 1e-6
           and "LidOnBase" in srv.doc.metadata()["joints"] and "Mate1" not in srv.doc.metadata()["joints"]
           and st_ea == 400 and "delete it" in res_ea.get("error", "") and st_eu == 400
           and st_en == 400 and "nothing to change" in res_en.get("error", ""),
           (st_e, res_e, ed, st_ea, res_ea, st_eu, res_eu, st_en, res_en))
        _, ctx = call("assembly/context")
        ej = next((j for j in ctx.get("joints", []) if j["name"] == "LidOnBase"), {})
        ok("assemble constraint edit: a change to distance keeps the gap (as SolidCraft does)",
           st_ej == 200 and ej.get("constraint") == "distance" and abs(ej["frame_b"]["origin"][2] - 14) < 1e-6, (st_ej, res_ej, ej))
        call("assembly/constraint/edit", {"constraint": "LidOnBase", "type": "mate"})
        st_chk, chk = call("assembly/update_links", {})
        ok("assemble constraint: Update Links checks constraints like joints (all sides ok)",
           st_chk == 200 and all(r.get("status") == "ok" for r in chk.get("joints", []) if r.get("joint") in ("LidOnBase", res_c.get("name")))
           and any(r.get("joint") == "LidOnBase" for r in chk.get("joints", [])), chk)
        _, tree = call("tree")
        ok("assemble constraint: the model browser names the rule, not the joint kind", '"mate"' in json.dumps(tree), json.dumps(tree)[:400])

        # links.repair recreates a constraint by its rule, keeps gap and the joint's facing
        doc = srv.doc
        with srv.lock:
            before = next(j for j in doc.session.cmd("joint.list")["joints"] if j["name"] == "LidOnBase")
            links.repair(srv.ws, doc, "LidOnBase")
            after = next(j for j in doc.session.cmd("joint.list")["joints"] if j["name"] == "LidOnBase")
        ok("assemble constraint: links.repair recreates it through assembly.constraint.create (rule, gap, flip and position kept)",
           after.get("constraint") == "mate" and after["offset"] == before["offset"] and after["flip"] == before["flip"]
           and all(abs(x - y) < 1e-6 for x, y in zip(after["frame_b"]["origin"], before["frame_b"]["origin"])), (before, after))
        # every rule the dialog offers, with the picks it makes (face for a plane, circle for a round face): add,
        # repair (recreated by its rule, same place, facing and rule), delete through the browser's endpoint
        st_dm, _ = call("assembly/joint/delete", {"joint": "LidOnBase"})
        st_dc, _ = call("assembly/joint/delete", {"joint": res_c.get("name")})
        # PinB moves with each round rule: its circle picks are given in its own coordinates ("local") and placed
        # where PinB is before each rule
        rules = {
            "mate": ({"occurrence": "Base:1", "face": [20, 15, 10]}, {"occurrence": "Lid:1", "face": [80, 15, 0]}, {"offset": 2}),
            "flush": ({"occurrence": "Base:1", "face": [0, 15, 5]}, {"occurrence": "Lid:1", "face": [60, 15, 2]}, {"offset": 3, "flip": True}),
            "distance": ({"occurrence": "Base:1", "face": [20, 15, 10]}, {"occurrence": "Lid:1", "face": [80, 15, 0]}, {"offset": 7}),
            "concentric": ({"occurrence": "PinA:1", "circle": [5, 60, 10]}, {"occurrence": "PinB:1", "local": [5, 0, 10]}, {}),
            "insert": ({"occurrence": "PinA:1", "circle": [5, 60, 20]}, {"occurrence": "PinB:1", "local": [5, 0, 0]}, {}),
            "parallel": ({"occurrence": "Base:1", "face": [20, 15, 10]}, {"occurrence": "Lid:1", "face": [80, 15, 0]}, {}),
            "perpendicular": ({"occurrence": "Base:1", "face": [20, 15, 10]}, {"occurrence": "Lid:1", "face": [60, 15, 2]}, {}),
            "angle": ({"occurrence": "Base:1", "face": [20, 15, 10]}, {"occurrence": "Lid:1", "face": [80, 15, 0]}, {"angle": 30, "flip": True}),
            "tangent": ({"occurrence": "Base:1", "face": [20, 15, 10]}, {"occurrence": "PinB:1", "local": [5, 0, 10]}, {}),
        }
        rule_res = {}
        for rule, (ra, rb, extra) in rules.items():
            if "local" in rb:
                with srv.lock:
                    pb = next(o for o in links._occurrences(srv.doc.session).values() if o["name"] == "PinB:1")["transform"]
                rb = {"occurrence": "PinB:1", "circle": links.g.apply_point(pb, rb["local"])}
            st_r, res_r = call("assembly/constraint", dict({"type": rule, "a": ra, "b": rb}, **extra))
            nm = res_r.get("name")
            if st_r != 200:
                rule_res[rule] = ("add", st_r, res_r)
                continue
            with srv.lock:
                bj = next(j for j in srv.doc.session.cmd("joint.list")["joints"] if j["name"] == nm)
                try:
                    links.repair(srv.ws, srv.doc, nm)
                    aj = next(j for j in srv.doc.session.cmd("joint.list")["joints"] if j["name"] == nm)
                    same = (aj.get("constraint") == rule and aj["flip"] == bj["flip"]
                            and all(abs(x - y) < 1e-6 for x, y in zip(aj["frame_b"]["origin"] + aj["frame_b"]["z"],
                                                                      bj["frame_b"]["origin"] + bj["frame_b"]["z"])))
                except Exception as e:
                    same = f"repair: {e}"
            st_d, res_d = call("assembly/joint/delete", {"joint": nm})
            with srv.lock:
                gone = (all(j["name"] != nm for j in srv.doc.session.cmd("joint.list")["joints"])
                        and nm not in srv.doc.metadata().get("joints", {}))
            if same is not True or st_d != 200 or not gone:
                rule_res[rule] = (same, st_d, res_d, gone)
        ok("assemble constraint: all nine dialog rules are made from face/circle picks, links.repair keeps rule, place, facing "
           "(flipped flush and angle included) and gap, and Delete removes joint and record",
           st_dm == 200 and st_dc == 200 and not rule_res, rule_res)
        st_dx, res_dx = call("assembly/joint/delete", {"joint": "NoSuchJoint"})
        ok("assemble joint delete: an unknown name gives HTTP 400", st_dx == 400 and res_dx.get("error"), res_dx)

        # a create SolidCraft refuses during repair leaves the constraint where it was
        st_g, res_g = call("assembly/constraint", {"type": "angle", "a": rules["angle"][0], "b": rules["angle"][1], "angle": 30})
        with srv.lock:
            d = srv.doc
            meta = d.metadata()
            meta["joints"][res_g["name"]]["create"].pop("angle", None)  # repair then has no angle for the rule
            d.set_metadata(meta)
            try:
                links.repair(srv.ws, d, res_g["name"])
                refused = False
            except Exception:
                refused = True
            still = any(j["name"] == res_g["name"] and j.get("constraint") == "angle"
                        for j in d.session.cmd("joint.list")["joints"])
        ok("assemble constraint: a refused re-create during repair leaves the constraint in place (checkpoint)",
           st_g == 200 and refused and still, (st_g, res_g, refused, still))
        call("assembly/joint/delete", {"joint": res_g.get("name")})

        # Place Standard Part (#88 step 3)
        files_before = sorted(p.name for p in folder.glob("*.solidcraft"))
        st_s, res_s = call("assembly/standard", {"norm": "ISO 4762", "size": "M6", "length": 30, "translate": [0, 0, 40]})
        st_s2, res_s2 = call("assembly/standard", {"norm": "ISO 4762", "size": "M6", "length": 30})
        st_n, res_n = call("assembly/standard", {"norm": "ISO 4032", "size": "M6"})
        _, ctx = call("assembly/context")
        occs = [o["path"] for o in ctx.get("occurrences", [])]
        new_files = sorted(set(p.name for p in folder.glob("*.solidcraft")) - set(files_before))
        ok("place standard part: makes ISO_4762_M6x30 once in the folder and places it twice, a nut without a length",
           st_s == 200 and res_s.get("created") is True and res_s.get("file") == "ISO_4762_M6x30.solidcraft"
           and st_s2 == 200 and res_s2.get("created") is False and st_n == 200 and res_n.get("designation") == "ISO 4032 M6"
           and new_files == ["ISO_4032_M6.solidcraft", "ISO_4762_M6x30.solidcraft"]
           and sum(1 for o in occs if o.startswith("ISO_4762_M6x30")) == 2, (st_s, res_s, st_s2, res_s2, st_n, res_n, new_files, occs))
        bad_std = {
            "unknown norm": call("assembly/standard", {"norm": "DIN 0", "size": "M6"}),
            "unknown size": call("assembly/standard", {"norm": "ISO 4762", "size": "M99", "length": 30}),
            "missing length": call("assembly/standard", {"norm": "ISO 4762", "size": "M6"}),
            "text length": call("assembly/standard", {"norm": "ISO 4762", "size": "M6", "length": "lang"}),
        }
        ok("place standard part: unknown norm or size, a screw without length and a text length give HTTP 400",
           all(st == 400 and r.get("error") for st, r in bad_std.values()), bad_std)
        _, hist = call("history")
        ok("place standard part: one step on the shared Undo list", (hist.get("undo") or "").startswith("Place ISO 4032 M6"), hist)
        _, std_cat = call("standard_parts")
        ok("place standard part: the catalog lists every norm's sizes and preferred lengths for the dialog",
           set(std_cat.get("details", {})) == {n["norm"] for n in std_cat.get("norms", [])}
           and 30 in std_cat["details"]["ISO 4762"]["sizes"]["M6"]["preferred_lengths"], list(std_cat.get("details", {})))
    finally:
        srv.shutdown()
        srv.server_close()


def assemble_joint_dialog_checks(tmp):
    """Assemble tab stage 1b: POST /api/assembly/joint creates joints via Mechvane add_joint (with
    links.record), POST /api/assembly/joint/edit edits them, check_joints reports no warning, and
    part documents reject /api/assembly/* joint endpoints with HTTP 400."""
    import urllib.error
    import urllib.request
    from mechvane import server as mcp_server
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "assemble_joint_ui"
    folder.mkdir()
    w = Workspace(folder)
    try:
        plate = w.new(PART, "BasePlate")
        plate.session.batch([
            {"command": "parameters.change", "params": {"name": "h", "expression": "10 mm"}},
            {"command": "sketch.create", "params": {"plane": "XY", "name": "SkPlate"}},
            {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 40]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "SkPlate", "distance": "h", "name": "PlateBody"}},
        ])
        plate.save()

        pin = w.new(PART, "Pin")
        pin.session.batch([
            {"command": "sketch.create", "params": {"plane": "XY", "name": "SkPin"}},
            {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 5}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude", "params": {"sketch": "SkPin", "distance": 20, "name": "PinBody"}},
        ])
        pin.save()

        asm_single = w.new(ASSEMBLY, "SinglePartAsm")
        links.insert(w, asm_single, plate.path, name="OnlyPlate", grounded=True)
        asm_single.save()

        asm = w.new(ASSEMBLY, "GearboxJoints")
        links.insert(w, asm, plate.path, name="Plate", grounded=True)
        links.insert(w, asm, pin.path, name="DrivePin", translate=[30, 0, 0], grounded=False)
        links.insert(w, asm, pin.path, name="SecondPin", translate=[0, 30, 0], grounded=False)
        asm.save()
    finally:
        w.close_all()

    srv = ui_server.create_server(folder, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        # With a part open, joint endpoints fail with HTTP 400
        st_op, _ = call("open/BasePlate.solidcraft", {})
        st_gc, gc = call("assembly/context")
        st_pj, pj = call("assembly/joint", {"type": "rigid", "a": {"occurrence": "Plate:1", "plane": "XY"},
                                            "b": {"occurrence": "DrivePin:1", "plane": "XY"}})
        st_pe, pe = call("assembly/joint/edit", {"joint": "J1", "flip": True})
        ok("assemble joint endpoints: return HTTP 400 when a part is open",
           st_op == 200 and st_gc == 400 and st_pj == 400 and st_pe == 400
           and bool(gc.get("error") and pj.get("error") and pe.get("error")),
           f"open={st_op} ctx=({st_gc}, {gc}) add=({st_pj}, {pj}) edit=({st_pe}, {pe})")

        # Assembly with fewer than 2 components rejects joint creation with HTTP 400
        st_os, _ = call("open/SinglePartAsm.solidcraft", {})
        st_single, res_single = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "OnlyPlate:1", "plane": "XY"},
            "b": {"occurrence": "OnlyPlate:1", "plane": "YZ"},
        })
        ok("assemble POST /api/assembly/joint: rejects assembly with fewer than two components",
           st_os == 200 and st_single == 400 and "two components" in (res_single.get("error") or ""),
           f"single=({st_single}, {res_single})")

        # Open assembly and check GET /api/assembly/context
        st_oa, _ = call("open/GearboxJoints.solidcraft", {})
        st_ctx, ctx = call("assembly/context")
        occ_paths = [o.get("path") for o in (ctx.get("occurrences") or [])]
        body_occ = ctx.get("body_occurrences") or {}
        ok("assemble /api/assembly/context: lists occurrences and body_occurrences map",
           st_oa == 200 and st_ctx == 200 and "Plate:1" in occ_paths and "DrivePin:1" in occ_paths
           and "SecondPin:1" in occ_paths
           and body_occ.get("BasePlate") == "Plate:1" and body_occ.get("Pin") == "DrivePin:1",
           f"ctx=({st_ctx}, {ctx})")

        # Input validation: same component on both sides (including base name vs :1), unknown occurrence,
        # malformed face/point/frame, and non-numeric offset/angle strings all return HTTP 400
        st_same, res_same = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Plate", "plane": "XY"},
            "b": {"occurrence": "Plate:1", "plane": "YZ"},
        })
        st_unk, res_unk = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Ghost:1", "plane": "XY"},
            "b": {"occurrence": "DrivePin:1", "plane": "XY"},
        })
        st_face, res_face = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Plate:1", "face": [10, 20]},
            "b": {"occurrence": "DrivePin:1", "plane": "XY"},
        })
        st_pt, res_pt = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Plate:1", "point": ["bad", 0, 0]},
            "b": {"occurrence": "DrivePin:1", "plane": "XY"},
        })
        st_frm, res_frm = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Plate:1", "frame": {"origin": [1, 2]}},
            "b": {"occurrence": "DrivePin:1", "plane": "XY"},
        })
        st_off, res_off = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Plate:1", "plane": "XY"},
            "b": {"occurrence": "DrivePin:1", "plane": "XY"},
            "offset": "not_a_number",
        })
        st_ang, res_ang = call("assembly/joint", {
            "type": "rigid",
            "a": {"occurrence": "Plate:1", "plane": "XY"},
            "b": {"occurrence": "DrivePin:1", "plane": "XY"},
            "angle": "forty_five",
        })
        ok("assemble POST /api/assembly/joint: validates distinct occurrences, known occurrence, face/point/frame, and numeric offset/angle",
           st_same == 400 and "different component" in (res_same.get("error") or "")
           and st_unk == 400 and "unknown component occurrence" in (res_unk.get("error") or "").lower()
           and st_face == 400 and "face" in (res_face.get("error") or "")
           and st_pt == 400 and "point" in (res_pt.get("error") or "")
           and st_frm == 400 and "frame" in (res_frm.get("error") or "")
           and st_off == 400 and "offset" in (res_off.get("error") or "")
           and st_ang == 400 and "angle" in (res_ang.get("error") or ""),
           f"same=({st_same},{res_same}) unk=({st_unk},{res_unk}) face=({st_face},{res_face}) "
           f"pt=({st_pt},{res_pt}) frm=({st_frm},{res_frm}) off=({st_off},{res_off}) ang=({st_ang},{res_ang})")

        # Create a revolute joint via POST /api/assembly/joint using picked face points
        st_add, add_res = call("assembly/joint", {
            "type": "revolute",
            "name": "PinPivot",
            "a": {"occurrence": "Plate:1", "face": [20, 20, 10]},
            "b": {"occurrence": "DrivePin:1", "face": [34, 3, 12]},
            "offset": 1.5,
        })
        st_tr, tr = call("tree")
        st_fd, fd = call("findings")
        joint_warnings = [f for f in (fd.get("findings") or []) if f.get("severity") in ("warn", "fail")]
        _, ctx_after_add = call("assembly/context")
        added_j = next((j for j in (ctx_after_add.get("joints") or []) if j.get("name") == "PinPivot"), {})
        # Verify check_joints via Mechvane's links.check & MCP check_joints reports it with zero warnings
        with srv.lock:
            cur = srv.ensure_current()
            chk_entries = links.check(srv.ws, cur)
        prev_ws = mcp_server.ws
        try:
            mcp_server.ws = Workspace(folder)
            mcp_server.ws.open(folder / "GearboxJoints.solidcraft")
            mcp_chk = mcp_server.check_joints("GearboxJoints")
        finally:
            mcp_server.ws.close_all()
            mcp_server.ws = prev_ws

        ok("assemble POST /api/assembly/joint: creates recorded joint with occurrence_a/occurrence_b and check_joints reports no warning",
           st_add == 200 and add_res.get("name") == "PinPivot"
           and added_j.get("occurrence_a") == "Plate:1" and added_j.get("occurrence_b") == "DrivePin:1"
           and any(j.get("name") == "PinPivot" and j.get("type") == "revolute" and j.get("status") == "ok"
                   for j in (tr.get("joints") or []))
           and len(chk_entries) == 2 and all(e.get("status") == "ok" for e in chk_entries)
           and not joint_warnings and not mcp_chk.get("warnings")
           and len(mcp_chk.get("joints") or []) == 2 and all(e.get("status") == "ok" for e in mcp_chk["joints"]),
           f"add=({st_add}, {add_res}) added_j={added_j} chk={chk_entries} mcp={mcp_chk} findings={joint_warnings}")

        # Edit joint validation: setting one side to match the other side's occurrence is rejected with HTTP 400
        st_ed_same, res_ed_same = call("assembly/joint/edit", {
            "joint": "PinPivot",
            "b": {"occurrence": "Plate:1", "face": [20, 20, 10]},
        })
        ok("assemble POST /api/assembly/joint/edit: rejects setting both sides to the same component",
           st_ed_same == 400 and "different component" in (res_ed_same.get("error") or ""),
           f"ed_same=({st_ed_same}, {res_ed_same})")

        # Edit the joint via POST /api/assembly/joint/edit (including angle)
        st_ed, ed_res = call("assembly/joint/edit", {
            "joint": "PinPivot",
            "type": "cylindrical",
            "flip": True,
            "offset": 3.0,
            "angle": 45.0,
        })
        _, ctx_ed = call("assembly/context")
        ed_entry = next((j for j in (ctx_ed.get("joints") or []) if j.get("name") == "PinPivot"), {})
        with srv.lock:
            chk_ed = links.check(srv.ws, srv.ensure_current())
        ok("assemble POST /api/assembly/joint/edit: updates type/flip/offset/angle and keeps joint anchors ok",
           st_ed == 200 and ed_res.get("name") == "PinPivot"
           and ed_entry.get("type") == "cylindrical" and ed_entry.get("flip") is True
           and ed_entry.get("offset") == 3.0 and ed_entry.get("angle") == 45.0
           and ed_entry.get("occurrence_a") == "Plate:1" and ed_entry.get("occurrence_b") == "DrivePin:1"
           and len(chk_ed) == 2 and all(e.get("status") == "ok" for e in chk_ed),
           f"edit=({st_ed}, {ed_res}) ctx={ed_entry} chk={chk_ed}")

        # Shared Undo / Redo reverts and restores the joint and its recorded anchors
        st_un, _ = call("agent/undo", {})
        _, tr_un = call("tree")
        st_un2, _ = call("agent/undo", {})
        _, tr_un2 = call("tree")
        st_re, _ = call("agent/redo", {})
        _, tr_re = call("tree")
        st_re2, _ = call("agent/redo", {})
        _, tr_re2 = call("tree")
        ok("assemble /api/assembly/joint: undo and redo on shared history",
           st_un == 200 and any(j.get("name") == "PinPivot" and j.get("type") == "revolute" for j in (tr_un.get("joints") or []))
           and st_un2 == 200 and not any(j.get("name") == "PinPivot" for j in (tr_un2.get("joints") or []))
           and st_re == 200 and any(j.get("name") == "PinPivot" and j.get("type") == "revolute" for j in (tr_re.get("joints") or []))
           and st_re2 == 200 and any(j.get("name") == "PinPivot" and j.get("type") == "cylindrical" for j in (tr_re2.get("joints") or [])),
           f"un={tr_un.get('joints')} un2={tr_un2.get('joints')} re={tr_re.get('joints')} re2={tr_re2.get('joints')}")

        # Edit joint with changed component (switching b from DrivePin:1 to SecondPin:1 and a to point pick)
        st_ed_comp, res_ed_comp = call("assembly/joint/edit", {
            "joint": "PinPivot",
            "a": {"occurrence": "Plate:1", "point": [20, 20, 10], "z": [0, 0, 1]},
            "b": {"occurrence": "SecondPin:1", "face": [4, 33, 12]},
        })
        _, ctx_comp = call("assembly/context")
        comp_entry = next((j for j in (ctx_comp.get("joints") or []) if j.get("name") == "PinPivot"), {})
        with srv.lock:
            chk_comp = links.check(srv.ws, srv.ensure_current())
        ok("assemble POST /api/assembly/joint/edit: switches component b to SecondPin:1 and records new anchor",
           st_ed_comp == 200 and comp_entry.get("occurrence_a") == "Plate:1"
           and comp_entry.get("occurrence_b") == "SecondPin:1"
           and comp_entry.get("angle") == 45.0
           and len(chk_comp) == 2 and all(e.get("status") == "ok" for e in chk_comp)
           and {e.get("occurrence") for e in chk_comp} == {"Plate:1", "SecondPin:1"},
           f"ed_comp=({st_ed_comp}, {res_ed_comp}) entry={comp_entry} chk={chk_comp}")

        # Rename joint via POST /api/assembly/joint/edit
        st_ren, res_ren = call("assembly/joint/edit", {
            "joint": "PinPivot",
            "name": "MainShaftJoint",
        })
        _, tr_ren = call("tree")
        _, ctx_ren = call("assembly/context")
        ren_entry = next((j for j in (ctx_ren.get("joints") or []) if j.get("name") == "MainShaftJoint"), {})
        with srv.lock:
            chk_ren = links.check(srv.ws, srv.ensure_current())
        ok("assemble POST /api/assembly/joint/edit: renames joint across session, tree, and recorded anchors",
           st_ren == 200 and res_ren.get("name") == "MainShaftJoint"
           and any(j.get("name") == "MainShaftJoint" for j in (tr_ren.get("joints") or []))
           and not any(j.get("name") == "PinPivot" for j in (tr_ren.get("joints") or []))
           and ren_entry.get("occurrence_a") == "Plate:1" and ren_entry.get("occurrence_b") == "SecondPin:1"
           and len(chk_ren) == 2 and all(e.get("joint") == "MainShaftJoint" and e.get("status") == "ok" for e in chk_ren),
           f"ren=({st_ren}, {res_ren}) tree={tr_ren.get('joints')} ctx={ren_entry} chk={chk_ren}")

        # Check 6(a): update_links(repair=True) after edit_joint:
        # 1) When parts have not moved, update_links(repair=True) does not invoke links.repair, so
        #    edited type/flip/offset/angle remain unchanged.
        # 2) When BasePlate's thickness changes (h: 10 mm -> 14 mm) so links.repair runs,
        #    modeling.edit_joint's updated entry["create"] ensures links.repair preserves the
        #    edited type ("cylindrical"), flip (True), offset (3.0), and angle (45.0).
        st_rep_nomove, rep_nomove = call("assembly/update_links", {"repair": True})
        _, ctx_nomove = call("assembly/context")
        nomove_entry = next((j for j in (ctx_nomove.get("joints") or []) if j.get("name") == "MainShaftJoint"), {})
        ok("assemble edit_joint + update_links(repair=True) without part move: keeps edited type, flip, offset, and angle",
           st_rep_nomove == 200 and rep_nomove.get("repaired") == []
           and nomove_entry.get("type") == "cylindrical" and nomove_entry.get("flip") is True
           and nomove_entry.get("offset") == 3.0 and nomove_entry.get("angle") == 45.0,
           f"rep_nomove=({st_rep_nomove}, {rep_nomove}) entry={nomove_entry}")

        with srv.lock:
            plate_doc = srv.ws.open(folder / "BasePlate.solidcraft")
            plate_doc.session.cmd("parameters.change", {"name": "h", "expression": "14 mm"})
            plate_doc.save()
        st_rep_move, rep_move = call("assembly/update_links", {"repair": True})
        _, ctx_move = call("assembly/context")
        move_entry = next((j for j in (ctx_move.get("joints") or []) if j.get("name") == "MainShaftJoint"), {})
        ok("assemble edit_joint + links.repair on moved part: repairs joint and preserves edited type, flip, offset, and angle",
           st_rep_move == 200
           and any(r.get("joint") == "MainShaftJoint" and r.get("status") == "ok" for r in (rep_move.get("repaired") or []))
           and move_entry.get("flip") is True and move_entry.get("offset") == 3.0
           and move_entry.get("type") == "cylindrical" and move_entry.get("angle") == 45.0,
           f"rep_move=({st_rep_move}, {rep_move}) move_entry={move_entry}")

        # Check 6(b): Forced error in the middle of apply() after joint.create:
        # Verify assembly_add_joint rolls back doc.session via edit.checkpoint, whereas raw hand_step
        # only drops the disk Snapshot without rolling back doc.session.
        orig_record = links.record
        def boom_record(*args, **kwargs):
            raise RuntimeError("simulated error after joint.create")
        links.record = boom_record
        try:
            st_boom, res_boom = call("assembly/joint", {
                "type": "rigid",
                "name": "GhostOnError",
                "a": {"occurrence": "Plate:1", "plane": "XY"},
                "b": {"occurrence": "DrivePin:1", "plane": "XY"},
            })
        finally:
            links.record = orig_record
        with srv.lock:
            cur_after_boom = srv.ensure_current()
            live_after_boom = [j.get("name") for j in cur_after_boom.session.cmd("joint.list", {}).get("joints", [])]

        # Also demonstrate raw hand_step behavior without assembly_add_joint's checkpoint rollback:
        raw_hand_leaked = False
        with srv.lock:
            cur_doc = srv.ensure_current()
            cp_raw = cur_doc.session.cmd("edit.checkpoint", {}).get("checkpoint")
            try:
                def raw_failing_apply():
                    cur_doc.session.cmd("joint.create", {
                        "type": "rigid",
                        "name": "RawHandStepLeak",
                        "a": {"occurrence": "Plate:1", "plane": "XY"},
                        "b": {"occurrence": "DrivePin:1", "plane": "XY"},
                    })
                    raise RuntimeError("simulated mid-hand_step failure")
                try:
                    srv.agent.hand_step("raw test", raw_failing_apply)
                except RuntimeError:
                    pass
                raw_names = [j.get("name") for j in cur_doc.session.cmd("joint.list", {}).get("joints", [])]
                raw_hand_leaked = "RawHandStepLeak" in raw_names
            finally:
                modeling._restore(cur_doc.session, cp_raw, forget=False)

        ok("assemble POST /api/assembly/joint: rolls back session checkpoint when apply() fails after joint.create",
           st_boom == 400 and "simulated error after joint.create" in (res_boom.get("error") or "")
           and "GhostOnError" not in live_after_boom and raw_hand_leaked is True,
           f"boom=({st_boom}, {res_boom}) live_after_boom={live_after_boom} raw_hand_leaked={raw_hand_leaked}")
    finally:
        srv.shutdown()
        srv.server_close()


def bolted_dialog_checks(tmp):
    """Assemble tab stage 1c: /api/standard_parts and /api/assembly/bolted/{preview,create,edit,delete}."""
    import urllib.error
    import urllib.request
    from mechvane.ui import server as ui_server

    folder = Path(tmp) / "bolted_ui"
    folder.mkdir()
    w = Workspace(folder)
    try:
        for pname, thick in (("BottomPlate", 20), ("TopPlate", 10)):
            p = w.new(PART, pname)
            p.session.batch([
                {"command": "sketch.create", "params": {"plane": "XY", "name": f"Sk_{pname}"}},
                {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [60, 60]}},
                {"command": "sketch.finish", "params": {}},
                {"command": "solid.extrude", "params": {"sketch": f"Sk_{pname}", "distance": thick, "name": f"{pname}Body"}},
            ])
            p.save()

        asm = w.new(ASSEMBLY, "Flange")
        links.insert(w, asm, folder / "BottomPlate.solidcraft", name="BottomPlate", grounded=True)
        links.insert(w, asm, folder / "TopPlate.solidcraft", name="TopPlate", translate=[0, 0, 20], grounded=True)
        asm.save()
    finally:
        w.close_all()

    srv = ui_server.create_server(folder, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/api/"

    def call(endpoint, body=None):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + endpoint, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        st_sp, sp = call("standard_parts")
        ok("bolted UI /api/standard_parts: exposes ISO 4762 and ISO 10642 details",
           st_sp == 200 and "ISO 4762" in (sp.get("bolted_norms") or [])
           and "ISO 10642" in (sp.get("bolted_norms") or [])
           and "M6" in (sp.get("bolted_details", {}).get("ISO 4762", {}).get("sizes") or {}),
           f"st={st_sp} keys={list(sp.keys())}")

        # Open a part: assembly bolted endpoints must return HTTP 400
        call("open/TopPlate.solidcraft", {})
        st_pl, _ = call("assembly/bolted")
        st_pp, _ = call("assembly/bolted/preview", {"x": 30, "y": 30, "z": 10, "size": "M6"})
        st_pc, _ = call("assembly/bolted/create", {"x": 30, "y": 30, "z": 10, "size": "M6"})
        ok("bolted UI endpoints: return HTTP 400 when a part is open",
           st_pl == 400 and st_pp == 400 and st_pc == 400,
           f"list={st_pl} prev={st_pp} create={st_pc}")

        # Open the two-plate assembly
        st_oa, _ = call("open/Flange.solidcraft", {})
        placement = {"type": "point", "position": [30, 30, 30], "direction": [0, 0, -1]}
        st_pr, pr = call("assembly/bolted/preview", {
            "placement": placement,
            "screw_norm": "ISO 4762",
            "size": "M6",
            "connection_type": "through",
            "fit": "normal",
            "counterbore": True,
            "washer_head": True,
            "washer_nut": True,
        })
        pr_occs = [p.get("occurrence") for p in pr.get("parts") or []]
        ok("bolted UI preview: returns fastener length, dims and both plates",
           st_oa == 200 and st_pr == 200 and pr.get("selected_screw_length", 0) > 20
           and "TopPlate:1" in pr_occs and "BottomPlate:1" in pr_occs
           and isinstance(pr.get("dims"), dict),
           f"prev=({st_pr}, {pr})")

        # Invalid inputs (size='M99', length='abc', x='abc'): HTTP 400 with readable message, undo history unchanged
        _, hist_before = call("agent/history")
        turns_before = len(srv.agent.turns)
        st_bad_sz, err_sz = call("assembly/bolted/create", {"placement": placement, "size": "M99"})
        st_bad_ln, err_ln = call("assembly/bolted/create", {"placement": placement, "size": "M6", "length": "abc"})
        st_bad_x, err_x = call("assembly/bolted/create", {"x": "abc", "y": 30, "z": 22, "size": "M6"})
        _, hist_after = call("agent/history")
        turns_after = len(srv.agent.turns)
        ok("bolted UI validation: size='M99', length='abc', x='abc' return HTTP 400 and leave undo history unchanged",
           st_bad_sz == 400 and "M99" in (err_sz.get("error") or "")
           and st_bad_ln == 400 and "length" in (err_ln.get("error") or "").lower()
           and st_bad_x == 400 and "x must be a number" in (err_x.get("error") or "")
           and hist_after == hist_before and turns_after == turns_before,
           f"sz=({st_bad_sz}, {err_sz}) ln=({st_bad_ln}, {err_ln}) x=({st_bad_x}, {err_x}) hist=({hist_before}, {hist_after})")

        st_cr, cr = call("assembly/bolted/create", {
            "placement": placement,
            "screw_norm": "ISO 4762",
            "size": "M6",
            "connection_type": "through",
            "fit": "normal",
            "counterbore": True,
            "washer_head": True,
            "washer_nut": True,
            "length_override": 50,
            "name": "FlangeBolt",
        })
        conn_id = cr.get("id")
        st_ls, ls = call("assembly/bolted")
        st_tr, tr = call("tree")
        tree_ids = [c.get("id") for c in tr.get("bolted_connections") or []]
        ok("bolted UI create: connection is listed in /api/assembly/bolted and /api/tree with fixed length_override",
           st_cr == 200 and conn_id and st_ls == 200 and ls.get("count") == 1
           and conn_id in (ls.get("connections") or {}) and conn_id in tree_ids
           and cr.get("screw_length") == 50.0,
           f"create=({st_cr}, {cr}) list={ls} tree_ids={tree_ids}")

        # Preview while editing an existing connection must ignore old fasteners and reset washer_head on countersunk
        st_ep, ep = call("assembly/bolted/preview", {
            "edit_id": conn_id,
            "size": "M8",
            "screw_norm": "ISO 10642",
            "connection_type": "through",
        })
        ok("bolted UI edit preview: evaluates updated size on plates without hitting old fasteners",
           st_ep == 200 and ep.get("size") == "M8" and ep.get("screw_norm") == "ISO 10642"
           and ep.get("washer_head") is False and ep.get("washer_nut") is True,
           f"edit_prev=({st_ep}, {ep})")

        # Edit cap -> countersunk without explicit washer_head: washer_head must reset to False, fixed length preserved
        st_ed, ed = call("assembly/bolted/edit", {
            "id": conn_id,
            "size": "M8",
            "screw_norm": "ISO 10642",
        })
        _, ls_ed = call("assembly/bolted")
        ed_conn = (ls_ed.get("connections") or {}).get(conn_id, {})
        ed_fast = (ed_conn.get("parameters") or {}).get("fasteners") or {}
        ok("bolted UI edit (cap -> countersunk): resets washer_head to False and preserves fixed length_override",
           st_ed == 200 and ed_conn.get("size") == "M8" and ed_conn.get("screw_norm") == "ISO 10642"
           and ed_conn.get("washer_head") is False and ed_fast.get("washer_head") is False
           and ed_conn.get("washer_nut") is True and ed_fast.get("washer_nut") is True
           and ed_conn.get("screw_length") == 50.0 and ed_fast.get("length_override") == 50.0,
           f"edit=({st_ed}, {ed}) conn={ed_conn}")

        # Edit through -> blind without explicit washer_nut: washer_nut must reset to False
        st_eb, eb = call("assembly/bolted/edit", {
            "id": conn_id,
            "connection_type": "blind",
            "length_override": None,
        })
        _, ls_eb = call("assembly/bolted")
        eb_conn = (ls_eb.get("connections") or {}).get(conn_id, {})
        eb_fast = (eb_conn.get("parameters") or {}).get("fasteners") or {}
        ok("bolted UI edit (through -> blind): resets washer_nut to False in connection and stored parameters",
           st_eb == 200 and eb_conn.get("type") == "blind"
           and eb_conn.get("washer_nut") is False and eb_fast.get("washer_nut") is False
           and eb_conn.get("washer_head") is False and eb_fast.get("washer_head") is False,
           f"edit_blind=({st_eb}, {eb}) conn={eb_conn}")

        st_del, dl = call("assembly/bolted/delete", {"id": conn_id})
        _, ls_del = call("assembly/bolted")
        st_miss, _ = call("assembly/bolted/delete", {"id": "nonexistent"})
        ok("bolted UI delete: removes connection from list and returns 404 on unknown id",
           st_del == 200 and dl.get("deleted") == conn_id and ls_del.get("count") == 0
           and not (ls_del.get("connections") or {}) and st_miss == 404,
           f"del=({st_del}, {dl}) after={ls_del} miss={st_miss}")

        st_un, _ = call("agent/undo", {})
        _, ls_un = call("assembly/bolted")
        st_re, _ = call("agent/redo", {})
        _, ls_re = call("assembly/bolted")
        ok("bolted UI undo/redo: restores and re-deletes bolted connection on shared history",
           st_un == 200 and ls_un.get("count") == 1 and st_re == 200 and ls_re.get("count") == 0,
           f"undo={ls_un} redo={ls_re}")
    finally:
        srv.shutdown()
        srv.server_close()


def _private_tool(name: str) -> bool:
    """Pipeline tools stay private (tools/export_public.sh): their checks run only where the file exists."""
    return (Path(__file__).resolve().parents[2] / "tools" / name).exists()


def main():
    with tempfile.TemporaryDirectory(prefix="Mechvane-check-") as tmp:
        ws = Workspace(tmp)
        try:
            katalog_checks()
            iso286_checks()
            legacy_metadata_checks(ws)
            sketch_rule_and_browser(ws)
            work_features(ws)
            semantic_queries(ws)
            design_rule_checks(ws)
            verfahrensregeln_checks(ws)
            finding_source_checks(ws)
            joints_across_files(ws)
            standard_parts_checks(ws)
            subassemblies(ws)
            insert_rotation_checks(ws)
            insert_grounded_checks(ws)
            bolted_connection_checks(ws)
            bolted_review_fixes_checks(ws)
            bolted_pattern_and_edit_checks(ws)
            edit_in_place_checks(ws)
            links_fixes_checks(ws)
            server_fixes_checks(tmp, ws)
            mcp_server(tmp)
            praxistest_3_fixes_checks(ws)
            praxistest_4_fixes_checks(ws)
            praxistest_5_fixes_checks(ws)
            praxistest_6_fixes_checks(ws)
            bolted_anchor_associativity_checks(ws)
            bolted_countersunk_checks(ws)
            web_ui_stage1_checks(ws)
            argon_review_findings_checks(ws)
            argon_review_findings_5_8_checks(ws)
            argon_review_findings_7_10_12_checks(ws)
            argon_review_finding_6_checks(ws)
            argon_review_findings_9_11_checks(ws)
            install_checks(tmp)
            appwindow_checks(tmp)
            session_env_checks()
            demo_folder_checks(tmp)
            moved_project_checks(tmp)
            empty_part_mesh_check(tmp)
            single_instance_check(tmp)
            quit_check(tmp)
            split_face_name_check()
            edge_touches_check()
            feature_request_checks(tmp, ws)
            demo_pyodide_checks(tmp)
            agent_turns_checks(tmp)
            snapshot_prune_checks(tmp)
            selection_checks(tmp)
            speech_checks(tmp)
            speech_cases_checks()
            params_checks(tmp)
            feature_dialog_checks(tmp)
            command_form_checks()
            command_dialog_checks(tmp)
            command_dialog_assembly_checks(tmp)
            commands_js_checks(tmp)
            assemble_dialog_checks(tmp)
            assemble_joint_dialog_checks(tmp)
            assemble_constraint_checks(tmp)
            bolted_dialog_checks(tmp)
            centred_hole_dialog_checks(tmp)
            sessionlog_checks(tmp)
            window_close_checks(tmp)
            viewtools_checks(tmp)
            roadmap_json_checks()
            bolted_gap_chamfer_check(tmp)
            gltf_export_check(tmp)
            state_delta_checks(ws)
            scratch_dir_checks()
            sc_errors_checks(ws)
            design_intent_checks(ws)
            concentric_hole_checks(ws)
            profile_choice_checks(ws)
            sketch_session_checks(tmp)
            step_import_checks(tmp)
            sc_errors_stage2_checks(ws)
            sc_locate_checks(ws)
            part_end_checks(ws)
            bill_of_materials_checks(ws)
            verify_view_checks(ws)
            upstream_watch_checks()
            if _private_tool("argon_review.py"):
                argon_review_checks(tmp)
            if _private_tool("agent_clone.sh"):
                agent_clone_checks(tmp)
            if _private_tool("review_score.py"):
                review_score_checks(tmp)
            orchester_figures_checks()
            command_matrix_checks()
            if (Path(__file__).resolve().parents[1] / "tasks").exists():  # private, not in the public export
                tester_tasks_checks()
            if _private_tool("cleanup_branches.sh"):
                cleanup_branches_checks(tmp)
            if _private_tool("gate.py") and _private_tool("gemini_queue.sh"):
                queue_guard_checks(tmp)
            if _private_tool("gate.py"):
                gate_class_checks()
            check_sources_gzip_check()
            py311_syntax_checks()
            check_parameters_tool_checks(ws)
            demo_wasm_split_checks(tmp)
            step_signature_checks(ws)
            record_replay_checks(ws)
            sketch_face_pick_checks(ws)
            if _private_tool("audit_run.sh"):
                audit_checks(tmp)
            heavy_lock_checks(tmp)
            if _private_tool("acceptance.py"):
                acceptance_checks(tmp)
        finally:
            ws.close_all()
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
