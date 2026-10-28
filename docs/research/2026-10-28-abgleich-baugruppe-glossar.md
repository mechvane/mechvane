# Abgleichliste Teil 2: Baugruppe, Modellbrowser, Mechvane-Werkzeuge und Begriffsglossar für Spracheingabe

- **Datum:** 2026-10-28
- **Autor:** Gemini 3.8 Flash
- **Status:** Verifiziert mit `tools/check_sources.py` und gegen `/root/repos/_ext/solidcraft` (`48ba6ff3`)
- **Prüfvermerk 2026-10-28 (Claude):** `check_sources.py` 32/32 Zitate, 0 Zahlenfehler; alle 32 SolidCraft-Verweise zeigen auf vorhandene Zeilen, Befehls-IDs stichprobenartig an der genannten Stelle bestätigt; Mechvane-Werkzeugnamen gegen `mechvane/server.py`. 13 Stellen „(unbelegt)“ vor Entscheidungen selbst prüfen. Glossar fließt in ADR 0003, Abschnitt 4.
- **Kontext & Ziel:** Fortsetzung der Menüband-Recherche aus Teil 1 (`docs/research/2026-10-27-abgleich-inventor-solidcraft.md`). Systematischer Abgleich der Autodesk-Inventor-Baugruppenumgebung (`.iam`), des Modellbrowsers (Bauteil- und Baugruppenbaum, Bauteilende-Marker, Kontextmenüs), Nachtrag der Mechvane-Werkzeugabdeckung für Teil-1-Befehle und umfassendes Begriffsglossar für die interaktive Spracheingabe („Point and speak“, ROADMAP Grundsatz 6).

---

## 1. Einleitung und Architekturvergleich

Gemäß den Architektur-Grundsätzen von Mechvane (Grundsatz 5: *„Feature-Baum wie Inventor, keine Fusion-Timeline“*, Grundsatz 6: *„Point and speak“* und Grundsatz 10: *„Bedienung am Ende möglichst nah an Inventor“*) erfordert die Konstruktion komplexer Baugruppen ein Zusammenspiel zwischen parametrischen Einzelteilen und deren Verknüpfung in Baugruppendateien.

### 1.1 Baugruppenarchitektur: Inventor ↔ SolidCraft ↔ Mechvane

