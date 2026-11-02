"""Click through the workspace in a headless browser: measure two points, open a section, Esc, then
walk right from the centre until a click lands on an edge and the readout measures it; in a part also
the Fillet dialog (preview, Esc, OK, edit by double-click, Ctrl+Z).

    <python with playwright> tools/ui_smoke.py [url] [out_dir]   (default http://127.0.0.1:8799/, screenshots in .)

Start the UI first (`python3 -m mechvane ui <part> --no-browser --port 8799`). Needs the playwright
package; the browser is taken from ~/.cache/ms-playwright (chrome-headless-shell) if installed there.
"""
import glob
import os
import sys

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8799/"
out = sys.argv[2] if len(sys.argv) > 2 else "."
shells = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=shells[-1] if shells else None,
                                 args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1300, "height": 750})
    errors = []
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
    edge = ""
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
    new_part = "skipped (no folder)"
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
    fillet = "skipped (assembly or static demo)"
    fillet_ok = True
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
    browser.close()
print("fillet:", fillet)
print("new part:", new_part)
print("measure:", measured.replace("\n", " | "))
print("section:", section)
print("esc closes:", closed, "page errors:", errors)
print("edge:", edge.replace("\n", " | ") or "none found")
sys.exit(0 if "Distance" in measured and "Section" in section and closed and edge and new_part_ok and fillet_ok
         and not errors else 1)
