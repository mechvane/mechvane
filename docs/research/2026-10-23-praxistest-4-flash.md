# Praxistest 4: 3D-Druck-Elektronikgehäuse mit inventa (2026-10-23)

Prüfer: Gemini 3.8 Flash (High)  
Branch: `gemini/praxistest-4`  
Testumgebung: SolidCraft-CLI 0.19.0, Python 3.12, Linux  
Workspace: `/tmp/praxis4-ws`  
Reproskripte: `docs/research/2026-10-23-praxistest-4-skripte/`  

---

## 1. Zusammenfassung & Gebaute Baugruppe

Im Praxistest 4 wurde ein vollständiges 3D-Druck-Elektronikgehäuse inklusive Unterbaugruppe und Schraubverbindungen ausschließlich über die Python-Schnittstelle von inventa konstruiert, montiert, analysiert, modifiziert und validiert:

1. **Bauteile:**
   - **Gehäuseunterteil:** $100 \times 70 \times 35\text{ mm}$, Wandstärke $2{,}5\text{ mm}$ (`gehaeuse_unterteil.solidcraft`, parametrisiert mit `L`, `W`, `H`, `wall`, `dx = L/2 - 15 mm`, `dy = W/2 - 15 mm`), mit vier massiven Domen $\varnothing\,8\text{ mm}$ für Ruthex-Gewindeeinsätze M3/M4. Volumen: $50.845{,}93\text{ mm}^3$.
   - **Deckel:** $100 \times 70 \times 3\text{ mm}$ (`deckel.solidcraft`, parametrisiert mit `L`, `W`, `T`). Volumen: $21.000{,}00\text{ mm}^3$.
   - **Platine:** $80 \times 50 \times 1{,}6\text{ mm}$ (`platine.solidcraft`) mit vier Durchgangsbohrungen $\varnothing\,3{,}4\text{ mm}$ bei $(\pm 35, \pm 20)\text{ mm}$. Volumen: $6.341{,}90\text{ mm}^3$.
   - **Abstandsbolzen:** Vier zylindrische Bolzen $\varnothing\,6\text{ mm}$, Höhe $10\text{ mm}$ (`abstandsbolzen.solidcraft`) mit Durchgangsbohrung $\varnothing\,3{,}4\text{ mm}$. Volumen: je $191{,}93\text{ mm}^3$.
2. **Unterbaugruppe (`platine_unterbaugruppe.solidcraft`):**
   - Platine fixiert (`grounded=True`).
   - Vier Abstandsbolzen koaxial an den Platinenbohrungen ausgerichtet und mit vier starren Gelenken (`Bolzen1Joint` bis `Bolzen4Joint`, `type="rigid"`) an der Platinenunterseite verankert.
3. **Hauptbaugruppe (`elektronikgehaeuse.solidcraft`):**
   - Gehäuseunterteil fixiert (`grounded=True`).
   - Unterbaugruppe (`Elektronik:1`) eingefügt und per `server.add_joint` starr auf die Gehäusedome gesetzt (`ElektronikAufDome`, verknüpft Zylinderfläche von Dom1 mit Zylinderfläche von Bolzen1).
   - Deckel (`Deckel:1`) auf das Gehäuse gesetzt ($Z = 35\text{ mm}$).
   - **Ruthex M3 Verschraubung:** Vier Gewindeeinsätze Ruthex M3 mit ISO 4762 M3 Schrauben im $2 \times 2$-Rechteckmuster ($70 \times 40\text{ mm}$) durch Deckel und Gehäusedome (`bolted_connection`, `use_insert=True`, `counterbore=False`, `parts=['Deckel:1', 'Gehaeuse:1']`). Schraubenlänge $8{,}0\text{ mm}$, Einschmelztiefe $5{,}7\text{ mm}$, 4 Einschmelz-Interferenzen à $23{,}10\text{ mm}^3$.
