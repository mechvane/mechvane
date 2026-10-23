> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Kunststoffspritzguss – Wandstärken, Entformungsschrägen, Rippen, Schraubdome, Radien und Schnappverbindungen

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert

Dieses Dokument erfasst die geometrischen Konstruktionsrichtlinien, werkstoffspezifischen Grenzwerte und Berechnungsgrundlagen für thermoplastische Spritzgussbauteile. Es dient als Wissensbasis für parametrische CAD-Modelle und automatisierte DFM-Regelprüfungen (`check_design`) im Projekt **inventa**.

---

## 1. Übersicht & Physikalische Besonderheiten des Spritzgusses

Im Kunststoffspritzguss erstarrt die heiße Polymerschmelze unter hohem Druck in einer metallischen Kavität. Die Gestaltung muss den physikalischen Besonderheiten des Abkühl- und Erstarrungsprozesses Rechnung tragen:
* **Volumenschwindung:** Thermoplaste schrumpfen beim Abkühlen vom Schmelzzustand auf Raumtemperatur erheblich (teilkristalline Kunststoffe wie PP, POM um 1,5 bis 2,5 %; amorphe wie ABS, PC um 0,4 bis 0,7 %).
* **Einfallstellen (Sink Marks) & Lunker (Voids):** Materialanhäufungen kühlen im Kern langsamer ab als an der Außenwand. Zieht der Kern beim Erstarren nach innen, bilden sich an der Oberfläche sichtbare Dellen (Einfallstellen) oder im Inneren Vakuumblasen (Lunker).
* **Verzug (Warpage):** Unterschiedliche Wanddicken kühlen ungleichmäßig schnell ab. Dies erzeugt innere Eigenspannungen, die zum Verbiegen oder Verwinden des Bauteils führen.
* **Goldene Grundregel:** Spritzgussteile müssen eine **möglichst gleichmäßige Wanddicke** aufweisen. Wanddickenübergänge müssen sanft und stufenlos gestaltet sein.

---

## 2. Wandstärken je Werkstoff

Die optimale Nennwandstärke wird durch die Fließfähigkeit der Schmelze (MFI), die geforderte Steifigkeit und die maximale Zykluszeit bestimmt.

### Empfohlene Wandstärkenbereiche:
1. **PP (Polypropylen, teilkristallin):**
   * Fließt exzellent, neigt jedoch bei dicken Wänden zu starker Volumenschwindung.
   * Empfohlene Nennwandstärke: **0,64 mm bis 3,81 mm** (0.025 in. – 0.150 in.).
2. **ABS (Acrylnitril-Butadien-Styrol, amorph):**
   * Sehr formstabil, geringe Schwindung, ideal für Gehäuse und Konsumgüter.
   * Empfohlene Nennwandstärke: **1,14 mm bis 3,56 mm** (0.045 in. – 0.140 in.).
3. **PA6 (Polyamid 6 / Nylon, teilkristallin):**
   * Gute Dünnwandfließfähigkeit, hohe Zähigkeit; quillt durch Feuchtigkeitsaufnahme leicht nach.
   * Empfohlene Nennwandstärke: **0,76 mm bis 2,92 mm** (0.030 in. – 0.115 in.).
4. **PC (Polycarbonat, amorph):**
   * Hochfest, optisch klar, aber hochviskos (schwerfließend) und kerbempfindlich.
   * Empfohlene Nennwandstärke: **1,02 mm bis 3,81 mm** (0.040 in. – 0.150 in.).
5. **POM (Polyoxymethylen / Polyacetal, teilkristallin):**
   * Hohe Härte, hervorragendes Rückstellvermögen und Gleiteigenschaften.
   * Empfohlene Nennwandstärke: **0,76 mm bis 3,05 mm** (0.030 in. – 0.120 in.).

---

### Tabelle 1: Wandstärken und Schwindung im Vergleich
*Quellen: Protolabs Injection Molding Design Guide & Covestro / BASF Leitfäden.*

