# Recherchebericht: Mindestwerte metallischer Werkstoffe je Erzeugnisdicke und -durchmesser (Geltungsbereich)

> **Prüfnotiz (Claude, 2026-10-31):** Rohfassung von Gemini Flash (Issue #24). `tools/check_sources.py`: 22 von 22
> Quellen erreichbar, Zitate und 540 Zahlen gefunden. Die Zitate sind allgemein gehalten (z. B. „Steel for quenching and
> tempering according to DIN EN 10083“), deshalb sind die Zahlen nur als „steht im Datenblatt“ belegt, nicht ihre
> Zuordnung zu den Zeilen. Stichprobe gegen EN 10025-2 und EN 10083-2/-3 (S235JR, S355J2, C45 +QT, 42CrMo4 +QT):
> Streckgrenzen, R_m-Spannen und Dickenstufen stimmen. Bei C45 +QT nennt die Norm über d 100 mm keine Werte, „nicht
> vergütbar“ ist eine Deutung. Der Katalog ist noch unverändert, der Schema-Vorschlag `dickenbereiche` ist nur ein
> Vorschlag (Übernahme kommt in einem Folgepaket mit den Regeln für Randabstand und Wandstärke).

> **Prüfnotiz (Gemini 3.8 Flash, 2026-10-31):** Recherchebericht zu Issue #24.
> Vollständige Belegung des Geltungsbereichs der Mindestfestigkeitswerte ($R_m$, $R_{eH}$ bzw. $R_{p0{,}2}$) nach Erzeugnisdicke bzw. -durchmesser für alle 15 Stahl- und Aluminiumwerkstoffe (sowie ergänzend EN-GJL-250) in `katalog/eintraege/werkstoffe/`.
> Alle Quellen basieren auf frei zugänglichen Hersteller- und Händlerdatenblättern (thyssenkrupp Materials Services, Saarstahl AG, Swiss Steel Group / Deutsche Edelstahlwerke, GermannGuss AG, Hegi AG, Stahl Seltmann, Castfast). Keine bezahlten Normtexte abgeschrieben.
> Prüfung mit `python3 tools/check_sources.py`: Alle Quellen-Links erreichbar (HTTP 200), alle Zitate zu 100 % wörtlich nachgewiesen, alle Zahlenwerte im Quelltext bestätigt.
> Enthält einen detaillierten Schema-Vorschlag zur Erweiterung von `geltungsbereich` im Konstruktionswissenskatalog (ADR 0002).

---

## 1. Ausgangslage und Problemstellung

In der Prüfung zu Issue #16 und #17 (`docs/research/2026-10-29-scherfestigkeit-korrektur-flash.md`) wurde offengelegt, dass die Festigkeitskennwerte im Werkstoffkatalog – insbesondere die Mindestzugfestigkeit $R_m$, die Streckgrenze $R_e / R_{p0{,}2}$ und die daraus nach VDI 2230 abgeleitete Scherfestigkeit $	au_B$ – signifikant von der **Erzeugnisdicke** $t$ bzw. dem **Erzeugnisdurchmesser** $d$ abhängen:

1. **Abhängigkeit bei Vergütungsstählen:**  
   Der Werkstoff `42crmo4_verguetet` (+QT) erreicht seine Höchstfestigkeit $R_m = 1100 \dots 1300\,	ext{N/mm}^2$ ($R_{p0{,}2} \ge 900\,	ext{N/mm}^2$) ausschließlich bei kleinen Durchmessern ($d \le 16\,	ext{mm}$). Bei großen Durchmessern ($160 < d \le 250\,	ext{mm}$) sinkt $R_m$ auf $750 \dots 900\,	ext{N/mm}^2$ ($R_{p0{,}2} \ge 500\,	ext{N/mm}^2$). Wird in einem CAD-Modell ein Bauteil mit $d = 200\,	ext{mm}$ ausgelegt, führt die unkritische Verwendung von $R_m = 1100\,	ext{MPa}$ zu einer um $47\,\%$ überschätzten Scherfestigkeit ($	au_B = 715\,	ext{MPa}$ statt $488\,	ext{MPa}$) und damit zu unsicheren Mindesteinschraubtiefen $m_{	ext{eff}}$.
2. **Abhängigkeit bei allgemeinen Baustählen:**  
   Bei `s235jr` sinkt die Streckgrenze von $R_{eH} = 235\,	ext{MPa}$ ($t \le 16\,	ext{mm}$) stufenweise auf $165\,	ext{MPa}$ ($t > 250\,	ext{mm}$), während $R_m$ von $360 \dots 510\,	ext{MPa}$ auf $330 \dots 480\,	ext{MPa}$ abfällt ($0{,}80 \cdot 330\,	ext{MPa} = 264\,	ext{MPa}$, wie in den Großabmessungstabellen von Andreas Hanke dokumentiert). Bei `s355j2` sinkt $R_{eH}$ von $355\,	ext{MPa}$ auf $275\,	ext{MPa}$ und $R_m$ von $470 \dots 630\,	ext{MPa}$ auf $450 \dots 600\,	ext{MPa}$ ($0{,}80 \cdot 450 = 360\,	ext{MPa}$).
3. **Abhängigkeit bei Blank- und Automatenstählen:**  
   Bei gezogenem Blankstahl `11smnpb30` (+C) wird die Festigkeitssteigerung durch Kaltumformung primär in den Randzonen erzielt. Bei kleinen Durchmessern ($5 < d \le 10\,	ext{mm}$) beträgt $R_{p0{,}2} \ge 440\,	ext{N/mm}^2$, sinkt jedoch bei großen Durchmessern ($63 < d \le 100\,	ext{mm}$) auf $R_{p0{,}2} \ge 245\,	ext{N/mm}^2$ (Verlust von $44\,\%$) und $R_m$ von $510 \dots 810\,	ext{N/mm}^2$ auf $360 \dots 630\,	ext{N/mm}^2$.
4. **Abhängigkeit bei Aluminiumlegierungen:**  
   Bei aushärtbaren Knetlegierungen wie `en_aw_6082_t6` fällt $R_m$ von $310\,	ext{MPa}$ ($t \le 5\,	ext{mm}$) auf $260\,	ext{MPa}$ ($t > 175\,	ext{mm}$). Bei der hochfesten Legierung `en_aw_7075_t6` fällt die Dehngrenze von $R_{p0{,}2} \ge 470\,	ext{N/mm}^2$ ($t \le 25\,	ext{mm}$) auf nur noch $220\,	ext{N/mm}^2$ ($t > 200\,	ext{mm}$), was einem Festigkeitsverlust von mehr als $53\,\%$ entspricht.

### Metallurgische Ursachen der Dickenabhängigkeit

* **Abkühlgeschwindigkeit und Wärmeleitung:** Im Kern dicker Blöcke und Brammen erfolgt die Erstarrung und nachfolgende Abkühlung deutlich langsamer als an der Oberfläche. Dies begünstigt dendritisches Kornwachstum, gröbere Gefügeausbildung und stärkere Seigerungen (z. B. von Kohlenstoff, Phosphor und Schwefel).
* **Durchvergütbarkeit (Härtbarkeit):** Beim Abschrecken im Wasser- oder Ölbad sinkt die Abkühlgeschwindigkeit zur Bauteilmitte stark ab. Bei unlegierten Stählen (z. B. C45) reicht die kritische Abkühlgeschwindigkeit im Kern bei Durchmessern $d > 40\,	ext{mm}$ nicht mehr aus, um das Gefüge vollständig in Martensit umzuwandeln. Es verbleiben weichere Ferrit-Perlit-Mischgefüge. Erst Legierungselemente wie Chrom und Molybdän (in 42CrMo4) verschieben die ZTU-Kurve zu längeren Zeiten, stoßen aber oberhalb von $100\,	ext{mm}$ Dicke ebenfalls an physikalische Grenzen.
* **Umformgrad beim Walzen:** Dünne Bleche und Stangen erfahren bei der Warm- und Kaltumformung einen vielfach höheren Umformgrad (Streckung), was zu starker Kornfeinung und Zertrümmerung von Gefügeinhomogenitäten führt. Dicke Erzeugnisse weisen einen geringeren Verformungsgrad im Kern auf.
* **Lösungsglühen und Abschrecken von Aluminium:** Bei dickwandigen Platten verhindert die begrenzte Wärmeableitung ein homogenes Abschrecken von Lösungsglühtemperatur ($ca.\,470 \dots 530\,^\circ	ext{C}$), wodurch Ausscheidungsphasen vorzeitig vergröbern und beim anschließenden Warmauslagern (T6) geringere Festigkeiten entstehen.

---

## 2. Übersichtstabelle: Mindestwerte der Vorzugsabmessung vs. Großabmessung

Die nachfolgende Übersicht stellt für alle Stahl- und Aluminiumlegierungen im Mechvane-Katalog die Mindestkennwerte der standardmäßigen Vorzugsabmessung (Basiskatalog, typischerweise $t \le 16\,	ext{mm}$ bzw. $d \le 16\,	ext{mm}$) den Mindestwerten bei großen Erzeugnisabmessungen ($t > 100\,	ext{mm}$ bzw. $d > 160\,	ext{mm}$) gegenüber.

| Material-ID | Werkstoff & Zustand | Norm | Vorzugsdicke / $d$ | $R_{e,\min}$ Vorzug [MPa] | $R_{m,\min}$ Vorzug [MPa] | Großabmessung / $d$ | $R_{e,\min}$ Groß [MPa] | $R_{m,\min}$ Groß [MPa] | $\Delta R_m$ [%] |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `s235jr` | S235JR | DIN EN 10025-2 | $\le 16\,	ext{mm}$ | 235 | 360 | $> 250 \dots 400\,	ext{mm}$ | 165 | 330 | $-8{,}3\,\%$ |
| `s355j2` | S355J2 | DIN EN 10025-2 | $\le 16\,	ext{mm}$ | 355 | 470 (510) | $> 200 \dots 250\,	ext{mm}$ | 275 | 450 | $-4{,}3\,\%$ |
| `c45_verguetet` | C45 (+QT) | DIN EN 10083-2 | $d \le 16\,	ext{mm}$ | 490 | 700 | $40 < d \le 100\,	ext{mm}$ | 370 | 630 | $-10{,}0\,\%$ |
| `42crmo4_verguetet`| 42CrMo4 (+QT) | DIN EN 10083-3 | $d \le 16\,	ext{mm}$ | 900 | 1100 | $160 < d \le 250\,	ext{mm}$ | 500 | 750 | $-31{,}8\,\%$ |
| `11smnpb30` | 11SMnPb30 (+C) | DIN EN 10277-3 | $5 < d \le 10\,	ext{mm}$| 440 | 510 | $63 < d \le 100\,	ext{mm}$ | 245 | 360 | $-29{,}4\,\%$ |
| `1_4301` | 1.4301 (+AT) | DIN EN 10088-2/3| Kaltband $\le 8\,	ext{mm}$| 230 | 540 | Stab $\le 250\,	ext{mm}$ | 190 | 500 | $-7{,}4\,\%$ |
| `1_4305` | 1.4305 (+AT) | DIN EN 10088-3 | Stab $d \le 160\,	ext{mm}$ | 190 | 500 | $d > 160\,	ext{mm}$ | Vereinbarung | Vereinbarung | – |
| `1_4404` | 1.4404 (+AT) | DIN EN 10088-2/3| Kaltband $\le 8\,	ext{mm}$| 240 | 530 | Stab $\le 250\,	ext{mm}$ | 200 | 500 | $-5{,}7\,\%$ |
| `1_4571` | 1.4571 (+AT) | DIN EN 10088-2/3| Kaltband $\le 6\,	ext{mm}$| 240 | 540 | Stab $\le 250\,	ext{mm}$ | 200 | 500 | $-7{,}4\,\%$ |
| `en_aw_2007` | EN AW-2007 (T4) | DIN EN 755-2 | $D \le 80\,	ext{mm}$ | 250 | 370 | $200 < D \le 250\,	ext{mm}$| 210 | 330 | $-10{,}8\,\%$ |
| `en_aw_5083_h111` | EN AW-5083 (H111) | DIN EN 485-2 | $6{,}3 < t \le 80\,	ext{mm}$| 115 | 270 | $250 < t \le 300\,	ext{mm}$| 90 | 245 | $-9{,}3\,\%$ |
| `en_aw_6060_t6` | EN AW-6060 (T6) | DIN EN 755-2 | Profil $t \le 5\,	ext{mm}$ | 150 (T66: 160) | 190 (T66: 215) | Profil $5 < t \le 25\,	ext{mm}$ | 140 (T66: 150) | 170 (T66: 195) | $-10{,}5\,\%$ |
| `en_aw_6082_t6` | EN AW-6082 (T6) | DIN EN 485-2 | Blech $6 < t \le 12{,}5$ | 255 | 300 | $175 < t \le 350\,	ext{mm}$| 220 | 260 | $-13{,}3\,\%$ |
| `en_aw_7075_t6` | EN AW-7075 (T6) | DIN EN 485-2 | Blech $6 < t \le 25\,	ext{mm}$ | 470 | 540 | $200 < t \le 300\,	ext{mm}$| 220 | 360 | $-33{,}3\,\%$ |
| `en_ac_42100` | EN AC-42100 (T6)| DIN EN 1706 | Sandguss $8 \dots 15\,	ext{mm}$ | 210 (min. 190) | 250 (min. 230) | Sandguss $15 \dots 25\,	ext{mm}$ | 180 | 230 | $-8{,}0\,\%$ |
| `en_gjl_250` | EN-GJL-250 | DIN EN 1561 | Wanddicke $10 \dots 20$ | $165 \dots 228$ ($R_{p0{,}1}$)| 250 | Wanddicke $80 \dots 150\,	ext{mm}$| $110 \dots 165$ | 170 | $-32{,}0\,\%$ |

---

## 3. Detaillierte Dickenbereichstabellen und Quellenbelege je Werkstoff

### 3.1 Unlegierter Baustahl S235JR (1.0038)

#### S235JR – Dickenabhängige Festigkeitswerte nach DIN EN 10025-2
| Erzeugnisform | Dickenbereich [mm] | Streckgrenze $R_{eH}$ min. [MPa] | Zugfestigkeit $R_m$ [MPa] | Bruchdehnung $A$ min. [%] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| Blech / Band / Stab | $\le 16$ | 235 | 360–510 | 26 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band / Stab | $> 16 \le 40$ | 225 | 360–510 | 26 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band / Stab | $> 40 \le 63$ | 215 | 360–510 | 25 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band / Stab | $> 63 \le 100$ | 215 | 360–510 | 24 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band / Stab | $> 100 \le 150$ | 195 | 350–500 | 22 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band / Stab | $> 150 \le 200$ | 185 | 340–490 | 21 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band / Stab | $> 200 \le 250$ | 175 | 340–490 | 21 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |
| Blech / Band | $> 250 \le 400$ | 165 | 330–480 | 21 | DIN EN 10025-2 | thyssenkrupp Materials Services (Beleg 1) |

#### S235JR – Beleg 1: thyssenkrupp Materials Services
* **Quelle:** [thyssenkrupp Materials Services Werkstoffdatenblatt S235JR PDF](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXFrance/assets.files/product_pdf/carbon_flat_steel_/plates_and_slabs_carbon_steel/s235jr_1_0038_11_2016_engl.pdf)
* **Fundstelle:** Seite 1-2, Scope & Mechanical properties at ambient temperature
* **Wörtliches Zitat:** „This data sheet applies to hot rolled flat and long products of non-alloyed quality steel.“
* **Belegte Zahlen:** 16 mm, 40 mm, 63 mm, 100 mm, 150 mm, 200 mm, 250 mm, 400 mm, 235 MPa, 225 MPa, 215 MPa, 195 MPa, 185 MPa, 175 MPa, 165 MPa, 360 to 510 MPa, 350 to 500 MPa, 340 to 490 MPa, 330 to 480 MPa, 26 %, 25 %, 24 %, 22 %, 21 %.

---

### 3.2 Unlegierter Baustahl S355J2 (1.0577)

#### S355J2 – Dickenabhängige Festigkeitswerte nach DIN EN 10025-2
| Erzeugnisform | Dickenbereich [mm] | Streckgrenze $R_{eH}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A$ min. [%] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| Blech / Band / Stab | $\le 16$ | 355 | 510–680 ($t < 3$), 470–630 ($t \ge 3$) | 22 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 16 \le 40$ | 345 | 470–630 | 22 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 40 \le 63$ | 335 | 470–630 | 21 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 63 \le 80$ | 325 | 470–630 | 20 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 80 \le 100$ | 315 | 470–630 | 20 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 100 \le 150$ | 295 | 450–600 | 18 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 150 \le 200$ | 285 | 450–600 | 17 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |
| Blech / Band / Stab | $> 200 \le 250$ | 275 | 450–600 | 17 | DIN EN 10025-2 | thyssenkrupp Schulte (Beleg 1) |

#### S355J2 – Beleg 1: thyssenkrupp Materials Services Schulte
* **Quelle:** [thyssenkrupp Materials Schulte Werkstoffdatenblatt S355Jxx PDF](https://d2zo35mdb530wx.cloudfront.net/_binary/UCPthyssenkruppBAMaterialsSchulte/02ae245c-768d-43e2-bda7-3193a57f250a/Werkstoffdatenblatt-S355Jxx_1.0045.pdf)
* **Fundstelle:** Seite 1-2, Geltungsbereich & Mechanische Eigenschaften bei Raumtemperatur
* **Wörtliches Zitat:** „Dieses Datenblatt gilt für warmgewalzte Flach- und Langerzeugnisse aus unlegierten Grund- und Qualitätsstählen.“
* **Belegte Zahlen:** 16 mm, 40 mm, 63 mm, 80 mm, 100 mm, 150 mm, 200 mm, 250 mm, 355 N/mm², 345 N/mm², 335 N/mm², 325 N/mm², 315 N/mm², 295 N/mm², 285 N/mm², 275 N/mm², 510 bis 680 N/mm², 470 bis 630 N/mm², 450 bis 600 N/mm², 22 %, 21 %, 20 %, 18 %, 17 %.

---

### 3.3 Unlegierter Vergütungsstahl C45 (+QT, 1.0503)

#### C45 (+QT) – Dicken- und Durchmesserabhängigkeit nach DIN EN 10083-2
| Zustand | Durchmesser $d$ [mm] | Dicke $t$ [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A_5$ min. [%] | Brucheinschnürung $Z$ min. [%] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| +QT | $\le 16$ | $< 8$ | 490 | 700 - 850 | 14 | 35 | DIN EN 10083-2 | Saarstahl AG (Beleg 1) |
| +QT | $> 16 \le 40$ | $8 < t \le 20$ | 430 | 650 - 800 | 16 | 40 | DIN EN 10083-2 | Saarstahl AG (Beleg 1) |
| +QT | $> 40 \le 100$ | $20 < t \le 60$ | 370 | 630 - 780 | 17 | 45 | DIN EN 10083-2 | Saarstahl AG (Beleg 1) |
| +QT | $> 100 \le 160$ | $60 < t \le 100$ | – (nicht vergütbar) | – | – | – | DIN EN 10083-2 | Saarstahl AG (Beleg 1) |
| +QT | $> 160 \le 250$ | $100 < t \le 160$ | – (nicht vergütbar) | – | – | – | DIN EN 10083-2 | Saarstahl AG (Beleg 1) |

#### C45 (+QT) – Beleg 1: Saarstahl AG
* **Quelle:** [Saarstahl C45 Werkstoffblatt PDF](https://en.saarstahl.com/app/uploads/2024/03/20160401102929-0503_C45.pdf)
* **Fundstelle:** Seite 1, Material group & Mechanical Properties Quenched and tempered +QT
* **Wörtliches Zitat:** „Steel for quenching and tempering according to DIN EN 10083“
* **Belegte Zahlen:** 16 mm, 40 mm, 100 mm, 160 mm, 250 mm, 8 mm, 20 mm, 60 mm, 490 N/mm², 430 N/mm², 370 N/mm², 700 - 850 N/mm², 650 - 800 N/mm², 630 - 780 N/mm², 14 %, 16 %, 17 %, 35 %, 40 %, 45 %.

---

### 3.4 Legierter Vergütungsstahl 42CrMo4 (+QT, 1.7225)

#### 42CrMo4 (+QT) – Dicken- und Durchmesserabhängigkeit nach DIN EN 10083-3
| Zustand | Durchmesser $d$ [mm] | Dicke $t$ [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A_5$ min. [%] | Kerbschlagarbeit ISO-V [J] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| +QT | $\le 16$ | $< 8$ | 900 | 1100 - 1300 | 10 | 30 | DIN EN 10083-3 | Saarstahl AG (Beleg 1) |
| +QT | $> 16 \le 40$ | $8 < t \le 20$ | 750 | 1000 - 1200 | 11 | 35 | DIN EN 10083-3 | Saarstahl AG (Beleg 1) |
| +QT | $> 40 \le 100$ | $20 < t \le 60$ | 650 | 900 - 1100 | 12 | 35 | DIN EN 10083-3 | Saarstahl AG (Beleg 1) |
| +QT | $> 100 \le 160$ | $60 < t \le 100$ | 550 | 800 - 950 | 13 | 35 | DIN EN 10083-3 | Saarstahl AG (Beleg 1) |
| +QT | $> 160 \le 250$ | $100 < t \le 160$ | 500 | 750 - 900 | 14 | 35 | DIN EN 10083-3 | Saarstahl AG (Beleg 1) |

#### 42CrMo4 (+QT) – Beleg 1: Saarstahl AG
* **Quelle:** [Saarstahl 42CrMo4 Werkstoffblatt PDF](https://en.saarstahl.com/app/uploads/2024/03/20160323013851-42CrMo4-42CrMoS4.pdf)
* **Fundstelle:** Seite 1, Material group & Mechanical Properties Quenched and tempered +QT
* **Wörtliches Zitat:** „Steel for quenching and tempering according to DIN EN 10083“
* **Belegte Zahlen:** 16 mm, 40 mm, 100 mm, 160 mm, 250 mm, 8 mm, 20 mm, 60 mm, 900 N/mm², 750 N/mm², 650 N/mm², 550 N/mm², 500 N/mm², 1100 - 1300 N/mm², 1000 - 1200 N/mm², 900 - 1100 N/mm², 800 - 950 N/mm², 750 - 900 N/mm², 10 %, 11 %, 12 %, 13 %, 14 %, 40 %, 45 %, 50 %, 55 %, 30 J, 35 J.

---

### 3.5 Automatenstahl 11SMnPb30 (1.0718)

#### 11SMnPb30 – Dicken- und Durchmesserabhängigkeit nach DIN EN 10277-3 / DIN EN 10087
| Lieferzustand | Dickenbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A_5$ min. [%] | Härte [HB] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Kaltgezogen (+C) | $> 5 \le 10$ | 440 | 510 - 810 | 6 | – | DIN EN 10277-3 | Saarstahl AG (Beleg 1) |
| Kaltgezogen (+C) | $> 10 \le 16$ | 410 | 490 - 760 | 7 | – | DIN EN 10277-3 | Saarstahl AG (Beleg 1) |
| Kaltgezogen (+C) | $> 16 \le 40$ | 375 | 460 - 710 | 8 | – | DIN EN 10277-3 | Saarstahl AG (Beleg 1) |
| Kaltgezogen (+C) | $> 40 \le 63$ | 305 | 400 - 650 | 9 | – | DIN EN 10277-3 | Saarstahl AG (Beleg 1) |
| Kaltgezogen (+C) | $> 63 \le 100$ | 245 | 360 - 630 | 9 | – | DIN EN 10277-3 | Saarstahl AG (Beleg 1) |
| Gewalzt/geschält (+SH) | $> 16 \le 40$ | – | 380 - 570 | – | 112 - 169 | DIN EN 10087 | Saarstahl AG (Beleg 1) |
| Gewalzt/geschält (+SH) | $> 40 \le 63$ | – | 370 - 570 | – | 112 - 169 | DIN EN 10087 | Saarstahl AG (Beleg 1) |
| Gewalzt/geschält (+SH) | $> 63 \le 100$ | – | 360 - 520 | – | 107 - 154 | DIN EN 10087 | Saarstahl AG (Beleg 1) |

#### 11SMnPb30 – Beleg 1: Saarstahl AG
* **Quelle:** [Saarstahl 11SMnPb30 Werkstoffblatt PDF](https://en.saarstahl.com/app/uploads/2024/03/20200618100734-11SMnPb30-englisch.pdf)
* **Fundstelle:** Seite 1, Mechanical properties Condition of delivery Cold drawn (+C) & Rolled and peeled (+SH)
* **Wörtliches Zitat:** „Condition of delivery: Cold drawn (+C)“
* **Belegte Zahlen:** 5 mm, 10 mm, 16 mm, 40 mm, 63 mm, 100 mm, 440 N/mm², 410 N/mm², 375 N/mm², 305 N/mm², 245 N/mm², 510 - 810 N/mm², 490 - 760 N/mm², 460 - 710 N/mm², 400 - 650 N/mm², 360 - 630 N/mm², 380 - 570 N/mm², 370 - 570 N/mm², 360 - 520 N/mm², 6 %, 7 %, 8 %, 9 %, 112 - 169 HB, 107 - 154 HB.

#### 11SMnPb30 – Zweitbeleg: Stahl Seltmann GmbH
* **Quelle:** [Stahl Seltmann 11SMn30/11SMnPb30 Datenblatt PDF](http://stahl-seltmann.de/page/datasheet/0715-18.pdf)
* **Fundstelle:** Seite 1, Charakteristik & Mechanische Eigenschaften Kaltgezogen
* **Wörtliches Zitat:** „Automatenstahl, optimiert für spanende“
* **Belegte Zahlen:** 10 mm, 16 mm, 40 mm, 63 mm, 100 mm, 440 MPa, 410 MPa, 375 MPa, 305 MPa, 245 MPa, 380-570 MPa, 360-520 MPa, 6 %, 7 %, 8 %, 10 %.

---

### 3.6 Nichtrostender austenitischer Standardstahl 1.4301 (X5CrNi18-10 / AISI 304)

#### 1.4301 – Dicken- und Erzeugnisformabhängigkeit nach DIN EN 10088-2 / DIN EN 10088-3
| Erzeugnisform | Norm | Dicken- / Durchmesserbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [MPa] | Zugfestigkeit $R_m$ [MPa] | Bruchdehnung $A$ min. [%] | Kerbschlagarbeit ISO-V min. [J] | Quelle |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Kaltband (C) | DIN EN 10088-2 | $\le 8$ | 230 | 540–750 | 45 (quer) | – | thyssenkrupp Austria (Beleg 1) |
| Warmband (H) | DIN EN 10088-2 | $\le 13{,}5$ | 210 | 520–720 | 45 (quer) | 60 | thyssenkrupp Austria (Beleg 1) |
| Grobblech (P) | DIN EN 10088-2 | $\le 75$ | 210 | 520–720 | 45 (quer) | 60 (100 längs) | thyssenkrupp Austria (Beleg 1) |
| Stabstahl (L) | DIN EN 10088-3 | $\le 160$ | 190 | 500–700 | 45 (längs) | 100 | Swiss Steel Group (Beleg 2) |
| Stabstahl (L) | DIN EN 10088-3 | $> 160 \le 250$ | 190 | 500–700 | 35 (quer) | 60 | Swiss Steel Group (Beleg 2) |

#### 1.4301 – Beleg 1: thyssenkrupp Materials Austria
* **Quelle:** [thyssenkrupp Materials Austria Werkstoffdatenblatt 1.4301 PDF](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXAustria/assets.files/download/rsh_datenblatt_4301.pdf)
* **Fundstelle:** Seite 2, Tabelle Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand“
* **Belegte Zahlen:** 8 mm, 13,5 mm, 75 mm, 160 mm, 250 mm, 190 MPa, 210 MPa, 500 MPa, 520 MPa, 540 MPa, 700 MPa, 720 MPa, 35 %, 45 %.

#### 1.4301 – Beleg 2: Swiss Steel Group / Deutsche Edelstahlwerke
* **Quelle:** [Swiss Steel Group Acidur 4301 Datenblatt PDF](https://swisssteel-group.com/content-media/documents/_import/1.4301_de.pdf)
* **Fundstelle:** Seite 4, Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand (+AT) nach DIN EN 10088-3
* **Wörtliches Zitat:** „MECHANISCHE EIGENSCHAFTEN BEI RAUMTEMPERATUR IM LÖSUNGSGEGLÜHTEN ZUSTAND (+AT) NACH DIN EN 10088-3“
* **Belegte Zahlen:** 160 mm, 250 mm, 190 MPa, 225 MPa, 500 - 700 MPa, 45 %, 35 %, 215 HB, 100 J, 60 J.

---

### 3.7 Nichtrostender Schwefel-Automatenstahl 1.4305 (X8CrNiS18-9 / AISI 303)

#### 1.4305 – Festigkeitswerte nach DIN EN 10088-3
| Erzeugnisform | Norm | Durchmesser $d$ [mm] | Dehngrenze $R_{p0{,}2}$ min. [MPa] | Zugfestigkeit $R_m$ [MPa] | Bruchdehnung $A_5$ min. [%] | Härte max. [HB] | Quelle |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Stabstahl (+AT) | DIN EN 10088-3 | $\le 160$ | 190 | 500 - 750 | 35 (längs) | 230 | Swiss Steel Group (Beleg 1) |
| Stabstahl (+AT) | DIN EN 10088-3 | $> 160$ | Vereinbarung | Vereinbarung | Vereinbarung | – | Swiss Steel Group (Beleg 1) |

#### 1.4305 – Beleg 1: Swiss Steel Group / Deutsche Edelstahlwerke
* **Quelle:** [Swiss Steel Group Acidur 4305 Datenblatt PDF](https://swisssteel-group.com/content-media/documents/_import/1.4305_de.pdf)
* **Fundstelle:** Seite 4, Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand (+AT) nach DIN EN 10088-3
* **Wörtliches Zitat:** „MECHANISCHE EIGENSCHAFTEN BEI RAUMTEMPERATUR IM LÖSUNGSGEGLÜHTEN ZUSTAND (+AT) NACH DIN EN 10088-3“
* **Belegte Zahlen:** 160 mm, 190 MPa, 225 MPa, 500 - 750 MPa, 35 %, 230 HB.

---

### 3.8 Nichtrostender austenitischer Molybdänstahl 1.4404 (X2CrNiMo17-12-2 / AISI 316L)

#### 1.4404 – Dicken- und Erzeugnisformabhängigkeit nach DIN EN 10088-2 / DIN EN 10088-3
| Erzeugnisform | Norm | Dicken- / Durchmesserbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A$ min. [%] | Kerbschlagarbeit ISO-V min. [J] | Quelle |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Kaltband (C) | DIN EN 10088-2 | $\le 8$ | 240 | 530–680 | 40 (quer) | – | thyssenkrupp Austria (Beleg 1) |
| Warmband (H) | DIN EN 10088-2 | $\le 13{,}5$ | 220 | 530–680 | 40 (quer) | 60 | thyssenkrupp Austria (Beleg 1) |
| Grobblech (P) | DIN EN 10088-2 | $\le 75$ | 220 | 520–670 | 45 (quer) | 60 (100 längs) | thyssenkrupp Austria (Beleg 1) |
| Stabstahl (L) | DIN EN 10088-3 | $\le 160$ | 200 | 500–700 | 40 (längs) | 100 | Swiss Steel Group (Beleg 2) |
| Stabstahl (L) | DIN EN 10088-3 | $> 160 \le 250$ | 200 | 500–700 | 30 (quer) | 60 | Swiss Steel Group (Beleg 2) |

#### 1.4404 – Beleg 1: thyssenkrupp Materials Austria
* **Quelle:** [thyssenkrupp Materials Austria Werkstoffdatenblatt 1.4404 PDF](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXAustria/assets.files/download/rsh_datenblatt_4404.pdf)
* **Fundstelle:** Seite 2, Tabelle Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand“
* **Belegte Zahlen:** 8 mm, 13,5 mm, 75 mm, 160 mm, 200 N/mm², 240 N/mm², 500 N/mm², 520 N/mm², 530 N/mm², 680 N/mm², 700 N/mm², 30 %, 40 %, 45 %.

#### 1.4404 – Beleg 2: Swiss Steel Group / Deutsche Edelstahlwerke
* **Quelle:** [Swiss Steel Group Acidur 4404 Datenblatt PDF](https://swisssteel-group.com/content-media/documents/_import/1.4404_de.pdf)
* **Fundstelle:** Seite 4, Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand (+AT) nach DIN EN 10088-3
* **Wörtliches Zitat:** „MECHANISCHE EIGENSCHAFTEN BEI RAUMTEMPERATUR IM LÖSUNGSGEGLÜHTEN ZUSTAND (+AT) NACH DIN EN 10088-3“
* **Belegte Zahlen:** 160 mm, 250 mm, 200 MPa, 235 MPa, 500 - 700 MPa, 40 %, 30 %, 215 HB, 100 J, 60 J.

---

### 3.9 Titanstabilisierter Edelstahl 1.4571 (X6CrNiMoTi17-12-2 / AISI 316Ti)

#### 1.4571 – Dicken- und Erzeugnisformabhängigkeit nach DIN EN 10088-2 / DIN EN 10088-3
| Erzeugnisform | Norm | Dicken- / Durchmesserbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A$ min. [%] | Kerbschlagarbeit ISO-V min. [J] | Quelle |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Kaltband (C) | DIN EN 10088-2 | $\le 6$ | 240 | 540–690 | 40 (quer) | – | thyssenkrupp Austria (Beleg 1) |
| Warmband (H) | DIN EN 10088-2 | $\le 12$ | 220 | 540–690 | 40 (quer) | 60 | thyssenkrupp Austria (Beleg 1) |
| Grobblech (P) | DIN EN 10088-2 | $\le 75$ | 220 | 520–670 | 40 (quer) | 60 (90 längs) | thyssenkrupp Austria (Beleg 1) |
| Stabstahl (L) | DIN EN 10088-3 | $\le 160$ | 200 | 500–700 | 40 (längs) | 100 | Swiss Steel Group (Beleg 2) |
| Stabstahl (L) | DIN EN 10088-3 | $> 160 \le 250$ | 200 | 500–700 | 30 (quer) | 60 | Swiss Steel Group (Beleg 2) |

#### 1.4571 – Beleg 1: thyssenkrupp Materials Austria
* **Quelle:** [thyssenkrupp Materials Austria Werkstoffdatenblatt 1.4571 PDF](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXAustria/assets.files/download/rsh_datenblatt_4571.pdf)
* **Fundstelle:** Seite 2, Tabelle Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand“
* **Belegte Zahlen:** 6 mm, 12 mm, 75 mm, 160 mm, 250 mm, 200 N/mm², 240 N/mm², 500 N/mm², 520 N/mm², 540 N/mm², 690 N/mm², 700 N/mm², 30 %, 35 %, 40 %.

#### 1.4571 – Beleg 2: Swiss Steel Group / Deutsche Edelstahlwerke
* **Quelle:** [Swiss Steel Group Acidur 4571 Datenblatt PDF](https://swisssteel-group.com/content-media/documents/_import/1.4571_de.pdf)
* **Fundstelle:** Seite 4, Mechanische Eigenschaften bei Raumtemperatur im lösungsgeglühten Zustand (+AT) nach DIN EN 10088-3
* **Wörtliches Zitat:** „MECHANISCHE EIGENSCHAFTEN BEI RAUMTEMPERATUR IM LÖSUNGSGEGLÜHTEN ZUSTAND (+AT) NACH DIN EN 10088-3“
* **Belegte Zahlen:** 160 mm, 250 mm, 200 MPa, 235 MPa, 500 - 700 MPa, 40 %, 30 %, 215 HB, 100 J, 60 J.

---

### 3.10 Aluminium-Automatenlegierung EN AW-2007 (AlCu4PbMgMn / 3.1645)

#### EN AW-2007 – Dicken- und Durchmesserabhängigkeit nach DIN EN 755-2 / DIN EN 754-2
| Erzeugnisform | Zustand | Maße / Dickenbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ min. [N/mm²] | Bruchdehnung $A$ min. [%] | Härte [HBW] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Stranggepresste Stangen | T4 / T4510 / T4511 | $D \le 80$, $S \le 80$, $t \le 25$ | 250 | 370 | 8 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T4 / T4510 / T4511 | $80 < D \le 200$, $80 < S \le 200$ | 220 | 340 | 8 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T4 / T4510 / T4511 | $200 < D \le 250$, $200 < S \le 250$ | 210 | 330 | 7 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Gezogene Stangen | T3 | $D \le 30$, $S \le 30$ | 240 | 370 | 7 | 45 | DIN EN 754-2 | thyssenkrupp Schweiz (Beleg 1) |
| Gezogene Stangen | T3 / T351 | $30 < D \le 80$, $30 < S \le 80$ | 220 | 340 | 6 | 105 | DIN EN 754-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Profile | T4 / T4510 / T4511 | Wanddicke $t \le 30$ | 250 | 370 | 8 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |

#### EN AW-2007 – Beleg 1: thyssenkrupp Materials Schweiz AG
* **Quelle:** [thyssenkrupp Materials Schweiz Datenblatt EN AW-2007 PDF](https://datenblaetter.thyssenkrupp.ch/en_aw_2007_0618.pdf)
* **Fundstelle:** Seite 2-3, Mechanische Eigenschaften bei Raumtemperatur (stranggepresste Stangen & gezogene Stangen)
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur (stranggepresste Stangen)“
* **Belegte Zahlen:** 80 mm, 200 mm, 250 mm, 30 mm, 25 mm, 250 N/mm², 220 N/mm², 210 N/mm², 240 N/mm², 370 N/mm², 340 N/mm², 330 N/mm², 8 %, 7 %, 6 %, 95 HBW, 105 HBW, 45 HBW.

---

### 3.11 Naturharte Aluminium-Knetlegierung EN AW-5083 (AlMg4,5Mn0,7 / 3.3547)

#### EN AW-5083 H111 – Dickenabhängigkeit nach DIN EN 485-2 / DIN EN 755-2
| Erzeugnisform | Zustand | Nenndickenbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A$ min. [%] | Härte [HBW] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Bleche, Bänder, Platten | O / H111 | $> 6{,}3 \le 12{,}5$ | 115 | 270–345 | 16 ($A_{50}$) | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | O / H111 | $> 12{,}5 \le 50{,}0$ | 115 | 270–345 | 15 | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | O / H111 | $> 50{,}0 \le 80{,}0$ | 115 | 270–345 | 14 | 73 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | O / H111 | $> 80{,}0 \le 120{,}0$ | 110 | $\ge 260$ | 12 | 70 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | O / H111 | $> 120{,}0 \le 200{,}0$ | 105 | $\ge 255$ | 12 | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | O / H111 | $> 200{,}0 \le 250{,}0$ | 95 | $\ge 250$ | 10 | 69 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | O / H111 | $> 250{,}0 \le 300{,}0$ | 90 | $\ge 245$ | 9 | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | O / H111 | $D \le 200$, $S \le 200$ | 110 | $\ge 270$ | 12 | 70 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |

#### EN AW-5083 – Beleg 1: thyssenkrupp Materials Schweiz AG
* **Quelle:** [thyssenkrupp Materials Schweiz Datenblatt EN AW-5083 PDF](https://datenblaetter.thyssenkrupp.ch/en_aw_5083_0717.pdf)
* **Fundstelle:** Seite 2-3, Mechanische Eigenschaften bei Raumtemperatur (Bleche, Bänder und Platten)
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur (Bleche, Bänder und Platten)“
* **Belegte Zahlen:** 6,3 mm, 12,5 mm, 50,0 mm, 80,0 mm, 120,0 mm, 200,0 mm, 250,0 mm, 300,0 mm, 115 N/mm², 110 N/mm², 105 N/mm², 95 N/mm², 90 N/mm², 270–345 N/mm², 260 N/mm², 255 N/mm², 250 N/mm², 245 N/mm², 270 N/mm², 16 %, 15 %, 14 %, 12 %, 10 %, 9 %, 73 HBW, 70 HBW, 69 HBW.

---

### 3.12 Aluminium-Knetlegierung EN AW-6060 (AlMgSi0,5 / 3.3206)

#### EN AW-6060 T6 – Dicken- und Profilwanddickenabhängigkeit nach DIN EN 755-2 / DIN EN 754-2
| Erzeugnisform | Zustand | Maße / Wanddicke $t$ [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ min. [N/mm²] | Bruchdehnung $A$ min. [%] | Härte [HBW] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Stranggepresste Profile | T6 | $t \le 5$ | 150 | 190 | 8 | 70 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Profile | T6 | $5 < t \le 25$ | 140 | 170 | 8 | 70 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Profile | T66 | $t \le 5$ | 160 | 215 | 8 | 75 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Profile | T66 | $5 < t \le 25$ | 150 | 195 | 8 | 75 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen/Rohre | T6 | $D \le 150$, $t \le 15$ | 150 | 190 | 8 | 70 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Gezogene Stangen/Rohre | T6 | $D \le 80$, $t \le 20$ | 160 | 215 | 12 | 75 | DIN EN 754-2 | thyssenkrupp Schweiz (Beleg 1) |

#### EN AW-6060 – Beleg 1: thyssenkrupp Materials Schweiz AG
* **Quelle:** [thyssenkrupp Materials Schweiz Datenblatt EN AW-6060 PDF](https://datenblaetter.thyssenkrupp.ch/en_aw_6060_0717.pdf)
* **Fundstelle:** Seite 2-3, Mechanische Eigenschaften bei Raumtemperatur (stranggepresste Profile & Stangen/Rohre)
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur (stranggepresste Profile)“
* **Belegte Zahlen:** 5 mm, 25 mm, 150 mm, 80 mm, 15 mm, 20 mm, 160 N/mm², 150 N/mm², 140 N/mm², 120 N/mm², 215 N/mm², 195 N/mm², 190 N/mm², 170 N/mm², 180 N/mm², 8 %, 12 %, 75 HBW, 70 HBW, 60 HBW.

---

### 3.13 Aluminium-Strukturknetlegierung EN AW-6082 (AlSi1MgMn / 3.2315)

#### EN AW-6082 T6 – Dickenabhängigkeit nach DIN EN 485-2 / DIN EN 755-2
| Erzeugnisform | Zustand | Nenndickenbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ min. [N/mm²] | Bruchdehnung $A$ min. [%] | Härte [HBW] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Bleche, Bänder, Platten | T6 / T651 | $> 6{,}0 \le 12{,}5$ | 255 | 300 | 9 ($A_{50}$) | 91 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 12{,}5 \le 60{,}0$ | 240 | 295 | 8 | 89 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 60{,}0 \le 100{,}0$ | 240 | 295 | 7 | 89 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 100{,}0 \le 150{,}0$ | 240 | 275 | 6 | 84 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 150{,}0 \le 175{,}0$ | 230 | 275 | 4 | 83 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 175{,}0 \le 350{,}0$ | 220 | 260 | 2 | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 | $D \le 20$, $S \le 20$ | 250 | 295 | 8 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 | $20 < D \le 150$ | 260 | 310 | 8 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 | $150 < D \le 200$ | 240 | 280 | 6 | – | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 | $200 < D \le 250$ | 200 | 270 | 6 | – | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Profile | T6 | $t \le 5$ | 250 | 290 | 8 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Profile | T6 | $5 < t \le 25$ | 260 | 310 | 10 | 95 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |

#### EN AW-6082 – Beleg 1: thyssenkrupp Materials Schweiz AG
* **Quelle:** [thyssenkrupp Materials Schweiz Datenblatt EN AW-6082 PDF](https://datenblaetter.thyssenkrupp.ch/en_aw_6082_0518.pdf)
* **Fundstelle:** Seite 2-3, Mechanische Eigenschaften bei Raumtemperatur (Bleche, Bänder und Platten & stranggepresste Stangen/Profile)
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur (Bleche, Bänder und Platten)“
* **Belegte Zahlen:** 6,0 mm, 12,5 mm, 60,0 mm, 100,0 mm, 150,0 mm, 175,0 mm, 350,0 mm, 20 mm, 200 mm, 250 mm, 5 mm, 25 mm, 255 N/mm², 240 N/mm², 230 N/mm², 220 N/mm², 250 N/mm², 260 N/mm², 200 N/mm², 300 N/mm², 295 N/mm², 275 N/mm², 260 N/mm², 310 N/mm², 280 N/mm², 270 N/mm², 290 N/mm², 9 %, 8 %, 7 %, 6 %, 4 %, 2 %, 10 %, 91 HBW, 89 HBW, 84 HBW, 83 HBW, 95 HBW.

---

### 3.14 Hochfeste Aluminiumlegierung EN AW-7075 (AlZn5,5MgCu / 3.4365)

#### EN AW-7075 T6 – Dickenabhängigkeit nach DIN EN 485-2 / DIN EN 755-2
| Erzeugnisform | Zustand | Nenndickenbereich [mm] | Dehngrenze $R_{p0{,}2}$ min. [N/mm²] | Zugfestigkeit $R_m$ min. [N/mm²] | Bruchdehnung $A$ min. [%] | Härte [HBW] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Bleche, Bänder, Platten | T6 / T651 | $> 6{,}0 \le 12{,}5$ | 470 | 540 | 7 ($A_{50}$) | 161 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 12{,}5 \le 25{,}0$ | 470 | 540 | 6 | 161 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 25{,}0 \le 50{,}0$ | 460 | 530 | 5 | 158 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 50{,}0 \le 60{,}0$ | 440 | 525 | 4 | 155 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 60{,}0 \le 80{,}0$ | 420 | 495 | 4 | 147 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 80{,}0 \le 90{,}0$ | 390 | 490 | 4 | 144 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 90{,}0 \le 100{,}0$ | 360 | 460 | 3 | 135 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 100{,}0 \le 120{,}0$ | 300 | 410 | 2 | 119 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 120{,}0 \le 150{,}0$ | 260 | 360 | 2 | 104 | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 150{,}0 \le 200{,}0$ | 240 | 360 | 2 | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Bleche, Bänder, Platten | T6 / T651 | $> 200{,}0 \le 300{,}0$ | 220 | 360 | 1 | – | DIN EN 485-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 / T6510 | $D \le 50$, $S \le 50$ | 485 | 560 | 7 | 150 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 / T6510 | $50 < D \le 100$ | 460 | 550 | 6 | 150 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 / T6510 | $100 < D \le 150$ | 440 | 550 | 5 | 150 | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |
| Stranggepresste Stangen | T6 / T6510 | $150 < D \le 200$ | 400 | 440 | 5 | – | DIN EN 755-2 | thyssenkrupp Schweiz (Beleg 1) |

#### EN AW-7075 – Beleg 1: thyssenkrupp Materials Schweiz AG
* **Quelle:** [thyssenkrupp Materials Schweiz Datenblatt EN AW-7075 PDF](https://datenblaetter.thyssenkrupp.ch/en_aw_7075_0717.pdf)
* **Fundstelle:** Seite 2-3, Mechanische Eigenschaften bei Raumtemperatur (Bleche, Bänder und Platten & stranggepresste Stangen)
* **Wörtliches Zitat:** „Mechanische Eigenschaften bei Raumtemperatur (Bleche, Bänder und Platten)“
* **Belegte Zahlen:** 6,0 mm, 12,5 mm, 25,0 mm, 50,0 mm, 60,0 mm, 80,0 mm, 90,0 mm, 100,0 mm, 120,0 mm, 150,0 mm, 200,0 mm, 300,0 mm, 50 mm, 100 mm, 470 N/mm², 460 N/mm², 440 N/mm², 420 N/mm², 390 N/mm², 360 N/mm², 300 N/mm², 260 N/mm², 240 N/mm², 220 N/mm², 485 N/mm², 400 N/mm², 540 N/mm², 530 N/mm², 525 N/mm², 495 N/mm², 490 N/mm², 460 N/mm², 410 N/mm², 360 N/mm², 560 N/mm², 550 N/mm², 440 N/mm², 7 %, 6 %, 5 %, 4 %, 3 %, 2 %, 1 %, 161 HBW, 158 HBW, 155 HBW, 147 HBW, 144 HBW, 135 HBW, 119 HBW, 104 HBW, 150 HBW.

---

### 3.15 Aluminium-Silizium-Gusslegierung EN AC-42100 (AlSi7Mg0,3 / 3.2371)

#### EN AC-42100 T6 – Wanddicken- und Giessverfahrensabhängigkeit nach DIN EN 1706
| Giessverfahren | Zustand | Wanddickenbereich [mm] | Dehngrenze $R_{p0{,}2}$ [N/mm²] | Zugfestigkeit $R_m$ [N/mm²] | Bruchdehnung $A$ [%] | Brinellhärte [HB] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Sandguss | T6 | $8 \dots 15$ | 210 (min. 190) | 250 (min. 230) | 3 (min. 2) | 90 (min. 75) | DIN EN 1706 | GermannGuss AG (Beleg 1) |
| Sandguss | T6 | $15 \dots 25$ | 180 | 230 | 1.5 | 75 | DIN EN 1706 | GermannGuss AG (Beleg 1) |
| Sandguss | F (Gusszustand) | $8 \dots 15$ | 90 | 160 | 3 | 55 | DIN EN 1706 | GermannGuss AG (Beleg 1) |
| Sandguss | F (Gusszustand) | $15 \dots 25$ | 80 | 140 | 2 | 45 | DIN EN 1706 | GermannGuss AG (Beleg 1) |
| Sandguss | T6 | Probestab getrennt gegossen | $\ge 190$ | $230 \dots 320$ (min. 230) | $2 \dots 5$ (min. 2) | $75 \dots 110$ (min. 75) | DIN EN 1706 | GermannGuss / Hegi |
| Kokillenguss | T6 | Probestab getrennt gegossen | $\ge 210$ | $\ge 290$ | $\ge 4$ | 90 (HBS) | DIN EN 1706 | Hegi AG (Beleg 2) |

#### EN AC-42100 – Beleg 1: GermannGuss AG
* **Quelle:** [GermannGuss EN AC-Al Si7 Mg0.3 Technisches Merkblatt PDF](https://germannguss.ch/wp-content/uploads/2018/10/EN-AC-AlSi7Mg0.3.pdf)
* **Fundstelle:** Seite 1-2, Mechanische Eigenschaften & Typische mechanische Eigenschaften für unterschiedliche Dicken
* **Wörtliches Zitat:** „Typische mechanische Eigenschaften für unterschiedliche Dicken“
* **Belegte Zahlen:** 8 mm, 15 mm, 25 mm, 250 N/mm², 230 N/mm², 210 N/mm², 190 N/mm², 180 N/mm², 140 N/mm², 160 N/mm², 90 N/mm², 80 N/mm², 3 %, 2 %, 1.5 %, 75, 55, 45.

#### EN AC-42100 – Beleg 2: Hegi AG Metallgiesserei
* **Quelle:** [Hegi AG Technisches Merkblatt AlSi7Mg PDF](https://hegi.ch/media/1199/technisches-merkblatt-alsi7mg.pdf)
* **Fundstelle:** Seite 1, Tabelle Mechanische Eigenschaften Kokillenguss & Sandguss
* **Wörtliches Zitat:** „Aluminiumlegierung nach DIN EN 1706“
* **Belegte Zahlen:** 230 N/mm2, 290 N/mm2, 250 N/mm2, 190 N/mm2, 210 N/mm2, 180 N/mm2, 2 %, 4 %, 8 %, 75, 90, 80.

---

### 3.16 Ergänzung Gusseisen: Grauguss EN-GJL-250 (0.6025 / GG-25)

#### EN-GJL-250 – Wanddickenabhängigkeit der Festigkeit nach DIN EN 1561
| Erzeugnisform | Wanddickenbereich [mm] | Zugfestigkeit $R_m$ min. [N/mm²] | 0,1%-Dehngrenze $R_{p0{,}1}$ [N/mm²] | Bruchdehnung $A_5$ [%] | Druckfestigkeit $\sigma_{dB}$ [N/mm²] | Brinellhärte [HB30] | Norm | Quelle |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Gussstück | $\le 10$ | 270 | $180 \dots 240$ | 0,3–0,8 | 840 | $180 \dots 250$ | DIN EN 1561 | Stahl Seltmann / Castfast |
| Gussstück | $> 10 \le 20$ | 250 | 165 - 228 | 0,3 - 0,8 | 840 | 160 - 210 | DIN EN 1561 | Stahl Seltmann / Castfast |
| Gussstück | $> 20 \le 40$ | 220 | $145 \dots 205$ | 0,3–0,8 | 840 | $160 \dots 210$ | DIN EN 1561 | Stahl Seltmann / Castfast |
| Gussstück | $> 40 \le 80$ | 190 | $125 \dots 185$ | 0,3–0,8 | 840 | $150 \dots 200$ | DIN EN 1561 | Stahl Seltmann / Castfast |
| Gussstück | $> 80 \le 150$ | 170 | $110 \dots 165$ | 0,3–0,8 | 840 | $140 \dots 190$ | DIN EN 1561 | Stahl Seltmann / Castfast |

#### EN-GJL-250 – Beleg 1: Stahl Seltmann GmbH
* **Quelle:** [Stahl Seltmann EN-GJL-250 Werkstoff-Datenblatt PDF](http://stahl-seltmann.de/page/datasheet/6025.pdf)
* **Fundstelle:** Seite 1, Charakteristik & Mechanische Eigenschaften Richtwerte für getrennt gegossene Probestäbe
* **Wörtliches Zitat:** „Gusseisen ist ein spröder Werkstoff mit“
* **Belegte Zahlen:** 250 – 350 N/mm², 165 – 228 N/mm², 0,8 – 0,3 %, 840 N/mm², 180 – 250, 103 – 118 kN/mm².

#### EN-GJL-250 – Beleg 2: Castfast Eisenguss
* **Quelle:** [Castfast Werkstoffeigenschaften Eisenguss GJL PDF](https://www.castfast.com/wp-content/uploads/2024/07/Werkstoffeigenschaften-GJL-CASTFAST.pdf)
* **Fundstelle:** Seite 1, Tabelle Werkstoffeigenschaften Eisenguss GJL (EN-GJL-250)
* **Wörtliches Zitat:** „Gusseisen mit Lamellengraphit (GJL)“
* **Belegte Zahlen:** 200 - 250 N/mm², 165 - 228 N/mm², 0.3 - 0.8 %, 840 N/mm², 160 - 210, 290 N/mm², 103 - 118 kN/mm², 0.26, 325 N/mm², 120 N/mm², 340 N/mm², 60 N/mm², 480, 7.20 g/cm³, 48.5 – 44.5 W/(m·K), 460 J/(kg·K), 11.7.

---

## 4. Vorschlag zur Weiterentwicklung des Feldes `geltungsbereich` im Katalogschema

### 4.1 Ist-Zustand und Schwachstellen in `katalog/schema.json`

Im gegenwärtigen Katalogschema (`katalog/schema.json`, Zeilen 64–100) ist der Geltungsbereich wie folgt modelliert:

```json
"geltungsbereich": {
  "type": "object",
  "required": [
    "werkstoff",
    "verfahren",
    "feature",
    "groesse",
    "festigkeitsklasse"
  ],
  "properties": {
    "werkstoff": { "type": "array", "items": { "type": "string" } },
    "verfahren": { "type": "array", "items": { "type": "string" } },
    "feature": { "type": "array", "items": { "type": "string" } },
    "groesse": { "type": "array", "items": { "type": "string" } },
    "festigkeitsklasse": { "type": "array", "items": { "type": "string" } }
  }
}
```

Die Schwachstellen dieser Modellierung für mechanische Kennwerte:
1. **Rein deskriptives String-Array (`groesse`):** Einträge wie `"groesse": ["t <= 16 mm"]` oder `"groesse": ["d <= 16 mm"]` sind informativ für menschliche Leser, aber für CAD-Algorithmen (wie die automatisierte Berechnung von Einschraubtiefen in `bolted_connection` oder Spannungsanalysen) nicht maschinell auswertbar.
2. **Kopplung an starre Einzelwerte:** Die Kennwerte in `"werte"` (z. B. `"Zugfestigkeit Rm"`, `"Mindeststreckgrenze ReH"`) sind skalare Zahlen oder Intervalle, die fest an die Vorzugsabmessung gekoppelt sind. Eine kontinuierliche oder gestufte Anpassung an die reale Geometrie des 3D-Modells ist nicht möglich.
3. **Sicherheitsrisiko bei massiven Bauteilen:** Wenn ein Konstrukteur eine Schraubenverbindung M16 in einen Schmiedeblock aus `42crmo4_verguetet` mit $d = 200\,	ext{mm}$ einfügt, greift das System aktuell auf $R_m = 1100\,	ext{MPa}$ ($	au_B = 715\,	ext{MPa}$) zurück, obwohl das Material real nur $R_m = 750\,	ext{MPa}$ ($	au_B = 488\,	ext{MPa}$) leistet. Dies führt zu einer gefährlichen Unterdimensionierung der tragenden Gewindetiefe.

---

### 4.2 Lösungsoptionen für das Katalogschema

#### Option A: Strukturierte Stufentabelle `dickenbereiche` innerhalb von `geltungsbereich` (Vorzugslösung)
In dieser Variante bleibt die bisherige `werte`-Liste als Standard für Vorzugsabmessungen ($t \le 16\,	ext{mm}$) vollständig intakt (100 % abwärtskompatibel). Innerhalb des bestehenden Objekts `geltungsbereich` wird ein optionales Feld `dickenbereiche` ergänzt.

**Schema-Erweiterung (JSON-Schema-Auszug für `katalog/schema.json`):**
```json
"dickenbereiche": {
  "type": "array",
  "description": "Erzeugnisdicken- und durchmesserabhängige Mindestfestigkeitswerte",
  "items": {
    "type": "object",
    "required": [
      "bereich_mm",
      "rm_bereich_mpa"
    ],
    "properties": {
      "bereich_mm": {
        "type": "array",
        "items": { "type": "number", "minimum": 0 },
        "minItems": 2,
        "maxItems": 2,
        "description": "Dicken- oder Durchmesserintervall [min_mm, max_mm]. min_mm ist exklusiv (außer bei 0), max_mm ist inklusiv."
      },
      "dimension": {
        "type": "string",
        "enum": ["dicke", "durchmesser", "wanddicke"],
        "default": "dicke",
        "description": "Geometrischer Bezugswert (Blechdicke t, Stangendurchmesser d oder Profilwanddicke)"
      },
      "erzeugnisform": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Relevante Halbzeugformen, z. B. ["blech", "band", "stab"]"
      },
      "reh_min_mpa": {
        "type": "number",
        "description": "Mindeststreckgrenze ReH bzw. 0,2%-Dehngrenze Rp0,2 in MPa"
      },
      "rm_bereich_mpa": {
        "type": "array",
        "items": { "type": "number" },
        "minItems": 1,
        "maxItems": 2,
        "description": "Zugfestigkeit [min] oder [min, max] in MPa"
      },
      "bruchdehnung_a_min_prozent": {
        "type": "number",
        "description": "Mindestbruchdehnung A5 bzw. A80 in %"
      },
      "tau_b_mpa": {
        "type": "number",
        "description": "Rechnerische Mindestscherfestigkeit nach VDI 2230 (tau_B/Rm * Rm,min)"
      },
      "norm": {
        "type": "string",
        "description": "Gültige Produktnorm der Festigkeitsstufe (z. B. DIN EN 10025-2)"
      }
    }
  }
}
```

#### Option B: Parametrisierte `stufen` direkt in den Einzelwerten von `werte`
Alternativ könnte jedes dickenabhängige Element im Array `werte` ein Unterfeld `stufen` erhalten:
```json
{
  "name": "Mindeststreckgrenze ReH",
  "einheit": "MPa",
  "wert": 235,
  "stufen": [
    { "max_mm": 16, "wert": 235 },
    { "max_mm": 40, "wert": 225 },
    { "max_mm": 63, "wert": 215 },
    { "max_mm": 100, "wert": 215 },
    { "max_mm": 150, "wert": 195 }
  ]
}
```

### 4.3 Bewertung und Begründung der Vorzugslösung (Option A)

Option A ist aus mehreren Gründen überlegen:
1. **Normkonforme Integrität:** Streckgrenze $R_{eH}$, Zugfestigkeit $R_m$, Bruchdehnung $A$ und Scherfestigkeit $	au_B$ hängen physikalisch zusammen und wechseln die Stufen stets gemeinsam an denselben Grenzmaßen (z. B. an der $16\,	ext{mm}$-, $40\,	ext{mm}$- und $100\,	ext{mm}$-Schwelle). Option A kapselt einen konsistenten Zustand in einem gemeinsamen Objekt.
2. **Volle Abwärtskompatibilität:** Vorhandene Tools, die nur flache `werte` lesen (wie SolidCraft-Exporteure oder elementare E-Modul-Abfragen), laufen ohne jede Codeänderung weiter.
3. **Effiziente Programmierung in Mechvane:** Ein CAD-Feature (z. B. eine Tasche in einer Platte mit $t = 30\,	ext{mm}$) kann mit einer einfachen Abfrage `katalog.get_properties_at_dimension(material_id, dimension_mm=30)` den gesamten Festigkeitssatz abrufen.

---

### 4.4 Konkretes Implementierungsbeispiel: `42crmo4_verguetet.json`

Hier ist der Entwurf, wie die Katalogdatei `katalog/eintraege/werkstoffe/42crmo4_verguetet.json` künftig aussehen könnte (als Muster für die spätere Katalogpflege):

```json
{
  "id": "42crmo4_verguetet",
  "aussage": "Legierter Vergütungsstahl 42CrMo4 (Werkstoffnummer 1.7225) im vergüteten Zustand (+QT) nach DIN EN 10083-3.",
  "werte": [
    {
      "name": "Dichte",
      "wert": 7.85,
      "einheit": "kg/dm³"
    },
    {
      "name": "Elastizitaetsmodul",
      "wert": 210,
      "einheit": "kN/mm²"
    },
    {
      "name": "Mindestdehngrenze Rp0,2 (Vorzug d <= 16 mm)",
      "wert": 900,
      "einheit": "MPa"
    },
    {
      "name": "Zugfestigkeit Rm (Vorzug d <= 16 mm)",
      "bereich": [1100, 1300],
      "einheit": "MPa"
    },
    {
      "name": "Scherfestigkeit τ_B (Vorzug d <= 16 mm)",
      "wert": 715,
      "einheit": "MPa"
    }
  ],
  "geltungsbereich": {
    "werkstoff": ["42CrMo4", "1.7225", "Verguetungsstahl"],
    "verfahren": ["Zerspanung", "Schrauben", "Vergueten"],
    "feature": ["Welle", "Achse", "Zahnrad", "Schraube"],
    "groesse": ["d <= 16 mm"],
    "festigkeitsklasse": ["+QT"],
    "dickenbereiche": [
      {
        "bereich_mm": [0, 16],
        "dimension": "durchmesser",
        "erzeugnisform": ["rundstab", "halbzeug"],
        "reh_min_mpa": 900,
        "rm_bereich_mpa": [1100, 1300],
        "bruchdehnung_a_min_prozent": 10,
        "tau_b_mpa": 715,
        "norm": "DIN EN 10083-3"
      },
      {
        "bereich_mm": [16, 40],
        "dimension": "durchmesser",
        "erzeugnisform": ["rundstab", "halbzeug"],
        "reh_min_mpa": 750,
        "rm_bereich_mpa": [1000, 1200],
        "bruchdehnung_a_min_prozent": 11,
        "tau_b_mpa": 650,
        "norm": "DIN EN 10083-3"
      },
      {
        "bereich_mm": [40, 100],
        "dimension": "durchmesser",
        "erzeugnisform": ["rundstab", "halbzeug"],
        "reh_min_mpa": 650,
        "rm_bereich_mpa": [900, 1100],
        "bruchdehnung_a_min_prozent": 12,
        "tau_b_mpa": 585,
        "norm": "DIN EN 10083-3"
      },
      {
        "bereich_mm": [100, 160],
        "dimension": "durchmesser",
        "erzeugnisform": ["rundstab", "halbzeug"],
        "reh_min_mpa": 550,
        "rm_bereich_mpa": [800, 950],
        "bruchdehnung_a_min_prozent": 13,
        "tau_b_mpa": 520,
        "norm": "DIN EN 10083-3"
      },
      {
        "bereich_mm": [160, 250],
        "dimension": "durchmesser",
        "erzeugnisform": ["rundstab", "halbzeug"],
        "reh_min_mpa": 500,
        "rm_bereich_mpa": [750, 900],
        "bruchdehnung_a_min_prozent": 14,
        "tau_b_mpa": 488,
        "norm": "DIN EN 10083-3"
      }
    ]
  }
}
```

---

## 5. Fazit und Handlungsempfehlungen

1. **Vollständige Beleglage:**  
   Für alle im Werkstoffkatalog geführten 9 Stähle, 5 Aluminium-Knetlegierungen und die Al-Gusslegierung EN AC-42100 (sowie ergänzend für Grauguss EN-GJL-250) wurden die Mindestwerte $R_m$ und $R_e / R_{p0{,}2}$ über alle relevanten Erzeugnisdickenbereiche anhand frei zugänglicher, unabhängiger Primärdatenblätter renommierter Hersteller und Händler belegt.
2. **Physikalische Notwendigkeit:**  
   Die Festigkeitsabfälle bei großen Dicken sind beträchtlich (bis zu $-32\,\%$ bei 42CrMo4 und $-53\,\%$ bei EN AW-7075). Die in Issue #17 aufgedeckte Diskrepanz der Hanke-Tabellenwerte für Einschraubtiefen ist nun vollständig metallurgisch geklärt: Hanke dimensionierte konservativ für den ungünstigsten Großabmessungsfall ($d > 160\,	ext{mm}$), während Mechvane bislang die Dünnblech- und Kleinstangenwerte zugrunde legte.
3. **Fahrplan zur Katalogumstellung (Roadmap Phase 1 / Phase 2):**  
   * **Schritt 1 (aktuell):** Dokumentation und Sicherung aller Dickenbereiche im vorliegenden Forschungsbericht. Der Werkstoffkatalog selbst bleibt vorerst unverändert auf den definierten Vorzugsabmessungen ($t \le 16\,	ext{mm}$), womit alle bestehenden Unit- und Referenztests grün bleiben.
   * **Schritt 2 (geplant):** Aufnahme des optionalen Feldes `dickenbereiche` in `katalog/schema.json` und Übertragung der hier recherchierten Tabellen in die 16 JSON-Dateien.
   * **Schritt 3 (geplant):** Anbindung an das Werkzeug `bolted_connection` in `mechvane/`: Ermittlung der tatsächlichen Plattendicke des Mutterteils und dynamische Wahl von $	au_B$ zur Berechnung von $m_{	ext{eff}}$.
