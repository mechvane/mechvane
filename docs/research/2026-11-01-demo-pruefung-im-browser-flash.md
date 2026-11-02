# Live-Demo: Prüfung nach dem Speichern im Browser (Pyodide-Prototyp)

**Stand:** 2026-11-01  
**Bezug:** Issue #35, ROADMAP.md v0.1 Punkt 1b („Offen: Befunde auch in der Demo nach dem Speichern“), ADR 0001 (SolidCraft-Schicht), ADR 0005 (Arbeitsbereich).  
**Verfasser:** Gemini (Automatisierter Prototyp & Messbericht)

---

## 1. Ziel und Hintergrund

In der statischen Live-Demo (`mechvane.dev`, gehostet auf GitHub Pages ohne lokalen Mechvane-Server) waren Prüfbefunde bisher vorberechnet (`demos/<name>/findings.json`). Beim Speichern in „Model by hand“ (`model.html`) blieben die Befunde auf dem ursprünglichen Stand stehen.

Ziel dieses Prototyps ist es, nach jedem Speichern (`file.save` bzw. Ctrl+S) im Browser die Prüfregeln aus `mechvane/design_rules.py` direkt im WebAssembly-Python-Interpreter (**Pyodide**) auszuführen, sodass Prüfbefunde und Urteils-Badge live aktualisiert werden – exakt wie bei einer installierten lokalen Mechvane-Instanz.

---

## 2. Ansatz und Architektur

### 2.1 Pyodide-Einbindung & Paket-Bundle
Gemäß Pyodide-Dokumentation:
> „Pyodide is a Python distribution for the browser and Node.js based on WebAssembly.“

Eingesetzt wird die feste Version **Pyodide v0.26.4** von `cdn.jsdelivr.net`.
Über `tools/build_demo_site.py` wird ein kompaktes Archiv `demo/mechvane.zip` (ca. 38 KB) erzeugt, das ausschließlich die für die Bauteilprüfung notwendigen Python-Module enthält:
- `mechvane/__init__.py`
- `mechvane/browser_check.py` (Session- und Document-Shim)
- `mechvane/design_rules.py` (Regelprüfung)
- `mechvane/geometry.py` (Vektor- und Geometrieberechnungen)
- `mechvane/hole_tables.py` (Normloch- und Gewindetabellen)
- `mechvane/standard_parts.py`
- `mechvane/sketch_rule.py`
- `mechvane/documents.py`
- `mechvane/solidcraft.py`
- `mechvane/install.py`

Externe Abhängigkeiten wie `mcp` werden im Browser nicht geladen.

### 2.2 Lösung des Synchronisations-Problems (Pre-Fetching & Session-Shim)
`design_rules.check(...)` in Python ist rein synchron implementiert (`session.cmd(...)`, `session.tool("measure", ...)`). Da JavaScript im Hauptthread der Web-App asynchron arbeitet und `app.execute(...)` ein Promise zurückgibt, kann ein synchroner Python-Aufruf im selben Thread nicht blockierend auf ein JS-Promise warten.

**Lösung:** Vor dem Python-Aufruf liest JavaScript (`demo_check.js:fetchInspectionData`) alle relevanten Modelldaten parallel aus der eingebetteten SolidCraft-App aus:
1. `document.inspect` mit `measure: true` (Hüllquader, Zeitleiste, Körper)
2. `document.metadata` (Regelkonfiguration und Material)
3. `model.threads` (Gewindeprüfung)
4. `inspect.measure` (entspricht dem CLI-Werkzeug `measure`, liefert zugewiesene Körperwerkstoffe)
5. `timeline.inspect` für Bohrungs- und Zylinder-Features ohne vorliegende Definition
6. `model.faces` und `model.edges` für alle festgestellten Körper

Diese Daten werden als JSON-Struktur an den Python-Shim `mechvane.browser_check.check_browser(...)` übergeben. Der Shim implementiert `BrowserSession.cmd` und `BrowserSession.tool` als zeitschnelle Wörterbuchabfragen im Speicher.

### 2.3 UI-Integration & Interaktion
- **Badge-Aktualisierung:** In `model.html` wurde das Badge `<span id="verdict-badge" class="badge" hidden></span>` integriert. Bei Initialisierung sowie nach jedem Speichern wird es entsprechend dem Prüfurteil (`badge-ok`, `badge-warn`, `badge-fail`) gesetzt.
- **Interaktive Selektion:** Findings erhalten wie auf dem Server ein `select`-Objekt (`{type: "face", body, index, point}`). Beim Klick auf einen Befund in der Befundliste richtet SolidCraft die Kamera aus und selektiert die betreffende Fläche im 3D-Modell.
- **Baugruppen:** Die Baugruppenprüfung (`links.check`) verlangt Dateizugriffe auf verknüpfte Bauteile. Für Baugruppen wird daher ein Hinweis ausgegeben, dass die Verknüpfungsprüfung in der statischen Demo vorberechnet bleibt.

---

## 3. Messwerte (Performance & Downloadgröße)

Die Messungen wurden unter Node.js v24 mit der V8-WASM-Engine sowie per HTTP-Netzwerkanalyse gegen `cdn.jsdelivr.net` ermittelt.

