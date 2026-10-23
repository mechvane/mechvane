# Bericht: Behebung der Befunde aus Praxistest 4 (inventa)

**Datum:** 2026-10-23  
**Prüfer:** Gemini 3.8 Flash (High)  
**Branch:** `gemini/praxistest-4-fixes`  
**Workspace:** `/root/repos/inventa-praxis4fix`  
**Referenz-Testlauf:** Praxistest 4 (`docs/research/2026-10-23-praxistest-4-flash.md`)  

---

## 1. Zusammenfassung

Im Praxistest 4 wurden bei der Konstruktion eines 3D-Druck-Elektronikgehäuses acht Befunde identifiziert. Die bestätigten Befunde 1–4, 6 und 8 wurden im vorliegenden Branch systematisch analysiert, vor der Änderung mit einem fehlschlagenden Test in `tests/inventa/check.py` abgesichert und anschließend vollständig behoben. Für Befund 7 wurde wie beauftragt ein detaillierter Architektur- und Lösungskonzeptentwurf verfasst.

Alle Testsuiten (`tests/inventa/check.py` und `tests/reference/check.py`) sind vollständig grün (0 Fehler). Alle betroffenen Reproskripte (01–04, 06, 08) wurden erneut ausgeführt und bestätigen die Behebung.

---

## 2. Detaillierte Maßnahmen je Befund

### Befund 2: Falschklassifikation massiver Dome als Bohrungen (`geometry.py`)
- **Ursache:** In `geometry.classify_hole_groups` wurde ein Prüfpunkt radial *innerhalb* des Zylinderradius platziert und `inspect.interference` aufgerufen. Da SolidCraft bei Körpern, die vollständig ineinander liegen (keine Oberflächen-Grenzflächenüberschneidung), 0 Interferenzen meldete, folgerte der alte Algorithmus fälschlich `has_mat = False` und stufte massive Zapfen/Dome als Bohrungen ein.
- **Lösung:**
  1. Falls SolidCraft Flächennormalen für die Zylinderfläche liefert, wird geprüft, ob die Normale zur Achse hin (Bohrung) oder von der Achse weg (Zapfen) zeigt.
  2. Robuste Materialseitenprüfung: Platzierung eines Prüfpunkts knapp *außerhalb* des Zylinderradius ($r_{\text{test}} = r + \delta$ mit $\delta = \min(0{,}1, 0{,}05 \cdot r)$) und Ausführung eines kleinen Testschnitts (`solid.sphere`, `operation: cut`, $r_{\text{probe}} = 0{,}04\text{ mm}$) innerhalb eines Checkpoints. Schneidet der Schnitt Material (`changed_bodies`), liegt außen Material vor $\to$ es handelt sich um eine Innenbohrung (`is_hole = True`). Schneidet der Schnitt Luft (`changed_bodies == []`), liegt außen freier Raum vor $\to$ es handelt sich um einen massiven Dom/Zapfen (`is_hole = False`).
- **Verifikation:**
  - Test `praxistest 4 / finding 2: massive boss/dome is not classified as hole` in `tests/inventa/check.py`: **ok**.
  - Reproskript `02_falschklassifikation_dome_als_bohrungen.py`: Dom Ø 8,0 mm wird nicht mehr als Bohrung gelistet, nur das echte Loch Ø 4,0 mm bleibt erhalten.

### Befund 3: Wandstärkenprüfung ignoriert zylindrische Domwände (`design_rules.py`)
- **Ursache:** In `_check_body` filterte die Abstandsmessung für Lochränder ausschließlich nach Planarflächen (`plane_normal`). Zylindrische Mantelflächen besitzen kein `plane_normal` und wurden ignoriert. Bei zylindrischen Domen fiel der Algorithmus auf die ferne Bounding-Box des Bodens zurück ($13\text{ mm}$) und winkte hochkritische, im 3D-Druck sofort abreißende Domwandstärken ($0{,}4\text{ mm}$) fälschlich mit `ok` durch.
- **Lösung:**
  1. `_extract_holes` erfasst nun neben den Bohrungen auch alle externen Zylinderflächen (`ext_cylinders`).
  2. In `_check_body` werden koaxiale Hohlzylinder (Schraubdome mit Bohrung) identifiziert: Die Wandstärke berechnet sich direkt als $W_{\text{dom}} = R_{\text{außen}} - r_{\text{innen}}$.
  3. Bei nicht-koaxialen Außenwänden wird der minimale Abstand zur Zylinderwand ermittelt und in die Wandstärkenprüfung einbezogen.
  4. Unterschreitet die resultierende Domwandstärke den Schwellenwert des Profils (z. B. $1{,}20\text{ mm}$ bei `fdm_0.4`), meldet `min_wall_thickness` zuverlässig `status: fail` mit dem exakten Wert (z. B. $0{,}40\text{ mm}$).
