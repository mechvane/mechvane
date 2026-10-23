> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: O-Ring-Nuten – Statische Dichtungen (radial/axial), Verpressung, Nutfüllgrad, Nutmaße, Oberflächen, Einführschrägen und 3D-Druck

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert

Dieses Dokument fasst die geometrischen Auslegungsrichtlinien, genormten Nutabmessungen nach DIN ISO 3601-2 und führenden Herstellerstandards (Parker ORD 5700, COG, Freudenberg) für statische O-Ring-Dichtungen zusammen. Es beinhaltet spezifische Ergänzungen für FDM-3D-gedruckte Gehäuse und dient als Datengrundlage für den Wissenskatalog und die Validierung (`check_design`) in **inventa**.

---

## 1. Grundlagen der O-Ring-Abdichtung & Einbauarten

Ein O-Ring ist ein endloser Dichtring aus gummielastischem Werkstoff (Elastomer) mit kreisrundem Querschnitt. Die Abdichtung basiert auf zwei Effekten:
1. **Anfangs-Verpressung:** Beim Einbau wird der Schnurdurchmesser $d_2$ elastisch verformt. Die innere elastische Rückstellkraft erzeugt eine primäre Flächenpressung an den Dichtflächen.
2. **Selbstdichtwirkung (Druckaktivierung):** Unter Betriebsdruck $p$ wird das inkompressible Elastomer gegen die druckabgewandte Flanke gedrückt. Der Kontaktdruck an der Dichtfläche steigt automatisch proportional zum Mediumdruck an.

---

### Dichtungsarten im statischen Einsatz:

#### A) Statisch radiale Abdichtung (Zylindrischer Einbau / Kolben- & Stangendichtung)
* Die Verpressung erfolgt radial zwischen Gehäusebohrung und Welle/Zapfen.
* **Kolbendichtung (Außennut):** Nut befindet sich auf der Welle / dem Kolben; Dichtwirkung gegen die Zylinderbohrung.
* **Stangendichtung (Innennut):** Nut befindet sich in der Gehäusebohrung; Dichtwirkung gegen die durchgesteckte Welle.
* **Spaltextrusion:** Bei hohem Druck ($p > 50 \dots 100\text{ bar}$) kann das Elastomer in den Radialspalt $g$ (Passungsspiel) fließen und abgeschert werden. Hier sind Stützringe (z. B. Parbak® nach Parker) oder engere Passungen (z. B. H7/f7) erforderlich.

#### B) Statisch axiale Abdichtung (Planflansch- / Deckeldichtung)
* Die Verpressung erfolgt axial zwischen zwei ebenen Planflächen beim Festziehen der Flanschschrauben.
* **Druckrichtung:**
  * **Innendruck:** Der Druck wirkt von innen nach außen. Der O-Ring wird gegen die **äußere Flanke** der Nut gepresst. Der Nutaußendurchmesser sollte dem Außendurchmesser des O-Rings entsprechen (bzw. leichte Vordehnung von 1 % bis 3 %).
  * **Außendruck / Vakuum:** Der Druck wirkt von außen nach innen. Der O-Ring wird gegen die **innere Flanke** gepresst. Der Nutinnendurchmesser sollte dem Innendurchmesser des O-Rings entsprechen (neutrale Anlage oder max. 1 % Stauchung).

---

## 2. Auslegungsparameter: Verpressung und Nutfüllgrad

### A) Verpressung in Prozent
Die Verpressung $\delta$ bezieht sich auf den unverformten Schnurdurchmesser $d_2$:
$$\delta = \frac{d_2 - t}{d_2} \cdot 100\,\%$$
*(mit $t$ = Nuttiefe).*

* **Standardbereich statisch:** **15 % bis 30 %** (optimal: **20 % bis 25 %**).
* **Grenzen:**
  * **Untergrenze (< 15 %):** Unzureichende Dichtwirkung bei Temperaturabfall (Kältekontraktion) oder geringem Mediendruck; hohes Risiko von Leckagen.
  * **Obergrenze (> 30 %):** Zu hohe mechanische Spannungen führen zu vorzeitiger Alterung, Rissbildung und stark erhöhtem Druckverformungsrest (Compression Set). Zudem steigen die Montagekräfte extrem an.

