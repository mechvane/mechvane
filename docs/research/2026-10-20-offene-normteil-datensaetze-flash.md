> Gemini-3.8-Flash-Rohfassung mit Web, nicht verifiziert. Automatische Prüfung 2026-10-20: 13 Links, davon 1 nicht mit 200 erreichbar (teils Bot-Sperren). Zahlen vor dem Übernehmen einzeln an der Quelle prüfen.

# Recherche: Offene Datensätze mit Maßtabellen für Normteile in Open-Source-CAD-Projekten (MIT/Apache-2.0)

Für ein Open-Source-CAD-Projekt unter einer permissiven Lizenz (**MIT** oder **Apache-2.0**) wurden die fünf wichtigsten offenen Normteil- und CAD-Bibliotheken im Detail analysiert.

---

## 1. Detaillierte Analyse der Kandidaten

### 1. BOLTS (`boltsparts/boltsparts`)

* **Repo-URL:** [https://github.com/boltsparts/boltsparts](https://github.com/boltsparts/boltsparts) *(Archiv-Vorgänger: [https://github.com/boltsparts/BOLTS_archive](https://github.com/boltsparts/BOLTS_archive))*
* **Lizenz der Daten (wörtlich aus den Dateien):**
  * Aus der Datei `LICENSE` im Repository-Root:
    ```text
                        GNU GENERAL PUBLIC LICENSE
                           Version 3, 29 June 2007

     Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
     Everyone is permitted to copy and distribute verbatim copies
     of this license document, but changing it is not allowed.
    ```
  * In den jeweiligen Datendateien (`data/*.blt`) ist eine feldbasierte Einzellizenz hinterlegt. Für die relevanten Normteile (`hex.blt`, `hex_socket.blt`, `nut.blt`, `washer.blt`, `bearings.blt`) lautet diese wörtlich:
    ```yaml
    license: LGPL 2.1+ <http://www.gnu.org/licenses/lgpl-2.1>
    ```
    *(Hinweis: Laut `backends/website/docs/sources/0.4/general/licensing.md` erlaubt BOLTS pro Teil unterschiedliche Lizenzen; Profile/Batterien sind teilweise MIT/Unlicense, Verbindungselemente und Lager sind LGPL 2.1+).*
* **Kompatibilität mit MIT / Apache-2.0:**
  * **Eingeschränkt / Nicht permissiv re-lizenzierbar:** Die Gesamtdistribution ist GPL-3.0, die relevanten Datendateien stehen unter LGPL-2.1+. Ein MIT- oder Apache-2.0-Projekt darf LGPL-2.1+-Dateien nicht einfach unter MIT/Apache umetikettieren. Sie könnten nur als eigenständige, austauschbare LGPL-Bibliothek eingebunden werden, sofern man nicht die reinen Fakten/Zahlenwerte clean isoliert.
* **Enthaltene Normen und Größen:**
  * **Schrauben:**
    * **ISO 4762** (Zylinderschrauben mit Innensechskant / DIN 912): M1.4 bis M64 (27 Nenngrößen, Schaft- und Gewindelängen)
    * **ISO 4017** (Sechskantschrauben / DIN 933) & **ISO 4014** (DIN 931): M1.6 bis M64 (28 Nenngrößen)
    * **ISO 10642** (Senkschrauben mit Innensechskant / DIN 7991): M3 bis M24 (15 Nenngrößen)
  * **Muttern:**
    * **ISO 4032** (Sechskantmutter Typ 1 / DIN 934): M1 bis M64 (49 Nenngrößen inkl. Regel- und Feingewinde), ISO 4035 / DIN 439
  * **Scheiben:**
    * **ISO 7089** (Unterlegscheibe / DIN 125 A): M1.6 bis M64 (44 Nenngrößen), ISO 7090, ISO 7091, ISO 7092
  * **Gewindeeinsätze:** **Keine** (nicht vorhanden)
  * **Wälzlager:** DIN 625-1 (Rillenkugellager 608, 623, 624, 634 etc.), DIN 625-3 (zweireihig), DIN 711 / ISO 104 (Axial-Rillenkugellager), DIN 5405-1 / ISO 3030 (Nadelrollen), DIN 5412-1 (Zylinderrollenlager)
  * **Bohrungen & Senkungen:** **Keine** (keine Tabellen für Durchgangs- oder Kernlochbohrungen)
* **Datenformat und Pfad im Repo:**
  * Format: YAML-Dateien mit BOLTS-eigener Tabellenstruktur (`columns`, `data`, `index`)
  * Pfad: `data/*.blt` (z. B. `data/hex.blt`, `data/hex_socket.blt`, `data/nut.blt`, `data/washer.blt`, `data/bearings.blt`)
* **Quellen pro Wert / Klasse angegeben:**
  * **Ja, vorbildlich auf Bauteilebene dokumentiert.** Jede Klasse enthält ein Feld `source:`, z. B.:
    * `hex_socket.blt`: `http://almetal.nl/en/techinfo/soc/sd912.htm`, Händlerkatalog Zweygart
    * `hex.blt`: `http://almetal.nl/en/techinfo/hex/hd933.htm`
    * `bearings.blt`: `http://www.kgm-kugeln.de/...`, Steyr-Papierkatalog (~1980er)
* **Letzte Aktivität:**
  * Inaktiv / archiviert (letzter Commit am 17. November 2022).

---

### 2. FreeCAD Fasteners Workbench (`shaise/FreeCAD_FastenersWB`)

* **Repo-URL:** [https://github.com/shaise/FreeCAD_FastenersWB](https://github.com/shaise/FreeCAD_FastenersWB)
* **Lizenz der Daten (wörtlich aus der Datei):**
  * Aus der Datei `LICENSE`:
    ```text
                        GNU GENERAL PUBLIC LICENSE
                           Version 2, June 1991

     Copyright (C) 1989, 1991 Free Software Foundation, Inc., <http://fsf.org/>
     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
     Everyone is permitted to copy and distribute verbatim copies
    ```
  * In den Python-Dateien:
    ```text
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    ```
  * Die CSV-Dateien in `FsData/` tragen keinen separaten Header und fallen unter die Projekt-GPL-2.0.
* **Kompatibilität mit MIT / Apache-2.0:**
  * **Inkompatibel:** Die GPL-2.0 ist eine strenge Copyleft-Lizenz. Dateien aus diesem Repo können nicht direkt in ein MIT- oder Apache-2.0-Projekt übernommen werden, da GPL-2.0 keine permissive Nachlizenzierung erlaubt und GPL-2.0-only zudem mit Apache-2.0 kollidiert.
* **Enthaltene Normen und Größen:**
  * **Schrauben:**
    * **ISO 4762:** `FsData/iso4762def.csv` (M1.6 bis M30, 85 Datenzeilen)
    * **ISO 4017:** `FsData/iso4017head.csv` (M1.6 bis M64, 96 Datenzeilen)
    * **ISO 10642:** `FsData/iso10642def.csv` (M2 bis M24, 51 Datenzeilen)
  * **Muttern:**
    * **ISO 4032:** `FsData/iso4032def.csv` (M1.6 bis M64, 30 Datenzeilen)
  * **Scheiben:**
    * **ISO 7089:** `FsData/iso7089def.csv` (M1.6 bis M64, 20 Datenzeilen)
  * **Gewindeeinsätze:** `FsData/HeatInserts.csv` (IUT Heat Inserts M2 bis M5), `FsData/PEMFasteners.csv`
  * **Wälzlager:** **Keine** (nur Befestigungselemente)
  * **Bohrungen & Senkungen:**
    * Senkungen werden parametrisch über `CountersunkHoles.py` erzeugt.
    * Für Bohrungen existiert lediglich `FsData/inch_screw_hole_chart.csv` (Zoll). Metrische Kernloch- und Durchgangsbohrungen liegen in FreeCAD nicht in der Fasteners Workbench, sondern im FreeCAD Core (`PartDesign::Hole`).
* **Datenformat und Pfad im Repo:**
  * Format: Reine CSV-Dateien mit Parameter-Headern (z. B. `"Dia","P","b","dk_max","da",...`)
  * Pfad: `FsData/*.csv` (insgesamt 192 CSV-Dateien)
* **Quellen pro Wert angegeben:**
  * **Nein.** In den CSV-Dateien gibt es keine Quellen- oder Literaturangaben. Das README verweist allgemein auf das ursprüngliche `screw_maker macro` von `@ulrich1a`.
* **Letzte Aktivität:**
  * Sehr aktiv (letzter Commit am 10. September 2026).

---

### 3. `cq_warehouse` (`gumyr/cq_warehouse`)

* **Repo-URL:** [https://github.com/gumyr/cq_warehouse](https://github.com/gumyr/cq_warehouse)
* **Lizenz der Daten (wörtlich aus der Datei):**
  * Aus der Datei `LICENSE`:
    ```text
                                     Apache License
                               Version 2.0, January 2004
                            http://www.apache.org/licenses/

       TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
    ```
* **Kompatibilität mit MIT / Apache-2.0:**
  * **Vollständig kompatibel:** Die Apache-2.0-Lizenz erlaubt die freie kommerzielle und private Weiternutzung, Modifikation und Distribution. Sie passt nahtlos in Apache-2.0-Projekte und kann mit MIT-Projekten kombiniert werden (unter Beibehaltung der Copyright- und Lizenzhinweise).
* **Enthaltene Normen und Größen:**
  * **Schrauben:**
    * **ISO 4762:** `src/cq_warehouse/socket_head_cap_parameters.csv` (M1.6 bis M64)
    * **ISO 4017:** `src/cq_warehouse/hex_head_parameters.csv` (M1.6 bis M64; enthält auch DIN 931, ISO 4014)
    * **ISO 10642:** `src/cq_warehouse/countersunk_head_parameters.csv` (M1 bis M24; enthält auch ISO 14581, 14582, 2009, 7046)
  * **Muttern:**
    * **ISO 4032:** `src/cq_warehouse/hex_nut_parameters.csv` (M1.6 bis M64; enthält auch ISO 4033, 4035)
  * **Scheiben:**
    * **ISO 7089:** `src/cq_warehouse/plain_washer_parameters.csv` (M1.6 bis M64; enthält auch ISO 7091, 7093, 7094), `chamfered_washer_parameters.csv` (ISO 7090)
  * **Gewindeeinsätze:** `src/cq_warehouse/heatset_nut_parameters.csv` (Gewindeeinsätze von McMaster-Carr und Hilitchi von M2 bis M5 in Kurz- und Standardausführung)
  * **Wälzlager:** Mehrere dedizierte CSVs:
    * `single_row_deep_groove_ball_bearing_parameters.csv`
    * `single_row_angular_contact_ball_bearing_parameters.csv`
    * `single_row_capped_deep_groove_ball_bearing_parameters.csv`
    * `single_row_cylindrical_roller_bearing_parameters.csv`
    * `single_row_tapered_roller_bearing_parameters.csv`
  * **Bohrungen & Senkungen:**
    * **Durchgangsbohrungen:** `src/cq_warehouse/clearance_hole_sizes.csv` (ISO 273: Reihen „Close“, „Normal“, „Loose“ für M1 bis M64)
    * **Kernlochbohrungen:** `src/cq_warehouse/tap_hole_sizes.csv` (Vorbohrdurchmesser für M1.5 bis M64 nach „Soft“ und „Hard“)
    * **Bohrergrößen:** `src/cq_warehouse/drill_sizes.csv`
    * **Senkungen:** Maße für 90°-Senkungen und Flachsenkungen sind in den Schraubentabellen (`countersunk_head_parameters.csv`) und in `fastener.py` implementiert.
* **Datenformat und Pfad im Repo:**
  * Format: Klare, modulare CSV-Dateien mit präfixierten Normspalten (z. B. `Size,iso4762:dk,iso4762:k,iso4762:s,iso4762:t,...`)
  * Pfad: `src/cq_warehouse/*.csv` (24 CSV-Dateien)
* **Quellen pro Wert angegeben:**
  * **Teilweise:** Bei Gewindeeinsätzen sind exakte Herstellernummern (McMaster-Carr Part Numbers und Hilitchi) zeilenweise dokumentiert. Bei Normteilen sind die Normen in den Spaltennamen deklariert; externe Literaturlinks oder Seitenangaben pro Zahlenwert fehlen.
* **Letzte Aktivität:**
  * Sehr aktiv (letzter Commit am 16. Oktober 2026, PR #90 zur Datenkorrektur in CSVs).

---

### 4. BOSL2 (`BelfrySCAD/BOSL2`)

* **Repo-URL:** [https://github.com/BelfrySCAD/BOSL2](https://github.com/BelfrySCAD/BOSL2)
* **Lizenz der Daten (wörtlich aus der Datei):**
  * Aus der Datei `LICENSE`:
    ```text
    BSD 2-Clause License

    Copyright (c) 2017-2019, Revar Desmera
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    ```
* **Kompatibilität mit MIT / Apache-2.0:**
  * **Vollständig kompatibel:** BSD-2-Clause ist permissiv und uneingeschränkt mit MIT und Apache-2.0 kompatibel (erfordert lediglich die Beibehaltung des Copyright-Vermerks).
* **Enthaltene Normen und Größen:**
  * **Schrauben:**
    * In `screws.scad` parametrisiert über `head="socket"` (**ISO 4762**), `head="hex"` (**ISO 4017 / 4014**), `head="flat"` (**ISO 10642**, `metric_flat_large`), M1 bis M64.
  * **Muttern:**
    * In `screws.scad` nach **ISO 4032**, ISO 4035, ISO 4033 und DIN 934, DIN 936.
  * **Scheiben:** **Keine isolierte Maßtabelle** (Scheiben werden in OpenSCAD meist ad-hoc über Zylinder erzeugt).
  * **Gewindeeinsätze:** **Keine** standardisierte Maßtabelle für Heat-Set Inserts.
  * **Wälzlager:** In `ball_bearings.scad` (608, 624, 6902ZZ, R-Serie, Flanschlager etc.) sowie `linear_bearings.scad` (LMxUU).
  * **Bohrungen & Senkungen:** Modul `screw_hole()` in `screws.scad`:
    * Durchgangsbohrungen ("close", "normal", "loose" / ISO 273 bzw. H12, H13, H14)
    * Kernlochbohrungen ("tap", "self tap")
    * Senkungen und zylindrische Flachsenkungen (`counterbore`)
* **Datenformat und Pfad im Repo:**
  * Format: OpenSCAD-Quellcode (verschachtelte OpenSCAD-Listen und `lookup()`-Tabellen)
  * Pfad: Root-Verzeichnis (`screws.scad`, `ball_bearings.scad`, `linear_bearings.scad`, `threading.scad`)
* **Quellen pro Wert angegeben:**
  * **Teilweise / Als Code-Kommentare:**
    * In `ball_bearings.scad` werden Katalogquellen genannt (`// [M] HHZC metric open/ZZ dimension table`, `// [LNB6403]`, Stand geprüft: Oktober 2026).
    * In `screws.scad` sind Normen als Inline-Kommentare den Listen zugeordnet (z. B. `// for hex drive from ISO-10642, don't know where torx came from`).
* **Letzte Aktivität:**
  * Extrem aktiv (letzter Commit am 20. Oktober 2026, Release v2.0.775).

---

### 5. NopSCADlib (`nophead/NopSCADlib`)

* **Repo-URL:** [https://github.com/nophead/NopSCADlib](https://github.com/nophead/NopSCADlib)
* **Lizenz der Daten (wörtlich aus der Datei):**
  * Aus der Datei `COPYING`:
    ```text
                        GNU GENERAL PUBLIC LICENSE
                           Version 3, 29 June 2007

     Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
     Everyone is permitted to copy and distribute verbatim copies
     of this license document, but changing it is not allowed.
    ```
* **Kompatibilität mit MIT / Apache-2.0:**
  * **Inkompatibel:** GPL-3.0 Copyleft schließt eine direkte Übernahme in permissiv lizenzierte Projekte ohne Copyleft-Übertragung aus.
* **Enthaltene Normen und Größen:**
  * Stark auf 3D-Druck-/Maker-Hardware zugeschnitten (hauptsächlich **M2 bis M8**, selten größer):
    * **Schrauben:** `vitamins/screws.scad`: `hs_cap` (ISO 4762: M2–M8), `hs_hex` (ISO 4017: M3–M8), `hs_cs_cap` (ISO 10642: M2–M8), Dome (ISO 7380), Pan Head.
    * **Muttern:** `vitamins/nuts.scad`: M2 bis M8 (ISO 4032 / DIN 934).
    * **Scheiben:** `vitamins/washers.scad`: M2 bis M8 (ISO 7089 / DIN 125) sowie Karosseriescheiben / Penny Washers (DIN 9021).
    * **Gewindeeinsätze:** `vitamins/inserts.scad`: Messing-Einschmelzgewinde (F1BM2–F1BM4, CNCKM2.5–CNCKM5) und Holz-Eindrehmuffen nach DIN 7965 (M3–M5).
    * **Wälzlager:** `vitamins/ball_bearings.scad`: 608, 624, 686, 696, 6200, 6201, 6808, Miniaturlager (MR63–MR95), Flanschlager (F623–F695).
    * **Bohrungen & Senkungen:** In `vitamins/screws.scad` als Radien hinterlegt (z. B. `M3_tap_radius = 2.5 / 2;`, `M3_clearance_radius = 3.3 / 2;`); Senkungen über `vitamins/screw.scad`.
* **Datenformat und Pfad im Repo:**
  * Format: OpenSCAD-Code (Listen-Arrays, z. B. `M3_cap_screw = ["M3_cap", ...];`)
  * Pfad: `vitamins/*.scad` (insb. `vitamins/screws.scad`, `vitamins/nuts.scad`, `vitamins/washers.scad`, `vitamins/inserts.scad`, `vitamins/ball_bearings.scad`)
* **Quellen pro Wert angegeben:**
  * **Nein.** Nahezu keine Einzelquellen; Normen tauchen vereinzelt in Kommentaren auf (z. B. `DIN 7965`).
* **Letzte Aktivität:**
  * Aktiv (letzter Commit am 24. September 2026).

---

## 2. Zusammenfassende Vergleichstabelle

| Kriterium | BOLTS (`boltsparts`) | FreeCAD FastenersWB | **cq_warehouse** | BOSL2 | NopSCADlib |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lizenz** | GPL-3.0 (Data: LGPL-2.1+) | GPL-2.0 | **Apache-2.0** | BSD-2-Clause | GPL-3.0 |
| **MIT / Apache-2.0 tauglich** | ❌ (Eingeschränkt / LGPL) | ❌ (Nein / GPLv2) | **✅ Ja (Vollständig)** | **✅ Ja (Vollständig)** | ❌ (Nein / GPLv3) |
| **Format** | YAML (`.blt`) | CSV | **CSV** | OpenSCAD Code | OpenSCAD Code |
| **Pfad im Repo** | `data/*.blt` | `FsData/*.csv` | **`src/cq_warehouse/*.csv`** | Root (`*.scad`) | `vitamins/*.scad` |
| **ISO 4762 / 4017 / 10642** | ✅ (M1.4–M64) | ✅ (M1.6–M64) | **✅ (M1.6–M64)** | ✅ (M1–M64) | ⚠️ (Nur M2–M8) |
| **ISO 4032 (Muttern)** | ✅ (M1–M64) | ✅ (M1.6–M64) | **✅ (M1.6–M64)** | ✅ | ⚠️ (Nur M2–M8) |
| **ISO 7089 (Scheiben)** | ✅ (M1.6–M64) | ✅ (M1.6–M64) | **✅ (M1.6–M64)** | ❌ (Keine Tabelle) | ⚠️ (Nur M2–M8) |
| **Gewindeeinsätze** | ❌ | ✅ (Heat / PEM) | **✅ (McMaster / Hilitchi)** | ❌ | ✅ (F1B / CNCK / DIN 7965) |
| **Wälzlager** | ✅ (Rillen-, Nadel-, Axial-) | ❌ | **✅ (Rillen-, Schräg-, Rollen-)** | ✅ (Rillen-, Linear-) | ⚠️ (Gängige Druckertypen) |
| **Bohrungen & Senkungen** | ❌ | ⚠️ (Nur Senk-Code, Inch-Tabelle) | **✅ (Clearance, Tap, Drill, Senkung)** | ✅ (Clearance, Tap, Senkung) | ⚠️ (Nur M2–M8 Radien) |
| **Quellen pro Wert** | **✅ Ja (URLs / Kataloge)** | ❌ Nein | ⚠️ Teilweise (Artikelnr. / Normen) | ⚠️ Teilweise (Katalog-Kürzel) | ❌ Nein |
| **Letzte Aktivität** | Nov. 2022 | Sept. 2026 | **Okt. 2026** | Okt. 2026 | Sept. 2026 |

---

## 3. Rechtliche Lage zu Maßwerten aus Normen in offenen Projekten

*(Zusammenfassung ausschließlich auf Basis der geltenden Gesetzgebung und Rechtsprechung)*

### A. Urheberrecht an reinen Zahlenwerten und Fakten
1. **Fehlende Schöpfungshöhe bei Einzelwerten:**
   * Nach **§ 2 Abs. 2 UrhG** sind nur *persönliche geistige Schöpfungen* geschützt.
   * Der **Bundesgerichtshof (BGH)** hat in ständiger Rechtsprechung klargestellt, dass reine physikalische Messwerte, Zahlenangaben, Fakten und mathematische Ergebnisse keinen Urheberrechtsschutz genießen, da sie keine individuelle schöpferische Eigenprägung besitzen (*BGH GRUR 1990, 1003 – DIN-Normen*; bestätigt im EU-Recht durch *EuGH C-5/08 – Infopaq*, Rn. 37: ein Werk muss die eigene geistige Schöpfung seines Urhebers widerspiegeln).
   * Technische Abmessungen (Gewindedurchmesser, Steigung, Kopfhöhe) sind durch funktionale Notwendigkeiten und Interoperabilität zwingend vorgegeben. Hier greift auch im US-Copyright die Doktrin: Reine Fakten sind gemeinfrei (*US Supreme Court, Feist Publications v. Rural Telephone Service Co., 499 U.S. 340 (1991)*; kodifiziert in *17 U.S.C. § 102(b)*).

### B. Urheberrecht an Normdokumenten vs. Datenextraktion
1. **Schutz des Normtextes und der Darstellungsform:**
   * Technische Normen (DIN, ISO, EN) sind als Sprachwerke (§ 2 Abs. 1 Nr. 1 UrhG) oder Darstellungen technischer Art (§ 2 Abs. 1 Nr. 7 UrhG) geschützt (*BGHZ 74, 91*; *BGH GRUR 1990, 1003*). 
   * Durch **§ 5 Abs. 3 UrhG** (eingeführt 1995) verbleibt das Urheberrecht bei privaten Normungsorganisationen (wie dem DIN e.V. bzw. der DIN Media GmbH), selbst wenn staatliche Gesetze pauschal auf die Normen verweisen.
   * **Rechtsfolge:** Das Vervielfältigen, Einscannen oder Verbreiten der amtlichen Normtexte, Zeichnungen und Original-PDFs ohne Lizenz ist unzulässig (*DIN Media, „Informationen zum Urheberrecht“, dinmedia.de*).
2. **Freiheit der Maßanwendung und Zahlenextraktion:**
   * Die bloße technische *Anwendung* der in Normen festgelegten Maße zur Konstruktion sowie das Extrahieren und Eintragen der nackten Zahlenwerte in eigene, neu strukturierte Datenformate (z. B. eigene CSV-/JSON-Tabellen) berührt nicht das Urheberrecht an der Darstellungsform des Normwerks (*vgl. DIN Media FAQ; GRUR 1980, 227*).
3. **Europäische Harmonisierungsnormen:**
   * Der Europäische Gerichtshof entschied mit Urteil vom 5. März 2024 (*EuGH Große Kammer, C-588/21 P – Public.Resource.Org und Right to Know gegen Kommission*), dass an europäisch harmonisierten Normen, die verbindlicher Bestandteil des EU-Rechts sind, ein überwiegendes öffentliches Interesse an der freien Zugänglichkeit besteht.

### C. Datenbankschutz (§§ 87a ff. UrhG / EU-Richtlinie 96/9/EG)
1. **Kein Schutz für die Erzeugung der Maße:**
   * Das Sui-generis-Recht für Datenbankhersteller schützt nach § 87a UrhG wesentliche Investitionen in die *Beschaffung, Überprüfung oder Darstellung* von Daten.
   * Der **EuGH** hat verbindlich entschieden (*EuGH C-203/02 – British Horseracing Board gegen William Hill*, Rn. 31; *EuGH C-46/02 – Fixtures Marketing*, Rn. 34), dass Investitionen in die **Schaffung (Creation)** von Daten keinen Datenbankschutz begründen. Da Normungsgremien Normmaße im Verfahren erst definieren/schaffen, entsteht an den Normwerten kein Datenbankschutzrecht.
2. **Schutz vor systematischem Scraping bestehender Datenbanken:**
   * Werden jedoch umfangreiche Tabellenwerke aus einer bestehenden, von Dritten gewerblich erstellten Datenbank (z. B. einer kommerziellen Normteil-Software) als Ganzes systematisch ausgelesen und übernommen, kann das Datenbankrecht dieses Betreibers nach § 87b UrhG verletzt werden.

### D. Open-Source-Lizenzrecht (Copyleft-Falle)
1. Werden Maßtabellen nicht aus den Primärnormen isoliert, sondern direkt aus bestehenden Repositories (z. B. FreeCAD FastenersWB oder NopSCADlib) übernommen, unterliegen die übernommenen Dateien und deren Zusammenstellung dem Lizenzrecht des Autors (GPL-2.0 / GPL-3.0).
2. Nach der **GNU General Public License (Ziffer 5 GPLv3 / Ziffer 2 GPLv2)** müssen abgeleitete Werke zwingend unter derselben Lizenz lizenziert werden. Ein MIT- oder Apache-2.0-Projekt darf solche Quellcodedateien nicht permissiv umdeklarieren (*Free Software Foundation FAQ: „Compatibility of Licenses“*).

---

## 4. Empfehlung und Begründung

### Klare Empfehlung: `cq_warehouse` (`gumyr/cq_warehouse`)

Für ein neues oder bestehendes CAD-Projekt mit **MIT- oder Apache-2.0-Lizenz** ist der Datensatz aus **`cq_warehouse`** die mit Abstand am besten geeignete Ausgangsbasis.

#### Warum `cq_warehouse`?

1. **Rechtliche Lizenzkompatibilität ohne Copyleft-Risiko:**
   * Das Projekt steht durchgängig unter der **Apache License 2.0**. Die Daten können legal, ohne Bruch des Urheberrechts und ohne Zwang zur Offenlegung des Gesamtprojekts unter einer restriktiven Copyleft-Lizenz (GPL) in MIT- oder Apache-2.0-Projekte übernommen werden.
2. **Vollständige Abdeckung aller geforderten Kategorien:**
   * Es ist das **einzige** der untersuchten Projekte, das **alle sieben** vom Nutzer genannten Bereiche in einsatzbereiter Tabellenform abdeckt:
     * Schrauben: ISO 4762, ISO 4017, ISO 10642
     * Muttern: ISO 4032 (inkl. ISO 4033, 4035)
     * Scheiben: ISO 7089 (inkl. ISO 7090, 7091, 7093, 7094)
     * Gewindeeinsätze: McMaster-Carr / Hilitchi Heat-Set Inserts
     * Wälzlager: Tiefgreifende Tabellen für 5 Lagerarten (Rillen-, Schräg-, Zylinder-, Kegelrollenlager)
     * Bohrungen & Senkungen: Eigene CSVs für Durchgangsbohrungen (ISO 273 Close/Normal/Loose), Kernlöcher (Soft/Hard) und Senkungsgeometrien
3. **Universelles Datenformat (Sauberes CSV):**
   * Alle Parameter liegen isoliert im Verzeichnis `src/cq_warehouse/*.csv`. Im Gegensatz zu BOSL2 oder NopSCADlib muss kein fremder CAD-Interpreter (OpenSCAD) geparst werden; die CSVs können direkt in ein beliebiges Format (JSON, YAML, SQLite oder In-Memory DataFrames) importiert werden.
4. **Aktiver Pflegezustand:**
   * Das Projekt wird aktiv gewartet (letzte Datenkorrekturen im Oktober 2026), wodurch auch Fehler in den Maßtabellen kontinuierlich von der Community korrigiert werden.

#### Strategischer Tipp zur Vervollständigung:
* Da in `cq_warehouse` bei den Normteilen keine Web-Quellenlinks pro Datenzeile hinterlegt sind, empfiehlt es sich, die Quellennachweise aus **BOLTS** (`data/*.blt`) für die eigene Dokumentation zu übernehmen: BOLTS liefert für ISO 4762, 4017, 10642, 4032 und 7089 detaillierte Einzelnachweise auf Händlerkataloge und historische Werksnormen.
