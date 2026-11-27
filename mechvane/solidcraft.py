"""A synchronous stdio client for one `solidcraft-cli mcp` session."""

import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time

from . import install


class SolidCraftError(RuntimeError):
    """A SolidCraft tool or command reported an error."""


_adapters_cache = None


def _windows_adapters() -> list[str]:
    """Names of the graphics adapters Windows reports, once per process; empty if the query fails."""
    global _adapters_cache
    if _adapters_cache is None:
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "(Get-CimInstance Win32_VideoController).Name"],
                capture_output=True, text=True, timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
            _adapters_cache = [line.strip() for line in out.splitlines() if line.strip()]
        except (OSError, subprocess.SubprocessError):
            _adapters_cache = []
    return _adapters_cache


def session_env(platform=sys.platform, environ=None, adapters=None) -> dict:
    """Environment for `solidcraft-cli mcp`. On Windows with only Intel graphics wgpu uses DirectX 12
    unless WGPU_BACKEND is set: saving renders a preview through wgpu, and with Intel's Vulkan driver
    (igvk64.dll) that crashes the CLI with 0xC0000005 on any part with a curved face
    (docs/research/2026-10-29-windows-zylinder-absturz.md, SolidCraft #5589). With an NVIDIA or AMD card
    the default (Vulkan) stays: there DirectX 12 crashes the CLI while building a socket head screw
    (Windows 11 VM with an RTX 2070, 2026-11-01)."""
    env = dict(os.environ if environ is None else environ)
    if platform == "win32" and "WGPU_BACKEND" not in env:
        names = [a.lower() for a in (_windows_adapters() if adapters is None else adapters)]
        discrete = any(k in a for a in names for k in ("nvidia", "geforce", "quadro", "amd", "radeon"))
        if not discrete and any("intel" in a for a in names):
            env["WGPU_BACKEND"] = "dx12"
    return env


def control_dir(platform=sys.platform, environ=None) -> str:
    """Folder where the SolidCraft app writes `<port>.token`, `<port>.pid` and `current.port`
    (docs/control-protocol.md "Token"); SOLIDCRAFT_CONTROL_DIR moves it."""
    env = os.environ if environ is None else environ
    if env.get("SOLIDCRAFT_CONTROL_DIR"):
        return env["SOLIDCRAFT_CONTROL_DIR"]
    home = env.get("HOME") or env.get("USERPROFILE") or "~"
    if platform == "win32":
        return os.path.join(env.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local"), "SolidCraft", "control")
    if platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "SolidCraft", "control")
    return os.path.join(env.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share"), "solidcraft", "control")


def _split_address(address: str):
    """('host', port) from '127.0.0.1:PORT', '[::1]:PORT' or a bare port; port None when it is not a number."""
    address = address.strip()
    if address.isdigit():
        return "127.0.0.1", int(address)
    host, _, port = address.rpartition(":")
    host = host.strip("[]") or "127.0.0.1"
    return host, int(port) if port.isdigit() else None


def _pid_alive(folder, port) -> bool:
    """False only when the window's `<port>.pid` names a process that is gone: then whatever listens on the
    port is not that SolidCraft window (#190). Unknown (no file, other platform) counts as alive."""
    try:
        with open(os.path.join(folder, f"{port}.pid")) as f:
            pid = int(f.read().strip())
    except (OSError, ValueError):
        return True
    if sys.platform == "win32":
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True  # exists, owned by someone else
    return True


def _listening(port: int, host="127.0.0.1", timeout=1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def find_app(control=None, probe=_listening) -> str:
    """The `127.0.0.1:PORT` of the one running SolidCraft window, from the files its control channel
    leaves in the control folder. Raises SolidCraftError with a plain message for no window, only
    stale files (an app that was force-quit leaves its token behind) and several windows (then the
    caller names the port itself)."""
    folder = control or control_dir()
    try:
        ports = sorted(int(n[:-6]) for n in os.listdir(folder) if n.endswith(".token") and n[:-6].isdigit())
    except OSError:
        ports = []
    if not ports:
        raise SolidCraftError(
            f"no running SolidCraft window found (no token file in {folder}); open the app with "
            "Settings > Assistant > Agents through MCP > 'Let AI agents connect' on, or start it with --control PORT. "
            "An app started with SOLIDCRAFT_CONTROL_TOKEN or another SOLIDCRAFT_CONTROL_DIR leaves no file here: "
            "name its address ('127.0.0.1:PORT') and token instead")
    answering = [p for p in ports if probe(p)]
    live = [p for p in answering if _pid_alive(folder, p)]
    if answering and not live:
        # the pid files say gone, yet the ports answer: the app may run in another pid namespace (Flatpak, Snap,
        # a sandbox), so trust the ports (#190 review)
        live = answering
    if not live:
        raise SolidCraftError(
            f"SolidCraft left token files for port(s) {', '.join(map(str, ports))} in {folder}, but nothing listens "
            "there (stale files from an app that was force-quit): start the app again or delete the files")
    if len(live) > 1:
        raise SolidCraftError(
            f"several SolidCraft windows are open (ports {', '.join(map(str, live))}): name one with address '127.0.0.1:PORT'")
    return f"127.0.0.1:{live[0]}"


def parse_version(text) -> tuple | None:
    """(0, 50, 0) from "0.50.0" or "0.51.0-nightly.20261127"; None when it does not look like a version."""
    import re
    m = re.match(r"\s*v?(\d+)\.(\d+)(?:\.(\d+))?", text) if isinstance(text, str) else None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)) if m else None


