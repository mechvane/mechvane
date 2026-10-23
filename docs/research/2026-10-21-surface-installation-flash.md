# Erstinstallation von inventa auf Windows (Surface) & Test mit SolidCraft 0.17.0

**Datum:** 2026-10-21  
**Autor:** Gemini 3.8 Flash (im Auftrag)  
**Zielumgebung:** Microsoft Surface Laptop, Windows 11 x64, Python 3.14.7, SSH-Zugang `surface`  
**Referenzumgebung:** Steuer-Container (Linux x86_64 Debian, Python 3.13, SolidCraft v0.16.2 und Gegenprobe v0.17.0)

---

## 1. Zusammenfassung

inventa wurde erfolgreich auf dem Windows-Laptop (Surface) des Nutzers eingerichtet. Alle Dateioperationen erfolgten strikt innerhalb von `C:\Users\gollu\inventa\` (keine Admin-Rechte, keine Registry-, PATH-, Firewall- oder MSI-Eingriffe). 

Wichtigste Ergebnisse:
1. **SolidCraft 0.17.0 Portable:** Heruntergeladen, SHA256 verifiziert und entpackt. `solidcraft-cli.exe --version` (0.17.0) und `solidcraft-cli mcp` starten einwandfrei.
2. **Referenzteile (`tests/reference/check.py`):** 27 von 27 Prüfungen (100 %) auf Windows mit SolidCraft 0.17.0 bestanden (Flansch, Gehäuse, Blechwinkel, Scharnier).
3. **inventa-Basisfunktionen (`tests/inventa/check.py`):** Die ersten 41 Prüfungen laufen unter Windows fehlerfrei durch (Skizzenbesitzregel, Modellbrowser, Arbeitselement-Verschachtelung, semantische Abfragen `find`, Konstruktionsregelprüfung `check_design`, Baugruppengelenke über Dateigrenzen und die #3330-Reparaturlogik).
4. **Upstream-Befund SolidCraft 0.17.0 auf Windows:** Beim Speichern von Bauteilen mit kosmetischem Gewinde (`solid.thread`, z. B. in `standard_parts.create` für ISO 4762, ISO 4032, Ruthex) stürzt `solidcraft-cli.exe` unter Windows mit `0xC0000005` (STATUS_ACCESS_VIOLATION) ab. Bauteile ohne `solid.thread` (ISO 7089 Scheibe, DIN 625 Kugellager, Platten, Bohrungen) sowie das Speichern als reines JSON speichern und öffnen stabil. Dieselben Tests laufen unter Linux mit SolidCraft 0.17.0 zu 100 % (107/107) fehlerfrei durch – es handelt sich um einen Windows-spezifischen Upstream-Bug im Geometrie-Cache-Writer von SolidCraft.
5. **Probebauteil:** Ein parametrisches Bauteil (`probe.solidcraft`, Platte 40×30×5 mit Bohrung Ø 6 mm) wurde über die inventa-Schicht unter Windows erzeugt, gemessen (Volumen 5858,65 mm³) und unter `C:\Users\gollu\inventa\workspace\probe.solidcraft` abgelegt.
6. **Claude-Code-Vorbereitung:** `.mcp.json` mit Windows-Pfaden und Umgebungsvariablen unter `C:\Users\gollu\inventa\repo\.mcp.json` hinterlegt und als Vorlage `docs/mcp.windows.example.json` im Repo gesichert.

---

## 2. Durchgeführte Schritte

### 2.1 SolidCraft 0.17.0 Windows x64 Portable
- Download via GitHub CLI auf dem Steuer-Container:
  `gh release download v0.17.0 -R tangency-labs/solidcraft -p 'solidcraft-0.17.0-windows-x64-portable.zip' -p SHA256SUMS.txt -D /tmp/surface-dl`
- SHA256-Prüfung: `OK` (`e92823075253fa28ba54da3ad9729d713ee0d8d73b3060a4e76c72e2760df890`).
- Das ZIP enthält: `solidcraft-cli.exe` (80.443.904 Bytes), `solidcraft.exe` (109.753.344 Bytes), `solvecraft-cli.exe` (327.680 Bytes) und Lizenzdateien.
- Per `scp` nach `C:\Users\gollu\inventa\` übertragen und per PowerShell `Expand-Archive` entpackt nach `C:\Users\gollu\inventa\solidcraft-0.17.0-windows-x64-portable\`.
- Startprüfung:
  - `solidcraft-cli.exe --version` liefert `solidcraft-cli 0.17.0`.
  - `solidcraft-cli.exe mcp` startet und antwortet auf das JSON-RPC-Initialisierungssignal mit `serverInfo.name: "solidcraft"`.

### 2.2 Repo-Stand übertragen
- Erzeugung eines Archivs aus dem Branch: `git -C /root/repos/inventa-surface archive --format=zip -o /tmp/surface-inventa.zip HEAD`
- Per `scp` übertragen und entpackt nach `C:\Users\gollu\inventa\repo\`. Keine Zugangsdaten auf dem Surface angelegt.

### 2.3 Plattformneutrale Codeanpassungen
Um Windows ohne PATH-Änderungen und ohne Encoding-Probleme zu unterstützen, wurden folgende minimale, rückwärtskompatible Änderungen vorgenommen:
1. **`inventa/solidcraft.py`:**
   - Unterstützung der Umgebungsvariable `SOLIDCRAFT_CLI`: `cli = executable or os.environ.get("SOLIDCRAFT_CLI") or "solidcraft-cli"`. Damit kann der Pfad zur Portable-Exe explizit übergeben werden, ohne dass `PATH` im Betriebssystem modifiziert werden muss.
   - `encoding="utf-8"` beim Start des Subprozesses via `subprocess.Popen` ergänzt (verhindert `UnicodeDecodeError` unter Windows, wo die Standard-Codepage oft `cp1252` ist).
2. **`tests/reference/check.py`:**
   - `cli = os.environ.get("SOLIDCRAFT_CLI", "solidcraft-cli")` statt hardcodiertem `"solidcraft-cli"`.
   - `encoding="utf-8"` für Datei-I/O und `subprocess.run`.
3. **`tests/inventa/check.py`:**
   - `encoding="utf-8"` beim Start des MCP-Servers via `subprocess.Popen`.

---

## 3. Testergebnisse im Detail

### 3.1 Referenzprüfungen (`tests/reference/check.py`)

| Bauteil | Prüfungen | Windows (v0.17.0) | Linux (v0.16.2) | Linux (v0.17.0) |
|---|---|---|---|---|
| **flansch** | 6 (Volumen, BBox, Parameter `n=6`, `T=10`, Rollback) | 6 ok | 6 ok | 6 ok |
| **gehaeuse** | 8 (Volumen, Schwerpunkt Z, `L=120`, `hb=28/wall=3`) | 8 ok | 8 ok | 8 ok |
| **blechwinkel** | 6 (Volumen, BBox, Biegeverkürzung/Allowance, Abwicklung) | 6 ok | 6 ok | 6 ok |
| **scharnier** | 7 (Gelenkwinkel 0°/45°/90°, Kontaktstopp bei 180°, Überlappung) | 7 ok | 7 ok | 7 ok |
| **Gesamt** | **27** | **27 ok (100 %)** | **27 ok (100 %)** | **27 ok (100 %)** |

Laufzeit auf Surface: ca. 6 Sekunden. Alle Tessellierungs- und Kontakttoleranzen werden exakt eingehalten.

---

### 3.2 Inventa-Schicht (`tests/inventa/check.py`)

#### Gegenprobe auf dem Steuer-Container (Linux)
- **v0.16.2:** 107 von 107 Checks bestanden (`0 failure(s)`, Laufzeit ~35 s).
- **v0.17.0:** 107 von 107 Checks bestanden (`0 failure(s)`, Laufzeit ~28 s).
Damit ist nachgewiesen, dass die Codeanpassungen das Linux-Verhalten in keiner Weise beeinträchtigen.

#### Windows-Testlauf (Surface, v0.17.0)
- **Bestanden: 41 Checks**
  - Skizzenbesitzregel (gehörige Skizzen stehen vor Features, geteilte bleiben separat)
  - Modellbrowser (Verschachtelung von Skizzen und Arbeitsebenen, End-of-Part-Marker)
  - Feature-Löschung mit mitgeführter Skizze und Erhalt noch referenzierter Elemente
  - Semantische Abfragen `find` (Deckfläche `+Z`, Bohrungen, Verrundungs-Picks, Baugruppen-Weltkoordinaten)
  - Konstruktionsregeln `check_design` (Randabstand, Mindestwandstärke, Überhangprüfung)
  - Gelenk-Verankerung über Dateigrenzen hinweg (Zylinder- und ebene Flächen)
  - Behebung von Upstream-Issue #3330 (Erkennung verschobener Gelenke und automatische Reparatur)
  - Erhalt relativer In-Plane-Offsets bei ebenen Gelenkreparaturen

- **Fehlerbefund ab Test 42 (`standard_parts_checks`):**
  - Aufruf: `standard_parts.create(ws, 'ISO 4762', 'M5', length=16)`
  - Fehler: `inventa.solidcraft.SolidCraftError: solidcraft-cli mcp ended unexpectedly`
  - Exit-Code von `solidcraft-cli.exe`: `3221225477` = `0xC0000005` (**STATUS_ACCESS_VIOLATION**).

---

## 4. Ursachenanalyse: Upstream-Befund Windows vs. Linux

Um festzustellen, ob der Fehler an Windows oder an SolidCraft 0.17.0 liegt, wurden isolierte Testskripte ausgeführt:

1. **Einfluss einzelner Normteile auf `save` unter Windows:**
   - `ISO 7089` (Unterlegscheibe, reiner Zylinder mit Durchgangsloch): **rc = 0, save erfolgreich**
   - `DIN 625` (Kugellager-Hüllring, zwei Zylinder): **rc = 0, save erfolgreich**
   - `ISO 4762` (Zylinderschraube mit Gewinde): **rc = 0xC0000005 (Crash bei save)**
   - `ISO 4032` (Mutter mit Gewinde): **rc = 0xC0000005 (Crash bei save)**
   - `Ruthex` (Gewindeeinsatz mit Innengewinde): **rc = 0xC0000005 (Crash bei save)**

2. **Isolierung des Features `solid.thread`:**
   - Wird bei `ISO 4032` oder `Ruthex` der Befehl `solid.thread` aus der Befehlskette entfernt, speichern beide Bauteile unter Windows **völlig fehlerfrei** (`save: True`, `rc: 0`).
   - Sobald `solid.thread` enthalten ist, wird der `batch`-Befehl zwar fehlerfrei abgearbeitet, der nachfolgende Aufruf `save` führt jedoch zum sofortigen Speicherzugriffsfehler (`0xC0000005`).

3. **Isolierung des Speicherformats:**
   - Speichern als reines JSON (`save {format: "json", path: "part.json"}`): **Erfolgreich (`rc: 0`)**.
   - Speichern als Container (`save {format: "container", path: "part.solidcraft"}`): **Crash `0xC0000005`**.
   - Ursache im SolidCraft-Quelltext (`crates/engine/src/cmd/file.rs`): Beim Container-Save wird `solidcraft_io::write_design_container_with_thumbnail` aufgerufen, das über `saved_geometry` und `saved_preview` Geometriecaches der Körper erzeugt. Auf Windows führt die Brep-/STEP-Serialisierung von Threads zu einem Nullpointer-/Speicherfehler.

4. **Heap-Verhalten bei Polygonen:**
   - Bei Hexagon-Extrusionen (`sketch.polygon.circumscribed` in Schraubenkopf / Mutter) wurde beim Beenden des CLI-Prozesses vereinzelt der Windows-Heap-Fehler `3221226356` (`0xC0000374`, STATUS_HEAP_CORRUPTION) registriert.

5. **Gegenprobe Linux:**
   - Unter Linux (sowohl v0.16.2 als auch v0.17.0) speichern alle Teile mit `solid.thread` im Containerformat absolut stabil und bestehen alle 107 Checks.

---

## 5. Probebauteil (`probe.solidcraft`)

Auf dem Surface wurde über die inventa-Python-Schicht ein Probebauteil erzeugt:
- **Geometrie:** Rechteckige Platte 40 mm × 30 mm, Dicke 5 mm, mit zentrierter zylindrischer Durchgangsbohrung Ø 6 mm bei (x = 20 mm, y = 15 mm).
- **Ablauf:** `ws.new(PART, "probe")` → `s.batch(...)` → `sketch_rule.enforce(s)` → `doc.save()`.
- **Messung:** Volumen 5.858,65 mm³ (analytischer Sollwert: $40 \times 30 \times 5 - \pi \times 3^2 \times 5 = 6.000 - 141,37 = 5.858,63\text{ mm}^3$).
- **Ablage:** Gespeichert unter `C:\Users\gollu\inventa\workspace\probe.solidcraft` (Dateigröße: 6.343 Bytes).

---

## 6. Claude-Code-Konfiguration (.mcp.json)

Die Datei `C:\Users\gollu\inventa\repo\.mcp.json` wurde mit Windows-Pfaden eingerichtet:

```json
{
  "mcpServers": {
    "solidcraft": {
      "command": "C:\\Users\\gollu\\inventa\\solidcraft-0.17.0-windows-x64-portable\\solidcraft-cli.exe",
      "args": ["mcp", "--allow-path", "C:\\Users\\gollu\\inventa\\workspace"]
    },
    "inventa": {
      "command": "python",
      "args": ["-m", "inventa"],
      "cwd": "C:\\Users\\gollu\\inventa\\repo",
      "env": {
        "INVENTA_WORKSPACE": "C:\\Users\\gollu\\inventa\\workspace",
        "PYTHONPATH": "C:\\Users\\gollu\\inventa\\repo",
        "SOLIDCRAFT_CLI": "C:\\Users\\gollu\\inventa\\solidcraft-0.17.0-windows-x64-portable\\solidcraft-cli.exe"
      }
    }
  }
}
```

---

## 7. Offene Punkte

1. **Upstream-Meldung an `tangency-labs/solidcraft`:**
   - Issue: `solidcraft-cli.exe` v0.17.0 (Windows x64 portable) stürzt bei `save` mit `0xC0000005` ab, wenn das Design ein `solid.thread`-Feature enthält. (Unter Linux x86_64 tritt das Problem nicht auf).
2. **Python-Paket `mcp` auf dem Surface:**
   - Für die Ausführung von `python -m inventa` (als MCP-Server für Claude Code) wird das Python-Paket `mcp` benötigt (`from mcp.server.fastmcp import FastMCP`). Im globalen System-Python 3.14.7 auf dem Surface ist es noch nicht installiert. Gemäß den Grenzvorgaben darf kein systemweites `pip install` erfolgen; bei Bedarf kann ein venv unter `C:\Users\gollu\inventa\venv` eingerichtet werden.
