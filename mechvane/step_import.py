"""STEP (and IGES, FreeCAD, Rhino) files as reference parts: a fixed body without history, e.g. a bought-in part
for an assembly or someone else's part to measure and check (ROADMAP v0.1, "STEP als Referenzkörper"). Not the
lossless import with feature history, which stays a long-term goal.

SolidCraft's file.insert_step brings the file in as a component; Mechvane parts are designs without components
(ADR 0001). So the import runs in a scratch session and component.extract writes the component's history (one
Import base feature) to its own design file, which is then a plain part.

When split=True, a STEP file with multiple bodies is imported as an assembly: each body becomes its own part file
<name>_<body_name>.solidcraft via component.extract, and an assembly file <name>.solidcraft is created with each
part inserted at its original position (the first part grounded)."""

from pathlib import Path
import re
import tempfile

from .documents import ASSEMBLY, PART, check_windows_writable
from . import links
from .solidcraft import Session

SUFFIXES = {".step", ".stp", ".iges", ".igs", ".fcstd", ".3dm"}


def _sanitize_name(name: str) -> str:
    """Sanitize body name for file names: replace invalid characters with underscores."""
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", name.strip()).strip("_")
    return cleaned


def import_step(ws, source, name: str | None = None, path: str | None = None, overwrite: bool = False,
                up: str = "z", split: bool = False) -> dict:
    """Make a part or assembly file from a STEP file and open it. source: the file (absolute, or relative to the project
    folder); name: the part's/assembly's name (default: the file name); path: where the file goes (default
    <project>/<name>.solidcraft); up: "y" when the file has Y up (turned so that Y becomes Z); split: if True,
    a file with multiple bodies is imported as an assembly with individual part files for each body."""
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

    if not split:
        scratch = Session(allow_paths=[ws.root, src.parent, target.parent])
        try:
            made = scratch.cmd("file.insert_step", {"path": str(src), "name": name, "up": up})
            check_windows_writable(target)  # extract writes the file before any save could check (#190)
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

    # split=True: import into scratch session, extract bodies into individual part files, then create assembly
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()  # long names: SolidCraft refuses Windows 8.3 short names
        temp_all = tmp_path / f"{name}_temp.solidcraft"
        scratch = Session(allow_paths=[ws.root, src.parent, target.parent, tmp_path])
        try:
            made = scratch.cmd("file.insert_step", {"path": str(src), "name": name, "up": up})
            out = scratch.cmd("component.extract", {"component": made["component"], "path": str(temp_all)})
        finally:
            scratch.close()

        warnings = list(made.get("warnings") or []) + list(out.get("warnings") or [])

        s_temp = Session(allow_paths=[ws.root, target.parent, tmp_path])
        try:
            s_temp.cmd("doc.open", {"path": str(temp_all)})
            b_list = s_temp.cmd("inspect.measure", {}).get("bodies", [])

            # Plan part names and check for conflicts before writing anything
            part_specs = []
            taken_suffixes = set()
            for i, b in enumerate(b_list):
                bname = b.get("name") or ""
                clean_bname = _sanitize_name(bname)
                if not clean_bname:
                    clean_bname = str(i + 1)
                cand = clean_bname
                num = 2
                while cand in taken_suffixes:
                    cand = f"{clean_bname}_{num}"
                    num += 1
                taken_suffixes.add(cand)
                part_name = f"{name}_{cand}"
                part_target = target.parent / f"{part_name}.solidcraft"
                part_specs.append((bname, part_name, part_target))

            for _, p_name, p_target in part_specs:
                if p_name in ws.docs:
                    raise ValueError(f"a document named {p_name!r} is already open")
                if p_target.exists() and not overwrite:
                    raise FileExistsError(f"document file {str(p_target)!r} already exists on disk; pass overwrite=True")
            # every file this import writes, checked before the first one is written: no half-written import (#190)
            for _, _, p_target in part_specs:
                check_windows_writable(p_target)
            check_windows_writable(target)

            # Extract each body to its own part file
            parts_info = []
            extracted_files = []
            for i, (bname, p_name, p_target) in enumerate(part_specs):
                b_step = tmp_path / f"body_{i}.step"
                s_temp.cmd("file.export_step", {"path": str(b_step), "bodies": [bname]})

                scratch_b = Session(allow_paths=[ws.root, target.parent, tmp_path])
                try:
                    m_b = scratch_b.cmd("file.insert_step", {"path": str(b_step), "name": p_name, "up": "z"})
                    check_windows_writable(p_target)
                    scratch_b.cmd("component.extract", {"component": m_b["component"], "path": str(p_target)})
                finally:
                    scratch_b.close()

                p_doc = ws.open(p_target, p_name)
                p_doc.kind = PART
                p_doc.set_metadata({"kind": PART, "format": 1, "imported_from": src.name})
                p_doc.save()
                p_meas = p_doc.session.cmd("inspect.measure", {})
                p_bodies = p_meas.get("bodies", [])
                vol = p_bodies[0].get("volume_mm3", 0.0) if p_bodies else 0.0
                bbox = p_bodies[0].get("bbox") if p_bodies else None
                ws.close(p_name)

                parts_info.append({
                    "name": p_name,
                    "path": str(p_target),
                    "volume_mm3": round(vol, 3),
                    "bbox": bbox,
                })
                extracted_files.append((p_target, p_name))
        finally:
            s_temp.close()

    # Create assembly and insert parts at original locations (first grounded, no joints)
    asm_doc = ws.new(ASSEMBLY, name, path=str(target), overwrite=overwrite)
    for p_target, p_name in extracted_files:
        links.insert(ws, asm_doc, p_target)
    asm_doc.set_metadata({"kind": ASSEMBLY, "format": 1, "imported_from": src.name})
    asm_doc.save()

    asm_meas = asm_doc.session.cmd("inspect.measure", {})
    asm_bodies = [{"name": b["name"], "volume_mm3": round(b.get("volume_mm3", 0.0), 3), "bbox": b.get("bbox")}
                  for b in asm_meas.get("bodies", [])]

    return {
        **asm_doc.info(),
        "assembly": asm_doc.name,
        "source": str(src),
        "system": made.get("system"),
        "parts": parts_info,
        "bodies": asm_bodies,
        "warnings": warnings,
    }