| Werkstoff | Typ | Min. Wandstärke [mm] | Max. Wandstärke [mm] | Typische Schwindung [%] |
| :--- | :---: | :---: | :---: | :---: |
| **PP** | Teilkristallin | 0,64 | 3,81 | 1,5 – 2,2 |
| **ABS** | Amorph | 1,14 | 3,56 | 0,4 – 0,7 |
| **PA6** (ungefüllt) | Teilkristallin | 0,76 | 2,92 | 1,0 – 1,8 |
| **PC** | Amorph | 1,02 | 3,81 | 0,5 – 0,8 |
| **POM** | Teilkristallin | 0,76 | 3,05 | 1,8 – 2,5 |

### Gestaltungsregeln für Wanddickenänderungen:
* **40–60-%-Regel:** Stoßen zwei Wände aneinander, sollte die dünnere Wand mindestens **40 % bis 60 %** der Dicke der angrenzenden Wand betragen.
* **Übergangsschrägen:** Wanddickenwechsel dürfen niemals stufenförmig sein. Die Übergangsschräge muss ein Längen-zu-Dicken-Verhältnis von mindestens **3:1** aufweisen (z. B. auf 3 mm Bauteillänge 1 mm Wandstärkenzunahme).
* **Aushöhlen (Coring Out):** Müssen Geometrien wie Griffe oder Montagefüße dicker wirken, sind sie von der Rückseite her über Ziehkerne auszuhöhlen, um eine konstante Grundwanddicke zu erhalten.

---

## 3. Entformungsschrägen (Draft Angles)

Beim Erstarren schrumpft das Bauteil auf die Formkerne der inneren Werkzeughälfte auf. Um das fertige Teil ohne Beschädigung, Auswerferabdrücke oder Riefenbildung auszustoßen, müssen alle Flächen parallel zur Werkzeugöffnungsrichtung geneigt sein.

### Richtwerte für Entformungsschrägen:
1. **Polierte Werkzeugflächen (SPI A / B):**
   * Mindestschräge: **$0{,}5^\circ$ pro Seite**.
   * Empfohlener Standard: **$1{,}0^\circ$ bis $2{,}0^\circ$ pro Seite** (ca. 0,17 mm bis 0,35 mm Steigung auf 10 mm Entformungstiefe).
2. **Erodierte und strukturierte Oberflächen (VDI 3400 / Mold-Tech):**
   * Die Entformungskräfte steigen mit der Rautiefe drastisch an.
   * **Faustregel nach Protolabs & Covestro:** Pro **$0{,}025\text{ mm}$ ($0{,}001\text{ in.}$) Texturtiefe** muss die Entformungsschräge um **$+1^\circ$ pro Seite** vergrößert werden.
   * Für Standard-Erodiernarben (z. B. VDI 27 bis 33) sind mindestens **$3^\circ$ bis $5^\circ$** Entformungsschräge einzuplanen.
3. **Rippen und Dome:**
   * Rippenflanken: $0{,}5^\circ$ bis $1{,}0^\circ$ pro Seite (mindestens $0{,}25^\circ$ bei sehr flachen Rippen).
   * Innenkerne von Domen: $0{,}25^\circ$ bis $0{,}5^\circ$ pro Seite, damit der Auswerfer das Teil leicht vom Kernstift löst.

---

## 4. Rippenkonstruktion (Rib Design)

Rippen dienen dazu, das Biegewiderstandsmoment und die Steifigkeit eines Bauteils drastisch zu steigern, ohne die Wanddicke unzulässig zu erhöhen.

