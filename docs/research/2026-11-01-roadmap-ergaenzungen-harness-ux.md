# Roadmap-Ergänzungen: Optimaler KI-Harness & Ingenieurs-CAD für Menschen

**Stand:** 2026-11-01  
**Bezug:** `ROADMAP.md` (Stand 2026-10-31 / 2026-11-01), ADR 0001 (SolidCraft-Schicht), ADR 0002 (Wissenskatalog), ADR 0003 (Point & Speak), ADR 0005 (Eigene Oberfläche).

Ziel dieser Ergänzungen ist es, die verbleibenden Lücken zwischen einem **optimalen Ausführungsumfeld für KI-Agenten (Harness)** und einem **verlässlichen, nachvollziehbaren Ingenieurs-Werkzeug nach Inventor-Vorbild** zu schließen.

---

## 1. Phase 1: Rund um v0.1, MCP-Schicht & Konstrukteurs-Agent

### 1.1 Bauteilende-Marker (End-of-Part / EOP) als aktives MCP-Werkzeug
In Grundsatz 5 ist der Inventor-typische Bauteilende-Marker bereits für das Datenmodell festgelegt. Neben der reinen UI-Bedienung für Menschen ist er eines der wichtigsten Debugging-Werkzeuge für den Konstrukteurs-Agenten.
* **Problem:** Ändert oder repariert der Agent in einem Bauteil mit 20+ Features ein frühes Feature (z. B. `Extrusion_2`), lösen nachfolgende Fasen und Bohrungen oft Kaskadenfehler aus (wie `#34` *lumps: shell boundaries intersect*), die die Fehlerlokalisierung erschweren.
* **Lösung (`set_eop_marker`):** Der Agent erhält ein MCP-Werkzeug (und die entsprechende Regel im Skill `konstrukteur`), um den Bauteilende-Marker gezielt vor die Fehlerstelle zu setzen, dort im isolierten Zustand zu messen (`measure`), die Skizze/Extrusion zu heilen und den Marker danach Schritt für Schritt wieder herunterzuziehen.

### 1.2 Nutzersperren („User-Locks“) & geschützte Funktionsflächen
Wenn Mensch und Agent abwechselnd über **Point and speak** (ADR 0003) und die **eigene Oberfläche** (ADR 0005) am selben Teil arbeiten, entsteht ein klassischer Konflikt: Der Agent „optimiert“ bei einer automatischen Korrektur (`check_design`-Befund beheben) versehentlich ein Anschlussmaß weg, das der Mensch bewusst festgelegt hat.
* **Lösung im Datenmodell:** Parameter, Skizzenmaße und Features erhalten in der Mechvane-Schicht ein Attribut `locked_by_user: true` (im Inventor-Modellbrowser als kleines Schloss-/Pin-Icon sichtbar).
* **Harness-Wirkung:** Versucht der Agent über MCP, einen gesperrten Parameter zu ändern oder eine als „Funktionsfläche / Keep-Out“ markierte Fläche zu überschneiden, blockiert die Mechvane-Schicht den Aufruf sofort mit einer sprechenden Meldung (z. B. *„Parameter `d_welle = 20 mm` ist durch Nutzer gesperrt (Anschlussmaß) – bitte stattdessen Außenwand anpassen“*).

### 1.3 Adaptive Projektion in Baugruppen (`project_geometry`)
Ergänzend zu `edit_in_place` / `finish_edit` und als robuster Workaround für verlorene Flächennamen über Verknüpfungen hinweg (SolidCraft `#3330`):
* **Lösung:** Konstruiert der Agent in einer Baugruppe „an Ort und Stelle“ ein zweites Bauteil passend zum ersten (z. B. Deckel auf Gehäuse, Rohrhalter), kopiert er keine starren Weltkoordinaten. Ein MCP-Befehl `project_geometry(source_part, face_or_edge, adaptive=True)` (analog zu Inventors „Geometrie projizieren“ mit Adaptivität) speichert im Zielbauteil die semantische Abfrage (`find`) der Quellfläche.
* **Wirkung:** Ändert sich das Quellbauteil, löst das Aktualisieren der Baugruppe die gespeicherten semantischen Abfragen neu auf und zieht die projizierten Skizzenelemente sauber nach.

---

## 2. Phase 1b / Eigene Oberfläche (ADR 0005)

