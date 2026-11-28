#!/bin/bash
# Build the edge-distance plugin (#220): wasm32 core module -> component -> package folder and zip.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"
PY=$(command -v python3 || command -v python)
cargo build --release --target wasm32-unknown-unknown
wasm-tools component new target/wasm32-unknown-unknown/release/mechvane_edge_distance.wasm \
  -o mechvane-edge-distance/mechvane-edge-distance.wasm
(cd mechvane-edge-distance && rm -f ../mechvane-edge-distance.zip && "$PY" -c "
import zipfile
with zipfile.ZipFile('../mechvane-edge-distance.zip', 'w') as z:
    z.write('plugin.json')
    z.write('mechvane-edge-distance.wasm')")
ls -l mechvane-edge-distance/mechvane-edge-distance.wasm mechvane-edge-distance.zip
