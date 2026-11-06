"""Click through the workspace in a headless browser: measure two points, open a section, Esc, then
walk right from the centre until a click lands on an edge and the readout measures it; in a part also
the Fillet dialog (preview, Esc, OK, edit by double-click, Ctrl+Z), the Hole dialog (face click,
Middle of face, Ctrl+Z twice), and the Extrude dialog with profile selection.

    <python with playwright> tools/ui_smoke.py [url] [out_dir]   (default http://127.0.0.1:8799/, screenshots in .)

Start the UI first (`python3 -m mechvane ui <part> --no-browser --port 8799`), or let this script
prepare a part and start a temporary server if none is running.

Prepare the test part:
    python3 tools/ui_smoke.py --prepare [path.solidcraft]

Needs the playwright package; the browser is taken from ~/.cache/ms-playwright (chrome-headless-shell)
if installed there.
"""
import glob
import json
import os
import re
import socket
import sys
import tempfile
import threading
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# Ensure mechvane is importable even when using playwright from a foreign virtualenv
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def prepare_part(path: str | Path):
    """Create a test part with a box 80x50x10 and a sketch with two separate circles (r 10 and r 5)."""
    from mechvane.documents import Workspace, PART

    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    ws = Workspace(p.parent)
    try:
        name = p.stem
        if name in ws.docs:
            ws.close(name)
        doc = ws.new(PART, name)
        s = doc.session
        s.cmd("solid.box", {"length": 80, "width": 50, "height": 10, "corner": [-40, -25, 0],
                            "body_name": "Body1", "name": "Box1"})
        s.cmd("sketch.create", {"plane": "XY", "name": "Sketch1"})
        s.cmd("sketch.circle.center", {"center": [100, 0], "radius": 10})
        s.cmd("sketch.circle.center", {"center": [140, 0], "radius": 5})
        s.cmd("sketch.finish", {})
        doc.save()
    finally:
        ws.close_all()
    print(f"Prepared test part: {p}")
    return p


if "--prepare" in sys.argv:
    idx = sys.argv.index("--prepare")
    target = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("-") else "smoke_part.solidcraft"
    prepare_part(target)
    sys.exit(0)

from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
url = args[0] if len(args) > 0 else "http://127.0.0.1:8799/"
out = args[1] if len(args) > 1 else "."

parsed_url = urlparse(url)
host = parsed_url.hostname or "127.0.0.1"
port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

# Check if a server is already listening
server_active = False
try:
    with socket.socket() as sock:
        sock.settimeout(1.0)
        server_active = (sock.connect_ex((host, port)) == 0)
except Exception:
    server_active = False

srv = None
tmp_dir = None
if not server_active:
    from mechvane.ui.server import create_server
    tmp_dir = tempfile.TemporaryDirectory(prefix="mechvane-smoke-")
    part_file = prepare_part(Path(tmp_dir.name) / "smoke_part.solidcraft")
    srv = create_server(str(part_file), port=port)
    srv_thread = threading.Thread(target=srv.serve_forever, daemon=True)
    srv_thread.start()
    time.sleep(0.5)

# Track session log position to detect new js_error entries
from mechvane import install
today_str = f"{date.today():%Y-%m-%d}.jsonl"
log_file = install.CACHE / "logs" / today_str
log_pos = log_file.stat().st_size if log_file.exists() else 0

shells = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))
errors = []

