"""Agent turns for the web UI (ADR 0003): the user's own coding agent, started over the Agent Client
Protocol (ACP), works on the project files through the Mechvane MCP server, one turn at a time.

- AcpAgent: JSON-RPC over the agent's stdio. The agent runs in an empty folder of its own, gets no file
  system or terminal from us and, for the Claude Code adapter, none of its built-in tools: it can change
  the model only through the Mechvane MCP server, and every tool call it makes comes here first.
- decide(): which of those tool calls run without asking.
- Snapshot: the project's .solidcraft files before a turn, outside the project, for Undo.
- AgentTurns: one turn after the other, its events for the page, Stop and Undo.
"""

import filecmp
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from .. import install

MECHVANE_TOOL = "mcp__mechvane__"
# Tools that remove something: they wait for the user (until the chat can ask, they are declined)
ASK_TOOLS = {"delete_feature", "delete_joint", "delete_bolted_connection", "close_document"}
FILE_KEYS = {"file", "dir", "output", "path", "source"}
FILE_EXTS = (".solidcraft", ".sc", ".step", ".stp", ".stl", ".3mf", ".obj", ".dxf", ".svg", ".png", ".iges",
             ".igs", ".gltf", ".glb", ".json", ".txt")


def _looks_like_file(v) -> bool:
    if not isinstance(v, str):
        return False
    return any(c in v for c in "/\\~") or v.startswith(".") or v.lower().endswith(FILE_EXTS)


def _command_ok(cmd: dict) -> str | None:
    """None when a SolidCraft command may run without asking, else the reason (ADR 0003, section 6)."""
    cid = str(cmd.get("command", ""))
    if cid.startswith(("file.", "doc.")) or "delete" in cid or cid.endswith(".remove"):
        return f"`{cid}` reads, writes or removes files or features"
    for k, v in (cmd.get("params") or {}).items():
        if k in ("file", "dir", "output") or (k in FILE_KEYS and _looks_like_file(v)):
            return f"`{cid}` names a file ({k})"
    return None


def decide(tool: str, params: dict | None) -> tuple[bool, str]:
    """Whether the agent may make this tool call without asking, and why not."""
    params = params or {}
    if not tool.startswith(MECHVANE_TOOL):
        return False, f"{tool} is not a Mechvane tool"
    name = tool[len(MECHVANE_TOOL):]
    if name in ASK_TOOLS:
        return False, f"{name} removes something and needs your OK"
    if name == "screenshot" and params.get("path"):
        return False, "screenshot to a file"
    if name == "run":
        for c in params.get("commands") or []:
            why = _command_ok(c if isinstance(c, dict) else {})
            if why:
                return False, why
    if name == "command":
        why = _command_ok({"command": params.get("command"), "params": params.get("params")})
        if why:
            return False, why
    return True, ""


def agent_command() -> list[str] | None:
    """The ACP agent to start: $MECHVANE_AGENT (a command line), else claude-agent-acp on PATH."""
    if os.environ.get("MECHVANE_AGENT"):
        return shlex.split(os.environ["MECHVANE_AGENT"], posix=sys.platform != "win32")
    found = shutil.which("claude-agent-acp")
    return [found] if found else None


