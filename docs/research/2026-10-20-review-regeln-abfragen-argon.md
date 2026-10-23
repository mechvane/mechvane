> Gemini-4-Argon-Review (nur lesend) von design_rules.py, query.py und Commit 9090fd0, 10 Befunde, nicht nachgestellt. Stichprobe Claude: Befund 5 (cos statt sin beim Überhangwinkel) rechnerisch bestätigt. Testfälle vor dem Beheben in tests/inventa/check.py nachstellen; die API-Namen in den Testfällen können abweichen.

Hier sind die **10 Befunde** nach absteigender Schwere geordnet:

---

### 1. [Hoch] Externe Zylinder/Zapfen (`operation="join"`) werden als Sacklöcher erkannt und lösen falsche Gewinde-Fehler aus
- **Fundstelle:** [inventa/design_rules.py:113-139](file:///root/repos/inventa/inventa/design_rules.py#L113-L139), [inventa/query.py:438-455](file:///root/repos/inventa/inventa/query.py#L438-L455)
- **Begründung:** `document.inspect` liefert `operation` nicht auf oberster Ebene eines Timeline-Eintrags, sondern unter `feat_info["definition"]["operation"]`. `feat_info.get("operation") == "cut"` ist daher immer `False`. Noch gravierender: Features mit `operation="join"` oder `"new"` (Bolzen, Zapfen, Dome) werden nicht ausgeschlossen, sondern fallen in den `else`-Zweig (`min_b[0] + r < center[0] < max_b[0] - r`). Jeder auf einer größeren Platte stehende Zapfen liegt innerhalb der X/Y-Bounding-Box und wird als Innenbohrung (`is_hole = True`) und wegen seiner Stirnfläche (`end_caps`) als Sackloch (`is_blind = True`) eingestuft. Hat der Zapfen z. B. Ø 5,0 mm (M6-Kernlochmaß), schlägt `check_design` mit `thread_depth: fail` fehl und `query.find(..., "holes")` gibt den Zapfen als Sackloch zurück.
- **Testfall:**
  ```python
  doc = ws.new(PART, "pin_part")
  doc.session.batch([
      {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [0, 0, 0]}},
      {"command": "solid.cylinder", "params": {"diameter": 5.0, "height": 5.0, "base": [20, 20, 5], "operation": "join", "name": "Pin"}},
  ])
  assert query.find(doc, "holes") == []                          # Ist: [{'name': 'Pin', 'type': 'hole', 'through': False, ...}]
  assert design_rules.check(doc.session)["verdict"] == "ok"      # Ist: 'fail' (thread_depth: 5.0 mm < 9.0 mm für M6 tap drill)
  ```

---

### 2. [Hoch] Horizontale Bohrungen (X-/Y-Achse) und um 90° gedrehte Baugruppen-Teile scheitern an hartcodierter Z-Achsen-Annahme
- **Fundstelle:** [inventa/design_rules.py:121-124](file:///root/repos/inventa/inventa/design_rules.py#L121-L124), [inventa/design_rules.py:188-195](file:///root/repos/inventa/inventa/design_rules.py#L188-L195), [inventa/query.py:446-455](file:///root/repos/inventa/inventa/query.py#L446-L455)
- **Begründung:**
  1. `design_rules.py:188-195` berechnet `dx` und `dy` zur Bounding-Box unabhängig von der Bohrungsachse `axis` und setzt `min_dist = min(min_dist, min(dx, dy))`. Bei einer horizontalen Bohrung entlang Y durch eine 6 mm dünne Wand (`60 × 6 × 40 mm`) ist `dy = 3.0 mm` die halbe **Wanddicke entlang der Bohrungsachse selbst**. `check_design` meldet fälschlich `Wall thickness to edge is 0.00 mm < 1.20 mm` und `Hole edge distance 3.00 mm < 9.00 mm to face F1:+z` (obwohl `F1:+z` 20 mm entfernt ist).
  2. In Baugruppen heißen alle Flächen `F{id}:face:…` (`ImportFeature`), sodass `query.py:446-454` immer in die X/Y-Bounding-Box-Heuristik fällt. Wird eine Platte mit dem neuen `rotate`-Parameter aus Commit `9090fd0` um 90° um X gedreht eingefügt, liegt der Zylinderursprung `p0[1]` auf der Vorder-/Rückseite (`min_y` bzw. `max_y`), `min_y + r - 0.1 <= p0[1] <= max_y - r + 0.1` schlägt fehl, und `query.find(asm, "holes")` findet **keine einzige Bohrung** (`[]`).
- **Testfall:**
  ```python
  plate = ws.new(PART, "wall")
  plate.session.batch([
      {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 6, "corner": [0, 0, 0]}},
      {"command": "solid.hole", "params": {"position": [30, 20, 6], "direction": [0, 0, -1], "diameter": 6.0, "name": "H1"}},
  ])
  plate.save()
  asm = ws.new(ASSEMBLY, "rot_asm")
  links.insert(ws, asm, plate.path, name="PlateX", rotate={"axis": [1, 0, 0], "angle": 90}, grounded=True)
  assert len(query.find(asm, "holes")) == 1  # Ist: 0 ([])
  ```

---

### 3. [Hoch] Unendliche Trägerebenen bei `hole_edge_distance` / `min_wall_thickness` erzeugen Fehlalarme an Stufen, Rippen und L-Winkeln
- **Fundstelle:** [inventa/design_rules.py:181-186](file:///root/repos/inventa/inventa/design_rules.py#L181-L186)
- **Begründung:** `dist = abs(g.dot(g.sub(c, sf["point"]), n))` misst den Abstand des Bohrungszentrums `c` zur **unendlichen Ebene** jeder vertikalen Fläche `sf`, ohne zu prüfen, ob `sf` im Höhenbereich (Z) der Bohrung liegt, ob die Projektion die Fläche trifft oder ob die Flächennormale `n` überhaupt vom Loch nach außen zeigt. Bei einem L-Winkel (Grundplatte `60 × 40 × 10 mm`, Steg `20 × 40 × 20 mm` bei `x ∈ [0, 20], z ∈ [10, 30]`) schneidet die unendliche Ebene der inneren Stufenwand `F2:+x` (`x = 20, z ∈ [10, 30]`) durch die Grundplatte (`z ∈ [0, 10]`). Eine Bohrung Ø 6 mm bei `x = 24, y = 20` hat real 21 mm Wandstärke bis `x = 0`, fällt aber gegen die darüberliegende Stufe `F2:+x` durch.
- **Testfall:**
  ```python
  doc = ws.new(PART, "l_bracket")
  doc.session.batch([
      {"command": "solid.box", "params": {"length": 60, "width": 40, "height": 10, "corner": [0, 0, 0], "name": "Base"}},
      {"command": "solid.box", "params": {"length": 20, "width": 40, "height": 20, "corner": [0, 0, 10], "operation": "join", "name": "Wall"}},
      {"command": "solid.hole", "params": {"position": [24, 20, 10], "direction": [0, 0, -1], "diameter": 6.0, "name": "MountHole"}},
  ])
  assert design_rules.check(doc.session)["verdict"] == "ok"
  # Ist: 'fail' (min_wall_thickness: 1.00 mm < 1.20 mm, hole_edge_distance: 4.00 mm < 9.00 mm to face F2:+x)
  ```

---

### 4. [Hoch] `float(feat_defn["depth"])` stürzt bei Einheiten-/Parameterausdrücken ab und überschätzt Einschraubtiefen in dünnen Platten
- **Fundstelle:** [inventa/design_rules.py:133-134](file:///root/repos/inventa/inventa/design_rules.py#L133-L134), [inventa/design_rules.py:302-303](file:///root/repos/inventa/inventa/design_rules.py#L302-L303), [inventa/design_rules.py:325](file:///root/repos/inventa/inventa/design_rules.py#L325), [inventa/query.py:471-474](file:///root/repos/inventa/inventa/query.py#L471-L474)
- **Begründung:**
  1. SolidCraft legt `depth` und `height` in `timeline.inspect` als Ausdrucks-String ab (z. B. `"10 mm"` oder Parameter `"h_depth"`). `float(feat_defn["depth"])` wirft dann `ValueError: could not convert string to float: '10 mm'`.
  2. Selbst bei reiner Zahl (`depth=10`) auf einer nur 5 mm dünnen Platte setzt `design_rules.py:133` wegen `"depth" in defn` `is_blind = True` (obwohl die Bohrung komplett durch die 5-mm-Platte geht) und nimmt in Zeile 303 ungeprüft den Feature-Parameter `10.0 mm` statt der tatsächlichen Zylinderlänge im Bauteil (`h["length"] == 5.0 mm`), sodass ein 5 mm kurzes M6-Kernloch die geforderten 9,0 mm Einschraubtiefe fälschlich besteht.
- **Testfall:**
  ```python
  doc = ws.new(PART, "thin_expr")
  doc.session.batch([
      {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 5, "corner": [0, 0, 0]}},
      {"command": "solid.hole", "params": {"position": [20, 20, 5], "direction": [0, 0, -1], "diameter": 5.0, "depth": "10 mm"}},
  ])
  design_rules.check(doc.session)  # Wirft ValueError: could not convert string to float: '10 mm'
  ```

---

### 5. [Mittel] Falsche Winkelfunktion (`cos` statt `sin`) bei `max_overhang_angle` invertiert strenge und großzügige Überhanggrenzen
- **Fundstelle:** [inventa/design_rules.py:15](file:///root/repos/inventa/inventa/design_rules.py#L15), [inventa/design_rules.py:340-350](file:///root/repos/inventa/inventa/design_rules.py#L340-L350)
- **Begründung:** `max_overhang_angle` ist als Winkel **von der Vertikalen** dokumentiert (`# degrees from vertical`). Eine um $\alpha$ aus der Vertikalen geneigte Überhangfläche hat die Normalenkomponente $n_z = -\sin(\alpha)$ ($\alpha = 0^\circ \Rightarrow n_z = 0$ vertikal; $\alpha = 90^\circ \Rightarrow n_z = -1$ horizontal). Zeile 340 rechnet jedoch `cos_limit = math.cos(math.radians(max_oh))` und prüft `n[2] < -cos_limit`. Das stimmt nur zufällig für $\alpha = 45^\circ$ ($\cos 45^\circ = \sin 45^\circ$). Bei einem strengen Profil `{"max_overhang_angle": 30.0}` ist `-cos(30°) = -0.866`, wodurch ein 50°-Überhang ($n_z = -0.766$) fälschlich besteht; bei einem großzügigen Profil `{"max_overhang_angle": 60.0}` ist `-cos(60°) = -0.5`, wodurch ein steiler 35°-Überhang ($n_z = -0.574$) fälschlich durchfällt.
- **Testfall:**
  ```python
  doc = ws.new(PART, "chamfer_oh")
  doc.session.batch([
      {"command": "solid.box", "params": {"length": 20, "width": 20, "height": 10, "corner": [0, 0, 0]}},
      {"command": "solid.chamfer", "params": {"edges": [[10, 0, 0]], "distance": 5}},  # 45°-Überhang (n_z = -0.7071)
  ])
  res = design_rules.check(doc.session, profile={"max_overhang_angle": 30.0})
  assert res["rules"]["printability"]["status"] == "fail"  # Ist: 'ok' (-0.7071 ist nicht < -cos(30°) = -0.8660)
  ```

---

### 6. [Mittel] 4×4-Matrix in `insert_part(..., rotate=...)` (Commit `9090fd0`) dreht in die Gegenrichtung und verwirft die Translation
- **Fundstelle:** [inventa/links.py:328-351](file:///root/repos/inventa/inventa/links.py#L328-L351), [inventa/geometry.py:63-80](file:///root/repos/inventa/inventa/geometry.py#L63-L80), [inventa/server.py:129-132](file:///root/repos/inventa/inventa/server.py#L129-L132)
- **Begründung:** Sowohl die übliche mathematische Darstellung als auch SolidCrafts eigener `occurrence.move(matrix=…)`-Befehl ([component_matrix.rs:28-30](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/component_matrix.rs#L28-L30)) erwarten eine zeilenweise 4×4-Matrix `[[r00, r01, r02, tx], …, [0, 0, 0, 1]]` (Spaltenvektor-Konvention). `_move_params` übergibt die Matrix jedoch direkt an `g.move_params(mat)`, das SolidCrafts internes transponiertes Format (`m[col][row]`, Translation in `m[3][:3]`) voraussetzt. Dadurch wird der Drehwinkel invertiert (`-angle` statt `+angle`) und die Translation in der 4. Spalte (`mat[0..2][3]`) komplett ignoriert (da `mat[3][:3] == [0, 0, 0]` gelesen wird). Eine 3×3-Rotationsmatrix (`len == 3`) fällt zudem in Zeile 354 (`axis, angle, origin = rotate`) und übergibt Zeile 1 als String `angle="[0, 0, 1]"`.
- **Testfall:**
  ```python
  # Zeilenweise 4x4-Matrix für +90° um X und Translation [10, 20, 30]
  mat = [[1, 0, 0, 10], [0, 0, -1, 20], [0, 1, 0, 30], [0, 0, 0, 1]]
  mp = links._move_params("Plate:1", rotate=mat)
  # Ist: translate=[0, 0, 0] (Translation verloren) und axis=[-2.0, 0, 0], angle=pi/2 (-90° statt +90°!)
  assert mp["translate"] == [10, 20, 30] and mp["axis"][0] > 0
  ```

---

### 7. [Mittel] `insert_part` einer Unterbaugruppe mit `grounded=True` lässt `update_links` nach Teilebewegung in der Unterbaugruppe abstürzen
- **Fundstelle:** [inventa/links.py:460-465](file:///root/repos/inventa/inventa/links.py#L460-L465), [inventa/links.py:624-625](file:///root/repos/inventa/inventa/links.py#L624-L625)
- **Begründung:** Wird eine Unterbaugruppe mit `grounded=True` eingefügt (wie in `insert_rotation_checks` aus Commit `9090fd0`), lässt `_insert_subassembly` über `keep_grounded` auch die Kind-Occurrences innerhalb der Hauptbaugruppe auf `grounded=True`. Verschiebt oder dreht sich später ein Bauteil in der Unterbaugruppen-Datei, ruft `_sync_subassemblies` in Zeile 625 `s.cmd("occurrence.move", ...)` direkt auf der fixierten Kind-Occurrence auf, ohne `grounded` vorübergehend zu lösen (wie es Zeile 633–641 für Gelenke tut). SolidCraft wirft `SolidCraftError: invalid parameters for occurrence.move: <Part> is grounded`.
- **Testfall:**
  ```python
  sub = ws.new(ASSEMBLY, "sub_u")
  links.insert(ws, sub, plate.path, name="Plate", translate=[10, 0, 0], grounded=True)
  sub.save()
  top = ws.new(ASSEMBLY, "top_u")
  links.insert(ws, top, sub.path, name="Sub", rotate={"axis": [1, 0, 0], "angle": 90}, grounded=True)
  sub.session.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": False})
  sub.session.cmd("occurrence.move", {"occurrence": "Plate:1", "translate": [20, 0, 0]})
  sub.session.cmd("occurrence.ground", {"occurrence": "Plate:1", "grounded": True})
  sub.save()
  links.update_links(ws, top)  # Wirft SolidCraftError: invalid parameters for `occurrence.move`: Plate:1 is grounded
  ```

---

### 8. [Mittel] In Baugruppen meldet `query.find(asm, "holes")` jedes Durchgangsloch als `through: False` (`is_through: False`)
- **Fundstelle:** [inventa/query.py:488-491](file:///root/repos/inventa/inventa/query.py#L488-L491), [inventa/design_rules.py:94](file:///root/repos/inventa/inventa/design_rules.py#L94), [inventa/design_rules.py:137-139](file:///root/repos/inventa/inventa/design_rules.py#L137-L139)
- **Begründung:** `end_caps = [f for f in faces if f["name"].startswith(f"F{feat_id}:") and not f.get("cylinder")]` prüft nur, ob irgendeine nicht-zylindrische Fläche im Körper dasselbe Feature-Präfix `F{feat_id}:` besitzt. Da verknüpfte Bauteile in Baugruppen als ein einzelnes `ImportFeature` (z. B. `F3`) geladen werden, heißen **alle** ebenen Außenflächen des Körpers `F3:face:…`. Damit ist `end_caps` immer nicht-leer und jede Durchgangsbohrung in einer Baugruppe erhält `through: False` (und den Import-Namen statt des Feature-Namens). Zudem hat eine importierte Bohrung nur eine Zylinderfläche (`len(grp) == 1`, Fläche $2\pi r L$), wofür die Fallback-Formel `total_area / (math.pi * r)` (`design_rules.py:94`, `query.py:476`) die **doppelte** Tiefe ($2L$) berechnet.
- **Testfall:**
  ```python
  # Direkt im bestehenden Testaufbau semantic_queries (tests/inventa/check.py:998-1003):
  asm_holes = query.find(asm, "holes")
  assert all(h["through"] is True for h in asm_holes)  # Ist: [False, False] trotz Durchgangslöchern!
  ```

---

### 9. [Niedrig] Warnung bei zu flachem Sackloch aktualisiert `rules["thread_depth"]["status"]` nicht (`verdict` bleibt `"ok"`)
- **Fundstelle:** [inventa/design_rules.py:323-334](file:///root/repos/inventa/inventa/design_rules.py#L323-L334)
- **Begründung:** Wenn ein unbemaßtes Sackloch (kein ISO-Kernlochmaß, z. B. Ø 4,0 mm) flacher als `1.5 * d` ist, hängt Zeile 327 zwar ein Finding mit `"status": "warn"` an `rules["thread_depth"]["findings"]` an, setzt aber anders als bei `printability` (Zeile 362–363) nicht `rules["thread_depth"]["status"] = "warn"`. Dadurch bleiben sowohl der Regelstatus als auch das Gesamt-`verdict` in Zeile 420 auf `"ok"`.
- **Testfall:**
  ```python
  doc = ws.new(PART, "shallow_blind")
  doc.session.batch([
      {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 10, "corner": [0, 0, 0]}},
      {"command": "solid.hole", "params": {"position": [20, 20, 10], "direction": [0, 0, -1], "diameter": 4.0, "depth": 3.0}},
  ])
  r = design_rules.check(doc.session)
  assert r["rules"]["thread_depth"]["findings"][0]["status"] == "warn"
  assert r["verdict"] == "warn"  # Ist: 'ok' ("Design check (fdm_0.4): OK - all rules passed")
  ```

---

### 10. [Niedrig] Selbstbestätigender MCP-Rotationstest (Commit `9090fd0`) und unvollständige Prüfungen in `check.py`
- **Fundstelle:** [tests/inventa/check.py:1195-1200](file:///root/repos/inventa/tests/inventa/check.py#L1195-L1200), [tests/inventa/check.py:654-665](file:///root/repos/inventa/tests/inventa/check.py#L654-L665), [tests/inventa/check.py:1002-1012](file:///root/repos/inventa/tests/inventa/check.py#L1002-L1012)
- **Begründung:**
  1. In `tests/inventa/check.py:1196-1200` prüft `ok("mcp: insert_part with rotate places rotated occurrence", not err_rot and ins_rot.get("occurrence") is not None)`. Da `links.insert` das Ergebnis von `component.insert_design` zurückgibt ([inventa/links.py:390-396](file:///root/repos/inventa/inventa/links.py#L390-L396)), enthält `ins_rot` weder die Transformation noch die Bounding-Box; der Test besteht selbst dann, wenn `server.py:insert_part` das Argument `rotate` komplett verwirft.
  2. In `tests/inventa/check.py:661-664` (`rule_th`) wird nur `r_th["rules"]["thread_depth"]["status"] == "ok"` geprüft, was auch bei `findings == []` (Loch gar nicht geprüft) immer wahr ist; ein positiver/negativer Test für `thread_depth` mit echtem Gewinde fehlt ganz.
  3. In `tests/inventa/check.py:1003-1012` wird bei `asm_holes = query.find(asm, "holes")` anders als in Zeile 980 `h["through"]` weggelassen, wodurch Befund #8 (`through == False` in der Baugruppe) unentdeckt blieb.
- **Testfall:**
  ```python
  # In tests/inventa/check.py:1196 "rotate": {"axis": [1, 0, 0], "angle": 90} ersatzlos streichen:
  err_rot, ins_rot = call("insert_part", {"assembly": "rot_unit", "part_path": "bracket.solidcraft", "name": "BracketRot"})
  # Der Test "mcp: insert_part with rotate places rotated occurrence" bleibt trotzdem grün!
  ```
