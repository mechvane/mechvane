"""Turn a real agent session of the web UI into a recording the live demo plays back (#124).

    python3 tools/record_replay.py EVENTS.json OUT.json --demo bracket --title "…" [--log SESSION.jsonl] [--turn N]

EVENTS.json is what `GET /api/agent/events?since=0` returned after the agent's turn (since #124 the tool events carry the
whole tool input and every event its time `t`). The agent's own words, tool calls and results are kept as they happened; only the
pauses are cut to at most MAX_GAP seconds, and paths and the computer's name are taken out. Events without a time
(sessions before #124) take theirs from the session log (`~/.cache/mechvane/logs/<date>.jsonl`, --log).

Tool calls that change the model are marked `do`: tools/build_demo_site.py runs them on the demo part with the
same Mechvane functions and stores the model after each one, so the demo shows the session without SolidCraft in
the page. A tool this script does not know stops the recording: better no replay than one that shows a model the
agent never made.
"""
import argparse
import json
import re
import socket
import sys
from pathlib import Path

MAX_GAP = 2.0
# Mechvane MCP tools that only read (or save the file): shown in the chat, nothing to replay
READ_ONLY = {
    "check_design", "browser", "list_commands", "list_documents", "open_document", "save_document", "close_document",
    "measure", "find", "verify_view", "screenshot", "list_standard_parts", "check_joints", "check_parameters",
    "list_bolted_connections", "preview_bolted_connection", "to_part_coords", "export_gltf", "part_end",
}
# Tools whose change build_demo_site.py can replay
REPLAYED = {"run", "command", "delete_feature", "rename_feature"}
# SolidCraft commands of the `command` tool that only read
READ_COMMAND = re.compile(r"(\.(inspect|list|get|query|describe|solve_status)$)|^(measure|document\.inspect|parameters\.list)")
KEEP = {"user", "text", "tool", "declined", "done"}

_PATH = re.compile(r"(?:[A-Za-z]:\\|/)(?:root|home|Users|tmp|var|private)[^\s'\"`,)\]]*")


def scrub(v, host=None):
    """Paths become their last part; the computer's name goes."""
    host = host or socket.gethostname()
    if isinstance(v, str):
        v = _PATH.sub(lambda m: re.split(r"[\\/]", m.group(0).rstrip("\\/"))[-1], v)
        # the name only where it names the computer (user@host, //host, host.local, host:port), not the same word in text
        return re.sub(rf"(?<=[@/]){re.escape(host)}\b|\b{re.escape(host)}(?=[.:/]\w)", "computer", v) if host else v
    if isinstance(v, list):
        return [scrub(x, host) for x in v]
    if isinstance(v, dict):
        return {k: scrub(x, host) for k, x in v.items()}
    return v


def is_change(tool: str, params: dict | None) -> bool:
    """Whether a tool call changed the model; raises for a tool the replay cannot show."""
    if tool in READ_ONLY:
        return False
    if tool == "command":
        return not READ_COMMAND.search((params or {}).get("command", ""))
    if tool in REPLAYED:
        return True
    raise ValueError(f"cannot replay tool {tool!r}: add it to READ_ONLY or teach build_demo_site.py to run it")


def apply_change(ws, doc, do: dict):
    """Run one recorded change on doc with the functions the MCP tool uses (tools/build_demo_site.py)."""
    from mechvane import modeling, sketch_rule  # noqa: PLC0415 (only the demo build needs SolidCraft)
    tool, p = do["tool"], do.get("params") or {}
    if tool == "run":
        return modeling.run_commands(doc, p["commands"])
    if tool == "command":
        return doc.session.cmd(p["command"], p.get("params") or {})
    if tool == "delete_feature":
        if p.get("keep_sketch"):
            return doc.session.cmd("timeline.delete", {"features": [p["feature"]]})
        return sketch_rule.delete_with_owned(doc.session, p["feature"])
    if tool == "rename_feature":
        return doc.session.cmd("timeline.rename", {"feature": p["feature"], "name": p["name"]})
    raise ValueError(f"cannot replay tool {tool!r}")


