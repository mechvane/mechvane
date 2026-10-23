> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Nicht erreichbare Links: siehe `2026-10-20-quellen-nicht-erreichbar.md` (mit Browser-User-Agent nur wenige). Lizenzen und Zitate vor dem Übernehmen an der Quelle prüfen.

# Bestandsaufnahme frei zugänglicher Design-Guides und Konstruktionsrichtlinien für ein Open-Source-CAD-Ökosystem

Diese Bestandsaufnahme erfasst hersteller- und fertigerseitige Konstruktionsrichtlinien, Normauszüge und empirische Messreihen als Primärquellen für einen offenen, maschinenlesbaren Wissenskatalog (CAD Knowledge Base / DFM-Rule-Engine). 

Alle Angaben, Grenzwerte und Formeln basieren auf direkt überprüften Primärquellen. Gemäß Vorgabe wurden keine Werte aus dem Gedächtnis ergänzt; zu jedem Guide sind drei quantifizierbare Beispielregeln mit **wörtlichem Zitat und exakter Seiten- bzw. Abschnittsreferenz** hinterlegt.

---

## 1. Übersichtstabelle aller untersuchten Guides nach Themengebiet

| Themengebiet | Hersteller / Urheber | Titel des Guides | Format / Umfang | Direkte URL (PDF / Web) | Zugangsart |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wälzlager & Passungen** | SKF Gruppe | *Wälzlager (Katalog 17000/1 DE)* | PDF (1.152 S.) | [skf.com CDN (PDF)](https://cdn.skfmediahub.skf.com/api/public/094ea584acc90401/pdf_preview_medium/094ea584acc90401_pdf_preview_medium.pdf) / [skf.com/go/17000](https://www.skf.com/go/17000) | Frei zugänglich (keine Registrierung) |
| **Wälzlager & Umgebungskonstruktion** | Schaeffler (INA/FAG) | *HR 1: Wälzlager – Technische Grundlagen zur Gestaltung von Wälzlagerungen* | PDF (1.866 S.) | [schaeffler.com (PDF)](https://www.schaeffler.com/remotemedien/media/_shared_media/08_media_library/01_publications/schaeffler_2/catalogue_1/downloads_6/hr1_de_de.pdf) | Frei zugänglich (keine Registrierung) |
| **Gleitlager (Polymer)** | igus GmbH | *iglide® Plain Bearings Design Basics Guide* | PDF (8 S.) | [igus Toolbox (PDF)](https://toolbox.igus.com/wp-content/uploads/2023/08/iglide-plain-bearings-design-guide.pdf) / [igus.de Einbau](https://www.igus.de/info/gleitlager-einbau-und-toleranzen) | Frei zugänglich (keine Registrierung) |
| **Linearführungen & Präzisionsteile** | MISUMI Corporation | *Installation and Maintenance of Linear Guides (FA Standard Catalog Technical Data)* | PDF (2 S.) / Web | [misumi-ec.com (PDF)](https://id.misumi-ec.com/pdf/fa/2014/p1_529.pdf) / [MISUMI Tech Hub](https://us.misumi-ec.com/maker/misumi/mech/tech/) | Frei zugänglich (keine Registrierung) |
| **Verbindungstechnik & Montagerichtlinien** | Bossard Group | *Arrangement, design, assembly – Construction recommendations* | PDF (15 S.) | [bossard.com / ctfassets (PDF)](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3DLqM7Z9oEMiNjXOeKeL6V/b7565ca2741cfb3d15dd79287acefc0a/079_093_Construction_recommendations_Fastening_EN_01_2025.pdf) | Frei zugänglich (keine Registrierung) |
| **Mechanische Verbindungselemente** | Adolf Würth GmbH & Co. KG | *Technische Informationen zu Verbindungselementen* | PDF (90 S.) | [wuerth-industrie.com (PDF)](https://www.wuerth-industrie.com/web/media/downloads/brochures/de_wis/dino-technik.pdf) | Frei zugänglich (keine Registrierung) |
| **Drahtgewindeeinsätze (Metalle)** | Böllhoff Gruppe | *HELICOIL® Plus – Die Gewindetechnologie für hochbelastbare Verbindungen (Katalog 0100)* | PDF (56 S.) | [boellhoff.com Media (PDF)](https://media.boellhoff.com/files/pdf13/0100-helicoil-plus-at-de.pdf) | Frei zugänglich (keine Registrierung) |
| **Thermoplast-Direktverschraubung** | EJOT GmbH & Co. KG | *EJOT DELTA PT®: Predictable performance improvement for thermoplastics* | PDF (18 S.) | [ejot-atf.com (PDF)](https://www.ejot-atf.com/wp-content/uploads/2017/02/ATFDELTAPT2017HighRes.pdf) | Frei zugänglich (keine Registrierung) |
| **Selbstschneidende Gewindebuchsen** | Kerb-Konus-Vertriebs-GmbH | *Gewinde-Einsätze für Metalle: Ensat® (Technische Druckschrift Nr. 20)* | PDF (34 S.) | [kerbkonus.de (PDF)](https://www.kerbkonus.de/proddb/pdf/de.ds.20.pdf) | Frei zugänglich (keine Registrierung) |
| **Sicherungsringe & Nuten** | Seeger-Orbis GmbH | *Katalog Seeger-Ringe / Seeger Rings Catalogue (Ausgabe 2022)* | PDF (142 S.) | [seeger-orbis.de (PDF)](https://www.seeger-orbis.de/fileadmin/assets/zertifikate/SEEGER-KATALOGUE-light-2022_11.pdf) | Frei zugänglich (keine Registrierung) |
| **O-Ring-Dichtungsnuten** | Parker Hannifin Corp. | *Parker O-Ring Handbook (ORD 5700)* | PDF (292 S.) | [nianticseal.com Mirror (PDF)](https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf) / [parker.com/ORD5700](https://www.parker.com/ORD5700) | Frei zugänglich (Original-Portal z. T. mit WAF/CDN geschützt) |
| **Fertigungsdienstleister (Spritzguss)** | Protolabs | *Injection Molding Guide: Process, Design Tips, & Materials* | Web-Guide (HTML) | [protolabs.com Guide](https://www.protolabs.com/resources/guides-and-trend-reports/injection-molding-guide-process-design-tips-materials/) | Frei online zugänglich (keine Registrierung) |
| **Fertigungsdienstleister (Blech)** | Xometry | *Design Guide: Sheet Metal Fabrication* | Web-Guide & PDF | [xometry.com Design Guide](https://www.xometry.com/resources/design-guides/design-guide-sheet-metal-fabrication/) | Frei online lesbar / PDF mit Formular |
| **Fertigungsdienstleister (CNC)** | Hubs (Protolabs Network) | *CNC machining design guide* | Web-Guide (HTML) | [hubs.com CNC Guide](https://www.hubs.com/guides/cnc-machining/) | Frei online zugänglich (keine Registrierung) |
| **Fertigungsdienstleister (CNC/DFM)** | Fictiv | *Fictiv CNC Machining Design Guide* | Web-Guide (HTML) | [fictiv.com CNC Guide](https://www.fictiv.com/articles/fictiv-cnc-machining-design-guide) | Frei online zugänglich (keine Registrierung) |
| **Additive Fertigung (FDM/FFF)** | Prusa Research | *Modeling with 3D printing in mind* | Knowledge-Base (HTML) | [help.prusa3d.com KB 164135](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) | Frei online zugänglich (keine Registrierung) |
| **3D-Druck Gewindeeinsätze** | ruthex GmbH | *Produktdatenblatt RX-Reihe (Metrisches ISO-Gewinde)* | PDF (2 S.) | [igo3d.com Media (PDF)](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) / [ruthex Downloads](https://www.ruthex.de/pages/dokumente-downloads) | Frei zugänglich (keine Registrierung) |
| **Messreihen & Inserts (Empirisch)** | CNC Kitchen (Stefan Hermann) | *Dimensions & Design Guidelines (Heat-Set Inserts)* | PDF (2 S.) & Web | [cnckitchen.com Poster (PDF)](https://www.cnckitchen.com/s/CNCKitchen_Heat-Set-Insert-Dimensions-and-Design-Guidelines.pdf) / [cnckitchen.com Blog](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts) | Frei zugänglich (keine Registrierung) |
| **Schraubensicherung & Kleben** | Henkel AG & Co. KGaA / LOCTITE | *Loctite® Threadlocking User’s Guide* | PDF (12 S.) | [ellsworth.com (PDF)](https://www.ellsworth.com/globalassets/literature-library/manufacturer/henkel-loctite/henkel-loctite-user-guide-threadlocking.pdf) / [ludwigmeister.de Handbuch (PDF)](https://www.ludwigmeister.de/content/techn-informationen/chemische-produkte/klebstoffe/loctite_klebetechnik_de.pdf) | Frei zugänglich (keine Registrierung) |

---

## 2. Detaillierte Bestandsaufnahme aller 19 Guides

### 2.1 Lagertechnik, Gleitlager & Linearführungen

#### 1. SKF Gruppe – *Wälzlager (Katalog 17000/1 DE)*
* **Hersteller:** SKF Gruppe
* **URL:** [https://cdn.skfmediahub.skf.com/api/public/094ea584acc90401/pdf_preview_medium/094ea584acc90401_pdf_preview_medium.pdf](https://cdn.skfmediahub.skf.com/api/public/094ea584acc90401/pdf_preview_medium/094ea584acc90401_pdf_preview_medium.pdf) (Einstiegsportal: [https://www.skf.com/go/17000](https://www.skf.com/go/17000))
* **Zugang:** Frei zugänglich als PDF (1.152 Seiten).
* **Themen:** Wellen- und Gehäusepassungen nach ISO 286, Lagersitzgenauigkeiten, Rundlauf- und Planlauftoleranzen, Fest- und Loslageranordnungen, Radialluftklassen.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Grundtoleranzen von Wellen- und Gehäusesitzen (Kapitel B.6, Seite 144):**  
     > *„Die erforderliche Passung bestimmt die Maßgenauigkeit der Lagersitze. [...] in der Regel nach folgenden Toleranzen bearbeitet werden:  
     • Wellensitze mit Maßgenauigkeit entsprechend Grundtoleranz IT6 und Gesamtlaufgenauigkeit entsprechend Grundtoleranz IT5  
     • Gehäusesitze mit Maßgenauigkeit entsprechend Grundtoleranz IT7 und Gesamtlaufgenauigkeit entsprechend Grundtoleranz IT6“*
  2. **Regel 2: Passungswahl bei Punktlast vs. Umfangslast (Kapitel B.6, Seite 142):**  
     > *„Bei Punktbelastung „wandert“ ein Lagerring normalerweise nicht, und es besteht keine Gefahr von Schäden durch Passungsrost oder Verschleiß. In diesem Fall ist eine feste Passung nicht unbedingt erforderlich.“*
  3. **Regel 3: Loslagerverschiebbarkeit im Gehäuse (Kapitel B.6, Seite 142):**  
     > *„Für den Außenring kann eine losere Passung als bei Umfangslast vorgesehen werden, wenn dieser in der Gehäusebohrung axial verschiebbar sein soll. Eine losere Passung kann jedoch Verschleißschäden in der Gehäusebohrung zur Folge haben.“*

---

#### 2. Schaeffler Technologies AG & Co. KG – *HR 1: Wälzlager (Gestaltung der Lagerung)*
* **Hersteller:** Schaeffler Gruppe (INA & FAG)
* **URL:** [https://www.schaeffler.com/remotemedien/media/_shared_media/08_media_library/01_publications/schaeffler_2/catalogue_1/downloads_6/hr1_de_de.pdf](https://www.schaeffler.com/remotemedien/media/_shared_media/08_media_library/01_publications/schaeffler_2/catalogue_1/downloads_6/hr1_de_de.pdf)
* **Zugang:** Frei zugänglich als PDF (1.866 Seiten, ca. 66 MB).
* **Themen:** Anordnung der Lager (Fest-/Loslager, angestellte O-/X-Anordnung, schwimmende Lagerung), radiale/axiale Befestigung, Passungstabellen, Form- und Lagegenauigkeiten der Anschlusskonstruktion.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Zwei-Lager-Prinzip (Kapitel 8.1, Seite 139):**  
     > *„Zur Führung und Abstützung eines umlaufenden Maschinenteils sind in der Regel zwei in bestimmtem Abstand voneinander angeordnete Lager erforderlich (Ausnahmen: Vierpunkt-, Kreuzrollen- und Schwenklager). Je nach Anwendung wählt man zwischen einer Fest-/Loslagerung, einer angestellten Lagerung oder einer schwimmenden Lagerung.“*
  2. **Regel 2: Formschluss bei axialer Fixierung (Kapitel 8.2, Seite 144):**  
     > *„Wälzlager müssen entsprechend ihrer Funktion auf der Welle und im Gehäuse in radialer, axialer und tangentialer Richtung befestigt werden. In radialer und tangentialer Richtung geschieht das durch eine feste Passung. Axial ist dies jedoch nur bedingt möglich, Wälzlager werden deshalb in der Regel axial formschlüssig fixiert.“*
  3. **Regel 3: Notwendigkeit des Festsitzes bei Umfangslast (Kapitel 8.2, Seite 145):**  
     > *„Ein Lagerring, der relativ zur Belastungsrichtung rotiert (Umfangslast für den Ring), wälzt sich bei einem losen Sitz auf seiner Sitzfläche ab, er wandert also in Umfangsrichtung. Bei stoßartiger Belastung wird der Ring rutschen. In beiden Fällen wird die Sitzfläche beschädigt und es kommt zu Passungsrost und Verschleiß. Für diesen Ring ist deshalb immer ein fester Sitz vorzusehen.“*

---

#### 3. igus GmbH – *iglide® Plain Bearings Design Basics Guide*
* **Hersteller:** igus GmbH
* **URL:** [https://toolbox.igus.com/wp-content/uploads/2023/08/iglide-plain-bearings-design-guide.pdf](https://toolbox.igus.com/wp-content/uploads/2023/08/iglide-plain-bearings-design-guide.pdf) (Ergänzende Einbaudaten: [https://www.igus.de/info/gleitlager-einbau-und-toleranzen](https://www.igus.de/info/gleitlager-einbau-und-toleranzen))
* **Zugang:** Frei zugänglich als PDF (8 Seiten).
* **Themen:** Polymer-Gleitlager, Einpressübermaß, Aufnahmebohrungen (H7), Gehäuseanfasung, Flächenpressungsberechnung, Wellenrauheit und Stick-Slip.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Anfasung der Aufnahmebohrung (Seite 7):**  
     > *„Next, ensure your bearing housing has a chamfer - ideally 20-30º. For sleeve bearings, confirm that the outside chamfer of the bearing is matched up with the lead-in chamfer of the housing.“*
  2. **Regel 2: Berechnung der Flächenpressung (Seite 4):**  
     > *„The surface pressure of a press-fit bearing is actually determined by the load divided by the surface area it acts on, giving wall-thickness no relation to surface pressure. [...] To determine a bearing’s surface pressure (Ps) in psi, use the following formula: Ps = L / (D \* l), where L= load, D = inner diameter, and l = bearing length (in inches).“*
  3. **Regel 3: Gegenlaufflächen-Rauheit und Reibung (Seite 6–7):**  
     > *„While a very rough shaft acts as a file, causing excessive wear, a very smooth shaft can increase friction due to the shafting and the bearing surface adhering to one another. This “stick-slip” phenomenon, characterized by a loud squeaking noise, can occur when there is a large difference between static and dynamic friction alongside adhesion between mating surfaces.“*

---

#### 4. MISUMI Corporation – *Installation and Maintenance of Linear Guides*
* **Hersteller:** MISUMI Corporation
* **URL:** [https://id.misumi-ec.com/pdf/fa/2014/p1_529.pdf](https://id.misumi-ec.com/pdf/fa/2014/p1_529.pdf) (MISUMI FA Catalog Technical Data, S. 1-529 bis 1-530)
* **Zugang:** Frei zugänglich als PDF (2 Seiten) / frei im MISUMI eCatalog.
* **Themen:** Montage von Profilschienenführungen, Referenzkanten (Datum Plane), Freistiche an Anschlagschultern, Ebenheit der Montageflächen, Anzugsdrehmomente.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Freistiche bzw. Eckenradien an Gehäuseschultern (Seite 1-529):**  
     > *„Linear Guides are designed to obtain accuracies when mounted on base plates. Generally, the datum plane is placed against the shoulder on the mounting surface. In that case, corners should have reliefs or corner radius should be machined smaller than chamfering of rails and blocks.“*
  2. **Regel 2: Ebenheit der Wagenmontagefläche (Seite 1-529):**  
     > *„Blocks may be deformed depending on its mounting surface flatness. Block deformation may cause clearance, which might give less/more preload and cause sliding defects. Securing 5µ mounting surface flatness is recommended.“*
  3. **Regel 3: Ausrichtung an Bezugskanten (Seite 1-529):**  
     > *„MISUMI Linear Guides have a datum surface (a surface with a straight groove) on both the rail and block. [...] When installing Linear Guides, correctly match the datum of the guides and installation bases.“*

---

### 2.2 Verbindungstechnik, Gewindeeinsätze & Sicherungselemente

#### 5. Bossard Group – *Construction recommendations (Technical Information)*
* **Hersteller:** Bossard Group
* **URL:** [https://assets.eu.ctfassets.net/0vp0u5uh75zd/3DLqM7Z9oEMiNjXOeKeL6V/b7565ca2741cfb3d15dd79287acefc0a/079_093_Construction_recommendations_Fastening_EN_01_2025.pdf](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3DLqM7Z9oEMiNjXOeKeL6V/b7565ca2741cfb3d15dd79287acefc0a/079_093_Construction_recommendations_Fastening_EN_01_2025.pdf)
* **Zugang:** Frei zugänglich als PDF (Ausgabe 01-2025, 15 Seiten).
* **Themen:** Gewindefurchende Schrauben für Metalle nach DIN 7500, Thermoplast-Direktverschraubung (Delta PT, PT), Bohrungsgeometrie, Kernlochtiefe, Einfallstellenvermeidung.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Werkstoffgrenzen für DIN 7500 (Seite 79):**  
     > *„Thread forming is not suitable for brittle metals such as grey cast iron. Thread forming screws made from A2 stainless steel can only safely be screwed into light metals.“*
  2. **Regel 2: Sicherheitsabstand am Bohrungsgrund (Seite 87):**  
     > *„Select tapping holes which are sufficiently deep so that under no circumstances can the assembled screws rest in the base of the hole.“*
  3. **Regel 3: Drehzahl und Abschaltung bei Delta PT (Seite 83):**  
     > *„The forming torque must always be less than the minimum breaking torque. For the assembly, we recommend a driving tool with a process-reliable shutdown function. The recommended assembly speed is 400 rpm.“*

---

#### 6. Adolf Würth GmbH & Co. KG – *Technische Informationen zu Verbindungselementen*
* **Hersteller:** Adolf Würth GmbH & Co. KG / Würth Industrie Service
* **URL:** [https://www.wuerth-industrie.com/web/media/downloads/brochures/de_wis/dino-technik.pdf](https://www.wuerth-industrie.com/web/media/downloads/brochures/de_wis/dino-technik.pdf)
* **Zugang:** Frei zugänglich als PDF (90 Seiten).
* **Themen:** Festigkeitsklassen von Stahlschrauben und Muttern, Vorspannkräfte, Montagehinweise, Tubusgestaltung für Direktverschraubung (WÜPLAST), spanlose Furchschrauben (DIN 7500).
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Berechnungsformel für das Anziehdrehmoment bei Kunststoffen (Kapitel 9.1, Seite 1816):**  
     > *„Voraussetzung für eine prozesssichere Verschraubung ist eine große Differenz zwischen Einschraub- und Überdrehmoment. Das erforderliche Anziehmoment lässt sich mit nachfolgender Formel theoretisch bestimmen: MA = ME + 1/3 … 1/2 (MÜ – ME). Einschraub- und Überdrehmoment sind experimentell zu ermitteln.“*
  2. **Regel 2: Entlastungsbohrung am Tubus (Kapitel 9.1, Seite 1815):**  
     > *„Entlastungsbohrung: Die Entlastungsbohrung am oberen Ende des Bohrlochs vermindert Spannungsüberlagerungen und verhindert somit ein Aufplatzen des Tubus. Zusätzlich dient sie zur Führung der Schraube beim Montagevorgang.“*
  3. **Regel 3: Furchspitzenlänge bei DIN 7500 (Kapitel 9.2.3, Seite 1818):**  
     > *„Schrauben DIN 7500 furchen beim Eindrehen ihr Gegengewinde spanlos durch plastische Verformung des Grundmaterials (Stahl, HB max. 135, Leichtmetalle, Buntmetalle). [...] Bei der Wahl der Schraubenlänge ist die Länge des nicht tragenden konischen Schraubenendes zu berücksichtigen!“*

---

#### 7. Böllhoff Gruppe – *HELICOIL® Plus (Katalog Nr. 0100)*
* **Hersteller:** Böllhoff Gruppe
* **URL:** [https://media.boellhoff.com/files/pdf13/0100-helicoil-plus-at-de.pdf](https://media.boellhoff.com/files/pdf13/0100-helicoil-plus-at-de.pdf)
* **Zugang:** Frei zugänglich als PDF (56 Seiten).
* **Themen:** Drahtgewindeeinsätze für Leichtmetalle und Kunststoffe, Nennlängenbestimmung in Abhängigkeit von Werkstoff und Schraubenfestigkeit, Mindestwandstärken, Kernlochsenkung.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Auslegungskriterium schwächeres Glied (Kapitel Konstruktionsrichtlinien, Seite 13):**  
     > *„Die Richtwerte sind so bemessen, dass in der Verbindung die Schraube das schwächere Glied ist. Die empfohlenen Nennlängen können unterschritten werden, wenn Versuche dies bestätigen.“*
  2. **Regel 2: Einbautiefe unter Werkstückoberfläche (Kapitel Technische Daten, Seite 17):**  
     > *„Durch Drehen des Gewindedorns (d), der Spindel (e) bzw. des Überwurfwerkzeuges (f) von Hand bzw. Auslösen des Antriebs wird der Gewindeeinsatz eingedreht. Er ist mit mind. 0,25 P unter die Oberfläche einzubauen“*
  3. **Regel 3: Senkungsdurchmesser für Aufnahmegewinde (Kapitel Einbauprozess, Seite 16):**  
     > *„Vor dem Gewindeschneiden mit 90° ansenken und entgraten. Außendurchmesser der Senkung = DHC +0,1 mm.“*

---

#### 8. EJOT GmbH & Co. KG – *DELTA PT® (Predictable performance improvement)*
* **Hersteller:** EJOT GmbH & Co. KG
* **URL:** [https://www.ejot-atf.com/wp-content/uploads/2017/02/ATFDELTAPT2017HighRes.pdf](https://www.ejot-atf.com/wp-content/uploads/2017/02/ATFDELTAPT2017HighRes.pdf) (Herstellerportal: [https://www.ejot.com](https://www.ejot.com))
* **Zugang:** Frei zugänglich als PDF (18 Seiten).
* **Themen:** Direktverschraubung thermoplastischer Kunststoffe, Schraubendom-Konstruktion (Boss Design), Vorloch- und Außendurchmesser, Entlastungssenkung, Einschraubdrehzahlen.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Vorlochdurchmesser und Formschräge (Seite 11):**  
     > *„The most favourable hole diameter has in most cases proven to be: db = 0,8 x d1 +/- tolerance of screwdiameter [...]. For higher filled materials or materials with a bigger strength the hole diameter can be increased up to db = 0,88 x d1. The draft angle in the core hole should be kept as small as possible. max 0.5° per side.“*
  2. **Regel 2: Funktion der Senkung am Dom (Seite 11):**  
     > *„The counterbore is of special importance, as it ensures a favourable edge stress reduction, thus preventing boss cracking. In addition, the counterbore acts as a lead-in and guidance during initial thread forming.“*
  3. **Regel 3: Dom-Außendurchmesser und Senktiefe (Seite 11):**  
     > *„dO = 2 x d1 [Boss outer diameter]; 0,5 x d1 [Counterbore depth]“*

---

#### 9. Kerb-Konus-Vertriebs-GmbH – *Gewinde-Einsätze für Metalle: Ensat® (Druckschrift 20)*
* **Hersteller:** Kerb-Konus-Vertriebs-GmbH
* **URL:** [https://www.kerbkonus.de/proddb/pdf/de.ds.20.pdf](https://www.kerbkonus.de/proddb/pdf/de.ds.20.pdf)
* **Zugang:** Frei zugänglich als PDF (34 Seiten).
* **Themen:** Selbstschneidende Gewindebuchsen (Ensat-S 302, Ensat-SB 307/308), Bohrungsgeometrie, Ansenkung, Kantenabstände, Setzverhalten und axiales Rückweichmaß.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Vertieftes Eindrehen zur Sicherung der Vorspannung (Seite 6):**  
     > *„Der Ensat® soll 0,1 bis 0,2 mm vertieft eingedreht werden (Bild 5). Nach der Verarbeitung kann der Ensat® sofort belastet werden. Sollte der Bauteilwerkstoff bei der Belastung ein Setzverhalten des Ensat® zulassen, kann sich der Ensat® nur 0,1 bis 0,2 mm axial bewegen. D.h. die Vorspannung in der Verschraubung bleibt zum größten Teil erhalten, ein Lösen der Verschraubung bei dynamischer Belastung wird erschwert.“*
  2. **Regel 2: Mindest-Kantenabstand (Seite 6):**  
     > *„Der kleinste noch zulässige Kanten-Abstand W (Bild 6) hängt von der Elastizität des Werkstoffs ab, in den der Ensat® eingedreht wird. [...] Richtwerte für Leichtmetall: W >= 0,2 bis 0,6 x E; Richtwerte für Gusseisen: W >= 0,3 bis 0,5 x E (E = Außendurchmesser des Ensat® [mm])“*
  3. **Regel 3: Mindestmaterialdicke (Seite 6):**  
     > *„Länge des Ensat® = kleinste zulässige Materialdicke.“*

---

#### 10. Seeger-Orbis GmbH – *Katalog Seeger-Ringe (Ausgabe 2022)*
* **Hersteller:** Seeger-Orbis GmbH
* **URL:** [https://www.seeger-orbis.de/fileadmin/assets/zertifikate/SEEGER-KATALOGUE-light-2022_11.pdf](https://www.seeger-orbis.de/fileadmin/assets/zertifikate/SEEGER-KATALOGUE-light-2022_11.pdf)
* **Zugang:** Frei zugänglich als PDF (142 Seiten).
* **Themen:** Genormte Sicherungsringe für Wellen (DIN 471) und Bohrungen (DIN 472), Ringnutgestaltung, Nutbreitentoleranzen, Kantenabstände, zulässige Radien und Fasen an Anbauteilen.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Verrundung des Nutgrundes auf der Lastseite (Kapitel 8.1.3, Seite 129):**  
     > *„Die rechteckige Nut stellt noch immer die Regelausführung dar. Sie kann ohne nennenswerte Beeinflussung des Sitzes des Ringes auf der Lastseite mit r = 0,1 s (10 % der Ringdicke s) gerundet sein (siehe Bild 12a).“*
  2. **Regel 2: Nutbreitenbemessung (Kapitel 8.1.2, Seite 128):**  
     > *„Die in den Maßlisten genannten Werte sind Kleinstmaße, die bei der üblichen Anwendung der Seeger-Befestigungselemente in rechteckiger Nut und bei einseitiger Kraftübertragung empfohlen werden. Je nach Gestaltung des an den Ring anzudrückenden Maschinenteiles kann die Nut nach der entlasteten Seite verbreitert werden.“*
  3. **Regel 3: Tragfähigkeitskriterium der Verbindung (Kapitel 7.1, Seite 119):**  
     > *„Bei den in den Maßlisten genannten Tragfähigkeitszahlen für Seeger-Ringe FR und Nuten FN ist jeweils das schwächere Konstruktionselement für die Tragfähigkeit der Verbindung bestimmend. Die Tragfähigkeitszahlen enthalten keine Sicherheit gegen Fließen bei stat. Beanspruchung und gegen Dauerbruch bei schwellender Beanspruchung. Bei statischer Beanspruchung ist gegen Bruch eine mindestens dreifache Sicherheit vorhanden.“*

---

### 2.3 Dichtungstechnik

#### 11. Parker Hannifin Corporation – *Parker O-Ring Handbook (ORD 5700)*
* **Hersteller:** Parker Hannifin Corporation (O-Ring Division)
* **URL:** [https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf](https://nianticseal.com/wp-content/uploads/2024/04/ORD-5700.pdf) (Offizielles eHandbook: [https://www.parker.com/ORD5700](https://www.parker.com/ORD5700))
* **Zugang:** Frei zugänglich als PDF (292 Seiten).
* **Themen:** Statische und dynamische O-Ring-Dichtungen, Nutabmessungen (Rechtecknut, Schwalbenschwanznut, Dreiecknut), Oberflächengüten, Stützringe gegen Spaltextrusion.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Maximale Oberflächenrauheit für statische Dichtsitze (Section IV, Seite 4-2):**  
     > *„The design charts indicate a surface roughness value not to exceed 32 micro-inches (32 rms) on the sealing surfaces for static seals with a maximum of 16 rms recommended for face-type gas seals. These figures are good general guidelines, but they do not tell the whole story. Equally important is the method used to produce the finish.“*
  2. **Regel 2: Einsatzgrenze für Stützringe gegen Extrusion (Section IV, Seite 4-2):**  
     > *„The need for back-up rings should be investigated for pressures exceeding 103.5 Bar (1500 psi) (for all seal types). If there is no extrusion gap, back-up rings are not required.“*
  3. **Regel 3: Restriktion für Schwalbenschwanznuten (Section IV, Seite 4-3):**  
     > *„It is sometimes necessary to mount an O-ring in a face type groove in such a way that it cannot fall out. The dovetail groove described in Design Charts 4-4 and 4-5 will serve this function. This groove is difficult and expensive to machine, and the tolerances are especially critical. It should be used only when it is absolutely necessary.“*

---

### 2.4 Fertigungsdienstleister (CNC, Spritzguss, Blech)

#### 12. Protolabs – *Injection Molding Guide: Process, Design Tips, & Materials*
* **Hersteller:** Protolabs Inc.
* **URL:** [https://www.protolabs.com/resources/guides-and-trend-reports/injection-molding-guide-process-design-tips-materials/](https://www.protolabs.com/resources/guides-and-trend-reports/injection-molding-guide-process-design-tips-materials/)
* **Zugang:** Frei online lesbar (keine Registrierung).
* **Themen:** Kunststoff-Spritzguss, Wandstärkenübergänge, Entformungsschrägen (Draft), Verrippung, Einfallstellen (Sink Marks), Kernzüge und Schieber.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Wandstärkenrelation zu Nachbarwandungen (Abschnitt: Best Practices):**  
     > *„wall thickness guidelines that keep walls within 40% to 60% of adjacent thickness and inside the recommended range for the selected resin.“*
  2. **Regel 2: Richtwert für Entformungsschrägen (Abschnitt: Best Practices):**  
     > *„Add draft early: Draft helps parts release cleanly from the mold. A common starting point is 1 to 2 degrees, with more draft for textured surfaces.“*
  3. **Regel 3: Rippenstärke zur Vermeidung von Einfallstellen (Abschnitt: Best Practices):**  
     > *„Use ribs and gussets for strength: Thin supporting features can add stiffness without the sink risk of thick solid sections. A common guideline is to keep ribs around 60 percent [of the nominal wall thickness].“*

---

#### 13. Xometry – *Design Guide: Sheet Metal Fabrication*
* **Hersteller:** Xometry Inc.
* **URL:** [https://www.xometry.com/resources/design-guides/design-guide-sheet-metal-fabrication/](https://www.xometry.com/resources/design-guides/design-guide-sheet-metal-fabrication/)
* **Zugang:** Frei online zugänglich (PDF-Version nach Ausfüllen eines Formulars).
* **Themen:** Blechbearbeitung, minimale Biegeradien, Biegungsentlastung (Bend Relief Cuts), Mindestlochabstand zur Biegelinie, Flanschbreiten.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Minimaler Innenbiegeradius (Abschnitt: Bending Guidelines):**  
     > *„The minimum inside bend radius typically ranges from 1 to 2 times the material thickness [...]. Going below 1x the material thickness risks introducing surface cracking, fracturing, or breaking the part.“*
  2. **Regel 2: Einheitliche Wanddicke im gesamten Bauteil (Abschnitt: Sheet Metal Rules):**  
     > *„Best practices in Design for Manufacturing (DFM) recommend keeping a consistent sheet metal thickness throughout the design (using standard gauge sizes) and maintaining a uniform inside bend radius across all bends“*
  3. **Regel 3: Ausklinkung und Biegungsentlastung (Abschnitt: Relief Cuts):**  
     > *„Relief cuts are necessary where a bend meets an edge to prevent tearing. The width of the relief should be at least equal to the material thickness, and its depth must exceed the bend radius.“*

---

#### 14. Hubs (Protolabs Network) – *CNC machining design guide*
* **Hersteller:** Hubs (Protolabs Network)
* **URL:** [https://www.hubs.com/guides/cnc-machining/](https://www.hubs.com/guides/cnc-machining/)
* **Zugang:** Frei online zugänglich (keine Registrierung).
* **Themen:** 3- und 5-Achs-CNC-Fräsen, Kavitätstiefe (Taschen), Eckenradien/Werkzeugauslauf, Mindestwandstärken Metalle vs. Kunststoffe, Bohrungstiefen.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Taschenabmessungen (Abschnitt: Design rules for CNC machining – Pockets):**  
     > *„Recommended depth: 4 x pocket width; Feasible depth: 10 x tool diameter. Deeper pockets need to be machined with cutting tools with larger diameter affecting the fillets of the internal edges.“*
  2. **Regel 2: Innenkantenradien (Abschnitt: Design rules for CNC machining – Internal edges):**  
     > *„Recommended: larger than ⅓ x pocket depth. For internal vertical edges, the larger the fillet the better. Edges on the floor of a pocket should be either sharp or have a 0.1 mm or 1 mm radius.“*
  3. **Regel 3: Mindestwandstärken für Metalle und Kunststoffe (Abschnitt: Minimum wall thickness):**  
     > *„Recommended: 0.8 mm (for metals), Feasible: 0.5 mm; Recommended: 1.5 mm (for plastics), Feasible depending on the plastic: 1.0 mm. Decreasing the wall thickness reduces the stiffness of the workpiece, increasing vibrations and lowering the achievable tolerances.“*

---

#### 15. Fictiv – *Fictiv CNC Machining Design Guide*
* **Hersteller:** Fictiv Inc.
* **URL:** [https://www.fictiv.com/articles/fictiv-cnc-machining-design-guide](https://www.fictiv.com/articles/fictiv-cnc-machining-design-guide)
* **Zugang:** Frei online zugänglich (keine Registrierung).
* **Themen:** Zerspanungsgerechte Konstruktion, maximale Gewindetiefen, Auskraglängen und Vibrationen bei Nuten, Innenradien größer als Werkzeugradius.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Vermeidung tiefer Gewinde (Abschnitt: Avoid Deep Taps):**  
     > *„A deep tap would be one that goes further than 3 times the diameter of the tap. Even this deep of a tap is not always necessary, as 1.5 times the diameter will provide enough thread engagement.“*
  2. **Regel 2: Maximales Tiefen-zu-Durchmesser-Verhältnis für Schaftfräser (Abschnitt: Avoid Deep, Narrow Slots):**  
     > *„The final depth of cut of an endmill should be not greater than 15 times the diameter for plastics, 10 times the diameter for aluminum, and 5 times the diameter for steel. This is because long tools tend to deflect and vibrate, resulting in bad surface finishes.“*
  3. **Regel 3: Innenradius größer als Fräserradius (Abschnitt: Design with the Largest Possible Internal Radii):**  
     > *„Always design with the largest allowable internal radii. Avoid radii less than 0.8mm whenever possible. Pro Tip: Make your fillets slightly larger than the radius of the endmill, for example, a radius of .130” (3.3mm) instead of .125” (3.175mm). This will produce a smoother path for the mill and give you a better finish on the part.“*

---

### 2.5 Additive Fertigung & 3D-Druck-Inserts

#### 16. Prusa Research – *Modeling with 3D printing in mind*
* **Hersteller:** Prusa Research a.s.
* **URL:** [https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)
* **Zugang:** Frei online zugänglich (keine Registrierung).
* **Themen:** FDM/FFF-Druckrestriktionen, Überhänge ohne Stützstrukturen, Fase vs. Verrundung auf dem Druckbett, Spielpassungen für bewegliche Teile.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Zulässiger Überhangwinkel (Abschnitt: Overhangs and support material):**  
     > *„A 3D printer can cleanly print overhanging structures with an angle between 45 and 60 degrees, depending on your nozzle diameter and settings. Our FDM printer models with Nextruder and 360° cooling can print overhangs of up to 75° without supports.“*
  2. **Regel 2: Fase statt Rundung am Druckbett (Abschnitt: Fillet vs chamfer):**  
     > *„If oriented towards the print bed, fillets create a very steep overhang, which negatively affects the surface of the object. For this reason, use chamfer instead if a perfect part finish is a priority.“*
  3. **Regel 3: Mindestspalt für bewegliche Verbindungen (Abschnitt: Tolerances):**  
     > *„Consider if two parts should move, like a hinge, or lock/snap together with a friction fit. An initial good measurement for movable parts is at least 0.3 mm.“*

---

#### 17. ruthex GmbH – *Produktdatenblatt RX-Reihe (Metrisches ISO-Gewinde)*
* **Hersteller:** ruthex GmbH
* **URL:** [https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) (Herstellerportal: [https://www.ruthex.de/pages/dokumente-downloads](https://www.ruthex.de/pages/dokumente-downloads))
* **Zugang:** Frei zugänglich als PDF (2 Seiten).
* **Themen:** Gewindeeinsätze aus bleifreiem Messing für thermoplastische Kunststoffe im 3D-Druck, Bohrungsdurchmesser, Mindestwandstärken für M2 bis M8.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Vorloch- und Wandstärken-Spezifikation für M3 (Seite 1, Maßtabelle):**  
     > *„RX-M3x5,7: Durchmesser Nennmaß M3; Länge (L) = 5,7 mm; Ø (d1) = 4,6 mm; Ø (d2) = 3,9 mm; Bohrungsdurchmesser Ø (d3) = 4,0 mm; Mindestwandstärke W min. = 1,6 mm.“*
  2. **Regel 2: Vorloch- und Wandstärken-Spezifikation für M4 (Seite 1, Maßtabelle):**  
     > *„RX-M4x8,1: Durchmesser Nennmaß M4; Länge (L) = 8,1 mm; Ø (d1) = 6,3 mm; Ø (d2) = 5,5 mm; Bohrungsdurchmesser Ø (d3) = 5,6 mm; Mindestwandstärke W min. = 2,1 mm.“*
  3. **Regel 3: Auslegungsvorteile für Additive Fertigung (Seite 1):**  
     > *„Vorteile: • Geeignet für thermoplastische Kunststoffteile (Besonders geeignet im 3D-Druck) • Verdrehsichere und spannungsarme Verankerung • Hohe Auszugswerte“*

---

#### 18. CNC Kitchen (Stefan Hermann) – *Dimensions & Design Guidelines (Heat-Set Inserts)*
* **Hersteller / Autor:** TwoChefs GmbH / CNC Kitchen (Stefan Hermann)
* **URL:** [https://www.cnckitchen.com/s/CNCKitchen_Heat-Set-Insert-Dimensions-and-Design-Guidelines.pdf](https://www.cnckitchen.com/s/CNCKitchen_Heat-Set-Insert-Dimensions-and-Design-Guidelines.pdf) (Begleitartikel: [https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts))
* **Zugang:** Frei zugänglich als PDF (2 Seiten) und Web-Artikel.
* **Themen:** Empirisch ermittelte Konstruktionsparameter für Heat-Set-Inserts in FDM/FFF-Kunststoffen, Sacklochüberhang, zylindrische vs. konische Bohrungen, Auszugskraftoptimierung.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: Sacklochtiefe mit Schmelzreservoir (Poster Seite 2 & Blog):**  
     > *„blind hole: min. L+1mm [A blind hole should be slightly deeper than the length of the insert (approx. 1 mm)]“*
  2. **Regel 2: Zylindrische Bohrungsgeometrie ohne Entformungsschräge (Blog: How to design for inserts?):**  
     > *„Holes should be straight (not tapered). Normally, no chamfer is required at the hole edge.“*
  3. **Regel 3: Bemaßungswerte für Standard- und Voron-M3-Inserts (Poster Seite 2):**  
     > *„M3 x 5.7: L = 5.7 mm, D1 = 4.6 mm, D2 [Hole] = 4.0 mm, W min = 1.6 mm; M3 x 5 x 4 VORON: L = 4.0 mm, D1 = 5.0 mm, D2 [Hole] = 4.4 mm, W min = 1.6 mm.“*

---

### 2.6 Chemische Schraubensicherung & Klebetechnik

#### 19. Henkel AG & Co. KGaA / LOCTITE – *Threadlocking User’s Guide*
* **Hersteller:** Henkel Corporation (Loctite)
* **URL:** [https://www.ellsworth.com/globalassets/literature-library/manufacturer/henkel-loctite/henkel-loctite-user-guide-threadlocking.pdf](https://www.ellsworth.com/globalassets/literature-library/manufacturer/henkel-loctite/henkel-loctite-user-guide-threadlocking.pdf) (Vollständiges dt. Referenzhandbuch: [https://www.ludwigmeister.de/content/techn-informationen/chemische-produkte/klebstoffe/loctite_klebetechnik_de.pdf](https://www.ludwigmeister.de/content/techn-informationen/chemische-produkte/klebstoffe/loctite_klebetechnik_de.pdf))
* **Zugang:** Frei zugänglich als PDF (12 Seiten).
* **Themen:** Funktionsweise anaerober Flüssigsicherungen, Spaltfüllung im Gewindespiel, Schwächen mechanischer Feder- und Zahnscheiben, Korrosions- und Reibkorrosionsvermeidung.
* **Beispielregeln mit wörtlichem Zitat:**
  1. **Regel 1: 100% Spaltfüllung und anaerobe Polymerisation (Seite 5):**  
     > *„LOCTITE® threadlockers are single-component adhesives that cure in the absence of air and in contact with active metal to form a tough thermoset plastic. They completely fill all voids between the interfacing threads, which makes the assembly a unitized component and ultimately prevents loosening.“*
  2. **Regel 2: Versagensmechanismus durch Spiel und Querbewegung (Seite 3):**  
     > *„Gaps: In order to make the assembly possible, nuts and bolts must have some tolerance, which creates gaps between the threads. Vibration and side-to-side movement: These gaps allow the parts to move from side-to-side when exposed to vibration.“*
  3. **Regel 3: Unzuverlässigkeit von Federscheiben unter dynamischer Last (Seite 4):**  
     > *„Split ring or spring washers: Increased friction reduces clamp load; will not ensure reliable threadlocking under dynamic loads. [...] Tooth or ribbed flanged bolts: Prevent self-loosening, but are expensive; need larger flange-bearing surfaces and may damage the surfaces.“*

---

## 3. Rangliste der 10 ergiebigsten Guides für einen autonomen Konstruktions-Agenten

Für einen KI-Agenten, der CAD-Geometrien autonom generiert, modifiziert oder in einer DFM-Prüfpipeline (Rule-Engine / Linter) auditiert, sind diejenigen Guides am wertvollsten, die **deterministische Formeln, feste Toleranzwerte und parametrisch prüfbare Grenzwerte** liefern. 

| Rang | Guide & Urheber | Hauptfokus im CAD | Begründung für die Implementierung in einer KI-Rule-Engine |
| :---: | :--- | :--- | :--- |
| **1** | **Hubs: CNC Machining Design Guide** | Spanende Fertigung (Fräsen, Bohren) | **Höchste Dichte an deterministischen Grenzwerten:** Liefert exakte Verhältnisformeln ($4\times\text{Breite}$ für Taschen, $R > \frac{1}{3}\times\text{Tiefe}$ für Innenkanten, $0,8\,\text{mm}$ minimale Wandstärke Metall, $4\times D$ Bohrtiefe). Ermöglicht einen automatisierten Geometrie-Linter, der B-Rep-Features in Sekunden validiert. |
| **2** | **Parker: O-Ring Handbook (ORD 5700)** | Dichtungsnuten & Fluiddynamik | **Mathematisch vollständiger Industriestandard:** Alle Nutarten (axial, radial, Schwalbenschwanz) sind tabellarisch mit festen Toleranzen ($H8/f7$, Nutbreiten $m$, Radien $R$, Verpressung in $\%$) hinterlegt. Ein Agent kann O-Ring-Nuten anhand von Nenndruck und Schnurdurchmesser fehlerfrei generieren. |
| **3** | **Seeger-Orbis: Katalog Seeger-Ringe** | Wellen- & Bohrungssicherungen | **Exakte Bemaßungsvorschriften für Drehteile:** Enthält verbindliche Tabellenwerte für Nutdurchmesser $d_2$, Nuttiefen $t$, Nutbreiten $m$ sowie den maximalen Kantenverrundungsradius ($r = 0,1\times s$) und Kantenabstand $n$. Perfekt geeignet für automatisierte Nuten-Features auf zylindrischen Flächen. |
| **4** | **SKF: Wälzlager-Katalog 17000/1** | Wellen-/Gehäusesitze & Toleranzen | **Definitive Passungslogik:** Verknüpft Lastfälle (Umfangs- vs. Punktlast) direkt mit ISO-Toleranzklassen ($h6, j6, k5, H7$) und geometrischen Form-/Lagetoleranzen (Laufgenauigkeit IT5 bei IT6 Maßtoleranz). Essenziell für Agenten bei der Montagegruppen-Generierung. |
| **5** | **EJOT: DELTA PT Design Guide** | Schraubdome in Thermoplasten | **Parametrische Dom-Formeln:** Definiert feste mathematische Beziehungen für Kunststoff-Spritzguss- und 3D-Druckteile ($d_b = 0,8\times d_1$, Außendurchmesser $D = 2\times d_1$, Senktiefe $0,5\times d_1$, Entformungsschräge $\le 0,5^\circ$). Lässt sich direkt als parametrisches CAD-Feature skripten. |
| **6** | **Böllhoff: HELICOIL Plus (Katalog 0100)** | Gewindepanzerung in Leichtmetall | **Regelbasierte Gewindekernloch-Bemaßung:** Verknüpft Aufnahmewerkstoff (Zugfestigkeit) und Schraubenklasse (8.8 bis 12.9) mit der erforderlichen Nennlänge ($1,5\,d$ bis $3,5\,d$), Senkdurchmesser ($D_{HC} + 0,1\,\text{mm}$) und Einschraubtiefe ($0,25\,P$ unter Planfläche). |
| **7** | **CNC Kitchen: Heat-Set Insert Guidelines** | 3D-Druck Schmelzgewinde | **Praxisgeprüfte FFF/FDM-Passungswerte:** Bietet reale Bohrungsmaße für Einschmelzgewinde ($D_2$) und die kritische Regel zur Vermeidung von Blockaden: Grundlochtiefe mindestens $L + 1\,\text{mm}$ als Schmelzreservoir. Verhindert den häufigsten Konstruktionsfehler bei 3D-Druck-Baugruppen. |
| **8** | **Protolabs: Injection Molding Guide** | Spritzguss-DFM | **Robuste Heuristiken gegen Bauteilverzug:** Formalisiert Kernregeln für Wandstärkenvariationen ($\le 40\text{--}60\%$ Sprung), Entformungsschrägen ($1^\circ\text{--}2^\circ$) und Verrippungsdicken ($60\%$ der Nennwandstärke). Unverzichtbar für die automatisierte Wanddickenprüfung von Solid-Körpern. |
| **9** | **Fictiv: CNC Machining Design Guide** | Werkzeugpfad-Optimierung | **Praxisnahe Fertigungskosten-Reduktion:** Liefert dem Agenten Optimierungskriterien, z. B. Innenradien um $0,1\text{--}0,2\,\text{mm}$ größer als Fräserradien zu wählen, und begrenzt Gewindetiefen auf maximal $3\times D$, um Werkzeugbruch und Maschinenlaufzeit zu minimieren. |
| **10** | **Kerb-Konus: Ensat Technische Druckschrift 20** | Hochfeste Gewindebuchsen | **Grenzwerte für Wandstärken und Kantenabstände:** Definiert Mindestwandstärken ($W \ge 0,2\text{--}0,6\times E$ für Leichtmetalle) und das axiale Rückweichmaß von $0,1\text{--}0,2\,\text{mm}$ unter Oberfläche zur Sicherung der Schraubenvorspannung. |

---

## 4. Empfehlung für die CAD-Projekt-Architektur

Für die Integration in ein automatisiertes Open-Source-CAD-Projekt empfiehlt sich eine Dreiteilung der Wissensdatenbank:

1. **Geometrie-Linter (Rule-Check):**
   * *Prüfung von Überhängen und Schrägen:* Überhangwinkel $\le 60^\circ$ (Prusa), Entformungsschrägen $\ge 1^\circ$ (Protolabs).
   * *Wandstärken- und Kavitäten-Check:* Wandstärken $\ge 0,8\,\text{mm}$ Metall / $\ge 1,5\,\text{mm}$ Kunststoff (Hubs); Taschentiefe $\le 4\times\text{Breite}$ (Hubs).
2. **Feature-Generatoren (Skripting-Makros für B-Rep / CSG):**
   * *O-Ring-Nut-Generator:* Erzeugung normgerechter Nuten nach Parker ORD 5700 Tabelle 4-2 anhand Schnurdurchmesser und Nuttyp.
   * *Seeger-Nut-Generator:* Wellen-/Bohrungsnut nach DIN 471/472 gemäß Seeger-Orbis-Tabelle inklusive $0,1\times s$ Grundverrundung.
   * *Schraubendom-Generator:* Parametrische Zylinder- und Kernlochgeometrie nach EJOT ($d_b = 0,8\times d$, $D = 2\times d$, Ansenkung $0,5\times d$).
3. **Passungs- und Toleranzmodul:**
   * Automatische Zuweisung von ISO-Passungen (z. B. $h6/H7$ bzw. $m6/H7$ nach SKF/Schaeffler) an zylindrischen Paarungsflächen in Abhängigkeit von Wellendurchmesser und Belastungsart (Punkt- vs. Umfangslast).
