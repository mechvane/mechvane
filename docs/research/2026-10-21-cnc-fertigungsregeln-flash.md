> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: CNC-Fertigungsregeln für Fräsen und Drehen

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert  
Sprache: Deutsch  

Dieser Bericht fasst die maßgeblichen Konstruktionsrichtlinien für die spanende CNC-Fertigung (Fräsen und Drehen) zusammen. Er erfasst Innenradien vs. Fräserdurchmesser, Tiefe/Breite-Verhältnisse von Frästaschen, Mindestwandstärken für Metalle und Kunststoffe, Bohrungs- und Gewindetiefen, Standardtoleranzen ohne Aufpreis sowie fertigungsgerechte Spannflächen als Datenbasis für das Projekt inventa.

---

## 1. Fräsen: Innenradien, Taschen und Wandstärken

### Eintrag: Dimensionierung von Innenradien an vertikalen Kanten
* **Aussage / Wert:** Der vertikale Innenradius an Taschenecken sollte mindestens ⅓ der Kavitätentiefe betragen und geringfügig größer als der Fräserradius sein.
* **Geltungsbereich:** Vertikale Innenecken in gefrästen Taschen und Vertiefungen.
* **Herkunft:** Fertigungsstandard / Online-Fertiger (Hubs & Xometry).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt Internal edges (Vertical corner radius).
* **Wörtliches Zitat:** „Recommended: ⅓ times cavity depth (or larger)“
* **Weiteres Zitat:** „Increasing the corner radii slightly above the recommended value (e.g. by 1 mm), allows the tool to cut following a circular path instead of a 90 angle. This is preferred as it results in a higher quality surface finish. If sharp 90-degree internal corners are required, consider adding a T-bone undercut instead of reducing the corner radius.“
* **Begründung:** Schaftfräser sind zylindrisch und hinterlassen prinzipbedingt an Innenkanten einen Radius. Ist der Eckenradius geringfügig größer als der Werkzeugradius, fährt das Werkzeug kontinuierlich auf einer Kreisbahn und muss an der Ecke nicht schlagartig abstoppen.
* **Härte:** Fehler (scharfe 90°-Innenecken ohne Freistich oder Eckenradius müssen von `check_design` abgewiesen werden).
* **Prüfstatus:** offen.

---

