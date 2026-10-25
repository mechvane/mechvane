// Drive the Mechvane "Model" page in headless Chromium over the DevTools protocol: wait until the
// SolidCraft web app has opened the document, run SolidCraft commands in it, save, wait for
// Mechvane's check and take a screenshot.
//
//   node tools/drive_model_ui.mjs <url> <out.png> [commands.json]
//
// commands.json: [{command, params}] run with window.solidcraft.execute before file.save.
// Prints a JSON report (the server's answer to the save, the app's errors) on stdout.
// CHROME: Chromium binary (default: Playwright's chromium under ~/.cache/ms-playwright).
import { spawn } from "node:child_process";
import { readFileSync, writeFileSync, readdirSync, mkdtempSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

const [url, out, cmdFile] = process.argv.slice(2);
const commands = cmdFile ? JSON.parse(readFileSync(cmdFile, "utf8")) : [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function chrome() {
  if (process.env.CHROME) return process.env.CHROME;
  const base = join(homedir(), ".cache/ms-playwright");
  const dir = readdirSync(base).filter((d) => /^chromium-\d+$/.test(d)).sort().pop();
  return join(base, dir, "chrome-linux64/chrome");
}

const profile = mkdtempSync(join(tmpdir(), "mv-chrome-"));
const proc = spawn(chrome(), [
  "--headless=new", "--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
  ...(process.env.CHROME_FLAGS ? process.env.CHROME_FLAGS.split(" ") : ["--enable-unsafe-webgpu"]), "--window-size=1600,900", `--user-data-dir=${profile}`,
  "--remote-debugging-port=0", "about:blank",
], { stdio: ["ignore", "ignore", "pipe"] });

const wsUrl = await new Promise((resolve, reject) => {
  let buf = "";
  proc.stderr.on("data", (d) => {
    buf += d;
    const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m) resolve(m[1]);
  });
  proc.on("exit", () => reject(new Error("chromium exited: " + buf.slice(-500))));
});

const port = new URL(wsUrl).port;
const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const page = targets.find((t) => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
const logs = [];
ws.addEventListener("message", (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  if (msg.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(msg.params.type))
    logs.push(msg.params.args.map((a) => a.value ?? a.description).join(" ").slice(0, 300));
  if (msg.method === "Runtime.exceptionThrown") logs.push(msg.params.exceptionDetails.text);
});
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text);
  return r.result?.result?.value;
};
const waitFor = async (expr, seconds) => {
  for (let i = 0; i < seconds * 2; i++) {
    const v = await evaluate(expr);
    if (v) return v;
    await sleep(500);
  }
  return null;
};

const report = { url };
try {
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Page.navigate", { url });
  const t0 = Date.now();
  report.ready = await waitFor("window.mechvaneReady || window.mechvaneError", 240);
  report.ready_s = (Date.now() - t0) / 1000;
  const sc = "document.getElementById('app').contentWindow.solidcraft";
  if (report.ready === true) {
    report.before = await evaluate(`${sc}.inspect().then(d => ({bodies: (d.bodies||[]).length, timeline: (d.timeline||[]).length, path: d.path, name: d.name}))`);
    report.results = [];
    for (const c of commands) report.results.push(await evaluate(`${sc}.execute(${JSON.stringify(c.command)}, ${JSON.stringify(c.params || {})})`));
    if (commands.length) {
      await evaluate(`${sc}.execute("file.save", {})`);
      const s = await waitFor("window.mechvaneLastSave", 120);
      report.save = s && { saved: s.saved, bytes: s.bytes, summary: s.findings.summary, update_links: s.update_links };
    }
    await sleep(3000);
  }
  const shot = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(out, Buffer.from(shot.result.data, "base64"));
} catch (e) {
  report.error = String(e.message || e);
} finally {
  report.logs = logs.slice(0, 20);
  console.log(JSON.stringify(report, null, 1));
  ws.close();
  proc.kill();
}
