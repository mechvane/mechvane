> **Prüfnotiz (Claude, 2026-11-05):** Rohfassung von Gemini Flash (#29). `check_sources.py`: alle Belege mit HTTP 200 gefunden, Zitate und Zahlen vollständig. Keine eigene Stichprobe an den Normtabellen; vor Übernahme in Normteile oder Katalog Werte an der Primärquelle prüfen.

> Gemini-3.8-Flash-Rohfassung mit Web, verifiziert mit `tools/check_sources.py`. Recherche 2026-11-01. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Aluminium-Nutprofile (20/30/40/80) und Verbindungstechnik für den Gestell-Generator

- **Datum:** 2026-11-01
- **Status:** Gemini 3.8 Flash, quellenverifiziert mit `tools/check_sources.py`
- **Bezug:** Issue #29 (Maßgrundlage für den Gestell-Generator / Frame Generator auf Basis stranggepresster Aluminium-Strebenprofile mit T-Nut)
- **Autor:** Antigravity (Gemini 3.8 Flash)

---

## 1. Ausgangslage und Motivation

In modernen Konstruktions- und CAD-Systemen (wie Autodesk Inventor Frame Generator, SolidWorks Weldments oder PTC Creo Advanced Framework) stellt der **Gestell-Generator** ein zentrales Produktivitätswerkzeug für den Maschinen-, Vorrichtungs- und Betriebsmittelbau dar. Anstatt jedes einzelne Träger- oder Strebenprofil manuell als Einzelteil mit Skizze, Austragung, Gehrungsschnitt und Bohrungen zu modellieren, arbeitet ein Gestell-Generator auf Basis eines **räumlichen Drahtgittermodells (3D-Wireframe)**:

1. Der Konstrukteur definiert ein 3D-Skelett aus Linien und Kanten (z. B. Kanten eines Referenzquaders oder einer 3D-Skizze).
2. Der Generator extrudiert entlang jeder Kante automatisch das gewünschte Profil aus einer parametrischen Querschnittsbibliothek.
3. An den Knotenkanten schneidet der Generator automatische Gehrungen (*Miter Cuts*) oder Stoßüberstände (*Butt Joints*).
4. Verbinder (Winkel, Nutensteine, Stirn- oder Bolzenverbinder) werden mitsamt den erforderlichen Bohrungen im Profilkörper semantisch platziert.

Gemäß der Mechvane-Roadmap (Meilenstein *Gestell-Generator*) soll SolidCraft um ein solches Modul erweitert werden. Im Gegensatz zum klassischen Stahlbau (mit genormten IPE-, HEB- oder Rechteckrohr-Profilen nach EN 10210/10219) dominiert im industriellen Automatisierungs-, Betriebsmittel- und Vorrichtungsbau das **Aluminium-Strebenprofil mit T-Nut**.

Auf dem Markt haben sich zwei dominierende Basissysteme sowie deren Handelsderivate etabliert:
* **System item (item MB Systembaukasten, „I-Typ“):** Entwickelt von Gerrit Pies und Wolfgang Rixen (Solingen, 1980er Jahre). Charakteristisch sind parallele Nutflanken, eine definierte Vorspannung der Nutlippen (konkave Wölbung um ca. 0,2 mm zur Schwingungssicherheit gegen Schraubenlockern) und die Rastermaße 20 (Nut 5), 30 (Nut 6), 40 (Nut 8) sowie 50 (Nut 10).
* **System Bosch Rexroth (Mechanik-Grundelemente MGE, „B-Typ“):** Entwickelt für modulare Montagetechnik und Transfersysteme. Charakteristisch sind leicht konische Nutflanken (ca. 15° Neigung zum Nutgrund, die ein selbstzentrierendes Festklemmen der Hammermuttern bewirken) und eine abweichende Raster-zu-Nut-Zuordnung: Raster 20 (Nut 6), Raster 30 (Nut 8), Raster 40/45 (Nut 10).
* **Handelsübliche Profile (Motedis, Dold Mechatronik, Misumi u. a.):** Im Handel und Open-Source-Hardwarebereich (3D-Drucker wie Voron, CNC-Fräsen wie PrintNC, Prüfstandsgestelle) werden stranggepresste Profile üblicherweise direkt nach diesen beiden Systemen als **I-Typ** oder **B-Typ** kategorisiert und vertrieben.

Ziel dieser Recherche ist die Schaffung einer verlässlichen, quellengestützten Datengrundlage aller geometrischen und mechanischen Profilwerte (Raster 20, 30, 40 und 40×80), der Verbindungselemente und Bohrbilder, der Klärung der gegenseitigen Kompatibilität, einer juristischen Absicherung der CAD-Nutzungsrechte sowie eines konkreten Schemavorschlags für die parametrische Profilskizze in Mechvane.

---

## 2. Geometrische und mechanische Kennwerte der Profile

Alle Angaben basieren auf den technischen Datenblättern und Gesamtkatalogen industrieller Systemprofil-Hersteller und Fachhändler (u. a. Dold Mechatronik Gesamtkatalog 2026_01_29, Motedis).

### 2.1 System I-Typ (item-kompatibel: Nut 5, Nut 6, Nut 8, Nut 10)

Die Nutbreite $w$ bei I-Typ-Profilen steigt strikt mit der Baureihennummer: Baureihe 5 besitzt Nut 5 mm, Baureihe 6 Nut 6,2 mm, Baureihe 8 Nut 8 mm und Baureihe 10 Nut 10 mm.

| Profilbezeichnung | Außenmaß [mm] | Nut | Nutbreite $w$ [mm] | Nuttiefe $t$ [mm] | Hinterschnitt $w_i$ [mm] | Lippe $t_l$ [mm] | Kernbohrung $\varnothing$ [mm] | Gewinde Kern | Fläche $A$ [mm²] | Metergewicht [kg/m] | $I_x$ [cm⁴] | $I_y$ [cm⁴] | $W_x$ [cm³] | $W_y$ [cm³] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **20×20L I-Typ Nut 5** | 20 × 20 | 5 | 5,0 (+0,3) | 6,35 | 11,5 | 1,8 | 4,3 (±0,1) | M5 | 181,9 | ca. 0,493 | 0,75 | 0,75 | 0,75 | 0,75 |
| **20×40L I-Typ Nut 5** | 20 × 40 | 5 | 5,0 (+0,3) | 6,35 | 11,5 | 1,8 | 2× 4,3 (±0,1) | M5 | 328,0 | ca. 0,890 | 1,42 | 5,23 | 1,42 | 2,62 |
| **30×30L I-Typ Nut 6** | 30 × 30 | 6 | 6,2 (+0,3) | 9,0 | 16,3 | 6,75 | 5,0 (+0,2) | M6 | 346,8 | ca. 0,940 | 2,95 | 2,95 | 1,97 | 1,97 |
| **40×40L I-Typ Nut 8 (leicht)** | 40 × 40 | 8 | 8,0 (+0,4) | 12,0 | 20,0 | 7,6 | 6,8 (−0,2) | M8 | 648,9 | ca. 1,759 | 9,06 | 9,06 | 4,53 | 4,53 |
| **40×40S I-Typ Nut 8 (schwer)** | 40 × 40 | 8 | 8,0 (+0,4) | 12,0 | 20,0 | 7,6 | 6,8 (−0,2) | M8 | 925,4 | ca. 2,508 | 14,11 | 14,11 | 7,06 | 7,06 |
| **40×80L I-Typ Nut 8 (leicht)** | 40 × 80 | 8 | 8,0 (+0,4) | 12,0 | 20,0 | 7,6 | 2× 6,8 (−0,2) | M8 | 1156,1 | ca. 3,133 | 17,14 | 70,04 | 8,57 | 17,51 |
| **40×80S I-Typ Nut 8 (schwer)** | 40 × 80 | 8 | 8,0 (+0,4) | 12,0 | 20,0 | 7,6 | 2× 6,8 (−0,2) | M8 | 1677,8 | ca. 4,547 | 27,02 | 102,09 | 13,51 | 25,52 |
| **50×50L I-Typ Nut 10** | 50 × 50 | 10 | 10,2 (+0,4) | 15,5 | 24,5 | 10,2 | 8,5 (±0,2) | M10 | 1084,0 | ca. 2,940 | 26,50 | 26,50 | 10,60 | 10,60 |

*Besonderheit der I-Typ-Geometrie:* Die Nutlippen sind mit einer elastischen Vorspannung von 0,2 mm (+0,1 / -0,15 mm) versehen. Beim Festziehen einer Schraubverbindung wird die Nutlippe elastisch plan gezogen, wodurch eine permanente Federwirkung entsteht, die ein Lösen der Verbindung unter dynamischer Schwingbelastung wirksam verhindert.

---

### 2.2 System B-Typ (Bosch-Rexroth-kompatibel: Nut 6, Nut 8, Nut 10)

Beim B-Typ korrespondiert die Nutbreite nicht mit der Baureihennummer, sondern ist im Verhältnis zum Außenmaß größer als beim I-Typ (20er Raster hat bereits Nut 6, 30er Raster Nut 8, 40er Raster Nut 10).

| Profilbezeichnung | Außenmaß [mm] | Nut | Nutbreite $w$ [mm] | Nuttiefe $t$ [mm] | Hinterschnitt $w_i$ [mm] | Lippe $t_l$ [mm] | Kernbohrung $\varnothing$ [mm] | Gewinde Kern | Fläche $A$ [mm²] | Metergewicht [kg/m] | $I_x$ [cm⁴] | $I_y$ [cm⁴] | $W_x$ [cm³] | $W_y$ [cm³] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **20×20L B-Typ Nut 6** | 20 × 20 | 6 | 6,0 (+0,3) | 5,5 | 12,1 | 1,5 | 5,5 (+0,2/−0,1) | M6 (Direkt/S6) | 162,1 | ca. 0,439 | 0,67 | 0,67 | 0,67 | 0,67 |
| **20×40L B-Typ Nut 6** | 20 × 40 | 6 | 6,0 (+0,3) | 5,5 | 12,1 | 1,5 | 2× 5,5 (+0,2/−0,1) | M6 (Direkt/S6) | 296,0 | ca. 0,802 | 1,25 | 4,60 | 1,25 | 2,30 |
| **30×30L B-Typ Nut 8** | 30 × 30 | 8 | 8,0 (+0,3) | 9,0 | 16,7 | 2,2 | 6,8 (−0,2) / 7,3 | M8 / Verbinder | 311,0 | ca. 0,843 | 2,68 | 2,68 | 1,79 | 1,79 |
| **40×40L B-Typ Nut 10** | 40 × 40 | 10 | 10,0 (+0,4) | 12,0 | 20,1 | 6,0 | 10,0 (±0,15) | M12 / Hülse M8 | 554,1 | ca. 1,502 | 9,04 | 9,04 | 4,52 | 4,52 |
| **40×80L B-Typ Nut 10** | 40 × 80 | 10 | 10,0 (+0,4) | 12,0 | 20,1 | 6,0 | 2× 10,0 (±0,15) | M12 / Hülse M8 | 972,4 | ca. 2,635 | 17,19 | 62,63 | 8,60 | 15,66 |
| **45×45L B-Typ Nut 10** | 45 × 45 | 10 | 10,0 (+0,4) | 12,0 | 20,1 | 6,0 | 10,0 (±0,15) | M12 / Hülse M8 | 682,0 | ca. 1,850 | 14,00 | 14,00 | 6,20 | 6,20 |
| **45×90L B-Typ Nut 10** | 45 × 90 | 10 | 10,0 (+0,4) | 12,0 | 20,1 | 6,0 | 2× 10,0 (±0,15) | M12 / Hülse M8 | 1215,0 | ca. 3,300 | 27,00 | 102,00 | 12,00 | 22,70 |

*Besonderheit der B-Typ-Geometrie:* Die Kernbohrung bei 40er- und 45er-Profilen mit Nut 10 misst $\varnothing 10{,}0\text{ mm}$. Diese Bohrung ist direkt für metrisches Regelgewinde M12 (Kernlochmaß für M12 ist $10{,}2\text{ mm}$) ausgelegt oder nimmt selbstformende Schrauben (S12) bzw. Gewindereduzierhülsen von M12 auf M8 auf. Für Direktverschraubungen mit M8 muss beim B-Typ eine Gewindehülse eingedreht werden.

---

### 2.3 Werkstoffkennwerte und Fertigungstoleranzen

Standard-Strebenprofile werden aus aushärtbaren Aluminium-Knetlegierungen im Strangpressverfahren (Extrusion) hergestellt:
* **Werkstoff:** EN AW-6063 T66 (AlMg0,7Si nach DIN EN 573-3 und DIN EN 515) bzw. EN AW-6060 T6 (AlMgSi0,5).
* **Dehngrenze:** $R_{p0{,}2} \ge 200\,\text{N/mm}^2$.
* **Zugfestigkeit:** $R_m \ge 245\,\text{N/mm}^2$.
* **Bruchdehnung:** $A \ge 8\,\%$ (bzw. $A_{50} \ge 6\,\%$).
* **Brinellhärte:** $\ge 80\,\text{HBW}$.
* **Elastizitätsmodul:** $E \approx 70\,000\,\text{N/mm}^2$, Schubmodul $G \approx 27\,000\,\text{N/mm}^2$.
* **Oberfläche:** Hochwertig eloxiert nach E6/EV1 (chemisch matt gebeizt und naturfarben eloxiert) mit einer Schichtdicke von $10 \dots 15\,\mu\text{m}$. Eloxal-Schichthärte ca. $250 \dots 350\,\text{HV}$, bietet hervorragenden Korrosions- und Kratzschutz.
* **Maßtoleranzen:** Präzisions-Strangpressprofile nach DIN EN 12020-2 (Feintoleranzen für Aluminium-Präzisionsprofile).

---

## 3. Verbindungstechnik, Zubehör und Profilbearbeitungen (Bohrbilder)

Die Verbindungstechnik entscheidet maßgeblich über die statische Steifigkeit, Montagezeit und die erforderlichen spanenden Bearbeitungsschritte (Bohren, Fräsen, Gewindeschneiden).

### 3.1 Standard-Winkel (Druckgusswinkel)

Druckgusswinkel (Aluminium- oder Zinkdruckguss) sind die am weitesten verbreitete kraft- und formschlüssige Verbindung für $90^\circ$-Eckverbindungen.
* **Geometrie & Schenkellängen:**
  * **Winkel 20 (für Raster 20, Nut 5/6):** Schenkelmaße $20 \times 20\text{ mm}$, Schenkelbreite ca. $18 \dots 20\text{ mm}$. Durchgangsbohrungen passend für M4- oder M5-Schrauben.
  * **Winkel 30 (für Raster 30, Nut 8/6):** Schenkelmaße $30 \times 30\text{ mm}$, Schenkelbreite ca. $28 \dots 30\text{ mm}$. Bohrungen passend für M6-Schrauben (z. B. Flachkopfschraube DIN 7984 M6×12).
  * **Winkel 40 (für Raster 40, Nut 8/10):** Schenkelmaße $40 \times 40\text{ mm}$ (bzw. Doppelwinkel $40 \times 80\text{ mm}$), Schenkelbreite ca. $36 \dots 40\text{ mm}$. Bohrungen passend für M8-Schrauben (z. B. Flachrundschraube ISO 7380 M8×16).
* **Zentriernasen (Führungsstege):**
  * An den Unterseiten der Schenkel sitzen gegossene Führungsstege, die spielfrei in die Profilnut eingreifen.
  * Sie ermöglichen eine schnelle, exakte und verdrehgesicherte Ausrichtung parallel zur Nutachse.
  * *Sollbruchstelle:* Bei einer Quermontage (Montage quer zur Nut, z. B. auf Flächenelementen oder versetzten Profilen) können die Zentriernasen einfach mit einem Schraubendreher oder einer Zange abgebrochen werden.
* **Vorteil für den Gestell-Generator:** Keine mechanische Profilbearbeitung erforderlich; Profile müssen lediglich rechtwinklig auf Länge gesägt werden.

---

### 3.2 Nutensteine, Hammermuttern und Zubehör

In die T-Nuten eingeschobene oder eingeschwenkte Muttern stellen das Innengewinde für Schrauben bereit.

1. **Nutenstein mit Steg und Kugel (Standard-Nutenstein):**
   * Wird stirnseitig in die Profilnut eingeschoben.
   * Ein federbelastetes Stahlkügelchen auf der Rückseite drückt den Nutenstein leicht gegen die Nutlippen und verhindert ein Verrutschen bei vertikaler Montage.
   * Der Führungssteg zentriert das Gewinde exakt in der Nutöffnung und nimmt Querkräfte auf.
   * *Abmessungen:*
     * Nut 5: $7{,}7 \times 4{,}65 \times 12\text{ mm}$ (Gewinde M3, M4, M5).
     * Nut 8 (I-Typ): $13{,}5 \times 7{,}2 \times 22\text{ mm}$ (Gewinde M4, M5, M6, M8).
     * Nut 8 (B-Typ): $11{,}8 \times 4{,}8 \times 16\text{ mm}$ bzw. schwer $16 \times 6 \times 16\text{ mm}$ (Gewinde M4, M5, M6, M8).
     * Nut 10 (B-Typ): $13{,}8 \times 5{,}3 \times 20\text{ mm}$ bzw. schwer $19{,}6 \times 10{,}5 \times 20\text{ mm}$ (Gewinde M4, M5, M6, M8).
2. **Einschwenk-Nutensteine (Rhombus-Nutenstein / 45°-Nutenstein):**
   * Besitzen parallelogrammförmige oder abgeschrägte Ecken ($45^\circ$) und ein rückseitiges Federblech.
   * Können an jeder beliebigen Stelle nachträglich von vorne in die geschlossene Nut eingedrückt und um $90^\circ$ gedreht werden.
   * Unverzichtbar für nachträgliche Erweiterungen an bereits montierten Gestellen.
3. **Hammermuttern:**
   * Kostengünstige Stanz- oder Drehteile mit schmalem Kopf (z. B. $7{,}7 \times 6 \times 16\text{ mm}$ bei B-Typ Nut 8 oder $9{,}7 \times 8{,}8 \times 19\text{ mm}$ bei B-Typ Nut 10).
   * Drehen sich beim Festziehen der Schraube automatisch um $90^\circ$ quer in den Hinterschnitt der Nut.

---

### 3.3 Stirn- und Längsverbinder: Typen und erforderliche Bohrbilder

Für geschlossene, saubere Rahmenkonstruktionen ohne störende Innenwinkel kommen innenliegende Verbinder zum Einsatz. Diese erfordern definierte mechanische Vorbearbeitungen:

#### A. Direktverschraubung / Stirnverbinder (Standard-Stirnverschraubung)
* **Funktionsprinzip:** Profil 1 stößt stumpf auf die Längsseite von Profil 2. In die Kernbohrung von Profil 1 wird stirnseitig ein metrisches Regelgewinde geschnitten:
  * Nut 5 (Kern $\varnothing 4{,}3\text{ mm}$): Gewinde **M5**, Gewindetiefe $\ge 15\text{ mm}$.
  * Nut 6 I-Typ (Kern $\varnothing 5{,}0\text{ mm}$): Gewinde **M6**, Gewindetiefe $\ge 18\text{ mm}$.
  * Nut 8 I-Typ / B-Typ (Kern $\varnothing 6{,}8\text{ mm}$): Gewinde **M8**, Gewindetiefe $\ge 25\text{ mm}$.
  * Nut 10 B-Typ (Kern $\varnothing 10{,}0\text{ mm}$): Gewinde **M12** (bzw. Gewindehülse M12 $\rightarrow$ M8).
* **Bohrbild in Profil 2:** Durchgangsbohrung quer durch die Profilnut auf Höhe der Kernbohrung:
  * Für M8: Durchgangsbohrung $\varnothing 9{,}0\text{ mm}$.
  * Auf der gegenüberliegenden Profilseite: Stufenbohrung / Zugangsbohrung $\varnothing 15{,}0\text{ mm}$ zum Versenken des Zylinderkopfes (DIN 912) und Einführen des Inbusschlüssels.

#### B. Standard-Verbindungssatz (item MB-Prinzip)
* **Funktionsprinzip:** Ein massives Verbindungsblech ($35 \times 17\text{ mm}$, Dicke $10\text{ mm}$) sitzt formschlüssig in den Nuten beider Profile.
* **Profilbearbeitung:**
  * Profil 1 (Stirnseite): Kernbohrung mit Gewinde M8 versehen.
  * Profil 2 (Querprofil): Querbohrung $\varnothing 9{,}0\text{ mm}$ im Abstand $L = 20\text{ mm}$ von der Stirnkante.
* **Befestigung:** Eine Flachrundschraube ISO 7380 M8×18 klemmt das Verbindungsblech spielfrei und hochfest fest.

#### C. Zentralverbinder / Schnellspannverbinder (Bosch Rexroth-Prinzip)
* **Funktionsprinzip:** Ein zylindrischer Spannbolzen wird stirnseitig in die Kernbohrung eingeschraubt. Im Querprofil greift eine Querbohrung / Stufenbohrung den Bolzenkopf ab.
* **Bohrbild (Stufenbohrung nach Rexroth-Norm DB11 / DB17):**
  * **Abstand von der Profilstirnkante:** $L = 22{,}5\text{ mm}$ (Standardmaß für Nut-10-Profile im 40er/45er Raster) bzw. $19{,}5 \dots 22{,}5\text{ mm}$ bei Nut 8.
  * **Großer Durchmesser $D_1$:** $\varnothing 17\text{ mm}$ (Zugang für Schraubenkopf / Werkzeug) bzw. $\varnothing 11\text{ mm}$ bei Nut 8.
  * **Kleiner Durchmesser $D_2$:** $\varnothing 11\text{ mm}$ (Durchgang für Spannhülse/Zugbolzen) bzw. $\varnothing 9\text{ mm}$ bei Nut 8.

#### D. Automatik-Verbinder (Spanlose Schnellverbindung)
* **Funktionsprinzip:** Eine Schneidhülse mit speziellem Außengewinde (Linksgewinde) wird mit einem Torx-Bit (TX40) direkt von der Stirnseite in den Nutgrund des Profils eingedreht.
* **Vorteil:** **Keinerlei Profilbearbeitung erforderlich!** Kein Bohren, kein Gewindeschneiden. Das Profil muss lediglich rechtwinklig abgelängt werden.
* **Montage:** Durch die Hülse wird eine Zylinderschraube DIN 912 M6×40 geführt und in eine Hammermutter oder einen Nutenstein des quer anstoßenden Profils geschraubt. Durch das Linksgewinde der Hülse spannt sich diese beim Rechtsanzug der Schraube selbsthemmend fest.

---

## 4. Kompatibilität und Unterschiede zwischen den Systemen

Eine der häufigsten Fehlerquellen bei Konstruktion und Beschaffung ist die Annahme, Aluminiumprofile gleicher Außenabmessung seien untereinander kompatibel.

### 4.1 Gegenüberstellung Raster vs. Nutbreite

| Rastermaß | System item (I-Typ) | System Bosch Rexroth (B-Typ) | Auswirkung auf Kompatibilität |
| :---: | :---: | :---: | :--- |
| **Raster 20** | **Nut 5** ($w = 5{,}0\text{ mm}$) | **Nut 6** ($w = 6{,}0\text{ mm}$) | **Inkompatibel:** Verbinder und Nutensteine für B-Typ Nut 6 fallen durch oder passen nicht in I-Typ Nut 5. |
| **Raster 30** | **Nut 6** ($w = 6{,}2\text{ mm}$) | **Nut 8** ($w = 8{,}0\text{ mm}$) | **Inkompatibel:** Grundlegender Unterschied! B-Typ 30 hat Nut 8 (M8-Schrauben möglich), I-Typ 30 hat Nut 6 (nur bis M6). |
| **Raster 40** | **Nut 8** ($w = 8{,}0\text{ mm}$) | **Nut 10** ($w = 10{,}0\text{ mm}$) | **Inkompatibel:** Standard B-Typ 40 nutzt Nut 10; I-Typ 40 nutzt Nut 8. M8-Nutensteine aus I-Typ kippen in B-Typ Nut 10 ab. |
| **Raster 45** | Nicht im Kernsortiment | **Nut 10** ($w = 10{,}0\text{ mm}$) | Klassisches Bosch-Rexroth-Stammraster. |

### 4.2 Geometrische Details der Nutkontur

1. **Flankenform:**
   * **I-Typ:** Rechtwinklige, exakt parallele Flanken mit ausgeprägtem Hinterschnitt. Die Nutlippen sind flach mit konkavem Spannwinkel. Nutensteine sitzen formschlüssig flach auf.
   * **B-Typ:** Konische Flanken (Trapezform). Die Nutinnenseite verjüngt sich leicht. Hammermuttern sind an den Ecken gerundet, gleiten an der Schräge ab und klemmen sich formschlüssig fest.
2. **Kernbohrung:**
   * Beim I-Typ 40×40 misst die Kernbohrung $\varnothing 6{,}8\text{ mm}$, perfekt für M8-Regelgewinde.
   * Beim B-Typ 40×40 misst die Kernbohrung $\varnothing 10{,}0\text{ mm}$. Ein M8-Gewindebohrer greift ins Leere! Es muss entweder M12 geschnitten werden oder eine Reduzier-Gewindehülse (M12 auf M8) eingepresst/eingedreht werden.
3. **Nutenstein-Kompatibilitätsmatrix:**

| Nutenstein-Typ | Nut 5 I-Typ | Nut 6 B-Typ | Nut 6 I-Typ | Nut 8 B-Typ | Nut 8 I-Typ | Nut 10 B-Typ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Nutenstein Nut 5 (I-Typ)** | **Passt** | Zu schmal / wackelt | Zu schmal | Fällt durch | Fällt durch | Fällt durch |
| **Nutenstein Nut 6 (B-Typ)** | Passt nicht (zu breit) | **Passt** | Klemmt oft | Fällt durch | Fällt durch | Fällt durch |
| **Nutenstein Nut 8 (B-Typ, 11,8 mm)** | Passt nicht | Passt nicht | Passt nicht | **Passt** | **Bedingt** (sitzt tief, Steghöhe prüfen) | Fällt durch |
| **Nutenstein Nut 8 (I-Typ, 13,5 mm)** | Passt nicht | Passt nicht | Passt nicht | **Klemmt** (Innenbreite B-Typ oft zu eng) | **Passt** | Fällt durch |
| **Nutenstein Nut 10 (B-Typ, 13,8/19,6 mm)**| Passt nicht | Passt nicht | Passt nicht | Passt nicht | Passt nicht (zu breit) | **Passt** |

---

## 5. Rechtliche Prüfung: Urheberrecht, Markenrecht und CAD-Nutzungsbedingungen

Ein wesentliches Anliegen für Mechvane als quelloffenes CAD-System ist die Klärung, ob und in welchem Umfang Abmessungen, Profilquerschnitte und Produktbezeichnungen in Open-Source-Code und öffentliche Kataloge einfließen dürfen.

### 5.1 Urheberrechtliche Schutzfähigkeit von Profil- und Maßdaten

* **Gesetzliche Grundlage:** Nach § 2 Abs. 2 UrhG (Urheberrechtsgesetz) sind Werke nur persönliche geistige Schöpfungen.
* **Einordnung von Maßwerten:** Reine technische Maßdaten (Außenmaß $40\text{ mm}$, Nutbreite $8\text{ mm}$, Kernbohrung $\varnothing 6{,}8\text{ mm}$, Querschnittsfläche $648{,}9\text{ mm}^2$, Trägheitsmoment $I_x = 90645\text{ mm}^4$) sind physikalische Fakten, funktionale Konstruktionsmerkmale und mathematische Messwerte. Sie besitzen keine individuelle Schöpfungshöhe und sind urheberrechtlich **gemeinfrei**.
* **Rechtsprechung:** Der Bundesgerichtshof (BGH) und der Europäische Gerichtshof (EuGH) haben wiederholt klargestellt, dass technische Funktionsformen, Maße, Toleranzen und Datenstrukturen keinem Urheberrechtsschutz unterliegen, da sonst funktionale Monopole außerhalb des Patentrechts entstünden.

### 5.2 Patentschutz und Gemeinfreiheit

Die grundlegenden Erfindungspatente auf Aluminium-Profilsysteme mit T-Nuten (insbesondere die item-Patente der Erfinder Gerrit Pies und Wolfgang Rixen aus den Jahren 1980–1984 sowie zeitgleiche Bosch-Schutzrechte) hatten eine maximale Laufzeit von 20 Jahren ab Anmeldetag. Sämtliche Basisschutzrechte auf die Profilquerschnitte sind seit vielen Jahren **abgelaufen und gemeinfrei**. Jeder Hersteller darf heute formkompatible I-Typ- und B-Typ-Profile fertigen und vertreiben.

### 5.3 Markenrecht und referenzielle Nutzung (§ 23 MarkenG)

* Die Bezeichnungen „item“ und „Bosch Rexroth“ sind eingetragene Wortmarken der jeweiligen Hersteller.
* **Erlaubte referenzielle Nutzung:** Nach § 23 Abs. 1 Nr. 3 MarkenG darf der Markeninhaber einem Dritten nicht untersagen, die Marke im geschäftlichen Verkehr als Hinweis auf die Bestimmung einer Ware (insbesondere als Zubehör oder Ersatzteil) oder zur Identifizierung der Kompatibilität zu verwenden, sofern die Nutzung den anständigen Gepflogenheiten entspricht.
* **Praxisempfehlung für Mechvane:** Im Katalog und UI sollten primär die neutralen Branchenbegriffe **„I-Typ“** und **„B-Typ“** verwendet werden. Der Zusatz „kompatibel mit item Baureihe 8“ oder „kompatibel mit Bosch Rexroth Raster 30“ ist als sachlicher Kompatibilitätshinweis rechtlich zulässig.

### 5.4 Nutzungsbedingungen der CAD-Daten (Hersteller-EULAs) und Clean-Room-Strategie

* **EULA-Beschränkungen:** Viele Hersteller (wie Misumi, item oder CAD-Portale wie TraceParts und CADENAS) untersagen in ihren Download-Bedingungen und AGB (z. B. Motedis AGB § 5 Ziff. 5: Vorbehalt der Eigentums- und Urheberrechte an Zeichnungen und Konstruktionen) die Weiterverbreitung heruntergeladener nativer CAD-Dateien (STEP, IPT, SLDPRT) als eigenständige CAD-Bibliothek.
* **Architektur-Entscheidung für Mechvane (Clean Room):**
  Mechvane importiert und redistribuiert **keine** proprietären Hersteller-STEP-Dateien!
  Stattdessen generiert Mechvane sämtliche Profilgeometrien, Nuten und Bohrbilder **vollständig prozedural und algorithmisch im Clean Room** über eine eigene parametrische Skizzenfunktion in Python (`solidcraft`/`mechvane`). Da nur die gemeinfreien Maßzahlen als Parameter in eigene Codezeilen einfließen, ist das System vollkommen frei von Rechten Dritter.

---

## 6. Vorschlag für das Datenformat: Profil als parametrische Skizze

Für die Integration in den Gestell-Generator wird ein kompaktes, voll parametrisches JSON-Datenformat definiert. Anstatt komplexe 2D-Polygone mit Hunderten Stützpunkten zu speichern, nutzt Mechvane die **Rotations- und Spiegelsymmetrie** der Profile: Ein quadratisches Viernut-Profil lässt sich durch die Geometrie eines einzigen Quadranten (Viertelprofil) eindeutig beschreiben.

### 6.1 Parameter der Profil-Querschnittsdefinition

Ein Profilquerschnitt wird durch folgende Primärparameter vollständig beschrieben:
1. `raster_x`, `raster_y`: Hüllmaße des Außenprofils (z. B. 40,0 × 40,0 mm).
2. `corner_radius`: Außenradius an den Profilecken (z. B. 4,0 mm bei I-Typ 40).
3. `center_bore_dia`: Durchmesser der Kernbohrung (z. B. 6,8 mm für M8).
4. `slot_width`: Öffnungsbreite der T-Nut (z. B. 8,0 mm).
5. `slot_depth`: Gesamttiefe der Nut von Außenkante bis Nutgrund (z. B. 12,0 mm).
6. `undercut_width`: Innere Breite der T-Nut (z. B. 20,0 mm).
7. `lip_thickness`: Stegdicke der Nutlippe (z. B. 7,6 mm bei I-Typ bzw. 2,2 mm bei B-Typ).
8. `flank_angle_deg`: Flankenwinkel der Nutinnenwand ($0^\circ$ für I-Typ, $\approx 15^\circ$ für B-Typ).
9. `lip_preload_offset`: Konkaver Lippenwinkel / Wölbungsvorspannung ($0{,}2\text{ mm}$ bei I-Typ, $0{,}0\text{ mm}$ bei B-Typ).
10. `mass_per_meter`, `ix_cm4`, `iy_cm4`: Mechanische Kennwerte für Statik und Durchbiegungsberechnung.

### 6.2 Semantische Joint-Anchors für Baugruppen

Der Gestell-Generator benötigt neben der reinen Extrusionsgeometrie semantische Ankerpunkte (*Anchors*) für Joints:
* `slot_centerlines`: 4 Achsen entlang der Nutgründe (für gleitende Nutenstein-Joints).
* `end_face_bore`: Stirnseitige Referenz für Fastened Joints bei Stirnverschraubungen.
* `drill_locations`: Parametrische Bohrbilder für Standard- und Zentralverbinder (z. B. $L_1 = 20{,}0\text{ mm}, D = 9{,}0\text{ mm}$).

### 6.3 JSON-Schema-Entwurf (`profile_cross_section_schema.json`)

```json
{
  "$schema": "json-schema:draft/2020-12/schema",
  "title": "MechvaneAluProfileCrossSection",
  "type": "object",
  "required": ["id", "system", "raster", "groove", "core_bore", "mechanics"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Eindeutige Profilkennung, z. B. alu_i_40x40_l_nut8"
    },
    "name": {
      "type": "string",
      "description": "Anzeigename im Gestell-Generator"
    },
    "system": {
      "type": "string",
      "enum": ["i_typ", "b_typ", "generic"]
    },
    "compatible_with": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Referenzielle Kompatibilitätsangaben (z. B. item Baureihe 8)"
    },
    "raster": {
      "type": "object",
      "required": ["width", "height", "corner_radius"],
      "properties": {
        "width": { "type": "number", "minimum": 10.0 },
        "height": { "type": "number", "minimum": 10.0 },
        "corner_radius": { "type": "number", "minimum": 0.0 }
      }
    },
    "groove": {
      "type": "object",
      "required": ["nominal_width", "slot_width", "slot_depth", "undercut_width", "lip_thickness", "flank_angle_deg"],
      "properties": {
        "nominal_width": { "type": "integer", "description": "Nenngröße der Nut, z. B. 5, 6, 8, 10" },
        "slot_width": { "type": "number", "description": "Istmaß Nutöffnung in mm" },
        "slot_depth": { "type": "number", "description": "Gesamttiefe der Nut in mm" },
        "undercut_width": { "type": "number", "description": "Hinterschnitt- bzw. Nutinnenbreite in mm" },
        "lip_thickness": { "type": "number", "description": "Dicke der tragenden Nutlippe in mm" },
        "flank_angle_deg": { "type": "number", "description": "0 für parallele Flanken, >0 für konische B-Typ Flanken" },
        "lip_preload_offset": { "type": "number", "default": 0.0, "description": "Vorspannungsknick der Lippe in mm (z. B. 0.2)" }
      }
    },
    "core_bore": {
      "type": "object",
      "required": ["diameter", "tap_thread"],
      "properties": {
        "diameter": { "type": "number", "description": "Kernlochdurchmesser in mm" },
        "tap_thread": { "type": "string", "description": "Regelgewinde, z. B. M5, M6, M8, M12" },
        "thread_depth_recommended": { "type": "number", "description": "Empfohlene Mindestgewindetiefe in mm" }
      }
    },
    "mechanics": {
      "type": "object",
      "required": ["mass_per_meter", "ix_cm4", "iy_cm4", "wx_cm3", "wy_cm3"],
      "properties": {
        "mass_per_meter": { "type": "number", "description": "Metergewicht in kg/m" },
        "area_mm2": { "type": "number", "description": "Querschnittsfläche in mm2" },
        "ix_cm4": { "type": "number", "description": "Flächenträgheitsmoment um X-Achse in cm4" },
        "iy_cm4": { "type": "number", "description": "Flächenträgheitsmoment um Y-Achse in cm4" },
        "wx_cm3": { "type": "number", "description": "Widerstandsmoment Wx in cm3" },
        "wy_cm3": { "type": "number", "description": "Widerstandsmoment Wy in cm3" }
      }
    },
    "connection_drilling": {
      "type": "object",
      "properties": {
        "standard_drill_dia": { "type": "number", "description": "Querbohrungsdurchmesser in mm (z. B. 9.0)" },
        "standard_drill_distance": { "type": "number", "description": "Bohrungsabstand zur Stirnkante in mm (z. B. 20.0)" },
        "step_drill_large_dia": { "type": "number", "description": "Senkdurchmesser für Zentralverbinder in mm (z. B. 17.0)" },
        "step_drill_distance": { "type": "number", "description": "Abstand Zentralverbinderbohrung in mm (z. B. 22.5)" }
      }
    }
  }
}
```

---

## 7. Quellenverzeichnis und wörtliche Zitate

### Beleg: Dold Mechatronik Aluminiumprofile Gesamtkatalog
* **Quelle:** [Dold Mechatronik Gesamtkatalog PDF](https://www.dold-mechatronik.de/documents/Datenblaetter/Aluminiumprofile/Dold_Mechatronik_Aluminiumprofile_Gesamtkatalog.pdf)
* **Fundstelle:** Seite 27 (Nut-Abmessungen B-Typen), Seite 80 (Nut-Abmessungen I-Typen), Seite 28 (20x20L B-Typ), Seite 81 (20x20L I-Typ), Seite 118 (40x40L I-Typ)
* **Wörtliches Zitat:** „Aluminiumprofil B-Typen Nut-Abmessungen“
* **Belegte Zahlen:** 6,0, 1,5, 12,1, 20, 162,1, 6688,1, 0,439.

### Beleg: Dold Mechatronik Aluminiumprofil 20x20L I-Typ Nut 5
* **Quelle:** [Dold Profil 20x20L I-Typ](https://www.dold-mechatronik.de/Aluminiumprofil-20x20L-I-Typ-Nut-5-049kg-m-Zuschnitt-50-6000mm)
* **Fundstelle:** Produktdatenblatt und Technische Daten
* **Wörtliches Zitat:** „Aluminiumprofil 20x20L I-Typ Nut 5“
* **Belegte Zahlen:** 0,493, 20, 5.

### Beleg: Dold Mechatronik Winkel 20 I-Typ Nut 5
* **Quelle:** [Dold Winkel 20 I-Typ](https://www.dold-mechatronik.de/Winkel-20-I-Typ-Nut-5)
* **Fundstelle:** Produktbeschreibung und Montagehinweis
* **Wörtliches Zitat:** „Winkel mit Zentriernasen ermöglichen eine schnelle, exakte und verdrehgesicherte Montage.“
* **Belegte Zahlen:** 20, 4.

### Beleg: Dold Mechatronik Winkel 30 B-Typ Nut 8
* **Quelle:** [Dold Winkel 30 B-Typ](https://www.dold-mechatronik.de/Winkel-30-B-Typ-Nut-8)
* **Fundstelle:** Technische Daten und Zentriernasen-Funktion
* **Wörtliches Zitat:** „Bei Montage quer zur Nut oder auf Platten kann man einfach die Zentriernasen abbrechen.“
* **Belegte Zahlen:** 30, 8, 6.

### Beleg: Dold Mechatronik Winkel 40 I-Typ Nut 8
* **Quelle:** [Dold Winkel 40 I-Typ](https://www.dold-mechatronik.de/Winkel-40-I-Typ-Nut-8)
* **Fundstelle:** Produktbeschreibung und Schraubenbefestigung
* **Wörtliches Zitat:** „bei Montage quer zur Nut oder auf Platten können die Zentriernasen abgebrochen werden“
* **Belegte Zahlen:** 40, 8, 16.

### Beleg: Dold Mechatronik Standardverbinder I-Typ Nut 8
* **Quelle:** [Dold Standardverbinder I-Typ](https://www.dold-mechatronik.de/Standardverbinder-I-Typ-Nut-8-inkl-Befestigungssatz)
* **Fundstelle:** Technische Daten und Abmessungen
* **Wörtliches Zitat:** „Der Standardverbinder sorgt für eine verdrehgesicherte Direktverbindung zwischen Alu-Profilen.“
* **Belegte Zahlen:** 35, 17, 9,0, 10, 8.

### Beleg: Dold Mechatronik Automatik-Verbinder Set I-Typ Nut 8
* **Quelle:** [Dold Automatik-Verbinder Set I-Typ](https://www.dold-mechatronik.de/Automatik-Verbinder-Set-I-Typ-Nut-8-mit-Befestigungssatz)
* **Fundstelle:** Produktbeschreibung und Montageeigenschaften
* **Wörtliches Zitat:** „Keine Profilbearbeitung erforderlich. Profil vormontiert aufsetzbar.“
* **Belegte Zahlen:** 8, 6, 40.

### Beleg: Dold Mechatronik Bolzenverbinder I-Typ Nut 8
* **Quelle:** [Dold Bolzenverbinder 40](https://www.dold-mechatronik.de/Bolzenverbinder-I-Typ-Nut-8-40)
* **Fundstelle:** Technische Daten und Bohrungsabstände
* **Wörtliches Zitat:** „Bohrungsabstand der Bohrungen im Bolzenverbinder: 26mm“
* **Belegte Zahlen:** 14, 26, 8, 20.

### Beleg: Dold Mechatronik Nutensteine I-Typ Nut 5
* **Quelle:** [Dold Nutensteine I-Typ Nut 5](https://www.dold-mechatronik.de/Nutensteine-Hammermuttern-und-Schrauben-fuer-Aluminiumprofile-I-Typ-Nut-5)
* **Fundstelle:** Produktauswahl und Maßangaben
* **Wörtliches Zitat:** „Nutenstein mit Steg und Kugel - 7,7*4,65*12 - M3, Stahl verzinkt, I-Typ Nut 5“
* **Belegte Zahlen:** 7,7, 4,65, 12, 5, 3.

### Beleg: Dold Mechatronik Nutensteine B-Typ Nut 8
* **Quelle:** [Dold Nutensteine B-Typ Nut 8](https://www.dold-mechatronik.de/Nutensteine-Hammermuttern-und-Schrauben-fuer-Aluminiumprofile-B-Typ-Nut-8)
* **Fundstelle:** Produktauswahl und Maßangaben
* **Wörtliches Zitat:** „Nutenstein mit Feder - 11,8*4,8*16, M4, Stahl verzinkt, B-Typ Nut 8“
* **Belegte Zahlen:** 11,8, 4,8, 16, 8, 4.

### Beleg: Dold Mechatronik Nutensteine B-Typ Nut 10
* **Quelle:** [Dold Nutensteine B-Typ Nut 10](https://www.dold-mechatronik.de/Nutensteine-Hammermuttern-und-Schrauben-fuer-Aluminiumprofile-B-Typ-Nut-10)
* **Fundstelle:** Produktauswahl und Maßangaben
* **Wörtliches Zitat:** „Nutenstein mit Feder - 13,8*5,3*20, M4, Stahl verzinkt, B-Typ Nut 10“
* **Belegte Zahlen:** 13,8, 5,3, 20, 10, 4.

### Beleg: Dold Mechatronik Nutensteine I-Typ Nut 8
* **Quelle:** [Dold Nutensteine I-Typ Nut 8](https://www.dold-mechatronik.de/Nutensteine-Hammermuttern-und-Schrauben-fuer-Aluminiumprofile-I-Typ-Nut-8)
* **Fundstelle:** Produktauswahl und Maßangaben
* **Wörtliches Zitat:** „Nutenstein mit Steg und Kugel - 13,5*7,2*22 - M4, Stahl verzinkt, I-Typ Nut 8“
* **Belegte Zahlen:** 13,5, 7,2, 22, 8, 4.

### Beleg: Motedis Aluminiumprofil 30x30 B-Typ Nut 8
* **Quelle:** [Motedis Profil 30x30 B-Typ](https://www.motedis.com/de/Aluprofil-30x30-B-Typ-Nut-8)
* **Fundstelle:** Produktdatenübersicht
* **Wörtliches Zitat:** „Produktdaten Aluprofil 30x30 B-Typ Nutbreite 8 in der Übersicht“
* **Belegte Zahlen:** 30, 8, 4, 9.

### Beleg: Motedis Aluminiumprofil 40x40 B-Typ Nut 10
* **Quelle:** [Motedis Profil 40x40 B-Typ](https://www.motedis.com/de/Aluprofil-40x40-B-Typ-Nut-10)
* **Fundstelle:** Produktdatenübersicht
* **Wörtliches Zitat:** „Produktdaten Aluprofil 40x40 B-Typ Nutbreite 10 in der Übersicht“
* **Belegte Zahlen:** 40, 10, 4, 12.

### Beleg: Motedis Allgemeine Geschäftsbedingungen AGB
* **Quelle:** [Motedis AGB](https://www.motedis.com/de/unsere-agb:_:3.html)
* **Fundstelle:** § 5 Eigentumsvorbehalt und Unterlagen
* **Wörtliches Zitat:** „An Zeichnungen, Konstruktionen und anderen Unterlagen von uns behalten wir uns Eigentums- und urheberrechtliche Verwertungsrechte“
* **Belegte Zahlen:** 5, 6.

### Beleg: Dold Mechatronik CAD-Daten Download
* **Quelle:** [Dold CAD-Download](https://www.dold-mechatronik.de/CAD-Daten-von-Aluprofilen-herunterladen)
* **Fundstelle:** Vorteile und Formatangaben
* **Wörtliches Zitat:** „Immer im passenden STEP-Format (.stp) – kompatibel mit gängiger Konstruktionssoftware“
* **Belegte Zahlen:** 1, 2, 3, 4, 5.

### Beleg: Urheberrechtsgesetz UrhG § 2 Geschützte Werke
* **Quelle:** [Gesetze im Internet UrhG § 2](https://www.gesetze-im-internet.de/urhg/__2.html)
* **Fundstelle:** § 2 Abs. 2 UrhG
* **Wörtliches Zitat:** „Werke im Sinne dieses Gesetzes sind nur persönliche geistige Schöpfungen.“
* **Belegte Zahlen:** 1, 2, 7.

### Beleg: Markengesetz MarkenG § 23 Benutzung von Namen und beschreibenden Angaben
* **Quelle:** [Gesetze im Internet MarkenG § 23](https://www.gesetze-im-internet.de/markeng/__23.html)
* **Fundstelle:** § 23 Abs. 1 Einleitung und Ziff. 3 MarkenG
* **Wörtliches Zitat:** „Der Inhaber einer Marke oder einer geschäftlichen Bezeichnung darf einem Dritten nicht untersagen, im geschäftlichen Verkehr Folgendes zu benutzen“
* **Belegte Zahlen:** 1, 2, 3.
