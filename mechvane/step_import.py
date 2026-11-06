"""STEP (and IGES, FreeCAD, Rhino) files as reference parts: a fixed body without history, e.g. a bought-in part
for an assembly or someone else's part to measure and check (ROADMAP v0.1, "STEP als Referenzkörper"). Not the
lossless import with feature history, which stays a long-term goal.

SolidCraft's file.insert_step brings the file in as a component; Mechvane parts are designs without components
(ADR 0001). So the import runs in a scratch session and component.extract writes the component's history (one
Import base feature) to its own design file, which is then a plain part."""

from pathlib import Path

from .documents import PART
from .solidcraft import Session

SUFFIXES = {".step", ".stp", ".iges", ".igs", ".fcstd", ".3dm"}


def import_step(ws, source, name: str | None = None, path: str | None = None, overwrite: bool = False,
                up: str = "z") -> dict:
    """Make a part file from a STEP file and open it. source: the file (absolute, or relative to the project
    folder); name: the part's name (default: the file name); path: where the part file goes (default
    <project>/<name>.solidcraft); up: "y" when the file has Y up (turned so that Y becomes Z)."""
    src = Path(source).expanduser()
    if not src.is_absolute():
        src = (ws.root / src)
    src = src.resolve()
    if not src.is_file():
        raise FileNotFoundError(f"no such file: {str(src)!r}")
    if src.suffix.lower() not in SUFFIXES:
        raise ValueError(f"not a STEP, IGES, FreeCAD or Rhino file: {src.name!r}")
    if up not in ("z", "y"):
        raise ValueError("up: 'z' (the file's axes as they are) or 'y' (the file has Y up)")
    name = name or src.stem
    target = ws._path(name, path)
    if name in ws.docs:
        raise ValueError(f"a document named {name!r} is already open")
    if target.exists() and not overwrite:
        raise FileExistsError(f"document file {str(target)!r} already exists on disk; pass overwrite=True")
    target.parent.mkdir(parents=True, exist_ok=True)

    scratch = Session(allow_paths=[ws.root, src.parent, target.parent])
    try:
        made = scratch.cmd("file.insert_step", {"path": str(src), "name": name, "up": up})
        out = scratch.cmd("component.extract", {"component": made["component"], "path": str(target)})
    finally:
        scratch.close()

    doc = ws.open(target, name)
    s = doc.session
    nested = [c["name"] for c in s.cmd("component.list")["components"][1:]]
    doc.kind = PART
    doc.set_metadata({"kind": PART, "format": 1, "imported_from": src.name})
    doc.save()
    bodies = [{"name": b["name"], "volume_mm3": round(b.get("volume_mm3", 0.0), 3), "bbox": b.get("bbox")}
              for b in s.cmd("inspect.measure", {}).get("bodies", [])]
    warnings = list(made.get("warnings") or []) + list(out.get("warnings") or [])
    if nested:
        # a STEP assembly keeps its products as components inside the part: fine to look at and measure,
        # but insert the parts one by one when the assembly needs their joints
        warnings.append(f"the file is an assembly: its parts stay components inside {name} ({', '.join(nested)})")
    return {**doc.info(), "source": str(src), "system": made.get("system"), "bodies": bodies, "warnings": warnings}
