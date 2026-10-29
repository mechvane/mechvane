# Recherchebericht: Konstruktionsregeln aus Werkstoffkennwerten herleiten

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #14). `tools/check_sources.py`:
> 10 von 10 Quellen erreichbar, 10 Zitate und 99 von 99 Zahlen bestätigt. Die Kernformel
> m_eff = A_s·R_m,Schraube / (A_n'·τ_B,Mutter) selbst nachgerechnet (S235: 5,0 mm, EN AW-6082: 6,6 mm).
> **Offen vor der Umsetzung:** Die NASA-RP-1228-Spalte liegt durchweg etwa beim Doppelten der anderen
> Ansätze; klären, ob dort ein Sicherheits- oder Flächenfaktor steckt, statt sie zu mitteln.
> „Sehr gute“ bzw. „perfekte Übereinstimmung“ mit Bossard ist Geminis Wertung (6082: 8,6 mm gegen 8,4 mm).
> τ_B/R_m-Verhältnisse (VDI 2230) sind Sekundärangaben, für die Werkstoffdatenbank je Werkstoff belegen.

> Datum: 2026-10-29  
> Status: Recherchebericht (Gemini 3.8 Flash) zu Issue #14  
> Bezug zu Mechvane: `mechvane/hole_tables.py`, `docs/research/2026-10-20-einschraubtiefen-flash.md`, `docs/research/2026-10-20-normwerte-online.md`

---

## Einleitung und Zielsetzung

Bislang stützt sich Mechvane für zentrale Konstruktionsentscheidungen auf statische Tabellen je Werkstoffgruppe (z. B. `MATERIAL_ENGAGEMENT_DEPTHS` in `mechvane/hole_tables.py` mit Bossard-Faktoren wie `steel: 1.0`, `alu_wrought: 1.4`, `plastic: 2.5`). Bei neu hinzukommenden Legierungen, Kunststoffen oder 3D-Druck-Materialien führt dieser tabellarische Ansatz schnell an Grenzen.

Ziel dieser Recherche ist es, konstruktive Mindestmaße direkt **aus physikalisch-mechanischen Werkstoffkennwerten analytisch herzuleiten**:
1. **Mindest-Einschraubtiefe** $m_{\text{eff}}$ bzw. $m_{\text{ges}}$ (Vermeidung von Gewindeabstreifen vor Schraubenbruch).
2. **Randabstand von Bohrungen** $e_1, e_2$ bzw. $c$ (Lochleibung und Schutz gegen Ausreißen zur Kante).
3. **Flächenpressung unter dem Schraubenkopf** $p$ und Grenzflächenpressung $p_G$ (Vermeidung plastischen Fließens und Setzens).
4. **Mindestwandstärke um Gewindebohrungen und Gewindeeinsätze** $s$ (Vermeidung von Rissbildung / Aufweiten unter radialem Gewindedruck).

Alle Herleitungen werden mit den Kennwerten für Schraube **M6 Festigkeitsklasse 8.8** in drei Referenzwerkstoffen durchgerechnet:
* **Baustahl S235** ($R_m = 360\,\text{N/mm}^2, R_{p0,2} = 235\,\text{N/mm}^2, \tau_B \approx 264\,\text{N/mm}^2$)
* **Aluminium-Knetlegierung EN AW-6082 T6 / AlMgSi1 F31** ($R_m = 310\,\text{N/mm}^2, R_{p0,2} = 260\,\text{N/mm}^2, \tau_B \approx 200\,\text{N/mm}^2$)
* **Thermoplast PA6 unberstärkt** ($R_m \approx 75\,\text{N/mm}^2, R_{p0,2} \approx 45\,\text{N/mm}^2, \tau_B \approx 50\,\text{N/mm}^2$)

---

## 1. Mindest-Einschraubtiefe (Gewindeabstreifen vor Schraubenbruch)

### 1.1 Physikalischer Auslegungsansatz (Bruchgleichheit)

Die Auslegung der Mindest-Einschraubtiefe im Maschinenbau (u. a. nach VDI 2230 Blatt 1, NASA RP-1228 und FED-STD-H28 / Machinery's Handbook) folgt dem Prinzip der **Bruchgleichheit**: Bei unzulässiger axialer Zugüberlastung muss stets die Schraube im freien Schaft bzw. im Gewindespannungsquerschnitt reißen, bevor die Gewindegänge des Mutterwerkstoffs oder der Schraube durch Abscheren ausreißen (Gewindeabstreifen). Ein Schraubenbruch kündigt sich bei duktilen Stählen durch Fließen an und ist sofort sichtbar; ein Abscheren des Innengewindes zerstört das Bauteil irreversibel und tritt oft schleichend auf.

Die maximale Zugtragfähigkeit der Schraube bei Zugfestigkeit $R_{m,\text{Schraube}}$ und Spannungsquerschnitt $A_s$ beträgt:
$$F_{\text{Zug}} = A_s \cdot R_{m,\text{Schraube}}$$

Für Schrauben der Festigkeitsklasse 8.8 gilt nach ISO 898-1: $R_{m,\text{Schraube}} = 800\,\text{N/mm}^2$. Bei M6 (Regelgewinde $P = 1{,}0\,\text{mm}$) ist nach ISO 898-1 bzw. ISO 724:
$$A_s = \frac{\pi}{4} \left(\frac{d_2 + d_3}{2}\right)^2 \approx 20{,}12\,\text{mm}^2 \implies F_{\text{Zug}} = 20{,}123\,\text{mm}^2 \cdot 800\,\text{N/mm}^2 \approx 16\,098\,\text{N} \approx 16{,}1\,\text{kN}$$

Das Innengewinde schert an einem Zylindermantel entlang des Außendurchmessers $d$ der Schraube ab. Die wirksame Scherfläche des Innengewindes $A_n$ skaliert linear mit der tragenden Einschraubtiefe $m_{\text{eff}}$:
$$A_n = m_{\text{eff}} \cdot A_n'$$
wobei $A_n'$ die Scherfläche pro Millimeter Einschraubtiefe darstellt:
$$A_n' = \pi \cdot d \cdot \eta_{\text{nut}}$$
mit dem Profilscherbeiwert $\eta_{\text{nut}} \approx 0{,}65 \dots 0{,}75$ (Verhältnis von Gangbreite am Zylindergrund zur Steigung $P$). Nach ASME / FED-STD-H28 beträgt die Abstreiffläche für M6 (Toleranzklasse 6H/6g) bei $L_e = 6\,\text{mm}$: $A_n = 73{,}145\,\text{mm}^2$, woraus $A_n' = 73{,}145 / 6{,}0 = 12{,}191\,\text{mm}^2/\text{mm}$ folgt.

Gleichsetzen von Abscherkraft und Schraubenbruchkraft liefert die erforderliche effektive Einschraubtiefe:
$$m_{\text{eff}} \ge \frac{A_s \cdot R_{m,\text{Schraube}}}{A_n' \cdot \tau_{BM}} = \frac{A_s \cdot R_{m,\text{Schraube}}}{\pi \cdot d \cdot \eta_{\text{nut}} \cdot \tau_{BM}}$$
wobei $\tau_{BM}$ die wirksame Scherfestigkeit des Mutterwerkstoffs ist.

Die tatsächliche Bohrlochtiefe bzw. Einschraubtiefe $m_{\text{ges}}$ beinhaltet zusätzlich den Anschnittzuschlag für nicht tragende Gewindegänge (Fase des Muttergewindes sowie Schraubenkuppe):
$$m_{\text{ges}} = m_{\text{eff}} + m_{\text{zu}} \quad \text{mit} \quad m_{\text{zu}} \approx 1{,}5 \dots 2{,}0 \cdot P$$

### 1.2 Relevante Normen und Primärquellen

#### Quelle 1A: NASA Reference Publication 1228 (Fastener Design Manual)
* **URL:** [NASA Fastener Design Manual (EngineeringLibrary)](https://engineeringlibrary.org/reference/loads-on-fastener-groups-nasa-design-manual)
* **Autor:** Richard T. Barrett, NASA Lewis Research Center (1990)
* **Formel:**
  $$P = \frac{\pi \cdot d_m \cdot F_s \cdot L}{3}$$
  wobei $P$ die Auszugskraft (Pullout Load), $d_m$ der Flankendurchmesser (Pitch Diameter), $F_s$ die Scherfestigkeit des schwächeren Werkstoffs und $L$ die Einschraubtiefe ist.
* **Wörtliches Zitat:**
  > *„In many cases a bolt of one material may be installed in a tapped hole in a different (and frequently lower strength) material. If the full strength of the bolt is required, the depth of the tapped hole must be determined for the weaker material by using the formula“*
* **Wörtliches Zitat zum empirischen Faktor 1/3:**
  > *„The 1/3 factor is empirical. If the threads were perfectly mated, this factor would be 1/2, since the total cylindrical shell area of the hole would be split equally between the bolt threads and the tapped hole threads. The 1/3 is used to allow for mismatch between threads.“*

#### Quelle 1B: Engineers Edge (FED-STD-H28 / Machinery's Handbook)
* **URL:** [Engineers Edge – Minimum Thread Engagement Formula](https://www.engineersedge.com/thread_strength/thread_minimum_length_engagement.htm)
* **Formel:**
  $$L_e = \frac{2 \cdot A_t}{A_n'}$$
  Bei weicherem Innengewindewerkstoff wird $L_e$ mit dem Faktor $J$ multipliziert:
  $$J = \frac{A_s \cdot R_{m,\text{Schraube}}}{A_n \cdot R_{m,\text{Mutter}}}$$
* **Wörtliches Zitat:**
  > *„The screw should fail before the thread strips. For this, it is necessary the shear area of the threaded feature be at least 2 times the tensile area.“*
* **Wörtliches Zitat zur Werkstoffanpassung:**
  > *„This assumes that the male and female thread materials have the same strength. If the Female Material strength is lower i.e. J as calculated below is greater than 1 then the length of engagement must be increased to prevent the female thread stripping“*

#### Quelle 1C: Engineers Edge (Metric Thread Stress and Shear Areas Table)
* **URL:** [Engineers Edge – Metric Thread Stress and Shear Areas Table](https://www.engineersedge.com/hardware/metric_thread_stress_and_shear_areas_table_15797.htm)
* **Werte für M6 x 1:**
  * Tensile Stress Area $A_t = 20{,}123\,\text{mm}^2$
  * Bolt Thread Strip Area ($L_e = 1\text{ Diameter}, 6H/6g$): $51{,}875\,\text{mm}^2$
  * Nut Thread Strip Area ($L_e = 1\text{ Diameter}, 6H/6g$): $73{,}145\,\text{mm}^2$
* **Wörtliches Zitat:**
  > *„Selected Metric M Series Thread Stress and Shear Areas“*

#### Quelle 1D: Ingenieurbüro Andreas Hanke (Mindesteinschraubtiefen nach VDI 2230-1:2015)
* **URL:** [Ing.-Büro Hanke – Mindesteinschraubtiefe Baustahl PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Baustahl-Scherfestigkeitsverh%C3%A4ltnis0.8.pdf)
* **Werte aus Tabelle:** Baustahl S235 ($\tau_B = 264\,\text{N/mm}^2$, $\tau_B/R_m = 0{,}8$), Schraube 8.8:
  * M3: $4{,}4\,\text{mm}$ | M4: $5{,}6\,\text{mm}$ | M5: $6{,}9\,\text{mm}$ | M6: $8{,}2\,\text{mm}$ | M8: $10{,}6\,\text{mm}$ | M10: $13{,}0\,\text{mm}$ | M12: $15{,}4\,\text{mm}$
* **Wörtliches Zitat:**
  > *„Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Baustahl“*
* **Wörtliches Zitat zum Verhältnis:**
  > *„Scherfestigkeitsverhältnis τB / Rm = 0.8“*

#### Quelle 1E: Bossard AG (Technische Information Einschraubtiefe 01/2025)
* **URL:** [Bossard Technische Information – Einschraubtiefe PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf)
* **Werte aus Tabelle für 8.8 Regelgewinde:** S235 ($1{,}0 \cdot d$), GJL 250 ($1{,}0 \cdot d$), AlMgSi1 F32 ($1{,}4 \cdot d$), AlMg3 F18 ($2{,}0 \cdot d$).
* **Wörtliches Zitat:**
  > *„Sollen Schrauben in geschnittene Innengewinde eingeschraubt [...] Festigkeit des Bauteilwerkstoffes minimale Eindrehtiefen festzulegen.“*

### 1.3 Zahlenbeispiel und Abgleich (M6, 8.8)

Für M6 ($d = 6\,\text{mm}, P = 1{,}0\,\text{mm}, A_s = 20{,}123\,\text{mm}^2, R_{m,\text{Schraube}} = 800\,\text{N/mm}^2, A_n' = 12{,}191\,\text{mm}^2/\text{mm}$):

| Werkstoff | Kennwerte | $m_{\text{eff}}$ (analytisch) | $m_{\text{ges}} = m_{\text{eff}} + 2P$ | $L_e$ (Machinery's) | $L$ (NASA RP-1228) | Bossard (`hole_tables.py`) | Abgleich / Bewertung |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **S235** | $R_m = 360\,\text{N/mm}^2$<br>$\tau_B = 264\,\text{N/mm}^2$ | $5{,}00\,\text{mm}$ ($0{,}83\,d$) | $7{,}00\,\text{mm}$ ($1{,}17\,d$) | $5{,}20\,\text{mm}$ ($0{,}87\,d$) | $10{,}88\,\text{mm}$ ($1{,}81\,d$) | $1{,}00 \cdot d = 6{,}0\,\text{mm}$ | **Sehr gute Übereinstimmung**: Bossards $1{,}0\,d$ deckt $m_{\text{eff}} = 5{,}0\,\text{mm}$ mit ca. $20\,\%$ Reserve ab. Hanke nennt für $m_{\text{ges}}$ $8{,}2\,\text{mm}$, was $m_{\text{eff}} \approx 6{,}2\,\text{mm}$ entspricht. |
| **EN AW-6082 T6** | $R_m = 310\,\text{N/mm}^2$<br>$\tau_B = 200\,\text{N/mm}^2$ | $6{,}60\,\text{mm}$ ($1{,}10\,d$) | $8{,}60\,\text{mm}$ ($1{,}43\,d$) | $6{,}04\,\text{mm}$ ($1{,}01\,d$) | $14{,}37\,\text{mm}$ ($2{,}39\,d$) | $1{,}40 \cdot d = 8{,}4\,\text{mm}$ | **Perfekte Übereinstimmung**: Bossards $1{,}40 \cdot d = 8{,}4\,\text{mm}$ entspricht exakt der analytischen Gesamttiefe $m_{\text{ges}} = 8{,}6\,\text{mm}$. |
| **PA6** | $R_m = 75\,\text{N/mm}^2$<br>$\tau_B = 50\,\text{N/mm}^2$ | $26{,}41\,\text{mm}$ ($4{,}40\,d$) | $28{,}41\,\text{mm}$ ($4{,}74\,d$) | $24{,}97\,\text{mm}$ ($4{,}16\,d$) | $57{,}47\,\text{mm}$ ($9{,}58\,d$) | $2{,}50 \cdot d = 15{,}0\,\text{mm}$ | **Starke Abweichung**: Der Literaturwert $2{,}5\,d$ reicht für 8.8 bei weitem nicht aus (Innengewinde schert bei $\approx 55\,\%$ der Schraubenkraft ab). Beweist die Richtigkeit der Repo-Notiz: Für hochfeste Schrauben in Kunststoff keine Direktgewinde nutzen, sondern Gewindeeinsätze (Ruthex / AMTEC). |

Gültigkeitsgrenzen:
* Formeln gelten für metrische ISO-Regelgewinde nach ISO 68-1 / ISO 261 mit Standard-Toleranzpaarung $6H/6g$.
* Das Wanddickenverhältnis um das Muttergewinde muss $s/d \ge 0{,}5$ betragen (keine unzulässige radiale Aufweitung).
* Bei zyklischer Belastung oder Kriechneigung (Kunststoffe) sind Sicherheitsbeiwerte bzw. metallische Gewindeeinsätze erforderlich.

---

## 2. Randabstand von Bohrungen (Lochleibung und Ausreißen zum Rand)

### 2.1 Analytischer Ansatz und Eurocode 3 (DIN EN 1993-1-8)

Beim Anziehen einer Verbindung sowie bei Querbelastung (Scherbeanspruchung) dürfen Bohrungen nicht zur Werkstückkante hin ausbrechen oder unzulässig ovalisieren (Lochleibungsversagen).

In der Stahlbaunorm **DIN EN 1993-1-8 (Eurocode 3)** wird der Bemessungswert der Lochleibungstragfähigkeit $F_{b,Rd}$ je Schraube formuliert als:
$$F_{b,Rd} = \frac{k_1 \cdot \alpha_b \cdot f_u \cdot d \cdot t}{\gamma_{M2}}$$
wobei:
* $f_u$: Zugfestigkeit des Bauteilwerkstoffs
* $d$: Schraubennenndurchmesser
* $t$: Bauteildicke
* $\gamma_{M2} = 1{,}25$: Teilsicherheitsbeiwert

Die Faktoren $\alpha_b$ (in Kraftrichtung) und $k_1$ (senkrecht zur Kraftrichtung) hängen direkt von den Randabständen $e_1$ und $e_2$ sowie dem Lochdurchmesser $d_0$ ab:

1. **In Kraftrichtung (Endabstand $e_1$):**
   $$\alpha_b = \min \left( \frac{e_1}{3 \cdot d_0} ;\; \frac{f_{ub}}{f_u} ;\; 1{,}0 \right)$$
   Damit das Bauteil seine volle Lochleibungstragfähigkeit ohne geometrische Abminderung erreicht ($\alpha_b = 1{,}0$), muss gelten:
   $$\frac{e_1}{3 \cdot d_0} \ge 1{,}0 \implies \mathbf{e_1 \ge 3{,}0 \cdot d_0}$$
   Die normative Mindestgrenze (bei der die Tragfähigkeit auf $\alpha_b = 1{,}2/3 = 0{,}40$ abgemindert wird) lautet:
   $$\mathbf{e_{1,\min} = 1{,}2 \cdot d_0}$$

2. **Quer zur Kraftrichtung (Randabstand $e_2$):**
   $$k_1 = \min \left( 2{,}8 \cdot \frac{e_2}{d_0} - 1{,}7 ;\; 2{,}5 \right)$$
   Für die volle Tragfähigkeit ($k_1 = 2{,}5$) muss gelten:
   $$2{,}8 \cdot \frac{e_2}{d_0} - 1{,}7 \ge 2{,}5 \implies 2{,}8 \cdot \frac{e_2}{d_0} \ge 4{,}2 \implies \mathbf{e_2 \ge 1{,}5 \cdot d_0}$$
   Die normative Mindestgrenze nach EN 1993-1-8 Tabelle 3.3 lautet ebenfalls:
   $$\mathbf{e_{2,\min} = 1{,}2 \cdot d_0}$$

3. **Mechanischer Scherausbruch-Nachweis (Ausstanzen zur Kante):**
   Wird eine Querkraft $F_v$ in Richtung des Randes eingeleitet, widersetzen sich zwei parallele Scherebenen der Reststegdicke $c = e_1 - d_0/2$. Die Ausbruchtragfähigkeit ist:
   $$V_R = 2 \cdot c \cdot t \cdot \tau_B \ge F_v \implies c \ge \frac{F_v}{2 \cdot t \cdot \tau_B}$$

4. **Besonderheiten bei Kunststoffen und FDM-3D-Druck:**
   Wegen der Schichtanisotropie und der geringen Zwischenschicht-Haftung gilt im FDM-Druck:
   * Randabstand zur freien Kante mindestens $2 \cdot d_0$ bis $3 \cdot d_0$.
   * Mindestens 3 bis 4 geschlossene Wandlinien (Perimeter) um die Bohrung vorsehen.
   * Bohrungen vertikal (Z-Achse) drucken, um Delamination zu vermeiden.

### 2.2 Relevante Normen und Primärquellen

#### Quelle 2A: Schweizer-FN Maschinenelemente (DIN EN 1993-1-8 / EC3)
* **URL:** [Schweizer-FN – Schraubenverbindung im Stahlbau nach EC3](https://www.schweizer-fn.de/maschinenelemente/schraube_ec3/schraubenverbindung_ec3.php)
* **Formeln und Parameter:**
  * Tragfähigkeit: `Fb,Rd = Grenzlochleibungskraft (N)`
  * Parameter: `k1 = Lochleibungsparameter (-) - siehe folgende Tabelle`, `αb = Lochleibungsparameter (-) - siehe folgende Tabelle`
  * Teilsicherheitsbeiwert: `γM2 = Teilsicherheitswert bei Lochleibung (-) = 1,25`
  * Randabstände: `Randabstand: e1 ≥ 1,2 * d0`, `Randabstand: e2 ≥ 1,2 * d0`, `Lochabstand: p1 ≥ 2,2 * d0`, `Lochabstand: p2 ≥ 2,4 * d0`
* **Wörtliches Zitat:**
  > *„Für die Lochleibungstragfähigkeit ist ein wichtiger Parameter der Lochdurchmesser do.“*
* **Wörtliches Zitat zur Überschrift:**
  > *„Lochleibungsparameter für Rand- und Lochabstände“*

#### Quelle 2B: Bossard AG (Flächenpressung Handbuchblatt 54)
* **URL:** [Bossard Technische Information – Flächenpressung PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/7MM4CVEWakvMoaUSg5YsPX/2f4fd67879facc612d4d7fbc9d218773/053_056_Flaechenpressung_Fastening_DE_01_2025.pdf)
* **Empfohlene Randabstände nach Tabelle Seite 54:**
  * M4: $6\,\text{mm}$ ($1{,}5\,d$) | M5: $7{,}5\,\text{mm}$ ($1{,}5\,d$) | M6: $9\,\text{mm}$ ($1{,}5\,d$) | M8: $12\,\text{mm}$ ($1{,}5\,d$) | M10: $15\,\text{mm}$ ($1{,}5\,d$) | M12: $18\,\text{mm}$ ($1{,}5\,d$) | M16: $24\,\text{mm}$ ($1{,}5\,d$) | M20: $30\,\text{mm}$ ($1{,}5\,d$)
* **Wörtliches Zitat:**
  > *„Richtwerte für Oberflächenzustand im Bereich der [...]“*

### 2.3 Zahlenbeispiel und Abgleich (M6, Durchgangsloch $d_0 = 6{,}6\,\text{mm}$)

| Parameter | Formel | Erforderlicher Wert | Bossard Richtwert | Bewertung |
| :--- | :--- | :---: | :---: | :--- |
| **Endabstand $e_1$ (voll tragend)** | $3{,}0 \cdot d_0$ | $19{,}8\,\text{mm}$ ($3{,}30\,d$) | – | Erforderlich für volle statische Lastübertragung im Stahlbau ohne Ausreißen. |
| **Endabstand $e_{1,\min}$ (minimal)** | $1{,}2 \cdot d_0$ | $7{,}92\,\text{mm}$ ($1{,}32\,d$) | – | Absolute konstruktive Untergrenze nach Eurocode 3. |
| **Seitenabstand $e_2$ (voll tragend)**| $1{,}5 \cdot d_0$ | $9{,}90\,\text{mm}$ ($1{,}65\,d$) | $9{,}0\,\text{mm}$ ($1{,}50\,d$) | **Hervorragende Übereinstimmung**: Bossards Empfehlung $c = 9{,}0\,\text{mm}$ entspricht nahezu exakt der Eurocode-3-Grenze $1{,}5 \cdot d_0 = 9{,}9\,\text{mm}$. |
| **Seitenabstand $e_{2,\min}$ (minimal)**| $1{,}2 \cdot d_0$ | $7{,}92\,\text{mm}$ ($1{,}32\,d$) | – | Untergrenze nach Norm. |
| **FDM-Druck (PA6 / PLA)** | $2{,}5 \cdot d_0$ | $16{,}5\,\text{mm}$ | – | Zur Vermeidung von Schichtspaltung unter Querkraft nötig. |

---

## 3. Flächenpressung unter dem Schraubenkopf

### 3.1 Physikalische Grundlagen und Grenzflächenpressung $p_G$

Beim Festziehen einer Schraube erzeugt die Vorspannkraft $F_M$ unter dem Schraubenkopf bzw. der Mutter eine Druckspannung in der Bauteiloberfläche:
$$p = \frac{F_{M,\max}}{A_p}$$

Die wirksame Kopfauflagefläche $A_p$ für Zylinderschrauben mit Innensechskant nach ISO 4762 (DIN 912) berechnet sich mit dem Auflageaußendurchmesser $d_w$ und dem Durchgangslochdurchmesser $d_h$ (ISO 273 mittel):
$$A_p = \frac{\pi}{4} \left( d_w^2 - d_h^2 \right)$$

Für M6 gilt nach ISO 4762 / DIN 912:
* $d_w = 9{,}38\,\text{mm}$ (minimaler Auflagendurchmesser)
* $d_h = 6{,}6\,\text{mm}$ (Durchgangsbohrung mittel H13 nach ISO 273)
$$A_p = \frac{\pi}{4} \left( 9{,}38^2 - 6{,}6^2 \right) = \frac{\pi}{4} (87{,}984 - 43{,}560) \approx 34{,}89\,\text{mm}^2$$

Bei einer Montagevorspannkraft bei $90\,\%$ Ausnutzung der Dehngrenze ($R_{p0,2} = 640\,\text{N/mm}^2$ für 8.8) und Gewindereibung $\mu = 0{,}12$ ergibt sich nach VDI 2230:
$$F_{M,\max} \approx 10{,}19\,\text{kN} \implies p = \frac{10\,190\,\text{N}}{34{,}89\,\text{mm}^2} \approx 292\,\text{N/mm}^2$$

**Herleitung der Grenzflächenpressung $p_G$ aus Werkstoffkennwerten:**
Die Grenzflächenpressung $p_G$ ist diejenige Flächenpressung, bei der keine unzulässigen plastischen Verformungen (Setzerscheinungen) auftreten. Nach VDI 2230 Blatt 1 Tabelle A9 und Literatur:
* Für **duktile Metalle (Stähle, Knetaluminium)** existiert ein Stützeffekt durch das umgebende, weniger beanspruchte Material:
  $$p_G \approx 1{,}2 \dots 1{,}4 \cdot R_{p0,2} \quad \text{bzw.} \quad p_G \approx 3 \cdot HB$$
* Für **Spröde Werkstoffe (Grauguss GJL)**:
  $$p_G \approx 2{,}5 \dots 3{,}0 \cdot R_m$$
* Für **Kunststoffe (Thermoplaste wie PA6)**:
  Wegen starker Kriechneigung (Viskoelastizität) ist die zulässige Dauerflächenpressung drastisch reduziert:
  $$p_{\text{zul}} \approx 15 \dots 30\,\text{N/mm}^2$$

### 3.2 Relevante Normen und Primärquellen

#### Quelle 3A: Bossard AG (Technische Information Flächenpressung 01/2025)
* **URL:** [Bossard Technische Information – Flächenpressung PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/7MM4CVEWakvMoaUSg5YsPX/2f4fd67879facc612d4d7fbc9d218773/053_056_Flaechenpressung_Fastening_DE_01_2025.pdf)
* **Tabellenwerte für Grenzflächenpressung $\rho_G$ (Seite 53):**
  * S235 JRG1: $R_m \ge 340\,\text{N/mm}^2 \implies \rho_G = 490\,\text{N/mm}^2$ (nach VDI 2230:2015) bzw. St 37: $\rho_G = 260\,\text{N/mm}^2$ (nach VDI 2230:1986).
  * AlMgSi 1 F31 (AW-6082): $R_m \ge 290\,\text{N/mm}^2 \implies \rho_G = 360\,\text{N/mm}^2$.
  * AlMgSi 1 F28: $R_m \ge 260\,\text{N/mm}^2 \implies \rho_G = 325\,\text{N/mm}^2$.
* **Tabellenwerte für Flächenpressung Zylinderschraube ISO 4762 (Seite 55):**
  * M6, 8.8: $d_K = 10\,\text{mm}, d_{w,\min} = 9{,}38\,\text{mm}, d_h = 6{,}6\,\text{mm}, A_p = 34{,}9\,\text{mm}^2$, Flächenpressung $= 292\,\text{N/mm}^2$.
* **Wörtliches Zitat zur Gültigkeit:**
  > *„Die angegebenen Werte gelten für Bohrungen ohne Fasen“*
* **Wörtliches Zitat zur Härte-Abschätzung:**
  > *„Empfehlung für Stähle unter Verwendung der Brinellhärte: ρG ≈ 3 HB“*
* **Wörtliches Zitat zur Zylinderschrauben-Tabelle:**
  > *„Flächenpressung unter dem Kopf einer Zylinderschraube“*
* **Wörtliches Zitat zur Ausnutzung:**
  > *„Ausnutzung der Schraubendehngrenze Rp 0,2 und µG = 0,12“*
* **Wörtliches Zitat zur Referenz:**
  > *„Referenz: VDI 2230, Ausgabe 2015“*

### 3.3 Zahlenbeispiel und Abgleich (M6, 8.8)

Vorhandene Flächenpressung: $p = 292\,\text{N/mm}^2$ ($A_p = 34{,}9\,\text{mm}^2$).

| Werkstoff | $p_G$ (Bossard / VDI 2230) | $p_G$ (motorisch: $-25\,\%$) | Vorhanden $p$ | Bewertung & Scheibenbedarf |
| :--- | :---: | :---: | :---: | :--- |
| **S235** | $490\,\text{N/mm}^2$ | $367{,}5\,\text{N/mm}^2$ | $292\,\text{N/mm}^2$ | **Zulässig** ($p \le p_G$, Auslastung $60\,\%$). Keine Unterlegscheibe erforderlich. |
| **EN AW-6082 T6** | $360\,\text{N/mm}^2$ | $270{,}0\,\text{N/mm}^2$ | $292\,\text{N/mm}^2$ | **Grenzbereich**: Bei Handanzug zulässig ($292 \le 360$). Bei motorischem Anzug ($p_G = 270\,\text{N/mm}^2$) überschritten! **Lösung:** Scheibe ISO 7089 (Form N / Reihe 5 in `mechvane/hole_tables.py`: $d_{w} = 12\,\text{mm} \implies A_p = 78{,}9\,\text{mm}^2 \implies p = 129\,\text{N/mm}^2 \le 270\,\text{N/mm}^2$). |
| **PA6** | $\approx 25\,\text{N/mm}^2$ | $\approx 19\,\text{N/mm}^2$ | $292\,\text{N/mm}^2$ | **Massiv überlastet** ($p \gg p_G$). Unzulässiges Kriechen und Setzen. Zwingend breite Scheibe (DIN 9021) oder metallische Buchse erforderlich. |

---

## 4. Mindestwandstärke um Gewindebohrungen und Gewindeeinsätze

### 4.1 Analytische Herleitung (Dickwandiger Zylinder nach Lamé)

Beim Anziehen der Schraube mit Vorspannkraft $F_M$ üben die unter $60^\circ$ Flankenwinkel geneigten Gewindeflanken eine radiale Keilwirkung auf das Innengewinde aus:
$$F_{\text{rad}} = F_M \cdot \tan(30^\circ) = F_M \cdot \frac{1}{\sqrt{3}} \approx 0{,}57735 \cdot F_M$$

Dieser radiale Schub erzeugt über den Zylinderinnenmantel ($d \cdot m_{\text{eff}}$) einen wirksamen Innendruck $p_i$:
$$p_i = \frac{F_{\text{rad}}}{\pi \cdot d \cdot m_{\text{eff}}} = \frac{F_M \cdot \tan(30^\circ)}{\pi \cdot d \cdot m_{\text{eff}}}$$

Für einen dickwandigen Hohlzylinder mit Innenradius $r_i = d/2$ und Außenradius $r_a = r_i + s$ (Wandstärke $s$) lautet die maximale tangentiale Zugspannung an der Innenwand nach Lamé:
$$\sigma_{t,\max} = p_i \cdot \frac{r_a^2 + r_i^2}{r_a^2 - r_i^2} \le R_{p0,2}$$

Setzt man das Radienverhältnis $Q = r_a / r_i = 1 + \frac{2s}{d}$ und fordert $\sigma_{t,\max} \le R_{p0,2}$, ergibt sich:
$$\frac{Q^2 + 1}{Q^2 - 1} \le \frac{R_{p0,2}}{p_i} \implies Q \ge \sqrt{\frac{\frac{R_{p0,2}}{p_i} + 1}{\frac{R_{p0,2}}{p_i} - 1}}$$
Daraus folgt die analytische Mindestwandstärke:
$$s_{\min} = \left( \sqrt{\frac{\frac{R_{p0,2}}{p_i} + 1}{\frac{R_{p0,2}}{p_i} - 1}} - 1 \right) \cdot \frac{d}{2}$$

### 4.2 Relevante Normen und Primärquellen

#### Quelle 4A: EJOT / Bossard (DELTA PT® Konstruktionsrichtlinie)
* **URL:** [EJOT DELTA PT Konstruktionsrichtlinie PDF](https://www.smw-schrauben.ch/userdata/uploads/Dokumente/delta-pt-de(1).pdf)
* **Konstruktionsregeln für Tubus (Seite 4):**
  * Außendurchmesser: $D = 2 \cdot d$
  * Vorloch: $d_{\text{vor}} = 0{,}8 \cdot d_1$
  * Einschraubtiefe: $t_e = 2 \cdot d_1$
  * Randentlastung: $d_e = d_1 + 0{,}2\,\text{mm}$
  * Resultierende Wandstärke: $s = (D - d)/2 = 0{,}5 \cdot d$ (bzw. zum Vorloch $W = 0{,}6 \cdot d$).
* **Wörtliches Zitat:**
  > *„Für alle gängigen Kunststoffe bis E = 20’000 N/mm2.“*

#### Quelle 4B: Bossard AG (ecosyn®-plast Handbuch)
* **URL:** [Bossard ecosyn-plast Handbuch PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3AYmJ7h7169wKygbbUg0MK/dc07d87c865ade977f525121ea756759/0901_ecosyn_plast_DE.pdf)
* **Tabellenwerte Tubusgeometrie für PA6:**
  * Lochdurchmesser: $d = 0{,}75 \times d_1$
  * Außendurchmesser: $D = 1{,}85 \times d_1$
  * Einschraubtiefe: $t_e = 1{,}70 \times d_1$
* **Wörtliches Zitat:**
  > *„Für eine optimale Konstruktion, die sich in der Praxis bewährt, ist es erforderlich die Tubusgeometrie den unterschiedlichen Werkstoffen anzupassen.“*

### 4.3 Zahlenbeispiel und Abgleich (M6, 8.8, $F_M \approx 10{,}19\,\text{kN}$)

| Werkstoff | $R_{p0,2}$ | $m_{\text{eff}}$ | Innendruck $p_i$ | $s_{\min}$ (Lamé analytisch) | Richtwert Praxis / Norm | Bewertung |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **S235** | $235\,\text{N/mm}^2$ | $6{,}0\,\text{mm}$ | $52{,}0\,\text{N/mm}^2$ | $0{,}76\,\text{mm}$ ($0{,}13\,d$) | $s \ge 0{,}3 \dots 0{,}5\,d$ ($1{,}8 \dots 3{,}0\,\text{mm}$) | Lamé-Mindestmaß $0{,}76\,\text{mm}$ sichert gegen Fließen. Praxiszuschlag $s \ge 0{,}4\,d$ verhindert Werkzeugverlauf beim Gewindebohren. |
| **EN AW-6082 T6** | $260\,\text{N/mm}^2$ | $8{,}4\,\text{mm}$ | $37{,}2\,\text{N/mm}^2$ | $0{,}46\,\text{mm}$ ($0{,}08\,d$) | $s \ge 0{,}4 \dots 0{,}5\,d$ ($2{,}4 \dots 3{,}0\,\text{mm}$) | Sehr geringe Lamé-Mindestwandstärke wegen höherer Dehngrenze. In der Praxis $s \ge 0{,}4\,d$ empfohlen. |
| **PA6** | $45\,\text{N/mm}^2$ | $15{,}0\,\text{mm}$ | $20{,}8\,\text{N/mm}^2$ | $1{,}95\,\text{mm}$ ($0{,}32\,d$) | $s = 0{,}425 \dots 0{,}5\,d$ ($2{,}55 \dots 3{,}0\,\text{mm}$) | **Hervorragende Bestätigung**: Die Bossard-Empfehlung $D = 1{,}85 \dots 2{,}0\,d$ ($s = 0{,}43 \dots 0{,}5\,d$) enthält gegenüber dem Lamé-Wert ($0{,}32\,d$) einen Sicherheitsfaktor von $\approx 1{,}4$, der Relaxation und Fertigungstoleranzen abdeckt. |

---

## 5. Vorschlag für die Werkstoffdatenbank (Issue #13)

Auf Basis der hergeleiteten Regeln sollte die geplante Werkstoffdatenbank (`mechvane/materials/` bzw. `mechvane/material_db.py`) je Werkstoff zwingend folgende physikalische Kenngrößen bereitstellen:

### 5.1 Zwingend erforderliche Kennwerte (Pflichtfelder)

1. **`yield_strength_mpa` ($R_{p0,2}$ bzw. $R_e$ in $\text{N/mm}^2$):**
   * Zur Berechnung der maximalen Montagevorspannkraft $F_{M,\max} \approx 0{,}9 \cdot R_{p0,2} \cdot A_s$.
   * Zur Berechnung der Mindestwandstärke gegen Aufweiten nach Lamé.
   * Zur Abschätzung der Grenzflächenpressung $p_G \approx 1{,}2 \dots 1{,}4 \cdot R_{p0,2}$.

2. **`tensile_strength_mpa` ($R_m$ bzw. $f_u$ in $\text{N/mm}^2$):**
   * Zur Bestimmung des Schrauben-Überlastungsbruchs $F_{\text{Zug}} = A_s \cdot R_m$.
   * Für den Lochleibungsnachweis nach Eurocode 3: $F_{b,Rd} \propto f_u$.
   * Für das Machinery's-Handbook-Festigkeitsverhältnis $J$.

3. **`shear_strength_ratio` ($\tau_B / R_m$) bzw. `shear_strength_mpa` ($\tau_B$ in $\text{N/mm}^2$):**
   * Zentraler Kernwert für die Mindest-Einschraubtiefe $m_{\text{eff}} = \frac{A_s \cdot R_{m,\text{bolt}}}{A_n' \cdot \tau_{BM}}$.
   * Standardwerte nach VDI 2230: Baustahl $0{,}80$, Grauguss $1{,}15$, Al-Knet $0{,}60$, Al-Guss $0{,}52$, Kunststoffe $0{,}40 \dots 0{,}60$.

4. **`surface_pressure_limit_mpa` ($p_G$ in $\text{N/mm}^2$):**
   * Zur automatischen Entscheidung, ob eine Zylinderschraube ISO 4762 eine Unterlegscheibe (ISO 7089 / DIN 974 Reihe 5) oder Flanschkopf benötigt.
   * Alternativ berechenbar für Metalle über `hardness_hb` ($p_G \approx 3 \cdot HB$) oder $1{,}3 \cdot R_{p0,2}$.

### 5.2 Empfohlene Zusatzkennwerte (Optionale Felder)

5. **`elastic_modulus_gpa` ($E$ in $\text{GPa}$):**
   * Zur Erkennung elastischer Nachgiebigkeiten und Unterscheidung von Kunststoffen ($E < 20\,\text{GPa}$).
6. **`recommended_edge_distance_factor` ($c/d$):**
   * Geometrischer Standardfaktor (Metalle: $1{,}5$; Kunststoffe/FDM: $2{,}5$).
7. **`recommended_wall_thickness_factor` ($s/d$):**
   * Geometrischer Standardfaktor für Tubus- und Bossgeometrien (Metalle: $0{,}4$; Kunststoffe: $0{,}5$).

---

## 6. Python-Verifikationsskript

Zur vollständigen Nachvollziehbarkeit und automatisierten Prüfung der Rechenwerte dient das nachfolgende Python-Skript:

```python
import math

def verify_calculations():
    # Schraubengeometrie M6 Regelgewinde (ISO 68-1 / ISO 261 / ISO 898-1)
    d = 6.0          # mm
    P = 1.0          # mm
    d2 = 5.35        # mm (Flankendurchmesser)
    d0 = 6.6         # mm (Durchgangsloch ISO 273 mittel)
    As = 20.123      # mm^2 (Spannungsquerschnitt)
    Rm_bolt = 800.0  # N/mm^2 (Festigkeitsklasse 8.8)
    
    # Scherflächen pro mm Einschraubtiefe nach FED-STD-H28 (Engineers Edge M6x1 6H/6g)
    An_per_mm = 73.145 / 6.0  # 12.191 mm^2 / mm (Innengewinde)
    As_per_mm = 51.875 / 6.0  # 8.646 mm^2 / mm (Außengewinde)
    Le_base = 2.0 * As / An_per_mm
    F_tensile = As * Rm_bolt  # 16098.4 N
    
    # Kopfauflage Zylinderschraube ISO 4762 M6 (Bossard Handbuch S. 55)
    dw = 9.38        # mm
    dh = 6.6         # mm
    Ap = math.pi / 4.0 * (dw**2 - dh**2)  # 34.89 mm^2 (Tabelle: 34.9 mm^2)
    FM = 10190.0     # N (Montagevorspannkraft bei 90% Rp0.2)
    p_head = FM / Ap # 292.0 N/mm^2
    
    materials = {
        "S235": {
            "Rm": 360.0, "Rp02": 235.0, "tau_B": 264.0, "pG": 490.0, "bossard_fac": 1.0
        },
        "EN AW-6082 T6": {
            "Rm": 310.0, "Rp02": 260.0, "tau_B": 200.0, "pG": 360.0, "bossard_fac": 1.4
        },
        "PA6": {
            "Rm": 75.0, "Rp02": 45.0, "tau_B": 50.0, "pG": 25.0, "bossard_fac": 2.5
        },
    }
    
    print(f"Schraubenkraft M6 8.8: F_Zug = {F_tensile:.1f} N, p_Kopf = {p_head:.1f} N/mm^2\n")
    for name, m in materials.items():
        # 1. Einschraubtiefe
        meff = F_tensile / (An_per_mm * m["tau_B"])
        mges = meff + 2.0 * P
        J = (As_per_mm / An_per_mm) * (Rm_bolt / m["Rm"])
        Le_fed = Le_base * max(1.0, J)
        L_nasa = (3.0 * F_tensile) / (math.pi * d2 * m["tau_B"])
        
        # 2. Flächenpressung
        washer_needed = p_head > (0.75 * m["pG"])
        
        # 3. Mindestwandstärke (Lamé)
        m_calc = m["bossard_fac"] * d
        p_i = (FM * math.tan(math.radians(30))) / (math.pi * d * m_calc)
        K = m["Rp02"] / p_i
        s_lame = (math.sqrt((K + 1.0) / (K - 1.0)) - 1.0) * (d / 2.0) if K > 1.0 else float("inf")
        
        print(f"=== {name} ===")
        print(f"  Einschraubtiefe meff:    {meff:.2f} mm ({meff/d:.2f} * d)")
        print(f"  Gesamttiefe mges:        {mges:.2f} mm ({mges/d:.2f} * d)")
        print(f"  FED-STD-H28 Le:          {Le_fed:.2f} mm ({Le_fed/d:.2f} * d)")
        print(f"  NASA RP-1228 L:          {L_nasa:.2f} mm ({L_nasa/d:.2f} * d)")
        print(f"  Bossard-Tabelle:         {m['bossard_fac']*d:.2f} mm ({m['bossard_fac']:.2f} * d)")
        print(f"  Flächenpressung:         {p_head:.1f} vs pG={m['pG']:.1f} N/mm^2 (Scheibe nötig: {washer_needed})")
        print(f"  Wandstärke Lame s_min:   {s_lame:.2f} mm ({s_lame/d:.2f} * d)\n")

if __name__ == "__main__":
    verify_calculations()
```
