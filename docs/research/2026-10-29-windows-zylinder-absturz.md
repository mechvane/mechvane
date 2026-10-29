# SolidCraft stürzt unter Windows beim Speichern eines Zylinders ab

Stand 2026-10-29, eigene Messung (Claude Code auf dem Surface des Nutzers), kein Gemini.

## Kurzfassung

`mechvane ui --demo` bricht auf dem Surface mit `SolidCraftError: solidcraft-cli mcp ended
unexpectedly` ab. Ursache ist ein Absturz von `solidcraft-cli.exe` selbst: Exit-Code
`0xC0000005` (STATUS_ACCESS_VIOLATION) beim `save`, sobald das Teil einen extrudierten Kreis
enthält. Ein extrudiertes Rechteck speichert fehlerfrei. Damit ist die Vermutung vom 2026-10-21
(`2026-10-21-surface-installation-flash.md`: Absturz nur mit `solid.thread`) widerlegt: das
Gewinde ist nicht nötig, und der Fehler besteht in SolidCraft 0.25.1 weiter.

Folge: unter Windows lässt sich auf diesem Rechner kein Normteil anlegen (Scheibe, Mutter,
Schraube), die Demo startet nicht, und jedes eigene Teil mit Bohrung oder Zylinder geht beim
Speichern verloren.

**Ursache gefunden (Nachtrag 2026-10-29, siehe „Messungen auf dem Surface“):** Der Absturz liegt im
Vulkan-Treiber der Intel-Grafik (`igvk64.dll`, Iris Plus, Treiber 31.0.101.2145), nicht in
SolidCraft und nicht an AVX-512. Mit `WGPU_BACKEND=dx12` speichern Zylinder und alle Normteile
fehlerfrei.

## Umgebung

| | |
|---|---|
| Rechner | Surface Laptop, Intel Core i7-1065G7 (Ice Lake, x64 nativ) |
| Windows | Windows 11 Home Insider Preview, Build 26220 |
| Python | 3.14.7 (AMD64), venv `~\mechvane-venv` |
| Mechvane | 0.1.0a4 aus PyPI |
| SolidCraft | 0.25.1, `solidcraft-0.25.1-windows-x64-portable` aus `mechvane setup` |

Die Windows-11-VM (Test vom 2026-10-28, nur über SSH) zeigte das Problem nicht, ob dort
`ui --demo` lief, ist nicht vermerkt.

## Eingrenzung

Jeder Fall in einem frischen Workspace unter `%TEMP%`, eigene SolidCraft-Session, danach
`doc.save()` (MCP-Tool `save`, Container-Format).

| Inhalt vor dem Speichern | Ergebnis |
|---|---|
| Rechteck 40×30, `solid.extrude` 5 mm | ok |
| Parameter `h`, Rechteck, `solid.extrude` mit `distance: "h"` | ok |
| Parameter `d2`, bemaßter Kreis (`sketch.draw.dimensioned`), **ohne** Extrusion | ok |
| Parameter, Skizzen bis vor die erste Extrusion (Scheibe ISO 7089) | ok |
| Kreis r = 6 (`sketch.circle.center`), `solid.extrude` 2 mm | **0xC0000005** |
| bemaßter Kreis mit festem Wert `12 mm`, `solid.extrude` | **0xC0000005** |
| bemaßter Kreis mit Parameter, `solid.extrude` mit Zahl statt Parameter | **0xC0000005** |
| `standard_parts.create` ISO 7089, ISO 4032, ISO 4762 (M6) | **0xC0000005** |

`sketch_rule.enforce` und `set_metadata` spielen keine Rolle (Absturz auch ohne beides). Die
`batch`-Befehle laufen fehlerfrei durch, es stürzt erst `save` ab. Auf stderr schreibt
SolidCraft vor dem Absturz nur die übliche Zeile zu den erlaubten Pfaden.

Kleinster Nachbau (mit dem Python des venv):

```python
import tempfile
from mechvane.documents import Workspace, PART

ws = Workspace(tempfile.mkdtemp())
doc = ws.new(PART, "zylinder")
doc.session.batch([
    {"command": "sketch.create", "params": {"plane": "XY", "name": "S"}},
    {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 6.0}},
    {"command": "sketch.finish", "params": {}},
    {"command": "solid.extrude", "params": {"sketch": "S", "distance": 2, "name": "P"}},
])
doc.save()   # SolidCraftError, solidcraft-cli.exe endet mit 0xC0000005
```

## Vermutungen (nicht geprüft)

1. **CPU-Befehlssatz:** Ice Lake hat AVX-512, eine VM blendet es oft aus. Ein fehlerhafter
   optimierter Pfad (Tessellierung oder Kompression beim Container-Save) würde dann nur auf
   echter Hardware auftreten. Passt dazu, dass ebene Flächen gehen und gekrümmte nicht.
2. **Insider-Build 26220:** Der Rechner läuft auf einer Vorabversion von Windows, die VM
   vermutlich nicht.

## Abgleich mit der VM und mit Upstream (2026-10-29, Steuer-Container)

| | Windows-11-VM (läuft) | Surface (stürzt ab) |
|---|---|---|
| CPU | Intel Core i7-10700K (Comet Lake), Gast mit `cpu: host` | Intel Core i7-1065G7 (Ice Lake) |
| AVX-512 | nein (`/proc/cpuinfo` des Hosts: nur AVX2) | ja |
| Windows | Build 26220 (Test 2026-10-27) | Build 26220 |

Gleicher Windows-Build auf beiden: Vermutung 2 (Insider-Build) entfällt. Der einzige bekannte Unterschied
ist AVX-512; das stützt Vermutung 1, beweist sie aber nicht.

