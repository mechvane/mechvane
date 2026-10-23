# SolidCraft: Feature-Baum, Plugins, Zeichnungen, Governance

Stand 2026-10-19, SolidCraft `main` bei `9c954b4` (Release v0.16.2 ist älter).
Quelle: Sparse-Klon `/root/repos/_ext/solidcraft` (nur `docs/` und die Quellen
von `crates/ui-egui`, `crates/doc`, `crates/engine`, kein Build), GitHub-API.
Schritte 3 und 5 aus `docs/uebergabe.md`.

## Kurzfassung

- **Feature-Baum:** SolidCraft hat bereits einen senkrechten Feature-Verlauf
  links über dem Browser, mit benannten Zeilen, Ordnern, Mehrfachauswahl und
  einem **Rollback-Balken, an dem neue Features eingefügt werden**. Das ist im
  Kern das Inventor-Modell mit „Ende des Teils“. Es ist eine Einstellung
  (`timeline_left`), Standard ist die Fusion-Leiste unten. **Optisch** also
  nahe an Inventor, **im Datenmodell nicht** (siehe Nachtrag unten): Der
  Nutzer will den Baum auch dort, das erfordert Änderungen im Kern-Crate
  `doc`.
- **Plugins:** Nur ein Entwurf (`docs/plugins.md`, Issue #1221 vom
  2026-10-14, offen, Label `question`, `priority:P3`). Im Code gibt es noch
  keinen Plugin-Host (kein WIT, kein wasmtime). Auch der Entwurf sieht **keine
  eigene UI für Plugins** vor, ein Slicer-Tab ginge damit nicht.
- **Zeichnungen:** M11 „2D drawings“ ist zurückgestellt. Es gibt einen Export
  der aktuellen Ansicht als DXF (verdeckte Kanten weggelassen oder
  gestrichelt) und den ersten Baustein des Zeichnungsplans (#860, W01a:
  Datensätze für Schnittgeometrie, ohne Erzeuger). Blätter, Bemaßung,
  Stückliste und Normen fehlen ganz.
- **Governance:** Sehr aktiv, schnelle Reaktion (erster Kommentar auf Issues im
  Median nach ~20 min, Merge im Median 7 h nach PR-Eröffnung). Strenge Regeln:
  **kein GPL/LGPL/AGPL-Code, nicht einmal lesen**, und keine Automatisierung
  kommerzieller CAD-Programme für Beiträge.

## Feature-Baum

Was es gibt (`crates/ui-egui/src/timeline_left.rs`, 1455 Zeilen,
`browser.rs`, `prefs.rs`):

- `preferences.timeline_left`: „Put the feature history above the parts
  browser in the left sidebar instead of along the bottom of the viewport.“
  Die Höhe zwischen Verlauf und Browser lässt sich verschieben, der Browser
  einklappen.
- Der Verlauf zeigt `FEATURE HISTORY` mit Icon und Namen je Feature,
  verschachtelte Ordner (`timeline.group`), Ziehen und Ablegen mit
  Abhängigkeitsprüfung, Unterdrücken, Umbenennen, Löschen samt abhängiger
  Features, Kopieren und Einfügen.
- **Rollback-Balken** als waagrechter Strich zwischen den Zeilen: „drag to
  roll the model back; new features are inserted here“. Dahinter liegen
  `timeline.rollback` und `timeline.roll_to`, die auch per MCP gehen. Danach
  liegende Features erscheinen ausgegraut.
- Skizzen mit Mustern lassen sich aufklappen
  (`sketch_pattern_tree`), Features bieten „Edit Profile Sketch“ an.

Was zum Inventor-Baum fehlt (Abgleich mit ROADMAP-Grundsatz 5, nicht im
laufenden Programm angesehen, das ist Schritt 4):

- Verbrauchte Skizzen hängen in Inventor **unter** ihrem Feature. In
  SolidCraft ist die Skizze eine eigene Zeile, das Feature verweist nur auf sie
  (bisher nur am Code gesehen).
- Ursprungsebenen, Körper und Feature-Verlauf liegen in Inventor in **einem**
  Baum. In SolidCraft sind es zwei Bereiche (Verlauf oben, Browser mit
  Komponenten, Körpern und Skizzen unten).
- Standard ist die Leiste unten; inventa würde `timeline_left` als Vorgabe
  setzen.

