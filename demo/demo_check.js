// demo_check.js - Live in-browser design rule checking via Pyodide for Mechvane demo

export const PYODIDE_VERSION = "v0.26.4";
export const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

let pyodidePromise = null;

export function initDemoCheck(opts = {}) {
  if (pyodidePromise) return pyodidePromise;

  pyodidePromise = (async () => {
    let pyodide;
    const zipUrl = opts.zipUrl || "mechvane.zip";

    if (opts.pyodide) {
      pyodide = opts.pyodide;
    } else if (typeof window !== "undefined") {
      if (!window.loadPyodide) {
        await new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.src = `${PYODIDE_CDN}pyodide.js`;
          script.onload = resolve;
          script.onerror = () => reject(new Error("Failed to load Pyodide from CDN"));
          document.head.appendChild(script);
        });
      }
      pyodide = await window.loadPyodide({ indexURL: PYODIDE_CDN });
    } else {
      throw new Error("Pyodide instance or browser environment required");
    }

    if (opts.zipBuffer) {
      const b = opts.zipBuffer;
      const u8 = (typeof Buffer !== "undefined" && Buffer.isBuffer(b))
        ? new Uint8Array(b.buffer, b.byteOffset, b.byteLength)
        : (b instanceof Uint8Array ? b : new Uint8Array(b));
      await pyodide.unpackArchive(u8, "zip");
    } else if (typeof fetch !== "undefined") {
      const res = await fetch(zipUrl);
      if (!res.ok) throw new Error(`Failed to load ${zipUrl}: HTTP ${res.status}`);
      const buf = await res.arrayBuffer();
      await pyodide.unpackArchive(new Uint8Array(buf), "zip");
    }

    pyodide.runPython(`
from mechvane.browser_check import check_browser_json
`);
    return pyodide;
  })();

  return pyodidePromise;
}

export async function fetchInspectionData(app) {
  if (!app) throw new Error("SolidCraft app instance is required");

  const exec = async (cmd, params = {}) => {
    if (app.execute) {
      try {
        return await app.execute(cmd, params);
      } catch (e) {
        if (app.request) return await app.request(cmd, params);
        throw e;
      }
    }
    if (app.request) return await app.request(cmd, params);
    throw new Error(`Cannot execute command ${cmd}: app has neither execute nor request`);
  };

  const docInfo = await exec("document.inspect", { measure: true });
  const metaRes = await exec("document.metadata", {}).catch(() => ({}));
  const threadsRes = await exec("model.threads", {}).catch(() => ({ threads: [] }));
  const measureRes = await exec("inspect.measure", {}).catch(() => ({}));

  const timelineInspect = {};
  const timeline = docInfo.timeline || [];
  for (const f of timeline) {
    if (["HoleFeature", "CylinderFeature", "ExtrudeFeature"].includes(f.type) && !f.definition) {
      try {
        timelineInspect[f.id] = await exec("timeline.inspect", { feature: f.id });
      } catch (e) {
        timelineInspect[f.id] = {};
      }
    }
  }

  const bodyFaces = {};
  const bodyEdges = {};
  const bodies = docInfo.bodies || [];
  for (const b of bodies) {
    try {
      bodyFaces[b.name] = await exec("model.faces", { body: b.name });
    } catch (e) {
      bodyFaces[b.name] = { faces: [] };
    }
    try {
      bodyEdges[b.name] = await exec("model.edges", { body: b.name });
    } catch (e) {
      bodyEdges[b.name] = { edges: [] };
    }
  }

  return {
    doc_info: docInfo,
    metadata: (metaRes && metaRes.metadata) || {},
    threads: threadsRes,
    measure: measureRes,
    timeline_inspect: timelineInspect,
    body_faces: bodyFaces,
    body_edges: bodyEdges,
  };
}

export async function checkInBrowser(app, docName, opts = {}) {
  const pyodide = await initDemoCheck(opts);
  const payload = opts.payload || (await fetchInspectionData(app));
  const checkFn = pyodide.globals.get("check_browser_json");
  const resultJson = checkFn(
    JSON.stringify(payload),
    docName || "doc.solidcraft",
    opts.profile || null,
    opts.material || null
  );
  return JSON.parse(resultJson);
}
