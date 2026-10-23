#!/usr/bin/env python3
"""Reproduction for Finding 6: Session.close() creates zombie (<defunct>) processes on timeout."""
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from mechvane.solidcraft import Session

# Create a session
s = Session()
pid = s._p.pid

# Simulate a subprocess that does not terminate upon stdin.close() within wait(10).
# We monkeypatch s._p.wait on the first call to simulate TimeoutExpired during wait(10),
# so Session.close() executes its timeout recovery handler (kill + wait).
orig_wait = s._p.wait
first_call = True


def timeout_wait(timeout=None):
    global first_call
    if first_call:
        first_call = False
        raise subprocess.TimeoutExpired(s._p.args, timeout)
    return orig_wait(timeout)


s._p.wait = timeout_wait

# Execute Session.close() directly to test Session's cleanup logic
s.close()

time.sleep(0.1)

# Inspect the OS status of the killed process in /proc and via waitpid
is_zombie = False
try:
    with open(f"/proc/{pid}/status") as f:
        state_line = next((line for line in f if line.startswith("State:")), "")
        print(f"Process {pid} state in /proc: {state_line.strip()}")
        is_zombie = "Z (zombie)" in state_line
except OSError:
    print(f"Process {pid} was already reaped and removed from /proc")

try:
    waited_pid, _ = os.waitpid(pid, os.WNOHANG)
    if waited_pid == pid:
        is_zombie = True
except ChildProcessError:
    pass

# Verify whether it is a zombie (Z)
assert is_zombie, f"Expected zombie state for process {pid}, but process was properly reaped by Session.close()"
print("CONFIRMED: Killing subprocess without wait() creates zombie (<defunct>) processes!")