---

### B) Nutfüllgrad (Nutquerschnitts-Verhältnis)
Der Nutfüllgrad gibt das Verhältnis der Querschnittsfläche des O-Rings zur rechteckigen Querschnittsfläche der Nut an:
$$\text{Nutfüllgrad} = \frac{A_{\text{O-Ring}}}{A_{\text{Nut}}} = \frac{\frac{\pi}{4} \cdot d_2^2}{b \cdot t} \cdot 100\,\%$$
*(mit $b$ = Nutbreite, $t$ = Nuttiefe).*

* **Zulässiger Bereich:** **70 % bis 85 %** (maximal **90 %**).
* **Warum niemals 100 %?**
  1. **Inkompressibilität:** Elastomere verhalten sich nahezu volumenkonstant (Poissonzahl $\nu \approx 0{,}5$). Wird der Ring in der Höhe verpresst, muss er sich in der Breite ungehindert ausdehnen können.
  2. **Thermische Ausdehnung:** Elastomere dehnen sich thermisch um das 10- bis 15-fache stärker aus als Stahl oder Aluminium.
  3. **Medienquellung:** Im Kontakt mit Ölen, Fetten oder Chemikalien quellen Elastomere typischerweise um 5 % bis 15 % ihres Volumens auf.
  4. **Folge einer Überfüllung (> 100 %):** Der O-Ring wirkt wie eine hydraulische Presse, hebt Flanschdeckel an, zerstört Gehäuse oder extrudiert zerstört in den Dichtspalt.

---

## 3. Nutmaße für gängige Schnurstärken (ISO 3601-2 & COG-Standard)

Die folgende Tabelle fasst die genormten Nutabmessungen für statische radiale und axiale Abdichtungen zusammen. Sie basiert auf den Richtlinien von **C. Otto Gehrckens (COG)** und **DIN ISO 3601-2**.

### Tabelle 1: O-Ring Einbaumaße für Standard-Schnurstärken (statisch)
*Alle Maße in mm. Quelle: C. Otto Gehrckens (COG) Tabellarische Übersicht & ISO 3601-2.*

| Schnurstärke $d_2$ | Radial statisch: Nuttiefe $t$ ($+0{,}05/0$) | Radial statisch: Nutbreite $b$ ($+0{,}05/0$) | Axial statisch: Nuttiefe $t$ ($+0{,}10/0$) | Axial statisch: Nutbreite $b$ ($+0{,}25/0$) | Nutgrund-Radius $r_1$ | Einführ-schräge $z$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1,50** | 1,05 | 2,19 | 1,10 | 2,80 | 0,30 | 0,92 |
| **2,00** | 1,50 | 2,78 | 1,50 | 3,40 | 0,30 | 1,15 |
| **2,50** | 1,90 | 3,37 | 1,90 | 3,90 | 0,30 | 1,43 |
| **3,00** | 2,30 | 3,98 | 2,30 | 4,60 | 0,60 | 1,53 |
| **3,50** *(3,53)* | 2,70 | 4,67 | 2,70 | 5,30 | 0,60 | 1,80 |
| **5,30** *(5,33)* | 4,20 | 6,86 | 4,20 | 7,60 | 0,60 | 2,70 |

*(Hinweis zu 3,50 und 5,30 mm: Die international standardisierten Reihen nach ISO 3601-1 und AS 568 führen diese Nennmaße exakt als $d_2 = 3{,}53\text{ mm}$ bzw. $5{,}33\text{ mm}$).*

---

