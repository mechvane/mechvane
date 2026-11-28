// Mechvane design rule `hole_edge_distance` as a SolidCraft command plugin (U2, #220).
//
// Port of mechvane/design_rules.py `_extract_holes` and `_check_body` rule 1 together with the helpers it uses
// from mechvane/geometry.py (`group_cylindrical_faces`, `classify_hole_groups`, `cylinder_group_*`,
// `edge_touches`). The Python code is the specification: same grouping, classification, distances, messages
// and rounding, so that the findings equal those of `mechvane check`.
//
// Probe without a cut: `classify_hole_groups` resolves ambiguous cylinder groups with probe cuts (a tiny
// sphere cut just outside the cylinder, then a checkpoint restore). A `read` entry may not edit the design;
// it asks `inspect.classify_points` instead whether the same probe point lies in material (`inside`: the cut
// would hit material, a hole) or not (`outside`: a boss). A point the host reports `on` a face, or a failed
// query, takes the geometric fallback, as a failed probe does in Python. SolidCraft 0.50 gives cylinder faces
// no normal, so many groups (e.g. holes drawn in the base sketch of a plain extrude) depend on this.
//
// Second deviation: `model.threads` counts as an edit command in 0.50 and is refused to a read entry, so
// internal threads take no part in the classification (the thread check is kept for when it becomes readable).
//
// Not exercised by the reference parts, ported literally: the counterbore exception, the open round without
// a wall in reach (`inf`). Blind holes and thread matching only feed
// other rules and are left out.

wit_bindgen::generate!({ path: "wit", world: "command-plugin" });

use craft::plugin::commands;
use craft::plugin::types::{FieldFailure, PluginError};
use exports::craft::plugin::entry::Guest;
use serde_json::{Map, Value, json};

struct Plugin;

type V = [f64; 3];

/// The catalog entry that states the rule's threshold, read at build time: the catalog stays the only source.
const CATALOG_ENTRY: &str = include_str!("../../../katalog/eintraege/schrauben/randabstand_bohrung_kante.json");
const RULE: &str = "hole_edge_distance";

fn v(x: &Value) -> Option<V> {
    let a = x.as_array()?;
    Some([a.first()?.as_f64()?, a.get(1)?.as_f64()?, a.get(2)?.as_f64()?])
}
fn dot(a: V, b: V) -> f64 { a[0] * b[0] + a[1] * b[1] + a[2] * b[2] }
fn sub(a: V, b: V) -> V { [a[0] - b[0], a[1] - b[1], a[2] - b[2]] }
fn add(a: V, b: V) -> V { [a[0] + b[0], a[1] + b[1], a[2] + b[2]] }
fn scale(a: V, s: f64) -> V { [a[0] * s, a[1] * s, a[2] * s] }
fn cross(a: V, b: V) -> V { [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]] }
fn norm(a: V) -> f64 { dot(a, a).sqrt() }
fn unit(a: V) -> V { let n = norm(a); if n > 0.0 { scale(a, 1.0 / n) } else { a } }
fn dist_to_line(p: V, origin: V, axis: V) -> f64 {
    let a = unit(axis);
    let d = sub(p, origin);
    norm(sub(d, scale(a, dot(d, a))))
}
fn parallel(a: V, b: V, tol: f64) -> bool { norm(cross(unit(a), unit(b))) < tol }
// Python round() takes ties to even
fn round4(x: f64) -> f64 { (x * 1e4).round_ties_even() / 1e4 }

/// geometry.edge_touches: an edge "<face A>|<face B>" borders a face; face names may contain "|" themselves.
fn edge_touches(edge: &str, face: &str) -> bool {
    edge == face
        || edge.strip_prefix(face).is_some_and(|r| r.starts_with('|'))
        || edge.strip_suffix(face).is_some_and(|r| r.ends_with('|'))
        || edge.split('|').any(|s| s == face)
}

/// geometry.blend_parts is not None: "F4:blend(...)" (since 0.40) or "F4:blend:..." (up to 0.30).
fn is_blend(name: &str) -> bool { (name.contains(":blend(") && name.ends_with(')')) || name.contains(":blend:") }

