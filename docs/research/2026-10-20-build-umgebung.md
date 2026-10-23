# Build-Umgebung für SolidCraft-PRs

Stand 2026-10-20. Frage des Nutzers: Dev-VM oder Colab? Messung auf Colab
`--high-mem` (8 Kerne, 50 GB RAM), SolidCraft `main`, Skript
[`2026-10-20-colab-build.sh`](2026-10-20-colab-build.sh).

| Schritt | Zeit |
|---|---|
| Rust 1.99.1 und Systempakete | 28 s |
| Klon (`--depth 1`) | 5 s |
| Kalter Release-Build `solidcraft-cli` | 387 s |
| Neubau nach Änderung in `crates/doc` (Release) | 222 s |
| `cargo xtask ci` komplett (Debug, alle Tests) | 5 201 s (87 min), `target` 17 GB |

Kosten: 0,41 CU für den ganzen Lauf (~1,6 h), Guthaben 383 CU.

`cargo xtask ci` endete rot, aber nur wegen der Umgebung:

- `wasm32-unknown-unknown` fehlte (`can't find crate for core`):
  `rustup target add wasm32-unknown-unknown` ins Skript.
- GPU-Tests (`crates/gpu/tests/capture.rs`, Snapshot-Tests der CLI, Teile von
  `ui-egui`, `mcp`, `io`) brauchen einen Grafikadapter. Auf dem
  Steuer-Container läuft dafür Mesa llvmpipe. Auf Colab vermutlich
  `mesa-vulkan-drivers` (lavapipe) nachinstallieren, noch nicht geprüft.
- Sonst 1 236 + 110 + 41 Tests grün in den großen Paketen.

## Empfehlung

**Colab `--high-mem`, nicht die Dev-VM.** Die Dev-VM (102, 6 Kerne, 20 GB)
hängt an der GPU per Passthrough: Ihr Start belegt 20 GB fest und fährt Frigate
und Open WebUI herunter. Colab kostet praktisch nichts und berührt das Homelab
nicht.

Arbeitsweise für einen PR: lokal ändern, auf einen Zweig im Fork pushen, in
einer Colab-Sitzung nur die betroffenen Crates bauen und testen
(`cargo test -p <crate>`, `cargo fmt --check`, `cargo clippy -p <crate>`).
Den vollen `cargo xtask ci` (87 min) höchstens einmal vor „ready for review“,
die volle CI läuft upstream ohnehin nach dem Label `approved-for-ci`.

Falls PRs häufig werden: kleiner Build-Container auf dem Proxmox-Host
(ohne GPU, dauerhafter Cache). Das ist eine Homelab-Änderung, nur mit OK.
