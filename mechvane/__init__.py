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


def read_metadata(meta: dict) -> dict:
    """This layer's entry from a document's metadata map, under the current or the legacy key."""
    meta = meta or {}
    return meta.get(METADATA_KEY) or meta.get(LEGACY_METADATA_KEY) or {}
