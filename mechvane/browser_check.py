"""In-browser design rule checking for parts (Pyodide demo shim).

Provides a lightweight synchronous session and document shim that consumes
pre-fetched SolidCraft command inspection data and runs design_rules.check,
formatting the result like collect_findings in mechvane.ui.server.
"""

import json
from . import METADATA_KEY, LEGACY_METADATA_KEY, design_rules, hole_tables, read_metadata
from .documents import PART


class BrowserSession:
    """Synchronous session shim backed by a pre-fetched dictionary of command results."""

    def __init__(self, data: dict):
        self.data = data

    def cmd(self, command: str, params: dict | None = None, timeout: float | None = None):
        params = params or {}
        if command == "document.inspect":
            return self.data.get("doc_info", {})
        if command == "document.metadata":
            return {"metadata": self.data.get("metadata", {})}
        if command == "model.threads":
            return self.data.get("threads", {"threads": []})
        if command == "timeline.inspect":
            fid = params.get("feature")
            res = self.data.get("timeline_inspect", {}).get(fid)
            if res is None:
                res = self.data.get("timeline_inspect", {}).get(str(fid), {})
            return res
        if command == "model.faces":
            b = params.get("body")
            return self.data.get("body_faces", {}).get(b, {"faces": []})
        if command == "model.edges":
            b = params.get("body")
            return self.data.get("body_edges", {}).get(b, {"edges": []})
        if command == "inspect.measure":
            return self.data.get("measure", {})
        raise ValueError(f"Unknown command in BrowserSession: {command}")

    def tool(self, name: str, args: dict | None = None, timeout: float | None = None):
        if name == "measure":
            return self.data.get("measure", {})
        if name == "execute":
            return self.cmd(args.get("command"), args.get("params"))
        raise ValueError(f"Unknown tool in BrowserSession: {name}")


class BrowserDoc:
    """Minimal document shim for a part."""

    def __init__(self, session: BrowserSession, name: str, kind: str = PART, metadata: dict | None = None):
        self.session = session
        self.name = name
        self.kind = kind
        self._metadata = metadata or {}

    def metadata(self) -> dict:
        if METADATA_KEY in self._metadata or LEGACY_METADATA_KEY in self._metadata:
            return read_metadata(self._metadata)
        return self._metadata


def check_browser(payload: dict | str, doc_name: str = "doc.solidcraft",
                  profile: str | None = None, material: str | None = None) -> dict:
    """Run design rule check on pre-fetched SolidCraft data and return findings in collect_findings format."""
    if profile is not None and not isinstance(profile, (str, dict)):
        profile = None
    if material is not None and not isinstance(material, str):
        material = None

    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload

    session = BrowserSession(data)
    doc = BrowserDoc(session, doc_name, kind=PART, metadata=data.get("metadata", {}))

    dr = design_rules.check(doc, profile=profile, material=material)
    findings = []
    for c in dr.get("checks", []):
        loc = dict(c.get("location") or {})
        face = loc.get("face")
        point = loc.get("point")
        status = c.get("status", "ok")
        item = {
            "source": "design_rules",
            "rule": c.get("rule", "design_rule"),
            "status": status,
            "severity": status,
            "message": c.get("message", ""),
            "location": loc,
            "face": face,
            "faces": [face] if face else [],
            "point": point,
        }
        if loc.get("body"):
            item["body"] = loc["body"]
        for k in ("value", "threshold"):
            if k in c:
                item[k] = c[k]
        findings.append(item)

    # Attach selection metadata for interactive face picking
    body_faces = data.get("body_faces", {})
    all_bodies = [b["name"] for b in data.get("doc_info", {}).get("bodies", []) if isinstance(b, dict) and "name" in b]
    for item in findings:
        loc = item.get("location") or {}
        name = loc.get("assembly_face") or item.get("face")
        if not name:
            continue
        bodies = [item["body"]] if item.get("body") else all_bodies
        for body in bodies:
            bf = body_faces.get(body, {}).get("faces", [])
            f = next((f for f in bf if f.get("name") == name), None)
            if f:
                item["select"] = {
                    "type": "face",
                    "body": body,
                    "index": f["index"],
                    "point": f.get("point") or f.get("centroid"),
                }
                break

    order = {"fail": 0, "warn": 1, "ok": 2}
    findings.sort(key=lambda x: (order.get(x.get("severity", "ok"), 3), 1 if x.get("rule") == "printability" else 0))

    has_fail = any(f["severity"] == "fail" for f in findings) or dr.get("verdict") == "fail"
    has_warn = any(f["severity"] == "warn" for f in findings) or dr.get("verdict") == "warn"
    verdict = "fail" if has_fail else ("warn" if has_warn else "ok")

    return {
        "status": verdict,
        "verdict": verdict,
        "profile": dr.get("profile", profile),
        "material": dr.get("material", material),
        "material_source": dr.get("material_source"),
        "profiles": {k: v["name"] for k, v in design_rules.PROFILES.items()},
        "materials": list(hole_tables.MATERIAL_ENGAGEMENT_DEPTHS),
        "summary": dr.get("summary"),
        "findings": findings,
        "checks": findings,
        "rules": dr.get("rules", {}),
        "joints": [],
    }


def check_browser_json(payload_json: str, doc_name: str = "doc.solidcraft",
                       profile: str | None = None, material: str | None = None) -> str:
    """Convenience entry point for JS/Pyodide that takes and returns JSON strings."""
    if profile is not None and not isinstance(profile, (str, dict)):
        profile = None
    if material is not None and not isinstance(material, str):
        material = None
    return json.dumps(check_browser(payload_json, doc_name=doc_name, profile=profile, material=material))
