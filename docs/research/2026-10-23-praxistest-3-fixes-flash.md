# Praxistest 3: Fehlerbehebungen und Analysebericht

Datum: 23. Oktober 2026  
Autor: Gemini 3.8 Flash  
Repository: `inventa` (Branch: `gemini/praxistest-3-fixes`)

---

## 1. Übersicht

Im Praxistest 3 wurden 7 Befunde identifiziert, die die CAD- und Normteil-Funktionalitäten von `inventa` sowie das Kernel-Verhalten von `solidcraft-cli` betrafen. Dieser Bericht dokumentiert die Behebung der Befunde 1, 2, 3, 4, 6 und 7 sowie die tiefgehende Ursachenanalyse von Befund 5 inklusive eines reinen SolidCraft-Minimalreproduktionsskripts für die Upstream-Meldung.

Alle bestehenden und neuen Tests in der Test-Suite laufen vollständig fehlerfrei durch:
* `tests/inventa/check.py`: 192 Prüfungen erfolgreich (0 Fehler)
* `tests/reference/check.py`: 58 Prüfungen erfolgreich (0 Fehler)
* Reproduktionsskripte 01–04 und 06: Alle Fehler erfolgreich abgestellt bzw. verifiziert.

---

## 2. Befund 1: Ergänzung DIN 625 um Miniatur- und 60er-Lager

### Problem
In `inventa/standard_parts.py` enthielt die Tabelle `BEARINGS_6000` nur die Größen 6000 bis 6005. Häufig im 3D-Druck und Modellbau benötigte Lager wie das 608 (Inlineskate- / Voron-Standard) sowie Miniaturlager (623–627, 609) fehlten. Zudem fehlte der Kantenabstand $r$ in der Tabellen- und Metadaten-Spezifikation.

### Behebung
* Ergänzung von `BEARINGS_6000` in `inventa/standard_parts.py` um:
  * **623**: $d=3$, $D=10$, $B=4$, $r=0.15$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-623)
  * **624**: $d=4$, $D=13$, $B=5$, $r=0.20$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-624)
  * **625**: $d=5$, $D=16$, $B=5$, $r=0.30$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-625)
  * **626**: $d=6$, $D=19$, $B=6$, $r=0.30$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-626)
  * **627**: $d=7$, $D=22$, $B=7$, $r=0.30$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-627)
  * **608**: $d=8$, $D=22$, $B=7$, $r=0.30$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-608)
  * **609**: $d=9$, $D=24$, $B=7$, $r=0.30$ mm (SKF: https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-609)
* Alle Einträge sind im Code direkt mit den entsprechenden SKF-Katalog-URLs belegt.
* DIN 625 erfasst nun auch den Kantenabstand $r$ als Parameter im CAD-Modell sowie in den Metadaten.

---

## 3. Befund 2 & 6: Bohrungsachsen-Erkennung und Randabstände bei gestuften Teilen in `design_rules`

### Problem
1. **Befund 2 (Horizontale Bohrungen)**: `inventa/design_rules.py` nahm bei der Randabstandsmessung stets an, dass Bohrungen parallel zur Z-Achse verlaufen. Der minimale Bounding-Box-Abstand wurde fest über `min(dx, dy)` ermittelt. Bei einer Bohrung entlang der Y-Achse war `dy` der Abstand entlang der Bohrungsachse zu den Eintrittsflächen. Dies führte dazu, dass $w_{\text{edge}} = e_{\text{edge}} - r$ negativ wurde (z. B. $-1.0$ mm) und ein unberechtigter Falschalarm für Mindestwandstärke ausgelöst wurde.
2. **Befund 6 (Innere Stufen/Absätze)**: Der Abstand wurde zu allen parallelen Planarflächen des Körpers gemessen, ohne zu prüfen, ob die Fläche die Bohrung überhaupt lateral begrenzt. Bei einem Flansch mit aufgesetztem Turm wurde die Stufenwand des Turms als Rand gewertet, obwohl sie in Bohrungsrichtung gar nicht mit der Bohrung überlappt.

### Behebung
* In `inventa/design_rules.py` (`_check_body`):
  * **Echte Achse aus Bohrungszylinder**: Die Bohrungsachse `axis` wird direkt aus den Zylinderdaten `h["axis"]` entnommen (`axis = g.unit(h.get("axis", [0, 0, 1]))`).
  * **Orthogonale Bounding-Box-Auswertung**: `min_dist_box` betrachtet nur noch Koordinatenachsen senkrecht zur Bohrungsachse (`abs(axis[i]) < 0.5`).
  * **Filter für laterale Begrenzungsflächen**:
    1. Die Fläche muss nach außen zeigen (`signed_dist = g.dot(g.sub(sf["point"], c), n) > -1e-4`).
    2. Die Fläche muss die Bohrung in Achsrichtung überlappen (`overlap = min(h_s_max, sf_s_max) - max(h_s_min, sf_s_min) >= 1e-3`).
    3. Die Bohrung muss transversal im Bereich der Fläche liegen (`u_sf_min - r <= u_hole <= u_sf_max + r`).
  * **Keine negative Wandstärke**: $w_{\text{edge}} = \max(0.0, \min(min\_dist\_box, min\_dist\_face) - r)$.

