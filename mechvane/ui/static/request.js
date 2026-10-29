// Request a feature dialog and GitHub Issue URL generator for Mechvane.

const GITHUB_NEW_ISSUE_URL = "https://github.com/mechvane/mechvane/issues/new";

let cachedAbout = null;

export function shortenUserAgent(ua = (typeof navigator !== "undefined" ? navigator.userAgent : "") || "") {
  let browser = "";
  if (/edg\/(\d+[\.\d]*)/i.test(ua)) browser = `Edge/${RegExp.$1}`;
  else if (/chrome\/(\d+[\.\d]*)/i.test(ua)) browser = `Chrome/${RegExp.$1}`;
  else if (/firefox\/(\d+[\.\d]*)/i.test(ua)) browser = `Firefox/${RegExp.$1}`;
  else if (/version\/(\d+[\.\d]*).*safari/i.test(ua)) browser = `Safari/${RegExp.$1}`;
  else browser = "Browser";

  let os = "";
  if (/windows nt 10/i.test(ua)) os = "Windows 10/11";
  else if (/windows/i.test(ua)) os = "Windows";
  else if (/mac os x (\d+[_\.\d]*)/i.test(ua)) os = `macOS ${RegExp.$1.replace(/_/g, ".")}`;
  else if (/android/i.test(ua)) os = "Android";
  else if (/linux/i.test(ua)) os = "Linux";
  else if (/iphone|ipad|ipod/i.test(ua)) os = "iOS";
  else os = "OS";

  return `${browser} on ${os}`;
}

export function getOpenDocumentName() {
  const el = typeof document !== "undefined" ? document.getElementById("doc-name") : null;
  let name = el ? el.textContent.trim() : "";
  if (!name || name === "—") {
    if (typeof window !== "undefined" && window.location) {
      const params = new URLSearchParams(window.location.search);
      name = params.get("doc") || params.get("demo") || "";
    }
  }
  if (!name || name === "—") return "none";
  return name.split(/[/\\]/).pop() || "none";
}

export async function fetchAbout() {
  if (cachedAbout) return cachedAbout;
  const isStatic = typeof document !== "undefined" && document.documentElement.dataset.static === "1";
  const endpoints = isStatic ? ["about.json", "/about.json"] : ["api/about", "/api/about"];
  for (const ep of endpoints) {
    try {
      const resp = await fetch(ep);
      if (resp.ok) {
        cachedAbout = await resp.json();
        return cachedAbout;
      }
    } catch {
      // try next endpoint
    }
  }
  return {
    mechvane: isStatic ? "live demo" : "unknown",
    solidcraft: isStatic ? "live demo" : "unknown",
  };
}

export function buildIssueUrl({ type, title, description, includeVersions, about, docName, shortUa }) {
  const issueTitle = `[${type}] ${title.trim()}`;
  let body = `### What\n\n${(description || "").trim()}\n\n### Why\n\n`;

  if (includeVersions) {
    const mvVer = (about && about.mechvane) || "unknown";
    const scVer = (about && about.solidcraft) || "unknown";
    const browser = shortUa || shortenUserAgent();
    const doc = docName || "none";
    body += `\n### Environment\n\n- Mechvane: ${mvVer}\n- SolidCraft: ${scVer}\n- Browser: ${browser}\n- Document: ${doc}\n`;
  }

  if (body.length > 6000) {
    body = body.slice(0, 6000);
  }

  const params = new URLSearchParams();
  params.set("title", issueTitle);
  params.set("body", body);

  return `${GITHUB_NEW_ISSUE_URL}?${params.toString()}`;
}

