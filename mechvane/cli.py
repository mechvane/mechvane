"""The `mechvane` command: setup, ui, shortcut, mcp and check.

  mechvane setup                 download the pinned SolidCraft CLI and web app into the cache
  mechvane ui [path] [--demo]    open the web UI for a .solidcraft file or project folder
  mechvane shortcut [folder]     add a start menu entry that opens folder (default: ~/Mechvane)
  mechvane mcp                   run the MCP server on stdio (for Claude Code and other agents)
  mechvane check [file]          run design rule checks on a .solidcraft file or open SolidCraft window
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

from . import install
from .ui import appwindow, webapp


def cmd_setup(args) -> int:
    cli = install.install_cli()
    print(f"SolidCraft CLI {install.VERSION}: {cli}")
    out = subprocess.run([str(cli), "--version"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=60)
    if out.returncode != 0:
        print(f"  but it does not start: {(out.stderr or out.stdout).strip()}", file=sys.stderr)
        return 1
    print(f"  {out.stdout.strip()}")
    print(f"SolidCraft web app {webapp.VERSION}: {webapp.webapp_dir()}")
    print("Ready. Next: connect your agent (mechvane mcp) and the SolidCraft app you have open, see docs/installation.md")
    return 0


def demo_folder() -> Path:
    """Folder with the example models, built on first use."""
    from .documents import Workspace
    from .examples import build_all

    folder = install.CACHE / "demo"
    done = folder / ".complete"  # written last, lists every file the build made
    if done.is_file() and all((folder / n).is_file() for n in done.read_text(encoding="utf-8").split()):
        return folder
    # A build that broke off (a crash, Ctrl+C) leaves some files behind: start again from an empty
    # folder. Built in place, not moved there afterwards: assemblies keep their parts' paths.
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    print(f"Building the example models in {folder} ...", flush=True)
    ws = Workspace(folder)
    try:
        build_all(ws)
    finally:
        ws.close_all()
    done.write_text("\n".join(sorted(p.name for p in folder.glob("*.solidcraft"))), encoding="utf-8")
    return folder


def cmd_ui(args) -> int:
    from .ui.server import run_server

    if args.demo:
        path = demo_folder()
    elif args.path:
        path = Path(args.path)
    else:
        path = Path.cwd()
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 1
    opener = None
    if args.browser:
        opener = lambda url, stop: webbrowser.open(url)  # noqa: E731
    elif not args.no_browser:
        opener = lambda url, stop: appwindow.open_window(url, on_close=stop)  # noqa: E731
    run_server(str(path), port=args.port, opener=opener)
    return 0


def cmd_shortcut(args) -> int:
    folder = Path(args.folder).expanduser().resolve() if args.folder else Path.home() / "Mechvane"
    try:
        entry = appwindow.create_shortcut(folder)
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        print(f"could not add the start menu entry: {e}", file=sys.stderr)
        return 1
    print(f"Start menu entry: {entry}\nOpens: {folder}")
    return 0


def cmd_mcp(args) -> int:
    if args.workspace:
        os.environ["MECHVANE_WORKSPACE"] = args.workspace
    from .server import main

    main()
    return 0


def _format_check_text(result: dict) -> str:
    """Format a design_rules.check() result for readable terminal output."""
    lines = [result["summary"]]
    if result.get("material"):
        mat_src = result.get("material_source")
        mat_line = f"Material: {result['material']}" + (f" ({mat_src})" if mat_src else "")
        lines.append(mat_line)
    for finding in result.get("checks", []):
        status = str(finding.get("status", "ok")).upper()
        rule = finding.get("rule", "")
        msg = finding.get("message", "")
        lines.append(f"[{status}] {rule}: {msg}")
        details = []
        if finding.get("value") is not None:
            details.append(f"value: {finding['value']}")
        if finding.get("threshold") is not None:
            details.append(f"threshold: {finding['threshold']}")
        loc = finding.get("location") or {}
        for key in ("face", "edge", "body"):
            if loc.get(key):
                details.append(f"{key}: {loc[key]}")
                break
        if details:
            lines.append("  " + " | ".join(details))
        src = finding.get("source")
        if isinstance(src, dict):
            title = src.get("titel") or src.get("entry") or ""
            ref_parts = [p for p in (src.get("entry"), src.get("stelle"), src.get("url")) if p]
            if title and ref_parts:
                lines.append(f"  source: {title} ({', '.join(ref_parts)})")
            elif ref_parts:
                lines.append(f"  source: {', '.join(ref_parts)}")
            elif title:
                lines.append(f"  source: {title}")
            zitat = src.get("zitat")
            if zitat:
                lines.append(f'  quote: "{zitat}"')
    return "\n".join(lines)


def cmd_check(args) -> int:
    from . import design_rules, hole_tables
    from .documents import PART, Workspace
    from .solidcraft import SolidCraftError

    if args.material:
        try:
            hole_tables.normalize_material(args.material)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

    vec = design_rules.parse_build_direction("+Z", allow_vector=False)
    ws = None
    tmp_dir = None
    try:
        if args.file:
            path = Path(args.file)
            if not path.is_file():
                print(f"not found: {path}", file=sys.stderr)
                return 2
            resolved = path.resolve()
            ws = Workspace(resolved.parent)
            doc = ws.open(resolved.name)
        else:
            tmp_dir = tempfile.TemporaryDirectory(prefix="mechvane-check-")
            ws = Workspace(tmp_dir.name)
            doc = ws.connect_window()
        doc = ws.get(doc.name, PART)
        result = design_rules.check(doc, profile=args.profile, build_direction=vec, material=args.material)
    except (SolidCraftError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    finally:
        if ws is not None:
            try:
                ws.close_all()
            except Exception:
                pass
        if tmp_dir is not None:
            tmp_dir.cleanup()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_format_check_text(result))

    has_fail = (
        result.get("verdict") == "fail"
        or any(c.get("status") == "fail" for c in result.get("checks", []))
    )
    return 1 if has_fail else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="mechvane", description="Mechvane: parametric CAD, you and your agent on the same model, on SolidCraft")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("setup", help="download the pinned SolidCraft CLI and web app")
    p.set_defaults(func=cmd_setup)
    p = sub.add_parser("ui", help="open the web UI")
    p.add_argument("path", nargs="?", help="a .solidcraft file or project folder (default: current folder)")
    p.add_argument("--demo", action="store_true", help="open the example models")
    p.add_argument("--port", type=int, default=8765, help="local port on 127.0.0.1 (default: 8765)")
    p.add_argument("--no-browser", action="store_true", help="do not open a window")
    p.add_argument("--browser", action="store_true", help="open a tab in the default browser instead of an app window")
    p.set_defaults(func=cmd_ui)
    p = sub.add_parser("shortcut", help="add a start menu entry (Windows, Linux)")
    p.add_argument("folder", nargs="?", help="project folder it opens (default: ~/Mechvane)")
    p.set_defaults(func=cmd_shortcut)
    p = sub.add_parser("mcp", help="run the MCP server on stdio")
    p.add_argument("--workspace", help="folder for new documents (default: $MECHVANE_WORKSPACE)")
    p.set_defaults(func=cmd_mcp)
    p = sub.add_parser("check", help="check a part against design rules")
    p.add_argument("file", nargs="?", help="a .solidcraft part file (default: active design in open SolidCraft window)")
    p.add_argument("--profile", choices=["fdm_0.4", "cnc_alu"], help="manufacturing profile (default: saved in file, else fdm_0.4)")
    p.add_argument("--material", metavar="NAME", help="material for thread depth rules (e.g. steel, alu, brass)")
    p.add_argument("--json", action="store_true", help="output check_design JSON unchanged")
    p.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
