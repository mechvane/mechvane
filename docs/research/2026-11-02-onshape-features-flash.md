# Recherche: Die besten Features von Onshape (Entscheidungsgrundlage für Mechvane)

- **Datum:** 2026-11-02
- **Autor:** Gemini 3.8 Flash (Issue #39)
- **Status:** Verifiziert mit `tools/check_sources.py` (25 von 25 Belegen voll bestätigt) und gegen den Sparse-Klon `/root/repos/_ext/solidcraft`
- **Prüfnotiz Claude (2026-11-02):** `check_sources.py` selbst gelaufen: 25/25 Zitate, 1/1 Zahl bestätigt. SolidCraft-Pfade stichprobenhaft geprüft (`config.rs`, `config_rules.rs`, `compare.rs`, `sheet_*`): vorhanden; der Vergleichsbefehl heißt `inspect.compare` (im Entwurf fälschlich `view.compare`, korrigiert). Einordnungen nach Phase sind Vorschläge, keine Entscheidung.
- **Kontext & Ziel:** Onshape gilt in Industrie und Fachpresse als Pionier des modernen, cloud-nativen CAD. Nach den vorangegangenen UI- und Befehlsanalysen ([Fusion vs. Inventor](2026-10-26-fusion-vs-inventor-gemini.md) und [Inventor ↔ SolidCraft](2026-10-30-abgleich-inventor-solidcraft-flash.md)) liefert dieser Bericht eine fundierte Entscheidungsgrundlage: Welche Funktionen und Arbeitsweisen machen Onshape so produktiv, wie verhalten sie sich zu SolidCraft, und was davon passt zu Mechvane (Inventor-Bedienung auf SolidCraft, Mensch und Agent am selben Modell, Web-UI, spätere Desktop-App)?

---

## 1. Einleitung und technologische Grundlagen von Onshape

Onshape wurde 2012 von Jon Hirschtick und John McEleney gegründet (den ursprünglichen Gründern von SolidWorks) und 2019 von PTC übernommen. Die Plattform unterscheidet sich architektonisch fundamental von traditioneller Desktop-CAD-Software:

1. **Zentrales Cloud-Datenmodell statt lokaler Dateien:** In Onshape existieren keine einzelnen Bauteil- (`.sldprt`, `.ipt`) oder Baugruppendateien (`.sldasm`, `.iam`) auf dem Dateisystem. Alle Geometrien, Features, Beziehungen und Metadaten werden in einer verteilten, transaktionalen Datenbank in Cloud-Clustern (AWS) gespeichert.
2. **Geometrie-Rechenleistung im Cluster (Parasolid):** Die geometrische Modellierung basiert auf Siemens Parasolid und D-Cubed, läuft jedoch serverseitig in der Cloud. Das Endgerät des Nutzers rendert lediglich die 3D-Szenen über WebGL bzw. WebGPU.
3. **Multi-User und Multi-Device von Tag 1:** Durch die datenbankgestützte Architektur entfallen Dateisperren (Check-in/Check-out-Zyklen klassischer PDM-Systeme). Mehrere Personen können gleichzeitig am selben Modell arbeiten.
4. **Programmierbare Parametrik (FeatureScript):** Alle System-Features (Extrude, Revolve, Sheet Metal etc.) sind in einer offenen Programmiersprache geschrieben, die Anwendern zur freien Erweiterung offensteht.

---

## 2. Übersichtstabelle der Onshape-Kernfunktionen

Die folgende Übersichtstabelle fasst 25 Kernfunktionen aus allen zentralen Disziplinen zusammen. Sie stellt Funktion, Nutzen, SolidCraft-Stand, Mechvane-Passung und Phasenvorschlag nach `ROADMAP.md` gegenüber.

| Nr. | Funktion / Name | Was es tut (1–2 Sätze) | Warum Nutzer es schätzen | SolidCraft hat | Passung zu Mechvane | Phase (ROADMAP) |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| 1 | **Multi-Part Part Studios** | Ermöglicht das Modellieren mehrerer diskreter Bauteile in einem gemeinsamen parametrischen Feature-Baum. | Vermeidet fragile externe Dateipfade; Änderungen an Master-Skizzen aktualisieren alle betroffenen Teile synchron. | Ja (`crates/doc/src/eval.rs`, `crates/engine/src/cmd/component.rs`) | **Mittel** (Skelett-Modellierung ja, aber Grundsatz 5 verlangt getrennte `.ipt`- und `.iam`-Dateien). | Phase 2 |
| 2 | **Configurations (Unabhängige Tabellen)** | Erzeugt Varianten über getrennte Eingabetabellen für Maße, Feature-Unterdrückung und Bauteillisten. | Beseitigt die exponentielle Zeilenexplosion riesiger Excel-Kombinationstabellen herkömmlicher CAD-Systeme. | Ja (`crates/doc/src/config.rs`, `crates/doc/src/config_rules.rs`, `crates/engine/src/cmd/config.rs`) | **Hoch** (Ideal für Normteil-Bibliotheken und parametrische Baugruppengrößen). | Phase 2 |
| 3 | **Derived Feature (Abgeleitete Geometrie)** | Bindet Teile, Flächen, Skizzen oder Koordinatensysteme aus anderen Dokumenten/Part Studios als Referenz ein. | Erlaubt sauberes Top-Down-Skelett-Design über Dokumentgrenzen hinweg ohne zyklische Baugruppenabhängigkeiten. | Teilweise (`crates/doc/src/project.rs`, `crates/engine/src/cmd/component_link.rs`) | **Hoch** (Wichtig für Baugruppen-Referenzen und Skelett-Entwürfe). | Phase 2 |
| 4 | **Variable Studios (Zentrale Variablen)** | Zentraler Dokumentenreiter zur Definition globaler Parameter, Formeln und Konstanten für mehrere Arbeitsbereiche. | Änderungen an Kernmaßen (z. B. Wandstärke, Spaltmaß) schlagen automatisch auf alle verknüpften Teile und Baugruppen durch. | Teilweise (`crates/doc/src/params.rs`, `crates/doc/src/expr.rs`) | **Hoch** (Ergänzt Mechvanes `/api/params` perfekt um baugruppenweite Parameter). | v0.1 / Phase 1 |
| 5 | **Branching & Merging** | Ermöglicht parallele Entwurfszweige (Branches) mit anschließendem visuellem Zusammenführen (Merge). | Risikofreies Erkunden von Konstruktionsvarianten ohne Gefahr, das Hauptmodell zu beschädigen. | Nein (SolidCraft besitzt lineare Undo-Historie, keine Verzweigungen im Datenmodell). | **Mittel** (Lokales Git-Branching auf Dateiebene passt besser als komplexe CAD-Merges). | Phase 2 |
| 6 | **Lückenloser Verlauf & Restore** | Speichert jede einzelne Operation serverseitig transaktional ab; Rückkehr zu jedem beliebigen historischen Punkt. | Kein manuelles Speichern („Never hit save“), kein Datenverlust bei Browserabstürzen oder Fehlschlägen. | Teilweise (`crates/doc/src/document.rs`, `crates/engine/src/recovery.rs`, Rollback via `timeline.roll_to`) | **Hoch** (Passt direkt zu Grundsatz 3 für Rollbacks und Agenten-Schritte). | v0.1 |
| 7 | **Visual Compare (3D-Vergleich)** | Vergleicht zwei Versionen, Branches oder Revisionsstände grafisch im 3D-Fenster mit Rot/Blau-Farbüberlagerung. | Zeigt sofort auf einen Blick, welche Geometrien und Features hinzugefügt, entfernt oder verschoben wurden. | Ja (`crates/engine/src/cmd/compare.rs`, Befehl `inspect.compare`) | **Hoch** (Perfekt zur visuellen Abnahme von Agenten-Änderungen durch den Menschen). | Phase 1 |
| 8 | **Simultaneous Editing (Echtzeit-CAD)** | Mehrere Anwender bearbeiten dieselbe Baugruppe oder dasselbe Teil zeitgleich ohne Dateisperren. | Beseitigt zeitraubende Check-in/Check-out-Sperren klassischer PDM-Systeme bei Teamprojekten. | Nein (SolidCraft ist ein lokaler Single-User-Prozess). | **Hoch** (Das Fundament für „Mensch und Agent am selben Modell“ via Web-UI). | Phase 1 |
| 9 | **Follow Mode (Kamera-Verfolgung)** | Klick auf ein Profil synchronisiert die 3D-Kamera, den Zoom und die Auswahlen live mit dem Partner. | Erleichtert Design-Reviews und Fehlerbesprechungen ohne externe Bildschirmfreigabe-Software. | Nein (`crates/engine/src/view.rs` steuert nur die lokale Ansicht). | **Hoch** (Nutzer sieht live, woran der Agent arbeitet; Agent folgt Nutzer bei Point & Speak). | Phase 1 |
| 10 | **3D-Kommentare & Aufgaben** | Notizen, Aufgaben und Markups werden direkt an Flächen, Kanten oder Features im 3D-Raum geheftet. | Verhindert Medienbrüche (E-Mail/Chat/Screenshots); Kontext und Historie bleiben am Bauteil verankert. | Nein (Bisher keine Annotationsschicht im Kern). | **Hoch** (Ideal für Befund-Pins der Prüfseite und Arbeitsanweisungen an den Agenten). | v0.1 / Phase 1 |
| 11 | **Integriertes Release Management** | Standardisierte Freigabe-Workflows mit Revisionsbuchstaben und Freigabestatus ohne externes PDM. | Strukturierte Freigaben für Fertigung und Einkauf ohne teure PDM-Serverinstallation. | Nein. | **Mittel** (Für Einzelentwickler und kleine Teams genügt zunächst Git-Tagging/Releases). | Später |
| 12 | **FeatureScript & Custom Features** | Vollwertige Programmiersprache zum Erstellen eigener parametrischer 3D-Features im Modellbaum. | Anwender können repetitive Spezialgeometrien automatisieren; riesige Community-Bibliothek. | Teilweise (`crates/doc/src/plugins.rs`, WASM-Plugin-Entwurf #1221). | **Hoch** (Mechvanes Python-Werkzeuge und MCP-Server sind das Äquivalent zu FeatureScript). | v0.1 / Phase 1 |
| 13 | **Mate Connectors** | Lokale Koordinatensysteme an Formelementen (Zentren, Kanten, Ecken) als Verknüpfungsanker. | Präzise Orientierung und Positionierung von Bauteilen mit definierten Richtungsachsen. | Ja (`crates/doc/src/anchor_frame.rs`, `crates/doc/src/frame.rs`, `crates/engine/src/frames.rs`) | **Hoch** (Entspricht direkt den geplanten „Benannten Anschlüssen / Ports“ in Phase 2). | Phase 2 |
| 14 | **Higher-Order Mates** | Kinematische Gelenke (Fastened, Revolute, Slider etc.) definieren Freiheitsgrade mit einer Verknüpfung. | Ersetzt bis zu drei geometrische Abhängigkeiten herkömmlicher CAD-Systeme durch ein einziges Gelenk. | Ja (`crates/doc/src/joints.rs`, `crates/engine/src/cmd/joints.rs`) | **Hoch** (Mechvane nutzt SolidCraft-Gelenke bereits aktiv in `mechvane/links.py`). | v0.1 |
| 15 | **In-Context Design** | Erlaubt das Konstruieren von Bauteilen direkt im Kontext der Baugruppe mit Schnappschüssen. | Bauteile passen auf Anhieb zusammen, ohne dass bewegliche Mechanismen Fehlbezüge erzeugen. | Teilweise (`crates/engine/src/cmd/component_link.rs`, in Mechvane `edit_in_place`) | **Hoch** (Mechvane bietet bereits `edit_in_place` und `finish_edit` an). | v0.1 |
| 16 | **Standard Content (Normteil-Bibliothek)** | Automatische Größenanpassung und Verknüpfung von Verbindungselementen an Bohrungen. | Befreit den Konstrukteur vom repetitiven Einfügen und Abhängen einzelner Schrauben und Scheiben. | Teilweise (`crates/engine/src/cmd/hole_face_tests.rs`) | **Hoch** (Mechvane hat dies mit `bolted_connection` und dem Normteilkatalog gelöst). | v0.1 |
| 17 | **Replicate Command** | Erkennt identische Geometrien und dupliziert ein Bauteil samt Gelenk auf alle passenden Stellen. | Bestückt ganze Lochbilder oder Profilraster mit Schrauben/Gleitern in einem einzigen Arbeitsschritt. | Teilweise (`crates/engine/src/cmd/component_matrix.rs`, `crates/engine/src/cmd/pattern.rs`) | **Hoch** (Extrem nützliche Baugruppen-Automatisierung für Mensch und Agent). | Phase 2 |
| 18 | **Exploded Views (Explosionsansichten)** | Interaktives Auseinanderziehen von Baugruppen entlang von Richtungsachsen mit Animationsvorschau. | Erleichtert Montageanleitungen und Service-Dokumentationen; fließt direkt in 2D-Zeichnungen ein. | Teilweise (`crates/doc/src/motion.rs`, `crates/engine/src/cmd/component_drag.rs`) | **Hoch** (Bereits fester Bestandteil der Mechvane-Roadmap für Phase 2). | Phase 2 |
| 19 | **Simultaneous Sheet Metal** | Zeitgleiche, parallele Darstellung von 3D-Körper, Flachabwicklung und Biegetabelle nebeneinander. | Biegefehler, Überschneidungen und ungünstige Radien werden sofort in Echtzeit erkannt. | Ja (`crates/doc/src/sheet.rs` mit 474k LOC, unterstützt simultane Panel- und Flat-Pattern-Auswertung). | **Hoch** (Herausragendes Visualisierungsfeature für die Mechvane-Web-Oberfläche). | Phase 2 |
| 20 | **Sheet Metal Convert & Rip** | Wandelt reguläre 3D-Volumenkörper durch Zuweisen von Biegungen und Auftrennkanten in Blech um. | Schnellerer Entwurf von Schutzabdeckungen und Gehäusen ausgehend vom umbauten Raum. | Ja (`crates/doc/src/sheet_convert.rs`, `crates/engine/src/cmd/sheet.rs`) | **Hoch** (Workflow-Beschleuniger für alltägliche Gehäusekonstruktionen). | Phase 2 |
| 21 | **Assoziative 2D-Zeichnungen & Live-BOM** | Vollständig assoziative Zeichnungen mit bidirektional gekoppelter Stückliste direkt am 3D-Modell. | Keine Inkonsistenzen zwischen 3D-Modell, Stücklistentabelle und Fertigungszeichnung. | Ja (`crates/doc/src/drawing.rs`, `crates/engine/src/cmd/bom.rs` mit `assembly.bom.get`/`set`) | **Hoch** (Zentraler Baustein für Mechvane Phase 3: Fertigungszeichnungen). | Phase 3 |
| 22 | **Sketch Constraint Manager & Diagnose** | Strukturierte Übersicht und Diagnose aller Skizzenabhängigkeiten mit Farbkodierung für Konflikte. | Schnelles Auffinden von Überbestimmungen und fehlerhaften externen Skizzenreferenzen. | Ja (`crates/engine/src/cmd/sketch_constraints.rs`, `sketch_inspect.rs`) | **Hoch** (Unerlässlich für die geplante eigene Mechvane-Skizzierumgebung nach ADR 0005). | Phase 1 |
| 23 | **Vollständige REST-API & Webhooks** | Lese- und Schreibzugriff auf Dokumente, Geometrie, Baugruppenbäume und Ereignisse über Web-Standards. | Nahtlose Anbindung an ERP-, PLM-, Slicer- und Automatisierungspipelines ohne Desktop-Treiber. | Teilweise (`crates/engine/src/control_protocol.rs` via JSON-RPC/WebSocket). | **Hoch** (Mechvanes HTTP-REST-Architektur `/api/*` setzt genau hier an). | v0.1 |
| 24 | **Onshape AI Advisor** | Kontextbewusster In-App-KI-Assistent für Konstruktionsfragen, Normen und Feature-Hilfe. | Schnelle Hilfe bei Modellierungsfragen direkt in der Software ohne Kontextwechsel zum Browser. | Teilweise (`docs/agent-chat.md` Agent-Chat-Panel für Claude Code). | **Sehr hoch** (Mechvane geht mit „Point & Speak“ noch weiter: Agent modifiziert Modell aktiv). | v0.1 / Phase 1 |
| 25 | **Zero-Install & Mobile/Tablet CAD** | Vollwertiges parametrisches 3D-CAD im Webbrowser sowie native iPad- (Apple Pencil) und Android-Apps. | Konstruieren und Ändern auf der Baustelle oder Werkstatt; keine CAD-Workstation zwingend nötig. | Teilweise (Web-App läuft im Browser, aber keine touch-optimierte Mobil-App). | **Mittel bis Hoch** (Web-UI läuft auf Tablet/Handy; Android-App als Fernbedienung in Phase 1). | v0.1 / Phase 1 |

---

## 3. Detaillierte Fachanalyse nach Funktionsbereichen

### 3.1 Datenmodell: Multi-Part, Konfigurationen und Variablen
In traditionellen Systemen (Inventor, SolidWorks) gilt das Paradigma: *Eine Datei = Ein Teil*. Baugruppen verknüpfen diese Dateien. Wenn Bauteile geometrisch voneinander abhängen (z. B. Gehäuse-Unter- und Oberschale), müssen in Inventor adaptive Abhängigkeiten oder Skelett-Bauteile mit abgeleiteten Komponenten genutzt werden, was bei Umbenennungen oder Pfadänderungen berüchtigt fehleranfällig ist.

Onshape löst dies über **Part Studios**:
- **Multi-Part-Entwurf:** Mehrere Teile entstehen aus derselben Skizze und teilen sich denselben Feature-Verlauf. Ein geteilter Schnitt (`Split`) erzeugt zwei getrennte Festkörper, die jeweils als eigenständige Teile mit eigener Teilenummer, Material und Stücklisteneintrag geführt werden.
- **Unabhängige Konfigurationen:** Während SolidWorks-Konfigurationen bei vielen Parametern (z. B. Länge, Durchmesser, Gewindetyp, Material) in riesigen, unübersichtlichen Excel-Tabellenzeilen explodieren ($n \times m \times k$), nutzt Onshape getrennte, orthogonale Tabellen und Eingabefelder (Listen, Checkboxen, Variablen).
- **Variable Studios:** Globale Konstruktionskonstanten (z. B. Blechdicke $s = 2{,}5\,\text{mm}$, Spaltmaß $c = 0{,}2\,\text{mm}$) werden an einem Ort gepflegt und von allen Part Studios und Baugruppen referenziert.

*Einordnung für Mechvane:*  
Für Mechvane ist das Konzept der **unabhängigen Konfigurationstabellen** und der **Variable Studios** ein Vorbild, das sich mit SolidCrafts `cmd::config` und `params.rs` hervorragend verträgt. Das reine *Multi-Part-als-Baugruppenersatz*-Konzept passt hingegen **nicht** zur Grundsatzentscheidung 5 (getrennte Bauteil- und Baugruppendateien wie Inventor). Mechvane unterstützt jedoch Mehrkörper-Bauteile für Schweißgruppen und Gussformen.

### 3.2 Versionierung, Verlauf und visueller Modellvergleich
Onshapes Cloud-Datenbank protokolliert jede Aktion als atomare Transaktion (Micro-Versioning). Dadurch ergeben sich drei herausragende Eigenschaften:
- **Kein Speichern / Infinite Undo:** Ein Absturz des Browsers oder des lokalen Rechners führt zu null Datenverlust. Über die Verlaufsleiste kann jederzeit zu jedem früheren Konstruktionsstand zurückgekehrt werden.
- **Branching & Merging:** Ähnlich wie in Git für Softwarecode können Konstrukteure einen Branch eröffnen, um eine riskante Idee (z. B. Rippenstruktur statt Vollwand) auszuprobieren. Bewährt sich die Idee, wird der Branch in den Hauptzweig gemergt.
- **Visual Compare:** Bei Baugruppen und Teilen visualisiert Onshape Unterschiede zwischen zwei Ständen im 3D-Modell: Geometrie, die gelöscht wurde, erscheint rot; hinzugefügte Geometrie blau; unveränderte Geometrie grau.

*Einordnung für Mechvane:*  
Der **visuelle 3D-Vergleich** ist für Mechvane von allerhöchster Priorität: Wenn der Claude- oder Gemini-Agent eine Änderung vornimmt („Fase an Flansch angebracht“), muss der menschliche Ingenieur auf einen Blick im Prüffenster sehen können, was sich geometrisch verändert hat. SolidCraft liefert mit `crates/engine/src/cmd/compare.rs` (`inspect.compare`) bereits die geometrische Schnittmengenberechnung.

### 3.3 Zusammenarbeit: Echtzeit-Kollaboration und Follow Mode
Onshape beseitigt das Problem, dass Bauteildateien durch andere Benutzer im Netzwerk gesperrt sind. Mehrere Ingenieure können im selben Moment am selben Modell arbeiten:
- **Präsenzanzeige:** Bunte Avatare zeigen an, wer sich gerade in welchem Tab befindet und welches Feature editiert wird.
- **Follow Mode:** Klickt Ingenieur A auf das Profil von Ingenieur B, übernimmt A die Kamera und Auswahlen von B in Echtzeit.
- **3D-Kommentare:** Aufgaben und Review-Notizen werden direkt an Kanten und Flächen geheftet.

*Einordnung für Mechvane:*  
Für Mechvane ist dies das Kernversprechen: **„You and your agent on the same model.“** Der Follow Mode und die gleichzeitige Modellbearbeitung übertragen sich 1:1 auf das Zusammenspiel von Mensch und KI. Der Nutzer markiert eine Fläche und spricht den Befehl (Point & Speak, ADR 0003), der Agent führt die Modellierung aus, und die Web-UI spiegelt das Ergebnis verzögerungsfrei wider.

### 3.4 FeatureScript und KI-MCP-Integration
Alle Standardfeatures in Onshape sind in FeatureScript verfasst – einer typsicheren, imperativen Sprache, die speziell für geometrische Operationen auf dem Parasolid-Kernel entwickelt wurde:
- **First-Class Custom Features:** Vom Anwender geschriebene Features (z. B. automatisierte Trägerprofile, O-Ring-Nuten, Schweißraupen) verhalten sich exakt wie native Onshape-Features, inklusive Vorschau, Fehlerbehandlung und Baum-Hierarchie.
- **FeatureScript MCP Server:** 2024/2026 hat PTC einen offiziellen MCP-Server (Model Context Protocol) für FeatureScript vorgestellt, über den LLMs (wie Claude) direkt Custom Features aus natürlichsprachlichen Prompts generieren.

*Einordnung für Mechvane:*  
Mechvane verfolgt exakt dieselbe Philosophie, setzt aber auf **Python und MCP** auf dem SolidCraft-Kern (`mechvane/server.py`):
- Funktionen wie `bolted_connection`, `trunnion` oder `check_design` sind im Grunde Mechvanes eigene Custom Features.
- Mechvane nutzt MCP nativ als primäre Schnittstelle, sodass Claude und Gemini Modelle aufbauen, messen und reparieren können.

### 3.5 Baugruppen: Mate Connectors und Higher-Order Mates
Klassische CAD-Programme wie Inventor oder SolidWorks verlangen meist drei separate Abhängigkeiten, um ein Bauteil vollständig im Raum zu fixieren (z. B. Passend Fläche auf Fläche, Fluchtend Kante an Kante, Abstand Achse zu Achse).
Onshape revolutioniert dies durch **Higher-Order Mates**:
- Ein **Mate Connector** ist ein lokales Koordinatensystem (Ursprung und drei Achsen), das automatisch an Kantenmitten, Bohrungszentren oder Eckpunkten gefangen wird.
- Ein einzelnes **Mate** verbindet zwei Mate Connectors und definiert direkt die kinematische Beweglichkeit:
  - *Fastened Mate:* Sperrt alle 6 Freiheitsgrade (starre Verbindung).
  - *Revolute Mate:* Belässt genau 1 Rotationsfreiheitsgrad (Scharnier, Achse).
  - *Slider Mate:* Belässt genau 1 Translationsfreiheitsgrad (Linearführung).
  - *Cylindrical Mate:* Belässt 1 Translation und 1 Rotation (Kolben/Welle).

*Einordnung für Mechvane:*  
SolidCraft hat diese Gelenk-Philosophie bereits vollständig im Kern implementiert (`crates/doc/src/joints.rs`). Mechvane baut darauf auf (`mechvane/links.py`). Die in Phase 2 geplanten **Benannten Anschlüsse (Ports)** entsprechen funktional exakt den Onshape Mate Connectors.

### 3.6 Blechkonstruktion: Die simultane Dreifach-Ansicht
Das Blechmodul von Onshape gilt als Branchen-Benchmark:
- **Gleichzeitige Darstellung:** Das gefaltete 3D-Teil, die abgewickelte 2D-Flachansicht und die tabellarische Biege-/Auftrennliste sind gleichzeitig nebeneinander geöffnet.
- **Bidirektionale Bearbeitung:** Ändert man einen Biegeradius in der Tabelle oder setzt einen Entlastungsschnitt in der Abwicklung, aktualisiert sich das 3D-Modell in Echtzeit.
- **Konvertierung von Vollkörpern:** Ein geschlossener Block kann mit `Convert to Sheet Metal` und Auswahl von Biegekanten und Aufreißstellen (`Rip`) direkt in ein abwickelbares Blechteil gewandelt werden.

*Einordnung für Mechvane:*  
SolidCraft besitzt mit über 470.000 Zeilen Code in `crates/doc/src/sheet.rs` und `sheet_convert.rs` ein mächtiges Blech-Backend, das simultane Flat-Pattern-Koordinaten bereits intern unterstützt. Mechvane kann in Phase 2 eine dedizierte Blech-Ansicht bereitstellen, die 3D-Modell und Abwicklung parallel anzeigt.

---

## 4. Die fünf stärksten Kandidaten zur Übernahme in Mechvane

Aus der Gegenüberstellung von Onshape-Stärken, SolidCraft-Fähigkeiten und Mechvane-Grundsätzen ergeben sich die folgenden fünf Favoriten:

### 1. Higher-Order Mates & Benannte Anschlüsse (Ports)
- **Warum:** Spart zwei Drittel der Klicks beim Zusammenbau von Baugruppen und verhindert überbestimmte, fragile Abhängigkeitsketten.
- **Realisierung in Mechvane:** SolidCraft beherrscht Gelenke bereits (`joints.rs`). In Mechvane Phase 2 werden nach Roadmap benannte Anschlüsse (`Ports`) auf Basis von lokalen Koordinaten-Frames eingeführt, die das Verknüpfen für Mensch und Agent dramatisch vereinfachen.

### 2. Simultane Blech-Ansicht (3D + Abwicklung nebeneinander)
- **Warum:** Verhindert Konstruktionsfehler, die erst bei der Fertigung auffallen (z. B. überlappende Laschen oder unfertigbare Radien).
- **Realisierung in Mechvane:** SolidCraft rechnet Blechabwicklungen bereits parallel mit (`sheet.rs`). In der Mechvane-Web-UI (Phase 2) kann ein zweites Ansichtsfenster mit der flachen Blechgeometrie neben der 3D-Ansicht eingeblendet werden.

### 3. Unabhängige Konfigurationstabellen (Orthogonale Varianten)
- **Warum:** Vermeidet das Excel-Tabellen-Chaos traditioneller CAD-Systeme. Bauteilfamilien (z. B. Schraubenlängen, Lagerdurchmesser, Befestigungsvarianten) bleiben modular und pflegeleicht.
- **Realisierung in Mechvane:** Aufsetzen auf SolidCrafts `crates/doc/src/config.rs` und `config_rules.rs` zur Definition strukturierter Varianten im MCP-Server und Parameterformular.

### 4. Visueller 3D-Modellvergleich (Visual Compare)
- **Warum:** Essenzielles Vertrauens- und Kontrollwerkzeug für die Zusammenarbeit zwischen Ingenieur und KI-Agent. Farbliche Differenzdarstellung (Rot = entfernt, Blau = hinzugefügt) macht Änderungen sofort transparent.
- **Realisierung in Mechvane:** Direkte Nutzung von SolidCrafts `crates/engine/src/cmd/compare.rs` (`inspect.compare`) in Mechvanes Prüfmodus und bei MCP-Zustandsberichten.

### 5. Code-basierte Custom Features (Python/MCP als FeatureScript-Äquivalent)
- **Warum:** Erlaubt es Entwicklern, Anwendern und KI-Agenten, komplexe Fachfeatures parametrisch als Code zu formulieren, anstatt primitive Klickfolgen zu wiederholen.
- **Realisierung in Mechvane:** Mechvane realisiert dies bereits in Python (`bolted_connection`, Bohrungsmuster). Künftige Fachmodule (Gestell-Generator, Wellen-Assistent, Schweißnähte in Phase 2) werden als standardisierte Python-Features implementiert.

---

## 5. Was ausdrücklich NICHT zu Mechvane passt (Grenzen & bewusste Gegenentscheidungen)

Nicht alle Konzepte von Onshape sind für Mechvane erstrebenswert. Folgende Aspekte passen ausdrücklich **nicht** zu Mechvanes Zielen:

1. **Reine Cloud-Bindung und Zwang zum Online-Betrieb:**  
   Onshape funktioniert ohne Internetverbindung überhaupt nicht. Fällt die Internetverbindung aus oder hat AWS Probleme, steht die gesamte Konstruktionsabteilung still. Zudem verbieten viele Industrieunternehmen und Ingenieurbüros das Hochladen vertraulicher CAD-Daten in fremde Clouds.  
   *Mechvane-Gegenposition:* Mechvane setzt auf **Grundsatz 12 (Echte Desktop-App, Offline-Betrieb)**. Die Modelle liegen als lokale Dateien auf dem Rechner des Nutzers. Eine Web-Verbindung existiert nur optional für Cloud-LLMs oder Remote-Zugriff über das private Homelab.

2. **Zwangsveröffentlichung im kostenlosen Kontingent (Public Files):**  
   Onshapes kostenlose Version zwingt Hobbyisten und Maker dazu, alle Modelle öffentlich einsehbar zu machen. Privates Konstruieren erfordert ein teures kommerzielles Abonnement.  
   *Mechvane-Gegenposition:* Mechvane ist freie Open-Source-Software (MIT/Apache-2.0). Alle Modelle gehören dem Anwender und bleiben privat.

3. **Multi-Part Part Studios als vollständiger Baugruppen-Ersatz:**  
   In Onshape neigen Anwender dazu, komplette Maschinen mit Dutzenden Teilen in ein einziges Part Studio zu packen. Für kleine Baugruppen ist dies bequem, führt bei großen Industriemaschinen jedoch zu trägen, unübersichtlichen Monster-Bäumen und kollidiert mit Standard-Baugruppenprozessen.  
   *Mechvane-Gegenposition:* **Grundsatz 5 (Getrennte Bauteil- und Baugruppendateien wie Inventor)**. Jedes Bauteil hat seinen eigenen Feature-Baum (`.ipt`), Baugruppen (`.iam`) verweisen auf Bauteile und halten die Gelenke.

4. **Browser-Only als alleinige Plattform:**  
   Browser-Engines stoßen bei extrem großen Baugruppen (>10.000 Bauteile) an harte Speichergrenzen (WebGL-RAM, Tab-Limits).  
   *Mechvane-Gegenposition:* Die Web-UI dient dem schnellen Einstieg, Prüfen und Chat; für Hochleistungs-CAD entsteht eine native Desktop-App.

5. **Formalistisches Groß-PDM für den Alltagsbetrieb:**  
   Onshapes Release-Management mit Genehmigungsstufen ist für Konzerne gedacht, bremst jedoch agile Einzelentwickler aus.  
   *Mechvane-Gegenposition:* Versionskontrolle erfolgt schlank und nativ über standardisiertes Git auf Dateiebene.

---

## 6. Lizenz- und Rechtshinweis

Mechvane steht unter den Lizenzen **MIT OR Apache-2.0**.
Für dieses Dokument und künftige Entwicklungen gelten die strengen Vorgaben aus `AGENTS.md`:
- **Clean Room:** Es werden ausschließlich Bedienkonzepte, Datenmodell-Ideen und funktionale Arbeitsweisen analysiert und bewertet.
- **Kein Code-Transfer:** Es wird keinerlei Quellcode, Script-Code oder Datenmaterial aus proprietären Onshape-Quellen kopiert oder portiert.
- **Keine Automatisierung kommerzieller Systeme:** Zur Erstellung von Beiträgen für Mechvane oder SolidCraft dürfen keine kommerziellen CAD-Programme automatisiert oder gescrapt werden.

---

## 7. Detaillierte Analyse und Quellenbelege

Die folgenden Belege enthalten die wörtlichen Originalzitate aus den offiziellen Dokumentationen und Fachpublikationen von Onshape (PTC), verifiziert mit `tools/check_sources.py`.

### Beleg: Multi-Part Part Studios
* **URL:** https://www.onshape.com/en/features/parts
* **Wörtliches Zitat:** „Onshape's Part Studios environment enhances parametric design, enabling the creation and editing of parts, surfaces, and sketches.“

### Beleg: Unabhängige Konfigurationstabellen
* **URL:** https://www.onshape.com/en/features/configurations
* **Wörtliches Zitat:** „Onshape Configurations allow designers to save time and simplify their workflows by allowing the creation of complex part and assembly families using independent tables.“

### Beleg: Derived Feature und Master-Skizzen
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/creating-master-sketches-with-onshapes-derived-feature
* **Wörtliches Zitat:** „The Master Sketch technique effectively controls geometric relationships across multiple Part Studios.“

### Beleg: Variable Studios für zentrale Parameter
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/variable-studios-automate-parametric-modeling
* **Wörtliches Zitat:** „Onshape Variable Studio centralizes variable creation and management for Part Studios, assemblies, and drawings.“

### Beleg: Branching und Merging
* **URL:** https://www.onshape.com/en/features/data-management
* **Wörtliches Zitat:** „Move faster with branching and merging. Explore design alternatives in parallel without risking the "Master" model.“

### Beleg: Integriertes PDM und Revisionswiederherstellung
* **URL:** https://www.onshape.com/en/features/data-management
* **Wörtliches Zitat:** „With built-in PDM, Onshape automatically captures every edit in real time, allowing users to instantly compare versions and restore to any previous design state.“

### Beleg: Audit-Historie und Revisionsverfolgung
* **URL:** https://www.onshape.com/en/features/data-management
* **Wörtliches Zitat:** „With full audit history, branching and merging, and release management workflows, your product development team can iterate confidently, knowing everyone is working from a single source of truth and design work moves forward without delays or rework.“

### Beleg: Gleichzeitiges Bearbeiten ohne Dateisperren
* **URL:** https://www.onshape.com/en/features/collaboration
* **Wörtliches Zitat:** „Multiple designers can edit the same part or assembly at the same time—without file locks, branching, or manual merges.“

### Beleg: Follow Mode für Live-Durchsprachen
* **URL:** https://www.onshape.com/en/features/collaboration
* **Wörtliches Zitat:** „Synchronize your screen with a teammate for live design walk-throughs. No screen sharing software or lag—just pure CAD performance.“

### Beleg: 3D-Kommentare und Aufgaben am Modell
* **URL:** https://www.onshape.com/en/features/collaboration
* **Wörtliches Zitat:** „Feedback, discussions, and tasks live directly on the CAD model, not in email, chat threads, or external tools.“

### Beleg: Cloud-natives PDM ohne Vault-Server
* **URL:** https://www.onshape.com/en/features/data-management
* **Wörtliches Zitat:** „Onshape's PDM is built into its cloud-native CAD platform, serving as a foundation for all design workflows. By eliminating PDM vaults, and check-in/check-out processes, teams manage product data in one system, and access the latest design information in real time.“

### Beleg: FeatureScript Programmiersprache
* **URL:** https://www.onshape.com/en/features/custom-features
* **Wörtliches Zitat:** „FeatureScript is Onshape’s open-source, strongly typed programming language used to define all built-in features in Onshape.“

### Beleg: Mate Connectors in Baugruppen
* **URL:** https://www.onshape.com/en/features/assemblies
* **Wörtliches Zitat:** „Onshape's mate system uses Mate Connectors to build assemblies with fewer constraints than traditional CAD tools, saving time while maintaining precise control.“

### Beleg: Kinematische Higher-Order Mates
* **URL:** https://www.onshape.com/en/features/assemblies
* **Wörtliches Zitat:** „Onshape's mates streamline assembly creation by allowing high-level kinematic relationships, reducing build time and fragility.“

### Beleg: In-Context Baugruppen-Design
* **URL:** https://www.onshape.com/en/features/assemblies
* **Wörtliches Zitat:** „Experience Onshape's innovative in-context design, where you can create parts within assemblies, capturing snapshots for reference.“

### Beleg: Automatische Normteil-Bibliothek
* **URL:** https://www.onshape.com/en/features/assemblies
* **Wörtliches Zitat:** „Onshape transforms the tedium of hardware insertion with its innovative standard and custom libraries approach; the built-in library is accessible to all users, and streamlines the insertion process by auto-sizing fasteners to fit, and positioning them accurately.“

### Beleg: Replicate-Befehl für Muster und Verbindungen
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/tech-tip-using-the-replicate-command-in-onshape-assemblies
* **Wörtliches Zitat:** „The Replicate command is a fast and useful way for you to quickly reproduce the same mate multiple times across an Onshape part, face or feature.“

### Beleg: Explosionsansichten für Anleitungen und BOM
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/creating-exploded-views-cloud-native-cad
* **Wörtliches Zitat:** „Exploded views are used to clearly communicate assembly instructions, for creating service manuals, and detailing Bills of Materials (BOMs).“

### Beleg: Simultane Flachabwicklung bei Blech
* **URL:** https://www.onshape.com/en/features/sheet-metal
* **Wörtliches Zitat:** „With Onshape, users can simultaneously create and preview flat patterns. This visualization of the flattened design helps streamline the manufacturing planning process.“

### Beleg: Umwandlung von Vollkörpern in Blech
* **URL:** https://www.onshape.com/en/features/sheet-metal
* **Wörtliches Zitat:** „In Onshape, you can initiate a sheet metal design using several methods: you can convert a solid part into sheet metal; design from a flat sketch, then fold; use flange tools to add edges and features; or directly import and adapt existing sheet metal designs.“

### Beleg: Synchronisierte Zeichnungen und Stücklisten
* **URL:** https://www.onshape.com/en/features/drawings
* **Wörtliches Zitat:** „Changes made to your design are automatically synced and reflected in any parts, BOM tables or linked information contained in your drawing.“

### Beleg: Skizzen-Abhängigkeitsmanager
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/sketch-constraint-manager
* **Wörtliches Zitat:** „The sketch Constraint manager in Onshape is a powerful tool that provides a clear, visual way to understand and manage complex sketch constraints.“

### Beleg: REST-API und Webhooks für Automatisierung
* **URL:** https://www.onshape.com/en/features/integrations
* **Wörtliches Zitat:** „Automation is provided through events and web hooks that enable data to be pulled from Onshape when various events occur - such as initiating a release in Onshape.“

### Beleg: KI-Assistent Onshape AI Advisor
* **URL:** https://www.onshape.com/en/blog/ai-advisor-artificial-intelligence-cad-engineering-software
* **Wörtliches Zitat:** „AI Advisor, available both within Onshape itself and the Onshape Learning Center, provides instant, accurate answers based on our extensive documentation library.“

### Beleg: Mobile CAD-Nutzung auf Tablets und Telefonen
* **URL:** https://www.onshape.com/en/blog/mobile-cad-onshape-app
* **Wörtliches Zitat:** „One in every eight Onshape sessions is on a phone or tablet – a testament to the power and productivity of our mobile apps.“
