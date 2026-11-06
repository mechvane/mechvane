import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { initViewTools } from "./viewtools.js";
import { initAgentChat } from "./chat.js";
import { openNewPartDialog, openImportStepDialog } from "./newpart.js";
import { initFeatureDialogs, EDITABLE_TYPES } from "./features.js";
import { initSketcher } from "./sketcher.js";
import { curvePoints, toWorld } from "./sketchgeom.js";

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

const viewportEl = document.getElementById("viewport");
const docNameEl = document.getElementById("doc-name");
const docKindEl = document.getElementById("doc-kind");
const docPathEl = document.getElementById("doc-path");
const verdictBadgeEl = document.getElementById("verdict-badge");
const statusEl = document.getElementById("status-indicator");
const treeContentEl = document.getElementById("tree-content");
const findingsContentEl = document.getElementById("findings-content");
const findingsCountEl = document.getElementById("findings-count");
const findingsSummaryEl = document.getElementById("findings-summary");
const selectionBannerEl = document.getElementById("selection-banner");
const axesLines = {
  x: document.getElementById("axis-x"),
  y: document.getElementById("axis-y"),
  z: document.getElementById("axis-z"),
};
const axesLabels = {
  x: document.getElementById("axis-label-x"),
  y: document.getElementById("axis-label-y"),
  z: document.getElementById("axis-label-z"),
};

const scene = new THREE.Scene();
// Parallel projection as in Inventor and every drawing: sizes do not shrink with depth (user 2026-11-06).
// viewHalf is half the visible height in mm at zoom 1; OrbitControls zooms through camera.zoom.
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10000);
let viewHalf = 60;
function setFrustum() {
  const w = viewportEl.clientWidth || 640, h = viewportEl.clientHeight || 480;
  const a = w / h;
  camera.left = -viewHalf * a;
  camera.right = viewHalf * a;
  camera.top = viewHalf;
  camera.bottom = -viewHalf;
  camera.updateProjectionMatrix();
}
camera.up.set(0, 0, 1);
camera.position.set(120, -140, 100);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
viewportEl.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = false;
controls.screenSpacePanning = true;

const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
scene.add(ambientLight);

const keyLight = new THREE.DirectionalLight(0xffffff, 0.75);
keyLight.position.set(150, -180, 220);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xffffff, 0.35);
fillLight.position.set(-160, 140, -100);
scene.add(fillLight);

const modelGroup = new THREE.Group();
const highlightGroup = new THREE.Group();
scene.add(modelGroup);
scene.add(highlightGroup);

let currentVersion = null;
let currentMeshData = null;
let currentFindings = [];
let selectedFindingIndex = null;
let cameraFitted = false;
let modelRadius = 50;
let modelCenter = new THREE.Vector3(0, 0, 0);
const viewTools = initViewTools({
  scene, camera, renderer, modelGroup, renderScene, controls,
  selectable: document.documentElement.dataset.static !== "1",
  containerEl: viewportEl.parentElement,
});

function updateAxesGizmo() {
  if (!axesLines.x) return;
  const invQuat = camera.quaternion.clone().invert();
  const dirs = {
    x: new THREE.Vector3(1, 0, 0).applyQuaternion(invQuat),
    y: new THREE.Vector3(0, 1, 0).applyQuaternion(invQuat),
    z: new THREE.Vector3(0, 0, 1).applyQuaternion(invQuat),
  };
  for (const k of ["x", "y", "z"]) {
    const v = dirs[k];
    const x2 = 32 + v.x * 17;
    const y2 = 32 - v.y * 17;
    const lx = 32 + v.x * 24;
    const ly = 32 - v.y * 24 + 3;
    if (axesLines[k]) {
      axesLines[k].setAttribute("x2", x2.toFixed(1));
      axesLines[k].setAttribute("y2", y2.toFixed(1));
    }
    if (axesLabels[k]) {
      axesLabels[k].setAttribute("x", lx.toFixed(1));
      axesLabels[k].setAttribute("y", ly.toFixed(1));
    }
  }
}

function applyThemeColors() {
  // Dark unless the page asks for the light theme (style.css)
  const isDark = document.documentElement.dataset.theme !== "light";
  scene.background = new THREE.Color(isDark ? 0x111418 : 0xf3f5f8);
  if (currentMeshData) {
    updateMeshView(currentMeshData, false);
    if (selectedFindingIndex !== null && currentFindings[selectedFindingIndex]) {
      highlightFinding(currentFindings[selectedFindingIndex]);
    }
  }
  renderScene();
}

applyThemeColors();

new MutationObserver(() => applyThemeColors()).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["data-theme"],
});

function renderScene() {
  updateAxesGizmo();
  if (originGroup) scaleOrigin();
  renderer.render(scene, camera);
}

controls.addEventListener("change", renderScene);

function fitCameraToModel(keepDirection = false) {
  // the whole model in view, also when the window is narrower than high
  const w = viewportEl.clientWidth || 640, h = viewportEl.clientHeight || 480;
  viewHalf = modelRadius * 1.15 * Math.max(1, h / w);
  camera.zoom = 1;
  setFrustum();
  const dist = modelRadius * 4 + 50;
  // home: isometric, looking down onto the X, -Y, Z corner
  let dir = new THREE.Vector3(1, -1, 1).normalize();
  if (keepDirection) {
    const cur = camera.position.clone().sub(controls.target);
    if (cur.lengthSq() > 1e-6) dir = cur.normalize();
  } else {
    camera.up.set(0, 0, 1);
  }
  camera.position.copy(modelCenter).addScaledVector(dir, dist);
  camera.near = 0.1;
  camera.far = dist + modelRadius * 8 + 1000;
  camera.updateProjectionMatrix();
  controls.target.copy(modelCenter);
  controls.update();
  cameraFitted = true;
  renderScene();
}

function homeView() {
  fitCameraToModel(false);
}

// Standard views as SolidCraft has them (crates/render/src/camera.rs): front looks along +Y, right from +X,
// top down onto XY with +Y up, iso from the front-right-top corner (Home). Direction = from the target to the eye.
const STANDARD_VIEWS = {
  front: [[0, -1, 0], [0, 0, 1]], back: [[0, 1, 0], [0, 0, 1]],
  right: [[1, 0, 0], [0, 0, 1]], left: [[-1, 0, 0], [0, 0, 1]],
  top: [[0, 0, 1], [0, 1, 0]], bottom: [[0, 0, -1], [0, 1, 0]],
  iso: [[1, -1, 1], [0, 0, 1]],
};
function standardView(name) {
  const v = STANDARD_VIEWS[name];
  if (!v) return;
  fitCameraToModel(false);
  const dist = camera.position.distanceTo(controls.target);
  camera.up.set(...v[1]);
  camera.position.copy(controls.target).addScaledVector(new THREE.Vector3(...v[0]).normalize(), dist);
  camera.lookAt(controls.target);
  controls.update();
  renderScene();
}
document.querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => standardView(b.dataset.view)));

function zoomAll() {
  fitCameraToModel(true);
}

function resizeViewport() {
  const w = viewportEl.clientWidth || 640;
  const h = viewportEl.clientHeight || 480;
  setFrustum();
  renderer.setSize(w, h, false);
  renderScene();
}

window.addEventListener("resize", resizeViewport);
resizeViewport();

function clearGroup(group) {
  while (group.children.length > 0) {
    const child = group.children.pop();
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
      else child.material.dispose();
    }
  }
}

