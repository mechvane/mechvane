// Live demo: play back a recorded agent session (#124). The recording (tools/record_replay.py) holds the chat
// events of a real session; the model after each change was computed when the site was built
// (demos/<name>/replay/<k>/), so the page swaps those in and the workspace shows the change as after any step
// (ghost of the state before, marks in the model browser, "Last step", the findings).
//   setBase(path)   where the workspace reads version/mesh/tree/findings from
//   reload(fit)     load them again (loadAll)
//   kernelChanged() whether the visitor made steps in the demo (then the page starts afresh first)

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function initReplay({ button, chatRoot, setBase, reload, kernelChanged }) {
  const log = chatRoot.querySelector(".chat-log");
  const composer = chatRoot.querySelector(".chat-composer");
  const hint = chatRoot.querySelector(".composer-hint");
  const summary = chatRoot.querySelector("summary");
  let demo = null, base = "", playing = null, paused = false, wake = null;

  const bar = document.createElement("div");
  bar.className = "replay-bar";
  bar.setAttribute("role", "group");
  bar.setAttribute("aria-label", "Recorded session");
  bar.hidden = true;
  const label = document.createElement("span");
  label.className = "replay-label";
  const pauseBtn = document.createElement("button");
  const stopBtn = document.createElement("button");
  const againBtn = document.createElement("button");
  for (const [b, text] of [[pauseBtn, "Pause"], [stopBtn, "Reset demo"], [againBtn, "Watch again"]]) {
    b.type = "button";
    b.className = "btn-text replay-btn";
    b.textContent = text;
  }
  againBtn.hidden = true;
  bar.append(label, pauseBtn, againBtn, stopBtn);
  chatRoot.querySelector(".chat-body").prepend(bar);

  // while the session plays, the dialogs and their keys rest: a step of the visitor's would land on the example
  // as it was, not on the model shown
  const blockKeys = (e) => {
    if (e.target && e.target.closest && e.target.closest(".replay-bar")) return;
    if (e.key === "Escape") { stop(); return; }
    if (e.key !== "Tab") e.stopImmediatePropagation();
  };

  const add = (cls, text) => {
    const li = document.createElement("li");
    li.className = cls;
    li.textContent = text;
    const working = log.querySelector(".working");
    (working ? working.before(li) : log.append(li));
    log.scrollTop = log.scrollHeight;
    return li;
  };
  const setWorking = (on) => {
    const w = log.querySelector(".working");
    if (on && !w) {
      const li = document.createElement("li");
      li.className = "working";
      li.textContent = "Working…";
      log.append(li);
    }
    if (!on && w) w.remove();
  };

  // the same lines as the live chat (chat.js)
  const tools = new Map();
  function show(e) {
    if (e.type === "user") {
      add("you", e.text);
      setWorking(true);
    } else if (e.type === "text") {
      add("agent", e.text);
    } else if (e.type === "tool" && e.tool) {
      tools.set(e.id, add("tool running", e.tool));
    } else if (e.type === "tool" && tools.has(e.id)) {
      const el = tools.get(e.id);
      el.className = "tool " + (e.status === "failed" ? "failed" : "ok");
      if (e.status === "failed" && e.error) {
        const err = e.error.replace(/```/g, "").trim();
        el.title = err;
        el.textContent += ` – ${err.slice(0, 160)}`;
      }
    } else if (e.type === "declined") {
      add("tool declined", `${e.tool}: declined, ${e.reason}`);
    } else if (e.type === "done") {
      setWorking(false);
      const files = [...(e.changed || []), ...(e.removed || [])];
      add("note", files.length ? "✓ Changed " + files.join(", ") : "No files changed");
    }
  }

  async function wait(ms) {
    let until = performance.now() + ms;
    for (;;) {
      if (!playing) return false;
      if (paused) {
        const left = until - performance.now();
        await new Promise((r) => { wake = r; });
        until = performance.now() + left;
        continue;
      }
      const left = until - performance.now();
      if (left <= 0) return true;
      await Promise.race([sleep(Math.min(left, 200)), new Promise((r) => { wake = r; })]);
    }
  }

  async function play() {
    // always from the example as published (after an earlier run the workspace shows its last state)
    setBase(base);
    await reload(true);  // as on opening: no "Last step" from the end of the run back to the start
    const rec = await (await fetch(`${base}replay.json`, { cache: "no-store" })).json();
    const run = (playing = {});
    paused = false;
    tools.clear();
    log.replaceChildren();
    chatRoot.hidden = false;
    chatRoot.open = true;
    composer.hidden = true;
    if (hint) hint.hidden = true;
    bar.hidden = false;
    againBtn.hidden = true;
    pauseBtn.hidden = false;
    pauseBtn.textContent = "Pause";
    stopBtn.textContent = "Stop";
    label.textContent = "Recorded session";
    label.title = rec.recorded || "";
    if (summary) summary.querySelector("h2").textContent = "Agent (recorded)";
    document.body.classList.add("replaying");
    window.addEventListener("keydown", blockKeys, true);
    button.disabled = true;
    let prev = 0;
    for (const step of rec.steps) {
      if (!(await wait((step.t - prev) * 1000))) return;
      if (playing !== run) return;
      prev = step.t;
      show(step.event);
      if (step.event.frame) {
        setBase(`${base}replay/${step.event.frame}/`);
        await reload(false);
      }
    }
    if (playing !== run) return;
    playing = null;
    pauseBtn.hidden = true;
    againBtn.hidden = false;
    stopBtn.textContent = "Reset demo";
    label.textContent = "End of the recorded session";
    button.disabled = false;
  }

  // restore: show the example as published again (not when another example was just opened)
  async function stop(restore = true) {
    playing = null;
    if (wake) wake();
    window.removeEventListener("keydown", blockKeys, true);
    document.body.classList.remove("replaying");
    bar.hidden = true;
    composer.hidden = false;
    chatRoot.hidden = true;
    if (summary) summary.querySelector("h2").textContent = "Agent";
    button.disabled = false;
    if (!restore) return;
    setBase(base);
    await reload(true);
  }

  pauseBtn.addEventListener("click", () => {
    paused = !paused;
    pauseBtn.textContent = paused ? "Resume" : "Pause";
    label.textContent = paused ? "Paused" : "Recorded session";
    if (!paused && wake) wake();
  });
  stopBtn.addEventListener("click", () => { stop(); });
  againBtn.addEventListener("click", () => { play(); });
  button.addEventListener("click", () => {
    if (!demo) return;
    // the visitor made steps in SolidCraft in the page: start from the example as published
    if (kernelChanged()) { location.search = `?demo=${encodeURIComponent(demo.name)}&replay=1`; return; }
    play();
  });

  return {
    // the example shown changed: offer its recording, if it has one; ?replay=1 starts it at once
    async update(entry, demoBase, autostart = false) {
      if (playing || !bar.hidden) await stop(false);
      demo = entry && entry.replay ? entry : null;
      base = demoBase;
      button.hidden = !demo;
      if (demo) button.title = demo.replay;
      if (demo && autostart) play();
    },
  };
}
