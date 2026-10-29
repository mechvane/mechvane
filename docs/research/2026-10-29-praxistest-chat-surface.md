# Praxistest Chat und Point and speak auf dem Surface (0.1.0a7)

Stand 2026-10-29, Claude Code auf dem Surface (Session `mechvane-dev-b3`), Auftrag von `mechvane-44`.

## Kurzfassung

Der Agent-Chat läuft unter Windows: Fase anlegen, Rückgängig und Bohrung an einer angeklickten Fläche
funktionieren, ein Zug dauert gut 20 s, Rechteabfragen kamen keine. Nicht getestet ist die echte
Bedienung im Browser (Kante/Fläche in der SolidCraft-App anklicken, Mikrofon): Die Aufträge gingen
über dieselbe Server-API, die die Seite benutzt (`/api/resolve_selection`, `/api/agent/send`,
`/api/agent/undo`), mit Auswahl wie aus der App. Die Spracherkennung selbst blieb ungetestet, nur die
Normalisierung (`mechvane.speech.normalize`).

Drei Befunde:

1. **Agent weiß nichts vom Rückgängig.** Nach Undo der Fase meldet der nächste Zug ungefragt „Achtung,
   die Fase fehlt … Wahrscheinlich ist die Datei inzwischen zurückgesetzt … Soll ich die Fase wieder
   anlegen?“. Die ACP-Sitzung behält den Verlauf, das Undo kommt dort nicht an.
2. **Kleines „m“ wird nicht normalisiert:** „M sechs“ → „M6“, aber „m sechs“ → „m 6“, „m6“ bleibt „m6“,
   „em sechs“ → „em 6“. Ob die Browser-Erkennung groß oder klein liefert, ist offen.
3. **Undo stellt alle Projektdateien wieder her**, nicht nur die geänderte (`restored` listet alle 8
   Demo-Dateien, `changed` nur `bracket.solidcraft`). Inhalt stimmt, aber Zeitstempel aller Dateien
   ändern sich; bei Projekten mit vielen oder großen Dateien unnötig.

Nebenbei: Im ersten Zug schlug der erste `list_commands`-Aufruf fehl (`status: failed`, keine
Meldung im Ereignis), der zweite ging. Ohne Folgen, aber die Fehlermeldung fehlt im Ereignis.

## Umgebung

| | |
|---|---|
| Rechner | Surface Laptop, i7-1065G7, Intel Iris Plus, Windows 11 Insider 26220 |
| Mechvane | 0.1.0a7 aus PyPI, venv `~\mechvane-venv` |
| SolidCraft | 0.25.1 (aus `mechvane setup`, schon vorhanden) |
| ACP-Adapter | `@agentclientprotocol/claude-agent-acp@0.90.0` per `npm install -g`, Node 24.16.0, npm 11.16.0 |
| Agent-Start | `agent_command()` findet `C:\Users\gollu\AppData\Roaming\npm\claude-agent-acp.CMD` |

Server: `mechvane ui --demo --no-browser --port 8790`, Dokument `bracket.solidcraft` über
`POST /api/open/…`. `WGPU_BACKEND` nicht gesetzt.

## Aufträge

### a) Fase 1 × 45° an dieser Kante: ok

Auswahl: Kante `F1:+y|F2:+z` (60 mm, obere Außenkante der Wand), aufgelöst über
`/api/resolve_selection` wie in `model.html`.

- Zug 1: **24 s**, Werkzeuge `list_commands` (fehlgeschlagen), `open_document`, `list_commands`,
  `find`, `run`, `find`, Ende `end_turn`, `changed: ["bracket.solidcraft"]`.
- Baum danach: `BasePlate, Wall, Hole, CountersinkNearWall, Chamfer1`.
- Antwort des Agenten (gekürzt): Fase als Feature **Chamfer1** angelegt, Fasenfläche 60 × 1,41 mm,
  Normale auf 45° geprüft.

### b) Rückgängig: ok

`POST /api/agent/undo`: sofort (< 1 s), `Chamfer1` weg, SHA-256 von `bracket.solidcraft` gleich wie
vor dem Zug (`37d7e173d02fbd15…`). Siehe Befund 3.

### c) Bohrung M6 durchgehend an angeklickter Fläche: ok (ohne echte Spracheingabe)

Text aus `normalize("hier eine Bohrung M sechs durchgehend")` = „hier eine Bohrung M6 durchgehend“,
Auswahl Fläche `F1:+z` (Oberseite Grundplatte) mit Klickpunkt (52, 8, 8).

- Zug 2: **21 s**, Werkzeuge `list_commands`, `run`, `browser`, `find`, Ende `end_turn`.
- Baum danach: `… CountersinkNearWall, Hole1`. Durchgangsbohrung Ø 6,6 mm (ISO 273, „normal“) am
  Klickpunkt, bemaßt auf rechte und vordere Kante. Der Agent fragt nach, ob ein Gewinde gemeint war.
- Danach Undo, Datei wieder wie am Anfang.

Bilder (gerendert mit `solidcraft-cli snapshot`, nicht aus dem Browser):
`docs/galerie/2026-10-29-chat-vorher.png`, `docs/galerie/2026-10-29-chat-bohrung-nachher.png`.

## Weitere Punkte

- **Rechteabfragen:** keine in drei Zügen; alle Aufrufe fielen unter `decide()` als erlaubt. Ein
  Fall mit Abfrage (z. B. Löschen) wurde nicht ausprobiert.
- **Fehlermeldungen:** Die eine fehlgeschlagene Werkzeug-Ausführung zeigt im Ereignis nur
  `status: failed` ohne Text. Sonst keine Fehler.
- **Dauer:** 21–24 s pro Zug mit 4–6 Werkzeugaufrufen, Undo sofort.
- **Nicht geprüft:** Klicken in der eingebetteten SolidCraft-App (`ui.selection`), Mikrofon und
  Browser-Spracherkennung, Aktualisierung der Prüfseite im offenen Fenster. Das braucht den Nutzer
  am Gerät.