function buildBodyGeometryAndEdges(body) {
  const pos = body.positions || [];
  const idx = body.indices || [];
  const fids = body.face_ids || [];
  const triCount = Math.floor(idx.length / 3);

  // Split vertices by (vertexIndex, faceId) so smooth faces stay smooth and sharp B-rep edges stay crisp
  const outPositions = [];
  const outIndices = [];
  const vertMap = new Map();
  let nextVert = 0;

  // Also collect edges between different face_ids for B-rep feature line rendering
  const edgeMap = new Map();

  for (let t = 0; t < triCount; t++) {
    const fid = fids[t] !== undefined ? fids[t] : 0;
    const v0 = idx[t * 3];
    const v1 = idx[t * 3 + 1];
    const v2 = idx[t * 3 + 2];
    const triVerts = [v0, v1, v2];
    const mapped = [0, 0, 0];

    for (let k = 0; k < 3; k++) {
      const origV = triVerts[k];
      const key = `${origV}:${fid}`;
      let mv = vertMap.get(key);
      if (mv === undefined) {
        mv = nextVert++;
        vertMap.set(key, mv);
        outPositions.push(pos[origV * 3], pos[origV * 3 + 1], pos[origV * 3 + 2]);
      }
      mapped[k] = mv;

      const va = triVerts[k];
      const vb = triVerts[(k + 1) % 3];
      const eKey = va < vb ? `${va}_${vb}` : `${vb}_${va}`;
      const existing = edgeMap.get(eKey);
      if (!existing) {
        edgeMap.set(eKey, { va, vb, fid, boundary: false });
      } else if (existing.fid !== fid) {
        existing.boundary = true;
      }
    }
    outIndices.push(mapped[0], mapped[1], mapped[2]);
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute("position", new THREE.Float32BufferAttribute(outPositions, 3));
  geom.setIndex(outIndices);
  geom.computeVertexNormals();

  const linePositions = [];
  for (const e of edgeMap.values()) {
    if (e.boundary) {
      linePositions.push(
        pos[e.va * 3], pos[e.va * 3 + 1], pos[e.va * 3 + 2],
        pos[e.vb * 3], pos[e.vb * 3 + 1], pos[e.vb * 3 + 2]
      );
    }
  }
  const edgeGeom = new THREE.BufferGeometry();
  edgeGeom.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));

  return { geom, edgeGeom };
}

function updateMeshView(meshData, fitCamera) {
  currentMeshData = meshData;
  clearGroup(modelGroup);
  clearGroup(highlightGroup);

  const isDark = document.documentElement.dataset.theme !== "light";
  const bodyColors = isDark
    ? [0x6e85a1, 0x7b9689, 0x998478, 0x827b9c, 0x74929c]
    : [0x94a8be, 0x9db4a9, 0xb8a598, 0xa39cb8, 0x93b0b8];
  const edgeColor = isDark ? 0x1e242c : 0x334155;

  const box = new THREE.Box3();
  const bodies = (meshData && meshData.bodies) || [];

  bodies.forEach((b, i) => {
    if (!b.positions || b.positions.length === 0) return;
    const { geom, edgeGeom } = buildBodyGeometryAndEdges(b);
    const mat = new THREE.MeshStandardMaterial({
      color: bodyColors[i % bodyColors.length],
      roughness: 0.55,
      metalness: 0.12,
      side: THREE.DoubleSide,
      polygonOffset: true,
      polygonOffsetFactor: 1,
      polygonOffsetUnits: 1,
    });
    const mesh = new THREE.Mesh(geom, mat);
    mesh.userData.bodyIndex = i;
    modelGroup.add(mesh);

    if (edgeGeom.attributes.position.count > 0) {
      const lineMat = new THREE.LineBasicMaterial({ color: edgeColor, transparent: true, opacity: 0.55 });
      modelGroup.add(new THREE.LineSegments(edgeGeom, lineMat));
    }

    geom.computeBoundingBox();
    if (geom.boundingBox) box.union(geom.boundingBox);
  });

  if (!box.isEmpty()) {
    const sphere = new THREE.Sphere();
    // a shown Origin belongs in the picture (its planes are what a first sketch goes on)
    if (originGroup && originState.folder) box.expandByPoint(new THREE.Vector3(0, 0, 0));
    box.getBoundingSphere(sphere);
    modelRadius = Math.max(sphere.radius, 5);
    modelCenter.copy(sphere.center);

    if (fitCamera || !cameraFitted) {
      fitCameraToModel(false);
    }
  } else {
    modelRadius = 50;
    modelCenter.set(0, 0, 0);
    if (fitCamera || !cameraFitted) {
      fitCameraToModel(false);
    }
  }

  viewTools.meshUpdated(meshData);
}

function severityColorHex(severity) {
  if (severity === "fail") return 0xe11d48;
  if (severity === "warn") return 0xd97706;
  return 0x16a34a;
}

function highlightFinding(finding) {
  clearGroup(highlightGroup);
  if (!finding) {
    selectionBannerEl.hidden = true;
    renderScene();
    return;
  }

  const colorHex = severityColorHex(finding.severity || finding.status);
  const faceNames = new Set();
  if (Array.isArray(finding.faces)) {
    finding.faces.forEach((fn) => fn && faceNames.add(fn));
  }
  if (finding.face) faceNames.add(finding.face);
  if (finding.location && finding.location.face) faceNames.add(finding.location.face);
  if (finding.location && finding.location.assembly_face) faceNames.add(finding.location.assembly_face);

  const wantBody = finding.body || (finding.location && finding.location.body) || null;
  const bodies = (currentMeshData && currentMeshData.bodies) || [];
  const highlightVerts = [];

  if (faceNames.size > 0) {
    const expandedPrefixes = [];
    for (const fn of faceNames) {
      const m = fn.match(/^(.*:side):\d+$/);
      if (m) expandedPrefixes.push(m[1] + ":");
    }
    for (const b of bodies) {
      if (wantBody && b.name !== wantBody) continue;
      const matchedIndices = new Set();
      for (const f of b.faces || []) {
        const fname = f.name || "";
        if (faceNames.has(fname)) {
          matchedIndices.add(f.index);
          continue;
        }
        if (expandedPrefixes.some((p) => fname.startsWith(p) && !fname.includes("#"))) {
          matchedIndices.add(f.index);
          continue;
        }
        for (const target of faceNames) {
          if (fname.includes("#") && fname.includes(target)) {
            matchedIndices.add(f.index);
            break;
          }
        }
      }
      if (matchedIndices.size === 0) continue;

      const pos = b.positions || [];
      const idx = b.indices || [];
      const fids = b.face_ids || [];
      for (let t = 0; t < fids.length; t++) {
        if (matchedIndices.has(fids[t])) {
          const v0 = idx[t * 3];
          const v1 = idx[t * 3 + 1];
          const v2 = idx[t * 3 + 2];
          highlightVerts.push(
            pos[v0 * 3], pos[v0 * 3 + 1], pos[v0 * 3 + 2],
            pos[v1 * 3], pos[v1 * 3 + 1], pos[v1 * 3 + 2],
            pos[v2 * 3], pos[v2 * 3 + 1], pos[v2 * 3 + 2]
          );
        }
      }
    }
  }

  if (highlightVerts.length > 0) {
    const hGeom = new THREE.BufferGeometry();
    hGeom.setAttribute("position", new THREE.Float32BufferAttribute(highlightVerts, 3));
    hGeom.computeVertexNormals();

    const solidMat = new THREE.MeshStandardMaterial({
      color: colorHex,
      emissive: colorHex,
      emissiveIntensity: 0.35,
      roughness: 0.3,
      side: THREE.DoubleSide,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
    });
    highlightGroup.add(new THREE.Mesh(hGeom, solidMat));

    const xrayMat = new THREE.MeshBasicMaterial({
      color: colorHex,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.35,
      depthTest: false,
    });
    const xrayMesh = new THREE.Mesh(hGeom, xrayMat);
    xrayMesh.renderOrder = 2;
    highlightGroup.add(xrayMesh);

    const edgesGeom = new THREE.EdgesGeometry(hGeom, 15);
    const edgesMat = new THREE.LineBasicMaterial({ color: colorHex, depthTest: false });
    const edgesLine = new THREE.LineSegments(edgesGeom, edgesMat);
    edgesLine.renderOrder = 3;
    highlightGroup.add(edgesLine);

    const labelFace = finding.face || Array.from(faceNames)[0];
    selectionBannerEl.textContent = `Highlighted face: ${labelFace}`;
    selectionBannerEl.hidden = false;
    renderScene();
    return;
  }

  const pt = finding.point || (finding.location && finding.location.point);
  if (Array.isArray(pt) && pt.length === 3 && pt.every((n) => typeof n === "number")) {
    const r = Math.max(0.8, modelRadius * 0.045);
    const sphereGeom = new THREE.SphereGeometry(r, 24, 16);
    const sphereMat = new THREE.MeshBasicMaterial({ color: colorHex, depthTest: false });
    const marker = new THREE.Mesh(sphereGeom, sphereMat);
    marker.position.set(pt[0], pt[1], pt[2]);
    marker.renderOrder = 4;
    highlightGroup.add(marker);

    const ringGeom = new THREE.RingGeometry(r * 1.35, r * 1.8, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: colorHex,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
      depthTest: false,
    });
    const ring = new THREE.Mesh(ringGeom, ringMat);
    ring.position.set(pt[0], pt[1], pt[2]);
    ring.lookAt(camera.position);
    ring.renderOrder = 4;
    highlightGroup.add(ring);

    const coords = pt.map((v) => v.toFixed(1)).join(", ");
    selectionBannerEl.textContent = `Marker bei Punkt: [${coords}]`;
    selectionBannerEl.hidden = false;
    renderScene();
    return;
  }

  selectionBannerEl.textContent = `Finding without a location`;
  selectionBannerEl.hidden = false;
  renderScene();
}

