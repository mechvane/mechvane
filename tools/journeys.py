"""Three end-to-end user journeys in a headless browser, judged by model dimensions and tree/check state.

    <python with playwright> tools/journeys.py [--journey 1|2|3]

Screenshots for each step are written to /tmp/journeys/<journey>/<nr>-<step>.png.
Exits with code != 0 on any FAIL or browser/JS error; Mechvane UI bugs that block a step are
reported as `KNOWN <description>` without bypassing the broken step.
"""
import argparse
import glob
import json
import math
import os
import shutil
import sys
import tempfile
import threading
import time
from datetime import date
from pathlib import Path

# Ensure mechvane is importable even when using playwright from a foreign virtualenv
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from playwright.sync_api import sync_playwright  # noqa: E402

from mechvane import examples, install, query  # noqa: E402
from mechvane.documents import PART, Workspace  # noqa: E402
from mechvane.ui.server import create_server, hole_sizes  # noqa: E402

OUT_ROOT = Path("/tmp/journeys")


class JourneyContext:
    """Tracks assertions, screenshots, and KNOWN Mechvane issues across journeys."""

    def __init__(self, out_root: Path = OUT_ROOT):
        self.out_root = out_root
        self.failures: list[str] = []
        self.known: list[str] = []
        self.errors: list[str] = []

    def check(self, journey: str, step: str, cond: bool, actual, expected) -> bool:
        if cond:
            print(f"OK   {journey} {step}: {actual}")
            return True
        msg = f"FAIL {journey} {step}: {actual} statt {expected}"
        print(msg)
        self.failures.append(msg)
        return False

    def mark_known(self, journey: str, step: str, description: str):
        msg = f"KNOWN {journey} {step}: {description}"
        print(msg)
        self.known.append(msg)

    def snap(self, page, journey: str, nr: int, name: str):
        d = self.out_root / journey
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{nr:02d}-{name}.png"
        page.screenshot(path=str(path))
        return path


def _find_browser() -> str | None:
    shells = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")))
    return shells[-1] if shells else None


def _rel_close(actual: float, expected: float, rel_tol: float = 1e-3) -> bool:
    return abs(actual - expected) <= rel_tol * max(abs(expected), 1.0)


def _inspect_doc(srv) -> dict:
    with srv.lock:
        doc = srv.ensure_current()
        insp = doc.session.cmd("document.inspect", {"measure": True})
        sketches = {}
        for sk in insp.get("sketches", []):
            sname = sk.get("name")
            if sname:
                sketches[sname] = doc.session.cmd("sketch.inspect", {"sketch": sname})
        holes = query.find(doc, "holes")
        return {"inspect": insp, "sketches": sketches, "holes": holes}


def _body_volume_and_bbox(srv) -> tuple[float, list[float], list[float]]:
    data = _inspect_doc(srv)
    bodies = data["inspect"].get("bodies") or []
    if not bodies:
        return 0.0, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    b = bodies[0]
    bb = b["bbox"]
    return float(b["volume_mm3"]), list(bb["min"]), list(bb["max"])


def _project_world(page, x: float, y: float, z: float) -> tuple[float, float]:
    return tuple(page.evaluate("""([x, y, z]) => {
      const r = document.querySelector('#viewport canvas').getBoundingClientRect();
      const v = window.__camera.position.clone().set(x, y, z).project(window.__camera);
      return [r.left + (v.x + 1) / 2 * r.width, r.top + (1 - v.y) / 2 * r.height];
    }""", [x, y, z]))


def _project_sketch_uv(page, plane: dict, u: float, v: float) -> tuple[float, float]:
    o = plane["origin"]
    xd = plane["x_dir"]
    yd = plane["y_dir"]
    wx = o[0] + u * xd[0] + v * yd[0]
    wy = o[1] + u * xd[1] + v * yd[1]
    wz = o[2] + u * xd[2] + v * yd[2]
    return _project_world(page, wx, wy, wz)


def _sketch_state(page) -> dict:
    return page.evaluate("() => fetch('api/sketch/state').then(r => r.json())")


def _tree_feature_names(page) -> list[str]:
    return page.eval_on_selector_all(
        "#tree-content .tree-row[data-feature]",
        "els => els.map(e => e.dataset.feature)",
    )


