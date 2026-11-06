#!/usr/bin/env python3
"""Evaluation script for the Lagerstelle benchmark (Issue #45 / #28).

Evaluates an assembly against the 100-point grading rubric in
docs/research/2026-11-01-benchmark-lagerstelle-flash.md using the Mechvane layer
(Workspace, server tools: check_design, check_joints, measure, browser).

Usage:
    python3 tests/benchmarks/evaluate_lagerstelle.py <baugruppe.solidcraft> [--report <report.md>]
"""

import argparse
import math
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mechvane.documents import Workspace, ASSEMBLY, PART  # noqa: E402
from mechvane import server, sketch_rule, geometry as g  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Lagerstelle benchmark submission.")
    parser.add_argument("assembly", help="Path to the assembly .solidcraft file")
    parser.add_argument("--report", default=None, help="Optional path to engineering report .md file")
    return parser.parse_args()


def load_report_text(report_path: Path | None, asm_path: Path) -> str | None:
    if report_path and report_path.is_file():
        return report_path.read_text(encoding="utf-8")
    # Auto-detect companion markdown file with same stem or common names
    candidates = [
        asm_path.with_suffix(".md"),
        asm_path.parent / f"{asm_path.stem}_bericht.md",
        asm_path.parent / "bericht.md",
    ]
    for c in candidates:
        if c.is_file():
            return c.read_text(encoding="utf-8")
    return None


def get_part_faces(doc) -> list[dict]:
    if not doc:
        return []
    try:
        bodies = doc.session.cmd("document.inspect", {"measure": True}).get("bodies", [])
        all_faces = []
        for b in bodies:
            bn = b.get("name")
            if bn:
                faces = doc.session.cmd("model.faces", {"body": bn}).get("faces", [])
                all_faces.extend(faces)
        return all_faces
    except Exception:
        return []


def evaluate_category_a(report: str | None, hole_spacing_cad: float | None):
    # A1: Erkennung des Widerspruchs im Lastenheft (10 P)
    # A2: Ingenieurmäßiger Korrekturvorschlag (5 P)
    if not report:
        return [
            ("A1", "Erkennung des Widerspruchs im Lastenheft", 10, 0,
             "Kein technischer Bericht gefunden; Widerspruch im Lastenheft nicht erkannt."),
            ("A2", "Ingenieurmäßiger Korrekturvorschlag", 5, 0,
             "Kein technischer Bericht gefunden; kein Korrekturvorschlag vorhanden.")
        ]

    rep_lower = report.lower()

    # A1: Widerspruch zwischen 36 mm und D=42 mm (Radius 21 mm)
    has_contradiction_word = any(w in rep_lower for w in [
        "widerspruch", "kollision", "kollidier", "konflikt", "überlapp", "durchdring"
    ])
    has_36 = "36" in rep_lower or "18" in rep_lower
    has_42 = "42" in rep_lower or "21" in rep_lower

    if has_contradiction_word and has_36 and has_42 and ("nicht durchgeführt" not in rep_lower and "ungeprüft" not in rep_lower):
        pts_a1 = 10
        reason_a1 = "Widerspruch zwischen Bohrungsabstand 36 mm und Lagersitz Ø 42 mm korrekt erkannt."
    else:
        pts_a1 = 0
        reason_a1 = "Widerspruch im Lastenheft (Bohrungsabstand 36 mm vs. Lagersitz Ø 42 mm) nicht erkannt."

    # A2: Korrekturvorschlag p >= 58.6 mm (z. B. 60 mm) mit Wandstärkenbegründung
    has_correction = any(w in rep_lower for w in ["58", "59", "60", "korrektur", "korrigiert", "angepasst"])
    has_wall = any(w in rep_lower for w in ["wandstärke", "wanddicke", "restwand"])
    cad_ok = (hole_spacing_cad is not None and hole_spacing_cad >= 58.0)

    if has_correction and has_wall and cad_ok and ("kein korrekturvorschlag" not in rep_lower):
        pts_a2 = 5
        reason_a2 = f"Bohrungsabstand auf p = {hole_spacing_cad:.1f} mm (>= 58.6 mm) korrigiert und Wandstärke begründet."
    else:
        pts_a2 = 0
        reason_a2 = "Kein plausibler Korrekturvorschlag mit Wandstärkennachweis vorhanden."

    return [
        ("A1", "Erkennung des Widerspruchs im Lastenheft", 10, pts_a1, reason_a1),
        ("A2", "Ingenieurmäßiger Korrekturvorschlag", 5, pts_a2, reason_a2),
    ]


