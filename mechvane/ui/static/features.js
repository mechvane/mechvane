// Feature dialogs of the workspace (ADR 0005, stage 2): pick in the 3D view, values in the
// Properties panel, a preview while you type, OK runs the command through /api/feature on the same
// SolidCraft session the agent uses. Each finished step lands in the shared undo list.
//
// A dialog describes its picks ("edges" or "point" on a face), its fields (number, select, check;
// shown or hidden by the other values), how the values become the command's parameters, and for
// editing how a feature's definition (timeline.inspect) becomes values and back (timeline.edit).
import * as THREE from "three";
import { bodyEdges, edgeInfo, edgeKey } from "./viewtools.js";

// Feature types the model browser can open in a dialog again (the server keeps the same list)
export const EDITABLE_TYPES = {
  FilletFeature: "fillet", ChamferFeature: "chamfer", HoleFeature: "hole",
  RectangularPatternFeature: "rectangular", CircularPatternFeature: "circular", MirrorFeature: "mirror",
  ExtrudeFeature: "extrude", RevolveFeature: "revolve",
};

const PREVIEW_DELAY_MS = 300;
const PICK_COLOR = 0x58a6ff;

const fmt = (v) => String(+(+v).toFixed(3));

const AXES = { X: [1, 0, 0], Y: [0, 1, 0], Z: [0, 0, 1] };
const AXIS_OPTIONS = (pickLabel) => [["X", "X axis"], ["Y", "Y axis"], ["Z", "Z axis"]]
  .concat(pickLabel ? [["edge", pickLabel]] : []);

// A world axis or the clicked straight edge as a direction, flipped on request
function axisVec(sel, flip = false, edge1 = null) {
  const v = sel === "edge" ? (edge1?.dir || [1, 0, 0]) : AXES[sel];
  return v.map((c) => (flip ? -c : c) + 0);
}

// Which world axis a stored direction is, and whether it points the other way
function axisOf(vec) {
  if (!Array.isArray(vec)) return { axis: null, flip: false };
  for (const [name, a] of Object.entries(AXES)) {
    const dot = a[0] * vec[0] + a[1] * vec[1] + a[2] * vec[2];
    if (Math.abs(Math.abs(dot) - 1) < 1e-9) return { axis: name, flip: dot < 0 };
  }
  return { axis: null, flip: false };
}

// An angle field in degrees as SolidCraft's expression
const deg = (v) => (typeof v === "number" ? `${v} deg` : String(v));

// The axis of a clicked edge for an edit (circle: its centre and axis; line: along it), with the edge as axis_ref
function edgeAxis(edge1) {
  const e = edge1.edge;
  const r6 = (v) => v.toArray().map((c) => +c.toFixed(6));
  const at = e.kind === "line" ? { axis: r6(e.dir), origin: r6(e.start) } : { axis: r6(e.axis), origin: r6(e.center) };
  return { ...at, axis_ref: { type: "edge", at: edge1.point } };
}

// Two directions in a plane with this normal (a custom mirror plane is stored by them)
function planeBasis(normal) {
  const n = new THREE.Vector3(...normal).normalize();
  const helper = Math.abs(n.x) < 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  const x = new THREE.Vector3().crossVectors(helper, n).normalize();
  const y = new THREE.Vector3().crossVectors(n, x).normalize();
  return [x, y].map((v) => v.toArray().map((c) => +c.toFixed(9)));
}

// The part's sketches for Extrude and Revolve (GET /api/sketches), loaded each time a dialog opens
let sketchList = [];
const SKETCH_OPTIONS = () => sketchList.map((sk) => [sk.name,
  sk.name + (sk.used_by.length ? ` (used by ${sk.used_by.join(", ")})` : "")]);
const OPERATIONS = [["join", "Join"], ["cut", "Cut"], ["new_body", "New body"], ["intersect", "Intersect"]];
// create takes "new", the definition (and timeline.edit) "new_body"
const opParam = (op) => (op === "new_body" ? "new" : op);
// the newest sketch nothing uses yet, else the newest
const defaultSketch = () => ([...sketchList].reverse().find((sk) => !sk.used_by.length) || sketchList[sketchList.length - 1])?.name || "";

// Tables for the Hole dialog (GET /api/hole_sizes), loaded once
let holeTables = null;

const HOLE_SIZE_OPTIONS = () => Object.keys(holeTables?.sizes || {}).map((s) => [s, s]);

function holeDefaults(v) {
  const t = holeTables?.sizes?.[v.size];
  if (!t) return {};
  const out = {};
  if (v.spec === "clearance") out.diameter = t.clearance[v.fit] ?? t.clearance.normal;
  if (v.spec === "tapped") out.diameter = t.tap_drill;
  if (t.counterbore) { out.cb_diameter = t.counterbore.diameter; out.cb_depth = t.counterbore.depth; }
  if (t.countersink) { out.cs_diameter = t.countersink.diameter; out.cs_angle = t.countersink.angle; }
  return out;
}

// Sketch dialog helpers: a shape in sketch coordinates drawn on the plane's frame
const r05 = (v) => Math.round(v * 2) / 2;
function shapeComplete(sh) {
  const n = (k) => sh[k] !== null && sh[k] !== undefined && sh[k] !== "";
  return n("x") && n("y") && (sh.type === "circle" ? n("d") : n("w") && n("h"));
}
function shapeLabel(sh) {
  return sh.type === "circle" ? `Circle Ø${sh.d} at ${sh.x}, ${sh.y}` : `Rectangle ${sh.w} x ${sh.h} at ${sh.x}, ${sh.y}`;
}
function shapeLines(sh, frame) {
  const o = new THREE.Vector3(...frame.origin), x = new THREE.Vector3(...frame.x_dir), y = new THREE.Vector3(...frame.y_dir);
  const at = (u, v) => o.clone().addScaledVector(x, u).addScaledVector(y, v);
  const nums = ["x", "y", "w", "h", "d"].map((k) => sh[k]);
  if (nums.some((n, i) => (sh.type === "circle" ? [0, 1, 4] : [0, 1, 2, 3]).includes(i) && typeof n !== "number")) return null;
  if (sh.type === "circle") {
    const pts = [];
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * Math.PI * 2;
      pts.push(at(sh.x + (sh.d / 2) * Math.cos(a), sh.y + (sh.d / 2) * Math.sin(a)));
    }
    return pts;
  }
  return [at(sh.x, sh.y), at(sh.x + sh.w, sh.y), at(sh.x + sh.w, sh.y + sh.h), at(sh.x, sh.y + sh.h), at(sh.x, sh.y)];
}

