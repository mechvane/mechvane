// The sketch environment (ADR 0005, addendum 2026-11-02, step a): create a sketch on a plane or a flat face,
// draw lines, rectangles and circles with a rubber band, snapping and input boxes at the cursor, and finish or
// cancel. The server keeps the sketch open in the part's SolidCraft session (/api/sketch/*, sketch_session.py);
// this module only draws what `sketch.inspect` returns and turns clicks into SolidCraft sketch commands.
import * as THREE from "three";
import { boxFromDrag, boxTakesCurve } from "./sketchgeom.js";

// Snap radii in screen pixels (SolidCraft's viewport uses 8 for points, 7 for inference; research #53)
const SNAP_POINT_PX = 8;
const SNAP_ALIGN_PX = 7;
const AXIS_SNAP_DEG = 2.5;

// Threshold in screen pixels to distinguish a click from a window/crossing box drag
// (SolidCraft crates/ui-egui/src/panel_runtime/tests.rs: 6 logical points)
const DRAG_THRESHOLD_PX = 6;

// What each tool asks for at the cursor: [role for sketch.draw.dimensioned, label, unit]
const HUD_FIELDS = {
  line: [["length", "Length", "mm"], ["angle", "Angle", "°"]],
  rectangle: [["width", "Width", "mm"], ["height", "Height", "mm"]],
  circle: [["diameter", "Diameter", "mm"]],
  offset: [["distance", "Distance", "mm"]],
};

const COLORS = {
  free: 0x58a6ff,       // under-constrained, as SolidCraft and Inventor show it
  fixed: 0xe6edf3,      // fully constrained (dark theme), see colorFixed()
  projected: 0xa371f7,  // projected geometry (SolidCraft SKETCH_PROJECTED RGB(130, 60, 200)), see colorProjected()
  preview: 0xf0b429,
  axisX: 0xe5534b,
  axisY: 0x57ab5a,
  align: 0x8b949e,
};

const fmt = (v) => String(Math.round(v * 1000) / 1000);
const num = (s) => {
  const v = parseFloat(String(s).replace(",", "."));
  return Number.isFinite(v) ? v : null;
};

