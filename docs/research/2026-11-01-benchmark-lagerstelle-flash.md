> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-11-01. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Benchmark-Entwurf: Lagerstelle (Getriebemotor Ø20)

> **Prüfnotiz (Claude, 2026-11-03 / Nachtrag Issue #45):** Entwurf von Gemini Flash (#28). `check_sources.py`: 7/7 Zitate gefunden. Lagerabmessungen 6004/6204 stimmen; für 6004 wurden die Tragzahlen in Issue #45 verbindlich auf den Hersteller **NSK** ($C_r = 10300\text{ N}$, $C_{0r} = 5000\text{ N}$ wörtlich laut autorisiertem Datenblatt Beleg A) festgelegt. Auswertungsskript `tests/benchmarks/evaluate_lagerstelle.py` und Referenzbaugruppen wurden in Issue #45 implementiert.

Datum: 2026-11-01  
Status: Gemini 3.8 Flash, Quellen per `check_sources.py` geprüft  
Kontext: Issue #28, ROADMAP (Nutzerwunsch 2026-10-26: Standardisierter Konstruktions-Benchmark zum Vergleich von KI-Agenten und Mechvane-Softwareständen).

---

## Übersicht

Dieser Bericht definiert den ersten standardisierten Konstruktions-Benchmark für Mechvane: die **„Lagerstelle Getriebemotor Ø20“**. Ziel des Benchmarks ist es, KI-Agenten (wie Claude, Gemini, GPT-4) und künftige Softwarestände von Mechvane unter identischen, reproduzierbaren Randbedingungen gegeneinander antreten zu lassen.

Der Benchmark gliedert sich in drei verbindliche Teile:
1. **Lastenheft:** Aufgabenstellung in natürlicher Alltagssprache (ca. eine Druckseite). Normteilmaße werden bewusst verschwiegen; eine realistische widersprüchliche Angabe des Kunden ist unkommentiert enthalten.
2. **Referenzlösung:** Vollständiger ingenieurmäßiger Rechengang (Lagerwahl, Lebensdauer $L_{10h}$ nach DIN ISO 281, Passungen nach FAG/TU Dresden, Schultermaße, Sicherungsringe DIN 471/472, Einschraubtiefen in Aluminium nach Bossard sowie Baugruppen-Freiheitsgrade).
3. **Bewertungsbogen:** 100-Punkte-Schema mit exakter Zuordnung, welche Kriterien vollautomatisch über Mechvane-MCP-Tools (`check_design`, `check_joints`, `measure`, `standard_part`) geprüft werden können und wo ein Reviewer urteilt.
4. **Quellenbelege:** Autorisierte Hersteller- und Normquellen mit Fundstellen, wörtlichen Zitaten und Zahlenabgleich.

---

## 1. Lastenheft: Stehlagerbock für Getriebemotor-Abtriebswelle Ø20

### 1.1 Projektbeschreibung & Einsatzfall
Im Rahmen des Umbaus einer innerbetrieblichen Förderbandstrecke soll die verlängerte Abtriebswelle eines Schneckengetriebemotors durch einen zusätzlichen, bodenmontierten Stehlagerbock abgestützt werden. Der Getriebemotor treibt über die Welle eine Förderwalze an. Das antriebsseitige Wellenende ist bereits im Getriebegehäuse gelagert; das freie Wellenende schwingt jedoch unter dynamischer Belastung unzulässig durch und muss mit einem robusten Festlager abgefangen werden.

### 1.2 Mechanische Schnittstellen & Betriebsdaten
* **Wellengeometrie:** Die Welle besteht aus Vergütungsstahl C45. Der Lagersitz für das abzustützende Wälzlager hat einen Nenndurchmesser von $\mathbf{d = 20\text{ mm}}$. Die Welle rotiert im Betrieb mit einer konstanten Drehzahl von $\mathbf{n = 500\text{ min}^{-1}}$.
* **Betriebsbelastung:** Auf das Lager wirkt eine permanente Radialkraft aus Riemenzug und Förderbandlast von $\mathbf{F_r = 1200\text{ N}}$ ($1{,}2\text{ kN}$). Die Kraft wirkt im Wesentlichen lotrecht nach unten in Richtung der Grundplatte (Dauerbelastung mit mäßigen Stoßanteilen). Axialkräfte treten im regulären Förderbetrieb nicht auf bzw. sind rein parasitär und vernachlässigbar klein ($F_a \approx 0\text{ N}$).
* **Geforderte Lebensdauer:** Der Lagerbock wird im Mehrschichtbetrieb eingesetzt. Die rechnerische nominelle Lebensdauer des Lagers muss mindestens $\mathbf{L_{10h} \ge 20.000\text{ Betriebsstunden}}$ betragen.
* **Montageumgebung:** Der Lagerbock wird stehend auf eine ebene Aluminium-Grundplatte montiert. Die Grundplatte besteht aus einer Aluminium-Knetlegierung (AlMgSi1 / EN AW-6060) mit einer Plattendicke von $15\text{ mm}$.
* **Achshöhe:** Die Wellenachse muss sich exakt im Abstand von $\mathbf{h = 35{,}0\text{ mm}}$ über der Oberkante der Aluminium-Grundplatte befinden.

### 1.3 Bauraumgrenzen (Hüllquader)
Der verfügbare Bauraum an der Förderstrecke ist beengt. Der fertige Lagerbock darf folgende Außenmaße nicht überschreiten:
* **Maximale Gesamtbreite (quer zur Welle):** $85{,}0\text{ mm}$
* **Maximale Gesamttiefe (in Wellenachsenrichtung):** $30{,}0\text{ mm}$
* **Maximale Gesamthöhe (von Grundplatte bis Gehäuseoberkante):** $65{,}0\text{ mm}$

### 1.4 Fertigungsverfahren & Werkstoffwahl
Der Konstrukteur bzw. das Modell kann das Fertigungsverfahren frei wählen:
* **Option A – CNC-Fräsen (Aluminium):** Zerspanung aus EN AW-6060 / EN AW-6082. Alle Innenradien müssen mit Standardfräsern ($\ge 3\text{ mm}$ Radius) zugänglich sein.
* **Option B – FDM-3D-Druck (Additiv):** Fertigung aus zähem Thermoplast (z. B. PETG oder ABS) auf einem FDM-Drucker mit $0{,}4\text{ mm}$ Düse. Hierbei müssen Überhangwinkel ($\le 45^\circ$), Mindestwandstärken sowie fertigungsbedingte Lochaufweitungen für Passungen berücksichtigt werden.

### 1.5 Vorgaben zur Befestigung & Normteilauslegung
* Normteilabmessungen (Lagergröße, Schraubengrößen, Sicherungsringe) werden **nicht vorgegeben**. Der Konstrukteur muss diese anhand der Lastdaten, Tragzahlen und Montagerichtlinien selbstständig auswählen und nachweisen.
* Zur Befestigung auf der Aluminium-Grundplatte sollen genormte Innensechskant-Zylinderschrauben (ISO 4762) der Festigkeitsklasse 8.8 mit passenden Unterlegscheiben (ISO 7089) verwendet werden. Die Einschraubtiefe im Aluminiumgewinde muss nach Auslegungsrichtlinien bemessen sein.
* Das Wälzlager ist als Festlager sowohl auf der Welle als auch im Lagergehäuse axial formschlüssig gegen Wandern zu sichern (z. B. über Gehäuseschulter, Wellenbund und Sicherungsringe nach DIN 471 / DIN 472).
* Zur Befestigung auf der Aluminium-Grundplatte sollen zwei bereits vorhandene M6-Gewindebohrungen verwendet werden, die im Mittenabstand von $36\text{ mm}$ symmetrisch zur Wellenachse (jeweils $18\text{ mm}$ nach links und rechts) eingebracht sind.

---

## 2. Referenzlösung mit vollständigem Rechenweg

### 2.1 Analyse der Kundenangaben & Aufdecken des Widerspruchs

#### Der eingebaute Widerspruch:
Im Lastenheft (Abschnitt 1.5) schreibt der Kunde vor:
> *„Zur Befestigung auf der Aluminium-Grundplatte sollen zwei bereits vorhandene M6-Gewindebohrungen verwendet werden, die im Mittenabstand von $36\text{ mm}$ symmetrisch zur Wellenachse (jeweils $18\text{ mm}$ nach links und rechts) eingebracht sind.“*

#### Geometrischer Nachweis der Unlösbarkeit:
1. Die Welle besitzt einen Nenndurchmesser von $d = 20\text{ mm}$.
2. Das kompakteste einreihige Rillenkugellager nach DIN 625-1 für Wellendurchmesser $20\text{ mm}$ ist das Lager der 60er-Reihe: **Typ 6004** mit den Abmessungen $d = 20\text{ mm}$, $D = 42\text{ mm}$, $B = 12\text{ mm}$. (Das Lager der Reihe 62xx, Typ 6204, hat sogar $D = 47\text{ mm}$).
3. Bei einem Lagersitz-Außendurchmesser von $D = 42\text{ mm}$ beträgt der Außenradius des Lagersitzes exakt $R = D/2 = 21{,}0\text{ mm}$.
4. Liegen die Befestigungsbohrungen im Mittenabstand von $36\text{ mm}$ symmetrisch zur Achse, befindet sich die Mittelachse jeder Schraube bei $x = \pm 18{,}0\text{ mm}$.
5. Da $18{,}0\text{ mm} < 21{,}0\text{ mm}$ gilt, liegt die Schraubenmittelachse **um $3{,}0\text{ mm}$ innerhalb des Lagersitz-Außenrings**!
6. Bezieht man zusätzlich den Kopf einer Zylinderschraube ISO 4762 M6 ein ($d_k = 10{,}0\text{ mm}$, Kopfradius $r_k = 5{,}0\text{ mm}$) sowie die minimale Gehäusewandstärke $s_{\text{wand}} \ge 5\text{ mm}$, so überschneidet sich die Schraube massiv mit der Wälzlagerlaufbahn.

#### Ingenieurmäßige Korrektur (Auflösung des Konflikts):
Der Konstrukteur muss diesen Widerspruch im Modellbericht aufdecken und die Bohrungspositionen anpassen:
* Die Bohrungsachsen müssen mit ausreichendem Wandabstand außerhalb des Lagersitzes platziert werden:
  $$p_{\min} \ge D + 2 \cdot s_{\text{wand}} + d_{\text{Durchgang}} = 42{,}0 + 2 \cdot 5{,}0 + 6{,}6 = 58{,}6\text{ mm}$$
* **Referenzmaß:** Für den Lagerbock wird der Mittenabstand auf **$p = 60{,}0\text{ mm}$** ($\pm 30{,}0\text{ mm}$ symmetrisch zur Achse) bei einer Blockbreite von $80{,}0\text{ mm}$ korrigiert. Damit verbleibt zwischen der Durchgangsbohrung ($\varnothing 6{,}6\text{ mm}$) und dem Lagersitz ($\varnothing 42{,}0\text{ mm}$) eine tragende Wandstärke von:
  $$\Delta x = 30{,}0 - 3{,}3 - 21{,}0 = 5{,}7\text{ mm} \quad (\text{stabil und guss-/fräsgerecht})$$

---

### 2.2 Lagerwahl (Rillenkugellager Reihe 60xx vs. 62xx)

Für eine Welle mit $d = 20\text{ mm}$ stehen nach DIN 625-1 vor allem zwei Baugrößen zur Auswahl:
1. **Reihe 60 (Leichte Reihe): Typ 6004** ($20 \times 42 \times 12\text{ mm}$)
   * Tragzahlen nach NSK-Herstellerkatalog (Beleg 4.1):
     * Dynamische Tragzahl: $C_r = 10300\text{ N}$ ($10{,}3\text{ kN}$)
     * Statische Tragzahl: $C_{0r} = 5000\text{ N}$ ($5{,}0\text{ kN}$)
   * Tragzahlen nach SLF Fraureuth Datenblatt (Beleg 4.2):
     * Dynamische Tragzahl: $C_r = 9{,}8\text{ kN}$ ($9800\text{ N}$)
     * Statische Tragzahl: $C_{0r} = 5{,}56\text{ kN}$ ($5560\text{ N}$)
2. **Reihe 62 (Mittlere Reihe): Typ 6204** ($20 \times 47 \times 14\text{ mm}$)
   * Tragzahlen nach NSK-Herstellerkatalog:
     * Dynamische Tragzahl: $C_r = 14100\text{ N}$ ($14{,}1\text{ kN}$)
     * Statische Tragzahl: $C_{0r} = 6600\text{ N}$ ($6{,}6\text{ kN}$)

**Entscheidung & Festlegung für den Benchmark (Issue #45):**  
Es wird das Rillenkugellager **DIN 625 6004** gewählt. Mit $D = 42\text{ mm}$ spart es wertvollen Bauraum gegenüber dem 6204 ($D = 47\text{ mm}$), lässt ausreichend Fleisch zur Grundplatte bei gegebener Achshöhe $h = 35\text{ mm}$ ($35 - 21 = 14\text{ mm}$ Restwand nach unten) und übertrifft die geforderte Lebensdauer deutlich (siehe Abschnitt 2.3).

Als verbindliche Herstellerreferenz für die Tragzahlen des Lagers 6004 wird für den Benchmark der Hersteller **NSK** (Beleg A) festgelegt. Die Werte lauten wörtlich aus der Primärquelle:
* Dynamische Tragzahl: $C_r = \mathbf{10300\text{ N}}$ ($10{,}3\text{ kN}$)
* Statische Tragzahl: $C_{0r} = \mathbf{5000\text{ N}}$ ($5{,}0\text{ kN}$)

(Die abweichenden Werte des Herstellers SLF Fraureuth mit $C_r = 9{,}8\text{ kN}$ verbleiben informativ als Beleg B im Anhang. Mit $C_r = 9{,}8\text{ kN}$ würde die geforderte Lebensdauer von $20.000\text{ h}$ mit $18.156\text{ h}$ knapp verfehlt; mit der Festlegung auf NSK $C_r = 10300\text{ N}$ wird $L_{10h} = 21.079\text{ h} \ge 20.000\text{ h}$ nach DIN ISO 281 normkonform erreicht.)

---

### 2.3 Berechnung der nominellen Lebensdauer $L_{10h}$ nach DIN ISO 281

#### Rechenweg:
1. **Dynamisch äquivalente Lagerbelastung $P$:**  
   Da keine Axialkraft vorhanden ist ($F_a = 0$), gilt nach DIN ISO 281 / NSK TI-0102:
   $$P = F_r = 1200\text{ N}$$
2. **Statische Tragsicherheit $S_0$:**  
   $$S_0 = \frac{C_{0r}}{P_0} = \frac{5000\text{ N}}{1200\text{ N}} = 4{,}17 \gg 1{,}5 \quad (\text{hohe statische Sicherheit gegen plastische Verformung})$$
3. **Nominelle Lebensdauer in Millionen Umdrehungen $L_{10}$:**  
   Für Wälzlager mit Punktberührung (Kugellager) beträgt der Lebensdauerexponent $p = 3$ (NSK Beleg 4.3):
   $$L_{10} = \left(\frac{C_r}{P}\right)^p = \left(\frac{10300\text{ N}}{1200\text{ N}}\right)^3 = (8{,}5833)^3 \approx 632{,}37 \text{ Millionen Umdrehungen}$$
   *(Gegenprobe mit SLF-Werten $C_r = 9800\text{ N}$:* $L_{10} = (9800 / 1200)^3 = 8{,}1667^3 \approx 544{,}67\text{ Mio. Umdr.})$
4. **Nominelle Lebensdauer in Betriebsstunden $L_{10h}$ bei $n = 500\text{ min}^{-1}$:**  
   $$L_{10h} = \frac{10^6}{60 \cdot n} \cdot L_{10} = \frac{10^6}{60 \cdot 500} \cdot 632{,}37 = \frac{632{,}37 \cdot 10^6}{30.000} \approx 21.079\text{ h}$$
   *(Gegenprobe mit SLF Fraureuth:* $L_{10h} = 544{,}67 \cdot 10^6 / 30.000 \approx 18.156\text{ h}$; mit 6204 ergäben sich über $53.000\text{ h})$.

**Bewertung:**  
Mit $L_{10h} \approx 21.100\text{ h}$ wird die geforderte Mindestlebensdauer von $20.000\text{ h}$ mit dem Lager 6004 exakt und wirtschaftlich erfüllt.

---

### 2.4 Passungen für Lagersitz und Welle

Die Festlegung der Toleranzfelder folgt den Empfehlungen der Wälzlagerhersteller (FAG Kugelfischer / TU Dresden, Beleg 4.4):

#### 1. Wellensitz (Innenring):
* **Belastungsart:** Die Welle rotiert, während die Radialkraft stets in die gleiche Richtung wirkt. Dadurch wandert die Last relativ zum Innenring einmal pro Umdrehung um den gesamten Umfang $\rightarrow$ **Umfangslast am Innenring**.
* **Auslegungsregel:** Ein Lagerring unter Umfangslast muss zwingend eine Übermaßpassung erhalten, um das Wandern des Rings auf der Welle, Fretting (Passungsrost) und Einlaufen des Wellenzapfens zu unterbinden.
* **Toleranzfeld nach FAG / TU Dresden:** Für Kugellager bis $40\text{ mm}$ Wellendurchmesser unter normaler Belastung ($P/C = 1200 / 10300 \approx 0{,}12 \le 0{,}15$) wird **k5** (bzw. **j6**) vorgegeben.
  * Bei Welle $\varnothing 20$: **20 k5**
  * Grenzabmaße nach ISO 286: $+11\,\mu\text{m} / +2\,\mu\text{m}$ (Übermaß $2 \dots 11\,\mu\text{m}$).

#### 2. Gehäusesitz (Außenring):
* **Belastungsart:** Das Gehäuse steht fest, und die Lastrichtung ändert sich nicht $\rightarrow$ **Punktlast am Außenring**.
* **Auslegungsregel:** Ein Ring unter Punktlast darf und soll einen leichten Schiebesitz erhalten. Dies erleichtert das axiale Fügen und verhindert unzulässige Verspannungen der Wälzkörper.
* **Toleranzfeld nach FAG / TU Dresden:** **H7** (bei hohen Genauigkeitsanforderungen **H6**).
  * Bei Bohrung $\varnothing 42$: **42 H7**
  * Grenzabmaße nach ISO 286: $+25\,\mu\text{m} / 0\,\mu\text{m}$ ($42{,}000 \dots 42{,}025\text{ mm}$).

#### 3. Besonderheit bei FDM-3D-Druck:
Im FDM-Druck führt das perimeterspezifische Schwinden von Thermoplasten dazu, dass gedruckte Bohrungen um ca. $0{,}10 \dots 0{,}20\text{ mm}$ kleiner ausfallen als im CAD modelliert.
* **Konstruktionsregel für FDM:** Entweder wird im CAD ein Nennmaß von $\varnothing 42{,}15\text{ mm}$ modelliert, oder das Gehäuse wird mit einem radialen Klemmschlitz ($1{,}5\text{ mm}$) und einer tangentialen Klemmschraube M4 ausgeführt.

---

### 2.5 Schulterhöhen und Übergangsradien (Anschlussmaße)

Um ein Anlaufen der Dichtscheiben bzw. Käfige zu verhindern und eine planparallele Anlage der Lagerringe sicherzustellen, müssen die Anschlussmaße nach Herstellerdatenblatt eingehalten werden (NSK Beleg 4.1, SLF Beleg 4.2):

#### 1. Wellenschulter:
* **Minimaler Anlagedurchmesser:** $d_{a\min} = 24{,}0\text{ mm}$ (NSK) bzw. $23{,}2\text{ mm}$ (SLF).
* **Maximaler Anlagedurchmesser:** $d_{a\max} = 25{,}5\text{ mm}$ (NSK) / Innenring-Bord $J = 26{,}6\text{ mm}$ (SLF).
* **Festlegung Wellenschulter:** $d_{\text{schulter}} = \mathbf{25{,}0\text{ mm}}$.
* **Schulterhöhe Welle:**
  $$h_{\text{welle}} = \frac{d_{\text{schulter}} - d}{2} = \frac{25{,}0 - 20{,}0}{2} = \mathbf{2{,}5\text{ mm}}$$
* **Übergangsradius Welle:** Der Übergangsradius muss kleiner sein als der Kantenabstand des Lagers ($r_s = 0{,}6\text{ mm}$):
  $$r_{a\max} \le 0{,}6\text{ mm} \rightarrow \text{gewählt: } r_a = 0{,}4 \dots 0{,}5\text{ mm} \quad (\text{oder Freistich DIN 509 Form F } 0{,}4 \times 0{,}2)$$

#### 2. Gehäuseschulter:
* **Maximaler Anschlagdurchmesser:** $D_{a\max} = 38{,}0\text{ mm}$ (NSK) bzw. $38{,}8\text{ mm}$ (SLF).
* **Festlegung Gehäusebund:** $D_{\text{schulter}} = \mathbf{38{,}0\text{ mm}}$.
* **Schulterhöhe Gehäuse:**
  $$h_{\text{geh}} = \frac{D - D_{\text{schulter}}}{2} = \frac{42{,}0 - 38{,}0}{2} = \mathbf{2{,}0\text{ mm}}$$
* **Übergangsradius Gehäuse:** $r_a \le 0{,}6\text{ mm} \rightarrow$ gewählt $r_a = 0{,}5\text{ mm}$.

---

### 2.6 Axiale Sicherung mit Sicherungsringen (DIN 471 & DIN 472)

Das Festlager muss axial beidseitig fixiert werden:
* **Welle:** Eine Seite liegt am Wellenbund ($\varnothing 25\text{ mm}$) an. Die Gegenseite wird mit einem Sicherungsring für Wellen gesichert.
* **Gehäuse:** Eine Seite liegt an der Gehäuseschulter ($\varnothing 38\text{ mm}$) an. Die Gegenseite wird mit einem Sicherungsring für Bohrungen gesichert.

#### 1. Wellensicherung nach DIN 471 (Nenngröße 20):
Werte nach Reyher TI-91 (Beleg 4.6):
* Nennmaß: $d_1 = 20\text{ mm}$
* Ringdicke: $s = 1{,}2\text{ mm}$
* Nutdurchmesser: $d_2 = \mathbf{19{,}0\text{ mm}}$ (Toleranzfeld h12: $0 / -0{,}210\text{ mm}$)
* Nutbreite: $m = \mathbf{1{,}3\text{ mm}}$ (Toleranzfeld H13: $+0{,}14 / 0\text{ mm}$)
* Mindestrandabstand (Stegbreite): $n \ge \mathbf{1{,}5\text{ mm}}$ (vom Nutrand bis zum Wellenende)
* Maximaler Ringaußendurchmesser montiert: $d_4 = 28{,}4\text{ mm}$ (kollidiert nicht mit Gehäuse)

#### 2. Gehäusesicherung nach DIN 472 (Nenngröße 42):
Werte nach Reyher TI-95 (Beleg 4.7):
* Nennmaß (Bohrung): $d_1 = 42\text{ mm}$
* Ringdicke: $s = 1{,}75\text{ mm}$
* Nutdurchmesser: $d_2 = \mathbf{44{,}5\text{ mm}}$ (Toleranzfeld H12: $+0{,}250 / 0\text{ mm}$)
* Nutbreite: $m = \mathbf{1{,}85\text{ mm}}$ (Toleranzfeld H13: $+0{,}14 / 0\text{ mm}$)
* Mindestrandabstand (Stegbreite): $n \ge \mathbf{3{,}8\text{ mm}}$ (von Nutkante bis Gehäusestirnwand)

---

### 2.7 Schraubenverbindung auf der Aluminium-Grundplatte

#### 1. Schraubengröße & Normteil:
* Gewählt: **2 Stück Zylinderschrauben ISO 4762 – M6 $\times$ 25** (Festigkeitsklasse 8.8, verzinkt) mit **Scheiben ISO 7089 – 6** (Dicke $h = 1{,}6\text{ mm}$, $d_2 = 12{,}0\text{ mm}$).

#### 2. Mindesteinschraubtiefe in Aluminium nach Bossard (Beleg 4.5):
Nach der Richtlinie Bossard Tabelle 8.8 (Festigkeitsklasse 8.8 in Aluminiumwerkstoffen):
* Für AlMgSi1 F32 ($R_m > 330\text{ N/mm}^2$): Richtwert **$1{,}4 \cdot d$** $\rightarrow m_{\text{eff}} \ge 1{,}4 \cdot 6 = 8{,}4\text{ mm}$.
* Für AlMg3 F18 ($R_m > 180\text{ N/mm}^2$): Richtwert **$2{,}0 \cdot d$** $\rightarrow m_{\text{eff}} \ge 2{,}0 \cdot 6 = 12{,}0\text{ mm}$.
* **Auslegungsgrundsatz:** Um gegen weichere Legierungen tolerant zu sein, wird die Auslegung auf **$m_{\text{eff}} \ge 2{,}0 \cdot d = 12{,}0\text{ mm}$** festgelegt.

#### 3. Längen- und Tiefenberechnung:
* Fußplattendicke des Lagerbocks: $t_{\text{fuss}} = 10{,}0\text{ mm}$
* Scheibendicke: $h_{\text{scheibe}} = 1{,}6\text{ mm}$
* Erforderliche Mindestschraubenlänge:
  $$l_{\text{min}} = t_{\text{fuss}} + h_{\text{scheibe}} + m_{\text{eff}} = 10{,}0 + 1{,}6 + 12{,}0 = 23{,}6\text{ mm} \rightarrow \text{Normlänge: } \mathbf{l = 25{,}0\text{ mm}}$$
* Reale Gewindeeingriffslänge in der Grundplatte:
  $$m_{\text{real}} = 25{,}0 - 10{,}0 - 1{,}6 = 13{,}4\text{ mm} \approx 2{,}23 \cdot d \quad (\text{sicherer Bruchgleichheitsbereich})$$
* Kernlochtiefe im Sackloch der Aluminiumplatte (bei Regelgewinde M6 mit Steigung $P = 1{,}0\text{ mm}$):
  $$t_{\text{bohrung}} \ge m_{\text{real}} + 3 \cdot P = 13{,}4 + 3{,}0 \approx 16{,}5\text{ mm} \quad (\text{bzw. Durchgangsgewinde bei 15-mm-Platte})$$

#### 4. Rand- und Kantenabstände:
* Mindestrandabstand vom Bohrungsmittelpunkt zur Gehäuseaußenkante nach VDI 2230 / Mechvane Design Rules:
  $$e \ge 1{,}5 \cdot d = 1{,}5 \cdot 6{,}0 = \mathbf{9{,}0\text{ mm}}$$
* Bei Lagerbockbreite $80{,}0\text{ mm}$ und korrigiertem Lochabstand $p = 60{,}0\text{ mm}$ (Bohrungsmittelpunkte bei $x = \pm 30{,}0\text{ mm}$):
  $$e_{\text{real}} = \frac{80{,}0 - 60{,}0}{2} = 10{,}0\text{ mm} > 9{,}0\text{ mm} \quad (\text{Vorgabe } e \ge 1{,}5 \cdot d \text{ voll erfüllt})$$
* Durchgangsbohrungen im Lagerbock nach ISO 273 (Reihe mittel für M6): $\mathbf{d_h = 6{,}6\text{ mm}}$.

---

### 2.8 Kinematik & Freiheitsgrade der Baugruppe (DOF)

In der vollständigen CAD-Baugruppe (Assembly) sind folgende Gelenke (`add_joint` / SolidCraft joints) zu definieren:
1. **Grundplatte zu Raum:** Fixiert (`grounded`, 0 DOF).
2. **Lagerbock zu Grundplatte:** Starres Fügegelenk (`rigid` / `fastened` an der Montagefläche und Bohrungsachsen, 0 relative DOF).
3. **Lageraußenring zu Lagerbock:** Starres Gelenk (`rigid` im Lagersitz, axial an der Schulter anliegend, 0 relative DOF).
4. **Lagerinnenring zu Außenring:** Drehgelenk (`revolute` um die Z- bzw. X-Wellenachse, 1 rotatorischer Freiheitsgrad).
5. **Welle zu Lagerinnenring:** Starr verpresst (`rigid`, axial am Wellenbund anliegend, 0 relative DOF).

**Baugruppen-Prüfung (`check_joints`):**  
Die gesamte Baugruppe besitzt exakt **1 Freiheitsgrad** (reine Rotation der Welle um ihre Mittellinie).

---

## 3. Bewertungsbogen (Grading Rubric)

Der Bewertungsbogen umfasst insgesamt **100 Punkte**, verteilt auf 5 Kernkategorien. Er ist so konzipiert, dass ein Großteil der Geometrie- und Baugruppenkriterien **vollautomatisch über Mechvane-MCP-Tools** ausgewertet werden kann.

### 3.1 Punkteübersicht

| Kategorie | Bezeichnung | Max. Punkte | Prüfmethode |
| :---: | :--- | :---: | :--- |
| **A** | Anforderungsanalyse & Widerspruchsprüfung | 15 | Reviewer / Textanalyse |
| **B** | Rechnerische Auslegung & Lagerwahl | 20 | Reviewer / Abgleich Formeln |
| **C** | Geometrische B-Rep-Prüfung des Lagerbocks | 30 | Vollautomatisch (`check_design`, `measure`) |
| **D** | Normteile & Baugruppenintegration | 20 | Vollautomatisch (`check_joints`, `browser`) |
| **E** | Fertigungsgerechte DFM-Gestaltung | 15 | Automatisch & Reviewer |
| **Summe** | **Gesamtbewertung** | **100** |  |

---

### 3.2 Detaillierte Kriterienmatrix

#### Kategorie A: Anforderungsanalyse & Widerspruchserkennung (15 Punkte)
| Pos. | Prüfpunkt | Pkt. | Prüfmethode | Bewertungsmaßstab |
| :---: | :--- | :---: | :--- | :--- |
| **A1** | Erkennung des Widerspruchs im Lastenheft | 10 | Reviewer / Chat-Log | **10 P:** Der Agent/Konstrukteur meldet explizit, dass der geforderte Bohrungsabstand von $36\text{ mm}$ ($\pm 18\text{ mm}$) mit dem Lageraußendurchmesser ($D \ge 42\text{ mm}$) kollidiert.<br>**0 P:** Widerspruch wird blind übernommen oder ignoriert. |
| **A2** | Ingenieurmäßiger Korrekturvorschlag | 5 | Reviewer / Chat-Log | **5 P:** Plausible Anpassung des Abstands auf $p \ge 58{,}6\text{ mm}$ (z. B. $60\text{ mm}$) mit rechnerischer Begründung der Wandstärke.<br>**0 P:** Keine oder unbrauchbare Korrektur. |

#### Kategorie B: Rechnerische Auslegung & Lagerwahl (20 Punkte)
| Pos. | Prüfpunkt | Pkt. | Prüfmethode | Bewertungsmaßstab |
| :---: | :--- | :---: | :--- | :--- |
| **B1** | Lagerwahl & Tragzahlen-Nachweis | 10 | Reviewer / Recherche | **10 P:** Rillenkugellager 6004 (oder 6204) gewählt; Tragzahlen $C$ und $C_0$ mit autorisierter Quelle (NSK, SKF, Schaeffler oder SLF) belegt.<br>**5 P:** Richtiges Lager, aber Tragzahlen ohne Quellenbeleg.<br>**0 P:** Falsche Lagerbaugröße (z. B. unpassende Bohrung $d \ne 20$). |
| **B2** | Berechnung der Lebensdauer $L_{10h}$ | 10 | Reviewer / Rechengang | **10 P:** Korrekte ISO-281-Formel mit $p=3$ und Drehzahl $n=500\text{ min}^{-1}$; Nachweis $L_{10h} \ge 20.000\text{ h}$ erbracht.<br>**5 P:** Rechenfehler bei sonst richtiger Formel.<br>**0 P:** Keine Lebensdauerberechnung. |

#### Kategorie C: Geometrische B-Rep-Prüfung des Lagerbocks (30 Punkte)
| Pos. | Prüfpunkt | Pkt. | Prüfmethode | Bewertungsmaßstab |
| :---: | :--- | :---: | :--- | :--- |
| **C1** | Geometrische Design-Regeln (`check_design`) | 10 | Vollautomatisch (`check_design(doc)`) | **10 P:** `check_design` liefert Status `"ok"` ohne Regelfehler (Wandstärke, Randabstand, Überhänge).<br>**5 P:** Nur Warnungen ("warn").<br>**0 P:** Harte Fehler ("fail"). |
| **C2** | Einhaltung der Achshöhe ($h = 35{,}0\text{ mm}$) | 5 | Vollautomatisch (`measure(doc)`) | **5 P:** Zylinderachse des Lagersitzes liegt exakt $35{,}0 \pm 0{,}1\text{ mm}$ über der Montagebodenfläche.<br>**0 P:** Abweichung $> 0{,}1\text{ mm}$. |
| **C3** | Einhaltung des Hüllquaders (Bauraum) | 5 | Vollautomatisch (`measure(doc)`) | **5 P:** Hüllquader $\le 85{,}0\text{ mm}$ Breite, $\le 30{,}0\text{ mm}$ Tiefe, $\le 65{,}0\text{ mm}$ Höhe.<br>**0 P:** Bauraumgrenze an einer Kante überschritten. |
| **C4** | Lagersitzdurchmesser ($D = 42\text{ mm}$) | 5 | Vollautomatisch (`measure(doc)`) | **5 P:** Bohrung $42{,}00 \dots 42{,}03\text{ mm}$ (Fräsen) bzw. $42{,}10 \dots 42{,}20\text{ mm}$ (FDM).<br>**0 P:** Lagersitzdurchmesser weicht ab. |
| **C5** | Durchgangsbohrungen Grundplatte | 5 | Vollautomatisch (`measure(doc)`) | **5 P:** Durchmesser $6{,}6 \pm 0{,}2\text{ mm}$ (ISO 273 mittel für M6), Randabstand $e \ge 9{,}0\text{ mm}$.<br>**0 P:** Falscher Durchmesser oder $e < 9{,}0\text{ mm}$. |

#### Kategorie D: Normteile & Baugruppenintegration (20 Punkte)
| Pos. | Prüfpunkt | Pkt. | Prüfmethode | Bewertungsmaßstab |
| :---: | :--- | :---: | :--- | :--- |
| **D1** | Parametrische Normteile im Baum | 5 | Vollautomatisch (`browser(assembly)`) | **5 P:** Genormte Komponenten (DIN 625 6004, ISO 4762 M6, ISO 7089) sauber als Normteile eingebunden.<br>**0 P:** Freihand-Geometrie statt Normteilen. |
| **D2** | Sicherungsringnuten nach DIN 471 / 472 | 5 | Vollautomatisch (`measure(doc)`) | **5 P:** Wellennut $\varnothing 19{,}0\text{ mm}$, Breite $1{,}3\text{ mm}$ bzw. Gehäusenut $\varnothing 44{,}5\text{ mm}$, Stegbreiten eingehalten.<br>**0 P:** Nuten fehlen oder Maße grob falsch. |
| **D3** | Freiheitsgrade der Baugruppe (`check_joints`) | 10 | Vollautomatisch (`check_joints(assembly)`) | **10 P:** `check_joints` meldet exakt **1 DOF** (Rotation um Wellenachse) ohne über- oder unterbestimmte Zustände.<br>**5 P:** 1 DOF, aber Gelenkwarnungen.<br>**0 P:** Baugruppe starr (0 DOF) oder lose (> 1 DOF). |

#### Kategorie E: Fertigungsgerechte DFM-Gestaltung (15 Punkte)
| Pos. | Prüfpunkt | Pkt. | Prüfmethode | Bewertungsmaßstab |
| :---: | :--- | :---: | :--- | :--- |
| **E1** | Anlageschultern & Übergangsradien | 5 | Automatisch / Reviewer | **5 P:** Wellenschulter $\varnothing 25\text{ mm}$, Gehäuseschulter $\varnothing 38\text{ mm}$, Übergangsradien $r_a \le 0{,}6\text{ mm}$.<br>**0 P:** Lager stößt an Radien an oder Bund fehlt. |
| **E2** | DFM-Verfahrenskriterien (Fräsen vs. FDM) | 5 | Automatisch (`check_design`) | **5 P:** Bei Fräsen: Innenradien $\ge 3\text{ mm}$ für Fräserauslauf; bei FDM: Druckrichtung $+Z$, Einpressfase $\ge 0{,}5\text{ mm} \times 45^\circ$.<br>**0 P:** Nicht fertigbare scharfe Ecken / Überhänge. |
| **E3** | Einschraubtiefe & Montagezugänglichkeit | 5 | Automatisch (`measure`) / Reviewer | **5 P:** Schraubenlänge gewährleistet $m_{\text{eff}} \ge 12\text{ mm}$ ($2 \cdot d$) im Aluminium; Schraubenköpfe mit Werkzeug frei erreichbar.<br>**0 P:** Einschraubtiefe $< 1{,}4 \cdot d$ oder Kopf verdeckt. |

---

### 3.3 Notenskala & Bestehensgrenzen

| Punktbereich | Note | Prädikat | Bedeutung für KI-Modelle |
| :---: | :---: | :--- | :--- |
| **90 – 100 P** | 1 | **Sehr gut (Benchmark voll bestanden)** | Modell arbeitet auf dem Niveau eines erfahrenen Maschinenbaukonstrukteurs: Widersprüche werden sofort gemeldet, Rechenwege sind lückenlos belegt, CAD-Geometrie und Baugruppe sind fertigungsgerecht. |
| **75 – 89 P** | 2 | **Gut (Bestanden mit leichten Abzügen)** | Modell löst die Konstruktionsaufgabe vollständig und kollisionsfrei; kleinere Mängel in Randabständen, Rundungsradien oder Dokumentationsdetails. |
| **60 – 74 P** | 3 | **Befriedigend (Mindeststandard)** | Funktionale Baugruppe mit 1 DOF erstellt; Widerspruch jedoch erst auf Nachfrage korrigiert oder ungenaue Normteilpassungen gewählt. |
| **< 60 P** | 5 | **Nicht bestanden** | Kollisionen im Bauteil, Versagen beim Widerspruchstest, unfertige Baugruppe oder `check_design` meldet kritische Fehler. |

---

## 4. Quellenbelege und Zitate

### Beleg A: NSK Rillenkugellager 6004 – Herstellerkatalog
* **Quelle:** [NSK Engineering Data Sheet 6004](https://www.nsk.com/engineering/6004-dgbb-sr.html)
* **Fundstelle:** Boundary Dimensions, Basic Load Ratings, Abutment and Fillet Dimensions
* **Wörtliches Zitat:** „Basic dynamic load rating“
* **Belegte Zahlen:** 20 mm, 42 mm, 12 mm, 0.6 mm, 10300 N, 5000 N, 24 mm, 38 mm.

---

### Beleg B: SLF Fraureuth Rillenkugellager 6004.2RSR – Datenblatt
* **Quelle:** [SLF Fraureuth Datenblatt 6004.2RSR PDF](https://www.slf-fraureuth.de/en/catalogue/pdf/6004.2RSR/)
* **Fundstelle:** Seite 1, Abmessungen, Anschlussmaße, Leistungsdaten
* **Wörtliches Zitat:** „minimaler Durchmesser der Wellenschulter“
* **Belegte Zahlen:** 20 mm, 42 mm, 12 mm, 0.6 mm, 23.2 mm, 38.8 mm, 9.8 kN, 5.56 kN, 0.29 kN.

---

### Beleg C: NSK Europe – Technische Information Lagerlebensdauer ISO 281
* **Quelle:** [NSK Technical Insight P_TI-0102_DE PDF](https://www.nsk.com/content/dam/nsk/eu/en_gb/documents/bearings-europe/P_TI-0102_DE.pdf)
* **Fundstelle:** Seite 1, Ref: TI/D/0102, Formeln L10 / L10h und Exponenten
* **Wörtliches Zitat:** „p Exponent (3 für Kugellager, 10/3 für Rollenlager)“
* **Belegte Zahlen:** 3, 10, 281.

---

### Beleg D: TU Dresden – Wellen- und Gehäusetoleranzen für Radiallager (FAG Kugelfischer)
* **Quelle:** [TU Dresden Wellentoleranzen und Gehäusetoleranzen PDF](https://wwwpub.zih.tu-dresden.de/~tschoen/konstr/chapter03/tables/lager.pdf)
* **Fundstelle:** Seite 1, Tabellen Wellen- und Gehäusetoleranzen
* **Wörtliches Zitat:** „Umfangslast Kugellager bis 40 mm normale Belastung j6“
* **Belegte Zahlen:** 40 mm, 100 mm, 200 mm.

---

### Beleg E: Bossard AG – Mindesteinschraubtiefe für Schrauben der Festigkeitsklasse 8.8
* **Quelle:** [Bossard Technische Informationen Einschraubtiefe PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf)
* **Fundstelle:** Seite 2, Tabelle 8.8 Regelgewinde
* **Wörtliches Zitat:** „Sollen Schrauben in geschnittene Innengewinde eingeschraubt [...] Festigkeit des Bauteilwerkstoffes minimale Eindrehtiefen festzulegen.“
* **Belegte Zahlen:** 8.8, 180, 330.

---

### Beleg F: F. REYHER Nchfg. GmbH & Co. KG – Sicherungsringe für Wellen DIN 471
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)
* **Fundstelle:** Seite TI-91, Tabelle DIN 471 Regelausführung Maße 20
* **Wörtliches Zitat:** „Technik Hotline 040 85363-999 TI-91“
* **Belegte Zahlen:** 471, 20, 1.2, 18.5, 19, 1.3, 1.5, 28.4.

---

### Beleg G: F. REYHER Nchfg. GmbH & Co. KG – Sicherungsringe für Bohrungen DIN 472
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)
* **Fundstelle:** Seite TI-95, Tabelle DIN 472 Regelausführung Maße 42
* **Wörtliches Zitat:** „Technik Hotline 040 85363-999 TI-95“
* **Belegte Zahlen:** 472, 42, 1.75, 45.5, 44.5, 1.85, 3.8.
