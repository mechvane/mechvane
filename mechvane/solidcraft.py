"""A synchronous stdio client for one `solidcraft-cli mcp` session."""

import json
import os
import queue
import subprocess
import threading
import time


class SolidCraftError(RuntimeError):
    """A SolidCraft tool or command reported an error."""


class Session:
    """One headless SolidCraft session (one open design)."""

    def __init__(self, allow_paths=(), executable=None, timeout=300.0):
        self.timeout = timeout
        self._closed = False
        args = [executable or os.environ.get("SOLIDCRAFT_CLI") or "solidcraft-cli", "mcp"]
        for p in allow_paths:
            args += ["--allow-path", str(p)]
        self._p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._n = 0
        # A reader thread instead of select() on the pipe, which Windows does not support.
        self._lines = queue.Queue()
        threading.Thread(target=self._reader, args=(self._p.stdout.fileno(), self._lines),
                         daemon=True).start()
        try:
            self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "mechvane", "version": "0.1"}})
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
            return text

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
