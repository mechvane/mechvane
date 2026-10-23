# ADR 0001: SolidCraft als Kern, Mechvane als eigene Schicht darüber

- Status: **angenommen** (vorgeschlagen 2026-10-19, vom Nutzer angenommen 2026-10-20)
- Entscheidet: Worauf Mechvane aufbaut (ROADMAP Phase 0, Optionen A/B/C)

## Kontext

Mechvane soll „Autodesk Inventor neu gedacht“ werden: parametrisches CAD mit
tief integrierten Agenten. Phase 0 hat SolidCraft (Rust, MIT/Apache-2.0,
eigener Kernel auf truck-Basis, MCP-Server) geprüft:

- **Trägt:** Kernel, Skizzenlöser, Parameter, Blech, Gelenke mit Grenzen und
  Kontakt, Agenten-Schnittstelle (MCP mit Batch, Rollback, Messwerten,
  Screenshots). Vier Referenzteile sind auf 10⁻⁵ maßhaltig
  ([Phase-0-Bericht](../research/2026-10-phase0-solidcraft.md)).
- **Fehlt:** Zeichnungen (zurückgestellt), Plugin-System (nur Entwurf, keine
  eigene Plugin-UI), Feature-Baum nach Inventor
  ([Bericht](../research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md)).
- **Projekt:** sehr aktiv (1 660 Commits in 30 Tagen), Beiträge werden im
  Median nach 7 h gemergt, aber strenge Regeln: kein GPL/LGPL/AGPL-Code, auch
  nicht lesen, keine Automatisierung kommerzieller CAD-Programme für
  Referenzen.

Vorgaben des Nutzers (ROADMAP-Grundsatz 5): Feature-Baum wie Inventor **im
Datenmodell, nicht nur optisch**; Skizzen gehören ihrem Feature; eigener
Verlauf mit Bauteilende je Bauteil; Abhängigkeiten an den Bauteilen;
**Bauteile und Baugruppen als getrennte Dateien**; grafischer Slicer als
Arbeitsbereich im selben Fenster.

Die Prüfung des Dokumentmodells
([Bericht](../research/2026-10-19-dokumentmodell.md)) zeigt: Eine
SolidCraft-Datei je Bauteil liefert den Verlauf je Bauteil von selbst.
Skizzenbesitz lässt sich als Regel in den Befehlen halten. Baugruppen gibt es
als Design mit verknüpften Komponenten. **Die Hauptlücke:** Über eine
Verknüpfung gehen die Flächennamen verloren, und ein Gelenk kann nach einer
Bauteiländerung still auf die falsche Fläche springen.

## Optionen

| | Beschreibung | Für | Gegen |
|---|---|---|---|
| **A** Erweiterung | Mechvane nur als Plugins und Beiträge zu SolidCraft | kein Wartungsaufwand, alles upstream | Plugin-System gibt es nicht, und es erlaubt keine eigene UI. Inventor-Baum und getrennte Dateien hängen ganz am Willen von upstream |
| **B** Fork | SolidCraft forken und `doc`/`ui-egui` umbauen | volle Freiheit | 1 660 Commits in 30 Tagen nicht nachziehbar. Der Fork verliert schnell den Anschluss an Kernel-Fixes |
| **C** Eigener Kern | Rust mit OCCT hinter einem Trait | unabhängig | widerspricht Grundsatz 1, Aufwand ein Vielfaches, OCCT ist LGPL (Konflikt mit Beiträgen zu SolidCraft) |
| FreeCAD-Unterbau | aus der Gemini-Gegenprobe | Zeichnungen fertig | anderer Stack (C++/Python/Qt), LGPL, verträgt sich nicht mit SolidCraft-Beiträgen |
| **A+** Kern + eigene Schicht | SolidCraft-Kern unverändert als Abhängigkeit, Mechvane bringt Dateimodell, Befehlsregeln, Baum und Arbeitsbereiche selbst mit, Kernlücken werden upstream behoben | Kern bleibt aktuell, Inventor-Modell ohne Formatänderung, Rückfall auf kleine Patches möglich | eigene UI-Arbeit, abhängig von wenigen Upstream-Beiträgen |

## Entscheidung

**Option A+.** Im Einzelnen:

