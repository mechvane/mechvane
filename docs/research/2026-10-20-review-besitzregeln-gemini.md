# Review der Besitzregeln (Gemini 4 Argon High, 2026-10-20)

Rohfassung von Gemini, gegen `inventa/` und den SolidCraft-Code
(`/root/repos/_ext/solidcraft`, Stand 2026-10-20) geprüft. Auftrag: Herleitung
der direkten Nutzer aus `timeline.dependents`, `enforce`, Löschen, Ordneransicht.

## Prüfnotiz (Claude)

| Befund | Geprüft | Stand |
|---|---|---|
| 3a Endlosschleife bei Feature mit zwei eigenen Skizzen (Loft) | bestätigt | behoben, Test `loft with two own sketches` |
| 3c Zielindex, wenn das Element hinter dem Besitzer steht | im Code nachvollzogen | behoben (Position `j` statt `j - 1`) |
| 2a Ebene auf einer Skizzenlinie zählt nicht als Nutzer der Skizze | bestätigt (`along_path`) | behoben: Nutzung aus den Definitionen, Test |
| 4a Löschen nimmt Gebrauchtes mit | Folge von 2a bestätigt; 1a-Beispiel (Split an der Ebene) **nicht** reproduziert, dort gilt die Ebene korrekt als geteilt | Schutz in `delete_with_owned` |
| 1a Diamant-Abhängigkeit | im Split-Fall nicht reproduziert | durch statische Bezüge gegenstandslos |
| 1b unterdrückte/zurückgerollte Nutzer fehlen in `would_fail` | bestätigt | behoben, Test |
| 1c, 2b, 3b Projektionen (`sketch.project`) erzeugen nur Warnungen | nachvollzogen | behoben über `sketch.inspect` → `links`, Test |
| 5a unbenutzt als `shared_by: []` | stimmt, nur Darstellung | behoben (`unused: true`) |
| 5b Marker zurück: Arbeitselement verliert Besitzer | Folge von 1b | behoben, Test |

Nachtrag (gleicher Tag): Die Nutzung kommt jetzt statisch aus
`timeline.inspect` und `sketch.inspect`. Damit ist alles behoben.

Ursprünglicher Kern der offenen Punkte: `would_fail` beruht auf einer Auswertung und sieht
weder übersprungene Features noch Bezüge, die nur Warnungen erzeugen. Eine
robuste Lösung liest die Bezüge statisch aus den Feature-Parametern
(`timeline.edit`-Sicht oder Skript-Export), statt sie aus Fehlern abzuleiten.

## Rohfassung

### 1. [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L14-L40) für Arbeitselemente (`would_fail`-Herleitung)

