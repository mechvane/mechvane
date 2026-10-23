# Praxistest 5: gelagerte Welle

Stand 2026-10-23. Aufbau und Skripte von Claude Sonnet 5.5 über agy. Der Lauf brach
ab, weil das Kontingent aufgebraucht war, deshalb gibt es keinen Bericht von Sonnet.
Claude (Opus, Hauptsession) hat die Fehlerskripte selbst laufen lassen und diese
Zusammenfassung geschrieben. Skripte liegen in `2026-10-23-praxistest-5-skripte/`
(`PYTHONPATH=. python3 <skript>`). `fehler_06` und `fehler_08` brauchen den Workspace
`/tmp/praxis5-ws` aus `bau_01`, `bau_02` und `aender_05`.

Aufbau: Welle Ø 8/10/12 mit Absätzen, Lager DIN 625 608 und 6000, zwei Lagerböcke,
Grundplatte, Verschraubungen (einmal Senkkopf), Drehgelenk. Nach der Änderung
(Absatz, Lagerabstand) und dem Neuöffnen: `check_joints` 32/32 ok,
`inspect.interference` count 0.

## Befunde (Ausgabe der Skripte bestätigt)

| Nr. | Schwere | Befund | Skript |
|---|---|---|---|
| 1 | hoch | `check_design` hält die Außenzylinder einer gedrehten Welle für Bohrungen (Randabstand „fail“). Ein `solid.cylinder` ist ok, also liegt es am Revolve-Fall der Klassifizierung. | `fehler_01` |
| 2 | mittel | `find(holes)` in der Baugruppe liefert die Lagersitze Ø 22 nicht (als Flächen sind sie da), der `diameter`-Filter findet nichts. | `fehler_02`, `fehler_05` |
| 3 | mittel | `through` ist bei der Senkbohrung durch einen 10-mm-Block `False`. | `fehler_02` |
| 4 | mittel | `measure` auf einer Baugruppe liefert Bounding-Box und Schwerpunkt in Bauteil-, nicht in Weltkoordinaten. | `fehler_03` |
| 5 | Lücke | Keine ISO-286-Passungen (H7, k6, h6) für Lagersitz und Welle, weder bei Bohrungen noch bei Normteilen. | `fehler_04` |
| 6 | niedrig | `motion.interference` meldet bei koaxialen, sich nur berührenden Teilen (Lager auf Welle) eine Kollision mit 0,02 mm Tiefe und 0 mm³. Vermutlich SolidCraft-Toleranz, Kandidat für Upstream. | `fehler_06` |
| 7 | hoch | **Test ohne Wirkung:** `tests/inventa/check.py` las die Translation mit `t[0][3]`, die Matrizen haben sie aber in Zeile 3. Die Prüfung „Schraube koaxial zur Bohrung“ in Weltkoordinaten prüfte damit nichts. **Behoben** (Ursprung per `g.apply_point`). | `fehler_07` |
| 8 | mittel | Die Kegelsenkung (`solid.hole` vom Typ `countersink`) ragt 0,81 mm über die Eintrittsfläche hinaus (Fläche `csink:base` bei z = 8,81 statt 8) und kerbt den 0,25 mm entfernten Ständer an. Werkzeug-Überstand in SolidCraft, nachgestellt in `08_minimal_solidcraft_senkung_ueberstand.json` (reines SolidCraft v0.19.0: Wand 0,15 mm neben dem Kegelrand, `model.faces` zeigt `F3:csink:base` bei z = 8,68 über der Eintrittsfläche z = 8). Auf freier Platte kein Überstand. In inventa fehlt außerdem eine Abstandsprüfung zwischen Senkung und Nachbarwand. | `fehler_08` |

Antwortgrößen (`messung_07`): `check_joints` 4,5 KB, `update_links` 5,2 KB (15 s),
`measure` 5,8 KB, `browser` 6,6 KB.