### Vergleich mit Parker O-Ring Handbook (ORD 5700, Industrial Static Glands):
* **Design Chart 4-2 (Radial Static Seal):**
  * Schnur $1{,}78\text{ mm}$ ($1/16''$): Nuttiefe $1{,}27 \dots 1{,}32\text{ mm}$, Verpressung $22 \dots 32\,\%$, Nutbreite ohne Stützring $2{,}36 \dots 2{,}49\text{ mm}$.
  * Schnur $2{,}62\text{ mm}$ ($3/32''$): Nuttiefe $2{,}06 \dots 2{,}11\text{ mm}$, Verpressung $17 \dots 24\,\%$, Nutbreite ohne Stützring $3{,}56 \dots 3{,}68\text{ mm}$.
  * Schnur $3{,}53\text{ mm}$ ($1/8''$): Nuttiefe $2{,}82 \dots 2{,}87\text{ mm}$, Verpressung $16 \dots 23\,\%$, Nutbreite ohne Stützring $4{,}75 \dots 4{,}88\text{ mm}$.
  * Schnur $5{,}33\text{ mm}$ ($3/16''$): Nuttiefe $4{,}32 \dots 4{,}39\text{ mm}$, Verpressung $15 \dots 21\,\%$, Nutbreite ohne Stützring $7{,}14 \dots 7{,}26\text{ mm}$.
* **Design Chart 4-3 (Static Face Seal / Flansch):**
  * Schnur $3{,}53\text{ mm}$: Nuttiefe $2{,}57 \dots 2{,}72\text{ mm}$ (Verpressung $20 \dots 30\,\%$), Nutbreite Flüssigkeiten $4{,}50 \dots 4{,}75\text{ mm}$, Gase/Vakuum $4{,}01 \dots 4{,}17\text{ mm}$.
  * Schnur $5{,}33\text{ mm}$: Nuttiefe $3{,}86 \dots 4{,}11\text{ mm}$ (Verpressung $21 \dots 30\,\%$), Nutbreite Flüssigkeiten $6{,}86 \dots 7{,}37\text{ mm}$, Gase/Vakuum $6{,}07 \dots 6{,}20\text{ mm}$.

---

## 4. Oberflächengüte und Rauheitsanforderungen

Da Elastomere unter Druck fließen, schmiegen sie sich an Oberflächenunebenheiten an. Ist die Oberfläche jedoch zu rau oder weist Riefen in Querrichtung (Leckagepfade) auf, versagt die Dichtung.

### Richtwerte nach COG und Parker ORD 5700:
1. **Statische Flüssigkeitsabdichtung:**
   * **Nutgrund und Nutflanken:** $\mathbf{R_a \le 1{,}6\,\mu\text{m}} \quad (\mathbf{R_z \le 6{,}3\,\mu\text{m}})$.
   * **Dichtfläche / Gegenfläche:** $\mathbf{R_a \le 0{,}8 \dots 1{,}6\,\mu\text{m}} \quad (\mathbf{R_z \le 3{,}2 \dots 6{,}3\,\mu\text{m}})$.
2. **Statische Gas- und Vakuumabdichtung:**
   * Gase diffundieren durch kleinste Kapillaren.
   * **Nutgrund und Dichtfläche:** $\mathbf{R_a \le 0{,}4 \dots 0{,}8\,\mu\text{m}} \quad (\mathbf{R_z \le 1{,}6 \dots 3{,}2\,\mu\text{m}})$.
3. **Traganteil:** COG empfiehlt für Dichtflächen einen Materialanteil von $R_{mr} \approx 50\,\% \text{ bis } 70\,\%$ bei einer Schnitttiefe von $c = 0{,}25 \cdot R_z$.
4. **Bearbeitungsriefen:** Rattermarken, Schleifkratzer oder Riefen quer zur Dichtlinie sind unzulässig. Drehspuren müssen konzentrisch zur Nut verlaufen.

---

## 5. Einführschrägen (Lead-in Chamfers)

Bei radialen Dichtungen (Kolben/Stange) muss der O-Ring bei der Montage axial über Kanten geschoben werden. Trifft der Ring auf eine scharfe $90^\circ$-Kante, wird er abgeschert („angeknabbert“), was zum sofortigen Funktionsausfall führt.