- **Verifikation:**
  - Test `praxistest 4 / finding 3: wall thickness check flags thin cylindrical boss wall` in `tests/inventa/check.py`: **ok**.
  - Reproskript `03_wandstaerkenpruefung_ignoriert_zylindrische_domwand.py`: `min_wall_thickness` wechselt von fälschlichem `ok` (13,0 mm) auf berechtigtes `fail` (0,40 mm).

### Befund 4: Werkstoffaliase für 3D-Druck (`PLA`, `PETG`, `ABS`) in Sacklöchern (`hole_tables.py`)
- **Prüfung der Datenquellen:** Im gesamten Repository existieren keine belegten Norm-Einschraubtiefen für metrische Maschinengewinde direkt in FDM-PLA/PETG/ABS (VDI 2230 gilt für Spritzguss-Thermoplaste; Direktverschraubung von Maschinenschrauben in FDM ist wegen Schichtspaltung unzuverlässig). Werte wurden daher richtlinienkonform **nicht** erfunden.
- **Lösung:**
  In `hole_tables.normalize_material` wird bei Eingabe von 3D-Druck-Werkstoffen (`PLA`, `PETG`, `ABS`, `ASA`) eine präzise, konstruktiv hilfreiche Fehlermeldung ausgegeben:
  ```
  ValueError: unsupported blind material 'PLA': direct metric threads in 3D-printed plastics (PLA) have no verified thread engagement depth; recommend heat-set inserts (use_insert=True) or thread-forming screws instead (available: steel, cast_iron, alu, alu_cast, alu_wrought, brass, plastic)
  ```
- **Verifikation:**
  - Test `praxistest 4 / finding 4: unsupported blind material PLA suggests use_insert or thread-forming screws`: **ok**.
  - Reproskript `04_fehlende_werkstoffaliase_pla_petg.py`: läuft fehlerfrei durch (`exit code 0`).

### Befund 1: Fehlermeldung bei Flachsenkung tiefer als oberstes Bauteil (`bolted.py`, `ROADMAP.md`)
- **Ursache:** Bei Standard-3D-Druck-Deckeln ($3\text{ mm}$) überschreitet die DIN 974-1 Senktiefe für M3 ($3{,}4\text{ mm}$) die Plattendicke.
- **Lösung:**
  1. In `preview_bolted_connection` vor jeder Bauteiländerung klare Fehlermeldung mit konkretem Lösungsvorschlag:
     ```
     counterbore depth (3.4 mm) exceeds or equals top plate thickness (3.0 mm); use counterbore=False to place screw head on top of the plate without counterbore
     ```
  2. Keine Teilsenkung erfunden.
  3. Senkkopfschrauben nach ISO 10642 mit $90^\circ$-Kegelsenkung als offener Punkt in `ROADMAP.md` unter dem Abschnitt *Bohrungsassistent mit Verschraubung* eingetragen.
- **Verifikation:**
  - Test `praxistest 4 / finding 1: counterbore exceeding top plate thickness suggests counterbore=False`: **ok**.
  - Reproskript `01_senkung_tiefe_ueberschreitet_deckeldicke.py`: meldet erwarteten Fehler inklusive Vorschlag (`exit code 0`).

### Befund 6: Voller Occurrence-Pfad für Bauteile in Unterbaugruppen (`query.py`, `links.py`)
- **Ursache:** `_collect_bodies` in `query.py` übernahm nur den einfachen Namen der Blatt-Occurrence (`"Platte:1"`) statt des vollen Baugruppenpfads (`"SubUnit:1/Platte:1"`).
- **Lösung:**
  1. In `links._occurrences` wird über `full_path()` die vollständige Elternkette bis zur Baugruppenwurzel aufgebaut und im Feld `"path"` hinterlegt.
  2. In `query._collect_bodies` wird `occ.get("path") or occ["name"]` als Occurrence-Bezeichnung an alle Abfrageergebnisse (`faces`, `edges`, `holes`) übergeben. Der Filter `where={"occurrence": ...}` akzeptiert sowohl den Blattnamen als auch den vollen Pfad.
  3. Geprüft, dass `server.add_joint` mit dem gelieferten Pfad (`"SubUnit:1/Platte:1"`) über `links.resolve_occurrences` einwandfrei funktioniert und intakte Gelenke (`status: ok`) erzeugt.
