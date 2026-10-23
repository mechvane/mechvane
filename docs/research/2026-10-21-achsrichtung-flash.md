# Untersuchung der Zylinderachsen-Richtung (`cylinder.axis`) zur Loch-/Zapfen-Klassifizierung

Datum: 2026-10-21  
Bearbeiter: Gemini (Antigravity-CLI)  
Zweig: `gemini/argon-fixes`  
Bezug: Hypothese zu `cylinder.axis` in SolidCraft (Beobachtung von Claude am Dom: Bohrung -Z, Außenmantel +Z)

---

### 1. Fragestellung und Hypothese

In SolidCraft liefert `model.faces` für Zylinderflächen ein Dictionary `cylinder` mit `{axis, origin, radius}`. Bei der Untersuchung des Doms (Ring-Extrusion `join`, Außen-Ø 8 mm, Bohrung Ø 2,5 mm) wurde beobachtet, dass die Achse der inneren Bohrung nach `-Z` zeigte (`[0, 0, -1]`), die der Außenfläche nach `+Z` (`[0, 0, 1]`).

**Hypothese:**  
Richtet SolidCraft die Achsrichtung `cylinder.axis` an der Flächenorientierung bzw. Materialseite aus, sodass sich Innenzylinder (Löcher) und Außenzylinder (Zapfen/Dome/Wellen) rein analytisch und ohne Prüfkörper (`solid.sphere` + `inspect.interference`) unterscheiden lassen?

---

### 2. Versuchsdurchführung (Schritt 1)

Zur systematischen Überprüfung wurde ein automatisierter Testdurchlauf über 21 geometrische Konfigurationen durchgeführt. Dabei wurden sämtliche erzeugten Zylinderflächen erfasst, deren geometrische Eigenschaften (`axis`, `origin`, `radius`, `point`) ausgelesen und mit der bekannten Wahrheit verglichen.

Geprüfte Fälle:
1. `solid.hole` von oben: Durchgangsloch, Sackloch (einfach), Sackloch (`type: drilled` mit 118°-Spitze), Stufenbohrung (`counterbore`), Senkung (`countersink`).
2. `solid.hole` von unten: Durchgangsloch, Sackloch.
3. `solid.cylinder` mit `operation: join` auf Platte (Zapfen).
4. Ring-Extrusion mit `operation: join` (Dom: Außenmantel und Innenbohrung).
5. `solid.extrude` mit `operation: cut` eines Kreises: Durchgangs- und Sackloch.
6. `solid.revolve` eines Profils mit Bohrung (Rohr/Ring: Innenbohrung und Außenmantel) sowie Vollzylinder.
7. Körper nach Drehung um 90° und 180° um die X-Achse.
8. Gespiegelte Körper (`solid.mirror` an der XY-Ebene).
9. Zylinder und Bohrungen entlang X- und Y-Achse statt Z.
10. Geteilte Zylinderflächen (`#1`, `#2`, `#3`).

---

### 3. Versuchsergebnisse

