# Mechvane: Installation unter Windows

## Schnellweg mit pip (seit 0.1.0a2, getestet 2026-10-27)

```powershell
python -m venv $HOME\mechvane-venv
$HOME\mechvane-venv\Scripts\pip install mechvane
$HOME\mechvane-venv\Scripts\mechvane setup       # SolidCraft-CLI und Web-App, ca. 90 MB, einmalig
$HOME\mechvane-venv\Scripts\mechvane ui --demo   # Beispielmodelle im Browser
```

`mechvane setup` legt alles unter `%LOCALAPPDATA%\mechvane` ab (portables
SolidCraft-ZIP 0.21.0, SHA256 geprüft). Ohne venv geht auch `pip install --user mechvane`;
findet Windows `mechvane` dann nicht, `python -m mechvane setup` (bzw. `ui`, `mcp`) nehmen.

Getestet auf der Windows-11-VM (x64, Build 26220) mit einer venv aus CPython 3.13.13
(das Python aus Blender 5.2, auf der VM ist kein python.org-Python installiert):
`pip install mechvane` (0.1.0a2) → `mechvane setup` in 48 s → `mechvane ui --demo` baut die
Beispielmodelle in 14 s; Check-Ansicht (3D-Modell, Modellbaum, Befunde, markierte Fläche)
und „Model by hand“ (eingebettete SolidCraft-Web-App) im Edge geprüft, alle
API-Endpunkte für Teil und Baugruppe liefern 200; `mechvane mcp` beantwortet
`initialize`, `tools/list` und legt mit `new_part` eine Datei an. Bekannt: 0.1.0a2 lässt pro
SolidCraft-Sitzung einen leeren Ordner `%TEMP%\solidcraft-mcp-*` zurück (Fehler in
SolidCraft 0.21.0, [Issue #7836](https://github.com/tangency-labs/solidcraft/issues/7836); ab 0.1.0a3 räumt Mechvane selbst auf).

Der Rest dieser Anleitung beschreibt den älteren Weg von Hand (Repository-Kopie,
SolidCraft 0.17.0), nur noch für Entwicklung am Repository nötig.

---

## 1. Voraussetzungen

- **Windows 10/11 x64**
- **Python 3.12+** (getestet mit 3.14.7). Der Befehl `python` muss in der Windows-Eingabeaufforderung verfügbar sein.
- **Git** oder eine Kopie des Repositories.

---

## 2. Ordnerstruktur vorbereiten

Öffnen Sie die Eingabeaufforderung (`cmd.exe`) und legen Sie das Basisverzeichnis an:

```cmd
mkdir C:\Users\%USERNAME%\mechvane
mkdir C:\Users\%USERNAME%\mechvane\workspace
```

---

## 3. SolidCraft portable herunterladen und entpacken

1. Laden Sie das portable ZIP-Archiv von SolidCraft (z. B. `solidcraft-0.17.0-windows-x64-portable.zip`) von [GitHub Releases](https://github.com/tangency-labs/solidcraft/releases) herunter.
2. Entpacken Sie das Archiv nach `C:\Users\%USERNAME%\mechvane\`:

```powershell
powershell -NoProfile -Command "Expand-Archive -Path solidcraft-0.17.0-windows-x64-portable.zip -DestinationPath C:\Users\$env:USERNAME\mechvane\ -Force"
```

Das Verzeichnis enthält anschließend `solidcraft-cli.exe` unter:
`C:\Users\%USERNAME%\mechvane\solidcraft-0.17.0-windows-x64-portable\solidcraft-cli.exe`.

Prüfung:
```cmd
C:\Users\%USERNAME%\mechvane\solidcraft-0.17.0-windows-x64-portable\solidcraft-cli.exe --version
```
Ausgabe: `solidcraft-cli 0.17.0`.

---

## 4. Mechvane-Repository ablegen

Kopieren oder entpacken Sie das Repository in den Ordner:
`C:\Users\%USERNAME%\mechvane\repo\`

---

## 5. Umgebungsvariable setzen & Funktionsprüfung

Mechvane nutzt die Umgebungsvariable `SOLIDCRAFT_CLI`, um den Pfad zum CLI-Binary zu finden, ohne dass der System-PATH verändert werden muss.

Setzen Sie die Variable in Ihrer Session:

```cmd
set SOLIDCRAFT_CLI=C:\Users\%USERNAME%\mechvane\solidcraft-0.17.0-windows-x64-portable\solidcraft-cli.exe
cd /d C:\Users\%USERNAME%\mechvane\repo
```

### Referenzteile prüfen
```cmd
python tests\reference\check.py
```
Ergebnis: Alle 27 Prüfungen (Flansch, Gehäuse, Blechwinkel, Scharnier) müssen grün (`ok`) durchlaufen.

### Mechvane-Schicht prüfen
```cmd
python tests\mechvane\check.py
```
*Hinweis:* Bis einschließlich Test 41 (Skizzenregel, Modellbrowser, Arbeitsebenen, semantische Abfragen `find`, Konstruktionsregeln `check_design`, Baugruppengelenke über Dateigrenzen und #3330-Reparatur) laufen alle Tests grün. Bei `standard_parts.create` mit kosmetischem Gewinde (`solid.thread`) stürzt SolidCraft 0.17.0 unter Windows aktuell in der Engine mit einer Access Violation (`0xC0000005`) beim Container-Save ab (bekannter Upstream-Bug, unter Linux unauffällig).

---

## 6. Eigenes Bauteil erzeugen (Probe)

Ein einfaches Bauteil (Platte 40×30×5 mit Bohrung Ø 6 mm) lässt sich mit folgendem Skript über die Mechvane-Schicht bauen:

```python
import os
import sys

os.environ["SOLIDCRAFT_CLI"] = r"C:\Users\gollu\mechvane\solidcraft-0.17.0-windows-x64-portable\solidcraft-cli.exe"
sys.path.insert(0, r"C:\Users\gollu\mechvane\repo")

from mechvane.documents import Workspace, PART
from mechvane import sketch_rule

ws = Workspace(r"C:\Users\gollu\mechvane\workspace")
doc = ws.new(PART, "probe")
s = doc.session

commands = [
    {"command": "sketch.create", "params": {"plane": "XY", "name": "BaseSketch"}},
    {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 30]}},
    {"command": "sketch.finish", "params": {}},
    {"command": "solid.extrude", "params": {"sketch": "BaseSketch", "distance": 5, "name": "Plate"}},
    {"command": "sketch.create", "params": {"plane": "XY", "name": "HoleSketch"}},
    {"command": "sketch.circle.center", "params": {"center": [20, 15], "radius": 3}},
    {"command": "sketch.finish", "params": {}},
    {"command": "solid.extrude", "params": {"sketch": "HoleSketch", "distance": 5, "operation": "cut", "name": "Hole"}},
]

s.batch(commands)
sketch_rule.enforce(s)
doc.save()
print("probe.solidcraft erfolgreich erstellt.")
ws.close("probe")
```

Das Modell wird unter `C:\Users\%USERNAME%\mechvane\workspace\probe.solidcraft` gespeichert.

---

## 7. Claude Code / MCP-Server konfigurieren

Kopieren Sie die Vorlage `docs\mcp.windows.example.json` nach `C:\Users\%USERNAME%\mechvane\repo\.mcp.json`:

```json
{
  "mcpServers": {
    "solidcraft": {
      "command": "C:\\Users\\gollu\\mechvane\\solidcraft-0.17.0-windows-x64-portable\\solidcraft-cli.exe",
      "args": ["mcp", "--allow-path", "C:\\Users\\gollu\\mechvane\\workspace"]
    },
    "mechvane": {
      "command": "python",
      "args": ["-m", "mechvane"],
      "cwd": "C:\\Users\\gollu\\mechvane\\repo",
      "env": {
        "MECHVANE_WORKSPACE": "C:\\Users\\gollu\\mechvane\\workspace",
        "PYTHONPATH": "C:\\Users\\gollu\\mechvane\\repo",
        "SOLIDCRAFT_CLI": "C:\\Users\\gollu\\mechvane\\solidcraft-0.17.0-windows-x64-portable\\solidcraft-cli.exe"
      }
    }
  }
}
```

*Hinweis zu MCP mit Python:* Für den MCP-Server `python -m mechvane` wird das Python-Paket `mcp` benötigt. Falls dies in der Standardinstallation nicht vorhanden ist, kann ein virtuelles Environment unter `C:\Users\%USERNAME%\mechvane\venv` angelegt und in `.mcp.json` referenziert werden (`C:\Users\%USERNAME%\mechvane\venv\Scripts\python.exe`).
