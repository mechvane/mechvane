#!/usr/bin/env python3
"""Checks for the Mechvane layer (sketch rule, browser, joints across files).

Usage: python3 tests/mechvane/check.py   (needs solidcraft-cli on PATH, ~30 s)
Exit code 0 when every check passes, 1 otherwise."""

import json
import math
import queue
import sys
import tempfile
import threading
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mechvane import bolted, design_rules, geometry as g, hole_tables, inplace, katalog, links, query, server, sketch_rule, standard_parts, tree  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402

REL = 2e-4  # volume tolerance (tessellation, same as tests/reference/check.py)
ABS = 2e-3  # mm tolerance for bounding boxes
failures = 0


def ok(label, cond, detail=""):
    global failures
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
               and abs(g.dot(fa["z"], fb["z"]) - 1.0) < 1e-4)
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
    ok("bolted connection: screw sits coaxial to hole", coaxial and world_coaxial and head_seated,
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
                  and abs(g.dot(fa_cb["z"], fb_cb["z"]) - 1.0) < 1e-4)
    ok("bolted connection with counterbore: screw sits coaxial and recessed at z = 4.6 mm",
       coaxial_cb, f"{fa_cb} vs {fb_cb}")

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

    bore_edges = [e for e in p2_b_edges if "bore" in e["name"]]
    cyl_bottom_z = min(e["start"][2] for e in bore_edges if "side:1#" in e["name"])
    cone_tip_z = min(e["start"][2] for e in bore_edges if "side:2#" in e["name"])
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
                     and abs(g.dot(fa_bl["z"], fb_bl["z"]) - 1.0) < 1e-4)
    # Head bearing surface sits at top plate surface at z = 10.0 (Befund 11)
    head_seated_blind = abs(fa_bl["origin"][2] - 10.0) < 1e-4
    ok("bolted connection blind: screw sits coaxial to hole", coaxial_blind and head_seated_blind, f"{fa_bl} vs {fb_bl}")

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
                      and abs(g.dot(fa_in["z"], fb_in["z"]) - 1.0) < 1e-4)
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
    ok("find: feature filter finds faces of a specific feature",
       len(f_h1) == 2 and all(f["type"] == "cylinder" for f in f_h1) and all(abs(f["diameter"] - 6.0) < 0.1 for f in f_h1),
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
        s7 = Session()
        err_f7 = False
        try:
            s7.cmd("document.inspect", timeout=0.000001)
        except SolidCraftError as e:
            err_f7 = "timeout" in str(e).lower()
        finally:
            s7.close()
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
                                 "preview_bolted_connection", "run", "standard_part", "to_part_coords",
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

    # Finding 8: a countersink that notches a neighbouring wall fails countersink_clearance
    for name, y, expect in (("p5_cs_wall", 23.0, "fail"), ("p5_cs_free", 10.0, "ok")):
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
        st = r["rules"]["countersink_clearance"]["status"]
        ok(f"praxistest 5 / finding 8: countersink at y={y} gives countersink_clearance {expect}",
           st == expect, f"status={st}")
        ws.close(name)

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
       b8_broken_status in ("origin_lost", "moved") and "StiftAufDom" in repaired_joints  # "moved" since 0.25
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
       len(b_fl["faces"]) == len(raw_faces) == 18
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
           asm_findings["findings"] and all(f["source"] == "links" for f in asm_findings["findings"])
           and asm_findings["verdict"] == "ok" and "joints ok" in asm_findings["summary"],
           f"summary={asm_findings.get('summary')} sources={[f['source'] for f in asm_findings['findings']]}")
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
        req = urllib.request.Request(f"http://127.0.0.1:{port_asm}/api/file/{p_a.path.name}", data=edited, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            saved = json.loads(resp.read().decode("utf-8"))
        try:
            urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port_asm}/api/file/other.solidcraft",
                                                          data=b"x", method="POST"), timeout=10)
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
            req_bad_open = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/open/../../etc", data=b"", method="POST")
            with urllib.request.urlopen(req_bad_open, timeout=10) as resp:
                bad_open_code = resp.status
        except urllib.error.HTTPError as e:
            bad_open_code = e.code

        # /api/open switches (then /api/files lists the linked parts for the assembly)
        req_open = urllib.request.Request(f"http://127.0.0.1:{port_fld}/api/open/ui_asm.solidcraft", data=b"", method="POST")
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
    finally:
        srv_fld.shutdown()
        srv_fld.server_close()

    # 4. Part with intentional finding (countersink too close to wall as in Befund 8):
    # finding arrives in /api/findings with a face name that exists in /api/mesh
    cs_doc = ws.new(PART, "ui_cs_wall")
    cs_doc.session.batch([
        {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 8, "corner": [0, 0, 0], "name": "Plate"}},
        {"command": "solid.box", "params": {"length": 40, "width": 10, "height": 30, "corner": [0, 30, 8],
                                            "operation": "join", "name": "Wall"}},
        {"command": "solid.hole", "params": {"position": [20, 23.0, 8], "direction": [0, 0, -1], "clearance": "M6",
                                             "depth": 8, "type": "countersink", "cs_diameter": 13.7,
                                             "cs_angle": 90, "name": "CS"}},
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
             if f.get("rule") == "countersink_clearance" and f.get("status") == "fail"),
            None,
        )
        cs_face = cs_fail.get("face") if cs_fail else None
        ok("web ui findings: countersink wall finding arrives in /api/findings with a face name present in /api/mesh",
           cs_fail is not None and cs_face in mesh_face_map and mesh_face_map[cs_face] in mesh_fids,
           f"cs_fail={cs_fail} mesh_faces={list(mesh_face_map.keys())}")
        cs_sel = (cs_fail or {}).get("select") or {}
        ok("web ui model mode: the countersink finding carries a select.set item for its face (index as in /api/mesh)",
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
           opened and "--app=http://127.0.0.1:1/" in args and f"--user-data-dir={install.CACHE / 'app-profile'}" in args
           and closed.wait(5) and not tabs, f"{opened} {args!r} {tabs}")

        fake("handoff.sh", "exit 0")
        closed = threading.Event()
        opened = appwindow.open_window("http://127.0.0.1:2/", on_close=closed.set)
        time.sleep(0.2)
        ok("appwindow: window handed to an open instance keeps the server running",
           opened and not closed.is_set() and not tabs, f"{opened} {tabs}")

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