function statusBadgeClass(sev) {
  if (sev === "fail") return "badge badge-fail";
  if (sev === "warn") return "badge badge-warn";
  return "badge badge-ok";
}

function renderFeatureNode(node) {
  const li = document.createElement("li");
  li.className = "tree-item";
  if (node.type === "EndOfPart") {
    li.className = "tree-eop";
    li.textContent = "── End of Part ──";
    return li;
  }
  if (node.suppressed || node.rolled_back) {
    li.classList.add("tree-suppressed");
  }
  const row = document.createElement("div");
  row.className = "tree-row";

  if (node.name && node.type) {
    row.dataset.feature = node.name;
    row.dataset.type = node.type;
    row.tabIndex = -1;
    if (EDITABLE_TYPES[node.type]) row.title = "Double-click to edit, right-click for more";
  }
  const nameSpan = document.createElement("span");
  nameSpan.className = "tree-name";
  nameSpan.textContent = node.name || "(unnamed)";
  row.appendChild(nameSpan);

  if (node.type) {
    const typeSpan = document.createElement("span");
    typeSpan.className = "tree-type";
    typeSpan.textContent = `[${node.type}]`;
    row.appendChild(typeSpan);
  }

  if (node.suppressed) {
    const sup = document.createElement("span");
    sup.className = "tree-meta";
    sup.textContent = "(suppressed)";
    row.appendChild(sup);
  }
  if (node.rolled_back) {
    const rb = document.createElement("span");
    rb.className = "tree-meta";
    rb.textContent = "(below End of Part)";
    row.appendChild(rb);
  }
  if (node.error) {
    const err = document.createElement("span");
    err.className = "badge badge-fail";
    err.textContent = `Error: ${node.error}`;
    row.appendChild(err);
  }
  li.appendChild(row);

  if (Array.isArray(node.children) && node.children.length > 0) {
    const ul = document.createElement("ul");
    ul.className = "tree-children";
    node.children.forEach((ch) => ul.appendChild(renderFeatureNode(ch)));
    li.appendChild(ul);
  }
  return li;
}

function renderOccurrenceNode(occ) {
  const li = document.createElement("li");
  li.className = "tree-item";

  const row = document.createElement("div");
  row.className = "tree-row";

  const nameSpan = document.createElement("span");
  nameSpan.className = "tree-name";
  nameSpan.textContent = occ.name;
  row.appendChild(nameSpan);

  if (occ.grounded) {
    const gSpan = document.createElement("span");
    gSpan.className = "badge badge-neutral";
    gSpan.textContent = "grounded";
    row.appendChild(gSpan);
  }

  if (occ.file) {
    const fSpan = document.createElement("span");
    fSpan.className = "tree-meta";
    fSpan.textContent = occ.file + (occ.file_missing ? " (FEHLT)" : "");
    row.appendChild(fSpan);
  }

  li.appendChild(row);

  const hasJoints = Array.isArray(occ.joints) && occ.joints.length > 0;
  const hasChildren = Array.isArray(occ.occurrences) && occ.occurrences.length > 0;
  if (hasJoints || hasChildren) {
    const ul = document.createElement("ul");
    ul.className = "tree-children";

    if (hasJoints) {
      for (const j of occ.joints) {
        const jli = document.createElement("li");
        jli.className = "tree-item";
        const jrow = document.createElement("div");
        jrow.className = "tree-row";

        const jname = document.createElement("span");
        jname.className = "tree-name";
        jname.textContent = `◆ ${j.name}`;
        jrow.appendChild(jname);

        const jtype = document.createElement("span");
        jtype.className = "tree-type";
        jtype.textContent = `[${j.type}] → ${j.with}`;
        jrow.appendChild(jtype);

        const st = j.status || "ok";
        const sev = j.severity || (st === "ok" ? "ok" : "warn");
        const jbadge = document.createElement("span");
        jbadge.className = statusBadgeClass(sev);
        jbadge.textContent = st;
        jrow.appendChild(jbadge);

        jli.appendChild(jrow);
        ul.appendChild(jli);
      }
    }

    if (hasChildren) {
      occ.occurrences.forEach((ch) => ul.appendChild(renderOccurrenceNode(ch)));
    }
    li.appendChild(ul);
  }
  return li;
}

function eyeButton(key, title) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "tree-eye";
  b.title = title;
  b.setAttribute("aria-label", title);
  b.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 8s2.5-4.5 6.5-4.5S14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="2"/></svg>';
  b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); toggleOrigin(key); });
  return b;
}

function renderOriginFolder() {
  const details = document.createElement("details");
  details.className = "tree-folder tree-origin";
  const summary = document.createElement("summary");
  summary.className = "tree-row tree-folder-summary";
  const nameSpan = document.createElement("span");
  nameSpan.className = "tree-name";
  nameSpan.textContent = "Origin";
  summary.appendChild(nameSpan);
  summary.appendChild(eyeButton("folder", "Show or hide the Origin"));
  details.appendChild(summary);

  const ul = document.createElement("ul");
  ul.className = "tree-children";
  for (const [key, label] of [["YZ", "YZ Plane"], ["XZ", "XZ Plane"], ["XY", "XY Plane"], ["X", "X Axis"], ["Y", "Y Axis"],
    ["Z", "Z Axis"], ["O", "Center Point"]]) {
    const li = document.createElement("li");
    li.className = "tree-item tree-origin-item";
    li.dataset.originRow = key;
    const span = document.createElement("span");
    span.className = "tree-meta";
    span.textContent = label;
    li.appendChild(span);
    li.appendChild(eyeButton(key, `Show or hide ${label}`));
    ul.appendChild(li);
  }
  details.appendChild(ul);
  return details;
}

function updateTreeView(treeData) {
  treeContentEl.innerHTML = "";
  if (!treeData) {
    treeContentEl.innerHTML = '<div class="empty-state">No model tree available</div>';
    return;
  }

  const rootHeader = document.createElement("div");
  rootHeader.className = "tree-root-header";
  rootHeader.textContent = (docNameEl && docNameEl.textContent && docNameEl.textContent !== "—")
    ? docNameEl.textContent
    : (treeData.kind === "assembly" ? "Assembly" : "Part");
  treeContentEl.appendChild(rootHeader);
  treeContentEl.appendChild(renderOriginFolder());
  loadOriginState();

  if (treeData.kind === "part") {
    const bodies = treeData.bodies || [];
    const features = treeData.features || [];
    if (bodies.length > 0) {
      const bDetails = document.createElement("details");
      bDetails.className = "tree-folder tree-bodies";
      const bSum = document.createElement("summary");
      bSum.className = "tree-row tree-folder-summary";
      const bName = document.createElement("span");
      bName.className = "tree-name";
      bName.textContent = `Solid Bodies (${bodies.length})`;
      bSum.appendChild(bName);
      bDetails.appendChild(bSum);

      const bList = document.createElement("ul");
      bList.className = "tree-children";
      bodies.forEach((b) => {
        const li = document.createElement("li");
        li.className = "tree-item tree-name";
        li.textContent = b;
        bList.appendChild(li);
      });
      bDetails.appendChild(bList);
      treeContentEl.appendChild(bDetails);
    }

    const fList = document.createElement("ul");
    fList.className = "tree-list";
    features.forEach((f) => fList.appendChild(renderFeatureNode(f)));
    if (!features.some((f) => f.type === "EndOfPart")) {
      fList.appendChild(renderFeatureNode({ type: "EndOfPart", name: "End of Part" }));
    }
    treeContentEl.appendChild(fList);
  } else {
    const occs = treeData.occurrences || [];
    const asmFeats = treeData.assembly_features || [];
    if (occs.length === 0 && asmFeats.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No components";
      treeContentEl.appendChild(empty);
      return;
    }
    if (occs.length > 0) {
      const oTitle = document.createElement("div");
      oTitle.className = "tree-section-title";
      oTitle.textContent = `Components (${occs.length})`;
      treeContentEl.appendChild(oTitle);

      const oList = document.createElement("ul");
      oList.className = "tree-list";
      occs.forEach((o) => oList.appendChild(renderOccurrenceNode(o)));
      treeContentEl.appendChild(oList);
    }
    if (asmFeats.length > 0) {
      const afTitle = document.createElement("div");
      afTitle.className = "tree-section-title";
      afTitle.textContent = "Assembly features";
      treeContentEl.appendChild(afTitle);

      const afList = document.createElement("ul");
      afList.className = "tree-list";
      asmFeats.forEach((f) => afList.appendChild(renderFeatureNode(f)));
      treeContentEl.appendChild(afList);
    }
  }
}