### 2.1 Visuelles 3D-Diff („Vorschau & Freigabe“) bei größeren Agenten-Eingriffen
Bei kurzen **Point and speak**-Befehlen („Da eine Fase $1 \times 45^\circ$“) soll das Ergebnis sofort sichtbar sein. Führt der Agent jedoch einen größeren Auftrag aus (z. B. *„Passe den Lagerbock an ein 6004er Lager an und korrigiere die Verschraubung“*), ändert er mehrere Stellen im Baum gleichzeitig.
* **UX-Brücke Mensch ↔ Agent:** Da die eigene Oberfläche `three.js` nutzt, behält Mechvane vor einem Agenten-Batch das vorherige Mesh im Speicher und blendet es auf Wunsch als dezentes Drahtgitter oder halbtransparentes „Geister-Volumen“ über den neuen Stand – kombiniert mit einer Diff-Markierung im Modellbrowser (grün: neues Feature, gelb: geänderter Parameter).
* **Mehrwert:** Der Nutzer sieht auf einen Blick, was der Agent verändert hat, und kann Änderungen gezielt annehmen oder verwerfen, statt blind `Undo` auszuführen.

### 2.2 Herkunft von Maßen im Baum („Design-Intent-Provenance“)
Wenn der Agent mit dem **Regelkatalog** (ADR 0002) und den **aus Werkstoffkennwerten hergeleiteten Formeln** (`#14`, z. B. $m_{\text{eff}} = \frac{A_s \cdot R_m}{A_n' \cdot \tau_B}$) konstruiert, ist für den Menschen später oft nicht mehr ersichtlich, *warum* eine Wand genau $4{,}2\text{ mm}$ dick ist oder warum das Sackloch $9{,}5\text{ mm}$ tief wurde.
* **Lösung:** Jedes Mal, wenn der Agent oder ein Assistent (`bolted_connection`) ein Maß berechnet oder aus dem Katalog setzt, schreibt er automatisch die Herleitung inkl. Quellen-/Katalog-ID in das Kommentarfeld des Parameters (z. B. `t_ein = 9.5 mm // Hergeleitet: m_eff für M6 (8.8) in EN AW-6060 + 1.5 mm Auslauf`).
* **UI-Darstellung:** In der eigenen Oberfläche erscheint diese Begründung direkt als Tooltip am Parameter und im Feature-Dialog.

---

## 3. Phase 2: Fachmodule, Import & Slicer

### 3.1 Slicer-Feedback-Schleife für den Konstrukteurs-Agenten (`check_slicing`)
Das geplante grafische Slicer-Modul bindet `CuraEngine` ohnehin als Hintergrundprozess (CLI bzw. Arcus/Protobuf) an. Dieselbe Schnittstelle lässt sich als hochpräziser DFM-Sensor für den Agenten nutzen:
* **Lösung:** Ergänzend zu den geometrischen B-Rep-Regeln in `check_design(profile="fdm_0.4")` führt ein Werkzeug `check_slicing(part)` im Hintergrund einen schnellen Slice-Durchlauf mit dem gewählten Ultimaker-/Cura-Profil durch.
* **Rückmeldung an den Agenten:** Reale Pfade statt Daumenregeln – das Tool meldet exakt zurück, an welchen Flächen Stützstruktur (`SUPPORT`) erzeugt würde, wo kritische Brücken (`BRIDGE`) entstehen oder wo dünne Wände im Slicer wegfallen bzw. auf nur einen Perimeter abmagern.

### 3.2 Toleranz- & Passungsprüfung über Baugruppen-Gelenke
Aufbauend auf `iso_fit` (ISO 286) und den geplanten Passungsattributen an Bohrung und Welle:
* **Lösung:** Sobald in einer Baugruppe ein Gelenk (`cylindrical` oder `revolute`) zwischen zwei Bauteilen gesetzt wird, prüft `check_joints` automatisch die Paarung der zugewiesenen ISO-Passungen sowie der Nennmaße (z. B. Warnung bei Nennmaß-Abweichung $\varnothing 20\text{ mm}$ auf $\varnothing 20{,}2\text{ mm}$, fehlender Passungsangabe am Gegenstück oder Widerspruch zwischen Gelenkart und Übermaßpassung). Zahlt direkt auf den Benchmark **„Lagerstelle“** ein.

### 3.3 Agenten-gestützte „Hybrid-Heilung“ beim nativen CAD-Import (`cadmpeg`)
Zu Grundsatz 7 (Umstieg ohne Verlust; nicht direkt abbildbare Features bleiben als Platzhalter samt Original-B-Rep und Originalparametern im Baum):
* **Lösung:** Bleiben nach dem deterministischen Import über `cadmpeg` einzelne komplexe Features als Platzhalter im Baum stehen, übernimmt auf Wunsch ein spezialisierter MCP-Agent die Nachkonvertierung.
* **Ablauf:** Der Agent erhält das B-Rep *vor* dem Platzhalter, das Soll-B-Rep *nach* dem Platzhalter sowie die dekodierten Originalparameter aus der Fremddatei. Er versucht iterativ, das Feature mit nativen SolidCraft-Befehlen nachzubauen, bis die Abweichung (Volumen, Schwerpunkt, Hüllquader, Flächenzahl analog zu `check.py`) gegen $0$ geht.

---

## 4. Phase 3: Fertigungszeichnungen

### 4.1 Semantische PMI-Vererbung aus dem 3D-Feature-Baum
Damit das Ziel **„Agent leitet Zeichnung ab (fertigungsgerecht bemaßt, prüft auf Über- und Unterbemaßung)“** zuverlässig funktioniert, darf der Agent in 2D nicht auf reine Liniengeometrie aus dem Hidden-Line-Removal angewiesen sein.
* **Lösung:** Jede projizierte 2D-Kante und jeder Kreisbogen in der Zeichnungsansicht behält seine Referenz auf das erzeugende 3D-Feature und dessen Metadaten (z. B. *„Kante gehört zu `bolted_connection_2`, Gewinde M6, Tiefe $12\text{ mm}$, Passung `H7`“* oder *„Kehlnaht $a=3$ aus Schweiß-Feature `#19`“*).
* **Wirkung:** Der Zeichnungs-Agent liest die Fertigungssemantik (Bezugskanten der Skizzen, Bohrungsgruppen, Passungen, Oberflächen, Schweißsymbole nach ISO 2553) direkt aus dem Modellbaum und übernimmt in `CADCraft` nur noch die normgerechte, kollisionsfreie Platzierung der Maße.

---

## Kopiervorlage für `ROADMAP.md` (Kompakt-Blöcke)

Falls du einzelne Punkte direkt in deine `ROADMAP.md` übernehmen möchtest, sind sie hier im passenden Format vorbereitet:

```markdown
### Ergänzungen Phase 1 (MCP, Agent & UI)
- [ ] **Bauteilende-Marker (EOP) über MCP steuern**: `set_eop_marker` für den Agenten, um bei Fehlern (z. B. `#34`) den Baum vor die Fehlerstelle zurückzurollen, isoliert zu messen/reparieren und schrittweise wieder vorzurücken (Regel im Skill `konstrukteur`).
- [ ] **Nutzersperren (User-Locks) im Baum**: Parameter, Maße und Funktionsflächen als „vom Nutzer festgelegt“ sperren (`locked_by_user`); MCP blockiert Änderungen durch den Agenten mit sprechender Meldung.
- [ ] **Herkunft von Maßen (Provenance) speichern**: Berechnete Maße aus Regelkatalog (ADR 0002) und Werkstoffformeln (`#14`) speichern automatisch ihre Formel/Quelle als Kommentar am Parameter (sichtbar als Tooltip in der eigenen Oberfläche).
- [ ] **3D-Diff bei Agenten-Änderungen**: Vor größeren Agenten-Eingriffen altes Mesh in `three.js` als halbtransparente Vorschau gegen den neuen Stand vergleichen, inkl. Diff-Markierung im Modellbrowser.

### Ergänzungen Phase 2 (Fachmodule & Import)
- [ ] **Adaptive Geometrieprojektion in Baugruppen**: `project_geometry` mit gespeicherter semantischer Abfrage (`find`), damit an Ort und Stelle konstruierte Anschlussbauteile bei Maßänderungen mitwandern (auch als Brücke für `#3330`).
- [ ] **Passungsprüfung über Baugruppen-Gelenke**: `check_joints` prüft an Wellen-/Naben-Verbindungen, ob Nennmaße und `iso_fit`-Passungen von Bohrung und Welle zueinander und zum Freiheitsgrad passen.
- [ ] **Slicer-Prüfung für den Agenten (`check_slicing`)**: `CuraEngine` headless nutzen, um dem Konstrukteurs-Agenten reale Stützstrukturen, kritische Brücken und zu dünne Wände vorab als Befund zurückzumelden.
- [ ] **Agenten-Heilung für Platzhalter beim CAD-Import**: Nicht direkt übersetzbare Features aus `cadmpeg` (Platzhalter mit Soll-Körper) durch den Agenten iterativ mit SolidCraft-Befehlen nachbauen lassen, geprüft gegen das Original-Volumen.

### Ergänzungen Phase 3 (Zeichnungen)
- [ ] **Semantische 3D→2D-Vererbung für Zeichnungen**: Projizierte Kanten in der 2D-Ansicht behalten ihre Feature-Herkunft (Bohrungsassistent, `iso_fit`, Schweißnaht `#19`), damit der Agent fertigungsgerecht bemaßt statt Geometrie zu raten.
```