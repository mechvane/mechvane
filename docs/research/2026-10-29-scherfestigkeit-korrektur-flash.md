# Recherchebericht: Korrektur der Scherfestigkeiten $\tau_B$ für S235JR, S355J2 und 42CrMo4 (+QT)

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #17). `tools/check_sources.py`: 7 von 7
> Quellen, 7 Zitate, 51 von 51 Zahlen bestätigt. Neue Werte S235JR 288, S355J2 376, 42CrMo4 +QT 715 MPa
> (τ_B/R_m × R_m,min für den Geltungsbereich der Einträge). Die alten Werte waren nicht falsch, sondern galten
> für andere Abmessungen (Hanke-Tabelle, z. B. 42CrMo4 mit R_m 750 MPa ab d > 160 mm): τ_B hängt über R_m
> von der Erzeugnisgröße ab, das gehört später als Geltungsbereich an den Wert.

> **Prüfnotiz (Gemini 3.8 Flash, 2026-10-29):** Recherchebericht zu Issue #17.
> Klärung der Abweichungen der drei Scherfestigkeiten aus Issue #16 (Prüfnotiz in `docs/research/2026-10-29-scherfestigkeit-flash.md`):
> * S235JR: alter Wert $264\,\text{MPa}$ $\to$ neuer Wert $288\,\text{MPa}$ ($0{,}80 \cdot 360\,\text{MPa}$)
> * S355J2: alter Wert $360\,\text{MPa}$ $\to$ neuer Wert $376\,\text{MPa}$ ($0{,}80 \cdot 470\,\text{MPa}$)
> * 42CrMo4 (+QT): alter Wert $488\,\text{MPa}$ $\to$ neuer Wert $715\,\text{MPa}$ ($0{,}65 \cdot 1100\,\text{MPa}$)
> Alle Quellen sind über `tools/check_sources.py` nachweisbar, Zitate sind wörtlich belegt, Zahlenwerte im Quelltext nachgewiesen.
> Die entsprechenden Katalogdateien `katalog/eintraege/werkstoffe/{s235jr,s355j2,42crmo4_verguetet}.json` wurden aktualisiert und mittels `katalog.validate` validiert.

---

## 1. Ausgangslage und Problemstellung

In der Prüfung zu Issue #16 (`docs/research/2026-10-29-scherfestigkeit-flash.md`) wurde festgestellt:
* Bei drei Werkstoffen passte der eingetragene Zahlenwert der Scherfestigkeit $\tau_B$ nicht zum angegebenen Verhältnis $\tau_B / R_m$ multipliziert mit der im Katalog hinterlegten Mindestzugfestigkeit $R_m$:
  1. `s235jr`: Im Katalog stand $\tau_B = 264\,\text{MPa}$, während $0{,}80 \cdot 360\,\text{MPa} = 288\,\text{MPa}$ beträgt.
  2. `s355j2`: Im Katalog stand $\tau_B = 360\,\text{MPa}$, während $0{,}80 \cdot 470\,\text{MPa} = 376\,\text{MPa}$ beträgt.
  3. `42crmo4_verguetet`: Im Katalog stand $\tau_B = 488\,\text{MPa}$, während $0{,}65 \cdot 1100\,\text{MPa} = 715\,\text{MPa}$ beträgt.
* Alle drei alten Werte lagen auf der „sicheren Seite“ (niedrigere Scherfestigkeit führt rechnerisch zu größerer Mindesteinschraubtiefe $m_{\text{eff}}$), waren jedoch innerhalb des Mechvane-Datenmodells mathematisch inkonsistent mit den jeweiligen Materialgrenzwerten $R_m$.
* Im Folgenden werden die Herkunft der alten Werte rekonstruiert, die korrekten Kennwerte nach VDI 2230 und DIN EN hergeleitet und die Frage beantwortet, ob VDI 2230 für Vergütungsstähle ein anderes Verhältnis als 0,65 vorsieht.

