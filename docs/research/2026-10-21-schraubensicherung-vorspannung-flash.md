> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Schraubensicherung, Vorspannkräfte und Anziehdrehmomente

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert  
Sprache: Deutsch  

Dieser Bericht erfasst die technischen Regeln zur Schraubensicherung (Unterscheidung zwischen Losdrehen und Lockern/Setzen, wirksame und unwirksame Sicherungselemente) sowie fundierte Richtwerte für Montagevorspannkräfte und Anziehdrehmomente für metrische Regelgewinde von M3 bis M12 (Festigkeitsklassen 8.8, 10.9, 12.9 und Edelstahl A2-70) als Datengrundlage für das Projekt inventa.

---

## 1. Schraubensicherung: Wirkmechanismen, wirksame und unwirksame Elemente

### Eintrag: Unwirksame Sicherungselemente laut aktueller Normung
* **Aussage / Wert:** Federringe (DIN 127, DIN 128, DIN 6905, DIN 7980), Federscheiben (DIN 137, DIN 6904), Zahnscheiben (DIN 6797, DIN 6906) und Fächerscheiben (DIN 6798, DIN 6907) besitzen keinerlei Sicherungswirkung gegen Losdrehen oder Lockern. Von der Verwendung mit Schrauben der Festigkeitsklasse 8.8 oder höher muss abgeraten werden.
* **Geltungsbereich:** Schraubverbindungen mit Schrauben der Festigkeitsklassen 8.8, 10.9, 12.9 im allgemeinen Maschinenbau.
* **Herkunft:** Norm über Sekundärquelle / Hersteller (Würth Industrie DiNo-Technik).
* **Quelle:** [Würth DiNo-Technik](https://www.wuerth-industrie.com/web/media/downloads/brochures/de_wis/dino-technik.pdf), Kapitel 7.4.1.
* **Seite bzw. Tabelle:** Kapitel 7.4.1 (Unwirksame Sicherungselemente).
* **Wörtliches Zitat:** „Die nachfolgend aufgeführten Produkte besitzen keinerlei [...] Sicherungswirkung, weder in Bezug auf das Lockern [...] noch in Bezug auf das Losdrehen [...] Von einer Verwendung [...] mit Schrauben der Festigkeitsklasse ≥ 8.8 muss abgeraten [...] werden [...] Federringe DIN 127, DIN 128, DIN 6905, DIN 7980 [...] Federscheiben DIN 137, DIN 6904 [...] Zahnscheiben DIN 6797, DIN 6906 [...] Fächerscheiben DIN 6798, DIN 6907“
* **Begründung:** Diese federnden Elemente sind bereits bei geringen Vorspannkräften vollständig flachgedrückt. Unter dynamischer Querbelastung federn sie nicht nach und können den Setzbetrag hochfester Schrauben nicht ausgleichen. Die entsprechenden DIN-Normen wurden vom Deutschen Institut für Normung (DIN) offiziell zurückgezogen.
* **Härte:** Fehler (`check_design` muss die Verwendung von DIN 127 / DIN 128 ablehnen).
* **Prüfstatus:** offen.

---

### Eintrag: Wirksame Losdrehsicherungen im Maschinenbau
* **Aussage / Wert:** Als wirksame Losdrehsicherungen unter dynamischer Querbeanspruchung gelten mechanische Verriegelungen an der Auflagefläche sowie stoffschlüssige Verklebungen im Gewinde.
* **Geltungsbereich:** Dynamisch beanspruchte Schraubverbindungen.
* **Herkunft:** Herstellerhandbuch (Würth Industrie DiNo-Technik).
* **Quelle:** [Würth DiNo-Technik](https://www.wuerth-industrie.com/web/media/downloads/brochures/de_wis/dino-technik.pdf), Kapitel 7.4.3.
* **Seite bzw. Tabelle:** Kapitel 7.4.3 (Losdrehsicherungen).
* **Wörtliches Zitat:** „Losdrehsicherungen verhindern unter dynamischen Belas- [...] tung, wirkungsvoll das selbsttätige Losdrehen. Bis auf ge- [...] ringe unvermeidliche Setzbeträge bleibt die Vorspannkraft [...] in der Verbindung erhalten [...] Verriegelung an der Auflage [...] Verklebung im Gewinde“
* **Begründung:** Im Unterschied zu bloßen Verliersicherungen (z. B. Muttern mit Polyamidring), die nach Vorspannkraftverlust lediglich das Abfallen verhindern, halten Verriegelungselemente (z. B. Keilsicherungsscheiben oder Sperrverzahnungen) und anaerobe Klebstoffe die Vorspannkraft aufrecht.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Verbot von Federringen und Zahnfederscheiben in der Raumfahrt
* **Aussage / Wert:** Frei mitdrehende Federringe und Zahnscheiben bieten minimalen bis keinen Schutz gegen Losdrehen.
* **Geltungsbereich:** Raumfahrtstrukturen und dynamisch belastete Baugruppen nach NASA-Standard.
* **Herkunft:** Raumfahrthandbuch (NASA-STD-5020B).
* **Quelle:** [NASA-STD-5020B](https://standards.nasa.gov/system/files/tmp/NASA-STD-5020B%20Revalidated%201-5-2026.pdf), Appendix B.2.
* **Seite bzw. Tabelle:** Seite 84, Appendix B.2, Paragraph d.
* **Wörtliches Zitat:** „Free spinning split lock and tooth lock washers provide minimal, if any, locking.“
* **Begründung:** Die Federsteifigkeit herkömmlicher Federringe ist im Verhältnis zur Schraubensteifigkeit vernachlässigbar gering. Nach dem Anziehen wirken sie wie einfache Unterlegscheiben ohne Sperreffekt.
* **Härte:** Fehler.
* **Prüfstatus:** offen.

---

### Eintrag: Anforderung an vorspannungsunabhängige Schraubensicherungen
* **Aussage / Wert:** Jede Schraubverbindung in Raumfahrthardware muss mindestens ein Sicherungselement aufweisen, dessen Funktion nicht von der Vorspannkraft abhängt.
* **Geltungsbereich:** Gewindeverbindungen in Raumfahrtsystemen.
* **Herkunft:** Handbuch / Raumfahrtstandard (NASA-STD-5020B).
* **Quelle:** [NASA-STD-5020B](https://standards.nasa.gov/system/files/tmp/NASA-STD-5020B%20Revalidated%201-5-2026.pdf), Abschnitt 4.6.1.
* **Seite bzw. Tabelle:** Seite 37, Paragraph 4.6.1 [TFSR 16].
* **Wörtliches Zitat:** „Regardless of the magnitude of preload, each threaded fastening system in spaceflight hardware shall incorporate a minimum of one locking feature that does not depend upon preload to function.“
* **Begründung:** Vibrationen und Schockbelastungen beim Start können zum Lockern oder Setzen führen; eine primär durch Reibung wirkende Verbindung verliert bei Setzbeträgen ihre Sicherung, wenn kein formschlüssiges oder stoffschlüssiges Sekundärsicherungselement vorhanden ist.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## 2. Montagevorspannkräfte und Anziehdrehmomente für Regelgewinde M3 bis M12 (8.8, 10.9, 12.9)

### Eintrag: Richtwerte nach VDI 2230 für Regelgewinde M3 bei Reibungszahl 0,14
* **Aussage / Wert:** Für Gewindegröße M3 beträgt bei Reibungszahl 0,14 die maximale Montagevorspannkraft 2436 N (Klasse 8.8), 3426 N (Klasse 10.9) und 4111 N (Klasse 12.9). Die zugehörigen maximalen Anziehdrehmomente betragen 141 Ncm (für 8.8), 198 Ncm (für 10.9) und 237 Ncm (für 12.9).
* **Geltungsbereich:** Schrauben M3 mit metrischem Regelgewinde nach ISO 262, Kopfformen nach ISO 4762 oder ISO 4014 bis 4018, Festigkeitsklassen 8.8, 10.9, 12.9, Reibungszahl 0,14.
* **Herkunft:** Hersteller / Technische Richtlinie (Bossard AG).
* **Quelle:** [Bossard Vorspannkräfte und Anziehdrehmomente PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3S40LEUM235Qk3rJk2phR1/dbffd8df726c87755678f2c2c11a443c/060_074_Vorspannkr_fte_Anziehdrehmomente_Fastening_DE_01_2025.pdf), Tabelle Seite 61.
* **Seite bzw. Tabelle:** Tabelle Seite 61, metrisches Regelgewinde VDI 2230.
* **Wörtliches Zitat:** „Angaben in Anlehnung an VDI 2230, Ausgabe 2015: Maximale zu­ [...] lässige Anziehdrehmomente und resultierende maximale Vorspann- [...] kräfte für Sechskantschrauben ISO 4014 – 4018, Innensechskant- [...] schrauben ISO 4762 und für Schrauben mit analogen Kopffestigkeiten [...] bei einer [...] 90 %-igen Ausnutzung der Streckgrenze“
* **Weiteres Zitat:** „0,14      685      914      1142     1827       2436   3426   4111     40       53       66       105        141    198    237      0,058“
* **Begründung:** M3-Schrauben reagieren aufgrund ihres geringen Kernquerschnitts extrem empfindlich auf Überlastung bei der Montage. Die Berechnung bei 90 % Ausnutzung der Dehngrenze nach VDI 2230 stellt die Obergrenze dar.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Richtwerte nach VDI 2230 für Regelgewinde M4 bis M12 bei Reibungszahl 0,14
* **Aussage / Wert:** Für Schaftschrauben mit Regelgewinde bei Reibungszahl 0,14 betragen die Vorspannkräfte und Anziehdrehmomente für 8.8, 10.9 und 12.9:
  * M4: FV = 4,30 kN / 6,30 kN / 7,40 kN; MA = 3,3 Nm / 4,8 Nm / 5,6 Nm.
  * M6: FV = 9,90 kN / 14,5 kN / 17,0 kN; MA = 11,3 Nm / 16,5 Nm / 19,3 Nm.
  * M8: FV = 18,1 kN / 26,6 kN / 31,1 kN; MA = 27,3 Nm / 40,1 Nm / 46,9 Nm.
  * M10: FV = 28,8 kN / 42,2 kN / 49,4 kN; MA = 54,0 Nm / 79,0 Nm / 93,0 Nm.
  * M12: FV = 41,9 kN / 61,5 kN / 72,0 kN; MA = 93,0 Nm / 137,0 Nm / 160,0 Nm.
* **Geltungsbereich:** Schaftschrauben mit metrischem Regelgewinde nach DIN ISO 262, Festigkeitsklassen 8.8, 10.9, 12.9, Reibungszahl 0,14.
* **Herkunft:** Norm über Sekundärquelle (Reyher Technische Informationen 2019 nach VDI 2230-1).
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf), Tabelle 5.
* **Seite bzw. Tabelle:** Seite TI-221, Tabelle 5 (Richtwerte für Schaftschrauben mit Regelgewinde, Reibungszahl µges = 0,14).
* **Wörtliches Zitat:** „Tabelle 5: Richtwerte für Schaftschrauben mit Regelgewinde, Reibungszahl µges = 0,14“
* **Tabellenzitate:**
  * „M   4       0,7            8,78          1,6      2,0         4,30        6,30      7,40     1,2         1,5          3,3         4,8     5,6“
  * „M   6       1,0           20,1           3,7      4,6         9,90       14,5      17,0      4,1         5,2         11,3        16,5    19,3“
  * „M   8       1,25          36,6           6,7      8,4        18,1        26,6      31,1     10,1        12,6         27,3        40,1    46,9“
  * „M 10        1,5           58,0          10,7     13,4        28,8        42,2      49,4     19,9        24,9         54,0        79,0    93,0“
  * „M 12        1,75          84,3          15,6     19,5        41,9        61,5      72,0     34,4        43,0         93,0       137,0   160,0“
* **Begründung:** Die Werte nach VDI 2230 gewährleisten eine 90%ige Ausnutzung der Schraubenstreckgrenze bzw. 0,2%-Dehngrenze und verhindern plastische Verformungen beim ordnungsgemäßen Anziehen.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

## 3. Verbindungselemente aus nichtrostenden Stählen (A2-70)

### Eintrag: Richtwerte für Schrauben aus nichtrostenden Stählen A2-70
* **Aussage / Wert:** Bei Edelstahlschrauben der Festigkeitsklasse A2-70 beträgt für Regelgewinde bei Reibungszahl 0,14:
  * M4: Montagevorspannkraft 2,97 kN, Anziehdrehmoment 2,2 Nm.
  * M6: Montagevorspannkraft 6,87 kN, Anziehdrehmoment 7,7 Nm.
  * M8: Montagevorspannkraft 12,61 kN, Anziehdrehmoment 18,8 Nm.
  * M10: Montagevorspannkraft 18,40 kN, Anziehdrehmoment 37,3 Nm.
* **Geltungsbereich:** Schrauben und Muttern nach DIN EN ISO 3506-1 aus austenitischem nichtrostendem Stahl A2-70.
* **Herkunft:** Norm über Sekundärquelle (Reyher Technische Informationen 2019).
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf), Tabelle 23.
* **Seite bzw. Tabelle:** Seite TI-251, Tabelle 23.
* **Wörtliches Zitat:** „Bei Verbindungselementen aus nicht rostenden Stählen sind die Reibungswerte im Gewinde und an den Auflageflächen wesentlich größer als bei vergüteten Stahlschrauben – auch der Streubereich der Reibungswerte ist hier viel größer (bis über 100 %!).“
* **Weiteres Zitat:** „Tabelle 23: unverbindliche Richtwerte für Schrauben A 2/A 4“
* **Tabellenzitate:**
  * „M4      70       3,14     2,71      2,97     2,89     2,80        2,71     2,30   1,95          1,8    2,0    2,2    2,4    2,6    2,8    3,4    3,8“
  * „M6      70       7,26     7,07      6,87     6,67     6,47        6,27     5,32   4,53          6,2    7,0    7,7    8,4    9,1    9,7   11,9   13,2“
  * „M8      70      13,30    12,96     12,61    12,25    11,88       11,51     9,79   8,34         15,0   17,0   18,8   20,6   22,2   23,6   29,1   32,5“
  * „M 10     70      21,16    20,63     18,40    19,50    18,92       18,34    15,60 13,29          29,5   33,5   37,3   40,7   41,9   46,8   57,8   67,7“
* **Begründung:** Edelstahl neigt bei der Montage stark zum Kaltverschweißen (Fressen). Daher ist der Streubereich der Reibungszahlen groß und Schmiermitteleinsatz ratsam.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

---

### Eintrag: Planmäßige Vorspannung bei nichtrostenden Stählen
* **Aussage / Wert:** Schrauben aus nichtrostendem Stahl dürfen nicht in planmäßig vorgespannten Anwendungen eingesetzt werden, sofern nichts anderes festgelegt wird.
* **Geltungsbereich:** Austenitische Verbindungselemente (A2, A4) nach ISO-Normen.
* **Herkunft:** Hersteller / Baupraxis (Bossard AG Whitepaper).
* **Quelle:** [Bossard Vorspannkräfte und Anziehdrehmomente PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3S40LEUM235Qk3rJk2phR1/dbffd8df726c87755678f2c2c11a443c/060_074_Vorspannkr_fte_Anziehdrehmomente_Fastening_DE_01_2025.pdf).
* **Seite bzw. Tabelle:** Seite 68, Kapitel Vorspannung von Schrauben aus nichtrostendem Stahl.
* **Wörtliches Zitat:** „Schrauben aus nichtrostendem Stahl dürfen nicht in planmässig vorgespannten Anwendungen eingesetzt werden, sofern nichts anderes festgelegt wird.“
* **Begründung:** Austenitische Edelstähle besitzen keine ausgeprägte Streckgrenze, sondern eine 0,2%-Dehngrenze mit ausgeprägter Neigung zu Kriech- und Relaxationsvorgängen unter Dauerlast.
* **Härte:** Fehler (bei tragenden, dynamisch planmäßig vorgespannten Verbindungen).
* **Prüfstatus:** offen.

---

## 4. Nicht erreichbare Quellen, offene Fragen und Versuchsvorschläge

### Nicht erreichbare Quellen
| URL | Code / Grund | Bemerkung |
| :--- | :---: | :--- |
| `https://ecss.nl/wp-content/uploads/2023/02/ECSS-E-HB-32-23A-Rev.1(6February2023).pdf` | 404 / 000 | ECSS-Handbuch Threaded Fasteners direkt nicht abrufbar (am 2026-10-20 vermerkt). |
| `https://www.boellhoff.com/de-de/produkte/schraubensicherung/` | 403 Bot-Sperre | Böllhoff-Webportal blockiert automatisierte Abrufe per Cloudflare WAF. |

### Offene Fragen
1. **Setzbeträge in 3D-gedruckten Kunststoffen (FDM):** Wie stark sinkt die Vorspannkraft einer M3- oder M4-Schraubverbindung in PLA bzw. PETG durch viskoelastisches Fließen des Thermoplasts innerhalb von 24 Stunden bei Raumtemperatur?
2. **Reibwertschwankungen bei A2-70 ohne Schmierstoff:** Welche Reibungszahl $\mu_{ges}$ stellt sich tatsächlich ein, wenn Edelstahlschrauben direkt in FDM-gedruckte Gewinde oder Messingeinsätze eingedreht werden?

### Vorschläge für eigene Versuche
1. **Druckversuch Prüfkörper Vorspannungsverlust (Ultimaker 2+):** FDM-Prüfkörper mit Schraubendurchgangsloch und Messing-Gewindeeinsatz (Ruthex M3 / M4) drucken. Schraube mit definiertem Drehmoment anziehen und Restdrehmoment zum Weiterdrehen nach 1 h, 24 h und 168 h messen.
2. **Vibrations-Losdrehversuch auf dem 3D-Drucker-Bett:** Prüfkörper mit federringgesicherter vs. keilsicherungs- / klebegesicherter Schraube auf der Z-Achse oder dem Druckbett montieren und bei 50–100 Hz Vibration das Losdrehverhalten beobachten.

---

Quellenprüfung (tools/check_sources.py, 2026-10-21): alle Zitate und Zahlen im abgerufenen Quelltext gefunden. Damit ist der Wert in der Quelle belegt, aber nicht zwingend richtig übernommen (Geltungsbereich, Reibwert und Spalte von Hand prüfen).