4. **Prüfung & Analyse (Schritt 2):**
   - **Konstruktionsregeln (`check_design`, Profil `fdm_0.4`):** Gehäuseunterteil und Deckel erhalten `verdict: ok`. Platine und Abstandsbolzen schlagen bei `hole_edge_distance` fehl ($5{,}00\text{ mm} < 5{,}10\text{ mm}$ bzw. $3{,}00\text{ mm} < 5{,}10\text{ mm}$, $1{,}5 \times d$).
   - **Semantische Abfragen (`find`):** Findet alle 16 zylindrischen Flächen am Gehäuse sowie Bohrungen an Platine und Hauptbaugruppe (20 Bohrungen). Identifiziert massive Außendome fälschlicherweise als Bohrungen (Befund 2).
5. **Änderung an Ort und Stelle & Weiterentwicklung (Schritt 3):**
   - **In-Place-Verlängerung:** Gehäuseunterteil direkt im Baugruppenkontext per `server.edit_in_place` geöffnet und parametrisch von $100\text{ mm}$ auf $110\text{ mm}$ verlängert (`parameters.change L = 110 mm`).
   - **Baugruppenaktualisierung (`update_links` & `repair`):** Dom 1 wandert parametrisch von $X = 35\text{ mm}$ nach $X = 40\text{ mm}$. Durch Aufruf von `server.update_links(repair=True)` folgt die gesamte Elektronik-Unterbaugruppe der Domverschiebung ($X = 40{,}00\text{ mm}$, Verschiebung $+5{,}00\text{ mm}$).
   - **Verschraubung M3 $\to$ M4:** `edit_bolted_connection` passt die Verschraubung atomar auf M4 und das neue Raster $80 \times 40\text{ mm}$ an (Bohrungsdurchmesser wächst auf $\varnothing\,5{,}6\text{ mm}$, Tiefe auf $9{,}1\text{ mm}$, M4-Schrauben/Ruthex-Einsätze werden neu generiert).
   - **Löschen der Verschraubung:** `delete_bolted_connection` entfernt alle 4 Ruthex M4 Einsätze, Schrauben, 8 Gelenke und die 8 Bohrungsfeatures in Deckel und Gehäuse vollständig.
   - **Neuanlage Sacklochverschraubung:** Versuch mit `blind_material='PLA'` dokumentiert (Befund 4), Ausführung mit `blind_material='plastic'` erzeugt 4 Sacklochverschraubungen mit Kernloch $\varnothing\,2{,}5\text{ mm}$, Tiefe $11{,}0\text{ mm}$ und Schraubenlänge $12{,}0\text{ mm}$.
6. **Endprüfung & Persistenz (Schritt 4):**
   - `inspect.interference`: 6 berechtigte Interferenzpaare (4x Schraubengewinde-Überdeckung im M3-Kernloch Plastik, 2x Bolzenauflage).
   - `check_joints`: Alle 18 Gelenke intakt (`status: ok`).
   - Persistenz: Dokument gespeichert, geschlossen und neu geöffnet (`save_document`, `close_document`, `open_document`); alle 18 Gelenke und die Verschraubung bleiben vollständig erhalten.
   - Headless Screenshot erfolgreich gerendert: `/tmp/praxis4-ws/elektronikgehaeuse.png` ($960 \times 600$, $381{,}9\text{ KB}$).
   - Vollständiger Ablauf in `docs/research/2026-10-23-praxistest-4-skripte/praxistest_4_ablauf.py` erfolgreich in 165 Sekunden durchgelaufen.

---

## 2. Übersicht der Befunde nach Schwere

