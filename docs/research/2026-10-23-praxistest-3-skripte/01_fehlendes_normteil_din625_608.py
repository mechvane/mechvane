#!/usr/bin/env python3
"""Befund 1: Fehlendes Normteil DIN 625 608 in mechvane.standard_parts.
Aufruf von standard_parts.create(ws, 'DIN 625', '608') wirft ValueError,
obwohl DIN 625 608 (8x22x7 mm) das Standard-Kugellager im 3D-Druck und
für kleine Lagerböcke ist. In BEARINGS_6000 existieren nur 6000 bis 6005.

Ausführen mit: PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/01_fehlendes_normteil_din625_608.py
"""
import sys
from pathlib import Path

from mechvane.documents import Workspace
from mechvane import standard_parts

def main():
    ws = Workspace("/tmp/praxis-test-repro-01")
    try:
        res = standard_parts.create(ws, "DIN 625", "608")
        print("Unerwartet erfolgreich:", res)
        sys.exit(1)
    except ValueError as e:
        print("Erfolgreich reproduziert:")
        print(f"  Typ: {type(e).__name__}")
        print(f"  Nachricht: {e}")
        assert "unknown bearing size '608'" in str(e)
        assert "available: 6000, 6001, 6002, 6003, 6004, 6005" in str(e)
    finally:
        ws.close_all()

if __name__ == "__main__":
    main()
