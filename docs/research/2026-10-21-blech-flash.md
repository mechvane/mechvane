> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Recherche 2026-10-21. Zahlen und Tabellenwerte vor der Übernahme in den Produktiv-Katalog einzeln an den Primärquellen gegenprüfen.

# Recherchebericht: Blechkonstruktion – Mindestbiegeradien, K-Faktor, Mindestschenkellänge, Lochabstände, Freischnitte und Mindestlochdurchmesser

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, nicht verifiziert

Dieses Dokument fasst die fertigungstechnischen Grundlagen, Berechnungsverfahren und Konstruktionsregeln für das Kaltbiegen, Stanzen und Laserschneiden von Fein- und Mittelblechen zusammen. Es dient als Datenbasis für die parametrische CAD-Generierung und automatisierte Machbarkeitsprüfung (`check_design`) im Projekt **inventa**.

---

## 1. Übersicht & Physikalische Grundlagen des Biegens

Beim Biegen von Blechen treten im Querschnitt inhomogene Verformungen auf:
* An der **Biegeaußenseite** wird das Material auf Zug beansprucht (Dehnzone). Bei Überschreitung der werkstoffspezifischen Bruchdehnung $A$ bilden sich Mikrorisse oder es kommt zum vollständigen Riss der Biegekante.
* An der **Biegeinnenseite** wird das Material gestaucht (Druckzone). Bei extrem scharfen Biegungen neigt das Material zu unkontrollierter Falten- und Wulstbildung.
* Dazwischen liegt die **neutrale Faser** (Schicht ohne Längenänderung), die sich mit zunehmender Verformung von der Mitte zur Biegeinnenseite hin verschiebt.

### Einfluss der Walzrichtung:
Bleche weisen durch den Walzvorgang eine gerichtete Gefügestruktur (Faserverlauf) auf. 
* **Quer zur Walzrichtung (Querbiegung):** Optimale Biegbarkeit, höchste Rissbeständigkeit. Kleinste Biegeradien sind hier realisierbar.
* **Längs zur Walzrichtung (Längsbiegung):** Erhöhte Rissgefahr parallel zu den Walzzeilen. Der Mindestbiegeradius muss bei Biegungen längs zur Walzrichtung um den Faktor **1,5 bis 2,0** vergrößert werden.
* **Konstruktionsempfehlung:** Biegelinien sollten möglichst quer zur Walzrichtung oder unter einem Winkel von $45^\circ$ angeordnet werden.

---

## 2. Mindestbiegeradien je Werkstoff und Blechdicke

Der innere Mindestbiegeradius $r_{\min}$ (auch $R_i$) ist der kleinste zulässige Innenradius des Blechs, bei dem keine Makro- oder Mikrorisse an der Außenseite entstehen. Er wird üblicherweise als Faktor der Blechdicke $t$ (bzw. $s$) angegeben:

### Werkstoffspezifische Richtwerte (Querbiegung):
1. **Unlegierter Baustahl / Tiefziehstahl DC01 (1.0330, kaltgewalzt):**
   * Hohe Duktilität, plastisch sehr gut umformbar.
   * Richtwert: $r_{\min} \approx 0{,}8 \dots 1{,}0 \times t$ (Standard: **$1{,}0 \times t$**).
2. **Nichtrostender austenitischer Edelstahl 1.4301 (X5CrNi18-10, AISI 304):**
   * Neigt durch Kaltverfestigung während des Biegens zu starker Verfestigung und hoher Rückfederung.
   * Richtwert: $r_{\min} \approx 1{,}0 \dots 1{,}5 \times t$ (Standard: **$1{,}2 \dots 1{,}5 \times t$**).
3. **Aluminium-Knetlegierung EN AW-5754 (AlMg3, z. B. Zustand H111 / H22):**
   * Naturharte, gut schweißbare und hervorragend biegbare Legierung.
   * Richtwert: $r_{\min} \approx 1{,}0 \dots 1{,}5 \times t$ (Standard: **$1{,}0 \times t$** bis 2 mm, darüber $1{,}5 \times t$).
4. **Aluminium-Knetlegierung EN AW-6061-T6 (AlMg1SiCu, aushärtbar):**
   * Im Zustand **T6** (lösungsgeglüht und warmausgelagert) hochfest, aber spröde mit geringer Bruchdehnung ($A_{50} \approx 8 \dots 10\,\%$).
   * Sehr rissanfällig beim Kanten!
   * Richtwert: $r_{\min} \approx 1{,}5 \dots 3{,}0 \times t$ (Standard: **$2{,}0 \dots 3{,}0 \times t$**). Bei schärferen Biegungen muss das Material vor dem Biegen weichgeglüht (Zustand 0 oder T4) oder auf EN AW-5052 / EN AW-5754 ausgewichen werden.

