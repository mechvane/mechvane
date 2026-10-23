> Gemini 3.8 Flash, nicht verifiziert. Recherche 2026-10-21.

# Allgemeine Gestaltungsregeln: Konstruktion, Montage und Toleranzen

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert  
Sprache: Deutsch

Dieses Dokument fasst allgemeine Gestaltungsregeln für den Maschinenbau und die Produktentwicklung zusammen. Es behandelt kraftfluss- und kerbgerechte Auslegung, Montage- und Wartungsgerechtigkeit nach DFMA-Prinzipien (Boothroyd-Dewhurst), Schraubensenkungen nach DIN 974-1 sowie Toleranzkettenberechnungen und die Konstruktionsmethodik nach VDI 2221 bis 2223. Es dient als Regelbasis für die algorithmische Geometrieprüfung (`check_design`) und parametrische Modellerstellung im Projekt **inventa**.

---

## Detaillierte Katalog-Einträge

### Montage: Fügerichtung von oben und Pyramidenmontage (Boothroyd-DFA)
* **Aussage / Wert:** Die Baugruppenmontage soll bevorzugt als Pyramidenmontage entlang einer einzigen Bezugsachse erfolgen; die Fügerichtung soll nach Möglichkeit von oben nach unten ausgerichtet sein.
* **Geltungsbereich:** Allgemeine Baugruppenmontage (DFMA – Design for Assembly nach Boothroyd & Dewhurst).
* **Herkunft:** Leitfaden / DFMA-Best-Practices (Five Flute DFA Guide nach Boothroyd-Dewhurst).
* **Quelle:** [Five Flute DFA Guide](https://www.fiveflute.com/guide/design-for-assembly-dfa-best-practices/)
  * *Wörtliches Zitat:* „Use pyramid assembly - provide for progressive assembly about one axis of reference. In general, it is best to assemble from above.“
* **Begründung:** Das Fügen von oben nutzt die Schwerkraft zur Unterstützung der Teilepositionierung und eliminiert zeit- sowie kostenintensive Bauteildrehungen oder Mehrachsen-Montagevorrichtungen.
* **Härte:** Hinweis (Konstruktionsempfehlung für effiziente Montage).
* **Prüfstatus:** offen.

---

### Montage: Einführfasen und Zentrierungen an Fügestellen
* **Aussage / Wert:** Paarungsflächen von Bauteilen sind mit Einführfasen zu versehen, um die Führung beim Fügen zu gewährleisten und den Einführwiderstand zu minimieren. Großzügige Spiele sind anzustreben, ohne Verkantungseffekte hervorzurufen.
* **Geltungsbereich:** Konstruktion von Fügestellen, Passungen und Steckverbindungen.
* **Herkunft:** Leitfaden / DFMA-Best-Practices (Five Flute DFA Guide nach Boothroyd-Dewhurst).
* **Quelle:** [Five Flute DFA Guide](https://www.fiveflute.com/guide/design-for-assembly-dfa-best-practices/)
  * *Wörtliches Zitat:* „Design so that there is little or no resistance to insertion and provide chamfers to guide insertion of two mating parts. Generous clearance should be provided, but care must be taken to avoid clearances that will result in a tendency for parts to jam or hang-up during insertion.“
* **Begründung:** Einführfasen kompensieren Positionstoleranzen des Werkers oder Montage-Roboters und verhindern Beschädigungen oder Verkanten an scharfen Kanten.
* **Härte:** Hinweis (Regelverstoß führt zu Hakeln bei manueller und Blockade bei automatisierter Montage).
* **Prüfstatus:** offen.

---

### Montage: Symmetrie und Poka-Yoke zur Verhinderung von Fehlmontage
* **Aussage / Wert:** Bauteile sind entweder mit vollständiger Symmetrie (End-zu-End und rotationssymmetrisch) zu konstruieren oder, falls Asymmetrie funktionell erforderlich ist, mit offensichtlicher Asymmetrie (Poka-Yoke) zu gestalten, um Fehlmontagen geometrisch unmöglich zu machen.
* **Geltungsbereich:** Auslegung von Einzelteilen für Serienmontagen.
* **Herkunft:** Leitfaden / DFMA-Best-Practices (Five Flute DFA Guide nach Boothroyd-Dewhurst).
* **Quelle:** [Five Flute DFA Guide](https://www.fiveflute.com/guide/design-for-assembly-dfa-best-practices/)
  * *Wörtliches Zitat:* „Design parts that have end-to-end symmetry and rotational symmetry about the axis of insertion. If this cannot be achieved, try to design parts having the maximum possible symmetry. Design parts that, in those instances where the part cannot be made symmetric, are obviously asymmetric. [...] Poka yoke is a design technique that uses asymmetry to enforce compatible assembly configuration and eliminate incompatible configurations.“
* **Begründung:** Vollständige Symmetrie erfordert kein vorheriges Ausrichten der Bauteile. Erzwungene Asymmetrie schließt spiegelverkehrtes oder verdrehtes Einbauen physisch aus.
* **Härte:** Fehler (wenn Funktionsflächen nicht rotationssymmetrisch sind, muss eine Poka-Yoke-Geometrie Verpolung oder Falscheinbau verhindern).
* **Prüfstatus:** offen.

---

### Montage: Selbstsichernde Verbindungselemente und Schnappverbindungen
* **Aussage / Wert:** Bauteile sollen nach Möglichkeit selbstsichernd gestaltet werden (z. B. durch Schnapphaken, Presssitze oder Nut-Feder-Verbindungen), um separate Verbindungselemente wie Schrauben oder Niete zu vermeiden.
* **Geltungsbereich:** Verbindungstechnik im Leichtbau und DFMA-gerechte Produktgestaltung.
* **Herkunft:** Leitfaden / DFMA-Best-Practices (Five Flute DFA Guide nach Boothroyd-Dewhurst).
* **Quelle:** [Five Flute DFA Guide](https://www.fiveflute.com/guide/design-for-assembly-dfa-best-practices/)
  * *Wörtliches Zitat:* „Self-Fastening Parts: Use parts that can secure themselves without the need for additional fasteners. Snap-fits, press-fits, and tab-slot designs can eliminate screws, bolts, and other separate fasteners.“
* **Begründung:** Jedes separate Befestigungselement erhöht Bauteilanzahl, Logistikkosten und Montageschritte. Schnappverbindungen lassen sich werkzeuglos und in Sekundenschnelle fügen.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Schrauben: Senkungsabmessungen nach DIN 974-1 für Zylinderschrauben
* **Aussage / Wert:** Für Zylinderschrauben nach ISO 4762 (ehemals DIN 912) definiert DIN 974-1 Form K folgende Abmessungen für Senkungsdurchmesser d1 und Senktiefe T: für M3 Senkung d1 6,00 mm und Tiefe T 3,40 mm; für M4 Senkung d1 8,00 mm und Tiefe T 4,40 mm; für M5 Senkung d1 10,00 mm und Tiefe T 5,40 mm; für M6 Senkung d1 11,00 mm und Tiefe T 6,40 mm.
* **Geltungsbereich:** Konstruktion versenkter Zylinderschraubverbindungen im Maschinen- und Vorrichtungsbau.
* **Herkunft:** Normen-Bohrtabelle nach DIN 974-1 / ISO 4762 über Fachquelle (schraube-mutter.de).
* **Quelle:** [schraube-mutter.de: Bohrtabelle für Zylinderschrauben DIN 974-1](https://schraube-mutter.de/bohrtabelle-fuer-zylinderschrauben/)
  * *Wörtliches Zitat:* „Bohrtabelle für Zylinderschrauben mit den Toleranzmaßen nach DIN 974-1 [...] Form K für Zylinderschrauben mit Innensechskant ISO 4762 (Zylinderschrauben mit Innensechskant / ehemals Zylinderschraube DIN 912)“
* **Begründung:** Die Senkung d1 muss größer sein als der Schraubenkopf, um Fluchtungsfehler auszugleichen und Werkzeugzugänglichkeit (Inbusschlüssel) zu sichern. Das Maß T muss bei Beilagscheiben entsprechend vertieft werden.
* **Härte:** Fehler (Kollisionsprüfung und Werkzeugzugang schlagen fehl, wenn Senkdurchmesser d1 unter Kopfdurchmesser liegt).
* **Prüfstatus:** offen.

---

### Toleranzketten: Arithmetische Tolerierung und Worst-Case-Ansatz
* **Aussage / Wert:** Bei der arithmetischen Tolerierung (Worst-Case-Tolerierung) wird unterstellt, dass alle Merkmale einer Maßkette gleichzeitig an ihren extremen oberen oder unteren Toleranzgrenzen liegen.
* **Geltungsbereich:** Lineare Maßkettenberechnung im Maschinenbau bei Kleinserien oder sicherheitskritischen Minimalspielen.
* **Herkunft:** Technische Fachpublikation (Robert Bosch GmbH, Qualitätsheft Nr. 5: Statistische Tolerierung).
* **Quelle:** [Bosch Qualitätsheft Nr. 5: Statistische Tolerierung PDF](https://assets.bosch.com/media/global/bosch_group/purchasing_and_logistics/information_for_business_partners/downloads/quality_docs/general_regulations/bosch_publications/booklet-no05-statistische-tolerierung_de.pdf)
  * *Wörtliches Zitat:* „Häufig wird die arithmetische Tolerierung auch als „Worst-Case-Tolerierung“ bezeichnet, weil davon ausgegangen wird, dass alle Merkmale genau an ihren oberen oder unteren Grenzen auftreten.“
* **Begründung:** Schließt Montageschwierigkeiten oder Funktionsversagen zu 100 % aus, führt jedoch bei vielen Kettengliedern zu extrem engen und fertigungstechnisch unökonomischen Einzeltoleranzen.
* **Härte:** Hinweis (für Standard-Großserien sollte vorrangig statistische Tolerierung gewählt werden).
* **Prüfstatus:** offen.

---

### Toleranzketten: Statistische Tolerierung und quadratische Addition
* **Aussage / Wert:** Die statistische Toleranzrechnung liefert für das Gesamtmaß kleinere Schließtoleranzen als die arithmetische Rechnung. Dieser wirtschaftliche Vorteil wächst mit steigender Bauteilanzahl in der Kette.
* **Geltungsbereich:** Lineare Toleranzketten in der Serienfertigung mit normalverteilten Prozessstreuungen.
* **Herkunft:** Technische Fachpublikation (Robert Bosch GmbH, Qualitätsheft Nr. 5: Statistische Tolerierung).
* **Quelle:** [Bosch Qualitätsheft Nr. 5: Statistische Tolerierung PDF](https://assets.bosch.com/media/global/bosch_group/purchasing_and_logistics/information_for_business_partners/downloads/quality_docs/general_regulations/bosch_publications/booklet-no05-statistische-tolerierung_de.pdf)
  * *Wörtliches Zitat:* „Die statistische Rechnung weist für das Gesamtmerkmal erwartungsgemäß kleinere Toleranzen auf als die arithmetische Toleranzrechnung. Dieser Vorteil steigt mit steigender Anzahl beteiligter Bauteile weiter an.“
* **Begründung:** Da das gleichzeitige Auftreten extremer Abweichungen an allen Bauteilen statistisch extrem unwahrscheinlich ist, erlaubt die quadratische Addition (Gaußsches Fehlerfortpflanzungsgesetz) größere Einzelfertigungstoleranzen bei gleichbleibender Baugruppenqualität.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Kraftfluss: Kraftflussleitung und kraftflussgerechte Gestaltung
* **Aussage / Wert:** Der Kraftfluss beschreibt den Weg der Kraft von der Einleitungsstelle bis zu den Auflagern; die Kraftflusslinien verlaufen entlang der Richtung der größten Hauptspannung.
* **Geltungsbereich:** Festigkeitsgerechte und werkstoffsparende Bauteilgestaltung.
* **Herkunft:** Fachlexikon / Maschinenbau-Grundlagen (Wikipedia Kraftfluss).
* **Quelle:** [Wikipedia: Kraftfluss](https://de.wikipedia.org/wiki/Kraftfluss)
  * *Wörtliches Zitat:* „Der Kraftfluss in einem Bauteil ist der Weg einer Kraft von der Stelle ihrer Einleitung bis zu den Auflagern, an denen die Kraft durch eine Reaktionskraft und/oder ein Reaktionsmoment aufgenommen wird. [...] Kraftflusslinien geben die Richtung der größten Hauptspannung in einem Punkt an.“
* **Begründung:** Umlenkungen oder Unterbrechungen des Kraftflusses erzeugen schädliche Spannungskonzentrationen; Bauteile sollen so dimensioniert werden, dass die Kraftlinien möglichst geradlinig und ohne Querschnittssprünge verlaufen.
* **Härte:** Hinweis (Gestaltungsprinzip für Leichtbau und Ermüdungsfestigkeit).
* **Prüfstatus:** offen.

---

### Kerbwirkung: Kerbarme Gestaltung und Entlastungskerben
* **Aussage / Wert:** Durch Einbringen einer zusätzlichen Kerbe mit großem Radius kann der Kraftfluss sanft um stark belastete Zonen herumgeleitet werden, wodurch die maximale Kerbspannung sinkt und die Tragfähigkeit steigt.
* **Geltungsbereich:** Hochbeanspruchte Wellenabsätze, Wellennuten und Querschnittsübergänge.
* **Herkunft:** Fachlexikon / Festigkeitslehre (Wikipedia Kerbwirkung).
* **Quelle:** [Wikipedia: Kerbwirkung](https://de.wikipedia.org/wiki/Kerbwirkung)
  * *Wörtliches Zitat:* „Entlastungskerben: Eine zusätzliche Kerbe kann den Kraftfluss an einem stark belasteten Bereich vorbeileiten. [...] Eine zusätzliche Kerbe [...] mit großem Radius lenkt den Kraftfluss sanft auf den kleineren, unteren Querschnitt um. So sinkt die maximale Spannung im Bauteil und die Tragfähigkeit erhöht sich, anstatt sich zu verringern.“
* **Begründung:** Scharfe Absätze erzeugen Spannungsspitzen (Formzahl alpha_k). Gezielte Entlastungsgeometrien (z. B. Freistiche oder tangentiale Ausrundungen) homogenisieren den Spannungsverlauf.
* **Härte:** Fehler (scharfkantige Querschnittsübergänge ohne Mindestausrundungsradius sind bei schwingender Belastung unzulässig).
* **Prüfstatus:** offen.

---

### Konstruktionsmethodik: Richtlinienreihe VDI 2221 bis 2223
* **Aussage / Wert:** Die Richtlinienreihe VDI 2221, 2222 und 2223 beschreibt das methodische Vorgehen bei der Produktentwicklung. VDI 2221-1 definiert das allgemeine Modell der Produktentwicklung als methodische Basis.
* **Geltungsbereich:** Methodische Entwicklung und Konstruktion von Produkten und Systemen.
* **Herkunft:** Hochschul-Bachelorarbeit über VDI-Richtlinienreihe (Nicolas Lein, HS Mittweida).
* **Quelle:** [HS Mittweida Bachelorarbeit Nicolas Lein PDF](https://monami.hs-mittweida.de/frontdoor/deliver/index/docId/15581/file/BA_57127_Nicolas_Lein.pdf)
  * *Wörtliches Zitat:* „Die Richtlinienreihe umfasst die VDI 2221, 2222 und 2223. In diesen wird das Vorgehen zur methodischen Produktentwicklung beschrieben und mithilfe von Beispielen verdeutlicht sowie Möglichkeiten zur Kostenabschätzung gegeben. Die VDI 2221-1 klärt wesentliche Begriffe, gibt eine Einführung in die Grundlagen der Produktentwicklung und erklärt welche Modelle und Methoden angewendet werden. So wird auch ein allgemeines Modell der Produktentwicklung vorgeschlagen und vorgestellt, welches die Basis für das methodische Vorgehen nach VDI 2222 und 2223 definiert.“
* **Begründung:** Ein phasenweises Vorgehen (Aufgabe klären, Konzipieren, Entwerfen, Ausarbeiten) nach VDI 2221 strukturiert den Konstruktionsprozess und vermeidet kostspielige späte Konstruktionsänderungen.
* **Härte:** Hinweis (prozessuales Vorgehensmodell für Agenten-Entwicklungsworkflows).
* **Prüfstatus:** offen.

---

## Nicht erreichbare Quellen

Folgende Quellen wurden während der Recherche geprüft und erwiesen sich als nicht automatisiert abrufbar:

| Quelle / URL | Status | Grund / Bemerkung |
| :--- | :---: | :--- |
| `https://www.hs-anhalt.de/...` | Timeout | Diverse Hochschulskripte zur Konstruktionslehre blockieren automatisierte Abfragen oder sind offline. |
| `https://www.iktd.uni-stuttgart.de/...` | 403 / SSO | Vorlesungsskripte zu Konstruktionsmethodik und DFMA liegen hinter Uni-Login bzw. Shibboleth-Schranken. |
| `https://tu-dresden.de/...` | 403 | Vorlesungsunterlagen Konstruktionstechnik erfordern Institutszugänge. |
| `https://www.vdi.de` | Paywall | Originalnormen (VDI 2221, VDI 2222) liegen hinter DIN-Media/Beuth-Paywalls; methodischer Inhalt über akkreditierte Hochschulpublikationen zitiert. |

---

## Offene Fragen

1. **Algorithmische DFMA-Bewertung:** Wie lassen sich DFMA-Kennzahlen (z. B. nach Boothroyd & Dewhurst: theoretische Mindestteilezahl vs. Ist-Teilezahl) in einem automatisierten Python-Prüfskript für Baugruppen formalisieren?
2. **Statistische Verteilungen bei additiven Toleranzketten:** Welche Verteilungsannahme (Normalverteilung vs. Rechteck- oder Dreiecksverteilung) beschreibt die Maßstreuung additiv gefertigter Kettenglieder am realistischsten?

---

## Vorschläge für eigene Prüf- und Druckversuche

1. **Poka-Yoke-Montagesteckplatz (FDM-Muster):**
   * Druck einer Baugruppe aus Stecker und Buchse mit asymmetrischen Führungsrippen zur praktischen Überprüfung fehlmontagesicherer Fügung.
2. **Kerbspannungs-Biegeversuch:**
   * 3D-Druck von drei Prüfstäben mit gleichem Grundquerschnitt, aber unterschiedlichen Übergängen am Absatz (scharfkantig R0, Standardausrundung R2, Entlastungskerbe R4) zur vergleichenden Ermittlung der statischen und dynamischen Biegesteifigkeit.
3. **Senkungs-Lehrenplatte nach DIN 974-1:**
   * Druck einer Prüfplatte mit zylindrischen Schraubensenkungen für M3, M4, M5 und M6 nach DIN 974-1 Form K zur Überprüfung von Kopfversenkung, Scheibenfreiraum und Werkzeugansatz (Innensechskant-Bit).

---

Quellenprüfung (tools/check_sources.py, 2026-10-21): alle Zitate und Zahlen im abgerufenen Quelltext gefunden. Damit ist der Wert in der Quelle belegt, aber nicht zwingend richtig übernommen.
