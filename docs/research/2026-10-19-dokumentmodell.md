# Dokumentmodell nach Inventor auf SolidCraft

Stand 2026-10-19 (Nacht), SolidCraft v0.16.2 (Versuche) und `main` (Code).
Schritt „Datenmodell genauer prüfen“ aus `docs/uebergabe.md`, Grundlage für
[ADR 0001](../adr/0001-grundlage-solidcraft.md). Versuchsskripte in
[`2026-10-dokumentmodell/`](2026-10-dokumentmodell/).

Anforderungen des Nutzers (ROADMAP-Grundsatz 5): Feature-Baum wie Inventor,
**auch im Datenmodell**; Skizzen gehören ihrem Feature; eigener Verlauf mit
Bauteilende je Bauteil; Abhängigkeiten an den Bauteilen; **Bauteile und
Baugruppen als getrennte Dateien**.

## Kurzfassung

- **Eine Bauteildatei = ein SolidCraft-Design ohne Komponenten.** Dann hat
  jedes Bauteil von selbst seinen eigenen Verlauf und sein eigenes
  Bauteilende (`Document.features` und `marker` gelten dann nur für dieses
  Teil). Dafür muss am Format nichts geändert werden.
- **Skizzenbesitz geht ohne Formatänderung**, als feste Regel in den
  inventa-Befehlen: Eine Skizze mit genau einem Verbraucher steht im Verlauf
  direkt vor ihm. Damit ist „Skizze unter dem Feature“ eine exakte
  Darstellung des gespeicherten Zustands, nicht nur Optik. Versuch:
  Verschieben einer Skizze direkt vor ihr Feature geht
  (`timeline.reorder`).
- **Eine Baugruppendatei = ein SolidCraft-Design mit verknüpften Komponenten**
  („Insert Design“, `component.insert_design`/`update_links`/`relink`) und
  Gelenken. Abhängigkeiten nach Inventor-Art (parallel, senkrecht, Winkel,
  Punkt auf Ebene, …) kommen auf `main` gerade als „Relations“ dazu.
- **Die Hauptlücke:** Über eine Verknüpfung gehen die Flächennamen verloren.
  Ändert sich die Bauteildatei so, dass eine gleich große Bohrung hinzukommt,
  **springt ein Gelenk still auf die falsche Bohrung** (keine Warnung, kein
  Fehler). Im selben Design bleibt es dank Lineage-Namen richtig. Das muss vor
  allem anderen behoben werden, am besten upstream.
- Bearbeiten an Ort und Stelle (Bauteil aus der Baugruppe heraus öffnen,
  ändern, zurück) gibt es nicht. Das ist UI und Arbeitsablauf, kein
  Kernproblem.

## Wie SolidCraft das Dokument hält (Code)

| Baustein | Stelle | Bedeutung für inventa |
|---|---|---|
| `Document.features: Vec<Feature>`, `marker: Option<usize>` | `crates/doc/src/document.rs` | Ein linearer Verlauf mit einem Marker je Datei. Bei einer Datei je Bauteil genau das Inventor-Bauteil |
| `Feature.component` | ebd. | Komponenten teilen sich einen Verlauf (Fusion-Stil). In einer Bauteildatei ohne Komponenten bedeutungslos |
| `FeatureKind::Sketch` als eigener Eintrag, `Extrude { sketch: SketchId }` | ebd. | Verbrauch ist eine Referenz. Besitz lässt sich daraus ableiten |
| `assembly.joints`, Gelenk mit `a`/`b` (Occurrence + Ursprung) | `crates/doc/src/joints.rs` | Zuordnung zu den Bauteilen ist gespeichert, Anzeige unter den Bauteilen ist reine UI |
| Relations (`parallel`, `perpendicular`, `angle`, `point_on_plane`, `point_on_line`, `line_on_plane`) | `joints_relations.rs`, Format „pending“ | Entspricht Inventor-Abhängigkeiten (Passend, Bündig, Winkel). Noch nicht im Release |
| `DesignLink { path, feature }`, Import-Feature mit STEP-Text | `document.rs`, `engine/src/cmd/component_link.rs` | Getrennte Dateien gibt es schon, aber als Körper-Kopie: B-Rep ohne die Namen aus der Bauteildatei |
| Flächennamen aus der Entstehung (Lineage), sonst aus Geometrie „unverified“ | `crates/doc/src/naming.rs` | Importierte Körper werden geometrisch benannt, daher die Lücke unten |

Größe und Tempo (`main`, 2026-10-19): `ui-egui` ~101 000 Zeilen, `engine`
~94 000, `doc` ~46 000 (nur Dateien direkt in `src/`). In 30 Tagen 1 660
Commits, davon 673 an `ui-egui`, 697 an `engine`, 375 an `doc`. Ein Fork, der
diese Crates ändert, müsste täglich Dutzende Commits nachziehen.

## Versuche

Alle mit `solidcraft-cli` v0.16.2, Skripte im Ordner `2026-10-dokumentmodell/`.

