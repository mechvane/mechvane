#!/usr/bin/env python3
"""Build the static live demo of the web UI: example models with precomputed mesh, tree and findings.

Usage: python3 tools/build_demo_site.py [out_dir]   (default site/, needs solidcraft-cli)
The output is a plain static site (GitHub Pages): the UI files plus demos/<name>/{version,mesh,tree,findings}.json."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from mechvane import bolted, links  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402
from mechvane.ui.mesh import collect_mesh  # noqa: E402
from mechvane.ui import webapp  # noqa: E402
from mechvane.ui.server import STATIC_DIR, collect_findings, collect_tree, collect_version  # noqa: E402


def bracket(ws):
    """A bracket whose countersink notches the wall (practice test 5, finding 8)."""
    part = ws.new(PART, "bracket")
    part.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 8, "corner": [0, 0, 0],
                                            "name": "BasePlate", "body_name": "Bracket"}},
        {"command": "solid.box", "params": {"length": 60, "width": 10, "height": 40, "corner": [0, 30, 8],
                                            "operation": "join", "name": "Wall"}},
        {"command": "solid.hole", "params": {"position": [18, 14, 8], "direction": [0, 0, -1],
                                             "clearance": "M6", "depth": 8, "name": "Hole"}},
        {"command": "solid.hole", "params": {"position": [42, 23, 8], "direction": [0, 0, -1],
                                             "clearance": "M6", "depth": 8, "type": "countersink",
                                             "cs_diameter": 13.7, "cs_angle": 90, "name": "CountersinkNearWall"}}])
    part.save()
    return part


def flange(ws):
    """The parametric flange from the reference corpus: sketches owned by their features."""
    part = ws.new(PART, "flange")
    cmds = json.loads((REPO / "tests" / "reference" / "flansch.build.json").read_text(encoding="utf-8"))["commands"]
    part.session.batch(cmds)
    part.save()
    return part


def bolted_plates(ws):
    """Two plates joined by four M6 cap screws with washers and nuts, holes drilled in both part files."""
    top = ws.new(PART, "top_plate")
    top.session.cmd("solid.box", {"length": 80, "width": 50, "height": 10, "corner": [-40, -25, 0],
                                  "body_name": "TopPlate", "name": "Plate"})
    top.save()
    base = ws.new(PART, "base_plate")
    base.session.cmd("solid.box", {"length": 80, "width": 50, "height": 8, "corner": [-40, -25, 0],
                                   "body_name": "BasePlate", "name": "Plate"})
    base.save()
    asm = ws.new(ASSEMBLY, "bolted_plates")
    links.insert(ws, asm, top.path, name="TopPlate", grounded=True)
    links.insert(ws, asm, base.path, name="BasePlate", translate=[0, 0, -8], grounded=True)
    asm.save()
    bolted.bolted_connection(ws, "bolted_plates", placement={"position": [-28, -15, 10], "direction": [0, 0, -1]},
                             size="M6", pattern={"type": "rectangular", "count": [2, 2], "spacing": [56, 30]})
    asm.save()
    return asm


DEMOS = [("bolted_plates", "Bolted connection (assembly)", bolted_plates),
         ("bracket", "Bracket with a design check finding", bracket),
         ("flange", "Parametric flange", flange)]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "site"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC_DIR, out)
    for page in ("index.html", "model.html"):
        html = (out / page).read_text(encoding="utf-8")
        (out / page).write_text(html.replace('<html lang="en">', '<html lang="en" data-static="1">', 1),
                                encoding="utf-8")
    # The SolidCraft web app for "Model by hand" (release asset, SHA256 checked in webapp.py)
    shutil.copytree(webapp.webapp_dir(), out / "sc")
    index = []
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        try:
            for name, title, build in DEMOS:
                doc = build(ws)
                d = out / "demos" / name
                d.mkdir(parents=True)
                data = {"version": collect_version(doc), "mesh": collect_mesh(doc, tmp_dir=tmp),
                        "tree": collect_tree(ws, doc), "findings": collect_findings(ws, doc)}
                data["version"]["path"] = ""
                # The design files themselves, for the web app: the document and its linked parts
                files = {doc.path.name: doc.path}
                if doc.kind == ASSEMBLY:
                    for link in links._links(doc.session).values():
                        if link.get("file") and Path(link["file"]).is_file():
                            files.setdefault(Path(link["file"]).name, Path(link["file"]))
                (d / "files").mkdir()
                for fname, src in files.items():
                    shutil.copyfile(src, d / "files" / fname)
                data["files"] = {"document": doc.path.name, "files": sorted(files)}
                for body in data["mesh"].get("bodies", []):
                    body["positions"] = [round(v, 4) for v in body["positions"]]  # 0.1 µm, halves the download
                for key, value in data.items():
                    (d / f"{key}.json").write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
                index.append({"name": name, "title": title})
                print(f"{name}: {sum((d / f'{k}.json').stat().st_size for k in data) // 1024} KB, "
                      f"{data['findings'].get('verdict')}")
        finally:
            ws.close_all()
    (out / "demos" / "index.json").write_text(json.dumps({"demos": index}, indent=1), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
