"""Example models the checks build (formerly mechvane/examples.py, the web UI's demo models, #232)."""

import json
from pathlib import Path

from mechvane import bolted, links
from mechvane.documents import ASSEMBLY, PART

FLANGE = Path(__file__).resolve().parents[1] / "reference" / "flansch.build.json"


def flange(ws):
    """The parametric flange from the reference corpus: sketches owned by their features."""
    part = ws.new(PART, "flange")
    part.session.batch(json.loads(FLANGE.read_text(encoding="utf-8"))["commands"])
    part.save()
    return part


def bolted_plates(ws):
    """Two plates joined by four M6 cap screws with washers and nuts, holes drilled in both part files."""
    top = ws.new(PART, "top_plate")
    top.session.cmd("solid.box", {"length": 80, "width": 50, "height": 10, "corner": [-40, -25, 0],
                                  "body_name": "TopPlate", "name": "Plate"})
    top.save()
    base = ws.new(PART, "base_plate")
    base.session.cmd("solid.box", {"length": 80, "width": 50, "height": 8, "corner": [-40, -25, 0],
                                   "body_name": "BasePlate", "name": "Plate"})
    base.save()
    asm = ws.new(ASSEMBLY, "bolted_plates")
    links.insert(ws, asm, top.path, name="TopPlate", grounded=True)
    links.insert(ws, asm, base.path, name="BasePlate", translate=[0, 0, -8], grounded=True)
    asm.save()
    bolted.bolted_connection(ws, "bolted_plates", placement={"position": [-28, -15, 10], "direction": [0, 0, -1]},
                             size="M6", pattern={"type": "rectangular", "count": [2, 2], "spacing": [56, 30]})
    asm.save()
    return asm
