### Kurzer Bericht zu den behobenen Befunden

Alle vier angegebenen Befunde aus `docs/research/2026-10-20-review-regeln-abfragen-argon.md` wurden behoben. Für jeden Befund wurde zunächst eine Prüfung in `tests/inventa/check.py` ergänzt, die vor dem Fix fehlschlug.

#### 1. Was geändert wurde

* **Befund 1** ([`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py#L133-L141), [`inventa/query.py`](file:///root/repos/mechvane-argonfix/inventa/query.py#L458-L466)):
  * Die Operation wird nun korrekt aus `feat_info.get("definition", {}).get("operation") or feat_info.get("operation")` ausgelesen (wie von `timeline.inspect` geliefert).
  * Features mit `operation in ("join", "new_body", "new")` (aufgesetzte Zapfen, Zylinder, Dome) werden explizit ausgeschlossen (`is_hole = False`) und fallen nicht mehr in die Bounding-Box-Innenheuristik.
  * Neuer Test: `ok("design rules and query: attached pin with join is not treated as hole", ...)` in [`tests/inventa/check.py`](file:///root/repos/mechvane-argonfix/tests/inventa/check.py#L667-L679).

* **Befund 4** ([`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py#L64-L84), [`inventa/query.py`](file:///root/repos/mechvane-argonfix/inventa/query.py#L35-L55)):
  * `float(feat_defn["depth"])` bzw. `["height"]` wurde durch die Hilfsfunktion `_eval_length(session, val, default)` ersetzt: Ausdrücke mit Einheiten (`"10 mm"`) oder Parameternamen werden sicher ausgewertet (inklusive Fallback auf `expr.evaluate` bei Parametern).
  * Die tatsächliche Sacklochtiefe wird durch `min(depth_val, h["length"])` auf die reale Zylinderlänge im Bauteil gedeckelt („Sacklochtiefe nie größer als tatsächliche Zylinderlänge“).
  * Eine Durchgangsbohrung, deren definierte Tiefe größer als die Plattendicke ist, wird nur als Sackloch markiert, wenn tatsächlich Abschlussflächen vorhanden sind (`end_caps`).
  * Neuer Test: `ok("design rules and query: expression depth is evaluated and pierced hole is through hole", ...)` in [`tests/inventa/check.py`](file:///root/repos/mechvane-argonfix/tests/inventa/check.py#L681-L700).

* **Befund 5** ([`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py#L370-L388)):
  * Da `max_overhang_angle` als Winkel von der Vertikalen definiert ist, gilt $n_z = -\sin(\alpha)$. Die Schranke wurde von `cos_limit` auf `sin_limit = math.sin(math.radians(max_oh))` und `n[2] < -sin_limit` korrigiert.
  * Neuer Test: `ok("design rules: 45 deg overhang fails when max_overhang_angle is 30 deg", ...)` in [`tests/inventa/check.py`](file:///root/repos/mechvane-argonfix/tests/inventa/check.py#L702-L711).

* **Befund 9** ([`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py#L357-L365)):
  * Wenn bei einem flachen Sackloch ein Finding mit `"status": "warn"` erzeugt wird, setzt `_check_body` nun wie bei `printability` den Regelstatus `rules["thread_depth"]["status"] = "warn"`, wodurch auch das Gesamtergebnis `verdict = "warn"` lautet.
  * Neuer Test: `ok("design rules: shallow blind hole warning sets thread_depth status and verdict to warn", ...)` in [`tests/inventa/check.py`](file:///root/repos/mechvane-argonfix/tests/inventa/check.py#L713-L726).

#### 2. Testergebnis

* `python3 tests/inventa/check.py`:
  * Vorher: **107 Prüfungen** bestanden.
  * Jetzt: **111 Prüfungen** bestanden, **0 failures** (alle grün).
* Git-Commit auf Branch `gemini/argon-fixes`: `c2b93d6 Fix design rules and query findings 1, 4, 5, 9 from review` (nicht gepusht, nicht gemergt).

#### 3. Was nicht gelöst werden konnte

* Alle vier beauftragten Befunde (1, 4, 5, 9) konnten vollständig und sauber gelöst werden. Keine offenen Punkte bei diesen Befunden.

---

### Prüfung durch Claude (2026-10-21)

* Tests auf `gemini/argon-fixes` (c2b93d6) nachgefahren: 111 Prüfungen, 0 Fehler. `expr.evaluate` gibt es in SolidCraft 0.16.2, Einheiten werden umgerechnet (`"1 cm"` ergibt 10.0).
* Befund 5 (Überhang): Die Rechnung `n_z < -sin(α)` stimmt, wenn der Winkel von der Senkrechten gemessen wird.
* Befund 9 (Status `warn`): korrekt.
* **Regression bei Befund 1:** `op in ("join", "new_body", "new")` schließt *alle* Zylinderflächen eines aufgesetzten Features aus, auch innenliegende. Ein Dom als Ring-Extrusion (`join`, Außen-Ø 8, Bohrung Ø 2,5 für M3) liefert auf dem Branch `holes == []`, und die Prüfung der Einschraubtiefe läuft für die Bohrung nicht mehr. Auf `main` wird die Bohrung erkannt, nur die Außenfläche fälschlich als Loch gemeldet. Abhilfe: innen und außen über die Flächennormale relativ zur Achse unterscheiden statt über die Operation. Dazu einen Testfall „Dom mit Bohrung“ ergänzen. Ohne diese Korrektur nicht mergen.
* Kleinigkeiten: `_eval_length` steht doppelt in `design_rules.py` und `query.py`. `rstrip("mm")` entfernt einzelne Zeichen und keine Endung, `expr.evaluate` allein würde reichen.

### Nachbesserung 16c56b8 (Gemini Flash, 2026-10-21), erste Sichtung durch Claude

* Selbst nachgefahren: 112 Prüfungen, 0 Fehler. Der Dom-Test liefert jetzt genau die Bohrung Ø 2,5, die Außenfläche zählt nicht mehr als Loch.
* Methode (`geometry.classify_hole_groups`): Bei unklaren Zylindern legt der Code kleine Prüfkugeln als neue Körper ins Dokument, ruft `inspect.interference` auf und setzt danach per `edit.restore_checkpoint` zurück. Eine Prüfung, die nur lesen soll, verändert also kurz das Modell.
* Vor dem Merge klären:
  1. Ob `edit.checkpoint`/`restore_checkpoint` den Rückgängig-Verlauf, den Speicherstand („geändert“) oder offene Skizzen beeinflusst.
  2. Fehlerpfad: Schlägt `inspect.interference` fehl, verschluckt `except Exception: pass` den Fehler. Die Gruppen stehen dann schon in `probe_map`, gelten als behandelt und fallen ohne Rückfall auf „kein Loch“. Das wäre wieder die alte Regression, nur still.
  3. Ob es einen Weg ohne Änderung am Modell gibt (Punkt-in-Körper-Abfrage oder Flächenorientierung aus SolidCraft).
