# Semantische Abfragen in inventa (Gemini, 2026-10-20)

Bericht zur Umsetzung semantischer Abfragen (`find`) in `inventa/query.py` und der
MCP-Schnittstelle in `inventa/server.py` auf dem Branch `gemini/abfragen`.

---

## 1. Ausgangslage und Zielsetzung

In [ROADMAP.md](../../ROADMAP.md) fordert **Grundsatz 3** („Agenten-Schnittstelle zuerst“):
> *„Agenten bekommen semantische Abfragen (‚alle ebenen Flächen mit Normale +Z‘), Batch mit Rollback, Messwerte und Snapshots.“*

Bislang mussten Agenten und Konstruktionsskripte entweder rohe `document.inspect`-Daten parsen,
auf das sperrige `body_topology` zurückgreifen oder Flächen manuell im Bild suchen.

Ziel dieser Umsetzung:
1. Modul [`inventa/query.py`](../../inventa/query.py) mit Funktion `find(document, what, where=None, limit=50)`.
2. MCP-Werkzeug `find` in [`inventa/server.py`](../../inventa/server.py).
3. Unterstützung für:
   - `what = "faces"`: Flächen mit Typ (`plane`, `cylinder`), Kennwerten (`normal`, `area`, `diameter`, `axis`),
     Lineage-Feature-Zuordnung und `pick`-Punkt auf der Fläche.
   - `what = "edges"`: Kanten mit Klassifizierung (`line`, `circle`), Länge, Endpunkten/Zentrum und
     Mittelpunkt-`pick` für `solid.fillet`/`solid.chamfer`.
   - `what = "holes"`: Logische Bohrungen als zusammengefasste zylindrische Innenflächen mit Durchmesser,
     Achse, Tiefe, Durchgängigkeit (`through`: `True`/`False`) und `pick`-Punkt am Bohrungseingang für `joint.create`.
4. Filterung via `where`:
   - `{"type": "plane", "normal": [0, 0, 1]}` (oder Richtungs-Strings wie `"+Z"`, `"-Y"`).
   - `{"type": "cylinder", "diameter": [5, 6]}` (Bereiche, Vergleiche wie `[">", 100]` oder Einzelwerte).
   - `{"area": [">", 100]}`.
   - `{"near": [x, y, z], "within": 5}` (euklidischer Abstand).
   - `{"feature": "Extrude2"}` (Zuordnung über Lineage-Namen wie `F4:side:c1#1`).
   - `{"body": "Body1"}`.
   - `{"edge": "circle" | "line", "length": [a, b]}`.
   - `{"occurrence": "Plate:1"}`.
5. In Baugruppen: Ergebnisse automatisch in Weltkoordinaten über [`links._occurrences`](../../inventa/links.py)
   bzw. SolidCrafts `world_state`.
6. Vermeidung teurer Aufrufe: Bevorzugung von `model.faces` und `model.edges` gegenüber `body_topology`.

---

## 2. Analyse SolidCraft: `model.faces`/`model.edges` vs. `body_topology`

### 2.1 Warum `body_topology` vermieden werden soll