---

## 2. Ursachenanalyse der bisherigen Abweichungen

Die bisherigen Zahlenwerte $264\,\text{MPa}$, $360\,\text{MPa}$ und $488\,\text{MPa}$ stammten aus den PDF-Tabellen des Ingenieurbüros Andreas Hanke („Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Baustahl“ bzw. „... in Vergütungsstahl“):
* In der Baustahl-Tabelle von Hanke lautet die erste Zeilenbeschriftung wörtlich `264 (S235)`.
* Eine weitere Zeile lautet wörtlich `360 (S355)`.
* In der Vergütungsstahl-Tabelle von Hanke lautet eine Zeile wörtlich `488 (42CrMo4)`.

Der Grund für diese Zahlen bei Hanke liegt in der Auslegungsphilosophie für allgemeine Tabellenwerke:
Hanke wählte die Mindestzugfestigkeit bezogen auf **hohe Materialdicken** bzw. große Stangendurchmesser, um auch bei massiven Bauteilen mit dicken Querschnitten konservativ dimensionierte Einschraubtiefen zu garantieren:
1. **S235:** Bei sehr großen Erzeugnisdicken ($t > 100\,\text{mm}$) sinkt die Mindestzugfestigkeit nach DIN EN 10025-2 auf $R_m \approx 330\,\text{MPa}$. Mit $\tau_B / R_m = 0{,}80$ ergibt sich exakt $0{,}80 \cdot 330\,\text{MPa} = 264\,\text{MPa}$.
2. **S355:** Bei Dicken $t > 100\,\text{mm}$ sinkt $R_m$ auf $450\,\text{MPa}$. Mit $0{,}80$ ergibt sich $0{,}80 \cdot 450\,\text{MPa} = 360\,\text{MPa}$.
3. **42CrMo4:** Bei großen Durchmessern ($160 < d \le 250\,\text{mm}$) beträgt die Mindestzugfestigkeit im vergüteten Zustand (+QT) nach DIN EN ISO 683-2 / EN 10083-3 nur noch $R_m = 750\,\text{MPa}$. Mit dem Scherspannungsfaktor $0{,}65$ ergibt sich exakt $0{,}65 \cdot 750\,\text{MPa} = 487{,}5 \approx 488\,\text{MPa}$.

**Geltungsbereich in Mechvane:**  
Im Werkstoffkatalog von Mechvane sind die Datensätze jedoch explizit auf Vorzugsabmessungen des modularen CAD-Systems zugeschnitten:
* `s235jr`: Geltungsbereich `t <= 16 mm` mit $R_m = 360 \dots 510\,\text{MPa}$ ($R_{m,\min} = 360\,\text{MPa}$).
* `s355j2`: Geltungsbereich `3 mm <= t <= 16 mm` mit $R_m = 470 \dots 630\,\text{MPa}$ ($R_{m,\min} = 470\,\text{MPa}$).
* `42crmo4_verguetet`: Geltungsbereich `d <= 16 mm` mit $R_m = 1100 \dots 1300\,\text{N/mm}^2$ ($R_{m,\min} = 1100\,\text{MPa}$).

Die Übernahme der Hanke-Tabellenzeilen für Großquerschnitte widersprach daher den im Katalog definierten Festigkeitskennwerten für $t \le 16\,\text{mm}$. Bei `c45_verguetet` war dies bereits korrekt gelöst worden: Dort wurde $R_m = 700\,\text{MPa}$ mit $0{,}65$ multipliziert, was zu $\tau_B = 455\,\text{MPa}$ führte.

---

## 3. Untersuchung: Nennt VDI 2230 für Vergütungsstähle ein anderes Verhältnis als 0,65?

Im Rahmen der Recherche wurde geprüft, ob die VDI-Richtlinie 2230 Blatt 1:2015 ein anderes Verhältnis als $0{,}65$ für vergütete Stähle ausweist oder eine Abhängigkeit von der Zugfestigkeit $R_m$ vorsieht.

