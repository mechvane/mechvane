"""One heavy run at a time on this machine (audit 2026-11-16, A5): the gate, review_branch.sh, ui_smoke.py and
demo_smoke.py take this lock first. Two of them side by side filled the swap and turned branches red that were fine
(#49, 2026-11-16). The outermost run holds the lock; the runs it starts see MECHVANE_HEAVY_LOCK and go on.

    from heavy_lock import hold; hold("ui_smoke")        (Python)
    review_branch.sh: flock on the same file              (shell, see there)

MECHVANE_HEAVY_WAIT: seconds to wait for the lock (default 10800); then the run stops with an error.
"""
import fcntl
import os
import sys
import time

LOCK = os.environ.get("MECHVANE_HEAVY_LOCKFILE", "/tmp/mechvane-heavy.lock")
_held = None  # keeps the file open (and the lock held) for the life of the process


def hold(name: str) -> None:
    global _held
    if os.environ.get("MECHVANE_HEAVY_LOCK") or _held is not None:
        return
    f = open(LOCK, "a+")
    wait = float(os.environ.get("MECHVANE_HEAVY_WAIT", "10800"))
    start, told = time.monotonic(), False
    while True:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if not told:
                print(f"{name}: waiting for another heavy run ({LOCK})", file=sys.stderr, flush=True)
                told = True
            if time.monotonic() - start > wait:
                sys.exit(f"{name}: another heavy run held {LOCK} for more than {wait:.0f} s")
            time.sleep(2)
    _held = f
    os.environ["MECHVANE_HEAVY_LOCK"] = name  # the runs this one starts inherit it
