# Inventor-Nachprüfung der Fusion-Punkte 7, 8, 9, 12, 13

Stand: 2026-10-27. Nachprüfung von fünf Punkten der Auswertungsliste ([2026-10-26-fusion-vs-inventor-liste.md](2026-10-26-fusion-vs-inventor-liste.md), Nr. 7, 8, 9, 12, 13) gegen Autodesk Inventor (2025/2026): Kann Inventor die jeweilige Funktion inzwischen auch, und seit welcher Version?

Grundlage der Belege sind die offiziellen Autodesk-Hilfeseiten (`help.autodesk.com`).

> **Prüfvermerk 2026-10-27 (Claude, Argon-Review):** Bewertungen und Zitate sind belegt (`check_sources.py` 5/5). Die Angaben „seit Version …“ stehen nicht in den Quellen und sind nur Schätzungen. Punkt 12 („nein“) gilt laut Hilfe 2025; ob Inventor 2026 modellierte Gewinde nachgereicht hat, ist nicht geprüft.

---

## Detailprüfung der Punkte

### Punkt 7: Sich überschneidende Skizzenlinien ergeben einzeln wählbare Profile

* **Ergebnis:** teilweise
* **Version:** Mehrere und sich schneidende Konturen/Bereiche werden seit Inventor 1 / R1 unterstützt. Eine vollautomatische Schnittmengen-Segmentierung wie in Fusion 360 (ohne Teilen/Stutzen) gibt es bis heute (Inventor 2025/2026) nicht.
* **Quelle:** [Autodesk Inventor 2025 Hilfe: So arbeiten Sie mit Skizzenprofilen](https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-4110FA02-0A8A-41F7-85B5-384819DAC528.htm)
* **Zitat:** „Ein Profil kann aus einer einzigen Kontur, mehreren Konturen, sich schneidenden Konturen oder Inseln bestehen. Sie können auf einer planaren Bauteilfläche skizzieren und eine oder mehrere geschlossene Konturen als Profil auswählen. Alle in einem einzigen Vorgang ausgewählten Konturen sind ein Profil.“
* **Erläuterung:** 
  * *Was Inventor kann:* Wenn Skizzen aus geschlossenen Konturen bestehen, die sich an gemeinsamen Kanten berühren oder Inseln bilden, erkennt Inventor diese als wählbare Profile oder Profilbereiche.
  * *Was Fusion besser macht:* In Fusion 360 wird jede freie Überkreuzung zweier beliebiger Skizzenlinien (auch ohne Endpunkte/Knoten, wie etwa zwei überlappende Kreise oder eine durchgezogene X-Linie) automatisch in einzeln wählbare Flächenprofile unterteilt. In Inventor hingegen führt das Überkreuzen von Linien ohne Knotenpunkte zu selbstdurchdringenden Schleifen (*self-intersecting loops*) oder Inventor wählt nur die Gesamtkontur aus. Der Anwender muss die Geometrie in Inventor erst mit *Stutzen* (Trim) oder *Teilen* (Split) aufbrechen oder explizite Skizzenpunkte auf den Schnittpunkt setzen.

---

### Punkt 8: Maße beim Zeichnen eintippen, Tab zum nächsten Wert (Heads-Up Display / Direkteingabe)

* **Ergebnis:** ja
* **Version:** Inventor 2011 (eingeführt 2010 unter dem Namen Heads-Up Display / Dynamische Eingabe)
* **Quelle:** [Autodesk Inventor 2025 Hilfe: 2D-Geometrie der dynamischen Eingabe zeichnen](https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-33A8B11D-A04C-4809-BC82-C0419215915F.htm)
* **Zitate:**
  * „Inventor bietet eine optionale exponierte Anzeige (HUD), die Ihnen hilft, sich bei der Arbeit mit den vielen 2D-Skizziergeometriewerkzeugen auf den Skizzierbereich zu konzentrieren. Die exponierte Anzeige ermöglicht die Eingabe von Werten in verschiebbare Werteingabefelder, die sich stets in der Nähe des Cursors befinden. Die Werte werden beim Bewegen des Cursors dynamisch aktualisiert.“
  * „Drücken Sie die TABULATORTASTE, um zum nächsten Eingabefeld zu wechseln.“
* **Erläuterung:** 
  * Inventor besitzt die direkte Maßeingabe am Mauszeiger (Heads-Up Display / HUD, in der deutschen Oberfläche als *Exponierte Anzeige* bzw. *Dynamische Eingabe* bezeichnet) seit Inventor 2011.
  * Beim Zeichnen von Linien, Kreisen, Bögen und Rechtecken blendet Inventor Werteingabefelder direkt neben dem Cursor ein. Über die Tab-Taste springt man zwischen den Feldern (z. B. Länge und Winkel), wodurch der Wert gesperrt wird. Bei Bestätigung mit der Eingabetaste wird automatisch eine permanente parametrische Skizzenbemaßung erzeugt. Die Prüfnotiz in der Vergleichsliste (*Inventor hat die Direkteingabe, vermutlich überholt*) ist damit bestätigt.

---

### Punkt 9: Kanten beim Skizzieren automatisch projizieren/fangen

* **Ergebnis:** ja
* **Version:** Seit frühen Versionen (mindestens Inventor 10 / R11 / 2008 / 2010), seit über 15 Jahren Standard
* **Quelle:** [Autodesk Inventor 2025 Hilfe: Registerkarte Skizze - Referenz (Anwendungsoptionen)](https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-1898C432-CFD2-46F1-8BAE-631392DFBF1D.htm)
* **Zitate:**
  * „Projiziert beim Erstellen oder Bearbeiten einer Skizze die Kanten einer ausgewählten Fläche automatisch als Referenzgeometrie auf die Skizzierebene.“
  * „Ermöglicht das Auswählen und Projizieren vorhandener Geometrie auf die aktuelle Skizze durch [...] bestehender Linien. Die Linien werden als Referenzgeometrie projiziert.“