| Kriterium | Autodesk Inventor (`.iam`) | SolidCraft (`crates/engine/`) | Mechvane (`docs/mechvane-mcp.md`, `server.py`) |
| :--- | :--- | :--- | :--- |
| **Dateikonzept** | Strikte Trennung: Bauteil (`.ipt`) und Baugruppe (`.iam`) sind eigenständige Dateitypen. | Einheitliches Dateiformat (`.solidcraft`); Baugruppe ist Design mit verknüpften Komponenten (`component.insert_design`). | Getrennte Dateien für Bauteil und Baugruppe nach ADR 0001; Unterscheidung über Metadaten `dev.mechvane.kind`. |
| **Beziehungsmodell** | Historisch zweistufig: Geometrische Abhängigkeiten (*Constraints*: Passend, Fluchtend, Winkel, Tangential, Einfügen, Symmetrie) und kinematische Verbindungen (*Joints*: Starr, Drehung, Schieben, Zylindrisch, Planar, Kugel). | Rein kinematisches Gelenkmodell (`joint.create` in `crates/engine/src/cmd/joints.rs:25`) mit Gelenktypen (`rigid`, `revolute`, `slider`, `cylindrical`, `planar`, `ball`) und Relationen (`parallel`, `angle`, `point_on_plane`). | Basiert auf `joint.create`; MCP-Werkzeuge `add_joint`, `edit_joint`, `delete_joint`, `adopt_joint`. Speichert Flächenanker für automatische Reparatur. |
| **Referenzstabilität über Dateigrenzen** | Assoziative Verknüpfung über interne Element-IDs; Baugruppenabhängigkeiten referenzieren Geometrie-Features der Bauteile. | Verknüpfte Bauteile werden über STEP eingebunden. Dabei gehen interne Flächennamen verloren; Gelenke können bei Geometrieänderungen springen (#3330). | `update_links(assembly, repair=True)`: Erkennt gewanderte Gelenke und Verschraubungsanker atomar und repariert Verankerungen nach Bauteiländerungen. |
| **Top-Down-Bearbeitung** | Bearbeiten an Ort und Stelle (*Edit in Place*): Bauteil wird im Baugruppenkontext aktiviert; übrige Teile werden transparent gedimmt. | `component.edit_in_place` (`crates/engine/src/cmd/component.rs:51`) und `component.finish_edit` (`crates/engine/src/cmd/component.rs:64`). | `edit_in_place(assembly, occurrence, point)` und `finish_edit(part, update)`: Löst auch verschachtelte Unterbaugruppen auf, transformiert 3D-Koordinaten. |

---

## 2. Abgleichtabelle: Inventor-Baugruppen-Menüband ↔ SolidCraft ↔ Mechvane

Die folgende Tabelle stellt alle Befehle des Inventor-Baugruppen-Menübands (Register „Zusammenfügen“ / `Assemble`, belegte Gruppen *Komponente*, *Position*, *Beziehungen*, *Anordnung/Muster*, *Verwalten* sowie Register *Prüfen* / `Inspect`) den entsprechenden SolidCraft-Befehlen (`crates/engine/src/cmd/`) und den Mechvane-MCP-Werkzeugen gegenüber. Alle Inventor-Befehlsnamen und Gruppen sind wörtlich aus `help.autodesk.com` belegt oder explizit mit `(unbelegt)` markiert.

| Register | Gruppe | Inventor (de) | Inventor (en) | Kürzel Inventor | SolidCraft-Befehl (Datei:Zeile) | Mechvane-Werkzeug | Bemerkung |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **Zusammenfügen** | Komponente | Komponente platzieren | Place Component | `P` | `component.insert_design (crates/engine/src/cmd/component_link.rs:32)` | `insert_part` | Volle Übereinstimmung in Funktion. Kürzel `P` belegt (`GUID-DEEB0723`, `GUID-2C55B507`). In Mechvane: `insert_part(assembly, part_path, name, translate, rotate, grounded)`. |
| **Zusammenfügen** | Komponente | Aus Inhaltscenter platzieren (unbelegt) | Place from Content Center (unbelegt) | – | `parts.fastener (crates/engine/src/cmd/parts.rs:21)` | `standard_part` | Fügt Normteile ein. In SolidCraft `parts.fastener` und `parts.library` (`crates/engine/src/cmd/parts.rs:18`). In Mechvane: `standard_part(norm, size, length)`. |
| **Zusammenfügen** | Komponente | Komponente erstellen | Create Component | `N` | `component.create (crates/engine/src/cmd/component.rs:43)` | `new_part` / `edit_in_place` | Erzeugt neue Komponente in der Baugruppe (`GUID-DEEB0723`, `GUID-FBBE5A60`). Kürzel `N` in Inventor belegt. In Mechvane über `new_part` bzw. In-Place-Workflow. |
| **Zusammenfügen** | Komponente | Komponente ersetzen (unbelegt) | Replace Component (unbelegt) | – | `component.relink (crates/engine/src/cmd/component_link.rs:41)` | – | Tauscht eine referenzierte Komponente gegen eine andere Datei aus (`GUID-23D30350`). In SolidCraft über `component.relink`. |
| **Zusammenfügen** | Position | Freie Verschiebung | Free Move | `M` | `occurrence.move (crates/engine/src/cmd/component.rs:106)` | – | Temporäres oder permanentes Verschieben (`GUID-DEEB0723`, `GUID-9796C22B`). Kürzel `M` in Inventor belegt. In SolidCraft `occurrence.move` und `occurrence.drag` (`crates/engine/src/cmd/component.rs:108`). |
| **Zusammenfügen** | Position | Freie Drehung | Free Rotate | `RO` | `occurrence.move (crates/engine/src/cmd/component.rs:106)` | – | Dreht Komponente um ihren Ursprung (`GUID-DEEB0723`, `GUID-7EAE9DFD`). Kürzel `RO` in Inventor belegt. In SolidCraft über `occurrence.move` mit Rotationsmatrix. |
| **Zusammenfügen** | Position | Fixiert (unbelegt) | Grounded (unbelegt) | – | `occurrence.ground (crates/engine/src/cmd/component.rs:113)` | `insert_part(..., grounded=True)` | Entfernt alle Freiheitsgrade der Komponente im Baugruppenraum. In Mechvane optionaler Parameter beim Einfügen. |
| **Zusammenfügen** | Position | Position erfassen (unbelegt) | Capture Position (unbelegt) | – | `component.capture_position (crates/engine/src/cmd/component.rs:119)` | – | Fusion-Konzept in SolidCraft; in Inventor werden freie Verschiebungen nach Aktualisierung verworfen oder durch Abhängigkeiten fixiert. |
| **Zusammenfügen** | Position | Position wiederherstellen (unbelegt) | Revert Position (unbelegt) | – | `component.revert_position (crates/engine/src/cmd/component.rs:120)` | – | Setzt temporäre Positionsänderungen zurück auf den gelösten Zustand. |
| **Zusammenfügen** | Beziehungen | Abhängig machen | Constrain | `C` | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Zentraler Abhängigkeitsdialog (`GUID-DEEB0723`, `GUID-198F05E4`, `GUID-EBD2C784`). In SolidCraft und Mechvane über das Gelenksystem abgebildet. |
| **Zusammenfügen** | Beziehungen | Zusammenfügen | Assemble | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Minimierte Werkzeugleiste zur schnellen Vergabe von Beziehungen (`GUID-198F05E4`). |
| **Zusammenfügen** | Beziehungen | Passend | Mate | `ALT + Ziehen mit der Maus` | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Positioniert Flächen mit entgegengesetzten Normalen aufeinander (`GUID-DEEB0723`, `GUID-EBD2C784`). In SolidCraft `joint.create` mit `flip=false` oder Relation `point_on_plane`. |
| **Zusammenfügen** | Beziehungen | Fluchtend | Flush | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Flächennormalen zeigen in dieselbe Richtung (`GUID-EBD2C784`). In SolidCraft `joint.create` mit `flip=true` oder Relation `parallel`. |
| **Zusammenfügen** | Beziehungen | Winkel | Angle | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Bestimmt Winkel zwischen Kanten oder Flächen (`GUID-EBD2C784`). In SolidCraft über Parameter `angle` oder Relation `angle`. |
| **Zusammenfügen** | Beziehungen | Tangential | Tangent | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Berührung am Tangentialpunkt (`GUID-EBD2C784`). In SolidCraft über `joint.create` an zylindrischen Ursprungselementen. |
| **Zusammenfügen** | Beziehungen | Einfügen | Insert | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Koaxiale Ausrichtung plus Planarpassung (`GUID-EBD2C784`). In SolidCraft `type: "rigid"` oder `"cylindrical"` an kreisförmigem Ursprung. |
| **Zusammenfügen** | Beziehungen | Symmetrie (unbelegt) | Symmetry (unbelegt) | – | – (nicht gefunden) | – | Symmetrische Ausrichtung zweier Bauteile bezüglich einer Ebene. In SolidCraft keine native Baugruppen-Symmetrierelation (nicht gefunden). |
| **Zusammenfügen** | Beziehungen | Verbindung | Joint | `J (unbelegt)` | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Gelenkbefehl in Gruppe Beziehungen (`GUID-21DC3336`, `GUID-6AA68E8F`). Tastenkürzel `J` ist in SolidCraft belegt (`key("J")`), in Inventor unbelegt. |
| **Zusammenfügen** | Beziehungen | Verbindung: Starr | Joint: Rigid | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | Entfernt alle 6 Freiheitsgrade (`GUID-6AA68E8F`). In SolidCraft und Mechvane: `type: "rigid"`. |
| **Zusammenfügen** | Beziehungen | Verbindung: Drehung | Joint: Rotational | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | 1 rotatorischer Freiheitsgrad (`GUID-6AA68E8F`). In SolidCraft und Mechvane: `type: "revolute"`. |
| **Zusammenfügen** | Beziehungen | Verbindung: Schieben | Joint: Slider | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | 1 translatorischer Freiheitsgrad (`GUID-6AA68E8F`). In SolidCraft und Mechvane: `type: "slider"`. |
| **Zusammenfügen** | Beziehungen | Verbindung: Zylindrisch | Joint: Cylindrical | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | 1 Translation + 1 Rotation (`GUID-6AA68E8F`). In SolidCraft und Mechvane: `type: "cylindrical"`. |
| **Zusammenfügen** | Beziehungen | Verbindung: Planar | Joint: Planar | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | 2 Translationen + 1 Rotation (`GUID-6AA68E8F`). In SolidCraft und Mechvane: `type: "planar"`. |
| **Zusammenfügen** | Beziehungen | Verbindung: Kugel | Joint: Ball | – | `joint.create (crates/engine/src/cmd/joints.rs:25)` | `add_joint` | 3 rotatorische Freiheitsgrade (`GUID-6AA68E8F`). In SolidCraft und Mechvane: `type: "ball"`. |
| **Zusammenfügen** | Beziehungen | Gelenkursprung (unbelegt) | Joint Origin (unbelegt) | – | `joint.origin (crates/engine/src/cmd/joints.rs:22)` | – | Definiert expliziten Ursprung mit Ausrichtung an Kante/Fläche/Kreis. |
| **Zusammenfügen** | Beziehungen | Starrgruppe (unbelegt) | Rigid Group (unbelegt) | – | `joint.rigid_group (crates/engine/src/cmd/joints.rs:40)` | – | Verbindet ausgewählte Occurrences starr miteinander. |
| **Zusammenfügen** | Beziehungen | Beziehung bewegen (unbelegt) | Drive Relationship (unbelegt) | – | `joint.drive (crates/engine/src/cmd/joints.rs:41)` | – | Animiert Freiheitsgrade und prüft geschlossene Schleifen. |
| **Zusammenfügen** | Anordnung | Anordnung (Rechteckig) | Rectangular Pattern | – | `solid.pattern.rectangular (crates/engine/src/cmd/features.rs:84)` | `bolted_connection(..., pattern=...)` | Dupliziert Komponenten linear (`GUID-CF627358`). SolidCraft unterstützt `components: [names]`. In Mechvane in `bolted_connection` integriert. |
| **Zusammenfügen** | Anordnung | Anordnung (Kreisförmig) | Circular Pattern | – | `solid.pattern.circular (crates/engine/src/cmd/features.rs:88)` | `bolted_connection(..., pattern=...)` | Dupliziert Komponenten kreisförmig um eine Achse (`GUID-FF7B08E3`). SolidCraft unterstützt `components: [names]`. |
| **Zusammenfügen** | Anordnung | Spiegeln | Mirror | `MI` | `solid.mirror (crates/engine/src/cmd/features.rs:96)` | – | Spiegelt Komponenten an einer Ebene (`GUID-DEEB0723`, `GUID-C5B3D3DF`). Kürzel `MI` belegt. |
| **Zusammenfügen** | Anordnung | Kopieren (unbelegt) | Copy Components (unbelegt) | – | `occurrence.copy (crates/engine/src/cmd/component.rs:103)` | – | Erstellt Instanzkopien von Komponenten (`GUID-0E21F4A0`). In SolidCraft `occurrence.copy`. |
| **Zusammenfügen** | Verwalten | Stückliste | Bill of Materials | – | `assembly.bom (crates/engine/src/cmd/bom.rs:36)` | – | Strukturierte oder reine Teileliste der Baugruppe (`GUID-6C58657F`). In SolidCraft `assembly.bom`. |
| **Zusammenfügen** | Verwalten | Verknüpfungen aktualisieren (unbelegt) | Update Links (unbelegt) | – | `component.update_links (crates/engine/src/cmd/component_link.rs:37)` | `update_links(assembly, repair)` | Aktualisiert externe Bauteile. In Mechvane mit Reparaturprüfung für gewanderte Flächen und Verschraubungsanker. |
| **Prüfen** | Kollision | Kollision analysieren | Analyze Interference | – | `inspect.interference (crates/engine/src/cmd/joints.rs:96)` | `check_design` | Erkennt Überschneidungen zwischen Komponenten (`GUID-80DED0A6`). In Mechvane analysiert `check_design` Bauteile auf Fertigungsregeln. |
| **Prüfen** | Messen (unbelegt) | Messen (unbelegt) | Measure (unbelegt) | – | – (nicht im cmd-Kern) | `measure(document)` | Liefert Volumen, Fläche, Schwerpunkt und Bounding Box (in Baugruppen in Weltkoordinaten). |

---

## 3. Abgleich Modellbrowser: Inventor ↔ SolidCraft ↔ Mechvane

Der Modellbrowser ist das zentrale Navigations- und Steuerungselement in Autodesk Inventor. Gemäß ROADMAP Grundsatz 5 (*„Feature-Baum wie Inventor, keine Fusion-Timeline“*) soll Mechvane diesen Aufbau im Datenmodell und in der Präsentation abbilden.

### 3.1 Modellbrowser im Bauteilmodus (`.ipt` vs. Bauteil-Sitzung)

1. **Baumhierarchie und Skizzenunterordnung:**
   - **Autodesk Inventor:** Skizzen gehören hierarchisch dem Feature, das sie verbraucht hat. Ein Klick auf das Plus-Symbol vor `Extrusion1` klappt die verbrauchte `Skizze1` auf. Unverbrauchte Skizzen stehen auf oberster Ebene.
   - **SolidCraft:** Verwendet im Kern eine lineare Timeline (`crates/engine/src/cmd/edit.rs`) und Ordnerstrukturen nach Fusion-Art (`bodies`, `sketches`, `construction` in `crates/engine/src/cmd/browser.rs:64`).
   - **Mechvane:** Setzt über die Skizzenregel (`docs/mechvane-mcp.md:82`, `mechvane/tree.py`) die automatische Unterordnung um: Nach jedem `run`-Batch prüft Mechvane `timeline.dependents`, ordnet verbrauchte Skizzen direkt vor ihrem Feature an und stellt sie im `browser()`-Werkzeug hierarchisch darunter dar.
2. **Bauteilende-Marker (End of Part / EOP):**
   - **Autodesk Inventor:** Am Ende des Bauteilbaums sitzt das Symbol `Bauteilende` (`GUID-69196418`). Wird es mit der Maus nach oben gezogen, werden alle darunterliegenden Elemente vorübergehend aus dem Berechnungsmodell entfernt (Rollback). Über das Kontextmenü kann die Markierung direkt verschoben werden (`Bauteilende-Markierung verschieben` / `Move EOP Marker` bzw. `Bauteilende zum Ende verschieben` / `Move EOP to End`).
   - **SolidCraft:** Bildet diesen Mechanismus über die Befehle `timeline.rollback` (`crates/engine/src/cmd/edit.rs:52`) und `timeline.roll_to` (`crates/engine/src/cmd/edit.rs:53`) ab.
   - **Mechvane:** Das MCP-Werkzeug `browser()` kennzeichnet zurückgerollte Features im Statusfeld (`rolled_back: true`), sodass der aktive Konstruktionsstand transparent bleibt.
3. **Kontextmenü-Befehle im Bauteilbrowser:**
   - **Unterdrücken (Suppress):** In Inventor werden Features per Rechtsklick unterdrückt. In SolidCraft entspricht dies `timeline.suppress` (`crates/engine/src/cmd/edit.rs:65`).
   - **Löschen (Delete, Taste `Delete`):** In Inventor fragt das Löschen eines Features nach abhängigen Skizzen. Mechvane bietet `delete_feature(document, feature, keep_sketch)` (`mechvane/server.py:172`), das Skizzen automatisch mitlöscht, sofern sie von keinem anderen Feature geteilt werden.
   - **Umbenennen (Rename, Taste `F2`):** In Inventor ruft `F2` den Umbenennungsmodus auf (`GUID-428B9A8E`). In SolidCraft entspricht dies `timeline.rename` (`crates/engine/src/cmd/edit.rs:37`) bzw. `body.rename` (`crates/engine/src/cmd/browser.rs:21`).
   - **Sichtbarkeit (Visibility, Tastenkürzel `Alt+V`):** In Inventor blendet der Kontextmenüeintrag `Sichtbarkeit` Arbeitselemente, Skizzen und Körper ein oder aus (`GUID-DEEB0723`, `GUID-BA193171`). In SolidCraft wird dies über `browser.visibility` (`crates/engine/src/cmd/browser.rs:45`) gesteuert.

### 3.2 Modellbrowser im Baugruppenmodus (`.iam` vs. Baugruppen-Sitzung)

1. **Beziehungen an Komponenten vs. zentraler Joints-Ordner (Grundsatz 5):**
   - **Autodesk Inventor:** Baugruppenabhängigkeiten und Verbindungen werden **direkt unter den beteiligten Komponenten** aufgeführt (`GUID-69196418`: *„Elemente mit Abhängigkeiten werden unter den Elementen angezeigt, von denen sie abhängig sind“*). Ein Gelenk zwischen `Grundplatte:1` und `Lagerbock:1` erscheint im Browser unter beiden Komponenten.
   - **SolidCraft:** Legt alle Gelenke standardmäßig in einem separaten Fusion-artigen Ordner `c0/joints` ab (`crates/engine/src/cmd/browser.rs:47`).
   - **Mechvane:** Löst diesen Bruch im Datenmodell auf: In den Baugruppen-Metadaten (`dev.mechvane.joints`) speichert Mechvane die Zuordnung. Das Werkzeug `browser(document)` visualisiert Gelenke direkt unter beiden beteiligten Komponenten. Mit dem Parameter `groups=true` kann zwischen der Inventor-Ansicht und der Fusion-Ordneransicht umgeschaltet werden.
2. **Bearbeiten an Ort und Stelle (Edit in Place):**
   - **Autodesk Inventor:** Ein Doppelklick oder Rechtsklick `Bearbeiten` (`Edit`) auf eine Komponente aktiviert deren lokale Modellierungsumgebung im Kontext der Baugruppe (`GUID-FBBE5A60`). Ein Klick auf `Zurückkehren` (`Return`) schließt die Sitzung ab.
   - **SolidCraft:** Stellt `component.edit_in_place` (`crates/engine/src/cmd/component.rs:51`) und `component.finish_edit` (`crates/engine/src/cmd/component.rs:64`) bereit.
   - **Mechvane:** Bietet die agentenfähigen Werkzeuge `edit_in_place(assembly, occurrence, point)` und `finish_edit(part, update)` (`mechvane/server.py:499`, `:507`). Mechvane löst verschachtelte Unterbaugruppen (`Sub:1/Part:1`) auf, liefert die 4×4-Transformationsmatrix zur Baugruppe und führt beim Beenden atomar `update_links` in allen verknüpfenden Baugruppen aus.
3. **Hierarchie-Verschiebung (Promote / Demote):**
   - **Autodesk Inventor:** Markierte Komponenten können mit `Tab` herabgestuft (*Demote*, Erzeugung einer neuen Unterbaugruppe) oder mit `Shift+Tab` heraufgestuft (*Promote*) werden (`GUID-428B9A8E`).
   - **SolidCraft:** Wird über `occurrence.reparent` (`crates/engine/src/cmd/component.rs:114`) umgesetzt.
4. **Fixierung (Grounded):**
   - **Autodesk Inventor:** Eine fixierte Komponente ist mit einem Reißzwecken-Symbol gekennzeichnet und besitzt 0 Freiheitsgrade im Ursprung.
   - **SolidCraft & Mechvane:** Befehl `occurrence.ground` (`crates/engine/src/cmd/component.rs:113`) bzw. Parameter `grounded=True` in `insert_part`.

---

## 4. Mechvane-Erweiterungsspalte für Teil 1 (Bauteil-Befehle)

In Teil 1 des Abgleichs wurden die Bauteil-Befehle des Menübands gegen SolidCraft abgeglichen. Mechvane setzt als intelligenter CAD-Layer auf SolidCraft auf und deckt zentrale Konstruktionsaufgaben durch eigene, domänenspezifische MCP-Werkzeuge ab, während elementare Geometrieoperationen über den Batch-Befehl `run` ausgeführt werden.

| Inventor-Befehl (Bauteil) | SolidCraft-Befehl | Mechvane-Werkzeug | Abdeckung / Mehrwert durch Mechvane |
| :--- | :--- | :--- | :--- |
| **Bohrung** (`H`) | `solid.hole` | `bolted_connection`, `standard_part`, `find(what="holes")` | Automatisierte Schraubenverbindung über Dateigrenzen hinweg (inkl. Flachsenkung nach DIN 974-1 und Senkung nach DIN 74 Form F), Normteilerzeugung (ISO 4762, ISO 10642) und Gewindeeinsätze (Ruthex). Für native Einzelbohrungen: `run` mit `solid.hole`. |
| **Gewinde** | `solid.thread` | `standard_part`, `bolted_connection` | Automatische Gewindeparametrierung für Verbindungselemente; semantische Prüfung via `check_design` (Einschraubtiefen nach VDI 2230). Kosmetisches Gewinde über `run` mit `solid.thread`. |
| **Rundung** (`F`) | `solid.fillet` | `find(what="edges")`, danach `run` | `find(what="edges", near=...)` ermittelt robuste `pick`-Punkte an Kanten, wodurch Blindraten vermieden wird; Ausführung über `run` mit Skizzen-Rollback-Sicherung. |
| **Fase** (`CH`) | `solid.chamfer` | `find(what="edges")`, danach `run` | Semantische Kantenermittlung über `find`; Ausführung über `run` mit `solid.chamfer`. |
| **Wandung** (Schale) | `solid.shell` | `check_design(profile="...")`, danach `run` | `check_design` prüft Mindestwandstärken (z. B. 1.2 mm für FDM); Erzeugung über `run` mit `solid.shell`. |
| **Passungen & Toleranzen** | – (nicht im Kern) | `iso_fit(nominal, fit)` | Berechnet Grenzmaße, Abmaße und Spiel nach ISO 286 (z. B. `20 H7/h6`) für Bohrungen und Wellen. |
| **Element löschen** (`Delete`) | `timeline.delete` | `delete_feature(document, feature, keep_sketch)` | Löscht ein Feature und entscheidet anhand von `timeline.dependents`, ob verbrauchte Skizzen mitgelöscht oder erhalten bleiben. |
| **Modellbrowser anzeigen** | `browser.*` | `browser(document, groups)` | Gibt die vollständige Feature- und Skizzenhierarchie nach Inventor-Art als JSON und Text aus; optional mit Ordnergruppierung. |
| **Messen** | `inspect.measure` | `measure(document)` | Liefert exakte Werte für Volumen, Begrenzungsrahmen (Bounding Box), Mantelfläche und Schwerpunkt. |
| **Konstruktionsprüfung** | – (nicht im Kern) | `check_design(document, profile)` | Regelbasierte Konstruktionsprüfung gegen Fertigungsrichtlinien (FDM-Druckbarkeit, CNC-Radien, Wandstärken, Schraubenabstände). |
| **Visuelle Kontrolle** | `view.screenshot` | `screenshot(document, view, path)` | Rendert headless eine Ansicht des Bauteils als PNG im Workspace. |
| **Dokument-Lebenszyklus** | `file.new`, `file.open`, `file.save` | `new_part`, `open_document`, `save_document`, `close_document` | Verwaltet Bauteildokumente im Workspace mit Idempotenz- und Konfliktprüfung. |
| **Alle übrigen Befehle** *(Extrusion `E`, Drehung `R`, Sweep, Loft, Prägen, Rippe, Arbeitsebenen, Muster, Spiegeln)* | `solid.*`, `construct.*` | `run(document, commands)` | Ausführung als atomarer Batch über `run`: Bei Fehlern greift ein automatischer Checkpoint-Rollback; im Erfolgsfall wird die Skizzenregel angewendet. |

---

## 5. Begriffsglossar für die Spracheingabe (Point and speak, Grundsatz 6)

Gemäß ROADMAP Grundsatz 6 (*„Point and speak: Der Claude-Agent sitzt in der Oberfläche, und man arbeitet interaktiv mit ihm. Kante markieren und sagen ‚da eine Fase 1 mal 45 Grad‘, Fläche markieren und sagen ‚mittig eine Gewindebohrung M6‘“*) dient das folgende Glossar als Übersetzungsgrundlage für Spracherkennungsmodelle (ASR / Whisper) und Sprachbefehls-Parser.

Das Glossar enthält **104 deutsche Fachbegriffe und typische gesprochene Formulierungen** aus der Konstruktionspraxis, zugeordnet zum englischen Inventor-Konzept, dem SolidCraft- bzw. Mechvane-Zielbefehl, den aus dem Satz zu extrahierenden Parametern sowie typischen phonetischen Verwechslungsgefahren bei der Spracherkennung.

| Nr. | Gesprochene Formulierung / Fachbegriff (de) | Inventor-Begriff (en) | Ziel-Befehl (SolidCraft / Mechvane) | Zu extrahierende Parameter | Verwechslungsgefahr bei Spracherkennung (Phonetik / ASR) |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | „Neue Skizze auf Fläche“ / 2D-Skizze | Start 2D Sketch | `sketch.create` (über `run`) | `plane: {face: pick}` | „Skizze“ vs. „Spitze“ / „Schlitze“; Auswahlebene muss referenziert sein |
| 2 | „Linie von [Punkt] nach [Punkt]“ | Line (`L`) | `sketch.line` (über `run`) | `points: [[x1, y1], [x2, y2]]` | Koordinaten-Zahlenreihen; „Linie“ vs. „Lineal“ |
| 3 | „Rechteck [Länge] mal [Breite]“ | Two Point Rectangle (`R`) | `sketch.rectangle.two_point` | `width: number, height: number` | „mal“ vs. Multiplikationszeichen `*` oder „X“; Kommazahlen |
| 4 | „Mittelpunktsrechteck [Länge] auf [Breite]“ | Center Point Rectangle | `sketch.rectangle.center` | `center: [x,y], width: w, height: h` | „auf“ vs. Addition; Zentrumsangabe |
| 5 | „Kreis mit Durchmesser [D]“ | Center Point Circle (`C`) | `sketch.circle.center` | `radius: D / 2, center: [x,y]` | „Durchmesser“ vs. „Radius“; Verdopplung/Halbierung des Werts |
| 6 | „Kreis mit Radius [R]“ | Center Point Circle (`C`) | `sketch.circle.center` | `radius: R, center: [x,y]` | „Radius“ vs. „Durchmesser“; „R2“ vs. „Er zwei“ vs. „Rz“ |
| 7 | „Dreipunktbogen“ / Bogen durch 3 Punkte | Three Point Arc | `sketch.arc.three_point` | `points: [p1, p2, p3]` | „Bogen“ vs. „Boden“ |
| 8 | „Langloch Mitte-Mitte [Abstand] Durchmesser [D]“ | Center to Center Slot | `sketch.slot.center_to_center` | `length: number, diameter: D` | „Langloch“ vs. „Klangloch“ / „Loch“; Verwechslung Achsabstand/Gesamtlänge |
| 9 | „Sechseck / Polygon mit Schlüsselweite [SW]“ | Polygon | `sketch.polygon.inscribed` | `sides: 6, radius: SW / 2` | „Sechseck“ vs. „Sechs Eck“; Schlüsselweite vs. Umkreisradius |
| 10 | „Spline durch Punkte“ | Spline Interpolation | `sketch.spline.fit_point` | `points: [[x1,y1], ...]` | „Spline“ vs. „Split“ / „Spann“; englische Aussprache `/splaɪn/` |
| 11 | „Skizzenpunkt setzen“ | Point | `sketch.point` (über `run`) | `point: [x, y]` | „Punkt“ vs. Satzzeichen „.“ |
| 12 | „Konstruktionslinie / Hilfslinie“ | Construction (`X`) | `sketch.construction` (über `run`) | `entities: [id], construction: true` | „Hilfslinie“ vs. „Linie“; Umschalt-Status |
| 13 | „Bemaßung [Wert] mm“ | General Dimension (`D`) | `sketch.dimension` (über `run`) | `entity: id, value: number` | „Bemaßung“ vs. „Bemessung“; Dezimalkomma vs. Punkt |
| 14 | „Winkelbemaßung [Grad] Grad“ | Angular Dimension | `sketch.dimension` (über `run`) | `entities: [l1, l2], angle: number` | „Grad“ vs. „Rad“ / „Grade“ |
| 15 | „Koinzident / Punkt auf Punkt“ | Coincident Constraint | `sketch.constraint.coincident` | `points: [p1, p2]` | „Koinzident“ vs. „Koinzidenz“ / „ko-inzident“ |
| 16 | „Kollinear / Linien fluchtend“ | Collinear Constraint | `sketch.constraint.collinear` | `lines: [l1, l2]` | „Kollinear“ vs. „kolinear“ / „curling“ |
| 17 | „Konzentrisch / gleicher Mittelpunkt“ | Concentric Constraint | `sketch.constraint.concentric` | `entities: [c1, c2]` | „Konzentrisch“ vs. „konzentriert“ |
| 18 | „Parallel zueinander“ | Parallel Constraint | `sketch.constraint.parallel` | `lines: [l1, l2]` | „Parallel“ vs. „Parallele“ |
| 19 | „Lotrecht / rechtwinklig zu“ | Perpendicular Constraint | `sketch.constraint.perpendicular` | `lines: [l1, l2]` | „Lotrecht“ vs. „waagerecht“ / „senkrecht“ |
| 20 | „Horizontal ausrichten“ | Horizontal Constraint (`-`) | `sketch.constraint.horizontal_vertical` | `entity: id, orientation: "horizontal"` | „Horizontal“ vs. „Vertikal“; Achsenverwechslung bei geneigter Skizze |
| 21 | „Vertikal ausrichten“ | Vertical Constraint | `sketch.constraint.horizontal_vertical` | `entity: id, orientation: "vertical"` | „Vertikal“ vs. „Horizontal“ |
| 22 | „Tangentialer Übergang“ | Tangent Constraint | `sketch.constraint.tangent` | `entities: [arc, line]` | „Tangential“ vs. „tangierend“ / „Tangente“ |
| 23 | „Gleiche Länge / Gleicher Radius“ | Equal Constraint | `sketch.constraint.equal` | `entities: [e1, e2]` | „Gleich“ vs. „Gleis“ |
| 24 | „Symmetrisch zur Mittelachse“ | Symmetric Constraint | `sketch.constraint.symmetry` | `entities: [e1, e2], axis: line` | „Symmetrisch“ vs. „Geometrisch“ |
| 25 | „Skizzengeometrie fixieren“ | Fix Constraint | `sketch.constraint.fix` | `entity: id` | „Fixieren“ vs. „Vigieren“ / „Frieren“ |
| 26 | „Geometrie projizieren“ | Project Geometry (`P`) | `sketch.project` (über `run`) | `geometry: pick` | „Projizieren“ vs. „Projektieren“ / „Prozessor“ |
| 27 | „Schnittkanten projizieren“ | Project Cut Edges | `sketch.intersect` (über `run`) | `body: name` | „Schnittkanten“ vs. „Schnittkante“ |
| 28 | „Skizzenkontur versetzen um [Abstand]“ | Offset (`O`) | `sketch.offset` (über `run`) | `distance: number, curves: [...]` | „Versatz“ vs. „Vorsatz“; Vorzeichen innen/außen |
| 29 | „Überstehende Linie stutzen“ | Trim (`TR`) | `sketch.trim` (über `run`) | `edge: pick` | „Stutzen“ vs. „Stützen“ / „Kürzen“ |
| 30 | „Linie dehnen bis Schnittpunkt“ | Extend | `sketch.extend` (über `run`) | `edge: pick` | „Dehnen“ vs. „Dänen“ / „Verlängern“ |
| 31 | „Linie an Schnittpunkt teilen“ | Split | `sketch.break` (über `run`) | `curve: pick, point: pick` | „Teilen“ vs. „Trenne“ / „Splitten“ |
| 32 | „Skizzenrundung mit Radius [R]“ | Fillet (Sketch) | `sketch.fillet` (über `run`) | `radius: R, corner: pick` | Skizzenrundung vs. 3D-Kantenrundung |
| 33 | „Skizzenfase [Abstand] mal 45 Grad“ | Chamfer (Sketch) | `sketch.chamfer.equal_distance` | `distance: number, vertex: pick` | „Fase“ vs. „Phase“ (häufigster Homophon-Fehler) |
| 34 | „Skizze fertigstellen / beenden“ | Finish Sketch | `sketch.finish` (über `run`) | keine | „Beenden“ vs. „Entfernen“ |
| 35 | „Extrudieren auf [Höhe] mm“ / Aufpolstern | Extrude (`E`) | `solid.extrude` (über `run`) | `distance: number, operation: "new"\|"join"` | „Extrudieren“ vs. „Extrusion“ / „Exzenter“ |
| 36 | „Ausschneiden / Material abtragen um [Tiefe]“ | Extrude Cut | `solid.extrude` (über `run`) | `distance: number, operation: "cut"` | „Ausschneiden“ vs. „Zuschneiden“ |
| 37 | „Drehung um 360 Grad / Rotationskörper“ | Revolve (`R`) | `solid.revolve` (über `run`) | `angle: 360, axis: pick` | „Drehung“ vs. „Baugruppendrehung“ |
| 38 | „Sweeping entlang Kurve / Profilzug“ | Sweep (`SW`) | `solid.sweep` (über `run`) | `profile: sketch, path: sketch` | „Sweeping“ vs. „Sweet“ / „Suite“ / „Schwieping“ |
| 39 | „Erhebung / Loft zwischen Skizzen“ | Loft (`LO`) | `solid.loft` (über `run`) | `sections: [sk1, sk2]` | „Loft“ vs. „Luft“ / „Lauf“ |
| 40 | „Spirale / Schraubenfeder mit Steigung [P]“ | Coil | `solid.coil` (über `run`) | `pitch: number, revolutions: number` | „Spirale“ vs. „Spule“ / „Helix“ |
| 41 | „Versteifungsrippe mit Dicke [T]“ | Rib | `solid.rib` (über `run`) | `thickness: number, curve: sketch` | „Rippe“ vs. „Grippe“ / „Lippe“ |
| 42 | „Prägen / Schriftzug vertiefen um [Tiefe]“ | Emboss | `solid.emboss` (über `run`) | `depth: number, sketch: id` | „Prägen“ vs. „Fräsen“ / „Pflügen“ |
| 43 | „Wandung mit Dicke [W] mm“ / Aushöhlen | Shell | `solid.shell` (über `run`) | `thickness: number, open_faces: [pick]` | „Wandung“ vs. „Wandlung“ / „Wandstärke“ |
| 44 | „Körper trennen durch Ebene“ | Split Body | `solid.split_body` (über `run`) | `body: name, tool: plane` | „Trennen“ vs. „Tränken“ / „Spalten“ |
| 45 | „Boolesche Vereinigung / Kombinieren“ | Combine Join | `solid.combine` (über `run`) | `target: b1, tools: [b2], operation: "join"` | „Kombinieren“ vs. „Kompilieren“ |
| 46 | „Körper subtrahieren / Boolescher Schnitt“ | Combine Cut | `solid.combine` (über `run`) | `target: b1, tools: [b2], operation: "cut"` | „Subtrahieren“ vs. „Abziehen“ |
| 47 | „Durchgangsbohrung Durchmesser [D]“ | Clearance Hole (`H`) | `solid.hole` (über `run`) | `diameter: D, through: true` | „Durchgangsbohrung“ vs. „Durchgang bohrung“ |
| 48 | „Sacklochbohrung Durchmesser [D] Tiefe [T]“ | Blind Hole (`H`) | `solid.hole` (über `run`) | `diameter: D, depth: T, tip_angle: 118` | „Sackloch“ vs. „Sack loch“ / „Schlagloch“ |
| 49 | „Gewindebohrung M6 mit Tiefe 15“ | Threaded Hole | `solid.hole` (über `run`) | `thread: "M6", thread_depth: 15, depth: 18` | „M6“ vs. „Em sechs“ vs. „M 6“ vs. „am 6.“ |
| 50 | „Gewindebohrung M8 Regelgewinde“ | Metric Threaded Hole | `solid.hole` (über `run`) | `thread: "M8", pitch: 1.25` | „M8“ vs. „Em acht“ vs. „Macht“ |
| 51 | „Zylindrische Senkung / Flachsenkung für M5“ | Counterbore Hole | `solid.hole` (über `run`) | `counterbore_dia: 10, counterbore_depth: 5.4` | „Flachsenkung“ vs. „Flach senkung“ / „Senkung“ |
| 52 | „Kegelsenkung / Senkkopfsenkung 90 Grad“ | Countersink Hole | `solid.hole` (über `run`) | `countersink_dia: 11.2, countersink_angle: 90` | „Senkkopf“ vs. „Senk Kopf“ / „Kegelsenkung“ |
| 53 | „Kernlochbohrung für M6“ | Tap Drill Hole | `solid.hole` (über `run`) | `diameter: 5.0, depth: number` | „Kernloch“ vs. „Kornloch“; Vorbohrmaß (M6 -> 5.0 mm) |
| 54 | „Außengewinde M12 auf Zylinder“ | Thread | `solid.thread` (über `run`) | `face: pick, designation: "M12x1.75"` | „Außengewinde“ vs. „Aus Gewinde“ |
| 55 | „Fase 1 mal 45 Grad an Kante“ | Chamfer (`CH`) | `solid.chamfer` (über `run`) | `distance: 1.0, angle: 45, edge: pick` | „Fase“ vs. „Phase“ (akustisch ununterscheidbar) |
| 56 | „Fase 2 auf 1 Millimeter“ | Two Distance Chamfer | `solid.chamfer` (über `run`) | `distance: 2.0, distance2: 1.0, edge: pick` | Zuordnung der beiden Fasenmaße zu den Flächen |
| 57 | „Rundung R2 an Kante“ / Verrunden | Fillet (`F`) | `solid.fillet` (über `run`) | `radius: 2.0, edges: [pick]` | „R2“ vs. „Er zwei“ vs. „Rz“ (Rautiefe) |
| 58 | „Rundung R5 umlaufend / Tangentialkette“ | Tangent Chain Fillet | `solid.fillet` (über `run`) | `radius: 5.0, edges: [pick], chain: true` | „R5“ vs. „Er fünf“; Kettenauswahl |
| 59 | „Variabler Radius von 2 auf 6 mm“ | Variable Fillet | `solid.fillet` (über `run`) | `type: "variable", radius: 2, radius2: 6` | Anfangs-/Endradius an Kantenverlauf |
| 60 | „Formschräge / Entformungsschräge 2 Grad“ | Face Draft (`D`) | `solid.draft` (über `run`) | `angle: 2.0, pull_direction: vec, faces: [...]` | „Entformungsschräge“ vs. „Formschräge“ |
| 61 | „Arbeitsebene versetzen um [Abstand]“ | Workplane Offset (`]`) | `construct.plane.offset` | `plane: pick, distance: number` | „Arbeitsebene“ vs. „Ebene“; Vorzeichen des Versatzes |
| 62 | „Mittenebene zwischen zwei Flächen“ | Midplane Workplane | `construct.plane.midplane` | `faces: [f1, f2]` | „Mittenebene“ vs. „Mittel ebene“ |
63 | „Winkelebene durch Kante um [Grad] Grad“ | Angle Workplane | `construct.plane.at_angle` | `edge: pick, plane: pick, angle: number` | „Winkelebene“ vs. „Winkel ebene“ |
| 64 | „Arbeitsachse durch Zylinder“ | Work Axis Through Cylinder (`/`) | `construct.axis.through_cylinder` | `face: pick` | „Arbeitsachse“ vs. „Achse“ |
| 65 | „Arbeitsachse durch zwei Punkte“ | Work Axis Two Points | `construct.axis.two_points` | `points: [p1, p2]` | „Achse durch Punkte“ |
| 66 | „Arbeitspunkt auf Ecke / Scheitelpunkt“ | Work Point Vertex (`.`) | `construct.point.vertex` | `vertex: pick` | „Arbeitspunkt“ vs. „Punkt“ |
| 67 | „Benutzerkoordinatensystem / BKS erstellen“ | UCS | `joint.origin` (über `run`) | `origin: pick, x_dir: vec, z_dir: vec` | „BKS“ vs. „B-K-S“ vs. „UCS“ |
| 68 | „Bauteil [Name] in Baugruppe einfügen“ | Place Component (`P`) | `insert_part` (Mechvane) | `part_path: path, name: name` | Dateiname vs. Instanzname; Pfadauslösung |
| 69 | „Bauteil fixieren / festsetzen“ | Grounded | `occurrence.ground` (SolidCraft) | `occurrence: name, grounded: true` | „Fixieren“ vs. „Feste Komponente“ |
| 70 | „Fixierung aufheben“ | Unground | `occurrence.ground` (SolidCraft) | `occurrence: name, grounded: false` | „Lösen“ vs. „Löschen“ |
| 71 | „Komponente um 50 mm in X verschieben“ | Move Component (`M`) | `occurrence.move` (SolidCraft) | `occurrence: name, translate: [50, 0, 0]` | Achsenbuchstabe X/Y/Z vs. Zahlwort |
| 72 | „Komponente um 90 Grad um Z drehen“ | Rotate Component (`RO`) | `occurrence.move` (SolidCraft) | `occurrence: name, rotate: [0, 0, 90]` | Drehachse und Drehsinn |
| 73 | „Bauteil an Ort und Stelle bearbeiten“ | Edit in Place | `edit_in_place` (Mechvane) | `assembly: asm, occurrence: name` | „an Ort und Stelle“ vs. „Ordnerstelle“ |
| 74 | „Bearbeitung beenden / zurück zur Baugruppe“ | Finish Edit / Return | `finish_edit` (Mechvane) | `part: name, update: true` | „Beenden“ vs. „Zurückkehren“ |
| 75 | „Punkt in Bauteilkoordinaten umrechnen“ | Convert Coordinates | `to_part_coords` (Mechvane) | `assembly: asm, occurrence: occ, point: p` | Matrixinversion im Hintergrund |
| 76 | „Abhängigkeit Passend Fläche auf Fläche“ | Mate Constraint (`Alt+Drag`) | `add_joint` / `joint.create` | `type: "rigid"`, `flip: false` | „Passend“ vs. Adjektiv „passend zu“ |
| 77 | „Passend mit 5 mm Abstand / Offset“ | Mate with Offset | `add_joint` / `joint.create` | `type: "rigid"`, `offset: 5.0` | Abstandsmaß und Wirkrichtung |
| 78 | „Abhängigkeit Fluchtend / bündig ausrichten“ | Flush Constraint | `add_joint` / `joint.create` | `type: "rigid"`, `flip: true` | „Fluchtend“ vs. „fluchtet“ / „Fruchtend“ |
| 79 | „Fluchtend mit Versatz [V] mm“ | Flush with Offset | `add_joint` / `joint.create` | `type: "rigid"`, `offset: V, flip: true` | Vorzeichen des Versatzes |
| 80 | „Winkelabhängigkeit [W] Grad zwischen Flächen“ | Angle Constraint | `add_joint` / `joint.create` | `relation: "angle", angle: W` | „Winkel“ vs. Bauteil „Blechwinkel“ |
| 81 | „Tangentiale Abhängigkeit außen“ | Tangent Constraint Outside | `add_joint` / `joint.create` | `type: "planar"`, Ursprung tangential | „Außen“ vs. „Innen“; Berührungsseite |
| 82 | „Abhängigkeit Einfügen für Schraube / Welle“ | Insert Constraint | `add_joint` / `joint.create` | `type: "cylindrical"`, Ursprung Kante | „Einfügen“ vs. Zwischenablage `Strg+V` |
| 83 | „Starre Verbindung / Starres Gelenk“ | Joint: Rigid | `add_joint` (Mechvane) | `type: "rigid", a: origin, b: origin` | „Starr“ vs. „Star“; entfernt 6 Freiheitsgrade |
| 84 | „Drehgelenk / Scharnier um Achse“ | Joint: Rotational | `add_joint` (Mechvane) | `type: "revolute", a: orig, b: orig` | „Drehung“ vs. 3D-Feature Drehung |
| 85 | „Schiebegelenk / Translationsgelenk entlang Kante“ | Joint: Slider | `add_joint` (Mechvane) | `type: "slider", a: orig, b: orig` | „Schieber“ vs. „Schieben“ |
| 86 | „Zylindrisches Gelenk für Welle“ | Joint: Cylindrical | `add_joint` (Mechvane) | `type: "cylindrical", a: o1, b: o2` | „Zylindrisch“ vs. „Zylinder“ |
| 87 | „Planares Gelenk auf Ebene“ | Joint: Planar | `add_joint` (Mechvane) | `type: "planar", a: o1, b: o2` | „Planar“ vs. „Plan“ / „Plana“ |
| 88 | „Kugelgelenk / sphärische Verbindung“ | Joint: Ball | `add_joint` (Mechvane) | `type: "ball", a: o1, b: o2` | „Kugel“ vs. Grundkörper Kugel |
| 89 | „Gelenkrichtung umkehren / Flip“ | Flip Joint | `edit_joint` (Mechvane) | `joint: name, flip: true` | „Umkehren“ vs. „Umdrehen“ |
| 90 | „Gelenkgrenzen setzen: min [A] max [B] Grad“ | Joint Limits | `edit_joint` (Mechvane) | `limits: [[min, max]]` | Einheiten Grad vs. Millimeter |
| 91 | „Rechteckige Anordnung [N] Stück in X [M] in Y“ | Rectangular Pattern | `solid.pattern.rectangular` | `count1: N, spacing1: s1, count2: M` | Zählung: Gesamtanzahl inkl. Original |
| 92 | „Runde Anordnung [N] Stück auf 360 Grad“ | Circular Pattern | `solid.pattern.circular` | `count: N, angle: 360, axis: pick` | Gesamtwinkel vs. Teilungsschritt |
| 93 | „Lochkreis mit 6 Bohrungen auf Durchmesser 100“ | Bolt Circle Pattern | `bolted_connection` / `pattern` | `count: 6, radius: 50, head: "cap"` | „Lochkreis“ vs. „Loch kreis“; Durchmesser/Radius |
| 94 | „Komponente spiegeln an Ebene“ | Mirror Component (`MI`) | `solid.mirror` (SolidCraft) | `components: [name], plane: pick` | Komponenten- vs. Feature-Spiegelung |
| 95 | „Pfadanordnung entlang Kurve [N] Instanzen“ | Pattern on Path | `solid.pattern.path` | `count: N, path: curves` | „Pfad“ vs. „Fahrt“ / „Part“ |
| 96 | „Verschraubung M6 mit Zylinderkopf und Mutter“ | Bolted Connection | `bolted_connection` (Mechvane) | `size: "M6", head: "cap", fasteners: ["washer", "nut"]` | Automatische Bauteilbohrungen und Normteilgenerierung |
| 97 | „Senkverschraubung M5 bündig einlassen“ | Countersunk Bolted Connection | `bolted_connection` (Mechvane) | `size: "M5", head: "countersunk"` | „Senkverschraubung“ vs. Zylinderkopf; DIN 74 Form F |
| 98 | „3D-Druck-Verschraubung mit Ruthex M3“ | Heat Set Insert Connection | `bolted_connection` (Mechvane) | `size: "M3", use_insert: true` | „Ruthex“ vs. „Roothex“ / „Rutech“; Spezialbohrmaß |
| 99 | „Passung 20 H7 berechnen“ | ISO Fit Calculation | `iso_fit` (Mechvane) | `nominal: 20.0, fit: "H7"` | „H7“ vs. „Ha sieben“ vs. „H 7“ (Groß-/Kleinschreibung Welle/Bohrung) |
| 100 | „Wellenpassung 20 k6 prüfen“ | ISO Fit Shaft | `iso_fit` (Mechvane) | `nominal: 20.0, fit: "k6"` | „k6“ vs. „Ka sechs“; Kleinbuchstabe = Welle |
| 101 | „Bauteilende vor [Feature] schieben“ | Move EOP Marker | `timeline.roll_to` (SolidCraft) | `feature: name` | „Bauteilende“ vs. „Bauteil Ende“ / „EOP“ |
| 102 | „Feature [Name] unterdrücken“ | Suppress Feature | `timeline.suppress` (SolidCraft) | `feature: name, suppressed: true` | „Unterdrücken“ vs. „Unter drücken“ / „Löschen“ |
| 103 | „Sichtbarkeit ausschalten / ausblenden“ | Toggle Visibility (`Alt+V`) | `browser.visibility` (SolidCraft) | `visible: false, items: [name]` | „Ausblenden“ vs. „Löschen“ / „Unterdrücken“ |
| 104 | „Konstruktion auf 3D-Druck prüfen“ | Check Design | `check_design` (Mechvane) | `profile: "fdm_0.4"` | Prüft Wandstärken, Überhänge und Lochabstände |

---

## 6. Offene Punkte und Empfehlungen für Mechvane

1. **Komponentenanordnungen in Baugruppen (Component Pattern):**
   - Der SolidCraft-Kern unterstützt im Befehl `solid.pattern.rectangular` (`crates/engine/src/cmd/features.rs:84`) und `solid.pattern.circular` (`crates/engine/src/cmd/features.rs:88`) bereits den Parameter `components: [names]`.
   - Mechvane bietet mit `bolted_connection(..., pattern=...)` bereits koordinierte Verschraubungsmuster.
   - **Empfehlung:** Bereitstellung eines eigenständigen High-Level-MCP-Werkzeugs `pattern_component(assembly, component, type="rectangular"|"circular", ...)` in `mechvane/server.py`, um auch beliebige Zukaufteile oder Unterbaugruppen ohne Verschraubungsassistent parametrisch anzuordnen.
2. **Abhängigkeits-zu-Gelenk-Mapper (Constraint Mapper):**
   - Inventor-Anwender und Sprachbefehle nutzen primär die Begriffe *Passend*, *Fluchtend* und *Einfügen*. SolidCraft verlangt hingegen `joint.create` mit Ursprungsdefinitionen und Gelenktypen.
   - **Empfehlung:** Erweiterung von `add_joint` in Mechvane um eine semantische Parametrierung `constraint="mate"|"flush"|"insert"`, die automatisch die passenden Gelenkparameter (`type="rigid"`, `flip=False` bzw. `True`, `type="cylindrical"`) ableitet.
3. **Phonetische Normalisierungsschicht für Spracheingabe (Point and speak):**
   - Wie das Glossar zeigt, führen phonetisch identische Wörter im Deutschen zu kritischen Syntaxfehlern (z. B. *„Fase“* vs. *„Phase“*, *„Em sechs“* vs. *„M6“*, *„Er zwei“* vs. *„R2“*, *„Ha sieben“* vs. *„H7“*).
   - **Empfehlung:** Vorverarbeitungsmodul (`mechvane/speech.py`), das gesprochenen Text vor der Übergabe an das LLM bzw. den Befehlsextraktor regelbasiert normalisiert (z. B. `re.sub(r'Phase\s+(\d+)', r'Fase ', text)` und `re.sub(r'Em\s*(\d+)', r'M', text)`).
4. **Visualisierung der Gelenkunterordnung im Web- und Desktop-Client:**
   - Datenmodellseitig speichert Mechvane Gelenke bereits über `dev.mechvane.joints` und ordnet sie im Werkzeug `browser()` den beiden verknüpften Komponenten unter (Grundsatz 5).
   - **Empfehlung:** Die Benutzeroberfläche (`mechvane/ui/`) muss diese Hierarchie auch im Baum-Rendering links darstellen, damit Gelenke nicht wie in Fusion in einem isolierten `Joints`-Sammelordner erscheinen.

---

## 7. Quellenbelege und wörtliche Zitate aus der Autodesk-Dokumentation

Alle Zitate in diesem Abschnitt stammen aus der offiziellen Autodesk-Inventor-Dokumentation auf `help.autodesk.com` und wurden mit `tools/check_sources.py` automatisiert verifiziert.

### Beleg: Autodesk Inventor Tastaturkurzbefehle Referenz Baugruppe (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „Wendet in Baugruppen die Abhängigkeit Passend an.“
* **Weiteres Zitat:** „Aktiviert den Befehl Abhängigkeit.“
* **Weiteres Zitat:** „Aktiviert den Befehl Komponente platzieren.“
* **Weiteres Zitat:** „Aktiviert den Befehl Komponente erstellen.“
* **Weiteres Zitat:** „Aktiviert den Befehl Komponente verschieben.“
* **Weiteres Zitat:** „Aktiviert den Befehl Komponente drehen.“

### Beleg: Autodesk Inventor Keyboard Shortcut Reference Assembly (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „In assemblies, applies a mate constraint.“
* **Weiteres Zitat:** „Activates the Constraint command.“
* **Weiteres Zitat:** „Activates the Place Component command.“
* **Weiteres Zitat:** „Activates the Create Component command.“
* **Weiteres Zitat:** „Activates the Move Component command.“
* **Weiteres Zitat:** „Activates the Rotate Component command.“

### Beleg: Vordefinierte Kurzbefehle Browser und Baugruppe (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „Wenn ein Browser-Knoten den Fokus hat, wird der Umbenennungsmodus aufgerufen.“
* **Weiteres Zitat:** „Fügt eine Baugruppenabhängigkeit hinzu“

### Beleg: Predefined Shortcuts Browser and Assembly (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „When a browser node has focus, enters rename mode.“
* **Weiteres Zitat:** „Adds an assembly constraint.“

### Beleg: Abhängigkeit platzieren und Zusammenfügen Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-198F05E4-2973-4818-8F25-A0B8B9796D07.htm
* **Wörtliches Zitat:** „Baugruppenabhängigkeiten entfernen Freiheitsgrade zwischen zwei ausgewählten Komponenten und positionieren die Komponenten relativ zueinander.“
* **Weiteres Zitat:** „Registerkarte Zusammenfügen Gruppe Beziehungen Zusammenfügen“

### Beleg: Place Constraint and Assemble Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-198F05E4-2973-4818-8F25-A0B8B9796D07.htm
* **Wörtliches Zitat:** „Assembly constraints remove degrees of freedom between two selected components, positioning them relative to one another.“
* **Weiteres Zitat:** „Assemble A mini toolbar displays in the graphics window instead of a dialog.“

### Beleg: Abhängigkeiten Registerkarte Baugruppe (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-EBD2C784-0E71-452A-B5F2-22738D22D45A.htm
* **Wörtliches Zitat:** „Die Abhängigkeit Passend positioniert Komponenten Fläche an Fläche oder nebeneinander liegend mit fluchtenden Flächen.“
* **Weiteres Zitat:** „Fluchtende Abhängigkeit“
* **Weiteres Zitat:** „Winkelabhängigkeit“
* **Weiteres Zitat:** „Mit der Abhängigkeit Tangential wird zwischen Flächen, Ebenen, Zylindern, Kugeln oder Kegeln eine Berührung am Tangentialpunkt festgelegt.“
* **Weiteres Zitat:** „Abhängigkeit Einfügen“

### Beleg: Place Constraint Assembly Tab (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-EBD2C784-0E71-452A-B5F2-22738D22D45A.htm
* **Wörtliches Zitat:** „A tangent constraint removes one degree of linear translation.“
* **Weiteres Zitat:** „The Insert constraint positions a bolt shank in a hole.“

### Beleg: Gelenkbeziehungen Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-21DC3336-5C51-42C1-90FB-4299CD66E0C6.htm
* **Wörtliches Zitat:** „Jeder Gelenktyp definiert die Position und die Bewegung der ausgewählten Komponenten vollständig.“

### Beleg: Joint Relationships Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-21DC3336-5C51-42C1-90FB-4299CD66E0C6.htm
* **Wörtliches Zitat:** „Each joint type fully defines the location and motion of the selected components.“

### Beleg: Erstellen von Gelenken Gelenktypen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-6AA68E8F-7C97-4806-8483-3941DE915E70.htm
* **Wörtliches Zitat:** „Starr Positioniert eine Komponente und entfernt alle Freiheitsgrade“
* **Weiteres Zitat:** „Drehung Positioniert eine Komponente und legt einen Drehfreiheitsgrad fest.“
* **Weiteres Zitat:** „Verschiebbar Positioniert eine Komponente und legt einen Übersetzungsfreiheitsgrad fest“
* **Weiteres Zitat:** „Zylindrisch Positioniert eine Komponente und legt einen Translations- und einen Drehfreiheitsgrad fest“
* **Weiteres Zitat:** „Eben Positioniert eine Komponente und legt zwei Translations- und einen Drehfreiheitsgrad“
* **Weiteres Zitat:** „Kugel Positioniert eine Komponente und legt drei Drehfreiheitsgrade fest“

### Beleg: Create Joints Joint Types (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-6AA68E8F-7C97-4806-8483-3941DE915E70.htm
* **Wörtliches Zitat:** „Rigid Positions a component and removes all degrees of freedom.“
* **Weiteres Zitat:** „Rotational Positions a component and specifies one rotational degree of freedom.“
* **Weiteres Zitat:** „Slider Positions a component and specifies one translational degree of freedom.“
* **Weiteres Zitat:** „Cylindrical Positions a component and specifies one translational and one rotational degree of freedom.“
* **Weiteres Zitat:** „Planar Positions a component and specifies two translational and one rotational degree of freedom“
* **Weiteres Zitat:** „Ball Positions a component and specifies three rotational degrees of freedom.“

### Beleg: Komponente platzieren Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-2C55B507-C204-4AD7-8804-BA9461306616.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Zusammenfügen Gruppe Komponente Platzieren“

### Beleg: Place Component Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-2C55B507-C204-4AD7-8804-BA9461306616.htm
* **Wörtliches Zitat:** „On the ribbon, click Assemble tab Component panel Place“

### Beleg: Komponente in der Baugruppe erstellen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-FBBE5A60-AE37-4087-81D7-AA91330D1B01.htm
* **Wörtliches Zitat:** „Registerkarte Zusammenfügen Gruppe Komponente Erstellen“

### Beleg: Create Component Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-FBBE5A60-AE37-4087-81D7-AA91330D1B01.htm
* **Wörtliches Zitat:** „Assemble tab Component panel Create“

### Beleg: Freie Verschiebung Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-9796C22B-23C1-4D69-BC2E-54056E46F255.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Zusammenfügen Gruppe Position Freie Verschiebung“

### Beleg: Free Move Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-9796C22B-23C1-4D69-BC2E-54056E46F255.htm
* **Wörtliches Zitat:** „On the ribbon, click Assemble tab Position panel Free Move“

### Beleg: Freie Drehung Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-7EAE9DFD-899A-4FD1-B63F-92DD41D0A916.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Zusammenfügen Gruppe Position Freie Drehung“

### Beleg: Free Rotate Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-7EAE9DFD-899A-4FD1-B63F-92DD41D0A916.htm
* **Wörtliches Zitat:** „On the ribbon, click Assemble tab Position panel Free Rotate“

### Beleg: Rechteckige Anordnung Baugruppe (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-CF627358-120F-4142-A9D0-13217BD3432D.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Zusammenfügen Gruppe Anordnung Anordnung“

### Beleg: Rectangular Pattern Assembly (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-CF627358-120F-4142-A9D0-13217BD3432D.htm
* **Wörtliches Zitat:** „On the ribbon, click Assemble tab Pattern panel Pattern“

### Beleg: Baugruppenkomponenten spiegeln (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-C5B3D3DF-27B3-4B4C-9058-A949138D8B8A.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Zusammenfügen Gruppe Anordnung Spiegeln“

### Beleg: Mirror Assembly Components (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-C5B3D3DF-27B3-4B4C-9058-A949138D8B8A.htm
* **Wörtliches Zitat:** „On the ribbon, click Assemble tab Pattern panel Mirror“

### Beleg: Stückliste Gruppe Verwalten (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-6C58657F-C902-433F-9AA6-22A2ACA09F16.htm
* **Wörtliches Zitat:** „Registerkarte Zusammenfügen Gruppe Verwalten Stückliste“

### Beleg: Bill of Materials Manage Panel (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-6C58657F-C902-433F-9AA6-22A2ACA09F16.htm
* **Wörtliches Zitat:** „Assemble tab Manage panel Bill of Materials“

### Beleg: Kollision analysieren Prüfen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-80DED0A6-AC65-4C7C-AD85-0144EE6DAB5B.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Prüfen Gruppe Kollision Kollision analysieren“

### Beleg: Analyze Interference Inspect (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-80DED0A6-AC65-4C7C-AD85-0144EE6DAB5B.htm
* **Wörtliches Zitat:** „On the ribbon, click Inspect tab Interference panel Analyze Interference“

### Beleg: Modellbrowser Bauteilende EOP (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-69196418-14DF-4128-B4F3-581FFC994C78.htm
* **Wörtliches Zitat:** „Suchen Sie unten im Browser das Symbol Bauteilende (oder Element), und ziehen Sie es nach oben, um das Modell in ein früheres Stadium zurückzusetzen.“

### Beleg: Model Browser End of Part EOP (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-69196418-14DF-4128-B4F3-581FFC994C78.htm
* **Wörtliches Zitat:** „Find the End of Part (or End of Feature) symbol at the bottom of the browser, and drag it up to“

### Beleg: Sichtbarkeit über Kontextmenü (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-BA193171-FAFC-4150-9222-CC43D8D4AA54.htm
* **Wörtliches Zitat:** „Wählen Sie im Browser oder in der Anzeige mindestens ein Arbeitselement, eine Skizze oder andere Elemente aus. Klicken Sie mit der rechten Maustaste, und deaktivieren Sie die Sichtbarkeit.“

### Beleg: Visibility via Context Menu (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-BA193171-FAFC-4150-9222-CC43D8D4AA54.htm
* **Wörtliches Zitat:** „In the browser or the display, select one or more work features, sketches, or other elements. Right-click and clear the visibility check mark to turn off.“
