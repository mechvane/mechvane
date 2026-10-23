# Normteile-Generator (`inventa/standard_parts.py`)

Stand 2026-10-20. Umsetzung des Phase-1-Bausteins „Normteile-Generator,
prozedural statt Inhaltscenter-Datenbank“ aus [ROADMAP.md](../../ROADMAP.md).

## 1. Einordnung und Werkzeug-Signatur

SolidCraft bringt unter `crates/engine/src/cmd/parts.rs` zwar ein eigenes
`parts.insert` / `parts.fastener` mit, legt damit aber Unterkomponenten im
aktuellen Design und mit fest einkodierten Zahlenwerten (ohne `parameters.add`)
an; zudem fehlen dort `M2,5`, das Lager `6005` sowie Einschmelzgewinde für den
3D-Druck.

Nach [ADR 0001](../adr/0001-grundlage-solidcraft.md) ist jedes Bauteil in
inventa eine eigene `.solidcraft`-Datei ohne Komponenten. `inventa/standard_parts.py`
erzeugt Normteile deshalb als eigenständige Bauteildateien:

- **Benannte Parameter (`parameters.add`)**: Alle Nennmaße aus der jeweiligen
  Normtabelle werden als Benutzerparameter angelegt (`d`, `P`, `dk`, `k`, `s`,
  `t`, `l`, `b`, `m_nut`, `d1`, `d2`, `h`, `D`, `L`, `B`, `d_hole`).
- **Bemaßte Skizzen (`sketch.draw.dimensioned`)**: Kreis- und Sechskantskizzen
  referenzieren diese Parameter direkt, sodass Änderungen über
  `parameters.change` die Geometrie tatsächlich neu berechnen.
- **Skizzenregel**: Jedes Feature (`Head`, `Shank`, `Socket`, `HexBody`,
  `Disk`, `Sleeve`, `Ring`, `Bore`) besitzt genau eine eigene Skizze direkt
  davor im Verlauf; `sketch_rule.enforce` hat keine Verschiebungen oder
  Ablehnungen (`moved: []`, `refused: []`).
- **Metadaten**: Unter `io.github.nilsgollub.inventa` wird neben `kind: "part"`
  und `format: 1` das Feld `standard` gespeichert (`norm`, `size`,
  `designation`, `dimensions`, bei Schrauben `length` und `preferred_length`,
  bei Einschmelzgewinden `mounting_hole`).

### MCP-Werkzeuge in `inventa/server.py`

1. `standard_part(norm, size, length=None, name=None, path=None)`
   - `norm` und `size` sind für alle Normen Pflicht (Aliase wie `DIN 912`,
     `DIN 934`, `DIN 125`, `heat_insert`, `ISO 15`, `bearing` sowie
     Kommaschreibweise `M2,5` werden aufgelöst).
   - `length` ist optional (`None`), da nur Schrauben (`ISO 4762`) eine frei
     wählbare Nennlänge haben, während Muttern, Scheiben, Einschmelzgewinde und
     Kugellager feste Tabellenmaße besitzen. Alternativ wird auch die
     Kurzschreibweise `size="M5x16"` erkannt.
   - `name` und `path` sind optional wie bei `new_part`/`open_document`: Ohne
     Angabe wird der Dokumentname aus der Normbezeichnung abgeleitet (z. B.
     `ISO_4762_M5x16` → `<workspace>/ISO_4762_M5x16.solidcraft`). Das Teil wird
     gespeichert und bleibt als Sitzung geöffnet.
2. `list_standard_parts(norm=None)`
   - Ohne Argument: Übersicht aller fünf Normen mit kanonischem Namen, Aliasen
     und verfügbaren Größen.
   - Mit `norm`: vollständige Maßtabelle dieser Norm (ohne SolidCraft-Prozess,
     direkt aus den Moduldaten).

---

## 2. Maßtabellen und Quellen

Alle Maße in Millimetern (mm). Regelgewinde-Steigungen $P$ nach
**DIN ISO 261 / DIN ISO 724**.

