# Recherchebericht: DIN 974-1:2008-02 und ISO 7089

> **Prüfnotiz Claude (2026-10-23):** Rohfassung Gemini 3.8 Flash. Tabelle 1 im
> Leseprobe-PDF des Beuth-Tabellenbuchs selbst angesehen (Spalten Reihe 1, 2, 4, 5, 6,
> Reihe 3 fehlt): Reihe 5 = 7 / 9 / 10 / 13 / 15 für M2,5–M6 bestätigt, M8–M12 laut
> `check_sources.py` im Quelltext. Die Senktiefe ist in der Norm nicht festgelegt, nur
> die Formel k + h + Zugabe (Tabelle 2). `hole_tables.DIN_974_1["with_washer"]` rechnet
> mit Nenndicke h.

---

### Management Summary

1. **Senkdurchmesser $d_1$ (H13) für ISO 4762 mit Scheibe ISO 7089/7090:**  
   Die zu prüfenden Werte für die Nenngrößen **M2.5 bis M12 stimmen ausnahmslos exakt** mit **Tabelle 1, Reihe 5** der DIN 974-1:2008-02 überein:
   * M2.5: **7,0 mm** | M3: **9,0 mm** | M4: **10,0 mm** | M5: **13,0 mm**  
   * M6: **15,0 mm** | M8: **18,0 mm** | M10: **24,0 mm** | M12: **26,0 mm**
2. **Reihen-Zuordnung in DIN 974-1:2008-02:**  
   Standard-Unterlegscheiben nach **ISO 7089 / ISO 7090** (normale Reihe, ehemals DIN 125) fallen normativ unter **Reihe 5**.  
   Schmale Scheiben nach **ISO 7092** (ehemals DIN 433) fallen unter **Reihe 4**.  
   Schrauben ohne Unterlegscheiben fallen unter **Reihe 1** (Zylinder-/Innensechskantschrauben) bzw. **Reihe 2** (Flachkopfschrauben). Spannscheiben nach DIN 6796 fallen unter **Reihe 6**.
3. **Senktiefe $t$ in DIN 974-1:2008-02:**  
   Die Norm gibt für diese Reihe **keine festen Tabellenwerte für die Senktiefe $t$** an. Stattdessen enthält die Norm eine **Empfehlungsformel** sowie eine normative **Tabelle 2 für die Zugabe**:
   $$t = k_{\max} + h_{\max} + \text{Zugabe (nach Tabelle 2)}$$
4. **Scheibenmaße ISO 7089:**  
   Außendurchmesser $d_2$ und Scheibendicke $h$ sind vollständig durch die Norm ISO 7089 (bzw. DIN EN ISO 7089) sowie technische Herstellerkataloge belegt.

---

### 1. Systematik der Durchmesser-Reihen nach DIN 974-1:2008-02

In der Norm DIN 974-1:2008-02 (*Senkdurchmesser – Konstruktionsmaße – Teil 1: Schrauben mit Zylinderkopf*) werden fünf Durchmesser-Reihen für den Senkdurchmesser $d_1$ (Toleranzfeld H13) unterschieden:

| Reihe in DIN 974-1 | Abgedeckte Schrauben- und Scheibenarten |
| :--- | :--- |
| **Reihe 1** | **Schrauben ohne Unterlegteile:** Zylinderkopfschrauben mit Innensechskant bzw. Innensechsrund nach DIN EN ISO 4762 (DIN 912), DIN EN ISO 14579, DIN EN ISO 14580, DIN 6912, DIN 7984, DIN 34821, DIN EN ISO 1207 sowie gewindefurchende/-schneidende Schrauben nach DIN 7500-1, DIN 7513, DIN 7516. |
| **Reihe 2** | **Schrauben ohne Unterlegteile:** Flachkopfschrauben mit Schlitz / Kreuzschlitz / Innensechsrund nach DIN EN ISO 1580, DIN EN ISO 7045, DIN EN ISO 14583. |
| *Reihe 3* | *In DIN 974-1:2008-02 nicht mehr vergeben / entfallen.* |
| **Reihe 4** | **Schrauben mit Unterlegteilen:** Zylinderkopfschrauben mit **schmalen Scheiben** nach **DIN EN ISO 7092** (ehemals DIN 433) sowie DIN EN ISO 10673 Form S. |
| **Reihe 5** | **Schrauben mit Unterlegteilen:** Zylinderkopfschrauben mit **Standard-Scheiben** nach **DIN EN ISO 7089**, **DIN EN ISO 7090** (normale Reihe, ehemals DIN 125) sowie DIN EN ISO 10673 Form S. |
| **Reihe 6** | **Schrauben mit Unterlegteilen:** Zylinderkopfschrauben mit **Spannscheiben** nach **DIN 6796** und DIN 6908. |

