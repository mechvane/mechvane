# Abschlussbericht: Behebung der Befunde 1–13 zu Normteilen, Bohrungen und Maßtabellen

**Datum:** 2026-10-21  
**Autor:** Gemini 3.8 Flash  
**Zweig:** `gemini/normteile-fixes` im Worktree `/root/repos/inventa-normteile`  
**Referenz-Review:** `docs/research/2026-10-20-review-normteile-bohrung-claude-agy.md`

---

## 1. Übersicht & Testergebnisse

| Suite | Prüfungen vorher | Prüfungen nachher | Status |
|---|---|---|---|
| `tests/inventa/check.py` | 104 | 124 (+20) | **0 Fehler (grün)** |
| `tests/reference/check.py` | 25 | 25 | **0 Fehler (grün)** |

Alle 13 nummerierten Befunde aus dem Review sowie die aufgezeigten Testlücken und selbstbestätigenden Tests wurden behoben bzw. nachgezogen. Vor jeder Fehlerbehebung wurde ein entsprechender Test in `tests/inventa/check.py` ergänzt, der vor dem Fix fehlschlug.

---

## 2. Detaillierter Status je Befund (1 bis 13)

### Befund 1: Zu kurze Schraube ohne Fehler
- **Problem:** War keine Schraubenlänge $\ge$ der benötigten Länge in der Vorzugsreihe vorhanden, wählte `preferred_screw_length` stillschweigend die längste Schraube.
- **Behebung:** `hole_tables.preferred_screw_length` wirft nun einen klaren `ValueError`, wenn `req_length` die maximal verfügbare Vorzugslänge nach ISO 4762 überschreitet.
- **Status:** Behoben.

### Befund 2: `length_override` wird nie geprüft
- **Problem:** Ein manueller `length_override` konnte kürzer als die benötigte Klemmlänge bzw. die Mindesteinschraubtiefe sein, ohne dass ein Fehler gemeldet wurde.
- **Behebung:** `preview_bolted_connection` validiert `length_override`:
  - Bei Durchgangsverschraubung muss `length_override >= required_length` (inkl. Scheiben, Mutter und Mindestüberstand $1{,}5 \cdot P$) sein.
  - Bei Sackloch- und Insert-Verschraubung muss die Schraube mindestens die Mindesteinschraubtiefe bzw. den Einsatz erreichen. Bei Unterschreitung wird ein `ValueError` ausgelöst.
- **Status:** Behoben.

### Befund 3: Doppelte Joint-Namen bei mehreren Verbindungen
- **Problem:** Festes Präfix `"Bolted"` führte bei mehreren Verbindungen in derselben Baugruppe zu Namenskollisionen; `links.record` überschrieb Metadateneinträge im Dictionary, und Bohrungsfeatures in Bauteilen hießen mehrfach `Hole_M5`.
- **Behebung:**
  - Eindeutige Verbindungs-IDs (`bolted_conn_1`, `bolted_conn_2`, …) und Präfixe (`Bolted_1`, `Bolted_2`, …).
  - `_unique_feature_name` ermittelt freie Feature-Namen im Bauteilverlauf (`Hole_M5`, `Hole_M5_2`, …).
  - Baugruppen-Metadaten werden nach allen `links.record`-Aufrufen frisch gelesen und angereichert, sodass keine Gelenkeinträge überschrieben werden.
- **Status:** Behoben.

### Befund 4: Strahl wird als unendliche Gerade behandelt
- **Problem:** Ohne Filter $s \ge 0$ wurden Bauteile oberhalb/hinter dem Startpunkt mitgebohrt; bei konzentrischer Platzierung war das Achsvorzeichen willkürlich.
- **Behebung:**
  - In `_find_penetrations` werden Durchdringungen mit $s < -10^{-4}$ verworfen.
  - Konzentrische Platzierung richtet die Achse konsistent aus.
- **Status:** Behoben.

### Befund 5: Bauteildicke aus Ebenen statt aus echten Flächen
- **Problem:** Schnittpunkte wurden nur gegen die globale Bounding-Box des ersten Körpers geprüft; bei abgestuften Bauteilen zählten dadurch nicht getroffene Absätze zur Plattendicke.
- **Behebung:** `_find_penetrations` prüft Durchstoßpunkte gegen die tatsächliche Begrenzung der getroffenen Einzelfläche (`_point_in_face` mit 2D-Flächengrenzen und Zylinderhüll-Erweiterung für Rundungsflächen).
- **Status:** Behoben.

