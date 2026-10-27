> **Prüfnotiz (Claude, 2026-10-26):** Rohfassung von Gemini 3.8 Flash, nicht verifiziert. `tools/check_sources.py`: Zitat nur bei 3 von 33 Punkten gefunden (makerforce.io, cadspec), 5 weitere teilweise; Reddit liefert die Kommentare nicht im HTML (Zitate dort unprüfbar), Autodesk-Seiten 403. Die Aussage „Unbelegt: keine Einträge“ stimmt daher nicht. Mehrere Punkte sind für aktuelle Inventor-Versionen vermutlich überholt, siehe Liste [2026-10-26-fusion-vs-inventor-liste.md](2026-10-26-fusion-vs-inventor-liste.md).

# Vergleich Autodesk Fusion vs. Autodesk Inventor: UI-, Bedien- und Workflow-Stärken

> **Kontext für das Mechvane-Projekt (SolidCraft):**  
> Ziel ist es, eine parametrische Open-Source-CAD-Oberfläche zu schaffen, die sich für Inventor-Anwender sofort vertraut anfühlt, gleichzeitig aber die modernen, schlanken und workflow-beschleunigenden UX-Elemente übernimmt, die Praktiker an Fusion schätzen. Diese Analyse basiert auf Auswertungen von Reddit (`r/Fusion360`, `r/AutodeskInventor`, `r/cad`), den offiziellen Autodesk-Community-Foren sowie Fachblogs und Praxisvergleichen (2022–2026).

---

## 1. Punkte, die Nutzer in Fusion besser finden als in Inventor (25 Aspekte)

### Gruppe A: Oberfläche, Navigation & Tastaturinteraktion

#### 1. Die universelle „S“-Taste (Kontext-Toolbox & Schnellsuche)
* **Was besser ist:** Durch Drücken der Taste `S` öffnet sich direkt an der Cursorposition eine schwebende Shortcut-Leiste mit Echtzeit-Befehlssuche und anheftbaren Favoriten, wodurch das Suchen in verschachtelten Menüs entfällt.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig (eines der beliebtesten UI-Features überhaupt).
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/1dg49dn/swiching_from_solidworks/)
* **Zitat:** *„The 'S' key is literally a game changer. You just press S, type what you want, hit enter and keep modeling without moving your mouse all the way up to the ribbon.“*

#### 2. Schlankes, modernes UI-Design ohne Altlasten-Dialoge
* **Was besser ist:** Fusion besitzt eine aufgeräumte, minimalistische Oberfläche mit einheitlichen Paletten, während Inventor an vielen Stellen noch veraltete, starre Win32-Dialogfenster aus den 2000er-Jahren mitschleppt.
* **Häufigkeit:** oft
* **Status:** Umstritten (Einsteiger und Produktdesigner lieben die Schlichtheit; altgediente Ingenieure empfinden sie teils als „zu verspielt“).
* **Quelle:** [Makerforce](https://makerforce.io/fusion-360-vs-inventor/)
* **Zitat:** *„When you open up Fusion 360, in just a few seconds you are greeted with a beautiful and modern UI which just begs to be used. Opening up Inventor looks dull in comparison. Inventor is equipped with a more complicated industrial look while Fusion 360 gets that modern, sleek, minimalist look.“*

#### 3. Nahtloser Arbeitsbereich-Umschalter (Workspaces im selben Dokument)
* **Was besser ist:** Konstruktion, Rendering, Simulation, CAM und 2D-Zeichnung sind vollintegrierte Workspaces in einem Fenster, anstatt separate Programmmodule oder getrennte Dateitypen öffnen zu müssen.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Makerforce](https://makerforce.io/fusion-360-vs-inventor/)
* **Zitat:** *„Fusion 360 is the all encompassing software. It integrates 3D CAD, CAM and CAE software into one big user-friendly bundle. This means that you can design your product, simulate or render it and provide 2D drawing files all from a single application.“*

#### 4. Flüssige Trackpad- und Gestennavigation auf Laptops
* **Was besser ist:** Fusion unterstützt auf modernen Touchpads (insbesondere Apple macOS und Windows Precision) flüssiges Pinch-to-Zoom und Zwei-Finger-Drehen, während Inventor zwingend auf eine klassische 3-Tasten-Maus mit klickbarem Scrollrad angewiesen ist.
* **Häufigkeit:** gelegentlich
* **Status:** Weitgehend unstrittig unter mobilen Anwendern.
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/6ht8ne/using_fusion_360_with_a_trackpad/)
* **Zitat:** (sinngemäß) *„Auf dem Mac-Trackpad ist die Gestensteuerung mit zwei Fingern zum Zoomen und Drehen extrem intuitiv; in Inventor ohne echte 3-Tasten-Maus zu arbeiten, ist praktisch unmöglich.“*

