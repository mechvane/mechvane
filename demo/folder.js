// "Open folder…" dialog of the workspace (File menu) and "Browse…" file picker for STEP import.
// Lists roots (drives on Windows, / and Home on POSIX), subfolders with .solidcraft/STEP file counts,
// and recently used folders. Switches the project folder via api/project/open.

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str == null ? "" : String(str);
  return d.innerHTML;
}

function renderCounts(sc, step) {
  const parts = [];
  parts.push(`${sc || 0} .solidcraft`);
  parts.push(`${step || 0} STEP`);
  return parts.join(" · ");
}

let dialogEl = null;

function ensureFolderDialog() {
  if (dialogEl) return dialogEl;
  dialogEl = document.getElementById("folder-dialog");
  if (dialogEl) return dialogEl;

  dialogEl = document.createElement("dialog");
  dialogEl.id = "folder-dialog";
  dialogEl.className = "request-dialog folder-dialog";
  dialogEl.innerHTML = `
    <form method="dialog" class="request-form">
      <div class="request-dialog-header">
        <h3 id="folder-dialog-title">Open folder</h3>
        <button type="button" class="request-dialog-close" aria-label="Close">&times;</button>
      </div>
      <div class="request-dialog-body folder-dialog-body">
        <div id="folder-recent-container" class="folder-recent-container" hidden>
          <div class="folder-section-label">Recent folders</div>
          <div id="folder-recent-list" class="folder-recent-list"></div>
        </div>

        <div class="folder-nav-bar">
          <select id="folder-roots-select" class="folder-roots-select" title="Jump to root"></select>
          <button type="button" id="folder-btn-up" class="folder-btn-nav" title="Parent folder">↑</button>
          <input type="text" id="folder-path-input" class="folder-path-input" autocomplete="off" spellcheck="false" placeholder="Folder path…">
          <button type="button" id="folder-btn-go" class="folder-btn-nav">Go</button>
        </div>

        <div class="folder-section-label" id="folder-list-label">Folders</div>
        <div id="folder-items-list" class="folder-items-list" tabindex="0" role="listbox"></div>

        <div id="folder-files-container" class="folder-files-container" hidden>
          <div class="folder-section-label">STEP files in this folder</div>
          <div id="folder-files-list" class="folder-files-list" tabindex="0" role="listbox"></div>
        </div>

        <div id="folder-dialog-error" class="new-part-error" role="alert" hidden></div>
      </div>
      <div class="request-dialog-footer">
        <button type="button" class="btn-cancel">Cancel</button>
        <button type="submit" class="btn-submit" id="folder-btn-submit">Open</button>
      </div>
    </form>
  `;
  document.body.appendChild(dialogEl);

  const titleEl = dialogEl.querySelector("#folder-dialog-title");
  const recentContainer = dialogEl.querySelector("#folder-recent-container");
  const recentList = dialogEl.querySelector("#folder-recent-list");
  const rootsSelect = dialogEl.querySelector("#folder-roots-select");
  const upBtn = dialogEl.querySelector("#folder-btn-up");
  const pathInput = dialogEl.querySelector("#folder-path-input");
  const goBtn = dialogEl.querySelector("#folder-btn-go");
  const itemsList = dialogEl.querySelector("#folder-items-list");
  const filesContainer = dialogEl.querySelector("#folder-files-container");
  const filesList = dialogEl.querySelector("#folder-files-list");
  const errorEl = dialogEl.querySelector("#folder-dialog-error");
  const submitBtn = dialogEl.querySelector("#folder-btn-submit");
  const closeBtn = dialogEl.querySelector(".request-dialog-close");
  const cancelBtn = dialogEl.querySelector(".btn-cancel");

  let currentPath = "";
  let currentData = null;
  let selectedStepPath = "";
  let confirmed = false;

  async function loadFolder(targetPath) {
    errorEl.hidden = true;
    submitBtn.disabled = true;
    itemsList.innerHTML = '<div class="folder-empty-note">Loading…</div>';
    if (dialogEl._mode === "step") {
      filesList.innerHTML = '<div class="folder-empty-note">Loading…</div>';
    }

    try {
      const url = targetPath ? `api/folders?path=${encodeURIComponent(targetPath)}` : "api/folders";
      const res = await fetch(url);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${res.status}`);
      }
      const data = await res.json();
      currentData = data;
      currentPath = data.current;
      pathInput.value = data.current;
      upBtn.disabled = !data.parent;

      // Populate roots
      const roots = data.roots || [];
      rootsSelect.innerHTML = roots.map((r) => `<option value="${esc(r.path)}">${esc(r.name)}</option>`).join("");
      const matchingRoot = roots.find((r) => r.path === currentPath);
      if (matchingRoot) rootsSelect.value = matchingRoot.path;

      // Populate recent folders
      const recent = data.recent || [];
      if (recent.length > 0) {
        recentContainer.hidden = false;
        recentList.innerHTML = "";
        for (const rf of recent) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "folder-recent-chip";
          btn.title = rf.path;
          btn.innerHTML = `
            <span class="recent-icon">📁</span>
            <span class="recent-name">${esc(rf.name)}</span>
            <span class="recent-counts">${esc(renderCounts(rf.solidcraft_count, rf.step_count))}</span>
          `;
          btn.addEventListener("click", () => loadFolder(rf.path));
          recentList.appendChild(btn);
        }
      } else {
        recentContainer.hidden = true;
      }

      // Populate subfolders
      const folders = data.folders || [];
      itemsList.innerHTML = "";
      if (folders.length > 0) {
        for (const f of folders) {
          const row = document.createElement("div");
          row.className = "folder-row";
          row.setAttribute("role", "option");
          row.dataset.path = f.path;
          row.innerHTML = `
            <span class="folder-icon">📁</span>
            <span class="folder-name">${esc(f.name)}</span>
            <span class="folder-counts">${esc(renderCounts(f.solidcraft_count, f.step_count))}</span>
          `;
          row.addEventListener("click", () => loadFolder(f.path));
          itemsList.appendChild(row);
        }
      } else {
        itemsList.innerHTML = '<div class="folder-empty-note">No subfolders</div>';
      }

      // Populate STEP files if in step mode
      if (dialogEl._mode === "step") {
        filesContainer.hidden = false;
        const stepFiles = data.step_files || [];
        filesList.innerHTML = "";
        selectedStepPath = "";
        submitBtn.disabled = true;

        if (stepFiles.length > 0) {
          for (const sf of stepFiles) {
            const frow = document.createElement("div");
            frow.className = "folder-file-row";
            frow.setAttribute("role", "option");
            frow.dataset.path = sf.path;
            frow.innerHTML = `
              <span class="file-icon">📄</span>
              <span class="file-name">${esc(sf.name)}</span>
            `;
            frow.addEventListener("click", () => {
              for (const r of filesList.querySelectorAll(".folder-file-row")) {
                r.classList.remove("selected");
              }
              frow.classList.add("selected");
              selectedStepPath = sf.path;
              submitBtn.disabled = false;
              errorEl.hidden = true;
            });
            frow.addEventListener("dblclick", () => {
              selectedStepPath = sf.path;
              confirmed = true;
              dialogEl.close();
              if (dialogEl._onSelected) dialogEl._onSelected(selectedStepPath);
            });
            filesList.appendChild(frow);
          }
        } else {
          filesList.innerHTML = '<div class="folder-empty-note">No STEP or IGES files in this folder</div>';
        }
      } else {
        filesContainer.hidden = true;
        submitBtn.disabled = false;
      }
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.hidden = false;
      itemsList.innerHTML = `<div class="folder-empty-note">Failed to read folder: ${esc(err.message)}</div>`;
      if (dialogEl._mode === "step") {
        filesList.innerHTML = "";
      }
    } finally {
      if (dialogEl._mode === "folder") {
        submitBtn.disabled = false;
      }
    }
  }

  rootsSelect.addEventListener("change", () => {
    if (rootsSelect.value) loadFolder(rootsSelect.value);
  });

  upBtn.addEventListener("click", () => {
    if (currentData && currentData.parent) {
      loadFolder(currentData.parent);
    }
  });

  pathInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const val = pathInput.value.trim();
      if (val) loadFolder(val);
    }
  });

  goBtn.addEventListener("click", () => {
    const val = pathInput.value.trim();
    if (val) loadFolder(val);
  });

  closeBtn.addEventListener("click", () => dialogEl.close());
  cancelBtn.addEventListener("click", () => dialogEl.close());
  dialogEl.addEventListener("click", (e) => { if (e.target === dialogEl) dialogEl.close(); });

  dialogEl.addEventListener("close", () => {
    if (!confirmed && dialogEl._onCancel) {
      dialogEl._onCancel();
    }
  });

  dialogEl.querySelector("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (dialogEl._mode === "folder") {
      if (!currentPath) return;
      submitBtn.disabled = true;
      submitBtn.textContent = "Opening…";
      try {
        const res = await fetch("api/project/open", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ folder: currentPath }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        confirmed = true;
        dialogEl.close();
        if (dialogEl._onOpened) dialogEl._onOpened(data);
      } catch (err) {
        errorEl.textContent = err.message;
        errorEl.hidden = false;
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Open";
      }
    } else if (dialogEl._mode === "step") {
      if (!selectedStepPath) {
        errorEl.textContent = "Please select a STEP file first";
        errorEl.hidden = false;
        return;
      }
      confirmed = true;
      dialogEl.close();
      if (dialogEl._onSelected) dialogEl._onSelected(selectedStepPath);
    }
  });

  dialogEl._open = (mode, initialPath) => {
    confirmed = false;
    dialogEl._mode = mode;
    errorEl.hidden = true;
    if (mode === "folder") {
      titleEl.textContent = "Open folder";
      submitBtn.textContent = "Open";
      filesContainer.hidden = true;
    } else {
      titleEl.textContent = "Select STEP file";
      submitBtn.textContent = "Select";
      filesContainer.hidden = false;
    }
    dialogEl.showModal();
    loadFolder(initialPath || "");
  };

  return dialogEl;
}

// Open folder dialog (File -> Open folder...): calls onOpened(projectData) on success
export function openFolderDialog(onOpened) {
  const dialog = ensureFolderDialog();
  dialog._onOpened = onOpened;
  dialog._onSelected = null;
  dialog._onCancel = null;
  dialog._open("folder");
}

// File picker for File -> Import STEP... -> Browse...: calls onSelected(filePath)
export function openStepBrowseDialog(onSelected, onCancel) {
  const dialog = ensureFolderDialog();
  dialog._onOpened = null;
  dialog._onSelected = onSelected;
  dialog._onCancel = onCancel;
  dialog._open("step");
}
