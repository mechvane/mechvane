"""Click through the Check page in a headless browser: measure two points, open a section, Esc, then
walk right from the centre until a click lands on an edge and the readout measures it.

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
    page.goto(url)
    page.wait_for_timeout(5000)
    box = page.locator("#viewport canvas").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.click("text=Measure")
    for dx, dy in ((-150, -60), (150, 40)):
        page.mouse.click(cx + dx, cy + dy)
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
    browser.close()
print("measure:", measured.replace("\n", " | "))
print("section:", section)
print("esc closes:", closed, "page errors:", errors)
print("edge:", edge.replace("\n", " | ") or "none found")
sys.exit(0 if "Distance" in measured and "Section" in section and closed and edge and not errors else 1)