const DIALOGS = {
  sketch: {
    title: "Sketch",
    command: "mechvane.sketch",
    view: "sketch",
    noPreview: true,
    noFieldCheck: true,
    hint: "Click in the view: first the corner (or centre), then the opposite corner (or a point on the circle)",
    fields: [
      { key: "plane", label: "Plane", type: "select", value: "XY",
        options: [["XY", "XY plane"], ["XZ", "XZ plane"], ["YZ", "YZ plane"], ["face", "Clicked face"]] },
      { key: "shape", label: "Shape", type: "select", value: "rectangle", options: [["rectangle", "Rectangle"], ["circle", "Circle"]] },
      { key: "x", label: "X", unit: "mm", value: "" },
      { key: "y", label: "Y", unit: "mm", value: "" },
      { key: "w", label: "Width", unit: "mm", value: "", show: (v) => v.shape === "rectangle" },
      { key: "h", label: "Height", unit: "mm", value: "", show: (v) => v.shape === "rectangle" },
      { key: "d", label: "Diameter", unit: "mm", value: "", show: (v) => v.shape === "circle" },
    ],
    extraHtml: `<div class="sketch-shapes"></div>
      <div class="feature-actions sketch-add-row"><button type="button" class="btn-text sketch-add">Add another shape</button></div>`,
    current: (v) => ({ type: v.shape, x: v.x, y: v.y, w: v.w, h: v.h, d: v.d }),
    ready: (v, p) => p.sketch.shapes.length > 0 || shapeComplete(DIALOGS.sketch.current(v)),
    status: (v, p) => (v.plane === "face" && !p.sketch.face ? "Click a flat face for the sketch" : null),
    params(v, p) {
      const cur = DIALOGS.sketch.current(v);
      const shapes = [...p.sketch.shapes, ...(shapeComplete(cur) ? [cur] : [])];
      return { plane: v.plane === "face" ? { face: p.sketch.face } : v.plane, shapes };
    },
    // the plane's frame from the server (also for faces), then clicks on it; the view turns onto it
    async init(active, h) {
      active.shapes = [];
      active.clicks = 0;
      const box = active.form.querySelector(".sketch-shapes");
      const list = () => {
        box.replaceChildren(...active.shapes.map((sh, i) => {
          const row = document.createElement("div");
          row.className = "sketch-shape";
          row.textContent = shapeLabel(sh);
          const del = document.createElement("button");
          del.type = "button";
          del.className = "btn-text";
          del.textContent = "×";
          del.title = "Remove";
          del.addEventListener("click", () => { active.shapes.splice(i, 1); list(); h.update(); });
          row.append(del);
          return row;
        }));
      };
      active.form.querySelector(".sketch-add").addEventListener("click", () => {
        const cur = DIALOGS.sketch.current(h.values());
        if (!shapeComplete(cur)) return;
        active.shapes.push(cur);
        for (const k of ["x", "y", "w", "h", "d"]) h.setValue(k, "");
        list();
        h.update();
      });
      active.loadPlane = async () => {
        const v = h.values();
        active.frame = null;
        h.update();
        if (v.plane === "face" && !active.face) {
          h.viewTools.startFacePick((pick) => {
            if (!pick.planar) return;
            active.face = pick.point.toArray().map((c) => +c.toFixed(4));
            active.loadPlane();
          });
          return;
        }
        const q = v.plane === "face" ? `face=${active.face.join(",")}` : `plane=${v.plane}`;
        try {
          active.frame = await h.get(`api/sketch_plane?${q}`);
        } catch (err) {
          h.setError(err.message);
          return;
        }
        h.lookAlong(active.frame);
        h.viewTools.startPlanePick(active.frame, ([u, w]) => {
          const val = h.values();
          if (active.clicks === 0) {
            h.setValue("x", fmt(r05(u)));
            h.setValue("y", fmt(r05(w)));
            for (const k of ["w", "h", "d"]) h.setValue(k, "");
            active.clicks = 1;
          } else {
            if (val.shape === "circle") {
              h.setValue("d", fmt(Math.max(0.5, r05(2 * Math.hypot(u - val.x, w - val.y)))));
            } else {
              // the dimensions are positive: the corner is the lower left one, whichever way it was dragged
              let x0 = val.x, y0 = val.y, wd = r05(u - x0), ht = r05(w - y0);
              if (wd < 0) { x0 += wd; wd = -wd; }
              if (ht < 0) { y0 += ht; ht = -ht; }
              h.setValue("x", fmt(x0)); h.setValue("y", fmt(y0));
              h.setValue("w", fmt(Math.max(wd, 0.5))); h.setValue("h", fmt(Math.max(ht, 0.5)));
            }
            active.clicks = 0;
          }
          h.update();
        });
        h.update();
      };
      await active.loadPlane();
    },
    onChange(key, v, set, active) {
      if (key === "plane" && active?.loadPlane) {
        if (v.plane === "face") active.face = null;
        active.loadPlane();
      }
      if (key === "shape" && active) active.clicks = 0;
    },
    draw(active, v, add) {
      if (!active.frame) return;
      // the sketch's own axes from its origin: X red, Y green, as in the view's axis gizmo
      const f = active.frame;
      const axis = (dir, color) => add([new THREE.Vector3(...f.origin),
        new THREE.Vector3(...f.origin).addScaledVector(new THREE.Vector3(...dir), 25)], color);
      axis(f.x_dir, 0xe5534b);
      axis(f.y_dir, 0x57ab5a);
      active.shapes.forEach((sh) => add(shapeLines(sh, active.frame), 0x58a6ff));
      add(shapeLines(DIALOGS.sketch.current(v), active.frame), 0xf0b429);
    },
    // a finished sketch goes straight on to Extrude, as in Inventor
    after: (res, dialogs) => dialogs.open("extrude"),
  },
  fillet: {
    title: "Fillet",
    command: "solid.fillet",
    view: "edges",
    hint: "Click the edges to round",
    fields: [{ key: "radius", label: "Radius", unit: "mm", value: "2" }],
    params: (v, picks) => ({ edges: picks.edges, radius: v.radius }),
    fromDefinition: (d) => ({ values: { radius: d.radius }, edges: d.edges || [] }),
  },
  chamfer: {
    title: "Chamfer",
    command: "solid.chamfer",
    view: "edges",
    hint: "Click the edges to bevel",
    fields: [{ key: "distance", label: "Distance", unit: "mm", value: "1" }],
    params: (v, picks) => ({ edges: picks.edges, distance: v.distance }),
    fromDefinition: (d) => ({ values: { distance: d.distance }, edges: d.edges || [] }),
  },
  hole: {
    title: "Hole",
    command: "solid.hole",
    view: "face",
    hint: "Click a face where the hole goes",
    status: (v) => ([v.x, v.y, v.z].every((c) => c !== null) ? "Click another face to move it, or type the position" : null),
    // a click on a face places the hole: rounded to 0.1 mm in the plane, drilled into the clicked side
    onFace(pick, set, active) {
      const p = pick.planar ? roundOnPlane(pick.point, pick.normal) : pick.point;
      set("x", fmt(p.x));
      set("y", fmt(p.y));
      set("z", fmt(p.z));
      active.face = null;
      active.point = { direction: pick.normal.clone().negate().toArray().map((c) => +c.toFixed(6)) };
    },
    needs: async (get) => { if (!holeTables) holeTables = await get("api/hole_sizes"); },
    fields: [
      { key: "x", label: "X", unit: "mm", value: "", group: "position" },
      { key: "y", label: "Y", unit: "mm", value: "", group: "position" },
      { key: "z", label: "Z", unit: "mm", value: "", group: "position" },
      { key: "spec", label: "Size", type: "select", value: "clearance",
        options: [["clearance", "Clearance for screw"], ["tapped", "Tapped thread"], ["diameter", "Diameter"]] },
      { key: "size", label: "Screw", type: "select", value: "M5", options: HOLE_SIZE_OPTIONS,
        show: (v) => v.spec !== "diameter" },
      { key: "fit", label: "Fit", type: "select", value: "normal",
        options: [["close", "Close (ISO 273 fine)"], ["normal", "Normal (ISO 273 medium)"], ["loose", "Loose (ISO 273 coarse)"]],
        show: (v) => v.spec === "clearance" },
      { key: "diameter", label: "Diameter", unit: "mm", value: "5.5", readonly: (v) => v.spec !== "diameter" },
      { key: "type", label: "Type", type: "select", value: "simple",
        options: [["simple", "Simple"], ["counterbore", "Counterbore"], ["countersink", "Countersink"]] },
      { key: "cb_diameter", label: "Cb. Ø", unit: "mm", value: "10", show: (v) => v.type === "counterbore" },
      { key: "cb_depth", label: "Cb. depth", unit: "mm", value: "5.4", show: (v) => v.type === "counterbore" },
      { key: "cs_diameter", label: "Cs. Ø", unit: "mm", value: "11.5", show: (v) => v.type === "countersink" },
      { key: "cs_angle", label: "Cs. angle", unit: "°", value: "90", show: (v) => v.type === "countersink" },
      { key: "through", label: "Through all", type: "check", value: true },
      { key: "depth", label: "Depth", unit: "mm", value: "10", show: (v) => !v.through },
    ],
    // size, fit or type changed: the table values follow (the user may still type over them)
    onChange(key, v, set) {
      if (!["spec", "size", "fit", "type"].includes(key)) return;
      const d = holeDefaults(v);
      for (const k of ["diameter", "cb_diameter", "cb_depth", "cs_diameter", "cs_angle"]) {
        if (d[k] !== undefined && (k !== "diameter" || v.spec !== "diameter")) set(k, fmt(d[k]));
      }
    },
    sourceNote(v) {
      if (!holeTables) return "";
      const s = holeTables.sources;
      const notes = [];
      if (v.spec === "clearance") notes.push(`Ø from ${s.clearance}`);
      if (v.spec === "tapped") notes.push(`tap drill from ${s.tap_drill}`);
      if (v.type === "counterbore") notes.push(`counterbore from ${s.counterbore}`);
      if (v.type === "countersink") notes.push(`countersink from ${s.countersink}`);
      return notes.length ? `Values: ${notes.join(", ")}` : "";
    },
    params(v, picks) {
      const p = { position: [v.x, v.y, v.z], diameter: v.diameter };
      if (picks.direction) p.direction = picks.direction;
      if (v.spec === "tapped") p.thread = v.size;
      if (!v.through) p.depth = v.depth;
      if (v.type === "counterbore") Object.assign(p, { type: "counterbore", cb_diameter: v.cb_diameter, cb_depth: v.cb_depth });
      if (v.type === "countersink") Object.assign(p, { type: "countersink", cs_diameter: v.cs_diameter, cs_angle: v.cs_angle });
      return p;
    },
    // timeline.edit merges into the definition: same fields, the hole type under "hole", null removes
    editSet(v, picks) {
      const hole = { type: v.type };
      if (v.type === "counterbore") Object.assign(hole, { cb_diameter: v.cb_diameter, cb_depth: v.cb_depth });
      if (v.type === "countersink") Object.assign(hole, { cs_diameter: v.cs_diameter, cs_angle: v.cs_angle });
      const set = { position: [v.x, v.y, v.z], diameter: v.diameter, depth: v.through ? null : v.depth,
                    thread: v.spec === "tapped" ? v.size : null, hole };
      if (picks.direction) set.direction = picks.direction;
      return set;
    },
    fromDefinition(d) {
      const h = d.hole || {};
      const dia = parseFloat(d.diameter);
      const v = { x: d.position?.[0], y: d.position?.[1], z: d.position?.[2], diameter: dia, type: h.type || "simple",
                  through: d.depth === undefined || d.depth === null, depth: d.depth ?? "10",
                  cb_diameter: h.cb_diameter, cb_depth: h.cb_depth, cs_diameter: h.cs_diameter, cs_angle: h.cs_angle };
      // which table entry made this diameter: a thread, a clearance hole of some fit, or neither
      if (d.thread) Object.assign(v, { spec: "tapped", size: d.thread });
      else {
        let match = null;
        for (const [size, t] of Object.entries(holeTables?.sizes || {})) {
          for (const [fit, val] of Object.entries(t.clearance)) if (!match && Math.abs(val - dia) < 1e-6) match = { size, fit };
        }
        Object.assign(v, match ? { spec: "clearance", ...match } : { spec: "diameter" });
      }
      return { values: v, direction: d.direction };
    },
  },
  extrude: {
    title: "Extrude",
    command: "solid.extrude",
    hint: "Choose the sketch to extrude",
    needs: async (get) => { sketchList = (await get("api/sketches")).sketches || []; },
    fields: [
      { key: "sketch", label: "Sketch", type: "select", value: defaultSketch, options: SKETCH_OPTIONS },
      { key: "operation", label: "Operation", type: "select", value: "join", options: OPERATIONS },
      { key: "direction", label: "Direction", type: "select", value: "positive",
        options: [["positive", "Direction 1"], ["negative", "Direction 2"], ["symmetric", "Symmetric"]] },
      { key: "through", label: "Through all", type: "check", value: false },
      { key: "distance", label: "Distance", unit: "mm", value: "10", show: (v) => !v.through },
    ],
    // a cut usually goes into the material, against the face's outward side
    onChange(key, v, set) {
      if (key === "operation" && v.operation === "cut" && v.direction === "positive") set("direction", "negative");
      if (key === "operation" && v.operation !== "cut" && v.direction === "negative") set("direction", "positive");
    },
    ready: (v) => !!v.sketch,
    status: (v) => (sketchList.length ? null : "This part has no sketch yet: make one in File → Open in SolidCraft, or ask your agent"),
    params(v) {
      const p = { sketch: v.sketch, operation: opParam(v.operation), direction: v.direction };
      if (v.through) p.through_all = true;
      else p.distance = v.distance;
      return p;
    },
    editSet(v) {
      return { sketch: v.sketch, operation: v.operation,
               extent: { direction: v.direction, through_all: !!v.through, distance: v.through ? "0" : String(v.distance) } };
    },
    fromDefinition(d, names) {
      const e = d.extent || {};
      return { values: { sketch: names[d.sketch] || d.sketch, operation: d.operation || "join", direction: e.direction || "positive",
                         through: !!e.through_all, distance: e.through_all ? "10" : e.distance } };
    },
  },
  revolve: {
    title: "Revolve",
    command: "solid.revolve",
    view: "edge",
    hint: "Choose the sketch and the axis",
    needs: async (get) => { sketchList = (await get("api/sketches")).sketches || []; },
    fields: [
      { key: "sketch", label: "Sketch", type: "select", value: defaultSketch, options: SKETCH_OPTIONS },
      { key: "axis", label: "Axis", type: "select", value: "Z", options: AXIS_OPTIONS("Clicked edge") },
      { key: "angle", label: "Angle", unit: "°", value: "360" },
      { key: "operation", label: "Operation", type: "select", value: "join", options: OPERATIONS },
    ],
    ready: (v, p) => !!v.sketch && (v.axis !== "edge" || !!p.edge1),
    status: (v, p) => (!sketchList.length ? "This part has no sketch yet: make one in File → Open in SolidCraft, or ask your agent"
      : v.axis === "edge" && !p.edge1 ? "Click a straight edge in the sketch's plane for the axis" : null),
    params(v, p) {
      return { sketch: v.sketch, axis: v.axis === "edge" ? { edge: p.edge1.point } : v.axis, angle: deg(v.angle),
               operation: opParam(v.operation) };
    },
    editSet(v, p) {
      const set = { sketch: v.sketch, angle: deg(v.angle), operation: v.operation };
      if (v.axis !== "edge") set.axis = { type: "world", axis: v.axis };
      else if (p.edge1?.keep) set.axis = p.edge1.keep;
      else set.axis = { edge: p.edge1.point };
      return set;
    },
    fromDefinition(d, names) {
      const world = d.axis?.type === "world";
      return { values: { sketch: names[d.sketch] || d.sketch, axis: world ? d.axis.axis : "edge",
                         angle: String(d.angle ?? "360").replace(/\s*deg$/, ""), operation: d.operation || "join" },
               edge1: world ? null : { point: d.axis?.at || [0, 0, 0], keep: d.axis } };
    },
  },
  rectangular: {
    title: "Rectangular Pattern",
    command: "solid.pattern.rectangular",
    features: true,
    view: "edge",
    hint: "Click the features to copy in the model browser",
    fields: [
      { key: "dir1", label: "Direction", type: "select", value: "X", options: AXIS_OPTIONS("Along the clicked edge") },
      { key: "flip1", label: "Flip", type: "check", value: false },
      { key: "count1", label: "Count", unit: "", value: "3" },
      { key: "spacing1", label: "Spacing", unit: "mm", value: "10" },
      { key: "two", label: "Second direction", type: "check", value: false },
      { key: "dir2", label: "Direction 2", type: "select", value: "Y", options: AXIS_OPTIONS(null), show: (v) => v.two },
      { key: "flip2", label: "Flip 2", type: "check", value: false, show: (v) => v.two },
      { key: "count2", label: "Count 2", unit: "", value: "2", show: (v) => v.two },
      { key: "spacing2", label: "Spacing 2", unit: "mm", value: "10", show: (v) => v.two },
    ],
    ready: (v, p) => p.features.length > 0 && (v.dir1 !== "edge" || !!p.edge1?.dir),
    status: (v, p) => (v.dir1 === "edge" && !p.edge1 ? "Click a straight edge for the direction" : null),
    params(v, p) {
      const out = { features: p.features, dir1: axisVec(v.dir1, v.flip1, p.edge1), count1: v.count1, spacing1: v.spacing1 };
      if (v.two) Object.assign(out, { dir2: axisVec(v.dir2, v.flip2), count2: v.count2, spacing2: v.spacing2 });
      return out;
    },
    editSet(v, p) {
      // a pattern's definition keeps counts and spacings as expressions (text); timeline.edit wants the same
      const pattern = { type: "rectangular", dir1: axisVec(v.dir1, v.flip1, p.edge1), count1: String(v.count1),
                        spacing1: String(v.spacing1), dir2: null, count2: null, spacing2: null };
      if (v.two) Object.assign(pattern, { dir2: axisVec(v.dir2, v.flip2), count2: String(v.count2), spacing2: String(v.spacing2) });
      return { features: p.features, pattern };
    },
    fromDefinition(d, names) {
      const q = d.pattern || {};
      const a1 = axisOf(q.dir1), a2 = axisOf(q.dir2);
      const v = { dir1: a1.axis || "edge", flip1: a1.flip, count1: q.count1, spacing1: q.spacing1, two: !!q.dir2,
                  dir2: a2.axis || "Y", flip2: a2.flip, count2: q.count2 ?? "2", spacing2: q.spacing2 ?? "10" };
      return { values: v, features: (d.features || []).map((id) => names[id] || id),
               edge1: a1.axis ? null : { dir: q.dir1, keep: true } };
    },
  },
  circular: {
    title: "Circular Pattern",
    command: "solid.pattern.circular",
    features: true,
    view: "edge",
    hint: "Click the features to copy in the model browser",
    fields: [
      { key: "axis", label: "Axis", type: "select", value: "edge", options: AXIS_OPTIONS("Clicked edge or hole") },
      { key: "count", label: "Count", unit: "", value: "4" },
      { key: "angle", label: "Angle", unit: "°", value: "360" },
    ],
    ready: (v, p) => p.features.length > 0 && (v.axis !== "edge" || !!p.edge1),
    status: (v, p) => (v.axis === "edge" && !p.edge1 ? "Click a hole's edge or a straight edge for the axis" : null),
    params(v, p) {
      return { features: p.features, axis: v.axis === "edge" ? { edge: p.edge1.point } : v.axis, count: v.count,
               angle: deg(v.angle) };
    },
    // an edit stores the axis as direction and origin; a clicked edge also as axis_ref, so it follows the model
    editSet(v, p) {
      // timeline.edit takes unitless values (counts) only as text
      const pattern = { type: "circular", count: String(v.count), angle: deg(v.angle) };
      if (v.axis !== "edge") Object.assign(pattern, { axis: axisVec(v.axis), origin: [0, 0, 0], axis_ref: null });
      else if (p.edge1?.keep) Object.assign(pattern, p.edge1.keep);
      else Object.assign(pattern, edgeAxis(p.edge1));
      return { features: p.features, pattern };
    },
    fromDefinition(d, names) {
      const q = d.pattern || {};
      const a = axisOf(q.axis);
      const world = a.axis && !a.flip && !q.axis_ref && (q.origin || [0, 0, 0]).every((c) => Math.abs(c) < 1e-9);
      const v = { axis: world ? a.axis : "edge", count: q.count, angle: String(q.angle ?? "360").replace(/\s*deg$/, "") };
      const keep = { axis: q.axis, origin: q.origin, axis_ref: q.axis_ref ?? null };
      return { values: v, features: (d.features || []).map((id) => names[id] || id),
               edge1: world ? null : { point: q.axis_ref?.at || q.origin, keep } };
    },
  },
  mirror: {
    title: "Mirror",
    command: "solid.mirror",
    features: true,
    view: "face",
    hint: "Click the features to mirror in the model browser",
    fields: [
      { key: "plane", label: "Plane", type: "select", value: "YZ",
        options: [["YZ", "YZ plane"], ["XZ", "XZ plane"], ["XY", "XY plane"], ["face", "Clicked face"]] },
    ],
    ready: (v, p) => p.features.length > 0 && (v.plane !== "face" || !!p.face),
    status: (v, p) => (v.plane === "face" && !p.face ? "Click a flat face for the mirror plane" : null),
    onFace(pick, set, active) {
      if (!pick.planar) return;
      active.face = { point: pick.point.toArray().map((c) => +c.toFixed(6)),
                      normal: pick.normal.toArray().map((c) => +c.toFixed(6)) };
      set("plane", "face");
    },
    params(v, p) {
      return { features: p.features, plane: v.plane === "face" ? { origin: p.face.point, normal: p.face.normal } : v.plane };
    },
    editSet(v, p) {
      if (v.plane !== "face") return { features: p.features, plane: { type: "origin", name: v.plane } };
      if (p.face.keep) return { features: p.features, plane: p.face.keep };
      const [x, y] = planeBasis(p.face.normal);
      return { features: p.features, plane: { type: "custom", plane: { origin: p.face.point, x_dir: x, y_dir: y } } };
    },
    fromDefinition(d, names) {
      const pl = d.plane || {};
      const world = pl.type === "origin";
      return { values: { plane: world ? pl.name : "face" }, features: (d.features || []).map((id) => names[id] || id),
               face: world ? null : { point: pl.plane?.origin, normal: null, keep: pl } };
    },
  },
};

