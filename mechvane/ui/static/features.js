// Feature dialogs of the workspace (ADR 0005, stage 2): pick in the 3D view, values in the
// Properties panel, a preview while you type, OK runs the command through /api/feature on the same
// SolidCraft session the agent uses. Each finished step lands in the shared undo list.
//
// A dialog describes its picks ("edges" or "point" on a face), its fields (number, select, check;
// shown or hidden by the other values), how the values become the command's parameters, and for
// editing how a feature's definition (timeline.inspect) becomes values and back (timeline.edit).
import * as THREE from "three";
import { profileShapes, profileAt, profileMesh, sketchLineAt, toWorld } from "./sketchgeom.js";
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
// Part files in the project folder eligible for Place (GET /api/files), loaded when Place opens
let placeFiles = [];
const PLACE_FILE_OPTIONS = () => (placeFiles.length ? placeFiles.map((f) => [f, f]) : [["", "No parts in folder"]]);
// Occurrences, world-body -> occurrence map, and existing joints (GET /api/assembly/context)
let jointContext = { occurrences: [], body_occurrences: {}, joints: [] };
const JOINT_TYPES = [
  ["rigid", "Rigid"],
  ["revolute", "Revolute"],
  ["slider", "Slider"],
  ["cylindrical", "Cylindrical"],
  ["ball", "Ball"],
];
const JOINT_COMPONENT_OPTIONS = () => (jointContext.occurrences.length
  ? jointContext.occurrences.map((o) => [o.path, o.grounded ? `${o.path} (grounded)` : o.path])
  : [["", "Place components first"]]);
const SKETCH_OPTIONS = () => sketchList.map((sk) => [sk.name,
  sk.name + (sk.used_by.length ? ` (used by ${sk.used_by.join(", ")})` : "")]);
const OPERATIONS = [["join", "Join"], ["cut", "Cut"], ["new_body", "New body"], ["intersect", "Intersect"]];
// create takes "new", the definition (and timeline.edit) "new_body"
const opParam = (op) => (op === "new_body" ? "new" : op);
// the newest sketch nothing uses yet, else the newest
const defaultSketch = () => ([...sketchList].reverse().find((sk) => !sk.used_by.length) || sketchList[sketchList.length - 1])?.name || "";
// Profile of the chosen sketch: all regions (SolidCraft's default) or one; "multi" keeps a choice of several
// made elsewhere (the agent) when the feature is edited here
const PROFILE_OPTIONS = (v) => {
  const sk = sketchList.find((x) => x.name === v?.sketch);
  const profs = sk?.profiles || [];
  const opts = [["all", profs.length > 1 ? `All ${profs.length} profiles` : "All"]];
  for (const p of profs) {
    opts.push([String(p.index), `Profile ${p.index + 1}: ${p.area} mm²${p.holes ? `, ${p.holes} hole${p.holes > 1 ? "s" : ""}` : ""}`]);
  }
  if (v?.profile === "multi") opts.push(["multi", "Several (as set)"]);
  return opts;
};
const PROFILE_FIELD = { key: "profile", label: "Profile", type: "select", value: "all", options: PROFILE_OPTIONS,
  show: (v) => (sketchList.find((x) => x.name === v.sketch)?.profiles?.length || 0) > 1 || v.profile !== "all" };
// a stored choice (loops of curves) back to profiles of the sketch
function profileValue(d, names) {
  const pr = d.profiles;
  if (!pr || pr.type === "all") return "all";
  const sk = sketchList.find((x) => x.name === (names[d.sketch] || d.sketch));
  const loops = pr.loops || [];
  const same = (a, b) => a.length === b.length && a.every((c) => b.includes(c));
  // each chosen profile is stored as its outer loop followed by one loop per hole
  const profs = sk?.profiles || [];
  const matched = [];
  let i = 0;
  while (i < loops.length) {
    const hit = profs.find((p) => same(p.curves, loops[i]) && i + 1 + (p.holes || 0) <= loops.length
      && (p.hole_loops || []).every((hl, j) => same(hl, loops[i + 1 + j])));
    if (!hit) return "multi";
    matched.push(hit.index);
    i += 1 + (hit.holes || 0);
  }
  return matched.length ? matched.join(",") : "multi";
}

function revolveAxisLabel(ax) {
  if (!ax) return "Click in view";
  if (ax.type === "world") return `${ax.axis} axis`;
  if (ax.type === "sketch_line") return `Sketch line ${ax.curve}`;
  if (ax.type === "edge") return "Clicked edge";
  return ax.label || "As set";
}

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

let boltedCache = { std: null, existing: [] };
const BOLTED_NORM_OPTIONS = () => {
  const norms = boltedCache.std?.bolted_norms || ["ISO 4762", "ISO 10642"];
  const labels = { "ISO 4762": "ISO 4762 (Cap screw)", "ISO 10642": "ISO 10642 (Countersunk)" };
  return norms.map((n) => [n, labels[n] || n]);
};
const BOLTED_SIZE_OPTIONS = (v) => {
  const norm = v?.screw_norm || "ISO 4762";
  const sizes = Object.keys(boltedCache.std?.bolted_details?.[norm]?.sizes || {});
  const list = sizes.length ? sizes : ["M3", "M4", "M5", "M6", "M8", "M10", "M12"];
  return list.map((s) => [s, s]);
};
const BOLTED_LENGTH_OPTIONS = (v) => {
  const norm = v?.screw_norm || "ISO 4762";
  const row = boltedCache.std?.bolted_details?.[norm]?.sizes?.[v?.size || "M6"];
  const lens = [...(row?.preferred_lengths || [10, 12, 16, 20, 25, 30, 35, 40, 50, 60])];
  const cur = Number(v?.length_override);
  if (Number.isFinite(cur) && cur > 0 && !lens.includes(cur)) {
    lens.push(cur);
    lens.sort((a, b) => a - b);
  }
  return [["auto", "Auto (standard fit)"], ...lens.map((l) => [String(l), `${l} mm`])];
};
const BOLTED_MATERIAL_OPTIONS = () => (boltedCache.std?.materials || ["steel", "aluminum", "brass", "cast_iron"])
  .map((m) => [m, m.replace(/_/g, " ")]);

// Place Standard Part (#88 step 3): the norms, sizes and preferred lengths of Mechvane's standard parts
let standardCache = null;
const STD_NORM_OPTIONS = () => (standardCache?.norms || []).map((n) => [n.norm, `${n.norm} · ${n.name.replace(/ \(.*\)$/, "")}`]);
const STD_SIZE_OPTIONS = (v) => Object.keys(standardCache?.details?.[v?.norm]?.sizes || {}).map((s) => [s, s]);
const STD_LENGTH_OPTIONS = (v) => (standardCache?.details?.[v?.norm]?.sizes?.[v?.size]?.preferred_lengths || [])
  .map((l) => [String(l), `${l} mm`]);
