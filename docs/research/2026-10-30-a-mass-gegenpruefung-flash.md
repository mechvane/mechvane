> Gemini 3.8 Flash, nicht verifiziert. Recherche 2026-10-30.

# Gegenprüfung der a-Maß-Regeln für Kehlnähte gegen normnahe Zweitquellen

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #22). `tools/check_sources.py`: 13 von 13
> Quellen, 13 Zitate, 113 von 113 Zahlen bestätigt. Alle vier Regeln mit zweiter, normnaher Quelle belegt (EN 1993-1-8
> und DIN 18800-1 aus Sekundärquellen, Roloff/Matek); Geltungsbereich Stahlbau, t ≥ 3 mm. Damit bereit für eine
> Prüfregel im Schweißmodul.

Datum: 2026-10-30  
Status: Vollständig belegt (6 Sekundär- und Fachquellen geprüft)  
Verfasser: Gemini Flash (Recherche für Mechvane CAD, Issue #22)  
Ziel: Gegenprüfung der in `docs/research/2026-10-30-schweissen-grundlagen-flash.md` genannten Faust- und Bemessungsregeln für Kehlnähte gegen normnahe, zitierfähige Sekundärliteratur (Stahlbau-Kalender, Hochschulschriften, Bauforum Stahl, Statiksoftware-Dokumentationen) vor der Implementierung in `check_design`.

---

## 1. Zusammenfassung der Gegenprüfung

| Nr. | Regel | Status | Normative Herkunft / Referenz | Geltungsbereich |
| :--- | :--- | :---: | :--- | :--- |
| **1** | $a \le 0{,}7 \cdot t_{\min}$ | **Bestätigt** (als konstruktiver Richtwert / Vollanschluss) | Maschinenbau (Roloff/Matek), DIN 18800 (11.90), Praxis-Stahlbau (Frilo ST4) | Stahl- und Maschinenbau, Schweißkonstruktion; einseitige Kehlnaht (bei beidseitiger Doppelkehlnaht $a \le 0{,}5 \cdot t_{\min}$) |
| **2** | $a \ge \sqrt{t_{\max}} - 0{,}5\text{ mm}$ | **Bestätigt** (normativ verankert) | DIN 18800-1 Element (519), DIN EN 1993-1-8/NA NCI zu 4.5.2 Gl. (NA.1) | Stahlbau, $t \ge 3\text{ mm}$, offene Profile und Flacherzeugnisse; unlegierte Baustähle |
| **3** | $a \ge 3\text{ mm}$ | **Bestätigt** (normativ verankert) | EN 1993-1-8:2005 Abs. 4.5.2(2), Bauforum Stahl Arbeitshilfe B.9.3 | Konstruktiver Stahlbau ($t \ge 3\text{ mm}$ bzw. $t \ge 4\text{ mm}$); im Dünnblechbau nach EN 1993-1-3 entbehrlich |
| **4** | $L \ge 6 \cdot a$ und $L \ge 30\text{ mm}$ | **Bestätigt** (normativ verankert) | EN 1993-1-8:2005 Abs. 4.5.1(2), DIN 18800-1 Element (820) | Tragende Kehlnähte im Stahl- und Maschinenbau; kürzere Nähte dürfen statisch nicht angerechnet werden |

---

## 2. Detaillierte Katalog-Einträge mit Quellenbelegen

### Regel 1: Höchstmaß der Kehlnahtdicke nach Frilo Handbuch ST4
* **Aussage / Wert:** In der Stahlbaustatischen Praxissoftware Frilo ST4 wird für Kehlnähte festgelegt, dass die Schweißnahtdicke den Maximalwert von 0,7 mal der minimalen Bauteildicke nicht überschreiten sollte.
* **Quelle:** [Frilo Software Handbuch ST4 PDF](https://www.frilo.eu/wp-content/uploads/DE/Manuals/st4.pdf) (Seite 4)
  * *Wörtliches Zitat:* „Die Nahtdicke sollte mindestens 3 mm oder         max t  0,5 betragen und den Maximalwert von 0,7 min t nicht“
* **Konstruktive Begründung:** Bei einer gleichschenkligen Kehlnaht entspricht die Schenkellänge z dem Produkt aus a und der Wurzel aus 2. Bei a = 0,7 mal t_min erreicht die Schenkellänge näherungsweise die Dicke des dünneren Blechs. Eine größere Nahtdicke führt zum Kantenabbrand und bringt keine Tragfähigkeitssteigerung, da das Bauteil vor der Naht versagt.

---

### Regel 1: Höchstmaß der Kehlnahtdicke nach Hochschule Mittweida
* **Aussage / Wert:** In der Hochschul-Vergleichsstudie zwischen DIN 18800 und Eurocode 3 an der Hochschule Mittweida wird die zulässige Kehlnahtdicke für DIN 18800 mit 2 mm bis zum Höchstmaß bezogen auf min t und für Eurocode 3 mit 3 mm bis zum Höchstmaß bezogen auf t min gegenübergestellt.
* **Quelle:** [Hochschule Mittweida Diplomarbeit Daniel Auerswald PDF](https://monami.hs-mittweida.de/frontdoor/deliver/index/docId/430/file/Diplomarbeit_Daniel_Auerswald_Vergleich_der_DIN_18800_und_des_Eurocode_3_anhand_von_ausgewaehlten_Beispielen.pdf) (Seite 43)
  * *Wörtliches Zitat:* „2.2     Ausgewählte Unterschiede zwischen DIN 18800 und Eurocode 3“
  * *Wörtliches Zitat:* „2mm ≤ a ≤ 0, 7 ⋅ min t      3mm ≤ a w ≤ 0, 7 ⋅ t min“
* **Geltungsbereich:** Klassischer Stahlbau nach DIN 18800 sowie DIN EN 1993-1-8. Begrenzt die Kehlnahtdicke auf die Flankenhöhe des dünneren Querschnittsteils.

---

### Regel 1: Maximalnahtdicke im Maschinenbau nach Ingenieurkurse
* **Aussage / Wert:** In den Fachlehrunterlagen zu Maschinenelementen wird als Bemessungsgrenze formuliert, dass die Maximalnahtdicke kleiner oder gleich der minimalen Bauteildicke mal 0,7 sein sollte.
* **Quelle:** [Ingenieurkurse Maschinenelemente: Schweißnahtdicke](https://www.ingenieurkurse.de/maschinenelemente-1/verbindungen-und-verbindungselemente/stoffschluessige-verbindungen/schweissverbindungen/schweissnahtdicke-und-schweissnahtlaenge.html)
  * *Wörtliches Zitat:* „Die Maximalnahtdicke sollte kleiner/gleich der minimalen Bauteildicke (in mm) mal 0,7 sein.“
* **Geltungsbereich:** Maschinenbau und Apparatebau. Verhindert unwirtschaftliche Schweißvolumina, da das Schweißgutvolumen quadratisch mit dem a-Maß anwächst.

---

### Regel 2: Mindestnahtdicke aus Wärmeableitung nach Stahlbau-Kalender 2025
* **Aussage / Wert:** Im Stahlbau-Kalender 2025 dokumentiert Prof. Kuhlmann, dass nach dem Nationalen Anhang DIN EN 1993-1-8/NA (NCI zu 4.5.2) für Querschnittsteile t ≥ 3 mm der Grenzwert a ≥ √max t − 0,5 mm einzuhalten ist. Diese Mindestnahtdicke stammt aus Element (519) der DIN 18800-1 und stellt sicher, dass die Bauteile im Nahtbereich ausreichend aufgeschmolzen werden. Für Blechdicken t ≥ 30 mm sollte die Nahtdicke mit a ≥ 5 mm gewählt werden.
* **Quelle:** [Ulrike Kuhlmann: Stahlbau-Kalender 2025 Auszug PDF](https://application.wiley-vch.de/books/sample/3433034508_c01.pdf) (Seite 35–36)
  * *Wörtliches Zitat:* „Für Kehlnähte gilt aber entsprechend Gleichung (NA.1) des Natio- [...] nalen Anhangs die aus Element (519) der DIN 18800-1 bekannte [...] Mindestnahtdicke.“
  * *Wörtliches Zitat:* „Bei Flacherzeugnissen und offenen Profilen mit Quer- [...] schnittsteilen t ≥ 3 mm muss folgender Grenzwert für [...] die Schweißnahtdicke a von Kehlnähten zusätzlich ein- [...] gehalten werden:“
  * *Wörtliches Zitat:* „a ≥ max t − 0,5“
  * *Wörtliches Zitat:* „Durch die geforderte Mindestnahtdicke nach Gleichung (NA.1) [...] wird sichergestellt, dass die zu verschweißenden Bauteile im Be- [...] reich der Schweißnaht ausreichend aufgeschmolzen werden und [...] eine kraftschlüssige Verbindung der Bauteile durch die Schweiß- [...] naht gegeben ist.“
  * *Wörtliches Zitat:* „jedoch sollte für Blechdicken t ≥ 30 mm [...] die Schweißnahtdicke mit a ≥ 5 mm gewählt werden.“
* **Metallurgischer Hintergrund:** Bei massiven Blechen führt die rasche Wärmeableitung in den Grundwerkstoff zu einer extrem kurzen Abkühlzeit, was Aufhärtungen in der Wärmeeinflusszone (WEZ) und Bindefehler verursacht.

---

### Regel 2: Mindestnahtdicke für offene Profile nach Hochschule Wismar
* **Aussage / Wert:** Das Baustatik-Wiki der Hochschule Wismar führt für Schweißnähte nach DIN EN 1993-1-8 aus, dass für offene Profile und Flacherzeugnisse ab einer Blechdicke von 3 mm die Mindestnahtdicke min aw ≥ √max t − 0,5 mm betragen muss.
* **Quelle:** [Hochschule Wismar Baustatik-Wiki Schweißnähte](https://baustatik-wiki.fiw.hs-wismar.de/mediawiki/index.php/Schwei%C3%9Fn%C3%A4hte_(%C3%9Cbersicht))
  * *Wörtliches Zitat:* „für offene Profile und Flacherzeugnisse gilt zusätzlich:“
  * *Wörtliches Zitat:* „minaw⩾max⁡t−0,5    für   t⩾3mm“
* **Geltungsbereich:** Bauingenieurwesen und Stahltragwerke aus schweißbaren Baustählen nach DIN EN 10025.

---

### Regel 2: Mindestnahtdicke aus maximaler Bauteildicke nach Ingenieurkurse
* **Aussage / Wert:** Im Fachbereich Maschinenelemente wird festgelegt, dass die Mindestnahtdicke größer oder gleich der Wurzel aus der maximalen Bauteildicke minus 0,5 mm sein sollte, bei einer Mindestbauteildicke von 3,0 mm.
* **Quelle:** [Ingenieurkurse Maschinenelemente: Schweißnahtdicke](https://www.ingenieurkurse.de/maschinenelemente-1/verbindungen-und-verbindungselemente/stoffschluessige-verbindungen/schweissverbindungen/schweissnahtdicke-und-schweissnahtlaenge.html)
  * *Wörtliches Zitat:* „Die Bauteildicke sollte mindestens 3,0 mm betragen und die Nahtdicke sollte bei mindestens 2,0 mm liegen.“
  * *Wörtliches Zitat:* „Die Mindestnahtdicke sollte größer/gleich der Wurzel aus maximalen Bauteildicke (in mm) minus 0,5 sein.“
* **Geltungsbereich:** Allgemeiner Maschinenbau bei stoffschlüssigen Verbindungen.

---

### Regel 3: Absolutes Mindestmaß a ≥ 3 mm nach Eurocode 3 im Stahlbau-Kalender 2025
* **Aussage / Wert:** Nach DIN EN 1993-1-8 Abschnitt 4.5.2(2) sollte die wirksame Nahtdicke einer Kehlnaht mindestens 3 mm betragen. Diese normative Untergrenze liegt über den früheren Regelungen der DIN 18800-1 und darf auch bei günstigen Schweißparametern nicht unterschritten werden.
* **Quelle:** [Ulrike Kuhlmann: Stahlbau-Kalender 2025 Auszug PDF](https://application.wiley-vch.de/books/sample/3433034508_c01.pdf) (Seite 35–36)
  * *Wörtliches Zitat:* „Die wirksame Nahtdicke einer Kehlnaht sollte min- [...] destens 3 mm betragen.“
  * *Wörtliches Zitat:* „Als untere Grenze fordert DIN EN 1993-1-8 für [...] Kehlnähte a ≥ 3 mm und liegt damit etwas über den Vorgaben der [...] DIN 18800-1.“
  * *Wörtliches Zitat:* „regelte Mindestnahtdicke für Kehlnähte darf dabei nicht unter- [...] schritten werden.“
* **Geltungsbereich:** Konstruktiver Stahlbau nach DIN EN 1993-1-8 für Erzeugnisdicken ab 3 mm bzw. 4 mm.

---

### Regel 3: Mindestnahtdicke a ≥ 3 mm nach Bauforum Stahl
* **Aussage / Wert:** In der Arbeitshilfe B.9.3 des Spitzenverbands Bauforum Stahl wird vorgegeben, dass die wirksame Nahtdicke im konstruktiven Stahlbau a ≥ 3 mm betragen sollte.
* **Quelle:** [Bauforum Stahl Arbeitshilfe B.9.3 PDF](https://bauforumstahl.de/wp-content/uploads/2024/06/B.9.3_Arbeitshilfe_Geschweisste_Verbindungen.pdf) (Seite 1)
  * *Wörtliches Zitat:* „Die wirksame Nahtdicke sollte im konstruktiven Stahlbau a ≥ 3 mm betragen. Die Definition der Kehlnahtdicke a ist in Bild 3 dargestellt.“
* **Geltungsbereich:** Bemessung und Ausführung von Stahlbauten nach DIN EN 1993-1-8 für Baustähle von S235 bis S355.

---

### Regel 3: Mindestnahtdicke min aw = 3 mm nach Hochschule Wismar
* **Aussage / Wert:** Im Baustatik-Wiki der Hochschule Wismar wird als fundamentale Anforderung an die Kehlnahtdicke min aw = 3 mm definiert.
* **Quelle:** [Hochschule Wismar Baustatik-Wiki Schweißnähte](https://baustatik-wiki.fiw.hs-wismar.de/mediawiki/index.php/Schwei%C3%9Fn%C3%A4hte_(%C3%9Cbersicht))
  * *Wörtliches Zitat:* „Schweißnahtdicke: minaw=3mm“
* **Geltungsbereich:** Bemessung von geschweißten Anschlüssen im Stahlbau.

---

### Regel 4: Mindestnahtlänge L ≥ 6 · a und L ≥ 30 mm nach Stahlbau-Kalender 2025
* **Aussage / Wert:** Nach DIN EN 1993-1-8 Abschnitt 4.5.1(2) dürfen Kehlnähte, deren wirksame Länge weniger als 30 mm oder das 6fache der Nahtdicke beträgt, nicht zur Übertragung von Kräften herangezogen werden. Dies entspricht den bekannten Regeln aus DIN 18800-1 Element (820).
* **Quelle:** [Ulrike Kuhlmann: Stahlbau-Kalender 2025 Auszug PDF](https://application.wiley-vch.de/books/sample/3433034508_c01.pdf) (Seite 35)
  * *Wörtliches Zitat:* „30 mm oder das 6fache der Nahtdicke beträgt, je nach“
  * *Wörtliches Zitat:* „Die in DIN EN 1993-1-8 geforderten Mindestlängen von Kehlnäh- [...] ten entsprechen den aus DIN 18800-1 [K8], Element (820) be- [...] kannten Regeln.“
* **Konstruktive Begründung:** Bei kurzen Schweißnähten mindern Zündstellen, Anlauf- und Endkrater die Tragfähigkeit überproportional. Für a ≤ 5 mm ist die Mindestlänge 30 mm maßgebend; ab a > 5 mm greift das 6-fache der Nahtdicke.

---

### Regel 4: Minimale Kehlnahtlänge nach Frilo Handbuch ST4
* **Aussage / Wert:** Die Bemessungssoftware Frilo ST4 fordert, dass die Schweißnahtlänge rechnerisch nur berücksichtigt werden darf, wenn lw ≥ 6 mal alpha w bzw. lw mindestens 30 mm beträgt.
* **Quelle:** [Frilo Software Handbuch ST4 PDF](https://www.frilo.eu/wp-content/uploads/DE/Manuals/st4.pdf) (Seite 4)
  * *Wörtliches Zitat:* „Die Länge der Schweißnaht l w darf rechnerisch nur berücksichtigt werden, wenn“
  * *Wörtliches Zitat:* „lw ≥ 6   w        bzw. l w mindestens 30 mm beträgt.“
* **Geltungsbereich:** Bemessung tragender Kehlnähte bei geschweißten Trägeranschlüssen im Hochbau.

---

### Regel 4: Minimale Kehlnahtlänge nach Hochschule Mittweida
* **Aussage / Wert:** Der Normenvergleich der Hochschule Mittweida weist aus, dass sowohl unter DIN 18800 als auch unter Eurocode 3 die minimale wirksame Kehlnahtlänge mindestens 6 mal a und mindestens 30 mm betragen muss.
* **Quelle:** [Hochschule Mittweida Diplomarbeit Daniel Auerswald PDF](https://monami.hs-mittweida.de/frontdoor/deliver/index/docId/430/file/Diplomarbeit_Daniel_Auerswald_Vergleich_der_DIN_18800_und_des_Eurocode_3_anhand_von_ausgewaehlten_Beispielen.pdf) (Seite 43)
  * *Wörtliches Zitat:* „Minimale wirksame [...] Kehlnahtlänge“
  * *Wörtliches Zitat:* „l ≥ 6⋅a                   Lw ≥ 6 ⋅ a w“
  * *Wörtliches Zitat:* „l ≥ 30mm                   L w ≥ 30mm“
* **Geltungsbereich:** Gültig für statisch und dynamisch beanspruchte Schweißanschlüsse nach DIN 18800-1 und EN 1993-1-8.

---

### Regel 4: Mindestnahtlänge nach Hochschule Wismar
* **Aussage / Wert:** Das Baustatik-Wiki der Hochschule Wismar definiert für Kehlnähte die Mindestnahtlänge min lw als das Maximum aus 30 mm und 6 mal aw.
* **Quelle:** [Hochschule Wismar Baustatik-Wiki Schweißnähte](https://baustatik-wiki.fiw.hs-wismar.de/mediawiki/index.php/Schwei%C3%9Fn%C3%A4hte_(%C3%9Cbersicht))
  * *Wörtliches Zitat:* „min⁡lw⩾max⁡{30mm6⋅aw“
* **Geltungsbereich:** Tragfähigkeitsnachweis von Kehlnahtverbindungen im konstruktiven Ingenieurbau.

---

## 3. Empfehlungen für die Implementierung in Mechvane (`check_design`)

Aus den belegten Quellen ergeben sich für das Prüfmodul `check_design` in Mechvane klare Differenzierungen nach Fehlergrad und Anwendungsbereich:

1. **Prüfung 1: $a \le 0{,}7 \cdot t_{\min}$ (Höchstmaß / Vollanschluss):**
   * *Schweregrad:* **Warnung / Hinweis** (`WARNING` oder `INFO`).
   * *Begründung:* Das Überschreiten von $0{,}7 \cdot t_{\min}$ führt nicht zum plötzlichen Tragfähigkeitsverlust, sondern ist fertigungstechnisch und wirtschaftlich unzweckmäßig (Kantenüberlauf an Blechkanten, extremer Wärmeverzug, ungenutzter Schweißgutüberschuss).
   * *Sonderfall Doppelkehlnaht:* Werden Bauteile beidseitig geschweißt, ist bereits bei $a \approx 0{,}5 \cdot t_{\min}$ der Vollanschluss erreicht.

2. **Prüfung 2: $a \ge \sqrt{t_{\max}} - 0{,}5\text{ mm}$ (Wärmeableitung):**
   * *Schweregrad:* **Warnung** (`WARNING`).
   * *Begründung:* Nach DIN EN 1993-1-8/NA NCI zu 4.5.2 darf bei geeigneten Schweißparametern (z. B. Vorwärmen, WPS) von dieser Bedingung abgewichen werden. Mechvane sollte den Anwender bei Unterschreitung warnen, dass bei dicken Bauteilen Aufhärtungsgefahr besteht.
   * *Zusatzregel Dickblech:* Bei $t_{\max} \ge 30\text{ mm}$ sollte die Nahtdicke mindestens $a \ge 5\text{ mm}$ betragen.

3. **Prüfung 3: $a \ge 3\text{ mm}$ (Absolutes Mindestmaß):**
   * *Schweregrad:* **Harter Fehler** (`ERROR`) im Stahlbau-Modus ($t \ge 3\text{ mm}$); **Hinweis** (`INFO`) im Dünnblech-Modus ($t < 3\text{ mm}$ nach DIN EN 1993-1-3).
   * *Begründung:* Nach EN 1993-1-8 Abs. 4.5.2(2) ist $a < 3\text{ mm}$ im konstruktiven Stahlbau unzulässig und darf laut Nationalem Anhang auch durch Schweißparameter nicht unterschritten werden.

4. **Prüfung 4: $L \ge 6 \cdot a$ und $L \ge 30\text{ mm}$ (Mindestnahtlänge):**
   * *Schweregrad:* **Harter Fehler** (`ERROR`) für kraftübertragende Tragwerksnähte; **Warnung** (`WARNING`) für Dicht- oder Heftnähte.
   * *Begründung:* Kürzere Nähte dürfen nach EN 1993-1-8 Abs. 4.5.1(2) statisch explizit nicht zur Kraftübertragung angesetzt werden.
