"""CLI entry point: python3 -m mechvane.ui <path> [--port 8765]."""

import argparse

from .server import run_server


def main():
    parser = argparse.ArgumentParser(description="Mechvane read-only web UI (Stage 1)")
    parser.add_argument("path", help="Path to a .solidcraft file or project folder")
    parser.add_argument("--port", type=int, default=8765, help="Local TCP port on 127.0.0.1 (default: 8765)")
    args = parser.parse_args()
    run_server(args.path, port=args.port)


if __name__ == "__main__":
    main()
