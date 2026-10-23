# Deep Research: Autodesk Inventor (Stand 2026/2027), Open-Source-CAD-Landschaft & Blaupause für ein modulares, KI-nativen 3D-CAD

> **Stand der Recherche:** Oktober 2026  
> **Zielsetzung:** Belastbare technische und funktionale Bestandsaufnahme als Fundament für eine Open-Source-Roadmap („Autodesk Inventor neu gedacht“ – modular, ohne Legacy-Ballast, mit tief integrierten KI-Agenten).

---

## Teil A – Funktionsumfang von Autodesk Inventor (Version 2027 inkl. 2025/2026 & Point-Releases)

Autodesk Inventor ist nach über 25 Jahren Entwicklungszeit (Release 1.0 erschien 1999) eines der funktionsmächtigsten, aber auch monolithischsten Desktop-CAD-Systeme für den Maschinen- und Anlagenbau. Die aktuelle Hauptversion ist **Autodesk Inventor 2027** (erschienen im Frühjahr 2026, aktuelles Point-Release **2027.1** vom Sommer 2026), aufbauend auf den Meilensteinen **Inventor 2025** und **Inventor 2026** (inkl. 2026.1, 2026.2, 2026.3).

Zur Einordnung für eure Roadmap ist jede Funktionsgruppe mit einer **Praxis-Relevanz für den Maschinenbau-Alltag (Einzelanwender, Maker, KMU / Sondermaschinenbau)** bewertet:
* **[KERN]** – Unverzichtbar für fast jedes Projekt (deckt ca. 80 % der täglichen Arbeit ab; Pflicht für ein MVP).
* **[HÄUFIG]** – Regelmäßig im professionellen KMU-Alltag genutzt (wichtig für v1.0 / Kern-Plugins).
* **[NISCHE]** – Spezialisierte Branchenlösung, Legacy-Funktion oder Enterprise-Funktion (idealer Kandidat für optionale Drittanbieter-Plugins oder gezieltes Weglassen).

---

### 1. Bauteilkonstruktion (Part Modeling `.ipt`)

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **2D-Skizze (2D Sketch)** | Linien, Rechtecke (2-/3-Punkt, Zentrum), Kreise, Bögen, Polygone, Langlöcher (Slots – gerade & gebogen), Ellipsen, Splines (Interpolations- & Kontrollpunkt-Splines, Gleichungskurven), Übergangskurven (G1–G3), Text (inkl. einliniger Gravurschriften), Punkt/Mittelpunkt. Modifikatoren: Stutzen (Trim), Dehnen (Extend), Teilen (Split), Versatz (Offset), Abrunden (Fillet), Fase (Chamfer), Strecken, Maßstab, Drehen, Kopieren, Rechteck-/Kreisanordnung, Spiegeln. Geometrie projizieren (Kanten, Schnittkanten, Blechabwicklung, DWG-Unterlagen). *Neu in 2026.1:* „Referenz ersetzen“ (Replace Reference) zum Heilen verlorener Projektionen ohne Löschen. | **[KERN]** |
| **3D-Skizze (3D Sketch)** | Linien und Splines im 3D-Raum mit 3D-Triade, 3D-Abrundungen, spiralförmige Kurven, Schnittkurven zweier Flächen (Intersection Curve), Projektion auf Flächen (Project to Surface), Silhouettenkurven, Kurven auf Flächen, Punkt-aus-Excel-Import. | **[HÄUFIG]** *(v. a. für Leitungsverläufe, Schweißrahmen, Sweeps)* |
| **Constraints (Abhängigkeiten)** | **Geometrisch:** Koinzident, Kollinear, Konzentrisch, Fest (Fix), Parallel, Lotrecht, Horizontal, Vertikal, Tangential, Stetig (G2-Krümmung), Symmetrisch, Gleich. Automatische Abhängigkeiten & Freiheitsgrad-Anzeige (DOF).<br>**Bemaßung:** Linear, Ausgerichtet, Winkel (*2026.2: Richtung umkehrbar*), Radius, Durchmesser, Bogenlänge, Getriebene Bemaßung (Driven Dimension). | **[KERN]** |
| **Volumen-Features (Solid Features)** | **Skizzenbasiert:** Extrusion (Volumen/Fläche, Vereinigen/Ausschneiden/Schnittmenge/Neuer Körper, Abstand, Bis-Fläche, Zwischen, Symmetrisch/Asymmetrisch), Drehung (Revolve), Sweeping (entlang Pfad + Leitkurve/Führungsfläche), Erhebung (Loft mit Leitlinien & Mittellinie), Spirale (Coil), Prägen (Emboss/Deboss auf ebenen & zylindrischen Flächen), Rippe/Steg (Rib), Aufkleber (Decal).<br>**Platziert:** Bohrung (Hole: einfach, Durchgang, Gewinde nach ISO/DIN/ANSI, Senkung, Kegelsenkung, Passungstoleranzen), Abrundung (Fillet: konstant, variabel, Sehnenlänge, Flächenabrundung, Vollrundung), Fase (Chamfer), Wandstärke/Schale (Shell: innen, außen, beidseitig, individuelle Wandstärken), Flächenverjüngung (Draft), Gewinde (Thread: kosmetisch per Textur + Gewindetabelle; für echte 3D-ausmodellierte Gewinde war lange ein Zusatztool/CoolOrange nötig, inzwischen nativer), Teilen (Split Face / Split Solid), Körper kombinieren (Combine), Fläche ersetzen (Replace Face), **Finish-Feature** (seit 2024/2025: Beschichtung, Wärmebehandlung, Lackierung, Oberflächenrauheit als Feature im Baum dokumentierbar).<br>**Anordnungen:** Rechteckig (inkl. unregelmäßiger Abstände seit 2026), Kreisförmig, Skizzengesteuert (Sketch Driven), Spiegeln. | **[KERN]** *(Basis-Features)*<br>**[HÄUFIG]** *(Sweeping, Loft, Rippe, Finish)* |
| **Kunststoff-Features (Plastic Parts)** | Spezielle Spritzguss-Makro-Features: Lüftungsöffnung (Grill), Einrastung (Snap Fit – Haken/Schlaufe), Absatz (Rest), Lippe/Nut (Lip), Schraubdom (Boss), Regelbasierte Verrundung (Rule Fillet). | **[NISCHE]** *(nur für Spritzguss-Gehäusekonstrukteure)* |
| **Konstruktionsgeometrie** | Arbeitsebenen (Work Planes: Versatz, Winkel, 3 Punkte, Tangential, Mittelebene/Torus), Arbeitsachsen (Work Axes), Arbeitspunkte (Work Points), Benutzerkoordinatensysteme (UCS). | **[KERN]** |
| **Flächenmodellierung (Surfaces)** | Flächen-Extrusion, -Drehung, -Loft, -Sweep; Begrenzungsfläche (Boundary Patch inkl. G0/G1/G2-Bedingungen), Fläche stutzen (Trim), Fläche dehnen (Extend), Flächen heften (Stitch zum Solid), Verdicken/Versatz (Thicken/Offset), Regelfläche (Ruled Surface), Fläche löschen (mit Heilungsoption). Analysewerkzeuge: Zebra-Streifen, Krümmungskämme, Formschrägenanalyse, Schnittanalyse. | **[HÄUFIG]** *(Flächen-Reparatur, Übergänge, Verdicken)*<br>**[NISCHE]** *(Class-A-Freiform)* |
| **Freiform / T-Splines (Freeform)** | Integrierte T-Splines-Umgebung (aus Autodesk Alias/Fusion übernommen): Quader/Zylinder/Kugel/Torus-SubD-Grundkörper, Flächen/Kanten/Scheitelpunkte ziehen, Kanten einfügen, Brücke (Bridge), Symmetrie, Konvertierung in exakte NURBS-B-Rep-Körper. | **[NISCHE]** *(im klassischen Maschinenbau fast nie genutzt; eher Industriedesign)* |
| **Direktbearbeitung (Direct Edit)** | Direktes Ziehen, Verschieben, Größenändern (z. B. Bohrungsdurchmesser ändern), Drehen und Löschen von Flächen – sowohl an nativen parametrischen Bauteilen (erzeugt ein parametrisches `Direct Edit`-Feature in der Timeline!) als auch an importierten „dummen“ STEP-Dateien. | **[HÄUFIG]** *(extrem wertvoll zum Anpassen zugekaufter STEP-Modelle!)* |
| **iParts, iFeatures, Modellzustände** | **iParts:** Klassische tabellengesteuerte Teilefamilien (erzeugt separate abgeleitete Member-Dateien auf der Festplatte – heute weitgehend durch Modellzustände abgelöst).<br>**iFeatures:** Wiederverwendbare Feature-Snippets (z. B. Nuten, Stanzformen) als `.ide`-Katalog.<br>**Modellzustände (Model States, seit 2022):** Mehrere Varianten, Fertigungsstufen (Gussrohteil -> Vorbearbeitung -> Fertigteil) oder Vereinfachungsstufen **in einer einzigen `.ipt`-Datei** durch Unterdrücken von Features und Überschreiben von Parametern/iProperties. | **[HÄUFIG]** *(Modellzustände für Rohteil/Fertigteil & Varianten)*<br>**[NISCHE]** *(alte iParts)* |
| **Parameter & Excel-Kopplung** | Modellparameter (`d0`, `d1`…), Benutzerparameter (Numerisch mit Einheiten, Text, Wahr/Falsch), Mehrwert-Auswahllisten, Gleichungen (`ul`, `mm`, `deg`, `sin`, `cos`, `min`, `max`, `floor`, `isolate`), Toleranz-Auswertung (Median, Ober-/Untergrenze für Neuberechnung), Verknüpfung/Einbettung von Excel-Tabellen (oder LibreOffice Calc). **Neu in Inventor 2027:** Der Parameter-Dialog ist endlich **nicht-modal (modeless)** und kann dauerhaft auf einem zweiten Monitor offen bleiben. | **[KERN]** *(Parameter & Gleichungen)*<br>**[HÄUFIG]** *(Tabellenkopplung)* |
| **Multibody-Design** | Mehrere unabhängige Volumenkörper in einer `.ipt`-Datei modellieren, Boolesche Verknüpfungen, Befehle „Komponenten erstellen“ (Make Components) und „Bauteil erstellen“ (Make Part), um ein Master-Multibody-Bauteil (Top-Down-Skelettmodellierung) assoziativ in eine Baugruppe mit Einzelteilen auszuleiten. | **[HÄUFIG]** *(Standard-Best-Practice für Schweißgruppen, Gehäuse und Top-Down-Design)* |

---