### 3.1 Downloadgrößen (Netzwerk-Wire-Größe)
| Ressource | Unkomprimiert | Komprimiert (Wire/Gzip) |
|---|---|---|
| `pyodide.js` (Loader) | 18,912 Bytes (~19 KB) | 5,960 Bytes (~6 KB) |
| `pyodide.asm.wasm` (Interpreter) | 9,598,218 Bytes (~9.6 MB) | 2,991,722 Bytes (~2.85 MB) |
| `python_stdlib.zip` (Standardbibliothek) | 2,545,637 Bytes (~2.5 MB) | 2,306,344 Bytes (~2.20 MB) |
| `mechvane.zip` (Regeln & Tabellen) | 114,820 Bytes (~115 KB) | 38,154 Bytes (~38 KB) |
| **Gesamter Transfer** | **~12.3 MB** | **~5.09 MB** |

*Vergleich:* Die SolidCraft WebAssembly-Anwendung selbst (`solidcraft-web-*.wasm`) umfasst ca. 85.5 MB (komprimiert ca. 20 MB). Der Pyodide-Download macht somit lediglich rund ein Viertel des Web-App-Transfers aus.

### 3.2 Lade- und Ausführungszeiten
| Schritt | Gemessene Dauer | Erläuterung |
|---|---|---|
| `loadPyodide()` | **1,550.3 ms** | WASM-Kompilierung & Start des Python-Runtimes |
| `unpackArchive(mechvane.zip)` | **11.8 ms** | Entpacken der Module in das virtuelle Dateisystem |
| Python-Import (`design_rules`, `hole_tables`) | **377.4 ms** | Laden des Bytecodes und Erstellen der Normtabellen |
| **Erste Bauteilprüfung** (`bracket.solidcraft`) | **4.1 ms** | Erstprüfung inklusive Cache-Aufbau |
| **Folgende Prüfungen** (5 Durchläufe) | **2.34 ms** (2.30–2.39 ms) | Durchschnittliche Dauer pro Speichervorgang |

*Praxiseffekt:* Pyodide wird im Hintergrund parallel geladen, während der Nutzer die Web-App startet (Dauer ca. 1.5–2 s). Wenn der Nutzer seine erste Bearbeitung vornimmt und speichert, ist Pyodide bereits initialisiert. Die tatsächliche Neuberechnung der Regeln benötigt lediglich **2 bis 4 Millisekunden** und ist für den Nutzer verzögerungsfrei.

---

## 4. Verifikation & Testergebnisse

Die Korrektheit des Shims wurde gegen die vorberechneten Referenzdaten der Demo-Modelle (`flange` und `bracket`) validiert:
1. **Flansch (`flange.solidcraft`):**
   - Urteil: `ok` (100% Übereinstimmung)
   - Prüfungen: 8 bestandene Prüfungen
   - JSON-Struktur: Exakter Treffer mit `findings.json`
2. **Winkel mit Senkung an Wand (`bracket.solidcraft`):**
   - Urteil: `fail` (100% Übereinstimmung)
   - Befunde: 6 Prüfungen, davon 2 Fehlschläge:
     - `countersink_clearance`: Wandanschnitt durch 90°-Senkung nahe der Kante (`F4:csink:base`)
     - `printability`: Überhangwinkel > 45° in Baurichtung +Z
   - JSON-Struktur: Exakter Treffer mit `findings.json` inklusive Klick-Selektionsdaten.

Automatisierte Tests:
- `tools/test_demo_check.js`: Führt den Test headless unter Node + Pyodide aus.
- `tests/mechvane/check.py`: Prüft in `demo_pyodide_checks` Python-Shim, Archiv-Erzeugung, statische Assets und den Node-Testlauf (`0 failure(s)`).

---

## 5. Offene Punkte & Grenzen

1. **Baugruppen (Gelenkprüfung):** `links.check` erfordert mehrere geöffnete Sitzungen für die verknüpften Einzelteile. Dies bleibt in der statischen Demo vorerst vorberechnet mit dem Statushinweis:
   *„Assembly joint checks are precomputed in the live demo; install Mechvane to check joints live after saving.“*
2. **Datentyp-Konvertierung (JsNull):** Pyodide übergibt JavaScript `null` als `pyodide.ffi.JsNull`. In `mechvane/browser_check.py` wurde dafür ein Schutz implementiert, der nicht-zeichenkettenartige Parameter sauber auf Python `None` abbildet.
3. **Startseite:** Auf `index.html` (Check-Ansicht) wird Pyodide bewusst nicht geladen; die Startseite bleibt vollkommen leichtgewichtig und lädt nur statisches JSON.

---

## 6. Empfehlung

Die Pyodide-Lösung hat sich im Prototyp hervorragend bewährt:
- **Null Codeduplikation:** Die bestehenden Python-Regeln (`design_rules.py`, `hole_tables.py`, `geometry.py`) werden ohne jede Portierung nach JavaScript im Browser wiederverwendet.
- **Vernachlässigbare Rechenzeit:** 2.3 ms pro Prüfung garantieren sofortiges Feedback nach dem Speichern.
- **Empfehlung:** Den Pyodide-Prototyp wie gebaut in den Hauptzweig übernehmen.

---

## 7. Quellenverzeichnis

### Pyodide-Dokumentation
- **Quelle:** [Pyodide Documentation](https://pyodide.org/en/stable/)
- **Zitat:** „Pyodide is a Python distribution for the browser and Node.js based on WebAssembly.“

### Pyodide Quickstart Guide
- **Quelle:** [Pyodide Quickstart Guide](https://pyodide.org/en/stable/usage/quickstart.html)
- **Zitat:** „loadPyodide() which sets up the Python environment“

### SolidCraft Browser-Befehls-API
- **Quelle:** SolidCraft Repository: `docs/browser-api.md` (lokaler Klon `_ext/solidcraft`)
- **Zitat:** „Every call returns a promise. It resolves to the control reply's result, or rejects with an Error.“