fillet = "skipped (assembly or static demo)"
fillet_ok = True
hole = "skipped (no hole dialog or not a part)"
hole_ok = True
extrude = "skipped (no extrude dialog or not a part)"
extrude_ok = True
sketch = "skipped (no sketch button or not a part)"
sketch_ok = True
new_part = "skipped (no folder)"
new_part_ok = True
measured = ""
section = ""
closed = False
edge = ""

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=shells[-1] if shells else None,
                                     args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1300, "height": 750})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("dialog", lambda d: (errors.append(f"browser dialog: {d.message}"), d.dismiss()))
        page.goto(url)
        page.wait_for_timeout(5000)
        page.click('.ribbon-tab[data-tab="inspect"]')
        box = page.locator("#viewport canvas").bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.click("text=Measure")
        # offsets relative to the 3D view: the workspace side panels make it narrower than the window
        for fx, fy in ((-0.08, -0.04), (0.08, 0.02)):
            page.mouse.click(cx + fx * box["width"], cy + fy * box["height"])
            page.wait_for_timeout(300)
        measured = page.locator(".measure-readout").inner_text()
        page.screenshot(path=os.path.join(out, "measure.png"))
        page.click("text=Section")
        page.wait_for_timeout(300)
        section = page.locator(".measure-readout").inner_text()
        page.screenshot(path=os.path.join(out, "section.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        closed = page.locator(".measure-readout").is_hidden()
        for dx in range(0, int(box["width"] / 2), 2):
            page.click("text=Measure")
            page.mouse.click(cx + dx, cy)
            page.wait_for_timeout(60)
            text = page.locator(".measure-readout").inner_text()
            page.keyboard.press("Escape")
            if any(w in text for w in ("Edge length", "Circle", "Arc")):
                edge = text
                page.click("text=Measure")
                page.mouse.click(cx + dx, cy)
                page.wait_for_timeout(200)
                page.screenshot(path=os.path.join(out, "measure_edge.png"))
                break

        # Folder mode only (File -> New part... visible): the app's own dialog, not prompt(). Typing the name of a
        # file that exists shows the error inside the dialog; Cancel closes it. Nothing is created.
        page.click("#file-menu > summary")
        if page.locator("#btn-new-part").is_visible():
            existing = page.locator(".file-doc-item").first.get_attribute("data-value") or ""
            page.click("#btn-new-part")
            dlg = page.locator("#new-part-dialog")
            default = page.locator("#new-part-name").input_value()
            page.fill("#new-part-name", existing.removesuffix(".solidcraft"))
            page.click("#new-part-dialog .btn-submit")
            page.wait_for_timeout(500)
            err = page.locator("#new-part-error")
            shown = dlg.is_visible() and err.is_visible() and err.inner_text().strip() != ""
            page.screenshot(path=os.path.join(out, "new_part.png"))
            page.click("#new-part-dialog .btn-cancel")
            new_part = f"default {default!r}, error for {existing!r}: {shown}, closes: {dlg.is_hidden()}"
            new_part_ok = bool(default) and shown and dlg.is_hidden()
        else:
            page.keyboard.press("Escape")
            new_part_ok = True

        # Feature dialog (parts only): Fillet opens in Properties, walking up from the centre a click picks an edge,
        # the preview shows the volume change, Esc cancels without a change; again with OK the tree gets Fillet1,
        # and Ctrl+Z takes it back, so the file ends as it started.
        if page.locator("#btn-fillet").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            fillet_ok = False
            page.click('.ribbon-tab[data-tab="3d-model"]')

            def pick_edge():
                page.click("#btn-fillet")
                for dy in range(0, int(box["height"] / 2) - 10, 6):
                    page.mouse.click(cx, cy - dy)
                    page.wait_for_timeout(60)
                    if "selected" in page.locator(".feature-pick-count").inner_text():
                        break
                page.fill('.feature-dialog input[name="radius"]', "0.5")
                # "Computing preview…" while SolidCraft works; then the volume change or an error
                page.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '')"
                                       " || !document.querySelector('.feature-error')?.hidden", timeout=30000)
                return page.locator(".feature-delta").inner_text(), page.locator(".feature-error").inner_text()

            tree_before = page.locator("#tree-content").inner_text()
            delta, err = pick_edge()
            page.screenshot(path=os.path.join(out, "fillet_preview.png"))
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            cancelled = page.locator(".feature-dialog").count() == 0 and page.locator("#tree-content").inner_text() == tree_before
            pick_edge()
            page.click(".feature-ok")
            page.wait_for_timeout(2500)
            added = "Fillet" in page.locator("#tree-content").inner_text() and "Fillet" not in tree_before
            # double-click in the model browser opens it again with its edge and radius; Esc leaves it as it is
            page.dblclick('.tree-row[data-type="FilletFeature"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            reopened = ("1 edge" in page.locator(".feature-pick-count").inner_text()
                        and page.input_value('.feature-dialog input[name="radius"]') == "0.5")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            page.keyboard.press("Control+z")
            page.wait_for_timeout(2500)
            undone = page.locator("#tree-content").inner_text() == tree_before
            fillet = (f"preview {delta!r} {err!r}, esc cancels: {cancelled}, ok adds: {added}, edit reopens: {reopened}, "
                      f"ctrl+z: {undone}")
            fillet_ok = "Volume" in delta and not err and cancelled and added and reopened and undone

        # Hole dialog: face click (Hole1), Middle of face (Hole centre sketch), Ctrl+Z twice
        if page.locator("#btn-hole").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            hole_ok = False
            page.click('.ribbon-tab[data-tab="3d-model"]')
            tree_before_hole = page.locator("#tree-content").inner_text()

            def pick_face(dx=0):
                page.click("#btn-hole")
                page.wait_for_selector(".feature-dialog", timeout=5000)
                for dy in range(0, int(box["height"] / 2) - 10, 6):
                    if errors:
                        break
                    page.mouse.click(cx + dx, cy - dy)
                    page.wait_for_timeout(60)
                    if page.input_value('.feature-dialog input[name="x"]'):
                        break

            # (a) von der Mitte der Ansicht aus klicken, bis input[name="x"] gefüllt ist; OK -> Hole1 im Baum
            pick_face(0)
            added_hole1 = False
            if not page.locator(".feature-ok").is_enabled():
                errors.append(f"Hole 1: OK button disabled (x={page.input_value('.feature-dialog input[name=\"x\"]')!r})")
            else:
                page.click(".feature-ok")
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Hole1')", timeout=10000)
                page.screenshot(path=os.path.join(out, "hole1.png"))
                added_hole1 = "Hole1" in page.locator("#tree-content").inner_text()

            # (b) neu, Häkchen input[name="centre"] („Middle of face“), Statuszeile enthält „Middle of the face“,
            # OK → Skizze Hole centre … im Baum
            pick_face(-30)
            page.check('.feature-dialog input[name="centre"]')
            page.wait_for_timeout(100)
            centre_status = page.locator(".feature-pick-count").inner_text()
            has_centre_status = "Middle of the face" in centre_status
            page.screenshot(path=os.path.join(out, "hole_centre.png"))

            added_centre = False
            if not page.locator(".feature-ok").is_enabled():
                errors.append(f"Hole 2: OK button disabled (x={page.input_value('.feature-dialog input[name=\"x\"]')!r})")
            else:
                page.click(".feature-ok")
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Hole centre')", timeout=10000)
                added_centre = "Hole centre" in page.locator("#tree-content").inner_text()

            # Danach Strg+Z zweimal, Datei wie vorher
            page.keyboard.press("Control+z")
            page.wait_for_timeout(2000)
            page.keyboard.press("Control+z")
            page.wait_for_timeout(2000)
            undone_holes = page.locator("#tree-content").inner_text() == tree_before_hole
            hole = (f"hole1: {added_hole1}, centre status: {has_centre_status}, centre sketch: {added_centre}, "
                    f"ctrl+z twice: {undone_holes}")
            hole_ok = added_hole1 and has_centre_status and added_centre and undone_holes

        # Extrusion mit Profilwahl: Teil mit zwei getrennten Kreisen (r 10 und r 5), Profil 2 wählen (+785 mm³),
        # OK -> Extrude1, Doppelklick öffnet Dialog mit Profil-Wert 1, Esc, Ctrl+Z
        if page.locator("#btn-extrude").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            extrude_ok = False
            page.click('.ribbon-tab[data-tab="3d-model"]')
            tree_before_extrude = page.locator("#tree-content").inner_text()
            page.click("#btn-extrude")
            page.wait_for_selector(".feature-dialog", timeout=5000)

            # select[name="profile"] zeigt drei Einträge
            opt_count = page.locator('.feature-dialog select[name="profile"] option').count()
            profiles_three = (opt_count == 3)

            # Profil 2 wählen
            page.select_option('.feature-dialog select[name="profile"]', "1")

            # Vorschau zeigt „Volume +785“ (± 1)
            page.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '')"
                                   " || !document.querySelector('.feature-error')?.hidden", timeout=30000)
            extrude_delta = page.locator(".feature-delta").inner_text()
            page.screenshot(path=os.path.join(out, "extrude_profile_preview.png"))
            vol_785 = bool(re.search(r"Volume\s*\+\s*78[456]", extrude_delta))

            # OK
            added_extrude = False
            if not page.locator(".feature-ok").is_enabled():
                errors.append("Extrude: OK button disabled")
            else:
                page.click(".feature-ok")
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Extrude1')", timeout=10000)
                added_extrude = "Extrude1" in page.locator("#tree-content").inner_text()

            # Doppelklick auf Extrude1 im Baum öffnet den Dialog mit Profil-Wert 1, Esc
            page.dblclick('.tree-row[data-type="ExtrudeFeature"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            reopened_val = page.input_value('.feature-dialog select[name="profile"]')
            reopened_ok = (reopened_val == "1")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            # Strg+Z, Datei wie vorher
            page.keyboard.press("Control+z")
            page.wait_for_timeout(2000)
            undone_extrude = page.locator("#tree-content").inner_text() == tree_before_extrude
            extrude = (f"3 profiles: {profiles_three}, delta: {extrude_delta!r} (vol_785: {vol_785}), "
                       f"ok adds: {added_extrude}, edit profile 1: {reopened_ok}, ctrl+z: {undone_extrude}")
            extrude_ok = profiles_three and vol_785 and added_extrude and reopened_ok and undone_extrude

        # Sketch environment (sketcher.js): S, plane XY, a line with a typed length (40, a dimension), a rectangle,
        # a circle, Ctrl+Z takes the circle back, Enter finishes; the tree gets a sketch, Ctrl+Z removes it again
        if page.locator("#btn-sketch").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            sketch_ok = False
            state = lambda: page.evaluate("fetch('api/sketch/state').then(r => r.json())")
            page.click('.ribbon-tab[data-tab="3d-model"]')
            tree_before_sketch = page.locator("#tree-content").inner_text()
            page.keyboard.press("s")
            page.click(".sketch-plane-bar [data-plane=XY]")
            page.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=10000)
            box = page.locator("#viewport canvas").bounding_box()
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            w = box["width"]
            page.keyboard.press("l")
            page.mouse.click(cx - 0.15 * w, cy + 0.1 * w)
            page.mouse.move(cx - 0.05 * w, cy + 0.1 * w)
            hud_shown = page.locator(".sketch-hud").is_visible()
            page.keyboard.type("40")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)
            page.keyboard.press("Escape")
            page.keyboard.press("r")
            page.mouse.click(cx + 0.02 * w, cy - 0.05 * w)
            page.mouse.click(cx + 0.1 * w, cy - 0.1 * w)
            page.wait_for_timeout(1500)
            page.keyboard.press("c")
            page.mouse.click(cx + 0.08 * w, cy + 0.08 * w)
            page.mouse.click(cx + 0.11 * w, cy + 0.08 * w)
            page.wait_for_timeout(1500)
            # Dimension: the typed length shows as "40" on the line; double-click it and change it to 45
            page.keyboard.press("Escape")
            label_40 = page.locator(".sketch-dim", has_text="40")
            dim_label = label_40.count() == 1
            if dim_label:
                label_40.first.dblclick()
                page.keyboard.press("Control+a")
                page.keyboard.type("45")
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)
            st = state()["state"]
            kinds = sorted(c["type"] for c in st["curves"])
            lengths = [c.get("value") for c in st["constraints"] if c.get("type") == "length"]
            page.screenshot(path=os.path.join(out, "sketch.png"))
            page.keyboard.press("Escape")
            # Ctrl+Z goes back one command: first the changed dimension (45 -> 40), then the circle
            page.keyboard.press("Control+z")
            page.wait_for_timeout(1500)
            back_to_40 = 40 in [c.get("value") for c in state()["state"]["constraints"] if c.get("type") == "length"]
            page.keyboard.press("Control+z")
            page.wait_for_timeout(1500)
            undone_circle = back_to_40 and "circle" not in [c["type"] for c in state()["state"]["curves"]]
            # Constraints show as symbols (the rectangle's H and V); click one H, Delete removes that constraint
            page.keyboard.press("Escape")
            n_hv = lambda: sum(c["type"] in ("horizontal", "vertical") for c in state()["state"]["constraints"])
            hv_before = n_hv()
            glyph_h = page.locator(".sketch-glyph", has_text="H")
            glyphs_shown = glyph_h.count() >= 2
            if glyphs_shown:
                glyph_h.first.click()
                page.keyboard.press("Delete")
                page.wait_for_timeout(1500)
            glyph_deleted = glyphs_shown and n_hv() == hv_before - 1
            page.keyboard.press("Enter")
            page.wait_for_function("document.querySelector('.ribbon-tab[data-tab=\"3d-model\"]').classList.contains('active')",
                                   timeout=10000)
            page.wait_for_timeout(2000)
            closed_sketch = not state().get("active")
            added_sketch = page.locator("#tree-content").inner_text() != tree_before_sketch
            page.keyboard.press("Control+z")
            page.wait_for_timeout(2500)
            undone_sketch = page.locator("#tree-content").inner_text() == tree_before_sketch
            sketch = (f"hud: {hud_shown}, curves: {kinds}, label 40: {dim_label}, length after edit: {lengths}, "
                      f"ctrl+z circle: {undone_circle}, delete H symbol: {glyph_deleted}, "
                      f"finished: {closed_sketch and added_sketch}, ctrl+z sketch: {undone_sketch}")
            sketch_ok = (hud_shown and kinds.count("line") == 5 and kinds.count("circle") == 1 and dim_label and 45 in lengths
                         and undone_circle and glyph_deleted and closed_sketch and added_sketch and undone_sketch)

        browser.close()