/// Feature id from a face name "F{id}:...", as `_extract_holes` reads it.
fn feature_id(name: &str) -> Option<i64> {
    let head = name.split(':').next()?;
    let digits = head.strip_prefix('F')?;
    if !digits.is_empty() && digits.chars().all(|c| c.is_ascii_digit()) { digits.parse().ok() } else { None }
}

fn run(cmd: &str, args: Value) -> Result<Value, PluginError> {
    let out = commands::run(cmd, &args.to_string())?;
    serde_json::from_str(&out).map_err(|e| invalid(cmd, e))
}

/// A cylindrical face as model.faces reports it.
#[derive(Clone)]
struct Cyl {
    name: String,
    axis: V,
    origin: V,
    radius: f64,
    area: f64,
    centroid: Option<V>,
    point: Option<V>,
    normal: Option<V>,
}

fn cyl_of(f: &Value) -> Option<Cyl> {
    let c = f.get("cylinder").filter(|c| !c.is_null())?;
    Some(Cyl {
        name: f["name"].as_str().unwrap_or_default().to_string(),
        axis: v(&c["axis"])?,
        origin: v(&c["origin"])?,
        radius: c["radius"].as_f64()?,
        area: f["area"].as_f64().unwrap_or(0.0),
        centroid: v(&f["centroid"]),
        point: v(&f["point"]),
        // Python: grp[0].get("normal") or grp[0].get("plane_normal"); null counts as absent
        normal: v(&f["normal"]).or_else(|| v(&f["plane_normal"])),
    })
}

/// geometry.group_cylindrical_faces
fn group_cylinders(faces: &[Cyl]) -> Vec<Vec<Cyl>> {
    let mut groups = Vec::new();
    let mut used = vec![false; faces.len()];
    for i in 0..faces.len() {
        if used[i] { continue }
        let c1 = &faces[i];
        let mut grp = vec![c1.clone()];
        used[i] = true;
        for j in 0..faces.len() {
            if used[j] { continue }
            let c2 = &faces[j];
            if parallel(c1.axis, c2.axis, 1e-3) && dist_to_line(c1.origin, c2.origin, c2.axis) < 0.05
                && (c1.radius - c2.radius).abs() < 0.05 {
                grp.push(c2.clone());
                used[j] = true;
            }
        }
        groups.push(grp);
    }
    groups
}

fn group_centroid(grp: &[Cyl]) -> Option<V> {
    let area: f64 = grp.iter().map(|f| f.area).sum();
    if area <= 0.0 || grp.iter().any(|f| f.centroid.is_none()) { return None }
    let mut cen = [0.0; 3];
    for f in grp {
        let c = f.centroid.unwrap_or_default();
        for i in 0..3 { cen[i] += f.area * c[i] / area }
    }
    Some(cen)
}

/// geometry.cylinder_group_is_open
fn group_is_open(grp: &[Cyl]) -> bool {
    let c = &grp[0];
    if c.radius <= 0.0 { return false }
    match group_centroid(grp) {
        Some(cen) => dist_to_line(cen, c.origin, unit(c.axis)) > 0.3 * c.radius,
        None => false,
    }
}

/// geometry.cylinder_group_closed_side
fn group_closed_side(grp: &[Cyl]) -> Option<V> {
    if !group_is_open(grp) { return None }
    let c = &grp[0];
    let axis = unit(c.axis);
    let vv = sub(group_centroid(grp)?, c.origin);
    Some(unit(sub(vv, scale(axis, dot(vv, axis)))))
}

/// geometry.cylinder_group_length
fn group_length(grp: &[Cyl]) -> f64 {
    let c = &grp[0];
    let r = c.radius;
    let area: f64 = grp.iter().map(|f| f.area).sum();
    let lone_half = grp.len() == 1
        && grp[0].centroid.is_some_and(|cen| dist_to_line(cen, c.origin, unit(c.axis)) > 0.3 * r);
    if lone_half { area / (std::f64::consts::PI * r) } else { area / (2.0 * std::f64::consts::PI * r) }
}

