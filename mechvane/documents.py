"""Part and assembly documents, each a .solidcraft file in its own SolidCraft session."""

from pathlib import Path

from . import METADATA_KEY, read_metadata
from .solidcraft import Session, SolidCraftError

PART, ASSEMBLY = "part", "assembly"


def _validate_name(name: str):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("document name cannot be empty")
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"document name {name!r} cannot contain path separators or '..'")


class Document:
    def __init__(self, name, kind, path, session):
        self.name, self.kind, self.path, self.session = name, kind, Path(path), session

    def metadata(self):
        meta = self.session.cmd("document.metadata").get("metadata") or {}
        return read_metadata(meta)

    def set_metadata(self, data):
        self.session.cmd("document.metadata.set", {"key": METADATA_KEY, "value": data})

    def save(self):
        self.session.tool("save", {"path": str(self.path)})

    def info(self):
        return {"name": self.name, "kind": self.kind, "path": str(self.path)}


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
                return doc
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

    def get(self, name, kind=None):
        doc = self.docs.get(name)
        if doc is None:
            raise KeyError(f"no open document {name!r} (open: {', '.join(self.docs) or 'none'})")
        if kind and doc.kind != kind:
            raise ValueError(f"{name!r} is a {doc.kind}, not a {kind}")
        return doc

    def close(self, name):
        self.get(name).session.close()
        del self.docs[name]

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
