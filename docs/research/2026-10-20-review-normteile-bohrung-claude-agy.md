> Review durch Claude Opus 5.5 über agy (nur lesend) von standard_parts.py, hole_tables.py, bolted.py, 13 Befunde, nicht nachgestellt. Maßtabellen aus Modellwissen ohne Primärquelle geprüft: nur Hypothese im Sinne des Wissenskatalogs. Das zweite Review (links.py, inplace.py, tree.py) brach ab: 5-Stunden-Fenster von Claude über agy nach einem Review leer.

root agent idle; waiting up to 25m0s for 2 background task(s)
I'm waiting for the probe run to finish.
# Code-Review: standard_parts / hole_tables / bolted

Ich habe nichts geändert. Die Testsuite läuft grün (0 failures). Die meisten Befunde unten habe ich in einem temporären Arbeitsverzeichnis nachgestellt, mit [probe.py](file:///root/.gemini/antigravity-cli/brain/81e859b0-64f6-4b25-831e-25aae36a34b8/scratch/probe.py). Was dort „belegt“ heißt, ist die tatsächliche Ausgabe. Befund 9 habe ich nur aus dem Code nachgerechnet, nicht laufen lassen.

## Hoch

**1. Zu kurze Schraube ohne Fehler** – [hole_tables.py:145-148](file:///root/repos/mechvane/inventa/hole_tables.py#L145-L148)
Ist keine Länge ≥ der benötigten Länge vorhanden, liefert die Funktion stillschweigend die längste.
Test: `preferred_screw_length("M5", 80)` → `50.0` (belegt). Bei Schraubenpaketen über ca. 40 mm (M5) baut [bolted.py:230](file:///root/repos/mechvane/inventa/bolted.py#L230) also eine Schraube ein, die die Mutter nicht erreicht.

**2. `length_override` wird nie geprüft** – [bolted.py:197](file:///root/repos/mechvane/inventa/bolted.py#L197), [:211](file:///root/repos/mechvane/inventa/bolted.py#L211), [:230](file:///root/repos/mechvane/inventa/bolted.py#L230)
Test: Platten 10 + 8 mm, M5, `fasteners={"length_override": 12}` → `selected_screw_length 12`, `required_length 24.9`, kein Fehler (belegt).
Beim Sackloch kommt dazu [Zeile 198](file:///root/repos/mechvane/inventa/bolted.py#L198): `max(min_eng, …)` meldet die Mindest-Einschraubtiefe, obwohl die Schraube kürzer greift.

**3. Doppelte Joint-Namen bei mehreren Verbindungen** – [bolted.py:413](file:///root/repos/mechvane/inventa/bolted.py#L413) zusammen mit [links.py:133](file:///root/repos/mechvane/inventa/links.py#L133)
Das Präfix ist fest `"Bolted"`, und SolidCraft prüft Joint-Namen nicht auf Eindeutigkeit (`joints.rs:644`). `links.record` speichert die Joints in einem Dict nach Namen, die zweite Verbindung überschreibt also die erste.
Test: zweimal `bolted_connection` ohne `name` in derselben Baugruppe. Ergebnis (belegt):
- `joint.list` hat 6 Joints.
- In den Metadaten stehen nur 3.
- `links.check` meldet alles „ok“, die erste Verbindung wird aber gar nicht mehr geprüft.
- Die Hole-Features heißen doppelt `['Hole_M5', 'Hole_M5']`.

**4. Strahl wird als unendliche Gerade behandelt** – [bolted.py:110-122](file:///root/repos/mechvane/inventa/bolted.py#L110-L122)
Es gibt keinen Filter `s_val ≥ 0`. Teile oberhalb des Startpunkts werden mitgebohrt, und das oberste davon bekommt Kopf und Senkung.
Test: Deckel (z 10…15) über Top (0…10) und Bot, Start bei [0,0,10] nach unten → `parts ['Cover:1','Top:1','Bot:1']`, Paket 23 statt 18 (belegt).
Bei der `concentric`-Platzierung ist das Achsvorzeichen der Bohrung zufällig. Damit dreht sich dort die Reihenfolge der Platten, also Kopf- und Mutterseite.

**5. Bauteildicke aus Ebenen statt aus echten Flächen** – [bolted.py:100-119](file:///root/repos/mechvane/inventa/bolted.py#L100-L119)
Der Schnittpunkt wird nur gegen die Bounding-Box geprüft, nicht gegen die Fläche selbst. So zählt z. B. die Deckfläche eines Absatzes, der gar nicht auf dem Strahl liegt.
Test: Platte 40×40×10 mit Absatz 10×10×10 in einer Ecke, Bohrung in der Mitte → `Top thickness 20.0` statt 10, Schraube 35 statt 25 (belegt).
Zusätzlich nimmt [Zeile 97](file:///root/repos/mechvane/inventa/bolted.py#L97) nur die Bounding-Box des ersten Körpers, die Flächen aber von allen Körpern.

**6. Kernloch weicht von DIN 336 ab (M8, M12)** – [bolted.py:363-371](file:///root/repos/mechvane/inventa/bolted.py#L363-L371)
Übergeben wird nur `"thread"`, keine `"diameter"`. SolidCraft rechnet dann Nenndurchmesser minus Steigung (`features.rs:1756-1758`), also M8 → 6,75 und M12 → 10,25. Die Vorschau meldet dagegen den DIN-336-Wert 6,8 bzw. 10,2.
Test: Sackloch M8 → gemeldet `tap_drill 6.8`, gebohrt Radius `3.375` (belegt).
Ursache: Dieselbe Kernlochtabelle gibt es dreimal (`hole_tables.DIN_336`, `design_rules.ISO_METRIC_THREADS`, SolidCraft).

**7. Bohrspitze bricht durch** – [bolted.py:202](file:///root/repos/mechvane/inventa/bolted.py#L202)
Geprüft wird nur `drill_depth` gegen die Plattendicke. In SolidCraft ist `depth` aber die zylindrische Tiefe, die Spitze kommt noch dazu (`eval.rs:3049-3053`). `total_depth` wird zwar in [hole_tables.py:262](file:///root/repos/mechvane/inventa/hole_tables.py#L262) berechnet, aber nirgends verwendet.
Test: M5 in Alu, Grundplatte 14 mm → Prüfung bestanden (13,2 ≤ 14), die Spitze reicht aber bis 13,2 + 1,262 = 14,46 mm.

**8. Gleiche Teildatei zweimal im Paket** – [bolted.py:346-400](file:///root/repos/mechvane/inventa/bolted.py#L346-L400)
Die Bohrungen landen beide in derselben Datei, also bekommen beide Vorkommen die Senkung.
Test: `sf_plate` zweimal gestapelt, `counterbore=True` → Radien `[2.75, 2.75, 5.0, 5.0]` (belegt).
Außerdem gibt es keinen Rollback: Jede Teildatei wird gespeichert, bevor die nächste gebohrt ist. `standard_parts.create` räumt dagegen bei Fehlern auf.

## Mittel

9. **Einsatz: Schraubenspitze hinter dem Aufnahmeloch** – [bolted.py:210-211](file:///root/repos/mechvane/inventa/bolted.py#L210-L211). Es fehlt die Prüfung `screw_length − grip ≤ min_depth`. Test (aus dem Code nachgerechnet, nicht laufen lassen): M4-Einsatz, Deckel 17,35 mm mit Senkung → Klemmlänge 12,95, benötigt 20,05, gewählt 25. Die Spitze sitzt 12,05 mm tief, das Loch ist nur 9,1 mm tief.

10. **Passung (`fit`) verhält sich anders als in SolidCraft** – [hole_tables.py:92-102](file:///root/repos/mechvane/inventa/hole_tables.py#L92-L102), [:124](file:///root/repos/mechvane/inventa/hole_tables.py#L124). Unbekannte Werte fallen stillschweigend auf „medium“ zurück, und `f/m/c` kennt SolidCraft nicht.
   - `clearance_hole("M5","xyz")` → 5,5 statt eines Fehlers (belegt).
   - `fit="f"`: Die Vorschau meldet 5,3, `bolted_connection` bricht dann mit `SolidCraftError` ab (belegt).

11. **Senkung tiefer als die obere Platte** – [bolted.py:182-188](file:///root/repos/mechvane/inventa/bolted.py#L182-L188). Das wird nicht geprüft. Test: Deckplatte 4 mm, M5 mit Senkung → Vorschau meldet Klemmlänge 6,6 ohne Fehler (belegt). Die Ausführung scheitert erst in SolidCraft (`eval.rs:3066`).

12. **`_parse_placement` mit `concentric`** – [bolted.py:61-69](file:///root/repos/mechvane/inventa/bolted.py#L61-L69).
   - `cyls[0]` nimmt irgendeine Zylinderfläche. Bei einem runden Teil kann das die Außenfläche sein.
   - Zeile 61 enthält toten Code (`doc.session if False else …`) und baut einen neuen `Workspace`, statt `ws.reader` zu verwenden.
   - [Zeile 34](file:///root/repos/mechvane/inventa/bolted.py#L34): Steht ein Schlüssel `position` in der Platzierung, wird `type` ignoriert.
   - Nichts davon ist getestet.

13. **Vorhandene Normteil-Datei wird ungeprüft wiederverwendet** – [bolted.py:24-26](file:///root/repos/mechvane/inventa/bolted.py#L24-L26). Liegt eine alte Datei mit anderen Maßen auf der Platte, wird sie trotzdem eingebaut.

## Tests, die sich selbst bestätigen oder Lücken haben

- **Bohrtiefe = Eingabewert:** [check.py:847-851](file:///root/repos/mechvane/tests/inventa/check.py#L847-L851) und [:933-937](file:///root/repos/mechvane/tests/inventa/check.py#L933-L937) lesen über `timeline.inspect` die Tiefe zurück, die inventa selbst übergeben hat. Die Geometrie wird nicht gemessen. Befund 7 kann so nicht auffallen.
- **„118° Bohrspitze“:** [check.py:840-844](file:///root/repos/mechvane/tests/inventa/check.py#L840-L844) prüft nur, ob eine Fläche `:bore:side:2#` heißt. Der Winkel wird gar nicht geprüft.
- **„koaxial“:** [check.py:723-725](file:///root/repos/mechvane/tests/inventa/check.py#L723-L725) (und die Gegenstücke) vergleichen `frame_a` mit `frame_b` eines starren Joints. Ist der Joint gelöst, sind die beiden Frames per Definition gleich. Die tatsächliche Lage der Schraube (Transformation oder Bounding-Box) wird nicht geprüft, Unterlegscheibe und Mutter gar nicht.
- **„ohne offenes Dokument“:** [check.py:424-440](file:///root/repos/mechvane/tests/inventa/check.py#L424-L440) verspricht das im Kommentar, prüft es aber nicht. Alle Fehlaufrufe scheitern schon in `spec()`, bevor `ws.new` läuft. Der Aufräumpfad in [standard_parts.py:423-425](file:///root/repos/mechvane/inventa/standard_parts.py#L423-L425) wird also nie durchlaufen.
- **Ungetestete Fälle:**
  - `washer_head` und damit die gesamte `with_washer`-Tabelle und [bolted.py:446-468](file:///root/repos/mechvane/inventa/bolted.py#L446-L468)
  - Richtungen außer −Z
  - `concentric`-Platzierung
  - M8/M12 (das hätte Befund 6 gezeigt)
  - mehrere Verbindungen in einer Baugruppe (Befund 3)
  - Kollisionsprüfung beim Einsatz-Fall

## Stil

- `bolted.py` greift 14-mal auf private Funktionen aus `links` zu (`links._occurrences`, `_links`, `_part_faces`, `_unique_comp_name`) und auf `ws._path`. Das macht sonst kein anderes Modul.
- `conn_record` und `ret` sind fast identisch dupliziert ([bolted.py:564-611](file:///root/repos/mechvane/inventa/bolted.py#L564-L611)).
- [check.py:955-956](file:///root/repos/mechvane/tests/inventa/check.py#L955-L956): Vor `def semantic_queries` fehlen die zwei Leerzeilen.
- `standard_parts_checks` ruft am Ende kein `ws.close_all()` auf, anders als die übrigen Prüfungen.
- Der Parameter `b` ([standard_parts.py:261-262](file:///root/repos/mechvane/inventa/standard_parts.py#L261-L262)) wird von der Gewindedarstellung nicht genutzt. Das Gewinde läuft über den ganzen Schaft.
  - `min(l, 2d+12)` stimmt für kurze Schrauben nicht: Nach ISO 4762 haben die kurzen Längen Gewinde bis zum Kopf. Wo die Grenze genau liegt, weiß ich nicht sicher.
- `preferred_lengths` ist eigentlich der handelsübliche Längenbereich aus ISO 4762, keine Vorzugsreihe.

## Maßtabellen

Gegen die Normen geprüft habe ich, aus meinem Normwissen ohne Primärquelle. Dabei habe ich **keine abweichenden Werte** gefunden:

| Tabelle | Geprüfte Werte | Ergebnis |
|---|---|---|
| ISO 4762 | dk, k, s, t, b, Längenbereiche M2,5–M12 | stimmt |
| ISO 4032 | s, m (auch M10 = 16 und M12 = 18 nach ISO, nicht DIN 934) | stimmt |
| ISO 7089 | d1, d2, h | stimmt |
| ISO 273 | fein / mittel / grob | stimmt |
| DIN 625 | 6000–6005 | stimmt |
| DIN 336 | Kernlöcher | stimmt |

## DIN 974-1

**Ohne Scheibe (Reihe 1):** Die Werte im Code halte ich für richtig.
- Senkdurchmesser d1 = 5,5 / 6,5 / 8 / 10 / 11 / 15 / 18 / 20
- Senktiefe t = k + Z mit Z = 0,4 mm bis M6 und 0,6 mm ab M8, also 2,9 / 3,4 / 4,4 / 5,4 / 6,4 / 8,6 / 10,6 / 12,6
- Sicherheit: hoch für M3–M12, mittel für M2,5.

**Mit Scheibe ISO 7089:** Hier sind die Werte im Code keine DIN-Werte.
- **Durchmesser:** Die 11,5 / 13,5 / 17,5 / 21,5 / 25,5 mm sind offenbar errechnet (Scheibe + 1,5 mm). DIN 974-1 sieht für Scheiben nach ISO 7089/7090 meiner Erinnerung nach Reihe 5 vor. Ich halte diese Werte für richtig:
  - M3 9, M4 10, M5 13, M6 15 – Sicherheit mittel
  - M8 18, M10 24, M12 26 – Sicherheit gering
  - Zwei Sekundärquellen widersprechen sich (eine nennt für M5/M6/M8 die Werte 11/13/18), und eine Primärquelle hatte ich nicht.
- **Tiefen:** Sie folgen nicht der Formel im eigenen Kommentar ([hole_tables.py:56](file:///root/repos/mechvane/inventa/hole_tables.py#L56)).
  - Mit t = k + h + Z und dem Nennmaß h ergibt sich: M2,5 3,4 · M3 3,9 · M4 5,2 · M5 6,4 · M6 8,0 · M8 10,2 · M10 12,6 · M12 15,1.
  - Der Code liegt 0,1–0,2 mm darüber. Teils passt das zu h_max, teils nicht, es ist also uneinheitlich.
  - Die Formel halte ich für richtig (Sicherheit mittel bis hoch), den genauen Wert von Z nur mit mittlerer Sicherheit.

Die Ausgabe im Kommentar ist veraltet: Statt „1999-04“ gilt meines Wissens die Ausgabe 2008-02, in der Reihe 3 entfallen ist.