### 2.1 ISO 4762 (früher DIN 912) – Zylinderschrauben mit Innensechskant

Quelle: **DIN EN ISO 4762** (Tabellen 1 und 2, Produktklasse A).
- $d$: Gewinde-Nenndurchmesser
- $P$: Steigung Regelgewinde
- $d_k$: Kopfdurchmesser (Nennmaß = Höchstmaß $d_{k,\max}$ für glatten Kopf)
- $k$: Kopfhöhe (Nennmaß = Höchstmaß $k_{\max}$)
- $s$: Schlüsselweite Innensechskant (Nennmaß $s_{\text{nom}}$)
- $t$: Einstecktiefe Innensechskant (Mindestmaß $t_{\min}$ nach Norm)
- $b_{\text{ref}}$: Referenz-Gewindelänge $2d + 12\text{ mm}$ (für $l \le 125\text{ mm}$; bei $l \le b_{\text{ref}}$ Gewinde bis Kopf)

| Größe | $d$ | $P$ | $d_k$ | $k$ | $s$ | $t$ | $b_{\text{ref}}$ | Vorzugslängen $l$ (Handelsbereich nach ISO 4762 Tab. 2) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **M2,5** | 2,5 | 0,45 | 4,5 | 2,5 | 2,0 | 1,1 | 17 | 4, 5, 6, 8, 10, 12, 16, 20, 25 |
| **M3** | 3,0 | 0,50 | 5,5 | 3,0 | 2,5 | 1,3 | 18 | 5, 6, 8, 10, 12, 16, 20, 25, 30 |
| **M4** | 4,0 | 0,70 | 7,0 | 4,0 | 3,0 | 2,0 | 20 | 6, 8, 10, 12, 16, 20, 25, 30, 35, 40 |
| **M5** | 5,0 | 0,80 | 8,5 | 5,0 | 4,0 | 2,5 | 22 | 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50 |
| **M6** | 6,0 | 1,00 | 10,0 | 6,0 | 5,0 | 3,0 | 24 | 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60 |
| **M8** | 8,0 | 1,25 | 13,0 | 8,0 | 6,0 | 4,0 | 28 | 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80 |
| **M10** | 10,0 | 1,50 | 16,0 | 10,0 | 8,0 | 5,0 | 32 | 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100 |
| **M12** | 12,0 | 1,75 | 18,0 | 12,0 | 10,0 | 6,0 | 36 | 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120 |

### 2.2 ISO 4032 (ersetzt DIN 934) – Sechskantmuttern Typ 1

Quelle: **DIN EN ISO 4032** (Tabelle 1, Produktklassen A und B). Gegenüber der
zurückgezogenen DIN 934 weichen Schlüsselweite $s$ (M10: 16 statt 17 mm, M12:
18 statt 19 mm) und Mutterhöhe $m$ ab.
- $s$: Schlüsselweite (Nennmaß = Höchstmaß $s_{\max}$)
- $m$: Mutterhöhe (Nennmaß = Höchstmaß $m_{\max}$)

| Größe | $d$ | $P$ | $s$ | $m$ |
|---|---:|---:|---:|---:|
| **M2,5** | 2,5 | 0,45 | 5,0 | 2,0 |
| **M3** | 3,0 | 0,50 | 5,5 | 2,4 |
| **M4** | 4,0 | 0,70 | 7,0 | 3,2 |
| **M5** | 5,0 | 0,80 | 8,0 | 4,7 |
| **M6** | 6,0 | 1,00 | 10,0 | 5,2 |
| **M8** | 8,0 | 1,25 | 13,0 | 6,8 |
| **M10** | 10,0 | 1,50 | 16,0 | 8,4 |
| **M12** | 12,0 | 1,75 | 18,0 | 10,8 |

### 2.3 ISO 7089 (ersetzt DIN 125-1) – Flache Scheiben, normale Reihe, 200 HV

