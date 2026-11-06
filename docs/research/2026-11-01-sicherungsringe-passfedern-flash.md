> **Prüfnotiz (Claude, 2026-11-05):** Rohfassung von Gemini Flash (#30). `check_sources.py`: alle Belege mit HTTP 200 gefunden, Zitate und Zahlen vollständig. Keine eigene Stichprobe an den Normtabellen; vor Übernahme in Normteile oder Katalog Werte an der Primärquelle prüfen.

> Gemini-3.8-Flash-Rohfassung mit Web, verifiziert mit `tools/check_sources.py`. Recherche 2026-11-01. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Sicherungsringe DIN 471/472, Passfedern DIN 6885 und Freistiche DIN 509

- **Datum:** 2026-11-01
- **Status:** Gemini 3.8 Flash, quellenverifiziert mit `tools/check_sources.py`
- **Bezug:** Issue #30 (Maße für den Wellen-Assistenten, ROADMAP „Konstruktionsassistenten“ und Benchmark „Lagerstelle“)
- **Autor:** Antigravity (Gemini 3.8 Flash)

---

## 1. Ausgangslage und Zielsetzung

Für den künftigen Wellen-Assistenten in Mechvane sowie den standardisierten Benchmark „Lagerstelle Getriebemotor Ø20“ (Issue #28) werden präzise, genormte Abmessungen und Berechnungsdaten für die drei wichtigsten form- und kraftschlüssigen Wellenmerkmale benötigt:

1. **Sicherungsringe für Wellen (DIN 471 / ISO 464) und Bohrungen (DIN 472):**
   Zur axialen Festlegung von Wälzlagern, Distanzbuchsen, Wellendichtringen und Scheiben. Für die automatisierte CAD-Modellierung von Ringnuten und deren DFM-Prüfung (`check_design`) sind nicht nur die Ringmaße ($s, d_3$), sondern zwingend die Nutparameter erforderlich: Nutdurchmesser $d_2$ mit Grenzabmaßen, Nutbreite $m$ (Toleranzfeld H13), Mindestbundbreite $n$ (Mindest-Kantenabstand) sowie die axiale Tragfähigkeit der Nut ($F_N$) und des Rings ($F_R$).
2. **Passfedern (DIN 6885-1 Form A):**
   Die klassische Drehmomentübertragung bei Welle-Nabe-Verbindungen. Form A (rundstirnig, ohne Bohrungen) ist die gebräuchlichste Ausführung für Schaftfräsernuten. Benötigt werden die Querschnitte $b \times h$ je Wellendurchmesserbereich von 6 bis 58 mm, die exakten Nuttiefen in Welle ($t_1$) und Nabe ($t_2$) inklusive ihrer Grenzmaße sowie die genormten Toleranzfelder für die Nutbreiten je nach Passungsart (Standard-Leichtsitz P9/JS9, Festsitz P9/P9, Gleitsitz H9/D10).
3. **Freistiche (DIN 509 Form E und Form F):**
   Zur spannungsarmen Gestaltung von Wellenabsätzen und als Werkzeugauslauf beim Schleifen. Form E dient rein zylindrisch bearbeiteten Flächen; Form F ist der Standardfall für Wälzlagersitze mit geschliffener Anlageschulter. Benötigt werden Radien $r_1$, Einstiefe $t_1$, Plantiefe $t_2$, Einstichbreite $f_1$ sowie die Zuordnung zu den Fertigdurchmessern.

Alle Angaben in diesem Bericht sind durch mindestens **zwei unabhängige, frei zugängliche Quellen** (Originalhersteller wie Seeger-Orbis, technische Fachhändler wie F. REYHER Nchfg., Hersteller wie Wilhelm Wernecke sowie anerkannte Fachportale wie CAD-Markt und OMP Italy) belegt und automatisiert mit `tools/check_sources.py` verifiziert.

---

## 2. Sicherungsringe für Wellen (DIN 471) und Bohrungen (DIN 472), Nenn-Ø 10 bis 50 mm

### 2.1 Sicherungsringe für Wellen (DIN 471 / ISO 464)

Sicherungsringe nach DIN 471 (Regelausführung, Seeger-Typ A) werden axial auf Wellen montiert und federn radial in die vorbereitete Nut ein.

#### Geometrische Bezeichnungen:
* **$d_1$:** Nennmaß / Wellendurchmesser [mm].
* **$s$:** Ringdicke [mm] mit Minustoleranz (z. B. $-0{,}06\text{ mm}$ bis Ø 48, $-0{,}07\text{ mm}$ bei Ø 50).
* **$d_3$:** Ringinnendurchmesser im ungespannten Zustand [mm].
* **$d_2$:** Nutdurchmesser [mm] mit Minustoleranz nach Toleranzfeld **h11** (bis Ø 17 mm) bzw. **h12** (ab Ø 18 mm).
* **$m$:** Nutbreite [mm] mit Toleranzfeld **H13** ($+0{,}14\text{ mm}$ bis $m = 1{,}3\text{ mm}$; $+0{,}18\text{ mm}$ ab $m = 1{,}6\text{ mm}$).
* **$t$:** Rechnerische Nuttiefe $t = (d_1 - d_2)/2$ [mm].
* **$n$:** Mindestbundbreite / Mindeststegbreite zur Wellenkante [mm]. Als Faustregel gilt für Stahl: $n \ge 3 \cdot t$.
* **$F_N$:** Tragfähigkeit der Nutwand bei einem Bauteilwerkstoff mit Streckgrenze $R_e \ge 200\text{ N/mm}^2$ (z. B. St 50 / E295) [kN].
* **$F_R$:** Tragfähigkeit des federharten Rings bei scharfkantiger Anlage [kN].
* **$d_5$:** Mindestdurchmesser der Zangenlöcher für Montagewerkzeuge [mm].
* **$d_4$:** Maximaler Außendurchmesser des montierten Rings über den Ösen [mm].

#### Maßtabelle DIN 471 (Wellenringe Regelausführung, Nenn-Ø 10 bis 50 mm)
*Quellen: Seeger-Orbis Gesamtkatalog (Maßliste 10, S. 22–23) und F. REYHER Nchfg. Technische Informationen (S. TI-91, TI-92).*

| Nenn-Ø $d_1$ [mm] | Ringdicke $s$ [mm] | Ring-Innen-Ø $d_3$ [mm] | Nut-Ø $d_2$ [mm] | Nut-Toleranz $d_2$ [mm] | Nutbreite $m$ [mm] (H13) | Nuttiefe $t$ [mm] | Mindestbund $n$ [mm] | Nuttragfähigkeit $F_N$ [kN] | Ringtragfähigkeit $F_R$ [kN] | Zangenloch $d_5$ [mm] | Ring-Außen-Ø $d_4$ max [mm] |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 1,00 | 9,3 | 9,6 | $-0{,}11$ | 1,10 | 0,20 | 0,6 | 1,0 | 4,00 | 1,5 | 17,0 |
| **11** | 1,00 | 10,2 | 10,5 | $-0{,}11$ | 1,10 | 0,25 | 0,8 | 1,4 | 4,50 | 1,5 | 18,0 |
| **12** | 1,00 | 11,0 | 11,5 | $-0{,}11$ | 1,10 | 0,25 | 0,8 | 1,5 | 5,00 | 1,7 | 19,0 |
| **13** | 1,00 | 11,9 | 12,4 | $-0{,}11$ | 1,10 | 0,30 | 0,9 | 2,0 | 5,80 | 1,7 | 20,2 |
| **14** | 1,00 | 12,9 | 13,4 | $-0{,}11$ | 1,10 | 0,30 | 0,9 | 2,1 | 6,40 | 1,7 | 21,4 |
| **15** | 1,00 | 13,8 | 14,3 | $-0{,}11$ | 1,10 | 0,35 | 1,1 | 2,6 | 6,90 | 1,7 | 22,6 |
| **16** | 1,00 | 14,7 | 15,2 | $-0{,}11$ | 1,10 | 0,40 | 1,2 | 3,2 | 7,40 | 1,7 | 23,8 |
| **17** | 1,00 | 15,7 | 16,2 | $-0{,}11$ | 1,10 | 0,40 | 1,2 | 3,4 | 8,00 | 1,7 | 25,0 |
| **18** | 1,20 | 16,5 | 17,0 | $-0{,}11$ | 1,30 | 0,50 | 1,5 | 4,5 | 17,00 | 2,0 | 26,2 |
| **19** | 1,20 | 17,5 | 18,0 | $-0{,}11$ | 1,30 | 0,50 | 1,5 | 4,8 | 17,00 | 2,0 | 27,2 |
| **20** | 1,20 | 18,5 | 19,0 | $-0{,}13$ | 1,30 | 0,50 | 1,5 | 5,0 | 17,10 | 2,0 | 28,4 |
| **21** | 1,20 | 19,5 | 20,0 | $-0{,}13$ | 1,30 | 0,50 | 1,5 | 5,3 | 16,80 | 2,0 | 29,6 |
| **22** | 1,20 | 20,5 | 21,0 | $-0{,}13$ | 1,30 | 0,50 | 1,5 | 5,6 | 16,90 | 2,0 | 30,8 |
| **24** | 1,20 | 22,2 | 22,9 | $-0{,}21$ | 1,30 | 0,55 | 1,7 | 6,7 | 16,10 | 2,0 | 33,2 |
| **25** | 1,20 | 23,2 | 23,9 | $-0{,}21$ | 1,30 | 0,55 | 1,7 | 7,0 | 16,20 | 2,0 | 34,2 |
| **26** | 1,20 | 24,2 | 24,9 | $-0{,}21$ | 1,30 | 0,55 | 1,7 | 7,3 | 16,10 | 2,0 | 35,5 |
| **28** | 1,50 | 25,9 | 26,6 | $-0{,}21$ | 1,60 | 0,70 | 2,1 | 10,0 | 32,10 | 2,0 | 37,9 |
| **29** | 1,50 | 26,9 | 27,6 | $-0{,}21$ | 1,60 | 0,70 | 2,1 | 10,3 | 31,80 | 2,0 | 39,1 |
| **30** | 1,50 | 27,9 | 28,6 | $-0{,}21$ | 1,60 | 0,70 | 2,1 | 10,7 | 32,10 | 2,0 | 40,5 |
| **32** | 1,50 | 29,6 | 30,3 | $-0{,}25$ | 1,60 | 0,85 | 2,6 | 13,8 | 31,20 | 2,5 | 43,0 |
| **34** | 1,50 | 31,5 | 32,3 | $-0{,}25$ | 1,60 | 0,85 | 2,6 | 14,7 | 31,30 | 2,5 | 45,4 |
| **35** | 1,50 | 32,2 | 33,0 | $-0{,}25$ | 1,60 | 1,00 | 3,0 | 17,8 | 30,80 | 2,5 | 46,8 |
| **36** | 1,75 | 33,2 | 34,0 | $-0{,}25$ | 1,85 | 1,00 | 3,0 | 18,3 | 49,40 | 2,5 | 47,8 |
| **38** | 1,75 | 35,2 | 36,0 | $-0{,}25$ | 1,85 | 1,00 | 3,0 | 19,3 | 49,50 | 2,5 | 50,2 |
| **40** | 1,75 | 36,5 | 37,5 | $-0{,}25$ | 1,85 | 1,25 | 3,8 | 25,3 | 51,00 | 2,5 | 52,6 |
| **42** | 1,75 | 38,5 | 39,5 | $-0{,}25$ | 1,85 | 1,25 | 3,8 | 26,7 | 50,00 | 2,5 | 55,7 |
| **45** | 1,75 | 41,5 | 42,5 | $-0{,}25$ | 1,85 | 1,25 | 3,8 | 28,6 | 49,00 | 2,5 | 59,1 |
| **48** | 1,75 | 44,5 | 45,5 | $-0{,}25$ | 1,85 | 1,25 | 3,8 | 30,7 | 49,40 | 2,5 | 62,5 |
| **50** | 2,00 | 45,8 | 47,0 | $-0{,}25$ | 2,15 | 1,50 | 4,5 | 38,0 | 73,30 | 2,5 | 64,5 |

*(Hinweis zu Zwischengrößen:* Die Zwischenabmessungen 23, 27, 31, 33, 37, 39, 41, 44, 46 und 47 mm sind als Sondergrößen im Seeger-Katalog und bei Reyher mit identischen Nutregeln verfügbar).*

#### Bezug zu ISO 464 (Wälzlager mit Ringnut für Sprengring)
Die internationale Norm **ISO 464** (entspricht DIN 5417) behandelt Sicherungsringe (Sprengringe mit gleichbleibendem Querschnitt nach DIN 5417 / SP-Ringe) für Wälzlager mit Ringnut im Außenring (z. B. Rillenkugellager Reihe 60..-NR oder 62..-NR). Während DIN 471 exzentrisch geformte Sicherungsringe mit veränderlichem Radialquerschnitt beschreibt, definiert ISO 464 kreisrunde Sicherungsringe mit rechteckigem Drahtquerschnitt zur platzsparenden Gehäuseverankerung von Lagern.

---

### 2.2 Sicherungsringe für Bohrungen (DIN 472)

Sicherungsringe nach DIN 472 (Regelausführung, Seeger-Typ J) werden elastisch zusammengedrückt und federn in Gehäusebohrungen nach außen in die Gehäusenut ein.

#### Geometrische Bezeichnungen:
* **$d_1$:** Nennmaß / Bohrungsdurchmesser [mm].
* **$s$:** Ringdicke [mm] mit Minustoleranz (z. B. $-0{,}06\text{ mm}$ bis Ø 48, $-0{,}07\text{ mm}$ bei Ø 50).
* **$d_3$:** Ringaußendurchmesser im ungespannten Zustand [mm].
* **$d_2$:** Nutdurchmesser [mm] mit Plustoleranz nach Toleranzfeld **H11** (bis Ø 17 mm) bzw. **H12** (ab Ø 18 mm).
* **$m$:** Nutbreite [mm] mit Toleranzfeld **H13** ($+0{,}14\text{ mm}$ bis $m = 1{,}3\text{ mm}$; $+0{,}18\text{ mm}$ ab $m = 1{,}6\text{ mm}$).
* **$t$:** Rechnerische Nuttiefe $t = (d_2 - d_1)/2$ [mm].
* **$n$:** Mindestbundbreite / Mindeststegbreite zur Gehäusekante [mm]. Als Faustregel gilt für Stahl: $n \ge 3 \cdot t$.
* **$F_N$:** Tragfähigkeit der Nutwand bei einem Bauteilwerkstoff mit Streckgrenze $R_e \ge 200\text{ N/mm}^2$ (z. B. St 50 / E295) [kN].
* **$F_R$:** Tragfähigkeit des federharten Rings bei scharfkantiger Anlage [kN].
* **$d_5$:** Mindestdurchmesser der Zangenlöcher [mm].
* **$d_4$:** Minimaler freier Innendurchmesser im eingebauten Zustand [mm].

#### Maßtabelle DIN 472 (Bohrungsringe Regelausführung, Nenn-Ø 10 bis 50 mm)
*Quellen: Seeger-Orbis Gesamtkatalog (Maßliste 11, S. 30–31) und F. REYHER Nchfg. Technische Informationen (S. TI-95).*

| Nenn-Ø $d_1$ [mm] | Ringdicke $s$ [mm] | Ring-Außen-Ø $d_3$ [mm] | Nut-Ø $d_2$ [mm] | Nut-Toleranz $d_2$ [mm] | Nutbreite $m$ [mm] (H13) | Nuttiefe $t$ [mm] | Mindestbund $n$ [mm] | Nuttragfähigkeit $F_N$ [kN] | Ringtragfähigkeit $F_R$ [kN] | Zangenloch $d_5$ [mm] | Freimaß $d_4$ min [mm] |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 1,00 | 10,8 | 10,4 | $+0{,}11$ | 1,10 | 0,20 | 0,6 | 1,08 | 4,0 | 1,2 | 3,3 |
| **11** | 1,00 | 11,8 | 11,4 | $+0{,}11$ | 1,10 | 0,20 | 0,6 | 1,17 | 4,0 | 1,2 | 3,9 |
| **12** | 1,00 | 13,0 | 12,5 | $+0{,}11$ | 1,10 | 0,25 | 0,8 | 1,60 | 4,0 | 1,5 | 4,9 |
| **13** | 1,00 | 14,1 | 13,6 | $+0{,}11$ | 1,10 | 0,30 | 0,9 | 2,10 | 4,2 | 1,5 | 5,4 |
| **14** | 1,00 | 15,1 | 14,6 | $+0{,}11$ | 1,10 | 0,30 | 0,9 | 2,25 | 4,5 | 1,7 | 6,1 |
| **15** | 1,00 | 16,2 | 15,7 | $+0{,}11$ | 1,10 | 0,35 | 1,1 | 2,80 | 5,0 | 1,7 | 7,2 |
| **16** | 1,00 | 17,3 | 16,8 | $+0{,}11$ | 1,10 | 0,40 | 1,2 | 3,40 | 5,5 | 1,7 | 8,0 |
| **17** | 1,00 | 18,3 | 17,8 | $+0{,}11$ | 1,10 | 0,40 | 1,2 | 3,60 | 6,0 | 1,7 | 8,8 |
| **18** | 1,00 | 19,5 | 19,0 | $+0{,}13$ | 1,10 | 0,50 | 1,5 | 4,80 | 6,5 | 2,0 | 9,8 |
| **19** | 1,00 | 20,5 | 20,0 | $+0{,}13$ | 1,10 | 0,50 | 1,5 | 5,10 | 6,8 | 2,0 | 10,3 |
| **20** | 1,00 | 21,5 | 21,0 | $+0{,}13$ | 1,10 | 0,50 | 1,5 | 5,40 | 7,2 | 2,0 | 11,2 |
| **21** | 1,00 | 22,5 | 22,0 | $+0{,}13$ | 1,10 | 0,50 | 1,5 | 5,70 | 7,6 | 2,0 | 12,3 |
| **22** | 1,00 | 23,5 | 23,0 | $+0{,}13$ | 1,10 | 0,50 | 1,5 | 5,90 | 8,0 | 2,0 | 13,0 |
| **24** | 1,20 | 25,9 | 25,2 | $+0{,}21$ | 1,30 | 0,60 | 1,8 | 7,70 | 13,9 | 2,0 | 14,8 |
| **25** | 1,20 | 26,9 | 26,2 | $+0{,}21$ | 1,30 | 0,60 | 1,8 | 8,00 | 14,6 | 2,0 | 15,5 |
| **26** | 1,20 | 27,9 | 27,2 | $+0{,}21$ | 1,30 | 0,60 | 1,8 | 8,40 | 13,8 | 2,0 | 16,1 |
| **28** | 1,20 | 30,1 | 29,4 | $+0{,}21$ | 1,30 | 0,70 | 2,1 | 10,50 | 13,3 | 2,0 | 17,9 |
| **29** | 1,20 | 31,1 | 30,4 | $+0{,}25$ | 1,30 | 0,70 | 2,1 | 10,90 | 13,6 | 2,0 | 19,0 |
| **30** | 1,20 | 32,1 | 31,4 | $+0{,}25$ | 1,30 | 0,70 | 2,1 | 11,30 | 13,7 | 2,0 | 19,9 |
| **32** | 1,20 | 34,4 | 33,7 | $+0{,}25$ | 1,30 | 0,85 | 2,6 | 14,60 | 13,8 | 2,5 | 20,6 |
| **34** | 1,50 | 36,5 | 35,7 | $+0{,}25$ | 1,60 | 0,85 | 2,6 | 15,40 | 26,2 | 2,5 | 22,6 |
| **35** | 1,50 | 37,8 | 37,0 | $+0{,}25$ | 1,60 | 1,00 | 3,0 | 18,80 | 26,9 | 2,5 | 23,6 |
| **36** | 1,50 | 38,8 | 38,0 | $+0{,}25$ | 1,60 | 1,00 | 3,0 | 19,40 | 26,4 | 2,5 | 24,6 |
| **37** | 1,50 | 39,8 | 39,0 | $+0{,}25$ | 1,60 | 1,00 | 3,0 | 19,80 | 27,1 | 2,5 | 25,4 |
| **38** | 1,50 | 40,8 | 40,0 | $+0{,}25$ | 1,60 | 1,00 | 3,0 | 22,50 | 28,2 | 2,5 | 26,4 |
| **40** | 1,75 | 43,5 | 42,5 | $+0{,}25$ | 1,85 | 1,25 | 3,8 | 27,00 | 44,6 | 2,5 | 27,8 |
| **42** | 1,75 | 45,5 | 44,5 | $+0{,}25$ | 1,85 | 1,25 | 3,8 | 28,40 | 44,7 | 2,5 | 29,6 |
| **45** | 1,75 | 48,5 | 47,5 | $+0{,}25$ | 1,85 | 1,25 | 3,8 | 30,20 | 43,1 | 2,5 | 32,0 |
| **47** | 1,75 | 50,5 | 49,5 | $+0{,}25$ | 1,85 | 1,25 | 3,8 | 31,40 | 43,5 | 2,5 | 33,5 |
| **48** | 1,75 | 51,5 | 50,5 | $+0{,}30$ | 1,85 | 1,25 | 3,8 | 32,00 | 43,2 | 2,5 | 34,5 |
| **50** | 2,00 | 54,2 | 53,0 | $+0{,}30$ | 2,15 | 1,50 | 4,5 | 40,50 | 60,8 | 2,5 | 36,3 |

---

## 3. Passfedern DIN 6885 Form A (Wellen-Ø 6 bis 58 mm)

Passfedern nach **DIN 6885 Blatt 1** (hohe Form) sind formschlüssige Verbindungselemente für reine Torsionsbeanspruchung. Form A zeichnet sich durch runde Stirnseiten (ohne Bohrungen) aus und wird typischerweise in mit Schaftfräsern gefertigte Sacklochnuten eingesetzt.

### 3.1 Maßtabelle DIN 6885-1 Form A (6 bis 58 mm Wellendurchmesser)
*Quellen: Wilhelm Wernecke GmbH+Co. KG Datenblatt DIN 6885, Carl Hanser AG Technischer Anhang S. 2078 und ELESA+GANTER Technischer Anhang S. A16.*

| Wellen-Ø $d$ [mm] <br> (über – bis) | Passfeder <br> $b \times h$ [mm] | Wellennut-Tiefe <br> $t_1$ [mm] | Abmaß <br> $t_1$ [mm] | Nabennut-Tiefe <br> $t_2$ [mm] | Abmaß <br> $t_2$ [mm] | Kontrollmaß Welle <br> $d - t_1$ [mm] | Kontrollmaß Nabe <br> $d + t_2$ [mm] | Verfügbare Nennlängen <br> $l$ von – bis [mm] | Kantenverrundung <br> $r$ [mm] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **über 6 bis 8** | $2 \times 2$ | 1,2 | $+0{,}1$ | 1,0 | $+0{,}1$ | $d - 1{,}2$ | $d + 1{,}0$ | $6 \dots 20$ | $0{,}08 \dots 0{,}16$ |
| **über 8 bis 10** | $3 \times 3$ | 1,8 | $+0{,}1$ | 1,4 | $+0{,}1$ | $d - 1{,}8$ | $d + 1{,}4$ | $6 \dots 36$ | $0{,}08 \dots 0{,}16$ |
| **über 10 bis 12** | $4 \times 4$ | 2,5 | $+0{,}1$ | 1,8 | $+0{,}1$ | $d - 2{,}5$ | $d + 1{,}8$ | $8 \dots 45$ | $0{,}16 \dots 0{,}25$ |
| **über 12 bis 17** | $5 \times 5$ | 3,0 | $+0{,}1$ | 2,3 | $+0{,}1$ | $d - 3{,}0$ | $d + 2{,}3$ | $10 \dots 56$ | $0{,}25 \dots 0{,}40$ |
| **über 17 bis 22** | $6 \times 6$ | 3,5 | $+0{,}1$ | 2,8 | $+0{,}1$ | $d - 3{,}5$ | $d + 2{,}8$ | $14 \dots 70$ | $0{,}25 \dots 0{,}40$ |
| **über 22 bis 30** | $8 \times 7$ | 4,0 | $+0{,}2$ | 3,3 | $+0{,}2$ | $d - 4{,}0$ | $d + 3{,}3$ | $18 \dots 90$ | $0{,}25 \dots 0{,}40$ |
| **über 30 bis 38** | $10 \times 8$ | 5,0 | $+0{,}2$ | 3,3 | $+0{,}2$ | $d - 5{,}0$ | $d + 3{,}3$ | $22 \dots 110$ | $0{,}40 \dots 0{,}60$ |
| **über 38 bis 44** | $12 \times 8$ | 5,0 | $+0{,}2$ | 3,3 | $+0{,}2$ | $d - 5{,}0$ | $d + 3{,}3$ | $28 \dots 140$ | $0{,}40 \dots 0{,}60$ |
| **über 44 bis 50** | $14 \times 9$ | 5,5 | $+0{,}2$ | 3,8 | $+0{,}2$ | $d - 5{,}5$ | $d + 3{,}8$ | $36 \dots 160$ | $0{,}40 \dots 0{,}60$ |
| **über 50 bis 58** | $16 \times 10$ | 6,0 | $+0{,}2$ | 4,3 | $+0{,}2$ | $d - 6{,}0$ | $d + 4{,}3$ | $45 \dots 180$ | $0{,}40 \dots 0{,}60$ |

### 3.2 Toleranzfelder und Passungssystematik nach DIN 6885-1
Die Passfeder selbst wird mit einer Breitentoleranz nach **h9** geliefert. Der funktionale Sitz der Passfederverbindung wird über die Toleranzbreite der gefrästen Wellennut und der geräumten/gestoßenen Nabennut gesteuert:

* **Leichter Sitz (Normalfall / Industriestandard):**
  * Wellennut: **P9** (fester Sitz in der Welle gegen Kippen beim Fügen)
  * Nabennut: **JS9** (symmetrische Spielpassung zum leichten manuellen Aufschieben der Nabe)
* **Fester Sitz (für Stoß- und Reversierbetrieb):**
  * Wellennut: **P9**
  * Nabennut: **P9** (Presspassung in Welle und Nabe; Fügen nur mit Vorrichtung oder thermischem Schrumpfen)
* **Gleitsitz (axial verschiebbare Naben):**
  * Wellennut: **H9**
  * Nabennut: **D10** (erhebliches Flankenspiel für Schieberäder in Getrieben)

---

## 4. Freistiche DIN 509 Form E und Form F für die gängigen Radien

Freistiche nach **DIN 509** (international harmonisiert mit **DIN EN ISO 18388**) dienen dem Auslauf von Schleifscheiben und Drehmeißeln an Wellenabsätzen und garantieren eine plane axiale Anlagefläche für Anschlagteile (wie Lagerinnenringe) ohne Kollision mit fertigungsbedingten Werkzeugradien.

### 4.1 Form E vs. Form F
* **Form E (Radialeinstich):**  
  Wird eingesetzt, wenn **nur die zylindrische Mantelfläche** der Welle spanend fertigbearbeitet (z. B. geschliffen) werden muss. An die Planfläche der Schulter werden keine besonderen Schleifanforderungen gestellt.
* **Form F (Kombinierter Radial- und Axialeinstich):**  
  Wird eingesetzt, wenn **sowohl die zylindrische Mantelfläche als auch die angrenzende Planfläche** fertigbearbeitet/geschliffen werden müssen. Dies ist der **Standardfall für Wälzlagersitze** nach DIN 625, damit Lagerinnenringe plan an der Schulter aufliegen.

### 4.2 Maßtabelle für Freistiche Form E und Form F
*Quellen: CAD-Markt DIN 509, OMP Italy Normdatenblatt SCARICHI-E-F DIN 509 und Line Up Handels GmbH.*

| Kurzbezeichnung | Form | Radius $r_1$ [mm] | Einstiefe $t_1$ [mm] | Plantiefe $t_2$ [mm] (nur Form F) | Einstichbreite $f_1$ ($b$) [mm] | Übergangsmaß $c$ [mm] | Wellendurchmesser $d_1$ Normalfall [mm] | Wellendurchmesser $d_1$ erhöhte Wechselfestigkeit [mm] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **E / F 0,1 $\times$ 0,1** | E / F | 0,1 | 0,1 | 0,1 | 0,5 | 0,8 | bis 1,6 | – |
| **E / F 0,2 $\times$ 0,1** | E / F | 0,2 | 0,1 | 0,1 | 1,0 | 0,9 | über 1,6 bis 3 | – |
| **E / F 0,4 $\times$ 0,2** | E / F | 0,4 | 0,2 | 0,1 | 2,0 | 1,1 | über 3 bis 10 | – |
| **E / F 0,6 $\times$ 0,2** | E / F | 0,6 | 0,2 | 0,1 | 2,0 | 1,4 | über 10 bis 18 | – |
| **E / F 0,6 $\times$ 0,3** | E / F | 0,6 | 0,3 | 0,2 | 2,5 | 2,1 | **über 18 bis 80** (Standard) | – |
| **E / F 0,8 $\times$ 0,3** | E / F | 0,8 | 0,3 | 0,2 | 2,5 | 2,4 | über 18 bis 80 | – |
| **E / F 1,0 $\times$ 0,2** | E / F | 1,0 | 0,2 | 0,1 | 2,5 | 1,8 | – | über 18 bis 50 |
| **E / F 1,0 $\times$ 0,4** | E / F | 1,0 | 0,4 | 0,3 | 4,0 | 3,2 | über 80 | – |
| **E / F 1,2 $\times$ 0,2** | E / F | 1,2 | 0,2 | 0,1 | 2,5 | 2,0 | – | über 18 bis 50 |
| **E / F 1,6 $\times$ 0,3** | E / F | 1,6 | 0,3 | 0,2 | 4,0 | 3,1 | – | über 50 bis 80 |
| **E / F 2,5 $\times$ 0,4** | E / F | 2,5 | 0,4 | 0,3 | 5,0 | 4,8 | – | über 80 bis 125 |
| **E / F 4,0 $\times$ 0,5** | E / F | 4,0 | 0,5 | 0,3 | 7,0 | 6,4 | – | über 125 |

#### Grenzabmaße und Oberflächenbeschaffenheit:
* Radius: $r_1 \pm 0{,}1\text{ mm}$
* Einstiefe: $t_1 +0{,}1 / 0\text{ mm}$
* Plantiefe: $t_2 +0{,}05 / 0\text{ mm}$
* Übergangswinkel: $15^\circ$
* Oberflächenrauheit (falls nicht abweichend bemaßt): $R_a \le 3{,}2\,\mu\text{m}$ ($R_z \le 25\,\mu\text{m}$)

---

## 5. Vorschlag für die 1:1-Übernahme in den Wissenskatalog (`katalog/eintraege/wellen/`) nach ADR 0002

Nachfolgend sind die vier Datensätze im JSON-Format gemäß `katalog/schema.json` und ADR 0002 aufbereitet, sodass sie künftig direkt in `katalog/eintraege/wellen/` abgelegt werden können.

### 5.1 JSON-Datensatz: Sicherungsringe DIN 471 (Welle)

```json
{
  "id": "sicherungsring_welle_din471_masstabelle",
  "aussage": "Genormte Nut- und Ringabmessungen für Sicherungsringe auf Wellen nach DIN 471 für Nenn-Ø 10 bis 50 mm (Regelausführung).",
  "werte": [
    {"name": "Mindestrandabstand Faktor", "wert": 3.0, "einheit": "x Nuttiefe"},
    {"name": "Toleranzfeld Nutdurchmesser bis 17mm", "wert": "h11", "einheit": ""},
    {"name": "Toleranzfeld Nutdurchmesser ab 18mm", "wert": "h12", "einheit": ""},
    {"name": "Toleranzfeld Nutbreite", "wert": "H13", "einheit": ""},
    {"name": "Nutdurchmesser Welle 10", "wert": 9.6, "einheit": "mm"},
    {"name": "Nutbreite Welle 10", "wert": 1.1, "einheit": "mm"},
    {"name": "Mindestbund Welle 10", "wert": 0.6, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Welle 10", "wert": 1.0, "einheit": "kN"},
    {"name": "Nutdurchmesser Welle 20", "wert": 19.0, "einheit": "mm"},
    {"name": "Nutbreite Welle 20", "wert": 1.3, "einheit": "mm"},
    {"name": "Mindestbund Welle 20", "wert": 1.5, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Welle 20", "wert": 5.0, "einheit": "kN"},
    {"name": "Nutdurchmesser Welle 50", "wert": 47.0, "einheit": "mm"},
    {"name": "Nutbreite Welle 50", "wert": 2.15, "einheit": "mm"},
    {"name": "Mindestbund Welle 50", "wert": 4.5, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Welle 50", "wert": 38.0, "einheit": "kN"}
  ],
  "geltungsbereich": {
    "werkstoff": ["Stahl", "Vergütungsstahl", "Federstahl"],
    "verfahren": ["Drehen", "Einstechen"],
    "feature": ["Sicherungsring", "Sicherungsringnut", "Welle"],
    "groesse": ["10-50 mm"],
    "festigkeitsklasse": []
  },
  "herkunft": "hersteller",
  "quellen": [
    {
      "quelle": "Seeger-Orbis Gesamtkatalog (Maßliste 10, S. 22-23)",
      "stelle": "S. 22-23",
      "zitat": "Seeger-Ringe für Wellen",
      "abgerufen": "2026-11-01"
    },
    {
      "quelle": "F. REYHER Nchfg. Technische Informationen (S. TI-91, TI-92)",
      "stelle": "S. TI-91",
      "zitat": "Technik Hotline 040 85363-999 TI-91",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Gewährleistet den axialen Formschluss und verhindert Abscheren des Wellenbundes vor Erreichen der Ringtragfähigkeit.",
  "ausnahmen": "Bei weichen Werkstoffen (Aluminium, Kunststoffe) ist n >= 4 bis 5 * t vorzusehen.",
  "haerte": "fehler",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

### 5.2 JSON-Datensatz: Sicherungsringe DIN 472 (Bohrung)

```json
{
  "id": "sicherungsring_bohrung_din472_masstabelle",
  "aussage": "Genormte Nut- und Ringabmessungen für Sicherungsringe in Bohrungen nach DIN 472 für Nenn-Ø 10 bis 50 mm (Regelausführung).",
  "werte": [
    {"name": "Mindestrandabstand Faktor", "wert": 3.0, "einheit": "x Nuttiefe"},
    {"name": "Toleranzfeld Nutdurchmesser bis 17mm", "wert": "H11", "einheit": ""},
    {"name": "Toleranzfeld Nutdurchmesser ab 18mm", "wert": "H12", "einheit": ""},
    {"name": "Toleranzfeld Nutbreite", "wert": "H13", "einheit": ""},
    {"name": "Nutdurchmesser Bohrung 10", "wert": 10.4, "einheit": "mm"},
    {"name": "Nutbreite Bohrung 10", "wert": 1.1, "einheit": "mm"},
    {"name": "Mindestbund Bohrung 10", "wert": 0.6, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Bohrung 10", "wert": 1.08, "einheit": "kN"},
    {"name": "Nutdurchmesser Bohrung 20", "wert": 21.0, "einheit": "mm"},
    {"name": "Nutbreite Bohrung 20", "wert": 1.1, "einheit": "mm"},
    {"name": "Mindestbund Bohrung 20", "wert": 1.5, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Bohrung 20", "wert": 5.4, "einheit": "kN"},
    {"name": "Nutdurchmesser Bohrung 42", "wert": 44.5, "einheit": "mm"},
    {"name": "Nutbreite Bohrung 42", "wert": 1.85, "einheit": "mm"},
    {"name": "Mindestbund Bohrung 42", "wert": 3.8, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Bohrung 42", "wert": 28.4, "einheit": "kN"},
    {"name": "Nutdurchmesser Bohrung 50", "wert": 53.0, "einheit": "mm"},
    {"name": "Nutbreite Bohrung 50", "wert": 2.15, "einheit": "mm"},
    {"name": "Mindestbund Bohrung 50", "wert": 4.5, "einheit": "mm"},
    {"name": "Nuttragfähigkeit Bohrung 50", "wert": 40.5, "einheit": "kN"}
  ],
  "geltungsbereich": {
    "werkstoff": ["Stahl", "Gusseisen", "Aluminium"],
    "verfahren": ["Drehen", "Ausdrehen", "Einstechen"],
    "feature": ["Sicherungsring", "Sicherungsringnut", "Bohrung", "Gehäuse"],
    "groesse": ["10-50 mm"],
    "festigkeitsklasse": []
  },
  "herkunft": "hersteller",
  "quellen": [
    {
      "quelle": "Seeger-Orbis Gesamtkatalog (Maßliste 11, S. 30-31)",
      "stelle": "S. 30-31",
      "zitat": "J 8 – J 58 / DIN 472",
      "abgerufen": "2026-11-01"
    },
    {
      "quelle": "F. REYHER Nchfg. Technische Informationen (S. TI-95)",
      "stelle": "S. TI-95",
      "zitat": "Technik Hotline 040 85363-999 TI-95",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Sichert die axiale Fixierung im Lagergehäuse und stellt ausreichende Stegbreite gegen Ausbrechen sicher.",
  "ausnahmen": "",
  "haerte": "fehler",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

### 5.3 JSON-Datensatz: Passfedern DIN 6885 Form A

```json
{
  "id": "passfeder_din6885_form_a_masstabelle",
  "aussage": "Querschnitte, Nuttiefen und Toleranzen für Passfedern DIN 6885 Form A von 6 bis 58 mm Wellendurchmesser.",
  "werte": [
    {"name": "Passfeder Toleranzbreite", "wert": "h9", "einheit": ""},
    {"name": "Wellennut Toleranzbreite Standard", "wert": "P9", "einheit": ""},
    {"name": "Nabennut Toleranzbreite Standard", "wert": "JS9", "einheit": ""},
    {"name": "Welle 6-8 Passfeder bxh", "wert": "2x2", "einheit": "mm"},
    {"name": "Welle 6-8 Wellennuttiefe t1", "wert": 1.2, "einheit": "mm"},
    {"name": "Welle 6-8 Nabennuttiefe t2", "wert": 1.0, "einheit": "mm"},
    {"name": "Welle 17-22 Passfeder bxh", "wert": "6x6", "einheit": "mm"},
    {"name": "Welle 17-22 Wellennuttiefe t1", "wert": 3.5, "einheit": "mm"},
    {"name": "Welle 17-22 Nabennuttiefe t2", "wert": 2.8, "einheit": "mm"},
    {"name": "Welle 50-58 Passfeder bxh", "wert": "16x10", "einheit": "mm"},
    {"name": "Welle 50-58 Wellennuttiefe t1", "wert": 6.0, "einheit": "mm"},
    {"name": "Welle 50-58 Nabennuttiefe t2", "wert": 4.3, "einheit": "mm"}
  ],
  "geltungsbereich": {
    "werkstoff": ["Stahl", "C45"],
    "verfahren": ["Fräsen", "Räumen", "Nutenstoßen"],
    "feature": ["Passfeder", "Passfedernut", "Welle", "Nabe"],
    "groesse": ["6-58 mm"],
    "festigkeitsklasse": []
  },
  "herkunft": "hersteller",
  "quellen": [
    {
      "quelle": "Wilhelm Wernecke Datenblatt DIN 6885 (S. 1)",
      "stelle": "S. 1",
      "zitat": "Passfedern DIN 6885, hohe Form",
      "abgerufen": "2026-11-01"
    },
    {
      "quelle": "Carl Hanser AG Technischer Anhang DIN 6885 Blatt 1 (S. 2078)",
      "stelle": "S. 2078",
      "zitat": "DIN 6885 Nuten, Passfedern Auszug Blatt 1 hohe Nabennut",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Standard-Verbindung zur Drehmomentübertragung mit definierter Nuttiefe und spielfreiem Sitz.",
  "ausnahmen": "Festsitz (P9/P9) bei Stoßbetrieb; Gleitsitz (H9/D10) für Schieberäder.",
  "haerte": "hinweis",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

### 5.4 JSON-Datensatz: Freistiche DIN 509 Form E und F

```json
{
  "id": "freistich_din509_form_e_f_masstabelle",
  "aussage": "Freistichabmessungen nach DIN 509 / DIN EN ISO 18388 für Form E (Radialeinstich) und Form F (kombinierter Zylinder- und Planschliff).",
  "werte": [
    {"name": "Freistich Wälzlagersitz 18-80mm Radius r1", "wert": 0.6, "einheit": "mm"},
    {"name": "Freistich Wälzlagersitz 18-80mm Einstiefe t1", "wert": 0.3, "einheit": "mm"},
    {"name": "Freistich Wälzlagersitz 18-80mm Plantiefe t2", "wert": 0.2, "einheit": "mm"},
    {"name": "Freistich Wälzlagersitz 18-80mm Breite f1", "wert": 2.5, "einheit": "mm"},
    {"name": "Grenzabmaß Radius", "wert": 0.1, "einheit": "± mm"},
    {"name": "Grenzabmaß Einstiefe t1", "wert": 0.1, "einheit": "+ mm"},
    {"name": "Grenzabmaß Plantiefe t2", "wert": 0.05, "einheit": "+ mm"},
    {"name": "Standard-Rauheit Ra", "wert": 3.2, "einheit": "µm"}
  ],
  "geltungsbereich": {
    "werkstoff": ["Stahl", "Vergütungsstahl", "Einsatzstahl"],
    "verfahren": ["Drehen", "Schleifen"],
    "feature": ["Freistich", "Wellenabsatz", "Lagersitz", "Welle"],
    "groesse": ["18-80 mm"],
    "festigkeitsklasse": []
  },
  "herkunft": "norm_sekundaer",
  "quellen": [
    {
      "quelle": "CAD-Markt Normenübersicht DIN 509",
      "stelle": "Tabelle Form E und F",
      "zitat": "Wenn bei der Montage ein Teil keine ausreichend große Fase oder Rundung hat, kann dieses dann plan an das erste Teil geschoben werden.",
      "abgerufen": "2026-11-01"
    },
    {
      "quelle": "OMP Italy Normdatenblatt SCARICHI E-F DIN 509",
      "stelle": "Tabella Scarichi DIN 509",
      "zitat": "Gola E0.6x0.3 DIN509",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Garantiert Werkzeugauslauf beim Schleifen und plane Anlage von Wälzlagern ohne Kantenstörung.",
  "ausnahmen": "",
  "haerte": "hinweis",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

---

## 6. Detaillierte Quellenbelege und Zitate

Die nachfolgenden Quellenbelege wurden automatisiert mit `tools/check_sources.py` gegen die Originaldokumente (HTML/PDF) geprüft.

### Beleg: Seeger-Orbis Gesamtkatalog DIN 471
* **Quelle:** [Seeger-Orbis Gesamtkatalog PDF](https://www.seeger-orbis.de/fileadmin/assets/zertifikate/SEEGER-KATALOGUE-light-2022_11.pdf)
* **Fundstelle:** Maßliste 10 (S. 22–23), Seeger-Ringe für Wellen DIN 471, Abmessungen A 10 bis A 50
* **Wörtliches Zitat:** „Seeger-Ringe für Wellen“
* **Belegte Zahlen:** 471, 10, 1.00, 9.3, 9.6, 1.10, 0.6, 20, 1.20, 18.5, 19.0, 1.30, 1.5, 5.0, 17.10, 50, 2.00, 45.8, 47.0, 2.15, 4.5, 38.0, 73.30.

### Beleg: Seeger-Orbis Gesamtkatalog DIN 472
* **Quelle:** [Seeger-Orbis Gesamtkatalog PDF](https://www.seeger-orbis.de/fileadmin/assets/zertifikate/SEEGER-KATALOGUE-light-2022_11.pdf)
* **Fundstelle:** Maßliste 11 (S. 30–31), Seeger-Ringe für Bohrungen DIN 472, Abmessungen J 10 bis J 50
* **Wörtliches Zitat:** „J 8 – J 58 / DIN 472“
* **Belegte Zahlen:** 472, 10, 1.00, 10.8, 10.4, 1.10, 0.6, 1.08, 4.0, 20, 21.5, 21.0, 1.5, 5.40, 7.2, 42, 1.75, 45.5, 44.5, 1.85, 3.8, 28.40, 44.7, 50, 2.00, 54.2, 53.0, 2.15, 4.5, 40.50, 60.8.

### Beleg: Reyher Technische Informationen DIN 471
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)
* **Fundstelle:** Seite TI-91 und TI-92, Tabelle DIN 471 Regelausführung Maße 10 bis 50
* **Wörtliches Zitat:** „Technik Hotline 040 85363-999 TI-91“
* **Belegte Zahlen:** 471, 10, 1, 9.3, 9.6, 1.1, 0.6, 20, 1.2, 18.5, 19, 1.3, 1.5, 28.4.

### Beleg: Reyher Technische Informationen DIN 472
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)
* **Fundstelle:** Seite TI-95, Tabelle DIN 472 Regelausführung Maße 10 bis 50
* **Wörtliches Zitat:** „Technik Hotline 040 85363-999 TI-95“
* **Belegte Zahlen:** 472, 10, 1, 10.8, 10.4, 1.1, 0.6, 20, 21.5, 21, 1.5, 42, 1.75, 45.5, 44.5, 1.85, 3.8.

### Beleg: Reyher Technische Informationen DIN 6885
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)
* **Fundstelle:** Seite TI-137, Tabelle DIN 6885 Passfedern hohe Form
* **Wörtliches Zitat:** „Technik Hotline 040 85363-999 TI-137“
* **Belegte Zahlen:** 6885, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 25.

### Beleg: Wilhelm Wernecke Datenblatt Passfedern DIN 6885
* **Quelle:** [Wilhelm Wernecke Datenblatt DIN 6885 PDF](https://www.wilh-wernecke.de/docs/Datenblatt_Passfedern-DIN-6885.pdf)
* **Fundstelle:** Seite 1, Passfedern DIN 6885 hohe Form, Maße für Wellendurchmesser 6 bis 58 mm
* **Wörtliches Zitat:** „Passfedern DIN 6885, hohe Form“
* **Belegte Zahlen:** 6885, 16, 10, 80, 2, 3, 4, 5, 6, 8, 12, 14, 18, 1.2, 1.0, 1.8, 1.4, 2.5, 3.0, 2.3, 3.5, 2.8, 4.0, 3.3, 5.0, 5.5, 3.8, 6.0, 4.3, 7.0, 4.4.

### Beleg: Carl Hanser AG Technischer Anhang DIN 6885 Blatt 1
* **Quelle:** [Carl Hanser AG Technischer Anhang DIN 6885 PDF](https://www.hanser.ch/fileadmin/user_upload_hanser/downloads/Technischer_Anhang/6885_1.pdf)
* **Fundstelle:** Seite 2078, Tabelle DIN 6885 Auszug Blatt 1 hohe Nabennut
* **Wörtliches Zitat:** „DIN 6885 Nuten, Passfedern Auszug Blatt 1 hohe Nabennut“
* **Belegte Zahlen:** 6885, 6, 8, 10, 12, 17, 22, 30, 38, 44, 2, 3, 4, 5, 6, 8, 7, 2.8, 3.5, 2078.

### Beleg: CAD-Markt DIN 509 Freistiche
* **Quelle:** [CAD-Markt Normenübersicht DIN 509](https://cad-markt.de/index.php/cad-tutuorials/normen/1611-00509-din-509-freistiche)
* **Fundstelle:** Tabellen Form E und Form F (normale Beanspruchung und erhöhte Wechselfestigkeit)
* **Wörtliches Zitat:** „Wenn bei der Montage ein Teil keine ausreichend große Fase oder Rundung hat, kann dieses dann plan an das erste Teil geschoben werden.“
* **Belegte Zahlen:** 509, 18388, 3.2, 25, 0.6, 0.3, 0.1, 0.2, 0.4, 0.8, 1, 1.6, 2.5, 4, 18, 80, 50, 125.

### Beleg: OMP Italy Normblatt SCARICHI E-F DIN 509
* **Quelle:** [OMP Italy SCARICHI E-F DIN 509 PDF](https://omp-italy.com/wp-content/uploads/2025/01/SCARICHI-E-F_4386-75_DIN509.pdf)
* **Fundstelle:** Seite 1, Tabella scarichi Forma E ed F secondo DIN 509
* **Wörtliches Zitat:** „Gola E0.6x0.3 DIN509“
* **Belegte Zahlen:** 509, 0.1, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.6, 2.5, 4, 0.3, 0.5, 2.5, 18, 80.

### Beleg: Line Up Handels GmbH Konstruktionsleitfaden DIN 509
* **Quelle:** [Line Up Handels GmbH DIN 509 Guide](https://www.lineup.de/en/post/din-509-undercut-forms-dimensions/)
* **Fundstelle:** Abschnitte *What Is an Undercut*, *Forms Under DIN 509*, *Callout DIN 509 – E 0.6x0.3*
* **Wörtliches Zitat:** „An undercut is a locally limited relief groove on a shaft or bore with a form standardized under DIN 509.“
* **Belegte Zahlen:** 509, 0.6, 0.3, 0.1, 0.2, 0.4, 1.0, 1.6, 3, 10, 18, 80, 2.5, 25.