class AcpAgent:
    """One ACP session with an agent process."""

    def __init__(self, command, workspace: Path, on_event, decide=decide, model=None):
        self.on_event, self.decide = on_event, decide
        self.cwd = tempfile.mkdtemp(prefix="mechvane-agent-")
        self._next = 0
        self._replies = {}
        self._cond = threading.Condition()
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     cwd=self.cwd, text=True, encoding="utf-8", bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()
        self._call("initialize", {"protocolVersion": 1, "clientCapabilities": {
            "fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False}}, timeout=60)
        mcp = {"name": "mechvane", "command": sys.executable,
               "args": ["-m", "mechvane", "mcp", "--workspace", str(workspace)],
               "env": [{"name": "MECHVANE_AUTOSAVE", "value": "1"},
                       # the agent starts the server in its own empty folder: find this package from there too
                       {"name": "PYTHONPATH", "value": os.pathsep.join(
                           [str(Path(__file__).resolve().parents[2])] + [x for x in [os.environ.get("PYTHONPATH")] if x])}]}
        options = {"tools": [], "settingSources": [], "strictMcpConfig": True}
        if model:
            options["model"] = model
        new = self._call("session/new", {"cwd": self.cwd, "mcpServers": [mcp],
                                         "_meta": {"claudeCode": {"options": options}}}, timeout=120)
        self.session = new["sessionId"]

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _call(self, method, params, timeout=None):
        with self._cond:
            self._next += 1
            i = self._next
        self._send({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
        end = None if timeout is None else time.monotonic() + timeout
        with self._cond:
            while i not in self._replies:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"the agent ended during {method}")
                left = None if end is None else end - time.monotonic()
                if left is not None and left <= 0:
                    raise TimeoutError(f"no answer to {method}")
                self._cond.wait(timeout=1 if left is None else min(1, left))
            msg = self._replies.pop(i)
        if "error" in msg:
            raise RuntimeError(msg["error"].get("message", str(msg["error"])))
        return msg.get("result") or {}

    def _read(self):
        for line in self.proc.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if "method" in msg and "id" in msg:
                self._request(msg)
            elif "id" in msg:
                with self._cond:
                    self._replies[msg["id"]] = msg
                    self._cond.notify_all()
            elif msg.get("method") == "session/update":
                self._update(msg["params"].get("update") or {})
        with self._cond:
            self._cond.notify_all()

    def _request(self, msg):
        if msg["method"] != "session/request_permission":
            self._send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "not supported"}})
            return
        call = msg["params"].get("toolCall") or {}
        tool = (call.get("_meta") or {}).get("claudeCode", {}).get("toolName") or call.get("name") or call.get("title") or ""
        ok, why = self.decide(tool, call.get("rawInput"))
        allow = next((o for o in msg["params"].get("options", []) if o.get("kind") == "allow_once"), None)
        if ok and allow:
            outcome = {"outcome": "selected", "optionId": allow["optionId"]}
        else:
            reject = next((o for o in msg["params"].get("options", []) if o.get("kind") == "reject_once"), None)
            outcome = {"outcome": "selected", "optionId": reject["optionId"]} if reject else {"outcome": "cancelled"}
            self.on_event({"type": "declined", "tool": tool.removeprefix(MECHVANE_TOOL), "reason": why})
        self._send({"jsonrpc": "2.0", "id": msg["id"], "result": {"outcome": outcome}})

    def _update(self, u):
        kind = u.get("sessionUpdate")
        if kind == "agent_message_chunk":
            text = (u.get("content") or {}).get("text")
            if text:
                self.on_event({"type": "text", "text": text})
        elif kind == "tool_call":
            title = u.get("title") or ""
            self.on_event({"type": "tool", "id": u.get("toolCallId"), "tool": title.removeprefix(MECHVANE_TOOL),
                           "status": u.get("status") or "pending"})
        elif kind == "tool_call_update" and u.get("status") in ("completed", "failed"):
            ev = {"type": "tool", "id": u.get("toolCallId"), "status": u["status"]}
            if u["status"] == "failed":
                ev["error"] = _tool_error(u)
            self.on_event(ev)

    def prompt(self, text: str) -> str:
        """Send one message and wait for the turn to end; returns the stop reason."""
        r = self._call("session/prompt", {"sessionId": self.session, "prompt": [{"type": "text", "text": text}]})
        return r.get("stopReason", "end_turn")

    def cancel(self):
        self._send({"jsonrpc": "2.0", "method": "session/cancel", "params": {"sessionId": self.session}})

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        shutil.rmtree(self.cwd, ignore_errors=True)


def _tool_error(u: dict) -> str:
    """The error text of a failed tool call, from its content or raw output (ACP), else a plain note."""
    parts = []
    for c in u.get("content") or []:
        inner = c.get("content") if isinstance(c, dict) else None
        if isinstance(inner, dict) and inner.get("text"):
            parts.append(inner["text"])
    raw = u.get("rawOutput")
    if not parts and raw:
        parts.append(raw if isinstance(raw, str) else json.dumps(raw)[:500])
    return " ".join(parts)[:500] or "the tool call failed without an error message"


def project_files(folder: Path) -> dict[str, Path]:
    """The project's .solidcraft files by path relative to folder (hidden files and folders left out)."""
    out = {}
    for p in folder.rglob("*.solidcraft"):
        rel = p.relative_to(folder)
        if p.is_file() and not any(part.startswith(".") for part in rel.parts):
            out[rel.as_posix()] = p
    return out


def _state(folder: Path) -> dict[str, int]:
    return {rel: p.stat().st_mtime_ns for rel, p in project_files(folder).items()}


class Snapshot:
    """Copies of the project's files, in the cache (outside every folder the agent may write to)."""

    def __init__(self, folder: Path, label: str):
        self.folder = folder
        key = hashlib.sha1(str(folder.resolve()).encode()).hexdigest()[:12]
        self.dir = install.CACHE / "history" / key / f"{time.strftime('%Y%m%d-%H%M%S')}-{label}"
        n = 1
        while self.dir.exists():
            n += 1
            self.dir = self.dir.with_name(f"{self.dir.name.rsplit('~', 1)[0]}~{n}")
        files = project_files(folder)
        for rel, p in files.items():
            target = self.dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "manifest.json").write_text(json.dumps(sorted(files)), encoding="utf-8")

    def restore(self) -> dict:
        """Put the project back as it was: changed files back, files added since removed."""
        keep = set(json.loads((self.dir / "manifest.json").read_text(encoding="utf-8")))
        removed = []
        for rel, p in project_files(self.folder).items():
            if rel not in keep:
                p.unlink()
                removed.append(rel)
        restored = []
        for rel in keep:
            target = self.folder / rel
            # files the turn did not touch stay as they are, with their timestamps
            if target.is_file() and filecmp.cmp(self.dir / rel, target, shallow=False):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(f".{target.name}.restore")
            shutil.copy2(self.dir / rel, tmp)
            os.replace(tmp, target)
            restored.append(rel)
        return {"restored": sorted(restored), "removed": sorted(removed)}


