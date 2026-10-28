# ADR 0003: Point and speak – Agent, Auswahl und Sprache in der Web-UI (Stufe 2)

- Status: **angenommen** (2026-10-28, Nutzer; vorgeschlagen 2026-10-28 von Claude, Review Gemini 4 Argon eingearbeitet)
- Entscheidet: wie der Agent an die Web-UI angebunden wird, wie Auswahl und gesprochener Auftrag zu
  ihm kommen, wie Rückgängig funktioniert und was der Agent ohne Rückfrage darf
- Bezug: ROADMAP Grundsatz 6 (Point and speak), Meilenstein v0.1 Schritt 2, Leitsatz „You and your
  agent on the same model.“, ADR 0001 (SolidCraft-Kern unverändert)

## Kontext

Heute gibt es zwei Wege, an einem Modell zu arbeiten, die nichts voneinander wissen:

- **Von Hand** in der Web-UI: Modus „Prüfen“ (`index.html`, three.js, Befunde, Flächen mit
  Mechvane-Namen) und Modus „Modellieren“ (`model.html`, eingebettete SolidCraft-Web-App, Dokument
  im OPFS des Browsers, Speichern per POST an `/api/file/<name>`, danach neue Prüfung und
  `update_links`).
- **Mit Agent** über den MCP-Server (`mechvane mcp`) in einer eigenen Sitzung, z. B. Claude Code im
  Terminal. Der Agent arbeitet auf den Dateien im Arbeitsordner, in je einer SolidCraft-Sitzung pro
  Dokument.

Grundsatz 6 verlangt: Kante oder Fläche markieren, sagen „da eine Fase 1 × 45°“, und der Agent
setzt das als editierbares Feature im Baum um. Dazu fehlen ein Chat in der UI, die Übergabe der
Auswahl mit stabilen Namen, die Spracheingabe und ein Rückgängig, das Agentenschritte umfasst.

Randbedingungen:

- Die Agenten-Chat-Funktion von SolidCraft ist laut `docs/agent-chat.md` nur in der Desktop-App
  vorhanden, nicht in der Web-App, die Mechvane einbettet. Sie kennt außerdem die Mechvane-Werkzeuge
  (`add_joint`, `update_links`, `check_design`, Normteile) nicht. Ihre Lösungen für Rechte,
  Auswahl und Rückgängig sind aber ein gutes Vorbild und werden unten übernommen.
- Die Logik von Mechvane (Skizzenregel, Lineage-Namen für Gelenke, Prüfungen, Wissenskatalog)
  läuft in Python auf dem Server, nicht im Browser.
- Kein Modellzugang über einen bezahlten API-Key als Standard: Der Nutzer bringt seinen eigenen
  Agenten mit (Claude Code, Codex, Gemini …), wie bei SolidCraft.
- Die Live-Demo (GitHub Pages) hat keinen Server und kann keinen Agenten starten.
- Grundsatz 12 verlangt für v0.1 Offline-Betrieb im App-Fenster.

## Entscheidungen im Einzelnen

### 1. Wo der Agent läuft: der Mechvane-Server startet ihn über ACP

| Option | Für | Gegen |
|---|---|---|
| **A: Mechvane-Server als ACP-Client** (Agent Client Protocol, wie SolidCraft-Desktop): startet den installierten Agenten des Nutzers (z. B. `claude-agent-acp`, `codex-acp`, `agy_acp_server`) und gibt ihm den Mechvane-MCP-Server für den Projektordner mit | eigenes Konto des Nutzers, kein Key, viele Agenten, bekanntes Muster aus SolidCraft | Node-Adapter je Agent muss installiert sein; ACP-Fähigkeiten je Agent unterschiedlich |
| B: Direkt `claude -p --input-format stream-json` | kein Adapter, einfach | nur Claude Code, eigenes Protokoll |
| C: Anthropic-/OpenAI-API mit Key | volle Kontrolle | kostet Geld, Key-Verwaltung, widerspricht „eigener Agent“ |
| D: kein Chat in der UI, Agent bleibt im Terminal, UI zeigt nur an | kein Aufwand | kein Point and speak |

