# Plugin `mechvane-edge-distance` (U2, #220)

Die Mechvane-Regel `hole_edge_distance` (Randabstand von Bohrungen und Langlochenden) als Befehls-Plugin für
SolidCraft 0.50 (`commands@0.2`, Entry `hole-edge-distance`, Wirkung `read`). Port von `mechvane/design_rules.py`
(`_extract_holes`, `_check_body` Regel 1) und den Helfern aus `mechvane/geometry.py`; die Python-Fassung ist das
Pflichtenheft.

- **Bauen:** `./build.sh` (rustup mit Target `wasm32-unknown-unknown`, `wasm-tools`; `PATH=$HOME/.cargo/bin:$PATH`),
  ergibt `mechvane-edge-distance/mechvane-edge-distance.wasm` und `mechvane-edge-distance.zip` (beide nicht im Repo).
- **Prüfen:** `solidcraft-cli plugin check mechvane-edge-distance`.
- **Tor:** `SOLIDCRAFT_CLI=… python3 plugins/edge-distance/gate.py [teil …]` baut die vier Referenzteile und die zwei Gegentests unter `tests/`, führt das
  Plugin aus und vergleicht mit den Baselines `tests/reference/design_rules/<teil>.<profil>.json` (Fläche, Status,
  Wert, Schwelle, Punkt, Katalogeintrag) und mit `design_rules.check` in derselben Sitzung (ganzer Befund mit
  Meldung, Quelle und Zitat). Gibt die Laufzeit je Teil aus. Nicht Teil von `tests/mechvane/check.py`, damit dieses
  nicht länger wird und ohne Rust läuft.
- **Installieren:** nur über die CLI oder die App, nie aus einer MCP-Sitzung:
  `solidcraft-cli exec plugin.install '{"path":"mechvane-edge-distance.zip","dry_run":true}'`, dann mit `approval`.
- **CI:** `.github/workflows/plugin.yml` (Linux und Windows, läuft nur im öffentlichen Repo; seit 2026-11-28 aktiv).

## Quelle

Der Befund trägt `source` wie `design_rules.check` (`entry`, `titel`, `url`, `stelle`, `zitat` aus der ersten
Quelle des Katalogeintrags `randabstand_bohrung_kante`). Der Eintrag wird beim Bauen per `include_str!` aus
`katalog/eintraege/schrauben/` eingelesen: Der Katalog bleibt die einzige Quelle, das Plugin braucht zur Laufzeit
keinen Dateizugriff und keine weitere Berechtigung, und der Eintrag ist rund 3 KB groß. Nach einer Änderung am
Eintrag neu bauen.

## Abweichungen von der Python-Fassung

- **Probe ohne Schnitt:** `classify_hole_groups` ordnet unklare Zylindergruppen mit einem kleinen Kugelschnitt
  knapp außerhalb der Wand ein. Eine `read`-Entry darf nicht schneiden; das Plugin fragt stattdessen
  `inspect.classify_points` (für read-Entries ohne Freigabe erlaubt), ob derselbe Punkt im Material liegt
  (`inside`: Bohrung, `outside`: Zapfen). Meldet der Host `on` oder scheitert die Abfrage, gilt wie in Python der
  geometrische Rückfall. Das ist in 0.50 häufig nötig, weil Zylinderflächen keine Normale tragen: Löcher in der
  Grundskizze eines einfachen Extrudes ordnet sonst nur der Rückfall ein, und der hält sie für Zapfen (Befund des
  Opus-Reviews in PR #241; Gegentests `tests/skizzenloch`, `tests/scheibe`, rot ohne Probe, grün mit).
- **Ohne Gewinde:** `model.threads` ist in SolidCraft 0.50 nicht als `read_only` markiert (`cmd/inspect.rs`, auch in
  der Nightly vom 2026-11-27) und wird einer `read`-Entry verweigert. Innengewinde helfen deshalb nicht bei der
  Einordnung; der Code dafür bleibt.
- Sacklöcher und Gewindezuordnung gehören zu anderen Regeln und fehlen.

Wörtlich portiert, aber von den Referenzteilen nicht abgedeckt: Senkungsausnahme (`:cbore:`), offene Rundung ohne
Wand in Reichweite, Rückfall über die Bounding Box (prüft wie Python nur x und y).

## Limits

Gemessen am 2026-11-28 (Linux, 0.50.0): Laufzeit 90–150 ms je Teil; das Gehäuse (35 Flächen, 72 Kanten) braucht
10–20 Mio. Fuel, 2 MiB Speicher reichen. Der Aufwand wächst mit Löcher × Flächen × Kanten; gesetzt sind
`fuel` 1e9, `memory_mib` 16, `deadline_ms` 10000.
