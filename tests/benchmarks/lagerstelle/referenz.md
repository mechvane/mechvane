# Technischer Bericht: Referenzlösung Lagerstelle

## 1. Anforderungsanalyse & Widerspruchsprüfung (Kategorie A)

### A1. Erkennung des Widerspruchs im Lastenheft
Im Lastenheft wurde ein Mittenabstand der Befestigungsbohrungen von **$p = 36\text{ mm}$** ($\pm 18\text{ mm}$ symmetrisch zur Mittelachse) gefordert.
Dies steht im **direkten geometrischen Widerspruch** zum Lagersitzdurchmesser:
* Für den Wellendurchmesser $d = 20\text{ mm}$ besitzt das Standard-Rillenkugellager 6004 einen Außendurchmesser von $D = 42\text{ mm}$ ($R = 21\text{ mm}$).
* Bei einem Bohrungsabstand von $36\text{ mm}$ lägen die Bohrungsachsen bei $x = \pm 18\text{ mm}$.
* Da $18\text{ mm} < 21\text{ mm}$ ist, würden die Befestigungsschrauben (M6 bzw. Senkung $\varnothing 11\text{ mm}$) direkt mitten durch den Lagersitz verlaufen und mit dem Kugellager kollidieren (Kollision / Restwandstärke $0\text{ mm}$).

### A2. Ingenieurmäßiger Korrekturvorschlag
Der Bohrungsabstand wird ingenieurmäßig auf **$p = 60\text{ mm}$** ($x = \pm 30\text{ mm}$) korrigiert (gefordert: $p \ge 58{,}6\text{ mm}$):
* Bei Senkdurchmesser $d_{\text{senk}} = 11{,}0\text{ mm}$ nach DIN 974-1 (Innenkante bei $x = 30 - 5{,}5 = 24{,}5\text{ mm}$) und Lagersitzradius $R = 21{,}0\text{ mm}$ verbleibt eine gesunde Mindestwandstärke von:
  $$s_{\text{min}} = 24{,}5 - 21{,}0 = 3{,}5\text{ mm} \ge 1{,}2\text{ mm}$$
* Randabstand zur Außenkante des Lagerbocks ($L = 80\text{ mm}$):
  $$e = \frac{80 - 60}{2} = 10{,}0\text{ mm} \ge 1{,}5 \cdot d = 9{,}0\text{ mm}$$

---

## 2. Rechnerische Auslegung & Lagerwahl (Kategorie B)

### B1. Lagerwahl & Tragzahlen-Nachweis
* **Gewähltes Lager:** Rillenkugellager **DIN 625 – 6004** ($20 \times 42 \times 12\text{ mm}$).
* **Autorisierte Herstellerquelle:** NSK Engineering Data Sheet 6004 (Herstellerkatalog).
* **Dynamische Tragzahl:** $C_r = 10{,}3\text{ kN} = 10300\text{ N}$
* **Statische Tragzahl:** $C_{0r} = 5{,}0\text{ kN} = 5000\text{ N}$

### B2. Lebensdauerberechnung nach DIN ISO 281
* **Betriebsdaten:**
  * Radialkraft: $F_r = 1200\text{ N} = 1{,}20\text{ kN}$
  * Axialkraft: $F_a = 0\text{ N} \rightarrow$ Dynamisch äquivalente Belastung $P = F_r = 1{,}20\text{ kN}$
  * Drehzahl: $n = 500\text{ min}^{-1}$
  * Lebensdauerexponent: $p = 3$ (Kugellager)
* **Berechnung der nominellen Lebensdauer $L_{10}$:**
  $$L_{10} = \left(\frac{C_r}{P}\right)^p = \left(\frac{10{,}3}{1{,}2}\right)^3 \approx 8{,}5833^3 \approx 632{,}38\text{ Millionen Umdrehungen}$$
* **Nominelle Lebensdauer in Betriebsstunden $L_{10h}$:**
  $$L_{10h} = \frac{10^6}{60 \cdot n} \cdot L_{10} = \frac{10^6}{60 \cdot 500} \cdot 632{,}38 = 33{,}333 \cdot 632{,}38 \approx \mathbf{21.079\text{ h}}$$
* **Bewertung:** Die geforderte Mindestlebensdauer von $L_{10h} \ge 20.000\text{ h}$ wird mit $21.079\text{ h}$ sicher erfüllt.

---

## 3. Konstruktive Gestaltung & Baugruppenintegration (Kategorien C, D, E)

* **Achshöhe (C2):** $h = 35{,}0\text{ mm}$ über Montagefläche.
* **Bauraum (C3):** Hüllquader $80{,}0 \times 30{,}0 \times 62{,}0\text{ mm} \le 85 \times 30 \times 65\text{ mm}$.
* **Lagersitz (C4):** Passungsbohrung $\varnothing 42{,}0\text{ mm}$, Breite $12{,}0\text{ mm}$.
* **Durchgangsbohrungen (C5):** $\varnothing 6{,}6\text{ mm}$ (ISO 273 mittel für M6) mit zylindrischer Senkung $\varnothing 11\text{ mm}$, Randabstand $e = 10{,}0\text{ mm} \ge 9{,}0\text{ mm}$.
* **Normteile (D1):** Rillenkugellager DIN 625 6004, Zylinderschrauben ISO 4762 M6x12, Scheiben ISO 7089 6.
* **Axiale Sicherung (D2):**
  * Gehäusenut DIN 472: $\varnothing 44{,}5\text{ mm}$, Breite $m = 1{,}85\text{ mm}$, Stegbreite $n = 4{,}0\text{ mm} \ge 3{,}8\text{ mm}$.
  * Wellennut DIN 471: $\varnothing 19{,}0\text{ mm}$, Breite $m = 1{,}30\text{ mm}$, Stegbreite $n = 2{,}7\text{ mm} \ge 1{,}5\text{ mm}$.
* **Freiheitsgrade (D3):** Baugruppe exakt 1 DOF (Rotation der Welle).
* **Anlageschultern (E1):** Wellenschulter $\varnothing 25{,}0\text{ mm}$, Gehäuseschulter $\varnothing 38{,}0\text{ mm}$.
* **DFM (E2):** Einpressfase $0{,}8\text{ mm} \times 45^\circ$ am Lagersitz.
* **Einschraubtiefe (E3):** Gewindeeingriff im Aluminium AlMgSi1: $m_{\text{eff}} = 8{,}4\text{ mm} = 1{,}4 \cdot d$ (Bossard-Richtwert für AlMgSi1 / $R_m > 330\text{ N/mm}^2$).