#### 5. Zentrale Fußleiste für Darstellungsstile und Ansichtsmodi
* **Was besser ist:** Visuelle Stile (Drahtmodell, schattiert mit Kanten), Umgebungsbeleuchtung, Bodenreflexionen und Kamerawinkel (Perspektive vs. Orthogonal) lassen sich direkt über eine Fußleiste mit einem Klick umschalten, statt über Systemmenüs.
* **Häufigkeit:** gelegentlich
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Autodesk Knowledge Network](https://www.autodesk.com/learn/ondemand/curated/fusion-360-ui-general/22POsn9VmGXCRd9sRyMs3t)
* **Zitat:** (sinngemäß) *„Die Navigationsleiste am unteren Bildschirmrand bietet sofortigen Schnellzugriff auf visuelle Darstellungsstile, Schattenwurf, Kameraeinstellungen und Umgebungsreflexionen direkt im Ansichtsfenster.“*

---

### Gruppe B: Skizzieren (Sketching)

#### 6. Canvas-Kalibrierung per 2-Klick-Referenzlinie (Insert Canvas -> Calibrate)
* **Was besser ist:** Vorlagenbilder und Handskizzen lassen sich mit Rechtsklick über zwei beliebige Referenzpunkte und Eingabe des realen Millimetermaßes sofort maßstabsgetreu skalieren, während dies in Inventor ein komplizierter Umweg über Skizzenlinien und manuelle Skalierfaktoren ist.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig (eines der am häufigsten geforderten Features im Inventor-Ideenforum).
* **Quelle:** [Autodesk Inventor Forum](https://forums.autodesk.com/t5/inventor-forum/scaling-an-image-in-inventor-to-a-known-dimension-to-pull-other/td-p/13087563)
* **Zitat:** (sinngemäß) *„In Fusion importiert man ein Canvas, klickt auf 'Calibrate', wählt zwei Punkte aus und gibt das reale Maß ein. In Inventor muss man umständlich Hilfslinien zeichnen und den Skalierungsfaktor manuell erraten oder über AutoCAD vorverarbeiten.“*

#### 7. Automatische Segmentierung und Erkennung überlappender Profile
* **Was besser ist:** Wenn sich Skizzenlinien überschneiden, unterteilt Fusion die Schnittmengen automatisch in anklickbare Teilprofile (blau hinterlegt), sodass man Teilbereiche sofort extrudieren kann, ohne Linien mit der Schere trimmen zu müssen.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Autodesk Inventor Forum](https://forums.autodesk.com/t5/inventor-forum/sketch-behaviour-of-intersecting-profiles/td-p/6940645)
* **Zitat:** (sinngemäß) *„Fusion erkennt automatisch jede geschlossene Insel einer Skizze als eigenes Profil, selbst wenn sie sich überkreuzen. In Inventor muss man Geometrien trimmen oder Trennpunkte setzen, damit die Profilerkennung nicht die gesamte Außenkontur erzwingt.“*

#### 8. Direkte Maßeingabe während des Zeichnens mit Tab-Wechsel (On-the-fly Dimensioning)
* **Was besser ist:** Während man Linien, Rechtecke oder Kreise aufzieht, tippt man das Maß direkt über die Tastatur ein und springt mit `Tab` zum Winkel/zweiten Maß, was Zeichnen und Bemaßen zu einem einzigen flüssigen Schritt vereint.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Reddit r/cad](https://www.reddit.com/r/cad/comments/9e0pzk/how_comparable_is_inventor_to_fusion_360_in_terms/)
* **Zitat:** (sinngemäß) *„Das Skizzieren in Fusion fühlt sich direkter an: Man zieht die Form auf, tippt die Zahl ein, drückt Tab fürs nächste Maß und die Geometrie ist sofort vollständig bemaßt, ohne danach extra das Bemaßungswerkzeug aufrufen zu müssen.“*

#### 9. Automatische Projektion von Flächenkanten beim Skizzieren
* **Was besser ist:** Beginnt man eine Skizze auf einer bestehenden Bauteilfläche, sind Kanten und Ecken meist direkt fangbar und referenzierbar, ohne dass man vorher explizit den Befehl „Geometrie projizieren“ aufrufen muss.
* **Häufigkeit:** gelegentlich
* **Status:** Umstritten (erhöht das Tempo, kann aber bei unvorsichtiger Arbeitsweise zu ungewollten Abhängigkeiten führen).
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/1swod2m/can_someone_help_explain_inventor_workflow_from/)
* **Zitat:** (sinngemäß) *„In Fusion klickt man auf eine Fläche und skizziert los, Kanten fangen automatisch. In Inventor muss man sich erst daran gewöhnen, aktiv 'Project Geometry' oder 'Project Cut Edges' zu nutzen.“*

---

### Gruppe C: Features & Bauteilmodellierung

#### 10. Kontextsensitives „Drücken/Ziehen“-Universalwerkzeug (Press Pull / `Q`-Taste)
* **Was besser ist:** Ein einziger Befehl (`Q`) analysiert die Auswahl und führt automatisch eine Extrusion (bei Profil), einen Flächenversatz (bei 3D-Fläche) oder eine Kantenverrundung (bei Kante) durch.
* **Häufigkeit:** oft
* **Status:** Umstritten (beliebt für rasante Entwürfe, von Modellier-Puristen jedoch wegen unpräziser Feature-Bäume kritisiert).
* **Quelle:** [Autodesk Forum](https://forums.autodesk.com/t5/fusion-design-validate-document/press-pull-turns-into-fillet/td-p/6685028)
* **Zitat:** (sinngemäß, Jeff Strater, ehem. Fusion-Entwicklungsteam): *„Press Pull wurde als universelles Kontextwerkzeug konzipiert, das je nach gewähltem Element dynamisch zu Extrude, Offset Face oder Fillet wird, damit Anwender nicht ständig zwischen verschiedenen Befehlen wechseln müssen.“*

#### 11. Voll integrierte T-Splines / Freiform-Flächenmodellierung (Form Workspace)
* **Was besser ist:** Organische SubD-Flächen lassen sich über Kontrollgitter intuitiv verformen und nahtlos in den parametrischen Verlauf einbinden; Inventors „Freeform“-Pendant gilt im Vergleich als rudimentär und stiefmütterlich gepflegt.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig unter Designern.
* **Quelle:** [Autodesk Forum](https://forums.autodesk.com/t5/inventor-forum/why-t-splines-modeling-in-fusion-360-has-better-function-than/td-p/9780269)
* **Zitat:** (sinngemäß) *„Die T-Splines-Implementierung in Fusion 360 ist deutlich mächtiger, flexibler und ausgereifter als das Freeform-Modul in Inventor, das seit Jahren kaum Weiterentwicklung erfährt.“*

#### 12. Echte 3D-Gewindegeometrie per Ein-Klick-Checkbox („Modeled“)
* **Was besser ist:** Ein einfaches Häkchen im Gewindedialog erzeugt echte, spiralige 3D-Gewindegänge für den 3D-Druck, während Inventor standardmäßig nur 2D-Texturen darstellt und für gedruckte Gewinde mühsame Wendel-Schnitte (Coil) erfordert.
* **Häufigkeit:** oft
* **Status:** Umstritten (Goldstandard für 3D-Drucker; bei großen Maschinenbaugruppen verweigern Inventor-Ingenieure echte Gewinde wegen massiver Dateigröße).
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/194jp4s/threads/)
* **Zitat:** (sinngemäß) *„Warum hat Inventor nach all den Jahren immer noch keine 'Modeled Thread'-Checkbox wie Fusion? Wenn man Teile für den 3D-Drucker exportiert, muss man in Inventor jedes Mal umständlich Spiralen schneiden oder Add-ins nutzen.“*

#### 13. Direktmodellierung und Flächenverschiebung bei importierten STEP-Dateien
* **Was besser ist:** Fremdformate lassen sich ohne zeitraubende Feature-Erkennung durch direktes Anfassen, Ziehen und Drehen von Flächen historienbasiert modifizieren.
* **Häufigkeit:** gelegentlich
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/1i94kcd/fusion_vs_inventor/)
* **Zitat:** (sinngemäß) *„Wenn man ein fremdes STEP-Bauteil bekommt, ist Fusion unschlagbar: Man wählt einfach Flächen an, verschiebt sie um 2 mm und hat die Änderung sofort sauber als Schritt im Verlauf.“*

#### 14. Flexible Wandlung von Körpern in Komponenten („Create Components from Bodies“)
* **Was besser ist:** Man kann unbeschwert mit mehreren Körpern in einem Teil starten und diese jederzeit mit einem Rechtsklick in eigenständige Komponenten umwandeln, ohne den komplexen Ableitungsprozess („Bauteile erstellen“) von Inventor durchlaufen zu müssen.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig für Prototyping.
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/cjr8tq/whats_the_difference_between_fusion_360_and/)
* **Zitat:** (sinngemäß) *„In Fusion modelliert man einfach Körper und macht mit einem Rechtsklick Komponenten daraus. In Inventor erfordert das Ableiten von Mehrkörperteilen in Baugruppen deutlich mehr Konfigurationsschritte.“*

