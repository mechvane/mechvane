#!/usr/bin/env python3
"""Build the static live demo of the web UI: example models with precomputed mesh, tree and findings.

Usage: python3 tools/build_demo_site.py [out_dir]   (default site/, needs solidcraft-cli)
The output is a plain static site (GitHub Pages): the website (website/) at the root, the live demo under demo/
(the UI files plus demo/demos/<name>/{version,mesh,tree,findings}.json), media/ and roadmap/."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from mechvane import design_rules, install, links  # noqa: E402
from mechvane.documents import ASSEMBLY, Workspace  # noqa: E402
from mechvane.examples import DEMOS  # noqa: E402
from mechvane.ui.mesh import collect_mesh  # noqa: E402
from mechvane.ui import webapp  # noqa: E402
from mechvane.ui.server import STATIC_DIR, collect_findings, collect_tree, collect_version, hole_sizes  # noqa: E402


def make_mechvane_zip(dest: Path):
    """Bundle the modules needed for the browser design rules check into a zip archive."""
    import zipfile
    modules = [
        "__init__.py", "browser_check.py", "design_rules.py", "geometry.py",
        "hole_tables.py", "standard_parts.py", "sketch_rule.py", "documents.py",
        "solidcraft.py", "install.py"
    ]
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in modules:
            zf.write(REPO / "mechvane" / name, f"mechvane/{name}")
        # the browser has no knowledge catalog: ship the sources of the design rules (#120)
        zf.writestr("mechvane/rule_sources.json", json.dumps(design_rules.rule_sources(), ensure_ascii=False))


PART_BYTES = 95 * 1024 * 1024  # GitHub Pages refuses files over 100 MB (#119)


def split_large_wasm(sc: Path) -> None:
    """GitHub Pages holds no file over 100 MB, SolidCraft's wasm is 167 MB from 0.41 on (#119). Split it into
    pieces that tools/demo_site/wasm-parts.js joins in the page (checked against the release file's SHA-256),
    and switch the web app's offline worker off for the demo: it keeps files by their SHA-256 and would keep
    visitors on an older build it cannot update. The SolidCraft files are otherwise unchanged."""
    import hashlib, re
    big = [w for w in sc.glob("*_bg.wasm") if w.stat().st_size > PART_BYTES]
    if not big:
        return
    for w in big:
        data = w.read_bytes()
        parts = []
        for i in range(0, len(data), PART_BYTES):
            name = f"{w.name}.part{i // PART_BYTES}"
            (sc / name).write_bytes(data[i:i + PART_BYTES])
            parts.append(name)
        (sc / f"{w.name}.parts.json").write_text(json.dumps(
            {"parts": parts, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}), encoding="utf-8")
        w.unlink()
    shutil.copy(REPO / "tools" / "demo_site" / "wasm-parts.js", sc / "wasm-parts.js")
    index = sc / "index.html"
    html = index.read_text(encoding="utf-8")
    html = re.sub(r'<link rel="preload" href="\./[^"]*_bg\.wasm"[^>]*>', "", html)  # the whole file is gone
    html = html.replace('navigator.serviceWorker.register("sw.js")', "Promise.resolve()")
    if '<script src="wasm-parts.js">' not in html:
        html = html.replace('<script type="module">', '<script src="wasm-parts.js"></script>\n<script type="module">', 1)
    if "wasm-parts.js" not in html or "_bg.wasm\" crossorigin" in html:
        raise RuntimeError("sc/index.html: could not wire the wasm pieces in")
    index.write_text(html, encoding="utf-8")
    sw = sc / "sw.js"
    if sw.exists():  # "dev" makes the worker retire: it drops what it kept and unregisters (see sw.js)
        text = sw.read_text(encoding="utf-8")
        new = re.sub(r'^/\* @build \*/ const VERSION = "[^"]*"', '/* @build */ const VERSION = "dev"', text, count=1, flags=re.M)
        if new == text:
            raise RuntimeError("sc/sw.js: build line not found, the old offline worker would stay")
        sw.write_text(new, encoding="utf-8")


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "site"
    if out.exists():
        shutil.rmtree(out)
    # Website at the root (website/), the live demo under /demo/, images under /media/, roadmap under /roadmap/
    shutil.copytree(REPO / "website", out, ignore=shutil.ignore_patterns("README.md"))
    shutil.copytree(REPO / "docs" / "media", out / "media")
    demo = out / "demo"
    shutil.copytree(STATIC_DIR, demo)
    make_mechvane_zip(demo / "mechvane.zip")
    # Mechvane's hole tables for the Hole dialog (the server answers /api/hole_sizes, the demo reads this file)
    (demo / "hole_sizes.json").write_text(json.dumps(hole_sizes()), encoding="utf-8")
    for page in ("index.html", "model.html"):
        html = (demo / page).read_text(encoding="utf-8")
        (demo / page).write_text(html.replace('<html lang="en">', '<html lang="en" data-static="1">', 1),
                                encoding="utf-8")
    # The SolidCraft web app for "Model by hand" (release asset, SHA256 checked in webapp.py)
    shutil.copytree(webapp.webapp_dir(), demo / "sc")
    split_large_wasm(demo / "sc")
    index = []
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        try:
            for name, title, build in DEMOS:
                doc = build(ws)
                d = demo / "demos" / name
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
                data["files"] = {"document": doc.path.name, "kind": doc.kind, "files": sorted(files)}
                for body in data["mesh"].get("bodies", []):
                    body["positions"] = [round(v, 4) for v in body["positions"]]  # 0.1 µm, halves the download
                for key, value in data.items():
                    (d / f"{key}.json").write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
                index.append({"name": name, "title": title})
                print(f"{name}: {sum((d / f'{k}.json').stat().st_size for k in data) // 1024} KB, "
                      f"{data['findings'].get('verdict')}")
        finally:
            ws.close_all()
    (demo / "demos" / "index.json").write_text(json.dumps({"demos": index}, indent=1), encoding="utf-8")
    (demo / "about.json").write_text(json.dumps({"mechvane": "live demo", "solidcraft": install.VERSION}, indent=1), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    # Old live-demo addresses (before the website moved in) forward to /demo/, keeping ?demo=…
    (out / "model.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Mechvane live demo</title>'
        '<script>location.replace("demo/model.html" + location.search)</script>'
        '<a href="demo/model.html">Mechvane live demo</a>', encoding="utf-8")
    # Roadmap page: reads roadmap.json live from the public main branch, this copy is the fallback
    (out / "roadmap").mkdir()
    shutil.copyfile(REPO / "tools" / "roadmap_page.html", out / "roadmap" / "index.html")
    shutil.copyfile(REPO / "roadmap.json", out / "roadmap" / "roadmap.json")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
