"""Click test for the sketch Modify tools and Project Geometry (sketcher.js, step d): trim, offset with a typed
distance, fix, project a model edge. Needs a running UI on the smoke part:

    tools/ui_smoke.py --prepare /tmp/sk/part.solidcraft && python3 -m mechvane.ui /tmp/sk/part.solidcraft --port 8811 &
    <python with playwright> tools/sketch_smoke.py

Screenshots go to /tmp/shots/. Exit code 1 on a failed step or a page error."""
import glob, os, sys
from playwright.sync_api import sync_playwright
sh = sorted(glob.glob("/root/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
errs = []
os.makedirs("/tmp/shots", exist_ok=True)
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=sh[-1], args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1400, "height": 860}, device_scale_factor=2)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8811/"); pg.wait_for_timeout(4000)
    st = lambda: pg.evaluate("fetch('api/sketch/state').then(r=>r.json())")["state"]
    box = pg.locator("#viewport canvas").bounding_box(); cx, cy = box["x"] + box["width"]/2, box["y"] + box["height"]/2
    pg.keyboard.press("s"); pg.click(".sketch-plane-bar [data-plane=XY]"); pg.wait_for_timeout(2500)
    # scale: a line placed freely from 100 px right of the centre, 100 px down
    pg.keyboard.press("l"); pg.keyboard.down("Control"); pg.mouse.click(cx + 100, cy); pg.mouse.click(cx + 100, cy + 100); pg.keyboard.up("Control"); pg.wait_for_timeout(1200)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    l1 = st()["curves"][0]; mpp = (l1["start_at"][1] - l1["end_at"][1]) / 100; x0 = l1["start_at"][0] - 100 * mpp
    print("mm per px", round(mpp, 4), "x at centre", round(x0, 2))
    sx = lambda u: cx + (u - x0) / mpp
    sy = lambda v: cy - (v - l1["start_at"][1]) / mpp
    # crossing lines for trim
    pg.keyboard.press("l"); pg.keyboard.down("Control")
    pg.mouse.click(sx(-30), sy(-15)); pg.mouse.click(sx(30), sy(-15)); pg.keyboard.up("Control"); pg.wait_for_timeout(500); pg.keyboard.press("Escape")
    pg.keyboard.down("Control"); pg.mouse.click(sx(0), sy(-35)); pg.mouse.click(sx(0), sy(5)); pg.keyboard.up("Control"); pg.wait_for_timeout(1200)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    n0 = len(st()["curves"])
    pg.keyboard.press("t"); pg.mouse.move(sx(20), sy(-15)); pg.mouse.click(sx(20), sy(-15)); pg.wait_for_timeout(1500)
    hl = [(c["start_at"], c["end_at"]) for c in st()["curves"] if c["type"] == "line" and abs(c["start_at"][1] + 15) < 0.5 and abs(c["end_at"][1] + 15) < 0.5]
    if not (len(hl) == 1 and abs(hl[0][1][0]) < 0.5): fails.append("trim")
    print("trim: curves", n0, "->", len(st()["curves"]), "| horizontal:", [[[round(v, 1) for v in a], [round(v, 1) for v in e]] for a, e in hl])
    # trim loose end with only one intersection (removes the remaining piece up to the intersection)
    pg.mouse.move(sx(-20), sy(-15)); pg.mouse.click(sx(-20), sy(-15)); pg.wait_for_timeout(1500)
    hl2 = [(c["start_at"], c["end_at"]) for c in st()["curves"] if c["type"] == "line" and abs(c["start_at"][1] + 15) < 0.5 and abs(c["end_at"][1] + 15) < 0.5]
    if len(hl2) != 0: fails.append("trim_loose_end")
    print("trim loose end: remaining horizontal:", len(hl2))
    # offset the vertical line by a typed 5 to the right
    pg.keyboard.press("o"); pg.mouse.click(sx(0), sy(-25)); pg.mouse.move(sx(8), sy(-25)); pg.wait_for_timeout(300)
    pg.screenshot(path="/tmp/shots/11-versatz-vorschau.png")
    pg.keyboard.type("5"); pg.keyboard.press("Enter"); pg.wait_for_timeout(1500)
    n5 = sum(1 for c in st()["curves"] if c["type"] == "line" and abs(c["start_at"][0] - 5) < 0.01 and abs(c["end_at"][0] - 5) < 0.01)
    if n5 != 1: fails.append("offset")
    print("offset: lines at x=5:", sum(1 for c in st()["curves"] if c["type"] == "line" and abs(c["start_at"][0] - 5) < 0.01 and abs(c["end_at"][0] - 5) < 0.01))
    # fix the first line
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    pg.click('[data-sketch-tool="con:fix"]'); pg.mouse.click(sx(l1["start_at"][0]), sy(l1["start_at"][1] - 7)); pg.wait_for_timeout(1500)
    if not any(c.get("fixed") for c in st()["curves"]): fails.append("fix")
    print("fix:", [c["id"] for c in st()["curves"] if c.get("fixed")], pg.locator(".sketch-glyph", has_text="⚓").count(), "| status:", pg.locator("#status-indicator").inner_text()[:90])
    # project: the box's top edge at y = 25 (z = 10, a little larger in perspective)
    pg.keyboard.press("Escape"); pg.keyboard.press("p")
    nproj = len(st()["curves"])
    for dy in [0, 2, -2, 4, -4, 6, 8, 10, 12]:
        pg.mouse.click(sx(10), sy(25) - dy); pg.wait_for_timeout(1200)
        if len(st()["curves"]) > nproj:
            print("project hit at dy", dy); break
    c = st()["curves"]
    if len(c) <= nproj: fails.append("project")
    print("project: curves", nproj, "->", len(c), c[-1].get("start_at"), c[-1].get("end_at"), c[-1].get("construction"))
    # project an origin axis (#137): the X axis in the view, right of the box where no model edge competes
    pg.keyboard.press("Escape"); pg.keyboard.press("p"); pg.wait_for_timeout(300)
    nax = len(st()["curves"])
    for ddx in [0, 4, -4, 8]:
        pg.mouse.click(sx(55 + ddx), sy(0)); pg.wait_for_timeout(1200)
        if len(st()["curves"]) > nax:
            break
    ax = st()["curves"][nax:]
    ax_ok = len(ax) == 1 and ax[0]["type"] == "line" and abs(ax[0]["start_at"][1]) < 1e-6 and abs(ax[0]["end_at"][1]) < 1e-6
    if not ax_ok: fails.append("project_origin_axis")
    print("project origin axis:", [(c["type"], c.get("start_at"), c.get("end_at")) for c in ax], "ok:", ax_ok)
    # construction mode (#138): X with nothing selected; a drawn line and a projected edge are construction
    # (Create commands, as in SolidCraft); X again leaves the mode
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape"); pg.keyboard.press("x"); pg.wait_for_timeout(300)
    mode_text = pg.locator("#status-indicator").inner_text()
    pg.keyboard.press("l"); pg.keyboard.down("Control")
    pg.mouse.click(sx(-30), sy(-45)); pg.mouse.click(sx(30), sy(-45)); pg.keyboard.up("Control"); pg.wait_for_timeout(1200)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    cl = [c for c in st()["curves"] if c["type"] == "line" and abs(c["start_at"][1] + 45) < 0.5 and abs(c["end_at"][1] + 45) < 0.5]
    pg.keyboard.press("p"); npc = len(st()["curves"])
    for dy in [0, 2, -2, 4, -4, 6, 8, 10, 12]:
        pg.mouse.click(sx(10), sy(-25) + dy); pg.wait_for_timeout(1200)
        if len(st()["curves"]) > npc:
            break
    pc = st()["curves"][npc:]
    pg.keyboard.press("Escape"); pg.keyboard.press("x"); pg.wait_for_timeout(300)
    left_mode = "Construction mode" not in pg.locator("#status-indicator").inner_text()
    cons_ok = (left_mode and "Construction" in mode_text and len(cl) == 1 and cl[0].get("construction") is True
               and len(pc) >= 1 and all(c.get("construction") is True for c in pc))
    if not cons_ok: fails.append("construction_mode")
    print("construction mode:", repr(mode_text[:60]), "left:", left_mode, "line:", [c.get("construction") for c in cl],
          "projected:", [c.get("construction") for c in pc], "ok:", cons_ok)
    pg.keyboard.press("Escape"); pg.mouse.move(cx, cy + 330); pg.wait_for_timeout(300)
    pg.screenshot(path="/tmp/shots/12-stutzen-versatz-projizieren.png")

    # Box selection test (#67): rectangle plus circle
    # Window left-to-right encloses only circle -> 1 element
    # Crossing right-to-left across rectangle edge -> that line
    # Delete removes the selection
    # Draw rectangle at [-40, -20] to [-10, 10]
    pg.keyboard.press("r"); pg.keyboard.down("Control")
    pg.mouse.click(sx(-40), sy(-20)); pg.mouse.click(sx(-10), sy(10))
    pg.keyboard.up("Control"); pg.wait_for_timeout(800)
    pg.keyboard.press("Escape")
    # Draw circle at center [30, 0], radius 12
    pg.keyboard.press("c"); pg.keyboard.down("Control")
    pg.mouse.click(sx(30), sy(0)); pg.mouse.click(sx(42), sy(0))
    pg.keyboard.up("Control"); pg.wait_for_timeout(800)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    pg.wait_for_timeout(500)

    curves = st()["curves"]
    circ = [c for c in curves if c["type"] == "circle"]
    top_line = [c for c in curves if c["type"] == "line" and abs(c["start_at"][1] - 10) < 0.5 and abs(c["end_at"][1] - 10) < 0.5]
    print("box selection setup: curves", len(curves), "circle:", [c["id"] for c in circ], "top line:", [c["id"] for c in top_line])

    # 1. Window selection (left to right): only around the circle
    pg.mouse.move(sx(15), sy(16))
    pg.mouse.down()
    pg.mouse.move(sx(45), sy(-16))
    pg.mouse.up()
    pg.wait_for_timeout(600)
    picked_win = pg.evaluate("window.mechvaneSketchPicked ? window.mechvaneSketchPicked() : []")
    win_ok = len(picked_win) == 1 and bool(circ) and picked_win[0]["id"] == circ[0]["id"]
    if not win_ok: fails.append("box_window_circle")
    print("box window circle:", len(picked_win), [p["id"] for p in picked_win], "ok:", win_ok)

    # 2. Crossing selection (right to left): across the rectangle top edge
    pg.mouse.move(sx(-20), sy(15))
    pg.mouse.down()
    pg.mouse.move(sx(-30), sy(5))
    pg.mouse.up()
    pg.wait_for_timeout(600)
    picked_cross = pg.evaluate("window.mechvaneSketchPicked ? window.mechvaneSketchPicked() : []")
    cross_ok = len(picked_cross) == 1 and bool(top_line) and picked_cross[0]["id"] == top_line[0]["id"]
    if not cross_ok: fails.append("box_crossing_line")
    print("box crossing line:", len(picked_cross), [p["id"] for p in picked_cross], "ok:", cross_ok)

    # 3. Delete removes the selection
    n_before = len(st()["curves"])
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(1000)
    n_after = len(st()["curves"])
    picked_after = pg.evaluate("window.mechvaneSketchPicked ? window.mechvaneSketchPicked() : []")
    del_ok = (n_after == n_before - 1) and not any(c["id"] == top_line[0]["id"] for c in st()["curves"]) and len(picked_after) == 0
    if not del_ok: fails.append("box_delete")
    print("box delete:", n_before, "->", n_after, "remaining:", [c["id"] for c in st()["curves"]], "ok:", del_ok)

    pg.screenshot(path="/tmp/shots/13-fensterauswahl.png")
    pg.click('[data-sketch-action="cancel"]'); pg.wait_for_timeout(1500)

    # Sketch on planar face (#68): auto-project 4 boundary edges of top face, snap a line from a projected corner
    pg.keyboard.press("s"); pg.wait_for_timeout(400)
    for dx, dy in [(-60, -20), (60, -20), (-80, 0), (0, -35), (-40, -40), (40, -40)]:
        pg.mouse.click(cx + dx, cy + dy); pg.wait_for_timeout(1200)
        if pg.locator(".sketch-plane-bar").count() == 0:
            break
    pg.wait_for_timeout(1000)
    face_st = st()
    proj_lines = [c for c in face_st.get("curves", []) if c["type"] == "line" and c.get("link")]
    if len(proj_lines) != 4:
        fails.append("face_autoproject_4_lines")
    print("face auto-project: projected lines:", len(proj_lines), [c["id"] for c in proj_lines])

    # Snap a line starting from the projected corner at [-40, -25]
    pg.keyboard.press("l")
    pg.mouse.move(sx(-40), sy(-25)); pg.wait_for_timeout(300)
    snap_vis = pg.locator(".sketch-snap").is_visible()
    pg.mouse.click(sx(-40), sy(-25))
    pg.mouse.move(sx(-10), sy(0)); pg.wait_for_timeout(200)
    pg.mouse.click(sx(-10), sy(0)); pg.wait_for_timeout(1200)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    face_st2 = st()
    drawn = [c for c in face_st2.get("curves", []) if c["type"] == "line" and not c.get("link")]
    coinc = [k for k in face_st2.get("constraints", []) if k.get("type") == "coincident"]
    snap_ok = (snap_vis and len(drawn) == 1
               and abs(drawn[0]["start_at"][0] + 40) < 1e-3 and abs(drawn[0]["start_at"][1] + 25) < 1e-3
               and len(coinc) >= 1)
    if not snap_ok:
        fails.append("face_snap_corner")
    print("face corner snap: visible:", snap_vis, "drawn:", [c["start_at"] for c in drawn], "coincident:", len(coinc), "ok:", snap_ok)
    pg.screenshot(path="/tmp/shots/14-flaechenkanten-projiziert.png")
    # command dialog in the sketch (#128): Ctrl+K, sketch.delete, the drawn line from the sketch's ids, OK removes
    # it as one step of the sketch's undo, Ctrl+Z brings it back
    n_cmd = len(st()["curves"])
    target = drawn[0]["id"] if drawn else None
    pg.keyboard.press("Control+k")
    pg.wait_for_selector(".cmd-palette:not([hidden]) .cmd-results li", timeout=60000)
    pg.keyboard.type("sketch.delete")
    pg.wait_for_selector(".cmd-results li.active .cmd-id:text-is('sketch.delete')", timeout=10000)
    pg.keyboard.press("Enter")
    pg.wait_for_selector(".cmd-dialog", timeout=30000)
    offered_ids = [o.get_attribute("value") for o in pg.locator('.cmd-field[data-name="entities"] datalist option').all()]
    # part 2: Pick takes the line from a click in the sketch; Preview draws the result and changes nothing
    pg.click('.cmd-field[data-name="entities"] .cmd-skpick')
    pg.mouse.click(sx(-25), sy(-12.5)); pg.wait_for_timeout(300)
    picked_val = pg.locator('.cmd-field[data-name="entities"] [data-field]').input_value()
    pg.click('.cmd-field[data-name="entities"] .cmd-skpick')  # Pick off again
    if picked_val.strip() != (target or ""):
        pg.locator('.cmd-field[data-name="entities"] [data-field]').fill(target or "")
    pg.click(".cmd-dialog .cmd-preview"); pg.wait_for_timeout(1200)
    preview_text = pg.locator(".cmd-dialog .feature-delta").inner_text()
    n_preview = len(st()["curves"])
    preview_ok = "Preview: drawn" in preview_text and n_preview == n_cmd
    pg.click(".cmd-dialog .feature-ok"); pg.wait_for_timeout(1500)
    n_del = len(st()["curves"])
    pg.mouse.move(cx, cy + 300); pg.keyboard.press("Control+z"); pg.wait_for_timeout(1500)
    n_back = len(st()["curves"])
    cmd_ok = (target in offered_ids and picked_val.strip() == target and preview_ok and n_del == n_cmd - 1 and n_back == n_cmd
              and pg.locator(".cmd-dialog").count() == 0)
    if not cmd_ok: fails.append("command_dialog_in_sketch")
    print("command dialog in sketch: ids", offered_ids[:6], "| deleted", n_cmd, "->", n_del, "| ctrl+z ->", n_back,
          "| pick", repr(picked_val), "| preview", repr(preview_text[:40]), "ok:", cmd_ok)

    pg.evaluate("fetch('api/sketch/cancel', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'})")
    # #134: with a sketch open, the Model page link finishes the sketch first, then opens the Model page
    pg.reload(); pg.wait_for_timeout(4000)
    pg.keyboard.press("s"); pg.click(".sketch-plane-bar [data-plane=XY]"); pg.wait_for_timeout(2500)
    pg.keyboard.press("l"); pg.keyboard.down("Control")
    pg.mouse.click(sx(-20), sy(40)); pg.mouse.click(sx(20), sy(40)); pg.keyboard.up("Control"); pg.wait_for_timeout(1200)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    was_open = pg.evaluate("fetch('api/sketch/state').then(r=>r.json())").get("active")
    pg.evaluate("document.getElementById('mode-model').click()")
    try:
        pg.wait_for_url("**/model**", timeout=20000)
        on_model = True
    except Exception:
        on_model = False
    after = pg.evaluate("fetch('/api/sketch/state').then(r=>r.json())") if on_model else {}
    model_ok = bool(was_open) and on_model and not after.get("active")
    if not model_ok: fails.append("model_mode_with_sketch")
    print("model mode with sketch open:", "was open", was_open, "| model page", on_model, "| sketch active after", after.get("active"), "ok:", model_ok)
    print("errors:", errs, "| failed:", fails or "none")
    b.close()
sys.exit(1 if errs or fails else 0)
