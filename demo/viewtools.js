// Measure and section tools for the 3D view of the Check page. Both work on the triangle mesh the page
// already has (face_ids per triangle), so they need no server and also run in the live demo.
import * as THREE from "three";

const SECTION_COLOR = 0xd26a0c;
const MARK_COLOR = 0xffad45;
const EDGE_PICK_PX = 6;

function fmt(v) {
  return (Math.abs(v) < 5e-4 ? 0 : v).toFixed(2);
}

// An axis direction pointing the positive way, e.g. (0, 0, 1)
function vec(v) {
  const sign = [v.x, v.y, v.z].find((c) => Math.abs(c) > 1e-6) < 0 ? -1 : 1;
  return `(${[v.x, v.y, v.z].map((c) => fmt(c * sign).replace(/\.?0+$/, "")).join(", ")})`;
}

// Area of one B-rep face of one body, its plane normal if flat, or its axis and radius if it is a
// cylinder (all facet normals at right angles to one axis; each facet normal passes through the axis)
export function faceInfo(body, fid) {
  const pos = body.positions;
  const idx = body.indices;
  const fids = body.face_ids || [];
  const tris = [];
  const verts = [];
  let area = 0;
  for (let t = 0; t < idx.length / 3; t++) {
    if ((fids[t] ?? 0) !== fid) continue;
    const [a, b, c] = [0, 1, 2].map((k) => new THREE.Vector3().fromArray(pos, idx[t * 3 + k] * 3));
    const n = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a));
    const twice = n.length();
    if (twice < 1e-12) continue;
    area += twice / 2;
    tris.push({ n: n.divideScalar(twice), c: a.clone().add(b).add(c).divideScalar(3) });
    verts.push(a, b, c);
  }
  if (!tris.length) return { area };
  if (tris.every((t) => t.n.dot(tris[0].n) > 0.9999)) return { area, normal: tris[0].n };

  // two facet normals as near a right angle as there are span the plane at right angles to a
  // cylinder's axis (not the most opposite: on a half cylinder those are parallel)
  let i0 = 0, j0 = 0, low = 2;
  for (let j = 1; j < tris.length; j++) {
    const d = Math.abs(tris[0].n.dot(tris[j].n));
    if (d < low) { low = d; j0 = j; }
  }
  const axis = new THREE.Vector3().crossVectors(tris[i0].n, tris[j0].n);
  if (axis.length() < 1e-6) return { area };
  axis.normalize();
  if (!tris.every((t) => Math.abs(t.n.dot(axis)) < 0.02)) return { area };
  // least-squares circle through the corners seen along the axis: x² + y² + Dx + Ey + F = 0
  const u = new THREE.Vector3().crossVectors(axis, Math.abs(axis.x) < 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0)).normalize();
  const v = new THREE.Vector3().crossVectors(axis, u);
  const o = verts[0];
  const M = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], R = [0, 0, 0];
  const pts = verts.map((p) => { const w = new THREE.Vector3().subVectors(p, o); return [w.dot(u), w.dot(v)]; });
  for (const [x, y] of pts) {
    const row = [x, y, 1], rhs = -(x * x + y * y);
    for (let i = 0; i < 3; i++) {
      R[i] += row[i] * rhs;
      for (let j = 0; j < 3; j++) M[i][j] += row[i] * row[j];
    }
  }
  const sol = new THREE.Matrix3().set(...M[0], ...M[1], ...M[2]);
  if (Math.abs(sol.determinant()) < 1e-12) return { area };
  const [D, E, F] = new THREE.Vector3(...R).applyMatrix3(sol.invert()).toArray();
  const cx = -D / 2, cy = -E / 2;
  const radius = Math.sqrt(Math.max(cx * cx + cy * cy - F, 0));
  const center = o.clone().addScaledVector(u, cx).addScaledVector(v, cy);
  if (pts.some(([x, y]) => Math.abs(Math.hypot(x - cx, y - cy) - radius) > Math.max(0.01 * radius, 1e-3))) return { area };
  return { area, axis, center, radius };
}

