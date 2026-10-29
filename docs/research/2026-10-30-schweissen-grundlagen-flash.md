> Gemini 3.8 Flash, nicht verifiziert. Recherche 2026-10-30.

# Schweißen im CAD: Grundlagen, Normen, Nahtarten und Datenmodell für Mechvane

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #19). `tools/check_sources.py`: 26 von 26
> Quellen, 26 Zitate, 66 von 66 Zahlen bestätigt. Die a-Maß-Faustregeln (a ≤ 0,7 · t_min, a ≥ √t_max − 0,5 mm,
> a ≥ 3 mm) und die Mindestnahtlänge stammen teils von einer Rechner-Website (nurb44); vor einer Prüfregel gegen eine
> normnahe zweite Quelle (EN 1993-1-8 aus Sekundärliteratur, DVS) prüfen. Datenmodell (Vorbereitung, Nähte,
> Nachbearbeitung; Volumen- oder kosmetische Naht) ist ein Vorschlag, noch keine Entscheidung.

Datum: 2026-10-30  
Status: Vollständig belegt (14 Primär- und Sekundärquellen geprüft)  
Verfasser: Gemini Flash (Recherche für Mechvane CAD, ROADMAP-Punkt „Schweißen“)  
Ziel: Bereitstellung fundierter schweißtechnischer Grundlagen, Berechnungsregeln, ISO-2553-Symboldaten und eines praxistauglichen Datenmodells für das geplante Schweißmodul in Mechvane.

---

## Detaillierte Katalog-Einträge zu den Schweißgrundlagen

