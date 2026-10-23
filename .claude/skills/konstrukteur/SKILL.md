---
name: konstrukteur
description: Konstruktions-Workflow für parametrische CAD-Bauteile in Mechvane (SolidCraft). Gibt den iterativen Ablauf vor (Anforderungen klären → Skizze/Feature → messen → check_design → Snapshot prüfen → korrigieren) mit Konstruktionsregeln (Wandstärken, Randabstände, Einschraubtiefe, Druckbarkeit) und klaren Abbruchkriterien.
---

# Konstrukteurs-Agent (Mechvane)

Dieser Skill leitet den Konstruktions-Workflow für Bauteile und Baugruppen in Mechvane an. Konstruieren ist ein zielgerichteter, iterativer Ingenieursprozess: Anforderungen verstehen, Geometrie analytisch planen, in wenigen kompakten Batches aufbauen, kontinuierlich nachmessen und anhand von Fertigungsregeln validieren.

## Leitprinzipien

1. **Vor dem ersten Werkzeugaufruf rechnen:** Maße, Symmetrieebenen, Bohrungskoordinaten, Wandstärken und Soll-Volumen vorab analytisch festlegen.
2. **Große Batches statt Einzelschritte:** Skizzen und Features in 2–4 zusammenhängenden `run()`-Aufrufen erzeugen (Parameter → Basiskörper → Rundungen/Fasen → Bohrungen/Ausschnitte).
3. **Kosten- und Token-Bewusstsein:**
   - Antworten knapp und technisch präzise halten. Keine unnötigen Erklärungen bekannter CAD-Konzepte.
   - **`body_topology` vermeiden:** Verbraucht 25–45 KB pro Aufruf. Für Verifikation stattdessen `measure` und `check_design` nutzen.
   - `run()` filtert leere Felder und Timings automatisch heraus.
4. **Skizzenregel von Mechvane:** Jede Skizze, die genau ein Feature verbraucht, wird automatisch direkt vor dieses Feature sortiert (`browser()` zeigt sie darunter).

---

## Der Konstruktionsablauf (Schritt für Schritt)

```
1. Anforderungen   --> 2. Vorbereitung  --> 3. Modellierung   --> 4. Regelprüfung  --> 5. Visuelle Prüfung --> 6. Korrektur /
   klären                 & Soll-Werte          (run, measure)        (check_design)       (screenshot)           Abschluss
```

### 1. Anforderungen klären
Vor der Modellerstellung müssen folgende Randbedingungen feststehen:
- **Funktion & Einbauraum:** Abmessungen (L × B × H), Befestigungspunkte, Schnittstellen zu Nachbarbauteilen.
- **Fertigungsverfahren & Profil:**
  - `fdm_0.4` (Standard): FDM 3D-Druck mit 0,4-mm-Düse (Mindestwandstärke 1,2 mm = 3 Perimeter, Mindestbohrung 2,0 mm, Überhang max. 45°).
  - `cnc_alu`: CNC-Fräsen in Aluminium (Mindestwandstärke 1,0 mm, Mindestbohrung 1,0 mm).
- **Verbindungselemente:** Schraubengrößen (z. B. M3, M5, M6), Durchgangs- vs. Gewindebohrung/Sackloch.

### 2. Vorbereitung & Soll-Werte
- Symmetrieursprung wählen: Bauteil zentriert auf Origin (XY/XZ/YZ) anlegen, damit Spiegelungen und Muster Ursprungsebenen nutzen können.
- Parameterliste definieren: Alle Hauptmaße parametrisieren (`parameters.add`), damit Varianten und Anpassungen ohne Geometrie-Neuaufbau möglich sind.
- Soll-Volumen und Bounding Box überschlägig im Kopf berechnen, um Fehler bei Extrusionen oder Booleschen Operationen sofort zu erkennen.

### 3. Modellierung mit Mechvane-Werkzeugen
1. **Bauteildatei anlegen:**
   `new_part(name="lasche")`
2. **Features in logischen Stufen bauen (`run`):**
   - **Stufe 1 (Basis):** Parameter + Skizze + Extrude des Grundkörpers.
   - **Stufe 2 (Formelemente):** Außenradien, Fasen, Taschen. Außenkanten vor Schalenfeatures (`solid.shell`) verrunden.
   - **Stufe 3 (Bohrungen & Verbindungen):** `solid.hole` oder `solid.cylinder` mit `operation: "cut"`.
3. **Verifizieren (`measure` & `browser`):**
   - `measure(document="lasche")` aufrufen: Stimmen `volume_mm3`, `bbox` und `center_of_mass` mit der Berechnung überein?
   - `browser(document="lasche")` prüfen: Liegen Skizzen sauber unter ihren verbrauchenden Features?

### 4. Regelprüfung (`check_design`)
Jedes fertige oder modifizierte Bauteil wird mit `check_design` gegen das gewählte Fertigungsprofil validiert:

`check_design(document="lasche", profile="fdm_0.4")`

Geprüfte Konstruktionsregeln:
- **Randabstand von Bohrungen (`hole_edge_distance`):**
  - Regel: Lochachse zum freien Rand $e \ge 1{,}5 \times d$ (Bohrungsdurchmesser).
  - Bei $d = 6\text{ mm}$ muss der Abstand Lochmitte zur Außenkante mindestens $9{,}0\text{ mm}$ betragen.