function selectFinding(idx) {
  if (selectedFindingIndex === idx) {
    selectedFindingIndex = null;
  } else {
    selectedFindingIndex = idx;
  }
  const cards = findingsContentEl.querySelectorAll(".finding-card");
  cards.forEach((c, i) => {
    c.classList.toggle("active", i === selectedFindingIndex);
  });
  highlightFinding(selectedFindingIndex !== null ? currentFindings[selectedFindingIndex] : null);
}

function updateFindingsView(data, preserveSelection) {
  currentFindings = (data && data.findings) || [];
  findingsCountEl.textContent = String(currentFindings.length);

  const verdict = (data && (data.verdict || data.status)) || "ok";
  verdictBadgeEl.className = statusBadgeClass(verdict);
  verdictBadgeEl.textContent = `Check: ${verdict.toUpperCase()}`;
  verdictBadgeEl.hidden = false;

  if (data && data.summary) {
    findingsSummaryEl.textContent = data.summary;
    findingsSummaryEl.hidden = false;
  } else {
    findingsSummaryEl.hidden = true;
  }

  findingsContentEl.innerHTML = "";
  if (currentFindings.length === 0) {
    findingsContentEl.innerHTML = '<div class="empty-state">No findings</div>';
    selectedFindingIndex = null;
    highlightFinding(null);
    return;
  }

  currentFindings.forEach((f, idx) => {
    const sev = f.severity || f.status || "ok";
    const card = document.createElement("div");
    card.className = `finding-card severity-${sev}`;
    card.dataset.index = String(idx);

    const header = document.createElement("div");
    header.className = "finding-header";

    const ruleSpan = document.createElement("span");
    ruleSpan.className = "finding-rule";
    ruleSpan.textContent = f.joint ? `${f.rule} (${f.joint})` : f.rule || "check";
    header.appendChild(ruleSpan);

    const badge = document.createElement("span");
    badge.className = statusBadgeClass(sev);
    badge.textContent = (f.status || sev).toUpperCase();
    header.appendChild(badge);

    card.appendChild(header);

    const msg = document.createElement("div");
    msg.className = "finding-msg";
    msg.textContent = f.message || "";
    card.appendChild(msg);

    const face = f.face || (f.location && f.location.face);
    const pt = f.point || (f.location && f.location.point);
    if (face) {
      const loc = document.createElement("div");
      loc.className = "finding-loc";
      loc.textContent = `Face: ${face}`;
      card.appendChild(loc);
    } else if (Array.isArray(pt) && pt.length === 3) {
      const loc = document.createElement("div");
      loc.className = "finding-loc";
      loc.textContent = `Punkt: [${pt.map((n) => Number(n).toFixed(1)).join(", ")}]`;
      card.appendChild(loc);
    }

    card.addEventListener("click", () => selectFinding(idx));
    findingsContentEl.appendChild(card);
  });

  if (preserveSelection && selectedFindingIndex !== null && selectedFindingIndex < currentFindings.length) {
    const cards = findingsContentEl.querySelectorAll(".finding-card");
    cards[selectedFindingIndex].classList.add("active");
    highlightFinding(currentFindings[selectedFindingIndex]);
  } else {
    const firstIssue = currentFindings.findIndex((f) => (f.severity || f.status) !== "ok");
    if (firstIssue >= 0) {
      selectedFindingIndex = null;
      selectFinding(firstIssue);
    } else {
      selectedFindingIndex = null;
      highlightFinding(null);
    }
  }
}

// Static mode (live demo on GitHub Pages): precomputed JSON under demos/<name>/, no polling.
const STATIC = document.documentElement.dataset.static === "1";
let demoBase = "";

// Session log (mechvane/ui/sessionlog.py): what happens in the browser goes to the server's log, for debugging
// test sessions; in the live demo there is no server and nothing is sent
const logBuffer = [];
function clientLog(kind, data = {}) {
  if (STATIC) return;
  logBuffer.push({ kind, ...data });
  if (logBuffer.length > 300) logBuffer.splice(0, logBuffer.length - 300);
}
function flushLog(beacon = false) {
  if (STATIC || !logBuffer.length) return;
  const body = JSON.stringify({ events: logBuffer.splice(0) });
  if (beacon && navigator.sendBeacon) navigator.sendBeacon("api/log", body);
  else fetch("api/log", { method: "POST", body }).catch(() => {});
}
if (!STATIC) {
  setInterval(flushLog, 1500);
  window.addEventListener("pagehide", () => {
    flushLog(true);
    // a closed app window stops Mechvane (the server waits a few seconds: a reload comes back at once)
    if (navigator.sendBeacon) navigator.sendBeacon("api/closing", "{}");
  });
  window.addEventListener("error", (e) => clientLog("js_error", { message: e.message, at: `${e.filename}:${e.lineno}:${e.colno}`,
                                                                 stack: e.error && e.error.stack }));
  window.addEventListener("unhandledrejection", (e) => clientLog("js_rejection", { message: String(e.reason && (e.reason.stack || e.reason)) }));
  const origError = console.error.bind(console);
  console.error = (...a) => { clientLog("console_error", { message: a.map(String).join(" ") }); origError(...a); };
  clientLog("page", { url: location.href, size: `${innerWidth}x${innerHeight}`, touch: navigator.maxTouchPoints > 0,
                      agent: navigator.userAgent });
}

// Live demo: the api/* requests of the dialogs go to the demo kernel (SolidCraft in a hidden iframe)
let demoKernel = null;
async function kernel() {
  if (!demoKernel) {
    const { createDemoKernel } = await import("./demo_kernel.js");
    demoKernel = createDemoKernel({ base: () => demoBase, onStatus: (t) => { statusEl.textContent = t; } });
  }
  return demoKernel;
}

async function fetchJson(url, opts = {}) {
  if (STATIC && url.startsWith("api/")) {
    return (await kernel()).api(opts.method || "GET", url, opts.body ? JSON.parse(opts.body) : null);
  }
  const res = await fetch(url, { cache: "no-store", ...opts });
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.error || `HTTP ${res.status}`);
    Object.assign(err, data);
    throw err;
  }
  return data;
}

function dataUrl(name) {
  // the demo shows the precomputed example until a step was made in it
  if (STATIC && !(demoKernel && demoKernel.changed)) return `${demoBase}${name}.json`;
  return `api/${name}`;
}

// Profile and material for the design rules, saved in the part file (POST /api/rules)
const ruleSetupEl = document.getElementById("rule-setup");
const ruleProfileEl = document.getElementById("rule-profile");
const ruleMaterialEl = document.getElementById("rule-material");

function fillRuleSetup(data) {
  if (STATIC || !data.profiles) return;
  const fill = (el, entries, value) => {
    el.replaceChildren(...entries.map(([v, label]) => new Option(label, v, false, v === value)));
  };
  fill(ruleProfileEl, Object.entries(data.profiles), data.profile);
  fill(ruleMaterialEl, [["", "Material: from part"], ...data.materials.map((m) => [m, m.replace(/_/g, " ")])],
    data.material_source === "saved" ? data.material : "");
  ruleSetupEl.hidden = false;
}

async function changeRules() {
  statusEl.textContent = "Computing…";
  try {
    const data = await fetchJson("api/rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: ruleProfileEl.value, material: ruleMaterialEl.value }),
    });
    updateFindingsView(data, true);
    fillRuleSetup(data);
    statusEl.textContent = "Ready";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
}
ruleProfileEl.addEventListener("change", changeRules);
ruleMaterialEl.addEventListener("change", changeRules);

