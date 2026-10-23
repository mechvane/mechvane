#!/usr/bin/env python3
"""Reproduction for Finding 2: Opening same file under different names causes concurrent sessions and lost updates."""
import tempfile
import shutil
from pathlib import Path
from mechvane.documents import Workspace, PART

d = tempfile.mkdtemp()
try:
    ws = Workspace(d)
    doc = ws.new(PART, "shared")
    ws.close("shared")

    # 1. Open the same file under two different names/aliases
    doc_a = ws.open("shared.solidcraft", name="doc_a")
    doc_b = ws.open("shared.solidcraft", name="doc_b")
    assert "doc_a" in ws.docs and "doc_b" in ws.docs
    print("Both sessions opened simultaneously pointing to same file on disk.")

    # 2. Modify doc_a (add a box) and save
    doc_a.session.batch([{"command": "solid.box", "params": {"name": "BoxA", "body_name": "BoxA", "length": 20, "width": 20, "height": 10}}])
    doc_a.save()

    # 3. Modify doc_b (add a cylinder) and save
    doc_b.session.batch([{"command": "solid.cylinder", "params": {"name": "CylB", "body_name": "CylB", "diameter": 10, "height": 30}}])
    doc_b.save()

    # 4. Close both and reload from disk
    ws.close("doc_a")
    ws.close("doc_b")
    doc_check = ws.open("shared.solidcraft", name="check")
    bodies = [b["name"] for b in doc_check.session.cmd("document.inspect").get("bodies", [])]
    print(f"Bodies found on disk after both saved: {bodies}")
    # BoxA was completely lost/overwritten by CylB!
    assert "BoxA" not in bodies, "BoxA was unexpectedly preserved"
    assert "CylB" in bodies, "CylB should be present"
    print("CONFIRMED: Lost update occurred; doc_a's changes were wiped out by doc_b!")
finally:
    ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