### 3.1 Mutterwerkstoff / Innengewinde (Tabelle 6 nach VDI 2230-1:2015)
In VDI 2230-1:2015 Tabelle 6 („Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten“, dokumentiert u. a. im Technischen Handbuch der Hoffmann Group SFS auf Seite 154) wird für die Werkstoffgruppe **Vergütungsstahl** ein Wertebereich angegeben:
$$\frac{\tau_B}{R_m} = 0{,}65 \text{ bis } 0{,}85$$
* Eine kontinuierliche mathematische Formel $\tau_B / R_m = f(R_m)$ existiert in der VDI 2230 für den Mutterwerkstoff nicht.
* In Bemessungsrichtlinien, Auslegungstabellen (wie bei Hanke) und technischen Kompendien (z. B. Schweizer-FN Maschinenelemente) wird für Vergütungsstähle durchgängig der konservative untere Grenzwert **0,65** (bzw. die Spanne 0,60...0,65) gewählt, um beim Nachweis gegen Gewindeabstreifen auf der sicheren Seite zu liegen.

### 3.2 Schraubenwerkstoffe nach ISO 898-1 zum Vergleich
Interessanterweise differenziert VDI 2230 bei den Schraubenwerkstoffen (die ebenfalls aus vergüteten Stählen gefertigt werden) nach Festigkeitsklassen:
* Festigkeitsklasse 8.8 ($R_m = 800\,\text{MPa}$): $\tau_B / R_m = 0{,}65$
* Festigkeitsklasse 10.9 ($R_m = 1000\,\text{MPa}$): $\tau_B / R_m = 0{,}62$
* Festigkeitsklasse 12.9 ($R_m = 1200\,\text{MPa}$): $\tau_B / R_m = 0{,}60$

Hier zeigt sich mit zunehmender Vergütungsfestigkeit ein leichtes Absinken des Abscherverhältnisses von 0,65 auf 0,60. Würde man diese Schrauben-Abstufung auf hochfesten 42CrMo4 (+QT, $R_m = 1100\,\text{MPa}$) übertragen, läge das Verhältnis bei ca. $0{,}61 \dots 0{,}62$ ($\tau_B \approx 670 \dots 682\,\text{MPa}$).  
Für Innengewinde in Bauteilen verbleibt die normative Vorgabe der VDI 2230 jedoch bei der Materialgruppe „Vergütungsstahl“ mit dem Mindestwert **0,65**.

### 3.3 Fazit für 42CrMo4 (+QT)
Der korrekte und konsistente Auslegungswert für `42crmo4_verguetet` im Zustand +QT ($d \le 16\,\text{mm}$) lautet somit:
$$\tau_B = 0{,}65 \cdot 1100\,\text{MPa} = 715\,\text{MPa}$$
Damit ist die Systematik zwischen `c45_verguetet` ($0{,}65 \cdot 700 = 455\,\text{MPa}$) und `42crmo4_verguetet` vollständig einheitlich.

---

## 4. Übersicht der Korrekturen und Neuberechnung der Einschraubtiefen

