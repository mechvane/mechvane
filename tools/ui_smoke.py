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


def _arm_undo_watch(page):
    """Before Ctrl+Z: note when the status line says Undone or Redone. undoRedo writes that only after its own
    reload, and a reload from the version poll can end earlier with Ready, so Ready is no proof (#156)."""
    page.evaluate("""() => {
        const el = document.getElementById('status-indicator');
        window.__undoSeen = false;
        el.textContent = '';
        new MutationObserver((_, obs) => {
            if (/^(Undone|Redone)$/.test(el.textContent)) { window.__undoSeen = true; obs.disconnect(); }
        }).observe(el, { childList: true, characterData: true, subtree: true });
    }""")


def _wait_undo_done(page, timeout=30.0):
    """The undo armed with _arm_undo_watch has finished (#156): the workspace said Undone after its reload and the
    server has a redo entry. Polled from Python: page.evaluate waits for the fetch, wait_for_function would not."""
    end = time.time() + timeout
    while True:
        seen = page.evaluate("window.__undoSeen === true")
        h = page.evaluate("fetch('api/history').then(r => r.json()).catch(() => ({}))") if seen else {}
        if seen and h.get("redo"):
            return
        if time.time() > end:
            raise TimeoutError(f"undo not finished after {timeout:.0f} s: status seen {seen}, history {h}")
        time.sleep(0.25)


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
        s.cmd("sketch.line", {"points": [[120, -10], [120, 10]], "construction": True})
        s.cmd("sketch.finish", {})
        doc.save()
    finally:
        ws.close_all()
    print(f"Prepared test part: {p}")
    return p


def prepare_edit_part(path: str | Path):
    """Create a part holding one of every EDITABLE feature type (each kept independent for roundtrip edits)."""
    from mechvane.documents import Workspace, PART

    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    ws = Workspace(p.parent)
    try:
        if p.stem in ws.docs:
            ws.close(p.stem)
        doc = ws.new(PART, p.stem)
        s = doc.session
        s.cmd("parameters.add", {"name": "P_VAL", "expression": "1.5"})
        s.cmd("solid.box", {"length": 80, "width": 50, "height": 10, "corner": [-40, -25, 0], "body_name": "Body1", "name": "Box1"})
        s.cmd("solid.hole", {"position": [-16, -6, 10], "direction": [0, 0, -1], "diameter": 3, "name": "SeedHole"})
        s.cmd("solid.hole", {"position": [-8, -6, 10], "direction": [0, 0, -1], "diameter": 4, "name": "AxisHole"})
        s.cmd("sketch.create", {"plane": {"face": [0, 0, 10]}, "project_edges": False, "name": "SkExt"})
        s.cmd("sketch.rectangle.two_point", {"p0": [-34, -12], "p1": [-24, -4]})
        s.cmd("sketch.rectangle.two_point", {"p0": [-34, 4], "p1": [-24, 14]})
        s.cmd("sketch.finish", {})
        s.cmd("solid.extrude", {"sketch": "SkExt", "profiles": [0], "distance": 5, "operation": "join", "direction": "positive", "name": "Ext1"})
        s.cmd("solid.hole", {"position": [20, 12, 10], "direction": [0, 0, -1], "diameter": 5.5, "depth": 6, "name": "Hole1"})
        s.cmd("solid.pattern.rectangular", {"features": ["SeedHole"], "dir1": [1, 0, 0], "count1": 2, "spacing1": 16, "name": "Rect1"})
        s.cmd("solid.pattern.circular", {"features": ["SeedHole"], "axis": "Z", "count": 2, "angle": "90 deg", "name": "Circ1"})
        s.cmd("solid.mirror", {"features": ["SeedHole"], "plane": "YZ", "name": "Mirror1"})
        s.cmd("solid.fillet", {"edges": [[-40, 0, 10]], "radius": 1, "name": "Fillet1"})
        s.cmd("solid.chamfer", {"edges": [[40, 0, 10]], "distance": 1, "name": "Chamfer1"})
        s.cmd("sketch.create", {"plane": "XY", "name": "SkRev"})
        s.cmd("sketch.circle.center", {"center": [50, 0], "radius": 4})
        s.cmd("sketch.circle.center", {"center": [60, 0], "radius": 3})
        s.cmd("sketch.line", {"points": [[45, -12], [45, 12]], "construction": True})
        s.cmd("sketch.finish", {})
        s.cmd("solid.revolve", {"sketch": "SkRev", "profiles": [0], "axis": "l1", "angle": "180 deg", "operation": "new", "name": "Rev1"})
        doc.save()
    finally:
        ws.close_all()
    return p


if "--prepare" in sys.argv:
    idx = sys.argv.index("--prepare")
    target = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("-") else "smoke_part.solidcraft"
    prepare_part(target)
    sys.exit(0)

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heavy_lock import hold  # noqa: E402

hold("ui_smoke")  # one heavy run at a time (audit 2026-11-16, A5)

args = [a for a in sys.argv[1:] if not a.startswith("--")]
url = args[0] if len(args) > 0 else "http://127.0.0.1:8799/"
# Screenshots go to a temp folder by default, never into the checkout (agents committed them, 2026-11-08).
out = args[1] if len(args) > 1 else os.path.join(tempfile.gettempdir(), "mechvane-ui-smoke")
os.makedirs(out, exist_ok=True)

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
command_dialog = "skipped (assembly or static demo)"
command_dialog_ok = True
hole = "skipped (no hole dialog or not a part)"
hole_ok = True
extrude = "skipped (no extrude dialog or not a part)"
extrude_ok = True
revolve = "skipped (no revolve dialog or not a part)"
revolve_ok = True
rename_status = "skipped"
rename_ok = True
sketch = "skipped (no sketch button or not a part)"
# set before the browser block: an early exception must end as FAIL with its cause, not as NameError (#87)
visibility_ok = False
visibility = "not tested (an earlier step failed)"
folder_mode = "skipped (server given)"
folder_ok = True
sketch_ok = True
new_part = "skipped (no folder)"
new_part_ok = True
open_folder = "skipped (no folder)"
open_folder_ok = True
import_browse = "skipped (no folder)"
import_browse_ok = True
assemble_tab = "skipped (no folder)"
assemble_tab_ok = True
edit_roundtrip_server = "skipped (server given)"
edit_roundtrip_server_ok = True
edit_roundtrip_demo = "skipped (server given)"
edit_roundtrip_demo_ok = True
measured = ""
section = ""
closed = False
edge = ""

def _apply_cpu_throttle(page):
    raw = os.environ.get("UI_SLOW", "").strip()
    if not raw or raw.lower() in ("0", "false", "no"):
        return
    rate = 4.0 if raw.lower() in ("1", "true", "yes") else float(raw)
    page.context.new_cdp_session(page).send("Emulation.setCPUThrottlingRate", {"rate": rate})


def _wait_frame(page):
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => r()))")


def _wait_ready(page, timeout=30000):
    page.wait_for_function(
        """() => {
            if (document.getElementById('status-indicator')?.textContent !== 'Ready') return false;
            if (!document.querySelector('#tree-content .tree-row')) return false;
            let hasMesh = false;
            window.__scene?.traverse(o => { if (o.isMesh && o.userData?.bodyName) hasMesh = true; });
            if (!hasMesh) return false;
            const unusedSketch = document.querySelector('#tree-content > ul.tree-list > li.tree-item > .tree-row[data-type="Sketch"]:not(.tree-hidden)');
            if (unusedSketch) {
                const g = window.__scene?.children?.find(c => c.renderOrder === 8);
                if (!g || !g.children.length) return false;
            }
            return true;
        }""",
        timeout=timeout,
    )


def _wait_dialog_done(page, timeout=20000):
    page.wait_for_function(
        "() => !document.querySelector('.feature-dialog') && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
        timeout=timeout,
    )


def _wait_dialog_closed(page, timeout=5000):
    page.wait_for_function("!document.querySelector('.feature-dialog')", timeout=timeout)


def _wait_sketch_idle(page, timeout=15000):
    page.wait_for_function(
        "() => !document.body.classList.contains('sketching') && document.getElementById('status-indicator')?.textContent === 'Ready'",
        timeout=timeout,
    )


def _build_edit_demo(part_path: Path, demo_dir: Path):
    """Build and serve a minimal static live-demo site containing part_path for edit-dialog roundtrips."""
    import http.server
    import shutil
    from mechvane.documents import Workspace
    from mechvane.ui import server as ui_srv, webapp
    from mechvane.ui.mesh import collect_mesh
    from build_demo_site import make_mechvane_zip

    shutil.copytree(ui_srv.STATIC_DIR, demo_dir)
    make_mechvane_zip(demo_dir / "mechvane.zip")
    (demo_dir / "hole_sizes.json").write_text(json.dumps(ui_srv.hole_sizes()), encoding="utf-8")
    idx = demo_dir / "index.html"
    idx.write_text(idx.read_text(encoding="utf-8").replace('<html lang="en">', '<html lang="en" data-static="1">', 1), encoding="utf-8")
    os.symlink(webapp.webapp_dir(), demo_dir / "sc")
    d = demo_dir / "demos" / part_path.stem
    (d / "files").mkdir(parents=True)
    shutil.copyfile(part_path, d / "files" / part_path.name)
    ws = Workspace(part_path.parent)
    try:
        doc = ws.open(part_path)
        data = {"version": dict(ui_srv.collect_version(doc), path=""), "mesh": collect_mesh(doc),
                "tree": ui_srv.collect_tree(ws, doc), "findings": ui_srv.collect_findings(ws, doc),
                "files": {"document": part_path.name, "kind": doc.kind, "files": [part_path.name]}}
        for k, v in data.items():
            (d / f"{k}.json").write_text(json.dumps(v, separators=(",", ":")), encoding="utf-8")
    finally:
        ws.close_all()
    (demo_dir / "demos" / "index.json").write_text(json.dumps({"demos": [{"name": part_path.stem, "title": part_path.stem}]}), encoding="utf-8")

    class _Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm"}
        def __init__(self, *a, **kw): super().__init__(*a, directory=str(demo_dir), **kw)
        def log_message(self, *a): pass

    return http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)