fn group_feature(grp: &[Cyl]) -> Option<i64> { grp.iter().find_map(|f| feature_id(&f.name)) }

/// geometry.classify_hole_groups with keep_open=True and probe=False (see the header comment).
fn classify(body: &str, groups: &[Vec<Cyl>], timeline: &Map<String, Value>, threads: &[Value], bmin: V, bmax: V)
             -> Vec<bool> {
    let mut is_hole = vec![false; groups.len()];
    let mut ambiguous = Vec::new();
    for (idx, grp) in groups.iter().enumerate() {
        let feat = group_feature(grp).and_then(|id| timeline.get(&id.to_string())).cloned().unwrap_or(Value::Null);
        let ftype = feat["type"].as_str().unwrap_or("");
        if matches!(ftype, "FilletFeature" | "ChamferFeature") || grp.iter().any(|f| is_blend(&f.name)) {
            continue;
        }
        let op = feat["definition"]["operation"].as_str().or_else(|| feat["operation"].as_str()).unwrap_or("");
        if ftype == "HoleFeature" { is_hole[idx] = true; continue }
        // keep_open: an open round is classified like any other group
        if op == "cut" { is_hole[idx] = true; continue }
        if grp.iter().any(|f| f.name.contains(":bore:") || f.name.contains(":cut:")) { is_hole[idx] = true; continue }
        if grp.iter().any(|f| f.name.to_lowercase().contains("hole")) { is_hole[idx] = true; continue }
        let (p0, axis) = (grp[0].origin, unit(grp[0].axis));
        let internal_thread = threads.iter().any(|th| {
            th["internal"].as_bool().unwrap_or(false)
                && v(&th["axis_point"]).is_some_and(|ap| dist_to_line(ap, p0, axis) < 0.05)
        });
        if internal_thread { is_hole[idx] = true; continue }
        if let (Some(n), Some(pt)) = (grp[0].normal, grp[0].point.or(grp[0].centroid)) {
            let p_axis = add(p0, scale(axis, dot(sub(pt, p0), axis)));
            let s = dot(n, sub(pt, p_axis));
            if s < -1e-4 { is_hole[idx] = true; continue }
            if s > 1e-4 { continue }
        }
        ambiguous.push((idx, op.to_string()));
    }
    // Probe: the point just outside the cylinder wall, in material or not (Python's probe sphere centre)
    let mut probes: Vec<(usize, V)> = Vec::new();
    for (idx, _) in &ambiguous {
        let c = &groups[*idx][0];
        let Some(pt) = c.point else { continue };
        let (axis, p0) = (unit(c.axis), c.origin);
        let rad = sub(pt, add(p0, scale(axis, dot(sub(pt, p0), axis))));
        let d_rad = norm(rad);
        if d_rad < 1e-4 { continue }
        let delta = (0.05 * c.radius).min(0.1);
        probes.push((*idx, add(pt, scale(rad, delta / d_rad))));
    }
    let mut handled = vec![false; groups.len()];
    for chunk in probes.chunks(256) {
        let pts: Vec<V> = chunk.iter().map(|(_, p)| *p).collect();
        let Ok(res) = run("inspect.classify_points", json!({"body": body, "points": pts})) else { continue };
        let results = res["results"].as_array().cloned().unwrap_or_default();
        for ((idx, _), r) in chunk.iter().zip(&results) {
            match r["class"].as_str() {
                Some("inside") => { is_hole[*idx] = true; handled[*idx] = true }
                Some("outside") => { is_hole[*idx] = false; handled[*idx] = true }
                _ => {}
            }
        }
    }
    // Geometric fallback (Python: groups the probe did not handle)
    for (idx, op) in ambiguous {
        if handled[idx] { continue }
        let c = &groups[idx][0];
        let (r, axis, p0) = (c.radius, unit(c.axis), c.origin);
        let (mut larger, mut smaller) = (false, false);
        for (other_idx, other) in groups.iter().enumerate() {
            if other_idx == idx { continue }
            let oc = &other[0];
            if parallel(axis, oc.axis, 1e-3) && dist_to_line(p0, oc.origin, oc.axis) < 0.05 {
                if oc.radius > r + 1e-3 { larger = true } else if oc.radius < r - 1e-3 { smaller = true }
            }
        }
        is_hole[idx] = if larger {
            true
        } else if smaller || matches!(op.as_str(), "join" | "new_body" | "new") {
            false
        } else {
            // Python checks x and y only, whatever the axis is
            bmin[0] + r < p0[0] && p0[0] < bmax[0] - r && bmin[1] + r < p0[1] && p0[1] < bmax[1] - r
        };
    }
    is_hole
}

