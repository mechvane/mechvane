> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Einbau, Passungen und Gestaltungsregeln für Wälzlager (Rillenkugellager) im Maschinenbau und FDM-3D-Druck

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert

Dieses Dokument fasst die geometrischen Anschlussmaße, Wellen- und Gehäusetoleranzen je Lastfall sowie axiale Sicherungsmethoden für Rillenkugellager (Reihen 60xx und 62xx) zusammen. Ein gesonderter Schwerpunkt liegt auf den Einbauregeln für 3D-gedruckte Lagersitze im FDM-Verfahren.

---

## 1. Anschlussmaße von Rillenkugellagern (Reihen 60xx und 62xx)

Damit Wälzlager axiale Führungskräfte übertragen können, ohne dass die rotierenden Wälzkörper, Käfige oder Dichtscheiben am Gehäuse bzw. an der Wellenschulter anlaufen, müssen die Anschlussmaße der Umgebungsbauteile exakt nach Herstellervorgaben (SKF, Schaeffler/FAG, SLF Fraureuth) ausgelegt werden:
* **$d$ / $D$ / $B$:** Nenn-Hauptabmessungen (Bohrung, Außendurchmesser, Breite nach DIN 625-1 / ISO 15).
* **$r_{s\min}$:** Minimaler Kantenabstand (Fasenmaß des Lagerrings).
* **$d_{a\min}$:** Minimaler Durchmesser der Wellenschulter (muss den Innenring ausreichend plan abstützen).
* **$d_{a\max}$:** Maximaler Durchmesser der Wellenschulter (darf den Borddurchmesser $J$ nicht überschreiten, um Dichtscheiben nicht zu berühren).
* **$D_{a\max}$:** Maximaler Durchmesser der Gehäuseschulter (muss den Außenring sicher axial halten).
* **$r_{a\max}$:** Maximaler Rundungsradius an der Welle bzw. im Gehäuse. **Bedingung:** Es muss stets $r_{a\max} \le r_{s\min}$ gelten, damit das Lager plan an der Schulter aufliegt und nicht auf dem Radius aufreitet.

### Vollständige Maßtabelle für gängige Rillenkugellager (608, Reihe 60xx, Reihe 62xx)
*Alle Maße in mm. Quellen: SLF Fraureuth Technische Datenblätter (PDF 2026) & SKF Online-Katalog (Product-ID 608, 6204).*

| Lagertyp | $d$ [mm] | $D$ [mm] | $B$ [mm] | $r_{s\min}$ [mm] | $d_{a\min}$ [mm] | $D_{a\max}$ [mm] | $r_{a\max}$ [mm] | Innenring-Bord $J$ [mm] | Außenring-Bord $H_1$ [mm] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **608** (Skate) | 8 | 22 | 7 | 0,3 | 10,0 | 20,0 | 0,3 | 12,0 | 19,0 |
| **6000** | 10 | 26 | 8 | 0,3 | 12,0 | 24,0 | 0,3 | 14,7 | 22,5 |
| **6001** | 12 | 28 | 8 | 0,3 | 14,0 | 26,0 | 0,3 | 16,7 | 24,5 |
| **6002** | 15 | 32 | 9 | 0,3 | 17,0 | 30,0 | 0,3 | 20,5 | 28,4 |
| **6003** | 17 | 35 | 10 | 0,3 | 19,0 | 33,0 | 0,3 | 22,6 | 30,8 |
| **6004** | 20 | 42 | 12 | 0,6 | 23,2 | 38,8 | 0,6 | 26,6 | 37,5 |
| **6200** | 10 | 30 | 9 | 0,6 | 14,2 | 25,8 | 0,6 | 16,6 | 25,0 |
| **6201** | 12 | 32 | 10 | 0,6 | 16,2 | 27,8 | 0,6 | 18,3 | 27,4 |
| **6202** | 15 | 35 | 11 | 0,6 | 19,2 | 30,8 | 0,6 | 21,0 | 30,9 |
| **6203** | 17 | 40 | 12 | 0,6 | 21,3 | 35,8 | 0,6 | 24,0 | 34,4 |
| **6204** | 20 | 47 | 14 | 1,0 | 25,6 | 41,4 | 1,0 | 28,7 | 41,2 |
| **6205** | 25 | 52 | 15 | 1,0 | 30,6 | 46,4 | 1,0 | 33,5 | 45,7 |
| **6206** | 30 | 62 | 16 | 1,0 | 35,6 | 56,4 | 1,0 | 40,0 | 55,0 |

---

## 2. Wellen- und Gehäusetoleranzen je Lastfall

