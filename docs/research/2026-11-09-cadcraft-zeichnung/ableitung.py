#!/usr/bin/env python3
"""Zeichnungsableitung aus SolidCraft-Referenzteilen mit CADCraft 0.8.0.

Dieses Skript demonstriert die automatisierte Ableitung einer normgerechten
2D-Fertigungszeichnung aus einem SolidCraft 3D-Referenzteil (Default: flansch):
1. Erzeugung der 3D-Geometrie und Export von drei 2D-Projektionen (Draufsicht,
   Vorderansicht, Seitenansicht) mit verdeckten Kanten ('hidden': 'dashed')
   ueber SolidCrafts `file.export_view_dxf`.
2. Initialisierung einer metrischen 2D-Zeichnung in CADCraft 0.8.0 ueber das
   Model Context Protocol (MCP) ueber Stdio (`cadcraft-cli mcp`).
3. Anordnung der drei Ansichten nach Projektionsmethode 1 (ISO 128 / DIN 6)
   mit Ausrichtung zueinander.
4. Bemaßung wesentlicher Geometrieelemente (Breite 60 mm, Dicke 8 mm,
   Bohrungsabstand 31.82 mm) mit Bemaßungsstil ISO-25.
5. Einfuegen von Form- und Lagetoleranzen (Ebenheit 0.05 mm) und eines
   DIN EN ISO 7200 Schriftfelds als formatierte Tabelle.
6. Export der fertigen Fertigungszeichnung nach DXF, PDF und PNG.

Aufruf:
  python3 docs/research/2026-11-09-cadcraft-zeichnung/ableitung.py
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[3]
CADCRAFT_CLI = Path(os.environ.get(
    "CADCRAFT_CLI",
    Path.home() / ".local/opt/cadcraft-0.8.0-linux-x86_64/bin/cadcraft-cli"
))
SOLIDCRAFT_CLI = Path(os.environ.get("SOLIDCRAFT_CLI", "solidcraft-cli"))


class CadcraftMcpClient:
    """Minimal MCP client communicating with cadcraft-cli mcp over stdio."""

    def __init__(self, cli_path: Path):
        self.cli_path = cli_path
        self.proc = None
        self.req_id = 1

    def __enter__(self):
        if not self.cli_path.is_file():
            raise FileNotFoundError(f"CADCraft CLI not found at {self.cli_path}")
        self.proc = subprocess.Popen(
            [str(self.cli_path), "mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        # MCP initialize
        init_reply = self.call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mechvane-research-drawing", "version": "1.0"}
        })
        if init_reply.get("error"):
            raise RuntimeError(f"MCP init failed: {init_reply}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

    def call(self, method: str, params: dict) -> dict:
        req = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params
        }
        self.req_id += 1
        line = json.dumps(req) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()
        raw = self.proc.stdout.readline()
        if not raw:
            stderr = self.proc.stderr.read()
            raise RuntimeError(f"CADCraft MCP exited prematurely: {stderr}")
        res = json.loads(raw)
        return res

    def tool(self, name: str, arguments: dict = None) -> dict:
        args = arguments or {}
        res = self.call("tools/call", {"name": name, "arguments": args})
        if res.get("error"):
            raise RuntimeError(f"Tool {name} error: {res['error']}")
        content = res.get("result", {}).get("content", [])
        if res.get("result", {}).get("isError"):
            err_msg = content[0].get("text") if content else str(res)
            raise RuntimeError(f"Tool {name} failed: {err_msg}")
        # Parse nested json in text content if available
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except Exception:
                return {"text": content[0]["text"]}
        return res.get("result", {})

    def execute_cmd(self, command: str, params: dict = None) -> dict:
        return self.tool("execute", {"command": command, "params": params or {}})


def build_views(part_name: str, out_dir: Path) -> dict[str, Path]:
    """Generates 3 view DXFs from a SolidCraft reference part."""
    build_file = REPO_ROOT / f"tests/reference/{part_name}.build.json"
    if not build_file.is_file():
        raise FileNotFoundError(f"Reference build file not found: {build_file}")

    build_spec = json.loads(build_file.read_text(encoding="utf-8"))
    commands = build_spec["commands"]

    top_dxf = out_dir / f"{part_name}_top.dxf"
    front_dxf = out_dir / f"{part_name}_front.dxf"
    side_dxf = out_dir / f"{part_name}_side.dxf"

    # In SolidCraft, target is the center of the part (flange 60x60x8 centered at z=4)
    # yaw, pitch, roll, distance, fov (small FOV + large distance = telecentric / orthographic)
    cam_top = {"target": [0.0, 0.0, 4.0], "yaw": 0.0, "pitch": 1.5707963, "distance": 100000.0, "fov": 0.0005}
    cam_front = {"target": [0.0, 0.0, 4.0], "yaw": 0.0, "pitch": 0.0, "distance": 100000.0, "fov": 0.0005}
    cam_side = {"target": [0.0, 0.0, 4.0], "yaw": -1.5707963, "pitch": 0.0, "distance": 100000.0, "fov": 0.0005}

    export_cmds = [
        {"command": "file.export_view_dxf", "params": {"camera": cam_top, "hidden": "dashed", "path": str(top_dxf)}},
        {"command": "file.export_view_dxf", "params": {"camera": cam_front, "hidden": "dashed", "path": str(front_dxf)}},
        {"command": "file.export_view_dxf", "params": {"camera": cam_side, "hidden": "dashed", "path": str(side_dxf)}}
    ]

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump({"commands": commands + export_cmds}, tf)
        tmp_script = tf.name

    try:
        proc = subprocess.run(
            [str(SOLIDCRAFT_CLI), "run", tmp_script],
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"SolidCraft view export failed:\n{proc.stderr}\n{proc.stdout}")
    finally:
        if os.path.exists(tmp_script):
            os.remove(tmp_script)

    for p in (top_dxf, front_dxf, side_dxf):
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"Expected view DXF was not written: {p}")

    return {"top": top_dxf, "front": front_dxf, "side": side_dxf}


def compose_drawing(views: dict[str, Path], out_dxf: Path, out_pdf: Path, out_png: Path):
    """Composes a 3-view dimensioned drawing with CADCraft MCP."""
    with CadcraftMcpClient(CADCRAFT_CLI) as client:
        # 1. New metric drawing
        client.tool("new_drawing", {"metric": True})

        # 2. Set current dimension style to ISO-25
        client.execute_cmd("dimstyle.current", {"name": "ISO-25"})

        # 3. Import 3 views into drawing (First Angle Projection ISO 128 / DIN 6)
        # Front view placed at [100, 160] (spans x: 70..130, y: 156..164)
        client.execute_cmd("import", {"path": str(views["front"]), "at": [100.0, 160.0]})
        # Top view placed at [100, 70] (spans x: 70..130, y: 40..100)
        client.execute_cmd("import", {"path": str(views["top"]), "at": [100.0, 70.0]})
        # Side view placed at [190, 160] (spans x: 160..220, y: 156..164)
        client.execute_cmd("import", {"path": str(views["side"]), "at": [190.0, 160.0]})

        # 4. Dimensions
        # Front view: Width = 60 mm (horizontal at top)
        client.execute_cmd("dimlinear", {
            "p1": [70.0, 164.0],
            "p2": [130.0, 164.0],
            "at": [100.0, 178.0]
        })
        # Front view: Thickness = 8 mm (vertical at right edge)
        client.execute_cmd("dimlinear", {
            "p1": [130.0, 156.0],
            "p2": [130.0, 164.0],
            "at": [142.0, 160.0]
        })
        # Top view: Outer width = 60 mm (horizontal at bottom)
        client.execute_cmd("dimlinear", {
            "p1": [70.0, 40.0],
            "p2": [130.0, 40.0],
            "at": [100.0, 26.0]
        })
        # Top view: Outer height = 60 mm (vertical at left edge)
        client.execute_cmd("dimlinear", {
            "p1": [70.0, 40.0],
            "p2": [70.0, 100.0],
            "at": [56.0, 70.0]
        })
        # Top view: Hole distance between top two holes = 31.82 mm
        client.execute_cmd("dimlinear", {
            "p1": [84.09, 85.91],
            "p2": [115.91, 85.91],
            "at": [100.0, 95.0]
        })

        # 5. Form- und Lagetoleranz (ISO 1101 / ASME Y14.5 Feature Control Frame)
        # Ebenheit 0.05 mm
        client.execute_cmd("tolerance", {
            "at": [160.0, 100.0],
            "symbol": "flatness",
            "tol1": "0.05"
        })

        # 6. Title block (DIN EN ISO 7200 Schriftfeld als Tabelle)
        tbl = client.execute_cmd("table", {
            "at": [150.0, 15.0],
            "rows": 4,
            "cols": 2,
            "rowHeight": 6.0,
            "colWidth": 35.0
        })
        handle = tbl.get("handle", "100")

        fields = [
            (0, 0, "Benennung"), (0, 1, "Flansch 60x60"),
            (1, 0, "Werkstoff"), (1, 1, "EN AW-6082 T6"),
            (2, 0, "Toleranz"),  (2, 1, "ISO 2768-m"),
            (3, 0, "Maßstab"),   (3, 1, "1:1")
        ]
        for r, c, txt in fields:
            client.execute_cmd("table.set", {
                "handle": handle,
                "row": r,
                "col": c,
                "text": txt
            })

        # 7. Save outputs
        client.tool("save", {"path": str(out_dxf)})
        client.tool("save", {"path": str(out_pdf)})
        client.tool("save", {"path": str(out_png)})


def main():
    parser = argparse.ArgumentParser(description="CADCraft 0.8.0 Zeichnungsableitung")
    parser.add_argument("--part", default="flansch", help="Name des Referenzteils (default: flansch)")
    parser.add_argument("--outdir", default=None, help="Ausgabeverzeichnis (default: Verzeichnis des Skripts)")
    args = parser.parse_args()

    out_dir = Path(args.outdir) if args.outdir else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Starte Zeichnungsableitung fuer '{args.part}' ===")
    print(f"SolidCraft CLI: {SOLIDCRAFT_CLI}")
    print(f"CADCraft CLI:   {CADCRAFT_CLI}")
    print(f"Ausgabeordner:  {out_dir}")

    # 1. 3D-Views exportieren
    print("\n1. Erzeuge 3D-Ansichten aus SolidCraft (Top, Front, Side)...")
    views = build_views(args.part, out_dir)
    for name, p in views.items():
        print(f"   - {name:5}: {p.name} ({p.stat().st_size:,} Bytes)")

    # 2. Zeichnung in CADCraft komponieren
    print("\n2. Komponiere 3-Ansichten-Zeichnung mit Maßen in CADCraft 0.8.0 via MCP...")
    out_dxf = out_dir / f"{args.part}_zeichnung.dxf"
    out_pdf = out_dir / f"{args.part}_zeichnung.pdf"
    out_png = out_dir / f"{args.part}_zeichnung.png"

    compose_drawing(views, out_dxf, out_pdf, out_png)

    # 3. Pruefe Ergebnisse
    print("\n3. Pruefe erzeugte Ausgabedateien:")
    all_ok = True
    for p in (out_dxf, out_pdf, out_png):
        exists = p.is_file() and p.stat().st_size > 0
        all_ok &= exists
        status = "OK" if exists else "FEHLT"
        size = f"{p.stat().st_size:,} Bytes" if exists else "-"
        print(f"   [{status}] {p.name:22} ({size})")

    if not all_ok:
        print("\nFEHLER: Nicht alle Ausgabedateien wurden erfolgreich geschrieben!")
        sys.exit(1)

    print("\nErfolg: Alle 3 Ansichten, Bemaßungen, Toleranzrahmen und Schriftfeld wurden exportiert.")


if __name__ == "__main__":
    main()