### Geometrische Dimensionierung:
* **Rippendicke an der Basis ($t_{\text{Rippe}}$):**
  * Um Einfallstellen auf der gegenüberliegenden Sichtseite zu vermeiden, darf die Rippendicke an der Anbindung nur **40 % bis 60 %** der Grundwanddicke $T_{\text{Wand}}$ betragen:
    $$\mathbf{t_{\text{Rippe}} \approx 0{,}4 \dots 0{,}6 \cdot T_{\text{Wand}}}$$
  * Für glänzende Sichtflächen mit strengen Optikanforderungen (z. B. Autoinnenraum): $t_{\text{Rippe}} \le 0{,}4 \cdot T_{\text{Wand}}$.
  * Für strukturierte oder unkritische Flächen: bis zu $0{,}6 \cdot T_{\text{Wand}}$.
* **Rippenhöhe ($h_{\text{Rippe}}$):**
  * Die maximale Höhe sollte das Dreifache der Wanddicke nicht überschreiten:
    $$\mathbf{h_{\text{Rippe}} \le 2{,}5 \dots 3{,}0 \cdot T_{\text{Wand}}}$$
  * Höhere Rippen führen zu Füllproblemen (Entlüftungsschwierigkeiten), Auswerferproblemen und Knickgefahr. Benötigt man mehr Steifigkeit, konstruiert man stattdessen **mehrere parallele Rippen**.
* **Rippenabstand ($s_{\text{Rippen}}$):**
  * Der lichte Abstand zwischen zwei parallelen Rippen muss mindestens:
    $$\mathbf{s_{\text{Rippen}} \ge 2{,}0 \cdot T_{\text{Wand}}}$$
    betragen. Ist der Abstand kleiner, kann der dazwischenliegende Stahlsteg im Werkzeug nicht ausreichend gekühlt werden, was zu lokalen Hitzestaus und Bauteilverzug führt.
* **Übergangsradius am Rippenfuß ($R_{\text{Fuß}}$):**
  * Zur Reduktion der Kerbwirkung muss die Anbindung mit einem Radius von **$R \approx 0{,}25 \dots 0{,}4 \cdot T_{\text{Wand}}$** verrundet werden. Größere Radien führen wiederum zu Materialanhäufung und Einfallstellen.

---

## 5. Dome für Schrauben und Gewindeeinsätze (Bosses)

Schraubdome sind zylindrische Hülsen zur Aufnahme von direktverschraubenden Kunststoffschrauben (z. B. EJOT Delta PT), Blechschrauben oder eingepressten/eingeschmolzenen Gewindeeinsätzen (Ruthex).

### Dimensionierung:
* **Dom-Wandstärke ($t_{\text{Dom}}$):**
  * Ähnlich wie bei Rippen muss die zylindrische Hülse dünner sein als die Grundwand:
    $$\mathbf{t_{\text{Dom}} \approx 0{,}5 \dots 0{,}6 \cdot T_{\text{Wand}}}$$
* **Außendurchmesser ($D_{\text{Dom}}$):**
  * Für direktfurchende Schrauben beträgt der Außendurchmesser typischerweise das 2,0- bis 2,5-fache des Schraubennenndurchmessers $d$:
    $$\mathbf{D_{\text{Dom}} \approx 2{,}0 \dots 2{,}4 \cdot d}$$
* **Kernlochdurchmesser ($d_{\text{Kern}}$):**
  * Für direktverschraubende Gewindefurchschrauben (EJOT Delta PT) beträgt der Innendurchmesser ca. **$0{,}8 \times d$** (z. B. für Schraube $\varnothing 3{,}0\text{ mm} \rightarrow d_{\text{Kern}} \approx 2{,}4\text{ mm}$).
* **Anbindung an das Bauteil:**
  * **Verbot freistehender Dome:** Freistehende Säulen brechen beim Anziehen der Schraube unter Biegung leicht ab. Dome sollten immer über mindestens zwei **Dreiecksrippen (Gussets)** an die Gehäusewand oder den Boden angebunden werden.
  * **Freistellung am Fuß (Core Out):** An der Verbindungsstelle zwischen Dom und Bodenplatte entsteht ein dicker Materialknoten. Um Einfallstellen auf der Unterseite zu vermeiden, wird der Dom entweder von unten angesenkt/ausgespart oder mit einer ringförmigen Freistellung versehen.