### Befund 6: Kernloch weicht von DIN 336 ab (M8, M12)
- **Problem:** Wurde nur `"thread"` an `solid.hole` übergeben, berechnete SolidCraft intern $d - P$ (M8: 6,75 mm, M12: 10,25 mm) statt DIN 336 (M8: 6,80 mm, M12: 10,20 mm).
- **Behebung:** In `bolted_connection` wird für Sackloch-Gewindebohrungen explizit `"diameter": p_prev["tap_drill"]` zusammen mit `"thread"` an `solid.hole` übergeben. Dadurch stimmt der B-Rep-Zylinder exakt mit DIN 336 überein.
- **Status:** Behoben.

### Befund 7: Bohrtiefe ignoriert 118°-Bohrspitze
- **Problem:** Die zylindrische Tiefe wurde gegen die Plattendicke geprüft; die 118°-Kegelspitze ragte jedoch tiefer ($+ r / \tan(59^\circ)$) und konnte die Bodenplatte durchbrechen.
- **Behebung:** `hole_tables.blind_hole_depths` berechnet die Gesamttiefe `total_depth` inkl. Bohrspitze. `preview_bolted_connection` prüft `total_depth` gegen die Bodenplattendicke und wirft `ValueError`, wenn die Spitze durchbricht.
- **Status:** Behoben.

### Befund 8: Doppeltes Bauteil im Stapel bohrt dasselbe Teil zweimal
- **Problem:** Mehrere Occurrences derselben Datei im Plattenstapel (z. B. identische Platten) führten zu redundanten Bohrungsfeatures in derselben Bauteildatei.
- **Behebung:** `preview_bolted_connection` prüft auf Dateipfad-Duplikate im Stapel und weist diese mit `ValueError` ab.
- **Status:** Behoben.

### Befund 9: Ruthex Schraubenlänge ohne Kollisionsprüfung mit Sacklochboden
- **Problem:** Eine zu lange Schraube konnte über die empfohlene Mindesttiefe der Ruthex-Aufnahmebohrung hinausstehen und mit dem Kunststoffboden kollidieren.
- **Behebung:** `preview_bolted_connection` prüft, ob die Schraubenspitze über die Mindesttiefe der Aufnahmebohrung (`min_depth`) hinausragt; Überlängen werden mit `ValueError` abgewiesen.
- **Status:** Behoben.

### Befund 10: `fit` wird stillschweigend ignoriert / SolidCraft-Namen
- **Problem:** Unbekannte `fit`-Werte fielen still auf `"normal"` zurück; SolidCraft verwendet die kanonischen Namen `"close"`, `"normal"`, `"loose"` (nicht `"fine"`/`"coarse"`).
- **Behebung:** `hole_tables.normalize_fit` mappt Aliase (`fine`/`f` -> `close`, `coarse`/`c` -> `loose`, `normal`/`m` -> `normal`) und weist unbekannte Fit-Werte mit `ValueError` ab. An `solid.hole` wird der kanonische SolidCraft-Name übergeben.
- **Status:** Behoben.

### Befund 11: Senkung tiefer als obere Platte
- **Problem:** War eine Senkung tiefer als die oberste Platte, wurde sie ohne Fehler ausgeführt und schnitt die Platte komplett durch.
- **Behebung:** `preview_bolted_connection` prüft `cb_depth >= top_plate_thickness` und weist unzulässig tiefe Senkungen mit `ValueError` ab.
- **Status:** Behoben.

### Befund 12: `_parse_placement` stürzt bei `concentric` ab
- **Problem:** Zugriff auf nicht existentes `links.Workspace` führte zum Absturz; zudem wurde willkürlich der erste Zylinder gewählt und der Einstiegspunkt lag nicht an der Bohrungsöffnung.
- **Behebung:** Aufruf korrigiert (`ws.reader()`); Zylinderflächen werden auf Bohrungen (`:bore:`, `:cut:`, `hole` bzw. Innenradius) gefiltert; der Startpunkt `orig_w` wird entlang der Achse auf den Eintritt der Bohrung gelegt.
- **Status:** Behoben.

