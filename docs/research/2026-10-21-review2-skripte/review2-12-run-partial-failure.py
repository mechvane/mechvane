#!/usr/bin/env python3
"""Reproduction for Finding 12: server.py:run commits commands but raises error if sketch_rule fails."""
import shutil
import tempfile
from unittest.mock import patch
from mechvane.documents import Workspace, PART
from mechvane import server

d = tempfile.mkdtemp()
try:
    server.ws = Workspace(d)
    doc = server.ws.new(PART, "test_part")
    doc.save()

    # We mock sketch_rule.enforce to simulate "sketch rule did not settle" or unexpected error
    with patch("mechvane.sketch_rule.enforce", side_effect=RuntimeError("sketch rule did not settle")):
        try:
            server.run("test_part", [
                {"command": "solid.box", "params": {"name": "Box1", "length": 10, "width": 10, "height": 10}}
            ])
            assert False, "Should have failed"
        except RuntimeError as e:
            print(f"server.run raised exception: {type(e).__name__}: {e}")

    # Inspect the document: Box1 was committed to the timeline even though run failed!
    bodies = doc.session.cmd("document.inspect").get("bodies", [])
    print(f"Bodies present in document session: {[b['name'] for b in bodies]}")
    assert len(bodies) == 1, "Box1 should have been executed by batch before enforce failed"
    print("CONFIRMED: server.run leaves document in modified state despite tool raising an error!")
finally:
    server.ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
