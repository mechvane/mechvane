# Normwerte online geprüft (2026-10-20)

Rohfassung: Gemini 3.8 Flash mit Websuche (unten). **Prüfnotiz (Claude):**
Die drei Hauptquellen habe ich selbst geladen und den Text aus dem PDF
gelesen:

| Wert | Quelle, selbst gelesen | Ergebnis |
|---|---|---|
| DIN 974-1, Senktiefe ohne Scheibe M4–M12 | Bühler-Werksnorm, nennt „Senkungen DIN 974-1“ | 4,4 / 5,4 / 6,4 / 8,6 / 10,6 / 12,6 mm, Senk-Ø 8 / 10 / 11 / 15 / 18 / 20 mm. Stimmt mit `hole_tables.py` überein |
| Ruthex RX-M2,5 bis M5 | Datenblatt ruthex GmbH | d1, L, Bohrung wie in `standard_parts.py` (M3 4,6 × 5,7, Ø 4,0; M4 6,3 × 8,1, Ø 5,6; M5 7,1 × 9,5, Ø 6,4) |
| Einschraubtiefe 8.8, Regelgewinde | Bossard, Technische Information 01/2025 | S235 1,0·d, GJL 250 1,0·d (bei uns war 1,25), AlMgSi1 1,4·d, AlMg3 2·d. Eine Zeile „S355“ aus der Rohfassung steht **nicht** im PDF |

Geändert: Grauguss 1,0·d statt 1,25·d, Senk-Ø M2,5 5,5 mm statt 6,0 mm
(nur eine Quelle), Quellen mit URL in den Code-Kommentaren. Weiter
ungeprüft: Senkungen mit Scheibe (hergeleitet), Aluminium-Guss, Messing,
Kunststoff.

## Rohfassung (Gemini)

# Recherchebericht: Normwerte und Konstruktionsmaße

Dieser Bericht enthält belastbare technische Norm- und Herstellerwerte zu Schraubensenkungen, Mindesteinschraubtiefen, Gewindeeinsätzen und Durchgangslöchern. Für jeden Wert sind die genaue Quellen-URL und das wörtliche Zitat bzw. der Tabellenauszug angegeben.

---

## 1. DIN 974-1: Senkungen für Zylinderschrauben ISO 4762 (Schrauben ohne Unterlegteil)

### Hintergrund zur Norm und Formelberechnung
Die Norm **DIN 974-1** (*„Senkdurchmesser – Konstruktionsmaße – Teil 1: Schrauben mit Zylinderkopf“*) legt in Tabelle 1 Senkdurchmesser $d_1$ in verschiedenen Reihen fest:
* **Reihe 1 (Standard):** Für Schrauben ohne Unterlegteil (Toleranzfeld H13).
* **Reihe 2:** Ebenfalls für Schrauben ohne Unterlegteil mit alternativen Durchmessern.
* **Reihe 4 und 5:** Für Schrauben mit Unterlegteilen (z. B. Scheiben nach ISO 7092 / DIN 433).

**Senktiefe $t$ in der Norm:**  
DIN 974-1 legt in Tabelle 1 **keine festen Senktiefen $t$** vor, da die Tiefe vom Anwendungsfall abhängt (Kopfform, bündiger Abschluss, Verwendung von Scheiben). Für einen **bündigen Abschluss** definiert die Norm in Tabelle 2 die Berechnungsformel:
$$t = k_{\max} + h_{\text{Scheibe, max}} + \text{Zugabe}$$
Für Schrauben ohne Unterlegteil ($h_{\text{Scheibe}} = 0$) gilt:
$$t = k_{\max} + \text{Zugabe}$$
wobei $k_{\max}$ die maximale Kopfhöhe der Schraube nach Produktnorm ist (bei Standard-Zylinderschrauben nach ISO 4762 gilt $k_{\max} = d$, also Kopfhöhe gleich Gewindenenndurchmesser).

**Zuschlag / Zugabe nach DIN 974-1 (Tabelle 2):**
* $d \le 1,4\text{ mm}$: Zugabe = **0,2 mm**
* $1,4\text{ mm} < d \le 6\text{ mm}$: Zugabe = **0,4 mm**
* $6\text{ mm} < d \le 20\text{ mm}$: Zugabe = **0,6 mm**
* $20\text{ mm} < d \le 27\text{ mm}$: Zugabe = **0,8 mm**
* $27\text{ mm} < d \le 100\text{ mm}$: Zugabe = **1,0 mm**