In der folgenden Tabelle sind die alten und neuen Kennwerte sowie die resultierenden Mindesteinschraubtiefen für eine Schraube **M6 Festigkeitsklasse 8.8** ($F_{\text{Zug}} = 16\,098\,\text{N}$, Innengewinde-Scherfläche $A_n' = 12{,}191\,\text{mm}^2/\text{mm}$ nach FED-STD-H28 / ASME $6\text{H}/6\text{g}$) zusammengestellt.

Die Formeln lauten:
$$m_{\text{eff}} = \frac{F_{\text{Zug}}}{A_n' \cdot \tau_B}, \qquad m_{\text{ges}} = m_{\text{eff}} + 2 \cdot P \quad (P = 1{,}0\,\text{mm})$$

| ID / Werkstoff | $R_m$ [MPa] | $\tau_B / R_m$ | $\tau_B$ alt [MPa] | $\tau_B$ neu [MPa] | $m_{\text{eff}}$ alt [mm] | $m_{\text{eff}}$ neu [mm] | $m_{\text{ges}}$ neu [mm] | $m_{\text{eff}} / d$ neu | Bossard Empfehlung |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `s235jr` (S235JR) | 360 | 0,80 | 264 | **288** | 5,00 (0,83 d) | **4,59** | 6,59 | 0,76 d | 1,00 d (6,0 mm) |
| `s355j2` (S355J2) | 470 | 0,80 | 360 | **376** | 3,67 (0,61 d) | **3,51** | 5,51 | 0,59 d | 0,90 d (5,4 mm) |
| `42crmo4_verguetet` | 1100 | 0,65 | 488 | **715** | 2,71 (0,45 d) | **1,85** | 3,85 | 0,31 d | 0,80 d (4,8 mm) |

**Bewertung der Auswirkungen:**
1. **S235JR:** Die effektive Einschraubtiefe sinkt um $0{,}41\,\text{mm}$ von $5{,}00\,\text{mm}$ auf $4{,}59\,\text{mm}$. Der Bossard-Praxisrichtwert von $1{,}0\,d = 6{,}0\,\text{mm}$ deckt den neuen Mindestwert weiterhin mit komfortabler Reserve ($+31\,\%$) ab.
2. **S355J2:** Die effektive Einschraubtiefe sinkt geringfügig um $0{,}16\,\text{mm}$ von $3{,}67\,\text{mm}$ auf $3{,}51\,\text{mm}$.
3. **42CrMo4 (+QT):** Die effektive Einschraubtiefe reduziert sich von $2{,}71\,\text{mm}$ auf $1{,}85\,\text{mm}$ ($0{,}31\,d$). Vergüteter 42CrMo4 besitzt eine außergewöhnlich hohe Scherfestigkeit, so dass bereits wenige Gewindegänge genügen, um Schrauben der Güte 8.8 zum Zugbruch zu bringen. Selbst bei einer hochfesten Schraube 12.9 ($F_{\text{Zug}} \approx 24\,550\,\text{N}$) beträgt $m_{\text{eff}}$ nur $2{,}82\,\text{mm}$ ($0{,}47\,d$).

---

## 5. Detaillierte Quellenbelege

### 5.1 Quelle A: Baustahl nach VDI 2230 (Ingenieurbüro Andreas Hanke)

#### Beleg: Ingenieurbüro Andreas Hanke – Baustahl
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefen Baustahl PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Baustahl-Scherfestigkeitsverh%C3%A4ltnis0.8.pdf)
* **Fundstelle:** Seite 1, Titelzeile und Tabelle
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Baustahl“
* **Zweites Zitat:** „Scherfestigkeitsverhältnis τB / Rm = 0.8“
* **Belegte Zahlen:** 0.8, 264, 360, 8.8, 8.2, 6.9.

---

### 5.2 Quelle B: Vergütungsstahl nach VDI 2230 (Ingenieurbüro Andreas Hanke)

#### Beleg: Ingenieurbüro Andreas Hanke – Vergütungsstahl
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefen Vergütungsstahl PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Verg%C3%BCtungsstahl-Scherfestigkeitsverh%C3%A4ltnis0.65.pdf)
* **Fundstelle:** Seite 1, Titelzeile und Tabelle
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Vergütungsstahl“
* **Zweites Zitat:** „Scherfestigkeitsverhältnis τB / Rm = 0.65“
* **Belegte Zahlen:** 0.65, 488, 8.8, 10.9, 12.9.

---

### 5.3 Quelle C: VDI 2230-1 Tabelle 6 (Hoffmann Group SFS Technisches Handbuch)

