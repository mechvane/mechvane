# Praxistest 3: Lagerbock-Baugruppe mit inventa (2026-10-23)

Prüfer: Gemini 3.8 Flash (High)  
Branch: `gemini/praxistest-3`  
Testumgebung: SolidCraft-CLI 0.19.0, Python 3.12, Linux  
Workspace: `/tmp/praxis-ws`  
Reproskripte: `docs/research/2026-10-23-praxistest-3-skripte/`  

---

## 1. Zusammenfassung & Gebaute Baugruppe

Im Praxistest 3 wurde eine vollständige Lagerbock-Baugruppe ausschließlich über die Python-Schnittstelle von inventa konstruiert, montiert, analysiert und modifiziert:

1. **Bauteile:**
   - **Grundplatte:** $120 \times 80 \times 10\text{ mm}$ (`grundplatte.solidcraft`, parametrisiert mit `L`, `W`, `T`).
   - **Lagerbock:** Gestufter Stehlager-Körper (`lagerbock.solidcraft`) mit Basisflansch ($90 \times 60 \times 14\text{ mm}$), zentralem Lagerturm ($50 \times 24 \times 40\text{ mm}$, parametrisiert mit `tower_h`) und durchgehender Bohrung $\varnothing\,22\text{ mm}$ für ein Rillenkugellager 608 nach DIN 625 ($Z = 34\text{ mm}$).
   - **Kugellager 608:** Rillenkugellager nach DIN 625 ($d = 8\text{ mm}$, $D = 22\text{ mm}$, $B = 7\text{ mm}$).
   - **Deckel:** Axialer Lagerschild/Abschlussdeckel ($50 \times 8 \times 40\text{ mm}$, `deckel.solidcraft`) mit Durchgangsbohrung $\varnothing\,12\text{ mm}$ für die rotierende Welle.
2. **Baugruppe (`lagerbock_baugruppe.solidcraft`):**
   - Grundplatte fixiert (`grounded=True`).
   - Lagerbock auf die Grundplatte gesetzt ($Z = 10\text{ mm}$).
   - Kugellager 608 koaxial in die $\varnothing\,22$-Bohrung des Lagerbocks montiert ($90^\circ$ gedreht).
   - Deckel stirnseitig vor den Lagerturm gesetzt ($Y = -12\dots -20\text{ mm}$).
   - **Grundplattenverschraubung:** 4 Schrauben ISO 4762 M6 im $2 \times 2$-Rechteckmuster ($64 \times 40\text{ mm}$ Spacing) durch den Flansch in die Grundplatte (`bolted_connection`, `counterbore=False`, Scheiben ISO 7089 und Muttern ISO 4032).
   - **Deckelverschraubung:** 2 Schrauben ISO 4762 M5 im $2 \times 1$-Muster ($32\text{ mm}$ Spacing) horizontal durch den Deckel als Sacklochverschraubung in den Lagerbock (`bolted_connection`, `connection_type="blind"`, `blind_material="alu"`).
