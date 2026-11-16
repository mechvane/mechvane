// Sketch geometry for drawing outside the sketch environment: curves and closed regions (profiles) from
// /api/sketches (sketch_shapes() in mechvane/ui/server.py, sketches() in demo_kernel.js) as polylines in sketch
// coordinates, turned into world points on the sketch plane, and a point-in-profile test for picking.
import * as THREE from "three";

const TAU = Math.PI * 2;

// one curve as points along it, from its start to its end (a circle closes on itself)
export function curvePoints(c, n = 64) {
  if (c.type === "line" && c.start_at && c.end_at) return [c.start_at, c.end_at];
  if (!c.center_at || !c.radius) return [];
  const [cx, cy] = c.center_at, r = c.radius;
  let a0 = 0, a1 = TAU;
  if (c.type === "arc" && c.start_at && c.end_at) {
    a0 = Math.atan2(c.start_at[1] - cy, c.start_at[0] - cx);
    a1 = Math.atan2(c.end_at[1] - cy, c.end_at[0] - cx);
    if (a1 <= a0) a1 += TAU;  // counter-clockwise from start to end
  }
  const k = Math.max(8, Math.ceil(((a1 - a0) / TAU) * n));
  return Array.from({ length: k + 1 }, (_, i) => {
    const a = a0 + ((a1 - a0) * i) / k;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
}

// a closed loop of curve ids as one polygon: curves chained in topological order and turned so that each
// starts where the last one ended (SolidCraft inspect profiles return curves in arbitrary order)
export function loopPoints(ids, byId) {
  const curves = (ids || []).map((id) => byId[id]).filter(Boolean).map((c) => curvePoints(c)).filter((pts) => pts.length > 0);
  if (!curves.length) return [];
  const remaining = curves.slice(1);
  let out = curves[0].slice();
  while (remaining.length) {
    const last = out[out.length - 1];
    let bestIdx = 0, bestDist = Infinity, bestRev = false;
    for (let i = 0; i < remaining.length; i++) {
      const pts = remaining[i];
      const d0 = Math.hypot(pts[0][0] - last[0], pts[0][1] - last[1]);
      const d1 = Math.hypot(pts[pts.length - 1][0] - last[0], pts[pts.length - 1][1] - last[1]);
      if (d0 < bestDist) { bestDist = d0; bestIdx = i; bestRev = false; }
      if (d1 < bestDist) { bestDist = d1; bestIdx = i; bestRev = true; }
    }
    let nextPts = remaining.splice(bestIdx, 1)[0];
    if (bestRev) nextPts = nextPts.slice().reverse();
    if (nextPts.length > 1 && Math.hypot(nextPts[0][0] - last[0], nextPts[0][1] - last[1]) < 1e-3) {
      nextPts = nextPts.slice(1);
    }
    out.push(...nextPts);
  }
  // drop duplicate closing point so Three.js Shape doesn't create a degenerate edge
  if (out.length > 2) {
    const first = out[0], last = out[out.length - 1];
    if (Math.hypot(last[0] - first[0], last[1] - first[1]) < 1e-3) out.pop();
  }
  return out;
}

// the sketch's closed regions: [{index, area, outer: [[u, v]...], holes: [[[u, v]...]...]}]
export function profileShapes(sketch) {
  const byId = Object.fromEntries((sketch.curves || []).map((c) => [c.id, c]));
  return (sketch.profiles || []).map((p) => ({
    index: p.index, area: p.area,
    outer: loopPoints(p.curves || [], byId),
    holes: (p.hole_loops || []).map((ids) => loopPoints(ids, byId)),
  }));
}

function inPolygon(pt, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

// the profile under a point (sketch coordinates): inside the outline and in none of its holes; the smallest
// one when regions nest (a circle inside a rectangle is its own region)
export function profileAt(shapes, pt) {
  const hits = shapes.filter((s) => s.outer.length > 2 && inPolygon(pt, s.outer) && !s.holes.some((h) => h.length > 2 && inPolygon(pt, h)));
  hits.sort((a, b) => a.area - b.area);
  return hits[0] || null;
}

// the sketch line (including construction lines) nearest to a point in sketch coordinates, within maxDist
export function sketchLineAt(sketch, pt, maxDist = Infinity) {
  if (!sketch || !Array.isArray(pt)) return null;
  let best = null, bestD = maxDist;
  for (const c of sketch.curves || []) {
    if (c.type !== "line" || !Array.isArray(c.start_at) || !Array.isArray(c.end_at)) continue;
    const [ax, ay] = c.start_at, [bx, by] = c.end_at;
    const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
    if (l2 < 1e-12) continue;
    const t = Math.max(0, Math.min(1, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / l2));
    const d = Math.hypot(pt[0] - (ax + t * dx), pt[1] - (ay + t * dy));
    if (d <= bestD) {
      bestD = d;
      best = { id: c.id, start: c.start_at, end: c.end_at, construction: !!c.construction, dist: d };
    }
  }
  return best;
}

// sketch coordinates to world points on the sketch's plane
export function toWorld(plane, pts) {
  const o = new THREE.Vector3(...plane.origin), x = new THREE.Vector3(...plane.x_dir), y = new THREE.Vector3(...plane.y_dir);
  return pts.map(([u, v]) => o.clone().addScaledVector(x, u).addScaledVector(y, v));
}

// a filled region as a mesh on the plane (outline with holes), for showing which profiles are picked
export function profileMesh(plane, shape, color, opacity) {
  const s = new THREE.Shape(shape.outer.map(([u, v]) => new THREE.Vector2(u, v)));
  for (const h of shape.holes) s.holes.push(new THREE.Path(h.map(([u, v]) => new THREE.Vector2(u, v))));
  const geom = new THREE.ShapeGeometry(s, 24);
  const o = new THREE.Vector3(...plane.origin), x = new THREE.Vector3(...plane.x_dir), y = new THREE.Vector3(...plane.y_dir);
  const z = new THREE.Vector3().crossVectors(x, y).normalize();
  geom.applyMatrix4(new THREE.Matrix4().makeBasis(x, y, z).setPosition(o));
  const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity, side: THREE.DoubleSide, depthTest: false, depthWrite: false });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.renderOrder = 9;
  return mesh;
}

// --- Window and crossing box selection (SolidCraft crates/ui-egui/src/selection.rs BoxSel) ---
// Dragged left-to-right: window selection (only items wholly enclosed).
// Dragged right-to-left: crossing selection (items touching or inside).

// Build a 2D bounding box from drag start and end points [x, y]
export function boxFromDrag(start, end) {
  return {
    minX: Math.min(start[0], end[0]),
    maxX: Math.max(start[0], end[0]),
    minY: Math.min(start[1], end[1]),
    maxY: Math.max(start[1], end[1]),
    crossing: end[0] < start[0],
  };
}

// Whether point pt [x, y] lies inside box
export function boxTakesPoint(box, pt) {
  return pt[0] >= box.minX && pt[0] <= box.maxX && pt[1] >= box.minY && pt[1] <= box.maxY;
}

// Do 2D line segments p-q and r-s cross or touch? (SolidCraft selection.rs segments_cross with touch)
export function segmentsCross(p, q, r, s) {
  const o = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const d1 = o(r, s, p), d2 = o(r, s, q);
  const d3 = o(p, q, r), d4 = o(p, q, s);
  if ((d1 > 0) !== (d2 > 0) && (d3 > 0) !== (d4 > 0)) return true;
  const onSeg = (a, b, c) =>
    c[0] >= Math.min(a[0], b[0]) - 1e-9 && c[0] <= Math.max(a[0], b[0]) + 1e-9 &&
    c[1] >= Math.min(a[1], b[1]) - 1e-9 && c[1] <= Math.max(a[1], b[1]) + 1e-9;
  if (Math.abs(d1) < 1e-9 && onSeg(r, s, p)) return true;
  if (Math.abs(d2) < 1e-9 && onSeg(r, s, q)) return true;
  if (Math.abs(d3) < 1e-9 && onSeg(p, q, r)) return true;
  if (Math.abs(d4) < 1e-9 && onSeg(p, q, s)) return true;
  return false;
}

// Does segment a-b cross the rectangle boundary or lie inside it? (SolidCraft selection.rs segment_hits_rect)
export function segmentHitsRect(a, b, box) {
  if (boxTakesPoint(box, a) || boxTakesPoint(box, b)) return true;
  const c = [
    [box.minX, box.minY],
    [box.maxX, box.minY],
    [box.maxX, box.maxY],
    [box.minX, box.maxY],
  ];
  for (let i = 0; i < 4; i++) {
    if (segmentsCross(a, b, c[i], c[(i + 1) % 4])) return true;
  }
  return false;
}

// Does the polyline count as selected? (SolidCraft selection.rs BoxSel::takes)
export function boxTakesPolyline(box, pts, crossing = box.crossing) {
  if (!pts || !pts.length) return false;
  if (!crossing) {
    return pts.every((p) => boxTakesPoint(box, p));
  }
  if (pts.some((p) => boxTakesPoint(box, p))) return true;
  for (let i = 1; i < pts.length; i++) {
    if (segmentHitsRect(pts[i - 1], pts[i], box)) return true;
  }
  return false;
}

// Test a line segment against the box (window: both ends inside; crossing: touches or intersects)
export function boxTakesLine(box, crossing, a, b) {
  if (!crossing) {
    return boxTakesPoint(box, a) && boxTakesPoint(box, b);
  }
  return segmentHitsRect(a, b, box);
}

// Test a circle against the box (window: entire bounding circle enclosed; crossing: touches or inside)
export function boxTakesCircle(box, crossing, center, radius, n = 48) {
  if (!crossing) {
    return (
      center[0] - radius >= box.minX &&
      center[0] + radius <= box.maxX &&
      center[1] - radius >= box.minY &&
      center[1] + radius <= box.maxY
    );
  }
  const pts = curvePoints({ type: "circle", center_at: center, radius }, n);
  return boxTakesPolyline(box, pts, true);
}

// Test an arc against the box (sampled into polyline)
export function boxTakesArc(box, crossing, center, radius, start_at, end_at, n = 48) {
  const pts = curvePoints({ type: "arc", center_at: center, radius, start_at, end_at }, n);
  return boxTakesPolyline(box, pts, crossing);
}

// Test any curve (line, circle, arc) against the box.
// project: optional projection function, e.g. screenOf to project 2D sketch points to screen pixels.
export function boxTakesCurve(box, curve, crossing = box.crossing, project = null) {
  if (!curve) return false;
  if (project) {
    if (curve.type === "line" && curve.start_at && curve.end_at) {
      return boxTakesLine(box, crossing, project(curve.start_at), project(curve.end_at));
    }
    const pts = curvePoints(curve, 48).map(project);
    return boxTakesPolyline(box, pts, crossing);
  }
  if (curve.type === "line" && curve.start_at && curve.end_at) {
    return boxTakesLine(box, crossing, curve.start_at, curve.end_at);
  }
  if (curve.type === "circle" && curve.center_at && curve.radius) {
    return boxTakesCircle(box, crossing, curve.center_at, curve.radius, 48);
  }
  if (curve.type === "arc" && curve.center_at && curve.radius) {
    return boxTakesArc(box, crossing, curve.center_at, curve.radius, curve.start_at, curve.end_at, 48);
  }
  return false;
}

