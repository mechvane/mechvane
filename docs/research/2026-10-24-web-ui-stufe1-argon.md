# Bericht: Mechvane Web-UI (Stufe 1, nur lesend)

**Datum:** 2026-10-24  
**Branch:** `argon/web-ui-1`

## 1. Was gebaut wurde

Mit `mechvane/ui/` verfügt Mechvane über eine erste, rein lesende Web-Oberfläche ohne externe Python-Abhängigkeiten und ohne Build-Schritt (`npm`/Bundler entfallen):

- **CLI-Start (`mechvane/ui/__main__.py`):** `python3 -m mechvane.ui <datei.solidcraft> [--port 8765]` startet einen lokalen HTTP-Server (gebunden ausschließlich an `127.0.0.1`) und öffnet das angegebene Bauteil oder die Baugruppe über `Workspace`.
- **Netz-Aufbereitung (`mechvane/ui/mesh.py`):**
  - `collect_mesh(doc_or_session, tmp_dir=None)` exportiert das geöffnete Modell über `session.tool("export", {"path": ..., "format": "3mf-tagged"})` in eine temporäre Datei unter einem freigegebenen Pfad (`allow_paths` bzw. `/tmp/ui1-*`) und entfernt sie unmittelbar im `finally`-Block.
  - `parse_3mf(path)` liest `3D/3dmodel.model` per `zipfile` und `xml.etree.ElementTree`, extrahiert je `<object>` die flache Knotenliste `positions` (`[x, y, z, …]`), die Dreiecksindizes `indices` (`[v1, v2, v3, …]`) sowie die B-Rep-Flächenindizes `face_ids` (`ft:face` im Namespace `https://github.com/bherbruck/solidcraft/formats/3mf-face-tags/2026/10`).
  - Anschließend ordnet `_body_faces` über `session.cmd("model.faces", {"body": name})["faces"]` jedem numerischen Flächenindex den stabilen B-Rep-Flächennamen (`[{"index", "name"}]`) zu.
- **Datensammlung & Server (`mechvane/ui/server.py`):**
  - Die Sammelfunktionen `collect_version`, `collect_mesh`, `collect_tree` und `collect_findings` sind ohne HTTP direkt aufruf- und testbar.
  - `UIServer` erweitert `ThreadingHTTPServer` und schützt sämtliche Zugriffe auf `Workspace` und die SolidCraft-Sitzung mit einem zentralen `threading.Lock`.
  - Endpunkte: `/api/version`, `/api/mesh`, `/api/tree`, `/api/findings`. Ausnahmen werden als JSON mit HTTP-Status 500 (`{"error": "…"}`) zurückgegeben, ohne den Server zu beenden.
- **Browser-Oberfläche (`mechvane/ui/static/index.html`, `app.js`, `style.css`):**
  - **3D-Ansicht:** `three@0.160.0` samt `OrbitControls` über Import-Map von `cdn.jsdelivr.net`, `Z` nach oben (`DEFAULT_UP = (0, 0, 1)`), automatische Kameraeinpassung über die Bounding Sphere beim Erstladen. Durch Trennung der Eckpunkte entlang unterschiedlicher `ft:face`-Werte werden Zylinderflächen glatt schattiert, während B-Rep-Flächengrenzen als scharfe Kanten und Feature-Linien gezeichnet werden.
  - **Modellbaum (links):** Zeigt Bauteile mit Körpern, Features, untergeordneten Skizzen und Bauteilende (`tree.part_tree`) sowie Baugruppen mit Occurrences, Gelenken und deren Prüfstatus aus `links.check` (`tree.assembly_tree`).
  - **Befundliste (rechts):** Kombiniert `design_rules.check` und bei Baugruppen zusätzlich `links.check`, farbig nach Schwere (`fail`, `warn`, `ok`). Ein Klick auf einen Befund hebt die zugehörigen Dreiecke über `Flächenname → Index → face_ids` im 3D-Modell hervor (inklusive halbtransparenter Röntgendarstellung für innenliegende Bohrungs-/Senkungsflächen). Befunde ohne Flächenbezug im Netz, aber mit 3D-Ort (`location.point`), zeigen einen 3D-Kugel-/Ring-Marker; Befunde ohne beides bleiben reine Textauswahl.
  - **Automatisches Neu-Laden:** Alle 2 s wird `/api/version` abgefragt. Ändert sich die `mtime` der Datei, lädt der Server das Dokument in `Workspace` neu und der Browser aktualisiert Netz, Baum und Befunde bei unveränderter Kameraposition.
  - **Farbschema:** Schlichtes Layout mit automatischem hellem und dunklem Modus über `prefers-color-scheme`.

## 2. Ergebnis der Untersuchung: Baugruppen-Koordinaten im `3mf-tagged`-Export

Geprüft wurde, wie SolidCraft Baugruppen beim Export mit `format: "3mf-tagged"` (sowie `model.faces` in der Baugruppensitzung) ausgibt:

1. **Ein `<object>` je Körper-Vorkommen (Occurrence):**
   - Jedes eingefügte Bauteil und jede per `occurrence.copy` vervielfältigte Instanz wird in `3D/3dmodel.model` als eigenes `<object type="model" name="…" ft:faces="N">` ausgegeben.
   - Bei mehrfach eingefügten gleichnamigen Körpern vergibt SolidCraft eindeutige Namen wie `BoxA (2)` bzw. bei `occurrence.copy` den Occurrence-Zusatz `BoxA (P1:2)`.
   - Im `<build>`-Abschnitt steht je Objekt ein `<item objectid="…"/>` ohne zusätzliche Transformationsmatrix.
