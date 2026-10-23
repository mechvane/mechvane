> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: ISO 286 Grundtoleranzen, Passungssysteme, ISO 2768 Allgemeintoleranzen und FDM-Passungsspiel

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert

Dieses Dokument fasst die Normgrundlagen und Konstruktionsregeln für Passungen und Toleranzen im Maschinenbau sowie deren Übertragung auf den FDM-3D-Druck zusammen. Es dient als Datenbasis für den Wissenskatalog des Projekts **inventa** (parametrisches CAD mit KI-Agenten).

---

## 1. ISO 286-1 Grundtoleranzen (IT-Toleranzgrade)

Das internationale Passungssystem nach **DIN EN ISO 286-1** definiert 20 Grundtoleranzgrade (IT01, IT0, IT1 bis IT18). Der IT-Grad bestimmt die absolute Größe des Toleranzfeldes für einen bestimmten Nennmaßbereich in Abhängigkeit von der Fertigungsgenauigkeit:
* **IT01 bis IT4:** Feinstmesszeuge, optische und hochpräzise feinmechanische Komponenten.
* **IT5 bis IT7:** Präzisionspassungen im Maschinenbau, Lagersitze, Spindeln, Passstifte.
* **IT8 bis IT11:** Allgemeiner Maschinenbau, Nuten, Passfedern, Bohrungen, Drehteile.
* **IT12 bis IT16:** Grobe Zerspanung, Gussteile, Stanzteile, Schweißbaugruppen.

### Maßtabelle: ISO-Grundtoleranzen IT5 bis IT11 (nach DIN EN ISO 286-1)
*Werte in Mikrometer ($\mu\text{m}$, mit $1\,\mu\text{m} = 0{,}001\,\text{mm}$). Quelle: ELESA+GANTER Technisches Handbuch (S. A21) & Reyher TI (TI-219).*

| Nennmaßbereich [mm] | IT5 [$\mu\text{m}$] | IT6 [$\mu\text{m}$] | IT7 [$\mu\text{m}$] | IT8 [$\mu\text{m}$] | IT9 [$\mu\text{m}$] | IT10 [$\mu\text{m}$] | IT11 [$\mu\text{m}$] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **bis 3** | 4 | 6 | 10 | 14 | 25 | 40 | 60 |
| **über 3 bis 6** | 5 | 8 | 12 | 18 | 30 | 48 | 75 |
| **über 6 bis 10** | 6 | 9 | 15 | 22 | 36 | 58 | 90 |
| **über 10 bis 18** | 8 | 11 | 18 | 27 | 43 | 70 | 110 |
| **über 18 bis 30** | 9 | 13 | 21 | 33 | 52 | 84 | 130 |
| **über 30 bis 50** | 11 | 16 | 25 | 39 | 62 | 100 | 160 |
| **über 50 bis 80** | 13 | 19 | 30 | 46 | 74 | 120 | 190 |
| **über 80 bis 120** | 15 | 22 | 35 | 54 | 87 | 140 | 220 |
| **über 120 bis 180** | 18 | 25 | 40 | 63 | 100 | 160 | 250 |
| **über 180 bis 250** | 20 | 29 | 46 | 72 | 115 | 185 | 290 |
| **über 250 bis 315** | 23 | 32 | 52 | 81 | 130 | 210 | 320 |
| **über 315 bis 400** | 25 | 36 | 57 | 89 | 140 | 230 | 360 |
| **über 400 bis 500** | 27 | 40 | 63 | 97 | 155 | 250 | 400 |

### Katalog-Einträge: Grundtoleranzen

