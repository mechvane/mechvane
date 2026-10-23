"""Mechvane: an Inventor-style document layer on top of SolidCraft.

Parts and assemblies are separate .solidcraft files. Each open document runs in its own
headless `solidcraft-cli mcp` session. See docs/adr/0001-grundlage-solidcraft.md."""

METADATA_KEY = "dev.mechvane"
# Key used before the rename to Mechvane; still read so older files keep working.
LEGACY_METADATA_KEY = "io.github.nilsgollub.inventa"


def read_metadata(meta: dict) -> dict:
    """This layer's entry from a document's metadata map, under the current or the legacy key."""
    meta = meta or {}
    return meta.get(METADATA_KEY) or meta.get(LEGACY_METADATA_KEY) or {}