export function initSketcher(h) {
  // h: { scene, camera, renderer, controls, renderScene, viewTools, lookAlong, statusEl, get, post, reload,
  //      activateTab, viewportEl, log, isDark }
  const group = new THREE.Group();
  group.renderOrder = 10;
  h.scene.add(group);

  let active = null;      // { name, frame, state, editing }
  let tool = null;        // "line" | "rectangle" | "circle" | null
  let clicks = [];        // placed points of the current shape: {at: [u, v], snap}
  let cursor = null;      // {at, snap, screen}
  let hud = null;         // {el, inputs: {role: input}, locked: {role: value}}
  let busy = false;
  let savedView = null;
  let savedButtons = null;
  let savedHint = null;
  let choosing = null;    // the plane chooser bar while a new sketch waits for its plane
  let autoProject = true; // Inventor's "Autoproject edges for sketch creation" (default on)

  const canvas = h.renderer.domElement;
  const snapEl = document.createElement("div");
  snapEl.className = "sketch-snap";
  snapEl.hidden = true;
  h.viewportEl.appendChild(snapEl);
  // Box selection marquee (window: solid blue, crossing: dashed green)
  const boxEl = document.createElement("div");
  boxEl.className = "sketch-box-select";
  boxEl.hidden = true;
  h.viewportEl.appendChild(boxEl);
  // dimension texts on the geometry (HTML over the view); double-click one to change its value
  const dimLayer = document.createElement("div");
  dimLayer.className = "sketch-dims";
  h.viewportEl.appendChild(dimLayer);
  let dimSel = [];        // the Dimension tool's picked entities: {kind: "point"|"curve", id, at|curve}
  let dimHover = null;
  let dimEdit = null;     // {param, input}
  let lastDim = null;
  let conSel = [];        // a constraint tool's picked entities
  let picked = [];        // with no tool: selected curves, points, constraints or dimensions (Delete removes them)     // params of the dimension just placed (to place it again as `name = expression`)
  let boxDrag = null;     // { startScreen, startClient, shift, ctrl, raw, active, pointerId }
  let lineType = "normal"; // the line type new curves get (SolidCraft's palette, #138): "normal" or "construction"
  window.mechvaneSketchPicked = () => picked;

  // --- plane geometry ---------------------------------------------------------------------------------------
  const vec = (a) => new THREE.Vector3(...a);
  function world([u, v]) {
    const f = active.frame;
    return vec(f.origin).addScaledVector(vec(f.x_dir), u).addScaledVector(vec(f.y_dir), v);
  }
  function screenOf(uv) {
    const p = world(uv).project(h.camera);
    const r = canvas.getBoundingClientRect();
    return [(p.x + 1) / 2 * r.width, (1 - p.y) / 2 * r.height];
  }
  function planeAt(ev) {
    const r = canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    const ray = new THREE.Raycaster();
    ray.setFromCamera(ndc, h.camera);
    const f = active.frame, x = vec(f.x_dir), y = vec(f.y_dir);
    const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(new THREE.Vector3().crossVectors(x, y).normalize(), vec(f.origin));
    const hit = ray.ray.intersectPlane(plane, new THREE.Vector3());
    if (!hit) return null;
    const d = hit.sub(vec(f.origin));
    return { uv: [d.dot(x), d.dot(y)], screen: [ev.clientX - r.left, ev.clientY - r.top] };
  }
  // mm per screen pixel on the plane near uv, for the grid step
  function mmPerPx(uv) {
    const a = screenOf(uv), b = screenOf([uv[0] + 1, uv[1]]);
    const px = Math.hypot(b[0] - a[0], b[1] - a[1]);
    return px > 1e-9 ? 1 / px : 1;
  }
  function gridStep(uv) {
    const raw = mmPerPx(uv) * 6;
    const p = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 5, 10].map((k) => k * p).find((s) => s >= raw) || 10 * p;
    return Math.max(step, 0.01);
  }

  // --- snapping (research #53, 3.1: points, midpoints, alignment, axis angle, grid; Ctrl turns it off) ----------
  function snapPoint(raw, ev) {
    const st = active.state || {};
    const scr = raw.screen;
    if (ev && (ev.ctrlKey || ev.metaKey)) return { at: raw.uv, snap: null };
    let best = null, bestD = Infinity;
    const consider = (uv, snap, px) => {
      const s = screenOf(uv);
      const d = Math.hypot(s[0] - scr[0], s[1] - scr[1]);
      if (d <= px && d < bestD) { best = { at: uv.slice(), snap }; bestD = d; }
    };
    for (const p of st.points || []) consider(p.at, { kind: "point", id: p.id }, SNAP_POINT_PX);
    for (const c of clicks) consider(c.at, { kind: "point" }, SNAP_POINT_PX);
    if (best) return best;
    for (const c of st.curves || []) {
      if (c.type !== "line") continue;
      const m = [(c.start_at[0] + c.end_at[0]) / 2, (c.start_at[1] + c.end_at[1]) / 2];
      consider(m, { kind: "mid", line: c.id }, SNAP_POINT_PX);
    }
    if (best) return best;
    // grid first, then alignment with existing points and the axis angle from the last click override it
    const g = gridStep(raw.uv);
    let at = [Math.round(raw.uv[0] / g) * g, Math.round(raw.uv[1] / g) * g];
    let snap = null;
    // a line's own start point gives H/V (below), not an alignment line
    const own = tool === "line" && clicks.length === 1 ? clicks[0].at : null;
    const refs = [...(st.points || []).map((p) => p.at), ...clicks.map((c) => c.at)]
      .filter((r) => !own || Math.hypot(r[0] - own[0], r[1] - own[1]) > 1e-9);
    // screen x/y are the sketch's u/v only when looking straight at it, so test alignment in sketch coordinates
    let alignX = null, alignY = null;
    const tol = mmPerPx(raw.uv) * SNAP_ALIGN_PX;
    for (const r of refs) {
      if (alignX === null && Math.abs(r[0] - raw.uv[0]) <= tol) alignX = r;
      if (alignY === null && Math.abs(r[1] - raw.uv[1]) <= tol) alignY = r;
    }
    if (alignX) { at[0] = alignX[0]; snap = { kind: "align", from: [alignX] }; }
    if (alignY) { at[1] = alignY[1]; snap = { kind: "align", from: [...(snap?.from || []), alignY] }; }
    if (tool === "line" && clicks.length === 1 && !alignX && !alignY) {
      const o = clicks[0].at, du = raw.uv[0] - o[0], dv = raw.uv[1] - o[1];
      const ang = Math.abs(Math.atan2(dv, du) * 180 / Math.PI);
      if (Math.min(ang, 180 - ang) <= AXIS_SNAP_DEG) { at = [at[0], o[1]]; snap = { kind: "horizontal" }; }
      else if (Math.abs(90 - ang) <= AXIS_SNAP_DEG) { at = [o[0], at[1]]; snap = { kind: "vertical" }; }
    }
    return { at, snap };
  }

  // --- drawing ------------------------------------------------------------------------------------------------
  function clearGroup() {
    while (group.children.length) {
      const o = group.children.pop();
      o.geometry?.dispose();
      o.material?.dispose();
    }
  }
  function addLine(pts, color, dashed = false) {
    if (!pts || pts.length < 2) return;
    const geom = new THREE.BufferGeometry().setFromPoints(pts.map(world));
    const mat = dashed
      ? new THREE.LineDashedMaterial({ color, dashSize: mmPerPx(pts[0]) * 6, gapSize: mmPerPx(pts[0]) * 4, depthTest: false })
      : new THREE.LineBasicMaterial({ color, depthTest: false });
    const line = new THREE.Line(geom, mat);
    if (dashed) line.computeLineDistances();
    line.renderOrder = 10;
    group.add(line);
  }
  function addPoints(list, color, size = 6) {
    if (!list.length) return;
    const geom = new THREE.BufferGeometry().setFromPoints(list.map(world));
    const pts = new THREE.Points(geom, new THREE.PointsMaterial({ color, size, sizeAttenuation: false, depthTest: false }));
    pts.renderOrder = 11;
    group.add(pts);
  }
  const circlePts = (c, r, a0 = 0, a1 = Math.PI * 2) => {
    const n = Math.max(16, Math.ceil(Math.abs(a1 - a0) / (Math.PI * 2) * 96));
    return Array.from({ length: n + 1 }, (_, i) => {
      const a = a0 + (a1 - a0) * (i / n);
      return [c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)];
    });
  };
  // the arc from s to e through t (null when the three points are in a line)
  function arcThrough(sp, e, t) {
    const ax = sp[0], ay = sp[1], bx = t[0], by = t[1], cx = e[0], cy = e[1];
    const d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
    if (Math.abs(d) < 1e-9) return null;
    const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d;
    const uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;
    const ang = (p) => Math.atan2(p[1] - uy, p[0] - ux);
    const norm = (a) => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
    const a0 = ang(sp), at = norm(ang(t) - a0), ae = norm(ang(e) - a0);
    // counter-clockwise from s to e if t lies on that way, else clockwise
    const sweep = at < ae ? ae : ae - 2 * Math.PI;
    return circlePts([ux, uy], Math.hypot(ax - ux, ay - uy), a0, a0 + sweep);
  }
  const colorFixed = () => (h.isDark() ? COLORS.fixed : 0x1f2328);
  const colorProjected = () => (h.isDark() ? COLORS.projected : 0x823cc8);

  function shapePreview() {
    if (!tool || !clicks.length || !cursor) return null;
    const a = clicks[0].at, b = previewEnd();
    if (tool === "line") return [a, b];
    if (tool === "rectangle") return [a, [b[0], a[1]], b, [a[0], b[1]], a];
    if (tool === "circle") return circlePts(a, Math.hypot(b[0] - a[0], b[1] - a[1]));
    if (tool === "arc") return clicks.length < 2 ? [a, b] : arcThrough(a, clicks[1].at, b) || [a, b, clicks[1].at];
    return null;
  }
  // the cursor point with the values locked in the input boxes applied
  function previewEnd() {
    const a = clicks[0].at;
    let b = cursor.at.slice();
    const L = hud?.locked || {};
    if (tool === "line") {
      let len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      let ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
      if (L.length != null) len = L.length;
      if (L.angle != null) ang = L.angle * Math.PI / 180;
      b = [a[0] + len * Math.cos(ang), a[1] + len * Math.sin(ang)];
    } else if (tool === "rectangle") {
      const sx = Math.sign(b[0] - a[0]) || 1, sy = Math.sign(b[1] - a[1]) || 1;
      if (L.width != null) b[0] = a[0] + sx * L.width;
      if (L.height != null) b[1] = a[1] + sy * L.height;
    } else if (tool === "circle" && L.diameter != null) {
      const d = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      b = [a[0] + (b[0] - a[0]) / d * L.diameter / 2, a[1] + (b[1] - a[1]) / d * L.diameter / 2];
    }
    return b;
  }

  // --- dimensions (step b) -----------------------------------------------------------------------------------
  function segDist(p, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
    const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
    return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
  }
  // the point (8 px) or curve (6 px) under the cursor, points first
  function pickEntity(scr) {
    const st = active.state || {};
    let best = null, bestD = Infinity;
    for (const p of st.points || []) {
      const s2 = screenOf(p.at), d = Math.hypot(s2[0] - scr[0], s2[1] - scr[1]);
      if (d <= SNAP_POINT_PX && d < bestD) { best = { kind: "point", id: p.id, at: p.at }; bestD = d; }
    }
    if (best) return best;
    return pickCurve(scr, 6);
  }
  // the curve (tol px) under the cursor, ignoring points (for trim, extend, offset)
  function pickCurve(scr, tol = 8) {
    const st = active.state || {};
    let best = null, bestD = Infinity;
    for (const c of st.curves || []) {
      let d = Infinity;
      if (c.type === "line") d = segDist(scr, screenOf(c.start_at), screenOf(c.end_at));
      else if ((c.type === "circle" || c.type === "arc") && c.center_at) {
        const cs = screenOf(c.center_at), e = screenOf([c.center_at[0] + c.radius, c.center_at[1]]);
        d = Math.abs(Math.hypot(scr[0] - cs[0], scr[1] - cs[1]) - Math.hypot(e[0] - cs[0], e[1] - cs[1]));
      }
      if (d <= tol && d < bestD) { best = { kind: "curve", id: c.id, curve: c }; bestD = d; }
    }
    return best;
  }
  const ANGLE_TYPES = new Set(["angle", "line_angle"]);
  function dimText(c) {
    const ang = ANGLE_TYPES.has(c.type);
    const pre = c.type === "diameter" ? "Ø" : c.type === "radius" ? "R" : "";
    const expr = String(c.expression ?? "");
    const plain = /^-?[0-9.]+\s*(mm|deg)?$/.test(expr.trim());
    const val = ang ? (plain ? parseFloat(expr) : c.value * 180 / Math.PI) : c.value;
    const num2 = `${pre}${fmt(Math.round(val * 100) / 100)}${ang ? "°" : ""}`;
    return plain ? num2 : `${expr.replace(/\s*mm$/, "")} = ${num2}`;
  }
  // --- dimension drawing (#132): extension lines, dimension line or arc with arrowheads, value on it --------------
  // All in screen pixels. A linear dimension sits DIM_OFF px off its geometry, on the side away from the middle of
  // the sketch (outside a rectangle); diameter and radius at 45°, as the text placement before.
  const DIM_OFF = 22, EXT_GAP = 3, EXT_OVER = 5, ARROW = 8;
  const v2 = {
    sub: (a, b) => [a[0] - b[0], a[1] - b[1]], add: (a, b) => [a[0] + b[0], a[1] + b[1]],
    mul: (a, k) => [a[0] * k, a[1] * k], len: (a) => Math.hypot(a[0], a[1]),
    unit: (a) => { const l = Math.hypot(a[0], a[1]) || 1; return [a[0] / l, a[1] / l]; },
    perp: (a) => [-a[1], a[0]], dot: (a, b) => a[0] * b[0] + a[1] * b[1], mid: (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
  };
  function sketchMiddle(st) {
    const pts = (st.points || []).filter((p) => p.id !== "origin" && !p.link).map((p) => screenOf(p.at));
    if (!pts.length) return screenOf([0, 0]);
    return v2.mul(pts.reduce((a, b) => v2.add(a, b), [0, 0]), 1 / pts.length);
  }
  // A and B (screen) measured along AB, dimension line `off` px to `side` (a unit vector)
  function alignedGeom(A, B, side, off = DIM_OFF) {
    const a2 = v2.add(A, v2.mul(side, off)), b2 = v2.add(B, v2.mul(side, off));
    const d = v2.unit(v2.sub(b2, a2));
    const sgn = off >= 0 ? 1 : -1;
    return {
      lines: [[a2, b2]],
      ext: [[v2.add(A, v2.mul(side, EXT_GAP * sgn)), v2.add(A, v2.mul(side, off + EXT_OVER * sgn))],
        [v2.add(B, v2.mul(side, EXT_GAP * sgn)), v2.add(B, v2.mul(side, off + EXT_OVER * sgn))]],
      arrows: [[a2, v2.mul(d, -1)], [b2, d]], text: v2.mid(a2, b2),
    };
  }
  function awayFrom(A, B, middle) {
    const n = v2.perp(v2.unit(v2.sub(B, A)));
    const toMid = v2.sub(middle, v2.mid(A, B));
    if (v2.len(toMid) < 1) return n[1] <= 0 ? n : v2.mul(n, -1);  // a lone line: above it
    return v2.dot(n, toMid) > 0 ? v2.mul(n, -1) : n;
  }
  // horizontal or vertical (sketch axes) distance between uv points P and Q, the dimension line `offPx` beyond both
  function axisGeom(P, Q, horizontal, offPx = DIM_OFF) {
    const k = offPx * mmPerPx(P);
    const A = horizontal ? [P[0], Math.max(P[1], Q[1]) + k] : [Math.max(P[0], Q[0]) + k, P[1]];
    const B = horizontal ? [Q[0], A[1]] : [A[0], Q[1]];
    const sP = screenOf(P), sQ = screenOf(Q), sA = screenOf(A), sB = screenOf(B);
    const over = (from, to) => v2.add(to, v2.mul(v2.unit(v2.sub(to, from)), EXT_OVER));
    const d = v2.unit(v2.sub(sB, sA));
    return { lines: [[sA, sB]], ext: [[sP, over(sP, sA)], [sQ, over(sQ, sB)]], arrows: [[sA, v2.mul(d, -1)], [sB, d]], text: v2.mid(sA, sB) };
  }
  // point P to the line through L0, L1 (uv): the dimension line along the perpendicular, the line extended to it
  function pointLineGeom(P, L0, L1) {
    const d = [L1[0] - L0[0], L1[1] - L0[1]], l2 = d[0] * d[0] + d[1] * d[1] || 1;
    const t = ((P[0] - L0[0]) * d[0] + (P[1] - L0[1]) * d[1]) / l2;
    const F = [L0[0] + t * d[0], L0[1] + t * d[1]];
    const sP = screenOf(P), sF = screenOf(F);
    const dir = v2.unit(v2.sub(sF, sP));
    const ext = t < 0 || t > 1 ? [[screenOf(t < 0 ? L0 : L1), sF]] : [];
    return { lines: [[sP, sF]], ext, arrows: [[sP, v2.mul(dir, -1)], [sF, dir]], text: v2.mid(sP, sF) };
  }
  // diameter (through the centre, arrows on the rim) or radius (from the centre); `dir` a screen direction
  function circleGeom(C, r, diameter, dir = null) {
    const sC = screenOf(C);
    const rim = screenOf([C[0] + r, C[1]]);
    const R = v2.len(v2.sub(rim, sC));
    const u = dir ? v2.unit(dir) : v2.unit([Math.SQRT1_2, -Math.SQRT1_2]);
    const far = v2.add(sC, v2.mul(u, R)), near = diameter ? v2.add(sC, v2.mul(u, -R)) : sC;
    const leaderEnd = v2.add(far, v2.mul(u, 18));
    return {
      lines: [[near, leaderEnd]], ext: [],
      arrows: diameter ? [[far, u], [near, v2.mul(u, -1)]] : [[far, u]],
      text: v2.add(far, v2.mul(u, 30)),
    };
  }
  // angle between lines A0A1 and B0B1 (uv): an arc around their crossing, from one line towards the other
  function angleGeom(A0, A1, B0, B1, radiusPx = 40) {
    const da = [A1[0] - A0[0], A1[1] - A0[1]], db = [B1[0] - B0[0], B1[1] - B0[1]];
    const den = da[0] * db[1] - da[1] * db[0];
    if (Math.abs(den) < 1e-9) return null;
    const t = ((B0[0] - A0[0]) * db[1] - (B0[1] - A0[1]) * db[0]) / den;
    const O = [A0[0] + t * da[0], A0[1] + t * da[1]];
    const sO = screenOf(O);
    // each leg points from the crossing to the farther end of its line
    const leg = (P0, P1) => v2.unit(v2.sub(screenOf(Math.hypot(P1[0] - O[0], P1[1] - O[1]) >= Math.hypot(P0[0] - O[0], P0[1] - O[1]) ? P1 : P0), sO));
    const ua = leg(A0, A1), ub = leg(B0, B1);
    let a0 = Math.atan2(ua[1], ua[0]), a1 = Math.atan2(ub[1], ub[0]);
    let sweep = a1 - a0;
    while (sweep > Math.PI) sweep -= 2 * Math.PI;
    while (sweep < -Math.PI) sweep += 2 * Math.PI;
    const pts = [];
    for (let i = 0; i <= 24; i++) {
      const a = a0 + (sweep * i) / 24;
      pts.push(v2.add(sO, [Math.cos(a) * radiusPx, Math.sin(a) * radiusPx]));
    }
    const am = a0 + sweep / 2;
    const tan = (a, sg) => [-Math.sin(a) * sg, Math.cos(a) * sg];
    const sg = sweep >= 0 ? 1 : -1;
    return {
      lines: [], arc: pts, ext: [[sO, v2.add(sO, v2.mul(ua, radiusPx + EXT_OVER))], [sO, v2.add(sO, v2.mul(ub, radiusPx + EXT_OVER))]],
      arrows: [[pts[0], tan(a0, -sg)], [pts[pts.length - 1], tan(a1, sg)]],
      text: v2.add(sO, [Math.cos(am) * (radiusPx + 14), Math.sin(am) * (radiusPx + 14)]),
    };
  }
  // the drawing of a placed dimension (a constraint with a value), or null for a kind not drawn yet
  function dimGeom(c, st, middle) {
    const P = (i) => st.points?.[i]?.at, C = (i) => st.curves?.[i];
    const line = (k) => (k?.type === "line" && k.start_at && k.end_at ? k : null);
    try {
      if (c.type === "length" && line(C(c.l))) {
        const k = C(c.l), A = screenOf(k.start_at), B = screenOf(k.end_at);
        return alignedGeom(A, B, awayFrom(A, B, middle));
      }
      if (c.type === "distance" && P(c.p) && P(c.q)) {
        const A = screenOf(P(c.p)), B = screenOf(P(c.q));
        return alignedGeom(A, B, awayFrom(A, B, middle));
      }
      if ((c.type === "distance_x" || c.type === "distance_y") && P(c.p) && P(c.q)) return axisGeom(P(c.p), P(c.q), c.type === "distance_x");
      if (c.type === "point_line_distance" && P(c.p) && line(C(c.l))) return pointLineGeom(P(c.p), C(c.l).start_at, C(c.l).end_at);
      if ((c.type === "diameter" || c.type === "radius") && C(c.c)?.center_at) return circleGeom(C(c.c).center_at, C(c.c).radius, c.type === "diameter");
      if (c.type === "angle" && line(C(c.a)) && line(C(c.b))) {
        return angleGeom(C(c.a).start_at, C(c.a).end_at, C(c.b).start_at, C(c.b).end_at);
      }
    } catch (_) { /* a half-solved sketch: no drawing, the value stays */ }
    return null;
  }
  // the preview while the Dimension tool has picked something (#132): what a click there would place, at the cursor
  function dimPreview(st) {
    if (tool !== "dimension" || !dimSel.length || !cursor) return null;
    const cur = screenOf(cursor.at);
    const ents = dimSel;
    const curveOf = (e) => (e.kind === "curve" ? e.curve : null);
    const ptOf = (e) => (e.kind === "point" ? e.at : null);
    const sideTo = (A, B) => {
      const n = v2.perp(v2.unit(v2.sub(B, A)));
      const off = v2.dot(n, v2.sub(cur, A));
      return { side: off >= 0 ? n : v2.mul(n, -1), off: Math.max(Math.abs(off), 12) };
    };
    const uvd = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
    if (ents.length === 1) {
      const k = curveOf(ents[0]);
      if (k?.type === "line") {
        const A = screenOf(k.start_at), B = screenOf(k.end_at), { side, off } = sideTo(A, B);
        return { ...alignedGeom(A, B, side, off), value: fmt(Math.round(uvd(k.start_at, k.end_at) * 100) / 100) };
      }
      if ((k?.type === "circle" || k?.type === "arc") && k.center_at) {
        const dia = k.type === "circle";
        const g = circleGeom(k.center_at, k.radius, dia, v2.sub(cur, screenOf(k.center_at)));
        return { ...g, text: cur, value: `${dia ? "Ø" : "R"}${fmt(Math.round((dia ? 2 * k.radius : k.radius) * 100) / 100)}` };
      }
      return null;
    }
    const [e1, e2] = ents;
    const p1 = ptOf(e1), p2 = ptOf(e2), l1 = curveOf(e1)?.type === "line" ? curveOf(e1) : null, l2 = curveOf(e2)?.type === "line" ? curveOf(e2) : null;
    if (p1 && p2) {
      const A = screenOf(p1), B = screenOf(p2), { side, off } = sideTo(A, B);
      return { ...alignedGeom(A, B, side, off), value: fmt(Math.round(uvd(p1, p2) * 100) / 100) };
    }
    const pl = p1 && l2 ? [p1, l2] : p2 && l1 ? [p2, l1] : null;
    if (pl) {
      const [P, L] = pl;
      const g = pointLineGeom(P, L.start_at, L.end_at);
      const d = [L.end_at[0] - L.start_at[0], L.end_at[1] - L.start_at[1]];
      const dist = Math.abs((P[0] - L.start_at[0]) * d[1] - (P[1] - L.start_at[1]) * d[0]) / (Math.hypot(...d) || 1);
      return { ...g, value: fmt(Math.round(dist * 100) / 100) };
    }
    if (l1 && l2) {
      const g = angleGeom(l1.start_at, l1.end_at, l2.start_at, l2.end_at);
      if (g) {
        const a = Math.atan2(l1.end_at[1] - l1.start_at[1], l1.end_at[0] - l1.start_at[0]);
        const b = Math.atan2(l2.end_at[1] - l2.start_at[1], l2.end_at[0] - l2.start_at[0]);
        let deg = Math.abs(((b - a) * 180) / Math.PI) % 180;
        if (deg > 90) deg = 180 - deg;
        return { ...g, value: `${fmt(Math.round(deg * 100) / 100)}°` };
      }
      const g2 = pointLineGeom(l1.start_at, l2.start_at, l2.end_at);
      const d = [l2.end_at[0] - l2.start_at[0], l2.end_at[1] - l2.start_at[1]];
      const dist = Math.abs((l1.start_at[0] - l2.start_at[0]) * d[1] - (l1.start_at[1] - l2.start_at[1]) * d[0]) / (Math.hypot(...d) || 1);
      return { ...g2, value: fmt(Math.round(dist * 100) / 100) };
    }
    return null;
  }
  const SVG_NS = "http://www.w3.org/2000/svg";
  function drawDimGeom(svg, g, cls) {
    const path = (d, extra) => {
      const el = document.createElementNS(SVG_NS, "path");
      el.setAttribute("d", d);
      el.setAttribute("class", `${cls}${extra ? ` ${extra}` : ""}`);
      svg.appendChild(el);
    };
    const P = (p) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`;
    for (const [a, b] of g.ext || []) path(`M${P(a)}L${P(b)}`, "dim-ext");
    for (const [a, b] of g.lines || []) path(`M${P(a)}L${P(b)}`, "dim-line");
    if (g.arc?.length) path(`M${g.arc.map(P).join("L")}`, "dim-line");
    for (const [tip, dir] of g.arrows || []) {
      const u = v2.unit(dir), n = v2.perp(u);
      const back = v2.sub(tip, v2.mul(u, ARROW));
      path(`M${P(tip)}L${P(v2.add(back, v2.mul(n, ARROW * 0.35)))}L${P(v2.sub(back, v2.mul(n, ARROW * 0.35)))}Z`, "dim-arrow");
    }
  }

  // where a dimension's text goes, in screen pixels
  function dimSpot(c, st) {
    const g = dimGeom(c, st, sketchMiddle(st));
    if (g) return g.text;
    const P = (i) => st.points?.[i]?.at, C = (i) => st.curves?.[i];
    if (c.c !== undefined && C(c.c)?.center_at) {
      const k = C(c.c), a = Math.PI / 4;
      return screenOf([k.center_at[0] + k.radius * Math.cos(a), k.center_at[1] + k.radius * Math.sin(a)]);
    }
    if (c.l !== undefined && C(c.l)?.start_at) {
      const k = C(c.l), a = screenOf(k.start_at), b = screenOf(k.end_at);
      const n = [-(b[1] - a[1]), b[0] - a[0]], L = Math.hypot(...n) || 1;
      return [(a[0] + b[0]) / 2 - n[0] / L * 14, (a[1] + b[1]) / 2 - n[1] / L * 14];
    }
    if (c.p !== undefined && c.q !== undefined && P(c.p) && P(c.q)) {
      const a = screenOf(P(c.p)), b = screenOf(P(c.q));
      return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 14];
    }
    return null;
  }
  function drawDims() {
    dimLayer.textContent = "";
    if (!active) return;
    const st = active.state || {};
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "sketch-dim-geo");
    dimLayer.appendChild(svg);
    const middle = sketchMiddle(st);
    const prev = dimPreview(st);
    if (prev) {
      drawDimGeom(svg, prev, "dim-preview");
      const el = document.createElement("span");
      el.className = "sketch-dim preview";
      el.textContent = prev.value;
      el.style.left = `${prev.text[0]}px`;
      el.style.top = `${prev.text[1]}px`;
      dimLayer.appendChild(el);
    }
    for (const c of st.constraints || []) {
      if (c.value === undefined || !c.param) continue;
      const g = dimGeom(c, st, middle);
      if (g) drawDimGeom(svg, g, picked.some((p) => p.id === c.id) || dimEdit?.param === c.param ? "dim-picked" : "dim");
      const at = g ? g.text : dimSpot(c, st);
      if (!at) continue;
      if (dimEdit?.param === c.param) { dimEdit.input.style.left = `${at[0]}px`; dimEdit.input.style.top = `${at[1]}px`; continue; }
      const el = document.createElement("span");
      el.className = "sketch-dim";
      el.dataset.param = c.param;
      el.textContent = dimText(c);
      el.title = `${c.param}: double-click to change`;
      el.style.left = `${at[0]}px`;
      el.style.top = `${at[1]}px`;
      el.addEventListener("dblclick", (e) => { e.stopPropagation(); openDimEditor(c.param); });
      el.addEventListener("click", (e) => { e.stopPropagation(); togglePick("dimension", c.id, e); });
      if (picked.some((p) => p.id === c.id)) el.classList.add("picked");
      dimLayer.appendChild(el);
    }
    drawGlyphs(st);
  }
  // the value box on a dimension: a number or expression changes it, `name = expression` (only right after
  // placing it) makes it a named parameter
  function openDimEditor(param) {
    closeDimEditor();
    const c = (active.state.constraints || []).find((k) => k.param === param);
    if (!c) return;
    const input = document.createElement("input");
    input.className = "sketch-dim-edit";
    input.value = ANGLE_TYPES.has(c.type) ? String(c.expression ?? "").replace(/\s*deg$/, "") : String(c.expression ?? "").replace(/\s*mm$/, "");
    input.setAttribute("aria-label", `Value of ${param}`);
    const fresh = lastDim && lastDim.param === param;
    input.addEventListener("keydown", async (e) => {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeDimEditor(); draw(); return; }
      if (e.key !== "Enter") return;
      e.preventDefault();
      e.stopPropagation();
      const v = input.value.trim();
      if (!v) return;
      busy = true;
      try {
        if (/^#?[A-Za-z_][A-Za-z0-9_]*\s*=/.test(v)) {
          if (!fresh) throw new Error("a name can only be given while placing the dimension");
          // place it again with the name: one undo step back, then the same dimension with `name = expression`
          await h.post("api/sketch/undo", {}).then((r) => { active.state = r.state; });
          await send("sketch.dimension", { ...lastDim.params, value: v });
        } else {
          const ang = ANGLE_TYPES.has(c.type) && /^-?[0-9.]+$/.test(v);
          await send("parameters.change", { changes: { [param]: ang ? `${v} deg` : v } });
        }
        lastDim = null;
        closeDimEditor();
        status();
      } catch (err) {
        h.statusEl.textContent = `Sketch: ${err.message}`;
        input.select();
      } finally {
        busy = false;
        draw();
      }
    });
    dimLayer.parentElement.appendChild(input);
    dimEdit = { param, input };
    drawDims();
    input.focus();
    input.select();
  }
  function closeDimEditor() {
    if (dimEdit) dimEdit.input.remove();
    dimEdit = null;
  }
  // Constrain tools: what each needs and the command it sends
  const CON = {
    horizontal: { label: "Horizontal", glyph: "H" }, vertical: { label: "Vertical", glyph: "V" },
    parallel: { label: "Parallel", glyph: "∥" }, perpendicular: { label: "Perpendicular", glyph: "⊥" },
    tangent: { label: "Tangent", glyph: "T" }, equal: { label: "Equal", glyph: "=" },
    coincident: { label: "Coincident", glyph: "" }, fix: { label: "Fixed", glyph: "⚓" },
  };
  const GLYPH = { horizontal: "H", vertical: "V", horizontal_points: "H", vertical_points: "V", parallel: "∥",
    perpendicular: "⊥", tangent: "T", equal: "=", fix: "⚓", concentric: "◎", midpoint: "M", symmetry: "⇋" };
  async function conClick(raw) {
    const kind = tool.slice(4);
    const ent = pickEntity(raw.screen);
    if (!ent || busy || conSel.some((e) => e.id === ent.id)) return;
    conSel.push(ent);
    const isLine = (e) => e.kind === "curve" && e.curve.type === "line";
    let command = null, params = null;
    if (kind === "horizontal" || kind === "vertical") {
      if (isLine(conSel[0])) { command = "sketch.constraint.horizontal_vertical"; params = { line: conSel[0].id, mode: kind }; }
      else if (conSel[0].kind !== "point") conSel = [];
      else if (conSel.length === 2 && conSel[1].kind === "point") {
        command = "sketch.constraint.horizontal_vertical"; params = { points: [conSel[0].id, conSel[1].id], mode: kind };
      } else if (conSel.length === 2) conSel = [];
    } else if (kind === "fix") {
      // without `fixed` SolidCraft toggles: a second click releases it
      command = "sketch.constraint.fix"; params = { entity: conSel[0].id };
    } else if (conSel.length === 2) {
      command = `sketch.constraint.${kind}`; params = { a: conSel[0].id, b: conSel[1].id };
    }
    if (command) {
      busy = true;
      try {
        await send(command, params);
        h.log?.("sketch_cmd", { command, kind });
      } catch (err) {
        h.statusEl.textContent = `Sketch: ${err.message}`;
        conSel = [];
        busy = false;
        draw();
        return;
      }
      busy = false;
      conSel = [];
    }
    status();
    draw();
  }
  // with no tool: a click selects a curve or point (Shift adds, Ctrl removes), Delete removes the selection
  function selectClick(raw, ev) {
    const ent = pickEntity(raw.screen);
    const item = ent ? { kind: ent.kind, id: ent.id, ent } : null;
    const isShift = ev.shiftKey;
    const isCtrl = ev.ctrlKey || ev.metaKey;
    if (!isShift && !isCtrl) picked = picked.filter((p) => item && p.id === item.id);
    if (item) {
      const i = picked.findIndex((p) => p.id === item.id);
      if (i >= 0 && (isShift || isCtrl)) picked.splice(i, 1);
      else if (i < 0 && !isCtrl) picked.push(item);
    }
    status();
    draw();
  }

  // Window selection (left-to-right): only items wholly enclosed
  // Crossing selection (right-to-left): any item touching or inside
  // Shift adds to selection, Ctrl removes from selection
  function applyBoxSelect(box, ev) {
    const st = active.state || {};
    const hits = [];
    for (const c of st.curves || []) {
      if (boxTakesCurve(box, c, box.crossing, screenOf)) {
        hits.push({ kind: "curve", id: c.id, ent: { kind: "curve", id: c.id, curve: c } });
      }
    }
    const isShift = ev.shiftKey;
    const isCtrl = ev.ctrlKey || ev.metaKey;
    if (isShift) {
      for (const h of hits) {
        if (!picked.some((p) => p.id === h.id)) picked.push(h);
      }
    } else if (isCtrl) {
      const hitIds = new Set(hits.map((h) => h.id));
      picked = picked.filter((p) => !hitIds.has(p.id));
    } else {
      picked = hits;
    }
    status();
    draw();
  }

  // Apply constraint tool directly to the selected entities where meaningful
  async function applyConstraintToPicked(kind) {
    if (!picked.length || busy) return false;
    const isLine = (p) => p.ent?.kind === "curve" && p.ent.curve?.type === "line";
    const isPoint = (p) => p.ent?.kind === "point" || p.kind === "point";
    const isCurve = (p) => p.ent?.kind === "curve" || p.kind === "curve";

    let cmds = [];
    if (kind === "fix") {
      for (const p of picked) cmds.push({ command: "sketch.constraint.fix", params: { entity: p.id } });
    } else if (kind === "horizontal" || kind === "vertical") {
      if (picked.length === 2 && isPoint(picked[0]) && isPoint(picked[1])) {
        cmds.push({ command: "sketch.constraint.horizontal_vertical", params: { points: [picked[0].id, picked[1].id], mode: kind } });
      } else {
        const lines = picked.filter(isLine);
        if (lines.length > 0) {
          for (const l of lines) cmds.push({ command: "sketch.constraint.horizontal_vertical", params: { line: l.id, mode: kind } });
        }
      }
    } else if (kind === "parallel" || kind === "perpendicular" || kind === "tangent") {
      if (picked.length === 2 && isCurve(picked[0]) && isCurve(picked[1])) {
        cmds.push({ command: `sketch.constraint.${kind}`, params: { a: picked[0].id, b: picked[1].id } });
      }
    } else if (kind === "equal") {
      const curves = picked.filter(isCurve);
      if (curves.length >= 2) {
        for (let i = 0; i < curves.length - 1; i++) {
          cmds.push({ command: "sketch.constraint.equal", params: { a: curves[i].id, b: curves[i + 1].id } });
        }
      }
    } else if (kind === "coincident") {
      if (picked.length === 2) {
        cmds.push({ command: "sketch.constraint.coincident", params: { a: picked[0].id, b: picked[1].id } });
      }
    }

    if (!cmds.length) return false;

    busy = true;
    try {
      for (const { command, params } of cmds) {
        await send(command, params);
        h.log?.("sketch_cmd", { command, kind });
      }
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    } finally {
      busy = false;
      status();
      draw();
    }
    return true;
  }
  function togglePick(kind, id, ev) {
    if (tool) return;
    const i = picked.findIndex((p) => p.id === id);
    if (ev.shiftKey) { if (i >= 0) picked.splice(i, 1); else picked.push({ kind, id }); }
    else picked = i >= 0 && picked.length === 1 ? [] : [{ kind, id }];
    status();
    draw();
  }
  async function deletePicked() {
    if (!picked.length || busy) return;
    busy = true;
    try {
      await send("sketch.delete", { entities: picked.map((p) => p.id) });
      h.log?.("sketch_cmd", { command: "sketch.delete", count: picked.length });
      picked = [];
      status();
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    } finally {
      busy = false;
      draw();
    }
  }
  // where a constraint's symbol goes: beside each curve it ties, stacked when a curve has several
  function drawGlyphs(st) {
    const used = {};
    const glyphMiddle = sketchMiddle(st);
    const spotOf = (curveIdx) => {
      const k = st.curves?.[curveIdx];
      if (!k) return null;
      const n = (used[curveIdx] = (used[curveIdx] || 0) + 1) - 1;
      let at;
      if (k.type === "line") {
        const a = screenOf(k.start_at), b = screenOf(k.end_at);
        const d = [b[0] - a[0], b[1] - a[1]], L = Math.hypot(...d) || 1;
        // on the other side of the line than its dimension (dimGeom puts that away from the sketch's middle), so the
        // two never cover each other
        const inward = v2.mul(awayFrom(a, b, glyphMiddle), -1);
        at = [(a[0] + b[0]) / 2 + inward[0] * 14 + d[0] / L * 16 * n, (a[1] + b[1]) / 2 + inward[1] * 14 + d[1] / L * 16 * n];
      } else if (k.center_at) {
        const e = screenOf([k.center_at[0] - k.radius * Math.SQRT1_2, k.center_at[1] - k.radius * Math.SQRT1_2]);
        at = [e[0] - 10 - 16 * n, e[1] + 10];
      }
      return at;
    };
    const ptSpot = (pi) => { const p = st.points?.[pi]; return p ? screenOf(p.at).map((v, i) => v + (i ? -12 : 12)) : null; };
    // fixed curves carry `fixed` (not a constraint): an anchor; Fix on it again releases it (projected curves have `link`)
    (st.curves || []).forEach((k, i) => {
      if (!k.fixed || k.link) return;
      const at = spotOf(i);
      if (!at) return;
      const el = document.createElement("span");
      el.className = "sketch-glyph";
      el.textContent = "⚓";
      el.title = `${k.id} is fixed: use Fix on it again to release it`;
      el.style.left = `${at[0]}px`;
      el.style.top = `${at[1]}px`;
      dimLayer.appendChild(el);
    });
    for (const c of st.constraints || []) {
      const g = GLYPH[c.type];
      if (!g || c.value !== undefined) continue;
      const spots = c.l !== undefined ? [spotOf(c.l)]
        : c.a !== undefined ? [spotOf(c.a), spotOf(c.b)]
        : c.p !== undefined && c.q !== undefined ? [ptSpot(c.q)] : [];
      for (const at of spots) {
        if (!at) continue;
        const el = document.createElement("span");
        const bad = (st.failing || []).some((f) => (f.id || f) === c.id);
        el.className = "sketch-glyph" + (picked.some((p) => p.id === c.id) ? " picked" : "") + (bad ? " conflict" : "");
        el.textContent = g;
        el.title = `${c.name || c.type} (${c.id}): click to select, Delete removes it`;
        el.style.left = `${at[0]}px`;
        el.style.top = `${at[1]}px`;
        el.addEventListener("click", (e) => { e.stopPropagation(); togglePick("constraint", c.id, e); });
        dimLayer.appendChild(el);
      }
    }
  }

  // Modify: trim / extend the clicked piece of a curve; offset a chain to the cursor's side
  let offSel = null;      // the Offset tool's picked curve
  function offsetDistance(c, uv) {
    if (c.type === "line") {
      const a = c.start_at, b = c.end_at, dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
      return Math.abs((uv[0] - a[0]) * dy - (uv[1] - a[1]) * dx) / L;
    }
    return c.center_at ? Math.abs(Math.hypot(uv[0] - c.center_at[0], uv[1] - c.center_at[1]) - c.radius) : 0;
  }
  async function modifyClick(raw) {
    if (busy) return;
    if (tool === "offset" && offSel) {
      const typed = hud?.locked?.distance;
      const d = typed ?? offsetDistance(offSel.curve, raw.uv);
      if (!(d > 1e-6)) return;
      busy = true;
      try {
        await send("sketch.offset", { curves: [offSel.id], distance: Math.round(d * 1000) / 1000, side: raw.uv });
        h.log?.("sketch_cmd", { command: "sketch.offset", typed: typed != null });
      } catch (err) {
        h.statusEl.textContent = `Sketch: ${err.message}`;
      }
      busy = false;
      offSel = null;
      openHud();
      status();
      draw();
      return;
    }
    const ent = pickCurve(raw.screen);
    if (!ent || ent.kind !== "curve") return;
    if (tool === "offset") { offSel = ent; status(); draw(); return; }
    busy = true;
    try {
      await send(tool === "trim" ? "sketch.trim" : "sketch.extend", { curve: ent.id, at: raw.uv });
      h.log?.("sketch_cmd", { command: `sketch.${tool}` });
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    }
    busy = false;
    status();
    draw();
  }
  // Project Geometry: model edges clicked in the view come into the sketch, linked to the model
  // Project takes model edges and the origin axes (#137), shown while the tool is on; the nearer one wins
  const AXIS_DIRS = { X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1] };
  function originAxisPick(clientX, clientY) {
    const o = h.originAxisAt?.(clientX, clientY);
    if (!o || !AXIS_DIRS[o.axis]) return null;
    const d = new THREE.Vector3(...AXIS_DIRS[o.axis]);
    return { key: o.axis, axis: o.axis, dist: o.dist, pts: [d.clone().multiplyScalar(-100), d.clone().multiplyScalar(100)] };
  }
  function startProject() {
    h.revealOriginAxes?.(true);
    h.viewTools.startEdgePick(async (pick) => {
      if (busy || tool !== "project") return;
      busy = true;
      const ref = pick.alt ? { axis: pick.alt.axis }
        : { edge: pick.point.toArray ? pick.point.toArray() : pick.point, body: pick.body };
      try {
        await send("sketch.project", { refs: [ref] });
        h.log?.("sketch_cmd", { command: "sketch.project", ref: pick.alt ? `axis ${pick.alt.axis}` : "edge" });
      } catch (err) {
        h.statusEl.textContent = /already projected/.test(err.message)
          ? `Sketch: ${pick.alt ? `the ${pick.alt.axis} axis` : "this edge"} is in the sketch already`
          : `Sketch: ${err.message}`;
      }
      busy = false;
      if (!/^Sketch: /.test(h.statusEl.textContent)) status();
      draw();
    }, { alt: originAxisPick });
  }

  async function dimClick(raw) {
    const ent = pickEntity(raw.screen);
    if (ent && dimSel.length < 2 && !dimSel.some((e) => e.id === ent.id)) {
      dimSel.push(ent);
      status();
      draw();
      return;
    }
    if (!dimSel.length || busy) return;
    const params = { entities: dimSel.map((e) => e.id), text_at: raw.uv };
    // a single line: its length (SolidCraft's auto would measure horizontally when the text sits above it)
    if (dimSel.length === 1 && dimSel[0].kind === "curve" && dimSel[0].curve.type === "line") params.type = "length";
    busy = true;
    try {
      const res = await send("sketch.dimension", params);
      dimSel = [];
      const param = res.result?.param;
      lastDim = param ? { param, params } : null;
      h.log?.("sketch_cmd", { command: "sketch.dimension", type: params.type || "auto" });
      status();
      busy = false;
      draw();
      if (param) openDimEditor(param);
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
      dimSel = [];
      busy = false;
      draw();
    }
  }

  function draw() {
    clearGroup();
    if (!active) { h.renderScene(); return; }
    const st = active.state || {};
    addLine([[0, 0], [25, 0]].map((p) => p), COLORS.axisX);
    addLine([[0, 0], [0, 25]], COLORS.axisY);
    for (const c of st.curves || []) {
      const color = c.link ? colorProjected() : c.fully_constrained ? colorFixed() : COLORS.free;
      if (c.type === "line") addLine([c.start_at, c.end_at], color, c.construction);
      else if (c.type === "circle") addLine(circlePts(c.center_at, c.radius), color, c.construction);
      else if (c.type === "arc" && c.center_at && c.start_at && c.end_at) {
        const a0 = Math.atan2(c.start_at[1] - c.center_at[1], c.start_at[0] - c.center_at[0]);
        let a1 = Math.atan2(c.end_at[1] - c.center_at[1], c.end_at[0] - c.center_at[0]);
        if (a1 <= a0) a1 += Math.PI * 2;
        addLine(circlePts(c.center_at, c.radius ?? Math.hypot(c.start_at[0] - c.center_at[0], c.start_at[1] - c.center_at[1]), a0, a1), color, c.construction);
      }
    }
    const pts = (st.points || []).filter((p) => p.id !== "origin");
    addPoints(pts.filter((p) => !p.link && !p.fully_constrained).map((p) => p.at), COLORS.free, 5);
    addPoints(pts.filter((p) => !p.link && p.fully_constrained).map((p) => p.at), colorFixed(), 5);
    addPoints(pts.filter((p) => p.link).map((p) => p.at), colorProjected(), 5);
    addPoints([[0, 0]], COLORS.axisX, 7);
    const prev = shapePreview();
    if (prev) addLine(prev, COLORS.preview);
    if (tool === "offset" && offSel && cursor) {
      const c = offSel.curve, d = hud?.locked?.distance ?? offsetDistance(c, cursor.at);
      if (c.type === "line") {
        const a = c.start_at, b = c.end_at, L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
        let n = [-(b[1] - a[1]) / L, (b[0] - a[0]) / L];
        if ((cursor.at[0] - a[0]) * n[0] + (cursor.at[1] - a[1]) * n[1] < 0) n = [-n[0], -n[1]];
        addLine([[a[0] + n[0] * d, a[1] + n[1] * d], [b[0] + n[0] * d, b[1] + n[1] * d]], COLORS.preview, true);
      } else if (c.center_at) {
        const out = Math.hypot(cursor.at[0] - c.center_at[0], cursor.at[1] - c.center_at[1]) > c.radius;
        addLine(circlePts(c.center_at, Math.max(0.01, c.radius + (out ? d : -d))), COLORS.preview, true);
      }
    }
    const drawing = tool && !["dimension", "trim", "extend", "offset", "project"].includes(tool) && !tool.startsWith("con:");
    if (drawing && cursor?.snap?.kind === "align") for (const r of cursor.snap.from) addLine([r, cursor.at], COLORS.align, true);
    if (drawing && cursor) addPoints([cursor.at], COLORS.preview, 7);
    const marks = tool === "dimension" ? [...dimSel, ...(dimHover ? [dimHover] : [])]
      : tool?.startsWith("con:") ? [...conSel, ...(dimHover ? [dimHover] : [])]
      : ["trim", "extend", "offset"].includes(tool) ? [...(offSel ? [offSel] : []), ...(dimHover?.kind === "curve" ? [dimHover] : [])]
      : !tool ? [...picked.filter((p) => p.ent).map((p) => p.ent), ...(dimHover ? [dimHover] : [])] : [];
    {
      for (const e of marks) {
        if (e.kind === "point") addPoints([e.at], COLORS.preview, 9);
        else if (e.curve.type === "line") addLine([e.curve.start_at, e.curve.end_at], COLORS.preview);
        else if (e.curve.center_at) addLine(circlePts(e.curve.center_at, e.curve.radius), COLORS.preview);
      }
    }
    h.renderScene();
    placeSnapMarker();
    placeHud();
    drawDims();
  }

  function placeSnapMarker() {
    const s = cursor?.snap;
    if (!active || !tool || ["dimension", "trim", "extend", "offset", "project"].includes(tool) || tool.startsWith("con:") || !s || !["point", "mid", "horizontal", "vertical"].includes(s.kind)) { snapEl.hidden = true; return; }
    const [x, y] = screenOf(cursor.at);
    snapEl.hidden = false;
    snapEl.dataset.kind = s.kind;
    snapEl.textContent = { point: "", mid: "", horizontal: "H", vertical: "V" }[s.kind];
    snapEl.style.left = `${x}px`;
    snapEl.style.top = `${y}px`;
  }

  // --- input boxes at the cursor (Tab: next box, a typed value locks; Enter: place with the locked values) -----
  function openHud() {
    closeHud();
    const fields = HUD_FIELDS[tool];
    if (!fields) return;
    const el = document.createElement("div");
    el.className = "sketch-hud";
    const inputs = {};
    for (const [role, label, unit] of fields) {
      const lab = document.createElement("label");
      lab.innerHTML = `<span>${label}</span>`;
      const inp = document.createElement("input");
      inp.type = "text";
      inp.inputMode = "decimal";
      inp.autocomplete = "off";
      inp.dataset.role = role;
      inp.setAttribute("aria-label", `${label} (${unit})`);
      inp.addEventListener("input", () => {
        const v = num(inp.value);
        if (v !== null && v > 0 || (role === "angle" && v !== null)) hud.locked[role] = v;
        else delete hud.locked[role];
        inp.classList.toggle("locked", role in hud.locked);
        draw();
      });
      lab.appendChild(inp);
      const u = document.createElement("span");
      u.className = "unit";
      u.textContent = unit;
      lab.appendChild(u);
      el.appendChild(lab);
      inputs[role] = inp;
    }
    h.viewportEl.appendChild(el);
    hud = { el, inputs, locked: {}, order: fields.map((f) => f[0]) };
  }
  function closeHud() {
    if (hud) hud.el.remove();
    hud = null;
  }
  function placeHud() {
    if (!hud) return;
    if (tool === "offset") {
      if (!offSel || !cursor) { hud.el.hidden = true; return; }
      hud.el.hidden = false;
      const [ox, oy] = screenOf(cursor.at);
      hud.el.style.left = `${ox + 18}px`;
      hud.el.style.top = `${oy + 14}px`;
      const inp = hud.inputs.distance;
      if (!("distance" in hud.locked) && document.activeElement !== inp) inp.value = fmt(Math.round(offsetDistance(offSel.curve, cursor.at) * 100) / 100);
      return;
    }
    if (!clicks.length || !cursor) { hud.el.hidden = true; return; }
    hud.el.hidden = false;
    const [x, y] = screenOf(cursor.at);
    hud.el.style.left = `${x + 18}px`;
    hud.el.style.top = `${y + 14}px`;
    // show the live values in the boxes that are not locked
    const a = clicks[0].at, b = previewEnd();
    const live = {
      length: Math.hypot(b[0] - a[0], b[1] - a[1]),
      angle: Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI,
      width: Math.abs(b[0] - a[0]),
      height: Math.abs(b[1] - a[1]),
      diameter: 2 * Math.hypot(b[0] - a[0], b[1] - a[1]),
    };
    for (const [role, inp] of Object.entries(hud.inputs)) {
      if (!(role in hud.locked) && document.activeElement !== inp) inp.value = fmt(live[role]);
    }
  }
  function focusHud(next = true) {
    if (!hud) return false;
    const order = hud.order;
    const cur = order.indexOf(document.activeElement?.dataset?.role);
    const i = cur < 0 ? 0 : (cur + (next ? 1 : order.length - 1)) % order.length;
    const inp = hud.inputs[order[i]];
    inp.focus();
    inp.select();
    return true;
  }

  // --- commands -----------------------------------------------------------------------------------------------
  async function send(command, params, extra = {}) {
    const res = await h.post("api/sketch/cmd", { command, params, ...extra });
    active.state = res.state;
    return res;
  }
  // a click held at a line's midpoint keeps it there (SolidCraft connects equal points by itself)
  async function holdMidpoints(snaps) {
    for (const { at, line } of snaps) {
      const p = (active.state.points || []).find((q) => q.id !== "origin" && !q.link && Math.hypot(q.at[0] - at[0], q.at[1] - at[1]) < 1e-6
        && !String(q.id).startsWith(line + "."));
      if (p) {
        try { await send("sketch.constraint.midpoint", { point: p.id, line }); } catch (_) { /* drawn anyway */ }
      }
    }
  }

  async function place() {
    if (busy || !clicks.length) return;
    const a = clicks[0].at, b = previewEnd();
    const L = hud?.locked || {};
    let command, params;
    if (tool === "line") {
      command = "sketch.line"; params = { points: [a, b], infer: true, connect: true };
    } else if (tool === "rectangle") {
      if (Math.abs(b[0] - a[0]) < 1e-6 || Math.abs(b[1] - a[1]) < 1e-6) return;
      command = "sketch.rectangle.two_point"; params = { p0: a, p1: b, connect: true };
    } else if (tool === "circle") {
      const r = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (r < 1e-6) return;
      command = "sketch.circle.center"; params = { center: a, radius: r, connect: true };
    } else if (tool === "arc") {
      if (clicks.length < 2 || !arcThrough(a, clicks[1].at, b)) return;
      command = "sketch.arc.three_point"; params = { start: a, end: clicks[1].at, through: b, connect: true };
    } else return;
    if (tool === "line" && Math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6) return;
    const dims = Object.fromEntries(Object.entries(L).filter(([role]) => (HUD_FIELDS[tool] || []).some((f) => f[0] === role)));
    busy = true;
    try {
      const lt = lineType === "normal" ? {} : { line_type: lineType };
      if (Object.keys(dims).length) await send("sketch.draw.dimensioned", { command, params, dimensions: dims }, lt);
      else await send(command, params, lt);
      const mids = [clicks[0], { at: b, snap: cursor?.snap }].filter((c) => c.snap?.kind === "mid").map((c) => ({ at: c.at, line: c.snap.line }));
      await holdMidpoints(mids);
      h.log?.("sketch_cmd", { command, dims: Object.keys(dims) });
      // a line goes on from its end point (chain) until Esc; other shapes start over
      clicks = tool === "line" ? [{ at: b, snap: { kind: "point" } }] : [];
      openHud();
      status();
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    } finally {
      busy = false;
      draw();
    }
  }

  // --- tools and events ---------------------------------------------------------------------------------------
  async function setTool(next) {
    if (boxDrag) {
      if (boxDrag.pointerId != null) { try { canvas.releasePointerCapture(boxDrag.pointerId); } catch (_) {} }
      boxDrag = null;
      boxEl.hidden = true;
    }
    if (tool === "project" && next !== "project") { h.viewTools.stopEdgePick(); h.revealOriginAxes?.(false); }
    if (next?.startsWith("con:") && picked.length > 0) {
      const applied = await applyConstraintToPicked(next.slice(4));
      if (applied) return;
    }
    tool = next;
    clicks = [];
    offSel = null;
    if (tool === "project") startProject();
    dimSel = [];
    conSel = [];
    picked = [];
    dimHover = null;
    closeHud();
    if (tool) openHud();
    dimLayer.classList.toggle("tool-active", Boolean(tool));
    document.querySelectorAll("[data-sketch-tool]").forEach((b) => b.classList.toggle("active", b.dataset.sketchTool === tool));
    status();
    draw();
  }
  function status() {
    if (!active) return;
    const st = active.state || {};
    const dof = !(st.curves || []).length ? "empty" : st.fully_constrained ? "fully constrained" : `${st.dof ?? "?"} degrees of freedom`;
    const hint = {
      line: clicks.length ? "Click the end point, type a length (Tab: angle), Esc ends the chain" : "Click the start point",
      rectangle: clicks.length ? "Click the opposite corner, or type width and height" : "Click the first corner",
      circle: clicks.length ? "Click a point on the circle, or type the diameter" : "Click the centre",
      dimension: dimSel.length === 1 ? "Click where the dimension goes, or a second point or line"
        : dimSel.length ? "Click where the dimension goes" : "Click a line, a circle or two points; double-click a dimension to change it",
      arc: clicks.length === 1 ? "Click the end point" : clicks.length ? "Click a point the arc passes through" : "Click the start point",
      trim: "Click the piece of a curve to remove (up to the nearest crossings)",
      extend: "Click near the end of a line or arc to extend it to the next curve",
      offset: offSel ? "Click the side and distance, or type the distance and press Enter" : "Click a curve (its connected chain is offset)",
      project: "Click model edges or an origin axis to bring them into the sketch (they follow the model)",
    }[tool] || (tool === "con:fix" ? "Click a point or curve to hold it where it is"
      : tool === "con:coincident" ? "Click two points, or a point and a curve, to join them"
      : tool?.startsWith("con:") ? (["con:horizontal", "con:vertical"].includes(tool)
      ? "Click a line, or two points" : "Click two curves") + ` to make them ${CON[tool.slice(4)].label.toLowerCase()}`
      : picked.length ? `${picked.length} selected · Delete removes, X construction, Esc clears`
      : "Draw: L R C A · Dimension D · Trim T, Offset O, Project P · X construction · click to select · Enter finishes the sketch");
    const failing = st.failing || [];
    const conflict = failing.length || (st.status && st.status !== "solved")
      ? ` · ⚠ ${st.status && st.status !== "solved" ? st.status.replace(/_/g, " ") : "conflict"}${failing.length ? `: ${failing.map((f) => f.id || f.name || f).join(", ")}` : ""}` : "";
    const mode = lineType === "construction" ? " · Construction mode: new curves are construction geometry" : "";
    h.statusEl.textContent = `${active.name} · ${dof}${conflict}${mode} · ${hint}`;
  }

  // Line type (#138), as SolidCraft's palette: with curves selected it changes them (one undo step), with
  // nothing selected it is the drawing mode for new curves. X toggles construction the same way.
  function showLineType() {
    document.querySelectorAll("[data-sketch-linetype]").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.sketchLinetype === lineType));
      b.classList.toggle("active", b.dataset.sketchLinetype === lineType && lineType !== "normal");
    });
  }
  async function setLineType(kind) {
    if (!active || busy) return;
    const curves = picked.filter((p) => p.kind === "curve").map((p) => p.id);
    if (!curves.length) {
      lineType = kind;
      showLineType();
      h.log?.("sketch_linetype", { mode: kind });
      status();
      return;
    }
    busy = true;
    try {
      await send("sketch.construction", { curves, value: kind === "construction" });
      h.log?.("sketch_cmd", { command: "sketch.construction", value: kind === "construction", count: curves.length });
      status();
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    } finally {
      busy = false;
      draw();
    }
  }
  function toggleConstruction() {
    const curves = picked.filter((p) => p.kind === "curve").map((p) => p.id);
    if (!curves.length) return setLineType(lineType === "construction" ? "normal" : "construction");
    const all = curves.every((id) => (active.state?.curves || []).find((c) => c.id === id)?.construction);
    return setLineType(all ? "normal" : "construction");
  }

  function onMove(ev) {
    if (!active) return;
    const raw = planeAt(ev);
    if (!raw) return;
    if (!tool && boxDrag) {
      const dx = ev.clientX - boxDrag.startClient[0];
      const dy = ev.clientY - boxDrag.startClient[1];
      if (!boxDrag.active && Math.hypot(dx, dy) >= DRAG_THRESHOLD_PX) {
        boxDrag.active = true;
      }
      if (boxDrag.active) {
        const minX = Math.min(boxDrag.startScreen[0], raw.screen[0]);
        const maxX = Math.max(boxDrag.startScreen[0], raw.screen[0]);
        const minY = Math.min(boxDrag.startScreen[1], raw.screen[1]);
        const maxY = Math.max(boxDrag.startScreen[1], raw.screen[1]);
        const crossing = raw.screen[0] < boxDrag.startScreen[0];
        boxEl.hidden = false;
        boxEl.className = `sketch-box-select ${crossing ? "crossing" : "window"}`;
        boxEl.style.left = `${minX}px`;
        boxEl.style.top = `${minY}px`;
        boxEl.style.width = `${maxX - minX}px`;
        boxEl.style.height = `${maxY - minY}px`;
        return;
      }
    }
    if (["trim", "extend", "offset"].includes(tool)) {
      cursor = { at: raw.uv, snap: null };
      dimHover = pickCurve(raw.screen);
    } else if (tool === "dimension" || !tool || tool.startsWith("con:") || tool === "project") {
      cursor = { at: raw.uv, snap: null };
      dimHover = pickEntity(raw.screen);
    } else {
      cursor = snapPoint(raw, ev);
    }
    draw();
  }
  function onDown(ev) {
    if (!active || ev.button !== 0) return;
    ev.preventDefault();
    const raw = planeAt(ev);
    if (!raw) return;
    if (!tool) {
      canvas.setPointerCapture?.(ev.pointerId);
      boxDrag = {
        startScreen: raw.screen,
        startClient: [ev.clientX, ev.clientY],
        shift: ev.shiftKey,
        ctrl: ev.ctrlKey || ev.metaKey,
        raw,
        active: false,
        pointerId: ev.pointerId,
      };
      return;
    }
    if (tool === "dimension") { dimClick(raw); return; }
    if (tool.startsWith("con:")) { conClick(raw); return; }
    if (tool === "project") return;  // the view's edge pick answers (startProject)
    if (["trim", "extend", "offset"].includes(tool)) { modifyClick(raw); return; }
    cursor = snapPoint(raw, ev);
    if (!clicks.length || (tool === "arc" && clicks.length === 1)) {
      clicks = [...clicks, { at: cursor.at, snap: cursor.snap }];
      status();
      draw();
    } else {
      place();
    }
  }
  function onUp(ev) {
    if (!active || ev.button !== 0) return;
    if (boxDrag) {
      if (boxDrag.pointerId != null) {
        try { canvas.releasePointerCapture(boxDrag.pointerId); } catch (_) {}
      }
      boxEl.hidden = true;
      const raw = planeAt(ev) || boxDrag.raw;
      const wasActive = boxDrag.active;
      const startScr = boxDrag.startScreen;
      const savedRaw = boxDrag.raw;
      boxDrag = null;
      if (wasActive && raw) {
        const box = boxFromDrag(startScr, raw.screen);
        applyBoxSelect(box, ev);
      } else {
        selectClick(raw || savedRaw, ev);
      }
    }
  }
  function onCancel() {
    if (boxDrag) {
      if (boxDrag.pointerId != null) { try { canvas.releasePointerCapture(boxDrag.pointerId); } catch (_) {} }
      boxDrag = null;
      boxEl.hidden = true;
      status();
      draw();
    }
  }
  function onContext(ev) {
    if (!active) return;
    ev.preventDefault();
  }
  function onKey(ev) {
    if (!active) return;
    const inHud = hud && hud.el.contains(ev.target);
    const other = !inHud && ev.target?.closest?.("input, textarea, select, [contenteditable]");
    if (other || document.querySelector("dialog[open]")) return;
    const k = ev.key;
    const mod = ev.ctrlKey || ev.metaKey;
    let handled = true;
    if (k === "Escape") {
      if (boxDrag) {
        if (boxDrag.pointerId != null) { try { canvas.releasePointerCapture(boxDrag.pointerId); } catch (_) {} }
        boxDrag = null;
        boxEl.hidden = true;
        status();
        draw();
      } else if (clicks.length || dimSel.length || conSel.length || offSel) { clicks = []; dimSel = []; conSel = []; offSel = null; openHud(); status(); draw(); }
      else if (!tool && picked.length) { picked = []; status(); draw(); }
      else if (tool) setTool(null);
    } else if (k === "Tab" && tool && clicks.length) {
      focusHud(!ev.shiftKey);
    } else if (k === "Enter" && tool === "offset" && offSel && cursor) {
      modifyClick({ uv: cursor.at, screen: screenOf(cursor.at) });
    } else if (k === "Enter") {
      if (tool && clicks.length) place();
      else if (!tool) finish();
    } else if (inHud) {
      handled = false;
    } else if ((k === "Delete" || k === "Backspace") && !tool && picked.length) {
      deletePicked();
    } else if (mod && (k === "z" || k === "Z") && !ev.shiftKey) {
      undo();
    } else if (!mod && !ev.altKey && (k === "x" || k === "X") && !tool) {
      toggleConstruction();
    } else if (!mod && !ev.altKey && /^[lrcdatop]$/i.test(k)) {
      setTool({ l: "line", r: "rectangle", c: "circle", d: "dimension", a: "arc", t: "trim", o: "offset", p: "project" }[k.toLowerCase()]);
    } else if (!mod && !ev.altKey && /^[0-9.,-]$/.test(k) && tool && (clicks.length || offSel) && hud) {
      // typing a number goes straight into the first box, as Dynamic Input does
      const inp = hud.inputs[hud.order[0]];
      inp.focus();
      inp.value = "";
      handled = false;
    } else if (mod || ev.altKey || k.length === 1) {
      // keep the 3D shortcuts (S, E, F, H, Ctrl+Y ...) away from the model while sketching
      handled = k.length === 1 || mod;
    } else {
      handled = false;
    }
    if (handled) {
      ev.preventDefault();
      ev.stopImmediatePropagation();
    }
  }

  async function undo() {
    if (busy) return;
    busy = true;
    try {
      const res = await h.post("api/sketch/undo", {});
      active.state = res.state;
      clicks = [];
      if (tool) openHud();
      status();
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    } finally {
      busy = false;
      draw();
    }
  }

  // --- entering and leaving -----------------------------------------------------------------------------------
  function enter(res) {
    active = { name: res.sketch, editing: res.editing, state: res.state, frame: res.state.plane };
    lineType = "normal";  // a sketch starts normal, as in SolidCraft
    showLineType();
    savedView = { pos: h.camera.position.clone(), up: h.camera.up.clone(), target: h.controls.target.clone() };
    savedButtons = { ...h.controls.mouseButtons };
    // left draws; the middle button pans, the right one turns the view
    h.controls.mouseButtons = { LEFT: null, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.ROTATE };
    if (h.controls.touches) h.controls.touches.ONE = null;
    h.viewTools.stopEdgePick();
    h.lookAlong(active.frame);
    h.activateTab("sketch");
    document.body.classList.add("sketching");
    h.onMode?.(true);
    // keys go to the sketcher (L, R, C, D, A, Esc, Enter), not to a frame or a ribbon button that had the focus
    if (canvas.tabIndex < 0 && !canvas.hasAttribute("tabindex")) canvas.tabIndex = -1;
    canvas.focus({ preventScroll: true });
    const hint = document.querySelector(".viewport-hint");
    if (hint) { savedHint = hint.textContent; hint.textContent = "Left: draw · Middle: pan · Right: rotate · Wheel: zoom · Ctrl: no snapping"; }
    setButtons(true);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerdown", onDown);
    canvas.addEventListener("pointerup", onUp);
    canvas.addEventListener("pointercancel", onCancel);
    window.addEventListener("pointerup", onUp);
    canvas.addEventListener("contextmenu", onContext);
    h.controls.addEventListener("change", draw);
    setTool(null);
    h.log?.("sketch_begin", { sketch: active.name, editing: active.editing });
  }
  function leave() {
    h.viewTools.stopEdgePick();
    if (tool === "project") h.revealOriginAxes?.(false);
    canvas.removeEventListener("pointermove", onMove);
    canvas.removeEventListener("pointerdown", onDown);
    canvas.removeEventListener("pointerup", onUp);
    canvas.removeEventListener("pointercancel", onCancel);
    window.removeEventListener("pointerup", onUp);
    canvas.removeEventListener("contextmenu", onContext);
    h.controls.removeEventListener("change", draw);
    if (boxDrag?.pointerId != null) { try { canvas.releasePointerCapture(boxDrag.pointerId); } catch (_) {} }
    boxDrag = null;
    boxEl.hidden = true;
    if (savedButtons) h.controls.mouseButtons = savedButtons;
    if (h.controls.touches) h.controls.touches.ONE = THREE.TOUCH.ROTATE;
    if (savedView) {
      h.camera.position.copy(savedView.pos);
      h.camera.up.copy(savedView.up);
      h.controls.target.copy(savedView.target);
      h.camera.lookAt(savedView.target);
      h.controls.update();
    }
    active = null; tool = null; clicks = []; cursor = null;
    dimLayer.classList.remove("tool-active");
    closeHud();
    closeDimEditor();
    dimLayer.textContent = "";
    snapEl.hidden = true;
    document.body.classList.remove("sketching");
    h.onMode?.(false);
    const hint = document.querySelector(".viewport-hint");
    if (hint && savedHint !== null) hint.textContent = savedHint;
    savedHint = null;
    setButtons(false);
    h.activateTab("3d-model");
    draw();
  }
  function setButtons(on) {
    document.querySelectorAll("[data-sketch-tool], [data-sketch-action], [data-sketch-linetype]").forEach((b) => { b.disabled = !on; });
  }

  // Starting a sketch can take a while (in the live demo SolidCraft loads first) and may fail: say so over the view,
  // where it is seen on a phone too, not only in the status bar at the foot of the page
  async function begin(body) {
    const note = document.createElement("div");
    note.className = "sketch-note";
    note.setAttribute("role", "status");
    note.textContent = "Starting the sketch…";
    h.viewportEl.appendChild(note);
    const follow = new MutationObserver(() => { if (h.statusEl.textContent) note.textContent = h.statusEl.textContent; });
    follow.observe(h.statusEl, { childList: true, characterData: true, subtree: true });
    try {
      const res = await h.post("api/sketch/begin", body);
      follow.disconnect();
      note.remove();
      enter(res);
    } catch (err) {
      follow.disconnect();
      h.statusEl.textContent = `Sketch: ${err.message}`;
      note.textContent = `Sketch: ${err.message}`;
      note.classList.add("error");
      setTimeout(() => note.remove(), 8000);
    }
  }

  // Create 2D Sketch: click a flat face, or choose an origin plane in the bar over the view
  function start() {
    if (active || choosing) return;
    const bar = document.createElement("div");
    bar.className = "sketch-plane-bar";
    bar.innerHTML = `<span>New sketch: click a plane or a flat face</span>
      <button type="button" data-plane="XY">XY</button><button type="button" data-plane="XZ">XZ</button>
      <button type="button" data-plane="YZ">YZ</button>
      <label class="sketch-autoproject" title="Automatically project face edges into the sketch (Inventor: Autoproject edges for sketch creation)"><input type="checkbox" data-autoproject${autoProject ? " checked" : ""}> Project edges</label>
      <button type="button" data-plane="">Cancel</button>`;
    h.viewportEl.appendChild(bar);
    const apBox = bar.querySelector("[data-autoproject]");
    apBox?.addEventListener("change", () => {
      autoProject = apBox.checked;
      h.post("api/sketch/auto_project", { value: autoProject }).catch(() => {});
    });
    // the origin planes (also hidden ones, as SolidCraft brings them back for this) are clicked directly
    h.revealOriginPlanes?.(true);
    const overPlane = (ev) => h.hoverOriginPlane?.(h.originPlaneAt?.(ev.clientX, ev.clientY) || null);
    const downPlane = (ev) => {
      if (ev.button !== 0) return;
      const name = h.originPlaneAt?.(ev.clientX, ev.clientY);
      if (!name) return;
      ev.stopImmediatePropagation();
      done();
      begin({ plane: name });
    };
    canvas.addEventListener("pointermove", overPlane);
    canvas.addEventListener("pointerdown", downPlane, true);
    const done = () => {
      h.viewTools.stopEdgePick();
      canvas.removeEventListener("pointermove", overPlane);
      canvas.removeEventListener("pointerdown", downPlane, true);
      h.revealOriginPlanes?.(false);
      bar.remove();
      window.removeEventListener("keydown", esc, true);
      choosing = null;
    };
    const esc = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopImmediatePropagation(); done(); h.statusEl.textContent = "Sketch cancelled"; } };
    window.addEventListener("keydown", esc, true);
    bar.querySelectorAll("[data-plane]").forEach((b) => b.addEventListener("click", () => {
      const p = b.dataset.plane;
      done();
      if (p) begin({ plane: p });
    }));
    h.viewTools.startFacePick((pick) => {
      if (!pick.planar) { h.statusEl.textContent = "That face is not flat: click a flat face or choose a plane"; return; }
      done();
      // the face hit as well: a tap near an edge gives a point on two faces, which SolidCraft refuses as ambiguous
      const face = { face: pick.point.toArray().map((c) => +c.toFixed(4)) };
      if (pick.body && Number.isInteger(pick.face)) Object.assign(face, { body: pick.body, index: pick.face });
      begin({ plane: face, project_edges: autoProject });
    });
    choosing = bar;
    h.statusEl.textContent = "New sketch: click an origin plane or a flat face, or choose XY, XZ or YZ";
  }

  async function finish() {
    if (!active || busy) return;
    busy = true;
    try {
      const res = await h.post("api/sketch/finish", {});
      leave();
      h.statusEl.textContent = `${res.done}`;
      await h.reload();
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
      // the server cancels a sketch it cannot finish; follow it
      const st = await h.get("api/sketch/state").catch(() => null);
      if (st && !st.active) { leave(); await h.reload(); }
    } finally {
      busy = false;
    }
  }
  async function cancel() {
    if (!active || busy) return;
    busy = true;
    try {
      await h.post("api/sketch/cancel", {});
    } catch (err) {
      h.statusEl.textContent = `Sketch: ${err.message}`;
    } finally {
      busy = false;
      leave();
      await h.reload();
    }
  }

  // ribbon buttons
  document.querySelectorAll("[data-sketch-tool]").forEach((b) => b.addEventListener("click", () => {
    if (active) setTool(tool === b.dataset.sketchTool ? null : b.dataset.sketchTool);
  }));
  document.querySelectorAll("[data-sketch-linetype]").forEach((b) => b.addEventListener("click", () => {
    setLineType(b.dataset.sketchLinetype);
  }));
  document.querySelectorAll("[data-sketch-action]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.sketchAction === "finish") finish();
    else if (b.dataset.sketchAction === "cancel") cancel();
  }));
  window.addEventListener("keydown", onKey, true);
  setButtons(false);

  // a sketch left open (page reloaded while sketching) is picked up again
  if (h.resume !== false) h.get("api/sketch/state").then((st) => {
    if (st && typeof st.auto_project === "boolean") autoProject = st.auto_project;
    if (st && st.active) enter(st);
  }).catch(() => {});

  return {
    start,
    startOn: (plane) => { if (!active && !choosing) begin({ plane }); },
    edit: (name) => { if (!active) begin({ edit: name }); },
    isActive: () => !!active || !!choosing,
    isOpen: () => !!active,
    finish,
    cancel,
  };
}
