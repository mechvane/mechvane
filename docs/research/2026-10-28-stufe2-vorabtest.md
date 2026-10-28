# Vorab-Test Stufe 2 (ADR 0003, Schritt 0)

- **Datum:** 2026-10-28
- **Autor:** Claude (Steuer-Container, headless Chromium mit SwiftShader, SolidCraft-Web-App 0.21.0)
- **Frage:** Trägt der Entwurf aus [ADR 0003](../adr/0003-point-and-speak.md)? Drei Punkte waren offen:
  Nachladen geänderter Dateien in der App, Auswahl aus der App lesen, ACP mit Claude Code.

## 1. Nachladen in der eingebetteten App

Versuch: Beispiel `bracket` in `model.html` geöffnet, die Datei auf dem Server außerhalb der App
geändert (ein Quader dazu, Zeitleiste 4 → 5), neue Bytes ins OPFS geschrieben.

| Weg | Ergebnis | Dauer |
|---|---|---|
| `doc.open` auf denselben Pfad, ohne Neuladen | `ok`, aber Zeitleiste bleibt alt (4) | 2,8 s |
| iframe neu laden, dann `doc.open` | neue Fassung (5) | 6,9 s |

Grund im Quelltext: Ein schon geöffnetes Design wird nur angewählt, nicht neu gelesen
(`crates/ui-egui/src/documents.rs:284`, „Select an already-open saved design without reloading“).
Einen Befehl zum Schließen oder Neuladen gibt es nicht (`doc.close`, `file.revert`, `doc.reload`:
„unknown command“; Liste der `doc.*`/`file.*`-Befehle in `crates/engine/src/cmd/`).

**Folge für ADR 0003, 2A:** Nach jedem Zug das iframe neu laden. 6,9 s gelten für Software-Rendering
auf 2 Kernen; mit echter GPU deutlich weniger zu erwarten, im Praxistest messen. Eine Datei unter
neuem Namen zu öffnen, scheidet aus (Baugruppen verweisen per relativem Pfad auf ihre Teile).
Möglicher Upstream-Wunsch an SolidCraft: `doc.open` mit `reload: true` (öffentlich, nur mit OK).

Kamera: `request("ui.camera", {})` liefert `distance, fov, pitch, roll, target, up, yaw` und lässt sich
nach dem Neuladen mit denselben Werten setzen.

Nebenbefund: Mit WebGPU über SwiftShader stürzt die App im Headless-Test ab (`createBuffer`, wgpu
panic) und `commands()` hängt; mit WebGL2 (`--enable-unsafe-swiftshader` ohne
`--enable-unsafe-webgpu`) läuft alles. Betrifft nur die Testumgebung.

## 2. Auswahl lesen

`select.set` braucht `{type, body, index, point}` (ohne `point`: „missing field `point`“).
`request("ui.selection", {})` gibt die Auswahl im selben Format zurück, dazu `hover`, `dialog` und
Bemaßungen; `inspect().selection` ebenso:

```json
[{"type": "face", "body": "Bracket", "index": 11, "point": [42.23, 30.35, 8.87]}]
```

`point` ist der angeklickte Punkt. Das passt direkt zu `/api/resolve_selection` in ADR 0003,
Abschnitt 3 (Körper + Index → Mechvane-Name, `point` → `click`).

## 3. ACP mit Claude Code

Adapter `@agentclientprotocol/claude-agent-acp` **0.90.0** (2026-10-13; neueste 0.99.0 ist vom
selben Tag wie der Test und wurde deshalb nicht genommen), lokal im Scratchpad mit
`--ignore-scripts`, Claude Code 2.1.312 über `CLAUDE_CODE_EXECUTABLE`. Prototyp-Client in Python
(JSON-RPC über stdio, ~120 Zeilen).

- `initialize` mit `fs` und `terminal` aus: geht.
- `session/new` mit `mcpServers: [mechvane mcp --workspace <projekt>]`, Arbeitsordner leer, und
  `_meta.claudeCode.options: {tools: [], settingSources: [], strictMcpConfig: true, model: "sonnet"}`:
  Der Agent sieht nur die Mechvane-Werkzeuge.
- Jeder Werkzeugaufruf kommt als `session/request_permission` beim Client an (Name, Parameter).
  Dort kann Mechvane die Regeln aus ADR 0003, Abschnitt 6 durchsetzen, zusätzlich zur Prüfung im
  MCP-Server.
- Auftrag „Fase 1 × 45° an den oberen Wandkanten, speichern, prüfen“: `open_document`,
  `list_commands`, `find`, `measure`, `run` (`solid.chamfer` an vier Kanten bei Z = 48),
  `save_document`, `check_design`; fertig nach rund 19 s, ganzer Zug mit Antwort rund 30 s.
- Gegenprobe: `/etc/hostname` lesen scheiterte (`open_document` lehnt Pfade außerhalb des
  Arbeitsordners ab), `ls` scheiterte (keine Shell, `command` kennt nur SolidCraft-Befehle).

## Ergebnis

Der Entwurf trägt. Änderungen an ADR 0003: Neuladen des iframes ist Pflicht (kein Neuladen ohne),
Rechteprüfung zusätzlich im ACP-Client über `session/request_permission`, Adapter-Version pinnen.
Schritt 1 kann beginnen.
