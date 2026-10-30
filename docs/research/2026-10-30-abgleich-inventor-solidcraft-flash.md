# Abgleichliste: Autodesk Inventor ↔ SolidCraft ↔ Mechvane

- **Datum:** 2026-10-30
- **Autor:** Gemini 3.8 Flash (Issue #23)
- **Status:** Verifiziert mit `tools/check_sources.py` und gegen `solidcraft-cli commands` / Sparse-Klon `/root/repos/_ext/solidcraft`
- **Kontext & Ziel:** Mechvane soll sich so nah wie möglich an Autodesk Inventor bedienen lassen (ROADMAP, Grundsatz 10: *„Bedienung am Ende möglichst nah an Inventor. Wer Inventor kennt, soll ohne Umlernen arbeiten können. Gemeint sind Aufbau und Begriffe der Oberfläche... Optisch aber dunkler und schicker als Inventor“*). Dieser Bericht liefert die systematische Abgleichliste für Menüband-Register (Ribbon-Tabs), Standard-Tastenkürzel, Modellbrowser (Feature-Baum, EOP-Marker, Unterdrücken, Neu ordnen) und Dialogarchitektur (Mini-Werkzeugkästen, Direkteingabe im Grafikfenster, Eigenschaftsgruppen), aus der sich ableiten lässt, was über SolidCraft-Befehle konfigurierbar ist und wo Mechvane eine eigene Oberfläche bzw. Oberflächen-Plugins benötigt.

---

## 1. Register/Ribbon-Tabs von Inventor und ihre wichtigsten Befehle

In Autodesk Inventor ist die Benutzeroberfläche in aufgabenspezifische Arbeitsumgebungen unterteilt. Jede Umgebung besitzt eine eigene Multifunktionsleiste (Ribbon) mit thematisch gegliederten Gruppen (*Panels*):
- **Skizzierumgebung (Register „Skizze“ / `Sketch`):** Aktiv beim Erstellen oder Bearbeiten einer 2D-Skizze auf einer Bauteilfläche oder Arbeitsebene.
- **Bauteilumgebung (Register „3D-Modell“ / `3D Model`):** Hauptarbeitsbereich zur volumenbasierten und flächenbasierten Modellierung parametrischer Einzelteile (`.ipt`).
- **Baugruppenumgebung (Register „Zusammenfügen“ / `Assemble` & „Prüfen“ / `Inspect`):** Arbeitsbereich zum Positionieren, Verknüpfen und Analysieren von Komponenten (`.iam`).

Die folgenden Tabellen stellen jeden Befehl mit seinem Standard-Tastenkürzel der exakten Befehls-ID in SolidCraft (`solidcraft-cli commands`) und der Entsprechung in Mechvane (`docs/mechvane-mcp.md`, `mechvane/server.py`) gegenüber.

### 1.1 Register „Skizze“ (Sketch)

| Inventor-Begriff/-Befehl | Inventor-Kürzel | SolidCraft-Befehl (ID) | Mechvane-Entsprechung | Bemerkung / Einordnung |
| :--- | :---: | :--- | :--- | :--- |
| **2D-Skizze starten** | `S` | `sketch.create` | `run(..., [sketch.create])` | In Inventor startet `S` die Skizze auf gewählter Fläche (`GUID-DEEB0723`). In SolidCraft öffnet `S` die Befehlssuche (`ui.palette`); Mechvane ordnet Skizzen hierarchisch vor Features an (`tree.py`). |
| **Linie** | `L` | `sketch.line` | `run(..., [sketch.line])` | Volle Übereinstimmung beim Kürzel `L` (`GUID-DEEB0723`). Unterstützt Linienzüge und Tangentenbögen. |
| **Kreis durch Mittelpunkt** | `C` | `sketch.circle.center` | `run(..., [sketch.circle.center])` | Volle Übereinstimmung beim Kürzel `C` (`GUID-DEEB0723`). Mittelpunkt- und Durchmesser-Eingabe. |
| **Kreis tangential** | – | `sketch.circle.two_tangent` | `run(..., [sketch.circle.two_tangent])` | Erzeugt Kreis tangential an zwei Kurven (`GUID-D489CE6D`). In SolidCraft `sketch.circle.two_tangent`. |
| **Bogen durch 3 Punkte** | – | `sketch.arc.three_point` | `run(..., [sketch.arc.three_point])` | Start-, End- und Radiuspunkt (`GUID-D489CE6D`). In SolidCraft `sketch.arc.three_point`. |
| **Bogen durch Mittelpunkt** | – | `sketch.arc.center_point` | `run(..., [sketch.arc.center_point])` | Mittelpunkt, Start- und Endwinkel (`GUID-D489CE6D`). In SolidCraft `sketch.arc.center_point`. |
| **Bogen tangential** | – | `sketch.arc.tangent` | `run(..., [sketch.arc.tangent])` | Schließt tangential an bestehende Kurve an (`GUID-D489CE6D`). In SolidCraft `sketch.arc.tangent`. |
| **Rechteck durch 2 Punkte** | – | `sketch.rectangle.two_point` | `run(..., [sketch.rectangle.two_point])` | In Inventor ohne Kürzel (`GUID-D489CE6D`). In SolidCraft mit Tastenkürzel `R` belegt (Konflikt mit Inventor-Drehung). |
| **Rechteck durch 3 Punkte** | – | `sketch.rectangle.three_point` | `run(..., [sketch.rectangle.three_point])` | Definiert Basislinie und Höhe (`GUID-D489CE6D`). In SolidCraft `sketch.rectangle.three_point`. |
| **Rechteck durch Mittelpunkt** | – | `sketch.rectangle.center` | `run(..., [sketch.rectangle.center])` | Mittelpunkt und Eckpunkt (`GUID-D489CE6D`). In SolidCraft `sketch.rectangle.center`. |
| **Langloch** | – | `sketch.slot.center_to_center` | `run(..., [sketch.slot.*])` | Langloch über Achsabstand und Radius (`GUID-D489CE6D`). In SolidCraft als Familie von `sketch.slot.*`-Befehlen. |
| **Polygon** | – | `sketch.polygon.inscribed` | `run(..., [sketch.polygon.*])` | Regelmäßiges Vieleck (`GUID-D489CE6D`). In SolidCraft `sketch.polygon.inscribed`. |
| **Spline (Interpolation)** | – | `sketch.spline.fit_point` | `run(..., [sketch.spline.fit_point])` | Spline durch Passpunkte (`GUID-D489CE6D`). In SolidCraft `sketch.spline.fit_point`. |
| **Spline (Steuerrahmen)** | – | `sketch.spline.control_point` | `run(..., [sketch.spline.control_point])` | Spline über Kontrollpolygon (`GUID-D489CE6D`). In SolidCraft `sketch.spline.control_point`. |
| **Punkt / Mittelpunkt** | – | `sketch.point` | `run(..., [sketch.point])` | Skizzenpunkte und Bohrungszentren (`GUID-D4A4288F`). In SolidCraft `sketch.point`. |
| **Text** | `T` | `sketch.text` | `run(..., [sketch.text])` | In Inventor Tastenkürzel `T` (`GUID-DEEB0723`). Konflikt: In SolidCraft ist `T` für *Stutzen* vergeben. |
| **Geometrie projizieren** | – | `sketch.project` | `run(..., [sketch.project])` | Projiziert Kanten und Flächen (`GUID-B8D8B07B`). In SolidCraft mit Kürzel `P` belegt (Konflikt mit Inventor-Platzieren). |
| **Schnittkanten projizieren** | – | `sketch.intersect` | `run(..., [sketch.intersect])` | Schneidet Bauteilkörper mit Skizzierebene (`GUID-B8D8B07B`). In SolidCraft `sketch.intersect`. |
| **Stutzen** | `TR` | `sketch.trim` | `run(..., [sketch.trim])` | Kürzt Kurven an Schnittpunkten (`GUID-DEEB0723`, `GUID-DD00037F`). In SolidCraft Tastenkürzel `T`. |
| **Dehnen** | – | `sketch.extend` | `run(..., [sketch.extend])` | Verlängert Kurve bis zur nächsten Begrenzung (`GUID-DD00037F`). In SolidCraft `sketch.extend`. |
| **Teilen** | – | `sketch.break` | `run(..., [sketch.break])` | Teilt Kurve am Schnittpunkt (`GUID-DD00037F`). In SolidCraft `sketch.break`. |
| **Versatz** | – | `sketch.offset` | `run(..., [sketch.offset])` | Äquidistanter Kurvenversatz (`GUID-962CEE71`). In SolidCraft mit Tastenkürzel `O` belegt. |
| **Verschieben** | – | `sketch.move` | `run(..., [sketch.move])` | Verschiebt Skizzengeometrie (`GUID-F8114270`). In SolidCraft `sketch.move`. |
| **Drehen** | – | `sketch.transform` | `run(..., [sketch.transform])` | Dreht Geometrie (`GUID-F8114270`). In SolidCraft kombiniert in `sketch.transform` (Kürzel `G`). |
| **Skalieren** | – | `sketch.scale` | `run(..., [sketch.scale])` | Skaliert Geometrie um Basispunkt (`GUID-962CEE71`). In SolidCraft `sketch.scale`. |
| **Rechteckige Anordnung** | `RP` | `sketch.pattern.rectangular` | `run(..., [sketch.pattern.rectangular])` | Skizzenraster (`GUID-DEEB0723`, `GUID-AAD3A699`). In SolidCraft `sketch.pattern.rectangular`. |
| **Runde Anordnung** | `CP` | `sketch.pattern.circular` | `run(..., [sketch.pattern.circular])` | Kreisanordnung (`GUID-DEEB0723`, `GUID-AAD3A699`). In SolidCraft `sketch.pattern.circular`. |
| **Spiegeln** | – | `sketch.mirror` | `run(..., [sketch.mirror])` | Spiegelt Skizzenkurven an Achse (`GUID-AAD3A699`). In SolidCraft `sketch.mirror`. |
| **Allgemeine Bemaßung** | `D` | `sketch.dimension` | `run(..., [sketch.dimension])` | Volle Übereinstimmung beim Kürzel `D` (`GUID-DEEB0723`, `GUID-5E25D5FB`). Universelles Maßwerkzeug. |
| **Abhängigkeit: Koinzident** | – | `sketch.constraint.coincident` | `run(..., [sketch.constraint.coincident])` | Punkt-auf-Punkt-/Kurven-Bindung (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.coincident`. |
| **Abhängigkeit: Kollinear** | – | `sketch.constraint.collinear` | `run(..., [sketch.constraint.collinear])` | Fluchtende Linien (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.collinear`. |
| **Abhängigkeit: Konzentrisch** | – | `sketch.constraint.concentric` | `run(..., [sketch.constraint.concentric])` | Gemeinsamer Mittelpunkt (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.concentric`. |
| **Abhängigkeit: Festgelegt** | – | `sketch.constraint.fix` | `run(..., [sketch.constraint.fix])` | Sperrt Freiheitsgrade (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.fix`. |
| **Abhängigkeit: Parallel** | – | `sketch.constraint.parallel` | `run(..., [sketch.constraint.parallel])` | Parallele Linien (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.parallel`. |
| **Abhängigkeit: Lotrecht** | – | `sketch.constraint.perpendicular` | `run(..., [sketch.constraint.perpendicular])` | Rechtwinklige Kurven (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.perpendicular`. |
| **Abhängigkeit: Horizontal** | `-` | `sketch.constraint.horizontal_vertical` | `run(..., [sketch.constraint.horizontal_vertical])` | In Inventor Tastenkürzel Bindestrich `-` (`GUID-DEEB0723`, `GUID-A85A7A30`). SolidCraft fasst Horizontal/Vertikal zusammen. |
| **Abhängigkeit: Vertikal** | – | `sketch.constraint.horizontal_vertical` | `run(..., [sketch.constraint.horizontal_vertical])` | In Inventor eigene Schaltfläche (`GUID-A85A7A30`). In SolidCraft über Richtungsheuristik im selben Befehl. |
| **Abhängigkeit: Tangential** | – | `sketch.constraint.tangent` | `run(..., [sketch.constraint.tangent])` | Tangentialer Übergang (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.tangent`. |
| **Abhängigkeit: Stetig (G2)** | – | `sketch.constraint.curvature` | `run(..., [sketch.constraint.curvature])` | Krümmungsstetigkeit an Splines (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.curvature`. |
| **Abhängigkeit: Symmetrisch** | – | `sketch.constraint.symmetry` | `run(..., [sketch.constraint.symmetry])` | Spiegelsymmetrie zur Achse (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.symmetry`. |
| **Abhängigkeit: Gleich** | – | `sketch.constraint.equal` | `run(..., [sketch.constraint.equal])` | Gleiche Länge oder Radius (`GUID-A85A7A30`). In SolidCraft `sketch.constraint.equal`. |
| **Konstruktionsgeometrie** | – | `sketch.construction` | `run(..., [sketch.construction])` | Hilfsgeometrie umschalten (`GUID-F5A5790A`). In SolidCraft mit Tastenkürzel `X` belegt. |
| **Mittellinie** | – | `sketch.centerline` | `run(..., [sketch.centerline])` | Rotationsachse für Drehelemente (`GUID-D4A4288F`). In SolidCraft `sketch.centerline`. |
| **Getriebene Bemaßung** | – | `sketch.toggle_driven` | `run(..., [sketch.toggle_driven])` | Referenzmaß ohne Überbestimmung (`GUID-026FE8D3`). In SolidCraft `sketch.toggle_driven`. |
| **Skizze beenden** | – | `sketch.finish` | `run(..., [sketch.finish])` | Schließt Skizziermodus ab (`GUID-E96FB3C4`). In SolidCraft `sketch.finish` (UI: Doppel-Escape). |

---

### 1.2 Register „3D-Modell“ (Bauteil / Part Environment)

| Inventor-Begriff/-Befehl | Inventor-Kürzel | SolidCraft-Befehl (ID) | Mechvane-Entsprechung | Bemerkung / Einordnung |
| :--- | :---: | :--- | :--- | :--- |
| **Extrusion** | `E` | `solid.extrude` | `run(..., [solid.extrude])` | Volle Übereinstimmung beim Kürzel `E` (`GUID-DEEB0723`, `GUID-B0CFA8E7`). Lineare Aufdickung. |
| **Drehung** | `R` | `solid.revolve` | `run(..., [solid.revolve])` | In Inventor Kürzel `R` (`GUID-DEEB0723`, `GUID-B0CFA8E7`). Konflikt: In SolidCraft für Rechteck vergeben. |
| **Sweeping** | `SW` | `solid.sweep` | `run(..., [solid.sweep])` | Profil entlang Leitkurve (`GUID-DEEB0723`, `GUID-B0CFA8E7`). In SolidCraft `solid.sweep`. |
| **Erhebung** | `LO` | `solid.loft` | `run(..., [solid.loft])` | Übergang zwischen Querschnitten (`GUID-DEEB0723`, `GUID-B0CFA8E7`). In SolidCraft `solid.loft`. |
| **Spirale** | – | `solid.coil` | `run(..., [solid.coil])` | Schraubenfedern und Gewindegänge (`GUID-B0CFA8E7`). In SolidCraft `solid.coil`. |
| **Rippe** | – | `solid.rib` | `run(..., [solid.rib])` | Versteifungsrippen aus offenen Konturen (`GUID-B0CFA8E7`). In SolidCraft `solid.rib`. |
| **Prägen** | – | `solid.emboss` | `run(..., [solid.emboss])` | Erhabene oder vertiefte Profile (`GUID-E6848555`). In SolidCraft `solid.emboss`. |
| **Grundkörper: Quader** | – | `solid.box` | `run(..., [solid.box])` | Direkte Quadererstellung (`GUID-B0CFA8E7`). In SolidCraft `solid.box`. |
| **Grundkörper: Zylinder** | – | `solid.cylinder` | `run(..., [solid.cylinder])` | Direkte Zylindererstellung (`GUID-B0CFA8E7`). In SolidCraft `solid.cylinder`. |
| **Grundkörper: Kugel** | – | `solid.sphere` | `run(..., [solid.sphere])` | Direkte Kugelerstellung (`GUID-401BABD2`). In SolidCraft `solid.sphere`. |
| **Grundkörper: Torus** | – | `solid.torus` | `run(..., [solid.torus])` | Direkte Toruserstellung (`GUID-401BABD2`). In SolidCraft `solid.torus`. |
| **Bohrung** | `H` | `solid.hole` | `bolted_connection` / `run` | Volle Übereinstimmung beim Kürzel `H` (`GUID-DEEB0723`, `GUID-B6A701E6`). Mechvane bietet mit `bolted_connection` einen vollautomatischen Normteil-Assistenten. |
| **Rundung** | `F` | `solid.fillet` | `run(..., [solid.fillet])` | Volle Übereinstimmung beim Kürzel `F` (`GUID-DEEB0723`, `GUID-590A8760`). Kantenverrundungen. |
| **Fase** | `CH` | `solid.chamfer` | `run(..., [solid.chamfer])` | Kantenfasen mit Alias `CH` (`GUID-DEEB0723`, `GUID-B6A701E6`). In SolidCraft `solid.chamfer`. |
| **Wandung** | – | `solid.shell` | `run(..., [solid.shell])` | Erzeugt Hohlkörper (`GUID-B6A701E6`). In SolidCraft `solid.shell`. |
| **Flächenverjüngung** | `D` | `solid.draft` | `run(..., [solid.draft])` | In Inventor im Bauteil Kürzel `D` (`GUID-DEEB0723`, `GUID-B6A701E6`). Konflikt: In SolidCraft ist `D` für Skizzenmaße reserviert. |
| **Gewinde** | – | `solid.thread` | `run(..., [solid.thread])` | Kosmetische Gewindetextur (`GUID-B6A701E6`). In SolidCraft `solid.thread`. |
| **Trennen (Körper)** | – | `solid.split_body` | `run(..., [solid.split_body])` | Teilt Festkörper durch Ebene/Fläche (`GUID-349C84EE`). In SolidCraft `solid.split_body`. |
| **Trennen (Fläche)** | – | `solid.split_face` | `run(..., [solid.split_face])` | Teilt Bauteilflächen (`GUID-349C84EE`). In SolidCraft `solid.split_face`. |
| **Kombinieren** | – | `solid.combine` | `run(..., [solid.combine])` | Boolesche Operationen Vereinigung/Differenz/Schnitt (`GUID-349C84EE`). In SolidCraft `solid.combine`. |
| **Körper verschieben** | – | `solid.move` | `run(..., [solid.move])` | Verschiebt Volumenkörper (`GUID-993A4C8C`). In SolidCraft mit Tastenkürzel `M` belegt. |
| **Fläche löschen** | – | `face.delete` | `run(..., [face.delete])` | Löscht Teilflächen und heilt Geometrie (`GUID-E9151557`). In SolidCraft `face.delete`. |
| **Arbeitsebene** | `]` | `construct.plane.offset` | `run(..., [construct.plane.*])` | Offset-, Winkel- und Mittelebenen mit Kürzel `]` (`GUID-DEEB0723`, `GUID-38A9748E`). In SolidCraft `construct.plane.*`. |
| **Arbeitsachse** | `/` | `construct.axis.through_cylinder` | `run(..., [construct.axis.*])` | Zylinder-, Kanten- und Schnittachsen mit Kürzel `/` (`GUID-DEEB0723`, `GUID-38A9748E`). In SolidCraft `construct.axis.*`. |
| **Arbeitspunkt** | `.` | `construct.point.vertex` | `run(..., [construct.point.*])` | Eck- und Mittelpunkte mit Kürzel `.` (`GUID-DEEB0723`, `GUID-38A9748E`). In SolidCraft `construct.point.*`. |
| **Fixierter Arbeitspunkt** | `;` | – | fehlt | Verankerter Raum-Arbeitspunkt mit Kürzel `;` (`GUID-DEEB0723`). In SolidCraft kein direkter Befehl vorhanden. |
| **Benutzerkoordinatensystem (BKS)** | – | `joint.origin` | fehlt | Definiert lokales Koordinatensystem (`GUID-38A9748E`). In SolidCraft als `joint.origin` für Gelenkanker realisiert. |
| **Rechteckige Anordnung** | `RP` | `solid.pattern.rectangular` | `run(..., [solid.pattern.rectangular])` | Lineare Feature- und Körperanordnung mit Kürzel `RP` (`GUID-DEEB0723`, `GUID-9B3D1B72`). |
| **Runde Anordnung** | – | `solid.pattern.circular` | `run(..., [solid.pattern.circular])` | Kreisanordnung um Achse (`GUID-9B3D1B72`). In SolidCraft `solid.pattern.circular`. |
| **Spiegeln** | `MI` | `solid.mirror` | `run(..., [solid.mirror])` | Spiegelt Features an Arbeitsebene mit Kürzel `MI` (`GUID-DEEB0723`, `GUID-9B3D1B72`). |
| **Füllfläche (Patch)** | – | `surface.patch` | `run(..., [surface.patch])` | Schließt Öffnungen mit getrimmter Fläche (`GUID-5A8568DF`). In SolidCraft `surface.patch`. |
| **Heften (Stitch)** | – | `surface.stitch` | `run(..., [surface.stitch])` | Verbindet Flächenkörper zu Volumenkörper (`GUID-5A8568DF`). In SolidCraft `surface.stitch`. |
| **Regelfläche** | – | `surface.ruled` | `run(..., [surface.ruled])` | Erzeugt Regelflächen an Kanten (`GUID-5A8568DF`). In SolidCraft `surface.ruled`. |
| **Fläche stutzen** | – | `surface.trim` | `run(..., [surface.trim])` | Trimmt Flächen an Schnittkurven (`GUID-7661F5F8`). In SolidCraft `surface.trim`. |
| **Fläche dehnen** | – | `surface.extend` | `run(..., [surface.extend])` | Verlängert Flächenkanten tangential (`GUID-7661F5F8`). In SolidCraft `surface.extend`. |
| **Fläche ersetzen** | – | `solid.replace_face` | `run(..., [solid.replace_face])` | Tauscht Körperflächen gegen Hilfsfläche aus (`GUID-E9151557`). In SolidCraft `solid.replace_face`. |

---

### 1.3 Register „Zusammenfügen“ (Baugruppe / Assembly Environment)

| Inventor-Begriff/-Befehl | Inventor-Kürzel | SolidCraft-Befehl (ID) | Mechvane-Entsprechung | Bemerkung / Einordnung |
| :--- | :---: | :--- | :--- | :--- |
| **Komponente platzieren** | `P` | `component.insert_design` | `insert_part` | Bindet Bauteildatei assoziativ ein mit Kürzel `P` (`GUID-DEEB0723`, `GUID-2C55B507`). In Mechvane: `insert_part(assembly, part_path, name, translate, rotate, grounded)`. |
| **Aus Inhaltscenter platzieren** | – | `parts.fastener` / `parts.library` | `standard_part` | Fügt Normteile ein. Mechvane bietet `standard_part(norm, size, length)` mit validiertem Offline-Katalog (`katalog/`). |
| **Komponente erstellen** | `N` | `component.create` | `new_part` / `edit_in_place` | Erzeugt neues In-Place-Bauteil mit Kürzel `N` (`GUID-DEEB0723`, `GUID-FBBE5A60`). In Mechvane über `new_part` und Top-Down-Workflow. |
| **Komponente ersetzen** | – | `component.relink` | fehlt | Tauscht referenzierte Datei gegen Version/Gleichteil aus. In SolidCraft `component.relink`. |
| **Freie Verschiebung** | `M` | `occurrence.move` | fehlt | Zieht Komponente temporär im Raum mit Kürzel `M` (`GUID-DEEB0723`, `GUID-9796C22B`). In SolidCraft `occurrence.move`. |
| **Freie Drehung** | `RO` | `occurrence.move` | fehlt | Dreht Komponente um ihren lokalen Schwerpunkt mit Kürzel `RO` (`GUID-DEEB0723`, `GUID-7EAE9DFD`). |
| **Fixiert (Grounded)** | – | `occurrence.ground` | `insert_part(..., grounded=True)` | Entfernt alle 6 Freiheitsgrade der Basiskomponente. In Mechvane Parameter beim Platzieren. |
| **Abhängig machen (Passend)** | `Alt+Ziehen` | `joint.create` | `add_joint` | Positioniert Flächen aufeinander (`GUID-DEEB0723`, `GUID-EBD2C784`). In SolidCraft/Mechvane über `joint.create` (Typ `rigid`/Relation `point_on_plane`). |
| **Abhängig machen (Fluchtend)** | – | `joint.create` | `add_joint` | Flächennormalen gleichgerichtet (`GUID-EBD2C784`). In SolidCraft/Mechvane über `joint.create` mit invertierter Ausrichtung (`flip=true`). |
| **Abhängig machen (Winkel)** | – | `joint.create` | `add_joint` | Fester oder variabler Winkel zwischen Kanten/Flächen (`GUID-EBD2C784`). In SolidCraft über Relation `angle`. |
| **Abhängig machen (Tangential)**| – | `joint.create` | `add_joint` | Berührung zylindrischer Flächen (`GUID-EBD2C784`). In SolidCraft an zylindrischen Ursprüngen. |
| **Abhängig machen (Einfügen)** | – | `joint.create` | `add_joint` | Koaxialität und Anschlagfläche in einem Schritt (`GUID-EBD2C784`). In SolidCraft/Mechvane als `type: "rigid"` oder `"cylindrical"`. |
| **Zusammenfügen (Assemble)** | – | `joint.create` | `add_joint` | Grafische Mini-Werkzeugleiste für Schnellverknüpfungen (`GUID-198F05E4`: *„Ein kleiner Werkzeugkasten wird im Grafikfenster anstelle eines Dialogfelds angezeigt“*). |
| **Verbindung: Starr** | – | `joint.create` | `add_joint(type="rigid")` | Sperrt alle 6 Freiheitsgrade (`GUID-6AA68E8F`). Mechvane speichert Geometrieanker zur automatischen Reparatur. |
| **Verbindung: Drehung** | – | `joint.create` | `add_joint(type="revolute")`| 1 rotatorischer Freiheitsgrad (`GUID-6AA68E8F`). In SolidCraft und Mechvane `type: "revolute"`. |
| **Verbindung: Schieben** | – | `joint.create` | `add_joint(type="slider")` | 1 translatorischer Freiheitsgrad (`GUID-6AA68E8F`). In SolidCraft und Mechvane `type: "slider"`. |
| **Verbindung: Zylindrisch** | – | `joint.create` | `add_joint(type="cylindrical")`| 1 Translation + 1 Rotation koaxial (`GUID-6AA68E8F`). In SolidCraft und Mechvane `type: "cylindrical"`. |
| **Verbindung: Planar** | – | `joint.create` | `add_joint(type="planar")` | 2 Translationen + 1 Rotation auf Ebene (`GUID-6AA68E8F`). In SolidCraft und Mechvane `type: "planar"`. |
| **Verbindung: Kugel** | – | `joint.create` | `add_joint(type="ball")` | 3 rotatorische Freiheitsgrade um Punkt (`GUID-6AA68E8F`). In SolidCraft und Mechvane `type: "ball"`. |
| **Baugruppen-Anordnung** | – | `solid.pattern.rectangular` | `bolted_connection(..., pattern=...)` | Multipliziert Komponenten linear (`GUID-CF627358`). In Mechvane in den Schraubenassistenten integriert. |
| **Baugruppen-Spiegeln** | `MI` | `solid.mirror` | fehlt | Spiegelt Komponenten an Baugruppenebene mit Kürzel `MI` (`GUID-DEEB0723`, `GUID-C5B3D3DF`). |
| **Stückliste (BOM)** | – | `assembly.bom` | fehlt | Strukturierte Teileliste (`GUID-6C58657F`). In SolidCraft `assembly.bom`. |
| **Verknüpfungen aktualisieren** | – | `component.update_links` | `update_links(assembly, repair=True)` | Aktualisiert externe Bauteile. Mechvane repariert automatisch gewanderte Gelenkanker (`links.py`). |
| **Kollision analysieren** | – | `inspect.interference` | `check_design` | Prüft Überschneidungen (`GUID-80DED0A6`). In Mechvane analysiert `check_design` Fertigungsregeln. |
| **Messen** | – | – | `measure(document)` | Liefert Volumen, Fläche, Schwerpunkt und Bounding Box (Weltkoordinaten in Baugruppen). |

---

## 2. Standard-Tastenkürzel von Inventor

Autodesk Inventor besitzt eine durchgängige Tastaturbelegung aus Einzelbuchstaben, alphanumerischen 2-Zeichen-Befehlsaliasen, Funktionstasten und Navigationskürzeln. Die folgende Tabelle fasst die wichtigsten Standard-Tastenkürzel gemäß den offiziellen Referenzen (`GUID-DEEB0723`, `GUID-428B9A8E`) zusammen und stellt sie SolidCraft und Mechvane gegenüber.

| Kürzel Inventor | Befehl in Inventor | Kategorie | Entsprechung SolidCraft | Entsprechung Mechvane | Konflikt / Bemerkung |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **`E`** | Extrusion | Bauteil | `solid.extrude` (`E`) | `run(..., [solid.extrude])` | **Kein Konflikt.** Volle Übereinstimmung. |
| **`R`** | Drehung (Revolve) | Bauteil | `solid.revolve` (kein Kürzel) | `run(..., [solid.revolve])` | **Konflikt:** In SolidCraft ist `R` für *2-Punkt-Rechteck* in Skizzen vergeben. Lösung: Kontexttrennung (Skizze vs. 3D-Modell). |
| **`H`** | Bohrung (Hole) | Bauteil | `solid.hole` (`H`) | `bolted_connection` / `run` | **Kein Konflikt.** Volle Übereinstimmung. |
| **`L`** | Linie | Skizze | `sketch.line` (`L`) | `run(..., [sketch.line])` | **Kein Konflikt.** Volle Übereinstimmung. |
| **`C`** | Kreis durch Mittelpunkt | Skizze | `sketch.circle.center` (`C`) | `run(..., [sketch.circle.center])` | **Kein Konflikt in Skizze.** In Baugruppen nutzt Inventor `C` für *Abhängig machen* (`Constrain`). |
| **`D`** | Allgemeine Bemaßung | Skizze | `sketch.dimension` (`D`) | `run(..., [sketch.dimension])` | **Kein Konflikt in Skizze.** Im Bauteilmodell nutzt Inventor `D` für *Flächenverjüngung* (`Face Draft`). |
| **`S`** | 2D-Skizze starten | 3D-Modell | `sketch.create` (kein Kürzel) | `run(..., [sketch.create])` | **Schwerer Konflikt:** In SolidCraft öffnet `S` fest verdrahtet die Befehlssuche (`ui.palette`). Für Inventor-Nutzer ist `S` der Standard-Skizzenstart auf einer gewählten Planarfläche. |
| **`S3`** | 3D-Skizze starten | 3D-Modell | `sketch.line3d` | fehlt | Startet 3D-Skizzierumgebung (`GUID-DEEB0723`). |
| **`F`** | Rundung (Fillet) | Bauteil | `solid.fillet` (`F`) | `run(..., [solid.fillet])` | **Kein Konflikt.** Volle Übereinstimmung. |
| **`CH`** | Fase (Chamfer) | Bauteil | `solid.chamfer` (kein Kürzel) | `run(..., [solid.chamfer])` | Alphanumerischer 2-Tasten-Befehlsalias in Inventor. |
| **`LO`** | Erhebung (Loft) | Bauteil | `solid.loft` (kein Kürzel) | `run(..., [solid.loft])` | Alphanumerischer Befehlsalias in Inventor. |
| **`SW`** | Sweeping (Sweep) | Bauteil | `solid.sweep` (kein Kürzel) | `run(..., [solid.sweep])` | Alphanumerischer Befehlsalias in Inventor. |
| **`T`** | Text | Skizze | `sketch.text` (kein Kürzel) | `run(..., [sketch.text])` | **Konflikt:** In SolidCraft ist `T` für *Stutzen* vergeben. In Inventor ist Stutzen `TR`. |
| **`TR`** | Stutzen (Trim) | Skizze | `sketch.trim` (`T`) | `run(..., [sketch.trim])` | In Inventor 2-Zeichen-Alias `TR`, in SolidCraft Einzeltaste `T`. |
| **`RP`** | Rechteckige Anordnung | Bauteil/Skizze | `solid.pattern.rectangular` | `bolted_connection` / `run` | Alphanumerischer Befehlsalias in Inventor für 2D und 3D. |
| **`CP`** | Runde Anordnung | Skizze | `sketch.pattern.circular` | `bolted_connection` / `run` | Alphanumerischer Befehlsalias in Inventor. |
| **`MI`** | Spiegeln | Bauteil/Baugruppe | `solid.mirror` (kein Kürzel) | `run(..., [solid.mirror])` | Alphanumerischer Befehlsalias in Inventor. |
| **`P`** | Komponente platzieren | Baugruppe | `component.insert_design` | `insert_part` | **Konflikt:** In SolidCraft ist `P` für *Geometrie projizieren* in Skizzen belegt. Durch Kontexttrennung (Skizze vs. Baugruppe) lösbar. |
| **`N`** | Komponente erstellen | Baugruppe | `component.create` | `new_part` | Erzeugt neues In-Place-Bauteil im Baugruppenkontext. |
| **`M`** | Freie Verschiebung | Baugruppe | `occurrence.move` | fehlt | **Konflikt:** In SolidCraft ist `M` für *Körper verschieben* (`solid.move`) belegt. |
| **`RO`** | Freie Drehung | Baugruppe | `occurrence.move` | fehlt | Alphanumerischer Befehlsalias in Baugruppen. |
| **`]`** | Arbeitsebene | 3D-Modell | `construct.plane.offset` | `run(..., [construct.plane.*])` | Standardkürzel eckige Klammer rechts `]`. |
| **`/`** | Arbeitsachse | 3D-Modell | `construct.axis.through_cylinder` | `run(..., [construct.axis.*])` | Standardkürzel Schrägstrich `/`. |
| **`.`** | Arbeitspunkt | 3D-Modell | `construct.point.vertex` | `run(..., [construct.point.*])` | Standardkürzel Punkt `.`. |
| **`;`** | Fixierter Arbeitspunkt | 3D-Modell | – | fehlt | Standardkürzel Semikolon `;`. In SolidCraft nicht vorhanden. |
| **`-`** | Abhängigkeit Horizontal | Skizze | `sketch.constraint.horizontal_vertical` | `run(...)` | Standardkürzel Bindestrich `-` (`GUID-DEEB0723`, `GUID-A85A7A30`). |
| **`Alt+V`** | Sichtbarkeit umschalten | Bauteil/Baugruppe | `browser.visibility` (`V`) | fehlt | Umschaltung der Sichtbarkeit von Körpern und Arbeitselementen (`GUID-DEEB0723`). SolidCraft nutzt Einzeltaste `V`. |
| **`Alt+Ziehen`**| Passend-Abhängigkeit | Baugruppe | `joint.create` | `add_joint` | Schnelles Vergeben von Passend-Beziehungen per Maus (`GUID-DEEB0723`). |
| **`F1`** | Hilfe | Global | – | fehlt | Hilfe zum aktiven Befehl oder Dialogfeld (`GUID-DEEB0723`). |
| **`F2`** | Pan / Umbenennen | Global | `view.tool` (Pan) / `timeline.rename` (`F2`) | fehlt | Pan im Grafikfenster; bei Klick im Browser Umbenennen des Knotens (`GUID-DEEB0723`). |
| **`F3`** | Zoom | Global | Mausrad / `view.tool` | fehlt | Dynamisches Vergrößern/Verkleinern (`GUID-DEEB0723`, `GUID-428B9A8E`). |
| **`F4`** | Drehen (Orbit) | Global | `view.navigate` | fehlt | 3D-Modell um Mittelpunkt drehen (`GUID-DEEB0723`). |
| **`F5`** | Vorherige Ansicht | Global | – | fehlt | Kehrt zur vorherigen Kameraposition zurück (`GUID-DEEB0723`). |
| **`F6`** | Isometrieansicht | Global | `view.isometric` (`Ctrl+7`) / `view.fit` (`F6`) | `screenshot(view="iso")` | **Bedeutungsunterschied:** In Inventor schaltet `F6` die isometrische Kamerapositionierung ein (`GUID-DEEB0723`). In SolidCraft ist `F6` für *Einpassen* (`view.fit`) belegt und `Ctrl+7` für `view.isometric`. |
| **`F7`** | Grafiken aufschneiden | Skizze | `inspect.section` | fehlt | Kappt Modell an Skizzierebene (`GUID-DEEB0723`). Unverzichtbarer Workflow für Innenskizzen. |
| **`F8`** | Alle Abhängigkeiten einblenden | Skizze | `sketch.glyphs` | fehlt | Blendet Skizzenabhängigkeiten ein (`GUID-DEEB0723`). |
| **`F9`** | Alle Abhängigkeiten ausblenden | Skizze | `sketch.glyphs` | fehlt | Blendet Skizzenabhängigkeiten aus (`GUID-DEEB0723`). |
| **`Ende` / `End`** | Auswahl zoomen (Zoom Selected) | Global | – | fehlt | Fokussiert das Grafikfenster formatfüllend auf das im Baum oder Grafikfenster selektierte Element. |
| **`Esc`** | Befehl beenden | Global | `select.clear` (`Escape`) | fehlt | Bricht aktiven Befehl oder Selektion ab (`GUID-DEEB0723`). |
| **`Löschen`** | Ausgewählte Objekte löschen | Global | `timeline.delete` (`Delete`) | `delete_feature` | Löscht gewählte Objekte (`GUID-428B9A8E`). Mechvane löscht verbrauchte Skizzen mit (`keep_sketch=False`). |
| **`Strg+Z`** | Rückgängig (Undo) | Global | `edit.undo` (`Ctrl+Z`) | `command(..., "edit.undo")` | Macht die letzte Aktion rückgängig (`GUID-428B9A8E`). |
| **`Strg+Y`** | Wiederherstellen (Redo) | Global | `edit.redo` (`Ctrl+Y`) | `command(..., "edit.redo")` | Stellt rückgängig gemachte Aktion wieder her (`GUID-428B9A8E`). |
| **`Strg+N`** | Neues Dokument | Global | `file.new` (`Ctrl+N`) | `new_part` / `new_assembly` | Erstellt ein neues Dokument (`GUID-428B9A8E`). |
| **`Strg+O`** | Dokument öffnen | Global | `doc.open` (`Ctrl+O`) | `open_document` | Öffnet eine vorhandene CAD-Datei (`GUID-428B9A8E`). |
| **`Strg+S`** | Dokument speichern | Global | `file.save` (`Ctrl+S`) | `save_document` | Speichert das aktive Dokument (`GUID-428B9A8E`). |

---

## 3. Browser (Modellbaum): Aufbau, Ende-des-Bauteils-Marke, Unterdrücken, Neu ordnen

Der Modellbrowser ist das zentrale Rückgrat von Autodesk Inventor. Die Architektur unterscheidet sich grundlegend von Systemen mit linearer Timeline nach Fusion-Art:

### 3.1 Aufbau der Baumhierarchie (Inventor-Feature-Baum vs. Fusion-Timeline)
- **Autodesk Inventor:** Verwendet eine strikte Eltern-Kind-Hierarchie (`GUID-36DB9904`, `GUID-69196418`). Skizzen und Arbeitselemente, die von einem Feature verbraucht werden, ordnen sich hierarchisch als Unterknoten direkt unter diesem Feature an. Unverbrauchte Skizzen liegen auf der Hauptebene. Bei Mehrfachverwendung (`Skizze wieder verwenden` / `Share sketch`) erscheint ein referenzierender Klonknoten unter dem Folgefeature.
- **SolidCraft:** Speichert die Modellhistorie im Kern als lineare Timeline (`crates/engine/src/cmd/edit.rs`) und trennt Geometrie im Browser nach Kategorien (`bodies`, `sketches`, `construction`, `joints` in `crates/engine/src/cmd/browser.rs`).
- **Mechvane:** Setzt gemäß Grundsatz 5 (*„Feature-Baum wie Inventor, keine Fusion-Timeline“*) und Grundsatz 10 auf ein transformiertes Baummodell:
  1. **Skizzenregel (`sketch_rule`):** Verbrauchte Skizzen werden über `timeline.dependents` identifiziert und im Datenmodell unmittelbar vor ihr verbrauchendes Feature sortiert.
  2. **Browser-Werkzeug (`browser(document)`):** Blendet die Fusion-Kategorieordner aus und stellt Features und deren verbrauchte Skizzen hierarchisch eingerückt dar.
  3. **Baugruppengelenke unter Komponenten:** Anstatt Gelenke in einem globalen `joints`-Ordner zu isolieren, ordnet Mechvane Verbindungen beiden beteiligten Komponenten als Unterknoten zu (`GUID-69196418`).

### 3.2 Ende-des-Bauteils-Marke (End of Part / EOP)
- **Autodesk Inventor:** Am Ende des Bauteilbaums sitzt die visuelle Trennlinie `Bauteilende` (`GUID-69196418`, `GUID-36DB9904`, `GUID-C6A19638`).
  - **Funktion:** Wird der Marker mit der Maus nach oben gezogen, werden alle darunterliegenden Elemente temporär aus dem Berechnungsmodell entfernt (Rollback). Neue Features werden an der aktuellen Position des Markers eingefügt.
  - **Kontextmenü-Befehle:**
    - `Bauteilende-Markierung verschieben`: Verschiebt den Marker unter das gewählte Feature oder in den Ursprungsordner (`GUID-36DB9904`).
    - `Bauteilende zum Anfang verschieben`: Rollt das Modell komplett auf den Ursprungszustand zurück (`GUID-36DB9904`).
    - `Bauteilende zum Ende verschieben`: Aktualisiert das Modell und rollt alle Elemente wieder vor (`GUID-69196418`, `GUID-36DB9904`).
    - `Alle Elemente unter Bauteilende löschen`: Bereinigt temporär zurückgerollte Features permanent (`GUID-36DB9904`).
- **SolidCraft-Entsprechung:** Bietet die Engine-Befehle `timeline.rollback` (`crates/engine/src/cmd/edit.rs:61`) und `timeline.roll_to` (`crates/engine/src/cmd/edit.rs:62`).
- **Mechvane-Entsprechung:** Das MCP-Werkzeug `browser()` markiert zurückgerollte Features mit `rolled_back: true`. In der geplanten Weboberfläche wird dieser Zustand als ziehbare EOP-Trennlinie gerendert.

### 3.3 Unterdrücken (Suppress) und Unterdrückung aufheben (Unsuppress)
- **Autodesk Inventor:** Per Kontextmenü können Features temporär unterdrückt werden (`GUID-36DB9904`: *„Entfernt das Element aus dem Grafikfenster. Im Browser wird es weiterhin angezeigt und durch eine graue Markierung gekennzeichnet. Wenn Sie die Unterdrückung aufheben möchten, klicken Sie mit der rechten Maustaste in den Browser, und wählen Sie Unterdrückung aufheben“*). Alle geometrisch abhängigen Kind-Elemente werden automatisch kaskadierend mitunterdrückt (`GUID-C6A19638`).
- **SolidCraft-Entsprechung:** `timeline.suppress` (`crates/engine/src/cmd/edit.rs:65`). Toggelt den Unterdrückungszustand einzelner Features, Feature-Listen oder ganzer Ordnergruppen (`groups`).
- **Mechvane-Entsprechung:** Über `command(document, "timeline.suppress", {"feature": name})` direkt ausführbar; Mechvane prüft im `browser()` den Status `suppressed: true`.

### 3.4 Neu ordnen (Reorder)
- **Autodesk Inventor:** Features können im Modellbaum per Drag-and-Drop an eine andere Stelle in der Historie gezogen werden (`GUID-EDF6B951`, `GUID-36DB9904`), sofern keine unlösbaren Eltern-Kind-Abhängigkeiten verletzt werden (z. B. ein Verrundungsfeature vor die erzeugende Extrusion zu ziehen).
- **SolidCraft-Entsprechung:**
  - `timeline.reorder` (`feature: id|name, position: number, allow_errors?: bool` in `crates/engine/src/cmd/edit.rs:64`).
  - `timeline.reorder_many` (`features: [id|name], position: number` in `crates/engine/src/cmd/edit.rs:66`).
  - `timeline.move_many` (`features?: [id|name], groups?: [ids], position: number` in `crates/engine/src/cmd/edit.rs:58`).
  - SolidCraft prüft standardmäßig (`allow_errors: false`), ob abhängige Features brechen würden, und verweigert ungültige Verschiebungen atomar.
- **Mechvane-Entsprechung:** Mechvane validiert Verschiebungen über `tree.py` und stellt sicher, dass verbrauchte Skizzen beim Verschieben ihres Features als Block mitwandern.

---

## 4. Dialoge und Interaktionskonzepte: Mini-Werkzeugleiste und Eingaben im Grafikfenster

Die Bedienphilosophie von Autodesk Inventor zeichnet sich durch minimale Mauswege und In-Canvas-Interaktion aus:

### 4.1 Mini-Werkzeugleiste (Mini-Toolbar / Mini-Werkzeugkasten)
- **Autodesk Inventor:** Mini-Werkzeugkästen sind kontextbezogene Werkzeugleisten, die im 3D-Grafikfenster unmittelbar neben dem ausgewählten Objekt oder dem Mauszeiger eingeblendet werden (`GUID-1FFC26DB`, `GUID-198F05E4`):
  - **Direkter Zugriff:** Optionen wie Abstand, Winkel, Verjüngung oder Boolesche Operationen (Vereinigung, Differenz, Schnitt) können direkt am Modell gewählt werden, ohne den Blick auf das Menüband oder einen modalen Dialog wenden zu müssen.
  - **Umschaltung & Fixierung:** Dialogfelder für Befehle wie Wandung, Fase, Flächenverjüngung oder Gelenke können wahlweise als volles Dialogfeld oder als kompakter Mini-Werkzeugkasten dargestellt werden (`GUID-1FFC26DB`: *„Es gibt einige Inventor-Dialogfelder, die über einen Mini-Werkzeugkasten verfügen, der zusätzlich zum Dialogfeld angezeigt werden kann. Die verfügbaren Optionen in diesen Mini-Werkzeugkästen sind die gleichen wie die Optionen im Dialogfeld“*). Die Leiste kann über einen Griff fixiert (*pin*) oder per *Auto-Fade* ausgeblendet werden.
  - **Befehl Zusammenfügen (Assemble):** Ersetzt den starren Abhängigkeitsdialog komplett durch eine schwebende Minileiste im Viewport (`GUID-198F05E4`: *„Ein kleiner Werkzeugkasten wird im Grafikfenster anstelle eines Dialogfelds angezeigt“*).
- **SolidCraft:** Besitzt keine nativen Mini-Werkzeugkästen im 3D-Viewport; Befehlseingaben erfolgen über modale Dialoge oder die Werkzeugleiste (`crates/ui-egui/src/toolbar.rs`).
- **Mechvane-Handlungsbedarf:** Mechvanes Web-UI („Model by hand“) benötigt eine schwebende HTML/Three.js-Minileiste direkt am selektierten 3D-Element (Kante: Rundung/Fase; Fläche: Skizze/Extrusion; Baugruppenkomponente: Gelenk/Verschraubung).

### 4.2 Eingaben im Grafikfenster / Heads-Up Display (HUD / Dynamische Eingabe)
- **Autodesk Inventor:** Beim Zeichnen von 2D-Skizzengeometrie blendet Inventor eine sogenannte *Exponierte Anzeige* (Heads-Up Display / HUD) direkt am Cursor ein (`GUID-33A8B11D`):
  - **Direkte Werteingabe:** Beim Ziehen von Linien, Kreisen oder Rechtecken erscheinen numerische Eingabefelder für Länge, Radius oder Winkel (`GUID-33A8B11D`: *„Die exponierte Anzeige ermöglicht die Eingabe von Werten in verschiebbare Werteingabefelder, die sich stets in der Nähe des Cursors befinden. Die Werte werden beim Bewegen des Cursors dynamisch aktualisiert“*).
  - **`Tab`-Taste:** Ein Druck auf die `Tab`-Taste sperrt den aktuellen Wert (Schloss-Symbol) und springt zum nächsten Eingabefeld (z. B. von Linienlänge zu Winkel; `GUID-33A8B11D`: *„Drücken Sie die TABULATORTASTE, um zum nächsten Eingabefeld zu wechseln“*).
  - **Automatische Bemaßungserzeugung:** Wird die Eingabe mit `Enter` bestätigt, erzeugt Inventor automatisch permanente parametrische Skizzenbemaßungen.
- **SolidCraft:** Unterstützt Direkteingaben während des Zeichnens nicht im Viewport.
- **Mechvane-Handlungsbedarf:** Im Skizziermodus des Mechvane-Frontends muss ein Eingabe-Overlay mit `Tab`-Wechsel und Wertesperre implementiert werden, das beim Abschluss den Befehl `sketch.draw.dimensioned` oder `sketch.dimension` aufruft.

### 4.3 Eigenschafts-Bedienfelder (Property Panels) vs. traditionelle Dialoge
- **Autodesk Inventor:** Seit Version 2019/2020 wurden modale Dialogfelder für zentrale Features (Extrusion, Drehung, Bohrung, Rundung, Sweeping usw.) durch moderne *Eigenschaftsgruppen* (`Property Panels`) abgelöst (`GUID-3E5505B9`):
  - **Top-to-Bottom-Workflow:** Die Parameter sind sequenziell von oben nach unten gegliedert. Frühere Auswahlen filtern dynamisch nachfolgende Optionen (`GUID-3E5505B9`: *„Eigenschaftsgruppen bieten kontextabhängigen Zugriff auf Parameter zum Erstellen und Bearbeiten von Elementen... Workflow - the property panel workflow is from top to bottom. Any property you set or select drives or filters the next options that display in the panel“*).
  - **Akkordeon-Struktur:** Statt unübersichtlicher Registerkarten nutzen Eigenschaftsgruppen einklappbare Parameterabschnitte (`GUID-3E5505B9`: *„Eigenschaftsgruppen verwenden Parametergruppen mit einem Akkordeon-Steuerelement anstelle von Registerkarten“*).
  - **Breadcrumbs:** Am oberen Rand des Bedienfelds zeigt eine Breadcrumb-Leiste die Position an (z. B. `Skizze1 > Extrusion1`). Durch Klick kann ohne Modusabbruch direkt in die übergeordnete Skizze gesprungen werden.
  - **Voreinstellungen (Presets):** Häufig benötigte Parametermengen (z. B. Passungsbohrungen, Standard-Blechradien) können gespeichert und mit einem Klick abgerufen werden.
- **SolidCraft:** Verwendet statische, egui-basierte Eigenschaftsfenster.
- **Mechvane-Handlungsbedarf:** Das Mechvane-Web-UI sollte das Konzept der Eigenschaftsgruppe mit Breadcrumbs und Presets übernehmen.

---

## 5. Lücken mit größtem Nutzen (Top 10)

Aus dem systematischen Abgleich ergeben sich die folgenden zehn Kernlücken mit dem größten Hebel für Mechvane, um das Bediengefühl von Autodesk Inventor nahtlos zu erreichen:

1. **Kontextsensitives Tastaturprofil „Inventor Standard“:**
   - *Problem:* Schwerer Konflikt bei der Taste `S` (Inventor = 2D-Skizze auf Fläche starten; SolidCraft = Befehlssuche `ui.palette`) sowie `R` (Inventor = Drehung; SolidCraft = Rechteck).
   - *Lösung:* Konfigurierbares Tastenprofil in Mechvane mit strikter Zustandstrennung: Im Modellmodus auf selektierter Fläche führt `S` den Skizzenstart aus; im Skizziermodus ist `R` das 2-Punkt-Rechteck, im Bauteilmodus die Drehung (`solid.revolve`).
2. **Visueller Ende-des-Bauteils-Marker (EOP-Marker):**
   - *Problem:* In SolidCraft muss Rollback abstrakt über Befehle (`timeline.rollback`, `timeline.roll_to`) ausgelöst werden; es fehlt die vertraute Drag-and-Drop-Trennlinie am Ende des Bauteilbaums.
   - *Lösung:* Im Mechvane-Browser einen interaktiven EOP-Balken einblenden, der per Maus zwischen Features gezogen werden kann und das Modell visuell zurückrollt.
3. **Direkteingabe im Grafikfenster (Heads-Up Display / Dynamic Input):**
   - *Problem:* Skizzenmaße müssen nachträglich mit `D` vergeben werden; kein Eintippen beim Zeichnen von Linien, Kreisen und Rechtecken.
   - *Lösung:* Schwebende Werteingabefelder am Cursor im Skizzen-Canvas mit `Tab`-Taste zum Umschalten/Sperren und automatischer Erzeugung von `sketch.dimension`.
4. **Mini-Werkzeugkasten im 3D-Viewport (Mini-Toolbar):**
   - *Problem:* Bei Selektion von Kanten oder Flächen müssen Befehle im Menüband oder über den Agenten gesucht werden.
   - *Lösung:* Kontextsensitive Mini-Werkzeugleiste direkt an der Selektion: Bei Kantenklick *Rundung* (`F`) und *Fase* (`CH`); bei Flächenklick *Neue Skizze* (`S`) und *Extrusion* (`E`).
5. **Universelles Bemaßungswerkzeug (`Allgemeine Bemaßung` mit Taste `D`):**
   - *Problem:* Unterschiedliche Bemaßungsarten erfordern in vielen Systemen getrennte Unterwerkzeuge.
   - *Lösung:* Wie in Inventor ermittelt das Werkzeug `sketch.dimension` (`D`) anhand der Selektion automatisch den Typ: 1 Linie = Länge; 2 Linien = Abstand oder Winkel; Kreis = Durchmesser; Bogen = Radius.
6. **Getrennte Horizontale und Vertikale Skizzen-Abhängigkeiten:**
   - *Problem:* SolidCraft fasst Horizontal und Vertikal in `sketch.constraint.horizontal_vertical` zusammen und entscheidet heuristisch nach dem aktuellen Linienwinkel. Dies führt bei leicht schrägen Linien zu Fehlern.
   - *Lösung:* Getrennte UI-Schaltflächen für *Horizontal* (mit Standardkürzel Bindestrich `-`) und *Vertikal*.
7. **Koaxiale und lineare Bohrungsplatzierung ohne vorherige Skizzenpunkte:**
   - *Problem:* `solid.hole` verlangt meist vorbereitete Skizzenpunkte. In Inventor wird eine Bohrung durch Klick auf eine Planarfläche und eine kreisförmige Referenzkante direkt koaxial platziert.
   - *Lösung:* Mechvanes `bolted_connection` bzw. Bohrungsdialog um direkte Kantenreferenzierung erweitern.
8. **Schnellverknüpfungs-Modus im Grafikfenster (Befehl `Zusammenfügen` / Assemble):**
   - *Problem:* Das Erstellen von Gelenken (`add_joint`) über Formulare ist zeitaufwendig.
   - *Lösung:* Minileiste im Baugruppen-Viewport: Klick auf Fläche 1, Klick auf Fläche 2, Sofortauswahl Passend/Fluchtend mit Abstandsoffset und Bestätigung per Häkchen.
9. **Standard-Navigationskürzel `Ende` (Auswahl zoomen / Zoom Selected):**
   - *Problem:* In großen Baugruppen verliert man leicht den Fokus auf kleine Teile; `F6` passt nur das Gesamtmodell ein.
   - *Lösung:* Tastenkürzel `Ende` (End) zentriert und zoomt die Kamera formatfüllend auf das im Baum oder Viewport selektierte Bauteil bzw. Feature.
10. **Eigenschaftsgruppe mit Breadcrumb-Navigation:**
    - *Problem:* Nach dem Aufrufen einer Extrusion ist die Skizze gesperrt; Anpassungen erfordern Abbrechen, Skizze öffnen, ändern, Skizze schließen, Extrusion erneut öffnen.
    - *Lösung:* Breadcrumbs am oberen Rand des Feature-Dialogs (`Skizze1 > Extrusion1`), um direkt in die Skizzenparameter zu springen, ohne das Feature verwerfen zu müssen.

---

## 6. Quellenbelege und wörtliche Zitate aus der Autodesk-Dokumentation

Alle Angaben zu Autodesk Inventor basieren auf den offiziellen Dokumentationen der Autodesk-Hilfe (`help.autodesk.com`, Version 2025):

### Beleg: Autodesk Inventor Tastaturkurzbefehle Referenz (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „Definieren Sie benutzerdefinierte Tastaturkurzbefehle und Befehls-Aliasnamen. Befehlsaliasse sind alphanumerische Zeichen oder Zeichenfolgen, mit denen Befehle ausgeführt werden können.“
* **Verifizierte Tastaturkürzel im Quelltext:**
  * Hilfe: `F1` („Hilfe für den aktiven Befehl oder das aktive Dialogfeld.“)
  * Pan: `F2` („Schwenkt das Grafikfenster.“)
  * Knoten umbenennen: `F2` („Aktiviert die Knotenumbenennungsfunktion im Modell-Browser“)
  * Zoom: `F3` („Vergrößert oder verkleinert die Darstellung im Grafikfenster.“)
  * Drehen: `F4` („Dreht Objekte im Grafikfenster.“)
  * Vorherige Ansicht: `F5` („Kehrt zur vorherigen Ansicht zurück.“)
  * Isometrieansicht: `F6` („Zeigt die Isometrieansicht des Modells an.“)
  * Grafiken aufschneiden: `F7` („Kappt einen Teil des Modells, um die Skizzierebene anzuzeigen.“)
  * Alle Abhängigkeiten einblenden: `F8` („Zeigt alle Abhängigkeiten an.“)
  * Alle Abhängigkeiten ausblenden: `F9` („Blendet alle Abhängigkeiten aus.“)
  * Beenden: `Esc` („Beendet einen Befehl“)
  * Kreis durch Mittelpunkt: `C` („Erstellt einen Kreis.“)
  * Fasen: `CH` („Erstellt eine Fase.“)
  * Runde Anordnung (2D-Skizze): `CP` („Erstellt eine runde Anordnung der Skizziergeometrie.“)
  * Allgemeine Bemaßung: `D` („Aktiviert den Befehl Allgemeine Bemaßung.“)
  * Flächenverjüngung: `D` („Erstellt eine Flächenverjüngung/Verjüngung.“)
  * Extrusion: `E` („Aktiviert den Befehl Extrusion.“)
  * Rundung: `F` („Erstellt eine Rundung.“)
  * Bohrung: `H` („Aktiviert den Befehl Bohrung.“)
  * Linie: `L` („Aktiviert den Befehl Linie.“)
  * Erhebung: `LO` („Erstellt ein erhabenes Element.“)
  * Spiegeln: `MI` („Erstellt ein gespiegeltes Element.“)
  * Komponente erstellen: `N` („Aktiviert den Befehl Komponente erstellen.“)
  * Komponente platzieren: `P` („Aktiviert den Befehl Komponente platzieren.“)
  * Drehung: `R` („Aktiviert den Befehl Drehung.“)
  * Freie Drehung: `RO` („Aktiviert den Befehl Komponente drehen.“)
  * Rechteckige Anordnung: `RP` („Erstellt eine rechteckige Anordnung der Element- oder Skizziergeometrie.“)
  * 2D-Skizze: `S` („Aktiviert den Befehl 2D-Skizze.“)
  * 3D-Skizze: `S3` („Aktiviert den Befehl 3D-Skizze.“)
  * Sweeping: `SW` („Erstellt ein Sweeping-Element.“)
  * Text: `T` („Aktiviert den Befehl Text.“)
  * Stutzen: `TR` („Aktiviert den Befehl Stutzen.“)
  * Arbeitsebene: `]` („Erstellt eine Arbeitsebene.“)
  * Arbeitsachse: `/` („Erstellt eine Arbeitsachse.“)
  * Arbeitspunkt: `.` („Erstellt einen Arbeitspunkt.“)
  * Fixierter Arbeitspunkt: `;` („Erstellt einen fixierten Arbeitspunkt.“)
  * Abhängigkeit Horizontal: `-` („Startet den Befehl Abhängigkeit Horizontal.“)
  * Sichtbarkeit: `Alt+V` („Aktiviert bzw. deaktiviert die Sichtbarkeit von ausgewählten Volumenkörpern und Arbeitselementen (Ebenen, Achsen, Punkte).“)
  * Passend / Spline-Formpunkte: `Alt + Ziehen mit der Maus` („Wendet in Baugruppen die Abhängigkeit Passend an. Verschiebt in einer Skizze Spline-Formpunkte.“)

### Beleg: Vordefinierte Befehlsaliasnamen und Windows-Tastaturkurzbefehle (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „Es folgen einige der in Inventor definierten Tastaturkurzbefehle und Befehlsaliasnamen.“
* **Verifizierte Kurzbefehle:**
  * Löschen: `Löschen` („Löscht ausgewählte Objekte“)
  * Rückgängig: `Strg+Z` („Entfernt bei aktivem Befehl Linie das zuletzt skizzierte Segment.“)
  * Wiederherstellen: `Strg+Y` („Aktiviert den Befehl Wiederherstellen (hebt den letzten Befehl Rückgängig auf).“)
  * Dokument speichern: `Strg+S` („Speichert das aktive Dokument“)
  * Neues Dokument: `Strg+N` („Erstellt ein Dokument“)
  * Dokument öffnen: `Strg+O` („Öffnet ein neues Dokument“)
  * Beenden: `Esc` („Beendet einen Befehl“)
  * Isometrieansicht: `F6` („Isometrieansicht.“)
  * Zoom: `F3` („Vergrößert oder verkleinert im Grafikfenster.“)

### Beleg: 2D- und 3D-Skizzen im Menüband starten und beenden (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E96FB3C4-136B-4551-BF45-F54594543ECB.htm
* **Wörtliches Zitat:** „Klicken Sie auf der Registerkarte 3D-Modell auf 2D-Skizze starten oder 3D-Skizze starten .“
* **Weiteres Zitat:** „Zum Beenden einer 2D-Skizze klicken Sie auf der Registerkarte Skizze auf Skizze beenden“

### Beleg: Menüband 3D-Modell Gruppen Erstellen und Grundkörper (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B0CFA8E7-D3F5-48A9-BE6F-C8DF668301BD.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte 3D-Modell Gruppe Erstellen Extrusion .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Grundkörper **Quader** oder Registerkarte 3D-Modell Gruppe Grundkörper **Zylinder** .“

### Beleg: Platzierte Elemente im Bauteil-Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B6A701E6-AFEB-4272-9EFC-EDC156FB8A59.htm
* **Wörtliches Zitat:** „Platzierte Elemente sind häufig verwendete Konstruktionselemente, für die bei der Erstellung in Autodesk Inventor keine Skizze erforderlich ist.“
* **Weiteres Zitat:** „Die Befehle für platzierte Elemente (Rundung, Fase, Bohrung, Gewinde, Flächenverjüngung und Wandung) befinden sich auf den Registerkarten Skizze und 3D-Modell:“

### Beleg: Menüband 3D-Modell Gruppe Ändern Rundung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-590A8760-FFBB-41C8-8169-6B7002207884.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Rundung .“

### Beleg: Menüband 3D-Modell Gruppe Arbeitselemente (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-38A9748E-FA2D-44D3-928C-DFE1326A9385.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte 3D-Modell Gruppe Arbeitselemente .“
* **Weiteres Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte 3D-Modell Gruppe Arbeitselemente Fixierter Punkt .“

### Beleg: Anordnungen im 3D-Modell Gruppe Anordnung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-9B3D1B72-340A-4F3E-9AD1-80E6DDD91ED2.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Anordnung Rechteckige Anordnung .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Anordnung Runde Anordnung .“
* **Weiteres Zitat:** „Klicken Sie in einer Bauteildatei auf Registerkarte 3D-Modell Gruppe Anordnung Spiegeln .“

### Beleg: Registerkarte Skizze Gruppe Erstellen Geometrie (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-D489CE6D-7299-4211-A43A-F3580A4BA357.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Ellipse .“
* **Weiteres Zitat:** „Das Werkzeug Polygon erstellt Polygone mit bis zu 120 Seiten.“
* **Weiteres Zitat:** „Das Werkzeug Rundung erstellt am Schnittpunkt von zwei ausgewählten Linien gerundete Ecken“
* **Weiteres Zitat:** „Das Werkzeug Fase erstellt am Schnittpunkt von zwei nicht parallelen Linien eine abgeschrägte Ecke.“

### Beleg: Allgemeine Bemaßung in der Skizzierumgebung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-5E25D5FB-3B94-44A0-AD50-80EF06F5A24F.htm
* **Wörtliches Zitat:** „Der Befehl Allgemeine Bemaßung erstellt eine lineare Bemaßung, wenn Sie ein oder zwei Elemente auswählen, eine Durchmesserbemaßung, wenn Sie einen Kreis auswählen, und eine Radiusbemaßung, wenn Sie einen Bogen auswählen.“

### Beleg: Geometrische Abhängigkeiten und Horizontal-Kürzel (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A85A7A30-7D81-4C75-8769-CAD034EEA930.htm
* **Wörtliches Zitat:** „Zum Starten des Befehls Abhängigkeit Horizontal drücken Sie den Bindestrich (Vorgabe-Tastaturkurzbefehl für den Befehl Horizontal) auf der Tastatur.“

### Beleg: Komponente platzieren Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-2C55B507-C204-4AD7-8804-BA9461306616.htm
* **Wörtliches Zitat:** „Sie können Komponenten in Inventor- oder anderen CAD-Formaten in einer Baugruppe platzieren.“
* **Weiteres Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte Zusammenfügen Gruppe Komponente Platzieren .“

### Beleg: Abhängigkeit platzieren und Zusammenfügen Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-198F05E4-2973-4818-8F25-A0B8B9796D07.htm
* **Wörtliches Zitat:** „Ein kleiner Werkzeugkasten wird im Grafikfenster anstelle eines Dialogfelds angezeigt.“
* **Weiteres Zitat:** „Baugruppenabhängigkeiten entfernen Freiheitsgrade zwischen zwei ausgewählten Komponenten und positionieren die Komponenten relativ zueinander.“

### Beleg: Erstellen von Gelenken Gelenktypen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-6AA68E8F-7C97-4806-8483-3941DE915E70.htm
* **Wörtliches Zitat:** „Baugruppengelenke positionieren Komponenten und definieren den Freiheitsgrad vollständig.“
* **Weiteres Zitat:** „Multifunktionsleiste: Registerkarte Zusammenfügen Gruppe Beziehungen Gelenk“

### Beleg: Modellbrowser Bauteilende EOP (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-69196418-14DF-4128-B4F3-581FFC994C78.htm
* **Wörtliches Zitat:** „Suchen Sie unten im Browser das Symbol Bauteilende (oder Element), und ziehen Sie es nach oben, um das Modell in ein früheres Stadium zurückzusetzen.“
* **Weiteres Zitat:** „Klicken Sie mit der rechten Maustaste auf ein Element im Browser, und wählen Sie Bauteilende-Markierung verschieben, um die Bauteilende-Markierung zu diesem Element zu verschieben.“
* **Weiteres Zitat:** „Hierdurch werden die Elemente unterhalb des Bauteilende-Symbols vorübergehend aus dem Modell entfernt.“
* **Weiteres Zitat:** „Um das Modell zu aktualisieren, ziehen Sie das Symbol im Browser wieder nach unten oder klicken mit der rechten Maustaste auf die Bauteilende-Markierung und wählen Bauteilende zum Ende verschieben.“

### Beleg: Bauteil-Browser Referenz und Kontextmenü (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-36DB9904-6DD2-45A4-856A-A843D75C83A1.htm
* **Wörtliches Zitat:** „Entfernt das Element aus dem Grafikfenster. Im Browser wird es weiterhin angezeigt und durch eine graue Markierung gekennzeichnet. Wenn Sie die Unterdrückung aufheben möchten, klicken Sie mit der rechten Maustaste in den Browser, und wählen Sie Unterdrückung aufheben.“
* **Weiteres Zitat:** „Bauteilende-Markierung verschieben Verschiebt die Bauteilende-Markierung unter das ausgewählte Element oder in den Ordner Ursprung.“
* **Weiteres Zitat:** „Bauteilende zum Anfang verschieben Wenn sich der Bauteilende-Indikator innerhalb der Bauteilelemente befindet, wird die Anzeige des Bauteilendes im Browser direkt an den Anfang der Elemente verschoben.“
* **Weiteres Zitat:** „Bauteilende zum Ende verschieben Wenn sich der Bauteilende-Indikator innerhalb der Bauteilelemente befindet, wird die Anzeige des Bauteilendes im Browser direkt an das Ende der Elemente verschoben.“
* **Weiteres Zitat:** „Alle Elemente unter Bauteilende löschen Löscht alle im Browser unterhalb dieser Markierung aufgeführten Elemente.“
* **Weiteres Zitat:** „Skizze wieder verwenden Wählt eine Skizze aus, die bereits in einem Element verwendet wird, und nutzt diese in einem neuen Element. Platziert eine Kopie der Skizze im Browser.“

### Beleg: Löschen und Unterdrücken von Elementen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-C6A19638-C241-4E35-92D5-6C8D3D78B1C6.htm
* **Wörtliches Zitat:** „Sie können Elemente unter die Markierung Bauteilende ziehen, um sie vorübergehend aus der Bearbeitung auszuschließen.“

### Beleg: 2D-Geometrie der dynamischen Eingabe zeichnen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-33A8B11D-A04C-4809-BC82-C0419215915F.htm
* **Wörtliches Zitat:** „Die exponierte Anzeige ermöglicht die Eingabe von Werten in verschiebbare Werteingabefelder, die sich stets in der Nähe des Cursors befinden. Die Werte werden beim Bewegen des Cursors dynamisch aktualisiert.“
* **Weiteres Zitat:** „Drücken Sie die TABULATORTASTE, um zum nächsten Eingabefeld zu wechseln.“

### Beleg: So blenden Sie die Mini-Werkzeugkästen ein oder aus (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-1FFC26DB-1410-422F-8629-9E11D46868DA.htm
* **Wörtliches Zitat:** „Es gibt einige Inventor-Dialogfelder, die über einen Mini-Werkzeugkasten verfügen, der zusätzlich zum Dialogfeld angezeigt werden kann. Die verfügbaren Optionen in diesen Mini-Werkzeugkästen sind die gleichen wie die Optionen im Dialogfeld.“
* **Weiteres Zitat:** „Sie können wählen, ob die Mini-Werkzeugkästen angezeigt oder ausgeblendet werden sollen, wenn Sie die folgenden Befehle aufrufen: Wandung, Flächenverjüngung, Fase und Gelenk.“

### Beleg: Eigenschaftsgruppen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-3E5505B9-9F60-43A0-BF32-97D183B91A70.htm
* **Wörtliches Zitat:** „Eigenschaftsgruppen bieten kontextabhängigen Zugriff auf Parameter zum Erstellen und Bearbeiten von Elementen.“
* **Weiteres Zitat:** „Eigenschaftsgruppen verwenden Parametergruppen mit einem Akkordeon-Steuerelement anstelle von Registerkarten.“
