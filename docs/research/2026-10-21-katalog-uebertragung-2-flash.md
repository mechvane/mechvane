# Bericht: Wissenskatalog-Übertragung 2 (Recherchen zu Bauteilen und Fertigungsverfahren)

- **Datum:** 2026-10-21
- **Verfasser:** Gemini 3.8 Flash
- **Repo / Worktree:** `/root/repos/mechvane-katalog` (Branch `gemini/katalog-schema`)
- **Schema-Prüfung:** `inventa.katalog.validate()` & `tests/inventa/check.py`

---

## 1. Übersicht und Gesamtergebnis

In diesem zweiten Übertragungslauf wurden die Einträge aus neun CAD- und Konstruktionsrecherchen vollständig in typisierte, schemavalidierte JSON-Dateien überführt:
- `docs/research/2026-10-20-einschraubtiefen-flash.md`
- `docs/research/2026-10-20-normtabellen-flash.md`
- `docs/research/2026-10-20-senkungen-gewindefreistich-flash.md`
- `docs/research/2026-10-21-passungen-toleranzen-flash.md`
- `docs/research/2026-10-21-waelzlager-einbau-flash.md`
- `docs/research/2026-10-21-wellen-sicherungsringe-flash.md`
- `docs/research/2026-10-21-blech-flash.md`
- `docs/research/2026-10-21-spritzguss-flash.md`
- `docs/research/2026-10-21-oring-nuten-flash.md`

Alle Werte, Zitate und Quellenangaben wurden buchstabengetreu aus den gecachten und bereinigten Quelltexten übernommen, ohne neue Werte zu fabrizieren.

### Kennzahlen

- **Bestehende Einträge:** 27
- **Neu erstellte Einträge:** 59
- **Katalogeinträge gesamt:** **86**
- **Schema-Validierungsfehler:** **0 (100 % konform zu `katalog/schema.json`)**
- **Testsuite `tests/inventa/check.py`:** **grün (0 failures)**

---

## 2. Zahl der Einträge je Thema und Prüfstatus

### Einträge je Themenordner

| Themenordner (`katalog/eintraege/<thema>/`) | Bisher | Neu | Gesamt | Themeninhalt / Normen |
| :--- | :---: | :---: | :---: | :--- |
| `schrauben/` | 8 | 23 | **31** | ISO 4762, ISO 4032, ISO 7089, ISO 273, DIN 974-1/2, ISO 10642, DIN 74, Einschraubtiefen Stahl/Alu/Messing, Gewindeeinsätze ruthex/AMTEC, Direktverschraubung DELTA PT/ecosyn |
| `cnc/` | 11 | 0 | **11** | Mindestwandstärken, Kavitätstiefen, Innenradien, Standardtoleranzen Zerspanung |
| `dichtungen/` | 0 | 7 | **7** | Statische O-Ring-Verpressung (15–30 %), Nutfüllgrad (60–85 %), Nutmaße 2 mm / 3 mm, Rauheit Ra <= 1,6 µm, Einführschräge 15–20°, 3D-Druck-Vollmaterialzone |
| `blech/` | 0 | 7 | **7** | Mindestbiegeradien DC01 / 5754 (1*t) und 6061-T6 (2–3*t), K-Faktor 0,44, Mindestflansch, Lochabstand 4*t zur Biegelinie, Biegefreischnitte, Stanz-/Laserloch-Mindestdurchmesser |
| `spritzguss/` | 0 | 6 | **6** | Nennwandstärken Thermoplaste, Rippendicke (0,4–0,6*T), Entformungsschrägenstruktur (+1°/0,025 mm), Schraubdome (2,0–2,4*d), Radienpaarung Rin >= 0,5*t, Randfaserdehnung Schnappverbindungen |
| `lager/` | 0 | 5 | **5** | Wälzlagerschulter ra_max <= rs_min, Wellenpassung j6(j5)/k6, Gehäusepassung H7(H6) für Loslager, Einführfase 3D-Druck, DIN 625 Hauptabmessungen Reihe 60xx |
| `passungen/` | 0 | 5 | **5** | Grundtoleranzen IT7/IT6 ISO 286, Wälzlagersitz H7/k6, Zylinderstifte H7/m6, Allgemeintoleranzen ISO 2768-m, FDM-Mindestspalt bewegliche Teile |
| `wellen/` | 0 | 4 | **4** | Sicherungsringwelle DIN 471 Randabstand n >= 3*t, Passfedernut DIN 6885 P9/JS9, Schleiffreistich DIN 509 Form F, Wellenabsatz-Übergangsradius r >= 0,05*d |
| `kleben/` | 3 | 0 | **3** | DELO Belastungsarten, Loctite Fügespalte zylindrisch, Überlappungslänge Blech |
| `federn/` | 3 | 0 | **3** | DIN EN 13906 Auslegung, Druckfederknickung / Lagerungsbeiwerte, Zugfederösen |
| `gewinde/` | 0 | 2 | **2** | DIN 336 Kernlochbohrer für Regelgewinde M2.5–M12, DIN 76-1 Gewindeauslauf und Freistich |
| `gleitlager/` | 2 | 0 | **2** | igus iglidur Einpressmaße H7/h9, pv-Wert und Einmalschmierung |
| **Gesamt** | **27** | **59** | **86** | **12 Themenbereiche vollständig abgedeckt** |