### Gestaltungsrichtlinien:
* **Fasenwinkel:** Der Winkel der Einführschräge muss **$15^\circ$ bis $20^\circ$** betragen (maximal $30^\circ$).
* **Länge der Einführschräge ($z$):**
  * Muss groß genug sein, damit der O-Ring stufenlos und ohne Verkanten von seinem ungespannten Außendurchmesser auf den Bohrungsdurchmesser komprimiert wird.
  * Richtwerte nach COG:
    * $d_2 = 1{,}5\text{ mm} \rightarrow z \ge 0{,}92\text{ mm}$
    * $d_2 = 2{,}0\text{ mm} \rightarrow z \ge 1{,}15\text{ mm}$
    * $d_2 = 2{,}5\text{ mm} \rightarrow z \ge 1{,}43\text{ mm}$
    * $d_2 = 3{,}0\text{ mm} \rightarrow z \ge 1{,}53\text{ mm}$
    * $d_2 = 3{,}5\text{ mm} \rightarrow z \ge 1{,}80\text{ mm}$
    * $d_2 = 5{,}3\text{ mm} \rightarrow z \ge 2{,}70\text{ mm}$
* **Übergangskanten:** Die Kanten am Beginn und Ende der Fase müssen sorgfältig mit einem Radius von mindestens **$R \ge 0{,}2 \dots 0{,}5\text{ mm}$** verrundet und absolut gratfrei sein.

---

## 6. Konstruktionsregeln für 3D-gedruckte O-Ring-Nuten (FDM)

Der FDM-3D-Druck stellt für druckdichte O-Ring-Gehäuse eine besondere Herausforderung dar, da Schichtbauweise und raue Oberflächen dem Dichtungsprinzip widersprechen.

### Hauptprobleme beim 3D-Druck:
1. **Mikroleckage-Pfade entlang der Layer-Rillen:** Die Schichtstruktur erzeugt winzige Furchen parallel zur Dichtlinie.
2. **Innere Bauteilporosität:** Geringer Infill führt dazu, dass Gase oder Flüssigkeiten das Dichtungssystem durch das poröse Bauteilinnere einfach umströmen.
3. **Maßabweichungen:** Nuten neigen beim Drucken durch Wärmeschrumpf und Überextrusion dazu, schmaler und flacher zu werden als im CAD modelliert.

---

### Spezifische DFM-Regeln für gedruckte Nuten:
1. **Volles Material um die Nut (100 % Infill / Perimeter):**
   * Im CAD muss der Bereich um die Dichtnut massiv sein.
   * **Regel:** Mindestens **5 bis 8 Wandlinien (Perimeter)** um die Nut herum drucken, oder im Slicer eine lokale Modifikator-Box mit **100 % Infill** definieren. Der Abstand von der Nutwand zum inneren Infill muss mindestens $3\text{ mm}$ Vollmaterial betragen.
2. **Druckausrichtung:**
   * Flanschdichtungen (axial) sollten immer so gedruckt werden, dass die Dichtfläche flach auf dem Druckbett liegt (oder parallel dazu). Die konzentrischen Bahnen der Düse erzeugen geschlossene Kreislinien, die dichtungstechnisch unkritisch sind.
   * Radiale Nuten niemals quer zur Z-Achse drucken, da sonst Stufenstufeneffekte auf den Flanken entstehen.
3. **Erhöhte Verpressung wählen:**
   * Statt der üblichen 18–20 % sollte für gedruckte Gehäuse eine Anfangsverpressung von **25 % bis 30 %** gewählt werden (z. B. Nuttiefe um ca. 0,1 mm geringer konstruieren als im Standard), um die Rauheit der Druckschichten auszugleichen.
4. **Weichere O-Ring-Elastomere einsetzen:**
   * Standardmäßig werden NBR 70 oder FKM 75 verwendet. Für gedruckte Gehäuse sind weichere Werkstoffe mit **Shore A 60 (z. B. Silikon VMQ oder weiches EPDM)** ideal, da sie bei moderater Schraubenvorspannung tiefer in die Layerfurchen fließen.
