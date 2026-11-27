#!/usr/bin/env python3
"""Build the static website mechvane.dev: the website (website/) at the root, media/ and roadmap/.

Usage: python3 tools/build_demo_site.py [out_dir]   (default site/)
The output is a plain static site (GitHub Pages); tools/publish_demo_site.sh pushes it. The live demo of the web UI
went offline with #186 and was removed with the web UI (#232)."""

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else REPO / "site"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(REPO / "website", out, ignore=shutil.ignore_patterns("README.md"))
    shutil.copytree(REPO / "docs" / "media", out / "media")
    (out / ".nojekyll").write_text("")
    # Roadmap page: reads roadmap.json live from the public main branch, this copy is the fallback
    (out / "roadmap").mkdir()
    shutil.copyfile(REPO / "tools" / "roadmap_page.html", out / "roadmap" / "index.html")
    shutil.copyfile(REPO / "roadmap.json", out / "roadmap" / "roadmap.json")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
