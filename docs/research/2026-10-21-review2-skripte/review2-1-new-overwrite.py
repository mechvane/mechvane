#!/usr/bin/env python3
"""Reproduction for Finding 1: Workspace.new silently overwrites existing files."""
import tempfile
import shutil
from pathlib import Path
from mechvane.documents import Workspace, PART

d = tempfile.mkdtemp()
try:
    ws = Workspace(d)
    # Create important part with geometry
    doc1 = ws.new(PART, "bracket")
    doc1.session.batch([{"command": "solid.box", "params": {"length": 50, "width": 30, "height": 10}}])
    doc1.save()
    ws.close("bracket")

    target_file = Path(d) / "bracket.solidcraft"
    orig_size = target_file.stat().st_size
    assert orig_size > 500, f"Expected non-trivial file size, got {orig_size}"

    # Now call new() with same name (e.g. from new_part MCP tool)
    doc2 = ws.new(PART, "bracket")
    new_size = target_file.stat().st_size
    print(f"Original size: {orig_size} bytes -> Overwritten size: {new_size} bytes")
    # File was overwritten with empty design (approx 410-415 bytes)
    assert new_size < orig_size, "File should have been overwritten with empty template"
    print("CONFIRMED: Workspace.new overwrote existing file on disk without checking!")
finally:
    ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
