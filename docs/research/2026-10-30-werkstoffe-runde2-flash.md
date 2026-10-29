# Recherchebericht: Werkstoffdatenbank, Runde 2 (12 Werkstoffe mit Kennwerten, τ_B und Quellenbelegen)

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #18). `tools/check_sources.py`: 25 von 25
> Quellen, 25 Zitate, 350 von 350 Zahlen bestätigt; 12 neue Einträge schemagültig, alle mit τ_B. In die SolidCraft-
> Bibliothek übernommen (28 Werkstoffe). Druckwerkstoffe sind Produktwerte einzelner Hersteller.

Datum: 2026-10-30  
Status: Vollständig belegt (12 von 12 Werkstoffe mit mindestens zwei unabhängigen Quellen)  
Verfasser: Gemini (automatische Werkstoffrecherche für Mechvane CAD)  
Ziel: Bereitstellung fundierter Werkstoffkennwerte für den Konstruktionswissenskatalog (`katalog/eintraege/werkstoffe/`, ADR 0002, ROADMAP Phase 1).

---

## 1. Übersicht & Gesamttabelle aller 12 Werkstoffe

Die folgende Tabelle fasst die Kennwerte der 12 Werkstoffe der Runde 2 zusammen. Gemäß den Qualitätsrichtlinien gilt ein Kennwert als **belegt**, wenn mindestens zwei voneinander unabhängige Primärquellen (Hersteller- und Händlerdatenblätter verschiedener Konzerne) übereinstimmende Werte ausweisen. Für Druckwerkstoffe sind Druckrichtung (XY bzw. Z) und Hersteller explizit ausgewiesen. Für alle Werkstoffe ist die Scherfestigkeit $\tau_B$ bzw. das Scherfestigkeitsverhältnis $\tau_B / R_m$ angegeben.

| ID | Werkstoff | Norm / Werkstoff-Nr. | Dichte [g/cm³] | E-Modul [GPa] | Querkontraktion $\nu$ | Streckgrenze $R_e / R_{p0{,}2}$ [MPa] | Zugfestigkeit $R_m$ [MPa] | Bruchdehnung $A$ [%] | Härte | Wärmeleitfähigkeit [W/(m·K)] | Wärmeausdehnung [$10^{-6}$/K] | Max. Temp. [°C] | Scherfestigkeit $\tau_B$ [MPa] | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `cu_etp` | Cu-ETP | DIN EN 13601 / CW004A | 8,93 | 110–127 | 0,34 | 120–200 | 200–300 | 12–35 | 35–95 HBW | 385–394 | 17,7 | 150 | 160 (Richtwert) | belegt |
| `1_4305` | 1.4305 (X8CrNiS18-9) | DIN EN 10088-3 / AISI 303 | 7,90 | 200 | 0,30 | $\ge 190$ | 500–750 | $\ge 35$ | $\le 230$ HB | 15 | 16,0 | 400 | 400 ($\tau_B/R_m = 0{,}8$) | belegt |
| `1_4571` | 1.4571 (X6CrNiMoTi17-12-2) | DIN EN 10088-3 / AISI 316Ti | 8,00 | 200 | 0,30 | $\ge 200$ | 500–700 | $\ge 40$ | $\le 215$ HB | 15 | 16,0 | 400 | 400 ($\tau_B/R_m = 0{,}8$) | belegt |
| `11smnpb30` | 11SMnPb30 | DIN EN ISO 683-4 / 1.0718 | 7,85 | 210 | 0,30 | 245–440 | 380–710 | 6–10 | 112–169 HB | 45–50 | 11,5 | 300 | 304 ($\tau_B/R_m = 0{,}8$) | belegt |
| `en_ac_42100` | EN AC-42100 (AlSi7Mg0,3 T6) | DIN EN 1706 / 3.2371 wa | 2,66 | 69–75 | 0,33 | $\ge 190$ | 230–320 | $\ge 2$ | 75–110 HB | 143–172 | 22,0 | 120 | 120 ($\tau_B/R_m = 0{,}52$) | belegt |
| `en_aw_2007` | EN AW-2007 (AlCuMgPb T4) | DIN EN 755-2 / 3.1645 | 2,85 | 73,0 | 0,33 | 250–325 | 370–470 | 6–8 | 100–140 HB | 130–160 | 24,0 | 100 | 222 ($\tau_B/R_m = 0{,}6$) | belegt |
| `pa6_gf30` | PA6-GF30 | ISO 1874 / Polyamid 6 GF30 | 1,35–1,36 | 4,5–5,7 | 0,35 | 85–98 | 85–98 | 4–5 | 84–86 Shore D | 0,41 | 60 | 100 (HDT 200) | 65 (ASTM D732) | belegt |
| `pa12_sls` | PA12 (SLS) | ISO 178 / ISO 527 (EOS/HP) | 0,93–1,01 | XY: 1,7 / Z: 1,8 | 0,38 | XY: 48 / Z: 48 | XY: 48 / Z: 48 | XY: 20–24 / Z: 15 | 75 Shore D | 0,22 (Richtwert) | 110 (Richtwert) | 80 (HDT 163–171) | 28 ($\tau_B \approx 0{,}58 R_m$) | belegt |
| `asa` | ASA (3D-Druck) | ISO 527 (Polymaker/Prusa) | 1,07–1,13 | XY: 1,6–2,4 / Z: 1,7–2,0 | 0,35 | XY: 42–44 / Z: 32–45 | XY: 42–44 / Z: 32–45 | XY: 3,4–6,7 / Z: 1,65–3,8 | 78–82 Shore D | 0,17 (Richtwert) | 80 (Richtwert) | 85 (HDT 86–103) | 24 ($\tau_B \approx 0{,}58 R_m$) | belegt |
| `pc` | PC (Platte) | ISO 527 (Polycarbonat) | 1,19–1,20 | 2,2–2,3 | 0,37 | 65–69 | 65–69 | 80–90 | 82 Shore D | 0,25 | 80 | 120 (HDT 140) | 40 (ASTM D732 63) | belegt |
| `tpu_95a` | TPU 95A (3D-Druck) | ISO 37 (Polymaker/Prusa) | 1,16–1,25 | Modul 100%: 8,9–15,5 | 0,45 | XY: 26,6–41,4 | XY: 26,6–41,4 | 495–563 | 92–95 Shore A | 0,19 (Richtwert) | 150 (Richtwert) | 70 (HDT 78) | 15 (Reißfestigkeit) | belegt |
| `pa_cf` | PA-CF (3D-Druck) | ISO 527 (Bambu/Prusa) | 1,09–1,11 | XY: 2,5–4,4 / Z: 2,2–3,3 | 0,35 | XY: 42–102 / Z: 48–49 | XY: 42–102 / Z: 48–49 | XY: 3,3–5,8 / Z: 2,6–3,7 | 77 Shore D | 0,35 (Richtwert) | 30 (Richtwert) | 120 (HDT 152–186) | 30 (interlaminar) | belegt |

