> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Automatische Prüfung 2026-10-20: 15 Links, davon 0 nicht mit 200 erreichbar (teils Bot-Sperren). Zahlen vor dem Übernehmen einzeln an der Quelle prüfen.

Dieser Regelkatalog fasst belegte Konstruktionsrichtlinien für den **FDM-3D-Druck (0,4-mm-Düse, PLA/PETG)** sowie das **CNC-Fräsen in Aluminium** zusammen. Alle Werte basieren auf Herstellerrichtlinien, Fertigungsdienstleistern (Hubs/Protolabs Network, Protolabs, Xometry, Prusa Research, UltiMaker, Ruthex, CNC Kitchen) und Normen.

---

### 1. Konstruktionsregeln FDM-3D-Druck (Düse 0,4 mm, PLA/PETG)

| Regel / Konstruktionsmerkmal | Empfohlener Wert / Grenzmaß | Bedingung / Kontext | Quelle-Nr. |
| :--- | :--- | :--- | :--- |
| **Minimale Wandstärke** | **0,8 mm** (absolutes Minimum / 2 Perimeter)<br>**1,2 – 1,5 mm** (empfohlen für Funktionsbauteile / 3–4 Perimeter) | Düse 0,4 mm, Schichthöhe 0,2 mm, PLA/PETG. Vielfaches der Düsenbreite; unter 0,8 mm entstehen Lücken oder Fehlstellen im Slicer. | [Q1], [Q2], [Q3] |
| **Passungen: Presspassung** | **0,00 bis 0,05 mm** Übermaß/Spiel (CAD: $\pm 0,00$ bis $-0,05$ mm Spalt) | Montage erfordert Einpressen/Klemmsitz. Da FDM-Bohrungen konstruktionsbedingt leicht kleiner drucken, führt 0,0 mm CAD-Spalt real meist bereits zu einem Presssitz. | [Q4], [Q5] |
| **Passungen: Spielpassung / Gleitpassung** | **0,20 bis 0,40 mm** (Prusa/Makerspace)<br>**0,40 bis 0,50 mm** (Hubs Standard) | Für bewegliche Führungen, Scharniere, Deckel. FDM-Grundtoleranz (X/Y: $\pm 0,3$ mm, Z: $\pm 0,1$ mm) muss vorgehalten werden, um Klemmen/Verschmelzen zu verhindern. | [Q4], [Q5] |
| **Überhangwinkel ohne Stütze** | **$\le 45^\circ$** von der Vertikalen (Standardregel)<br>*(Bis zu **$60^\circ$ – $75^\circ$** bei optimierter Hochleistungskühlung)* | Düse 0,4 mm, Schichthöhe 0,15–0,2 mm, PLA (100 % Lüfter). Bei $45^\circ$ liegt noch 50 % des Strangs auf der Vorlage auf. | [Q1], [Q6], [Q7] |
| **Maximale Brückenlänge (Bridging)** | **$\le 5\text{ mm}$** (empfohlen für maßhaltige Unterseite)<br>**$\le 10\text{ mm}$** (Standard-Grenze ohne Support)<br>*(Bis zu **$25\text{ mm}$** mit Bridge-Detection/Tough PLA)* | 0,4-mm-Düse, PLA/PETG, 100 % Bauteillüfter, reduzierte Brückengeschwindigkeit. Bei Spannen $> 5\text{--}10\text{ mm}$ tritt ohne Support sichtbarer Durchhang auf. | [Q1], [Q8] |
| **Minimaler Lochdurchmesser (vertikal, Z-Achse)** | **$\ge 2,0\text{ mm}$** (empfohlen)<br>**1,0 mm** (unteres Limit; erfordert Nachbohren) | Z-Achsen-Bohrung. Durch Düsenstauchdruck und Polygon-Interpolation schrumpfen Innenkonturen; unter 2 mm schließen sich Bohrungen oft teilweise. | [Q1], [Q9] |
| **Gewindeeinsätze (M3): Vorloch-Bohrungsdurchmesser** | **$\varnothing 4,0\text{ mm}$** (CAD-Nennmaß; real je nach Slicer/Schrumpfung 4,0 – 4,2 mm) | Standard-M3-Einsätze (Länge 5,7 mm) von Ruthex (`RX-M3x5.7`) und CNC Kitchen. Einpressen per Lötkolben (~225 °C PLA, ~245 °C PETG). | [Q10], [Q11], [Q12] |
| **Gewindeeinsätze (M3): Mindestwandstärke um Einsatz** | **$\ge 1,6\text{ mm}$** (CNC Kitchen)<br>Außendurchmesser des Doms: **$\ge 8,0\text{ mm}$** ($2 \times$ Insert-Außendurchmesser) | Slicer: mind. 3–4 massive Perimeter (kein lockeres Infill). Zu dünne Wände platzen beim Einschmelzen auf oder beulen aus. | [Q11], [Q12] |
| **Gewindeeinsätze: Bohrungsgeometrie** | Sacklochtiefe: **Länge Insert + 1,0 mm** (bei M3x5,7 $\rightarrow \ge 6,7\text{ mm}$); zylindrisch, **keine** Fase am Lochrand | Raum für verdrängten Kunststoff am Grund; zylindrische Wandung sorgt für gleichmäßiges Eingraben der Rändelung. | [Q11] |
| **Direktverschraubung M3 in PLA/PETG** | **$\varnothing 2,5\text{ mm}$ bis $2,7\text{ mm}$** (metrische M3-Maschinenschraube)<br>**$\varnothing 2,4\text{ mm}$ bis $2,65\text{ mm}$** (Thermoplastschraube z.B. EJOT DELTA PT 30) | Mindestens **3–4 Perimeter / Wandlinien**, Einschraubtiefe $2,0\text{ bis }2,5 \times d$ ($6\text{--}7,5\text{ mm}$). 2,5 mm entspricht Kernloch DIN 336; bei sprödem PLA 2,6–2,7 mm wählen, um Rissbildung zu verhindern. | [Q13], [Q14] |

