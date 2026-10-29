// Measure and section tools for the 3D view of the Check page. Both work on the triangle mesh the page
// already has (face_ids per triangle), so they need no server and also run in the live demo.
import * as THREE from "three";

const SECTION_COLOR = 0xd26a0c;
const MARK_COLOR = 0xffad45;

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

export function initViewTools({ scene, camera, renderer, modelGroup, renderScene, containerEl }) {
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
    <button type="button" data-tool="measure" title="Click two points or faces">Measure</button>
    <button type="button" data-tool="section" title="Cut the model with a plane">Section</button>
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

  function setMode(next) {
    mode = mode === next ? null : next;
    bar.querySelectorAll("[data-tool]").forEach((b) => b.classList.toggle("active", b.dataset.tool === mode));
    if (mode !== "measure") clearMeasure();
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

  function describe() {
    const [a, b] = picks;
    const lines = [];
    if (!b) {
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
    const info = faceInfo(body, fid);
    if (picks.length === 2) clearMeasure();
    picks.push({ point: hit.point.clone(), ...info });
    marker(hit.point);
    if (picks.length === 2) {
      const g = new THREE.BufferGeometry().setFromPoints([picks[0].point, picks[1].point]);
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
    if (mode !== "measure" || !down || e.button !== 0) return;
    if (Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 5) pick(e);
  });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mode) setMode(mode);
  });

  return {
    // Called after the view was rebuilt from new mesh data (each mesh carries userData.bodyIndex)
    meshUpdated(data) {
      meshData = data;
      modelBox = new THREE.Box3().setFromObject(modelGroup);
      markerSize = Math.max(modelBox.getSize(new THREE.Vector3()).length() / 250, 0.05);
      addCaps();
      clearMeasure();
      applySection();
    },
    clear() {
      if (mode) setMode(mode);
    },
  };
}