3. **Analyse & Modifikation:**
   - **Semantische Abfragen (`find`):** Alle Bohrungen in den Bauteilen (4x M6 Durchgang in Grundplatte; 1x Lager Ø22, 4x M6 Durchgang, 2x M5 Sackloch im Lagerbock; 1x Welle Ø12, 2x M5 Durchgang im Deckel) sowie in der Baugruppe (23 zylindrische Flächen in Weltkoordinaten mit Occurrence-Zuordnung) fehlerfrei identifiziert.
   - **Konstruktionsregeln (`check_design`):** Prüfung aller Bauteile mit Profil `fdm_0.4`. Grundplatte `verdict: ok`. Bei Deckel und Lagerbock wurden systematische Falschalarme aufgedeckt (Befunde 2 und 6).
   - **Bearbeiten an Ort und Stelle (`edit_in_place`):** Lagerbock direkt im Baugruppenkontext geöffnet, Höhe des Lagerturms parametrisch von $40\text{ mm}$ auf $45\text{ mm}$ vergrößert (`parameters.change tower_h = 45 mm`), per `finish_edit` gespeichert und Baugruppe aktualisiert.
   - **Gelenküberwachung (`update_links`):** Erkennt bei 2 Schraubengelenken an der Grundplatte eine Verschiebung der STEP-Flächennamen (`status: moved` nach #3330).
   - **Verschraubung Deckel löschen:** `delete_bolted_connection` entfernt alle M5-Normteile, Gelenke und die erzeugten Bohrungsfeatures in Deckel und Lagerbock; Volumen beider Bauteile wird exakt wiederhergestellt.
   - **Verschraubung Grundplatte ändern:** `edit_bolted_connection` ändert die $2 \times 2$-Verschraubung atomar von M6 auf M8 (Bohrungen in Flansch und Grundplatte wachsen auf $\varnothing\,9{,}0\text{ mm}$, M8-Schrauben/Scheiben/Muttern werden neu generiert und koaxial verknüpft).
4. **Endprüfung:**
   - `inspect.interference`: `count == 0` (vollkommen kollisionsfrei, 0 Durchdringungen).
   - `links.check`: Alle 24 verbleibenden Gelenke grün (`status: ok`).
   - Gesamtlaufzeit des vollständigen Ablaufs: ca. 93 Sekunden.

---

## 2. Übersicht der Befunde nach Schwere

| Nr. | Schwere | Bereich | Kurzbezeichnung | Repro-Skript |
|---|---|---|---|---|
| **1** | **Mittel** | `standard_parts` | Normteil DIN 625 608 fehlt im Lager-Katalog | `01_fehlendes_normteil_din625_608.py` |
| **2** | **Hoch** | `check_design` | Falschalarm & negative Wandstärke bei horizontalen Bohrungen | `02_falschalarm_check_design_horizontale_bohrung.py` |
| **3** | **Hoch** | `bolted` | Keine Bauteileinschränkung in `bolted_connection` (Raycast-Durchschuss) | `03_bolted_connection_keine_bauteilbegrenzung_durchschuss.py` |
| **4** | **Hoch** | `bolted` | Falsche Gelenkausrichtung ($180^\circ$ Flip) bei `counterbore=True` im Muster | `04_bolted_counterbore_pattern_screw_flip_bug.py` |
| **5** | **Hoch** | `bolted` / SolidCraft | Boolean Refusal bei `edit_bolted_connection` nach Sackloch mit Bohrspitze | `05_edit_bolted_connection_nach_sackloch_boolean_refusal.py` |
| **6** | **Mittel** | `check_design` | Falschalarm bei `hole_edge_distance` an inneren Absätzen/Stufen | `06_falschalarm_check_design_innere_stufen.py` |
| **7** | **Niedrig** | `server` / API | Inkonsistente Status-Felder (`verdict` vs. `status`) in `check_design` | - (Dokumentation) |

---

## 3. Detaillierte Befundberichte

### Befund 1 (Mittel): Normteil DIN 625 608 fehlt im Standardteile-Katalog
- **Symptom:** Der Aufruf `standard_parts.create(ws, 'DIN 625', '608')` bzw. MCP-Tool `standard_part(norm="DIN 625", size="608")` schlägt mit `ValueError: unknown bearing size '608' for DIN 625 (available: 6000, 6001, 6002, 6003, 6004, 6005)` fehl.
- **Ursache:** In `inventa/standard_parts.py` ist die Tabelle `BEARINGS_6000` (Zeile 79–86) ausschließlich mit den Standardgrößen 6000 bis 6005 der ISO 15 Maßreihe 10 hinterlegt. Das Miniatur-/Skate-Lager 608 ($d=8\text{ mm}, D=22\text{ mm}, B=7\text{ mm}$) nach DIN 625-1 (Maßreihe 18 / Miniatur) fehlt. Gerade für 3D-gedruckte Baugruppen, Leitrollen, Spindeln und Lagerböcke ist das 608-Lager jedoch das weltweit verbreitetste Standardbauteil.
- **Workaround:** Manuelles Anlegen des Bauteils `DIN_625_608.solidcraft` mit den Abmessungen $8 \times 22 \times 7\text{ mm}$ und Zuweisung der DIN 625-Metadaten.
- **Reproduktion:** `PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/01_fehlendes_normteil_din625_608.py`

---

### Befund 2 (Hoch): Falschalarm und negative Wandstärke in `check_design` bei horizontalen Bohrungen
- **Symptom:** Bei Bauteilen mit horizontalen Bohrungen (Achse entlang Y oder X, z. B. Lagerbohrung $\varnothing\,22$ oder Wellendurchlass $\varnothing\,12$) meldet `check_design` `verdict: fail` mit absurder negativer Wandstärke:
  `Wall thickness to edge is -1.00 mm < 1.20 mm for hole Ø 22.0 mm`
  und schlägt fälschlich bei `hole_edge_distance` Alarm (`10.0 mm < 33.0 mm`), obwohl die reale Wandstärke in X und Z über $14\text{ mm}$ beträgt.
- **Ursache:** In `inventa/design_rules.py` (Zeile 160–164) berechnet `_check_body` den Randabstand jeder Bohrung pauschal aus der Bounding Box in X und Y:
  ```python
  dx = min(abs(c[0] - bbox["min"][0]), abs(c[0] - bbox["max"][0]))
  dy = min(abs(c[1] - bbox["min"][1]), abs(c[1] - bbox["max"][1]))
  min_dist_box = min(dx, dy)
  e_edge = min(min_dist_box, min_dist_face)
  w_edge = e_edge - r
  ```
  Liegt die Bohrungsachse entlang Y, ist `dy` der Abstand vom Bohrungsmittelpunkt zur Eintritts-/Austrittsfläche der Bohrung (z. B. $10\text{ mm}$ in einer $20\text{ mm}$ dicken Wand). `min_dist_box` wählt `dy = 10 mm`, wodurch $w_{\text{edge}} = 10{,}0 - 11{,}0 = -1{,}0\text{ mm}$ wird! Der Algorithmus nimmt fälschlicherweise an, dass jede Bohrung in Z-Richtung verläuft.
- **Empfehlung:** `min_dist_box` darf nur Achsen senkrecht zur Bohrungsachse berücksichtigen: Bei einer Bohrung entlang Y müssen nur $dx$ und $dz$ zur Auswertung herangezogen werden ($dz = \min(|c_z - z_{\min}|, |c_z - z_{\max}|)$).
- **Reproduktion:** `PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/02_falschalarm_check_design_horizontale_bohrung.py`

---

### Befund 3 (Hoch): Keine Bauteileinschränkung in `bolted_connection` (Raycast-Durchschuss)
- **Symptom:** Bei übereinander montierten Komponenten (z. B. Deckel auf Lagerbock auf Grundplatte) kann der Deckel nicht vertikal per Sackloch am Lagerbock verschraubt werden. Der Aufruf bricht mit:
  `ValueError: required screw length 54.6 mm exceeds maximum preferred length 50 mm for ISO 4762 M5`
  ab bzw. schneidet die Sacklochbohrung durch den gesamten Lagerbock hindurch in die darunterliegende Grundplatte.
- **Ursache:** `bolted_connection` und `preview_bolted_connection` akzeptieren keine Parameter wie `parts` oder `occurrences`. Die Funktion `_find_penetrations` schießt einen unendlichen Strahl in die Baugruppe und sammelt *alle* geschnittenen Bauteile. Bei 3 Bauteilen im Strahl (`[Deckel, Lagerbock, Grundplatte]`) interpretiert `bolted.py` das letzte Bauteil (Grundplatte) als Sacklochträger und alle vorherigen Bauteile (Deckel + Lagerbock = $50\text{ mm}$) als Klemmlänge.
- **Lösung im Test:** Der Deckel wurde stirnseitig (horizontal in +Y-Richtung) am Lagerbock befestigt, sodass der Strahl hinter dem Lagerbock ins Leere läuft und die Grundplatte unberührt bleibt.
- **Empfehlung:** Optionaler Parameter `occurrences: list[str]` oder `limit_parts: int` in `bolted_connection`, damit Verschraubungen gezielt auf benachbarte Bauteilpaare begrenzt werden können.
- **Reproduktion:** `PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/03_bolted_connection_keine_bauteilbegrenzung_durchschuss.py`

---

### Befund 4 (Hoch): Falsche Gelenkausrichtung ($180^\circ$ Flip) bei `counterbore=True` im Muster
- **Symptom:** Bei Ausführung von `bolted_connection` mit Senkung (`counterbore=True`) in einem Rechteckmuster (z. B. $2 \times 2$) wird eine der Schrauben (Instanz 4) um $180^\circ$ verkehrt herum eingebaut (Schaft nach außen/oben statt in die Bohrung). `inspect.interference` meldet daraufhin $151{,}7\text{ mm}^3$ und $13{,}2\text{ mm}^3$ schwere Kollisionen mit den Platten.
- **Ursache:** In `inventa/bolted.py` (Zeile 881) ist beim Anlegen des `ScrewJoint` der Parameter `"flip": True` fest einprogrammiert:
  ```python
  screw_jp = {
      "type": "rigid",
      "name": screw_jname,
      "flip": True,
      "a": {"occurrence": screw_target_occ, "circle": p_screw_bearing},
      "b": {"occurrence": inst_screw, "circle": p_screw_bearing},
  }
  ```
  `p_screw_bearing` ist der Mittelpunkt der Senkstufen-Kreiskante. SolidCraft teilt Zylinderkanten in zwei Halbkanten (`:side:0` und `:side:1`), deren lokale Orientierungsachsen entgegengesetzt liegen (`z = +1.0` bzw. `z = -1.0`). Je nachdem, welche Halbkante SolidCraft am Mittelpunkt zuerst auflöst, hat der Gelenkrahmen `fa_z = +1.0` oder `fa_z = -1.0`. Durch das starre `"flip": True` wird die Schraube bei umgekehrter Kantenachse auf den Kopf gestellt! In den bestehenden Tests `check.py` wurde das Rechteckmuster nur mit `counterbore=False` geprüft, weshalb der Fehler unbemerkt blieb.
- **Lösung im Test:** Nutzung von `counterbore=False` für das Rechteckmuster der Grundplatte ($4\times$ M6).
- **Empfehlung:** `bolted.py` muss nach dem Erzeugen des Gelenks prüfen, ob die Ausrichtung des Schraubenschafts mit `dir_k` übereinstimmt ($\mathbf{z}_{\text{screw}} \cdot \mathbf{d} = 1$). Falls $\mathbf{z}_{\text{screw}} \cdot \mathbf{d} = -1$, muss `joint.edit(joint, flip=not current_flip)` aufgerufen werden.
- **Reproduktion:** `PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/04_bolted_counterbore_pattern_screw_flip_bug.py`

---

### Befund 5 (Hoch): Boolean Refusal bei `edit_bolted_connection` nach Sackloch mit Bohrspitze
- **Symptom:** Führt man `edit_bolted_connection` (z. B. M6 auf M8 an der Grundplatte) an einem Lagerbock durch, der bereits eine Sacklochverschraubung (M5 Deckel) enthält und zuvor per `edit_in_place` vergrößert wurde, bricht SolidCraft mit einem internen CSG/Boolean-Fehler ab:
  `SolidCraftError: the cut could not be computed reliably: it would change the body away from the tool, at (-16.699, 4.041, 33.973) (outside the tool's region)`
- **Ursache:** Die Fehlerkoordinate $(-16.699, 4.041, 33.973)$ liegt exakt an der facettierten Kegelspitze des M5-Sacklochs (`F8:bore:side:2#1`), weit entfernt von den M8-Bohrungen ($X=-32, Y=-20, Z=14$). `bolted.py` legt Sacklöcher mit `"type": "drilled"`, `"tip_angle": "118 deg"` an. Wenn der Verlauf zurückgerollt wird, um die M6-Bohrungen zu löschen und M8 neu zu schneiden, scheitert der Parasolid/B-Rep-Kernel an der spitzen Topologie der Sacklochspitze.
- **Lösung im Test:** Löscht man die Sacklochverbindung per `delete_bolted_connection` *vor* der Ausführung von `edit_bolted_connection M6 -> M8`, läuft die Änderung fehlerfrei durch und erzeugt eine vollkommen kollisionsfreie Baugruppe (`Interferenz: 0`, alle 24 Gelenke `ok`).
- **Empfehlung:** Sacklöcher im Bolted-Modul wahlweise als Flachsenkung (`type: "simple"`) modellieren oder vor Boolean-Operationen Geometrie-Checkpoints setzen.
- **Reproduktion:** `PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/05_edit_bolted_connection_nach_sackloch_boolean_refusal.py`

---

### Befund 6 (Mittel): Falschalarm in `check_design` bei inneren Absätzen/Stufen
- **Symptom:** Bei gestuften Körpern (Lagerbock mit Grundflansch bis $X = -45\text{ mm}$ und zentralem Lagerturm ab $X = -25\text{ mm}$) beanstandet `check_design` die Flanschbohrung bei $X = -32\text{ mm}$ mit:
  `Hole edge distance 7.00 mm < 9.90 mm (1.5 × d for Ø 6.6 mm) to face F2:-x`
  als unzulässig (`verdict: fail`).
- **Ursache:** `_check_body` sammelt alle Planarflächen, deren Normale senkrecht zur Bohrungsachse steht, und misst den orthogonalen Abstand zur unendlichen Ebene dieser Fläche. Die vertikale Stufenwand des Turms (`F2:-x` bei $X = -25$) wird dabei wie ein freier Bauteilaußenrand behandelt, obwohl nach innen Vollmaterial anschließt und der tatsächliche freie Rand nach außen bei $X = -45$ liegt ($13\text{ mm} \ge 9{,}9\text{ mm}$).
- **Empfehlung:** Prüfung, ob die Flächennormale vom Bohrungsmittelpunkt weg zeigt (Außenfläche) oder zum Bohrungsmittelpunkt hin (innere Stufe/Taschenwand).
- **Reproduktion:** `PYTHONPATH=. python3 docs/research/2026-10-23-praxistest-3-skripte/06_falschalarm_check_design_innere_stufen.py`

---

### Befund 7 (Niedrig): Inkonsistente Status-Felder in `check_design` (`verdict` vs. `status`)
- **Symptom:** In `inventa/server.py` liefert `check_design` ein Dictionary mit dem Top-Level-Schlüssel `verdict` (`"ok"` | `"warn"` | `"fail"`), während alle Unterregeln und die übrigen inventa-Funktionen (`links.check`, `bolted`, `browser`) den Standard-Schlüssel `status` verwenden.
- **Reibungspunkt:** Bei programmatischer Nutzung führt `res["status"]` zu einem unerwarteten `KeyError: 'status'`.
- **Empfehlung:** Zusätzlich zu `verdict` auch ein Top-Level-Feld `status` mit identischem Wert zurückgeben.

---

## 4. Fazit & Bewertung des Werkzeugkastens

Die inventa-Schicht meistert komplexe Baugruppen-Workflows über Dateigrenzen hinweg (Normteilgenerierung, Gelenküberwachung nach #3330, automatisches Bohren, atomares Editieren und Löschen von Verbindungspaketen) bereits auf hohem Niveau:
- **Hervorragend:** Die semantischen Abfragen (`find`) liefern in Bauteilen wie Baugruppen exakte geometrische Merkmale ohne teure `body_topology`-Aufrufe.
- **Hervorragend:** `edit_in_place` und `finish_edit` verwalten Multi-Dokument-Transaktionen und Abhängigkeiten nahtlos; verschobene STEP-Flächen werden zuverlässig erkannt.
- **Kritisch für den Alltagseinsatz:** Die geometrischen Annahmen in `check_design` (strikte Z-Ausrichtung von Bohrungen) und die unkonditionierte Gelenkausrichtung (`flip: True`) in `bolted_connection` bei Senkungen im Muster stellen reale Stolperfallen dar, die den Anwender zu Workarounds zwingen. Alle 6 reproduzierten Schwachstellen lassen sich mit den bereitgestellten Testskripten deterministisch validieren und beheben.
