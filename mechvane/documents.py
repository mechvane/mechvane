"""Part and assembly documents, each a .solidcraft file in its own SolidCraft session."""

import warnings
import weakref
from pathlib import Path

from . import METADATA_KEY, files_on_disk, files_relative, read_metadata
from .solidcraft import Session, SolidCraftError

PART, ASSEMBLY = "part", "assembly"

# designs open in a SolidCraft window (connect_window): a file Mechvane writes may be open there too (#191)
_WINDOWS = weakref.WeakSet()


def _window_states(path):
    """(window, its active tab's (path, dirty, document_id) or None) for every window that may show `path`."""
    target = Path(path).resolve()
    out = []
    for w in list(_WINDOWS):
        st = w.state()
        if st is None:
            if w.pinned_path == target:
                out.append((w, None))
            continue
        if st[0] is not None and w.document_id is not None and st[2] == w.document_id:
            w.pinned_path = st[0]  # the connected tab in front: follow a "save as" in the app (#190)
        if target in (st[0], w.pinned_path):
            out.append((w, st))
    return out


def check_windows_writable(path):
    """Raise when Mechvane must not write `path` because a connected window shows it with unsaved work, or the
    window cannot be asked; return the windows to reload afterwards (#191)."""
    name = Path(path).name
    reload = []
    for w, st in _window_states(path):
        if st is None:
            raise ValueError(f"{name} is open in the SolidCraft window {w.name!r}, which does not answer: "
                             "close_document it (or the app), then try again")
        if w.document_id is not None and st[2] != w.document_id:
            raise ValueError(f"{name} is open in the SolidCraft window, but another tab is in front of the one "
                             f"{w.name!r} is connected to: show that tab again, then try again")
        if st[1]:
            raise ValueError(f"{name} is open in the SolidCraft window with unsaved changes ({w.name!r}): save or "
                             "discard them in the app first, then try again (otherwise one of the two versions "
                             "would be lost)")
        reload.append(w)
    return reload


def windows_showing(path):
    """The connected windows whose design is the file `path`."""
    target = Path(path).resolve()
    return [w for w, st in _window_states(path) if st is not None and st[0] == target]


def reload_windows(path):
    """After Mechvane wrote `path`: show the new file in every window that has it open and in front, so a later
    save in the app does not write the old state back. Unsaved work in the app is never thrown away: such a
    window is left as it is, with a warning. Returns the names of the reloaded window documents."""
    out = []
    for w, st in _window_states(path):
        if st is None or st[0] != Path(path).resolve() or (w.document_id is not None and st[2] != w.document_id):
            continue
        if st[1]:
            warnings.warn(f"{Path(path).name} changed on disk, but the SolidCraft window {w.name!r} has unsaved "
                          "changes and still shows the old state: do not save it there over the file")
            continue
        if w.reload():
            out.append(w.name)
    return out


def _validate_name(name: str):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("document name cannot be empty")
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"document name {name!r} cannot contain path separators or '..'")


class Document:
    def __init__(self, name, kind, path, session):
        self.name, self.kind, self.path, self.session = name, kind, Path(path), session
        self.mtime = self.disk_mtime()  # file state this session was loaded from or last saved to

    def disk_mtime(self):
        try:
            return self.path.stat().st_mtime_ns
        except OSError:
            return None

    def dirty(self) -> bool:
        return bool(self.session.cmd("document.inspect").get("dirty"))

    @property
    def base_dir(self):
        """The folder relative part paths in this document are taken from."""
        return self.path.parent

    def metadata(self):
        meta = self.session.cmd("document.metadata").get("metadata") or {}
        meta = read_metadata(meta)
        return files_on_disk(meta, self.base_dir) if self.base_dir is not None else meta

    def set_metadata(self, data):
        # part files relative to this document: the project folder can move
        self.session.cmd("document.metadata.set", {"key": METADATA_KEY,
                                                    "value": files_relative(data, self.path.parent)})

    def save(self):
        cur = self.disk_mtime()
        if self.mtime is not None and cur is not None and cur != self.mtime:
            raise ValueError(f"{self.path.name} changed on disk since {self.name!r} was loaded here (saved in the "
                             "SolidCraft app?): close_document it and open it again, so that change is not lost")
        check_windows_writable(self.path)
        self.session.tool("save", {"path": str(self.path)})
        self.mtime = self.disk_mtime()
        reload_windows(self.path)  # checks for unsaved work in the window once more, right before the reload

    def info(self):
        return {"name": self.name, "kind": self.kind, "path": str(self.path)}