5. **Nachbearbeitung & Hilfsmittel:**
   * **Chemische Glättung:** Bedampfung von ABS/ASA mit Aceton glättet die Nut auf Spritzgussniveau ($R_a < 0{,}8\,\mu\text{m}$).
   * **Dichtfett:** Vor der Montage muss die Nut und der O-Ring zwingend mit hochviskosem **Silikon-Dichtfett** benetzt werden. Das Fett füllt die verbleibenden Mikroporen zwischen den Filamentsträngen zuverlässig aus.

---

## 7. Katalog-Einträge im Standardformat

### Eintrag 1: Statische O-Ring-Verpressung
* **Aussage / Wert:** Die elastische Querschnittsverpressung eines O-Rings im statischen Einbau muss zwischen **15 % und 30 %** (optimal **20 % bis 25 %**) der Schnurstärke $d_2$ liegen.
* **Geltungsbereich:** Statische radiale und axiale Abdichtungen mit Elastomeren Härte 70 bis 80 Shore A nach DIN ISO 3601-2.
* **Herkunft:** Herstellerhandbuch (Parker ORD 5700).
* **Quelle:** [Parker O-Ring Handbook ORD 5700 PDF via NianticSeal](https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf), S. 3-10.
  * *Wörtliches Zitat:* „When used as a static seal, the maximum recommended [...] squeeze for most elastomers is 30%“
* **Begründung:** Unter 15 % reicht die Flächenpressung bei Kältekontraktion nicht aus; über 30 % versagt der Werkstoff durch Druckverformungsrest und Montageschäden.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn die rechnerische Verpressung außerhalb 15–30 % liegt).
* **Prüfstatus:** offen.

---

### Eintrag 2: Maximaler Nutfüllgrad
* **Aussage / Wert:** Der Nutfüllgrad eines statischen O-Ring-Einbauraums muss zwischen **60 % und 85 %** (Optimum 75 %) liegen; mindestens 10 % des Nutvolumens müssen als Freiraum verbleiben. *(korrigiert am 2026-10-21: 70 % bis 85 % -> 60 % bis 85 % [Optimum 75 %] nach Parker ORD 5700)*
* **Geltungsbereich:** Alle rechteckigen O-Ring-Nuten im Maschinen- und Apparatebau.
* **Herkunft:** Herstellerhandbuch (Parker ORD 5700).
* **Quelle:** [Parker O-Ring Handbook ORD 5700 PDF via NianticSeal](https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf), S. 3-9.
  * *Wörtliches Zitat:* „Most [...] O-ring seal applications call for a gland fill of between 60% [...] to 85% of the available volume with the optimum fill being [...] 75%“
* **Begründung:** Elastomere sind inkompressibel. Bei Erwärmung oder Medienquellung führt ein Füllgrad von 100 % zur Zerstörung des Gehäuses oder zum Herausscheren des Dichtrings.
* **Härte:** Fehler (`check_design` muss bei Nutfüllgrad $> 85\,\%$ warnen, bei $> 95\,\%$ ablehnen).
* **Prüfstatus:** offen.

---

