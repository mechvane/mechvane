#!/usr/bin/env python3
"""Render the README demo: a joint jumps to the wrong hole after a part edit, update_links repairs it.

Usage: python3 tools/demo_update_links.py [out_dir]   (default docs/media, needs solidcraft-cli and Pillow)
Writes update_links.gif and one PNG per step."""

import base64
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from mechvane import links  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402

W, H, BAR = 720, 440, 64
CAMERA = {"target": [0, 0, 10], "yaw": 30, "pitch": 32, "distance": 100}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render(asm, path):
    r = asm.session.tool("screenshot", {"source": "model", "width": W, "height": H, "camera": CAMERA,
                                        "grid": False, "axes": False})
    path.write_bytes(base64.b64decode(r["images"][0]["image"]))


def caption(png, step, title, text, accent):
    img = Image.open(png).convert("RGB")
    out = Image.new("RGB", (W, H + BAR), "white")
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    d.rectangle([0, H, W, H + BAR], fill=(245, 246, 248))
    d.rectangle([0, H, 8, H + BAR], fill=accent)
    d.text((24, H + 10), f"{step}  {title}", font=ImageFont.truetype(FONT_BOLD, 19), fill=(20, 20, 20))
    d.text((24, H + 37), text, font=ImageFont.truetype(FONT, 15), fill=(70, 70, 70))
    out.save(png)
    return out


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "media"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        try:
            plate = ws.new(PART, "plate")
            plate.session.batch([
                {"command": "solid.box", "params": {"length": 80, "width": 40, "height": 6, "corner": [-40, -20, 0],
                                                    "operation": "new", "body_name": "Plate"}},
                {"command": "solid.cylinder", "params": {"diameter": 8, "height": 8, "base": [20, 0, -1],
                                                         "operation": "cut", "name": "Bore"}}])
            plate.save()

            asm = ws.new(ASSEMBLY, "demo")
            s = asm.session
            s.cmd("component.insert_design", {"path": str(plate.path), "name": "Plate"})
            s.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": True})
            s.batch([{"command": "solid.cylinder", "params": {"diameter": 8, "height": 30, "base": [0, 60, 0],
                                                              "operation": "new", "body_name": "PinBody"}},
                     {"command": "component.create", "params": {"name": "Pin", "parent": "root", "activate": False}},
                     {"command": "component.move_bodies", "params": {"bodies": ["PinBody"], "component": "Pin"}}])
            params = {"type": "rigid", "name": "PinInBore", "flip": False,
                      "a": {"occurrence": "Plate:1", "circle": [24, 0, 6]},
                      "b": {"occurrence": "Pin:1", "circle": [4, 60, 0]}}
            s.cmd("joint.create", params)
            links.record(ws, asm, "PinInBore", params)
            asm.save()

            frames = []
            p1 = out_dir / "update_links_1.png"
            render(asm, p1)
            frames.append(caption(p1, "1", "Pin joined to the bore of a separate part file",
                                  "Parts and assemblies are separate files, joints refer to part faces.",
                                  (60, 120, 200)))

            # Add a same-size hole earlier in the part's history (tangency-labs/solidcraft#3330).
            plate.session.cmd("timeline.roll_to", {"position": 1})
            plate.session.cmd("solid.cylinder", {"diameter": 8, "height": 8, "base": [-20, 0, -1],
                                                 "operation": "cut", "name": "Bore0"})
            plate.session.cmd("timeline.roll_to", {})
            plate.save()
            r = links.update_links(ws, asm)
            moved = [w for w in r["warnings"] if w["status"] == "moved"]
            p2 = out_dir / "update_links_2.png"
            render(asm, p2)
            frames.append(caption(p2, "2", "Part edited: a second bore of the same size",
                                  "After reloading, the joint silently jumps to the new bore. "
                                  + ("Mechvane reports it." if moved else ""),
                                  (210, 70, 60)))

            links.update_links(ws, asm, repair_moved=True)
            p3 = out_dir / "update_links_3.png"
            render(asm, p3)
            frames.append(caption(p3, "3", "update_links puts it back",
                                  "Mechvane remembers the face by its history name and repairs the joint.",
                                  (50, 150, 90)))
        finally:
            ws.close_all()

    gif = out_dir / "update_links.gif"
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=[2600, 3200, 3200], loop=0,
                   optimize=True)
    print(f"wrote {gif} ({gif.stat().st_size // 1024} KB), moved reported: {bool(moved)}")


if __name__ == "__main__":
    main()