class WindowDocument(Document):
    """The design open in the running SolidCraft window (`connect_window`). The user owns it: it is read and
    edited through the window's own session, never opened, replaced or saved from here (the user saves, in the
    app), and nothing reloads it from disk."""

    window = True

    def __init__(self, name, kind, session):
        super().__init__(name, kind, "<window>", session)  # a path no file has
        try:
            self.document_id = session.cmd("document.revision", timeout=getattr(session, "CONNECT_TIMEOUT", None)).get("document_id")
        except (AttributeError, SolidCraftError):
            self.document_id = None  # older app or a stand-in session: no tab check
        st = self.state()
        self.pinned_path = st[0] if st else None  # the file of the connected tab, also while another is in front
        _WINDOWS.add(self)

    @property
    def base_dir(self):
        # the folder of the connected tab's file (#190); an unsaved design has none, its paths stay as stored.
        # Read again here, so a "save as" into another folder is followed before the next write check
        st = self.state()
        if st and st[0] is not None and self.document_id is not None and st[2] == self.document_id:
            self.pinned_path = st[0]
        return self.pinned_path.parent if getattr(self, "pinned_path", None) else None

    def state(self):
        """(path, dirty, document_id) of the window's active tab, or None when the window does not answer.
        A window that does not answer (also one whose session closed after a timeout) blocks only its own file
        (`pinned_path`), until close_document disconnects it: a busy app must not lose that protection."""
        s = self.session
        if getattr(s, "_closed", False):
            return None
        t = getattr(s, "CONNECT_TIMEOUT", None)
        try:
            i = s.cmd("document.inspect", {"measure": False}, timeout=t)
            r = s.cmd("document.revision", timeout=t)
        except Exception:
            return None
        if not isinstance(i, dict) or not isinstance(r, dict):
            return None
        p = i.get("path")
        return (Path(p).resolve() if p else None, bool(i.get("dirty")), r.get("document_id"))

    def file_path(self):
        """The file of the design in front in the window (None for an unsaved one or a stand-in session)."""
        st = self.state()
        return st[0] if st else None

    def reload(self):
        """Show the file on disk again. SolidCraft 0.43 has no revert and ignores `open` for the file it
        already shows, so the window starts a new design and opens the file (its undo history ends here).
        A failure is a warning, not an error: the file is written either way."""
        path = self.file_path()
        if path is None:
            return False
        try:
            self.session.batch([{"command": "new_design", "params": {}},
                                {"command": "open", "params": {"path": str(path)}}])
        except Exception as e:
            warnings.warn(f"the SolidCraft window {self.name!r} could not open {path.name} again ({e}): open it "
                          "in the app before saving there")
            return False
        try:
            self.document_id = self.session.cmd("document.revision").get("document_id")
        except Exception:
            self.document_id = None
        self.pinned_path = path
        return True

    def check_active(self):
        """Every call goes to the window's active tab: refuse when the user switched to another design."""
        if self.document_id is None:
            return
        now = self.session.cmd("document.revision").get("document_id")
        if now != self.document_id:
            raise ValueError(f"the active design in the SolidCraft window is not the one {self.name!r} was connected to "
                             "(another tab is in front): show that tab again, or close_document and connect_window anew")

    def disk_mtime(self):
        return None

    def save(self):
        raise ValueError(f"{self.name!r} is the design in the open SolidCraft window: save it in the app (Ctrl+S)")

    def set_metadata(self, data):
        raise ValueError(f"{self.name!r} is the design in the open SolidCraft window: Mechvane does not write its metadata")

    def info(self):
        return {"name": self.name, "kind": self.kind, "window": True}


