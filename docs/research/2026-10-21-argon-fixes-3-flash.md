# Bericht zu SolidCraft-Befehlen, Modellintegrität und Fehlerpfad bei der Lochklassifizierung

Datum: 2026-10-21  
Bearbeiter: Gemini (Antigravity-CLI)  
Zweig: `gemini/argon-fixes`  
Bezug: Prüfung durch Claude (2026-10-21) in `docs/research/2026-10-20-argon-fixes-bericht-flash.md` (Abschnitt "Nachbesserung 16c56b8")

---

### 1. Untersuchung der SolidCraft-Befehle (Punkt-in-Körper / Flächennormale)

Über die SolidCraft-Session wurden alle 394 registrierten Engine-Befehle via `session.tool("list_commands", {})` sowie die MCP-Tools (`body_topology`, `inspect_design`, `measure`) systematisch durchsucht:

* **Punkt-in-Körper-Abfrage**:  
  Es existiert in SolidCraft (Stand 0.16.2) kein Befehl für eine Punkt-im-Festkörper-Klassifizierung (weder `body.contains_point` noch ein entsprechendes `inspect.*`-Kommando).
* **Flächennormale und Flächenorientierung (sense/reversed)**:
  * `model.faces` und `body_topology` liefern für Zylinderflächen `plane_normal: None` und im `cylinder`-Dictionary lediglich `{origin, axis, radius}`. Orientierungsflags wie `reversed`, `sense` oder Normalenvektoren an Oberflächenpunkten werden nicht ausgegeben.
  * `inspect.measure` liefert bei Zylinderflächen nur skalare geometrische Eigenschaften (`diameter`, `radius`, `circumference`, `area_mm2`), aber keinen Normalenvektor und keine Information darüber, auf welcher Seite das Material liegt.
  * `inspect.curvature_comb` und `inspect.minimum_radius` ermitteln Krümmungskämme bzw. Hauptkrümmungsradien; deren Normalen richten sich nach der Kurvenparametrisierung, nicht nach dem Bauteilinneren.
  * `construct.axis.normal_to_face` würde eine Construction Axis als neues Feature erzeugen und ist daher keine reine Leseabfrage.

**Fazit**: Eine reine Leseabfrage ohne Prüfkörper steht in SolidCraft derzeit nicht zur Verfügung. Daher wird die bewährte Methode mit temporären Prüfkugeln (`solid.sphere` + `inspect.interference`) beibehalten, jedoch wie gefordert abgesichert und um einen robusten geometrischen Fallback ergänzt.

---

### 2. Was geändert wurde

* **Modellintegrität und Speicherstatus ([`inventa/geometry.py`](file:///root/repos/inventa-argonfix/inventa/geometry.py))**:
  * Die Interferenzprüfung mit Prüfkugeln läuft innerhalb eines `try...finally`-Blocks abgesichert über `edit.checkpoint` und `edit.restore_checkpoint`.
  * Durch Tests nachgewiesen: Nach Aufruf von `query.find` und `design_rules.check` sind Körperanzahl (`bodies`), Feature-Anzahl (`timeline`), Undo-/Redo-Zähler (`undo`, `redo`) und der Geändert-Status (`dirty: False` bei zuvor gespeichertem Modell) exakt unverändert.
  * Ein nachfolgendes `edit.undo` rollt direkt den letzten Benutzerschritt zurück und greift nicht auf interne Prüfkörper zu.

* **Fehlerbehandlung und koaxialer Fallback ([`inventa/geometry.py`](file:///root/repos/inventa-argonfix/inventa/geometry.py))**:
  * Im Fehlerfall der Interferenzprüfung (z. B. Ausnahme in `session.batch` oder `inspect.interference`) werden die betroffenen Gruppen nun **nicht** mehr in `handled` aufgenommen.
  * Ausnahmen werden nicht mehr stillschweigend mit `pass` verschluckt, sondern lösen eine Warnung aus:  
    `warnings.warn(f"classify_hole_groups: interference probe failed ({e}); falling back to geometric heuristics", UserWarning, stacklevel=2)`.
  * Im Fallback wurde eine koaxiale Geometrieanalyse implementiert:
    * Befinden sich mehrere koaxiale Zylinderflächen auf derselben Achse (wie beim Dom/Standoff: Innenbohrung Ø 2,5 mm und Außenmantel Ø 8 mm), wird die innenliegende Zylinderfläche (`larger_coaxial == True`) als Bohrung klassifiziert und die außenliegende (`smaller_coaxial == True`) als Außenwand.
    * Für einzelne Zylinder ohne koaxiale Innenzylinder und mit `operation in ("join", "new_body", "new")` (z. B. massiver Zapfen) gilt weiterhin `is_hole = False`.
    * Dadurch führt auch ein vollständiger Ausfall der Interferenzabfrage nicht mehr stillschweigend zu "kein Loch" für die Dom-Bohrung.

* **Neue Prüfungen ([`tests/inventa/check.py`](file:///root/repos/inventa-argonfix/tests/inventa/check.py))**:
  * **Test 11**: `design rules and query: model unchanged after checks (body count, timeline, undo/redo, dirty)`:
    Prüft nach `query.find` und `design_rules.check` auf einem gespeicherten Modell, dass `len(bodies)`, `len(timeline)`, `undo`, `redo` und `dirty == False` unverändert bleiben und `edit.undo` die vorherige Benutzer-Feature ansteuert.
  * **Test 12**: `design rules and query: probe failure falls back to geometric heuristics with warning without losing standoff bore`:
    Simuliert per Monkeypatch eine Ausnahme in `inspect.interference`. Weist nach, dass:
    1. Die Dom-Bohrung Ø 2,5 mm weiterhin als Loch erkannt wird,
    2. Die Außenfläche Ø 8 mm nicht als Loch gewertet wird,
    3. `thread_depth` mit Status `ok` besteht,
    4. Eine `UserWarning` geworfen und erfasst wird (nicht stillschweigend),
    5. Keine verwaisten Prüfkörper im Dokument verbleiben (`len(bodies) == 1`).

---

### 3. Testergebnis

* `python3 tests/inventa/check.py`:
  * Vorher: **112 Prüfungen** bestanden.
  * Nachher: **114 Prüfungen bestanden**, **0 failure(s)** (alle grün).
* Vollständige Suite läuft fehlerfrei durch.

---

### 4. Offene Punkte

* Keine offenen Punkte oder funktionale Einschränkungen.
* Sollte künftig in SolidCraft ein nativer `inspect.point_in_body`-Befehl oder ein Flächennormalen-Feld für Zylinderflächen in `model.faces` ergänzt werden, kann der Prüfpfad in `classify_hole_groups` direkt darauf umgestellt werden. Der bestehende koaxiale Fallback bleibt als sichere Rückfallebene erhalten.
