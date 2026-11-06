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

// a closed loop of curve ids as one polygon: each curve turned so that it starts where the last one ended
export function loopPoints(ids, byId) {
  const out = [];
  for (const id of ids) {
    const c = byId[id];
    if (!c) continue;
    let pts = curvePoints(c);
    if (out.length && pts.length > 1) {
      const last = out[out.length - 1];
      const d0 = Math.hypot(pts[0][0] - last[0], pts[0][1] - last[1]);
      const d1 = Math.hypot(pts[pts.length - 1][0] - last[0], pts[pts.length - 1][1] - last[1]);
      if (d1 < d0) pts = pts.slice().reverse();
      pts = pts.slice(1);
    }
    out.push(...pts);
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
