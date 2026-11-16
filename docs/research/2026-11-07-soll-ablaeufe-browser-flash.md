# Recherche Soll-Abläufe 3: Modellbrowser, Rückgängig und Parameter wie Inventor und SolidCraft

- **Datum:** 2026-11-07
- **Autor:** Gemini 3.8 Flash (Issue #57)
- **Status:** Verifiziert mit `python3 tools/check_sources.py docs/research/2026-11-07-soll-ablaeufe-browser-flash.md` und gegen den Sparse-Klon `/root/repos/_ext/solidcraft`
- **Prüfnotiz (Claude, 2026-11-07):** `check_sources.py`: alle Inventor-Zitate und Zahlen belegt. SolidCraft-Fundstellen sind Stichproben gegen den Klon vom 2026-11-07 (nach v0.30.1); Zeilennummern können verschoben sein. Nicht bestätigt: „`solid.revolve` hat kein Standard-Tastenkürzel“.
- **Kontext & Ziel:** Diese Recherche definiert eine normative Soll-Liste (Target Specification) für Standardabläufe im Modellbrowser, beim Rückgängigmachen/Wiederholen (Undo/Redo) und im Parameter-Dialog. Sie bildet die Entscheidungsgrundlage für die Mechvane-Oberfläche (v0.1), damit Entwickler und Agents den Funktionsstand dagegen abgleichen können und etabliertes Standardverhalten aus Autodesk Inventor nicht jedes Mal neu begründet werden muss.

---

## 1. Einleitung & Architektur-Gegenüberstellung

Ein CAD-System wird vom Konstrukteur maßgeblich über drei Kernkomponenten gesteuert: den **Modellbrowser** (Struktur- und Chronologiebaum), das **Transaktionssystem** (Undo/Redo) und die **Parametertabelle** (geometrische Steuerung). Beim Abgleich zwischen Autodesk Inventor und SolidCraft zeigen sich fundamentale Gemeinsamkeiten, aber auch architektonische Divergenzen in der Präsentation:

1. **Modellbaum-Hierarchie:**
   - **Autodesk Inventor** besitzt einen einheitlichen, chronologischen Modellbrowser (*Model Browser*). Jedes skizzenbasierte 3D-Feature (z. B. `Extrusion1`) verzehrt seine Profilskizze (`Skizze1`). Die Skizze wird hierarchisch unter den Feature-Knoten eingerückt (*consumed*). Am Ende des Bauteilbaums sitzt die verschiebbare Markierung **Bauteilende** (*End of Part* / EOP).
   - **SolidCraft** trennt in seiner Benutzeroberfläche standardmäßig zwischen dem Objekt-Browser (`crates/ui-egui/src/browser.rs`, gegliedert nach Komponenten, Körpern, Skizzen und Konstruktionselementen) und der horizontalen Zeitleiste (*Timeline* / History in `crates/ui-egui/src/timeline.rs`). Allerdings bietet SolidCraft intern bereits eine Browser-Darstellung für Features (`crates/ui-egui/src/browser/features.rs`) mit chronologischer Reihenfolge, Drag-Verschiebung und Ordnergruppierung.
   - **Empfehlung für Mechvane (v0.1):** Mechvane soll sich wie Inventor anfühlen (ROADMAP Grundsatz 10). Die Web-UI benötigt daher einen primären, vertikalen Modellbrowser, in dem Features chronologisch von oben nach unten gelistet sind, einbezogene Skizzen unter ihren Features verschachtelt werden und die Bauteilende-Markierung direkt im Baum sitzt. Unter der Haube mappt Mechvane diese Aktionen atomar auf SolidCrafts Engine-Befehle (`solidcraft_engine::cmd`).

2. **Transaktions-Granularität:**
   - Beide Systeme behandeln geometrische Feature-Änderungen als atomare Schritte. Reine Ansichtsoperationen (Drehen, Zoomen, Schwenken) und Selektionsänderungen landen in keinem der beiden Systeme im Modell-Undo.
   - Mehrfach-Edits (z. B. gemeinsames Ändern mehrerer Parameter oder ein kontinuierliches Überstreichen von Sichtbarkeits-Augensymbolen) werden in SolidCraft explizit zu genau einem Undo-Schritt zusammengefasst (`several_parameters_change_in_one_rebuild_and_one_undo`, `eye_drag_frame`).

3. **Parametrisches Gleichungssystem:**
   - Beide Systeme trennen strikt zwischen automatisch generierten **Modellparametern** (Bemaßungen `d0, d1...`, Feature-Tiefen) und expliziten **Benutzerparametern**.
   - Beide Systeme unterstützen die direkte Inline-Parameterdefinition über Gleichungen (`Breite = 50 mm`) direkt im Bemaßungsfeld, benennen den Modellparameter dabei unterbrechungsfrei um und propagieren den neuen Namen sofort auf alle referenzierenden Ausdrücke.

---

## 2. Modellbrowser (Soll-Abläufe)

### 2.1 Symbole je Feature-Typ

Die visuelle Erkennung von Feature-Typen im Modellbrowser erfolgt über prägnante Symbole (Icons).

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Feature-Icons im Baum** | Im Bauteil-Browser werden standardisierte Piktogramme für alle Grund- und Bearbeitungselemente geführt: `Extrusion`, `Drehung`, `Bohrung`, `Rundung`, `Fase`, `Spirale`, `Wandung`, `Erhebung`, `Sweeping`, `Bauteilende-Markierung` ([Beleg GUID-5F5D6502](#beleg-inventor-bauteil-browser-referenz-symbole)). | SolidCraft ordnet jedem Feature-Typ ein statisches SVG-Symbol zu: `pub(crate) fn icon_of(k: &FeatureKind) -> &'static str` (`crates/ui-egui/src/timeline.rs:136-213`), u. a. `"extrude"`, `"revolve"`, `"fillet"`, `"chamfer"`, `"hole"`, `"loft"`, `"sweep"`, `"shell"`, `"draft"`, `"coil"`, `"pattern_rect"`, `"pattern_circ"`, `"mirror"`. | Mechvane übernimmt exakt die 1:1-Zuordnung der SolidCraft-Icons für die Web-UI (`mechvane/ui/static/`), orientiert sich aber bei der Beschriftung (`Extrusion1`, `Drehung1`, `Bohrung1`) strikt an der deutschen Inventor-Nomenklatur. |
| **Arbeitselemente (Konstruktion)** | Arbeitsebenen, Arbeitsachsen und Arbeitspunkte besitzen differenzierte Symbole je nach Definitionsart ([Beleg GUID-5F5D6502](#beleg-inventor-bauteil-browser-referenz-symbole)). | `crates/ui-egui/src/timeline.rs:166-181`: Differenzierte Icons für Ebenen, Achsen (`"axis_through_cylinder"`, `"axis_normal_to_face"`, etc.) und Punkte (`"point_vertex"`, `"point_center"`, etc.). | Eigene Icon-Gruppe für Hilfs- und Konstruktionsgeometrie im Browser; standardmäßig in einem übergeordneten Knoten `Ursprung` (Origin) zusammengefasst. |
| **Status-Indikatoren am Icon** | Fehlerhafte oder regelverletzende Elemente erhalten ein gelbes Warndreieck oder rotes Stopp-Symbol ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). | `crates/engine/src/cmd/edit.rs:112`: `inputs: [...] error, warning`. In der UI als Warn-Overlay am Feature-Icon gerendert. | Warn- und Fehler-Badges direkt am Icon anzeigen; Mouseover zeigt den genauen Fehlertext an. |

### 2.2 Sichtbarkeit (Visibility)

Das Ein- und Ausblenden von Körpern, Skizzen und Arbeitselementen ist eine der häufigsten Interaktionen im Modellbrowser.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Sichtbarkeit umschalten** | Kontextmenüeintrag `Sichtbarkeit Aktiviert oder deaktiviert die Sichtbarkeit einer Komponente` bzw. eines Elements ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). Ausgeblendete Objekte werden im Browser abgeblendet/grau dargestellt. | `crates/ui-egui/src/browser.rs:601`: `Item::action("ui.origin", "Show/Hide", "eye").key("V")`. Ausgeführt über `browser.visibility` (`crates/engine/src/cmd/browser.rs:101`). | Augensymbol in jeder Browserzeile (Hover sichtbar, ausgeblendet dauerhaft sichtbar). Klick schaltet Sichtbarkeit um. |
| **Tastenkürzel** | Tastatur-Umschaltung für Sichtbarkeit (in Bauteil/Baugruppe konfigurierbar, Standardkontextmenü `Sichtbarkeit`). | `crates/ui-egui/src/browser.rs:601` und `crates/ui-egui/src/context_menu.rs:893`: Taste **`V`** schaltet Sichtbarkeit der markierten Elemente um. | Taste **`V`** für `Sichtbarkeit ein/aus` auf aktuell selektierten Objekten verbindlich unterstützen. |
| **Überstreichen (Eye-Drag)** | In Inventor können mehrere Einträge im Browser mit gedrückter Maustaste markiert und über Kontextmenü gemeinsam umgeschaltet werden. | `crates/ui-egui/src/browser.rs:615-628`: `eye_drag_frame`: `„A drag over the eyes is one undo step (#9680)... the steps the drag made are merged into the first of them.“` | Ziehen mit gedrückter Maustaste über mehrere Augen-Icons schaltet alle überstrichenen Zeilen in einem einzigen Undo-Schritt um. |
| **Ordner / Gruppen ausblenden** | Ordner-Sichtbarkeit schaltet alle enthaltenen Elemente um ([Beleg GUID-5F975252](#beleg-inventor-baugruppen-browser-ordner)). | `crates/ui-egui/src/browser.rs:609-613`: `toggle_folder(app, key)` schaltet Gruppen-Sichtbarkeit ohne Verlust des individuellen Objektstatus um. | Ordner erhalten eigenes Augensymbol; Ausblenden verbirgt Inhalt, behält aber den individuellen Unterstatus bei. |

### 2.3 Umbenennen (Rename)

Die Benennung von Features und Parametern sorgt für Übersicht in komplexen Baugruppen.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Inline-Umbenennen per Klick** | Klick auf bereits selektierten Browser-Knoten nach kurzer Pause (Klickverzögerung) oder Druck auf `F2` aktiviert das Inline-Textfeld ([Beleg GUID-428B9A8E](#beleg-inventor-tastaturkurzbefehle-referenz)). | `crates/ui-egui/src/browser.rs:3234-3245`: `„A double-click renames the row (sketch rows open for editing instead), like F2. A body is edited in its own row.“` | Druck auf **`F2`** oder Klickverzögerung aktiviert Inline-Textfeld im Browser; Bestätigen mit `Enter`, Verwerfen mit `Esc`. |
| **Kontextmenü** | Kontextmenüeintrag zum Umbenennen von Komponenten und Ordnern. | `crates/ui-egui/src/context_menu.rs:650, 887`: `act("ui.rename", "Rename", "rename").key("F2")`. | Eintrag `Umbenennen (F2)` im Kontextmenü aller Browser-Elemente. |
| **Referenz-Propagierung** | Das Umbenennen von Parametern und Elementen aktualisiert automatisch alle referenzierenden Formeln und Skizzen ([Beleg GUID-595F9D8E](#beleg-inventor-so-arbeiten-sie-mit-parametern-in-modellen)). | `crates/engine/src/cmd/parameters_tests.rs:149-179`: `rename_updates_every_reference()`: `„Model and feature parameters can be renamed too: dimensions and features follow.“` | Namensänderungen werden unterbrechungsfrei in allen Gleichungen und Kind-Features aktualisiert. |

### 2.4 Unterdrücken (Suppress)

Unterdrückte Features werden temporär aus der Geometrieberechnung entfernt, bleiben aber im Modellbaum erhalten.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Manuelles Unterdrücken** | `Element unterdrücken Entfernt das Element aus dem Grafikfenster. Im Browser wird es weiterhin angezeigt und durch eine graue Markierung gekennzeichnet. Wenn Sie die Unterdrückung aufheben möchten, klicken Sie mit der rechten Maustaste in den Browser, und wählen Sie Unterdrückung aufheben.` ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). | `crates/engine/src/cmd/edit.rs:99-103`: `timeline.suppress`: Schaltet den Unterdrückungsstatus für Features, Kind-Features oder ganze Ordnergruppen um (`suppressed?: bool`). | Kontextmenü `Unterdrücken` / `Unterdrückung aufheben`. Unterdrücktes Feature wird im 3D-View ausgeblendet und im Browser abgeblendet. |
| **Visuelle Darstellung im Browser** | `Unterdrückte Elemente werden im Grafikfenster nicht angezeigt und sind im Browser abgeblendet dargestellt.` ([Beleg GUID-983D8293](#beleg-inventor-elemente-loeschen-oder-unterdruecken)). Text ist durchgestrichen oder hellgrau. | `crates/ui-egui/src/context_menu.rs:651`: Dynamischer Menütext (`Unsuppress` vs. `Suppress`); Browserzeile wird mit reduzierter Opazität gerendert. | Schriftzug des unterdrückten Features im Browser hellgrau abblenden und mit Durchstreichung versehen; Icon leicht transparent. |
| **Bedingtes Unterdrücken** | `Bedingtes Unterdrücken skizzierter oder platzierter Elemente`: In den Eigenschaften kann eine mathematische Bedingung an einen Parameter geknüpft werden (`Wenn`, z. B. `Breite < 50 mm`) ([Beleg GUID-983D8293](#beleg-inventor-elemente-loeschen-oder-unterdruecken)). | `crates/engine/src/cmd/parameters.rs:33-35`: `switched?: [{feature, name, suppressed}] (the configuration rules that switch a feature's suppression and read a parameter whose value changed run in their order)`. | Für v0.1 Vorbereitung in den Feature-Eigenschaften: Bedingungsausdruck an Parameter koppeln (`timeline.suppress`). |

### 2.5 Löschen mit abhängigen Features (Delete with Dependents)

Das Löschen eines übergeordneten Features betrifft oft dessen Skizzen, Folge-Features und referenzierte Arbeitselemente.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Lösch-Dialogfeld** | `Geben Sie im Dialogfeld Elemente löschen an, welche zusätzlichen abhängigen Elemente, Skizzen oder Arbeitselemente gelöscht werden sollen:` ([Beleg GUID-983D8293](#beleg-inventor-elemente-loeschen-oder-unterdruecken)). | `crates/ui-egui/src/delete.rs:1-4`: `„When it takes other features with it or makes some fail, a confirmation lists them first.“` | Beim Löschen eines Features mit Abhängigkeiten öffnet sich ein Bestätigungsdialog mit Einzelelement-Auswahl. |
| **Einbezogene Skizzen beibehalten** | `Einbezogene Skizzen und Elemente. Diese Option ist standardmäßig ausgewählt. ... Wenn Sie die einbezogenen Skizzen und Elemente beibehalten möchten, deaktivieren Sie das Kontrollkästchen.` ([Beleg GUID-983D8293](#beleg-inventor-elemente-loeschen-oder-unterdruecken)). | `crates/ui-egui/src/delete.rs:188-205`: Zeigt Bestätigungskarte `These features will be deleted:` und `These features will fail:`. | Kontrollkästchen *"Einbezogene Skizzen beibehalten"* anbieten. Wird es aktiviert, bleibt die Skizze als freistehende Skizze im Modell erhalten. |
| **Abhängige Arbeitselemente** | `Abhängige Arbeitselemente. ... Wenn Sie beim Löschen des übergeordneten Elements die abhängigen Arbeitselemente beibehalten möchten, deaktivieren Sie das Kontrollkästchen. Beibehaltene Arbeitselemente werden fixiert.` ([Beleg GUID-983D8293](#beleg-inventor-elemente-loeschen-oder-unterdruecken)). | `crates/engine/src/cmd/edit.rs:70`: `timeline.delete` entfernt abhängige Geometrie kaskadierend, sofern nicht explizit entkoppelt. | Arbeitselemente, die auf gelöschten Flächen lagen, werden bei Beibehaltung automatisch auf fixierte Raumkoordinaten umgestellt. |

### 2.6 Bauteilende ziehen (End of Part / EOP / Rollback Marker)

Der Rollback-Marker steuert den historischen Berechnungsstand des Modells.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Marker im Baum ziehen** | `Suchen Sie unten im Browser das Symbol Bauteilende (oder Element), und ziehen Sie es nach oben, um das Modell in ein früheres Stadium zurückzusetzen.` `Hierdurch werden die Elemente unterhalb des Bauteilende-Symbols vorübergehend aus dem Modell entfernt.` ([Beleg GUID-69196418](#beleg-inventor-modellbrowser-bauteilende-eop)). | `crates/engine/src/cmd/edit.rs:86-88`: `timeline.rollback` und `timeline.roll_to` (`position: number of features to keep active, or "end"`). | EOP-Balken am Ende des Browsers; Ziehen per Drag & Drop zwischen beliebige Features rollt das 3D-Modell sofort zurück. |
| **Abbruch mit Escape** | `Beim Verschieben der Bauteilende-Markierung können Sie den Vorgang abbrechen, indem Sie die ESC-TASTE drücken. Der Abbruch des Vorgangs wird in einer Meldung bestätigt.` ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue), [Beleg GUID-983D8293](#beleg-inventor-elemente-loeschen-oder-unterdruecken)). | `crates/ui-egui/src/timeline.rs`: Maus-Release außerhalb oder Escape bricht Drag-Zustand ab; Position bleibt unverändert. | Während des Ziehens des EOP-Markers bricht die **`Escape`**-Taste den Drag sofort ab; der Marker springt an die Ausgangsstelle zurück. |
| **Kontextmenü am Feature** | `Bauteilende-Markierung verschieben Verschiebt die Bauteilende-Markierung unter das ausgewählte Element oder in den Ordner Ursprung.` ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). | `crates/ui-egui/src/context_menu.rs:654`: `act("timeline.roll_to", "Roll Back Here", "rollback").with(json!({"feature":id}))`. | Kontextmenü-Eintrag an jedem Feature: `Bauteilende hierher verschieben`. |
| **Kontextmenü am EOP-Marker** | `Bauteilende zum Anfang verschieben` und `Bauteilende zum Ende verschieben` ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). | `crates/engine/src/cmd/edit.rs:86`: `timeline.rollback` mit `position: 0` bzw. `position: "end"`. | Rechtsklick auf den EOP-Marker bietet: `Zum Anfang verschieben` und `Zum Ende verschieben`. |
| **Alle Elemente unter EOP löschen** | `Alle Elemente unter Bauteilende löschen Löscht alle im Browser unterhalb dieser Markierung aufgeführten Elemente.` ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). | `crates/ui-egui/src/timeline.rs:356-376`: `delete_after_marker_button`: `„timeline.delete_after_marker_one“` / `other`. | Rechtsklick auf EOP-Marker (wenn nicht am Ende): `Alle Elemente unter Bauteilende löschen` mit Sicherheitsabfrage. |

### 2.7 Kontextmenü-Einträge

Das Kontextmenü (Rechtsklick) bietet situationsbezogene Operationen auf dem selektierten Objekt.

| Element-Typ | Inventor Kontextmenü (Zitate aus [GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)) | SolidCraft Kontextmenü (Code-Zitate) | Mechvane-Soll (v0.1) |
| :--- | :--- | :--- | :--- |
| **3D-Feature** (Extrusion, Bohrung etc.) | - `Element bearbeiten`<br>- `Skizze bearbeiten`<br>- `Element unterdrücken`<br>- `Sichtbarkeit`<br>- `Bemaßungen anzeigen`<br>- `Löschen`<br>- `Bauteilende-Markierung verschieben` | `crates/ui-egui/src/context_menu.rs:642-660`: `feature_items`: `ui.editFeature`, `ui.editSketch`, `ui.rename` (F2), `timeline.suppress`, `timeline.roll_to`, `ui.cut` (Ctrl+X), `ui.copy` (Ctrl+C), `ui.delete` (Del), `ui.findTimeline`. | 1. Element bearbeiten (Enter/Doppelklick)<br>2. Profilskizze bearbeiten<br>3. Bemaßungen anzeigen<br>4. Unterdrücken<br>5. Umbenennen (F2)<br>6. Löschen (Entf)<br>7. Bauteilende hierher verschieben |
| **Skizze** | - `Skizze bearbeiten`<br>- `Skizze neu definieren`<br>- `Skizze wieder verwenden`<br>- `Sichtbarkeit`<br>- `Löschen` | `crates/ui-egui/src/context_menu.rs:876-896`: `sketch_items`: `ui.extrudeSketch` (E), `ui.editSketch`, `ui.redefineSketch`, `ui.exportDxf`, `ui.delete` (Del), `ui.rename` (F2), `ui.lookAt`, `ui.sketchDims`, `ui.showSketch` / `ui.hideSketch` (V). | 1. Skizze bearbeiten (Doppelklick)<br>2. Skizze neu definieren (Ebene wechseln)<br>3. Extrusion starten (E)<br>4. Sichtbarkeit ein/aus (V)<br>5. DXF exportieren…<br>6. Umbenennen (F2)<br>7. Löschen (Entf) |
| **Arbeitselement** (Ebene, Achse) | - `Element bearbeiten`<br>- `Neue Skizze` (auf Ebene)<br>- `Sichtbarkeit`<br>- `Löschen` | `crates/ui-egui/src/context_menu.rs:901-920`: `plane_items`: `sketch.create`, `ui.editFeature`, `ui.rename` (F2), `ui.delete` (Del), `ui.originPart` (V). | 1. Neue Skizze erstellen (S)<br>2. Ebene bearbeiten<br>3. Sichtbarkeit (V)<br>4. Umbenennen (F2)<br>5. Löschen (Entf) |

### 2.8 Ordner (Folders / Groups)

Ordner dienen der Strukturierung komplexer Modellbäume ohne Auswirkung auf die Rechenreihenfolge.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Ordner anlegen** | `Erstellen Sie Ordner, um die Browser-Knoten in Gruppen zu organisieren oder das Konzept zu kommunizieren.` ([Beleg GUID-5F975252](#beleg-inventor-baugruppen-browser-ordner)). Mehrere Features markieren > Rechtsklick > *Zu neuem Ordner hinzufügen*. | `crates/engine/src/cmd/browser.rs:62-66`: `browser.group`: `CommandSpec::new("browser.group", "New Group")`. `crates/engine/src/cmd/edit.rs:72`: `timeline.group` (`"Group Features into Folder"`). | Mehrere Features selektieren > Kontextmenü `In Ordner gruppieren`. Erzeugt einen aufklappbaren Gruppenknoten. |
| **Verschieben per Drag & Drop** | Features können frei in Ordner hinein und heraus gezogen werden ([Beleg GUID-5F975252](#beleg-inventor-baugruppen-browser-ordner)). | `crates/engine/src/cmd/browser.rs:77-81`: `browser.move`: Verschiebt Knoten in Gruppen oder ordnet sie neu an. Bis zu 8 Verschachtelungsebenen (`at most 8 levels`). | Drag & Drop von Features in und aus Ordnern unterstützen. |
| **Ordner auflösen (Ungroup)** | Ordner löschen bietet Auswahl: *Nur Ordner löschen* (Inhalt bleibt erhalten) oder *Ordner und Inhalt löschen*. | `crates/engine/src/cmd/browser.rs:67-71`: `browser.ungroup`: `„its items and child groups go up to the group that holds it, or the folder“`. `crates/engine/src/cmd/edit.rs:76`: `timeline.ungroup`. | Kontextmenü am Ordner: `Gruppe auflösen` verschiebt Features wieder auf die Hauptebene des Baums zurück. |

### 2.9 Doppelklick (Double-Click Workflows)

Der Doppelklick ist die intuitivste Abkürzung für Bearbeitungsschritte.

| Zielobjekt | Inventor Verhalten (Zitate & Belege) | SolidCraft Verhalten (Code-Zitate) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Skizze** | `Doppelklicken Sie auf das Skizzensymbol im Browser.` Aktiviert sofort die Skizzenumgebung ([Beleg GUID-E96FB3C4](#beleg-inventor-so-erstellen-und-bearbeiten-sie-skizzen)). | `crates/ui-egui/src/browser.rs:3210-3213`: `„if r.double && folder == "sketches" { app.edit_sketch_in(id, ...); }“` | Doppelklick auf Skizzenknoten öffnet sofort die Skizzierumgebung (`sketcher.js`). |
| **3D-Feature** | Doppelklick auf ein Feature im Browser öffnet den Feature-Dialog bzw. die Eigenschaftsgruppe zur Werteänderung ([Beleg GUID-36DB9904](#beleg-inventor-bauteil-browser-referenz-kontextmenue)). | `crates/ui-egui/src/browser/features.rs:341-345`: `if r.double { app.edit_feature(id); }` und `crates/ui-egui/src/timeline.rs:1117-1119`. | Doppelklick auf Feature-Zeile öffnet den Eigenschaftsdialog/Mini-Toolbar zur Parameteranpassung. |
| **Komponente (Baugruppe)** | Doppelklick auf eine Komponente in der Baugruppe aktiviert diese für die Bearbeitung an Ort und Stelle (*Edit in Place*), blendet den Rest ab ([Beleg GUID-FBBE5A60](#beleg-inventor-komponente-in-der-baugruppe-erstellen-referenz)). | `crates/ui-egui/src/browser.rs:1793-1798`: `if r.double { crate::edit_in_place::double_click_component(app, json!({ "component": id })); }` und `crates/ui-egui/src/browser/features.rs:343`. | Doppelklick auf Komponente aktiviert `edit_in_place` (Top-Down-Kontext). Doppelklick in den leeren Raum kehrt zur Hauptbaugruppe zurück. |

### 2.10 Hervorhebung im Modell beim Überfahren (Hover Highlight / Pre-Highlight)

Die visuelle Rückkopplung zwischen Modellbaum und 3D-Ansicht verhindert Fehlselektionen.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Vorab-Hervorhebung (Pre-Highlight)** | `Vorab-Hervorhebung aktivieren Objekte werden hervorgehoben, wenn Sie den Cursor darüber bewegen. So erhalten Sie Informationen zu dem Objekt, das Sie auswählen. Vorgabemäßig aktiviert.` ([Beleg GUID-62188BB2](#beleg-inventor-registerkarte-farben-vorab-hervorhebung)). | `crates/ui-egui/src/browser.rs:3251-3258`: `if r.hovered && !e.bodies.is_empty() { acts.hover(e.bodies.iter()); }` und `acts.hover_plane = Some(name.clone());`. `crates/ui-egui/src/browser.rs:957`: `lit: Lit` (bidirektional). | Beim Überfahren (Hover) einer Zeile im Browser leuchtet die zugehörige 3D-Geometrie (Körper, Fläche, Skizze, Arbeitsebene) im Viewport mit einer Akzentfarbe auf. |
| **Rückwärts-Hervorhebung (3D zu Browser)** | Bewegt sich der Cursor im Grafikfenster über Geometrie, wird das zugehörige Element im Browser automatisch unterstrichen bzw. hervorgehoben ([Beleg GUID-B8F6E805](#beleg-inventor-so-waehlen-sie-objekte-aus-und-heben-die-auswahl-auf)). | `crates/ui-egui/src/browser.rs:957`: `„What the selection and the 3D view's pointer light in the tree.“` | Zeigt der Mauszeiger im 3D-Viewport auf eine Fläche, wird die erzeugende Feature-Zeile im Modellbrowser dezent akzentuiert. |

---

## 3. Rückgängig/Wiederholen (Undo / Redo)

Das Transaktionsmodell definiert, welche Interaktionen rückgängig gemacht werden können und wie atomare Schritte abgegrenzt sind.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Tastenkürzel** | `STRG+Z Aktiviert den Befehl Rückgängig (hebt den letzten Vorgang auf)` und `STRG+Y Aktiviert den Befehl Wiederherstellen (hebt den letzten Befehl Rückgängig auf)` ([Beleg GUID-428B9A8E](#beleg-inventor-tastaturkurzbefehle-referenz)). | `crates/engine/src/cmd/edit.rs:22-35`: `CommandSpec::new("edit.undo", "Undo").key("Ctrl+Z")` und `CommandSpec::new("edit.redo", "Redo").key("Ctrl+Y")`. | Standardtasten **`Strg+Z`** (Undo) und **`Strg+Y`** (Redo) global registrieren. |
| **Transaktionsumfang eines Schritts** | Einzelschritt umfasst jede dokumentverändernde Operation (Feature erstellen, Feature löschen, Maße ändern). Ansichtsänderungen (Pan, Zoom, Orbit) sind vom Modell-Undo getrennt (Inventor besitzt eigenes Ansichts-Rückgängig `F5`). | `crates/engine/src/cmd/edit.rs:141-155`: `undo(s, p)` und `redo(s, p)`. Reine Selektions- und Ansichtsbefehle sind mit `.noundo()` deklariert (`select.set`, `select.clear`, `camera.orbit`). | Nur Geometrie-, Parameter- und Dokumentänderungen erzeugen einen Undo-Schritt. Kamera- und Selektionsbewegungen verändern den Undo-Stapel nicht. |
| **Mehrfach-Parameteränderungen** | Das Ändern mehrerer Parameterzeilen im Dialogfeld vor Klick auf *Übernehmen* wird als eine einzige gemeinsame Transaktion rückgängig gemacht ([Beleg GUID-595F9D8E](#beleg-inventor-so-arbeiten-sie-mit-parametern-in-modellen)). | `crates/engine/src/cmd/parameters_tests.rs:895-913`: `several_parameters_change_in_one_rebuild_and_one_undo()`: `„All or nothing: an unknown name or a broken expression changes nothing. ... run(&mut s, "edit.undo", json!({}));“` stellt alle geänderten Variablen zusammen zurück. | Werden im Parameter-Dialog mehrere Werte geändert und mit *OK/Übernehmen* bestätigt, bildet dies genau 1 Undo-Schritt (`parameters.change` mit `changes: {...}`). |
| **Augen-Drag (Sichtbarkeits-Überstreichen)** | Gemeinsames Umschalten mehrerer Elemente über Kontextmenü ist ein Undo-Schritt. | `crates/ui-egui/src/browser.rs:615`: `„A drag over the eyes is one undo step (#9680)... the steps the drag made are merged into the first of them.“` | Zusammenhängendes Ziehen über Sichtbarkeits-Icons wird beim Loslassen der Maustaste zu genau 1 Undo-Schritt verschmolzen. |
| **Skizze verwerfen / Abbrechen** | `Wenn Sie eine Skizze abbrechen, werden alle aktuellen Aktionen verworfen. Beim Erstellen einer Skizze werden alle Aktionen verworfen, einschließlich der Erstellung der Skizze.` ([Beleg GUID-E96FB3C4](#beleg-inventor-so-erstellen-und-bearbeiten-sie-skizzen)). | `crates/ui-egui/src/sketch_tools.rs`: Abbrechen einer neuen Skizze löscht das Skizzen-Feature vollständig aus der Session. | Klick auf *"Skizze abbrechen"* (Cancel) rollt alle in der Skizzensitzung gemachten Änderungen atomar zurück. |

---

## 4. Parameter-Dialog (Parameters)

### 4.1 Benutzer- und Modellparameter

Parametrische CAD-Modelle unterscheiden streng zwischen systemgenerierten Maßen und anwenderdefinierten Konstruktionsvariablen.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Modellparameter (Model Parameters)** | `Inventor definiert automatisch Modellparameter in Skizzen, Baugruppenabhängigkeiten und Elementen.` ([Beleg GUID-8E5C63EA](#beleg-inventor-parameter-in-modellen)). Werden fortlaufend nummeriert (`d0, d1, d2...`). | `crates/engine/src/cmd/parameters.rs:38`: `parameters.list` mit `filter?: all\|user\|sketch\|feature\|favorites`. `crates/engine/src/cmd/parameters_tests.rs:95-102`: Feature-Inputs (`Distance`, `Angle`) und Skizzenmaße erhalten automatisch generierte Parameternamen. | Bemaßungen und Feature-Tiefen generieren automatisch Modellparameter (`d0, d1...`), die in der Tabelle unter *Modellparameter* aufgeführt werden. |
| **Benutzerparameter (User Parameters)** | Anwender können eigene Variablen anlegen (`Benutzerparameter hinzufügen`), um globale Maße zu steuern ([Beleg GUID-595F9D8E](#beleg-inventor-so-arbeiten-sie-mit-parametern-in-modellen)). | `crates/engine/src/cmd/parameters.rs:41-45`: `parameters.add`: `CommandSpec::new("parameters.add", "Add User Parameter")` (`name, expression, unit?, comment?, favorite?`). | Schaltfläche *„Benutzerparameter hinzufügen“* im Dialogkopf; erzeugt eine neue editierbare Tabellenzeile. |
| **Löschbarkeit** | Modellparameter können nicht isoliert gelöscht werden (nur durch Löschen der Bemaßung im Modell). Benutzerparameter können gelöscht werden, sofern sie nicht verwendet werden: `Um einen Parameter zu löschen, klicken Sie mit der rechten Maustaste auf die Parameterzeile und wählen Parameter löschen.` ([Beleg GUID-595F9D8E](#beleg-inventor-so-arbeiten-sie-mit-parametern-in-modellen)). | `crates/engine/src/cmd/parameters_tests.rs:114-116`: `„Feature inputs can't be deleted on their own. assert!(err(&mut s, "parameters.delete", json!({"name": d})).contains("feature's input"));“` und `crates/engine/src/cmd/parameters.rs:51-55`: Verwendete Parameter werden abgewiesen (`refused while something uses it`). | Löschen-Aktion nur für unbenutzte Benutzerparameter aktivieren; für Modellparameter deaktivieren/ausblenden (Löschung nur via Geometrie). |

### 4.2 Ausdrücke & Berechnungen

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Gleichungen & Operatoren** | Unterstützt Standardoperatoren `+`, `-`, `*`, `/`, `^`, Gleitpunkt-Modulo `%` sowie Klammern `()` ([Beleg GUID-0106478A](#beleg-inventor-ausdrucksreferenz-fuer-numerische-parameter)). Trennzeichen für mehrparametrige Funktionen ist das Semikolon `;` (`atan2(y; x)`). | `crates/engine/src/cmd/parameters_tests.rs:139`: `expr.evaluate` mit `atan2(b; a) + tilt`. Unterstützt Standard-Arithmetik und mathematische Standardfunktionen. | Rechenausdrücke mit `+`, `-`, `*`, `/`, `^` und Semikolon `;` als Argument-Trennzeichen in Funktionsaufrufen unterstützen. |
| **Zirkelbezüge** | Zirkuläre Abhängigkeiten (z. B. `A = B + 1` und `B = A * 2`) werden erkannt und mit Fehlermeldung blockiert. | `crates/engine/src/cmd/parameters_tests.rs:128-130`: `assert!(e.contains("circular reference: a → b → a"));` und `assert!(err(..., "circular"));`. | Zirkelbezugsprüfung bei jeder Eingabe; bei Endlosschleife Eingabe rot markieren und ablehnen (`circular reference`). |
| **Syntax-Rückmeldung** | `Ein korrekt eingegebener Ausdruck wird in einem Bearbeitungsfeld schwarz angezeigt. Ungültige oder nicht erkannte Syntax wird in Rot angezeigt.` ([Beleg GUID-9DD43CD9](#beleg-inventor-so-definieren-sie-numerische-parameter-in-bearbeitungsfeldern)). | `crates/engine/src/cmd/parameters.rs:86-90`: `expr.evaluate`: Liefert `{ok: bool, value, error}`. | Live-Syntaxprüfung im Eingabefeld: Valide Syntax = Standardfarbe, ungültige Formel = rote Schrift + Fehlertooltip. |

### 4.3 Einheiten & Dimensionen

CAD-Gleichungssysteme erzwingen dimensionale Konsistenz zur Vermeidung von Einheitenfehlern.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Längen- und Winkeleinheiten** | Standardeinheiten sind Millimeter (`mm`) und Grad (`deg`/`grd`). Werden Ausdrücken keine Einheiten angefügt, gelten die Dokumenteigenschaften ([Beleg GUID-0106478A](#beleg-inventor-ausdrucksreferenz-fuer-numerische-parameter)). | `crates/engine/src/cmd/parameters.rs:28`: `unit?: mm\|cm\|m\|in\|ft\|deg\|rad\|""\|text`. | Unterstützung für metrische Längen (`mm`, `cm`, `m`), imperiale (`in`) und Winkel (`deg`, `rad`). Vorgabe ist `mm`. |
| **Einheitenlose Werte (oE / Unitless)** | Einheitenlose Faktoren werden in Inventor mit `oE` (*ohne Einheit*) oder reinen Zahlenwerten deklariert: `2 oE *(6+3)` ([Beleg GUID-0106478A](#beleg-inventor-ausdrucksreferenz-fuer-numerische-parameter)). | `crates/engine/src/cmd/parameters_tests.rs:136-138`: Einheitenlose Ausdrücke (z. B. `b / a`) erhalten intern die Einheit `""` (`assert_eq!(s.doc.param("n").map(|p| p.unit.as_str()), Some(""));`). | Einheitenlose Werte als reine Zahl oder Kennung `ul` / `oE` akzeptieren; Division zweier gleicher Einheiten ergibt einheitenlos. |
| **Verbot von Dimensionskonflikten** | `Im Bearbeitungsfeld werden allen Termen Standardeinheiten zugewiesen, wenn keine Einheit angegeben ist. Die Ergebnisse führen zu einem Fehler, da ungleiche Einheiten nicht addiert werden können` ([Beleg GUID-0106478A](#beleg-inventor-ausdrucksreferenz-fuer-numerische-parameter)). | `crates/engine/src/cmd/parameters_tests.rs:121-125`: `„cannot add a length and an angle“`, `„expected an angle, got a length“`. | Strikte Einheitenprüfung: Addition von Länge und Winkel (`10 mm + 5 deg`) strikt mit Validierungsfehler abweisen. |

### 4.4 Umbenennen von `d0` (Inline-Parameterdefinition)

Die Inline-Definition beschleunigt die Benennung maßgebender Parameter direkt während der Skizzenbemaßung dramatisch.

| Schritt / Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Inline-Syntax im Bemaßungsfeld** | `Beispiel: Sie möchten eine Linie in der Skizziergeometrie bemaßen. Geben Sie im Dialogfeld Bemaßung bearbeiten für diese Linie als Länge = 20 mm ein, und klicken Sie auf das grüne Häkchen, um den Eintrag zu übernehmen. Wenn Sie das Dialogfeld Parameter öffnen, um die definierten Modellparameter anzuzeigen, hat der Parameter Länge den Wert 20 mm.` ([Beleg GUID-9DD43CD9](#beleg-inventor-so-definieren-sie-numerische-parameter-in-bearbeitungsfeldern)). | `crates/engine/src/cmd/parameters.rs:30`: `„an expression new = value renames to new and sets value, or sets new when the expression is just new“`. `crates/engine/src/cmd/parameters_tests.rs:1135-1163`: `changing_a_parameter_to_a_definition_renames_it()`. | Direkteingabe von `Parametername = Ausdruck` (z. B. `Laenge = 45 mm`) in jedes Bemaßungsfeld und jeden Feature-Dialog erlauben. |
| **Ergebnis im Datenmodell** | Der anonyme Modellparameter (z. B. `d0`) wird ohne Neuanlage eines zweiten Parameters in den Wunschnamen umbenannt. In der Skizze steht fortan `d0` oder `fx:Laenge = 20 mm` ([Beleg GUID-8E5C63EA](#beleg-inventor-parameter-in-modellen)). | `crates/engine/src/cmd/parameters_tests.rs:1141-1145`: `assert_eq!((r["name"].as_str(), r["renamed"]["from"].as_str()), (Some("height"), Some(d.as_str())));` und `assert_eq!(..., count, "no extra parameter");`. | Der bestehende Modellparameter wird atomar umbenannt; es entsteht kein doppelter Parameter. |
| **Unterbrechungsfreie Propagierung** | Alle Skizzen, Abhängigkeiten und Features, die bisher auf den alten Parameternamen verwiesen haben, folgen automatisch dem neuen Namen. | `crates/engine/src/cmd/parameters_tests.rs:1146-1152`: `„A dimension's parameter too; whatever refers to it follows.“` | Referenzen werden augenblicklich im gesamten Dokument auf den neuen Namen aktualisiert. |
| **Rückgängig-Verhalten** | Ein Undo stellt sowohl den alten Parameternamen als auch den alten Zahlenwert wieder her. | `crates/engine/src/cmd/parameters_tests.rs:1153-1155`: `run(&mut s, "edit.undo", json!({})); assert!(s.doc.param("wide").is_none()); assert_eq!(expr_of_now(&s, &width), "40");`. | Undo setzt Namen und Wert in einer einzigen Aktion auf den vorherigen Zustand zurück. |

---

## 5. Die 10 wichtigsten Punkte, die ein Inventor-Nutzer zuerst vermissen würde

Ein Konstrukteur, der jahrelang mit Autodesk Inventor gearbeitet hat, bewegt sich flüssig durch eingespielte Reflexe und optische Fixpunkte. Fehlen diese, wirkt die Software unfertig oder fremd. Die folgende priorisierte Liste fasst die 10 kritischsten Punkte zusammen:

1. **Verschachtelung verzehrter Skizzen unter 3D-Features (*Consumed Sketches*):**
   In Inventor gehört eine Skizze unmittelbar zu der Extrusion oder Drehung, die sie verbraucht hat. Ein Klick auf das `+`/Dreieck vor `Extrusion1` klappt `Skizze1` auf. Ein separater Ordner nur für Skizzen (wie im Standard-SolidCraft-Browser) bricht diesen mentalen Zusammenhang auf und erschwert das Auffinden der Profilskizze eines Bauteilbereichs erheblich.
2. **Bauteilende-Marker (*End of Part* / EOP) direkt im Modellbaum:**
   Der EOP-Marker ist in Inventor das universelle Werkzeug zum Debuggen, Zwischenfügen von Features und Prüfen von Konstruktionszuständen. Ein Fehlen des Markers oder die Verbannung in ein separates Zeitleisten-Panel am Bildschirmrand irritiert jeden erfahrenen Konstrukteur sofort.
3. **Abbruch des EOP-Ziehens per Escape-Taste:**
   Verschiebt man die Bauteilende-Markierung in einem Modell mit 50 Features versehentlich an die falsche Stelle, bricht ein geübter Nutzer den Ziehvorgang reflexartig mit **`Esc`** ab, bevor ein zeitaufwendiger Neuaufbau ausgelöst wird.
4. **„Elemente löschen“-Dialog mit Auswahl für einbezogene Skizzen:**
   Löscht man ein 3D-Feature in Inventor, fragt das System sofort über Kontrollkästchen, ob die einbezogene Skizze mitgelöscht oder behalten werden soll. Ohne diese Abfrage verliert der Nutzer beim Löschen eines Fehlversuchs ungewollt seine aufwendig bemaßte Skizzenkontur.
5. **Inline-Parameterdefinition (`Name = Wert`) in Skizzenbemaßungen:**
   Der Standard-Workflow in Inventor lautet: Doppelklick auf ein Maß, Eintippen von `Wandstaerke = 3 mm`, Bestätigen. Dass damit gleichzeitig der Parameter benannt, mit Wert belegt und im gesamten Modell verfügbar gemacht wird, ohne den Parameterdialog öffnen zu müssen, ist einer der größten Produktivitätstreiber.
6. **Vorab-Hervorhebung (*Pre-Highlight / Hover*) zwischen Baum und Viewport:**
   Fährt die Maus über einen Browsereintrag, muss das zugehörige 3D-Volumenkörper- oder Skizzenelement im Ansichtsfenster sofort aufleuchten (und umgekehrt). Ohne diese bidirektionale Kopplung verliert der Nutzer bei komplexen Bauteilen mit vielen ähnlichen Bohrungen und Fasen sofort die Orientierung.
7. **Schnell-Tastenkürzel für Sichtbarkeit (`V`) und Umbenennen (`F2`):**
   Objekt anklicken, **`V`** drücken zum Ausblenden, **`F2`** drücken zum Umbenennen. Dies geschieht in Inventor blind mit der linken Hand, während die rechte Hand die Maus führt.
8. **Doppelklick-Aktionen zur kontextbezogenen Bearbeitung:**
   Doppelklick auf Skizze = Skizzenmodus aktiv; Doppelklick auf Feature = Eigenschaftsdialog offen; Doppelklick auf Unterkomponente = Bearbeitung an Ort und Stelle. Ein Zwang zum Rechtsklick oder Suchen in Menübändern verlangsamt die Arbeit drastisch.
9. **Visuelle Abblendung und Kennzeichnung unterdrückter Features:**
   Unterdrückte Features müssen im Baum unmissverständlich als inaktiv zu erkennen sein (hellgrau, durchgestrichener Text). Bleiben sie optisch identisch mit aktiven Features, ist unklar, warum Geometrie im 3D-Fenster fehlt.
10. **Einheitenkonsistenz und `oE`-Syntax im Gleichungsfeld:**
    Gibt ein Anwender in ein Maßfeld eine geometrisch unzulässige Formel wie `10 mm + 5 deg` ein, erwartet er eine sofortige rote Signalisierung vor dem Schließen des Dialogs. Ebenso erwartet er, dass Faktoren oder Zähler als dimensionslos (`oE` / unitless) berechnet werden können.

---

## 6. Quellenbelege

### Beleg: Inventor Bauteil-Browser Referenz (Symbole)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-5F5D6502-BADB-4539-A5EF-5D00D09D73CE.htm
* **Wörtliches Zitat:** „Bauteil-Browser - Referenz“
* **Wörtliches Zitat:** „Bauteilende-Markierung“
* **Wörtliches Zitat:** „Extrusion zeigt das Volumenkörper-Extrusionselement an.“
* **Wörtliches Zitat:** „Rundung zeigt das zugehörige Rundungselement an.“
* **Wörtliches Zitat:** „Bohrung zeigt das zugehörige Bohrungselement an.“
* **Wörtliches Zitat:** „Fase zeigt das zugehörige Fasenelement an.“
* **Wörtliches Zitat:** „Winkel-iMate zeigt das mit Abhängigkeit Winkel bestimmte iMate an.“

### Beleg: Inventor Bauteil-Browser Referenz (Kontextmenü)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-36DB9904-6DD2-45A4-856A-A843D75C83A1.htm
* **Wörtliches Zitat:** „Element bearbeiten Aktiviert das Dialogfeld Element, in dem Sie die Größe, die Grenzen und andere Werte neu definieren können“
* **Wörtliches Zitat:** „Skizze bearbeiten Aktiviert die Skizze.“
* **Wörtliches Zitat:** „Skizze neu definieren Verschiebt eine Skizze von der ursprünglichen Ebene oder Fläche und ordnet sie einer anderen Ebene bzw. Fläche zu“
* **Wörtliches Zitat:** „Skizze wieder verwenden Wählt eine Skizze aus, die bereits in einem Element verwendet wird, und nutzt diese in einem neuen Element. Platziert eine Kopie der Skizze im Browser.“
* **Wörtliches Zitat:** „Bemaßungen anzeigen Zeigt Skizzenbemaßungen für das ausgewählte Element an. Eingeblendete Bemaßungen können bearbeitet oder gelöscht werden.“
* **Wörtliches Zitat:** „Element unterdrücken Entfernt das Element aus dem Grafikfenster. Im Browser wird es weiterhin angezeigt und durch eine graue Markierung gekennzeichnet. Wenn Sie die Unterdrückung aufheben möchten, klicken Sie mit der rechten Maustaste in den Browser, und wählen Sie Unterdrückung aufheben.“
* **Wörtliches Zitat:** „Sichtbarkeit Aktiviert oder deaktiviert die Sichtbarkeit einer Komponente“
* **Wörtliches Zitat:** „Bauteilende-Markierung verschieben Verschiebt die Bauteilende-Markierung unter das ausgewählte Element oder in den Ordner Ursprung.“
* **Wörtliches Zitat:** „Bauteilende zum Anfang verschieben Wenn sich der Bauteilende-Indikator innerhalb der Bauteilelemente befindet, wird die Anzeige des Bauteilendes im Browser direkt an den Anfang der Elemente verschoben.“
* **Wörtliches Zitat:** „Bauteilende zum Ende verschieben Wenn sich der Bauteilende-Indikator innerhalb der Bauteilelemente befindet, wird die Anzeige des Bauteilendes im Browser direkt an das Ende der Elemente verschoben.“
* **Wörtliches Zitat:** „Alle Elemente unter Bauteilende löschen Löscht alle im Browser unterhalb dieser Markierung aufgeführten Elemente.“
* **Wörtliches Zitat:** „Beim Verschieben der Bauteilende-Markierung können Sie den Vorgang abbrechen, indem Sie die ESC-TASTE drücken. Der Abbruch des Vorgangs wird in einer Meldung bestätigt.“

### Beleg: Inventor Elemente löschen oder unterdrücken
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-983D8293-90EC-4BA7-B756-48685DDE1B00.htm
* **Wörtliches Zitat:** „Geben Sie im Dialogfeld Elemente löschen an, welche zusätzlichen abhängigen Elemente, Skizzen oder Arbeitselemente gelöscht werden sollen:“
* **Wörtliches Zitat:** „Einbezogene Skizzen und Elemente. Diese Option ist standardmäßig ausgewählt. Zusätzlich zum ausgewählten Element werden auch von dem Element einbezogene Skizzen, Flächenelemente und Arbeitselemente gelöscht.“
* **Wörtliches Zitat:** „Abhängige Skizzen und Elemente. Dieses Kontrollkästchen ist automatisch aktiviert, wenn das Element abhängige nicht einbezogene Skizzen und skizzenbasierte Elemente enthält.“
* **Wörtliches Zitat:** „Abhängige Arbeitselemente. Dieses Kontrollkästchen ist automatisch aktiviert, wenn das Element abhängige Arbeitselemente enthält. Wenn Sie beim Löschen des übergeordneten Elements die abhängigen Arbeitselemente beibehalten möchten, deaktivieren Sie das Kontrollkästchen. Beibehaltene Arbeitselemente werden fixiert.“
* **Wörtliches Zitat:** „Mit der ESC-TASTE können Sie eine unerwünschte Neupositionierung der Bauteilende-Markierung im Modell-Browser abbrechen.“
* **Wörtliches Zitat:** „Unterdrückte Elemente werden im Grafikfenster nicht angezeigt und sind im Browser abgeblendet dargestellt.“
* **Wörtliches Zitat:** „Bedingtes Unterdrücken skizzierter oder platzierter Elemente“

### Beleg: Inventor Modellbrowser Bauteilende EOP
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-69196418-14DF-4128-B4F3-581FFC994C78.htm
* **Wörtliches Zitat:** „Suchen Sie unten im Browser das Symbol Bauteilende (oder Element), und ziehen Sie es nach oben, um das Modell in ein früheres Stadium zurückzusetzen.“
* **Wörtliches Zitat:** „Hierdurch werden die Elemente unterhalb des Bauteilende-Symbols vorübergehend aus dem Modell entfernt.“
* **Wörtliches Zitat:** „Um das Modell zu aktualisieren, ziehen Sie das Symbol im Browser wieder nach unten oder klicken mit der rechten Maustaste auf die Bauteilende-Markierung und wählen Bauteilende zum Ende verschieben.“

### Beleg: Inventor Löschen und Unterdrücken von Elementen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-C6A19638-C241-4E35-92D5-6C8D3D78B1C6.htm
* **Wörtliches Zitat:** „Sie können Elemente unter die Markierung Bauteilende ziehen, um sie vorübergehend aus der Bearbeitung auszuschließen.“

### Beleg: Inventor Baugruppen-Browser Ordner
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-5F975252-BDB4-488C-A2C5-8B15C7D3C641.htm
* **Wörtliches Zitat:** „Erstellen Sie Ordner, um die Browser-Knoten in Gruppen zu organisieren oder das Konzept zu kommunizieren.“

### Beleg: Inventor So erstellen und bearbeiten Sie Skizzen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E96FB3C4-136B-4551-BF45-F54594543ECB.htm
* **Wörtliches Zitat:** „Doppelklicken Sie auf das Skizzensymbol im Browser.“
* **Wörtliches Zitat:** „Wenn Sie eine Skizze abbrechen, werden alle aktuellen Aktionen verworfen.“

### Beleg: Inventor Registerkarte Farben (Vorab-Hervorhebung)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-62188BB2-1880-4CDA-91DB-10237FC3ED99.htm
* **Wörtliches Zitat:** „Vorab-Hervorhebung aktivieren“
* **Wörtliches Zitat:** „Objekte werden hervorgehoben, wenn Sie den Cursor darüber bewegen. So erhalten Sie Informationen zu dem Objekt, das Sie auswählen. Vorgabemäßig aktiviert.“

### Beleg: Inventor Registerkarte Allgemein (Wiederherstellungsdatei)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A8E50133-E4FF-4459-B2AE-9568D2C9F565.htm
* **Wörtliches Zitat:** „Größe der Wiederherstellungsdatei (MB)“
* **Wörtliches Zitat:** „Legt die Größe der temporären Datei fest, die Änderungen an einem Modell oder an einer Zeichnung verfolgt, sodass Aktionen rückgängig gemacht werden können.“

### Beleg: Inventor So wählen Sie Objekte aus und heben die Auswahl auf
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B8F6E805-2E4B-4366-8FF6-33F0ED1C1C4A.htm
* **Wörtliches Zitat:** „So wählen Sie Objekte aus und heben die Auswahl auf“
* **Wörtliches Zitat:** „Wählen Sie das Objekt im Grafikfenster aus. Zur Auswahl mehrerer Objekte halten Sie die STRG-Taste oder die Umschalttaste gedrückt, während Sie auf nicht ausgewählte Objekte klicken, um sie zur Auswahl hinzuzufügen.“

### Beleg: Inventor Tastaturkurzbefehle Referenz
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „Aktiviert den Befehl Rückgängig (hebt den letzten Vorgang auf)“
* **Wörtliches Zitat:** „Aktiviert den Befehl Wiederherstellen (hebt den letzten Befehl Rückgängig auf)“

### Beleg: Inventor So arbeiten Sie mit Parametern in Modellen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-595F9D8E-9EEA-4446-91AB-830E5BAE548E.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Verwalten Gruppe Parameter Parameter.“
* **Wörtliches Zitat:** „Erweitern oder reduzieren Sie die Listen Modellparameter und Benutzerparameter.“
* **Wörtliches Zitat:** „Um einen Parameter zu löschen, klicken Sie mit der rechten Maustaste auf die Parameterzeile und wählen Parameter löschen.“
* **Wörtliches Zitat:** „Klicken Sie zum Ändern des Parameternamens, der Gleichung oder des Kommentars auf das entsprechende Feld, um den vorhanden Wert auszuwählen und den neuen Wert einzugeben.“
* **Wörtliches Zitat:** „Wenn Sie ein Element bearbeiten, ändern sich alle abhängigen Parameter mit dem Element.“

### Beleg: Inventor Parameter in Modellen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-8E5C63EA-0540-4EBE-9B17-B8159C7FE40C.htm
* **Wörtliches Zitat:** „Inventor definiert automatisch Modellparameter in Skizzen, Baugruppenabhängigkeiten und Elementen.“
* **Wörtliches Zitat:** „Vor Bemaßungen, die durch eine Gleichung berechnet werden, steht das Präfix fx.“

### Beleg: Inventor So definieren Sie numerische Parameter in Bearbeitungsfeldern
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-9DD43CD9-6391-4D8B-896A-3EC51041495B.htm
* **Wörtliches Zitat:** „Geben Sie im Dialogfeld Bemaßung bearbeiten für diese Linie als Länge = 20 mm ein, und klicken Sie auf das grüne Häkchen, um den Eintrag zu übernehmen. Wenn Sie das Dialogfeld Parameter öffnen, um die definierten Modellparameter anzuzeigen, hat der Parameter Länge den Wert 20 mm.“
* **Wörtliches Zitat:** „Ein korrekt eingegebener Ausdruck wird in einem Bearbeitungsfeld schwarz angezeigt. Ungültige oder nicht erkannte Syntax wird in Rot angezeigt.“

### Beleg: Inventor Ausdrucksreferenz für numerische Parameter
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-0106478A-B340-4164-A81B-866062877D60.htm
* **Wörtliches Zitat:** „Eine Gleichung kann einfach sein, kann aber auch viele algebraische Operatoren, Präfixe und Funktionen enthalten. Dies hier ist z. B. eine einfache Gleichung:“
* **Wörtliches Zitat:** „2 oE *(6+3)“
* **Wörtliches Zitat:** „; Trennzeichen für Funktionen mit mehreren Argumenten“
* **Wörtliches Zitat:** „Im Bearbeitungsfeld werden allen Termen Standardeinheiten zugewiesen, wenn keine Einheit angegeben ist. Die Ergebnisse führen zu einem Fehler, da ungleiche Einheiten nicht addiert werden können“

### Beleg: Inventor Komponente in der Baugruppe erstellen (Referenz)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-FBBE5A60-AE37-4087-81D7-AA91330D1B01.htm
* **Wörtliches Zitat:** „Erstellen Sie Komponenten in einer Baugruppe mit einem Arbeitsablauf von oben nach unten.“
* **Wörtliches Zitat:** „Registerkarte Zusammenfügen Gruppe Komponente Erstellen“
