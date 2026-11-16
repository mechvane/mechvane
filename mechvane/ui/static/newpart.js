// "New part" dialog of the workspace (File menu): asks for the file name in the app's own dialog instead of
// the browser's prompt(), creates the part through api/new and reports errors (name taken, bad name) inline.

import { openStepBrowseDialog } from "./folder.js";

function suggestName(existing) {
  const taken = new Set(existing.map((n) => n.toLowerCase()));
  for (let i = 1; i < 1000; i++) {
    const name = `part_${i}`;
    if (!taken.has(`${name}.solidcraft`)) return name;
  }
  return "part";
}

function ensureDialog() {
  let dialog = document.getElementById("new-part-dialog");
  if (dialog) return dialog;
  dialog = document.createElement("dialog");
  dialog.id = "new-part-dialog";
  dialog.className = "request-dialog";
  dialog.innerHTML = `
    <form method="dialog" class="request-form">
      <div class="request-dialog-header">
        <h3>New part</h3>
        <button type="button" class="request-dialog-close" aria-label="Close">&times;</button>
      </div>
      <div class="request-dialog-body">
        <div class="request-field-group">
          <label for="new-part-name">File name <span class="required">*</span></label>
          <input type="text" id="new-part-name" required autocomplete="off" spellcheck="false">
        </div>
        <div class="request-dialog-note">Saved as <span id="new-part-file"></span> in this folder.</div>
        <div id="new-part-error" class="new-part-error" role="alert" hidden></div>
      </div>
      <div class="request-dialog-footer">
        <button type="button" class="btn-cancel">Cancel</button>
        <button type="submit" class="btn-submit">Create</button>
      </div>
    </form>
  `;
  document.body.appendChild(dialog);
  const input = dialog.querySelector("#new-part-name");
  const fileEl = dialog.querySelector("#new-part-file");
  const errorEl = dialog.querySelector("#new-part-error");
  const fileName = () => input.value.trim().replace(/\.solidcraft$/i, "") + ".solidcraft";
  const showFile = () => {
    fileEl.textContent = fileName();
    errorEl.hidden = true;
  };
  input.addEventListener("input", showFile);
  dialog.querySelector(".request-dialog-close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".btn-cancel").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });

  const submit = dialog.querySelector(".btn-submit");
  dialog.querySelector("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!input.value.trim()) {
      input.reportValidity();
      return;
    }
    submit.disabled = true;
    try {
      const res = await fetch("api/new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: fileName() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      dialog.close();
      dialog._onCreated(data);
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.hidden = false;
      input.focus();
    } finally {
      submit.disabled = false;
    }
  });
  dialog._open = (existing) => {
    input.value = suggestName(existing);
    showFile();
    dialog.showModal();
    input.select();
  };
  return dialog;
}

// existing: file names already in the folder (for a free default name); onCreated gets api/new's answer
export function openNewPartDialog(existing, onCreated) {
  const dialog = ensureDialog();
  dialog._onCreated = onCreated;
  dialog._open(existing);
}

