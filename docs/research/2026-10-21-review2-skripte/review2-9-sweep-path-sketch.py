#!/usr/bin/env python3
"""Reproduction for Finding 9: sketch_rule.references ignores path_sketch in solid.sweep."""
from mechvane.solidcraft import Session
from mechvane import sketch_rule, tree

s = Session()
try:
    s.batch([
        {"command": "sketch.create", "params": {"plane": "XY", "name": "Profile"}},
        {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 2}},
        {"command": "sketch.finish", "params": {}},
        {"command": "sketch.create", "params": {"plane": "XZ", "name": "SweepPath"}},
        {"command": "sketch.line", "params": {"points": [[0, 0], [0, 20]]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.sweep", "params": {"sketch": "Profile", "path_sketch": "SweepPath", "path": ["l1"], "name": "Sweep1"}},
    ])

    # 1. Check consumers reported by sketch_rule
    cons = sketch_rule.consumers(s)
    print(f"Consumers: {cons}")
    # SweepPath is used by Sweep1, but consumers reports empty list []!
    assert cons.get("SweepPath") == [], f"Expected SweepPath to be ignored, got {cons.get('SweepPath')}"

    # 2. Check owners
    own = sketch_rule.owners(cons)
    print(f"Owners: {own}")
    assert "SweepPath" not in own, "SweepPath should have been owned by Sweep1"

    # 3. Check browser tree
    t = tree.part_tree(s)
    # SweepPath appears at root level rather than nested under Sweep1
    root_names = [f["name"] for f in t["features"] if f.get("name")]
    print(f"Root browser features: {root_names}")
    assert "SweepPath" in root_names, "SweepPath incorrectly placed at root level"

    print("CONFIRMED: sketch_rule.references ignores path_sketch; SweepPath ownership is broken!")
finally:
    s.close()