async function loadAll(initial = false) {
  try {
    statusEl.textContent = "Computing…";
    const ver = await fetchJson(dataUrl("version"));
    docNameEl.textContent = ver.name || "Document";
    const [mesh, tree, findings] = await Promise.all([
      fetchJson(dataUrl("mesh")),
      fetchJson(dataUrl("tree")),
      fetchJson(dataUrl("findings")),
    ]);
    currentVersion = ver.version;
    docNameEl.textContent = ver.name || "Document";
    docKindEl.textContent = ver.kind === "assembly" ? "Assembly" : "Part";
    docKindEl.hidden = false;
    docPathEl.textContent = STATIC ? "" : (ver.path || "");

    viewBeforeEdit = null;  // a dialog editing a feature showed an earlier state: the new model replaces it
    updateMeshView(mesh, initial);
    if (featureDialogs) featureDialogs.modelChanged();
    updateTreeView(tree);
    updateFindingsView(findings, !initial);
    // rules are saved per part; an assembly has none to choose
    if (ver.kind === "assembly") ruleSetupEl.hidden = true;
    else fillRuleSetup(findings);
    if (!STATIC) await loadParams();
    refreshHistory();
    statusEl.textContent = "Ready";
    // unused sketches come after: in the live demo /api/sketches takes seconds, Undo must not wait for it
    refreshSketchOverlay(ver.kind, initial).catch(() => {});
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
}

// Sketches nothing uses yet stay visible in the model, as in Inventor: drawn on their planes over the bodies.
// Not in the precomputed live demo (that would start SolidCraft in the page); after a step there, yes.
const sketchOverlay = new THREE.Group();
sketchOverlay.renderOrder = 8;
scene.add(sketchOverlay);
async function refreshSketchOverlay(kind, fit = false) {
  clearGroup(sketchOverlay);
  if (kind === "assembly" || (STATIC && !(demoKernel && demoKernel.changed))) { renderScene(); return; }
  let list = [];
  try { list = (await fetchJson("api/sketches")).sketches || []; } catch (_) { return; }
  const isDark = document.documentElement.dataset.theme !== "light";
  for (const sk of list) {
    if ((sk.used_by || []).length || !sk.plane) continue;
    for (const c of sk.curves || []) {
      const pts = curvePoints(c);
      if (pts.length < 2) continue;
      const mat = c.construction
        ? new THREE.LineDashedMaterial({ color: 0x8b949e, dashSize: 2, gapSize: 1.5, depthTest: false })
        : new THREE.LineBasicMaterial({ color: isDark ? 0x58a6ff : 0x1f6feb, depthTest: false });
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(toWorld(sk.plane, pts)), mat);
      if (c.construction) line.computeLineDistances();
      line.renderOrder = 8;
      line.userData.sketch = sk.name;
      sketchOverlay.add(line);
    }
  }
  sketchOverlay.visible = !document.body.classList.contains("sketching");
  // zoom all and home take the unused sketches in, as in Inventor
  if (sketchOverlay.children.length) {
    const box = new THREE.Box3().setFromObject(modelGroup);
    box.union(new THREE.Box3().setFromObject(sketchOverlay));
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    if (sphere.radius > modelRadius * 1.01 || sphere.center.distanceTo(modelCenter) > modelRadius * 0.01) {
      modelRadius = Math.max(sphere.radius, 5);
      modelCenter.copy(sphere.center);
      if (fit) fitCameraToModel(false);
    }
  }
  renderScene();
}

// The Origin as SolidCraft draws it (crates/ui-egui/src/selection.rs origin_quads/origin_size): the three planes
// as squares in the positive quadrant, the axes and the centre point, sized to 15 % of the visible height so
// they stay the same on screen. Shown by default; the Origin folder and each item hide one by one (kept per
// document in the browser). While Create 2D Sketch waits for its plane, hidden planes come back to be clicked.
const ORIGIN_PLANES = { XY: [[1, 0, 0], [0, 1, 0]], XZ: [[1, 0, 0], [0, 0, 1]], YZ: [[0, 1, 0], [0, 0, 1]] };
const ORIGIN_AXES = { X: [[1, 0, 0], 0xe5534b], Y: [[0, 1, 0], 0x57ab5a], Z: [[0, 0, 1], 0x539bf5] };
// var: renderScene runs before this point while the page starts
var originGroup = new THREE.Group();
originGroup.renderOrder = 7;
scene.add(originGroup);
const originParts = {};
for (const [name, [u, v]] of Object.entries(ORIGIN_PLANES)) {
  const a = new THREE.Vector3(...u), b = new THREE.Vector3(...v);
  const corners = [new THREE.Vector3(), a.clone(), a.clone().add(b), b.clone()];
  const geom = new THREE.BufferGeometry().setFromPoints([corners[0], corners[1], corners[2], corners[0], corners[2], corners[3]]);
  const fill = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({ color: 0xd29922, transparent: true, opacity: 0.12,
    side: THREE.DoubleSide, depthWrite: false }));
  const edge = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(corners),
    new THREE.LineBasicMaterial({ color: 0xd29922, transparent: true, opacity: 0.7 }));
  const g = new THREE.Group();
  g.add(fill, edge);
  g.userData = { origin: name, kind: "plane", fill };
  originGroup.add(g);
  originParts[name] = g;
}
for (const [name, [d, color]] of Object.entries(ORIGIN_AXES)) {
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3(...d).multiplyScalar(1.3)]),
    new THREE.LineBasicMaterial({ color }));
  line.userData = { origin: name, kind: "axis" };
  originGroup.add(line);
  originParts[name] = line;
}
{
  const dot = new THREE.Mesh(new THREE.SphereGeometry(0.035, 12, 8), new THREE.MeshBasicMaterial({ color: 0xd29922 }));
  dot.userData = { origin: "O", kind: "point" };
  originGroup.add(dot);
  originParts.O = dot;
}
var originState = { folder: true, hidden: new Set(), reveal: false, hover: null };
const originKey = () => `mechvane-origin:${docNameEl?.textContent || "doc"}`;
function loadOriginState() {
  try {
    const st = JSON.parse(localStorage.getItem(originKey()) || "{}");
    originState.folder = st.folder !== false;
    originState.hidden = new Set(st.hidden || []);
  } catch (_) { /* defaults */ }
  applyOrigin();
}
function saveOriginState() {
  try { localStorage.setItem(originKey(), JSON.stringify({ folder: originState.folder, hidden: [...originState.hidden] })); } catch (_) { /* private mode */ }
}
function applyOrigin() {
  for (const [name, part] of Object.entries(originParts)) {
    const plane = part.userData.kind === "plane";
    part.visible = (originState.reveal && plane) || (originState.folder && !originState.hidden.has(name));
    if (plane) part.userData.fill.material.opacity = originState.hover === name ? 0.35 : 0.12;
  }
  document.querySelectorAll("[data-origin-row]").forEach((li) => {
    const off = !originState.folder || originState.hidden.has(li.dataset.originRow);
    li.classList.toggle("origin-hidden", off);
  });
  const folder = document.querySelector(".tree-origin");
  if (folder) folder.classList.toggle("origin-hidden", !originState.folder);
  renderScene();
}
function toggleOrigin(name) {
  if (name === "folder") originState.folder = !originState.folder;
  else if (originState.hidden.has(name)) { originState.hidden.delete(name); originState.folder = true; }
  else originState.hidden.add(name);
  saveOriginState();
  applyOrigin();
}
// keep the Origin 15 % of the visible height, as SolidCraft's origin_size
function scaleOrigin() {
  const visibleHeight = (camera.top - camera.bottom) / (camera.zoom || 1);
  originGroup.scale.setScalar(Math.max(visibleHeight * 0.15, 1e-3));
}
// the origin plane under the pointer (shown ones only), for Create 2D Sketch
function originPlaneAt(clientX, clientY) {
  const r = renderer.domElement.getBoundingClientRect();
  const ray = new THREE.Raycaster();
  ray.setFromCamera(new THREE.Vector2(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1), camera);
  const fills = Object.values(originParts).filter((p) => p.userData.kind === "plane" && p.visible).map((p) => p.userData.fill);
  const hit = ray.intersectObjects(fills, false)[0];
  if (!hit) return null;
  // a body face in front of the plane wins (the face pick of Create 2D Sketch takes it)
  const body = ray.intersectObjects(modelGroup.children, true).find((h) => h.object.isMesh);
  return body && body.distance < hit.distance - 1e-6 ? null : hit.object.parent.userData.origin;
}
function revealOriginPlanes(on) {
  originState.reveal = on;
  if (!on) originState.hover = null;
  applyOrigin();
}
function hoverOriginPlane(name) {
  if (originState.hover === name) return;
  originState.hover = name;
  applyOrigin();
}

// Parameter form: user parameters first, feature dimensions folded away. Changes go to SolidCraft
// together (all or nothing); the saved file then reloads the view through pollVersion.
const paramsSection = document.getElementById("params-section");
const paramsForm = document.getElementById("params-form");
const paramsApply = document.getElementById("params-apply");
const paramsError = document.getElementById("params-error");