// A value field holds a number or an expression with parameters ("t/2"); numbers go as numbers
function fieldValue(text) {
  const t = String(text).trim().replace(/^(-?\d+),(\d+)$/, "$1.$2");
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : t;
}

// The first line of a SolidCraft error: Mechvane's explanation and hint, without the raw reply under it
function firstLine(msg) {
  return String(msg || "").split("\n")[0];
}

// The mesh edge a stored edge point lies on (a feature keeps its edges as points), or null
function edgeAt(meshData, point) {
  const p = new THREE.Vector3(...point);
  let best = null, bestD = Infinity;
  for (const body of (meshData && meshData.bodies) || []) {
    const edges = bodyEdges(body);
    for (const e of edges) {
      const ab = new THREE.Vector3().subVectors(e.b, e.a);
      const t = THREE.MathUtils.clamp(new THREE.Vector3().subVectors(p, e.a).dot(ab) / Math.max(ab.lengthSq(), 1e-12), 0, 1);
      const d = e.a.clone().addScaledVector(ab, t).distanceTo(p);
      if (d < bestD) { bestD = d; best = [edges, e]; }
    }
  }
  // the mesh cuts corners of arcs: allow a little more than rounding
  return best && bestD < 0.05 ? edgeInfo(best[0], best[1]) : null;
}