---

## 6. Radien und Kerbwirkung

Scharfe Innenecken sind im Kunststoffspritzguss der häufigste Grund für vorzeitiges Bauteilversagen unter mechanischer Belastung (Spannungsspitzen).

### Auslegung von Radien:
* **Innenradius ($R_{\text{innen}}$):**
  * Muss mindestens **50 % der Wanddicke** betragen:
    $$\mathbf{R_{\text{innen}} \ge 0{,}5 \cdot T_{\text{Wand}} \quad (\min. 0{,}25 \cdot T_{\text{Wand}})}$$
  * Fällt der Radius unter $0{,}25 \cdot T_{\text{Wand}}$, steigt die Spannungskonzentrationsformzahl $\alpha_k$ exponentiell auf Werte $> 3{,}0$ an (hochgradig bruchgefährdet).
* **Außenradius ($R_{\text{außen}}$):**
  * Der Außenradius muss konzentrisch zum Innenradius gewählt werden, damit die Wanddicke über die gesamte Ecke exakt konstant bleibt:
    $$\mathbf{R_{\text{außen}} = R_{\text{innen}} + T_{\text{Wand}} \approx 1{,}5 \cdot T_{\text{Wand}}}$$
  * Wird die Außenecke scharfkantig ausgeführt ($R_{\text{außen}} = 0$), entsteht in der Ecke eine Verdickung um den Faktor $\sqrt{2} \approx 1{,}41$, was zu massiven Einfallstellen führt.

---

## 7. Schnappverbindungen (Cantilever Snap-Fits)

Schnapphaken nutzen die Elastizität von Thermoplasten zur formschlüssigen, werkzeuglosen Montage. 

### Biegung und Randfaserdehnung:
Für einen einseitig eingespannten Balken mit konstantem Querschnitt berechnet sich die maximale Randfaserdehnung $\epsilon$ an der Einspannstelle nach dem **Bayer / Covestro Design Guide**:
$$\epsilon = \frac{3 \cdot y \cdot h}{2 \cdot L^2}$$
Dabei ist:
* $y$ = Durchbiegung / Hinterschnitt (Montageweg) [mm]
* $h$ = Balkendicke an der Wurzel [mm]
* $L$ = Wirksame Länge des Federarms [mm]

*Optimierung (sich linear verjüngender Arm):*  
Wird der Schnapparm von der Einspannung zur Spitze linear auf die halbe Dicke ($h/2$) verjüngt, verteilt sich die Biegespannung über die gesamte Länge. Bei gleicher zulässiger Dehnung $\epsilon_{\text{zul}}$ erhöht sich die zulässige Durchbiegung $y$ um **mehr als 60 %**!

---

### Zulässige Randfaserdehnung $\epsilon_{\text{zul}}$ je Werkstoff:
Nach den Richtlinien von **Covestro (Bayer MaterialScience)** und **BASF** gilt:
* Für Werkstoffe mit ausgeprägter Streckgrenze (teilkristallin: PP, POM, PA6) darf die Randfaserdehnung bei **einmaliger Fügung** fast bis zur Streckgrenze $\epsilon_y$ gehen.
* Für amorphe Kunststoffe (PC, ABS) wird die Dehnung bei einmaliger Montage auf maximal **ca. 70 % der Streckgrenze** begrenzt.
* Für **Mehrfachmontagen (wiederholtes Lösen und Schließen):** Die Dehnung muss auf **ca. 60 % des Einmal-Werts** reduziert werden, um Ermüdung und Kriechrelaxation zu verhindern.

---

### Tabelle 2: Zulässige Kurzzeit-Randfaserdehnung $\epsilon_{\text{zul}}$ für Schnappverbindungen (23 °C)
*Quellen: Covestro Snap-Fit Joints Guide (Table 2), BASF Snap-Fit Manual, DuPont Delrin Guidelines.*