const stdHasLength = (v) => Boolean(standardCache?.details?.[v?.norm]?.has_length);

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
    status: (v, p) => {
      if (v.centre_fixed) return "centred on face";
      if ([v.x, v.y, v.z].some((c) => c === null || c === undefined || c === "")) return null;
      if (v.centre) return "Middle of the face: the hole stays in the middle when the part changes";
      if (v.edge1 === "edge" && v.edge2 === "edge") {
        if (p?.edgePicks?.length >= 2) {
          const [e1, e2] = p.edgePicks;
          if (e1?.edge?.dir && e2?.edge?.dir && e1.edge.dir.clone().cross(e2.edge.dir).length() < 1e-4) {
            return "The reference edges are parallel: pick edges that cross";
          }
        }
        return "2 edges selected: set the distances";
      }
      if (v.edge1 === "edge") return "Edge 1 selected: click a second edge, or set the distance";
      return "Face selected: click up to 2 edges for distance references, or type the position";
    },
    ready: (v, p) => {
      if (v.centre) return true;
      if ([v.x, v.y, v.z].some((c) => c === null || c === undefined || c === "")) return false;
      const n = p?.edgePicks?.length || 0;
      if (v.edge1 === "edge" && n < 1) return false;
      if (v.edge2 === "edge" && n < 2) return false;
      if (n >= 2) {
        const [e1, e2] = p.edgePicks;
        if (e1?.edge?.dir && e2?.edge?.dir && e1.edge.dir.clone().cross(e2.edge.dir).length() < 1e-4) return false;
      }
      return true;
    },
    onClear(active, set, v) {
      if (v?.centre_fixed) return;
      active.edges.clear();
      set("edge1", "none");
      set("dist1", "");
      set("edge2", "none");
      set("dist2", "");
      if (active.startFace) active.startFace();
    },
    async init(active, h) {
      function startEdges() {
        h.viewTools.startEdgePick((pick) => {
          if (!active || h.values().centre) return;
          if (pick.edge.kind !== "line") {
            h.log("pick_edge_ignored", { kind: pick.edge.kind, reason: "not_straight" });
            return;
          }
          if (active.edges.has(pick.key)) {
            active.edges.delete(pick.key);
            syncEdgesToFields();
          } else {
            if (active.edges.size >= 2) return;
            active.edges.set(pick.key, pick);
            syncEdgesToFields(pick);
          }
          h.update();
        });
      }

      function syncEdgesToFields(justAddedPick) {
        const edgeList = Array.from(active.edges.values());
        const v = h.values();
        const pt = [Number(v.x) || 0, Number(v.y) || 0, Number(v.z) || 0];
        if (edgeList.length === 0) {
          h.setValue("edge1", "none");
          h.setValue("dist1", "");
          h.setValue("edge2", "none");
          h.setValue("dist2", "");
        } else if (edgeList.length === 1) {
          h.setValue("edge1", "edge");
          if (justAddedPick && justAddedPick.key === edgeList[0].key) {
            const d = distanceToLineEdge(pt, edgeList[0].edge);
            h.setValue("dist1", fmt(Math.round(d * 10) / 10));
          }
          h.setValue("edge2", "none");
          h.setValue("dist2", "");
        } else if (edgeList.length === 2) {
          h.setValue("edge1", "edge");
          h.setValue("edge2", "edge");
          if (justAddedPick && justAddedPick.key === edgeList[1].key) {
            const d = distanceToLineEdge(pt, edgeList[1].edge);
            h.setValue("dist2", fmt(Math.round(d * 10) / 10));
          }
        }
      }

      function startFace() {
        h.viewTools.startFacePick((pick) => {
          if (!active) return;
          h.log("pick_face", { dialog: active.kind, point: pick.point.toArray().map((c) => +c.toFixed(3)),
                             normal: pick.normal.toArray().map((c) => +c.toFixed(3)), planar: pick.planar });
          const p = pick.planar ? roundOnPlane(pick.point, pick.normal) : pick.point;
          h.setValue("x", fmt(p.x));
          h.setValue("y", fmt(p.y));
          h.setValue("z", fmt(p.z));
          active.face = null;
          active.point = { direction: pick.normal.clone().negate().toArray().map((c) => +c.toFixed(6)) };
          active.edges.clear();
          h.setValue("edge1", "none");
          h.setValue("dist1", "");
          h.setValue("edge2", "none");
          h.setValue("dist2", "");
          startEdges();
          h.update();
        });
      }

      active.startEdges = startEdges;
      active.startFace = startFace;

      const v = h.values();
      if (v.centre_fixed) return;
      if (v.x !== null && v.x !== "" && v.x !== undefined) {
        startEdges();
      } else {
        startFace();
      }
    },
    // a click on a face places the hole (fallback if init not used):
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
      { key: "x", label: "X", unit: "mm", value: "", group: "position",
        show: (v) => !v.centre_fixed && v.edge1 !== "edge" },
      { key: "y", label: "Y", unit: "mm", value: "", group: "position",
        show: (v) => !v.centre_fixed && v.edge1 !== "edge" },
      { key: "z", label: "Z", unit: "mm", value: "", group: "position",
        show: (v) => !v.centre_fixed && v.edge1 !== "edge" },
      { key: "centre", label: "Middle of face", type: "check", value: false,
        show: (v) => !v.centre_fixed && v.edge1 !== "edge" },
      { key: "centre_note", label: "Position", value: "centred on face", readonly: () => true,
        show: (v) => !!v.centre_fixed },
      { key: "edge1", label: "Edge 1", type: "select", value: "none",
        options: [["none", "None"], ["edge", "Clicked edge"]], show: (v) => !v.centre },
      { key: "dist1", label: "Distance 1", unit: "mm", value: "",
        show: (v) => !v.centre && v.edge1 === "edge" },
      { key: "edge2", label: "Edge 2", type: "select", value: "none",
        options: [["none", "None"], ["edge", "Clicked edge"]],
        show: (v) => !v.centre && v.edge1 === "edge" },
      { key: "dist2", label: "Distance 2", unit: "mm", value: "",
        show: (v) => !v.centre && v.edge2 === "edge" },
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
    onChange(key, v, set, active) {
      if (key === "edge1" && v.edge1 === "none") {
        active.edges.clear();
        set("dist1", "");
        set("edge2", "none");
        set("dist2", "");
        if (active.startEdges) active.startEdges();
      }
      if (key === "edge2" && v.edge2 === "none") {
        if (active.edges.size === 2) {
          const first = Array.from(active.edges.values())[0];
          active.edges.clear();
          active.edges.set(first.key, first);
        }
        set("dist2", "");
        if (active.startEdges) active.startEdges();
      }
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
      const p = { position: [+v.x, +v.y, +v.z], diameter: v.diameter };
      if (picks.direction) p.direction = picks.direction;
      if (v.spec === "tapped") p.thread = v.size;
      if (!v.through) p.depth = v.depth;
      if (v.type === "counterbore") Object.assign(p, { type: "counterbore", cb_diameter: v.cb_diameter, cb_depth: v.cb_depth });
      if (v.type === "countersink") Object.assign(p, { type: "countersink", cs_diameter: v.cs_diameter, cs_angle: v.cs_angle });

      if (v.centre) {
        p.centre = true;  // the server ties the hole to the middle of the face (design intent rule)
        return p;
      }
      const edgeList = (picks.edgePicks || []);
      const refs = [];
      const pt = (q) => (Array.isArray(q) ? q : [q.x, q.y, q.z].map((c) => +c.toFixed(6)));
      if (v.edge1 === "edge" && edgeList[0] && v.dist1 !== null && v.dist1 !== "") {
        refs.push({ edge: pt(edgeList[0].point), distance: v.dist1 });
      }
      if (v.edge2 === "edge" && edgeList[1] && v.dist2 !== null && v.dist2 !== "") {
        refs.push({ edge: pt(edgeList[1].point), distance: v.dist2 });
      }
      if (refs.length > 0) p.references = refs;
      return p;
    },
    // timeline.edit merges into the definition: same fields, the hole type under "hole", null removes
    editSet(v, picks) {
      const hole = { type: v.type };
      if (v.type === "counterbore") Object.assign(hole, { cb_diameter: v.cb_diameter, cb_depth: v.cb_depth });
      if (v.type === "countersink") Object.assign(hole, { cs_diameter: v.cs_diameter, cs_angle: v.cs_angle });
      const set = { diameter: v.diameter, depth: v.through ? null : v.depth,
                    thread: v.spec === "tapped" ? v.size : null, hole };
      if (v.centre) {
        set.centre = true;
      } else {
        set.position = [+v.x, +v.y, +v.z];
        if (picks.direction) set.direction = picks.direction;

        const edgeList = (picks.edgePicks || []);
        const refs = [];
        const pt = (q) => (Array.isArray(q) ? q : [q.x, q.y, q.z].map((c) => +c.toFixed(6)));
        if (v.edge1 === "edge" && edgeList[0] && v.dist1 !== null && v.dist1 !== "") {
          refs.push({ edge: pt(edgeList[0].point), distance: v.dist1 });
        }
        if (v.edge2 === "edge" && edgeList[1] && v.dist2 !== null && v.dist2 !== "") {
          refs.push({ edge: pt(edgeList[1].point), distance: v.dist2 });
        }
        set.references = refs;  // an empty list removes them; SolidCraft takes no null here (#111)
      }
      return set;
    },
    fromDefinition(d) {
      const h = d.hole || {};
      const dia = parseFloat(d.diameter);
      const isCentred = !!(d.centre || (d.points && d.points.sketch && Array.isArray(d.points.ids) && d.points.ids.includes("c")));
      const v = { x: d.position?.[0], y: d.position?.[1], z: d.position?.[2], diameter: dia, type: h.type || "simple",
                  through: d.depth === undefined || d.depth === null, depth: d.depth ?? "10",
                  cb_diameter: h.cb_diameter, cb_depth: h.cb_depth, cs_diameter: h.cs_diameter, cs_angle: h.cs_angle,
                  edge1: "none", dist1: "", edge2: "none", dist2: "",
                  centre: isCentred, centre_fixed: isCentred, centre_note: "centred on face" };
      // which table entry made this diameter: a thread, a clearance hole of some fit, or neither
      if (d.thread) Object.assign(v, { spec: "tapped", size: d.thread });
      else {
        let match = null;
        for (const [size, t] of Object.entries(holeTables?.sizes || {})) {
          for (const [fit, val] of Object.entries(t.clearance)) if (!match && Math.abs(val - dia) < 1e-6) match = { size, fit };
        }
        Object.assign(v, match ? { spec: "clearance", ...match } : { spec: "diameter" });
      }
      const edgePoints = [];
      if (Array.isArray(d.references) && d.references.length > 0) {
        const refs = d.references;
        if (refs[0]) {
          v.edge1 = "edge";
          v.dist1 = refs[0].distance;
          edgePoints.push(refs[0].edge);
        }
        if (refs[1]) {
          v.edge2 = "edge";
          v.dist2 = refs[1].distance;
          edgePoints.push(refs[1].edge);
        }
      }
      return { values: v, direction: d.direction, edges: edgePoints };
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
      // the profile choice is made by clicking in the view; this keeps it for editing (see init)
      { ...PROFILE_FIELD, show: () => false },
    ],
    // a cut usually goes into the material, against the face's outward side
    onChange(key, v, set, active) {
      if (key === "operation" && v.operation === "cut" && v.direction === "positive") set("direction", "negative");
      if (key === "operation" && v.operation !== "cut" && v.direction === "negative") set("direction", "positive");
      if (key === "sketch" && active?.startProfilePick) active.startProfilePick(v.sketch, "fresh");
    },
    // Profiles as in Inventor: one closed region is picked for you, several are clicked in the view
    async init(active, h) {
      active.startProfilePick = (name, from) => {
        const sk = sketchList.find((x) => x.name === name);
        active.prof = { sketch: sk, shapes: sk?.plane ? profileShapes(sk) : [], picked: new Set(), touched: false };
        const n = active.prof.shapes.length;
        const val = h.values().profile;
        if (from !== "fresh" && val === "all") active.prof.shapes.forEach((x) => active.prof.picked.add(x.index));
        else if (from !== "fresh" && /^\d+(,\d+)*$/.test(String(val))) {
          String(val).split(",").forEach((i) => active.prof.picked.add(Number(i)));
        }
        else if (from !== "fresh" && val === "multi") active.prof.keep = true;  // the agent's own choice: kept unless clicked
        else if (n === 1) active.prof.picked.add(active.prof.shapes[0].index);
        if (from === "fresh") active.prof.touched = true;
        if (sk?.plane && n) {
          h.viewTools.startPlanePick(sk.plane, ([u, w]) => {
            const hit = profileAt(active.prof.shapes, [u, w]);
            if (!hit) return;
            const p = active.prof;
            if (p.picked.has(hit.index)) p.picked.delete(hit.index); else p.picked.add(hit.index);
            p.touched = true;
            p.keep = false;
            h.log?.("pick_profile", { sketch: name, profile: hit.index, picked: p.picked.size });
            h.update();
          });
        } else h.viewTools.stopEdgePick();
        h.update();
      };
      // a stored choice only when editing; a new extrusion starts from nothing (one profile: that one)
      active.startProfilePick(h.values().sketch, active.edit ? "edit" : "fresh");
    },
    draw(active, v, add, addMesh) {
      const p = active.prof;
      if (!p?.sketch?.plane) return;
      for (const shape of p.shapes) {
        const on = p.picked.has(shape.index) || p.keep;
        addMesh(profileMesh(p.sketch.plane, shape, on ? 0x58a6ff : 0x8b949e, on ? 0.45 : 0.12));
        add(toWorld(p.sketch.plane, [...shape.outer, shape.outer[0]]), on ? 0x58a6ff : 0x8b949e);
      }
    },
    ready: (v, pk, active) => !!v.sketch && !!(active?.prof?.picked.size || active?.prof?.keep),
    status: (v, pk, active) => {
      if (!sketchList.length) return "This part has no sketch yet: make one with Create 2D Sketch (S), or ask your agent";
      const p = active?.prof;
      if (!p || !p.shapes.length) return null;
      if (p.keep) return "Extrudes the profiles chosen before; click profiles in the view to choose again";
      const n = p.shapes.length, k = p.picked.size;
      if (!k) return `Click the profile${n > 1 ? "s" : ""} to extrude in the view (${n} in ${v.sketch})`;
      return n > 1 ? `${k} of ${n} profiles selected · click in the view to add or remove` : null;
    },
    params(v, pk, active) {
      const p = { sketch: v.sketch, operation: opParam(v.operation), direction: v.direction };
      const pr = active?.prof;
      if (pr && pr.picked.size && pr.picked.size < pr.shapes.length) p.profiles = [...pr.picked].sort((a, b) => a - b);
      if (v.through) p.through_all = true;
      else p.distance = v.distance;
      return p;
    },
    editSet(v, pk, active) {
      const set = { sketch: v.sketch, operation: v.operation,
                    extent: { direction: v.direction, through_all: !!v.through, distance: v.through ? "0" : String(v.distance) } };
      const pr = active?.prof;
      if (pr && pr.touched && pr.picked.size) {
        set.profiles = pr.picked.size === pr.shapes.length ? "all" : [...pr.picked].sort((a, b) => a - b);
      }
      return set;
    },
    fromDefinition(d, names) {
      const e = d.extent || {};
      return { values: { sketch: names[d.sketch] || d.sketch, profile: profileValue(d, names), operation: d.operation || "join", direction: e.direction || "positive",
                         through: !!e.through_all, distance: e.through_all ? "10" : e.distance } };
    },
  },
  revolve: {
    title: "Revolve",
    command: "solid.revolve",
    hint: "Choose the profile and axis in the view",
    needs: async (get) => { sketchList = (await get("api/sketches")).sketches || []; },
    fields: [
      { key: "sketch", label: "Sketch", type: "select", value: defaultSketch, options: SKETCH_OPTIONS },
      { key: "profile", label: "Profile", type: "pick", value: "Click in view" },
      { key: "axis", label: "Axis", type: "pick", value: "Click in view" },
      { key: "angle", label: "Angle", unit: "°", value: "360" },
      { key: "operation", label: "Operation", type: "select", value: "join", options: OPERATIONS },
    ],
    onChange(key, v, set, active) {
      if (key === "sketch" && active?.startRevolvePick) active.startRevolvePick(v.sketch, "fresh");
    },
    // Profiles and axis as in Inventor and SolidCraft (dialogs.rs): two selection fields (Profile, Axis),
    // the active field decides what a click in the view selects; Tab or clicking a field switches between them.
    // When a sketch has one closed region, it is preselected and Axis is active right away.
    async init(active, h) {
      const syncSlots = () => {
        const p = active.prof;
        const n = p?.shapes?.length || 0, k = p?.picked?.size || 0;
        h.setValue("profile", p?.keep ? "As set" : !k ? "Click in view" : n === 1 ? "1 profile" : `${k} of ${n} profiles`);
        h.setValue("axis", revolveAxisLabel(active.axis));
      };
      active.setSlot = (slot) => {
        if (slot !== "profile" && slot !== "axis") return;
        active.slot = slot;
        h.revealOriginAxes?.(slot === "axis");
        syncSlots();
        h.log?.("dialog_slot", { dialog: active.kind, slot });
        h.update();
      };
      active.startRevolvePick = (name, from) => {
        const sk = sketchList.find((x) => x.name === name);
        active.prof = { sketch: sk, shapes: sk?.plane ? profileShapes(sk) : [], picked: new Set(), touched: false };
        const n = active.prof.shapes.length;
        const val = active.fromProfile;
        if (from !== "fresh" && val === "all") active.prof.shapes.forEach((x) => active.prof.picked.add(x.index));
        else if (from !== "fresh" && /^\d+(,\d+)*$/.test(String(val || ""))) {
          String(val).split(",").forEach((i) => active.prof.picked.add(Number(i)));
        } else if (from !== "fresh" && val === "multi") active.prof.keep = true;
        else if (n === 1) active.prof.picked.add(active.prof.shapes[0].index);
        if (from === "fresh") {
          active.prof.touched = true;
          if (active.axis?.type === "sketch_line") active.axis = null;
          active.slot = n === 1 ? "axis" : "profile";
        } else {
          active.slot = active.axis || active.prof.picked.size || active.prof.keep ? "axis" : "profile";
        }
        h.revealOriginAxes?.(active.slot === "axis");
        syncSlots();
        if (sk?.plane) {
          h.viewTools.startPlanePick(sk.plane, (uv, _at, info) => {
            if (!active) return;
            if (active.slot === "profile") {
              const hit = uv && profileAt(active.prof.shapes, uv);
              if (!hit) return;
              const p = active.prof;
              if (p.picked.has(hit.index)) p.picked.delete(hit.index); else p.picked.add(hit.index);
              p.touched = true;
              p.keep = false;
              syncSlots();
              h.log?.("pick_profile", { sketch: name, profile: hit.index, picked: p.picked.size });
              h.update();
              return;
            }
            const line = uv && sketchLineAt(sk, uv, info?.planeTol ?? 3);
            const edgePick = info?.edge?.();
            const orig = info && h.originAxisAt?.(info.clientX, info.clientY);
            const linePx = line ? (line.dist * 10) / Math.max(info?.planeTol || 3, 1e-6) : Infinity;
            const edgePx = edgePick ? edgePick.dist : Infinity;
            const origPx = orig ? orig.dist : Infinity;
            if (line && linePx - 1.5 <= Math.min(edgePx, origPx)) {
              active.axis = { type: "sketch_line", curve: line.id };
              active.edge1 = null;
              h.log?.("pick_axis", { kind: "sketch_line", curve: line.id });
            } else if (edgePick && edgePx <= origPx) {
              active.edge1 = edgePick;
              active.axis = { type: "edge", point: edgePick.point };
              h.log?.("pick_axis", { kind: "edge", point: edgePick.point });
            } else if (orig) {
              active.axis = { type: "world", axis: orig.axis };
              active.edge1 = null;
              h.log?.("pick_axis", { kind: "world", axis: orig.axis });
            } else {
              return;
            }
            syncSlots();
            h.update();
          });
        } else h.viewTools.stopEdgePick();
        h.update();
      };
      active.pickOrigin = (axis) => {
        if (!AXES[axis]) return false;
        active.axis = { type: "world", axis };
        active.edge1 = null;
        active.slot = "axis";
        h.revealOriginAxes?.(true);
        syncSlots();
        h.log?.("pick_axis", { kind: "world", axis });
        h.update();
        return true;
      };
      active.startRevolvePick(h.values().sketch, active.edit ? "edit" : "fresh");
    },
    draw(active, v, add, addMesh) {
      const p = active.prof;
      if (p?.sketch?.plane) {
        for (const shape of p.shapes) {
          const on = p.picked.has(shape.index) || p.keep;
          addMesh(profileMesh(p.sketch.plane, shape, on ? 0x58a6ff : 0x8b949e, on ? 0.45 : 0.12));
          add(toWorld(p.sketch.plane, [...shape.outer, shape.outer[0]]), on ? 0x58a6ff : 0x8b949e);
        }
        for (const c of p.sketch.curves || []) {
          if (c.type !== "line" || !c.start_at || !c.end_at) continue;
          const on = active.axis?.type === "sketch_line" && active.axis.curve === c.id;
          if (on || c.construction) {
            add(toWorld(p.sketch.plane, [c.start_at, c.end_at]), on ? 0x58a6ff : 0x8b949e);
          }
        }
      }
      if (active.axis?.type === "world" && AXES[active.axis.axis]) {
        const d = new THREE.Vector3(...AXES[active.axis.axis]);
        add([d.clone().multiplyScalar(-50), d.clone().multiplyScalar(50)], 0x58a6ff);
      }
    },
    ready: (v, pk, active) => !!v.sketch && !!(active?.prof?.picked.size || active?.prof?.keep) && !!active?.axis,
    status: (v, pk, active) => {
      if (!sketchList.length) return "This part has no sketch yet: make one with Create 2D Sketch (S), or ask your agent";
      const p = active?.prof;
      if (!p || !p.shapes.length) return null;
      const n = p.shapes.length, k = p.picked.size;
      const hasProf = k > 0 || p.keep;
      const ax = active?.axis;
      if (!hasProf) return `Click the profile${n > 1 ? "s" : ""} to revolve in the view (${n} in ${v.sketch})`;
      if (!ax) {
        return active.slot === "profile"
          ? `${k} of ${n} profiles selected · click Axis (or press Tab), then click a sketch line, model edge or origin axis`
          : "Click a sketch line, model edge or origin axis in the view for the axis";
      }
      if (active.slot === "profile") {
        return p.keep
          ? "Revolves the profiles chosen before · click profiles in the view to choose again"
          : `${k} of ${n} profile${n > 1 ? "s" : ""} selected · click in the view to add or remove`;
      }
      return `${n > 1 ? `${k} of ${n} profiles · ` : ""}${revolveAxisLabel(ax)} · click in the view to change`;
    },
    params(v, pk, active) {
      const ax = active?.axis;
      const axis = ax?.type === "world" ? ax.axis
        : ax?.type === "sketch_line" ? ax.curve
        : { edge: ax?.point || pk.edge1?.point };
      const out = { sketch: v.sketch, axis, angle: deg(v.angle), operation: opParam(v.operation) };
      const pr = active?.prof;
      if (pr && pr.picked.size && pr.picked.size < pr.shapes.length) out.profiles = [...pr.picked].sort((a, b) => a - b);
      return out;
    },
    editSet(v, pk, active) {
      const set = { sketch: v.sketch, angle: deg(v.angle), operation: v.operation };
      const pr = active?.prof;
      if (pr && pr.touched && pr.picked.size) {
        set.profiles = pr.picked.size === pr.shapes.length ? "all" : [...pr.picked].sort((a, b) => a - b);
      }
      const ax = active?.axis;
      if (ax?.type === "world") set.axis = { type: "world", axis: ax.axis };
      else if (ax?.type === "sketch_line") set.axis = { type: "sketch_line", curve: ax.curve };
      else if (ax?.keep) set.axis = ax.keep;
      else if (ax?.type === "edge") set.axis = { type: "model", geo: { type: "edge", at: ax.point } };
      return set;
    },
    fromDefinition(d, names) {
      const a = d.axis || {};
      let axis = null, edge1 = null;
      if (a.type === "world") axis = { type: "world", axis: a.axis };
      else if (a.type === "sketch_line") axis = { type: "sketch_line", curve: a.curve };
      else if (a.type === "model" && a.geo?.at) {
        axis = { type: "edge", point: a.geo.at, keep: a };
        edge1 = { point: a.geo.at, keep: a };
      } else if (a.type) {
        axis = { type: "keep", keep: a, label: a.type === "sketch_axis" ? `Sketch ${a.axis}` : "As set" };
      }
      return {
        values: {
          sketch: names[d.sketch] || d.sketch,
          angle: String(d.angle ?? "360").replace(/\s*deg$/, ""),
          operation: d.operation || "join",
        },
        profile: profileValue(d, names),
        axis,
        edge1,
      };
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
  // Place dialog for assemblies (POST /api/assembly/insert).
  // Deviation from SolidCraft (dialogs_assembly.rs): SolidCraft has no Place parameters dialog and
  // instead inserts designs via an open-designs menu or OS file picker without XYZ or Grounded inputs;
  // Mechvane follows its feature-dialog pattern with folder file list, Name, Translation/Rotation XYZ, and Grounded.
  place: {
    title: "Place",
    endpoint: "api/assembly/insert",
    noPreview: true,
    hint: "Choose a part from the project folder",
    needs: async (get) => {
      const d = await get("api/files");
      const selfName = d.document || "";
      placeFiles = (d.parts || d.files || []).filter((f) => f !== selfName);
    },
    fields: [
      { key: "file", label: "File", type: "select", value: () => placeFiles[0] || "", options: PLACE_FILE_OPTIONS },
      { key: "name", label: "Name", type: "text", value: "", placeholder: "Optional" },
      { key: "tx", label: "Move X", unit: "mm", value: "0", group: "position" },
      { key: "ty", label: "Move Y", unit: "mm", value: "0", group: "position" },
      { key: "tz", label: "Move Z", unit: "mm", value: "0", group: "position" },
      { key: "rx", label: "Rotate X", unit: "°", value: "0", group: "rotation" },
      { key: "ry", label: "Rotate Y", unit: "°", value: "0", group: "rotation" },
      { key: "rz", label: "Rotate Z", unit: "°", value: "0", group: "rotation" },
      { key: "grounded", label: "Grounded", type: "select", value: "",
        options: [["", "Auto (first grounded)"], ["true", "Yes (grounded)"], ["false", "No (free)"]] },
    ],
    ready: (v) => Boolean(v.file),
    status: (v) => (!v.file ? "No other .solidcraft parts found in project folder" : `Place ${v.file}`),
    params(v) {
      const out = {
        file: v.file,
        translate: [v.tx || 0, v.ty || 0, v.tz || 0],
        rotate: [v.rx || 0, v.ry || 0, v.rz || 0],
      };
      if (v.name) out.name = v.name;
      if (v.grounded !== "") out.grounded = v.grounded === "true";
      return out;
    },
  },
  // Place Standard Part (POST /api/assembly/standard). Inventor places from the Content Center; Mechvane makes the
  // parametric part file in the folder (as the MCP tool standard_part does, reused when it exists) and places it.
  // SolidCraft has no standard part library of its own, so there is no dialog there to follow.
  place_standard: {
    title: "Place Standard Part",
    endpoint: "api/assembly/standard",
    noPreview: true,
    hint: "Choose a norm, a size and a length",
    needs: async (get) => {
      standardCache = standardCache || await get("api/standard_parts");
    },
    fields: [
      { key: "norm", label: "Norm", type: "select", value: () => standardCache?.norms?.[0]?.norm || "", options: STD_NORM_OPTIONS },
      { key: "size", label: "Size", type: "select", value: "M6", options: STD_SIZE_OPTIONS },
      { key: "length", label: "Length", type: "select", value: "", options: STD_LENGTH_OPTIONS, show: stdHasLength },
      { key: "tx", label: "Move X", unit: "mm", value: "0", group: "position" },
      { key: "ty", label: "Move Y", unit: "mm", value: "0", group: "position" },
      { key: "tz", label: "Move Z", unit: "mm", value: "0", group: "position" },
      { key: "grounded", label: "Grounded", type: "select", value: "false",
        options: [["false", "No (free)"], ["true", "Yes (grounded)"], ["", "Auto (first grounded)"]] },
    ],
    onChange(key, v, setValue) {
      // a size or length the new norm or size does not have falls back to its first one
      if (key === "norm" || key === "size") {
        const sizes = STD_SIZE_OPTIONS(v).map((o) => o[0]);
        if (key === "norm" && !sizes.includes(v.size)) setValue("size", sizes.includes("M6") ? "M6" : sizes[0] || "");
        const lens = STD_LENGTH_OPTIONS({ ...v, size: key === "norm" && !sizes.includes(v.size) ? (sizes.includes("M6") ? "M6" : sizes[0]) : v.size }).map((o) => o[0]);
        if (!lens.includes(String(v.length))) setValue("length", lens.includes("20") ? "20" : lens[0] || "");
      }
    },
    ready: (v) => Boolean(v.norm && v.size && (!stdHasLength(v) || v.length)),
    status: (v) => (!v.norm ? "No standard parts available" : stdHasLength(v) && !v.length
      ? "Choose a length" : `Place ${v.norm} ${v.size}${stdHasLength(v) ? `x${v.length}` : ""}`),
    params(v) {
      const out = { norm: v.norm, size: v.size, translate: [v.tx || 0, v.ty || 0, v.tz || 0] };
      if (stdHasLength(v)) out.length = Number(v.length);
      if (v.grounded !== "") out.grounded = v.grounded === "true";
      return out;
    },
  },
  // Joint dialog for assemblies (POST /api/assembly/joint and POST /api/assembly/joint/edit).
  // Built against the SolidCraft CLI command schema for joint.create / joint.edit and Inventor's
  // Joint dialog workflow (two component origins, type: rigid/revolute/slider/cylindrical/ball,
  // flip, axial offset in mm, angle in deg).
  // Deviation from SolidCraft (crates/ui-egui/src/dialogs_assembly.rs, compared 2026-11-15): SolidCraft
  // offers 13 types (TYPES, also pin_slot, planar and the relations parallel/perpendicular/angle/
  // point_on_*/line_on_plane), limits and a driven live preview (world_preview). This dialog is the
  // first step of #88 with the five types the issue asks for, no limits and no preview; those can follow.
  joint: {
    title: "Joint",
    endpoint: (dlg) => (dlg?.edit ? "api/assembly/joint/edit" : "api/assembly/joint"),
    noPreview: true,
    slots: ["origin_a", "origin_b"],
    hint: "Click a face on the first component",
    needs: async (get) => {
      jointContext = await get("api/assembly/context");
    },
    fields: [
      { key: "type", label: "Type", type: "select", value: "rigid", options: JOINT_TYPES },
      { key: "comp_a", label: "Component 1", type: "select",
        value: () => jointContext.occurrences[0]?.path || "", options: JOINT_COMPONENT_OPTIONS },
      { key: "origin_a", label: "Origin 1", type: "pick", value: "Click face 1 in 3D view" },
      { key: "comp_b", label: "Component 2", type: "select",
        value: () => jointContext.occurrences[1]?.path || jointContext.occurrences[0]?.path || "", options: JOINT_COMPONENT_OPTIONS },
      { key: "origin_b", label: "Origin 2", type: "pick", value: "Click face 2 in 3D view" },
      { key: "name", label: "Name", type: "text", value: "", placeholder: "Optional" },
      { key: "flip", label: "Flip", type: "check", value: false },
      { key: "offset", label: "Offset", unit: "mm", value: "0", show: (v) => v.type !== "ball" },
      { key: "angle", label: "Angle", unit: "°", value: "0", show: (v) => v.type === "revolute" || v.type === "cylindrical" },
    ],
    loadEdit(edit, active, setValue) {
      setValue("type", edit.type || "rigid");
      setValue("comp_a", edit.occurrence_a || "");
      setValue("comp_b", edit.occurrence_b || "");
      setValue("name", edit.name || "");
      setValue("flip", !!edit.flip);
      setValue("offset", String(edit.offset ?? 0));
      setValue("angle", String(edit.angle ?? 0));
      const aLabel = edit.anchors?.a?.face ? `${edit.occurrence_a} · ${edit.anchors.a.face} (keep)` : `${edit.occurrence_a || "Origin 1"} (keep)`;
      const bLabel = edit.anchors?.b?.face ? `${edit.occurrence_b} · ${edit.anchors.b.face} (keep)` : `${edit.occurrence_b || "Origin 2"} (keep)`;
      setValue("origin_a", aLabel);
      setValue("origin_b", bLabel);
      active.jointFrames = { a: edit.frame_a || null, b: edit.frame_b || null };
      active.origCompA = edit.occurrence_a || "";
      active.origCompB = edit.occurrence_b || "";
      active.keepA = Boolean(edit.occurrence_a);
      active.keepB = Boolean(edit.occurrence_b);
      active.jointA = null;
      active.jointB = null;
    },
    onChange(key, v, setValue, active) {
      if (!active) return;
      if (key === "comp_a" && (!active.jointA || active.jointA.occurrence !== v.comp_a)) {
        active.jointA = null;
        active.keepA = false;
        setValue("origin_a", "Click face 1 in 3D view");
        active.slot = "origin_a";
      } else if (key === "comp_b" && (!active.jointB || active.jointB.occurrence !== v.comp_b)) {
        active.jointB = null;
        active.keepB = false;
        setValue("origin_b", "Click face 2 in 3D view");
        active.slot = "origin_b";
      }
    },
    hasClear: (active) => Boolean(active.jointA || active.jointB),
    onClear(active, setValue) {
      active.jointA = null;
      active.jointB = null;
      active.keepA = false;
      active.keepB = false;
      setValue("origin_a", "Click face 1 in 3D view");
      setValue("origin_b", "Click face 2 in 3D view");
      active.setSlot?.("origin_a");
    },
    async init(active, h) {
      active.jointA = active.jointA || null;
      active.jointB = active.jointB || null;
      active.slot = "origin_a";
      h.revealOriginAxes?.(true);
      const ORIGIN_KEYS = { XY: "plane", XZ: "plane", YZ: "plane", X: "axis", Y: "axis", Z: "axis" };
      const applySidePick = (slot, data) => {
        if (slot === "origin_a") {
          active.jointA = data;
          active.keepA = false;
          h.setValue("comp_a", data.occurrence);
          h.setValue("origin_a", data.label);
          if (!active.jointB && !active.keepB) active.slot = "origin_b";
        } else {
          active.jointB = data;
          active.keepB = false;
          h.setValue("comp_b", data.occurrence);
          h.setValue("origin_b", data.label);
        }
        h.revealOriginAxes?.(true);
        h.update();
      };
      active.setSlot = (next) => {
        active.slot = next === "origin_b" ? "origin_b" : "origin_a";
        h.revealOriginAxes?.(true);
        h.update();
      };
      active.pickOrigin = (name) => {
        const kind = ORIGIN_KEYS[name];
        if (!kind) return false;
        const slot = active.slot === "origin_b" ? "origin_b" : "origin_a";
        const v = h.values();
        const occ = slot === "origin_a" ? v.comp_a : v.comp_b;
        if (!occ) return false;
        const side = { occurrence: occ, label: `${occ} · ${name}` };
        side[kind] = name;
        h.log?.("pick_joint_origin", { slot, occurrence: occ, [kind]: name });
        applySidePick(slot, side);
        return true;
      };
      h.viewTools.startFacePick((pick) => {
        if (!active) return;
        const occ = jointContext.body_occurrences?.[pick.body];
        if (!occ) return;
        const pt = pick.point.toArray().map((c) => +c.toFixed(6));
        const n = pick.normal.toArray().map((c) => +c.toFixed(6));
        const slot = active.slot === "origin_b" ? "origin_b" : "origin_a";
        const short = pt.map((c) => fmt(c)).join(", ");
        const label = pick.faceName ? `${occ} · ${pick.faceName}` : `${occ} (${short})`;
        h.log?.("pick_joint_face", { slot, occurrence: occ, face: pick.faceName || null, point: pt });
        // the Constrain dialog takes a round face as an axis reference (circle), a flat one as a plane (face)
        const key = active.kind === "constrain" && !pick.planar ? "circle" : "face";
        applySidePick(slot, { occurrence: occ, [key]: pt, normal: n, label });
      });
    },
    draw(active, v, add, addMesh) {
      const ms = Math.max(active.markerSize || 1, 0.25);
      const drawSide = (side, frame, color) => {
        const pt = side?.face || side?.circle || frame?.origin;
        const norm = side?.normal || frame?.z;
        if (!pt) return;
        const at = new THREE.Vector3(...pt);
        const dot = new THREE.Mesh(
          new THREE.SphereGeometry(ms, 16, 12),
          new THREE.MeshBasicMaterial({ color, depthTest: false }),
        );
        dot.position.copy(at);
        dot.renderOrder = 22;
        addMesh(dot);
        if (norm) {
          const end = at.clone().addScaledVector(new THREE.Vector3(...norm), ms * 10);
          add([at, end], color);
        }
      };
      drawSide(active.jointA, active.keepA ? active.jointFrames?.a : null, PICK_COLOR);
      drawSide(active.jointB, active.keepB ? active.jointFrames?.b : null, 0x3fb950);
    },
    ready(v, _pk, active) {
      if (jointContext.occurrences.length < 2) return false;
      if (!v.comp_a || !v.comp_b || v.comp_a === v.comp_b) return false;
      const hasA = Boolean(active?.jointA || (active?.edit && active?.keepA && v.comp_a === active.origCompA));
      const hasB = Boolean(active?.jointB || (active?.edit && active?.keepB && v.comp_b === active.origCompB));
      return hasA && hasB;
    },
    status(v, _pk, active) {
      if (jointContext.occurrences.length < 2) return "Place at least two components before creating a joint";
      if (v.comp_a && v.comp_b && v.comp_a === v.comp_b) return "Choose two different components (Component 1 and Component 2 must differ)";
      const hasA = Boolean(active?.jointA || (active?.edit && active?.keepA && v.comp_a === active.origCompA));
      const hasB = Boolean(active?.jointB || (active?.edit && active?.keepB && v.comp_b === active.origCompB));
      if (!hasA) return "Origin 1: click a face in the 3D view (or Origin plane/axis)";
      if (!hasB) return "Origin 2: click a face on the second component";
      return `Ready: ${v.type} between ${v.comp_a} and ${v.comp_b}`;
    },
    params(v, _pk, active) {
      const strip = (s) => {
        if (!s) return undefined;
        const out = { occurrence: s.occurrence };
        for (const k of ["face", "point", "circle", "edge", "plane", "axis", "frame"]) {
          if (s[k] !== undefined) out[k] = s[k];
        }
        return out;
      };
      const req = { type: v.type, flip: !!v.flip };
      if (active?.edit) req.joint = active.edit;
      if (v.name) req.name = v.name;
      const sideA = strip(active?.jointA);
      const sideB = strip(active?.jointB);
      if (sideA) req.a = sideA;
      if (sideB) req.b = sideB;
      if (v.type !== "ball" && v.offset !== null && v.offset !== "") req.offset = v.offset;
      if ((v.type === "revolute" || v.type === "cylindrical") && v.angle !== null && v.angle !== "") req.angle = v.angle;
      return req;
    },
  },
  // Bolted Connection dialog for assemblies (POST /api/assembly/bolted/*).
  // Deviation from SolidCraft: SolidCraft has no bolted connection generator dialog (bolted connections
  // are a Mechvane layer on top of SolidCraft); Mechvane follows Inventor's Bolted Connection Generator
  // (placement point/hole + standard screw/washer/nut stack + live preview + list/edit/delete of existing).
  bolted: {
    title: "Bolted Connection",
    previewEndpoint: "api/assembly/bolted/preview",
    endpoint: (dlg) => (dlg.boltedEditId ? "api/assembly/bolted/edit" : "api/assembly/bolted/create"),
    hint: "Click a hole or flat face in the 3D view, or type X/Y/Z",
    extraHtml: `<div class="bolted-existing"></div>`,
    needs: async (get) => {
      const [std, existing] = await Promise.all([
        get("api/standard_parts"),
        get("api/assembly/bolted"),
      ]);
      boltedCache.std = std;
      boltedCache.existing = existing.items || [];
    },
    fields: [
      { key: "name", label: "Name", type: "text", value: "", placeholder: "Auto", show: (_v, dlg) => !dlg?.boltedEditId },
      { key: "x", label: "X", unit: "mm", value: "", group: "position" },
      { key: "y", label: "Y", unit: "mm", value: "", group: "position" },
      { key: "z", label: "Z", unit: "mm", value: "", group: "position" },
      { key: "flip", label: "Flip direction", type: "check", value: false },
      { key: "screw_norm", label: "Standard", type: "select", value: "ISO 4762", options: BOLTED_NORM_OPTIONS },
      { key: "size", label: "Size", type: "select", value: "M6", options: BOLTED_SIZE_OPTIONS },
      { key: "length_override", label: "Length", type: "select", value: "auto", options: BOLTED_LENGTH_OPTIONS },
      { key: "connection_type", label: "Type", type: "select", value: "through",
        options: [["through", "Through + nut"], ["blind", "Blind tapped"], ["insert", "Ruthex insert"]] },
      { key: "fit", label: "Fit", type: "select", value: "normal",
        options: [["close", "Close"], ["normal", "Normal"], ["loose", "Loose"]] },
      { key: "blind_material", label: "Material", type: "select", value: "steel", options: BOLTED_MATERIAL_OPTIONS,
        show: (v) => v.connection_type === "blind" },
      { key: "counterbore", label: "Counterbore", type: "check", value: true, show: (v) => v.screw_norm !== "ISO 10642" },
      { key: "washer_head", label: "Head washer (ISO 7089)", type: "check", value: true, show: (v) => v.screw_norm !== "ISO 10642" },
      { key: "washer_nut", label: "Nut washer (ISO 7089)", type: "check", value: true, show: (v) => v.connection_type === "through" },
    ],
    ready: (v) => [v.x, v.y, v.z].every((c) => typeof c === "number"),
    status: (v, _p, dlg) => {
      if (dlg?.boltedEditId) return `Editing ${dlg.boltedEditId} (${v.screw_norm} ${v.size})`;
      if ([v.x, v.y, v.z].every((c) => typeof c === "number")) {
        return `${v.screw_norm} ${v.size} at (${v.x}, ${v.y}, ${v.z})`;
      }
      return "Click a hole or flat face in the 3D view, or type X/Y/Z";
    },
    sourceNote: (v) => {
      const parts = [v.screw_norm || "ISO 4762", "clearance hole ISO 273"];
      if (v.connection_type === "through") parts.push("nut ISO 4032");
      if (v.connection_type === "insert") parts.push("Ruthex insert");
      if (v.washer_head || v.washer_nut) parts.push("washer ISO 7089");
      return parts.join(" · ");
    },
    onChange(changed, v, set) {
      if (changed === "screw_norm") {
        const isCs = v.screw_norm === "ISO 10642";
        set("counterbore", !isCs);
        set("washer_head", !isCs);
      }
      if (changed === "connection_type") {
        set("washer_nut", v.connection_type === "through");
      }
    },
    describePreview: (res) => {
      const stack = (res.parts || []).map((p) => p.occurrence).join(" → ");
      const len = res.selected_screw_length ? ` × ${res.selected_screw_length} mm` : "";
      const cb = res.counterbore ? " · counterbored" : "";
      return `${res.screw_norm} ${res.size}${len} · stack ${res.stack_thickness} mm · ${res.fit} Ø${res.clearance_diameter} mm${cb}${stack ? ` · ${stack}` : ""}`;
    },
    params(v, _p, dlg) {
      const baseDir = dlg.boltedDirection || [0, 0, -1];
      const dir = v.flip ? baseDir.map((c) => -c) : baseDir;
      const out = {
        placement: { type: "point", position: [v.x, v.y, v.z], direction: dir },
        screw_norm: v.screw_norm || "ISO 4762",
        size: v.size || "M6",
        fit: v.fit || "normal",
        connection_type: v.connection_type || "through",
        counterbore: v.screw_norm === "ISO 10642" ? false : !!v.counterbore,
        washer_head: v.screw_norm === "ISO 10642" ? false : !!v.washer_head,
        washer_nut: v.connection_type === "through" ? !!v.washer_nut : false,
        length_override: v.length_override === "auto" ? null : Number(v.length_override),
      };
      if (v.connection_type === "blind") out.blind_material = v.blind_material || "steel";
      if (v.name && !dlg.boltedEditId) out.name = v.name;
      if (dlg.boltedEditId) out.id = dlg.boltedEditId;
      return out;
    },
    previewParams(v, _p, dlg) {
      const out = DIALOGS.bolted.params(v, _p, dlg);
      if (dlg.boltedEditId) out.edit_id = dlg.boltedEditId;
      return out;
    },
    draw(active, v, add, addMesh) {
      if (![v.x, v.y, v.z].every((c) => typeof c === "number")) return;
      const prev = active.previewData;
      const baseDir = active.boltedDirection || [0, 0, -1];
      const dirArr = prev?.direction || (v.flip ? baseDir.map((c) => -c) : baseDir);
      const dir = new THREE.Vector3(...dirArr).normalize();
      const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      const pts = prev?.points || [[v.x, v.y, v.z]];
      const mat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.45, depthWrite: false });
      const cylAt = (center, rTop, rBot, h, radial = 20) => {
        if (!(h > 0 && rTop > 0 && rBot > 0)) return;
        const m = new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBot, h, radial), mat);
        m.position.copy(center);
        m.quaternion.copy(quat);
        m.renderOrder = 21;
        addMesh(m);
      };
      for (const p of pts) {
        const at = new THREE.Vector3(...p);
        add([at, at.clone().addScaledVector(dir, prev?.selected_screw_length || 20)], PICK_COLOR);
        if (!prev?.dims) continue;
        const d = prev.dims;
        const cbOffset = prev.counterbore && prev.cb_depth ? prev.cb_depth : 0;
        let bearing = at.clone().addScaledVector(dir, cbOffset);
        if (prev.washer_head && prev.head !== "countersunk") {
          cylAt(bearing.clone().addScaledVector(dir, -d.washer_h / 2), d.washer_d2 / 2, d.washer_d2 / 2, d.washer_h);
          bearing = bearing.clone().addScaledVector(dir, -d.washer_h);
        }
        if (prev.head === "countersunk") {
          cylAt(bearing.clone().addScaledVector(dir, d.k / 2), d.d / 2, d.dk / 2, d.k);
          const L = prev.selected_screw_length || 20;
          cylAt(bearing.clone().addScaledVector(dir, L / 2), d.d / 2, d.d / 2, L);
        } else {
          cylAt(bearing.clone().addScaledVector(dir, -d.k / 2), d.dk / 2, d.dk / 2, d.k);
          const L = prev.selected_screw_length || 20;
          cylAt(bearing.clone().addScaledVector(dir, L / 2), d.d / 2, d.d / 2, L);
        }
        if (prev.connection_type === "through" && prev.total_thickness > 0) {
          let nutBase = at.clone().addScaledVector(dir, prev.total_thickness);
          if (prev.washer_nut) {
            cylAt(nutBase.clone().addScaledVector(dir, d.washer_h / 2), d.washer_d2 / 2, d.washer_d2 / 2, d.washer_h);
            nutBase = nutBase.clone().addScaledVector(dir, d.washer_h);
          }
          const nutR = d.nut_s / Math.sqrt(3);
          cylAt(nutBase.clone().addScaledVector(dir, d.nut_m / 2), nutR, nutR, d.nut_m, 6);
        }
      }
    },
    init(active, h) {
      active.boltedDirection = [0, 0, -1];
      active.boltedEditId = active.boltedEditId || null;
      active.previewData = null;
      const box = active.form.querySelector(".bolted-existing");
      const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      const titleEl = active.form.querySelector(".feature-dialog-title");

      const loadConn = (c) => {
        if (!c) return;
        active.boltedEditId = c.id;
        titleEl.textContent = `Edit ${c.name || c.id}`;
        const pl = c.placement || c.parameters?.placement || {};
        const pt = Array.isArray(pl.position) ? pl.position : (Array.isArray(pl.point) ? pl.point : (c.instances?.[0]?.point || [0, 0, 0]));
        const dir = Array.isArray(pl.direction) ? pl.direction : [0, 0, -1];
        active.boltedDirection = dir.map((x) => +Number(x).toFixed(6));
        h.setValue("x", +Number(pt[0] ?? 0).toFixed(3));
        h.setValue("y", +Number(pt[1] ?? 0).toFixed(3));
        h.setValue("z", +Number(pt[2] ?? 0).toFixed(3));
        h.setValue("flip", false);
        const norm = c.screw_norm || (c.head === "countersunk" ? "ISO 10642" : "ISO 4762");
        h.setValue("screw_norm", norm);
        h.setValue("size", c.size || "M6");
        h.setValue("connection_type", c.type || "through");
        h.setValue("fit", c.fit || "normal");
        h.update();
        const ov = c.parameters?.fasteners?.length_override;
        h.setValue("length_override", ov ? String(Number(ov)) : "auto");
        if (c.blind_material) h.setValue("blind_material", c.blind_material);
        h.setValue("counterbore", !!c.counterbore);
        h.setValue("washer_head", !!c.washer_head);
        h.setValue("washer_nut", !!c.washer_nut);
        renderExisting();
        h.update();
      };

      const renderExisting = () => {
        if (!box) return;
        const items = boltedCache.existing || [];
        const newBtn = active.boltedEditId
          ? `<button type="button" class="btn-text bolted-new-btn">New</button>`
          : "";
        if (!items.length) {
          box.innerHTML = `<div class="bolted-list-head"><span>Existing connections (0)</span>${newBtn}</div>`;
        } else {
          const rows = items.map((c) => {
            const isCur = active.boltedEditId === c.id;
            const len = c.screw_length ? ` × ${c.screw_length}` : "";
            return `<div class="bolted-item${isCur ? " active" : ""}">
              <span class="bolted-item-label" title="${esc(c.id)}">${esc(c.name || c.id)} · ${esc(c.size || "")}${esc(len)}</span>
              <span class="bolted-item-actions">
                <button type="button" class="btn-text" data-bolted-edit="${esc(c.id)}">Edit</button>
                <button type="button" class="btn-text" data-bolted-del="${esc(c.id)}">Delete</button>
              </span>
            </div>`;
          }).join("");
          box.innerHTML = `<div class="bolted-list-head"><span>Existing connections (${items.length})</span>${newBtn}</div><div class="bolted-list">${rows}</div>`;
        }
        box.querySelector(".bolted-new-btn")?.addEventListener("click", () => {
          active.boltedEditId = null;
          titleEl.textContent = "Bolted Connection";
          renderExisting();
          h.update();
        });
        box.querySelectorAll("[data-bolted-edit]").forEach((btn) => {
          btn.addEventListener("click", () => {
            const target = (boltedCache.existing || []).find((x) => x.id === btn.dataset.boltedEdit);
            if (target) loadConn(target);
          });
        });
        box.querySelectorAll("[data-bolted-del]").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const cid = btn.dataset.boltedDel;
            h.setError("");
            try {
              const res = await h.post("api/assembly/bolted/delete", { id: cid });
              if (active.boltedEditId === cid) {
                active.boltedEditId = null;
                titleEl.textContent = "Bolted Connection";
              }
              const fresh = await h.get("api/assembly/bolted");
              boltedCache.existing = fresh.items || [];
              await h.reload();
              renderExisting();
              if (h.statusEl) h.statusEl.textContent = res.done || `Deleted ${cid}`;
              h.update();
            } catch (err) {
              h.setError(firstLine(err.message));
            }
          });
        });
      };

      h.viewTools.startHoleOrFacePick((pick) => {
        if (!active) return;
        const p = pick.planar && !pick.hole ? roundOnPlane(pick.point, pick.normal) : pick.point;
        const coords = p.toArray().map((c) => +c.toFixed(3));
        const dir = (pick.direction || pick.normal.clone().negate()).toArray().map((c) => +c.toFixed(6));
        active.boltedDirection = dir;
        h.setValue("x", coords[0]);
        h.setValue("y", coords[1]);
        h.setValue("z", coords[2]);
        h.setValue("flip", false);
        h.log?.("pick_bolted", { point: coords, direction: dir, hole: !!pick.hole });
        h.update();
      });

      if (active.boltedEditId) {
        const target = (boltedCache.existing || []).find((x) => x.id === active.boltedEditId);
        if (target) loadConn(target);
      }
      renderExisting();
    },
  },
};