Erste Bewertung (überholt): Optisch ließe sich der Inventor-Baum in `ui-egui`
nachbauen und upstream als Option vorschlagen (SolidCraft nimmt UI-Optionen
an, siehe M6: „optional compact named left feature history“).

### Nachtrag: Inventor-Baum im Datenmodell (2026-10-19)

Der Nutzer will den Baum **nicht nur optisch**, und Abhängigkeiten sollen an
den Bauteilen hängen statt in einem eigenen Ordner. Abgleich mit dem Code
(`crates/doc/src/document.rs`, `joints.rs`, `ui-egui/src/browser.rs`):

| Inventor | SolidCraft heute |
|---|---|
| Skizze gehört dem Feature, das sie verbraucht | `FeatureKind::Sketch` ist ein eigener Eintrag in `features`, `Extrude { sketch: SketchId, … }` zeigt per Id darauf |
| Jedes Bauteil hat seinen eigenen Verlauf und eigenes Bauteilende | **Eine** Liste `Document.features` mit **einem** `marker` fürs ganze Design, die Komponente steht nur als Feld `Feature.component` |
| Bauteile als eigene Dateien, Baugruppe verweist darauf | Alles in einem Design. „Insert Design“ (`DesignLink`) holt nur die Körper als Import-Feature, ohne Bearbeiten an Ort und Stelle |
| Abhängigkeiten unter den beteiligten Bauteilen | `assembly.joints` (je Gelenk `a`/`b` mit Occurrence), im Browser ein eigener Ordner „Joints“ an der Wurzel (`dialogs_assembly::browser_joints`), zusätzlich im Verlauf |

Folgen:

- Die Gelenke unter den Bauteilen anzuzeigen ist reine UI (die Zuordnung
  steckt in `a`/`b`). Das wäre upstream als Option denkbar.
- Skizzen als Kinder ihres Features und ein Verlauf je Bauteil ändern das
  **Dateiformat und die Auswertung** in `doc`. SolidCraft folgt bewusst Fusion,
  ein solcher Umbau wird upstream kaum angenommen. Das spricht für B (Fork) oder
  eine eigene inventa-Dokumentschicht über den SolidCraft-Crates (Kernel,
  Skizze, Engine-Befehle wiederverwenden, eigenes Dokumentmodell). Für die
  ADR 0001 ist das jetzt die Kernfrage.
- **Entscheidung des Nutzers (2026-10-19): getrennte Dateien** für Bauteile
  und Baugruppen. SolidCraft kennt das nur als „Insert Design“ (Körper als
  Import, ohne Bearbeiten an Ort und Stelle). Ein Mehrdatei-Modell mit
  Verweisen, Neuladen und Bearbeiten im Kontext der Baugruppe ist damit ein
  eigener, großer Baustein der inventa-Dokumentschicht.

## Plugin-System (#1221, `docs/plugins.md`)

Entwurf:

- WebAssembly-Komponenten mit WIT-Schnittstelle (`solidcraft:plugin@1.0.0`),
  in einer Sandbox (Rechte im Manifest, Fuel- und Speicherlimits). Auf dem
  Desktop über wasmtime, im Web über einen Broker.
- Plugins ändern das Modell nur über die normalen Befehle
  (`run(command, args)`, dieselbe JSON-Schnittstelle wie MCP), also mit Undo
  und im Journal.
- Stufe 1: einmalige Plugins (`execute`). Stufe 2: parametrische Plugins als
  eigene Feature-Zeile (`FeatureKind::Plugin`) mit `evaluate` beim
  Neuberechnen, Verhalten bei fehlendem Plugin (gespeichertes Netz,
  gespeichertes Befehlsskript, unterdrücken oder Fehler).
- UI: Plugins dürfen nur Label, Tooltip und ein Icon aus der Liste der App
  setzen. „No per-plugin egui in milestone 2.“ Später vielleicht ein
  Parameterschema, aus dem die App Eingabefelder baut.

Stand:

- Im Code fehlt jede Spur davon (keine Datei mit `plugin`, `wit` oder `wasm`
  unter `crates/`).
- Issue #1221 hat 15 Kommentare. Diskutiert werden noch Grundsätze (Rhai statt
  WASM, Netzwerkzugriff über CollabCraft), ein Dritter baut bereits ein
  Möbel-Plugin („KorpusPRO“).

Folgen für inventa:

- Ein **Slicer-Tab mit eigener Oberfläche ist über das geplante
  Plugin-System nicht möglich.** Die Optionen sind: (a) upstream eine
  UI-Erweiterung vorschlagen (eigener Arbeitsbereich oder Panel für Plugins),
  (b) der Slicer läuft in einer inventa-eigenen Hülle neben SolidCraft, die
  SolidCraft als Bibliothek oder per Steuerprotokoll einbettet, (c) Fork von
  `ui-egui`.
- Die Engine soll als getrennter Prozess laufen (ROADMAP Phase 2). Das passt
  auch zur Regel „kein GPL/LGPL/AGPL-Code“: CuraEngine (AGPL) und libslic3r
  (AGPL) könnten **nie upstream** in SolidCraft landen, nur in inventa und nur
  über eine Prozessgrenze.
- Bis Plugins kommen, ist der Weg für eigene Werkzeuge: Befehlsskripte über
  MCP oder das Steuerprotokoll (`--control`), wie bei den Referenzteilen.

## Zeichnungen (`docs/drawing-foundations.md`, `docs/drawing-geometry.md`)

- SolidCraft-ROADMAP M11 „2D drawings“: **deferred**.
- Vorhanden: File → Export Current View as DXF. Gezeigte Körper aus der
  aktuellen Kamera als 2D-Zeichnung in mm, verdeckte Kanten weggelassen oder
  gestrichelt, Kurven angenähert (`docs/view-dxf.md`). Keine Blätter, keine
  Beschriftung, keine exakten projizierten Kurven.
- Zeichnungsplan RFC #860 mit 48 Arbeitspaketen (W00–W47). Umgesetzt ist
  W01a: neutrale Datensätze für Schnittgeometrie in einer Ebene, nur mit
  Strukturprüfung. Noch kein Schnitt eines Körpers, keine Sichtbarkeit, kein
  `drawing.view`, kein Export, kein Zeichnungsdokument. Offen ist ein
  Vorschlag `inspect.section_curves` (PR #2068).
- Für inventa Phase 3: Hier gibt es nichts, auf das sich aufbauen ließe, außer
  dem Ansichts-DXF. Die Zeichnungsableitung wäre die größte Eigenleistung.
  Mitarbeit an #860 wäre der Weg, bei dem sie upstream landet (dann
  MIT/Apache und ohne Blick in TechDraw/FreeCAD-Code).

## Governance

| Punkt | Befund |
|---|---|
| Lizenz | MIT OR Apache-2.0, Beiträge ebenso |
| Aktivität | 7 172 Sterne, 1 428 offene Issues, letzter Push 2026-10-19 |
| Reaktionszeit | Erster Kommentar auf Issues im Median ~20 min (23 der letzten 60 kommentiert, viel davon Bots/Claims) |
| Merge-Zeit | Median 7 h vom PR bis zum Merge (letzte 60), 19 Autoren, 26 davon vom Hauptautor `bherbruck` |
| Ablauf | Issue zuerst, dann Claim per Draft-PR (`claim: #N`) oder `/claim`. Der niedrigste offene PR gewinnt, ohne Push 72 h bzw. 14 Tage verfällt der Claim. `cargo xtask ci` vor dem Push, volle CI erst nach Review (`approved-for-ci`) |
| Harte Regeln | Kein GPL/LGPL/AGPL-Code, auch nicht lesen (OCCT, FreeCAD, planegcs, SolveSpace, CadQuery). Kein Steuern oder Auslesen kommerzieller CAD-Programme für Referenzen. Eigene Befehls-IDs, keine fremden Icons oder Texte |
| Agenten | `AGENTS.md` und `CLAUDE.md` im Repo, Beiträge von Agenten sind offenbar üblich |

Folgen:

- Beiträge upstream sind realistisch und werden schnell bearbeitet.
- **Fusion-Vergleiche** (win-cad) sind für inventa-eigene Tests in Ordnung,
  dürfen aber nicht als Referenz in SolidCraft-Beiträge einfließen.
- Die FreeCAD-Hybrid-Idee aus der Gemini-Gegenprobe verträgt sich nicht mit
  Upstream-Beiträgen: Wer FreeCAD-Code liest, sollte für SolidCraft keinen Code
  zum selben Thema schreiben.
- Kollisions-Bug: Eine Suche nach `interference`/`contact.check` findet keine
  Dublette (verwandt: #3249, Mesh-Körper bei `inspect.interference`). Er ist
  meldefertig, **wartet auf das OK des Nutzers**.