struct Round {
    faces: Vec<String>,
    point: Value,
    radius: f64,
    axis: V,
    origin: V,
    center: V,
    length: f64,
    closed_side: Option<V>,
}

/// Axial range along `axis` of the edges bordering `faces`, else centre ± length/2.
fn axial_range(edges: &[Value], faces: &[String], axis: V, center: V, length: f64) -> (f64, f64) {
    let mut lo = f64::INFINITY;
    let mut hi = f64::NEG_INFINITY;
    for e in edges {
        let en = e["name"].as_str().unwrap_or("");
        if !faces.iter().any(|f| edge_touches(en, f)) { continue }
        for p in [v(&e["start"]), v(&e["end"])].into_iter().flatten() {
            let t = dot(p, axis);
            lo = lo.min(t);
            hi = hi.max(t);
        }
    }
    if lo.is_finite() { (lo, hi) } else { let c = dot(center, axis); (c - length / 2.0, c + length / 2.0) }
}

fn edge_points(edges: &[Value], face: &str) -> Vec<V> {
    edges.iter().filter(|e| edge_touches(e["name"].as_str().unwrap_or(""), face))
        .flat_map(|e| [v(&e["start"]), v(&e["end"])]).flatten().collect()
}

fn check_body(body: &Value, timeline: &Map<String, Value>, threads: &[Value], factor: f64, source: &Value,
              debug: &mut Vec<Value>) -> Result<Vec<Value>, PluginError> {
    let name = body["name"].as_str().unwrap_or_default();
    let faces = run("model.faces", json!({"body": name}))?["faces"].as_array().cloned().unwrap_or_default();
    let edges = run("model.edges", json!({"body": name})).ok()
        .and_then(|e| e["edges"].as_array().cloned()).unwrap_or_default();
    let (bmin, bmax) = (v(&body["bbox"]["min"]).unwrap_or_default(), v(&body["bbox"]["max"]).unwrap_or_default());

    // _extract_holes: group per feature (in order of first appearance), then classify all groups together
    let mut per_feature: Vec<(Option<i64>, Vec<Cyl>)> = Vec::new();
    for c in faces.iter().filter_map(cyl_of) {
        let fid = feature_id(&c.name);
        match per_feature.iter_mut().find(|(k, _)| *k == fid) {
            Some((_, list)) => list.push(c),
            None => per_feature.push((fid, vec![c])),
        }
    }
    let groups: Vec<Vec<Cyl>> = per_feature.iter().flat_map(|(_, l)| group_cylinders(l)).collect();
    let is_hole = classify(name, &groups, timeline, threads, bmin, bmax);

    let mut holes = Vec::new();
    let mut open_rounds = Vec::new();
    let mut ext = Vec::new();
    for (grp, &hole) in groups.iter().zip(&is_hole) {
        let c = &grp[0];
        let axis = unit(c.axis);
        let total_area: f64 = grp.iter().map(|f| f.area).sum();
        if total_area <= 0.0 || c.radius <= 0.0 { continue } // degenerate face: Python would divide by zero
        let weighted_t = grp.iter().map(|f| f.area * dot(sub(f.centroid.unwrap_or(c.origin), c.origin), axis))
            .sum::<f64>() / total_area;
        let center = add(c.origin, scale(axis, weighted_t));
        let rep = |p: Option<V>| p.map(|p| json!(p)).unwrap_or(json!(center));
        let closed_side = if hole { group_closed_side(grp) } else { None };
        let round = Round {
            faces: grp.iter().map(|f| f.name.clone()).collect(),
            point: if hole { rep(c.point) } else { rep(c.point.or(c.centroid)) },
            radius: c.radius,
            axis,
            origin: c.origin,
            center,
            length: group_length(grp),
            closed_side,
        };
        debug.push(json!({"faces": round.faces, "hole": hole, "closed_side": closed_side, "center": center}));
        if !hole { ext.push(round) } else if closed_side.is_some() { open_rounds.push(round) } else { holes.push(round) }
    }

    let side_faces: Vec<&Value> = faces.iter().filter(|f| v(&f["plane_normal"]).is_some()).collect();
    let mut out = Vec::new();
    for h in holes.iter().chain(&open_rounds) {
        let (c, r, axis) = (h.center, h.radius, h.axis);
        let d = 2.0 * r;
        let closed = h.closed_side;
        let towards_wall = |dir: V| closed.is_none_or(|cs| dot(dir, cs) > 0.1);
        let (th_min, th_max) = axial_range(&edges, &h.faces, axis, c, h.length);

        let mut dist_faces: Vec<(f64, String)> = Vec::new();
        for sf in &side_faces {
            let Some(n) = v(&sf["plane_normal"]) else { continue };
            if dot(n, axis).abs() >= 0.1 { continue }
            let Some(p) = v(&sf["point"]) else { continue };
            let signed = dot(sub(p, c), n);
            // the face must look away from the hole, not into it as an inner step or pocket does
            if signed < -1e-4 || !towards_wall(n) { continue }
            let sname = sf["name"].as_str().unwrap_or_default();
            let sp = edge_points(&edges, sname);
            if !sp.is_empty() {
                let ts_min = sp.iter().map(|p| dot(*p, axis)).fold(f64::INFINITY, f64::min);
                let ts_max = sp.iter().map(|p| dot(*p, axis)).fold(f64::NEG_INFINITY, f64::max);
                if ts_max.min(th_max) - ts_min.max(th_min) < 1e-3 { continue } // no overlap along the axis
                let u = unit(cross(axis, n));
                let uh = dot(c, u);
                let us_min = sp.iter().map(|p| dot(*p, u)).fold(f64::INFINITY, f64::min);
                let us_max = sp.iter().map(|p| dot(*p, u)).fold(f64::NEG_INFINITY, f64::max);
                if uh < us_min - r - 1e-4 || uh > us_max + r + 1e-4 { continue } // does not cover the hole
            }
            dist_faces.push((signed.abs(), sname.to_string()));
        }

        // non-coaxial external cylinder walls (bosses, fillet and shell rounds)
        for ec in &ext {
            if !parallel(axis, ec.axis, 1e-3) { continue }
            let d_axes = dist_to_line(c, ec.origin, ec.axis);
            if d_axes < 0.05 { continue } // coaxial: a wall thickness matter, not an edge distance
            let to = sub(ec.center, c);
            if !towards_wall(unit(sub(to, scale(axis, dot(to, axis))))) { continue }
            let (te_min, te_max) = axial_range(&edges, &ec.faces, axis, ec.center, ec.length);
            if te_max.min(th_max) - te_min.max(th_min) < 1e-3 { continue }
            let dist = if d_axes + r <= ec.radius + 1e-4 { ec.radius - d_axes } else { d_axes - ec.radius };
            dist_faces.push((dist, ec.faces[0].clone()));
        }

        // bounding box, only across the axis
        let mut d_box = f64::INFINITY;
        for i in 0..3 {
            if axis[i].abs() >= 0.5 { continue }
            let mut e = [0.0; 3];
            e[i] = 1.0;
            let mut sides = f64::INFINITY;
            if towards_wall(scale(e, -1.0)) { sides = sides.min((c[i] - bmin[i]).abs()) }
            if towards_wall(e) { sides = sides.min((c[i] - bmax[i]).abs()) }
            d_box = d_box.min(sides);
        }

        // Python's min() keeps the first of equal distances
        let (min_dist, nearest) = match dist_faces.iter().fold(None::<&(f64, String)>, |best, x| match best {
            Some(b) if b.0 <= x.0 => Some(b),
            _ => Some(x),
        }) {
            Some((dist, f)) => (dist.min(d_box), f.clone()),
            None => (d_box, "bbox".to_string()),
        };
        if min_dist.is_infinite() { continue } // an open round with no wall in reach on its closed side
        if h.faces.iter().any(|f| f.contains(":cbore:")) { continue } // head recess: its bore counts
        let req = factor * d;
        let what = if closed.is_some() { "Slot end" } else { "Hole" };
        let fail = min_dist < req - 1e-4;
        let message = if fail {
            format!("{what} edge distance {min_dist:.2} mm < {req:.2} mm ({factor:.1} × d for Ø {d:.1} mm) to face {nearest}")
        } else {
            format!("{what} edge distance {min_dist:.2} mm >= {req:.2} mm ({factor:.1} × d for Ø {d:.1} mm)")
        };
        let mut finding = json!({
            "status": if fail { "fail" } else { "ok" },
            "location": {"point": h.point, "face": h.faces[0]},
            "message": message,
            "value": round4(min_dist),
            "threshold": round4(req),
            "rule": RULE,
        });
        if !source.is_null() { finding["source"] = source.clone() }
        out.push(finding);
    }
    Ok(out)
}