| Nr. | Schwere | Bereich | Kurzbezeichnung | Repro-Skript |
|---|---|---|---|---|
| **1** | **Hoch** | `bolted` | `counterbore=True` scheitert bei üblichen $3\text{ mm}$ 3D-Druck-Deckeln (DIN 974-1 Senktiefe $\ge$ Plattendicke) | `01_senkung_tiefe_ueberschreitet_deckeldicke.py` |
| **2** | **Hoch** | `geometry` / `find` | `classify_hole_groups` stuft massive Außendome als Bohrungen ein | `02_falschklassifikation_dome_als_bohrungen.py` |
| **3** | **Mittel** | `check_design` | Wandstärkenprüfung ignoriert zylindrische Domwände (Fallback auf Bauteil-Boundingbox) | `03_wandstaerkenpruefung_ignoriert_zylindrische_domwand.py` |
| **4** | **Mittel** | `hole_tables` | Werkstoffaliase für 3D-Druck (`PLA`, `PETG`, `ABS`) fehlen in `_MATERIAL_ALIASES` | `04_fehlende_werkstoffaliase_pla_petg.py` |
| **5** | **Mittel** | `bolted` | `bolted_connection` schlägt ohne `parts`-Filter bei Baugruppen mit Innenkomponenten fehl | `05_raycast_durchdringung_unterbaugruppe_ohne_parts.py` |
| **6** | **Niedrig** | `query` / `server` | `find` liefert für Bauteile in Unterbaugruppen unvollständige Occurrence-Pfade | `06_find_unterbaugruppen_pfad_unvollstaendig.py` |
| **7** | **Hoch** | `bolted` / `inplace` | Bolted-Connection-Bohrungen sind statisch numerisch (Gelenkabrisse bei parametrischer Änderung) | `07_bolted_connection_bohrungen_nicht_parametrisch_abriss.py` |
| **8** | **Mittel** | `links` / `server` | `update_links(repair=True)` ignoriert `origin_lost` (repariert nur `moved`), fehlendes `repair_joint`-Tool | `08_update_links_ignoriert_origin_lost.py` |

---

## 3. Detaillierte Befundberichte

### Befund 1 (Hoch): `counterbore=True` scheitert bei üblichen $3\text{ mm}$ 3D-Druck-Deckeln

- **Symptom:** Der Aufruf von `bolted_connection` mit Senkung (`counterbore=True`, `size="M3"`) auf einem $3{,}0\text{ mm}$ dicken Deckel bricht mit einem harten `ValueError` ab:
  ```
  ValueError: counterbore depth (3.4 mm) exceeds or equals top plate thickness (3.0 mm); reduce counterbore depth or increase plate thickness
  ```
- **Ursache:** In `inventa/hole_tables.py` (Zeile 108–117) ist für Flachsenkungen nach DIN 974-1 Reihe 1 für M3 eine feste Senktiefe von $t_1 = 3{,}4\text{ mm}$ (für M4: $4{,}4\text{ mm}$, für M5: $5{,}4\text{ mm}$) hartcodiert. In `inventa/bolted.py` (Zeile 422–424) prüft `bolted_connection`:
  ```python
  if cb_depth >= top_thick - TOL:
      raise ValueError(f"counterbore depth ({cb_depth} mm) exceeds or equals top plate thickness ({top_thick} mm)...")
  ```
  Da 3D-Druck-Gehäusedeckel standardmäßig $2{,}5\text{ mm}$ bis $3{,}0\text{ mm}$ dick sind (bei $0{,}4\text{ mm}$ Düse typischerweise 6–8 Schichten), scheitert jede M3- oder M4-Flachsenkung. Es gibt aktuell weder einen Parameter `counterbore_depth` zur manuellen Begrenzung der Senktiefe (Teilsenkung) noch Unterstützung für DIN 7991 / ISO 10642 Senkschrauben (Kegelsenkung $90^\circ$).