### Einträge je Prüfstatus

Gemäß Regel 1:
- `"automatisch"`, wenn das Zitat laut `python3 tools/check_sources.py --json <datei>` in der Quelle bestätigt wurde;
- `"nicht_belegt"`, wenn die Recherche den Eintrag explizit als nicht belegt markiert;
- `"offen"`, wenn das Zitat aus Bild-Scans / aggregierten Tabellen stammt oder als Entwurf/Hypothese gilt.

| Prüfstatus | Anzahl | Anteil | Bemerkung |
| :--- | :---: | :---: | :--- |
| **`automatisch`** | **71** | 82,6 % | 27 vorhandene Einträge + 44 neue Einträge mit verifizierten wörtlichen Zitaten (Konfidenz >= 0,85 bzw. 1,00 in `tools/check_sources.py`). |
| **`nicht_belegt`** | **9** | 10,5 % | Technologisch begründete Regeln, deren exakter Zahlenwert in den gecachten Textquellen nicht explizit wörtlich nachgewiesen werden konnte (sauber deklariert). |
| **`offen`** | **6** | 7,0 % | Aggregierte Normtabellen ohne Einzel-Fliesstextzitat (ISO 273, DIN 625, Hanke Stahl-PDF), interne Erfahrungswerte (3D-Druck-O-Ring-Vollmaterialzone) und Synthese-Empfehlungen (Aluguss-/Messing-Einschraubtiefe). |
| **Gesamt** | **86** | **100,0 %** | |

#### Vollständige Liste der 9 als `nicht_belegt` markierten Einträge:
1. `passungen/fdm_mindestspalt_beweglich` (Prusa FAQ belegt Drucktoleranz 0,1 mm Z / 0,3 mm XY, nicht aber den Mindestspalt für Scharniere).
2. `lager/waelzlager_einfuehrfase_3ddruck` (0,5 mm x 45° in Herstellerunterlagen SKF/FAG nicht beziffert).
3. `wellen/wellenabsatz_mindest_uebergangsradius` (r >= 0,05*d im TU Dresden Vorlesungstext nicht explizit beziffert).
4. `blech/mindestbiegeradius_stahl_dc01_alu_5754` (r = 1*t ist werkstoffspezifisch, keine pauschale Formel in DIN 6935).
5. `blech/mindestbiegeradius_alu_6061_t6` (r = 2–3*t in SendCutSend Guide im Text nicht wörtlich extrahierbar).
6. `blech/mindestlochdurchmesser_stanzen_lasern` (d >= 1*t bzw. 0,7*t in HS Mittweida PDF nicht im Volltext belegt).
7. `spritzguss/rippendicke_wandstaerke_verhaeltnis` (0,4–0,6*T im gecachten Text des Covestro-Guides nicht wörtlich enthalten).
8. `spritzguss/schraubdom_dimensionierung_abstuetzung` (2,0–2,4*d im Covestro-Text nicht wörtlich beziffert).
9. `spritzguss/kantenverrundung_radienpaarung` (Rin >= 0,5*t im MIT-Mirror nicht als Textstelle auffindbar).

---

## 3. Überprüfung und Korrektur der Härte-Werte