function paramRow(p) {
  const row = document.createElement("label");
  row.className = "param-row";
  row.title = p.feature ? `${p.feature} · ${p.input || ""}` : (p.comment || "");
  const name = document.createElement("span");
  name.className = "param-name";
  name.textContent = p.name;
  const input = document.createElement("input");
  input.type = "text";
  input.name = p.name;
  input.value = p.expression;
  input.dataset.original = p.expression;
  input.spellcheck = false;
  input.addEventListener("input", () => {
    input.classList.toggle("param-changed", input.value !== input.dataset.original);
    paramsApply.disabled = !paramsForm.querySelector(".param-changed");
  });
  const value = document.createElement("span");
  value.className = "param-value";
  value.textContent = p.error ? "error" : `${+Number(p.value).toFixed(4)} ${p.unit || ""}`;
  if (p.error) value.title = p.error;
  row.append(name, input, value);
  return row;
}

function updateParamsView(data) {
  const params = data.parameters || [];
  paramsForm.replaceChildren();
  paramsSection.hidden = params.length === 0;
  const own = params.filter((p) => p.source === "user" || p.favorite);
  const dims = params.filter((p) => !own.includes(p));
  own.forEach((p) => paramsForm.appendChild(paramRow(p)));
  if (dims.length) {
    const more = document.createElement("details");
    more.open = own.length === 0;
    const sum = document.createElement("summary");
    sum.textContent = `Feature dimensions (${dims.length})`;
    more.appendChild(sum);
    dims.forEach((p) => more.appendChild(paramRow(p)));
    paramsForm.appendChild(more);
  }
  paramsApply.disabled = true;
}

async function loadParams() {
  try {
    updateParamsView(await fetchJson("api/params"));
  } catch {
    paramsSection.hidden = true;
  }
}

async function applyParams(ev) {
  if (ev) ev.preventDefault();
  const changes = {};
  paramsForm.querySelectorAll(".param-changed").forEach((i) => { changes[i.name] = i.value; });
  if (!Object.keys(changes).length) return;
  paramsApply.disabled = true;
  paramsError.hidden = true;
  statusEl.textContent = "Computing…";
  try {
    const res = await fetch("api/params", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ changes }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    updateParamsView(data);
    await pollVersion();
    statusEl.textContent = "Ready";
  } catch (err) {
    paramsError.textContent = err.message;
    paramsError.hidden = false;
    paramsApply.disabled = false;
    statusEl.textContent = "Not changed";
  }
}

if (!STATIC) {
  paramsForm.addEventListener("submit", applyParams);
  paramsForm.addEventListener("keydown", (e) => { if (e.key === "Enter") applyParams(e); });
  paramsApply.addEventListener("click", applyParams);
}

// Ribbon tabs, File menu, Ribbon buttons, keyboard shortcuts (F6, Esc) and panel splitters
const fileMenu = document.getElementById("file-menu");
const ribbonTabs = Array.from(document.querySelectorAll(".ribbon-tab[data-tab]"));
const ribbonPanels = Array.from(document.querySelectorAll(".ribbon-panel[data-tab-panel]"));

function activateRibbonTab(tabId) {
  for (const tab of ribbonTabs) {
    const active = tab.dataset.tab === tabId;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
  }
  for (const panel of ribbonPanels) {
    const active = panel.dataset.tabPanel === tabId;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  }
}

for (const tab of ribbonTabs) {
  tab.addEventListener("click", () => activateRibbonTab(tab.dataset.tab));
}

document.addEventListener("click", (e) => {
  if (fileMenu && fileMenu.open && !fileMenu.contains(e.target)) {
    fileMenu.open = false;
  }
});

const btnRibbonParams = document.getElementById("btn-ribbon-params");
if (btnRibbonParams) {
  btnRibbonParams.addEventListener("click", () => {
    paramsSection.hidden = false;
    if (!paramsForm.children.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No parameters in this document";
      paramsForm.appendChild(empty);
    }
    paramsSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    const firstInput = paramsForm.querySelector("input");
    if (firstInput) firstInput.focus();
  });
}

const btnDesignCheck = document.getElementById("btn-design-check");
const designCheckSection = document.getElementById("design-check-section");
if (btnDesignCheck && designCheckSection) {
  btnDesignCheck.addEventListener("click", () => {
    designCheckSection.open = true;
    designCheckSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    if (ruleProfileEl && !ruleSetupEl.hidden) ruleProfileEl.focus();
  });
}

const btnRibbonHome = document.getElementById("btn-ribbon-home");
const btnHomeView = document.getElementById("btn-home-view");
const btnZoomAll = document.getElementById("btn-zoom-all");
if (btnRibbonHome) btnRibbonHome.addEventListener("click", homeView);
if (btnHomeView) btnHomeView.addEventListener("click", homeView);
if (btnZoomAll) btnZoomAll.addEventListener("click", zoomAll);

window.addEventListener("keydown", (e) => {
  if (e.key === "F6") {
    e.preventDefault();
    homeView();
  } else if (e.key === "Escape") {
    if (fileMenu && fileMenu.open) fileMenu.open = false;
    if (selectedFindingIndex !== null) {
      selectFinding(selectedFindingIndex);
    }
  }
});

const LEFT_WIDTH_KEY = "mechvane.ui.leftWidth";
const RIGHT_WIDTH_KEY = "mechvane.ui.rightWidth";

function initSplitters() {
  try {
    const lw = Number(localStorage.getItem(LEFT_WIDTH_KEY));
    if (lw >= 180 && lw <= 600) {
      document.documentElement.style.setProperty("--left-panel-width", `${lw}px`);
    }
    const rw = Number(localStorage.getItem(RIGHT_WIDTH_KEY));
    if (rw >= 220 && rw <= 640) {
      document.documentElement.style.setProperty("--right-panel-width", `${rw}px`);
    }
  } catch {
    // localStorage may be blocked or unavailable
  }

  const bindSplitter = (el, side) => {
    if (!el) return;
    let dragging = false;
    el.addEventListener("pointerdown", (e) => {
      if (window.innerWidth <= 760) return;
      e.preventDefault();
      dragging = true;
      el.classList.add("dragging");
      el.setPointerCapture(e.pointerId);
    });
    el.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      if (side === "left") {
        const w = Math.round(Math.min(600, Math.max(180, e.clientX)));
        document.documentElement.style.setProperty("--left-panel-width", `${w}px`);
      } else {
        const w = Math.round(Math.min(640, Math.max(220, window.innerWidth - e.clientX)));
        document.documentElement.style.setProperty("--right-panel-width", `${w}px`);
      }
      resizeViewport();
    });
    const finish = () => {
      if (!dragging) return;
      dragging = false;
      el.classList.remove("dragging");
      try {
        const val = document.documentElement.style.getPropertyValue(
          side === "left" ? "--left-panel-width" : "--right-panel-width"
        );
        const px = parseInt(val, 10);
        if (px) {
          localStorage.setItem(side === "left" ? LEFT_WIDTH_KEY : RIGHT_WIDTH_KEY, String(px));
        }
      } catch {
        // ignore storage errors
      }
    };
    el.addEventListener("pointerup", finish);
    el.addEventListener("pointercancel", finish);
  };

  bindSplitter(document.getElementById("splitter-left"), "left");
  bindSplitter(document.getElementById("splitter-right"), "right");
}

initSplitters();
resizeViewport();

function populateFileDocList(items, currentVal, onSelect) {
  const listEl = document.getElementById("file-doc-list");
  if (!listEl) return;
  listEl.replaceChildren();
  for (const item of items) {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "file-doc-item" + (item.value === currentVal ? " active" : "");
    btn.textContent = item.label;
    btn.dataset.value = item.value;
    btn.addEventListener("click", () => {
      onSelect(item.value);
      if (fileMenu) fileMenu.open = false;
    });
    li.appendChild(btn);
    listEl.appendChild(li);
  }
}

async function pollVersion() {
  try {
    const ver = await fetchJson(dataUrl("version"));
    if (currentVersion !== null && ver.version !== currentVersion) {
      currentVersion = ver.version;
      await loadAll(false);
    }
  } catch (err) {
    statusEl.textContent = "Connection lost";
  }
}

async function initStatic() {
  const index = await fetchJson("demos/index.json");
  const select = document.getElementById("demo-select");
  const items = index.demos.map((d) => ({ value: d.name, label: d.title }));
  for (const d of index.demos) {
    const opt = document.createElement("option");
    opt.value = d.name;
    opt.textContent = d.title;
    select.appendChild(opt);
  }
  const wanted = new URLSearchParams(location.search).get("demo");
  if (wanted && index.demos.some((d) => d.name === wanted)) select.value = wanted;
  const open = async (fit) => {
    demoBase = `demos/${select.value}/`;
    document.getElementById("mode-model").href = `model?demo=${select.value}`;
    populateFileDocList(items, select.value, (val) => {
      select.value = val;
      select.dispatchEvent(new Event("change"));
    });
    await loadAll(fit);
  };
  select.addEventListener("change", () => {
    if (fileMenu) fileMenu.open = false;
    // SolidCraft in the page holds the other example: start afresh with this one
    if (demoKernel && demoKernel.started) {
      location.search = `?demo=${select.value}`;
      return;
    }
    demoKernel = null;
    history.replaceState(null, "", `?demo=${select.value}`);
    open(true);
  });
  document.getElementById("demo-bar").hidden = false;
  await open(true);
}

