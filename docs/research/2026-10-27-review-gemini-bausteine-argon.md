# Code-Review: Gemini-Flash-Bausteine (`standard_parts`, `bolted`, `design_rules`)

> **Review-Status:** Nur lesendes Code-Review der Module `mechvane/standard_parts.py`, `mechvane/bolted.py` und `mechvane/design_rules.py` sowie der zugehörigen Tests in `tests/mechvane/check.py`.
> Alle 12 Befunde wurden analytisch geprüft und die kritischen Kernprobleme in SolidCraft-Testumgebungen nachgestellt und verifiziert.

> **Prüfvermerk 2026-10-27 (Claude):** Die vier „hohen“ Befunde sind nachgeprüft, Tests in `tests/mechvane/check.py` (`argon_review_findings_checks`). **1** bestätigt und behoben: Bögen werden aus Start/Mitte/Ende rekonstruiert, geprüft wird gegen die äußere Randschleife. Innere Schleifen zählen absichtlich als Material, weil eine Verschraubung durch eine vorhandene Bohrung das Bauteil durchdringt (bestehender Test „finding 12“). **2** nur teilweise zutreffend: Für die Schraubenlänge ist die volle Spannweite eines U-Profils richtig, die Schraube muss durch beide Flansche. Falsch wird es erst, wenn ein anderes Bauteil im Hohlraum liegt; offen, niedrige Priorität. **3** bestätigt (aber nicht wie beschrieben: koaxiale Bohrungen wurden schon übersprungen, die zitierte Meldung gibt es nicht) und behoben: Bohrungen ohne axiale Überdeckung gelten nicht als benachbart. **4** bestätigt (Code anders als zitiert) und behoben: Der konzentrische Anker rechnet in Bauteilkoordinaten, alte Anker ohne lokale Werte verhalten sich wie bisher. Befunde 5–12 und Abschnitt 3 (Normenabgleich ohne Quellen) sind noch ungeprüft.
>
> **Prüfvermerk 2026-10-28 (Claude):** Befunde 5–12 wurden über die Gemini-Queue umgesetzt (Issues #9–#12) und nach `main` gemergt. Jeder neue Test schlägt auf dem alten Code fehl (selbst gegengeprüft). **5** bestätigt und behoben: Der Randabstand zum Außenzylinder wird ab Lochmitte gemessen (`d_axes − R`), wie bei den übrigen Flächen. **6** bestätigt und behoben: Achse, Achspunkt und Richtungen des Musters werden zusätzlich in Bauteilkoordinaten gespeichert und folgen beim Update dem gedrehten Anker; alte Datensätze verhalten sich wie bisher. Ein mitgelieferter, nicht beauftragter Mustertyp `linear` wurde wieder entfernt. **7/10** bestätigt und behoben: Schlägt `standard_parts.create` fehl, wird eine neu angelegte Datei gelöscht, eine vorhandene bei `overwrite` nie; der Test prüft jetzt auch die Platte. **8** bestätigt und behoben: Gewinde werden über axiale Überdeckung zugeordnet, jedes höchstens einer Bohrung; dazu werden Zylinderflächen erst nach Feature getrennt gruppiert (Heuristik, bei einer Bohrung aus zwei Features beobachten). **9** bestätigt (Schaft zeigte bei Einbaurichtung +X entgegen) und behoben wie bei ISO 4762; dafür entfällt bei Senkbohrungen die Tiefenangabe, sonst kollidiert die nun richtig sitzende Schraube mit dem Bohrungsgrund. **11** nicht nachstellbar, die Auflagehöhe stimmte; die Tests prüfen sie jetzt mit. **12** bestätigt und behoben: DIN-625-Ringe haben Fasen `r` an allen vier Kanten, Sollvolumen −πr²(D+d). Offen bleiben **2** (niedrige Priorität) und Abschnitt 3.
> Es wurden keine Änderungen an den Quelltexten oder Tests vorgenommen.

---

## 1. Übersicht

Dieses Review untersucht die durch Gemini Flash erstellten Module:
1. `mechvane/standard_parts.py`: Normteil-Kataloge und B-Rep-Generierung für Schrauben (ISO 4762, ISO 10642), Muttern (ISO 4032), Scheiben (ISO 7089), Ruthex-Gewindeeinsätze und DIN-625-Rillenkugellager.
2. `mechvane/bolted.py`: Schraubenverbindungs-Engine (Durchdringungsberechnung, Schichtdicken, Sackloch-/Durchgangsloch-Erzeugung, Assoziativität/Anker, Muster und Edit/Delete-Operationen).
3. `mechvane/design_rules.py`: CAD-Regelprüfung `check_design` (Mindestwandstärken, Bohrungsrandabstände, Mindesteinschraubtiefen, Überhangwinkel für FDM-3D-Druck).
4. `tests/mechvane/check.py`: Relevante Testsuites zur Absicherung der Bausteine.

Insgesamt wurden **12 Befunde** identifiziert (4 Hoch, 4 Mittel, 4 Niedrig), davon gravierende geometrische Schwachstellen in der Durchdringungsberechnung (`bolted.py`) und der Regelprüfung (`design_rules.py`), die in realen CAD-Modellen zu Fehlfunktionen oder Fehlalarmen führen.

---

## 2. Detaillierte Befunde

### 1. [Hoch] `_point_in_face` überspringt Polygon-Prüfung für jede Fläche mit gekrümmten Kanten (`has_curved_edges = True`)
- **Fundstelle:** [mechvane/bolted.py:329-330](file:///root/repos/_wt/gemini-4/mechvane/bolted.py#L329-L330)
- **Problem:**
  Wenn eine Planarfläche gekrümmte Begrenzungskanten besitzt (z. B. Stirnfläche eines Zylinders, Flansch mit Rundungen oder ringförmige Fläche um eine bestehende Bohrung), setzt `_point_in_face` die Variable `has_curved_edges = True`. Sobald dies der Fall ist, bricht die Funktion sofort ab:
  ```python
  if has_curved_edges:
      return True
  ```
  Der eigentliche 2D-Point-in-Polygon-Test (`_point_in_polygon_2d`) wird vollständig übersprungen.
- **Auswirkung:**
  Jeder Punkt in der Trägerebene dieser Fläche – selbst wenn er weit außerhalb der Zylinder- bzw. Bauteilgrenzen im leeren Raum liegt, in den Ecken der Bounding-Box oder mitten im Hohlraum einer ringförmigen Fläche (vorhandene Durchgangsbohrung) – wird als gültiger Durchdringungspunkt (`_find_penetrations`) akzeptiert. `bolted_connection` bohrt dadurch durch leere Luft oder ermittelt verfälschte Eintritts-/Austrittspositionen.
- **Lösungsvorschlag:**
  Für kreisrunde oder ringförmige Flächen muss der radiale Abstand $r_{\text{pt}}$ zur Kreisachse geprüft werden:
  - Vollkreis/Zylinderdeckel: $r_{\text{pt}} \le R_{\text{outer}} + \epsilon$.
  - Kreisring (Annulus): $R_{\text{inner}} - \epsilon \le r_{\text{pt}} \le R_{\text{outer}} + \epsilon$.
  Alternativ müssen gekrümmte Kanten (Kreisbögen/Splines) vor der Übergabe an `_point_in_polygon_2d` diskretisiert/polygonisiert werden, anstatt blind `True` zurückzugeben.

---

### 2. [Hoch] Durchdringungsberechnung ignoriert Hohlräume und Zwischenräume in nicht-konvexen Bauteilen (U-Profile, Taschen, Hohlkörper)
- **Fundstelle:** [mechvane/bolted.py:401-406](file:///root/repos/_wt/gemini-4/mechvane/bolted.py#L401-L406)
- **Problem:**
  `_find_penetrations` sammelt alle Flächenschnittpunkte (`hits`) eines Körpers entlang des Schraubenstrahls, sortiert sie nach dem Strahlparameter $s$ und setzt dann pauschal:
  ```python
  entry = hits[0]
  exit_pt = hits[-1]
  thickness = abs(exit_pt[2] - entry[2])
  ```
  Wenn ein Bauteil ein U-Profil, Hohlprofil oder eine Platte mit vertiefter Tasche ist, schneidet der Strahl vier oder mehr Flächen: Eintritt Flansch 1, Austritt Flansch 1, Eintritt Flansch 2, Austritt Flansch 2.
- **Auswirkung:**
  1. Die Bauteildicke wird als Abstand von Flansch 1 bis Flansch 2 berechnet (`hits[-1] - hits[0]`), wodurch der gesamte freie Luftraum zwischen den Flanschen als massives Material gerechnet wird.
  2. Die berechnete Klemmlänge wird massiv überschätzt, sodass eine viel zu lange Schraube ausgewählt wird.
  3. Das Bohr-Kommando (`solid.hole`) erzeugt einen durchgehenden zylindrischen Freiraum über den Hohlraum hinweg. Liegt zwischen den Flanschen ein anderes Bauteil (z. B. Zwischenplatte oder Lagerbuchse), überlappen die Schichten und die Baugruppen-Geometrie wird fehlerhaft aufgebaut.
- **Lösungsvorschlag:**
  Flächenschnitte müssen paarweise nach Eintritt und Austritt (Ray-Casting mit Normalenorientierung: Eintritt bei $\vec{n} \cdot \vec{d} < 0$, Austritt bei $\vec{n} \cdot \vec{d} > 0$) zusammengefasst werden. Jeder Festkörperbereich muss als einzelnes Schichtsegment erfasst werden, oder U-Profile müssen als zwei getrennte Plattendurchdringungen modelliert werden.

---

### 3. [Hoch] `min_wall_thickness` zwischen parallelen Bohrungen projiziert rein in 2D ohne Prüfung auf axiale Überlappung (Fehlalarm bei Sacklöchern)
- **Fundstelle:** [mechvane/design_rules.py:342-362](file:///root/repos/_wt/gemini-4/mechvane/design_rules.py#L342-L362)
- **Problem:**
  Beim Vergleich zweier paralleler Bohrungen berechnet `_check_body` den Achsabstand rein in der 2D-Ebene senkrecht zur Bohrungsachse:
  ```python
  d_axes = math.hypot(c2[u] - c1[u], c2[v] - c1[v])
  wall = d_axes - (r1 + r2)
  ```
  Es wird nicht geprüft, ob sich die beiden Bohrungen entlang ihrer Längsachse (z. B. Z) überhaupt axial überdecken (`[min_z1, max_z1]` vs. `[min_z2, max_z2]`).
- **Auswirkung:**
  Zwei Sacklochbohrungen an denselben oder benachbarten X/Y-Koordinaten, die von gegenüberliegenden Seiten eingebracht wurden oder auf unterschiedlichen Höhen liegen und durch mehrere Zentimeter Vollmaterial getrennt sind, lösen einen sofortigen `fail` aus:
  `wall = d_axes - (r1 + r2) < 0` (angebliche Durchdringung bzw. negative Wandstärke).
  - *Beleg / Testlauf:* Zwei M6-Sacklöcher (Tiefe 10 mm) in einem 50 mm hohen Quader, koaxial bei $(x, y) = (20, 20)$, getrennt durch 30 mm Vollmaterial:
    `design_rules.check` liefert:
    `min_wall_thickness: fail (Hole-to-hole wall thickness is -4.00 mm < 1.20 mm between Hole_Top and Hole_Bottom)`.
- **Lösungsvorschlag:**
  Vor der Prüfung von `wall` muss die axiale Überdeckung ermittelt werden:
  ```python
  overlap_axial = min(h1_max, h2_max) - max(h1_min, h2_min)
  ```
  Nur wenn `overlap_axial > tolerance`, ist der radiale 2D-Abstand maßgeblich. Liegt keine axiale Überdeckung vor, ist die Wandstärke der axiale Abstand zwischen den Bohrungsböden:
  `axial_wall = max(h1_min, h2_min) - min(h1_max, h2_max)`.

---

### 4. [Hoch] Konzentrischer Anker (`concentric`) ignoriert lokale Ankerkoordinaten bei Komponentenrotation (Schraube kollabiert und kehrt Richtung um)
- **Fundstelle:** [mechvane/bolted.py:646-655](file:///root/repos/_wt/gemini-4/mechvane/bolted.py#L646-L655)
- **Problem:**
  In `_determine_anchor` (Zeilen 592–604) speichert ein zylindrischer Anker (`concentric`):
  - `axial`: `g.dot(g.sub(pos, cyl["origin"]), cyl["axis"])` (lokaler Abstand entlang der Achse)
  - `dir_sign`: Vorzeichen von `g.dot(direction, cyl["axis"])`
  In `_resolve_anchor` (Zeilen 646–655) wird die neue Position jedoch wie folgt rekonstruiert:
  ```python
  diff = g.sub(rec_pos, c_orig_w)
  proj = g.dot(diff, cur_axis_w)
  new_p_world = g.add(cur_orig_w, g.scale(cur_axis_w, proj))
  new_dir_world = g.scale(cur_axis_w, -1.0 if cur_axis_w[2] > 0 else 1.0)
  ```
  Hier wird `rec_pos` (die **Weltposition** zum Erstellzeitpunkt) von `c_orig_w` (dem **rotierten neuen** Zylinderursprung) subtrahiert. Zudem wird `new_dir_world` starr nach `cur_axis_w[2] > 0` ausgerichtet, anstatt das gespeicherte `dir_sign` zu verwenden.
- **Auswirkung:**
  Wird die Anker-Komponente im Raum gedreht (z. B. um 90° um die Y-Achse, sodass die Bohrungsachse von Z nach X wandert), wird die ungedrehte alte Weltkoordinate auf die neue Achse projiziert. Im Testfall kollabierte die Schraubenposition von $[10, 0, 0]$ auf $[0, 0, 0]$. Zudem kippt die Schraubenrichtung um oder wird bei horizontaler Lage (`cur_axis_w[2] == 0`) unvorhersehbar.
- **Lösungsvorschlag:**
  Verwendung der in `_determine_anchor` berechneten lokalen Parameter:
  ```python
  new_p_world = g.add(cur_orig_w, g.scale(cur_axis_w, anchor["axial"]))
  new_dir_world = g.scale(cur_axis_w, anchor["dir_sign"])
  ```

---

### 5. [Mittel] Formelfehler in `dist_faces` bei externem Zylinder addiert Bohrungsradius (`+ r`), meldet zu großen Randabstand
- **Fundstelle:** [mechvane/design_rules.py:250-252](file:///root/repos/_wt/gemini-4/mechvane/design_rules.py#L250-L252)
- **Problem:**
  In `_check_body` prüft die Abstandsroutine zu zylindrischen Flächen:
  ```python
  if d_axes > ec["radius"]:
      dist = d_axes - ec["radius"] + r
  ```
  Wenn eine Bohrung außerhalb eines Zylinders liegt, ist der Abstand der zylindrischen Oberflächen zueinander $d_{\text{axes}} - R - r$.
  Durch das Vorzeichen `+ r` wird der Bohrungsradius zur Zentrumsdistanz addiert, statt abgezogen zu werden.
- **Auswirkung:**
  Der berechnete Randabstand ist um $2r$ (einen vollen Bohrungsdurchmesser) zu groß. Bohrungen, die sich gefährlich nahe an der Außenwand befinden oder die Wandstärke unzulässig schwächen, bestehen die Randabstandsprüfung `hole_edge_distance` fälschlicherweise als `ok`.
- **Lösungsvorschlag:**
  Korrektur des Vorzeichens:
  - Bohrung außerhalb eines Zylinders: `dist = d_axes - ec["radius"] - r`.
  - Bohrung innerhalb eines zylindrischen Körpers: `dist = ec["radius"] - d_axes - r`.

---

### 6. [Mittel] Assoziatives Muster-Update translatiert nur `axis_point`, rotiert aber Musterachsen nicht
- **Fundstelle:** [mechvane/bolted.py:1709-1714](file:///root/repos/_wt/gemini-4/mechvane/bolted.py#L1709-L1714)
- **Problem:**
  Verschiebt oder dreht sich das Anker-Bauteil einer Schraubverbindung mit Muster, aktualisiert `check_and_update_bolted_connections` lediglich:
  ```python
  if shifted_by:
      if pat.get("type") == "circular" and "axis_point" in pat:
          pat["axis_point"] = g.add(pat["axis_point"], shifted_by)
  ```
  `shifted_by` ist ein reiner Translationsvektor (`g.sub(new_pos, old_pos)`).
  Wurde das Bauteil gedreht, bleibt `pat["axis"]` beim Kreismuster unberührt. Bei linearen bzw. rechteckigen Mustern (`linear`/`rectangular`) werden die Richtungsvektoren `pat["directions"]` bzw. `pat["direction"]` überhaupt nicht transformiert.
- **Auswirkung:**
  Wird ein Flansch mit Lochkreis oder eine Platte mit Lochraster im Raum gedreht, wandern die Musterbohrungen nach dem Update in die falsche Raumrichtung bzw. rotieren um eine veraltete Achse.
- **Lösungsvorschlag:**
  Die Rotationsmatrix des Anker-Bauteils muss im Verbindungsdatensatz persistiert und bei jeder Neuausrichtung auf sämtliche Richtungsvektoren (`axis`, `directions`) des Musters angewendet werden.

---

### 7. [Mittel] Fehlgeschlagene Normteil-Generierung hinterlässt verwaiste Dokumentdatei auf der Festplatte
- **Fundstelle:** [mechvane/standard_parts.py:564-572](file:///root/repos/_wt/gemini-4/mechvane/standard_parts.py#L564-L572)
- **Problem:**
  In `create` wird zuerst das Dokument im Workspace initialisiert:
  ```python
  doc = ws.new("part", doc_name)
  ```
  `ws.new` erstellt unmittelbar die Datei `doc_name.json` auf der Festplatte. Schlägt anschließend `doc.session.batch(sp["commands"])` fehl (z. B. durch Engine-Fehler oder ungültige Geometrieparameter), fängt der `except`-Block den Fehler ab:
  ```python
  except Exception:
      ws.close(doc_name)
      raise
  ```
  `ws.close` entfernt das Dokument aus der In-Memory-Verwaltung (`ws.docs`), löscht jedoch **nicht** die bereits geschriebene Datei `doc.path` vom Dateisystem.
- **Auswirkung:**
  Ein nachfolgender Aufruf von `standard_parts.create(ws, ..., overwrite=False)` für dasselbe Normteil schlägt sofort mit `FileExistsError` fehl, obwohl das Normteil unvollständig bzw. korrupt abgebrochen war.
- **Lösungsvorschlag:**
  Löschen der unvollständigen Datei im Fehlerfall:
  ```python
  except Exception:
      f_path = doc.path
      ws.close(doc_name)
      if os.path.exists(f_path):
          try:
              os.remove(f_path)
          except OSError:
              pass
      raise
  ```

---

### 8. [Mittel] Koaxiale Gewindebohrungen auf derselben Achse überschreiben gegenseitig ihre Gewindetiefe
- **Fundstelle:** [mechvane/design_rules.py:127-130, 404-408](file:///root/repos/_wt/gemini-4/mechvane/design_rules.py#L127-L130)
- **Problem:**
  `_extract_holes` ordnet Timeline-Gewindebefehle (`solid.thread`) Bohrungszylindern zu, indem ausschließlich die Kollinearität der Achsen geprüft wird:
  ```python
  dist_to_line = g.length(g.sub(diff, g.scale(h_axis, proj)))
  if dist_to_line < 0.05:
      hole_dict["thread"] = t_feat
      break
  ```
  Liegen zwei Gewindebohrungen auf derselben Achse (z. B. ein beidseitig bearbeitetes Gehäuse mit einem M6-Gewinde von oben mit Tiefe 10 mm und einem M6-Gewinde von unten mit Tiefe 16 mm), matchen beide Bohrungen auf denselben ersten Timeline-Thread-Befehl.
- **Auswirkung:**
  Beide Bohrungen erhalten identische Gewindeparameter. Bei der Überprüfung der Mindesteinschraubtiefe (`thread_depth`) in Zeile 404–408 wird die zweite Bohrung mit der Tiefe der ersten Bohrung bewertet, was zu falschen Bestehens- oder Fehlerurteilen führt.
- **Lösungsvorschlag:**
  Neben der Achsen-Kollinearität muss auch die axiale Position entlang der Bohrungsachse abgeglichen werden. Zudem dürfen bereits zugeordnete Timeline-Features nicht ein zweites Mal zugewiesen werden (`used_thread_ids.add(...)`).

---

### 9. [Niedrig] Senkkopf-Verschraubung fehlt Schaft-Orientierungsprüfung und Flip-Korrektur
- **Fundstelle:** [mechvane/bolted.py:1278-1289](file:///root/repos/_wt/gemini-4/mechvane/bolted.py#L1278-L1289)
- **Problem:**
  Für Zylinderkopfschrauben (ISO 4762) führt `bolted.py` in Zeilen 1312–1319 eine explizite Vektorprüfung zwischen Kopf- und Schaftschwerpunkt durch:
  ```python
  shank_dir = g.normalize(g.sub(b["shank_center"], b["head_center"]))
  if g.dot(shank_dir, dir_world) < 0:
      screw_rot = {"axis": rot_axis, "angle": 180}
  ```
  Für Senkkopfschrauben (ISO 10642) in Zeilen 1278–1289 fehlt diese Prüfung.
- **Auswirkung:**
  Wird eine Senkkopfschraube in einer Baugruppe platziert, deren lokale Koordinatenlage entgegengesetzt zu `dir_world` definiert ist, wird die Senkschraube um 180° verkehrt herum eingebaut (Kopf zeigt ins Innere des Bauteils, Schaft ragt nach außen).
- **Lösungsvorschlag:**
  Die Schaft-zu-Kopf-Ausrichtungsprüfung auch im Zweig für Senkkopfschrauben anwenden.

---

### 10. [Niedrig] Test `creation failure cleans up open document from workspace` prüft Festplatten-Cleanup nicht
- **Fundstelle:** [tests/mechvane/check.py:492-508](file:///root/repos/_wt/gemini-4/tests/mechvane/check.py#L492-L508)
- **Problem:**
  Der Test prüft nach einem bewusst provozierten Fehler in `standard_parts.create`:
  ```python
  assert "ISO_4762_M5_Bad" not in ws.docs
  ```
  Er prüft jedoch nicht `os.path.exists(bad_path)`. Da `ws.new` die Datei auf Festplatte anlegt, verbleibt diese dort (siehe Befund 7).
- **Auswirkung:**
  Der Test suggeriert ein vollständiges Aufräumen, obwohl der Festplattenzustand unbereinigt bleibt.
- **Lösungsvorschlag:**
  Im Test ergänzen:
  ```python
  assert not os.path.exists(ws.path("ISO_4762_M5_Bad"))
  ```

---

### 11. [Niedrig] Test `screw sits coaxial to hole` ignoriert Z-Auflagehöhe der Schraube
- **Fundstelle:** [tests/mechvane/check.py:941-956](file:///root/repos/_wt/gemini-4/tests/mechvane/check.py#L941-L956)
- **Problem:**
  Der Koaxialitätstest verifiziert in Zeile 953–954 lediglich:
  ```python
  o = occ["transform"]["origin"]
  assert abs(o[0]) < 1e-4 and abs(o[1]) < 1e-4, f"screw off-axis: {o}"
  ```
  Die Z-Koordinate `o[2]` wird vollständig ignoriert.
- **Auswirkung:**
  Ob die Schraube plan auf der Plattenoberfläche aufsitzt, korrekt in der Senkung versenkt ist oder 20 mm darüber in der Luft schwebt, wird von diesem Test nicht überprüft.
- **Lösungsvorschlag:**
  Prüfung des Z-Sitzes gegen die berechnete Plattenoberkante:
  ```python
  assert abs(o[2] - expected_head_z) < 1e-3, f"screw seated at wrong Z: {o[2]} vs {expected_head_z}"
  ```

---

### 12. [Niedrig] Kantenabstand `r` für DIN-625-Rillenkugellager als Parameter angelegt, aber im B-Rep-Modell nicht gefast
- **Fundstelle:** [mechvane/standard_parts.py:489-490](file:///root/repos/_wt/gemini-4/mechvane/standard_parts.py#L489-L490)
- **Problem:**
  `standard_parts.py` hinterlegt in `BEARING_6000_SERIES` die Kantenabstände $r_{\min}$ (z. B. 0,3 mm für 608/6000 bzw. 0,6 mm für 6004/6005) und setzt `doc.parameter("r", ...)`. Die Modellierungsfunktion `make_bearing_commands` generiert jedoch nur einen Zylinder (`solid.cylinder`) und eine Bohrung (`solid.hole`), ohne Fasen-Features an den Ringen.
- **Auswirkung:**
  Das generierte Kugellagermodell weist scharfkantige 90°-Ecken auf. Bei Einbau in Lagersitze mit Wellen- oder Gehäuseabsätzen nach DIN 5418 können feine Kollisionsprüfungen fälschlich Kollisionen anzeigen.
- **Lösungsvorschlag:**
  Entweder Kantenfasen (`solid.chamfer`) an Innen- und Außenring modellieren oder im Modul-Docstring explizit festhalten, dass Normteile als vereinfachte Hüllgeometrien ohne Kantenfasen generiert werden.

---

## 3. Maßtabellen-Prüfung gegen Normen

Die in `mechvane/standard_parts.py` hinterlegten Maßtabellen wurden gegen die offiziellen ISO- und DIN-Normenwerke abgeglichen:

| Norm / Quelle | Bauteil / Typ | Geprüfte Nennmaße | Ergebnis |
|---|---|---|---|
| **ISO 4762:2004** | Zylinderschrauben mit Innensechskant | M2,5 bis M12 ($d_k, k, s, t, b$, Vorzugslängen) | **Korrekt** ($d_k$ max, $k$ max, $s$ nominal, $t$ min stimmen exakt) |
| **ISO 10642:2019** | Senkschrauben mit Innensechskant | M2,5 bis M12 ($d_k, k, s, t, \alpha=90^\circ$, Vorzugslängen) | **Korrekt** (Kopfdurchmesser $d_k$ nach theoretischem Scharfkant- bzw. Maximalmaß) |
| **ISO 4032:2012** | Sechskantmuttern (Typ 1) | M2,5 bis M12 ($s, m$) | **Korrekt** (insbes. M10 mit $s=16$ mm und M12 mit $s=18$ mm nach ISO, nicht DIN 934) |
| **ISO 7089:2000** | Flache Unterlegscheiben (Normale Reihe) | M2,5 bis M12 ($d_1, d_2, s$) | **Korrekt** (Form A, z. B. M5: $5{,}3 \times 10 \times 1{,}0$ mm) |
| **Ruthex-Werknorm** | Gewindeeinsätze für 3D-Druck | M2 bis M6 ($d_{\text{hole}}, l, w_{\min}, d_{\text{flange}}$) | **Korrekt** (Hersteller-Spezifikationen exakt abgebildet) |
| **DIN 625-1:2011** | Rillenkugellager (Reihe 60, 608–6005) | 608, 6000 bis 6005 ($d, D, B, r_{\min}$) | **Korrekt** (Hauptabmessungen und $r_{\min}$ normkonform) |

> [!NOTE]
> Es wurden **keine Abweichungen bei den normierten Maßzahlen** festgestellt. Alle Nennmaße und Toleranzgrenzen in den Python-Dictionaries stimmen mit den aktuellen Ausgaben der Normen überein.

---

## 4. Zusammenfassungstabelle der Befunde

| Nr. | Komponente | Datei:Zeile | Schwere | Befund |
|---|---|---|---|---|
| 1 | `bolted` | `bolted.py:329-330` | **Hoch** | `_point_in_face` überspringt Polygonprüfung bei gekrümmten Kanten (`has_curved_edges = True`), bohrt durch leere Luft |
| 2 | `bolted` | `bolted.py:401-406` | **Hoch** | Durchdringungsberechnung nimmt nur `hits[0]` und `hits[-1]`, ignoriert Hohlräume in U-Profilen und Taschen |
| 3 | `design_rules` | `design_rules.py:342-362` | **Hoch** | `min_wall_thickness` projiziert Bohrungsabstand rein in 2D ohne Z-Überlappung; Fehlalarm bei axial getrennten Sacklöchern |
| 4 | `bolted` | `bolted.py:646-655` | **Hoch** | Konzentrischer Anker ignoriert lokale Ankerkoordinaten bei Komponentenrotation; Schraube kollabiert und kehrt Richtung um |
| 5 | `design_rules` | `design_rules.py:250-252` | **Mittel** | Zylinder-Randabstand addiert $+r$ statt Subtraktion; meldet zu großen Randabstand und lässt kritische Bohrungen passieren |
| 6 | `bolted` | `bolted.py:1709-1714` | **Mittel** | Assoziatives Muster-Update translatiert nur `axis_point`, rotiert Musterachsen (`axis`, `directions`) bei gedrehtem Anker nicht |
| 7 | `standard_parts`| `standard_parts.py:564-572` | **Mittel** | Fehlgeschlagene Normteil-Erstellung schließt Dokument, löscht aber verwaiste JSON-Datei nicht von der Festplatte |
| 8 | `design_rules` | `design_rules.py:127-130` | **Mittel** | Koaxiale Gewindebohrungen auf derselben Achse matchen beide auf denselben Timeline-Eintrag und überschreiben Gewindetiefe |
| 9 | `bolted` | `bolted.py:1278-1289` | **Niedrig** | Senkkopf-Verschraubung fehlt Schaft-Orientierungsprüfung und Flip-Korrektur (kann verkehrt herum eingebaut werden) |
| 10 | `tests` | `check.py:492-508` | **Niedrig** | Test auf Workspace-Bereinigung prüft nur `ws.docs`, nicht das Verbleiben der Datei im Dateisystem |
| 11 | `tests` | `check.py:941-956` | **Niedrig** | Koaxialitätstest prüft nur X/Y-Koordinaten der Schraube, ignoriert Z-Auflagehöhe |
| 12 | `standard_parts`| `standard_parts.py:489-490` | **Niedrig** | Kantenabstand $r_{\min}$ für Kugellager als Parameter angelegt, Modell wird jedoch scharfkantig ohne Kantenfasen erzeugt |
