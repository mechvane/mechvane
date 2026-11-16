#!/usr/bin/env python3
"""Cross-platform smoke test for Mechvane CI (Windows, macOS, Linux).

Verifies:
1. `mechvane setup` (download and unpack pinned SolidCraft CLI and web app).
2. Python interface: create a part (plate with hole), check_design, save, reopen,
   and verify volume against expected value.
3. UI server: launch `mechvane ui --demo --no-browser --port <free>`, query
   /api/project and /api/mesh, and terminate cleanly via /api/quit.

Standard library only, plus mechvane.
"""

import json
import math
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Ensure repository root is on sys.path even when invoked without pip install -e
REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def get_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_setup() -> None:
    """Run `mechvane setup` via CLI entry point."""
    print("== [1/3] Running `mechvane setup` ==", flush=True)
    cmd = [sys.executable, "-m", "mechvane", "setup"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        print(f"FAIL: `mechvane setup` failed with code {res.returncode}", file=sys.stderr)
        print("stdout:\n", res.stdout, file=sys.stderr)
        print("stderr:\n", res.stderr, file=sys.stderr)
        sys.exit(res.returncode or 1)
    for line in res.stdout.strip().splitlines():
        print(f"  {line}")
    print("  OK: setup completed successfully.\n", flush=True)


def test_part_modeling() -> None:
    """Create a plate with a hole, check_design, save, reopen, and verify volume."""
    print("== [2/3] Testing part creation, check_design, save, reopen, volume ==", flush=True)
    from mechvane.documents import Workspace, PART
    from mechvane import server

    with tempfile.TemporaryDirectory(prefix="mechvane-ci-smoke-") as tmp_dir:
        ws = Workspace(tmp_dir)
        server.ws = ws

        # 1. Create part document
        doc = ws.new(PART, "plate")
        print("  Created part 'plate'", flush=True)

        # 2. Add plate (100x100x10 mm) and through hole (Ø 10 mm at centre)
        plate_length = 100.0
        plate_width = 100.0
        plate_thickness = 10.0
        hole_diameter = 10.0

        doc.session.batch([
            {
                "command": "solid.box",
                "params": {
                    "length": plate_length,
                    "width": plate_width,
                    "height": plate_thickness,
                    "corner": [0.0, 0.0, 0.0],
                    "name": "Platte",
                },
            },
            {
                "command": "solid.hole",
                "params": {
                    "position": [plate_length / 2.0, plate_width / 2.0, plate_thickness],
                    "direction": [0.0, 0.0, -1.0],
                    "diameter": hole_diameter,
                    "depth": plate_thickness,
                    "name": "Bohrung",
                },
            },
        ])
        print("  Added box and hole features", flush=True)

        # 3. check_design
        report = server.check_design("plate")
        verdict = report.get("verdict")
        print(f"  check_design verdict: {verdict}", flush=True)
        if verdict != "ok":
            raise RuntimeError(f"check_design reported failure: {report}")

        # 4. Save
        doc.save()
        saved_path = doc.path
        print(f"  Saved part to {saved_path}", flush=True)
        ws.close("plate")
        print("  Closed part session", flush=True)

        # 5. Reopen
        doc2 = ws.open(saved_path)
        print("  Reopened part from disk", flush=True)

        # 6. Check volume against analytical expectation
        meas = server.measure("plate")
        bodies = meas.get("bodies", [])
        if not bodies:
            raise RuntimeError("No bodies returned from measure")
        measured_vol = bodies[0].get("volume_mm3", 0.0)

        expected_box_vol = plate_length * plate_width * plate_thickness
        expected_hole_vol = math.pi * ((hole_diameter / 2.0) ** 2) * plate_thickness
        expected_vol = expected_box_vol - expected_hole_vol

        diff = abs(measured_vol - expected_vol)
        print(f"  Measured volume: {measured_vol:.2f} mm³", flush=True)
        print(f"  Expected volume: {expected_vol:.2f} mm³", flush=True)
        print(f"  Difference: {diff:.2f} mm³", flush=True)

        if diff > 5.0:
            raise RuntimeError(f"Volume difference {diff:.2f} mm³ exceeds tolerance (5.0 mm³)")

        ws.close_all()

    print("  OK: part modeling and volume check passed.\n", flush=True)


def test_ui_server() -> None:
    """Launch `mechvane ui --demo --no-browser --port <free>`, query APIs, exit cleanly."""
    print("== [3/3] Testing UI server (--demo mode) ==", flush=True)
    port = get_free_port()
    cmd = [
        sys.executable,
        "-m",
        "mechvane",
        "ui",
        "--demo",
        "--no-browser",
        "--port",
        str(port),
    ]
    print(f"  Starting UI server: {' '.join(cmd)}", flush=True)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for server to respond to /api/project
        base_url = f"http://127.0.0.1:{port}"
        project_data = None
        deadline = time.time() + 45.0

        while time.time() < deadline:
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=5)
                raise RuntimeError(
                    f"UI server process terminated prematurely with exit code {proc.returncode}:\n{out}\n{err}"
                )
            try:
                req = urllib.request.Request(f"{base_url}/api/project")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        project_data = json.loads(resp.read().decode("utf-8"))
                        break
            except Exception:
                time.sleep(0.3)

        if project_data is None:
            raise TimeoutError("UI server did not respond to /api/project within 45 seconds")

        documents = project_data.get("documents", [])
        print(f"  /api/project OK: mode={project_data.get('mode')}, {len(documents)} document(s)", flush=True)
        if not documents:
            raise RuntimeError("No documents found in /api/project demo response")

        # Open a document to query /api/mesh
        doc_name = documents[0]["name"]
        encoded_name = urllib.parse.quote(doc_name)
        open_req = urllib.request.Request(
            f"{base_url}/api/open/{encoded_name}",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(open_req, timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError(f"/api/open/{doc_name} returned status {resp.status}")
        print(f"  Opened demo document: {doc_name}", flush=True)

        # Query /api/mesh
        mesh_req = urllib.request.Request(f"{base_url}/api/mesh")
        with urllib.request.urlopen(mesh_req, timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError(f"/api/mesh returned status {resp.status}")
            mesh_data = json.loads(resp.read().decode("utf-8"))

        bodies = mesh_data.get("bodies", [])
        if not bodies:
            raise RuntimeError(f"No bodies returned in /api/mesh for {doc_name}")
        print(f"  /api/mesh OK: {len(bodies)} body/bodies in mesh", flush=True)

        # Clean shutdown via /api/quit
        quit_req = urllib.request.Request(
            f"{base_url}/api/quit",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(quit_req, timeout=5) as resp:
                print(f"  /api/quit sent (HTTP {resp.status})", flush=True)
        except Exception as e:
            print(f"  Warning on /api/quit request: {e}", flush=True)

        try:
            proc.wait(timeout=10)
            print(f"  Server process exited with code {proc.returncode}", flush=True)
        except subprocess.TimeoutExpired:
            print("  Warning: server did not exit within 10s after /api/quit, terminating...", flush=True)
            proc.terminate()
            proc.wait(timeout=5)

        if proc.returncode != 0:
            out, err = proc.communicate()
            raise RuntimeError(f"UI server finished with non-zero exit code {proc.returncode}:\n{out}\n{err}")

        print("  OK: UI server started, responded to API queries, and stopped cleanly.\n", flush=True)

    except Exception as exc:
        # show the server's answer and its own output, so a CI failure says why (Windows: HTTP 500 on /api/mesh)
        if isinstance(exc, urllib.error.HTTPError):
            print(f"  HTTP {exc.code} body: {exc.read()[:2000]!r}", file=sys.stderr, flush=True)
        if proc.poll() is None:
            proc.terminate()
        try:
            out, err = proc.communicate(timeout=10)
        except Exception:
            out, err = "", ""
        print("---- UI server stdout (tail) ----\n" + "\n".join((out or "").splitlines()[-60:]), file=sys.stderr)
        print("---- UI server stderr (tail) ----\n" + "\n".join((err or "").splitlines()[-60:]), file=sys.stderr, flush=True)
        raise

    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def main() -> None:
    print("=== Mechvane CI Smoke Test ===\n", flush=True)
    t0 = time.time()
    run_setup()
    test_part_modeling()
    test_ui_server()
    elapsed = time.time() - t0
    print(f"=== All CI smoke checks passed in {elapsed:.1f}s ===", flush=True)


if __name__ == "__main__":
    main()