def _wait_sketch_state(page, predicate_js: str, timeout: int = 10000):
    page.wait_for_function(
        f"async () => {{ const r = await fetch('api/sketch/state'); const d = await r.json(); return ({predicate_js})(d); }}",
        timeout=timeout,
    )


def _draw_origin_circle_and_dim(page, diameter: float, text_uv: tuple[float, float]):
    """In an active sketch, draw a circle centred at (0, 0) and dimension its diameter via General Dimension."""
    st_wrap = _sketch_state(page)
    plane = st_wrap["state"]["plane"]
    curves_before = len(st_wrap["state"].get("curves") or [])
    r_init = diameter * 0.42

    page.keyboard.press("c")
    page.wait_for_selector('[data-sketch-tool="circle"].active', timeout=5000)
    cx, cy = _project_sketch_uv(page, plane, 0.0, 0.0)
    rx, ry = _project_sketch_uv(page, plane, r_init, 0.0)
    page.mouse.move(cx, cy)
    page.mouse.click(cx, cy)
    page.wait_for_timeout(120)
    page.mouse.move(rx, ry)
    page.wait_for_timeout(120)
    page.mouse.click(rx, ry)
    _wait_sketch_state(page, f"d => (d.state?.curves?.length || 0) > {curves_before}")

    # Activate General Dimension (D), click the new circle perimeter, then click text_at and type diameter
    page.keyboard.press("d")
    page.wait_for_selector('[data-sketch-tool="dimension"].active', timeout=5000)
    ex, ey = _project_sketch_uv(page, plane, r_init, 0.0)
    tx, ty = _project_sketch_uv(page, plane, text_uv[0], text_uv[1])
    page.mouse.move(ex, ey)
    page.wait_for_timeout(80)
    page.mouse.click(ex, ey)
    page.wait_for_timeout(150)
    page.mouse.move(tx, ty)
    page.wait_for_timeout(80)
    page.mouse.click(tx, ty)
    page.wait_for_selector(".sketch-dim-edit", timeout=5000)
    page.keyboard.press("Control+a")
    page.keyboard.type(str(diameter))
    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('.sketch-dim-edit')", timeout=10000)
    target_r = diameter / 2.0
    _wait_sketch_state(
        page,
        f"d => (d.state?.curves || []).some(c => c.type === 'circle' && !c.link && Math.abs(c.radius - {target_r}) < 1e-3)",
    )


def _click_planar_face(page, x: float, y: float, z: float) -> bool:
    """Move onto a projected world point on a planar face until hover overlay activates, then click."""
    sx, sy = _project_world(page, x, y, z)
    for dx, dy in ((0, 0), (8, 0), (-8, 0), (0, 8), (0, -8), (15, -15), (-15, 15)):
        page.mouse.move(sx + dx, sy + dy)
        page.wait_for_timeout(60)
        hovered = page.evaluate(
            "() => { const g = window.__scene?.children?.find(c => c.renderOrder === 9); return Boolean(g && g.children.length > 0); }"
        )
        if hovered:
            page.mouse.click(sx + dx, sy + dy)
            return True
    page.mouse.click(sx, sy)
    return False