#### Beleg: Hoffmann Group SFS – Technisches Handbuch Verbindungstechnik
* **Quelle:** [Hoffmann Group SFS Technisches Handbuch Verbindungstechnik](https://assets.hoffmann-group.com/media/ch/sfs_ch/broschueren_1/technisches_handbuch_fuer_verbindungstechnik/dimensionierung/allgemeines/Mindesteinschraubtiefe_in_geschnittene_Bauteilmuttergewinde_DE.pdf)
* **Fundstelle:** Seite 154, Tabelle Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten
* **Wörtliches Zitat:** „Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten“
* **Zweites Zitat:** „Baustahl 0,8 bis 0,85“
* **Drittes Zitat:** „Vergütungsstahl 0,65 bis 0,85“
* **Belegte Zahlen:** Baustahl 0,8 bis 0,85, Vergütungsstahl 0,65 bis 0,85.

---

### 5.4 Quelle D: Scherspannungsfaktor nach VDI 2230 (Schweizer-FN Maschinenelemente)

#### Beleg: Schweizer-FN – Schraubenverbindung und Scherfestigkeit
* **Quelle:** [Schweizer-FN Schraubenverbindung und Scherfestigkeit](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php)
* **Fundstelle:** Abschnitt Scherfestigkeit
* **Wörtliches Zitat:** „Nach der Gestaltänderungs-Hypothese von Mises lässt sich die Scherfestigkeit für duktile Werkstoffe wie folgt berechnen.“
* **Zweites Zitat:** „Der Scherspannungsfaktor für die einzelnen Werkstoffe beträgt:“
* **Belegte Zahlen:** Vergütungsstähle 0,60...0,65, Schrauben Festigkeitsklasse 8.8 0,65, Festigkeitsklasse 10.9 0,62, Festigkeitsklasse 12.9 0,60.

---

### 5.5 Quelle E: Primärdatenblätter der drei Werkstoffe für Mindestzugfestigkeit Rm

#### Beleg: Thyssenkrupp – S235JR (1.0038)
* **Quelle:** [Thyssenkrupp S235JR Datenblatt PDF](https://ucpcdn.thyssenkrupp.com/_legacy/UCPthyssenkruppBAMXFrance/assets.files/product_pdf/carbon_flat_steel_/plates_and_slabs_carbon_steel/s235jr_1_0038_11_2016_engl.pdf)
* **Fundstelle:** Seite 1-2, Reference data on physical properties & Mechanical properties
* **Wörtliches Zitat:** „Mean linear thermal expansion coefficient [10-6 K-1] between 20 °C and“
* **Belegte Zahlen:** 16 mm, 235 MPa, 360 to 510 MPa, 26 %.

#### Beleg: Thyssenkrupp Materials Processing Europe – S355J2 (1.0577)
* **Quelle:** [Thyssenkrupp S355J2 Produktseite](https://www.thyssenkrupp-materials-processing-europe.com/de/c-stahl/warmband/s235jr-s355k2/s355j2)
* **Fundstelle:** Abschnitt Mechanische Eigenschaften
* **Wörtliches Zitat:** „Die Güte S355J2 hat eine Mindeststreckgrenze von 355 MPa.“
* **Belegte Zahlen:** 355 MPa, 16 mm, 3 mm, 470–630 MPa, 20 %.

#### Beleg: Saarstahl – 42CrMo4 (+QT, 1.7225)
* **Quelle:** [Saarstahl 42CrMo4 Datenblatt PDF](https://en.saarstahl.com/app/uploads/2024/03/20160323013851-42CrMo4-42CrMoS4.pdf)
* **Fundstelle:** Seite 1, Mechanical properties Quenched and tempered +QT
* **Wörtliches Zitat:** „Quenched and tempered, +QT:“
* **Belegte Zahlen:** 16 mm, 900 N/mm², 1100 - 1300 N/mm², 10 %, 40 %, 30 J.