def _clock(t: str) -> float:
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def times_from_log(events: list[dict], log_lines: list[dict]) -> list[float | None]:
    """The time of each event from the session log: its agent_event lines come in the same order as the events
    (text is logged in stretches, so a text event takes the time of the event before it)."""
    logged = [x for x in log_lines if x.get("kind") == "agent_event"]
    # the day's log holds other sessions too: start at the last time this user message was logged
    first = next((e for e in events if e.get("type") == "user"), None)
    starts = [k for k, x in enumerate(logged) if first and x.get("type") == "user" and x.get("text") == first.get("text")]
    logged = logged[starts[-1]:] if starts else logged
    out, i, last = [], 0, None
    for e in events:
        if e.get("type") == "text":
            out.append(last)
            continue
        while i < len(logged):
            x = logged[i]
            i += 1
            if x.get("type") == e.get("type") and x.get("id") == e.get("id") and x.get("status") == e.get("status"):
                last = _clock(x["t"])
                break
        out.append(last)
    return out


def build(events: list[dict], *, demo: str, title: str, turn: int | None = None, times=None, host=None) -> dict:
    if turn is None:
        turn = max((e.get("turn", 0) for e in events if e.get("type") == "user"), default=0)
    picked = [(i, e) for i, e in enumerate(events) if e.get("turn", turn) == turn and e.get("type") in KEEP]
    if not picked or picked[0][1].get("type") != "user":
        raise ValueError(f"turn {turn} has no message from the user")
    stamps = [(e.get("t") if e.get("t") is not None else (times[i] if times else None)) for i, e in picked]
    steps, clock, prev, names = [], 0.0, None, {}
    for (i, e), ts in zip(picked, stamps):
        if steps:
            clock += min(max(ts - prev, 0.0), MAX_GAP) if ts is not None and prev is not None else 0.5
        if ts is not None:
            prev = ts
        ev = {k: v for k, v in e.items() if k not in ("n", "turn", "t", "from")}
        if ev["type"] == "text" and steps and steps[-1]["event"]["type"] == "text":
            steps[-1]["event"]["text"] += ev["text"]  # one stretch of the agent's words is one line in the chat
            continue
        if ev["type"] == "tool":
            if ev.get("tool"):
                names[ev["id"]] = ev["tool"]
                ev.pop("params", None)
            else:
                tool = names.get(ev["id"], "")
                if ev.get("status") == "completed" and is_change(tool, ev.get("params")):
                    ev["do"] = {"tool": tool, "params": ev.get("params") or {}}
        if ev["type"] == "user":
            ev.pop("selection_names", None)
        steps.append({"t": round(clock, 2), "event": ev})
    return scrub({"title": title, "demo": demo, "prompt": picked[0][1]["text"], "steps": steps}, host)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("events")
    ap.add_argument("out")
    ap.add_argument("--demo", required=True, help="the live-demo example the session ran on (examples.DEMOS)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--turn", type=int)
    ap.add_argument("--log", help="session log for events without a time")
    ap.add_argument("--note", help="how it was recorded (agent, adapter, date), kept in the file")
    a = ap.parse_args(argv)
    data = json.loads(Path(a.events).read_text(encoding="utf-8"))
    events = data["events"] if isinstance(data, dict) else data
    times = None
    if a.log:
        lines = [json.loads(x) for x in Path(a.log).read_text(encoding="utf-8").splitlines() if x.strip()]
        times = times_from_log(events, lines)
    rec = build(events, demo=a.demo, title=a.title, turn=a.turn, times=times)
    if a.note:
        rec["recorded"] = a.note
    Path(a.out).write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n_do = sum(1 for s in rec["steps"] if s["event"].get("do"))
    print(f"{a.out}: {len(rec['steps'])} steps, {n_do} change(s), {rec['steps'][-1]['t']:.1f} s")


if __name__ == "__main__":
    sys.exit(main())
