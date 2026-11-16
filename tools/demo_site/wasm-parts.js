// Loads a SolidCraft wasm that GitHub Pages can only hold in pieces (100 MB per file, #119).
// tools/build_demo_site.py splits <name>_bg.wasm into <name>_bg.wasm.part0, .part1, ... and writes
// <name>_bg.wasm.parts.json ({parts, size, sha256}); this script answers fetch() for the whole file
// with the pieces joined, checked against the SHA-256 of the original release file.
(() => {
  const real = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const href = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(href, location.href);
    if (!url.pathname.endsWith("_bg.wasm")) return real(input, init);
    const manifest = await real(url.href + ".parts.json", { cache: "no-cache" });
    if (!manifest.ok) return real(input, init);  // a whole file after all
    const { parts, size, sha256 } = await manifest.json();
    const buffers = await Promise.all(parts.map(async (p) => {
      const r = await real(new URL(p, url).href);
      if (!r.ok) throw new Error(`wasm piece ${p}: HTTP ${r.status}`);
      return r.arrayBuffer();
    }));
    const blob = new Blob(buffers, { type: "application/wasm" });
    if (blob.size !== size) throw new Error(`wasm pieces: ${blob.size} bytes instead of ${size}`);
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", await blob.arrayBuffer()));
    const hex = Array.from(digest, (b) => b.toString(16).padStart(2, "0")).join("");
    if (hex !== sha256) throw new Error("wasm pieces: SHA-256 does not match the release file");
    return new Response(blob, { status: 200, headers: { "Content-Type": "application/wasm" } });
  };
})();
