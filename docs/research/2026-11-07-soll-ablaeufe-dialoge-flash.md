# Recherche: Soll-Abläufe für Feature-Dialoge (Inventor vs. SolidCraft vs. Mechvane)

- **Datum:** 2026-11-07
- **Autor:** Gemini 3.8 Flash (Issue #56)
- **Status:** Verifiziert mit `python3 tools/check_sources.py docs/research/2026-11-07-soll-ablaeufe-dialoge-flash.md` und gegen Sparse-Klon `/root/repos/_ext/solidcraft` (Stand v0.25.1)
- **Prüfnotiz (Claude, 2026-11-07):** `check_sources.py`: alle Inventor-Zitate und Zahlen belegt. SolidCraft-Fundstellen sind Stichproben gegen den Klon vom 2026-11-07 (nach v0.30.1); Zeilennummern können verschoben sein. Nicht bestätigt: „`solid.revolve` hat kein Standard-Tastenkürzel“.
- **Kontext & Ziel:** Als Entscheidungsgrundlage für die browserbasierte Mechvane-Oberfläche (v0.1) dokumentiert dieser Bericht die Soll-Abläufe und Standard-Verhaltensweisen für die sieben wichtigsten 3D-Feature-Dialoge:
  1. **Extrusion** (`solid.extrude`)
  2. **Drehung** (`solid.revolve`)
  3. **Bohrung** (`solid.hole`)
  4. **Rundung** (`solid.fillet`)
  5. **Fase** (`solid.chamfer`)
  6. **Muster** (Rechteckig & Kreisförmig: `solid.pattern.rectangular`, `solid.pattern.circular`)
  7. **Spiegeln** (`solid.mirror`)

Damit der Anwender Standardverhalten nicht erklären muss und Claude den heutigen Implementierungsstand dagegen prüfen kann, wird je Dialog systematisch untersucht:
welche Eingabe zuerst verlangt wird, was vorgewählt ist, Vorschau, Richtung umkehren, Abschlussarten (Abstand, durch alle, bis Fläche, zwischen), Operationen (Vereinigen, Ausschneiden, Schnitt, Neuer Körper), Mehrfachauswahl von Kanten und Ketten, Fehlermeldungen und Sonderfälle, Tastenkürzel, OK/Anwenden/Abbrechen sowie das Bearbeiten über den Browser.

---

## 1. Allgemeine Dialog-Architektur und Interaktionskonzepte

### 1.1 Autodesk Inventor: Eigenschaftsgruppen (Property Panels) und HUD
In modernen Inventor-Versionen (2020–2026) wurden herkömmliche modale Dialogfelder für 3D-Features durch **Eigenschaftsgruppen** (*Property Panels*) abgelöst:
- **Fluss von oben nach unten:** „Der Arbeitsablauf in der Gruppe Eigenschaften verläuft von oben nach unten. Jede Eigenschaftsgruppe verfügt über Breadcrumbs, die den Kontext angeben und über die Sie schnell zwischen der Element- und der Skizzenbearbeitung wechseln können.“ ([Beleg: Eigenschaftsgruppen](#beleg-inventor-eigenschaftsgruppen)).
- **Breadcrumbs:** Am oberen Rand der Gruppe wird der hierarchische Pfad (z. B. `Bauteil > Skizze 1 > Extrusion 1`) eingeblendet. Ein Klick auf den Skizzen-Breadcrumb öffnet direkt die Skizze zur Bearbeitung; nach Skizzenabschluss kehrt Inventor nahtlos in den Feature-Dialog zurück.
- **Tastaturnavigation:**
  - `TABULATORTASTE`: Springt schrittweise zum nächsten Wertefeld ([Beleg: Eigenschaftsgruppen](#beleg-inventor-eigenschaftsgruppen)).
  - `EINGABETASTE`: Wendet die aktuelle Wertbearbeitung an ([Beleg: Eigenschaftsgruppen](#beleg-inventor-eigenschaftsgruppen)).
  - `STRG + EINGABETASTE`: Beendet die Elementdefinition, erstellt das Element und schließt die Eigenschaftsgruppe ([Beleg: Eigenschaftsgruppen](#beleg-inventor-eigenschaftsgruppen)).
  - `ESC`: Bricht den Befehl ab und schließt die Gruppe ([Beleg: Vordefinierte Kurzbefehle](#beleg-inventor-vordefinierte-kurzbefehle)).
- **Interaktionszustand:** Schaltflächen `OK`, `Anwenden` (`+`, Element erstellen und Dialog für nächste Operation geöffnet halten) und `Abbrechen`.

### 1.2 SolidCraft: Architektur in `crates/ui-egui/src/dialogs.rs`
SolidCraft bildet Dialoge deklarativ über die Datenstruktur `Dialog` und die Aufzählung `Kind` ab:
- **Zustandsmaschine:** `Dialog::for_command(app, cmd)` initialisiert die Wertefelder (`Kind`) und die Eingabeschlitze `pub inputs: Vec<SelInput>` (`crates/ui-egui/src/dialogs.rs:895-1045`).
- **Fokus & Auswahl:** Viewport-Klicks werden an den aktuell aktiven Schlitz `d.active` weitergeleitet. Sobald eine Auswahl vollständig ist, schaltet SolidCraft häufig automatisch auf den nächsten Schlitz weiter.
- **Tastatursteuerung:** In `crates/ui-egui/src/dialogs.rs:4022-4028` verarbeitet SolidCraft `Key::Enter` als `Apply` und `Key::Escape` als `Cancel`:
  `// Keyboard: Enter applies (from a value field, or with nothing focused), Esc cancels.`
  `let (enter_free, esc) = ctx.input(|i| (i.key_pressed(egui::Key::Enter), i.key_pressed(egui::Key::Escape)));`
- **Aktionen:** Die Schaltflächenleiste emittiert `Action::Ok`, `Action::Apply` (setzt `apply_again = true`) und `Action::Cancel` (`crates/ui-egui/src/dialogs.rs:3943-3955`).

---

## 2. Soll-Abläufe der Feature-Dialoge im Detail

### 2.1 Extrusion (`solid.extrude`)

Die lineare Materialaufdickung oder der lineare Abtrag entlang der Profilnormalen.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Profilauswahl aktiv. Wenn nur 1 geschlossenes Profil in der Skizze vorliegt, wird dieses automatisch gewählt: „Ein Profil - Enthält die Skizze nur ein geschlossenes Profil, wird dieses automatisch ausgewählt.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `vec![SelInput::new("Profiles", EXTRUDE_ACCEPT, true)]` (`dialogs.rs:913`). Das neue Profil wird sofort übernommen: `// The new sketch's profile is taken at once.` (`dialogs.rs:8208-8209`). | Profil-Picker ist aktiv. Enthält die Skizze genau 1 geschlossenes Profil, wird es automatisch selektiert und der Cursor springt direkt ins Abstandsfeld. |
| **2. Vorbelegung (Defaults)** | Vorgabemäßig Volumenkörper: „Vorgabemäßig erstellen Sie mit der Option Extrusion einen Volumenkörper aus einem offenen oder geschlossenen Profil.“ Startet auf Skizzierebene: „Von - Als Vorgabe beginnt die Extrusion auf der Skizzierebene.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `distance: length_default(s, "10")`, `direction: 0`, `operation: usize::from(has_bodies)`, `auto_op: true`, `taper: "0 deg".into()` (`dialogs.rs:896-904`). | Standard-Abstand $10\,\text{mm}$; Start auf Skizzierebene; Operation automatisch `New Body` (wenn Bauteil leer) oder `Join` (wenn Körper existiert). |
| **3. Vorschau** | 3D-Vorschau mit Richtungsanzeige: „Der Befehl zeigt eine Vorschau der Richtung der Booleschen Operation an.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `SELECT_MANIP: &[Scope::Selection, Scope::Manipulator, Scope::FeaturePreview]` (`dialogs.rs:34, 39`) über `StraightPreview` (`extrude_preview.rs:16-30`). | Live-3D-Vorschau im Ansichtsfenster: Halbtransparentes Volumen mit Richtungspfeil; Blau/Grün für Addition, Rot für Subtraktion. |
| **4. Richtung umkehren** | 4 Richtungsoptionen: Vorgabe (Einseitig), Umgekehrt, Symmetrisch, Asymmetrisch: „Symmetrisch - Extrudiert in die entgegengesetzten Richtungen von der Skizzierebene und verwendet dabei die Hälfte des angegebenen Werts für Abstand A in jede Richtung.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `DIRS: [&str; 5] = ["positive", "negative", "symmetric", "positive", "negative"]` (`dialogs.rs:85`), `pub const TWO_SIDES: usize = 3;` (`dialogs.rs:87`), `convention?: total_distance` (`features.rs:42`). | 4 Buttons/Icons: Einseitig, Umgekehrt, Symmetrisch (Gesamtabstand!), Zwei Seiten (asymmetrisch mit `distance2`). Pfeil im Viewport klickbar zum Umkehren. |
| **5. Abschlussarten** | Abstand, Durch alle, Zur Nächsten: „Durch alle - Extrudiert das Profil durch alle Elemente und Skizzen hindurch in der angegebenen Richtung.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `distance: expr (or through_all: true)`, `all: bool` (`dialogs.rs:189`), `to?: [x,y,z]` (`features.rs:42`), `from?: [x,y,z]` (`features.rs:42`). | Dropdown mit: `Abstand` (Distance), `Durch alle` (Through All), `Bis Fläche/Körper` (To Object) mit partiellem Offset, `Von Fläche` (From Object). |
| **6. Boolesche Operationen** | Vereinigung, Differenz, Schnittmenge, Neuer Volumenkörper: „Vereinigung - Fügt das durch das extrudierte Element erstellte Volumen einem anderen Element oder Körper hinzu.“ / „Differenz - Entfernt das durch das extrudierte Element erstellte Volumen...“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `pub(crate) const OPS: [&str; 4] = ["new", "join", "cut", "intersect"];` (`dialogs.rs:83`), `auto_op: true`: `/// Into a body: cut; additions: join when a solid exists, otherwise new.` (`dialogs.rs:173-175`). | 4 Operationen: `Vereinigen` (Join), `Ausschneiden` (Cut), `Schnittmenge` (Intersect), `Neuer Körper` (New Body). Intelligente Auto-Vorwahl (`auto_op`). |
| **7. Mehrfachauswahl / Ketten** | Mehrere Profile per Klick oder Fenster: „Sie können einen Auswahlrahmen verwenden, um schnell mehrere geschlossene Profile in der Skizze auszuwählen.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | `SelInput::new("Profiles", EXTRUDE_ACCEPT, true)` (`dialogs.rs:913`), mehrere koplanare Flächen `faces?: [[x,y,z], ...]` (`dialogs.rs:5229`), dünne Wandung `thin: bool`, `curves?: [curve ids]` (`dialogs.rs:5186`). | Mehrfachauswahl für Profile und Planarflächen; Checkbox für "Dünne Extrusion" (Thin Extrude) entlang offener oder geschlossener Kurvenzüge. |
| **8. Fehlermeldungen / Sonderfälle** | Automatische Flächenerweiterung: „Flächendehnung bis Endelement - Wird automatisch aktiviert, wenn die Auswahl Von das extrudierte Profil nicht schneidet.“ Form anpassen bei offenen Profilen ([Beleg: Extrusion](#beleg-inventor-extrusion)) | Verweigerung bei leeren Booleschen Schnitten: `"boolean Cut: the operation failed: no result..."` (`dialogs.rs:8145`), Berührungsbehandlung: `touching?: separate\|one_body` (`features.rs:42`), Eckenverjüngung: `corner?: preserve_curvature\|tangent\|round` (`features.rs:42`). | Eindeutige Fehlermeldung bei Schnittfehlschlag ("Schnitt schneidet keinen Körper"); automatische Dehnung bis Zielkörper; Verjüngungswinkel (Taper Angle). |
| **9. Tastenkürzel** | Taste `E` startet Extrusion: „Extrusion Aktiviert den Befehl Extrusion.“ ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)) | `CommandSpec::new("solid.extrude", "Extrude", ...).key("E")` (`crates/engine/src/cmd/features.rs:36-39`). | Taste `E` öffnet im 3D-Modus sofort die Extrusion. |
| **10. Bestätigen / Abbrechen** | `Enter` (Wert anwenden), `Strg+Enter` (OK), `Esc` (Abbrechen) ([Beleg: Eigenschaftsgruppen](#beleg-inventor-eigenschaftsgruppen)), Schaltfläche `+` (Anwenden). | `Enter` wendet an, `Esc` bricht ab (`dialogs.rs:4023`), Buttons `Ok`, `Cancel`, `Apply` (`dialogs.rs:3943-3955`). | `Enter` = OK & Schließen; `Shift+Enter` = Anwenden & Dialog offen halten; `Esc` = Abbrechen. |
| **11. Bearbeiten über Browser** | Rechtsklick > Element bearbeiten oder Klick auf Breadcrumb: „Klicken Sie im Grafikfenster oder Browser mit der rechten Maustaste auf das Element, und wählen Sie Element bearbeiten.“ ([Beleg: Extrusion](#beleg-inventor-extrusion)) | Rechtsklick / Doppel-Klick ruft `ui.editFeature` auf (`dialogs.rs:6658`), setzt `d.editing = Some((id, marker))` (`dialogs.rs:510`). | Doppelklick im Modellbaum öffnet Extrusions-Dialog; Breadcrumb oben erlaubt Rücksprung in die Skizze. |

---

### 2.2 Drehung (`solid.revolve`)

Rotation eines ebenen Profils um eine definierte Drehachse.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Profilauswahl aktiv. Wenn 1 Profil und 1 Achse vorhanden sind, automatische Vorwahl: „Liegt in der Skizze nur eine sichtbare Skizze mit nur einem Profil und einer Achse vor, wird diese automatisch als Eingabegeometrieprofil ausgewählt, und eine Vorschau wird angezeigt.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `vec![SelInput::new("Profile", PROFILES \| PLANAR_FACES, true), SelInput::new("Axis", AXIS_PICKS, false)]` (`dialogs.rs:917`). Profil ist erstes Eingabefeld, Achse das zweite. | Profil-Picker ist initial aktiv. Wenn Skizze nur 1 Profil hat, dieses selektieren und Fokus sofort auf Achs-Picker setzen. |
| **2. Vorbelegung (Defaults)** | Vorgabemäßig Volumenkörper, Drehwinkel $360^\circ$ (Vollständig): „Volumenkörper (Vorgabe) - Erstellt aus einem offenen oder geschlossenen Profil einen neuen Volumenkörper.“ / „Vollständig: Dreht das Profil um ganze 360 Grad.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `Kind::Revolve { angle: "360 deg".into(), operation: 0, axis: None }` (`dialogs.rs:916`). | Standard-Winkel $360^\circ$ (Vollständig); Operation `Join` (bei bestehendem Körper) oder `New Body`. |
| **3. Vorschau** | 3D-Vorschau mit Bearbeitungsmöglichkeit für Maße: „Wichtig: Bei der Elementvorschau können sichtbare Skizzenbemaßungen bearbeitet werden, ohne die Skizzierumgebung aufzurufen.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | Manipulator & FeaturePreview: `ToolModifiers { tool: "solid.revolve", scopes: SELECT_MANIP, ... }` (`dialogs.rs:40`). | Interaktive 3D-Rotationsvorschau mit Bogen-Manipulator im Grafikfenster zum Ziehen des Winkels. |
| **4. Richtung umkehren** | 4 Richtungen: Vorgabe, Umgekehrt, Symmetrisch, Asymmetrisch: „Symmetrisch: Dreht in die entgegengesetzten Richtungen von der Skizzierebene... Asymmetrisch: Dreht in die entgegengesetzten Richtungen von der Skizzierebene und verwendet dabei zwei Werte: Winkel A und Winkel B.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `direction?: symmetric`, `angle2?: expr` (Two Sides), `convention?: sketch_normal\|legacy_axis_start` (`features.rs:46`), `remembered_extra_keys`: `&["angle2", "direction"]` (`dialogs.rs:4271`). | Buttons: Einseitig, Umgekehrt, Symmetrisch, Zwei Winkel (Asymmetrisch). Pfeil-Manipulator zum Umschalten. |
| **5. Abschlussarten** | Vollständig ($360^\circ$), Winkel, Bis Fläche/Ebene, Zur Nächsten: „Bis: Erfordert bei Bauteildrehungen eine Endfläche bzw. -ebene, auf der die Drehung ausgeführt werden soll.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `angle?: expr (default 360 deg)`, `to?: [x,y,z] (To Object: turn until that face, vertex or point)` (`features.rs:46`). | Vollständig ($360^\circ$), Winkel (mit Grad-Eingabe), Bis Objekt/Fläche (`to`). |
| **6. Boolesche Operationen** | Vereinigung, Differenz, Schnittmenge, Neuer Volumenkörper: „Vereinigung: Fügt das durch das Drehelement erstellte Volumen einem anderen Element oder Körper hinzu.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `operation?: new\|join\|cut\|intersect\|auto` (`features.rs:46`). | 4 Standard-Operationen (Join, Cut, Intersect, New Body) mit Auto-Erkennung. |
| **7. Mehrfachauswahl / Achswahl** | Mehrere Profile wählbar. Achse kann Skizzenlinie, Kante oder Arbeitsachse sein: „Achse - Klicken Sie mit der rechten Maustaste in die Anzeige, und wählen Sie Weiter aus, oder klicken Sie auf die Eigenschaftengruppen-Auswahl, und wählen Sie dann eine Achse aus der aktiven Skizze aus.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `SelInput::new("Profile", PROFILES \| PLANAR_FACES, true)`, `SelInput::new("Axis", AXIS_PICKS, false)` (`dialogs.rs:917`). Achse akzeptiert Skizzenlinie, X/Y-Skizzenachse, X/Y/Z-Weltachse, Konstruktionsachse oder zylindrische Kante/Fläche (`features.rs:46`). | Mehrfachauswahl für Profile; Achsen-Picker akzeptiert Skizzenlinien, Modellkanten, Zylinderflächen und Koordinatenachsen. |
| **8. Fehlermeldungen / Sonderfälle** | Schnitt der Achse durch das Profil führt zu Fehlermeldung; "Form anpassen" bei offenen Profilen: „Bei aktivierter Option Form anpassen wird ein Drehelement vom Typ Füllen erstellt.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | Verweigerung bei sich selbst schneidender Geometrie; Berührungsregeln: `touching?: separate\|one_body` (`features.rs:46`). | Warnung, wenn Drehachse das Profil schneidet; Unterstützung für offene Profile mit Flächenerweiterung. |
| **9. Tastenkürzel** | Taste `R` startet Drehung: „Drehung Aktiviert den Befehl Drehung.“ ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)) | **Kein Kürzel** in SolidCraft (`features.rs:43-46`), da Taste `R` in SolidCraft für 2-Punkt-Rechtecke in Skizzen belegt ist! | **Konflikt lösen:** Im 3D-Modus muss Taste `R` die Drehung (`solid.revolve`) aufrufen (wie Inventor!). |
| **10. Bestätigen / Abbrechen** | `OK`, `Neues Element erstellen` (`+`), `Enter`, `Esc`: „Klicken Sie auf OK oder (Neues Element erstellen), um die Definition von Drehelementen fortzusetzen.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `Enter` wendet an, `Esc` bricht ab (`dialogs.rs:4023`), Apply (`dialogs.rs:3952`). | `OK` (Enter), `Anwenden` (Shift+Enter), `Abbrechen` (Esc). |
| **11. Bearbeiten über Browser** | Rechtsklick > Element bearbeiten oder Klick auf Breadcrumb: „Um die Elementskizze zu bearbeiten, klicken Sie im Breadcrumb-Text der Eigenschaftengruppe auf die Skizzennummer und beginnen mit der Bearbeitung der Skizze.“ ([Beleg: Drehung](#beleg-inventor-drehung)) | `ui.editFeature` (`dialogs.rs:6658`, `revolve_edit_tests.rs`). | Doppelklick im Modellbaum öffnet Drehelement-Dialog; Breadcrumb erlaubt direkten Sprung in die Skizze. |

---

### 2.3 Bohrung (`solid.hole`)

Platzierte Bohrungen mit Senkungen, Gewinden und flexiblen Platzierungsmodi.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Flächen- oder Punkt-Auswahl aktiv. Keine Skizze zwingend nötig: „Geben Sie die Positionen an. Es ist keine vorhandene Skizze erforderlich. Zu den gültigen Eingaben für die Bohrungspositionen zählen Fläche Skizzierpunkt (Ende oder Mitte) sowie Arbeitspunkt.“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | `single_hole_inputs()`: `vec![SelInput::new("Face", HOLE_FACES, true)]` + `crate::hole_refs::inputs()` (`dialogs.rs:441-444`). Klick ohne Fläche wirft: `error: "first pick a face"` (`dialogs.rs:7995`). | Flächen-Picker ist aktiv. Klick auf eine ebene Fläche setzt die Bohrung und schaltet Kantenreferenz-Felder frei. |
| **2. Vorbelegung (Defaults)** | Einfache Bohrung, Aufsatztyp Keine, Durch alle oder Abstand: „Bohrungstyp Bei einer einfachen Bohrung wird eine Bohrung ohne Gewinde erstellt.“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | `hole_defaults`: `diameter: "5 mm"`, `depth: "10 mm"`, `kind: 0` (Simple), `cb_diameter: "9 mm"`, `cb_depth: "3 mm"`, `cs_diameter: "10 mm"`, `cs_angle: "90 deg"`, `angled: true`, `tip_angle: "118 deg"`, `tapped: false`, `thread: "M5"`, `hand: Right` (`dialogs.rs:4646-4656, 480-499`). | Einfache Bohrung, $5\,\text{mm}$ Durchmesser, $10\,\text{mm}$ Tiefe (oder Durch alle), $118^\circ$ Bohrspitze (DIN/ISO-Standard). |
| **3. Vorschau** | 3D-Vorschau mit dynamischen Maßen: „Vorschausteuerelemente stehen während der Bearbeitung von Elementen und Skizzen zur Verfügung.“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | Schnittbild im Dialog: `pub(crate) fn preview(ui: &mut egui::Ui, form: &Kind, ...)` (`dialogs_hole.rs:113`) und 3D-Vorschau (`dialogs.rs:73`). | 3D-Bohrungszylinder halbtransparent im Modell; dynamische Schnittansicht im Dialog mit bemaßten Feldern. |
| **4. Richtung umkehren** | Richtungsumkehr-Button: „Richtung 2: Kehrt die Bohrungsrichtung um.“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | `direction?: [x,y,z] (default: into the face, against its outward normal...)`, `flip?: bool` (`features.rs:108`), `hole_direction_ui_tests.rs`. | Manipulator-Pfeil im Ansichtsfenster zum Umschlagen der Bohrrichtung in die Gegenwand. |
| **5. Abschlussarten** | Abstand, Durch alle, Bis Fläche ([Beleg: Bohrung](#beleg-inventor-bohrung)). Bei Blech Vorgabe `Stärke`. | `depth? (default through all) \| to?: [x,y,z]` (`features.rs:108`), `opts.all: bool` (`dialogs.rs:453`). | Abstand (Sackloch), Durch alle (Through All), Bis Fläche (To Object). |
| **6. Aufsatz- und Bohrungstypen** | 4 Aufsatztypen: Keine, Zylindrische Senkung, Ansenkung, Flachsenkung; Bohrungstypen: Einfach, Durchgang, Gewinde, Verjüngt: „Bohrungsspitze Flach: Erstellt einen flachen Bohrungspunkt. Winkel: Erstellt Bohrungsspitzen.“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | `type?: simple\|drilled\|counterbore\|countersink`, `cb_diameter`, `cb_depth`, `cs_diameter`, `cs_angle`, `bridge?: length` (3D-Druck-Brücke), Gewinde ISO/UNC/G/NPT (`features.rs:108`, `dialogs_thread.rs`). | Kachel-Auswahl: Einfach, Flachsenkung (Zylindrisch), Kegelsenkung, Gewindebohrung (kosmetisch oder modelliert mit `modeled: true`), 3D-Druck-Brücke (`bridge`). |
| **7. Positionierung / Mehrfach** | Linear (2 Kanten), Konzentrisch, Skizzenpunkte, Freie Punkte: „Klicken Sie auf eine Referenzkante, um die Bemaßungen zu platzieren. Bemaßungen für die lineare Platzierung können ausgewählt, bearbeitet oder gelöscht werden...“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | Bis zu 2 Referenzkanten: `references?: [{edge: [x,y,z] on a straight edge of the face, distance: expr}]` (`features.rs:108`), oder Skizzenpunkte: `sketch + points: [sketch point ids]` (`features.rs:108`, `dialogs.rs:451`). | 1. Linear (Klick auf Fläche + 2 Kantenabstände); 2. Konzentrisch (Klick auf Rundungskante); 3. Skizzenpunkte (Mehrfachbohrung aus Skizze). |
| **8. Fehlermeldungen / Sonderfälle** | Warnung bei Gewindetiefe > Bohrungstiefe: „Visuelles Feedback zur Wertänderung - Wenn ein Wert ungültig ist, beispielsweise, wenn die angegebene Gewindetiefe größer ist als die Bohrungstiefe, wird der Text im Wertefeld rot angezeigt...“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | Verweigerung: `thread_depth?: positive length independent of drill depth (... must fit that wall)` (`features.rs:108`), Verweigerung ohne Fläche: `"first pick a face"` (`dialogs.rs:7995`). | Rote Feldmarkierung, wenn Gewindetiefe > Bohrtiefe; automatische Berechnung der Kernlochbohrung nach Normteilkatalog. |
| **9. Tastenkürzel** | Taste `H` startet Bohrung: „Bohrung Aktiviert den Befehl Bohrung.“ ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)) | `CommandSpec::new("solid.hole", "Hole", ...).key("H")` (`crates/engine/src/cmd/features.rs:104-107`). | Taste `H` öffnet im 3D-Modus den Bohrungs-Dialog. |
| **10. Bestätigen / Abbrechen** | `OK`, `Bohrung erstellen (+)` (Apply), `Enter`, `Esc`: „Klicken Sie auf OK, oder klicken Sie zum Erstellen einer weiteren Bohrung mit der aktuellen Definition auf Bohrung erstellen (+).“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | `Enter` wendet an, `Esc` bricht ab (`dialogs.rs:4023`), Apply (`dialogs.rs:3952`). | `OK` (Enter), `+` (Bohrung erstellen / Apply), `Abbrechen` (Esc). |
| **11. Bearbeiten über Browser** | Doppelklick oder Rechtsklick > Element bearbeiten: „Doppelklicken Sie auf den Elementknoten. Klicken Sie mit der rechten Maustaste auf den Elementknoten, und wählen Sie Element bearbeiten aus.“ ([Beleg: Bohrung](#beleg-inventor-bohrung)) | `ui.editFeature` (`dialogs.rs:8041`). Nach Flächenverschiebung wird die Seed-Fläche angepasst (`dialogs.rs:8057-8082`, `#10689`). | Doppelklick auf Bohrungsknoten im Baum öffnet Bohrungsdialog; Referenzmaße bleiben editierbar. |

---

### 2.4 Rundung (`solid.fillet`)

Verrundung von Modellkanten mit konstantem, variablem oder stetigem Radius.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Kantenauswahl sofort aktiv: „In der Gruppe Eigenschaften ist Kantensätze mit konstantem Radius sofort aktiv. Sie können mit der Auswahl von Modellkanten beginnen.“ ([Beleg: Rundung](#beleg-inventor-rundung)) | `vec![SelInput::new("Edges", EDGES \| FACES, true)]` (`dialogs.rs:919`). Kanten- und Flächenpicker sofort aktiv. | Kanten-Picker hat sofortigen Fokus. Klicks im Grafikfenster fügen Kanten zum Auswahlsatz hinzu. |
| **2. Vorbelegung (Defaults)** | Konstanter Radius, Tangentiale Kette aktiviert: „Alle Kanten (Vorgabe): Wendet sowohl Abrundungen als auch Rundungen an.“ Kontinuität G1 (Tangential) ([Beleg: Rundung](#beleg-inventor-rundung)) | `radius: length_default(s, "2")` (2 mm), `chamfer: false`, `chain: true`, `corner: rolling`, `fit: exact` (`dialogs.rs:919`, `features.rs:88`). | Standard-Radius $2\,\text{mm}$; Tangentiale Kantenkette vorgewählt; G1-Übergang. |
| **3. Vorschau** | Dynamische 3D-Vorschau mit Manipulator-Griff am Radius ([Beleg: Rundung](#beleg-inventor-rundung)) | Manipulator & FeaturePreview: `ToolModifiers { tool: "solid.fillet", scopes: SELECT_MANIP, ... }` (`dialogs.rs:41`). | Live-Vorschau der Rundungsflächen im Ansichtsfenster mit Pfeil-Manipulator zum Ziehen des Radius. |
| **4. Stetigkeit (G1 vs. G2)** | G1 (Tangential) und G2 (Krümmungsstetig): „Wendet tangentiale (G1) Abrundungen auf benachbarte Flächen an.“ / „Wendet stetige (G2) Abrundungen mit Krümmungsstetigkeit auf benachbarte Flächen an.“ ([Beleg: Rundung](#beleg-inventor-rundung)) | `type?: constant\|curvature (alias g2: curvature-continuous quintic between planar faces along straight edges...)` (`features.rs:88`). | Umschalter G1 (Tangential) vs. G2 (Krümmungsstetig / Curvature Continuous). |
| **5. Kantenketten & Mehrfachauswahl** | Tangentiale Kantenverfolgung: „Fortlaufende Kanten. Legt die Voreinstellung zur Kantenauswahl für Kantenrundungen fest. Aktivieren Sie das Kontrollkästchen, um beim Auswählen einer zu rundenden Kante automatisch alle tangentialen Kanten auszuwählen.“ ([Beleg: Rundung](#beleg-inventor-rundung)) | `tangent_chain?: bool (default true: each picked edge's tangent chain is rounded with it; false: exactly the picked edges)` (`features.rs:88`), `d.sync_fillet_chain(&app.session)` (`dialogs.rs:3917, 3923`). | Checkbox "Tangentiale Kette" (vorgewählt); Mehrfachauswahl durch Klick oder Auswahlfenster; Umschalt-Klick zum Entfernen. |
| **6. Eckenausführung (Setbacks)** | Eckenausführung hinzufügen bei 3+ Kanten: „Eckenausführung hinzufügen... Geben Sie unter Verhalten der Eckenausführung den Abstand für Eckenausführung an.“ / Minimal ([Beleg: Rundung](#beleg-inventor-rundung)) | `corner?: rolling\|g2`, `setbacks?: [{vertex: [x,y,z], distance: expr}]` (Standard: $1{,}5 \times \text{Radius}$), `setback: Option<String>` (`features.rs:88`, `dialogs.rs:215-218`). | Ecken-Rücksprung (Setback) editierbar bei Zusammentreffen von 3 Kanten an einer Ecke (Standard $1{,}5 \times R$). |
| **7. Auswahlfilter** | Kante, Kontur, Element, Volumenkörper ([Beleg: Rundung](#beleg-inventor-rundung)) | `EDGES \| FACES` (`dialogs.rs:919`). Klick auf Fläche verrundet alle Begrenzungskanten. | Filter-Umschalter: Kante, Kontur (Loop), Feature, Alle Kanten des Körpers. |
| **8. Fehlermeldungen / Sonderfälle** | Gelegentliche Verschmelzungsfehler bei zu großem Radius: „Gelegentlich wird eine Meldung angezeigt, die besagt, dass die ausgewählten Kanten nicht verschmolzen werden können... Verringern Sie die Abrundungsgröße.“ ([Beleg: Rundung](#beleg-inventor-rundung)) | `pub(crate) fn fillet_plain_error(error: &str, setback_in_field: bool) -> Option<FilletRefusal>` (`dialogs.rs:3347`), Kern meldet Maximalwert: `fit?: exact\|reduce\|taper` (`features.rs:88`). | Wenn Radius zu groß für Geometrie: Klare Rückmeldung mit Angabe des maximal möglichen Radius ("Maximal möglich: X mm"). |
| **9. Tastenkürzel** | Taste `F` startet Rundung: „Erstellt eine Rundung.“ ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)) | `CommandSpec::new("solid.fillet", "Fillet", ...).key("F")` (`crates/engine/src/cmd/features.rs:82-86`). | Taste `F` öffnet im 3D-Modus den Rundungs-Dialog. |
| **10. Bestätigen / Abbrechen** | `OK`, `Anwenden`, `Enter`, `Esc`: „Klicken Sie auf OK, um den Vorgang abzuschließen und die Gruppe Eigenschaften zu schließen. Klicken Sie auf Anwenden, um mit dem Anwenden von Abrundungen und Rundungen fortzufahren.“ ([Beleg: Rundung](#beleg-inventor-rundung)) | `Enter` wendet an, `Esc` bricht ab (`dialogs.rs:4023`), Apply (`dialogs.rs:3952`). | `OK` (Enter), `Anwenden` (Shift+Enter), `Abbrechen` (Esc). |
| **11. Bearbeiten über Browser** | Doppelklick oder Rechtsklick > Element bearbeiten: „Klicken Sie im Browser mit der rechten Maustaste auf das Element, und wählen Sie Element bearbeiten. Doppelklicken Sie im Browser auf das Element.“ ([Beleg: Rundung](#beleg-inventor-rundung)) | `ui.editFeature` (`dialogs.rs:6658`). | Doppelklick auf Rundungselement im Modellbaum; Kanten und Radien werden sofort editierbar. |

---

### 2.5 Fase (`solid.chamfer`)

Abschrägung von Modellkanten durch Abstände oder Winkel.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Kantenauswahl sofort aktiv: „Wählen Sie die Kante, die Kanten oder die Flächen und Kanten aus, die gefast werden sollen.“ ([Beleg: Fase](#beleg-inventor-fase)) | `vec![SelInput::new("Edges", EDGES \| FACES, true)]` (`dialogs.rs:920`). | Kanten-Picker hat sofortigen Fokus. |
| **2. Vorbelegung (Defaults)** | Methode Abstand (gleicher Abstand beidseitig): „Abstand. Definiert eine Fase mit demselben Versatzabstand von der Kante an beiden Flächen.“ ([Beleg: Fase](#beleg-inventor-fase)) | `distance: length_default(s, "1")` (1 mm), `chamfer: true`, `ctype: 0` (Gleicher Abstand), `flip: false` (`dialogs.rs:920, 209-214`). | Standard-Fase $1\,\text{mm}$ mit gleichem Abstand ($45^\circ$). |
| **3. Vorschau** | 3D-Vorschau mit Abstandsindikatoren und Manipulatoren ([Beleg: Fase](#beleg-inventor-fase)) | Manipulator & FeaturePreview: `ToolModifiers { tool: "solid.chamfer", scopes: SELECT_MANIP, ... }` (`dialogs.rs:42`). | 3D-Vorschau der Fasenflächen im Ansichtsfenster mit Manipulator. |
| **4. Definitionstypen (Methoden)** | 3 Methoden: 1. Abstand (gleich), 2. Abstand und Winkel, 3. Zwei Abstände: „Abstand und Winkel. Definiert eine Fase mittels des Versatzes von einer Kante und eines Winkels von einer Fläche zum Versatz.“ / „Zwei Abstände. Erstellt eine Fase an einer oder mehreren Kanten mit einem für jede Fläche festgelegten Abstand.“ ([Beleg: Fase](#beleg-inventor-fase)) | `ctype: usize`: 0 gleich, 1 zwei Abstände (`distance2`), 2 Abstand und Winkel (`angle`) (`dialogs.rs:209-214`, `features.rs:89`). | 3 Buttons: `Gleicher Abstand`, `Zwei Abstände`, `Abstand und Winkel`. |
| **5. Richtung umkehren (Flip)** | Richtungsumkehr bei ungleichen Maßen: „(Optional) Wenn Sie die Methode Zwei Abstände zum Definieren der Fase wählen, klicken Sie auf Umkehren, um die Richtung der Fasenabstände umzukehren.“ ([Beleg: Fase](#beleg-inventor-fase)) | `flip: bool` im Dialog (`dialogs.rs:214`), `flip?: bool (which face is first: by default the one facing up most)` (`features.rs:89`). | Richtungsumkehr-Button zum Vertauschen von Referenzfläche 1 und 2. |
| **6. Kantenketten & Mehrfachauswahl** | Tangentiale Kantenverfolgung: „Alle tangential verbundenen Kanten. Schließt alle tangentialen Kanten in die Fase ein.“ ([Beleg: Fase](#beleg-inventor-fase)) | `tangent_chain?: bool (default true: each picked edge's tangent chain is cut with it; false: exactly the picked edges)` (`features.rs:89`), Mehrfachauswahl `SelInput::new("Edges", EDGES \| FACES, true)` (`dialogs.rs:920`). | Checkbox "Tangentiale Kette" standardmäßig aktiv; Mehrfachkanten wählbar. |
| **7. Partielle Fase** | Partielle Fasen mit Anfangs- und Endpunkten: „Erstellen Sie eine partielle Fase, indem Sie die Position der Anfangs- und Endscheitelpunkte entlang einer vorhandenen Modellkante festlegen.“ ([Beleg: Fase](#beleg-inventor-fase)) | Keine partielle Fase im Kernel (nur volle Kantenlängen, `features.rs:89`). | Für v0.1: Volle Kantenlängen; partielle Fasen für Roadmap v0.2 vormerken. |
| **8. Eckenausführung** | Eckenausführung vs. Gehrung: „Eckenausführung . Verbindet die Fase an einem flachen Schnitt.“ ([Beleg: Fase](#beleg-inventor-fase)) | Kernel verschnittet Ecken automatisch (`features.rs:89`). | Standardmäßig flacher Gehrungsschnitt an 3-Kanten-Ecken. |
| **9. Tastenkürzel** | Alias `CH` in Inventor ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)). | **Kein Kürzel** in SolidCraft (`features.rs:89`). | Tastenkürzel `C` (im 3D-Modus) oder Alias `CH` zuweisen. |
| **10. Bestätigen / Abbrechen** | `OK`, `Enter`, `Esc`: „Klicken Sie auf OK.“ ([Beleg: Fase](#beleg-inventor-fase)) | `Enter` / `Esc` (`dialogs.rs:4023`), Apply (`dialogs.rs:3952`). | `OK` (Enter), `Anwenden` (Shift+Enter), `Abbrechen` (Esc). |
| **11. Bearbeiten über Browser** | Rechtsklick > Element bearbeiten ([Beleg: Fase](#beleg-inventor-fase)). | `ui.editFeature` (`dialogs.rs:6658`). | Doppelklick auf Fase im Modellbaum öffnet Fasen-Dialog. |

---

### 2.6 Muster / Anordnung (`solid.pattern.rectangular`, `solid.pattern.circular`)

Vervielfältigung von Features, Körpern oder Komponenten entlang linearer Richtungen oder um eine Drehachse.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Zu ordnende Objekte auswählen: „Wählen Sie im Grafikfenster oder im Browser mindestens ein Element oder einen Körper für die Anordnung aus.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `vec![SelInput::new("Objects", BODIES, true), SelInput::new("Direction", AXES \| EDGES, false), SelInput::new("Direction 2", AXES \| EDGES, false)]` (`dialogs.rs:1016-1019`), Kreismuster: `vec![SelInput::new("Objects", BODIES, true), SelInput::new("Axis", AXIS_PICKS, false)]` (`dialogs.rs:1023`). | Objekte-Picker ist initial aktiv (Features oder Körper); nach Auswahl springt Fokus auf Richtungs- bzw. Achsen-Picker. |
| **2. Vorbelegung (Defaults)** | Rechteckmuster: Anzahl 2 in Richtung 1; Kreismuster: Anzahl 6 über $360^\circ$ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | Rechteck: `count: "3"`, `spacing: "20 mm"`, `count2: "1"`, `spacing2: "20 mm"` (`dialogs.rs:1014`). Kreis: `count: "6"`, `angle: "360 deg"` (`dialogs.rs:1022`). | Rechteckmuster: 3 Exemplare à $20\,\text{mm}$ in Richtung 1, 1 Exemplar in Richtung 2. Kreismuster: 6 Exemplare über $360^\circ$. |
| **3. Vorschau** | 3D-Vorschau aller Exemplare mit grünen/orangen Markierungen ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | Pfeile und Vorschauinstanzen (`pattern_arrow_tests.rs`). | 3D-Vorschau aller Instanzen mit Richtungsachsen im Viewport. |
| **4. Richtung umkehren / Ausrichtung** | Richtungsumkehr und Mittelebene: „Pfad. Wählt die Richtung aus, in der die Exemplare hinzugefügt werden.“ / „Umkehren. Kehrt die Richtung der Exemplare um.“ / „Mittelebene. Erstellt eine Anordnung, bei der die Exemplare auf beiden Seiten des Originalelements verteilt werden.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `reversed?, reversed2?: bool (Flip)`, `alignment?, alignment2?: left\|center\|right (default right; counts include the original)` (`features.rs:94, 98`), `pattern_toggle` (`dialogs.rs:3188`). | Flip-Button je Richtung; Zentriert / Symmetrisch (Mittelebene). |
| **5. Abstandsmethoden** | Abstand, Intervall oder Gesamtlänge ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | `spacing` (Intervall) vs. `distance` (Gesamtabstand) (`features.rs:102`). | Umschalter: `Abstand` (Pitch zwischen Instanzen) vs. `Gesamtlänge` (Spanne). |
| **6. Umgrenzung (Boundary Mask)** | Muster innerhalb einer Skizzenumgrenzung mit Versatz ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | Keine Umgrenzungsmaske im SolidCraft-Kern (`features.rs:94, 102`). | Für v0.1: Standardraster; Begrenzungskontur als Roadmap-Punkt. |
| **7. Berechnungsmethode** | Optimiert, Identisch, Anpassen ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | Geometrische Feature-Recomputation bzw. Körperduplikation (`features.rs:94, 98`). | Standardmäßig optimierte Geometriekopie. |
| **8. Unterdrücken einzelner Instanzen** | Einzelne Exemplare unterdrückbar ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | `pattern_objects` / `pattern_features` (`dialogs.rs:6057-6065`). | Klick auf Exemplarmarker im Ansichtsfenster unterdrückt einzelne Instanzen. |
| **9. Tastenkürzel** | `RP` (Rechteckige Anordnung), `CP` (Runde Anordnung) ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)). | **Keine Kürzel** in SolidCraft (`features.rs:91-98`). | Kürzel `RP` (Rectangular Pattern) und `CP` (Circular Pattern) anbieten. |
| **10. Bestätigen / Abbrechen** | `OK`, `Enter`, `Esc`: „Klicken Sie auf OK.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `Enter` / `Esc` (`dialogs.rs:4023`), Apply (`dialogs.rs:3952`). | `OK` (Enter), `Anwenden` (Shift+Enter), `Abbrechen` (Esc). |
| **11. Bearbeiten über Browser** | Rechtsklick > Element bearbeiten ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | `ui.editFeature` (`dialogs.rs:6658`). | Doppelklick im Modellbaum öffnet Muster-Dialog. |

---

### 2.7 Spiegeln (`solid.mirror`)

Erzeugung spiegelbildlicher Geometrie an einer planaren Spiegelebene.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **1. Initialer Eingabefokus** | Zu spiegelnde Elemente oder Körper wählen: „Wählen Sie im Grafikfenster oder im Browser die Elemente aus, die Sie spiegeln möchten.“ Danach: „Klicken Sie im Dialogfeld Spiegeln auf Spiegelebene, und wählen Sie dann eine Arbeitsebene oder eine planare Fläche als Spiegelebene aus.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `vec![SelInput::new("Objects", BODIES, true), SelInput::new("Mirror Plane", PLANES \| PLANAR_FACES, false)]` (`crates/ui-egui/src/dialogs.rs:929`). Objects hat initialen Fokus, Spiegelebene den zweiten. | Objekte-Picker ist initial aktiv (Features oder Körper); nach Auswahl springt Fokus automatisch auf Spiegelebene. |
| **2. Vorbelegung (Defaults)** | Einzelne Elemente spiegeln (oder Körper spiegeln); Spiegelebene unbesetzt ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | `Kind::Mirror` (`dialogs.rs:929`), `combine: false` (`features.rs:103`, `dialogs.rs:4274`). | Körper/Feature-Spiegelung; Checkbox "Mit Original vereinigen" (`combine`). |
| **3. Vorschau** | 3D-Vorschau der gespiegelten Geometrie auf Gegenseite der Ebene ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | FeaturePreview im Ansichtsfenster (`dialogs.rs:33, 929`). | Live-Ghosting der gespiegelten Geometrie im Ansichtsfenster. |
| **4. Spiegelebene** | Planare Fläche oder Arbeitsebene: „Als Spiegelebene verwenden Sie eine Arbeitsebene oder eine vorhandene planare Fläche.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `plane: XY\|XZ\|YZ\|construction plane name or id\|{origin, normal}\|{origin, x_dir, y_dir}` (`features.rs:103`), `PLANES \| PLANAR_FACES` (`dialogs.rs:929`). | Planare Flächen, Ursprungsebenen (XY, XZ, YZ) und Arbeitsebenen. |
| **5. Operation (Neuer Körper, Vereinigung, Original entfernen)** | Vereinigung, Neuer Volumenkörper, Original entfernen: „Vereinigung . Verbindet das Element mit dem ausgewählten Körper.“ / „Neuer Volumenkörper . Erstellt einen neuen Körper in einem Bauteil mit mehreren Körpern.“ / „Original entfernen. Entfernt den Originalkörper. Nur die gespiegelte Version bleibt in der Bauteildatei erhalten.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `features: [names] \| bodies: [names] (combine?: join with the original)` (`features.rs:103`). Kein direktes "Original entfernen" im Kernbefehl. | Radio-Buttons: `Neuer Körper` (New Body), `Mit Original vereinigen` (Join), `Original entfernen` (Transformiert linkes in rechtes Teil!). |
| **6. Teilnehmer entfernen / Unterdrücken** | Untergeordnete Teilnehmer unterdrückbar: „Tipp: Zum Entfernen von Teilnehmern (Elementen) aus einer Spiegelung erweitern Sie das Element im Browser, klicken mit der rechten Maustaste auf ein untergeordnetes Element, und wählen Sie Unterdrücken.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | Features als Liste übergeben (`features: [names]`, `features.rs:103`). | Untergeordnete Feature-Teilnehmer im Baum unterdrückbar machen. |
| **7. Berechnungsmethoden** | Optimiert, Identisch, Anpassen ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | Exakte Geometrieerzeugung über Kernel (`features.rs:103`). | Kernel löst Geometrie exakt auf. |
| **8. Fehlermeldungen / Sonderfälle** | Spiegelebene darf Körper schneiden; Fehler bei nicht-planaren Flächen ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | Verweigerung ohne planare Ebene; Berührungsregeln bei `combine` (`features.rs:103`). | Fehlermeldung "Bitte eine planare Fläche oder Arbeitsebene wählen", falls Klick auf Freiformfläche erfolgt. |
| **9. Tastenkürzel** | `MI` (Spiegeln) in Inventor ([Beleg: Tastaturkurzbefehle](#beleg-inventor-tastaturkurzbefehle)). | **Kein Kürzel** in SolidCraft (`features.rs:103`). | Tastenkürzel `MI` (Mirror) zuweisen. |
| **10. Bestätigen / Abbrechen** | `OK`, `Enter`, `Esc`: „Klicken Sie auf OK.“ ([Beleg: Anordnungen](#beleg-inventor-anordnungen)) | `Enter` / `Esc` (`dialogs.rs:4023`), Apply (`dialogs.rs:3952`). | `OK` (Enter), `Anwenden` (Shift+Enter), `Abbrechen` (Esc). |
| **11. Bearbeiten über Browser** | Rechtsklick > Element bearbeiten ([Beleg: Anordnungen](#beleg-inventor-anordnungen)). | `ui.editFeature` (`dialogs.rs:6658`). | Doppelklick auf Spiegelelement im Baum; Spiegelebene und Quellkörper werden hervorgehoben. |

---

## 3. Die 10 wichtigsten Punkte, die ein Inventor-Nutzer zuerst vermissen würde

Ein erfahrener Autodesk-Inventor-Konstrukteur, der erstmals mit SolidCraft bzw. einem unvollständigen Mechvane-Prototyp arbeitet, stößt auf zehn fundamentale Brüche im Bedienfluss:

1. **Breadcrumb-Navigation in der Eigenschaftengruppe (Direkter Skizzen-Rücksprung):**
   In Inventor klickt der Anwender während der Feature-Definition oben im Breadcrumb auf `Skizze 1`, ändert ein Skizzenmaß und kehrt sofort wieder in den Extrusions-/Drehdialog zurück. In SolidCraft muss der Dialog abgebrochen, die Skizze im Baum gesucht, geöffnet, geändert, beendet und das Feature neu aufgerufen werden.
2. **Direkte Maßeingabe im Grafikfenster bei Live-Vorschau (HUD & Drag-Manipulatoren):**
   In Inventor erscheinen Maßeingabefelder direkt am Modell (Heads-Up Display). Durch Ziehen an den Pfeilen oder Direkttippen wird das Maß geändert, ohne mit der Maus ins Dialogfenster fahren zu müssen.
3. **Erstellung von Bohrungsmittelpunkten direkt auf der Bauteilfläche ohne vorherige Skizze:**
   In Inventor startet der Befehl `Bohrung` (`H`) sofort: Klick auf eine Planarfläche setzt den Bohrungspunkt und blendet zwei Kantenabstände zur Bemaßung ein. In SolidCraft gibt es zwar Einzelbohrungen mit Kantenreferenzen (`crate::hole_refs`), aber keine freie Mehrpunktplatzierung auf einer Fläche ohne vorheriges Zeichnen einer Skizze.
4. **Auswahlfilter-Umschalter bei Rundungen (Kante, Kontur, Element, Volumenkörper):**
   In Inventor schaltet der Rundungsdialog mit einem Klick zwischen *Kante*, *Geschlossene Kontur* (Loop), *Feature-Kanten* und *Alle Kanten des Körpers* um. In SolidCraft müssen Kanten einzeln oder mühsam über Flächen selektiert werden.
5. **Interaktive Eckenausführung bei Rundungen und Fasen (Corner Relief / Setbacks per Scheitelpunkt):**
   In Inventor kann jeder 3-Kanten-Eckpunkt angeklickt und mit einem individuellen Rücksprungmaß (Setback) oder einer Ausklinkung versehen werden. In SolidCraft ist dies nur als globale Kernel-Option (`corner: g2`, `setbacks`) ohne interaktive Scheitelpunktauswahl vorhanden.
6. **Partielle Fase (Teilweise Fase mit variablen Anfangs- und Endpunkten entlang einer Kante):**
   Inventor erlaubt es, Fasen nur über einen Teilabschnitt einer Kante zu ziehen (mit interaktiven Anfangs- und Endkugeln). SolidCraft fast zwingend die gesamte Kante oder Kette an.
7. **Tastenkürzel-Inkonsistenz (insbesondere `R` für Drehung vs. Rechteck, `CH` für Fase):**
   In Inventor ist `R` fest im motorischen Gedächtnis als *Drehung* (`Revolve`) verankert. In SolidCraft ist `R` jedoch für das 2-Punkt-Rechteck in der Skizze belegt, wodurch `solid.revolve` überhaupt kein Tastenkürzel besitzt! Ebenso fehlen `CH` (Fase), `RP` (Rechteckmuster) und `CP` (Kreismuster).
8. **Anordnung innerhalb einer Umgrenzung (Pattern within Boundary / Ausschlussbereich):**
   Inventor kann Muster auf die Fläche einer beliebigen Skizzenumgrenzung beschränken (z. B. Lochblech mit Randabstand). SolidCraft unterstützt ausschließlich feste rechteckige Spalten/Reihen oder Kurvenpfade.
9. **Option „Original entfernen“ beim Spiegeln (Remove Original Body):**
   In Inventor kann beim Spiegeln eines Volumenkörpers das Original direkt verworfen werden, um aus einem linken Bauteil in einem Schritt das symmetrische rechte Bauteil zu erzeugen. In SolidCraft muss der Originalkörper nachträglich manuell gelöscht werden (`solid.remove`).
10. **Berechnungsmethoden bei Mustern (Optimiert vs. Identisch vs. Anpassen):**
    Inventor unterscheidet zwischen *Optimiert* (schnelles Flächenkopieren) und *Anpassen* (Recompute jedes Exemplars, sodass z. B. Bohrungen mit "Bis Fläche" an geneigten Gegenwänden ihre Tiefe für jedes Exemplar individuell anpassen). SolidCraft dupliziert Geometrie statisch.

---

## 4. Quellenbelege und wörtliche Zitate

Die folgenden Belege stammen aus den offiziellen Autodesk-Dokumentationen (Autodesk Help System, Inventor 2025/2026) und dem Quellcode von SolidCraft (`crates/ui-egui/src` und `crates/engine/src/cmd`). Alle externen Links wurden mit `tools/check_sources.py` automatisiert auf HTTP 200 und wortwörtliche Übereinstimmung geprüft.

### Beleg: Extrusion
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B0CFA8E7-D3F5-48A9-BE6F-C8DF668301BD.htm
* **Wörtliches Zitat:** „Ein Profil - Enthält die Skizze nur ein geschlossenes Profil, wird dieses automatisch ausgewählt.“
* **Wörtliches Zitat:** „Vorgabemäßig erstellen Sie mit der Option Extrusion einen Volumenkörper aus einem offenen oder geschlossenen Profil.“
* **Wörtliches Zitat:** „Von - Als Vorgabe beginnt die Extrusion auf der Skizzierebene.“
* **Wörtliches Zitat:** „Der Befehl zeigt eine Vorschau der Richtung der Booleschen Operation an.“
* **Wörtliches Zitat:** „Richtung: Vorgabe - Extrudiert nur in eine Richtung.“
* **Wörtliches Zitat:** „Umgekehrt - Extrudiert in die entgegengesetzte Richtung der Einstellung Richtung.“
* **Wörtliches Zitat:** „Symmetrisch - Extrudiert in die entgegengesetzten Richtungen von der Skizzierebene und verwendet dabei die Hälfte des angegebenen Werts für Abstand A in jede Richtung.“
* **Wörtliches Zitat:** „Asymmetrisch - Extrudiert in die entgegengesetzten Richtungen von der Skizzierebene und verwendet dabei zwei Werte: Abstand A und Abstand B.“
* **Wörtliches Zitat:** „Durch alle - Extrudiert das Profil durch alle Elemente und Skizzen hindurch in der angegebenen Richtung.“
* **Wörtliches Zitat:** „Zur Nächsten - (Nicht verfügbar für Basiselemente oder Baugruppenextrusionen.) Wählt die nächstmögliche Fläche oder Ebene für die Ausführung der Extrusion in der angegebenen Richtung aus“
* **Wörtliches Zitat:** „Vereinigung - Fügt das durch das extrudierte Element erstellte Volumen einem anderen Element oder Körper hinzu.“
* **Wörtliches Zitat:** „Differenz - Entfernt das durch das extrudierte Element erstellte Volumen von einem anderen Element oder Körper.“
* **Wörtliches Zitat:** „Neuer Volumenkörper - Erstellt einen neuen Volumenkörper.“
* **Wörtliches Zitat:** „Sie können einen Auswahlrahmen verwenden, um schnell mehrere geschlossene Profile in der Skizze auszuwählen.“
* **Wörtliches Zitat:** „Flächendehnung bis Endelement - Wird automatisch aktiviert, wenn die Auswahl Von das extrudierte Profil nicht schneidet.“
* **Wörtliches Zitat:** „Oben in der Eigenschaftsgruppe wird der Breadcrumb angezeigt.“
* **Wörtliches Zitat:** „Klicken Sie im Grafikfenster oder Browser mit der rechten Maustaste auf das Element, und wählen Sie Element bearbeiten.“

### Beleg: Drehung
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-401BABD2-8D5B-4300-BA8D-70037445044F.htm
* **Wörtliches Zitat:** „Liegt in der Skizze nur eine sichtbare Skizze mit nur einem Profil und einer Achse vor, wird diese automatisch als Eingabegeometrieprofil ausgewählt, und eine Vorschau wird angezeigt.“
* **Wörtliches Zitat:** „Volumenkörper (Vorgabe) - Erstellt aus einem offenen oder geschlossenen Profil einen neuen Volumenkörper.“
* **Wörtliches Zitat:** „Wichtig: Bei der Elementvorschau können sichtbare Skizzenbemaßungen bearbeitet werden, ohne die Skizzierumgebung aufzurufen.“
* **Wörtliches Zitat:** „Vollständig: Dreht das Profil um ganze 360 Grad.“
* **Wörtliches Zitat:** „Achse - Klicken Sie mit der rechten Maustaste in die Anzeige, und wählen Sie Weiter aus, oder klicken Sie auf die Eigenschaftengruppen-Auswahl, und wählen Sie dann eine Achse aus der aktiven Skizze aus.“
* **Wörtliches Zitat:** „Vereinigung: Fügt das durch das Drehelement erstellte Volumen einem anderen Element oder Körper hinzu.“
* **Wörtliches Zitat:** „Klicken Sie auf OK oder (Neues Element erstellen), um die Definition von Drehelementen fortzusetzen.“
* **Wörtliches Zitat:** „Um die Elementskizze zu bearbeiten, klicken Sie im Breadcrumb-Text der Eigenschaftengruppe auf die Skizzennummer und beginnen mit der Bearbeitung der Skizze.“

### Beleg: Bohrung
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Geben Sie die Positionen an. Es ist keine vorhandene Skizze erforderlich. Zu den gültigen Eingaben für die Bohrungspositionen zählen Fläche Skizzierpunkt (Ende oder Mitte) sowie Arbeitspunkt.“
* **Wörtliches Zitat:** „Wenn die Option Erstellung von Mittelpunkt zulassen AKTIVIERT ist (Vorgabe), können Sie Mittelpunkte nach dem Zufallsprinzip auf einer Bauteilfläche hinzufügen.“
* **Wörtliches Zitat:** „Klicken Sie auf eine Referenzkante, um die Bemaßungen zu platzieren. Bemaßungen für die lineare Platzierung können ausgewählt, bearbeitet oder gelöscht werden, während der Befehl Bohrung aktiv ist.“
* **Wörtliches Zitat:** „Vorschausteuerelemente stehen während der Bearbeitung von Elementen und Skizzen zur Verfügung.“
* **Wörtliches Zitat:** „Bohrungsspitze Flach: Erstellt einen flachen Bohrungspunkt. Winkel: Erstellt Bohrungsspitzen.“
* **Wörtliches Zitat:** „Doppelklicken Sie auf den Elementknoten. Klicken Sie mit der rechten Maustaste auf den Elementknoten, und wählen Sie Element bearbeiten aus.“
* **Wörtliches Zitat:** „Benennen Sie aktive Bohrungs- und Skizzenknoten in der Gruppe Eigenschaften um, indem Sie auf den Breadcrumb klicken.“

### Beleg: Rundung
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-590A8760-FFBB-41C8-8169-6B7002207884.htm
* **Wörtliches Zitat:** „In der Gruppe Eigenschaften ist Kantensätze mit konstantem Radius sofort aktiv. Sie können mit der Auswahl von Modellkanten beginnen.“
* **Wörtliches Zitat:** „Fortlaufende Kanten. Legt die Voreinstellung zur Kantenauswahl für Kantenrundungen fest. Aktivieren Sie das Kontrollkästchen, um beim Auswählen einer zu rundenden Kante automatisch alle tangentialen Kanten auszuwählen.“
* **Wörtliches Zitat:** „Wendet tangentiale (G1) Abrundungen auf benachbarte Flächen an.“
* **Wörtliches Zitat:** „Wendet stetige (G2) Abrundungen mit Krümmungsstetigkeit auf benachbarte Flächen an.“
* **Wörtliches Zitat:** „Klicken Sie auf OK, um den Vorgang abzuschließen und die Gruppe Eigenschaften zu schließen. Klicken Sie auf Anwenden, um mit dem Anwenden von Abrundungen und Rundungen fortzufahren.“
* **Wörtliches Zitat:** „Klicken Sie im Browser mit der rechten Maustaste auf das Element, und wählen Sie Element bearbeiten. Doppelklicken Sie im Browser auf das Element.“
* **Wörtliches Zitat:** „Gelegentlich wird eine Meldung angezeigt, die besagt, dass die ausgewählten Kanten nicht verschmolzen werden können“

### Beleg: Fase
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-D40DA0A5-0547-41FE-A1BC-0B42AE1CC8E4.htm
* **Wörtliches Zitat:** „Abstand. Definiert eine Fase mit demselben Versatzabstand von der Kante an beiden Flächen.“
* **Wörtliches Zitat:** „Abstand und Winkel. Definiert eine Fase mittels des Versatzes von einer Kante und eines Winkels von einer Fläche zum Versatz.“
* **Wörtliches Zitat:** „Zwei Abstände. Erstellt eine Fase an einer oder mehreren Kanten mit einem für jede Fläche festgelegten Abstand.“
* **Wörtliches Zitat:** „(Optional) Wenn Sie die Methode Zwei Abstände zum Definieren der Fase wählen, klicken Sie auf Umkehren, um die Richtung der Fasenabstände umzukehren.“
* **Wörtliches Zitat:** „Alle tangential verbundenen Kanten. Schließt alle tangentialen Kanten in die Fase ein.“
* **Wörtliches Zitat:** „Eckenausführung . Verbindet die Fase an einem flachen Schnitt.“
* **Wörtliches Zitat:** „Erstellen Sie eine partielle Fase, indem Sie die Position der Anfangs- und Endscheitelpunkte entlang einer vorhandenen Modellkante festlegen.“
* **Wörtliches Zitat:** „Klicken Sie im Grafikfenster oder Browser mit der rechten Maustaste auf das Element, und wählen Sie Bearbeiten aus.“

### Beleg: Anordnungen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-9B3D1B72-340A-4F3E-9AD1-80E6DDD91ED2.htm
* **Wörtliches Zitat:** „Das Werkzeug Rechteckige Anordnung kopiert Elemente oder Körper und ordnet die Ergebnisse ausgehend vom Originalelement in einer rechteckigen Anordnung entlang eines Pfads oder bidirektional an.“
* **Wörtliches Zitat:** „Mit dem Befehl Runde Anordnung können Sie Exemplare ausgewählter Elemente oder Körpers in einer bogenförmigen oder kreisförmigen Anordnung duplizieren.“
* **Wörtliches Zitat:** „Mit dem Befehl Spiegeln können Sie eine spiegelverkehrte Kopie eines oder mehrerer Elemente, des gesamten Volumenkörpers oder eines neuen Volumenkörpers in gleichmäßigen Abständen auf einer Ebene erstellen.“
* **Wörtliches Zitat:** „Einzelne Elemente anordnen. Ordnet einzelne Volumenelemente, Arbeitselemente und Flächenelemente an.“
* **Wörtliches Zitat:** „Volumenkörper anordnen. Ordnet einen Volumenkörper einschließlich der Elemente an, die nicht einzeln angeordnet werden können.“
* **Wörtliches Zitat:** „Umkehren. Kehrt die Richtung der Exemplare um.“
* **Wörtliches Zitat:** „Mittelebene. Erstellt eine Anordnung, bei der die Exemplare auf beiden Seiten des Originalelements verteilt werden.“
* **Wörtliches Zitat:** „Als Spiegelebene verwenden Sie eine Arbeitsebene oder eine vorhandene planare Fläche.“
* **Wörtliches Zitat:** „Original entfernen. Entfernt den Originalkörper. Nur die gespiegelte Version bleibt in der Bauteildatei erhalten.“
* **Wörtliches Zitat:** „Klicken Sie auf Weitere Optionen , um den Startpunkt der Richtung, die Berechnungsmethode und die Ausrichtung der angeordneten Elemente festzulegen:“
* **Wörtliches Zitat:** „Klicken Sie auf Weitere Optionen , um die Berechnungsmethode für die gespiegelten Elemente festzulegen:“

### Beleg: Eigenschaftsgruppen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-3E5505B9-9F60-43A0-BF32-97D183B91A70.htm
* **Wörtliches Zitat:** „Eigenschaftsgruppen bieten kontextabhängigen Zugriff auf Parameter zum Erstellen und Bearbeiten von Elementen.“
* **Wörtliches Zitat:** „Arbeitsablauf - Der Arbeitsablauf in der Gruppe Eigenschaften verläuft von oben nach unten.“
* **Wörtliches Zitat:** „Breadcrumb - Schnelles Wechseln zwischen der Bearbeitung des Elements und der zugehörigen Skizze.“
* **Wörtliches Zitat:** „EINGABETASTE - Wertbearbeitungen anwenden“
* **Wörtliches Zitat:** „STRG + EINGABETASTE - Elementdefinition beenden, Element erstellen und Eigenschaftengruppe schließen“
* **Wörtliches Zitat:** „TABULATORTASTE - Schrittweise zum nächsten Feld wechseln“

### Beleg: Tastaturkurzbefehle
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „Extrusion Aktiviert den Befehl Extrusion.“
* **Wörtliches Zitat:** „Drehung Aktiviert den Befehl Drehung.“
* **Wörtliches Zitat:** „Bohrung Aktiviert den Befehl Bohrung.“
* **Wörtliches Zitat:** „Erstellt eine Rundung.“

### Beleg: Vordefinierte Kurzbefehle
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „Beendet einen Befehl“
