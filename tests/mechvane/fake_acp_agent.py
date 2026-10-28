"""A stand-in ACP agent for the web UI's agent tests: speaks JSON-RPC on stdio like claude-agent-acp.

On session/prompt it asks permission for a few tool calls, reports the answers as text and, depending on
words in the prompt, changes the project through a Mechvane Workspace:
  edit   add a box to plate.solidcraft and create extra.solidcraft
  slow   edit, then wait up to 20 s for session/cancel
  crash  edit, then exit in the middle of the turn
"""

import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mechvane.documents import PART, Workspace  # noqa: E402

lock = threading.Lock()
pending = {}
cancelled = threading.Event()
state = {"workspace": None, "next": 1000}


def send(msg):
    with lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def ask(tool, raw):
    with lock:
        state["next"] += 1
        i = state["next"]
        ev = pending[i] = [threading.Event(), None]
    send({"jsonrpc": "2.0", "id": i, "method": "session/request_permission", "params": {
        "sessionId": "s1", "toolCall": {"toolCallId": f"t{i}", "title": tool, "rawInput": raw,
                                        "_meta": {"claudeCode": {"toolName": tool}}},
        "options": [{"optionId": "allow", "kind": "allow_once", "name": "Allow"},
                    {"optionId": "reject", "kind": "reject_once", "name": "Reject"}]}})
    ev[0].wait(30)
    outcome = (ev[1] or {}).get("outcome", {})
    return outcome.get("optionId") == "allow"


def chunk(text):
    send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "s1", "update": {
        "sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": text}}}})


def edit():
    ws = Workspace(state["workspace"])
    try:
        d = ws.open("plate.solidcraft")
        d.session.cmd("solid.box", {"length": 5, "width": 5, "height": 5, "corner": [0, 0, 10], "operation": "join"})
        d.save()
        if not (Path(state["workspace"]) / "extra.solidcraft").exists():
            ws.new(PART, "extra")
    finally:
        ws.close_all()


def prompt(i, text):
    send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "s1", "update": {
        "sessionUpdate": "tool_call", "toolCallId": "c1", "title": "mcp__mechvane__run", "status": "pending"}}})
    answers = {
        "run chamfer": ask("mcp__mechvane__run", {"document": "plate", "commands": [
            {"command": "solid.chamfer", "params": {"edges": [[0, 0, 5]], "distance": 1}}]}),
        "run export": ask("mcp__mechvane__run", {"document": "plate", "commands": [
            {"command": "file.export", "params": {"path": "/tmp/x.step"}}]}),
        "Bash": ask("Bash", {"command": "ls"}),
        "delete_feature": ask("mcp__mechvane__delete_feature", {"document": "plate", "feature": "Box1"}),
    }
    chunk("answers " + json.dumps(answers))
    if any(w in text for w in ("edit", "slow", "crash")):
        edit()
    if "crash" in text:
        os._exit(3)
    if "slow" in text:
        cancelled.wait(20)
    stop = "cancelled" if cancelled.is_set() else "end_turn"
    cancelled.clear()
    send({"jsonrpc": "2.0", "id": i, "result": {"stopReason": stop}})


for line in sys.stdin:
    msg = json.loads(line)
    method, i = msg.get("method"), msg.get("id")
    if method is None and i in pending:
        pending[i][1] = msg.get("result")
        pending[i][0].set()
    elif method == "initialize":
        send({"jsonrpc": "2.0", "id": i, "result": {"protocolVersion": 1, "agentCapabilities": {}}})
    elif method == "session/new":
        mcp = msg["params"]["mcpServers"][0]
        state["workspace"] = mcp["args"][mcp["args"].index("--workspace") + 1]
        assert {"name": "MECHVANE_AUTOSAVE", "value": "1"} in mcp["env"]
        assert msg["params"]["_meta"]["claudeCode"]["options"]["tools"] == []
        send({"jsonrpc": "2.0", "id": i, "result": {"sessionId": "s1"}})
    elif method == "session/prompt":
        text = " ".join(b.get("text", "") for b in msg["params"]["prompt"])
        threading.Thread(target=prompt, args=(i, text), daemon=True).start()
    elif method == "session/cancel":
        cancelled.set()