### Belege und Tabellenauszüge

| Wert / Parameter | Quelle (URL) | Zitat / Tabellenauszug |
| :--- | :--- | :--- |
| **M2,5:** $d_1 = 5,5\text{ mm}$, $t = 2,9\text{ mm}$ ($k=2,5 + 0,4$) | [Ifanger AG Präzisionswerkzeuge / Defruytier Normtabelle Flachsenkungen nach DIN 974-1](https://www.defruytier.be/uploads/product/files/ifanger-VFL.pdf) | *„Flachsenkungen nach DIN 974-1: Gewinde M2,5 \| Senk-Ø S mm: 5,5 \| Durchgangsloch Ø B mm fein: 2,7 \| mittel: 2,9“* |
| **M3:** $d_1 = 6,5\text{ mm}$, $t = 3,4\text{ mm}$ ($k=3,0 + 0,4$) | [Neue Physik – Senkungen Tabellen (DIN 974-1)](https://www.neue-physik.de/353.9_Senkungen.php) | *„Gewindegröße d: M3 \| Durchgangsloch dh mittel: 3,4 \| Zylindersenkung d1: 6,5 \| Tiefe der Senkung t: 3,4“* |
| **M4:** $d_1 = 8,0\text{ mm}$, $t = 4,4\text{ mm}$ ($k=4,0 + 0,4$) | [Bühler AG Werksnorm LHH-N 300.009 (Senkungen DIN 974-1 für ISO 4762)](https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628) | *„Für Gewinde d: M4 \| dk max. 7,0 \| k max. 4,0 \| dh mittel H13: 4,5 \| d2 ohne Scheibe H13: 8 \| t1 ohne Scheibe: 4,4“* |
| **M5:** $d_1 = 10,0\text{ mm}$, $t = 5,4\text{ mm}$ ($k=5,0 + 0,4$) | [Bühler AG Werksnorm LHH-N 300.009](https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628) | *„Für Gewinde d: M5 \| dk max. 8,5 \| k max. 5,0 \| dh mittel H13: 5,5 \| d2 ohne Scheibe H13: 10 \| t1 ohne Scheibe: 5,4“* |
| **M5 Abweichender Wert:** $t = 5,7\text{ mm}$ | [CAD.de Forum – Forenbeitrag zu Tiefenmaßen DIN 974-1 / Hoischen](https://ww3.cad.de/foren/ubb/Forum200/HTML/000551.shtml) | *„ich möchte eine M5 zylinderschraube iso 4762 versenken, aber leider finde ich unterschiedliche angaben zum thema tiefe. tabellenbuch sagt 5,4 und hoischen steht 5,7 (beides ohne scheibe) [...] update: ich konnte heute auf das normblatt din 974-1 zugreifen [...] empfohlen wird schraubenkopfdicke max. + zugabe [...] und die ist bei M5 0,4mm“* |
| **M6:** $d_1 = 11,0\text{ mm}$, $t = 6,4\text{ mm}$ ($k=6,0 + 0,4$) | [Bühler AG Werksnorm LHH-N 300.009](https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628) | *„Für Gewinde d: M6 \| dk max. 10,0 \| k max. 6,0 \| dh mittel H13: 6,6 \| d2 ohne Scheibe H13: 11 \| t1 ohne Scheibe: 6,4“* |
| **M8:** $d_1 = 15,0\text{ mm}$, $t = 8,6\text{ mm}$ ($k=8,0 + 0,6$) | [Bühler AG Werksnorm LHH-N 300.009](https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628) | *„Für Gewinde d: M8 \| dk max. 13,0 \| k max. 8,0 \| dh mittel H13: 9 \| d2 ohne Scheibe H13: 15 \| t1 ohne Scheibe: 8,6“* |
| **M8 Abweichender Wert:** $t_1 = 9,0\text{ mm}$ (aus alter DIN 74-2 Form K) | [DIN 74-2 / antpedia Normauszug](https://www.antpedia.com) / [CAD.de](https://ww3.cad.de/foren/ubb/Forum200/HTML/000551.shtml) | *„DIN 74-2 Form K (Zylinderschrauben DIN 912): M8 Durchgangsloch d1 mittel 9,0 mm, Senkdurchmesser d2 15,0 mm, Senktiefe t1 = 9,0 mm“* (Hinweis: 9,0 mm ist bei M8 zugleich der Durchgangsloch-Ø nach ISO 273 mittel). |
| **M10:** $d_1 = 18,0\text{ mm}$, $t = 10,6\text{ mm}$ ($k=10,0 + 0,6$) | [Bühler AG Werksnorm LHH-N 300.009](https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628) | *„Für Gewinde d: M10 \| dk max. 16,0 \| k max. 10,0 \| dh mittel H13: 11 \| d2 ohne Scheibe H13: 18 \| t1 ohne Scheibe: 10,6“* |
| **M12:** $d_1 = 20,0\text{ mm}$, $t = 12,6\text{ mm}$ ($k=12,0 + 0,6$) | [Bühler AG Werksnorm LHH-N 300.009](https://dam.buhlergroup.com/asset/b8a11dd24a59463f9d1dc4051b63b628) | *„Für Gewinde d: M12 \| dk max. 18,0 \| k max. 12,0 \| dh mittel H13: 13,5 \| d2 ohne Scheibe H13: 20 \| t1 ohne Scheibe: 12,6“* |
| **Formel & Zuschlag:** $t = k_{\max} + h_{\text{max}} + \text{Zugabe}$ | [DIN 974-1 Normblatt / Scribd Normdokument](https://www.scribd.com) | *„DIN 974-1 Tabelle 2 – Empfohlene Zugabe für bündigen Abschluss: d ≤ 1,4 mm: 0,2 mm; 1,4 < d ≤ 6 mm: 0,4 mm; 6 < d ≤ 20 mm: 0,6 mm; 20 < d ≤ 27 mm: 0,8 mm; 27 < d ≤ 100 mm: 1,0 mm“* |

Ergebnis: Die Senkdurchmesser $d_1$ (Reihe 1, Toleranz H13) lauten: **M2,5: 5,5 mm | M3: 6,5 mm | M4: 8,0 mm | M5: 10,0 mm | M6: 11,0 mm | M8: 15,0 mm | M10: 18,0 mm | M12: 20,0 mm**. Die Norm DIN 974-1 enthält eine explizite Berechnungsformel $t = k_{\max} + \text{Zugabe}$ mit Zuschlägen von **0,4 mm** für M2,5 bis M6 und **0,6 mm** für M8 bis M12. Daraus ergeben sich die Tiefen $t$: **M2,5: 2,9 mm | M3: 3,4 mm | M4: 4,4 mm | M5: 5,4 mm | M6: 6,4 mm | M8: 8,6 mm | M10: 10,6 mm | M12: 12,6 mm**. Zur Klärung: Für M5 ist **5,4 mm** normativ korrekt (5,7 mm ist ein veralteter/nicht-normativer Lehrbuchwert mit 0,7 mm Übermaß); für M8 ist **8,6 mm** nach DIN 974-1 korrekt (9,0 mm stammt aus der alten DIN 74-2 Form K bzw. entspricht dem Lochdurchmesser). **Sicherheit: Hoch / Verifiziert durch Normblatt, Werksnormen und Werkzeugkataloge.**

---

## 2. Mindesteinschraubtiefen für Regelgewinde nach Werkstoff

### Grundprinzip nach VDI 2230
Die Mindesteinschraubtiefe ($m_{\text{eff}}$ bzw. $L_e$) ist nach **VDI 2230 Blatt 1** die *rein effektive tragende Gewindelänge* (ohne Bauteilansenkung und ohne Gewindeauslauf der Schraube). Das Auslegungsziel lautet: Bei Überlastung muss die Schraube im Schaft bzw. freien Gewinde reißen (Bolzenbruch), bevor die Gewindegänge des Innengewindes abscheren (Abstreifen).

### Belege und Tabellenauszüge

| Wert / Parameter | Quelle (URL) | Zitat / Tabellenauszug |
| :--- | :--- | :--- |
| **Stahl $R_m > 360\text{ N/mm}^2$ (S235 / St37)** | [Bossard Technische Information 01/2025: Einschraubtiefe (PDF)](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff S235 (St37-2), Rm > 360 N/mm²: Empfohlene Mindest-Einschraubtiefe für Schraubenfestigkeitsklasse 8.8 Regelgewinde: 1,0 · d [1,5 · d nach VDI 2230]; 10.9 Regelgewinde: 1,25 · d [1,8 · d]; 12.9 Regelgewinde: 1,4 · d [2,1 · d]“* |
| **Stahl $R_m > 500\text{ N/mm}^2$ (S355 / St52)** | [Bossard Technische Information 01/2025](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff S355 (St52-3), Rm > 500 N/mm²: Schraubenfestigkeitsklasse 8.8 Regelgewinde: 0,9 · d [1,3 · d nach VDI 2230]; 10.9: 1,0 · d [1,6 · d]; 12.9: 1,2 · d [1,8 · d]“* |
| **Stahl $R_m > 800\text{ N/mm}^2$ (Vergütungsstahl C45, 42CrMo4)** | [Bossard Technische Information 01/2025](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff C45 V, 42CrMo4 V, Rm > 800 N/mm²: Schraubenfestigkeitsklasse 8.8 Regelgewinde: 0,8 · d [0,9 · d nach VDI 2230]; 10.9: 0,9 · d [1,1 · d]; 12.9: 1,0 · d [1,2 · d]“* |
| **Grauguss GJL 250 (GG-25, $R_m > 220\text{ N/mm}^2$)** | [Bossard Technische Information 01/2025](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff GJL 250 (GG-25), Rm > 220 N/mm²: Schraubenfestigkeitsklasse 8.8 Regelgewinde: 1,0 · d [1,3 · d nach VDI 2230]; 10.9: 1,25 · d [1,6 · d]; 12.9: 1,4 · d [1,8 · d]“* |
| **Grauguss (GG-22 / Gusseisen allgemein)** | [Schweizer-FN Maschinenelemente / Tabellenbuch Metall / VDI 2230](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php) | *„Gusseisenwerkstoffe: 3.6-4.6: 1,3 * d \| 4.8-6.8: 1,5 * d \| 8.8: 1,5 * d [VDI 2230]; GG-22 d/P < 9 bei 8.8: 1,0 * d; d/P ≥ 9 bei 8.8: 1,2 * d [Tabellenbuch Metall]“* |
| **Aluminium-Knetlegierung ausgehärtet ($R_m > 330\text{ N/mm}^2$, z. B. AlMgSi1 F32)** | [Bossard Technische Information 01/2025](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff AlMgSi1 F32, Rm > 330 N/mm²: Schraubenfestigkeitsklasse 8.8 Regelgewinde: 1,4 · d; 10.9: 1,6 · d“* |
| **Aluminium-Knetlegierung hochfest ($R_m > 550\text{ N/mm}^2$, z. B. AlZnMgCu0,5 F50)** | [Bossard Technische Information 01/2025](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff AlZn MgCu 0,5 F50, Rm > 550 N/mm²: Schraubenfestigkeitsklasse 8.8 Regelgewinde: 1,0 · d“* |
| **Aluminium-Knetlegierung weich ($R_m > 180\text{ N/mm}^2$, z. B. AlMg3 F18)** | [Bossard Technische Information 01/2025](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Bauteilwerkstoff AlMg3 F18, Rm > 180 N/mm²: Schraubenfestigkeitsklasse 8.8 Regelgewinde: 2 · d [3 · d nach VDI 2230]“* |
| **Aluminium-Gusslegierungen** | [Schweizer-FN / VDI 2230 Blatt 1](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php) / [Bossard (GMgAl9Zn1)](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf) | *„Aluminium-Gusslegierungen: 3.6-4.6: 1,6 * d \| 4.8-6.8: 2,2 * d [VDI 2230]; GMgAl9 Zn1 Rm > 230: 8.8: 1,4 · d \| 10.9: 1,6 · d [Bossard]“* (Hinweis: VDI 2230 rät bei 8.8 in Al-Guss zu Gewindeeinsätzen, da rechnerisch > 2,0 · d erforderlich wäre, was zum Gewindeklemmen führt). |
| **Messing / Kupferlegierungen (CuZn)** | [Schweizer-FN / VDI 2230 Blatt 1](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php) | *„Kupferlegierungen: 3.6 - 4.6: 1,3 * d \| 4.8 - 6.8: 1,3 * d [VDI 2230]; Praxis-Richtwert 8.8: 1,2 · d bis 1,5 · d“* |
| **Kunststoffe (Thermoplaste / Duroplaste)** | [Schweizer-FN / VDI 2230 Blatt 1 / Decker Maschinenelemente](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php) | *„Kunststoffe: 3.6 - 4.6: 2,5 * d [VDI 2230/Lit. 1]; für 8.8: Direktgewinde ungeeignet (Kriechen/Vorspannkraftverlust), Einsatz von Gewindebuchsen erforderlich.“* |

Ergebnis: Für eine Schraube der Festigkeitsklasse **8.8** (Regelgewinde) betragen die belastbaren Mindesteinschraubtiefen:
* **Stahl:** Baustahl (S235): **$1,0 \cdot d$** (Versuchswert Bossard) bis **$1,25 \cdot d$** (Tabellenbuch Metall) bzw. **$1,5 \cdot d$** (VDI 2230 rein theoretisch); Vergütungsstahl (C45/42CrMo4): **$0,8 \cdot d$**.
* **Grauguss (GJL/GG):** **$1,0 \cdot d$** bis **$1,2 \cdot d$** (praxisnah) bzw. bis **$1,3 \cdot d$** bis **$1,5 \cdot d$** (VDI 2230).
* **Aluminium-Knetlegierungen:** Ausgehärtet (AlMgSi1): **$1,4 \cdot d$**; weich/ungehärtet (AlMg3): **$2,0 \cdot d$** (theoretisch bis **$3,0 \cdot d$**).
* **Aluminium-Gusslegierungen:** **$1,4 \cdot d$** (hochfester Guss) bis **$2,0 \cdot d$**; für 8.8 wird ab $1,5 \cdot d$ der Einsatz von Gewindeeinsätzen empfohlen (Klemmgefahr bei $6g/6H$).
* **Messing (CuZn):** Für 4.8–6.8: **$1,3 \cdot d$**; für 8.8 als Praxiswert **$1,2 \cdot d$ bis $1,5 \cdot d$**.
* **Kunststoffe:** Direktes Regelgewinde nur für niedrige Festigkeitsklassen (bis 4.6) mit **$2,0 \cdot d$ bis $2,5 \cdot d$**; für 8.8-Schrauben wegen Kriechneigung und geringer Scherfestigkeit ungeeignet (zwingend Gewindeeinsätze nötig).  
**Sicherheit: Hoch / Abgestützt durch Hersteller-Prüfwerte (Bossard 01/2025) und Berechnungsnorm VDI 2230 Blatt 1.**

---

## 3. Ruthex-Gewindeeinsätze (Standardlänge) für den 3D-Druck

### Spezifikation laut ruthex GmbH
Die Werte stammen aus dem offiziellen Produktdatenblatt der **ruthex GmbH** (Schlehdornstraße 6, 26215 Wiefelstede, Dokumentenstand 15.08.2022) für die metrische RX-Reihe aus bleifreiem Messing:
* **$d_1$:** Außendurchmesser an der Rändelung
* **$d_2$:** Schaftdurchmesser (Einstich)
* **$L$:** Länge des Einsatzes (Nennmaß Standardlänge)
* **$d_3$:** Empfohlener Bohrungsdurchmesser (Lochdurchmesser im Druckteil)
* **Mindesttiefe:** In der offiziellen technischen Zeichnung verbindlich bemaßt als **$L + 1\text{ mm min.}$** (Länge des Einsatzes zzgl. mindestens 1 mm Puffer für verdrängten Kunststoff und Schraubenüberstand bei Sacklöchern).

### Belege und Tabellenauszüge

| Gewindegröße | Parameter & Maße | Quelle (URL) | Zitat / Tabellenauszug |
| :--- | :--- | :--- | :--- |
| **RX-M2.5 (Standard)** | Außendurchmesser $d_1 = \mathbf{4,6\text{ mm}}$<br>Länge $L = \mathbf{5,7\text{ mm}}$<br>Bohrung $d_3 = \mathbf{4,0\text{ mm}}$<br>Mindesttiefe $= \mathbf{6,7\text{ mm}}$ ($5,7+1,0$) | [ruthex GmbH – Offizielles Produktdatenblatt RX-Reihe (PDF)](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) | *„Durchmesser d: M 2,5 \| Gewindeeinsatz: RX-M2,5x5,7 \| Ø (d1): 4,6 \| Ø (d2): 3,9 \| Länge (L) Nennmaß: 5,7 \| W min.: 1,6 \| Ø (d3): 4,0 \| Zeichnung: L + 1mm min.“* |
| **RX-M3 (Standard)** | Außendurchmesser $d_1 = \mathbf{4,6\text{ mm}}$<br>Länge $L = \mathbf{5,7\text{ mm}}$<br>Bohrung $d_3 = \mathbf{4,0\text{ mm}}$<br>Mindesttiefe $= \mathbf{6,7\text{ mm}}$ ($5,7+1,0$) | [ruthex GmbH – Offizielles Produktdatenblatt RX-Reihe (PDF)](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) | *„Durchmesser d: M 3 \| Gewindeeinsatz: RX-M3x5,7 \| Ø (d1): 4,6 \| Ø (d2): 3,9 \| Länge (L) Nennmaß: 5,7 \| W min.: 1,6 \| Ø (d3): 4,0 \| Zeichnung: L + 1mm min.“* |
| **RX-M4 (Standard)** | Außendurchmesser $d_1 = \mathbf{6,3\text{ mm}}$<br>Länge $L = \mathbf{8,1\text{ mm}}$<br>Bohrung $d_3 = \mathbf{5,6\text{ mm}}$<br>Mindesttiefe $= \mathbf{9,1\text{ mm}}$ ($8,1+1,0$) | [ruthex GmbH – Offizielles Produktdatenblatt RX-Reihe (PDF)](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) | *„Durchmesser d: M 4 \| Gewindeeinsatz: RX-M4x8,1 \| Ø (d1): 6,3 \| Ø (d2): 5,5 \| Länge (L) Nennmaß: 8,1 \| W min.: 2,1 \| Ø (d3): 5,6 \| Zeichnung: L + 1mm min.“* |
| **RX-M5 (Standard)** | Außendurchmesser $d_1 = \mathbf{7,1\text{ mm}}$<br>Länge $L = \mathbf{9,5\text{ mm}}$<br>Bohrung $d_3 = \mathbf{6,4\text{ mm}}$<br>Mindesttiefe $= \mathbf{10,5\text{ mm}}$ ($9,5+1,0$) | [ruthex GmbH – Offizielles Produktdatenblatt RX-Reihe (PDF)](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) | *„Durchmesser d: M 5 \| Gewindeeinsatz: RX-M5x9,5 \| Ø (d1): 7,1 \| Ø (d2): 6,3 \| Länge (L) Nennmaß: 9,5 \| W min.: 2,6 \| Ø (d3): 6,4 \| Zeichnung: L + 1mm min.“* |
| **Zusatzbeleg Bohrer-Set** | Bohrer-Ø: 4,0 mm (M2.5/M3), 5,6 mm (M4), 6,4 mm (M5) | [ruthex.de – HSS-Bohrerset Produktseite](https://www.ruthex.de/products/ruthex-hss-bohrer-set-5-tlg-fur-gewindeeinsatze-m2-m2-5-m3-m4-m5-m6-din-338-bohrer-3-2-4-0-5-6-6-4-8-0-mm-fur-kunststoff-stahl-alu-kupfer-messing-uvm) | *„Das Set beinhaltet 5 Bohrer zwischen 3,2 und 8 mm Durchmesser für die Gewindeeinsatzgrößen M2, M2,5, M3, M4, M5, M6 und 1/4" [Bohrer 3,2 / 4,0 / 5,6 / 6,4 / 8,0 mm]“* |

Ergebnis: Laut offiziellem Produktdatenblatt der ruthex GmbH lauten die Werte für die Standardeinsätze:
* **RX-M2.5 (RX-M2,5x5,7):** Außendurchmesser **4,6 mm**, Länge **5,7 mm**, empfohlene Bohrung **4,0 mm**, Mindesttiefe **6,7 mm** (Mindestwandstärke $w = 1,6\text{ mm}$).
* **RX-M3 (RX-M3x5,7):** Außendurchmesser **4,6 mm**, Länge **5,7 mm**, empfohlene Bohrung **4,0 mm**, Mindesttiefe **6,7 mm** (Mindestwandstärke $w = 1,6\text{ mm}$).
* **RX-M4 (RX-M4x8,1):** Außendurchmesser **6,3 mm**, Länge **8,1 mm**, empfohlene Bohrung **5,6 mm**, Mindesttiefe **9,1 mm** (Mindestwandstärke $w = 2,1\text{ mm}$).
* **RX-M5 (RX-M5x9,5):** Außendurchmesser **7,1 mm**, Länge **9,5 mm**, empfohlene Bohrung **6,4 mm**, Mindesttiefe **10,5 mm** (Mindestwandstärke $w = 2,6\text{ mm}$).  
**Sicherheit: Absolut sicher (100 %) / Direkt aus dem Herstellerdatenblatt der ruthex GmbH (Stand 15.08.2022).**

---

## 4. ISO 273 (DIN EN 20273): Durchgangslöcher für Schrauben (M3, M5, M8)

### Spezifikation nach ISO 273
Die Norm **ISO 273** (in Deutschland identisch übernommen als **DIN EN 20273**, früher DIN ISO 273) unterscheidet drei Passungsreihen:
* **Reihe fein (Toleranzklasse H12):** Für enge Passungen / Präzisionsverbindungen.
* **Reihe mittel (Toleranzklasse H13):** Die Standardreihe für den allgemeinen Maschinenbau.
* **Reihe grob (Toleranzklasse H14):** Für grobe Konstruktionen und Schweiß-/Gussbauteile mit Versatz.

### Belege und Tabellenauszüge

| Gewindegröße | fein (H12) | mittel (H13) | grob (H14) | Quelle (URL) | Zitat / Tabellenauszug |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **M3** | **3,2 mm** | **3,4 mm** | **3,6 mm** | [CAD-Markt Normtabelle DIN EN 20273 / ISO 273](https://cad-markt.de/index.php/cad-tutuorials/normen/364-20273-din-iso-20273-durchgangsl) | *„Gewinde: M 3 \| fein: 3,2 \| mittel: 3,4 \| grob: 3,6“* |
| **M5** | **5,3 mm** | **5,5 mm** | **5,8 mm** | [CAD-Markt Normtabelle DIN EN 20273 / ISO 273](https://cad-markt.de/index.php/cad-tutuorials/normen/364-20273-din-iso-20273-durchgangsl) | *„Gewinde: M 5 \| fein: 5,3 \| mittel: 5,5 \| grob: 5,8“* |
| **M8** | **8,4 mm** | **9,0 mm** | **10,0 mm** | [CAD-Markt Normtabelle DIN EN 20273 / ISO 273](https://cad-markt.de/index.php/cad-tutuorials/normen/364-20273-din-iso-20273-durchgangsl) | *„Gewinde: M 8 \| fein: 8,4 \| mittel: 9 \| grob: 10“* |
| **Vergleichsbeleg** | M3: 3,2 / 3,4 / 3,6<br>M5: 5,3 / 5,5 / 5,8<br>M8: 8,4 / 9,0 / 10,0 | [Neue Physik – Durchgangslöcher (Tabelle ISO 273)](https://www.neue-physik.de/353.9_Senkungen.php) | *„Durchgangslöcher: M3: fein 3,2, mittel 3,4, grob 3,6 \| M5: fein 5,3, mittel 5,5, grob 5,8 \| M8: fein 8,4, mittel 9,0, grob 10,0“* |

Ergebnis: Die Durchgangslochdurchmesser nach ISO 273 (DIN EN 20273) betragen:
* **M3:** fein = **3,2 mm** | mittel = **3,4 mm** | grob = **3,6 mm**
* **M5:** fein = **5,3 mm** | mittel = **5,5 mm** | grob = **5,8 mm**
* **M8:** fein = **8,4 mm** | mittel = **9,0 mm** | grob = **10,0 mm**  
**Sicherheit: Absolut sicher (100 %) / Universell identischer Standardwert aller Normauszüge und Fachkataloge.**
