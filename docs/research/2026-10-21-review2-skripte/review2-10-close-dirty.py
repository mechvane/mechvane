#!/usr/bin/env python3
"""Reproduction for Finding 10: close_document silently discards uncommitted edits despite SolidCraft dirty: True."""
import shutil
import tempfile
from mechvane.documents import Workspace, PART
from mechvane import server

d = tempfile.mkdtemp()
try:
    server.ws = Workspace(d)
    doc = server.ws.new(PART, "test_part")
    doc.save()

    # Modify the document via batch command
    server.run("test_part", [{"command": "solid.box", "params": {"name": "Box", "length": 10, "width": 10, "height": 10}}])

    # SolidCraft knows the document has unsaved edits
    inspect_data = doc.session.cmd("document.inspect")
    is_dirty = inspect_data.get("dirty")
    print(f"SolidCraft document dirty flag: {is_dirty}")
    assert is_dirty is True, "Document should be dirty"

    # Document.info and list_documents do NOT expose the dirty status
    info = doc.info()
    print(f"Document.info(): {info}")
    assert "dirty" not in info, "dirty flag unexpectedly exposed"

    # close_document silently closes without saving and without warning
    res = server.close_document("test_part")
    print(f"close_document result: {res}")

    # Reopen to verify that changes were lost
    doc2 = server.ws.open("test_part.solidcraft")
    bodies = doc2.session.cmd("document.inspect").get("bodies", [])
    print(f"Bodies after reopening: {bodies}")
    assert len(bodies) == 0, "Unsaved changes were unexpectedly written"
    print("CONFIRMED: close_document silently discards unsaved changes without checking dirty flag!")
finally:
    server.ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