class Workspace:
    """The open documents. Every session may read and write below `root`."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.docs = {}

    def session(self):
        return Session(allow_paths=[self.root])

    def _path(self, name, path):
        if name is not None:
            _validate_name(name)
        p = Path(path) if path else self.root / f"{name}.solidcraft"
        if not p.is_absolute():
            p = (self.root / p).resolve()
        else:
            p = p.resolve()
        try:
            p.relative_to(self.root)
        except ValueError:
            raise ValueError(f"path {path or name!r} is outside workspace {self.root}")
        if p == self.root:
            raise ValueError("document path cannot be workspace root")
        return p

    def new(self, kind, name, path=None, overwrite: bool = False):
        if name in self.docs:
            raise ValueError(f"a document named {name!r} is already open")
        p = self._path(name, path)
        if p.exists() and not overwrite:
            raise FileExistsError(f"document file {str(p)!r} already exists on disk; use open or pass overwrite=True")
        s = self.session()
        try:
            s.tool("new_design", {"name": name})
            doc = Document(name, kind, p, s)
            doc.set_metadata({"kind": kind, "format": 1})
            p.parent.mkdir(parents=True, exist_ok=True)
            doc.save()
            self.docs[name] = doc
            return doc
        except Exception:
            s.close()
            raise

    def open(self, path, name=None):
        p = self._path(name, path)
        for doc in self.docs.values():
            if doc.path.resolve() == p:
                if name and name != doc.name:
                    raise ValueError(f"document {str(p)!r} is already open under name {doc.name!r}")
                return self._fresh(doc)
        name = name or p.stem
        if not name:
            raise ValueError(f"cannot determine document name from path {str(p)!r}")
        if name in self.docs:
            raise ValueError(f"a document named {name!r} is already open")
        s = self.session()
        try:
            s.tool("open", {"path": str(p)})
            kind = read_metadata(s.cmd("document.metadata").get("metadata")).get("kind")
            if kind is None:
                # A plain SolidCraft design: an assembly if it links other designs.
                kind = ASSEMBLY if s.cmd("component.links").get("links") else PART
        except Exception:
            s.close()
            raise
        doc = Document(name, kind, p, s)
        self.docs[name] = doc
        return doc

    def connect_window(self, name="window", connect="auto", token=None):
        """Attach the design in the running SolidCraft window as document `name` (kind from its content)."""
        _validate_name(name)
        if name in self.docs:
            raise ValueError(f"a document named {name!r} is already open")
        s = Session(allow_paths=[self.root], connect=connect, token=token)
        try:
            meta = s.cmd("document.metadata", timeout=Session.CONNECT_TIMEOUT).get("metadata")  # first call: a dead port ends here
            kind = read_metadata(meta).get("kind")
            if kind is None:
                kind = ASSEMBLY if s.cmd("component.links").get("links") else PART
            doc = WindowDocument(name, kind, s)
        except Exception:
            s.close()
            raise
        self.docs[name] = doc
        return doc

    def file_docs(self):
        """The open documents that are files (not the design in the SolidCraft window): what code that saves,
        relinks or finds parts by file name may touch."""
        return [d for d in self.docs.values() if not getattr(d, "window", False)]

    def file_doc(self, name):
        """The open file document `name`, or None (also when `name` is the window's design)."""
        d = self.docs.get(name)
        return None if d is None or getattr(d, "window", False) else self._fresh(d)

    def get(self, name, kind=None):
        doc = self.docs.get(name)
        if doc is None:
            raise KeyError(f"no open document {name!r} (open: {', '.join(self.docs) or 'none'})")
        if kind and doc.kind != kind:
            raise ValueError(f"{name!r} is a {doc.kind}, not a {kind}")
        if getattr(doc, "window", False):
            doc.check_active()
        if kind == ASSEMBLY and getattr(doc, "window", False):
            # joints, links and bolted connections work on files next to the assembly: not for the window yet
            raise ValueError(f"{name!r} is the assembly open in the SolidCraft window: assembly tools need its file "
                             "(save it in the app and open_document it); in the window only reading and `run` work")
        return self._fresh(doc)

    def _fresh(self, doc):
        """The document, read again from its file if that changed on disk since it was loaded or saved
        here (saved by hand in SolidCraft, or by another process). Reloads in the same session and
        Document, so callers holding it keep a working reference."""
        cur = doc.disk_mtime()
        if cur is None or doc.mtime is None or cur == doc.mtime:
            return doc
        if doc.dirty():
            raise ValueError(f"{doc.name!r} changed on disk and has unsaved changes here: "
                             f"save it to keep these changes, or close it with discard=True to load the file")
        doc.session.tool("open", {"path": str(doc.path)})
        doc.mtime = cur
        return doc

    def close(self, name):
        if name not in self.docs:
            self.get(name)  # the usual error
        doc = self.docs.pop(name)
        _WINDOWS.discard(doc)  # a disconnected window protects nothing any more
        doc.session.close()

    def close_all(self):
        for name in list(self.docs):
            self.close(name)

    def reader(self, path):
        """A throwaway session with a design opened read-only (for looking up face names)."""
        s = self.session()
        try:
            s.tool("open", {"path": str(path)})
            return s
        except Exception:
            s.close()
            raise