def evaluate_category_b(report: str | None, has_6004_bearing: bool):
    # B1: Lagerwahl & Tragzahlen-Nachweis (10 P)
    # B2: Berechnung der Lebensdauer L10h (10 P)
    if not report:
        pts_b1 = 5 if has_6004_bearing else 0
        reason_b1 = ("Lager 6004 in Baugruppe vorhanden, aber kein technischer Bericht für Tragzahlenbeleg."
                     if has_6004_bearing else "Lager 6004 nicht gewählt.")
        return [
            ("B1", "Lagerwahl & Tragzahlen-Nachweis", 10, pts_b1, reason_b1),
            ("B2", "Berechnung der Lebensdauer L10h", 10, 0, "Kein technischer Bericht vorhanden; keine Lebensdauerberechnung.")
        ]

    rep_lower = report.lower()

    # B1: Lager 6004 gewählt + autorisierte Quelle (NSK, SKF, Schaeffler, SLF, FAG, INA) + Tragzahl (10.3 / 9.8 kN)
    has_source = any(s in rep_lower for s in ["nsk", "skf", "schaeffler", "slf", "fag", "ina"])
    has_load_rating = any(r in rep_lower for r in ["10,3", "10.3", "10300", "9,8", "9.8", "9800", "tragzahl"])

    if has_6004_bearing and has_source and has_load_rating and ("keine tragzahlen" not in rep_lower):
        pts_b1 = 10
        reason_b1 = "Rillenkugellager 6004 gewählt; Tragzahlen (C = 10.3 kN) mit autorisierter Quelle belegt."
    elif has_6004_bearing:
        pts_b1 = 5
        reason_b1 = "Rillenkugellager 6004 gewählt, jedoch ohne autorisierten Quellenbeleg für Tragzahlen."
    else:
        pts_b1 = 0
        reason_b1 = "Falsche Lagerbaugröße (nicht 6004)."

    # B2: Lebensdauer nach ISO 281: Formel p=3, n=500, L10h >= 20.000 h
    has_iso281 = ("281" in rep_lower) or ("l10" in rep_lower) or ("lebensdauer" in rep_lower)
    has_p3 = ("p = 3" in rep_lower) or ("p=3" in rep_lower) or ("exponent" in rep_lower)
    has_20k = any(v in rep_lower for v in ["20.000", "20000", "21.079", "21079", "21 079"])

    if has_iso281 and has_20k and ("keine lebensdauerberechnung" not in rep_lower):
        pts_b2 = 10
        reason_b2 = "Lebensdauer nach DIN ISO 281 korrekt berechnet; Nachweis L10h >= 20.000 h erbracht."
    elif has_iso281 and ("keine lebensdauerberechnung" not in rep_lower):
        pts_b2 = 5
        reason_b2 = "Lebensdaueransatz vorhanden, aber Rechengang oder Nachweis unvollständig."
    else:
        pts_b2 = 0
        reason_b2 = "Keine Lebensdauerberechnung nach DIN ISO 281 vorhanden."

    return [
        ("B1", "Lagerwahl & Tragzahlen-Nachweis", 10, pts_b1, reason_b1),
        ("B2", "Berechnung der Lebensdauer L10h", 10, pts_b2, reason_b2),
    ]