except Exception as exc:
    errors.append(f"browser test exception: {exc}")
finally:
    if srv:
        srv.shutdown()
        srv.server_close()
    if tmp_dir:
        tmp_dir.cleanup()

# Read js_error events from session log
time.sleep(0.5)
js_errors = []
if log_file.exists():
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            f.seek(log_pos)
            for line in f:
                try:
                    ev = json.loads(line)
                    if ev.get("kind") == "browser" and ev.get("event") == "js_error":
                        js_errors.append(ev.get("message") or str(ev))
                except Exception:
                    pass
    except Exception as e:
        print("warning: reading session log failed:", e)

print("fillet:", fillet)
print("hole:", hole)
print("extrude:", extrude)
print("sketch:", sketch)
print("new part:", new_part)
print("measure:", measured.replace("\n", " | "))
print("section:", section)
print("esc closes:", closed, "page errors:", errors)
print("session log js_errors:", js_errors)
print("edge:", edge.replace("\n", " | ") or "none found")

all_checks_ok = ("Distance" in measured and "Section" in section and closed and bool(edge) and new_part_ok and fillet_ok
                 and hole_ok and extrude_ok and sketch_ok and not errors and not js_errors)

if errors:
    for e in errors:
        print(f"FAIL pageerror: {e}")
if js_errors:
    for e in js_errors:
        print(f"FAIL js_error: {e}")

if not all_checks_ok:
    print("FAIL")
    sys.exit(1)

sys.exit(0)
