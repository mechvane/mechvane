# Versuch: Allgemeiner Befehlsdialog aus den SolidCraft-Schemas

**Datum:** 2026-11-15 (Erstfassung 2026-11-12; überarbeitet nach Review auf Typ-zuerst-Regeln und Ableitung direkt aus JSON-Schema/`$defs`)  
**Autor:** Antigravity / Gemini  
**Kontext:** `ROADMAP.md` Z. 239–243 („Allgemeiner Befehlsdialog und Abdeckungsmatrix“), Strategiepapier [docs/strategie/2026-11-10-agentik-roadmap-v01.md](../strategie/2026-11-10-agentik-roadmap-v01.md#L303-L312) Abs. 7.2, Issue #77.

---

## 1. Ziel und Fragestellung

Ziel dieses Versuchs ist zu klären, ob sich für jeden SolidCraft-Befehl ein generischer Dialog aus seiner Schemabeschreibung erzeugen lässt. In der Roadmap heißt es dazu:

> „Befehlssuche (Strg+K) und ein Formular, das aus dem Schema jedes SolidCraft-Befehls entsteht (`describe_command`), Auswahlfelder für Kanten, Flächen und Skizzen über die vorhandene Auswahl, Vorschau und Rückgängig über `/api/feature`. Eigene Dialoge bleiben für die häufigsten Befehle. Eine Matrix führt je Befehl, wie er erreichbar ist (eigener Dialog, allgemeiner Dialog, MCP); ein Test geht die Befehlsliste durch. Zuerst ein Versuch an zehn Befehlen quer durch die Bereiche.“ ([ROADMAP.md](../../ROADMAP.md#L239-L243))

Und im Strategiepapier:

> „SolidCraft beschreibt jeden Befehl mit Parametern und Schema (`describe_command`). Daraus lässt sich **ein allgemeiner Dialog** erzeugen: Befehlssuche (Strg+K), Formular aus dem Schema, Auswahlfelder für Kanten, Flächen und Skizzen über die vorhandene Auswahl, Vorschau und Rückgängig über das vorhandene `/api/feature`. Eigene Dialoge bleiben für die etwa 15 häufigsten Befehle. Damit ist die Abdeckung messbar vollständig, und jeder neue SolidCraft-Befehl ist am Tag seines Erscheinens da. Zuerst ein Versuch von einem Tag: Schemas von zehn Befehlen quer durch die Bereiche (Blech, Fläche, Muster, Baugruppe) ziehen und prüfen, ob sich die Auswahlfelder aus den Parameternamen sicher erkennen lassen.“ ([docs/strategie/2026-11-10-agentik-roadmap-v01.md](../strategie/2026-11-10-agentik-roadmap-v01.md#L303-L312))

Hierfür wurde das Analysewerkzeug [tools/command_matrix.py](../../tools/command_matrix.py) entwickelt. Es befragt eine headless SolidCraft-Sitzung (`Session` aus [mechvane/solidcraft.py](../../mechvane/solidcraft.py)) via MCP-Protokoll (`list_commands`, `describe_command`), erfasst alle Parameter, stuft diese anhand der JSON-Schema-Struktur (Typ vor Name, ohne hartcodierte `$defs`-Listen) ein und schreibt die erzeugte Matrix nach `build/befehlsmatrix.json` (git-ignoriertes Artefakt unter `/build/`).

---

## 2. Ausgabe der automatischen Prüfung (`tools/command_matrix.py`)

Die Ausführung von `python3 tools/command_matrix.py` gegen das in Mechvane aktuelle CLI `solidcraft-cli 0.41.0` (`VERSION = "0.41.0"` in [mechvane/install.py](../../mechvane/install.py#L19)) liefert wörtlich folgende vollständige Ausgabe:

```text
Starte SolidCraft-Sitzung und lese Befehlskatalog...

Matrix geschrieben nach: build/befehlsmatrix.json

============================================================
ÜBERSICHT: BEFEHLE JE BEREICH
============================================================
Bereich              | Gesamt   | Mit Schema | Anteil Schema
------------------------------------------------------------
appearance           |       10 |          3 |        30.0%
assembly             |        4 |          4 |       100.0%
body                 |        3 |          3 |       100.0%
browser              |        9 |          9 |       100.0%
canvas               |        7 |          6 |        85.7%
component            |       32 |         27 |        84.4%
config               |        8 |          8 |       100.0%
construct            |       23 |         23 |       100.0%
contact              |        7 |          7 |       100.0%
diagnostics          |        6 |          6 |       100.0%
doc                  |        4 |          4 |       100.0%
document             |        6 |          5 |        83.3%
edit                 |        5 |          5 |       100.0%
engine               |        2 |          2 |       100.0%
explode              |        4 |          4 |       100.0%
expr                 |        1 |          1 |       100.0%
face                 |        1 |          0 |         0.0%
file                 |       17 |         15 |        88.2%
frame                |        5 |          5 |       100.0%
inspect              |       21 |         19 |        90.5%
joint                |       19 |         19 |       100.0%
layout               |        5 |          5 |       100.0%
library              |        3 |          3 |       100.0%
material             |        8 |          8 |       100.0%
mesh                 |        1 |          1 |       100.0%
model                |        5 |          5 |       100.0%
motion               |       11 |         11 |       100.0%
note                 |        4 |          4 |       100.0%
occurrence           |        7 |          6 |        85.7%
panel                |       25 |         25 |       100.0%
parameters           |       13 |         13 |       100.0%
parts                |        4 |          4 |       100.0%
plastic              |        7 |          7 |       100.0%
plugin               |        4 |          4 |       100.0%
pointcloud           |        5 |          3 |        60.0%
render               |       65 |         58 |        89.2%
select               |        4 |          2 |        50.0%
selection            |        2 |          1 |        50.0%
settings             |        7 |          0 |         0.0%
sheet                |       13 |         12 |        92.3%
sketch               |      131 |        125 |        95.4%
solid                |       36 |         27 |        75.0%
surface              |       19 |         16 |        84.2%
timeline             |       22 |         22 |       100.0%
ui                   |        3 |          3 |       100.0%
view                 |       44 |         32 |        72.7%

============================================================
ÜBERSICHT: PARAMETER JE EINSTUFUNG
============================================================
Auswahl in der Ansicht              |   765 |  28.7%
Zahl/Ausdruck                       |   693 |  26.0%
Text                                |   490 |  18.4%
Schalter                            |   358 |  13.4%
unklar                              |   206 |   7.7%
Auswahlliste (enum)                 |   155 |   5.8%

  Detail 'Auswahl in der Ansicht':
    - Kanten                    |   192 |   7.2%
    - Körper                    |   174 |   6.5%
    - Skizze                    |   138 |   5.2%
    - Geometrie                 |   123 |   4.6%
    - Feature                   |   105 |   3.9%
    - Flächen                   |    17 |   0.6%
    - Profil                    |    16 |   0.6%

============================================================
ERGEBNIS DER PRÜFUNG:
============================================================
Befehle gesamt: 572 (mit Schema; 642 im Gesamtkatalog)
Parameter gesamt: 2667
Anteil „unklar“: 7.7% (206 von 2667)
Fehler bei describe_command: 0
```

*(Hinweis: Der Pfad in der Zeile `Matrix geschrieben nach:` gibt zur Laufzeit den vollständigen lokalen Pfad zur erzeugten `build/befehlsmatrix.json` im jeweiligen Arbeitsverzeichnis aus.)*

### Vergleich zum Ausgangsstand (`0.30.1` vs. `0.41.0`)
In der früher in Mechvane hinterlegten Version `solidcraft-cli 0.30.1` besaßen lediglich 103 von 570 Befehlen (18,1 %, 530 Parameter) ein JSON-Schema (`input`). Mit `solidcraft-cli 0.41.0` auf `main` liegt die Schemaabdeckung bei **572 von 642 Befehlen (89,1 %)** mit insgesamt **2667 Parametern**. Lediglich 70 Befehle liefern im CLI noch kein strukturiertes Schema (`has_schema: false`), darunter alle 7 `settings`-Befehle, 12 `view`-Befehle, 9 `solid`-Befehle, 7 `appearance`-Befehle, 7 `render`-Befehle, 6 `sketch`-Befehle, 5 `component`-Befehle, 3 `surface`-Befehle sowie kleinere Lücken in `canvas` (1), `document` (1), `face` (1), `file` (2), `inspect` (2), `occurrence` (1), `pointcloud` (2), `select` (2), `selection` (1) und `sheet` (1).

---

## 3. Zahl der Befehle je Bereich

Insgesamt umfasst der Befehlskatalog in `solidcraft-cli 0.41.0` **642 Befehle** in **46 Bereichen** (Präfixen). Die Verteilung der Befehle und Schemas je Bereich lautet:

| Bereich (Präfix) | Befehle gesamt | Mit Schema (`0.41.0`) | Anteil mit Schema | Bemerkung zum Bereich |
| :--- | :---: | :---: | :---: | :--- |
| `appearance` | 10 | 3 | 30.0% | Erscheinungsbilder/Farben |
| `assembly` | 4 | 4 | 100.0% | Baugruppenabfragen, Stückliste und Constraints |
| `body` | 3 | 3 | 100.0% | Körperbefehle (`body.repair`, `body.print_face`) |
| `browser` | 9 | 9 | 100.0% | Modellbaum-Gruppierung, Sortierung, Sichtbarkeit |
| `canvas` | 7 | 6 | 85.7% | Bildhintergründe einfügen, kalibrieren, ausrichten |
| `component` | 32 | 27 | 84.4% | Komponenten, Verknüpfungen, Kontextbearbeitung |
| `config` | 8 | 8 | 100.0% | Konfigurationstabelle, Varianten, Regeln |
| `construct` | 23 | 23 | 100.0% | Konstruktionsebenen, -achsen, -punkte |
| `contact` | 7 | 7 | 100.0% | Kontaktdefinitionen |
| `diagnostics` | 6 | 6 | 100.0% | Diagnose- und Prüfbefehle |
| `doc` | 4 | 4 | 100.0% | Dokumenteigenschaften (Kurzform) |
| `document` | 6 | 5 | 83.3% | Dokumentverwaltung und Metadaten |
| `edit` | 5 | 5 | 100.0% | Rückgängig/Wiederholen, Checkpoints |
| `engine` | 2 | 2 | 100.0% | Systembefehl `engine.describe` |
| `explode` | 4 | 4 | 100.0% | Explosionsansichten |
| `expr` | 1 | 1 | 100.0% | Ausdrucksauswertung (`expr.evaluate`) |
| `face` | 1 | 0 | 0.0% | Einzelflächenoperationen |
| `file` | 17 | 15 | 88.2% | STEP-, STL-, 3MF-, OBJ-, DXF-, SVG-, URDF-Export/-Import |
| `frame` | 5 | 5 | 100.0% | Gestell- / Profilbefehle |
| `inspect` | 21 | 19 | 90.5% | Form-, Krümmungs-, Interferenz- und Parameteranalysen |
| `joint` | 19 | 19 | 100.0% | Gelenke erstellen, bearbeiten, antreiben |
| `layout` | 5 | 5 | 100.0% | Arbeitsbereichslayout |
| `library` | 3 | 3 | 100.0% | Komponentenbibliothek |
| `material` | 8 | 8 | 100.0% | Materialzuweisungen und Materialkarten |
| `mesh` | 1 | 1 | 100.0% | Netzgeometrie |
| `model` | 5 | 5 | 100.0% | Topologieabfragen |
| `motion` | 11 | 11 | 100.0% | Bewegungssimulation |
| `note` | 4 | 4 | 100.0% | Notizen im Modell |
| `occurrence` | 7 | 6 | 85.7% | Vorkommnisse verschieben/ausrichten/kopieren |
| `panel` | 25 | 25 | 100.0% | UI-Panel- und Fenstersteuerung |
| `parameters` | 13 | 13 | 100.0% | Parameterverwaltung |
| `parts` | 4 | 4 | 100.0% | Normteil- und Bauteilfunktionen |
| `plastic` | 7 | 7 | 100.0% | Kunststoff-Konstruktionselemente |
| `plugin` | 4 | 4 | 100.0% | Plugin-Schnittstelle |
| `pointcloud` | 5 | 3 | 60.0% | Punktwolken |
| `render` | 65 | 58 | 89.2% | Rendereinstellungen, Beleuchtung, Studio, Kameras |
| `select` | 4 | 2 | 50.0% | Auswahlbefehle |
| `selection` | 2 | 1 | 50.0% | Selektionspuffer (`selection.delete`) |
| `settings` | 7 | 0 | 0.0% | Systemeinstellungen |
| `sheet` | 13 | 12 | 92.3% | Blechbefehle (Flansch, Perforation, Falz, Konvertierung usw.) |
| `sketch` | 131 | 125 | 95.4% | Skizzierer (Linien, Kreise, Constraints, Hilfslinien usw.) |
| `solid` | 36 | 27 | 75.0% | Volumenkörper (Extrude, Revolve, Fillet, Chamfer, Muster, Grundkörper) |
| `surface` | 19 | 16 | 84.2% | Flächenbefehle (Patch, Loft, Sweep, Trim, Blend, Offset usw.) |
| `timeline` | 22 | 22 | 100.0% | Verlauf abspielen, Gruppen, Bearbeiten |
| `ui` | 3 | 3 | 100.0% | UI-Steuerung |
| `view` | 44 | 32 | 72.7% | Ansichtssteuerung, Renderrahmen, Kamera |
| **Gesamt** | **642** | **572** | **89.1%** | |

---

## 4. Anteil der Parameter je Einstufung

Über alle 572 Befehle mit Schema wurden **2667 Parameter** analysiert. Die Klassifikation in [tools/command_matrix.py](../../tools/command_matrix.py) wertet konsequent **Schema-Typ vor Parametername** aus und leitet Strukturmuster direkt aus dem JSON-Schema (`enum`, `anyOf`/`oneOf`, `pattern`, `minimum`/`maximum`/`minItems`/`maxItems`, `properties`, `items`, `additionalProperties`) ab, statt manuelle `$defs`-Listen zu pflegen:

1. Eindeutige Skalar-Typen zuerst: `boolean` -> **Schalter**; `number`/`integer` (ohne ID-/Index-Listen) -> **Zahl/Ausdruck**; `any`/untypisiert (`serde_json::Value`) -> **unklar** (nie über den Namen geraten); `enum`/`oneOf`/`anyOf`-Literale und `$defs` mit Choice-Muster (z. B. `BendTableFormat`) -> **Auswahlliste (enum)**.
2. Strukturierte `array`/`object`-Typen direkt aus ihrer Schema-Form: 2D/3D-Vektoren und `Point3` (wie `from`, `to`, `surface.patch.edges`, `surface.patch.points`) -> **Zahl/Ausdruck**; Listen von CAD-Auswahlobjekten oder topologischen Auswahlfeldern -> **Auswahl in der Ansicht**; offene Konfigurations-, Kamera-, Tabellen- und Material-Objekte -> **unklar**.
3. Nur mehrdeutige Zeichenketten-/Referenztypen (`string`, `StringList`, `IdOrName`, `NameList`, `string|integer`) werden weiter über Beschreibung (`$defs`-Text + Parameterbeschreibung) und Parametername auf **Auswahl in der Ansicht**, **Zahl/Ausdruck** (`*Expr`) oder **Text** (Standard-Rückfall für beliebige `string`-Werte, z. B. `doc.recover.dir` oder `config.row.name`) aufgelöst.

| Einstufung des Eingabefelds | Anzahl Parameter | Anteil an allen Parametern | Typische Schema-Typen / Beispiele |
| :--- | :---: | :---: | :--- |
| **Auswahl in der Ansicht** | **765** | **28.7%** | 3D-Viewport-/Baum-Auswahl (Kanten, Körper, Skizzen, Geometrie, Features, Flächen, Profile) |
| **Zahl/Ausdruck** | **693** | **26.0%** | `LengthExpr`, `AngleExpr`, `NumberExpr`, `number`, `integer`, `Point3`, Vektoren |
| **Text** | **490** | **18.4%** | `name`, `body_name`, `body_names`, Pfade (`dir`, `path`), Bezeichner (`string`) |
| **Schalter** | **358** | **13.4%** | `boolean` (z. B. `through_all`, `thin`, `flip`, `reverse`) |
| **unklar** | **206** | **7.7%** | Untypisierte `any`-Werte, offene Dicts, Kamera-/Render-/Panel-Objekte, Untertabellen |
| **Auswahlliste (enum)** | **155** | **5.8%** | `enum`, `oneOf`, Literal-/Choice-Varianten (`Operation`, `Direction`, `BendTableFormat`) |
| **Gesamt** | **2667** | **100.0%** | |

### Detailaufschlüsselung der Kategorie „Auswahl in der Ansicht“
Die interaktive Auswahl in der 3D-Ansicht bzw. im Modellbaum (765 Parameter = 28.7 %) teilt sich wie folgt auf:

- **Kanten (`edges`, `curves`, `bends`, `EdgeRef`, `SketchOperand`, `sketch.pattern.rectangular.direction`):** 192 Parameter (7.2%)  
  Kantenpicks, Skizzenkurven, Biegelinien und Richtungs-Referenzen für Fasen, Rundungen, Laschen, Skizzenmuster.
- **Körper (`bodies`, `body`, `participants`, `targets`, `face_body`):** 174 Parameter (6.5%)  
  Auswahl teilnehmender Festkörper für Boolesche Operationen, Schnitte, Blechumformung.
- **Skizzen (`sketch`, `SketchRef`, `SketchTarget`):** 138 Parameter (5.2%)  
  Auswahl der zugrundeliegenden Skizze im Featurebaum oder Viewport.
- **Geometrie (`GeoRef`, `PlaneOrFace`, `PatternAxis`, `JointOrigin`, `ToolFace`, `PlacementPath`, `sketch.move_point.point`):** 123 Parameter (4.6%)  
  Referenzebenen, Achsen, Gelenkursprünge, Occurrence-Pfade, strukturierte Fläche-/Punkt-Selektoren.
- **Features / Komponenten / Gelenke (`features`, `components`, `joint`, `IdOrName`):** 105 Parameter (3.9%)  
  Auswahl existierender Features, Komponenten, Gelenke, Gruppen oder Studien im Modellbaum.
- **Flächen (`faces`, `face` als String-/Objektauswahl):** 17 Parameter (0.6%)  
  Flächenpicks über String- oder Flächenreferenzen.
- **Profile (`profiles`, `Profiles`, `profiles_3d`):** 16 Parameter (0.6%)  
  Auswahl geschlossener Regionen/Profile innerhalb einer Skizze.

---

## 5. Liste aller „unklar“-Fälle (206 Fälle, 7.7%)

Die 206 Parameter, die nach den strengen Typ-zuerst-Regeln als „unklar“ eingestuft wurden, verteilen sich auf **25 Bereiche** (vollständige Einzelliste im JSON-Feld `summary.unklar_faelle` von `build/befehlsmatrix.json`). Gegenüber einer reinen Namensheuristik werden dadurch untypisierte `any`-Felder (wie `sketch.construction_line.{at, through}` oder `sketch.insert_{dxf, svg}.*`) nicht mehr fälschlich über ihren Namen als Zahlen oder Geometrie geraten, sondern transparent als Schema-Lücke bzw. Spezialobjekt ausgewiesen:

### Klasse A: Render-, Kamera-, Material-, Erscheinungsbild- und UI-Panel-Objekte (113 Fälle)
Ganze Zustandsobjekte, Kamera-Structs, PBR-/Materialkarten und UI-Docking-Ziele, die eigene Inspektoren statt eines einfachen Parameter-Formulars brauchen:
- **`render` (71 Fälle):**
  - `render.surface.import.{frame, maps, provenance, set}`, `render.environment.set.set` (5)
  - `render.lights.{set, add, duplicate, remove}.{set, settings}`, `render.lights.list.settings` (9)
  - `render.coat.bind.{coat, set}`, `render.coat.unbind.target`, `render.optics.bind.{optics, set}`, `render.optics.unbind.target` (6)
  - `render.result.{regrade.job, regrade.presentation, pin.job, copy.job}`, `render.{status, cancel, export}.job` (7)
  - `render.camera.set.camera`, `render.preset.{resolve, apply}.set`, `render.quality.prepare.cpu`, `render.stage.{ground, backdrop, clear}.set` (7)
  - `render.library.surface.{bind.set, bind.surface, unbind.set, unbind.target}`, `render.library.environment.apply.set`, `render.library.studio.{prepare.set, apply.rig, apply.set}` (8)
  - `render.settings.{capture_hdr.set, set.set}`, `render.batch.request` (3)
  - `render.preflight.{adaptive, aging, backdrop, caustics, denoise_settings, environment, finishing, led_strip, lens, lighting, raytrace, settings, volume}` (13)
  - `render.start.{adaptive, aging, backdrop, caustics, denoise_settings, environment, finishing, led_strip, lens, lighting, raytrace, settings, volume}` (13)
- **`panel` (18 Fälle):**
  - `panel.{action, activate, close, collapse, float, focus, move, native_close, peek, popout, resize}.target` (11)
  - `panel.{float, move, open, popout}.destination` (4), `panel.resize.size`, `panel.resize_pair.{first_size, second_size}` (3)
- **`view` (11 Fälle):**
  - `view.{save, apply, navigate, normal_to, front, back, left, right, top, bottom, isometric}.camera` (11)
- **`material` (6 Fälle):**
  - `material.{create, edit}.{pbr, physical_card}` (4), `material.properties.{validate, directional}.card` (2)
- **`appearance` (2 Fälle), `inspect` (2 Fälle), `file` (1 Fall), `motion` (1 Fall), `library` (1 Fall):**
  - `appearance.assign.{color, pbr}` (2), `inspect.compare.color`, `inspect.silhouette.camera` (2), `file.export_view_dxf.camera` (1), `motion.export_animation.camera` (1), `library.export.provenance` (1)

### Klasse B: Untypisierte `any`-Felder (`serde_json::Value`) und offene Dictionaries (59 Fälle)
Felder ohne festes JSON-Schema (`type: any`) oder freie Key-Value-Dictionaries, über deren Widget die UI ohne Schemaverfeinerung keine sichere Aussage treffen kann:
- **`sketch` (39 von 43 Sketch-Fällen):**
  - `sketch.construction_line.{at, through}` über alle 10 Varianten (`construction_line`, `horizontal`, `vertical`, `angle`, `parallel`, `perpendicular`, `tangent_external`, `tangent_at`, `tangent_two`, `bisector`) = **20 Fälle** (`any`)
  - `sketch.{insert_dxf, insert_svg}.{height, name, path, plane, scale}` = **10 Fälle** (`any`, bedingte Parameter)
  - `sketch.create.{face, origin, x_dir, y_dir}` (`InsidePlane`, explizit abgewiesene Altparameter) = **4 Fälle**
  - `sketch.scale.base`, `sketch.move.center`, `sketch.pattern.circular.center` (`SketchPointOrId`, 2D-Punkt `[x, y]` oder Punkt-ID) = **3 Fälle**
  - `sketch.draw.dimensioned.params` (`CreatorParams`), `sketch.drag_end.constraint` (`DragConstraint`) = **2 Fälle**
- **`file` (5 von 6 File-Fällen):**
  - `file.insert_step.tolerance`, `file.insert_mesh.{folder, names}`, `file.save_mesh.{ascii, single_instance}` (`any`)
- **`construct` (3 Fälle):**
  - `construct.{plane, axis, point}.with` (`object`, methodenabhängige Zusatzparameter)
- **`motion` (3 von 5 Motion-Fällen):**
  - `motion.export_animation.{from, index, to}` (`any`)
- **`component` (2 Fälle), `document` (2 Fälle), `joint` (2 von 6 Joint-Fällen):**
  - `component.metadata.set.{properties, values}`, `document.metadata.set.{value, values}`, `joint.as_built.{value, values}`
- **`parameters` (1 Fall), `plugin` (1 Fall), `sheet` (1 von 2 Sheet-Fällen):**
  - `parameters.change.changes`, `plugin.run.params`, `sheet.flange.segments`

### Klasse C: Verschachtelte Listen, Paartabellen und polymorphe Verbundfelder (34 Fälle)
Arrays aus Teilobjekten, Wertepaaren `[a, b]` oder polymorphen Verbundtypen, die eine Untertabelle bzw. ein Spezial-Widget erfordern:
- **`config` (5 Fälle):** `config.configure.face_appearances`, `config.column.face_appearance`, `config.row.values`, `config.rule.{rule, rules}`
- **`joint` (4 Fälle):** `joint.origin.{circle, face}` (`OriginFace`), `joint.{create, as_built}.limits` (`JointLimits`)
- **`sketch` (4 Fälle):** `sketch.edit.restore_marker` (`EditMarker`), `sketch.draw.dimensioned.dimensions` (`DimensionValues`), `sketch.arc.tangent.end` (`ArcEnd`), `sketch.edit_text.edits` (`array`)
- **`solid` (4 Fälle):** `solid.cylinder.references`, `solid.fillet.{mid, setbacks}`, `solid.align.axes` (`AlignAxes`)
- **`surface` (4 Fälle):** `surface.boundary.{u, v}`, `surface.patch.continuity`, `surface.loft.sections`
- **`timeline` (4 Fälle):** `timeline.redefine.params`, `timeline.edit.set`, `timeline.add.{feature, params}`
- **`inspect` (3 Fälle):** `inspect.continuity.edges`, `inspect.parameter_variants.variants`, `inspect.measure.items`
- **`browser` (1 Fall):** `browser.reparent.occurrences`
- **`explode` (1 Fall):** `explode.create.moves`
- **`frame` (1 Fall):** `frame.member.names` (`MemberNames`)
- **`motion` (1 Fall):** `motion.study.keys`
- **`occurrence` (1 Fall):** `occurrence.move.to` (`MoveTo`)
- **`sheet` (1 Fall):** `sheet.flange.then` (`ThenSteps`)

---

## 6. Handprüfung von zehn Befehlen gegen den SolidCraft-Quellcode

Zur Validierung der automatischen Matrix wurden zehn repräsentative Befehle quer durch alle Bereiche manuell gegen den SolidCraft-Quellcode (Upstream-Stand Commit `3d9725dc8`, Verzeichnis `crates/engine/src/`) geprüft und mit der aktuellen `tools/command_matrix.py`-Einstufung auf `solidcraft-cli 0.41.0` abgeglichen:

### 1. Blech (Sheet Metal): `sheet.flange`
- **Fundstelle:** `crates/engine/src/schema/sheet.rs:363` (`struct FlangeParams`) und `crates/engine/src/cmd/sheet.rs:42`.
- **Parameter in Matrix (`0.41.0`):** 23 Parameter (`angle`, `body`, `body_name`, `body_names`, `corner_relief`, `corner_relief_shape`, `curves`, `distance`, `edges`, `flip`, `height`, `height_from`, `name`, `participants`, `position`, `profiles`, `radius`, `reverse`, `rule`, `segments`, `sketch`, `then`, `type`).
- **Abgleich:**
  - `type`, `height_from`, `position`, `corner_relief_shape` -> **Auswahlliste (enum)** (bestätigt).
  - `edges` (`FlangeEdges`), `curves` (`StringList`) -> **Auswahl in der Ansicht (Kanten)** (bestätigt).
  - `profiles` (`Profiles`) -> **Auswahl in der Ansicht (Profil)**; `sketch` (`IdOrName`) -> **Auswahl in der Ansicht (Skizze)**; `body`, `participants` -> **Auswahl in der Ansicht (Körper)** (bestätigt).
  - `height`, `distance`, `radius`, `angle`, `corner_relief` -> **Zahl/Ausdruck** (bestätigt).
  - `flip`, `reverse` -> **Schalter**; `name`, `body_name`, `body_names`, `rule` -> **Text** (bestätigt).
  - `then` (`ThenSteps`), `segments` (`any`) -> **unklar** (korrekt).

### 2. Flächen (Surface): `surface.patch`
- **Fundstelle:** `crates/engine/src/schema/surface.rs:1019` (`struct PatchParams`) und `crates/engine/src/cmd/surface.rs:43`.
- **Parameter in Matrix (`0.41.0`):** 12 Parameter (`body`, `body_name`, `body_names`, `continuity`, `crown`, `edges`, `name`, `participants`, `points`, `profiles`, `profiles_3d`, `sketch`).
- **Abgleich:**
  - `sketch` (`IdOrName`) -> **Auswahl in der Ansicht (Skizze)** (bestätigt).
  - `profiles` (`Profiles`), `profiles_3d` (`array` von Profilketten) -> **Auswahl in der Ansicht (Profil)** (bestätigt).
  - `body`, `participants` -> **Auswahl in der Ansicht (Körper)** (bestätigt).
  - `crown` (`number`) -> **Zahl/Ausdruck**; `name`, `body_name`, `body_names` -> **Text** (bestätigt).
  - `continuity` (`string|array|object`) -> **unklar** (polymorph: akzeptiert `g0..g4` oder eine Liste `{edge, continuity}`).
  - **Einheitliche `Point3`-Regel für `edges` und `points`:** Beide Felder sind im Schema als `array` von `Point3` (`[x, y, z]` oder `{"x", "y", "z"}`) definiert und landen daher beide einheitlich bei **Zahl/Ausdruck** (ohne Namens-Sonderfall für `edges`). Im UI sollte jedes `Point3`-Feld optional einen 3D-Viewport-Pick unterstützen.

### 3. Muster (Pattern): `solid.pattern.circular`
- **Fundstelle:** `crates/engine/src/schema/features.rs:961` (`struct PatternCircularParams`) und `crates/engine/src/cmd/features.rs:122`.
- **Parameter in Matrix (`0.41.0`):** 12 Parameter (`alignment`, `angle`, `axis`, `bodies`, `body_name`, `body_names`, `components`, `count`, `features`, `name`, `participants`, `reversed`).
- **Abgleich:**
  - `features`, `components` (`NameList`) -> **Auswahl in der Ansicht (Feature)** (bestätigt).
  - `bodies` (`NameList`), `participants` (`StringList`) -> **Auswahl in der Ansicht (Körper)** (bestätigt).
  - `axis` (`PatternAxis`) -> **Auswahl in der Ansicht (Geometrie)** (bestätigt).
  - `count` (`NumberExpr`), `angle` (`AngleExpr`) -> **Zahl/Ausdruck** (bestätigt).
  - `alignment` -> **Auswahlliste (enum)**; `reversed` (`boolean`) -> **Schalter**; `name`, `body_name`, `body_names` -> **Text** (bestätigt).

### 4. Baugruppe / Gelenke: `joint.edit`
- **Fundstelle:** `crates/engine/src/schema/joints.rs:57` (`struct EditJointParams`) und `crates/engine/src/cmd/joints.rs:170`.
- **Parameter in Matrix:** 10 Parameter (`a`, `angle`, `b`, `flip`, `joint`, `name`, `offset`, `quiet`, `suppressed`, `type`).
- **Abgleich:**
  - `joint` (`IdOrName`) -> **Auswahl in der Ansicht (Feature)**; `a`, `b` (`JointOrigin`) -> **Auswahl in der Ansicht (Geometrie)** (bestätigt).
  - `flip`, `suppressed`, `quiet` (`boolean`) -> **Schalter** (bestätigt).
  - `offset` (`LengthExpr`), `angle` (`AngleExpr`) -> **Zahl/Ausdruck** (bestätigt).
  - `name` (`string`) -> **Text** (bestätigt).
  - **Abweichung bei `type`:** In `EditJointParams` ist `kind` (`type`) als `Option<String>` statt als Rust-`enum` definiert. Die Typ-zuerst-Regel stuft `type` sauber als **Text** ein, obwohl der Beschreibungstext (`rigid, revolute, slider, ...`) im Dialog eine **Auswahlliste** nahelegt.

### 5. Skizze: `sketch.edit`
- **Fundstelle:** `crates/engine/src/schema/sketch.rs:27` (`struct EditParams`) und `crates/engine/src/cmd/sketch.rs:106`.
- **Parameter in Matrix:** 2 Parameter (`restore_marker`, `sketch`).
- **Abgleich:**
  - `sketch` (`IdOrName`) -> **Auswahl in der Ansicht (Skizze)** (bestätigt).
  - `restore_marker` (`EditMarker`) -> **unklar** (akzeptiert Timeline-Position, `null` oder `false` und wird ohne Sonderliste als spezielles Zustandsobjekt gemeldet).

### 6. Volumenkörper: `solid.extrude`
- **Fundstelle:** `crates/engine/src/schema/features.rs:73` (`struct ExtrudeParams`) und `crates/engine/src/cmd/features.rs:49`.
- **Parameter in Matrix (`0.41.0`):** 31 Parameter (`body`, `body_name`, `body_names`, `convention`, `curves`, `direction`, `distance`, `distance2`, `exact_regions`, `extent`, `face`, `face_body`, `faces`, `fixed`, `from`, `name`, `operation`, `participants`, `profiles`, `side`, `sketch`, `start_offset`, `taper`, `targets`, `thickness`, `thickness2`, `thin`, `through_all`, `to`, `to_offset`, `touching`).
- **Abgleich:**
  - `sketch` (`IdOrName`) -> **Auswahl in der Ansicht (Skizze)**; `profiles` (`Profiles`) -> **Auswahl in der Ansicht (Profil)**; `curves` (`StringList`) -> **Auswahl in der Ansicht (Kanten)**; `body`, `face_body`, `targets`, `participants` -> **Auswahl in der Ansicht (Körper)** (bestätigt).
  - `distance`, `distance2`, `start_offset`, `to_offset`, `thickness`, `thickness2`, `taper` -> **Zahl/Ausdruck** (bestätigt).
  - `direction`, `operation`, `side`, `convention`, `extent`, `touching` -> **Auswahlliste (enum)** (bestätigt).
  - `through_all`, `thin`, `exact_regions`, `fixed` -> **Schalter**; `name`, `body_name`, `body_names` -> **Text** (bestätigt).
  - **Einheitliche `Point3`-Regel:** `from` (`Point3`), `to` (`Point3`), `face` (`Point3`) und `faces` (`Faces`, Array aus `Point3`) folgen exakt derselben Regel wie `surface.patch.{edges, points}` und landen einheitlich unter **Zahl/Ausdruck**. Im UI profitieren alle `Point3`-Felder von einem einheitlichen „Punkt/Fläche im Viewport picken“-Helfer.

### 7. Konstruktionsebenen: `construct.plane.offset`
- **Fundstelle:** `crates/engine/src/schema/features.rs:732` (`struct OffsetPlaneParams`) und `crates/engine/src/cmd/features.rs:176`.
- **Parameter in Matrix:** 5 Parameter (`base`, `name`, `offset`, `participants`, `through`).
- **Abgleich:**
  - `base` (`PlaneOrFace`), `through` (`GeoRef`) -> **Auswahl in der Ansicht (Geometrie)** (bestätigt).
  - `offset` (`LengthExpr`) -> **Zahl/Ausdruck** (bestätigt).
  - `name` (`PlaneName`) -> **Text**; `participants` (`StringList`) -> **Auswahl in der Ansicht (Körper)** (bestätigt).

### 8. Prüfen / Formanalyse: `inspect.draft`
- **Fundstelle:** `crates/engine/src/schema/surface_analysis.rs:43` (`struct DraftParams`) und `crates/engine/src/cmd/surface_analysis.rs:33`.
- **Parameter in Matrix:** 3 Parameter (`angle`, `clear`, `pull`).
- **Abgleich:**
  - `pull` (`AxisDir`), `angle` (`number`) -> **Zahl/Ausdruck** (bestätigt).
  - `clear` (`boolean`) -> **Schalter** (bestätigt).

### 9. Datei-Export: `file.export_step`
- **Fundstelle:** `crates/engine/src/schema/file.rs:47` (`struct ExportStepParams`) und `crates/engine/src/cmd/file.rs:108`.
- **Parameter in Matrix:** 2 Parameter (`bodies`, `path`).
- **Abgleich:**
  - `path` (`string`) -> **Text** (Zieldateipfad, bestätigt).
  - `bodies` (`StringList`) -> **Auswahl in der Ansicht (Körper)** (bestätigt).

### 10. Komponenten / Kontextbearbeitung: `component.edit_in_place`
- **Fundstelle:** `crates/engine/src/schema/component.rs:27` (`struct EditInPlaceParams`) und `crates/engine/src/cmd/component.rs:110`.
- **Parameter in Matrix:** 2 Parameter (`component`, `path`).
- **Abgleich:**
  - `component` (`IdOrName`) -> **Auswahl in der Ansicht (Feature)** (verknüpfte Komponente, bestätigt).
  - `path` (`array` von Occurrence-IDs/Pfadsegmenten) -> **Auswahl in der Ansicht (Geometrie)** (über die Array-Strukturregel, sauber getrennt vom `string`-Dateipfad in `file.export_step.path`, bestätigt).

---

## 7. Vergleich mit bestehenden Dialogen (`FEATURE_COMMANDS`)

In Mechvanes Web-Oberfläche existieren heute für neun zentrale Modellierbefehle maßgeschneiderte Dialoge. In [mechvane/ui/server.py](../../mechvane/ui/server.py#L360-L373) sind diese unter `FEATURE_COMMANDS` registriert:

```python
FEATURE_COMMANDS = {
    "mechvane.sketch": _sketch_label,
    "solid.fillet": lambda p: f"Fillet R{_num(p.get('radius'))} on {_edges_label(p)}",
    "solid.chamfer": lambda p: f"Chamfer {_num(p.get('distance'))} on {_edges_label(p)}",
    "solid.hole": _hole_label,
    "solid.pattern.rectangular": _pattern_label("Rectangular"),
    "solid.pattern.circular": _pattern_label("Circular"),
    "solid.mirror": lambda p: f"Mirror {_features_label(p)}",
    "solid.extrude": lambda p: f"{_op_label(p)}Extrude {p.get('sketch', '')}"
                               + (", through all" if (p.get("extent") or p).get("through_all") else
                                  f", {_num((p.get('extent') or p).get('distance'))}"),
    "solid.revolve": lambda p: f"{_op_label(p)}Revolve {p.get('sketch', '')}"
                               + (f", {_num(p['angle'])}" if p.get("angle") is not None else ""),
}
```

### Abgleich mit der Schemaabdeckung (`solidcraft-cli 0.41.0`)
| Befehl in `FEATURE_COMMANDS` | Hat Schema in `0.41.0` | Anzahl Parameter | Begründung / Einordnung |
| :--- | :---: | :---: | :--- |
| `mechvane.sketch` | *(Virtuell)* | – | Mechvane-spezifischer Einstieg in Skizzenumgebung |
| `solid.extrude` | **Ja** | 31 | Kernfeature; eigener Dialog für schnelle intuitive Eingabe |
| `solid.fillet` | **Ja** | 19 | Kernfeature; eigener Dialog für Kantenvorschau & Radius |
| `solid.chamfer` | **Ja** | 11 | Kernfeature; eigener Dialog für Kantenauswahl & Abstand |
| `solid.revolve` | **Ja** | 21 | Kernfeature; eigener Dialog für Achse & Winkel |
| `solid.pattern.circular` | **Ja** | 12 | Eigener Dialog für Achse, Winkel & Anzahl |
| `solid.pattern.rectangular` | **Nein** | – | Auch in `0.41.0` ohne strukturiertes JSON-Schema |
| `solid.mirror` | **Nein** | – | Auch in `0.41.0` ohne strukturiertes JSON-Schema |
| `solid.hole` | **Nein** | – | Auch in `0.41.0` ohne JSON-Schema; in Mechvane mit Normtabellen (ISO 273, DIN 974-1) verknüpft |

**Erkenntnis:**  
Mit `solidcraft-cli 0.41.0` besitzen fünf der acht SolidCraft-Befehle in `FEATURE_COMMANDS` (`extrude`, `fillet`, `chamfer`, `revolve`, `pattern.circular`) ein vollständiges Schema, während `pattern.rectangular`, `mirror` und `hole` weiter ohne strukturiertes JSON-Schema sind. Für häufige Kernfeatures und den normbasierten Bohrungsassistenten bleiben maßgeschneiderte Dialoge sinnvoll; für die übrigen 567 schematisierten Befehle liefert der **allgemeine Befehlsdialog** eine direkte Abdeckung.

---

## 8. Fazit und Handlungsempfehlungen für die Umsetzung

1. **Machbarkeit:**  
   In `solidcraft-cli 0.41.0` lassen sich **92.3 % aller 2667 Schema-Parameter** (2461 von 2667 Parametern, bei 206 „unklar“-Fällen = 7.7 %) allein aus JSON-Schema-Struktur, Beschreibung und Parametername auf Standard-UI-Eingabefelder abbilden:
   - 28.7 % Auswahlfelder in der 3D-Ansicht bzw. im Baum (Kanten, Körper, Skizzen, Geometrie, Features, Flächen, Profile)
   - 26.0 % Zahlen-, Ausdrucks- und Punkt-/Vektorfelder
   - 18.4 % Textfelder
   - 13.4 % Schalter / Checkboxen
   - 5.8 % Auswahllisten / Dropdowns
2. **Einheitliche Behandlung von `Point3` und `Option<String>`:**  
   - Alle `Point3`-Parameter (`surface.patch.{edges, points}`, `solid.extrude.{from, to, face, faces}`) teilen denselben Schema-Typ; der generische UI-Renderer sollte daher für jedes `Point3`-Feld ein Koordinatenfeld mit optionalem Viewport-Pick-Button anbieten.
   - `Option<String>`-Felder mit Aufzählung in der Beschreibung (wie `joint.edit.type`) bleiben in der statischen Klassifikation ehrlich als `Text`, können aber im UI-Renderer optional durch Vorschläge ergänzt werden.
3. **Behandlung der 206 „unklar“-Fälle:**  
   - **113 Fälle (54.9 %)** betreffen Render-, Kamera-, Material- und UI-Panel-Objekte, die nicht in einen Konstruktions-Befehlsdialog gehören.
   - **59 Fälle** sind untypisierte `any`-Werte (`serde_json::Value`) oder offene Dictionaries (darunter 20 `sketch.construction_line.*`-Punkte), bei denen erst eine Präzisierung der Upstream-Schemas oder der interaktive Skizzierer Klarheit schafft.
   - **34 Fälle** sind echte verschachtelte Verbundobjekte/Tabellen (`sheet.flange.then`, `solid.fillet.mid`, `config.*`, `surface.patch.continuity`), für die kleine Spezial-Widgets vorgesehen werden sollten.

---

## 9. Quellenbelege

Die folgenden Belege dokumentieren die geprüften SolidCraft-Befehlsverträge (`crates/engine/src/schema/` und `crates/engine/src/cmd/`, Commit `3d9725dc8`) mit wörtlichen Zitaten aus den Quelldateien.

### Beleg: sheet.flange (FlangeParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/sheet.rs
- **Wörtliches Zitat:** „Edge: further bends, each a flange on the far edge of the one before (at most 16). Refused“

### Beleg: surface.patch (PatchParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/surface.rs
- **Wörtliches Zitat:** „A planar face on a sketch's regions or on its planar 3D-sketch loops, or one face on a closed“

### Beleg: solid.pattern.circular und solid.extrude (features.rs)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/features.rs
- **Wörtliches Zitat:** „Copy features, bodies or components evenly round an axis.“
- **Wörtliches Zitat:** „Extrude sketch profiles (or a planar body face) into a solid.“
- **Wörtliches Zitat:** „Add a construction plane parallel to“

### Beleg: Befehlsverträge in cmd/features.rs
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/cmd/features.rs
- **Wörtliches Zitat:** „features: [names] | bodies: [names] | components: [names]; dir1: [x,y,z]; count1; spacing1;“

### Beleg: joint.edit (EditJointParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/joints.rs
- **Wörtliches Zitat:** „The joint's type, as joint.create takes it (rigid, revolute, slider, ...).“

### Beleg: sketch.edit (EditParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/sketch.rs
- **Wörtliches Zitat:** „temporarily roll to this sketch and“

### Beleg: inspect.draft (DraftParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/surface_analysis.rs
- **Wörtliches Zitat:** „Nonzero pull direction. Default +Z; normalised by the handler.“

### Beleg: file.export_step (ExportStepParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/file.rs
- **Wörtliches Zitat:** „The bodies to export, by name. Default: every body.“

### Beleg: component.edit_in_place (EditInPlaceParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/component.rs
- **Wörtliches Zitat:** „The placement to edit it at, as occurrence ids from the top of the assembly down“

### Beleg: sketch.construction_line (ConstructionLineParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/sketch_create.rs
- **Wörtliches Zitat:** „Create a reference line in the active sketch: infinite, or a segment of a given length.“

### Beleg: render.environment.set (EnvironmentParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/render.rs
- **Wörtliches Zitat:** „Complete numerical draft, validated before applying the requested edit.“

### Beleg: render.batch (BatchParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/render_ui.rs
- **Wörtliches Zitat:** „Without a request, use the first saved shot's setup (name order).“

### Beleg: render.lights.* (EditParams)
- **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/3d9725dc8/crates/engine/src/schema/render_lights.rs
- **Wörtliches Zitat:** „Complete unsaved setup, used as the edit's starting point without losing other controls.“

---

## 10. Quellenprüfung (`tools/check_sources.py`)

Der Lauf von `python3 tools/check_sources.py docs/research/2026-11-15-befehlsdialog-versuch.md` am 2026-11-15 endete mit Exit-Code `0`:

```text
- Datum: 2026-11-15
- Befehl: python3 tools/check_sources.py docs/research/2026-11-15-befehlsdialog-versuch.md
- Geprüfte Markdown-Dateien: 1

Zusammenfassung:
- Quellen-Links gesamt: 13
- Erreichbar (HTTP 200): 13 von 13 (100.0%)
- Nicht erreichbar: 0 von 13 (Bot-Sperren, 404, Timeouts)
- Zitate bestätigt: 13 voll bestätigt, 0 teilweise bestätigt, 0 nicht gefunden
- Zahlenwerte bestätigt: 2 von 2 Werten im Quelltext nachgewiesen (100.0%)

Auffällige Einträge mit nicht gefundenen Zahlen: Keine.
```