---

## 4. Befund 3: Bauteilbegrenzung `parts` in `bolted_connection`

### Problem
`bolted_connection` und `preview_bolted_connection` boten keinen Parameter, um festzulegen, welche Bauteile verbunden werden sollen. Ein Strahl schnitt alle getroffenen Bauteile der Baugruppe (z. B. Deckel $\to$ Lagerbock $\to$ Grundplatte), was bei Sacklochverbindungen dazu führte, dass die Grundplatte ungewollt als unterstes Bauteil interpretiert wurde und die Klemmlänge überschritten wurde.

### Behebung
* `preview_bolted_connection`, `bolted_connection` und `edit_bolted_connection` unterstützen das optionale Argument `parts: list[str] | None = None`.
* Durchdringungen werden mit `_filter_penetrations_by_parts(penetrations, parts)` gefiltert. Der Strahl stoppt nach dem letzten genannten Teil.
* Ist `parts` nicht gesetzt und die Schraubenlänge überschreitet das Maximum, nennt die Fehlermeldung nun alle durchdrungenen Bauteile und weist explizit auf `parts` hin:
  `"...; penetrated parts: ['Deckel:1', 'Lagerbock:1', 'Grundplatte:1']; use 'parts' to restrict bolted connection to specific occurrences"`
* Das MCP-Tool in `inventa/server.py` sowie die Dokumentation `docs/inventa-mcp.md` wurden um den Parameter `parts` erweitert.

---

## 5. Befund 4: Dynamische Schraubengelenk-Ausrichtung bei Senkung und Mustern

### Problem
In `inventa/bolted.py` war beim Erstellen des `ScrewJoint` das Attribut `"flip": True` fest verdrahtet. SolidCraft zerlegt Zylinderkanten in zwei Halbkreise (`:side:0` und `:side:1`), deren lokale Z-Achsen entgegengesetzt orientiert sind (`+Z` vs. `-Z`). Bei Mustern (z. B. 2x2 Rechteckmuster oder Teilkreismuster) wählte SolidCraft an einzelnen Instanzen (z. B. Instanz 4) die Halbkreiskante mit umgekehrter Z-Achse. Durch das starre `flip: True` wurde diese Schraube um 180° verkehrt herum eingebaut (Schaft nach oben, Kopf in die Platte), was massive Kollisionen zur Folge hatte (`inspect.interference count > 0`).

### Behebung
* Die Ausrichtung von `ScrewJoint` wird nun für jede Musterinstanz dynamisch bestimmt:
  * Die Z-Achse der gewählten Kreiskante im Weltkoordinatensystem (`fa_z = g.unit(g.apply_dir(t_target, circle_z))`) wird gegen die Strahlrichtung `dir_k` geprüft.
  * `flip = bool(g.dot(fa_z, dir_k) < 0)`.
  * Nach dem Platzieren wird zusätzlich verifiziert, dass der Schraubenschaft in Strahlrichtung zeigt (`g.dot(shank_w, dir_k) >= 0.5`).
* Hinweis zu `HeadWasherJoint`: Die Unterlegscheibe behält ihr ursprüngliches `flip: True`, da sie auf der Planarfläche aufliegt und bei Invertierung ihre Fase und Kante falsch ausrichten würde.

---

## 6. Befund 5: Ursachenanalyse des Kernel-Schnittfehlers bei Sacklochspitzen nach `edit_in_place`

### Analyse
Bei Praxistest 3 scheiterte ein Schnitt an einem Lagerbock nach `edit_in_place`, wenn an der gleichen Geometrie Sacklöcher mit 118°-Bohrerspitzen existierten. Der SolidCraft-Kernel verweigerte den Befehl mit:
`"error: step 9 (solid.hole): the cut could not be computed reliably: it would change the body away from the tool, at (-16.699, 4.041, 33.973) (outside the tool's region)"`.

#### Ursache im SolidCraft-Kernel (CAD Engine)
1. **Flächen-Perturbation bei Koinzidenz**: Wenn eine Durchgangsbohrung (`solid.hole`) bündig mit der Unterseite eines Körpers ($Z = 0$) abschließt, wendet der SolidCraft-Kernel eine Flächenstörungs-Routine an (`face_shift_mm ~ 2.82 mm`), um coplanare Flächen bei der booleschen Differenz zu trennen.
2. **Koinzidenz-Reevaluierung nach Parameteränderung**: Nach einer Parameteränderung (`parameters.change`) und Neu-Evaluierung des Features-Trees führt diese Kernel-Perturbation dazu, dass sich Facetten und Scheitelpunkte an den 118°-Kegelspitzen benachbarter Sacklöcher bei $(-16.699, 4.041, 33.973)$ geometrisch minimal verschieben.
3. **Plausibilitätsprüfung des Kernels**: SolidCraft vergleicht den Körper vor und nach dem Schnitt. Erkennt der Kernel, dass sich Geometrie außerhalb des Einflussbereichs des Schnittwerkzeugs (tool bbox / bounding sphere) verändert hat, bricht er die Operation vorsorglich mit der obigen Fehlermeldung ab.

