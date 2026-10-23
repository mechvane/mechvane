> Gemini 3.8 Flash, nicht verifiziert. Recherche 2026-10-21.

# FDM-3D-Druck: Konstruktions- und Fertigungsregeln

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert  
Sprache: Deutsch

Dieses Dokument fasst die werkstoff- und fertigungstechnischen Konstruktionsregeln für das Schmelzschichtverfahren (FDM / FFF) zusammen. Es dient als Regelbasis für die algorithmische Geometrieprüfung (`check_design`) und parametrische Modellerstellung im Projekt **inventa**.

---

## Detaillierte Katalog-Einträge

### FDM: Maximaler Überhangwinkel ohne Stützstruktur (Standard)
* **Aussage / Wert:** Der maximal zulässige Überhangwinkel für stützenfreies Drucken beträgt standardmäßig bis zu 45° gegenüber der Vertikalen.
* **Geltungsbereich:** FDM-Verfahren, thermoplastische Filamente, Standardkühlung, Standarddüse.
* **Herkunft:** Hersteller / Fertigungsleitfaden (Hubs).
* **Quelle:** [Hubs FDM 3D Printing Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
  * *Wörtliches Zitat:* „Depending on the material, an overhang can usually be printed up to 45° without compromising quality. At 45°, the newly printed layer is supported by 50% of the previous layer.“
* **Begründung:** Bei einem Winkel von 45° wird die neu abgelegte Schicht noch zu 50% von der darunterliegenden Raupe abgestützt. Größere Neigungswinkel führen ohne Unterstützung zu Durchhängen und rauen Oberflächen.
* **Härte:** Hinweis (weiche Grenze; Geometrien über 45° erfordern Stützstrukturen oder Hochleistungskühlung).
* **Prüfstatus:** offen.

---

### FDM: Erweiterter Überhangwinkel bei optimierter 360-Grad-Bauteilkühlung
* **Aussage / Wert:** Mit optimierter 360°-Bauteilkühlung und Nextruder können Überhänge im Bereich von 45 bis 60 Grad sauber und bis zu 75° ohne Stützen gedruckt werden.
* **Geltungsbereich:** FDM-Drucker mit Rundumkühlung (z. B. Prusa MK4S, CORE One), PLA/PETG.
* **Herkunft:** Hersteller (Prusa Research).
* **Quelle:** [Prusa Knowledge Base: Modeling with 3D printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
  * *Wörtliches Zitat:* „A 3D printer can cleanly print overhanging structures with an angle between 45 and 60 degrees, depending on your nozzle diameter and settings. Our FDM printer models with Nextruder and 360° cooling can print overhangs of up to 75° without supports.“
* **Begründung:** Durch die sofortige Erstarrung der Schmelze im gerichteten Luftstrom wird das Absacken der überstehenden Raupe auch bei geringer Schichtüberdeckung verhindert.
* **Härte:** Hinweis (gilt nur für Drucker mit entsprechender Kühlausstattung).
* **Prüfstatus:** offen.

---

### FDM: Maximale Brückenlänge ohne Stützstruktur
* **Aussage / Wert:** Horizontale Brücken ohne Stützstruktur sollten eine freie Spannweite von 5 mm nicht überschreiten, um Durchhang und Oberflächenraupen zu vermeiden.
* **Geltungsbereich:** Horizontale Brückenelemente (Bridging) im FDM-Druck aller Standard-Thermoplaste.
* **Herkunft:** Fertigungsdienstleister (Hubs).
* **Quelle:** [Hubs FDM 3D Printing Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
  * *Wörtliches Zitat:* „Due to the nature of FDM, sagging or marks from support material are to some extent always present unless the bridge is less than 5mm. If a smooth, level surface is required, an advanced solution is to split the design into separate parts or do some form of post-processing.“
* **Begründung:** Ohne darunterliegende Tragschicht neigt der frei extrudierte Faden durch Gravitation und Eigenspannungen zum Durchhängen; unter 5 mm ist dieser Effekt vernachlässigbar klein.
* **Härte:** Fehler (bei Sichtflächen und Passflächen ohne Support); Hinweis (bei rein tragenden Hohlräumen).
* **Prüfstatus:** offen.

---

### FDM: Mindestwandstärke und Extrusionsbreite bei 0,4-mm-Standarddüse
* **Aussage / Wert:** Bei einer Standarddüse von 0.4 mm Durchmesser beträgt die Standard-Extrusionsbreite 0.45 mm. Wände, die dünner als ein Perimeter sind, können nicht gedruckt werden.
* **Geltungsbereich:** FDM-Druck mit 0.4 mm Düsendurchmesser.
* **Herkunft:** Hersteller / Slicer-Spezifikation (Prusa Research).
* **Quelle:** [Prusa Knowledge Base: Modeling with 3D printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
  * *Wörtliches Zitat:* „The most common size and stock nozzle size on MK3S is 0.4 mm, which in PrusaSlicer has an extrusion width of 0.45 mm. PrusaSlicer can improve upon this in multiple ways. However, it may be wise to keep these numbers in mind, especially when you’re designing thin walls or tiny features. Walls thinner than one nozzle perimeter are not printable.“
* **Begründung:** Der Slicer erzeugt Bahnen basierend auf der Düsen-Extrusionsbreite. Unterschreitet die Wandstärke im CAD-Modell die einfache Perimeterbreite von 0.45 mm, wird die Kontur im G-Code vollständig ausgelassen.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn vertikale Wände dünner als die einfache Düsenbahn sind).
* **Prüfstatus:** offen.

---

### FDM: Bohrungsdurchmesser und Lochverengung bei vertikaler Achse
* **Aussage / Wert:** Vertikale Bohrungen drucken im FDM-Verfahren systematisch mit verringertem Innendurchmesser und fallen kleiner aus als im CAD konstruiert.
* **Geltungsbereich:** Z-Achsen-Bohrungen im Schmelzschichtverfahren.
* **Herkunft:** Hersteller / Fertigungsleitfaden (Hubs).
* **Quelle:** [Hubs FDM 3D Printing Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
  * *Wörtliches Zitat:* „As the nozzle prints the perimeter of a vertical axis hole, it compresses the newly printed layer down onto the existing build layers to help improve adhesion. The nozzle’s compressing force deforms the extruded round layer shape from a circle into a wider, flatter shape (see image below). This increases the area of contact with the previously printed layer, improving adhesion but widening the extruded segment. This causes a decrease in the hole diameter being printed.“
* **Begründung:** Der Stauchdruck der Düse verformt den kreisförmigen Extrusionsstrang in einen abgeflachten Querschnitt, der nach innen in die Bohrung ausweicht. Bei engen Passtoleranzen muss nachgebohrt oder im Slicer kompensiert werden.
* **Härte:** Hinweis (kritische Passungsbohrungen im CAD überdimensionieren oder Nacharbeit vorsehen).
* **Prüfstatus:** offen.

---

### FDM: Maßkorrektur über XY-Lochkompensation
* **Aussage / Wert:** Die XY-Lochkompensation im Slicer passt gezielt die lichten Maße innerer Hohlräume an, ohne die Außenabmessungen des Modells zu beeinflussen.
* **Geltungsbereich:** Slicing-Parameter für Funktionsbauteile (Bambu Studio, PrusaSlicer).
* **Herkunft:** Hersteller (Bambu Lab Wiki).
* **Quelle:** [Bambu Lab Wiki: XY Hole and Contour Compensation](https://wiki.bambulab.com/en/software/bambu-studio/xy-hole-contour-compensation)
  * *Wörtliches Zitat:* „XY Hole Compensation Adjusts the size of holes (closed, hollow areas) in each layer. It only affects holes and does not change the outer size of the model. XY Contour Compensation Adjusts the outer contour of the model. It increases or decreases the overall XY size while keeping hole sizes unchanged.“
* **Begründung:** Durch Schrumpfung, Schichtstauchung und thermische Kontraktion schrumpfen Innenkonturen. Die Entkopplung von Innen- und Außenkonturkompensation ermöglicht maßhaltige Passsitze.
* **Härte:** Hinweis (Best Practice für den Slicing-Prozess).
* **Prüfstatus:** offen.

---

### FDM: Grundtoleranz und Passungsspiel für bewegliche Teile
* **Aussage / Wert:** Ein gut kalibrierter FDM-Drucker erreicht eine Grundgenauigkeit von mindestens 0.2 mm. Für bewegliche Verbindungen wie Scharniere wird ein Spaltmaß von mindestens 0.3 mm empfohlen.
* **Geltungsbereich:** Passungen, Scharniere und Gelenke im FDM-Druck.
* **Herkunft:** Hersteller (Prusa Research).
* **Quelle:** [Prusa Knowledge Base: Modeling with 3D printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
  * *Wörtliches Zitat:* „An Original Prusa will be accurate to at least 0.2 mm, but you also need to remember that different materials can warp or shrink during printing. Consider if two parts should move, like a hinge, or lock/snap together with a friction fit. An initial good measurement for movable parts is at least 0.3 mm.“
* **Begründung:** Fertigungstoleranzen in XY und Z sowie thermischer Verzug erfordern einen konstruktiven Mindestabstand, um ein unlösbares Verschmelzen benachbarter Schichten zu verhindern.
* **Härte:** Fehler (bei Gelenken mit Spaltmaß unter 0.2 mm); Hinweis (bei Reibsitz und Schnappverbindungen).
* **Prüfstatus:** offen.

---

### FDM: Mindestwandstärke um gedruckte Gewindebohrungen
* **Aussage / Wert:** Als Richtwert muss die minimale Wandstärke um eine Gewindebohrung mindestens dem Durchmesser des Verbindungselements entsprechen, beispielsweise mindestens 5 mm Wandstärke bei einem M5 Verbindungselement.
* **Geltungsbereich:** Direktverschraubungen und Gewinde in FDM-Bauteilen.
* **Herkunft:** Fertigungsleitfaden (Hubs).
* **Quelle:** [Hubs Knowledge Base: Assembling 3D printed parts with threaded fasteners](https://www.hubs.com/knowledge-base/how-assemble-3d-printed-parts-threaded-fasteners/)
  * *Wörtliches Zitat:* „As a rule of thumb the minimum wall thickness around a thread should match the diameter of the fastener (e.g. an M5 fastener requires a minimum of 5mm wall thickness around the threaded hole). If the wall thickness is too low, parts can bulge and distort due to the added stress and in some cases (particularly with FDM) delamination or fracturing can occur.“
* **Begründung:** Geringe Wandstärken wölben sich unter Schraubenvorspannung aus oder führen durch Sprengwirkung zum Delaminieren der Schichten entlang der Schweißnähte.
* **Härte:** Fehler (Sollbruchgefahr bei Unterschreitung).
* **Prüfstatus:** offen.

---

### FDM: Abmessungen für M3-Gewindeeinsätze zum Einschmelzen
* **Aussage / Wert:** Für standardmäßige M3 Gewindeeinsätze mit einer Länge L von 5.7 mm beträgt der Einsatzdurchmesser D1 4.6 mm, der empfohlene Vorlochdurchmesser D2 4.0 mm, die Mindestwandstärke W 1.6 mm und die Sacklochtiefe mindestens L + 1 mm.
* **Geltungsbereich:** Metrische Gewindeeinsätze (Heat-Set Inserts) in thermoplastischen Kunststoffen.
* **Herkunft:** Hersteller / Prüflabor (CNC Kitchen).
* **Quelle:** [CNC Kitchen Heat-Set Insert Dimensions and Design Guidelines PDF](https://www.cnckitchen.com/s/CNCKitchen_Heat-Set-Insert-Dimensions-and-Design-Guidelines.pdf)
  * *Wörtliches Zitat:* „L = length D1 = insert diameter D2 = hole diameter W = min. wall thickness“
* **Begründung:** Der zylindrische Hohlraum mit D2 = 4.0 mm bietet genau das erforderliche Materialvolumen, um die Rändelung beim thermischen Einpressen formschlüssig zu umschließen. Der Tiefenzuschlag von 1 mm verhindert ein Aufsitzen des Einsatzes auf verdrängter Schmelze.
* **Härte:** Fehler (bei Wandstärken unter 1.6 mm platzt der Kunststoffdom auf).
* **Prüfstatus:** offen.

---

### FDM: Mechanische Anisotropie und Schichtorientierung
* **Aussage / Wert:** FDM-Komponenten weisen ein ausgeprägt anisotropes Festigkeitsverhalten auf und besitzen entlang der Schichtaufbaurichtung (Z-Achse) eine inhärente Schwachstelle.
* **Geltungsbereich:** Alle thermoplastischen FDM-Drucke unter mechanischer Zug- und Biegebelastung.
* **Herkunft:** Fertigungsleitfaden (Hubs).
* **Quelle:** [Hubs FDM 3D Printing Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
  * *Wörtliches Zitat:* „Due to the anisotropic nature of FDM printing, understanding the application of a component and how it is built are critical to the success of a design. FDM components are inherently weaker in one direction due to layer orientation. A lack of continuous material paths and the stress concentration created by each layer joint contribute to this weakness. Since the layers are printed as a round-ended rectangle, the joints between each layer are actually small valleys. This creates a stress concentration with a tendency to crack.“
* **Begründung:** Der abgerundete Querschnitt der extrudierten Raupen erzeugt an den Schichtfugen winzige Kerbtäler. Bei Zugbelastung senkrecht zur Schichtebene wirken diese als Spannungskonzentratoren und führen zu vorzeitigem Sprödbruch.
* **Härte:** Hinweis (Hauptbelastungsrichtung im CAD parallel zu den Schichten in der XY-Ebene orientieren).
* **Prüfstatus:** offen.

---

### FDM: Schichthaftung und Einfluss der Extrusionsbreite
* **Aussage / Wert:** Eine Verbreiterung der Extrusionsbahn verbessert die Schichtverbindung messbar: Die Schichthaftung steigt ab 90% der Düsenbreite kontinuierlich an und erreicht ihr Maximum bei etwa 150%.
* **Geltungsbereich:** Schichtverbindung und Festigkeitsoptimierung im FDM-Druck.
* **Herkunft:** Versuch / Fachartikel (CNC Kitchen).
* **Quelle:** [CNC Kitchen: The effect of extrusion width on strength and quality of 3D prints](https://www.cnckitchen.com/blog/the-effect-of-extrusion-width-on-strength-and-quality-of-3d-prints)
  * *Wörtliches Zitat:* „Layer adhesion climbs from 90% and peaks around 150%, then falls again, probably because the rough surface creates stress concentrations.“
* **Begründung:** Ein höherer Stauchdruck presst die Schmelze intensiver in die Mikrostrukturen der Vorlage. Über 150% Extrusionsbreite nehmen Oberflächenunregelmäßigkeiten zu, die erneut als Kerben wirken.
* **Härte:** Hinweis (Best Practice für hochfeste Funktionsbauteile).
* **Prüfstatus:** offen.

---

### FDM: Werkstoffschwindung und Verzug bei ABS und ASA
* **Aussage / Wert:** Bauteile aus ABS und ASA unterliegen beim Abkühlen einer merklichen Schwindung; der typische Schwindungsfaktor liegt im Bereich von 1 bis 2 %.
* **Geltungsbereich:** Technische Thermoplaste ABS (Acrylnitril-Butadien-Styrol) und ASA (Acrylnitril-Styrol-Acrylat).
* **Herkunft:** Hersteller (Prusa Research).
* **Quelle:** [Prusa Knowledge Base: ASA Filament Guide](https://help.prusa3d.com/article/asa_2058)
  * *Wörtliches Zitat:* „You should keep in mind that ABS-printed parts tend to shrink slightly after cooling down. We recommend printing a testing object and comparing it with a source model. The shrinkage factor of this material is usually somewhere around 1-2%.“
* **Begründung:** Hohe Wärmeausdehnungskoeffizienten führen bei ungleichmäßiger Abkühlung zu starkem Verzug (Warping) und Maßabweichungen, weshalb beheizte Bauräume erforderlich sind.
* **Härte:** Fehler (bei passgenauen Teilen muss der Skalierungsfaktor im Slicer berücksichtigt werden).
* **Prüfstatus:** offen.

---

### FDM: Maßhaltigkeit und Temperaturbeständigkeit von PETG
* **Aussage / Wert:** PETG weist nur sehr geringe thermische Ausdehnung auf, schrumpft und verzieht sich kaum und ist für Einsatztemperaturen unter 80 °C geeignet.
* **Geltungsbereich:** Glykol-modifiziertes Polyethylenterephthalat (PETG).
* **Herkunft:** Hersteller (Prusa Research).
* **Quelle:** [Prusa Knowledge Base: PETG Filament Guide](https://help.prusa3d.com/article/petg_2059)
  * *Wörtliches Zitat:* „PETG has a glossy surface, adheres greatly to a print sheet, and does not shrink or warp (it has very little thermal expansion), therefore it’s suitable for printing large models. Plus, its high tenacity and flexibility often prevent it from breaking. Due to good temperature resistance, PETG parts are suitable both for interior and most exterior use (with temperatures below 80 °C).“
* **Begründung:** Die Glykol-Modifikation verringert die Kristallisationsneigung, was für gleichmäßige Maßhaltigkeit bei großen Bauteilen sorgt.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### FDM: Temperatureinsatzgrenze und Versagensverhalten von PLA
* **Aussage / Wert:** Unmodifiziertes Standard-PLA erweicht und verformt sich bei Temperaturen über 60 °C und bricht bei Stoßbeanspruchung entlang der Schichten oder in Splitter.
* **Geltungsbereich:** Polylactid (PLA).
* **Herkunft:** Hersteller (Prusa Research).
* **Quelle:** [Prusa Knowledge Base: PLA Filament Guide](https://help.prusa3d.com/article/pla_2062)
  * *Wörtliches Zitat:* „It doesn’t resist high temperatures (it gets soft and deforms at temperatures over 60 °C), degrades under UV light and its mechanical resistance is also inferior - it breaks along layers or into shards upon impact.“
* **Begründung:** Die Glasübergangstemperatur von ca. 60 °C schließt PLA für thermisch beanspruchte mechanische Komponenten aus.
* **Härte:** Fehler (`check_design` muss warnen, wenn Bauteile für Betriebstemperaturen über 60 °C aus PLA gewählt werden).
* **Prüfstatus:** offen.

---

## Nicht erreichbare Quellen

Folgende Quellen wurden während der Recherche geprüft und erwiesen sich als nicht automatisiert abrufbar:

| Quelle / URL | Status | Grund / Bemerkung |
| :--- | :---: | :--- |
| `https://help.prusa3d.com/article/pla_2056` | 404 | Veraltete Artikel-ID auf Prusa Help; korrekte Ziel-ID ist `pla_2062`. |
| `https://help.prusa3d.com/article/polyamide-nylon_124176` | 404 | Veraltete URL; korrekter Pfad ist `polyamide-nylon_167188`. |
| `https://wiki.bambulab.com/en/software/bambu-studio/filament-shrinkage` | 404 | Einzelseite existiert nicht separat; Information ist in Wissensartikeln zur Kompensation integriert. |

---

## Offene Fragen

1. **Dynamische Schwindungskompensation je nach Füllgrad (Infill):** Wie stark skaliert die reale Bauteilschwindung bei hochgefüllten Teilen (z. B. 100% Infill) gegenüber dünnwandigen Schalenstrukturen bei ABS und Polyamid?
2. **Direkt gedruckte Gewinde M4 und kleiner:** Ab welcher Düsenfeinheit (0.2 mm vs. 0.25 mm) sind direkt geschnittene/gedruckte Gewinde kleiner als M5 bei FDM mechanisch belastbar?

---

## Vorschläge für eigene Druckversuche (Ultimaker 2+)

1. **Passungs- und Spaltmaßprüfkörper:**
   * Zylindrischer Zapfen (Nenndurchmesser 10 mm) mit abgestuften Passbohrungen von Spaltmaß 0.10 mm bis 0.40 mm in 0.05-mm-Schritten (PLA und PETG, Schichthöhe 0.15 mm).
   * Ermittlung des Übergangs von Presssitz zu leichtgängigem Spielsitz.
2. **Überhang- und Brückenkamm:**
   * Stufenkörper mit Überhangwinkeln von 30° bis 75° (in 5°-Schritten) und Brückenlängen von 5 mm bis 30 mm ohne Support.
   * Vermessung des Durchhangs an der Unterseite mit Messuhr.
3. **Ausreißversuch für M3-Gewindeeinsätze:**
   * Prüfblöcke mit Einschmelz-Vorlochdurchmessern von 3.8 mm, 4.0 mm und 4.2 mm bei Wandstärken von 1.2 mm bis 2.0 mm zur Verifikation der optimalen Haltekraft.

---

Quellenprüfung (tools/check_sources.py, 2026-10-21): alle Zitate und Zahlen im abgerufenen Quelltext gefunden. Damit ist der Wert in der Quelle belegt, aber nicht zwingend richtig übernommen.