// A project folder (`mechvane ui <folder>`, `--demo`): no document is open yet. List the folder's
// documents in the selector and open the one asked for (?doc=), else the first assembly, else the first.
async function initFolder() {
  const project = await fetchJson("api/project");
  if (project.mode !== "folder") return;
  const newPartBtn = document.getElementById("btn-new-part");
  if (newPartBtn) {
    newPartBtn.hidden = false;
    newPartBtn.addEventListener("click", () => {
      if (fileMenu) fileMenu.open = false;
      openNewPartDialog((project.documents || []).map((d) => d.name), (data) => {
        statusEl.textContent = "Computing…";
        location.search = `?doc=${encodeURIComponent(data.document)}`;
      });
    });
  }
  const importBtn = document.getElementById("btn-import-step");
  if (importBtn && project.mode === "folder") {
    importBtn.hidden = false;
    importBtn.addEventListener("click", async () => {
      if (fileMenu) fileMenu.open = false;
      // the folder may have new files since the page loaded
      const fresh = await fetchJson("api/project").catch(() => project);
      openImportStepDialog(fresh.step_files || [], (data) => {
        statusEl.textContent = "Computing…";
        location.search = `?doc=${encodeURIComponent(data.document)}`;
      });
    });
  }
  const docs = project.documents || [];
  if (!docs.length) {
    statusEl.textContent = "No .solidcraft files in this folder yet: click File → New part…";
    docNameEl.textContent = "No document";
    for (const el of [treeContentEl, findingsContentEl]) {
      el.innerHTML = '<div class="empty-state">Nothing open yet</div>';
    }
    return false;
  }
  const select = document.getElementById("demo-select");
  const sectionLabel = document.getElementById("demo-section-label");
  if (sectionLabel) sectionLabel.textContent = "Open from folder";
  for (const a of document.querySelectorAll("#demo-bar a")) a.hidden = true;  // "Install to open your own files": live demo only
  const items = docs.map((d) => ({
    value: d.name,
    label: d.name.replace(/\.solidcraft$/, "") + (d.kind === "assembly" ? " (assembly)" : ""),
  }));
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item.value;
    opt.textContent = item.label;
    select.appendChild(opt);
  }
  const wanted = new URLSearchParams(location.search).get("doc");
  const pick = [wanted, project.current, (docs.find((d) => d.kind === "assembly") || {}).name, docs[0].name]
    .find((n) => n && docs.some((d) => d.name === n));
  select.value = pick;
  const open = async (fit) => {
    const res = await fetch("api/open/" + encodeURIComponent(select.value), { method: "POST" });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || `HTTP ${res.status}`);
    document.getElementById("mode-model").href = `model?doc=${encodeURIComponent(select.value)}`;
    populateFileDocList(items, select.value, (val) => {
      select.value = val;
      select.dispatchEvent(new Event("change"));
    });
    currentVersion = null;
    await loadAll(fit);
  };
  select.addEventListener("change", () => {
    if (fileMenu) fileMenu.open = false;
    history.replaceState(null, "", `?doc=${encodeURIComponent(select.value)}`);
    open(true).catch((err) => { statusEl.textContent = `Error: ${err.message}`; });
  });
  document.getElementById("demo-bar").hidden = false;
  await open(true);
  return true;
}

if (STATIC) {
  initStatic().catch((err) => { statusEl.textContent = `Error: ${err.message}`; });
} else {
  let poll = true;
  initFolder()
    .then((opened) => {
      // Empty folder: no document to poll, keep the hint instead of "Connection lost", and
      // reload once a document appears (made with "New part" in Model by hand)
      if (opened === false) {
        poll = false;
        setInterval(async () => {
          const p = await fetchJson("api/project").catch(() => null);
          if (p && (p.documents || []).length) location.reload();
        }, 3000);
      }
      if (opened === undefined) return loadAll(true);
    })
    .catch((err) => { statusEl.textContent = `Error: ${err.message}`; })
    .finally(() => { if (poll) setInterval(pollVersion, 2000); });
}

// The agent chat below the findings (not in the static live demo, there is no agent there)
if (!STATIC) {
  initAgentChat({
    root: document.getElementById("agent-chat"),
    getSelection: () => viewTools.getSelection(),
    clearSelection: () => viewTools.clearSelection(),
    // only the agent's own turns: a hand step is busy for a moment too and sets its own status
    onBusy: (b) => {
      if (b) statusEl.textContent = "Computing…";
      else if (statusEl.textContent === "Computing…") statusEl.textContent = "Ready";
    },
    onChanged: () => loadAll(false),
  });
}

// Preview of a feature dialog: the result drawn in place of the model, while picks still hit the
// model underneath (the raycaster ignores visibility), so more edges can be added during a preview
const previewGroup = new THREE.Group();
scene.add(previewGroup);
let hiddenForPreview = null;

function showPreview(meshData) {
  if (!hiddenForPreview) {
    hiddenForPreview = modelGroup.children.filter((o) => o.visible);
    hiddenForPreview.forEach((o) => { o.visible = false; });
  }
  clearGroup(previewGroup);
  const isDark = document.documentElement.dataset.theme !== "light";
  for (const b of (meshData && meshData.bodies) || []) {
    if (!b.positions || !b.positions.length) continue;
    const { geom, edgeGeom } = buildBodyGeometryAndEdges(b);
    previewGroup.add(new THREE.Mesh(geom, new THREE.MeshStandardMaterial({
      color: isDark ? 0x7d9cc4 : 0x9db8da, roughness: 0.5, metalness: 0.1, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
    })));
    if (edgeGeom.attributes.position.count > 0) {
      previewGroup.add(new THREE.LineSegments(edgeGeom, new THREE.LineBasicMaterial({
        color: isDark ? 0x1e242c : 0x334155, transparent: true, opacity: 0.6 })));
    }
  }
  renderScene();
}

function clearPreview() {
  clearGroup(previewGroup);
  if (hiddenForPreview) {
    hiddenForPreview.forEach((o) => { if (o.parent === modelGroup) o.visible = true; });
    hiddenForPreview = null;
  }
  renderScene();
}

