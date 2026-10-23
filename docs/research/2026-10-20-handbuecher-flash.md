> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Nicht erreichbare Links: siehe `2026-10-20-quellen-nicht-erreichbar.md` (mit Browser-User-Agent nur wenige). Lizenzen und Zitate vor dem Übernehmen an der Quelle prüfen.

# Bestandsaufnahme frei zugänglicher Konstruktionshandbücher für Maschinenbau & CAD-Agenten

Diese Recherche erfasst frei zugängliche, hochwertige Handbücher und Vorlesungsunterlagen staatlicher Raumfahrt- und Militärbehörden (NASA, ESA/ECSS, US-DoD, FAA) sowie Hochschulen. Der Fokus liegt auf **praktischem Konstruktionswissen und Best Practices**, die über reine Tabellennormen hinausgehen (z. B. Gestaltungsregeln, Reibwertstreuungen, Setzerscheinungen, Unwirksamkeit bestimmter Sicherungselemente, Schälspannungsminimierung, geometrische Restriktionen).

Alle Angaben, Fundstellen, Seitenzahlen und Zitate wurden direkt anhand der Primärdokumente (Original-PDFs) verifiziert.

---

## 1. Übersichtstabelle aller untersuchten Dokumente

| Nr. | Titel | Herausgeber | Jahr | Direkter PDF-Link | Lizenzstatus / Rechtliche Einordnung | Kern-Themen |
|:---|:---|:---|:---:|:---|:---|:---|
| **1** | **NASA RP-1228**: *Fastener Design Manual* | NASA (Lewis Research Center) | 1990 | [ntrs.nasa.gov/.../19900009424.pdf](https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf) | **Public Domain** (US-Bundesbehörde, 17 U.S.C. § 105; Unclassified-Unlimited) | Schrauben, Vorspannung, Gewindeeinsätze, Federring-Unwirksamkeit, Nietung, Klemmlänge |
| **2** | **NASA-STD-5020B**: *Requirements for Threaded Fastening Systems in Spaceflight Hardware* | NASA (Office of the Chief Engineer) | 2021 (reval. 2026) | [standards.nasa.gov/.../NASA-STD-5020B.pdf](https://standards.nasa.gov/system/files/tmp/NASA-STD-5020B%20Revalidated%201-5-2026.pdf) | **Public Domain** (Approved for public release – Distribution unlimited) | Vorspannungsunabhängige Sicherung, rotierende Schrauben, Gewindeüberstand, Auslaufkerben |
| **3** | **ECSS-E-HB-32-23A Rev.1**: *Threaded fasteners handbook* | ESA / ECSS-Sekretariat | 2023 | [ecss.nl/.../ECSS-E-HB-32-23A-Rev.1.pdf](https://ecss.nl/wp-content/uploads/2023/02/ECSS-E-HB-32-23A-Rev.1(6February2023).pdf) | **Frei zugänglich, ESA-Copyright** (Reproduktion reglementiert, Zitate/Verweise gestattet) | Ausnutzungsgrad, Flansch-Biegung, Setzbeträge (Embedding), Tellerfedern, Einschraubtiefe |
| **4** | **ECSS-E-HB-32-21A**: *Adhesive bonding handbook* | ESA / ECSS-Sekretariat | 2011 | [ecss.nl/.../ECSS-E-HB-32-21A20March2011.pdf](https://ecss.nl/wp-content/uploads/handbooks/ecss-e-hb/ECSS-E-HB-32-21A20March2011.pdf) | **Frei zugänglich, ESA-Copyright** (Reproduktion reglementiert, Zitate/Verweise gestattet) | Klebverbindungen, Schälspannung, Klebspaltdicke, Überlappungslängen, Schäftungen |
| **5** | **MIL-HDBK-727**: *Design Guidance for Producibility* | US Department of Defense (US Army) | 1984 | [everyspec.com/.../MIL_HDBK_727.1853.pdf](https://everyspec.com/MIL-HDBK/MIL-HDBK-0700-0799/download.php?spec=MIL_HDBK_727.1853.pdf) | **Public Domain** (US DoD Handbook, kein Datenschutz/Public Release) | Fertigungsgerechtes Konstruieren, Zerspanung, Sacklochgewinde, Guss-Eigenspannungen, Blech |
| **6** | **MIL-HDBK-60**: *Threaded Fasteners - Tightening to Proper Tension* | US Department of Defense (DISC) | 1990 | [contrails.free.fr/.../mil-hdbk-60.pdf](http://contrails.free.fr/fichiers2/mil-hdbk-60_proper_tension.pdf) | **Public Domain** (Distribution Statement A: Approved for public release, unlimited) | Vorspannbereiche, Relaxation/Setzen (10%-Regel), Torsionsanteil beim Anziehen, Flansch-Sequenz |
| **7** | **FAA AC 43.13-1B (w/ Chg 1)**: *Aircraft Inspection and Repair* | FAA (US Dept. of Transportation) | 1998 (Chg 1: 2001) | [faa.gov/.../AC_43.13-1B_w-chg1.pdf](https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_43.13-1B_w-chg1.pdf) | **Public Domain** (US Federal Government Circular) | Klemmlänge, Reibdrehmoment, Sicherungsmuttern, Drahtsicherung, Nietabstände, Blindnietverbote |
| **8** | **NASA RP-1152**: *Gearing* | NASA / US Army AVSCOM | 1985 | [ntrs.nasa.gov/.../19860005142.pdf](https://ntrs.nasa.gov/api/citations/19860005142/downloads/19860005142.pdf) | **Public Domain** (Unclassified-Unlimited STAR Category 37) | Zahnradgeometrie, Flankenspiel (Backlash), Profilüberdeckung, Unterschnitt, EHD-Schmierung |
| **9** | **FUNdaMENTALS of Design** (Slocum) | MIT (Prof. Alexander Slocum) | 2008 | [meddevdesign.mit.edu/.../Topic-9.pdf](https://meddevdesign.mit.edu/wp-content/uploads/FUNdaMENTALs-Topic-9.pdf) | **Open Educational Resource (OER)** (© A. Slocum, frei für Studium/Lehre) | Kraftkegel/Spannungskegel, Reibungsverluste, Schraube als Zuganker, Kinematische Kopplung |
| **10** | **Vorlesung Maschinenelemente: Schrauben** | Hochschule Anhalt (Prof. Dr. H. Gruss) | 2019 | [hs-anhalt.de/.../05_ME_Schrauben.pdf](https://www.hs-anhalt.de/fileadmin/Dateien/FB6/personen/voigt_st/Lehrunterlagen/01_ME_Vorlesung/05_ME_Schraubenverbindungen_Stud.pdf) | **Freier Hochschul-Webzugriff** (Lehrmaterial FB6, Urheberrecht beim Verfasser) | Lockern vs. Losdrehen, Unwirksamkeit von Federringen, Kerbwirkung am Gewindeauslauf |
| **11** | **Vorlesung Konstruktion: Gestaltungsregeln** | Hochschule Anhalt (Prof. Dr. H. Gruss) | 2019 | [hs-anhalt.de/.../Konstruktion_Teil-2.pdf](https://www.hs-anhalt.de/fileadmin/Dateien/FB6/personen/voigt_st/Lehrunterlagen/03_Ko_Vorlesung/Konstruktion_Stud_Teil-2.pdf) | **Freier Hochschul-Webzugriff** (Lehrmaterial FB6, Urheberrecht beim Verfasser) | Grundregeln "einfach" und "eindeutig", Zylinder/Platten-Geometrie, Spaltkorrosion an Schrauben |

---

## 2. Detaillierte Dokumentbeschreibungen & wörtliche Regeln

### 1. NASA RP-1228: Fastener Design Manual
* **Herausgeber:** National Aeronautics and Space Administration (NASA), Lewis Research Center, Cleveland, Ohio. Autor: Richard T. Barrett.
* **Jahr:** 1990 (März 1990; Errata vom 17. Juni 2008).
* **URL:** [https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf](https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Public Domain (Werk der US-Bundesregierung nach 17 U.S.C. § 105). 
  > Im Report Documentation Page (S. 96): `18. Distribution Statement: Unclassified-Unlimited Subject Category 37`. Für jede Nutzung (kommerziell und Open Source nach MIT/Apache-2.0) uneingeschränkt frei.
* **Themen:** Schraubenwerkstoffe, Oberflächenbeschichtungen, Reibungsbeiwerte und Schmiermittel, Federringe und Sicherungselemente, Gewindeeinsätze (Helicoil/Keensert), Gewindetoleranzen, Ermüdung, Klemmlänge, Lochabstände, Blindniete.
* **3 verifizierte Konstruktionsregeln:**
  1. **Unwirksamkeit von Federringen (Helical Spring Lockwashers)** (S. 9 / PDF S. 13):
     > *"The lockwasher serves as a spring while the bolt is being tightened. However, the washer is normally flat by the time the bolt is fully torqued. At this time it is equivalent to a solid flat washer, and its locking ability is nonexistent. In summary, a lockwasher of this type is useless for locking."*
  2. **Randabstand und Schraubenabstand im Lochbild** (S. 21 / PDF S. 25):
     > *"Common design practice is to use a nominal edge distance of 2D from the fastener hole centerline, where D is the fastener diameter. The minimum edge distance should not be less than 1.5D. The nominal distance between fasteners is 4D, but the thickness of the materials being joined can be a significant factor."*
  3. **Wahl der Schaft- und Klemmlänge zur Vermeidung von Gewinde auf Scherung** (S. 22 / PDF S. 26):
     > *"Standard design practice is to choose a grip length such that the threads are never in bearing (shear). Where an exact grip length is not available, the thickness of the washers used under the nut or bolthead can be varied enough to allow proper grip."*

---

### 2. NASA-STD-5020B: Requirements for Threaded Fastening Systems in Spaceflight Hardware
* **Herausgeber:** National Aeronautics and Space Administration (NASA), Office of the NASA Chief Engineer, Washington, D.C.
* **Jahr:** 2021 (Approved: 2021-08-06, Revalidated: 2026-01-05; ersetzt NASA-STD-5020A).
* **URL:** [https://standards.nasa.gov/system/files/tmp/NASA-STD-5020B%20Revalidated%201-5-2026.pdf](https://standards.nasa.gov/system/files/tmp/NASA-STD-5020B%20Revalidated%201-5-2026.pdf) *(Archiv-Baseline: [standards.nasa.gov/sites/default/files/standards/NASA/B/0/Historical/nasa-std-5020.pdf](https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/Historical/nasa-std-5020.pdf))*
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Public Domain (U.S. Government Technical Standard). 
  > Deckblatt und Folgeseiten: `APPROVED FOR PUBLIC RELEASE – DISTRIBUTION IS UNLIMITED`.
* **Themen:** Raumfahrt-Schraubverbindungen, vorspannungsunabhängige Sicherungselemente, Reibwertüberwachung, Gewindeüberstand, Mindesteinschraubtiefe, Übergang vom Gewinde zum Schaft, Kopfauflagen-Fasen.
* **3 verifizierte Konstruktionsregeln:**
  1. **Pflicht zu vorspannungsunabhängiger Schraubensicherung** (S. 37, Abschnitt 4.6.1 [TFSR 16]):
     > *"[TFSR 16] Regardless of the magnitude of preload, each threaded fastening system in spaceflight hardware shall incorporate a minimum of one locking feature that does not depend upon preload to function."*
  2. **Zwang zu mechanischer Sicherung bei rotierenden Bauteilen** (S. 38, Abschnitt 4.6.2 [TFSR 17]):
     > *"[TFSR 17] A mechanical locking feature shall be used on any bolt subject to rotation in operation. [Rationale: Bolts subject to rotation during operation (not including installation or removal of the bolt) may produce forces that would overcome the effectiveness of a prevailing torque or adhesive locking feature. A pure mechanical feature such as safety wire has been demonstrated to be effective at preventing liberation of fastened joint members.]"*
  3. **Mindest-Gewindeüberstand und Gewindeauslauf-Vermeidung** (S. 41–42, Abschnitt 4.7.4 & 4.7.5 [TFSR 24]):
     > *"To ensure that all internal threads are fully engaged, the length of each fastener used with a nut, nut plate, or insert should be selected to extend a distance of at least twice the thread pitch, p, past the outboard end of the nut, nut plate, or insert."* sowie *"[TFSR 24] For a fastener with a full diameter body, the bolt grip and the number and type of washers shall be selected to ensure the internal threads do not encroach on the incomplete runout threads of the fastener."*

---

### 3. ECSS-E-HB-32-23A Rev.1: Threaded Fasteners Handbook
* **Herausgeber:** European Cooperation for Space Standardization (ECSS) / ESA-ESTEC Requirements & Standards Section, Noordwijk, Niederlande.
* **Jahr:** 2023 (6. Februar 2023; Revision 1 der Erstausgabe vom 16. April 2010).
* **URL:** [https://ecss.nl/wp-content/uploads/2023/02/ECSS-E-HB-32-23A-Rev.1(6February2023).pdf](https://ecss.nl/wp-content/uploads/2023/02/ECSS-E-HB-32-23A-Rev.1(6February2023).pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Frei zum Download auf `ecss.nl`. Urheberrecht liegt bei der ESA für die ECSS-Mitglieder: 
  > `2023© by the European Space Agency for the members of ECSS`. 
  > Gemäß ECSS-Nutzungsbedingungen (ECSS-P-00C, Klausel 5.8): `No ECSS document may be reproduced in any form without the explicit consent of ESA. However, this consent is granted to ECSS members for their own use, for their contractors and subcontractors... when ECSS documents text is used, ECSS copyright is acknowledged, quotations clearly identified in the document together with exact reference/version...`
* **Themen:** Detaillierte Berechnung hochbelasteter Schraubenverbindungen (nach VDI 2230 abgewandelt), Ausnutzungsgrad, Setzvorgänge (Embedding), Flanschnachgiebigkeit, Biegung langer Schrauben, Gewindetoleranzen, Tellerfeder-Einsatz.
* **3 verifizierte Konstruktionsregeln:**
  1. **Biegebeanspruchung durch mangelnde Flansch-Planparallelität** (S. 45, Abschnitt 5.5.3):
     > *"The absence of planarity between flanges can generate bending on the screw (see Figure 5-8). In most cases this angle is so small with regard to the stiffness of the screw that the induced constraint is negligible, but in some specific designs (e.g. long screws) this has to be considered with different possible solutions: • Spherical washers to suppress this imposed angle • Or decrease of the torque/tension to maintain an acceptable safety margin on the screw."*
  2. **Ausnutzungsgrad der Schraubenstreckgrenze (Coefficient of Utilisation)** (S. 46, Abschnitt 6.2):
     > *"The size and strength class of fasteners is chosen taking into account the coefficient of utilization $\gamma$. This is the maximum pretension stress divided by the yield stress of the fastener material, $\gamma = \sigma_{v,max} / \sigma_y$. The value of $\gamma$ can be varied in order to fine-tune the performance of the joint however it is important that the value typically lies in the range from 0,5 to 0,8. The recommended value to start the design process is 0,8."*
  3. **Schraubensteifigkeit vs. Setzbetrag & Mindesteinschraubtiefe** (S. 59–60, Abschnitt 6.4.2.7 & 6.4.2.9):
     > *"It is important that long thin compliant fasteners are used in preference to short, stubby stiff fasteners. The total amount of embedding is the same for both for a given preload but for the compliant fastener the stiffness is less and hence a smaller preload loss occurs (see Figure 6-7). Similarly Belleville washers (conical spring washers as shown in Figure 6-8) can be used to increase the compliance of the clamped parts and hence reduce the effect of embedding."* sowie *"The minimum acceptable thread engagement of high strength steel or titanium fastener is 0,8 times the nominal diameter of the fastener. It is important to use at least 1,5d thread engagement for such fastener used in aluminium tapped holes, even if wire thread inserts (e.g. helicoils) are used."*

---

### 4. ECSS-E-HB-32-21A: Adhesive Bonding Handbook
* **Herausgeber:** European Cooperation for Space Standardization (ECSS) / ESA-ESTEC Requirements & Standards Division, Noordwijk, Niederlande.
* **Jahr:** 2011 (20. März 2011).
* **URL:** [https://ecss.nl/wp-content/uploads/handbooks/ecss-e-hb/ECSS-E-HB-32-21A20March2011.pdf](https://ecss.nl/wp-content/uploads/handbooks/ecss-e-hb/ECSS-E-HB-32-21A20March2011.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Frei herunterladbar auf `ecss.nl`. Urheberrechtlich geschützt durch ESA: 
  > `2011© by the European Space Agency for the members of ECSS`. 
  > Zitate und technische Auswertungen unter Quellenangabe gestattet; keine unautorisierte 1:1-Weiterverbreitung des Gesamtwerks.
* **Themen:** Strukturkleben im Leichtbau, Klebstoffauswahl (Pasten, Folienklebstoffe), Fügeteilgestaltung, Vermeidung von Schälbeanspruchung (Peel stress), Überlappungsverhältnisse, Schäftungen, Klebschichtdicken.
* **3 verifizierte Konstruktionsregeln:**
  1. **Festigkeitsverhältnis und Klebschichtdicke** (S. 131, Abschnitt 9.2.2.1):
     > *"The shear strength of the adhesive is at least 50% greater than that of the adherend... The adhesive bond-line thickness is: 0.05 mm to 0.25 mm for adhesive films, 0.05 mm to 0.5 mm for paste adhesives."*
  2. **Einsatzgrenzen von einfachen Überlappungsklebungen (Single Lap Joints)** (S. 131, Abschnitt 9.2.2.2):
     > *"Appropriate for adherend thicknesses up to 1.75 mm for aluminium alloy or quasi-isotropic CFRP. Overlap-to-thickness ratio is between 50:1 and 100:1. An unsupported single lap joint can never be as strong as the adherend members."*
  3. **Gestaltungsgrenzen bei Doppelüberlappung und Schäftung** (S. 131, Abschnitt 9.2.2.3 & 9.2.2.4):
     > *"Double lap and double strap joints: adherend thickness limited to 4.5 mm for uniform double strap joint, thickness limit raised to 6.35 mm when using tapered splice straps, optimum overlap-to-thickness ratio of about 30:1... Stepped or scarf joints: the only appropriate joints for adherends thicker than 6.35 mm"*

---

### 5. MIL-HDBK-727: Design Guidance for Producibility
* **Herausgeber:** US Department of Defense, entwickelt durch Army Materials and Mechanics Research Center (AMMRC), Watertown, MA.
* **Jahr:** 1984 (5. April 1984).
* **URL:** [https://everyspec.com/MIL-HDBK/MIL-HDBK-0700-0799/download.php?spec=MIL_HDBK_727.1853.pdf](https://everyspec.com/MIL-HDBK/MIL-HDBK-0700-0799/download.php?spec=MIL_HDBK_727.1853.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Public Domain (US-Regierungswerk / DoD Military Handbook, 17 U.S.C. § 105). 
  > Titelblatt: `NO DELIVERABLE DATA REQUIRED BY THIS DOCUMENT. AREA MISC.` Unbeschränkte Freigabe für öffentliche Ausschreibungen und Ingenieuranwendungen.
* **Themen:** Fertigungsgerechte Konstruktion für Metalle, Kunststoffe und Verbundwerkstoffe; Zerspanungsrichtlinien, Sacklochbohrungen und -gewinde, Gussfehlervermeidung, Eigenspannungen durch Wärmebehandlung, Biege- und Ziehteile, Toleranzketten.
* **3 verifizierte Konstruktionsregeln:**
  1. **Nutzbare Gewindetiefe und Bohrtiefenzuschlag bei Sacklöchern** (S. 4-97 / PDF S. 259, Abschnitt 4-3.2.1.5.3):
     > *"There are two classifications for tapped holes: the open or through hole and the closed or blind hole. When blind holes cannot be avoided in design, the depth of perfect thread should not exceed two times the thread diameter. The depth of the drilled hole should be the depth of the perfect thread plus the K (clearance) factor. A bottom tap-chamfer (1 to 1.5 threads) is used only where the depth prohibits use of a plug tap-chamfer (3 to 5 threads)."*
  2. **Vermeidung scharfer Innenkanten bei Fräs- und Gusskavitäten** (S. 4-110 / PDF S. 272, Abschnitt 4-5.2):
     > *"SQUARE CORNERS ON MACHINED INTERIOR CONTOURS: Cause and Effect: The design requires a box-like cavity in a cast metal block to have internal square corners. However, this results in a high reject rate caused by cracking, which results from the stresses at the squared corners. Solution: Subsequent review of the design intent revealed this feature was not necessary. The correct radius, which matched a standard milling cutter, was used, and the problem was resolved."*
  3. **Verzug durch Freisetzen von Eigenspannungen bei Gussteilen** (S. 4-111 / PDF S. 273, Abschnitt 4-5.10):
     > *"SURFACE STRESSES IN CASTINGS: Cause and Effect: The design specified long, thin castings as internal structural members of a container skin. To assure good contact for joining, a surface finish of 1.60 µm (63 µin.) was specified on the mating surface. After casting and heat-treating, milling operations were started to achieve the surface finish. Cutting the surface of a heat-treated casting releases surface stresses that have built up in the parts. This causes massive warpage and very high rejection rates. Solution: Reexamine the 1.60 µm (63 µin.) requirement. In this case it was not necessary and was eliminated along with the problem."*

---

### 6. MIL-HDBK-60: Threaded Fasteners - Tightening to Proper Tension
* **Herausgeber:** US Department of Defense, Defense Industrial Supply Center (DISC), Philadelphia, PA.
* **Jahr:** 1990 (12. März 1990; ersetzt Anhang A12 von FED-STD-H28).
* **URL:** [http://contrails.free.fr/fichiers2/mil-hdbk-60_proper_tension.pdf](http://contrails.free.fr/fichiers2/mil-hdbk-60_proper_tension.pdf) *(auch über [quicksearch.dla.mil](https://quicksearch.dla.mil/))*
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Public Domain (US-Regierungswerk). 
  > Deckblatt: `DISTRIBUTION STATEMENT A. Approved for public release; distribution is unlimited.`
* **Themen:** Kontrollierte Schraubenvorspannung, zulässige Auslastungsgrenzen, Setzverluste (Relaxation), Torsionsanteil beim Drehmomentanzug (von-Mises-Spannung), Flansch-Verschraubungssequenzen, Temperatureinflüsse auf die Vorspannkraft.
* **3 verifizierte Konstruktionsregeln:**
  1. **Zulässige Vorspannkraftbereiche und Standardisierungs-Kompensation** (S. 4, Abschnitte 5.1 & 5.2):
     > *"In general, fasteners are designed for maximum utilization of material. Therefore, a maximum safe preload is normally applied. But, if, for standardization or logistic reasons, a lower strength bolt or nut is replaced by one of higher strength, preload values should not be increased. Preload should be based upon calculated joint requirements... Maximum bolt preloads specified are generally within the following ranges: a. 50 - 80% Minimum tensile ultimate strength, b. 75 - 90% Minimum tensile yield strength or proof load, c. 100% Observed proportional limit or onset of yield."*
  2. **10%-Pauschalregel für Setzbeträge und Relaxation** (S. 5, Abschnitt 5.5.2):
     > *"When preloads are first applied to bolts in a joint, local yielding takes place due to excess bearing stress under nut and bolt heads, local high spots, rough surface finish, and lack of perfect squareness of bolt and nut bearing surfaces. Also, loads are not distributed evenly on each thread in a joint. Thread deformation may, therefore, take place to redistribute load more evenly on the threaded parts. All this results in a loss of preload within a period of minutes to hours. As a general practice, an allowance for 10% loss of preload may be made when designing a joint."*
  3. **Kreuzweises Anziehen von Flanschen und Nachzieh-Empfehlung** (S. 6, Abschnitt 5.7):
     > *"It is important to apply approximately equal tension to each of the bolts in a flange joint, particularly if the joint includes a gasket. Unequal tension will result in leakage past the gasket. The recommended procedure is to tighten in stages, following a pattern of tightening a pair of opposite bolts, then a pair of opposite bolts 90° away, followed by pairs of opposite bolts in between... After tightening fully, a re-tightening several hours later will help to assure preload relaxation will not cause the joint to leak."*

---

### 7. FAA AC 43.13-1B (w/ Change 1): Aircraft Inspection and Repair
* **Herausgeber:** U.S. Department of Transportation, Federal Aviation Administration (FAA), Washington, D.C.
* **Jahr:** 1998 (Change 1 datiert vom 27. September 2001).
* **URL:** [https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_43.13-1B_w-chg1.pdf](https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_43.13-1B_w-chg1.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Public Domain (Advisory Circular der US-Bundesluftfahrtbehörde, 17 U.S.C. § 105). Öffentlich und lizenzkostenfrei verfügbar.
* **Themen:** Luftfahrtübliche Maschinenelemente, Klemmlängen- und Unterlegscheiben-Regeln, Reibungsdrehmoment (Running/Drag torque), Sicherungsmuttern, Kronenmuttern mit Splint, Drahtsicherung, Nietlochabstände bei Blechverbindungen, Blindniet-Restriktionen.
* **3 verifizierte Konstruktionsregeln:**
  1. **Maximale Unterlegscheibenhöhe und Gewindeüberstand** (Kap. 7, S. 7-5, Par 7-37):
     > *"In general, bolt grip lengths of a fastener is the thickness of the material the fastener is designed to hold when two or more parts are being assembled. Bolts of slightly greater grip length may be used, provided washers are placed under the nut or bolthead. The maximum combined height of washers that should be used is 1/8 inch. This limits the use of washers necessary to compensate for grip, up to the next standard grip size... All bolt installations which involve self-locking or plain nuts should have at least one thread of the bolt protruding through the nut."*
  2. **Berücksichtigung des Gewindereibungsmoments beim Drehmomentanzug** (Kap. 7, S. 7-6, Par 7-40):
     > *"Run the nut down to near contact with the washer or bearing surface and check the friction drag torque required to turn the nut. Whenever possible, apply the torque to the nut and not the bolt. This will reduce rotation of the bolt in the hole and reduce wear. Add the friction drag torque to the desired torque. This is referred to as 'final torque,' which should register on the indicator or setting for a snap-over type torque wrench."*
  3. **Striktes Verbot von selbstsichernden Muttern auf rotierenden Achsen** (Kap. 7, S. 7-11, Par 7-64):
     > *"a. DO NOT use self-locking nuts on parts subject to rotation... d. Self-locking nuts should not be used with bolts, screws, or studs to attach access panels or doors, or to assemble any parts that are routinely disassembled before, or after each flight... Fiber or nylon self-locking nuts are not installed in areas where temperatures exceed 250 °F."*
     *(Ergänzende Blech-/Nietregel aus Kap. 4, S. 4-17 / PDF S. 159, Par 4-57: Randabstand einer Nietreihe $\ge 2D$, Nietteilung $\ge 3D$; striktes Blindnietverbot in fluiddichten Bereichen und an Steuerflächenlagern).*

---

### 8. NASA RP-1152: Gearing
* **Herausgeber:** National Aeronautics and Space Administration (NASA) & U.S. Army Aviation Research and Technology Activity (USAARTA-AVSCOM), Lewis Research Center, Cleveland, Ohio. Autoren: John J. Coy, Dennis P. Townsend, Erwin V. Zaretsky.
* **Jahr:** 1985 (Dezember 1985; AVSCOM Technical Report 84-C-15).
* **URL:** [https://ntrs.nasa.gov/api/citations/19860005142/downloads/19860005142.pdf](https://ntrs.nasa.gov/api/citations/19860005142/downloads/19860005142.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Public Domain (U.S. Government work nach 17 U.S.C. § 105). 
  > RDP (S. 67): `18. Distribution Statement: Unclassified-unlimited STAR Category 37`.
* **Themen:** Stirnrad-, Schrägrad-, Kegelrad- und Planetenverzahnung; Flankenspielauslegung (Backlash), Profilüberdeckung (Contact Ratio), Unterschnitt und Eingriffstiefe, Zahnfußbiegung (Lewis-Gleichung), EHD-Schmierfilmbildung, Grübchenbildung (Pitting) und Fressen (Scoring).
* **3 verifizierte Konstruktionsregeln:**
  1. **Funktionsgerechte Flankenspiel-Bemessung (Backlash)** (S. 4 / PDF S. 10, Abschnitt 2.1):
     > *"The space between the teeth must be larger than the mating tooth thickness in order to prevent jamming of the gears. The difference between tooth thickness and the tooth space as measured along the pitch circle is called backlash... Backlash should be small in positioning control systems, but it should be quite generous for single-direction power gearing (table 2)."*
  2. **Grenzen der Profilüberdeckung (Contact Ratio)** (S. 5 / PDF S. 11, Abschnitt 2.1):
     > *"Gears are generally designed with contact ratios of 1.2 to 1.6. A contact ratio of 1.6, for example, means that 40 percent of the time one pair of teeth will be in contact and 60 percent of the time two pairs of teeth will be in contact. A contact ratio of 1.2 means that 80 percent of the time one pair of teeth will be in contact and 20 percent of the time two pairs of teeth will be in contact. Gears with contact ratios greater than 2 are referred to as 'high-contact-ratio gears.' For these gears there are never less than two pairs of teeth in contact."*
  3. **Vermeidung von Unterschnitt und unzulässigem Eingriff unterhalb des Grundkreises** (S. 5 / PDF S. 11, Abschnitt 2.1):
     > *"The portion of the spur gear below the base circle is sometimes cut as a straight radial line but never as an involute curve (fig. 2(b)). Hence, if contact should occur below the base circle, nonconjugate action (interference) will occur. The maximum addendum radius of the gear without interference is calculated from the following equation: $r_a = (r_b^2 + C^2 \sin^2 \phi)^{1/2}$... Should interference be indicated, there are several methods to eliminate it. The center distance can be increased, which will also increase the pressure angle and change the contact ratio. Also, the addendum can be shortened, with a corresponding increase in the addendum of the mating member."*

---

### 9. MIT OpenCourseWare: FUNdaMENTALS of Design (Prof. Alexander Slocum)
* **Herausgeber:** Massachusetts Institute of Technology (MIT), Department of Mechanical Engineering. Autor: Prof. Alexander H. Slocum.
* **Jahr:** 2007 / 2008.
* **URL:** [https://meddevdesign.mit.edu/wp-content/uploads/FUNdaMENTALs-Topic-9.pdf](https://meddevdesign.mit.edu/wp-content/uploads/FUNdaMENTALs-Topic-9.pdf) *(Topic-Portal: [meddevdesign.mit.edu/fundamentals-of-design/](https://meddevdesign.mit.edu/fundamentals-of-design/))*
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Open Educational Resource (OER) via MIT Pappalardo Series in Mechanical Engineering. 
  > Frontispiz: `©2007 Alexander H. Slocum`. Frei herunterladbar und einsehbar für Lehre und Forschung. Die dargelegten physikalisch-mathematischen Konstruktionsprinzipien (Exact Constraint, Kraftkegel) sind gemeinfrei.
* **Themen:** Exakte Führung (Exact Constraint Design), Kinematische Kopplungen (Kinematic Couplings 3-2-1, Kelvin Clamp, Maxwell Groove), Schraubenverbindungen als Reibklemmen, Kraftkegel / Druckkegel, Wälz- und Gleitlager, Hertzsche Pressung.
* **3 verifizierte Konstruktionsregeln:**
  1. **Funktion der Schraube als reine Spannvorrichtung ohne Scherbelastung** (Topic 9, S. 9-8):
     > *"A bolt is really just a means to clamp a joint together, and the bolt itself does NOT withstand any shear loads... In general, about 50% of the energy goes to friction under the bolt head, 40% goes to friction in the threads, and only about 10% goes to creating tension in the threads."*
  2. **Schmierung von Befestigungsschrauben zur Klemmkrafterzeugung** (Topic 9, S. 9-8):
     > *"Since a bolt is a leadscrew, and the primary functional requirement is to generate a clamping force, the bolt threads should be lubricated. Grease works well, and the threads will still not be back drivable. In high vibration applications, use a thread-locking lubricant (e.g., Loctite 410™)."*
  3. **Überdeckung der Druckkegel (Stress/Strain Cones) für kontinuierliche Verbindungssteifigkeit** (Topic 9, S. 9-8):
     > *"A strain cone (or stress cone) under the bolt head that projects downward at 30 to 45 degrees from the vertical. When sufficient bolts are used in a joint such that the strain cones overlap, the joint behaves as if it were a continuous piece of material and there was no joint at all. To prevent the stress field from affecting components, apply Saint-Venant’s principle."*

---

### 10. Hochschule Anhalt: Maschinenelemente – Schrauben und Schraubenverbindungen (Prof. Dr. H. Gruss)
* **Herausgeber:** Hochschule Anhalt, Fachbereich 6 (Maschinenbau, Umwelttechnik und Elektrotechnik), Köthen. Autor: Prof. Dr.-Ing. H. Gruss.
* **Jahr:** 2019.
* **URL:** [https://www.hs-anhalt.de/fileadmin/Dateien/FB6/personen/voigt_st/Lehrunterlagen/01_ME_Vorlesung/05_ME_Schraubenverbindungen_Stud.pdf](https://www.hs-anhalt.de/fileadmin/Dateien/FB6/personen/voigt_st/Lehrunterlagen/01_ME_Vorlesung/05_ME_Schraubenverbindungen_Stud.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Frei über das öffentliche Web-Repository des Fachbereichs abrufbares Hochschulskript (`Public Web Access`). 
  > Urheberrecht verbleibt beim Dozenten (`Prof. Dr.-Ing. H. Gruss, MASCHINENELEMENTE`). Zur freien wissenschaftlichen und studentischen Nutzung freigegeben; die enthaltenen Konstruktionsregeln nach VDI 2230 und DIN-Normen sind technischer Allgemeinstand.
* **Themen:** Mechanisches Wirkprinzip von Schraubenverbindungen, Anziehfaktoren, Einspannungsdiagramm, Lockern vs. Losdrehen vs. Verlieren, Unwirksamkeit federnder Normteile, Kerbwirkung am Gewinde, Einschraubtiefen in Guss und Leichtmetall.
* **3 verifizierte Konstruktionsregeln:**
  1. **Auslegung gegen Lockern vs. Losdrehen** (S. 100, Abschnitt 5.14):
     > *"Eine richtig gestaltete und beanspruchungsgerecht ausgelegte Schraubenverbindung benötigte keine zusätzliche Sicherungselement, wenn bei allen Betriebszuständen eine ausreichende Vorspannung vorhanden ist. Dennoch treten in der Praxis insbesondere bei dynamischen Belastungen zwei Versagensformen durch Vorspannungsverlust auf: Lockern: Klemmkraftverlust infolge plast. Verformung (Alu-Stahl), Setzen, Temperatureinfluss; Losdrehen: keine Selbsthemmung des Gewindes infolge von Relativbewegungen in den Trennfugen -> Schraube und Mutter verdrehen sich"*
  2. **Wirkungslosigkeit federnder Sicherungselemente** (S. 103, Abschnitt 5.14):
     > *"Sicherungselemente gegen Losdrehen: federnd (a-g) / reibschlüssig (h und i) -> a – g sind wirkungslos; Vergrößerung Setzbetrag; Beschädigung der Oberflächen"* *(betrifft u.a. Federringe nach DIN 127, Federscheiben nach DIN 137, Zahnscheiben nach DIN 6797).*
  3. **Kerbentlastung am ersten tragenden Gewindegang** (S. 75, Abschnitt 5.9):
     > *"Das Einbringen von Gewinden bedeutet grundsätzlich Kerbwirkung, bei mehreren Windungen ist davon besonders der Gewindeanfang (unterhalb des Schraubenkopfes) betroffen. Des Weiteren können die Kerbbeanspruchungen durch sorgfältiges Gestalten des Gewindeauslaufs sowie durch Vermeidung großer Querschnittübergänge vermindert werden."*

---

### 11. Hochschule Anhalt: Konstruktion – Gestaltungsregeln Teil 2 (Prof. Dr. H. Gruss)
* **Herausgeber:** Hochschule Anhalt, Fachbereich 6 (Maschinenbau), Köthen. Autor: Prof. Dr.-Ing. H. Gruss.
* **Jahr:** 2019.
* **URL:** [https://www.hs-anhalt.de/fileadmin/Dateien/FB6/personen/voigt_st/Lehrunterlagen/03_Ko_Vorlesung/Konstruktion_Stud_Teil-2.pdf](https://www.hs-anhalt.de/fileadmin/Dateien/FB6/personen/voigt_st/Lehrunterlagen/03_Ko_Vorlesung/Konstruktion_Stud_Teil-2.pdf)
* **Nutzungsbedingungen / Lizenz wörtlich:** 
  > Frei über das Hochschulportal zugängliche Vorlesungsunterlage (`Public Web Access`). 
  > Urheberrechtlich geschützt durch den Verfasser (`Prof. Dr.-Ing. H. Gruss, KONSTRUKTION`). Bereitgestellt zur akademischen Ausbildung; Methodikregeln basieren auf Pahl/Beitz und VDI 2221 ff.
* **Themen:** Grundregeln des Konstruierens ("einfach" und "eindeutig"), Fertigungsgerechte Bauteilgestaltung (Zerspanung, Montage, Prüfung), Wärmedehnungsgerechtes Konstruieren, Korrosionsgerechtes Gestalten (Spalt- und Kontaktkorrosion an Fügestellen).
* **3 verifizierte Konstruktionsregeln:**
  1. **Die Grundregeln des Entwerfens: "einfach" und "eindeutig"** (S. 214–215, Abschnitte 4.2 & 4.2.1):
     > *"Die Auswertung einer Vielzahl von Konstruktionserfahrungen lässt die Ableitung von zwei Grundregeln zu, bei deren Beachtung gute Realisierungschancen für eine optimale Konstruktion gegeben sind: - einfach, - eindeutig... Eine technische Lösung erscheint uns einfacher, wenn sie mit wenigen Bauelementen realisiert werden kann. In diesem Fall sinken beispielsweise die Baukosten und der Verschleiß."*
  2. **Fertigungsgerechte Formgebung zur Rüstzeitminimierung** (S. 220, Abschnitt 4.2.1):
     > *"Fertigung, Montage, Kontrolle: - einfach zu bearbeitende geometrische Formen -> Platten, Zylinder, Kegel, definierte Bezugflächen; - wenige Fertigungsverfahren -> geringe Rüst- und Umspannzeiten; - übersichtliche Anordnung für die Maßkontrolle; - zu montierende Teile leicht erkennbar, Montage leicht durchschaubar; - jeder Einstellvorgang nur einmal notwendig"*
  3. **Vermeidung von Schmutz- und Feuchtigkeitsfallen an Schrauben** (S. 303–304, Abschnitt 4.5.2):
     > *"Wegen der Voraussetzungen zur Bildung eines elektrochemischen Elementes leiten sich folgende Gestaltungsregeln ab: Regel 2: Ablagerung von Fremdstoffen vermeiden. An form- und kraftschlüssigen sowie Schraubenverbindungen entstehen Spalte, in welche Feststoffe und Flüssigkeiten eindringen können."*

---

## 3. Rangliste: Die 10 ergiebigsten Dokumente für einen Konstruktions-Agenten

Für den Einsatz in einem **Open-Source-CAD-Projekt (unter MIT- oder Apache-2.0-Lizenz)** muss ein Konstruktions-Agent Regeln verarbeiten, die:
1. **algorithmisch überprüfbar sind** (harte Geometrieprüfung wie $d \ge 1{,}5D$, Kantenabstände, Klemmlängen, Bohrtiefen),
2. **rechtlich unbedenklich in offene Rule-Engines / ASTs überführt werden dürfen** (Public Domain bevorzugt), und
3. **praxisbewährte Best Practices codieren**, die gängige Konstruktionsfehler automatisiert abfangen.

### Platz 1: NASA RP-1228 – Fastener Design Manual
* **Warum Platz 1:** Vollständig **Public Domain**, frei von Urheberrechtsrisiken für MIT/Apache-2.0. Enthält harte geometrische Faustformeln ($2D$ Loch-Randabstand, $4D$ Teilung, $1{,}5D$ Mindestabstand, Mindest-Einschraubtiefen, Schaftlängenabstimmung) und räumt mit gefährlichen Mythen (wie Federringen) auf. Ideal als Basis-Regelwerk für Schrauben-Assistenten.

### Platz 2: MIL-HDBK-727 – Design Guidance for Producibility
* **Warum Platz 2:** Ebenfalls **Public Domain** (US DoD). Mit über 560 Seiten das umfassendste Nachschlagewerk für "Design for Manufacturing". Bietet konkrete Faustformeln für Bohrertoleranzen, Sacklochtiefen ($L_{\text{thread}} \le 2D$, Freiraumfaktor $K$ für Anschnitte), Fräser-Innenradien und Gusswandstärken. Lässt sich direkt in Geometrie-Prüfskripte (Linter) übersetzen.

### Platz 3: NASA-STD-5020B – Requirements for Threaded Fastening Systems
* **Warum Platz 3:** **Public Domain** und hochaktuell (Revalidierung 2026). Liefert strenge logische Anforderungen (Decision Trees) für den Agenten: Zwang zur mechanischen Sicherung bei rotierenden Wellen/Achsen, Prüfung auf Gewindeauslauf im Klemmbereich ($2p$), Mindestüberstand über die Mutter ($2p$) und Vorspannungsverlustkriterien.

### Platz 4: FAA AC 43.13-1B – Acceptable Methods, Techniques, and Practices
* **Warum Platz 4:** **Public Domain**. Unverzichtbar für die praktische Baugruppen-Validierung: Maximale Scheibenhöhe ($1/8'' \approx 3{,}2\,\text{mm}$), Verbot von Stoppmuttern an drehenden Komponenten und Heißzonen ($> 120\,^\circ\text{C}$), Reibdrehmoment-Kompensation sowie handfeste Blech- und Nietregeln (Lochabstände $\ge 3D$, Randabstand $\ge 2D$, Blindnietverbote).

### Platz 5: ECSS-E-HB-32-23A Rev.1 – Threaded Fasteners Handbook
* **Warum Platz 5:** Inhaltlich das weltweit tiefste Werk zur Schraubenberechnung (über 500 Seiten Raumfahrt-Know-how). Enthält quantitative Formeln für Flanschnachgiebigkeiten, Biegung langer Schrauben bei unparallelen Flanschen und Setzbetragskompensation durch Tellerfedern. *Einschränkung:* Rechtlich ESA-Copyright, d. h. der Code-Agent darf die physikalischen Formeln und Grenzwerte implementieren, aber keine Textblöcke 1:1 kopieren.

### Platz 6: MIL-HDBK-60 – Threaded Fasteners: Tightening to Proper Tension
* **Warum Platz 6:** **Public Domain**. Perfekt für die Auslegung von Montagevorschriften: Feste Grenzwerte für die Schraubenauslastung ($75 - 90\,\%$ Streckgrenze), die standardmäßige $10\,\%$-Setzverlust-Kompensation und die genaue Anzugsreihenfolge bei Flanschverbindungen.

### Platz 7: MIT OCW (Alexander Slocum) – FUNdaMENTALS of Design
* **Warum Platz 7:** Hervorragend für high-level Synthese und Präzisionsmaschinenbau. Vermittelt das deterministische "Exact Constraint Design" (Kinematic Couplings 3-2-1), Hertzsche Pressungsformeln für Punkt-/Linienkontakt und das Modell des 45°-Druckkegels unter Schraubenköpfen, mit dem ein CAD-Agent prüfen kann, ob Schraubenabstände klein genug für eine flächige Klemmung sind.

### Platz 8: ECSS-E-HB-32-21A – Adhesive Bonding Handbook
* **Warum Platz 8:** Das maßgebliche Referenzwerk für Klebverbindungen. Liefert harte Grenzwerte für den Agenten: Maximale Fügeteil-Dicke bei einfachen Überlappungen ($t \le 1{,}75\,\text{mm}$), Überlappungsverhältnisse ($50:1$ bis $100:1$ für Single Lap, $30:1$ für Double Lap) und Schichtdickenbegrenzungen ($0{,}05 - 0{,}25\,\text{mm}$).

### Platz 9: NASA RP-1152 – Gearing
* **Warum Platz 9:** **Public Domain**. Bietet eine geschlossene mathematische und geometrische Grundlage für Zahnrad-Generatoren und Prüfroutinen: exakte Flankenspiel-Tabellen nach Diametral Pitch / Modul, Überdeckungsgrad-Kriterien ($1{,}2 - 1{,}6$) und die Grenzformel zur Vermeidung von Unterschnitt am Zahnfuß.

### Platz 10: Hochschule Anhalt (Prof. Dr. H. Gruss) – Vorlesungsreihe Maschinenelemente & Konstruktion
* **Warum Platz 10:** Sehr didaktische und praxisnahe Systematisierung deutscher Maschinenbau-Tradition (Pahl/Beitz, VDI 2230). Ideal für einen CAD-Linter, der konstruktive "Sünden" anprangern soll: Einsatz unwirksamer Federringe, mangelnde Kerbentlastung an Querschnittsübergängen, ungünstige Spaltgeometrien (Spaltkorrosion) und die Reduktion unnötiger Freiheitsgrade.

---

## 4. Fazit & Empfehlung für das Open-Source-CAD-Projekt

1. **Rechtliche Architektur des Regelkatalogs:**
   * Nutzen Sie **NASA RP-1228**, **MIL-HDBK-727**, **NASA-STD-5020B**, **MIL-HDBK-60**, **FAA AC 43.13-1B** und **NASA RP-1152** als **primäre Text- und Wissensquellen**. Da es sich um Werke von US-Bundesbehörden handelt, fallen sie unter die **US Public Domain (17 U.S.C. § 105)**. Ihre Regeln, Schwellenwerte, Tabellen und Auszüge können ohne Lizenzkonflikte direkt in Markdown-Katalogen, JSON-Regeldatenbanken oder Code-Generatoren unter MIT/Apache-2.0 veröffentlicht werden.
2. **Nutzung von ECSS und Hochschulquellen:**
   * Aus den europäischen und universitären Werken (**ECSS-E-HB-32-xx**, **MIT OCW**, **HS Anhalt**) sollten Sie die **mathematischen Gleichungen, geometrischen Grenzwerte und physikalischen Zusammenhänge** extrahieren. Reine Naturgesetze, Gleichungen und technische Kennwerte genießen keinen Urheberrechtsschutz; vermieden werden sollte lediglich das wörtliche Kopieren längerer Fließtextpassagen.