| Fall | Fläche | Wahrheit | `cylinder.axis` | `cylinder.origin` | Radius (mm) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| solid.hole top through | `F2:bore:side:0` | **HOLE** | `[0.0, -0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 2.5 |
| solid.hole top through | `F2:bore:side:1` | **HOLE** | `[-0.0, 0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 2.5 |
| solid.hole top blind (simple) | `F2:bore:side:1` | **HOLE** | `[0.0, -0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 2.5 |
| solid.hole top blind (simple) | `F2:bore:side:0` | **HOLE** | `[-0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 2.5 |
| solid.hole top blind (drilled tip) | `F2:bore:side:1#1` | **HOLE** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 2.5 |
| solid.hole top blind (drilled tip) | `F2:bore:side:1#2` | **HOLE** | `[-0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 2.5 |
| solid.hole top blind (drilled tip) | `F2:bore:side:1#3` | **HOLE** | `[0.0, -0.0, -1.0]` | `[20.0, 20.0, 10.0]` | 2.5 |
| solid.hole top counterbore | `F2:bore:side:0` | **HOLE** | `[0.0, -0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 2.5 |
| solid.hole top counterbore | `F2:bore:side:1` | **HOLE** | `[-0.0, 0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 2.5 |
| solid.hole top counterbore | `F2:cbore:side:0` | **HOLE** | `[0.0, -0.0, -1.0]` | `[20.0, 20.0, 7.0]` | 4.5 |
| solid.hole top counterbore | `F2:cbore:side:1` | **HOLE** | `[-0.0, 0.0, -1.0]` | `[20.0, 20.0, 7.0]` | 4.5 |
| solid.hole top countersink (blind) | `F2:bore:side:0` | **HOLE** | `[0.0, -0.0, -1.0]` | `[20.0, 20.0, 7.5]` | 2.5 |
| solid.hole top countersink (blind) | `F2:bore:side:1` | **HOLE** | `[-0.0, 0.0, -1.0]` | `[20.0, 20.0, 7.5]` | 2.5 |
| solid.hole bottom through | `F2:bore:side:1` | **HOLE** | `[0.0, -0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 2.5 |
| solid.hole bottom through | `F2:bore:side:0` | **HOLE** | `[-0.0, 0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 2.5 |
| solid.hole bottom blind | `F2:bore:side:0` | **HOLE** | `[-0.0, 0.0, 1.0]` | `[20.0, 20.0, 6.0]` | 2.5 |
| solid.hole bottom blind | `F2:bore:side:1` | **HOLE** | `[0.0, -0.0, 1.0]` | `[20.0, 20.0, 6.0]` | 2.5 |
| solid.cylinder join on plate (boss) | `F2:side#1` | **BOSS** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 3.0 |
| solid.cylinder join on plate (boss) | `F2:side#2` | **BOSS** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 3.0 |
| Ring-Extrusion join (Dom) | `F3:side:c1#1` | **BOSS** | `[-0.0, 0.0, 1.0]` | `[20.0, 20.0, 3.0]` | 4.0 |
| Ring-Extrusion join (Dom) | `F3:side:c1#2` | **BOSS** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, 3.0]` | 4.0 |
| Ring-Extrusion join (Dom) | `F3:side:c2#1` | **HOLE** | `[0.0, 0.0, -1.0]` | `[20.0, 20.0, 3.0]` | 1.25 |
| Ring-Extrusion join (Dom) | `F3:side:c2#2` | **HOLE** | `[0.0, 0.0, -1.0]` | `[20.0, 20.0, 3.0]` | 1.25 |
| extrude cut circle through | `F3:side:c1#1` | **HOLE** | `[0.0, 0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 3.0 |
| extrude cut circle through | `F3:side:c1#2` | **HOLE** | `[0.0, 0.0, -1.0]` | `[20.0, 20.0, 0.0]` | 3.0 |
| extrude cut circle blind | `F3:side:c1#2` | **HOLE** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 3.0 |
| extrude cut circle blind | `F3:side:c1#1` | **HOLE** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, 10.0]` | 3.0 |
| revolve profile with bore | `F2:side:l2#1` | **BOSS** | `[-0.0, 0.0, 1.0]` | `[-0.0, 0.0, 0.0]` | 15.0 |
| revolve profile with bore | `F2:side:l4#1` | **HOLE** | `[0.0, 0.0, 1.0]` | `[-0.0, -0.0, -20.0]` | 5.0 |
| revolve profile with bore | `F2:side:l2#2` | **BOSS** | `[0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0]` | 15.0 |
| revolve profile with bore | `F2:side:l4#2` | **HOLE** | `[-0.0, 0.0, 1.0]` | `[0.0, -0.0, -20.0]` | 5.0 |
| revolve profile with bore | `F2:side:l2#3` | **BOSS** | `[0.0, 0.0, 1.0]` | `[-0.0, 0.0, 0.0]` | 15.0 |
| revolve profile with bore | `F2:side:l4#3` | **HOLE** | `[0.0, -0.0, 1.0]` | `[0.0, 0.0, -20.0]` | 5.0 |
| revolve solid cylinder (boss) | `F2:side:l2#1` | **BOSS** | `[0.0, 0.0, 1.0]` | `[-0.0, -0.0, 0.0]` | 10.0 |
| revolve solid cylinder (boss) | `F2:side:l2#2` | **BOSS** | `[0.0, 0.0, 1.0]` | `[0.0, -0.0, 0.0]` | 10.0 |
| revolve solid cylinder (boss) | `F2:side:l2#3` | **BOSS** | `[0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0]` | 10.0 |
| solid.hole rotated 90° X | `F2:bore:side:1` | **HOLE** | `[-0.0, -1.0, 0.0]` | `[20.0, -10.0, 20.0]` | 2.5 |
| solid.hole rotated 90° X | `F2:bore:side:0` | **HOLE** | `[0.0, -1.0, -0.0]` | `[20.0, -10.0, 20.0]` | 2.5 |
| solid.hole rotated 180° X | `F2:bore:side:1` | **HOLE** | `[-0.0, -0.0, -1.0]` | `[20.0, -20.0, -10.0]` | 2.5 |
| solid.hole rotated 180° X | `F2:bore:side:0` | **HOLE** | `[-0.0, 0.0, -1.0]` | `[20.0, -20.0, -10.0]` | 2.5 |
| Dom rotated 90° X | `F3:side:c1#1` | **BOSS** | `[0.0, -1.0, 0.0]` | `[20.0, -3.0, 20.0]` | 4.0 |
| Dom rotated 90° X | `F3:side:c1#2` | **BOSS** | `[0.0, -1.0, 0.0]` | `[20.0, -3.0, 20.0]` | 4.0 |
| Dom rotated 90° X | `F3:side:c2#1` | **HOLE** | `[0.0, 1.0, -0.0]` | `[20.0, -3.0, 20.0]` | 1.25 |
| Dom rotated 90° X | `F3:side:c2#2` | **HOLE** | `[0.0, 1.0, 0.0]` | `[20.0, -3.0, 20.0]` | 1.25 |
| solid.hole mirrored (XY plane) | `F2:bore:side:1` | **HOLE** | `[0.0, -0.0, 1.0]` | `[20.0, 20.0, 20.0]` | 2.5 |
| solid.hole mirrored (XY plane) | `F2:bore:side:0` | **HOLE** | `[-0.0, 0.0, 1.0]` | `[20.0, 20.0, 20.0]` | 2.5 |
| solid.hole mirrored (XY plane) | `F2:bore:side:1@F3.1` | **HOLE** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, -20.0]` | 2.5 |
| solid.hole mirrored (XY plane) | `F2:bore:side:0@F3.1` | **HOLE** | `[0.0, 0.0, 1.0]` | `[20.0, 20.0, -20.0]` | 2.5 |
| solid.cylinder along X (boss) | `F2:side#1` | **BOSS** | `[1.0, 0.0, 0.0]` | `[10.0, 20.0, 20.0]` | 3.0 |
| solid.cylinder along X (boss) | `F2:side#2` | **BOSS** | `[1.0, 0.0, 0.0]` | `[10.0, 20.0, 20.0]` | 3.0 |
| solid.hole along X (hole) | `F2:bore:side:0` | **HOLE** | `[-1.0, 0.0, -0.0]` | `[4.0, 20.0, 20.0]` | 2.5 |
| solid.hole along X (hole) | `F2:bore:side:1` | **HOLE** | `[-1.0, -0.0, 0.0]` | `[4.0, 20.0, 20.0]` | 2.5 |
| solid.cylinder along Y (boss) | `F2:side#1` | **BOSS** | `[0.0, 1.0, 0.0]` | `[20.0, 10.0, 20.0]` | 3.0 |
| solid.cylinder along Y (boss) | `F2:side#2` | **BOSS** | `[0.0, 1.0, 0.0]` | `[20.0, 10.0, 20.0]` | 3.0 |
| solid.hole along Y (hole) | `F2:bore:side:1` | **HOLE** | `[0.0, 1.0, -0.0]` | `[20.0, 10.0, 20.0]` | 2.5 |
| solid.hole along Y (hole) | `F2:bore:side:0` | **HOLE** | `[-0.0, 1.0, 0.0]` | `[20.0, 10.0, 20.0]` | 2.5 |

---

### 4. Analyse und Widerlegung der Hypothese

Die experimentellen Befunde zeigen eindeutig, dass die Hypothese **nicht zutrifft**. Die Achsrichtung `cylinder.axis` richtet sich **nicht** nach der Materialseite oder Flächenorientierung aus:

1. **Gleiche Achse für Loch und Zapfen (Sackloch vs. Zapfen)**:  
   * Ein einfaches Sackloch von oben (`solid.hole top blind`) besitzt die Achse `[0, 0, 1]` (+Z).
   * Ein Zapfen auf einer Platte (`solid.cylinder join`) besitzt exakt dieselbe Achse `[0, 0, 1]` (+Z).
   * Bei einer koaxialen Gegenüberstellung mit gleichem Radius und gleichem Z-Bereich liefern Sackloch und Zapfen identische Werte für `axis` (`+Z`), `radius` und `plane_normal` (`None`). Weder aus `axis`, `origin` noch `point` lässt sich ableiten, auf welcher Seite das Material liegt.

2. **Gegensätzliche Achsen für gleichartige Löcher (Sackloch vs. Durchgangsloch vs. Senkung)**:  
   * Bei `solid.hole` in `-Z`-Richtung:
     * Durchgangsloch: `axis = [0, 0, -1]` (-Z)
     * Einfaches Sackloch: `axis = [0, 0, 1]` (+Z)
     * Senkung (blind countersink): `axis = [0, 0, -1]` (-Z)
   * Gleichartige Bohrungen in derselben Bohrrichtung weisen entgegengesetzte Achsrichtungen auf.

3. **Gleiche Achse für Innenbohrung und Außenmantel bei `revolve`**:  
   * Bei einem Drehteil (`solid.revolve`) mit zentrischer Bohrung haben sowohl der Außenmantel (Zapfen/Außenwand) als auch die Innenwand (Bohrung) die Achse `[0, 0, 1]` (+Z).

4. **Inkonsistenz innerhalb derselben Bohrung bei `type: drilled`**:  
   * Bei einer Bohrung mit Bohrerspitze (`type: drilled`, 118°) wird die Zylinderwand in drei Segmente unterteilt:
     * Segment `#1`: `axis = [0, 0, 1]` (+Z)
     * Segment `#2`: `axis = [0, 0, 1]` (+Z)
     * Segment `#3`: `axis = [0, 0, -1]` (-Z)
   * Selbst innerhalb ein und derselben Bohrung variiert das Vorzeichen der Achse zwischen den Teilflächen.

5. **Ursache der Claude-Beobachtung beim Dom**:  
   * Dass beim Dom die Innenbohrung `-Z` und der Außenmantel `+Z` aufwies, ist ausschließlich eine Eigenschaft der 2D-Profil-Extrusion in SolidCraft: In einer 2D-Skizze mit Kreisring ist die äußere Kontur im Gegenuhrzeigersinn (CCW) parametrisiert, die innere Hohlraum-Kontur im Uhrzeigersinn (CW). Beim linearen Extrudieren entlang `+Z` erzeugt die CW-Kontur eine Zylinderfläche mit Achsenvektor `-Z`. Dies gilt jedoch nur für ringförmige Extrusionen und überträgt sich nicht auf Bohrungen anderer Feature-Typen (`solid.hole`, `solid.revolve`, `extrude cut`).

6. **Invertierung durch nachfolgende boolesche Operationen**:  
   * Wird auf einem Bauteil mit einem Zapfen nachträglich an anderer Stelle ein `solid.hole` ausgeführt, kann die boolesche CSG-Zusammenführung von SolidCraft die Zylinderfläche des bestehenden Zapfens reparametrisieren: Aus `axis = +Z`, `origin.z = 10` wurde im Test `axis = -Z`, `origin.z = 18`.

---

### 5. Schlussfolgerung und Vorgehen (Schritt 2)

* **Regel gilt in allen Fällen?** **Nein.**
* **Code-Änderung**: Gemäß der verbindlichen Vorgabe (*"Nur wenn eine Regel in ALLEN Fällen stimmt: classify_hole_groups auf diese Regel umstellen ... Wenn die Regel nicht in allen Fällen stimmt: Code nicht ändern."*) wurde **keine Änderung am Produktivcode** (`inventa/geometry.py`) vorgenommen.
* Die bestehende, über `edit.checkpoint` / `edit.restore_checkpoint` abgesicherte Prüfkörper-Interferenzprüfung (`solid.sphere` + `inspect.interference`) in Kombination mit dem koaxialen geometrischen Fallback ist die einzige verlässliche Methode zur Innen-/Außen-Klassifizierung in SolidCraft 0.16.2.
* Alle **114 Prüfungen** der Testsuite (`python3 tests/inventa/check.py`) sind unverändert grün (**0 failure(s)**).