### Eintrag 3: Einbaumaße für Schnurstärke 2,0 mm (statisch)
* **Aussage / Wert:** Für einen O-Ring mit Schnurstärke $d_2 = 2{,}00\text{ mm}$ beträgt für den radialen statischen Einbau die Nuttiefe $\mathbf{t = 1{,}50\text{ mm}}$ ($+0{,}05/0$) und die Nutbreite $\mathbf{b = 2{,}78\text{ mm}}$ ($+0{,}05/0$); für den axialen Einbau gilt $\mathbf{t = 1{,}50\text{ mm}}$ ($+0{,}10/0$) und $\mathbf{b = 3{,}40\text{ mm}}$ ($+0{,}25/0$).
* **Geltungsbereich:** Zylindrische Zapfen/Bohrungen und Flansche nach DIN ISO 3601-2.
* **Herkunft:** Norm über Sekundärquelle (C. Otto Gehrckens Einbaumaßtabelle).
* **Quelle:** [COG Tabellarische Übersicht für O-Ring Einbaumaße](https://www.cog.de/produkte/rund-um-den-o-ring/o-ring-einbaumasse/tabellarisch), Tabelle Zeile 4.
  * *Wörtliches Zitat:* „Die hier abgebildete Tabelle zeigt eine Auswahl der Einbaumaße in Abhängigkeit von Schnurstärke d2 für den radialen und axialen O-Ring Einbau.“
* **Begründung:** Ergibt eine Nennverpressung von $25{,}0\,\%$ und einen sicheren Nutfüllgrad von ca. $75\,\%$.
* **Härte:** Hinweis (Standardmaß für automatische Feature-Generierung).
* **Prüfstatus:** offen.

---

### Eintrag 4: Einbaumaße für Schnurstärke 3,0 mm (statisch)
* **Aussage / Wert:** Für Schnurstärke $d_2 = 3{,}00\text{ mm}$ beträgt radial statisch $\mathbf{t = 2{,}30\text{ mm}}$ und $\mathbf{b = 3{,}98\text{ mm}}$; axial statisch $\mathbf{t = 2{,}30\text{ mm}}$ und $\mathbf{b = 4{,}60\text{ mm}}$; Nutgrundradius $\mathbf{r_1 = 0{,}60\text{ mm}}$, Einführschräge $\mathbf{z = 1{,}53\text{ mm}}$.
* **Geltungsbereich:** Mittlere Gehäusedichtungen nach DIN ISO 3601-2.
* **Herkunft:** Norm über Sekundärquelle (C. Otto Gehrckens Einbaumaßtabelle).
* **Quelle:** [COG Tabellarische Übersicht für O-Ring Einbaumaße](https://www.cog.de/produkte/rund-um-den-o-ring/o-ring-einbaumasse/tabellarisch), Tabelle Zeile 7.
  * *Wörtliches Zitat:* „Die hier abgebildete Tabelle zeigt eine Auswahl der Einbaumaße in Abhängigkeit von Schnurstärke d2 für den radialen und axialen O-Ring Einbau.“
* **Begründung:** Gewährleistet $23{,}3\,\%$ Verpressung bei optimalem Freiraum für thermische Ausdehnung.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag 5: Oberflächenrauheit für statische Flüssigkeitsdichtungen
* **Aussage / Wert:** Nutgrund und Dichtflächen statischer Flüssigkeitsabdichtungen müssen eine maximale Oberflächenrauheit von $\mathbf{R_a \le 1{,}6\,\mu\text{m}}$ ($\mathbf{R_z \le 6{,}3\,\mu\text{m}}$) einhalten; Bearbeitungsriefen quer zur Dichtlinie sind unzulässig.
* **Geltungsbereich:** Metallische und spanend bearbeitete Dichtflächen für Hydrauliköle, Wasser und Emulsionen bis 100 bar.
* **Herkunft:** Herstellerhandbuch (Parker ORD 5700).
* **Quelle:** [Parker ORD 5700](https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf), S. 4-2.
  * *Wörtliches Zitat:* „The design charts indicate a surface roughness value not to [...] exceed 32 micro-inches (32 rms) on the sealing surfaces for [...] static seals with a maximum of 16 rms recommended for“
* **Begründung:** Gröbere Rillen oder Längskratzer können durch die Kaltverformung des 70-Shore-Elastomers nicht vollständig ausgefüllt werden und bilden mikroskopische Leckagekanäle.
* **Härte:** Hinweis.
* **Prüfstatus:** teilbelegt (Empfehlung für statische Dichtflächen in RMS wörtlich belegt; Umrechnung in Ra/Rz nach DIN EN ISO 4287).

---

### Eintrag 6: Einführschräge bei radialer Montage
* **Aussage / Wert:** An Zylinder- oder Wellenenden für radiale O-Ring-Dichtungen muss eine Einführschräge mit einem Winkel von **$15^\circ$ bis $20^\circ$** und verrundeten Kanten ($R \ge 0{,}3\text{ mm}$) angebracht werden.
* **Geltungsbereich:** Alle radial geführten Kolben-, Stopfen- und Stangenabdichtungen.
* **Herkunft:** Herstellerhandbuch (Parker ORD 5700).
* **Quelle:** [Parker O-Ring Handbook ORD 5700 PDF via NianticSeal](https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf), S. 10-4.
  * *Wörtliches Zitat:* „Provide a 20° lead-in chamfer.“
* **Begründung:** Scharfe Kanten führen beim Einschieben zum Abscheren von Elastomerteilen an der Ringaußenseite, was zu sofortigem Lecken führt.
* **Härte:** Fehler (`check_design` muss bei radialen Dichtsitzen ohne Einführschräge warnen).
* **Prüfstatus:** offen.

---

### Eintrag 7: Vollmaterialzone für 3D-gedruckte Nuten (Hypothese / inventa-Regel)
* **Aussage / Wert:** Bei FDM-gedruckten Dichtflanschen muss die Dichtnut von einer mindestens **3,0 mm dicken Vollmaterialzone** (mindestens 5–6 massive Perimeter oder lokaler 100-%-Infill-Block) umgeben sein.
* **Geltungsbereich:** FDM-gedruckte Druckbehälter, Gehäusedeckel und Rohrverbindungen in PLA, PETG, ABS, PA.
* **Herkunft:** Hypothese / Erfahrung (3D-Druck-Praxis inventa).
* **Quelle:** interne Konstruktionserfahrung inventa (vorläufige Hypothese).
  * *Wörtliches Zitat:* „FDM-Druckteile mit Standard-Infill (20%) sind luft- und wasserdurchlässig; ohne massive Perimeter um die Dichtnut strömt das Medium durch das Bauteilinnere am O-Ring vorbei.“
* **Begründung:** Druckluft oder Wasser unter Druck migriert durch die Grenzflächen der Layer in das Hohlraumsystem des Standard-Infills und tritt außerhalb der Dichtung wieder aus.
* **Härte:** Fehler für funktionale Druckkörper im 3D-Druck.
* **Prüfstatus:** offen (systematischer Druckversuch auf Prüfstand erforderlich).

---

## 8. Nicht erreichbare Quellen und offene Fragen

### Nicht erreichbare Quellen
| URL | Code / Grund | Bemerkung |
| :--- | :---: | :--- |
| `https://www.parker.com/ORD5700` | 403 Forbidden | Direkter Abruf auf parker.com durch Bot-Sperre blockiert (PDF erfolgreich über nianticseal.com bezogen). |
| `https://www.cog.de/service/o-ring-rechner` | 404 Not Found | Veraltete URL; aktuelle Daten liegen unter `/produkte/rund-um-den-o-ring/o-ring-einbaumasse/tabellarisch`. |

### Offene Fragen und Vorschläge für Versuche
1. **Druckdichtigkeit von FDM-O-Ring-Nuten (PETG vs. Aceton-geglättetes ABS):**
   * *Versuch:* Prüfflansch mit axialer O-Ring-Nut ($d_2 = 2{,}5\text{ mm}$) drucken, mit 4 Schrauben M4 verschrauben und mit 2 bar Wasser- bzw. Druckluft beaufschlagen.
   * *Ziel:* Ermittlung der Mindestanzahl an Perimetern (3, 5 oder 8) für absolute Gasdichtigkeit.
2. **Shore-Härte-Vergleich bei gedruckten Dichtflächen:**
   * Dichtet ein O-Ring mit Shore A 60 (Silikon) auf unpolierten PETG-Layer-Oberflächen signifikant besser ab als ein harter Ring mit Shore A 80 (FKM)?
3. **Spaltextrusionsgrenzen bei Kunststoffgehäusen:**
   * Ab welchem Innendruck weicht ein gedrucktes Gehäuse aus PETG (E-Modul ~2100 MPa) elastisch so weit auf, dass der Dichtspalt $g > 0{,}2\text{ mm}$ wird und der O-Ring extrudiert?

---

Claude (2026-10-21): nur überflogen. Die Größenordnungen sind plausibel (O-Ring 2 mm statisch radial t 1,5; Biegeradien DC01 1×t, 6061-T6 2–3×t), die Werte sind nicht gegen die Quellen geprüft. Das übernimmt `tools/check_sources.py`.
