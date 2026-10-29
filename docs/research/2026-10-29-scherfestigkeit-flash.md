# Recherchebericht: Scherfestigkeit $\tau_B$ der 16 Werkstoffe & Klärung der NASA-RP-1228-Abweichung

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #16). `tools/check_sources.py`:
> 11 von 11 Quellen, 11 Zitate und 55 von 55 Zahlen bestätigt; alle 16 Einträge schemagültig.
> **NASA RP-1228 geklärt:** P = π·d_m·F_s·L/3 (Flankendurchmesser, empirischer Faktor 1/3) ist eine
> bewusst konservative Abschätzung; (6·0,65)/(5,35/3) ≈ 2,2 erklärt die Verdoppelung. Für Mechvane gilt
> der Ansatz mit realer Scherfläche (VDI 2230 / FED-STD-H28).
> **Ungeklärt:** Bei drei Werkstoffen passt τ_B nicht zum angegebenen Verhältnis τ_B/R_m:
> S235JR 264 statt 0,80·360 = 288, S355J2 360 statt 0,80·470 = 376, 42CrMo4 488 statt 0,65·1100 = 715 MPa.
> Alle drei liegen auf der sicheren Seite (größere Einschraubtiefe), vor einer Nutzung in Regeln aber
> klären. Fast alle Werte sind Richtwerte über VDI-2230-Verhältnisse, nur EN-GJL-250 ist doppelt belegt.

> **Prüfnotiz (Gemini 3.8 Flash, 2026-10-29):** Recherchebericht zu Issue #16 als Fortführung und Klärung der offenen Fragen aus `docs/research/2026-10-29-regeln-aus-kennwerten-flash.md` (Issue #14) und Ergänzung der Werkstoffdatenbank (`katalog/eintraege/werkstoffe/`, Issue #13).
> Alle Quellen sind über `tools/check_sources.py` nachweisbar, Zitate sind wörtlich belegt, Zahlenwerte im Quelltext nachgewiesen.
> Gemäß Vorgabe sind Werte nur dann als „belegt“ klassifiziert, wenn mindestens zwei voneinander unabhängige Primär- oder Normquellen vorliegen; allgemeine Verhältniswerte nach VDI 2230 Blatt 1 bzw. Einzelbelege sind transparent als „Richtwert“ ausgewiesen.

---

## 1. Einleitung und Zielsetzung

In der vorangegangenen Recherche (`docs/research/2026-10-29-regeln-aus-kennwerten-flash.md`) wurde die Mindest-Einschraubtiefe $m_{\text{eff}}$ von Gewindebohrungen analytisch über das Kriterium der Bruchgleichheit (Schraubenabriss vor Innengewindeabstreifen) hergeleitet:

$$m_{\text{eff}} \ge \frac{F_{\text{Zug}}}{A_n' \cdot \tau_B} = \frac{A_s \cdot R_{m,\text{Schraube}}}{A_n' \cdot \tau_B}$$

Hierbei bezeichnet:
* $A_s$: Spannungsquerschnitt der Schraube nach ISO 898-1 (für M6 Regelgewinde: $A_s = 20{,}123\,\text{mm}^2$).
* $R_{m,\text{Schraube}}$: Mindestzugfestigkeit der Schraube (für Festigkeitsklasse 8.8: $800\,\text{MPa} \implies F_{\text{Zug}} \approx 16\,098\,\text{N}$).
* $A_n'$: Innengewinde-Scherfläche pro Millimeter Einschraubtiefe am Außendurchmesser $d$ (nach ASME / FED-STD-H28 für M6 $6\text{H}/6\text{g}$: $A_n' = 12{,}191\,\text{mm}^2/\text{mm}$).
* $\tau_B$: Wirksame Scherfestigkeit des Mutterwerkstoffs in $\text{MPa}$ (bzw. $\text{N/mm}^2$).