// B-rep edges of one body as mesh segments between two different faces: [{a, b, faces: [fa, fb]}].
// Vertices are matched by position, since a mesh may repeat them along a seam.
export function bodyEdges(body) {
  const pos = body.positions;
  const idx = body.indices;
  const fids = body.face_ids || [];
  const key = (v) => [0, 1, 2].map((k) => Math.round(pos[v * 3 + k] * 1e4)).join(",");
  const seen = new Map();
  for (let t = 0; t < idx.length / 3; t++) {
    const fid = fids[t] ?? 0;
    for (let k = 0; k < 3; k++) {
      const va = idx[t * 3 + k], vb = idx[t * 3 + (k + 1) % 3];
      const ka = key(va), kb = key(vb);
      if (ka === kb) continue;
      const s = ka < kb ? `${ka}|${kb}` : `${kb}|${ka}`;
      const e = seen.get(s);
      if (!e) seen.set(s, { a: va, b: vb, ka, kb, faces: [fid] });
      else if (!e.faces.includes(fid)) e.faces.push(fid);
    }
  }
  return [...seen.values()].filter((e) => e.faces.length === 2).map((e) => ({
    a: new THREE.Vector3().fromArray(pos, e.a * 3), b: new THREE.Vector3().fromArray(pos, e.b * 3),
    ka: e.ka, kb: e.kb, faces: e.faces.sort((x, y) => x - y),
  }));
}

// The edge through segment `seg` (from bodyEdges): the chain of segments between the same two faces.
// A straight edge gives its length and direction, a circle or arc its centre, axis and radius.
export function edgeInfo(edges, seg) {
  const same = edges.filter((e) => e.faces[0] === seg.faces[0] && e.faces[1] === seg.faces[1]);
  const at = new Map();
  for (const e of same) for (const k of [e.ka, e.kb]) at.set(k, [...(at.get(k) || []), e]);
  // grow the chain from the picked segment in both directions
  const used = new Set([seg]);
  const pts = [seg.a, seg.b];
  const keys = [seg.ka, seg.kb];
  for (const end of [1, 0]) {
    for (;;) {
      const k = end ? keys[keys.length - 1] : keys[0];
      const next = (at.get(k) || []).find((e) => !used.has(e));
      if (!next) break;
      used.add(next);
      const [nk, np] = next.ka === k ? [next.kb, next.b] : [next.ka, next.a];
      if (end) { keys.push(nk); pts.push(np); } else { keys.unshift(nk); pts.unshift(np); }
    }
  }
  const closed = keys.length > 3 && keys[0] === keys[keys.length - 1];
  let length = 0;
  for (let i = 1; i < pts.length; i++) length += pts[i].distanceTo(pts[i - 1]);
  const info = { points: pts, length, closed, faces: seg.faces };
  const first = pts[0], last = pts[pts.length - 1];
  const chord = new THREE.Vector3().subVectors(last, first);
  const tol = Math.max(1e-3, 1e-4 * length);
  if (!closed && chord.length() > tol) {
    const dir = chord.clone().normalize();
    const off = (p) => new THREE.Vector3().subVectors(p, first).cross(dir).length();
    if (pts.every((p) => off(p) < tol)) return { ...info, kind: "line", dir, start: first, end: last };
  }
  // circle through three points spread along the chain, then every point must lie on it
  const n = pts.length - (closed ? 1 : 0);
  if (n < 3) return { ...info, kind: "curve" };
  const [p, q, r] = closed ? [pts[0], pts[Math.floor(n / 3)], pts[Math.floor((2 * n) / 3)]]
    : [first, pts[Math.floor(n / 2)], last];
  const u = new THREE.Vector3().subVectors(q, p), v = new THREE.Vector3().subVectors(r, p);
  const axis = new THREE.Vector3().crossVectors(u, v);
  const a2 = axis.lengthSq();
  if (a2 < 1e-12) return { ...info, kind: "curve" };
  // circumcentre: p + ((|u|² v − |v|² u) × (u × v)) / (2 |u × v|²)
  const center = p.clone().add(new THREE.Vector3().subVectors(v.clone().multiplyScalar(u.lengthSq()),
    u.clone().multiplyScalar(v.lengthSq())).cross(axis).divideScalar(2 * a2));
  axis.normalize();
  const radius = center.distanceTo(p);
  const rtol = Math.max(0.01 * radius, 1e-3);
  if (!pts.every((s) => Math.abs(s.distanceTo(center) - radius) < rtol
      && Math.abs(new THREE.Vector3().subVectors(s, center).dot(axis)) < rtol)) return { ...info, kind: "curve" };
  // SolidCraft splits a hole into two half faces: carry an arc on over segments that share one of its
  // faces and stay on the circle, so a hole edge reads as a full circle
  if (!closed) {
    const onCircle = (s) => Math.abs(s.distanceTo(center) - radius) < rtol
      && Math.abs(new THREE.Vector3().subVectors(s, center).dot(axis)) < rtol;
    const more = edges.filter((e) => !used.has(e) && (e.faces.includes(seg.faces[0]) || e.faces.includes(seg.faces[1]))
      && onCircle(e.a) && onCircle(e.b));
    const near = new Map();
    for (const e of more) for (const k of [e.ka, e.kb]) near.set(k, [...(near.get(k) || []), e]);
    for (const end of [1, 0]) {
      for (;;) {
        const k = end ? keys[keys.length - 1] : keys[0];
        if (keys.length > 3 && keys[0] === keys[keys.length - 1]) break;
        const next = (near.get(k) || []).find((e) => !used.has(e));
        if (!next) break;
        used.add(next);
        const [nk, np] = next.ka === k ? [next.kb, next.b] : [next.ka, next.a];
        if (end) { keys.push(nk); pts.push(np); } else { keys.unshift(nk); pts.unshift(np); }
      }
    }
    info.closed = keys.length > 3 && keys[0] === keys[keys.length - 1];
  }
  // the mesh cuts corners: take the arc length and angle from the true circle, not the chords
  let angle = 0;
  for (let i = 1; i < pts.length; i++) {
    angle += new THREE.Vector3().subVectors(pts[i - 1], center).angleTo(new THREE.Vector3().subVectors(pts[i], center));
  }
  return { ...info, kind: info.closed ? "circle" : "arc", center, axis, radius, length: angle * radius,
           angle: THREE.MathUtils.radToDeg(angle) };
}