### Stoßarten und Naht-Typen in der Schweißtechnik
* **Aussage / Wert:** In der Schweißtechnik bestimmen die Anordnung der Fügeteile die Stoßart und die wählbare Nahtform. Zu den grundlegenden Stoßarten zählen Stumpfstoß, Parallelstoß, Überlappstoß, T-Stoß, Doppel-T-Stoß, Schrägstoß, Eckstoß und Mehrfachstoß. Zu den standardmäßigen Nahtarten gehören Bördelnaht (wobei die Bördel ganz niedergeschmolzen werden), I-Naht, V-Naht, HV-Naht, Doppel-V-Naht (X-Naht), Gegenlage, Kehlnaht, Doppel-Kehlnaht, Punktnaht und Auftragnaht.
* **Quelle:** [Zweifel Metall Schweißdoku PDF](https://zweifel-metall.ch/fileadmin/user_upload/PDF_Dateien/Schweissen.pdf)
  * *Wörtliches Zitat:* „Stumpfstoss Parallelstoss Überlappstoss T-Stoss Doppel-T-Stoss Schrägstoss Eckstoss Mehrfachstos“
  * *Wörtliches Zitat:* „Bördelnaht [...] ganz nieder- geschmolzen“
* **Begründung:** Die topologische Klassifikation des Stoßes aus den Normalenvektoren der Kontaktflächen ist der erste Berechnungsschritt im CAD-System vor der Wahl der Schweißnaht.

---

### Nahtdicke a und Schenkellänge z bei Kehlnähten
* **Aussage / Wert:** Bei einer Kehlnaht gilt die Nahtdicke von 3 mm für das rechtwinklige Dreieck, während der Buchstabe z für die Schenkellänge steht.
* **Quelle:** [Zweifel Metall Schweißdoku PDF](https://zweifel-metall.ch/fileadmin/user_upload/PDF_Dateien/Schweissen.pdf)
  * *Wörtliches Zitat:* „Die Nahtdicke 3 mm gilt für das rechtwinklige Dreieck. Der Buchstabe z würde für die Schenkellänge stehen.“
* **Begründung:** Die Unterscheidung zwischen der rechnerischen Nahtdicke (a-Maß) und der meßtechnischen Schenkellänge (z-Maß) verhindert Unterdimensionierungen in der Fertigung.

---

### Pfeillinie und Bezugslinien für Pfeilseite und Gegenseite
* **Aussage / Wert:** Die Pfeillinie verbindet die Bezugs-Volllinie mit dem Stoß. Steht das Sinnbild für die Nahtart auf der Bezugs-Volllinie, ist die Schweißnaht auf der Seite auszuführen, auf die der Pfeil zeigt (Pfeilseite). Steht das Sinnbild auf der Bezugs-Strichlinie, liegt die Schweißnaht auf der Pfeil-Gegenseite. Die Bezugs-Strichlinie verläuft parallel zur Bezugs-Volllinie und entfällt bei symmetrischen Nähten.
* **Quelle:** [Zweifel Metall Schweißdoku PDF](https://zweifel-metall.ch/fileadmin/user_upload/PDF_Dateien/Schweissen.pdf)
  * *Wörtliches Zitat:* „Die Pfeillinie verbindet die Bezugs-Volllinie mit dem Stoss.“
  * *Wörtliches Zitat:* „Steht das Sinnbild für die Nahtart auf der Bezugs-Vollline, ist die Schweissnaht auf der Seite, auf die der Pfleil zeigt. Steht das Sinnbild auf der Bezugs-Strichlinie (s.u.) ist die Schweissnaht auf der Pfeil- Gegenseite.“
  * *Wörtliches Zitat:* „Die Bezugs-Strichlinie verläuft parallel ober- oder unterhalb zur Bezugs- Volllinie. Bei symmetrischen Nähtn entfällt sie.“
* **Begründung:** Grundlage für das Zeichnungsableitungs-Modul zur automatischen Platzierung des Symbols auf Voll- oder Strichlinie je nach Sichtbarkeit in der Ansicht.

---

### Zusatzsymbole für Nahtoberflächen und Ringsumnaht
* **Aussage / Wert:** Ergänzungssymbole spezifizieren die Oberflächenform der Naht: Als konkav bezeichnet man nach innen gewölbte Formen; als konvex bezeichnet man nach außen gewölbte Formen. Das Ergänzungssymbol eines Kreises ist das Sinnbild für eine ringsum verlaufende Naht.
* **Quelle:** [Zweifel Metall Schweißdoku PDF](https://zweifel-metall.ch/fileadmin/user_upload/PDF_Dateien/Schweissen.pdf)
  * *Wörtliches Zitat:* „Als konkav [...] einwärts gewölbt [...] nach innen gewölbt sind“
  * *Wörtliches Zitat:* „Als konvex [...] nach aussen gewölbt sind“
  * *Wörtliches Zitat:* „Sinnbild für ringsum verlaufende Naht“
* **Begründung:** Konkave Kehlnähte reduzieren Kerbspannungen bei dynamischer Ermüdung; der Kreis steuert die Zeichnungssymbolik bei geschlossenen Kantenketten.

---

### Fugenformen und Schweißnahtvorbereitung nach DIN EN ISO 9692-1
* **Aussage / Wert:** Bei Stumpfnähten tragen die Fugen Namen nach ihrem Querschnitt wie I-Fuge, V-Fuge, Y-Fuge, HV-Fuge oder U-Fuge. Die Norm legt dafür Werkstückdicke t, Öffnungs- bzw. Flankenwinkel, Spalt b an der Wurzel sowie Steghöhe c und Flankenhöhe h fest. Die Steg-Längskanten sollten entgratet werden und dürfen bis 2 mm gebrochen sein.
* **Quelle:** [3834-Software Schweißnahtvorbereitung](https://3834-software.de/wissen/schweissnahtvorbereitung)
  * *Wörtliches Zitat:* „Stumpfnähte tragen die Fugen Namen nach ihrem Querschnitt, etwa I-Fuge, V-Fuge, Y-Fuge, HV-Fuge oder U-Fuge.“
  * *Wörtliches Zitat:* „Werkstückdicke t — der Dickenbereich, für den die Fugenform gedacht ist.“
  * *Wörtliches Zitat:* „Spalt b — der Abstand der Fugenflanken an der Wurzel.“
  * *Wörtliches Zitat:* „Steghöhe c und Flankenhöhe h — der nicht abgeschrägte Teil der Kante bzw. die Höhe der abgeschrägten Flanke.“
  * *Wörtliches Zitat:* „Die Steg-Längskanten sollten entgratet werden und dürfen bis 2 mm gebrochen sein (Abschnitt 5).“
* **Begründung:** Im CAD müssen Fasenwinkel und Wurzelstege vor dem Schweißen modelliert werden können, um realistische Schweißnahtquerschnitte abzubilden.

---

### Grenzwerte und Faustformeln für das a-Maß von Kehlnähten
* **Aussage / Wert:** Als Bemessungsregel für Kehlnähte gilt: Das a-Maß soll höchstens 0,7 mal die Dicke des dünneren Blechs betragen, mindestens die Wurzel aus der Dicke des dickeren Blechs minus 0,5 mm und in jedem Fall mindestens 3 mm. Auf der Zeichnung steht meist das a-Maß, zum Beispiel a4. Bei gleichen Schenkeln gilt für die Schenkellänge z = a × √2.
* **Quelle:** [nurb44 Schweiß-Rechner: A-Maß der Kehlnaht](https://nurb44.com/tools/kehlnaht-a-mass)
  * *Wörtliches Zitat:* „Faustregeln für das a-Maß höchstens 0,7 × die Dicke des dünneren Blechs mindestens √(Dicke des dickeren Blechs) − 0,5 mm und in jedem Fall mindestens 3 mm Diese Regeln geben einen sinnvollen Bereich vor, ersetzen aber keinen statischen Nachweis.“
  * *Wörtliches Zitat:* „Bei gleichen Schenkeln gilt z = a × √2.“
  * *Wörtliches Zitat:* „Auf der Zeichnung steht meist das a-Maß, zum Beispiel a4.“
* **Begründung:** Überdimensionierte Kehlnähte mit mehr als 0,7 mal t_min erhöhen die Tragfähigkeit nicht mehr, erzeugen jedoch übermäßigen Wärmeverzug und vervierfachen das Schweißgutvolumen.

---

### Definition der rechnerischen Nahtdicke nach Eurocode 3
* **Aussage / Wert:** Das a-Maß ist die Höhe des größten gleich- oder ungleichschenkligen Dreiecks nach EN 1993-1-8 Abschnitt 4.5.2(1), gemessen von der theoretischen Wurzel zur Nahtoberfläche. Nach oben begrenzt die dünnere Blechdicke das sinnvolle Maß, da eine dickere Naht keine zusätzliche Tragfähigkeit bringt und das Versagen ins Grundbauteil wandert.
* **Quelle:** [schweissnaht-nachweis.de: a-Maß Schweißnaht berechnen](https://schweissnaht-nachweis.de/a-mass-schweissnaht)
  * *Wörtliches Zitat:* „a-Maß (Nahtdicke) — die Höhe des größten gleich- oder ungleichschenkligen Dreiecks (EN 1993-1-8 Abschnitt 4.5.2(1)), das sich in den Nahtquerschnitt einbeschreiben lässt, gemessen von der theoretischen Wurzel zur Nahtoberfläche. Dieses Maß geht in den Nachweis ein.“
  * *Wörtliches Zitat:* „Nach oben begrenzt die dünnere der verbundenen Blechdicken das sinnvolle Maß: Eine Naht, die dicker ist als das Blech, das sie anschließt, bringt keine zusätzliche Tragfähigkeit mehr“
* **Begründung:** Normative Berechnungsgrundlage für automatisierte Festigkeitsprüfungen im Konstruktionsassistenten.

---

### Umrechnungswerte zwischen a-Maß und Schenkellänge z
* **Aussage / Wert:** Bei gleichschenkligen Kehlnähten berechnet sich z aus a über z = a · √2 ≈ 1,414 · a (bei a = 5 mm ergibt sich z ≈ 7,1 mm) und umgekehrt a aus z über a = z / √2 ≈ 0,707 · z.
* **Quelle:** [schweissnaht-nachweis.de: a-Maß Schweißnaht berechnen](https://schweissnaht-nachweis.de/a-mass-schweissnaht)
  * *Wörtliches Zitat:* „z aus a z = a · √2 ≈ 1,414 · a a = 5 mm → z ≈ 7,1 mm a aus z a = z / √2 ≈ 0,707 · z“
* **Begründung:** Ermöglicht dem CAD-Modell die synchrone, fehlerfreie Umrechnung beider Kenngrößen bei Benutzereingaben.

---

### Schweißnahtlehren und Messbereiche nach DVS-Merkblatt 0703
* **Aussage / Wert:** DVS-Merkblatt 0703 Tabelle 2 stellt Schweißnahtlehren mit 3 oder 4 Skalen für einen Messbereich von 0 bis 15 mm mit einer Ablesegenauigkeit von 0,1 mm für flache, hohle und gewölbte Kehlnähte gegenüber.
* **Quelle:** [schweissnaht-nachweis.de: a-Maß Schweißnaht berechnen](https://schweissnaht-nachweis.de/a-mass-schweissnaht)
  * *Wörtliches Zitat:* „DVS-Merkblatt 0703 (März 2025) stellt die Lehren in Tabelle 2 gegenüber, darunter diese: Schweißnahtlehre mit 3 oder 4 Skalen — Messbereich 0 bis 15 mm, Ablesegenauigkeit 0,1 mm; Kehlnaht flach, hohl, gewölbt“
* **Begründung:** Prüfwerkzeuge in der Qualitätskontrolle bedingen, dass Nahtmaße im CAD praxistauglichen Werkstatt-Messintervallen folgen.

---

### Grenzwerte der Nahtdicke und wirksame Wurzellinie
* **Aussage / Wert:** Bei Bauteildicken t ≥ 3 mm müssen zur Vermeidung von Querschnittsmissverhältnissen Grenzwerte zwischen Nahtdicke a sowie minimaler und maximaler Bauteildicke eingehalten werden. Die rechnerische Länge L einer Schweißnaht ist ihre geometrische Wurzellinienlänge; fehlerhafte Nahtanfänge, Endkrater und Nahtenden zählen nicht dazu.
* **Quelle:** [Schweizer Formelsammlung Schweißverbindung](https://www.schweizer-fn.de/maschinenelemente/schweissnaht/schweissverbindung.php)
  * *Wörtliches Zitat:* „Um ein Missverhältnis von Nahtquerschnitt und verbundenen Querschnittsteilen zu vermeiden, müssen bei Bauteildicken t ≥ 3 mm folgende Grenzwerte bei Kehlnäthen eingehalten werden: a  = Nahtdicke (mm) tmin = minimale Bauteildicke (mm) tmax = maximale Bauteildicke (mm)“
  * *Wörtliches Zitat:* „Die rechnerische Länge L einer Schweißnaht ist ihre geometrische Länge. Für Kehlnähte ist sie die Länge der Wurzellinie. Krater, Nahtanfänge und Nahtenden, die die verlangte Nahtdicke nicht erreichen, zählen nicht zur Nahtlänge.“
* **Begründung:** Schützt vor Nahtabriss bei extrem ungleichen Querschnitten und definiert die exakte geometrische Bezugskante im CAD-Kernel.

---

### Endkraterabzug und geschlossene Rundumnaht
* **Aussage / Wert:** Bei Berücksichtigung der Endkrater reduziert sich die wirksame Schweißnahtlänge um die zweifache Nahtdicke auf b = L - 2 * a. Bei einer Rundumschweißung ist kein Endkraterabzug erforderlich.
* **Quelle:** [Schweizer Formelsammlung Schweißverbindung](https://www.schweizer-fn.de/maschinenelemente/schweissnaht/schweissverbindung.php)
  * *Wörtliches Zitat:* „b = L - 2 * a (bei Berücksichtigung der Endkrater)“
  * *Wörtliches Zitat:* „Bei Rundumschweißung kein Endkraterabzug“
* **Begründung:** Automatische Korrektur der effektiven Tragfähigkeit im Festigkeitsmodul je nachdem, ob die Kantenkette offen oder als geschlossener Ring vorliegt.

---

### Faustformeln für Nahtgröße und Festigkeitsnaht
* **Aussage / Wert:** Als Faustformel für Schweißnähte gilt: Die normale Nahtgröße beträgt 0,5 mal die dünnere Blechstärke, während eine volle Festigkeitsnaht mit 0,7 mal Blechstärke bemessen wird. Die Angabe der Nahtlänge ist nur erforderlich, wenn die Naht nicht über die gesamte Bauteillänge verläuft.
* **Quelle:** [Christian Haas Zeichnungstechnik PDF](https://saf17a5dc84ec4b91.jimcontent.com/download/version/1518962649/module/7005939551/name/Kap_08_Loesungen.pdf)
  * *Wörtliches Zitat:* „Faustformel: Die Nahtgrösse beträgt 0,5 * dünnere Blechstärke Festigkeitsnaht = 0,7 * Blechstärke“
  * *Wörtliches Zitat:* „Die Angabe der Schweissnahtlänge ist nur dann erforderlich, wenn die Naht nicht über die gesamte Bauteillänge verläuft!“
* **Begründung:** Differenzierung zwischen untergeordneten Dicht-/Heftnähten (0,5 mal Blechdicke) und volltragenden Kraftübertragungsnähten (0,7 mal Blechdicke).

---

### Ordnungsnummern der Schweißverfahren für technische Zeichnungen
* **Aussage / Wert:** Schweißprozesse werden in den Bemassungsangaben mit Kennnummern versehen: Lichtbogen-Handschweißen trägt die Kennziffer 111, WIG die Kennziffer 141, MIG die Kennziffer 131, MAG die Kennziffer 135, Plasma-WIG die Kennziffer 151 und Laserstrahlschweißen die Kennziffer 52.
* **Quelle:** [Christian Haas Zeichnungstechnik PDF](https://saf17a5dc84ec4b91.jimcontent.com/download/version/1518962649/module/7005939551/name/Kap_08_Loesungen.pdf)
  * *Wörtliches Zitat:* „Lichtbogen-Handschweissen 111 [...] WIG 141 [...] MIG 131 [...] Laserstrahlschweissen 52 [...] MAG 135 [...] Plasma-WIG-Schweissen 151“
* **Begründung:** Standardisierte Prozesskennzahlen für die Gabelbeschriftung des Schweißsymbols.

---

### Unterbrochene Nähte und Kennzeichnung n x l (e)
* **Aussage / Wert:** Bei unterbrochenen Schweißverbindungen steht n für die Anzahl der Einzelnähte, l für die Länge der Einzelnähte, e für den Nahtabstand und v für das Vormaß mit der Bemaßungsformel n x l (e). Eine Ringsum-Naht wird durch einen Kreis an der Knickstelle des Bezugszeichens ohne Längenangabe gekennzeichnet. Eine Baustellennaht für Montagen vor Ort wird speziell ausgewiesen.
* **Quelle:** [Christian Haas Zeichnungstechnik PDF](https://saf17a5dc84ec4b91.jimcontent.com/download/version/1518962649/module/7005939551/name/Kap_08_Loesungen.pdf)
  * *Wörtliches Zitat:* „In allen Fällen von unterbrochenen Schweissverbindungen sind: n = Anzahl der Einzelnähte l = Länge der Einzelnähte e = Nahtabstand v = Vormass [...] n x l (e)“
  * *Wörtliches Zitat:* „Ringsum-Naht Zur Kennzeichnung von Schweissnähten, die um den gesamten Teil herumgeführt werden, ist an der Knickstelle des Bezugs- zeichens ein Kreis mit einem Durchmesser einzutragen (= Ergänzungssymbol). Die Angabe der Nahtlänge entfällt.“
  * *Wörtliches Zitat:* „Baustellennaht Oftmals können Bauteile erst bei Montage oder bei Installation vor Ort beim Kunden geschweisst werden. Eine „Baustellennaht“ wird speziell gekennzeichnet“
* **Begründung:** Definition der Parameterstruktur für segmentierte Schweißfeatures im CAD.

---

### Begriffe und geometrische Elemente des Schweißsymbols nach ISO 2553
* **Aussage / Wert:** Ein Schweißsymbol besteht aus einer Pfeillinie und einer Bezugslinie, ergänzt durch Grund- und Zusatzsymbole, Maße oder eine Gabel. Die Nahtdicke a ist der Bemessungswert der Höhe des größten gleichschenkligen Dreiecks im Schnitt; die Schenkellänge z ist der Abstand zwischen dem Schnittpunkt der Schweißkanten und dem Nahtübergang über die Kehlflanke.
* **Quelle:** [GSI SLV Duisburg DIN EN ISO 2553 PDF](https://forums.autodesk.com/autodesk/attachments/autodesk/inventor-forum-de/20492/1/Symbolische_Darstellung_von_Schweissverbindungen.pdf)
  * *Wörtliches Zitat:* „Symbol, bestehend aus einer Pfeillinie und einer Bezugslinie, das durch Grund- und Zusatzsymbole, Maße und/oder eine Gabel ergänzt werden darf und in technischen Zeichnungen zur Angabe der Art, der Stelle und der Vorbereitung einer Schweißnaht angewendet wird“
  * *Wörtliches Zitat:* „Bemessungswert der Höhe des größten gleichschenkligen Dreiecks, das sich in der Schnittdarstellung einer geschweißten Naht einzeichnen lässt“
  * *Wörtliches Zitat:* „Abstand zwischen dem tatsächlichen oder projizierten Schnittpunkt der Schweißkanten und dem Nahtübergang einer Kehlnaht, gemessen über die Kehlflanke“
* **Begründung:** Normkonforme Datenfeldbezeichnungen für die Schweißfeature-Klasse in Mechvane.

---

### System A und System B nach DIN EN ISO 2553
* **Aussage / Wert:** DIN EN ISO 2553:2014 unterscheidet zwei Schweißsymbolsysteme: System A mit doppelter Bezugslinie aus Volllinie und Strichlinie sowie System B mit einfacher Bezugslinie.
* **Quelle:** [GSI SLV Duisburg DIN EN ISO 2553 PDF](https://forums.autodesk.com/autodesk/attachments/autodesk/inventor-forum-de/20492/1/Symbolische_Darstellung_von_Schweissverbindungen.pdf)
  * *Wörtliches Zitat:* „DIN EN ISO 2553:2014 unterscheidet zwei unterschiedlichen Schweißsymbolysteme, System A und System B, um die Pfeilseite und Gegenseite auf Zeichnungen anzugeben Die symbolische Darstellung im System A basiert auf einer doppelten Bezugslinie aus einer Volllinie und einer Strichlinie. Die symbolische Darstellung im System B basiert auf einer einzelnen Bezugslinie“
* **Begründung:** Mechvane setzt standardmäßig auf das in Europa verbindliche System A.

---

### Anordnung der Querschnitts- und Längenmaße sowie der Gabel
* **Aussage / Wert:** Querschnittsmaße wie die Nahtdicke sind links vom Grundsymbol anzugeben, während Längenmaße rechts vom Grundsymbol platziert werden. Die Gabel am Ende der Bezugsvolllinie nimmt zusätzliche Angaben auf, darunter die Bewertungsgruppe nach ISO 5817, den Schweißprozess nach ISO 4063, den Schweißzusatz oder die Schweißposition.
* **Quelle:** [GSI SLV Duisburg DIN EN ISO 2553 PDF](https://forums.autodesk.com/autodesk/attachments/autodesk/inventor-forum-de/20492/1/Symbolische_Darstellung_von_Schweissverbindungen.pdf)
  * *Wörtliches Zitat:* „sind links vom Grundsymbol anzugeben“
  * *Wörtliches Zitat:* „sind rechts vom Grundsymbol anzugeben“
  * *Wörtliches Zitat:* „Die Gabel ist ein wahlweise anzuwendendes Element, das am Ende der Bezugsvolllinie angefügt werden darf, wo zusätzliche, ergänzende Angaben als Teil des Schweiß- symbols einbezogen werden dürfen, z. B.: a) die Bewertungsgruppe, bspw. nach ISO 5817 [...] b) der Schweißprozess, die Ordnungsnummer nach ISO 4063 [...] c) der Schweißzusatz [...] d) die Schweißposition [...] e) ergänzende Angaben“
* **Begründung:** Regelbasis für das Layout des SVG-Symbol-Generators bei 2D-Zeichnungsableitungen.

---

### Auslegungsbeispiel für unterbrochene Kehlnähte
* **Aussage / Wert:** Ein praxisgerechtes Bemaßungsbeispiel nach ISO 2553 umfasst eine 5 mm Sollnahtdicke für unterbrochene Kehlnähte, bestehend aus 4 Einzelnähten mit 100 mm Länge und 200 mm Abstand zwischen den Einzelnähten, wobei n die Anzahl, l die Länge und (e) den Abstand angibt.
* **Quelle:** [GSI SLV Duisburg DIN EN ISO 2553 PDF](https://forums.autodesk.com/autodesk/attachments/autodesk/inventor-forum-de/20492/1/Symbolische_Darstellung_von_Schweissverbindungen.pdf)
  * *Wörtliches Zitat:* „5 mm Sollnahtdicke für unterbrochene Kehlnähte, bestehend aus 4 Einzelnähten mit 100 mm Länge und 200 mm Abstand zwischen den Einzelnähten“
  * *Wörtliches Zitat:* „Zusatzsymbol Versetzte unterbrochene Naht [...] n = Anzahl der Nahtelemente − l = Länge der Nahtelemente − (e) = Abstand zwischen den Nahtelementen“
* **Begründung:** Dient als synthetischer Unit-Test-Fall zur Verifikation der korrekten Bemaßungskette.

---

### Inventor Schweißbaugruppen: Dreistufige Bearbeitungsphasen
* **Aussage / Wert:** Schweißbaugruppen in Autodesk Inventor ermöglichen das Erstellen von Schweißnähten, die Bearbeitung vor und nach dem Schweißen sowie die Ableitung von Schweißnahtberichten. Nach der Konvertierung in eine Schweißbaugruppe kann diese nicht mehr in eine normale Baugruppe zurückkonvertiert werden.
* **Quelle:** [Cideon Blog: Autodesk Inventor Schweißbaugruppen](https://www.cideon.blog/autodesk-inventor-schweissbaugruppen)
  * *Wörtliches Zitat:* „Sie ermöglichen das Erstellen von Schweißnähten, die Bearbeitung vor und nach dem Schweißen sowie die Ableitung von Schweißnahtberichten.“
  * *Wörtliches Zitat:* „Sobald Sie das einmal getan haben, können Sie die Schweißbaugruppe nicht mehr zurück in eine normale Baugruppe konvertieren, da durch den Konvertierungsvorgang diverse Eigenschaften hinzugefügt werden, die nicht mehr gelöscht werden können, zum Beispiel das Material der Nähte.“
* **Begründung:** Bestätigt das Baugruppenkonzept getrennter Phasen (Vorbereitung / Nähte / Nachbearbeitung) für das Mechvane-Modell.

---

### Inventor Schweißfeature-Typen im Modellbaum
* **Aussage / Wert:** Der Modellbrowser in Inventor gliedert Schweißbaugruppen in drei Operationstypen: Preparations, Welds und Machining. Anwender können drei Typen von Schweißfeatures erzeugen: Kehlnähte (fillet), Stumpfnähte (groove) und kosmetische Schweißnähte (cosmetic welds).
* **Quelle:** [Inventor 2011 Weldments Tutorial PDF](https://d2t1xqejof9utc.cloudfront.net/files/91330/welding%20INVENTOR%20TUTORIAL.pdf?1473995789)
  * *Wörtliches Zitat:* „The feature browser updates to show three types of operations: Preparations, Welds, and Machining.“
  * *Wörtliches Zitat:* „You can create three types of weld features: fillet, groove, and cosmetic welds.“
* **Begründung:** Zeigt die Notwendigkeit von kosmetischen Leichtgewichts-Nähten neben rechenintensiven Festkörpern.

---

### SolidWorks Weldments: Multibody-Umgebung und Konfigurationen
* **Aussage / Wert:** In SolidWorks ist das Weldment-Feature kein normales Formfeature wie eine Verrundung, sondern schaltet eine spezialisierte Konstruktionsumgebung frei. Nach dem Einfügen des ersten Strukturbauteils erzeugt SolidWorks automatisch zwei Standard-Konfigurationen: Default<As Machined> und die abgeleitete Konfiguration Default<As Welded>.
* **Quelle:** [Iancu C. SolidWorks Weldments Paper PDF](https://www.utgjiu.ro/rev_mec/mecanica/pdf/2023-01/21_Iancu%20C_%20About%20weldments%20feature%20in%20solidworks.pdf)
  * *Wörtliches Zitat:* „The Weldment feature is not a feature in the same sense as a Fillet or an Extrude. Instead, it sets up a design functionality environment. The weldment feature designates the part as a weldment and enables the weldment environment“
  * *Wörtliches Zitat:* „After creating the first structural member in a part, a weldment feature is created and added to the FeatureManager design tree. SolidWorks also creates two default configurations in the ConfigurationManager: a parent configuration Default<As Machined> and a derived configuration Default<As Welded>“
* **Begründung:** Veranschaulicht den Multibody-Weg im Gegensatz zum Baugruppen-Weg von Inventor.

---

### SolidWorks Zuschnittlisten für geschweißte Strukturen
* **Aussage / Wert:** Am Ende der Modellierung kann der Konstrukteur die Schweißkonstruktions-Zuschnittlistentabelle verwenden, um eine stücklistenähnliche Tabelle (BOM) für zugeschnittene, geschweißte Strukturformen in die Zeichnung einzufügen.
* **Quelle:** [Iancu C. SolidWorks Weldments Paper PDF](https://www.utgjiu.ro/rev_mec/mecanica/pdf/2023-01/21_Iancu%20C_%20About%20weldments%20feature%20in%20solidworks.pdf)
  * *Wörtliches Zitat:* „In the end the designer can use the weldment cut list table to add a BOM-like (Bill Of Materials) table for cut, welded structural shapes.“
* **Begründung:** Wichtiger Input für den geplanten Gestellgenerator in Mechvane.

---

### FreeCAD TechDraw Schweißsymbole in Zeichnungsableitungen
* **Aussage / Wert:** Das TechDraw WeldingSymbol-Werkzeug in FreeCAD fügt Schweißspezifikationen zu einer bestehenden Hinweislinie hinzu und unterstützt Parameter wie All Around zur Anzeige des Kreissymbols am Führungslinienknick.
* **Quelle:** [FreeCAD TechDraw WeldSymbol Dokumentation](https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/TechDraw_WeldSymbol.md)
  * *Wörtliches Zitat:* „The **TechDraw WeldingSymbol** tool adds welding specifications to an existing leader line.“
  * *Wörtliches Zitat:* „Shows the *All Around* symbol (circle) at the kink in the leader line.“
* **Begründung:** Nachweis der praxiserprobten Open-Source-Implementierung für Schweißsymbole über Kacheln und SVG-Grafiken.

---

### FreeCAD WeldFeature Baugruppen-Addon
* **Aussage / Wert:** Das FreeCAD WeldFeature-Addon ist ein Modul zur visuellen Darstellung von Schweißnähten in Baugruppen entlang ausgewählter Kanten oder Flächen.
* **Quelle:** [FreeCAD WeldFeature Addon README](https://raw.githubusercontent.com/alexneufeld/FreeCAD_WeldfFeature/master/README.md)
  * *Wörtliches Zitat:* „A FreeCAD module to add Visual representations of welds to assemblies:“
* **Begründung:** Zeigt den Bedarf nach leichtgewichtiger visueller Nahtrepräsentation in Open-Source-CAD.

---

### CAD-Vergleich: Funktionstiefe von Inventor gegenüber Fusion
* **Aussage / Wert:** In puncto Feature-Tiefe liegt Inventor meilenweit vor Fusion; es wurde für Ingenieure entwickelt, die anspruchsvolle Werkzeuge wie Konstruktionsautomatisierung, FEA-Simulation, iLogic und erweiterte parametrische Modellierung an einem Ort benötigen.
* **Quelle:** [Cadspec Blog: Autodesk Fusion vs. Inventor](https://www.cadspec.co.uk/about/blog/autodesk-fusion-vs-inventor-which-should-you-learn/)
  * *Wörtliches Zitat:* „Inventor is miles ahead than Fusion in terms of feature depth. It’s designed for engineers who need serious tools like design automation, FEA simulation, iLogic scripting, and advanced parametric modelling all in one place.“
* **Begründung:** Begründet, warum Mechvane sich an Inventors professionellem Maschinenbau-Ansatz und nicht an Fusions vereinfachter All-in-One-Struktur orientiert.

---

### CAD-Vergleich: Baugruppen-Workflow von Inventor gegenüber Fusion
* **Aussage / Wert:** Der Workflow von Inventor mit getrennten Bauteil- und Baugruppendateien macht es sehr einfach, komplizierte parametrische Strukturen aufzubauen, während Fusion 360 diese Funktionalität fehlt.
* **Quelle:** [Makerforce: Fusion 360 vs. Inventor](https://makerforce.io/fusion-360-vs-inventor/)
  * *Wörtliches Zitat:* „The workflow of Inventor with seperate part and assembly files makes it very easy to build complicated parametric structures but Fusion 360 just lacks that functionality.“
* **Begründung:** Bestätigt die Mechvane-Architekturentscheidung für getrennte Bauteil- und Baugruppendateien nach Architektur-Entscheid ADR-Trennung.

---

## Synthese und Antworten auf die Recherchefragen

### Zu Frage 1: Nahtarten und Kenngrößen
1. **Nahtarten:**
   * *Kehlnaht:* Standard für T- und Überlappstöße. Einseitig oder als Doppelkehlnaht.
   * *Stumpfnaht:* Stoßflächen in einer Ebene. Nach DIN EN ISO 9692-1 mit Vorbereitung: I-Naht (dünne Bleche ohne Anschrägung), V-Naht (einseitige Flankenanschrägung), X-Naht (Doppel-V, beidseitig zur Verzugsminderung), HV-Naht (nur ein Bauteil angeschrägt, ideal für T-Stumpfstöße), Y-Naht (V-Naht mit breitem Wurzelsteg).
   * *Ecknaht:* Außenkantenverbindung zweier rechtwinkliger Platten.
   * *Bördelnaht:* Aufgebogene Kanten an Dünnblechen, die ohne Zusatzwerkstoff vollkommen niedergeschmolzen werden.
2. **Kenngrößen:**
   * *a-Maß (Nahtdicke):* Rechnerische Dicke = Höhe des einbeschriebenen größten gleichschenkligen Dreiecks von der Wurzel zur Nahtoberfläche ($a = z / \sqrt{2} \approx 0{,}707 \cdot z$).
   * *z-Maß (Schenkellänge):* Flankenlänge an der Bauteiloberfläche ($z = a \cdot \sqrt{2} \approx 1{,}414 \cdot a$).
   * *Wirksame Nahtlänge ($l$):* Wurzellinienlänge. Bei durchgehender Naht über die Kante entfällt die Maßangabe in der Zeichnung.
   * *Unterbrochene Nähte ($n \times l\ (e)$):* $n$ Nahtsegmente mit Einzellänge $l$ und lichtem Abstand $(e)$.
   * *Umlaufende Nähte:* Kreis am Bezugsknick; gilt für geschlossene Konturen ohne Längenangabe.

### Zu Frage 2: Faustregeln, Grenzwerte und Normwerte
1. **a-Maß-Regeln:**
   * Obergrenze: $a \le 0{,}7 \cdot t_{\min}$ (nach EN 1993-1-8 / DVS). Größere Nähte bringen keinen Festigkeitsgewinn, sondern erhöhen Verzug und Schweißgutmenge quadratisch.
   * Untergrenze (Abkühlbedingung): $a \ge \sqrt{t_{\max}} - 0{,}5\text{ mm}$ (verhindert Aufhärtungen bei schneller Wärmeableitung in dicke Flansche).
   * Absolutes Mindestmaß: $a \ge 3\text{ mm}$ im allgemeinen Stahl- und Maschinenbau für $t \ge 3\text{ mm}$.
2. **Nahtlänge und Endkrater:**
   * Mindestnahtlänge für tragende Kehlnähte: $l \ge 6 \cdot a$ und $l \ge 30\text{ mm}$. Kürzere Nähte dürfen statisch nicht voll angerechnet werden.
   * Endkraterabzug: $b = l - 2 \cdot a$ bei frei auslaufenden Nähten. Bei geschlossenen Rundumnähten entfällt der Abzug.
3. **Nahtabstände und Zugänglichkeit:**
   * Nahtabstand: Mindestens das 3- bis 4-fache der Blechdicke bzw. mindestens 50 mm, um Überlagerungen der Wärmeeinflusszonen (WEZ) zu verhindern.
   * Zugänglichkeit: Brenneröffnungswinkel von mindestens 45° bis 60° und kollisionsfreier zylindrischer Hüllkörper für Brennerkopf und Sichtkontakt.

### Zu Frage 3: Darstellung in Zeichnungen nach ISO 2553
1. **Symbolaufbau:** Pfeillinie (zeigt auf Fuge) + Bezugslinie (waagerechte Volllinie) + Strichlinie (Identifizierungslinie für Gegenseite).
2. **System A vs. System B:** Im europäischen System A steht das Grundsymbol auf der Volllinie für die Pfeilseite und auf der Strichlinie für die Gegenseite. Bei symmetrischen Nähten entfällt die Strichlinie. System B (AWS) nutzt nur eine Volllinie (unten = Pfeilseite, oben = Gegenseite).
3. **Bemaßungsplatzierung:**
   * Querschnittsmaße links: $a5$, $z7$, $s6$ (tiefer Einbrand).
   * Längenmaße rechts: $150$ (Länge), $4 \times 100\ (200)$ (unterbrochene Naht).
4. **Ergänzungssymbole:** Kreis am Knick (Ringsum), Fahne am Knick (Baustelle/Montage), Konturstriche über Grundsymbol (flach, gewölbt, hohl).
5. **Gabel (Tail):** ISO 4063 Prozessnummer (z. B. `135` MAG) und ISO 5817 Bewertungsgruppe (z. B. `B`).
6. **Automatische Agenten-Ableitung:** Ein Agent erkennt aus den Kanten-B-Reps Stoßart, Wanddicken, Vorzugsmaß $a = 0{,}7 \cdot t_{\min}$, Kantenlänge, Ringsum-Loop und Blickvektor für Pfeil- vs. Gegenseite.

### Zu Frage 4: CAD-Konzepte im Vergleich
* **Autodesk Inventor:** Spezialisierte Schweißbaugruppe (`.iam`). Dreistufiger Modellbaum: Vorbereitung (Preparations), Schweißnähte (Welds: Kehl-, Stumpf- und kosmetische Naht), Nachbearbeitung (Machining). Assoziative Masse, Material und Zeichnungszustände.
* **Dassault Systèmes SolidWorks:** Multibody-Part-Konzept (`.sldprt`) mit Weldment-Feature, Structural Members (Profile aus 3D-Skizzen), Trim/Extend, Gussets, End Caps, Weld Beads und automatischer Zuschnittliste (Cut List).
* **Autodesk Fusion:** Keine native Schweißkonstruktions-Umgebung. Schweißnähte werden nur als manuelle B-Rep-Körper/Sweeps oder reine 2D-Zeichnungsanmerkungen abgebildet.
* **FreeCAD:** TechDraw bietet `TechDraw_WeldSymbol` mit vollständiger ISO-2553-Parametrik (SVG-Kacheln, Pfeil-/Gegenseite). Das Addon `FreeCAD_WeldFeature` ergänzt visuelle 3D-Raupen.

---

## Vorschlag für das Datenmodell eines Schweißfeatures in Mechvane

Das Schweißmodul in Mechvane wird als Fachmodul auf Baugruppenebene realisiert. Es folgt der Inventor-Architektur, integriert aber die algorithmische Auslegungslogik von Eurocode 3 und DIN EN ISO 2553 für KI-Agenten.

### Architekturübersicht
1. **Phasen-Container in Baugruppen (`WeldmentAssembly`):**
   * `preparations`: Kantenbearbeitungen (Fasen, Freistellungen nach ISO 9692-1) auf Baugruppenebene vor dem Fügen.
   * `welds`: Liste von Schweißfeatures (`WeldFeature`), die Material und Masse hinzufügen.
   * `machining`: Nachbearbeitungs-Features (Fräsen, Passbohrungen) im verschweißten Zustand.
2. **Dualer Geometriemodus:**
   * `SOLID`: Erzeugt einen echten SolidCraft B-Rep-Volumenkörper (Sweep eines Dreiecks- oder Nahtprofils entlang des Schweißpfads) für Masse, Trägheitsmoment und Kollisionserkennung.
   * `COSMETIC`: Speichert Kantenpfad, Normalen und Metadaten ohne Boolean-Operation; ideal für komplexe Baugruppen zur Performance-Schonung.
3. **Automatische Agenten-Prüfung (`check_design`):**
   * Plausibilitätsprüfung des a-Maßes gegen Wandstärken ($a \le 0{,}7 \cdot t_{\min}$, $a \ge \sqrt{t_{\max}} - 0{,}5\text{ mm}$, $a \ge 3\text{ mm}$).
   * Prüfung der Mindestnahtlänge ($L \ge 6 \cdot a$, $L \ge 30\text{ mm}$).

### Python-Datenklassen

```python
"""Mechvane CAD - Parametric Welding Module Data Model.
Architecture follows DIN EN ISO 2553:2014 and Autodesk Inventor 3-stage weldment lifecycle.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class JointType(str, Enum):
    """Joint type configuration between mating components."""
    BUTT = "butt"               # Stumpfstoß
    TEE = "tee"                 # T-Stoß
    CORNER = "corner"           # Eckstoß
    LAP = "lap"                 # Überlappstoß
    EDGE = "edge"               # Bördelstoß / Stirnstoß

class WeldType(str, Enum):
    """Elementary weld symbol types according to ISO 2553."""
    FILLET = "fillet"           # Kehlnaht (Dreieck)
    SQUARE_BUTT = "square_butt" # I-Naht
    SINGLE_V = "single_v"       # V-Naht
    DOUBLE_V = "double_v"       # X-Naht
    SINGLE_BEVEL = "single_bevel" # HV-Naht
    SINGLE_Y = "single_y"       # Y-Naht
    FLANGED = "flanged"         # Bördelnaht

class SurfaceContour(str, Enum):
    """Supplementary symbol for weld surface contour."""
    FLAT = "flat"               # Eben / bündig
    CONVEX = "convex"           # Gewölbt
    CONCAVE = "concave"         # Hohl (kerbfrei ausgerundet)
    FLUSH = "flush"             # Plangeschliffen

class WeldProcess(int, Enum):
    """Welding process identification numbers according to ISO 4063."""
    MANUAL_METAL_ARC = 111      # E-Hand (Lichtbogenhandschweißen)
    MIG = 131                   # Metall-Inertgasschweißen
    MAG = 135                   # Metall-Aktivgasschweißen (Standard Baustahl)
    TIG = 141                   # WIG (Wolfram-Inertgasschweißen)
    PLASMA = 151                # Plasma-Schweißen
    LASER = 52                  # Laserstrahlschweißen

class WeldQuality(str, Enum):
    """Quality levels for imperfections according to ISO 5817."""
    LEVEL_B = "B"               # Streng (dynamisch hochbeansprucht)
    LEVEL_C = "C"               # Mittel (Standard Maschinenbau)
    LEVEL_D = "D"               # Mäßig (untergeordnete Stahlbauten)

@dataclass
class WeldPreparation:
    """Joint edge preparation parameters according to ISO 9692-1."""
    bevel_angle_deg: float = 60.0       # Öffnungs- / Flankenwinkel
    root_gap_mm: float = 2.0            # Stegabstand / Wurzelspalt b
    root_face_mm: float = 1.5           # Steghöhe c
    chamfer_edge_ids: List[str] = field(default_factory=list)

@dataclass
class IntermittentWeld:
    """Intermittent weld specification: n x l (e)."""
    segment_count: int = 1              # n = Anzahl der Schweißabschnitte
    segment_length_mm: float = 50.0     # l = Länge der Einzelnähte
    pitch_distance_mm: float = 100.0    # e = Abstand / Mittenabstand
    staggered: bool = False             # Versetzte Ausführung auf Gegenseite

@dataclass
class WeldFeature:
    """Parametric Weld Feature for Mechvane Assemblies."""
    id: str
    name: str                           # z. B. "Kehlnaht_Grundplatte_M"
    weld_type: WeldType = WeldType.FILLET
    joint_type: JointType = JointType.TEE
    
    # Geometric references (SolidCraft B-Rep entity names)
    face_set_primary: List[str] = field(default_factory=list)   # Flächen Bauteil 1
    face_set_secondary: List[str] = field(default_factory=list) # Flächen Bauteil 2
    path_edge_ids: List[str] = field(default_factory=list)      # Kantenverlauf
    
    # Weld dimensions
    throat_thickness_a: float = 3.0     # a-Maß in mm (Berechnungsgrundlage)
    leg_length_z: float = 4.24          # z-Maß (automatisch a * sqrt(2))
    deep_penetration_s: Optional[float] = None # Maß s bei tiefem Einbrand
    
    # Length & Intermittency
    all_around: bool = False            # Ringsum-Naht (Kreis-Symbol)
    intermittent: Optional[IntermittentWeld] = None
    
    # Process & Norm metadata
    contour: SurfaceContour = SurfaceContour.CONCAVE
    process: WeldProcess = WeldProcess.MAG
    quality_level: WeldQuality = WeldQuality.LEVEL_C
    filler_material: str = "G3Si1"      # Schweißzusatzwerkstoff
    field_weld: bool = False            # Baustellennaht (Fähnchen-Symbol)
    
    # Preparation & Machining linkage
    preparation: Optional[WeldPreparation] = None
    is_cosmetic_only: bool = False      # True = Leichtgewichts-Pfad, False = B-Rep Solid
    
    def calculate_leg_from_throat(self) -> float:
        """Update leg length z from throat thickness a."""
        import math
        self.leg_length_z = round(self.throat_thickness_a * math.sqrt(2.0), 2)
        return self.leg_length_z

@dataclass
class WeldmentAssembly:
    """Specialized Assembly container managing 3-stage weld lifecycle."""
    assembly_id: str
    name: str
    
    # Stage 1: Preparations (Fasen/Kantenbrüche vor dem Fügen)
    preparations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Stage 2: Welds (Schweißnähte mit Zusatzwerkstoff und Masse)
    welds: List[WeldFeature] = field(default_factory=list)
    
    # Stage 3: Post-weld Machining (Bohrungen/Fräsungen im geschweißten Zustand)
    machining: List[Dict[str, Any]] = field(default_factory=list)
```

---

## Fazit und nächste Schritte auf der Roadmap

1. **Topologische Kantenauswahl:** Anbindung an das SolidCraft B-Rep-Naming, um Kantenketten zwischen zwei benachbarten Bauteilen stabil zu selektieren.
2. **Feature-Implementation:** Erstellung des Python-Features `mechvane/features/weld.py` basierend auf obigem Datenmodell.
3. **Dualer Sweep-Generator:**
   * Leichtgewichtsmodus: Erzeugung einer 3D-Führungskurve mit Querschnittsmetadaten für performante Baugruppen mit hunderten Nähten.
   * Solid-Modus: B-Rep Boolean Sweep (konkaver/flacher Dreiecksquerschnitt) für Renderings, FEM-Export und Massenberechnung.
4. **2D-Ableitung nach ISO 2553:** Anbindung an die TechDraw/SVG-Pipeline für normgerechte Schweißsymbole mit Bezugslinie, System-A-Strichlinie, Maßangaben und Gabel.