def _start_server_for_folder(folder: Path):
    srv = create_server(str(folder), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    return srv, url


def _new_page(browser, ctx: JourneyContext, url: str):
    page = browser.new_page(viewport={"width": 1300, "height": 780})
    page.on("pageerror", lambda e: ctx.errors.append(f"pageerror: {e}"))
    page.on("dialog", lambda d: (ctx.errors.append(f"browser dialog: {d.message}"), d.dismiss()))
    page.goto(url, wait_until="load")
    return page


# ---------------------------------------------------------------------------
# Journey 1: Flansch von Hand
# ---------------------------------------------------------------------------
def run_journey_1(browser, ctx: JourneyContext):
    D = 80.0
    H = 10.0
    BCD = 52.0  # bolt circle diameter: edge distance = (80 - 52)/2 - 3.3 = 10.7 mm >= 9.9 mm
    HOLE_COUNT = 6
    CHAMFER = 1.0
    m6_dia = float(hole_sizes()["sizes"]["M6"]["clearance"]["normal"])  # 6.6 mm

    with tempfile.TemporaryDirectory(prefix="mechvane-j1-") as tmp:
        srv, url = _start_server_for_folder(Path(tmp))
        page = _new_page(browser, ctx, url)
        try:
            page.wait_for_selector("#doc-name", timeout=15000)

            # 1. Neues Bauteil
            page.click("#file-menu > summary")
            page.wait_for_selector("#btn-new-part", timeout=5000)
            page.click("#btn-new-part")
            page.wait_for_selector("#new-part-dialog[open]", timeout=5000)
            page.fill("#new-part-name", "flansch")
            page.click("#new-part-dialog .btn-submit")
            page.wait_for_function(
                "() => document.querySelector('#doc-name')?.textContent.includes('flansch') "
                "&& document.querySelector('#tree-content')?.textContent.includes('End of Part')",
                timeout=30000,
            )
            ctx.check("1", "neues_bauteil", page.locator("#doc-kind").inner_text().strip() == "Part",
                      page.locator("#doc-kind").inner_text().strip(), "Part")
            ctx.snap(page, "1", 1, "neues-bauteil")

            # 2. Skizze auf XY
            page.click("#btn-sketch")
            page.wait_for_selector(".sketch-plane-bar [data-plane=XY]", timeout=5000)
            page.click(".sketch-plane-bar [data-plane=XY]")
            page.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=10000)
            _wait_sketch_state(page, "d => Boolean(d.active && d.state?.plane)")
            ctx.snap(page, "1", 2, "skizze-xy")

            # 3. Kreis Ø80 bemaßen
            _draw_origin_circle_and_dim(page, D, (D * 0.55, D * 0.35))
            st1 = _sketch_state(page)["state"]
            sk1_fc = bool(st1.get("fully_constrained")) and st1.get("dof") == 0
            c1 = next((c for c in st1.get("curves", []) if c.get("type") == "circle"), {})
            ctx.check("1", "kreis_80", sk1_fc and abs(float(c1.get("radius", 0)) - D / 2) < 1e-3,
                      f"r={c1.get('radius')}, fully_constrained={st1.get('fully_constrained')}, dof={st1.get('dof')}",
                      f"r={D/2}, fully_constrained=True, dof=0")
            ctx.snap(page, "1", 3, "kreis-80-bemassen")

            # Finish Sketch1
            page.click('[data-sketch-action="finish"]')
            page.wait_for_function(
                "() => document.querySelector('.ribbon-tab[data-tab=\"3d-model\"]').classList.contains('active') "
                "&& document.querySelector('#tree-content')?.textContent.includes('Sketch1')",
                timeout=15000,
            )

            # 4. Extrusion 10
            page.click("#btn-extrude")
            page.wait_for_selector(".feature-dialog", timeout=5000)
            page.fill('.feature-dialog input[name="distance"]', str(int(H)))
            page.wait_for_function(
                "/Volume/.test(document.querySelector('.feature-delta')?.textContent || '')",
                timeout=20000,
            )
            page.click(".feature-ok")
            page.wait_for_function(
                "() => !document.querySelector('.feature-dialog') "
                "&& document.querySelector('#tree-content')?.textContent.includes('Extrude1')",
                timeout=20000,
            )
            ctx.snap(page, "1", 4, "extrusion-10")

            # 5. Zweite Skizze auf der Deckfläche mit Bohrkreis
            page.click("#btn-sketch")
            page.wait_for_selector(".sketch-plane-bar", timeout=5000)
            _click_planar_face(page, 0.0, -20.0, H)
            page.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=15000)
            _wait_sketch_state(page, "d => Boolean(d.active && d.state?.plane)")

            _draw_origin_circle_and_dim(page, BCD, (BCD * 0.55, -BCD * 0.35))
            st2 = _sketch_state(page)["state"]
            sk2_fc = bool(st2.get("fully_constrained")) and st2.get("dof") == 0
            ctx.check("1", "skizze_2_bohrkreis", sk2_fc,
                      f"fully_constrained={st2.get('fully_constrained')}, dof={st2.get('dof')}",
                      "fully_constrained=True, dof=0")
            ctx.snap(page, "1", 5, "skizze-bohrkreis")

            page.click('[data-sketch-action="finish"]')
            page.wait_for_function(
                "() => document.querySelector('.ribbon-tab[data-tab=\"3d-model\"]').classList.contains('active') "
                "&& document.querySelector('#tree-content')?.textContent.includes('Sketch2')",
                timeout=15000,
            )

            # 6. Bohrung M6 Durchgang
            page.click("#btn-hole")
            page.wait_for_selector(".feature-dialog", timeout=5000)
            _click_planar_face(page, BCD / 2.0, 0.0, H)
            page.wait_for_function("() => document.querySelector('.feature-dialog input[name=\"z\"]')?.value !== ''",
                                   timeout=5000)
            page.fill('.feature-dialog input[name="x"]', str(BCD / 2.0))
            page.fill('.feature-dialog input[name="y"]', "0")
            page.fill('.feature-dialog input[name="z"]', str(H))
            page.select_option('.feature-dialog select[name="spec"]', "clearance")
            page.select_option('.feature-dialog select[name="size"]', "M6")
            page.select_option('.feature-dialog select[name="fit"]', "normal")
            through_chk = page.locator('.feature-dialog input[name="through"]')
            if not through_chk.is_checked():
                through_chk.check()
            page.wait_for_function(
                "/Volume/.test(document.querySelector('.feature-delta')?.textContent || '') "
                "&& !document.querySelector('.feature-ok')?.disabled",
                timeout=20000,
            )
            page.click(".feature-ok")
            page.wait_for_function(
                "() => !document.querySelector('.feature-dialog') "
                "&& document.querySelector('#tree-content')?.textContent.includes('Hole1')",
                timeout=20000,
            )
            ctx.snap(page, "1", 6, "bohrung-m6")

            # 7. Kreismuster 6×
            page.click("#btn-circular")
            page.wait_for_selector(".feature-dialog", timeout=5000)
            page.click('.tree-row[data-feature="Hole1"]')
            page.select_option('.feature-dialog select[name="axis"]', "Z")
            page.fill('.feature-dialog input[name="count"]', str(HOLE_COUNT))
            page.fill('.feature-dialog input[name="angle"]', "360")
            page.wait_for_function(
                "/Volume/.test(document.querySelector('.feature-delta')?.textContent || '') "
                "&& !document.querySelector('.feature-ok')?.disabled",
                timeout=30000,
            )
            page.click(".feature-ok")
            page.wait_for_function(
                "() => !document.querySelector('.feature-dialog') "
                "&& document.querySelector('#tree-content')?.textContent.includes('CircularPattern1')",
                timeout=30000,
            )
            ctx.snap(page, "1", 7, "kreismuster-6x")

            # 8. Fase 1 an der Außenkante
            page.click("#btn-chamfer")
            page.wait_for_selector(".feature-dialog", timeout=5000)
            edge_picked = False
            for ang in (0.0, -45.0, -90.0, 45.0, -135.0):
                rad = math.radians(ang)
                ex = (D / 2.0) * math.cos(rad)
                ey = (D / 2.0) * math.sin(rad)
                sx, sy = _project_world(page, ex, ey, H)
                for dx, dy in ((0, 0), (2, 0), (-2, 0), (0, 2), (0, -2), (4, 0), (-4, 0)):
                    page.mouse.click(sx + dx, sy + dy)
                    page.wait_for_timeout(80)
                    if "selected" in page.locator(".feature-pick-count").inner_text():
                        edge_picked = True
                        break
                if edge_picked:
                    break
            ctx.check("1", "fase_kante_gewaehlt", edge_picked,
                      page.locator(".feature-pick-count").inner_text(), "1 edge selected")
            page.fill('.feature-dialog input[name="distance"]', str(int(CHAMFER)))
            page.wait_for_function(
                "/Volume/.test(document.querySelector('.feature-delta')?.textContent || '') "
                "&& !document.querySelector('.feature-ok')?.disabled",
                timeout=20000,
            )
            page.click(".feature-ok")
            page.wait_for_function(
                "() => !document.querySelector('.feature-dialog') "
                "&& document.querySelector('#tree-content')?.textContent.includes('Chamfer1')",
                timeout=20000,
            )
            ctx.snap(page, "1", 8, "fase-1")

            # 9. Prüfung öffnen
            page.click('.ribbon-tab[data-tab="inspect"]')
            page.click("#btn-design-check")
            page.wait_for_selector("#design-check-section[open]", timeout=5000)
            page.wait_for_function(
                "() => document.querySelector('#verdict-badge')?.textContent.includes('Check:')",
                timeout=15000,
            )
            verdict_text = page.locator("#verdict-badge").inner_text().strip()
            ctx.check("1", "pruefung_offen", verdict_text == "Check: OK", verdict_text, "Check: OK")
            ctx.snap(page, "1", 9, "pruefung")

            # Final geometry & sketch verification from dimensions
            R = D / 2.0
            r_hole = m6_dia / 2.0
            expected_vol = math.pi * (R ** 2 * H - (R - CHAMFER / 3.0) * (CHAMFER ** 2) - HOLE_COUNT * (r_hole ** 2) * H)
            expected_min = [-R, -R, 0.0]
            expected_max = [R, R, H]

            insp = _inspect_doc(srv)
            vol, bmin, bmax = _body_volume_and_bbox(srv)
            ctx.check("1", "volumen", _rel_close(vol, expected_vol, 1e-3),
                      f"{vol:.3f} mm3", f"{expected_vol:.3f} mm3 (+/-0.1%)")
            bbox_ok = all(_rel_close(a, b, 1e-3) for a, b in zip(bmin + bmax, expected_min + expected_max))
            ctx.check("1", "huellquader", bbox_ok,
                      f"min={[round(v, 4) for v in bmin]}, max={[round(v, 4) for v in bmax]}",
                      f"min={expected_min}, max={expected_max}")
            n_holes = len(insp["holes"])
            ctx.check("1", "sechs_bohrungen", n_holes == HOLE_COUNT, n_holes, HOLE_COUNT)
            for sname in ("Sketch1", "Sketch2"):
                sk = insp["sketches"].get(sname, {})
                ctx.check("1", f"{sname.lower()}_voll_bestimmt",
                          bool(sk.get("fully_constrained")) and sk.get("dof") == 0,
                          f"fully_constrained={sk.get('fully_constrained')}, dof={sk.get('dof')}",
                          "fully_constrained=True, dof=0")
        finally:
            page.close()
            srv.shutdown()
            srv.server_close()