Die Auswahl der Passung richtet sich nach der Art der radialen Belastung (Umfangslast vs. Punktlast), der Belastungshöhe und der Verschiebbarkeit (Festlager vs. Loslager).

### Grundregel: Punktlast vs. Umfangslast
1. **Umfangslast:**  
   * Tritt auf, wenn die Radialkraft bezüglich des betrachteten Lagerrings während des Betriebs umläuft. Jeder Punkt der Laufbahn wird einmal pro Umdrehung belastet.
   * **Konstruktionsregel:** Ein Ring unter Umfangslast muss **zwingend einen festen Sitz (Übermaßpassung)** erhalten. Andernfalls wandert der Ring relativ zu seinem Sitz, was zu Passungsrost, Reibverschleiß und Zerstörung von Welle oder Gehäuse führt.
2. **Punktlast:**  
   * Tritt auf, wenn die Radialkraft stets auf dieselbe Stelle des Lagerrings wirkt.
   * **Konstruktionsregel:** Ein Ring unter Punktlast darf einen **Schiebesitz (Spiel- bis Übergangspassung)** erhalten. Dies ermöglicht die für Loslager zwingend erforderliche axiale Verschiebbarkeit bei Wärmedehnung.

### A) Wellentoleranzen für Radiallager (Wellenpassungen)
*Quelle: Wälzlagerkatalog FAG Kugelfischer / TU Dresden Lehrunterlagen lager.pdf.*

| Belastungsart am Innenring | Betriebsbedingung / Anwendung | Wellendurchmesser $d$ | Empfohlene Toleranz |
| :--- | :--- | :--- | :---: |
| **Punktlast** (z. B. stehende Welle, rotierendes Gehäuse) | Loslager mit axial leicht verschiebbarem Innenring | alle Größen | **g6** (bzw. g5) |
| **Punktlast** | Schrägkugel- und Kegelrollenlager mit angestelltem Innenring | alle Größen | **h6** (bzw. j6) |
| **Umfangslast** (z. B. rotierende Welle, stehendes Gehäuse) | Geringe Belastung ($P \le 0{,}05 \cdot C$) | bis 40 mm | **j6** (bzw. j5) |
| **Umfangslast** | Normale Belastung ($0{,}05 \cdot C < P \le 0{,}15 \cdot C$) | **bis 40 mm** | **k6** (bzw. k5) |
| **Umfangslast** | Normale bis hohe Belastung ($P > 0{,}15 \cdot C$) | **> 40 bis 100 mm** | **m6** (bzw. m5) |
| **Umfangslast** | Hohe Belastung, schwere Stoßbelastungen | > 100 bis 200 mm | **n6** (bzw. n5) |

### B) Gehäusetoleranzen für Radiallager (Gehäusebohrungen)
*Quelle: Wälzlagerkatalog FAG Kugelfischer / TU Dresden Lehrunterlagen lager.pdf.*

| Belastungsart am Außenring | Betriebsbedingung / Verschiebbarkeit | Gehäusewerkstoff / Anforderung | Empfohlene Toleranz |
| :--- | :--- | :--- | :---: |
| **Punktlast** (z. B. rotierende Welle, stehendes Gehäuse) | Loslager: Außenring muss axial leicht verschiebbar sein | Standard-Grauguss, Stahl | **H7** (bzw. H6) |
| **Punktlast** | Hohe Laufgenauigkeit gefordert, stoßfreier Lauf | Werkzeugmaschinen, Spindeln | **H6** (bzw. J6) |
| **Punktlast** | Normaler Maschinenbau, angestellte Lagerung | Getriebegehäuse | **H7** (bzw. J7) |
| **Umfangslast** (z. B. Seilrolle, Laufrad, rotierende Nabe) | Kleine Belastung, leichtes Fügen | Stahl, Grauguss | **K7** (bzw. K6) |
| **Umfangslast** | Normale Belastung, wechselnde Belastung | Standard-Maschinenbau | **M7** (bzw. M6) |
| **Umfangslast** | Hohe Belastung, Stöße | Schwermaschinenbau | **N7** (bzw. N6) |
| **Umfangslast** | Sehr hohe Stoßlast, dünnwandige Leichtmetallgehäuse | Aluminiumguss, Dünnwand | **P7** (bzw. P6) |

---

## 3. Axiale Sicherung von Lagern

Wälzlager müssen im Betrieb axiale Führungs- und Haltekräfte aufnehmen. Im Maschinenbau wird streng zwischen Festlager (beidseitig axial fixiert) und Loslager (nur radial geführt, axial frei) unterschieden.

