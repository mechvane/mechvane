// General command dialog (#128): Ctrl+K searches every SolidCraft command, the form comes from the command's
// input schema (/api/command, made by mechvane/command_form.py), Preview and OK go through /api/feature with
// generic: true, so a change is one entry of the same undo list as the other dialogs and the agent's turns.
// A command that only reads (inspect, list ...) shows its result in the dialog and leaves no undo entry.

const MAX_RESULTS = 40;

// How well q matches s (0 = not at all): a prefix beats a word start beats a substring beats the letters in
// order with gaps. Same ranking as SolidCraft's own command box (crates/ui-egui/src/shortcut_box.rs, score).
export function scoreMatch(q, s) {
  if (!q) return 1;
  s = String(s || "").toLowerCase();
  if (s.startsWith(q)) return 1000 - Math.min(s.length, 500);
  if (s.split(/[^\p{L}\p{N}]+/u).some((w) => w.startsWith(q))) return 800;
  if (s.includes(q)) return 600;
  let gaps = 0, i = 0, lastHit = true;
  for (const qc of q) {
    let found = false;
    while (i < s.length) {
      const c = s[i++];
      if (c === qc) { found = true; break; }
      if (lastHit) gaps++;
      lastHit = false;
    }
    if (!found) return 0;
    lastHit = true;
  }
  return Math.max(300 - gaps * 20, 10);
}

// The query matches the label and the id, and with a third of the weight the tab and panel (as SolidCraft).
// Offered commands come before the ones the dialog does not offer yet.
export function searchCommands(list, query) {
  const q = query.trim().toLowerCase();
  const rows = [];
  for (const c of list) {
    const s = Math.max(scoreMatch(q, c.label), Math.floor(scoreMatch(q, c.id) * 9 / 10),
      Math.floor(Math.max(scoreMatch(q, c.tab), scoreMatch(q, c.panel)) / 3));
    if (s > 0) rows.push([s + (c.offered ? 10000 : 0), c]);
  }
  rows.sort((a, b) => b[0] - a[0] || a[1].label.localeCompare(b[1].label));
  return rows.slice(0, MAX_RESULTS).map((r) => r[1]);
}

const NUMBER = /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i;

function expr(text) {
  const t = text.trim();
  return NUMBER.test(t) ? Number(t) : t;
}

// One field's value from what the form holds (strings), undefined when left empty. Throws with the field name
// on a value that cannot be one (bad JSON, not a number).
export function fieldValue(field, raw) {
  const name = field.name || "parameters";
  if (field.kind === "point") {
    if (raw.every((v) => !v.trim())) return undefined;
    return raw.map((v) => (v.trim() ? expr(v) : 0));
  }
  const t = typeof raw === "string" ? raw.trim() : raw;
  if (t === "" || t === undefined || t === null) return undefined;
  switch (field.kind) {
    case "expr": return expr(t);
    case "number": {
      const n = Number(t);
      if (!Number.isFinite(n) || (field.integer && !Number.isInteger(n))) throw new Error(`${name}: not ${field.integer ? "a whole number" : "a number"}`);
      return n;
    }
    case "bool": return t === "true";
    case "list": return t.split(",").map((x) => x.trim()).filter(Boolean);
    case "json":
      try {
        return JSON.parse(t);
      } catch (err) {
        throw new Error(`${name}: not valid JSON (${err.message})`);
      }
    default: return raw;
  }
}

