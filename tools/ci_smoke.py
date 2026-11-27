#!/usr/bin/env python3
"""Cross-platform smoke test for Mechvane CI (Windows, macOS, Linux).

Verifies:
1. `mechvane setup` (download and unpack the pinned SolidCraft CLI).
2. Python interface: create a part (plate with hole), check_design, save, reopen,
   and verify volume against expected value.
3. Wheel: contains the knowledge catalog, installs into a fresh venv and finds the rule sources there (#169).

Standard library only, plus mechvane.
"""

import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Ensure repository root is on sys.path even when invoked without pip install -e
REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def run_setup() -> None:
    """Run `mechvane setup` via CLI entry point."""
    print("== [1/2] Running `mechvane setup` ==", flush=True)
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
    print("== [2/2] Testing part creation, check_design, save, reopen, volume ==", flush=True)
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


def test_wheel_ships_catalog() -> None:
    """The wheel carries the knowledge catalog (#169): 0.1.0a24 shipped without it, so installed packages showed findings
    without their source. Builds the wheel, compares its catalog entries and the other package data with the source tree,
    installs it into a fresh venv and asks for the rule sources there."""
    import shutil
    import zipfile
    print("Testing wheel contents (catalog)...", flush=True)
    # a leftover build/lib from an earlier build would be packed again and could hide a broken configuration
    shutil.rmtree(REPO / "build" / "lib", ignore_errors=True)
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-q", "-w", td], cwd=REPO,
                           capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, f"pip wheel failed: {(r.stdout + r.stderr)[-500:]}"
        wheel = next(Path(td).glob("mechvane-*.whl"))
        names = set(zipfile.ZipFile(wheel).namelist())

        def tree(sub: str) -> set:
            return {p.relative_to(REPO / sub).as_posix() for p in (REPO / sub).rglob("*") if p.is_file()}

        prefix = "mechvane/katalog_data/eintraege/"
        shipped = {n[len(prefix):] for n in names if n.startswith(prefix)}
        expected = {n for n in tree("katalog/eintraege") if n.endswith(".json")}
        assert shipped == expected and len(expected) >= 100, (
            f"wheel catalog differs from katalog/eintraege: missing {sorted(expected - shipped)[:3]}, extra {sorted(shipped - expected)[:3]}")
        for sub, pat in (("mechvane/data", ".json"),):  # other package data must survive the explicit package list
            want = {f"{sub}/{n}" for n in tree(sub) if n.endswith(pat)}
            assert want and want <= names, f"wheel misses package data under {sub}: {sorted(want - names)[:3]}"
        # install into a fresh venv and ask for the sources there (no SolidCraft needed); -I keeps the checkout out of sys.path
        venv = Path(td) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=300)
        py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        r = subprocess.run([str(py), "-m", "pip", "install", "--no-deps", "-q", str(wheel)], capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, f"pip install failed: {(r.stdout + r.stderr)[-500:]}"
        r = subprocess.run([str(py), "-I", "-c", "from mechvane import design_rules, katalog; "
                            "s = design_rules.rule_sources(); assert len(s) >= 10 and all(v.get('zitat') for v in s.values()), s; "
                            "print(len(katalog.load()), len(s))"], capture_output=True, text=True, cwd=td, timeout=120)
        assert r.returncode == 0, f"installed wheel finds no rule sources: {(r.stdout + r.stderr)[-500:]}"
    print(f"  ok: {len(shipped)} catalog entries in the wheel; installed copy reports {r.stdout.strip()} (entries, rule sources)", flush=True)


def main() -> None:
    print("=== Mechvane CI Smoke Test ===\n", flush=True)
    t0 = time.time()
    run_setup()
    test_wheel_ships_catalog()
    test_part_modeling()
    elapsed = time.time() - t0
    print(f"=== All CI smoke checks passed in {elapsed:.1f}s ===", flush=True)


if __name__ == "__main__":
    main()
