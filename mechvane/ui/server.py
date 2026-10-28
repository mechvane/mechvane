"""Local HTTP server (127.0.0.1) and data collection functions for the Mechvane Web-UI."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from urllib.parse import unquote, urlparse
import zipfile

from .. import design_rules, links, query, tree
from . import webapp
from .. import METADATA_KEY, read_metadata
from ..documents import ASSEMBLY, PART, Workspace, _validate_name
from ..solidcraft import Session
from .mesh import collect_mesh

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_UPLOAD = 64 * 1024 * 1024

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


def _add_selections(doc, findings):
    """Give each finding with a face a `select` item for the SolidCraft app's `select.set`
    ({type: face, body, index, point}), so clicking it in the "Model" mode selects that face."""
    faces = {}

    def body_faces(body):
        if body not in faces:
            try:
                faces[body] = doc.session.cmd("model.faces", {"body": body}).get("faces", [])
            except Exception:
                faces[body] = []
        return faces[body]

    all_bodies = None
    for item in findings:
        loc = item.get("location") or {}
        name = loc.get("assembly_face") or item.get("face")
        if not name:
            continue
        if item.get("body"):
            bodies = [item["body"]]
        else:
            if all_bodies is None:
                try:
                    all_bodies = [b["world_name"] for b in query._collect_bodies(doc, {})]
                except Exception:
                    all_bodies = []
            bodies = all_bodies
        for body in bodies:
            f = next((f for f in body_faces(body) if f.get("name") == name), None)
            if f:
                item["select"] = {"type": "face", "body": body, "index": f["index"],
                                  "point": f.get("point") or f.get("centroid")}
                break


def _joint_summary(joint_checks) -> str:
    bad = sorted({j["joint"] for j in joint_checks if j.get("status") != "ok"})
    if not joint_checks:
        return "Assembly: no joints recorded by Mechvane"
    if bad:
        return f"Joint check: {len(bad)} joint(s) need attention: {', '.join(bad)}"
    return f"Joint check: all {len({j['joint'] for j in joint_checks})} joints ok"


def collect_findings(ws, doc, profile: str = "fdm_0.4") -> dict:
    """Collect design rule findings for a part, joint link findings for an assembly.

    Design rules are part rules (like check_design): on an assembly they would treat screws and
    plates as one printed body."""
    dr = design_rules.check(doc.session, profile=profile) if doc.kind == PART else {}
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

    _add_selections(doc, findings)
    order = {"fail": 0, "warn": 1, "ok": 2}
    findings.sort(key=lambda x: (order.get(x.get("severity", "ok"), 3), 1 if x.get("rule") == "printability" else 0))

    has_fail = any(f["severity"] == "fail" for f in findings)
    has_warn = any(f["severity"] == "warn" for f in findings)
    verdict = "fail" if has_fail else ("warn" if has_warn else "ok")

    return {
        "status": verdict,
        "verdict": verdict,
        "profile": dr.get("profile", profile),
        "summary": dr.get("summary") or _joint_summary(joint_checks),
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


def detect_kind(p: Path, ws: Workspace | None = None) -> str:
    try:
        with zipfile.ZipFile(p) as zf:
            d = json.loads(zf.read("document.json"))
        meta_kind = read_metadata(d.get("metadata")).get("kind")
        if meta_kind in (PART, ASSEMBLY):
            return meta_kind
        return ASSEMBLY if d.get("links") else PART
    except Exception:
        if ws is not None:
            try:
                r = ws.reader(p)
                try:
                    kind = read_metadata(r.cmd("document.metadata").get("metadata")).get("kind")
                    if kind in (PART, ASSEMBLY):
                        return kind
                    return ASSEMBLY if r.cmd("component.links").get("links") else PART
                finally:
                    r.close()
            except Exception:
                pass
        return PART


class UIServer(ThreadingHTTPServer):
    """ThreadingHTTPServer holding a locked Workspace and open Document."""

    # On Windows SO_REUSEADDR lets a second server bind the same port silently
    allow_reuse_address = sys.platform != "win32"
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, path):
        self.lock = threading.Lock()
        self.path = Path(path).resolve()
        if not self.path.exists():
            raise FileNotFoundError(f"path not found: {self.path}")
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="ui1-", dir="/tmp"))
        self._kind_cache = {}

        if self.path.is_dir():
            self.is_folder = True
            self.folder_path = self.path
            self.file_path = None
            self.doc = None
            self.doc_name = None
            self.mtime = None
            ws_root = self.folder_path
            self.ws = Workspace(ws_root)
            self.ws.session = lambda: Session(allow_paths=[self.ws.root, self.tmp_dir])
            try:
                super().__init__(server_address, RequestHandlerClass)
            except Exception:
                self.ws.close_all()
                shutil.rmtree(self.tmp_dir, ignore_errors=True)
                raise
        elif self.path.is_file():
            self.is_folder = False
            self.file_path = self.path
            self.folder_path = self.file_path.parent
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
        else:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
            raise FileNotFoundError(f"not a file or directory: {self.path}")

    def _get_kind(self, p: Path) -> str:
        mtime = p.stat().st_mtime
        key = (p.name, mtime)
        cached = self._kind_cache.get(key)
        if cached is not None:
            return cached
        k = detect_kind(p, self.ws)
        self._kind_cache[key] = k
        return k

    def ensure_current(self):
        if self.file_path is None:
            return None
        cur = self.file_path.stat().st_mtime
        if cur != self.mtime:
            if self.doc_name in self.ws.docs:
                self.ws.close(self.doc_name)
            self.doc = self.ws.open(self.file_path)
            self.doc_name = self.doc.name
            self.mtime = cur
        return self.doc

    def files(self) -> dict:
        """Files the "Model" mode may load and save, by name: the open document and, for an
        assembly, its linked part files."""
        if self.file_path is None:
            return {}
        out = {self.file_path.name: self.file_path}
        doc = self.ensure_current()
        if doc and doc.kind == ASSEMBLY:
            for link in links._links(doc.session).values():
                p = Path(link.get("file") or "")
                if not p.is_absolute() and self.folder_path:
                    p = self.folder_path / p
                if p.is_file():
                    out.setdefault(p.name, p.resolve())
        return out

    def save(self, name: str, data: bytes) -> dict:
        """Write a file saved in the web app, reload the document and check it again."""
        if self.file_path is None:
            raise KeyError(name)
        target = self.files().get(name)
        if target is None:
            raise KeyError(name)
        tmp = target.with_name(f".{target.name}.upload")
        tmp.write_bytes(data)
        os.replace(tmp, target)
        if target != self.file_path:
            # A linked part changed: reopen the assembly so update_links reads it again.
            self.mtime = None
        doc = self.ensure_current()
        out = {"saved": name, "bytes": len(data), "findings": collect_findings(self.ws, doc)}
        if doc.kind == ASSEMBLY:
            out["update_links"] = links.update_links(self.ws, doc)
        return out

    def list_documents(self) -> list[dict]:
        if not self.is_folder:
            kind = self.doc.kind if self.doc else self._get_kind(self.file_path)
            return [{"name": self.file_path.name, "kind": kind}]
        docs = []
        for p in sorted(self.folder_path.iterdir(), key=lambda x: x.name):
            if p.is_file() and p.name.endswith(".solidcraft") and not p.name.startswith("."):
                docs.append({"name": p.name, "kind": self._get_kind(p)})
        return docs

    def project(self) -> dict:
        return {
            "folder": self.folder_path.name,
            "current": self.file_path.name if self.file_path else None,
            "documents": self.list_documents(),
            "mode": "folder" if self.is_folder else "file",
        }

    def open_document(self, name: str) -> dict:
        valid_docs = {d["name"] for d in self.list_documents()}
        if name not in valid_docs:
            raise KeyError(name)
        target = (self.folder_path / name if self.is_folder else self.file_path).resolve()
        if not target.is_file():
            raise KeyError(name)
        if self.doc_name and self.doc_name in self.ws.docs:
            self.ws.close(self.doc_name)
        self.file_path = target
        self.doc = self.ws.open(target)
        self.doc_name = self.doc.name
        self.mtime = target.stat().st_mtime
        return {"document": self.file_path.name, "files": sorted(self.files())}

    def new_document(self, name: str) -> dict:
        if not self.is_folder:
            raise NotADirectoryError("new document only supported in folder mode")
        _validate_name(name)
        stem = name[:-11] if name.endswith(".solidcraft") else name
        _validate_name(stem)
        target = self.folder_path / f"{stem}.solidcraft"
        if target.exists():
            raise FileExistsError(f"document {target.name!r} already exists")
        doc = self.ws.new(PART, stem)
        if self.doc_name and self.doc_name in self.ws.docs:
            self.ws.close(self.doc_name)
        self.file_path = target
        self.doc = doc
        self.doc_name = doc.name
        self.mtime = target.stat().st_mtime
        return {"document": self.file_path.name, "files": sorted(self.files())}

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

    def _send_static(self, filename: str, content_type: str | None = None):
        root = STATIC_DIR.resolve()
        target = (root / unquote(filename)).resolve()
        if (root not in target.parents and target != root) or not target.is_file():
            self._send_json(404, {"error": f"file not found: {filename}"})
            return
        if content_type is None:
            content_type = "text/plain; charset=utf-8" if target.name == "LICENSE" else webapp.mime(target)
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str, cache: str = "no-store"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def _send_webapp(self, rel: str):
        target = webapp.resolve(rel)
        if target is None:
            self._send_json(404, {"error": f"not in the SolidCraft web build: {rel}"})
            return
        self._send_bytes(target.read_bytes(), webapp.mime(target), cache="no-cache")

    def do_POST(self):
        path = urlparse(self.path).path
        srv: UIServer = self.server  # type: ignore[assignment]
        try:
            if path.startswith("/api/open/"):
                name = unquote(path[len("/api/open/"):])
                if not name:
                    self._send_json(404, {"error": "document name required"})
                    return
                with srv.lock:
                    try:
                        result = srv.open_document(name)
                    except KeyError:
                        self._send_json(404, {"error": f"document not found: {name}"})
                        return
                self._send_json(200, result)
                return

            if path == "/api/new":
                if not srv.is_folder:
                    self._send_json(404, {"error": "new document only supported in folder mode"})
                    return
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0 or length > 65536:
                    self._send_json(400, {"error": "invalid content length"})
                    return
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    self._send_json(400, {"error": "invalid JSON body"})
                    return
                name = body.get("name") if isinstance(body, dict) else None
                if not name or not isinstance(name, str) or not name.strip():
                    self._send_json(400, {"error": "document name cannot be empty"})
                    return
                with srv.lock:
                    try:
                        result = srv.new_document(name.strip())
                    except ValueError as e:
                        self._send_json(400, {"error": str(e)})
                        return
                    except FileExistsError as e:
                        self._send_json(409, {"error": str(e)})
                        return
                self._send_json(200, result)
                return

            if path.startswith("/api/file/"):
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0 or length > MAX_UPLOAD:
                    self._send_json(413, {"error": f"expected 1 to {MAX_UPLOAD} bytes"})
                    return
                data = self.rfile.read(length)
                with srv.lock:
                    try:
                        result = srv.save(unquote(path[len("/api/file/"):]), data)
                    except KeyError:
                        self._send_json(404, {"error": "not a file of this document"})
                        return
                self._send_json(200, result)
                return

            self._send_json(404, {"error": f"unknown endpoint: {path}"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

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
            if path in ("/model", "/model.html"):
                self._send_static("model.html", "text/html; charset=utf-8")
                return
            if path in ("/favicon.ico", "/logo.svg"):
                self._send_static(path.lstrip("/"))
                return
            if path.startswith("/vendor/"):
                self._send_static(path.lstrip("/"))
                return
            if path.startswith("/static/"):
                self._send_static(path[len("/static/"):])
                return
            if path.startswith("/sc/"):
                self._send_webapp(path[len("/sc/"):])
                return
            if path == "/api/project":
                with srv.lock:
                    data = srv.project()
                self._send_json(200, data)
                return
            if path == "/api/files":
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    names = sorted(srv.files())
                    doc_name = srv.file_path.name
                self._send_json(200, {"document": doc_name, "files": names})
                return
            if path.startswith("/api/file/"):
                with srv.lock:
                    if srv.file_path is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    target = srv.files().get(unquote(path[len("/api/file/"):]))
                if target is None:
                    self._send_json(404, {"error": "not a file of this document"})
                    return
                self._send_bytes(target.read_bytes(), "application/octet-stream")
                return

            if path == "/api/version":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_version(doc)
                self._send_json(200, data)
                return

            if path == "/api/mesh":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_mesh(doc, tmp_dir=srv.tmp_dir)
                self._send_json(200, data)
                return

            if path == "/api/tree":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_tree(srv.ws, doc)
                self._send_json(200, data)
                return

            if path == "/api/findings":
                with srv.lock:
                    doc = srv.ensure_current()
                    if doc is None:
                        self._send_json(409, {"error": "no document open"})
                        return
                    data = collect_findings(srv.ws, doc)
                self._send_json(200, data)
                return

            self._send_json(404, {"error": f"unknown endpoint: {path}"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def create_server(path, port: int = 8765, host: str = "127.0.0.1") -> UIServer:
    """Create a UIServer bound to host:port for the given .solidcraft file or project folder."""
    return UIServer((host, port), UIRequestHandler, path)


def run_server(path, port: int = 8765):
    """Run the UI server on 127.0.0.1:<port> until interrupted."""
    srv = create_server(path, port=port, host="127.0.0.1")
    actual_port = srv.server_address[1]
    target_name = srv.folder_path.name if srv.is_folder else srv.file_path.name
    print(f"Mechvane UI running at http://127.0.0.1:{actual_port}/ ({target_name})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
