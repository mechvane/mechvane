# Abgleich Soll-Abläufe ↔ Mechvane-Oberfläche (2026-11-07)

Grundlage: die drei Gemini-Recherchen vom 2026-11-07 (#55 Skizze/Ansicht/Auswahl, #56 Feature-Dialoge,
#57 Browser/Rückgängig/Parameter), Quellen mit `check_sources.py` belegt. Abgeglichen mit dem Stand von
`mechvane/ui/static/*.js` und `mechvane/tree.py` (main, 2026-11-07). Einordnung: **v0.1** = klein und von
Inventor-Nutzern sofort vermisst; **später** = Overhaul oder eigener größerer Schritt nach v0.1.

## Schon vorhanden

| Soll (Quelle) | Stand Mechvane |
| :--- | :--- |
| Ansicht dreht sich senkrecht zur Skizze, Rückkehr nach Fertig (#55-1) | `sketcher.js` speichert und stellt die Ansicht wieder her |
| `S` startet eine Skizze, `F6` Home-Ansicht (#55-2, #55-4) | `app.js` Tastenkürzel |
| Freiheitsgrade in der Statusleiste und als Farbe, Konflikte rot (#55-5) | Skizzierer (d), 2026-11-06 |
| Ein einziges Profil vorgewählt (#55-8) | Extrusion seit 2026-11-06 |
| `Name = Ausdruck` direkt im Maß (#57-5) | Bemaßen (b), 2026-11-06 |
| Verbrauchte Skizzen unter dem Feature (#57-1) | `tree.py` (`children`) |
| Unterdrückte und zurückgerollte Features abgeblendet (#57-9) | `tree-suppressed` in `app.js` |
| Doppelklick bearbeitet Skizze bzw. Feature (#57-8) | Baum und Ansicht |
| Bohrung auf Fläche ohne Skizze, Abstand zu Kanten (#56-3) | Bohrungsdialog, #43 |

## Lücken

| # | Lücke (Quelle) | Einordnung | Begründung |
| :--- | :--- | :--- | :--- |
| 1 | Umbenennen im Baum (`F2`, Kontextmenü) (#57-7) | **v0.1** | Klein, wird sofort vermisst; SolidCraft `timeline.rename` vorhanden |
| 2 | Sichtbarkeit von Skizzen und Körpern umschalten (Auge, `V`) (#57-7) | **v0.1** | Bisher nur Ursprung-Ordner mit Auge |
| 3 | Löschen eines Features fragt, ob die verbrauchte Skizze bleibt (#57-4) | **v0.1** | Verhindert Verlust bemaßter Skizzen; Verhalten heute prüfen |
| 4 | Skizze auf Fläche projiziert die Flächenkanten automatisch (#55-3) | **v0.1** | Ohne das kein Fangen an Körperkanten; Projizieren (P) ist schon da |
| 5 | Fensterauswahl im Skizzierer, links→rechts umschließend, rechts→links kreuzend (#55-6) | **v0.1** | SolidCraft `BoxSel` (`selection.rs`) als Vorlage |
| 6 | Vorab-Hervorhebung Baum ↔ Ansicht (#57-6) | **v0.1** | Steht schon als „Hervorhebung von Flächen“ im Plan |
| 7 | Drehung: Profil per Klick in der Ansicht (#55, Abschnitt 4) | **v0.1** | Steht schon in der ROADMAP („Drehung noch mit Auswahlliste“) |
| 8 | Kürzel `R` Drehung (außerhalb der Skizze) (#56-7) | **v0.1** | Eine Zeile in `app.js`; im Skizzierer bleibt `R` das Rechteck |
| 9 | ViewCube mit Klickflächen und Ecken (#55-4) | später | Overhaul; Home und Standardansichten gibt es schon |
| 10 | Bauteilende-Marker im Baum ziehen, `Esc` bricht ab (#57-2, #57-3) | später | Zurückrollen geht über `part_end`; Ziehen im Baum ist Overhaul |
| 11 | Getriebenes Maß statt Fehler bei Überbestimmung (#55-10) | später | SolidCraft-Unterstützung erst klären |
| 12 | Einheitenprüfung im Formelfeld, rot vor dem Schließen (#57-10) | später | |
| 13 | Breadcrumb aus dem Feature-Dialog in die Skizze und zurück (#56-1) | später | |
| 14 | Maßeingabe und Ziehpfeile am Modell (HUD) (#56-2) | später | Overhaul |
| 15 | Rundung: Filter Kante/Kontur/Feature/alle Kanten (#56-4) | später | |
| 16 | Eckenausführung, partielle Fase (#56-5, #56-6) | später | |
| 17 | Muster in Umgrenzung, Berechnung „Anpassen“ (#56-8, #56-10) | später | Kein SolidCraft-Gegenstück |
| 18 | Spiegeln mit „Original entfernen“ (#56-9) | später | |
| 19 | „Andere auswählen“ für verdeckte Geometrie (#55-9) | später | |
| 20 | Skizze mehrfach verwenden (Share Sketch) (#55-7) | später | |
| 21 | Ordner im Baum (#57, Abschnitt 2.8) | später | Steht schon als „Ordner-Dialog“ unter „Nicht heute“ |

Nicht bestätigt und deshalb nicht übernommen: „`solid.revolve` hat in SolidCraft kein Standard-Kürzel“
(Prüfnotiz in den Recherchen). Für Mechvane spielt es keine Rolle, Lücke 8 gilt unabhängig davon.
