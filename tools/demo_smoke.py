"""Click through the feature dialogs of the static live demo (demo_kernel.js) in a headless browser:
fillet with preview, OK, edit by double-click, Ctrl+Z / Ctrl+Y, hole with the tables, extrude hint, a sketch.

    tools/build_demo_site.py /tmp/demosite && (cd /tmp/demosite && python3 -m http.server 8811 &)
    <python with playwright> tools/demo_smoke.py [url]   (default http://localhost:8811/demo/?demo=bracket)

The first dialog starts SolidCraft in the page: about 10 s headless. Exit code 1 on a failed step or page error.
"""
import glob, os, sys, time
from playwright.sync_api import sync_playwright
shells = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=shells[-1], args=["--use-gl=swiftshader","--enable-unsafe-swiftshader"])
    p = b.new_page(viewport={"width":1400,"height":850})
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
    print("findings:", p.locator("#findings-summary").inner_text()[:120], "| undo:", p.locator("#btn-undo").get_attribute("title"))
    p.dblclick('.tree-row[data-feature="Fillet1"]'); p.wait_for_selector(".feature-dialog-title:has-text('Edit')", timeout=60000)
    print("edit:", p.locator(".feature-pick-count").inner_text(), p.input_value('input[name="radius"]'))
    p.keyboard.press("Escape"); p.wait_for_timeout(500)
    p.keyboard.press("Control+z"); p.wait_for_function("!document.querySelector('#tree-content').innerText.includes('Fillet1')", timeout=60000)
    print("undo ok |", p.locator("#btn-redo").get_attribute("title"))
    p.keyboard.press("Control+y"); p.wait_for_function("document.querySelector('#tree-content').innerText.includes('Fillet1')", timeout=60000)
    print("ctrl+y redo ok")
    # hole with the tables from hole_sizes.json
    p.keyboard.press("h"); p.wait_for_timeout(800)
    p.mouse.click(box["x"]+box["width"]*0.45, box["y"]+box["height"]*0.72)
    p.wait_for_function("/Volume|⚠/.test(document.querySelector('.feature-delta')?.textContent || '') || !document.querySelector('.feature-error')?.hidden", timeout=60000)
    print("hole:", p.locator(".feature-note").inner_text(), "|", p.locator(".feature-delta").inner_text(), p.locator(".feature-error").inner_text())
    p.keyboard.press("Escape")
    p.keyboard.press("e"); p.wait_for_timeout(1500); print("extrude:", p.locator(".feature-pick-count").inner_text())
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
    print("\n".join(errs) or "no errors")
    b.close()
sys.exit(1 if errs else 0)
