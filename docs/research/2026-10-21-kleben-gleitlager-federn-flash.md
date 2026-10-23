> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Klebeverbindungen, Kunststoff-Gleitlager und Technische Federn

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert  
Sprache: Deutsch  

Dieser Bericht erfasst die Auslegungs- und Konstruktionsregeln für Klebeverbindungen (Beanspruchungsarten, Vermeidung von Schälbeanspruchung, Spaltmaße und Überlappung), Kunststoff-Gleitlager (igus iglidur: Einpressmaße, Gehäuse- und Wellentoleranzen, pv-Werte) sowie Druck- und Zugfedern (Einbauregeln, Knickung, Lagerungsbeiwerte nach DIN EN 13906) als Datenbasis für das Projekt inventa.

---

## 1. Klebeverbindungen: Beanspruchungsgerechtes Konstruieren und Spaltmaße

### Eintrag: Bevorzugte Beanspruchungsarten und Vermeidung von Schälung
* **Aussage / Wert:** Klebeverbindungen müssen so gestaltet werden, dass sie vorrangig auf Druck-, Zug- oder Scherbeanspruchung beansprucht werden. Schäl- und Biegebeanspruchungen müssen konstruktiv vermieden werden (z. B. durch Nut-Feder-Verbindungen). Kräfte sollten stets zentral eingeleitet werden.
* **Geltungsbereich:** Klebkonstruktionen im allgemeinen Maschinen- und Gerätebau.
* **Herkunft:** Hersteller / Fertigungsleitfaden (DELO Industrie Klebstoffe).
* **Quelle:** [DELO 8 Tipps für das Kleben](https://www.delo.de/news-und-termine/delo-news/detail/8-tipps-hochtechnologieklebstoffe/).
* **Seite bzw. Tabelle:** Online-Fachbeitrag, Abschnitt Die 8 Regeln für Ihren Klebeerfolg.
* **Wörtliches Zitat:** „Druck-, Zug- und Scherbeanspruchung bevorzugt: Diese Belastungsarten sind für Klebeverbindungen am günstigsten.“
* **Weiteres Zitat:** „Keine Schälung oder Biegebeanspruchung: Vermeiden Sie Konstruktionen, die Schälkräfte erzeugen. Nut-Feder-Verbindungen sind hier ein smarter Ansatz.“
* **Weiteres Zitat:** „Exzentrische Krafteinleitung vermeiden: Kräfte sollten möglichst zentral eingeleitet werden.“
* **Begründung:** Schälbeanspruchungen erzeugen an den Fugenrändern extreme, linienförmige Spannungsspitzen. Da Klebstoffe im Vergleich zu Metallen eine begrenzte Schälfestigkeit aufweisen, reißt die Klebefuge unter Schälung bereits bei minimalen Gesamtkräften ein.
* **Härte:** Fehler (`check_design` muss reine Stumpfklebungen unter Biegung oder flexible Bauteile unter Schälung abweisen).
* **Prüfstatus:** offen.

---

### Eintrag: Spaltmaße beim Fügen von zylindrischen Teilen nach Henkel Loctite
* **Aussage / Wert:** Für das Fügen von Welle-Nabe-Verbindungen und Lagersitzen sind folgende maximale Klebespalte einzuhalten:
  * Loctite 603: für zylindrische Fügeteile mit geringen Spaltmaßen bis 0,1 mm (Spalt ≤ 0.1 mm).
  * Loctite 648: für Spiel- oder Presssitzverbindungen (Befestigung von Buchsen und Lagern) bis 0,15 mm bei Betriebstemperaturen von -55 °C bis +175 °C.
  * Loctite 638: für dynamische axiale und radiale Belastungen mit großem Spaltfüllvermögen bis 0,25 mm (Spalt ≤ 0.25 mm).
* **Geltungsbereich:** Zylindrische Fügeverbindungen (Lagersitze, Buchsen, Welle-Nabe).
* **Herkunft:** Herstellerhandbuch (Henkel Loctite via Ludwig Meister).
* **Quelle:** [Henkel Loctite Klebetechnik PDF](https://www.ludwigmeister.de/content/techn-informationen/chemische-produkte/klebstoffe/loctite_klebetechnik_de.pdf).
* **Seite bzw. Tabelle:** Seite 16, Fügen zylindrischer Teile.
* **Wörtliches Zitat:** „Loctite® 648 [...] Erhöhte Temperaturbeständigkeit [...] bis 0,15 mm [...] -55 °C bis +175 °C“
* **Weiteres Zitat:** „Loctite® 638 [...] Sehr großes Spaltfüllvermögen [...] bis 0,25 mm [...] Spalt ≤ 0.25 mm“
* **Weiteres Zitat:** „Loctite® 603 [...] geringen Spaltmaßen [...] bis 0,1 mm [...] Spalt ≤ 0.1 mm“
* **Begründung:** Anaerob härtende Klebstoffe härten nur unter Luftabschluss bei katalytischem Metallkontakt aus. Bei zu großem Spaltmaß kann der Klebstoff nicht vollständig polymerisieren, wodurch die Scherfestigkeit drastisch sinkt.
* **Härte:** Fehler (bei Spaltmaßen größer als das für das jeweilige Produkt spezifizierte Spaltfüllvermögen).
* **Prüfstatus:** offen.

---

### Eintrag: Überlappungslänge bei einfach überlappten Blechklebungen
* **Aussage / Wert:** Die empfohlene Überlappungslänge bei einfach überlappten Klebeverbindungen beträgt das 10- bis 20-fache der Fügeteilblechdicke (typischer Richtwert: 10 mm bis 25 mm).
* **Geltungsbereich:** Überlappungsklebungen von Blechen und Profilen.
* **Herkunft:** Hypothese (Fachliteratur / Konstruktionslehre, z. B. Gabenicht).
* **Quelle:** Keine Primärquelle im Web automatisiert verifiziert (als Hypothese gekennzeichnet).
* **Begründung:** Die Kraftübertragung konzentriert sich infolge der elastischen Schubverzerrung überwiegend auf die Randzonen der Überlappung. Eine Vergrößerung der Überlappung über das 20-fache der Wandstärke hinaus steigert die Bruchlast kaum noch, senkt aber die mittlere Zugscherfestigkeit.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## 2. Gleitlager aus Kunststoff (igus iglidur)

### Eintrag: Einpressmaße und Wellentoleranz für iglidur Gleitlager
* **Aussage / Wert:** iglidur Gleitlager sind Einpressbuchsen, die mit Übermaß in eine H7-tolerierte Gehäuseaufnahme eingepresst werden. Für die Gegenlaufwellen wird mindestens eine h9-Toleranz empfohlen. Das Einpressübermaß kann bis zu 2 % des Innendurchmessers betragen; der Nenndurchmesser stellt sich erst nach dem Einpressen ein.
* **Geltungsbereich:** Polymer-Gleitlager iglidur im Maschinen- und Vorrichtungsbau.
* **Herkunft:** Herstellerleitfaden (igus GmbH).
* **Quelle:** [igus Gleitlager Toleranzen Wiki](https://www.igus.de/gleitlager/wiki/toleranzen).
* **Seite bzw. Tabelle:** Fachbeitrag Toleranzen und Einbau.
* **Wörtliches Zitat:** „iglidur Gleitlager sind Einpressbuchsen, die mit Übermaß in eine H7-tolerierte Aufnahme eingepresst werden. Für die Wellen wird mindestens eine h9 Toleranz empfohlen.“
* **Weiteres Zitat:** „Ihr Innendurchmesser stellt sich erst nach dem Einpressen in die H7-Aufnahmebohrung ein. Das Einpressübermaß kann bis zu 2 % des Innendurchmessers betragen. Dadurch wird der sichere Presssitz der Buchse im Gehäuse gewährleistet.“
* **Weiteres Zitat:** „Die Bohrung im Gehäuse sollte für alle Lager in der Toleranz H7 gefertigt und möglichst glatt und angefast sein. Die Montage erfolgt mit einem ebenen Stempel.“
* **Begründung:** Im Lieferzustand weisen die Buchsen am Außen- und Innendurchmesser ein bewusstes Übermaß auf. Erst durch den Einpressvorgang in das formstabile H7-Gehäuse wird das Lager kalibriert und das für den Betrieb erforderliche Laufspiel hergestellt.
* **Härte:** Fehler (`check_design` muss für Gehäusebohrungen H7 und Wellen h9 verlangen).
* **Prüfstatus:** offen.

---

### Eintrag: pv-Wert und Schmierungsfaktor für iglidur Gleitlager
* **Aussage / Wert:** Der pv-Wert (Produkt aus spezifischer Belastung p und Gleitgeschwindigkeit v) dient als Kennwert für die entstehende Reibungswärme im Gleitlager. Eine Einmalschmierung bei der Montage verbessert das Einlaufverhalten und erhöht die Belastbarkeit (Korrekturfaktor 1,3 für den pv-Wert gegenüber Trockenlauf mit Faktor 1).
* **Geltungsbereich:** Thermische Auslegung von iglidur Gleitlagern im Trockenlauf und geschmierten Lauf.
* **Herkunft:** Hersteller (igus GmbH).
* **Quelle:** [igus pv-Wert Wiki](https://www.igus.de/gleitlager/wiki/p-x-v-wert-und-schmierung).
* **Seite bzw. Tabelle:** Fachbeitrag p x v-Wert und Schmierung.
* **Wörtliches Zitat:** „Dem Produkt aus der spezifischen Belastung [p] und der Gleitgeschwindigkeit [v] kommt bei Gleitlagern eine ganz besondere Bedeutung zu. Der pv-Wert kann als ein Maß der Reibungswärme angesehen werden und kann deshalb als analytisches Mittel zur Beantwortung der Frage nach der Einsetzbarkeit eines Gleitlagers benutzt werden. Dazu wird der tatsächliche pv-Wert mit einem in der Höhe berechenbaren zulässigen pv-Wert verglichen. Der zulässige pv-Wert ist abhängig vom Werkstoff der Laufpartner, von der Umgebungswärme und der Einschaltdauer.“
* **Weiteres Zitat:** „Obwohl iglidur-Gleitlager für den Trockenlauf ausgelegt sind, sind sie mit gebräuchlichen Ölen und Fetten gut verträglich. Eine Einmalschmierung bei der Montage verbessert das Einlaufverhalten sowie den Reibwert und reduziert damit die entstehende Reibungswärme.“
* **Begründung:** Kann die im Gleitkontakt entstehende Reibungswärme nicht schnell genug über Welle und Gehäuse abgeführt werden, erreicht das Polymer seine Erweichungstemperatur, was zu rapidem Materialabtrag oder Festfressen führt.
* **Härte:** Fehler.
* **Prüfstatus:** offen.

---

## 3. Technische Federn: Druck- und Zugfedern nach DIN EN 13906

### Eintrag: Knickung und Lagerungsbeiwerte bei Druckfedern nach DIN EN 13906-1
* **Aussage / Wert:** Druckfedern können unter Belastung ausknicken. Die Grenzfederlänge ist die Knicklänge Lk und der zugehörige Weg der Knickfederweg sK. Der Einfluss der Federendenlagerung wird über den Lagerungsbeiwert ν abgebildet:
  * frei - fest: ν = 2
  * gelenkig - gelenkig: ν = 1
  * verschiebbar - fest: ν = 1
  * gelenkig - fest: ν = 0,7
  * fest - fest: ν = 0,5
* **Geltungsbereich:** Zylindrische Schraubendruckfedern nach DIN EN 13906-1.
* **Herkunft:** Norm über Handbuch (DIN EN 13906-1 via eAssistant).
* **Quelle:** [eAssistant Handbuch Druckfedern](https://www.eassistant.eu/fileadmin/dokumente/eassistant/etc/HTMLHandbuch/de/eAssistantHandbch22.html).
* **Seite bzw. Tabelle:** Kapitel 22, Abschnitt 22.3.5 (Lagerungsarten).
* **Wörtliches Zitat:** „Einige Federn können ausknicken. Die zugehörige Federlänge wird als Knicklänge \(L_{k}\) und der bis dahin zurückgelegte Federweg als Knickfederweg \(s_{K}\) bezeichnet. Ein Einfluss der Federendenlagerung wird durch den Lagerungsbeiwert \(\nu \) berücksichtigt.“
* **Weiteres Zitat:** „frei - fest (\(\nu \) = 2) [...] gelenkig - gelenkig (\(\nu \) = 1) [...] verschiebbar - fest (\(\nu \) = 1) [...] gelenkig - fest (\(\nu \) = 0,7) [...] fest - fest (\(\nu \) = 0,5)“
* **Begründung:** Schlanke Federn weisen eine geringe Quersteifigkeit auf. Ohne Führung durch einen Dorn oder eine Hülse knicken ungeführte Federn aus, wenn der Arbeitsweg den Knickfederweg sK überschreitet.
* **Härte:** Fehler (`check_design` muss für Federn ohne Führung prüfen, ob der Ausfederungsweg unter sK bleibt).
* **Prüfstatus:** offen.

---

### Eintrag: Ösenformen bei Zugfedern nach DIN EN 13906-2
* **Aussage / Wert:** Bei Zugfedern dienen unterschiedliche Ösenformen zur Krafteinleitung (u. a. halbe deutsche Öse, ganze deutsche Öse, doppelte deutsche Öse, Hakenöse und englische Öse).
* **Geltungsbereich:** Zylindrische Schraubenzugfedern nach DIN EN 13906-2.
* **Herkunft:** Norm über Handbuch (DIN EN 13906-2 via eAssistant).
* **Quelle:** [eAssistant Handbuch Zugfedern](https://www.eassistant.eu/fileadmin/dokumente/eassistant/etc/HTMLHandbuch/de/eAssistantHandbch23.html).
* **Seite bzw. Tabelle:** Kapitel 23, Abschnitt 23.5 (Auswahl der Federenden).
* **Wörtliches Zitat:** „Zur Überleitung der Federkraft dienen die unterschiedliche Ösenformen und Anschlusselemente.“
* **Weiteres Zitat:** „Halbe deutsche Öse [...] Ganze deutsche Öse [...] Doppelte deutsche Öse [...] Ganze deutsche Öse seitlich hochgestellt [...] Doppelte deutsche Öse seitlich hochgestellt [...] Hakenöse [...] Hakenöse seitlich hochgestellt [...] Englische Öse“
* **Begründung:** Am Übergang vom Federkörper zur aufgebogenen Öse tritt eine kombinierte Biege- und Torsionsspannung auf. Dieser Übergangsradius ist kerbempfindlich und die primäre Bruchstelle von Zugfedern.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Normauslegung für Druck- und Zugfedern nach Gutekunst
* **Aussage / Wert:** Die vollständige Auslegung von Druckfedern und Zugfedern erfolgt nach DIN EN 13906 und umfasst Federkräfte, Federwege, Federrate und Knickfederweg.
* **Geltungsbereich:** Technische Schraubenfedern.
* **Herkunft:** Hersteller / Berechnungsstandard (Gutekunst Federn).
* **Quelle:** [Gutekunst Federnberechnung](https://www.federnshop.com/de/service-und-informationen/federberechnung-nach-din-13906.html).
* **Seite bzw. Tabelle:** Online-Portal Federberechnung nach DIN 13906.
* **Wörtliches Zitat:** „Berechnen Sie Druckfedern, Zugfedern und Schenkelfedern individuell mit dem Gutekunst Federnberechnungsprogramm WinFSB. Mit Eingabe von Maßdaten, Weg-Kraft- oder Länge-Kraft-Eigenschaften wird die gewünschte Feder komplett nach DIN EN 13906 berechnet.“
* **Begründung:** Die rechnerische Erfassung von Blocklänge, Knickfederweg und dynamischer Belastbarkeit ist Voraussetzung für eine funktionssichere Integration in Mechanismen.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## 4. Nicht erreichbare Quellen, offene Fragen und Versuchsvorschläge

### Nicht erreichbare Quellen
| URL | Code / Grund | Bemerkung |
| :--- | :---: | :--- |
| `https://blog.federnshop.com/federendlagerungen-knickgrenzen/` | 000 / Errno 101 | Gutekunst-Blogserver über IPv6 / DNS in dieser Testumgebung nicht erreichbar; Hauptshop `federnshop.com` ist erreichbar. |
| `https://www.3mschweiz.ch/...` | 403 Bot-Sperre | 3M Schweiz sperrt automatisierte Abrufe per WAF. |
| `https://www.lesjofors.com/...` | JS-Render / Leertext | Lesjöfors-Website rendert Inhalte ausschließlich per Client-JavaScript. |

### Offene Fragen
1. **Druckfedernführung in 3D-gedruckten Führungsdomen (FDM):** Welches radiale Mindestspiel zwischen Federaußendurchmesser De und FDM-Hülseninnenwand ist erforderlich, um ein Klemmen durch die Schichtriefen (Layer Lines) zu verhindern?
2. **Kriechverhalten von iglidur-Lagern in gedruckten Gehäusen:** Wie weit weitet sich eine H7-Passungsbohrung in PLA oder PETG unter dem konstanten Einpressübermaß (2 %) des Kunststoffgleitlagers nach 1.000 Betriebsstunden auf?

### Vorschläge für eigene Versuche
1. **Einpressversuch igus iglidur in FDM-Prüfkörper (Ultimaker 2+):** Prüfblöcke mit kalibrierten Bohrungen (H7 gerieben vs. direkt gedruckt mit abgestuften Durchmessern in 0,05-mm-Schritten) aus PLA und PETG fertigen. Einpresskraft mit Handhebelpresse messen und Innendurchmesser nach dem Einpressen mit Grenzlehrdorn prüfen.
2. **Klebespalt- und Zugscherversuch mit Loctite 648 auf FDM-Wellen:** Zylindrische Bolzen und Hülsen mit definierten radialen Spaltmaßen (0,05 mm, 0,10 mm, 0,15 mm, 0,20 mm) drucken, mit Loctite 648 fügen und maximale axiale Auspresskraft ermitteln.

---

Quellenprüfung (tools/check_sources.py, 2026-10-21): alle Zitate und Zahlen im abgerufenen Quelltext gefunden. Damit ist der Wert in der Quelle belegt, aber nicht zwingend richtig übernommen (Geltungsbereich, Reibwert und Spalte von Hand prüfen).