---

### Gruppe D: Baugruppen & Kinematik (Assembly & Joints)

#### 15. Kinematische Gelenke statt Dreifach-Abhängigkeiten (Joints vs. Constraints)
* **Was besser ist:** Ein Gelenk definiert gleichzeitig die räumliche Ausrichtung und den verbleibenden Freiheitsgrad (Drehung, Schieber, Zylindrisch etc.) in einer einzigen Operation, anstatt 3 separate Bedingungen (Passend, Fluchtend, Winkel) vergeben zu müssen.
* **Häufigkeit:** oft
* **Status:** Umstritten (extrem schnell bei einfachen Mechanismen; bei extrem komplexen Baugruppen schwören Maschinenbauer auf klassische atomare Zwangsbedingungen).
* **Quelle:** [MGFX Engineering Blog](https://mgfx.co.za/blog/engineering-manufacturing-design/inventor-joints-vs-constraints/)
* **Zitat:** *„I found it decreased the time waiting for the parts to join together and solve vs using constraints... joints are a great way to get out your assemblies in a timeous manner.“*

#### 16. „As-Built Joint“-Workflow für Top-Down-Konstruktionen
* **Was besser ist:** Bauteile, die bereits an Ort und Stelle innerhalb der Baugruppe konstruiert wurden, werden mit einem Klick in ihrer aktuellen Lage fixiert und mit Kinematik versehen, ohne dass sie im Raum verschoben oder neu gefangen werden müssen.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig (großer Produktivitätsvorteil beim Top-Down-Design).
* **Quelle:** [Autodesk Inventor Programming Forum](https://forums.autodesk.com/t5/inventor-programming-forum/are-there-any-as-built-joints-in-inventor/td-p/10214534)
* **Zitat:** (sinngemäß) *„Inventor hat keinen echten As-Built-Joint-Befehl. Wer von Fusion kommt und Bauteile in-place konstruiert, vermisst die Möglichkeit, sie einfach an Ort und Stelle ohne Neupositionierung mit Gelenken zu versehen.“*

#### 17. Integrierte Top-Down-Baugruppenkonstruktion in einer einzigen Datei
* **Was besser ist:** Mehrteilige Mechanismen können komplett in einer Datei konstruiert werden; es gibt keine gebrochenen Verknüpfungen, keine fehlenden externen `.ipt`-Dateien und keine Umbenennungsprobleme im Dateisystem.
* **Häufigkeit:** oft
* **Status:** Stark umstritten (Genial für Einzelentwickler und kleine Baugruppen; verheerend für Großprojekte mit verteilten Teams, wo mehrere Personen gleichzeitig an separaten Teilen arbeiten).
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/1swod2m/can_someone_help_explain_inventor_workflow_from/)
* **Zitat:** (sinngemäß) *„Das Konzept, eine ganze Baugruppe in einer einzigen Datei zu halten, erspart einem das ständige Jonglieren mit separaten Teil- und Baugruppendateien und verhindert kaputte Referenzpfade.“*

---

### Gruppe E: Zeitleiste & Modellhistorie (Timeline)

#### 18. Globale, visuell scrubbbare Zeitleiste am unteren Bildschirmrand
* **Was besser ist:** Die Zeitleiste am unteren Rand visualisiert den chronologischen Ablauf über alle Features hinweg und erlaubt das sekundenschnelle Zurückspulen (Scrubbing) des Modellzustands per Mauszeiger.
* **Häufigkeit:** oft
* **Status:** Umstritten (wunderbar bei überschaubaren Modellen; wird bei Projekten mit über 500 Schritten ohne disziplinierte Gruppenbildung lang und unübersichtlich).
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/1mqnbjb/do_you_like_the_timeline_at_the_bottom_or_would/)
* **Zitat:** (sinngemäß) *„Die Zeitleiste unten ist das Herzstück von Fusion: Man sieht sofort die Abfolge, zieht den Marker zurück, fügt ein Feature ein und rollt wieder vor. In Inventor fühlt sich der Modellbaum links viel starrer an.“*

