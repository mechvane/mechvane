> Gemini 3.8 Flash, nicht verifiziert. Lesendes Code-Review von `inventa/links.py`, `inventa/inplace.py`, `inventa/tree.py`, den zugehörigen Aufrufen in `inventa/server.py` sowie den Tests in `tests/inventa/check.py`.
> Datum: 2026-10-21. Geprüfter Commit auf `main`: `bca360960e8fd08bcaa59fd52d5a6578cba335f1`.
> Alle Befunde 1 bis 10 wurden durch eigenständige Reproduktionsskripte unter `/tmp/review-lit-*.py` mit `PYTHONPATH=/root/repos/inventa` gegen die installierte SolidCraft-CLI empirisch bestätigt.

---

# Review-Bericht: `links.py`, `inplace.py`, `tree.py` und MCP-Server

Das Review konzentriert sich auf echte Fehler und funktionale Mängel in drei Kernbereichen:
1. Gelenkverankerung, -prüfung und -reparatur über Dateigrenzen hinweg (`links.py`).
2. Bearbeitung an Ort und Stelle sowie Synchronisation von Baugruppen (`inplace.py`).
3. Modell- und Baugruppenbrowser (`tree.py`).

Zusammenfassend wurden **12 Befunde** ermittelt: 5 mit Schweregrad **Hoch**, 5 mit Schweregrad **Mittel**, 2 mit Schweregrad **Niedrig** (inklusive Testlücken), sowie 2 Punkte unter **Unsicher**.

---

## Übersicht der Befunde

| Nr. | Schweregrad | Modul / Fundstelle | Kurzbeschreibung | Empirisch bestätigt |
|---|---|---|---|---|
| 1 | **Hoch** | `links.py:180-186` | `check()` ignoriert axiale Verschiebung bei Zylindergelenken und In-Plane-Verschiebung bei Ebenengelenken (`status` bleibt fälschlich `"ok"`) | Ja (`review-lit-1`) |
| 2 | **Hoch** | `links.py:77-84` | `_match` ordnet koaxiale Zylinder (z. B. Senkungen, Stufenbohrungen) alphabetisch erstem Feature zu | Ja (`review-lit-2`) |
| 3 | **Hoch** | `links.py:616-625` | `update_links` stürzt mit `SolidCraftError` ab, wenn fixierte Unterbaugruppe verschobene Teile synchronisiert | Ja (`review-lit-3`) |
| 4 | **Hoch** | `server.py:151-158` | `edit_joint` stürzt bei Umbenennung eines Gelenks mit `KeyError` ab und hinterlässt verwaiste Metadaten | Ja (`review-lit-4`) |
| 5 | **Hoch** | `inplace.py:184-210` | `finish_edit` speichert aktualisierte Baugruppen nicht auf Festplatte; ungeöffnete Zwischenbaugruppen bleiben veraltet | Ja (`review-lit-5`) |
| 6 | **Mittel** | `inplace.py:25-50` | `resolve_occurrence` überspringt bei mehrstufigen Pfaden Zwischenstufen und liefert falsches Bauteil | Ja (`review-lit-6`) |
| 7 | **Mittel** | `links.py:755-758` | `repair` verwirft Gelenkkonfigurationen wie `suppressed`, `angle` und `limits` | Ja (`review-lit-7`) |
| 8 | **Mittel** | `links.py:163-167`, `documents.py:93-97` | Fehlende Bauteildatei führt zum Absturz von `check()`/`update_links()` und leckt Subprozess-Sitzungen | Ja (`review-lit-8`) |
| 9 | **Mittel** | `inplace.py:57-60` | Fallback-Präfixsuche in `resolve_occurrence` wählt falsches Bauteil ohne Trennzeichenprüfung (`PlateWasher` statt `Plate`) | Ja (`review-lit-9`) |
| 10 | **Mittel** | `links.py:207-210` | `resolve_occurrences` verliert bei Pfaden ohne Instanzindex das Subassembly-Präfix und bindet falsche Komponenten | Ja (`review-lit-10`) |
| 11 | **Niedrig** | `tree.py:109, 134-136` | `tree.render` unterschlägt `assembly_features` in Baugruppen vollständig | Codebeleg |
| 12 | **Niedrig** | `tests/inventa/check.py` | Lücken in den Tests für hierarchische Baugruppen, Verschiebungen und Fehlerbehandlung | Codebeleg |

---