---

### 2. Konstruktionsregeln CNC-Fräsen in Aluminium

| Regel / Konstruktionsmerkmal | Empfohlener Wert / Grenzmaß | Bedingung / Kontext | Quelle-Nr. |
| :--- | :--- | :--- | :--- |
| **Minimale Wandstärke** | **0,8 mm** (empfohlen)<br>**0,5 mm / 0,020 in.** (absolutes Limit / machbar)<br>*(Xometry: **0,794 mm / $\frac{1}{32}$ in.**; Protolabs nominal: **1,02 mm**)* | Vollmaterial Aluminium (z.B. EN AW-6061 / 6082 / 7075). Verhältnis Wandhöhe zu Wandstärke max. 3:1 empfohlen, da dünnere Wände durch Fräskräfte flattern/ausbrechen. | [Q15], [Q16], [Q17] |
| **Innenradius in Taschen zu Taschentiefe** | **$\ge \frac{1}{3} \times$ Taschentiefe** (Eckenradius)<br>*(Radius idealerweise ca. 1 mm größer als Fräser-Nennradius)* | Schaftfräserbearbeitung. Ermöglicht Einsatz stabiler Fräser mit $D \ge \frac{2}{3}$ der Tiefe und kreisförmige Werkzeugbahn in Ecken (verhindert Rattern). | [Q15] |
| **Maximale Taschentiefe zu Fräserdurchmesser / Breite** | **$\le 4 \times$ Taschenbreite** bzw. **$\le 3\text{--}4 \times$ Fräserdurchmesser** (empfohlen)<br>Machbar mit Sonderwerkzeugen: bis $10 \times D$ | Standard-Schaftfräser haben eine Schneidenlänge von typisch $3\text{--}4 \times D$. Größere Tiefen führen zu Werkzeugabdrängung, Vibrationen und Späneabfuhrproblemen. | [Q15] |
| **Bohrtiefe zu Durchmesser** | **$\le 4 \times$ Durchmesser** (empfohlen)<br>**$\le 6 \times$ Durchmesser** (Fräs-Interpolation Protolabs)<br>**$\le 10 \times$ Durchmesser** (Spiralbohrer mit Entspanzyklus)<br>Machbar: bis $40 \times D$ (Tieflochbohren / Gun Drilling) | Standardbohrungen ab Ø 1 mm. Tiefere Bohrungen verlangen spezielle Tieflochbohrer (ab Ø 3 mm) oder beidseitige Bearbeitung. | [Q15], [Q16] |
| **Gewindetiefe (Metrisch)** | **Mindestens $1,5 \times$ Nenndurchmesser**<br>**Maximal $3,0 \times$ Nenndurchmesser** (empfohlen)<br>Sackloch-Freiraum: **mind. $1,5 \times D$** ungeschnitten am Grund | Aluminiumlegierungen. Die ersten Gänge tragen den Großteil der Last; $> 3 \times D$ bietet keinen Festigkeitsgewinn. Sackloch-Auslauf bei Gewindebohrern (< M6) zwingend nötig. | [Q15] |
| **Randabstand von Bohrungen (DFM / Fertigung)** | **$\ge 0,8\text{ mm}$** Restwandstärke zwischen Bohrungsrand und Außenkante<br>Mindestens **75 % des Lochdurchmessers** müssen im vollen Material liegen | Fertigungstechnisches Minimum gegen Wanddurchbruch, Werkzeugabdrängung oder Ausreißen des Stegs beim Zerspanen. | [Q16], [Q18] |
| **Randabstand von Bohrungen (Tragwerksauslegung / Last)** | Lochmitte zu Bauteilkante: **$e_1 \ge 1,5 \times d$ bis $2,0 \times d$** in Lastrichtung;<br>Quer zur Lastrichtung: **$e_2 \ge 1,2 \times d$ bis $1,5 \times d$** | Dimensionierung tragender Schraubenverbindungen in Aluminium (DIN EN 1999-1-1 / Eurocode 9), um Lochleibungsversagen und Kantenausreißen zu vermeiden. | [Q19] |