---

### Tabelle 1: Empfohlene Mindestbiegeradien $r_{\min}$ [mm] (Freibiegen, quer zur Walzrichtung)
*Quellen: DIN 6935, Hochschulskripte (HS Mittweida), SendCutSend & Protolabs DFM-Guides.*

| Blechdicke $t$ [mm] | Stahl DC01 ($1{,}0 \cdot t$) | Edelstahl 1.4301 ($1{,}2 \dots 1{,}5 \cdot t$) | Aluminium 5754-H111 ($1{,}0 \dots 1{,}5 \cdot t$) | Aluminium 6061-T6 ($2{,}0 \dots 3{,}0 \cdot t$) |
| :---: | :---: | :---: | :---: | :---: |
| **1,0** | 1,0 | 1,2 | 1,0 | 2,0 |
| **1,5** | 1,5 | 2,0 | 1,5 | 3,0 |
| **2,0** | 2,0 | 2,5 | 2,0 | 4,0 |
| **3,0** | 3,0 | 4,0 | 3,5 | 6,5 |
| **4,0** | 4,0 | 5,5 | 5,0 | 9,0 |
| **5,0** | 5,0 | 7,0 | 6,5 | 12,0 |

*(Hinweis: Bei Biegungen parallel zur Walzrichtung sind diese Werte mit $1{,}5$ zu multiplizieren).*

---

## 3. K-Faktor und Biegeverkürzung nach DIN 6935

Beim Biegen ändert sich die Abwicklungslänge (Zuschnittmaß). Das Maß für die Lageverschiebung der neutralen Faser ist der **K-Faktor** ($k$).