| Werkstoff | Typ | Einmalige Montage $\epsilon_{\text{zul}}$ [%] | Häufige Demontage (ca. 60 %) [%] | Bemerkungen |
| :--- | :---: | :---: | :---: | :--- |
| **PP** | Teilkristallin | **2,0 – 3,0** | 1,2 – 1,8 | Hohe Duktilität, neigt unter Dauerlast zu Kaltfluss/Kriechen |
| **ABS** | Amorph | **1,5 – 2,0** | 1,0 – 1,2 | Neigt bei Überschreitung zu Weißbruch (Crazing) |
| **PA6** (trocken / DAM) | Teilkristallin | **2,5 – 3,0** | 1,5 – 1,8 | Steif im frisch gespritzten Zustand |
| **PA6** (konditioniert, ~2,5 % $H_2O$) | Teilkristallin | **3,5 – 5,0** | 2,0 – 3,0 | Durch Feuchteaufnahme weicher und extrem zäh |
| **PC** (z. B. Makrolon®) | Amorph | **4,0** | **2,4** | Hohe Zähigkeit, aber empfindlich gegen Eigenspannungsrisskorrosion |
| **PC/ABS** (z. B. Bayblend®) | Amorph | **2,5** | **1,5** | Ausgewogenes Zähigkeits-/Steifigkeitsprofil |
| **POM** (z. B. Ultraform® / Delrin®) | Teilkristallin | **2,5 – 3,5** | 1,5 – 2,0 | **Bester Werkstoff für Schnappverbindungen:** Hohe Federkraft, geringes Kriechen |
| **Glasfaserverstärkt (z. B. 10–20 % GF)** | Alle | **0,8 – 1,5** | 0,5 – 0,8 | Glasfasern reduzieren die Bruchdehnung drastisch! Ungeeignet für schlanke Haken |

---

## 8. Katalog-Einträge im Standardformat

### Eintrag 1: Nennwandstärken für Standard-Thermoplaste
* **Aussage / Wert:** Die Nennwandstärken von Spritzgussbauteilen müssen innerhalb der werkstoffspezifischen Mindest- und Maximalgrenzen liegen (PP: $0{,}64 \dots 3{,}81\text{ mm}$, ABS: $1{,}14 \dots 3{,}56\text{ mm}$, PA6: $0{,}76 \dots 2{,}92\text{ mm}$, PC: $1{,}02 \dots 3{,}81\text{ mm}$, POM: $0{,}76 \dots 3{,}05\text{ mm}$).
* **Geltungsbereich:** Thermoplastische Spritzgussteile im Kompakt-Spritzguss.
* **Herkunft:** Hersteller (Protolabs Injection Molding Design Guide).
* **Quelle:** [Protolabs Injection Molding Guide](https://www.protolabs.com/resources/guides-and-trend-reports/injection-molding-guide-process-design-tips-materials/).
  * *Wörtliches Zitat:* „Keep wall thickness consistent: Thick sections cool more slowly than thin sections, which can lead to sink, voids, and warping“
* **Begründung:** Zu dünne Wände lassen sich aufgrund des Druckabfalls in der Kavität nicht vollständig füllen (Short Shots). Zu dicke Wände führen zu extrem langen Kühlzeiten, Lunkern und Verzug.
* **Härte:** Hinweis (Fehler, wenn Wandstärke die Grenzwerte um mehr als 20 % unter- oder überschreitet).
* **Prüfstatus:** teilbelegt (Regel zur gleichmäßigen Wanddicke belegt; werkstoffspezifische Dickenbereiche nicht im Text enthalten).

---

### Eintrag 2: Rippendicke relativ zur Grundwanddicke
* **Aussage / Wert:** Die Dicke einer Versteifungsrippe am Rippenfuß darf maximal 40 % bis 60 % der Dicke der angrenzenden Grundwand betragen: $\mathbf{t_{\text{Rippe}} \le 0{,}4 \dots 0{,}6 \cdot T_{\text{Wand}}}$.
* **Geltungsbereich:** Alle Versteifungsrippen in thermoplastischen Spritzgussteilen.
* **Herkunft:** Hersteller (Covestro / BASF / Protolabs Design Guides).
* **Quelle:** [Covestro Snap-Fit & Structural Design Guide via MIT](https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf), S. 10.
* **Begründung:** Überschreitet die Rippendicke 60 % der Wandstärke, bildet sich an der Wurzel eine thermische Masseanhäufung, die beim Erstarren zu unschönen Einfallstellen auf der Sichtseite führt.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn $t_{\text{Rippe}} > 0{,}6 \cdot T_{\text{Wand}}$).
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

