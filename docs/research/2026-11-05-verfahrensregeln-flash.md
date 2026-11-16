> Gemini-3.8-Flash-Rohfassung mit Web, verifiziert. Recherche 2026-11-05. Zahlen und Zitate an den Primärquellen geprüft.

# Recherchebericht: Fertigungsverfahrensregeln für FDM-3D-Druck und CNC-Fräsen

Datum: 2026-11-05  
Status: Gemini 3.8 Flash, verifiziert  
Sprache: Deutsch  

Dieser Bericht dokumentiert die fertigungstechnischen Grundlagen und Kennwerte für die Erweiterung des automatischen Prüfwerkzeugs `check_design` in Mechvane (Issue #46). Behandelt werden:
1. FDM: Liegende Bohrungen (waagrechte Achse, Brückenbildung, Notwendigkeit von Stützstrukturen oder Tropfenform/Teardrop ab 5 bis 6 mm Durchmesser).
2. FDM: Vorlochbohrungen und Sacklochtiefe für Einschmelz-Gewindeeinsätze (Ruthex RX-Serie / CNC Kitchen) je M-Größe.
3. CNC-Fräsen: Innenradien von Kavitäten und Taschen vs. Fräswerkzeuge (Mindestradius, vertikale Kanten, scharfe 90°-Innenecken).
4. CNC-Bohren: Bohrtiefe im Verhältnis zum Durchmesser für Spiral-/Wendelbohrer (Standardgrenzwerte und Tieflochgrenzen).
5. CNC-Fräsen: Hinterschnitte (Undercuts, T-Nuten, Schwalbenschwanz, nicht von oben zugängliche Flächen).

---

## 1. FDM-3D-Druck: Liegende Bohrungen und Brückenbildung

### Eintrag: Liegende Bohrungen und Überhänge beim FDM-Druck
* **Aussage / Wert:** Bei horizontal liegender Zylinderachse (waagrecht zur Druckaufbaurichtung) bilden Bohrungen im oberen Scheitelbereich eine Brücke (Bridge). Bei Durchmessern über 5 mm tritt ohne Stützstruktur unzulässiges Durchhängen (Sagging) auf. Abhilfe bieten Stützstrukturen (Support), eine Änderung der Bauteilausrichtung um 90° oder die konstruktive Umgestaltung des oberen Bohrungsscheitels in Tropfenform (Teardrop) oder Rautenform (Diamond). In Mechvane prüft `check_design` horizontal liegende Bohrungen mit Durchmessern über diesem Grenzwert.
* **Geltungsbereich:** FDM-Druckverfahren, zylindrische Durchgangs- und Sacklochbohrungen mit horizontaler Achse.
* **Herkunft:** Fertigungsrichtlinie (Hubs FDM 3D Printing Guide).
* **Quelle:** [Hubs FDM Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
* **Stelle:** Abschnitt Bridging and horizontal-axis holes
* **Wörtliches Zitat:** „Bridging in FDM occurs when the printer is required to print between two supports or anchor points. Because there is nothing to build on, no support is offered for the initial layer being printed and the material tends to sag. Bridges most often occur in horizontal-axis holes found in the walls of objects or in the top layer (or roof) of hollow parts.“
* **Weiteres Zitat:** „Due to the nature of FDM, sagging or marks from support material are to some extent always present unless the bridge is less than 5mm.“
* **Weiteres Zitat:** „The best way to avoid support for holes is by changing the print orientation. Removal of support in horizontal-axis holes can often be difficult, but rotating the build direction 90° eliminates the need for support.“
* **Begründung:** FDM baut Bauteile schichtweise auf. Bei horizontalen Bohrungen nimmt der Überhangwinkel zur Bohrungsmitte hin stetig zu und erreicht im Scheitel 90° (horizontale Brücke). Ab einem Bohrungsdurchmesser von ca. 5 mm führt das Eigengewicht des extrudierten Schmelzstrangs ohne Stütze zu sichtbarem Durchhängen und Formabweichungen.
* **Härte:** Hinweis (Warnung mit Vorschlag Tropfenform oder Stütze).
* **Prüfstatus:** automatisch.

---

## 2. FDM-3D-Druck: Kernloch und Mindesttiefe für Gewindeeinsätze

### Eintrag: Vorlochgeometrie für Einschmelz-Gewindeeinsätze
* **Aussage / Wert:** Vorlochbohrungen für thermisch eingebettete Messing-Gewindeeinsätze (z. B. ruthex RX-Serie oder CNC Kitchen) müssen zylindrisch ausgeführt sein (keine Verjüngung / no draft) und bei Sacklöchern eine Tiefe von mindestens Einsatzlänge plus ca. 1 mm ($L + 1\text{ mm}$) aufweisen.
* **Geltungsbereich:** FDM-Druckteile aus Thermoplasten (PLA, PETG, ABS, ASA) mit Einschmelz-Gewindebuchsen M2 bis M8.
* **Herkunft:** Hersteller / Prüflabor (CNC Kitchen / ruthex).
* **Quelle:** [CNC Kitchen Tips and Tricks for Heat-Set Inserts](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts)
* **Stelle:** Design rules for blind holes and insert geometry
* **Wörtliches Zitat:** „A blind hole should be slightly deeper than the length of the insert (approx. 1 mm)“
* **Weiteres Zitat:** „Holes should be straight (not tapered)“
* **Weiteres Zitat:** „Normally, no chamfer is required at the hole edge“
* **Weiteres Zitat:** „Design rules: a blind hole roughly 1 mm deeper than the insert is long, straight rather than tapered holes, respect the minimum wall thickness, and normally no chamfer at the hole edge.“
* **Begründung:** Der Freiraum von 1 mm am Grund des Sacklochs verhindert, dass beim thermischen Einpressen verdrängtes thermoplastisches Schmelzgut den Gewindeeinsatz anhebt oder die Gewindegänge von unten zusetzt. Zylindrische Bohrungen sichern den gleichmäßigen Formschluss der Rändelung über die gesamte Länge.
* **Härte:** Fehler (bei Unterschreitung von Durchmesser oder Mindesttiefe für eine erkannte Gewindegröße).
* **Prüfstatus:** automatisch.

---

### Eintrag: Vorlochdurchmesser und Formschluss bei M3-Einsätzen
* **Aussage / Wert:** Der empfohlene CAD-Vorlochdurchmesser für Standard-M3-Einsätze beträgt 4,0 mm. Bei Bohrungsdurchmessern über 4,1 bis 4,2 mm sinkt die Auszugsfestigkeit drastisch ab.
* **Geltungsbereich:** Gewindeeinsätze Nenngröße M3 in FDM-gedruckten Bauteilen.
* **Herkunft:** Prüflabor / Hersteller (CNC Kitchen).
* **Quelle:** [CNC Kitchen Heat-Set Insert Datasheet Testing](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong)
* **Stelle:** CAD hole sizing and knurling engagement
* **Wörtliches Zitat:** „This again shows that our nominally suggested diameter of 4.0 millimeters on the packaging is actually a very good fit.“
* **Weiteres Zitat:** „The plastic locks into the knurling, it doesn’t stick to it“
* **Begründung:** Der Halt entsteht durch Hinterschnitt der Rändelstrukturen mit dem plastifizierten Thermoplasten. Ist die Bohrung zu groß, greifen die Rändelzähne nicht tief genug ins Material ein.
* **Härte:** Fehler.
* **Prüfstatus:** automatisch.

---

## 3. CNC-Fräsen: Innenradien von Taschen und vertikale Ecken

### Eintrag: Vertikaler Eckenradius in Frästaschen
* **Aussage / Wert:** Vertikale Innenkanten in gefrästen Taschen müssen verrundet sein. Der empfohlene Innenradius beträgt mindestens ⅓ der Kavitätentiefe (cavity depth). Scharfe 90°-Innenecken ohne Radius sind mit Standard-Schaftfräsern nicht fertigbar.
* **Geltungsbereich:** CNC-Fräsen von Taschen und Kavitäten in Aluminium, Stahl und Kunststoffen.
* **Herkunft:** Fertigungsrichtlinie (Hubs CNC Design Guide).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
* **Stelle:** Abschnitt Internal edges (Vertical corner radius)
* **Wörtliches Zitat:** „Recommended: ⅓ times cavity depth (or larger)“
* **Weiteres Zitat:** „Increasing the corner radii slightly above the recommended value (e.g. by 1 mm), allows the tool to cut following a circular path instead of a 90 angle. This is preferred as it results in a higher quality surface finish. If sharp 90-degree internal corners are required, consider adding a T-bone undercut instead of reducing the corner radius.“
* **Weiteres Zitat:** „Floor radius“
* **Weiteres Zitat:** „Recommended: 0.5 mm, 1 mm or no radius“
* **Begründung:** Schaftfräser sind rotierende zylindrische Werkzeuge, die an konkaven Innenecken zwangsläufig ihren Fräserradius abbilden.
* **Härte:** Fehler (bei scharfen Innenecken oder Innenradien unter dem Werkzeugmindestradius).
* **Prüfstatus:** automatisch.

---

## 4. CNC-Fräsen: Bohrtiefe und Wendelbohrer

### Eintrag: Maximale Bohrtiefe bei Spiral- und Wendelbohrern
* **Aussage / Wert:** Für CNC-gebohrte Bohrungen beträgt die empfohlene maximale Bohrtiefe das 4-fache des Nenndurchmessers ($4 \times d$). Typisch machbar mit Standard-Wendelbohrern ist eine Bohrtiefe bis zum 10-fachen Nenndurchmesser ($10 \times d$). Größere Tiefen erfordern Tieflochbohrwerkzeuge.
* **Geltungsbereich:** CNC-Bohren und Fräsen von zylindrischen Durchgangs- und Sacklöchern.
* **Herkunft:** Fertigungsrichtlinie (Hubs CNC Design Guide).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
* **Stelle:** Abschnitt Holes (Maximum depth)
* **Wörtliches Zitat:** „Recommended: 4 times nominal diameter“
* **Weiteres Zitat:** „Holes deeper than the typical value are machined using specialized drill bits (with a minimum diameter of 3mm). Blind holes machined with a drill have a conical floor (135-degree angle), while holes machined with an end mill tool are flat.“
* **Weiteres Zitat:** „For high-accuracy holes with a diameter smaller than 20 mm, using a standard diameter is recommended.“
* **Begründung:** Bei großen Längen-zu-Durchmesser-Verhältnissen neigen Spiralbohrer zum Auslenken (Verlaufen der Achse), und die Spanabfuhr aus der Spannut verschlechtert sich stark, was zu Spanverklemmung und Werkzeugbruch führen kann.
* **Härte:** Hinweis (Warnung bei Bohrtiefe $> 10 \times d$).
* **Prüfstatus:** automatisch.

---

## 5. CNC-Fräsen: Hinterschnitte (Undercuts)

### Eintrag: Hinterschneidungen und Zugänglichkeit
* **Aussage / Wert:** Hinterschnitte (Undercuts) sind Geometrien, die mit Standardwerkzeugen von oben (Werkzeugachse Z) nicht zugänglich sind. Sie erfordern Sonderwerkzeuge (z. B. T-Nutenfräser, Scheibenfräser) oder Mehrachs-Bearbeitung (4-Achs/5-Achs) und sollten als Hinweis gekennzeichnet werden.
* **Geltungsbereich:** CNC-Fräsen (3-Achs-Standardfräsmaschinen).
* **Herkunft:** Fertigungsrichtlinie (Hubs CNC Design Guide).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
* **Stelle:** Abschnitt CNC machining undercuts
* **Wörtliches Zitat:** „Undercuts are features that cannot be machined using standard cutting tools, as some of their surfaces are not accessible directly from above.“
* **Weiteres Zitat:** „There are two main types of undercuts: T-slots and dovetails. Undercuts can be one-sided or double-sided and are machined using special tools.“
* **Weiteres Zitat:** „When designing parts with undercuts on internal walls, remember to add enough clearance for the tool. A good rule of thumb is to add space equal to at least four times the depth of the undercut between the machined wall and any other internal wall.“
* **Begründung:** Bei der 3-Achs-Fräsbearbeitung erfolgt der Werkzeugzugriff ausschließlich entlang der Spindelachse von oben. Flächen, die nach unten zeigen oder durch überhängendes Material verdeckt sind, können mit geraden Schaftfräsern nicht kollisionsfrei erreicht werden.
* **Härte:** Hinweis (Warnung zur Fertigungsaufwandsprüfung).
* **Prüfstatus:** automatisch.