Quelle: **DIN EN ISO 7089** (Tabelle 1, Produktklasse A, Härteklasse 200 HV).
- $d_1$: Lochdurchmesser (Nennmaß = Mindestmaß $d_{1,\min}$ nach ISO 273 mittel)
- $d_2$: Außendurchmesser (Nennmaß = Höchstmaß $d_{2,\max}$)
- $h$: Scheibendicke (Nennmaß $h_{\text{nom}}$)

| Größe | $d$ | $d_1$ | $d_2$ | $h$ |
|---|---:|---:|---:|---:|
| **M2,5** | 2,5 | 2,7 | 6,0 | 0,5 |
| **M3** | 3,0 | 3,2 | 7,0 | 0,5 |
| **M4** | 4,0 | 4,3 | 9,0 | 0,8 |
| **M5** | 5,0 | 5,3 | 10,0 | 1,0 |
| **M6** | 6,0 | 6,4 | 12,0 | 1,6 |
| **M8** | 8,0 | 8,4 | 16,0 | 1,6 |
| **M10** | 10,0 | 10,5 | 20,0 | 2,0 |
| **M12** | 12,0 | 13,0 | 24,0 | 2,5 |

### 2.4 Gewindeeinsätze zum Einschmelzen für 3D-Druck (Ruthex / CNC Kitchen)

Quelle: **Ruthex Herstellerdatenblätter** (Standard-Reihe Messing, baugleich
mit dem CNC-Kitchen-Standardsortiment).
- $D$: Außendurchmesser über der Rändelung ($D_1$)
- $L$: Länge des Gewindeeinsatzes
- $d_{\text{hole}}$: empfohlener Durchmesser der zylindrischen Aufnahmebohrung
  im Druckteil
- $\text{min\_depth}$: empfohlene Mindesttiefe des Sacklochs ($L + 1{,}0\text{ mm}$)

| Größe | Artikelcode | $d$ | $P$ | $D$ | $L$ | Aufnahmebohrung $\varnothing\,d_{\text{hole}}$ | Mindesttiefe |
|---|---|---:|---:|---:|---:|---:|---:|
| **M2,5** | `RX-M2.5x5.7` | 2,5 | 0,45 | 4,6 | 5,7 | 4,0 | 6,7 |
| **M3** | `RX-M3x5.7` | 3,0 | 0,50 | 4,6 | 5,7 | 4,0 | 6,7 |
| **M4** | `RX-M4x8.1` | 4,0 | 0,70 | 6,3 | 8,1 | 5,6 | 9,1 |
| **M5** | `RX-M5x9.5` | 5,0 | 0,80 | 7,1 | 9,5 | 6,4 | 10,5 |

### 2.5 DIN 625-1 / ISO 15 – Einreihige Rillenkugellager 6000er-Reihe

Quelle: **DIN 625-1** / **ISO 15** (Maßreihe 10).
- $d$: Bohrungsdurchmesser (Wellensitz)
- $D$: Außendurchmesser (Gehäusesitz)
- $B$: Lagerbreite

| Bezeichnung | $d$ | $D$ | $B$ |
|---|---:|---:|---:|
| **6000** | 10,0 | 26,0 | 8,0 |
| **6001** | 12,0 | 28,0 | 8,0 |
| **6002** | 15,0 | 32,0 | 9,0 |
| **6003** | 17,0 | 35,0 | 10,0 |
| **6004** | 20,0 | 42,0 | 12,0 |
| **6005** | 25,0 | 47,0 | 12,0 |

---

## 3. Vereinfachungen und Modellierungsdetails

1. **Gewinde als Nenndurchmesser + kosmetisches `solid.thread`**:
   Schraubenschäfte (`ISO 4762`) und Mutter-/Einsatzbohrungen (`ISO 4032`,
   `Ruthex`) werden mit ihrem Nennmaß $d$ extrudiert und erhalten ein
   kosmetisches `ThreadFeature` (`modeled: false`, z. B. `M5x0.8`). Dadurch
   bleibt der B-Rep-Körper frei von teuren Helix-Flächen, das Volumen ist exakt
   analytisch prüfbar, und `model.threads` führt das Gewinde trotzdem für
   Zeichnungen und Prüfungen.
