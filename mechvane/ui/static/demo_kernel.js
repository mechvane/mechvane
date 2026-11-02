// The live demo has no server: this kernel answers the workspace's api/* requests in the browser,
// through the SolidCraft web app loaded into a hidden iframe (the same app as "Model by hand"), so
// the feature dialogs, Undo and the design check work on mechvane.dev as with `mechvane ui`.
// It mirrors mechvane/ui/server.py (run_feature, feature_for_edit, sketches, history) closely; the
// design check runs in Pyodide (demo_check.js). The example stays in this browser (OPFS).
import { checkInBrowser, initDemoCheck } from "./demo_check.js";

const CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02";
const FT_NS = "https://github.com/bherbruck/solidcraft/formats/3mf-face-tags/2026/10";

// Same lists as the server: what dialogs may run, and which feature types open in a dialog again
const COMMANDS = {
  "mechvane.sketch": "Sketch", "solid.fillet": "Fillet", "solid.chamfer": "Chamfer", "solid.hole": "Hole",
  "solid.pattern.rectangular": "Rectangular pattern", "solid.pattern.circular": "Circular pattern",
  "solid.mirror": "Mirror", "solid.extrude": "Extrude", "solid.revolve": "Revolve",
};
const EDITABLE = {
  FilletFeature: ["fillet", "solid.fillet"], ChamferFeature: ["chamfer", "solid.chamfer"],
  HoleFeature: ["hole", "solid.hole"], RectangularPatternFeature: ["rectangular", "solid.pattern.rectangular"],
  CircularPatternFeature: ["circular", "solid.pattern.circular"], MirrorFeature: ["mirror", "solid.mirror"],
  ExtrudeFeature: ["extrude", "solid.extrude"], RevolveFeature: ["revolve", "solid.revolve"],
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// SolidCraft's error in one line, as the server's short_error: its own words, without the prefix
function shortError(err) {
  let text = String(err && err.message ? err.message : err).split("\n")[0].replace(/^Error:\s*/, "");
  try {
    const failed = JSON.parse(String(err.message || err)).failed;
    if (failed && failed.error) text = failed.error;
  } catch { /* not a batch reply */ }
  text = text.replace(/^not supported yet:\s*/, "").replace(/^invalid parameters for `[^`]+`:\s*/, "");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// A zip entry of a 3MF (stored or deflated), read through the central directory
async function unzipEntry(buf, wanted) {
  const v = new DataView(buf);
  let eocd = -1;
  for (let i = buf.byteLength - 22; i >= Math.max(0, buf.byteLength - 65557); i--) {
    if (v.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("not a zip file");
  let p = v.getUint32(eocd + 16, true);
  const n = v.getUint16(eocd + 10, true);
  const dec = new TextDecoder();
  for (let k = 0; k < n; k++) {
    const method = v.getUint16(p + 10, true), size = v.getUint32(p + 20, true);
    const nameLen = v.getUint16(p + 28, true), extraLen = v.getUint16(p + 30, true), commentLen = v.getUint16(p + 32, true);
    const local = v.getUint32(p + 42, true);
    const name = dec.decode(new Uint8Array(buf, p + 46, nameLen));
    if (name === wanted) {
      const start = local + 30 + v.getUint16(local + 26, true) + v.getUint16(local + 28, true);
      const data = new Uint8Array(buf, start, size);
      if (method === 0) return dec.decode(data);
      const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
      return await new Response(stream).text();
    }
    p += 46 + nameLen + extraLen + commentLen;
  }
  throw new Error(`${wanted} missing in the 3MF`);
}

// 3MF with face tags → [{name, positions, indices, face_ids}], as mechvane/ui/mesh.py parse_3mf
function parse3mf(xml) {
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  const bodies = [];
  for (const obj of doc.getElementsByTagNameNS(CORE_NS, "object")) {
    const mesh = obj.getElementsByTagNameNS(CORE_NS, "mesh")[0];
    if (!mesh) continue;
    const positions = [], indices = [], face_ids = [];
    for (const vtx of mesh.getElementsByTagNameNS(CORE_NS, "vertex")) {
      positions.push(+vtx.getAttribute("x"), +vtx.getAttribute("y"), +vtx.getAttribute("z"));
    }
    for (const t of mesh.getElementsByTagNameNS(CORE_NS, "triangle")) {
      indices.push(+t.getAttribute("v1"), +t.getAttribute("v2"), +t.getAttribute("v3"));
      face_ids.push(+(t.getAttributeNS(FT_NS, "face") || 0));
    }
    bodies.push({ name: obj.getAttribute("name") || `Object${obj.getAttribute("id") || ""}`, positions, indices, face_ids });
  }
  return bodies;
}

// base: () => "demos/<name>/", read when the kernel starts (the page sets it after loading the index)
export function createDemoKernel({ base, onStatus = () => {} }) {
  let app = null;        // window.solidcraft of the hidden app
  let booting = null;
  let files = null;      // files.json of the example
  let version = 1;
  let stepped = false;   // a step was made: the page shows this model, no longer the precomputed one
  let meshSeq = 0;
  const done = [];       // hand steps for Undo: {label}
  const undone = [];     // for Redo
  let holeSizes = null;

  const exec = (cmd, params = {}) => app.execute(cmd, params);

  async function boot() {
    if (app) return;
    if (!booting) {
      booting = (async () => {
        onStatus("Starting SolidCraft in your browser… (first time: about 50 MB)");
        if (!files) files = await (await fetch(`${base()}files.json`)).json();
        const dir = await navigator.storage.getDirectory();
        for (const name of files.files) {
          const bytes = new Uint8Array(await (await fetch(`${base()}files/${encodeURIComponent(name)}`)).arrayBuffer());
          const h = await dir.getFileHandle(name, { create: true });
          const w = await h.createWritable();
          await w.write(bytes);
          await w.close();
        }
        initDemoCheck().catch((err) => console.warn("Pyodide pre-load:", err));
        const frame = document.createElement("iframe");
        frame.title = "SolidCraft (computes the live demo)";
        frame.setAttribute("aria-hidden", "true");
        frame.tabIndex = -1;
        // offscreen, not display:none: the app needs a real canvas size to start
        frame.style.cssText = "position:fixed;left:-10000px;top:0;width:800px;height:600px;border:0;visibility:hidden";
        frame.src = "sc/index.html?t=" + Date.now();
        document.body.append(frame);
        await new Promise((r) => frame.addEventListener("load", r, { once: true }));
        let sc = null;
        for (let i = 0; i < 600 && !sc; i++) { sc = frame.contentWindow.solidcraft; if (!sc) await sleep(100); }
        if (!sc) throw new Error("SolidCraft did not start");
        await sleep(1500);
        for (let i = 0; ; i++) {
          try { await sc.execute("doc.open", { path: "/opfs/" + files.document }); break; }
          catch (e) { if (i >= 30) throw e; await sleep(1000); }
        }
        await sc.request("ui.home", { open: false }).catch(() => {});
        app = sc;
        onStatus("Ready");
      })().catch((err) => { booting = null; throw err; });
    }
    await booting;
  }

  async function timeline() {
    return (await exec("document.inspect", { measure: false })).timeline || [];
  }

  async function errors() {
    const out = {};
    for (const f of await timeline()) if (f.error) out[f.name] = f.error;
    return out;
  }

  async function measure() {
    const bodies = (await exec("document.inspect", { measure: true })).bodies || [];
    return { volume: bodies.reduce((s, b) => s + (b.volume_mm3 || 0), 0), bodies: bodies.length };
  }

  function delta(a, b) {
    const d = { bodies: b.bodies, volume_mm3: +b.volume.toFixed(2), volume_change_mm3: +(b.volume - a.volume).toFixed(2) };
    if (Math.abs(b.volume - a.volume) < 1e-6 && a.bodies === b.bodies) {
      d.warnings = ["Feature had no effect: volume unchanged."];
    }
    return d;
  }

  async function mesh() {
    const ins = await exec("document.inspect", { measure: false });
    if (!(ins.bodies || []).length) return { bodies: [] };
    const name = `.mechvane-mesh-${++meshSeq}.3mf`;
    const res = await exec("file.export", { path: "/opfs/" + name, format: "3mf-tagged" });
    // the app writes OPFS a moment later: wait for all of its bytes
    const dir = await navigator.storage.getDirectory();
    let file = null;
    for (let i = 0; i < 100; i++) {
      try { file = await (await dir.getFileHandle(name)).getFile(); } catch { file = null; }
      if (file && file.size >= (res.bytes || 1)) break;
      await sleep(30);
    }
    const bodies = parse3mf(await unzipEntry(await file.arrayBuffer(), "3D/3dmodel.model"));
    dir.removeEntry(name).catch(() => {});
    for (const b of bodies) {
      try {
        const faces = (await exec("model.faces", { body: b.name })).faces || [];
        b.faces = faces.map((f) => ({ index: +f.index, name: f.name })).sort((x, y) => x.index - y.index);
      } catch { b.faces = []; }
    }
    return { bodies };
  }

  // The model browser as the server's collect_tree: features with the sketch each one uses under it
  async function tree() {
    const tl = await timeline();
    const byId = Object.fromEntries(tl.map((f) => [f.id, f]));
    const owned = new Map();
    for (const f of tl) {
      if (f.type === "Sketch") continue;
      const def = (await exec("timeline.inspect", { feature: f.id })).definition || {};
      const sk = byId[def.sketch];
      if (sk && sk.type === "Sketch" && !owned.has(sk.name)) owned.set(sk.name, f.name);
    }
    const node = (f) => ({ name: f.name, type: f.type, suppressed: f.suppressed || undefined,
                           rolled_back: f.rolled_back || undefined, error: f.error || undefined });
    const features = [];
    for (const f of tl) {
      if (f.type === "Sketch" && owned.has(f.name)) continue;
      const n = node(f);
      const kids = tl.filter((s) => s.type === "Sketch" && owned.get(s.name) === f.name).map(node);
      if (kids.length) n.children = kids;
      features.push(n);
    }
    features.push({ type: "EndOfPart" });
    const ins = await exec("document.inspect", { measure: false });
    return { kind: files.kind || "part", name: files.document.replace(/\.solidcraft$/, ""),
             bodies: (ins.bodies || []).map((b) => b.name), features };
  }

  async function findings() {
    try {
      return await checkInBrowser(app, files.document);
    } catch (err) {
      return { summary: `Design check in the browser failed: ${err.message}`, findings: [], verdict: "warn" };
    }
  }

  async function namesToIds(set) {
    const ids = Object.fromEntries((await timeline()).map((f) => [f.name, f.id]));
    const out = { ...set };
    if (Array.isArray(out.features)) out.features = out.features.map((f) => ids[f] ?? f);
    if (typeof out.sketch === "string" && ids[out.sketch] !== undefined) out.sketch = ids[out.sketch];
    return out;
  }

  // mechvane.sketch as the server's sketch_commands: rectangles and circles, each fully dimensioned,
  // all or nothing; one undo step in the app is not guaranteed here, so the step is not undoable
  async function sketch(params) {
    const plane = params.plane && params.plane.face ? { face: params.plane.face } : params.plane;
    const cp = (await exec("edit.checkpoint")).checkpoint;
    try {
      await exec("sketch.create", { plane });
      for (const sh of params.shapes || []) {
        const num = (v, d) => (typeof v === "number" ? v : d);
        let dims;
        if (sh.type === "rectangle") {
          const r = await exec("sketch.rectangle.two_point", { p0: [num(sh.x, 0), num(sh.y, 0)],
            p1: [num(sh.x, 0) + num(sh.w, 10), num(sh.y, 0) + num(sh.h, 10)], connect: false });
          dims = [[{ entities: [r.sides.bottom], type: "length" }, sh.w], [{ entities: [r.sides.left], type: "length" }, sh.h],
                  [{ entities: ["origin", r.corners.bottom_left], type: "distance_x" }, sh.x],
                  [{ entities: ["origin", r.corners.bottom_left], type: "distance_y" }, sh.y]];
        } else {
          const r = await exec("sketch.circle.center", { center: [num(sh.x, 0), num(sh.y, 0)], diameter: num(sh.d, 10), connect: false });
          const center = r.created.points.find((pt) => pt.endsWith("center"));
          dims = [[{ entities: [r.created.curves[0]], type: "diameter" }, sh.d],
                  [{ entities: ["origin", center], type: "distance_x" }, sh.x],
                  [{ entities: ["origin", center], type: "distance_y" }, sh.y]];
        }
        for (const [spec, value] of dims) await exec("sketch.dimension", { ...spec, value });
      }
      await exec("sketch.finish", {});
    } catch (err) {
      await exec("edit.restore_checkpoint", { checkpoint: cp }).catch(() => {});
      throw new ApiError(400, shortError(err));
    }
    await exec("edit.restore_checkpoint", { checkpoint: cp, forget: true }).catch(() => {});
    // several app steps: Undo in the demo stops here (the list is cleared), the sketch stays
    done.length = 0;
    undone.length = 0;
    version++;
    stepped = true;
    const name = (await timeline()).filter((f) => f.type === "Sketch").at(-1)?.name;
    return { done: "Sketch", results: [{ name }] };
  }

  async function sketchPlane(url) {
    const face = url.searchParams.get("face");
    const plane = face ? { face: face.split(",").map(Number) } : (url.searchParams.get("plane") || "XY");
    const cp = (await exec("edit.checkpoint")).checkpoint;
    try {
      await exec("sketch.create", { plane });
      const f = (await exec("sketch.inspect", {})).plane || {};
      return { origin: f.origin, x_dir: f.x_dir, y_dir: f.y_dir };
    } catch (err) {
      throw new ApiError(400, shortError(err));
    } finally {
      await exec("edit.restore_checkpoint", { checkpoint: cp });
    }
  }

  async function feature(body) {
    const { command, params, preview } = body;
    if (!COMMANDS[command]) throw new ApiError(403, `command not available in the workspace: ${command}`);
    if (command === "mechvane.sketch") {
      if (preview || body.edit) throw new ApiError(403, "a sketch is drawn in the dialog and made with OK");
      return sketch(params);
    }
    let step = { cmd: command, params };
    if (typeof body.edit === "string") {
      const f = (await timeline()).find((x) => x.name === body.edit);
      if (!f) throw new ApiError(404, `feature not found: ${body.edit}`);
      if ((EDITABLE[f.type] || [])[1] !== command) throw new ApiError(403, `${body.edit} is not edited with ${command}`);
      step = { cmd: "timeline.edit", params: { feature: body.edit, set: await namesToIds(params) } };
    }
    const failingBefore = body.edit ? await errors() : {};
    const before = await measure();
    const cp = (await exec("edit.checkpoint")).checkpoint;
    let result;
    try {
      result = await exec(step.cmd, step.params);
      const now = await errors();
      const fresh = Object.keys(now).filter((k) => !(k in failingBefore));
      if (body.edit && fresh.length) throw new Error(fresh.map((k) => `${k}: ${now[k]}`).join("; "));
    } catch (err) {
      await exec("edit.restore_checkpoint", { checkpoint: cp }).catch(() => {});
      throw new ApiError(400, shortError(err));
    }
    const d = delta(before, await measure());
    if (preview) {
      const m = await mesh();
      await exec("edit.restore_checkpoint", { checkpoint: cp });
      return { preview: true, delta: d, mesh: m };
    }
    await exec("edit.restore_checkpoint", { checkpoint: cp, forget: true }).catch(() => {});
    const label = (body.edit ? `Edit ${body.edit}: ` : "") + COMMANDS[command];
    done.push({ label });
    undone.length = 0;
    version++;
    stepped = true;
    return { done: label, delta: d, results: [result] };
  }

  async function featureForEdit(name) {
    const tl = await timeline();
    const at = tl.findIndex((f) => f.name === name);
    if (at < 0) throw new ApiError(404, `feature not found: ${name}`);
    const kind = EDITABLE[tl[at].type];
    if (!kind) throw new ApiError(403, `${name} (${tl[at].type}) cannot be edited in the workspace yet`);
    const info = await exec("timeline.inspect", { feature: name });
    const cp = (await exec("edit.checkpoint")).checkpoint;
    let before;
    try {
      await exec("timeline.roll_to", { position: at });
      before = await mesh();
    } finally {
      await exec("edit.restore_checkpoint", { checkpoint: cp });
    }
    return { name, type: info.type, dialog: kind[0], definition: info.definition || {}, before,
             feature_names: Object.fromEntries(tl.map((f) => [String(f.id), f.name])) };
  }

  async function remove(name) {
    const failingBefore = await errors();
    if (!(await timeline()).some((f) => f.name === name)) throw new ApiError(404, `feature not found: ${name}`);
    try {
      await exec("timeline.delete", { features: [name] });
    } catch (err) {
      throw new ApiError(400, shortError(err));
    }
    const now = await errors();
    done.push({ label: `Delete ${name}` });
    undone.length = 0;
    version++;
    stepped = true;
    return { done: `Deleted ${name}`, deleted: [name],
             failing: Object.fromEntries(Object.entries(now).filter(([k]) => !(k in failingBefore))) };
  }

  async function sketches() {
    const tl = await timeline();
    const byId = Object.fromEntries(tl.map((f) => [f.id, f.name]));
    const used = {};
    for (const f of tl) {
      if (f.type === "Sketch") continue;
      const def = (await exec("timeline.inspect", { feature: f.id })).definition || {};
      if (byId[def.sketch]) (used[byId[def.sketch]] ||= []).push(f.name);
    }
    return { sketches: tl.filter((f) => f.type === "Sketch").map((f) => ({ name: f.name, used_by: used[f.name] || [] })) };
  }

  // Each hand step here is one SolidCraft command, so one step of the app's own undo history
  async function undoRedo(which) {
    const from = which === "undo" ? done : undone, to = which === "undo" ? undone : done;
    if (!from.length) throw new ApiError(404, `nothing to ${which}`);
    await exec(which === "undo" ? "edit.undo" : "edit.redo");
    to.push(from.pop());
    version++;
    stepped = true;
    return { [which === "undo" ? "undone" : "redone"]: to[to.length - 1].label };
  }

  // The server's api/* endpoints the workspace calls, answered here
  async function api(method, path, body) {
    const url = new URL(path, "http://demo/");
    const route = url.pathname.replace(/^\/api\//, "");
    if (route === "hole_sizes") {
      if (!holeSizes) holeSizes = await (await fetch("hole_sizes.json")).json();
      return holeSizes;
    }
    if (route === "history") {
      return { busy: !app && !!booting, undo: done.at(-1)?.label ?? null, redo: undone.at(-1)?.label ?? null };
    }
    if (!files) files = await (await fetch(`${base()}files.json`)).json();
    if (files.kind === "assembly" && /^feature|^sketch/.test(route)) {
      throw new ApiError(403, "features are added in a part: open one of the parts in Model by hand");
    }
    await boot();
    if (route === "version") return { version, name: files.document.replace(/\.solidcraft$/, ""), kind: files.kind || "part" };
    if (route === "mesh") return mesh();
    if (route === "tree") return tree();
    if (route === "findings") return findings();
    if (route === "sketches") return sketches();
    if (route === "sketch_plane") return sketchPlane(url);
    if (route === "feature" && method === "GET") return featureForEdit(url.searchParams.get("name") || "");
    if (route === "feature") return feature(body);
    if (route === "feature/delete") return remove(body.name);
    if (route === "agent/undo") return undoRedo("undo");
    if (route === "agent/redo") return undoRedo("redo");
    throw new ApiError(404, `not available in the live demo: ${route}`);
  }

  return {
    api,
    get started() { return !!app; },
    // a step was made here: the page shows the kernel's model from now on, not the precomputed files
    get changed() { return stepped; },
  };
}
