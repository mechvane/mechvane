# Konstrukteurs-Agent und Regelprüfung (Phase 1)

**Datum:** 2026-10-20  
**Autor:** Antigravity / Gemini 3.8 Flash  
**Status:** Umgesetzt (Branch `gemini/konstrukteur`)

---

## 1. Übersicht

Im Rahmen von ROADMAP Phase 1 wurde der Konstrukteurs-Workflow für inventa realisiert:
1. **Regelprüfung als Code (`inventa/design_rules.py`):** Modul zur automatisierten Prüfung von Bauteilen gegen Fertigungsregeln über die laufende SolidCraft-Sitzung.
2. **MCP-Werkzeug (`check_design` in `inventa/server.py`):** Liefert einen strukturierten Prüfbericht mit Gesamt-Urteil (`ok`, `warn`, `fail`), Regelergebnissen und genauer Verortung (Punkt, Fläche).
3. **Agent-Vorlage (`.claude/skills/konstrukteur/SKILL.md`):** Projekt-Skill, der den iterativen Konstruktionsablauf anleitet (Anforderungen klären → Skizze/Feature → messen → Snapshot prüfen → korrigieren) mit klaren Abbruchkriterien und Kostenbewusstsein.
4. **Testabdeckung (`tests/inventa/check.py`):** 4 neue Tests für Randabstands-Fehler (`fail`), regelkonformes Bauteil (`ok`), ungestützten Überhang (`fail`) und Aufruf über den MCP-Server (`ok`).

---

## 2. Was geprüft wird

Die Prüfung unterscheidet konfigurierbare Profile (Standard: `fdm_0.4` für FDM 3D-Druck mit 0,4-mm-Düse; dazu `cnc_alu` für CNC-Fräsen in Aluminium):

| Regel | Kriterium (`fdm_0.4`) | Kriterium (`cnc_alu`) | Details & Begründung |
|---|---|---|---|
| **Randabstand von Bohrungen** (`hole_edge_distance`) | $\ge 1{,}5 \times d$ | $\ge 1{,}5 \times d$ | Abstand Lochachse zu allen parallelen Außenkanten/Begrenzungen. Verhindert Ausbrechen unter Last. |
| **Mindestwandstärke** (`min_wall_thickness`) | $\ge 1{,}2\text{ mm}$ (3 Perimeter) | $\ge 1{,}0\text{ mm}$ | Geprüft wird: Wandung Bohrung zu Außenkante ($e - r$), Wandung zwischen benachbarten Bohrungen ($D - (r_1 + r_2)$) sowie Bauteil-Minimalmaße. |
| **Einschraubtiefe** (`thread_depth`) | $\ge 1{,}5 \times d_{\text{nom}}$ | $\ge 1{,}5 \times d_{\text{nom}}$ | Tragende Gewindetiefe in Sacklöchern/Gewindebohrungen. Erkennt `model.threads`, `HoleFeature` (`thread`) und gleicht Bohrungsdurchmesser mit ISO-Metrisch-Kernlöchern ab (M2–M20). |
| **Druckbarkeit (Überhänge)** (`printability`) | Max. $45^\circ$ von Vertikalen | Keine Grenze | Nach unten gerichtete Flächen ($N_z < -0{,}707$) oberhalb des Druckbetts ($z > z_{\min} + 0{,}05$) werden als stützbedürftig beanstandet. |
| **Druckbarkeit (Kleinste Bohrung)** (`printability`) | $\ge 2{,}0\text{ mm}$ | $\ge 1{,}0\text{ mm}$ | Kleinere Bohrungen neigen im FDM-Druck zum Zuwachsen durch Filament-Squish. |

### Sparsamer Ressourcenverbrauch
Die Prüfung verzichtet bewusst auf Aufrufe des teuren `body_topology`-Werkzeugs (25–45 KB JSON-Payload). Stattdessen werden leichtgewichtige, semantische Abfragen kombiniert:
- `document.inspect` für Bounding Box, Volumen und Feature-Historie,
- `model.faces` für Flächennormalen, Zylinderachsen und Schwerpunkte,
- `model.threads` für explizite Gewindedaten,
- `timeline.inspect` nur gezielt für gefundene Bohrungsfeatures.

---

## 3. Vereinfachungen

Folgende ingenieurmäßige Vereinfachungen wurden getroffen und sind im Code dokumentiert:

1. **Druckorientierung:** Es wird standardmäßig von einer Baurichtung entlang $+Z$ ausgegangen (SolidCraft-Konvention: Z oben). Ein automatisches Drehen zur Ermittlung einer optimalen Drucklage ist vorerst nicht implementiert.
2. **Stützstrukturen:** Es erfolgt keine Slicer-Simulation; jede nach unten gerichtete Fläche ($N_z < -0{,}707$), die nicht direkt auf dem Druckbett ($z \approx z_{\min}$) liegt, gilt als ungestützt.
3. **Brücken (Bridging):** Vollkommen horizontale Deckenflächen ($N = [0, 0, -1]$) im freien Raum werden als Überhang beanstandet. Eine Erkennung, ob es sich um eine kurze Brücke zwischen zwei Stützwänden handelt (die ein FDM-Drucker bis ca. 10–20 mm überbrücken könnte), findet noch nicht statt.
4. **Horizontale Bohrungen:** Zylindrische Bohrungen mit horizontaler Achse besitzen im Scheitelpunkt theoretisch eine $90^\circ$-Decke. Diese werden von der Überhang-Prüfung ausgenommen, da der stetige Bogen im Schichtaufbau bis ca. 10 mm Durchmesser ohne Stützmaterial druckbar ist.
5. **Gewinde vs. Passbohrung:** Bohrungen ohne explizite Gewindemarkierung, deren Durchmesser aber innerhalb von $\pm 0{,}15\text{ mm}$ auf ein ISO-Kernloch passt (z. B. 4,2 mm für M5 oder 5,0 mm für M6), werden als Gewindebohrung eingestuft und auf $1{,}5 \times d_{\text{nom}}$ Tiefe geprüft.

---

## 4. Offene Punkte

- **Bridging-Erkennung:** Automatische Unterscheidung zwischen frei schwebenden Inseln/Vorkragungen und echten Brücken mit beidseitigen Pfeilern.
- **Drucklagen-Optimierer:** Analysieren mehrerer Orientierungen (z. B. 6 Hauptansichten) und Empfehlung der Orientierung mit minimalem Überhangvolumen.
- **Passungsauslegung:** Prüfregeln für Passungen (H7/h6, Spiel- und Presssitze für Kugellager und Passstifte) in Verbindung mit dem Normteile-Generator.
- **CAD-Zeichnungsanmerkungen:** Ausgabe der Regelprüfungsergebnisse als maßstäbliche Bemaßungshinweise in den Ansichten (Phase 3).