2. **Reservierter Parametername `m` in SolidCraft**:
   SolidCraft lehnt `parameters.add` mit `name: "m"` ab (`'m' is a unit,
   constant or function name`, da `m` für Meter steht). In `ISO 4032` heißt der
   Benutzerparameter im Modell daher `m_nut`, während in der Maßtabelle und in
   `metadata["standard"]["dimensions"]["m"]` die Normbezeichnung `m` erhalten
   bleibt.
3. **Verzicht auf Fasen, Rändelungen und Kantenrundungen**:
   - **ISO 4762**: Ohne Kopfrändelung, Kopfoberkanten-Fase, Unterkopfradius
     $r$, Kuppe am Schaftende und ohne Bohrungskegel am Grund des
     Innensechskants. Die Kopfauflage liegt auf $z = 0$ (Kopf $0 \dots k$,
     Schaft $-l \dots 0$), passend zur Konvention für Baugruppen-Gelenke.
   - **ISO 4032**: Sechskantprisma ohne beidseitige 15°–30°-Senkfase und ohne
     Auflageansatz $d_w$.
   - **Ruthex-Gewindeeinsätze**: Modelliert als zylindrische Hülse mit dem
     maximalen Außendurchmesser $D$ über den Rändelrippen, ohne gegenläufige
     Schrägrändelung und ohne abgestuften Einführbund.
   - **DIN 625 Kugellager**: Entschieden für die Darstellung als geschlossener
     **Hüllring** mit $d, D, B$ (ohne Kugeln, Käfig, Schulterdurchmesser
     $d_1/D_1$ und Kantenabstand $r$). Grund: Die Innengeometrie ($d_1, D_1$,
     Kugeldurchmesser, Kugelanzahl) ist in DIN 625 / ISO 15 nicht festgelegt,
     sondern herstellerabhängig. Der Hüllring kommt ohne erfundene Zwischenmaße
     aus, liefert die für Wellen- und Gehäusesitz relevanten Zylinder- und
     Stirnflächen und hat ein exakt durch die Normtabelle bestimmtes Volumen.

### Messvergleich (analytisches Sollvolumen vs. SolidCraft)

| Normteil | Formel Sollvolumen | Soll (mm³) | SolidCraft (mm³) | Rel. Abweichung |
|---|---|---:|---:|---:|
| `ISO 4762 M5x16` | $\pi (d_k/2)^2 k + \pi (d/2)^2 l - \frac{\sqrt{3}}{2} s^2 t$ | 563,2433 | 563,1591 | $1{,}49 \cdot 10^{-4}$ |
| `ISO 4032 M5` | $\left(\frac{\sqrt{3}}{2} s^2 - \pi (d/2)^2\right) m$ | 168,2162 | 168,2297 | $8{,}06 \cdot 10^{-5}$ |
| `ISO 7089 M5` | $\pi \left((d_2/2)^2 - (d_1/2)^2\right) h$ | 56,4780 | 56,4758 | $3{,}95 \cdot 10^{-5}$ |
| `Ruthex RX-M3x5.7` | $\pi \left((D/2)^2 - (d/2)^2\right) L$ | 54,4375 | 54,4323 | $9{,}51 \cdot 10^{-5}$ |
| `DIN 625 6000` | $\pi \left((D/2)^2 - (d/2)^2\right) B$ | 3619,1147 | 3618,9274 | $5{,}18 \cdot 10^{-5}$ |

Alle Werte liegen innerhalb der Tessellierungstoleranz `REL = 2e-4`.

---

## 4. Unsichere bzw. herstellerabhängige Werte

