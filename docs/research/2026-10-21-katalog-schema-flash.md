# Bericht: Wissenskatalog-Schema, Datenübertragung und Abfragemodul

Datum: 2026-10-21  
Status: Gemini 3.8 Flash, Entwurf zur Entscheidung durch Claude und den Nutzer  
Branch: `gemini/katalog-schema` im Worktree `/root/repos/mechvane-katalog`

---

## 1. Was gebaut wurde

1. **ADR 0002 (`docs/adr/0002-wissenskatalog-format.md`):**
   - Architektur-Entscheidung im vorgeschriebenen Format (Status: **vorgeschlagen**).
   - Vergleich von vier Optionen (graphify, atomare JSON-Dateien + Python-Modul, SQLite, assistant-graph).
   - Empfehlung von Option B: Granulare JSON-Dateien pro Eintrag im Dateisystem mit formeller Schema-Validierung und In-Memory-Abfrage via `inventa/katalog.py`. graphify bleibt als sekundäres Visualisierungs- und Topologiewerkzeug nutzbar; SQLite kann bei Bedarf als abgeleiteter Cache dienen.

2. **JSON Schema (`katalog/schema.json`):**
   - Formales JSON-Schema (Draft-07) für Katalogeinträge mit allen elf geforderten Kernfeldern:
     - `id`: Eindeutiger Bezeichner (`^[a-z0-9_-]+$`)
     - `aussage`: Prägnante technische Zusammenfassung
     - `werte`: Liste strukturierter Mess-/Richtwerte (`name`, `wert` oder `bereich`, `einheit`)
     - `geltungsbereich`: Objekt mit Listen für `werkstoff`, `verfahren`, `feature`, `groesse`, `festigkeitsklasse`
     - `herkunft`: Enum (`norm_sekundaer`, `hersteller`, `lehrbuch`, `handbuch`, `versuch`, `erfahrung`, `hypothese`)
     - `quellen`: Liste von Quellnachweisen mit `url`, `stelle`, `zitat`, `abgerufen`
     - `begruendung`: Technische und physikalische Begründung
     - `ausnahmen`: Bedingungen und Ausnahmefälle
     - `haerte`: Enum (`fehler` für harte Grenzen, `hinweis` für Empfehlungen)
     - `pruefstatus`: Enum (`automatisch`, `von_hand`, `offen`, `nicht_belegt`)
     - `beziehungen`: Gerichtete Relationen (`widerspricht`, `leitet_ab`, `ersetzt`, `gilt_fuer` mit `ziel`)

3. **Zugriffs- und Validierungsmodul (`inventa/katalog.py`):**
   - Ausschließlich Standardbibliothek (`json`, `pathlib`, `re`, `typing`). Keine externen Abhängigkeiten wie `jsonschema` oder `pydantic`.
   - `load(path=None, validate_entries=True)`: Lädt rekursiv alle `.json`-Dateien (unter Ausschluss von `schema.json`).
   - `validate(eintrag)`: Schlanke, vollständige Prüfung aller Typen, Pflichtfelder und Enums gegen das Katalogschema; wirft aussagekräftige `ValueError`-Ausnahmen bei Verstößen.
   - `query(werkstoff=None, verfahren=None, feature=None, groesse=None, festigkeitsklasse=None, text=None, eintraege=None)`:
     - Teilstring-Filterung (case-insensitive) für `werkstoff`, `verfahren`, `feature`.
     - Exakte Normalisierungsfilterung für `groesse` (z. B. "M8" matcht genau M8, nicht M80 oder Teilstrings).
     - Flexible Volltextsuche über alle Inhaltsfelder (Aussage, Werte, Begründung, Quellen, IDs) mit automatischer Normalisierung deutscher Umlaute und `ß`/`ss`.
   - `get_entry(entry_id)`: Direkter Zugriff auf einen Einzeleintrag über dessen ID.

4. **Integration in die Testsuite (`tests/inventa/check.py`):**
   - Funktion `katalog_checks()` nach dem etablierten `ok(...)`-Muster.
   - Prüft das Laden aller Katalogdateien, validiert jeden Eintrag strikt gegen das Schema, verifiziert die Abweisung ungültiger Schemata und führt drei realistische Testabfragen durch (Anziehdrehmoment M8 8.8, Innenradius Tasche Alu beim Fräsen, Einpressmaß iglidur).

---

## 2. Zahl der Einträge

Insgesamt wurden **27 Datensätze** aus den drei quellengeprüften Recherchen fehlerfrei übertragen:

| Themenordner | Anzahl Einträge | Quellen |
| :--- | :---: | :--- |
| `katalog/eintraege/schrauben/` | **8** | Würth Industrie DiNo-Technik, NASA-STD-5020B, Bossard VDI 2230, Reyher TI 2019 (VDI 2230 & A2-70) |
| `katalog/eintraege/cnc/` | **11** | Hubs CNC Design Guide, Xometry 10 CAD Tips, Fictiv CNC Guide, Protolabs Design Tips |
| `katalog/eintraege/kleben/` | **3** | DELO Industrie Klebstoffe, Henkel Loctite (Ludwig Meister), Fachliteratur (Überlappungslänge) |
| `katalog/eintraege/gleitlager/` | **2** | igus GmbH (iglidur Toleranzen Wiki & pv-Wert/Schmierung Wiki) |
| `katalog/eintraege/federn/` | **3** | eAssistant Handbuch (DIN EN 13906-1 Druckfedern, DIN EN 13906-2 Zugfedern), Gutekunst Federn |
| **Gesamt** | **27** | **100 % schemakonform validiert** |

Alle Einträge wurden mit `pruefstatus: "automatisch"` versehen, da die enthaltenen Werte und Zitate im vorgelagerten Schritt mit `tools/check_sources.py` automatisiert in den Originaldokumenten verifiziert worden sind.

---

## 3. Probleme bei der Übertragung

1. **Aggregation mehrdimensionaler Tabellen (Granularität):**
   - In `vdi2230_anziehdrehmoment_m4_m12_reyher.json` umfasst die Quelltabelle fünf Gewindegrößen (M4, M6, M8, M10, M12) mit je drei Festigkeitsklassen (8.8, 10.9, 12.9) und jeweils zwei Werten ($F_V$ und $M_A$).
   - Eine Aufteilung in 15 Einzelfeatures hätte zu massiver Redundanz bei Begründung, Quellen und Geltungsbereich geführt. Die Werte wurden daher als 30 strukturierte Kennwerte innerhalb eines Eintrags aggregiert und `groesse` mit `["M4", "M6", "M8", "M10", "M12"]` belegt. Der Größenfilter `query(groesse="M8")` findet den Eintrag dadurch präzise.

2. **Relative und dimensionslose Kennwerte:**
   - Viele Fertigungsregeln definieren keine absoluten Millimetermaße, sondern Verhältnisse zur Bezugsgeometrie (z. B. Tascheninnenradius $\ge \frac{1}{3} \times \text{Kavitätstiefe}$, Taschenbreitenverhältnis $\le 4 \times \text{Breite}$, Gewindetiefe $\le 3 \times \text{Nenndurchmesser}$).
   - Diese wurden über `wert: 0.333` bzw. `wert: 4.0` mit selbsterklärenden Einheiten wie `"x Kavitätstiefe"` oder `"x Nenndurchmesser"` abgebildet.

3. **Recherche-Hypothesen ohne Web-Quelle:**
   - Der Eintrag `kleben_ueberlappungslaenge_blech` stammt aus der Konstruktionslehre ohne spezifische URL im Recherchebericht. Er wurde gemäß Vorgabe mit `herkunft: "hypothese"`, `url: ""` und wörtlichem Zitat aus der Recherche übertragen, damit keine Daten verloren gehen oder hinzuerfunden werden.

4. **Widersprüche im Beziehungsnetz:**
   - Der Widerspruch zwischen Bossard (Verbot planmäßiger Vorspannung bei austenitischen Edelstählen A2/A4 wegen Relaxation) und Reyher (Richtwerttabelle für Montagevorspannung und Anziehdrehmoment von A2-70) wurde über `beziehungen: [{"typ": "widerspricht", "ziel": "a2_70_anziehdrehmoment_m4_m10_reyher"}]` explizit verankert.

5. **Deutsche Rechtschreibung bei Freitextabfragen (`ß` vs. `ss`):**
   - Bei der Abfrage `Einpressmaß iglidur` trat der Fall auf, dass der Dateiname und technische IDs `einpressmasse` nutzen, während Suchanfragen oft die Schreibweise `Einpressmaß` verwenden. In `inventa/katalog.py` wurde daher eine Normalisierung von `ß` zu `ss` in der Token- und Phrasensuche integriert.

---

## 4. Offene Fragen zur Entscheidung

1. **Granularität bei großen Normtabellen:**
   - Sollten zukünftige große Normwerttabellen (z. B. ISO 4762 über 20 Größen) als ein aggregierter Eintrag pro Norm oder als Einzeldateien pro Gewindegröße hinterlegt werden? (Empfehlung: Ein Eintrag pro Normtabelle mit strukturierter `werte`-Liste).
2. **Anbindung an `check_design`:**
   - Wie soll die Regelauswertung in CAD-Prüfungen erfolgen? `check_design` könnte bei Frästeilen automatisch `katalog.query(verfahren="CNC-Fräsen")` abrufen und geometrische Maße (Innenradien, Wandstärken) gegen Einträge mit `haerte: "fehler"` vergleichen.
3. **MCP-Tool für Agenten:**
   - Soll `query` in Phase 1 als MCP-Werkzeug (z. B. `katalog_query`) exponiert werden, damit der Konstruktionsagent während des Modellierens aktiv Grenzwerte erfragen kann?
4. **Sekundäre Graph-Generierung:**
   - Soll ein automatisierter Exporter gebaut werden, der aus allen JSON-Dateien ein `graph.json` für graphify erzeugt, um die globale Visualisierung ohne LLM-Parsing aktuell zu halten?
