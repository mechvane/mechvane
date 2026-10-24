# Bericht zur Behebung der Regression bei Befund 1 (Dom/Standoff mit Bohrung)

Datum: 2026-10-21  
Bearbeiter: Gemini (Antigravity-CLI)  
Zweig: `gemini/argon-fixes`  
Bezug: Prüfung durch Claude (2026-10-21) in `docs/research/2026-10-20-argon-fixes-bericht-flash.md`

---

### 1. Was geändert wurde

* **Testfall ergänzt** ([`tests/inventa/check.py`](file:///root/repos/mechvane-argonfix/tests/inventa/check.py)):
  * Ein neuer Testfall `10. Standoff with bore (ring extruded with join)` wurde hinzugefügt: Platte 40×40×3 mm (`solid.box`), Skizze auf XY mit Offset 3 mm, zwei konzentrische Kreise um (20, 20) mit $r=4$ und $r=1{,}25$ mm, `solid.extrude` Distanz 8 mm mit Operation `join`, Profil nur der Ring (`[{"point": [23, 20]}]`).
  * Geprüft wird: `query.find(doc, "holes")` findet genau ein Loch mit Durchmesser 2,5 mm, die Außenfläche Ø8 mm wird nicht als Loch gemeldet, und `design_rules.check` erfasst die Bohrung in der Regel `thread_depth`.
  * Dieser Test schlug vor der Behebung wie gefordert fehl (`st_holes == []`, `thread_depth` ohne Befunde).

* **Geometrische Innen-/Außenunterscheidung statt Operations-Ausschluss** ([`inventa/geometry.py`](file:///root/repos/mechvane-argonfix/inventa/geometry.py), [`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py), [`inventa/query.py`](file:///root/repos/mechvane-argonfix/inventa/query.py)):
  * Die Prüfung von `model.faces` ergab: SolidCraft liefert für Zylinderflächen kein `plane_normal` und kein Orientierungsfeld.
  * In [`inventa/geometry.py`](file:///root/repos/mechvane-argonfix/inventa/geometry.py) wurden die zentralen Hilfsfunktionen `group_cylindrical_faces` und `classify_hole_groups` implementiert:
    * Eindeutige Bohrungsfeatures (`HoleFeature`, `operation == "cut"`, Flächennamen mit `:bore:`/`:cut:`/`hole` oder passende Innengewinde) werden direkt als Loch klassifiziert.
    * Bei Zylinderflächen ohne explizite Schnitt-Semantik (z. B. aufgesetzte Features mit Operation `join`/`new` wie Dome, Standoffs oder Zapfen) wird ein Testpunkt knapp innerhalb des Zylinderradius ($\Delta = \min(0{,}2,\, 0{,}2 \cdot r)$ mm vom Flächenpunkt radial zur Zylinderachse) auf Material geprüft:
      * Mittels temporärer Prüfkörper (`solid.sphere` mit $r_{\text{probe}} = \min(0{,}05,\, 0{,}4 \cdot \Delta)$ mm) und `inspect.interference` wird geprüft, ob sich an diesem Punkt Festkörpermaterial des Zielbauteils befindet.
      * Die Erzeugung und Interferenzprüfung erfolgt gebündelt in einem Schritt, abgesichert über `edit.checkpoint` und `edit.restore_checkpoint` (in einem `try...finally`-Block), sodass der Bauteilzustand und die Timeline unverändert bleiben.
      * Befindet sich Material knapp innerhalb der Fläche, zeigt die Normale nach außen (Zapfen/Außendurchmesser $\rightarrow$ kein Loch).
      * Befindet sich dort Leerraum (keine Interferenz), zeigt die Flächennormale zur Achse (Hohlraum/Bohrung $\rightarrow$ Loch).
    * Schlägt der Test fehl oder ist keine Session verfügbar, greift der konservative Bounding-Box-/Operations-Fallback.
  * Diese Regel gilt identisch in [`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py) und [`inventa/query.py`](file:///root/repos/mechvane-argonfix/inventa/query.py).

* **Zentralisierung von `eval_length`** ([`inventa/geometry.py`](file:///root/repos/mechvane-argonfix/inventa/geometry.py)):
  * `eval_length(session, val, default=0.0)` ist jetzt zentral in [`inventa/geometry.py`](file:///root/repos/mechvane-argonfix/inventa/geometry.py) definiert.
  * Die fehleranfällige Zeichenketten-Manipulation `rstrip("mm")` wurde entfernt: Zahlen (`int`, `float`) werden direkt übernommen, Strings werden über SolidCrafts `expr.evaluate` ausgewertet (mit Fallback auf `float(val_str)`).
  * In [`inventa/design_rules.py`](file:///root/repos/mechvane-argonfix/inventa/design_rules.py) und [`inventa/query.py`](file:///root/repos/mechvane-argonfix/inventa/query.py) wurden die doppelten lokalen Implementierungen entfernt und durch `_eval_length = g.eval_length` ersetzt.

---

### 2. Testergebnis

* `python3 tests/inventa/check.py`:
  * Vorher (Stand c2b93d6): **111 Prüfungen**, 0 Fehler.
  * Neuer Testfall vor Fix: **Fehlgeschlagen** (1 failure: `holes=[] thread_depth=[]`).
  * Nach Fix: **112 Prüfungen bestanden**, **0 failure(s)** (alle grün).
  * Der bestehende Test `design rules and query: attached pin with join is not treated as hole` bleibt ebenfalls grün.

---

### 3. Offene Punkte / Unsichere Stellen

* Keine funktionalen Regressionen festgestellt. Alle 112 Prüfungen in `tests/inventa/check.py` laufen fehlerfrei durch.
* Laufzeit-Hinweis: Die Interferenzprüfung für uneindeutige Zylinderflächen via `solid.sphere` + `inspect.interference` + `restore_checkpoint` benötigt ca. 150–250 ms, greift aber nur bei Zylinderflächen aus `join`/`new`/unbekannten Operationen; standardmäßige Bohrungen (`solid.hole` bzw. `cut`) laufen weiterhin sofort ohne Interferenzprüfung.