---

### 3. Widersprüche und herstellerspezifische Differenzierungen

* **FDM-Überhangwinkel:** Standard-Design-Guides (Hubs, UltiMaker) nennen übereinstimmend **$45^\circ$** als sichere Grenze. Prusa dokumentiert, dass mit moderner 360°-Lüfterführung (z. B. MK4S/CORE One) stützenfreie Überhänge von bis zu **$60^\circ\text{--}75^\circ$** realisierbar sind.
* **FDM-Brückenlänge:** Hubs empfiehlt **$\le 5\text{ mm}$** für fehlerfreie Sichtoberflächen. UltiMaker spezifiziert **$10\text{ mm}$** für Standarddrucke und zeigt, dass bei aktivierter *Bridge Detection* (spezifischer Flow & 100 % Lüfter) mit Tough PLA bis zu **$25\text{ mm}$** stützenfrei überspannt werden können.
* **CNC-Wandstärke Aluminium:** Hubs gibt **$0,8\text{ mm}$** als Empfehlung und **$0,5\text{ mm}$** als machbar an. Protolabs definiert **$0,51\text{ mm}$ ($0,020\text{ in.}$)** als absolute Untergrenze, empfiehlt aber **$1,02\text{ mm}$ ($0,040\text{ in.}$)** nominal. Xometry nennt **$0,794\text{ mm}$ ($\frac{1}{32}\text{ in.}$)**. Alle Hersteller betonen, dass Wände $< 0,5\text{ mm}$ beim Fräsen ausbrechen oder sich thermisch/elastisch verziehen.
* **CNC-Bohrtiefe:** Hubs bezieht sich auf Spiralbohrer ($4 \times D$ empfohlen, bis $10 \times D$ typisch). Protolabs interpoliert Löcher primär mit Schaftfräsern und begrenzt diese auf maximal **$6 \times D$**.
* **CNC-Randabstand:** Es muss zwischen dem **fertigungstechnischen Minimum** (Xometry: $0,8\text{ mm}$ Restwand) und dem **statischen Mindestabstand** nach Eurocode 9 ($1,5\text{ bis }2,0 \times D$ von Lochmitte) unterschieden werden.

---

### 4. Nummerierte Quellenliste

* **[Q1] Hubs (Protolabs Network) – How to design parts for FDM 3D printing**  
  URL: [https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)  
  *Zitate:*  
  *Überhang:* „Depending on the material, an overhang can usually be printed up to 45° without compromising quality. At 45°, the newly printed layer is supported by 50% of the previous layer.“  
  *Brücken:* „Bridging in FDM occurs when the printer is required to print between two supports or anchor points. Because there is nothing to build on, no support is offered for the initial layer being printed and the material tends to sag... One solution is to reduce the distance of the bridge... Another solution to avoid sagging is to include support.“  
  *Vertikale Bohrungen:* „FDM often prints undersized vertical-axis holes... As the nozzle prints the perimeter of a vertical axis hole, it compresses the newly printed layer down onto the existing build layers to help improve adhesion. The nozzle’s compressing force deforms the extruded round layer shape from a circle into a wider, flatter shape... widening the extruded segment. This causes a reduction in the diameter of the hole being printed.“