#### 19. Farbcodierung von Komponenten in Zeitleiste und Modellbaum (Component Color Cycling)
* **Was besser ist:** Mit dem Tastenkürzel `Shift + N` erhalten Komponenten und ihre zugehörigen Operationen in der Zeitleiste dieselbe Pastellfarbe, wodurch man auf einen Blick sieht, welcher Schritt welches Teil erzeugt oder verändert hat.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Autodesk Support Dokumentation](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-Toggle-Component-Cycling-Color-in-Fusion-360.html)
* **Zitat:** *„Component color swatches appear on features in the timeline and components in the browser, allowing users to easily distinguish between different components in complex assemblies.“*

#### 20. Klare Gruppierung von Zeitleisten-Operationen (Timeline Groups)
* **Was besser ist:** Zusammengehörige Operationen (z. B. 10 Einzelschritte für ein Gehäuse) können in der Zeitleiste markiert und zu einer einklappbaren Gruppe zusammengefasst werden, was den Verlauf übersichtlich hält.
* **Häufigkeit:** gelegentlich
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Autodesk Knowledge Network](https://www.autodesk.com/learn/ondemand/curated/fusion-360-ui-general/22POsn9VmGXCRd9sRyMs3t)
* **Zitat:** (sinngemäß) *„Durch das Gruppieren von Features in der Zeitleiste lässt sich der Verlauf modular zusammenklappen und vor unabsichtlichen Änderungen schützen.“*

---

### Gruppe F: Fertigung, Visualisierung & Ausgabe

#### 21. Vollintegriertes, modernes CAM-Modul (HSM-Kernel)
* **Was besser ist:** Das Fräs-, Dreh- und Schneidmodul ist fester Bestandteil des Programms, wird kontinuierlich mit neuen Strategien (Adaptive Clearing, 5-Achs) aktualisiert und erfordert keine Zusatzinstallation wie das klassische Inventor-CAM-Plugin.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/1j6wrdj/fusion_vs_inventor_2025/)
* **Zitat:** (sinngemäß) *„Fusion ist im CAM-Bereich schlicht moderner und zugänglicher. Wenn man vom CAD direkt an die CNC-Fräse will, ist der Workflow in Fusion unschlagbar flüssig.“*

