# Was Nutzer an Fusion besser finden als an Inventor (Entscheidungsliste)

Stand 2026-10-26. Grundlage: Recherche von Gemini 3.8 Flash
([Rohfassung mit Quellen](2026-10-26-fusion-vs-inventor-gemini.md)), von mir gesichtet. Zweck: später
je Punkt entscheiden, ob Mechvane näher an Fusion oder an Inventor bleibt (ROADMAP, Grundsatz 10:
Bedienung nah an Inventor, Optik dunkler und schicker).

**Belegstand:** Die Zitate sind größtenteils nicht geprüft. `check_sources.py` fand sie nur bei
makerforce.io und cadspec, Reddit liefert die Kommentare nicht im HTML, Autodesk-Seiten antworten mit
403. Die Spalte „Prüfnotiz“ nennt Punkte, bei denen Inventor die Funktion nach meinem Wissen
inzwischen auch hat. Diese Punkte vor einer Entscheidung in einer aktuellen Inventor-Version nachsehen.

Häufigkeit laut Gemini: oft / gelegentlich. Entscheidung: **F** = wie Fusion, **I** = wie Inventor,
**B** = beides (z. B. umschaltbar), offen = noch nicht entschieden.

## Fusion besser

| # | Punkt | Häufigkeit | Prüfnotiz | Entscheidung |
|---|---|---|---|---|
| 1 | Taste **S**: Befehlssuche und Favoriten am Mauszeiger | oft | SolidCraft hat „Search commands“ (S) schon | offen |
| 2 | Aufgeräumte, einheitliche Oberfläche statt alter Dialogfenster | oft | umstritten, deckt sich mit „dunkler und schicker“ | offen |
| 3 | Arbeitsbereiche (Konstruktion, Render, Simulation, CAM, Zeichnung) in einem Fenster | oft | Inventor hat Umgebungen (Studio, Belastungsanalyse) im selben Dokument, Zeichnungen sind eigene Dateien | offen |
| 4 | Trackpad- und Gestensteuerung auf Laptops | gelegentlich | nicht geprüft | offen |
| 5 | Leiste unten für Darstellungsstil, Perspektive, Umgebung | gelegentlich | SolidCraft hat eine ähnliche Leiste | offen |
| 6 | Bild einfügen und mit zwei Punkten auf Maß kalibrieren | oft | nicht geprüft | offen |
| 7 | Sich überschneidende Skizzenlinien ergeben einzeln wählbare Profile | oft | Inventor kann Teilprofile auch wählen, vermutlich überholt | offen |
| 8 | Maße beim Zeichnen eintippen, Tab zum nächsten Wert | oft | Inventor hat die Direkteingabe (Heads-Up Display), vermutlich überholt | offen |
| 9 | Kanten der Fläche beim Skizzieren automatisch fangbar | gelegentlich | Inventor projiziert Kanten automatisch (Option), vermutlich überholt | offen |
| 10 | Ein Werkzeug „Drücken/Ziehen“ (Q) für Extrusion, Versatz und Rundung je nach Auswahl | oft | umstritten (unsaubere Historie) | offen |
| 11 | Freiformflächen (T-Splines, Form-Arbeitsbereich) | oft | Nische für Maschinenbau | offen |
| 12 | Echtes 3D-Gewinde per Häkchen „Modelliert“ (3D-Druck) | oft | Inventor hat modellierte Gewinde seit ca. 2022, vermutlich überholt | offen |
| 13 | Direktes Bearbeiten importierter STEP-Flächen | gelegentlich | Inventor hat „Direkt bearbeiten“, Vergleich offen | offen |
| 14 | Mehrere Körper in einem Teil, per Rechtsklick zu Komponenten machen | oft | widerspricht teilweise Grundsatz 5 (getrennte Dateien) | offen |
| 15 | Gelenk statt drei Abhängigkeiten (Lage und Freiheitsgrad in einem Schritt) | oft | Inventor hat „Verbindung“ (Joint) zusätzlich zu Abhängigkeiten; Mechvane nutzt schon Gelenke | offen |
| 16 | „As-Built Joint“: Gelenk an Ort und Stelle, ohne Verschieben | oft | nicht geprüft | offen |
| 17 | Ganze Mechanismen in einer Datei, keine gebrochenen Verknüpfungen | oft | stark umstritten; Mechvane hat sich für getrennte Dateien entschieden (Grundsatz 5) | I (Grundsatz 5) |
| 18 | Zeitleiste unten zum Zurückspulen | oft | umstritten; Grundsatz 5 sagt: keine Fusion-Zeitleiste | I (Grundsatz 5) |
| 19 | Komponentenfarben in Zeitleiste und Baum (Shift+N) | oft | nicht geprüft | offen |
| 20 | Schritte im Verlauf zu Gruppen zusammenfassen | gelegentlich | Mechvane hat Ordner im Browser | offen |
| 21 | CAM fest eingebaut | oft | außerhalb des Plans (Phase 2 und später) | offen |
| 22 | Raytracing direkt im Ansichtsfenster | oft | Grundsatz 8 (Blender) | offen |
| 23 | Ein Klick an den Slicer (Bambu, Prusa, Orca, Cura) | oft | Inventor hat eine 3D-Druck-Umgebung; passt zum Skill `3d-druck` (CuraEngine) | offen |
| 24 | McMaster-Carr-Katalog im Ansichtsfenster | oft | Mechvane hat Normteile (`standard_part`) | offen |
| 25 | Läuft auf macOS und Windows | oft | Mechvane: Browser plus SolidCraft, plattformunabhängig | F (gegeben) |

## Inventor besser (Gegenprobe)

| # | Punkt | Häufigkeit | Bezug zu Mechvane |
|---|---|---|---|
| 1 | Große Baugruppen laufen schneller | oft | Grenze von SolidCraft, später messen |
| 2 | Reifere 2D-Fertigungszeichnungen | oft | Phase 3 (CADCraft) |
| 3 | Tiefere Blechfunktionen | oft | SolidCraft hat ein Register Sheet Metal |
| 4 | Normteilbibliothek (Content Center, DIN/ISO) | oft | `standard_part`, `bolted_connection` |
| 5 | Konstruktionsassistenten (Design Accelerator) | oft | Fachmodule Phase 2 |
| 6 | Gestellgenerator für Rahmen und Schweißkonstruktionen | oft | Fachmodul-Kandidat |
| 7 | Lokale Daten, Vault, offline | oft | Mechvane: lokale Dateien, git |
| 8 | Regelbasierte Automatisierung (iLogic) | oft | Agent und MCP übernehmen diese Rolle |

## Erste Einordnung (Vorschlag, nicht entschieden)

- Zu übernehmen lohnt sich wohl: S-Suche (1), Gelenke wie heute (15) plus As-Built (16),
  Komponentenfarben (19), modellierte Gewinde als Option (12), Slicer-Übergabe (23), Kalibrieren von
  Bildern (6).
- Bleiben wie Inventor, schon entschieden: getrennte Dateien (17) und vertikaler Browser statt
  Zeitleiste (18).
- Zuerst prüfen, ob Inventor das schon kann: 7, 8, 9, 12, 13.