class AgentTurns:
    """The chat of one UI server: one agent session, turns one after the other.

    on_files_changed() is called (under no lock) after a turn changed files, so the server reopens
    its documents."""

    def __init__(self, folder: Path, on_files_changed=None, command=None):
        self.folder = Path(folder)
        self.on_files_changed = on_files_changed or (lambda: None)
        self.command = command
        self.lock = threading.Lock()
        self.busy = False
        self.events: list[dict] = []
        self.turns: list[dict] = []  # {id, text, snapshot, after, state, summary}
        self.notes: list[str] = []  # for the agent, sent with the next message
        self.agent: AcpAgent | None = None
        self._stop = False

    def _event(self, e: dict):
        with self.lock:
            e = {"n": len(self.events) + 1, "turn": len(self.turns), **e}
            self.events.append(e)

    def events_since(self, n: int) -> dict:
        with self.lock:
            return {"busy": self.busy, "events": self.events[n:], "next": len(self.events),
                    "undo": self._undo_label()}

    def _undo_label(self):
        done = [t for t in self.turns if self._undoable(t)]
        return done[-1]["text"][:60] if done else None

    @staticmethod
    def _undoable(t) -> bool:
        s = t.get("summary") or {}
        return t["state"] == "done" and not t.get("undone") and bool(s.get("changed") or s.get("removed"))

    def send(self, text: str, selection: list | None = None, document: str | None = None) -> int:
        with self.lock:
            if self.busy:
                raise RuntimeError("the agent is still working on the last message")
            self.busy = True
            self._stop = False
            turn = {"id": len(self.turns) + 1, "text": text, "state": "running"}
            self.turns.append(turn)
        names = [x.get("name") or x.get("kind") for x in (selection or []) if isinstance(x, dict)]
        self._event({"type": "user", "text": text, "selected": len(selection or []),
                     "selection_names": [n for n in names if n][:8]})
        threading.Thread(target=self._run, args=(turn, text, selection, document), daemon=True).start()
        return turn["id"]

    def _note(self, text: str):
        """Something the agent's own history does not show (undo, redo, a stopped turn); goes with the next message."""
        self.notes.append(text)

    def _message(self, text, selection, document):
        context = {"document": document, "selection": selection or []}
        notes, self.notes = self.notes, []
        prefix = "".join(f"Note: {n}\n" for n in notes)
        return prefix + ("You work on a Mechvane CAD project with the user, through the mechvane MCP tools only. "
                "Changes are saved automatically after each tool call. Model with features that stay editable "
                "in the tree. The user's selection uses Mechvane face names; `click` is where they clicked.\n"
                f"Context: {json.dumps(context)}\n\nUser: {text}")

    def _run(self, turn, text, selection, document):
        try:
            turn["snapshot"] = Snapshot(self.folder, f"turn{turn['id']}")
            self._event({"type": "status", "status": "working"})
            if self.agent is None or self.agent.proc.poll() is not None:
                cmd = self.command or agent_command()
                if not cmd:
                    raise RuntimeError("no agent found: install the Claude Code ACP adapter "
                                       "(npm install -g @agentclientprotocol/claude-agent-acp) or set MECHVANE_AGENT")
                self.agent = AcpAgent(cmd, self.folder, self._event)
            reason = self.agent.prompt(self._message(text, selection, document))
            if self._stop or reason == "cancelled":
                turn["state"] = "stopped"
                self._event({"type": "status", "status": "stopped", **turn["snapshot"].restore()})
                self._note(f"the user stopped your turn {turn['id']} ({turn['text']!r}); the files are back as "
                           "they were before it.")
            else:
                turn["state"] = "done"
                turn["after"] = _state(self.folder)
                before = set(json.loads((turn["snapshot"].dir / "manifest.json").read_text(encoding="utf-8")))
                changed = sorted(r for r, m in turn["after"].items()
                                 if r not in before or (turn["snapshot"].dir / r).stat().st_mtime_ns != m)
                turn["summary"] = {"changed": changed, "removed": sorted(before - set(turn["after"]))}
                self._event({"type": "done", "reason": reason, **turn["summary"]})
        except Exception as e:  # the turn failed: back to how it was before
            turn["state"] = "failed"
            restored = turn["snapshot"].restore() if turn.get("snapshot") else {}
            self._event({"type": "error", "error": str(e), **restored})
        finally:
            with self.lock:
                self.busy = False
            self.on_files_changed()

    def stop(self):
        with self.lock:
            if not self.busy:
                return False
            self._stop = True
        if self.agent:
            self.agent.cancel()
        return True

    def undo(self, force: bool = False) -> dict:
        """Undo the last finished turn. Refused (unless force) when the files changed since it ended."""
        with self.lock:
            if self.busy:
                raise RuntimeError("the agent is working")
            done = [t for t in self.turns if self._undoable(t)]
            if not done:
                raise LookupError("nothing to undo")
            turn = done[-1]
            if not force and _state(self.folder) != turn.get("after"):
                raise PermissionError("the files changed since this turn; undo would discard those changes")
            redo = Snapshot(self.folder, f"redo{turn['id']}")
            out = turn["snapshot"].restore()
            turn["undone"] = True
            turn["redo"] = redo
            self._note(f"the user undid your turn {turn['id']} ({turn['text']!r}); the project files are back as "
                       "they were before it. Do not redo it unless the user asks.")
        self._event({"type": "undone", "turn_id": turn["id"], **out})
        self.on_files_changed()
        return out

    def redo(self) -> dict:
        """Put back the turn undone last, as long as nothing changed since the undo."""
        with self.lock:
            if self.busy:
                raise RuntimeError("the agent is working")
            undone = [t for t in self.turns if t.get("undone")]
            if not undone:
                raise LookupError("nothing to redo")
            turn = undone[-1]
            out = turn.pop("redo").restore()
            turn["undone"] = False
            turn["after"] = _state(self.folder)
            self._note(f"the user redid your turn {turn['id']} ({turn['text']!r}); its changes are back in the files.")
        self._event({"type": "redone", "turn_id": turn["id"], **out})
        self.on_files_changed()
        return out

    def close(self):
        if self.agent:
            self.agent.close()
            self.agent = None
