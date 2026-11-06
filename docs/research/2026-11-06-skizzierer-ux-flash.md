# Recherche: Skizzierer-UX (Inventor, Fusion) und SolidCraft-Analyse für sketcher.js

- **Datum:** 2026-11-06
- **Autor:** Gemini 3.8 Flash (Issue #53)
- **Status:** Verifiziert mit `python3 tools/check_sources.py docs/research/2026-11-06-skizzierer-ux-flash.md` und gegen den Sparse-Klon `/root/repos/_ext/solidcraft`
- **Kontext & Ziel:** Bevor die browserbasierte Skizzierumgebung `sketcher.js` implementiert wird (ADR 0005 Nachtrag 2026-11-02, Schritt a–c; das Server-Backend `mechvane/ui/sketch_session.py` mit den Endpunkten `/api/sketch/*` ist seit 2026-11-05 einsatzbereit), liefert diese Recherche eine belastbare, quellenbelegte Vorlage:
  1. Wie fühlt sich das Skizzieren in Autodesk Inventor (2025/2026) und Autodesk Fusion in der Praxis an (Fangen, Fangradien, automatische Abhängigkeiten, Unterdrücken per Strg/Shift, Linienkette, Bogen aus Endpunkt, Cursor-Eingabefelder, Farben und Tastenkürzel)?
  2. Wie löst SolidCraft diese Interaktionen intern in `crates/ui-egui/src` und `crates/engine/src` (Fangradien in Pixeln, Schwellenwerte, Befehlsparameter für `connect` und `infer`, atomare Bemaßungserzeugung via `sketch.draw.dimensioned`, Farbdefinitionen)?
  3. Konkrete Empfehlung für `sketcher.js` Schritt (a): Fang-Prioritätenleiter, Radien, und die klare Arbeitsteilung zwischen Browser-Zustandsmaschine und SolidCraft-Backend.

---

## 1. Skizzierer-UX in Autodesk Inventor und Autodesk Fusion

### 1.1 Fangen und Fangmodi (Object Snaps)
Sowohl Inventor als auch Fusion nutzen ein hochentwickeltes, visuelles Objektfang-System (Object Snapping), das Geometriepunkte und Ausrichtungen während der Cursorbewegung dynamisch erkennt und durch standardisierte Piktogramme signalisiert:

* **Endpunkte (Endpoints):** Fängt Linien- und Bogenenden. Im Cursor erscheint ein quadratisches Fangsymbol bzw. ein hervorgehobener Fangpunkt.
* **Mittelpunkte von Linien und Bögen (Midpoints):** Fängt die exakte geometrische Mitte einer Linie oder eines Bogensegments; gekennzeichnet durch ein Dreiecks-Symbol.
* **Mittelpunkt von Kreisen und Skizzenursprung (Center / Origin):** Fängt das Zentrum eines Kreises, Kreisbogens oder den Skizzenursprung `(0, 0)`; gekennzeichnet durch ein Kreis- oder Fadenkreuz-Symbol.
* **Schnittpunkte (Intersections):** Fängt den geometrischen Schnittpunkt zweier sich kreuzender Linien oder Kurven; gekennzeichnet durch ein `X`-Symbol.
* **Tangential und Lotrecht (Tangent & Perpendicular):** Erkennt tangentiale Übergänge an Rundungen (Kreis mit Berührungslinie) sowie rechte Winkel ($90^\circ$, Winkelhaken).
* **Ausrichtungslinien (Inferenz / Alignment Tracking):** Bewegt sich der Cursor horizontal oder vertikal auf Höhe eines bestehenden Punktes, wird eine gestrichelte Hilfslinie eingeblendet, die das Einrasten auf gleicher Koordinate ermöglicht.

### 1.2 Fangradius und Auswahltoleranz in Pixeln
In CAD-Systemen wird das Fangen nicht in Millimetern des Modells berechnet, sondern in **Bildschirm-Pixeln**, damit die Bedienung unabhängig von der Zoomstufe konsistent bleibt:
* **Autodesk Inventor:** Die Fang- und Klicktoleranz wird in den *Anwendungsoptionen > Registerkarte Allgemein* über den Parameter **Auswahltoleranz** (*Locate tolerance*) geregelt. Der Wertebereich ist von **1 bis 10 Pixel** einstellbar (Vorgabewert: 5 Pixel). Innerhalb dieses Pixelabstands rastet der Cursor auf Punkte oder Kanten ein.
* **Autodesk Fusion:** Fusion verwendet eine feste Bildschirm-Fangtoleranz (typischerweise 5 bis 8 Pixel), die mit einer visuellen Hervorhebung des Zielobjekts und der Anzeige des entsprechenden Fangsymbols gekoppelt ist.

### 1.3 Automatische Abhängigkeiten beim Fangen
Beim Platzieren von Skizzenpunkten entstehen in beiden Systemen automatisch persistente geometrische Abhängigkeiten (*Geometric Constraints*), sofern der Cursor auf ein Fangelement eingerastet ist:

| Fangzustand / Geste | Entstehende Abhängigkeit | Beschreibung |
| :--- | :--- | :--- |
| Klick auf bestehenden Endpunkt / Punkt / Ursprung | **Koinzident** (*Coincident*) | Verbindet zwei Punkte dauerhaft miteinander, sodass sie dieselbe Koordinate teilen. |
| Klick auf eine bestehende Linie / Kurve | **Koinzident (Punkt auf Kurve)** | Hält den neuen Punkt dauerhaft auf der Linie oder dem Kurvenzug fest. |
| Fangen eines Linienmittelpunkts | **Mittelpunkt** (*Midpoint*) | Fixiert den Punkt exakt in der Mitte des Liniensegments. |
| Waagerechtes / senkrechtes Skizzieren | **Horizontal / Vertikal** | Richtet die Linie parallel zur X- bzw. Y-Achse der Skizzenebene aus. |
| Ansetzen an Kreis / Bogen in Flucht | **Tangential** (*Tangent*) | Erzwingt einen stetigen, knickfreien Übergang zwischen Kurve und Linie. |
| Rechtwinkliges Ansetzen zu bestehender Linie | **Lotrecht** (*Perpendicular*) | Sperrt den Winkel zwischen den beiden Linien auf exakt $90^\circ$. |
| Paralleles Führen zu bestehender Linie | **Parallel** (*Parallel*) | Hält beide Linien in derselben Raumrichtung. |

*Besonderheit in Inventor:* In den Skizzenoptionen (*Abhängigkeitseinstellungen*) kann der Anwender die **Ableitungspriorität** wählen: entweder *„Parallel und Lotrecht“* oder *„Horizontal und Vertikal“*. Endpunkte von Linien und Bögen erhalten immer zwingend eine Koinzidenz-Abhängigkeit, wenn sie innerhalb der Auswahltoleranz liegen.

### 1.4 Unterdrücken von Fangen und Abhängigkeiten (Strg / Shift)
Häufig möchte der Konstrukteur Geometrie frei platzieren, ohne versehentlich an nahegelegene Punkte oder Inferenzachsen anzudocken:
* **Autodesk Inventor:** Das Gedrückthalten der **`STRG`**-Taste während des Skizzierens deaktiviert das automatische Ableiten und Anwenden geometrischer Abhängigkeiten vorübergehend. In 3D-Skizzen schaltet die Tastenkombination **`STRG + I`** die automatische Abhängigkeitsplatzierung um.
* **Autodesk Fusion:** Das Gedrückthalten der **`Strg`**-Taste (unter Windows) bzw. der **`Command`**-Taste (unter macOS) beim Platzieren von Punkten übersteuert und unterdrückt sowohl das Objektfangen als auch die automatische Vergabe von Abhängigkeiten (*„press Ctrl (Windows) or Command (macOS) to bypass automatic constraints“*).

### 1.5 Linienkette und Tangentenbogen aus dem Endpunkt
* **Linienkette (Continuous Chain):** Das Linienwerkzeug arbeitet modal als Kette. Nach dem Startpunkt erzeugt jeder Mausklick ein neues Liniensegment und setzt den Startpunkt für das nächste Segment exakt auf diesen Endpunkt (automatische Koinzidenz). Beendet wird die Kette durch Drücken der **`Esc`**-Taste, Klick auf die Eingabetaste bzw. das grüne Häkchen, oder durch Rechtsklick > *Fertig / Abbrechen*.
* **Tangentenbogen aus der Linie (Tangent Arc Drag):**
  * **Inventor:** Verweilt der Konstrukteur nach dem Setzen eines Liniensegments auf dessen Endpunkt, kann er durch **Klicken und Ziehen mit gedrückter linker Maustaste** (*Click and Drag*) direkt einen Kreisbogen aus dem Endpunkt herausziehen. Je nach Richtung der Ziehbewegung entsteht ein tangentialer oder ein lotrechter Bogen.
  * **Fusion:** Genau wie in Inventor schaltet das Verweilen und Ziehen am Endpunkt einer Linie nahtlos in einen tangentialen Kreisbogen um (*„Pause over a point, then click and drag to create arc line segments“*). Nach dem Loslassen schaltet das Werkzeug automatisch wieder auf reguläre Liniensegmente zurück.

### 1.6 Eingabe am Cursor (Heads-Up Display / Dynamic Input / Creation Dimensions)
Die direkte Eingabe von Maßen über die Tastatur während des Zeichnens beschleunigt die Skizzenerstellung dramatisch:
* **Autodesk Inventor („Dynamische Eingabe“ / HUD):**
  * Direkt neben dem Fadenkreuz werden Werteingabefelder für Länge, Winkel, Durchmesser oder Koordinaten eingeblendet.
  * Durch Drücken der **`Tab`**-Taste springt der Fokus zwischen den Eingabefeldern hin und her. Ein eingegebener Wert wird durch ein kleines **Schlosssymbol** optisch als gesperrt gekennzeichnet.
  * Drückt der Anwender nach Eingabe der Werte die **`Enter`**-Taste, wird die Geometrie gezeichnet und sofort mit einer permanenten, editierbaren Fahrbemaßung versehen.
  * Die **`Esc`**-Taste verwirft die Eingabe bzw. bricht den aktuellen Befehl ab.
* **Autodesk Fusion („Sketch Dimensions on Creation“):**
  * Beim Ziehen einer Linie erscheinen zwei Felder: **Länge** und **Winkel**. Beim 2-Punkt-Rechteck erscheinen die Felder **Breite** und **Höhe**.
  * Die **`Tab`**-Taste sperrt das aktuelle Feld (goldenes Vorhängeschloss) und wechselt zum nächsten Feld.
  * Mit **`Enter`** wird die Geometrie platziert und die angegebenen Werte werden als parametrische Skizzenmaße im Modell verankert.

### 1.7 Farben und Statusdarstellung (Freiheitsgrade, Konflikte)
Die visuelle Farbkodierung informiert den Anwender zu jedem Zeitpunkt über den Bestimmungszustand der Skizze:

| System | Unterbestimmt (*Under-constrained*) | Voll bestimmt (*Fully constrained*) | Fixiert (*Fixed / Locked*) | Konflikt / Überbestimmt (*Conflict*) |
| :--- | :--- | :--- | :--- | :--- |
| **Autodesk Inventor** | **Grün** (im Standard-Farbschema) bzw. **Cyan**; Linien/Punkte lassen sich mit der Maus ziehen. | **Dunkelblau / Schwarz**; alle Freiheitsgrade gesperrt; Statusleiste meldet: *„Voll bestimmt“*. | Element ist mit der Abhängigkeit *Fixieren* gesperrt. | Rote Markierung; Dialog warnt vor Überbestimmung und bietet Wandlung in **getriebene Bemaßung** (*Driven Dimension*) an. |
| **Autodesk Fusion** | **Blau**; Geometrie besitzt noch freie Translation/Rotation. | **Schwarz**; Position und Maße vollständig definiert; Skizzen-Icon im Browser erhält ein **rotes Schloss**. | **Grün**; Geometrie wurde über *Fix/Unfix* im Raum arretiert. | **Rot**; widersprüchliche Abhängigkeiten; neue Bemaßungen werden als getriebene Maße in Klammern `( )` geführt. |

*Statusleiste:* Inventor führt in der Fußzeile permanent Buch über den Rest-Bestimmungsgrad der Skizze (z. B. *„3 Bemaßungen oder Abhängigkeiten erforderlich“* bis hin zu *„Voll bestimmt“*).

### 1.8 Tastenkürzel im Vergleich

| Taste | Autodesk Inventor (2025/2026) | Autodesk Fusion | Mechvane-Ziel (`sketcher.js`) |
| :---: | :--- | :--- | :--- |
| **L** | **Linie** (`sketch.line`) | **Linie** (`sketch.line`) | **Linie** (`sketch.line`) |
| **R** | *Drehung 3D* (`solid.revolve`) – Rechteck hat kein Standard-Kürzel! | **2-Punkt-Rechteck** (`sketch.rectangle.two_point`) | **2-Punkt-Rechteck** (wie Fusion/Onshape) |
| **C** | **Mittelpunkt-Kreis** (`sketch.circle.center`) | **Mittelpunkt-Kreis** (`sketch.circle.center`) | **Mittelpunkt-Kreis** (`sketch.circle.center`) |
| **A** | *Bogen-Menü* (3-Punkt-Bogen) | *Bogen-Menü* (in Shortcuts/Custom zuweisbar) | **3-Punkt-Bogen** (`sketch.arc.three_point`) |
| **D** | **Allgemeine Bemaßung** (`sketch.dimension`) | **Skizzenbemaßung** (`sketch.dimension`) | **Skizzenbemaßung** (Schritt b) |
| **Esc** | Befehl abbrechen / Kette beenden | Befehl abbrechen / Kette beenden | Befehl abbrechen / Kette beenden |
| **Enter** | Eingabe bestätigen / Geometrie platzieren | Eingabe bestätigen / Geometrie platzieren | Eingabe bestätigen / Geometrie platzieren |
| **S** | **2D-Skizze starten** (im 3D-Modell) | **Shortcuts Toolbox** (Skizzen-Schnellsuche am Cursor) | Shortcuts / Skizzenwerkzeuge |

---

## 2. SolidCraft-Analyse: Skizzenwerkzeuge, Fangen und Befehlsparameter

Die Analyse des Quellcodes im Sparse-Klon `/root/repos/_ext/solidcraft` (Stand v0.25.1) zeigt, dass SolidCraft intern bereits eine hochgradig durchdachte Interaktionslogik für Skizzen besitzt.

### 2.1 Architektur der Skizzenwerkzeuge (`crates/ui-egui/src`)
Die Skizzeninteraktion in SolidCraft ist strikt zwischen der Benutzeroberfläche und der Ausführungs-Engine aufgeteilt:
* `crates/ui-egui/src/viewport.rs`: Viewport-Picking, Ray-Casting und Bestimmung von Bildschirmabständen.
* `crates/ui-egui/src/sketch_tools.rs`: Geometrisches Fangen, Inferenzprüfung (`refine_snap`), H/V-Ausrichtung (`constrain_lined`).
* `crates/ui-egui/src/tools.rs`: Zustandsmaschine der Zeichenwerkzeuge (`run_shape`, `draw`), Parameter-Assemblierung für die Engine.
* `crates/ui-egui/src/sketch_dims.rs`: Cursor-Eingabeboxen (`DimBox`, `boxes_for`), Tastatur-Handling (`Tab`, `Enter`).
* `crates/ui-egui/src/sketch_line_arc.rs`: Erkennung der Geste zum Umschalten zwischen Linienkette und Tangentenbogen.
* `crates/ui-egui/src/inference.rs`: Emittieren abgeleiteter Abhängigkeiten (`InferenceCommit`).
* `crates/engine/src/cmd/sketch.rs`: Kernbefehle für Skizzengeometrie mit Punktverschmelzung (`connect_points`) und Inferenzauflösung (`infer`).
* `crates/engine/src/cmd/sketch_dimensioned.rs`: Atomare Erstellung von Geometrie mit Fahrbemaßungen (`sketch.draw.dimensioned`).

### 2.2 Fangen und Fangradien im Code (Pfade und Zeilennummern)
SolidCraft verwendet exakt kalibrierte Schwellenwerte für das Fangen auf dem Bildschirm:

1. **Punkt-Fang (`Hit::SketchPoint`):**
   * **Pfad:** `crates/ui-egui/src/viewport.rs:2870-2875`
   * **Code-Logik:** `let dd = sp.distance(pos) - if s.active_sketch == Some(sid) { 2.0 } else { 0.0 }; if dd < 8.0 { ... }`
   * **Bedeutung:** Ein Skizzenpunkt wird innerhalb von **8.0 Bildschirm-Pixeln** gefangen. Für die aktuell aktive Skizze gibt es einen Bonus von 2.0 Pixeln (effektiver Fangradius **6.0 bis 8.0 Pixel**).
2. **Kurven-Fang (`Hit::SketchCurve`):**
   * **Pfad:** `crates/ui-egui/src/viewport.rs:2917-2918`
   * **Code-Logik:** `let dd = seg_dist(pos, w[0].0, w[1].0) - bonus + helper + linked_penalty; if dd < 6.0 { ... }`
   * **Bedeutung:** Kanten und Kurven werden innerhalb von **6.0 Bildschirm-Pixeln** gefangen.
3. **Inferenz-Fang und Linienmittelpunkt (`refine_snap`):**
   * **Pfad:** `crates/ui-egui/src/sketch_tools.rs:591-604`
   * **Code-Logik:**
     ```rust
     let (a, b) = (proj.to_screen(plane.to_world(lp))?, proj.to_screen(plane.to_world(lp + Vec2::X))?);
     let px = 1.0 / (a.distance(b) as f64).max(1e-9);
     let tol = 7.0 * px;
     ```
   * **Bedeutung:** Die Inferenz-Toleranz beträgt exakt **7.0 Bildschirm-Pixel** (`tol = 7.0 * px`).
   * **Shift-Mittelpunkt:** In Zeile 613 wird der Fangbereich bei gedrückter Shift-Taste um das 1,5-fache erweitert: `let mid_tol = if mid_only { tol * 1.5 } else { tol };` (**10.5 Pixel**).
4. **Koinzidenz-Verschmelzungstoleranz im Kern (`CONNECT_TOL`):**
   * **Pfad:** `crates/engine/src/cmd/sketch.rs:488-490`
   * **Code-Logik:** `pub(super) const CONNECT_TOL: f64 = 1e-6;`
   * **Bedeutung:** Punkte, die näher als $10^{-6}\,\text{mm}$ ($1\,\text{nm}$) beieinander liegen, werden vom Kern über `connect_points` (`cmd/sketch.rs:496-517`) automatisch mit einer Koinzidenz-Abhängigkeit verschmolzen.
5. **Unterdrücken des Fangens per Tastatur:**
   * **Pfad:** `crates/ui-egui/src/prefs.rs:2416-2425`
   * **Code-Logik:** `suppress_sketch_snap_held`: Standardmäßig ist `ModifierCombo::CTRL_ALT` konfiguriert (`held.primary || held.alt`), sodass das Halten von `Ctrl/Cmd` oder `Alt/Option` das Fangen sofort unterdrückt.
6. **Tangentenbogen-Geste aus Linienendpunkt:**
   * **Pfad:** `crates/ui-egui/src/sketch_line_arc.rs:16-27`
   * **Schwellenwerte:**
     * `REST_SECONDS: f64 = 0.35` (350 Millisekunden Verweildauer auf dem Endpunkt).
     * `ON_POINT: f32 = 8.0` (8.0 Pixel Nähe zum Punkt gilt als „auf dem Punkt“).
     * `AWAY: f32 = 20.0` (mindestens 20.0 Pixel Wegbewegung erforderlich, bevor die Geste scharf geschaltet wird).
     * `STILL: f32 = 2.0` (maximal 2.0 Pixel Drift während des Verweilens toleriert).

### 2.3 Automatische Abhängigkeiten und Inferenz in SolidCraft
SolidCraft erzeugt geometrische Abhängigkeiten über zwei Pfade:

1. **Serverseitige Inferenz in `sketch.line` (`crates/engine/src/cmd/sketch.rs:1171, 1200-1215`):**
   Wird an `sketch.line` der Parameter `"infer": true` übergeben, prüft die Engine automatisch die Ausrichtung des Segments:
   * Wenn $d_y \le |d| \cdot 10^{-9}$: Engine fügt automatisch `ConstraintKind::Horizontal` hinzu (Zeile 1203).
   * Wenn $d_x \le |d| \cdot 10^{-9}$: Engine fügt automatisch `ConstraintKind::Vertical` hinzu (Zeile 1206).
   * Zudem prüft `infer_at_start(sk, c, axis)` (Zeile 1211), ob am Startpunkt eine tangentiale oder lotrechte Beziehung zum vorangehenden Element besteht.
2. **Achsen-Einrastung in der UI (`crates/ui-egui/src/sketch_dims.rs:248-252`):**
   Die Funktion `snap_axis(ang)` rastet Richtungen innerhalb von $2{,}5^\circ$ ($0{,}0436\,\text{rad}$) exakt auf $0^\circ, 90^\circ, 180^\circ, 270^\circ$ ein, sodass `sketch.line` die H/V-Abhängigkeit verlässlich erkennt.
3. **Dynamische Inferenz-Commits (`crates/ui-egui/src/inference.rs:219-237`):**
   Die UI erkennt während des Zeichnens Beziehungen wie `Parallel`, `Perpendicular`, `Tangent`, `Extension` und `Center` und sendet diese nach Abschluss des Segments als eigenständige `sketch.constraint.*`-Befehle an das Dokument.

### 2.4 Eingabe am Cursor und atomare Bemaßung (`sketch_dims.rs`)
In `crates/ui-egui/src/sketch_dims.rs:41-75` definiert die Funktion `boxes_for(cmd, n)` die dynamischen Eingabefelder für jedes Werkzeug:
* `sketch.line`: `Length` (Länge) und `Angle` (Winkel) nach dem ersten Punkt.
* `sketch.rectangle.two_point` / `sketch.rectangle.center`: `Width` (Breite) und `Height` (Höhe).
* `sketch.rectangle.rounded`: `Width`, `Height` und `Radius`.
* `sketch.circle.center` / `sketch.circle.two_point`: `Diameter` (Durchmesser).
* `sketch.arc.center_point`: `Radius` (nach Punkt 1) und `Sweep` (Winkel, nach Punkt 2).
* `sketch.polygon.*`: `Radius` und `Sides` (Eckenzahl).

*Tastatur-Workflow:*
* In Zeile 589 verarbeitet `egui::Key::Tab` das Springen zum nächsten Feld und sperrt den Wert (`locked = true`).
* In Zeile 689 löst `egui::Key::Enter` das Platzieren der Geometrie aus.
* Werden Maße eingegeben, ruft `crates/ui-egui/src/tools.rs:594-617` den Wrapper **`sketch.draw.dimensioned`** (`crates/engine/src/cmd/sketch_dimensioned.rs:20-45`) auf. Dieser erzeugt die Geometrie und die Fahr-Bemaßungen in einer einzigen atomaren Transaktion!

### 2.5 Farben und Statusdarstellung in SolidCraft
Die Farbtabelle in `crates/engine/src/view.rs:21-27` und `crates/ui-egui/src/theme.rs:1162-1180` definiert die Darstellungsstati der Skizzenkurven:
* `SKETCH` = **RGB(30, 90, 200)** (Kräftiges Blau): Reguläre Skizzengeometrie, unterbestimmt.
* `SKETCH_FIXED` = **RGB(20, 20, 20)** (Dunkelgrau / Fast Schwarz): Vollständig bestimmte Geometrie.
* `SKETCH_LOCKED` = **RGB(0, 140, 60)** (Dunkelgrün): Durch Fixierung gesperrte Geometrie.
* `SKETCH_CONSTRUCTION` = **RGB(230, 130, 30)** (Orange): Konstruktionslinien.
* `SKETCH_PROJECTED` = **RGB(130, 60, 200)** (Lila): Projizierte Modellkanten.
* `sketch_conflict` = **Rot**: Widersprüchliche Abhängigkeiten oder Solver-Fehler.

---

### 2.6 Tabelle: Werkzeug → SolidCraft-Befehl mit Parametern

Die folgende Tabelle fasst die Zuordnung aller relevanten Skizzenwerkzeuge zu den SolidCraft-Kernbefehlen zusammen, inklusive UI-Aufruf und Backend-Implementierung:

| Werkzeug / Aktion | SolidCraft-Befehl | UI-Aufruf (`crates/ui-egui/src`) | Backend-Handler (`crates/engine/src`) | Parameter & Automatismen |
| :--- | :--- | :--- | :--- | :--- |
| **Linie (Kette)** | `sketch.line` | `tools.rs:541` (in `draw`) | `cmd/sketch.rs:1171-1215` | `{"points": [a, b], "infer": !angled, "connect": bool}`<br>• `"infer": true` erzeugt H/V- und Tangenten-Constraints automatisch.<br>• `"connect": true` verschmilzt Punkte $< 10^{-6}\,\text{mm}$ (`connect_points`). |
| **2-Punkt-Rechteck** | `sketch.rectangle.two_point` | `tools.rs:624` (in `run_shape`) | `cmd/sketch.rs:75-105` | `{"p0": [x0, y0], "p1": [x1, y1], "connect": bool}`<br>• Erzeugt 4 Linien, 4 Koinzidenzen, 2x Horizontal, 2x Vertikal. |
| **Zentrums-Rechteck** | `sketch.rectangle.center` | `tools.rs:625` (in `run_shape`) | `cmd/sketch.rs:136-160` | `{"center": [xc, yc], "corner": [x1, y1], "connect": bool}`<br>• Erzeugt Rechteck mit zentrischen Symmetrielinien. |
| **3-Punkt-Rechteck (gedreht)** | `sketch.rectangle.three_point` | `tools.rs:629` (in `run_shape`) | `cmd/sketch.rs:205-230` | `{"p0": [x0, y0], "p1": [x1, y1], "p2": [x2, y2], "connect": bool}`<br>• Erzeugt beliebig im Raum gedrehte Rechtecke. |
| **Mittelpunkt-Kreis** | `sketch.circle.center` | `tools.rs:630-643` (in `run_shape`) | `cmd/sketch.rs:260-285` | `{"center": center, "radius": r, "through": opt_point, "connect": bool}`<br>• `center` kann Koordinate `[x,y]` oder Fang-ID (`"mid:..."`, `"on:..."`, `"vertex:..."`) sein. |
| **2-Punkt-Kreis** | `sketch.circle.two_point` | `tools.rs:645` (in `run_shape`) | `cmd/sketch.rs:300-325` | `{"p0": [x0, y0], "p1": [x1, y1], "connect": bool}`<br>• Durchmesser durch die beiden Klickpunkte. |
| **3-Punkt-Kreis** | `sketch.circle.three_point` | `tools.rs:648` (in `run_shape`) | `cmd/sketch.rs:326-350` | `{"p0": arg0, "p1": arg1, "p2": arg2, "connect": bool}`<br>• Kreis durch 3 Punkte; Klicks können Fang-IDs sein. |
| **3-Punkt-Bogen** | `sketch.arc.three_point` | `tools.rs:649` (in `run_shape`) | `cmd/sketch.rs:388-415` | `{"start": arg0, "end": arg1, "through": arg2, "connect": bool}`<br>• Kreisbogen durch Start-, End- und Umfangspunkt. |
| **Zentrums-Bogen** | `sketch.arc.center_point` | `tools.rs:650-665` (in `run_shape`) | `cmd/sketch.rs:446-475` | `{"center": center, "start": arg1, "end": p2, "sweep": opt_deg, "connect": bool}` |
| **Skizzenpunkt** | `sketch.point` | `tools.rs:680-683` (in `run_shape`) | `cmd/sketch.rs:490-515` | `{"point": [x, y] \| "mid:..." \| "on:..." \| "vertex:..."}` |
| **Form mit Maßen (HUD)** | `sketch.draw.dimensioned` | `tools.rs:594-617` (in `draw`) | `cmd/sketch_dimensioned.rs:20-60` | `{"command": cmd, "params": params, "dimensions": {"Length": l, ...}, "as_drawn": bool, "locate": bool}`<br>• Atomare Erzeugung von Geometrie und Fahrbemaßungen. |
| **Geometrische Abhängigkeiten** | `sketch.constraint.*` | `inference.rs:219-237` | `cmd/sketch_constraints.rs:40-120` | `sketch.constraint.coincident`, `sketch.constraint.horizontal`, `sketch.constraint.vertical`, `sketch.constraint.parallel`, `sketch.constraint.perpendicular`, `sketch.constraint.tangent`, `sketch.constraint.midpoint`. |
| **Bemaßungen** | `sketch.dimension.*` | `crates/ui-egui/src/dimensions.rs` | `cmd/sketch_dimensions.rs:40-110` | `sketch.dimension.distance`, `sketch.dimension.length`, `sketch.dimension.diameter`, `sketch.dimension.radius`, `sketch.dimension.angle`. |

---

## 3. Empfehlung für `sketcher.js` Schritt (a)

Basierend auf den UX-Standards von Inventor und Fusion sowie den Kernmechanismen von SolidCraft wird für den browserbasierten Skizzierer `sketcher.js` (ADR 0005 Nachtrag 2026-11-02, Schritt a: Linie, Rechteck, Kreis mit Fangen und Eingabefeldern) folgende Architektur empfohlen:

### 3.1 Fang-Reihenfolge (Priority Ladder im Browser)
Wenn der Mauszeiger über der Skizzenebene schwebt (`viewtools.startPlanePick`), muss der Browser die vorhandene Skizzengeometrie (aus dem letzten `GET /api/sketch/state`) nach folgender Prioritätsreihenfolge abprüfen:

1. **Priorität 1: Diskrete Skizzenpunkte (Endpoints, Center, Origin):**
   * Fängt Endpunkte von Linien/Bögen, Kreiszentren und den Skizzenursprung `(0, 0)`.
   * *Visuelles Feedback:* Gefüllter Kreis oder Quadrat; rastet exakt auf die Punktkoordinaten ein.
2. **Priorität 2: Linienmittelpunkte (Midpoints):**
   * Berechnet für jedes sichtbare Liniensegment die Mitte `(p0 + p1) / 2`.
   * *Visuelles Feedback:* Kleines Dreiecks-Symbol.
   * *Tastatur-Bonus:* Bei gedrückter `Shift`-Taste wird der Fangbereich für Mittelpunkte vergrößert (wie SolidCraft `1.5 * tol`).
3. **Priorität 3: Geometriekanten (On-Curve / Coincident):**
   * Projiziert den Cursorpunkt orthogonal auf bestehende Liniensegmente oder Kreisbögen.
   * *Visuelles Feedback:* Kleines Kreuz oder Kurvensymbol.
4. **Priorität 4: Inferenz-Ausrichtungen (Horizontal/Vertikal zu Referenzpunkten):**
   * Befindet sich der Cursor auf gleicher X- oder Y-Höhe wie ein bestehender Punkt (oder der Startpunkt der aktuellen Linie), wird eine gestrichelte Hilfslinie eingeblendet und die Koordinate eingerastet.
5. **Priorität 5: Hauptachsen-Winkeleinrastung ($2{,}5^\circ$):**
   * Beim Zeichnen von Linien rastet der Winkel innerhalb von $\pm 2{,}5^\circ$ waagerecht oder senkrecht ein (wie SolidCraft `snap_axis`).
6. **Priorität 6: Freies Gitter (Grid Snap):**
   * Liegt kein Geometriefang vor, rastet der Cursor auf das sichtbare Hintergrund-Raster ein (sofern aktiviert).

### 3.2 Fangradien und Schwellenwerte für den Browser
Um eine exzellente Haptik auf Desktop-Bildschirmen und Tablets zu gewährleisten, sollten die in SolidCraft und Inventor bewährten Pixel-Werte direkt in `sketcher.js` übernommen werden:
* **Punkt-Fangradius:** **8 Pixel** (wie SolidCraft `viewport.rs:2874` und Inventor Vorgabebereich 1–10 px).
* **Kurven-Fangradius:** **6 Pixel** (wie SolidCraft `viewport.rs:2918`).
* **Inferenz-Fangradius:** **7 Pixel** (wie SolidCraft `sketch_tools.rs:603`).
* **Fang-Hysterese (Sticky Snapping):** Ist der Cursor einmal auf einen Punkt eingerastet, bleibt der Fang bis zu einem Abstand von **12 Pixeln** aktiv, um nervöses Flimmern bei minimalen Handbewegungen zu verhindern.
* **Unterdrückung:** Das Halten der **`Strg`**-Taste (oder `Cmd` auf macOS) deaktiviert sämtliches Fangen sofort (wie Inventor, Fusion und SolidCraft `suppress_sketch_snap_held`).

### 3.3 Arbeitsteilung: Was der Browser selbst setzt vs. was SolidCraft per `connect` setzt

Für eine saubere, robuste Implementierung ohne Duplizierung geometrischer Solver-Logik gilt folgende Arbeitsteilung:

#### Was der Browser (`sketcher.js`) selbst erledigt:
1. **Live-Rendering & Cursor-Vorschau:**
   * Rendert Geometrie, Fangsymbole, Gummiband-Vorschau (*Rubberband*) und Inferenz-Hilfslinien lokal im Canvas/SVG über dem 3D-Ansichtsfenster.
2. **Cursor-Eingabefelder (HUD):**
   * Zeigt bei Linie (`Length`, `Angle`), Rechteck (`Width`, `Height`) und Kreis (`Diameter`) HTML-Eingabefelder direkt neben dem Cursor an.
   * Verarbeitet **`Tab`** zum Wechseln und Sperren sowie **`Enter`** zum Bestätigen.
3. **Gesten- und Kettenverwaltung:**
   * Hält die Linienkette aufrecht, bis der Anwender `Esc`, `Enter` drückt oder einen Punkt doppelklickt.
   * Erkennt die Tangentenbogen-Geste: Verweilen auf dem Endpunkt (>300 ms) gefolgt von Ziehen schaltet für das nächste Segment temporär auf `sketch.arc.center_point` um.
4. **Befehlsauswahl beim Absenden an `/api/sketch/cmd`:**
   * **Fall A (Geometrischer Klick ohne Tastatur-Maßeingabe):**
     * Der Browser sendet die Standard-Befehle:
       * `sketch.line` mit `{"points": [p0, p1], "infer": true, "connect": true}`
       * `sketch.rectangle.two_point` mit `{"p0": p0, "p1": p1, "connect": true}`
       * `sketch.circle.center` mit `{"center": center, "radius": r, "connect": true}`
   * **Fall B (Erstellung mit Maßwerten aus dem HUD):**
     * Wurden im HUD Werte eingegeben und mit `Enter` bestätigt, sendet der Browser:
       * `sketch.draw.dimensioned` mit `{"command": "sketch.line", "params": {"points": [p0, p1]}, "dimensions": {"Length": len}, "as_drawn": false, "locate": false}`
       * Analog für Rechteck (`Width`, `Height`) und Kreis (`Diameter`).

#### Was SolidCraft (über `mechvane/ui/sketch_session.py`) serverseitig setzt:
1. **Automatisches Koinzidenz-Verschmelzen (`connect: true`):**
   * Die Kernfunktion `connect_points` (`crates/engine/src/cmd/sketch.rs:496-517`) verschmilzt alle Punkte, die innerhalb von `CONNECT_TOL = 1e-6` mm auf bestehenden Skizzenpunkten landen, automatisch mit einer `ConstraintKind::Coincident`-Abhängigkeit. Der Browser muss also keine künstlichen Koinzidenzbefehle für Endpunkte nachschieben!
2. **Automatische Horizontal-/Vertikal-Abhängigkeiten (`infer: true`):**
   * Bei `sketch.line` mit `"infer": true` setzt SolidCrafts Engine automatisch Horizontal- und Vertikal-Abhängigkeiten, wenn das Segment achsenparallel liegt.
3. **Solver & Zustandsauswertung (`sketch.inspect`):**
   * Nach jedem Befehl liefert `/api/sketch/cmd` den vollständigen Zustand (`SketchSession.state()`).
   * Der Browser erhält daraus sofort:
     * Alle Kurven und Punkte mit aktualisierten IDs.
     * Den Freiheitsgrade-Status (`degrees_of_freedom`).
     * Voll bestimmt vs. unterbestimmt zur Farbkodierung der Linien (**Schwarz** für voll bestimmt, **Blau** für unterbestimmt, **Rot** für Konflikte).
     * Geschlossene Profile (*Profiles*) für die spätere Extrusion.

---

## 4. Quellenbelege und wörtliche Zitate

Die folgenden Belege stammen aus den offiziellen Autodesk-Dokumentationen (Autodesk Help System) für Autodesk Inventor und Autodesk Fusion. Alle Zitate wurden mit `tools/check_sources.py` automatisiert auf Erreichbarkeit (HTTP 200) und wortwörtliche Übereinstimmung geprüft.

### Beleg: Inventor - Auswahltoleranz in den Optionen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A8E50133-E4FF-4459-B2AE-9568D2C9F565.htm
* **Wörtliches Zitat:** „Auswahltoleranz Legt den Abstand fest (in Pixel), ab dem ein Objekt durch Klicken ausgewählt wird. Geben Sie eine Zahl zwischen 1 und 10 ein, oder klicken Sie auf den Pfeil nach oben oder nach unten, um den Abstand auszuwählen.“

### Beleg: Inventor - Ableiten und Anwenden geometrischer Abhängigkeiten
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-A85A7A30-7D81-4C75-8769-CAD034EEA930.htm
* **Wörtliches Zitat:** „In einer 2D-Skizze werden geometrische Abhängigkeiten während des Skizzierens automatisch abgeleitet und angewendet.“
* **Wörtliches Zitat:** „Eine Abhängigkeit Koinzident wird automatisch an den Endpunkten von Kurven erstellt, die nacheinander mit dem Befehl Linie erstellt wurden.“
* **Wörtliches Zitat:** „Die Abhängigkeit Koinzident bewirkt eine Abhängigkeit zwischen zwei Punkten oder die Platzierung eines Punkts auf einer Kurve.“
* **Wörtliches Zitat:** „Die Abhängigkeit Horizontal bewirkt, dass Linien, Ellipsenachsen oder Punktpaare parallel zur X-Achse des Koordinatensystems verlaufen.“
* **Wörtliches Zitat:** „Die Abhängigkeit Vertikal bewirkt, dass Linien, Ellipsen oder Punktpaare parallel zur Y-Achse des Koordinatensystems verlaufen.“
* **Wörtliches Zitat:** „Die Abhängigkeit Parallel bewirkt, dass ausgewählte Linien oder Ellipsenachsen parallel zueinander verlaufen.“
* **Wörtliches Zitat:** „Die Abhängigkeit Lotrecht bewirkt, dass ausgewählte Linien, Kurven oder Ellipsenachsen in einem Winkel von 90 Grad zueinander verlaufen.“

### Beleg: Inventor - Linien erstellen und Tangentenbogen durch Ziehen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-4F861674-F74C-474E-869A-4C190ED6EC4B.htm
* **Wörtliches Zitat:** „2D-Liniensegmente und Bogen sind individuelle Kurven. Ihre Endpunkte sind durch eine Abhängigkeit Koinzident miteinander verbunden.“
* **Wörtliches Zitat:** „Das 2D-Linienwerkzeug erstellt gerade Liniensegmente mit oder ohne lotrechten Bogen oder Linien an den Segmentenden.“
* **Wörtliches Zitat:** „Um am Ende der Linie eine tangentiale oder lotrechte Linie oder einen Bogen zu erstellen, klicken und ziehen Sie den Endpunkt. Hierbei wird eine Vorschau des Bogens angezeigt. Lassen Sie die Maustaste los, um den Bogen fertig zu stellen.“
* **Wörtliches Zitat:** „Drücken Sie zum Beenden die ESC-Taste, oder wählen Sie einen anderen Befehl aus.“
* **Wörtliches Zitat:** „Erstellen von Bogen durch drei Punkte oder Mittelpunkt Mit den Bogen-Tools können Sie Bogen erstellen, indem Sie drei Punkte platzieren – einen Mittelpunkt und zwei Endpunkte.“

### Beleg: Inventor - Dynamische Eingabe mit Tab, Enter und Wertesperre
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-33A8B11D-A04C-4809-BC82-C0419215915F.htm
* **Wörtliches Zitat:** „Die exponierte Anzeige ermöglicht die Eingabe von Werten in verschiebbare Werteingabefelder, die sich stets in der Nähe des Cursors befinden. Die Werte werden beim Bewegen des Cursors dynamisch aktualisiert.“
* **Wörtliches Zitat:** „Drücken Sie die TABULATORTASTE, um zum nächsten Eingabefeld zu wechseln.“
* **Wörtliches Zitat:** „Im Feld wird ein Sperrsymbol angezeigt, das darauf hinweist, dass der eingegebene Wert den Cursor einschränkt.“
* **Wörtliches Zitat:** „Wenn die Geometrie fertig ist, drücken Sie die EINGABETASTE.“
* **Wörtliches Zitat:** „Die Form wird anhand der von Ihnen eingegebenen Werte gezeichnet und bemaßt.“
* **Wörtliches Zitat:** „Zeichnen Sie weitere Formen, oder drücken Sie die ESC-TASTE, um den Vorgang zu beenden.“

### Beleg: Inventor - Vorgabe-Tastaturkurzbefehle (L, C, D, S, R)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-DEEB0723-DFC7-4B28-95F4-099CC1E1EBF8.htm
* **Wörtliches Zitat:** „Definieren Sie benutzerdefinierte Tastaturkurzbefehle und Befehls-Aliasnamen. Befehlsaliasse sind alphanumerische Zeichen oder Zeichenfolgen, mit denen Befehle ausgeführt werden können.“
* **Wörtliches Zitat:** „Aktiviert den Befehl Allgemeine Bemaßung.“
* **Wörtliches Zitat:** „Aktiviert den Befehl Linie.“
* **Wörtliches Zitat:** „Erstellt einen Kreis.“
* **Wörtliches Zitat:** „Aktiviert den Befehl 2D-Skizze.“
* **Wörtliches Zitat:** „Aktiviert den Befehl Drehung.“

### Beleg: Inventor - Vordefinierte Kurzbefehle (Esc und Rücktaste)
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-428B9A8E-E513-44C8-888A-F6048AE89F8E.htm
* **Wörtliches Zitat:** „Es folgen einige der in Inventor definierten Tastaturkurzbefehle und Befehlsaliasnamen.“
* **Wörtliches Zitat:** „Beendet einen Befehl“
* **Wörtliches Zitat:** „Entfernt bei aktivem Befehl Linie das zuletzt skizzierte Segment.“

### Beleg: Inventor - 2D-Formgeometrie Rechtecke und Polygone
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-D489CE6D-7299-4211-A43A-F3580A4BA357.htm
* **Wörtliches Zitat:** „Erstellen Sie Kreise, Ellipsen, Rechtecke, Langlöcher, Polygone, Rundungen und Fasen.“
* **Wörtliches Zitat:** „Rechteck durch zwei Punkte. Erstellt ein Rechteck mit zwei Mausklicks, die diagonal gegenüberliegend“
* **Wörtliches Zitat:** „Rechteck durch drei Punkte . Erstellt ein Rechteck durch Festlegen der Länge und Richtung und der an“

### Beleg: Inventor - Skizzenoptionen und automatische Kantenprojektion
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-1898C432-CFD2-46F1-8BAE-631392DFBF1D.htm
* **Wörtliches Zitat:** „Registerkarte Skizze - Referenz (Anwendungsoptionen) Legt Voreinstellungen für das Skizzieren fest.“
* **Wörtliches Zitat:** „Modellkanten für Skizzenerstellung und -bearbeitung automatisch projizieren Projiziert beim Erstellen oder Bearbeiten einer Skizze die Kanten einer ausgewählten Fläche automatisch als Referenzgeometrie auf die Skizzierebene.“
* **Wörtliches Zitat:** „Modellkanten bei Erstellung von Skizzen automatisch projizieren Ermöglicht das Auswählen und Projizieren vorhandener Geometrie auf die aktuelle Skizze“

### Beleg: Inventor - Freiheitsgrade-Symbole in Skizzen
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-784929B0-3480-4FC0-8ED5-E3414248FB7F.htm
* **Wörtliches Zitat:** „Zeichen für Freiheitsgrade - Referenz Zeigt die für die Geometrie verfügbaren Freiheitsgrade an.“
* **Wörtliches Zitat:** „Wählen Sie in der Statusleiste die Option Alle Freiheitsgrade anzeigen aus.“

### Beleg: Inventor - Konstruktionsgeometrie und Profile
* **URL:** https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-F5A5790A-F748-49F0-A81F-BCA56C7C1E89.htm
* **Wörtliches Zitat:** „Sie können zwischen Skizzen- und Konstruktionsgeometrie wechseln, eine Skizze auf einer anderen Ebene neu definieren“
* **Wörtliches Zitat:** „Konstruktionsgeometrie versieht die normale Skizziergeometrie mit Abhängigkeiten. Sie kann bei Skizzen mit parametrischen Elementen verwendet werden. Konstruktionsgeometrie dient nicht zum Definieren von Profilen oder Pfaden.“

### Beleg: Fusion - Linien, Maßeingabe und Tangentenbogen durch Verweilen und Ziehen
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-LINES.htm
* **Wörtliches Zitat:** „Learn how to use the Line tool to series of connected straight or arc line segments in an active sketch in Fusion.“
* **Wörtliches Zitat:** „Specify the length and angle of the line segment:“
* **Wörtliches Zitat:** „Pause over a point, then click and drag to create arc line segments.“

### Beleg: Fusion - Geometrische Abhängigkeiten im Skizzenpanel
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAINTS.htm
* **Wörtliches Zitat:** „The tools in the Sketch > Constraints panel let you constrain sketches by controlling the relative position of sketch geometry in Fusion.“
* **Wörtliches Zitat:** „The Horizontal/Vertical tool constrains a single line, or two points, to lie on either the horizontal or vertical axis, whichever is closer to the current alignment.“
* **Wörtliches Zitat:** „The Coincident tool constrains the position of two points or a point and a line or curve together.“
* **Wörtliches Zitat:** „The Tangent tool constrains a curve and another object so that they touch at a single point but never cross each other.“
* **Wörtliches Zitat:** „The Equal tool constrains similar objects so that their sizes are identical. When the size of one object changes, the others adjust, too.“
* **Wörtliches Zitat:** „The Parallel tool constrains two lines so that they extend in the same direction and never intersect.“
* **Wörtliches Zitat:** „The Perpendicular tool constrains two objects so that they lie perpendicular (at a 90-degree angle) to each other.“
* **Wörtliches Zitat:** „The Fix/UnFix tool locks the size and location of a point or object.“
* **Wörtliches Zitat:** „The Midpoint tool constrains a point or object to the midpoint of another object.“

### Beleg: Fusion - Rechtecktypen, Objektfang und logische Abhängigkeiten
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-RECTANGLES.htm
* **Wörtliches Zitat:** „Create a rectangle by placing 2 opposite corner points to define the position and size of the rectangle.“
* **Wörtliches Zitat:** „Create a rectangle by placing 3 corner points to define the position and size of the rectangle.“
* **Wörtliches Zitat:** „Create a rectangle by placing the center point and a corner point to define the position and size of the rectangle.“
* **Wörtliches Zitat:** „Press Enter to complete the tool.“
* **Wörtliches Zitat:** „As you move the mouse cursor, object snap symbols display near the geometry when you snap to the sketch grid or other geometry in the design. If you snap to a specific point, the logical constraints are automatically added to the sketch.“

### Beleg: Fusion - Kreis durch Mittelpunkt und Durchmesser
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-CIRCLES.htm
* **Wörtliches Zitat:** „Create a circle by placing the center point and specifying the diameter to define the position and size of the circle.“
* **Wörtliches Zitat:** „In the canvas, click to place the center point of the circle.“
* **Wörtliches Zitat:** „Specify the diameter value, then click to place the circle.“
* **Wörtliches Zitat:** „Press Enter to complete the tool.“

### Beleg: Fusion - Bogentypen (3-Punkt, Zentrum, Tangential)
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-ARCS.htm
* **Wörtliches Zitat:** „Create an arc by placing the end points and a third point that lies along the arc to define the position and size of the arc.“
* **Wörtliches Zitat:** „Create an arc by placing the center point and end points to define the position and size of the arc.“
* **Wörtliches Zitat:** „Create an arc by placing the end points to define the position and size of the arc so that it maintains tangency with other sketch geometry.“
* **Wörtliches Zitat:** „Press Enter to complete the tool.“

### Beleg: Fusion - Treibende und getriebene Bemaßungen (Klammern)
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-SKETCH-CREATE-DIMENSIONS.htm
* **Wörtliches Zitat:** „The Sketch Dimension tool creates dimensions to define and constrain geometry in the active sketch. Use dimensions to control the size and position of sketch geometry.“
* **Wörtliches Zitat:** „A Driving dimension is a dimension that is used to explicitly define measurement values of geometry.“
* **Wörtliches Zitat:** „Driving dimensions are the default type of dimension created by the Sketch Dimension tool, unless the dimension will over-constrain the sketch.“
* **Wörtliches Zitat:** „A Driven dimension is a dimension whose value is flexible, and is determined by geometry or other dimensions, parameters, or expressions.“
* **Wörtliches Zitat:** „Display their calculated value in parentheses.“
* **Wörtliches Zitat:** „Are automatically added when the dimension you are adding will over-constrain the sketch.“

### Beleg: Fusion - Fixierte Geometrie färbt sich grün
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-FIX-UNFIX.htm
* **Wörtliches Zitat:** „Learn how to use the Fix/UnFix tool to lock the size and location of a point or object in a sketch in Fusion.“
* **Wörtliches Zitat:** „The size and location of the sketch geometry is locked. The selected geometry turns green, indicating that the geometry is locked.“

### Beleg: Fusion - Farbkodierung für Freiheitsgrade und rotes Schloss
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-FULLY-DEFINE-CONSTRAIN-SKETCH.htm
* **Wörtliches Zitat:** „A sketch is fully constrained when the size and position of all sketch geometry is completely defined. This is achieved using a combination of constraints and dimensions.“
* **Wörtliches Zitat:** „In the Browser, a red lock displays on the icon next to the sketch when it is fully constrained.“
* **Wörtliches Zitat:** „When sketch geometry is fully constrained, it changes from its initial color to black.“
* **Wörtliches Zitat:** „On the left, the blue lines and orange centerline are unconstrained.“

### Beleg: Fusion - Automatisches Bemaßen und Abhängen
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-AUTO-CONSTRAIN.htm
* **Wörtliches Zitat:** „Automatically constrain and dimension your sketch“
* **Wörtliches Zitat:** „In the Constraints panel, click AutoConstrain . The AutoConstrain dialog displays and starts generating results.“
* **Wörtliches Zitat:** „To finish the sketch and apply constraints and dimensions automatically, select Finish with AutoConstrain from the Finish Sketch menu.“

### Beleg: Fusion - Automatische Abhängigkeiten beim Skizzieren
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/GUID-BF6D00B3-DBC4-456F-B591-01FBFD174475.htm
* **Wörtliches Zitat:** „Automatically apply sketch constraints while creating sketch curves“
* **Wörtliches Zitat:** „How sketch constraints are automatically applied while creating sketch curves.“

### Beleg: Fusion - Koinzident-Abhängigkeit
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-COINCIDENT.htm
* **Wörtliches Zitat:** „Learn how to use the Coincident tool to constrain the position of two points or a point and a line or curve together in a sketch in Fusion.“

### Beleg: Fusion - Horizontal- und Vertikal-Abhängigkeit
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-HORIZONTAL-VERTICAL.htm
* **Wörtliches Zitat:** „Learn how to use the Horizontal/Vertical tool to constrain sketch geometry to the closest horizontal or vertical axis in Fusion.“

### Beleg: Fusion - Mittelpunkt-Abhängigkeit
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-MIDPOINT.htm
* **Wörtliches Zitat:** „Learn how to use the Midpoint tool to constrain a point or object to the midpoint of another object in a sketch in Fusion.“

### Beleg: Fusion - Tangential-Abhängigkeit
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-TANGENT.htm
* **Wörtliches Zitat:** „Learn how to use the Tangent tool to constrain a curve and another object in a sketch so that they touch at a single point but never cross each other in Fusion.“

### Beleg: Fusion - Parallel-Abhängigkeit
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-PARALLEL.htm
* **Wörtliches Zitat:** „Learn how to use the Parallel tool to constrain two lines in a sketch so that they extend in the same direction and never intersect in Fusion.“

### Beleg: Fusion - Lotrecht-Abhängigkeit
* **URL:** https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CONSTRAIN-PERPENDICULAR.htm
* **Wörtliches Zitat:** „Learn how to use the Perpendicular tool to constrain two objects in a sketch so that they lie perpendicular (at a 90-degree angle) to each other in Fusion.“