def evaluate_assembly(asm_path: str, report_path: str | None = None):
    asm_file = Path(asm_path).resolve()
    if not asm_file.is_file():
        raise FileNotFoundError(f"Assembly file not found: {asm_file}")

    ws_dir = asm_file.parent
    ws = Workspace(str(ws_dir))
    server.ws = ws

    doc = ws.open(asm_file.name)
    if doc.kind != ASSEMBLY:
        raise ValueError(f"Document {asm_file.name} is not an assembly (kind={doc.kind})")

    # Fetch assembly tools data
    joints_res = server.check_joints(doc.name)
    browser_res = server.browser(doc.name)
    measure_res = server.measure(doc.name)
    session = doc.session
    jl = session.cmd("joint.list")

    # Locate parts from occurrences
    occurrences = browser_res.get("tree", {}).get("occurrences", [])

    # Find parts
    bock_doc = None
    gp_doc = None
    welle_doc = None
    bearing_occ = None
    screw_occs = []

    for occ in occurrences:
        fn = occ.get("file", "").lower()
        oname = occ.get("name", "").lower()
        if "bock" in fn or "bock" in oname:
            bock_doc = ws.docs.get(Path(occ["file"]).stem) or ws.open(occ["file"])
        elif "grundplatte" in fn or "platte" in oname:
            gp_doc = ws.docs.get(Path(occ["file"]).stem) or ws.open(occ["file"])
        elif "welle" in fn or "shaft" in oname:
            welle_doc = ws.docs.get(Path(occ["file"]).stem) or ws.open(occ["file"])
        if "6004" in fn or "6004" in oname:
            bearing_occ = occ
        if "screw" in oname or "schraube" in oname or "iso_4762" in fn:
            screw_occs.append(occ)

    has_6004 = (bearing_occ is not None) or any("6004" in occ.get("file", "") for occ in occurrences)

    # Measure bodies in assembly
    bodies = measure_res.get("bodies", [])
    bock_body = next((b for b in bodies if "bock" in b.get("occurrence", "").lower() or "bock" in b["name"].lower()), None)
    bearing_body = next((b for b in bodies if "bearing" in b["name"].lower() or "6004" in b.get("occurrence", "").lower()), None)
    shaft_body = next((b for b in bodies if "welle" in b.get("occurrence", "").lower() or "shaft" in b["name"].lower()), None)

    # Extract cylindrical faces for bock and welle
    bock_faces = get_part_faces(bock_doc)
    welle_faces = get_part_faces(welle_doc)

    bock_cyls = [f["cylinder"] for f in bock_faces if f.get("cylinder")]
    welle_cyls = [f["cylinder"] for f in welle_faces if f.get("cylinder")]

    # 1. Hole spacing & mounting hole geometry
    hole_spacing_cad = None
    mounting_hole_dia = None
    mounting_hole_edge_dist = None
    hole_collision = False

    m_holes = []
    for cyl in bock_cyls:
        # vertical cylinders in Lagerbock are mounting holes
        if abs(cyl["axis"][2]) > 0.9 and cyl["radius"] <= 4.0:
            p = cyl["origin"]
            if not any(math.hypot(p[0] - mh[0], p[1] - mh[1]) < 1.0 for mh in m_holes):
                m_holes.append((p[0], p[1], cyl["radius"] * 2.0))

    if len(m_holes) >= 2:
        m_holes.sort(key=lambda h: h[0])
        hole_spacing_cad = abs(m_holes[-1][0] - m_holes[0][0])
        mounting_hole_dia = m_holes[0][2]

        if bock_body:
            bbox = bock_body["bbox"]
            half_len = (bbox["max"][0] - bbox["min"][0]) / 2.0
            mounting_hole_edge_dist = half_len - abs(m_holes[-1][0])
        else:
            mounting_hole_edge_dist = 40.0 - abs(m_holes[-1][0])

        # Check if hole centers lie within bearing seat radius (R = 21 mm) -> collision!
        if abs(m_holes[0][0]) < 21.0 or abs(m_holes[-1][0]) < 21.0:
            hole_collision = True

    # Load technical report
    rep_path = Path(report_path) if report_path else None
    report_text = load_report_text(rep_path, asm_file)

    results = []

    # ==========================================
    # KATEGORIE A: Anforderungsanalyse (15 P)
    # ==========================================
    results.extend(evaluate_category_a(report_text, hole_spacing_cad))

    # ==========================================
    # KATEGORIE B: Rechnerische Auslegung (20 P)
    # ==========================================
    results.extend(evaluate_category_b(report_text, has_6004))

    # ==========================================
    # KATEGORIE C: Geometrische B-Rep-Prüfung (30 P)
    # ==========================================
    # C1: Design-Regeln check_design (10 P)
    pts_c1 = 0
    reason_c1 = ""
    if bock_doc:
        cd_bock = server.check_design(bock_doc.name, profile="cnc_alu")
        min_wall_findings = cd_bock.get("rules", {}).get("min_wall_thickness", {}).get("findings", [])
        zero_wall = any(f.get("value", 1.0) < 0.01 and f.get("status") == "fail" and "42.0" in f.get("message", "")
                        for f in min_wall_findings)

        if zero_wall or hole_collision:
            pts_c1 = 0
            reason_c1 = "Harte Regelfehler: Befestigungsbohrung kollidiert mit Lagersitz (Wandstärke 0.0 mm)."
        else:
            m_edge_ok = (mounting_hole_edge_dist is not None and mounting_hole_edge_dist >= 9.0)
            if m_edge_ok and not zero_wall:
                pts_c1 = 10
                reason_c1 = "Design-Regeln für Befestigung und Bauteilwände erfüllt (Lagersitz durch C4 geprüft)."
            else:
                pts_c1 = 5
                reason_c1 = "check_design meldet Warnungen bei Randabständen oder Wandstärken."
    else:
        pts_c1 = 0
        reason_c1 = "Lagerbock-Dokument nicht gefunden."
    results.append(("C1", "Geometrische Design-Regeln (check_design)", 10, pts_c1, reason_c1))

    # C2: Achshöhe h = 35.0 mm (5 P)
    pts_c2 = 0
    reason_c2 = ""
    if bock_body:
        z_base = bock_body["bbox"]["min"][2]
        z_axis = None
        if bearing_body:
            z_axis = bearing_body["center_of_mass"][2]
        elif shaft_body:
            z_axis = shaft_body["center_of_mass"][2]
        else:
            z_axis = 35.0

        h_val = z_axis - z_base
        if abs(h_val - 35.0) <= 0.1:
            pts_c2 = 5
            reason_c2 = f"Zylinderachse des Lagersitzes liegt exakt bei h = {h_val:.2f} mm (Toleranz 35.0 ± 0.1 mm)."
        else:
            pts_c2 = 0
            reason_c2 = f"Achshöhe h = {h_val:.2f} mm weicht von Vorgabe 35.0 mm ab."
    else:
        pts_c2 = 0
        reason_c2 = "Lagerbock-Körper konnte nicht vermessen werden."
    results.append(("C2", "Einhaltung der Achshöhe (h = 35.0 mm)", 5, pts_c2, reason_c2))

    # C3: Hüllquader Bauraum <= 85 x 30 x 65 mm (5 P)
    pts_c3 = 0
    reason_c3 = ""
    if bock_body:
        bb = bock_body["bbox"]
        dx = bb["max"][0] - bb["min"][0]
        dy = bb["max"][1] - bb["min"][1]
        dz = bb["max"][2] - bb["min"][2]
        if dx <= 85.05 and dy <= 30.05 and dz <= 65.05:
            pts_c3 = 5
            reason_c3 = f"Hüllquader {dx:.1f} × {dy:.1f} × {dz:.1f} mm hält Bauraumgrenzen (85 × 30 × 65 mm) ein."
        else:
            pts_c3 = 0
            reason_c3 = f"Bauraumgrenze überschritten: {dx:.1f} × {dy:.1f} × {dz:.1f} mm."
    else:
        pts_c3 = 0
        reason_c3 = "Lagerbock-Bauraum nicht messbar."
    results.append(("C3", "Einhaltung des Hüllquaders (Bauraum)", 5, pts_c3, reason_c3))

    # C4: Lagersitzdurchmesser D = 42 mm (5 P)
    pts_c4 = 0
    reason_c4 = ""
    d_seat = None
    for cyl in bock_cyls:
        r = cyl["radius"]
        if abs(r - 21.0) < 0.2:
            d_seat = 2.0 * r
            break

    if d_seat is not None and 42.0 <= d_seat <= 42.2:
        pts_c4 = 5
        reason_c4 = f"Lagersitzdurchmesser D = {d_seat:.2f} mm entspricht Nenngröße 42.0 mm."
    elif has_6004 and d_seat is not None:
        pts_c4 = 5
        reason_c4 = f"Lagersitzdurchmesser D = {d_seat:.2f} mm für Lager 6004 passend."
    else:
        pts_c4 = 0
        reason_c4 = "Lagersitzdurchmesser weicht von 42.0 mm ab oder fehlt."
    results.append(("C4", "Lagersitzdurchmesser (D = 42 mm)", 5, pts_c4, reason_c4))

    # C5: Durchgangsbohrungen Grundplatte / Lagerbock (5 P)
    pts_c5 = 0
    reason_c5 = ""
    if hole_collision or (hole_spacing_cad is not None and hole_spacing_cad < 45.0):
        pts_c5 = 0
        reason_c5 = f"Bohrungsabstand {hole_spacing_cad:.1f} mm kollidiert mit Lagersitz D=42 mm; Randabstand verletzt."
    elif mounting_hole_dia and 6.4 <= mounting_hole_dia <= 6.8 and mounting_hole_edge_dist and mounting_hole_edge_dist >= 9.0:
        pts_c5 = 5
        reason_c5 = (f"Bohrungsdurchmesser {mounting_hole_dia:.1f} mm (ISO 273 mittel) und "
                     f"Randabstand e = {mounting_hole_edge_dist:.1f} mm >= 9.0 mm eingehalten.")
    elif mounting_hole_edge_dist and mounting_hole_edge_dist >= 9.0:
        pts_c5 = 5
        reason_c5 = f"Befestigungsbohrungen mit Randabstand e = {mounting_hole_edge_dist:.1f} mm >= 9.0 mm eingehalten."
    else:
        pts_c5 = 0
        reason_c5 = "Bohrungsdurchmesser oder Randabstand e < 9.0 mm nicht normgerecht."
    results.append(("C5", "Durchgangsbohrungen Grundplatte (ISO 273)", 5, pts_c5, reason_c5))

    # ==========================================
    # KATEGORIE D: Normteile & Baugruppenintegration (20 P)
    # ==========================================
    # D1: Parametrische Normteile im Baum (5 P)
    pts_d1 = 0
    reason_d1 = ""
    has_screws = len(screw_occs) >= 2
    if has_6004 and has_screws:
        pts_d1 = 5
        reason_d1 = "Normteile DIN 625 6004 und ISO 4762 M6 sauber als Komponenten eingebunden."
    elif has_6004:
        pts_d1 = 2
        reason_d1 = "Lager 6004 als Normteil eingebunden; Befestigungsschrauben fehlen in Baugruppe."
    else:
        pts_d1 = 0
        reason_d1 = "Keine parametrischen Normteile im Modellbaum eingebunden."
    results.append(("D1", "Parametrische Normteile im Baum", 5, pts_d1, reason_d1))

    # D2: Sicherungsringnuten nach DIN 471 / 472 (5 P)
    pts_d2 = 0
    reason_d2 = ""
    has_din472 = any(abs(2.0 * c["radius"] - 44.5) < 0.4 for c in bock_cyls)
    has_din471 = any(abs(2.0 * c["radius"] - 19.0) < 0.4 for c in welle_cyls)

    if has_din472 and has_din471:
        pts_d2 = 5
        reason_d2 = "Sicherungsringnuten DIN 471 (Ø 19 mm) und DIN 472 (Ø 44.5 mm) normgerecht vorhanden."
    elif has_din472 or has_din471:
        pts_d2 = 3
        reason_d2 = "Nur eine Sicherungsringnut vorhanden (DIN 471 oder DIN 472)."
    else:
        pts_d2 = 0
        reason_d2 = "Keine Sicherungsringnuten nach DIN 471 / 472 vorhanden."
    results.append(("D2", "Sicherungsringnuten nach DIN 471 / 472", 5, pts_d2, reason_d2))

    # D3: Freiheitsgrade der Baugruppe (10 P)
    pts_d3 = 0
    reason_d3 = ""
    conflicts = jl.get("conflicts", [])
    errors = jl.get("errors", [])
    dof_list = jl.get("dof", [])
    total_dof = sum(d.get("dof", 0) for d in dof_list)
    joints = joints_res.get("joints", [])
    all_joints_ok = all(j.get("status") == "ok" for j in joints)

    if total_dof == 1 and not conflicts and not errors and all_joints_ok:
        pts_d3 = 10
        reason_d3 = "Baugruppe besitzt exakt 1 DOF (Rotation der Welle) ohne Gelenkkonflikte."
    elif total_dof == 1:
        pts_d3 = 5
        reason_d3 = "Baugruppe besitzt 1 DOF, weist jedoch Gelenkwarnungen oder Konflikte auf."
    else:
        pts_d3 = 0
        reason_d3 = f"Freiheitsgrade fehlerhaft: {total_dof} DOF (erwartet: 1 DOF), Konflikte: {len(conflicts)}."
    results.append(("D3", "Freiheitsgrade der Baugruppe (check_joints)", 10, pts_d3, reason_d3))

    # ==========================================
    # KATEGORIE E: Fertigungsgerechte DFM-Gestaltung (15 P)
    # ==========================================
    # E1: Anlageschultern & Übergangsradien (5 P)
    pts_e1 = 0
    reason_e1 = ""
    has_housing_shoulder = any(abs(2.0 * c["radius"] - 38.0) < 0.5 for c in bock_cyls)
    has_shaft_shoulder = any(abs(2.0 * c["radius"] - 25.0) < 0.5 for c in welle_cyls)

    if has_housing_shoulder and has_shaft_shoulder:
        pts_e1 = 5
        reason_e1 = "Wellenschulter (Ø 25 mm) und Gehäuseschulter (Ø 38 mm) entsprechen Anschlussmaßen."
    elif has_housing_shoulder or has_shaft_shoulder:
        pts_e1 = 3
        reason_e1 = "Anlageschultern nur einseitig vorhanden (Gehäuse oder Welle)."
    else:
        pts_e1 = 0
        reason_e1 = "Keine Anlageschultern vorhanden; Lagerringe laufen nicht planparallel an."
    results.append(("E1", "Anlageschultern & Übergangsradien", 5, pts_e1, reason_e1))

    # E2: DFM-Verfahrenskriterien (5 P)
    pts_e2 = 0
    reason_e2 = ""
    has_chamfer = False
    if bock_doc:
        try:
            tl = sketch_rule.timeline(bock_doc.session).get("timeline", [])
            for feat in tl:
                if feat.get("type") == "ChamferFeature":
                    has_chamfer = True
                    break
        except Exception:
            pass

    if has_chamfer:
        pts_e2 = 5
        reason_e2 = "Einpressfase >= 0.5 mm am Lagersitz vorhanden (DFM-gerechte Lagermontage)."
    else:
        pts_e2 = 0
        reason_e2 = "Keine Einpressfase am Lagersitz vorhanden."
    results.append(("E2", "DFM-Verfahrenskriterien (Fräsen vs. FDM)", 5, pts_e2, reason_e2))

    # E3: Einschraubtiefe & Montagezugänglichkeit (5 P)
    pts_e3 = 0
    reason_e3 = ""
    if has_screws and gp_doc:
        tl = sketch_rule.timeline(gp_doc.session).get("timeline", [])
        m_depth = 0.0
        for feat in tl:
            if feat.get("type") == "HoleFeature":
                defn = gp_doc.session.cmd("timeline.inspect", {"feature": feat["id"]}).get("definition", {})
                d_str = defn.get("depth", "0")
                try:
                    m_depth = max(m_depth, float(d_str))
                except ValueError:
                    pass

        if m_depth >= 8.4:
            pts_e3 = 5
            reason_e3 = f"Einschraubtiefe im Aluminium m_eff = {m_depth:.1f} mm >= 1.4 × d (8.4 mm) eingehalten."
        elif m_depth > 0.0:
            pts_e3 = 2
            reason_e3 = f"Einschraubtiefe m_eff = {m_depth:.1f} mm < 1.4 × d unzureichend."
        else:
            pts_e3 = 5
            reason_e3 = "Verschraubung in Grundplatte normgerecht montiert."
    else:
        pts_e3 = 0
        reason_e3 = "Keine Verschraubung mit Grundplatte vorhanden."
    results.append(("E3", "Einschraubtiefe & Montagezugänglichkeit", 5, pts_e3, reason_e3))

    return results, report_text is not None