- **Workaround:** Im Praxistest musste `counterbore=False` gewählt werden (Zylinderkopf liegt auf dem Deckel auf).
- **Empfohlene Lösung:**
  1. Parameter `counterbore_depth: float | None = None` in `bolted_connection` erlauben, um die Senktiefe explizit vorzugeben.
  2. Unterstützung für ISO 10642 / DIN 7991 Senkkopfschrauben mit $90^\circ$-Kegelsenkung hinzufügen, deren Senktiefe bei M3 nur $1{,}7\text{ mm}$ beträgt.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/01_senkung_tiefe_ueberschreitet_deckeldicke.py`

---

### Befund 2 (Hoch): `classify_hole_groups` stuft massive Außendome als Bohrungen ein

- **Symptom:** Der Aufruf `server.find(doc, "holes")` meldet an einem Gehäuseunterteil mit 4 massiven Schraubdomen ($\varnothing\,8\text{ mm}$, Vollmaterial) 8 Bohrungen statt 4: Sowohl die Sacklöcher als auch die massiven Zylinderaußenwände der Dome werden als Bohrungen aufgelistet. In `check_design` führt dies dazu, dass der Abstand der Dom-Außenwand zum Plattenrand als "Lochrandabstand" geprüft wird.
- **Ursache:** In `inventa/geometry.py` (`classify_hole_groups`, Zeile 109–137) prüft der SolidCraft-Algorithmus, ob ein Zylinder eine Bohrung ist, indem ein Testpunkt $0{,}1\text{ mm}$ radial in die Zylinderwand eingetaucht und per Raycast getestet wird, ob Material vorliegt (`has_mat = len(hits) % 2 == 1`). Bei massiven Domen, die einteilig aus dem Gehäuseboden herauswachsen (`operation: join`), liefert der Raycast-Test in SolidCraft 0 Kollisionen mit den Boundary-Flächen (`len(hits) == 0` $\to$ gerade $\to$ `has_mat = False`), woraus die Heuristik `is_hole = not has_mat` fälschlicherweise `is_hole = True` schließt.
- **Auswirkung:**
  - `find("holes")` listet massive Zylinderkörper als Bohrungen.
  - `check_design` wendet `hole_edge_distance` und `hole_diameter` auf massive Montagezapfen und Dome an.
- **Workaround:** Im Skript müssen gefundene "Bohrungen" anhand ihres Durchmessers und ihrer Flächenorientierung gefiltert werden.
- **Empfohlene Lösung:** Die Materialprüfung für Zylinder sollte den Flächennormalenvektor der Zylinderfläche auswerten: Bei einer Innenfläche (Bohrung) zeigt die Flächennormale radial zur Zylinderachse hin; bei einem Außendom zeigt die Flächennormale radial von der Zylinderachse nach außen weg.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/02_falschklassifikation_dome_als_bohrungen.py`

---

### Befund 3 (Mittel): Wandstärkenprüfung ignoriert zylindrische Domwände

- **Symptom:** An einem Gehäuse mit dünnwandigen Schraubdomen (z. B. Außendurchmesser $\varnothing\,4{,}8\text{ mm}$ mit Kernloch $\varnothing\,4{,}0\text{ mm}$, resultierende Zylinderwandstärke nur $0{,}4\text{ mm}$) meldet `check_design("fdm_0.4")` für `min_wall_thickness` fälschlicherweise `verdict: ok` mit Wandstärken von $12{,}6\text{ mm}$ bis $13{,}0\text{ mm}$.
- **Ursache:** In `inventa/design_rules.py` (`_check_body`, Zeile 163–208) filtert der Wandstärken-Algorithmus `side_faces` ausschließlich nach planaren Flächen:
  ```python
  side_faces = [f for f in faces if f.get("plane_normal") is not None and abs(f["plane_normal"][2]) < 0.1]
  ```
  Zylindrische Mantelflächen besitzen kein `plane_normal` und werden vollständig ignoriert. Bei der Abstandsmessung der Bohrungswand zu den Außenflächen des Körpers stehen daher keine zylindrischen Außenflächen zur Verfügung. Die Funktion greift auf die Bounding-Box des Gesamtkörpers zurück (`bbox_dist = 13.0 mm`), wodurch hochkritische, im 3D-Druck sofort abreißende Domwandstärken unbemerkt als "ok" durchgewunken werden.
