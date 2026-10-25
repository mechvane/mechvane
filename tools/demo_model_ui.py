#!/usr/bin/env python3
"""Render the README screenshot of the "Model by hand" mode: the bracket whose countersink notches the
wall, the countersink moved away from the wall in the SolidCraft web app and saved, Mechvane checked again.

Usage: python3 tools/demo_model_ui.py [out.png]   (default docs/media/model-mode.png; needs solidcraft-cli,
node and Playwright's Chromium, see tools/drive_model_ui.mjs)"""

import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from build_demo_site import bracket  # noqa: E402
from mechvane.documents import Workspace  # noqa: E402
from mechvane.ui import create_server  # noqa: E402
from mechvane.ui.webapp import webapp_dir  # noqa: E402

EDIT = [{"command": "timeline.edit", "params": {"feature": "CountersinkNearWall", "set": {"position": [42, 14, 8]}}}]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "media" / "model-mode.png"
    webapp_dir()
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(Path(tmp))
        doc = bracket(ws)
        ws.close_all()
        srv = create_server(doc.path, port=0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            cmds = Path(tmp) / "edit.json"
            cmds.write_text(json.dumps(EDIT), encoding="utf-8")
            env = dict(os.environ, CHROME_FLAGS=os.environ.get("CHROME_FLAGS", "--disable-features=WebGPU"))
            r = subprocess.run(["node", str(REPO / "tools" / "drive_model_ui.mjs"),
                                f"http://127.0.0.1:{srv.server_address[1]}/model", str(out), str(cmds)],
                               env=env, capture_output=True, text=True, timeout=600)
            report = json.loads(r.stdout)
        finally:
            srv.shutdown()
            srv.server_close()
    save = report.get("save") or {}
    print(f"wrote {out} ({out.stat().st_size // 1024} KB), after the edit: {save.get('summary')}")
    if report.get("error"):
        sys.exit(f"error: {report['error']}")


if __name__ == "__main__":
    main()