async function postJson(url, body) {
  return fetchJson(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

// A sketch turns the view onto its plane: looking against the normal, the sketch's Y up
function lookAlongFrame(frame) {
  if (!frame) return fitCameraToModel(false);
  const x = new THREE.Vector3(...frame.x_dir), y = new THREE.Vector3(...frame.y_dir);
  const n = new THREE.Vector3().crossVectors(x, y).normalize();
  // an empty part has no size yet: leave room for a first sketch of a few centimetres
  const empty = !(currentMeshData && (currentMeshData.bodies || []).length);
  const dist = modelRadius * 4 + 50;
  viewHalf = empty ? 60 : Math.max(modelRadius * 1.3, 30);
  camera.zoom = 1;
  setFrustum();
  camera.far = dist + modelRadius * 8 + 1000;
  camera.up.copy(y);
  camera.position.copy(modelCenter).addScaledVector(n, dist);
  controls.target.copy(modelCenter);
  camera.lookAt(modelCenter);
  controls.update();
  updateAxesGizmo();
  renderScene();
}

var featureDialogs = null;
var sketcher = null;
var viewBeforeEdit = null;
{
  featureDialogs = initFeatureDialogs({
    scene, viewTools, renderScene,
    propertiesEl: document.getElementById("properties-content"),
    statusEl, post: postJson, get: (url) => fetchJson(url), showPreview, clearPreview, log: clientLog,
    reload: () => loadAll(false),
    // editing a feature shows the model as it was before it; Cancel puts the current model back
    showModel: (mesh) => {
      if (!viewBeforeEdit) viewBeforeEdit = currentMeshData;
      updateMeshView(mesh, false);
    },
    restoreModel: () => {
      if (viewBeforeEdit) updateMeshView(viewBeforeEdit, false);
      viewBeforeEdit = null;
    },
    lookAlong: lookAlongFrame,
  });
  initTreeActions();
  // the sketch environment (ADR 0005): not in the live demo yet, it needs the SolidCraft session on the server
  // in the live demo the same environment runs on the demo kernel (demo_kernel.js), SolidCraft in the browser
  const btnSketch = document.getElementById("btn-sketch");
  {
    sketcher = initSketcher({
      resume: !STATIC,
      scene, camera, renderer, controls, renderScene, viewTools, lookAlong: lookAlongFrame, statusEl, viewportEl,
      get: (url) => fetchJson(url), post: postJson, reload: () => loadAll(false), activateTab: activateRibbonTab,
      log: clientLog, isDark: () => document.documentElement.dataset.theme !== "light",
      // the sketch being edited is drawn by the sketcher, not twice by the overlay of unused sketches
      onMode: (on) => { sketchOverlay.visible = !on; renderScene(); },
      originPlaneAt, revealOriginPlanes, hoverOriginPlane,
    });
    if (btnSketch) {
      btnSketch.disabled = false;
      btnSketch.title = btnSketch.dataset.title || btnSketch.title;
      btnSketch.addEventListener("click", () => sketcher.start());
    }
  }
  document.querySelectorAll("[data-feature]").forEach((b) => {
    b.disabled = false;
    b.title = b.dataset.title || b.title;
    b.addEventListener("click", () => featureDialogs.open(b.dataset.feature));
  });
}

// Undo and Redo: one list for hand steps (dialogs, parameters) and the agent's turns (Grundsatz 6)
const undoBtn = document.getElementById("btn-undo");
const redoBtn = document.getElementById("btn-redo");

function refreshHistory() {
  fetchJson("api/history").then((h) => {
    undoBtn.disabled = !h.undo || h.busy;
    redoBtn.disabled = !h.redo || h.busy;
    undoBtn.title = h.undo ? `Undo: ${h.undo} (Ctrl+Z)` : "Nothing to undo";
    redoBtn.title = h.redo ? `Redo: ${h.redo} (Ctrl+Y)` : "Nothing to redo";
  }).catch(() => {});
}

async function undoRedo(which) {
  if (featureDialogs && featureDialogs.isOpen()) featureDialogs.close();
  try {
    await postJson(`api/agent/${which}`, {});
    refreshHistory();  // the buttons follow at once, the model view may take a moment
    await loadAll(false);
    statusEl.textContent = which === "undo" ? "Undone" : "Redone";
  } catch (err) {
    statusEl.textContent = `${which === "undo" ? "Undo" : "Redo"}: ${err.message}`;
    refreshHistory();
  }
}

{
  undoBtn.hidden = false;
  redoBtn.hidden = false;
  undoBtn.addEventListener("click", () => undoRedo("undo"));
  redoBtn.addEventListener("click", () => undoRedo("redo"));
  setInterval(refreshHistory, 4000);
  window.addEventListener("keydown", (e) => {
    const t = e.target;
    if (t && t.closest && t.closest("input, textarea, select, [contenteditable]")) return;
    if (document.querySelector("dialog[open]")) return;
    const mod = e.ctrlKey || e.metaKey;
    if (mod && !e.altKey && (e.key === "z" || e.key === "Z") && !e.shiftKey) {
      e.preventDefault();
      if (!undoBtn.disabled) undoRedo("undo");
    } else if (mod && !e.altKey && (e.key === "y" || e.key === "Y" || ((e.key === "z" || e.key === "Z") && e.shiftKey))) {
      e.preventDefault();
      if (!redoBtn.disabled) undoRedo("redo");
    } else if (!mod && !e.altKey && (e.key === "f" || e.key === "F")) {
      e.preventDefault();
      featureDialogs.open("fillet");
    } else if (!mod && !e.altKey && (e.key === "s" || e.key === "S") && sketcher) {
      e.preventDefault();
      sketcher.start();
    } else if (!mod && !e.altKey && (e.key === "e" || e.key === "E")) {
      e.preventDefault();
      featureDialogs.open("extrude");
    } else if (!mod && !e.altKey && (e.key === "h" || e.key === "H")) {
      e.preventDefault();
      featureDialogs.open("hole");
    }
  });
}

// Model browser: double-click edits a feature in its dialog, right-click offers Edit and Delete,
// Delete removes the selected feature (Ctrl+Z puts it back)
function initTreeActions() {
  let selectedRow = null;
  const menu = document.createElement("div");
  menu.className = "context-menu";
  menu.hidden = true;
  document.body.append(menu);
  const hideMenu = () => { menu.hidden = true; };

  function select(row) {
    if (selectedRow) selectedRow.classList.remove("selected");
    selectedRow = row;
    if (row) row.classList.add("selected");
  }
  const rowOf = (e) => e.target.closest && e.target.closest(".tree-row[data-feature]");

  treeContentEl.addEventListener("click", (e) => {
    hideMenu();
    const row = rowOf(e);
    // a pattern or mirror dialog is open: the click picks the feature for it
    if (row && featureDialogs.pickFeature(row.dataset.feature, row.dataset.type)) return;
    select(row);
  });
  treeContentEl.addEventListener("dblclick", (e) => {
    if (featureDialogs.picksFeatures()) return;
    const row = rowOf(e);
    if (row && row.dataset.type === "Sketch" && sketcher) sketcher.edit(row.dataset.feature);
    else if (row && EDITABLE_TYPES[row.dataset.type]) featureDialogs.edit(row.dataset.feature);
  });
  treeContentEl.addEventListener("contextmenu", (e) => {
    const originRow = e.target.closest && e.target.closest("[data-origin-row]");
    if (originRow) {
      // as SolidCraft's origin_plane_items: Create Sketch on a plane, Show/Hide on every item
      e.preventDefault();
      const key = originRow.dataset.originRow;
      menu.innerHTML = "";
      const add = (label, fn) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "context-item";
        b.textContent = label;
        b.addEventListener("click", () => { hideMenu(); fn(); });
        menu.append(b);
      };
      if (ORIGIN_PLANES[key] && sketcher) add(`Create Sketch on ${key}`, () => sketcher.startOn(key));
      add(originState.folder && !originState.hidden.has(key) ? "Hide" : "Show", () => toggleOrigin(key));
      menu.style.left = `${e.clientX}px`;
      menu.style.top = `${e.clientY}px`;
      menu.hidden = false;
      return;
    }
    const row = rowOf(e);
    if (!row) return;
    e.preventDefault();
    select(row);
    const name = row.dataset.feature;
    menu.innerHTML = "";
    const item = (label, fn, disabled = false) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "context-item";
      b.textContent = label;
      b.disabled = disabled;
      b.addEventListener("click", () => { hideMenu(); fn(); });
      menu.append(b);
    };
    if (row.dataset.type === "Sketch" && sketcher) item(`Edit ${name}`, () => sketcher.edit(name), false);
    else item(`Edit ${name}`, () => featureDialogs.edit(name), !EDITABLE_TYPES[row.dataset.type]);
    item(`Delete ${name}`, () => featureDialogs.remove(name));
    menu.style.left = `${e.clientX}px`;
    menu.style.top = `${e.clientY}px`;
    menu.hidden = false;
  });
  document.addEventListener("click", (e) => { if (!menu.contains(e.target)) hideMenu(); });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideMenu();
    if (e.key !== "Delete" || !selectedRow || !selectedRow.isConnected) return;
    const t = e.target;
    if (t && t.closest && t.closest("input, textarea, select, [contenteditable]")) return;
    e.preventDefault();
    featureDialogs.remove(selectedRow.dataset.feature);
    select(null);
  });
}

// Session log: what the user does, briefly (buttons, keys outside text fields, the status line)
if (!STATIC) {
  document.addEventListener("click", (e) => {
    const el = e.target.closest && e.target.closest("button, a, summary, .tree-row, .finding-card");
    if (!el) return;
    clientLog("click", { what: el.id || el.dataset.feature || el.dataset.tool || el.dataset.tab || el.className,
                         text: (el.textContent || "").trim().slice(0, 60) });
  }, true);
  window.addEventListener("keydown", (e) => {
    const t = e.target;
    if (t && t.closest && t.closest("input, textarea, [contenteditable]")) return;
    if (e.key.length === 1 || /^(Escape|Delete|Enter|F\d+)$/.test(e.key)) {
      clientLog("key", { key: (e.ctrlKey || e.metaKey ? "Ctrl+" : "") + (e.shiftKey && e.key.length > 1 ? "Shift+" : "") + e.key });
    }
  }, true);
  let lastStatus = "";
  new MutationObserver(() => {
    const t = statusEl.textContent;
    if (t !== lastStatus) {
      lastStatus = t;
      clientLog("status", { text: t });
    }
  }).observe(statusEl, { childList: true, characterData: true, subtree: true });
}
