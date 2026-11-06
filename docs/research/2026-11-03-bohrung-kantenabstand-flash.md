# Recherche: Bohrung über Abstände zu Kanten platzieren (Inventor, Fusion, Onshape)

> **Prüfnotiz (Claude, 2026-11-03):** Rohfassung von Gemini Flash (#41). `check_sources.py`: 14/14 Zitate gefunden. Angaben zu SolidCraft `solid.hole` mit `references` im Quellcode nachgeprüft (`crates/doc/src/hole_reference.rs`, Fehlermeldungen, numerische Position, `edge_names`); seit SolidCraft v0.22.0, also in 0.25.1 vorhanden.

- **Datum:** 2026-11-03
- **Autor:** Gemini 3.8 Flash (Issue #41)
- **Status:** Verifiziert mit `python3 tools/check_sources.py docs/research/2026-11-03-bohrung-kantenabstand-flash.md` (14 von 14 Belegen voll bestätigt) und gegen den SolidCraft-Kern `/root/repos/_ext/solidcraft`
- **Kontext:** Der Bohrungsdialog im Mechvane-Arbeitsbereich (`mechvane/ui/static/features.js`, `DIALOGS.hole`) setzt die Position heute starr per Klick auf eine Fläche plus drei statischer X/Y/Z-Koordinatenfelder. SolidCrafts Kernbefehl `solid.hole` unterstützt jedoch seit Format v35 vollwertige parametrische Kantenreferenzen: `references: [{edge: [x,y,z], distance: expr}]` (bis zu zwei Kanten, Mittelpunkt folgt den Kanten bei Bauteiländerungen).
- **Ziel der Recherche:**
  1. Untersuchung marktführender CAD-Systeme (Autodesk Inventor, Autodesk Fusion, PTC Onshape): Klickabläufe, Dialogfelder, Anzeige und Bearbeitung von Abständen, Verhalten bei Größenänderungen der Teile.
  2. Ausarbeitung eines konkreten Vorschlags für Mechvane: Interaktionsablauf im Web-Dialog, Abbildung auf `solid.hole references`, Behandlung von Bearbeitungsschritten (`timeline.inspect`, `feature_for_edit`, `editSet`).
  3. Vollständige Quellenbelege mit wörtlichen Zitaten.

---

## 1. Problemstellung und Ausgangslage

In der mechanischen Konstruktion werden Bohrungen selten an absoluten Weltkoordinaten platziert. Die funktionale Konstruktionsabsicht (*Design Intent*) orientiert sich fast immer an Referenzgeometrien des umgebenden Körpers:
- Randabstand von Außenkanten (z. B. 15 mm von der linken Kante, 20 mm von der Vorderkante).
- Zentrierung oder Symmetrie zu Bauteilkanten (z. B. halbe Bauteilbreite `wid / 2`).
- Lochkreise oder Konzentrizität zu zylindrischen Absätzen und Wellen.

### Derzeitiger Zustand in Mechvane
Im Mechvane-Web-UI (`mechvane/ui/static/features.js`) arbeitet der Bohrungsdialog (`DIALOGS.hole`) mit `view: "face"`:
- Ein Klick auf eine Fläche ermittelt die Koordinaten `[x, y, z]` des Klickpunkts (auf 0,1 mm gerundet) sowie den Normalenvektor der Fläche.
- Im Dialog werden drei numerische Eingabefelder für X, Y und Z eingeblendet.
- **Nachteil:** Die erzeugte Bohrung speichert lediglich absolute Koordinaten `position: [x, y, z]`. Wenn das Bauteil später über Parameter (z. B. `len = 100 mm` statt `50 mm`) vergrößert wird, verbleibt die Bohrung starr an den ursprünglichen Koordinaten. Der Randabstand zur gegenüberliegenden Kante wächst ungewollt an; die Bohrung wandert nicht mit dem Rand mit.

### Bereits vorhandene Kernfunktionalität in SolidCraft
Der unterliegende CAD-Kern SolidCraft bietet in `solidcraft_engine` und `solidcraft_doc` bereits die vollständige Unterstützung für referenzierte Bohrungen (`crates/doc/src/hole_reference.rs` und `crates/ui-egui/src/hole_refs.rs`):
- Parameter `references` bei `solid.hole`:
  ```json
  "references": [
    {"edge": [x1, y1, z1], "distance": "15 mm"},
    {"edge": [x2, y2, z2], "distance": "20 mm"}
  ]
  ```
- **Berechnungslogik (`ReferenceFrame`):**
  - **1 Kantenreferenz:** Die Bohrung verschiebt sich in der Flächenebene rechtwinklig zur Kante auf das angegebene Abstandsmaß; ihre Position entlang der Kantenrichtung bleibt erhalten.
  - **2 Kantenreferenzen:** Der Mittelpunkt wird exakt an der Schnittstelle der beiden parallelen Versatzlinien in der Flächenebene platziert.
  - **Regeln:** Die Kanten müssen geradlinig sein und in oder an der Bohrungsfläche liegen. Parallele Kanten werden abgelehnt (`the reference edges are parallel: pick edges that cross`). Die Abstände müssen größer oder gleich 0 sein und der Bohrungspunkt muss auf der Planarfläche liegen.
  - **Persistente Benennung (`edge_names`):** SolidCraft speichert für jede Referenzkante den persistenten topologischen Kantennamen. Ändert sich die Bauteilgröße über Parameter, werden die Kanten über ihre Namen wiedergefunden und die Bohrung wird automatisch neu berechnet.

---

## 2. Analyse der Referenz-CAD-Systeme

### 2.1 Autodesk Inventor

Autodesk Inventor gilt im Maschinenbau als Maßstab für werkstattgerechte Bohrungsplatzierung. Die Entwicklung verlief in zwei großen Epochen: der klassische modale Dialog (bis ca. Inventor 2018) und die ab Inventor 2019 eingeführten *Property Panels* (Eigenschaftengruppen) mit skizzenloser Modellierung.

#### Platzierungsmethoden im klassischen Dialog
Im traditionellen Bohrungsdialog wählte der Anwender im Dropdown-Menü **Platzierung (Placement)** zwischen vier Modi:
1. **Linear:** Platzierung auf einer planaren Fläche über zwei lineare Kanten (*Reference 1*, *Reference 2*).
2. **Konzentrisch (Concentric):** Platzierung auf einer Planarfläche mit Referenz auf eine kreisförmige Modellkante oder Zylinderfläche.
3. **Auf Punkt (On Point):** Platzierung direkt auf einem vorhandenen Arbeitspunkt (*Work Point*) oder Skizzenpunkt.
4. **Nach Skizze (From Sketch):** Automatische oder manuelle Platzierung auf Skizzenmittelpunkten einer bestehenden Skizze.

#### Moderner Ablauf in der Eigenschaftengruppe (ab 2019 / skizzenlos)
In modernen Inventor-Versionen ist der Arbeitsablauf progressiv in der Eigenschaftengruppe organisiert:
- **Skizzenlose Platzierung:** Es ist keine vorab erstellte Skizze erforderlich. Ist die Option *Erstellung von Mittelpunkt zulassen* aktiviert, kann der Konstrukteur direkt auf jede planare Fläche klicken.
- **Klick-Ablauf:**
  1. *Klick 1 (Fläche):* Klick auf eine planare Fläche oder Arbeitsebene. Inventor setzt an der Klickstelle einen vorläufigen Bohrungsmittelpunkt und blendet sofort die 3D-Vorschau der Bohrungsgeometrie ein.
  2. *Klick 2 (Referenzkante 1):* Klick auf eine lineare Kante der Fläche. Inventor erzeugt eine lineare Bemaßung zwischen Kante und Bohrungsachse. Das Abstandsmaß wird hervorgehoben und kann sofort per Tastatur eingegeben werden.
  3. *Klick 3 (Referenzkante 2):* Klick auf eine zweite (nicht-parallele) Kante. Eine zweite Bemaßung wird platziert, womit die Position in der Ebene vollständig bestimmt ist.
- **Felder und Steuerungselemente:**
  - *Positionen (Positions):* Auswahlliste für Fläche/Punkte.
  - *Referenzbemaßungen:* Erscheinen dynamisch im Panel sowie direkt im Grafikfenster (*In-Canvas*).
  - *Elementbemaßung auswählen:* Über ein Kontextmenü am Bemaßungsfeld können bestehende Modellparameter oder Maße anderer Features direkt als Referenzmaß übernommen werden.
- **Anzeige und Bearbeitung:**
  - Bemaßungspfeile und Werteboxen werden als *Heads-Up-Display* direkt am 3D-Modell eingeblendet.
  - Maße können durch Doppelklick geändert werden.
  - Mit der `Entf`-Taste auf einer ausgewählten Maßlinie kann eine Kantenreferenz wieder gelöscht werden; der Mittelpunkt wird dann wieder frei ziehbar.
- **Verhalten bei Größenänderung des Bauteils:**
  - Intern erzeugt Inventor bei skizzenloser linearer Platzierung automatisch eine assoziative Skizze mit Punkten und Kantenabhängigkeiten (*„Mit der Option Lineare Platzierung erstellte frühere Bohrungselemente verfügen bei der Migration über eine Skizze mit erstellten Punkten und Abhängigkeiten.“*).
  - Ändert sich die Länge oder Breite des Bauteils, behält die Bohrung ihren festen Abstand zur Referenzkante bei.
  - Wird eine Referenzkante gelöscht oder durch vorgelagerte Features (z. B. Verrundung/Fase) unterbrochen, markiert Inventor das Element im Modellbaum als fehlerhaft (*Sick Feature*), und der Anwender muss die Referenz über *Element bearbeiten* neu zuweisen.

---

### 2.2 Autodesk Fusion

Autodesk Fusion kombiniert direkte Modellierung mit parametrischer Historie über die Zeitachse (*Timeline*).

#### Platzierungsmethoden
Der Bohrungsbefehl (`Konstruktion > Volumenkörper > Erstellen > Bohrung`) unterscheidet im Dropdown **Platzierung (Placement)** zwei grundlegende Modi:
1. **An Punkt (einzelne Bohrung) / At Point (Single Hole):** Platzierung einer einzelnen Bohrung direkt auf einer Fläche, Ebene oder einem Punkt.
2. **Aus Skizze (mehrere Bohrungen) / From Sketch (Multiple Holes):** Platzierung mehrerer Bohrungen auf vorab definierten Skizzierpunkten.

#### Klick-Ablauf bei „An Punkt“
1. *Klick 1 (Fläche/Punkt):* Auswahl der Zielfläche. Fusion setzt den Bohrungsmittelpunkt an die Klickposition und blendet Manipulatoren ein.
2. *Klick 2 (Referenzkante 1):* Der Selektor *Referenzen* im Dialog wird aktiv. Der Anwender klickt die erste Referenzkante an. Sofort spannt Fusion eine Bemaßungslinie von der Kante zum Bohrungsmittelpunkt auf und öffnet ein Eingabefeld für den Abstand.
3. *Klick 3 (Referenzkante 2):* Klick auf die zweite Kante. Ein zweites Maßfeld und ein zweiter Manipulatorpfeil erscheinen.

#### Felder und Steuerung im Dialog
- **Platzierung:** `An Punkt` / `Aus Skizze`.
- **Fläche/Punkt:** Auswahlschaltfläche für die Trägerfläche.
- **Referenzen:** Multi-Selektor für bis zu zwei Referenzkanten (nur sichtbar bei `An Punkt`).
- **Manipulatoren im Ansichtsbereich:**
  - Weißer Kreismittelpunkt zum freien Verschieben der Bohrung auf der Fläche.
  - Blaue Pfeilmanipulatoren für die beiden Kantenabstände.
  - Manipulatoren für Durchmesser, Senkungstiefe und Bohrtiefe.
- **Anzeige und Bearbeitung:**
  - Die Abstände können wahlweise direkt im 3D-Ansichtsbereich über die Maßfelder eingetippt, an den Pfeilgriffen gezogen oder im Dialogfeld eingetragen werden.
  - Abstandsmaße akzeptieren arithmetische Ausdrücke und benannte Parameter (z. B. `d12 / 2`).

#### Verhalten bei Bauteiländerungen
- Da die Referenzen als topologische Beziehungen im Feature hinterlegt sind, wandert die Bohrung synchron mit den Kanten mit, wenn vorgelagerte Extrusionen oder Parameter modifiziert werden.
- Geht eine Kante verloren, zeigt Fusion in der Zeitachse eine gelbe Warnung (*Compute Warning: Missing Reference*) an.

---

### 2.3 PTC Onshape

PTC Onshape verfolgt als rein cloud-native Plattform ein anderes CAD-Paradigma: Im standardmäßigen Feature-Dialog des **Hole Tools** gibt es bewusst **keine direkte lineare Kantenplatzierung** wie in Inventor oder Fusion. Onshape bietet stattdessen zwei klar getrennte Lösungswege:

#### Weg 1: Der skizzenbasierte Standard-Workflow (Best Practice in Onshape)
1. Der Konstrukteur erstellt eine 2D-Skizze auf der Zielfläche.
2. Mit dem Befehl *Punkt (Point)* setzt er einen oder mehrere Skizzenpunkte auf die Fläche.
3. Mit dem Bemaßungswerkzeug (*Dimension*, Tastenkürzel `D`) klickt er den Punkt und die erste Kante an (Abstand 1), anschließend den Punkt und die zweite Kante (Abstand 2).
4. Skizze schließen (`Grünes Häkchen`).
5. Das *Hole*-Feature aufrufen und die Skizzenpunkte als Platzierungsreferenz auswählen.

#### Weg 2: Skizzenlose Platzierung über Mate Connectors (On-the-Fly)
Um aufwendige Skizzen für Einzelbohrungen zu vermeiden, nutzt Onshape sein einzigartiges System der **Mate Connectors** im Part Studio:
1. Im Dialog des Hole-Features kann als Platzierungsursprung ein Mate Connector ausgewählt werden.
2. Über das Mate-Connector-Symbol im Dialog kann dieser **on-the-fly** ohne vorheriges separates Feature erstellt werden.
3. Der Konstrukteur wählt eine Geometrie (z. B. eine Ecke oder den Mittelpunkt einer Kante als impliziten Mate Connector).
4. Im aufklappenden Subdialog aktiviert er die Checkbox **Verschieben (Move)**: Hier können nun numerische Versätze in X-, Y- und Z-Richtung relativ zum Ursprungspunkt eingetragen werden (z. B. `X = 15 mm`, `Y = 20 mm`).
5. Über **Neu ausrichten (Realign)** kann die Z-Achse an einer Kante oder Fläche orientiert werden.

#### Bewertung des Onshape-Ansatzes
- **Vorteil:** Extrem mächtige und einheitliche Abstraktion; Mate Connectors können für Extrusionen, Schnitte, Bohrungen und Baugruppenverknüpfungen gleichermaßen genutzt werden.
- **Nachteil:** Für den schnellen Werkstatt-Alltag („Bohrung 10 mm vom linken und 15 mm vom vorderen Rand“) erfordert der Mate-Connector-Subdialog deutlich mehr Klicks und Koordinatendenken (Vorzeichen in X/Y je nach Ausrichtung der Triade) als das intuitive Anklicken zweier Kanten wie in Inventor oder Fusion.

---

### 2.4 Vergleichsmatrix der CAD-Systeme

| Kriterium | Autodesk Inventor | Autodesk Fusion | PTC Onshape | Mechvane (Ist-Zustand) | Mechvane (Ziel-Zustand) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primärer Klick-Ablauf** | Fläche → Kante 1 → Kante 2 | Fläche → Kante 1 → Kante 2 | Skizze → Bemaßung `D` *oder* Mate Connector mit Move | Fläche → absolute X/Y/Z-Felder | Fläche → Kante 1 → Kante 2 |
| **Skizzenlos möglich?** | Ja (ab 2019 Standard) | Ja (`An Punkt`) | Nur über Mate Connector Versatz | Ja (aber ohne Kantenbezug) | Ja (direkt auf `solid.hole references`) |
| **Max. Referenzkanten** | 2 lineare Kanten | 2 lineare Kanten | N/A (Skizzenmaße beliebig) | Keine (nur Koordinaten) | Bis zu 2 geradlinige Kanten |
| **In-Canvas Bemaßung** | Ja (interaktive Maßlinien/Pfeile) | Ja (Manipulatoren und Maßboxen) | In Skizze ja, bei Mate Connector nein | Nein | Geplant (Maße im Viewport) |
| **Eingabe von Ausdrücken** | Ja (`Elementbemaßung`, Parameter) | Ja (Formeln, Parameter) | Ja (Variablen, Formeln) | Ja (SolidCraft Länge-Ausdrücke) | Ja (z. B. `wid / 2`, `15 mm`) |
| **Verhalten bei Bauteildehnung** | Bohrung hält Kantenabstand | Bohrung hält Kantenabstand | Hält Kantenabstand | **Bohrung bleibt starr stehen (Fehler)** | Bohrung wandert assoziativ mit |
| **Konzentrische Option** | Klick auf Rundung/Zylinder | Klick auf Rundung/Zylinder | Impliziter Kreismittelpunkt | Nein | In Phase 2 vorgesehen |

---

## 3. Vorschlag für den Mechvane-Arbeitsbereich

Basierend auf den Stärken von Inventor und Fusion sowie der bereits vorhandenen Kernarchitektur von SolidCraft (`solid.hole references`) wird folgendes Interaktionsmodell für Mechvane empfohlen:

### 3.1 Interaktionsablauf im Web-Dialog (`features.js`)

Der Dialog `DIALOGS.hole` sollte von der reinen Flächenauswahl auf einen mehrstufigen Pick-Workflow umgestellt werden:

1. **Schritt 1: Fläche anklicken (`view: "face"` / Klick 1)**
   - Der Anwender klickt auf eine planare Fläche des Bauteils.
   - Mechvane bestimmt den Normalenvektor der Fläche (Bohrungsrichtung `direction = -normal`) sowie die Flächenebene.
   - Der Bohrungsmittelpunkt wird zunächst an der Klickstelle gerendert (visuelle Sofort-Rückmeldung).
   - Der Hilfetext im Dialog wechselt auf: *„Fläche gewählt. Klicke bis zu zwei Kanten für den Randabstand an, oder tippe feste Koordinaten.“*

2. **Schritt 2: Erste Kante anklicken (Klick 2, optional)**
   - Nach dem Klick auf die Fläche schaltet die Ansicht automatisch in den Kanten-Auswahlmodus (oder erlaubt simultanes Picken von Kanten der gewählten Fläche).
   - Sobald eine geradlinige Kante der Fläche angeklickt wird:
     - Mechvane ermittelt die Gerade der Kante in der Flächenebene.
     - Der senkrechte Abstand des aktuellen Bohrungsmittelpunkts zur Kante wird berechnet und in das Feld `dist1` eingetragen.
     - Die Kante wird visuell hervorgehoben (z. B. gelbe Hervorhebung).
     - Die Bohrung ist nun an Kante 1 gebunden.

3. **Schritt 3: Zweite Kante anklicken (Klick 3, optional)**
   - Klickt der Anwender eine zweite geradlinige Kante an:
     - Prüfung auf Nicht-Parallelität: Sind die beiden Kanten parallel, meldet der Statusbereich: *„Die Referenzkanten sind parallel: Wähle Kanten, die sich schneiden.“* (entspricht exakt SolidCrafts Kernprüfung).
     - Bei gültiger Kante wird der Abstand zur zweiten Kante berechnet und in `dist2` eingetragen.
     - Der Bohrungsmittelpunkt springt exakt an den Schnittpunkt der beiden Abstände in der Flächenebene.
     - Die Koordinatenfelder X/Y/Z werden schreibgeschützt oder ausgeblendet, da die Position nun vollständig durch die Kantenreferenzen parametrisiert ist.

4. **Kanten entfernen / Umschalten:**
   - Ein erneuter Klick auf eine bereits ausgewählte Kante hebt deren Auswahl auf.
   - Werden beide Kanten abgewählt, werden die X/Y/Z-Felder wieder editierbar (Rückfall auf freie Platzierung).

---

### 3.2 Dialogfelder und Datenmodell im Frontend

Im Dialogfeld `DIALOGS.hole` in `mechvane/ui/static/features.js`:

```javascript
fields: [
  // Nur anzeigen, wenn keine Referenzkanten gewählt sind:
  { key: "x", label: "X", unit: "mm", value: "", group: "position",
    show: (v, p) => !p?.edge1 },
  { key: "y", label: "Y", unit: "mm", value: "", group: "position",
    show: (v, p) => !p?.edge1 },
  { key: "z", label: "Z", unit: "mm", value: "", group: "position",
    show: (v, p) => !p?.edge1 },

  // Kantenreferenzen (erscheinen, sobald Fläche gewählt ist):
  { key: "dist1", label: "Abstand Kante 1", unit: "mm", value: "",
    show: (v, p) => !!p?.edge1 },
  { key: "dist2", label: "Abstand Kante 2", unit: "mm", value: "",
    show: (v, p) => !!p?.edge2 },

  // Standard-Bohrungsparameter (unverändert):
  { key: "spec", label: "Size", type: "select", value: "clearance", ... },
  { key: "diameter", label: "Diameter", unit: "mm", value: "5.5", ... },
  // ... (type, depth, through, etc.)
]
```

### 3.3 Abbildung auf SolidCraft `solid.hole`

Bei Klick auf **OK** oder im interaktiven Vorschaubefehl baut die Funktion `params(v, picks)` die JSON-Struktur für SolidCraft zusammen:

```javascript
params(v, picks) {
  const p = {
    position: [v.x, v.y, v.z],
    diameter: v.diameter
  };
  if (picks.direction) p.direction = picks.direction;
  if (v.spec === "tapped") p.thread = v.size;
  if (!v.through) p.depth = v.depth;
  if (v.type === "counterbore") {
    Object.assign(p, { type: "counterbore", cb_diameter: v.cb_diameter, cb_depth: v.cb_depth });
  }
  if (v.type === "countersink") {
    Object.assign(p, { type: "countersink", cs_diameter: v.cs_diameter, cs_angle: v.cs_angle });
  }

  // Kantenreferenzen hinzufügen:
  const refs = [];
  if (picks.edge1 && v.dist1) {
    refs.push({ edge: picks.edge1.point, distance: v.dist1 });
  }
  if (picks.edge2 && v.dist2) {
    refs.push({ edge: picks.edge2.point, distance: v.dist2 });
  }
  if (refs.length > 0) {
    p.references = refs;
  }
  return p;
}
```

**Zu beachtende SolidCraft-Regeln:**
1. `position` muss stets als numerisches Koordinaten-Array `[x, y, z]` übergeben werden (SolidCraft verweigert `references` in Kombination mit String-Ausdrücken in `position`: *„with a numeric position only“*).
2. Der Punkt `picks.edge1.point` muss exakt auf der geradlinigen Modellkante liegen (z. B. der Klickpunkt des Raycasts oder der Kantenmittelpunkt).
3. `distance` kann eine Zahl oder ein parametrischer String sein (z. B. `"12.5"`, `"15 mm"`, `"wid / 2"`).

---

### 3.4 Was beim Bearbeiten (`timeline.inspect` und `timeline.edit`) zu beachten ist

Wenn ein Benutzer im Modellbaum auf eine bestehende Bohrung klickt, ruft das Web-UI `api/feature?name=<Name>` auf. Auf dem Server führt `feature_for_edit()` zwei entscheidende Schritte aus:
1. `info = doc.session.cmd("timeline.inspect", {"feature": name})`
2. `doc.session.cmd("timeline.roll_to", {"position": at})` und Mesh-Rückgabe des Modells *vor* der Bohrung.

#### Rückgabe von `timeline.inspect`
Für eine Bohrung mit Kantenreferenzen liefert SolidCraft in `info.definition`:
- `definition.position`: Aktuelle Weltkoordinaten des Bohrungsmittelpunkts.
- `definition.references`: Array der gespeicherten Kantenreferenzen:
  ```json
  "references": [
    {"edge": [0.0, 20.0, 10.0], "distance": "10 mm"},
    {"edge": [25.0, 0.0, 10.0], "distance": "12 mm"}
  ]
  ```
- `info.inputs`: Liste aller Feature-Parameter, darunter die Einträge mit dem Label `"Reference distance"`.

#### Was `fromDefinition(d)` in `features.js` tun muss
Aktuell liest `fromDefinition` nur `d.position` aus und ignoriert `d.references`. Bei Kantenreferenzen muss `fromDefinition` erweitert werden:
1. Prüfen, ob `d.references` vorhanden und nicht leer ist.
2. Wenn vorhanden:
   - `values.dist1 = d.references[0].distance`
   - `picks.edge1 = { point: d.references[0].edge }`
   - Falls zweite Referenz existiert: `values.dist2 = d.references[1].distance`, `picks.edge2 = { point: d.references[1].edge }`.
   - Die X/Y/Z-Felder werden mit der aktuellen Position befüllt, aber als referenzgebunden markiert.
3. Durch den Rollback von `feature_for_edit` auf das Modell *vor* der Bohrung sind die originalen Referenzkanten im 3D-Canvas wieder sichtbar und können bei Bedarf direkt neu angeklickt oder geändert werden.

#### Was `editSet(v, picks)` für `timeline.edit` tun muss
Beim Speichern der Änderung sendet das Web-UI ein `timeline.edit`-Kommando mit dem Dictionary `set`:
```javascript
editSet(v, picks) {
  const set = {
    position: [v.x, v.y, v.z],
    diameter: v.diameter,
    depth: v.through ? null : v.depth,
    thread: v.spec === "tapped" ? v.size : null,
    hole: { type: v.type }
  };
  // Referenzen zusammenstellen:
  if (picks.edge1 && v.dist1) {
    const refs = [{ edge: picks.edge1.point, distance: v.dist1 }];
    if (picks.edge2 && v.dist2) {
      refs.push({ edge: picks.edge2.point, distance: v.dist2 });
    }
    set.references = refs;
  } else {
    // Referenzen wurden entfernt: auf null setzen, damit SolidCraft sie löscht
    set.references = null;
  }
  return set;
}
```

#### Kernverhalten in SolidCrafts `timeline.edit`
In `crates/engine/src/cmd/edit.rs` (Zeile 1205–1210) ist bereits implementiert:
```rust
// New reference edges for a hole (#37): the names of the edges there now.
if let (FeatureKind::Hole { references: a, position, .. }, FeatureKind::Hole { references: b, .. }) = (&nf.kind, &f.kind) {
    let edges = |r: &[solidcraft_doc::HoleReference]| r.iter().map(|x| x.edge.0).collect::<Vec<_>>();
    if edges(a) != edges(b) {
        nf.edge_names = solidcraft_doc::hole_reference::reference_edge_names(&s.model.state_before(id), position.0, &edges(a));
    }
}
```
Das bedeutet: Wenn neue Kantenpunkte übergeben werden, berechnet SolidCraft automatisch die persistenten Kantennamen im Modellzustand vor dem Feature neu. Werden nur die Distanzen geändert (oder Distanzen per Parameter angepasst), bleiben die bestehenden Kantenreferenzen unberührt und stabil.

---

## 4. Detaillierte Quellenbelege und wörtliche Zitate

Die folgenden Belege wurden im Volltext über HTTP abgerufen und mit dem Prüfwerkzeug `python3 tools/check_sources.py` automatisiert validiert.

### Beleg: Inventor Skizzenlose Bohrungspositionen
* **URL:** https://help.autodesk.com/cloudhelp/2026/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Geben Sie die Positionen an. Es ist keine vorhandene Skizze erforderlich. Zu den gültigen Eingaben für die Bohrungspositionen zählen Fläche Skizzierpunkt (Ende oder Mitte) sowie Arbeitspunkt.“

### Beleg: Inventor Flächenklick und Mittelpunktplatzierung
* **URL:** https://help.autodesk.com/cloudhelp/2026/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Wenn Sie auf eine Fläche klicken, wird der der Fläche zugeordnete Körper ausgewählt, eine Skizze erstellt und der Bohrungsmittelpunkt platziert.“

### Beleg: Inventor Lineare Platzierungsbemaßung an Kanten
* **URL:** https://help.autodesk.com/cloudhelp/2026/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Klicken Sie auf eine Referenzkante, um die Bemaßungen zu platzieren. Bemaßungen für die lineare Platzierung können ausgewählt, bearbeitet oder gelöscht werden, während der Befehl Bohrung aktiv ist. Wählen Sie die Bemaßung aus, und ändern Sie den Wert, bzw. drücken Sie die ENTF-Taste, um die Bemaßung zu entfernen.“

### Beleg: Inventor Elementbemaßung für Positionierung verwenden
* **URL:** https://help.autodesk.com/cloudhelp/2026/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Um bei der Positionierung von Bohrungen vorhandene Parameter oder Bemaßungen zu verwenden, klicken Sie auf den Pfeil der Bemaßungsoption und wählen Elementbemaßung auswählen“

### Beleg: Inventor Migration linearer Bohrungen zu Skizzen
* **URL:** https://help.autodesk.com/cloudhelp/2026/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Mit der Option Lineare Platzierung erstellte frühere Bohrungselemente verfügen bei der Migration über eine Skizze mit erstellten Punkten und Abhängigkeiten.“

### Beleg: Inventor Konzentrische Bohrungsplatzierung
* **URL:** https://help.autodesk.com/cloudhelp/2026/DEU/Inventor-Help/files/GUID-94EB6947-0347-4888-870D-4BA22DB144D8.htm
* **Wörtliches Zitat:** „Um konzentrische Bohrungen zu erstellen, platzieren Sie den Bohrungsmittelpunkt und klicken auf die Modellkante oder gekrümmte Fläche, um die die Bohrung konzentrisch verlaufen soll.“

### Beleg: Fusion Bohrungsbefehl und Referenz
* **URL:** https://help.autodesk.com/cloudhelp/DEU/Fusion-Model/files/GUID-3A76B269-8C8D-437B-8F4A-85D0B2BBA492.htm
* **Wörtliches Zitat:** „Bohrung - Referenz Die Option Bohrung definiert eine einfache Bohrung, eine zylindrische Bohrung mit Senkung oder eine konische Bohrung mit Senkung. Konstruktion > Volumenkörper > Erstellen > Bohrung“

### Beleg: Fusion Platzierung An Punkt vs Aus Skizze
* **URL:** https://help.autodesk.com/cloudhelp/DEU/Fusion-Model/files/GUID-3A76B269-8C8D-437B-8F4A-85D0B2BBA492.htm
* **Wörtliches Zitat:** „Wählen Sie An Punkt (einzelne Bohrung) oder Aus Skizze (mehrere Bohrungen).“

### Beleg: Fusion Referenzkanten bei An Punkt
* **URL:** https://help.autodesk.com/cloudhelp/DEU/Fusion-Model/files/GUID-3A76B269-8C8D-437B-8F4A-85D0B2BBA492.htm
* **Wörtliches Zitat:** „Referenzen Verfügbar, wenn An Punkt aktiv ist. Wählen Sie Kanten aus, um die Bohrung zu positionieren.“

### Beleg: Fusion Manipulatoren für Mittelpunkt und Kanten
* **URL:** https://help.autodesk.com/cloudhelp/DEU/Fusion-Model/files/GUID-0DFCBD4F-5130-4CC9-B1A7-23C88147752A.htm
* **Wörtliches Zitat:** „Ziehen Sie die Manipulatorgriffe für Mittelpunkt, Kante und Tiefe, um die Bohrung nach dem Platzieren zu verschieben und ihre Größe zu ändern, oder geben Sie genaue Werte ein.“

### Beleg: Fusion Referenzgeometrie für Bohrungsmaße
* **URL:** https://help.autodesk.com/cloudhelp/DEU/Fusion-Model/files/GUID-0DFCBD4F-5130-4CC9-B1A7-23C88147752A.htm
* **Wörtliches Zitat:** „Wählen Sie Referenzgeometrie aus, um die Größe und Tiefe der Bohrung anhand vorhandener Bemaßungen in Ihrer Konstruktion zu definieren.“

### Beleg: Onshape Mate Connector Auswahl im Feature-Dialog
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/redefining-implicit-mate-connectors
* **Wörtliches Zitat:** „Selecting a Mate Connector for a Feature In a Part Studio, whenever a mate connector is able to be selected for a feature, you can either select a pre-defined mate connector or create one on-the-fly using the mate connector icon in the feature dialog.“

### Beleg: Onshape Mate Connector Positionsversatz über Move
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/redefining-implicit-mate-connectors
* **Wörtliches Zitat:** „Adjusting the Position of Mate Connectors To edit position and orientation, use the Move checkbox. This will open a dialog containing movement options for the X, Y, and Z directions, as well as an option to specify a number of degrees to rotate around any of those axes. These options are useful for dialing in exact offsets, like placing a hole a fixed distance off a face or shifting a split location.“

### Beleg: Onshape Bohrungserstellung über Skizzenpunkte
* **URL:** https://www.onshape.com/en/resource-center/tech-tips/tech-tip-creating-holes-through-multiple-parts
* **Wörtliches Zitat:** „To start off, click the Hole feature from the toolbar. Then define the hole type, size, and sketch points as you normally would when creating any hole.“