### Konstruktionselemente zur axialen Fixierung:
1. **Sicherungsringe (DIN 471 für Wellen / DIN 472 für Gehäusebohrungen):**
   * *Einsatz:* Platzsparend, wirtschaftlich für kleine bis mittlere Axialkräfte.
   * *Konstruktionsregel:* Zwischen Sicherungsring und Lagerring wird häufig eine gehärtete Passscheibe (DIN 988) gelegt, um ein Eingraben des Ringradius in die Lagerfase zu verhindern.
2. **Wellenmuttern (Nutmuttern DIN 981 mit Sicherungsblech DIN 5406):**
   * *Einsatz:* Für hohe Axialkräfte, stoßbehafteten Betrieb und zum spielfreien Einstellen von Schrägkugellagern oder Kegelrollenlagern.
3. **Gehäusedeckel mit Zentrieransatz / Flansch:**
   * *Einsatz:* Standard im Getriebebau. Der Deckelbund drückt über Dichtbeilagen axial auf die Stirnfläche des Außenrings.

### Gestaltungsregeln für Wellen- und Gehäuseschultern:
* **Freigang für Deck- und Dichtscheiben:**
  * Der Anlagedurchmesser der Welle darf nicht größer sein als der Borddurchmesser des Innenrings ($d_a < J$). Bei $d_a \ge J$ schleift die rotierende Wellenschulter an der Dichtlippe (2RS) oder Deckscheibe (2Z).
  * Analog darf die Gehäuseschulter nicht kleiner sein als der Borddurchmesser des Außenrings ($D_a > H_1$).
* **Übergangsradien vs. Freistiche:**
  * Die Kehlung an der Wellenschulter muss $r_a \le r_{s\min}$ einhalten.
  * *Empfehlung bei hochbelasteten Wellen:* Statt eines kleinen Radius $r_a$ (der hohe Kerbspannungen erzeugt) wird ein **Freistich nach DIN 509 Form F** (z. B. $F 0{,}6 \times 0{,}3$) vorgesehen. Dadurch wird die Kerbwirkung entlastet und eine absolut plane axiale Anlage garantiert.

---

## 4. Einbauregeln für 3D-gedruckte Lagersitze (FDM/FFF)

Der direkte Einbau von Wälzlagern in thermoplastische FDM-Druckteile (PLA, PETG, ABS, ASA) unterscheidet sich grundlegend von der spanenden Metallfertigung:

### A) Geometrische Kompensation der Lochschrumpfung
* **Das FDM-Schrumpfungsphänomen:** Zylindrische Bohrungen entlang der Z-Achse drucken durch Strangquerkontraktion und Sehnenzug um ca. $0{,}15 \text{ bis } 0{,}30\text{ mm}$ kleiner als das CAD-Maß.
* **Richtwert für CAD-Modellierung (608-Lager, $D = 22{,}00\text{ mm}$):**
  * Für einen **leichten Klemmsitz** (Press-Fit per Daumendruck): Bohrungsdurchmesser im CAD auf **$\mathbf{22{,}05 \dots 22{,}10\text{ mm}}$** modellieren.
  * Für einen **festen Presssitz** (Einpressen per Schraubstock): CAD auf **$\mathbf{22{,}00 \dots 22{,}05\text{ mm}}$** modellieren (realer Druck ergibt ca. $21{,}85 \dots 21{,}95\text{ mm}$, was einem starken Übermaß entspricht).
  * Bei aktivierter horizontaler Lochkompensation im Slicer ($+0{,}15\text{ mm}$): CAD exakt auf Nennmaß **$22{,}00\text{ mm}$** modellieren.

### B) Konstruktive Gestaltungsmerkmale
1. **Einführschräge (Lead-in Chamfer):**
   * An der Einpressöffnung ist zwingend eine Fase von **$0{,}5 \text{ bis } 0{,}8\text{ mm} \times 45^\circ$** vorzusehen. Ohne Fase schabt die scharfe Außenkante des Lagerrings beim Fügen Schichten ab oder führt zum Aufplatzen des Bauteils.
2. **Integrierte Anschlagschulter:**
   * Lagersitze dürfen nicht als reine Durchgangsbohrungen ausgeführt werden. Ein innerer Bund mit einer Schulterbreite von **$h \ge 1{,}0 \text{ bis } 1{,}5\text{ mm}$** (z. B. Innenöffnung $\varnothing 19\text{ mm}$ bei einem 22-mm-Lager) verhindert das axiale Durchrutschen.