Das MCP-Werkzeug [`body_topology`](file:///root/repos/_ext/solidcraft/docs/mcp.md#L150) von SolidCraft
baut das vollständige topologische B-Rep-Netz des Körpers auf und serialisiert:
- Alle Ecken (Vertices) mit Koordinaten.
- Alle Halbkanten und Kanten mit Adjazenzverknüpfungen.
- Alle getrimmten Facetten mit Schleifen (Loops) und Dreiecksnetzen.

Dies führt zu zwei gravierenden Problemen:
1. **Laufzeit- und Speicheraufwand**: Bei Körpern mit Bohrungen und Fasen muss der Kernel die
   komplette Adjazenzstruktur neu berechnen und als JSON-Baum übertragen.
2. **Tokenverbrauch**: Selbst für einfache Bauteile erzeugt `body_topology` mehrere Kilobyte
   strukturierter Daten, die den Kontext eines LLM unnötig belasten.

### 2.2 Die Alternative: Engine-Befehle `model.faces` und `model.edges`

SolidCraft stellt in [`crates/engine/src/cmd/inspect.rs`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/inspect.rs#L276-L320)
zwei spezialisierte Engine-Befehle bereit:
- `model.faces` (`{"body": name}`):
  Liefert Index, stabiler Lineage-Name (z. B. `F1:+z`, `F3:side:c1#1`), `exact`, `area`, `centroid`,
  `plane_normal`, `point` (ein Punkt, der exakt auf der Fläche liegt und als Pick-Referenz dient)
  sowie bei Zylinderflächen `cylinder` mit `{origin, axis, radius}`.
- `model.edges` (`{"body": name}`):
  Liefert Index, Name der anstoßenden Flächen (`face1|face2`), `mid` (Mittelpunkt auf der Kante),
  `length`, `start` und `end`.

Beide Befehle laufen direkt auf dem aktuellen `world_state()` des Modells, benötigen keine
vollständige Topologie-Serialisierung und liefern exakt die Daten, die für semantische Abfragen
benötigt werden. In `inventa/query.py` wird `body_topology` daher **nicht** benötigt.

---

## 3. Umsetzung in `inventa/query.py`

### 3.1 Kantenklassifizierung (`line` vs. `circle`)

In `model.edges` gibt SolidCraft Kanten als Kurven aus, unterscheidet im JSON aber nicht explizit
zwischen Geraden und Kreisbögen. [`_query_edges`](../../inventa/query.py) klassifiziert Kanten anhand
geometrischer und topologischer Kriterien:
1. **Gerade Kanten (`line`)**:
   Wenn der euklidische Abstand zwischen `start` und `end` der Kantenlänge entspricht
   (`abs(length - norm(end - start)) < 1e-3`), handelt es sich um eine gerade Linie.
2. **Kreiskanten (`circle`)**:
   Wenn die Kante gekrümmt ist und eine der beiden anstoßenden Flächen im Kantennamen (`f1|f2`)
   eine Zylinderfläche ist, stammt der Radius `r` und die Achse direkt aus der Zylinderdefinition
   der anstoßenden Fläche. Das Zentrum $C$ wird als Projektion des Kantenmittelpunkts `mid` auf die
   Zylinderachse bestimmt:
   $$C = P_0 + \mathbf{a} \cdot \left((\mathbf{m} - P_0) \cdot \mathbf{a}\right)$$
   Für freie Kurven wird alternativ der Umkreis über drei Punkte (`start`, `mid`, `end`) berechnet.

Der Kantenmittelpunkt `e["mid"]` dient direkt als `pick`-Punkt für Modifikations-Features wie
`solid.fillet` und `solid.chamfer`.

### 3.2 Bohrungserkennung (`holes`)

Bohrungen werden in CAD-Modellen oft als zwei Halbzylinder modelliert (z. B. `F2:side#1` und `F2:side#2`).
[`_query_holes`](../../inventa/query.py):
1. **Gruppierung**: Fasst Zylinderflächen zusammen, deren Achsen kollinear sind (`parallel` und
   `dist_to_line < 0.05 mm`) und den gleichen Radius aufweisen (`abs(r1 - r2) < 0.05 mm`).
2. **Innen- vs. Außenflächen**: Unterscheidet Bohrungen von Zapfen/Stiften über:
   - Feature-Typ (`HoleFeature` oder `operation == "cut"`).
   - Namensfragmente (`:cut:`, `:bore:`, `hole`).
   - Bounding-Box-Lage (Achse im Materialbereich des Körpers).
3. **Tiefe (`depth`)**:
   - Primär über die Länge der Seam-Kanten entlang der Zylinderachse aus `model.edges`.
   - Sekundär über die Feature-Definition im Verlauf (`timeline.inspect`).
   - Tertiär über die Mantelfläche: $L = A / (2\pi r)$.
4. **Durchgängigkeit (`through`)**:
   - Bei `HoleFeature`: Prüfung auf `depth` ohne `to` (Sackloch vs. Durchgangsloch).
   - Bei sonstigen Features: Prüfung, ob zum selben Feature eine planare Deck-/Bodenfläche
     gehört (z. B. `F{id}:bottom` oder `F{id}:base`). Fehlt diese Bodenfläche, ist die Bohrung
     durchgehend (`through = True`).
5. **Pick-Punkt**:
   Liefert das Zentrum der Öffnung an der Deckseite entlang der Achse. Dieser Punkt kann direkt in
   `joint.create` mit `circle: pick` als Gelenkursprung übergeben werden.

### 3.3 Baugruppen und Weltkoordinaten

In Baugruppendateien wertet `inventa/query.py` die Komponentenstruktur und [`links._occurrences`](../../inventa/links.py)
aus:
- Jede Komponenten-Instanz (Occurrence) wird mit ihrer globalen 4×4-Transformationsmatrix erfasst.
- Abfragen auf den Weltkörpern (z. B. `Body1` für Instanz 1, `Body1 (Plate:2)` für Instanz 2)
  liefern Punkte, Normalen und Achsen automatisch im Weltkoordinatensystem.
- Bei transformierten Einzelkörpern werden Punkte und Richtungen mit [`geometry.apply_point`](../../inventa/geometry.py)
  und [`geometry.apply_dir`](../../inventa/geometry.py) in Weltkoordinaten überführt.
- Jedes Ergebnisobjekt nennt seine Instanz im Feld `occurrence` (z. B. `"occurrence": "Plate:1"`).

---

## 4. Tests und Verifikation

In [`tests/inventa/check.py`](../../tests/inventa/check.py) wurden die Prüfungen in
`semantic_queries(ws)` und `mcp_server(tmp)` integriert:
1. **Deckfläche**: `find faces` mit Filter `{"type": "plane", "normal": [0, 0, 1]}` liefert auf einer
   60 × 40 × 10 mm Platte mit zwei Bohrungen und einer 2-mm-Fase exakt die eine Deckfläche auf $z = 10$.
   Die Fase (Normalenkomponenten in Y und Z) und die Unterseite ($z = 0$, Normale $-Z$) werden
   zuverlässig ausgeschlossen.
2. **Bohrungen**: `find holes` liefert beide Bohrungen mit Durchmesser Ø 6,0 mm und Ø 8,0 mm,
   Tiefe 10,0 mm und `through: True`.
3. **Feature-Filter**: `find faces` mit `{"feature": "Hole1"}` liefert exakt die beiden Zylinder-Halbflächen
   des Features `Hole1`.
4. **Fillet-Pick**: Der `pick`-Punkt einer Kantenabfrage (`edges` mit `edge: "line"`, Länge 60 mm am Boden)
   wird an `solid.fillet` übergeben und erzeugt erfolgreich ein Kantenverrundungs-Feature `Fillet1`.
5. **Baugruppen-Weltkoordinaten**: In einer Baugruppe mit einer um `[100, 200, 50]` verschobenen
   Komponente liefert `find` die Deckfläche auf $z = 60{,}0\text{ mm}$ und die Bohrungsmitten auf
   $x = 115{,}0\text{ mm}$ bzw. $145{,}0\text{ mm}$ und $y = 220{,}0\text{ mm}$, jeweils mit
   `occurrence: "PlateOcc:1"`.
6. **MCP-Endpunkt**: Aufruf von `find` über den JSON-RPC/stdio-Server liefert die Deckfläche des `bracket`-Bauteils.

Testergebnis:
- `python3 tests/inventa/check.py`: **62/62 Prüfungen bestanden** (0 Fehler, ~9 s).
- `python3 tests/reference/check.py`: **27/27 Referenzprüfungen bestanden** (0 Fehler, ~9 s).

---

## 5. Fazit

Mit [`inventa/query.py`](../../inventa/query.py) und dem MCP-Werkzeug `find` verfügt inventa nun über eine
robuste, token- und rechenzeiteffiziente Abfrageschnittstelle. Ein Claude- oder Gemini-Agent kann nun
ohne Umwege Abfragen wie „alle Bohrungen im Bauteil“ oder „die Deckfläche mit Normale +Z“ ausführen und
die zurückgegebenen `pick`-Punkte direkt in nachfolgende CAD-Befehle einsetzen.
