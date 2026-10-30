// The agent chat (ADR 0003) on both pages: on the Check page the selection comes from the 3D view's
// Select tool, in "Model by hand" from the SolidCraft app, which also has to save before each turn.
//   getSelection()   the selected items (may return a promise)
//   beforeSend()     before a turn goes out; return false to cancel it
//   beforeAction()   before undo or redo
//   onBusy(busy)     the agent started or stopped working
//   onChanged()      the agent changed files (not called for the turns already there on page load)
//   onIdle()         nothing is running any more, also after a refused send, undo or redo

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function initAgentChat({ root, getSelection, clearSelection, beforeSend, beforeAction, onBusy, onChanged, onIdle }) {
  const $ = (sel) => root.querySelector(sel);
  const log = $(".chat-log");
  const input = $(".chat-input");
  const sendBtn = $(".send-btn");
  const undoBtn = $(".chat-undo");
  const redoBtn = $(".chat-redo");
  let next = 0, busy = false, agentText = null, working = null, polling = false;
  let spoken = null;  // the selection when the user started to speak
  const tools = new Map();

  const add = (cls, text) => {
    const li = document.createElement("li");
    li.className = cls;
    li.textContent = text;
    (working ? working.before(li) : log.append(li));
    log.scrollTop = log.scrollHeight;
    return li;
  };
  const show = (state) => {
    busy = state.busy;
    sendBtn.classList.toggle("stop", busy);
    sendBtn.textContent = busy ? "■" : "↑";
    sendBtn.title = busy ? "Stop" : "Send";
    undoBtn.hidden = busy || !state.undo;
    undoBtn.textContent = state.undo ? "↶ Undo: " + state.undo : "";
    if (busy && !working) {
      working = document.createElement("li");
      working.className = "working";
      working.textContent = "Working…";
      log.append(working);
    }
    if (!busy && working) { working.remove(); working = null; }
    if (onBusy) onBusy(busy);
  };
  const idle = () => { if (onIdle) onIdle(); };
  const selected = async () => (getSelection ? (await getSelection()) || [] : []);

  async function poll(initial = false) {
    if (polling) return;
    polling = true;
    try {
      for (;;) {
        const st = await (await fetch("api/agent/events?since=" + next)).json();
        next = st.next;
        let changed = false;
        for (const e of st.events) {
          if (e.type === "user") {
            agentText = null;
            const li = add("you", e.text);
            if (e.selected) {
              const sel = document.createElement("span");
              sel.className = "sel";
              sel.textContent = e.selection_names && e.selection_names.length
                ? "Selected: " + e.selection_names.join(", ") : `${e.selected} selected`;
              li.append(sel);
            }
          } else if (e.type === "text") {
            if (!agentText) agentText = add("agent", "");
            agentText.textContent += e.text;
          } else if (e.type === "tool" && e.tool) {
            agentText = null;
            tools.set(e.id, add("tool running", e.tool));
          } else if (e.type === "tool" && tools.has(e.id)) {
            const el = tools.get(e.id);
            el.className = "tool " + (e.status === "failed" ? "failed" : "ok");
            if (e.status === "failed" && e.error) { el.title = e.error; el.textContent += ` – ${e.error.slice(0, 160)}`; }
          } else if (e.type === "declined") {
            agentText = null;
            add("tool declined", `${e.tool}: declined, ${e.reason}`);
          } else if (e.type === "done") {
            agentText = null;
            changed = e.changed.length > 0 || e.removed.length > 0;
            add("note", changed ? "✓ Changed " + [...e.changed, ...e.removed].join(", ") : "No files changed");
          } else if (e.type === "status" && e.status === "stopped") {
            add("note", "Stopped. The files are as before this message.");
            changed = true;
          } else if (e.type === "error") {
            add("err", `Error: ${e.error}. The files are as before this message.`);
            changed = true;
          } else if (e.type === "undone" || e.type === "redone") {
            add("note", e.type === "undone" ? "↶ Undone" : "↷ Redone");
            changed = true;
          }
        }
        show(st);
        if (st.busy) redoBtn.hidden = true;
        if (changed && onChanged && !initial) await onChanged();  // on page load the view has these files
        if (!st.busy) break;
        await sleep(700);
      }
    } finally {
      polling = false;
      idle();
    }
  }

  async function send() {
    const text = input.value.trim();
    if (!text || busy) return;
    if (beforeSend && (await beforeSend()) === false) return;
    let sel = spoken || await selected();
    spoken = null;
    if (sel.length) {
      const rr = await fetch("api/resolve_selection", { method: "POST", body: JSON.stringify({ items: sel }) });
      if (rr.ok) sel = (await rr.json()).selection;
    }
    input.value = "";
    const r = await fetch("api/agent/send", { method: "POST", body: JSON.stringify({ text, selection: sel }) });
    const res = await r.json();
    if (!r.ok) { add("err", res.error); idle(); return; }
    if (clearSelection) clearSelection();
    show({ busy: true, undo: null });
    poll();
  }

  async function act(path, label) {
    if (beforeAction) beforeAction();
    const r = await fetch("api/agent/" + path, { method: "POST", body: "{}" });
    const res = await r.json();
    if (!r.ok) {
      idle();
      if (r.status === 409 && path === "undo" && confirm(res.error + "\n\nUndo anyway?")) {
        await fetch("api/agent/undo", { method: "POST", body: JSON.stringify({ force: true }) });
      } else { add("err", label + ": " + res.error); return; }
    }
    if (path === "undo") redoBtn.hidden = false;
    if (path === "redo") redoBtn.hidden = true;
    await poll();
  }

  sendBtn.addEventListener("click", () => (busy ? fetch("api/agent/stop", { method: "POST", body: "{}" }) : send()));
  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
  undoBtn.addEventListener("click", () => act("undo", "Undo"));
  redoBtn.addEventListener("click", () => act("redo", "Redo"));
  initSpeech(root.querySelector(".mic-btn"), input, root.querySelector(".composer-hint"), selected,
    (sel) => { if (sel.length) spoken = sel; });
  root.hidden = false;
  poll(true);
}