**Vorschlag: A**, für v0.1 nur dieser eine Weg (B erst, wenn A beim Nutzer scheitert). D bleibt
nebenher möglich (MCP im Terminal, die UI lädt die Änderung nach, siehe 2). Dass ACP beim Start
einer Sitzung MCP-Server übergeben kann (`session/new` mit `mcpServers`), steht so in der
Spezifikation; vor dem Umsetzen mit dem Claude-Adapter selbst prüfen. Antigravity spricht ACP
nicht über `agy`, sondern über den eigenen Download `agy_acp_server` (SolidCraft `agent-chat.md`).

### 2. Wo der Agent wirkt: auf den Dateien, Zug um Zug

| Option | Für | Gegen |
|---|---|---|
| **A: Dateibasiert.** Vor dem Auftrag speichert die Seite, der Agent arbeitet über Mechvane-MCP auf der Datei, danach lädt die Seite die neue Fassung in die App | nutzt alle Mechvane-Werkzeuge und Prüfungen unverändert; funktioniert im Modus „Prüfen“, „Modellieren“ und mit dem Agenten im Terminal gleich | Neuladen der App nach jedem Zug; Undo-Verlauf der App geht verloren (ersetzt durch 5) |
| B: Live-Brücke: Befehle des Agenten laufen über den Server an `window.solidcraft.execute` im Browser | kein Neuladen, App-Undo bleibt | Mechvane-Logik müsste Befehle in die Brücke statt in die eigene Sitzung schicken; zweite Wahrheit neben der Datei; schwer testbar |

**Vorschlag: A für v0.1.** B nur, wenn das Neuladen im Praxistest stört. Dafür muss Folgendes
gebaut werden (Review-Befunde 6–10):

- **Speichern vor dem Zug, verlässlich:** `model.html` pausiert ihre 1-s-Schleife über das OPFS,
  löst das Speichern in der App aus, lädt jede geänderte Datei per POST hoch und wartet auf die
  Antwort. Scheitert das (offener Dialog, offene Skizze), startet der Zug nicht, der Chat sagt warum.
- **Sperren:** Ein Flag `agent_busy` im UI-Server weist während des Zuges schreibende Anfragen
  (`POST /api/file/*`, `/api/open/*`, `/api/new`) mit 409 ab; `self.lock` wird nur kurz gehalten,
  damit Stream und Stop jederzeit durchkommen. Die App zeigt „Agent arbeitet …“ und ist gesperrt.
- **Eine Wahrheit, auch im Speicher:** Der MCP-Server prüft vor jedem Zugriff die `mtime` der Datei
  gegen die geladene Sitzung und lädt neu, wenn sie sich geändert hat (wie
  `UIServer.ensure_current`). Am Ende des Zuges speichert der Server alle geänderten Dokumente
  selbst; der Agent muss nicht an `save_document` denken.
- **Nachladen nach dem Zug:** `model.html` holt `/api/files` und `/api/project` neu (der Agent kann
  Dateien anlegen; `UIServer.files()` muss dafür auch Unterbaugruppen liefern), schreibt geänderte
  und neue Dateien ins OPFS, merkt sich vorher die Kamera (`ui.camera`) und stellt sie danach wieder
  her. Erster Test: Sieht `doc.open` geänderte OPFS-Dateien ohne Neuladen des iframes? Die App liest
  das OPFS laut bisherigem Stand nur beim Start; dann ist ein Neuladen des iframes nötig, und dessen
  Dauer entscheidet über 2B.
- **Abbruch und Fehler mitten im Zug:** Ein Zug umfasst oft viele Werkzeugaufrufe. Bei Stop oder
  einem Fehler, nach dem der Agent aufgibt, wird der Stand vor dem Zug automatisch wiederhergestellt
  (Zug ist atomar). Der Chat bietet „Teilergebnis behalten“ an, falls der Nutzer es doch will.

### 3. Auswahl: stabile Mechvane-Namen statt Bildschirmkoordinaten