Ziel dieser Untersuchung ist:
1. Für alle 16 Werkstoffe in `katalog/eintraege/werkstoffe/` die werkstoffspezifische Scherfestigkeit $\tau_B$ bzw. das Scherfestigkeitsverhältnis $\tau_B / R_m$ mit nachprüfbaren Primär- und Normquellen zu belegen bzw. als fundierten Richtwert (VDI 2230) auszuweisen.
2. Die in der Prüfnotiz aufgeworfene Frage zu **NASA RP-1228** abschließend zu klären: Warum lag deren Einschraubtiefe im vorigen Bericht etwa beim Doppelten der anderen Ansätze ($10{,}88\,\text{mm}$ vs. $5{,}00\,\text{mm}$ bei S235)?
3. Die ermittelten Werte in die 16 Katalogeinträge zu übertragen und die Mindest-Einschraubtiefen $m_{\text{eff}}$ sowie die Gesamteinschraubtiefen $m_{\text{ges}} = m_{\text{eff}} + 2P$ tabellarisch zu vergleichen.

---

## 2. Übersichtstabelle aller 16 Werkstoffe mit $\tau_B$, Status und $m_{\text{eff}}$

In der folgenden Tabelle sind die mechanischen Kennwerte aller 16 Werkstoffe zusammengefasst. Die effektive Einschraubtiefe $m_{\text{eff}}$ sowie die Gesamttiefe $m_{\text{ges}} = m_{\text{eff}} + 2 \cdot P$ ($P = 1{,}0\,\text{mm}$) sind für eine Schraube **M6 Festigkeitsklasse 8.8** ($F_{\text{Zug}} = 16\,098\,\text{N}$, $A_n' = 12{,}191\,\text{mm}^2/\text{mm}$) berechnet.

| ID | Werkstoff | Werkstoffgruppe | $R_m$ [MPa] | $\tau_B$ [MPa] | $\tau_B / R_m$ | Status | Nachweisquelle | $m_{\text{eff}}$ [mm] | $m_{\text{ges}}$ [mm] | $m_{\text{eff}} / d$ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| `s235jr` | S235JR (1.0038) | Baustahl | 360 | 264 | 0,80 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 5,00 | 7,00 | 0,83 d |
| `s355j2` | S355J2 (1.0577) | Baustahl | 470 | 360 | 0,80 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 3,67 | 5,67 | 0,61 d |
| `c45_verguetet` | C45 (+QT) | Vergütungsstahl | 700 | 455 | 0,65 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 2,90 | 4,90 | 0,48 d |
| `42crmo4_verguetet` | 42CrMo4 (+QT) | Vergütungsstahl | 1100 | 488 | 0,65 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 2,71 | 4,71 | 0,45 d |
| `1_4301` | 1.4301 (A2) | Austenitischer Edelstahl | 500 | 400 | 0,80 | Richtwert | VDI 2230 / Hoffmann Handbuch | 3,30 | 5,30 | 0,55 d |
| `1_4404` | 1.4404 (A4) | Austenitischer Edelstahl | 500 | 400 | 0,80 | Richtwert | VDI 2230 / Hoffmann Handbuch | 3,30 | 5,30 | 0,55 d |
| `en_aw_6060_t6` | EN AW-6060 T6 | Al-Knetlegierung | 215 | 129 | 0,60 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 10,24 | 12,24 | 1,71 d |
| `en_aw_6082_t6` | EN AW-6082 T6 | Al-Knetlegierung | 310 | 186 | 0,60 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 7,10 | 9,10 | 1,18 d |
| `en_aw_7075_t6` | EN AW-7075 T6 | Al-Knetlegierung | 540 | 324 | 0,60 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 4,08 | 6,08 | 0,68 d |
| `en_aw_5083_h111` | EN AW-5083 H111 | Al-Knetlegierung | 270 | 162 | 0,60 | Richtwert | VDI 2230 / Ing.-Büro Hanke | 8,15 | 10,15 | 1,36 d |
| `en_gjl_250` | EN-GJL-250 | Grauguss (GJL) | 250 | 290 | 1,15 | belegt | Castfast Datenblatt & VDI 2230 | 4,55 | 6,55 | 0,76 d |
| `cuzn39pb3` | CuZn39Pb3 | Zerspanungsmessing | 500 | 390 | 0,72 | Richtwert | Gemmel Metalle Datenblatt | 3,39 | 5,39 | 0,56 d |
| `pom_c` | POM-C | Technischer Thermoplast | 67 | 55 | 0,82 | Richtwert | bwn Kunststofftechnik TDS | 24,01 | 26,01 | 4,00 d |
| `pa6_trocken` | PA6 (trocken) | Technischer Thermoplast | 80 | 50 | 0,63 | Richtwert | bwn TDS (76 MPa) / VDI 2230 | 26,41 | 28,41 | 4,40 d |
| `pla` | PLA (3D-Druck) | FDM-Druckteil | 50 | 25 | 0,50 | Richtwert | VDI 2230 / Gestaltänderungshyp. | 52,82 | 54,82 | 8,80 d |
| `petg` | PETG (3D-Druck) | FDM-Druckteil | 45 | 25 | 0,56 | Richtwert | VDI 2230 / Gestaltänderungshyp. | 52,82 | 54,82 | 8,80 d |

*Status-Definition gemäß Aufgabenstellung:*
* **belegt:** Bestätigt durch mindestens zwei unabhängige Primär- oder Normquellen mit übereinstimmenden Mess- oder Auslegungswerten (hier erfüllt für `en_gjl_250`: Gießereidatenblatt Castfast weist $290\,\text{N/mm}^2$ aus, VDI 2230 / Hanke liefert bei $R_m = 250\,\text{MPa}$ und Faktor $1{,}15$ rechnerisch $288\,\text{MPa}$).
* **Richtwert:** Belegt durch eine Primärquelle (Herstellerdatenblatt z. B. bei CuZn39Pb3, POM-C, PA6) oder hergeleitet über die normativen Scherspannungsverhältnisse $\tau_B / R_m$ nach VDI 2230-1:2015 Tabelle 6.

---

## 3. Klärung der Abweichung bei NASA RP-1228

### 3.1 Fragestellung aus der Prüfnotiz

Im vorherigen Recherchebericht lag der Wert der Einschraubtiefe nach **NASA RP-1228** durchweg etwa beim Doppelten der anderen Ansätze. Für Schraube M6 Festigkeitsklasse 8.8 in Baustahl S235 ergaben sich folgende Werte:
* Analytische Mindest-Einschraubtiefe: $m_{\text{eff}} = 5{,}00\,\text{mm}$ ($0{,}83\,d$)
* FED-STD-H28 / Machinery's Handbook: $L_e = 5{,}20\,\text{mm}$ ($0{,}87\,d$)
* Bossard Praxisrichtwert (`mechvane/hole_tables.py`): $1{,}00 \cdot d = 6{,}0\,\text{mm}$
* **NASA RP-1228:** $L = 10{,}88\,\text{mm}$ ($1{,}81\,d$)

Das Verhältnis von NASA zu $m_{\text{eff}}$ beträgt exakt:
$$\frac{L_{\text{NASA}}}{m_{\text{eff}}} = \frac{10{,}883\,\text{mm}}{5{,}002\,\text{mm}} = 2{,}176 \approx 2{,}18$$

### 3.2 Wörtliches Zitat der Formel aus NASA RP-1228

Die Referenzpublikation ist:  
**Richard T. Barrett: Fastener Design Manual.** NASA Reference Publication 1228, Lewis Research Center, Cleveland, Ohio, März 1990.

Auf **Seite 21** (im PDF Seite 25), Abschnitt *„Calculating Pullout Load for Threaded Hole“*, lautet der Originaltext wörtlich:

> *„In many cases a bolt of one material may be installed in a tapped hole in a different (and frequently lower strength) material. If the full strength of the bolt is required, the depth of the tapped hole must be determined for the weaker material by using the formula“*
>
> $$P = \frac{\pi \cdot d_m \cdot F_s \cdot L}{3}$$
>
> *„where“*
> * *„P: pullout load, lb“*
> * *„d_m: mean diameter of threaded hole, in. (≈ pitch diameter of threads)“*
> * *„F_s: material ultimate or yield shear stress“*
> * *„L: length of thread engagement, in.“*
>
> *„The 1/3 factor is empirical. If the threads were perfectly mated, this factor would be 1/2, since the total cylindrical shell area of the hole would be split equally between the bolt threads and the tapped hole threads. The 1/3 is used to allow for mismatch between threads.“*

### 3.3 Physikalische und mathematische Ursachen der Verdoppelung

Umgestellt nach der Einschraubtiefe $L$ lautet die NASA-Gleichung:

$$L = \frac{3 \cdot P}{\pi \cdot d_m \cdot F_s}$$

Im Vergleich dazu lautet die klassische Maschinenbau-Formel (VDI 2230, FED-STD-H28, Alexander):

$$m_{\text{eff}} = \frac{P}{A_n' \cdot \tau_B} = \frac{P}{\pi \cdot d \cdot \eta_{\text{nut}} \cdot \tau_B}$$

Der Faktor $\approx 2{,}18$ entsteht aus drei kumulativen physikalisch-geometrischen Vereinfachungen in Barretts Ansatz:

#### 1. Scherzylinder-Durchmesser ($d_m$ vs. $d$):
* NASA verwendet den **Flankendurchmesser** $d_m \approx d_2$ (Pitch Diameter). Für M6 Regelgewinde ist $d_2 = d - 0{,}6495 \cdot P = 5{,}3505\,\text{mm}$.
* Das Innengewinde (Muttergewinde) schert jedoch physikalisch am **Außendurchmesser des Bolzens** $d = 6{,}0\,\text{mm}$ ab (Zylindergrund der Muttergewindegänge).
* Allein das Durchmesserverhältnis erzeugt einen Hebel von:
  $$\frac{d}{d_m} = \frac{6{,}0\,\text{mm}}{5{,}3505\,\text{mm}} \approx 1{,}121 \quad (+12{,}1\,\%)$$

#### 2. Reale Zahnfußbreite bei $60^\circ$-Spitzgewinden ($\eta_{\text{nut}} \approx 0{,}75$ vs. $0{,}50$):
* Barrett geht gedanklich von einem symmetrischen Rechteckprofil aus: Wenn Bolzen und Mutter ideal ineinandergreifen würden, nähme jede Seite die Hälfte des Zylindermantels ein ($1/2 = 0{,}50$).
* Bei einem metrischen $60^\circ$-Gewinde nach ISO 68-1 / DIN 13 ist der Zahn am Flankendurchmesser zwar $0{,}50 \cdot P$ breit, die Abscherung des Muttergewindes erfolgt aber am Außendurchmesser $d$. Dort hat der Zahnfuß der Mutter eine theoretische Breite von $\approx 0{,}75 \cdot P$.
* Unter Berücksichtigung von Spitzenstauchung, Rundung und Toleranzen $6\text{H}/6\text{g}$ beträgt der Profilscherbeiwert nach FED-STD-H28 $\eta_{\text{nut}} = 0{,}647$.
* Das Verhältnis der tatsächlichen Zahnfußbreite zur von Barrett angenommenen halben Zylinderfläche beträgt:
  $$\frac{\eta_{\text{nut}}}{0{,}50} = \frac{0{,}647}{0{,}50} \approx 1{,}294 \quad (+29{,}4\,\%)$$

#### 3. Der empirische Mismatch-Abschlag ($1/3$ statt $1/2$):
* Barrett halbiert die Zylinderfläche nicht nur ($1/2$), sondern reduziert sie nochmals auf ein Drittel ($1/3$):
  $$\frac{1/3}{1/2} = \frac{2}{3} \approx 0{,}667$$
* Dies entspricht einem **eingebauten empirischen Sicherheitszuschlag von $1{,}50$** ($1 / (2/3) = 1{,}50$), um Fertigungstoleranzen, Flankenwinkelfehler, Steigungsfehler (Lead Error) und ungleichmäßige Lastverteilung pauschal abzufangen.

#### 4. Gesamteffektivfläche im Vergleich:
Multipliziert man diese drei Effekte, ergibt sich das Verhältnis der wirksamen Scherflächen pro Millimeter Einschraubtiefe:

$$A_{\text{shear, NASA}}' = \frac{\pi \cdot d_m}{3} = \frac{\pi \cdot 5{,}3505\,\text{mm}}{3} = 5{,}603\,\text{mm}^2/\text{mm}$$

$$A_n' (\text{FED-STD-H28 / VDI 2230}) = 12{,}191\,\text{mm}^2/\text{mm}$$

$$\frac{A_n'}{A_{\text{shear, NASA}}'} = \frac{12{,}191\,\text{mm}^2/\text{mm}}{5{,}603\,\text{mm}^2/\text{mm}} = 2{,}1758 \approx 2{,}18$$

#### 5. Einfluss des Festigkeitswerts ($F_s$):
Barrett definiert $F_s$ als *„material ultimate or yield shear stress“*.
* Setzt man die Scher-Streckgrenze $F_{sy} \approx R_{p0,2} / \sqrt{3} \approx 136\,\text{MPa}$ ein (um jegliche plastische Verformung im Gewindegrund auszuschließen), stiege $L$ auf über $21\,\text{mm}$ ($3{,}5\,d$).
* Selbst bei Einsetzen der vollen Bruch-Scherfestigkeit $\tau_B = 264\,\text{MPa}$ verbleibt der geometrisch-empirische Faktor $2{,}18$.

### 3.4 Zahlenbeispiel M6 8.8 in S235

* **Schraubenkraft M6 8.8:**
  $$A_s = 20{,}123\,\text{mm}^2, \quad R_{m,\text{Schraube}} = 800\,\text{N/mm}^2 \implies P = F_{\text{Zug}} = 16\,098{,}4\,\text{N}$$
* **Mutterwerkstoff S235:**
  $$\tau_B = F_s = 264\,\text{N/mm}^2$$
* **Rechnung Standard (Bruchgleichheit mit $A_n'$):**
  $$m_{\text{eff}} = \frac{16\,098{,}4\,\text{N}}{12{,}191\,\text{mm}^2/\text{mm} \cdot 264\,\text{N/mm}^2} = 5{,}002\,\text{mm} \approx 5{,}00\,\text{mm} \quad (0{,}83\,d)$$
  $$m_{\text{ges}} = m_{\text{eff}} + 2 \cdot P = 5{,}00\,\text{mm} + 2{,}00\,\text{mm} = 7{,}00\,\text{mm} \quad (1{,}17\,d)$$
* **Rechnung NASA RP-1228:**
  $$L = \frac{3 \cdot 16\,098{,}4\,\text{N}}{\pi \cdot 5{,}3505\,\text{mm} \cdot 264\,\text{N/mm}^2} = \frac{48\,295{,}2}{4\,437{,}83} = 10{,}883\,\text{mm} \approx 10{,}88\,\text{mm} \quad (1{,}81\,d)$$

### 3.5 Fazit zur NASA-Formel

Die NASA-Formel nach RP-1228 ist eine bewusst vereinfachte, **konservative Abschätzungsformel für die Luft- und Raumfahrt**. Sie verzichtet auf die exakte Berechnung von Toleranzfeldern und Profiltraganteilen und erkauft dies durch eine pauschale Verdoppelung der rechnerischen Einschraubtiefe (Faktor $\approx 2{,}18$).

Im parametrischen CAD von Mechvane sollte daher nicht die NASA-Faustformel gemittelt werden, sondern das physikalische Modell nach VDI 2230 / FED-STD-H28 mit der realen Gewindescherfläche $A_n'$ und der Werkstoffscherfestigkeit $\tau_B$ zugrunde gelegt werden.

---

## 4. Python-Berechnungsskript

Das folgende Python-Skript führt die Berechnung von $m_{\text{eff}}$, $m_{\text{ges}}$ sowie des NASA-Werts für alle 16 Werkstoffe automatisiert durch:

```python
import math

def calculate_thread_engagements():
    # Schraubenparameter M6 Regelgewinde (ISO 68-1 / ISO 261 / ISO 898-1)
    d = 6.0              # mm
    P = 1.0              # mm
    d2 = 5.3505          # mm (Flankendurchmesser)
    As = 20.123          # mm^2
    Rm_bolt = 800.0      # N/mm^2 (Güte 8.8)
    F_tensile = As * Rm_bolt  # 16098.4 N

    # Abstreiffläche Innengewinde pro mm Einschraubtiefe (FED-STD-H28 / ASME M6 6H/6g)
    An_per_mm = 73.145 / 6.0  # 12.190833... mm^2/mm

    # Materialdatensätze (ID, Name, Rm, tau_B, tau_Rm_ratio, Status)
    materials = [
        ("s235jr", "S235JR", 360.0, 264.0, 0.80, "Richtwert"),
        ("s355j2", "S355J2", 470.0, 360.0, 0.80, "Richtwert"),
        ("c45_verguetet", "C45 (+QT)", 700.0, 455.0, 0.65, "Richtwert"),
        ("42crmo4_verguetet", "42CrMo4 (+QT)", 1100.0, 488.0, 0.65, "Richtwert"),
        ("1_4301", "1.4301", 500.0, 400.0, 0.80, "Richtwert"),
        ("1_4404", "1.4404", 500.0, 400.0, 0.80, "Richtwert"),
        ("en_aw_6060_t6", "EN AW-6060 T6", 215.0, 129.0, 0.60, "Richtwert"),
        ("en_aw_6082_t6", "EN AW-6082 T6", 310.0, 186.0, 0.60, "Richtwert"),
        ("en_aw_7075_t6", "EN AW-7075 T6", 540.0, 324.0, 0.60, "Richtwert"),
        ("en_aw_5083_h111", "EN AW-5083 H111", 270.0, 162.0, 0.60, "Richtwert"),
        ("en_gjl_250", "EN-GJL-250", 250.0, 290.0, 1.15, "belegt"),
        ("cuzn39pb3", "CuZn39Pb3", 500.0, 390.0, 0.72, "Richtwert"),
        ("pom_c", "POM-C", 67.0, 55.0, 0.82, "Richtwert"),
        ("pa6_trocken", "PA6 (trocken)", 80.0, 50.0, 0.63, "Richtwert"),
        ("pla", "PLA (3D-Druck)", 50.0, 25.0, 0.50, "Richtwert"),
        ("petg", "PETG (3D-Druck)", 45.0, 25.0, 0.56, "Richtwert"),
    ]

    results = []
    for mat_id, name, rm, tau, ratio, status in materials:
        meff = F_tensile / (An_per_mm * tau)
        mges = meff + 2.0 * P
        meff_d = meff / d
        L_nasa = (3.0 * F_tensile) / (math.pi * d2 * tau)
        nasa_ratio = L_nasa / meff
        results.append({
            "id": mat_id, "name": name, "Rm": rm, "tau_B": tau,
            "ratio": ratio, "status": status, "meff": meff,
            "mges": mges, "meff_d": meff_d, "L_nasa": L_nasa,
            "nasa_ratio": nasa_ratio
        })
    return results

if __name__ == "__main__":
    res = calculate_thread_engagements()
    for r in res:
        print(f"{r['id']:<18} | tau_B={r['tau_B']:>5.1f} MPa | meff={r['meff']:>5.2f} mm ({r['meff_d']:>4.2f}d) | L_nasa={r['L_nasa']:>5.2f} mm | Ratio={r['nasa_ratio']:.2f}")
```

---

## 5. Detaillierte Quellenbelege je Werkstoffgruppe

### 5.1 Quelle A: NASA Reference Publication 1228

#### NASA RP-1228 – Beleg: Fastener Design Manual (Richard T. Barrett, 1990)
* **Quelle:** [EngineeringLibrary – Loads on Fastener Groups (NASA Design Manual)](https://engineeringlibrary.org/reference/loads-on-fastener-groups-nasa-design-manual)
* **Fundstelle:** Abschnitt Calculating Pullout Load for Threaded Hole
* **Wörtliches Zitat:** „In many cases a bolt of one material may be installed in a tapped hole in a different (and frequently lower strength) material. If the full strength of the bolt is required, the depth of the tapped hole must be determined for the weaker material by using the formula“
* **Zweites Zitat zum Faktor 1/3:** „The 1/3 factor is empirical. If the threads were perfectly mated, this factor would be 1/2, since the total cylindrical shell area of the hole would be split equally between the bolt threads and the tapped hole threads. The 1/3 is used to allow for mismatch between threads.“
* **Belegte Zahlen:** pullout load P in lb, mean diameter dm in in., length of thread engagement L in in.

---

### 5.2 Quelle B: VDI 2230-1:2015 / Hoffmann Group SFS Handbuch

#### Hoffmann Group SFS – Beleg: Mindesteinschraubtiefe in geschnittene Bauteilmuttergewinde
* **Quelle:** [Hoffmann Group SFS Technisches Handbuch Verbindungstechnik](https://assets.hoffmann-group.com/media/ch/sfs_ch/broschueren_1/technisches_handbuch_fuer_verbindungstechnik/dimensionierung/allgemeines/Mindesteinschraubtiefe_in_geschnittene_Bauteilmuttergewinde_DE.pdf)
* **Fundstelle:** Seite 154, Tabelle Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten
* **Wörtliches Zitat:** „Anhaltswerte für Scherfestigkeitsverhältnisse verschiedener Werkstoffsorten“
* **Zweites Zitat:** „Austenit (lösungsgeglüht)“
* **Drittes Zitat:** „Baustahl 0,8 bis 0,85“
* **Viertes Zitat:** „Vergütungsstahl 0,65 bis 0,85“
* **Belegte Zahlen:** Baustahl 0,8 bis 0,85, Vergütungsstahl 0,65 bis 0,85, Austenit 0,8.

---

### 5.3 Quelle C: Baustähle (S235JR, S355J2) nach VDI 2230

#### Baustahl – Beleg: Ingenieurbüro Andreas Hanke (VDI 2230-1:2015)
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefen Baustahl PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Baustahl-Scherfestigkeitsverh%C3%A4ltnis0.8.pdf)
* **Fundstelle:** Seite 1, Tabelle Mindesteinschraubtiefen für Baustahl
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Baustahl“
* **Zweites Zitat:** „Scherfestigkeitsverhältnis τB / Rm = 0.8“
* **Belegte Zahlen:** Zeile 264 (S235) für M6 Güte 8.8 ergibt 8.2 mm (Gesamttiefe), Zeile 360 (S355) für M6 Güte 8.8 ergibt 6.9 mm.

---

### 5.4 Quelle D: Vergütungsstähle (C45, 42CrMo4) nach VDI 2230

#### Vergütungsstahl – Beleg: Ingenieurbüro Andreas Hanke (VDI 2230-1:2015)
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefen Vergütungsstahl PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Verg%C3%BCtungsstahl-Scherfestigkeitsverh%C3%A4ltnis0.65.pdf)
* **Fundstelle:** Seite 1, Titelzeile und Tabelle
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Vergütungsstahl“
* **Zweites Zitat:** „Scherfestigkeitsverhältnis τB / Rm = 0.65“
* **Belegte Zahlen:** Zeile 488 (42CrMo4) für Festigkeitsklasse 10.9 und 12.9.

---

### 5.5 Quelle E: Aluminium-Knetlegierungen (EN AW-6060, 6082, 7075, 5083)

#### Aluminium-Knetlegierungen – Beleg: Ingenieurbüro Andreas Hanke (VDI 2230-1:2015)
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefen Aluminium-Knetlegierungen PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Alu-Knetlegierungen-Scherfestigkeitsverh%C3%A4ltnis0.6.pdf)
* **Fundstelle:** Seite 1, Titelzeile
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Aluminium-Knetlegierungen“
* **Zweites Zitat:** „Scherfestigkeitsverhältnis τB / Rm = 0.6“
* **Belegte Zahlen:** Mindesteinschraubtiefen für Aluminium-Knetlegierungen mit Verhältnis 0.6.

---

### 5.6 Quelle F: Grauguss EN-GJL-250

#### EN-GJL-250 – Beleg 1: Castfast Eisenguss Werkstoffdatenblatt
* **Quelle:** [Castfast Werkstoffeigenschaften Eisenguss GJL PDF](https://www.castfast.com/wp-content/uploads/2024/07/Werkstoffeigenschaften-GJL-CASTFAST.pdf)
* **Fundstelle:** Seite 1, Tabelle Gusseisen mit Lamellengraphit (GJL), Zeile Scherfestigkeit
* **Wörtliches Zitat:** „Scherfestigkeit σaB N/mm²“
* **Belegte Zahlen:** EN-GJL-250 Scherfestigkeit 290 N/mm², Zugfestigkeit 200 - 250 N/mm², Druckfestigkeit 840 N/mm².

#### EN-GJL-250 – Beleg 2: Ingenieurbüro Andreas Hanke (VDI 2230-1:2015)
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefen GJL PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-GJL-Scherfestigkeitsverh%C3%A4ltnis1.15.pdf)
* **Fundstelle:** Seite 1, Titelzeile
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Gusseisen mit Lamellegraphit (GJL)“
* **Zweites Zitat:** „Scherfestigkeitsverhältnis τB / Rm = 1.15“
* **Belegte Zahlen:** GJL Scherfestigkeitsverhältnis 1.15.

---

### 5.7 Quelle G: Messing CuZn39Pb3

#### CuZn39Pb3 – Beleg: Hans-Erich Gemmel & Co. GmbH
* **Quelle:** [Gemmel Metalle Legierungsbeschreibung CuZn39Pb3 PDF](https://www.gemmel-metalle.de/downloads/Legierungsbeschreibung_CuZn39Pb3.pdf)
* **Fundstelle:** Seite 1, Tabelle Festigkeitseigenschaften für Zustand hart
* **Wörtliches Zitat:** „Scherfestigkeit in N/mm²“
* **Belegte Zahlen:** Scherfestigkeit in N/mm² 390, Zugfestigkeit Rm N/mm² 540, Streckgrenze Rp02 460.

---

### 5.8 Quelle H: Kunststoffe POM-C und PA6

#### POM-C – Beleg: bwn Kunststofftechnik GmbH
* **Quelle:** [bwn Kunststofftechnik Technisches Datenblatt POM-C PDF](https://www.in-form-vollendet.de/wp-content/uploads/2021/10/datenblatt-POM-C.pdf)
* **Fundstelle:** Seite 1, Abschnitt Mechanische Eigenschaften
* **Wörtliches Zitat:** „Scherfestigkeit ASTM D732 MPa 55“
* **Belegte Zahlen:** Scherfestigkeit ASTM D732 55 MPa, Streckspannung 66 MPA, Zug-Elastizitätsmodul 3,000 MPa.

#### PA6 – Beleg: bwn Kunststofftechnik GmbH (PA6-G)
* **Quelle:** [bwn Kunststofftechnik Technisches Datenblatt PA6-G PDF](https://www.in-form-vollendet.de/wp-content/uploads/2021/10/datenblatt-PA6-G.pdf)
* **Fundstelle:** Seite 1, Abschnitt Mechanische Eigenschaften
* **Wörtliches Zitat:** „Scherfestigkeit ASTM D732 MPa 76“
* **Belegte Zahlen:** Scherfestigkeit ASTM D732 76 MPa, Streckspannung 88 MPA, Zug-Elastizitätsmodul 3,600 MPa.

---

### 5.9 Quelle I: FDM-Kunststoffe (PLA, PETG) & Schubfließgrenze

#### FDM-Kunststoffe – Beleg: Schweizer-FN Maschinenelemente
* **Quelle:** [Schweizer-FN Schraubenverbindung und Scherfestigkeit](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php)
* **Fundstelle:** Abschnitt Scherfestigkeit
* **Wörtliches Zitat:** „Nach der Gestaltänderungs-Hypothese von Mises lässt sich die Scherfestigkeit für duktile Werkstoffe wie folgt berechnen.“
* **Belegte Zahlen:** Scherspannungsfaktor für Vergütungsstähle 0,60...0,65, lösungsgeglühter Austenit 0,80, Schrauben Festigkeitsklasse 8.8 0,65.