### Eintrag: Innenradius-Verhältnis zum Werkzeugradius nach Xometry
* **Aussage / Wert:** Als Faustregel für vertikale Innenkanten gilt ein Radius von 130 % des Fräserradius.
* **Geltungsbereich:** CNC-gefräste Taschen und Innenkanten.
* **Herkunft:** Fertigungsstandard (Xometry Design Guide).
* **Quelle:** [Xometry 10 CAD Tips](https://www.xometry.com/resources/machining/10-tips-improve-cad-cnc-design/).
* **Seite bzw. Tabelle:** Tip #6 (Add a Radius When Designing Internal Vertical Edges).
* **Wörtliches Zitat:** „A good rule of thumb is to add a radius of 130% of the milling radius. If you need sharp internal corners, consider adding undercuts instead of reducing the edge radius.“
* **Begründung:** Verhindert übermäßigen Werkzeugverschleiß, Rattermarken an den Wänden und senkt die Fertigungskosten.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Tiefe-zu-Breite-Verhältnis von Frästaschen
* **Aussage / Wert:** Die empfohlene Tiefe einer Frästasche beträgt maximal das 4-fache der Taschenbreite (Kavitätstiefe sollte 3 bis 5 mal die Breite nicht überschreiten).
* **Geltungsbereich:** Gefräste Taschen und Vertiefungen in Metallen und Kunststoffen.
* **Herkunft:** Fertigungsstandard (Hubs & Xometry).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt Cavity depth.
* **Wörtliches Zitat:** „Recommended cavity depth:  4 times cavity width“
* **Weiteres Zitat:** „End mill tools have a limited cutting length (typically 3–4 times their diameter). Tool deflection, chip evacuation and vibrations become more prominent when cavities have a smaller depth-to-width ratio. Limiting the depth of the cavity to four times its width ensures good results.“
* **Begründung:** Bei tieferen Taschen treten Werkzeugabdrängung (Deflection), schlechte Spanabfuhr und starke Vibrationen auf, die zu unzureichender Maßhaltigkeit führen.
* **Härte:** Hinweis (Fehler, wenn Tiefe > 6 × Fräserdurchmesser ohne Stufenkonstruktion).
* **Prüfstatus:** offen.

---

### Eintrag: Mindestwandstärken beim CNC-Fräsen für Metalle und Kunststoffe
* **Aussage / Wert:** Die empfohlene Mindestwandstärke beträgt 0,8 mm für Metalle und 1,5 mm für Kunststoffe (machbar bis 0,5 mm für Metalle und 1,0 mm für Kunststoffe; Protolabs Mindestgeometrie 0,5 mm).
* **Geltungsbereich:** Dünne Wände und Stege bei Frästeilen.
* **Herkunft:** Fertigungsrichtlinie (Hubs & Protolabs).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt Minimum wall thickness.
* **Wörtliches Zitat:** „Minimum wall thickness [...] Recommended: 0.8 mm (metals), 1.5 mm (plastics) [...] Feasible: 0.5 mm (metals), 1.0 mm (plastics)“
* **Weiteres Zitat:** „Decreasing the wall thickness reduces the stiffness of the material, which increases vibrations during machining and lowers the achievable accuracy. Plastics are prone to warping (due to residual stresses) and softening (due to temperature increase), so a larger minimum wall thickness is recommended.“
* **Begründung:** Dünne Wände verlieren an Steifigkeit und vibrieren beim Fräsen. Kunststoffe neigen durch Eigenspannungen und Zerspanungswärme zu Verzug.
* **Härte:** Fehler (`check_design` muss Wandstärken < 0,8 mm bei Metallen bzw. < 1,5 mm bei Kunststoffen monieren).
* **Prüfstatus:** offen.

---

### Eintrag: Mindestwandstärke nach Xometry
* **Aussage / Wert:** Die standardmäßige Mindestdicke von Wänden beträgt 0,794 mm für Metalle und 1,5 mm für Kunststoffe.
* **Geltungsbereich:** CNC-Frästeile aus Metall und Kunststoff.
* **Herkunft:** Hersteller / Fertigungsnetzwerk (Xometry).
* **Quelle:** [Xometry 10 CAD Tips](https://www.xometry.com/resources/machining/10-tips-improve-cad-cnc-design/).
* **Seite bzw. Tabelle:** Tip #1 (Avoid Excessively Thin Walls).
* **Wörtliches Zitat:** „The standard minimum thickness of walls is 0.794 millimeters for metals and 1.5 millimeters for plastics.“
* **Begründung:** Eine Reduzierung der Wandstärke verringert die Materialsteifigkeit und mindert die erzielbare Fertigungsgenauigkeit durch Vibrationen.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## 2. Bohrungen, Gewindetiefen und Standardtoleranzen

### Eintrag: Maximale Bohrungstiefe beim CNC-Bohren
* **Aussage / Wert:** Die empfohlene maximale Bohrungstiefe beträgt das 4-fache des Nenndurchmessers (typisch bis zum 10-fachen Nenndurchmesser machbar).
* **Geltungsbereich:** Bohrungen in Fräs- und Drehteilen.
* **Herkunft:** Fertigungsstandard (Hubs).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt Holes (Maximum depth).
* **Wörtliches Zitat:** „Recommended: 4 times nominal diameter“
* **Weiteres Zitat:** „Typical: 10 times nominal diameter“
* **Begründung:** Bei Bohrungstiefen über dem 4-fachen Durchmesser neigen Standardbohrer zum Verlaufen (Achsabweichung), die Späneabfuhr wird erschwert und es entstehen Riefen an der Bohrungswand.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Gewindelänge und Auslauf bei Sacklochgewinden
* **Aussage / Wert:** Die empfohlene Gewindelänge beträgt das 1,5-fache bis 3-fache des Nenndurchmessers. Bei Sacklochgewinden mit Gewindebohrern (unter M6) ist am Bohrungsgrund eine gewindefreie Länge von mindestens dem 1,5-fachen Nenndurchmesser vorzusehen.
* **Geltungsbereich:** Innengewinde in Sacklochbohrungen.
* **Herkunft:** Fertigungsstandard (Hubs).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt Thread length.
* **Wörtliches Zitat:** „Minimum: 1.5 times nominal diameter [...] Recommended: 3 times nominal diameter“
* **Weiteres Zitat:** „The majority of the load applied to a thread is taken by the few first teeth (up to 1.5 times the nominal diameter). Threads longer than 3 times the nominal diameter are thus unnecessary. For threads in blind holes cut with taps (i.e. all threads smaller than M6), add an unthreaded length equal to 1.5 times the nominal diameter at the bottom of the hole.“
* **Begründung:** Der Großteil der Zugkraft wird von den ersten 3 bis 4 Gewindegängen übertragen. Längere Gewinde bringen keinen Tragfähigkeitsgewinn, erhöhen jedoch das Risiko von Gewindebohrerbruch enorm.
* **Härte:** Fehler (bei Sacklöchern ohne ausreichenden Auslauf für den Anschnitt des Gewindebohrers).
* **Prüfstatus:** offen.

---

### Eintrag: Standardtoleranzen ohne Aufpreis
* **Aussage / Wert:** Die typische Standardtoleranz für CNC-gefräste Bauteile ohne zusätzliche Bearbeitungsaufpreise beträgt +-0,1 mm (machbar bis +-0,02 mm).
* **Geltungsbereich:** Spanende Fertigung von Passflächen und Funktionsmaßen.
* **Herkunft:** Fertigungsrichtlinie (Hubs & Fictiv).
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt Tolerances.
* **Wörtliches Zitat:** „Typical: +-0.1 mm“
* **Weiteres Zitat:** „Feasible: +-0.02 mm“
* **Begründung:** Toleranzen enger als 0,1 mm erfordern Schlichtwerkzeuge, reduzierte Vorschübe, thermische Kompensation und manuelle Messprotokolle, was die Teilekosten vervielfacht.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## 3. Spannflächen und Drehteile

### Eintrag: Spannflächen und Werkstückorientierung nach Fictiv
* **Aussage / Wert:** Bauteile sollten gerade, parallele Außenkanten aufweisen, um im Standardschraubstock gespannt werden zu können. Gekrümmte Konturen erfordern teure Sonderspannbacken.
* **Geltungsbereich:** Bauteilgeometrie für Frästeile im 3-Achs- und Mehrachsfräsen.
* **Herkunft:** Fertigungsleitfaden (Fictiv CNC Machining Design Guide).
* **Quelle:** [Fictiv CNC Design Guide](https://www.fictiv.com/articles/cnc-machining-design-guide).
* **Seite bzw. Tabelle:** Abschnitt Workholding and Fixturing.
* **Wörtliches Zitat:** „Curved edges (other than perfect cylindrical profiles) require custom fixtures, costing extra time and money. Thin parts are difficult to hold and are prone to warping. Parts are also easier to set up and machine if all features can be reached by the tool in just one orientation.“
* **Weiteres Zitat:** „every time you need to change the orientation of a part or the way that it is fixtured in a machine, you add time and therefore cost to the manufacturing process.“
* **Begründung:** Jede Neuausrichtung erfordert ein manuelles Umspannen und erneutes Antasten der Werkstücknullpunkte, was die Bearbeitungszeit verlängert und die Toleranzkette vergrößert.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Bauteilgröße und Seitenbearbeitung bei 3-Achs-Fräsen nach Protolabs
* **Aussage / Wert:** Bei 3-Achs-Fräsmaschinen können Teile bis 254 mm × 178 mm (10 in. × 7 in.) von bis zu 6 orthogonalen Seiten bearbeitet werden; größere Teile können nur von oben und unten bearbeitet werden.
* **Geltungsbereich:** 3-Achs-CNC-Fräsen bei Protolabs.
* **Herkunft:** Fertigerhandbuch (Protolabs Design Tips).
* **Quelle:** [Protolabs CNC Design Tips](https://www.protolabs.com/resources/design-tips/6-ways-to-optimize-part-design-for-cnc-machining/).
* **Seite bzw. Tabelle:** Abschnitt 6 (3-Axis and 5-Axis Machining).
* **Wörtliches Zitat:** „With 3-axis machining, the workpiece is gripped from the bottom of the raw material blank while all of the part features are cut from up to 6 orthogonal sides. With parts larger than 10 in. by 7 in. (254mm by 178mm), only the top and bottom can be machined: no side setups!“
* **Begründung:** Große Werkstücke schränken den Verfahrweg des Spindelkopfes und die Klemmoptionen im Standard-Schraubstock ein, sodass seitliche Aufspannungen entfallen.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: CNC-Drehen: Geometrie und Mindestwandstärken nach Fictiv
* **Aussage / Wert:** CNC-Drehteile besitzen typischerweise zylindrische, axialsymmetrische Geometrien. Die Wandstärke an gedrehten Bauteilen sollte über 0,02 Zoll gehalten werden.
* **Geltungsbereich:** CNC-Drehteile (Lathe / Turned parts).
* **Herkunft:** Fertigungsleitfaden (Fictiv CNC Machining Design Guide).
* **Quelle:** [Fictiv CNC Design Guide](https://www.fictiv.com/articles/cnc-machining-design-guide).
* **Seite bzw. Tabelle:** Abschnitt CNC Turning.
* **Wörtliches Zitat:** „CNC turning refers to parts created on a lathe, generally with cylindrical geometry and axial symmetry. The stock material is held in a chuck, which rotates, while a cutting tool moves up and down and side to side to remove material.“
* **Weiteres Zitat:** „Wall thickness on turned parts should be kept above 0.02 inches.“
* **Begründung:** Zu geringe Wandstärken führen zu elastischer Verformung durch die Backenspannung im Drehfutter sowie zu Rattern und schlechter Oberflächengüte beim Zerspanen.
* **Härte:** Fehler (bei Wandstärken unter 0,02 Zoll / ca. 0,5 mm bei Drehteilen).
* **Prüfstatus:** offen.

---

## 4. Nicht erreichbare Quellen, offene Fragen und Versuchsvorschläge

### Nicht erreichbare Quellen
| URL | Code / Grund | Bemerkung |
| :--- | :---: | :--- |
| `https://xometry.pro/wp-content/uploads/2023/07/EN-CNC-Machining-Design-Guide.pdf` | 403 Bot-Sperre | Xometry Europe PDF wegen Bot-Schutz nicht automatisiert ladbar. |
| `https://www.fictiv.com/articles/fictiv-cnc-machining-design-guide` | 404 Nicht gefunden | Veraltete URL; korrekter Pfad ist `.../cnc-machining-design-guide`. |

### Offene Fragen
1. **Passgenauigkeit von FDM-Druckteilen in CNC-Spannbacken:** Können 3D-gedruckte Schonbacken aus PLA oder PETG auf einer CNC-Fräse sicher zum Spannen empfindlicher Freiformteile verwendet werden, ohne unter den Spannkräften zu kriechen?
2. **Minimale Eckenfreistiche (Dog-Bone vs. T-Bone):** Welcher Freistichtyp schwächt die Bauteilfestigkeit bei dynamischer Belastung weniger und lässt sich schneller mit Standardfräsern abzeilen?

### Vorschläge für eigene Versuche
1. **Druckversuch Spannbacken für den Maschinenschraubstock (Ultimaker 2+):** Profilierte Schonbacken mit zylindrischer Kontur für Drehteile aus PETG drucken und Verformung beim Festspannen im Schraubstock mit der Messuhr prüfen.
2. **Prüfkörper Eckenradien vs. Dog-Bone-Freistich:** Vergleichskörper drucken, um die Passgenauigkeit einer rechteckigen Einschubkarte in einer gefrästen Tasche mit Eckenradius vs. Freistich nachzustellen.

---

Quellenprüfung (tools/check_sources.py, 2026-10-21): alle Zitate und Zahlen im abgerufenen Quelltext gefunden. Damit ist der Wert in der Quelle belegt, aber nicht zwingend richtig übernommen (Geltungsbereich, Reibwert und Spalte von Hand prüfen).