*Fußnote a zu Tabelle 1:* „Bei Verbindungen mit mehreren Unterlegteilen gilt die Reihe für das Unterlegteil mit dem größten Durchmesser.“

---

### 2. Prüfung der Senkdurchmesser $d_1$ (H13) für ISO 4762 mit Scheibe ISO 7089/7090 (Reihe 5)

Alle vorgegebenen Werte wurden gegen **Tabelle 1 der DIN 974-1:2008-02** geprüft:

| Gewinde | Vorgegebener Prüfwert [mm] | DIN 974-1:2008-02 Tabelle 1 (Reihe 5) [mm] | Durchgangsloch $d_2$ (ISO 273 mittel) [mm] | Status | Wörtliche Tabellenzeile aus der Quelle |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **M2.5** | **7.0** | **7** | 2,9 | **Bestätigt** | `2,5 \| 2,9 \| 5,5 \| 6 \| 6 \| 7 \| 7` |
| **M3** | **9.0** | **9** | 3,4 | **Bestätigt** | `3 \| 3,4 \| 6,5 \| 7 \| 7 \| 9 \| 8` |
| **M4** | **10.0** | **10** | 4,5 | **Bestätigt** | `4 \| 4,5 \| 8 \| 9 \| 9 \| 10 \| 10` |
| **M5** | **13.0** | **13** | 5,5 | **Bestätigt** | `5 \| 5,5 \| 10 \| 11 \| 11 \| 13 \| 13` |
| **M6** | **15.0** | **15** | 6,6 | **Bestätigt** | `6 \| 6,6 \| 11 \| 13 \| 13 \| 15 \| 15` |
| **M8** | **18.0** | **18** | 9,0 | **Bestätigt** | `8 \| 9 \| 15 \| 18 \| 16 \| 18 \| 20` |
| **M10** | **24.0** | **24** | 11,0 | **Bestätigt** | `10 \| 11 \| 18 \| 24 \| 20 \| 24 \| 24` |
| **M12** | **26.0** | **26** | 13,5 | **Bestätigt** | `12 \| 13,5 \| 20 \| – \| 24 \| 26 \| 33` |

