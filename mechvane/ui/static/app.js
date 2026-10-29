import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { initViewTools } from "./viewtools.js";

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

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 10000);
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
const viewTools = initViewTools({
  scene, camera, renderer, modelGroup, renderScene,
  containerEl: viewportEl.parentElement,
});

function applyThemeColors() {
  // Dark unless the page asks for the light theme (style.css)
  const isDark = document.documentElement.dataset.theme !== "light";
  scene.background = new THREE.Color(isDark ? 0x111418 : 0xf3f5f8);
  renderScene();
}

applyThemeColors();

function renderScene() {
  renderer.render(scene, camera);
}

controls.addEventListener("change", renderScene);

function resizeViewport() {
  const w = viewportEl.clientWidth || 640;
  const h = viewportEl.clientHeight || 480;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
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
    box.getBoundingSphere(sphere);
    modelRadius = Math.max(sphere.radius, 5);

    if (fitCamera || !cameraFitted) {
      const center = sphere.center;
      const halfFov = THREE.MathUtils.degToRad(camera.fov * 0.5);
      const effHalfFov = camera.aspect < 1 ? Math.atan(Math.tan(halfFov) * camera.aspect) : halfFov;
      const dist = (modelRadius / Math.sin(effHalfFov)) * 1.15;
      const dir = new THREE.Vector3(1.25, -1.45, 1.05).normalize();
      camera.position.copy(center).addScaledVector(dir, dist);
      camera.near = Math.max(0.05, modelRadius * 0.01);
      camera.far = Math.max(2000, modelRadius * 40);
      camera.updateProjectionMatrix();
      controls.target.copy(center);
      controls.update();
      cameraFitted = true;
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

  const nameSpan = document.createElement("span");
  nameSpan.className = "tree-name";
  nameSpan.textContent = node.name || "(unbenannt)";
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
    err.textContent = `FEHLER: ${node.error}`;
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

function updateTreeView(treeData) {
  treeContentEl.innerHTML = "";
  if (!treeData) {
    treeContentEl.innerHTML = '<div class="empty-state">No model tree available</div>';
    return;
  }

  if (treeData.kind === "part") {
    const bodies = treeData.bodies || [];
    const features = treeData.features || [];
    if (bodies.length === 0 && features.length === 0) {
      treeContentEl.innerHTML = '<div class="empty-state">No features</div>';
      return;
    }
    if (bodies.length > 0) {
      const bTitle = document.createElement("div");
      bTitle.className = "tree-section-title";
      bTitle.textContent = `Bodies (${bodies.length})`;
      treeContentEl.appendChild(bTitle);

      const bList = document.createElement("ul");
      bList.className = "tree-list";
      bodies.forEach((b) => {
        const li = document.createElement("li");
        li.className = "tree-item tree-name";
        li.textContent = b;
        bList.appendChild(li);
      });
      treeContentEl.appendChild(bList);
    }

    const fTitle = document.createElement("div");
    fTitle.className = "tree-section-title";
    fTitle.textContent = "History";
    treeContentEl.appendChild(fTitle);

    const fList = document.createElement("ul");
    fList.className = "tree-list";
    features.forEach((f) => fList.appendChild(renderFeatureNode(f)));
    treeContentEl.appendChild(fList);
  } else {
    const occs = treeData.occurrences || [];
    const asmFeats = treeData.assembly_features || [];
    if (occs.length === 0 && asmFeats.length === 0) {
      treeContentEl.innerHTML = '<div class="empty-state">No components</div>';
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

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-store" });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

function dataUrl(name) {
  if (STATIC) return `${demoBase}${name}.json`;
  return name === "findings" ? `api/findings?${ruleQuery()}` : `api/${name}`;
}

// Profile and material for the design rules, remembered per document in this browser
const ruleSetupEl = document.getElementById("rule-setup");
const ruleProfileEl = document.getElementById("rule-profile");
const ruleMaterialEl = document.getElementById("rule-material");

function ruleKey() {
  return `mechvane.rules.${docNameEl.textContent}`;
}

function ruleChoice() {
  try {
    return JSON.parse(localStorage.getItem(ruleKey()) || "{}");
  } catch {
    return {};
  }
}

function ruleQuery() {
  const c = ruleChoice();
  return new URLSearchParams({ profile: c.profile || "fdm_0.4", material: c.material || "" }).toString();
}

function fillRuleSetup(data) {
  if (STATIC || !data.profiles) return;
  const fill = (el, entries, value) => {
    el.replaceChildren(...entries.map(([v, label]) => new Option(label, v, false, v === value)));
  };
  fill(ruleProfileEl, Object.entries(data.profiles), data.profile);
  fill(ruleMaterialEl, [["", "Material: from part"], ...data.materials.map((m) => [m, m.replace(/_/g, " ")])],
    data.material_source === "argument" ? data.material : "");
  ruleSetupEl.hidden = false;
}

async function changeRules() {
  try {
    localStorage.setItem(ruleKey(), JSON.stringify({ profile: ruleProfileEl.value, material: ruleMaterialEl.value }));
  } catch {
    // private window: the choice holds until the page reloads
  }
  statusEl.textContent = "Checking…";
  try {
    const data = await fetchJson(`api/findings?${new URLSearchParams({ profile: ruleProfileEl.value, material: ruleMaterialEl.value })}`);
    updateFindingsView(data, true);
    fillRuleSetup(data);
    statusEl.textContent = "Up to date";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
}
ruleProfileEl.addEventListener("change", changeRules);
ruleMaterialEl.addEventListener("change", changeRules);

async function loadAll(initial = false) {
  try {
    statusEl.textContent = "Loading…";
    // the version first: its name keys the remembered profile and material for the findings
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

    updateMeshView(mesh, initial);
    updateTreeView(tree);
    updateFindingsView(findings, !initial);
    fillRuleSetup(findings);
    if (!STATIC) await loadParams();
    statusEl.textContent = STATIC ? "Live demo, precomputed" : "Up to date";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
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
  statusEl.textContent = "Rebuilding…";
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
    await loadAll(fit);
  };
  select.addEventListener("change", () => {
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
  const docs = project.documents || [];
  if (!docs.length) {
    statusEl.textContent = "No .solidcraft files in this folder yet: open Model by hand and click New part";
    return false;
  }
  const select = document.getElementById("demo-select");
  document.querySelector('label[for="demo-select"]').textContent = "Document";
  for (const a of document.querySelectorAll("#demo-bar a")) a.hidden = true;  // "Install to open your own files": live demo only
  for (const d of docs) {
    const opt = document.createElement("option");
    opt.value = d.name;
    opt.textContent = d.name.replace(/\.solidcraft$/, "") + (d.kind === "assembly" ? " (assembly)" : "");
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
    currentVersion = null;
    await loadAll(fit);
  };
  select.addEventListener("change", () => {
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