# From this SolidCraft version on, `document.inspect {"measure": true}` reports the bodies of an assembly in world
# coordinates (0.49.1 and older: in part coordinates). Checked 2026-11-27 on 0.43.0, 0.47.0, 0.49.0, 0.49.1 (part) and 0.50.0 (world), #231.
MEASURE_WORLD_FROM = (0, 50, 0)


class Session:
    """One SolidCraft session: headless (one open design of its own), or, with `connect`, bridged to the
    design in the running app's window (`connect="auto"` finds the window, or `"127.0.0.1:PORT"`)."""

    CONNECT_TIMEOUT = 20.0  # the app answers at once or not at all; a hang would block the agent for `timeout`

    def __init__(self, allow_paths=(), executable=None, timeout=300.0, connect=None, token=None):
        self.timeout = timeout
        self._closed = False
        self.engine_version = None  # (major, minor, patch) of the SolidCraft process, set by initialize
        self.connected = connect is not None
        self.address = None
        if self.connected:
            self.address = find_app() if connect == "auto" else connect
            # `mcp --connect` only connects at the first tool call ("tool calls connect once it runs"), so a
            # dead port would show up as a hang or a vague error later: check it here
            host, port = _split_address(self.address)
            if port is None or not _listening(port, host):
                raise SolidCraftError(f"no SolidCraft window listens at {self.address}: open the app with "
                                      "'Let AI agents connect' on, or start it with --control PORT")
            if self.address.strip().isdigit():
                self.address = f"127.0.0.1:{port}"  # a bare port
            args = [executable or install.find_cli(), "mcp", "--connect", self.address]
            if token:
                args += ["--token", token]
        else:
            # --headless: since 0.25 a plain `mcp` joins a running SolidCraft app instead; each Mechvane
            # document needs its own session
            args = [executable or install.find_cli(), "mcp", "--headless"]
        for p in allow_paths:
            args += ["--allow-path", str(p)]
        self._p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, bufsize=1, env=session_env(),
                                   encoding="utf-8", errors="replace")  # not the Windows ANSI code page
        self._n = 0
        # A reader thread instead of select() on the pipe, which Windows does not support.
        self._lines = queue.Queue()
        threading.Thread(target=self._reader, args=(self._p.stdout.fileno(), self._lines),
                         daemon=True).start()
        try:
            init = self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                            "clientInfo": {"name": "mechvane", "version": "0.1"}},
                             timeout=self.CONNECT_TIMEOUT if self.connected else None)
            info = init.get("serverInfo") if isinstance(init, dict) else None
            self.engine_version = parse_version(info.get("version") if isinstance(info, dict) else None)
            self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except Exception:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _send(self, msg):
        try:
            self._p.stdin.write(json.dumps(msg) + "\n")
            self._p.stdin.flush()
        except OSError as e:
            self.close()
            raise SolidCraftError(f"solidcraft-cli communication failed: {e}") from e

    @staticmethod
    def _reader(fd, lines):
        # Raw os.read, not the BufferedReader: a daemon thread blocked inside the buffered
        # reader holds its lock and aborts the interpreter at shutdown.
        buf = b""
        try:
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    lines.put(line)
        except OSError:
            pass
        lines.put(None)

    def _readline(self, timeout):
        try:
            line = self._lines.get(timeout=max(0.0, timeout))
        except queue.Empty:
            self.close()
            raise SolidCraftError(f"timeout waiting for solidcraft-cli response after {timeout}s")
        if line is None:
            self.close()
            raise SolidCraftError("solidcraft-cli mcp ended unexpectedly")
        return line.rstrip(b"\r").decode("utf-8")

    def _rpc(self, method, params, timeout=None):
        call_timeout = self.timeout if timeout is None else timeout
        self._n += 1
        self._send({"jsonrpc": "2.0", "id": self._n, "method": method, "params": params})
        deadline = time.monotonic() + call_timeout
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            line = self._readline(remaining)
            if not line:
                self.close()
                raise SolidCraftError("solidcraft-cli mcp ended unexpectedly")
            msg = json.loads(line)
            if msg.get("id") == self._n:
                break
        if "error" in msg:
            raise SolidCraftError(f"{method}: {msg['error'].get('message', msg['error'])}")
        return msg["result"]

    def tool(self, name, args=None, timeout=None):
        """Call an MCP tool. Returns parsed JSON where the reply is JSON, else the text;
        images come back as {"image": base64, "mime": ...}."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)
        texts, images = [], []
        for c in res.get("content", []):
            if c["type"] == "text":
                texts.append(c["text"])
            elif c["type"] == "image":
                images.append({"image": c["data"], "mime": c.get("mimeType", "image/png")})
        text = "\n".join(texts)
        if res.get("isError"):
            raise SolidCraftError(text)
        if images:
            return {"images": images, "text": text}
        try:
            return json.loads(text)
        except ValueError:
            pass
        # Since 0.25 a headless session appends a plain-text note after the JSON ("Note: this is a
        # headless session ..."): keep the JSON value at the start.
        try:
            value, end = json.JSONDecoder().raw_decode(text.lstrip())
        except ValueError:
            return text
        return value

    def cmd(self, command, params=None, timeout=None):
        """Run one engine command."""
        return self.tool("execute", {"command": command, "params": params or {}, "verbose": False}, timeout=timeout)

    def batch(self, commands, rollback=True, timeout=None):
        """Run steps all-or-nothing. Raises with the failing step's error."""
        r = self.tool("batch", {"commands": commands, "rollback": rollback, "verbose": False}, timeout=timeout)
        if isinstance(r, dict) and r.get("ok") is False:
            raise SolidCraftError(json.dumps(r.get("error", r))[:2000])
        return r

    def close(self):
        if self._closed or self._p is None:
            return
        self._closed = True
        try:
            if self._p.stdin and not self._p.stdin.closed:
                try:
                    self._p.stdin.close()
                except OSError:
                    pass
            self._p.wait(10)
        except (OSError, subprocess.TimeoutExpired):
            try:
                self._p.kill()
            except OSError:
                pass
            try:
                self._p.wait(5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        finally:
            if self._p.stdout and not self._p.stdout.closed:
                try:
                    self._p.stdout.close()
                except OSError:
                    pass
