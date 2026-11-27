// Mechvane website script — progressive enhancement for copy buttons and live v0.1 milestone progress.
(function () {
  "use strict";

  // 1. Copy buttons for install & MCP snippets
  document.querySelectorAll(".copy-btn[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const text = btn.getAttribute("data-copy") || "";
      if (!navigator.clipboard) return;
      try {
        await navigator.clipboard.writeText(text);
        const prev = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1500);
      } catch {
        // Clipboard access denied or unavailable
      }
    });
  });

  // 2. Live milestone progress from roadmap.json (with fallback without numbers)
  const LIVE_ROADMAP = "https://raw.githubusercontent.com/mechvane/mechvane/main/roadmap.json";
  const LOCAL_FALLBACK = "/roadmap/roadmap.json";

  async function fetchRoadmap() {
    for (const url of [LIVE_ROADMAP, LOCAL_FALLBACK]) {
      try {
        const res = await fetch(url, { cache: "no-store" });
        if (res.ok) return await res.json();
      } catch {
        // Try next source or keep static fallback without numbers
      }
    }
    return null;
  }

  fetchRoadmap().then((data) => {
    if (!data || !Array.isArray(data.sections) || !data.milestone) return;
    const msName = data.milestone.name || "v0.1";
    const msItems = data.sections
      .flatMap((s) => s.items || [])
      .filter((i) => i.milestone === msName);
    if (!msItems.length) return;

    const msDone = msItems.filter((i) => i.status === "done" || i.status === "next").length;
    const msProgress = msItems.filter((i) => i.status === "progress").length;
    const pct = Math.round((100 * msDone) / msItems.length);

    const titleEl = document.getElementById("ms-title");
    const goalEl = document.getElementById("ms-goal");
    const barEl = document.getElementById("ms-bar");
    const fillEl = document.getElementById("ms-fill");
    const detailEl = document.getElementById("ms-detail");

    if (titleEl) {
      titleEl.textContent = `Next milestone: ${msName} · ${pct} % done`;
    }
    if (goalEl && data.milestone.goal) {
      goalEl.textContent = data.milestone.goal;
    }
    if (barEl && fillEl) {
      barEl.hidden = false;
      fillEl.style.width = `${pct}%`;
    }
    if (detailEl) {
      detailEl.textContent = `${msDone} of ${msItems.length} parts of ${msName} are done, ${msProgress} in progress.`;
    }
  });
})();