2. **Eckpunkte bereits vollständig in Weltkoordinaten:**
   - Die `<vertex x="…" y="…" z="…"/>`-Einträge jedes `<object>` enthalten bereits die mit der Welt-Transformationsmatrix der jeweiligen Occurrence umgerechneten Koordinaten (sowohl Translation als auch Rotation, einschließlich Gelenklösung `joint.solve`).
   - Im Browser-Client ist daher keine nachträgliche 4×4-Matrixmultiplikation je Occurrence nötig; alle Körper aus `/api/mesh` liegen direkt im gemeinsamen Baugruppen-Weltkoordinatensystem.
3. **`model.faces` in Baugruppen:**
   - `session.cmd("model.faces", {"body": name})` akzeptiert auch die instanziierten Namen (z. B. `BoxA (P1:2)` oder `Pin`) direkt und liefert deren Flächen ebenfalls in Weltkoordinaten.
   - Da SolidCraft verknüpfte Bauteile als STEP in die Baugruppe übernimmt, tragen die Flächen in der Baugruppensitzung STEP-Namen (`F3:face:0` usw.), während `links.check` die Lineage-Namen aus der Bauteildatei (`F2:side#1` usw.) meldet. `collect_findings` löst deshalb bei Baugruppen-Gelenken über den Gelenkrahmen (`links._match`) zusätzlich die korrespondierende STEP-Fläche der Baugruppe auf und übergibt den Gelenkursprung als `point`, sodass Gelenkbefunde im 3D-Modell sowohl per Fläche als auch per 3D-Marker hervorgehoben werden können.

## 3. Prüfungen

- In `tests/mechvane/check.py` wurde `web_ui_stage1_checks` ergänzt (5 neue Prüfungen, insgesamt 238 Prüfungen):
  1. `mesh.py` gegen den Referenz-Flansch aus `tests/reference/flansch.build.json` (18 Flächen wie in `model.faces`, alle Dreiecks-`face_ids` und Knotenindizes gültig, alle Flächennamen vorhanden).
  2. Start des UI-Servers auf Port 0 in einem Hintergrund-Thread, Abruf aller vier Endpunkte (`/api/version`, `/api/mesh`, `/api/tree`, `/api/findings`) und Prüfung der JSON-Struktur.
  3. Baugruppe aus zwei Teilen mit Drehgelenk (`PinInPlate`): `/api/tree` enthält das Gelenk samt Status `"ok"` aus `links.check`, `/api/mesh` liefert die Geometrie am gelösten Gelenkort in Weltkoordinaten.
  4. Bauteil mit absichtlichem Befund nach Befund 8 (Senkung kerbt Nachbarwand, `countersink_clearance`): Der `fail`-Befund erscheint in `/api/findings` mit dem Flächennamen `F3:csink:base`, der in `/api/mesh` unter `faces` und `face_ids` existiert.
  5. Dateiänderung auf Platte (`mtime`-Erhöhung): `/api/version` meldet die neue Version, der Server lädt das Dokument neu und `/api/tree` enthält das neu hinzugefügte Feature.
- `python3 tests/reference/check.py` läuft vollständig grün.
- Headless-WebGL-Screenshot mit `chrome-headless-shell` (`--use-gl=swiftshader --enable-unsafe-swiftshader`) erfolgreich erzeugt und unter `docs/media/web-ui-1.png` abgelegt sowie in `README.md` eingebunden.

## 4. Offene Punkte & Ausblick auf Stufe 2

Was in Stufe 2 anders bzw. weiterführend gemacht werden sollte:

1. **Bauteil-Befunde in Baugruppen und Datei-Überwachung:**
   - Derzeit prüft `/api/version` nur die `mtime` der geöffneten Hauptdatei, und `design_rules.check` läuft auf der geöffneten Sitzung (in Baugruppen also auf den STEP-Körpern ohne Bauteil-Feature-Historie). In Stufe 2 sollte der Server bei Baugruppen auch die `mtime` aller verknüpften Bauteil- und Unterbaugruppendateien überwachen und Bauteil-Konstruktionsregeln in den verknüpften Bauteildateien prüfen, wobei die gemeldeten Bauteilflächen über `links._match` bzw. Flächentransformation auf die Baugruppen-Körper abgebildet werden.
2. **Interaktive Flächen- und Kantenauswahl im 3D-Viewport (Picking):**
   - Da jedes Dreieck in `face_ids` bereits seinen B-Rep-Flächenindex kennt, kann ein `THREE.Raycaster` beim Klick auf das 3D-Modell sofort `faceIndex = body.face_ids[intersection.faceIndex]` und damit den B-Rep-Flächennamen bestimmen. Das ermöglicht in Stufe 2 direktes Auswählen von Flächen im 3D-Modell (inkl. Anzeige von Flächenkennwerten aus `find` und Kopieren von Pick-Koordinaten für Agenten).
3. **Gemeinsame Sitzung mit dem MCP-Server statt Datei-Polling:**
   - In Stufe 1 öffnet `python3 -m mechvane.ui` eine eigene `Workspace`-Instanz und erkennt Änderungen über `mtime` beim Speichern. In Stufe 2 sollte die Web-UI direkt an den laufenden MCP-Server (`mechvane/server.py`) angebunden werden (z. B. per Server-Sent Events oder WebSocket), damit Änderungen eines KI-Agenten sofort nach jedem `run` — noch vor `save_document` — live im Browser erscheinen.
4. **Lokales Vendoring von `three.js`:**
   - Für vollständig offline-fähigen Betrieb ohne CDN-Abhängigkeit (`cdn.jsdelivr.net`) sollten `three.module.js` und `OrbitControls.js` in Stufe 2 lokal unter `mechvane/ui/static/vendor/` ausgeliefert werden.