// Constrain dialog (Inventor's Constrain; SolidCraft assembly.constraint.create/edit, POST /api/assembly/constraint).
// Built on the Joint dialog: two components, a face picked on each (a round face is an axis), the rule and its
// gap or angle. As in SolidCraft's dialogs_constrain.rs (compared 2026-11-15) the rule changes in place but the
// references stay: to pick other faces, delete the constraint and add a new one. Deviation: SolidCraft offers only
// the rules that fit the picked references and keeps the dialog open for the next rule; here all ten are listed
// and SolidCraft's refusal explains a misfit. point_on_axis needs a point pick this dialog does not make; it stays
// with the MCP tool add_constraint.
const CONSTRAINT_TYPES = [
  ["mate", "Mate (faces against each other)"],
  ["flush", "Flush (faces the same way)"],
  ["distance", "Distance"],
  ["concentric", "Concentric (round faces)"],
  ["insert", "Insert (round edges)"],
  ["parallel", "Parallel"],
  ["perpendicular", "Perpendicular"],
  ["angle", "Angle"],
  ["tangent", "Tangent (round face on a plane)"],
];
const GAP_RULES = new Set(["mate", "flush", "distance"]);
DIALOGS.constrain = {
  ...DIALOGS.joint,
  title: "Constrain",
  endpoint: (dlg) => (dlg?.edit ? "api/assembly/constraint/edit" : "api/assembly/constraint"),
  fields: [
    { key: "type", label: "Rule", type: "select", value: "mate", options: CONSTRAINT_TYPES },
    ...DIALOGS.joint.fields.filter((f) => ["comp_a", "origin_a", "comp_b", "origin_b", "name", "flip"].includes(f.key)),
    { key: "offset", label: "Offset", unit: "mm", value: "0", show: (v) => GAP_RULES.has(v.type) },
    { key: "angle", label: "Angle", unit: "°", value: "30", show: (v) => v.type === "angle" },
  ],
  loadEdit(edit, active, setValue) {
    DIALOGS.joint.loadEdit(edit, active, setValue);
    setValue("type", edit.constraint || "mate");
    setValue("flip", false);  // the joint's flip counts differently; Flip on edit turns b over from how it faces now
  },
  status(v, pk, active) {
    const base = DIALOGS.joint.status(v, pk, active);
    if (active?.edit && (active.jointA || active.jointB)) return "A constraint keeps its faces: delete it and add a new one to pick others";
    return base.replace(/^Ready: \S+/, `Ready: ${v.type}`).replace("before creating a joint", "before adding a constraint");
  },
  ready(v, pk, active) {
    if (active?.edit && (active.jointA || active.jointB)) return false;
    return DIALOGS.joint.ready(v, pk, active);
  },
  params(v, _pk, active) {
    const strip = (s) => {
      const out = { occurrence: s.occurrence };
      for (const k of ["face", "circle", "point", "plane", "axis"]) if (s[k] !== undefined) out[k] = s[k];
      return out;
    };
    const req = { type: v.type };
    if (v.flip) req.flip = true;
    if (v.name) req.name = v.name;
    if (active?.edit) req.constraint = active.edit;
    else {
      if (active?.jointA) req.a = strip(active.jointA);
      if (active?.jointB) req.b = strip(active.jointB);
    }
    if (GAP_RULES.has(v.type) && v.offset !== null && v.offset !== "") req.offset = v.offset;
    if (v.type === "angle" && v.angle !== null && v.angle !== "") req.angle = v.angle;
    return req;
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

// What a dialog shows for a refused step: the place when the server found one (edge, what is in the way,
// the size that fits), else the explanation or SolidCraft's words, with what the step was aimed at
function errorText(err) {
  const where = err.where || "";
  if (where && (err.location || {}).kind !== "picks") return where;
  return [err.explanation || firstLine(err.message), where].filter(Boolean).join(" ");
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

// Perpendicular distance from a 3D point to a straight edge's line
function distanceToLineEdge(point, edge) {
  if (!edge || !edge.start || !edge.dir) return 0;
  const p = new THREE.Vector3(...point);
  return p.sub(edge.start).cross(edge.dir).length();
}

export function initFeatureDialogs({ scene, viewTools, renderScene, propertiesEl, statusEl, post, get,
                                     showPreview, clearPreview, reload, showModel, restoreModel,
                                     lookAlong = () => {}, originAxisAt = () => null, revealOriginAxes = () => {},
                                     log = () => {} }) {
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
      }, (mesh) => pickGroup.add(mesh));
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
      else if (f.type === "select" || f.type === "pick") out[f.key] = el.value || "";
      else if (f.type === "text") out[f.key] = el.value.trim();
      else out[f.key] = fieldValue(el.value);
    }
    return out;
  }

  function setValue(key, value) {
    const el = input(key);
    const f = active.def.fields.find((x) => x.key === key);
    if (!el || !f || value === undefined || value === null) return;
    if (f.type === "check") el.checked = !!value;
    else if (f.type === "pick") {
      el.textContent = String(value);
      el.value = String(value);
    } else {
      if (f.type === "select" && typeof f.options === "function") fillOptions(el, f, { ...values(), [key]: value });
      el.value = String(value);
    }
  }

  // A select whose options depend on the other values (Profile follows Sketch): rebuilt when they change
  function fillOptions(el, f, v) {
    const opts = f.options(v);
    const sig = JSON.stringify(opts);
    if (el.dataset.sig === sig) return;
    const cur = el.value;
    el.innerHTML = opts.map(([val, l]) => `<option value="${val}">${l}</option>`).join("");
    el.dataset.sig = sig;
    if (opts.some(([val]) => val === cur)) el.value = cur;
  }

  // Fields shown or read-only by the other values, and the note naming the tables
  function refreshFields() {
    const v = values();
    for (const f of active.def.fields) {
      const el = input(f.key);
      if (f.type === "select" && typeof f.options === "function" && f.options.length) fillOptions(el, f, v);
      if (f.type === "pick") el.classList.toggle("active", active.slot === f.key);
      const row = el.closest(".feature-field");
      row.hidden = f.show ? !f.show(v, active) : false;
      if (f.readonly) el.readOnly = f.readonly(v, active);
    }
    active.noteEl.textContent = active.def.sourceNote ? active.def.sourceNote(v, active) : "";
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
    return { edges: Array.from(active.edges.values(), (e) => e.point), edgePicks: Array.from(active.edges.values()),
             direction: active.point?.direction || null,
             features: [...active.features], edge1: active.edge1, face: active.face,
             sketch: { shapes: active.shapes || [], face: active.face } };
  }

  // Everything the command needs is there: picks, and every shown number field filled
  function ready() {
    const def = active.def, v = values(), p = picks();
    if (def.view === "edges" && !active.edges.size) return false;
    if (def.ready && !def.ready(v, p, active)) return false;
    if (def.noFieldCheck) return true; // the sketch: shapes already added count, the fields may be empty
    return def.fields.every((f) => f.type === "check" || f.type === "select" || f.type === "pick" || f.type === "text"
      || (f.show && !f.show(v, active)) || v[f.key] !== null);
  }

  function update() {
    const def = active.def, v = values(), p = picks();
    let text = def.status ? def.status(v, p, active) : null;
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
      active.clearBtn.hidden = def.hasClear ? !def.hasClear(active) : (active.edges.size === 0 || !!v.centre_fixed);
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
      body.params = active.def.editSet ? active.def.editSet(v, p, active) : active.def.params(v, p, active);
    } else body.params = active.def.params(v, p, active);
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
      let res;
      if (dlg.def.previewEndpoint) {
        const req = dlg.def.previewParams ? dlg.def.previewParams(values(), picks(), dlg) : dlg.def.params(values(), picks(), dlg);
        res = await post(dlg.def.previewEndpoint, req);
        if (active !== dlg || dlg.stale || seq !== dlg.seq) return;
        setError("");
        dlg.previewData = res;
        if (res.mesh) showPreview(res.mesh);
        else clearPreview();
        drawPicks();
        dlg.deltaEl.textContent = dlg.def.describePreview ? dlg.def.describePreview(res, dlg) : "";
      } else {
        const req = request(true);
        res = await post("api/feature", req);
        if (active !== dlg || dlg.stale || seq !== dlg.seq) return; // closed, or the values changed meanwhile
        setError("");
        showPreview(res.mesh);
        dlg.deltaEl.textContent = describeDelta(res.delta);
      }
    } catch (err) {
      if (active !== dlg || dlg.stale || seq !== dlg.seq) return;
      log("dialog_preview_error", { dialog: dlg.kind, values: values(), error: firstLine(err.message) });
      if (dlg.def.previewEndpoint) {
        dlg.previewData = null;
        drawPicks();
      }
      clearPreview();
      dlg.deltaEl.textContent = "";
      setError(errorText(err));
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
      const customEp = typeof dlg.def.endpoint === "function" ? dlg.def.endpoint(dlg) : dlg.def.endpoint;
      const endpoint = customEp || "api/feature";
      const req = customEp ? dlg.def.params(values(), picks(), dlg) : request(false);
      log("dialog_ok", { dialog: dlg.kind, edit: dlg.edit || dlg.boltedEditId, values: values(), request: req });
      const res = await post(endpoint, req);
      const def = dlg.def;
      close();
      await reload();
      statusEl.textContent = res.done || "Done";
      if (def.after) def.after(res, api);
    } catch (err) {
      log("dialog_ok_error", { dialog: dlg.kind, error: firstLine(err.message) });
      dlg.busy = false;
      if (active === dlg) {
        setError(errorText(err));
        update();
      }
    }
  }

  function close() {
    if (!active) return;
    log("dialog_close", { dialog: active.kind, edit: active.edit });
    clearTimeout(active.timer);
    const wasEdit = active.edit, wasSketch = active.def.view === "sketch";
    active = null;
    revealOriginAxes(false);
    if (wasEdit) restoreModel();
    if (wasSketch) lookAlong(null); // back to the usual view, as Inventor does after Finish Sketch
    viewTools.stopEdgePick();
    clearPreview();
    drawPicks();
    propertiesEl.innerHTML = emptyHtml;
    document.querySelectorAll("[data-feature], [data-assembly]").forEach((b) => b.classList.remove("active"));
  }

  function fieldHtml(f) {
    let control;
    if (f.type === "select") {
      const opts = typeof f.options === "function" ? f.options() : f.options;
      control = `<select name="${f.key}">${opts.map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}</select>`;
    } else if (f.type === "check") {
      control = `<input type="checkbox" name="${f.key}">`;
    } else if (f.type === "pick") {
      control = `<button type="button" class="feature-slot" name="${f.key}" data-slot="${f.key}"></button>`;
    } else {
      // no inputmode="decimal": some touch keyboards then hide the minus sign, and fields take expressions (t/2)
      const ph = f.placeholder ? ` placeholder="${f.placeholder}"` : "";
      control = `<input name="${f.key}"${ph} spellcheck="false" autocapitalize="off" autocomplete="off">`;
    }
    return `<label class="feature-field${f.type === "check" ? " feature-check" : ""}"><span>${f.label}</span>${control}`
      + `<span class="feature-unit">${f.unit || ""}</span></label>`;
  }

  function renderFieldsHtml(fields) {
    let html = "";
    for (let i = 0; i < fields.length;) {
      const grp = fields[i].group;
      if (grp) {
        const chunk = [];
        while (i < fields.length && fields[i].group === grp) chunk.push(fields[i++]);
        html += `<div class="feature-position">${chunk.map(fieldHtml).join("")}</div>`;
      } else {
        html += fieldHtml(fields[i++]);
      }
    }
    return html;
  }

  async function open(kind, edit = null) {
    const def = DIALOGS[kind];
    if (!def) return;
    // any edit object but a bolted connection's (feature definitions, joints with loadEdit) edits in place
    const isFeatureEdit = Boolean(edit && !edit.boltedEditId);
    const boltedEditId = edit?.boltedEditId || null;
    if (active && active.kind === kind && !isFeatureEdit && !boltedEditId && !active.edit && !active.boltedEditId) return close();
    close();
    if (def.needs) {
      try {
        await def.needs(get);
      } catch (err) {
        statusEl.textContent = `${def.title}: ${err.message}`;
        return;
      }
    }
    propertiesEl.innerHTML = `
      <form class="feature-dialog" autocomplete="off">
        <div class="feature-dialog-title"></div>
        <div class="feature-pick">
          <span class="feature-pick-count"></span>
          <button type="button" class="btn-text feature-clear" hidden>Clear</button>
        </div>
        ${renderFieldsHtml(def.fields)}
        <div class="feature-note"></div>
        <div class="feature-delta"></div>
        <div class="feature-error" hidden></div>
        <div class="feature-actions">
          <button type="button" class="btn-text feature-cancel">Cancel</button>
          <button type="submit" class="feature-ok" disabled>OK</button>
        </div>
      </form>`;
    const form = propertiesEl.querySelector("form");
    form.querySelector(".feature-dialog-title").textContent = isFeatureEdit ? `Edit ${edit.name}` : def.title;
    log("dialog_open", { dialog: kind, edit: isFeatureEdit ? edit.name : boltedEditId });
    active = {
      kind, def, form, edges: new Map(), point: null, edge1: null, face: null, features: [],
      timer: null, seq: 0, busy: false, edit: isFeatureEdit ? edit.name : null,
      boltedEditId, previewData: null,
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
      if (def.onClear) def.onClear(active, setValue, values());
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
    form.querySelectorAll(".feature-slot").forEach((el) => {
      el.addEventListener("click", () => active?.setSlot?.(el.dataset.slot));
    });

    if (isFeatureEdit) {
      if (def.loadEdit) {
        def.loadEdit(edit, active, setValue);
      } else {
        const from = def.fromDefinition(edit.definition, edit.feature_names || {});
        for (const [k, v] of Object.entries(from.values || {})) setValue(k, v);
        for (const point of from.edges || []) {
          const edge = edgeAt(edit.before, point);
          active.edges.set(edge ? edgeKey(edge) : `point|${point.join(",")}`, { point, edge });
        }
        if (from.direction) active.point = { direction: from.direction };
        if (from.features) active.features = from.features;
        if (from.edge1) {
          const edge = from.edge1.point ? edgeAt(edit.before, from.edge1.point) : null;
          active.edge1 = edge ? { ...from.edge1, edge } : from.edge1;
        }
        if (from.face) active.face = from.face;
        if (from.profile !== undefined) active.fromProfile = from.profile;
        if (from.axis !== undefined) active.axis = from.axis;
      }
    } else {
      document.querySelectorAll(`[data-feature="${kind}"], [data-assembly="${kind}"]`).forEach((b) => b.classList.add("active"));
    }
    const box = new THREE.Box3().setFromObject(scene);
    markerSize = Math.max(box.isEmpty() ? 1 : box.getSize(new THREE.Vector3()).length() / 250, 0.05);
    active.markerSize = markerSize;

    if (def.init) {
      await def.init(active, { get, post, reload, statusEl, setValue, values, update, setError, viewTools, lookAlong, originAxisAt, revealOriginAxes, log });
    } else if (def.view === "edges") {
      viewTools.startEdgePick((pick) => {
        if (!active) return;
        if (active.edges.has(pick.key)) active.edges.delete(pick.key);
        else active.edges.set(pick.key, pick);
        log("pick_edge", { dialog: active.kind, kind: pick.edge.kind, point: pick.point, selected: active.edges.size });
        update();
      });
    } else if (def.view === "edge") {
      // one edge: a direction (straight edge) or an axis (straight or circular edge, a hole)
      viewTools.startEdgePick((pick) => {
        if (!active) return;
        log("pick_edge", { dialog: active.kind, kind: pick.edge.kind, point: pick.point });
        const dir = pick.edge.kind === "line" ? pick.edge.dir.toArray().map((c) => +c.toFixed(9)) : null;
        active.edge1 = { ...pick, dir };
        const sel = def.fields.find((f) => f.type === "select" && f.options && (typeof f.options === "function"
          ? f.options() : f.options).some(([val]) => val === "edge"));
        if (sel) setValue(sel.key, "edge");
        update();
      });
    } else if (def.view === "face") {
      viewTools.startFacePick((pick) => {
        if (!active || !def.onFace) return;
        log("pick_face", { dialog: active.kind, point: pick.point.toArray().map((c) => +c.toFixed(3)),
                           normal: pick.normal.toArray().map((c) => +c.toFixed(3)), planar: pick.planar });
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

  async function editJoint(name) {
    close();
    statusEl.textContent = `Opening ${name}…`;
    try {
      jointContext = await get("api/assembly/context");
    } catch (err) {
      statusEl.textContent = err.message;
      return;
    }
    const found = (jointContext.joints || []).find((j) => j.name === name);
    if (!found) {
      statusEl.textContent = `Joint ${name} not found`;
      return;
    }
    await open(found.constraint ? "constrain" : "joint", found);
    statusEl.textContent = "Ready";
  }

  // Delete confirmation dialog, Inventor style:
  // When deleting a feature that consumes a sketch, ask "Delete the sketch too?" with a preselected
  // "Delete consumed sketch" checkbox. If unchecked, keep_sketch=true is sent.
  // Deviation from SolidCraft: SolidCraft's ui-egui timeline.delete only confirms cascading deletes
  // via a binary ConfirmDelete dialog ("Also deletes", "Will fail"). Mechvane follows Inventor
  // (GUID-983D8293): features with consumed sketches ask "Delete the sketch too?" with a pre-selected
  // checkbox "Delete consumed sketch", allowing the user to preserve their constrained sketches.
  function ensureDeleteDialog() {
    let dialog = document.getElementById("delete-feature-dialog");
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.id = "delete-feature-dialog";
    dialog.className = "request-dialog delete-feature-dialog";
    dialog.innerHTML = `
      <form method="dialog" class="request-form">
        <div class="request-dialog-header">
          <h3 id="delete-feature-dialog-title">Delete Features</h3>
          <button type="button" class="request-dialog-close" aria-label="Close">&times;</button>
        </div>
        <div class="request-dialog-body">
          <p id="delete-feature-prompt" style="margin: 0 0 12px 0;">Delete the sketch too?</p>
          <div class="request-checkbox-row">
            <label>
              <input type="checkbox" id="delete-consumed-sketch" checked>
              Delete consumed sketch
            </label>
          </div>
          <div id="delete-feature-error" class="new-part-error" role="alert" hidden></div>
        </div>
        <div class="request-dialog-footer">
          <button type="button" class="btn-cancel">Cancel</button>
          <button type="submit" class="btn-submit" id="delete-feature-submit">Delete</button>
        </div>
      </form>
    `;
    document.body.appendChild(dialog);
    dialog.querySelector(".request-dialog-close").addEventListener("click", () => dialog.close());
    dialog.querySelector(".btn-cancel").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
    return dialog;
  }

  function promptDeleteWithSketch(name) {
    return new Promise((resolve) => {
      const dialog = ensureDeleteDialog();
      const checkbox = dialog.querySelector("#delete-consumed-sketch");
      checkbox.checked = true; // Preselected as in Inventor (vorausgewählt)
      const form = dialog.querySelector("form");
      let resolved = false;

      const finish = (result) => {
        if (resolved) return;
        resolved = true;
        form.removeEventListener("submit", onSubmit);
        dialog.removeEventListener("close", onClose);
        resolve(result);
      };

      const onSubmit = (e) => {
        e.preventDefault();
        const keepSketch = !checkbox.checked;
        dialog.close();
        finish({ confirmed: true, keepSketch });
      };

      const onClose = () => {
        finish({ confirmed: false });
      };

      form.addEventListener("submit", onSubmit);
      dialog.addEventListener("close", onClose, { once: true });
      dialog.showModal();
    });
  }

  function consumesSketch(name) {
    const row = document.querySelector(`.tree-row[data-feature="${CSS.escape(name)}"]`);
    if (!row) return false;
    if (row.dataset.consumesSketch === "true") return true;
    const item = row.closest(".tree-item");
    return Boolean(item?.querySelector(":scope > .tree-children .tree-row[data-type='Sketch']"));
  }

  async function remove(name, keepSketch = undefined) {
    close();
    if (keepSketch === undefined) {
      if (consumesSketch(name)) {
        const res = await promptDeleteWithSketch(name);
        if (!res.confirmed) return;
        keepSketch = res.keepSketch;
      } else {
        keepSketch = false;
      }
    }
    statusEl.textContent = `Deleting ${name}…`;
    try {
      const res = await post("api/feature/delete", { name, keep_sketch: !!keepSketch });
      const failing = Object.keys(res.failing || {});
      await reload();
      statusEl.textContent = failing.length
        ? `${res.done}. Now failing: ${failing.join(", ")} (Ctrl+Z puts it back)`
        : res.done;
    } catch (err) {
      statusEl.textContent = `Delete ${name}: ${err.message}`;
    }
  }

  async function rename(feature, newName) {
    close();
    statusEl.textContent = `Renaming ${feature}…`;
    try {
      const res = await post("api/feature/rename", { feature, name: newName });
      await reload();
      statusEl.textContent = res.done || `Renamed ${feature} to ${newName}`;
      return true;
    } catch (err) {
      statusEl.textContent = `Rename: ${err.message}`;
      return false;
    }
  }

  async function renameJoint(joint, newName) {
    close();
    statusEl.textContent = `Renaming ${joint}…`;
    try {
      const res = await post("api/assembly/joint/edit", { joint, name: newName });
      await reload();
      statusEl.textContent = res.done || `Renamed ${joint} to ${newName}`;
      return true;
    } catch (err) {
      statusEl.textContent = `Rename: ${err.message}`;
      return false;
    }
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && active) {
      e.preventDefault();
      close();
    } else if (e.key === "Tab" && active?.setSlot && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      const slots = active.def.slots?.length ? active.def.slots : ["profile", "axis"];
      const next = slots[(slots.indexOf(active.slot) + 1) % slots.length];
      active.setSlot(next);
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

  function pickOrigin(name) {
    return active?.pickOrigin ? active.pickOrigin(name) : false;
  }

  const api = {
    open,
    close,
    edit,
    editJoint,
    remove,
    rename,
    renameJoint,
    pickFeature,
    pickOrigin,
    picksFeatures: () => !!(active && active.def.features),
    // The model was reloaded under an open dialog (agent, undo): the picked edges may be gone
    modelChanged() {
      if (active && active.edit) close();
      else if (active && !active.busy) {
        active.edges.clear();
        active.edge1 = null;
        active.face = null;
        if (active.axis?.type === "edge") active.axis = null;
        if (active.kind === "joint") {
          active.jointA = null;
          active.jointB = null;
        }
        update();
      }
      if (active) markTree();
    },
    isOpen: () => !!active,
  };
  return api;
}

function ensureUpdateLinksDialog() {
  let dialog = document.getElementById("update-links-dialog");
  if (dialog) return dialog;
  dialog = document.createElement("dialog");
  dialog.id = "update-links-dialog";
  dialog.className = "request-dialog";
  dialog.innerHTML = `
    <div class="request-form">
      <div class="request-dialog-header">
        <h3>Update Links</h3>
        <button type="button" class="request-dialog-close" aria-label="Close">&times;</button>
      </div>
      <div class="request-dialog-body">
        <div id="update-links-summary"></div>
        <div id="update-links-details" class="request-dialog-note"></div>
        <div id="update-links-error" class="new-part-error" role="alert" hidden></div>
      </div>
      <div class="request-dialog-footer">
        <button type="button" class="btn-submit" id="update-links-repair">Repair</button>
        <button type="button" class="btn-cancel" id="update-links-close">Close</button>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);
  dialog.querySelector(".request-dialog-close").addEventListener("click", () => dialog.close());
  dialog.querySelector("#update-links-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  return dialog;
}

function formatUpdateLinksHtml(data) {
  const checked = data.checked_joints || [];
  const count = data.joint_count ?? checked.length;
  const moved = data.moved_joints || [];
  const repaired = data.repaired || [];
  const updated = data.update?.updated || [];
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const lines = [];
  lines.push(`<p><strong>${count} joint${count === 1 ? "" : "s"} checked.</strong>`
    + (moved.length ? ` Moved: <strong>${moved.map(esc).join(", ")}</strong>.` : "") + `</p>`);
  if (updated.length) {
    lines.push(`<p>Updated components: ${updated.map(esc).join(", ")}.</p>`);
  }
  if (repaired.length) {
    const items = repaired.map((r) => `${esc(r.joint)} (${esc(r.status)}${r.error ? `: ${esc(r.error)}` : ""})`);
    lines.push(`<p>Repair result: ${items.join(", ")}.</p>`);
  }
  const warnings = data.warnings || [];
  if (warnings.length) {
    lines.push("<ul>" + warnings.map((w) => {
      if (w.status === "link_blocked") {
        // SolidCraft refused to read this part again: its old bodies stay in the assembly
        return `<li>Part ${esc(w.component || "?")} not updated${w.feature ? `: feature ${esc(w.feature)} fails` : ""}. Fix the part, then Update Links again.</li>`;
      }
      const target = w.joint ? `Joint ${esc(w.joint)} (${esc(w.side || "?")})` : `Bolted ${esc(w.connection || "?")}`;
      return `<li>${target}: ${esc(w.status)}${w.now_on ? ` (now on ${esc(w.now_on)})` : ""}</li>`;
    }).join("") + "</ul>");
  }
  return {
    summary: lines.join(""),
    details: data.message || data.done || "",
  };
}

/** Run POST /api/assembly/update_links and show the result dialog with a Repair button (repair=true). */
export async function runUpdateLinks({ post, reload, statusEl, log = () => {} }) {
  const dialog = ensureUpdateLinksDialog();
  const summaryEl = dialog.querySelector("#update-links-summary");
  const detailsEl = dialog.querySelector("#update-links-details");
  const errorEl = dialog.querySelector("#update-links-error");
  const repairBtn = dialog.querySelector("#update-links-repair");

  async function execute(repair) {
    errorEl.hidden = true;
    repairBtn.disabled = true;
    statusEl.textContent = repair ? "Repairing joints…" : "Updating links…";
    try {
      const res = await post("api/assembly/update_links", { repair: !!repair });
      log("assembly_update_links", { repair: !!repair, joint_count: res.joint_count, moved: res.moved_joints });
      const formatted = formatUpdateLinksHtml(res);
      summaryEl.innerHTML = formatted.summary;
      detailsEl.textContent = formatted.details;
      await reload();
      statusEl.textContent = res.message || res.done || "Links updated";
      if (!dialog.open) dialog.showModal();
    } catch (err) {
      errorEl.textContent = err.message || "Update links failed";
      errorEl.hidden = false;
      statusEl.textContent = errorEl.textContent;
      if (!dialog.open) dialog.showModal();
    } finally {
      repairBtn.disabled = false;
    }
  }

  repairBtn.onclick = () => execute(true);
  await execute(false);
}
