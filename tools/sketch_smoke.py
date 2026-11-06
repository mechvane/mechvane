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
    pg.mouse.click(sx(-30), sy(-15)); pg.mouse.click(sx(30), sy(-15)); pg.keyboard.up("Control"); pg.keyboard.press("Escape")
    pg.keyboard.down("Control"); pg.mouse.click(sx(0), sy(-35)); pg.mouse.click(sx(0), sy(5)); pg.keyboard.up("Control"); pg.wait_for_timeout(1200)
    pg.keyboard.press("Escape"); pg.keyboard.press("Escape")
    n0 = len(st()["curves"])
    pg.keyboard.press("t"); pg.mouse.move(sx(20), sy(-15)); pg.mouse.click(sx(20), sy(-15)); pg.wait_for_timeout(1500)
    hl = [(c["start_at"], c["end_at"]) for c in st()["curves"] if c["type"] == "line" and abs(c["start_at"][1] + 15) < 0.5 and abs(c["end_at"][1] + 15) < 0.5]
    if not (len(hl) == 1 and abs(hl[0][1][0]) < 0.5): fails.append("trim")
    print("trim: curves", n0, "->", len(st()["curves"]), "| horizontal:", [[[round(v, 1) for v in a], [round(v, 1) for v in e]] for a, e in hl])
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
    pg.keyboard.press("Escape"); pg.mouse.move(cx, cy + 330); pg.wait_for_timeout(300)
    pg.screenshot(path="/tmp/shots/12-stutzen-versatz-projizieren.png")
    pg.evaluate("fetch('api/sketch/cancel', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'})")
    print("errors:", errs, "| failed:", fails or "none")
    b.close()
sys.exit(1 if errs or fails else 0)
