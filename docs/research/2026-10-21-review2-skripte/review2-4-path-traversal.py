#!/usr/bin/env python3
"""Reproduction for Finding 4: Path traversal and missing boundary checks in Workspace._path."""
import shutil
import tempfile
from pathlib import Path
from mechvane.documents import Workspace, PART

d = tempfile.mkdtemp()
try:
    ws = Workspace(d)

    # 1. Path traversal via name
    p_traversal = ws._path("../../escaped", None)
    print(f"ws.root: {ws.root}")
    print(f"Resolved path for name='../../escaped': {p_traversal}")
    assert not p_traversal.is_relative_to(ws.root), "Path should have escaped ws.root"

    # 2. Path traversal via absolute path
    p_abs = ws._path(None, "/etc/passwd")
    print(f"Resolved path for path='/etc/passwd': {p_abs}")
    assert p_abs == Path("/etc/passwd").resolve()
    assert not p_abs.is_relative_to(ws.root)

    # 3. Empty name creates hidden dotfile .solidcraft
    doc_empty = ws.new(PART, "")
    print(f"Empty name creates document with path: {doc_empty.path}")
    assert doc_empty.path.name == ".solidcraft"
    assert doc_empty.path.is_file()
    ws.close("")

    print("CONFIRMED: Workspace._path fails to enforce workspace boundaries and allows path traversal!")
finally:
    ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