1. **Kern unverändert.** `kernel`, `sketch`, `doc`, `engine`, `io` kommen von
   SolidCraft, auf einen Release oder Commit gepinnt. Kein Fork dieser
   Crates. Kernlücken gehen als Issue oder PR upstream, unter deren Regeln.
2. **Dateimodell nach Inventor:**
   - Bauteil = SolidCraft-Design ohne Komponenten, mit eigenem Verlauf und
     eigenem Bauteilende.
   - Baugruppe = SolidCraft-Design mit verknüpften Komponenten
     (`component.insert_design`) plus Gelenken und Relations.
   - Eigene Dateiendungen erst, wenn die Hülle steht.
3. **Skizzenbesitz als Befehlsregel:** Eine verbrauchte Skizze steht direkt
   vor ihrem einzigen Verbraucher. Wird ein Feature verschoben oder gelöscht,
   geht die Skizze mit bzw. wird nachgefragt. Eine geteilte Skizze bleibt eine
   eigene Zeile.
4. **Agenten zuerst (Grundsatz 3):** Die Mechvane-Schicht entsteht zuerst als
   eigener MCP-Server vor `solidcraft-cli mcp`. Er öffnet und speichert
   Bauteile und Baugruppen, aktualisiert Verknüpfungen, hält die
   Skizzenregel und bietet semantische Abfragen. Prototyp in Python (schnell,
   passt zu `tests/reference/check.py`). Rust, sobald die Schnittstelle
   steht.
5. **Oberfläche danach.** Der Inventor-Baum (Bauteile mit Abhängigkeiten
   darunter, Skizzen unter Features, Bauteilende) und der Slicer-Arbeitsbereich
   kommen zuerst als Vorschlag upstream (#1221 ist gefragt). Falls abgelehnt:
   kleine, abgegrenzte Patches auf `ui-egui` (eigenes Modul plus wenige
   Einhängepunkte), regelmäßig neu aufgesetzt. Kein Fork der ganzen UI.
6. **Slicer:** CuraEngine als eigener Prozess (AGPL bleibt draußen), erst über
   die Befehlszeile, dann als Daemon über Arcus
   ([Recherche](../research/2026-10-19-slicer-engines-gemini.md)).

### Upstream-Beiträge in dieser Reihenfolge

1. **Flächennamen über Verknüpfungen** (Blocker für getrennte Dateien):
   Fehlerfall aus Versuch 1 im Dokumentmodell-Bericht melden, Vorschlag dazu:
   das Import-Feature übernimmt die Lineage-Namen aus dem verknüpften Design.
   Gemeldet als [#3330](https://github.com/tangency-labs/solidcraft/issues/3330)
   (2026-10-20).
2. Bearbeiten an Ort und Stelle für verknüpfte Komponenten.
3. Browser-Optionen: Gelenke unter den beteiligten Occurrences, Skizzen unter
   ihrem Feature.
4. Plugin-Panels, Viewport-Overlays, eigener Arbeitsbereich (#1221, gefragt).
5. Kollisions-Bug #3323 (gemeldet).

## Folgen

- Phase 1 beginnt mit dem Mechvane-MCP-Server (Dateimodell, Skizzenregel) und
  dem Upstream-Beitrag zu Flächennamen. Die Referenzteile bekommen eine
  Baugruppe aus zwei Dateien als neuen Testfall (Versuch 1 als Regressionstest:
  muss nach dem Fix auf der richtigen Bohrung bleiben oder eine Meldung geben).
- Solange die Namen über Verknüpfungen nicht halten, prüft der
  Mechvane-Server nach jedem `update_links` die Gelenk-Frames gegen ihren
  vorherigen Stand. Springt eines, warnt er laut.
- Zeichnungen (Phase 3) bleiben die größte Eigenleistung. Mitarbeit an
  SolidCraft #860 ist der Weg, bei dem sie upstream landen.
- Für Beiträge zu SolidCraft gilt: keinen GPL-Code lesen, keine Fusion-Werte
  als Referenz. Fusion-Vergleiche nur für Mechvane-eigene Tests.
- **Prüfpunkt:** Lehnt upstream die Namen über Verknüpfungen ab oder bleibt
  das sechs Wochen liegen, wird neu entschieden. Dann bleibt entweder ein
  eigener Patch auf `doc`/`engine` (Teil-Fork) oder ein eigenes Baugruppenformat
  in Mechvane, das Bauteile selbst auswertet und die Namen behält.