### 1. Gelenk auf verknüpftem Bauteil nach Änderung der Bauteildatei

Platte 60 × 40 × 5 mit Bohrung Ø 6 bei x = `hx` als eigene Datei
(`part_a.json`, `hx` = 10). Baugruppe (`asm.json`): Platte per
`component.insert_design` verknüpft und festgelegt, ein Stift als eigene
Komponente, starres Gelenk vom Stift auf die Bohrungskante. Danach wird die
Bauteildatei geändert und `component.update_links` ausgeführt (`upd.json`).

| Änderung der Bauteildatei | Gelenk danach | richtig? |
|---|---|---|
| `part_b`: Bohrung nach x = 20 verschoben | x = 20 | ja |
| `part_c`: neue gleich große Bohrung bei x = −10, im Verlauf **vor** der alten, alte bei x = 20 | x = **−10** | **nein, still falsch** |
| `part_d`: alte Bohrung nach x = 5, neue bei x = 15 | x = 15 | **nein** (zur neuen Bohrung) |

`update_links` meldet keine Warnung, `joint.list` keine Fehler.

### 2. Derselbe Fall in einem einzigen Design

`ein-design.json`: Platte, Bohrung, Stift und Gelenk in einer Datei. Dann
Marker vor die Bohrung, neue Bohrung bei x = −10 einfügen, Marker ans Ende,
alte Bohrung per `timeline.redefine` nach x = 20. Ergebnis: Gelenk bei
**x = 20**, richtig. Die Lineage-Namen (`F3:side…`) tragen die Referenz.

Folgerung: Der Unterschied liegt allein in der Verknüpfung. Das Import-Feature
speichert die Körper als STEP-Text, dabei gehen die Namen aus der
Bauteildatei verloren, und die Referenzen werden über Geometrie neu
zugeordnet. Das verletzt Grundsatz 2 (bricht eine Referenz, gibt es eine
klare Meldung statt stillem Raten).

### 3. Skizze direkt vor ihr Feature verschieben

`S1` (Rechteck), `S2` (Kreis), `E1` = Extrusion von `S1`. Dann
`timeline.reorder S1 → Position 1`. Ergebnis: Reihenfolge `S2, S1, E1`, ohne
Fehler. `timeline.dependents S1` meldet `deleted_with_it: [E1]`.

Folgerung: Die Regel „verbrauchte Skizze steht direkt vor ihrem Verbraucher“
lässt sich mit vorhandenen Befehlen herstellen und halten. Eine Skizze mit
mehreren Verbrauchern (geteilte Skizze) bleibt eine eigene Zeile, wie in
Inventor. Später zu einer Skizze zu verschieben ist immer erlaubt, weil
Referenzen nur rückwärts zeigen. Ausnahme: Ein Feature dazwischen benutzt die
Skizze, dann ist sie geteilt.

## Abbildung Inventor → SolidCraft

| Inventor | Umsetzung | Aufwand (grob) |
|---|---|---|
| Bauteildatei mit eigenem Verlauf und Bauteilende | `.solidcraft`-Design ohne Komponenten | keiner |
| Skizze unter ihrem Feature, wandert mit, wird mit gelöscht | Regel in inventa-Befehlen (Reorder beim Erzeugen, Löschen des Features fragt nach der Skizze), Anzeige im Baum | klein bis mittel |
| Baugruppendatei verweist auf Bauteile | Design mit verknüpften Komponenten | vorhanden |
| **Referenzen über Dateigrenzen bleiben stabil** | Verknüpfung muss die Flächennamen der Bauteildatei mitnehmen (Import aus dem Design statt aus STEP, oder Namen neben dem STEP speichern) | **mittel bis groß, Kern (`doc`/`engine`)** |
| Abhängigkeiten unter den Bauteilen | Anzeige aus `a`/`b` | klein (UI) |
| Abhängigkeiten nach Inventor-Art | Relations auf `main` | vorhanden, sobald im Release |
| Bauteil an Ort und Stelle bearbeiten | Bauteildatei in zweiter Sitzung öffnen, speichern, `update_links` | mittel (UI und Ablauf) |
| Mehrfach verbaute Teile | Occurrences derselben Komponente | vorhanden |

Aufwand heißt hier: klein = Tage, mittel = 1–3 Wochen, groß = Monate,
jeweils mit Agentenhilfe und grob geschätzt.

## Offene Punkte

- Ob upstream die Namen über Verknüpfungen annimmt und wie: gemeldet als
  [#3330](https://github.com/tangency-labs/solidcraft/issues/3330)
  (2026-10-20) mit Vorschlag zur Umsetzung.
- Ob die Relations im nächsten Release landen und wie sie sich mit Gelenken
  mischen.
- Leistung bei Baugruppen mit vielen verknüpften Teilen (jede Verknüpfung
  wertet das Bauteil-Design beim Einfügen aus und speichert eine STEP-Kopie).
- Dateiendungen: `.solidcraft` für beides, oder eigene Endungen für Bauteil
  und Baugruppe. Erst entscheiden, wenn die Hülle steht.
