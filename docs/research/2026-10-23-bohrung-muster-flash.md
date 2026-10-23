# Erweiterung des Bohrungsassistenten: Muster sowie Ändern und Löschen von Verschraubungen

Stand: 2026-10-23  
Branch: `gemini/bohrung-muster`  
Modell: Gemini 3.8 Flash  

---

## 1. Was gebaut wurde

Der Bohrungsassistent (`inventa/bolted.py`, `inventa/server.py`) wurde um drei Kernfunktionalitäten erweitert:

### 1.1 Musterunterstützung (`pattern`)
Sowohl `bolted_connection` als auch `preview_bolted_connection` akzeptieren nun den optionalen Parameter `pattern`. Unterstützt werden zwei primäre Mustertypen:
- **Kreismuster (`type: "circular"`):** Teilkreis- oder Vollkreisanordnung um eine definierte 3D-Achse:
  `{"type": "circular", "count": N, "axis_point": [x, y, z], "axis": [ax, ay, az]}`
  Startposition ($k=0$) ist der Basisstrahl aus `placement`. Nachfolgende Positionen werden über die Rodrigues-Rotationsformel exakt um die Achse gedreht (sowohl Startpunkt als auch Richtungsvektor).
- **Rechteckmuster (`type: "rectangular"`):** Gitteranordnung in zwei Raumrichtungen:
  `{"type": "rectangular", "count": [nx, ny], "spacing": [dx, dy], "directions": [[x1, y1, z1], [x2, y2, z2]]}`
  Startposition ($ix=0, iy=0$) ist der Basisstrahl; alle weiteren $nx \times ny$ Positionen werden entlang der Einheitsrichtungsvektoren verschoben.

**Strikte Vorab-Validierung:**
Bevor irgendeine Bauteildatei geöffnet oder verändert wird, werden alle Musterstrahlen geometrisch analysiert (`_find_penetrations`). Weicht auch nur eine Position in der Anzahl der geschnittenen Platten, der Bauteilzuordnung oder der Bauteildicke (Klemmlänge) von der Startposition ab, bricht der Assistent mit einem klaren `ValueError` ab. Bauteildateien und Baugruppe bleiben zu 100 % unberührt.

**Effiziente Batch-Erzeugung:**
In jedem betroffenen Bauteil werden alle $N$ Bohrungen in einem einzigen Durchlauf mit eindeutigen Feature-Namen gebohrt, die Skizzenregel wird anschließend je Bauteil einmal durchgesetzt und die Datei gespeichert. Die Baugruppe aktualisiert die Links der verknüpften Komponenten einmalig (`component.update_links`) und platziert anschließend für jede Instanz die Normteile mit eindeutigen Instanz- und Gelenknamen (`Bolted_1_ScrewJoint`, `Bolted_2_ScrewJoint` etc.).

### 1.2 Verschraubungen als Einheit (Persistenz, Listen, Löschen, Ändern)
In den Metadaten der Baugruppe (`bolted_connections`) wird jede Verbindung vollständig als logische Einheit dokumentiert:
- Eindeutige Verbindungs-ID (`id`)
- Vollständiger Parametersatz (`parameters` mit `placement`, `pattern`, `size`, `fasteners`, `fit`, `counterbore`, `connection_type`, etc.)
- Liste aller erzeugten Normteil-Komponenten (`components`)
- Liste aller erzeugten Baugruppen-Gelenke (`joints`)
- Bauteilbezogene Bohrungsfeatures (`parts` mit `occurrence`, `file`, `hole_features`)
- Instanzliste (`instances`) mit Positions- und Gelenkzuordnung

Drei neue Werkzeuge und MCP-Tools wurden bereitgestellt:
- **`list_bolted_connections(assembly)`**: Gibt alle gespeicherten Verschraubungen der Baugruppe strukturiert zurück.
- **`delete_bolted_connection(assembly, id)`**:
  1. Entfernt alle zugehörigen Baugruppen-Gelenke (`joint.delete`) und bereinigt die inventa-Verankerungen (`links.forget`).
  2. Bricht die Links der Normteilkomponenten ab und löscht die Komponenten aus der Baugruppe (`component.delete`).
  3. Öffnet die betroffenen Bauteildateien und löscht alle zugehörigen Bohrungsfeatures in umgekehrter Entstehungsreihenfolge via `sketch_rule.delete_with_owned`, setzt die Skizzenregel durch und speichert.
  4. Führt `component.update_links` in der Baugruppe aus und bereinigt die Metadaten.
  5. Das Volumen aller Platten ist danach exakt auf das Ausgangsvolumen vor dem Bohren zurückgesetzt.
- **`edit_bolted_connection(assembly, id, **changes)`**:
  Erlaubt die nachträgliche Änderung von Verbindungsparametern (z. B. Nenngröße $M5 \to M6$, Längenübersteuerung, Kopfsenkung, Passung). Umgesetzt als atomare Sequenz aus Löschen und Neuanlegen unter exakter Beibehaltung der ursprünglichen Positionen und des Musters.

### 1.3 Transaktionales Rollback (Vermeidung von halbfertigen Zuständen)
Sowohl `bolted_connection` als auch `edit_bolted_connection` sichern vor Modifikationen an Disk-Dateien die Baugruppendatei und alle durchdrungenen Bauteildateien in einem temporären Backup-Ordner (`/tmp/muster-backup-*`).
Schlägt ein Schritt während des Bohrens, Instanziierens oder Verknüpfens fehl, greift der `except`-Block:
- Alle Originaldateien werden aus dem Backup wiederhergestellt.
- Alle offenen Dokument-Sitzungen in `Workspace` werden über `doc.session.tool("open")` unmittelbar vom Disk-Stand neu geladen.
- Der Fehler wird transparent weitergereicht. Es verbleiben weder verwaiste Features noch halbe Gelenke.