## Befunde

### 1. [Hoch] `links.check` ignoriert axiale Verschiebung bei Zylindergelenken und In-Plane-Verschiebung bei Ebenengelenken (`status` fälschlich `"ok"`)

- **Fundstelle:** [inventa/links.py:180-186](file:///root/repos/inventa/inventa/links.py#L180-L186), [inventa/links.py:67-74](file:///root/repos/inventa/inventa/links.py#L67-L74)
- **Was falsch ist:**
  1. `links.record` speichert bei Zylindergelenken gewissenhaft `anchor["axial"]` (den Abstand entlang der Zylinderachse) und bei Ebenengelenken `anchor["offset"]` (den 2D/3D-Versatz zum Flächenschwerpunkt).
  2. In `links.check(ws, doc)` wird für Zylinder jedoch ausschließlich `ok = any(test(f, o, d) for f in named)` mit `test = _on_cylinder` ausgewertet. `_on_cylinder` prüft lediglich:
     ```python
     dist_to_line(o, c["origin"], c["axis"]) < TOL and parallel(z, c["axis"], TOL)
     ```
     Dies ist die unendliche Zylinderachse. `anchor["axial"]` wird **nirgends in `check()` geprüft**. Wandert das Gelenk entlang der Bohrungsachse (z. B. durch Upstream-Bug #3330 vom oberen auf den unteren Rand, oder nach Änderung der Plattendicke weit aus dem Bauteil heraus), liefert `check()` fälschlich `status: "ok"`.
  3. Bei Ebenengelenken prüft `check` nur, ob `found["face"]` (über `_match`) mit `anchor["face"]` übereinstimmt:
     ```python
     found["face"] in {f["name"] for f in named} or _base(found["face"]) == _base(anchor["face"])
     ```
     Der in `record` abgelegte Versatz `anchor["offset"]` wird **überhaupt nicht mit der aktuellen Lage verglichen**. Verschiebt sich ein Gelenk auf derselben Deckfläche um 50 mm zur Seite, meldet `check()` weiterhin `status: "ok"`.
  4. **Auswirkung:** Die Kernfunktion von inventa (das Erkennen von verschobenen Gelenken nach Änderungen) schlägt bei Lageverschiebungen auf denselben Flächen stillschweigend fehl. `update_links(..., repair=True)` repariert solche Gelenke nicht, weil `moved` gar nicht erst gemeldet wird.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Bolzen wird an der Oberkante einer 20 mm dicken Bohrung verankert (`axial = -20.0`). Der Gelenkrahmen verschiebt sich entlang der Achse auf z=0 (`axial = 0.0`, z. B. auf den unteren Rand).
  ```python
  rep = links.check(ws, asm)
  assert rep[0]["status"] == "moved"  # Ist: 'ok'
  ```
- **Bestätigt:** Ja, durch `/tmp/review-lit-1-check-axial-plane.py`.
- **Vorschlag zur Behebung:**
  In `inventa/links.py:check`:
  - Bei Zylindern die axiale Koordinate gegen den Anker prüfen:
    ```python
    if anchor["kind"] == "cylinder":
        c = named[0]["cylinder"]
        cur_axial = g.dot(g.sub(o, c["origin"]), g.unit(c["axis"]))
        ok = any(test(f, o, d) for f in named) and abs(cur_axial - anchor["axial"]) < TOL
    ```
  - Bei Ebenen den aktuellen Schwerpunkt-Versatz gegen `anchor["offset"]` prüfen:
    ```python
    cur_offset = g.sub(o, named[0]["centroid"])
    ok = any(test(f, o, d) for f in named) and found is not None and (
        found["face"] in {f["name"] for f in named} or _base(found["face"]) == _base(anchor["face"])
    ) and g.norm(g.sub(cur_offset, anchor["offset"])) < TOL
    ```

---

### 2. [Hoch] `_match` ordnet koaxiale Zylinder (z. B. Senkungen, Stufenbohrungen) alphabetisch erstem Feature zu

- **Fundstelle:** [inventa/links.py:77-84](file:///root/repos/inventa/inventa/links.py#L77-L84), [inventa/links.py:67-70](file:///root/repos/inventa/links.py#L67-L70)
- **Was falsch ist:**
  Bei Senkungen (DIN 974-1 / ISO 4762), gestuften Zylindern oder koaxialen Innen-/Außenzylindern teilen sich mehrere Zylinderflächen dieselbe geometrische Achsenlinie.
  In `_match`:
  ```python
  cyl = [f for f in faces if _on_cylinder(f, o, z)]
  if cyl:
      f = sorted(cyl, key=lambda f: f["name"])[0]
  ```
  `_on_cylinder` prüft weder den Durchmesser/Radius noch den Höhenbereich der Zylinder. Bei einer Senkbohrung mit zylindrischer Senkung $\varnothing 12$ ($z \in [15, 20]$) und Durchgangsbohrung $\varnothing 6$ ($z \in [0, 15]$) liegen beide Zylinder in `cyl`.
  `sorted(cyl, key=lambda f: f["name"])[0]` wählt rein alphabetisch immer `F2:bore:side:0` vor `F2:cbore:side:0`.
  Wird ein Gelenk an der Senkungsoberkante (z=20, $\varnothing 12$) angelegt, speichert `record` fälschlicherweise die 6-mm-Durchgangsbohrung als Verankerungsfläche und berechnet `axial` bezogen auf den Nullpunkt der Durchgangsbohrung. Ändert sich später die Senktiefe, repariert `links.repair` das Gelenk relativ zur falschen Fläche.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Bauteil mit Senkbohrung: Senkung $\varnothing 12$ oben ($z \in [15, 20]$), Durchgangsloch $\varnothing 6$ unten ($z \in [0, 15]$). Gelenk wird an der Senkungsoberkante bei `[20, 20, 20]` platziert.
  ```python
  entry = links.record(ws, asm, "ScrewJoint", params)
  # Ist: entry["sides"]["a"]["face"] == "F2:bore:side:0" (Durchgangsloch) statt "F2:cbore:side:0" (Senkung)!
  ```
- **Bestätigt:** Ja, durch `/tmp/review-lit-2-cbore-match.py`.
- **Vorschlag zur Behebung:**
  In `_match`: Aus allen kandidierenden Zylindern (`cyl`) denjenigen auswählen, dessen Centroid dem Punkt `o` axial am nächsten liegt:
  ```python
  f = min(cyl, key=lambda f: abs(g.dot(g.sub(o, f["centroid"]), g.unit(f["cylinder"]["axis"]))))
  ```
  Optional zusätzlich prüfen, ob der Radius des Zylinders zur Kreisauswahl im Gelenkaufruf passt.

---

### 3. [Hoch] `update_links` stürzt mit `SolidCraftError` ab, wenn fixierte Unterbaugruppe verschobene Teile synchronisiert

- **Fundstelle:** [inventa/links.py:616-625](file:///root/repos/inventa/inventa/links.py#L616-L625)
- **Was falsch ist:**
  Wird eine Unterbaugruppe mit `grounded=True` eingefügt (z. B. Maschinenrahmen, Gehäuse), setzt `_insert_subassembly` (Zeile 461-465) auch die Kind-Occurrences in der Hauptbaugruppe auf `grounded=True`.
  Verschiebt sich später ein Bauteil in der Konstruktionsdatei der Unterbaugruppe, sammelt `_sync_subassemblies` die neue Position in `to_move`. In Zeile 624-625 ruft es auf:
  ```python
  for oid, target_local in to_move:
      s.cmd("occurrence.move", dict(g.move_params(target_local), occurrence=oid))
  ```
  SolidCraft verweigert `occurrence.move` auf fixierten Teilen grundsätzlich und wirft:
  `SolidCraftError: invalid parameters for occurrence.move: <Part> is grounded`.
  (Während Zeilen 632-641 für das Neuerzeugen von Unterbaugruppen-Gelenken die Occurrences temporär entfixieren, fehlt diese Schutzmaßnahme vor Zeile 625 völlig).
- **Szenario (Eingabe -> falsches Ergebnis):**
  Unterbaugruppe `Sub` mit fixiertem Teil `Plate` wird in `Top` eingefügt (`grounded=True`).
  In `Sub` wird `Plate` verschoben und gespeichert.
  Eingabe: `links.update_links(ws, top)`
  Falsches Ergebnis: Unbehandelter Programmabsturz mit `SolidCraftError: invalid parameters for occurrence.move: Plate:1 is grounded`.
- **Bestätigt:** Ja, durch `/tmp/review-lit-3-grounded-move.py`.
- **Vorschlag zur Behebung:**
  In `_sync_subassemblies` vor dem Bewegen die Fixierung lösen und danach wiederherstellen:
  ```python
  for oid, target_local in to_move:
      was_gr = occs.get(oid, {}).get("grounded", False)
      if was_gr:
          s.cmd("occurrence.ground", {"occurrence": oid, "grounded": False})
      s.cmd("occurrence.move", dict(g.move_params(target_local), occurrence=oid))
      if was_gr:
          s.cmd("occurrence.ground", {"occurrence": oid, "grounded": True})
  ```

---

### 4. [Hoch] `server.edit_joint` stürzt bei Umbenennung eines Gelenks mit `KeyError` ab und hinterlässt verwaiste Metadaten

- **Fundstelle:** [inventa/server.py:151-158](file:///root/repos/inventa/inventa/server.py#L151-L158), [inventa/links.py:107-113](file:///root/repos/inventa/inventa/links.py#L107-L113)
- **Was falsch ist:**
  SolidCrafts `joint.edit`-Befehl unterstützt den Parameter `name`, um ein bestehendes Gelenk umzubenennen.
  In `server.py`:
  ```python
  r = doc.session.cmd("joint.edit", dict(params, joint=joint))
  return {"joint": r, "anchors": links.record(ws, doc, joint)["sides"]}
  ```
  Wenn `params` ein neues `"name": "NewName"` enthält, benennt SolidCraft das Gelenk erfolgreich um.
  Unmittelbar danach ruft `edit_joint` jedoch `links.record(ws, doc, joint)` mit dem **alten** Namen `joint` auf. `record()` liest `_frames(s)` aus. Da das Gelenk jetzt `NewName` heißt, existiert `joint` nicht mehr in `_frames(s)`, und Zeile 112 wirft `KeyError: no joint 'OldName'`.
  Der MCP-Aufruf bricht mit einem Fehler ab; in den Dokument-Metadaten verbleibt der alte Eintrag unter `old_name`, während der umbenannte Gelenkname völlig ungesichert ist.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Gelenk `Rev1` umbenennen:
  Eingabe: `edit_joint("asm", "Rev1", {"name": "Rev1_Renamed"})`
  Falsches Ergebnis: Absturz mit `KeyError: "no joint 'Rev1'"`.
- **Bestätigt:** Ja, durch `/tmp/review-lit-4-rename-joint.py`.
- **Vorschlag zur Behebung:**
  In `inventa/server.py:edit_joint`:
  ```python
  new_name = params.get("name", joint)
  r = doc.session.cmd("joint.edit", dict(params, joint=joint))
  if new_name != joint:
      links.forget(doc, joint)
  return {"joint": r, "anchors": links.record(ws, doc, new_name)["sides"]}
  ```

---

### 5. [Hoch] `finish_edit` speichert offene/aktualisierte Baugruppen nicht auf Festplatte; ungeöffnete Zwischenbaugruppen bleiben veraltet

- **Fundstelle:** [inventa/inplace.py:184-210](file:///root/repos/inventa/inventa/inplace.py#L184-L210), [inventa/links.py:523-537](file:///root/repos/inventa/inventa/links.py#L523-L537)
- **Was falsch ist:**
  1. `finish_edit` speichert zwar das geänderte Bauteil (`part_doc.save()`), ruft aber nach dem `update_links` in den verknüpfenden Baugruppen **kein `asm_doc.save()`** auf. Alle Baugruppen-Updates verbleiben ausschließlich im flüchtigen SolidCraft-Speicher. Werden die Baugruppen geschlossen oder stürzt der Server ab, sind die Änderungen in den Baugruppen verloren.
  2. Gravierender Datenverlust bei Unterbaugruppen: Befindet sich das bearbeitete Teil in einer Unterbaugruppe `sub.solidcraft`, die in `top.solidcraft` eingebunden ist, ist `sub.solidcraft` beim In-Place-Editing über `top` typischerweise **nicht** in `ws.docs` geöffnet. `finish_edit` aktualisiert nur offene Dokumente in `ws.docs`. Die Datei `sub.solidcraft` auf der Festplatte bleibt im alten Zustand.
  3. Führt `top` später ein erneutes `update_links` aus, liest `_sync_subassemblies` die veraltete `sub.solidcraft` von Festplatte (`ws.reader(file)`) und überschreibt die in der Hauptbaugruppe vorgenommenen Änderungen wieder mit dem veralteten Stand.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Unterbaugruppe `Sub` mit `Plate` (Breite 40 mm) in `Top` verbaut. `Plate` wird per `edit_in_place(top, "Sub:1/Plate:1")` auf 80 mm verbreitert und mit `finish_edit("Plate")` abgeschlossen.
  Eingabe: `finish_edit("Plate")`
  Falsches Ergebnis: `sub.solidcraft` auf der Festplatte verbleibt bei 40 mm. `top.solidcraft` wird auf der Festplatte nicht persistiert.
- **Bestätigt:** Ja, durch `/tmp/review-lit-5-sub-stale-save.py`.
- **Vorschlag zur Behebung:**
  In `inventa/inplace.py:finish_edit`:
  - Für jede offene Baugruppe nach `update_links` zwingend `asm_doc.save()` aufrufen.
  - Wenn ein Teil zu einer Unterbaugruppe gehört, deren Datei nicht in `ws.docs` geöffnet ist, muss diese Unterbaugruppendatei temporär geöffnet, per `update_links` synchronisiert, gespeichert und wieder geschlossen werden, bevor übergeordnete Baugruppen aktualisiert werden.

---

### 6. [Mittel] `inplace.resolve_occurrence` überspringt bei mehrstufigen Pfaden Zwischenstufen und liefert falsches Bauteil

- **Fundstelle:** [inventa/inplace.py:25-50](file:///root/repos/inventa/inventa/inplace.py#L25-L50)
- **Was falsch ist:**
  In `resolve_occurrence`:
  ```python
  parts = [p.strip() for p in str(occurrence).split("/") if p.strip()]
  if len(parts) >= 2:
      parent_ref, leaf = parts[0], parts[-1]
  ```
  Es werden bei jedem Pfad mit Schrägstrichen nur das erste Element (`parts[0]`) und das letzte Element (`parts[-1]`) betrachtet; alle Zwischenglieder werden verworfen.
  Enthält eine Baugruppe `Top` eine Baugruppe `Sub2`, und `Sub2` enthält zwei Unterbaugruppen `Sub1A` (bei x=0 mit Bauteil `PartP`) und `Sub1B` (bei x=50 mit Bauteil `PartP`), dann sucht die Funktion in `Sub2["parts"]` nach `leaf` (`PartP`) und nimmt den ersten Treffer (das `PartP` aus `Sub1A` bei x=0).
  Die Koordinatentransformation liefert x=0 statt x=50, und `to_part_coords` rechnet mit einem falschen Offset von 50 mm.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Baugruppenstruktur: `Top -> Sub2 -> Sub1B (x=50) -> PartP`.
  Eingabe: `resolve_occurrence(top, "Sub2:1/Sub1B:1/PartP:1")`
  Falsches Ergebnis: Liefert `PartP` aus `Sub1A` mit x=0.0 statt x=50.0.
- **Bestätigt:** Ja, durch `/tmp/review-lit-6-nested-path.py`.
- **Vorschlag zur Behebung:**
  Pfadkomponenten hierarchisch von links nach rechts rekursiv durchlaufen, anstatt nur `parts[0]` und `parts[-1]` zu verwenden.

---

### 7. [Mittel] `links.repair` verwirft Gelenkkonfigurationen wie `suppressed`, `angle` und `limits`

- **Fundstelle:** [inventa/links.py:755-758](file:///root/repos/inventa/inventa/links.py#L755-L758)
- **Was falsch ist:**
  In `links.repair()`:
  ```python
  live = next(j for j in s.cmd("joint.list").get("joints", []) if j["name"] == joint)
  params.update({k: live[k] for k in ("flip", "offset") if k in live})
  s.cmd("joint.delete", {"joint": joint})
  s.cmd("joint.create", params)
  ```
  Es werden aus dem Live-Zustand des Gelenks nur `flip` und `offset` in die Neuerzeugung übernommen.
  1. War das Gelenk unterdrückt (`suppressed: True`), wird es nach der Reparatur stillschweigend reaktiviert (`suppressed: False`).
  2. Hatte das Gelenk einen Drehwinkel (`angle`, z. B. 45°), wird es mit 0° neu angelegt.
  3. Hatte das Gelenk Bewegungsgrenzen (`limits`), gehen diese ersatzlos verloren.
  (In `_recreate_sub_joint`, Zeilen 269-274 und 307-308, werden diese Parameter vorbildlich berücksichtigt; in `repair` fehlen sie).
- **Szenario (Eingabe -> falsches Ergebnis):**
  Drehgelenk `Rev1` mit `suppressed=True` und `angle=45` versehen. Nach Bauteiländerung wird `update_links(..., repair=True)` aufgerufen.
  Falsches Ergebnis: Gelenk ist nach Reparatur wieder aktiv (`suppressed: False`) und Drehwinkel steht auf 0.
- **Bestätigt:** Ja, durch `/tmp/review-lit-7-repair-suppressed-angle.py`.
- **Vorschlag zur Behebung:**
  In `links.repair`:
  `params.update({k: live[k] for k in ("flip", "offset", "angle") if k in live})`
  und nach `joint.create`:
  ```python
  if live.get("suppressed"):
      s.cmd("joint.edit", {"joint": joint, "suppressed": True})
  ```

---

### 8. [Mittel] Fehlende Bauteildatei führt zum Absturz von `check()`/`update_links()` und leckt Subprozess-Sitzungen

- **Fundstelle:** [inventa/links.py:163-167](file:///root/repos/inventa/inventa/links.py#L163-L167), [inventa/links.py:711-715](file:///root/repos/inventa/inventa/links.py#L711-L715), [inventa/documents.py:93-97](file:///root/repos/inventa/inventa/documents.py#L93-L97)
- **Was falsch ist:**
  1. `links.check` und `links.repair` rufen `ws.reader(file)` auf, ohne vorher zu prüfen, ob die Datei existiert (`Path(file).is_file()`).
  2. `ws.reader(path)` erzeugt zuerst eine neue SolidCraft-Sitzung (`s = self.session()`) und ruft dann `s.tool("open", ...)` auf. Wenn die Datei fehlt, wirft `open` eine `SolidCraftError`-Exception.
  3. Weil `ws.reader` keinen `try/except`-Block besitzt, wird die neu gestartete Sitzung `s` niemals geschlossen und läuft als Zombie-Prozess weiter (Subprozess-Ressourcenleck).
  4. Gleichzeitig stürzt `check()` bzw. `update_links()` mit einer unbehandelten Exception ab, anstatt im Bericht `status: "file_missing"` zurückzugeben.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Eine Baugruppe verknüpft ein Bauteil. Das Bauteil wird im Arbeitsordner gelöscht oder verschoben.
  Eingabe: `links.check(ws, asm)` oder MCP `check_joints("asm")`
  Falsches Ergebnis: Unbehandelter Fehler `SolidCraftError: No such file or directory` und verwaister SolidCraft-CLI-Prozess im Hintergrund.
- **Bestätigt:** Ja, durch `/tmp/review-lit-8-missing-file-crash.py`.
- **Vorschlag zur Behebung:**
  1. In `documents.py:Workspace.reader`:
     ```python
     s = self.session()
     try:
         s.tool("open", {"path": str(path)})
         return s
     except Exception:
         s.close()
         raise
     ```
  2. In `links.py:check`:
     ```python
     if not Path(file).is_file():
         report.append(dict(item, status="file_missing"))
         continue
     ```

---

### 9. [Mittel] Ungenaue Präfixsuche in `resolve_occurrence` (Fallback) wählt falsches Bauteil ohne Trennzeichenprüfung

- **Fundstelle:** [inventa/inplace.py:57-60](file:///root/repos/inventa/inventa/inplace.py#L57-L60)
- **Was falsch ist:**
  Im Fallback-Zweig von `resolve_occurrence`:
  ```python
  target_leaf = leaf if leaf in children else next(
      (name for name in children if name == f"{p_comp['name']}_{leaf}" or name.startswith(leaf)), None
  )
  ```
  `name.startswith(leaf)` prüft ohne Wortgrenze (ohne Doppelpunkt `:`).
  Gibt es in der Baugruppe ein Bauteil `PlateWasher:1` und ein Bauteil `Plate:1`, und sucht der Aufrufer nach `"Plate"`, liefert `name.startswith("Plate")` in Dictionary-Reihenfolge sofort `PlateWasher:1`.
  `edit_in_place` öffnet daraufhin die falsche Bauteildatei, und `to_part_coords` rechnet mit den Koordinaten der Unterlegscheibe statt der Platte.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Unterbaugruppe enthält `PlateWasher:1` und `Plate:1`.
  Eingabe: `resolve_occurrence(top, "Sub/Plate")`
  Falsches Ergebnis: Liefert `PlateWasher:1` statt `Plate:1`.
- **Bestätigt:** Ja, durch `/tmp/review-lit-9-prefix-matching.py`.
- **Vorschlag zur Behebung:**
  Auf echte Komponenten-Namen oder Trennzeichen prüfen:
  ```python
  target_leaf = leaf if leaf in children else next(
      (name for name in children if name.split(":")[0] in (leaf, f"{p_comp['name']}_{leaf}")), None
  )
  ```

---

### 10. [Mittel] `links.resolve_occurrences` verliert bei Pfaden ohne Instanzindex das Subassembly-Präfix und bindet falsche Komponenten

- **Fundstelle:** [inventa/links.py:207-210](file:///root/repos/inventa/inventa/links.py#L207-L210)
- **Was falsch ist:**
  In `resolve_occurrences`:
  ```python
  if p_comp:
      children = {o["name"] for o in p_comp.get("children", [])}
      if leaf not in children and f"{p_comp['name']}_{leaf}" in children:
          leaf = f"{p_comp['name']}_{leaf}"
  out[side] = dict(out[side], occurrence=leaf)
  ```
  In SolidCraft besitzen Occurrences immer einen Instanzindex (z. B. `Sub_Plate:1`).
  Wird ein Pfad wie `"Sub:1/Plate"` übergeben (ohne `:1` am Ende):
  - `leaf` ist `"Plate"`.
  - `f"{p_comp['name']}_{leaf}"` ist `"Sub_Plate"`.
  Weder `"Plate"` noch `"Sub_Plate"` existieren exakt so in `children` (dort liegt nur `"Sub_Plate:1"`).
  Die Ersetzung schlägt fehl; `out[side]["occurrence"]` bleibt `"Plate"`.
  Existiert auf Hauptebene ein anderes Bauteil `Plate:1`, bindet SolidCraft das Gelenk fälschlich an das Hauptbauteil statt an das Teil in der Unterbaugruppe!
- **Szenario (Eingabe -> falsches Ergebnis):**
  Hauptbaugruppe enthält `Plate:1` und Unterbaugruppe `Sub` (mit `Sub_Plate:1`).
  Eingabe: `resolve_occurrences(top.session, {"b": {"occurrence": "Sub:1/Plate"}})`
  Falsches Ergebnis: Liefert `occurrence: "Plate"`, wodurch das Gelenk an `Plate:1` der Hauptebene gebunden wird.
- **Bestätigt:** Ja, durch `/tmp/review-lit-10-resolve-occurrences.py`.
- **Vorschlag zur Behebung:**
  Beim Abgleich in `children` auch Präfixe mit `:1` oder vor dem Doppelpunkt berücksichtigen:
  ```python
  match = next((name for name in children if name in (leaf, f"{p_comp['name']}_{leaf}") or name.split(":")[0] in (leaf, f"{p_comp['name']}_{leaf}")), None)
  if match:
      leaf = match
  ```

---

### 11. [Niedrig] `tree.render` unterschlägt `assembly_features` in Baugruppen vollständig

- **Fundstelle:** [inventa/tree.py:109](file:///root/repos/inventa/inventa/tree.py#L109), [inventa/tree.py:134-136](file:///root/repos/inventa/inventa/tree.py#L134-L136)
- **Was falsch ist:**
  `assembly_tree` liest `assembly_features: root.get("features", [])` aus.
  `tree.render(tree)` rendert für Baugruppen jedoch nur `occurrences` und `groups`. Baugruppen-Features (wie Durchgangsbohrungen oder Schnitte im Baugruppenkontext) werden in der Textansicht des Browsers komplett ignoriert.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Baugruppe besitzt ein Baugruppenfeature (z. B. Montageausklinkung).
  Eingabe: `browser("asm")` (Textausgabe)
  Falsches Ergebnis: Das Feature taucht im Text-Browser nicht auf.
- **Bestätigt:** Codebeleg.
- **Vorschlag zur Behebung:**
  In `tree.render` für Baugruppen analog zu Bauteilen vorhandene `assembly_features` ausgeben:
  ```python
  if tree.get("assembly_features"):
      lines.append("  [Baugruppen-Features]")
      for f in tree["assembly_features"]:
          lines.append(f"    {f['name']} [{f['type']}]")
  ```

---

### 12. [Niedrig] Fehlende Tests für Randfälle und fehlerhafte Annahmen in `tests/inventa/check.py`

- **Fundstelle:** [tests/inventa/check.py:443-574](file:///root/repos/inventa/tests/inventa/check.py#L443-L574), [tests/inventa/check.py:1018-1100](file:///root/repos/inventa/tests/inventa/check.py#L1018-L1100)
- **Was falsch ist:**
  Die bestehende Testsuite weist mehrere Lücken auf, wodurch kritische Randfälle nicht abgedeckt sind:
  1. **Axiale und planare Gelenkverschiebung:** Getestet wird bisher nur das Springen eines Gelenks auf eine andere Bohrung. Verschiebungen entlang der Achse oder auf derselben Fläche werden nicht getestet (Befund #1 blieb deshalb unbemerkt).
  2. **Koaxiale Zylinder / Senkbohrungen:** Es gibt keinen Test für Gelenkverankerungen an Senkbohrungen (Befund #2).
  3. **Hierarchische Unterbaugruppen:** `subassemblies(ws)` testet nur eine einzige Baugruppenebene (`Top -> Sub -> Part`). Mehrstufige Pfade (`Top -> Sub2 -> Sub1 -> Part`) fehlen (Befund #6).
  4. **Gelenkkonfiguration bei Reparatur:** Tests für `repair` prüfen nur `flip` und `offset`, nicht jedoch `suppressed`, `angle` oder `limits` (Befund #7).
  5. **Fehlende Dateien:** Es gibt keine Tests für gelöschte oder umbenannte Bauteildateien in `update_links` oder `check_joints` (Befund #8).
  6. **Disk-Persistenz nach In-Place-Editing:** `edit_in_place_checks` prüft `finish_edit` nur im flüchtigen Sitzungsspeicher, ohne zu prüfen, ob die Baugruppendateien auf der Festplatte synchronisiert und gespeichert wurden (Befund #5).
- **Schweregrad:** Niedrig (Testsuite-Lücke).
- **Vorschlag zur Behebung:**
  Die Testfälle aus `/tmp/review-lit-*.py` als dedizierte Testfunktionen in `tests/inventa/check.py` übernehmen.

---

## Unsicher (Vermutungen ohne abschließenden Beweis)

1. **Akkumulierte Transformationsmatrizen in `_occurrences` bei mehrstufigen Rotationen:**
   In `links.py:41-47`:
   ```python
   def world_transform(o):
       m = o["transform"]
       cur = o
       while cur.get("parent", 0) != 0 and cur["parent"] in first_of:
           cur = first_of[cur["parent"]]
           m = g.mat_mul(cur["transform"], m)
       return m
   ```
   SolidCraft verwendet die Konvention $[x, y, z, 1] \cdot M$. `mat_mul(parent, child)` multipliziert `parent * child`.
   In der Schleife wird `cur["transform"]` sukzessive von links an `m` multipliziert. Bei mehrfach verschachtelten, rotierten Unterbaugruppen (`Top (rot)` -> `Sub (rot)` -> `Part (rot)`) muss verifiziert werden, ob SolidCrafts `occurrence.list` lokale Relativtransformationen oder bereits akkumulierte Baugruppentransformationen liefert, um Doppelmultiplikationen auszuschließen.

2. **Ausrichtung bei Fallback auf `joint.as_built`:**
   In `_recreate_sub_joint` (Zeile 303-306): Wenn `joint.create` scheitert, fällt die Erzeugung auf `s.cmd("joint.as_built", {"type": j["type"], "name": jname, "a": top_a, "b": top_b})` zurück. Bei `joint.as_built` werden keine Rahmenvektoren (`frame_a`, `frame_b`) übergeben. Für Dreh- und Zylindergelenke ist unklar, wie SolidCraft ohne explizite Achse die Bewegungsrichtung ableitet (möglicherweise aus der Flächengeometrie zum Zeitpunkt des Aufrufs).

---

### Stichprobe durch Claude (2026-10-21)

Die Reproduktionsskripte liegen unter `docs/research/2026-10-21-review-lit-skripte/`, aufzurufen mit `PYTHONPATH=. python3 <skript>`. Befund 7 (`repair` setzt `suppressed` zurück) und Befund 9 (Präfixsuche wählt `PlateWasher:1` statt `Plate:1`) habe ich nachgefahren, beide sind bestätigt, und der Aufbau ist realistisch. Die übrigen Befunde sind nicht gegengeprüft.