1. **ISO 4762 – Randstufen der Vorzugslängen je Durchmesser**:
   Die allgemeine Vorzugslängenreihe nach ISO 4762 Tabelle 2 (`4, 5, 6, 8, 10,
   12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120`)
   sowie die eingeklammerten Zwischenlängen (`14, 18, 22`) sind eindeutig. An
   den oberen und unteren Stufenlinien des handelsüblichen Bereichs je Größe
   (z. B. ob `M3×4` oder `M12×65` noch innerhalb der Stufenlinie liegt) weichen
   Tabellenbücher und Händlerkataloge gelegentlich um eine Stufe ab. Da jede
   positive Länge zulässig ist und nur eine Warnung erzeugt wird, blockiert das
   keine Konstruktion.
2. **ISO 4762 – Einstecktiefe $t$**:
   In ISO 4762 ist $t$ als **Mindestmaß** ($t_{\min}$) genormt, während $d_k$
   und $k$ Höchstmaße sind. Reale Schrauben haben eine etwas größere
   Innensechskanttiefe plus Grundkegel. Für das prozedurale Modell wird
   durchgängig $t_{\min}$ verwendet (übereinstimmend mit SolidCrafts `SHCS`-Tabelle).
3. **Ruthex-Gewindeeinsätze – Außendurchmesser und Aufnahmebohrung**:
   Einschmelzgewinde sind Herstellerteile ohne ISO/DIN-Norm:
   - Der Außendurchmesser $D$ (`4,6 / 4,6 / 6,3 / 7,1 mm`) ist in den
     Ruthex-Datenblättern als Richtwert über der Rändelung (`~`) angegeben.
   - Bei **M5** (`RX-M5x9,5`) nennen manche Händlerübersichten `6,3 mm` bis
     `6,4 mm` als Vorbohrung; hier ist der Ruthex-Standardwert `6,4 mm`
     hinterlegt.
   - Die Mindesttiefe `L + 1,0 mm` (`6,7 / 6,7 / 9,1 / 10,5 mm`) ist eine
     praxisübliche Konstruktionsregel für Sacklöcher im FDM-Druck, kein starres
     Normmaß. Zudem empfiehlt CNC Kitchen / Ruthex alternativ konische
     Aufnahmebohrungen, während hier die zylindrische Standardbohrung angegeben
     ist.

---

## 5. Offene Punkte

1. **Bohrungsassistent mit Verschraubung (ROADMAP Phase 1)**:
   Nächster Baustein, der Durchgangsbohrung (ISO 273) bzw. Aufnahmebohrung
   (`mounting_hole` aus den Metadaten der Einschmelzgewinde) im Bauteil anlegt
   und Schraube + Scheibe + Mutter/Einsatz automatisch per `insert_part` und
   `add_joint` in der Baugruppe platziert.
2. **Größenwechsel über `solid.thread`**:
   Ändert man an einem bereits erzeugten Normteil per `parameters.change` nur
   Längen- oder Außenmaße (`l`, `dk`, `k`, `s`), rechnet alles fehlerfrei nach.
   Ändert man dagegen den Gewindedurchmesser `d` (z. B. von `5 mm` auf `6 mm`),
   meldet das kosmetische `solid.thread`-Feature einen Fehler, weil seine
   `designation` (`M5x0.8`) fest eingetragen ist. Ohne `designation` würde
   SolidCraft bei Innenbohrungen auf Nenndurchmesser $d$ jedoch das nächstgrößere
   Gewinde raten (interpretiert $d = 5\text{ mm}$ als Kernloch für `M6`). Ein
   späteres `resize_standard_part`-Werkzeug sollte daher `designation` am
   `Thread`-Feature mitziehen.
3. **Weitere Reihen**:
   Kurzvarianten der Einschmelzgewinde (`M3x4,0`, `M4x4,0`), Senkschrauben
   (ISO 10642), Linsenkopfschrauben (ISO 7380) sowie Kugellager `608` und
   `6200`er-Reihe lassen sich im selben Tabellenschema ergänzen.