- **Empfohlene Lösung:** Zylindrische Mantelflächen in die Nachbarschaftsprüfung einbeziehen: Bei koaxialen Zylindern entspricht die Wandstärke exakt $(R_{\text{aussen}} - R_{\text{innen}})$.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/03_wandstaerkenpruefung_ignoriert_zylindrische_domwand.py`

---

### Befund 4 (Mittel): Werkstoffaliase für 3D-Druck (`PLA`, `PETG`, `ABS`) fehlen in `_MATERIAL_ALIASES`

- **Symptom:** Der Aufruf `bolted_connection(..., connection_type="blind", blind_material="PLA")` schlägt mit `ValueError` fehl:
  ```
  ValueError: unsupported blind material 'PLA' (available: steel, cast_iron, alu, alu_cast, alu_wrought, brass, plastic)
  ```
- **Ursache:** In `inventa/hole_tables.py` (Zeile 30–42) mappt das Dictionary `_MATERIAL_ALIASES` nur englische und deutsche generische Bezeichnungen (`plastic`, `kunststoff`, `alu`, `stahl`). Die im 3D-Druck allgegenwärtigen Filamente (`PLA`, `PETG`, `ABS`, `ASA`, `Nylon`) sind nicht hinterlegt, obwohl für Kunststoffe ohnehin die VDI 2230 Richtwerte für Thermoplaste ($m_{\text{eff}} = 2{,}5 \times d$) herangezogen werden.
- **Workaround:** Der Aufrufer muss explizit den generischen Begriff `blind_material="plastic"` verwenden.
- **Empfohlene Lösung:** Ergänzung von `_MATERIAL_ALIASES` in `hole_tables.py`:
  ```python
  "pla": "plastic",
  "petg": "plastic",
  "abs": "plastic",
  "asa": "plastic",
  ```
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/04_fehlende_werkstoffaliase_pla_petg.py`

---

### Befund 5 (Mittel): `bolted_connection` schlägt ohne `parts`-Filter bei Baugruppen mit Innenkomponenten fehl

- **Symptom:** Wird in einer Gehäusebaugruppe mit innenliegender Elektronik-Unterbaugruppe (Platine und 4 Abstandsbolzen) eine Deckelverschraubung im Rechteckmuster angelegt, bricht `bolted_connection` ab:
  ```
  ValueError: pattern position 1 intersects different parts: ['Deckel:1', 'Bolzen2:1', 'Gehaeuse:1'] vs ['Deckel:1', 'Gehaeuse:1']
  ```
  oder (wenn der Raycast durch Platinenbohrungen schießt):
  ```
  ValueError: required screw length 42.7 mm exceeds maximum preferred length 30 mm for ISO 4762 M3; penetrated parts: ['Deckel:1', 'Gehaeuse:1', 'Platine:1']
  ```
- **Ursache:** In `inventa/bolted.py` (Zeile 520–524) verlangt der Algorithmus für Musterpositionen, dass an jeder Position exakt dieselbe geordnete Liste von Occurrences durchdrungen wird:
  ```python
  if penetrated != first_penetrated:
      raise ValueError(f"pattern position {idx} intersects different parts: ...")
  ```
  Wenn im Gehäuseinneren Bauteile (wie einzelne Bolzen `Bolzen1:1`, `Bolzen2:1` etc.) liegen, trifft der Raycast unterschiedliche Occurrences oder durchschlägt nach der Gehäusewand noch die darunterliegende Platine.