### 2. Baugruppen (Assemblies `.iam`)

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **Abhängigkeiten (Constraints) & Gelenke (Joints)** | **Klassische Abhängigkeiten:** Passend/Fluchtend (Mate/Flush – *seit 2026.1 mit Mehrfachauswahl*), Winkel, Tangential, Einfügen (Insert für Schrauben/Wellen), Symmetrie; Bewegungsabhängigkeiten (Rotation, Rotation-Translation für Zahnräder/Spindeln); Übergangsabhängigkeit (Transition für Kurvenscheiben). *Neu in 2027.1:* Halten der `Alt`-Taste blendet Ursprungsebenen/-achsen der Bauteile temporär ein.<br>**Gelenke (Joints, wie in Fusion):** Starr (Rigid), Drehung (Rotational), Schieber (Slider), Zylindrisch, Planar, Kugel (Ball) – reduziert die Anzahl nötiger Einzel-Constraints. Grenzwerte (Limits/Min-Max) und Kollisions-Kontaktsätze (Contact Solver). | **[KERN]** |
| **Baugruppen-Spiegeln & -Anordnen** | Komponenten in Baugruppen rechteckig, kreisförmig oder gekoppelt an Bauteil-Feature-Muster anordnen. **Neu in Inventor 2026:** Echtes **assoziatives Spiegeln** in Baugruppen (Geometrie- und Positionsänderungen im Quellbauteil aktualisieren die gespiegelte Baugruppe automatisch). | **[KERN]** |
| **Modellzustände (Model States) & Vereinfachung (Simplify)** | Modellzustände ersetzen seit Inventor 2022 die alten „Detailgenauigkeiten“ (Level of Detail / LOD). Speichert Varianten, Montage-Bauzustände und **Ersatzdarstellungen (Substitute Model States)** direkt in der `.iam`.<br>**Vereinfachen-Befehl (Simplify):** Entfernt Kleinteile nach Größe, schließt Bohrungen/Taschen/Abrundungen, ersetzt Komponenten durch Hüllkörper (Quader/Zylinder – *erweitert in 2025/2026*) und speichert das Ergebnis als leichtgewichtiges Einzelteil oder direkt als RVT/STEP für den Kunden (Know-how-Schutz / BIM).<br>**Express-Modus (Express Mode):** Lädt riesige Baugruppen (>10.000 Teile) über gecachte Grafikdaten im Bruchteil der Zeit. | **[HÄUFIG]** *(Simplify für Kundendaten / große Baugruppen)* |
| **Positions- & Ansichtsdarstellungen** | **Positionsdarstellungen (Positional Representations):** Überschreiben Constraints/Offsets (z. B. Zylinder eingefahren vs. ausgefahren, Tür 0° vs. 90° offen); können auf 2D-Zeichnungen als gestrichelte **Überlagerungsansicht (Overlay View)** dargestellt werden.<br>**Ansichtsdarstellungen (View Representations):** Speichern Sichtbarkeit, Transparenz, Kameraposition und Farb-Überschreibungen. | **[HÄUFIG]** |
| **Gestell-Generator (Frame Generator)** | Platziert genormte Stahlbau-/Alu-Profile (DIN, ISO, EN, ANSI) entlang eines 2D/3D-Drahtmodells oder an Bauteilkanten. Automatische Endenbearbeitung: Gehrung (Miter), Ausklinkung (Notch – auch für Rohre/Freiformprofile), Stumpfstoß (Trim to Frame), Verlängern/Verkürzen, Endkappen. Automatische Profil-Stücklisten-Zusammenfassung gleicher Längen. | **[HÄUFIG]** *(im Sondermaschinen- & Vorrichtungsbau fast unverzichtbar)* |
| **Konstruktions-Assistent (Design Accelerator)** | Regel- und berechnungsbasierte Generatoren für Maschinenelemente (inkl. Festigkeitsnachweis nach DIN/ISO/ANSI): Wellen-Generator (inkl. Biegelinie, Torsions-/Biegespannung, Lagerauflager), Stirnrad-, Kegelrad- und Schneckengetriebe, Zahnriemen/Keilriemen, Rollenketten, Wälzlager, Passfedern, Keilwellen, Scheiben-/Kurvengetriebe (Cam), Druck-/Zug-/Schenkelfedern, O-Ringe, Sicherungsringe, Stifte, Trapezgewindespindeln. | **[HÄUFIG]** *(Wellengenerator, Zahnräder, Lager)*<br>**[NISCHE]** *(Kurvenscheiben, Keilriemenberechnung)* |
| **Verschraubungs-Generator & Inhaltscenter** | **Bolted Connection:** Erzeugt komplette Schraubenverbindungen (Schraube + Scheiben + Mutter + automatische Durchgangs-/Gewindebohrung in allen durchdrungenen Bauteilen) in einem Schritt.<br>**Inhaltscenter (Content Center):** Datenbank mit >750.000 Normteilen (DIN, ISO, EN, ANSI, JIS, GOST). *Neu in 2026.1:* Gleichzeitiges Ändern der Größe mehrerer platzierter Normteile einer Familie. | **[KERN]** *(Normteile-Bibliothek & Schrauben)* |
| **Rohrleitungen (Tube & Pipe)** | Routenbasierter Generator für starre Rohrleitungen mit Fittings, gebogene Hydraulikrohre und flexible Schläuche (Biegeradius-Prüfung). Export als ISOGEN-Isometrie (`.pcf`) und Biegemaschinendaten (`.xyz`). | **[NISCHE]** *(Anlagenbau / Hydraulik; das Modul in Inventor gilt als veraltet und sperrig)* |
| **Kabel & Kabelbaum (Cable & Harness)** | 3D-Verlegung von Einzeldrähten, mehradrigen Kabeln und Flachbandkabeln durch Segmente, Stecker-Pin-Zuweisung (Import von Schaltplan-Netzlisten aus AutoCAD Electrical / EPLAN), automatische **Nagelbrett-Abwicklung (Nailboard)** für die 2D-Fertigungszeichnung. | **[NISCHE]** *(Elektrokonstruktion / Schaltschrankbau)* |
| **Schweißkonstruktion (Weldments)** | Spezieller Baugruppen-Typ mit 3 Prozessstufen: 1. **Vorbereitung** (Fasen/Freistellungen an Einzelteilen nur für das Schweißen), 2. **Schweißnähte** (Kehlnaht, Stumpfnaht, kosmetische Naht, Punktschweißen + Schweißnaht-Massenberechnung), 3. **Nachbearbeitung** (Fräsen/Bohren nach dem Schweißen – erscheint nicht in den Einzelteilzeichnungen!). | **[HÄUFIG]** *(im klassischen Stahl- und Maschinenbau sehr beliebt)* |

---

### 3. Blechkonstruktion (Sheet Metal)

*Inventor 2025 und 2026 haben die Blech-Oberfläche massiv modernisiert (neue Property-Panels für Lasche, Fläche, Schnitt und Konturrolle).*

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **Blechregeln (Sheet Metal Rules)** | Zentrale Steuerung von Blechstärke (`Thickness`), Material, K-Faktor / Biegungstabelle / Ausgleichsgleichung, Biegeradius, Eckfreistellungen (Rund, Quadratisch, Riss, Laser-Schweißspalt) und Biegefreistellungen. | **[KERN]** |
| **Blech-Features** | **Fläche (Face):** Basisblech aus geschlossener Skizze.<br>**Lasche (Flange):** Anbiegen an Kanten mit Winkel, Höhe, Biegungsposition (innen/außen/tangential), automatischer Gehrung bei benachbarten Laschen.<br>**Konturlasche (Contour Flange):** Offene Skizze als gebogenes Blechprofil extrudieren.<br>**Konturrolle (Contour Roll):** Gebogene Bleche über eine Rotationsachse.<br>**Übergangslasche (Lofted Flange):** Übergang z. B. von Eckig auf Rund (Trichter, Absaugungen) mit Abwicklung über Kant-Facetten oder Walzform.<br>**Falz (Hem):** Einfach, Tropfenform, Gerollt, Doppelt.<br>**Biegung (Fold):** Skizzenlinie auf ebenem Blech als Biegelinie falten.<br>**Schnitt (Cut):** Inkl. Option „Über Biegung schneiden“ und „Senkrecht zur Oberfläche schneiden“ (wichtig für senkrechte Laserschneidkanten!).<br>**Ecken:** Eckverbindung (Corner Seam), Eckenrundung, Eckenfase, Aufreißen (Rip). | **[KERN]** *(Fläche, Lasche, Konturlasche, Schnitt, Ecke)*<br>**[HÄUFIG]** *(Falz, Übergangslasche)* |
| **Abwicklung (Flat Pattern) & Export** | Automatische Berechnung der Abwicklung (Länge × Breite der Rohtafel für Stückliste), Biegelinien (oben/unten), Biegefolgen-Nummern, Kosmetische Mittellinien. Direkter Rechtsklick-Export der Abwicklung als **DXF oder DWG** mit konfigurierbarer Layer-Zuordnung (Außenkontur, Innenkontur, Biegelinie oben/unten) für Trumpf/Bystronic-Lasersoftware. | **[KERN]** |
| **Stanzwerkzeuge (Punch Tools)** | Platzieren von Umformwerkzeugen (Kiemen/Lüftungsschlitze, Sicken, Durchzüge, Einpressmuttern-Vorbereitungen) auf Basis von Skizzenpunkten; in der Abwicklung wahlweise als reale 3D-Geometrie, 2D-Skizzensymbol oder nur als Stanzmittelpunkt mit Werkzeug-ID und Winkel darstellbar. | **[HÄUFIG]** |
| **Abwickeln / Zurückfalten (Unfold / Refold)** | Gezieltes Aufbiegen einzelner Biegungen im 3D-Modell, um Schnitte oder Bohrungen über die Biegelinie hinweg einzubringen, und anschließendes Zurückfalten. | **[HÄUFIG]** |

---

### 4. Zeichnungen (2D Drawings `.idw` / `.dwg`) & Model-Based Definition (MBD)

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **Zeichnungsansichten** | Erstansicht (Base View), Parallelansichten (Projected), Hilfsansicht (Auxiliary), Schnittansicht (Section – voll, halb, versetzt, ausgerichtet; *in 2026 verbessert*), Detailansicht (Detail – rund/rechteckig, glatt/gezackt; *in 2026 mit besseren Projektionsoptionen*), Unterbrochene Ansicht (Break View für lange Wellen/Profile), Ausbruch (Break Out mit Tiefenreferenz), Überlagerungsansicht (Overlay für Positionsdarstellungen), Entwurfsansicht (2D-Skizze), Blechabwicklungsansicht. Schattiert, Verdeckte Kanten, Tangentialkanten, Gewindedarstellung. | **[KERN]** |
| **Bemaßung & Symbole (Annotations)** | Allgemeine Bemaßung, Basislinien-, Ordinaten- und Kettenbemaßungs-Sätze; Bohrungs- und Gewindeinfos (automatisch aus 3D-Feature ausgelesen!), Fasenbemaßung, Biegelinien-Infos (z. B. `ABWÄRTS 90° R2`), Stanz-Infos; Mittellinien, Symmetrielinien, Lochkreise; Oberflächensymbole (inkl. aktueller **ISO 21920**), Schweißsymbole (EN ISO 2553), Form- und Lagetoleranzen (GD&T nach ISO 1101 / ASME Y14.5), Bezugrahmenteile, Führungslinien-Text, Revisionstabellen & Revisionswolken. Modellbemaßungen direkt abrufen (Retrieve Dimensions). | **[KERN]** |
| **Stücklisten (BOM), Teilelisten & Positionsnummern** | Bidirektionale Verknüpfung zwischen Baugruppen-BOM und Zeichnungs-Teileliste (Parts List): Strukturiert (alle Ebenen), Nur Bauteile (Parts Only); Mengen-Zusammenfassung, virtuelle Bauteile (z. B. Schmierfett, Lack), Kaufteile/Normteile/Phantom-Baugruppen. Automatische Positionsnummern (Balloons) mit Ausrichtung und Gruppierung. Bohrungstabellen und Biegungstabellen. | **[KERN]** |
| **Normen & Stile (Styles & Standards)** | Vollständige Vorlagen und Stilbibliotheken für **DIN, ISO, EN, ANSI, BSI, GB, GOST, JIS** (Projektionsmethode 1 / Europäisch vs. Projektionsmethode 3 / Amerikanisch, Schriftfelder, Linienbreitengruppen nach ISO 128, Bemaßungspfeile, Passungstabellen H7/g6 etc.). | **[KERN]** |
| **Model-Based Definition (MBD / 3D-Annotationen)** | Anbringen von 3D-Toleranzen, Bemaßungen, Oberflächen- und Form-/Lagetoleranzen (PMI – Product and Manufacturing Information) direkt am 3D-Bauteil und (*neu ausgebaut in 2025/2026*) auf Baugruppenebene. Integrierter **Toleranz-Berater (Tolerance Advisor)** prüft, ob alle Flächen normgerecht nach ISO GPS / ASME Y14.41 bestimmt sind. Export als interaktives **3D-PDF**, **STEP AP242** (mit PMI) und **JT**. | **[NISCHE]** *(Großindustrie/Automotive/Luftfahrt; im KMU- und Maker-Alltag dominiert weiterhin zu >95 % die 2D-PDF/DXF-Zeichnung)* |

---

### 5. Simulation, Kinematik & Generatives Design

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **Belastungsanalyse (Stress Analysis / Basis-FEM)** | Direkt in Inventor integrierte lineare statische Spannungsanalyse und Modalanalyse (Eigenfrequenzen): automatische Vernetzung (Tetraeder mit lokaler Netzverfeinerung), automatische und manuelle Kontakterkennung (Verbund, Trennung, Gleiten, Schrumpfpassung), Dünnwand-Erkennung (Schalenelemente), **Parametrische Dimensionierungsstudien** (Parameterbereiche variieren, Zielgröße z. B. Masse minimieren unter Einhaltung von $\sigma_{\text{zul}}$). | **[HÄUFIG]** *(schnelle Überschlagsrechnung für Konstrukteure)* |
| **Gestellanalyse (Frame Analysis)** | 1D-Balken-FEM speziell für mit dem Gestell-Generator erzeugte Rahmenkonstruktionen: extrem schnelle Berechnung von Durchbiegung, Normal-/Querkraft- und Biegemomentenverläufen sowie Knicklängen. | **[HÄUFIG]** *(für Schweißrahmen/Gestelle sehr nützlich)* |
| **Inventor Nastran (Add-in in PD&M Collection)** | Vollwertiger industrieller FEM-Solver im Inventor-Fenster: Nichtlineare Statik (Plastizität, große Verformungen), Thermische Analyse (stationär/transient) & Thermospannung, Lineares/Nichtlineares Knicken, Ermüdung (Fatigue), Stoß-/Falltest, Zufallsschwingungen, Verbundwerkstoffe (Composites). | **[NISCHE]** *(Berechnungsingenieure)* |
| **Dynamische Simulation (Dynamic Simulation)** | Echte physikalische Mehrkörper-Kinematik und -Kinetik: Übersetzt Baugruppen-Constraints automatisch in kinematische Gelenke, simuliert Schwerkraft, Federn/Dämpfer, 3D-Kontakt/Reibung, zeitabhängige Motoren/Kräfte/Momente. Zeichnet Weg-, Geschwindigkeits-, Beschleunigungs- und Kraftgraphen auf und übergibt die **zeitlich kritischsten Lastfälle direkt als Randbedingung in die FEM-Belastungsanalyse**. | **[NISCHE]** *(Sondermaschinen mit komplexer Kinetik)* |
| **Formgenerator (Shape Generator) / Generative Design** | **Lokal in Inventor:** *Shape Generator* (Topologieoptimierung eines Bauteils unter Lasten/Einspannungen und Ziel-Massenreduktion in %; erzeugt ein Referenz-Mesh, das der Konstrukteur manuell per Skizze nachzeichnet).<br>**Cloud (Autodesk Fusion):** Für echtes, fertigungsgerechtes *Generative Design* (gleichzeitige Berechnung von Fräs-, Guss- und 3D-Druck-Varianten mit direkten B-Rep/T-Spline-Ergebnissen) verweist Autodesk auf den Ein-Klick-Transfer zu **Autodesk Fusion**. | **[NISCHE]** *(Shape Generator gelegentlich für Leichtbau/3D-Druck)* |