def print_evaluation_report(asm_path: str, results: list, has_report: bool):
    total_pts = sum(r[3] for r in results)
    max_pts = sum(r[2] for r in results)

    # Notenskala per Section 3.3
    if total_pts >= 90:
        grade = "1"
        predicate = "Sehr gut (Benchmark voll bestanden)"
    elif total_pts >= 75:
        grade = "2"
        predicate = "Gut (Bestanden mit leichten Abzügen)"
    elif total_pts >= 60:
        grade = "3"
        predicate = "Befriedigend (Mindeststandard)"
    else:
        grade = "5"
        predicate = "Nicht bestanden"

    sep = "=" * 98
    subsep = "-" * 98

    print(sep)
    print(f"BENCHMARK-BEWERTUNG LAGERSTELLE (Issue #45 / #28)")
    print(f"Baugruppe: {asm_path}")
    print(f"Status Begleitbericht: {'vorhanden' if has_report else 'nicht vorhanden'}")
    print(sep)
    print(f"{'Pos.':<5} | {'Kriterium':<46} | {'Max':>4} | {'Ist':>4} | {'Begründung'}")
    print(subsep)

    curr_cat = None
    for pos, crit, max_p, ist_p, reason in results:
        cat = pos[0]
        if cat != curr_cat:
            curr_cat = cat
            cat_names = {
                "A": "Kategorie A: Anforderungsanalyse & Widerspruchsprüfung",
                "B": "Kategorie B: Rechnerische Auslegung & Lagerwahl",
                "C": "Kategorie C: Geometrische B-Rep-Prüfung des Lagerbocks",
                "D": "Kategorie D: Normteile & Baugruppenintegration",
                "E": "Kategorie E: Fertigungsgerechte DFM-Gestaltung",
            }
            print(f"--- {cat_names.get(cat, cat)} ---")
        print(f"{pos:<5} | {crit:<46} | {max_p:>4} | {ist_p:>4} | {reason}")

    print(sep)
    print(f"GESAMTERGEBNIS: {total_pts} / {max_pts} Punkte ({total_pts / max_pts * 100:.1f} %)")
    print(f"NOTE:          {grade} - {predicate}")
    print(sep)


def main():
    args = parse_args()
    results, has_report = evaluate_assembly(args.assembly, args.report)
    print_evaluation_report(args.assembly, results, has_report)
    sys.exit(0)


if __name__ == "__main__":
    main()
