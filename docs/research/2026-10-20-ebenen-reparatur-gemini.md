# Reparatur verschobener Gelenke an ebenen Flächen in inventa (Gemini, 2026-10-20)

Bericht zur Untersuchung und Umsetzung der Reparatur von Gelenken an ebenen Flächen über Dateigrenzen hinweg (Problemstellung [#3330](https://github.com/tangency-labs/solidcraft/issues/3330)) im Ordner `/root/repos/inventa-ebenen` auf dem Branch `gemini/ebenen-reparatur`.

---

## 1. Problemstellung und Ausgangslage

SolidCraft speichert verknüpfte Bauteile in Baugruppen intern als STEP-Importe ab. Dadurch gehen die stabilen Feature- und Flächenbezeichnungen aus dem Modellierungsverlauf der Bauteildatei verloren. Bei nachträglichen Änderungen an der Bauteildatei – insbesondere wenn neue Features (z. B. Absätze, Bohrungen) zeitlich vor bestehenden Features in die Historie eingefügt werden – ordnet SolidCraft nach einem „Update Links“ die Gelenke stillschweigend anderen Flächen zu (Fehlerfall [#3330](https://github.com/tangency-labs/solidcraft/issues/3330)).

inventa überwacht Gelenke über Dateigrenzen hinweg in `inventa/links.py`:
- `record` speichert bei `add_joint` den Lineage-Namen der Bauteilfläche (z. B. `F2:+z`).
- `check` gleicht den Gelenkrahmen gegen die aktuelle Lage der benannten Fläche in der Bauteildatei ab.
- `repair` stellt verschobene Gelenke wieder her.

**Bisherige Lücke:**
`links.repair` übersprang alle Flächen mit `kind != "cylinder"`. Verschobene Gelenke an ebenen Flächen (z. B. Platte auf Platte oder Gelenke auf Deckflächen) wurden zwar durch `update_links` als `moved` gemeldet, konnten aber nicht automatisch repariert werden.

---

## 2. Geometrische Analyse und Repräsentation

### 2.1 Verhalten von SolidCraft (`joint.create`)

In SolidCrafts Quellcode ([`crates/engine/src/cmd/joints.rs`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/joints.rs#L338-L355)) werden Gelenkursprünge auf Flächen wie folgt aufgelöst:
1. **`face: [x, y, z]`**: Führt zu [`Snap::FaceCenter`](file:///root/repos/_ext/solidcraft/crates/doc/src/joints.rs#L756-L768). SolidCraft sucht die planare Fläche am Pick und platziert den Gelenkursprung **deterministisch auf dem Flächenschwerpunkt** (`f.centroid`) dieser Fläche. Ein übergebener Pick außerhalb des Schwerpunkts bestimmt nur, welche Fläche gewählt wird, die Lage des Rahmens springt jedoch immer ins Zentrum der Fläche.
2. **`point: [x, y, z]`**: Führt zu `Snap::Point`. SolidCraft positioniert den Gelenkrahmen exakt an der angegebenen Koordinate mit der vorgegebenen `z`-Richtung.

### 2.2 Entscheidung und Begründung zur Repräsentation der relativen Lage

Um Gelenke an ebenen Flächen zu reparieren, muss deren relative Lage innerhalb der Ebene erhalten bleiben:
- **Entscheidung:** Speicherung des Versatzvektors $\mathbf{v} = O - C_{\text{face}}$ in 3D-Bauteilkoordinaten als `offset: [x, y, z]`.
- **Begründung:**
  1. *Keine willkürliche Bezugsrichtung / U-V-Basis nötig:* Die Konstruktion eines intrinsischen 2D-Flächenkoordinatensystems $(u, v)$ erfordert die Projektion einer willkürlichen Referenzachse auf die Ebene. Bei Normalen nahe dieser Referenzachse entstehen Singularitäten (Gimbal Lock) oder Diskontinuitäten. Ein 3D-Differenzvektor im Bauteilsystem ist eindeutig, stetig und koordinatenfrei auf der Ebene definiert.
  2. *CAD-Modellierung erfolgt im Bauteil-Koordinatensystem:* Features werden entlang der Hauptachsen des Bauteils ausgerichtet. Werden Features im Verlauf verschoben oder durch vorangehende Features im Index verschoben (#3330), bleibt die Ausrichtung der Ebenen im Bauteilkoordinatensystem erhalten.
  3. *Translationsinvarianz bei Feature-Verschiebungen:* Verschiebt sich die Fläche im Bauteil, wandert ihr Flächenschwerpunkt $C_{\text{face}}$ exakt mit. Der Gelenkursprung $C'_{\text{face}} + \mathbf{v}$ behält somit seine relative Position auf dem Feature bei.
  4. *Exakte Ebenenprojektion:* Bei der Reparatur wird $\mathbf{v}$ auf die Zielebene projiziert:
     $$\mathbf{v}_{\text{tangent}} = \mathbf{v} - (\mathbf{v} \cdot \mathbf{n})\mathbf{n}$$
     $$O_{\text{reconstructed}} = C_{\text{face}} + \mathbf{v}_{\text{tangent}}$$
     Dadurch liegt der rekonstruierte Punkt garantiert numerisch stabil auf der gemerkten Fläche.

### 2.3 Abwärtskompatibilität

- **Speicherung:** `_match` speichert für Ebenen zusätzlich `offset: [round(x, 6) for x in g.sub(o, f["centroid"])]`.
- **Alt-Einträge:** Existiert kein `offset`-Schlüssel im Metadaten-Anchor (aus älteren inventa-Versionen), bleibt der Eintrag in `check` voll prüfbar. Bei `repair` wird der Flächenschwerpunkt $C_{\text{face}}$ verwendet und eine Warnung ausgegeben (`warnings.warn` sowie Aufnahme in `warnings` und `repaired`).

---

## 3. Erkennung koplanarer Flächen in `check`

Bei der Überprüfung zeigte sich ein wichtiger geometrischer Randfall:
`_on_plane(f, o, z)` prüft lediglich die Erfüllung der unendlichen Ebenengleichung:
$$|(o - f[\text{"point"}]) \cdot \mathbf{n}| < \text{TOL}$$

Besitzt ein Bauteil zwei separate, aber koplanare Absätze/Pads (z. B. auf gleicher Höhe $z = 10$), so erfüllte ein auf den zweiten Absatz verschobener Gelenkrahmen weiterhin die Ebenengleichung des ersten Absatzes. `any(test(f, o, d) for f in named)` meldete fälschlicherweise `ok`, obwohl `_match` bereits erkannt hatte, dass der Rahmen auf dem anderen Absatz lag.

**Behebung:** In `links.check` wird für Ebenen zusätzlich geprüft, ob die durch `_match` ermittelte Fläche tatsächlich zur gemerkten Lineage gehört:
```python
ok = any(test(f, o, d) for f in named) and found is not None and (
    found["face"] in {f["name"] for f in named} or _base(found["face"]) == _base(anchor["face"])
)
```
Damit werden auch Sprünge zwischen gleich hohen, koplanaren Teilflächen zuverlässig als `moved` erkannt.

---

## 4. Umsetzung

Die Änderungen konzentrieren sich auf [`inventa/links.py`](file:///root/repos/inventa-ebenen/inventa/links.py):
1. **`_match`**: Liefert für `kind == "plane"` den Schlüssel `offset` zurück.
2. **`check`**: Verifiziert für Ebenen, dass die gefundene Fläche zur Ziel-Lineage gehört.
3. **`_create_params`**: Erzeugt bei adoptierten Gelenken mit Versatz aus dem Schwerpunkt einen Punkt-Pick mit `z`-Richtung.
4. **`repair`**:
   - Unterstützt `kind == "plane"` neben `kind == "cylinder"`.
   - Rekonstruiert den lokalen Ursprung aus Schwerpunkt und tangentialem Versatz (bzw. Schwerpunkt mit Warnung bei Alt-Einträgen).
   - Rechnet den Ursprung und die Normale über die Occurrence-Weltmatrix um und setzt die Parameter (`point` und `z` bei Versatz; `face` bei zentrischen Pickups).
5. **`update_links`**: Sammelt Reparatur-Warnungen und reicht sie in `repaired` und `warnings` durch.
6. **`inventa/server.py`**: Docstring von `update_links` um planare Flächen ergänzt.

---

## 5. Verifikation und Testergebnisse

In [`tests/inventa/check.py`](file:///root/repos/inventa-ebenen/tests/inventa/check.py) wurden umfassende Tests für Gelenke an ebenen Flächen ergänzt:
- **Platte-auf-Platte (`PlateOnPlate`):** Starres Gelenk auf einer Deckfläche (`Deck1`) eines Plattenbauteils.
- **Fall #3330 auf Ebene:** Einfügen eines identischen Absatzes (`Deck0`) zeitlich vor `Deck1` in der Bauteildatei führt zum unbemerkten Verschieben des Gelenks; `update_links` erkennt und meldet `status="moved"`.
- **Automatische Reparatur:** `update_links(repair_moved=True)` stellt das Gelenk auf `Deck1` (`x = 25`) wieder her.
- **Erhalt des In-Plane-Offsets:** Ein Gelenk mit Versatz zum Schwerpunkt (`x = 28, y = 3`) wird nach Verschiebung exakt an seiner ursprünglichen relativen Position (`x = 28, y = 3`) wiederhergestellt.
- **Alt-Eintrag ohne Versatz:** Manuell um `offset` bereinigter Anchor wird mit `UserWarning` am Flächenschwerpunkt repariert.

**Ergebnis Testläufe:**
- `python3 tests/inventa/check.py`: **0 failure(s)** (alle 80 Prüfungen erfolgreich)
- `python3 tests/reference/check.py`: **alle Referenzprüfungen erfolgreich**
