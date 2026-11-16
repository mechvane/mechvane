# Recherche Phase 3: Zeichnungsableitung mit CADCraft 0.8.0

- **Datum:** 2026-11-09
- **Autor:** Gemini 3.8 Flash (Issue #52)
- **Status:** Erfolgreich verifiziert mit Erkundungsskript `docs/research/2026-11-09-cadcraft-zeichnung/ableitung.py` und gegen den Quelltext in `/root/repos/artcraft/cadcraft`
- **Geprüfte Binärdateien:**
  - `cadcraft-cli 0.8.0` (`~/.local/opt/cadcraft-0.8.0-linux-x86_64/bin/cadcraft-cli`)
  - `solidcraft-cli` (`/root/.local/bin/solidcraft-cli`)

---

## 1. Einleitung und Zielsetzung

In Phase 3 der Mechvane-Roadmap (**Manufacturing drawings / Fertigungszeichnungen**) soll der Agent in die Lage versetzt werden, aus einem parametrischen 3D-Modell normgerechte 2D-Fertigungszeichnungen nach ISO/DIN mit Ansichten, Schnitten, Bemaßung, Toleranzen, Passungen, Oberflächenangaben, Schriftfeld und Stückliste abzuleiten und als PDF/DXF zu exportieren.

CADCraft ist die 2D-Schwester von SolidCraft aus dem ArtCraft-Ökosystem (Repository `storytold/cadcraft`). Beide Projekte basieren auf Rust, teilen dieselbe UI- und Grafik-Infrastruktur (`egui 0.36`, `wgpu 30`) und folgen dem Paradigma: *Alles ist ein Befehl*.

Ziel dieser Recherche ist es, den aktuellen Entwicklungsstand von CADCraft v0.8.0 systematisch für die Fertigungszeichnungsableitung zu untersuchen:
1. Welche Befehle und MCP-Werkzeuge stellt `cadcraft-cli` bereit?
2. Wie verhält sich CADCraft bei den 8 Kernanforderungen von Phase 3?
3. Wie funktioniert das Zusammenspiel zwischen SolidCraft (3D-Geometrie / Ansichtsexport) und CADCraft (2D-Komposition / Bemaßung / Plot)?
4. Welche Lücken bestehen gegenüber der ROADMAP Phase 3 und wie sehen die ersten Schritte aus?

---

## 2. CLI- und MCP-Schnittstellen von CADCraft 0.8.0

### 2.1 Befehlszeilenschnittstelle (`cadcraft-cli --help`)
`cadcraft-cli` (v0.8.0) stellt folgende Modi bereit:

```
usage:
  cadcraft-cli info FILE.dxf
  cadcraft-cli convert IN.dxf OUT.(dxf|dwg|svg|png|pdf) [FRAMING]
  cadcraft-cli run [FILE | --sample | --metric] [--script TEXT] [--script-file F.scr] [--cmd 'id {json}']... [--save OUT.dxf] [--export OUT.(png|svg|pdf)] [FRAMING]
  cadcraft-cli commands [FILTER]
  cadcraft-cli mcp [--connect HOST:PORT [--lazy] [--launch]]
  cadcraft-cli perf [N | FILE]
  cadcraft-cli sample (bracket|floorplan) OUT.(dxf|dwg|svg|png)
  cadcraft-cli --version
```

- **`commands [FILTER]`**: Gibt den gesamten Befehlskatalog im JSON-Format aus (insgesamt **426 registrierte Befehle**).
- **`run --cmd 'id {json}'`**: Führt Befehle stapelweise und headless ohne GUI aus.
- **`convert` / `--export`**: Ermöglicht den direkten Export nach DXF, DWG, SVG, PNG und PDF inklusive Framing-Optionen (`--window`, `--view extents`, `--view current`).

### 2.2 Der MCP-Server (`cadcraft-cli mcp`)
CADCraft implementiert das Model Context Protocol (MCP) über Stdio (oder TCP-Bridge zur laufenden GUI-Applikation). Der Server registriert über `tools/list` **12 Kernwerkzeuge**:

| MCP-Werkzeug | Parameter | Kurzbeschreibung (aus Schema / `crates/mcp/src/tools.rs`) |
| :--- | :--- | :--- |
| `command_line` | `{text}` | Interaktive AutoCAD-Prompt-Eingabe (z. B. `line 0,0 @10,0`, `circle 5,2 1`, Leerzeichen = Enter). |
| `script` | `{text}` | Führt mehrzeilige AutoCAD-kompatible `.scr`-Skripte aus. |
| `execute` | `{command, params}` | Führt jeden der 426 Befehle strukturiert mit JSON-Parametern aus (keine GUI-Dialoge). |
| `list_commands` | `{filter?}` | Durchsucht den Befehlskatalog nach ID, Label oder Alias. |
| `inspect_drawing` | `{entities?, limit?}` | Liefert Zusammenfassung: Objektanzahlen, Extents, Layer, Stile, Blöcke, Layouts, Selection, Undo-Historie. |
| `query_entities` | `{type?, layer?, window?, crossing?, limit?, offset?}` | Filtert Entitäten nach Typ, Layer oder Koordinatenfenster. |
| `render` | `{width?, height?, fit?, window?, background?, plot_style?}` | Rendert die aktive Zeichnung oder einen Fensterausschnitt direkt als PNG-Bildblock. |
| `find_text` | `{contains?, layer?, window?, limit?, offset?}` | Durchsucht lesbare Texte (TEXT, MTEXT, Attribute, Multileader) ohne Geometrieübertragung. |
| `new_drawing` | `{metric?}` | Erstellt eine neue Zeichnung (standardmäßig imperial, mit `metric: true` metrisch mit `ISO-25`). |
| `open` | `{path}` | Öffnet eine bestehende DXF-Zeichnung. |
| `save` | `{path?}` | Speichert als DXF/DWG; Pfade auf `.svg`, `.png` oder `.pdf` lösen einen Export aus. |
| `cancel` | `{}` | Entspricht der Escape-Taste (bricht laufende Aktionen ab). |

Zusätzlich stellt CADCraft zwei MCP-Ressourcen bereit: `cadcraft://drawing` (aktuelle Inspektionsdaten) und `cadcraft://commands` (Befehlskatalog).

---

## 3. Fähigkeitsmatrix: CADCraft 0.8.0 für Fertigungszeichnungen

Die folgende Tabelle fasst die Untersuchung der 8 Kernfunktionen für Fertigungszeichnungen zusammen:

| Nr. | Fähigkeit | Status | Beleg (Befehl, Quellcode-Stelle oder Ausgabe) | Bewertung für Mechvane Phase 3 |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **3D-Ansichten-Import** (Projektion, verdeckte Kanten, Schnitt, Detail) | **Fehlt in CADCraft** *(vorhanden via SolidCraft)* | `ROADMAP.md:78` („3D modelling and rendering 2 %“); Befehle `solview`, `viewbase`, `sectionview` existieren nicht in CADCraft. In SolidCraft: `file.export_view_dxf` (`crates/engine/src/cmd/view_dxf.rs:24`). | CADCraft ist ein reines 2D-CAD-System ohne 3D-B-Rep-Kernel. Ansichten müssen von SolidCraft/Mechvane als DXF projiziert und in CADCraft via `import` platziert werden. |
| **2** | **Bemaßung** (Linear, Aligned, Radius, Diameter, Angular, Ordinate, ISO-25) | **Vorhanden** | Befehle: `dimlinear`, `dimaligned`, `dimradius`, `dimdiameter`, `dimangular`, `dimordinate`, `dimcontinue`, `dimbaseline`, `qdim`, `dimstyle.current`. Quellcode: `crates/doc/src/tables.rs:600` (`DimStyle::iso25()`). | Vollständig und normgerecht vorhanden. Mit `new_drawing {metric: true}` ist `ISO-25` mit 2,5 mm Schrifthöhe und 2 Nachkommastellen vorkonfiguriert. |
| **3** | **Toleranzen & Passungen** (Abmaße, Grenzmaße, Form-/Lagetoleranzen, ISO 286) | **Teilweise** | **Vorhanden:** Befehl `tolerance` (`crates/engine/src/cmd/dim/tolerance.rs`), `dimoverride` mit `tolerance: true`, `tolPlus`, `tolMinus` (`crates/render/src/dim/text.rs:23`). **Fehlt:** ISO 286 Passungstabellen. | Form- und Lagetoleranzrahmen (ISO 1101 / ASME Y14.5) sowie numerische Abmaße/Grenzmaße sind voll nutzbar. ISO 286 Passungsklassen (z. B. H7, g6) liefert Mechvanes `iso286.py`. |
| **4** | **Gewindedarstellung** (DIN ISO 6410 / ISO 128-36) | **Fehlt** | Keine Treffer für Gewindebefehle (`crates/render`, `crates/doc`). Treffer für `thread` betreffen ausschließlich OS-Threads (`std::thread`). | CADCraft besitzt kein Konzept für Gewindelinien (3/4-Kreis bzw. 0,25 mm Volllinie). Gewindedarstellung muss aus den 3D-Bohrungsmetadaten als 2D-Geometrie erzeugt werden. |
| **5** | **Oberflächenzeichen** (ISO 1302 / ISO 21920) | **Fehlt** | Keine Befehle für Oberflächenbeschaffenheit (`roughness`, `finish`, `amsurf` fehlen). | Oberflächenangaben (z. B. Ra 3,2, Rz 16) existieren nicht als CADCraft-Primitive. Sie können in 2D nur als Block-Definitionen mit Attributen oder `mleader` abgebildet werden. |
| **6** | **Schriftfeld** (DIN EN ISO 7200) | **Vorhanden** (über Blöcke / Tabellen) | Befehle: `table`, `table.set`, `table.cellstyle` (`crates/engine/src/cmd/table.rs`) sowie `block`, `attdef`, `insert`. | Kein dedizierter „Schriftfeld-Assistent“, aber die Standard-Mechanismen (AutoCAD-kompatible Tabellen oder Blöcke mit editierbaren Attributen) funktionieren einwandfrei. |
| **7** | **Stückliste & Balloons** (BOM, Tabellen, Formeln, Positionsnummern) | **Teilweise** | **Vorhanden:** `table`, `table.formula`, `counttable`, `dataextraction`, `mleader` (mit Block-Inhalt). **Fehlt:** Live-Kopplung an 3D-Baugruppen. | Formatierte 2D-Tabellen mit Formeln (`sum`, `average`) und Blasen-Multileader sind vorhanden. Die Kopplung an 3D-Baugruppenkomponenten muss Mechvane steuern. |
| **8** | **PDF- und DXF-Export** | **Vorhanden** | Befehle: `exportpdf`, `plot`, `convert`, `save` (`crates/engine/src/cmd/file.rs:288`, `crates/io/src/plot/pdf.rs`). | Exzellent implementiert. Headless-Export nach PDF (inkl. Liniengewichten), PNG, SVG und DXF (R2000 bis R2018) funktioniert deterministisch. |

---

## 4. Detaillierte Analyse der einzelnen Fähigkeiten

### 4.1 3D-Ansichten-Import aus SolidCraft
In CADCraft gibt es keinerlei 3D-Geometrie und keine Projektionsfunktionen:
- Das Repository stellt fest: `ROADMAP.md` beziffert 3D-Modellierung und Rendering auf **2 %** (geschätzter Restaufwand 300–450 h für ein primitives 3D-Drahtgittermodell).
- Die Befehle `solview`, `soldraw`, `viewbase`, `flatshot` oder `sectionview` sind nicht vorhanden.
- **Lösung über SolidCraft:** SolidCraft verfügt über den Befehl `file.export_view_dxf` (`crates/engine/src/cmd/view_dxf.rs:24`). Übergeben wird eine Kamera (`camera: Camera`), eine Option für verdeckte Kanten (`hidden: "dashed"|"omit"`) und eine Sehnentoleranz (`tolerance: 0.01`).
- **Aktuelle Einschränkung bei SolidCraft:** `file.export_view_dxf` trianguliert alle Körper und projiziert sichtbare/verdeckte Kanten als diskrete `LINE`- und `LWPOLYLINE`-Elemente (z. B. 464 Linien und 74 Polylinien für den Flansch). Echte Kurven (Kreise, Ellipsen, Splines) fehlen upstream noch (SolidCraft Zeichnungsplan #860).

### 4.2 Bemaßung & Bemaßungsstile
CADCraft besitzt ein vollständiges, ausgereiftes Bemaßungssystem:
- Unterstützte Bemaßungsarten: Linear (`dimlinear`), ausgerichtet (`dimaligned`), Radius (`dimradius`), Durchmesser (`dimdiameter`), Winkel (`dimangular`), Bogenlänge (`dimarc`), Koordinatenbemaßung (`dimordinate`), Kettenbemaßung (`dimcontinue`) und Bezugskantenbemaßung (`dimbaseline`).
- Schnellbemaßung: `qdim` erzeugt Ketten- oder Bezugskantenmaße über eine Liste von Objekthandles.
- **Normstile:** CADCraft definiert in `crates/doc/src/tables.rs:600` den Stil `ISO-25`:
  ```rust
  pub fn iso25() -> Self {
      DimStyle {
          name: "ISO-25".into(),
          arrow_size: 2.5,
          ext_offset: 0.625,
          ext_extend: 1.25,
          text_height: 2.5,
          text_gap: 0.625,
          decimals: 2,
          text_above: 1,
          center_mark: 2.5,
          zero_suppression: 8,
          baseline_spacing: 3.75,
          force_line_inside: true,
          ..Default::default()
      }
  }
  ```
- Über `dimstyle.current {"name": "ISO-25"}` wird dieser Stil für alle nachfolgenden Maße aktiv. Textübersteuerungen (z. B. `<> H7` oder Prüfmaße via `diminspect`) werden vollständig unterstützt.

### 4.3 Toleranzen und Passungen
Hier zeigt sich eine klare Zweiteilung:
- **Form- und Lagetoleranzen (ISO 1101 / ASME Y14.5):** Der Befehl `tolerance` (Alias `tol`) erzeugt normgerechte Toleranzrahmen mit Symbolen (`position`, `flatness`, `concentricity`, `parallelism`, `perpendicularity` etc.), Toleranzwerten mit Materialmodifikatoren (`%%c0.1(M)`) und bis zu drei Bezügen (`datums: ["A", "B", "C"]`).
- **Grenzabmaße (Toleranzen an Maßen):** Unterstützt über `DimStyle`-Variablen (`DIMTOL`, `DIMTP`, `DIMTM`, `DIMTDEC`, `DIMTOLJ`) oder direkt über `dimoverride`:
  ```json
  {"command": "dimoverride", "params": {"handles": ["101"], "tolerance": true, "tolPlus": 0.1, "tolMinus": 0.05}}
  ```
  Im Rendering (`crates/render/src/dim/text.rs:37`) werden diese als sauber gestapelte MTEXT-Brüche (`{\H0.7;\S+0.10^-0.05;}`) dargestellt.
- **Passungsklassen nach ISO 286:** Fehlen in CADCraft vollständig (keine Tabellen für H7, g6, h6 etc.). Da Mechvane mit `mechvane/iso286.py` (`iso286.deviations`, `iso286.fit`) bereits ein geprüftes Modul besitzt, kann Mechvane die Passungstexte und Abmaße vorab berechnen und als Maßtext an CADCraft übergeben.

### 4.4 Gewinde und Oberflächenangaben
- **Gewindedarstellung:** CADCraft hat keinerlei Spezialbefehle für Gewinde nach DIN ISO 6410. Um Gewinde darzustellen, müssen bei der Zeichnungsableitung die Gewindegrund- bzw. Gewindekerndurchmesser als dünne 2D-Volllinien (0,25 mm) bzw. 270°-Bögen generiert werden.
- **Oberflächenbeschaffenheit:** Es gibt keine Symbole für Oberflächenrauheit nach DIN EN ISO 1302 / ISO 21920. In 2D-CAD werden diese klassisch als Blöcke mit Attributen (Grundsymbol, Ra-Wert, Bearbeitungszugabe) eingefügt.

### 4.5 Schriftfeld und Stückliste
- **Schriftfeld (DIN EN ISO 7200):** Kann entweder als AutoCAD-Block mit Attributen (`ATTDEF`) oder als formatierte Tabelle (`table`) angelegt werden. Im Erkundungsskript wurde das Schriftfeld über eine Tabelle mit 4 Zeilen und 2 Spalten realisiert und über `table.set` mit Benennung, Werkstoff, Allgemeintoleranz und Maßstab befüllt.
- **Stückliste (BOM) & Positionsnummern:** CADCraft bringt mit `table` (inkl. Formeln `=SUM(A1:A5)`), `counttable` (automatisches Zählen von Blockreferenzen) und `dataextraction` mächtige 2D-Tabellenwerkzeuge mit. Positionsnummern (Balloons) lassen sich über `mleader` mit Kreis- oder Sechseck-Blockinhalt abbilden. Die Verknüpfung zur 3D-Baugruppe muss jedoch von Mechvane bereitgestellt werden.

### 4.6 PDF- und DXF-Export
CADCraft verfügt über eine eigenständige Plot- und Render-Engine (`crates/io/src/plot/`):
- `exportpdf` und `plot` unterstützen Papierformate (A4, A3, A2, A1, A0), Ausrichtung (`landscape`/`portrait`), Liniengewichte (`lineweights: true`) und Plot-Stil-Tabellen (`.ctb` / `.stb`).
- Der MCP-Befehl `save {"path": "out.pdf"}` exportiert automatisch als PDF.
- Der direkte Export nach PNG (`save {"path": "out.png"}` oder MCP-Tool `render`) liefert hochauflösende Rasterbilder (2400 × 1600 px) für visuelle Prüfungen durch Agenten.

---

## 5. Das Erkundungsskript (`docs/research/2026-11-09-cadcraft-zeichnung/`)

Unter `docs/research/2026-11-09-cadcraft-zeichnung/ableitung.py` wurde ein vollständiges, automatisiertes Skript entwickelt, das den gesamten Ablauf demonstriert:

### 5.1 Ablauf
1. **SolidCraft-Export:**
   - Liest das parametrische Referenzteil `tests/reference/flansch.build.json` (Flansch $60 \times 60 \times 8\,\text{mm}$, 4 Bohrungen $\varnothing 6{,}6\,\text{mm}$ auf Lochkreis $45\,\text{mm}$, $1\,\text{mm}$ Fase).
   - Platziert Kameras mit großem Abstand ($100\,000\,\text{mm}$) und minimalem Öffnungswinkel ($\text{fov} = 0{,}0005$), um eine telezentrische Parallelprojektion zu erzielen:
     - Draufsicht: $\text{pitch} = \pi/2$, $\text{yaw} = 0$
     - Vorderansicht: $\text{pitch} = 0$, $\text{yaw} = 0$
     - Seitenansicht: $\text{pitch} = 0$, $\text{yaw} = -\pi/2$
   - Ruft `solidcraft-cli run` auf und erzeugt `flansch_top.dxf`, `flansch_front.dxf` und `flansch_side.dxf` mit verdeckten Kanten (`hidden: "dashed"`).
2. **CADCraft MCP-Steuerung:**
   - Startet `cadcraft-cli mcp` als Subprozess über Stdio.
   - Initialisiert eine neue metrische Zeichnung (`new_drawing {metric: true}`) und aktiviert den Stil `ISO-25`.
   - Importiert die drei Ansichten nach Projektionsmethode 1 (ISO 128 / DIN 6):
     - Vorderansicht bei $(100, 160)$
     - Draufsicht bei $(100, 70)$ (vertikal unter der Vorderansicht ausgerichtet)
     - Seitenansicht bei $(190, 160)$ (horizontal rechts der Vorderansicht ausgerichtet)
3. **Bemaßung und Anmerkungen:**
   - Vorderansicht: Breite $60\,\text{mm}$ und Plattendicke $8\,\text{mm}$.
   - Draufsicht: Außenmaße $60 \times 60\,\text{mm}$ sowie horizontaler Lochabstand $31{,}82\,\text{mm}$.
   - Form- und Lagetoleranz: Ebenheitstoleranz $0{,}05\,\text{mm}$ via `tolerance`.
   - Schriftfeld: DIN EN ISO 7200 Tabelle mit Benennung, Werkstoff, Allgemeintoleranz und Maßstab.
4. **Ergebnisse & Dateigrößen:**
   - `flansch_zeichnung.dxf`: $199\,899\,\text{Bytes}$ (AutoCAD 2018 DXF, 636 Entitäten, sauber strukturiert)
   - `flansch_zeichnung.pdf`: $52\,260\,\text{Bytes}$ (vektorbasiertes PDF mit ISO-25 Bemaßung und Tabellen)
   - `flansch_zeichnung.png`: $173\,091\,\text{Bytes}$ ($2400 \times 1600\,\text{px}$, 8-Bit RGBA)

Das Skript lief ohne manuelle Eingriffe durch und belegt, dass der Brückenschlag zwischen SolidCraft und CADCraft 0.8.0 bereits heute technisch funktioniert.

---

## 6. Lückenabgleich gegen ROADMAP Phase 3

In `roadmap.json` (Abschnitt *„Manufacturing drawings“*) und `docs/research/2026-11-01-roadmap-ergaenzungen-harness-ux.md` sind folgende Kernziele für Phase 3 definiert:

| Roadmap-Ziel Phase 3 | Stand in CADCraft 0.8.0 | Lücke / Wer muss es lösen? |
| :--- | :--- | :--- |
| **Views** (*Base, projected, section and detail views with hidden lines*) | **0 % in CADCraft** (kann nur 2D DXF importieren). SolidCraft kann einfache Parallelansichten mit HLR via `file.export_view_dxf`. | **Lücke SolidCraft/Mechvane:** Schnittansichten (Schnittverlauf A-A mit Schraffur), Detailansichten mit Maßstabsfaktor und exakte Kurvenprojektion (Kreise statt Sehnenketten) müssen upstream in SolidCraft (Plan #860) oder als Mechvane-Schnittgenerator gebaut werden. |
| **Dimensions and tolerances** (*Fits, thread representation, surface symbols, geometric tolerances to ISO*) | Bemaßung und ISO 1101 Form-/Lagetoleranzen sind **zu 100 % in CADCraft**. | **Lücke Mechvane:** ISO 286 Passungsabmaße (aus `mechvane/iso286.py`), Gewindesymbole (DIN ISO 6410) und Oberflächensymbole (ISO 1302) müssen als semantische Anmerkungen von Mechvane generiert werden. |
| **Title block and parts list** (*Title block, parts list and balloons. Linked to the model in both directions*) | 2D-Tabellen und Multileader sind **zu 100 % in CADCraft**. | **Lücke Mechvane:** Die bidirektionale Kopplung an Baugruppen (`assembly.bom.get`/`set`, Bauteil-Metadaten) muss Mechvane verwalten und die Tabelleneinträge in CADCraft synchronisieren. |
| **Drawings by your agent** (*Your agent derives a drawing ready for manufacturing and checks it for missing or duplicate dimensions*) | CADCraft bietet volle Agentensteuerung über Stdio-MCP (`cadcraft-cli mcp`). | **Lücke Mechvane:** Ein Agenten-Workflow (`derive_drawing`), der Maße kollisionsfrei platziert und Prüfungen auf Über- und Unterbemaßung (Grad der Bestimmtheit) durchführt. |
| **Drawings that know the model** (*Every edge in a view keeps the feature it comes from, with thread, depth, fit or weld*) | **Fehlt vollständig in DXF/CADCraft.** Ein DXF-Export verliert alle 3D-Feature-Bezüge. | **Lücke Mechvane (Kernherausforderung):** Semantische 3D→2D-Vererbung. Projizierte 2D-Kanten müssen über IDs oder XData/Metadaten an das 3D-Feature (`Hole1`, `Fillet2`, `Plate`) gekoppelt bleiben, damit Maße Modelländerungen überleben. |
| **PDF and DXF export** | **Zu 100 % in CADCraft vorhanden.** | Keine Lücke. CADCraft exportiert hochqualitative PDFs und DXFs direkt über CLI oder MCP. |

---

## 7. Vorschlag für die ersten Schritte (Architektur Phase 3)

Auf Basis der Erkenntnisse empfiehlt sich folgende modulare Architektur für Mechvane Phase 3:

```
┌─────────────────────────────────────────────────────────────┐
│                 Mechvane Phase 3 Architektur                │
├──────────────────────────────┬──────────────────────────────┤
│    3D-Modellseite            │     2D-Zeichnungsseite       │
│    (SolidCraft + Mechvane)   │     (CADCraft Crates / CLI)  │
├──────────────────────────────┼──────────────────────────────┤
│ • B-Rep Feature-Baum         │ • Blattformat & Layouts      │
│ • Semantische PMI            │ • Ansichtsfenster (Viewports)│
│   (Passung H7, M6-Gewinde)   │ • ISO-25 Bemaßungsdarstellung│
│ • Schnitt- und Ansichts-     │ • ISO 1101 Toleranzrahmen    │
│   Projektion (Plan #860)     │ • DIN EN ISO 7200 Schriftfeld│
│ • Assoziative Kanten-IDs     │ • PDF- und DXF-Export        │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             Mechvane MCP-Zeichnungswerkzeuge                │
│  - derive_drawing: Automatische Erstellung der Standardblatt│
│  - dimension_feature: Assoziative Bemaßung aus 3D-Feature   │
│  - check_drawing: Prüfung auf Unter- und Überbemaßung       │
└─────────────────────────────────────────────────────────────┘
```

### Konkrete nächste Entwicklungsschritte:

1. **Schritt 1: Prototypisches Python-Modul `mechvane/drawing.py`**
   - Kapselung des `CadcraftMcpClient` aus dieser Recherche in Mechvane.
   - Bereitstellung grundlegender Zeichenwerkzeuge: `create_drawing(part_or_asm, template="A4_landscape")`, `place_views()`, `add_title_block()`.

2. **Schritt 2: Assoziative Geometriekoordination (PMI-Vererbung)**
   - Statt reiner Koordinatenbemaßung liest Mechvane die Feature-Maße aus dem Modellbaum aus:
     - `Plate`: Länge $60\,\text{mm}$, Breite $60\,\text{mm}$, Dicke $8\,\text{mm}$
     - `BoltHoles`: 4 Bohrungen $\varnothing 6{,}6\,\text{mm}$ auf Teilkreis $\varnothing 45\,\text{mm}$
   - Übergabe dieser Maße mit korrekten Passungsbezeichnungen (`iso286.deviations`) direkt an CADCraft.

3. **Schritt 3: Behebung der Sehnen-Triangulierung (Upstream-Mitarbeit SolidCraft #860)**
   - SolidCrafts `file.export_view_dxf` exportiert zylindrische Flächen aktuell als diskrete Liniensegmente.
   - Mitarbeit an SolidCraft Issue #860 (exakte 2D-Projektion analytischer Flächen: Zylinder werden zu echten `CIRCLE`/`ARC`-Elementen im DXF), damit Durchmesser- und Radiusmaße (`dimdiameter`, `dimradius`) assoziativ an Kanten fassen können.

4. **Schritt 4: Schnittansichten und Gewindesymbole**
   - Generator für 2D-Schnittansichten: Körper an Schnittebene teilen (`inspect.section`), Schnittfläche mit DIN-Schraffur (`hatch {pattern: "ANSI31"}`) füllen.
   - Generator für Gewindekanten nach DIN ISO 6410 (3/4-Kreisbogen auf Kerndurchmesser).

---

## 8. Fazit

CADCraft 0.8.0 ist die **ideale 2D-Zeichnungsseite** für Mechvane Phase 3:
- Es deckt Blatt, ISO-25-Bemaßung, Toleranzrahmen, Tabellen, Blöcke, Attribute und PDF/DXF-Export bereits heute vollständig und headless über MCP ab.
- Die **Modellseite** (exakte Kantenprojektion, Schnitte, Gewindesemantik und Feature-Assoziativität) muss hingegen von SolidCraft und Mechvane kommen.
- Durch die identische Technologiebasis (Rust, egui 0.36, wgpu 30, MIT/Apache-2.0-Lizenz) können die Crates von CADCraft mittelfristig sogar direkt als native Rust-Bibliothek eingebunden werden, ohne dass ein externer Prozess nötig ist.

---

## Prüfvermerk Claude (2026-11-09)

- Nachgeprüft: 426 Befehle in `cadcraft-cli commands`, `dimlinear`, `tolerance`, `table`, `counttable`, `exportpdf`
  vorhanden, `viewbase` fehlt; `file.export_view_dxf` in SolidCraft `crates/engine/src/cmd/view_dxf.rs:24`;
  CADCraft-Lizenz `MIT OR Apache-2.0`; SolidCraft-Plan #860 in `docs/drawing-hlr.md`.
- Abweichung: Im erzeugten PNG ist das Schriftfeld praktisch leer. Die Zellentexte erscheinen nur als winzige
  Striche, die Texthöhe der Tabelle passt nicht zum Blatt. „Schriftfeld befüllt“ gilt also nur technisch.
- „Ideale 2D-Seite“ und „zu 100 %“ sind Geminis Wertung nach einem einzigen Flansch-Beispiel, keine belegte Aussage.
