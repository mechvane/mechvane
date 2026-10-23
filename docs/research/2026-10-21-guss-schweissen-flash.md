> Gemini 3.8 Flash, nicht verifiziert. Recherche 2026-10-21.

# Guss- und Schweißkonstruktion: Fertigungsgerechte Gestaltungsregeln

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert  
Sprache: Deutsch

Dieses Dokument fasst die gussgerechten und schweißgerechten Konstruktionsregeln für metallische Bauteile zusammen. Es dient als Regelbasis für die algorithmische Geometrieprüfung (`check_design`) und parametrische Modellerstellung im Projekt **inventa**.

---

## Detaillierte Katalog-Einträge

### Guss: Wanddicken im NE-Druckguss für Aluminium, Zink und Magnesium
* **Aussage / Wert:** Im Druckguss sind möglichst gleichmäßige Wanddicken anzustreben. Richtwerte für gut herstellbare Wanddicken betragen: für Aluminiumlegierungen ab 0,8 bis 3 mm, für Zinklegierungen ab 0,3 bis 2 mm und für Magnesiumlegierungen ab 0,7 bis 3 mm.
* **Geltungsbereich:** Druckguss von Nichteisenmetallen (Aluminium, Zink, Magnesium).
* **Herkunft:** Verband / Technische Richtlinie (BDG – Bundesverband der Deutschen Gießerei-Industrie).
* **Quelle:** [BDG-Richtlinie: Druckguss aus NE-Metallen PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/druckguss_aus_ne-metallen.pdf)
  * *Wörtliches Zitat:* „für Aluminiumlegierungen ab 0,8 bis 3 mm [...] für Zinklegierungen ab 0,3 bis 2 mm [...] für Magnesiumlegierungen ab 0,7 bis 3 mm“
* **Begründung:** Zu geringe Wanddicken führen zu mangelhafter Formfüllung oder Unebenheiten; zu große Wanddicken verursachen Erstarrungslunker (Schrumpfungsporosität), längere Taktzeiten und Bauteilverzug.
* **Härte:** Hinweis (weiche Fertigungsgrenze; Dicken unter 0,8 mm bei Aluminium nur lokal zulässig).
* **Prüfstatus:** offen.

---

### Guss: Minimalwerte für Aushebeschrägen im Druckguss
* **Aussage / Wert:** Gemäß Tabelle 8.1 betragen die werkstoffabhängigen Minimalwerte für Aushebeschrägen bei Aluminium an Außenflächen 0,5° und für Innenflächen bei festem Kern 0,75°.
* **Geltungsbereich:** Lokale Funktionsflächen im NE-Druckguss (z. B. Lagersitze, Positionierhilfen).
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Druckguss aus NE-Metallen PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/druckguss_aus_ne-metallen.pdf), Tabelle 8.1, S. 24.
  * *Wörtliches Zitat:* „Tabelle 8.1: Werkstoffabhängige Minimalwerte für lokale Aushebeschrägen im Druckguss“
* **Begründung:** Unnachgiebige Stahlformen und die sofortige thermische Kontraktion des erstarrenden Metalls erfordern Entformungsschrägen, um Riefenbildung und Verzug beim Auswerfen zu verhindern.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn Entformungsschrägen bei Aluminium-Druckguss unter 0,5° liegen).
* **Prüfstatus:** offen.

---

### Guss: Richtwerte für allgemeine Aushebeschrägen im Druckguss
* **Aussage / Wert:** Gemäß Tabelle 8.2 liegen die empfohlenen Richtwerte für allgemeine Aushebeschrägen bei Aluminium an Außenflächen bei 0,7 bis 1° und für Innenflächen bei festem Kern bei 1,5 bis 2°.
* **Geltungsbereich:** Allgemeine Bauteilkonturen im Aluminium-Druckguss.
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Druckguss aus NE-Metallen PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/druckguss_aus_ne-metallen.pdf), Tabelle 8.2, S. 24.
  * *Wörtliches Zitat:* „Tabelle 8.2: Werkstoffabhängige Richtwerte für allgemeine Aushebeschrägen im Druckguss“
* **Begründung:** Aufschrumpfende Innenflächen greifen fester auf die Werkzeugkerne als Außenflächen und benötigen daher größere Schrägen (1,5 bis 2°), um ein zerstörungsfreies Entformen zu sichern.
* **Härte:** Hinweis (Best Practice für prozesssichere Fertigung).
* **Prüfstatus:** offen.

---

