# Konzeptentwurf: Parametrische Assoziativität von Verschraubungsbohrungen bei Bauteiländerungen (Befund 7)

**Datum:** 2026-10-23  
**Autor:** Gemini 3.8 Flash (High)  
**Status:** Entwurf / RFC  
**Bezug:** Praxistest 4, Befund 7 (`07_bolted_connection_bohrungen_nicht_parametrisch_abriss.py`)  

---

## 1. Problemstellung & Ausgangslage

In `inventa` wird eine Schraubverbindung (`bolted_connection`) auf Baugruppenebene definiert. Der Algorithmus ermittelt über Raycasting die durchdrungenen Bauteile (Occurrences), transformiert den Baugruppen-Rayvektor in das lokale Koordinatensystem jedes Bauteils und erzeugt dort Bohrungsfeatures (`solid.hole`).

### Das Problem (Befund 7)
Aktuell übergibt `bolted.py` die ermittelten lokalen Koordinaten als **statische Gleitkommazahlen** an SolidCraft:
```python
hole_params = {
    "position": loc_pos,  # z. B. [35.0, 20.0, 32.5]
    "direction": loc_dir, # z. B. [0.0, 0.0, -1.0]
    ...
}
part_doc.session.cmd("solid.hole", hole_params)
```
Wird nun eines der verschraubten Bauteile per `edit_in_place` parametrisch verändert (im Praxistest 4: Gehäuselänge $L = 100 \to 110\text{ mm}$, wodurch der Schraubdom parametrisch über $dx = L/2 - 15\text{ mm}$ von $X = 35\text{ mm}$ nach $X = 40\text{ mm}$ wandert), passiert Folgendes:
1. **Bohrungen wandern nicht mit:** Die Bohrung im Gehäuse verbleibt bei $X = 35{,}0\text{ mm}$.
2. **Geometriezerstörung:** Die Bohrung schneidet nun durch den dünnen Gehäuseboden statt durch den Dom.
3. **Gelenkabrisse:** Der Zylinder des Doms behält zwar seine Identität, aber die Stirnfläche und die Gewindeeinsatz-Bohrung stimmen geometrisch nicht mehr überein. Gelenke meldeten beim anschließenden `update_links`: `status: origin_lost` oder `face_missing`.
4. **Bruch der Baugruppen-Parametrik:** Das Kernversprechen parametrischer CAD-Systeme („Änderungen an Maßen propagieren durch die gesamte Baugruppe“) ist für Schraubverbindungen unterbrochen.

---

## 2. Vergleich mit Autodesk Inventor

In Autodesk Inventor ist der **Verschraubungs-Generator** (Bolted Connection Component Generator) fest in das Baugruppen- und Feature-Framework integriert:
1. **Platzierungsarten in Inventor:**
   - **Linear:** Bohrung wird auf einer ebenen Fläche platziert und über zwei Abstandskanten (linear dimensions) referenziert. Ändert sich die Kantenposition, wandert die Bohrung mit.
   - **Konzentrisch:** Bohrung wird an eine zylindrische Kante oder Fläche gebunden. Wandert der Zapfen/Dom, folgt die Bohrung automatisch dessen Achse.
   - **Auf Skizzenpunkt:** Bohrung referenziert Punkte einer 2D- oder 3D-Skizze.
   - **Nach Bohrung:** Bohrung nutzt ein bereits im ersten Teil vorhandenes Loch als Master.
2. **Inventor-Baugruppenfeatures:**
   Inventor kann Bohrungen entweder als echte Bauteilfeatures in die Teile schreiben (mit adaptiver oder skizzenbasierter Verknüpfung) oder als reine Baugruppenschnitte führen.

---

## 3. Analyse der Lösungsoptionen in inventa / SolidCraft

Zur Behebung dieses Problems stehen in der `inventa`-Architektur mit dem `solidcraft-cli`-Kernel drei grundlegende Optionen zur Verfügung:

---

### Option (a): Bohrungsposition als Ausdruck auf Bauteilparameter

#### Funktionsweise
SolidCraft unterstützt laut `solidcraft-cli commands` in `solid.hole` parametrische Ausdrücke für Koordinaten:
```
solid.hole --> position: [x,y,z] on a face (numbers, or length expressions the hole follows)
```
Statt numerischer Floats `[35.0, 20.0, 32.5]` werden Ausdrücke übergeben, z. B.:
`["dx", "dy", "H"]` oder `["L / 2 - 15 mm", "W / 2 - 15 mm", "H"]`.

#### Vorteile
- **Echte Bauteilparametrik:** Die Bohrung ist nativ im Part-Modell an dessen eigene Parameter gebunden. Öffnet man das Bauteil isoliert außerhalb der Baugruppe und ändert $L$, wandert die Bohrung im CAD-Kernel direkt mit.
- **Keine zusätzlichen Hilfsgeometrien:** Es werden keine Hilfsskizzen oder Bemaßungsconstraints benötigt; die mathematische Auswertung übernimmt der Expression-Evaluator von SolidCraft.