* **Erläuterung:** 
  * Inventor bietet zwei getrennte Optionen unter *Extras > Anwendungsoptionen > Registerkarte Skizze*:
    1. *Modellkanten für Skizzenerstellung und -bearbeitung automatisch projizieren*: Erzeugt man eine Skizze auf einer vorhandenen Bauteilfläche, werden alle Kanten dieser Fläche sofort als Referenzgeometrie projiziert.
    2. *Modellkanten bei Erstellung von Skizzen automatisch projizieren*: Beim Zeichnen reicht das einfache Berühren (Hovern) einer Kante mit dem Cursor, um sie automatisch als Referenzlinie in die Skizze zu übernehmen und zu fangen.
  * Die Prüfnotiz in der Vergleichsliste (*Inventor projiziert Kanten automatisch (Option), vermutlich überholt*) ist damit bestätigt.

---

### Punkt 12: Modellierte (echte 3D-)Gewinde per Ein-Klick-Checkbox

* **Ergebnis:** nein
* **Version:** In keiner Inventor-Version bis einschließlich Inventor 2025/2026 nativ vorhanden
* **Quelle:** [Autodesk Inventor 2025 Hilfe: So Erstellen Sie Gewinde](https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-C0848D58-12CB-4605-8165-0836232927F0.htm)
* **Zitat:** „Um maximale Leistung sicherzustellen, werden die Gewinde in Inventor in einer dekorativen Darstellung, oder Textur, angezeigt, es werden nicht die tatsächlichen Gewinde modelliert.“
* **Erläuterung:** 
  * Die Prüfnotiz in der Vergleichsliste (*Inventor hat modellierte Gewinde seit ca. 2022, vermutlich überholt*) ist nicht zutreffend.
  * Der native Gewindebefehl in Inventor erzeugt bis heute ausschließlich kosmetische Texturen auf Zylindern, um große Baugruppen performant zu halten. Eine Checkbox wie *Modelliert* in Fusion 360 gibt es in Inventor nativ nicht.
  * Wer in Inventor echte 3D-Gewinde benötigt (z. B. für den 3D-Druck), muss entweder manuell eine Spirale (*Coil*) mit Schnittprofil modellieren, externe Werkzeuge wie das Add-In *coolOrange threadModeler* installieren oder das Bauteil in Fusion 360 erstellen.

---

### Punkt 13: Direktes Bearbeiten importierter STEP-Flächen (Direct Edit)

* **Ergebnis:** ja
* **Version:** Inventor 2015 (eingeführt 2014)
* **Quelle:** [Autodesk Inventor 2025 Hilfe: Direktbearbeitungen anwenden](https://help.autodesk.com/cloudhelp/2025/DEU/Inventor-Help/files/GUID-96463E7B-A7E1-4DA5-B579-C4F346015AD7.htm)
* **Zitate:**
  * „Mithilfe der Direktbearbeitung können Sie die Größe, Form und/oder Position von Modellelementen anpassen, indem Sie die Geometrie direkt ändern.“
  * „Verwenden Sie die Direktbearbeitung, um [...] importierte Basisbauteile zu ändern, das ursprüngliche Modell aber beizubehalten.“
* **Erläuterung:** 
  * Inventor besitzt seit Version 2015 das dedizierte Werkzeug *Direktbearbeitung* (Direct Edit) unter *3D-Modell > Ändern*.
  * Damit können importierte Fremdformate (STEP, IGES, SAT) ohne Feature-Historie direkt modifiziert werden: Flächen und Körper lassen sich verschieben, drehen, in der Größe ändern (z. B. Durchmesser von Bohrungen/Zylindern) oder löschen.
  * Die Direktbearbeitung erzeugt im Modellbaum von Inventor parametrische Einträge und Parameter, die auch nachträglich editiert werden können. Die Prüfnotiz (*Inventor hat 'Direkt bearbeiten'*) ist damit bestätigt.

---

## Zusammenfassung

| # | Punkt | Kann Inventor das? | Seit Version | Inventor-Funktion / Anmerkung |
|---|---|---|---|---|
| 7 | Sich überschneidende Skizzenlinien ergeben einzeln wählbare Profile | teilweise | Inventor 1 / R1 (teilweise) | Geschlossene Konturen/Inseln wählbar; freies Überkreuzen ohne Knoten erfordert Teilen/Stutzen oder Skizzenpunkte (in Fusion vollautomatisch). |
| 8 | Maße beim Zeichnen eintippen, Tab zum nächsten Wert | ja | Inventor 2011 | Exponierte Anzeige (Heads-Up Display / HUD) mit Direkteingabe, `Tab`-Wechsel und Wertesperre. |
| 9 | Kanten beim Skizzieren automatisch projizieren/fangen | ja | Inventor 10 / 2008 | Anwendungsoptionen: Modellkanten für Skizzenerstellung... und Modellkanten bei Erstellung... (durch Berühren). |
| 12 | Modellierte (echte 3D-)Gewinde per Ein-Klick-Checkbox | nein | nicht vorhanden | Nativ nur kosmetische Texturen (Performance-Entscheidung); 3D-Gewinde nur per Spirale (Coil) oder Add-In. Prüfnotiz ca. 2022 war falsch. |
| 13 | Direktes Bearbeiten importierter STEP-Flächen | ja | Inventor 2015 | Befehl Direktbearbeitung (Direct Edit) im 3D-Modell-Menü; verschiebt, skaliert, dreht und löscht Flächen historienbasiert. |
