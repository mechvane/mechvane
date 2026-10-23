# Abschlussbericht: Assoziative Verankerung von Verschraubungen (Befund 7, Option c)

**Datum:** 2026-10-23  
**Autor:** Gemini 3.8 Flash (High)  
**Status:** Umgesetzt & Verifiziert  
**Bezug:** Befund 7 aus Praxistest 4 (`07_bolted_connection_bohrungen_nicht_parametrisch_abriss.py`), [Konzeptentwurf](2026-10-23-bohrungen-parametrisch-entwurf-flash.md)

---

## 1. Ausgangslage & Problemstellung

Im Praxistest 4 zeigte sich bei Befund 7 (`07_bolted_connection_bohrungen_nicht_parametrisch_abriss.py`), dass von `bolted_connection` erzeugte Bohrungsfeatures (`solid.hole`) in durchdrungenen Bauteildateien bisher mit statischen Gleitkommazahlen platziert wurden. 

Wurde ein Gehäuse nachträglich per `edit_in_place` parametrisch modifiziert (z. B. Gehäuselänge $L = 100 \to 110\text{ mm}$, wodurch ein Schraubdom parametrisch von $x = 35$ nach $x = 40\text{ mm}$ wanderte), passierte Folgendes:
1. Die Bohrungsfeatures verblieben bei $x = 35\text{ mm}$.
2. Die Bohrung schnitt durch den dünnen Gehäuseboden neben dem Dom.
3. Die Stirnfläche des Doms verlor ihre Identität, was bei `update_links` zu Gelenkabrissen (`face_missing`, `origin_lost`) führte.
4. Es gab keine automatische Nachführung von Baugruppen-Verschraubungen.

Gemäß dem Architekturentwurf wurde **Option (c)** (Koordination durch `update_links` mittels geometrischer Verankerung und atomarer Rekonstruktion per `edit_bolted_connection`) umgesetzt. Option (a) wurde verworfen, da Einzelteile in heterogenen Baugruppen keine einheitlichen Parameternamen teilen.

---

## 2. Architektur & Implementierung

### 2.1 Geometrische Ankererfassung in `bolted_connection` (`inventa/bolted.py`)

Vor dem Schneiden der Bohrungen ermittelt `bolted_connection` für jede Instanz der Verschraubung (Einzelverbindung oder Musterposition) eine geometrische Verankerungsreferenz mit folgender Prioritätskette:

1. **Vorrang 1 – Koaxialer Zylinder im Trägerbauteil:**
   - Sucht in den durchdrungenen Bauteilen (vom Träger-/Bodenbauteil ausgehend) nach einer koaxialen Zylinderfläche (Schraubdom oder Vorbohrung).
   - Prüft: Zylinderachse parallel zur Strahlrichtung ($|\vec{d} \times \vec{a}| < 10^{-4}$) und Strahlachse koaxial ($\text{dist}(\vec{p}, \text{Achse}) < 10^{-3}\text{ mm}$).
   - Speichert den stabilen Lineage-Namen der Fläche (`face`), die Occurrence, die relative Achsenrichtung und die axiale Koordinate.
   - Typ: `concentric` / `cylinder`.

2. **Vorrang 2 – Eintrittsfläche des obersten Teils + Kantenabstände / lokaler Versatz:**
   - Liegt keine zylindrische Referenz vor (z. B. flache Platten), wird die Eintrittsfläche des ersten durchdrungenen Bauteils als Referenz gewählt.
   - Ermittelt die Tangentialachsen der Fläche ($u, v$) und die Abstände zu den jeweils nächstgelegenen Begrenzungskanten (`offset_u`, `ref_u="min"|"max"`, `offset_v`, `ref_v="min"|"max"`) sowie den lokalen Punkt und Richtungsvektor im Bauteilkoordinatensystem.
   - Typ: `offset` / `plane`.

3. **Ablage in Metadaten:**
   - In `metadata["bolted_connections"][id]`:
     - `anchor`: Primäranker (Basisplatzierung / Instanz 0).
     - `anchors`: Liste der Anker aller Instanzen.
     - `instances[k]["anchor"]`: Spezifischer Anker der $k$-ten Instanz.
   - **Abwärtskompatibilität:** Vorhandene Einträge ohne Anker bleiben uneingeschränkt gültig.

### 2.2 Prüfung & Heilung in `update_links` (`inventa/links.py` & `inventa/bolted.py`)

Nach der Prüfung und Reparatur der Gelenke prüft `update_links` alle erfassten Verschraubungen:

1. **Auflösung des Ankers (`_resolve_anchor`):**
   - Schlägt die Auflösung fehl (Bauteildatei fehlt, Occurrence fehlt oder Ankerfläche im B-Rep nicht mehr auffindbar), wird `status: "anchor_lost"` gemeldet. Es wird nichts geraten.
   - Bei Zylinderankern wird die neue Lage der Zylinderachse im Weltkoordinatensystem berechnet. Die Platzierungshöhe entlang des Strahls wird durch Projektion erhalten.
   - Bei Flächenankern werden bei veränderter Bauteilgröße (z. B. parametrisches Plattenwachstum) die neuen Kantenkoordinaten im Part ermittelt und die Position relativ zur Ankerkante reproduziert.