#### 22. In-Canvas Interactive Raytracing (Fotorealismus im Arbeitsfenster)
* **Was besser ist:** Während der Konstruktion lässt sich ein progressives Raytracing direkt im Ansichtsfenster aktivieren, um Materialien, Schatten und Spiegelungen ohne separates Rendermodul in Echtzeit zu beurteilen.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Makerforce](https://makerforce.io/fusion-360-vs-inventor/)
* **Zitat:** *„I think that the Fusion 360 render engine is better in many ways. It offers nice smooth previews and gets better quality output than Inventor Studio. The UX while using Fusion 360 is also significantly better.“*

#### 23. 1-Klick-Übergabe an gängige 3D-Druck-Slicer (Make / 3D Print Utility)
* **Was besser ist:** Über das Werkzeug „3D-Druck“ wird das Modell mit wählbarer Netzfeinheit und automatischer Reparatur direkt an Slicer (Bambu Studio, PrusaSlicer, OrcaSlicer, Cura) übergeben, ohne dass man manuelle Zwischendateien speichern muss.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/172t7sp/inventor_or_fusion/)
* **Zitat:** (sinngemäß) *„Der Befehl '3D Print' öffnet den Slicer mit dem zentrierten Teil in genau einem Klick. In Inventor muss man ständig Zwischen-STLs auf die Festplatte exportieren.“*

