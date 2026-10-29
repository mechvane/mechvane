"""Mechvane: an Inventor-style document layer on top of SolidCraft.

Parts and assemblies are separate .solidcraft files. Each open document runs in its own
headless `solidcraft-cli mcp` session. See docs/adr/0001-grundlage-solidcraft.md."""

from pathlib import Path

METADATA_KEY = "dev.mechvane"
# Key used before the rename to Mechvane; still read so older files keep working.
LEGACY_METADATA_KEY = "io.github.nilsgollub.inventa"


def _read_version() -> str:
    """The installed package's version, else the one in pyproject.toml (a source checkout)."""
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version("mechvane")
    except PackageNotFoundError:
        pass
    import tomllib
    toml_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        return tomllib.loads(toml_path.read_text(encoding="utf-8"))["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"


__version__ = _read_version()


def _map_files(v, fn):
    if isinstance(v, dict):
        return {k: (fn(x) if k == "file" and isinstance(x, str) and x else _map_files(x, fn)) for k, x in v.items()}
    if isinstance(v, list):
        return [_map_files(x, fn) for x in v]
    return v


def files_relative(meta, base) -> dict:
    """Metadata with every part `file` relative to the document's folder, so a project folder can be
    moved or copied to another computer. Paths on another drive stay absolute."""
    import os

    def rel(f):
        p = Path(f)
        if not p.is_absolute():
            return f
        try:
            return Path(os.path.relpath(p, base)).as_posix()
        except ValueError:  # another drive on Windows
            return f
    return _map_files(meta, rel)


def files_on_disk(meta, base) -> dict:
    """Metadata with every part `file` as an absolute path. Relative paths are taken from the
    document's folder; an absolute path from before a move that no longer exists is looked for by
    its name in the document's folder."""
    base = Path(base)

    def resolve(f):
        p = Path(f)
        if not p.is_absolute():
            return str((base / p).resolve())
        if not p.is_file() and (base / p.name).is_file():
            return str((base / p.name).resolve())
        return f
    return _map_files(meta, resolve)


def read_metadata(meta: dict) -> dict:
    """This layer's entry from a document's metadata map, under the current or the legacy key."""
    meta = meta or {}
    return meta.get(METADATA_KEY) or meta.get(LEGACY_METADATA_KEY) or {}
