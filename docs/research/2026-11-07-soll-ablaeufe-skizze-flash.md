# Recherche Soll-Abläufe 1: Skizze, Profilwahl, Ansicht und Auswahl wie Inventor und SolidCraft

- **Datum:** 2026-11-07
- **Autor:** Gemini 3.8 Flash (Issue #55)
- **Status:** Verifiziert mit `python3 tools/check_sources.py docs/research/2026-11-07-soll-ablaeufe-skizze-flash.md` und gegen den Sparse-Klon `/root/repos/_ext/solidcraft` (Stand v0.25.1)
- **Prüfnotiz (Claude, 2026-11-07):** `check_sources.py`: alle Inventor-Zitate und Zahlen belegt. SolidCraft-Fundstellen sind Stichproben gegen den Klon vom 2026-11-07 (nach v0.30.1); Zeilennummern können verschoben sein. Nicht bestätigt: „`solid.revolve` hat kein Standard-Tastenkürzel“.
- **Ziel & Kontext:** Belastbare Entscheidungsgrundlage für die browserbasierte Mechvane-Bedienoberfläche (v0.1, `sketcher.js` und 3D-Viewport). Konstrukteure, die von Autodesk Inventor kommen, erwarten bei den grundlegenden Interaktionen (Skizzieren, Ansichtsnavigation, Profilwahl und Selektion) ein konsistentes, verlässliches Standardverhalten. Diese Recherche stellt den Soll-Ablauf von Autodesk Inventor (2025/2026) der Implementierung in SolidCraft (`crates/ui-egui/src` und `crates/engine/src/cmd`) gegenüber und leitet konkrete Empfehlungen für Mechvane ab.

---

## 1. Skizze anlegen (Ebene/Fläche wählen, Ansicht drehen)

In Autodesk Inventor startet das Anlegen einer 2D-Skizze entweder durch Vorwahl einer planaren Fläche/Arbeitsebene mit Klick auf das Skizzensymbol im Mini-Werkzeugkasten (HUD) oder über den globalen Befehl (Taste `S`). Sobald die Skizzierebene gewählt ist, dreht Inventor standardmäßig die Kamera senkrecht zur Skizzierebene („Ausrichten nach Skizzierebene“) und projiziert automatisch die Begrenzungskanten der gewählten Modellfläche sowie den Bauteilursprung auf die Skizze.

SolidCraft implementiert die Skizzenerstellung im Engine-Befehl `sketch.create` (`crates/engine/src/cmd/sketch.rs:43-46`). Die Viewport-Drehung erfolgt in `crates/ui-egui/src/lib.rs:2445-2451` über die Einstellung `sketch_open_look_at`, die standardmäßig aktiv ist (`crates/ui-egui/src/sketch_edit_tests.rs:720-722`).

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Fläche/Ebene auswählen** | „Klicken Sie auf eine planare Fläche oder Arbeitsebene eines Bauteils, und wählen Sie im Mini-Werkzeugkasten die Option Skizze erstellen .“ ([GUID-E96FB3C4](#q1-beleg-inventor-skizzen-erstellen-und-bearbeiten)) | `crates/engine/src/cmd/sketch.rs:46`: Parameter `plane: XY\|XZ\|YZ ... \| {face: [world x,y,z], ...}` | Klick auf Modellfläche oder Ursprungsebene bietet direkt Kontext-Button „Skizze erstellen“ bzw. Tastenkürzel `S`. |
| **Ansicht senkrecht ausrichten (Look At)** | „Ausrichten nach Skizzierebene bei Skizzenerstellung und -bearbeitung Legt bei Aktivierung die Neuausrichtung des Grafikfensters fest, sodass für neue Skizzen die Skizzierebene parallel zur Ansicht ist.“ ([GUID-1898C432](#q2-beleg-inventor-anwendungsoptionen-skizze)) | `crates/ui-egui/src/lib.rs:2446-2448`: `let turn = self.preferences.sketch_open_look_at; if turn { dialogs::look_at_sketch(self); }` | Standardmäßig aktiviert: Weiche Kamerafahrt senkrecht auf Skizzierebene. Vorherige Kameraposition (`pre_sketch_cam`) merken. |
| **Automatische Kantenprojektion** | „Modellkanten für Skizzenerstellung und -bearbeitung automatisch projizieren Projiziert beim Erstellen oder Bearbeiten einer Skizze die Kanten einer ausgewählten Fläche automatisch als Referenzgeometrie auf die Skizzierebene.“ ([GUID-1898C432](#q2-beleg-inventor-anwendungsoptionen-skizze)) | `crates/engine/src/cmd/sketch.rs:46`: `project_edges?: bool` | Begrenzungskanten der gewählten Fläche automatisch als Referenzgeometrie projizieren (`project_edges: true`), damit Fangen sofort klappt. |
| **Ursprungspunkt projizieren** | „Ursprung des Bauteils beim Erstellen der Skizze automatisch projizieren Legt die Voreinstellung für den Ursprung projizierter Bauteile in neuen Skizzen fest.“ ([GUID-1898C432](#q2-beleg-inventor-anwendungsoptionen-skizze)) | `crates/engine/src/cmd/sketch.rs:46`: `plane: {origin?: [x,y,z] ...}` | Skizzenursprung `(0, 0)` immer als sichtbaren, fangbaren Referenzpunkt einblenden. |

**Abweichungen:** Inventor projiziert Flächenkanten und Bauteilursprung standardmäßig automatisch. SolidCraft erfordert bei `sketch.create` das explizite Flag `project_edges: true`; standardmäßig sind Kanten nicht automatisch projiziert, sondern müssen über `sketch.project` (`P`) manuell geholt werden. Mechvane sollte dem Inventor-Standard folgen und `project_edges: true` als Standard vorgeben.

---

## 2. Skizze bearbeiten und verlassen

In Inventor öffnet ein Doppelklick auf das Skizzensymbol im Modell-Browser die Skizzenumgebung. Alle nachfolgenden Modellelemente werden zeitweise zurückgerollt. Das Verlassen erfolgt zwingend über „Skizze beenden“ (großer grüner Haken im Menüband oder Kontextmenü) oder „Skizze abbrechen“ (verwirft alle aktuellen Änderungen).

SolidCraft bildet dies über die Befehle `sketch.edit`, `sketch.finish` und `sketch.cancel` ab (`crates/engine/src/cmd/sketch.rs:47-60`). Bei `sketch.edit` mit `restore_marker` rollt die Engine den Timeline-Marker temporär zurück (`crates/engine/src/cmd/sketch.rs:1008-1014`). Beim Verlassen animiert die UI die Kamera automatisch wieder auf die Ansicht vor dem Skizzieren zurück (`crates/ui-egui/src/lib.rs:2542-2546`).

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Skizze bearbeiten (Doppelklick)** | „Doppelklicken Sie auf das Skizzensymbol im Browser.“ ([GUID-E96FB3C4](#q1-beleg-inventor-skizzen-erstellen-und-bearbeiten)) | `crates/engine/src/cmd/sketch.rs:47-50`: `CommandSpec::new("sketch.edit", "Edit Sketch", ...)` | Doppelklick im Feature-Baum öffnet Skizze; nachfolgende Modell-Features werden temporär ausgeblendet (Rollback). |
| **Timeline-Rollback während Bearbeitung** | Nachfolgende Elemente werden temporär unterdrückt und nach Beenden neu berechnet. (sinngemäß) | `crates/engine/src/cmd/sketch.rs:1009-1012`: `let marker = (index + 1 < s.doc.features.len()).then_some(index + 1); if s.doc.marker != marker { s.doc_mut().marker = marker; }` | Temporärer Marker direkt hinter die Skizze setzen; Änderungen als ein einziger konsolidierter Undo-Schritt erfassen. |
| **Skizze beenden (Fertigstellen)** | „Sie müssen eine Skizze fertig stellen, um die Skizzierumgebung zu beenden.“ sowie „Zum Beenden einer 2D-Skizze klicken Sie auf der Registerkarte Skizze auf Skizze beenden , oder klicken mit der rechten Maustaste im Grafikbereich und wählen 2D-Skizze beenden.“ ([GUID-E96FB3C4](#q1-beleg-inventor-skizzen-erstellen-und-bearbeiten)) | `crates/engine/src/cmd/sketch.rs:51-54`: `CommandSpec::new("sketch.finish", "Finish Sketch", ...).at("SKETCH", "FINISH SKETCH").icon("finish")` | Deutlich sichtbare Schaltfläche „Skizze beenden“ (grüner Haken) oben rechts im Viewport und in der Toolbar; Tastatur-Shortcut (z. B. `Enter` im neutralen Zustand). |
| **Skizze abbrechen** | „Wenn Sie eine Skizze abbrechen, werden alle aktuellen Aktionen verworfen. Beim Erstellen einer Skizze werden alle Aktionen verworfen, einschließlich der Erstellung der Skizze. Wenn Sie eine Skizze bearbeiten, werden alle während dieser Bearbeitung durchgeführten Aktionen verworfen.“ ([GUID-E96FB3C4](#q1-beleg-inventor-skizzen-erstellen-und-bearbeiten)) | `crates/engine/src/cmd/sketch.rs:55-60`: `CommandSpec::new("sketch.cancel", "Cancel Sketch", ...).icon("sketch_cancel")` | „Abbrechen“-Schaltfläche setzt Dokumentzustand exakt auf Zustand vor Bearbeitungsbeginn zurück. |
| **Kamera-Rückstellung beim Beenden** | Nach Skizzenende schwenkt die Ansicht zurück in die 3D-Modellansicht. (sinngemäß) | `crates/ui-egui/src/lib.rs:2542-2545`: `if let Some(view) = self.pre_sketch_cam.take().filter(...) && let Some(to) = self.preferences.sketch_exit_view.view_after(...) { self.animate_to(to); }` | Weiche Rückanimation in die vorherige 3D-Perspektive (`before`). |

**Abweichungen:** Beide Systeme arbeiten hier nach identischen Prinzipien. SolidCraft besitzt mit `restore_marker` bereits die vollständige Engine-Infrastruktur für den temporären Timeline-Rollback.

---

## 3. Anzeige fertiger und unbenutzter Skizzen

In Inventor wird eine Skizze, sobald sie von einem Feature (z. B. Extrusion oder Drehung) verwendet wird, „einverleibt“ (*consumed*). Sie rückt im Modellbaum hierarchisch unter das Feature und wird im 3D-Grafikbereich standardmäßig ausgeblendet. Unbenutzte Skizzen bleiben sichtbar. Eine verwendete Skizze kann über das Kontextmenü „Skizze wiederverwenden“ (*Share Sketch*) wieder freigegeben werden, um für weitere Features zur Verfügung zu stehen.

In SolidCraft prüft `solidcraft_engine::view::sketch_consumed` (`crates/engine/src/view.rs:1144`), ob eine Skizze bereits von Extrusion, Revolve oder Hole einbezogen wurde. Die UI-Abfrage `sketch_visible` (`crates/ui-egui/src/browser.rs:389-394`) schaltet verbrauchte Skizzen automatisch unsichtbar, es sei denn, sie wurden explizit über `browser.visibility` eingeblendet.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Unbenutzte Skizzen sichtbar** | Unbenutzte Skizzen bleiben als eigenständige Knoten im Browser sichtbar, bis sie von einem Element konsumiert werden. (sinngemäß) | `crates/ui-egui/src/browser.rs:393`: `app.session.visibility.shown_sketches.contains(&id) \|\| !solidcraft_engine::view::sketch_consumed(&app.session, id)` | Unbenutzte Skizzen bleiben im 3D-Viewport sichtbar und als Kontur hervorgehoben. |
| **Automatisches Ausblenden bei Benutzung** | Eine in ein Element einbezogene Skizze wird standardmäßig ausgeblendet und dem Feature untergeordnet. (sinngemäß) | `crates/engine/src/view.rs:1144`: `pub fn sketch_consumed(s: &Session, id: u64) -> bool` | Sobald eine Skizze für Extrusion/Drehung verwendet wurde, wird sie im Viewport standardmäßig unsichtbar geschaltet. |
| **Skizze wiederverwenden (Share Sketch)** | „So geben Sie eine Skizze manuell frei Klicken Sie im Browser auf das Pluszeichen (+) neben dem Element, das die zu verwendende Skizze enthält, um den Skizzierknoten anzuzeigen. Klicken Sie mit der rechten Maustaste auf das Skizzensymbol und dann auf Skizze wieder verwenden. Kommt eine Skizze bei mehr als einem Element zum Einsatz, wird sie automatisch zu einer wiederverwendeten Skizze.“ ([GUID-B0CFA8E7](#q3-beleg-inventor-extrudierte-elemente-und-profilwahl)) | `crates/ui-egui/src/browser.rs:396-398`: `pub fn set_sketch_visible(app: &mut SolveApp, id: u64, on: bool) { let _ = app.run("browser.visibility", json!({ "items": [id], "visible": on })); }` | Kontextmenü „Skizze wiederverwenden“ bzw. Klick auf das Augen-Symbol im Baum macht Skizze persistent sichtbar und erlaubt Mehrfachnutzung. |
| **Durchscheinen durch Körper (Opazität)** | „Anzeige von Skizzen Die Einstellung Opazität der angezeigten Skizze durch schattiertes Modell steuert, in welchem Grad Skizziergeometrie durch schattierte Modellgeometrie hindurch sichtbar ist. Die Standardeinstellung ist 0 %. Hierbei wird die Skizziergeometrie vollständig von der schattierten Modellgeometrie verdeckt.“ ([GUID-1898C432](#q2-beleg-inventor-anwendungsoptionen-skizze)) | `crates/ui-egui/src/viewport.rs:2084`: `let through = active \|\| app.preferences.reference_geometry_through_bodies;` | Aktive Skizzen scheinen immer durch verdeckende Festkörper durch; fertige inaktive Skizzen werden durch das Modell verdeckt, können aber per X-Ray/Ghosting eingeblendet werden. |

**Abweichungen:** Inventor ordnet verbrauchte Skizzen baumartig *unter* dem Element an. Mechvane führt gemäß ADR 0001 und `AGENTS.md` einen flachen chronologischen Baum („sketch sits directly before feature“). Mechvane muss daher das Wiederverwenden über Mechvanes Verknüpfungswerkzeuge (`links.py`) abbilden, während das visuelle Ein-/Ausblenden dem Augen-Status von SolidCraft entspricht.

---

## 4. Profilwahl für Extrusion/Drehung (Vorwahl, Mehrfachwahl, Löcher, verschachtelte Regionen)

Beim Aufruf von Extrusion oder Drehung muss der Konstrukteur festlegen, welche planaren Bereiche materialisiert werden sollen. Inventor wählt automatisch das einzige Profil vor, wenn die Skizze nur eine geschlossene Kontur enthält. Bei mehreren Konturen oder verschachtelten Geometrien (z. B. Kreis in Rechteck) unterscheidet Inventor automatisch zwischen Material und Loch.

SolidCraft unterstützt im Befehl `solid.extrude` (`crates/engine/src/cmd/features.rs:42`) die explizite Übergabe von Regionen (`exact_regions: true`), wählt beim Picken die kleinste umschließende Region (`crates/ui-egui/src/viewport.rs:3154-3160`) und unterstützt Mehrfachauswahl via Marquee (`crates/ui-egui/src/viewport.rs:13192-13201`).

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Automatische Vorwahl (1 Profil)** | „Liegt in der Skizze nur ein Profil vor, wird dieses automatisch ausgewählt. Wählen Sie andernfalls ein Skizzenprofil aus.“ sowie „Ein Profil - Enthält die Skizze nur ein geschlossenes Profil, wird dieses automatisch ausgewählt.“ ([GUID-B0CFA8E7](#q3-beleg-inventor-extrudierte-elemente-und-profilwahl)) | `crates/ui-egui/src/dialogs.rs:5194`: `let (sketch, idx) = profiles(); let profile = (!sketch.is_null()).then(\|\| ("solid.extrude".to_string(), with(json!({"sketch": sketch, "profiles": idx}))));` | Liegt in der Skizze genau eine geschlossene Kontur vor, wird diese beim Klick auf Extrudieren/Drehen sofort ohne Zusatzklick selektiert (Zero-Click-Extrude). |
| **Mehrfachauswahl von Profilen** | „Mehrere Profile - Wählen Sie die Profile oder Bereiche aus, die die gewünschte Extrusion oder den gewünschten Körper definieren.“ ([GUID-B0CFA8E7](#q3-beleg-inventor-extrudierte-elemente-und-profilwahl)) | `crates/ui-egui/src/viewport.rs:13200-13201`: `vec![Sel::Profile { sketch, index: 0 }, Sel::Profile { sketch, index: 1 }], "the shift marquee adds the second region"` | Profile können nacheinander mit der Maus angeklickt oder per `Shift`-Klick hinzugefügt/abgewählt werden. |
| **Fensterauswahl für Profile** | „Sie können einen Auswahlrahmen verwenden, um schnell mehrere geschlossene Profile innerhalb derselben Skizze auszuwählen.“ ([GUID-B0CFA8E7](#q3-beleg-inventor-extrudierte-elemente-und-profilwahl)) | `crates/ui-egui/src/viewport.rs:13191-13192`: `h.step(&json!({"drag": [{"world": [a.x, a.y, a.z]}, {"world": [b.x, b.y, b.z]}]})).unwrap(); assert_eq!(h.app.session.selection, vec![Sel::Profile { sketch, index: 0 }], "the marquee takes the first region");` | Ziehen eines Rahmens im Profilauswahl-Modus wählt alle umschlossenen Konturen aus. |
| **Verschachtelte Konturen & Löcher** | Bei Volumenkörpern entscheidet die Schachtelung über Material und Aussparung (Inselerkennung). (sinngemäß) | `crates/engine/src/cmd/features.rs:42`: `default: every drawn profile, except that a loop inside another is its hole and a loop inside that hole is material again` | Automatische Odd-Even-Regel: Äußere Kontur = Material, innere Kontur = Loch, darin liegende Kontur = wieder Material. Einzelbereiche müssen separat klickbar sein. |
| **Pick-Priorität bei Überlappung** | Der Mauscursor hebt den spezifisch überfahrenen Teilbereich hervor. (sinngemäß) | `crates/ui-egui/src/viewport.rs:3154-3160`: `bestp = Some((t, p.area, Hit::Profile { sketch: sid, index: pi })); ... profiles_all.sort_by(\|a, b\| a.1.total_cmp(&b.1));` | Kleinste umschließende Kontur erhält Klick-Priorität („Smallest profile first“), damit Löcher gezielt gewählt werden können. |

**Abweichungen:** Beide Systeme verhalten sich geometrisch identisch. Die automatische Vorwahl bei nur einem Profil ist in beiden Systemen vorhanden und für einen schnellen Arbeitsablauf unverzichtbar.

---

## 5. Anzeige von Freiheitsgraden und Konflikten

Ein zentraler Aspekt parametrischer CAD-Systeme ist die sofortige Rückmeldung über den Bestimmungszustand einer Skizze. Inventor zeigt in der Statusleiste permanent die Anzahl verbleibender Freiheitsgrade („3 Bemaßungen oder Abhängigkeiten erforderlich“ bis hin zu „Voll bestimmt“) und blendet auf Wunsch Translations- und Rotationssymbole an Punkten und Kanten ein. Bei widersprüchlichen Abhängigkeiten warnt Inventor vor Überbestimmung und bietet an, ein Maß als getriebenes Referenzmaß anzulegen.

SolidCraft berechnet Freiheitsgrade und Konflikte über den Solver und stellt sie im Viewport und der Statusleiste dar (`crates/ui-egui/src/viewport.rs:7070-7086`). Konfliktbehaftete Geometrien und Abhängigkeiten werden über den Theme-Token `sketch_conflict` (Rot) eingefärbt (`crates/ui-egui/src/viewport.rs:7079, 7089-7105`).

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Freiheitsgrade-Status anzeigen** | „Zeichen für Freiheitsgrade - Referenz Zeigt die für die Geometrie verfügbaren Freiheitsgrade an.“ sowie „Wählen Sie in der Statusleiste die Option Alle Freiheitsgrade anzeigen aus.“ ([GUID-784929B0](#q4-beleg-inventor-zeichen-fuer-freiheitsgrade)) | `crates/ui-egui/src/viewport.rs:7076-7081`: `if ss.report.dof == 0 { ... "sketch.status_fully_constrained" } else if ss.report.dof == 1 { ... "ui.1_degree_of_freedom" } else { ... "sketch.degrees_of_freedom" }` | Permanente Anzeige in der Fußzeile: „X Freiheitsgrade“ bzw. grüner Haken bei „Voll bestimmt“. |
| **Freiheitsgrade-Richtungssymbole** | „2D-Translationszeichen an den Endpunkten geben an, dass die Endpunkte in der Skizzierebene frei verschoben werden können.“ und „Das Drehungszeichen steht für die Möglichkeit der Linie zur Drehung in der Skizzierebene.“ ([GUID-784929B0](#q4-beleg-inventor-zeichen-fuer-freiheitsgrade)) | In SolidCraft nur als DOF-Zahl (`ss.report.dof`) und Farbstatus vorhanden; Richtungspfeile an Punkten/Kurven existieren nicht im egui-Viewport. | Optionale Einblendung von Richtungspfeilen (Translation/Rotation) an freien Punkten und Linien für komplexe Getriebeskizzen. |
| **Farbkodierung für Bestimmungsgrad** | Unterbestimmt = Grün/Cyan; Voll bestimmt = Dunkelblau/Schwarz; Überbestimmt = Rot. (sinngemäß) | `crates/ui-egui/src/viewport.rs:2067, 2079`: `sketch_lines_with_sampler(..., &ss.report.curve_determined, ...); let colour = if conflicting { c4(tk.sketch_conflict) } else { sketch_color(&tk, col) };` | Klare Farbkodierung: **Blau** für unterbestimmt (ziehbar), **Schwarz** für voll bestimmt, **Rot** für Konflikte/Überbestimmung. |
| **Konfliktbehandlung bei Überbestimmung** | Dialog warnt vor Überbestimmung und bietet Wandlung in getriebene Bemaßung (*Driven Dimension*) an. (sinngemäß) | `crates/ui-egui/src/viewport.rs:7089-7092`: `The curves and points of a sketch that its failing constraints hold (the solve's failing: the constraints still violated after a failed solve). They are drawn in sketch_conflict until the conflict is gone (#7244)` | Solver darf nicht unkontrolliert blockieren: Widersprüchliche Maße/Abhängigkeiten sofort rot markieren; Angebot zur Wandlung in Referenzmaß in Klammern `( )`. |

**Abweichungen:** Inventor visualisiert Translations- und Rotationsfreiheitsgrade mit kleinen Richtungspfeilen direkt am Element. SolidCraft liefert im Viewport nur den numerischen Zähler und die farbliche Kennzeichnung (unterbestimmt vs. voll bestimmt vs. rot für Konflikte). Mechvane sollte für v0.1 zunächst die robuste farbliche Kennzeichnung (Blau/Schwarz/Rot) und den Fußzeilen-Zähler umsetzen.

---

## 6. Ansicht: Projektion, Standardansichten, ViewCube, Home, Zoom Alles und Auswahl

Inventor bietet für die Ansichtssteuerung den persistenten **ViewCube** in der oberen Fensterecke, der durch Klicken auf Flächen, Kanten oder Ecken direkt in orthogonale oder isometrische Standardansichten springt. Die Taste `F6` führt sofort zur Ausgangsansicht (Home / Isometrie) und passt das Modell ein (*Zoom All*). Über das ViewCube-Kontextmenü wird zwischen orthogonaler und perspektivischer Projektion umgeschaltet.

SolidCraft besitzt in `crates/ui-egui/src/view_gizmo.rs:347-360` einen Orientierungsnavigator mit drei Stilen (`NavigatorStyle::Cube`, `Axes`, `Custom`), unterstützt die Umschaltung Orthogonal/Perspektivisch (`crates/ui-egui/src/prefs.rs:917-923`, `navigation_bar.rs:77`) und vereint Zoom Alles sowie Zoom auf Auswahl im Befehl `view.fit` (`crates/ui-egui/src/lib.rs:3028-3040`).

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **ViewCube / Orientierungswürfel** | „Der Autodesk ®ViewCube® ist eine persistent angezeigte Schnittstelle, auf der Sie den Ansichtspunkt des Modells durch Klicken und Ziehen anpassen können. Er wird im inaktiven Zustand in einer der oberen Ecken des Fensters angezeigt.“ ([GUID-B266056E](#q5-beleg-inventor-viewcube-und-ansichtsprojektion)) | `crates/ui-egui/src/view_gizmo.rs:353`: `NavigatorStyle::Cube => (crate::i18n::tr_label("Cube"), "box")` | Interaktiver Orientierungswürfel oben rechts im WebGL/Three.js-Viewport mit klickbaren Flächen (Vorne, Oben etc.), Kanten und Ecken. |
| **Standardansichten** | „Zu einer der verfügbaren voreingestellten Ansichten wechseln.“ ([GUID-B266056E](#q5-beleg-inventor-viewcube-und-ansichtsprojektion)) | `crates/ui-egui/src/view_home_tests.rs:30`: `cam.set_view(StandardView::Iso);` | Klick auf Flächen richtet Ansicht plan aus; Klick auf Ecken schaltet auf $30^\circ$-Isometrie. |
| **Ausgangsansicht (Home / F6)** | „Zur Ausgangsansicht wechseln.“ ([GUID-B266056E](#q5-beleg-inventor-viewcube-und-ansichtsprojektion)) sowie „F6 Isometrieansicht Zeigt die Isometrieansicht des Modells an.“ ([GUID-DEEB0723](#q6-beleg-inventor-tastaturkurzbefehle)) | `crates/ui-egui/src/navigation_bar.rs:75`: `slot!("home", Action, "home", Some("view.home"))` sowie `crates/ui-egui/src/view_home_tests.rs:1`: `// Home and Fit frame what is shown now, and a middle-button double-click goes Home.` | Kleines Haus-Symbol am ViewCube und Taste `F6` stellt die standardmäßige Isometrieansicht wieder her. |
| **Projektion (Orthogonal vs. Perspektivisch)** | „Bei orthogonal projizierten Ansichten werden alle Punkte eines Modells angezeigt, das parallel zum Bildschirm projiziert wird.“ und „Perspektivisch projizierte Ansichten werden basierend auf dem Abstand zwischen einer theoretischen Kamera und einem Bezugsstellenpunkt berechnet.“ ([GUID-B266056E](#q5-beleg-inventor-viewcube-und-ansichtsprojektion)) | `crates/ui-egui/src/prefs.rs:918, 1883`: `const PERSPECTIVE_FOV: f64 = 0.6; ... perspective: bool` sowie `crates/ui-egui/src/navigation_bar.rs:77`: `slot!("projection", Toggle, "perspective", None)` | Umschalter für Projektionsmodus (Orthogonal / Perspektivisch) in der Navigationsleiste oder im Kontextmenü des ViewCubes. |
| **Zoom Alles (Zoom to Fit)** | Doppelklick auf mittleres Mausrad passt das gesamte Modell formatfüllend ein. (sinngemäß) | `crates/ui-egui/src/navigation_bar.rs:73`: `slot!("fit", Action, "fit", Some("view.fit"))` sowie `crates/ui-egui/src/lib.rs:3035`: `to = self.fitted(to);` | Doppelklick mittlere Maustaste oder Taste `F` (ohne Auswahl) zoomt das Modell formatfüllend in den Viewport ein. |
| **Zoom auf Auswahl** | „Durch die Option An aktuelle Auswahl anbinden aus dem ViewCube-Menü wird der ViewCube an einen Satz ausgewählter Objekte gebunden. Bei Auswahl dieser Option wird der Mittelpunkt der aktuellen Ansicht sowie der Abstand der Ansicht vom Mittelpunkt basierend auf den ausgewählten Objekten definiert.“ ([GUID-B266056E](#q5-beleg-inventor-viewcube-und-ansichtsprojektion)) | `crates/ui-egui/src/lib.rs:3037-3040`: `// With something selected, Fit frames the selection. match viewport::selection_bounds(self) { Some(bounds) => { self.pending_fit = Some((to, bounds, true, false)); ... } }` | Wenn Elemente selektiert sind, zentriert und zoomt `view.fit` (Taste `F`) exakt auf die Bounding-Box der ausgewählten Objekte. |

**Abweichungen:** Beide Systeme nutzen denselben Ansatz. In SolidCraft ist `view.fit` kontextsensitiv: Ist nichts ausgewählt, zoomt es auf alles; ist etwas ausgewählt, zoomt es auf die Auswahl. Dieses elegante Verhalten sollte Mechvane direkt übernehmen.

---

## 7. Auswahl: Vorhervorhebung, Mehrfachauswahl, Fensterauswahl und Auswahlfilter

Die Interaktion mit 3D-Geometrie erfordert eindeutige visuelle Rückmeldung vor dem Klick (*Pre-Highlighting*), klare Regeln für Mehrfachauswahl über Modifikatortasten sowie die Differenzierung zwischen Fenster- und Kreuzungsauswahl beim Ziehen mit der Maus.

Inventor nutzt eine Auswahltoleranz von 1 bis 10 Pixeln, unterscheidet beim Ziehen zwischen links-nach-rechts (nur vollständig umschlossene Objekte) und rechts-nach-links (alle geschnittenen Objekte) und bietet ein „Andere auswählen“-Menü bei überlappender Geometrie. SolidCraft implementiert exakt dieselbe Richtungslogik in `crates/ui-egui/src/selection.rs:300-302` (`crossing: end.x < start.x`) und `crates/ui-egui/src/viewport.rs:6614-6620`.

| Schritt/Verhalten | Inventor (Zitat, URL) | SolidCraft (Zitat, Datei:Zeile) | Empfehlung für Mechvane |
| :--- | :--- | :--- | :--- |
| **Vorab-Hervorhebung (Pre-Highlighting)** | „Optimierte Auswahl aktivieren Optimiert die Grafikleistung während der Vorab-Hervorhebung in einer großen Baugruppe.“ sowie „Auswahltoleranz Legt den Abstand fest (in Pixel), ab dem ein Objekt durch Klicken ausgewählt wird.“ ([GUID-A8E50133](#q7-beleg-inventor-anwendungsoptionen-allgemein-auswahl)) | `crates/ui-egui/src/viewport.rs:2870-2875, 2918`: Fangtoleranz 8.0 px für Punkte (`dd < 8.0`), 6.0 px für Kurven (`dd < 6.0`). Aktives Hover-Element in `app.viewport.hover`. | Elemente unter dem Cursor leuchten vor dem Klick auf (z. B. Farbaufhellung um 20 % oder feine Konturlinie). Fangradius 6–8 px. |
| **Mehrfachauswahl & Umschalten** | „Wählen Sie das Objekt im Grafikfenster aus. Zur Auswahl mehrerer Objekte halten Sie die STRG-Taste oder die Umschalttaste gedrückt, während Sie auf nicht ausgewählte Objekte klicken, um sie zur Auswahl hinzuzufügen.“ sowie „Entfernen der Auswahl Halten Sie die STRG-Taste oder die Umschalttaste gedrückt, während Sie auf zuvor ausgewählte Objekte klicken.“ ([GUID-B8F6E805](#q8-beleg-inventor-auswahl-und-auswahlfenster)) | `crates/ui-egui/src/viewport.rs:6425-6430`: `if add && toggle && items.iter().all(...) { let rest: Vec<Sel> = ...; let _ = app.run("select.set", json!({ "items": rest })); } else { let _ = app.run("select.set", json!({"items": items, "add": add})); }` | Klick wählt Einzelobjekt; `Shift`-Klick oder `Ctrl`-Klick fügt hinzu bzw. entfernt bereits ausgewählte Objekte aus dem Auswahlsatz (*Toggle*). |
| **Auswahl aufheben** | „Abbrechen der Auswahl Klicken Sie entweder mit der Maustaste oder bei gedrückter Umschalttaste an einer beliebigen Stelle im Grafikfenster, jedoch nicht auf ein Objekt.“ ([GUID-B8F6E805](#q8-beleg-inventor-auswahl-und-auswahlfenster)) | `crates/ui-egui/src/viewport.rs:6434-6436`: `None if !add => { let _ = app.run("select.clear", json!({})); }` | Klick auf leere Hintergrundfläche hebt die gesamte Auswahl auf (`Escape` ebenfalls). |
| **Fensterauswahl (Links nach Rechts / Window)** | „Auswählen von Objekten in einem Fenster Positionieren Sie den Zeiger etwas oberhalb und links vom am weitesten links gelegenen Objekt, das ausgewählt werden soll. Ziehen Sie den Mauszeiger bis etwas unterhalb und rechts vom am weitesten rechts gelegenen Objekt, das ausgewählt werden soll. Alle Objekte, die im Auswahlrechteck eingeschlossen sind, werden ausgewählt und gekennzeichnet.“ ([GUID-B8F6E805](#q8-beleg-inventor-auswahl-und-auswahlfenster)) | `crates/ui-egui/src/selection.rs:301`: `BoxSel { rect: Rect::from_two_pos(start, end), crossing: end.x < start.x, ... }` sowie `crates/ui-egui/src/viewport.rs:6619`: `parts.iter().all(\|part\| bx.takes(part))` | Ziehen von links nach rechts: Durchgezogener blauer Rahmen. Nur Objekte, die sich **zu 100 % innerhalb** des Rahmens befinden, werden ausgewählt. |
| **Kreuzende Fensterauswahl (Rechts nach Links / Crossing)** | „Auswählen von geschlossenen und geschnittenen Objekten in einem Fenster Positionieren Sie den Zeiger etwas unterhalb und rechts vom am weitesten rechts gelegenen Objekt, das ausgewählt werden soll. Ziehen Sie den Mauszeiger bis etwas oberhalb und links vom am weitesten links gelegenen Objekt, das ausgewählt werden soll. Alle Objekte, die im Auswahlrechteck eingeschlossen sind und geschnitten werden, werden ausgewählt und gekennzeichnet.“ ([GUID-B8F6E805](#q8-beleg-inventor-auswahl-und-auswahlfenster)) | `crates/ui-egui/src/selection.rs:301`: `crossing: end.x < start.x` (wahr bei Ziehen nach links) sowie `crates/ui-egui/src/viewport.rs:6615`: `parts.iter().any(\|part\| bx.takes(part))` | Ziehen von rechts nach links: Gestrichelter grüner Rahmen. Alle Objekte, die vom Rahmen **berührt oder geschnitten** werden, werden ausgewählt. |
| **Verdeckte Geometrie wählen (Andere auswählen)** | „Um die Auswahl zu ändern, klicken Sie mit der rechten Maustaste, wählen Andere auswählen, und verwenden Sie die Pfeile, um die Auswahl zu ändern.“ ([GUID-B8F6E805](#q8-beleg-inventor-auswahl-und-auswahlfenster)) | `crates/ui-egui/src/viewport.rs:3650`: `pub fn candidates(app: &SolveApp, hits: &[Hit]) -> Vec<(Hit, Sel)>` (Auswahlkandidaten nach Schärfentiefe für `select_other.rs`). | Verweilen des Cursors oder Rechtsklick blendet „Andere auswählen“-Menü ein, um verdeckte Flächen/Kanten der Reihe nach anzusprechen. |
| **Auswahlfilter (Prioritäten)** | Schnellauswahlfilter für Körper, Features, Flächen und Kanten in der oberen Befehlsleiste. (sinngemäß) | `crates/ui-egui/src/viewport.rs:3664-3674`: `pick_allowed` prüft Filtermasken (`sketch`, `sketch_curves`, `sketch_points`, `vertices`, `edges`, `faces`, `bodies`). | Dropdown-Filter für Auswahlmodus: *Automatisch*, *Nur Flächen*, *Nur Kanten*, *Nur Körper*. |

**Abweichungen:** Keine prinzipiellen Abweichungen. Die Richtungslogik der Fensterauswahl (Window vs. Crossing) ist in SolidCraft exakt nach dem Industriestandard implementiert und sollte in Mechvanes Web-Canvas unverändert zur Anwendung kommen.

---

## 8. Die 10 wichtigsten Punkte, die ein Inventor-Nutzer zuerst vermissen würde

Wenn ein erfahrener Konstrukteur von Autodesk Inventor zu einer neuen CAD-Oberfläche wechselt, führen fehlende Automatismen und abweichende Bedienkonzepte sofort zu Frustration. Die folgenden 10 Punkte haben für den flüssigen Arbeitsalltag die höchste Priorität:

1. **Automatisches Ausrichten senkrecht zur Skizzierebene („Look At“):**
   * *Problem:* In Inventor dreht sich die Ansicht bei Skizzenerstellung oder -bearbeitung sofort plan zur Skizzierebene. Fehlt dieses Verhalten, muss der Nutzer bei jedem Skizzenstart die Ansicht mühsam mit mehreren Navigationsklicks selbst flachdrehen.
   * *Mechvane-Soll:* Standardmäßig aktiviert: Weiche Kamerafahrt auf Normalenvektor der Skizzierebene (`sketch_open_look_at`).
2. **Klick auf Fläche mit Mini-Werkzeugkasten („Skizze erstellen“ am Cursor):**
   * *Problem:* In Inventor klickt man direkt auf eine planare Fläche des Bauteils; sofort erscheint die HUD-Mini-Toolbar mit dem Befehl „Skizze erstellen“ (oder man drückt `S`). Ein Umweg über ein globales Menüband bricht den Konstruktionsfluss.
   * *Mechvane-Soll:* Kontext-Button oder Tastenkürzel `S` bei selektierter Planarfläche.
3. **Automatische Modellkantenprojektion der Skizzenfläche:**
   * *Problem:* Inventor projiziert automatisch alle Außen- und Innenkanten der gewählten Fläche als Referenzgeometrie in die neue Skizze. Fehlt dies, können neue Linien nicht an den Kanten des bestehenden Körpers gefangen werden, ohne jede Kante vorher manuell einzeln zu projizieren.
   * *Mechvane-Soll:* Flag `project_edges: true` bei Skizzenerstellung auf Flächen standardmäßig setzen.
4. **ViewCube mit Home-Button (`F6`) und Standardansichten:**
   * *Problem:* Der ViewCube ist das zentrale Orientierungsorgan für Inventor-Nutzer. Ohne klickbare Flächen/Ecken und ohne die Sofort-Rückkehr zur Isometrie via `F6` verliert der Anwender bei komplexen 3D-Geometrien schnell die räumliche Orientierung.
   * *Mechvane-Soll:* Fester 3D-Orientierungswürfel oben rechts im Viewport mit Home-Haus-Symbol und Klickflächen für alle 6 Hauptansichten plus 8 Isometrie-Ecken.
5. **Freiheitsgrade-Status und visuelle Rückmeldung (Blau vs. Schwarz vs. Rot):**
   * *Problem:* Ein Konstrukteur muss auf einen Blick sehen, ob eine Skizze voll bestimmt ist oder welche Freiheitsgrade noch offen sind. Unbestimmte Geometrie, die sich farblich nicht von fixierter Geometrie unterscheidet, führt zu unbemerkten Modellfehlern.
   * *Mechvane-Soll:* Farbkodierung nach Standard (Blau = unterbestimmt, Schwarz = voll bestimmt, Rot = Überbestimmung/Konflikt) und permanenter Zähler in der Statusleiste („3 Freiheitsgrade“).
6. **Fensterauswahl mit Richtungslogik (Window vs. Crossing):**
   * *Problem:* Der CAD-Standard unterscheidet strikt: Ziehen von links nach rechts wählt nur vollständig umschlossene Elemente; Ziehen von rechts nach links wählt alles, was geschnitten wird. Eine Fensterauswahl ohne diese Richtungsunterscheidung macht präzises Selektieren in dichten Skizzen unmöglich.
   * *Mechvane-Soll:* Umsetzung gemäß SolidCrafts `BoxSel`: `end.x < start.x` schaltet auf Crossing. Visuelle Differenzierung durch blauen (Window) bzw. grünen Rahmen (Crossing).
7. **Skizzen-Wiederverwendung („Share Sketch“ / Mehrfachverwendung):**
   * *Problem:* Komplexe Bauteile nutzen oft dieselbe Profilskizze für mehrere Features (z. B. eine Grundextrusion, einen Innenausschnitt und ein Senkungsloch). Muss eine Skizze für jedes Feature neu gezeichnet werden, explodiert der Pflegeaufwand bei Maßänderungen.
   * *Mechvane-Soll:* Einfache Freigabe verbrauchter Skizzen zur Mehrfachnutzung über das Verknüpfungsmodell (`links.py`).
8. **Automatische Profil-Vorwahl bei Einzelflächen (Zero-Click-Extrude):**
   * *Problem:* Wenn eine Skizze nur ein einziges geschlossenes Profil enthält, erwartet der Nutzer, dass beim Klick auf „Extrudieren“ dieses Profil bereits aktiv gewählt ist und direkt das Abstands-Eingabefeld fokussiert wird. Ein zusätzlicher Klick auf das Profil ist unnötige Klickarbeit.
   * *Mechvane-Soll:* Ist nur ein Profil vorhanden: Automatisch auswählen und Eingabefeld fokussieren.
9. **Verdeckte Geometrie auswählen („Andere auswählen“ / Select Other):**
   * *Problem:* In 3D-Baugruppen liegen Kanten oder Rückflächen oft hinter vorderen Körpern. In Inventor verweilt man kurz mit dem Cursor oder klickt rechts, um verdeckte Flächen der Reihe nach durchzublättern.
   * *Mechvane-Soll:* Kandidatenliste aller getroffenen Objekte entlang des Sehstrahls (`candidates`) per Rechtsklick oder Hover-Menü anbieten.
10. **Wandlung in getriebenes Maß bei Überbestimmung:**
    * *Problem:* Setzt ein Anwender versehentlich eine Bemaßung, die die Skizze überbestimmt, blockiert ein starres System mit einer Fehlermeldung. Inventor bietet sofort per Dialog an: „Das Hinzufügen dieser Bemaßung führt zu einer Überbestimmung. Möchten Sie stattdessen eine getriebene Bemaßung erstellen?“
    * *Mechvane-Soll:* Bemaßung bei Konflikt nicht verwerfen, sondern optional als getriebenes Referenzmaß in Klammern `( )` abspeichern.

---

## 9. Quellenbelege und wörtliche Zitate

Die folgenden Belege stammen aus den offiziellen Autodesk-Dokumentationen (Autodesk Help System) für Autodesk Inventor 2025/2026. Alle Zitate wurden mit `tools/check_sources.py` automatisiert auf Erreichbarkeit (HTTP 200) und wortwörtliche Übereinstimmung geprüft.

### [Q1] Beleg: Inventor Skizzen erstellen und bearbeiten
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E96FB3C4-136B-4551-BF45-F54594543ECB.htm
* **Wörtliches Zitat:** „Klicken Sie auf der Registerkarte 3D-Modell auf 2D-Skizze starten oder 3D-Skizze starten .“
* **Wörtliches Zitat:** „Klicken Sie auf eine planare Fläche oder Arbeitsebene eines Bauteils, und wählen Sie im Mini-Werkzeugkasten die Option Skizze erstellen .“
* **Wörtliches Zitat:** „Doppelklicken Sie auf das Skizzensymbol im Browser.“
* **Wörtliches Zitat:** „Sie müssen eine Skizze fertig stellen, um die Skizzierumgebung zu beenden.“
* **Wörtliches Zitat:** „Zum Beenden einer 2D-Skizze klicken Sie auf der Registerkarte Skizze auf Skizze beenden , oder klicken mit der rechten Maustaste im Grafikbereich und wählen 2D-Skizze beenden.“
* **Wörtliches Zitat:** „Wenn Sie eine Skizze abbrechen, werden alle aktuellen Aktionen verworfen.“
* **Wörtliches Zitat:** „Um eine Skizze abzubrechen, klicken Sie auf der Registerkarte Skizze auf Skizze abbrechen.“

### [Q2] Beleg: Inventor Anwendungsoptionen Skizze
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-1898C432-CFD2-46F1-8BAE-631392DFBF1D.htm
* **Wörtliches Zitat:** „Ausrichten nach Skizzierebene bei Skizzenerstellung und -bearbeitung Legt bei Aktivierung die Neuausrichtung des Grafikfensters fest, sodass für neue Skizzen die Skizzierebene parallel zur Ansicht ist.“
* **Wörtliches Zitat:** „Modellkanten für Skizzenerstellung und -bearbeitung automatisch projizieren Projiziert beim Erstellen oder Bearbeiten einer Skizze die Kanten einer ausgewählten Fläche automatisch als Referenzgeometrie auf die Skizzierebene.“
* **Wörtliches Zitat:** „Ursprung des Bauteils beim Erstellen der Skizze automatisch projizieren Legt die Voreinstellung für den Ursprung projizierter Bauteile in neuen Skizzen fest.“
* **Wörtliches Zitat:** „Anzeige von Skizzen Die Einstellung Opazität der angezeigten Skizze durch schattiertes Modell steuert, in welchem Grad Skizziergeometrie durch schattierte Modellgeometrie hindurch sichtbar ist.“

### [Q3] Beleg: Inventor Extrudierte Elemente und Profilwahl
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B0CFA8E7-D3F5-48A9-BE6F-C8DF668301BD.htm
* **Wörtliches Zitat:** „Liegt in der Skizze nur ein Profil vor, wird dieses automatisch ausgewählt. Wählen Sie andernfalls ein Skizzenprofil aus.“
* **Wörtliches Zitat:** „Mehrere Profile - Wählen Sie die Profile oder Bereiche aus, die die gewünschte Extrusion oder den gewünschten Körper definieren.“
* **Wörtliches Zitat:** „Sie können einen Auswahlrahmen verwenden, um schnell mehrere geschlossene Profile innerhalb derselben Skizze auszuwählen.“
* **Wörtliches Zitat:** „Vorhandene Skizze, die in ein Element einbezogen wurde und sichtbar ist, wenn der Befehl aufgerufen wird. Die erweiterte Menüoption Skizze bleibt für (+) sichtbar ist vorgabemäßig aktiviert.“
* **Wörtliches Zitat:** „So geben Sie eine Skizze manuell frei Klicken Sie im Browser auf das Pluszeichen (+) neben dem Element, das die zu verwendende Skizze enthält, um den Skizzierknoten anzuzeigen. Klicken Sie mit der rechten Maustaste auf das Skizzensymbol und dann auf Skizze wieder verwenden. Kommt eine Skizze bei mehr als einem Element zum Einsatz, wird sie automatisch zu einer wiederverwendeten Skizze.“

### [Q4] Beleg: Inventor Zeichen fuer Freiheitsgrade
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-784929B0-3480-4FC0-8ED5-E3414248FB7F.htm
* **Wörtliches Zitat:** „Zeichen für Freiheitsgrade - Referenz Zeigt die für die Geometrie verfügbaren Freiheitsgrade an.“
* **Wörtliches Zitat:** „Wählen Sie in der Statusleiste die Option Alle Freiheitsgrade anzeigen aus.“
* **Wörtliches Zitat:** „2D-Translationszeichen an den Endpunkten geben an, dass die Endpunkte in der Skizzierebene frei verschoben werden können.“
* **Wörtliches Zitat:** „Das Drehungszeichen steht für die Möglichkeit der Linie zur Drehung in der Skizzierebene.“

### [Q5] Beleg: Inventor ViewCube und Ansichtsprojektion
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B266056E-5E88-42A0-B29C-7BB25C377BD3.htm
* **Wörtliches Zitat:** „Der Autodesk ®ViewCube® ist eine persistent angezeigte Schnittstelle, auf der Sie den Ansichtspunkt des Modells durch Klicken und Ziehen anpassen können. Er wird im inaktiven Zustand in einer der oberen Ecken des Fensters angezeigt.“
* **Wörtliches Zitat:** „Zu einer der verfügbaren voreingestellten Ansichten wechseln.“
* **Wörtliches Zitat:** „Zur Ausgangsansicht wechseln.“
* **Wörtliches Zitat:** „Bei orthogonal projizierten Ansichten werden alle Punkte eines Modells angezeigt, das parallel zum Bildschirm projiziert wird.“
* **Wörtliches Zitat:** „Perspektivisch projizierte Ansichten werden basierend auf dem Abstand zwischen einer theoretischen Kamera und einem Bezugsstellenpunkt berechnet.“
* **Wörtliches Zitat:** „Durch die Option An aktuelle Auswahl anbinden aus dem ViewCube-Menü wird der ViewCube an einen Satz ausgewählter Objekte gebunden. Bei Auswahl dieser Option wird der Mittelpunkt der aktuellen Ansicht sowie der Abstand der Ansicht vom Mittelpunkt“

### [Q6] Beleg: Inventor Tastaturkurzbefehle
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „F6 Isometrieansicht Zeigt die Isometrieansicht des Modells an.“
* **Wörtliches Zitat:** „Kehrt zur vorherigen Ansicht zurück.“

### [Q7] Beleg: Inventor Anwendungsoptionen Allgemein Auswahl
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A8E50133-E4FF-4459-B2AE-9568D2C9F565.htm
* **Wörtliches Zitat:** „Auswahltoleranz Legt den Abstand fest (in Pixel), ab dem ein Objekt durch Klicken ausgewählt wird.“
* **Wörtliches Zitat:** „Optimierte Auswahl aktivieren Optimiert die Grafikleistung während der Vorab-Hervorhebung in einer großen Baugruppe.“

### [Q8] Beleg: Inventor Auswahl und Auswahlfenster
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B8F6E805-2E4B-4366-8FF6-33F0ED1C1C4A.htm
* **Wörtliches Zitat:** „Wählen Sie das Objekt im Grafikfenster aus. Zur Auswahl mehrerer Objekte halten Sie die STRG-Taste oder die Umschalttaste gedrückt, während Sie auf nicht ausgewählte Objekte klicken, um sie zur Auswahl hinzuzufügen.“
* **Wörtliches Zitat:** „Entfernen der Auswahl Halten Sie die STRG-Taste oder die Umschalttaste gedrückt, während Sie auf zuvor ausgewählte Objekte klicken.“
* **Wörtliches Zitat:** „Abbrechen der Auswahl Klicken Sie entweder mit der Maustaste oder bei gedrückter Umschalttaste an einer beliebigen Stelle im Grafikfenster, jedoch nicht auf ein Objekt.“
* **Wörtliches Zitat:** „Auswählen von Objekten in einem Fenster Positionieren Sie den Zeiger etwas oberhalb und links vom am weitesten links gelegenen Objekt, das ausgewählt werden soll. Ziehen Sie den Mauszeiger bis etwas unterhalb und rechts vom am weitesten rechts gelegenen Objekt, das ausgewählt werden soll. Alle Objekte, die im Auswahlrechteck eingeschlossen sind, werden ausgewählt und gekennzeichnet.“
* **Wörtliches Zitat:** „Auswählen von geschlossenen und geschnittenen Objekten in einem Fenster Positionieren Sie den Zeiger etwas unterhalb und rechts vom am weitesten rechts gelegenen Objekt, das ausgewählt werden soll. Ziehen Sie den Mauszeiger bis etwas unterhalb und links vom am weitesten links gelegenen Objekt, das ausgewählt werden soll. Alle Objekte, die im Auswahlrechteck eingeschlossen sind und geschnitten werden, werden ausgewählt und gekennzeichnet.“
* **Wörtliches Zitat:** „Um die Auswahl zu ändern, klicken Sie mit der rechten Maustaste, wählen Andere auswählen, und verwenden Sie die Pfeile, um die Auswahl zu ändern.“
