---
name: varianten
description: Parametervarianten eines vorhandenen Bauteils in Mechvane durchrechnen und als Manifest mit Bericht liefern ("was passiert, wenn A zwischen 50 und 70 mm liegt und die Bohrung 6,6 bis 20 mm"). Prüft vorher, ob ein Parameter überhaupt etwas treibt, lässt die Anzahl der Varianten bestätigen, fasst die Basis nie an, meldet Fehlschläge je Variante statt abzubrechen. Nutzen bei Fragen wie "probier mal Werte durch", "wie empfindlich ist das Teil auf X", "wo kippt es". Nicht für Optimierung, Last- oder Festigkeitsrechnung und nicht für neue Geometrie.
---

# Parametervarianten (Mechvane)

Ablauf über das Werkzeug `check_parameters(document, set)`: Es setzt Werte probeweise, misst und stellt das Design zurück
(`restored: true`). Dazu `check_design`, `run` (mit `parameters.change`, `edit.checkpoint`, `edit.restore_checkpoint`) und `browser`.
Ergebnis ist ein **Manifest** (JSON Lines) und ein kurzer Bericht, keine neuen Bauteildateien.

## Ablauf

0. **Vorbereiten.** Parameternamen mit `run(document, [{"command": "parameters.list"}])` lesen und genau diese Namen verwenden
   (ein unbekannter Name wird mit der Liste der echten abgelehnt). Ist das Teil in einer Baugruppe eingebunden, vorher sagen, dass Lage
   und Passung in der Baugruppe nicht mitgeprüft werden.
1. **Ausgangslage.** `check_parameters` mit **einem** Parameter auf seinem aktuellen Wert (`set` darf nicht leer sein). Merken:
   `measure.total.volume_mm3`, `measure.body_count`, `bbox` des Körpers, die Zylinderliste (`cylinders`: Mittelpunkte auf 0,1 mm,
   Radien auf 0,01 mm gerundet).
2. **Treiberprüfung.** Je gewünschtem Parameter ein Probelauf am Rand seines Bereichs, verglichen mit der Ausgangslage. **Alle vier
   Größen vergleichen, nicht nur das Volumen:** Ein Lochkreis ändert das Volumen nicht, nur die Lage der Bohrungen. Ändert sich
   nichts, kommt der Parameter als `requested_not_driving` ins Manifest, der Lauf geht mit den übrigen weiter.
3. **Menge bestätigen lassen.** Parameter, Bereiche, Schrittweite und die **Anzahl als Zahl** nennen (z. B. 3 × 3 = 9) und auf ein Ja
   warten. Ohne Ja nichts erzeugen. Ab etwa 30 Varianten fragen, ob der Bereich enger sein soll.
4. **Lauf.** Je Variante `check_parameters` mit allen Werten (Einheit mit angeben: `"70 mm"`):
   - `errors`, `parameter_errors` nicht leer, **oder** `body_count` 0, **oder** keine Zylinder, obwohl die Basis welche hat →
     `regeneration_failed` mit Grund. Ein zu großes Maß meldet sich oft nur als leerer Körper, nicht als Fehler.
   - andere Körperzahl als in der Ausgangslage (das Teil zerfällt) → `topology_changed`.
   - sonst `generated`.

   Für `generated` die **Regelbefunde**: `check_parameters` stellt zurück und `check_design` prüft nur den aktuellen Stand, also
   `edit.checkpoint` (die Nummer steht in `results[0].checkpoint` der `run`-Antwort) → `parameters.change` mit
   `{"changes": {"A": "70 mm", ...}}` → `check_design` → `edit.restore_checkpoint` (`{"checkpoint": Nummer}`)
   (**ohne** `forget`; `forget: true` verwirft nur und stellt nicht zurück) → Parameterausdrücke lesen und mit den ursprünglichen
   vergleichen. Weichen sie ab, den Lauf abbrechen und das melden. Für fehlgeschlagene Varianten gibt es keinen Befund: `findings: null`.
   Ein Fehlschlag bricht den Lauf nie ab; an den Bereichsrändern sind sie normal.
5. **Manifest** neben die Teiledatei schreiben (`<Teil>.varianten.jsonl`, eine Zeile je Variante, zuerst eine Kopfzeile). Felder siehe
   `reference/beispiel-manifest.jsonl`, aus einem echten Lauf am Referenzflansch.
6. **Bericht.** Tabelle der Varianten und in Worten: welche Parameter treiben, wo der erste Fehlschlag und die erste Regelverletzung
   liegen, welche Variante die Regeln erfüllt. Keine Wertung ohne Kriterien des Nutzers.

## Manifest

Kopfzeile: `base`, `parameters_varied`, `requested_not_driving`, `variant_count_confirmed`, `parametric_check` (`ran`, `baseline`).
Je Variante: `variant_id`, `parameter_values`, `status` (`generated`, `regeneration_failed`, `topology_changed`, `skipped`),
`status_detail`, `volume_mm3`, `mass_g`, `bodies`, `bbox_max`, `findings` (`verdict`, `failed_rules`) oder `null`.
**Nicht geprüft ist etwas anderes als geprüft und in Ordnung:** `findings: null` heißt "nicht geprüft", eine leere Liste "in Ordnung".

## Grenzen

- Die Varianten werden nicht als Dateien gespeichert. Wer eine behalten will, setzt ihre Werte von Hand (`parameters.change`,
  danach `save_document`).
- Mechvane rechnet keine Lasten. Masse folgt aus Volumen und Werkstoff, mehr nicht.
- Die Basis bleibt unverändert; nach dem Lauf stimmen alle Parameterausdrücke mit denen vor dem Lauf überein.