### Minimales SolidCraft-Skript (ohne inventa)
Der Fehler lässt sich in einem minimalen SolidCraft-Skript (9 Schritte, reine SolidCraft-Befehle, ausführbar mit `solidcraft-cli run`) reproduzieren:

```json
{
  "commands": [
    {"command": "parameters.add", "params": {"name": "tower_h", "expression": "40 mm"}},
    {"command": "solid.box", "params": {"length": 90, "width": 60, "height": 14, "corner": [-45.0, -30.0, 0.0], "name": "Base"}},
    {"command": "solid.box", "params": {"length": 50, "width": 24, "height": "tower_h", "corner": [-25.0, -12.0, 14.0], "operation": "join", "name": "Tower"}},
    {"command": "solid.cylinder", "params": {"diameter": 22, "height": 28, "base": [0, -14, 34], "axis": [0, 1, 0], "operation": "cut", "name": "Bore"}},
    {"command": "solid.hole", "params": {"position": [-16, -12, 34], "direction": [0, 1, 0], "diameter": 4.2, "depth": 15.2, "type": "drilled", "tip_angle": "118 deg", "thread": "M5", "name": "Hole_M5_Blind_1"}},
    {"command": "solid.hole", "params": {"position": [16, -12, 34], "direction": [0, 1, 0], "diameter": 4.2, "depth": 15.2, "type": "drilled", "tip_angle": "118 deg", "thread": "M5", "name": "Hole_M5_Blind_2"}},
    {"command": "parameters.change", "params": {"name": "tower_h", "expression": "45 mm"}},
    {"command": "solid.hole", "params": {"position": [-32, -20, 14], "direction": [0, 0, -1], "diameter": 9.0, "depth": 14, "name": "Hole_M8_1"}},
    {"command": "solid.hole", "params": {"position": [-32, 20, 14], "direction": [0, 0, -1], "diameter": 9.0, "depth": 14, "name": "Hole_M8_2"}}
  ]
}
```

Ausführung via:
`solidcraft-cli run --batch minimal_repro.json`
Ausgabe:
`error: step 9 (solid.hole): the cut could not be computed reliably: it would change the body away from the tool, at (-16.699, 4.041, 33.973) (outside the tool's region)`

Dieses Skript eignet sich direkt als Testcase für den Upstream-Bugreport an SolidCraft.

---

## 7. Befund 7: `status`-Feld in `check_design`

### Problem
`check_design` lieferte auf oberster Ebene nur das Feld `verdict`. Zur Konsistenz mit den Einzelregeln (wo `status` verwendet wird) und anderen MCP-Tools wurde ein Feld `status` erwartet.

### Behebung
In `inventa/design_rules.py` liefert `check()` nun auf oberster Ebene sowohl `"status": verdict` als auch weiterhin `"verdict": verdict` (Abwärtskompatibilität).

---

## 8. Testergebnisse

### Test-Suiten
* **`tests/inventa/check.py`**:
  * 192/192 Prüfungen erfolgreich (`0 failure(s)`).
  * Beinhaltet die neue Testfunktion `praxistest_3_fixes_checks` mit dedizierten Tests für alle Befunde (1, 2, 3, 4, 6, 7).
* **`tests/reference/check.py`**:
  * 58/58 Prüfungen erfolgreich (`0 failure(s)`).
  * Keinerlei Regressionen in Bauteilvolumina, Bounding Boxes oder Gelenkberechnungen.

### Verifikation der Praxis-Skripte 01–04 und 06
* **Skript 01** (`01_fehlendes_normteil_din625_608.py`):
  Erzeugt erfolgreich `DIN 625 608` ($d=8, D=22, B=7, r=0.3$). Die frühere `ValueError`-Exception tritt nicht mehr auf.
* **Skript 02** (`02_falschalarm_check_design_horizontale_bohrung.py`):
  `min_wall_thickness` meldet Status `ok` mit Wandstärke $14.00$ mm $\ge 1.20$ mm. Die frühere Falschmeldung einer negativen Wandstärke ($-1.0$ mm) ist behoben.
* **Skript 03** (`03_bolted_connection_keine_bauteilbegrenzung_durchschuss.py`):
  Ohne `parts` nennt die Exception nun die penetrierten Teile (`Deckel:1`, `Lagerbock:1`, `Grundplatte:1`) und verweist auf `parts`. Mit `parts=['Deckel:1', 'Lagerbock:1']` wird die Verbindung sauber nur durch Deckel und Lagerbock gebohrt; die Grundplatte bleibt unberührt.
* **Skript 04** (`04_bolted_counterbore_pattern_screw_flip_bug.py`):
  Alle Schrauben in der Senkung werden mit dem Schaft in Strahlrichtung ausgerichtet. `inspect.interference` meldet `count: 0` (keinerlei Kollision).
* **Skript 06** (`06_falschalarm_check_design_innere_stufen.py`):
  `hole_edge_distance` meldet Status `ok` ($10.00$ mm $\ge 9.90$ mm). Der innere Turmabsatz wird nicht mehr fälschlich als Kante gewertet.
