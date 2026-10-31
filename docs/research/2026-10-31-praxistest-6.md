# Praxistest 6: Halteteil headless (2026-10-31)

v0.1 Schritt 4, Tagespaket 2026-10-31. Ein Alu-Winkel (Fuß 50 × 30, Steg 50 × 40, Dicke als Parameter `dicke`)
wird mit zwei M5 auf eine Stahl-Grundplatte geschraubt. Der ganze Ablauf läuft über die Mechvane-Werkzeugfunktionen
(`mechvane.server`, dieselben Funktionen wie die MCP-Tools; der laufende MCP-Server hatte noch einen alten Stand).
Skript: Scratchpad `pt6b.py`, nicht versioniert. Ablauf: `new_part` → `run` (Parameter, Skizzen, Extrusionen) →
`parameters.change` → `new_assembly`/`insert_part` → `preview_bolted_connection`/`bolted_connection` (M5, Muster 2 × 1)
→ `check_joints` → `check_design` mit und ohne Werkstoff, `remember=True` → Prüfseite (`tools/ui_smoke.py`
und ein Browsertest der Auswahlfelder).

## Ergebnis

- Gespeicherter Werkstoff (neu heute): `check_design(profile="cnc_alu", material="alu_wrought", remember=True)`
  schreibt in die Datei. Der nächste Aufruf ohne Angabe nimmt beides (`material_source: saved`), die Prüfseite
  zeigt es, eine Änderung im Browser landet in der Datei, ein frischer Browser ohne `localStorage` zeigt sie.
- Messen auf der Prüfseite: Punkt, Schnitt, Esc, Kante 40,00 mm, keine Seitenfehler.
- Verschraubung: 2 × M5 ISO 4762 mit Scheibe und Mutter, Klemmlänge richtig, `check_joints` alles ok.

## Befunde

1. **Behoben:** Die Flachsenkung einer Durchgangsbohrung (wie `bolted_connection` sie bohrt) galt als Sackloch,
   weil `F5:cbore:base` als Bohrungsgrund zählte. Dazu prüfte die Randabstandsregel die Senkung Ø10 mit 1,5 × 10 mm
   (Fehlalarm bei 12 mm Randabstand). Jetzt gilt der Randabstand der Bohrung, für die Senkung bleibt die
   Wandstärkenprüfung. Test in `check.py`, auf dem alten Code rot.
2. **Behoben:** `check_design` meldete ein Bauteil ohne Körper als OK, jetzt als Warnung.
3. **Offen (ROADMAP):** `bolted_connection` bohrt mit fester Tiefe (`depth: "8"`, die Dicke beim Bohren). Mit
   `dicke` = 12 mm werden beide Löcher zu Sacklöchern. `check_design` warnt, aber die Bohrung sollte „durch alle“
   gehen oder an der Dicke hängen.
4. **Offen (ROADMAP):** Überlappen die Teile (mein Modellfehler im ersten Lauf: der Steg hing durch die
   Grundplatte), bricht `bolted_connection` mit der SolidCraft-Meldung „lumps: shell boundaries intersect or touch;
   cavity ownership is ambiguous“ ab. Besser wäre eine Kollisionsprüfung vorher mit klarer Meldung.
5. **Stolperstein für Agenten:** Auf der XZ-Ebene zeigt die Skizzen-y-Achse nach −Z (wie in Fusion). Ein
   Rechteck bis y = 40 liegt unter dem Fuß. Gehört in die Skill-Hinweise.
6. **Stolperstein:** Punkte in Skizzenbefehlen nehmen keine Parameter (`"p1": ["breite", 30]` bricht ab). Parameter
   wirken über `sketch.dimension` oder Feature-Werte. Ein ungenutzter Parameter (`breite`) bleibt ohne Hinweis.
7. **Upstream-Kandidat:** `solid.hole` ignoriert unbekannte Parameter still (ein verschachteltes
   `"hole": {"type": "counterbore", …}` ergab eine Bohrung ohne Senkung). Im Test aufgefallen, nicht gemeldet.

Kosten: ~1 % (inkl. Fehlersuche Befund 1).