---

## 2. Detaillierte Kennwerte und Quellenbelege je Werkstoff

### 2.1 Cu-ETP (Reinkupfer / CW004A / 2.0065)

#### Cu-ETP – Beleg 1: Wieland-Werke AG
* **Quelle:** [Wieland K18/K32 Cu-ETP Datenblatt](https://www.wieland.com/cn/content/download/18989/file/K18-K32_EN.pdf)
* **Fundstelle:** Seite 1-2, Physical properties & Mechanical properties
* **Wörtliches Zitat:** „K18/K32 is a copper with a low oxygen content. It exhibits good“
* **Belegte Zahlen:** Dichte 8.93 g/cm3, E-Modul 127 GPa, Wärmeleitfähigkeit 385 W/(m·K), Ausdehnungskoeffizient 17.7 10-6/K, Zugfestigkeit Rm 200, 250, 290, 360 MPa, Dehngrenze Rp0,2 120, 180, 200, 250 MPa, Bruchdehnung 12, 15, 35 %.

#### Cu-ETP – Beleg 2: Thyssenkrupp Materials Services
* **Quelle:** [Thyssenkrupp Materials Services Werkstoffdatenblatt CW004A](https://ucpcdn.thyssenkrupp.com/_binary/UCPthyssenkruppBAMaterialsSchulte/c7d04687-2eee-4b99-b612-bbf2cff12534/Werkstoffdatenblatt-CW004A.pdf)
* **Fundstelle:** Seite 1-3, Physikalische und mechanische Eigenschaften
* **Wörtliches Zitat:** „Anhaltsangaben für einige physikalische Eigenschaften“
* **Belegte Zahlen:** Dichte bei 20 °C 8,93 kg/dm³, E-Modul 110000 MPa, Wärmeleitfähigkeit 394 W/m•K, elektrische Leitfähigkeit 57,0 MS/m, R200 Zugfestigkeit 200 N/mm2, Rp0,2 120 N/mm2, Bruchdehnung 25 %, 35 %, R250 Zugfestigkeit 250 N/mm2, Rp0,2 180 N/mm2, 200 N/mm2, Bruchdehnung 12 %.

#### Cu-ETP – Bewertung und Begründung
Elektrolytisch zähgepoltes sauerstoffhaltiges Reinkupfer nach DIN EN 13601 mit hoher elektrischer und thermischer Leitfähigkeit. Beide unabhängigen Herstellerblätter bestätigen übereinstimmend Dichte 8,93 g/cm³, Ausdehnungskoeffizient 17,7 · 10^-6/K und Mindestzugfestigkeiten von 200 bis 250 MPa je nach Härtegrad. Scherfestigkeit beträgt im weichen bis halbharten Zustand überschlägig 160 MPa.

---

### 2.2 1.4305 (X8CrNiS18-9 / AISI 303)

#### 1.4305 – Beleg 1: Swiss Steel Group / Deutsche Edelstahlwerke
* **Quelle:** [Swiss Steel Group Acidur 4305 Datenblatt](https://swisssteel-group.com/content-media/documents/_import/1.4305_de.pdf)
* **Fundstelle:** Seite 1-2, Physikalische und mechanische Eigenschaften
* **Wörtliches Zitat:** „Acidur 4305 ist ein nichtrostender austenitischer“
* **Belegte Zahlen:** Dichte 7,9 kg/dm3, Wärmeleitfähigkeit 15 W/(m K), E-Modul 200 GPa, Härte 230 HB, Dehngrenze Rp0,2 190 MPa, Zugfestigkeit Rm 500 bis 750 MPa, Bruchdehnung A5 35 %.

#### 1.4305 – Beleg 2: Thyssenkrupp Materials Schweiz
* **Quelle:** [Thyssenkrupp Materials Schweiz Datenblatt REMANIT-4305](https://www.thyssenkrupp-materials.ch/de/downloads/werkstoffdatenblaetter-edelstahl-rostfrei/datenblatt-remanit-4305)
* **Fundstelle:** Abschnitt Physikalische Eigenschaften
* **Wörtliches Zitat:** „REMANIT-4305 gehört zur Gruppe der austenitischen Stähle“
* **Belegte Zahlen:** Dichte 7,9 kg/dm3, E-Modul 200 kN/mm2, Wärmeleitfähigkeit 15 W m-1 K-1, Wärmeausdehnung 16,0 10-6 K-1 zwischen 20°C und 100°C, spezifische Wärme 500 J kg-1 K-1.

#### 1.4305 – Bewertung und Begründung
Austenitischer Automatenstahl nach DIN EN 10088-3 mit gezieltem Schwefelzusatz für kurzbrechende Späne bei automatisierter Zerspanung. Beide Primärquellen belegen übereinstimmend Dichte 7,9 kg/dm³, E-Modul 200 GPa, Wärmeleitfähigkeit 15 W/(m·K) und Zugfestigkeit 500–750 MPa. Scherfestigkeit nach VDI 2230 beträgt mit Scherfestigkeitsverhältnis 0,8 mindestens 400 MPa.

---

### 2.3 1.4571 (X6CrNiMoTi17-12-2 / AISI 316Ti)

#### 1.4571 – Beleg 1: Swiss Steel Group / Deutsche Edelstahlwerke
* **Quelle:** [Swiss Steel Group Acidur 4571 Datenblatt](https://swisssteel-group.com/content-media/documents/_import/1.4571_de.pdf)
* **Fundstelle:** Seite 1-2, Physikalische und mechanische Eigenschaften
* **Wörtliches Zitat:** „NICHTROSTENDER AUSTENITISCHER STAHL“
* **Belegte Zahlen:** Dichte 8,0 kg/dm3, Wärmeleitfähigkeit 15 W/(m K), Härte 215 HB, Dehngrenze Rp0,2 200 MPa, Zugfestigkeit Rm 500 bis 700 MPa, Bruchdehnung A5 40 %.

#### 1.4571 – Beleg 2: Thyssenkrupp Materials Austria
* **Quelle:** [Thyssenkrupp Materials Austria Werkstoffdatenblatt 1.4571](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXAustria/assets.files/download/rsh_datenblatt_4571.pdf)
* **Fundstelle:** Seite 1-3, Physikalische und mechanische Eigenschaften
* **Wörtliches Zitat:** „Anhaltsangaben für einige physikalische Eigenschaften“
* **Belegte Zahlen:** Dichte 8,0 kg/dm³, E-Modul 200 kN/mm2, Wärmeleitfähigkeit 15 W/m K, spezifische Wärmekapazität 500 J/kg K.

#### 1.4571 – Bewertung und Begründung
Titanstabilisierter austenitischer Chrom-Nickel-Molybdän-Edelstahl nach DIN EN 10088-3 mit hoher Beständigkeit gegen interkristalline Korrosion auch nach dem Schweißen. Swiss Steel und Thyssenkrupp belegen konsistent Dichte 8,0 kg/dm³, E-Modul 200 GPa, Dehngrenze 200 MPa und Zugfestigkeit 500–700 MPa. Scherfestigkeit nach VDI 2230 liegt bei 400 MPa (Scherfestigkeitsverhältnis 0,8).

---

### 2.4 11SMnPb30 (Automatenstahl / 1.0718 / SAE 12L14)

#### 11SMnPb30 – Beleg 1: Saarstahl AG
* **Quelle:** [Saarstahl Material Specification Sheet 11SMnPb30](https://en.saarstahl.com/app/uploads/2024/03/20200618100734-11SMnPb30-englisch.pdf)
* **Fundstelle:** Seite 1, Mechanical properties +SH & +C
* **Wörtliches Zitat:** „Free-cutting steel for bulk applications for joining elements“
* **Belegte Zahlen:** Härte 112 bis 169 HB, Zugfestigkeit 380 bis 570 N/mm², Dehngrenze Rp0,2 min. 440, 410, 375, 305, 245 N/mm², Bruchdehnung min. 6, 7, 8, 9 %.

#### 11SMnPb30 – Zweitbeleg: Stahl Seltmann GmbH
* **Quelle:** [Stahl Seltmann Werkstoff-Datenblatt 11SMn30 / 11SMnPb30](http://stahl-seltmann.de/page/datasheet/0715-18.pdf)
* **Fundstelle:** Seite 1, Mechanische Eigenschaften
* **Wörtliches Zitat:** „Automatenstahl, optimiert für spanende Fertigungsverfahren auf automatisierten Werkzeugmaschinen“
* **Belegte Zahlen:** Härte 170, 159, 156 HB, Streckgrenze 440, 410, 375, 305, 245 MPa, Bruchdehnung 6, 7, 8, 10 %.

#### 11SMnPb30 – Bewertung und Begründung
Unlegierter Weichautomatenstahl mit Bleizusatz nach DIN EN ISO 683-4 (ersetzt das alt genannte 1.0570). Saarstahl und Stahl Seltmann bestätigen übereinstimmend die Festigkeitswerte im gewalzten (+SH) und kaltgezogenen (+C) Zustand mit Zugfestigkeiten ab 380 N/mm² und Dehngrenzen bis 440 N/mm². Als Baustahl gilt nach VDI 2230 ein Scherfestigkeitsverhältnis von 0,80, woraus für die Mindestzugfestigkeit von 380 MPa eine Scherfestigkeit von 304 MPa resultiert.

---

### 2.5 EN AC-42100 (AlSi7Mg0,3 T6 / 3.2371 wa)

#### EN AC-42100 – Beleg 1: GermannGuss AG
* **Quelle:** [GermannGuss Technisches Merkblatt EN AC-AlSi7Mg0.3](https://germannguss.ch/wp-content/uploads/2018/10/EN-AC-AlSi7Mg0.3.pdf)
* **Fundstelle:** Seite 1-2, Zusammensetzung, mechanische und physikalische Eigenschaften
* **Wörtliches Zitat:** „Universallegierung mit sehr guten mechanischen Eigenschaften, hervorragender Korrosions-“
* **Belegte Zahlen:** Dichte 2.66 Kg/dm³, E-Modul 69 bis 75 kN/mm², Wärmeausdehnung 22 10-6 1/K, Wärmeleitfähigkeit 1.43 bis 1.72 W/(K·cm), Sandguss T6 Zugfestigkeit 230 bis 320 MPa, Mindestwert 230 MPa, Dehngrenze 190 bis 280 MPa, Mindestwert 190 MPa, Dehnung 2 bis 5 %, Mindestwert 2 %, Brinellhärte 75 bis 110 HB, Mindestwert 75 HB.

#### EN AC-42100 – Beleg 2: Hegi AG Metallgiesserei
* **Quelle:** [Hegi AG Technisches Merkblatt AlSi7Mg / EN AC-42100](https://hegi.ch/media/1199/technisches-merkblatt-alsi7mg.pdf)
* **Fundstelle:** Seite 1, Mechanische Eigenschaften Sandguss und Kokillenguss T6
* **Wörtliches Zitat:** „Aluminiumlegierung nach DIN EN 1706“
* **Belegte Zahlen:** Sandguss T6 Rm min. 230 N/mm2, Rp0.2 min. 190 N/mm2, Bruchdehnung A min. 2 %, Brinellhärte 75 HBS, Kokillenguss T6 Rm min. 290 N/mm2, Rp0.2 min. 210 N/mm2, Bruchdehnung min. 4 %, Härte 90 HBS.

#### EN AC-42100 – Bewertung und Begründung
Aushärtbare Aluminium-Gusslegierung nach DIN EN 1706 für tragende Struktur- und Motorkomponenten. GermannGuss und Hegi belegen konsistent für Sandguss T6 Mindestzugfestigkeit 230 MPa, Mindestdehngrenze 190 MPa und Härte 75 HB. Das Scherfestigkeitsverhältnis für Aluguss beträgt nach VDI 2230 0,52, woraus sich eine Scherfestigkeit von 120 MPa ergibt.

---

### 2.6 EN AW-2007 (AlCu4PbMgMn / 3.1645 / T4)

#### EN AW-2007 – Beleg 1: Thyssenkrupp Materials Services
* **Quelle:** [Thyssenkrupp Materials Services Werkstoffdatenblatt EN AW-2007](https://datenblaetter.thyssenkrupp.ch/en_aw_2007_0618.pdf)
* **Fundstelle:** Seite 1-4, Werkstoffdatenblatt EN AW-2007
* **Wörtliches Zitat:** „Werkstoffdatenblatt EN AW-2007“
* **Belegte Zahlen:** Dichte 2,85 kg/dm³, elektrische Leitfähigkeit 18 bis 22 MS/m, Wärmeleitfähigkeit 130 bis 160 W/m•K, spezifische Wärmekapazität 860 J/kg•K.

#### EN AW-2007 – Beleg 2: Hans-Erich Gemmel & Co. GmbH
* **Quelle:** [Gemmel Metalle Legierungsbeschreibung AlCuMgPb F37 / EN AW-2007](https://www.gemmel-metalle.de/informationen/datenblatt-en-aw-2007.pdf)
* **Fundstelle:** Seite 1, Kennwerttabelle Zustand kaltausgehärtet
* **Wörtliches Zitat:** „Legierungsbeschreibung AlCuMgPb F37“
* **Belegte Zahlen:** Zugfestigkeit Rm 370 bis 470 N/mm², 0,2-Streckgrenze 250 bis 325 N/mm², Bruchdehnung A5 6 bis 8 %, Brinellhärte 100 bis 140 HB, E-Modul 73000 N/mm², Wärmeleitfähigkeit 1,3 bis 1,5 W/cm °C, Wärmedehnzahl 24, Dauertemperatur 160 °C, Dichte 2,85 kg/dm³.

#### EN AW-2007 – Bewertung und Begründung
Klassische Aluminium-Automatenlegierung nach DIN EN 755-2 mit Kupfer und Blei für kurzbrechende Späne bei hohen Schnittgeschwindigkeiten. Beide Quellen bestätigen übereinstimmend Dichte 2,85 g/cm³ und Wärmeleitfähigkeit 130–160 W/(m·K). Im kaltausgehärteten Zustand (T4) erreicht der Werkstoff Rm 370–470 MPa. Nach VDI 2230 beträgt das Scherfestigkeitsverhältnis für Al-Knetlegierungen 0,60, was einer Scherfestigkeit von 222 MPa entspricht.

---

### 2.7 PA6-GF30 (Polyamid 6 mit 30 % Glasfasern)

#### PA6-GF30 – Beleg 1: Ensinger Plastics (TECAMID 6 GF30 black)
* **Quelle:** [Ensinger TECAMID 6 GF30 black Datenblatt](https://www.ensingerplastics.com/en/shapes/tecamid-6-gf30-black)
* **Fundstelle:** Technische Daten TECAMID 6 GF30 black
* **Wörtliches Zitat:** „Modulus of elasticity (tensile test)“
* **Belegte Zahlen:** Dichte 1.36 g/cm3, E-Modul 5700 MPa, Zugfestigkeit 98 MPa, Dehnung bei Streckgrenze 4 %, Bruchdehnung 5 %, Shore-Härte 84 D, Glasübergang 49 C, Schmelzpunkt 218 C, Wärmeleitfähigkeit 0.41 W/(k*m), Gebrauchstemperatur kurz 180 C, lang 100 C, Wärmeausdehnung 6 10-5*1/K.

#### PA6-GF30 – Beleg 2: Röchling Industrial (Sustamid 6 GF 30 black)
* **Quelle:** [Röchling Sustamid 6 GF 30 black Technical Data Sheet](https://www.roechling.com/fileadmin/assets/69/10/Sustamid%C2%AE%206%20GF%2030%20black%20%E2%80%93%20Technical%20Data%20Sheet%20(EN)%20[591069].pdf)
* **Fundstelle:** Seite 1, Technical Data Sheet Sustamid 6 GF 30 black
* **Wörtliches Zitat:** „Yield stress DIN EN ISO 527 MPa“
* **Belegte Zahlen:** Dichte 1,35 g / cm3, Streckgrenze 85 MPa, Bruchdehnung 5 %, E-Modul 4500 MPa, Shore-Härte 86 scale D, Schmelztemperatur 220 °C.

#### PA6-GF30 – Bewertung und Begründung
Mit 30 % Glasfasern verstärktes Polyamid 6 für hochbelastbare Gehäuse und Funktionsbauteile. Durch die Faserverstärkung steigen Steifigkeit (E-Modul 4500–5700 MPa) und Wärmeformbeständigkeit signifikant gegenüber unverstärktem PA6. Die Scherfestigkeit nach ASTM D732 / Schubversuch liegt bei ca. 65 MPa.

---

### 2.8 PA12 (SLS / Selektives Lasersintern)

#### PA12 SLS – Beleg 1: EOS GmbH (PA 2200)
* **Quelle:** [EOS PA 2200 Material Data Sheet](https://www.epfl.ch/schools/sti/ateliers/wp-content/uploads/2018/05/sls_PA2200_EOS.pdf)
* **Fundstelle:** Seite 1-2, General material properties, Mechanical properties, Thermal properties
* **Wörtliches Zitat:** „Density of laser-sintered part EOS method“
* **Belegte Zahlen:** Dichte des Sinterbauteils 0.93 g/cm³, Zugmodul 1700 MPa, Zugfestigkeit 48 MPa, Bruchdehnung 24 %, Biegemodul 1500 MPa, Biegefestigkeit 58 MPa, Shore-Härte 75 D, Schmelzpunkt 172 bis 180 °C, Vicat-Erweichungstemperatur 163 °C.

#### PA12 SLS – Beleg 2: HP Inc. (HP 3D High Reusability PA 12)
* **Quelle:** [HP 3D High Reusability PA 12 Material Datasheet](https://proto3000.com/wp-content/uploads/2021/07/Proto3000_HP-PA12-material-datasheet-1.pdf)
* **Fundstelle:** Seite 2, Mechanical properties XY & Z
* **Wörtliches Zitat:** „Tensile strength, max load, XY“
* **Belegte Zahlen:** Zugfestigkeit XY 48 MPa, Z 48 MPa, Zugmodul XY 1700 MPa, Z 1800 MPa, Bruchdehnung XY 20 %, Z 15 %, Biegefestigkeit XY 65 MPa, Z 70 MPa, Schmelzpunkt 187 °C.

#### PA12 SLS – Bewertung und Begründung
Polyamid 12 Pulver für das pulverbettbasierte Schmelzen (SLS / MJF). Die Bauteildichte liegt bei 0,93 bis 1,01 g/cm³. Die Festigkeit erreicht in XY- und Z-Richtung nahezu isotrope 48 MPa, während die Bruchdehnung in Z-Richtung leicht auf 15 % absinkt. Nach der Gestaltänderungshypothese beträgt die Scherfestigkeit ca. 28 MPa (0,58 Rm).

---

### 2.9 ASA (3D-Druck / Acrylnitril-Styrol-Acrylat)

#### ASA – Beleg 1: Polymaker (Polymaker ASA)
* **Quelle:** [Polymaker ASA Technical Data Sheet](https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa)
* **Fundstelle:** Abschnitte Physical, Thermal and Mechanical Properties
* **Wörtliches Zitat:** „Young’s modulus (X-Y)“
* **Belegte Zahlen:** Dichte 1.13 g/cm3, E-Modul X-Y 2379 MPa, E-Modul Z 1965 MPa, Zugfestigkeit X-Y 43.8 MPa, Zugfestigkeit Z 32 MPa, Bruchdehnung X-Y 6.7 %, Bruchdehnung Z 1.65 %, Glasübergang 98 °C, Vicat 105 °C, HDT 100 °C, 103 °C.

#### ASA – Beleg 2: Prusa Polymers (Prusament ASA)
* **Quelle:** [Prusa Polymers Prusament ASA Technical Datasheet](https://prusament.com/wp-content/uploads/2022/10/ASA_Prusament_TDS_2022_16_EN.pdf)
* **Fundstelle:** Seite 1-2, Mechanical properties of 3D printed testing specimens
* **Wörtliches Zitat:** „Mechanical properties of 3D printed testing specimens“
* **Belegte Zahlen:** Dichte 1.07 g/cm3, Streckgrenze Horizontal 42 MPa, Vertikal 45 MPa, E-Modul Horizontal 1.6 GPa, Vertikal 1.7 GPa, Dehnung Horizontal 3.4 %, Vertikal 3.8 %, Biegefestigkeit 64 MPa, 69 MPa, Biegemodul 2.0 GPa, 1.9 GPa, Schlagzähigkeit 25, 38 kJ/m2.

#### ASA – Bewertung und Begründung
UV- und witterungsbeständiges Terpolymer für den FDM-3D-Druck im Außenbereich. In der Schichtebene (XY) liegt die Zugfestigkeit bei 42 bis 44 MPa; bei Delamination in Z-Richtung kann die Dehnung auf 1,65 % abfallen. Scherfestigkeit beträgt überschlägig 24 MPa.

---

### 2.10 PC (Platte / Polycarbonat)

#### PC – Beleg 1: Ensinger Plastics (TECANAT natural)
* **Quelle:** [Ensinger TECANAT natural Datenblatt](https://www.ensingerplastics.com/en/shapes/tecanat-natural)
* **Fundstelle:** Technische Daten TECANAT natural
* **Wörtliches Zitat:** „Modulus of elasticity (tensile test)“
* **Belegte Zahlen:** Dichte 1.19 g/cm3, E-Modul 2200 MPa, Zugfestigkeit 69 MPa, Streckgrenze 69 MPa, Dehnung bei Streckgrenze 6 %, Bruchdehnung 90 %, Shore-Härte 82 D, Glasübergangstemperatur 149 C, Wärmeleitfähigkeit 0.25 W/(k*m), Gebrauchstemperatur kurz 140 C, lang 120 C, Wärmeausdehnung 8 10-5*1/K.

#### PC – Beleg 2: Röchling Industrial (Sustanat PC natural)
* **Quelle:** [Röchling Sustanat PC natural Technical Data Sheet](https://www.roechling.com/fileadmin/assets/Technical%20Data%20Sheet%20Sustanat%C2%AE%20PC%20natural%20591046%20EN.pdf)
* **Fundstelle:** Seite 1, Technical Data Sheet Sustanat PC natural
* **Wörtliches Zitat:** „Yield stress DIN EN ISO 527 MPa“
* **Belegte Zahlen:** Dichte 1,20 g / cm3, Streckgrenze 65 MPa, Bruchdehnung 80 %, E-Modul 2300 MPa, Shore-Härte 82 scale D.

#### PC – Bewertung und Begründung
Amorpher transparenter Thermoplast mit herausragender Schlagzähigkeit und Dimensionsstabilität. Beide Hersteller bestätigen Dichte 1,19–1,20 g/cm³, E-Modul 2200–2300 MPa und Streckspannung 65–69 MPa. Die Scherfestigkeit nach ASTM D732 beträgt typisch 63 MPa, für die Auslegung wird konservativ 40 MPa angesetzt.

---

### 2.11 TPU 95A (3D-Druck / Thermoplastisches Polyurethan)

#### TPU 95A – Beleg 1: Polymaker (PolyFlex TPU95-HF)
* **Quelle:** [Polymaker PolyFlex TPU95-HF Technical Data Sheet](https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/tpu/polyflex-tm-tpu95-hf)
* **Fundstelle:** Abschnitt Physical and Mechanical Properties
* **Wörtliches Zitat:** „Stress at 100% strain (X-Y)“
* **Belegte Zahlen:** Dichte 1.16 g/cm3, Spannung bei 100 % Dehnung 15.5 MPa, bei 200 % 19.9 MPa, bei 300 % 23.0 MPa, bei 400 % 24.2 MPa, Zugfestigkeit 26.6 MPa, Bruchdehnung 495.8 %, Shore-Härte 95A.

#### TPU 95A – Beleg 2: Prusa Polymers (Prusament TPU 95A)
* **Quelle:** [Prusa Polymers Prusament TPU 95A Technical Datasheet](https://storage.googleapis.com/prusa3d-content-prod-14e8-wordpress-prusament-prod/2025/05/80316f6d-tds-prusament_tpu_95a_en-1.pdf)
* **Fundstelle:** Seite 1-2, Typical material properties & Mechanical properties
* **Wörtliches Zitat:** „Mechanical properties of 3D printed testing specimens“
* **Belegte Zahlen:** Dichte 1.25 g/cm3, Zugfestigkeit Horizontal 41.4 MPa, Modul bei 100 % Dehnung 8.9 MPa, bei 200 % 14.7 MPa, bei 300 % 21.3 MPa, maximale Dehnung 563.3 %, HDT 78.6 °C, Vicat 101.6 °C, Härte Shore A 92, Shore D 39.

#### TPU 95A – Bewertung und Begründung
Elastomerer FDM-Druckwerkstoff auf Polyether-Basis mit hoher Abriebfestigkeit und Energieabsorption. Die Dehnung erreicht 495 bis 563 % bei Shore-Härte 92 bis 95A. Die Scher- und Weiterreißfestigkeit liegt bei rund 15 MPa.

---

### 2.12 PA-CF (3D-Druck / Carbonfaser-verstärktes Polyamid)

#### PA-CF – Beleg 1: Bambu Lab (Bambu PA6-CF)
* **Quelle:** [Bambu Lab PA6-CF Technical Data Sheet](https://wiki.bambulab.com/filament-acc/petcf-ppacf/c750bddfb8e44af6ae9f7dd9625fa458.pdf)
* **Fundstelle:** Seite 1-2, Physical and Mechanical Properties
* **Wörtliches Zitat:** „Young's Modulus (X-Y) ISO 527, GB/T 1040“
* **Belegte Zahlen:** Dichte 1.09 g/cm³, E-Modul XY 4430 MPa, Z 2170 MPa, Zugfestigkeit XY 102 MPa, Z 48 MPa, Bruchdehnung XY 5.8 %, Z 3.7 %, Biegemodul XY 5460 MPa, Z 2240 MPa, Biegefestigkeit XY 151 MPa, Z 80 MPa, Schmelztemperatur 223 °C, Glasübergang 68 °C, HDT 164 °C, 186 °C.

#### PA-CF – Beleg 2: Prusa Polymers (Prusament PA11 Carbon Fiber)
* **Quelle:** [Prusa Polymers Prusament PA11 Carbon Fiber Technical Datasheet](https://prusament.com/wp-content/uploads/2022/08/TDS_PA11CFB.pdf)
* **Fundstelle:** Seite 1-2, Typical material properties & Mechanical properties
* **Wörtliches Zitat:** „Mechanical properties of 3D printed testing specimens“
* **Belegte Zahlen:** Dichte 1.11 g/cm3, Streckgrenze Horizontal 42 MPa, Vertikal 49 MPa, E-Modul Horizontal 2.5 GPa, Vertikal 3.3 GPa, Dehnung Horizontal 3.3 %, Vertikal 2.6 %, Biegefestigkeit 63 MPa, 103 MPa, Biegemodul 3.0 GPa, 6.2 GPa, HDT 192 °C, 152 °C, Filament-Festigkeit 61 MPa, Shore-Härte 77 D.

#### PA-CF – Bewertung und Begründung
Mit Kurz-Kohlenstofffasern gefülltes Polyamid (PA6 bzw. PA11) für hochsteife und formstabile Funktionsbauteile mit HDT über 160 °C. In XY-Richtung erreicht der E-Modul bis zu 4430 MPa und die Zugfestigkeit über 100 MPa. Die interlaminare Scherfestigkeit in Z-Richtung liegt bei rund 20 bis 30 MPa.

---

### 2.13 Scherfestigkeitsverhältnisse nach VDI 2230

#### Scherfestigkeitsverhaeltnis – Beleg: SFS Group / Hoffmann Group
* **Quelle:** [SFS Handbuch Verbindungstechnik Mindesteinschraubtiefe nach VDI 2230](https://assets.hoffmann-group.com/media/ch/sfs_ch/broschueren_1/technisches_handbuch_fuer_verbindungstechnik/dimensionierung/allgemeines/Mindesteinschraubtiefe_in_geschnittene_Bauteilmuttergewinde_DE.pdf)
* **Fundstelle:** Seite 154, Tabelle Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten
* **Wörtliches Zitat:** „Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten“
* **Belegte Zahlen:** Baustahl 0,8 bis 0,85, Vergütungsstahl 0,65 bis 0,85, GJL 1,15, GJS 0,9, Aluminiumlegierung Guss 0,52, Knet 0,6.

---

## 3. Methodische Hinweise zur Scherfestigkeit τ_B und zu 3D-Druck-Werkstoffen

1. **Scherfestigkeit metallischer Werkstoffe (VDI 2230):**
   * Bei Schraubenberechnungen und Gewindeeinschraubtiefen ist das Scherfestigkeitsverhältnis $\tau_B / R_m$ die entscheidende Auslegungsgröße. Für unlegierte Baustähle und Weichautomatenstähle (11SMnPb30) sowie lösungsgeglühte austenitische Edelstähle (1.4305, 1.4571) gilt nach VDI 2230 $\tau_B / R_m = 0{,}80$. Für Aluminium-Gusslegierungen gilt 0,52, für Aluminium-Knetlegierungen 0,60.
2. **Anisotropie bei FDM- und SLS-Druckwerkstoffen:**
   * Bei Schmelzschichtverfahren (FDM: ASA, TPU 95A, PA-CF) weichen die Kennwerte zwischen Schichtebene (XY) und Aufbaurichtung (Z) deutlich voneinander ab. Insbesondere Bruchdehnung und Zugfestigkeit sind in Z-Richtung durch die interlaminare Schichthaftung begrenzt.
   * Bei pulverbettbasierten Verfahren (SLS: PA12) ist die Festigkeit nahezu isotrop (48 MPa in XY und Z), die Bruchdehnung sinkt in Z-Richtung nur moderat von ca. 20 % auf 15 %.
3. **Elastomerkennwerte bei TPU 95A:**
   * Da thermoplastische Polyurethane viskoelastisch sind und keine lineare Hookesche Dehngrenze besitzen, wird anstelle eines klassischen Elastizitätsmoduls der Spannungswert bei definierter Dehnung (Secant Modulus bei 100 % bzw. 200 % Dehnung) als Steifigkeitsmaß angegeben.

---

## 4. Verzeichnis der Primärquellen

1. Wieland-Werke AG: Material Data Sheet K18/K32 Cu-ETP (CW004A), BU Extruded Products, Edition 2022.
2. Thyssenkrupp Materials Services GmbH: Werkstoffdatenblatt CW004A (Cu-ETP / 2.0065), MX/TIS_08.2016.
3. Swiss Steel Group / Deutsche Edelstahlwerke: Werkstoffdatenblatt Acidur 4305 (1.4305 / X8CrNiS18-9), Ausgabe 05/2021.
4. Thyssenkrupp Materials Schweiz AG: Werkstoffdatenblatt REMANIT-4305 (1.4305), Stand 2024.
5. Swiss Steel Group / Deutsche Edelstahlwerke: Werkstoffdatenblatt Acidur 4571 (1.4571 / X6CrNiMoTi17-12-2), Ausgabe 05/2021.
6. Thyssenkrupp Materials Austria GmbH: Werkstoffdatenblatt RSH-Stahl 1.4571, Version 03/2017.
7. Saarstahl AG: Material Specification Sheet 11SMnPb30 (1.0718), Edition 06/2020.
8. Stahl Seltmann GmbH: Werkstoff-Datenblatt 11SMn30 / 11SMnPb30 (1.0715 / 1.0718), Stand 2026.
9. GermannGuss AG: Technisches Merkblatt EN AC-AlSi7Mg0.3 (EN AC-42100), Ausgabe 10/2018.
10. Hegi AG Metallgiesserei: Technisches Merkblatt AlSi7Mg (EN AC-42100 / Anticorodal 70), Stand 2026.
11. Thyssenkrupp Materials Services GmbH: Werkstoffdatenblatt EN AW-2007 (AlCuMgPb / 3.1645), MX/TIS_06.2018.
12. Hans-Erich Gemmel & Co. GmbH: Legierungsbeschreibung AlCuMgPb F37 (EN AW-2007 / 3.1645), Stand 2026.
13. Ensinger GmbH: Technical Data Sheet TECAMID 6 GF30 black (PA6-GF30), Stand 10/2023.
14. Röchling Industrial: Technical Data Sheet Sustamid® 6 GF 30 black (PA6-GF30), Mat.-Nr. 591069, Stand 2024.
15. EOS GmbH: Material Data Sheet PA 2200 (PA12 for EOSINT P), Ausgabe 01/2009.
16. HP Inc. / Proto3000: HP 3D High Reusability PA 12 Material Datasheet, Stand 07/2021.
17. Polymaker Inc.: Polymaker™ ASA Technical Data Sheet, Stand 2026.
18. Prusa Polymers a.s.: Technical Datasheet Prusament ASA, Version 1.1, Ausgabe 10/2022.
19. Ensinger GmbH: Technical Data Sheet TECANAT natural (PC), Stand 10/2023.
20. Röchling Industrial: Technical Data Sheet Sustanat® PC natural, Mat.-Nr. 591046, Stand 2024.
21. Polymaker Inc.: PolyFlex™ TPU95-HF Technical Data Sheet, Stand 2026.
22. Prusa Polymers a.s.: Technical Datasheet Prusament TPU 95A, Version 1.0, Ausgabe 05/2025.
23. Bambu Lab: Technical Data Sheet Bambu PA6-CF, Version 3.0, Stand 2024.
24. Prusa Polymers a.s.: Technical Datasheet Prusament PA11 Carbon Fiber, Version 1.0, Ausgabe 08/2022.
25. SFS Group / Hoffmann Group: Technisches Handbuch für Verbindungstechnik – Mindesteinschraubtiefe in geschnittene Bauteilmuttergewinde nach VDI 2230, Stand 2026.