// "Import STEP..." dialog (File menu): pick a STEP/IGES file from the project folder; the server makes a part
// file with its body (a fixed body without history, mechvane/step_import.py) and opens it.
function ensureImportDialog() {
  let dialog = document.getElementById("import-step-dialog");
  if (dialog) return dialog;
  dialog = document.createElement("dialog");
  dialog.id = "import-step-dialog";
  dialog.className = "request-dialog";
  dialog.innerHTML = `
    <form method="dialog" class="request-form">
      <div class="request-dialog-header">
        <h3>Import STEP</h3>
        <button type="button" class="request-dialog-close" aria-label="Close">&times;</button>
      </div>
      <div class="request-dialog-body">
        <div class="request-field-group">
          <label for="import-step-file">File in this folder</label>
          <div style="display: flex; gap: 6px;">
            <select id="import-step-file" style="flex: 1;"></select>
            <button type="button" id="import-step-browse" class="btn-cancel" style="white-space: nowrap;">Browse…</button>
          </div>
        </div>
        <div class="request-field-group" style="margin-top: 8px;">
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-weight: normal;">
            <input type="checkbox" id="import-step-split">
            Split into parts (assembly)
          </label>
        </div>
        <div class="request-dialog-note" id="import-step-note">Becomes a part with a fixed body (no history), saved next to it as
          <span id="import-step-target"></span>. Insert it into an assembly, measure it or check it.</div>
        <div id="import-step-error" class="new-part-error" role="alert" hidden></div>
      </div>
      <div class="request-dialog-footer">
        <button type="button" class="btn-cancel">Cancel</button>
        <button type="submit" class="btn-submit">Import</button>
      </div>
    </form>
  `;
  document.body.appendChild(dialog);
  const select = dialog.querySelector("#import-step-file");
  const browseBtn = dialog.querySelector("#import-step-browse");
  const target = dialog.querySelector("#import-step-target");
  const splitCheckbox = dialog.querySelector("#import-step-split");
  const noteEl = dialog.querySelector("#import-step-note");
  const errorEl = dialog.querySelector("#import-step-error");
  const submit = dialog.querySelector(".btn-submit");
  const showTarget = () => {
    const val = select.value ? select.value.split(/[/\\]/).pop() : "";
    const stem = val ? val.replace(/\.[^.]+$/, "") : "";
    target.textContent = stem ? stem + ".solidcraft" : "";
    if (splitCheckbox && splitCheckbox.checked) {
      noteEl.innerHTML = `Becomes an assembly (<span id="import-step-target">${stem ? stem + ".solidcraft" : ""}</span>) with each body as its own part file (<span style="font-family: monospace;">${stem}_&lt;body&gt;.solidcraft</span>), placed at their original positions.`;
    } else {
      noteEl.innerHTML = `Becomes a part with a fixed body (no history), saved next to it as <span id="import-step-target">${stem ? stem + ".solidcraft" : ""}</span>. Insert it into an assembly, measure it or check it.`;
    }
    errorEl.hidden = true;
  };
  select.addEventListener("change", showTarget);
  if (splitCheckbox) {
    splitCheckbox.addEventListener("change", showTarget);
  }
  if (browseBtn) {
    browseBtn.addEventListener("click", () => {
      dialog.close();
      openStepBrowseDialog(
        (selectedFilePath) => {
          let opt = Array.from(select.options).find((o) => o.value === selectedFilePath);
          if (!opt) {
            opt = document.createElement("option");
            opt.value = selectedFilePath;
            opt.textContent = `${selectedFilePath.split(/[/\\]/).pop()} (${selectedFilePath})`;
            select.prepend(opt);
          }
          select.value = selectedFilePath;
          submit.disabled = false;
          errorEl.hidden = true;
          showTarget();
          dialog.showModal();
        },
        () => {
          dialog.showModal();
        }
      );
    });
  }
  dialog.querySelector(".request-dialog-close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".btn-cancel").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  dialog.querySelector("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!select.value) return;
    submit.disabled = true;
    submit.textContent = "Importing…";
    try {
      const res = await fetch("api/import_step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file: select.value, split: splitCheckbox ? splitCheckbox.checked : false }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      dialog.close();
      dialog._onCreated(data);
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.hidden = false;
    } finally {
      submit.disabled = false;
      submit.textContent = "Import";
    }
  });
  dialog._open = (files) => {
    if (splitCheckbox) splitCheckbox.checked = false;
    select.replaceChildren(...files.map((f) => Object.assign(document.createElement("option"), { value: f, textContent: f })));
    submit.disabled = !select.value;
    if (!files.length) {
      errorEl.textContent = "No STEP or IGES files in this folder yet: click Browse… or copy one in.";
      errorEl.hidden = false;
    } else {
      errorEl.hidden = true;
    }
    showTarget();
    if (!files.length) errorEl.hidden = false;
    dialog.showModal();
  };
  return dialog;
}

// files: STEP/IGES files in the project folder (api/project step_files); onCreated gets api/import_step's answer
export function openImportStepDialog(files, onCreated) {
  const dialog = ensureImportDialog();
  dialog._onCreated = onCreated;
  dialog._open(files);
}