#### Nachteile
- **Baugruppenübergreifende Parameter-Diskrepanz:** Eine Verschraubung verbindet mindestens zwei unterschiedliche Bauteile (z. B. Deckel und Gehäuseunterteil). Deckel und Gehäuse haben meist völlig unterschiedliche interne Parameternamen oder unterschiedliche Ursprünge. Es existiert in SolidCraft kein globales Baugruppen-Parametersystem, das automatisch Ausdrücke in allen Teilen synchronisiert.
- **Fehlende Zuordnung:** Wenn der Benutzer in `bolted_connection` eine Baugruppenkoordinate übergibt, kann `inventa` nicht erraten, aus welchen internen Parametern des Gehäuses (`L`, `wall`, `dx`) sich diese Koordinate zusammensetzt.
- **Nur für vollparametrische Eigenbauteile:** Für Standard-Teile, importierte STEP-Dateien oder Bauteile ohne Parameter-Setup versagt dieser Ansatz vollständig.

---

### Option (b): Bohrung an eine Fläche + Abstände binden (Skizzenbezug / Konzentrizität)

#### Funktionsweise
Laut `solidcraft-cli commands` bietet SolidCraft zwei Möglichkeiten für assoziative Platzierung:
1. `solid.hole` mit Skizzenpunkten:
   `solid.hole --> sketch + points: [sketch point ids] (one hole each, perpendicular to the sketch...)`
2. `sketch.create` mit Flächenbindung:
   `sketch.create --> plane: ... | {face: [world x,y,z], body?: exact world body, index?: face index, ...}`
3. Geometrische Abhängigkeiten im Sketch:
   `sketch.draw.dimensioned` oder `sketch.constraint.concentric`.

Bei dieser Option würde `bolted_connection` auf der Oberfläche des Trägerbauteils (z. B. Stirnfläche des Doms oder Deckeloberseite) eine Skizze anlegen, dort einen Skizzenpunkt konzentrisch zur Dom-Kante verankern und die Bohrung über `sketch + points` ausführen.

#### Vorteile
- **Geometrische Robustheit:** Wenn der Dom als 3D-Körper verschoben wird, wandert die auf seiner Stirnfläche verankerte Skizze und damit der Bohrungsmittelpunkt automatisch mit.
- **Unabhängig von Parameternamen:** Funktioniert auch, wenn die Verschiebung durch geometrische Modifikatoren, direkte Modellierung oder verschobene Features erfolgt, ohne dass Parameternamen bekannt sein müssen.

#### Nachteile
- **B-Rep-Topologieinstabilität (Naming Problem):** SolidCraft verlangt für `sketch.create` auf Flächen eine „unique certified source“. Wird das Bauteil stark verändert, können Flächen-Indizes kippen.
- **Komplexität über Plattenstapel:** Bei 3 oder 4 durchdrungenen Platten müsste in jeder Platte eine eigene Skizze mit Projektion (`sketch.project`) angelegt und gepflegt werden. Das vervielfacht die Feature-Anzahl im Timeline-Browser massiv und verlangsamt das Modell.
- **Zirkuläre Abhängigkeiten:** Bohrungen, die auf die Stirnfläche eines Doms referenzieren, schneiden genau diese Stirnfläche auf (sie wird zum Kreisring). Bei Neuaufbau kann der Sketch-Solver seine Referenzfläche verlieren.

---

### Option (c): `update_links` koordiniert Baugruppen-Verschraubungen atomar (`edit_bolted_connection`)

#### Funktionsweise
In `inventa` speichert die Baugruppe bereits heute Metadaten über alle erstellten Schraubverbindungen (`meta["bolted_connections"][conn_id]`).
In Option (c) wird die logische Platzierungsabsicht (**Design Intent**) in den Metadaten festgehalten:
- Entweder: **Konzentrisch** zu einem Zylinder/Dom: `{type: "concentric", anchor: {"occurrence": "Gehaeuse:1", "face": "F2:side#1"}}`
- Oder: **Relativ zu Kanten/Flächen** des Trägerteils: `{type: "offset", anchor_occurrence: "Deckel:1", ref_faces: ["F1:+x", "F1:+y"], offset: [15.0, 15.0]}`
- Oder: **Muster-Referenz**: `{type: "pattern", base_placement: ...}`

Wenn ein Bauteil per `edit_in_place` geändert wird und anschließend `finish_edit` bzw. `server.update_links` aufgerufen wird:
1. `update_links` prüft anhand der Ankerflächen der Verschraubung, ob sich deren Lage im Baugruppenraum verändert hat (genau wie es `links.check` für normale Gelenke bereits tut: `status: moved`).
2. Erkennt `update_links`, dass eine Schraubverbindung verschoben ist, ruft es intern automatisch `bolted.edit_bolted_connection` mit den neu berechneten Koordinaten auf.
3. `edit_bolted_connection` führt die bewährte atomare Aktualisierung durch:
   - Löschen der alten Bohrungsfeatures in allen Platten (vollständige Volumen-Wiederherstellung).
   - Schneiden der neuen Bohrungen an den aktuellen Zielkoordinaten.
   - Verschieben der Schrauben, Scheiben und Ruthex-Einsätze.
   - Wiederherstellen aller Gelenke ohne Abriss.

