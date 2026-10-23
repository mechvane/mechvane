> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Stichprobe 2026-10-20 (Claude): alle zitierten URLs erreichbar; Böllhoff-HELICOIL-Zitat wörtlich bestätigt; Ing.-Büro-Hanke-Werte für G-AlSiCu3 weichen ab (PDF: M6 23,2 mm, M8 27,1 mm statt 21,3/27,9 mm). Zahlen vor dem Übernehmen einzeln an der Quelle prüfen.

# Recherchebericht: Mindest-Einschraubtiefen für Schrauben der Festigkeitsklasse 8.8 (Regelgewinde)

Die Auslegung der Mindest-Einschraubtiefe im Maschinenbau (u. a. nach **VDI 2230 Blatt 1**) folgt dem Grundsatz der **Bruchgleichheit**: Bei einer Überlastung der Verbindung muss die Schraube im freien Gewinde bzw. Schaft plastisch dehnen und reißen, bevor das Innengewinde im Bauteil durch Abscheren versagt (Gewindeauszug). 

Da Werkstoffe unterschiedliche Scherfestigkeiten $\tau_B$ aufweisen, skaliert die erforderliche tragende Einschraubtiefe als Vielfaches des Schraubennenndurchmessers $d$. Bei den Angaben ist strikt zwischen der **effektiven Gewindeüberdeckung** $m_{\text{eff}}$ (rein tragende Gänge) und der **Gesamteinschraubtiefe** $m_{\text{ges}}$ (inklusive Anschnitt-/Fasenzuschlag $m_{\text{zu}} \approx 2 \cdot P$) zu unterscheiden.

---

## a) Aluminium-Gusslegierungen (z. B. AlSi10Mg, AlSi9Cu3, G-AlSi12)

Bei Aluminium-Gusslegierungen liegt das Scherfestigkeitsverhältnis nach VDI 2230 typischerweise bei $\tau_B / R_m \approx 0{,}52$. Die Mindestzugfestigkeit schwankt je nach Legierung und Gussverfahren stark (ca. $150 \text{ bis } 320\,\text{N/mm}^2$).

### 1. Quelle: Bossard AG (Technisches Handbuch / Whitepaper)
* **URL:** [Bossard Technische Informationen – Einschraubtiefe PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf)
* **Genaue Bedingung:** Schraubenfestigkeitsklasse 8.8, metrisches ISO-Regelgewinde, Toleranzpaarung 6g / 6H, ausreichende Wandstärke beim Muttergewinde.
  * **AlMg3 F18** ($R_m > 180\,\text{N/mm}^2$): **$2{,}0 \cdot d$** (Versuchswert) bzw. **$[3{,}0 \cdot d]$** (theoretischer VDI 2230-Rechenwert).
  * **AlMgSi1 F32** ($R_m > 330\,\text{N/mm}^2$): **$1{,}4 \cdot d$**.
  * **Al 99,5** ($R_m > 180\,\text{N/mm}^2$): **`–` (für 8.8 Regelgewinde nicht angegeben / nicht empfohlen)**.
  * *Hinweis Legierungsvergleich:* Für Magnesiumguss **GMgAl9 Zn1** ($R_m > 230\,\text{N/mm}^2$): **$1{,}4 \cdot d$**.
* **Wörtliches Zitat:**
  > *„Sollen Schrauben in geschnittene Innengewinde eingeschraubt [...] Festigkeit des Bauteilwerkstoffes minimale Eindrehtiefen festzulegen.“*