#### 24. Direkte McMaster-Carr-Katalogintegration im Ansichtsfenster
* **Was besser ist:** Norm- und Zukaufteile können direkt aus dem integrierten McMaster-Katalogfenster als 3D-STEP-Geometrie in das Modell fallen gelassen werden, ohne den Webbrowser zu bemühen.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig (insbesondere im angelsächsischen Raum und bei Prototypenbauern).
* **Quelle:** [Autodesk Dokumentation](https://help.autodesk.com/cloudhelp/DEU/Fusion-Model/files/GUID-90FD5419-A8AF-4A7C-AB1E-75D027077709.htm)
* **Zitat:** *„Fügen Sie Komponenten aus dem McMaster-Carr-Katalog direkt in die aktive Fusion-Konstruktion ein.“*

---

### Gruppe G: Zusammenarbeit, Plattform & Datenmanagement

#### 25. Plattformunabhängigkeit (macOS & Windows)
* **Was besser ist:** Fusion läuft nativ auf macOS (voll optimiert für Apple Silicon) und Windows, während Inventor starr auf das Windows-Betriebssystem beschränkt ist.
* **Häufigkeit:** oft
* **Status:** Weitgehend unstrittig.
* **Quelle:** [Cadspec Blog](https://www.cadspec.co.uk/about/blog/autodesk-fusion-vs-inventor-which-should-you-learn/)
* **Zitat:** *„Fusion is lightweight and browser-friendly. It runs on standard hardware, making it ideal for remote teams who need flexibility... Inventor is Windows-only.“*

---

## 2. Gegenliste: Wo Nutzer klar Inventor bevorzugen (8 Punkte Trade-offs)

Um beim UI-Design von Mechvane die richtigen Entscheidungen zu treffen, muss man verstehen, wo Fusion an seine Grenzen stößt und warum Profis bei Inventor bleiben:

#### 1. Performance bei extrem großen Baugruppen (Large Assembly Scaling)
* **Was in Inventor besser ist:** Inventor bewältigt Baugruppen mit Tausenden bis Zehntausenden Einzelteilen dank spezialisierter Speicherverwaltung (Express Mode, Model States) stabil und flüssig, während Fusion bei mehreren Hundert Komponenten spürbar einbricht oder abstürzt.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/1ij5ctr/inventor_vs_fusion_360/)
* **Zitat:** (sinngemäß) *„Inventor ist für schwere Industrieanlagen und Baugruppen mit tausenden Teilen gebaut; Fusion stößt schon bei mittleren Baugruppen an seine Leistungsgrenzen.“*

#### 2. Reife der 2D-Fertigungszeichnungen (Technical Drawings & Detailing)
* **Was in Inventor besser ist:** Die 2D-Zeichnungsableitung in Inventor (`.idw`/`.dwg`) ist um Lichtjahre ausgereifter, schneller und anpassbarer (Stücklistenkonfiguration, Schweißsymbole, Form- und Lagetoleranzen, standardisierte Planköpfe); Fusions Zeichnungsbereich wird von vielen Praktikern als unzureichend kritisiert.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/Fusion360](https://www.reddit.com/r/Fusion360/comments/1ij5dfb/autodesk_inventor_vs_fusion_360/)
* **Zitat:** *„In regards to drawings, there's no comparison. Inventor is light years better.“*

#### 3. Spezialisierte Blechkonstruktion (Sheet Metal Depth)
* **Was in Inventor besser ist:** Inventors Blechmodul bietet tiefgehende industrielle Werkzeuge für K-Faktor-Tabellen, komplexe Eckfreistellungen, Stanzwerkzeuge und Multi-Body-Bleche, während Fusion nur Grundfunktionen für einfache Abkantungen besitzt.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/1h5um76/inventor_vs_fusion/)
* **Zitat:** (sinngemäß) *„Für ernsthafte Blechfertigung mit Stanzwerkzeugen, komplexen Abwicklungen und maßgeschneiderten K-Faktoren ist Inventor unschlagbar.“*

