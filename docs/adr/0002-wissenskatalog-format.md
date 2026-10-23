# ADR 0002: Format und Struktur des Wissenskatalogs für Konstruktionswissen

- Status: **angenommen** (2026-10-23, Nutzer; vorgeschlagen 2026-10-21)
- Entscheidet: Datenformat, Ablagestruktur und Abfragemechanismus des Wissenskatalogs (Plan [2026-10-20-wissenskatalog-plan.md](../research/2026-10-20-wissenskatalog-plan.md), Probelauf [2026-10-21-graphify-katalog-probelauf-flash.md](../research/2026-10-21-graphify-katalog-probelauf-flash.md))

## Kontext

Die Agenten in Mechvane benötigen für automatisierte Modellierungsassistenten (z. B. Bohrungs- und Schraubenassistent) und Prüfwerkzeuge (`check_design`) schnellen Zugriff auf praktisches Konstruktionswissen. Dieses Wissen umfasst nicht nur standardisierte Normmaße, sondern empirische Fertigungs- und Montagegrenzen (z. B. Einschraubtiefen in Leichtmetallen, Innenradien beim CNC-Fräsen, Mindestwandstärken, Toleranzen, Klebespalte).

Die Evaluation des Wissensgraphen-Probelaufs mit graphify ([Bericht](../research/2026-10-21-graphify-katalog-probelauf-flash.md)) ergab:
- graphify eignet sich hervorragend zur semantischen Topologieanalyse, visuellen Exploration und Erkennung von Widersprüchen über Korpora hinweg.
- Als primäre Datenbasis für CAD-Agenten scheitert graphify jedoch an drei Punkten:
  1. Das starre Metamodell erzwingt unpassende Knotentypen (alles Fachwissen landet als generischer Typ `concept`).
  2. Die Graphsuche arbeitet rein heuristisch über Vokabularexpansion und Volltext-BFS; es fehlt jede deterministische, parametrische Filterung nach Werkstoffen, Größen (z. B. exakt "M8"), Fertigungsverfahren oder Zahlenintervallen.
  3. Kanten sind standardmäßig ungerichtet, wodurch asymmetrische Beziehungen (`widerspricht`, `leitet_ab`) ihre Gerichtetheit einbüßen.

Der Wissenskatalog muss daher präzise typisiert, schemavalidiert, git- und reviewfreundlich (PR-Workflows) sowie ohne externe Laufzeitabhängigkeiten abfragbar sein.

## Optionen

| | Beschreibung | Für | Gegen |
|---|---|---|---|
| **A** graphify als Primärspeicher | Reiner Wissensgraph aus Markdown-Texten via graphify (`graph.json`) | Visuelle HTML-Darstellung fertig, Clustering und God-Nodes automatisch | Keine parametrische Filterung nach Zahlen/Werkstoffen, starres `file_type`-Schema, ungerichtete Kanten, ungeeignet für `check_design` |
| **B** Typisierte JSON-Dateien + Modul | Einzelne JSON-Dateien unter `katalog/eintraege/<thema>/<id>.json`, validiert gegen `katalog/schema.json`, In-Memory-Abfrage via `mechvane/katalog.py` | Git-freundlich (jede Regel diffbar im PR), schema-validiert, deterministische Filterung nach Parametern, null Abhängigkeiten (Python-Standardbibliothek) | Graph-Visualisierung erfordert sekundären Export |
| **C** Zentrale SQLite-Datenbank | Alle Einträge und Relationen in einer `katalog.sqlite`-Datei | SQL-Abfragen, relationale Integrität | Binärdatei im Git-Repo führt zu Merge-Konflikten bei kollaborativen PRs; schlechte Nachvollziehbarkeit bei Code-Reviews |
| **D** assistant-graph / Graph-DB-Dienst | Dedizierter Graphdatenbank-Service (z. B. Neo4j oder assistant-graph MCP-Server) | Komplexe Graph-Query-Sprache (Cypher / SPARQL) | Hoher Betriebsaufwand, externe Serverabhängigkeit, nicht offline-/CI-fähig ohne Container |

## Entscheidung

**Option B (Typisierte JSON-Dateien pro Eintrag mit schlankem Python-Abfragemodul).**

Im Einzelnen:

1. **Ablagestruktur:**
   - Jede Konstruktionsregel und jeder Wertesatz ist eine eigenständige, menschenlesbare JSON-Datei unter `katalog/eintraege/<thema>/<id>.json`.
   - Die Themenstrukturierung erfolgt fachbezogen (z. B. `schrauben`, `cnc`, `kleben`, `gleitlager`, `federn`).
   - Diese granulare Struktur ermöglicht saubere Git-Diffs, kollaborative Ergänzungen per Feature-Branch und isolierte Reviews.

2. **Formale Spezifikation (`katalog/schema.json`):**
   - Ein JSON-Schema sichert die Datenqualität ab: eindeutige `id`, `aussage`, `werte` (Liste mit `name`, `wert` oder `bereich`, `einheit`), `geltungsbereich` (`werkstoff`, `verfahren`, `feature`, `groesse`, `festigkeitsklasse` als Listen), `herkunft` (Norm über Sekundärquelle, Hersteller, Handbuch, Lehrbuch, Versuch, Erfahrung, Hypothese), `quellen` (mit URL, Fundstelle, wörtlichem Zitat, Abrufdatum), `begruendung`, `ausnahmen`, `haerte` (`fehler` vs. `hinweis`), `pruefstatus` (`automatisch`, `von_hand`, `offen`, `nicht_belegt`) und gerichtete `beziehungen` (`widerspricht`, `leitet_ab`, `ersetzt`, `gilt_fuer`).

3. **Schlankes Zugriffsmodul (`mechvane/katalog.py`):**
   - Das Modul bietet `load(path)`, `validate(eintrag)` und `query(...)`.
   - Ausschließlich Python-Standardbibliothek (`json`, `pathlib`, `re`); keine Laufzeitabhängigkeit von schwergewichtigen Validatoren wie `jsonschema` oder `pydantic`.
   - Abfragen erlauben parametrisches Filtern: Teilstring-Matching für Text, Werkstoffe, Verfahren und Features; exaktes Matching für Normgrößen (z. B. "M8").

4. **Rolle von graphify und SQLite:**
   - graphify bleibt als sekundäres Werkzeug erhalten: Aus den JSON-Dateien kann jederzeit ein Wissensgraph für visuelle Navigation und semantische Clusteranalysen erzeugt werden.
   - SQLite kann bei steigender Eintragszahl (ab mehreren tausend Datensätzen) als transiente In-Memory-Cache-Schicht im Ladevorgang von `mechvane/katalog.py` dienen, bleibt aber ein abgeleitetes Artefakt und nicht die Primärquelle.

## Folgen

- Neue Wissensquellen werden nach der automatisierten Link- und Zitatprüfung (`tools/check_sources.py`) direkt als JSON-Dateien in den Katalog überführt.
- Der Testlauf `tests/mechvane/check.py` prüft alle Katalogeinträge automatisiert gegen das Schema.
- CAD-Prüfungen (`check_design`) und Feature-Generatoren können Regeln und Grenzwerte deterministisch über `mechvane.katalog.query(...)` abfragen.
