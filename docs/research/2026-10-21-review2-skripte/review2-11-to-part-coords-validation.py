#!/usr/bin/env python3
"""Reproduction for Finding 11: to_part_coords crashes with IndexError on invalid point."""
import shutil
import tempfile
from mechvane.documents import Workspace, PART, ASSEMBLY
from mechvane import server

d = tempfile.mkdtemp()
try:
    server.ws = Workspace(d)
    part = server.ws.new(PART, "p")
    part.session.batch([{"command": "solid.box", "params": {"length": 10, "width": 10, "height": 10}}])
    part.save()

    asm = server.ws.new(ASSEMBLY, "a")
    server.insert_part("a", "p.solidcraft", name="P1", translate=[10, 0, 0], grounded=True)

    # Valid call works
    valid = server.to_part_coords("a", "P1", [15, 0, 0])
    print(f"Valid result: {valid}")

    # Invalid call with 2D point [x, y] raises IndexError instead of clean validation error
    try:
        server.to_part_coords("a", "P1", [15, 0])
        assert False, "Should have failed"
    except Exception as e:
        print(f"Call with [15, 0] failed with: {type(e).__name__}: {e}")
        assert isinstance(e, IndexError), f"Expected IndexError, got {type(e)}"

    # Invalid call with empty list []
    try:
        server.to_part_coords("a", "P1", [])
        assert False, "Should have failed"
    except Exception as e:
        print(f"Call with [] failed with: {type(e).__name__}: {e}")
        assert isinstance(e, IndexError)

    print("CONFIRMED: to_part_coords crashes with unhandled IndexError when point is not a 3D coordinate!")
finally:
    server.ws.close_all()
    shutil.rmtree(d, ignore_errors=True)