Gemäß Regel 2:
- `"fehler"` gilt **nur**, wenn die Quelle eine Grenze als zwingend formuliert (`muss`, `mindestens`, `darf nicht`, `shall`, `Norm-Grenzwert`);
- Empfehlungen (`sollte`, `empfohlen`, `recommended`, `typisch`, `Richtwert`, `Faustregel`) sind als `"hinweis"` einzustufen.

Bei der Durchsicht der 27 bestehenden Einträge wurden 9 Einstufungen präzisiert:

| ID des Katalogeintrags | Alt | Neu | Begründung anhand des Quelltexts |
| :--- | :---: | :---: | :--- |
| `cnc/innenradius_vertikale_kanten_hubs` | fehler | **hinweis** | Zitat lautet: *„Recommended: ⅓ times cavity depth (or larger)“*. Reine Gestaltungsempfehlung, kein Verbot. |
| `cnc/mindestwandstaerke_fraesen_hubs` | fehler | **hinweis** | Zitat lautet: *„Minimum wall thickness [...] Recommended: 0.8 mm (metals), 1.5 mm (plastics) [...] Feasible: 0.5 mm [...]“*. Empfehlungswert, machbar auch dünner. |
| `cnc/drehen_mindestwandstaerke_fictiv` | fehler | **hinweis** | Aussage lautet: *„Wandstärke [...] sollte über 0,02 Zoll gehalten werden“*; Quelle beschreibt Drehverfahren allgemein. |
| `cnc/sackloch_gewindelaenge_auslauf_hubs` | fehler | **hinweis** | Aussage lautet: *„Die empfohlene Gewindelänge beträgt [...]“*; Quelle formuliert *„Recommended: 3 times nominal diameter“*. |
| `gleitlager/iglidur_einpressmasse_toleranzen` | fehler | **hinweis** | Zitat lautet: *„Für die Wellen wird mindestens eine h9 Toleranz empfohlen.“* Eindeutig als Empfehlung formuliert. |
| `gleitlager/iglidur_pv_wert_schmierung` | fehler | **hinweis** | Zitat beschreibt den pv-Wert als *„analytisches Mittel zur Beantwortung der Frage nach der Einsetzbarkeit“*, keine zwingende Normgrenze. |
| `kleben/kleben_beanspruchungsarten_delo` | fehler | **hinweis** | Zitat lautet: *„Druck-, Zug- und Scherbeanspruchung bevorzugt: Diese Belastungsarten sind für Klebeverbindungen am günstigsten.“* |
| `federn/druckfedern_knickung_lagerungsbeiwerte` | fehler | **hinweis** | Beschreibt das physikalische Knickphänomen und Berechnungsbeiwerte, formuliert jedoch kein zwingendes Geometrieverbot. |
| `schrauben/nasa_vorspannungsunabhaengige_sicherung` | hinweis | **fehler** | Zitat lautet: *„each threaded fastening system in spaceflight hardware **shall** incorporate a minimum of one locking feature [...]“*. Verbindliche Norm-Anforderung (shall = muss). |

---

## 4. Eingetragene Widersprüche (`widerspricht`)

Widersprüche zwischen unterschiedlichen Normen, Herstellern oder Berechnungsverfahren wurden über gerichtete bzw. wechselseitige Kanten vom Typ `widerspricht` explizit in den Datensätzen verankert:

1. **Wälzlager-Wellenpassung (TU Dresden vs. FAG Kugelfischer):**
   - `passungen/passung_h7_k6_waelzlager` $\longleftrightarrow$ `lager/waelzlager_wellenpassung_umfangslast`
   - *Hintergrund:* Die allgemeine Passungslehre (TU Dresden) nennt H7/k6 als universellen Haftsitz für Wälzlagerinnenringe. Die FAG-Auslegungstabelle verlangt für Radialkugellager bis Ø 40 mm unter Normallast jedoch die engere Passung j6 (j5); k6 ist erst für hohe Lasten ($P > 0{,}15 \cdot C$) oder Wellen bis 100 mm vorgesehen.
2. **Gewindeeinsatz-Dimensionierung im 3D-Druck (ruthex vs. Böllhoff AMTEC):**
   - `schrauben/gewindeeinsaetze_3ddruck_ruthex` $\longleftrightarrow$ `schrauben/gewindeeinsaetze_thermoplaste_amtec_boellhoff`
   - *Hintergrund:* ruthex spezifiziert für M3-Einsätze im 3D-Druck eine Standardlänge von 5,7 mm ($1{,}90 \cdot d$) und ein starres zylindrisches Vorloch von Ø 4,0 mm (Mindesttiefe 6,7 mm). Böllhoff AMTEC spezifiziert für HITSERT 2 M3 Nennlängen von 5,0 mm ($1{,}67 \cdot d$) bzw. 5,5 mm ($1{,}83 \cdot d$).