### Guss: Vermeidung von Materialanhäufungen und Knotenpunkten im Druckguss
* **Aussage / Wert:** Die Wanddicke muss sich vom Anguss zum Ende hin verjüngen; Knotenpunkte und Materialanhäufungen sind zwingend zu vermeiden. Übergänge müssen fließend ausgerundet werden.
* **Geltungsbereich:** Geometriegestaltung aller Druckgussteile.
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Druckguss aus NE-Metallen PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/druckguss_aus_ne-metallen.pdf)
  * *Wörtliches Zitat:* „Die Wanddicke sollte sich möglichst vom Anguss zum Gussstückende hin verjüngen, Knoten (Materialanhäufungen) sind zu vermeiden. Übergänge sollten fließend erfolgen und in den Ecken ausgerundet werden.“
* **Begründung:** An Materialanhäufungen erstarrt das Metall zuletzt, ohne dass flüssiges Material nachgespeist werden kann, was zu Vakuum- und Schrumpfungslunkern führt.
* **Härte:** Fehler (scharfkantige Querschnittssprünge und massive Knotenpunkte sind unzulässig).
* **Prüfstatus:** offen.

---

### Guss: Schwindmaße im Sandguss und Kokillenguss für Aluminium
* **Aussage / Wert:** Als Schwindmaße können für Aluminium-Sandguss 1,0 bis 1,25 Prozent und für Kokillenguss 0,8 bis 1,0 Prozent angesetzt werden.
* **Geltungsbereich:** Modell- und Formbau für Aluminiumguss nach Sand- und Kokillengießverfahren.
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Sand- und Kokillenguss aus Aluminium PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/sand-_und_kokillenguss_aus_aluminium.pdf)
  * *Wörtliches Zitat:* „Als Schwindmaße können für den Sandguss 1,0 bis 1,25 Prozent und für den Kokillenguss 0,8 bis 1,0 Prozent angesetzt werden.“
* **Begründung:** Die thermische Schrumpfung der flüssigen und festen Phase muss bei der Modellbemaßung über ein entsprechendes Aufmaß vorgehalten werden.
* **Härte:** Hinweis (Grundlage für die CAD-Modellskalierung im Gießereimodellbau).
* **Prüfstatus:** offen.

---

### Guss: Mindest-Formschrägen an Sandguss-Modellwerkzeugen
* **Aussage / Wert:** Beim Sandgießen müssen an den Modellwerkzeugen Formschrägen vorgesehen werden; Schrägen kleiner als 2° sind wenn möglich zu vermeiden.
* **Geltungsbereich:** Sandformverfahren für Aluminium- und Eisenguss.
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Sand- und Kokillenguss aus Aluminium PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/sand-_und_kokillenguss_aus_aluminium.pdf)
  * *Wörtliches Zitat:* „Beim Sandgießen muss ein einwandfreies Ausheben des Modells ohne Beschädigung der sehr empfindlichen Sandform möglich sein. Dazu sind an den Modellwerkzeugen Formschrägen vorzusehen. Formschrägen kleiner als 2° sind wenn möglich zu vermeiden.“
* **Begründung:** Die geringe Scherfestigkeit der verdichteten Sandform führt bei steilen Flanken beim Ziehen des Modells zu Kantenabbrüchen und Sandeinschlüssen im Gussstück.
* **Härte:** Fehler (bei Aushebeflächen im Sandguss unter 2°).
* **Prüfstatus:** offen.

---

### Guss: Vorgegossene Bohrungen im Sand- und Kokillenguss
* **Aussage / Wert:** Gemäß Tabelle 8 beträgt der minimale vorgegossene Bohrungsdurchmesser im Sandguss 10 bis 15 mm und im Kokillenguss 4 bis 5 mm. Die Formschräge der Kerne muss mindestens 2° betragen.
* **Geltungsbereich:** Eingegossene Bohrungen und Durchbrüche.
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Sand- und Kokillenguss aus Aluminium PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/sand-_und_kokillenguss_aus_aluminium.pdf), Tabelle 8, S. 42.
  * *Wörtliches Zitat:* „Tabelle 8: Vorgegossene Bohrungen“
* **Begründung:** Sehr dünne Sandkerne brennen thermisch fest oder brechen unter dem statischen Gießdruck ab. Kleinere Bohrungen müssen zerspanend gebohrt werden.
* **Härte:** Fehler (`check_design` muss bei Sandguss-Löchern unter 10 mm ein Ausgießen und Nachbohren vorschreiben).
* **Prüfstatus:** offen.

---

