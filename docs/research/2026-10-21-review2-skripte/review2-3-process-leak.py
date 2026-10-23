#!/usr/bin/env python3
"""Reproduction for Finding 3: Leaked solidcraft-cli processes on failed new() and reader()."""
import os
import shutil
import subprocess
import tempfile
from mechvane.documents import Workspace, PART

d = tempfile.mkdtemp()
leaked_pids = []
try:
    ws = Workspace(d)

    # 1. Failed Workspace.new (e.g. non-existent subdirectory)
    try:
        ws.new(PART, "parts/bracket")
    except Exception as e:
        print(f"ws.new failed as expected: {type(e).__name__}: {e}")

    # Check child processes running under current python PID
    out1 = subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split()
    print(f"Child PIDs running after failed new(): {out1}")
    assert len(out1) >= 1, "Expected at least 1 leaked process"
    leaked_pids.extend(out1)

    # 2. Failed Workspace.reader (e.g. non-existent file)
    try:
        ws.reader(os.path.join(d, "nonexistent.solidcraft"))
    except Exception as e:
        print(f"ws.reader failed as expected: {type(e).__name__}: {e}")

    out2 = subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split()
    print(f"Child PIDs running after failed reader(): {out2}")
    assert len(out2) >= 2, "Expected at least 2 leaked processes"
    leaked_pids.extend(out2)

    # Calling close_all does NOT clean them up because they are not in ws.docs!
    ws.close_all()
    out3 = subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split()
    print(f"Child PIDs still running after ws.close_all(): {out3}")
    assert len(out3) >= 2, "Leaked processes were not cleaned up by close_all"
    print("CONFIRMED: Both failed new() and failed reader() permanently leak subprocesses!")
finally:
    for pid in set(leaked_pids):
        try:
            os.kill(int(pid), 9)
        except OSError:
            pass
    shutil.rmtree(d, ignore_errors=True)
