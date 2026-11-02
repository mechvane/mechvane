"""Session log of the web UI for debugging test sessions: one JSON line per event in
<cache>/logs/<date>.jsonl (on Windows %LOCALAPPDATA%\\mechvane\\logs). It records the api requests of the
workspace (path, status, time, the request body and the error, not mesh data), the agent's turns and tool
calls with the allow/decline decision, and what the browser reports (errors, dialogs, status line).

It stays on the computer; nothing is sent anywhere. Logs older than 14 days are removed. Read it with
tools/remote_debug.py (over SSH) or any text viewer.
"""

import json
import threading
import time
from datetime import datetime, timedelta

from .. import install

KEEP_DAYS = 14
MAX_STR = 2000
_lock = threading.Lock()
_pruned = False


def log_dir():
    return install.CACHE / "logs"


def _clip(v, depth=0):
    """Long strings and big lists cut short: the log stays readable and small."""
    if isinstance(v, str):
        return v if len(v) <= MAX_STR else v[:MAX_STR] + f"… (+{len(v) - MAX_STR})"
    if isinstance(v, list):
        out = [_clip(x, depth + 1) for x in v[:50]]
        return out + [f"… (+{len(v) - 50})"] if len(v) > 50 else out
    if isinstance(v, dict):
        if depth > 6:
            return "…"
        return {str(k): _clip(x, depth + 1) for k, x in v.items()}
    return v


def _prune():
    global _pruned
    _pruned = True
    cutoff = (datetime.now() - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    try:
        for p in log_dir().glob("*.jsonl"):
            if p.stem < cutoff:
                p.unlink(missing_ok=True)
    except OSError:
        pass


def log(kind: str, **data):
    """Append one event. Never raises: logging must not break the UI."""
    try:
        if not _pruned:
            _prune()
        now = time.time()
        line = {"t": datetime.fromtimestamp(now).strftime("%H:%M:%S.") + f"{int(now * 1000) % 1000:03d}",
                "kind": kind, **_clip(data)}
        d = log_dir()
        d.mkdir(parents=True, exist_ok=True)
        with _lock, open(d / f"{datetime.now():%Y-%m-%d}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass
