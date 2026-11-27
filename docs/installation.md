# Mechvane installieren (Windows & Linux)

Mechvane ist die Maschinenbau-Schicht auf [SolidCraft](https://github.com/tangency-labs/solidcraft) und arbeitet über MCP am offenen SolidCraft-Fenster. Von Hand modellierst du in der SolidCraft-App selbst *(die frühere Web-UI `mechvane ui` ist entfernt)*.

## 1. Voraussetzungen
- **Python ≥ 3.11** (Windows: `python`, Linux: `python3`) und **MCP-fähiger Agent** (z. B. Claude Code)
- **SolidCraft-App** in der Version **0.43.0** ([Release v0.43.0](https://github.com/tangency-labs/solidcraft/releases/tag/v0.43.0), Windows x64: `solidcraft-0.43.0-windows-x64-portable.zip` oder Installer `.msi`, Linux x86_64: [`solidcraft-0.43.0-linux-x86_64.tar.gz`](https://github.com/tangency-labs/solidcraft/releases/download/v0.43.0/solidcraft-0.43.0-linux-x86_64.tar.gz) (entpackt in den Ordner `solidcraft-0.43.0-linux-x86_64/`, die App ist `bin/solidcraft` darin) oder `.AppImage`). Nicht die neueste Version nehmen: Mechvane v0.1 ist auf 0.43.0 abgenommen, und SolidCraft ab 0.49 stürzt auf Windows mit Intel-Grafik beim Start ab (SolidCraft-Issue #22110, der Fix steckt noch in keinem stabilen Release).

## 2. Installation in einer venv (`pip install mechvane`)
Unter PowerShell steht `&` vor `$HOME`-Pfaden:

```powershell
# Windows (PowerShell)
python -m venv $HOME\mechvane-venv
& $HOME\mechvane-venv\Scripts\pip install mechvane
```

```sh
# Linux
python3 -m venv ~/mechvane-venv
~/mechvane-venv/bin/pip install mechvane
```

## 3. `mechvane setup`
Lädt `solidcraft-cli` (**0.43.0**, rund 175 MB Download, entpackt rund 450 MB unter Linux) mit SHA256-Prüfung herunter. Das ist die Kommandozeile, mit der Mechvane ohne Fenster arbeitet. Die App aus Schritt 1 brauchst du für das Fenster. Beide gehören zu 0.43.0. Danach testet `mechvane setup` mit `solidcraft-cli --version`, ob die CLI startet (Cache: Windows `%LOCALAPPDATA%\mechvane` bzw. `~/.cache/mechvane`, Linux `~/.cache/mechvane` bzw. `$XDG_CACHE_HOME/mechvane`; Suchreihenfolge: `$SOLIDCRAFT_CLI` → Cache → `PATH`):

```powershell
# Windows (PowerShell) – Fallback: & $HOME\mechvane-venv\Scripts\python -m mechvane setup
& $HOME\mechvane-venv\Scripts\mechvane setup
```

```sh
# Linux – Fallback: ~/mechvane-venv/bin/python -m mechvane setup
~/mechvane-venv/bin/mechvane setup
```

Am Ende steht `Ready. Next: connect your agent (mechvane mcp) and the SolidCraft app you have open, see docs/installation.md`.

## 4. Agent anbinden (`mechvane mcp`)
`mechvane mcp` startet den MCP-Server über `stdio` (`--workspace <Ordner>`, sonst `$MECHVANE_WORKSPACE`, sonst `./workspace`). Im Projektordner `.mcp.json` anlegen (Benutzername anpassen; JSON löst `~` nicht auf):

**Windows (`.mcp.json`):**

```json
{
  "mcpServers": {
    "mechvane": {
      "command": "C:\\Users\\<Benutzer>\\mechvane-venv\\Scripts\\mechvane.exe",
      "args": ["mcp", "--workspace", ".\\workspace"]
    }
  }
}
```

**Linux (`.mcp.json`):**

```json
{
  "mcpServers": {
    "mechvane": {
      "command": "/home/<benutzer>/mechvane-venv/bin/mechvane",
      "args": ["mcp", "--workspace", "./workspace"]
    }
  }
}
```

*(Alternativ `"command"` auf `Scripts\\python.exe` bzw. `bin/python` und `"args": ["-m", "mechvane", "mcp", "--workspace", "./workspace"]`.)*

## 5. Verbindung zum offenen Fenster (`connect_window`)
1. In SolidCraft **Settings > Assistant > Agents through MCP > Let AI agents connect** aktivieren (oder App mit `--control PORT` starten). Die App schreibt `<port>.token`, `<port>.pid` und `current.port` nach `%LOCALAPPDATA%\SolidCraft\control` (Windows) bzw. `~/.local/share/solidcraft/control` (`$XDG_DATA_HOME/solidcraft/control`, überschreibbar über `SOLIDCRAFT_CONTROL_DIR`).
2. Agent ruft `connect_window` auf (`address="auto"`, bei mehreren Fenstern `"127.0.0.1:PORT"`). Lesen (`measure`, `check_design`, `verify_view`, `find`, `browser`, `check_parameters`) und Modellieren (`run` nach Positivliste, ohne Datei-/Speicher-Schritte) wirken im aktiven Tab; gespeichert wird in SolidCraft (`Ctrl+S`), Baugruppen (`add_joint`, `bolted_connection`) brauchen Dateien im Workspace. Details: [docs/mechvane-mcp.md](mechvane-mcp.md).

## 6. Erster Test: einen Flansch bauen lassen
1. SolidCraft mit leerem Design öffnen (**Let AI agents connect** aktiv) und Claude Code im Ordner mit `.mcp.json` starten:
   > Verbinde dich per `connect_window` mit dem offenen SolidCraft-Fenster und baue einen Flansch (Platte 60 × 60 × 8 mm auf XY, obere Kanten 1 mm gefast, 4 Bohrungen Ø 6,6 mm auf Lochkreis 45 mm, ohne weitere Bohrung; Sollvolumen etwa 27 590 mm³). Prüfe ihn mit `check_design`.
2. Gegenprüfung im Terminal am offenen Fenster (Exit-Code `0`, alle Regeln `ok`; optional `--profile fdm_0.4` oder `cnc_alu`):

```powershell
# Windows (PowerShell)
& $HOME\mechvane-venv\Scripts\mechvane check
```

```sh
# Linux
~/mechvane-venv/bin/mechvane check
```

*(Im geklonten Repo liegt die Referenz `tests/reference/flansch.build.json`, und `python3 tests/reference/check.py flansch` prüft zudem Volumen und Bounding-Box; nutzt `SOLIDCRAFT_CLI` oder `PATH`.)*

## 7. Häufige Fehler
- **`invalid choice: 'check'` oder `connect_window` fehlt:** Mechvane ist zu alt (0.1.0a25 und älter kennen beides nicht). `pip install --upgrade mechvane` in der venv, danach `mechvane --help` zeigt `check`.
- **`no running SolidCraft window found`:** In SolidCraft **Let AI agents connect** einschalten oder App mit `--control PORT` starten.
- **`stale files from an app that was force-quit`:** Verwaiste `.token`/`.pid`-Dateien im Steuerordner → App neu starten oder alte Dateien dort löschen.
- **`several SolidCraft windows are open`:** Mehrere Fenster offen → `connect_window` mit `address="127.0.0.1:PORT"` aufrufen.
- **`another tab is in front`:** Tab gewechselt → ursprünglichen Tab wieder öffnen oder `close_document` + `connect_window`.
- **PowerShell `Unerwartetes Token` / Befehl nicht gefunden:** `&` vor `$HOME\...` setzen; ohne `PATH`-Eintrag `python -m mechvane <unterbefehl>`.
- **Windows-Grafik (`WGPU_BACKEND`):** Bei reiner Intel-Grafik setzt Mechvane für die CLI-Prozesse, die es selbst startet, `WGPU_BACKEND=dx12` als Behelf gegen Vulkan-Abstürze bei runden Flächen (ein Workaround, die Ursache liegt im Intel-Vulkan-Treiber und in SolidCraft); bei NVIDIA/AMD bleibt Vulkan aktiv. Manuell gesetztes `WGPU_BACKEND` wird nicht überschrieben.
- **Befehl am Fenster abgelehnt:** Datei-, Speicher- und Baugruppenbefehle arbeiten nicht im ungesicherten Fenster (`save_document` lehnt ab, `add_joint`/`bolted_connection` brauchen Dateien).