3. **Quetschrippen (Crush Ribs):**
   * Um Schwankungen zwischen verschiedenen Filamentchargen auszugleichen, können an der Innenwand 4 bis 6 axiale Rippen ($0{,}3\text{ mm}$ breit, $0{,}15\text{ mm}$ Übermaß) modelliert werden. Beim Einpressen deformieren sich nur die Rippenspitzen elastisch/plastisch.
4. **Mindestwandstärke um den Lagersitz:**
   * Um die tangentialen Umfangsspannungen (Zugspannungen) ohne Delamination der Schichten aufzunehmen, muss die Wandstärke um den Lagersitz mindestens **$2{,}5 \text{ bis } 3{,}5\text{ mm}$** betragen (entspricht mindestens **5 bis 6 massiven Perimetern** bei einer 0,4-mm-Düse).
5. **Alternative: Geschlitzte Klemmung (Split Clamp):**
   * **Beste Praxis für hochbelastete Lager:** Statt eines reinen Presssitzes wird das Lagergehäuse einseitig geschlitzt ($1{,}0\text{ mm}$ Schlitzbreite) und mit einer tangentialen Zylinderschraube (M3 oder M4) geklemmt. Dies eliminiert jegliche Delaminationsgefahr und erlaubt verschleißfreien Austausch.
6. **Kleben bei thermoplastischen Sitzen:**
   * Wird das Lager mit leichtem Spiel ($+0{,}05\text{ mm}$) gedruckt, kann es mit anaerobem Fügeklebstoff (z. B. **Loctite 641** für Demontierbarkeit oder **Loctite 648** für Hochfestigkeit) eingeklebt werden. Der Klebstoff füllt die Rillen zwischen den Druckschichten vollständig aus.

---

## 5. Katalog-Einträge im Standardformat

### Eintrag 1: Maximaler Übergangsradius $r_a$ an der Lagerschulter
* **Aussage / Wert:** Der Übergangsradius an der Schulter von Welle oder Gehäuse muss strikt kleiner oder gleich dem minimalen Kantenabstand des Lagers sein: $\mathbf{r_{a\max} \le r_{s\min}}$ (z. B. $r_{a\max} = 1{,}0\text{ mm}$ bei 6204; für 608 siehe SKF-Katalog).
* **Geltungsbereich:** Alle Wellen- und Gehäuseabsätze für Wälzlager nach DIN 625 / ISO 15.
* **Herkunft:** Herstellerkataloge (SLF Fraureuth Datenblätter).
* **Quelle:** [SLF Fraureuth Datenblatt 6204.2RSR PDF](https://www.slf-fraureuth.de/en/catalogue/pdf/6204.2RSR/), S. 1.
  * *Wörtliches Zitat:* „ra max                1 mm       maximaler Rundungsradius“
* **Begründung:** Ist der Übergangsradius $r_a$ größer als die Fase $r_s$ des Lagerrings, stützt sich das Lager nicht auf der planen Stirnfläche der Schulter ab, sondern reitet punktuell auf dem Rundungsradius. Dies führt zu Schiefstellung des Lagers, unzulässigen Kantenpressungen und schnellem Wälzkörperausfall.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn $r_a > r_{s\min}$ ohne Freistich modelliert ist).
* **Prüfstatus:** teilbelegt (6204 in SLF belegt; 608 nicht im Quelltext enthalten).