---

### 6. Präsentationen, Explosionsdarstellungen, Rendering & Studio

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **Präsentationen (`.ipn`)** | Eigene Dateiumgebung für **Explosionsdarstellungen** und Montageanleitungen: Timeline-basiertes Drehbuch (Storyboard), Komponenten verschieben/drehen (Tweaks) mit Explosionspfaden (Trail Lines), Deckkraft-Steuerung, Kamerafahrten. *Neu in 2025:* „Modell ersetzen“ (Replace Model) direkt in der `.ipn`. Ausleitung von **Snapshot-Ansichten** für isometrische Explosionszeichnungen und Export als Video (MP4/WMV) oder Rasterbild. | **[HÄUFIG]** *(Explosionsansichten für Ersatzteilkataloge & Montagezeichnungen)* |
| **Inventor Studio & Viewport-Raytracing** | **Viewport:** Echtzeit-Schattierung mit Schatten, Umgebungsokklusion (AO), Spiegelungen, IBL-Umgebungen (Image-Based Lighting) und **GPU-Raytracing** (auf Basis von Autodesk RapidRT / DirectX Raytracing).<br>**Inventor Studio:** Dedizierte Umgebung für Standbild-Renderings und zeitachsenbasierte Animationen (Animation von Parametern, Abhängigkeiten, Ausblendungen, Kameras und Lichtquellen). | **[NISCHE]** *(Gelegentlich für Angebots- und Katalogbilder; für High-End-Marketing nutzen KMU meist Blender oder KeyShot)* |

---

### 7. iLogic, API, Add-ins, Automatisierung & Configurator

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **iLogic** | Tief integrierte Regel-Engine (auf Basis von VB.NET) zum Steuern von Parametern, Unterdrücken von Features/Komponenten, Tauschen von Teilen, Ausfüllen von iProperties, Steuern von Zeichnungsansichten und Stücklisten. Unterstützt **interne Regeln** (im Dokument gespeichert), **externe Regeln** (zentral im Netzwerk/Vault), **Ereignisauslöser** (z. B. *Vor dem Speichern*, *Nach Parameteränderung*, *Vor Vault Check-In* seit 2025) und einen Drag-&-Drop-**Formular-Generator** für Mini-Konfiguratoren.<br>**Neu in Inventor 2027: iLogic Code Blocks** – visuelle Block-Programmierung (ähnlich Scratch/Blockly), die parallel den echten iLogic-Code erzeugt. | **[HÄUFIG]** *(eines der stärksten Verkaufsargumente von Inventor im KMU-Umfeld!)* |
| **COM / .NET API & Add-ins** | Extrem umfangreiches Objektmodell (COM-basiert mit .NET-Interoperabilität), das nahezu 100 % aller Inventor-Funktionen programmatisch exponiert.<br>**Wichtiger Technologiewechsel (seit Inventor 2025):** Migration von Microsoft `.NET Framework 4.8` auf modernes **`.NET 8`** (Performance-Gewinn, erforderte Portierung alter Add-ins).<br>**VBA:** Weiterhin aus Kompatibilitätsgründen enthalten, aber für Neuentwicklungen zugunsten von iLogic / .NET 8 Add-ins abgeraten. | **[HÄUFIG]** *(für Automatisierung & Unternehmensanpassungen)* |
| **Headless / Design Automation** | **Aufgabenplanung (Task Scheduler):** Lokale Batch-Konvertierung, Migration, Drucken, iLogic-Ausführung (*seit 2026.2 mit Option zum Unterdrücken von iLogic/Events beim Batch-Lauf*).<br>**Inventor Server & APS Design Automation API:** Oberfläche-lose (`InventorCoreConsole.exe`) Engine für Web-Konfiguratoren in der Autodesk Platform Services (APS, ehemals Forge) Cloud. | **[NISCHE]** *(Enterprise / Web-Konfiguratoren)* |

---

### 8. Datenaustausch, AnyCAD, Vault/PDM & Cloud

| Funktionsbereich | Detaillierter Funktionsumfang in Inventor 2027 | Relevanz (KMU / Maker) |
| :--- | :--- | :--- |
| **Standard-Austauschformate (Import/Export)** | **B-Rep / Exakt:** STEP (AP203, AP214, AP242 inkl. PMI und Farben), IGES, Parasolid (`.x_t`, `.x_b` bis v36+), ACIS (`.sat`, `.sab`), Autodesk ShapeManager (`.smt`, `.smb`), JT (inkl. PMI), Pro/E Granite.<br>**Mesh / Visualisierung:** STL, **3MF**, OBJ, **glTF / GLB**, **USDz** (Universal Scene Description), DWF/DWFx.<br>**2D:** AutoCAD DWG (inkl. **DWG TrueConnect**: Inventor-Zeichnungen können nativ als `.dwg` gespeichert und direkt in AutoCAD geöffnet werden), DXF, PDF, Bilder. | **[KERN]** *(STEP, DXF/DWG, STL/3MF, PDF)*<br>**[HÄUFIG]** *(Parasolid, glTF)* |
| **AnyCAD (Assoziativer Fremdformat-Import)** | Referenzieren nativer CAD-Dateien aus **SolidWorks, PTC Creo, Siemens NX, CATIA V5, Alias, Rhino, Autodesk Fusion** sowie neutraler **STEP-Dateien** ohne Konvertierung: Ändert sich die Originaldatei auf dem Laufwerk, aktualisiert Inventor die Baugruppe, abhängige Skizzen und Zeichnungen automatisch unter Erhalt der Topologie-Referenzen. | **[HÄUFIG]** *(in Multi-CAD-Lieferketten extrem hilfreich)* |
| **BIM / Revit / IFC (AEC Exchange)** | Dedizierte BIM-Werkzeuge: Klassifizierung nach OmniClass/UniFormat und Revit-Familienkategorien, Anschlüsse für Elektro/HLK/Rohr definieren, Export als native **Revit-Projektdatei (`.rvt`)** (*seit 2025 auch abwärtskompatibel für ältere Revit-Versionen bis 2023!*) oder Revit-Familie (`.rfa`), sowie **IFC2x3** und **IFC 4x3** (*neu in 2026*). Assoziatives Referenzieren von großen Revit-Gebäudemodellen via AnyCAD. | **[NISCHE]** *(Zulieferer für Bauwesen, Gebäudetechnik, Stahlbau/Fassade)* |
| **PDM: Autodesk Vault** | **Vault Basic** (kostenlos in der Subscription enthalten): Check-in/Check-out, Versionierung, Dateisuche, Wo-verwendet-Nachweis (Where Used), Copy Design.<br>**Vault Professional** (kostenpflichtig): Revisionswesen, Freigabe-Lebenszyklen (Work in Progress -> Überprüfung -> Freigegeben), automatische PDF/DXF/STEP-Generierung bei Freigabe über Job-Prozessor, Änderungsaufträge (ECO), Artikelstamm- & Stücklistenverwaltung, ERP-Kopplung. | **[HÄUFIG]** *(im Mehrbenutzer-KMU ab 2–3 Konstrukteuren essenziell, da Dateireferenzen im Dateisystem sonst brechen)* |
| **Cloud (Autodesk Docs & Fusion)** | **Shared Views:** 3D-Modelle und 2D-Zeichnungen per Browser-Link mit Kunden teilen (Kommentare, Messen, Schnitte im Browser ohne Installation).<br>**Autodesk Docs / Desktop Connector:** Cloud-Laufwerks-Synchronisation.<br>**Fusion-Interop:** Direkte Übergabe von Inventor-Teilen an Autodesk Fusion für Cloud-CAM (Fräsen/Drehen), Generative Design, Elektronik-PCB-Integration und Spritzgusssimulation. | **[HÄUFIG]** *(Shared Views & CAM-Übergabe)* |

---

### 9. Was war in den letzten 3 Releases neu (2025–2027) – inkl. KI-Funktionen

#### **Autodesk Inventor 2025** *(Veröffentlicht im März 2024 – 25-jähriges Jubiläum, >140 Verbesserungen)*
* **Technologie-Umbau (.NET 8):** Kompletter Unterbau-Wechsel von `.NET Framework 4.8` auf **`.NET 8`** für höhere Ausführungsgeschwindigkeit und Zukunftssicherheit.
* **Modernisierte Blech-UI:** Komplett neue, kontextsensitive Property-Panels und interaktive 3D-Manipulatoren für *Fläche (Face)*, *Lasche (Flange)* und *Schnitt (Cut)*.
* **Finish-Feature-Ausbau:** Schnellere Performance und bessere Ableitbarkeit für Oberflächenbehandlungen/Lackierungen.
* **Revit-Abwärtskompatibilität:** Export von `.rvt`-Dateien für ältere Revit-Versionen (zurück bis Revit 2023) und neuer IFC-Import-Dialog.
* **Zeichnungen & Anordnungen:** Bessere Begrenzungssteuerung (Boundary) für Skizzen- und Feature-Muster, Zellen-Zusammenführung in Tabellen, Sicherheits-Scanner für iLogic-Regeln.

#### **Autodesk Inventor 2026 + Point-Releases 2026.1 / 2026.2 / 2026.3** *(Veröffentlicht März 2025 – Herbst 2025)*
* **Assoziatives Spiegeln in Baugruppen:** Gespiegelte Unterbaugruppen bleiben voll assoziativ mit der Quellbaugruppe (sowohl Geometrie als auch Positionsänderungen).
* **BIM & IFC 4x3:** Unterstützung für den neuesten Standard **IFC 4x3**, direkte Zuweisung von Revit-Kategorien im Bauteil-Browser und Koordinatensystem-Ausrichtung für den Revit-Export.
* **Unregelmäßige Muster & Bauteil-Vereinfachung:** Rechteckige und kreisförmige Anordnungen erlauben nun unregelmäßige Abstände/Auslassungen; der *Simplify*-Befehl steht nun auch direkt in Einzelteilen (`.ipt`) zur Verfügung.
* **Blech-Konturrolle & Eckrundung:** Migration von *Contour Roll* und *Corner Round* auf die moderne Property-Panel-Architektur, verbesserte Stanzwerkzeug-Bearbeitung.
* **Highlight aus 2026.1:** **„Referenz ersetzen“ (Replace Reference)** in 2D-Skizzen (verhindert das Aufplatzen von Skizzen nach Topologieänderungen) sowie Mehrfachauswahl beim *Passend*-Constraint und Massen-Größenänderung von Inhaltscenter-Schrauben.
* **Highlight aus 2026.2:** Umkehrbare Winkelbemaßungen in Skizzen, Direkt-Sprung aus der Parametertabelle zum referenzierten Bauteil und iLogic-Unterdrückung im Task Scheduler.

#### **Autodesk Inventor 2027 + Point-Release 2027.1** *(Veröffentlicht Frühjahr 2026 – Sommer 2026)*
* **Autodesk Assistant (KI-Assistent – Tech Preview):** Erstmals ist ein generativer KI-Assistent direkt in die Inventor-Benutzeroberfläche eingebettet (Text- und Spracheingabe). Er beantwortet Fragen zum geöffneten Modell, analysiert unbekannte Baugruppen, durchsucht Dokumenteigenschaften, schlägt Workflows vor und unterstützt beim Erstellen von Automatisierungsregeln.
* **iLogic Code Blocks:** Visuelle, knoten-/blockbasierte Programmierumgebung für iLogic-Regeln, die simultan den entsprechenden VB.NET/iLogic-Code generiert (senkt die Einstiegshürde für Nicht-Programmierer drastisch).
* **Nicht-modaler Parameter-Dialog (Modeless Parameters):** Einer der am häufigsten gewünschten „Just Do It“-Wünsche der Community: Das Parameterfenster blockiert nicht mehr den Arbeitsbereich, sondern bleibt offen, während man im Modell klickt, misst oder zwischen Dateien wechselt.
* **Browser-Ordner in Bauteilen:** Features im Bauteil-Modellbaum (`.ipt`) lassen sich nun genau wie in Baugruppen in benutzerdefinierten Ordnern gruppieren.
* **Multi-Sheet-Plot & Content Center:** Vereinfachtes Plotten von Zeichnungssätzen mit unterschiedlichen Blattformaten in einem Durchgang sowie Batch-Umbenennung.
* **Highlight aus 2027.1:** Während des Befehls *Abhängigkeit (Constraint)* blendet das Gedrückthalten der `Alt`-Taste temporär die Ursprungsebenen und -achsen der überfahrenen Komponenten ein – ein massiver Ergonomiegewinn beim Zusammenbauen.