def _run_edit_roundtrip(page, label: str, target_url: str, *, is_demo: bool = False):
    """Open every EDITABLE feature by double-click, confirm unchanged, then edit every field type & 3D pick."""
    from mechvane.ui import server as ui_srv

    fjs = (ui_srv.STATIC_DIR / "features.js").read_text(encoding="utf-8")
    djs = (ui_srv.STATIC_DIR / "demo_kernel.js").read_text(encoding="utf-8")
    f_keys = sorted(re.findall(r"(\w+Feature)\s*:", re.search(r"export const EDITABLE_TYPES = \{([^}]+)\}", fjs).group(1)))
    d_keys = sorted(re.findall(r"(\w+Feature)\s*:", re.search(r"const EDITABLE = \{([^}]+)\}", djs).group(1)))
    tested = ["FilletFeature", "ChamferFeature", "HoleFeature", "RectangularPatternFeature",
              "CircularPatternFeature", "MirrorFeature", "ExtrudeFeature", "RevolveFeature"]
    assert f_keys == d_keys == sorted(ui_srv.EDITABLE) == sorted(tested), f"EDITABLE mismatch: {f_keys} / {d_keys}"

    step = f"{label}: load"
    page.goto(target_url)
    _wait_ready(page, timeout=60000)

    def mesh_geom():
        return page.evaluate("""() => {
            let vol = 0, cx = 0, cy = 0, cz = 0, bodies = 0;
            window.__scene?.traverse(o => {
                if (!o.isMesh || !o.userData?.bodyName || !o.visible) return;
                bodies++;
                const pos = o.geometry.attributes.position, idx = o.geometry.index;
                if (!pos || !idx) return;
                const a = pos.array, x = idx.array;
                for (let i = 0; i < x.length; i += 3) {
                    const p = x[i]*3, q = x[i+1]*3, r = x[i+2]*3;
                    const ax=a[p], ay=a[p+1], az=a[p+2], bx=a[q], by=a[q+1], bz=a[q+2], dx=a[r], dy=a[r+1], dz=a[r+2];
                    const v = (ax*(by*dz-bz*dy) - ay*(bx*dz-bz*dx) + az*(bx*dy-by*dx)) / 6;
                    vol += v; cx += v*(ax+bx+dx)/4; cy += v*(ay+by+dy)/4; cz += v*(az+bz+dz)/4;
                }
            });
            return { vol: Math.abs(vol), c: Math.abs(vol) > 1e-9 ? [cx/vol, cy/vol, cz/vol] : [0,0,0], bodies };
        }""")

    def geom_same(a, b):
        return (a["bodies"] == b["bodies"] and abs(a["vol"] - b["vol"]) < 1e-2
                and sum((x - y) ** 2 for x, y in zip(a["c"], b["c"])) ** 0.5 < 1e-2)

    def open_edit(feat, first=False):
        page.evaluate("() => { window.__editDef = null; }")
        page.dblclick(f'.tree-row[data-feature="{feat}"]')
        page.wait_for_function(
            "() => !!document.querySelector('.feature-dialog-title')?.textContent.includes('Edit')"
            " && window.__editDef !== null && document.getElementById('status-indicator')?.textContent === 'Ready'",
            timeout=180000 if (first and is_demo) else 60000)
        return page.evaluate("() => window.__editDef")

    def submit_edit(feat):
        page.evaluate("""() => {
            const el = document.getElementById('status-indicator');
            window.__editDone = false;
            new MutationObserver((_, obs) => {
                if (/^(Edit |Done)/.test(el.textContent || '')) { window.__editDone = true; obs.disconnect(); }
            }).observe(el, { childList: true, characterData: true, subtree: true });
        }""")
        page.wait_for_selector(".feature-ok:not([disabled])", timeout=10000)
        page.click(".feature-ok")
        page.wait_for_function(
            "() => (!document.querySelector('.feature-dialog') && window.__editDone === true"
            " && document.getElementById('status-indicator')?.textContent !== 'Computing…')"
            " || document.querySelector('.feature-error')?.hidden === false",
            timeout=120000 if is_demo else 30000)
        if page.locator(".feature-dialog").count() and page.locator(".feature-error").is_visible():
            raise AssertionError(f"{feat} edit error: {page.locator('.feature-error').inner_text()}")
        _wait_frame(page)
        return mesh_geom()

    val = lambda k: page.input_value(f'.feature-dialog [name="{k}"]')
    chk = lambda k: page.is_checked(f'.feature-dialog input[name="{k}"]')
    slot = lambda k: page.locator(f'.feature-slot[data-slot="{k}"]')

    def put(**kw):
        for k, v in kw.items():
            if isinstance(v, bool):
                page.set_checked(f'.feature-dialog input[name="{k}"]', v)
            elif page.locator(f'.feature-dialog select[name="{k}"]').count():
                page.select_option(f'.feature-dialog select[name="{k}"]', v)
            else:
                page.fill(f'.feature-dialog input[name="{k}"]', v)

    def verify_step(feat, prev_def, prev_geom, *, changed=True, dom=None, defn=None, keep_open=True):
        cur_geom = submit_edit(feat)
        assert (not geom_same(cur_geom, prev_geom)) if changed else geom_same(cur_geom, prev_geom), (
            f"{feat}: geom mismatch ({prev_geom} -> {cur_geom})")
        cur_def = open_edit(feat)
        assert (cur_def != prev_def) if changed else (cur_def == prev_def), f"{feat}: def mismatch ({cur_def})"
        for k, want in (dom or {}).items():
            got = chk(k) if isinstance(want, bool) else val(k)
            assert got == want, f"{feat}: field {k}={got!r}, expected {want!r}"
        if defn and not defn(cur_def):
            raise AssertionError(f"{feat}: reopened state mismatch ({cur_def})")
        if not keep_open:
            page.keyboard.press("Escape")
            _wait_dialog_closed(page)
        return cur_def, cur_geom

    def click_3d(pt3, cond_js, view=None):
        if view:
            set_view(view)
        xy = page.evaluate("""([x, y, z]) => {
            const p = window.__camera.position.clone().set(x, y, z).project(window.__camera);
            const r = document.querySelector('#viewport canvas').getBoundingClientRect();
            return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height];
        }""", pt3)
        hit = False
        for dx, dy in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2)):
            page.mouse.click(xy[0] + dx, xy[1] + dy)
            _wait_frame(page)
            if page.evaluate(cond_js):
                hit = True
                break
        if view:
            set_view("iso")
        if not hit:
            raise AssertionError(f"3D click at {pt3} did not satisfy {cond_js}")

    def set_view(name):
        if name == "iso":
            page.keyboard.press("F6")
            page.wait_for_function("() => Math.abs((window.__camera?.up?.z ?? 0) - 1) < 1e-4", timeout=5000)
        else:
            page.evaluate(f"() => document.querySelector('[data-view=\"{name}\"]')?.click()")
            page.wait_for_function("() => Math.abs((window.__camera?.up?.y ?? 0) - 1) < 1e-4", timeout=5000)
        _wait_frame(page)

    def start(feat, first=False):
        nonlocal step, g0
        step, g0 = f"{label}: {feat}", mesh_geom()
        return verify_step(feat, open_edit(feat, first=first), g0, changed=False)

    try:
        d0, g0 = start("Fillet1", first=True)
        put(radius="1.2"); d0, g0 = verify_step("Fillet1", d0, g0, dom={"radius": "1.2"})
        put(radius="P_VAL"); d0, g0 = verify_step("Fillet1", d0, g0, dom={"radius": "P_VAL"}, defn=lambda d: d.get("radius") == "P_VAL")
        click_3d([0, -25, 10], "() => (document.querySelector('.feature-pick-count')?.textContent || '').includes('2 edges')")
        verify_step("Fillet1", d0, g0, keep_open=False, defn=lambda d: "2 edges" in page.locator(".feature-pick-count").inner_text() and len(d.get("edges", [])) == 2)

        d0, g0 = start("Chamfer1")
        put(distance="1.2"); d0, g0 = verify_step("Chamfer1", d0, g0, dom={"distance": "1.2"})
        put(distance="0.5 + 1"); d0, g0 = verify_step("Chamfer1", d0, g0, dom={"distance": "0.5 + 1"}, defn=lambda d: d.get("distance") == "0.5 + 1")
        click_3d([0, 25, 10], "() => (document.querySelector('.feature-pick-count')?.textContent || '').includes('2 edges')")
        verify_step("Chamfer1", d0, g0, keep_open=False, defn=lambda d: "2 edges" in page.locator(".feature-pick-count").inner_text() and len(d.get("edges", [])) == 2)

        d0, g0 = start("Hole1")
        put(spec="diameter", diameter="6", depth="5", type="counterbore", cb_diameter="8", cb_depth="2.5")
        d0, g0 = verify_step("Hole1", d0, g0, dom={"spec": "diameter", "diameter": "6", "depth": "5", "type": "counterbore"},
                             defn=lambda d: d.get("hole", {}).get("cb_diameter") == "8")
        put(diameter="3 + 1", through=True)
        d0, g0 = verify_step("Hole1", d0, g0, dom={"diameter": "3 + 1", "through": True},
                             defn=lambda d: d.get("diameter") == "3 + 1" and d.get("depth") is None)
        click_3d([0, 25, 10], "() => document.querySelector('.feature-dialog select[name=\"edge1\"]')?.value === 'edge'")
        put(dist1="10")
        d0, g0 = verify_step("Hole1", d0, g0, dom={"edge1": "edge", "dist1": "10"}, defn=lambda d: len(d.get("references") or []) == 1)
        page.click(".feature-clear")
        click_3d([22, -25, 5], "() => Math.abs(Number(document.querySelector('.feature-dialog input[name=\"y\"]')?.value) + 25) < 0.2")
        put(type="simple", through=False, depth="6")
        verify_step("Hole1", d0, g0, keep_open=False,
                    defn=lambda d: abs(float(val("y")) + 25) < 0.2 and d.get("direction", [0, 0, 0])[1] > 0.9 and not d.get("references"))

        d0, g0 = start("Rect1")
        put(dir1="Y", flip1=True, spacing1="4 + 4", two=True, dir2="X", spacing2="16")
        d0, g0 = verify_step("Rect1", d0, g0, dom={"dir1": "Y", "flip1": True, "spacing1": "4 + 4", "two": True},
                             defn=lambda d: d.get("pattern", {}).get("spacing1") == "4 + 4")
        put(two=False)
        click_3d([0, -25, 10], "() => document.querySelector('.feature-dialog select[name=\"dir1\"]')?.value === 'edge'")
        verify_step("Rect1", d0, g0, dom={"two": False}, keep_open=False, defn=lambda d: abs(d.get("pattern", {}).get("dir1", [0])[0]) > 0.99)

        d0, g0 = start("Circ1")
        put(axis="Z", count="3", angle="60 + 30")
        d0, g0 = verify_step("Circ1", d0, g0, dom={"count": "3", "angle": "60 + 30"}, defn=lambda d: d.get("pattern", {}).get("angle") == "60 + 30")
        click_3d([-8, -4, 10], "() => document.querySelector('.feature-dialog select[name=\"axis\"]')?.value === 'edge'", view="top")
        verify_step("Circ1", d0, g0, dom={"axis": "edge"}, keep_open=False, defn=lambda d: (d.get("pattern", {}).get("axis_ref") or {}).get("type") == "edge")

        d0, g0 = start("Mirror1")
        put(plane="XZ")
        d0, g0 = verify_step("Mirror1", d0, g0, dom={"plane": "XZ"}, defn=lambda d: d.get("plane", {}).get("name") == "XZ")
        click_3d([-29, -12, 12.5], "() => document.querySelector('.feature-dialog select[name=\"plane\"]')?.value === 'face'")
        verify_step("Mirror1", d0, g0, dom={"plane": "face"}, keep_open=False, defn=lambda d: d.get("plane", {}).get("type") == "custom")

        d0, g0 = start("Ext1")
        put(distance="8"); d0, g0 = verify_step("Ext1", d0, g0, dom={"distance": "8"})
        put(operation="cut", distance="3 + 3")
        d0, g0 = verify_step("Ext1", d0, g0, dom={"operation": "cut", "direction": "negative", "distance": "3 + 3"},
                             defn=lambda d: d.get("extent", {}).get("distance") == "3 + 3")
        put(through=True)
        click_3d([-29, 9, 10], "() => (document.querySelector('.feature-pick-count')?.textContent || '').includes('2 of 2')", view="top")
        verify_step("Ext1", d0, g0, dom={"through": True}, keep_open=False, defn=lambda d: (
            "2 of 2" in page.locator(".feature-pick-count").inner_text()
            and d.get("extent", {}).get("through_all") is True and d.get("profiles", {}).get("type") == "all"))

        d0, g0 = start("Rev1")
        put(angle="120"); d0, g0 = verify_step("Rev1", d0, g0, dom={"angle": "120"})
        put(angle="90 + 45")
        slot("profile").click(); page.wait_for_selector('.feature-slot[data-slot="profile"].active', timeout=5000)
        click_3d([60, 0, 0], "() => (document.querySelector('.feature-slot[data-slot=\"profile\"]')?.textContent || '').includes('2 of 2')")
        slot("axis").click(); page.wait_for_selector('.feature-slot[data-slot="axis"].active', timeout=5000)
        click_3d([40, 0, 0], "() => document.querySelector('.feature-slot[data-slot=\"axis\"]')?.textContent === 'Clicked edge'")
        d0, g0 = verify_step("Rev1", d0, g0, dom={"angle": "90 + 45"}, defn=lambda d: (
            "2 of 2" in slot("profile").inner_text() and slot("axis").inner_text() == "Clicked edge"
            and d.get("profiles", {}).get("type") == "all" and d.get("axis", {}).get("type") == "model"))
        put(operation="join")
        verify_step("Rev1", d0, g0, dom={"operation": "join"}, keep_open=False, defn=lambda d: d.get("operation") == "join")
        return True, f"all {len(tested)} types ok"
    except Exception as exc:
        return False, f"error at {step}: {exc}"[:220]