- **Verifikation:**
  - Test `praxistest 4 / finding 6: find in assembly returns full occurrence path for subassemblies and add_joint works`: **ok**.
  - Reproskript `06_find_unterbaugruppen_pfad_unvollstaendig.py`: liefert jetzt `"SubUnit:1/Platte:1"`.

### Befund 8: `update_links(repair=True)` repariert auch `origin_lost` (`links.py`, `server.py`)
- **Ursache:** In `links.update_links` wurden ausschließlich Gelenke mit `status == "moved"` an `repair()` übergeben. Gelenke, deren lokales Koordinatensystem nach Topologieänderungen temporär verloren ging (`origin_lost`), wurden ignoriert, obwohl `repair()` sie auf der vorhandenen Bauteilfläche fehlerfrei wiederherstellen kann.
- **Lösung:**
  1. `update_links(repair_moved=True)` filtert nun auf `status in ("moved", "origin_lost")`.
  2. `repair()` sichert die Frame-Koordinaten ab, falls `frame_side` None ist.
  3. `update_links` meldet das Reparaturergebnis je Gelenk strukturiert im Feld `repaired`: `{"joint": name, "status": "ok", "after": [...]}` bzw. bei Fehler `{"joint": name, "status": "failed", "error": msg}`.
  4. Neues MCP-Tool `repair_joint(assembly: str, joint: str)` in `server.py` bereitgestellt.
- **Verifikation:**
  - Test `praxistest 4 / finding 8: update_links with repair=True repairs origin_lost and reports result per joint`: **ok**.
  - Reproskript `08_update_links_ignoriert_origin_lost.py`: Gelenkstatus wechselt nach `update_links(repair=True)` von `origin_lost` sofort auf `ok` (`exit code 0`).

### Befund 7: Konzeptentwurf für parametrisch mitwandernde Bohrungen
- Wie beauftragt wurde Befund 7 nicht voreilig implementiert, sondern ein fundierter architektonischer Entwurf verfasst:
  `docs/research/2026-10-23-bohrungen-parametrisch-entwurf-flash.md`.
- Es wurden drei Optionen mit Vor- und Nachteilen analysiert:
  - (a) Bohrungsposition als Ausdruck auf Bauteilparameter
  - (b) Bohrung an eine Fläche + Abstände/Skizzenpunkt binden (Befehlsdoku `solidcraft-cli`)
  - (c) Baugruppen-Koordination über `update_links` mit automatischem Rebuild via `edit_bolted_connection`
- **Empfehlung:** Hybrider Ansatz mit Option (c) als Baugruppen-Standard und Option (a) für explizite Parameterübergabe.

---

## 3. Übersicht der Testergebnisse

| Testsuite / Skript | Status | Details |
|---|---|---|
| `tests/inventa/check.py` | **GRÜN (0 Failures)** | Alle 100+ Tests bestanden, inklusive der 6 neuen Praxistest-4-Prüfungen |
| `tests/reference/check.py` | **GRÜN (0 Failures)** | Alle 7 parametrischen Referenzbauteile (Flansch, Gehäuse, Blechwinkel, Scharnier, Welle, Rohrhalter, Rippenplatte) unverändert intakt |
| Skript 01 (`01_senkung_...py`) | **GRÜN** | Fällt wie erwartet ab und schlägt `counterbore=False` vor |
| Skript 02 (`02_falschklassifikation_...py`) | **BEHOBEN** | Dom Ø 8 mm wird nicht mehr als Bohrung gelistet |
| Skript 03 (`03_wandstaerkenpruefung_...py`) | **BEHOBEN** | Meldet nun korrekt `fail` für unzulässige 0,40 mm Domwand |
| Skript 04 (`04_fehlende_werkstoffaliase_...py`) | **GRÜN** | Meldet klaren Fehler mit Ruthex-Empfehlung und vorhandenen Werkstoffen |
| Skript 06 (`06_find_unterbaugruppen_...py`) | **BEHOBEN** | Liefert vollen hierarchischen Pfad `SubUnit:1/Platte:1` |
| Skript 08 (`08_update_links_...py`) | **GRÜN** | `update_links(repair=True)` repariert `origin_lost` erfolgreich zu `ok` |

---

## 4. Fazit

Alle bestätigten Befunde aus Praxistest 4 sind vollständig und sauber im Einklang mit der Architektur von `inventa` gelöst. Die Parametrik, Abfragegenauigkeit, DFM-Wandstärkenprüfung und Gelenkstabilität wurden messbar gestärkt.