export function initViewTools({ scene, camera, renderer, modelGroup, renderScene, containerEl, selectable = false }) {
  const measureGroup = new THREE.Group();
  scene.add(measureGroup);

  let meshData = null;
  let mode = null; // "measure" | "section" | null
  let picks = [];
  const plane = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);
  let sectionAxis = "z";
  let sectionPos = 0.5;
  let modelBox = new THREE.Box3();
  let markerSize = 1;

  // Toolbar and readout over the view
  const bar = document.createElement("div");
  bar.className = "view-tools";
  bar.innerHTML = `
    <button type="button" data-tool="measure" title="Click two points, faces or edges">Measure</button>
    <button type="button" data-tool="section" title="Cut the model with a plane">Section</button>
    <button type="button" data-tool="select" title="Click faces to point the agent at them" hidden>Select</button>
    <span class="section-controls" hidden>
      <select aria-label="Section plane"><option value="x">YZ (X)</option><option value="y">XZ (Y)</option><option value="z" selected>XY (Z)</option></select>
      <input type="range" min="0" max="1000" value="500" aria-label="Section position">
      <button type="button" data-flip title="Show the other side">⇅</button>
    </span>`;
  const readout = document.createElement("div");
  readout.className = "measure-readout";
  readout.hidden = true;
  containerEl.append(bar, readout);
  const sectionControls = bar.querySelector(".section-controls");
  const axisSelect = sectionControls.querySelector("select");
  const slider = sectionControls.querySelector("input");
  let flipped = false;

  // Faces picked for the agent (chat): {type, body, index, point, name} as the SolidCraft app reports them
  const selectGroup = new THREE.Group();
  scene.add(selectGroup);
  let selection = [];
  if (selectable) bar.querySelector('[data-tool="select"]').hidden = false;

  function showSelection() {
    while (selectGroup.children.length) {
      const c = selectGroup.children.pop();
      c.geometry?.dispose();
      c.material?.dispose();
    }
    for (const it of selection) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(markerSize * 1.2, 16, 12),
        new THREE.MeshBasicMaterial({ color: 0x58a6ff, depthTest: false }));
      m.position.set(...it.point);
      m.renderOrder = 11;
      selectGroup.add(m);
    }
    if (mode === "select") {
      readout.innerHTML = selection.length
        ? `<strong>${selection.length} selected</strong><br>${selection.map((s) => s.name || `face ${s.index}`).join("<br>")}`
          + "<br>Now tell the agent what to do"
        : "Click faces to select them for the agent";
      readout.hidden = false;
    }
    renderScene();
  }

  function setMode(next) {
    mode = mode === next ? null : next;
    bar.querySelectorAll("[data-tool]").forEach((b) => b.classList.toggle("active", b.dataset.tool === mode));
    if (mode !== "measure") clearMeasure();
    if (mode === "select") showSelection();
    sectionControls.hidden = mode !== "section";
    applySection();
  }
  bar.querySelectorAll("[data-tool]").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.tool)));
  axisSelect.addEventListener("change", () => { sectionAxis = axisSelect.value; applySection(); });
  slider.addEventListener("input", () => { sectionPos = slider.value / 1000; applySection(); });
  sectionControls.querySelector("[data-flip]").addEventListener("click", () => { flipped = !flipped; applySection(); });

  function applySection() {
    const on = mode === "section" && !modelBox.isEmpty();
    if (on) {
      const k = { x: 0, y: 1, z: 2 }[sectionAxis];
      const lo = modelBox.min.getComponent(k), hi = modelBox.max.getComponent(k);
      const at = lo + (hi - lo) * sectionPos;
      // keep the half away from the camera, so the cut faces the viewer; ⇅ shows the other half
      const keepLow = (camera.position.getComponent(k) > at) !== flipped;
      plane.set(new THREE.Vector3().setComponent(k, keepLow ? -1 : 1), keepLow ? at : -at);
      readout.textContent = `Section ${sectionAxis.toUpperCase()} = ${fmt(at)} mm`;
    }
    readout.hidden = !(on || picks.length);
    // on the renderer, so finding highlights added later are cut as well
    renderer.clippingPlanes = on ? [plane] : [];
    modelGroup.children.forEach((o) => { if (o.userData.sectionCap) o.visible = on; });
    renderScene();
  }

  // Back faces drawn in one flat colour look like the cut surface (a cap) where the plane opens a body
  function addCaps() {
    const caps = [];
    modelGroup.children.forEach((o) => {
      if (!o.isMesh) return;
      const cap = new THREE.Mesh(o.geometry, new THREE.MeshBasicMaterial({ color: SECTION_COLOR, side: THREE.BackSide }));
      cap.userData.sectionCap = true;
      cap.visible = false;
      caps.push(cap);
    });
    caps.forEach((c) => modelGroup.add(c));
  }

  function clearMeasure() {
    picks = [];
    while (measureGroup.children.length) {
      const c = measureGroup.children.pop();
      c.geometry?.dispose();
      c.material?.dispose();
    }
    if (mode !== "section") readout.hidden = true;
    renderScene();
  }

  function marker(p) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(markerSize, 16, 12),
      new THREE.MeshBasicMaterial({ color: MARK_COLOR, depthTest: false }));
    m.position.copy(p);
    m.renderOrder = 10;
    measureGroup.add(m);
  }

  function edgeLines(e) {
    if (e.kind === "line") return [`Edge length ${fmt(e.length)} mm`, `Direction ${vec(e.dir)}`];
    if (e.kind === "circle") return [`Circle Ø ${fmt(2 * e.radius)} mm`, `Centre ${fmt(e.center.x)}, ${fmt(e.center.y)}, ${fmt(e.center.z)}`,
      `Axis ${vec(e.axis)}, circumference ${fmt(e.length)} mm`];
    if (e.kind === "arc") return [`Arc R ${fmt(e.radius)} mm, ${fmt(e.angle)}°`, `Centre ${fmt(e.center.x)}, ${fmt(e.center.y)}, ${fmt(e.center.z)}`,
      `Arc length ${fmt(e.length)} mm`];
    return [`Edge length ${fmt(e.length)} mm`];
  }

  // Two picks where at least one is an edge: lines give angle or gap, circles their centres
  function edgePairLines(a, b) {
    const lines = [];
    const at = (p) => (p.edge?.center ?? p.point);
    const d = new THREE.Vector3().subVectors(at(b), at(a));
    const centres = a.edge?.center || b.edge?.center;
    lines.push(`Distance ${fmt(d.length())} mm${centres ? " (circle centres)" : ""}`);
    lines.push(`ΔX ${fmt(d.x)}  ΔY ${fmt(d.y)}  ΔZ ${fmt(d.z)}`);
    const da = a.edge?.kind === "line" ? a.edge.dir : null, db = b.edge?.kind === "line" ? b.edge.dir : null;
    if (da && db) {
      const cos = Math.min(1, Math.abs(da.dot(db)));
      if (cos > 0.9999) {
        const w = new THREE.Vector3().subVectors(b.edge.start, a.edge.start);
        lines.push(`Parallel edges, ${fmt(w.addScaledVector(da, -w.dot(da)).length())} mm apart`);
      } else lines.push(`Angle between edges ${fmt(THREE.MathUtils.radToDeg(Math.acos(cos)))}°`);
    }
    const [line, face] = da && b.normal && !b.edge ? [da, b] : db && a.normal && !a.edge ? [db, a] : [];
    if (line) {
      const s = Math.abs(line.dot(face.normal));
      if (s < 1e-4) {
        const edge = face === b ? a.edge : b.edge;
        lines.push(`Edge parallel to face, ${fmt(Math.abs(new THREE.Vector3().subVectors(edge.start, face.point).dot(face.normal)))} mm apart`);
      } else lines.push(`Angle edge to face ${fmt(THREE.MathUtils.radToDeg(Math.asin(Math.min(1, s))))}°`);
    }
    if (a.edge?.axis && b.edge?.axis && Math.abs(a.edge.axis.dot(b.edge.axis)) > 0.9999) {
      const w = new THREE.Vector3().subVectors(b.edge.center, a.edge.center);
      const apart = w.addScaledVector(a.edge.axis, -w.dot(a.edge.axis)).length();
      if (apart < 1e-3) lines.push("Coaxial");
      else lines.push(`Axes ${fmt(apart)} mm apart`);
    }
    return lines;
  }

  function describe() {
    const [a, b] = picks;
    const lines = [];
    if (!b && a.edge) {
      lines.push(...edgeLines(a.edge), "Click a second edge, face or point");
    } else if (b && (a.edge || b.edge)) {
      lines.push(...edgePairLines(a, b));
    } else if (!b) {
      lines.push(`Point ${fmt(a.point.x)}, ${fmt(a.point.y)}, ${fmt(a.point.z)}`);
      if (a.radius) lines.push(`Cylinder Ø ${fmt(2 * a.radius)} mm, axis ${vec(a.axis)}`);
      lines.push(a.normal ? `Planar face, area ${fmt(a.area)} mm²` : `${a.radius ? "Area" : "Curved face, area"} ${fmt(a.area)} mm²`);
      lines.push("Click a second point");
    } else {
      const d = new THREE.Vector3().subVectors(b.point, a.point);
      lines.push(`Distance ${fmt(d.length())} mm`);
      lines.push(`ΔX ${fmt(d.x)}  ΔY ${fmt(d.y)}  ΔZ ${fmt(d.z)}`);
      if (a.radius && b.radius && Math.abs(a.axis.dot(b.axis)) > 0.9999) {
        const w = new THREE.Vector3().subVectors(b.center, a.center);
        const apart = w.addScaledVector(a.axis, -w.dot(a.axis)).length();
        const diameters = `Ø ${fmt(2 * a.radius)} / ${fmt(2 * b.radius)}`;
        lines.push(apart < 1e-3 ? `Coaxial (${diameters})` : `Axes ${fmt(apart)} mm apart (${diameters})`);
      }
      if (a.normal && b.normal) {
        const cos = Math.min(1, Math.abs(a.normal.dot(b.normal)));
        const gap = Math.abs(d.dot(a.normal));
        if (cos > 0.9999) lines.push(gap < 1e-3 ? "Both on one plane" : `Parallel faces, ${fmt(gap)} mm apart`);
        else lines.push(`Angle between faces ${fmt(THREE.MathUtils.radToDeg(Math.acos(a.normal.dot(b.normal))))}°`);
      }
    }
    readout.innerHTML = lines.map((l, i) => (i === 0 ? `<strong>${l}</strong>` : l)).join("<br>");
    readout.hidden = false;
  }

  // An edge of the clicked face within a few pixels of the click, as edgeInfo, or null
  let edgeCache = new Map();
  function nearEdge(bi, body, fid, x, y, rect) {
    if (!edgeCache.has(bi)) edgeCache.set(bi, bodyEdges(body));
    const edges = edgeCache.get(bi);
    const screen = (p) => {
      const s = p.clone().project(camera);
      return new THREE.Vector2((s.x + 1) / 2 * rect.width, (1 - s.y) / 2 * rect.height);
    };
    const c = new THREE.Vector2(x, y);
    let best = null, bestD = EDGE_PICK_PX;
    for (const e of edges) {
      if (!e.faces.includes(fid)) continue;
      const a = screen(e.a), b = screen(e.b);
      const ab = new THREE.Vector2().subVectors(b, a);
      const t = THREE.MathUtils.clamp(new THREE.Vector2().subVectors(c, a).dot(ab) / Math.max(ab.lengthSq(), 1e-9), 0, 1);
      const d = a.clone().addScaledVector(ab, t).distanceTo(c);
      if (d < bestD) { bestD = d; best = e; }
    }
    return best && edgeInfo(edges, best);
  }

  function pick(ev) {
    const rect = renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2(((ev.clientX - rect.left) / rect.width) * 2 - 1,
      -((ev.clientY - rect.top) / rect.height) * 2 + 1);
    const ray = new THREE.Raycaster();
    ray.setFromCamera(ndc, camera);
    const meshes = modelGroup.children.filter((o) => o.isMesh && !o.userData.sectionCap);
    let hits = ray.intersectObjects(meshes, false);
    if (renderer.clippingPlanes.length) {
      hits = hits.filter((h) => plane.distanceToPoint(h.point) >= 0);
    }
    const hit = hits[0];
    if (!hit) return;
    const body = meshData.bodies[hit.object.userData.bodyIndex];
    const fid = (body.face_ids || [])[hit.faceIndex] ?? 0;
    if (mode === "select") {
      const at = selection.findIndex((s) => s.body === body.name && s.index === fid);
      if (at >= 0) selection.splice(at, 1);
      else if (selection.length < 16) {
        const name = (body.faces || []).find((f) => f.index === fid)?.name;
        selection.push({ type: "face", body: body.name, index: fid, name,
                         point: [hit.point.x, hit.point.y, hit.point.z].map((v) => +v.toFixed(4)) });
      }
      showSelection();
      return;
    }
    if (picks.length === 2) clearMeasure();
    const edge = nearEdge(hit.object.userData.bodyIndex, body, fid, ev.clientX - rect.left, ev.clientY - rect.top, rect);
    if (edge) {
      picks.push({ point: hit.point.clone(), edge });
      const g = new THREE.BufferGeometry().setFromPoints(edge.points);
      const line = new THREE.Line(g, new THREE.LineBasicMaterial({ color: MARK_COLOR, depthTest: false }));
      line.renderOrder = 10;
      measureGroup.add(line);
      marker(edge.center ?? hit.point);
    } else {
      picks.push({ point: hit.point.clone(), ...faceInfo(body, fid) });
      marker(hit.point);
    }
    if (picks.length === 2) {
      const at = (p) => p.edge?.center ?? p.point;
      const g = new THREE.BufferGeometry().setFromPoints([at(picks[0]), at(picks[1])]);
      const line = new THREE.Line(g, new THREE.LineBasicMaterial({ color: MARK_COLOR, depthTest: false }));
      line.renderOrder = 10;
      measureGroup.add(line);
    }
    describe();
    renderScene();
  }

  // A click, not the end of a rotate or pan drag
  let down = null;
  renderer.domElement.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", (e) => {
    if ((mode !== "measure" && mode !== "select") || !down || e.button !== 0) return;
    if (Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 5) pick(e);
  });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mode) setMode(mode);
  });

  return {
    // Called after the view was rebuilt from new mesh data (each mesh carries userData.bodyIndex)
    meshUpdated(data) {
      meshData = data;
      edgeCache = new Map();
      modelBox = new THREE.Box3().setFromObject(modelGroup);
      markerSize = Math.max(modelBox.getSize(new THREE.Vector3()).length() / 250, 0.05);
      addCaps();
      clearMeasure();
      applySection();
      selection = [];  // the faces may have changed
      showSelection();
    },
    clear() {
      if (mode) setMode(mode);
    },
    getSelection() {
      return selection.map(({ name, ...item }) => item);
    },
    clearSelection() {
      selection = [];
      showSelection();
    },
  };
}