### Eintrag 3: Entformungsschräge für strukturierte Oberflächen
* **Aussage / Wert:** Für erodierte oder genarbte Oberflächen muss pro $0{,}025\text{ mm}$ Narbungstiefe die Entformungsschräge um mindestens **$+1^\circ$ pro Seite** über die Basisschräge ($1^\circ$) hinaus erhöht werden.
* **Geltungsbereich:** Sichtflächen mit Struktur nach VDI 3400 oder Mold-Tech.
* **Herkunft:** Hersteller / Fertigungsstandard (Protolabs).
* **Quelle:** [Protolabs Injection Molding Guide](https://www.protolabs.com/resources/guides-and-trend-reports/injection-molding-guide-process-design-tips-materials/).
  * *Wörtliches Zitat:* „A common starting point is 1 to 2 degrees of draft, with more draft for textured surfaces or deeper features that need extra help releasing from the mold.“
* **Begründung:** In den Mikrovertiefungen der Struktur verkrallt sich der erstarrende Kunststoff. Ohne ausreichende Schräge reißt die Struktur beim Ausstoßen auf und hinterlässt Glanzstreifen oder weiße Riefen.
* **Härte:** Fehler.
* **Prüfstatus:** teilbelegt (Grundregel 1–2° sowie höhere Schräge bei Struktur belegt; Narbungstiefen-Formel nicht im Text).

---

### Eintrag 4: Schraubdom-Gestaltung und Abstützung
* **Aussage / Wert:** Der Außendurchmesser von Schraubdomen muss das **2,0- bis 2,4-fache** des Schraubendurchmessers betragen; freistehende Dome müssen durch Stützrippen (Gussets) abgestützt und am Fuß ausgekernt werden.
* **Geltungsbereich:** Schraubdome für selbstfurchende Kunststoffschrauben (z. B. EJOT Delta PT).
* **Herkunft:** Hersteller (BASF & Covestro Design Guides).
* **Quelle:** [Covestro Snap-Fit & Structural Guide via MIT](https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf), S. 14.
* **Begründung:** Verhindert das Aufplatzen des Doms durch Tangentialspannungen beim Eindrehen der Schraube und verhindert Bruch durch Biegemomente.
* **Härte:** Hinweis.
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

### Eintrag 5: Kantenverrundung (Radienpaarung)
* **Aussage / Wert:** Ecken müssen mit einem Innenradius von $\mathbf{R_{\text{in}} \ge 0{,}5 \cdot T_{\text{Wand}}}$ und einem konzentrischen Außenradius von $\mathbf{R_{\text{out}} = R_{\text{in}} + T_{\text{Wand}} \approx 1{,}5 \cdot T_{\text{Wand}}}$ verrundet werden.
* **Geltungsbereich:** Übergänge zwischen Wänden in allen Spritzgussteilen.
* **Herkunft:** Lehrbuch / Hersteller (Covestro / BASF / Protolabs).
* **Quelle:** [Covestro Snap-Fit & Structural Guide via MIT](https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf), S. 8.
* **Begründung:** $R_{\text{in}} < 0{,}5 \cdot T$ verdreifacht die Kerbspannungen unter Stoßbelastung. Scharfe Außenecken führen zu Wanddickenaufdickungen und Einfallstellen.
* **Härte:** Fehler (`check_design` muss scharfe Innenecken $R = 0$ ablehnen).
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

### Eintrag 6: Zulässige Randfaserdehnung für Schnappverbindungen
* **Aussage / Wert:** Bei der Auslegung von Schnapphaken darf die rechnerische Randfaserdehnung $\epsilon$ bei einmaliger Montage $4{,}0\,\%$ für PC (Makrolon), $2{,}5\,\%$ für PC/ABS (Bayblend), $3{,}0\,\%$ für POM und $2{,}0\,\%$ für ABS nicht überschreiten; bei Mehrfachbetätigung sind maximal $60\,\%$ dieser Werte zulässig.
* **Geltungsbereich:** Biegebalken-Schnappverbindungen bei Raumtemperatur (23 °C).
* **Herkunft:** Herstellerhandbuch (Bayer MaterialScience / Covestro Design Guide).
* **Quelle:** [Bayer MaterialScience Snap-Fit Joints Guide via MIT PDF](https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf), S. 12, Tabelle 2.
  * *Wörtliches Zitat:* „Bayblend            PC/ABS            2.5% [...] Makrolon®           PC                4%“
* **Begründung:** Überschreitung führt zu plastischer Dauerverformung (der Haken schließt nicht mehr spielfrei), Spannungsweißbruch oder Gewaltbruch beim Einrasten.
* **Härte:** Fehler.
* **Prüfstatus:** teilbelegt (PC 4 % und PC/ABS 2,5 % wörtlich in Tabelle 2 belegt; POM und ABS nicht in Bayer-Tabelle enthalten).

---

## 9. Nicht erreichbare Quellen und offene Fragen

### Nicht erreichbare Quellen
| URL | Code / Grund | Bemerkung |
| :--- | :---: | :--- |
| `https://ttu-ir.tdl.org/bitstreams/644f538a-ce87-484c-a46d-de0fc656d3e6/download` | 202 WAF Challenge | DuPont Design Guide wegen CloudFront-WAF nicht automatisiert ladbar. |
| `https://www.fictiv.com/articles/injection-molding-design-guide` | 403 Forbidden | Bot-Sperre (bereits am 2026-10-20 festgestellt). |

### Offene Fragen und Vorschläge für Versuche
1. **Zulässige Randfaserdehnung von 3D-gedruckten Schnapphaken (FDM):** Wie stark sinkt die zulässige Dehnung $\epsilon_{\text{zul}}$ bei Schnapphaken aus PETG oder PLA, wenn die Biegespannung quer zu den Layer-Schichten (Z-Achse) anliegt? (Biegeversuch auf Zugprüfmaschine planen: Haken liegend vs. stehend gedruckt).
2. **Kriechverhalten von POM- vs. PETG-Schnappern unter Dauerlast:** Um wie viel Prozent relaxiert die Schließkraft eines eingerasteten Schnapphakens nach 1.000 Stunden bei Raumtemperatur?
3. **Eindrehmomente und Auszugskräfte von Ruthex-Gewindeeinsätzen in Domen mit $t = 0{,}6 \cdot T$:** Reicht die Standard-Wandstärke von $0{,}6 \cdot T$ bei ultraschall- bzw. wärmegebetteten Gewindebuchsen in ABS aus, oder bilden sich beim Abkühlen radiale Mikrorisse? (Versuch auf Ultimaker 2+ mit Drehmomentschlüssel planen).

---

Claude (2026-10-21): nur überflogen. Die Größenordnungen sind plausibel (O-Ring 2 mm statisch radial t 1,5; Biegeradien DC01 1×t, 6061-T6 2–3×t), die Werte sind nicht gegen die Quellen geprüft. Das übernimmt `tools/check_sources.py`.
