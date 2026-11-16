# SolidCraft-Plugins: RFC 0002 und was es für Mechvane heißt (2026-11-11)

Quelle: Issue #1221 (tangency-labs/solidcraft), RFC `docs/rfcs/0002-plugins.md` im PR #15110 (offen, Branch
`docs/rfc-0002-plugin-decisions`), Kommentare von bherbruck und raykholo vom 2026-11-11. Selbst gelesen, nicht über Gemini.

## Entschieden (laut RFC)

- API = Befehlsfläche des MCP-Servers, eine Oberfläche. Laufzeit WebAssembly (wasmtime), kein CPython.
- Kein Netz am Anfang; `net` im Manifest wird abgelehnt. Später nur signierte offizielle Plugins aus kuratiertem Index.
- Plugin-Oberfläche zeichnet die App aus deklarierten Eingabeschemas (Formularbau in #15100). Plugins liefern keinen UI-Code.
- Agent-first (6a): API-Referenz aus WIT und Befehlsschemas erzeugt, Plugin-Skill-Datei, `plugin test` headless mit JSON, typisierte Fehler.
- Host als app-neutrale Crates `craft-plugin` und `craft-plugin-wasm` (6b); jede Craft-App liefert ihren Befehlskatalog.
- Phasen: 1 Host + `execute` (raykholo, Draft #15112), 2 Import/Export + `plugin check/test`, 3 `FeatureKind::Plugin` mit
  Rückfall, 4 Installation + Add-on-Manager + Dialoge aus Schemas, 5 Web, 6 signierter Index. Erst Phase 1 läuft.

## Was für uns zählt

1. **Unsere Wünsche vom 2026-11-02/08 stehen nicht im RFC.** PR #4980 (Abschnitt 13a: typisierte `input` über
   `engine.describe`/`plugin.list`, gespeicherte Eingaben samt aufgelösten Bezügen, Ziele als Liste, Ergebnis in verwaltetem
   Timeline-Ordner) wurde geschlossen und ersetzt. Das RFC sagt nur „Eingaben sind Schemas“. Ziele als Liste, lesbare
   Instanzen und Joints kommen nicht vor (Suche nach joint/assembl/occurrence/target: keine Treffer).
2. **Unsere zwei Fragen sind offen:** darf ein Generator Joints anlegen, darf ein Ziel ein eingefügtes Teil sein
   (Features im Teil oder in der Baugruppe)? Ohne beides bleibt `bolted_connection` in der Mechvane-Schicht;
   `standard_part` passt schon (neues Bauteil, native Features, Rückfall `recorded_script`).
3. **Slicer-Workspace (Phase 2 unserer Roadmap):** Offene Frage 2 im RFC lässt Viewport-Overlays und Workspaces offen;
   Nutzung eines lokalen Dienstes (Companion) und `physical`-Bestätigung frühestens Phase 6. Slicer-Tab also nicht auf Plugins
   bauen. nomadsgalaxy hat sich zudem gegen Slicing in SolidCraft ausgesprochen (Übergabe bevorzugt).
4. **Python-Schicht:** Plugins sind WASM (Rust zuerst, TypeScript danach). Unsere Python-Fachfeatures lassen sich nicht
   übernehmen, nur neu schreiben. Das gehört in den Prüfpunkt Sprache (Rust/WASM) der Roadmap.
5. **Terminlage:** Phase 3/4 (Feature-Zeilen, Dialoge) ist nicht begonnen. Nichts davon trägt v0.1.

## Nächster Schritt (wartet auf Nutzer-OK, öffentlicher Kommentar)

Am Issue #1221 oder am RFC #15110 kurz nachfragen: (a) die Punkte aus 13a (Ziele als Liste, lesbare Eingaben/Instanzen) in
die Phase-3-Beschreibung übernehmen, (b) Joints durch Generatoren und Ziele in eingefügten Teilen als offene Fragen im RFC
Abschnitt 9 führen. Entwurf steht in der Übergabe-Antwort an den Nutzer.

## Nachtrag 2026-11-11 (Kommentar gepostet, Antwort)

Kommentar am PR #15110 gepostet (Nutzer-OK). raykholo antwortet am selben Tag: lesbare Eingaben und Ziele als Liste werden in
Phase 1 gebaut; gespeicherte Eingaben mit aufgelösten Bezügen, Joints durch Generatoren und Ziele in eingefügten Teilen kommen
mit Phase 3 oder in RFC-Abschnitt 9, die Verschraubung ist dort Abnahmebeispiel. Entscheidung `bolted_connection` als Plugin
bleibt bis dahin offen.
