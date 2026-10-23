#!/usr/bin/env python3
"""Reproduction for Finding 5: screenshot MCP tool overwrites and destroys CAD files."""
import shutil
import tempfile
from pathlib import Path
from mechvane.documents import Workspace, PART
from mechvane import server

d = tempfile.mkdtemp()
try:
    server.ws = Workspace(d)
    doc = server.ws.new(PART, "test_part")
    doc.session.batch([{"command": "solid.box", "params": {"length": 20, "width": 20, "height": 10}}])
    doc.save()

    cad_file = server.ws.root / "test_part.solidcraft"
    orig_bytes = cad_file.read_bytes()
    assert not orig_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "Original file must be a CAD file, not PNG"

    # Client takes a screenshot specifying a path pointing to the model file
    server.screenshot("test_part", path="test_part.solidcraft")

    new_bytes = cad_file.read_bytes()
    print(f"Header after screenshot: {new_bytes[:8]}")
    assert new_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "File was converted to PNG image"

    # Now trying to open the CAD file fails
    server.ws.close("test_part")
    try:
        server.ws.open("test_part.solidcraft")
        assert False, "Opening overwritten CAD file should fail"
    except Exception as e:
        print(f"Reopening destroyed CAD file failed as expected: {type(e).__name__}: {e}")

    print("CONFIRMED: screenshot tool overwrote and destroyed CAD model with PNG bytes!")
finally:
    server.ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