Die Seite schickt, was die Ansicht liefert, an einen neuen Endpunkt `/api/resolve_selection`:
im Modus „Modellieren“ die Auswahl der App (Fläche oder Kante als Körper + Index + Punkt; Name und
Rückgabe des Abfragebefehls der Web-App vorher über `solidcraft.commands()` prüfen, `model.html`
nutzt bisher nur `select.set`), im Modus „Prüfen“ den Trefferpunkt des Klicks und die `face_id` aus
dem Netz. Das Netz kennt keine B-Rep-Kanten; Kanten und Bohrungen in der Nähe des Klickpunkts sucht
der Server mit `query.find` (`edges`, `holes` mit `near`).

Der Server antwortet mit dem Block, der mit dem Auftrag an den Agenten geht. Feldnamen wie in
`query.py`, zusätzlich der Klickpunkt und das erzeugende Feature:

```json
{"document": "bracket.solidcraft",
 "selection": [{"kind": "face", "name": "F4:csink:base", "type": "plane",
                "normal": [0, 0, 1], "click": [41.9, 30.3, 8.0], "centroid": [40.0, 30.0, 8.0],
                "feature": "CountersinkNearWall"}],
 "said": "da eine Fase 1 mal 45 Grad"}
```

`click` ist der angeklickte Punkt („da“), `centroid` der Flächenschwerpunkt („mittig“).
Dafür bekommt `query.py` eine Suche nach Index und gibt das erzeugende Feature aus (`F<id>` über die
Zeitleiste).

**Baugruppen** (Review-Befund 3): Dort tragen Flächen nur STEP-Namen (`F3:face:0`), weil SolidCraft
verknüpfte Teile als STEP einbettet. Für eine Auswahl auf einer Komponente rechnet der Server den
Punkt mit der inversen Matrix der Occurrence in Bauteilkoordinaten um und löst den Lineage-Namen in
der Bauteildatei auf, wie es `_match_assembly_face` im UI-Server und `links.py` schon tun. Der Block
nennt dann Komponente und Bauteilfläche.

**Mehrere Bezüge** („Gelenk von dieser Fläche auf diese Fläche“): Die Auswahl beim Drücken der
Sprechtaste wird als Chip 1 festgehalten; jeder weitere Klick, solange die Taste gehalten wird,
hängt einen Chip an. Kamera bewegen löscht nichts. Chips lassen sich vor dem Senden entfernen.

### 4. Sprache: Browser-Spracherkennung zuerst, Server-Erkennung für offline

| Option | Für | Gegen |
|---|---|---|
| **A: Web Speech API** (`SpeechRecognition`) | kein Download, sofort, Chrome und Edge | braucht Internet, Chrome verarbeitet die Sprache bei Google (Hinweis und Einschalten durch den Nutzer); fehlt in Firefox und in WebKitGTK; Fachbegriffe |
| B: Whisper lokal (`faster-whisper`) hinter `/api/transcribe` | offline, Fachbegriffe per `initial_prompt` aus dem Glossar | Modell-Download, CPU-Last, Verzögerung |

**Vorschlag: A zuerst, B vor der echten Desktop-App** (Grundsatz 12, Offline). Die Seite fällt
von selbst auf B zurück (Aufnahme per `MediaRecorder`, Upload), wenn `SpeechRecognition` fehlt oder
keine Verbindung besteht. Für beide gilt:

- Drücken und halten (Mikrofon-Knopf, Taste nach der Abgleichliste festlegen) statt Daueraufnahme.
- Der erkannte Text erscheint im Eingabefeld und kann korrigiert werden, bevor er gesendet wird.
  Senden mit Enter oder automatisch nach dem Loslassen (Einstellung).
- Eine Nachbearbeitung im Code normalisiert Maße und Normbezeichnungen aus dem Glossar
  („Em sechs“ → „M6“, „eins mal fünfundvierzig Grad“ → „1 × 45°“, „Phase“ → „Fase“) und erkennt
  englische CAD-Begriffe in deutscher Aussprache („Fillet“, „Chamfer“, „Counterbore“) sowie die
  Namen von Features, Körpern, Komponenten und Parametern des offenen Dokuments. Zahlen und Einheiten
  werden im Code gelesen, nicht vom Modell geraten (Glossar: Recherche
  `2026-10-28-abgleich-baugruppe-glossar.md`).

### 5. Rückgängig: ein Agentenzug ist ein Schritt

