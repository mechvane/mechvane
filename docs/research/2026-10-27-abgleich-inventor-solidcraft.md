# Abgleichliste: Autodesk Inventor-Menüband und Tastenkürzel ↔ SolidCraft

- **Datum:** 2026-10-27
- **Autor:** Gemini 3.8 Flash, Nacharbeit Gemini 4 Argon (Issue #2)
- **Status:** Verifiziert mit `tools/check_sources.py` und gegen `/root/repos/_ext/solidcraft` (`4afd9333`)
- **Prüfvermerk 2026-10-27 (Claude):** `check_sources.py` 56/56 Zitate, 51/51 Zahlen; alle 107 SolidCraft-Zeilenangaben gegen `9cba66c1` nachgeprüft (Befehls-ID steht an der genannten Stelle). Als „unbelegt“ markierte Kürzel und Gruppen (31 Stellen) vor Entscheidungen selbst prüfen.
- **Kontext & Ziel:** Grundlage für die Abgleichliste Inventor ↔ SolidCraft ↔ Mechvane gemäß ROADMAP (Grundsatz 10: *„Bedienung am Ende möglichst nah an Inventor. Wer Inventor kennt, soll ohne Umlernen arbeiten können. Gemeint sind Aufbau und Begriffe der Oberfläche... Optisch aber dunkler und schicker als Inventor“*).

---

## 1. Einleitung und Architekturvergleich

Im Rahmen der UI-Konzeption von Mechvane (Grundsatz 10) soll die Bedienung des CAD-Systems für Anwender von **Autodesk Inventor** ohne kognitiven Bruch möglich sein. Während SolidCraft im Kern ein modernes, an Fusion 360 angelehntes Modellierungskonzept mit deklarativen Befehlen (`CommandSpec`) bereitstellt, besitzt Inventor eine historisch gewachsene, präzise strukturierte Menüband-Architektur (Ribbon) mit getrennten Arbeitsumgebungen für Bauteile (`.ipt`), Baugruppen (`.iam`), Zeichnungen (`.idw`/`.dwg`) und Präsentationen (`.ipn`).

### Struktur des Inventor-Bauteil-Menübands
Im Bauteilmodus (`Part Environment`) unterscheidet Inventor strikt zwischen zwei Hauptmodi:
1. **Modellierungsmodus (Register „3D-Modell“ / `3D Model`):**  
   Enthält Befehle zur Erzeugung und Bearbeitung dreidimensionaler Körper in den belegten Gruppen *Erstellen* (`Create`), *Grundkörper* (`Primitives`), *Ändern* (`Modify`), *Arbeitselemente* (`Work Features`), *Anordnung* (`Pattern`) und *Fläche* (`Surface`).
2. **Skizziermodus (Register „Skizze“ / `Sketch`):**  
   Wird beim Erstellen oder Bearbeiten einer 2D-Skizze auf einer Planarfläche oder Arbeitsebene aktiv. Das Menüband schaltet um auf Skizzenwerkzeuge in den belegten Gruppen *Erstellen* (`Create`), *Ändern* (`Modify`), *Anordnung* (`Pattern`), *Abhängig machen* (`Constrain`) und *Format* (`Format`).

### SolidCraft-Befehlssystem und Tastaturmodell
SolidCraft organisiert Befehle über statische Tabellen von `CommandSpec`-Strukturen im Modul `crates/engine/src/cmd/` (z. B. `features.rs`, `features_more.rs`, `sketch.rs`, `sketch_create.rs`, `sketch_modify.rs`, `sketch_constraints.rs`, `sketch_project.rs`, `construct.rs`, `surface.rs`, `view_navigation.rs`, `edit.rs`, `file.rs`). Die Oberfläche (`crates/ui-egui/`) blendet Befehle über eine Werkzeugleiste (`crates/ui-egui/src/toolbar.rs`) ein. Tastenkürzel werden entweder deklarativ über `CommandSpec::key(...)` zugewiesen oder global in `crates/ui-egui/src/toolbar.rs` (Funktionstasten wie `F2`, `F6`, Tasten wie `S`, `V`, `Delete`, `Escape`) bzw. `crates/ui-egui/src/keymap.rs` abgefangen.

---

## 2. Abgleichstabelle: Bauteil-Menüband und Tastenkürzel

Die folgende Tabelle stellt alle Befehle des Inventor-Bauteil-Menübands (Register „3D-Modell“ und „Skizze“) sowie die offiziellen Standard-Tastenkürzel aus der Autodesk-Hilfe (`help.autodesk.com`) den entsprechenden SolidCraft-Befehlen und deren exakten Dateipfaden samt Zeilennummern gegenüber. Menüband-Gruppen oder Tastenkürzel, für die in den abgerufenen Seiten von `help.autodesk.com` kein wörtliches Zitat vorliegt, sind explizit mit `(unbelegt)` gekennzeichnet; nicht im SolidCraft-Engine-Kern vorhandene Befehle sind mit `nicht gefunden` markiert.

| Register | Gruppe | Inventor (de) | Inventor (en) | Kürzel Inventor | SolidCraft-Befehl | Kürzel SolidCraft | Bemerkung |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **3D-Modell** | Skizze (unbelegt) | 2D-Skizze starten | Start 2D Sketch | `S` | `sketch.create` | – | In Inventor startet `S` eine 2D-Skizze (`GUID-DEEB0723`, `GUID-E96FB3C4`). In SolidCraft öffnet `S` die Befehlssuche (`ui.palette` in `crates/ui-egui/src/toolbar.rs:2150`). Befehl definiert in `crates/engine/src/cmd/sketch.rs:35`. |
| **3D-Modell** | Skizze (unbelegt) | 3D-Skizze starten | Start 3D Sketch | `S3` | `sketch.line3d` | – | In Inventor startet `S3` die 3D-Skizze (`GUID-DEEB0723`, `GUID-E96FB3C4`). SolidCraft bietet 3D-Skizzenlinien über `sketch.line3d` in `crates/engine/src/cmd/sketch_3d.rs:16`. |
| **3D-Modell** | Erstellen | Extrusion | Extrude | `E` | `solid.extrude` | `E` | Volle Übereinstimmung in Funktion und Tastenkürzel `E` (`GUID-DEEB0723`, `GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features.rs:22`. |
| **3D-Modell** | Erstellen | Drehung | Revolve | `R` | `solid.revolve` | – | Konflikt: In Inventor startet `R` die Drehung (`GUID-DEEB0723`, `GUID-B0CFA8E7`). In SolidCraft ist `R` für 2-Punkt-Rechtecke in Skizzen vergeben. Definiert in `crates/engine/src/cmd/features.rs:29`. |
| **3D-Modell** | Erstellen | Sweeping | Sweep | `SW` | `solid.sweep` | – | Sweep entlang Leitkurven (`GUID-DEEB0723`, `GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features.rs:33`. |
| **3D-Modell** | Erstellen | Erhebung | Loft | `LO` | `solid.loft` | – | Übergang zwischen mehreren Querschnitten (`GUID-DEEB0723`, `GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features.rs:37`. |
| **3D-Modell** | Erstellen | Spirale | Coil | – | `solid.coil` | – | Schraubenfedern und Gewindewendeln (`GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features_more.rs:21`. |
| **3D-Modell** | Erstellen | Rippe | Rib | – | `solid.rib` | – | Versteifungsrippen und Stege (`GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features_more.rs:27`. |
| **3D-Modell** | Erstellen | Steg (unbelegt) | Web (unbelegt) | – | `solid.web` | – | In Inventor im Befehl *Rippe* integriert; in SolidCraft eigener Befehl `solid.web` in `crates/engine/src/cmd/features_more.rs:31`. |
| **3D-Modell** | Erstellen | Prägen | Emboss | – | `solid.emboss` | – | Erhabene oder vertiefte Profile auf Flächen (`GUID-E6848555`). Definiert in `crates/engine/src/cmd/features_more.rs:35`. |
| **3D-Modell** | Grundkörper | Quader | Box | – | `solid.box` | – | Direkte Quadererzeugung in Gruppe *Grundkörper* / *Primitives* (`GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features.rs:38`. |
| **3D-Modell** | Grundkörper | Zylinder | Cylinder | – | `solid.cylinder` | – | Direkte Zylindererzeugung in Gruppe *Grundkörper* (`GUID-B0CFA8E7`). Definiert in `crates/engine/src/cmd/features.rs:44`. |
| **3D-Modell** | Grundkörper | Kugel | Sphere | – | `solid.sphere` | – | Kugel-Grundkörper in Gruppe *Grundkörper* (`GUID-401BABD2`). Definiert in `crates/engine/src/cmd/features.rs:45`. |
| **3D-Modell** | Grundkörper | Torus | Torus | – | `solid.torus` | – | Torus-Grundkörper in Gruppe *Grundkörper* (`GUID-401BABD2`). Definiert in `crates/engine/src/cmd/features.rs:46`. |
| **3D-Modell** | Ändern | Bohrung | Hole | `H` | `solid.hole` | `H` | Volle Übereinstimmung bei Kürzel `H` (`GUID-DEEB0723`, `GUID-B6A701E6`). Definiert in `crates/engine/src/cmd/features.rs:68`. |
| **3D-Modell** | Ändern | Rundung | Fillet | `F` | `solid.fillet` | `F` | Volle Übereinstimmung bei Kürzel `F` (`GUID-DEEB0723`, `GUID-590A8760`). Definiert in `crates/engine/src/cmd/features.rs:48`. |
| **3D-Modell** | Ändern | Fase | Chamfer | `CH` | `solid.chamfer` | – | Kantenfasen (`GUID-DEEB0723`, `GUID-B6A701E6`). Definiert in `crates/engine/src/cmd/features.rs:53`. |
| **3D-Modell** | Ändern | Wandung | Shell | – | `solid.shell` | – | Hohlkörper mit definierter Wandstärke (`GUID-B6A701E6`). Definiert in `crates/engine/src/cmd/features.rs:97`. |
| **3D-Modell** | Ändern | Flächenverjüngung | Face Draft | `D` | `solid.draft` | – | In Inventor im Bauteil Kürzel `D` (`GUID-DEEB0723`, `GUID-B6A701E6`). In SolidCraft ist `D` für Skizzenbemaßung belegt. Definiert in `crates/engine/src/cmd/features.rs:101`. |
| **3D-Modell** | Ändern | Gewinde | Thread | – | `solid.thread` | – | Gewindeelemente auf zylindrischen Flächen (`GUID-B6A701E6`). Definiert in `crates/engine/src/cmd/features.rs:93`. |
| **3D-Modell** | Ändern | Verdickung/Versatz | Thicken/Offset | – | `surface.thicken` | – | In Inventor in Gruppe *Ändern* (`GUID-A9A4FF6E`). Macht aus Flächen Festkörper mit Dicke. Definiert in `crates/engine/src/cmd/surface.rs:27`. |
| **3D-Modell** | Ändern | Trennen (Körper) | Split | – | `solid.split_body` | – | Trennt Volumenkörper in Gruppe *Ändern* (`GUID-349C84EE`). Definiert in `crates/engine/src/cmd/features.rs:119`. |
| **3D-Modell** | Ändern | Trennen (Fläche) | Split | – | `solid.split_face` | – | Trennt Bauteilflächen in Gruppe *Ändern* (`GUID-349C84EE`). Definiert in `crates/engine/src/cmd/features.rs:113`. |
| **3D-Modell** | Ändern | Kombinieren | Combine | – | `solid.combine` | – | Boolesche Operationen in Gruppe *Ändern* (`GUID-349C84EE`). Definiert in `crates/engine/src/cmd/features.rs:54`. |
| **3D-Modell** | Ändern | Körper verschieben | Move Bodies | – | `solid.move` | `M` | In Inventor in Gruppe *Ändern* ohne Standardkürzel (`GUID-993A4C8C`); `M` ist in Inventor für *Komponente verschieben* in Baugruppen belegt (`GUID-DEEB0723`). In SolidCraft `M` in `crates/engine/src/cmd/features.rs:128`. |
| **3D-Modell** | Ändern | Fläche löschen | Delete Face | – | `face.delete` | – | Löscht Flächen in Gruppe *Ändern* (`GUID-E9151557`). Definiert in `crates/engine/src/cmd/features.rs:85`. |
| **3D-Modell** | Ändern | Drücken/Ziehen (unbelegt) | Press Pull (unbelegt) | – | `solid.press_pull` | `Q` | Kein Inventor-Befehl (Fusion-Konzept mit `Q`; in Inventor ist `Q` für *iMate erstellen* belegt, `GUID-DEEB0723`). Definiert in `crates/engine/src/cmd/features.rs:123`. |
| **3D-Modell** | Ändern | Bauteil skalieren (unbelegt) | Scale (unbelegt) | – | `solid.scale` | – | In Inventor über *Abgeleitete Komponente* oder *Direktbearbeitung*; in SolidCraft eigener Befehl in `crates/engine/src/cmd/features.rs:81`. |
| **3D-Modell** | Ändern | Ausrichten (unbelegt) | Align (unbelegt) | – | `solid.align` | – | Kein eigener Bauteil-Ribbon-Befehl in Inventor; in SolidCraft definiert in `crates/engine/src/cmd/features_more.rs:43`. |
| **3D-Modell** | Arbeitselemente | Arbeitsebene | Workplane | `]` | `construct.plane.offset` | – | In Inventor Standardkürzel `]` (`GUID-DEEB0723`, `GUID-38A9748E`). In SolidCraft definiert in `crates/engine/src/cmd/features.rs:105` (weitere Ebenen wie `construct.plane.midplane` in `crates/engine/src/cmd/construct.rs:67`). |
| **3D-Modell** | Arbeitselemente | Arbeitsachse | Work Axis | `/` | `construct.axis.through_cylinder` | – | In Inventor Standardkürzel `/` (`GUID-DEEB0723`, `GUID-38A9748E`). In SolidCraft definiert in `crates/engine/src/cmd/construct.rs:23`. |
| **3D-Modell** | Arbeitselemente | Arbeitspunkt | Work Point | `.` | `construct.point.vertex` | – | In Inventor Standardkürzel `.` (`GUID-DEEB0723`, `GUID-38A9748E`). In SolidCraft definiert in `crates/engine/src/cmd/construct.rs:43`. |
| **3D-Modell** | Arbeitselemente | Fixierter Arbeitspunkt | Grounded Work Point | `;` | – (nicht gefunden) | – | In Inventor verankerter Arbeitspunkt mit Kürzel `;` (`GUID-DEEB0723`). Kein entsprechender Befehl in SolidCraft (nicht gefunden). |
| **3D-Modell** | Arbeitselemente | BKS (unbelegt) | UCS (unbelegt) | – | `joint.origin` | – | Benutzerkoordinatensystem in Gruppe *Arbeitselemente* (Gruppe belegt in `GUID-38A9748E`, Befehl `BKS` unbelegt). In SolidCraft als `joint.origin` definiert in `crates/engine/src/cmd/joints.rs:22`. |
| **3D-Modell** | Anordnung | Rechteckige Anordnung | Rectangular Pattern | `RP` | `solid.pattern.rectangular` | – | Rasteranordnung mit Kürzel `RP` für Bauteil und 2D-Skizze (`GUID-DEEB0723`, `GUID-9B3D1B72`). Definiert in `crates/engine/src/cmd/features.rs:55`. |
| **3D-Modell** | Anordnung | Runde Anordnung | Circular Pattern | `CP (unbelegt)` | `solid.pattern.circular` | – | Befehl in Gruppe *Anordnung* belegt (`GUID-9B3D1B72`), das Kürzel `CP` ist in `GUID-DEEB0723` jedoch nur für die Kategorie *2D-Skizze* dokumentiert (für 3D-Modell daher `unbelegt`). Definiert in `crates/engine/src/cmd/features.rs:59`. |
| **3D-Modell** | Anordnung | Pfadanordnung (unbelegt) | Pattern on Path (unbelegt) | – | `solid.pattern.path` | – | In Inventor Option innerhalb der rechteckigen Anordnung; in SolidCraft eigener Befehl in `crates/engine/src/cmd/features.rs:63`. |
| **3D-Modell** | Anordnung | Spiegeln | Mirror | `MI` | `solid.mirror` | – | Spiegeln von Bauteil-Elementen mit Kürzel `MI` (`GUID-DEEB0723`, `GUID-9B3D1B72`). Definiert in `crates/engine/src/cmd/features.rs:67`. |
| **3D-Modell** | Fläche | Füllfläche | Patch | – | `surface.patch` | – | Begrenzte Fläche in Gruppe *Fläche* / *Surface* (`GUID-5A8568DF`). Definiert in `crates/engine/src/cmd/surface.rs:19` (zusätzlich `surface.boundary` in `crates/engine/src/cmd/surface_boundary.rs:29`). |
| **3D-Modell** | Fläche | Heften | Stitch | – | `surface.stitch` | – | Verbindet Flächenkörper in Gruppe *Fläche* (`GUID-5A8568DF`). Definiert in `crates/engine/src/cmd/surface.rs:23`. |
| **3D-Modell** | Fläche | Regelfläche | Ruled Surface | – | `surface.ruled` | – | Erzeugt Regelflächen in Gruppe *Fläche* (`GUID-5A8568DF`). Definiert in `crates/engine/src/cmd/surface.rs:59`. |
| **3D-Modell** | Fläche | Stutzen | Trim | – | `surface.trim` | – | Stutzt Flächen in Gruppe *Fläche* (`GUID-7661F5F8`). Definiert in `crates/engine/src/cmd/surface.rs:35`. |
| **3D-Modell** | Fläche | Dehnen | Extend | – | `surface.extend` | – | Dehnt Flächen in Gruppe *Fläche* (`GUID-7661F5F8`). Definiert in `crates/engine/src/cmd/surface.rs:31`. |
| **3D-Modell** | Fläche | Fläche ersetzen | Replace Face | – | `solid.replace_face` | – | Ersetzt Körperflächen durch Arbeits- oder Flächengeometrie in Gruppe *Fläche* (`GUID-E9151557`). Definiert in `crates/engine/src/cmd/features_more.rs:39`. |
| **Skizze** | Erstellen | Linie | Line | `L` | `sketch.line` | `L` | Volle Übereinstimmung bei Funktion und Kürzel `L` (`GUID-DEEB0723`). Definiert in `crates/engine/src/cmd/sketch.rs:46`. |
| **Skizze** | Erstellen | Kreis durch Mittelpunkt | Center Point Circle | `C` | `sketch.circle.center` | `C` | Volle Übereinstimmung bei Funktion und Kürzel `C` (`GUID-DEEB0723`). Definiert in `crates/engine/src/cmd/sketch.rs:76`. |
| **Skizze** | Erstellen | Kreis tangential | Tangent Circle | – | `sketch.circle.two_tangent` | – | Tangentialer Kreis (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch_create.rs:38`. |
| **Skizze** | Erstellen | Bogen durch drei Punkte | Three Point Arc | – | `sketch.arc.three_point` | – | Bogen über drei Punkte (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch.rs:96`. |
| **Skizze** | Erstellen | Bogen durch Mittelpunkt | Center Point Arc | – | `sketch.arc.center_point` | – | Bogen über Mittelpunkt (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch.rs:97`. |
| **Skizze** | Erstellen | Bogen tangential | Tangent Arc | – | `sketch.arc.tangent` | – | Tangentialer Bogen (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch_create.rs:34`. |
| **Skizze** | Erstellen | Rechteck durch 2 Punkte | Two Point Rectangle | – | `sketch.rectangle.two_point` | `R` | In Gruppe *Erstellen* (`GUID-D489CE6D`) ohne Inventor-Kürzel. In SolidCraft mit Kürzel `R` definiert in `crates/engine/src/cmd/sketch.rs:55`. |
| **Skizze** | Erstellen | Rechteck durch 3 Punkte | Three Point Rectangle | – | `sketch.rectangle.three_point` | – | Rechteck über drei Punkte (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch.rs:61`. |
| **Skizze** | Erstellen | Rechteck durch Mittelpunkt | Center Point Rectangle | – | `sketch.rectangle.center` | – | Rechteck aus Mittelpunkt (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch.rs:71`. |
| **Skizze** | Erstellen | Langloch | Slot | – | `sketch.slot.center_to_center` | – | Langloch von Mitte zu Mitte (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch.rs:117`. |
| **Skizze** | Erstellen | Polygon | Polygon | – | `sketch.polygon.inscribed` | – | Regelmäßiges Vieleck in Gruppe *Erstellen* (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch.rs:102`. |
| **Skizze** | Erstellen | Spline (Interpolation) | Spline Interpolation | – | `sketch.spline.fit_point` | – | Interpolations-Spline (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch_create.rs:67`. |
| **Skizze** | Erstellen | Spline (Steuerrahmen) | Spline Control Vertex | – | `sketch.spline.control_point` | – | Kontrollpunkt-Spline (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch_create.rs:72`. |
| **Skizze** | Erstellen | Punkt | Point | – | `sketch.point` | – | Skizzenpunkt / Mittelpunkt (`GUID-D4A4288F`). Definiert in `crates/engine/src/cmd/sketch.rs:127`. |
| **Skizze** | Erstellen | Text | Text | `T` | `sketch.text` | – | Konflikt: In Inventor `T` für Text (`GUID-DEEB0723`). In SolidCraft ist `T` für Stutzen belegt; `sketch.text` ist definiert in `crates/engine/src/cmd/sketch_create.rs:103`. |
| **Skizze** | Erstellen | Ellipse | Ellipse | – | `sketch.ellipse` | – | Ellipse in Gruppe *Erstellen* (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch_create.rs:63`. |
| **Skizze** | Erstellen | Rundung (Skizze) | Fillet | `F (unbelegt)` | `sketch.fillet` | – | In Inventor in Register *Skizze* Gruppe *Erstellen* (`GUID-D489CE6D`); Kürzel `F` ist in `GUID-DEEB0723` nur für *Bauteil/Baugruppe* belegt (für Skizze daher `unbelegt`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:22`. |
| **Skizze** | Erstellen | Fase (Skizze) | Chamfer | – | `sketch.chamfer.equal_distance` | – | In Inventor in Register *Skizze* Gruppe *Erstellen* (`GUID-D489CE6D`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:27`. |
| **Skizze** | Erstellen | Geometrie projizieren | Project Geometry | – | `sketch.project` | `P` | In Inventor in Register *Skizze* Gruppe *Erstellen* (`GUID-B8D8B07B`); `P` ist in Inventor für *Komponente platzieren* in Baugruppen belegt (`GUID-DEEB0723`). In SolidCraft mit `P` definiert in `crates/engine/src/cmd/sketch_project.rs:23`. |
| **Skizze** | Erstellen | Schnittkanten projizieren | Project Cut Edges | – | `sketch.intersect` | – | In Inventor in Register *Skizze* Gruppe *Erstellen* (`GUID-B8D8B07B`). Definiert in `crates/engine/src/cmd/sketch_project.rs:24`. |
| **Skizze** | Ändern | Versatz | Offset | `O (unbelegt)` | `sketch.offset` | `O` | In Inventor in Gruppe *Ändern* (`GUID-962CEE71`), Kürzel `O` jedoch nicht in `GUID-DEEB0723` / `GUID-428B9A8E` aufgeführt (`unbelegt`). In SolidCraft mit `O` definiert in `crates/engine/src/cmd/sketch_modify.rs:42`. |
| **Skizze** | Ändern | Stutzen | Trim | `TR` | `sketch.trim` | `T` | In Inventor 2-Zeichen-Alias `TR` (`GUID-DEEB0723`, `GUID-DD00037F`). In SolidCraft Einzeltaste `T` in `crates/engine/src/cmd/sketch_modify.rs:56`. |
| **Skizze** | Ändern | Dehnen | Extend | – | `sketch.extend` | – | Dehnt Kurven in Gruppe *Ändern* (`GUID-DD00037F`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:69`. |
| **Skizze** | Ändern | Teilen | Split | – | `sketch.break` | – | Teilt Kurven in Gruppe *Ändern* (`GUID-DD00037F`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:74`. |
| **Skizze** | Ändern | Verschieben | Move | – | `sketch.move` | – | Verschiebt Skizzengeometrie in Gruppe *Ändern* (`GUID-F8114270`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:90`. |
| **Skizze** | Ändern | Drehen | Rotate | – | `sketch.transform` | `G` | Dreht Skizzengeometrie in Gruppe *Ändern* (`GUID-F8114270`). In SolidCraft über `sketch.transform` (Verschieben/Drehen/Skalieren, Taste `G`) in `crates/engine/src/cmd/sketch_modify.rs:84`. |
| **Skizze** | Ändern | Skalieren | Scale | – | `sketch.scale` | – | Skaliert Skizzengeometrie in Gruppe *Ändern* (`GUID-962CEE71`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:79`. |
| **Skizze** | Anordnung | Rechteckig | Rectangular | `RP` | `sketch.pattern.rectangular` | – | Rechteckige Skizzenanordnung in Gruppe *Anordnung* (`GUID-AAD3A699`) mit Kürzel `RP` (`GUID-DEEB0723`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:105`. |
| **Skizze** | Anordnung | Kreisförmig | Circular | `CP` | `sketch.pattern.circular` | – | Runde Skizzenanordnung in Gruppe *Anordnung* (`GUID-AAD3A699`) mit Kürzel `CP` (`GUID-DEEB0723`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:100`. |
| **Skizze** | Anordnung | Spiegeln | Mirror | `MI (unbelegt)` | `sketch.mirror` | – | Befehl in Gruppe *Anordnung* belegt (`GUID-AAD3A699`), Kürzel `MI` in `GUID-DEEB0723` jedoch nur für *Bauteil/Baugruppe* dokumentiert (`unbelegt`). Definiert in `crates/engine/src/cmd/sketch_modify.rs:95`. |
| **Skizze** | Abhängig machen | Allgemeine Bemaßung | General Dimension | `D` | `sketch.dimension` | `D` | Volle Übereinstimmung beim Kürzel `D` in Gruppe *Abhängig machen* / *Constrain* (`GUID-DEEB0723`, `GUID-026FE8D3`, `GUID-5E25D5FB`). Definiert in `crates/engine/src/cmd/sketch.rs:128`. |
| **Skizze** | Abhängig machen | Koinzident | Coincident | – | `sketch.constraint.coincident` | – | Punkt-auf-Punkt-/Kurven-Bindung (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:136`. |
| **Skizze** | Abhängig machen | Kollinear | Collinear | – | `sketch.constraint.collinear` | – | Linien auf gemeinsame Fluchtlinie legen (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:176`. |
| **Skizze** | Abhängig machen | Konzentrisch | Concentric | – | `sketch.constraint.concentric` | – | Gleicher Mittelpunkt für Kreise/Bögen (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:171`. |
| **Skizze** | Abhängig machen | Festgelegt | Fix | – | `sketch.constraint.fix` | – | Fixiert Punkte und Kurven im Raum (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:161`. |
| **Skizze** | Abhängig machen | Parallel | Parallel | – | `sketch.constraint.parallel` | – | Parallele Ausrichtung zweier Linien (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:151`. |
| **Skizze** | Abhängig machen | Lotrecht | Perpendicular | – | `sketch.constraint.perpendicular` | – | Rechtwinklige Ausrichtung zweier Kurven (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:156`. |
| **Skizze** | Abhängig machen | Horizontal | Horizontal Constraint | `-` | `sketch.constraint.horizontal_vertical` | – | In Inventor Standardkürzel Bindestrich `-` (`GUID-DEEB0723`, `GUID-A85A7A30`). In SolidCraft kombiniert als `sketch.constraint.horizontal_vertical` in `crates/engine/src/cmd/sketch.rs:131`. |
| **Skizze** | Abhängig machen | Vertikal | Vertical Constraint | – | – (nicht gefunden) | – | In Inventor eigene Abhängigkeit (`GUID-A85A7A30`). In SolidCraft keine separate Befehls-ID (nicht gefunden; gemeinsam innerhalb von `sketch.constraint.horizontal_vertical` in `crates/engine/src/cmd/sketch.rs` behandelt). |
| **Skizze** | Abhängig machen | Tangential | Tangent | – | `sketch.constraint.tangent` | – | Tangentialer Übergang (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:141`. |
| **Skizze** | Abhängig machen | Stetig (G2) | Smooth (G2) | – | `sketch.constraint.curvature` | – | Krümmungsstetige Bedingung für Splines (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch_constraints.rs:14`. |
| **Skizze** | Abhängig machen | Symmetrisch | Symmetric | – | `sketch.constraint.symmetry` | – | Symmetrie bezüglich einer Mittellinie (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:181`. |
| **Skizze** | Abhängig machen | Gleich | Equal | – | `sketch.constraint.equal` | – | Gleiche Länge oder gleicher Radius (`GUID-A85A7A30`). Definiert in `crates/engine/src/cmd/sketch.rs:146`. |
| **Skizze** | Abhängig machen | Alle Abhängigkeiten einblenden | Show All Constraints | `F8` | `sketch.glyphs` | – | Zeigt alle Abhängigkeiten an (`GUID-DEEB0723`). In SolidCraft als Umschalter `sketch.glyphs` definiert in `crates/engine/src/cmd/sketch_constraints.rs:47`. |
| **Skizze** | Abhängig machen | Alle Abhängigkeiten ausblenden | Hide All Constraints | `F9` | – (nicht gefunden) | – | Blendet alle Abhängigkeiten aus (`GUID-DEEB0723`). Kein separater Ausblenden-Befehl in SolidCraft (nicht gefunden; Umschaltung erfolgt über `sketch.glyphs` bzw. `show_constraints` in `crates/ui-egui/src/sketch_palette.rs`). |
| **Skizze** | Format | Konstruktion | Construction | – | `sketch.construction` | `X` | In Inventor in Register *Skizze* Gruppe *Format* (`GUID-F5A5790A`). SolidCraft nutzt Kürzel `X` in `crates/engine/src/cmd/sketch.rs:186`. |
| **Skizze** | Format | Mittellinie | Centerline | – | `sketch.centerline` | – | In Inventor in Gruppe *Format* (`GUID-D4A4288F`). Definiert in `crates/engine/src/cmd/sketch_create.rs:95`. |
| **Skizze** | Format | Getriebene Bemaßung | Driven Dimension | – | `sketch.toggle_driven` | – | In Inventor in Register *Skizze* Gruppe *Format* (`GUID-026FE8D3`). Definiert in `crates/engine/src/cmd/sketch_constraints.rs:44`. |
| **Skizze** | Beenden (unbelegt) | Skizze beenden | Finish Sketch | – | `sketch.finish` | `Escape` | Befehl auf Registerkarte *Skizze* belegt (`GUID-E96FB3C4`), Gruppenname unbelegt. In SolidCraft definiert in `crates/engine/src/cmd/sketch.rs:40` (UI-Doppel-Escape in `crates/ui-egui/src/toolbar.rs:2126`). |
| **Global** | Navigation (unbelegt) | Isometrieansicht | Isometric View | `F6` | `view.fit` | `F6` | In Inventor zeigt `F6` die Isometrieansicht (`GUID-DEEB0723`, Kategorie *Global*). In SolidCraft ist `F6` für *Fit to Window* (`view.fit`) in `crates/engine/src/cmd/view_navigation.rs:10` (UI in `crates/ui-egui/src/toolbar.rs:2160`) und `Ctrl+7` für `view.isometric` in `crates/engine/src/cmd/view_navigation.rs:52` vergeben. |
| **Global** | Navigation (unbelegt) | Grafiken aufschneiden | Slice Graphics | `F7` | `inspect.section` | – | Kappt Modell an Skizzierebene (`GUID-DEEB0723`, Kategorie *Skizze*). In SolidCraft Schnittanalyse `inspect.section` in `crates/engine/src/cmd/section.rs:12` (sowie `slice` in `crates/ui-egui/src/sketch_palette.rs:33`). |
| **Global** | Navigation (unbelegt) | Pan | Pan | `F2` | `view.tool` | – | Schwenkt das Grafikfenster (`GUID-DEEB0723`, Kategorie *Global*). In SolidCraft über `view.tool` (Modus `"pan"`) in `crates/engine/src/cmd/view_navigation.rs:14`. |
| **Global** | Navigation (unbelegt) | Zoom | Zoom | `F3` | – (nicht gefunden) | – | Vergrößert/verkleinert im Grafikfenster (`GUID-DEEB0723`, Kategorie *Global*). Keine separate `view.zoom`-Befehls-ID in SolidCraft (nicht gefunden; über Mausrad in `crates/ui-egui/src/viewport.rs` gesteuert). |
| **Global** | Navigation (unbelegt) | Drehen | Rotate | `F4` | `view.navigate` | – | Dreht Objekte im Grafikfenster (`GUID-DEEB0723`, Kategorie *Global*). In SolidCraft Kameranavigation `view.navigate` in `crates/engine/src/cmd/view_navigation.rs:36`. |
| **Global** | Navigation (unbelegt) | Vorherige Ansicht | Previous View | `F5` | – (nicht gefunden) | – | Kehrt zur vorherigen Ansicht zurück (`GUID-DEEB0723`, Kategorie *Global*). Nicht gefunden in SolidCraft. |
| **Global** | System (unbelegt) | Hilfe | Help | `F1` | – (nicht gefunden) | – | Hilfe für aktiven Befehl oder Dialogfeld (`GUID-DEEB0723`, Kategorie *Global*). Keine `CommandSpec`-ID im Engine-Kern (nicht gefunden; Hilfe-Menü in `crates/ui-egui/src/help.rs`). |
| **Global** | System (unbelegt) | Umbenennen | Rename | `F2` | `timeline.rename` | `F2` | Knotenumbenennung im Modell-Browser (`GUID-DEEB0723`, Kategorie *Global*). In SolidCraft `timeline.rename` in `crates/engine/src/cmd/edit.rs:29` (UI-Taste `Key::F2` in `crates/ui-egui/src/toolbar.rs:2156`). |
| **Global** | System (unbelegt) | Beenden | Quit | `Esc` | `select.clear` | `Escape` | Beendet aktiven Befehl (`GUID-DEEB0723`, Kategorie *Global*). In SolidCraft `select.clear` in `crates/engine/src/cmd/edit.rs:74` (UI-Taste `Key::Escape` in `crates/ui-egui/src/toolbar.rs:2101`). |
| **Global** | System (unbelegt) | Löschen | Delete | `Löschen` | `timeline.delete` | `Delete` | Löscht ausgewählte Objekte (`GUID-428B9A8E`: „Löscht ausgewählte Objekte“ / „Deletes selected objects.“; in `GUID-DEEB0723` DEU fehlerhaft als „Löscht das ausgewählte Projekt.“ übersetzt). In SolidCraft `timeline.delete` in `crates/engine/src/cmd/edit.rs:24` (UI in `crates/ui-egui/src/toolbar.rs:2162`) sowie `selection.delete` in `crates/engine/src/cmd/delete.rs:15`. |
| **Global** | System (unbelegt) | Rückgängig | Undo | `Strg+Z` | `edit.undo` | `Ctrl+Z` | Macht letzten Befehl rückgängig (`GUID-428B9A8E`, `GUID-DEEB0723`). In SolidCraft `edit.undo` in `crates/engine/src/cmd/edit.rs:13` (UI in `crates/ui-egui/src/toolbar.rs:2081`). |
| **Global** | System (unbelegt) | Wiederherstellen | Redo | `Strg+Y` | `edit.redo` | `Ctrl+Y` | Stellt letzten Befehl wieder her (`GUID-428B9A8E`, `GUID-DEEB0723`). In SolidCraft `edit.redo` in `crates/engine/src/cmd/edit.rs:14` (UI in `crates/ui-egui/src/toolbar.rs:2086`). |
| **Global** | System (unbelegt) | Neues Dokument | Create Document | `Strg+N` | `file.new` | `Ctrl+N` | Erstellt ein Dokument (`GUID-428B9A8E`). In SolidCraft `file.new` in `crates/engine/src/cmd/file.rs:25` (UI in `crates/ui-egui/src/toolbar.rs:2071`). |
| **Global** | System (unbelegt) | Dokument öffnen | Open Document | `Strg+O` | `doc.open` | `Ctrl+O` | Öffnet ein Dokument (`GUID-428B9A8E`). In SolidCraft `doc.open` in `crates/engine/src/cmd/file.rs:26` (UI in `crates/ui-egui/src/toolbar.rs:2073`). |
| **Global** | System (unbelegt) | Dokument speichern | Save Document | `Strg+S` | `file.save` | `Ctrl+S` | Speichert das aktive Dokument (`GUID-428B9A8E`). In SolidCraft `file.save` in `crates/engine/src/cmd/file.rs:39` (UI in `crates/ui-egui/src/toolbar.rs:2092`). |
| **Global** | System (unbelegt) | Volumenkörper und Arbeitselemente | Solids and work features | `Alt+V` | `browser.visibility` | `V` | Schaltet Sichtbarkeit von Volumenkörpern und Arbeitselementen um (`GUID-DEEB0723`). In SolidCraft `browser.visibility` in `crates/engine/src/cmd/browser.rs:45` (UI-Taste `Key::V` in `crates/ui-egui/src/toolbar.rs:2152`). |
| **Global** | System (unbelegt) | Befehl wiederholen (unbelegt) | Repeat Last Command (unbelegt) | `Leertaste (unbelegt)` | – (nicht gefunden) | `Shift+R` | In `GUID-DEEB0723` und `GUID-428B9A8E` nicht als Kürzel für *Befehl wiederholen* belegt (`unbelegt`). In SolidCraft keine `CommandSpec`-ID im Engine-Kern (nicht gefunden; als `repeat_last` in `crates/ui-egui/src/lib.rs` mit `REPEAT_KEY` `Shift+R` in `crates/ui-egui/src/keymap.rs` und `crates/ui-egui/src/toolbar.rs` implementiert). |

---

## 3. Zentrale Handlungsfelder für Mechvane (Grundsatz 10)

Aus dem Vergleich ergeben sich konkrete Handlungsfelder für die Realisierung der Inventor-nahen Oberfläche in Mechvane:

1. **Auflösung der schwerwiegenden Tastaturkürzel-Kollisionen:**
   - **Taste `S`:** Für Inventor-Konstrukteure ist `S` der reflexartige Tastendruck, um eine Skizze auf einer gewählten Fläche zu beginnen (`GUID-DEEB0723`). In SolidCraft ist `S` fest für die schwebende Befehlssuche (`ui.palette` in `crates/ui-egui/src/toolbar.rs:2150`) verdrahtet. Empfehlung für Mechvane: Konfigurierbares Tastenprofil (*„Inventor Standard“* vs. *„Fusion Standard“*), sodass `S` im Inventor-Profil auf einer selektierten Fläche `sketch.create` ausführt.
   - **Taste `R`:** In Inventor für *Drehung* (`solid.revolve`), in SolidCraft für *2-Punkt-Rechteck* (`sketch.rectangle.two_point`). Da Drehung ein 3D-Befehl und Rechteck ein Skizzenbefehl ist, kann dieser Konflikt über strikte Kontexttrennung (in aktiver Skizze vs. im Bauteilmodell) gelöst werden.
   - **Taste `T` / `TR`:** In Inventor ist `T` *Text* und `TR` *Stutzen*. SolidCraft nutzt `T` für *Stutzen*.
   - **Taste `D`:** In Inventor im Bauteil *Flächenverjüngung* (`Face Draft`), in Skizzen *Allgemeine Bemaßung*. SolidCraft unterstützt `D` nur in Skizzen.

2. **Menüband-Strukturierung (Ribbon-Nachbildung):**
   - SolidCraft verwendet feste Arbeitsbereiche (`SOLID`, `SKETCH`, `SURFACE`, `SHEET METAL`).
   - Für Mechvane soll gemäß Grundsatz 10 die Ribbon-Struktur aus Inventor mit den in der Autodesk-Hilfe belegten Gruppen (*Erstellen*, *Grundkörper*, *Ändern*, *Arbeitselemente*, *Anordnung*, *Fläche*, *Abhängig machen*, *Format*) angeboten werden.

3. **Funktionstasten und Navigationsabgleich:**
   - `F6` ist in beiden Systemen vorhanden, fokussiert jedoch in Inventor auf die Isometrieansicht (`GUID-DEEB0723`), während SolidCraft das Modell einpasst (`view.fit`, `crates/engine/src/cmd/view_navigation.rs:10`). Mechvane sollte bei `F6` die isometrische Kamerapositionierung (`view.isometric`, `crates/engine/src/cmd/view_navigation.rs:52`) anfahren.
   - `F7` (Grafiken aufschneiden) ist ein Kern-Workflow in Inventor, um das Bauteil temporär an der aktuellen Skizzierebene freizuschneiden. In SolidCraft existiert sowohl `inspect.section` (`crates/engine/src/cmd/section.rs:12`) als auch die Skizzenoption `slice` (`crates/ui-egui/src/sketch_palette.rs:33`), der das Kürzel `F7` direkt zugewiesen werden sollte.

---

## 4. Quellenbelege und wörtliche Zitate aus der Autodesk-Dokumentation

### Beleg: Autodesk Inventor Tastaturkurzbefehle Referenz (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „Definieren Sie benutzerdefinierte Tastaturkurzbefehle und Befehls-Aliasnamen. Befehlsaliasse sind alphanumerische Zeichen oder Zeichenfolgen, mit denen Befehle ausgeführt werden können.“
* **Verifizierte Befehlskürzel im Quelltext:**
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
  * Wiederherstellen: `Strg+Y` („Aktiviert den Befehl Wiederherstellen (hebt den letzten Befehl Rückgängig auf).“)
  * Rückgängig: `Strg+Z` („Entfernt bei aktivem Befehl Linie das zuletzt skizzierte Segment.“)
  * Kreis durch Mittelpunkt: `C` („Erstellt einen Kreis.“)
  * Fasen: `CH` („Erstellt eine Fase.“)
  * Runde Anordnung (Kategorie 2D-Skizze): `CP` („Erstellt eine runde Anordnung der Skizziergeometrie.“)
  * Allgemeine Bemaßung: `D` („Aktiviert den Befehl Allgemeine Bemaßung.“)
  * Flächenverjüngung: `D` („Erstellt eine Flächenverjüngung/Verjüngung.“)
  * Extrusion: `E` („Aktiviert den Befehl Extrusion.“)
  * Rundung (Kategorie Bauteil/Baugruppe): `F` („Erstellt eine Rundung.“)
  * Bohrung: `H` („Aktiviert den Befehl Bohrung.“)
  * Linie: `L` („Aktiviert den Befehl Linie.“)
  * Erhebung: `LO` („Erstellt ein erhabenes Element.“)
  * Spiegeln (Kategorie Bauteil/Baugruppe): `MI` („Erstellt ein gespiegeltes Element.“)
  * Drehung: `R` („Aktiviert den Befehl Drehung.“)
  * Rechteckige Anordnung (Kategorie Bauteil/2D-Skizze): `RP` („Erstellt eine rechteckige Anordnung der Element- oder Skizziergeometrie.“)
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
  * Sichtbarkeit: `ALT+V` („Aktiviert bzw. deaktiviert die Sichtbarkeit von ausgewählten Volumenkörpern und Arbeitselementen (Ebenen, Achsen, Punkte).“)

### Beleg: Autodesk Inventor Keyboard Shortcut Reference (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „Define custom shortcut keys and command aliases. A command alias is an alphanumeric character or character sequence that can be used to start a command.“
* **Verifizierte Befehlskürzel im Quelltext:**
  * Help: `F1` („Help for the active command or dialog box.“)
  * Pan: `F2` („Pans the graphics window.“)
  * Rename: `F2` („Enables node renaming capability in model browser“)
  * Zoom: `F3` („Zooms in or out in the graphics window.“)
  * Rotate: `F4` („Rotates objects in the graphics window.“)
  * Previous View: `F5` („Returns to the previous view.“)
  * Isometric View: `F6` („Display the isometric view of the model.“)
  * Slice Graphics: `F7` („Partially slice away the model to reveal the sketch plane.“)
  * Show All Constraints: `F8` („Display all constraints.“)
  * Hide All Constraints: `F9` („Hide All Constraints.“)
  * Quit: `Esc` („Quits a command.“)
  * Delete: `Delete` („Deletes selected objects.“)
  * Redo: `Ctrl + Y` („Activates Redo (revokes the last Undo).“)
  * Undo: `Ctrl + Z` („In the active Line command, removes the last sketched segment.“)
  * Center point circle: `C` („To draw a circle.“)
  * Chamfer: `CH` („Create a chamfer“)
  * Circular Pattern (Category 2D Sketch): `CP` („Creates circular pattern of sketch geometry.“)
  * General Dimension: `D` („Activates the General Dimension command.“)
  * Face Draft: `D` („Creates a face draft / taper.“)
  * Extrude: `E` („Activates the Extrude command.“)
  * Fillet (Category Part /Assembly): `F` („Creates a fillet.“)
  * Hole: `H` („Activates the Hole command.“)
  * Line: `L` („Activates the Line command“)
  * Loft: `LO` („Creates a loft feature.“)
  * Mirror (Category Part /Assembly): `MI` („Creates a mirror feature.“)
  * Revolve: `R` („Activates the Revolve command.“)
  * Rectangular Pattern (Category Part /2D Sketch): `RP` („Creates rectangular pattern of feature or sketch geometry.“)
  * 2D Sketch: `S` („Activates the 2D Sketch command.“)
  * 3D Sketch: `S3` („Activates the 3D Sketch command.“)
  * Sweep: `SW` („Creates a sweep feature.“)
  * Text: `T` („Activates the Text command.“)
  * Trim: `TR` („Activates the Trim command.“)
  * Workplane: `]` („Creates a workplane.“)
  * Work Axis: `/` („Creates a work axis.“)
  * Work Point: `.` („Creates a work point.“)
  * Grounded Work Point: `;` („Creates a grounded work point.“)
  * Horizontal Constraint: `-` („Starts the Horizontal Constraint command“)
  * Solids and work features: `Alt+V` („Toggles visibility of selected solids, work features (planes, axis, points) on and off.“)

### Beleg: Vordefinierte Befehlsaliasnamen und Windows-Tastaturkurzbefehle (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „Es folgen einige der in Inventor definierten Tastaturkurzbefehle und Befehlsaliasnamen.“
* **Verifizierte Befehlskürzel im Quelltext:**
  * Neues Dokument (`STRG+N`): „Erstellt ein Dokument“
  * Dokument öffnen (`STRG+O`): „Öffnet ein neues Dokument“
  * Dokument speichern (`STRG+S`): „Speichert das aktive Dokument“
  * Wiederherstellen (`STRG+Y`): „Stellt den letzten Befehl wieder her“
  * Rückgängig (`STRG+Z`): „Macht den letzten Befehl rückgängig“
  * Löschen (`Löschen`): „Löscht ausgewählte Objekte“

### Beleg: Predefined Command Aliases and Windows Shortcuts (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „The following are some of the shortcuts and command aliases predefined in Inventor.“
* **Verifizierte Befehlskürzel im Quelltext:**
  * New (`Ctrl+N`): „Create a document.“
  * Open (`Ctrl+O`): „Open a new document.“
  * Save (`Ctrl+S`): „Save the active document.“
  * Delete (`Delete`): „Deletes selected objects.“
  * Undo (`Ctrl+Z`): „Activates Undo (revokes the last action).“

### Beleg: 2D- und 3D-Skizzen im Menüband starten und beenden (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E96FB3C4-136B-4551-BF45-F54594543ECB.htm
* **Wörtliches Zitat:** „Klicken Sie auf der Registerkarte 3D-Modell auf 2D-Skizze starten oder 3D-Skizze starten .“
* **Weiteres Zitat:** „Zum Beenden einer 2D-Skizze klicken Sie auf der Registerkarte Skizze auf Skizze beenden“

### Beleg: Start and Finish 2D and 3D Sketches on the Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-E96FB3C4-136B-4551-BF45-F54594543ECB.htm
* **Wörtliches Zitat:** „On the 3D Model tab, click Start 2D Sketch or Start 3D Sketch .“
* **Weiteres Zitat:** „To end a 2D sketch, on the Sketch tab click Finish Sketch“

### Beleg: Menüband 3D-Modell Gruppen Erstellen und Grundkörper (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B0CFA8E7-D3F5-48A9-BE6F-C8DF668301BD.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte 3D-Modell Gruppe Erstellen Extrusion .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Grundkörper Quader oder Registerkarte 3D-Modell Gruppe Grundkörper Zylinder .“

### Beleg: Ribbon 3D Model Create and Primitives Panels (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-B0CFA8E7-D3F5-48A9-BE6F-C8DF668301BD.htm
* **Wörtliches Zitat:** „On the ribbon, click 3D Model tab Create panel Extrude .“
* **Weiteres Zitat:** „Click 3D Model tab Primitives panel ** Box** or 3D Model tab Primitives panel ** Cylinder** .“

### Beleg: Menüband 3D-Modell Gruppe Erstellen Prägen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E6848555-B274-4858-8401-84E260771E84.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Erstellen Prägen .“

### Beleg: Ribbon 3D Model Create Panel Emboss (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-E6848555-B274-4858-8401-84E260771E84.htm
* **Wörtliches Zitat:** „Click 3D Model tab Create panel Emboss .“

### Beleg: Menüband 3D-Modell Gruppe Grundkörper Kugel und Torus (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-401BABD2-8D5B-4300-BA8D-70037445044F.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Grundkörper Kugel oder Registerkarte 3D-Modell Gruppe Grundkörper Torus .“

### Beleg: Ribbon 3D Model Primitives Panel Sphere and Torus (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-401BABD2-8D5B-4300-BA8D-70037445044F.htm
* **Wörtliches Zitat:** „Click 3D Model tab Primitives panel Sphere or 3D Model tab Primitives panel Torus .“

### Beleg: Platzierte Elemente im Bauteil-Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B6A701E6-AFEB-4272-9EFC-EDC156FB8A59.htm
* **Wörtliches Zitat:** „Die Befehle für platzierte Elemente (Rundung, Fase, Bohrung, Gewinde, Flächenverjüngung und Wandung) befinden sich auf den Registerkarten Skizze und 3D-Modell:“

### Beleg: Placed Features on Part Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-B6A701E6-AFEB-4272-9EFC-EDC156FB8A59.htm
* **Wörtliches Zitat:** „The commands for placed features (fillet, chamfer, hole, thread, face draft, and shell,) are located on the Sketch and 3D Model tabs:“

### Beleg: Menüband 3D-Modell Gruppe Ändern Rundung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-590A8760-FFBB-41C8-8169-6B7002207884.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Rundung .“

### Beleg: Ribbon 3D Model Modify Panel Fillet (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-590A8760-FFBB-41C8-8169-6B7002207884.htm
* **Wörtliches Zitat:** „Click 3D Model tab Modify panel Fillet .“

### Beleg: Menüband 3D-Modell Gruppe Ändern Verdickung/Versatz (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A9A4FF6E-9569-4BED-8AC7-EB245E6456F8.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Verdickung/Versatz .“

### Beleg: Ribbon 3D Model Modify Panel Thicken/Offset (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-A9A4FF6E-9569-4BED-8AC7-EB245E6456F8.htm
* **Wörtliches Zitat:** „Click 3D Model tab Modify panel Thicken/Offset .“

### Beleg: Menüband 3D-Modell Gruppe Ändern Kombinieren und Trennen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-349C84EE-2D24-4DFC-A239-AFD55E5441AD.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Kombinieren .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Trennen .“

### Beleg: Ribbon 3D Model Modify Panel Combine and Split (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-349C84EE-2D24-4DFC-A239-AFD55E5441AD.htm
* **Wörtliches Zitat:** „Click 3D Model tab Modify panel Combine .“
* **Weiteres Zitat:** „Click 3D Model tab Modify panel Split .“

### Beleg: Menüband 3D-Modell Gruppe Ändern Körper verschieben (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-993A4C8C-867E-4F87-8C50-EE90C61A7F3A.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Körper verschieben .“

### Beleg: Ribbon 3D Model Modify Panel Move Bodies (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-993A4C8C-867E-4F87-8C50-EE90C61A7F3A.htm
* **Wörtliches Zitat:** „Click 3D Model tab Modify panel Move Bodies .“

### Beleg: Menüband 3D-Modell Fläche löschen und Fläche ersetzen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E9151557-0811-49FE-AC40-3AA364466DA8.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Ändern Fläche löschen .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Fläche Fläche ersetzen .“

### Beleg: Ribbon 3D Model Delete Face and Replace Face (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-E9151557-0811-49FE-AC40-3AA364466DA8.htm
* **Wörtliches Zitat:** „Click 3D Model tab Modify panel Delete Face .“
* **Weiteres Zitat:** „Click 3D Model tab Surface panel Replace Face .“

### Beleg: Arbeitselemente im Bauteil-Menüband (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-E0C11929-0C49-4923-84E7-1138C8D8014F.htm
* **Wörtliches Zitat:** „Zu den Arbeitselementen zählen Arbeitsebenen, Arbeitsachsen und Arbeitspunkte.“

### Beleg: Work Features on Part Ribbon (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-E0C11929-0C49-4923-84E7-1138C8D8014F.htm
* **Wörtliches Zitat:** „Work features include work planes, work axes, and work points.“

### Beleg: Menüband 3D-Modell Gruppe Arbeitselemente (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-38A9748E-FA2D-44D3-928C-DFE1326A9385.htm
* **Wörtliches Zitat:** „Klicken Sie in der Multifunktionsleiste auf Registerkarte 3D-Modell Gruppe Arbeitselemente .“

### Beleg: Ribbon 3D Model Work Features Panel (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-38A9748E-FA2D-44D3-928C-DFE1326A9385.htm
* **Wörtliches Zitat:** „On the ribbon, click 3D Model tab Work Features panel .“
* **Weiteres Zitat:** „On the ribbon, click 3D Model tab Work Features panel Grounded Point .“

### Beleg: Anordnungen im 3D-Modell Gruppe Anordnung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-9B3D1B72-340A-4F3E-9AD1-80E6DDD91ED2.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Anordnung Rechteckige Anordnung .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Anordnung Runde Anordnung .“
* **Weiteres Zitat:** „Klicken Sie in einer Bauteildatei auf Registerkarte 3D-Modell Gruppe Anordnung Spiegeln .“

### Beleg: Patterns on 3D Model Pattern Panel (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-9B3D1B72-340A-4F3E-9AD1-80E6DDD91ED2.htm
* **Wörtliches Zitat:** „Click 3D Model tab Pattern panel Rectangular Pattern .“
* **Weiteres Zitat:** „Click 3D Model tab Pattern panel Circular Pattern .“
* **Weiteres Zitat:** „Click 3D Model tab Pattern panel Mirror .“

### Beleg: Menüband 3D-Modell Gruppe Fläche Füllfläche, Heften und Regelfläche (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-5A8568DF-5BDA-47B9-97FC-2722B8A78A89.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Fläche Füllfläche .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Fläche Heften .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Fläche Regelfläche .“

### Beleg: Ribbon 3D Model Surface Panel Patch, Stitch and Ruled Surface (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-5A8568DF-5BDA-47B9-97FC-2722B8A78A89.htm
* **Wörtliches Zitat:** „Click 3D Model tab Surface panel Patch .“
* **Weiteres Zitat:** „Click 3D Model tab Surface panel Stitch .“
* **Weiteres Zitat:** „Click 3D Model tab Surface panel Ruled Surface .“

### Beleg: Menüband 3D-Modell Gruppe Fläche Stutzen und Dehnen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-7661F5F8-2C6C-42E9-8B7F-E7B62F2C7422.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Fläche Stutzen .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte 3D-Modell Gruppe Fläche Dehnen .“

### Beleg: Ribbon 3D Model Surface Panel Trim and Extend (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-7661F5F8-2C6C-42E9-8B7F-E7B62F2C7422.htm
* **Wörtliches Zitat:** „click 3D Model tab Surface panel Trim .“
* **Weiteres Zitat:** „Click 3D Model tab Surface panel Extend .“

### Beleg: Registerkarte Skizze Gruppe Erstellen Geometrie (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-D489CE6D-7299-4211-A43A-F3580A4BA357.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Ellipse .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Rechteck .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Rundung .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Fase .“

### Beleg: Sketch Tab Create Panel Geometry (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-D489CE6D-7299-4211-A43A-F3580A4BA357.htm
* **Wörtliches Zitat:** „Click Sketch tab Create panel Ellipse .“
* **Weiteres Zitat:** „Click Sketch tab Create panel Polygon .“
* **Weiteres Zitat:** „Click Sketch tab Create panel Fillet .“
* **Weiteres Zitat:** „Click Sketch tab Create panel Chamfer .“

### Beleg: Registerkarte Skizze Gruppe Erstellen Geometrie projizieren (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-B8D8B07B-86F2-4CB7-AB21-3131D94AD1CC.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Geometrie projizieren .“
* **Weiteres Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Erstellen Schnittkanten projizieren .“

### Beleg: Sketch Tab Create Panel Project Geometry (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-B8D8B07B-86F2-4CB7-AB21-3131D94AD1CC.htm
* **Wörtliches Zitat:** „Click Sketch tab Create panel Project Geometry .“
* **Weiteres Zitat:** „Click Sketch tab Create panel Project Cut Edges .“

### Beleg: Registerkarte Skizze Gruppe Ändern Versatz und Skalieren (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-962CEE71-8BE4-4DA6-B51E-341319C64FA4.htm
* **Wörtliches Zitat:** „Klicken Sie auf Registerkarte Skizze Gruppe Ändern Versatz .“
* **Weiteres Zitat:** „Klicken Sie in einer 2D-Skizze auf Registerkarte Skizze Gruppe Ändern Skalieren .“

### Beleg: Sketch Tab Modify Panel Offset and Scale (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-962CEE71-8BE4-4DA6-B51E-341319C64FA4.htm
* **Wörtliches Zitat:** „click Sketch tab Modify panel Offset .“
* **Weiteres Zitat:** „In a 2D sketch, click Sketch tab Modify panel Scale .“

### Beleg: Registerkarte Skizze Gruppe Ändern Teilen, Stutzen und Dehnen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DD00037F-6BBA-4B95-AA90-4F99DCEB667D.htm
* **Wörtliches Zitat:** „Klicken Sie in einer Skizze auf Registerkarte Skizze Gruppe Ändern Teilen .“
* **Weiteres Zitat:** „Klicken Sie in einer Skizze auf Registerkarte Skizze Gruppe Ändern Stutzen .“
* **Weiteres Zitat:** „Klicken Sie in einer Skizze auf Registerkarte Skizze Gruppe Ändern Dehnen .“

### Beleg: Sketch Tab Modify Panel Split, Trim and Extend (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-DD00037F-6BBA-4B95-AA90-4F99DCEB667D.htm
* **Wörtliches Zitat:** „In a sketch, click Sketch tab Modify panel Split .“
* **Weiteres Zitat:** „In a sketch, click Sketch tab Modify panel Trim .“
* **Weiteres Zitat:** „In a sketch, click Sketch tab Modify panel Extend .“

### Beleg: Registerkarte Skizze Gruppe Ändern Verschieben und Drehen (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-F8114270-18F7-4C7A-947E-AC489EDACFA9.htm
* **Wörtliches Zitat:** „Klicken Sie in einer 2D-Skizze auf Registerkarte Skizze Gruppe Ändern Verschieben .“
* **Weiteres Zitat:** „Klicken Sie in einer 2D-Skizze auf Registerkarte Skizze Gruppe Ändern Drehen .“

### Beleg: Sketch Tab Modify Panel Move and Rotate (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-F8114270-18F7-4C7A-947E-AC489EDACFA9.htm
* **Wörtliches Zitat:** „In a 2D sketch, click Sketch tab Modify panel Move .“
* **Weiteres Zitat:** „In a 2D sketch, click Sketch tab Modify panel Rotate .“

### Beleg: Registerkarte Skizze Gruppe Anordnung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-AAD3A699-FED8-4614-A31D-0A2316328CEE.htm
* **Wörtliches Zitat:** „Klicken Sie in einer Skizze unter Registerkarte Skizze Gruppe Anordnung auf Rechteckig.“
* **Weiteres Zitat:** „Klicken Sie in einer Skizze unter Registerkarte Skizze Gruppe Anordnung auf Kreisförmig .“
* **Weiteres Zitat:** „Klicken Sie in einer Skizze auf Registerkarte Skizze Gruppe Anordnung Spiegeln (2D) oder auf Registerkarte 3D-Skizze Gruppe Anordnung Spiegeln (3D).“

### Beleg: Sketch Tab Pattern Panel (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-AAD3A699-FED8-4614-A31D-0A2316328CEE.htm
* **Wörtliches Zitat:** „In a sketch, click Sketch tab Pattern panel, click Rectangular .“
* **Weiteres Zitat:** „In a sketch, click Sketch tab Pattern panel, click Circular .“
* **Weiteres Zitat:** „In a sketch, click Sketch tab Pattern panel Mirror (2D) or 3D Sketch tab Pattern panel Mirror (3D)“

### Beleg: Registerkarte Skizze Gruppen Abhängig machen und Format (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-026FE8D3-AFBB-4834-BC18-73D9CFF78185.htm
* **Wörtliches Zitat:** „Klicken Sie in einer Skizze auf Registerkarte Skizze Gruppe Abhängig machen Bemaßung (2D-Skizze)“
* **Weiteres Zitat:** „Klicken Sie auf die Registerkarte Skizze Gruppe Format > Getriebene Bemaßung (2D-Skizzen)“

### Beleg: Sketch Tab Constrain and Format Panels (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-026FE8D3-AFBB-4834-BC18-73D9CFF78185.htm
* **Wörtliches Zitat:** „In a sketch, click Sketch tab Constrain panel Dimension (2D sketch)“
* **Weiteres Zitat:** „Click Sketch tab Format panel > Driven Dimension (2D sketches)“

### Beleg: Geometrische Abhängigkeiten und Horizontal-Kürzel (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A85A7A30-7D81-4C75-8769-CAD034EEA930.htm
* **Wörtliches Zitat:** „Zum Starten des Befehls Abhängigkeit Horizontal drücken Sie den Bindestrich (Vorgabe-Tastaturkurzbefehl für den Befehl Horizontal) auf der Tastatur.“

### Beleg: Geometric Constraints and Horizontal Shortcut (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-A85A7A30-7D81-4C75-8769-CAD034EEA930.htm
* **Wörtliches Zitat:** „To start the Horizontal constraint command, press the dash sign (default shortcut key for the Horizontal command) on your keyboard.“

### Beleg: Allgemeine Bemaßung in der Skizzierumgebung (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-5E25D5FB-3B94-44A0-AD50-80EF06F5A24F.htm
* **Wörtliches Zitat:** „Der Befehl Allgemeine Bemaßung erstellt eine lineare Bemaßung, wenn Sie ein oder zwei Elemente auswählen, eine Durchmesserbemaßung, wenn Sie einen Kreis auswählen, und eine Radiusbemaßung, wenn Sie einen Bogen auswählen.“

### Beleg: General Dimension in Sketch Environment (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-5E25D5FB-3B94-44A0-AD50-80EF06F5A24F.htm
* **Wörtliches Zitat:** „The General Dimension command creates a linear dimension when you select one or two elements, a diameter dimension when you select a circle, and a radius dimension when you select an arc.“

### Beleg: Registerkarte Skizze Gruppe Format Konstruktion (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-F5A5790A-F748-49F0-A81F-BCA56C7C1E89.htm
* **Wörtliches Zitat:** „Bevor Sie in der Skizzierumgebung mit dem Zeichnen beginnen, klicken Sie auf Registerkarte Skizze Gruppe Format Konstruktion.“

### Beleg: Sketch Tab Format Panel Construction (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-F5A5790A-F748-49F0-A81F-BCA56C7C1E89.htm
* **Wörtliches Zitat:** „Before starting to draw in the sketch environment, click Sketch tab Format panel Construction.“

### Beleg: Registerkarte Skizze Gruppe Format Mittelpunkt und Punkt (Deutsch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-D4A4288F-32F1-4E23-A382-930EBA152E87.htm
* **Wörtliches Zitat:** „(2D-Skizze) Klicken Sie auf Registerkarte Skizze > Gruppe Erstellen > Punkt .“
* **Weiteres Zitat:** „Zum Wechseln zwischen Mittelpunkten und Skizzierpunkten klicken Sie vor dem Erstellen oder Importieren von Punkten auf Gruppe Format > Mittelpunkt.“

### Beleg: Sketch Tab Format Panel Center Point and Point (Englisch)
* **URL:** https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-Help/files/GUID-D4A4288F-32F1-4E23-A382-930EBA152E87.htm
* **Wörtliches Zitat:** „(2D sketch) Click Sketch tab > Create panel > Point .“
* **Weiteres Zitat:** „To change between center points and sketch points, click Format panel > Center Point before you create or import points.“
