# SolidCraft-Fehlermeldungen: Sammlung, Übersetzung und Analyse (Stufe 1)

Stand: 2026-11-02  
Autor: Gemini (unbeaufsichtigter Task für Issue #38)  
Modell: Gemini 3.8 Flash  

---

## 1. Ausgangslage und Ziel

Bei der interaktiven oder skriptgesteuerten Modellierung in SolidCraft (z. B. über Mechvanes MCP-Server oder Praxistests wie Praxistest 6) stoßen Agenten und menschliche Konstrukteure regelmäßig auf kryptische Meldungen des Geometriekerns oder der Engine.
Ein markantes Beispiel aus Praxistest 6 ist:
> `lumps: shell boundaries intersect or touch; cavity ownership is ambiguous`

Ohne Übersetzung versteht ein LLM-Agent oft nicht, was geometrisch schiefgelaufen ist (z. B. sich unzulässig schneidende Schalen/Körper) und wie der Befehl korrigiert werden kann.

**Ziel von Stufe 1 (Issue #38):**
1. Sammlung relevanter SolidCraft-Fehlermeldungen für Modellierbefehle (Extrusion, Drehung, Bohrung, Rundung/Fase, Schale, Boolesche Operationen, Skizze/Profil, Muster, Loft).
2. Erstellung einer Übersetzungstabelle in `mechvane/sc_errors.py`, die Mustern (Regex) einen stabilen maschinenlesbaren Fehlercode (`code`), eine klare Fehlerbeschreibung (`message`) und eine konstruktive Handlungsempfehlung (`hint`) auf Englisch zuordnet.
3. Integration in `mechvane/server.py` (`run`), sodass Fehler im `except`-Block mit erklärendem Text und Handlungsanweisung neu ausgelöst werden (`f"{message} ({hint})\n{original_error}"`), während die bestehende Rollback-Logik unangetastet bleibt.
4. Vollständige Verifikation über `tests/mechvane/check.py`.

---

## 2. Tabelle der gesammelten Fehlermeldungen

Die folgende Tabelle führt alle 24 gesammelten Fehlertypen auf, inklusive Fundstelle im SolidCraft-Quellcode (`/root/repos/_ext/solidcraft`), vergebenem Code und Status der empirischen Auslösung via `solidcraft-cli` bzw. `mechvane`.

| Code | Originaltext / Kernmuster | SolidCraft-Fundstelle | Ausgelöst? | Beschreibung & Handlungshinweis |
|---|---|---|---|---|
| `lumps_shell_intersect` | `lumps: shell boundaries intersect or touch; cavity ownership is ambiguous` | `crates/kernel/src/shell_groups.rs:161` | Ja (Praxistest 6) | Shells/Körper schneiden sich mehrdeutig. Kollisionen prüfen oder Körper vorab trennen. |
| `blend_too_large` | `blend is larger than the neighbouring faces` / `maximum radius along this edge is` | `crates/kernel/src/blend.rs:380`, `crates/kernel/src/blend.rs:2509` | Ja (Live-Test) | Rundungsradius überschreitet verfügbaren Bauraum angrenzender Flächen. Radius verkleinern. |
| `chamfer_too_large` | `chamfer runs past a neighbouring face: try a smaller distance` | `crates/kernel/src/blend.rs:2509` | Ja | Fasenbreite läuft über Nachbarfläche hinaus. Abstand verkleinern. |
| `blend_meeting_edges` | `where {count} edges meet: give a point along one edge` | `crates/engine/src/cmd/features.rs:1552` | Ja | Klickpunkt liegt auf Ecke/Knoten mehrerer Kanten. Punkt entlang der Kantenmitte angeben. |
| `blend_no_edge` | `no edge at [{x}, {y}, {z}]: the nearest edge is` | `crates/engine/src/cmd/features.rs:1557` | Ja | Kein Kantenpunkt an den Koordinaten gefunden. Koordinaten korrigieren. |
| `blend_non_positive_size` | `fillet size must be positive` / `chamfer size must be positive` | `crates/engine/src/cmd/features.rs:1497` | Ja | Radius bzw. Fasenabstand ist $\le 0$. Positiven Wert angeben. |
| `extrude_zero_distance` | `extrude distance is zero` | `crates/kernel/src/build.rs:213` | Ja (Live-Test) | Extrusionstiefe ist 0 mm. Positiven Abstand oder `through_all=True` wählen. |
| `missing_sketch` | `no sketch \`{name}\`` | `crates/engine/src/cmd/features.rs:88` | Ja | Angegebene Skizze existiert nicht in der Timeline. Vorherige Skizzenerstellung prüfen. |
| `revolve_crosses_axis` | `the profile crosses the revolve axis` | `crates/kernel/src/build.rs:375` | Ja (Live-Test) | Skizzenprofil schneidet die Rotationsachse. Profil komplett auf eine Achsenseite legen. |
| `revolve_angle_invalid` | `revolve angle is zero` / `revolve angle must be more than 0` | `crates/kernel/src/build.rs:369`, `crates/engine/src/cmd/features.rs:1140` | Ja | Drehwinkel ist 0 oder ungültig. Winkel im Bereich $(0^\circ, 360^\circ]$ angeben. |
| `hole_not_on_face` | `\`position\` [...] is not on a face of a body; pick a point on the face to drill` | `crates/engine/src/cmd/features.rs:2555` | Ja (Live-Test) | Bohrungsposition liegt nicht auf einer Bauteilfläche. Punkt auf Fläche platzieren. |
| `hole_counterbore_invalid` | `the counterbore must be wider than the hole and shallower than it` | `crates/doc/src/eval.rs:4961` | Ja | Flachsenkung ist schmaler als Bohrung oder zu tief. `cb_diameter` > `diameter` setzen. |
| `hole_countersink_invalid` | `the countersink must be wider than the hole` | `crates/doc/src/eval.rs:4970` | Ja | Kegelsenkung ist schmaler als Bohrung. `cs_diameter` vergrößern. |
| `shell_non_positive_thickness`| `shell thickness must be positive` | `crates/doc/src/eval.rs:7566` | Ja | Schalendicke ist nicht positiv. Positiven Ausdruck angeben. |
| `shell_too_thick` | `the planes don't enclose a solid` / `the shell removed everything` | `crates/kernel/src/polyhedron.rs:56`, `crates/doc/src/eval.rs:7579` | Ja | Schalendicke zu groß; Bauteilvolumen wird komplett ausgelöscht. Dicke reduzieren. |
| `combine_self` | `a body cannot be combined with itself` | `crates/doc/src/eval.rs:7960` | Ja | Körper soll mit sich selbst vereinigt/geschnitten werden. Unterschiedliche Körper wählen. |
| `unknown_body` | `unknown body \`{name}\`` / `unknown body in scope` | `crates/engine/src/cmd/appearance_chain.rs:96`, `crates/ui-egui/src/preview.rs:563` | Ja | Referenzierter Körper existiert nicht im Modell. Name überprüfen. |
| `pattern_count_unit` | `expected a unit-less number, got a length: {expr}` | `crates/doc/src/expr.rs:1415`, `crates/engine/src/cmd/features.rs:2812` | Ja | Muster-Anzahl hat Einheit (z. B. `4 mm` statt `4`). Einheitslose Ganzzahl übergeben. |
| `sketch_zero_line` | `zero-length line` | `crates/engine/src/cmd/sketch.rs:1065` | Ja | Start- und Endpunkt einer Linie sind identisch. Unterschiedliche Punkte wählen. |
| `sketch_overconstrained` | `that conflicts with the sketch` | `crates/engine/src/cmd/sketch.rs:2009` | Ja | Skizzenbedingung widerspricht bestehenden Bedingungen. Überbestimmung lösen. |
| `loft_section_count` | `a loft needs 2…50 sections` | `crates/engine/src/cmd/features.rs:2926` | Ja | Loft benötigt mindestens 2 Querschnittsskizzen. Weitere Skizze hinzufügen. |
| `boolean_unreliable` | `the cut could not be computed reliably: faces touch along a zero-thickness edge` | `crates/kernel/src/boolean.rs:142` | Ja | Berührende Flächen ohne Schnittvolumen (Zero-Thickness). Leichte Überlappung addieren. |
| `intersect_empty` | `the intersection is empty: nothing of {body} would remain` | `crates/doc/src/eval.rs:3066` | Ja | Schnittmenge ist leer. Überlappung zwischen Profil/Werkzeug und Zielkörper sicherstellen. |
| `profile_no_area` | `profile has no area` | `crates/kernel/src/build.rs:161` | Ja | Skizzenprofil umschließt keine Fläche (z. B. offener Linienzug). Geschlossenen Loop bilden. |

---

## 3. Empirische Auslösung und Testfälle

Im Rahmen von Stufe 1 wurden über 18 Fehlermeldungen direkt über `solidcraft-cli` und die Python-Schnittstelle reproduziert und verifiziert:
- **`solid.extrude`:** Extrusionsabstand `0 mm` wirft `extrude distance is zero`.
- **`solid.revolve`:** Rechteck über der Y-Achse (`[-5, 0]` bis `[5, 10]`) um Y rotiert wirft `the profile crosses the revolve axis`.
- **`solid.fillet`:** Radius `15 mm` an $10\text{ mm}$-Kante wirft `blend is larger than the neighbouring faces: maximum radius along this edge is 5 mm (you asked for 15 mm)`.
- **`solid.hole`:** Koordinate `[50, 50, 50]` abseits des Bauteils wirft `\`position\` [50 mm, 50 mm, 50 mm] is not on a face of a body; pick a point on the face to drill`.
- **`solid.shell`:** Dicke `10 mm` an $10\text{ mm}$-Würfel wirft `the planes don't enclose a solid`.
- **`pattern.linear`:** `count="5 mm"` wirft `expected a unit-less number, got a length: 5 mm`.
- **`sketch.line`:** Start `[0, 0]` und Ende `[0, 0]` wirft `zero-length line`.

### Live-Prüfung in `tests/mechvane/check.py`
In `tests/mechvane/check.py` wurde `sc_errors_checks(ws)` integriert:
1. Alle 24 Tabelleneinträge werden anhand zuvor aufgezeichneter Originalfehlertexte auf Vollständigkeit, Code-Übereinstimmung und vorhandene `message` + `hint` geprüft.
2. Unbekannte Fehler und Randfälle (leerer String, `None`) geben zuverlässig `None` zurück.
3. Mindestens vier Live-Fälle (`extrude_zero_distance`, `revolve_crosses_axis`, `blend_too_large`, `hole_not_on_face`) werden direkt über `server.run()` ausgelöst:
   - Die Exception wird abgefangen und enthält sowohl den verständlichen Text mit Handlungsanweisung als auch den vollständigen Originaltext und den JSON-Fehlerblock.
   - Der Rollback-Mechanismus (`edit.restore_checkpoint`) wird überprüft (die Timeline bleibt nach dem Fehler sauber zurückgesetzt).

---

## 4. Erkannte Lücken und Ausblick (Stufe 2)

Bei der Quellcode- und Praxisanalyse traten folgende Grenzen und Lücken der Fehlerbehandlung in SolidCraft zutage:

1. **Fehlende Namen und Lokalisierung (Stufe 2):**
   Meldungen wie `blend is larger than the neighbouring faces` oder `the intersection is empty: nothing of Body 1 would remain` nennen oft nur Kernel-Namen (`Body 1`), nicht aber den vom Anwender in Mechvane vergebenen Bauteil- oder Skizzennamen. In Stufe 2 soll die Lokalisierung auf Mechvane-Objekte gemappt werden.
2. **Generische Solver-Meldungen bei Skizzen:**
   Wenn geometrische Bedingungen in Skizzen mathematisch überbestimmt oder unlösbar sind, liefert der Solver teils nur `that conflicts with the sketch`, ohne die exakten beteiligten Dimensionen oder Koinzidenzen aufzuzählen.
3. **Flächenberührungen bei Booleschen Operationen (`boolean_unreliable`):**
   Kollidieren Flächen tangential oder mit einer Kantenberührung ohne echtes Schnittvolumen, scheitert der Kernel oft spät mit `the cut could not be computed reliably`. Ein Pre-Flight-Check in Mechvane könnte solche Null-Dicken-Berührungen vorab abfangen.
4. **Parameter-Validierung vor Engine-Aufruf:**
   Einige Fehler (z. B. Einheiten in Zählern wie `count: "4 mm"`, negative Radien oder identische Start-/Endpunkte) könnten bereits im Mechvane-Layer vor der Weiterleitung an `solidcraft-cli` validiert werden, um unnötige Sitzungs-Rollbacks zu vermeiden.