/// The rule's source as design_rules.rule_sources() gives it: the first source of the catalog entry.
fn rule_source() -> Value {
    let Ok(e) = serde_json::from_str::<Value>(CATALOG_ENTRY) else { return Value::Null };
    let q = &e["quellen"][0];
    if q.is_null() { return Value::Null }
    json!({"entry": e["id"], "titel": e["aussage"], "url": q["url"], "stelle": q["stelle"], "zitat": q["zitat"]})
}

fn check(factor: f64, want_debug: bool) -> Result<Value, PluginError> {
    let doc = run("document.inspect", json!({"measure": true}))?;
    // model.threads is not marked read-only in SolidCraft 0.50 (no `.read_only()` in cmd/inspect.rs), so a read
    // entry is refused it: internal threads cannot help classify a group here (see the header comment).
    let threads: Vec<Value> = Vec::new();
    // feature id -> timeline entry, with its definition for the feature types whose operation matters
    let mut timeline = Map::new();
    for f in doc["timeline"].as_array().cloned().unwrap_or_default() {
        let Some(id) = f["id"].as_i64() else { continue };
        let mut f = f;
        let ftype = f["type"].as_str().unwrap_or("");
        if matches!(ftype, "HoleFeature" | "CylinderFeature" | "ExtrudeFeature") && f["definition"].as_object().is_none_or(|d| d.is_empty()) {
            if let Ok(insp) = run("timeline.inspect", json!({"feature": id})) {
                f["definition"] = insp["definition"].clone();
            }
        }
        timeline.insert(id.to_string(), f);
    }
    let source = rule_source();
    let mut findings = Vec::new();
    let mut debug = Vec::new();
    for body in doc["bodies"].as_array().cloned().unwrap_or_default() {
        findings.extend(check_body(&body, &timeline, &threads, factor, &source, &mut debug)?);
    }
    let status = if findings.iter().any(|f| f["status"] == "fail") { "fail" } else { "ok" };
    let mut out = json!({RULE: {"status": status, "findings": findings}});
    if want_debug { out["debug"] = json!(debug) }
    Ok(out)
}

impl Guest for Plugin {
    fn execute(entry: String, params: String) -> Result<String, PluginError> {
        let params: Value = serde_json::from_str(&params).map_err(|e| invalid("params", e))?;
        match entry.as_str() {
            "hole-edge-distance" => {
                let factor = params["factor"].as_f64().unwrap_or(1.5);
                Ok(check(factor, params["debug"].as_bool().unwrap_or(false))?.to_string())
            }
            _ => Err(invalid("entry", format!("no entry `{entry}`"))),
        }
    }
}

fn invalid(field: &str, reason: impl ToString) -> PluginError {
    PluginError::InvalidInput(FieldFailure { field: field.into(), reason: reason.to_string() })
}

export!(Plugin);