// A clicked point on a plane, rounded to 0.1 mm in the plane and kept exactly on it
function roundOnPlane(point, normal) {
  const r = new THREE.Vector3(...point.toArray().map((x) => Math.round(x * 10) / 10));
  return r.addScaledVector(normal, -new THREE.Vector3().subVectors(r, point).dot(normal));
}

export function initFeatureDialogs({ scene, viewTools, renderScene, propertiesEl, statusEl, post, get,
                                     showPreview, clearPreview, reload, showModel, restoreModel,
                                     lookAlong = () => {} }) {
  const pickGroup = new THREE.Group();
  scene.add(pickGroup);
  const emptyHtml = propertiesEl.innerHTML;
  // {kind, def, form, edges: Map(key → {point, edge}), edge1: one clicked edge, face: one clicked face,
  //  features: names picked in the model browser, point: {direction} (hole), timer, seq, busy, edit}
  let active = null;
  let markerSize = 1;

  function drawPicks() {
    while (pickGroup.children.length) {
      const c = pickGroup.children.pop();
      c.geometry?.dispose();
      c.material?.dispose();
    }
    if (!active) {
      markTree();
      return renderScene();
    }
    const lineMat = () => new THREE.LineBasicMaterial({ color: PICK_COLOR, depthTest: false });
    const edgeList = [...active.edges.values()];
    if (active.edge1?.edge) edgeList.push(active.edge1);
    for (const { edge } of edgeList) {
      if (!edge) continue;
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(edge.points), lineMat());
      line.renderOrder = 20;
      pickGroup.add(line);
    }
    if (active.face?.normal) {
      const at = new THREE.Vector3(...active.face.point);
      const dot = new THREE.Mesh(new THREE.SphereGeometry(markerSize, 16, 12),
        new THREE.MeshBasicMaterial({ color: PICK_COLOR, depthTest: false }));
      dot.position.copy(at);
      dot.renderOrder = 20;
      pickGroup.add(dot);
      const end = at.clone().addScaledVector(new THREE.Vector3(...active.face.normal), markerSize * 12);
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([at, end]), lineMat());
      line.renderOrder = 20;
      pickGroup.add(line);
    }
    markTree();
    if (active.def.draw) {
      active.def.draw(active, values(), (pts, color) => {
        if (!pts) return;
        const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
          new THREE.LineBasicMaterial({ color, depthTest: false }));
        line.renderOrder = 21;
        pickGroup.add(line);
      });
    } else if (active.def.fields.some((f) => f.key === "x")) {
      const v = values();
      if ([v.x, v.y, v.z].every((c) => typeof c === "number")) {
        const at = new THREE.Vector3(v.x, v.y, v.z);
        const dot = new THREE.Mesh(new THREE.SphereGeometry(markerSize, 16, 12),
          new THREE.MeshBasicMaterial({ color: PICK_COLOR, depthTest: false }));
        dot.position.copy(at);
        dot.renderOrder = 20;
        pickGroup.add(dot);
        if (active.point?.direction) {
          const end = at.clone().addScaledVector(new THREE.Vector3(...active.point.direction), markerSize * 12);
          const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([at, end]), lineMat());
          line.renderOrder = 20;
          pickGroup.add(line);
        }
      }
    }
    renderScene();
  }

  // Features picked for a pattern or mirror are marked in the model browser
  function markTree() {
    const picked = new Set(active ? active.features : []);
    document.querySelectorAll(".tree-row[data-feature]").forEach((row) => {
      row.classList.toggle("picked", picked.has(row.dataset.feature));
    });
  }

  function input(key) {
    return active.form.querySelector(`[name="${key}"]`);
  }

  function values() {
    const out = {};
    for (const f of active.def.fields) {
      const el = input(f.key);
      if (f.type === "check") out[f.key] = el.checked;
      else if (f.type === "select") out[f.key] = el.value;
      else out[f.key] = fieldValue(el.value);
    }
    return out;
  }

  function setValue(key, value) {
    const el = input(key);
    const f = active.def.fields.find((x) => x.key === key);
    if (!el || !f || value === undefined || value === null) return;
    if (f.type === "check") el.checked = !!value;
    else el.value = String(value);
  }

  // Fields shown or read-only by the other values, and the note naming the tables
  function refreshFields() {
    const v = values();
    for (const f of active.def.fields) {
      const row = input(f.key).closest(".feature-field");
      row.hidden = f.show ? !f.show(v) : false;
      if (f.readonly) input(f.key).readOnly = f.readonly(v);
    }
    active.noteEl.textContent = active.def.sourceNote ? active.def.sourceNote(v) : "";
  }

  function setError(msg) {
    active.errorEl.textContent = msg || "";
    active.errorEl.hidden = !msg;
  }

  function describeDelta(d) {
    if (!d) return "";
    const parts = [];
    if (d.volume_change_mm3 !== undefined) {
      const v = d.volume_change_mm3;
      parts.push(`Volume ${v > 0 ? "+" : ""}${v.toFixed(1)} mm³`);
    }
    if (d.bodies !== undefined && d.bodies !== 1) parts.push(`${d.bodies} bodies`);
    for (const w of d.warnings || []) {
      // editing with the values unchanged is not a feature without effect
      if (active && active.edit && /no effect/i.test(w)) continue;
      parts.push(`⚠ ${w}`);
    }
    return parts.join(" · ");
  }

  function picks() {
    return { edges: Array.from(active.edges.values(), (e) => e.point), direction: active.point?.direction || null,
             features: [...active.features], edge1: active.edge1, face: active.face,
             sketch: { shapes: active.shapes || [], face: active.face } };
  }

  // Everything the command needs is there: picks, and every shown number field filled
  function ready() {
    const def = active.def, v = values(), p = picks();
    if (def.view === "edges" && !active.edges.size) return false;
    if (def.ready && !def.ready(v, p)) return false;
    if (def.noFieldCheck) return true; // the sketch: shapes already added count, the fields may be empty
    return def.fields.every((f) => f.type === "check" || f.type === "select" || (f.show && !f.show(v))
      || v[f.key] !== null);
  }

  function update() {
    const def = active.def, v = values(), p = picks();
    let text = def.status ? def.status(v, p) : null;
    if (def.view === "edges") {
      const n = active.edges.size;
      text = text || (n ? `${n} edge${n === 1 ? "" : "s"} selected` : def.hint);
      active.clearBtn.hidden = n === 0;
    } else if (def.features) {
      const n = active.features.length;
      text = !n ? def.hint : text || `${active.features.join(", ")}: click more in the model browser, or set the values`;
      active.clearBtn.hidden = n === 0;
    } else {
      text = text || def.hint;
      active.clearBtn.hidden = true;
    }
    active.countEl.textContent = text;
    if (def.view === "sketch" && !active.frame && !(def.status && def.status(v, p))) {
      active.countEl.textContent = "Loading the plane…";
    }
    active.okBtn.disabled = !ready() || active.busy;
    refreshFields();
    drawPicks();
    schedulePreview();
  }

  function schedulePreview() {
    clearTimeout(active.timer);
    if (active.def.noPreview) return; // drawn here, made with OK
    if (!ready()) {
      active.seq++; // a preview still on its way is no longer wanted
      active.stale = false;
      clearPreview();
      active.deltaEl.textContent = "";
      setError("");
      return;
    }
    // the shown result belongs to the old values: clear it until the new one is there
    active.deltaEl.textContent = "";
    setError("");
    active.timer = setTimeout(runPreview, PREVIEW_DELAY_MS);
  }

  function request(preview) {
    const v = values(), p = picks();
    const body = { command: active.def.command, preview };
    if (active.edit) {
      body.edit = active.edit;
      body.params = active.def.editSet ? active.def.editSet(v, p) : active.def.params(v, p);
    } else body.params = active.def.params(v, p);
    return body;
  }

  // One preview at a time: SolidCraft takes seconds for some features (patterns), and the server works
  // the requests one after the other. While one runs, changes only mark it stale; the latest values
  // follow when it is back.
  async function runPreview() {
    if (!active || !ready()) return;
    const dlg = active;
    if (dlg.inflight) {
      dlg.stale = true;
      return;
    }
    dlg.inflight = true;
    dlg.stale = false;
    const seq = ++dlg.seq;
    const slow = setTimeout(() => { if (active === dlg) dlg.deltaEl.textContent = "Computing preview…"; }, 250);
    try {
      const res = await post("api/feature", request(true));
      if (active !== dlg || dlg.stale || seq !== dlg.seq) return; // closed, or the values changed meanwhile
      setError("");
      showPreview(res.mesh);
      dlg.deltaEl.textContent = describeDelta(res.delta);
    } catch (err) {
      if (active !== dlg || dlg.stale || seq !== dlg.seq) return;
      clearPreview();
      dlg.deltaEl.textContent = "";
      setError(firstLine(err.message));
    } finally {
      clearTimeout(slow);
      dlg.inflight = false;
      if (active === dlg && dlg.stale && !dlg.busy) runPreview();
    }
  }

  async function apply() {
    if (!active || !ready() || active.busy) return;
    clearTimeout(active.timer);
    active.busy = true;
    active.okBtn.disabled = true;
    const dlg = active;
    try {
      const res = await post("api/feature", request(false));
      const def = dlg.def;
      close();
      await reload();
      statusEl.textContent = res.done || "Done";
      if (def.after) def.after(res, api);
    } catch (err) {
      dlg.busy = false;
      if (active === dlg) {
        setError(firstLine(err.message));
        update();
      }
    }
  }

  function close() {
    if (!active) return;
    clearTimeout(active.timer);
    const wasEdit = active.edit, wasSketch = active.def.view === "sketch";
    active = null;
    if (wasEdit) restoreModel();
    if (wasSketch) lookAlong(null); // back to the usual view, as Inventor does after Finish Sketch
    viewTools.stopEdgePick();
    clearPreview();
    drawPicks();
    propertiesEl.innerHTML = emptyHtml;
    document.querySelectorAll("[data-feature]").forEach((b) => b.classList.remove("active"));
  }

  function fieldHtml(f) {
    let control;
    if (f.type === "select") {
      const opts = typeof f.options === "function" ? f.options() : f.options;
      control = `<select name="${f.key}">${opts.map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}</select>`;
    } else if (f.type === "check") {
      control = `<input type="checkbox" name="${f.key}">`;
    } else {
      // no inputmode="decimal": some touch keyboards then hide the minus sign, and fields take expressions (t/2)
      control = `<input name="${f.key}" spellcheck="false" autocapitalize="off" autocomplete="off">`;
    }
    return `<label class="feature-field${f.type === "check" ? " feature-check" : ""}"><span>${f.label}</span>${control}`
      + `<span class="feature-unit">${f.unit || ""}</span></label>`;
  }

  async function open(kind, edit = null) {
    const def = DIALOGS[kind];
    if (!def) return;
    if (active && active.kind === kind && !edit && !active.edit) return close();
    close();
    if (def.needs) {
      try {
        await def.needs(get);
      } catch (err) {
        statusEl.textContent = `${def.title}: ${err.message}`;
        return;
      }
    }
    const position = def.fields.filter((f) => f.group === "position");
    const rest = def.fields.filter((f) => f.group !== "position");
    propertiesEl.innerHTML = `
      <form class="feature-dialog" autocomplete="off">
        <div class="feature-dialog-title"></div>
        <div class="feature-pick">
          <span class="feature-pick-count"></span>
          <button type="button" class="btn-text feature-clear" hidden>Clear</button>
        </div>
        ${position.length ? `<div class="feature-position">${position.map(fieldHtml).join("")}</div>` : ""}
        ${rest.map(fieldHtml).join("")}
        <div class="feature-note"></div>
        <div class="feature-delta"></div>
        <div class="feature-error" hidden></div>
        <div class="feature-actions">
          <button type="button" class="btn-text feature-cancel">Cancel</button>
          <button type="submit" class="feature-ok" disabled>OK</button>
        </div>
      </form>`;
    const form = propertiesEl.querySelector("form");
    form.querySelector(".feature-dialog-title").textContent = edit ? `Edit ${edit.name}` : def.title;
    active = {
      kind, def, form, edges: new Map(), point: null, edge1: null, face: null, features: [],
      timer: null, seq: 0, busy: false, edit: edit ? edit.name : null,
      countEl: form.querySelector(".feature-pick-count"),
      clearBtn: form.querySelector(".feature-clear"),
      okBtn: form.querySelector(".feature-ok"),
      noteEl: form.querySelector(".feature-note"),
      deltaEl: form.querySelector(".feature-delta"),
      errorEl: form.querySelector(".feature-error"),
    };
    for (const f of def.fields) setValue(f.key, typeof f.value === "function" ? f.value() : f.value);
    if (def.extraHtml) active.noteEl.insertAdjacentHTML("beforebegin", def.extraHtml);
    if (def.onChange) def.onChange("size", values(), setValue, active);
    form.addEventListener("submit", (e) => { e.preventDefault(); apply(); });
    form.querySelector(".feature-cancel").addEventListener("click", close);
    active.clearBtn.addEventListener("click", () => {
      active.edges.clear();
      active.features = [];
      update();
    });
    form.querySelectorAll("input, select").forEach((el) => {
      const handler = () => {
        if (def.onChange) def.onChange(el.name, values(), setValue, active);
        update();
      };
      el.addEventListener(el.tagName === "SELECT" || el.type === "checkbox" ? "change" : "input", handler);
    });

    if (edit) {
      const from = def.fromDefinition(edit.definition, edit.feature_names || {});
      for (const [k, v] of Object.entries(from.values || {})) setValue(k, v);
      for (const point of from.edges || []) {
        const edge = edgeAt(edit.before, point);
        active.edges.set(edge ? edgeKey(edge) : `point|${point.join(",")}`, { point, edge });
      }
      if (from.direction) active.point = { direction: from.direction };
      if (from.features) active.features = from.features;
      if (from.edge1) active.edge1 = from.edge1;
      if (from.face) active.face = from.face;
    } else {
      document.querySelectorAll(`[data-feature="${kind}"]`).forEach((b) => b.classList.add("active"));
    }
    const box = new THREE.Box3().setFromObject(scene);
    markerSize = Math.max(box.isEmpty() ? 1 : box.getSize(new THREE.Vector3()).length() / 250, 0.05);

    if (def.view === "edges") {
      viewTools.startEdgePick((pick) => {
        if (!active) return;
        if (active.edges.has(pick.key)) active.edges.delete(pick.key);
        else active.edges.set(pick.key, pick);
        update();
      });
    } else if (def.view === "edge") {
      // one edge: a direction (straight edge) or an axis (straight or circular edge, a hole)
      viewTools.startEdgePick((pick) => {
        if (!active) return;
        const dir = pick.edge.kind === "line" ? pick.edge.dir.toArray().map((c) => +c.toFixed(9)) : null;
        active.edge1 = { ...pick, dir };
        const sel = def.fields.find((f) => f.type === "select" && f.options && (typeof f.options === "function"
          ? f.options() : f.options).some(([val]) => val === "edge"));
        if (sel) setValue(sel.key, "edge");
        update();
      });
    } else if (def.view === "sketch") {
      await def.init(active, { get, setValue, values, update, setError, viewTools, lookAlong });
    } else if (def.view === "face") {
      viewTools.startFacePick((pick) => {
        if (!active || !def.onFace) return;
        def.onFace(pick, setValue, active);
        update();
      });
    }
    update();
    const first = form.querySelector(".feature-field:not([hidden]) input:not([type=checkbox])");
    if (first && def.view === "edges") { first.focus(); first.select(); }
  }

  // Edit a feature from the model browser: its values, and the model as it was before it (Inventor
  // rolls back the same way), so the edges it consumed can be picked again
  async function edit(name) {
    close();
    statusEl.textContent = `Opening ${name}…`;
    let data;
    try {
      data = await get(`api/feature?name=${encodeURIComponent(name)}`);
      if (DIALOGS[data.dialog]?.needs) await DIALOGS[data.dialog].needs(get);
    } catch (err) {
      statusEl.textContent = err.message;
      return;
    }
    showModel(data.before);
    await open(data.dialog, data);
    statusEl.textContent = "Ready";
  }

  async function remove(name) {
    close();
    statusEl.textContent = `Deleting ${name}…`;
    try {
      const res = await post("api/feature/delete", { name });
      const failing = Object.keys(res.failing || {});
      await reload();
      statusEl.textContent = failing.length
        ? `${res.done}. Now failing: ${failing.join(", ")} (Ctrl+Z puts it back)`
        : res.done;
    } catch (err) {
      statusEl.textContent = `Delete ${name}: ${err.message}`;
    }
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && active) {
      e.preventDefault();
      close();
    }
  });

  // A click in the model browser while a pattern or mirror dialog is open picks (or unpicks) that feature
  function pickFeature(name, type) {
    if (!active || !active.def.features) return false;
    if (type === "Sketch" || name === active.edit) return true;
    const at = active.features.indexOf(name);
    if (at >= 0) active.features.splice(at, 1);
    else active.features.push(name);
    update();
    return true;
  }

  const api = {
    open,
    close,
    edit,
    remove,
    pickFeature,
    picksFeatures: () => !!(active && active.def.features),
    // The model was reloaded under an open dialog (agent, undo): the picked edges may be gone
    modelChanged() {
      if (active && active.edit) close();
      else if (active && !active.busy) {
        active.edges.clear();
        active.edge1 = null;
        active.face = null;
        update();
      }
      if (active) markTree();
    },
    isOpen: () => !!active,
  };
  return api;
}
