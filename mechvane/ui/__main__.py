"""CLI entry point: python3 -m mechvane.ui <file.solidcraft> [--port 8765]."""

import argparse

from .server import run_server


def main():
    parser = argparse.ArgumentParser(description="Mechvane read-only web UI (Stage 1)")
    parser.add_argument("file", help="Path to a .solidcraft part or assembly file")
    parser.add_argument("--port", type=int, default=8765, help="Local TCP port on 127.0.0.1 (default: 8765)")
    args = parser.parse_args()
    run_server(args.file, port=args.port)


if __name__ == "__main__":
    main()