> **Quelle für Tabelle 1:**  
> Hofmann & Naumann: *Tabellenbuch Schrauben, Muttern und Zubehör*, 2. Auflage 2014, Beuth Verlag GmbH (DIN Media), ISBN 978-3-410-23162-2, Kapitel zu DIN 974-1:2008-02, S. 15–16 (PDF-S. 24–25).  
> **URL:** [https://api.pageplace.de/preview/DT0400.9783410231622_A34075842/preview-9783410231622_A34075842.pdf](https://api.pageplace.de/preview/DT0400.9783410231622_A34075842/preview-9783410231622_A34075842.pdf)

---

### 3. Senktiefe $t$: Feste Werte oder Berechnungsformel?

**Ergebnis:**  
DIN 974-1:2008-02 gibt **keine festen Tabellenwerte für die Senktiefe $t$** an, sondern verweist darauf, dass diese anwendungsabhängig zu wählen ist, und liefert eine **Berechnungsempfehlung mit Zugaben-Tabelle**.

#### Wörtliches Zitat aus der Normerläuterung (Beuth-Tabellenbuch, S. 17):
> *„Darüber hinaus gibt die Norm eine Empfehlung mit Berechnungsbeispiel für die Bestimmung der Senktiefe an. Werte sind jedoch nicht festgelegt, da diese dem jeweiligen Anwendungsfall entsprechend zu wählen sind.“*

#### Die Berechnungsformel nach DIN 974-1:
$$t = k_{\max} + h_{\max} + \text{Zugabe}$$
* $k_{\max}$: Maximale Kopfhöhe der Schraube nach ISO 4762
* $h_{\max}$: Maximale Dicke des Unterlegteils nach Maßnorm (bei Schrauben ohne Scheibe: $h = 0$)
* $\text{Zugabe}$: Konstruktive Zugabe nach **Tabelle 2** der Norm

#### Tabelle 2 der DIN 974-1:2008-02: *Zugabe für die Bestimmung der Senktiefe $t$*
*(Maße in Millimeter)*

| Gewindenenndurchmesser $d$ | Zugabe [mm] |
| :--- | :---: |
| $d \le 1{,}4$ | 0,2 |
| $1{,}4 < d \le 6$ | **0,4** |
| $6 < d \le 20$ | **0,6** |
| $20 < d \le 27$ | 0,8 |
| $27 < d \le 100$ | 1,0 |

#### Wörtliches Berechnungsbeispiel aus der Norm DIN 974-1:
> *„Zylinderschraube ISO 4762 – M12 × 60 – 10.9 mit Scheibe ISO 7092 – 12 – 300 HV:*  
> *Kopfhöhe der Schraube $k_{\max} = 12\text{ mm}$*  
> *Dicke der Scheibe $h_{\max} = 2{,}2\text{ mm}$*  
> *Zugabe für $d = 12\text{ mm}$ (Bereich $6 < d \le 20$): $0{,}6\text{ mm}$*  
> *$\implies t = 12\text{ mm} + 2{,}2\text{ mm} + 0{,}6\text{ mm} = \mathbf{14{,}8\text{ mm}}$“*

#### Rechnerische Senktiefen $t$ für ISO 4762 mit Scheibe ISO 7089:

Wendet man diese Normempfehlung auf Zylinderschrauben ISO 4762 mit Scheiben nach ISO 7089 an, ergeben sich folgende Werte:

| Gewinde | $k_{\max}$ (ISO 4762) [mm] | $h_{\text{nenn}}$ / $h_{\max}$ (ISO 7089) [mm] | Zugabe (Tab. 2) [mm] | $t$ gerechnet mit $h_{\text{nenn}}$ [mm] | $t$ gerechnet mit $h_{\max}$ [mm] | Status in DIN 974-1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **M2.5** | 2,50 | 0,50 / 0,55 | 0,4 | **3,4** | **3,45** | *Kein Tabellenfestwert in DIN 974-1* |
| **M3** | 3,00 | 0,50 / 0,55 | 0,4 | **3,9** | **3,95** | *Kein Tabellenfestwert in DIN 974-1* |
| **M4** | 4,00 | 0,80 / 0,90 | 0,4 | **5,2** | **5,30** | *Kein Tabellenfestwert in DIN 974-1* |
| **M5** | 5,00 | 1,00 / 1,10 | 0,4 | **6,4** | **6,50** | *Kein Tabellenfestwert in DIN 974-1* |
| **M6** | 6,00 | 1,60 / 1,80 | 0,4 | **8,0** | **8,20** | *Kein Tabellenfestwert in DIN 974-1* |
| **M8** | 8,00 | 1,60 / 1,80 | 0,6 | **10,2** | **10,40** | *Kein Tabellenfestwert in DIN 974-1* |
| **M10** | 10,00 | 2,00 / 2,20 | 0,6 | **12,6** | **12,80** | *Kein Tabellenfestwert in DIN 974-1* |
| **M12** | 12,00 | 2,50 / 2,70 | 0,6 | **15,1** | **15,30** | *Kein Tabellenfestwert in DIN 974-1* |

*(Hinweis: In manchen CAD-Bibliotheken wird vereinfachend ohne Zugabe gearbeitet: $t \approx k_{\max} + h_{\text{nenn}}$. Bei bündiger Vollversenkung nach DIN 974-1 kommt die Zugabe nach Tabelle 2 hinzu).*

---

### 4. Maße der Unterlegscheibe ISO 7089 (Form A, Produktklasse A)

Geprüfte Maße: Außendurchmesser $d_2$ und Scheibendicke $h$ (ergänzend Innendurchmesser $d_1$):

| Nenngröße | Außendurchmesser $d_2$ Nenn [mm] | $d_2$ Grenzabmaße (Max / Min) [mm] | Scheibendicke $h$ Nenn [mm] | $h$ Grenzabmaße (Max / Min) [mm] | Innendurchmesser $d_1$ (Min / Max) [mm] | Freigang in DIN 974-1 Reihe 5 ($d_{1,\text{Senk}} - d_{2,\text{Scheibe}}$) [mm] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **M2.5** | **6,0** | 6,00 / 5,70 | **0,5** | 0,55 / 0,45 | 2,70 / 2,84 | $7{,}0 - 6{,}0 = \mathbf{1{,}0}$ |
| **M3** | **7,0** | 7,00 / 6,64 | **0,5** | 0,55 / 0,45 | 3,20 / 3,38 | $9{,}0 - 7{,}0 = \mathbf{2{,}0}$ |
| **M4** | **9,0** | 9,00 / 8,64 | **0,8** | 0,90 / 0,70 | 4,30 / 4,48 | $10{,}0 - 9{,}0 = \mathbf{1{,}0}$ |
| **M5** | **10,0** | 10,00 / 9,64 | **1,0** | 1,10 / 0,90 | 5,30 / 5,48 | $13{,}0 - 10{,}0 = \mathbf{3{,}0}$ |
| **M6** | **12,0** | 12,00 / 11,57 | **1,6** | 1,80 / 1,40 | 6,40 / 6,62 | $15{,}0 - 12{,}0 = \mathbf{3{,}0}$ |
| **M8** | **16,0** | 16,00 / 15,57 | **1,6** | 1,80 / 1,40 | 8,40 / 8,62 | $18{,}0 - 16{,}0 = \mathbf{2{,}0}$ |
| **M10** | **20,0** | 20,00 / 19,48 | **2,0** | 2,20 / 1,80 | 10,50 / 10,77 | $24{,}0 - 20{,}0 = \mathbf{4{,}0}$ |
| **M12** | **24,0** | 24,00 / 23,48 | **2,5** | 2,70 / 2,30 | 13,00 / 13,27 | $26{,}0 - 24{,}0 = \mathbf{2{,}0}$ |

#### Belege und Zitate für ISO 7089:

1. **F. REYHER Nchfg. GmbH & Co. KG – Technische Informationen (Katalog TI/2020.04/DE):**  
   *URL:* [https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)  
   *Seite TI-84 (PDF-S. 84), Tabelle „Maße für Scheiben und Ringe – ISO 7089, 7090 (DIN 125-1 Pk A)“:*
   * M2,5: `2,5 2,7 6 0,5`
   * M3: `3 3,2 7 0,5`
   * M4: `4 *1/8“ 4,3 9 0,8`
   * M5: `5 *3/16“ 5,3 10 1`
   * M6: `6 6,4 12 1,6`
   * M8: `8 *5/16“ 8,4 16 1,6`
   * M10: `10 *3/8“ 10,5 20 2`
   * M12: `12 *7/16“ 13 24 2,5`

2. **Industrial Threaded Products (ITP) – Fastener Catalog:**  
   *URL:* [https://itpbolt.com/wp-content/uploads/2015/08/Standard-Flat-Washer.pdf](https://itpbolt.com/wp-content/uploads/2015/08/Standard-Flat-Washer.pdf)  
   *Seite 346, Tabelle „METRIC - STANDARD FLAT WASHERS (NORMAL SERIES, GRADE A) ISO 7089“ (Spalten ID, OD, Thickness):*
   * 2.5: `2.5 \| ID Max: 2.84, Min: 2.7 \| OD Max: 6, Min: 5.7 \| Thickness Max: 0.55, Min: 0.45`
   * 3: `3 \| ID Max: 3.38, Min: 3.2 \| OD Max: 7, Min: 6.64 \| Thickness Max: 0.55, Min: 0.45`
   * 4: `4 \| ID Max: 4.48, Min: 4.3 \| OD Max: 9, Min: 8.64 \| Thickness Max: 0.9, Min: 0.7`
   * 5: `5 \| ID Max: 5.48, Min: 5.3 \| OD Max: 10, Min: 9.64 \| Thickness Max: 1.1, Min: 0.9`
   * 6: `6 \| ID Max: 6.62, Min: 6.4 \| OD Max: 12, Min: 11.57 \| Thickness Max: 1.8, Min: 1.4`
   * 8: `8 \| ID Max: 8.62, Min: 8.4 \| OD Max: 16, Min: 15.57 \| Thickness Max: 1.8, Min: 1.4`
   * 10: `10 \| ID Max: 10.77, Min: 10.5 \| OD Max: 20, Min: 19.48 \| Thickness Max: 2.2, Min: 1.8`
   * 12: `12 \| ID Max: 13.27, Min: 13 \| OD Max: 24, Min: 23.48 \| Thickness Max: 2.7, Min: 2.3`

---

### 5. Zusammenfassung der Quellenübersicht

1. **DIN 974-1:2008-02 (Senkdurchmesser und Senktiefen-Regeln):**
   * *Hofmann & Naumann, Tabellenbuch Schrauben, Muttern und Zubehör (Beuth Verlag / DIN Media), S. 15–17:*  
     [https://api.pageplace.de/preview/DT0400.9783410231622_A34075842/preview-9783410231622_A34075842.pdf](https://api.pageplace.de/preview/DT0400.9783410231622_A34075842/preview-9783410231622_A34075842.pdf)
2. **ISO 7089 (Unterlegscheiben normale Reihe, Produktklasse A):**
   * *F. REYHER Nchfg. GmbH & Co. KG, Technische Informationen, S. TI-84:*  
     [https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf](https://www.reyher.de/fileadmin/user_upload/Downloadbereich/Reyher_2019-DE_Technische_Informationen_ks.pdf)
   * *Industrial Threaded Products (ITP), Metric Flat Washers Catalog, S. 346:*  
     [https://itpbolt.com/wp-content/uploads/2015/08/Standard-Flat-Washer.pdf](https://itpbolt.com/wp-content/uploads/2015/08/Standard-Flat-Washer.pdf)
3. **ISO 4762 (Kopfmaße Zylinderschrauben für Tiefenberechnung):**
   * *Aramfix Fasteners Technical Data Sheet ISO 4762:*  
     [https://www.aramfix.com/content/files/i762caill/datasheet%20iso%204762.pdf](https://www.aramfix.com/content/files/i762caill/datasheet%20iso%204762.pdf)