- **Workaround:** Dem Aufruf muss zwingend `parts=['Deckel:1', 'Gehaeuse:1']` übergeben werden, um den Raycast strikt auf die beiden Verschraubungspartner zu begrenzen.
- **Empfohlene Lösung:** Wenn `parts` nicht angegeben ist, sollte `bolted_connection` bei Mustern nicht hart abbrechen, sondern den gemeinsamen Schnitt der durchdrungenen Strukturteile bilden oder in der Fehlermeldung darauf hinweisen, dass `parts` bei innenliegenden Baugruppen Pflicht ist.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/05_raycast_durchdringung_unterbaugruppe_ohne_parts.py`

---

### Befund 6 (Niedrig): `find` liefert für Bauteile in Unterbaugruppen unvollständige Occurrence-Pfade

- **Symptom:** Wird `server.find(assembly, "holes")` auf eine Hauptbaugruppe mit Unterbaugruppen aufgerufen, enthalten die Treffer als `occurrence` lediglich den unqualifizierten Blattnamen (z. B. `'Platine:1'`) statt des vollen Pfades (z. B. `'Elektronik:1/Platine:1'`).
- **Ursache:** In `inventa/query.py` (`_find_in_session`, Zeile 190–205) wird `occurrence["name"]` aus `component.list` übernommen. In SolidCraft ist `occurrence["name"]` der Name innerhalb der Baugruppenebene, während `occurrence.get("path")` den hierarchischen Pfad enthält.
- **Auswirkung:** Wird der zurückgegebene Occurrence-Name direkt an Folgewerkzeuge wie `server.add_joint` übergeben, schlägt die Auflösung fehl oder erfordert unsaubere Fallbacks.
- **Workaround:** Vor der Weiterverwendung prüfen, ob der Name einen Schrägstrich `/` enthält, bzw. `occurrence.get("path")` bevorzugen.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/06_find_unterbaugruppen_pfad_unvollstaendig.py`

---

### Befund 7 (Hoch): Bolted-Connection-Bohrungen sind statisch numerisch (Gelenkabrisse bei parametrischer Änderung)