export function ensureDialog() {
  let dialog = document.getElementById("request-feature-dialog");
  if (dialog) return dialog;

  dialog = document.createElement("dialog");
  dialog.id = "request-feature-dialog";
  dialog.className = "request-dialog";
  dialog.innerHTML = `
    <form method="dialog" class="request-form">
      <div class="request-dialog-header">
        <h3>Request a feature</h3>
        <button type="button" class="request-dialog-close" aria-label="Close">&times;</button>
      </div>
      <div class="request-dialog-body">
        <div class="request-field-group">
          <label for="request-type">Kind</label>
          <select id="request-type">
            <option value="Feature">Feature</option>
            <option value="Module">Module</option>
            <option value="Standard part">Standard part</option>
            <option value="Design rule">Design rule</option>
            <option value="Bug">Bug</option>
          </select>
        </div>
        <div class="request-field-group">
          <label for="request-title">Title <span class="required">*</span></label>
          <input type="text" id="request-title" required placeholder="Short summary">
        </div>
        <div class="request-field-group">
          <label for="request-desc">Description</label>
          <textarea id="request-desc" rows="5" placeholder="Describe the feature or improvement..."></textarea>
        </div>
        <div class="request-checkbox-row">
          <label>
            <input type="checkbox" id="request-include-versions" checked>
            Include versions
          </label>
        </div>
        <div id="request-versions-preview" class="request-versions-preview">Loading version info…</div>
        <div class="request-dialog-note">
          Opens GitHub in a new tab. Nothing is sent until you submit it there.
        </div>
      </div>
      <div class="request-dialog-footer">
        <button type="button" class="btn-cancel">Cancel</button>
        <button type="submit" class="btn-submit">Open on GitHub</button>
      </div>
    </form>
  `;
  document.body.appendChild(dialog);

  const form = dialog.querySelector("form");
  const closeBtn = dialog.querySelector(".request-dialog-close");
  const cancelBtn = dialog.querySelector(".btn-cancel");
  const typeSelect = dialog.querySelector("#request-type");
  const titleInput = dialog.querySelector("#request-title");
  const descTextarea = dialog.querySelector("#request-desc");
  const includeVersionsCheckbox = dialog.querySelector("#request-include-versions");
  const versionsPreview = dialog.querySelector("#request-versions-preview");

  async function updateVersionsPreview() {
    if (!includeVersionsCheckbox.checked) {
      versionsPreview.style.display = "none";
      return;
    }
    versionsPreview.style.display = "block";
    const about = await fetchAbout();
    const docName = getOpenDocumentName();
    const shortUa = shortenUserAgent();
    versionsPreview.textContent = `Mechvane: ${about.mechvane || "—"} · SolidCraft: ${about.solidcraft || "—"} · ${shortUa} · Document: ${docName}`;
  }

  includeVersionsCheckbox.addEventListener("change", updateVersionsPreview);

  const closeDialog = () => {
    dialog.close();
  };

  closeBtn.addEventListener("click", closeDialog);
  cancelBtn.addEventListener("click", closeDialog);
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) dialog.close();
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = titleInput.value.trim();
    if (!title) {
      titleInput.reportValidity();
      titleInput.focus();
      return;
    }
    const type = typeSelect.value;
    const description = descTextarea.value;
    const includeVersions = includeVersionsCheckbox.checked;
    const about = includeVersions ? await fetchAbout() : {};
    const docName = getOpenDocumentName();
    const shortUa = shortenUserAgent();

    const url = buildIssueUrl({
      type,
      title,
      description,
      includeVersions,
      about,
      docName,
      shortUa,
    });

    window.open(url, "_blank", "noopener,noreferrer");
    dialog.close();
  });

  dialog._updateVersionsPreview = updateVersionsPreview;
  return dialog;
}

export function initRequestFeature() {
  const btn = document.getElementById("btn-request-feature");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const dialog = ensureDialog();
    const titleInput = dialog.querySelector("#request-title");
    if (dialog._updateVersionsPreview) {
      dialog._updateVersionsPreview();
    }
    dialog.showModal();
    if (titleInput) titleInput.focus();
  });
}

// Whether closing this window stops Mechvane: an app window owns the server, a browser tab does not,
// so a tab gets a Quit button instead. The server learns it owns the window a few seconds after start.
async function showRunState(el) {
  let about = {};
  try {
    const resp = await fetch("api/about", { cache: "no-store" });
    if (resp.ok) about = await resp.json();
  } catch {
    return;
  }
  const quit = el.querySelector("button");
  const note = el.querySelector("span");
  note.textContent = about.stops_with_window ? "Closing this window quits Mechvane" : "Runs until you quit it";
  quit.hidden = !!about.stops_with_window;
  el.hidden = false;
}

export function initRunState() {
  const right = document.querySelector(".topbar-right");
  if (!right || document.documentElement.dataset.static === "1") return;
  const el = document.createElement("span");
  el.className = "run-state";
  el.hidden = true;
  el.innerHTML = '<span class="status-text"></span><button type="button" class="btn-text" hidden>Quit</button>';
  el.querySelector("button").addEventListener("click", async () => {
    try {
      await fetch("api/quit", { method: "POST" });
    } catch {
      // the server may already be gone
    }
    document.body.innerHTML = '<p class="run-stopped">Mechvane has stopped. You can close this tab.</p>';
  });
  right.prepend(el);
  showRunState(el);
  setTimeout(() => showRunState(el), 5000);
}

function init() {
  initRequestFeature();
  initRunState();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}
