"""Click through the feature dialogs of the static live demo (demo_kernel.js) in a headless browser:
fillet with preview, OK, edit by double-click, Ctrl+Z / Ctrl+Y, hole with the tables, extrude hint, a sketch,
the command dialog (Ctrl+K, #128) and the recorded agent session (#124: chat lines, the model changes, the check is green at the end, Reset demo).

    tools/build_demo_site.py /tmp/demosite --with-demo && (cd /tmp/demosite && python3 -m http.server 8811 &)
    <python with playwright> tools/demo_smoke.py [url]   (default http://localhost:8811/demo/?demo=bracket)

The first dialog starts SolidCraft in the page: about 10 s headless. Exit code 1 on a failed step or page error.
"""
import glob, os, sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heavy_lock import hold
hold("demo_smoke")  # one heavy run at a time (audit 2026-11-16, A5)
shells = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=shells[-1], args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
    p = b.new_page(viewport={"width":1400,"height":850})
    if os.environ.get("DEMO_SLOW"):  # emulate a slow CI runner: CPU throttled by this factor
        p.context.new_cdp_session(p).send("Emulation.setCPUThrottlingRate", {"rate": float(os.environ["DEMO_SLOW"])})
    errs=[]
    p.on("pageerror", lambda e: errs.append("pageerror "+str(e)))
    p.on("console", lambda m: errs.append("console "+m.text[:200]) if m.type=="error" and "400" not in m.text else None)
    p.goto(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8811/demo/?demo=bracket", wait_until="load"); p.wait_for_timeout(4000)
    tree = lambda: p.locator("#tree-content").inner_text().replace("\n"," | ")
    status = lambda: p.locator("#status-indicator").inner_text()
    print("fillet enabled:", p.locator("#btn-fillet").is_enabled(), "| undo visible:", p.locator("#btn-undo").is_visible())
    p.click("#btn-fillet"); p.wait_for_timeout(300)
    box = p.locator("#viewport canvas").bounding_box(); cx, cy = box["x"]+box["width"]/2, box["y"]+box["height"]/2
    for dy in range(0, 300, 6):
        p.mouse.click(cx, cy - dy); p.wait_for_timeout(40)
        if "selected" in p.locator(".feature-pick-count").inner_text(): break
    print("picked:", p.locator(".feature-pick-count").inner_text(), "| status:", status())
    t=time.time()
    p.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '') || !document.querySelector('.feature-error')?.hidden", timeout=180000)
    print(f"preview after {time.time()-t:.1f}s:", p.locator(".feature-delta").inner_text(), "|", p.locator(".feature-error").inner_text(), "| status:", status())
    p.fill('.feature-dialog input[name="radius"]', "3"); t=time.time()
    p.wait_for_function("/Volume/.test(document.querySelector('.feature-delta')?.textContent || '')", timeout=60000)
    print(f"r3 after {time.time()-t:.1f}s:", p.locator(".feature-delta").inner_text())
    p.click(".feature-ok"); t=time.time()
    p.wait_for_function("document.querySelector('#tree-content').innerText.includes('Fillet1')", timeout=120000)
    print(f"ok after {time.time()-t:.1f}s:", status(), "|", tree()[-120:])
    # #121 review: the first step in the demo marks only what it added, not every feature (the precomputed tree is signed
    # by the server, the kernel signs its own)
    p.wait_for_selector("#step-changes", timeout=60000)
    bar = p.locator("#step-changes").inner_text().replace("\n", " ")
    print("last step:", bar)
    assert "+ Fillet1" in bar and "~" not in bar, f"first step marks more than the new feature: {bar!r}"
    print("findings:", p.locator("#findings-summary").inner_text()[:120], "| undo:", p.locator("#btn-undo").get_attribute("title"))
    p.dblclick('.tree-row[data-feature="Fillet1"]'); p.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=60000)
    print("edit:", p.locator(".feature-pick-count").inner_text(), p.input_value('input[name="radius"]'))
    p.keyboard.press("Escape"); p.wait_for_timeout(500)
    p.keyboard.press("Control+z")
    try:
        p.wait_for_function("!document.querySelector('#tree-content').innerText.includes('Fillet1')", timeout=60000)
    except Exception:
        print("UNDO FAILED | status:", status(), "| focus:", p.evaluate("document.activeElement && (document.activeElement.tagName + ' ' + (document.activeElement.name || document.activeElement.id || document.activeElement.className))"),
              "| props:", p.locator("#properties").inner_text()[:200].replace("\n", " / ") if p.locator("#properties").count() else "-",
              "| undo:", p.locator("#btn-undo").get_attribute("title"), p.locator("#btn-undo").is_disabled())
        raise
    print("undo ok |", p.locator("#btn-redo").get_attribute("title"))
    p.keyboard.press("Control+y"); p.wait_for_function("document.querySelector('#tree-content').innerText.includes('Fillet1')", timeout=60000)
    print("ctrl+y redo ok")
    # hole with the tables from hole_sizes.json
    p.keyboard.press("h"); p.wait_for_selector(".feature-dialog-title:has-text('Hole')", timeout=60000)  # wait for the state, not a time
    p.mouse.click(box["x"]+box["width"]*0.45, box["y"]+box["height"]*0.72)
    p.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '') || !document.querySelector('.feature-error')?.hidden", timeout=60000)
    print("hole:", p.locator(".feature-note").inner_text(), "|", p.locator(".feature-delta").inner_text(), p.locator(".feature-error").inner_text())
    p.keyboard.press("Escape")
    p.keyboard.press("e"); p.wait_for_selector(".feature-dialog-title:has-text('Extrude')", timeout=60000)
    p.wait_for_timeout(500); print("extrude:", p.locator(".feature-pick-count").inner_text())
    p.keyboard.press("Escape"); p.wait_for_timeout(500)
    # Sketch environment on the demo kernel: S, XZ, a 50 x 20 rectangle typed at the cursor, Enter finishes,
    # the sketch is one step for Ctrl+Z
    box = p.locator("#viewport canvas").bounding_box(); cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    p.keyboard.press("s"); p.click(".sketch-plane-bar [data-plane=XZ]")
    p.wait_for_selector('.ribbon-tab[data-tab="sketch"].active', timeout=60000); p.wait_for_timeout(500)
    p.keyboard.press("r"); p.mouse.click(cx - 150, cy + 150); p.mouse.move(cx + 50, cy + 50)
    p.keyboard.type("50"); p.keyboard.press("Tab"); p.keyboard.type("20"); p.keyboard.press("Enter"); p.wait_for_timeout(3000)
    dims = sorted(p.locator(".sketch-dim").all_inner_texts())
    p.keyboard.press("Escape"); p.keyboard.press("Enter")
    p.wait_for_function("document.querySelector('.ribbon-tab[data-tab=\"3d-model\"]').classList.contains('active')", timeout=60000)
    p.wait_for_function("document.querySelector('#tree-content').innerText.includes('Sketch1')", timeout=60000)
    p.keyboard.press("Control+z"); p.wait_for_function("!document.querySelector('#tree-content').innerText.includes('Sketch1')", timeout=60000)
    print("sketch:", dims, "finished and undone")
    if dims != ["20", "50"]:
        errs.append(f"sketch: dimensions {dims}, expected 20 and 50")
    # #128: the general command dialog on the demo kernel: Ctrl+K, solid.chamfer, Pick an edge in the view, OK adds
    # the chamfer as one undo step, Ctrl+Z takes it back; a command that only reads leaves no undo entry; a command
    # with Mechvane's own handler says it is not in the live demo
    tree_before = p.locator("#tree-content").inner_text()
    def open_cmd(cid):
        p.keyboard.press("Control+k")
        p.wait_for_selector(".cmd-palette:not([hidden]) .cmd-results li", timeout=60000)
        p.keyboard.type(cid)
        p.wait_for_selector(f".cmd-results li.active .cmd-id:text-is('{cid}')", timeout=5000)
        p.keyboard.press("Enter")
    open_cmd("solid.chamfer"); p.wait_for_selector(".cmd-dialog", timeout=60000)
    edges = p.locator('.cmd-field[data-name="edges"]')
    p.locator('.cmd-field[data-name="distance"] [data-field]').fill("0.5")
    box = p.locator("#viewport canvas").bounding_box(); cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    # walk down from the centre (the fillet step above rounded the edges above it) and try each picked edge: a
    # smooth edge (between a face and a fillet) is refused by SolidCraft, the next sharp one takes the chamfer
    picked, tried, cmd_err, added = "", set(), "", False
    for dy in range(0, int(box["height"] / 2) - 10, 6):
        if len(tried) >= 6:
            break
        edges.locator("textarea").fill("")
        if not p.locator(".cmd-pick.active").count():
            edges.locator(".cmd-pick").click(); p.wait_for_selector(".cmd-pick.active", timeout=5000)
        p.mouse.click(cx, cy + dy); p.wait_for_timeout(50)
        picked = edges.locator("textarea").input_value()
        if not picked or picked in tried:
            continue
        tried.add(picked)
        p.click(".cmd-dialog .feature-ok")
        p.wait_for_function("document.querySelector('#tree-content')?.textContent.includes('Chamfer')"
                            " || document.querySelector('.cmd-dialog .feature-error')?.hidden === false", timeout=60000)
        added = "Chamfer" in p.locator("#tree-content").inner_text()
        cmd_err = p.locator(".cmd-dialog .feature-error").inner_text() if p.locator(".cmd-dialog").count() else ""
        if added:
            break
        open_cmd("solid.chamfer"); p.wait_for_selector(".cmd-dialog", timeout=60000)
        edges = p.locator('.cmd-field[data-name="edges"]')
        p.locator('.cmd-field[data-name="distance"] [data-field]').fill("0.5")
    # the Undo title after the chamfer: from a history poll after it (every 4 s), not one still under way
    if added:
        p.wait_for_function("/chamfer/i.test(document.getElementById('btn-undo')?.title || '')", timeout=15000)
    undo_title = p.locator("#btn-undo").get_attribute("title")
    open_cmd("parameters.list"); p.wait_for_selector(".cmd-dialog", timeout=60000)
    p.click(".cmd-dialog .feature-ok")
    # the read ran (its result is shown), then two history polls later Undo still names the chamfer
    p.wait_for_function("(document.querySelector('.cmd-dialog .cmd-result')?.textContent || '').trim().length > 0", timeout=60000)
    p.wait_for_timeout(8500)
    read_only = p.locator("#btn-undo").get_attribute("title") == undo_title
    p.click(".cmd-dialog .feature-cancel"); p.wait_for_function("!document.querySelector('.cmd-dialog')", timeout=10000)
    p.keyboard.press("Control+k"); p.wait_for_selector(".cmd-palette:not([hidden]) .cmd-results li", timeout=60000)
    p.fill(".cmd-palette input", "timeline.rename")
    # offered commands come first in the list, so it is clicked rather than the first row taken
    p.locator(".cmd-results li:has(.cmd-id:text-is('timeline.rename'))").click(timeout=5000)
    try:
        p.wait_for_function("/not in the live demo/.test(document.querySelector('.cmd-palette-note')?.textContent || '')", timeout=5000)
        routed = True
    except Exception:
        routed = False
    p.keyboard.press("Escape")
    if added:  # only then: otherwise Undo would take back an earlier step; the button, as the focus may still be in
        # the closed search box, where Ctrl+Z belongs to the text
        p.click("#btn-undo")
        p.wait_for_function("t => document.querySelector('#tree-content')?.innerText === t", arg=tree_before, timeout=60000)
    print(f"command dialog: picked {picked!r}, ok adds: {added} {cmd_err!r}, read-only no undo entry: {read_only}, "
          f"routed refused: {routed}, undo ok")
    if not (picked and added and read_only and routed):
        errs.append(f"command dialog: picked {picked!r} added {added} {cmd_err!r} read-only {read_only} routed {routed}")
    # #124: the recorded agent session plays in a fresh page (?replay=1 starts it), from precomputed states
    r = b.new_page(viewport={"width": 1400, "height": 850})
    if os.environ.get("DEMO_SLOW"):
        r.context.new_cdp_session(r).send("Emulation.setCPUThrottlingRate", {"rate": float(os.environ["DEMO_SLOW"])})
    r.on("pageerror", lambda e: errs.append("replay pageerror " + str(e)))
    url = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8811/demo/?demo=bracket").split("?")[0]
    r.goto(url + "?demo=bracket&replay=1", wait_until="load")
    r.wait_for_selector(".replay-btn:has-text('Watch again')", timeout=180000)
    lines = r.locator(".chat-log li").all_inner_texts()
    bar = r.locator("#step-changes").inner_text().replace("\n", " ") if r.locator("#step-changes").count() else ""
    summary = r.locator("#findings-summary").inner_text()
    print(f"replay: {len(lines)} chat lines | {bar} | {summary[:60]}")
    if not (lines and "design check fails" in lines[0] and "run" in lines and lines[-1].startswith("✓ Changed")):
        errs.append(f"replay: chat lines {lines[:3]} … {lines[-1:]}")
    if "~ Hole" not in bar:
        errs.append(f"replay: the model did not change (last step {bar!r})")
    if "OK" not in summary:
        errs.append(f"replay: check not green at the end: {summary!r}")
    # started again from the top bar after the end: from the example as published, so the hole moves again
    r.click("#btn-replay")
    r.wait_for_function("!/~ Hole/.test(document.querySelector('#step-changes')?.textContent || '')", timeout=60000)
    r.wait_for_function("/~ Hole/.test(document.querySelector('#step-changes')?.textContent || '')", timeout=180000)
    r.wait_for_selector(".replay-btn:has-text('Watch again')", timeout=180000)
    print("replay again from the top bar ok")
    r.click(".replay-btn:has-text('Reset demo')")
    r.wait_for_function("/FAIL/.test(document.querySelector('#findings-summary').textContent)", timeout=60000)
    print("replay reset ok")
    print("\n".join(errs) or "no errors")
    b.close()
sys.exit(1 if errs else 0)