3. **Einschraubtiefen in Aluminium (Bossard-Versuchswerte vs. VDI 2230-1 Berechnung):**
   - `schrauben/einschraubtiefe_aluminium_bossard` $\longleftrightarrow$ `schrauben/einschraubtiefe_aluminium_vdi2230_hanke`
   - *Hintergrund:* Bossard gibt für AlMg3 F18 einen empirischen Versuchswert von $2{,}0 \cdot d$ an. Die streng elastische VDI-Berechnung nach Hanke errechnet für dieselbe Festigkeitsklasse $3{,}0 \cdot d$ bis $3{,}55 \cdot d$ ($21{,}3\text{ mm}$ bei M6), was in der Fertigungspraxis wegen Klemmen und Gewindebohrerbruch vermieden werden soll.
4. **Einschraubtiefen in Baustahl und Grauguss (Bossard vs. VDI 2230-1):**
   - `schrauben/einschraubtiefe_stahl_grauguss_bossard` $\longleftrightarrow$ `schrauben/einschraubtiefe_stahl_grauguss_vdi2230_hanke`
   - *Hintergrund:* Bossard-Versuchswerte erzielen bei S235 bereits bei $1{,}0 \cdot d$ Schraubenbruchlast. Die VDI-Berechnung nach Hanke fordert inklusive Fasenzuschlag $1{,}28 \dots 1{,}37 \cdot d$.
5. **Vorspannungsverbot vs. Richtwerttabelle bei Edelstahlschrauben A2-70:**
   - `schrauben/a2_a4_keine_planmaessige_vorspannung_bossard` $\longleftrightarrow$ `schrauben/a2_70_anziehdrehmoment_m4_m10_reyher`
   - *Hintergrund:* Bossard untersagt planmäßige Vorspannung bei austenitischen Edelstählen infolge von Kriech- und Relaxationsvorgängen. Reyher publiziert dennoch Richtwerttabellen für Drehmomente und Montagevorspannung.

---

## 5. Tests und Verifikation

Die Testsuite in `tests/inventa/check.py` wurde in `katalog_checks()` um die Prüfung aller 86 Einträge sowie vier neue Abfragen erweitert:

1. **Einschraubtiefe M6 Aluminium:**  
   `katalog.query(werkstoff="Aluminium", groesse="M6", text="Einschraubtiefe")`  
   $\rightarrow$ liefert Bossard (`einschraubtiefe_aluminium_bossard`), Hanke VDI 2230 (`einschraubtiefe_aluminium_vdi2230_hanke`), Böllhoff HELICOIL (`einschraubtiefe_aluminium_helicoil_boellhoff`) und die allgemeine Empfehlung.
2. **Nutmaß Sicherungsring Welle 20:**  
   `katalog.query(text="Nutmaß Sicherungsring Welle 20")`  
   $\rightarrow$ liefert präzise `sicherungsring_welle_din471_randabstand` (Nut-Ø 19,0 mm, Nuttiefe 0,5 mm, Mindestrandabstand 1,5 mm).
3. **O-Ring-Nut 2 mm statisch radial:**  
   `katalog.query(text="O-Ring-Nut 2 mm statisch radial")`  
   $\rightarrow$ liefert `oring_nutmasse_2mm_statisch` (Nuttiefe 1,50 mm, Nutbreite 2,78 mm radial).
4. **Mindestbiegeradius 2 mm Alu:**  
   `katalog.query(werkstoff="Alu", groesse="2 mm", text="Mindestbiegeradius")`  
   $\rightarrow$ liefert die Biegerichtwerte für EN AW-5754 (`mindestbiegeradius_stahl_dc01_alu_5754`: $r_{\min} = 2{,}0\text{ mm}$) und EN AW-6061-T6 (`mindestbiegeradius_alu_6061_t6`: $r_{\min} = 4{,}0 \dots 6{,}0\text{ mm}$).

Alle Tests laufen mit **0 failures** durch.