### Guss: Auflösung von Knotenpunkten und gerichtete Erstarrung
* **Aussage / Wert:** Materialanhäufungen sind möglichst zu vermeiden, Knotenpunkte aufzulösen und Wanddicken so zu gestalten, dass sie zum Speiser hin größer werden.
* **Geltungsbereich:** Gusskonstruktionen aller Gießverfahren.
* **Herkunft:** Verband / Technische Richtlinie (BDG).
* **Quelle:** [BDG-Richtlinie: Sand- und Kokillenguss aus Aluminium PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/sand-_und_kokillenguss_aus_aluminium.pdf)
  * *Wörtliches Zitat:* „Materialanhäufungen möglichst vermeiden, Knotenpunkte auflösen, Wanddicken sollten zum Speiser hin größer werden, Keine scharfen Wanddickenübergänge“
* **Begründung:** Eine kontinuierliche Zunahme der Querschnitte sichert das Prinzip der gerichteten Erstarrung vom kältesten Bauteilpunkt hin zum Speiser und verhindert Innenporosität.
* **Härte:** Fehler (ungespeiste Materialanhäufungen führen unweigerlich zu Ausschuss).
* **Prüfstatus:** offen.

---

### Schweißen: Grenzwerte und Faustformeln für das a-Maß von Kehlnähten
* **Aussage / Wert:** Als Bemessungsregel für Kehlnähte gilt: Das a-Maß soll höchstens 0,7 mal die Dicke des dünneren Blechs betragen, mindestens die Wurzel aus der Dicke des dickeren Blechs minus 0,5 mm und in jedem Fall mindestens 3 mm.
* **Geltungsbereich:** Schmelzgeschweißte Kehlnahtverbindungen im Stahlbau und Maschinenbau.
* **Herkunft:** Berechnungstool / Konstruktionspraxis (nurb44).
* **Quelle:** [nurb44 Schweiß-Rechner: A-Maß der Kehlnaht](https://nurb44.com/tools/kehlnaht-a-mass)
  * *Wörtliches Zitat:* „Faustregeln für das a-Maß höchstens 0,7 × die Dicke des dünneren Blechs mindestens √(Dicke des dickeren Blechs) − 0,5 mm und in jedem Fall mindestens 3 mm Diese Regeln geben einen sinnvollen Bereich vor, ersetzen aber keinen statischen Nachweis.“
* **Begründung:** Größere Nähte als 0,7 * t_min bringen keinen Tragfähigkeitsgewinn, weil das dünnere Grundblech vorher versagt. Zudem steigen Verzug und Zusatzwerkstoffkosten quadratisch mit dem a-Maß.
* **Härte:** Fehler (bei Unterschreitung von 3 mm Mindestnahtdicke im baulichen Stahlbau); Hinweis (zur Vermeidung von Überdimensionierung).
* **Prüfstatus:** offen.

---

### Schweißen: Geometrischer Zusammenhang zwischen a-Maß und Schenkellänge z
* **Aussage / Wert:** Bei gleichschenkligen Kehlnähten gilt für die Schenkellänge z = a mal Wurzel 2. Als Fertigungsbeispiel gilt eine Kehlnaht a4.
* **Geltungsbereich:** Zeichnungsangaben und Werkstattprüfung von Kehlnähten.
* **Herkunft:** Fachpraxis (nurb44).
* **Quelle:** [nurb44 Schweiß-Rechner: A-Maß der Kehlnaht](https://nurb44.com/tools/kehlnaht-a-mass)
  * *Wörtliches Zitat:* „Bei gleichen Schenkeln gilt z = a × √2. Auf der Zeichnung steht meist das a-Maß, zum Beispiel a4. In der Werkstatt ist das z-Maß leichter zu prüfen, etwa mit einer Schweißnahtlehre.“
* **Begründung:** Das a-Maß geht in den rechnerischen Festigkeitsnachweis ein, während in der Fertigung meist die Schenkellänge z mit Schweißnahtlehren an der Nahtflanke gemessen wird.
* **Härte:** Hinweis (Verwechslung von a und z führt zu signifikanter Nahtunterdimensionierung).
* **Prüfstatus:** offen.

---

### Schweißen: Definition der rechnerischen Nahtdicke nach Eurocode 3
* **Aussage / Wert:** Die rechnerische Nahtdicke a ist die Höhe des größten gleich- oder ungleichschenkligen Dreiecks nach EN 1993-1-8 Abschnitt 4.5.2(1), gemessen von der theoretischen Wurzel zur Nahtoberfläche.
* **Geltungsbereich:** Tragfähigkeitsnachweis geschweißter Stahlbauten nach Eurocode 3.
* **Herkunft:** Norm über Sekundärquelle (schweissnaht-nachweis.de).
* **Quelle:** [schweissnaht-nachweis.de: a-Maß Schweißnaht berechnen](https://schweissnaht-nachweis.de/a-mass-schweissnaht)
  * *Wörtliches Zitat:* „a-Maß (Nahtdicke) — die Höhe des größten gleich- oder ungleichschenkligen Dreiecks (EN 1993-1-8 Abschnitt 4.5.2(1)), das sich in den Nahtquerschnitt einbeschreiben lässt, gemessen von der theoretischen Wurzel zur Nahtoberfläche. Dieses Maß geht in den Nachweis ein.“
* **Begründung:** Zur Bestimmung der Schweißnahtspannungen wird normgemäß ausschließlich der wirksame Innenquerschnitt herangezogen; Überwölbungen bleiben unberücksichtigt.
* **Härte:** Fehler (Bemessungsgrundlage für statische Nachweise).
* **Prüfstatus:** offen.

---

### Schweißen: Schweißnahtlehren und Messbereiche nach DVS-Merkblatt 0703
* **Aussage / Wert:** DVS-Merkblatt 0703 Tabelle 2 definiert Schweißnahtlehren mit 3 oder 4 Skalen für einen Messbereich von 0 bis 15 mm mit einer Ablesegenauigkeit von 0,1 mm für flache, hohle und gewölbte Kehlnähte.
* **Geltungsbereich:** Fertigungsprüfung und Qualitätssicherung geschweißter Bauteile.
* **Herkunft:** Verband / DVS-Merkblatt über Sekundärquelle (schweissnaht-nachweis.de).
* **Quelle:** [schweissnaht-nachweis.de: a-Maß Schweißnaht berechnen](https://schweissnaht-nachweis.de/a-mass-schweissnaht)
  * *Wörtliches Zitat:* „DVS-Merkblatt 0703 (März 2025) stellt die Lehren in Tabelle 2 gegenüber, darunter diese: Schweißnahtlehre mit 3 oder 4 Skalen — Messbereich 0 bis 15 mm, Ablesegenauigkeit 0,1 mm; Kehlnaht flach, hohl, gewölbt“
* **Begründung:** Eine normgerechte Prüfung des geschweißten a-Maßes verlangt standardisierte Messwerkzeuge zur Vermeidung von Messunsicherheiten an Nahtüberhöhungen.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## Nicht erreichbare Quellen

Folgende Quellen wurden während der Recherche geprüft und erwiesen sich als nicht automatisiert abrufbar:

| Quelle / URL | Status | Grund / Bemerkung |
| :--- | :---: | :--- |
| `https://www.giessereilexikon.com/giesserei-lexikon/doc/show/giessgerechte-gestaltung/` | Timeout | Server blockiert automatisierte Abfragen oder reagiert mit Verbindungsabbruch. |
| `https://schweisshelden.de/fachwissen/a-mass-kehlnaht` | 403 | Bot-Sperre / Cloudflare-Schutz auf Fachportal. |
| `https://www.lincolnelectric.com/en/welding-resources/distortion` | 403 | Web-Sperre auf Hauptdomain; PDF-Delivery-Server (`ch-delivery.lincolnelectric.com`) separat erreichbar. |

---

## Offene Fragen

1. **Mindestwandstärken bei Niederdruck-Sandguss:** Wie weit lässt sich die minimale Wandstärke von Aluminiumbauteilen im Niederdrucksandguss unter 3 mm drücken, ohne dass Kaltläufe entstehen?
2. **Dynamische Kerbwirkungszahlen bei unausgefüllten Schweiß-Endkratern:** Welche Dauerfestigkeitsabminderung muss bei automatisierter Berechnung (`check_design`) angesetzt werden, wenn Schweißnähte ohne Auslaufstücke direkt an freien Bauteilkanten enden?

---

## Vorschläge für eigene Prüf- und Druckversuche

1. **Gussgerechte Wanddickenübergänge (FDM-Muster):**
   * Druck von Prüfkörpern mit abrupten Querschnittsübergängen (Verhältnis 4:1) vs. kontinuierlich verrundeten Übergängen (Winkel 1:3) zur Demonstration von Kerbspannungen und Abkühlungsverzug.
2. **Entformungskeile für Formschrägenversuch:**
   * Fertigung von Modellstufen mit Winkeln von 0.5°, 1.0°, 1.5° und 2.0° zum praktischen Testen des Aushebeverhaltens in Formkies/Formsand.
3. **Kehlnaht-Lehrenkörper:**
   * 3D-Druck einer Funktions-Schweißnahtlehre nach DVS 0703 für Kehlnähte a3 bis a10 zur haptischen Maßprüfung an geschweißten Homelab-Baugruppen.

---

Quellenprüfung (tools/check_sources.py, 2026-10-21): alle Zitate und Zahlen im abgerufenen Quelltext gefunden. Damit ist der Wert in der Quelle belegt, aber nicht zwingend richtig übernommen.