### 2. Quelle: Ingenieurbüro Andreas Hanke (Berechnungstabellen nach VDI 2230-1:2015)
* **URL:** [Ing.-Büro Hanke – Fachartikel Mindesteinschraubtiefe nach VDI 2230](https://www.ing-hanke.de/know-how/mindesteinschraubtiefe-von-hochfesten-schraubverbindungen-mit-metrischem-regelgewinde-nach-vdi-2230-blatt-1/)
* **Genaue Bedingung:** Schraubenklasse 8.8, Scherfestigkeitsverhältnis $\tau_B / R_m = 0{,}52$, Gesamteinschraubtiefe $m_{\text{ges}}$ inklusive 2 nicht tragenden Gewindegängen ($m_{\text{ges}} = m_{\text{eff}} + 2 \cdot P$), Wandverhältnis $s/d > 1{,}9$:
  * **G-AlSiCu3 S F** ($R_m = 150\,\text{N/mm}^2$, $\tau_B = 78\,\text{N/mm}^2$):
    * M6 ($P=1{,}0$): $21{,}3\,\text{mm} \rightarrow \mathbf{3{,}55 \cdot d}$
    * M8 ($P=1{,}25$): $27{,}9\,\text{mm} \rightarrow \mathbf{3{,}49 \cdot d}$
    * M10 ($P=1{,}5$): $34{,}5\,\text{mm} \rightarrow \mathbf{3{,}45 \cdot d}$
    * M12 ($P=1{,}75$): $41{,}2\,\text{mm} \rightarrow \mathbf{3{,}43 \cdot d}$
    *(Hinweis: Liegt im Bereich $m_{\text{ges}} > 3 \cdot d$, vom Autor rot hervorgehoben als fertigungstechnisch zu vermeiden).*
  * **Alu-Gusslegierung mit $\tau_B = 100\,\text{N/mm}^2$** (z. B. weicher Sandguss G-AlSi12 / AlSi10Mg ungehärtet, $R_m \approx 192\,\text{N/mm}^2$):
    * M6: $17{,}1\,\text{mm} \rightarrow \mathbf{2{,}85 \cdot d}$ | M8: $22{,}3\,\text{mm} \rightarrow \mathbf{2{,}79 \cdot d}$ | M10: $27{,}6\,\text{mm} \rightarrow \mathbf{2{,}76 \cdot d}$
  * **Alu-Gusslegierung mit $\tau_B = 130\,\text{N/mm}^2$** (z. B. AlSi10Mg T6 wärmebehandelt oder AlSi9Cu3 Druckguss, $R_m \approx 250\,\text{N/mm}^2$):
    * M6: $13{,}6\,\text{mm} \rightarrow \mathbf{2{,}27 \cdot d}$ | M8: $17{,}8\,\text{mm} \rightarrow \mathbf{2{,}23 \cdot d}$ | M10: $21{,}9\,\text{mm} \rightarrow \mathbf{2{,}19 \cdot d}$
  * **G-AlCu4MgTi K T4** ($R_m = 320\,\text{N/mm}^2$, $\tau_B = 166\,\text{N/mm}^2$):
    * M6: $10{,}9\,\text{mm} \rightarrow \mathbf{1{,}82 \cdot d}$ | M8: $14{,}2\,\text{mm} \rightarrow \mathbf{1{,}78 \cdot d}$ | M10: $17{,}5\,\text{mm} \rightarrow \mathbf{1{,}75 \cdot d}$
* **Wörtliches Zitat:**
  > *„Bei der Berechnung der Zahlenwerte wurden die beiden Gewindegänge, die nicht mittragen, bereits berücksichtigt und der effektiven Einschraubtiefe hinzuaddiert... Bei Materialpaarungen mit besonders großen Unterschieden der Festigkeiten von Schraube und Innengewinde werden sehr hohe Einschraubtiefen ermittelt. Dies verursacht Probleme in der Herstellung und in der Anwendung der Schraubverbindung (Gewindebohren, „Festfressen“ bei der Montage). Kritisch angesehen werden Einschraubtiefen ab einer Länge von 1.5*d [1]. Je länger die Einschraubtiefen werden, desto problematischer sind die Effekte. Fertigungstechnisch wird empfohlen, Gewindebohrungen länger als 3*d zu vermeiden.“*

### 3. Quelle: Böllhoff Gruppe (HELICOIL® Plus Katalog 0100)
* **URL:** [Böllhoff HELICOIL® Plus Gesamtkatalog PDF](https://media.boellhoff.com/files/pdf13/0100-helicoil-plus-at-de.pdf)
* **Genaue Bedingung:** Nennlängenbestimmung für Gewindeeinsätze in Aluminium sowie Werkstoffen mit Scherspannung/Zugspannung $= 0{,}6 \text{ bis } 0{,}7$ bei Schraubenfestigkeitsklasse 8.8 (S. 13):
  * $R_m \le 100\,\text{N/mm}^2$: **$3{,}5 \cdot d$**
  * $R_m > 100 \text{ bis } 200\,\text{N/mm}^2$ (weicher Aluguss): **$2{,}5 \cdot d$**
  * $R_m > 200 \text{ bis } 300\,\text{N/mm}^2$ (z. B. AlSi10Mg): **$1{,}5 \cdot d$**
  * $R_m > 300\,\text{N/mm}^2$: **$1{,}5 \cdot d$**
* **Wörtliches Zitat:**
  > *„Die Richtwerte sind so bemessen, dass in der Verbindung die Schraube das schwächere Glied ist. Die empfohlenen Nennlängen können unterschritten werden, wenn Versuche dies bestätigen.“*

### 4. Quelle: SFS Group / Hoffmann Group (Technisches Handbuch Verbindungstechnik)
* **URL:** [Hoffmann Group / SFS Technisches Handbuch – Mindesteinschraubtiefe PDF](https://assets.hoffmann-group.com/media/ch/sfs_ch/broschueren_1/technisches_handbuch_fuer_verbindungstechnik/dimensionierung/allgemeines/Mindesteinschraubtiefe_in_geschnittene_Bauteilmuttergewinde_DE.pdf)
* **Genaue Bedingung:** Schraubenklasse 8.8 Regelgewinde:
  * AlMg3 F18 ($R_m > 180\,\text{N/mm}^2$): **$2{,}0 \cdot d$**
  * AlMgSi1 F32 ($R_m > 330\,\text{N/mm}^2$): **$1{,}4 \cdot d$**
* **Wörtliches Zitat (S. 153–154):**
  > *„Dieses Verhältnis liegt bei Vergütungs- [...] stahl zwischen 0,65 und 0,85, bei lösungsgeglühtem Austenit [...] bei 0,8, bei Aluminiumlegierungen zwischen 0,52 und 0,6“*

### 5. Quelle: DIN-Normung Stiftschrauben (DIN 835 / DIN 940)
* **URL:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf), S. TI-20 (DIN 835).
* **Genaue Bedingung:** Einschraubende $b_1$ für Stiftschrauben in Leichtmetalle / Aluminiumlegierungen.
  * DIN 835: **$e \approx 2{,}0 \cdot d$**
  * DIN 940: **$e \approx 2{,}5 \cdot d$**
* **Wörtliches Zitat:**
  > *„Stiftschrauben [...] DIN 835 [...] Einschraubende ≈ 2 d“*
* **Prüfstatus:** teilbelegt (DIN 835 in Reyher TI-20 belegt; DIN 940 nach DIN-Normblatt).

---

## b) Messing (z. B. CuZn39Pb3, CuZn37)

Messing besitzt typischerweise Zugfestigkeiten zwischen $360 \text{ und } 540\,\text{N/mm}^2$ (je nach Kaltverfestigungsgrad) und Scherfestigkeiten von $\tau_B \approx 250 \text{ bis } 350\,\text{N/mm}^2$.

### 1. Hersteller Bossard, Würth, Fabory
* **Ergebnis:** **Keine Quelle gefunden.** In den allgemeinen Auslegungstabellen für Mindesteinschraubtiefen (z. B. Bossard Handbuch Blatt 52, SFS/Hoffmann Handbuch S. 153) ist Messing nicht explizit tabelliert (dort werden fast ausschließlich Stähle, Grauguss und Aluminium geführt).

### 2. Quelle: VDI 2230 Blatt 1 / Schweizer-FN Maschinenbau
* **URL:** [Schweizer-FN Maschinenelemente – Schraubenverbindungen](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php#einschraubtiefe)
* **Genaue Bedingung:** Werkstoffgruppe *„Kupferlegierungen“*, Schraubenfestigkeitsklasse 8.8, metrisches Regelgewinde.
* **Faktor:** **`-` (kein Wert angegeben / in VDI 2230 Tabelle nicht belegt)**. (Hinweis: Für die niedrigeren Klassen 3.6–6.8 nennt die Tabelle $1{,}3 \cdot d$, lässt 8.8 jedoch leer).
* **Wörtliches Zitat:**
  > *„Kupferlegierungen“*

### 3. Quelle: JUS Spanntechnik (Festigkeitsauslegung nach VDI-Prinzip)
* **URL:** [JUS Spanntechnik – Gewindelänge & Einschraubtiefe berechnen](https://jus-spanntechnik.de/ratgeber/gewindelaenge-berechnen/)
* **Genaue Bedingung:** Schraubenklasse 8.8, Innengewindewerkstoff Messing ($R_m = 380\,\text{N/mm}^2$, Scherfestigkeitsverhältnis $\tau_B/R_m = 0{,}60 \rightarrow \tau_B \approx 228\,\text{N/mm}^2$).
* **Faktor:** Rechnerisch ca. **$1{,}2 \cdot d \text{ bis } 1{,}4 \cdot d$** (tragend) bzw. inklusive Auslaufzuschlag ca. **$1{,}4 \cdot d \text{ bis } 1{,}6 \cdot d$**.
* **Wörtliches Zitat:**
  > *„Scherfestigkeit des Bauteilwerkstoffs (≈ 0,6 · Rm,M)“*

### 4. Quelle: Auswertungsdiagramm nach VDI 2230 (SFS / Hoffmann Group Handbuch, S. 154)
* **URL:** [Hoffmann Group / SFS Technisches Handbuch PDF](https://assets.hoffmann-group.com/media/ch/sfs_ch/broschueren_1/technisches_handbuch_fuer_verbindungstechnik/dimensionierung/allgemeines/Mindesteinschraubtiefe_in_geschnittene_Bauteilmuttergewinde_DE.pdf)
* **Genaue Bedingung:** Bezogene Einschraubtiefe $m_{\text{eff}}/d$ über die Scherfestigkeit für Schraubenklasse 8.8:
  * Bei weicherem Messing ($\tau_B \approx 250\,\text{N/mm}^2$): $m_{\text{eff}} \approx 1{,}05 \cdot d \rightarrow m_{\text{ges}} \approx \mathbf{1{,}3 \cdot d \text{ bis } 1{,}4 \cdot d}$.
  * Bei halbhartem Automatenmessing CuZn39Pb3 ($\tau_B \approx 320\,\text{N/mm}^2$): $m_{\text{eff}} \approx 0{,}8 \cdot d \rightarrow m_{\text{ges}} \approx \mathbf{1{,}1 \cdot d \text{ bis } 1{,}2 \cdot d}$.
* **Wörtliches Zitat:**
  > *„Somit gilt für die Gesamt- [...] einschraubtiefe m ges = meff + mzu.“*

---

## c) Thermoplaste bei Direktverschraubung & Gewindeeinsätze im 3D-Druck

### 1. Direktverschraubung in Thermoplaste (Spezialschrauben wie EJOT DELTA PT®, Bossard ecosyn®-plast)

*(Hinweis zur Bedingung: Eine Standard-8.8-Schraube mit metrischem Regelgewinde darf **nicht** direkt in Thermoplaste geschraubt werden. Die VDI 2230 listet für 8.8 in Kunststoff einen Strich `-`. Direktverschraubungen erfolgen mit gewindefurchenden Spezialschrauben mit 30°-Flankenwinkel).*

#### Quelle A: EJOT / Bossard (DELTA PT® Konstruktionsrichtlinie)
* **URL:** [Bossard / EJOT DELTA PT® Broschüre PDF](https://www.smw-schrauben.ch/userdata/uploads/Dokumente/delta-pt-de(1).pdf)
* **Genaue Bedingung:** Gewindefurchende Direktverschraubung in Thermoplaste mit einem Elastizitätsmodul bis $E = 20\,000\,\text{N/mm}^2$.
* **Faktor:** **$t_e = 2 \times d_1$** ($d_1 = \text{Nenndurchmesser}$).
* **Wörtliches Zitat (S. 4):**
  > *„Für alle gängigen Kunststoffe bis E = 20’000 N/mm2. [...] Einschraubtiefe te = 2 x d1“*

#### Quelle B: Bossard AG (ecosyn®-plast Handbuch)
* **URL:** [Bossard ecosyn®-plast Katalog 0901 PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3AYmJ7h7169wKygbbUg0MK/dc07d87c865ade977f525121ea756759/0901_ecosyn_plast_DE.pdf)
* **Genaue Bedingung:** Werkstoffspezifische Tubusauslegung für ecosyn®-plast Schrauben in Thermoplasten (S. 5):
  * **ABS / PC-Blend:** **$2{,}00 \times d_1$** (Vorloch $0{,}80 \times d_1$)
  * **PA 6 / PA 6.6:** **$1{,}70 \times d_1$**
  * **PA 6 - GF 30:** **$1{,}90 \times d_1$** | **PA 6.6 - GF 30:** **$1{,}80 \times d_1$**
  * **POM:** **$2{,}00 \times d_1$**
  * **PP:** **$2{,}00 \times d_1$**
  * **PC (Polycarbonat):** **$2{,}20 \times d_1$** (Vorloch $0{,}85 \times d_1$)
  * **PPO:** **$2{,}20 \times d_1$**
  * **PE (weich):** **$2{,}00 \times d_1$** | **PE (hart):** **$1{,}80 \times d_1$**
* **Wörtliches Zitat:**
  > *„Für eine optimale Konstruktion, die sich in der Praxis bewährt, ist es erforderlich die Tubusgeometrie den unterschiedlichen Werkstoffen anzupassen. Die angegebenen Werte basieren auf umfassenden Laborversuchen mit Modellkörpern.“*

---

### 2. Gewindeeinsätze für Thermoplaste / 3D-Druck

#### Quelle A: Böllhoff Gruppe (AMTEC® Präzisionsgewindeeinsätze, Katalog 0200)
* **URL:** [Böllhoff AMTEC® Katalog 0200 PDF](https://media.boellhoff.com/files/pdf1/amtec-praezisionsgewindeeinsaetze-fuer-kunststoffbauteile-de-0200.pdf)
* **Genaue Bedingung:** Wärmeeinbett-Einsätze HITSERT® 2 (Werkstoff Messing CuZn38Pb2 / CuZn39Pb3) in thermoplastischen Formteilen:
  * **Einsatz-Nennlängen:**
    * M2: $l = 5{,}0\,\text{mm} \rightarrow \mathbf{2{,}50 \cdot d}$
    * M2,5: $l = 5{,}0\,\text{mm} \rightarrow \mathbf{2{,}00 \cdot d}$
    * M3: $l = 5{,}0\,\text{mm} \rightarrow \mathbf{1{,}67 \cdot d}$ bzw. $5{,}5\,\text{mm} \rightarrow \mathbf{1{,}83 \cdot d}$
    * M4: $l = 6{,}0\,\text{mm} \rightarrow \mathbf{1{,}50 \cdot d}$
    * M5: $l = 7{,}0\,\text{mm} \rightarrow \mathbf{1{,}40 \cdot d}$
  * **Schraubeneingriffslänge im Einsatz:**
    * Vorgabe: **$\text{Länge des Einsatzes } (l) + 1 \cdot P$** (Gewindesteigung).
* **Wörtliches Zitat (S. 41):**
  > *„➂ Schraubeneingriffslänge = min. Länge des Gewindeeinsatzes (l) + 1p (Steigung)“*

#### Quelle B: ruthex® (Standard für FDM/FFF-3D-Druck in PLA, PETG, ABS, PA)
* **URL:** [ruthex Gewindeeinsatz RX-M3x5.7 Produktseite](https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen)
* **Genaue Bedingung:** Einschmelzgewindeeinsätze (Messing) für 3D-gedruckte Bauteile (PLA, PETG, ABS, ASA, PA). Das Mutterngewinde wird im Messingeinsatz abgebildet:
  * **M2 (RX-M2x4):** $L = 4{,}0\,\text{mm} \rightarrow \mathbf{2{,}00 \cdot d}$
  * **M2,5 (RX-M2.5x5.7):** $L = 5{,}7\,\text{mm} \rightarrow \mathbf{2{,}28 \cdot d}$
  * **M3 (RX-M3x5.7):** Standard $L = 5{,}7\,\text{mm} \rightarrow \mathbf{1{,}90 \cdot d}$ (Short-Variante RX-M3Sx4.0: $4{,}0\,\text{mm} \rightarrow \mathbf{1{,}33 \cdot d}$)
  * **M4 (RX-M4x8.1):** Standard $L = 8{,}1\,\text{mm} \rightarrow \mathbf{2{,}025 \cdot d}$ (Short-Variante RX-M4Sx4.0: $4{,}0\,\text{mm} \rightarrow \mathbf{1{,}00 \cdot d}$)
  * **M5 (RX-M5x9.5):** Standard $L = 9{,}5\,\text{mm} \rightarrow \mathbf{1{,}90 \cdot d}$
  * **M6 (RX-M6x12.7):** Standard $L = 12{,}7\,\text{mm} \rightarrow \mathbf{2{,}12 \cdot d}$ (Short: $6{,}8\,\text{mm} \rightarrow \mathbf{1{,}13 \cdot d}$)
  * **M8 (RX-M8x12.7):** Standard $L = 12{,}7\,\text{mm} \rightarrow \mathbf{1{,}59 \cdot d}$
* **Wörtliches Zitat:**
  > *„Optimal für alle gängigen thermoplastischen Werkstoffe wie PLA, PETG, ABS, PP, PPS und mehr.“*

---

## d) Zum Vergleich: Stahl und Grauguss

### 1. Quelle: Bossard AG (Handbuch Blatt 52)
* **URL:** [Bossard Technische Informationen – Einschraubtiefe PDF](https://assets.eu.ctfassets.net/0vp0u5uh75zd/3wPlDC2XQOYT3XOdwCk6lz/78349182054251c341bf2565b01f69c9/052_Einschraubtiefe_Fastening_DE_01_2025.pdf)
* **Genaue Bedingung:** Schraubenklasse 8.8, Regelgewinde, Toleranz 6g/6H:
  * **Baustahl S235 / St37-2** ($R_m > 360\,\text{N/mm}^2$): **$1{,}0 \cdot d$** (Versuchswert) bzw. **$[1{,}5 \cdot d]$** (VDI 2230)
  * **Baustahl S355 / St52-3** ($R_m > 500\,\text{N/mm}^2$): **$0{,}9 \cdot d$** (Versuchswert) bzw. **$[1{,}3 \cdot d]$** (VDI 2230)
  * **Vergütungsstahl C45 V / 42CrMo4 V** ($R_m > 800\,\text{N/mm}^2$): **$0{,}8 \cdot d$** (Versuchswert) bzw. **$[0{,}9 \cdot d]$** (VDI 2230)
  * **Grauguss GJL 250 (GG-25)** ($R_m > 220\,\text{N/mm}^2$): **$1{,}0 \cdot d$** (Versuchswert) bzw. **$[1{,}3 \cdot d]$** (VDI 2230)
* **Wörtliches Zitat:**
  > *„S235 (St37-2) [...] 1,0 · d             1,25 · d                    1,25 · d            1,4 · d             1,4 · d“*

### 2. Quelle: Ingenieurbüro Andreas Hanke (VDI 2230-1:2015 Tabellen)
* **URLs:** 
  * [Hanke – Mindesteinschraubtiefe Baustahl PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-Baustahl-Scherfestigkeitsverh%C3%A4ltnis0.8.pdf)
  * [Hanke – Mindesteinschraubtiefe GJL PDF](https://www.ing-hanke.de/wp-content/uploads/2019/10/Mindesteinschraubtiefe-hochfester-Schrauben-mit-metrischem-Regelgewinde-nach-VDI-2230-Blatt-1-GJL-Scherfestigkeitsverh%C3%A4ltnis1.15.pdf)
* **Genaue Bedingung:** Schraubenklasse 8.8, Regelgewinde, $m_{\text{ges}} = m_{\text{eff}} + 2 \cdot P$:
  * **Baustahl S235** ($R_m = 330\,\text{N/mm}^2, \tau_B = 264\,\text{N/mm}^2, \tau_B/R_m = 0{,}80$):
    * M6: $8{,}2\,\text{mm} \rightarrow \mathbf{1{,}37 \cdot d}$ | M8: $10{,}6\,\text{mm} \rightarrow \mathbf{1{,}33 \cdot d}$ | M10: $13{,}0\,\text{mm} \rightarrow \mathbf{1{,}30 \cdot d}$ | M12: $15{,}4\,\text{mm} \rightarrow \mathbf{1{,}28 \cdot d}$
  * **Baustahl S355** ($R_m = 450\,\text{N/mm}^2, \tau_B = 360\,\text{N/mm}^2$):
    * M6: $6{,}8\,\text{mm} \rightarrow \mathbf{1{,}13 \cdot d}$ | M8: $8{,}8\,\text{mm} \rightarrow \mathbf{1{,}10 \cdot d}$ | M10: $10{,}7\,\text{mm} \rightarrow \mathbf{1{,}07 \cdot d}$ | M12: $12{,}6\,\text{mm} \rightarrow \mathbf{1{,}05 \cdot d}$
  * **Grauguss GJL-100** ($R_m = 100\,\text{N/mm}^2, \tau_B = 115\,\text{N/mm}^2, \tau_B/R_m = 1{,}15$):
    * M6: $15{,}1\,\text{mm} \rightarrow \mathbf{2{,}52 \cdot d}$ | M8: $19{,}8\,\text{mm} \rightarrow \mathbf{2{,}48 \cdot d}$ | M10: $24{,}4\,\text{mm} \rightarrow \mathbf{2{,}44 \cdot d}$
  * **Grauguss GJL-200** ($R_m = 200\,\text{N/mm}^2, \tau_B = 230\,\text{N/mm}^2$):
    * M6: $8{,}9\,\text{mm} \rightarrow \mathbf{1{,}48 \cdot d}$ | M8: $11{,}6\,\text{mm} \rightarrow \mathbf{1{,}45 \cdot d}$ | M10: $14{,}2\,\text{mm} \rightarrow \mathbf{1{,}42 \cdot d}$
  * **Grauguss GJL-250** ($R_m = 250\,\text{N/mm}^2, \tau_B = 288\,\text{N/mm}^2$):
    * M6: $7{,}8\,\text{mm} \rightarrow \mathbf{1{,}30 \cdot d}$ | M8: $10{,}0\,\text{mm} \rightarrow \mathbf{1{,}25 \cdot d}$ | M10: $12{,}3\,\text{mm} \rightarrow \mathbf{1{,}23 \cdot d}$

### 3. Quelle: Schweizer-FN / Europa Lehrmittel (Tabellenbuch Metall) & VDI 2230
* **URL:** [Schweizer-FN Schraubenverbindung](https://www.schweizer-fn.de/maschinenelemente/schraube/schraubenverbindung.php#einschraubtiefe)
* **Genaue Bedingung:** Schraubenklasse 8.8, Regelgewinde:
  * Stahl auf Stahl (gleiche Festigkeitsklasse): **$0{,}8 \cdot d$** [Tabellenbuch Metall]
  * St37 ($d/P < 9$): **$1{,}0 \cdot d$**; ($d/P \ge 9$): **$1{,}25 \cdot d$** [Tabellenbuch Metall]
  * Baustahl $R_m = 400 - 600\,\text{N/mm}^2$: **$1{,}2 \cdot d$** [VDI 2230]
  * C45V ($d/P < 9$): **$0{,}8 \cdot d$**; ($d/P \ge 9$): **$0{,}9 \cdot d$** [Tabellenbuch Metall]
  * Gusseisenwerkstoffe allgemein: **$1{,}5 \cdot d$** [VDI 2230]
  * GG-22 ($d/P < 9$): **$1{,}0 \cdot d$**; ($d/P \ge 9$): **$1{,}2 \cdot d$** [Tabellenbuch Metall]

### 4. Quelle: DIN-Normung Stiftschrauben (DIN 938 / DIN 939)
* **URL:** [Reyher Technische Informationen PDF](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf), S. TI-20 (DIN 938, DIN 939).
* **Faktor & Werkstoff:**
  * DIN 938 (Stahl): **$e \approx 1{,}0 \cdot d$**
  * DIN 939 (Grauguss): **$e \approx 1{,}25 \cdot d$**
* **Wörtliches Zitat:**
  > *„DIN 938 = mit Einschraubende ≈ 1 d [...] DIN 939 = mit Einschraubende ≈ 1,25 d“*

---

## Gegenüberstellung und Widerspruchsanalyse

| Werkstoffgruppe | Praxis-/Versuchswerte & Tabellenbuch | Theoretische Berechnung VDI 2230-1 | Normung Stiftschrauben |
| :--- | :--- | :--- | :--- |
| **Baustahl (S235)** | $0{,}8 \cdot d \dots 1{,}0 \cdot d$ (Bossard, Schweizer-FN) | $1{,}3 \cdot d \dots 1{,}5 \cdot d$ (Hanke, Bossard VDI) | $1{,}0 \cdot d$ (DIN 938) |
| **Grauguss (GJL-200/250)** | $1{,}0 \cdot d \dots 1{,}25 \cdot d$ (Bossard, Schweizer-FN) | $1{,}25 \cdot d \dots 1{,}5 \cdot d$ (Hanke, VDI 2230) | $1{,}25 \cdot d$ (DIN 939) |
| **Aluminium-Guss** | $1{,}4 \cdot d \dots 2{,}0 \cdot d$ (Bossard, JUS) | $2{,}2 \cdot d \dots 3{,}5 \cdot d$ (Hanke, Bossard VDI) | $2{,}0 \cdot d \dots 2{,}5 \cdot d$ (DIN 835 / 940) |
| **Messing (CuZn)** | $1{,}2 \cdot d \dots 1{,}5 \cdot d$ (JUS, Fachpraxis) | $1{,}25 \cdot d \dots 1{,}4 \cdot d$ (VDI-Diagramm) | *(keine gesonderte DIN-Stiftschraube)* |
| **Thermoplaste (Direkt)** | $1{,}7 \cdot d \dots 2{,}2 \cdot d$ (Bossard ecosyn, EJOT DELTA PT) | Keine Normschraube 8.8 zulässig (`-`) | *(nicht genormt)* |
| **3D-Druck (Einsätze)** | $1{,}9 \cdot d \dots 2{,}1 \cdot d$ (ruthex, Böllhoff AMTEC) | Gewindetragung im Messingeinsatz | *(herstellerspezifisch)* |

### Ursachen der Abweichungen:
1. **Reine Gewindeüberdeckung ($m_{\text{eff}}$) vs. Gesamteinschraubtiefe ($m_{\text{ges}}$):** Tabellenbücher und Hersteller (z. B. Bossard) listen oft die reine tragende Überdeckung $m_{\text{eff}}$. Rechner nach VDI 2230 (z. B. Hanke) schlagen stets $2 \cdot P$ für Ansenkung und Schraubenkuppe auf, was bei kleinen Abmessungen (z. B. M6) bis zu $+0{,}33 \cdot d$ Unterschied ausmacht.
2. **Plastifizierung im Kerbgrund:** In der Realität plastifizieren die ersten 2 bis 3 Gewindegänge bei hoher Vorspannung lokal, wodurch nachfolgende Gänge stärker mittragen, als die streng elastische VDI-Berechnung modelliert. Dadurch erzielen empirische Versuche (Bossard) bereits bei $1{,}0 \cdot d$ (Stahl) oder $2{,}0 \cdot d$ (Alu) die Schraubenbruchlast.
3. **Fertigungsgrenze ($1{,}5 \cdot d$ bis $3{,}0 \cdot d$):** Bei tiefen Gewindebohrungen führen Steigungsfehlertoleranzen nach ISO 965-1 zum Klemmen oder Festfressen. Einschraubtiefen $> 3 \cdot d$ werden in der Fertigungspraxis strikt vermieden.

---

## Empfehlung und Begründung

### 1. Für „Aluguss unbekannter Legierung“: **$2{,}0 \cdot d$ bis $2{,}5 \cdot d$**
* **Begründung:** Unbekannter Aluguss kann eine weiche Sandgusslegierung (z. B. AlSi12 mit $R_m \approx 150\,\text{N/mm}^2, \tau_B \approx 78\,\text{N/mm}^2$) oder ein festerer Druckguss (z. B. AlSi10Mg oder AlSi9Cu3 mit $R_m > 240\,\text{N/mm}^2$) sein. 
* Eine rein rechnerische Auslegung für den ungünstigsten Sandguss ergäbe nach VDI 2230 rechnerisch über $3{,}0 \cdot d$. Solche Tiefen sind jedoch fertigungstechnisch unbrauchbar (Gefahr von Werkzeugbruch beim Gewindebohren und Klemmen der Schraube durch Steigungstoleranzen). 
* Ein Faktor von **$2{,}0 \cdot d$ (effektiv tragend) bzw. $2{,}5 \cdot d$ (Nenntiefe im Sackloch)** deckt sich mit der Stiftschraubennormung DIN 940 ($2{,}5 \cdot d$), DIN 835 ($2{,}0 \cdot d$) sowie den empirischen Grenzwerten von Bossard und Böllhoff.
* *Wichtiger Konstruktionshinweis:* Muss die 8.8er Schraube bis an ihre volle Streckgrenze ($R_{p0{,}2} = 640\,\text{N/mm}^2$) vorgespannt werden, sollte in Aluguss unbekannter Güte **nicht** tiefer als $2{,}0 \cdot d$ geschnitten, sondern zwingend ein drahtgewickelter Gewindeeinsatz (z. B. Böllhoff HELICOIL® Plus mit $1{,}5 \cdot d$ bis $2{,}0 \cdot d$) oder selbstdurchschneidender Einsatz (Kerb-Konus Ensat®) vorgesehen werden.

### 2. Für „Messing“: **$1{,}5 \cdot d$**
* **Begründung:** Gängiges Messing (insbesondere Automatenmessing CuZn39Pb3 / CW614N oder CuZn37) besitzt im gezogenen Zustand eine Zugfestigkeit von $R_m \approx 360 \text{ bis } 500\,\text{N/mm}^2$ und eine Scherfestigkeit von $\tau_B \approx 250 \text{ bis } 320\,\text{N/mm}^2$. Es ist damit deutlich scherfester als Aluminiumguss, erreicht aber nicht die Werte von Vergütungsstahl.
* Gemäß dem VDI-Berechnungsdiagramm benötigt eine 8.8-Schraube bei $\tau_B \approx 250\,\text{N/mm}^2$ eine effektive Mindesteinschraubtiefe von $m_{\text{eff}} \approx 1{,}05 \cdot d$. 
* Mit dem fertigungstechnischen Sicherheitszuschlag von $2 \cdot P$ für die unvollständigen Anschnittgänge und die Bohrungsfase ergibt sich eine Gesamteinschraubtiefe von ca. $1{,}3 \cdot d$ bis $1{,}4 \cdot d$. 
* Ein Faktor von **$1{,}5 \cdot d$** ist für Messing konservativ, bietet Sicherheitsreserven gegen Chargenschwankungen und liegt noch unterhalb der kritischen Klemmschwelle langer Gewinde.

### 3. Für „Kunststoff direkt“: **$2{,}0 \cdot d$** (nur mit Thermoplast-Spezialschrauben!)
* **Begründung:** 
  * Eine direkte Verschraubung mit einer metrischen 8.8-Regelgewindeschraube in Thermoplasten ist **technisch unzulässig**. Der 60°-Flankenwinkel erzeugt zu hohe Radialkräfte (Aufplatzen des Doms), und die geringe Steigung schert die dünnen Kunststoffstege sofort ab.
  * Für die Direktverschraubung müssen gewindefurchende Thermoplastschrauben mit 30°-Flankenwinkel verwendet werden (z. B. EJOT DELTA PT®, Bossard ecosyn®-plast).
  * Für diese Schrauben ist ein Faktor von **$t_e = 2{,}0 \cdot d$** (bzw. $2{,}0 \times d_1$) der herstellerübergreifende Standard für fast alle technischen Kunststoffe (PP, PA, POM, ABS, PBT). Lediglich bei extrem kerbempfindlichen Thermoplasten wie unmodifiziertem Polycarbonat (PC) empfiehlt Bossard $2{,}2 \cdot d$.
  * Werden im 3D-Druck (FDM/FFF mit PLA, PETG, ABS) metrische 8.8-Schrauben eingesetzt, erfolgt die Verbindung über **Gewindeeinsätze aus Messing** (z. B. ruthex®, Böllhoff AMTEC® HITSERT). Deren Standard-Einbaulänge liegt herstellerseitig bei **$1{,}9 \cdot d \text{ bis } 2{,}1 \cdot d$** (z. B. ruthex M3x5.7 entspricht $1{,}90 \cdot d$, M4x8.1 entspricht $2{,}02 \cdot d$), was die Last gleichmäßig im Schichtverbund verteilt.