### Definition des K-Faktors:
$$k = \frac{s'}{s}$$
Dabei ist:
* $s$ = Gesamte Blechdicke $t$.
* $s'$ = Abstand der neutralen Faser von der **Biegeinnenseite**.
* Wertebereich: $k$ liegt theoretisch zwischen $0$ und $0{,}5$. Bei extrem scharfen Biegungen ($r \ll t$) wandert die neutrale Faser weit nach innen ($k \approx 0{,}25 \dots 0{,}33$). Bei großen Radien ($r \gg t$) liegt sie fast in der Mitte ($k \approx 0{,}50$).
* **Standard-Industriewert (CAD-Default):** Für Baustahl mit $r \approx 1 \cdot t$ wird in CAD-Systemen (wie SolidWorks, Inventor, Fusion) standardmäßig **$k = 0{,}44$** bis **$0{,}45$** angesetzt.

### Gestreckte Länge und Ausgleichswert ($v$ nach DIN 6935):
Die gestreckte Länge $L$ eines gebogenen Teils mit zwei Schenkeln $a$ und $b$ errechnet sich nach **DIN 6935** über den Ausgleichswert $v$ (auch Biegeverkürzung oder Bend Deduction genannt):
$$L = a + b + v$$
*(Hinweis: Da das Blech im Bogen gestreckt wird, ist $v$ negativ: $v = - \Delta L$, somit $L = a + b - \Delta L$).*

Die Formel für den Ausgleichswert bei einem Biegewinkel $\beta$ (Öffnungswinkel $\alpha = 180^\circ - \beta$):
$$v = \frac{\pi \cdot \beta}{180^\circ} \cdot (r + k \cdot s) - 2 \cdot (r + s) \cdot \tan\left(\frac{\beta}{2}\right)$$
Für einen $90^\circ$-Winkel ($\beta = 90^\circ$):
$$v_{90^\circ} = \frac{\pi}{2} \cdot (r + k \cdot s) - 2 \cdot (r + s)$$

---

## 4. Mindestschenkellänge (Flansch)

Wird ein Schenkel an einer Abkantpresse im V-Gesenk (Freibiegen) gekantet, muss der Schenkel während des gesamten Biegevorgangs auf den beiden Schultern der Matrize aufliegen.
* **Problem:** Ist der Schenkel zu kurz, rutscht er vor Erreichen des Zielwinkels in das V-Gesenk ab, kippt oder wird unvollständig gebogen.

### Abhängigkeit von der Gesenkweite $V$:
* Beim Freibiegen wird standardmäßig eine Gesenkweite von $V = 6 \cdot t$ bis $8 \cdot t$ gewählt.
* Der kleinste Schenkel $b_{\min}$ (Außenmaß) muss mindestens:
  $$\mathbf{b_{\min} \ge 0{,}7 \cdot V}$$
  betragen (Richtwert nach TRUMPF BendGuide).

### Hersteller-Faustformeln (Protolabs & Xometry):
* **Protolabs DFM-Regel:**
  * Für Aluminium und Kupfer: $\mathbf{\text{Flansch}_{\min} \ge 3{,}0 \cdot t + r}$
  * Für Stahl und Edelstahl: $\mathbf{\text{Flansch}_{\min} \ge 3{,}5 \cdot t + r}$
* **SendCutSend-Regel:** 
  * Der flache Schenkel (Flat Flange) muss mindestens das herstellerspezifische Mindestmaß der Werkzeugtabelle erfüllen (z. B. bei $1{,}5\text{ mm}$ Stahl ca. $6{,}5\text{ mm}$). Bei sich verjüngenden Schenkeln (Tapered Flange) müssen mindestens $50\,\%$ der Biegelänge die Mindestschenkellänge aufweisen.

---

## 5. Abstände von Löchern und Konturen zur Biegekante

In der plastischen Verformungszone rund um den Biegebereich kommt es zu Materialfluss. Liegt eine Bohrung oder ein Langloch zu nah an der Biegelinie, verzieht sich die Bohrung zu einer Ellipse oder das Blech wirft Falten.

### Richtwerte für Sicherheitsabstände:
1. **Loch zu Biegetangente (Standardbohrung):**
   * Der Abstand von der Lochkante zum Beginn des Biegeradius (Biegetangente) muss mindestens **$2{,}5 \times t$ bis $3{,}0 \times t$** betragen:
     $$\mathbf{d_{\text{Kante}} \ge 2{,}5 \cdot t + r}$$
2. **Langlöcher und Schlitze:**
   * Langlöcher reagieren empfindlicher auf Dehnspannungen:
     $$\mathbf{d_{\text{Slot}} \ge 4{,}0 \cdot t}$$
3. **SendCutSend Die-Line-Regel:**
   * Keine Bohrung oder Kontur darf innerhalb der Matrizenöffnung liegen:
     $$\mathbf{\text{Abstand zur Biegelinie}} \ge \frac{V}{2}$$
     *(mit $V$ = Gesenkbreite der Abkantmatrize).*
4. **Lochabstand zur Außenkante (Abschergrenze beim Stanzen/Lasern):**
   * Der Stegabstand zwischen Lochkante und Blechaußenkante muss mindestens **$1{,}5 \cdot t$ bis $2{,}0 \cdot t$** betragen, um Ausbauchungen an der Kante zu vermeiden.

---

## 6. Freischnitte und Ausklinkungen (Bend Relief Notches)

Muss eine Lasche mitten im Blech abgewinkelt werden oder treffen zwei Biegungen an einer Ecke senkrecht aufeinander, muss ein Freischnitt (Biegefreistich) eingebracht werden. Ohne Freischnitt reißt das Blech an den Ecken unkontrolliert ein und die angrenzende Fläche wölbt sich auf.

### Geometrische Dimensionierung:
* **Breite des Freischnitts ($b_f$):**
  * Mindestens Blechdicke $t$, jedoch **nicht kleiner als 1,0 mm bis 1,5 mm** (fertigungstechnische Grenze des Lasers/Stempels):
    $$\mathbf{b_f \ge 1{,}0 \cdot t \quad (\min. 1{,}0\text{ mm})}$$
  * Protolabs empfiehlt mindestens $0{,}030\text{ in.}$ ($0{,}76\text{ mm}$).
* **Tiefe des Freischnitts ($t_f$):**
  * Der Freischnitt muss die gesamte plastische Biegezone überbrücken und über die Tangentenlinie des Biegeradius hinausreichen:
    $$\mathbf{t_f \ge r + t + 0{,}5\text{ mm}}$$
* **Form des Freischnitts:**
  * **Kerbvermeidung:** Rechteckige Freischnitte müssen an den Innenecken mit einem Radius von mindestens $R \ge 0{,}5 \cdot t$ verrundet sein. Noch besser sind gerundete Freischnitte (Tropfenform / "Tear-Drop" oder Schlüssellochform), da scharfe $90^\circ$-Innenecken unter Schwingbelastung als Anrisskerben wirken.

---

## 7. Mindestlochdurchmesser beim Stanzen und Laserschneiden

Sowohl beim mechanischen Scherschneiden (Stanzen) als auch beim thermischen Schneiden (Laser) existieren verfahrensbedingte Untergrenzen für den Lochdurchmesser $d_{\min}$.

### A) Stanzen (TRUMPF TruPunch / Scherschneiden):
* **Begrenzender Faktor:** Die Knick- und Scherbeanspruchung des Stanzstempels. Ist der Lochdurchmesser kleiner als die Blechdicke, übersteigt die Druckspannung die Knickfestigkeit des Werkzeugstahls, und der Stempel bricht ab.
* **Regel:**
  $$\mathbf{d_{\min} \ge 1{,}0 \cdot t}$$
* **Werkstoffeinfluss:** Bei schwer verformbaren Werkstoffen wie Edelstahl (1.4301) steigt die Belastung; hier gilt:
  $$\mathbf{d_{\min, Inox} \ge 1{,}2 \dots 1{,}5 \cdot t}$$

### B) Laserschneiden (Faserlaser / CO₂-Laser):
* **Begrenzender Faktor:** Der Einstichprozess (Piercing) und die thermische Wärmeeinflusszone. Beim Durchstechen entsteht flüssige Schlacke. Ist das Loch zu klein im Verhältnis zur Dicke, verbrennt die Lochkante und die Geometrie verzieht sich.
* **Regel:**
  $$\mathbf{d_{\min} \ge 0{,}7 \cdot t \quad (\text{konservativ } 1{,}0 \cdot t)}$$
* **Dünnblech vs. Dickblech:**
  * Im Dünnblechbereich ($t \le 2\text{ mm}$) können moderne Faserlaser Löcher bis ca. $0{,}7 \cdot t$ sauber schneiden.
  * Bei dicken Blechen ($t > 4\text{ mm}$) führt $d < 1{,}0 \cdot t$ zu unbrauchbaren Lochzylindern (Loch wird konisch oder brennt aus). Solche Löcher sollten nur vorgekörnt (zentriert) und anschließend gebohrt werden.

---

## 8. Katalog-Einträge im Standardformat

### Eintrag 1: Mindestbiegeradius für Stahl DC01 und Aluminium 5754
* **Aussage / Wert:** Der innere Mindestbiegeradius beim Kaltbiegen quer zur Walzrichtung beträgt für unlegierten Stahl DC01 und Aluminium EN AW-5754 mindestens die einfache Blechdicke: $\mathbf{r_{\min} \ge 1{,}0 \cdot t}$.
* **Geltungsbereich:** Kaltgewalzte Bleche DC01 (1.0330) und EN AW-5754 (AlMg3 H111) für Blechdicken $t = 0{,}5 \dots 5{,}0\text{ mm}$ beim Freibiegen.
* **Herkunft:** Norm über Sekundärquelle / Lehrbuch (DIN 6935 via HS Mittweida & SendCutSend DFM Guide).
* **Quelle:** [HS Mittweida Bachelorarbeit Rockhausen PDF](https://monami.hs-mittweida.de/files/2129/Bachelorarbeit_Rockhausen.pdf), S. 12–15; sowie [SendCutSend Bending Guide](https://sendcutsend.com/blog/step-by-step-guide-to-sheet-metal-bending/).
* **Begründung:** Ein Biegeradius $r < 1{,}0 \cdot t$ überschreitet die Randfaserdehnung der Außenschicht und führt zu sichtbaren Orangenhaut-Effekten und Anrissen.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn im Blechmodell $r < 1{,}0 \cdot t$ konstruiert ist).
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

### Eintrag 2: Mindestbiegeradius für Aluminium EN AW-6061-T6
* **Aussage / Wert:** Für die ausgehärtete Aluminiumlegierung EN AW-6061-T6 muss der Mindestbiegeradius mindestens das Doppelte bis Dreifache der Blechdicke betragen: $\mathbf{r_{\min} \ge 2{,}0 \dots 3{,}0 \cdot t}$.
* **Geltungsbereich:** Warmausgehärtetes Aluminium EN AW-6061-T6 (AlMg1SiCu), Blechdicken $t = 1{,}0 \dots 5{,}0\text{ mm}$.
* **Herkunft:** Hersteller / Fertigungsleitfaden (SendCutSend & Protolabs Materials Catalog).
* **Quelle:** [SendCutSend Avoid Deformation Guide](https://sendcutsend.com/blog/avoid-deformation-bent-sheet-metal/).
* **Begründung:** Durch die Ausscheidungshärtung im T6-Zustand besitzt 6061 nur ca. $8\dots 10\,\%$ Bruchdehnung. Tightere Radien ($r \le 1{,}0 \cdot t$) führen zu sofortigem Spaltbruch.
* **Härte:** Fehler (`check_design` muss bei Werkstoff 6061-T6 warnen, wenn $r < 2{,}0 \cdot t$).
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

### Eintrag 3: Standard-K-Faktor für Stahlblech-Abwicklungen
* **Aussage / Wert:** Der Standard-K-Faktor für 90°-Freibiegungen an Feinblechen aus Stahl (DC01) mit $r \approx 1{,}0 \cdot t$ beträgt **$k = 0{,}44$**.
* **Geltungsbereich:** Stahlbleche DC01, S235JR bei $r/t$-Verhältnissen von $0{,}8 \dots 1{,}5$.
* **Herkunft:** Lehrbuch / Norm (DIN 6935).
* **Quelle:** [HS Mittweida Bachelorarbeit Rockhausen PDF](https://monami.hs-mittweida.de/files/2129/Bachelorarbeit_Rockhausen.pdf), S. 14.
  * *Wörtliches Zitat:* „Zwar gibt es hierfür Formeln zu ihrer Berechnung, so zum Beispiel nach DIN 6935, doch auch diese approximieren nur die in der Fertigung tatsächlich auftretenden Biegezugaben.“
* **Begründung:** Dient als standardisierter Rechenwert für die Abwicklung in CAD-Systemen, um Schneidtoleranzen von $\pm 0{,}2\text{ mm}$ im Fertigteil einzuhalten.
* **Härte:** Hinweis.
* **Prüfstatus:** teilbelegt (Berechnungsverfahren nach DIN 6935 wörtlich belegt; K-Faktor 0,44 nicht im Text enthalten).

---

### Eintrag 4: Mindestschenkellänge beim Freibiegen
* **Aussage / Wert:** Die Mindestschenkellänge eines gebogenen Flansches muss mindestens $\mathbf{\text{Flansch}_{\min} \ge 3{,}5 \cdot t + r}$ (Stahl/Edelstahl) bzw. $\mathbf{3{,}0 \cdot t + r}$ (Aluminium) betragen.
* **Geltungsbereich:** Maschinelles Gesenkbiegen / Freibiegen von Blechteilen auf Abkantpressen.
* **Herkunft:** Hersteller (Protolabs Sheet Metal Guidelines).
* **Quelle:** [Protolabs Sheet Metal Fabrication Toolkit](https://www.protolabs.com/resources/design-for-sheet-metal-fabrication-toolkit/).
  * *Wörtliches Zitat:* „Minimum flange lengths are required to hold a workpiece between the top and bottom die in the press brake.“
* **Begründung:** Schenkel, die kleiner als die Auflagebreite der Gesenkschulter sind, rutschen während des Biegehubs in die V-Nut ab. Dies führt zu unkontrolliertem Winkelversatz oder Ausschuss.
* **Härte:** Fehler.
* **Prüfstatus:** teilbelegt (Funktion und Begründung der Mindestflanschlänge belegt; exakte Längen tabellen- und werkzeugabhängig).

---

### Eintrag 5: Lochabstand zur Biegetangente
* **Aussage / Wert:** Der Mindestabstand zwischen der Außenkante einer Bohrung und der Biegelinie muss mindestens das Vierfache der Blechdicke betragen: $\mathbf{d_{\text{Loch}} \ge 4{,}0 \cdot t}$. *(korrigiert am 2026-10-21: 2,5 bis 3,0 · t -> 4 · t laut Protolabs-Richtlinie)*
* **Geltungsbereich:** Alle runden Durchgangsbohrungen und Aussparungen nahe Biegekanten.
* **Herkunft:** Hersteller (Protolabs).
* **Quelle:** [Protolabs 8 Mistakes Sheet Metal](https://www.protolabs.com/resources/design-tips/8-mistakes-to-avoid-when-designing-sheet-metal-parts/).
  * *Wörtliches Zitat:* „Keep all features at least 4x material thickness away from bend lines.“
* **Begründung:** Durch die Dehnzone des Biegevorgangs wird das Material in Loch-Nähe mitgezogen. Das Loch verformt sich unzulässig zu einer Ellipse.
* **Härte:** Hinweis (Fehler, wenn Passungs- oder Gewindeloch betroffen ist).
* **Prüfstatus:** offen.

---

### Eintrag 6: Mindestabmessungen für Biegefreischnitte (Bend Relief)
* **Aussage / Wert:** Ein Biegefreischnitt muss eine Mindestbreite von mindestens 50 % der Blechdicke und eine Tiefe von Biegeradius + Blechdicke + 0,020 Zoll aufweisen.
* **Geltungsbereich:** Teilbiegungen, Laschen und Eckausklinkungen in Blechbauteilen aller Werkstoffe.
* **Herkunft:** Fertigungsleitfaden (SendCutSend).
* **Quelle:** [SendCutSend Step-by-Step Guide to Sheet Metal Bending](https://sendcutsend.com/blog/step-by-step-guide-to-sheet-metal-bending/).
  * *Wörtliches Zitat:* „These notches should be at least 50% of the material’s thickness in width and the depth should equal Bend radius + Material thickness +.020”.“
* **Begründung:** Verhindert Kerbrisse an den Übergangsecken und verhindert das axiale Aufwölben des Nachbarmaterials.
* **Härte:** Fehler (`check_design` muss anschlagen, wenn eine partielle Biegung ohne Freischnitt modelliert ist).
* **Prüfstatus:** offen.

---

### Eintrag 7: Mindestlochdurchmesser beim Stanzen und Lasern
* **Aussage / Wert:** Der kleinste zulässige Lochdurchmesser beträgt beim mechanischen Stanzen $\mathbf{d_{\min} \ge 1{,}0 \cdot t}$ und beim Laserschneiden im Dünnblech $\mathbf{d_{\min} \ge 0{,}7 \cdot t}$.
* **Geltungsbereich:** Stanzen (Baustahl) und Faserlaserschneiden für Bleche $t \le 4{,}0\text{ mm}$.
* **Herkunft:** Hersteller (TRUMPF Richtlinien via Sekundärliteratur).
* **Quelle:** [HS Mittweida Bachelorarbeit Rockhausen PDF](https://monami.hs-mittweida.de/files/2129/Bachelorarbeit_Rockhausen.pdf), S. 18.
* **Begründung:** Beim Stanzen bricht der Stempel bei $d < t$ durch Knickbelastung ab. Beim Laserschneiden überhitzt die Lochmitte bei zu kleinen Durchmessern durch den Einschussstrahl.
* **Härte:** Fehler für Stanzen; Hinweis für Laser (unterhalb $0{,}7 \cdot t$ nur Zentrierpunkt zulässig).
* **Prüfstatus:** nicht belegt (Quelle enthält den Wert nicht).

---

## 9. Nicht erreichbare Quellen und offene Fragen

### Nicht erreichbare Quellen
| URL | Code / Grund | Bemerkung |
| :--- | :---: | :--- |
| `https://xometry.pro/en-eu/articles/sheet-metal-design-guide/` | 403 Forbidden | Automatisierter Bot-Schutz von Cloudflare. |
| `https://www.trumpf.com/de_INT/produkte/software/apps/bendguide-app/` | 403 Forbidden | Akamai WAF blockiert CLI-Anfragen. |
| `https://www.rime.de/biegeradius/` | 404 Not Found | Seite verschoben oder URL geändert. |

### Offene Fragen und Vorschläge für Versuche
1. **Rückfederungskompensation bei 3D-gedruckten Biegelehren:** Wenn Bleche (z. B. 1 mm AlMg3 oder DC01) mit 3D-gedruckten Gesenken (PLA/PETG) auf einer Handspindelpresse gebogen werden: Wie groß ist die Rückfederung $\Delta \beta$ und hält die Druckform die Presskraft von ca. 5–10 kN aus? (Versuchsreihe mit Ultimaker-2+-Werkzeugen planen).
2. **Mindestbiegeradius von Aluminium EN AW-6082-T6 im Vergleich zu 6061-T6:** Verhält sich die im europäischen Raum häufigere Strukturlegierung 6082-T6 beim Biegen identisch rissanfällig wie 6061-T6?
3. **Einfluss von Entgratung / Trowalisieren auf Biegerissbildung:** Führt das Gleitschleifen der lasergeschnittenen Blechkanten vor dem Biegen zu einer signifikanten Reduktion des Mindestbiegeradius bei 1.4301?

---

Claude (2026-10-21): nur überflogen. Die Größenordnungen sind plausibel (O-Ring 2 mm statisch radial t 1,5; Biegeradien DC01 1×t, 6061-T6 2–3×t), die Werte sind nicht gegen die Quellen geprüft. Das übernimmt `tools/check_sources.py`.