- **Mindestwandstärke (`min_wall_thickness`):**
  - Regel: Wandstärke zwischen Bohrungswand und Außenkante ($e - r$) sowie zwischen zwei Bohrungen mindestens $1{,}2\text{ mm}$ (FDM, 3 Perimeter) bzw. $1{,}0\text{ mm}$ (CNC).
  - Regel: Keine massiven Bauteilbereiche dünner als die Profilgrenze.
- **Einschraubtiefe (`thread_depth`):**
  - Regel: Für Sacklöcher und Gewindebohrungen mindestens $1{,}5 \times d_{\text{nom}}$ tragende Gewindetiefe.
  - Gewindebohrungen werden über `model.threads`, `HoleFeature` (`thread: "M..."`) oder ISO-Kernlochdurchmesser (z. B. Ø 2,5 für M3, Ø 4,2 für M5, Ø 5,0 für M6) automatisch erkannt.
  - Beispiel: Für M5-Gewinde muss die tragende Tiefe $\ge 7{,}5\text{ mm}$ sein.
- **Druckbarkeit (`printability`):**
  - Regel: Überhänge $> 45^\circ$ zur Vertikalen ohne Stütze (nach unten gerichtete Flächen $N_z < -0{,}707$ oberhalb der Druckbett-Ebene $z_{\min}$) werden beanstandet.
  - Regel: Kleinste Bohrung $\ge 2{,}0\text{ mm}$ bei 0,4-mm-Düse (Gefahr des Zuwachsens).

### 5. Visuelle Endkontrolle (`screenshot`)
Mit `screenshot(document="lasche", view="iso")` (oder `view="top"`) ein Bild des gerenderten Modells erzeugen und visuell prüfen:
- Zeigen Radien und Fasen in die gewünschte Richtung?
- Sitzen Durchbrüche auf der richtigen Seite?
- Bei Baugruppen: Zeigen montierte Teile nach `add_joint` in die richtige Ausrichtung (kein verdrehter Bolzen)?

### 6. Korrekturschleife & Abbruchkriterien
- **Wenn `check_design` `fail` oder `warn` meldet:**
  - Fehlermeldung und Ort (`location.face`, `location.point`) analysieren.
  - Gezielt korrigieren: Parameter per `run(document, [{"command": "parameters.change", "params": {"name": ..., "expression": ...}}])` anpassen oder Feature per `delete_feature` ersetzen.
  - Erneut `measure` und `check_design` ausführen.
- **Abbruchkriterien:**
  - Maximale Iterationszahl: Wenn nach **3 Korrekturversuchen** ein Regelkonflikt nicht behoben ist (z. B. geometrischer Zielkonflikt: Bauteilaußenmaß lässt rechnerisch keinen Randabstand von $1{,}5 \times d$ zu), **anhalten** und dem Nutzer das Problem mit konkreten Zahlen vorlegen (z. B. „Bauteilbreite 20 mm mit zwei Bohrungen Ø 6 mm erlaubt maximal Randabstand 4 mm; gefordert sind 9 mm. Soll das Bauteil verbreitert oder der Durchmesser reduziert werden?“).

---

## Praxiserfahrungen: Das Klappscharnier-Beispiel

Aus dem Praxistest Klappscharnier (zwei Laschen 40 × 20 × 5, Bolzen Ø 6 × 14, Drehgelenke):

1. **Randabstand-Falle:**
   - Im Ursprungsentwurf lagen zwei Bohrungen Ø 6 bei $x = 8$ und $x = 32$.
   - **Befund von `check_design`:** Randabstand Lochmitte zur Kante $x = 0$ beträgt $8{,}0\text{ mm}$. Gefordert bei $d = 6\text{ mm}$ sind jedoch $1{,}5 \times 6 = 9{,}0\text{ mm}$!
   - **Lösung:** Entweder Laschenlänge auf 42 mm verlängern (Bohrung bei $x = 9$) oder bei fixer Länge 40 mm die Bohrung auf $x = 9$ rücken (Mittenabstand 22 mm).
2. **Kompakte Modellierung der Lasche:**
   ```json
   [
     {"command": "parameters.add", "params": {"name": "L", "expression": "42 mm"}},
     {"command": "parameters.add", "params": {"name": "W", "expression": "20 mm"}},
     {"command": "parameters.add", "params": {"name": "T", "expression": "5 mm"}},
     {"command": "solid.box", "params": {"length": "L", "width": "W", "height": "T", "corner": [0, 0, 0], "name": "Basis"}},
     {"command": "solid.cylinder", "params": {"diameter": 6, "height": "T + 2 mm", "base": [9, 10, -1], "operation": "cut", "name": "Bohrung1"}},
     {"command": "solid.cylinder", "params": {"diameter": 6, "height": "T + 2 mm", "base": [33, 10, -1], "operation": "cut", "name": "Bohrung2"}}
   ]
   ```
3. **Baugruppe & Gelenke (`add_joint`):**
   - Teile separat speichern (`save_document`).
   - Baugruppe anlegen (`new_assembly`), Teile mit `insert_part` referenzieren.
   - Gelenke immer über `add_joint` von Mechvane anlegen (merkt sich Flächennamen für spätere Konsistenzprüfung).
   - Nach Bauteiländerungen `update_links(assembly, repair=True)` aufrufen.
