"""The `mechvane` command: setup, ui and mcp.

  mechvane setup                 download the pinned SolidCraft CLI and web app into the cache
  mechvane ui [path] [--demo]    open the web UI for a .solidcraft file or project folder
  mechvane shortcut [folder]     add a start menu entry that opens folder (default: ~/Mechvane)
  mechvane mcp                   run the MCP server on stdio (for Claude Code and other agents)
"""

import argparse
import os
import subprocess
import sys
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
    print("Ready. Try: mechvane ui --demo")
    return 0


def demo_folder() -> Path:
    """Folder with the example models, built on first use."""
    from .documents import Workspace
    from .examples import DEMOS, build_all

    folder = install.CACHE / "demo"
    if all((folder / f"{name}.solidcraft").is_file() for name, _, _ in DEMOS):
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Building the example models in {folder} ...", flush=True)
    ws = Workspace(folder)
    try:
        build_all(ws)
    finally:
        ws.close_all()
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
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