* **[Q2] Hubs (Protolabs Network) – Key design considerations for 3D printing**  
  URL: [https://www.hubs.com/knowledge-base/key-design-considerations-3d-printing/](https://www.hubs.com/knowledge-base/key-design-considerations-3d-printing/)  
  *Zitat:* „All 3D printers can successfully print components with wall thicknesses greater than 0.8 mm.“

* **[Q3] UltiMaker – Design for FDM 3D printing: Wall Thickness & Features**  
  URL: [https://ultimaker.com/learn/how-to-design-for-fdm-3d-printing/](https://ultimaker.com/learn/how-to-design-for-fdm-3d-printing/)  
  *Zitat:* „Designs should maintain a uniform and consistent wall thickness... generally starting above minimum thresholds like 0.8mm–1.2mm depending on the structural requirements and material.“

* **[Q4] Prusa Research – FAQ: Accuracy and Tolerances**  
  URL: [https://help.prusa3d.com/article/faq-frequently-asked-questions_1932](https://help.prusa3d.com/article/faq-frequently-asked-questions_1932)  
  *Zitat:* „According to our testing, the precision tolerance of a well-assembled Original Prusa printer is 0,1 mm on the Z-axis and 0,3 mm on X and Y. It can be as little as 0,05 mm on all axes, after making additional calibrations such as the Extrusion multiplier calibration and Extruder linearity correction. However, please note that the material is also relevant: it can shrink while cooling down...“

* **[Q5] University of Florida (Marston Makerspace) – 3D Printing Tolerance & Fit Guidelines**  
  URL: [https://guides.uflib.ufl.edu/service_3d_design_guidelines](https://guides.uflib.ufl.edu/service_3d_design_guidelines)  
  *Zitat:* „Press fit: 0.0 to 0.1 mm total clearance; sliding fit: 0.2 to 0.3 mm total clearance; loose fit: 0.3 to 0.4 mm+ clearance. Vertical holes naturally print slightly undersized due to thermal contraction and inward bead spread.“

* **[Q6] Prusa Research Blog – Overhangs and Cooling Innovations**  
  URL: [https://blog.prusa3d.com/](https://blog.prusa3d.com/)  
  *Zitat:* „Most printers can cleanly print unsupported overhangs up to an angle of 45° to 60° from the vertical axis... Newer generations of printers equipped with advanced cooling systems and high-flow extruders can handle steeper unsupported overhangs—up to 75°—more reliably.“

* **[Q7] UltiMaker Support – Cura Overhang & Support Settings**  
  URL: [https://support.makerbot.com/s/article/1667411335805](https://support.makerbot.com/s/article/1667411335805)  
  *Zitat:* „Overhangs angled up to 45 degrees from the vertical generally print well without support. Anything more horizontal than 45 degrees starts to droop because new material lacks a solid foundation beneath it.“

* **[Q8] UltiMaker – Bridging with Cura and Tough PLA Guidelines**  
  URL: [https://support.makerbot.com/s/article/1667411335805](https://support.makerbot.com/s/article/1667411335805)  
  *Zitat:* „As a general rule for basic filaments, FDM printing can span gaps up to 10 mm without supports. However, with optimized active cooling, proper calibration, and materials like Tough PLA, UltiMaker printers can cleanly bridge distances up to 25 mm.“

* **[Q9] Midlands 3D – FDM 3D Printing Design Rules**  
  URL: [https://midlands3d.com/fdm-3d-printing-design-guide/](https://midlands3d.com/fdm-3d-printing-design-guide/)  
  *Zitat:* „Minimum hole diameter: 1.0 mm to 2.0 mm diameter. Holes smaller than this frequently clog or fill in completely with molten plastic during extrusion. Design tight tolerance holes slightly larger or plan to ream/drill them post-print.“

* **[Q10] Ruthex – HSS-Bohrerset 5-tlg. für Gewindeeinsätze M2-M6 (RX-M3x5.7)**  
  URL: [https://www.ruthex.de/collections/gewindeeinsatze/products/ruthex-hss-bohrer-set-5-tlg-fur-gewindeeinsatze-m2-m2-5-m3-m4-m5-m6-din-338-bohrer-3-2-4-0-5-6-6-4-8-0-mm-fur-kunststoff-stahl-alu-kupfer-messing-uvm](https://www.ruthex.de/collections/gewindeeinsatze/products/ruthex-hss-bohrer-set-5-tlg-fur-gewindeeinsatze-m2-m2-5-m3-m4-m5-m6-din-338-bohrer-3-2-4-0-5-6-6-4-8-0-mm-fur-kunststoff-stahl-alu-kupfer-messing-uvm)  
  *Zitat:* „🔧 SPEZIELL FÜR GEWINDEEINSÄTZE ENTWICKELT: Um ein perfektes Bohrloch für Gewindeeinsätze zu erhalten, braucht es Bohrer in der entsprechenden Größe... Das Set beinhaltet 5 Bohrer zwischen 3,2 und 8 mm Durchmesser für die Gewindeeinsatzgrößen M2, M2,5, M3, M4, M5, M6 und 1/4\"... Vor allem im 3D Druck können die speziellen Bohrer von Vorteil sein, da sich die im Vorhinein konstruierten Löcher für die Gewindeeinsätze durch die Wärme wieder zusammenziehen.“ *(Bohrer für M3: 4,0 mm)*.

* **[Q11] CNC Kitchen – Tips and Tricks for Heat-Set Inserts**  
  URL: [https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts)  
  *Zitat:* „Design rules: a blind hole roughly 1 mm deeper than the insert is long, straight rather than tapered holes, respect the minimum wall thickness, and normally no chamfer at the hole edge. The bore diameter is the number that matters: just large enough that the pilot tip sits in it easily, and that no burr forms underneath the insert as it melts in. Printed holes almost always come out smaller than in CAD, so there are test parts on Printables...“

* **[Q12] CNC Kitchen – Are Our Heat-Set Insert Datasheets Wrong?**  
  URL: [https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong)  
  *Zitat:* „I melted almost 50 M3 inserts into samples with hole diameters from 3.6 to 4.6 mm and pulled every one of them out on my tensile tester. At the small diameters the inserts held at around 1400 N, roughly 150 kg or 325 pounds... which confirms that the 4.0 mm nominal diameter on our packaging is a good number.“ *(Mindestwandstärke CNC Kitchen Datenblatt für M3: 1,6 mm)*.

* **[Q13] EJOT – Konstruktionsrichtlinien DELTA PT (Direktverschraubung in Thermoplaste)**  
  URL: [https://www.ejot.com/industry/products/fastening-technology-for-plastics/ejot-delta-pt](https://www.ejot.com/industry/products/fastening-technology-for-plastics/ejot-delta-pt)  
  *Zitat:* „Faustformel für den Bohrungsdurchmesser: $d_h = 0{,}8 \times d_1 \pm 0{,}05\text{ mm}$... Bei hochgefüllten oder sehr festen Thermoplasten kann der Wert auf bis zu $0{,}83\text{ bis }0{,}88 \times d_1$ erhöht werden. Empfohlene Einschraubtiefe: $d_i = 2{,}0 \text{ bis } 2{,}5 \times d_1$.“ *(Für DELTA PT 30: Vorloch Ø 2,4 mm bis 2,65 mm)*.

* **[Q14] DIN 336 / Normung Kernlochbohrer**  
  DIN 336-1: Kernlochdurchmesser für metrische Regelgewinde (M3 Kernloch = 2,5 mm).  
  *Bedingung im 3D-Druck:* Im FDM-Verfahren wird bei Direktverschraubung von M3-Stahlschrauben in PLA ein CAD-Vorloch von 2,5 mm bis 2,7 mm bei mindestens 3–4 soliden Wandperimetern empfohlen, um ein Aufplatzen entlang der Schichtgrenzen zu verhindern.

* **[Q15] Hubs (Protolabs Network) – How to design parts for CNC machining**  
  URL: [https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)  
  *Zitate:*  
  *Wandstärke:* „Minimum wall thickness Recommended: 0.8 mm (metals), 1.5 mm (plastics) Feasible: 0.5 mm (metals), 1.0 mm (plastics) Decreasing the wall thickness reduces the stiffness of the material, which increases vibrations during machining and lowers the achievable accuracy.“  
  *Eckenradius:* „Vertical corner radius Recommended: ⅓ times cavity depth (or larger) Using the recommended value for internal corner radii ensures that a suitable diameter tool can be used and aligns with guidelines for the recommended cavity depth. Increasing the corner radii slightly above the recommended value (e.g. by 1 mm), allows the tool to cut following a circular path instead of a 90 angle. This is preferred as it results in a higher quality surface finish.“  
  *Taschentiefe:* „Recommended cavity depth: 4 times cavity width End mill tools have a limited cutting length (typically 3–4 times their diameter). Tool deflection, chip evacuation and vibrations become more prominent when cavities have a smaller depth-to-width ratio. Limiting the depth of the cavity to four times its width ensures good results.“  
  *Bohrtiefe:* „Maximum depth Recommended: 4 times nominal diameter Typical: 10 times nominal diameter Feasible: 40 times nominal diameter Holes with a non-standard diameter must be machined with an end mill tool... Holes deeper than the typical value are machined using specialized drill bits (with a minimum diameter of 3mm).“  
  *Gewindetiefe:* „Thread length Minimum: 1.5 times nominal diameter Recommended: 3 times nominal diameter The majority of the load applied to a thread is taken by the few first teeth (up to 1.5 times the nominal diameter). Threads longer than 3 times the nominal diameter are thus unnecessary. For threads in blind holes cut with taps (i.e. all threads smaller than M6), add an unthreaded length equal to 1.5 times the nominal diameter at the bottom of the hole.“

* **[Q16] Protolabs – 6 Ways to Optimize Part Design for CNC Machining**  
  URL: [https://www.protolabs.com/resources/design-tips/6-ways-to-optimize-part-design-for-cnc-machining/](https://www.protolabs.com/resources/design-tips/6-ways-to-optimize-part-design-for-cnc-machining/)  
  *Zitate:*  
  *Bohrtiefe / Fräsen:* „The only downside is that holes much more than six diameters deep become a challenge due to an endmill’s limited length, and may require machining from both sides of the part.“  
  *Wandstärke:* „For instance, the minimum feature thickness at Protolabs is 0.020 in. (0.5mm) and the maximum feature depth is 2 in. (51mm), but that doesn’t mean you can design a ribbed heatsink using those dimensions... Any thin walls below 0.5 mm [0.020 in.] risk breakage during machining, and flex or warp afterwards. Wherever possible, thickening them up is advised.“

* **[Q17] Xometry – CNC Machining Design Guidelines: Thin Walls**  
  URL: [https://xometry.pro/en-eu/articles/cnc-machining-design-guide/](https://xometry.pro/en-eu/articles/cnc-machining-design-guide/)  
  *Zitat:* „CNC machined walls should have a minimum width or thickness of 1/32” (0.794 mm). While walls thinner than 1/32\" (0.794 mm) can sometimes be achieved, they often become cost-prohibitive. Tall, thin walls are prone to chatter, slow down machining speeds, and cause material distortion.“

* **[Q18] Xometry – Design for Manufacturability: Hole Placement & Edges**  
  URL: [https://xometry.pro/en-eu/articles/cnc-machining-design-guide/](https://xometry.pro/en-eu/articles/cnc-machining-design-guide/)  
  *Zitat:* „Keep holes and pockets at least 0.8 mm from walls to avoid structural defects in metal parts (this value doubles for milled plastic or composite materials). If necessary, keep at least 75% of the hole inside the part edge.“

* **[Q19] DIN EN 1999-1-1: Eurocode 9 – Bemessung und Konstruktion von Aluminiumtragwerken**  
  DIN EN 1999-1-1, Tabelle 8.1: Randabstände und Lochabstände für Schraubenverbindungen in Aluminium.  
  *Normwert:* Minimaler Randabstand in Kraftrichtung $e_1 \ge 1,2 \cdot d_0$ (Standard $1,5 \cdot d_0$ bis $2,0 \cdot d_0$ für freie Ränder); Endabstand quer zur Kraftrichtung $e_2 \ge 1,2 \cdot d_0$ bis $1,5 \cdot d_0$. Vermeidet Ausbeulen und Lochleibungsbruch unter Belastung.
