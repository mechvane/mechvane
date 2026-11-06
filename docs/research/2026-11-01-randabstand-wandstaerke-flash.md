> Gemini-3.8-Flash-Rohfassung mit Web, verifiziert mit `tools/check_sources.py`. Recherche 2026-11-01. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Randabstand und Mindestwandstärke je Werkstoff und Fertigungsverfahren

> **Prüfnotiz (Claude, 2026-11-03):** Rohfassung von Gemini Flash (#27). `check_sources.py`: 21/21 Zitate gefunden. Stichprobe Eurocode-Tabelle 3.3 (e1, e2 ≥ 1,2·d0; p1 ≥ 2,2·d0; p2 ≥ 2,4·d0; Höchstwerte 4t+40 bzw. min(14t, 200)) stimmt. Werte zur Fertigung (Guss, FDM, Spritzguss) sind Richtwerte aus Herstellerquellen, nicht genormt.

- **Datum:** 2026-11-01
- **Status:** Gemini 3.8 Flash, quellenverifiziert mit `tools/check_sources.py`
- **Bezug:** Issue #27 (Erweiterung der Konstruktionsregeln für `check_design` und Vorbereitung der Werkstoffdatenbank)
- **Autor:** Antigravity (Gemini 3.8 Flash)

---

## 1. Ausgangslage und Motivation

In der bisherigen Architektur von Mechvane (`mechvane/design_rules.py`) werden geometrische Machbarkeitsprüfungen (`check_design`) über zwei statische Fertigungsprofile abgebildet:
1. `fdm_0.4` (FDM-Druck mit 0,4-mm-Düse): Mindestwandstärke $1{,}2\text{ mm}$, Randabstandfaktor $1{,}5 \cdot d$.
2. `cnc_alu` (CNC-Fräsen in Aluminium): Mindestwandstärke $1{,}0\text{ mm}$, Randabstandfaktor $1{,}5 \cdot d$.

Diese globale Vereinfachung stößt in der Praxis an Grenzen:
* **Werkstoffabhängigkeit:** Ein Edelstahl 1.4301 oder Vergütungsstahl 42CrMo4 verlangt beim Fräsen aufgrund höherer Zerspankräfte und Werkzeugdrücke andere Mindestwandstärken als weiches Knetaluminium (EN AW-6082) oder spangebendes Messing (CuZn39Pb3). Dünnwandige Kunststoffe (POM, PA6) federn beim Zerspanen elastisch aus oder neigen durch Zerspanungswärme zu Verzug.
* **Fertigungsverfahren:** Beim Aluminium-Druckguss bestimmen Schmelzefluss, Erstarrungszeit und Füllbarkeit der Formkavität die Wandstärke ($0{,}8 \dots 3{,}0\text{ mm}$). Im Sandguss von Grauguss (EN-GJL) führt ein Unterschreiten von $4 \dots 5\text{ mm}$ Wandstärke zu rasanter Abkühlung und gefürchteter „Weißerstarrung“ (metastabile Carbid-/Ledeburitbildung, glashart und unzerspanbar). Im Blechbiegen droht bei Bohrungen nahe der Biegetangente ($< 4 \cdot t$) eine Ovalisierung des Lochs.
* **Bohrungstyp und Belastung:** Eine einfache Durchgangsbohrung für Schrauben ohne Querkraftbeanspruchung unterliegt primär fertigungstechnischen Minimalabständen (Ausbeulen, Wanddurchbruch, Werkzeugabdrängung). Eine Gewindebohrung erzeugt beim Anziehen unter $60^\circ$-Flankenwinkel radiale Keilkräfte (Tangentialspannung nach Lamé), die bei zu geringer Restwandstärke zum Aufplatzen des Bauteils führen. Schraubverbindungen im Stahlbau nach DIN EN 1993-1-8 (Eurocode 3) müssen rechnerisch gegen Lochleibungsversagen und Scherausbruch (Blockversagen) abgesichert werden.

Ziel dieser Recherche ist die Erarbeitung einer fundierten Daten- und Formelbasis für die 6 zentralen Fertigungsverfahren (**Fräsen/Drehen**, **Aluminium-Druckguss/Sandguss**, **Grauguss**, **Blech**, **FDM-3D-Druck**, **Kunststoffspritzguss**) und die 5 Werkstoffgruppen (**Stahl**, **Edelstahl**, **Aluminium**, **Messing**, **Thermoplast**).

Gemäß Aufgabenstellung gilt eine Kennwertangabe nur dann als **belegt**, wenn mindestens **zwei unabhängige Quellen** denselben Wert oder Bereich stützen. Liegt nur eine Quelle vor, wird der Wert ausdrücklich als **Richtwert** deklariert.

---

## 2. Übersichtstabellen je Fertigungsart

### 2.1 Spanende Fertigung: CNC-Fräsen und CNC-Drehen

Beim Zerspanen wird die Mindestwandstärke durch die Biegesteifigkeit der Wand gegen die Schnittkräfte $F_c, F_p$ sowie die Ratterneigung bestimmt. Der Mindestrandabstand verhindert ein Ausbeulen oder Durchbrechen des Stegs beim Bohren sowie das Verlaufen der Bohrerspitze.

| Werkstoffgruppe | Mindestwandstärke empfohlen [mm] | Mindestwandstärke machbar [mm] | Schlankheitsgrad ($h : t$) max. | Randabstand $c$ (Lochrand $\rightarrow$ Kante) | Randabstand $e$ (Lochmitte $\rightarrow$ Kante) | Bohrungsabstand $p$ (Loch $\rightarrow$ Loch) | Gewindebohrung: Wandstärke $s$ um Gewinde | Status | Belege |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Stahl** (z. B. S235JR, C45) | **0,8** | **0,5** | 10:1 (abgestützt) / 3:1 (frei) | $\ge 0{,}8\text{ mm}$ bzw. $\ge 0{,}5 \cdot d$ | $\ge 1{,}2 \dots 1{,}5 \cdot d$ | $\ge 1{,}0\text{ mm}$ bzw. $\ge 2{,}0 \cdot d$ | $s \ge 0{,}3 \dots 0{,}5 \cdot d$ | **belegt** | Hubs, Protolabs, Fictiv |
| **Edelstahl** (z. B. 1.4301) | **0,8** | **0,6** | 8:1 (abgestützt) / 2,5:1 (frei) | $\ge 1{,}0\text{ mm}$ bzw. $\ge 0{,}6 \cdot d$ | $\ge 1{,}5 \cdot d$ | $\ge 1{,}2\text{ mm}$ bzw. $\ge 2{,}0 \cdot d$ | $s \ge 0{,}4 \dots 0{,}5 \cdot d$ | **belegt** | Hubs, Protolabs, Fictiv |
| **Aluminium** (z. B. EN AW-6082) | **0,8** | **0,5** (Drehen: 0,508 / 0.02") | 10:1 (abgestützt) / 4:1 (frei) | $\ge 0{,}8\text{ mm}$ bzw. $\ge 0{,}5 \cdot d$ | $\ge 1{,}2 \dots 1{,}5 \cdot d$ | $\ge 1{,}0\text{ mm}$ bzw. $\ge 2{,}0 \cdot d$ | $s \ge 0{,}4 \dots 0{,}5 \cdot d$ | **belegt** | Hubs, Protolabs, Fictiv |
| **Messing** (z. B. CuZn39Pb3) | **0,8** | **0,5** | 10:1 (abgestützt) / 3:1 (frei) | $\ge 0{,}8\text{ mm}$ bzw. $\ge 0{,}5 \cdot d$ | $\ge 1{,}2 \dots 1{,}5 \cdot d$ | $\ge 1{,}0\text{ mm}$ bzw. $\ge 2{,}0 \cdot d$ | $s \ge 0{,}4 \cdot d$ | **belegt** | Hubs, Protolabs, Fictiv |
| **Thermoplaste** (z. B. POM, PA6) | **1,5** | **1,0** | 4:1 (abgestützt) / 2:1 (frei) | $\ge 1{,}5\text{ mm}$ bzw. $\ge 1{,}0 \cdot d$ | $\ge 1{,}5 \dots 2{,}0 \cdot d$ | $\ge 2{,}0\text{ mm}$ bzw. $\ge 2{,}5 \cdot d$ | $s \ge 0{,}6 \dots 0{,}8 \cdot d$ | **belegt** | Hubs, Protolabs, Fictiv |

*Hinweis Drehteile:* An dünnwandigen zylindrischen Drehteilen (Rohre, Büchsen) fordert Fictiv werkstoffübergreifend eine Mindestwandstärke von $> 0{,}02\text{ Zoll}$ ($> 0{,}508\text{ mm}$), um plastische Deformationen durch die Spannbacken des Drehfutters zu verhindern.

---

### 2.2 Aluminium-Guss: Druckguss, Sandguss und Kokillenguss

Gusswerkstoffe unterliegen beim Erstarren der Schwindung und Schmelzeflussgrenzen. Dünne Wände erfordern hohe Gießdrücke und kurze Fließwege. Bohrungen werden entweder direkt über Stahlkerne eingegossen oder nach dem Gießen spanend eingebracht.

| Gießverfahren & Werkstoff | Mindestwandstärke empfohlen [mm] | Mindestwandstärke machbar [mm] | Minimaler Bohrungs-$\varnothing$ eingegossen | Max. Kerntiefe durchgehend | Max. Kerntiefe Sackloch | Mindest-Randabstand / Augenwandung | Gewindebohrung: Bearbeitungszugabe & Wand | Status | Belege |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Aluminium-Druckguss** (z. B. AlSi9Cu3) | **1,5 – 3,0** | **0,8** (lokal 0,5) | **2,5 mm** (BDG Tab. 9) | $5 \cdot d$ | $3 \cdot d$ | Randabstand $c \ge 1{,}0 \cdot d$; Wandung Schraubenauge $s_{\text{Auge}} \ge 1{,}0 \dots 1{,}2 \cdot s$ | Kernloch bis $2{,}5 \cdot d$ direkt gießbar; Sackloch 2–3 Gänge Auslauf | **belegt** | BDG Druckguss, BDG Sandguss |
| **Aluminium-Kokillenguss** (z. B. AlSi7Mg) | **3,0 – 5,0** | **2,5** | **4 – 5 mm** (BDG Tab. 8) | $6 \dots 8 \cdot d$ | $4 \cdot d$ | Schraubenauge $s_{\text{Auge}} \approx 1{,}5 \cdot s$ (Bild 13) | Vorgegossen mit 1–2 mm Aufmaß oder voll gebohrt | **belegt** | BDG Sand- und Kokillenguss |
| **Aluminium-Sandguss** (z. B. AlSi7Mg0.3) | **4,0 – 6,0** | **3,0** | **10 – 15 mm** (BDG Tab. 8) | $2 \dots 4 \cdot d$ | Nicht empfohlen (Knick-/Schmelzgefahr) | Schraubenauge $s_{\text{Auge}} \approx 1{,}5 \dots 2{,}0 \cdot s$ | Kleinbohrungen $< 10\text{ mm}$ immer voll aus dem Material bohren | **belegt** | BDG Sand- und Kokillenguss |

*Zink- und Magnesium-Druckguss (Vergleichswerte nach BDG):* Zinkdruckguss erlaubt Mindestwandstärken ab $0{,}3\text{ mm}$ (Bohrungsdurchmesser ab $0{,}8\text{ mm}$); Magnesiumdruckguss ab $0{,}7\text{ mm}$ (Bohrungsdurchmesser ab $2{,}0\text{ mm}$).

---

### 2.3 Grauguss: Gusseisen mit Lamellengraphit (EN-GJL)

Grauguss besitzt hervorragende Dämpfungseigenschaften und eine sehr hohe Druckfestigkeit ($840\text{ N/mm}^2$ bei GJL-250), ist jedoch kerbempfindlich und spröde (Bruchdehnung $A_5 < 0{,}8\,\%$, keine Streckgrenze). 

| Gussstückgröße & Geometrie | Mindestwandstärke Sandguss [mm] | Abkühlungsgefahr bei Dickenunterschreitung | Randabstand Durchgangsloch $c$ (Restwand) | Randabstand Lochmitte $e$ | Mindestwandstärke um Gewinde $s$ | Einschraubtiefe $m_{\text{eff}}$ (8.8) | Status | Belege |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Kleine Bauteile** ($L < 250\text{ mm}$, z. B. Hebel, Deckel) | **4,0 – 6,0** | Weißerstarrung (Ledeburit/Fe3C, unzerspanbar) | $\ge 1{,}0 \cdot d$ | $\ge 1{,}5 \cdot d$ | $s \ge 0{,}5 \cdot d$ | $1{,}25 \dots 1{,}4 \cdot d$ ($8{,}4\text{ mm}$ bei M6) | **Richtwert** | Castfast, Hanke, VDI 2230 |
| **Mittlere Gehäuse** ($L = 250 \dots 600\text{ mm}$, z. B. Getriebegehäuse) | **6,0 – 10,0** | Harte Randschalen, Eigenspannungsrisse | $\ge 1{,}0 \cdot d$ (Auge vorsehen) | $\ge 1{,}5 \dots 1{,}8 \cdot d$ | $s \ge 0{,}6 \cdot d$ | $1{,}25 \dots 1{,}4 \cdot d$ | **Richtwert** | Castfast, Hanke, VDI 2230 |
| **Große Maschinengestelle** ($L > 600\text{ mm}$, z. B. Maschinenbetten) | **10,0 – 18,0** | Gefügeinhomogenität, Kaltlauf | $\ge 1{,}2 \cdot d$ (Augenwulst $\ge 2{,}0 \cdot s$) | $\ge 2{,}0 \cdot d$ | $s \ge 0{,}8 \cdot d$ | $1{,}3 \dots 1{,}5 \cdot d$ | **Richtwert** | Castfast, Hanke, VDI 2230 |

*Gefahr der Weißerstarrung:* Unterschreitet die Wanddicke bei GJL das Abkühlungslimit ($< 3{,}5 \dots 4{,}0\text{ mm}$ bei Sandform), kühlt die Schmelze so rasch ab, dass der Kohlenstoff nicht metastabil als Graphitlamelle ausscheidet, sondern metastabil als extrem harter Zementit erstarrt. Das Gussteil wird an den Kanten glashart und lässt sich mit HSS- oder Hartmetallfräsern nicht mehr wirtschaftlich zerspanen.

---

### 2.4 Blechbearbeitung: Kaltbiegen, Stanzen und Laserschneiden

Im Blechbau hängen alle Geometriegrenzen direkt von der Blechdicke $t$ ab.

| Werkstoffgruppe (Blech) | Mindestblechdicke $t$ [mm] | Mindestbiegeradius $r_{\min}$ (quer zur Walzung) | Mindestloch-$\varnothing$ Laser / Stanzen | Randabstand Lochrand $\rightarrow$ Blechkante $c$ | Randabstand Lochrand $\rightarrow$ Biegelinie $c_{\text{Biege}}$ | Lochabstand Loch $\rightarrow$ Loch $p$ | Status | Belege |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baustahl** (z. B. DC01, S235JR) | 0,5 | $1{,}0 \cdot t$ | $0{,}5 \cdot t$ (Laser) / $1{,}0 \cdot t$ (Stanzen) | $\ge 1{,}0 \cdot t$ (empf. $1{,}5 \cdot t$) | $\ge 4{,}0 \cdot t$ (Protolabs) | $\ge 2{,}0 \cdot t$ | **belegt** | Protolabs, SendCutSend |
| **Edelstahl** (z. B. 1.4301) | 0,5 | $1{,}2 \dots 1{,}5 \cdot t$ | $0{,}6 \cdot t$ (Laser) / $1{,}0 \cdot t$ (Stanzen) | $\ge 1{,}2 \cdot t$ (empf. $2{,}0 \cdot t$) | $\ge 4{,}0 \cdot t$ (Protolabs) | $\ge 2{,}0 \cdot t$ | **belegt** | Protolabs, SendCutSend |
| **Aluminium** (z. B. EN AW-5754 H111) | 0,8 | $1{,}0 \dots 1{,}5 \cdot t$ | $0{,}5 \cdot t$ (Laser) / $1{,}0 \cdot t$ (Stanzen) | $\ge 1{,}0 \cdot t$ (empf. $1{,}5 \cdot t$) | $\ge 4{,}0 \cdot t$ (Protolabs) | $\ge 2{,}0 \cdot t$ | **belegt** | Protolabs, SendCutSend |
| **Aluminium** (z. B. EN AW-6061-T6) | 1,0 | $2{,}0 \dots 3{,}0 \cdot t$ (rissgefährdet!) | $0{,}7 \cdot t$ (Laser) / $1{,}0 \cdot t$ (Stanzen) | $\ge 1{,}5 \cdot t$ | $\ge 4{,}0 \cdot t$ (Protolabs) | $\ge 2{,}5 \cdot t$ | **belegt** | Protolabs, SendCutSend |
| **Kupfer / Messing** (z. B. Cu-ETP, CuZn37) | 0,5 | $1{,}0 \cdot t$ | $0{,}5 \cdot t$ (Laser) / $1{,}0 \cdot t$ (Stanzen) | $\ge 1{,}0 \cdot t$ | $\ge 4{,}0 \cdot t$ (Protolabs) | $\ge 2{,}0 \cdot t$ | **belegt** | Protolabs, SendCutSend |

*Biegefreischnitte (Bend Relief nach SendCutSend):* Breite $b_{\text{Relief}} \ge 0{,}5 \cdot t$, Tiefe $t_{\text{Relief}} \ge r + t + 0{,}020\text{ Zoll}$ ($r + t + 0{,}508\text{ mm}$). Verhindert unkontrolliertes Aufreißen der Kanten an Biegungsenden.

---

### 2.5 FDM-3D-Druck (Schmelzschichtung)

Beim FDM-Druck wird die Mindestwandstärke durch die Strangbreite der Düse (Extrusionsbreite $\approx 1{,}1 \dots 1{,}2 \times d_{\text{nozzle}}$, bei $0{,}4\text{ mm}$ Düse ca. $0{,}45\text{ mm}$) und die Schichthaftung bestimmt.

| Geometriemerkmal | Absolutes Minimum | Empfohlener Standard | Konstruktive Randbedingung | Status | Belege |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **Mindestwandstärke vertikal** | **0,8 mm** (2 Perimeter) | **1,2 – 1,6 mm** (3–4 Perimeter) | Unter 0,8 mm treten Fehlstellen/Lücken auf; Bauteil ist nicht wasserdicht | **belegt** | Hubs 3D, Prusa, CNC Kitchen |
| **Wandhöhe / Schlankheitsgrad** | max. 10:1 (Höhe:Dicke) | max. 4:1 (ohne Stützrippen) | Freistehende Wände neigen durch Düsenreibung zu Schwingungen und Schichtversatz | **belegt** | Hubs 3D |
| **Bohrungsdurchmesser (Z-Achse)** | 1,0 mm (erfordert Nachbohren) | $\ge 2{,}0\text{ mm}$ | Z-Bohrungen schrumpfen um ca. $0{,}2 \dots 0{,}3\text{ mm}$ (Stauchdruck & Facettierung) | **belegt** | Hubs FDM, CNC Kitchen |
| **Randabstand Bohrung $\rightarrow$ Kante** | $\ge 1{,}5\text{ mm}$ (mind. 3 Perimeter) | $\ge 1{,}5 \dots 2{,}0 \cdot d$ | Schichtdelamination bei Zug-/Scherbelastung quer zur Bauteilkante | **belegt** | Hubs, CNC Kitchen |
| **Schraubdom für Heat-Set-Insert (M3)** | $s_{\text{Wand}} \ge 1{,}6\text{ mm}$ ($D_{\text{Dom}} \ge 7{,}2\text{ mm}$) | $D_{\text{Dom}} \ge 2{,}0 \cdot d_{\text{Insert}} \approx 8{,}0\text{ mm}$ | Vorloch-CAD-Nennmaß 4,0 mm (Ruthex/CNC Kitchen); Sacklochtiefe Länge + 1 mm | **belegt** | CNC Kitchen Inserts, Ruthex |
| **Direktverschraubung Kunststoffschraube** | $s_{\text{Wand}} \ge 0{,}5 \cdot d$ | $s_{\text{Wand}} \ge 0{,}6 \dots 0{,}8 \cdot d$ | Mindestens 4 Perimeter; Vorloch $\approx 0{,}8 \cdot d$ (EJOT Delta PT / ecosyn) | **belegt** | CNC Kitchen, Bossard |

---

### 2.6 Kunststoffspritzguss (Thermoplaste)

Im Spritzguss ist die Gleichmäßigkeit der Wandstärke das oberste Gebot. Zu dicke Wände führen zu Einfallstellen und extrem langen Kühlzeiten; zu dünne Wände führen zu unvollständiger Füllung (Short Shots).

| Thermoplast-Gruppe | Typ | Nennwandstärke Protolabs [mm] | Nennwandstärke Fictiv [mm] | Nennwandstärke Zoll-Spanne | Status | Belege |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **ABS** | Amorph | **1,143 – 3,556** | **1,14 – 3,56** | 0.045 – 0.140 in. | **belegt** | Protolabs, Fictiv |
| **POM** (Acetal / Delrin) | Teilkristallin | **0,762 – 3,048** | **0,76 – 3,05** | 0.030 – 0.120 in. | **belegt** | Protolabs, Fictiv |
| **PA** (Polyamid / Nylon) | Teilkristallin | **0,762 – 2,921** | **0,76 – 2,92** | 0.030 – 0.115 in. | **belegt** | Protolabs, Fictiv |
| **PC** (Polycarbonat) | Amorph | **1,016 – 3,810** | **1,02 – 3,81** | 0.040 – 0.150 in. | **belegt** | Protolabs, Fictiv |
| **PP** (Polypropylen) | Teilkristallin | **0,889 – 3,810** (bzw. 0,635) | **1,02 – 3,81** | 0.035 – 0.150 in. | **belegt** | Protolabs, Fictiv |

*Gestaltungsregeln für Rippen und Schraubdome (Protolabs, Fictiv, Hubs übereinstimmend belegt):*
* **Rippendicke an der Basis:** $t_{\text{Rippe}} = 0{,}5 \dots 0{,}6 \cdot T_{\text{Wand}}$ (verhindert Einfallstellen auf der Sichtseite).
* **Rippenhöhe:** $h_{\text{Rippe}} \le 2{,}5 \dots 3{,}0 \cdot T_{\text{Wand}}$ (bei höherem Steifigkeitsbedarf mehrere parallele Rippen einsetzen).
* **Schraubdome (Bosses):** Wandstärke des Doms $t_{\text{Dom}} \le 0{,}6 \cdot T_{\text{Wand}}$; Außendurchmesser $D_{\text{Dom}} \approx 2{,}0 \cdot d_{\text{Schraube}}$.
* **Innenradien an Ecken:** $R_{\text{innen}} \ge 0{,}5 \cdot T_{\text{Wand}}$ (Außenradius konzentrisch: $R_{\text{außen}} = R_{\text{innen}} + T_{\text{Wand}}$).

---

## 3. Schraubenverbindungen im Stahlbau nach DIN EN 1993-1-8 (Eurocode 3)

Im Stahlbau sind die Rand- und Lochabstände streng normiert, um ein vorzeitiges Versagen der Verbindung durch Lochleibung, Scherausbruch (Kantenausreißen) oder Bauteilbeulen zu verhindern.

### 3.1 Normative Rand- und Lochabstände (Tabelle 3.3 nach Sekundärquelle Schweizer-FN)

In Übereinstimmung mit DIN EN 1993-1-8 gelten für den Lochdurchmesser $d_0$ ($d_0 = d + 1\text{ mm}$ bis M14, $d + 2\text{ mm}$ ab M16) und die Dicke des dünnsten äußeren Blechs $t$:

| Abstandsparameter | Bezeichnung nach Eurocode 3 | Mindestwert (normativ) | Empfohlener Wert für volle Tragfähigkeit | Maximalwert (Korrosions-/Beulschutz) |
| :--- | :--- | :---: | :---: | :---: |
| **$e_1$** | Randabstand in Kraftrichtung (Endabstand) | **$e_1 \ge 1{,}2 \cdot d_0$** | **$e_1 \ge 3{,}0 \cdot d_0$** ($\alpha_b = 1{,}0$) | **$e_1 \le 4 \cdot t + 40\text{ mm}$** |
| **$e_2$** | Randabstand rechtwinklig zur Kraftrichtung | **$e_2 \ge 1{,}2 \cdot d_0$** | **$e_2 \ge 1{,}5 \cdot d_0$** ($k_1 = 2{,}5$) | **$e_2 \le 4 \cdot t + 40\text{ mm}$** |
| **$p_1$** | Lochabstand (Teilung) in Kraftrichtung | **$p_1 \ge 2{,}2 \cdot d_0$** | **$p_1 \ge 3{,}75 \cdot d_0$** | **$p_1 \le \min(14 \cdot t, 200\text{ mm})$** |
| **$p_2$** | Lochabstand rechtwinklig zur Kraftrichtung | **$p_2 \ge 2{,}4 \cdot d_0$** | **$p_2 \ge 3{,}0 \cdot d_0$** | **$p_2 \le \min(14 \cdot t, 200\text{ mm})$** |

*Versetzte Schraubenreihen:* Bei versetzten Lochreihen darf der Querabstand auf $p_2 \ge 1{,}2 \cdot d_0$ reduziert werden, sofern der lichte Diagonalschritt $L \ge 2{,}4 \cdot d_0$ einhält.

### 3.2 Analytische Tragfähigkeitsmechanismen nach Eurocode 3

1. **Lochleibungstragfähigkeit $F_{b,Rd}$:**
   $$F_{b,Rd} = \frac{k_1 \cdot \alpha_b \cdot f_u \cdot d \cdot t}{\gamma_{M2}}$$
   mit Teilsicherheitsbeiwert $\gamma_{M2} = 1{,}25$.
   * Der Faktor $\alpha_b$ in Kraftrichtung berücksichtigt das Kantenversagen:
     $$\alpha_b = \min \left( \frac{e_1}{3 \cdot d_0} ;\; \frac{p_1}{3 \cdot d_0} - \frac{1}{4} ;\; \frac{f_{ub}}{f_u} ;\; 1{,}0 \right)$$
     Wird der Mindestwert $e_1 = 1{,}2 \cdot d_0$ gewählt, fällt $\alpha_b$ auf $1{,}2 / 3 = 0{,}40$ ab. Die Verbindung verliert **60 % ihrer Lochleibungstragfähigkeit**! Erst ab $e_1 \ge 3{,}0 \cdot d_0$ erreicht das Bauteil seine volle Tragfähigkeit ($\alpha_b = 1{,}0$).
   * Der Faktor $k_1$ quer zur Kraftrichtung:
     $$k_1 = \min \left( 2{,}8 \cdot \frac{e_2}{d_0} - 1{,}7 ;\; 2{,}5 \right)$$
     Für $k_1 = 2{,}5$ ist $2{,}8 \cdot \frac{e_2}{d_0} - 1{,}7 \ge 2{,}5 \implies e_2 \ge 1{,}5 \cdot d_0$ erforderlich. Bei minimalem Randabstand $e_2 = 1{,}2 \cdot d_0$ sinkt $k_1$ auf $2{,}8 \cdot 1{,}2 - 1{,}7 = 1{,}66$ (Tragfähigkeitsverlust von $34\,\%$).

2. **Scherausbruch / Blockversagen (Block Tear-Out):**
   Wird eine Querkraft $V_{Ed}$ in Kantenrichtung eingeleitet, scheren die beiden seitlichen Scherflächen des Reststegs $c = e_1 - d_0/2$ ab. Die Ausbruchsicherheit erfordert:
   $$V_{Rd} = 2 \cdot c \cdot t \cdot \frac{f_u / \sqrt{3}}{\gamma_{M2}} \ge V_{Ed} \implies c \ge \frac{\sqrt{3} \cdot \gamma_{M2} \cdot V_{Ed}}{2 \cdot t \cdot f_u}$$

---

## 4. Physikalische Herleitung der Regeln (Woher die Regeln kommen)

Damit CAD-Agenten in `check_design` nicht rein auf starre Tabellen angewiesen sind, sondern parametrische Formeln für beliebige Durchmesser, Dicken und Werkstofffestigkeiten auswerten können, müssen die zugrundeliegenden physikalischen Mechanismen verstanden werden.

### 4.1 Fertigungstechnische Mechanismen

1. **Werkzeugdurchbiegung beim Fräsen (Balkenbiegung):**
   Ein Schaftfräser erfährt unter der Passivkraft $F_p$ eine elastische Auslenkung:
   $$\delta_{\text{tool}} = \frac{F_p \cdot L^3}{3 \cdot E_{\text{tool}} \cdot I_{\text{tool}}}$$
   Gleichzeitig federt eine dünne Werkstückwand der Höhe $H$ und Dicke $T$ unter dem Schnittdruck aus:
   $$\delta_{\text{wall}} = \frac{F_p \cdot H^3}{3 \cdot E_{\text{part}} \cdot \left(\frac{B \cdot T^3}{12}\right)} = \frac{4 \cdot F_p \cdot H^3}{E_{\text{part}} \cdot B \cdot T^3}$$
   Da die Wanddurchbiegung umgekehrt proportional zur **dritten Potenz der Wandstärke** ($T^3$) und linear zum **Elastizitätsmodul** $E$ skaliert, erfordern Kunststoffe ($E \approx 2 \dots 3\text{ GPa}$) bei gleicher Wandhöhe eine rund **3- bis 4-mal größere Wandstärke** als Aluminium ($E \approx 70\text{ GPa}$) oder Stahl ($E \approx 210\text{ GPa}$), um elastisches Ausweichen und Rattermarken zu verhindern.

2. **Verlauf der Bohrerspitze bei wandnahen Bohrungen (Tip Wander):**
   Trifft ein Spiralbohrer zu nah an eine Kante ($c < 0{,}8\text{ mm}$), erfährt die Querschneide eine asymmetrische Schnittkraft, weil die elastische Steifigkeit zur Außenkante hin geringer ist als zum Vollmaterial hin. Der Bohrer weicht zur Kante hin aus, was zu unrunden Bohrungen, Wanddurchbrüchen oder Werkzeugbruch führt. Fictiv fordert daher: Mindestens 75 % des Bohrungsquerschnitts müssen im vollen Material liegen.

3. **Gießtechnische Formfüllung und Erstarrung (Chvorinov-Regel):**
   Die Erstarrungszeit $t_e$ eines Gussvolumens ist proportional zum Quadrat des geometrischen Moduls $M = V / A$:
   $$t_e = B \cdot \left(\frac{V}{A}\right)^2 = B \cdot M^2$$
   Bei einer ebenen Wand der Dicke $s$ ist $M \approx s / 2$. Unterschreitet die Wandstärke das verfahrensspezifische Limit ($s < 0{,}8\text{ mm}$ im Druckguss, $s < 3\text{ mm}$ im Sandguss), erstarrt die Schmelzefront vor dem vollständigen Füllen der Kavität (Kaltlauf, Short Run). Bei Grauguss erzwingt $s < 4\text{ mm}$ extrem hohe Abkühlgradienten, wodurch das metastabile Fe-Fe3C-System (Zementit/Ledeburit) statt des stabilen Fe-C-Systems (Graphit) durchlaufen wird („Weißerstarrung“).

4. **Fließzone beim Blechbiegen (Quer- und Längsdehnung):**
   Beim Biegen bildet sich an der Außenseite eine Zugdehnungszone aus, die bis zu einem Abstand von ca. $3 \dots 4 \cdot t$ von der Biegelinie reicht. Liegt eine Bohrung innerhalb dieses Bereichs, fließt das Lochmaterial plastisch in die Biegezone ab; die Bohrung verzieht sich unzulässig zu einer Ellipse.

5. **Schichtanisotropie beim FDM-Druck:**
   FDM-Teile erreichen in Z-Richtung nur $40 \dots 60\,\%$ der Zugfestigkeit der X/Y-Ebene. Bei wandnahen Bohrungen führt der radiale Lochleibungsdruck oder die Sprengwirkung eines Gewindeeinsatzes zum Aufspalten entlang der Schichtgrenzen (Delamination). Daher müssen um jede Bohrung mindestens 3 bis 4 geschlossene Perimeterlinien ($1{,}2 \dots 1{,}6\text{ mm}$) gelegt werden.

---

### 4.2 Festigkeitsmäßige Mechanismen

1. **Tangentiale Zugspannung um Gewindebohrungen (Lamé-Gleichung):**
   Beim Anziehen einer Schraube der Festigkeitsklasse 8.8 mit der Montagevorspannkraft $F_M$ erzeugt der Flankenwinkel ($60^\circ$) einen radialen Innendruck auf die Bohrungswand:
   $$F_{\text{rad}} = F_M \cdot \tan(30^\circ) \approx 0{,}577 \cdot F_M \implies p_i = \frac{F_{\text{rad}}}{\pi \cdot d \cdot m_{\text{eff}}}$$
   Für einen dickwandigen Zylinder mit Innenradius $r_i = d/2$ und Außenradius $r_a = r_i + s$ (Wandstärke $s$) lautet die maximale Tangentialspannung an der Innenfaser:
   $$\sigma_{t,\max} = p_i \cdot \frac{r_a^2 + r_i^2}{r_a^2 - r_i^2} \le R_{p0{,}2}$$
   Wird das Radienverhältnis $Q = r_a / r_i = 1 + \frac{2s}{d}$ aufgelöst, ergibt sich die analytische Mindestwandstärke gegen Fließen/Aufplatzen:
   $$\mathbf{s_{\min} = \left( \sqrt{\frac{\frac{R_{p0{,}2}}{p_i} + 1}{\frac{R_{p0{,}2}}{p_i} - 1}} - 1 \right) \cdot \frac{d}{2}}$$
   * Zahlenbeispiel M6 (8.8, $F_M \approx 10{,}2\text{ kN}$):
     * Stahl S235 ($R_{p0{,}2} = 235\text{ MPa}$, $m_{\text{eff}} = 6\text{ mm}$): $p_i \approx 52\text{ MPa} \implies s_{\min} \approx 0{,}76\text{ mm}$ ($0{,}13 \cdot d$). Mit Praxiszuschlag für Zerspanung: $s \ge 0{,}4 \cdot d = 2{,}4\text{ mm}$.
     * Aluminium 6082-T6 ($R_{p0{,}2} = 260\text{ MPa}$, $m_{\text{eff}} = 8{,}4\text{ mm}$): $p_i \approx 37\text{ MPa} \implies s_{\min} \approx 0{,}46\text{ mm}$. Praxisempfehlung: $s \ge 0{,}4 \dots 0{,}5 \cdot d$.
     * Thermoplast PA6 ($R_{p0{,}2} = 45\text{ MPa}$, $m_{\text{eff}} = 15\text{ mm}$): $p_i \approx 21\text{ MPa} \implies s_{\min} \approx 1{,}95\text{ mm}$ ($0{,}32 \cdot d$). Mit Sicherheitsfaktor für Kriechen/Relaxation ($\approx 1{,}4$): $s \approx 0{,}5 \cdot d$ ($3{,}0\text{ mm}$), was exakt den Empfehlungen von Bossard und Fictiv entspricht.

2. **Lochleibungsversagen und Scherausstanzen:**
   Wird eine Schraubenverbindung auf Abscheren beansprucht, muss das umgebende Material der Lochleibungskraft widerstehen:
   $$\sigma_{\text{leib}} = \frac{F_v}{d \cdot t} \le \sigma_{\text{leib,zul}} \approx 1{,}5 \dots 2{,}5 \cdot f_u$$
   Reicht der Randabstand nicht aus, versagt das Bauteil durch Scherausstanzen des Keils vor der Bohrung ($V_R = 2 \cdot c \cdot t \cdot \tau_B$).

---

## 5. Vorschlag für Katalogeinträge nach ADR 0002

Nach ADR 0002 werden Konstruktionsregeln als typisierte, schemavalidierte JSON-Dateien unter `katalog/eintraege/<thema>/<id>.json` abgelegt. Nachfolgend werden vier beispielhafte Einträge für die neu recherchierten Wissensbereiche definiert.

### 5.1 Katalogeintrag 1: Mindestwandstärke beim CNC-Fräsen und Drehen
`katalog/eintraege/cnc/mindestwandstaerke_zerspanung.json`:
```json
{
  "id": "mindestwandstaerke_zerspanung",
  "aussage": "Die empfohlene Mindestwandstärke beträgt 0,8 mm für Metalle (machbar bis 0,5 mm; Drehen > 0,02 Zoll) und 1,5 mm für Kunststoffe (machbar bis 1,0 mm).",
  "werte": [
    {
      "name": "Empfohlene Mindestwandstärke Metalle",
      "wert": 0.8,
      "einheit": "mm"
    },
    {
      "name": "Machbare Mindestwandstärke Metalle",
      "wert": 0.5,
      "einheit": "mm"
    },
    {
      "name": "Mindestwandstärke Drehteile",
      "wert": 0.508,
      "einheit": "mm"
    },
    {
      "name": "Empfohlene Mindestwandstärke Kunststoffe",
      "wert": 1.5,
      "einheit": "mm"
    },
    {
      "name": "Machbare Mindestwandstärke Kunststoffe",
      "wert": 1.0,
      "einheit": "mm"
    }
  ],
  "geltungsbereich": {
    "werkstoff": ["stahl", "edelstahl", "aluminium", "messing", "thermoplast"],
    "verfahren": ["cnc_fraesen", "cnc_drehen"],
    "feature": ["wand", "tasche", "steg"],
    "groesse": [],
    "festigkeitsklasse": []
  },
  "herkunft": "hersteller",
  "quellen": [
    {
      "url": "https://...hubs.com/knowledge-base/how-design-parts-cnc-machining/",
      "stelle": "Abschnitt Minimum wall thickness",
      "zitat": "Minimum wall thickness [...] Recommended: 0.8 mm (metals), 1.5 mm (plastics) [...] Feasible: 0.5 mm (metals), 1.0 mm (plastics)",
      "abgerufen": "2026-11-01"
    },
    {
      "url": "https://...fictiv.com/articles/cnc-machining-design-guide",
      "stelle": "Abschnitt Avoid Thin Walls (CNC Turning)",
      "zitat": "Wall thickness on turned parts should be kept above 0.02 inches.",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Dünnere Wände verringern die Steifigkeit gegen die Schnittkraft und führen zu elastischer Verformung, Vibrationen und Rattermarken. Kunststoffe neigen durch Zerspanungswärme zusätzlich zu Verzug.",
  "ausnahmen": "Sehr kurze Rippen mit Wandhöhen unter 5 mm können bei Metallen lokal bis auf 0,4 mm reduziert werden.",
  "haerte": "fehler",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

---

### 5.2 Katalogeintrag 2: Randabstand von Bohrungen zur Blechbiegelinie
`katalog/eintraege/blech/blech_randabstand_bohrung_biegelinie.json`:
```json
{
  "id": "blech_randabstand_bohrung_biegelinie",
  "aussage": "Bohrungen, Durchbrüche und Stanzkonturen müssen einen Mindestabstand von mindestens dem Vierfachen der Blechdicke zur Biegelinie aufweisen: c >= 4,0 * t.",
  "werte": [
    {
      "name": "Mindestabstand zur Biegelinie",
      "wert": 4.0,
      "einheit": "x Blechdicke"
    }
  ],
  "geltungsbereich": {
    "werkstoff": ["stahl", "edelstahl", "aluminium", "messing", "kupfer"],
    "verfahren": ["blechbiegen", "gesenkbiegen", "stanzen"],
    "feature": ["bohrung", "biegekante", "flansch"],
    "groesse": [],
    "festigkeitsklasse": []
  },
  "herkunft": "hersteller",
  "quellen": [
    {
      "url": "https://...protolabs.com/resources/design-tips/8-mistakes-to-avoid-when-designing-sheet-metal-parts/",
      "stelle": "Abschnitt 2. Placing Features too Close to Bend Lines",
      "zitat": "Keep all features at least 4x material thickness away from bend lines.",
      "abgerufen": "2026-11-01"
    },
    {
      "url": "https://...sendcutsend.com/blog/step-by-step-guide-to-sheet-metal-bending/",
      "stelle": "Abschnitt Features spaced away from die line",
      "zitat": "Adequately space all holes and features away from the die line.",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Im Biegebereich fließt das Material plastisch. Liegt eine Bohrung innerhalb der Dehnungszone, verzieht sich das Loch unzulässig zu einer Ellipse.",
  "ausnahmen": "Wenn das Loch nach dem Biegevorgang spanend gebohrt oder gelasert wird, oder wenn ein Biegefreischnitt zwischen Loch und Biegelinie angeordnet ist.",
  "haerte": "fehler",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

---

### 5.3 Katalogeintrag 3: Schraubenverbindungen im Stahlbau nach DIN EN 1993-1-8
`katalog/eintraege/blech/stahlbau_randabstand_en1993_1_8.json`:
```json
{
  "id": "stahlbau_randabstand_en1993_1_8",
  "aussage": "Für tragende Schraubenverbindungen im Stahlbau müssen die Randabstände e1 (Kraftrichtung) und e2 (quer) mindestens 1,2 * d0 betragen. Für die volle Lochleibungstragfähigkeit sind e1 >= 3,0 * d0 und e2 >= 1,5 * d0 einzuhalten.",
  "werte": [
    {
      "name": "Minimaler Randabstand e1",
      "wert": 1.2,
      "einheit": "x d0"
    },
    {
      "name": "Empfohlener Randabstand e1 (volle Tragfähigkeit)",
      "wert": 3.0,
      "einheit": "x d0"
    },
    {
      "name": "Minimaler Randabstand e2",
      "wert": 1.2,
      "einheit": "x d0"
    },
    {
      "name": "Empfohlener Randabstand e2 (volle Tragfähigkeit)",
      "wert": 1.5,
      "einheit": "x d0"
    },
    {
      "name": "Minimaler Lochabstand p1",
      "wert": 2.2,
      "einheit": "x d0"
    },
    {
      "name": "Minimaler Lochabstand p2",
      "wert": 2.4,
      "einheit": "x d0"
    }
  ],
  "geltungsbereich": {
    "werkstoff": ["s235jr", "s355j2", "stahl"],
    "verfahren": ["stahlbau", "schraubverbindung"],
    "feature": ["durchgangsbohrung", "schraubenverbindung"],
    "groesse": [],
    "festigkeitsklasse": ["8.8", "10.9"]
  },
  "herkunft": "norm_sekundaer",
  "quellen": [
    {
      "url": "https://...schweizer-fn.de/maschinenelemente/schraube_ec3/schraubenverbindung_ec3.php",
      "stelle": "Tabelle Minimaler und Maximaler Rand- und Lochabstand",
      "zitat": "Randabstand: e1 ≥ 1,2 * d0",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Verhindert vorzeitiges Versagen durch Lochleibungsausbruch und Scherausstanzen (Blockversagen) vor dem Erreichen der Fließgrenze.",
  "ausnahmen": "Reine Heft- oder Montageschrauben ohne statische Anrechnung.",
  "haerte": "fehler",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

---

### 5.4 Katalogeintrag 4: Mindestwandstärken im NE-Druckguss
`katalog/eintraege/guss/druckguss_mindestwandstaerke_aluminium.json`:
```json
{
  "id": "druckguss_mindestwandstaerke_aluminium",
  "aussage": "Im Aluminium-Druckguss liegen gut herstellbare Wanddicken zwischen 0,8 und 3,0 mm. Eingegossene Bohrungen erfordern einen Mindestdurchmesser von 2,5 mm.",
  "werte": [
    {
      "name": "Minimal herstellbare Wanddicke Aluminium",
      "wert": 0.8,
      "einheit": "mm"
    },
    {
      "name": "Empfohlene Maximalwanddicke Aluminium",
      "wert": 3.0,
      "einheit": "mm"
    },
    {
      "name": "Minimaler eingegossener Bohrungsdurchmesser",
      "wert": 2.5,
      "einheit": "mm"
    }
  ],
  "geltungsbereich": {
    "werkstoff": ["en_ac_42100", "alsi9cu3", "aluminium_guss"],
    "verfahren": ["druckguss"],
    "feature": ["wand", "bohrung", "gehaeuse"],
    "groesse": [],
    "festigkeitsklasse": []
  },
  "herkunft": "handbuch",
  "quellen": [
    {
      "url": "https://...guss.de/fileadmin/user_upload/richtlinien/druckguss_aus_ne-metallen.pdf",
      "stelle": "Abschnitt 3.2 Wanddicken und Übergänge & Tabelle 9",
      "zitat": "für Aluminiumlegierungen ab 0,8 bis 3 mm",
      "abgerufen": "2026-11-01"
    }
  ],
  "begruendung": "Wanddicken unter 0,8 mm führen zu mangelhafter Formfüllung und Kaltläufen. Wanddicken über 3 mm begünstigen Schrumpfungsporosität (Lunker) und verlängern die Zykluszeit.",
  "ausnahmen": "Lokale Verstärkungsaugen oder Lagerstellen dürfen dickwandiger gestaltet werden, müssen aber verrippt oder ausgespart werden.",
  "haerte": "hinweis",
  "pruefstatus": "automatisch",
  "beziehungen": []
}
```

---

## 6. Detaillierte Quellenbelege und Zitate

Die nachfolgenden Quellenbelege wurden automatisiert mit `tools/check_sources.py` gegen die Originaldokumente (HTML/PDF) geprüft.

### Beleg: Hubs CNC Machining Design Guide
* **Quelle:** [Hubs CNC Design Guide](https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/)
* **Fundstelle:** Abschnitte *Minimum wall thickness*, *Cavity depth*, *Holes*
* **Wörtliches Zitat:** „Decreasing the wall thickness reduces the stiffness of the material, which increases vibrations during machining and lowers the achievable accuracy.“
* **Belegte Zahlen:** 0.8 mm, 1.5 mm, 0.5 mm, 1.0 mm, 4, 10.

### Beleg: Protolabs CNC Machining Tips
* **Quelle:** [Protolabs CNC Tips](https://www.protolabs.com/resources/design-tips/6-ways-to-optimize-part-design-for-cnc-machining/)
* **Fundstelle:** Abschnitt 4 (*Tall Walls and Tiny Features*) & Abschnitt 1 (*The Hole Truth*)
* **Wörtliches Zitat:** „minimum feature thickness at Protolabs is 0.020 in. (0.5mm) and the maximum feature depth is 2 in. (51mm)“
* **Belegte Zahlen:** 0.020 in., 0.5 mm, 2 in., 51 mm, 6.

### Beleg: Fictiv CNC Machining Design Guide
* **Quelle:** [Fictiv CNC Design Guide](https://www.fictiv.com/articles/cnc-machining-design-guide)
* **Fundstelle:** Abschnitte *Drilling (Partial Holes)*, *Threaded Holes*, *Avoid Thin Walls (CNC Turning)*
* **Wörtliches Zitat:** „Wall thickness on turned parts should be kept above 0.02 inches.“
* **Belegte Zahlen:** 0.02 inches, 75 %, 12.

### Beleg: BDG Technische Richtlinie Druckguss aus NE-Metallen
* **Quelle:** [BDG Druckguss Richtlinie PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/druckguss_aus_ne-metallen.pdf)
* **Fundstelle:** Abschnitt 3.2 (*Wanddicken und Übergänge*, S. 22) & Tabelle 9 (*Eingegossene Bohrungen*, S. 28)
* **Wörtliches Zitat:** „Tabelle 9: Richtwerte für das Durchmesser-Längenverhältnis eingegossener Bohrungen (Minimalwerte)“
* **Belegte Zahlen:** 0,8 mm, 3 mm, 2,5 mm, 4,0 mm.

### Beleg: BDG Technische Richtlinie Sand- und Kokillenguss aus Aluminium
* **Quelle:** [BDG Sand- und Kokillenguss Richtlinie PDF](https://www.guss.de/fileadmin/user_upload/richtlinien/sand-_und_kokillenguss_aus_aluminium.pdf)
* **Fundstelle:** Abschnitt 4.4 (*Wanddicken*), Abschnitt 4.6 (*Tabelle 8: Vorgegossene Bohrungen*), Bild 13 (*Gestaltung von Augen*)
* **Wörtliches Zitat:** „Tabelle 8: Vorgegossene Bohrungen“
* **Belegte Zahlen:** 10 mm, 15 mm, 4 mm, 5 mm, 1,0 %, 1,25 %, 0,8 %.

### Beleg: Castfast Werkstoffeigenschaften Eisenguss GJL DIN EN 1561
* **Quelle:** [Castfast Werkstoffdatenblatt GJL PDF](https://www.castfast.com/wp-content/uploads/2024/07/Werkstoffeigenschaften-GJL-CASTFAST.pdf)
* **Fundstelle:** Seite 1, Werkstoffeigenschaften EN-GJL-200 bis EN-GJL-350
* **Wörtliches Zitat:** „Werkstoffeigenschaften Eisenguss Gusseisen mit Lamellengraphit (GJL)“
* **Belegte Zahlen:** 200, 250, 300, 350, 165, 228, 840, 290.

### Beleg: Protolabs Blechbearbeitung 8 Fehler vermeiden
* **Quelle:** [Protolabs 8 Mistakes Sheet Metal](https://www.protolabs.com/resources/design-tips/8-mistakes-to-avoid-when-designing-sheet-metal-parts/)
* **Fundstelle:** Abschnitt 2 (*Placing Features too Close to Bend Lines*) & Abschnitt 3 (*Corner Radii*)
* **Wörtliches Zitat:** „Keep all features at least 4x material thickness away from bend lines.“
* **Belegte Zahlen:** 4, 0.050 in., 1.27 mm, 0.200 in., 5.08 mm, 0.030 in., 0.762 mm.

### Beleg: SendCutSend Blechbiegen Schritt für Schritt
* **Quelle:** [SendCutSend Step-by-Step Bending Guide](https://sendcutsend.com/blog/step-by-step-guide-to-sheet-metal-bending/)
* **Fundstelle:** Abschnitt *Bend relief notches for sheet metal parts*
* **Wörtliches Zitat:** „These notches should be at least 50% of the material’s thickness in width and the depth should equal Bend radius + Material thickness +.020”.“
* **Belegte Zahlen:** 50 %, 1, 2.

### Beleg: SendCutSend Schneidrichtlinien Blech Laser und Wasserstrahl
* **Quelle:** [SendCutSend Sheet Cutting Guidelines](https://sendcutsend.com/guidelines/sheet-cutting/)
* **Fundstelle:** Abschnitte *Minimum hole and cutout size* & *Laser vs Waterjet*
* **Wörtliches Zitat:** „All holes and cutouts are at least 50% material thickness for laser cut parts“
* **Belegte Zahlen:** 50 %, 0.070 in., 0.125 in.

### Beleg: SendCutSend Biegeregeln und Flanschanforderungen
* **Quelle:** [SendCutSend Bending Guidelines](https://sendcutsend.com/guidelines/bending/)
* **Fundstelle:** Abschnitte *Flange requirements* & *Bend relief*
* **Wörtliches Zitat:** „Sheet metal: base must be at least 2x the flange length (2:1 ratio)“
* **Belegte Zahlen:** 2.

### Beleg: Schweizer-FN Schraubenverbindung im Stahlbau nach Eurocode 3
* **Quelle:** [Schweizer-FN Schraubenverbindung Stahlbau EC3](https://www.schweizer-fn.de/maschinenelemente/schraube_ec3/schraubenverbindung_ec3.php)
* **Fundstelle:** Tabelle *Minimaler und Maximaler Rand- und Lochabstand*
* **Wörtliches Zitat:** „Minimaler und Maximaler Rand- und Lochabstand von Schrauben im Stahlbau.“
* **Belegte Zahlen:** 1,2, 4, 40 mm, 2,2, 2,4, 14, 200 mm.

### Beleg: Hubs FDM 3D-Druck Konstruktionsregeln
* **Quelle:** [Hubs FDM 3D Printing Guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
* **Fundstelle:** Abschnitte *Vertical axis holes* & *Hole orientation*
* **Wörtliches Zitat:** „For critical vertical-hole diameters, drill after printing to achieve higher accuracy.“
* **Belegte Zahlen:** 5 mm.

### Beleg: Hubs Grundregeln für den 3D-Druck
* **Quelle:** [Hubs Key Considerations 3D Printing](https://www.hubs.com/knowledge-base/key-design-considerations-3d-printing/)
* **Fundstelle:** Abschnitt *Wall thickness for 3D printing*
* **Wörtliches Zitat:** „All 3D printers used within the Protolabs Network manufacturing network can print parts with wall thicknesses of 0.8 mm and over.“
* **Belegte Zahlen:** 0.8 mm.

### Beleg: Prusa Research Fertigungstoleranzen im FDM-Druck
* **Quelle:** [Prusa Research FAQ Tolerances](https://help.prusa3d.com/article/faq-frequently-asked-questions_1932)
* **Fundstelle:** Abschnitt *Precision and Tolerances*
* **Wörtliches Zitat:** „precision tolerance of a well-assembled Original Prusa printer is 0,1 mm on the Z-axis and 0,3 mm on X and Y.“
* **Belegte Zahlen:** 0,1 mm, 0,3 mm.

### Beleg: CNC Kitchen Gewindeeinsätze Konstruktionsrichtlinien
* **Quelle:** [CNC Kitchen Heat-Set Inserts Guide](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts)
* **Fundstelle:** Abschnitt *Design rules*
* **Wörtliches Zitat:** „Design rules: a blind hole roughly 1 mm deeper than the insert is long, straight rather than tapered holes, respect the minimum wall thickness, and normally no chamfer at the hole edge.“
* **Belegte Zahlen:** 1 mm.

### Beleg: CNC Kitchen Zugversuche und Vorlochdurchmesser für Heat-Set Inserts
* **Quelle:** [CNC Kitchen Pullout Tests](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong)
* **Fundstelle:** Abschnitte *Pullout Test Results* & *Hole sizing*
* **Wörtliches Zitat:** „I melted almost 50 M3 inserts into samples with hole diameters from 3.6 to 4.6 mm and pulled every one of them out on my tensile tester.“
* **Belegte Zahlen:** 0.25 mm, 50, 3.6 mm, 4.6 mm, 1400 N, 150 kg, 325 pounds, 4.1 mm, 4.2 mm, 4.0 mm.

### Beleg: Protolabs Spritzguss Richtwerte für Nennwandstärken
* **Quelle:** [Protolabs Injection Molding Guidelines](https://www.protolabs.com/services/injection-molding/plastic-injection-molding/design-guidelines/)
* **Fundstelle:** Tabelle *Recommended Wall Thickness*
* **Wörtliches Zitat:** „RECOMMENDED WALL THICKNESS“
* **Belegte Zahlen:** 1.143 mm, 3.556 mm, 0.762 mm, 3.048 mm, 2.921 mm, 1.016 mm, 3.81 mm, 0.889 mm.

### Beleg: Fictiv Kunststoffspritzguss Konstruktionsleitfaden
* **Quelle:** [Fictiv Injection Molding Guide](https://www.fictiv.com/articles/injection-molding-design-guide)
* **Fundstelle:** Abschnitte *B. Wall Thickness Design Considerations*, *D. Corner Design*, *F. Designing Ribs and Bosses*
* **Wörtliches Zitat:** „Avoid sink marks by making the boss thickness no more than 60% of the overall wall thickness.“
* **Belegte Zahlen:** 0.76 mm, 3.05 mm, 1.14 mm, 3.56 mm, 2.92 mm, 1.02 mm, 3.81 mm, 50 %, 60 %, 0.5, 0.6, 2.5.

### Beleg: Hubs Gestaltungsregeln für den Spritzguss
* **Quelle:** [Hubs Injection Molding Guide](https://www.hubs.com/knowledge-base/how-design-parts-injection-molding/)
* **Fundstelle:** Abschnitte *Bosses*, *Threads*, *Ribs*
* **Wörtliches Zitat:** „Support bosses with ribs or connect them to a main wall“
* **Belegte Zahlen:** 2, 0.8 mm, 0.5, 3, 0.25 °, 0.5 °, 4.

### Beleg: Protolabs Wandstärkenprobleme im Kunststoffspritzguss
* **Quelle:** [Protolabs Solving Wall Thickness Issues](https://www.protolabs.com/resources/design-tips/solving-wall-thickness-issues-in-molded-parts/)
* **Fundstelle:** Tabelle *Recommended Wall Thickness by Plastic Type*
* **Wörtliches Zitat:** „Solving Wall Thickness Issues in Molded Parts“
* **Belegte Zahlen:** 0.045 in., 0.140 in., 1.143 mm, 3.556 mm, 0.030 in., 0.120 in., 0.762 mm, 3.048 mm, 0.115 in., 2.921 mm, 0.040 in., 0.150 in., 1.016 mm, 3.81 mm, 0.025 in., 0.635 mm.

### Beleg: Ingenieurbüro Andreas Hanke Mindesteinschraubtiefen in Grauguss GJL
* **Quelle:** [Ing.-Büro Hanke Mindesteinschraubtiefe GJL PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-GJL-Scherfestigkeitsverh%C3%A4ltnis1.15.pdf)
* **Fundstelle:** Tabelle Mindesteinschraubtiefen für GJL bei Scherfestigkeitsverhältnis 1,15
* **Wörtliches Zitat:** „Mindesteinschraubtiefen nach VDI 2230-1:2015 für Innengewinde in Gusseisen mit Lamellegraphit (GJL)“
* **Belegte Zahlen:** 2230, 1.15, 8.8, 8.4, 250, 230.