Vor jedem Zug legt der Server eine Kopie aller Projektdateien ab, mit einem Verzeichnis der
vorhandenen Dateien, und zwar **außerhalb** der Ordner, die die SolidCraft-Sitzungen beschreiben
dürfen (im Cache, nicht im Projektordner). Nach dem Zug zeigt der Chat eine Zusammenfassung: neue
und geänderte Features und Dateien, Befunde vorher/nachher.

„Rückgängig: Fase 1 × 45° an F4“ stellt den Stand vor dem Zug her: geänderte Dateien zurück, im Zug
neu angelegte Dateien entfernt. Danach schließen UI-Server und MCP-Server ihre offenen Sitzungen
dieser Dateien, und die Seite lädt neu. Wie bei SolidCraft gilt der Knopf nur, solange seitdem
nichts anderes passiert ist: Hat der Nutzer danach von Hand gespeichert, fragt Mechvane nach, bevor
es seine Änderung überschreibt. Vor dem Zurückspielen wird der aktuelle Stand gesichert, damit
„Wiederherstellen“ möglich ist.

### 6. Was der Agent darf, technisch durchgesetzt

- **Eigene Werkzeuge des Agenten aus** (wie SolidCraft): ACP-Handshake ohne Dateisystem und
  Terminal, Start in einem leeren Arbeitsordner (nicht im Projektordner), beim Claude-Adapter Shell-,
  Datei- und Web-Werkzeuge für die Sitzung abschalten, Rechteanfragen für fremde Werkzeuge ablehnen.
  Der Agent ändert das Modell nur über den Mechvane-MCP-Server.
- **Ohne Rückfrage:** Features anlegen und ändern, Normteile und Verschraubungen einsetzen (auch wenn
  das mehrere Projektdateien ändert, der Zug ist ja als Ganzes rückgängig zu machen), Gelenke
  anlegen, prüfen, messen. Alles landet als Feature im Baum und ist editierbar (Grundsatz 6).
- **Mit Rückfrage im Chat:** Features, Körper oder Dateien löschen, SolidCraft-Befehle mit
  Dateinamen (Export, Import, Speichern unter, Öffnen: Parameter `file`, `dir`, `output`, `path`,
  `source`, Regel wie in SolidCraft `agent-chat.md`). Diese Prüfung sitzt in `run` und `command` des
  MCP-Servers, nicht nur im Prompt.
- **Nie:** Dateien außerhalb des Projektordners, den Ordner der Rückgängig-Kopien.
- Optional ein Limit an Änderungen pro Nachricht (wie SolidCraft), Stop wirkt immer.
- Nach jedem Zug prüft der Server neu wie heute nach dem Speichern (`collect_findings`):
  `check_design` bei Bauteilen, `links.check` bei Baugruppen. Neue Befunde erscheinen im Chat.

## Ablauf (Beispiel)

1. Nutzer klickt in „Modellieren“ die obere Kante der Senkung an, hält den Mikrofon-Knopf und sagt
   „da eine Fase 1 mal 45 Grad“.
2. Seite: Auswahl als Chip festgehalten; Text erscheint im Feld, normalisiert zu „da eine Fase
   1 × 45°“; Speichern und Hochladen, bis der Server bestätigt; `/api/resolve_selection`;
   Nachricht an `/api/agent/send`.
3. Server: `agent_busy`, Kopie für Rückgängig, Nachricht mit Auswahlblock an den Agenten (ACP),
   Stream der Antwort an die Seite.
4. Agent: `run` mit `solid.chamfer` an der Kante.
5. Server: geänderte Dokumente speichern, `collect_findings`, `agent_busy` aus.
6. Seite: neue Fassung ins OPFS, App neu laden, Kamera zurück; Chat zeigt „Fase 1 × 45°
   (Chamfer3)“, Befunde und „Rückgängig“.

## Umsetzung in Schritten

