#!/usr/bin/env python3
"""Render the README screenshot of the web UI: a bracket whose countersink notches the wall.

Usage: python3 tools/demo_web_ui.py [out.png]   (default docs/media/web-ui-1.png, needs solidcraft-cli and a
headless Chromium, path in CHROME or Playwright's chrome-headless-shell)."""

import glob
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from mechvane.documents import PART, Workspace  # noqa: E402
from mechvane.ui.server import create_server  # noqa: E402


def chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    found = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")))
    if not found:
        sys.exit("no headless Chromium found, set CHROME")
    return found[-1]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "media" / "web-ui-1.png"
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        try:
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
                                                     "cs_diameter": 13.7, "cs_angle": 90,
                                                     "name": "CountersinkNearWall"}}])
            part.save()
            path = part.path
        finally:
            ws.close_all()

        srv = create_server(path, port=0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{srv.server_address[1]}/"
            subprocess.run([chrome(), "--headless", "--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader",
                            "--hide-scrollbars", "--window-size=1280,800", "--virtual-time-budget=15000",
                            f"--screenshot={out}", url], check=True, capture_output=True, timeout=120)
        finally:
            srv.shutdown()
            srv.server_close()
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