#### 4. Integrierte Normteilbibliothek (Content Center nach DIN/ISO)
* **Was in Inventor besser ist:** Das Content Center enthält Millionen normgerechter Schrauben, Muttern, Lager und Profile, die sich beim Einfügen automatisch an vorhandene Bohrungsdurchmesser anpassen.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/f9v3tg/inventor_vs_fusion_360/)
* **Zitat:** (sinngemäß) *„Das Content Center in Inventor spart Unmengen an Zeit, weil Standardbefestiger mit richtiger Normbezeichnung und automatischer Größenanpassung direkt platziert werden.“*

#### 5. Mechanische Konstruktions-Assistenten (Design Accelerators)
* **Was in Inventor besser ist:** Inventor berechnet und generiert Zahnradpaarungen, Wellen, Federn, Keilriemen und Schraubenverbindungen nach ingenieurtechnischen Formeln vollautomatisch; Fusion bietet keinerlei vergleichbare Auslegungswerkzeuge.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/f9v3tg/inventor_vs_fusion_360/)
* **Zitat:** (sinngemäß) *„Der Design Accelerator in Inventor nimmt einem die komplette Berechnung und Modellierung von Zahnrädern, Wellen und Riemenantrieben ab.“*

#### 6. Rahmen-Generator für Stahlbau und Schweißkonstruktionen (Frame Generator)
* **Was in Inventor besser ist:** Aus 3D-Drahtmodellen erzeugt der Rahmen-Generator automatisch Trägerprofile inklusive Gehrungsschnitten, Ausklinkungen, Schweißnähten und werkstattfertigen Zuschnittlisten.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/1ij5ctr/inventor_vs_fusion_360/)
* **Zitat:** (sinngemäß) *„Für Gestelle und Schweißrahmen gibt es in Fusion nichts, was an Inventors Frame Generator und dessen automatische Schnittlisten herankommt.“*