0. **Vorab-Test** (1 Tag): ACP mit `claude-agent-acp` und `mcpServers`; App-Neuladen nach
   geänderter OPFS-Datei messen; Abfrage der Auswahl in der Web-App klären. *Erledigt 2026-10-28*
   ([Bericht](../research/2026-10-28-stufe2-vorabtest.md)): `doc.open` liest eine offene Datei nicht
   neu, also iframe neu laden (6,9 s mit Software-Rendering); Auswahl über `ui.selection` als
   `{type, body, index, point}`; ACP mit Adapter 0.90.0, nur Mechvane-Werkzeuge, jeder Aufruf kommt
   als `session/request_permission` beim Client an (dort Rechte zusätzlich prüfen), Zug ~30 s.
1. **Chat ohne Sprache und Auswahl** (1,5–2 Wochen; *fertig 2026-10-28*: Server-Seite und Chat in „Modellieren“, siehe `docs/mechvane-mcp.md`): ACP-Client im Server, Endpunkte
   `/api/agent/*` (Senden, Stream, Stop), Sperren, `mtime`-Abgleich und Speichern im MCP-Server,
   Speichern vor und Nachladen nach dem Zug in „Modellieren“, Chat-Spalte zuerst nur dort,
   Rückgängig und Wiederherstellen pro Zug, Rechteprüfung in `run`/`command`.
2. **Auswahl** (3–5 Tage; *Auflösung fertig 2026-10-28*: `mechvane/ui/selection.py`, `/api/resolve_selection`, Namen im Chat): `/api/resolve_selection` für Bauteile und Baugruppen, Chips,
   Klickpunkt in „Prüfen“.
3. **Sprache** (2–3 Tage; *erste Fassung 2026-10-28*: Mikrofon-Knopf mit Web Speech API, `mechvane/speech.py`, `/api/speech`): Web Speech API, Drücken und halten, Normalisierung aus dem Glossar.
4. **Praxistest mit dem Nutzer** an drei echten Teilen, dann über Live-Brücke (2B), Chat im Modus
   „Prüfen“ und Whisper (4B) entscheiden.

Zusammen 2,5–3 Wochen, wie in der ROADMAP veranschlagt. Live-Demo: kein Agent; dort eine
Aufzeichnung eines Zuges zeigen (Text und Ergebnis).

## Offene Fragen

- Welche Agenten für v0.1 offiziell? Vorschlag: Claude Code (ACP-Adapter), Codex und Antigravity
  (`agy_acp_server`) danach.
- Wie viel Kontext bekommt der Agent pro Zug automatisch (Baum, Befunde, Parameter)? Zu viel kostet
  Tokens, zu wenig führt zu Rückfragen.
- Tastenkürzel für das Mikrofon: hängt an der Abgleichliste (Konflikte mit Inventor- und
  SolidCraft-Kürzeln).
- Datenschutz-Hinweis bei Option 4A: einmalige Zustimmung in der UI.

## Folgen

- Mechvane bekommt einen eigenen ACP-Client und Endpunkte für den Agenten; der MCP-Server bleibt
  die einzige Schnittstelle, über die der Agent das Modell ändert, und setzt die Rechte durch.
- Die Datei bleibt die einzige Wahrheit: Von Hand, mit Agent in der UI und mit Agent im Terminal
  wirken alle auf dieselbe Datei, mit denselben Prüfungen.
- Das Neuladen der App nach jedem Zug ist der bewusst in Kauf genommene Preis für Variante 2A.

## Review

Gemini 4 Argon, 2026-10-28: 17 Befunde (9 hoch). Eingearbeitet: falsche Annahmen zu `query.py`
und Baugruppen-Flächennamen (3), Kanten im Modus „Prüfen“, Prüfungen auf Baugruppen und
Speichern am Zugende (5), Sitzungen im MCP-Server und `mtime` (6), Sperren (7), Speichern vor dem
Zug (8), Nachladen mit Kamera und neuen Dateien (9), Abbruch mitten im Zug (10), eigene Werkzeuge
des Agenten und Rechteprüfung im MCP-Server (11, 12), Offline-Spracherkennung (13), mehrere Bezüge
und „da“ gegen „mittig“ (14), englische Begriffe (15), Rückgängig mit neuen Dateien, Hand-Änderungen
und Wiederherstellen (16), Schätzung (17), `agy_acp_server` (1). Geprüft von Claude an den
Fundstellen in `agent-chat.md`, `mechvane-mcp.md`, `query.py` und `server.py`.