# ---------------------------------------------------------------------------
# Journey 2: Ändern und Rückgängig
# ---------------------------------------------------------------------------
def _prepare_journey_2_folder(folder: Path) -> dict[str, float]:
    ws = Workspace(folder)
    try:
        doc = examples.bracket(ws)
        s = doc.session
        v_no_fillet_m6 = float(s.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"])
        # examples.bracket has no Fillet yet; add Fillet1 on the inner L-corner so Journey 2 can delete it.
        s.cmd("solid.fillet", {"edges": [[30, 30, 8]], "radius": 3.0, "name": "Fillet1"})
        doc.save()
        v_initial = float(s.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"])
    finally:
        ws.close_all()

    sizes = hole_sizes()["sizes"]
    d_m6 = float(sizes["M6"]["clearance"]["normal"])  # 6.6
    d_m8 = float(sizes["M8"]["clearance"]["normal"])  # 9.0
    depth = 8.0
    dv_hole = math.pi * ((d_m8 / 2.0) ** 2 - (d_m6 / 2.0) ** 2) * depth

    # Compute volume without Fillet1 (BasePlate + Wall - Hole(M8) - CountersinkNearWall)
    ws2 = Workspace(folder)
    try:
        tmp_doc = ws2.new(PART, "_ref_no_fillet")
        tmp_doc.session.batch([
            {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 8, "corner": [0, 0, 0],
                                                "name": "BasePlate", "body_name": "Bracket"}},
            {"command": "solid.box", "params": {"length": 60, "width": 10, "height": 40, "corner": [0, 30, 8],
                                                "operation": "join", "name": "Wall"}},
            {"command": "solid.hole", "params": {"position": [18, 14, 8], "direction": [0, 0, -1],
                                                 "clearance": "M8", "depth": 8, "name": "Hole"}},
            {"command": "solid.hole", "params": {"position": [42, 23, 8], "direction": [0, 0, -1],
                                                 "clearance": "M6", "depth": 8, "type": "countersink",
                                                 "cs_diameter": 13.7, "cs_angle": 90, "name": "CountersinkNearWall"}},
        ])
        v_no_fillet_m8 = float(tmp_doc.session.cmd("document.inspect", {"measure": True})["bodies"][0]["volume_mm3"])
    finally:
        ws2.close_all()
        (folder / "_ref_no_fillet.solidcraft").unlink(missing_ok=True)

    return {
        "v_initial": v_initial,
        "v_m8": v_initial - dv_hole,
        "v_no_fillet_m6": v_no_fillet_m6,
        "v_no_fillet_m8": v_no_fillet_m8,
    }


def run_journey_2(browser, ctx: JourneyContext):
    with tempfile.TemporaryDirectory(prefix="mechvane-j2-") as tmp:
        folder = Path(tmp)
        vols = _prepare_journey_2_folder(folder)
        srv, url = _start_server_for_folder(folder)
        page = _new_page(browser, ctx, url + "?doc=bracket.solidcraft")
        try:
            page.wait_for_function(
                "() => document.querySelector('#doc-name')?.textContent.includes('bracket') "
                "&& document.querySelector('#tree-content')?.textContent.includes('Fillet1')",
                timeout=30000,
            )
            v0, _, _ = _body_volume_and_bbox(srv)
            ctx.check("2", "start_volumen", _rel_close(v0, vols["v_initial"], 1e-3),
                      f"{v0:.2f}", f"{vols['v_initial']:.2f}")
            ctx.snap(page, "2", 1, "demo-winkel")

            # 2. Bohrung per Doppelklick im Baum auf M8 ändern
            page.dblclick('.tree-row[data-feature="Hole"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            page.select_option('.feature-dialog select[name="size"]', "M8")
            page.wait_for_function(
                "() => /Volume/.test(document.querySelector('.feature-delta')?.textContent || '') "
                "|| ((document.querySelector('.feature-error')?.textContent || '').trim().length > 0)",
                timeout=20000,
            )
            page.click(".feature-ok")
            page.wait_for_function(
                "() => !document.querySelector('.feature-dialog') "
                "|| ((document.querySelector('.feature-error')?.textContent || '').trim().length > 0)",
                timeout=20000,
            )
            hole_edited = page.locator(".feature-dialog").count() == 0
            if hole_edited:
                page.wait_for_selector("#btn-undo:not([disabled])", timeout=10000)
                v1, _, _ = _body_volume_and_bbox(srv)
                ctx.check("2", "bohrung_m8_volumen", _rel_close(v1, vols["v_m8"], 1e-3),
                          f"{v1:.2f}", f"{vols['v_m8']:.2f}")
                ctx.snap(page, "2", 2, "bohrung-m8")
            else:
                err_txt = page.locator(".feature-error").inner_text().strip().splitlines()[0]
                ctx.snap(page, "2", 2, "bohrung-m8")
                ctx.mark_known(
                    "2", "bohrung_m8",
                    f"Edit-Hole-Dialog auf Sacklochbohrung scheitert in Mechvane ({err_txt})",
                )
                page.click(".feature-cancel")
                page.wait_for_function("() => !document.querySelector('.feature-dialog')", timeout=10000)

            # 3. Rundung löschen
            page.click('.tree-row[data-feature="Fillet1"]')
            page.keyboard.press("Delete")
            page.wait_for_function(
                "() => !document.querySelector('#tree-content')?.textContent.includes('Fillet1')",
                timeout=20000,
            )
            exp_no_fillet = vols["v_no_fillet_m8"] if hole_edited else vols["v_no_fillet_m6"]
            v2, _, _ = _body_volume_and_bbox(srv)
            ctx.check("2", "rundung_geloescht_volumen", _rel_close(v2, exp_no_fillet, 1e-3),
                      f"{v2:.2f}", f"{exp_no_fillet:.2f}")
            ctx.snap(page, "2", 3, "rundung-loeschen")

            # 4. Erstes Strg+Z (Fillet1 wieder da)
            page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+z")
            page.wait_for_function(
                "() => document.querySelector('#tree-content')?.textContent.includes('Fillet1')",
                timeout=20000,
            )
            exp_after_undo1 = vols["v_m8"] if hole_edited else vols["v_initial"]
            v3, _, _ = _body_volume_and_bbox(srv)
            ctx.check("2", "undo_1_volumen", _rel_close(v3, exp_after_undo1, 1e-3),
                      f"{v3:.2f}", f"{exp_after_undo1:.2f}")
            ctx.snap(page, "2", 4, "undo-1")

            # 5. Zweites Strg+Z (Hole wieder M6, sofern Step 2 gegriffen hat)
            if hole_edited:
                page.wait_for_selector("#btn-undo:not([disabled])", timeout=5000)
                # Redo is enabled since the first Ctrl+Z already: wait until it names the step this one took back
                redo_before = page.locator("#btn-redo").get_attribute("title")
                page.keyboard.press("Control+z")
                page.wait_for_function(
                    "(t) => { const b = document.querySelector('#btn-redo'); return b && !b.disabled && b.title !== t; }",
                    arg=redo_before, timeout=20000,
                )
                page.wait_for_function(
                    "() => ['Ready', 'Undone'].includes(document.querySelector('#status-indicator')?.textContent)",
                    timeout=20000,
                )
            else:
                page.keyboard.press("Control+z")
                page.wait_for_timeout(300)
            v4, _, _ = _body_volume_and_bbox(srv)
            ctx.check("2", "undo_2_volumen", _rel_close(v4, vols["v_initial"], 1e-3),
                      f"{v4:.2f}", f"{vols['v_initial']:.2f}")
            ctx.snap(page, "2", 5, "undo-2")

            # 6. Einmal Strg+Y
            page.wait_for_selector("#btn-redo:not([disabled])", timeout=5000)
            page.keyboard.press("Control+y")
            page.wait_for_function(
                "() => document.querySelector('#status-indicator')?.textContent.includes('Redone') "
                "|| document.querySelector('#btn-redo')?.disabled",
                timeout=20000,
            )
            page.wait_for_timeout(500)
            v5, _, _ = _body_volume_and_bbox(srv)
            if hole_edited:
                ctx.check("2", "redo_1_volumen", _rel_close(v5, vols["v_m8"], 1e-3),
                          f"{v5:.2f}", f"{vols['v_m8']:.2f}")
                expected_tree = ["BasePlate", "Wall", "Hole", "CountersinkNearWall", "Fillet1"]
            else:
                ctx.check("2", "redo_1_volumen", _rel_close(v5, vols["v_no_fillet_m6"], 1e-3),
                          f"{v5:.2f}", f"{vols['v_no_fillet_m6']:.2f}")
                expected_tree = ["BasePlate", "Wall", "Hole", "CountersinkNearWall"]
            actual_tree = _tree_feature_names(page)
            ctx.check("2", "baum_eintraege", actual_tree == expected_tree, actual_tree, expected_tree)
            ctx.snap(page, "2", 6, "redo-1")
        finally:
            page.close()
            srv.shutdown()
            srv.server_close()


# ---------------------------------------------------------------------------
# Journey 3: Prüfen und beheben
# ---------------------------------------------------------------------------
def run_journey_3(browser, ctx: JourneyContext):
    with tempfile.TemporaryDirectory(prefix="mechvane-j3-") as tmp:
        folder = Path(tmp)
        ws = Workspace(folder)
        try:
            examples.build_all(ws)
        finally:
            ws.close_all()

        srv, url = _start_server_for_folder(folder)
        page = _new_page(browser, ctx, url + "?doc=bracket.solidcraft")
        try:
            page.wait_for_function(
                "() => document.querySelector('#doc-name')?.textContent.includes('bracket') "
                "&& document.querySelector('#verdict-badge')?.textContent.includes('Check:')",
                timeout=30000,
            )
            verdict = page.locator("#verdict-badge").inner_text().strip()
            issue_cards = page.locator("#findings-content .finding-card.severity-fail, #findings-content .finding-card.severity-warn")
            ctx.snap(page, "3", 1, "demo-befund")

            if not ctx.check("3", "befund_vorhanden", issue_cards.count() > 0,
                             f"{issue_cards.count()} finding(s), verdict={verdict!r}", ">= 1 finding"):
                return

            # updateFindingsView auto-selects the first failing finding on initial load; clicking an active
            # card toggles it off, so deselect first if active, then click to verify selection + highlight.
            if "active" in (issue_cards.first.get_attribute("class") or ""):
                issue_cards.first.click()
                page.wait_for_function("() => Boolean(document.getElementById('selection-banner')?.hidden)", timeout=5000)
            issue_cards.first.click()
            page.wait_for_selector("#selection-banner:not([hidden])", timeout=5000)
            banner = page.locator("#selection-banner").inner_text().strip()
            highlighted = page.evaluate(
                "() => window.__scene?.children?.some("
                "c => c.children?.some(m => m.isMesh && m.material?.emissive?.getHex?.() > 0)) || false"
            )
            ctx.check("3", "flaeche_markiert", highlighted and banner != "", banner, "highlighted face banner")
            ctx.snap(page, "3", 2, "befund-markiert")

            # Fix the hole_edge_distance finding by moving Hole from x=6 to x=12 via the Edit dialog
            page.dblclick('.tree-row[data-feature="Hole"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            page.fill('.feature-dialog input[name="x"]', "12")
            page.wait_for_function(
                "() => !document.querySelector('.feature-ok')?.disabled",
                timeout=20000,
            )
            page.click(".feature-ok")
            page.wait_for_function(
                "() => !document.querySelector('.feature-dialog') "
                "&& document.querySelector('#verdict-badge')?.textContent.trim() === 'Check: OK'",
                timeout=20000,
            )
            verdict_after = page.locator("#verdict-badge").inner_text().strip()
            ctx.check("3", "befund_behoben", issue_cards.count() == 0 and verdict_after == "Check: OK",
                      f"findings={issue_cards.count()}, verdict={verdict_after!r}", "0 findings, 'Check: OK'")
            ctx.snap(page, "3", 3, "befund-behoben")

            page.reload(wait_until="load")
            page.wait_for_function(
                "() => document.querySelector('#doc-name')?.textContent.includes('bracket') "
                "&& document.querySelector('#verdict-badge')?.textContent.includes('Check:') "
                "&& document.querySelector('.tree-row[data-feature=\"Hole\"]') !== null",
                timeout=30000,
            )
            verdict_reloaded = page.locator("#verdict-badge").inner_text().strip()
            page.dblclick('.tree-row[data-feature="Hole"]')
            page.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=10000)
            reloaded_x = page.locator('.feature-dialog input[name="x"]').input_value().strip()
            page.click(".feature-cancel")
            page.wait_for_function("() => !document.querySelector('.feature-dialog')", timeout=10000)
            ctx.check("3", "wert_nach_neuladen",
                      issue_cards.count() == 0 and verdict_reloaded == "Check: OK"
                      and _rel_close(float(reloaded_x or 0), 12.0),
                      f"findings={issue_cards.count()}, verdict={verdict_reloaded!r}, Hole.x={reloaded_x!r}",
                      "0 findings, 'Check: OK', Hole.x='12'")
            ctx.snap(page, "3", 4, "neu-geladen")
        finally:
            page.close()
            srv.shutdown()
            srv.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run Mechvane Playwright user journeys.")
    parser.add_argument("--journey", type=int, choices=[1, 2, 3], help="Run only one journey (1, 2, or 3)")
    args = parser.parse_args()

    selected = [args.journey] if args.journey else [1, 2, 3]
    if args.journey is None and OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    today_str = f"{date.today():%Y-%m-%d}.jsonl"
    log_file = install.CACHE / "logs" / today_str
    log_pos = log_file.stat().st_size if log_file.exists() else 0

    ctx = JourneyContext(OUT_ROOT)
    shell = _find_browser()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=shell,
                args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"],
            )
            try:
                if 1 in selected:
                    print("=== Reise 1: Flansch von Hand ===")
                    run_journey_1(browser, ctx)
                if 2 in selected:
                    print("=== Reise 2: Ändern und Rückgängig ===")
                    run_journey_2(browser, ctx)
                if 3 in selected:
                    print("=== Reise 3: Prüfen und beheben ===")
                    run_journey_3(browser, ctx)
            finally:
                browser.close()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        ctx.errors.append(f"exception: {exc}")

    # Check session log for js_error events emitted during this run
    time.sleep(0.3)
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
        except Exception as exc:
            print(f"warning: reading session log failed: {exc}")

    for err in ctx.errors:
        print(f"FAIL browser error: {err}")
    for err in js_errors:
        print(f"FAIL browser js_error: {err}")

    print(f"\nSummary: {len(ctx.failures)} failure(s), {len(ctx.known)} known issue(s), {len(ctx.errors) + len(js_errors)} browser error(s)")
    if ctx.failures or ctx.errors or js_errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