Upstream: [tangency-labs/solidcraft#5589](https://github.com/tangency-labs/solidcraft/issues/5589)
(anderer Melder, 2026-10-23) zeigt dasselbe Bild: `0xc0000005` in `solidcraft-cli.exe` nur bei `--save`,
STL/3MF-Export geht, auslösend dort ein Fillet (gekrümmte Fläche). Der Maintainer konnte es unter macOS
und Windows 11 (Build 26300) nicht nachstellen und hat nach Prozessor und Windows-Build gefragt; darauf
kam keine Antwort. Unser Nachbau ist kleiner (ein extrudierter Kreis) und liefert genau diese Angaben.

## Messungen auf dem Surface (2026-10-29, Nachtrag)

Gleicher Nachbau (Kreis r = 6, `solid.extrude` 2 mm), SolidCraft 0.25.1:

| Aufruf | Ergebnis |
|---|---|
| `save` (Container) | **0xC0000005** |
| `export`, `format: "step"` | ok, 5 734 Byte |
| `export`, `format: "3mf"` | ok, 13 639 Byte |
| `save` mit `WGPU_BACKEND=dx12` | **ok** |
| `save` mit `WGPU_BACKEND=gl` | **0xC0000005** |
| `standard_parts.create` ISO 7089, ISO 4032, ISO 4762 M6 mit `WGPU_BACKEND=dx12` | **ok** |

**Ereignisanzeige:** Die heutigen Abstürze (0.25.1) stehen nicht im Anwendungsprotokoll (Id 1000),
die letzten Einträge zu `solidcraft-cli.exe` sind vom 2026-10-20 (0.17.0, Pfad noch
`~\inventa\…`). Alle nennen dasselbe Modul:

```
Fehlerhafter Modulname: igvk64.dll, Version: 31.0.101.2145
Ausnahmecode: 0xc0000005
Fehleroffset: 0x000000000064ea82   (einmal 0x0000000000630e71)
Modulpfad: C:\WINDOWS\System32\DriverStore\FileRepository\iigd_dch.inf_amd64_98d08511a5a11871\igvk64.dll
```

`igvk64.dll` ist der Vulkan-Treiber der Intel-Grafik (hier Intel Iris Plus Graphics, Treiber
31.0.101.2145 vom 2026-09-02). Minidumps von damals liegen unter `%LOCALAPPDATA%\CrashDumps`.
Der Offset von #5589 (`0x212c409` in `solidcraft-cli.exe`) passt nicht dazu; ob es derselbe
Fehler ist, bleibt offen.

**Deutung:** `save` rendert offenbar ein Vorschaubild über wgpu, `export` nicht. Vulkan ist auf
Windows das bevorzugte Backend; der Intel-Treiber stürzt bei gekrümmter Geometrie ab (OpenGL über
denselben Treiber ebenfalls), DX12 nicht. Die VM hat keine Intel-GPU und rendert in Software,
deshalb läuft sie. AVX-512 (Vermutung 1) ist damit nicht nötig zur Erklärung; der
Unterschied VM/Surface ist die Grafik.

**Umgehung:** `WGPU_BACKEND=dx12` vor dem Start setzen, z. B. in PowerShell
`$env:WGPU_BACKEND = "dx12"` und dann `& $HOME\mechvane-venv\Scripts\mechvane ui --demo`.

## Prüfung des Fixes b2528c3 auf dem Surface (2026-10-29)

`session_env()` setzt unter Windows `WGPU_BACKEND=dx12`. Getestet mit dem Repo-Stand über
`PYTHONPATH` (venv weiter 0.1.0a4), `WGPU_BACKEND` nicht gesetzt:

| Prüfung | Ergebnis |
|---|---|
| Nachbau Kreis + `doc.save()` | ok |
| `standard_parts.create` ISO 7089, ISO 4032, ISO 4762 M6 | ok |
| `mechvane ui --demo --no-browser`, Aufbau der Beispiele | ok, alle 8 Dateien inkl. Normteile |
| `mechvane ui --demo --no-browser`, Start des Servers | **Fehler**, siehe unten |

Zwei weitere Fehler, unabhängig vom Grafiktreiber:

1. **`/tmp` fest verdrahtet:** `mechvane/ui/server.py:324` legt sein Arbeitsverzeichnis mit
   `tempfile.mkdtemp(prefix="ui1-", dir="/tmp")` an. Unter Windows ist das `\tmp` auf dem
   aktuellen Laufwerk; fehlt `C:\tmp`, bricht der Start mit `FileNotFoundError [WinError 3]` ab.
   Schon in 0.1.0a4. Auf der VM gibt es `C:\tmp` vermutlich, deshalb lief es dort.
2. **Halb gebaute Demo blockiert:** Bricht der erste Aufbau der Beispiele ab (hier durch den
   Absturz), liegen einzelne Dateien schon in `%LOCALAPPDATA%\mechvane\demo`. `demo_folder()` baut
   dann neu, `ws.new` scheitert an der vorhandenen Datei (`FileExistsError`). Wer einmal
   abgestürzt ist, kommt ohne Löschen des Ordners nicht weiter.

Den alten Demo-Ordner auf dem Surface nach `demo.kaputt-2026-10-29` verschoben. App-Fenster und
Anzeige der Beispiele sind wegen Fehler 1 noch ungeprüft.

## Prüfung von b521160 auf dem Surface (2026-10-29)

`WGPU_BACKEND` nicht gesetzt, Repo-Stand über `PYTHONPATH`.

| Prüfung | Ergebnis |
|---|---|
| Server-Start (`/tmp`-Fix) | ok, `Mechvane UI running at http://127.0.0.1:8799/ (demo)` |
| Demo nach Abbruch: `bolted_plates.solidcraft` gelöscht | ok, Ordner neu gebaut, alle 8 Dateien |
| Demo nach Abbruch: nur `top_plate.solidcraft` gelöscht | **nicht erkannt**, Server startet mit fehlendem Teil |
| App-Fenster | öffnet (`chrome.exe --app=http://127.0.0.1:8799/`, eigenes Profil) |
| Startseite „Check“ zeigt die Beispiele | **nein**, siehe unten |
| „Model by hand“ öffnen und speichern | ok: im App-Fenster vom Nutzer geändert und mit Ctrl+S gespeichert, `ISO_4032_M6.solidcraft` neu geschrieben (01:50:22), kein Absturz |

**Startseite leer (nicht Windows-spezifisch):** Im Ordnermodus (`--demo` und jeder Projektordner)
ist beim Start kein Dokument offen. `static/app.js` ruft auf der Startseite aber direkt
`api/version`, `api/mesh`, `api/tree` und `api/findings` ab; alle antworten
`409 {"error": "no document open"}`, die Seite bleibt bei „Loading model tree…“ und meldet
„Connection lost“. `/api/project` liefert die 8 Dokumente, die Startseite fragt es nicht ab, und
die Auswahl „Example“ bleibt leer.

**Vollständigkeit der Demo:** `demo_folder()` prüft nur die drei Einträge aus `DEMOS`. Fehlt ein
Unterteil (z. B. `top_plate`), gilt der Ordner als vollständig. Bei einem echten Absturz fehlt
auch die Baugruppe, deshalb in der Praxis selten.

**„Model by hand“:** Die Seite lädt und öffnet ein Dokument. Im Tab des normalen Chrome (über die
Browser-Erweiterung) hing danach der Renderer, Screenshots liefen zweimal in eine Zeitüberschreitung.
Ob das an der eingebetteten SolidCraft-Web-App (WebGPU auf der Intel-Grafik) liegt oder am
Hintergrund-Tab, ist offen. Im App-Fenster lief es: Der Nutzer hat ein Teil geändert und mit Ctrl+S
gespeichert.

## Prüfung von 70cc436 auf dem Surface (2026-10-29)

`WGPU_BACKEND` nicht gesetzt, Repo-Stand über `PYTHONPATH`, `mechvane ui --demo` im App-Fenster.

| Prüfung | Ergebnis |
|---|---|
| Nur `top_plate.solidcraft` gelöscht, neu gestartet | ok, Demo neu gebaut, alle 8 Dateien |
| Startseite zeigt die Baugruppe | ok, `bolted_plates (assembly)` gewählt, „Check: OK“, 3D-Ansicht (Nutzer) |
| Dokument wechseln | ok, Auswahl mit allen 8 Dokumenten, Modell wechselt (Nutzer) |
| „Model by hand“ und zurück | ok, Dokument bleibt gewählt (Nutzer) |

Damit läuft `mechvane ui --demo` unter Windows auf dem Surface ohne Umgehung.

## Nächste Schritte

- [x] Auf dem Surface: Fehler-Offset aus der Ereignisanzeige und `export` (STEP/3MF) testen.
- [x] Prüfen, ob `export` (STEP/3MF) ebenfalls abstürzt: nein.
- [x] Mechvane: unter Windows `WGPU_BACKEND=dx12` für `solidcraft-cli` setzen, wenn der Nutzer
      nichts anderes vorgibt (`session_env()`, b2528c3, auf dem Surface geprüft).
- [x] `ui/server.py`: `dir="/tmp"` entfernen (Fehler 1), b521160, geprüft.
- [x] `demo_folder()`: halb gebaute Demo neu bauen (Fehler 2), b521160, geprüft.
- [x] Startseite im Ordnermodus: Auswahl aus `/api/project`, erste Baugruppe öffnen (70cc436, geprüft).
- [x] Am Surface im App-Fenster: „Model by hand“, Teil ändern, Ctrl+S: speichert, kein Absturz.
- [ ] Intel-Grafiktreiber auf dem Surface aktualisieren und ohne `WGPU_BACKEND` erneut prüfen.
- [ ] Kommentar an #5589 um den Treiberbefund ergänzen (`igvk64.dll`, DX12 als Umgehung).
- [ ] Bis zur Klärung in der README unter „Alpha“ vermerken, dass Windows auf manchen Rechnern
      beim Speichern runder Teile abstürzt.