2. **Verschiebungsprüfung (`_check_anchor_movement`):**
   - Weicht die ermittelte Position oder Richtung um mehr als $10^{-3}\text{ mm}$ von den gespeicherten Werten ab, gilt der Anker als gewandert.
   - `shifted_by = [dx, dy, dz]`.

3. **Verhalten bei `repair=False`:**
   - Meldet `status: "moved"` und `shifted_by`.
   - Nimmt keinerlei Änderungen an Dateien oder CAD-Sitzungen vor.

4. **Verhalten bei `repair=True`:**
   - Ruft `edit_bolted_connection` mit der neuen Platzierung (`position`, `direction`) und angepassten Muster-Parametern auf.
   - `edit_bolted_connection` löscht die alten Bohrungen in allen Platten, schneidet die neuen Bohrungen, verschiebt Normteile und Gelenke atomar.
   - Bei Fehlern greift der automatische Dateibackup-Rollback.
   - Bei Erfolg meldet `update_links`: `status: "moved_repaired"`.
   - Nach erfolgreicher Reparatur wird der Gelenkstatus aktualisiert, sodass alle Gelenke wieder als `ok` gemeldet werden.

5. **Rückgabestruktur von `update_links`:**
   ```python
   {
       "update": ...,
       "subassemblies": ...,
       "joints": [...],
       "repaired": [...],
       "bolted_connections": [
           {
               "id": "bolted_conn_1",
               "status": "ok" | "moved" | "moved_repaired" | "anchor_lost" | "failed",
               "shifted_by": [dx, dy, dz],
               "error": ... # nur bei "failed"
           }
       ],
       "warnings": [...]
   }
   ```

---

## 3. Aktualisierte Werkzeuge und Dokumentation

1. `inventa/bolted.py`:
   - `_backup_files` nutzt temporäre Verzeichnisse unter `/tmp/anker-bolted-*`.
   - `_find_penetrations` merkt `entry_face` und `exit_face`.
   - Neue Hilfsfunktionen: `_determine_anchor`, `_resolve_anchor`, `_check_anchor_movement`.
   - Neue API-Funktion: `check_and_update_bolted_connections(ws, doc, repair=False)`.
   - `bolted_connection` speichert `anchor` und `anchors` in Metadaten.

2. `inventa/links.py`:
   - `update_links` ruft `bolted.check_and_update_bolted_connections` auf, aktualisiert Gelenke nach erfolgreichen Reparaturen und liefert `bolted_connections` zurück.

3. `inventa/server.py`:
   - MCP-Tool `update_links` angepasst und dokumentiert.

4. `docs/inventa-mcp.md`:
   - Werkzeugtabelle und Verschraubungsabschnitt um Punkt 10 („Geometrische Verankerung & Assoziativität“) erweitert.

---

## 4. Verifikation & Tests

In `tests/inventa/check.py` wurden in `bolted_anchor_associativity_checks` vier Kernprüfungen implementiert:

1. **Skript-07-Fall (Gehäuse mit Dom):**
   - Gehäuse mit parametrischem Dom $dx = L/2 - 15\text{ mm}$ und Deckel.
   - `bolted_connection` erzeugt M3-Insert-Verschraubung bei $x = 35\text{ mm}$, Zylinderanker auf Dom wird registriert.
   - Per `edit_in_place` wird $L = 100 \to 110\text{ mm}$ geändert ($dx = 35 \to 40\text{ mm}$).
   - `server.update_links(repair=True)` repariert die Verbindung:
     - `status == "moved_repaired"`, `shifted_by == [5.0, 0.0, 0.0]`.
     - Bohrung im Gehäuse liegt exakt bei $x = 40{,}0\text{ mm}$ (koaxial zum Dom).
     - Alle Gelenke `ok`.
     - Kollisionsprüfung `inspect.interference` count == 0 (ohne kosmetischen Knurl-Pressfit des Gewindeeinsatzes).

2. **Muster-Fall (2x2 auf parametrisch wachsender Platte):**
   - Platte 1 mit $L = 100\text{ mm}$, 2x2-Rechteckmuster mit Schrauben bei $x = -35\text{ mm}$ (15 mm von der Kante bei $-50\text{ mm}$).
   - Platte wird auf $L = 120\text{ mm}$ verlängert (Kante wandert nach $-60\text{ mm}$).
   - `update_links(repair=True)` verschiebt das Muster atomar um $\Delta x = -10\text{ mm}$ ($x = -45\text{ mm}$).
   - Der Abstand der Bohrungen zur Ankerkante bleibt konstant bei $15{,}0\text{ mm}$.
   - Kollisionen: 0, Gelenke: alle `ok`.

3. **Prüfung `repair=False`:**
   - Meldet `status: "moved"` und den Verschiebungsvektor, ohne Dateien oder CAD-Features zu manipulieren.

4. **Prüfung `anchor_lost`:**
   - Dom wird aus dem Gehäuse gelöscht.
   - `update_links` meldet `status: "anchor_lost"` ohne Absturz, ohne Raten und ohne Fehlmodifikationen.
