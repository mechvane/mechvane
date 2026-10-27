"""Example models for the live demo and `mechvane ui --demo`."""

import json
from pathlib import Path

from . import bolted, links
from .documents import ASSEMBLY, PART

DATA = Path(__file__).resolve().parent / "data"


def bracket(ws):
    """A bracket whose countersink notches the wall (practice test 5, finding 8)."""
    part = ws.new(PART, "bracket")
    part.session.batch([
        {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 8, "corner": [0, 0, 0],
                                            "name": "BasePlate", "body_name": "Bracket"}},
        {"command": "solid.box", "params": {"length": 60, "width": 10, "height": 40, "corner": [0, 30, 8],
                                            "operation": "join", "name": "Wall"}},
        {"command": "solid.hole", "params": {"position": [18, 14, 8], "direction": [0, 0, -1],
                                             "clearance": "M6", "depth": 8, "name": "Hole"}},
        {"command": "solid.hole", "params": {"position": [42, 23, 8], "direction": [0, 0, -1],
                                             "clearance": "M6", "depth": 8, "type": "countersink",
                                             "cs_diameter": 13.7, "cs_angle": 90, "name": "CountersinkNearWall"}}])
    part.save()
    return part


def flange(ws):
    """The parametric flange from the reference corpus: sketches owned by their features."""
    part = ws.new(PART, "flange")
    cmds = json.loads((DATA / "flange.build.json").read_text(encoding="utf-8"))["commands"]
    part.session.batch(cmds)
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


DEMOS = [("bolted_plates", "Bolted connection (assembly)", bolted_plates),
         ("bracket", "Bracket with a design check finding", bracket),
         ("flange", "Parametric flange", flange)]


def build_all(ws):
    """Build every example in workspace ws and save it; returns the documents in DEMOS order."""
    return [build(ws) for _, _, build in DEMOS]