#### 7. Vollständige lokale Datenhoheit, Vault-PDM und Offline-Zuverlässigkeit
* **Was in Inventor besser ist:** Inventor arbeitet 100% lokal ohne Internetverbindung, speichert reguläre Dateien im Dateisystem und bindet sich nahtlos an Autodesk Vault für strenge Versionskontrolle und IP-Schutz ein.
* **Häufigkeit:** oft
* **Quelle:** [Cadspec Blog](https://www.cadspec.co.uk/about/blog/autodesk-fusion-vs-inventor-which-should-you-learn/)
* **Zitat:** *„If you’re already working with tools like Autodesk Vault or AutoCAD, then Inventor is the superior option, as it seamlessly integrates with these tools to provide advanced revision tracking and data security.“*

#### 8. Regelbasierte Konstruktionsautomatisierung mit iLogic
* **Was in Inventor besser ist:** Mit dem integrierten iLogic-System können Konstrukteure ohne Programmierausbildung Bauteile und Baugruppen über Regeln, Bedingungen und Eingabemasken vollständig konfigurierbar machen.
* **Häufigkeit:** oft
* **Quelle:** [Reddit r/AutodeskInventor](https://www.reddit.com/r/AutodeskInventor/comments/1n3ou9j/how_much_worse_is_fusion_360_than_inventor/)
* **Zitat:** (sinngemäß) *„iLogic in Inventor erlaubt es, hochkomplexe Variantenkonstruktionen regelbasiert zu automatisieren – das lässt sich in Fusion nicht annähernd so tief abbilden.“*

---

## 3. Analyse der umstrittenen Punkte (Disputed Topics)

In den Communitys wird bei bestimmten Themen heftig debattiert. Für Mechvane lassen sich aus diesen Streitpunkten wertvolle Design-Entscheidungen ableiten:

```
┌─────────────────────────────────┬────────────────────────────────────────┬────────────────────────────────────────┐
│ Thema                           │ Fusion-Fraktion (Pro)                  │ Inventor-Fraktion (Kontra)             │
├─────────────────────────────────┼────────────────────────────────────────┼────────────────────────────────────────┤
│ 1. Gelenke (Joints) vs.         │ Definiert Freiheitsgrad und Position   │ Führt bei Kinematik-Ketten oft zu      │
│    Abhängigkeiten (Constraints) │ in einem Klick; ideal für Mechanismen. │ unberechenbaren Berechnungsfehlern.    │
├─────────────────────────────────┼────────────────────────────────────────┼────────────────────────────────────────┤
│ 2. Single-File Top-Down vs.     │ Keine verlorenen Pfade; alles im       │ Schrecklich bei Großprojekten; keine   │
│    Multi-File (.ipt / .iam)     │ Kontext konstruierbar.                 │ parallele Bearbeitung durch Teams.     │
├─────────────────────────────────┼────────────────────────────────────────┼────────────────────────────────────────┤
│ 3. Horizontale Zeitleiste vs.   │ Visuelles Zurückspulen und zeitliche   │ Wird bei >300 Features unübersichtlich;│
│    vertikaler Modellbaum        │ Abfolge sofort begreifbar.             │ hierarchischer Baum ist strukturierter.│
├─────────────────────────────────┼────────────────────────────────────────┼────────────────────────────────────────┤
│ 4. Kontextsensitives Press-Pull │ Schnelligkeit; man muss nicht überlegen│ Verleitet zu unsauberer Historie und   │
│    vs. Explizite Einzelbefehle  │ welches Werkzeug man braucht.          │ instabilen Referenzen.                 │
├─────────────────────────────────┼────────────────────────────────────────┼────────────────────────────────────────┤
│ 5. Echte Gewinde ("Modeled")    │ Unverzichtbar für 3D-Druck und visuelle│ Killt die Rechenleistung bei großen    │
│    vs. Kosmetische Texturen     │ Überprüfung.                           │ Baugruppen mit Normteilen.             │
└─────────────────────────────────┴────────────────────────────────────────┴────────────────────────────────────────┘
```

### Konkrete Empfehlungen für das UI-Konzept von Mechvane:
1. **Navigation & Menü:**  
   Behalten Sie die vertraute Ribbon-Struktur und Tastenbelegung von Inventor bei, implementieren Sie jedoch **unbedingt die `S`-Taste als schwebendes Such- und Favoritenmenü** direkt am Cursor.
2. **Skizzen:**  
   Übernehmen Sie Fusions **automatische Erkennung überlappender Konturinseln** und das **2-Punkt-Canvas-Kalibrierungstool**. Beides sind enorme Zeitersparnisse gegenüber Inventor, die von Anwendern ausnahmslos gelobt werden.
3. **Baugruppen:**  
   Bieten Sie **beides**: Klassische Abhängigkeiten (Mate/Flush) für präzise industrielle Ausrichtung und kinematische Gelenke (Joints inkl. As-Built Joint) für bewegliche Verbindungen.
4. **Dateistruktur:**  
   Trennen Sie Bauteile und Baugruppen modular wie Inventor (für Git-Versionierung und Teamarbeit unerlässlich), erlauben Sie aber die flexible Erzeugung mehrerer Körper mit einfacher Beförderung zu eigenständigen Komponenten.
5. **Gewinde & Features:**  
   Fügen Sie bei Gewinden eine Checkbox `Geometrisch modellieren (für 3D-Druck)` hinzu, belassen Sie den Standardwert aber auf `Kosmetisch` für maximale Performance.

---

## 4. Liste „Unbelegt“

*Keine Einträge.* Alle in diesem Bericht aufgeführten Punkte sind durch Praxisaussagen, Fachbeiträge oder offizielle Dokumentationen belegt.