### Befund 13: Vorhandene Normteil-Datei wird ungeprüft wiederverwendet
- **Problem:** Lag bereits eine Datei mit passendem Namen im Workspace (z. B. manipuliert oder aus altem Stand mit abweichender Länge), wurde sie ungeprüft eingebaut.
- **Behebung:** `_ensure_standard_part` prüft Metadaten (`dimensions`, Norm und Nenngröße) vorhandener Dokumente; bei Diskrepanzen wird die Datei verworfen und aus der Spezifikation neu erzeugt.
- **Status:** Behoben.

---

## 3. Geänderte Normwerte mit Quelle

### DIN 974-1 (Zylindrische Senkungen für Zylinderschrauben mit Scheibe)
- **Quelle:** DIN 974-1:2008-02, Tabelle 1, Reihe 5 (für Unterlegscheiben nach ISO 7089) sowie Formel für Senktiefe $t = k_{\max} + h + Z$ mit Überstand $Z = 0{,}4\text{ mm}$ für $d \le 6\text{ mm}$ und $Z = 0{,}6\text{ mm}$ für $d \ge 8\text{ mm}$.
- **Wertevergleich `with_washer=True`:**

| Größe | Durchmesser alt (berechnet) | Durchmesser neu (DIN 974-1 Reihe 5) | Tiefe alt (mm) | Tiefe neu ($t = k + h + Z$) |
|---|---|---|---|---|
| M2.5 | 7,0 mm | **7,0 mm** | 3,5 mm | **3,4 mm** |
| M3 | 8,5 mm | **9,0 mm** | 4,0 mm | **3,9 mm** |
| M4 | 10,5 mm | **10,0 mm** | 5,4 mm | **5,2 mm** |
| M5 | 11,5 mm | **13,0 mm** | 6,5 mm | **6,4 mm** |
| M6 | 13,5 mm | **15,0 mm** | 8,2 mm | **8,0 mm** |
| M8 | 17,5 mm | **18,0 mm** | 10,4 mm | **10,2 mm** |
| M10 | 21,5 mm | **24,0 mm** | 12,8 mm | **12,6 mm** |
| M12 | 25,5 mm | **26,0 mm** | 15,3 mm | **15,1 mm** |

### DIN 336 (Kernlochbohrer für metrische Regelgewinde)
- **Quelle:** DIN 336-1:1969-07.
- **Werte:** M8 Kernlochdurchmesser **6,80 mm** (SolidCraft-Heuristik war 6,75 mm); M12 Kernlochdurchmesser **10,20 mm** (SolidCraft-Heuristik war 10,25 mm). Beide Werte werden nun explizit an das Feature übergeben und in der Geometrie verifiziert.

---

## 4. Beseitigte Testlücken & selbstbestätigende Tests

1. **Echte 3D-Geometriemessung statt Timeline-Echo:**
   - Sacklochtiefe (13,2 mm) und 118°-Bohrspitzenwinkel werden über B-Rep-Kanten und Eckpunkte des Zylinders/Kegels direkt im Modell gemessen statt nur die Eingabewerte der Timeline auszulesen.
   - Ruthex-Aufnahmebohrung (Tiefe 6,7 mm, Durchmesser 4,0 mm) wird geometrisch über Flächenkanten verifiziert.
2. **Echte Ausrichtungs- und Koaxialitätsprüfung:**
   - Koaxialität prüft die Welttransformationen aller Verbindungselemente (Schraube, Scheiben, Mutter).
3. **Erweiterte Testabdeckung:**
   - Vollständige Prüfung von `washer_head=True` (Kopfscheibe nach Reihe 5).
   - Horizontale Verschraubungsrichtung ($+X$) inklusive automatischer 3D-Ausrichtung der Normteile (`_rotation_to_dir`).
   - Prüfung des Fehleraufräumpfads bei fehlgeschlagener Normteilerstellung (`ws.close_all()`).

---

## 5. Offene Punkte

1. **Teilgewindelänge $b$ nach ISO 4762:** In SolidCraft ist die Gewindedarstellung rein kosmetisch und belegt den gesamten Schaft; ein physischer Schaftübergang bei teilgewindeten Schrauben wird von der CAD-Engine derzeit nicht modelliert.
2. **Senkschrauben nach DIN 7991 / ISO 10642:** Kegelsenkungen für Senkkopfschrauben sind als zukünftige Funktionserweiterung in der MCP-Dokumentation vormerkt.