step = "init"
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=shells[-1] if shells else None,
                                     args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1300, "height": 750})
        _apply_cpu_throttle(page)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("dialog", lambda d: (errors.append(f"browser dialog: {d.message}"), d.dismiss()))
        step = "initial load"
        page.goto(url)
        _wait_ready(page)
        page.click('.ribbon-tab[data-tab="inspect"]')
        box = page.locator("#viewport canvas").bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        # find the body on screen first: "zoom all" frames unused sketches too, so the part need not be in the
        # middle; then measure between two points a little apart on it
        step = "measure: find body"
        on_body = None
        for fx, fy in ((0, 0), (-0.08, -0.04), (-0.15, -0.08), (-0.2, 0), (0.08, 0.02), (-0.1, 0.1), (0.15, -0.1)):
            page.click("text=Measure")
            page.mouse.click(cx + fx * box["width"], cy + fy * box["height"])
            _wait_frame(page)
            hit = "Point" in page.locator(".measure-readout").inner_text()
            page.keyboard.press("Escape")
            page.wait_for_selector(".measure-readout", state="hidden", timeout=5000)
            if hit:
                on_body = (cx + fx * box["width"], cy + fy * box["height"])
                break
        bx, by = on_body or (cx, cy)
        step = "measure: distance"
        page.click("text=Measure")
        page.mouse.click(bx, by)
        page.wait_for_selector(".measure-readout", state="visible", timeout=5000)
        page.mouse.click(bx + 0.06 * box["width"], by + 0.02 * box["height"])
        try:
            page.wait_for_function("() => (document.querySelector('.measure-readout')?.textContent || '').includes('Distance')", timeout=5000)
        except Exception:
            pass
        measured = page.locator(".measure-readout").inner_text()
        page.screenshot(path=os.path.join(out, "measure.png"))
        step = "measure: section"
        page.click("text=Section")
        page.wait_for_function("() => (document.querySelector('.measure-readout')?.textContent || '').includes('Section')", timeout=5000)
        section = page.locator(".measure-readout").inner_text()
        page.screenshot(path=os.path.join(out, "section.png"))
        page.keyboard.press("Escape")
        page.wait_for_selector(".measure-readout", state="hidden", timeout=5000)
        closed = page.locator(".measure-readout").is_hidden()
        step = "measure: edge"
        for dx in range(0, int(box["width"] / 2), 2):
            page.click("text=Measure")
            page.mouse.click(bx + dx, by)
            _wait_frame(page)
            text = page.locator(".measure-readout").inner_text()
            page.keyboard.press("Escape")
            if any(w in text for w in ("Edge length", "Circle", "Arc")):
                edge = text
                page.click("text=Measure")
                page.mouse.click(bx + dx, by)
                page.wait_for_selector(".measure-readout", state="visible", timeout=5000)
                _wait_frame(page)
                page.screenshot(path=os.path.join(out, "measure_edge.png"))
                page.keyboard.press("Escape")
                page.wait_for_selector(".measure-readout", state="hidden", timeout=5000)
                break

        # Folder mode only (File -> New part... visible): the app's own dialog, not prompt(). Typing the name of a
        # file that exists shows the error inside the dialog; Cancel closes it. Nothing is created.
        step = "new part"
        page.click("#file-menu > summary")
        if page.locator("#btn-new-part").is_visible():
            existing = page.locator(".file-doc-item").first.get_attribute("data-value") or ""
            page.click("#btn-new-part")
            dlg = page.locator("#new-part-dialog")
            default = page.locator("#new-part-name").input_value()
            page.fill("#new-part-name", existing.removesuffix(".solidcraft"))
            page.click("#new-part-dialog .btn-submit")
            page.wait_for_selector("#new-part-error", state="visible", timeout=5000)
            err = page.locator("#new-part-error")
            shown = dlg.is_visible() and err.is_visible() and err.inner_text().strip() != ""
            page.screenshot(path=os.path.join(out, "new_part.png"))
            page.click("#new-part-dialog .btn-cancel")
            new_part = f"default {default!r}, error for {existing!r}: {shown}, closes: {dlg.is_hidden()}"
            new_part_ok = bool(default) and shown and dlg.is_hidden()
        else:
            page.keyboard.press("Escape")
            new_part_ok = True

        # Model browser inline rename (F2, type, Enter -> tree shows new name; Esc cancels; Ctrl+Z reverts)
        if page.locator("#doc-kind").inner_text().strip() == "Part":
            page.click('.ribbon-tab[data-tab="3d-model"]')
            box_row = page.locator('.tree-row[data-feature="Box1"]')
            if box_row.count() > 0:
                rename_ok = False
                # Test Esc cancels rename without changes
                step = "rename: esc"
                box_row.click()
                page.keyboard.press("F2")
                page.wait_for_selector(".tree-rename-input", timeout=5000)
                page.fill(".tree-rename-input", "DiscardMe")
                page.keyboard.press("Escape")
                page.wait_for_selector(".tree-rename-input", state="detached", timeout=5000)
                esc_cancelled = page.locator(".tree-rename-input").count() == 0 and "DiscardMe" not in page.locator("#tree-content").inner_text()

                # Test typing new name and committing with Enter
                step = "rename: enter"
                box_row.click()
                page.keyboard.press("F2")
                page.wait_for_selector(".tree-rename-input", timeout=5000)
                page.fill(".tree-rename-input", "MainBox")
                page.keyboard.press("Enter")
                page.wait_for_function(
                    "document.querySelector('#tree-content')?.textContent.includes('MainBox')"
                    " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                    timeout=10000,
                )
                # the rename's own message comes after its reload, which refreshes Undo (#156)
                page.wait_for_function("/^(Renamed |Ready$)/.test(document.getElementById('status-indicator')?.textContent || '')",
                                       timeout=15000)
                renamed_to_main = "MainBox" in page.locator("#tree-content").inner_text() and "Box1" not in page.locator("#tree-content").inner_text()

                # Ctrl+Z reverts rename
                step = "rename: ctrl+z"
                try:
                    page.wait_for_selector("#btn-undo:not([disabled])", timeout=10000)
                except Exception:
                    # what the workspace saw (#156): the history the server reports, the button, the status line
                    diag = page.evaluate("""async () => ({
                        history: await fetch('api/history').then(r => r.json()).catch(e => String(e)),
                        undo_disabled: document.getElementById('btn-undo')?.disabled,
                        undo_title: document.getElementById('btn-undo')?.title,
                        status: document.getElementById('status-indicator')?.textContent,
                    })""")
                    print("rename ctrl+z diag:", json.dumps(diag), flush=True)
                    raise
                _arm_undo_watch(page)
                page.keyboard.press("Control+z")
                page.wait_for_function(
                    "document.querySelector('#tree-content')?.textContent.includes('Box1')"
                    " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                    timeout=10000,
                )
                _wait_undo_done(page)
                reverted_rename = "Box1" in page.locator("#tree-content").inner_text() and "MainBox" not in page.locator("#tree-content").inner_text()

                rename_ok = esc_cancelled and renamed_to_main and reverted_rename
                rename_status = f"esc: {esc_cancelled}, f2 rename: {renamed_to_main}, ctrl+z: {reverted_rename}"

        # Feature dialog (parts only): Fillet opens in Properties, walking up from the centre a click picks an edge,
        # the preview shows the volume change, Esc cancels without a change; again with OK the tree gets Fillet1,
        # and Ctrl+Z takes it back, so the file ends as it started.
        if page.locator("#btn-fillet").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            fillet_ok = False
            page.click('.ribbon-tab[data-tab="3d-model"]')

            def pick_edge():
                page.click("#btn-fillet")
                page.wait_for_selector(".feature-dialog", timeout=5000)
                for px_x in (cx, bx):
                    for dy in range(0, int(box["height"] / 2) - 10, 6):
                        page.mouse.click(px_x, cy - dy)
                        _wait_frame(page)
                        if "selected" in page.locator(".feature-pick-count").inner_text():
                            break
                    if "selected" in page.locator(".feature-pick-count").inner_text():
                        break
                if "selected" not in page.locator(".feature-pick-count").inner_text():
                    return "", "no edge selected"
                page.fill('.feature-dialog input[name="radius"]', "0.5")
                # "Computing preview…" while SolidCraft works; then the volume change or an error
                page.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '')"
                                       " || !document.querySelector('.feature-error')?.hidden", timeout=30000)
                return page.locator(".feature-delta").inner_text(), page.locator(".feature-error").inner_text()

            tree_before = page.locator("#tree-content").inner_text()
            step = "fillet: preview"
            delta, err = pick_edge()
            page.screenshot(path=os.path.join(out, "fillet_preview.png"))
            step = "fillet: esc"
            page.keyboard.press("Escape")
            _wait_dialog_closed(page)
            cancelled = page.locator(".feature-dialog").count() == 0 and page.locator("#tree-content").inner_text() == tree_before
            step = "fillet: ok"
            pick_edge()
            page.click(".feature-ok")
            _wait_dialog_done(page, timeout=20000)
            page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Fillet')", timeout=10000)
            added = "Fillet" in page.locator("#tree-content").inner_text() and "Fillet" not in tree_before
            # #121: the step is named above the browser, the new row marked, the old model shown as a ghost
            step_bar = page.locator("#step-changes").inner_text() if page.locator("#step-changes").count() else ""
            step_new = page.locator('.tree-row.tree-step-new[data-type="FilletFeature"]').count() == 1
            # double-click in the model browser opens it again with its edge and radius; Esc leaves it as it is
            step = "fillet: edit"
            page.dblclick('.tree-row[data-type="FilletFeature"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            reopened = ("1 edge" in page.locator(".feature-pick-count").inner_text()
                        and page.input_value('.feature-dialog input[name="radius"]') == "0.5")
            page.keyboard.press("Escape")
            _wait_dialog_closed(page)
            step = "fillet: ctrl+z"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "t => document.querySelector('#tree-content')?.innerText === t"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                arg=tree_before,
                timeout=15000,
            )
            undone = page.locator("#tree-content").inner_text() == tree_before
            step_undo = page.locator("#step-changes").inner_text() if page.locator("#step-changes").count() else ""
            page.click("#step-changes .step-changes-toggle")
            hidden_marks = page.evaluate("document.getElementById('tree-content').classList.contains('step-marks-hidden')")
            page.click("#step-changes .step-changes-toggle")
            step_ok = ("+ Fillet1" in step_bar and step_new and "\u2212 Fillet1" in step_undo and hidden_marks)
            fillet = (f"preview {delta!r} {err!r}, esc cancels: {cancelled}, ok adds: {added}, edit reopens: {reopened}, "
                      f"ctrl+z: {undone}, last step: {step_bar!r} / {step_undo!r}, marked: {step_new}, hide: {hidden_marks}")
            fillet_ok = "Volume" in delta and not err and cancelled and added and reopened and undone and step_ok

        # #128 general command dialog: Ctrl+K, search "solid.chamfer", its form from the schema, Pick, click an edge in
        # the view, distance, OK adds the chamfer, Ctrl+Z takes it back (not in the static demo yet)
        if (page.locator("#doc-kind").inner_text().strip() == "Part"
                and page.evaluate("document.documentElement.dataset.static !== '1'")):
            command_dialog_ok = False
            tree_before_cmd = page.locator("#tree-content").inner_text()
            step = "command dialog: search"
            page.keyboard.press("Control+k")
            page.wait_for_selector(".cmd-palette:not([hidden]) .cmd-results li", timeout=60000)
            page.keyboard.type("solid.chamfer")
            page.wait_for_selector(".cmd-results li.active .cmd-id:text-is('solid.chamfer')", timeout=5000)
            page.keyboard.press("Enter")
            page.wait_for_selector(".cmd-dialog", timeout=30000)
            step = "command dialog: pick"
            edges_field = page.locator('.cmd-field[data-name="edges"]')
            edges_field.locator(".cmd-pick").click()
            page.wait_for_selector(".cmd-pick.active", timeout=5000)
            box = page.locator("#viewport canvas").bounding_box()
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            picked = ""
            for px_x in (cx, bx):
                for dy in range(0, int(box["height"] / 2) - 10, 6):
                    page.mouse.click(px_x, cy - dy)
                    _wait_frame(page)
                    picked = edges_field.locator("textarea").input_value()
                    if picked:
                        break
                if picked:
                    break
            page.locator('.cmd-field[data-name="distance"] [data-field]').fill("0.5")
            step = "command dialog: ok"
            page.click(".cmd-dialog .feature-ok")
            # done: the tree shows the chamfer; refused: the dialog stays open with its error
            page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Chamfer')"
                                   " || document.querySelector('.cmd-dialog .feature-error')?.hidden === false", timeout=30000)
            cmd_err = page.locator(".cmd-dialog .feature-error").inner_text() if page.locator(".cmd-dialog").count() else ""
            cmd_added = "Chamfer" in page.locator("#tree-content").inner_text() and "Chamfer" not in tree_before_cmd
            step = "command dialog: ctrl+z"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "t => document.querySelector('#tree-content')?.innerText === t"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                arg=tree_before_cmd, timeout=15000)
            cmd_undone = page.locator("#tree-content").inner_text() == tree_before_cmd
            command_dialog = f"picked {picked!r}, ok adds: {cmd_added} {cmd_err!r}, ctrl+z: {cmd_undone}"
            command_dialog_ok = bool(picked) and cmd_added and cmd_undone

            # a routed command (Mechvane's own handler): timeline.rename from Ctrl+K, the feature chosen from the
            # names of the open part, OK renames it (one undo step), Ctrl+Z takes it back
            step = "command dialog: routed rename"
            tree_before_rn = page.locator("#tree-content").inner_text()
            page.keyboard.press("Control+k")
            page.wait_for_selector(".cmd-palette:not([hidden]) .cmd-results li", timeout=60000)
            page.keyboard.type("timeline.rename")
            page.wait_for_selector(".cmd-results li.active .cmd-id:text-is('timeline.rename')", timeout=5000)
            page.keyboard.press("Enter")
            page.wait_for_selector(".cmd-dialog", timeout=30000)
            choice = page.locator('.cmd-field[data-name="feature"] datalist option').first.get_attribute("value")
            page.locator('.cmd-field[data-name="feature"] input').fill(choice or "")
            page.locator('.cmd-field[data-name="name"] [data-field]').fill("RoutedName")
            page.click(".cmd-dialog .feature-ok")
            page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('RoutedName')"
                                   " || document.querySelector('.cmd-dialog .feature-error')?.hidden === false", timeout=30000)
            rn_done = "RoutedName" in page.locator("#tree-content").inner_text()
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "t => document.querySelector('#tree-content')?.innerText === t"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                arg=tree_before_rn, timeout=15000)
            rn_undone = page.locator("#tree-content").inner_text() == tree_before_rn
            command_dialog += f"; routed rename of {choice!r}: {rn_done}, ctrl+z: {rn_undone}"
            command_dialog_ok = command_dialog_ok and bool(choice) and rn_done and rn_undone

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
                    _wait_frame(page)
                    if page.input_value('.feature-dialog input[name="x"]'):
                        break

            # (a) von der Mitte der Ansicht aus klicken, bis input[name="x"] gefüllt ist; OK -> Hole1 im Baum
            step = "hole: hole1"
            pick_face(0)
            added_hole1 = False
            if not page.locator(".feature-ok").is_enabled():
                x_val = page.input_value('.feature-dialog input[name="x"]')
                errors.append(f"Hole 1: OK button disabled (x={x_val!r})")
            else:
                page.click(".feature-ok")
                _wait_dialog_done(page, timeout=15000)
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Hole1')", timeout=10000)
                page.screenshot(path=os.path.join(out, "hole1.png"))
                added_hole1 = "Hole1" in page.locator("#tree-content").inner_text()

            # (b) neu, Häkchen input[name="centre"] („Middle of face“), Statuszeile enthält „Middle of the face“,
            # OK → Skizze Hole centre … im Baum
            step = "hole: centre"
            pick_face(-30)
            page.check('.feature-dialog input[name="centre"]')
            try:
                page.wait_for_function(
                    "() => (document.querySelector('.feature-pick-count')?.textContent || '').includes('Middle of the face')",
                    timeout=5000,
                )
            except Exception:
                pass
            centre_status = page.locator(".feature-pick-count").inner_text()
            has_centre_status = "Middle of the face" in centre_status
            page.screenshot(path=os.path.join(out, "hole_centre.png"))

            added_centre = False
            if not page.locator(".feature-ok").is_enabled():
                x_val = page.input_value('.feature-dialog input[name="x"]')
                errors.append(f"Hole 2: OK button disabled (x={x_val!r})")
            else:
                page.click(".feature-ok")
                _wait_dialog_done(page, timeout=15000)
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Hole centre')", timeout=10000)
                added_centre = "Hole centre" in page.locator("#tree-content").inner_text()

            # Danach Strg+Z zweimal, Datei wie vorher
            step = "hole: ctrl+z twice"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "() => !document.querySelector('#tree-content')?.textContent.includes('Hole centre')"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                timeout=15000,
            )
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            try:  # #112: the second press must not be lost while the first undo still runs
                page.wait_for_function(
                    "t => document.querySelector('#tree-content')?.innerText === t"
                    " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                    arg=tree_before_hole,
                    timeout=15000,
                )
            except Exception:
                pass
            undone_holes = page.locator("#tree-content").inner_text() == tree_before_hole
            hole = (f"hole1: {added_hole1}, centre status: {has_centre_status}, centre sketch: {added_centre}, "
                    f"ctrl+z twice: {undone_holes}")
            hole_ok = added_hole1 and has_centre_status and added_centre and undone_holes

        # Extrusion mit Profilwahl: Teil mit zwei getrennten Kreisen (r 10 und r 5), Profil 2 wählen (+785 mm³),
        # OK -> Extrude1, Doppelklick öffnet Dialog mit Profil-Wert 1, Esc, Ctrl+Z
        if page.locator("#btn-extrude").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            extrude_ok = False
            step = "extrude: open"
            page.click('.ribbon-tab[data-tab="3d-model"]')
            tree_before_extrude = page.locator("#tree-content").inner_text()
            page.click("#btn-extrude")
            page.wait_for_selector(".feature-dialog", timeout=5000)

            # Profile werden in der Ansicht angeklickt: bei zwei Profilen ist zuerst keins gewählt (OK gesperrt);
            # die Ansicht absuchen, bis ein Klick genau eins wählt (r 10: +3141 mm³, r 5: +785 mm³)
            step = "extrude: pick profile"
            count = lambda: page.locator(".feature-pick-count").inner_text()
            profiles_prompt = "Click the profiles" in count() and not page.locator(".feature-ok").is_enabled()
            box = page.locator("#viewport canvas").bounding_box()
            picked_one = False
            for fx in (0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55):
                for fy in (0.5, 0.45, 0.55, 0.4, 0.6, 0.65):
                    page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy)
                    _wait_frame(page)
                    if "1 of 2" in count():
                        picked_one = True
                        break
                if picked_one:
                    break
            page.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '')"
                                   " || !document.querySelector('.feature-error')?.hidden", timeout=30000)
            extrude_delta = page.locator(".feature-delta").inner_text()
            page.screenshot(path=os.path.join(out, "extrude_profile_preview.png"))
            m = re.search(r"Volume\s*\+\s*([0-9.]+)", extrude_delta)
            one_vol = float(m.group(1)) if m else 0.0
            vol_785 = picked_one and (abs(one_vol - 785.4) < 1.5 or abs(one_vol - 3141.6) < 1.5)
            profiles_three = profiles_prompt

            # OK
            step = "extrude: ok"
            added_extrude = False
            if not page.locator(".feature-ok").is_enabled():
                errors.append("Extrude: OK button disabled")
            else:
                page.click(".feature-ok")
                _wait_dialog_done(page, timeout=15000)
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Extrude1')", timeout=10000)
                added_extrude = "Extrude1" in page.locator("#tree-content").inner_text()

            # Doppelklick auf Extrude1 im Baum öffnet den Dialog mit Profil-Wert 1, Esc
            step = "extrude: edit"
            page.dblclick('.tree-row[data-type="ExtrudeFeature"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            # the stored single profile comes back as the one picked
            try:
                page.wait_for_function(
                    "() => (document.querySelector('.feature-pick-count')?.textContent || '').includes('1 of 2')"
                    " && document.getElementById('status-indicator')?.textContent === 'Ready'",
                    timeout=10000,
                )
            except Exception:
                pass
            reopened_ok = "1 of 2" in count()
            page.keyboard.press("Escape")
            _wait_dialog_closed(page)

            # Löschen fragt nach verbrauchter Skizze (Issue #66):
            # Extrude1 anwählen, Entf drücken -> Dialog öffnet sich mit Häkchen vorausgewählt;
            # Häkchen entfernen und Löschen bestätigen -> Extrude1 weg, Sketch1 bleibt als ungenutzte Skizze im Baum;
            # Strg+Z holt Extrude1 zurück.
            step = "extrude: delete"
            page.click('.tree-row[data-feature="Extrude1"]')
            page.keyboard.press("Delete")
            page.wait_for_selector("#delete-feature-dialog[open]", timeout=5000)
            chk = page.locator("#delete-consumed-sketch")
            chk_default = chk.is_checked()
            chk.uncheck()
            page.click("#delete-feature-submit")
            page.wait_for_function("!document.getElementById('delete-feature-dialog')?.open", timeout=5000)
            page.wait_for_function(
                "!document.querySelector('#tree-content')?.textContent.includes('Extrude1')"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                timeout=10000,
            )
            tree_text_deleted = page.locator("#tree-content").inner_text()
            delete_keeps_sketch = ("Extrude1" not in tree_text_deleted and "Sketch1" in tree_text_deleted)

            # Strg+Z holt Extrude1 zurück
            step = "extrude: undo delete"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "document.querySelector('#tree-content')?.textContent.includes('Extrude1')"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                timeout=10000,
            )
            undo_delete_ok = "Extrude1" in page.locator("#tree-content").inner_text()

            # Weiteres Strg+Z, Datei wie vorher
            step = "extrude: ctrl+z"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            try:
                page.wait_for_function(
                    "t => document.querySelector('#tree-content')?.innerText === t"
                    " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                    arg=tree_before_extrude,
                    timeout=15000,
                )
            except Exception:
                pass
            undone_extrude = page.locator("#tree-content").inner_text() == tree_before_extrude
            extrude = (f"pick prompt: {profiles_three}, one picked: {picked_one}, delta: {extrude_delta!r} (one profile: {vol_785}), "
                       f"ok adds: {added_extrude}, edit keeps it: {reopened_ok}, delete chk: {chk_default}, "
                       f"delete keeps sketch: {delete_keeps_sketch}, undo delete: {undo_delete_ok}, ctrl+z: {undone_extrude}")
            extrude_ok = (profiles_three and vol_785 and added_extrude and reopened_ok and chk_default
                          and delete_keeps_sketch and undo_delete_ok and undone_extrude)

        # Revolve mit Profil- und Achsenwahl per Klick in der Ansicht (Issue #59):
        # Zwei Auswahlfelder Profile und Axis; erst ein Profil anklicken, mit Tab auf Axis wechseln,
        # dann die Konstruktionslinie l1 (bei x=120 zwischen den beiden Kreisen) in der Ansicht anklicken,
        # Vorschau prüfen, OK -> Revolve1, Doppelklick zeigt Profil und Achse wieder, Esc, Ctrl+Z
        if page.locator("#btn-revolve").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            revolve_ok = False
            step = "revolve: open"
            page.click('.ribbon-tab[data-tab="3d-model"]')
            tree_before_revolve = page.locator("#tree-content").inner_text()
            # Shortcut 'r' outside sketcher opens Revolve dialog (Issue #64)
            page.keyboard.press("r")
            page.wait_for_selector(".feature-dialog", timeout=5000)
            rev_shortcut_ok = "Revolve" in page.locator(".feature-dialog-title").inner_text()

            count = lambda: page.locator(".feature-pick-count").inner_text()
            prof_slot = page.locator('.feature-slot[data-slot="profile"]')
            axis_slot = page.locator('.feature-slot[data-slot="axis"]')
            slots_initial = (prof_slot.inner_text() == "Click in view" and axis_slot.inner_text() == "Click in view"
                             and "active" in (prof_slot.get_attribute("class") or "")
                             and not page.locator(".feature-ok").is_enabled())

            step = "revolve: pick profile"
            box = page.locator("#viewport canvas").bounding_box()
            rev_prof_picked = False
            for fx in (0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55):
                for fy in (0.5, 0.45, 0.55, 0.4, 0.6, 0.65):
                    page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy)
                    _wait_frame(page)
                    if "1 of 2" in prof_slot.inner_text():
                        rev_prof_picked = True
                        break
                if rev_prof_picked:
                    break

            # Tab switches the active selection field from Profile to Axis
            step = "revolve: tab to axis"
            page.keyboard.press("Tab")
            try:
                page.wait_for_function(
                    "() => document.querySelector('.feature-slot[data-slot=\"axis\"]')?.classList.contains('active')",
                    timeout=5000,
                )
            except Exception:
                pass
            tab_switched = "active" in (axis_slot.get_attribute("class") or "")

            # Click the Z origin axis in the view -> "Z axis"
            step = "revolve: pick Z axis"
            origin_axis_picked = False
            for fx in [x / 100.0 for x in range(30, 44)]:
                page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * 0.33)
                _wait_frame(page)
                if axis_slot.inner_text() == "Z axis":
                    origin_axis_picked = True
                    break

            # Click a model edge in the view -> "Clicked edge"
            step = "revolve: pick edge axis"
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            edge_axis_picked = False
            for dy in range(0, int(box["height"] / 2) - 10, 6):
                page.mouse.click(cx, cy - dy)
                _wait_frame(page)
                if axis_slot.inner_text() == "Clicked edge":
                    edge_axis_picked = True
                    break

            # Then click the sketch line l1 (at x=120 between the two circles) in the view -> "Sketch line l1"
            step = "revolve: pick sketch axis"
            rev_axis_picked = False
            axis_at = None
            for fx in (0.67, 0.65, 0.69, 0.63, 0.71, 0.66, 0.68):
                for fy in (0.64, 0.62, 0.66, 0.60, 0.68, 0.65, 0.63):
                    page.mouse.click(box["x"] + box["width"] * fx, box["y"] + box["height"] * fy)
                    _wait_frame(page)
                    if axis_slot.inner_text() == "Sketch line l1":
                        rev_axis_picked = True
                        axis_at = (box["x"] + box["width"] * fx, box["y"] + box["height"] * fy)
                        break
                if rev_axis_picked:
                    break

            # Hover feedback (#133): over the sketch line the pointer is a hand, over empty space an arrow again
            step = "revolve: hover cursor"
            hover_cursor_ok = False
            hover_cursor_got = None
            if axis_at:
                cursor_js = "getComputedStyle(document.querySelector('#viewport canvas')).cursor"
                page.mouse.move(box["x"] + 5, box["y"] + 5)
                _wait_frame(page)
                page.mouse.move(*axis_at)
                _wait_frame(page)
                _wait_frame(page)
                on_line = page.evaluate(cursor_js)
                page.mouse.move(box["x"] + 5, box["y"] + 5)
                _wait_frame(page)
                _wait_frame(page)
                off_line = page.evaluate(cursor_js)
                hover_cursor_got = (on_line, off_line)
                hover_cursor_ok = on_line == "pointer" and off_line != "pointer"
            if not hover_cursor_ok:
                errors.append(f"Revolve: hover over the sketch line does not show a pointer cursor: {hover_cursor_got}")

            picked_axis_label = axis_slot.inner_text()
            page.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '')"
                                   " || !document.querySelector('.feature-error')?.hidden", timeout=30000)
            revolve_delta = page.locator(".feature-delta").inner_text()
            page.screenshot(path=os.path.join(out, "revolve_preview.png"))
            m_rev = re.search(r"Volume\s*\+\s*([0-9.]+)", revolve_delta)
            rev_vol = float(m_rev.group(1)) if m_rev else 0.0
            rev_vol_ok = rev_prof_picked and origin_axis_picked and edge_axis_picked and rev_axis_picked and rev_vol > 1000.0

            step = "revolve: ok"
            added_revolve = False
            if not page.locator(".feature-ok").is_enabled():
                errors.append("Revolve: OK button disabled")
            else:
                page.click(".feature-ok")
                _wait_dialog_done(page, timeout=15000)
                page.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Revolve1')", timeout=10000)
                added_revolve = "Revolve1" in page.locator("#tree-content").inner_text()

            # Doppelklick auf Revolve1 im Baum zeigt Profil und Achse wieder
            step = "revolve: edit"
            page.dblclick('.tree-row[data-type="RevolveFeature"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            try:
                page.wait_for_function(
                    "([p, a]) => (document.querySelector('.feature-slot[data-slot=\"profile\"]')?.textContent || '').includes(p)"
                    " && (document.querySelector('.feature-slot[data-slot=\"axis\"]')?.textContent || '') === a"
                    " && document.getElementById('status-indicator')?.textContent === 'Ready'",
                    arg=["1 of 2", picked_axis_label],
                    timeout=10000,
                )
            except Exception:
                pass
            rev_edit_ok = ("1 of 2" in prof_slot.inner_text() and axis_slot.inner_text() == picked_axis_label)
            page.keyboard.press("Escape")
            _wait_dialog_closed(page)

            step = "revolve: ctrl+z"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            _arm_undo_watch(page)
            page.keyboard.press("Control+z")
            try:
                page.wait_for_function(
                    "t => document.querySelector('#tree-content')?.innerText === t"
                    " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                    arg=tree_before_revolve,
                    timeout=15000,
                )
            except Exception:
                pass
            # the undo is done only when the workspace says so (after its reload) and the server is no longer busy:
            # a sketch begun while it still runs loses its first line (#156)
            _wait_undo_done(page)
            undone_revolve = page.locator("#tree-content").inner_text() == tree_before_revolve
            revolve = (f"shortcut r: {rev_shortcut_ok}, slots: {slots_initial}, prof: {rev_prof_picked}, tab: {tab_switched}, "
                       f"origin axis: {origin_axis_picked}, edge axis: {edge_axis_picked}, "
                       f"sketch axis: {picked_axis_label!r}, delta: {revolve_delta!r}, "
                       f"ok: {added_revolve}, edit restores both: {rev_edit_ok}, ctrl+z: {undone_revolve}")
            revolve_ok = (rev_shortcut_ok and slots_initial and rev_prof_picked and tab_switched and origin_axis_picked
                          and edge_axis_picked and rev_axis_picked and rev_vol_ok and added_revolve
                          and rev_edit_ok and undone_revolve)

        # Sketch environment (sketcher.js): S, plane XY, a line with a typed length (40, a dimension), a rectangle,
        # a circle, Ctrl+Z takes the circle back, Enter finishes; the tree gets a sketch, Ctrl+Z removes it again
        if page.locator("#btn-sketch").is_enabled() and page.locator("#doc-kind").inner_text().strip() == "Part":
            sketch_ok = False
            step = "sketch: enter XY"
            state = lambda: page.evaluate("fetch('api/sketch/state').then(r => r.json())")
            page.click('.ribbon-tab[data-tab="3d-model"]')
            tree_before_sketch = page.locator("#tree-content").inner_text()
            page.keyboard.press("s")
            page.wait_for_selector(".sketch-plane-bar [data-plane=XY]", timeout=5000)
            page.click(".sketch-plane-bar [data-plane=XY]")
            page.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=10000)
            box = page.locator("#viewport canvas").bounding_box()
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            w = box["width"]
            step = "sketch: line 40"
            page.keyboard.press("l")
            page.mouse.click(cx - 0.15 * w, cy + 0.1 * w)
            page.mouse.move(cx - 0.05 * w, cy + 0.1 * w)
            hud_shown = page.locator(".sketch-hud").is_visible()
            page.keyboard.type("40")
            page.keyboard.press("Enter")
            try:
                page.wait_for_selector(".sketch-dim:has-text('40')", timeout=10000)
            except Exception:
                # what the sketcher saw (#156): tab, status line, HUD, focus, curves on the server
                diag = page.evaluate("""async () => ({
                    tab: document.querySelector('.ribbon-tab.active')?.dataset.tab,
                    status: document.getElementById('status-indicator')?.textContent,
                    statusline: document.getElementById('statusbar')?.textContent?.replace(/\\s+/g, ' ').slice(0, 300),
                    sketching: document.body.classList.contains('sketching'),
                    hud: !!document.querySelector('.sketch-hud'), hud_hidden: document.querySelector('.sketch-hud')?.hidden,
                    hud_values: [...document.querySelectorAll('.sketch-hud input')].map(i => i.value),
                    focus: document.activeElement?.tagName + '.' + (document.activeElement?.className || ''),
                    dialog: !!document.querySelector('dialog[open]'),
                    dims: [...document.querySelectorAll('.sketch-dim')].map(d => d.textContent),
                    curves: await fetch('api/sketch/state').then(r => r.json()).then(j => (j.state?.curves || []).length).catch(e => String(e)),
                })""")
                print("sketch line 40 diag:", json.dumps(diag), "hud shown after first click:", hud_shown, flush=True)
                page.screenshot(path=os.path.join(out, "sketch_line40_fail.png"))
                raise
            page.keyboard.press("Escape")
            step = "sketch: rectangle"
            page.keyboard.press("r")
            page.mouse.click(cx + 0.02 * w, cy - 0.05 * w)
            page.mouse.click(cx + 0.1 * w, cy - 0.1 * w)
            page.wait_for_function("() => document.querySelectorAll('.sketch-glyph').length >= 4", timeout=10000)
            step = "sketch: circle"
            page.keyboard.press("c")
            page.mouse.click(cx + 0.08 * w, cy + 0.08 * w)
            page.mouse.click(cx + 0.11 * w, cy + 0.08 * w)
            page.wait_for_function(
                "() => fetch('api/sketch/state').then(r => r.json()).then(d => Boolean(d.state?.curves?.some(c => c.type === 'circle')))",
                timeout=10000,
            )
            # Dimension: the typed length shows as "40" on the line; double-click it and change it to 45
            step = "sketch: edit dim"
            page.keyboard.press("Escape")
            page.wait_for_function("!document.querySelector('.sketch-dims.tool-active')", timeout=5000)
            label_40 = page.locator(".sketch-dim", has_text="40")
            dim_label = label_40.count() == 1
            if dim_label:
                label_40.first.dblclick()
                page.wait_for_selector(".sketch-dim-edit", timeout=5000)
                page.keyboard.press("Control+a")
                page.keyboard.type("45")
                page.keyboard.press("Enter")
                page.wait_for_selector(".sketch-dim:has-text('45')", timeout=10000)
            st = state()["state"]
            kinds = sorted(c["type"] for c in st["curves"])
            lengths = [c.get("value") for c in st["constraints"] if c.get("type") == "length"]
            page.screenshot(path=os.path.join(out, "sketch.png"))
            page.keyboard.press("Escape")
            # Ctrl+Z goes back one command: first the changed dimension (45 -> 40), then the circle
            step = "sketch: undo dim & circle"
            page.keyboard.press("Control+z")
            page.wait_for_selector(".sketch-dim:has-text('40')", timeout=10000)
            back_to_40 = 40 in [c.get("value") for c in state()["state"]["constraints"] if c.get("type") == "length"]
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "() => fetch('api/sketch/state').then(r => r.json()).then(d => !d.state?.curves?.some(c => c.type === 'circle'))",
                timeout=10000,
            )
            undone_circle = back_to_40 and "circle" not in [c["type"] for c in state()["state"]["curves"]]
            # Constraints show as symbols (the rectangle's H and V); click one H, Delete removes that constraint
            step = "sketch: delete constraint"
            page.keyboard.press("Escape")
            n_hv = lambda: sum(c["type"] in ("horizontal", "vertical") for c in state()["state"]["constraints"])
            hv_before = n_hv()
            glyph_h = page.locator(".sketch-glyph", has_text="H")
            h_before = glyph_h.count()
            glyphs_shown = h_before >= 2
            if glyphs_shown:
                glyph_h.first.click()
                page.keyboard.press("Delete")
                page.wait_for_function(
                    f"() => Array.from(document.querySelectorAll('.sketch-glyph')).filter(e => e.textContent === 'H').length < {h_before}",
                    timeout=10000,
                )
            glyph_deleted = glyphs_shown and n_hv() == hv_before - 1
            step = "sketch: finish"
            page.keyboard.press("Enter")
            page.wait_for_function("document.querySelector('.ribbon-tab[data-tab=\"3d-model\"]').classList.contains('active')",
                                   timeout=10000)
            page.wait_for_function(
                "t => !document.body.classList.contains('sketching') && document.querySelector('#tree-content')?.innerText !== t"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                arg=tree_before_sketch,
                timeout=15000,
            )
            closed_sketch = not state().get("active")
            added_sketch = page.locator("#tree-content").inner_text() != tree_before_sketch
            step = "sketch: undo sketch"
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "t => document.querySelector('#tree-content')?.innerText === t"
                " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                arg=tree_before_sketch,
                timeout=15000,
            )
            undone_sketch = page.locator("#tree-content").inner_text() == tree_before_sketch
            # XZ as in Inventor's front view: sketch x along world +X, y along world +Z (Z up on screen)
            step = "sketch: XZ plane"
            page.keyboard.press("s")
            page.wait_for_selector(".sketch-plane-bar [data-plane=XZ]", timeout=5000)
            page.click(".sketch-plane-bar [data-plane=XZ]")
            page.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=10000)
            xz = state()["state"].get("plane") or {}
            xz_up = ([round(v) for v in xz.get("x_dir", [])] == [1, 0, 0]
                     and [round(v) for v in xz.get("y_dir", [])] == [0, 0, 1])
            page.click('[data-sketch-action="cancel"]')
            _wait_sketch_idle(page)
            undone_sketch = undone_sketch and page.locator("#tree-content").inner_text() == tree_before_sketch

            # Create 2D Sketch: planar face hover and selection on the part face (issue #61)
            step = "sketch: face hover"
            page.keyboard.press("s")
            page.wait_for_selector(".sketch-plane-bar", timeout=5000)
            face_hover_ok = False
            for dx in (-100, -80, -60, -40, -120, -140):
                for dy in (0, -20, 20, -40, 40):
                    page.mouse.move(cx + dx, cy + dy)
                    page.wait_for_timeout(60)
                    if page.evaluate("() => { const g = window.__scene?.children?.find(c => c.renderOrder === 9); return Boolean(g && g.children.length > 0); }"):
                        face_hover_ok = True
                        page.screenshot(path=os.path.join(out, "face_hover.png"))
                        page.mouse.click(cx + dx, cy + dy)
                        break
                if face_hover_ok:
                    break
            page.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=10000)
            face_sketch_active = bool(state().get("active"))
            page.click('[data-sketch-action="cancel"]')
            _wait_sketch_idle(page)

            # Ribbon tabs overflow check: tabs must not overflow vertically or have scrollbars (issue #61)
            ribbon_tabs_ok = page.evaluate("() => { const el = document.querySelector('.ribbon-tabs'); return window.getComputedStyle(el).overflowX === 'visible'; }")

            sketch = (f"XZ z up: {xz_up}, face hover: {face_hover_ok}, face sketch: {face_sketch_active}, ribbon tabs: {ribbon_tabs_ok}, "
                      f"hud: {hud_shown}, curves: {kinds}, label 40: {dim_label}, length after edit: {lengths}, "
                      f"ctrl+z circle: {undone_circle}, delete H symbol: {glyph_deleted}, "
                      f"finished: {closed_sketch and added_sketch}, ctrl+z sketch: {undone_sketch}")
            sketch_ok = (hud_shown and kinds.count("line") == 5 and kinds.count("circle") == 1 and dim_label and 45 in lengths
                         and undone_circle and glyph_deleted and closed_sketch and added_sketch and undone_sketch and xz_up
                         and face_hover_ok and face_sketch_active and ribbon_tabs_ok)

        # Model browser visibility (issue #65):
        # Click eye on Sketch1 -> sketch disappears from view, entry dimmed; key V switches it back.
        visibility_ok = False
        visibility = "not tested"
        step = "visibility"
        try:
            sketch_row = page.locator('.tree-row[data-feature="Sketch1"]')
            sketch_row.wait_for(timeout=10000)
            sketch_eye = sketch_row.locator(".tree-eye")

            # 1. Sketch1 is initially visible in 3D overlay and row is not dimmed
            page.wait_for_function(
                "() => { const g = window.__scene?.children?.find(c => c.renderOrder === 8); "
                "return Boolean(g && g.children.some(ch => ch.userData?.sketch === 'Sketch1')); }",
                timeout=10000
            )
            init_visible = not sketch_row.evaluate("el => el.classList.contains('tree-hidden')")

            # 2. Click eye on Sketch1 -> Sketch1 removed from overlay, row is dimmed (.tree-hidden)
            sketch_eye.click()
            page.wait_for_function(
                "() => { const g = window.__scene?.children?.find(c => c.renderOrder === 8); "
                "return Boolean(g && !g.children.some(ch => ch.userData?.sketch === 'Sketch1')); }",
                timeout=10000
            )
            page.wait_for_function(
                "() => document.querySelector('.tree-row[data-feature=\"Sketch1\"]').classList.contains('tree-hidden')",
                timeout=10000
            )
            eye_hidden = sketch_row.evaluate("el => el.classList.contains('tree-hidden')")

            # 3. Select Sketch1 row, press V -> Sketch1 returns to overlay, tree-hidden removed
            sketch_row.click()
            page.keyboard.press("v")
            page.wait_for_function(
                "() => { const g = window.__scene?.children?.find(c => c.renderOrder === 8); "
                "return Boolean(g && g.children.some(ch => ch.userData?.sketch === 'Sketch1')); }",
                timeout=10000
            )
            page.wait_for_function(
                "() => !document.querySelector('.tree-row[data-feature=\"Sketch1\"]').classList.contains('tree-hidden')",
                timeout=10000
            )
            v_restored = not sketch_row.evaluate("el => el.classList.contains('tree-hidden')")

            # 4. Also check body visibility (Body1 in Solid Bodies)
            body_row = page.locator('.tree-row[data-body="Body1"]')
            body_row.wait_for(timeout=10000)
            body_eye = body_row.locator(".tree-eye")
            body_eye.click()
            page.wait_for_function(
                "() => { const mg = window.__scene?.children?.find(c => c.children?.some(ch => ch.userData?.bodyName === 'Body1')); "
                "const b = mg?.children?.find(ch => ch.userData?.bodyName === 'Body1'); return b && b.visible === false; }",
                timeout=10000
            )
            body_hidden = body_row.evaluate("el => el.classList.contains('tree-hidden')")

            body_row.click()
            page.keyboard.press("v")
            page.wait_for_function(
                "() => { const mg = window.__scene?.children?.find(c => c.children?.some(ch => ch.userData?.bodyName === 'Body1')); "
                "const b = mg?.children?.find(ch => ch.userData?.bodyName === 'Body1'); return b && b.visible === true; }",
                timeout=10000
            )
            body_restored = not body_row.evaluate("el => el.classList.contains('tree-hidden')")

            visibility = (f"init: {init_visible}, eye hide: {eye_hidden}, v restore: {v_restored}, "
                          f"body hide: {body_hidden}, body restore: {body_restored}")
            visibility_ok = init_visible and eye_hidden and v_restored and body_hidden and body_restored
        except Exception as e:
            visibility = f"error: {e}"

        # Folder mode (mechvane ui <folder>, as the Start-menu shortcut starts it): the document opens and its
        # tree loads. 0.1.0a18 broke here on a renamed menu label while every file-mode check above passed.
        if tmp_dir:
            folder_ok = False
            open_folder_ok = False
            import_browse_ok = False
            from mechvane.ui.server import create_server as _cs
            fsrv = _cs(tmp_dir.name, port=port + 1)
            threading.Thread(target=fsrv.serve_forever, daemon=True).start()
            try:
                fpage = browser.new_page(viewport={"width": 1300, "height": 750})
                _apply_cpu_throttle(fpage)
                fpage.on("pageerror", lambda e: errors.append(f"folder mode: {e}"))
                step = "folder: initial load"
                fpage.goto(f"http://{host}:{port + 1}/")
                _wait_ready(fpage, timeout=60000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('End of Part')",
                                        timeout=60000)
                folder_mode = "tree loaded"
                folder_ok = True

                # Test File -> Open folder... dialog
                step = "folder: open folder dialog"
                fpage.click("#file-menu summary")
                fpage.wait_for_selector("#btn-open-folder", timeout=5000)
                fpage.click("#btn-open-folder")
                fpage.wait_for_selector("#folder-dialog[open]", timeout=5000)
                folder_dialog_title = fpage.locator("#folder-dialog-title").inner_text()
                has_nav = fpage.locator("#folder-roots-select").count() > 0 and fpage.locator("#folder-path-input").count() > 0
                has_items = fpage.locator("#folder-items-list").count() > 0
                fpage.keyboard.press("Escape")
                fpage.wait_for_function("!document.getElementById('folder-dialog')?.open", timeout=5000)
                open_folder = f"title: '{folder_dialog_title}', nav: {has_nav}, items: {has_items}, closed: True"
                open_folder_ok = ("Open folder" in folder_dialog_title and has_nav and has_items)

                # Test File -> Import STEP... dialog with Browse...
                step = "folder: import step browse"
                fpage.click("#file-menu summary")
                fpage.wait_for_selector("#btn-import-step", timeout=5000)
                fpage.click("#btn-import-step")
                fpage.wait_for_selector("#import-step-dialog[open]", timeout=5000)
                fpage.wait_for_selector("#import-step-browse", timeout=5000)
                fpage.click("#import-step-browse")
                fpage.wait_for_selector("#folder-dialog[open]", timeout=5000)
                step_dialog_title = fpage.locator("#folder-dialog-title").inner_text()
                files_visible = fpage.locator("#folder-files-container").is_visible()
                fpage.keyboard.press("Escape")
                # When browse dialog closes, import-step dialog reopens
                fpage.wait_for_selector("#import-step-dialog[open]", timeout=5000)
                fpage.keyboard.press("Escape")
                fpage.wait_for_function("!document.getElementById('import-step-dialog')?.open", timeout=5000)
                import_browse = f"browse title: '{step_dialog_title}', files container: {files_visible}, closed: True"
                import_browse_ok = ("Select STEP file" in step_dialog_title and files_visible)

                # Assemble tab check: disabled in a part ("Open an assembly"), enabled in an assembly
                step = "assemble: part disabled"
                fpage.click('.ribbon-tab[data-tab="assemble"]')
                part_place_disabled = fpage.locator("#btn-place").is_disabled()
                part_place_title = fpage.locator("#btn-place").get_attribute("title") or ""
                part_joint_disabled = fpage.locator("#btn-joint").is_disabled()
                part_joint_title = fpage.locator("#btn-joint").get_attribute("title") or ""
                part_constrain_disabled = fpage.locator("#btn-constrain").is_disabled()
                part_std_disabled = fpage.locator("#btn-place-standard").is_disabled()
                part_bolted_disabled = fpage.locator("#btn-bolted-connection").is_disabled()
                part_bolted_title = fpage.locator("#btn-bolted-connection").get_attribute("title") or ""
                part_upd_disabled = fpage.locator("#btn-update-links").is_disabled()
                part_upd_title = fpage.locator("#btn-update-links").get_attribute("title") or ""

                from mechvane.documents import Workspace as _Ws, ASSEMBLY as _ASM, PART as _PART
                _aws = _Ws(tmp_dir.name)
                try:
                    _top = _aws.new(_PART, "smoke_top")
                    _top.session.cmd("solid.box", {"length": 80, "width": 50, "height": 15, "corner": [-40, -25, 0],
                                                   "body_name": "Body1", "name": "Box1"})
                    _top.save()
                    _asm = _aws.new(_ASM, "smoke_asm")
                    _asm.save()
                finally:
                    _aws.close_all()
                step = "assemble: open smoke_asm"
                fpage.evaluate("""() => fetch('api/open/smoke_asm.solidcraft', {
                  method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'
                })""")
                fpage.reload()
                fpage.wait_for_function(
                    "document.querySelector('#doc-kind')?.textContent === 'Assembly'"
                    " && document.getElementById('status-indicator')?.textContent === 'Ready'",
                    timeout=20000,
                )
                fpage.click('.ribbon-tab[data-tab="assemble"]')
                asm_place_enabled = not fpage.locator("#btn-place").is_disabled()
                asm_joint_enabled = not fpage.locator("#btn-joint").is_disabled()
                asm_constrain_enabled = not fpage.locator("#btn-constrain").is_disabled()
                asm_std_enabled = not fpage.locator("#btn-place-standard").is_disabled()
                asm_bolted_enabled = not fpage.locator("#btn-bolted-connection").is_disabled()
                asm_upd_enabled = not fpage.locator("#btn-update-links").is_disabled()
                step = "assemble: place 1"
                fpage.click("#btn-place")
                fpage.wait_for_selector(".feature-dialog select[name='file']", timeout=5000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('smoke_part')", timeout=20000)

                # With only 1 component placed, Joint dialog disables OK and asks for at least two components
                step = "assemble: single comp joint"
                fpage.click("#btn-joint")
                fpage.wait_for_selector(".feature-dialog select[name='type']", timeout=5000)
                single_comp_ok_disabled = fpage.locator(".feature-ok").is_disabled()
                single_comp_status = fpage.locator(".feature-pick-count").inner_text()
                fpage.click(".feature-cancel")
                _wait_dialog_closed(fpage)

                # Place a second instance (tx=120) and third instance (tx=240)
                step = "assemble: place 2 & 3"
                fpage.click("#btn-place")
                fpage.wait_for_selector(".feature-dialog input[name='tx']", timeout=5000)
                fpage.fill(".feature-dialog input[name='tx']", "120")
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('smoke_part:2')", timeout=20000)

                fpage.click("#btn-place")
                fpage.wait_for_selector(".feature-dialog input[name='tx']", timeout=5000)
                fpage.fill(".feature-dialog input[name='tx']", "240")
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('smoke_part:3')", timeout=20000)

                # Switch to top view so smoke_part:1 (left), smoke_part:2 (center), smoke_part:3 (right) sit along y=cy
                step = "assemble: joint pick & create"
                fpage.evaluate("() => document.querySelector('[data-view=\"top\"]')?.click()")
                fpage.wait_for_function("() => Math.abs((window.__camera?.up?.y ?? 0) - 1) < 1e-4", timeout=5000)
                _wait_frame(fpage)
                fbox = fpage.locator("#viewport canvas").bounding_box()
                fcx = fbox["x"] + fbox["width"] / 2
                fcy = fbox["y"] + fbox["height"] / 2

                def _click_part_face(dx_candidates):
                    for dx in dx_candidates:
                        for dy in (0, -15, 15, -30, 30):
                            fpage.mouse.move(fcx + dx, fcy + dy)
                            fpage.wait_for_timeout(40)
                            hovered = fpage.evaluate(
                                "() => { const g = window.__scene?.children?.find(c => c.renderOrder === 9); "
                                "return Boolean(g && g.children.length > 0); }"
                            )
                            if hovered:
                                fpage.mouse.click(fcx + dx, fcy + dy)
                                return True
                    return False

                fpage.click("#btn-joint")
                fpage.wait_for_selector(".feature-dialog select[name='type']", timeout=5000)
                joint_types = fpage.eval_on_selector_all(
                    ".feature-dialog select[name='type'] option",
                    "els => els.map(e => e.value)",
                )
                fpage.select_option(".feature-dialog select[name='type']", "revolute")

                # Pick 3D face of smoke_part:1 (left) and smoke_part:2 (center) on the viewport canvas
                picked_face_1 = _click_part_face((-180, -160, -140, -120, -100, -200, -220))
                slot_a_text = fpage.locator('.feature-slot[data-slot="origin_a"]').inner_text()
                picked_face_2 = _click_part_face((0, -20, 20, -40, 40))
                slot_b_text = fpage.locator('.feature-slot[data-slot="origin_b"]').inner_text()
                face_pick_ok = (
                    picked_face_1 and picked_face_2
                    and slot_a_text.startswith("smoke_part:1 · ")
                    and slot_b_text.startswith("smoke_part:2 · ")
                )

                # Selecting the same component on both sides disables OK
                fpage.select_option(".feature-dialog select[name='comp_b']", "smoke_part:1")
                _click_part_face((-180, -160, -140, -120, -100, -200, -220))
                same_comp_disabled = fpage.locator(".feature-ok").is_disabled()

                # Re-select smoke_part:2 and pick its 3D face again
                fpage.select_option(".feature-dialog select[name='comp_b']", "smoke_part:2")
                _click_part_face((0, -20, 20, -40, 40))
                fpage.wait_for_selector(".feature-ok:not([disabled])", timeout=5000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Revolute1')", timeout=20000)

                # Edit mode: double-click Revolute1 in tree, verify prefilled components, switch comp_b to smoke_part:3
                step = "assemble: joint edit"
                fpage.locator('.tree-row[data-joint="Revolute1"]').first.dblclick()
                fpage.wait_for_selector(".feature-dialog select[name='comp_a']", timeout=5000)
                edit_comp_a = fpage.locator(".feature-dialog select[name='comp_a']").input_value()
                edit_comp_b = fpage.locator(".feature-dialog select[name='comp_b']").input_value()
                fpage.select_option(".feature-dialog select[name='comp_b']", "smoke_part:3")
                edit_switch_disabled = fpage.locator(".feature-ok").is_disabled()
                picked_face_3 = _click_part_face((140, 160, 180, 120, 200, 100, 220))
                slot_b3_text = fpage.locator('.feature-slot[data-slot="origin_b"]').inner_text()
                fpage.wait_for_selector(".feature-ok:not([disabled])", timeout=5000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)

                # Rename joint in the browser tree via F2 inline rename (after loadAll completed above)
                step = "assemble: joint rename"
                fpage.wait_for_selector('.tree-row[data-joint="Revolute1"]', timeout=20000)
                fpage.locator('.tree-row[data-joint="Revolute1"]').first.click()
                fpage.keyboard.press("F2")
                fpage.wait_for_selector(".tree-rename-input", timeout=5000)
                fpage.fill(".tree-rename-input", "PivotRenamed", timeout=5000)
                fpage.keyboard.press("Enter")
                fpage.wait_for_function(
                    "document.querySelector('#tree-content')?.textContent.includes('PivotRenamed')"
                    " && document.getElementById('status-indicator')?.textContent !== 'Computing…'",
                    timeout=20000,
                )
                joint_renamed_ok = (
                    fpage.locator('.tree-row[data-joint="PivotRenamed"]').count() >= 1
                    and fpage.locator('.tree-row[data-joint="Revolute1"]').count() == 0
                )

                # Constrain dialog (#88 step 3): nine rules (point_on_axis only through MCP), the gap only for mate/flush/distance, the angle only for angle
                step = "assemble: constrain dialog"
                fpage.click("#btn-constrain")
                fpage.wait_for_selector(".feature-dialog select[name='type']", timeout=5000)
                constrain_rules = fpage.eval_on_selector_all(".feature-dialog select[name='type'] option", "els => els.map(e => e.value)")
                gap_shown_mate = fpage.locator(".feature-dialog input[name='offset']").is_visible()
                fpage.select_option(".feature-dialog select[name='type']", "parallel")
                fpage.wait_for_selector(".feature-dialog input[name='offset']", state="hidden", timeout=5000)
                gap_hidden_parallel = not fpage.locator(".feature-dialog input[name='offset']").is_visible()
                fpage.select_option(".feature-dialog select[name='type']", "angle")
                fpage.wait_for_selector(".feature-dialog input[name='angle']", state="visible", timeout=5000)
                angle_shown = fpage.locator(".feature-dialog input[name='angle']").is_visible()
                constrain_title = fpage.locator(".feature-dialog-title").inner_text()
                fpage.click(".feature-cancel")
                _wait_dialog_closed(fpage)
                constrain_ok = (len(constrain_rules) == 9 and constrain_rules[0] == "mate" and gap_shown_mate
                                and gap_hidden_parallel and angle_shown and constrain_title == "Constrain")

                # Place Standard Part (#88 step 3): norms from the catalog, no length for a nut, places a screw
                step = "assemble: place standard"
                fpage.click("#btn-place-standard")
                fpage.wait_for_selector(".feature-dialog select[name='norm']", timeout=10000)
                std_norms = fpage.eval_on_selector_all(".feature-dialog select[name='norm'] option", "els => els.map(e => e.value)")
                fpage.select_option(".feature-dialog select[name='norm']", "ISO 4032")
                fpage.wait_for_selector(".feature-dialog select[name='length']", state="hidden", timeout=5000)
                std_nut_no_length = not fpage.locator(".feature-dialog select[name='length']").is_visible()
                fpage.select_option(".feature-dialog select[name='norm']", "ISO 4762")
                fpage.select_option(".feature-dialog select[name='size']", "M8")
                fpage.wait_for_selector(".feature-dialog select[name='length'] option[value='25']", state="attached", timeout=5000)
                std_lengths = fpage.eval_on_selector_all(".feature-dialog select[name='length'] option", "els => els.map(e => e.value)")
                fpage.select_option(".feature-dialog select[name='length']", "25")
                fpage.fill(".feature-dialog input[name='tz']", "60")
                fpage.wait_for_selector(".feature-ok:not([disabled])", timeout=5000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=60000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('ISO_4762_M8x25')", timeout=30000)
                std_ok = ("ISO 4762" in std_norms and "ISO 4032" in std_norms and std_nut_no_length and "25" in std_lengths)

                step = "assemble: update links"
                fpage.click("#btn-update-links")
                fpage.wait_for_selector("#update-links-dialog[open]", timeout=20000)
                upd_summary = fpage.locator("#update-links-summary").inner_text()
                fpage.keyboard.press("Escape")
                fpage.wait_for_function("!document.getElementById('update-links-dialog')?.open", timeout=5000)

                # Constrain gets an assembly of its own: in smoke_asm the joint checks stacked the parts in the top view
                step = "assemble: constrain apply & edit"
                _cws = _Ws(tmp_dir.name)
                try:
                    _cws.new(_ASM, "smoke_cons").save()
                finally:
                    _cws.close_all()
                fpage.evaluate("""() => fetch('api/open/smoke_cons.solidcraft', {
                  method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'
                })""")
                fpage.reload()
                fpage.wait_for_function(
                    "document.querySelector('#doc-kind')?.textContent === 'Assembly'"
                    " && document.getElementById('status-indicator')?.textContent === 'Ready'",
                    timeout=20000,
                )
                fpage.click('.ribbon-tab[data-tab="assemble"]')
                for _file, _tx, _gr in (("smoke_part.solidcraft", "0", "true"), ("smoke_top.solidcraft", "150", "false")):
                    fpage.click("#btn-place")
                    fpage.wait_for_selector(".feature-dialog select[name='file']", timeout=5000)
                    fpage.select_option(".feature-dialog select[name='file']", _file)
                    fpage.fill(".feature-dialog input[name='tx']", _tx)
                    fpage.select_option(".feature-dialog select[name='grounded']", _gr)
                    fpage.click(".feature-ok")
                    _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('smoke_top')", timeout=20000)
                fpage.keyboard.press("F6")
                fpage.wait_for_function("() => Math.abs((window.__camera?.up?.z ?? 0) - 1) < 1e-4", timeout=5000)
                _wait_frame(fpage)
                # Constrain applied by hand: flush between the top faces of smoke_part:1 and smoke_top:1,
                # shown with its rule in the browser, reopened by double-click as Edit, gap changed to 5 mm
                fpage.click("#btn-constrain")
                fpage.wait_for_selector(".feature-dialog select[name='type']", timeout=5000)
                fpage.select_option(".feature-dialog select[name='type']", "flush")
                # click each part's top face where the view shows it now (projected from the scene, not a fixed offset)
                body_of = {occ: body for body, occ in fpage.evaluate(
                    "() => fetch('api/assembly/context').then(r => r.json())").get("body_occurrences", {}).items()}

                def _top_face_xy(body):
                    return fpage.evaluate("""(name) => {
                      let mesh = null;
                      window.__scene.traverse((o) => { if (!mesh && o.isMesh && o.userData.bodyName === name) mesh = o; });
                      if (!mesh) return null;
                      mesh.geometry.computeBoundingBox();
                      const box = mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
                      const V = box.min.constructor;
                      const p = new V((box.min.x + box.max.x) / 2, (box.min.y + box.max.y) / 2, box.max.z).project(window.__camera);
                      const r = document.querySelector('#viewport canvas').getBoundingClientRect();
                      return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height];
                    }""", body)

                def _click_top(occ, slot):
                    xy = _top_face_xy(body_of.get(occ, ""))
                    if not xy:
                        return False
                    fpage.mouse.move(*xy)
                    fpage.wait_for_timeout(80)
                    fpage.mouse.click(*xy)
                    try:
                        fpage.wait_for_function(
                            "([s, prefix]) => (document.querySelector(`.feature-slot[data-slot=\"${s}\"]`)?.textContent || '').startsWith(prefix)",
                            arg=[slot, occ + " "],
                            timeout=3000,
                        )
                    except Exception:
                        pass
                    return fpage.locator(f'.feature-slot[data-slot="{slot}"]').inner_text().startswith(occ + " ")
                c_pick_a = _click_top("smoke_part:1", "origin_a")
                c_pick_b = _click_top("smoke_top:1", "origin_b")
                fpage.wait_for_selector(".feature-ok:not([disabled])", timeout=5000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=30000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Flush1')", timeout=20000)
                c_row_text = fpage.locator('.tree-row[data-joint="Flush1"]').first.inner_text()
                fpage.locator('.tree-row[data-joint="Flush1"]').first.dblclick()
                fpage.wait_for_selector(".feature-dialog select[name='type']", timeout=10000)
                c_edit_title = fpage.locator(".feature-dialog-title").inner_text()
                c_edit_rule = fpage.locator(".feature-dialog select[name='type']").input_value()
                fpage.fill(".feature-dialog input[name='offset']", "5")
                fpage.wait_for_selector(".feature-ok:not([disabled])", timeout=5000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=30000)
                c_ctx = fpage.evaluate("() => fetch('api/assembly/context').then(r => r.json())")
                c_live = next((j for j in c_ctx.get("joints", []) if j.get("name") == "Flush1"), {})
                constrain_apply_ok = (c_pick_a and c_pick_b and "flush" in c_row_text and c_edit_title == "Edit Flush1"
                                      and c_edit_rule == "flush" and c_live.get("constraint") == "flush"
                                      and abs(float(c_live.get("offset") or 0) - 5) < 1e-6)
                # Delete from the browser's context menu
                fpage.locator('.tree-row[data-joint="Flush1"]').first.click(button="right")
                fpage.locator("text=Delete Flush1").click()
                fpage.wait_for_function("!document.querySelector('.tree-row[data-joint=\"Flush1\"]')", timeout=20000)

                # The bolted connection gets an assembly of its own: after the joint checks above, two instances
                # of smoke_part.solidcraft sit in the stack under the pick, and a bolted connection refuses to go
                # through the same part file twice (each plate must be a distinct file)
                step = "assemble: bolted connection"
                _bws = _Ws(tmp_dir.name)
                try:
                    _bws.new(_ASM, "smoke_bolt").save()
                finally:
                    _bws.close_all()
                fpage.evaluate("""() => fetch('api/open/smoke_bolt.solidcraft', {
                  method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'
                })""")
                fpage.reload()
                fpage.wait_for_function(
                    "document.querySelector('#doc-kind')?.textContent === 'Assembly'"
                    " && document.getElementById('status-indicator')?.textContent === 'Ready'",
                    timeout=20000,
                )
                fpage.click('.ribbon-tab[data-tab="assemble"]')
                fpage.click("#btn-place")
                fpage.wait_for_selector(".feature-dialog select[name='file']", timeout=5000)
                fpage.select_option(".feature-dialog select[name='file']", "smoke_part.solidcraft")
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('smoke_part')", timeout=20000)

                # Place second plate at z=10 so bolted connection has a 2-plate stack (z=0..20)
                fpage.click("#btn-place")
                fpage.wait_for_selector(".feature-dialog select[name='file']", timeout=5000)
                fpage.select_option(".feature-dialog select[name='file']", "smoke_top.solidcraft")
                fpage.fill(".feature-dialog input[name='tz']", "10")
                fpage.select_option(".feature-dialog select[name='grounded']", "true")
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=20000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('smoke_top')", timeout=20000)

                fpage.click("#btn-bolted-connection")
                fpage.wait_for_selector(".feature-dialog select[name='screw_norm']", timeout=5000)
                bolted_norms = fpage.eval_on_selector_all(
                    ".feature-dialog select[name='screw_norm'] option",
                    "els => els.map(e => e.value)",
                )
                # Click the top planar face (z=25) in the 3D view via startHoleOrFacePick
                fbox = fpage.locator("#viewport canvas").bounding_box()
                fcx, fcy = fbox["x"] + fbox["width"] / 2, fbox["y"] + fbox["height"] / 2
                bolted_picked = False
                for fx, fy in ((0, -0.05), (0, 0), (-0.05, -0.05), (0.05, -0.05), (0, -0.1), (-0.08, -0.08), (0.08, -0.08), (0, 0.05)):
                    fpage.mouse.click(fcx + fx * fbox["width"], fcy + fy * fbox["height"])
                    _wait_frame(fpage)
                    z_str = fpage.locator(".feature-dialog input[name='z']").input_value().strip()
                    try:
                        if abs(float(z_str) - 25.0) < 1e-2:
                            bolted_picked = True
                            break
                    except ValueError:
                        pass
                bx_str = fpage.locator(".feature-dialog input[name='x']").input_value().strip()
                by_str = fpage.locator(".feature-dialog input[name='y']").input_value().strip()
                bz_str = fpage.locator(".feature-dialog input[name='z']").input_value().strip()
                fpage.wait_for_function(
                    "() => /×\\s*\\d+/.test(document.querySelector('.feature-delta')?.textContent || '')",
                    timeout=20000,
                )
                bolted_preview_text = fpage.locator(".feature-delta").inner_text()
                # Choose M10 with fixed length 80 mm (not in M6's option list) and apply
                fpage.select_option(".feature-dialog select[name='size']", "M10")
                fpage.wait_for_selector(".feature-dialog select[name='length_override'] option[value='80']", state="attached", timeout=5000)
                fpage.select_option(".feature-dialog select[name='length_override']", "80")
                fpage.wait_for_function(
                    "() => /M10\\s*×\\s*80/.test(document.querySelector('.feature-delta')?.textContent || '')",
                    timeout=20000,
                )
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=30000)
                fpage.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('M10')", timeout=20000)

                # Reopen dialog, click Edit on the existing connection, verify size/length and press OK
                fpage.click("#btn-bolted-connection")
                fpage.wait_for_selector(".feature-dialog [data-bolted-edit]", timeout=5000)
                fpage.click(".feature-dialog [data-bolted-edit]")
                edit_size_val = fpage.locator(".feature-dialog select[name='size']").input_value()
                edit_len_val = fpage.locator(".feature-dialog select[name='length_override']").input_value()
                fpage.wait_for_function("!document.querySelector('.feature-ok')?.disabled", timeout=20000)
                fpage.click(".feature-ok")
                _wait_dialog_done(fpage, timeout=30000)
                bolted_after_edit = fpage.evaluate("() => fetch('api/assembly/bolted').then(r => r.json())")
                saved_item = (bolted_after_edit.get("items") or [{}])[0]
                bolted_edit_ok = (
                    edit_size_val == "M10"
                    and edit_len_val == "80"
                    and saved_item.get("size") == "M10"
                    and saved_item.get("screw_length") == 80.0
                    and (saved_item.get("parameters", {}).get("fasteners") or {}).get("length_override") == 80.0
                )

                # Parts list (BOM, #49): the button opens a table with the parts and the M10 screw by its standard;
                # "Flat" reloads it, Close shuts it
                step = "assemble: bom"
                fpage.click("#btn-bom")
                fpage.wait_for_selector("#bom-dialog[open] .bom-table tbody tr", timeout=30000)
                bom_text = fpage.locator("#bom-dialog .bom-table").inner_text()
                bom_rows = fpage.locator("#bom-dialog .bom-table tbody tr").count()
                fpage.screenshot(path=os.path.join(out, "bom.png"))
                fpage.check("#bom-flat")
                fpage.wait_for_function("() => (document.getElementById('status-indicator')?.textContent || '').startsWith('Parts list:')",
                                        timeout=30000)
                fpage.wait_for_selector("#bom-dialog .bom-table tbody tr", timeout=30000)
                fpage.click("#bom-close")
                bom_ok = (bom_rows >= 2 and "smoke_part" in bom_text and "ISO" in bom_text and "M10" in bom_text
                          and not fpage.locator("#bom-dialog[open]").count())

                assemble_tab_ok = (
                    part_place_disabled and part_joint_disabled and part_bolted_disabled and part_upd_disabled
                    and part_place_title == "Open an assembly"
                    and part_joint_title == "Open an assembly"
                    and part_bolted_title == "Open an assembly"
                    and part_upd_title == "Open an assembly"
                    and asm_place_enabled and asm_joint_enabled and asm_bolted_enabled and asm_upd_enabled
                    and single_comp_ok_disabled and "two components" in single_comp_status
                    and joint_types == ["rigid", "revolute", "slider", "cylindrical", "ball"]
                    and face_pick_ok and same_comp_disabled
                    and edit_comp_a == "smoke_part:1" and edit_comp_b == "smoke_part:2"
                    and edit_switch_disabled and picked_face_3 and slot_b3_text.startswith("smoke_part:3 · ")
                    and joint_renamed_ok
                    and part_constrain_disabled and asm_constrain_enabled and constrain_ok and constrain_apply_ok
                    and part_std_disabled and asm_std_enabled and std_ok
                    and "ISO 4762" in bolted_norms and "ISO 10642" in bolted_norms
                    and bolted_picked and bx_str != "" and by_str != "" and "×" in bolted_preview_text
                    and bolted_edit_ok
                    and "1 joint checked" in upd_summary
                    and bom_ok
                )
                assemble_tab = (f"part disabled: {part_place_disabled and part_joint_disabled and part_bolted_disabled and part_upd_disabled}, "
                                f"asm enabled: {asm_place_enabled and asm_joint_enabled and asm_bolted_enabled and asm_upd_enabled}, "
                                f"3d pick: {face_pick_ok}, edit switch: {edit_switch_disabled and picked_face_3}, "
                                f"rename: {joint_renamed_ok}, constrain: {constrain_ok} ({len(constrain_rules)} rules), applied+edited+deleted: {constrain_apply_ok}, standard part: {std_ok}, "
                                f"bolted pick: {bolted_picked} ({bx_str},{by_str},{bz_str}) prev={bolted_preview_text!r}, "
                                f"bolted edit: {bolted_edit_ok} ({edit_size_val}x{edit_len_val}), upd: {upd_summary!r}, "
                                f"bom: {bom_ok} ({bom_rows} rows)")
            except Exception as e:
                folder_mode = f"error at {step}: {e}"[:200]
                # an exception here must fail the run, not leave the later checks as "skipped"
                folder_ok = False
                assemble_tab_ok = False
            finally:
                fsrv.shutdown()
                fsrv.server_close()

            # Edit-dialog roundtrip across all 8 EDITABLE feature types on Server and Live-Demo (#129)
            edit_part = prepare_edit_part(Path(tmp_dir.name) / "edit_part.solidcraft")
            dsrv = _build_edit_demo(edit_part, Path(tmp_dir.name) / "edit_demo")
            for mode_lbl, is_d, srv_obj, base_url in (
                ("edit roundtrip server", False, _cs(str(edit_part), port=port + 2), f"http://{host}:{port + 2}/"),
                ("edit roundtrip demo", True, dsrv, None),
            ):
                step = mode_lbl
                threading.Thread(target=srv_obj.serve_forever, daemon=True).start()
                ep = browser.new_page(viewport={"width": 1300, "height": 750})
                _apply_cpu_throttle(ep)
                ep.on("pageerror", lambda e, lbl=mode_lbl: errors.append(f"{lbl}: {e}"))
                try:
                    turl = base_url or f"http://127.0.0.1:{srv_obj.server_address[1]}/?demo={edit_part.stem}"
                    ok_flag, msg = _run_edit_roundtrip(ep, mode_lbl, turl, is_demo=is_d)
                    if is_d:
                        edit_roundtrip_demo_ok, edit_roundtrip_demo = ok_flag, msg
                    else:
                        edit_roundtrip_server_ok, edit_roundtrip_server = ok_flag, msg
                finally:
                    ep.close()
                    srv_obj.shutdown()
                    srv_obj.server_close()

        browser.close()
except Exception as exc:
    import traceback
    traceback.print_exc()
    errors.append(f"browser test exception at {step}: {exc}")
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

print("rename:", rename_status)
print("fillet:", fillet)
print("command dialog:", command_dialog)
print("hole:", hole)
print("extrude:", extrude)
print("revolve:", revolve)
print("sketch:", sketch)
print("visibility:", visibility)
print("folder mode:", folder_mode)
print("open folder:", open_folder)
print("import step browse:", import_browse)
print("assemble tab:", assemble_tab)
print("edit roundtrip server:", edit_roundtrip_server)
print("edit roundtrip demo:", edit_roundtrip_demo)
print("new part:", new_part)
print("measure:", measured.replace("\n", " | "))
print("section:", section)
print("esc closes:", closed, "page errors:", errors)
print("session log js_errors:", js_errors)
print("edge:", edge.replace("\n", " | ") or "none found")

all_checks_ok = ("Distance" in measured and "Section" in section and closed and bool(edge) and new_part_ok and fillet_ok
                 and command_dialog_ok
                 and hole_ok and extrude_ok and revolve_ok and sketch_ok and visibility_ok and folder_ok and open_folder_ok
                 and import_browse_ok and assemble_tab_ok and rename_ok
                 and edit_roundtrip_server_ok and edit_roundtrip_demo_ok and not errors and not js_errors)

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