// The command's params from the form's values ({field name: raw}); refuses a missing required field.
export function formParams(form, values) {
  if (form.raw) {
    const v = fieldValue(form.fields[0], values[""] ?? "");
    if (v !== undefined && (typeof v !== "object" || Array.isArray(v) || v === null)) throw new Error("the parameters must be a JSON object");
    return v || {};
  }
  const params = {};
  const missing = [];
  for (const f of form.fields) {
    const v = fieldValue(f, values[f.name] ?? (f.kind === "point" ? ["", "", ""] : ""));
    if (v === undefined) {
      if (f.required) missing.push(f.name);
    } else params[f.name] = v;
  }
  if (missing.length) throw new Error(`required: ${missing.join(", ")}`);
  return params;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const PICK_HINT = {
  edges: "edges, each [x, y, z] on it", faces: "faces, each [x, y, z] on it", bodies: "body names",
  features: "feature names", sketch: "a sketch name", components: "component names or ids",
};

// A click in the view for a pick field (field.pick edges|faces|bodies, field.write point|key:face|key:edge|name):
// the picks so far ([{key, value}]) → the new picks. A list field toggles the clicked item, a single field
// takes it. pick: {key, point: [x, y, z], body}.
export function applyPick(field, picks, pick) {
  const value = field.write === "name" ? pick.body
    : field.write && field.write.startsWith("key:") ? { [field.write.slice(4)]: pick.point } : pick.point;
  const key = field.write === "name" ? `body|${pick.body}` : pick.key;
  if (!field.multi) return [{ key, value }];
  return picks.some((p) => p.key === key) ? picks.filter((p) => p.key !== key) : [...picks, { key, value }];
}

// What the field's control shows for the picks: JSON for a json field, names for a text or list field.
export function pickText(field, picks) {
  if (!picks.length) return "";
  const values = picks.map((p) => p.value);
  if (field.kind === "json") return JSON.stringify(field.multi ? values : values[0]);
  return field.multi ? values.join(", ") : values[0];
}

// A point on a curved face onto the true surface: the mesh is flat between its vertices, so a click on a
// cylinder lies on a chord, inside the face, and SolidCraft could take a neighbouring face for it (narrow
// rounds). info: faceInfo's {center, axis, radius} (THREE vectors) for a cylinder; point: [x, y, z].
export function ontoFace(point, info) {
  if (!info || info.normal || !info.axis || !info.center || !info.radius) return point.map((v) => +v.toFixed(6));
  const c = [info.center.x, info.center.y, info.center.z];
  const len = Math.hypot(info.axis.x, info.axis.y, info.axis.z);
  const a = [info.axis.x / len, info.axis.y / len, info.axis.z / len];
  const d = point.map((v, i) => v - c[i]);
  const t = d[0] * a[0] + d[1] * a[1] + d[2] * a[2];
  const r = d.map((v, i) => v - t * a[i]);
  const rl = Math.hypot(...r);
  if (rl < 1e-9) return point.map((v) => +v.toFixed(6));
  return c.map((v, i) => +(v + t * a[i] + (r[i] / rl) * info.radius).toFixed(6));
}

const PICK_LABEL = { edges: "edges", faces: "faces", bodies: "bodies" };

function controlHtml(f, i) {
  const ph = (t) => (t ? ` placeholder="${esc(t)}"` : "");
  const dflt = f.default !== undefined ? `default ${JSON.stringify(f.default)}` : (f.required ? "required" : "");
  switch (f.kind) {
    case "enum":
      return `<select data-field="${i}">${f.required ? "" : `<option value="">${esc(dflt || "default")}</option>`}`
        + f.options.map((o) => `<option value="${esc(o)}">${esc(o)}</option>`).join("") + "</select>";
    case "bool":
      return `<select data-field="${i}"><option value="">${esc(dflt || "default")}</option>`
        + `<option value="true">yes</option><option value="false">no</option></select>`;
    case "point":
      return `<span class="cmd-point">${["x", "y", "z"].map((a) => `<input data-field="${i}" data-axis="${a}"${ph(a)} spellcheck="false" autocomplete="off">`).join("")}</span>`;
    case "json":
      return `<textarea data-field="${i}" rows="${f.name ? 2 : 5}" spellcheck="false"${ph(f.pick ? `JSON: ${PICK_HINT[f.pick] || f.pick}` : (f.name ? "JSON" : "{ … }"))}></textarea>`;
    case "list":
      return `<input data-field="${i}"${ph(dflt || "a, b, …")} spellcheck="false" autocomplete="off">`;
    default:
      return `<input data-field="${i}"${ph(dflt)} spellcheck="false" autocapitalize="off" autocomplete="off">`;
  }
}

export function initCommandDialog({ propertiesEl, statusEl, post, get, showPreview, clearPreview, reload, closeOthers = () => {},
                                    viewTools = null, showPicks = () => {}, getSelection = () => [], log = () => {} }) {
  let list = null;          // [{id, label, tab, panel, offered, reason}] of the open document's SolidCraft
  let active = null;        // {form, el} of the open command form
  const emptyHtml = () => propertiesEl.dataset.emptyHtml;

  const palette = document.createElement("div");
  palette.className = "cmd-palette";
  palette.hidden = true;
  palette.innerHTML = `<input class="cmd-search" placeholder="Search commands (Ctrl+K)" spellcheck="false" autocomplete="off" aria-label="Search commands">
    <ul class="cmd-results" role="listbox"></ul><div class="cmd-palette-note"></div>`;
  document.body.append(palette);
  const input = palette.querySelector(".cmd-search");
  const results = palette.querySelector(".cmd-results");
  const note = palette.querySelector(".cmd-palette-note");
  let shown = [], index = 0;

  function renderResults() {
    shown = list ? searchCommands(list, input.value) : [];
    index = Math.min(index, Math.max(shown.length - 1, 0));
    results.innerHTML = shown.map((c, i) => `<li role="option" data-i="${i}" class="${i === index ? "active" : ""}${c.offered ? "" : " off"}"`
      + `${c.offered ? "" : ` title="${esc(c.reason)}"`}><span class="cmd-label">${esc(c.label)}</span>`
      + `<span class="cmd-id">${esc(c.id)}</span></li>`).join("");
    const cur = shown[index];
    note.textContent = !list ? "Loading commands…" : !shown.length ? "No command matches."
      : cur && !cur.offered ? `Not in the command dialog yet: ${cur.reason}` : "↑ ↓ to choose, Enter to open, Esc to close";
    results.querySelector("li.active")?.scrollIntoView({ block: "nearest" });
  }

  async function openPalette() {
    palette.hidden = false;
    input.value = "";
    index = 0;
    input.focus();
    log("command_search_open", {});
    // loaded on each opening: what is offered depends on the open document (a part or an assembly)
    renderResults();
    try {
      list = (await get("api/commands")).commands;
    } catch (err) {
      note.textContent = `Commands not available: ${err.message}`;
      return;
    }
    if (!palette.hidden) renderResults();
  }

  function closePalette() {
    palette.hidden = true;
  }

  input.addEventListener("input", () => { index = 0; renderResults(); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      index = Math.max(0, Math.min(shown.length - 1, index + (e.key === "ArrowDown" ? 1 : -1)));
      renderResults();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (shown[index]) choose(shown[index]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      closePalette();
    }
  });
  results.addEventListener("mousedown", (e) => {
    const li = e.target.closest("li[data-i]");
    if (!li) return;
    e.preventDefault();
    choose(shown[Number(li.dataset.i)]);
  });
  input.addEventListener("blur", () => setTimeout(() => { if (document.activeElement !== input) closePalette(); }, 0));

  function choose(c) {
    if (!c.offered) {
      note.textContent = `Not in the command dialog yet: ${c.reason}`;
      return;
    }
    closePalette();
    openForm(c.id);
  }

  async function openForm(id) {
    closeOthers();
    close();
    let form;
    try {
      form = await get(`api/command?id=${encodeURIComponent(id)}`);
    } catch (err) {
      statusEl.textContent = `${id}: ${err.message}`;
      return;
    }
    if (!form.offered) {
      statusEl.textContent = `${form.label}: not in the command dialog yet: ${form.reason}`;
      return;
    }
    if (propertiesEl.dataset.emptyHtml === undefined) propertiesEl.dataset.emptyHtml = propertiesEl.innerHTML;
    log("command_dialog_open", { command: id });
    const fields = form.fields.map((f, i) => `<label class="cmd-field" data-name="${esc(f.name)}" title="${esc(f.description)}">`
      + `<span>${esc(f.name || "parameters")}${f.required ? " *" : ""}</span>`
      + (f.pick ? `<span class="cmd-pickwrap">${controlHtml(f, i)}<button type="button" class="btn-text cmd-pick" data-pick="${i}"`
        + ` title="Click ${PICK_LABEL[f.pick]} in the view${f.multi ? " (again to remove)" : ""}">Pick</button></span>` : controlHtml(f, i))
      + "</label>").join("");
    propertiesEl.innerHTML = `
      <form class="feature-dialog cmd-dialog" autocomplete="off">
        <div class="feature-dialog-title"></div>
        <div class="cmd-command"></div>
        <div class="cmd-description"></div>
        ${fields || '<div class="cmd-description">No parameters.</div>'}
        <details class="cmd-help"><summary>SolidCraft's parameters</summary><pre></pre></details>
        <div class="feature-delta"></div>
        <div class="feature-error" hidden></div>
        <pre class="cmd-result" hidden></pre>
        <div class="feature-actions">
          <button type="button" class="btn-text feature-cancel">Close</button>
          <button type="button" class="btn-text cmd-preview">Preview</button>
          <button type="submit" class="feature-ok">OK</button>
        </div>
      </form>`;
    const el = propertiesEl.querySelector("form");
    el.querySelector(".feature-dialog-title").textContent = form.label;
    el.querySelector(".cmd-command").textContent = form.id;
    el.querySelectorAll(".cmd-description")[0].textContent = form.description || "";
    el.querySelector(".cmd-help pre").textContent = form.help || "";
    active = { form, el, busy: false, picks: new Map(), pickField: null, pickEdges: new Map() };
    el.addEventListener("submit", (e) => { e.preventDefault(); run(false); });
    el.querySelector(".cmd-preview").addEventListener("click", () => run(true));
    el.querySelector(".feature-cancel").addEventListener("click", close);
    el.addEventListener("input", (e) => {
      if (!active) return;
      clearPreview();
      setText(".feature-delta", "");
      // typed by hand: the text is the value now, the picks shown for it are gone
      const i = e.target.dataset?.field;
      if (i !== undefined && active.picks.has(Number(i))) {
        active.picks.delete(Number(i));
        drawPicks();
      }
    });
    el.querySelectorAll(".cmd-pick").forEach((b) => b.addEventListener("click", (e) => {
      e.preventDefault();
      const i = Number(b.dataset.pick);
      if (active.pickField === i) stopPick();
      else startPick(i);
    }));
    prefill();
    el.querySelector("[data-field]")?.focus();
  }

  function setText(sel, text) {
    const n = active.el.querySelector(sel);
    n.textContent = text;
    n.hidden = !text;
  }

  function values() {
    const out = {};
    active.form.fields.forEach((f, i) => {
      const nodes = [...active.el.querySelectorAll(`[data-field="${i}"]`)];
      out[f.name] = f.kind === "point" ? nodes.map((n) => n.value) : nodes[0].value;
    });
    return out;
  }

  async function run(preview) {
    if (!active || active.busy) return;
    const dlg = active;
    let params;
    try {
      params = formParams(dlg.form, values());
    } catch (err) {
      setText(".feature-error", err.message);
      return;
    }
    dlg.busy = true;
    setText(".feature-error", "");
    setText(".cmd-result", "");
    setText(".feature-delta", preview ? "Computing preview…" : "Running…");
    log(preview ? "command_dialog_preview" : "command_dialog_ok", { command: dlg.form.id, params });
    try {
      const res = await post("api/feature", { command: dlg.form.id, params, generic: true, preview });
      if (active !== dlg) return;
      if (preview) {
        if (res.mesh) showPreview(res.mesh);
        else clearPreview();
        setText(".feature-delta", res.changed ? "Preview: the design changes (nothing saved)." : "Preview: the design stays as it is.");
        if (!res.changed) setText(".cmd-result", JSON.stringify(res.results, null, 1));
      } else if (res.changed) {
        close();
        await reload();
        statusEl.textContent = res.done || "Done";
      } else {
        // only read: the answer stays in the dialog, nothing to undo
        setText(".feature-delta", "Done; the design is unchanged.");
        setText(".cmd-result", JSON.stringify(res.results, null, 1));
      }
    } catch (err) {
      if (active !== dlg) return;
      log("command_dialog_error", { command: dlg.form.id, error: String(err.message).split("\n")[0] });
      setText(".feature-delta", "");
      setText(".feature-error", err.message);
    } finally {
      dlg.busy = false;
    }
  }

  // Picks in the view: one field at a time takes clicks (edges, faces, or a face's body)
  function startPick(i) {
    stopPick();
    const f = active.form.fields[i];
    if (!viewTools || !f?.pick) return;
    active.pickField = i;
    active.el.querySelector(`[data-pick="${i}"]`)?.classList.add("active");
    const onPick = (raw) => {
      if (!active || active.pickField !== i) return;
      let pick;
      if (f.pick === "edges") {
        pick = { key: raw.key, point: raw.point, body: raw.body };
        active.pickEdges.set(raw.key, raw.edge);
      } else {
        const p = raw.point.toArray ? raw.point.toArray() : raw.point;
        pick = { key: `face|${raw.body}|${raw.face}`, point: ontoFace(p, raw.info), body: raw.body };
      }
      const next = applyPick(f, active.picks.get(i) || [], pick);
      active.picks.set(i, next);
      writePicks(i);
      log("command_dialog_pick", { command: active.form.id, field: f.name, pick: f.pick, count: next.length });
    };
    if (f.pick === "edges") viewTools.startEdgePick(onPick);
    else viewTools.startFacePick(onPick);
  }

  function stopPick() {
    if (!active || active.pickField === null) return;
    active.el.querySelector(`[data-pick="${active.pickField}"]`)?.classList.remove("active");
    active.pickField = null;
    viewTools?.stopEdgePick();
  }

  function writePicks(i) {
    const f = active.form.fields[i];
    const node = active.el.querySelector(`[data-field="${i}"]`);
    if (node) node.value = pickText(f, active.picks.get(i) || []);
    clearPreview();
    setText(".feature-delta", "");
    drawPicks();
  }

  function drawPicks() {
    if (!active) return showPicks([]);
    const out = [];
    active.picks.forEach((picks, i) => {
      const f = active.form.fields[i];
      for (const p of picks) {
        if (f.pick === "edges") out.push({ kind: "edge", edge: active.pickEdges.get(p.key), point: p.value.edge || p.value });
        else if (f.pick === "faces") out.push({ kind: "point", point: p.value.face || p.value });
      }
    });
    showPicks(out);
  }

  // Faces selected in the view before the dialog opened fill its first faces field (not a body field: a face
  // selected for the agent would silently change the target body of a command)
  async function prefill() {
    let sel = [];
    try {
      sel = (await getSelection()) || [];
    } catch {
      return;
    }
    const faces = sel.filter((s) => s.type === "face" && s.point);
    if (!active || !faces.length) return;
    const fields = active.form.fields;
    const i = fields.findIndex((f) => f.pick === "faces");
    if (i < 0) return;
    const f = fields[i];
    let picks = [];
    for (const s of faces) {
      const pick = { key: `face|${s.body}|${s.index}`, point: s.point, body: s.body };
      picks = applyPick(f, picks, pick);
      if (!f.multi) break;
    }
    active.picks.set(i, picks);
    writePicks(i);
  }

  function close() {
    if (!active) return;
    stopPick();
    const { el } = active;
    active = null;
    showPicks([]);
    clearPreview();
    // another dialog may have taken the panel meanwhile: only put the panel back when it still shows this form
    if (el.isConnected && emptyHtml() !== undefined) propertiesEl.innerHTML = emptyHtml();
  }

  return {
    open: openPalette,
    openForm,
    close() { closePalette(); close(); },
    isOpen: () => !palette.hidden || !!active,
    // the model was reloaded (agent, undo): the commands stay, nothing to clear
    // the model was reloaded under the form (agent, undo): picked edges and faces may be gone, as in the
    // feature dialogs; the picks and their text are cleared
    modelChanged() {
      if (!active || active.busy) return;
      active.picks.forEach((_, i) => {
        const node = active.el.querySelector(`[data-field="${i}"]`);
        if (node) node.value = "";
      });
      active.picks.clear();
      active.pickEdges.clear();
      drawPicks();
    },
  };
}