* **Aussage / Wert:** Grundtoleranz IT7 für Nennmaße 18–30 mm beträgt $21\,\mu\text{m}$ ($0{,}021\,\text{mm}$); IT6 beträgt $13\,\mu\text{m}$.
  * **Geltungsbereich:** Metallische Bauteile, spanende Fertigung (Reiben, Feindrehen, Rundschleifen), Nennmaßbereich > 18 bis 30 mm.
  * **Herkunft:** Norm über Sekundärquelle (DIN EN ISO 286-1 via ELESA+GANTER Handbuch 2018).
  * **Quelle:** [ELESA+GANTER DIN ISO 286 Grundtoleranzen PDF](https://www.elesa-ganter.at/siteassets/technical/DIN_ISO_286_ISO_Fundamental_Tolerances_DE.pdf), Tabelle S. A21: „       7            10          12           15           18        21       25         30        35        40        46        52        57        63“.
  * **Begründung:** IT7 stellt im allgemeinen Maschinenbau die Standardgenauigkeit für Passungsbohrungen (H7) dar, die mit handelsüblichen Maschinenreibahlen kostengünstig herstellbar ist. IT6 ist die Standardgüte für geschliffene Wellenpassungen (h6, k6, g6).
  * **Härte:** Hinweis.
  * **Prüfstatus:** offen.

---

## 2. Gängige ISO 286 Passungen im System Einheitsbohrung (H7)

Im Maschinenbau wird fast ausnahmslos das **System Einheitsbohrung** (Basisbohrung mit Grundabmaß **H**, unteres Abmaß $EI = 0$) bevorzugt, da Bohrungswerkzeuge (Bohrer, Reibahlen) feste Maße haben, während Außendurchmesser auf der Drehmaschine flexibel toleriert werden können.

### Passungscharakterisierung nach DIN 7154 / DIN 7157 / DIN ISO 286

1. **H7/f7 – Reiner Laufsitz (Spielpassung):**
   * *Verhalten:* Reichliches Spiel, gleitfähig, nimmt Schmierfilm auf.
   * *Anwendung:* Mehrfach gelagerte Wellen, Kolbenführungen, Gleitlagerungen mit Wärmedehnung.
2. **H7/g6 – Enger Laufsitz / Feiner Schiebesitz (Spielpassung):**
   * *Verhalten:* Geringes Spiel ohne merkliches Wackeln, von Hand leicht verschiebbar bei guter Schmierung.
   * *Anwendung:* Schieberäder in Schaltgetrieben, verschiebbare Kupplungshälften, axial bewegliche Loslager (Außenring im Gehäuse oder Innenring auf Welle).
3. **H7/h6 – Gleitsitz (Spielpassung mit Nulllinie):**
   * *Verhalten:* Spiel liegt zwischen $0\,\mu\text{m}$ und Maximalspiel. Von Hand mit leichtem Druck fügbar, kein freies Klappern.
   * *Anwendung:* Wechselräder, Pinolen, Fräsdornaufnahmen, Führungsstangen, Stellringe.
4. **H7/js6 (bzw. H7/j6) – Schiebesitz / Leichte Übergangspassung:**
   * *Verhalten:* Symmetrisches Toleranzfeld ($\pm$), minimale Spiele oder minimale Übermaße. Mit Holzhammer leicht fügbar.
   * *Anwendung:* Häufig auszubauende Naben, Handräder, Riemenscheiben bei geringer Beanspruchung.
5. **H7/k6 – Haftsitz (Klassische Übergangspassung):**
   * *Verhalten:* Meist leichtes Übermaß (Festsitz), selten geringfügiges Spiel. Mit Gummi- oder Schonhammer fügbar.
   * *Anwendung:* **Standard für Wälzlagerinnenringe** auf Wellen bei normaler Last, Riemenscheiben, Zahnräder mit zusätzlicher Passfeder.
6. **H7/m6 – Treibsitz (Übergangspassung mit überwiegendem Übermaß):**
   * *Verhalten:* Merkliches Übermaß. Montage erfordert Handhammer mit Treibdorn oder leichte Spindelpresse.
   * *Anwendung:* **Zylinderstifte (DIN 7 / DIN 6325)** zur Fixierung, Passschrauben, Wälzlagerinnenringe bei hoher Stoßbelastung.
7. **H7/n6 – Fester Treibsitz (Übergangs- bis leichte Übermaßpassung):**
   * *Verhalten:* Deutliches Übermaß. Hoher Montagekraftaufwand (mechanische Presse).
   * *Anwendung:* Radkränze, Schneckenräder, feste Kupplungen.
8. **H7/p6 – Leichter Presssitz (Reine Übermaßpassung):**
   * *Verhalten:* Sicheres Übermaß in allen Toleranzlagen. Fügen erfordert hydraulische Presse oder Erwärmen der Nabe auf ca. 80–120 °C.
   * *Anwendung:* Einpressbuchsen (Gleitlager), Zahnräder ohne zusätzliche Passfeder bei mittleren Momenten, Lagersitze bei extremen Stoßlasten.
9. **H7/s6 (bzw. H7/r6) – Fester Presssitz (Pressverband):**
   * *Verhalten:* Hohes Übermaß. Nur durch Aufschrumpfen (Erwärmen des Außenrings auf > 150 °C / Unterkühlen der Welle mit Flüssigstickstoff) fügbar.
   * *Anwendung:* Kupplungen auf Wellenenden, Bronzekränze auf Schneckenradkörpern, Schrumpfscheibenverbände ohne Verdrehsicherung.

---

### Vollständige Grenzabmaße für gängige Nennmaße (in $\mu\text{m}$)
*Abmaße in $\mu\text{m}$ ($1\,\mu\text{m} = 0{,}001\,\text{mm}$). $EI/es/ei$: $EI$ = unteres Bohrungsabmaß, $ES$ = oberes Bohrungsabmaß, $ei$ = unteres Wellenabmaß, $es$ = oberes Wellenabmaß. Quellen: ELESA+GANTER S. A22, Axes Industries Memento M15, Böttcher/Forberg.*

| Nennmaß $d$ [mm] | Bohrung H7 ($EI / ES$) | Welle f7 ($ei / es$) | Welle g6 ($ei / es$) | Welle h6 ($ei / es$) | Welle js6 ($ei / es$) | Welle k6 ($ei / es$) | Welle m6 ($ei / es$) | Welle n6 ($ei / es$) | Welle p6 ($ei / es$) | Welle s6 ($ei / es$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **6** | $0 / +12$ | $-22 / -10$ | $-12 / -4$ | $-8 / 0$ | $\pm 4$ | $+1 / +9$ | $+4 / +12$ | $+8 / +16$ | $+12 / +20$ | $+19 / +27$ |
| **10** | $0 / +15$ | $-28 / -13$ | $-14 / -5$ | $-9 / 0$ | $\pm 4{,}5$ | $+1 / +10$ | $+6 / +15$ | $+10 / +19$ | $+15 / +24$ | $+23 / +32$ |
| **18** | $0 / +18$ | $-34 / -16$ | $-17 / -6$ | $-11 / 0$ | $\pm 5{,}5$ | $+1 / +12$ | $+7 / +18$ | $+12 / +23$ | $+18 / +29$ | $+28 / +39$ |
| **25** | $0 / +21$ | $-41 / -20$ | $-20 / -7$ | $-13 / 0$ | $\pm 6{,}5$ | $+2 / +15$ | $+8 / +21$ | $+15 / +28$ | $+22 / +35$ | $+35 / +48$ |
| **30** | $0 / +21$ | $-41 / -20$ | $-20 / -7$ | $-13 / 0$ | $\pm 6{,}5$ | $+2 / +15$ | $+8 / +21$ | $+15 / +28$ | $+22 / +35$ | $+35 / +48$ |
| **50** | $0 / +25$ | $-50 / -25$ | $-25 / -9$ | $-16 / 0$ | $\pm 8$ | $+2 / +18$ | $+9 / +25$ | $+17 / +33$ | $+26 / +42$ | $+43 / +59$ |

### Resultierende Grenzspiele und Grenzübermaße für gängige Nennmaße

*Definitionen:*  
* *Spielpassung:* Höchstspiel $P_{\max} = ES - ei$; Mindestspiel $P_{\min} = EI - es$.  
* *Übermaßpassung:* Höchstübermaß $U_{\max} = es - EI$; Mindestübermaß $U_{\min} = ei - ES$.  
* Positive Werte = Spiel (Luft); negative Werte = Übermaß (Klemmen).

| Nennmaß | H7/g6 Spiel [$P_{\min} \dots P_{\max}$] | H7/h6 Spiel [$P_{\min} \dots P_{\max}$] | H7/k6 Passungscharakter | H7/p6 Übermaß [$U_{\min} \dots U_{\max}$] |
| :---: | :---: | :---: | :---: | :---: |
| **Ø 6 mm** | $+4 \dots +24\,\mu\text{m}$ | $0 \dots +20\,\mu\text{m}$ | $-9\,\mu\text{m}$ (Übermaß) bis $+11\,\mu\text{m}$ (Spiel) | $+0 \dots +20\,\mu\text{m}$ Übermaß |
| **Ø 10 mm** | $+5 \dots +29\,\mu\text{m}$ | $0 \dots +24\,\mu\text{m}$ | $-10\,\mu\text{m}$ bis $+14\,\mu\text{m}$ | $+0 \dots +24\,\mu\text{m}$ Übermaß |
| **Ø 18 mm** | $+6 \dots +35\,\mu\text{m}$ | $0 \dots +29\,\mu\text{m}$ | $-12\,\mu\text{m}$ bis $+17\,\mu\text{m}$ | $+0 \dots +29\,\mu\text{m}$ Übermaß |
| **Ø 25 mm** | $+7 \dots +41\,\mu\text{m}$ | $0 \dots +34\,\mu\text{m}$ | $-15\,\mu\text{m}$ bis $+19\,\mu\text{m}$ | $+1 \dots +35\,\mu\text{m}$ Übermaß |
| **Ø 30 mm** | $+7 \dots +41\,\mu\text{m}$ | $0 \dots +34\,\mu\text{m}$ | $-15\,\mu\text{m}$ bis $+19\,\mu\text{m}$ | $+1 \dots +35\,\mu\text{m}$ Übermaß |
| **Ø 50 mm** | $+9 \dots +50\,\mu\text{m}$ | $0 \dots +41\,\mu\text{m}$ | $-18\,\mu\text{m}$ bis $+23\,\mu\text{m}$ | $+1 \dots +42\,\mu\text{m}$ Übermaß |

---

## 3. Typische industrielle Anwendungen und Gestaltungsregeln

### A) Wälzlagersitze
* **Innenring auf rotierender Welle (Umfangslast am Innenring):**
  * Toleranz: **k5 / k6** (für normale Belastung bis Ø 40 mm) bzw. **m5 / m6** (für mittlere bis hohe Lasten bis Ø 100 mm).
  * Begründung: Der Innenring neigt unter der rotierenden Radialkraft zum Wandern auf dem Zapfen („Rundwandern“). Ein minimales Übermaß verhindert Passungsrost und Relativbewegung.
* **Außenring im stehenden Gehäuse (Punktlast am Außenring):**
  * Toleranz: **H7** (für leicht verschiebbare Loslager) bzw. **J7 / K7** (für Festlager ohne Schläge).
  * Begründung: Das Loslager muss Wärmedehnungen der Welle axial ausgleichen können, ohne zu verspannen.
* **Innenring auf stehender Achse (Punktlast am Innenring):**
  * Toleranz: **g6 / h6**. Das Lager lässt sich leicht axial montieren und verschieben.

### B) Zylinderstifte und Passstifte (DIN 7 / ISO 2338 & DIN 6325 / ISO 8734)
* **Passungsbohrung:** Ausführung immer in **H7**.
* **Zylinderstift ungehärtet (DIN 7 / ISO 2338 Form A):**
  * Stifttoleranz: **m6** (Standardausführung) bzw. **h6**.
  * Paarung H7/m6: Ergibt einen Treibsitz, der durch elastische Deformation eine spielfreie Ausrichtung von Bauteilen garantiert.
* **Zylinderstift durchgehärtet (DIN 6325 / ISO 8734):**
  * Stifttoleranz: **m5** (Standard für gehärtete Führungs- und Anschlagstifte nach Reyher TI-10).
  * Paarung H7/m5: Hohe Wiederholgenauigkeit bei geringerem Fressrisiko als m6, da gehärteter Stahl kaum fließt.

### C) Gleitlagerbuchsen (z. B. Sinterbronze, POM, igus iglidur®)
* **Aufnahmebohrung im Gehäuse:** Ausführung **H7**.
* **Außendurchmesser der Buchse vor dem Einpressen:** Toleriert mit **r7 / s7 / p6**.
  * Begründung: Die Buchse benötigt festen Halt im Gehäuse, um axiale Schubkräfte und Drehmomente ohne zusätzliche Schrauben aufzunehmen.
* **Innendurchmesser nach dem Einpressen:**
  * Durch das Einpressen schnürt sich die dünnwandige Buchse um ca. 80–100 % des Übermaßes ein.
  * Resultierende Lagerbohrung: **H9** bis **D10** (abhängig vom Wanddickenverhältnis).
  * Passende Welle: **h6** bis **f7** (gewährleistet Betriebsspiel von 0,02 bis 0,06 mm für Schmierfilmaufbau).

---

## 4. Allgemeintoleranzen nach DIN EN 22768-1 / ISO 2768-1

Die Norm **ISO 2768-1** gilt für spanend bearbeitete oder umgeformte metallische Werkstücke für Maße ohne direkte Toleranzangabe. Sie verhindert die unnötige Über-Tolerierung von Zeichnungen.

### Tabelle 1: Grenzabmaße für Längenmaße (nach ISO 2768-1, Werte in mm)
*Quelle: DIN EN 22768-1 / Reyher TI-216 / CAD-Markt.*

| Nennmaßbereich [mm] | f (fein) [mm] | m (mittel) [mm] | c (grob) [mm] | v (sehr grob) [mm] |
| :--- | :---: | :---: | :---: | :---: |
| **0,5 bis 3** | $\pm 0{,}05$ | $\pm 0{,}10$ | $\pm 0{,}20$ | — |
| **über 3 bis 6** | $\pm 0{,}05$ | $\pm 0{,}10$ | $\pm 0{,}30$ | $\pm 0{,}50$ |
| **über 6 bis 30** | $\pm 0{,}10$ | $\pm 0{,}20$ | $\pm 0{,}50$ | $\pm 1{,}00$ |
| **über 30 bis 120** | $\pm 0{,}15$ | $\pm 0{,}30$ | $\pm 0{,}80$ | $\pm 1{,}50$ |
| **über 120 bis 400** | $\pm 0{,}20$ | $\pm 0{,}50$ | $\pm 1{,}20$ | $\pm 2{,}50$ |
| **über 400 bis 1000** | $\pm 0{,}30$ | $\pm 0{,}80$ | $\pm 2{,}00$ | $\pm 4{,}00$ |
| **über 1000 bis 2000** | $\pm 0{,}50$ | $\pm 1{,}20$ | $\pm 3{,}00$ | $\pm 6{,}00$ |
| **über 2000 bis 4000** | — | $\pm 2{,}00$ | $\pm 4{,}00$ | $\pm 8{,}00$ |

### Tabelle 2: Grenzabmaße für gebrochene Kanten (Radien $r$ und Fasenhöhen $h$)

| Nennmaßbereich [mm] | f (fein) [mm] | m (mittel) [mm] | c (grob) [mm] | v (sehr grob) [mm] |
| :--- | :---: | :---: | :---: | :---: |
| **0,5 bis 3** | $\pm 0{,}20$ | $\pm 0{,}20$ | $\pm 0{,}40$ | $\pm 0{,}40$ |
| **über 3 bis 6** | $\pm 0{,}50$ | $\pm 0{,}50$ | $\pm 1{,}00$ | $\pm 1{,}00$ |
| **über 6** | $\pm 1{,}00$ | $\pm 1{,}00$ | $\pm 2{,}00$ | $\pm 2{,}00$ |

### Tabelle 3: Form- und Lagetoleranzen nach ISO 2768-2 (Geradheit und Ebenheit)

| Nennmaßbereich [mm] | H [mm] | K [mm] | L [mm] |
| :--- | :---: | :---: | :---: |
| **bis 10** | $0{,}02$ | $0{,}05$ | $0{,}10$ |
| **über 10 bis 30** | $0{,}05$ | $0{,}10$ | $0{,}20$ |
| **über 30 bis 100** | $0{,}10$ | $0{,}20$ | $0{,}40$ |
| **über 100 bis 300** | $0{,}20$ | $0{,}40$ | $0{,}80$ |
| **über 300 bis 1000** | $0{,}30$ | $0{,}60$ | $1{,}20$ |

*Standard-Zeichnungseintrag:* Im Maschinenbau ist die Kombination **ISO 2768-mK** (Längenmaße mittel, Geometrie K) der de-facto-Industriestandard für Zerspanungsteile.

---

## 5. Passungsspiel und Toleranzen für den FDM-3D-Druck

### Warum FDM-Bohrungen konstruktionsbedingt schrumpfen
Im FDM-Verfahren hergestellte zylindrische Innenkonturen (Bohrungen entlang der Z-Achse) drucken bei Standardeinstellungen systematisch **$0{,}15 \text{ bis } 0{,}35\text{ mm}$ kleiner** als das CAD-Nennmaß. Ursachen:
1. **Polygonierung:** Exportierte STL-Netze approximieren Kreise durch Sehnen, wodurch der Innenkreisradius geometrisch verkleinert wird.
2. **Strangstauchung (Extrusion Die Swell & Flattening):** Die Düse presst den zylindrischen Kunststoffstrang flach. Bei engen Radien wird der Strang nach innen gezogen (Sehnenkraft des viskosen Filaments).
3. **Thermische Schwindung:** Das Filament erstarrt und kontrahiert zur Lochmitte hin.

### Empfohlene CAD-Passungsspaltmaße für FDM (PLA/PETG, Düse 0,4 mm)
*Basierend auf Prusa Research Guidelines, CNC Kitchen Untersuchungen und Praxistests.*

| Passungsart | CAD-Nennspalt (radial) | CAD-Maßabweichung (Durchmesser) | Verhalten & Montage |
| :--- | :---: | :---: | :--- |
| **Fester Presssitz** | $-0{,}05 \dots 0{,}00\text{ mm}$ | $\mathbf{0{,}00 \dots +0{,}05\text{ mm}}$ über Nennmaß | Fügen mit Schraubstock, Klemme oder thermisch. Bei PLA Bruchgefahr; ideal für PETG/ABS. |
| **Leichter Klemmsitz / Lagersitz** | $+0{,}05 \dots +0{,}10\text{ mm}$ | $\mathbf{+0{,}10 \dots +0{,}15\text{ mm}}$ über Nennmaß | Sitzt spielfrei, per Hand/Daumendruck fügbar. Verrutscht im Betrieb nicht. |
| **Schiebesitz / Übergang** | $+0{,}10 \dots +0{,}15\text{ mm}$ | $\mathbf{+0{,}20 \dots +0{,}30\text{ mm}}$ über Nennmaß | Bauteile lassen sich saugend ineinander schieben (z. B. Führungsstifte, Deckel). |
| **Bewegliche Spielpassung** | $+0{,}20 \dots +0{,}25\text{ mm}$ | $\mathbf{+0{,}40 \dots +0{,}50\text{ mm}}$ über Nennmaß | Für Scharniere, rotierende Wellen und Gelenke (Print-in-Place). |
| **Lose Führung** | $> +0{,}30\text{ mm}$ | $\mathbf{> +0{,}60\text{ mm}}$ über Nennmaß | Ungeführte Durchführungen, Kabelkanäle, lockere Schieber. |

### Konstruktionsregeln für 3D-Druck-Passungen

* **Horizontale Lochkompensation im Slicer (X/Y hole compensation):**
  * Statt im CAD jedes Loch künstlich aufzuweiten, wird im Slicer (PrusaSlicer / BambuStudio) ein globaler Offset von **$+0{,}10 \text{ bis } +0{,}15\text{ mm}$** auf Innenlöcher gelegt. Dadurch stimmen CAD-Nennmaße mit dem Realteil überein.
* **Einführfasen:** 
  * An jeder Einpressöffnung zwingend eine Fase von **$0{,}5\text{ mm} \times 45^\circ$** oder **$1{,}0\text{ mm} \times 30^\circ$** anbringen, um ein Abscheren der Schichten beim Fügen zu verhindern.
* **Quetschrippen (Crush Ribs):**
  * Für unkalibrierte Drucker: Statt einer zylindrischen Vollwandung 3 bis 4 spitze Längsrippen ($0{,}3\text{ mm}$ breit, $0{,}15\text{ mm}$ Übermaß) an der Bohrungswand modellieren. Diese verformen sich beim Einpressen plastisch/elastisch und nehmen Drucktoleranzen schadlos auf.
* **Mindestwandstärken um Presssitze:**
  * Mindestens **$2{,}0 \text{ bis } 3{,}0\text{ mm}$ Wandstärke** bzw. **4 bis 5 massive Perimeter**, um die Umfangsspannung (Kesselformel) ohne Delamination aufzunehmen.

---

## 6. Katalog-Einträge im Standardformat

### Eintrag 1: Passung H7/k6 für Wälzlager-Festsitz
* **Aussage / Wert:** Bei einem Nenndurchmesser von Ø 20 mm liegt die Passung H7/k6 zwischen $-15\,\mu\text{m}$ (Höchstübermaß) und $+19\,\mu\text{m}$ (Höchstspiel). *(korrigiert am 2026-10-21: +17 µm -> +19 µm)*
* **Geltungsbereich:** Stahlwellen und Wälzlagerinnenringe bei rotierender Welle (Umfangslast), Durchmesserbereich > 18 bis 30 mm.
* **Herkunft:** Norm über Sekundärquelle (DIN ISO 286 via TU Dresden Konstruktionslehre).
* **Quelle:** [TU Dresden – Kennzeichen und Anwendungsbeispiele wichtiger Passungen PDF](https://wwwpub.zih.tu-dresden.de/~tschoen/konstr/chapter03/tables/passung.pdf), S. 1.
  * *Wörtliches Zitat:* „H7/k6     K7/h6     H7/k6     Haftsitzteile unter  Riemenscheiben,“
* **Begründung:** Durch die leichte Überdeckung wird verhindert, dass der gehärtete Innenring auf der Welle relativ rotiert und Reibkorrosion (Passungsrost) verursacht, während die Montage mit leichten Hammerschlägen noch möglich bleibt.
* **Härte:** Hinweis.
* **Prüfstatus:** teilbelegt (Anwendungsempfehlung H7/k6 in TU Dresden wörtlich belegt; Grenzmaße aus DIN ISO 286).

### Eintrag 2: Passung H7/m6 für Zylinderstifte
* **Aussage / Wert:** Bohrung H7 ($0 / +15\,\mu\text{m}$) gepaart mit Stift m6 ($+6 / +15\,\mu\text{m}$) für Ø 10 mm ergibt $-15\,\mu\text{m}$ bis $0\,\mu\text{m}$ Übermaß (Treibsitz).
* **Geltungsbereich:** Ungehärtete Zylinderstifte nach DIN 7 / ISO 2338 in Durchgangs- und Sacklochbohrungen.
* **Herkunft:** Norm über Sekundärquelle (DIN ISO 286 via Reyher TI-10 & Böttcher/Forberg).
* **Quelle:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf), S. TI-115.
  * *Wörtliches Zitat:* „ISO 2338 [...] ersetzt DIN 7 [...] Toleranzfeld m6“
* **Begründung:** Garantiert spielfreie Zentrierung von zwei Gehäusehälften ohne Nachbearbeitung im montierten Zustand.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

### Eintrag 3: Allgemeintoleranz Längenmaße ISO 2768-m
* **Aussage / Wert:** Längenmaße von über 30 bis 120 mm dürfen bei Toleranzklasse „m“ um maximal $\pm 0{,}3\text{ mm}$ vom Nennmaß abweichen.
* **Geltungsbereich:** Spanend gefertigte Bauteile aus Metall (Fräsen, Drehen) und Kunststoffspritzguss, Nennmaße 30–120 mm.
* **Herkunft:** Norm über Sekundärquelle (ISO 2768-1 via Messtec).
* **Quelle:** [Messtec Allgemeintoleranzen DIN ISO 2768-1 PDF](https://www.messtec.ch/downloads/Allgemeintoleranzen_DIN_ISO_2768-1.pdf), Tabelle 1 (Grenzabmaße für Längenmaße).
  * *Wörtliches Zitat:* „m (mittel)       ± 0,1        ± 0,1        ± 0,2        ± 0,3         ± 0,5     ± 0,8         ± 1,2           ±2“
* **Begründung:** Festlegung des wirtschaftlich erreichbaren Fertigungsstandards ohne Sonderwerkzeuge.
* **Härte:** Fehler (bei Überschreitung in `check_design` als Zeichnungsfehler zu werten, wenn ISO 2768-m angegeben ist).
* **Prüfstatus:** offen.

### Eintrag 4: FDM-Mindestspalt für bewegliche Verbindungen
* **Aussage / Wert:** Der konstruktive Spalt für bewegliche Baugruppen (Scharniere, Gelenke, Führungen) muss mindestens $\mathbf{0{,}30\text{ mm}}$ (empfohlen $0{,}40\text{ mm}$) betragen.
* **Geltungsbereich:** FDM-3D-Druck, Standard-Düse 0,4 mm, Schichthöhe 0,15–0,25 mm, Werkstoffe PLA, PETG, ABS.
* **Herkunft:** Hersteller / Fertigungsdienstleister (Prusa Research).
* **Quelle:** [Prusa Research FAQ Tolerances](https://help.prusa3d.com/article/faq-frequently-asked-questions_1932).
  * *Wörtliches Zitat:* „According to our testing, the precision tolerance of a well-assembled Original Prusa printer is 0,1 mm on the Z-axis and 0,3 mm on X and Y.“
* **Begründung:** Bei Spaltmaßen $< 0{,}30\text{ mm}$ verschmelzen benachbarte Perimeterschichten durch Wärmestrahlung und Materialquellung unlösbar miteinander.
* **Härte:** Fehler (bei Print-in-Place Scharnieren mit Spalt $< 0{,}3\text{ mm}$ schlägt der Druck fehl).
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht; Prusa belegt nur Fertigungstoleranz 0,1 mm Z / 0,3 mm X/Y, nicht den Mindestspalt für bewegliche Teile).

---

## 7. Nicht erreichbare Quellen und offene Fragen

### Nicht erreichbare Quellen
| URL | Code / Fehler | Bemerkung |
| :--- | :---: | :--- |
| `https://www.hug-technik.com/inhalt/ta/passung.html` | 502 Bad Gateway | Server-Fehler beim Händlerportal. |
| `https://de.misumi-ec.com/maker/misumi/mech/tech/meviy_fa_accuracy.html` | 000 Timeout | Misumi blockiert automatisierte Container-Anfragen via WAF. |
| `https://partbase.com` | 403 Forbidden | Bot-Schutz aktiv. |

### Offene Fragen
1. **Verifizierung von s6-Grenzabmaßen bei Großabmessungen:** Weichen die s6-Abmaße für Nennmaße $> 100\text{ mm}$ zwischen ISO 286:1988 und der Neufassung ISO 286:2010 ab? (Prüfung am Vollnormblatt erforderlich).
2. **Kriecheffekt bei FDM-Presssitzen:** Wie stark relaxiert die Einpresskraft bei PLA- und PETG-Lagersitzen nach 100 Betriebsstunden unter Raumtemperatur durch viskoelastisches Fließen? (Versuch auf Ultimaker 2+ planen).
3. **Einfluss von Infill-Dichte auf Bohrungstoleranz:** Verändert ein Gitter-Infill (Grid) gegenüber Gyroid-Infill die Kreisformtoleranz von Z-Bohrungen messbar? (Messreihe mit Innenmikrometer planen).

---

Stichprobe Claude (2026-10-21): IT6/IT7 für 18–30 mm (13/21 µm) stimmen.