* **Befund 1a – Diamant-Abhängigkeiten verschlucken direkte Nutzer:**
  - **Begründung:** [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L31-L39) nimmt den ersten Eintrag `n` in `affected` als direkten Nutzer und wirft danach pauschal `below |= set(sum(dependents(n), []))` weg. Wenn ein späteres Feature `F` ein Arbeitselement `WP1` **direkt** referenziert (z. B. `plane: "WP1"` bei `solid.mirror`, `solid.split_body`, `solid.draft`, `construct.plane.between`) **und zugleich** vom Körper/Ergebnis des ersten Nutzers `n` abhängt (z. B. `n = "S1"` -> `E1` erzeugt `Body1`, und `F` spiegelt/teilt `Body1` an `WP1`), steht `F` bereits in `dependents("S1")[1]` (`would_fail` von `S1`, weil ohne `S1` auch `E1` und damit `Body1` fehlt). `F` landet in `below` und wird als direkter Nutzer von `WP1` übersehen (`consumers["WP1"] == ["S1"]` statt `["S1", "F"]`).
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L31-L39), [`dependents`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1336-L1349), [`Document::delete_feature`](file:///root/repos/_ext/solidcraft/crates/doc/src/document.rs#L3021-L3064).
  - **Testfall:**
    ```python
    [{"cmd": "construct.plane.offset", "params": {"base": "XY", "offset": 10, "name": "WP1"}},
     {"cmd": "sketch.create", "params": {"plane": "WP1", "name": "S1"}},
     {"cmd": "sketch.circle.center", "params": {"center": [0, 0], "radius": 5}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S1", "distance": 10, "name": "E1"}},
     {"cmd": "solid.mirror", "params": {"features": ["E1"], "plane": "WP1", "name": "M1"}}]
    # consumers(s)["WP1"] liefert ["S1"] statt ["S1", "M1"] -> WP1 gilt fälschlich als Alleinbesitz von S1/E1.
    ```

* **Befund 1b – Unterdrückte, zurückgerollte oder bereits fehlerhafte Features fehlen in `would_fail`:**
  - **Begründung:** [`dependents`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1347) bestimmt `would_fail` über [`newly_broken`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1050-L1060). Dort gilt `was_ok = b.error.is_none() && !b.skipped` ([edit.rs](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1056)). Unterdrückte Features (`suppressed`) und Features hinter dem Rollback-Marker haben `skipped = true` ([`Model::evaluate_from`](file:///root/repos/_ext/solidcraft/crates/doc/src/eval.rs#L1302-L1315)). Teilt sich `WP1` zwei Skizzen `S1` (aktiv) und `S2` (unterdrückt oder hinter dem Marker), meldet `would_fail` nur `S1`. `WP1` wird fälschlich `S1` allein zugeordnet. Ist der einzige Nutzer unterdrückt/zurückgerollt, gilt `WP1` als unbenutzt (`[]`).
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L22-L39), [`newly_broken`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1050-L1060), [`Model::evaluate_from`](file:///root/repos/_ext/solidcraft/crates/doc/src/eval.rs#L1302-L1315).
  - **Testfall:**
    ```python
    [{"cmd": "construct.plane.offset", "params": {"base": "XY", "offset": 10, "name": "WP1"}},
     {"cmd": "sketch.create", "params": {"plane": "WP1", "name": "S1"}},
     {"cmd": "sketch.circle.center", "params": {"center": [0, 0], "radius": 5}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S1", "distance": 10, "name": "E1"}},
     {"cmd": "sketch.create", "params": {"plane": "WP1", "name": "S2"}},
     {"cmd": "sketch.circle.center", "params": {"center": [20, 0], "radius": 5}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S2", "distance": 10, "name": "E2"}},
     {"cmd": "timeline.suppress", "params": {"feature": "S2"}}]  # oder timeline.roll_to auf E1
    # consumers(s)["WP1"] liefert ["S1"] statt ["S1", "S2"].
    ```

* **Befund 1c – In Skizzen projizierte Arbeitselemente (`sketch.project`) erscheinen nie in `would_fail`:**
  - **Begründung:** Projiziert eine Skizze `S1` eine Arbeitsebene `WP1` (`LinkSource::Plane`), setzt [`refresh_links_in`](file:///root/repos/_ext/solidcraft/crates/doc/src/project.rs#L675-L678) beim Fehlen von `WP1` nur `sk.set_link_lost(..., true)` und gibt eine Warnung zurück; [`eval_feature`](file:///root/repos/_ext/solidcraft/crates/doc/src/eval.rs#L4932-L4940) setzt `warning`, aber kein `error`. Da [`newly_broken`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1055) nur `r.error.is_some()` prüft, taucht `S1` nicht in `would_fail` auf.
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L31), [`refresh_links_in`](file:///root/repos/_ext/solidcraft/crates/doc/src/project.rs#L675-L678), [`eval_feature`](file:///root/repos/_ext/solidcraft/crates/doc/src/eval.rs#L4932-L4940).
  - **Testfall:**
    ```python
    [{"cmd": "construct.plane.offset", "params": {"base": "XZ", "offset": 15, "name": "WP1"}},
     {"cmd": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
     {"cmd": "sketch.project", "params": {"refs": [{"plane": "WP1"}]}},
     {"cmd": "sketch.finish", "params": {}}]
    # consumers(s)["WP1"] ist [] statt ["S1"].
    ```

---

### 2. [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L28-L29) für Skizzen (nimmt nur `deleted_with_it`)

*(Hinweis: Wenn zwei Solid-/Surface-Features Profile derselben Skizze nutzen, stehen beide in [`input_sketches()`](file:///root/repos/_ext/solidcraft/crates/doc/src/feature_refs.rs#L20-L29) und damit in `deleted_with_it` – dieser Fall funktioniert. Falsch wird es bei Referenzen ohne `SketchId`-Feld:)*

* **Befund 2a – Arbeitselemente auf Skizzengeometrie (`GeoRef::SketchCurve` / `SketchPoint`) stehen nur in `would_fail`, nicht in `deleted_with_it`:**
  - **Begründung:** [`Document::delete_feature`](file:///root/repos/_ext/solidcraft/crates/doc/src/document.rs#L3024) bestimmt `deleted_with_it` über [`FeatureKind::input_sketches()`](file:///root/repos/_ext/solidcraft/crates/doc/src/feature_refs.rs#L20-L29). [`Walk for GeoRef`](file:///root/repos/_ext/solidcraft/crates/doc/src/walk.rs#L430-L454) besucht die `sketch: u64`-Felder in [`GeoRef::SketchPoint`](file:///root/repos/_ext/solidcraft/crates/doc/src/construct.rs#L55) und [`GeoRef::SketchCurve`](file:///root/repos/_ext/solidcraft/crates/doc/src/construct.rs#L57) **nicht** als `Ref::Sketch`. Ein Arbeitselement (z. B. `construct.plane.along_path`, `construct.axis.edge`, `construct.point.vertex` auf einer Skizze) landet deshalb nur in `would_fail`. Da [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L28-L29) für Skizzen `would_fail` verwirft (`dependents(f["name"])[0]`), wird das Arbeitselement nicht als Nutzer der Skizze erkannt.
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L28-L29), [`Walk for GeoRef`](file:///root/repos/_ext/solidcraft/crates/doc/src/walk.rs#L430-L454), [`GeoRef`](file:///root/repos/_ext/solidcraft/crates/doc/src/construct.rs#L55-L57).
  - **Testfall:**
    ```python
    [{"cmd": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
     {"cmd": "sketch.line", "params": {"points": [[0, 0], [20, 0]], "ids": ["l1"]}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "construct.plane.along_path", "params": {"sketch": "S1", "curve": "l1", "t": 0.5, "name": "WP1"}}]
    # timeline.dependents("S1") liefert deleted_with_it=[], would_fail=["WP1"].
    # consumers(s)["S1"] ist [] statt ["WP1"].
    ```

* **Befund 2b – Skizze projiziert/schneidet eine andere Skizze (`sketch.project` / `sketch.intersect` / `sketch.include_3d`):**
  - **Begründung:** [`Walk for solidcraft_sketch::Sketch`](file:///root/repos/_ext/solidcraft/crates/doc/src/walk.rs#L46) ist leer; `LinkSource::SketchCurve` und `LinkSource::SketchPoint` sind nicht in [`input_sketches()`](file:///root/repos/_ext/solidcraft/crates/doc/src/feature_refs.rs#L20-L29) enthalten (`deleted_with_it` enthält die projizierende Skizze `S2` nicht, und `would_fail` wegen `set_link_lost` in [`refresh_links_in`](file:///root/repos/_ext/solidcraft/crates/doc/src/project.rs#L675-L678) ebenfalls nicht). Nutzt `E1` die Skizze `S1` als Profil und `S2` projiziert aus `S1`, erkennt [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L28-L29) nur `["E1"]` statt `["E1", "S2"]`.
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L28-L29), [`Walk for Sketch`](file:///root/repos/_ext/solidcraft/crates/doc/src/walk.rs#L46), [`refresh_links_in`](file:///root/repos/_ext/solidcraft/crates/doc/src/project.rs#L675-L678).
  - **Testfall:**
    ```python
    [{"cmd": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
     {"cmd": "sketch.circle.center", "params": {"center": [0, 0], "radius": 10, "id": "c1"}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "sketch.create", "params": {"plane": "XY", "name": "S2"}},
     {"cmd": "sketch.project", "params": {"refs": [{"sketch": "S1", "curve": "c1"}]}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S1", "distance": 5, "name": "E1"}}]
    # consumers(s)["S1"] ist ["E1"] (S2 fehlt).
    ```

---

### 3. [`enforce()`](file:///root/repos/inventa/inventa/sketch_rule.py#L56-L77): Endlosschleife und kaputter Verlauf

* **Befund 3a – Deterministische Endlosschleife (`RuntimeError: sketch rule did not settle`), sobald ein Feature $\ge 2$ eigene Skizzen/Arbeitselemente besitzt:**
  - **Begründung:** [`enforce()`](file:///root/repos/inventa/inventa/sketch_rule.py#L64-L68) verlangt für **jedes** `(sketch, feature)` in `owners`, dass `j == i + 1` gilt (also dass *jedes* besessene Element unmittelbar auf Index `j - 1` direkt vor `feature` steht). Hat ein Feature zwei eigene Elemente (z. B. `solid.loft` mit `S1`, `S2`; `solid.sweep` mit Profil `S1` und Pfad `S2`; ein Feature mit eigener Skizze `S1` **und** direkt genutzter eigener Ebene `WP1`; oder eine Ebene `construct.plane.between` auf zwei eigenen Ebenen `WP1`, `WP2`), schiebt [`enforce()`](file:///root/repos/inventa/inventa/sketch_rule.py#L60-L77) abwechselnd `S1` und `S2` auf Position `j - 1` direkt vor das Feature und bricht nach 200 Iterationen mit `RuntimeError("sketch rule did not settle")` ab, nachdem der Verlauf durch 200 `timeline.reorder`-Aufrufe verändert wurde.
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L60-L77).
  - **Testfall:**
    ```python
    [{"cmd": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
     {"cmd": "sketch.circle.center", "params": {"center": [0, 0], "radius": 10}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "sketch.create", "params": {"plane": "XY", "offset": 20, "name": "S2"}},
     {"cmd": "sketch.circle.center", "params": {"center": [0, 0], "radius": 5}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.loft", "params": {"sections": [{"sketch": "S1"}, {"sketch": "S2"}], "name": "Loft1"}}]
    # sketch_rule.enforce(s) -> RuntimeError: sketch rule did not settle
    ```

* **Befund 3b – Kaputter Verlauf durch `timeline.reorder` bei projizierter Skizzen-/Ebenen-Geometrie:**
  - **Begründung:** [`reorder`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1080) lehnt das Verschieben nur ab, wenn [`newly_broken`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1050-L1060) ein neues `error.is_some()` meldet. Verliert eine Skizze `S2` beim Verschieben von `S1` hinter `S2` ihren Projektions-Link auf `S1` (`projected reference lost`), erzeugt das in SolidCraft nur eine `warning`, keinen `error` ([`eval_feature`](file:///root/repos/_ext/solidcraft/crates/doc/src/eval.rs#L4932-L4940)). [`enforce()`](file:///root/repos/inventa/inventa/sketch_rule.py#L69-L73) schiebt `S1` (aus Befund 2b) hinter `S2` direkt vor `E1`; `timeline.reorder` gelingt und zerstört den Link in `S2` (`lost = true`).
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L64-L74), [`reorder`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1080), [`eval_feature`](file:///root/repos/_ext/solidcraft/crates/doc/src/eval.rs#L4932-L4940).
  - **Testfall:** Im Testfall aus **Befund 2b** (`[S1, S2, E1]`) verschiebt `sketch_rule.enforce(s)` `S1` hinter `S2` (`[S2, S1, E1]`), woraufhin `S2` die Warnung `"projected reference lost: sketch 1 has no curve c1"` erhält.

* **Befund 3c – Falscher Zielindex `j - 1` in `enforce()`, wenn das Arbeitselement im Verlauf hinter seinem Besitzer steht (`i > j`):**
  - **Begründung:** [`Document::resolve_plane_in`](file:///root/repos/_ext/solidcraft/crates/doc/src/document.rs#L3254) löst `PlaneRef::Construction` per `self.find_feature(name)` dokumentweit auf, falls die Ebene noch nicht im vorangehenden `ModelState` liegt. Wird eine Skizze `S1` per `timeline.edit` auf eine weiter hinten stehende Ebene `WP1` gesetzt (`i > j`), übergibt [`enforce()`](file:///root/repos/inventa/inventa/sketch_rule.py#L67) `position = j - 1` an [`reorder`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1071-L1074). Da `remove(i)` bei `i > j` die Indizes $\le j$ nicht verschiebt, fügt `insert(j - 1, ...)` `WP1` **vor dem Vorgänger von `S1`** (`j - 1` statt `j`) ein. Liegt auf Index `j - 1` das Feature `Box1`, auf dessen Fläche `WP1` ruht, schlägt `reorder` auf Position `0` (vor `Box1`) fehl (`refused`), obwohl Position `1` (nach `Box1`, direkt vor `S1`) gültig wäre.
  - **Fundstelle:** [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L64-L74), [`reorder`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1071-L1074), [`Document::resolve_plane_in`](file:///root/repos/_ext/solidcraft/crates/doc/src/document.rs#L3247-L3257).
  - **Testfall:**
    ```python
    [{"cmd": "solid.box", "params": {"length": 10, "width": 10, "height": 10, "name": "Box1"}},
     {"cmd": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
     {"cmd": "sketch.circle.center", "params": {"center": [5, 5], "radius": 2}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S1", "distance": 5, "name": "E1"}},
     {"cmd": "construct.plane.offset", "params": {"base": {"face": [5, 5, 10], "body": "Body1"}, "offset": 5, "name": "WP1"}},
     {"cmd": "timeline.edit", "params": {"feature": "S1", "set": {"plane": "WP1"}}}]
    # WP1 ist an Index 4, S1 an Index 1. enforce(s) versucht position=0 (vor Box1) -> refused=[('WP1', 'S1')],
    # obwohl timeline.reorder(feature="WP1", position=1) problemlos funktioniert.
    ```

---

### 4. [`owned_by()`](file:///root/repos/inventa/inventa/sketch_rule.py#L48-L53) und [`delete_feature`](file:///root/repos/inventa/inventa/server.py#L101-L110) in `inventa/server.py`

* **Befund 4a – `delete_feature` löscht Skizzen und Arbeitselemente mit, die noch von anderen Features gebraucht werden:**
  - **Begründung:** [`delete_feature`](file:///root/repos/inventa/inventa/server.py#L105-L108) löscht bei `keep_sketch=False` alles aus `owned_by(owners(consumers(doc.session)), feature)` per `timeline.delete`. In allen Fällen aus Befund **1a**, **1b**, **1c**, **2a** und **2b**, in denen ein zweiter Nutzer von [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L14-L40) nicht gezählt wird, hat die Skizze bzw. das Arbeitselement scheinbar nur **einen** Nutzer (`len(v) == 1`) und wird beim Löschen von `feature` mitgelöscht:
    1. **Aus 2a:** Skizze `S1` wird von `E1` extrudiert **und** trägt eine Konstruktionsebene `WP1` (`along_path` auf Kurve von `S1`). `delete_feature(..., "E1")` löscht `S1` mit -> `WP1` bricht (`error`).
    2. **Aus 2b:** Skizze `S1` wird von `E1` extrudiert **und** von `S2` projiziert. `delete_feature(..., "E1")` löscht `S1` mit -> `S2` verliert ihre projizierte Referenz.
    3. **Aus 1b:** Arbeitsebene `WP1` trägt `S1` -> `E1` (aktiv) und `S2` -> `E2` (unterdrückt oder hinter dem Rollback-Marker). `delete_feature(..., "E1")` löscht `S1` und `WP1` mit -> `S2` bricht beim Ent-Unterdrücken / Vorrollen.
    4. **Aus 1a:** Arbeitsebene `WP1` trägt `S1` -> `E1` (`operation: "join"` auf bestehenden Körper `Body1` aus `Box1`) und ein späteres `Split1` teilt `Body1` an `plane: "WP1"`. Weil `Split1` beim Test-Löschen von `S1` (in `dependents("S1")`) ebenfalls fehlschlägt oder in `below` landet, gilt `WP1` als Besitz von `S1`/`E1`; `delete_feature(..., "E1")` löscht `WP1` mit und macht `Split1` kaputt, obwohl `Body1` aus `Box1` weiter existiert!
  - **Fundstelle:** [server.py](file:///root/repos/inventa/inventa/server.py#L101-L110), [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L43-L53).
  - **Testfall (zeigt direkt das Kaputtgehen eines verbleibenden Features durch `delete_feature`):**
    ```python
    [{"cmd": "sketch.create", "params": {"plane": "XY", "name": "S1"}},
     {"cmd": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [20, 10]}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S1", "distance": 5, "name": "E1"}},
     {"cmd": "construct.plane.along_path", "params": {"sketch": "S1", "curve": "l1", "t": 0.5, "name": "WP1"}}]
    # Aufruf von delete_feature(doc, "E1") löscht ["E1"] und danach owned=["S1"].
    # Danach steht WP1 mit error != None im Verlauf, obwohl WP1 nicht zu E1 gehörte.
    ```

---

### 5. [`part_tree(groups=True)`](file:///root/repos/inventa/inventa/tree.py#L6-L53) in `inventa/tree.py`

* **Befund 5a – Unbenutzte Skizzen und Arbeitselemente werden in `groups` als `{"shared_by": []}` markiert:**
  - **Begründung:** In [`part_tree`](file:///root/repos/inventa/inventa/tree.py#L48-L50) prüft `entry(f)` nur `if len(users) == 1 else {"shared_by": users}`. Für unbenutzte Skizzen/Arbeitselemente (`len(users) == 0`) liefert die Datenstruktur `{"shared_by": []}` statt sie als unbenutzt zu kennzeichnen (was [`render()`](file:///root/repos/inventa/inventa/tree.py#L125) nachträglich mit `if r["shared_by"] else "unbenutzt"` kaschiert).
  - **Fundstelle:** [tree.py](file:///root/repos/inventa/inventa/tree.py#L48-L52).
  - **Testfall:**
    ```python
    [{"cmd": "construct.plane.offset", "params": {"base": "XY", "offset": 10, "name": "WP1"}}]
    # part_tree(s, groups=True)["groups"]["work_features"][0]
    # liefert {"name": "WP1", "type": "ConstructionPlane", "shared_by": []}.
    ```

* **Befund 5b – Zurückrollen des `EndOfPart`-Markers löscht die Besitz-/Gruppen-Zuordnung von Arbeitselementen in `part_tree`:**
  - **Begründung:** Während [`input_sketches()`](file:///root/repos/_ext/solidcraft/crates/doc/src/feature_refs.rs#L20-L29) für Skizzen statisch über alle Features läuft (weshalb `S3` in [`check.py`](file:///root/repos/inventa/tests/inventa/check.py#L57-L60) auch hinter `EndOfPart` unter `Cut2` gruppiert bleibt), hängt `would_fail` für Arbeitselemente von der Auswertung ab ([`newly_broken`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1056) ignoriert alle Features mit `skipped == true` hinter dem Marker). Rollt man den Marker vor den Nutzer eines Arbeitselements, liefert [`consumers()`](file:///root/repos/inventa/inventa/sketch_rule.py#L31) `[]`: Das Arbeitselement fällt in [`part_tree`](file:///root/repos/inventa/inventa/tree.py#L36-L52) aus seinem Besitzer-Knoten heraus auf die oberste Ebene und steht in `groups["work_features"]` als `"shared_by": []` („unbenutzt“).
  - **Fundstelle:** [tree.py](file:///root/repos/inventa/inventa/tree.py#L14-L52), [sketch_rule.py](file:///root/repos/inventa/inventa/sketch_rule.py#L31), [`newly_broken`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/edit.rs#L1056).
  - **Testfall:**
    ```python
    [{"cmd": "construct.plane.offset", "params": {"base": "XY", "offset": 10, "name": "WP1"}},
     {"cmd": "sketch.create", "params": {"plane": "WP1", "name": "S1"}},
     {"cmd": "sketch.circle.center", "params": {"center": [0, 0], "radius": 5}},
     {"cmd": "sketch.finish", "params": {}},
     {"cmd": "solid.extrude", "params": {"sketch": "S1", "distance": 10, "name": "E1"}},
     {"cmd": "timeline.roll_to", "params": {"feature": "WP1"}}]
    # part_tree(s, groups=True): WP1 ist nicht mehr Kind von S1/E1, sondern Top-Level
    # und hat in groups["work_features"] {"shared_by": []} statt {"owner": "S1"}.
    ```
