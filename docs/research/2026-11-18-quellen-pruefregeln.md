# Quellenrecherche: Belege für die fünf Prüfregeln ohne Katalogeintrag (#123)

- **Datum:** 2026-11-18
- **Abgerufen:** alle Quellen am 2026-11-18 geprüft
- **Bezug:** Issue #123 (Folgeauftrag zu #120)
- **Zweck:** Dokumentation der Erstquellen (Hersteller-, Fertiger- und Normen-Sekundärquellen) für die fünf Prüfregeln `min_wall_thickness`, `hole_edge_distance`, `thread_depth`, `printability` und `countersink_clearance` sowie Gegenüberstellung zu den aktuellen Schwellen in `mechvane/design_rules.py` und `mechvane/hole_tables.py`.

---

## Mindestwandstärke (`min_wall_thickness`)

### Hubs: FDM-Standardwandstärke und Mindestwandstärke
- **URL:** [https://www.hubs.com/3d-printing/fdm/](https://www.hubs.com/3d-printing/fdm/)
- **Stelle:** Abschnitte *We have high standards for FDM 3D printing* & *Recommended size*
- **Kennwerte laut Quelle:** Standard-Wandstärke `1.2 mm` (`3` Outline-/Perimeter-Bahnen); Mindestwandstärke (Unsupported walls) `0.8 mm` (`0.0315 in`).
- **Wörtliches Zitat:**
  > „All parts are printed with 3 outline / perimeter shells or a wall thickness of 1.2 mm. [...] Unsupported walls 0.8 mm (0.0315 in)“

### Xometry: FDM-Wandstärke für tragende Strukturen
- **URL:** [https://www.xometry.com/resources/3d-printing/mini-guide-fdm-3d-printing/](https://www.xometry.com/resources/3d-printing/mini-guide-fdm-3d-printing/)
- **Stelle:** Design Tip 1: Wall Thickness
- **Kennwerte laut Quelle:** Empfohlene Wandstärke für tragende Strukturen mindestens `0.047” – 0.06”` (`1.2 – 1.5 mm`).
- **Wörtliches Zitat:**
  > „For supporting structures, walls need to be at least 0.047” – 0.06” (1.2 – 1.5 mm) thick for best results by allowing filament to fill between layers.“

### Protolabs: CNC-Fräsen Nominelle Teiledicke und Merkmalsdicke
- **URL:** [https://www.protolabs.com/services/cnc-machining/cnc-milling/design-guidelines/](https://www.protolabs.com/services/cnc-machining/cnc-milling/design-guidelines/)
- **Stelle:** Abschnitt *Nominal Thickness*
- **Kennwerte laut Quelle:** Nominelle Teiledicke über `0.040 in.` (`1.02mm`) erforderlich; Merkmalsdicken über `0.020 in.` (`0.51mm`) empfohlen.
- **Wörtliches Zitat:**
  > „Part features are recommended to be thicker than 0.020 in. (0.51mm) throughout the part, and a nominal part thickness above 0.040 in. (1.02mm) is required.“

### Hubs: CNC-Fräsen Mindestwandstärke Metalle und Kunststoffe
- **URL:** [https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
- **Stelle:** Abschnitt *Minimum wall thickness*
- **Kennwerte laut Quelle:** Empfohlen `0.8 mm` (Metalle), `1.5 mm` (Kunststoffe); machbar `0.5 mm` (Metalle), `1.0 mm` (Kunststoffe).
- **Wörtliches Zitat:**
  > „Minimum wall thickness [...] Recommended: 0.8 mm (metals), 1.5 mm (plastics) [...] Feasible: 0.5 mm (metals), 1.0 mm (plastics)“

---

## Randabstand von Bohrungen (`hole_edge_distance`)

### AS 4100 (über Draftsperson): Mindestrandabstand ab Lochmitte
- **URL:** [https://blog.draftsperson.net/edge-distance-for-bolts/](https://blog.draftsperson.net/edge-distance-for-bolts/)
- **Stelle:** AS 4100 Minimum Edge Distance
- **Kennwerte laut Quelle:** `1.50 ×` Schraubendurchmesser (gewalzte Plattenkante, maschinell brenngeschnitten, gesägt oder gehobelt); `1.75 ×` Schraubendurchmesser (gescherte oder handbrenngeschnittene Kante); `1.25 ×` Schraubendurchmesser (gewalzte Profilkante). (1.75× und 1.25× stehen nicht im Zitat und sind deshalb nicht in den Katalog übernommen, 2026-11-18)
- **Wörtliches Zitat:**
  > „Edge distance is the distance from the centre of a bolt hole to the edge of the steel. [...] 1.50 × bolt diameter — a rolled plate edge, machine flame cut, sawn or planed.“

### Eurocode 3 (EN 1993-1-8, über Schweizer-FN): Rand- und Lochabstand
- **URL:** [https://www.schweizer-fn.de/maschinenelemente/schraube_ec3/schraubenverbindung_ec3.php](https://www.schweizer-fn.de/maschinenelemente/schraube_ec3/schraubenverbindung_ec3.php)
- **Stelle:** Minimaler und Maximaler Rand- und Lochabstand von Schrauben im Stahlbau (EN 1993-1-8)
- **Kennwerte laut Quelle:** `e1 >= 1,2 * d0`, `e2 >= 1,2 * d0` (Standardlöcher), `e3 >= 1,5 * d0` (Langlöcher).
- **Wörtliches Zitat:**
  > „Minimaler und Maximaler Rand- und Lochabstand von Schrauben im Stahlbau. [...] Randabstand: e1 ≥ 1,2 * d0 [...] Randabstand: e2 ≥ 1,2 * d0 [...] Randabstand: e3 ≥ 1,5 * d0“

### BS EN 1993-1-8:2005 (über SteelSpec Data Hub): Messbezug Bohrungsmitte
- **URL:** [https://structuralsteelcomponents.com/steelspec-data-hub/connection-design-rules/](https://structuralsteelcomponents.com/steelspec-data-hub/connection-design-rules/)
- **Stelle:** BS EN 1993-1-8:2005 Table 3.3 & Table 3.4
- **Kennwerte laut Quelle:** `e1 >= 1.2 × d0`, `e2 >= 1.2 × d0` (jeweils ab Bohrungsmitte); Lochleibungsfaktor `k1 = min(2.8 × e2/d0 − 1.7, 2.5)`.
- **Wörtliches Zitat:**
  > „All distances measured to the centre of the bolt hole. [...] End distance e1 ≥ 1.2 × d0 [...] Edge distance e2 ≥ 1.2 × d0“

---

## Einschraubtiefe (`thread_depth`)

### Bossard Blatt 52 (01/2025): Einschraubtiefe nach Werkstoff (8.8 Regelgewinde)
- **URL:** [https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf)
- **Stelle:** Bossard Technische Informationen Blatt 52 (01/2025), Tabelle 8.8 Regelgewinde
- **Kennwerte laut Quelle:** Baustahl `S235` (`> 360` N/mm²): `1,0 · d`; Grauguss `GJL 250` (`> 220` N/mm²): `1,0 · d`; weiches Aluminium `AlMg3 F18` (`> 180` N/mm²): `2 · d` (VDI 2230: `3 · d`); Knetaluminium `AlMgSi1 F32` (`> 330` N/mm²): `1,4 · d`.
- **Wörtliches Zitat:**
  > „S235 (St37-2) > 360 (Ferrit / Perlit-Gefüge) 1,0 · d [...] GJL 250 (GG-25) > 220 1,0 · d [...] AlMg3 F18 > 180 2 · d [3 · d]1) [...] AlMgSi1 F32 > 330 1,4 · d“

### Hubs: Allgemeine Mindest-Gewindelänge beim CNC-Fräsen
- **URL:** [https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
- **Stelle:** Abschnitt *Thread length*
- **Kennwerte laut Quelle:** Minimum `1.5` × Nenndurchmesser; empfohlen `3` × Nenndurchmesser.
- **Wörtliches Zitat:**
  > „Minimum: 1.5 times nominal diameter [...] Recommended: 3 times nominal diameter“

### EcomFasteners: Faustwerte für Stahl, Grauguss, Messing, Aluminium und Kunststoffe
- **URL:** [https://www.ecomfasteners.com/pages/thread-engagement-chart](https://www.ecomfasteners.com/pages/thread-engagement-chart)
- **Stelle:** Thread Engagement Chart / Rule of Thumb
- **Kennwerte laut Quelle:** Stahl `1x`; Grauguss, Messing/Bronze `1.5x`; Aluminium, Zink oder Kunststoffe `2x`.
- **Wörtliches Zitat:**
  > „As a rule of thumb, engage at least 1x the bolt's nominal diameter in steel (10 mm for an M10). Softer materials need more: about 1.5x in cast iron, brass or bronze, and about 2x in aluminum, zinc or plastics.“

---

## Druckbarkeit (`printability`)

### Hubs: Maximaler FDM-Überhangwinkel ohne Stütze
- **URL:** [https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
- **Stelle:** Abschnitt *Overhangs*
- **Kennwerte laut Quelle:** Überhänge bis `45°` ohne Qualitätseinbuße druckbar (`50%` Schichtüberdeckung).
- **Wörtliches Zitat:**
  > „Depending on the material, an overhang can usually be printed up to 45° without compromising quality. At 45°, the newly printed layer is supported by 50% of the previous layer.“

### Hubs: Mindest-Lochdurchmesser FDM
- **URL:** [https://www.hubs.com/3d-printing/fdm/](https://www.hubs.com/3d-printing/fdm/)
- **Stelle:** Abschnitt *Recommended size: Minimum hole diameter*
- **Kennwerte laut Quelle:** Mindest-Lochdurchmesser FDM `2.0 mm` (`0.0787 in`).
- **Wörtliches Zitat:**
  > „Minimum feature size 2.0 mm (0.0787 in) Minimum hole diameter 2.0 mm (0.0787 in)“

### Protolabs: Mindest-Lochdurchmesser FDM
- **URL:** [https://www.protolabs.com/en-gb/services/3d-printing/fused-deposition-modelling/](https://www.protolabs.com/en-gb/services/3d-printing/fused-deposition-modelling/)
- **Stelle:** Capabilities table: Minimum Hole Diameter
- **Kennwerte laut Quelle:** Mindest-Lochdurchmesser FDM `2.0 mm`.
- **Wörtliches Zitat:**
  > „Minimum Hole Diameter 2.0 mm“

### Hubs: Mindest-Lochdurchmesser CNC-Bearbeitung
- **URL:** [https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
- **Stelle:** Abschnitte *Holes (Diameter)* & *Small features (Minimum hole diameter)*
- **Kennwerte laut Quelle:** Machbar jeder Bohrungsdurchmesser größer als `1 mm` (unter *Holes -> Diameter*); empfohlen für Standardwerkzeuge ohne Mikrozerspanung `2.5 mm` (`0.1 inches`).
- **Wörtliches Zitat:**
  > „Feasible: any diameter larger than 1 mm [...] Most machine shops can accurately machine cavities and holes using tools down to 2.5 mm (0.1 inches) in diameter.“

---

## Senkungsfreiraum (`countersink_clearance`)

### Protolabs: Werkzeugzugang neben hohen Wänden und Maßbezug Senkdurchmesser
- **URL:** [https://www.protolabs.com/resources/blog/cnc-hole-design-through-blind-tapped-and-more/](https://www.protolabs.com/resources/blog/cnc-hole-design-through-blind-tapped-and-more/)
- **Stelle:** Abschnitte *Tool Access* & *Edge Distance*
- **Aussage laut Quelle (sinngemäß):** Bohrungen nahe an hohen Wänden erfordern längere, unsteifere Werkzeuge; dem Werkzeug ist ein freier Zugangsweg zu lassen. Bei der Abstandsprüfung ist der größte Durchmesser des gesamten Merkmals inklusive Flachsenkung und Kegelsenkung zu berücksichtigen.
- **Wörtliches Zitat:**
  > „Holes inside deep pockets or close to tall walls may require longer, less rigid tools, which can hurt accuracy and increase machining time. Give the tool a clear path to the feature whenever possible. [...] When checking edge distance, consider the largest diameter of the entire feature, including counterbores and countersinks.“

### TZR Metal: Werkzeugkollision mit senkrechten Flanschen und Randabstand von Senkungen
- **URL:** [https://tzrmetal.com/countersink-holes/](https://tzrmetal.com/countersink-holes/)
- **Stelle:** Abschnitt *Edge and Bend Clearance*
- **Kennwerte laut Quelle:** Abstand Senkungsmitte zu Kante mindestens `1.5` × größter Senkdurchmesser; Freiraum stets vom Außendurchmesser der Senkung (Major Diameter) bemessen, um Kollision des Kegelsenkers mit senkrechten Flanschen/Wänden zu vermeiden.
- **Wörtliches Zitat:**
  > „Furthermore, placing a countersink too close to a bend line creates tooling interference: the angled cutter will strike the vertical flange, damaging both the tool and the workpiece. Always calculate clearance from the major diameter of the countersink, not the center point of the pilot hole. [...] As a standard rule of thumb, the minimum distance from the edge of the part to the center of the countersink should be at least 1.5 times the major diameter.“

---

## Abgleich mit Mechvane (Abweichungen)

Die Schwellen in `mechvane/design_rules.py` und `mechvane/hole_tables.py` blieben unverändert. Festgestellte Abweichungen gegenüber den geprüften Quellen:

1. **`min_wall_thickness` (CNC Alu):** Mechvane prüft `1,0 mm`. Protolabs fordert eine nominelle Teiledicke über `1,02 mm` (`0.040 in.`) bei Merkmalen über `0,51 mm`; Hubs empfiehlt `0,8 mm` für Metalle (machbar `0,5 mm`). Keine der geprüften Primärquellen nennt exakt `1,0 mm` für CNC-Aluminium. Für FDM bestätigt Hubs `1,2 mm` (3 Perimeter) als Standard-Wandstärke und `0,8 mm` als druckbares Minimum.
2. **`hole_edge_distance`:** Mechvane prüft `1,5 × d` einheitlich auf den Bohrungsdurchmesser in beiden Profilen (`fdm_0.4`, `cnc_alu`). AS 4100 nennt `1,50 × Schraubendurchmesser` (maschinell geschnittene/gesägte/gewalzte Kante), Eurocode 3 (EN 1993-1-8) nennt `1,2 × d0` (Lochdurchmesser) für Standard-Rundlöcher bzw. `1,5 × d0` für Langlöcher und erreicht bei `e2 >= 1,5 × d0` den vollen Lochleibungsfaktor `k1 = 2,5`.
3. **`thread_depth`:** `steel` (`1,0`), `cast_iron` (`1,0`), `alu` (`2,0`), `alu_wrought` (`1,4`) sowie der Profil-Standard `1,5` decken sich direkt mit Bossard Blatt 52 (01/2025) bzw. Hubs CNC. Abweichungen bzw. Lücken in `mechvane/hole_tables.py`:
   - `brass`: `hole_tables.py` führt `1,2 × d` (mit Vermerk `UNVERIFIED`, Verweis auf Roloff-Matek); frei zugängliche Online-Quellen (EcomFasteners `1,5×`, Tameson `1,5–2,0×`) nennen `1,5 × d` (Bossard listet kein Messing; Ingenieurkurse gibt `1,3 × d` nur bis Festigkeitsklasse `6.8` an und lässt `8.8` offen).
   - `alu_cast`: `hole_tables.py` führt `2,0 × d` (`UNVERIFIED`); Bossard hat keine eigene Guss-Zeile, Hanke/VDI 2230 liefert je nach Legierung `2,2–3,5 × d`, EcomFasteners pauschal `2×`.
   - `plastic`: `hole_tables.py` führt `2,5 × d` (`UNVERIFIED`); EcomFasteners nennt `2,0×` allgemein und `2,5–3,0×` für weiche Kunststoffe.
4. **`printability`:** FDM-Überhang `<= 45°` und FDM-Mindestbohrung `2,0 mm` stimmen mit Hubs und Protolabs überein. CNC-Mindestbohrung `1,0 mm` entspricht Hubs' machbarem Grenzwert unter *Holes → Diameter* (`> 1 mm`), während Hubs unter *Small features* ab `2,5 mm` als Standardgrenze vor Mikrozerspanung empfiehlt.
5. **`countersink_clearance`:** Geometrische Kollisionsprüfung ohne Zahlenwert (`:csink:base`); Protolabs und TZR Metal belegen die Anforderung, den gesamten Senkdurchmesser (Major Diameter) frei von benachbarten Wänden/Flanschen zu halten.
