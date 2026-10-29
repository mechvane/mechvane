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

from mechvane import links  # noqa: E402
from mechvane.documents import ASSEMBLY, Workspace  # noqa: E402
from mechvane.examples import DEMOS  # noqa: E402
from mechvane.ui.mesh import collect_mesh  # noqa: E402
from mechvane.ui import webapp  # noqa: E402
from mechvane.ui.server import STATIC_DIR, collect_findings, collect_tree, collect_version  # noqa: E402


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
    (out / "about.json").write_text(json.dumps({"mechvane": "live demo", "solidcraft": "live demo"}, indent=1), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    # Roadmap page: reads roadmap.json live from the public main branch, this copy is the fallback
    (out / "roadmap").mkdir()
    shutil.copyfile(REPO / "tools" / "roadmap_page.html", out / "roadmap" / "index.html")
    shutil.copyfile(REPO / "roadmap.json", out / "roadmap" / "roadmap.json")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
