#!/usr/bin/env python3
"""Build reference and faulty CAD models for the Lagerstelle benchmark (Issue #45)."""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mechvane.documents import Workspace, PART, ASSEMBLY  # noqa: E402
from mechvane import server, standard_parts, bolted, links  # noqa: E402


def build_models():
    target_dir = ROOT / "tests" / "benchmarks" / "lagerstelle"
    target_dir.mkdir(parents=True, exist_ok=True)

    ws = Workspace(str(target_dir))
    server.ws = ws

    print(f"Building benchmark models in {target_dir}...")

    # ==========================================
    # 1. REFERENZLÖSUNG
    # ==========================================

    # 1.1 Grundplatte (15 mm AlMgSi1 / EN AW-6060)
    print("Building referenz_grundplatte...")
    gp = ws.new(PART, "referenz_grundplatte", overwrite=True)
    server.run("referenz_grundplatte", [
        {"command": "solid.box", "params": {
            "length": 120, "width": 60, "height": 15,
            "corner": [-60, -15, -15],
            "operation": "new", "body_name": "Grundplatte", "name": "Platte"
        }}
    ])
    gp.save()

    # 1.2 Lagerbock (korrigierter Mittenabstand p = 60 mm, d.h. x = +-30 mm)
    print("Building referenz_lagerbock...")
    bock = ws.new(PART, "referenz_lagerbock", overwrite=True)
    server.run("referenz_lagerbock", [
        # Fuss 80 x 30 x 10 mm
        {"command": "solid.box", "params": {
            "length": 80, "width": 30, "height": 10,
            "corner": [-40, 0, 0],
            "operation": "new", "body_name": "Lagerbock", "name": "Fuss"
        }},
        # Steg 32 x 30 x 25 mm
        {"command": "solid.box", "params": {
            "length": 32, "width": 30, "height": 25,
            "corner": [-16, 0, 10],
            "operation": "join", "name": "Steg"
        }},
        # Gehaeuseaussenwand Zylinder D=54 mm, B=30 mm bei Achshoehe z=35 mm
        {"command": "solid.cylinder", "params": {
            "diameter": 54, "height": 30,
            "base": [0, 0, 35], "axis": "Y",
            "operation": "join", "name": "GehaeuseAussen"
        }},
        # Lagersitz D=42.0 mm, B=12.0 mm
        {"command": "solid.cylinder", "params": {
            "diameter": 42.0, "height": 12.0,
            "base": [0, 0, 35], "axis": "Y",
            "operation": "cut", "name": "Lagersitz"
        }},
        # Gehaeuseschulter D=38.0 mm (Anschlag fuer Lager-Aussenring)
        {"command": "solid.cylinder", "params": {
            "diameter": 38.0, "height": 18.0,
            "base": [0, 12.0, 35], "axis": "Y",
            "operation": "cut", "name": "Schulter"
        }},
        # Sicherungsringnut DIN 472 (D=44.5 mm, Nutbreite m=1.85 mm, Steg n=4.0 mm >= 3.8 mm)
        {"command": "solid.cylinder", "params": {
            "diameter": 44.5, "height": 1.85,
            "base": [0, 4.0, 35], "axis": "Y",
            "operation": "cut", "name": "NutDIN472"
        }},
        # Einpressfase am Lagersitz (0.8 mm x 45 deg)
        {"command": "solid.chamfer", "params": {
            "edges": [[0, 0, 56]], "distance": 0.8,
            "name": "Einpressfase"
        }},
    ])
    bock.save()

    # 1.3 Welle mit Wellenschulter D=25 mm, Lagersitz d=20 mm und DIN 471 Nut d=19 mm
    print("Building referenz_welle...")
    welle = ws.new(PART, "referenz_welle", overwrite=True)
    server.run("referenz_welle", [
        {"command": "sketch.create", "params": {"plane": "YZ", "name": "WellenProfil"}},
        {"command": "sketch.line", "params": {"closed": True, "points": [
            [-20.0, 0.0],
            [-20.0, 12.5],     # Bund D=25 (r=12.5)
            [0.0, 12.5],
            [0.0, 10.0],       # Lagersitz d=20 (r=10.0)
            [12.0, 10.0],      # Nutbeginn DIN 471
            [12.0, 9.5],       # Nutgrund d=19 (r=9.5)
            [13.3, 9.5],       # Nutbreite m=1.3 (y=12.0..13.3)
            [13.3, 10.0],      # Steg n=2.7 >= 1.5
            [15.5, 10.0],
            [16.0, 9.5],       # Endfase 0.5x45 deg
            [16.0, 0.0],
        ]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.revolve", "params": {
            "sketch": "WellenProfil", "axis": "Y",
            "operation": "new", "body_name": "Welle", "name": "Drehteil"
        }},
    ])
    welle.save()

    # 1.4 Normteile
    print("Building lager_6004...")
    standard_parts.create(ws, "DIN 625", "6004", name="lager_6004", overwrite=True)
    ws.docs["lager_6004"].save()

    print("Building scheibe_m6...")
    standard_parts.create(ws, "ISO 7089", "6", name="scheibe_m6", overwrite=True)
    ws.docs["scheibe_m6"].save()

    # 1.5 Referenzbaugruppe
    print("Building referenz (Assembly)...")
    asm = ws.new(ASSEMBLY, "referenz", overwrite=True)
    links.insert(ws, asm, "referenz_grundplatte.solidcraft", name="Grundplatte", grounded=True)
    links.insert(ws, asm, "referenz_lagerbock.solidcraft", name="Lagerbock", grounded=False)
    links.insert(ws, asm, "lager_6004.solidcraft", name="Lager6004",
                 rotate={"axis": [1, 0, 0], "angle": 90}, translate=[0, 12, 35])
    links.insert(ws, asm, "referenz_welle.solidcraft", name="Welle", translate=[0, 0, 35])
    asm.save()

    # Verschraubungen links (x = -30) und rechts (x = +30) ueber bolted_connection
    for x, name in [(-30, "SchraubeLinks"), (30, "SchraubeRechts")]:
        print(f"Creating bolted connection {name} at x={x}...")
        res = bolted.bolted_connection(
            ws, "referenz",
            placement={"position": [x, 15, 10], "direction": [0, 0, -1]},
            size="M6",
            connection_type="blind",
            blind_material="alu_wrought",
            counterbore=True,
            name=name,
        )
        print(f"Bolted connection {name} created: id={res['id']}")

    # Gelenke
    server.add_joint("referenz", {
        "name": "BockAufPlatte",
        "type": "rigid",
        "flip": True,
        "a": {"occurrence": "Grundplatte:1", "point": [0, 15, 0], "z": [0, 0, 1]},
        "b": {"occurrence": "Lagerbock:1", "point": [0, 15, 0], "z": [0, 0, 1]},
    })
    server.add_joint("referenz", {
        "name": "LagerImBock",
        "type": "rigid",
        "a": {"occurrence": "Lagerbock:1", "point": [0, 12, 35], "z": [0, -1, 0]},
        "b": {"occurrence": "Lager6004:1", "point": [0, 12, 35], "z": [0, -1, 0]},
    })
    server.add_joint("referenz", {
        "name": "WelleImLager",
        "type": "revolute",
        "a": {"occurrence": "Lager6004:1", "point": [0, 0, 35], "z": [0, 1, 0]},
        "b": {"occurrence": "Welle:1", "point": [0, 0, 35], "z": [0, 1, 0]},
    })
    asm.save()
    print("Referenzlösung erfolgreich gebaut!")

    # ==========================================
    # 2. FEHLERHAFTE VARIANTE (Widerspruch 36 mm blind übernommen)
    # ==========================================

    # 2.1 Fehlerhafte Grundplatte
    print("Building fehlerhaft_grundplatte...")
    gp_f = ws.new(PART, "fehlerhaft_grundplatte", overwrite=True)
    server.run("fehlerhaft_grundplatte", [
        {"command": "solid.box", "params": {
            "length": 120, "width": 60, "height": 15,
            "corner": [-60, -15, -15],
            "operation": "new", "body_name": "Grundplatte", "name": "Platte"
        }}
    ])
    gp_f.save()

    # 2.2 Fehlerhafter Lagerbock (Bohrungsabstand 36 mm, d.h. x = +-18 mm -> Kollision mit Lagersitz D=42)
    print("Building fehlerhaft_lagerbock...")
    bock_f = ws.new(PART, "fehlerhaft_lagerbock", overwrite=True)
    server.run("fehlerhaft_lagerbock", [
        {"command": "solid.box", "params": {
            "length": 80, "width": 30, "height": 10,
            "corner": [-40, 0, 0],
            "operation": "new", "body_name": "Lagerbock", "name": "Fuss"
        }},
        {"command": "solid.box", "params": {
            "length": 32, "width": 30, "height": 25,
            "corner": [-16, 0, 10],
            "operation": "join", "name": "Steg"
        }},
        {"command": "solid.cylinder", "params": {
            "diameter": 54, "height": 30,
            "base": [0, 0, 35], "axis": "Y",
            "operation": "join", "name": "GehaeuseAussen"
        }},
        {"command": "solid.cylinder", "params": {
            "diameter": 42.0, "height": 12.0,
            "base": [0, 0, 35], "axis": "Y",
            "operation": "cut", "name": "Lagersitz"
        }},
        {"command": "solid.cylinder", "params": {
            "diameter": 38.0, "height": 18.0,
            "base": [0, 12.0, 35], "axis": "Y",
            "operation": "cut", "name": "Schulter"
        }},
        # Fehlerhafte Bohrungen bei x = +-18 mm: durchdringen den Lagersitz (R=21 mm)!
        {"command": "solid.cylinder", "params": {
            "diameter": 6.6, "height": 15.0,
            "base": [-18.0, 15.0, -1.0], "axis": "Z",
            "operation": "cut", "name": "FehlerBohrungLinks"
        }},
        {"command": "solid.cylinder", "params": {
            "diameter": 6.6, "height": 15.0,
            "base": [18.0, 15.0, -1.0], "axis": "Z",
            "operation": "cut", "name": "FehlerBohrungRechts"
        }},
    ])
    bock_f.save()

    # 2.3 Fehlerhafte Baugruppe
    print("Building fehlerhaft (Assembly)...")
    asm_f = ws.new(ASSEMBLY, "fehlerhaft", overwrite=True)
    links.insert(ws, asm_f, "fehlerhaft_grundplatte.solidcraft", name="Grundplatte", grounded=True)
    links.insert(ws, asm_f, "fehlerhaft_lagerbock.solidcraft", name="Lagerbock", grounded=False)
    links.insert(ws, asm_f, "lager_6004.solidcraft", name="Lager6004",
                 rotate={"axis": [1, 0, 0], "angle": 90}, translate=[0, 12, 35])
    links.insert(ws, asm_f, "referenz_welle.solidcraft", name="Welle", translate=[0, 0, 35])
    asm_f.save()

    # Gelenke fuer fehlerhafte Baugruppe
    server.add_joint("fehlerhaft", {
        "name": "BockAufPlatte",
        "type": "rigid",
        "flip": True,
        "a": {"occurrence": "Grundplatte:1", "point": [0, 15, 0], "z": [0, 0, 1]},
        "b": {"occurrence": "Lagerbock:1", "point": [0, 15, 0], "z": [0, 0, 1]},
    })
    server.add_joint("fehlerhaft", {
        "name": "LagerImBock",
        "type": "rigid",
        "a": {"occurrence": "Lagerbock:1", "point": [0, 12, 35], "z": [0, -1, 0]},
        "b": {"occurrence": "Lager6004:1", "point": [0, 12, 35], "z": [0, -1, 0]},
    })
    server.add_joint("fehlerhaft", {
        "name": "WelleImLager",
        "type": "revolute",
        "a": {"occurrence": "Lager6004:1", "point": [0, 0, 35], "z": [0, 1, 0]},
        "b": {"occurrence": "Welle:1", "point": [0, 0, 35], "z": [0, 1, 0]},
    })
    asm_f.save()
    print("Fehlervariante erfolgreich gebaut!")

    ws.close_all()
    print("Alle Benchmark-Modelle erfolgreich erzeugt!")


if __name__ == "__main__":
    build_models()