#### Vorteile
- **Maximale Zuverlässigkeit:** Nutzt den bereits im Praxistest 4 umfassend verifizierten und getesteten Code von `edit_bolted_connection`.
- **Bauteilunabhängig:** Funktioniert für alle Arten von Bauteilen (parametrische Teile, Formfeature-Modelle, STEP-Importe, Unterbaugruppen).
- **Keine Geometrie-Artefakte im Bauteil:** Die Einzelteile bleiben sauber und enthalten einfache, unverschachtelte `solid.hole`-Features ohne fragile Skizzenabhängigkeiten.
- **Architektonische Konsistenz:** Entspricht der Philosophie von `inventa`: Die Baugruppe ist die koordinierende Instanz („Master“), die Einzelteile sind autonome Dokumente („Slaves“).

#### Nachteile
- Die Anpassung geschieht nicht live im isolierten Bauteil, sondern erst auf Baugruppenebene beim Aufruf von `finish_edit` bzw. `update_links`. (Da Baugruppenverschraubungen jedoch ohnehin nur im Baugruppenkontext existieren, ist dies in der Praxis kein Nachteil).

---

## 4. Gegenüberstellung der Optionen

| Kriterium | Option (a): Expression | Option (b): Skizzenbindung | Option (c): `update_links`-Koordination |
|---|---|---|---|
| **Verlässlichkeit & Robustheit** | Gering (Parameterkonflikte) | Mittel (Topologie-Instabilität) | **Sehr hoch** (atomare Neuplatzierung) |
| **Mehrteilige Stapel** | Sehr schwierig | Aufwendig (Projektionsketten) | **Einfach & nativ** (Raycast durch Stapel) |
| **Unterstützung für Fremdteile (STEP)** | Nein | Bedingt | **Ja** |
| **Auswirkungsgrad im Bauteil** | Nur Parameterwerte | Viele Hilfsskizzen/Features | **Saubere Standard-Bohrungen** |
| **Aufwand der Umsetzung** | Mittel | Sehr hoch | **Gering bis mittel** (nutzt `edit_bolted_connection`) |

---

## 5. Empfehlung & Umsetzungsstrategie

### Empfohlener Ansatz: Hybride Baugruppen-Koordination (Option c als Basis, Option a als Ergänzung)

Wir empfehlen für `inventa` die Umsetzung von **Option (c)** als primären Standard-Mechanismus, ergänzt um **Option (a)** für explizit parametrisierte Platzierungen:

### Schritt 1: Platzierungsabsicht in Metadaten erfassen (Option c)
In `bolted.bolted_connection` wird bei Übergabe von `placement={"concentric": ...}` oder bei der automatischen Schnapp-Erkennung an Domen der Verankerungszylinder in `metadata["bolted_connections"][conn_id]["anchor"]` abgelegt:
```json
{
  "conn_id": "bolted_conn_1",
  "placement_mode": "concentric",
  "anchor": {
    "occurrence": "Gehaeuse:1",
    "face": "F2:side#1",
    "part_file": "gehaeuse.solidcraft"
  }
}
```

### Schritt 2: Erkennung in `update_links` & automatische Heilung
In `links.update_links` wird nach der Prüfung der Gelenke eine Prüfung der `bolted_connections` eingefügt:
```python
# Prüfen, ob Anker von Verschraubungen gewandert sind
for conn_id, conn_meta in meta.get("bolted_connections", {}).items():
    anchor = conn_meta.get("anchor")
    if anchor and _has_anchor_moved(ws, doc, anchor):
        new_pos = _resolve_anchor_position(ws, doc, anchor)
        bolted.edit_bolted_connection(ws, doc.name, conn_id, placement={"position": new_pos, "direction": ...})
```
Wandert ein Dom von $X = 35\text{ mm}$ nach $X = 40\text{ mm}$, erkennt `update_links` die Verschiebung, verschiebt die Verschraubung per `edit_bolted_connection` automatisch und meldet:
`"repaired_connections": [{"connection": "bolted_conn_1", "status": "ok", "shifted_by": [5.0, 0.0, 0.0]}]`.

### Schritt 3: Unterstützung für Ausdrücke (Option a)
Übergibt ein Agent in `bolted_connection` explizit parametrische Ausdrücke für `placement` (z. B. `placement={"position": ["dx", "dy", 35]}`), werden diese Strings direkt in das `solid.hole`-Feature der betreffenden Platte durchgereicht.

Mit diesem Konzept wird das Problem aus Befund 7 elegant, robust und ohne Architekturbrüche gelöst.