#### **Bewertung der KI-Strategie von Autodesk in Inventor (Stand 2026):**
Obwohl Autodesk unter dem Label **„Autodesk AI“** stark wirbt, ist die KI-Integration in Inventor 2027 im Vergleich zu modernen Agenten-Ansätzen **eher konservativ und oberflächennah**:
1. Der *Autodesk Assistant* fungiert primär als konversationeller Co-Pilot für Dokumentation, Modellabfragen und Skript-Snippets.
2. Es gibt in Inventor **keinen nativen, bidirektionalen Agenten-Loop (wie MCP)**, über den ein externes LLM autonom komplexe Baugruppen konstruiert, Schnittbilder visuell prüft und Fehler selbstständig zurückrollt.
3. Autodesks tiefere KI-Forschung (wie *Project Bernini* für 3D-Shape-Generierung und automatisierte Zeichnungsableitung in *Fusion*) fließt primär in die Cloud-Plattform **Autodesk Fusion**, während Inventor aufgrund seiner 25 Jahre alten C++/COM-Desktop-Architektur nur schrittweise modernisiert wird.

---

### 10. Systemvoraussetzungen, Geometrie-Kernel & Lizenzmodell

* **Systemvoraussetzungen (Inventor 2027):**
  * **Betriebssystem:** Ausschließlich **64-Bit Microsoft Windows 11** (kein macOS, kein Linux, kein Web-Client).
  * **CPU:** Empfohlen $\ge$ 3,0 GHz, 4+ Kerne mit **AVX2 / AVX512**-Befehlssatz (Minimum: 2,5 GHz). Da viele klassische B-Rep-Feature-Rekonstruktionen im Kern weiterhin stark Single-Thread-limitiert sind, zählt hoher Single-Core-Boost-Takt mehr als reine Kernanzahl.
  * **RAM:** Empfohlen **32 GB bis 64 GB** (Minimum: 16 GB für Baugruppen $< 500$ Bauteile).
  * **GPU:** Empfohlen 8–16 GB VRAM mit $\ge$ 240 GB/s Speicherbandbreite, **DirectX 12** (Feature Level 12_0) für GPU-Raytracing (Minimum: 4 GB VRAM, DirectX 11).
  * **Festplatte:** ~40 GB freier Speicherplatz für die Installation (massiver Footprint!).
* **Geometrie-Kernel – Autodesk ShapeManager (ASM):**
  * Inventor nutzt **ShapeManager (ASM)**, Autodesks proprietären C++-B-Rep/NURBS-Kernel (derselbe Kern steckt auch in AutoCAD und Autodesk Fusion).
  * *Historie:* ASM entstand 2001 als offizieller Fork von **Spatial ACIS Version 7.0** (bevor Dassault Systèmes Spatial übernahm) und wird seitdem von Autodesk intern weiterentwickelt. Er ist extrem ausgereift bei komplexen Verrundungen (Fillets), Wandstärken (Shell) und Topologie-Heilung, aber ein reines Closed-Source-Blackbox-System.
  * Für den 2D/3D-Skizzierer und Baugruppen-Constraints setzt Autodesk zusätzlich auf eigene Solver-Komponenten in Kombination mit lizenzierten Industriestandards (historisch u. a. D-Cubed-Konzepte).
* **Lizenzmodell & Kosten (Stand 2026):**
  * **Reines Abonnement (Named User Subscription) oder Flex-Tokens** (keine Kauflizenzen mehr).
  * **Preise:** Einzel-Abo Inventor Professional liegt bei ca. **315 € / Monat** (bzw. ~216 $–300 $/Monat je nach Region), ca. **2.500 € – 2.700 € / Jahr** (inkl. MwSt. im DACH-Raum). In der **Product Design & Manufacturing Collection** (inkl. AutoCAD, Fusion, Inventor Nastran, Vault Basic) ca. **3.600 € / Jahr**.
  * **Schmerzpunkt für Maker, Startups & KMU:** Keine kostenlose Hobby-/Maker-Lizenz für Inventor (im Gegensatz zu Fusion), massiver Vendor-Lock-in durch proprietäre `.ipt`/`.iam`/`.idw`-Dateiformate (wer das Abo kündigt, kann seine nativen Konstruktionshistorien und Zeichnungen nicht mehr bearbeiten!).

---

## Teil B – Die Open-Source-Landschaft (Stand Oktober 2026)

### 1. Identifikation von „OpenCraft“ / „Open Craft“: Das *SolidCraft*- & *ArtCraft*-Ökosystem

Bei der Suche nach *„OpenCraft“* im Kontext von *„aktuelles, inspirierendes Open-Source-CAD-Projekt in Rust mit Fusion-360-Workflow“* liegt eine **Namensverschmelzung** vor, die in der Community (Hacker News, Reddit, 3D-Druck-Foren) aktuell häufig passiert: Gemeint ist **SolidCraft** (ursprünglich kurz unter dem Namen **SolveCraft** gestartet) sowie die eng verwandte Open-Source-Initiative **ArtCraft / CADCraft** (bei der alle 13+ Programme auf `-Craft` enden).

Hier sind alle relevanten Kandidaten im Detail aufgeschlüsselt:

#### **Kandidat 1 (Haupttreffer für 3D-CAD / Fusion-360-Nachbau): SolidCraft & SolidCore**
* **GitHub-Repository (Hauptanwendung):** https://github.com/tangency-labs/solidcraft *(Weiterleitung von https://github.com/bherbruck/solidcraft)*
* **GitHub-Repository (Neuer Rust-Kernel):** https://github.com/bherbruck/solidcore *(Status-Dashboard: https://tangency-labs.github.io/solidcore/)*
* **Webseite & Live-Web-App:** https://solidcraft.io | Web-App: https://solidcraft.io/app | Dokumentation: https://docs.solidcraft.io/
* **Lizenz:** **MIT OR Apache-2.0** (Dual-Lizenz, maximal permissiv, Clean-Room-Entwicklung).
* **Entwicklungsstand (Oktober 2026, Version 0.16.2):**
  * Über **7.080 GitHub-Stars**, extrem hohe Entwicklungsgeschwindigkeit.
  * **75 von 76 öffentlichen Referenzbauteilen** (`docs/oracle.md`) stimmen exakt mit den analytischen bzw. von FreeCAD berechneten Werten für Volumen, Oberfläche, Schwerpunkt und Bounding-Box überein.
  * **Beeindruckender Machbarkeitsnachweis (Showcase):** Der wissenschaftliche Rover **„SELENE“** (https://github.com/0xlillith/solidcraft-rover) wurde **vollständig durch einen KI-Agenten über den MCP-Server von SolidCraft konstruiert** – eine komplexe Baugruppe mit **3.323 editierbaren Timeline-Schritten** (Wanne, Räder, Fahrwerk, Greifarm, Solarflügel, Kameraturm), die fehlerfrei parametrisch neu berechnet wird.
* **Funktionsumfang (Was heute schon funktioniert):**
  * **Skizze & eigener Solver:** 2D-Skizzen auf Ursprungsebenen, Versatzebenen und Körperflächen; eigener zweistufiger Solver: 1. konstruktive Platzierung nach *Owen (1991)* und *Fudos–Hoffmann (1997)* (verhindert das „Umklappen“ von Skizzen bei Maßänderungen!), 2. numerischer Levenberg-Marquardt-Solver mit Jacobi-Rang-Prüfung für Freiheitsgrade. Auch 3D-Skizzenkurven (Schnittkurven, Projektionen).
  * **Volumen-Timeline:** Extrude, Revolve, Sweep, Loft, Fillet/Chamfer (inkl. variabler Radien, Sehnenlänge und G2-Ecken-Patches), Bohrungen, Gewinde (kosmetisch & ausmodelliert M3–M20), Muster, Spiegeln, Schale (Shell), Formschräge (Draft), Teilen, Prägen (Emboss).
  * **Blech (Sheet Metal) & Kunststoff-Features:** Laschen, Konturlaschen, Falze, Abwickeln/Zurückfalten, Blechregeln (K-Faktor, Freistellungen), Abwicklung mit exaktem DXF-Export und Biegungstabelle; plus Kunststoff-Features (Boss, Rib, Web, Lip/Groove, Snap Fit) für Elektronikgehäuse.
  * **Baugruppen & Kinematik:** Verschachtelte Komponenten/Occurrences, Gelenke (Rigid, Revolute, Slider, Cylindrical, Pin-Slot, Planar, Ball) inkl. geschlossener kinematischer Ketten (Viergelenk, Kurbelschwinge), Kurvenscheiben (`joint.cam`), Kontaktsätze, Bewegungsstudien (Motion Studies), Explosionsansichten und **URDF-Export** für Robotik-Simulatoren.
  * **Parameter & Konfigurationen:** Einheitenbewusste Ausdrücke (`2 * width + 5 mm`), Konfigurationstabellen (vergleichbar mit Inventor-Modellzuständen).
  * **Datenaustausch:** Eigenes `.solidcraft`-Containerformat + JSON; Import/Export von **STEP (AP203/214/242)**, **IGES 5.3**, **3MF** (inkl. B-Rep-Face-Tags), **STL**, **OBJ**, **glTF 2.0**, aktueller Kamera-Ansichtsexport als **2D-DXF** mit Verdeckte-Kanten-Berechnung (HLR), sowie Import von FreeCAD (`.FCStd`) und Rhino (`.3dm`) über das Schwesterprojekt **`cadmpeg`** (https://github.com/cadmpeg/cadmpeg).
* **Architektur (Blaupausen-Charakter für euer Projekt!):**
  * **100 % Pure Rust**, kompiliert nativ für Windows, macOS, Linux (Desktop-GUI mit `egui` + `wgpu`, inkl. nativer 3Dconnexion-SpaceMouse-Unterstützung) sowie im Browser via **WebAssembly (WebGPU/WebGL2)** und als **Headless CLI** (`solidcraft-cli`).
  * **Strikte 6-Schichten-Architektur (Cargo Workspace):**
    * `L0 (geom)`: Vektoren, Ebenen, Profile, Meshes, Maße.
    * `L1 (sketch, kernel, render)`: Eigener Constraint-Solver; B-Rep-Kernel-Kapselung (nutzt aktuell `truck` + eigene Kernel-Erweiterungen für Booleans, Blends und Flächen; parallel entsteht **`solidcore`** als Safe-Rust-Port von NVIDIAs SMLib!); eigener GPU-Compute-Shader-Tessellator (65 ms für 78 Referenzkörper!).
    * `L2 (doc)`: Parameter, Ausdrücke, Feature-Timeline, inkrementelle Neuberechnung und deterministisches Topologisches Naming (`lineage.rs` / `history_names.rs`).
    * `L3 (io)`: STEP/IGES/3MF/STL/DXF-Übersetzer.
    * `L4 (engine)`: Session-State & zentrale Command-Registry (**„Everything is a Command“** – jede Aktion ist ein JSON-Befehl wie `{"command": "solid.extrude", "params": {"distance": 20}}`).
    * `L5 (gpu, ui-egui, mcp)`: Austauschbares UI-Frontend und der eingebaute **MCP-Server** (`solidcraft-cli mcp`), der entweder headless läuft oder sich per `--connect 127.0.0.1:7878` live in die geöffnete Desktop-App einklinkt.
  * **Geplantes Plugin-System (`docs/plugins.md`):** Sandboxed **WebAssembly-Plugins über WIT (`solidcraft:plugin@1.0.0`)** – sowohl als One-Shot-Skripte als auch als echte parametrische Timeline-Features (`FeatureKind::Plugin`), die bei der Modell-Neuberechnung über dieselbe `run(command, args)`-Schnittstelle evaluieren.

#### **Kandidat 2 (Schwester-Ökosystem für 2D-CAD & Creative Suite): ArtCraft & CADCraft**
* **Webseite:** https://getartcraft.com | App-Übersicht: https://getartcraft.com/apps | https://cadcraft.org
* **GitHub-Repository (CADCraft):** https://github.com/storytold/cadcraft
* **Was es ist:** **ArtCraft** ist eine Open-Source-Suite aus 13+ nativen Rust-Anwendungen (`PhotoCraft`, `VectorCraft`, `FilmCraft`, `DesignCraft`, `WordCraft`, `GridCraft`, **`CADCraft`**), die als abofreie, lokale Alternativen zu Adobe und Autodesk entwickelt werden.
* **CADCraft im Detail:** Ein Clean-Room-Nachbau von **AutoCAD** in reinem Rust (`egui`, Lizenz `MIT OR Apache-2.0`). Beherrscht Befehlszeile (`L`, `@5<45`), Objektfänge, Layer, Bemaßungen, Schraffuren, Blöcke, Papierbereich-Layouts mit Viewports, PDF-Plot, natives Lesen/Schreiben von DXF und DWG (über `acadrust`), parametrische 2D-Constraints und besitzt – genau wie SolidCraft – einen eingebauten **MCP-Server (`cadcraft-cli mcp`)** für KI-Agenten.

#### **Kandidat 3 (Weitere Open-Source-Projekte mit ähnlichem Anspruch oder Namen):**
* **Chili3D** (https://github.com/xiangechen/chili3d | https://chili3d.com): Browser-basiertes 3D-CAD in TypeScript mit Ribbon-UI (optisch sehr nah an Inventor/Fusion), das OpenCASCADE (OCCT) nach WebAssembly kompiliert, Three.js für das Rendering nutzt und ein dynamisches Plugin-System inkl. Visueller Programmierung (Rete.js) und KI-Assistenten-Anbindung bietet.
* **Dune 3D** (https://github.com/dune3d/dune3d | https://dune3d.org): Leichtgewichtiges Desktop-3D-CAD (C++/GTK4, GPLv3) vom Entwickler von *Horizon EDA*, das den SolveSpace-Constraint-Solver (auch in 3D!) mit dem OpenCASCADE-Kernel (für STEP-Import/Export und Fillets/Chamfers) kombiniert.
* **CADmium** (https://github.com/CADmium-Co/CADmium): Frühes, inzwischen archiviertes lokales Browser-CAD-Experiment in Rust auf Basis des `truck`-Kernels (außerdem Name eines akademischen Text-to-CAD-Modells: https://github.com/chandar-lab/CADmium).
* *Hinweis zu wörtlichen „OpenCraft“-Repositories auf GitHub:* Projekte mit dem exakten Namen `opencraft` (z. B. https://github.com/dgunay/OpenCraft) sind ältere Voxel-/Minecraft-Engine-Klone in C/C++/Java und haben keinen Bezug zu parametrischem 3D-CAD.

---

### 2. Bestehende Open-Source-CAD-Projekte, Geometrie-Kernel & Solver als Baustein-Kandidaten

#### **A. Vollständige CAD-Systeme & Code-CAD-Frameworks**

1. **FreeCAD (Version 1.0 Ende 2024, Version 1.1 am 24. März 2026 veröffentlicht)**
   * **URLs:** https://www.freecad.org | https://github.com/FreeCAD/FreeCAD
   * **Stack & Lizenz:** C++ / Python, Qt-UI, Coin3D (OpenInventor-Szenegraph), OCCT-Kernel; Lizenz: **LGPL-2.0-or-later**.
   * **Stand 2026:** Mit **FreeCAD 1.0** wurden die zwei größten historischen Schmerzpunkte gelöst: Realthunders Algorithmus zur Entschärfung des *Topological Naming Problems (TNP)* wurde in den Hauptzweig integriert, und eine native **Assembly-Workbench** (auf Basis des neu entwickelten *OndselSolver*) samt einheitlichem Materialsystem wurde eingeführt. **FreeCAD 1.1 (März 2026)** brachte erstklassige Datum-Features (Koordinatensysteme, Ebenen, Achsen), interaktive 3D-Dragger/Manipulatoren im Viewport (für Extrude, Fillet, Chamfer mit transparenter Vorschau) und ein überarbeitetes CAM-Werkzeugsystem.
   * **Eignung als Baustein:** Einzelne Module wie **PlaneGCS** (2D-Skizzensolver) und **OndselSolver** (Baugruppen-Kinematik) sind unter LGPLv2+ exzellent wiederverwendbar. Die Gesamtanwendung leidet jedoch unter 20+ Jahren gewachsenem C++/Python/Qt/Coin3D-Code und inkonsistenten Workbenches.

2. **build123d & CadQuery (Code-CAD in Python)**
   * **URLs:** https://github.com/gumyr/build123d | https://build123d.readthedocs.io | https://github.com/CadQuery/cadquery
   * **Stack & Lizenz:** Python auf Basis von **`OCP`** (automatisch generierte `pybind11`-Python-Bindings für OpenCASCADE); Lizenz: **Apache-2.0**.
   * **Architektur:** Während *CadQuery* das Fluent-Builder-Pattern (angelehnt an jQuery) etablierte, bietet das modernere **build123d** sowohl einen zustandsbehafteten *Builder-Modus* (`with BuildPart(): ...`) als auch einen klaren *algebraischen Modus* (`part = Box(10, 10, 10) - Cylinder(2, 10)`) sowie mächtige 1D/2D/3D-Selektoren (`part.edges().filter_by(Axis.Z).group_by(Axis.Z)[-1]`).
   * **Bedeutung für euer Projekt:** `build123d` und `CadQuery` sind 2026 die **De-facto-Sprache für LLM-gestützte Bauteilgenerierung**, weil LLMs Python-Code und semantische Selektoren (`faces(">Z")`) viel zuverlässiger schreiben als fragile kryptische GUI-Makros.

3. **Zoo / KittyCAD (Zoo Design Studio, KCL & Engine)**
   * **URLs:** https://zoo.dev | https://github.com/KittyCAD/modeling-app | https://github.com/KittyCAD/kcl-lib
   * **Stack & Lizenz:** Frontend/App (`modeling-app`) in TypeScript/React + Rust/WASM (für den **KCL**-Compiler und Language Server) unter **MIT-Lizenz**; die eigentliche B-Rep/GPU-Geometrie-Engine läuft jedoch **proprietär in der Zoo-Cloud** (Streamt das 3D-Bild als WebRTC-Videostream an den Client).
   * **Was man davon lernen muss:** Das Konzept der **bidirektionalen Code-GUI-Synchronisation**: Jede Mausaktion im Viewport (Skizze zeichnen, Extrudieren) modifiziert in Echtzeit den menschenlesbaren **KCL-Quelltext (KittyCAD Language)**, und jede Code-Änderung durch Mensch oder KI-Agent aktualisiert sofort das Modell. Dadurch sind CAD-Projekte reine Textdateien und nativ Git-versionierbar.

4. **SolveSpace**
   * **URLs:** https://solvespace.com | https://github.com/solvespace/solvespace
   * **Stack & Lizenz:** C++, eigener kleiner NURBS/Mesh-Kernel und exzellenter 2D/3D-Constraint-Solver (`libslvs`); Lizenz: **GPL-3.0-or-later**.
   * **Einschätzung:** Extrem schlank (~50.000 Zeilen Code), blitzschneller Solver, aber der eigene Geometrie-Kernel unterstützt **keine Fillets/Chamfers an gekrümmten Kanten**, keinen nativen STEP-Import und degradiert bei komplexen Booleschen Operationen oft auf Dreiecksnetze. Zudem zwingt die **GPLv3** jedes einbindende Projekt unter strenges Copyleft.

---

#### **B. Geometrie-Kernel im Vergleich (Das Herzstück jedes CAD-Systems)**

| Kernel | Sprache & Lizenz | Reifegrad (B-Rep / NURBS) | Stärken | Schwächen / Risiken |
| :--- | :--- | :--- | :--- | :--- |
| **OpenCASCADE (OCCT 8.0)**<br>https://dev.opencascade.org<br>https://github.com/Open-Cascade-SAS/OCCT | **C++17**<br>LGPL-2.1 (+ Exception) | **Industriereif** (seit 1990er Jahren; v8.0 erschien 2025/2026) | Vollständiger B-Rep-Kernel: komplexe variable Fillets, Lofts, Sweeps, Booleans, Offset/Shell, **HLR (Hidden Line Removal für 2D-Zeichnungen!)**, ausgereifter STEP/IGES-Translator. In OCCT 8.0 modernisiertes C++17 und bessere Parallelisierung. | Riesige, historisch gewachsene C++-Codebasis (>2 Mio. LoC), eigenwillige Speicherverwaltung (`Handle()`), steile Lernkurve, manche Fillets/Booleans bei degenerierten Fällen instabil. |
| **NVIDIA `usd-brep` (SMLib)**<br>https://github.com/NVIDIA-Omniverse/usd-brep | **C++ / Python**<br>**Apache-2.0** | **Hoch (Kommerzielles Erbe)** | **Geheimtipp 2025/2026:** NVIDIA hat den kommerziellen **SMLib**-Kernel (von Solid Modeling Solutions) unter Apache-2.0 als Open Source veröffentlicht! Exakte NURBS/B-Rep-Geometrie, Booleans, Fillets, Shelling, Stitching, OpenUSD-Integration. | Stark auf das NVIDIA-Omniverse-Buildsystem (`repo_build` / Packman) zugeschnitten; kleinere freie Entwickler-Community als OCCT. |
| **SolidCore (Rust-Port von SMLib)**<br>https://github.com/bherbruck/solidcore | **Safe Rust**<br>Apache-2.0 / MIT | **Im Aufbau (~33 % portiert)** | Portiert NVIDIAs SMLib Einheit für Einheit nach 100 % Safe Rust (kein `unsafe`, kein Panic, `wasm32`-kompatibel) mit automatischem Differential-Testing (`1e-9` Genauigkeit) gegen den C++-Referenzkern. | Noch nicht End-to-End für Booleans/Fillets fertiggestellt (Stand Okt. 2026: Mathe-, NURBS- und Kurvenschicht fertig, Flächen/Topologie in Arbeit). |
| **Truck (`ricosjp/truck`)**<br>https://github.com/ricosjp/truck<br>https://truckkernel.com | **Pure Rust**<br>Apache-2.0 | **Mittel (Solides Fundament)** | Von der japanischen Firma RICOS entwickelt; sauber modulare Rust-Crates (`truck-topology`, `truck-modeling`, `truck-shapeops`, `truck-meshalgo`, `truck-stepio`), läuft nativ in WebAssembly und nutzt `wgpu`. | Allein noch kein vollwertiger Industriekern: komplexe Kantenverrundungen (Fillets), koplanare Booleans und komplexe Sweeps erfordern massive eigene Aufsätze (wie SolidCraft sie in `crates/kernel` bauen musste). |
| **Fornjot**<br>https://www.fornjot.app<br>https://github.com/hannobraun/fornjot | **Pure Rust**<br>0BSD / MIT / Apache-2.0 | **Eingestellt / Archiviert** | Sehr saubere Code-Architektur und Dokumentation. | **Wichtiges Mahnmal:** Der Autor musste das Projekt einstellen, weil der Bau eines eigenen B-Rep-Kernels von Grund auf für einen Einzelentwickler ohne bestehendes Mathe-Fundament zu groß war. |
| **Manifold (`elalish/manifold`)**<br>https://github.com/elalish/manifold | **C++20** (Bindings für Rust/Python/WASM)<br>Apache-2.0 | **Exzellent (aber nur für Meshes!)** | Garantiert topologisch wasserdichte Dreiecksnetze (Manifoldness), extrem schnelle und 100 % zuverlässige CSG-Booleans (Standard-Backend in modernem OpenSCAD und Blender). | **Kein analytischer B-Rep/NURBS-Kernel!** Zylindrische Flächen sind facettiert; kein echter STEP-Export mit analytischen Zylinderflächen, ungeeignet für klassische Maschinenbau-Fertigungszeichnungen. |

---

#### **C. Geometrische Constraint-Solver (2D Skizze & 3D Baugruppe)**

1. **PlaneGCS (FreeCAD Sketcher Solver)**
   * **Quelle:** Im FreeCAD-Repo unter `src/Mod/Sketcher/App/planegcs` (plus eigenständige Ports/WASM-Wrapper wie https://github.com/salus/planegcs).
   * **Lizenz:** **LGPL-2.0-or-later**.
   * **Technik:** C++17, nutzt DogLeg, Levenberg-Marquardt und BFGS sowie QR-/SVD-Zerlegung der Jacobi-Matrix zur exakten Bestimmung von Freiheitsgraden (DOF), überbestimmten (redundanten/widersprüchlichen) Constraints und Teilgraphen-Zerlegung. Sehr ausgereift für komplexe 2D-Maschinenbauskizzen.
2. **SolveSpace Solver (`libslvs`)**
   * **Quelle:** https://github.com/solvespace/solvespace | Rust-Crate: https://crates.io/crates/slvs | Python: https://pypi.org/project/py-slvs/
   * **Lizenz:** **GPL-3.0** (Achtung: infiziert das Gesamtprojekt mit GPLv3, sofern nicht als strikt getrennter Prozess über IPC/RPC angesprochen!).
   * **Technik:** Löst sowohl 2D- als auch echte 3D-Constraints (genutzt in SolveSpace und Dune 3D).
3. **Konstruktive Dekomposition + Levenberg-Marquardt (Der *SolidCraft*-Ansatz)**
   * **Technik:** Das größte Problem rein numerischer Solver (wie Newton-Raphson/LM allein) ist das **„Umklappen“ (Flipping / Branch Jumping)** einer Skizze, wenn man ein Maß von `20 mm` auf `150 mm` ändert. SolidCraft löst dies in reinem Rust (`crates/sketch`), indem zuerst ein **konstruktiver Graph-Solver nach Owen (1991) und Fudos–Hoffmann (1997)** Punkte und starre Cluster exakt auf dem bisherigen geometrischen Zweig (Branch) platziert und erst der verbleibende gekoppelte Rest per Levenberg-Marquardt gelöst wird.
4. **OndselSolver (ASMT – Assembly Constraints & MBD)**
   * **Quelle:** https://github.com/Ondsel-Development/OndselSolver
   * **Lizenz:** **LGPL-2.0-or-later**.
   * **Technik:** Speziell für 3D-Baugruppen-Gelenke (Joints) und Kinematik in FreeCAD 1.0/1.1 entwickelter C++-Solver.

---

#### **D. Das Topologische Naming-Problem (TNP) und wie man es löst**

**Was ist das Problem?**  
In einem B-Rep-Modell besteht ein Körper aus Topologie-Elementen (`Faces`, `Edges`, `Vertices`). Wenn Feature 1 ein Quader mit 6 Flächen (`Face[0]` bis `Face[5]`) ist und Feature 2 eine Fase auf `Edge[3]` platziert, passiert Folgendes, sobald der Nutzer zurück in die Skizze von Feature 1 geht und eine Nut hinzufügt: Der Kernel erzeugt beim Extrudieren nun 10 Flächen statt 6. Die internen Array-Indizes verschieben sich komplett – `Edge[3]` ist plötzlich eine völlig andere Kante, und die Fase (sowie alle darauf aufgebauten Skizzen und Baugruppen-Constraints) springt an eine falsche Stelle oder schlägt fehl.

**Die 3 Lösungsarchitekturen (Stand 2026):**
1. **OCCT `TNaming` (OCAF):** Das in OpenCASCADE eingebaute Framework speichert bei jeder Operation `Generated`, `Modified` und `Deleted`-Evolutionspaare von `TopoDS_Shape`s in einem Dokumentbaum. In der Praxis komplex zu bedienen und bei komplexen Booleschen Verschneidungen oft unvollständig.
2. **Realthunders ElementMap-Algorithmus (in FreeCAD 1.0 & 1.1 integriert):** Jedem Skizzenelement wird eine persistente ID zugewiesen. Jedes Feature kombiniert diese IDs hierarchisch zu String-Hashes (z. B. `Pad1;Sketch1:Edge3;F`), die durch Boolesche Operationen und Verrundungen propagiert werden. Bricht eine Referenz dennoch, rät FreeCAD nicht mehr stillschweigend irgendeinen neuen Index, sondern markiert die Referenz und bietet über geometrische Heuristiken Reparatur-Kandidaten an.
3. **Deterministische Kernel-Lineage & Nachbarschafts-Signatur (Der *SolidCraft*-Ansatz, `docs/book/src/dev/naming.md`):**
   * **Strikte Regel:** Niemals über abgetastete Geometrie-Schwerpunkte raten! („Nothing tells the user, which is the worst thing a CAD tool can do.“)
   * Jede Kernel-Operation gibt exakt zurück, aus welchen Quell-Flächen/-Kanten jede Ergebnisfläche entstanden ist (`crates/kernel/src/history.rs`).
   * Flächen erhalten semantische Herkunftsnamen: z. B. `F2:side:l4` (Seitenwand aus Linie `l4` von Feature 2), `F2:top` (Deckfläche), `F5:blend:<edge>` (Verrundungsfläche).
   * **Wird eine Fläche durch einen Schnitt in mehrere Stücke geteilt**, werden die Stücke nicht nach zufälliger Kernel-Reihenfolge nummeriert, sondern **durch ihre exklusiven Nachbarflächen unterschieden**: `F2:top#[F2:side:l4,F4:side:l4]`. Selbst wenn die Nut (`F4`) verschoben oder vergrößert wird, bleibt die Signatur der Nachbarflächen invariant!
   * **Kanten** haben keine eigene fragile ID, sondern werden als Schnitt zweier benannter Flächen adressiert: `<Face A>|<Face B>`.

---

### 3. KI in CAD: Stand der Technik 2026

Im Jahr 2026 hat sich im Bereich „KI für CAD“ eine klare Zweiteilung herauskristallisiert: **Polygon-Diffusionsmodelle** (wie Meshy, Tripo3D, Rodin) sind zwar für Gaming/Deko-Assets brauchbar, aber **für den Maschinenbau völlig wertlos**, da sie unpräzise Dreieckswolken ohne exakte Zylinderachsen, Passungen, Bohrungen oder Feature-Historie erzeugen.

Für konstruktives, fertigungsgerechtes 3D-CAD dominieren 2026 drei echte Paradigmen:

#### **1. Text-to-Parametric-Code (LLM generiert CadQuery / build123d / KCL)**
Statt eigene binäre Token-Formate (wie früher bei *DeepCAD* oder *SkexGen*) zu trainieren, nutzen moderne Modelle die Tatsache, dass große Sprachmodelle (Claude, Gemini, GPT, Qwen-Coder) bereits exzellent in Python, räumlicher Mathematik und Programmierlogik sind:
* **CAD-Coder (NeurIPS 2025/2026):** (https://openreview.net/forum?id=cad-coder / arXiv) Übersetzt natürliche Sprache über Chain-of-Thought-Planung (CoT) direkt in ausführbaren **CadQuery**-Code. Der Durchbruch gelang durch **Group Reward Policy Optimization (GRPO / Reinforcement Learning)** mit einer zweistufigen Belohnungsfunktion: 1. Kompiliert das Skript im OCCT-Kernel fehlerfrei zu einem validen B-Rep-Solid? 2. Wie klein ist die geometrische **Chamfer Distance** zur Zielgeometrie?
* **CAD-MLLM & CADFusion (2025/2026):** Multimodale Modelle (https://cad-mllm.github.io), die Textprompts, handgezeichnete Skizzen, Fotos oder verrauschte 3D-Scans/Punktwolken kombinieren und in parametrische Sketch-and-Extrude-Sequenzen überführen. *CADFusion* nutzt dabei einen iterativen **Visual Feedback Loop (VF)**: Das Modell rendert sein eigenes generiertes CAD-Teil aus mehreren Kamerawinkeln, bewertet es mit einem Vision-Language-Model (VLM) auf geometrische Fehler (z. B. Durchdringungen, fehlende Bohrungen) und korrigiert den Code.
* **Zoo Text-to-CAD & Zookeeper (`ML-ephant`):** (https://zoo.dev/text-to-cad) Kommerzieller API-Dienst und in *Zoo Design Studio* integrierter Agent (*Zookeeper*), der aus Prompts editierbaren **KCL-Code** und exakte B-Rep-STEP-Dateien generiert und bestehende Flächen im Modell per Prompt modifizieren kann.

#### **2. Agentic CAD über Model Context Protocol (MCP)**
Der größte praktische Durchbruch 2025/2026 für komplexe reale Konstruktionen (weit über einfache Einzelteile hinaus) ist die Steuerung von CAD-Systemen durch autonome Coding-Agenten über das **Model Context Protocol (MCP)**:
* **SolidCraft MCP (`solidcraft-cli mcp`):** Der aktuelle Referenzstandard für Open-Source-CAD (https://github.com/tangency-labs/solidcraft/blob/main/docs/mcp.md). Bietet dem Agenten nicht nur Schreibbefehle (`execute`, `batch` mit automatischem Transaktions-Rollback bei Fehlern!), sondern **geometrische Introspektions-Werkzeuge**:
  * `inspect_design` & `body_topology` (liefert alle Körper, Flächen-Normalen, Zylinderradien, Mittelpunkte und persistenten Flächennamen als kompaktes JSON).
  * `measure` (exaktes Volumen, Masse, Schwerpunkt, Mindestabstände, Kollisionsprüfung).
  * `screenshot` (mit Schnitt-Ebene `--section z=12` und transparenten Werkzeugkörpern, sodass ein multimodales LLM ins Innere einer Verschraubung oder Tasche schauen kann!).
  * **Dedizierte Agent-Skills (`skills/solidcraft-modeling`, `solidcraft-mechanisms`):** Geben dem LLM domänenspezifisches Ingenieurwissen (wie man Koordinaten berechnet, mit `measure` verifiziert und kinematische Gelenke aufbaut).
* **Zoo MCP Server (`zoo-mcp`):** (https://github.com/KittyCAD/zoo-mcp) Verbindet Claude/Cursor mit der Zoo-Engine, um KCL-Code zu schreiben, Geometriefehler abzufangen und STEP/STL zu exportieren.
* **FreeCAD MCP (`neka-nat/freecad-mcp`, `proximile/FreeCAD-MCP`):** (https://github.com/neka-nat/freecad-mcp) Startet einen lokalen RPC-Server in FreeCAD, über den Agenten Python-Code im Dokument ausführen, den Feature-Baum auslesen und Viewport-Screenshots abrufen.
* **Autodesk Fusion MCP (`Joe-Spencer/fusion-mcp-server`, `frankhommers/autodesk-fusion-mcp`):** Lokale Fusion-Add-ins, die die Fusion-Python/C++-API als MCP-Tools für Claude Code / Desktop bereitstellen.
* **Blender MCP (`ahujasid/blender-mcp`):** Sehr populärer MCP-Server (>10.000 Stars) für `bpy`-Steuerung, Szene-Inspektion und Rendering (allerdings Polygon-Modeling statt parametrischem Maschinenbau-CAD).

---

## Teil C – Strategische Empfehlung & Architektur-Blaupause für „Inventor neu gedacht“

### 1. Strategische Grundsatzentscheidung: Nicht das Rad (allein) neu erfinden!

Bevor ihr eine einzige Zeile Code schreibt, solltet ihr eine fundamentale strategische Abwägung treffen:
Mit **SolidCraft** (`tangency-labs/solidcraft`, `MIT OR Apache-2.0`) existiert seit 2025/2026 ein Projekt, das eure Kernvision (**Pure Rust, kein Legacy-Ballast, Command-zentriert, tief integrierter MCP-Agenten-Server, Wasm-Plugin-Architektur in Planung**) bereits zu einem beachtlichen Teil in exakt dieser Philosophie umgesetzt hat.

Ihr habt daher **zwei realistische Wege**:
* **Option 1 (Ökosystem-Aufbau / Fork / Upstream-Kooperation mit SolidCraft):** Ihr nutzt `SolidCraft` (MIT/Apache-2.0) als Basis-Plattform und konzentriert eure Ressourcen genau auf das, was SolidCraft für den harten **Inventor-Maschinenbau-Alltag** noch fehlt (insb. 2D-Normzeichnungen nach DIN/ISO, Inhaltscenter/Normteile-Bibliothek, Rahmengenerator-Plugin, Maschinenelemente-Assistenten, direkter Kernel-Adapter auf OCCT 8.0 / NVIDIA SMLib).
* **Option 2 (Eigenständige Neuentwicklung mit bewährtem Industriekern):** Ihr baut euer eigenes System von Grund auf, vermeidet aber den größten Fehler fast aller gescheiterten Open-Source-CAD-Projekte (wie *Fornjot*), indem ihr **keinen eigenen B-Rep-Mathe-Kernel von Null auf programmiert**, sondern einen reifen Kernel (OCCT 8.0 oder NVIDIA SMLib) hinter einem strikten Rust-Trait kapselt.

Für beide Optionen gilt die folgende Zielarchitektur.

---

### 2. Empfohlene Systemarchitektur: „Command-First, Dual-Representation, Zero-Bloat“

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Mensch & KI-Agenten (Gleichberechtigt)               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐  │
│  │ Desktop/Web GUI     │  │ Eingebetteter       │  │ Externer Agent  │  │
│  │ (Viewport, Skizze,  │  │ KI-Co-Pilot (Chat,  │  │ via MCP Server  │  │
│  │  Timeline, Dialoge) │  │  Auto-Constraints)  │  │ (stdio / HTTP)  │  │
│  └──────────┬──────────┘  └──────────┬──────────┘  └────────┬────────┘  │
└─────────────┼────────────────────────┼──────────────────────┼───────────┘
              │                        │                      │
              ▼                        ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             Zentrale Command- & Transaktions-Engine (Rust)              │
│   • "Everything is a Command" (JSON-Schema-typisierte Operationen)      │
│   • Bidirektionale Synchronisation: Feature-Graph  <===>  Lesbare DSL   │
│   • Atomares Undo/Redo, Batch-Rollback, Deterministisches Replay        │
└─────────────┬───────────────────────────────────────────────┬───────────┘
              │                                               │
              ▼                                               ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────┐
│   Parametrischer Dokument-Kern (Core) │ │  WASM-Plugin-Host (Wasmtime)  │
│   • Parameter-DAG & Einheiten-Engine  │ │  • WIT-Interface (Sandboxed)  │
│   • 2D/3D-Skizzen-Solver              │ │  • Lazy-Loaded bei Bedarf:    │
│   • 3D-Assembly-Joint-Solver          │ │    - Blech (Sheet Metal)      │
│   • Deterministische Topologie-Namen  │ │    - Gestell-Generator (DIN)  │
│     (History Lineage + Nachbarschaft) │ │    - Schrauben & Normteile    │
└───────────────────┬───────────────────┘ │    - Zahnrad/Wellen-Rechner   │
                    │                     │    - 2D-Zeichnungsableitung   │
                    │                     │    - FEM / CAM-Brücke         │
                    ▼                     └───────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│               Abstraktes Geometrie-Kernel-Trait (`BRepKernel`)          │
│     • Strikt entkoppelt; gibt bei jeder Op Topologie-Historie zurück    │
├────────────────────────────────────┬────────────────────────────────────┤
│   Primär-Backend (Industriereif):  │   WASM-/Leichtgewicht-Backend:     │
│   • OCCT 8.0 (C++17 via cxx-FFI)   │   • Truck / SolidCore (Pure Rust)  │
│   • oder NVIDIA SMLib (Apache-2.0) │   • Manifold (für schnelle CSG-    │
│     für harte Fillets, STEP & HLR  │     Mesh-Vorschauen & 3D-Druck)    │
└────────────────────────────────────┴────────────────────────────────────┘
```

#### **Die 4 architektonischen Grundpfeiler:**

1. **Sprache & UI-Stack: Rust im Kern + `wgpu` Rendering**
   * **Warum Rust?** Absolute Speichersicherheit bei komplexen Topologie-Graphen, exzellente Performance (Rayon-Multithreading bei Tessellierung und Baugruppen-Auswertung), erstklassige Unterstützung für das **WebAssembly Component Model (WIT)** (ideal für das Plugin-System) und `cxx`-FFI zu C++-Kerneln.
   * **UI-Optionen:**
     * *Variante A (Nativ & Ultra-leichtgewichtig):* **`egui` + `wgpu`** (wie in SolidCraft) oder **Slint / Iced** + `wgpu`-Viewport. Startet in $< 0,5$ Sekunden, verbraucht $< 100\text{ MB}$ RAM (statt 40 GB Installation und 4 GB Leerlauf-RAM bei Inventor!), läuft identisch auf Linux, Windows, macOS und im Browser.
     * *Variante B (Web-Tech-Desktop):* **Tauri v2** (Rust-Backend) + TypeScript/React für komplexe Dock-Panels/Tabellen, während der 3D-Viewport direkt über einen nativen Rust-`wgpu`-Surface gerendert wird.

2. **„Everything is a Command“ & Duale Repräsentation (GUI $\leftrightarrow$ Lesbare DSL)**
   * In Inventor sind GUI-Klicks, die COM-API und das binäre `.ipt`-Dateiformat drei völlig getrennte Welten.
   * **Neu gedacht:** Jede Modellieraktion ist ein strikt typisierter, deklarativer Befehl im Feature-Graphen. Das Dateiformat ist kein binärer Blackbox-Container, sondern ein **menschen- und Git-lesbares Text-/JSON-Format (oder eine kompakte DSL wie KCL)** plus optionalem Geometrie-Cache (`.brep`/Mesh) für sofortiges Öffnen ohne Re-Evaluation.
   * Dadurch arbeiten Maus-Bediener, Skript-Entwickler, Plugins und KI-Agenten auf **exakt derselben Schnittstelle**.

3. **Modulare Plugin-Architektur („Zero-Bloat“ durch WebAssembly Components)**
   * Warum ist Inventor 40 GB groß und überfrachtet? Weil Rohrleitungsbau, Kabelbaum, Spritzguss-Lüftungsgitter, BIM-Revit-Export, Nastran-FEM und Gestellgenerator fest in denselben monolithischen Adressraum geladen werden.
   * **Lösung:** Der **Core** enthält *ausschließlich*: Dokumentmodell, Parameter/Gleichungen, 2D/3D-Skizzierer, Basis-Volumenkörper (Extrude, Revolve, Loft, Sweep, Fillet, Chamfer, Hole, Shell, Pattern, Boolean), Baugruppen mit Joints und STEP/STL/3MF-I/O.
   * Alle Fachmodule (**Blech**, **Rahmengenerator**, **Normteile/Inhaltscenter**, **Wellen-/Zahnradberechnung**, **Schweißbaugruppen**, **FEM**) werden als **WebAssembly-Komponenten über `wasmtime` und WIT (`Component Model`)** implementiert:
     * **Lazy Loading:** Das Blech-Plugin wird erst in der Millisekunde geladen, in der ein Dokument ein Blech-Feature enthält oder der Nutzer den Blech-Tab aktiviert.
     * **Keine eigene Geometrie-Magie nötig:** Ein Plugin für Stirnräder oder Stahlbau-Rahmen muss keinen eigenen B-Rep-Kernel mitbringen – es implementiert die WIT-Funktion `evaluate(params) -> CommandList` und erzeugt darüber reguläre Skizzen-, Extrusions- und Schnitt-Kommandos im Host-Kernel!
     * **Crash- & Security-Isolation:** Ein fehlerhaftes Community-Plugin kann niemals die Hauptanwendung zum Absturz bringen oder ungefragt Dateien im System lesen.

4. **Tief integrierte KI-Agenten („Agent-Native CAD“ statt aufgeflanschtem Chatbot)**
   Damit ein KI-Agent wirklich wie ein erfahrener Konstrukteur in eurem System arbeiten kann, braucht er vier Dinge, die herkömmlichen CAD-APIs fehlen:
   * **Semantische Topologie-Abfragen (Semantic Selector Engine):** Ein LLM scheitert daran, `Face_ID_4829` im Raum zu erraten. Euer System muss über MCP semantische Abfragen bieten (inspiriert von `build123d` + `SolidCraft`):  
     *„Gib mir alle ebenen Flächen mit Normalenvektor $+Z$, deren Fläche $> 50\text{ mm}^2$ ist“* oder *„Finde alle scharfen konvexen Außenkanten der Deckfläche“*.
   * **Transaktionale Batch-Ausführung mit Auto-Rollback & Diagnose:** Der Agent schickt 15 Konstruktionsschritte als `batch`. Schlägt Schritt 11 fehl (z. B. `Fillet radius 8 mm too large for wall thickness 5 mm on edge F2:top|F2:side:l1`), rollt die Engine automatisch auf den sauberen Zustand zurück und gibt dem Agenten eine **mathematisch präzise Fehlermeldung** zurück, mit der er sich selbst korrigiert.
   * **Multimodales Visuelles Feedback (Visual Self-Check):** Eine eingebaute Headless-Snapshot-Funktion rendert für den Agenten in $< 50\text{ ms}$ eine 4-Ansichten-Übersicht (Isometrisch, Vorne, Oben, Schnittansicht durch kritische Bohrungen) mit eingeblendetem Koordinatenkreuz und Bemaßungs-Labels.
   * **Konstruktions-Wissens-Agenten (Design Rules & DFM-Critics):** Spezialisierte Sub-Agenten prüfen im Hintergrund automatisch Fertigungsregeln (Design for Manufacturing): *„Achtung: Diese M6-Senkschraube hat nur 1,2 mm Randabstand zur Außenkante“*, *„Diese Innenecke einer Frästasche hat Radius 0 mm – soll ich automatisch Freistiche oder $R3$-Radien anlegen?“* oder *„Für diese 200 N Last auf dem Alu-Profil reicht ein 30×30-Nutprofil (Durchbiegung 0,18 mm)“*.

---

### 3. Was gehört in das MVP (Minimum Viable Product)?

Um den **Maschinenbau-Alltag von Einzelanwendern, Makern und KMU (Sondermaschinen, Vorrichtungen, 3D-Druck, Fräs-/Dreh-/Laserteile)** zu 80 % abzudecken, sollte das MVP streng fokussiert sein:

#### **In das MVP (Pflichtumfang):**
1. **Parametrische Basis & Dateiformat:**
   * Parameter-Tabelle mit Einheiten (`mm`, `deg`, `kg`) und mathematischen Ausdrücken.
   * Lesbares, Git-freundliches JSON/DSL-Dokumentformat + Crash-sicheres Autosave.
2. **2D-Skizzierer (Auf Ebenen & Bauteilflächen):**
   * Linie, Rechteck, Kreis, Bogen, Langloch, Polygon, Konstruktionslinien.
   * Projektion von Körperkanten (assoziativ mit „Referenz ersetzen“-Reparaturdialog).
   * Stutzen (Trim), Versatz (Offset), Skizzen-Rundung/Fase.
   * Constraints: Koinzident, Parallel, Lotrecht, Tangential, Horizontal/Vertikal, Symmetrisch, Gleich, Konzentrisch + Bemaßungen + vollständige Freiheitsgrad-Farbanzeige.
3. **Volumen-Modellierung (Part & Multibody):**
   * Extrusion (Join, Cut, Intersect, New Body), Drehung (Revolve), Sweep, Loft.
   * Bohrungswizard (metrische ISO-Durchgangs-/Sackloch-/Gewindebohrungen, Senkungen M2–M30).
   * Abrundung (Fillet) und Fase (Chamfer), Schale (Shell), Lineare/Kreisförmige Muster, Spiegeln.
   * Arbeitsebenen, -achsen, -punkte.
   * **Direct Edit Move/Delete Face** (extrem wichtig, um importierte STEP-Kauf-teile schnell anzupassen!).
4. **Leichtgewichtige Baugruppen (Assemblies):**
   * Komponenten einfügen (intern & extern referenziert), Unterbaugruppen.
   * **Joint-basierter Ansatz (wie Fusion/Onshape/SolidCraft):** Statt 3 einzelner Constraints pro Schraube primär *Starr, Drehung, Schieber, Zylindrisch, Planar* + klassisches *Passend/Fluchtend* für Sonderfälle.
   * Kollisionsprüfung (Interference Check) & Schnittansicht im 3D-Viewport.
5. **Fertigungs-Output (Der Mindestweg in die Werkstatt):**
   * **STEP (AP242)** Import & Export (inkl. Baugruppenstruktur und Farben).
   * **3MF & STL** Export (für 3D-Druck).
   * **DXF-Flächen- & Ansichtsexport:** Rechtsklick auf jede beliebige ebene Bauteilfläche $\rightarrow$ *„Als exakte 2D-DXF exportieren“* (deckt 90 % aller Laser-/Wasserstrahl-/CNC-Plattenbauteile ab, noch bevor ein komplettes 2D-Zeichnungsmodul fertig ist!).
6. **Agenten-Schnittstelle (MCP Server + CLI):**
   * Vollständiger MCP-Server (`execute`, `batch`, `inspect_design`, `body_topology`, `measure`, `screenshot`, `export`) ab Tag 1.

#### **Bewusst NICHT ins MVP (sondern als Phase-2-Plugins):**
* Vollständiger 2D-Zeichnungsableitungs-Editor nach DIN/ISO (erst in Phase 2, siehe Risiko 4).
* Blech-Abwicklung mit K-Faktor (als erstes offizielles Core-Plugin in Phase 2).
* Gestell-Generator (DIN-Stahlbauprofile) & Schrauben-Inhaltscenter (ideale erste Community-/WASM-Plugins!).
* T-Splines/Freiform, Rohrleitungs-Routing, Kabelbaum, integrierte FEM, Raytracing-Studio (alles weglassen bzw. an spezialisierte Open-Source-Tools wie Blender oder CalculiX/PrePoMax delegieren).

---

### 4. Die 5 größten technischen Risiken & wie ihr sie entschärft

| # | Technisches Risiko | Warum daran Projekte scheitern | Konkrete Gegenmaßnahme für euer Projekt |
| :--- | :--- | :--- | :--- |
| **1** | **Die „Geometrie-Kernel-Falle“**<br>*(Filleting, Booleans, Tangential-Verschneidungen)* | Ein eigener B-Rep-Kernel von Grund auf (NURBS-Flächenschnitte, Rolling-Ball-Verrundungen an 3+ Kanten, koplanare Booleans) kostet **30–50 Personenjahre** höherer numerischer Mathematik. Daran ist *Fornjot* gescheitert. | **Keinen Kernel bei Null starten!** Entweder:<br>1. **OCCT 8.0** (LGPL-2.1) oder **NVIDIA `usd-brep` / SMLib** (Apache-2.0!) als C++-Backend hinter einem sauberen Rust-Trait (`BRepKernel`) kapseln, oder<br>2. Direkt mit dem **SolidCraft / SolidCore**-Ökosystem (Rust-Port von SMLib + `truck`) zusammenarbeiten. |
| **2** | **Topologisches Naming-Problem (TNP)** | Sobald ein früheres Feature im Baum geändert wird, explodieren nachfolgende Skizzen, Fasen und Baugruppen-Gelenke. Wenn das passiert, verliert der Nutzer sofort das Vertrauen in das CAD-System. | **Von Tag 1 an ins Datenmodell einbauen:** Niemals Topologie über Indizes (`Face[4]`) oder Schwerpunkt-Sampling referenzieren. Jede Kernel-Operation muss eine `HistoryMap` liefern; Flächen werden über deterministische **Feature-Lineage + Nachbarschafts-Signaturen** benannt (wie in SolidCrafts `lineage.rs`). Bricht eine Referenz, darf das System *niemals* still raten, sondern muss einen klaren „Referenz neu zuweisen“-Dialog (bzw. MCP-Fehler) liefern. |
| **3** | **Skizzen-Solver-Stabilität & „Umklappen“ (Branch Jumping)** | Rein numerische Solver (Levenberg-Marquardt) finden bei großen Maßänderungen oft eine mathematisch gültige, aber spiegelverkehrte/umgeklappte Lösung – besonders tödlich, wenn KI-Agenten Parameter variieren! | **Zweistufiger Solver:** Vor den numerischen Solver (z. B. *PlaneGCS* oder eigener Rust-LM-Solver) einen **konstruktiven Graph-Dekompositions-Schritt** (nach *Owen 1991 / Fudos-Hoffmann 1997*) schalten, der Orientierungen (Vorzeichen von Kreuzprodukten) prüft und Schritte ablehnt, die eine Skizze umstülpen würden. |
| **4** | **2D-Zeichnungsableitung (HLR, Bemaßung, DIN/ISO)** | Im Maschinenbau ist eine 2D-PDF-Zeichnung mit Toleranzen, Schnitten und Gewindedarstellung (3/4-Kreis nach ISO) für jede Dreherei/Fräserei Pflicht. Exaktes **Hidden Line Removal (HLR)** auf gekrümmten NURBS-Flächen ist extrem schwer zu implementieren. | **Stufenplan:**<br>• *Stufe 1:* 2D-Flächen-DXF + Kamera-Ansichts-DXF mit HLR. Wenn ihr **OCCT 8.0** als Kernel-Backend nutzt, bekommt ihr den industriereifen **`HLRBRep_Algo`** (exakte analytische Projektion inkl. verdeckter Kanten und Silhouetten) kostenlos mitgeliefert!<br>• *Stufe 2:* Dediziertes 2D-Drawing-Workspace-Modul mit SVG/PDF-Renderer (z. B. via `typst` oder `krilla`/`pdf-writer` in Rust für gestochen scharfe DIN-Schriftfelder und Tabellen). |
| **5** | **Performance bei großen Baugruppen (>1.000 Teile) & STEP-Importen** | Ein zugekauftes Industrieventil als STEP-Datei hat oft 5.000 NURBS-Flächen. Wenn das UI oder die Tessellierung auf einem Thread läuft, friert das Programm Minuten ein. | • **Instancing im Szenengraph:** 500 gleiche DIN-912-Schrauben werden nur *einmal* im Kernel berechnet und per GPU-Instancing (`wgpu`) gerendert.<br>• **Parallele Tessellierung** über alle CPU-Kerne (`rayon`) + **GPU-Compute-Shader-Tessellierung**.<br>• Persistenter **Mesh-Cache** in der Projektdatei: Große Baugruppen öffnen in $< 1$ Sekunde im Ansichtsmodus (wie Inventors *Express Mode*), und nur aktiv bearbeitete Bauteile laden den schweren B-Rep-Graphen in den RAM. |

---

### 5. Realistischer Entwicklungsaufwand & Roadmap-Schätzung

Dank moderner KI-gestützter Softwareentwicklung (Coding-Agenten, automatisiertes Differential-Testing gegen Referenz-Kernel wie OCCT/FreeCAD/SMLib – genau die Methode, mit der *SolidCraft* und *SolidCore* in wenigen Monaten tausende Stunden klassischer C++-Entwicklung komprimiert haben) hat sich die Aufwandsgleichung im Jahr 2026 massiv verschoben. Dennoch bleibt 3D-CAD eine der anspruchsvollsten Domänen der Informatik.

| Entwicklungsphase | Inhalt / Meilensteine | Realistischer Aufwand (mit massivem KI-Agenten-Einsatz & bestehendem Kernel wie OCCT / SMLib / SolidCraft-Basis) | Aufwand *ohne* bestehenden Kernel (Eigenbau-B-Rep von Null) |
| :--- | :--- | :--- | :--- |
| **Phase 1: Fundament & Agent-Core (Monat 1–4)** | Command-Engine, JSON/DSL-Dokumentformat, Parameter-DAG, Kapselung des B-Rep-Kernels (OCCT 8.0 oder SMLib/Truck), deterministisches Topologisches Naming, Headless-CLI & **MCP-Server v1**, automatisierte Oracle-Testsuite gegen 100 Referenzteile. | **~1–2 Entwickler, 3–4 Monate** *(oder sofort verfügbar durch Aufbau auf `SolidCraft`!)* | *2–4 Jahre (hohes Scheiterrisiko)* |
| **Phase 2: Interaktives 3D-Part-MVP (Monat 5–9)** | `wgpu`-3D-Viewport (PBR, Schnittebene, Selektions-Picking), 2D-Skizzierer mit konstruktivem + numerischem Solver, Basis-Volumenfeatures (Extrude, Revolve, Fillet, Chamfer, Hole, Shell, Pattern), STEP/3MF/STL/DXF-I/O, Direct-Edit (Move/Delete Face), integrierter KI-Assistent im UI. | **~2–3 Entwickler, 4–5 Monate** | *+1–2 Jahre* |
| **Phase 3: Baugruppen & WASM-Plugin-System (Monat 10–15)** | Multi-Component-Baugruppen mit Joint-Solver, Kollisionsprüfung, **WASM/WIT-Plugin-Host**, erste 3 offizielle Plugins: **1. Blech (Sheet Metal + Flat-Pattern-DXF)**, **2. DIN/ISO-Normteile-Generator (Schrauben/Lager)**, **3. Gestell-Generator (Alu-Systemprofile & Stahlbau)**. | **~2–4 Entwickler, 6 Monate** | *+1–2 Jahre* |
| **Phase 4: 2D-Fertigungszeichnungen nach DIN/ISO (Monat 16–24)** | Assoziative 2D-Zeichnungsableitung (Basis-, Projektions-, Schnitt- und Detailansichten via HLR), Bemaßung, Passungen, Oberflächen-/Schweißsymbole, automatische Stücklisten (BOM) & Positionsnummern, PDF/DXF-Export. | **~2–4 Entwickler, 6–9 Monate** *(eines der arbeitsintensivsten UI-/Norm-Module!)* | *+1 Jahr* |

#### **Fazit für eure Roadmap:**
1. **Schaut euch sofort `SolidCraft` (https://github.com/tangency-labs/solidcraft) und `SolidCore` (https://github.com/bherbruck/solidcore) im Detail an.** Die Architektur von SolidCraft (`L0` bis `L5`, Pure Rust, „Everything is a Command“, deterministisches Naming, nativer MCP-Server, geplante WIT-WASM-Plugins, `MIT OR Apache-2.0`) deckt sich zu **über 90 %** mit eurer Zielvision.
2. **Entscheidet euch bewusst gegen Inventor-Legacy-Ballast:** Streicht iParts (nur Konfigurationstabellen/Modellzustände), ersetzt die 3-Klick-Constraint-Orgie in Baugruppen durch moderne **Joints** (mit optionalen Einzel-Constraints), ersetzt ein aufgeblähtes 40-GB-Inhaltscenter durch **parametrische, prozedurale WASM-Generatoren** (ein prozedurales DIN/ISO-Schrauben- und Profil-Plugin ist nur wenige Megabyte groß und generiert jedes Normteil on-the-fly!), und macht das Dateiformat von Tag 1 an **text-/JSON-basiert und Git-fähig**.
3. **Positioniert KI dort, wo Ingenieure wirklich Zeit verlieren:** Nicht beim „Erzeuge mir ein unscharfes 3D-Auto per Textprompt“, sondern bei **iterativer Konstruktionsarbeit über MCP**: *„Füge auf dem Flansch einen 6er Lochkreis für M6-Zylinderschrauben nach DIN 912 hinzu, senke die Bohrungen passend ab, platziere die Schrauben aus dem Normteile-Plugin und prüfe per Schnittbild, ob die Einschraubtiefe mindestens $1{,}5 \times d$ beträgt.“*

---

## Quellenverzeichnis (Verifizierte Direkt-URLs)

### Teil A – Autodesk Inventor (2025, 2026, 2027)
* **Inventor 2027 What's New (Offizielle Autodesk-Dokumentation):** https://help.autodesk.com/view/INVNTOR/2027/ENU/?guid=GUID-ECD996B8-D4E8-4B9B-9E4E-1F2A6B6F8A01 (sowie deutsche Hilfe: https://help.autodesk.com/view/INVNTOR/2027/DEU/)
* **Inventor 2027 Systemvoraussetzungen (Autodesk):** https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/System-requirements-for-Autodesk-Inventor-2027.html
* **Inventor 2026 What's New & Point Releases (2026.1 / 2026.2):** https://help.autodesk.com/view/INVNTOR/2026/ENU/ | Artaker CAD-Übersicht 2026.1/2026.2: https://www.artaker.com/de/blog/
* **Inventor 2025 Release Highlights (.NET 8 Migration, Blech-UI, Revit-Interop):** https://help.autodesk.com/view/INVNTOR/2025/ENU/ | Engineering.com Analyse: https://www.engineering.com/whats-new-in-autodesk-inventor-2025/
* **Autodesk ShapeManager (ASM) Kernel Hintergrund:** https://en.wikipedia.org/wiki/ShapeManager | https://www.autodesk.com/products/inventor/overview

### Teil B – OpenCraft / SolidCraft / ArtCraft & Open-Source-CAD-Landschaft
* **SolidCraft (Parametric 3D CAD in Pure Rust + MCP):** https://github.com/tangency-labs/solidcraft *(bzw. https://github.com/bherbruck/solidcraft)*
* **SolidCraft Offizielle Webseite, Web-App & Buch-Doku:** https://solidcraft.io | https://solidcraft.io/app | https://docs.solidcraft.io/
* **SolidCraft Architektur-, Naming-, Plugin- & MCP-Spezifikationen:**
  * Roadmap: https://github.com/tangency-labs/solidcraft/blob/main/ROADMAP.md
  * Persistent Naming: https://github.com/tangency-labs/solidcraft/blob/main/docs/book/src/dev/naming.md
  * MCP-Server & Agent-Skills: https://github.com/tangency-labs/solidcraft/blob/main/docs/mcp.md
  * WASM-Plugins (WIT): https://github.com/tangency-labs/solidcraft/blob/main/docs/plugins.md
  * SELENE Rover (3.323 Schritte per MCP gebaut): https://github.com/0xlillith/solidcraft-rover
* **SolidCore (Safe-Rust-Port des SMLib B-Rep-Kernels):** https://github.com/bherbruck/solidcore | Live-Status: https://tangency-labs.github.io/solidcore/
* **NVIDIA `usd-brep` (Open-Source SMLib NURBS/B-Rep-Kernel, Apache-2.0):** https://github.com/NVIDIA-Omniverse/usd-brep
* **cadmpeg (Open-Source Native CAD File Translator in Rust):** https://github.com/cadmpeg/cadmpeg
* **CADCraft (Open-Source AutoCAD-Alternative in Pure Rust + MCP):** https://github.com/storytold/cadcraft | https://cadcraft.org
* **ArtCraft & The Crafting Apps Suite:** https://getartcraft.com | https://getartcraft.com/apps
* **FreeCAD (Version 1.0 & 1.1 Release Notes):** https://www.freecad.org | https://github.com/FreeCAD/FreeCAD | https://wiki.freecad.org/Release_notes_1.0 | https://wiki.freecad.org/Release_notes_1.1
* **OpenCASCADE Technology (OCCT 7.8 / 7.9 / 8.0):** https://dev.opencascade.org | https://github.com/Open-Cascade-SAS/OCCT
* **Truck (Pure Rust B-Rep & NURBS Kernel by RICOS):** https://github.com/ricosjp/truck | https://truckkernel.com
* **Fornjot (Archiviertes Rust-B-Rep-Kernel-Experiment):** https://www.fornjot.app | https://github.com/hannobraun/fornjot
* **build123d & CadQuery (Python Code-CAD auf OCCT-Basis):** https://github.com/gumyr/build123d | https://build123d.readthedocs.io | https://github.com/CadQuery/cadquery
* **Chili3D (Browser-basiertes 3D-CAD mit OCCT-WASM & Three.js):** https://github.com/xiangechen/chili3d | https://chili3d.com
* **Dune 3D (Desktop 3D-CAD mit OCCT + SolveSpace-Solver):** https://github.com/dune3d/dune3d | https://dune3d.org
* **SolveSpace & `libslvs` Constraint Solver:** https://solvespace.com | https://github.com/solvespace/solvespace | Rust-Bindings: https://crates.io/crates/slvs
* **OndselSolver (C++ Assembly & MBD Solver, LGPLv2+):** https://github.com/Ondsel-Development/OndselSolver
* **Manifold (Topologisch exakte Mesh-CSG-Bibliothek):** https://github.com/elalish/manifold | https://manifoldcad.org
* **Zoo / KittyCAD (Zoo Design Studio, KCL & Text-to-CAD):** https://zoo.dev | https://github.com/KittyCAD/modeling-app | https://github.com/KittyCAD/kcl-lib

### Teil B.3 – KI in CAD (MCP-Server & Forschung 2025/2026)
* **Model Context Protocol (MCP) Spezifikation:** https://modelcontextprotocol.io
* **Zoo MCP Server:** https://github.com/KittyCAD/zoo-mcp
* **FreeCAD MCP Server:** https://github.com/neka-nat/freecad-mcp | https://github.com/proximile/FreeCAD-MCP
* **Autodesk Fusion MCP Server:** https://github.com/Joe-Spencer/fusion-mcp-server | https://github.com/frankhommers/autodesk-fusion-mcp
* **Blender MCP Server:** https://github.com/ahujasid/blender-mcp
* **CAD-MLLM (Multimodal Conditioned Parametric CAD Generation):** https://cad-mllm.github.io
* **CADmium (Fine-Tuning Code LLMs for Sequential CAD Design):** https://github.com/chandar-lab/CADmium