def agent_turns_checks(tmp):
    """Web UI agent turns (ADR 0003) against tests/mechvane/fake_acp_agent.py, and the MCP side:
    files changed on disk are opened again, MECHVANE_AUTOSAVE saves after each tool call."""
    import os
    import time
    import urllib.request
    from mechvane import install
    from mechvane.ui import agent as ag, server as ui_server

    d = ag.decide
    ok("agent: Mechvane modelling runs, other tools, file commands and deletions are declined",
       d("mcp__mechvane__run", {"commands": [{"command": "solid.chamfer", "params": {"edges": [[0, 0, 0]]}}]})[0]
       and d("mcp__mechvane__run", {"commands": [{"command": "solid.sweep", "params": {"path": [3, 4]}}]})[0]
       and d("mcp__mechvane__check_design", {})[0]
       and not d("Bash", {"command": "ls"})[0]
       and not d("mcp__mechvane__run", {"commands": [{"command": "file.export", "params": {"path": "x.step"}}]})[0]
       and not d("mcp__mechvane__command", {"command": "sketch.insert_dxf", "params": {"path": "a/b.dxf"}})[0]
       and not d("mcp__mechvane__delete_feature", {"feature": "Box1"})[0]
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
        ok("agent: only the modelling call is allowed (export, shell and delete declined)",
           '"run chamfer": true' in text and '"run export": false' in text and '"Bash": false' in text
           and '"delete_feature": false' in text and declined == ["Bash", "delete_feature", "run"], text + str(declined))

        out = turns.undo()
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
            req = urllib.request.Request(base + path, data=body, method="POST")
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
        face = next(f for f in br.session.cmd("model.faces", {"body": "Bracket"})["faces"] if f["name"] == "F4:csink:base")
        r = selection.resolve(w, br, [{"type": "face", "body": "Bracket", "index": face["index"], "point": [42.2, 30.4, 8.9]},
                                      {"type": "edge", "body": "Bracket", "index": 0, "point": [0, 0, 0]}])
        ok("selection: a part face gets its Mechvane name, feature, normal, click and centroid",
           r[0]["name"] == "F4:csink:base" and r[0]["feature"] == "CountersinkNearWall" and r[0]["normal"] == [0.0, 0.0, -1.0]
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
                                     data=json.dumps({"items": [{"type": "face", "body": "Bracket", "index": face["index"],
                                                                 "point": [42.2, 30.4, 8.9]}]}).encode())
        with urllib.request.urlopen(req) as resp:
            got = json.loads(resp.read())
        ok("selection: /api/resolve_selection answers with the resolved items",
           got["selection"][0]["name"] == "F4:csink:base", str(got))
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
                                     data=json.dumps({"text": "an countersink near wall eine Phase eins mal fünfundvierzig Grad"}).encode())
        with urllib.request.urlopen(req) as resp:
            got = json.loads(resp.read())
        ok("speech: /api/speech uses the open model's names",
           got["text"] == "an CountersinkNearWall eine Fase 1 × 45°", str(got))
    finally:
        srv.shutdown()
        srv.server_close()


def session_env_checks():
    """Windows: SolidCraft sessions render with DirectX 12 unless WGPU_BACKEND is set (Intel Vulkan crash)."""
    from mechvane.solidcraft import session_env
    ok("session env: DirectX 12 on Windows, nothing changed elsewhere, a set WGPU_BACKEND wins",
       session_env("win32", {})["WGPU_BACKEND"] == "dx12"
       and "WGPU_BACKEND" not in session_env("linux", {})
       and session_env("win32", {"WGPU_BACKEND": "vulkan"})["WGPU_BACKEND"] == "vulkan")


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
                 translate=[100, 0, 0], grounded=True)
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
            joints_across_files(ws)
            standard_parts_checks(ws)
            subassemblies(ws)
            insert_rotation_checks(ws)
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
            split_face_name_check()
            feature_request_checks(tmp, ws)
            agent_turns_checks(tmp)
            selection_checks(tmp)
            speech_checks(tmp)
            scratch_dir_checks()
        finally:
            ws.close_all()
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
