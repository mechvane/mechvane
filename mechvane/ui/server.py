"""Local HTTP server (127.0.0.1) and data collection functions for the Mechvane Web-UI."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from urllib.parse import urlparse

from .. import design_rules, links, query, tree
from ..documents import ASSEMBLY, PART, Workspace
from ..solidcraft import Session
from .mesh import collect_mesh

STATIC_DIR = Path(__file__).resolve().parent / "static"

_JOINT_PRIO = ("joint_missing", "file_missing", "face_missing", "origin_lost", "moved", "unverifiable", "ok")


def _joint_severity(status: str) -> str:
    if status == "ok":
        return "ok"
    if status in ("moved", "unverifiable"):
        return "warn"
    return "fail"


def _pick_joint_status(entries: list[dict]) -> str:
    if not entries:
        return "ok"
    statuses = {e.get("status", "ok") for e in entries}
    for p in _JOINT_PRIO:
        if p in statuses:
            return p
    return next(iter(statuses))


def collect_version(doc) -> dict:
    """Return file mtime and basic document info."""
    mtime = doc.path.stat().st_mtime
    return {
        "version": mtime,
        "mtime": mtime,
        "name": doc.name,
        "kind": doc.kind,
        "path": str(doc.path),
    }


def collect_tree(ws, doc) -> dict:
    """Return the model browser tree; for assemblies, enrich joints with status from links.check."""
    if doc.kind == PART:
        return tree.part_tree(doc.session, groups=True)

    t = tree.assembly_tree(doc.session, groups=True)
    checks = links.check(ws, doc)
    by_joint = {}
    for c in checks:
        by_joint.setdefault(c["joint"], []).append(c)

    status_map = {jname: _pick_joint_status(entries) for jname, entries in by_joint.items()}

    def _enrich_occ(occ):
        for j in occ.get("joints", []):
            j["status"] = status_map.get(j["name"], "ok")
            j["severity"] = _joint_severity(j["status"])
        for ch in occ.get("occurrences", []):
            _enrich_occ(ch)

    for occ in t.get("occurrences", []):
        _enrich_occ(occ)

    rels = t.get("groups", {}).get("relations", [])
    for r in rels:
        r["status"] = status_map.get(r["name"], "ok")
        r["severity"] = _joint_severity(r["status"])

    t["joints"] = [
        {
            "name": r["name"],
            "type": r["type"],
            "between": r["between"],
            "status": r["status"],
            "severity": r["severity"],
        }
        for r in rels
    ]
    t["joint_checks"] = checks
    return t


def _match_assembly_face(doc, occ_name: str, origin, z) -> tuple[str | None, str | None]:
    if not occ_name or origin is None or z is None:
        return None, None
    try:
        targets = query._collect_bodies(doc, {"occurrence": occ_name})
        for bt in targets:
            wname = bt["world_name"]
            faces = doc.session.cmd("model.faces", {"body": wname}).get("faces", [])
            for f in faces:
                f.setdefault("body", wname)
            m = links._match(faces, origin, z)
            if m and m.get("face"):
                return wname, m["face"]
    except Exception:
        pass
    return None, None


def collect_findings(ws, doc, profile: str = "fdm_0.4") -> dict:
    """Collect design rule findings (and joint link findings for assemblies)."""
    dr = design_rules.check(doc.session, profile=profile)
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

    joint_checks = []
    if doc.kind == ASSEMBLY:
        joint_checks = links.check(ws, doc)
        frames = links._frames(doc.session)
        for jc in joint_checks:
            jname = jc["joint"]
            side = jc["side"]
            occ = jc.get("occurrence")
            face = jc.get("face")
            st = jc.get("status", "ok")
            sev = _joint_severity(st)
            _, origin, z = frames.get(jname, {}).get(side, (None, None, None))
            asm_body, asm_face = _match_assembly_face(doc, occ, origin, z)
            face_list = [f for f in (face, asm_face) if f]
            if st == "ok":
                msg = f"Joint {jname} (side {side} on {occ}): ok ({face or 'verified'})"
            elif st == "moved":
                msg = f"Joint {jname} (side {side} on {occ}): moved from {face} to {jc.get('now_on') or '?'}"
            else:
                msg = f"Joint {jname} (side {side} on {occ}): {st}"
            loc = {"point": origin, "face": face}
            if asm_face:
                loc["assembly_face"] = asm_face
            if asm_body:
                loc["body"] = asm_body
            item = {
                "source": "links",
                "rule": "joint_check",
                "joint": jname,
                "side": side,
                "occurrence": occ,
                "status": st,
                "severity": sev,
                "message": msg,
                "location": loc,
                "face": face or asm_face,
                "faces": face_list,
                "point": origin,
            }
            if asm_body:
                item["body"] = asm_body
            findings.append(item)

    order = {"fail": 0, "warn": 1, "ok": 2}
    findings.sort(key=lambda x: (order.get(x.get("severity", "ok"), 3), 1 if x.get("rule") == "printability" else 0))

    has_fail = any(f["severity"] == "fail" for f in findings)
    has_warn = any(f["severity"] == "warn" for f in findings)
    verdict = "fail" if has_fail else ("warn" if has_warn else "ok")

    return {
        "status": verdict,
        "verdict": verdict,
        "profile": dr.get("profile", profile),
        "summary": dr.get("summary", ""),
        "findings": findings,
        "checks": findings,
        "rules": dr.get("rules", {}),
        "joints": joint_checks,
    }


def _resolve_workspace_root(file_path: Path) -> Path:
    env_ws = os.environ.get("MECHVANE_WORKSPACE") or os.environ.get("INVENTA_WORKSPACE")
    if env_ws:
        cand = Path(env_ws).resolve()
        try:
            file_path.relative_to(cand)
            return cand
        except ValueError:
            pass
    return file_path.parent


class UIServer(ThreadingHTTPServer):
    """ThreadingHTTPServer holding a locked Workspace and open Document."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, file_path):
        self.lock = threading.Lock()
        self.file_path = Path(file_path).resolve()
        if not self.file_path.is_file():
            raise FileNotFoundError(f"document not found: {self.file_path}")
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="ui1-", dir="/tmp"))
        ws_root = _resolve_workspace_root(self.file_path)
        self.ws = Workspace(ws_root)
        self.ws.session = lambda: Session(allow_paths=[self.ws.root, self.tmp_dir])
        try:
            self.doc = self.ws.open(self.file_path)
            self.doc_name = self.doc.name
            self.mtime = self.file_path.stat().st_mtime
            super().__init__(server_address, RequestHandlerClass)
        except Exception:
            self.ws.close_all()
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
            raise

    def ensure_current(self):
        cur = self.file_path.stat().st_mtime
        if cur != self.mtime:
            if self.doc_name in self.ws.docs:
                self.ws.close(self.doc_name)
            self.doc = self.ws.open(self.file_path)
            self.doc_name = self.doc.name
            self.mtime = cur
        return self.doc

    def server_close(self):
        try:
            super().server_close()
        finally:
            with self.lock:
                self.ws.close_all()
                shutil.rmtree(self.tmp_dir, ignore_errors=True)


class UIRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, filename: str, content_type: str):
        target = STATIC_DIR / filename
        if not target.is_file():
            self._send_json(404, {"error": f"file not found: {filename}"})
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        srv: UIServer = self.server  # type: ignore[assignment]
        try:
            if path in ("/", "/index.html"):
                self._send_static("index.html", "text/html; charset=utf-8")
                return
            if path == "/app.js":
                self._send_static("app.js", "application/javascript; charset=utf-8")
                return
            if path == "/style.css":
                self._send_static("style.css", "text/css; charset=utf-8")
                return

            if path == "/api/version":
                with srv.lock:
                    doc = srv.ensure_current()
                    data = collect_version(doc)
                self._send_json(200, data)
                return

            if path == "/api/mesh":
                with srv.lock:
                    doc = srv.ensure_current()
                    data = collect_mesh(doc, tmp_dir=srv.tmp_dir)
                self._send_json(200, data)
                return

            if path == "/api/tree":
                with srv.lock:
                    doc = srv.ensure_current()
                    data = collect_tree(srv.ws, doc)
                self._send_json(200, data)
                return

            if path == "/api/findings":
                with srv.lock:
                    doc = srv.ensure_current()
                    data = collect_findings(srv.ws, doc)
                self._send_json(200, data)
                return

            self._send_json(404, {"error": f"unknown endpoint: {path}"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def create_server(file_path, port: int = 8765, host: str = "127.0.0.1") -> UIServer:
    """Create a UIServer bound to host:port for the given .solidcraft file."""
    return UIServer((host, port), UIRequestHandler, file_path)


def run_server(file_path, port: int = 8765):
    """Run the UI server on 127.0.0.1:<port> until interrupted."""
    srv = create_server(file_path, port=port, host="127.0.0.1")
    actual_port = srv.server_address[1]
    print(f"Mechvane UI running at http://127.0.0.1:{actual_port}/ ({srv.file_path.name})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