---

## 2. Architekturentscheidungen

1. **Rodrigues-Formel statt Baugruppenmatrizen:**
   Für Kreismuster werden Startpunkte und Achsvektoren im Weltkoordinatensystem über die Vektordrehung nach Rodrigues berechnet. Dies vermeidet Singularitäten und arbeitet unabhängig von der Orientierung der Baugruppenkoordinaten.
2. **Abwärtskompatibilität der Metadaten:**
   Um bestehende Tests und Werkzeuge nicht zu brechen, bleiben Einzelfelder wie `screw`, `nut`, `washers`, `joints` und `parts[0]["hole_feature"]` auch bei Einzelverschraubungen identisch erhalten. Für Muster werden zusätzlich `screws`, `nuts`, `hole_features` und `instances` geführt.
3. **Löschreihenfolge in B-Rep-Historie:**
   Beim Löschen von Bohrungen in Bauteilen werden die Features in umgekehrter Reihenfolge ihrer Erstellung (`reversed(hole_features)`) gelöscht. Dadurch werden Skizzen- und Ebenenabhängigkeiten sauber abgebaut, ohne dass SolidCraft Refusals wirft.
4. **Edit als Delete + Recreate:**
   Da eine Größenänderung (z. B. M5 auf M6) sowohl den Bohrungsdurchmesser im Bauteil als auch Normteile (Schraubenkopf, Scheiben-Außendurchmesser, Mutterhöhe) und Gelenkebenen verschiebt, ist ein sauberer atomarer Rebuild geometrisch robuster und wartungsärmer als das manuelle Umparametrieren bestehender B-Rep-Topologien.

---

## 3. Tests und Verifikation

In `tests/inventa/check.py` wurde die neue Testsuite `bolted_pattern_and_edit_checks(ws)` integriert:

1. **Teilkreis mit 4 Schrauben (`test_circular_pattern`):**
   - Zwei aufeinanderliegende Platten ($80 \times 80 \times 10\text{ mm}$ und $80 \times 80 \times 8\text{ mm}$).
   - M5-Verschraubung mit Teilkreis $r = 20\text{ mm}$, count = 4.
   - Prüfungen: Genau 4 Bohrungsfeatures je Platte, genau 4 Schrauben instanziiert, `inspect.interference count == 0`, alle 12 Gelenke (24 Gelenkseiten) mit Status `ok` verankert.
2. **List & Delete (`test_list_delete`):**
   - `list_bolted_connections` findet die erzeugte Verbindung.
   - `delete_bolted_connection` entfernt alle Bohrungsfeatures in beiden Platten, alle Schrauben und Gelenke in der Baugruppe.
   - Plattenvolumen vor dem Bohren und nach dem Löschen stimmen auf $< 10^{-4}\text{ mm}^3$ exakt überein.
3. **Rechteckmuster 2x2 (`test_rectangular_pattern`):**
   - Anordnung $2 \times 2$ Schrauben im Raster $30 \times 30\text{ mm}$.
   - Prüfungen: Genau 4 Bohrungen je Platte, 4 Schrauben, `inspect.interference count == 0`, alle Gelenke `ok`.
4. **Edit-Operation & Rollback (`test_edit_and_rollback`):**
   - Änderung von M5 auf M6 per `edit_bolted_connection(asm, id, size="M6")`.
   - Prüfungen: Bohrungsdurchmesser in beiden Platten wächst auf $\varnothing\,6{,}6\text{ mm}$ (Radius 3,3 mm), Schrauben und Muttern sind auf M6 aktualisiert, alle 12 Gelenke grün, keine Kollision.
   - Fehler-Rollback: Edit-Versuch mit zu geringer Schraubenlänge (`length_override=5`). Der Aufruf bricht mit `ValueError` ab; der M6-Zustand wird vollständig und unbeschädigt wiederhergestellt.
5. **Uneinheitliche Durchdringung (`test_nonuniform_error`):**
   - Platte A ($50 \times 50\text{ mm}$) und Platte B ($30 \times 30\text{ mm}$).
   - Muster positioniert eine Schraube außerhalb von Platte B.
   - Sowohl `preview_bolted_connection` als auch `bolted_connection` weisen die Anforderung mit `ValueError` ab.
   - Beide Platten und die Baugruppe bleiben zu 100 % unverändert (keine Bohrungen, Volumen unverändert).

### Testergebnisse
- `python3 tests/inventa/check.py`: **183 ok, 0 failures**
- `python3 tests/reference/check.py`: **26 ok, 0 failures**

---

## 4. Offene Punkte / Grenzen

1. **Skizzenpunkt-basierte Muster (`By Points`):**
   Der Assistent unterstützt analytische Kreise und Rechteckgitter. Willkürliche Punktmengen aus einer 2D-Skizze können künftig über `placement: {"type": "points", ...}` nach gleichem Muster angebunden werden.
2. **Teilmuster mit Auslassungen:**
   Aktuell wird jede Instanz im Gitter erzeugt. Für komplexe Flansche mit Aussparungen (z. B. geteilte Gehäusefugen) könnte ein Filter `skip_indices: [2, 5]` ergänzt werden.