- **Symptom:** Wird ein Gehäuse nach Erstellung einer `bolted_connection` per `edit_in_place` parametrisch vergrößert ($L = 100 \to 110\text{ mm}$), wandern die Gehäusedome parametrisch mit ($dx = L/2 - 15$). Die von `bolted_connection` geschnittenen Gewindeeinsatz-Bohrungen verbleiben jedoch an den alten statischen Koordinaten ($X = 35\text{ mm}$). Beim anschließenden `finish_edit` und `update_links` melden alle 4 Ruthex-Einsatzgelenke sofort `status: origin_lost` oder `face_missing`: Die Bohrungen sind von den Domen abgerissen!
- **Ursache:** `bolted_connection` platziert Bohrungsfeatures als statische numerische Werte (`base: [x, y, z]`), anstatt parametrische Ausdrücke oder Skizzenabhängigkeiten an das Zielbauteil zu binden.
- **Auswirkung:** Das Kernversprechen der parametrischen CAD-Modellierung ("Änderungen an Ort und Stelle propagieren durch die Baugruppe") wird für alle Schraubverbindungen gebrochen. Nach jeder Geometrieänderung müssen Verschraubungen manuell per `edit_bolted_connection` mit neuen Koordinaten aktualisiert oder per `delete_bolted_connection` gelöscht und neu angelegt werden.
- **Empfohlene Lösung:**
  1. `edit_in_place` und `update_links` sollten erkennen, wenn Bohrungen zu einer `bolted_connection` gehören, und eine klare Warnung ausgeben: *"Bohrungen von bolted_conn_1 sind statisch positioniert; bitte edit_bolted_connection aufrufen"*.
  2. Perspektivisch: Möglichkeit bieten, `placement` in `bolted_connection` relativ zu Referenzflächen/Features zu verankern.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/07_bolted_connection_bohrungen_nicht_parametrisch_abriss.py`

---

### Befund 8 (Mittel): `update_links(repair=True)` ignoriert `origin_lost` (repariert nur `moved`)

- **Symptom:** Wenn sich die Topologie eines Bauteils durch neue Features (z. B. Bohrungen) ändert und der SolidCraft-Solver beim Neuladen temporär den lokalen Koordinatenursprung einer Gelenkseite verliert (`frame_a = None`), klassifiziert `links.check` das Gelenk als `status: 'origin_lost'`. Ein anschließender Aufruf von `server.update_links(assembly, repair=True)` repariert das Gelenk jedoch **nicht** (es bleibt `origin_lost`). Ruft man dagegen intern direkt `links.repair(ws, doc, joint)` auf, wird das Gelenk auf der nach wie vor vorhandenen benannten Fläche fehlerfrei neu erstellt (`status: ok`).
- **Ursache:** In `inventa/links.py` (Zeile 860–862) iteriert `update_links` ausschließlich über Gelenke mit `status == "moved"`:
  ```python
  if repair_moved:
      for joint in sorted({r["joint"] for r in report if r["status"] == "moved"}):
          after = repair(ws, doc, joint)
  ```
  Gelenke mit `status == "origin_lost"` werden strikt ignoriert, obwohl `repair()` auch für diese Gelenke voll funktionsfähig ist. Darüber hinaus bietet `inventa/server.py` dem Aufrufer kein direktes MCP-Tool wie `repair_joint(assembly, joint)` an.
- **Workaround:** Im Python-Skript muss `links.repair(ws, doc, joint)` direkt aufgerufen werden, um das Gelenk wiederherzustellen.
- **Empfohlene Lösung:**
  1. In `update_links` auch Gelenke mit `status == "origin_lost"` zur Reparatur zulassen, sofern die verankerte Fläche im Bauteil existiert.
  2. Ein MCP-Tool `repair_joint(assembly: str, joint: str)` in `inventa/server.py` bereitstellen.
- **Repro-Skript:** `docs/research/2026-10-23-praxistest-4-skripte/08_update_links_ignoriert_origin_lost.py`

---

## 4. Fazit & Empfehlungen für FDM-Elektronikgehäuse

Der Praxistest 4 zeigt eindrucksvoll, wie leistungsfähig das Zusammenspiel von `inventa` und `SolidCraft` bei 3D-Druck-Konstruktionen bereits ist:
- **Echte Baugruppenhierarchie:** Unterbaugruppen (Platine + 4 Bolzen) lassen sich sauber kapseln und als bewegliche bzw. starre Einheit in übergeordnete Gehäuse einbinden.
- **Verschraubungslebenszyklus:** Ruthex-Gewindeeinsätze für FDM werden mit realen Einschmelztiefen und Bohrungstabellen unterstützt. `edit_bolted_connection` (M3 $\to$ M4) und `delete_bolted_connection` stellen das Bauteilvolumen ohne Geometriereste exakt wieder her.
- **Headless-Rendering:** `server.screenshot` erzeugt gestochen scharfe Isometrie-Renderings der fertigen Konstruktion direkt auf dem Headless-Server.

Die wichtigsten Hebel zur Beseitigung der verbleibenden Reibungspunkte:
1. **Flachsenkungstiefe flexibilisieren & Senkkopfschrauben ergänzen (Befund 1):** Essentiell für Standard-3D-Druck-Deckel ($2{,}5\dots 3\text{ mm}$).
2. **Flächennormalen-Check in `classify_hole_groups` (Befund 2):** Verhindert, dass massive Außendome als Bohrungen fehlinterpretiert werden.
3. **Zylinderflächen in Wandstärkenprüfung einbeziehen (Befund 3):** Entscheidend, um Sollbruchstellen an dünnwandigen Schraubdomen vor dem Druck zuverlässig aufzudecken.
4. **Werkstoffaliase `PLA`/`PETG`/`ABS` hinterlegen (Befund 4):** Standard im FDM-Bereich.
5. **Gelenkreparatur auf `origin_lost` erweitern (Befund 8):** Schließt die Lücke bei der automatischen Wiederherstellung von Baugruppengelenken.