// Hold the microphone button and speak (ADR 0003, 4): the browser's speech recognition, then Mechvane's
// clean-up on the server (numbers, units, "Fase", names in the model). The selection at the moment the
// user starts to speak is the one meant by "here".
function initSpeech(btn, input, hint, selected, keepSelection) {
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!btn || !Rec) return;  // Firefox, WebKitGTK: type instead
  btn.hidden = false;
  const KEY = "mechvane.speech.ok";
  const allowed = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return false; } };
  let rec = null, heard = "", before = "";
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    if (!allowed()) {
      if (!confirm("Speech input uses your browser's online speech service (Google for Chrome, Microsoft for Edge): what you say is sent there to be written down. Turn it on?")) return;
      try { localStorage.setItem(KEY, "1"); } catch {}
    }
    heard = "";
    before = input.value;
    selected().then(keepSelection).catch(() => {});
    rec = new Rec();
    rec.lang = "de-DE";
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (ev) => {
      let final = "", interim = "";
      for (const r of ev.results) (r.isFinal ? (final += r[0].transcript) : (interim += r[0].transcript));
      heard = final || interim;
      input.value = (before ? before + " " : "") + heard;
    };
    rec.onerror = (ev) => { if (hint) hint.textContent = "Speech: " + ev.error; };
    rec.onend = async () => {
      btn.classList.remove("listening");
      rec = null;
      if (!heard.trim()) return;
      const r = await fetch("api/speech", { method: "POST", body: JSON.stringify({ text: heard }) }).catch(() => null);
      input.value = (before ? before + " " : "") + (r && r.ok ? (await r.json()).text : heard);
      input.focus();
    };
    btn.classList.add("listening");
    rec.start();
  });
  const stop = () => { if (rec) rec.stop(); };
  btn.addEventListener("pointerup", stop);
  btn.addEventListener("pointerleave", stop);
}
