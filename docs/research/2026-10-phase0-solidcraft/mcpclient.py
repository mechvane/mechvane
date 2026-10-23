"""Minimal stdio MCP client for solidcraft-cli mcp. Usage: import and call Session.tool()."""
import base64, json, subprocess, sys, time


class Session:
    def __init__(self, args, log):
        self.p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1)
        self.n = 0
        self.log = open(log, "w")
        r = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                    "clientInfo": {"name": "inventa-phase0", "version": "0"}})
        self.instructions = r["result"].get("instructions", "")
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.tools = self.rpc("tools/list", {})["result"]["tools"]

    def send(self, msg):
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()

    def rpc(self, method, params):
        self.n += 1
        self.send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})
        line = self.p.stdout.readline()
        return json.loads(line)

    def tool(self, name, args=None, png=None):
        t0 = time.time()
        r = self.rpc("tools/call", {"name": name, "arguments": args or {}})
        ms = (time.time() - t0) * 1000
        texts, size = [], len(json.dumps(r))
        if "error" in r:
            texts.append("RPC ERROR " + json.dumps(r["error"]))
            err = True
        else:
            res = r["result"]
            err = res.get("isError", False)
            for c in res["content"]:
                if c["type"] == "text":
                    texts.append(c["text"])
                elif c["type"] == "image" and png:
                    open(png, "wb").write(base64.b64decode(c["data"]))
        out = "\n".join(texts)
        self.log.write(f"### {name} {json.dumps(args)[:400]}\n-> isError={err} {ms:.0f} ms, {size} B\n{out[:3000]}\n\n")
        self.log.flush()
        return err, out, ms, size

    def close(self):
        self.p.stdin.close()
        self.p.wait(10)
        return self.p.stderr.read()