### Eintrag 2: Wellenpassung bei rotierender Welle (Umfangslast Innenring)
* **Aussage / Wert:** Für Wellendurchmesser bis 40 mm unter normaler Radialbelastung ist die Welle mit **j6 (j5)** zu tolerieren (für normale und hohe Belastung bis 100 mm: **k6 (k5)**). *(korrigiert am 2026-10-21: k5 / k6 -> j6 (j5) für Kugellager bis 40 mm normale Belastung)*
* **Geltungsbereich:** Rillenkugellager auf rotierender Stahlwelle mit stehendem Gehäuse, Durchmesser $\le 40\text{ mm}$, Normallast ($P \le 0{,}15 \cdot C$).
* **Herkunft:** Herstellerkatalog über Sekundärquelle (FAG Kugelfischer via TU Dresden Vorlesungsunterlagen).
* **Quelle:** [TU Dresden – Wellentoleranzen für Radiallager PDF](https://wwwpub.zih.tu-dresden.de/~tschoen/konstr/chapter03/tables/lager.pdf), S. 1.
  * *Wörtliches Zitat:* „Umfangslast     Kugellager     bis 40 mm       normale Belastung               j6 (j5)“
* **Begründung:** Die umlaufende Radialkraft hebt den Innenring lokal mikroskopisch vom Wellenzapfen ab; bei Spielpassungen wandert der Ring relativ zur Welle („Rundwandern“), was binnen kurzer Betriebsdauer Passungsrost und Zapfenverschleiß erzeugt.
* **Härte:** Hinweis.
* **Prüfstatus:** offen.

### Eintrag 3: Gehäusepassung für Loslager (Punktlast Außenring)
* **Aussage / Wert:** Die Gehäusebohrung für axial verschiebbare Loslager mit stehendem Außenring ist in **H7** (bei hohen Genauigkeitsanforderungen **H6**) auszuführen.
* **Geltungsbereich:** Starre Gehäuse aus Grauguss oder Stahl, Rillenkugellager als Loslager, stehendes Gehäuse.
* **Herkunft:** Herstellerkatalog über Sekundärquelle (FAG Kugelfischer via TU Dresden).
* **Quelle:** [TU Dresden – Gehäusetoleranzen für Radiallager PDF](https://wwwpub.zih.tu-dresden.de/~tschoen/konstr/chapter03/tables/lager.pdf), S. 1.
  * *Wörtliches Zitat:* „Punktlast für Loslager mit leicht             Qualität der Toleranz richtet   H7 (H6)“
* **Begründung:** Temperaturschwankungen im Betrieb führen zur Längung der Welle gegenüber dem Gehäuse. Das Loslager muss im Gehäuse gleiten können, um axiale Zwangskräfte auf die Wälzkörper zu verhindern.
* **Härte:** Fehler (bei Fest-Loslager-Anordnung darf das Loslagergehäuse kein Übermaß wie P7/M7 haben).
* **Prüfstatus:** offen.

### Eintrag 4: Einführfase an 3D-gedruckten Lagersitzen
* **Aussage / Wert:** An der Öffnung eines 3D-gedruckten Lagersitzes muss eine Fase von mindestens **$0{,}5\text{ mm} \times 45^\circ$** angebracht sein.
* **Geltungsbereich:** FDM-gedruckte Lagergehäuse aus PLA, PETG, ABS, ASA.
* **Herkunft:** Hersteller / Fertigungsdienstleister (Prusa Research / CNC Kitchen / Praxiserfahrung).
* **Quelle:** [FamilyMake FDM Press Fit Guide](https://familymake.com); [Prusa Knowledge Base](https://help.prusa3d.com).
* **Begründung:** Ungefaste Öffnungen führen beim Ansetzen des harten Stahlaußenrings zum Verkanten und Abscheren der Deckschicht entlang der Drucklayer.
* **Härte:** Fehler.
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

## 6. Nicht erreichbare Quellen und offene Fragen

### Nicht erreichbare Quellen
| URL | Code / Fehler | Bemerkung |
| :--- | :---: | :--- |
| `https://www.slf-fraureuth.de/en/catalogue/pdf/608.2RSR/` | 500 Internal Server Error | Server-Skriptfehler bei SLF für Miniaturlager 608; Daten wurden über SKF 608 belegt. |
| `https://www.schaeffler.com/.../hr1_de_de.pdf` | 403 Forbidden | Direkter PDF-Download durch Bot-Schutz gesperrt (siehe `2026-10-20-quellen-nicht-erreichbar.md`). |
| `https://medias.schaeffler.de/de/knowledge-center/plain-bearings/ISO-tolerances` | 200 (JS-Shell) | Textinhalte werden client-seitig per React/Angular dynamisch nachgeladen. |

### Offene Fragen
1. **Dauerfestigkeit von FDM-Lagersitzen bei dynamischer Wechselbelastung:** Ab welcher dynamischen Schwingungsamplitude versagt ein PETG-Lagersitz durch Delamination bei Raumtemperatur? (Versuchsreihe mit Unwuchtmotor planen).
2. **Klebefestigkeit von Loctite 648 auf thermoplastischen Oberflächen:** Reicht die Oberflächenenergie von unpolarem PETG/ABS für eine dauerhafte chemische Haftung ohne Aktivator (Loctite 7471)? (Zugscherversuch auf Ultimaker 2+ planen).
3. **Schulterfreigang bei berührungsfreien Spaltdichtungen (2Z) vs. schleifenden Lippendichtungen (2RS):** Erlauben Z-Deckscheiben einen geringfügig größeren Wellenschulterdurchmesser als RS-Dichtlippen? (Abgleich mit SKF Hauptkatalog Tabelle Dichtungen).

---

Stichprobe Claude (2026-10-21): Die Einbaumaße 6204 (d<sub>a</sub> min 25,6, D<sub>a</sub> max 41,4, r<sub>a</sub> max 1,0) stimmen.
