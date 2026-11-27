#!/usr/bin/env python3
"""Upstream watch: a weekly, model-free inventory of SolidCraft (issue #90).

(1) New releases of tangency-labs/solidcraft since the last run (release notes go into the report).
(2) Command difference: `list_commands` of the installed CLI against the latest stable and the latest pre-release
    (downloaded once into build/canary/<version>/, SHA256 checked by tools/sc_canary.py): new, removed and changed
    commands, and commands that went from "planned" to available. For new ones: whether Mechvane's code mentions them.
(3) Watched upstream issues (tools/upstream_watched.json): reports the ones that are closed, with the place in the
    repository to update.

Output: docs/upstream/YYYY-MM-DD.md and one short ntfy message. State: build/upstream/state.json.
  tools/upstream_watch.py [--no-download] [--no-ntfy] [--dry-run] [--offline OLD.json NEW.json]
--offline compares two saved command lists (fixtures) and prints the report, nothing else (used by the tests).
Exit code 0 also when there is news; != 0 only for tool errors.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

STATE_DIR = ROOT / "build" / "upstream"
STATE = STATE_DIR / "state.json"
WATCHED = ROOT / "tools" / "upstream_watched.json"
OUT_DIR = ROOT / "docs" / "upstream"
GH_API = "https://api.github.com/repos/tangency-labs/solidcraft"


# ------------------------------------------------------------------------------------------ pure functions

def snapshot_from_list(cmds: list[dict]) -> dict[str, dict]:
    """{command id: the fields that matter for a difference} from the answer of `list_commands`."""
    out = {}
    for c in cmds:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        out[c["id"]] = {
            "label": c.get("label"),
            "enabled": bool(c.get("enabled", True)),
            "planned": str(c["planned"]) if c.get("planned") else None,
            "params": c.get("params") if isinstance(c.get("params"), str) else json.dumps(c.get("params"), sort_keys=True),
        }
    return out


def diff_commands(old: dict[str, dict], new: dict[str, dict]) -> dict:
    """Added, removed and changed commands; `ready` are those that were planned (or disabled) and now work."""
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed, ready = [], []
    for cid in sorted(set(old) & set(new)):
        a, b = old[cid], new[cid]
        if a["planned"] and not b["planned"]:
            ready.append(cid)
            continue
        if a["params"] != b["params"]:
            changed.append({"id": cid, "what": "parameters"})
        elif a["enabled"] != b["enabled"] or a["planned"] != b["planned"]:
            changed.append({"id": cid, "what": "availability"})
    # a command that appears already available (not planned) is new in the strict sense
    new_available = [c for c in added if not new[c]["planned"]]
    new_planned = [c for c in added if new[c]["planned"]]
    return {"added": added, "new_available": new_available, "new_planned": new_planned, "removed": removed,
            "changed": changed, "ready": ready}


def mentioned_in_mechvane(ids: list[str], files: list[Path] | None = None) -> dict[str, bool]:
    """For each command id: does a Python or JavaScript file of Mechvane name it? (Every command is reachable
    through the generic `run`/`command` tools; "not named" means there is no dedicated handling, check or dialog.)"""
    if files is None:
        files = [p for pat in ("mechvane/**/*.py", "mechvane/**/*.js") for p in ROOT.glob(pat)]
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files if p.is_file())
    return {cid: (f'"{cid}"' in text or f"'{cid}'" in text) for cid in ids}


def issue_news(watched: list[dict], states: dict[str, str], previous: dict[str, str]) -> list[dict]:
    """Watched issues that are closed now; `newly` marks those that were open at the last run."""
    out = []
    for w in watched:
        key = str(w["number"])
        if states.get(key) == "closed":
            out.append({**w, "newly": previous.get(key) not in (None, "closed")})
    return out


def new_releases(releases: list[dict], seen: list[str]) -> list[dict]:
    """Releases whose tag is not in `seen`, oldest first."""
    fresh = [r for r in releases if r.get("tag_name") not in seen]
    return sorted(fresh, key=lambda r: r.get("published_at") or r.get("created_at") or "")


def render_report(day: str, installed: str, releases_new: list[dict], diffs: dict[str, dict], coverage: dict[str, bool],
                  issues: list[dict], notes_limit: int = 1800) -> str:
    L = [f"# Upstream-Bestandsaufnahme {day}", "",
         f"Installierte SolidCraft-Version: **{installed}**. Erzeugt von `tools/upstream_watch.py` (ohne Modell).", ""]
    L.append("## Neue Releases seit dem letzten Lauf")
    if not releases_new:
        L.append("\nKeine.")
    for r in releases_new:
        kind = "Vorabversion" if r.get("prerelease") else "stabil"
        L.append(f"\n### {r.get('tag_name')} ({kind}, {str(r.get('published_at') or '')[:10]})")
        body = (r.get("body") or "").strip()
        L.append(body[:notes_limit] + (" …" if len(body) > notes_limit else "") if body else "_ohne Release-Notes_")
    L.append("\n## Befehlsdifferenz")
    if not diffs:
        L.append("\nKeine neuere Version als die installierte zum Vergleichen.")
    for label, d in diffs.items():
        L.append(f"\n### {label}")
        L.append(f"- neu und verfügbar: **{len(d['new_available'])}**, neu geplant: {len(d['new_planned'])}, "
                 f"jetzt verfügbar (vorher geplant): **{len(d['ready'])}**, geändert: {len(d['changed'])}, "
                 f"entfernt: {len(d['removed'])}")
        for title, ids in (("Neu verfügbar", d["new_available"]), ("Jetzt verfügbar", d["ready"])):
            if ids:
                L.append(f"\n{title} (✔ = Mechvane-Code nennt den Befehl, ✘ = nur über `run`/`command` erreichbar):")
                L += [f"- {'✔' if coverage.get(c) else '✘'} `{c}`" for c in ids[:60]]
                if len(ids) > 60:
                    L.append(f"- … und {len(ids) - 60} weitere")
        if d["removed"]:
            L.append("\nEntfernt (prüfen, ob Mechvane sie nutzt):")
            L += [f"- `{c}`" for c in d["removed"][:40]]
        if d["changed"]:
            L.append("\nGeändert:")
            L += [f"- `{c['id']}` ({c['what']})" for c in d["changed"][:40]]
    L.append("\n## Beobachtete Upstream-Issues")
    if not issues:
        L.append("\nKeines geschlossen.")
    for i in issues:
        mark = "**neu geschlossen**" if i.get("newly") else "geschlossen"
        L.append(f"- #{i['number']} {mark}: {i.get('title') or ''}. Nachziehen: {i.get('follow_up', '-')}")
    return "\n".join(L) + "\n"


def ntfy_text(releases_new: list[dict], diffs: dict[str, dict], coverage: dict[str, bool], issues: list[dict]) -> str:
    parts = []
    if releases_new:
        parts.append("Releases: " + ", ".join(r.get("tag_name", "?") for r in releases_new[-3:]))
    for label, d in diffs.items():
        ids = d["new_available"] + d["ready"]
        if ids:
            without = sum(1 for c in ids if not coverage.get(c))
            parts.append(f"{label}: {len(ids)} neue Befehle ({without} ohne Mechvane-Code)")
    newly = [f"#{i['number']}" for i in issues if i.get("newly")]
    if newly:
        parts.append("Upstream-Issues geschlossen: " + ", ".join(newly))
    return "; ".join(parts) or "Nichts Neues bei SolidCraft."


# ------------------------------------------------------------------------------------------ side effects

def sh_version(cli: str) -> str:
    out = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    m = re.search(r"\d+\.\d+\.\d+\S*", out)
    return m.group(0) if m else out or "unbekannt"


def commands_of(cli: str) -> dict[str, dict]:
    from mechvane.solidcraft import Session
    s = Session(executable=cli, timeout=120.0)
    try:
        return snapshot_from_list(s.tool("list_commands", {}))
    finally:
        s.close()


def load_snapshot(version: str, cli: str | None) -> dict[str, dict] | None:
    path = STATE_DIR / f"commands-{version}.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    if cli is None:
        return None
    snap = commands_of(cli)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return snap


def gh_issue_states(watched: list[dict]) -> dict[str, tuple[str, str]]:
    out = {}
    for w in watched:
        req = urllib.request.Request(f"{GH_API}/issues/{w['number']}", headers={"User-Agent": "mechvane-upstream-watch"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))
            out[str(w["number"])] = (d.get("state", "?"), d.get("title", ""))
        except Exception as e:  # one unreachable issue must not stop the report
            out[str(w["number"])] = ("unknown", f"({e})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-download", action="store_true", help="only compare with versions already unpacked")
    ap.add_argument("--no-ntfy", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the report; write no file, no state, no message")
    ap.add_argument("--offline", nargs=2, metavar=("OLD", "NEW"), help="compare two saved command lists and print")
    a = ap.parse_args()
    day = dt.date.today().isoformat()

    if a.offline:
        old = snapshot_from_list(json.loads(Path(a.offline[0]).read_text(encoding="utf-8")))
        new = snapshot_from_list(json.loads(Path(a.offline[1]).read_text(encoding="utf-8")))
        d = diff_commands(old, new)
        cov = mentioned_in_mechvane(d["new_available"] + d["ready"])
        print(render_report(day, "(offline)", [], {"offline": d}, cov, []))
        return 0

    import sc_canary
    from mechvane import install

    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {}
    releases = sc_canary.fetch_releases()
    seen = state.get("seen_tags")
    first_run = seen is None
    fresh = [] if first_run else new_releases(releases, seen)
    pre, stable = sc_canary.get_latest_versions(releases)
    if first_run:  # the first run only records the state; show the newest of each kind as context
        fresh = [r for r in (stable, pre) if r]

    # The CLI the project actually uses (PATH / SOLIDCRAFT_CLI) comes first; a stale download cache from `mechvane setup`
    # made the report of 2026-11-16 name 0.41.0 although 0.43.0 was installed.
    installed_cli = os.environ.get("SOLIDCRAFT_CLI") or shutil.which("solidcraft-cli") or install.find_cli()
    installed = sh_version(installed_cli)
    base = load_snapshot(installed, installed_cli)

    diffs, coverage = {}, {}
    candidates = [("neueste stabile", stable)]
    if pre and (not stable or sc_canary.release_timestamp(pre) > sc_canary.release_timestamp(stable)):
        candidates.append(("neueste Vorabversion", pre))  # only when it is newer than the latest stable
    for kind, rel in candidates:
        if not rel:
            continue
        ver = rel["tag_name"].lstrip("v")
        if ver == installed:
            continue
        cli = None
        vdir = ROOT / "build" / "canary" / ver
        if not (STATE_DIR / f"commands-{ver}.json").is_file():
            if a.no_download and not vdir.is_dir():
                continue
            cli = str(sc_canary.ensure_cli(rel, vdir))
        snap = load_snapshot(ver, cli)
        if snap and base:
            d = diff_commands(base, snap)
            diffs[f"{installed} → {ver} ({kind})"] = d
            coverage.update(mentioned_in_mechvane(d["new_available"] + d["ready"]))

    watched = json.loads(WATCHED.read_text(encoding="utf-8"))["issues"]
    states = gh_issue_states(watched)
    for w in watched:
        w["title"] = states[str(w["number"])][1]
    issues = issue_news(watched, {k: v[0] for k, v in states.items()}, state.get("issues", {}))

    report = render_report(day, installed, fresh, diffs, coverage, issues)
    msg = ntfy_text(fresh if not first_run else [], diffs, coverage, issues)
    if a.dry_run:
        print(report)
        print("ntfy:", msg)
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{day}.md").write_text(report, encoding="utf-8")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"seen_tags": sorted({r["tag_name"] for r in releases}), "installed": installed,
                                 "issues": {k: v[0] for k, v in states.items()}, "last_run": day},
                                indent=1), encoding="utf-8")
    print(f"wrote docs/upstream/{day}.md")
    notify = os.environ.get("MECHVANE_NOTIFY_SCRIPT")  # optional shell script that defines `notify TITLE TEXT PRIORITY`
    if not a.no_ntfy and notify and Path(notify).is_file():
        subprocess.run(["bash", "-c", f'source "$2" && notify "Mechvane: Upstream" "$1" low', "_", msg, str(Path(notify).resolve())],
                       check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
