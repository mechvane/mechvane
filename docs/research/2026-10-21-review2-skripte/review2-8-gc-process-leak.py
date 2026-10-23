#!/usr/bin/env python3
"""Reproduction for Finding 8: Session lacks __del__ and leaks subprocess upon GC."""
import gc
import os
import subprocess
from mechvane.solidcraft import Session

def create_and_drop_session():
    s = Session()
    pid = s._p.pid
    return pid

# Create session and let it go out of scope
child_pid = create_and_drop_session()
# Force garbage collection
gc.collect()

# Check whether the child process is still running
child_pids = subprocess.check_output(["pgrep", "-P", str(os.getpid())]).decode().split()
print(f"Child process {child_pid} still running after GC? {str(child_pid) in child_pids}")

try:
    assert str(child_pid) in child_pids, "Process should still be running because Session has no __del__"
    print("CONFIRMED: Discarded Session instances leak subprocesses indefinitely!")
finally:
    try:
        os.kill(child_pid, 9)
    except OSError:
        pass
