# ADR 0005: Eigene Oberfläche – Mechvane-Arbeitsbereich statt eingebetteter SolidCraft-App

- Status: **angenommen** (2026-10-31, Nutzer; vorgeschlagen am selben Tag von Claude nach Nutzerentscheid „eigene vollständige Oberfläche in v0.1“)
- Entscheidet: Aufbau des Arbeitsbereichs, wie Befehle aus eigenen Dialogen an SolidCraft gehen, Auswahl,
  Vorschau und Rückgängig, Reihenfolge der Stufen, was in v0.1 gehört
- Bezug: ROADMAP Grundsatz 5 (Feature-Baum wie Inventor), 10 (Bedienung wie Inventor, dunkler und schicker),
  12 (Desktop-App), Eintrag „Eigene Oberfläche, SolidCraft nur noch im Hintergrund“ (Nutzer 2026-10-28),
  ADR 0001 (SolidCraft-Kern unverändert), ADR 0003 (Point and speak), Abgleichlisten
  `docs/research/2026-10-27-abgleich-inventor-solidcraft.md` und `2026-10-30-…-flash.md`

## Kontext

Heute hat die Web-UI zwei Seiten: „Check“ (`index.html`, eigene three.js-Ansicht, Modellbaum, Befunde,
Parameter, Messen, Schnitt, Chat) und „Model by hand“ (`model.html`, eingebettete SolidCraft-Web-App).
Modelliert wird von Hand also in der SolidCraft-Oberfläche. Wer die Demo öffnet, sieht beim Modellieren
vor allem SolidCraft. Der Nutzer will möglichst schnell etwas zeigen, das als eigenes Produkt wirkt
(2026-10-31): eine vollständige Mechvane-Oberfläche, SolidCraft rechnet darunter.

Vorhanden und wiederverwendbar:
- three.js-Ansicht mit Netz aus SolidCraft (`/api/mesh`), Flächen-IDs je Dreieck, Kanten aus dem Netz
  (`viewtools.js`: `bodyEdges`, `edgeInfo`), Auswahl von Flächen (Modus „Select“) und Kanten (Messen).
- Modellbaum wie Inventor (`/api/tree`, Skizze unter ihrem Feature), Parameterformular (`/api/params`,
  alles oder nichts), Befunde und Regeln, Chat mit Agent (ADR 0003) samt Snapshot-Rückgängig
  (`mechvane/ui/agent.py`, `Snapshot`).
- Je Dokument eine headless SolidCraft-Sitzung im Server (`Session.cmd`), dieselbe, auf der Agent und
  Prüfung arbeiten. Feature-Befehle nehmen Kanten und Flächen als Punkte (`solid.fillet {edges: [[x,y,z]]}`).
- SolidCraft #8517 (nur Ansicht einbetten, bearbeitbar) ist offen und nicht eingeplant; darauf warten wir nicht.

## Entscheidung

### 1. Ein Arbeitsbereich statt zwei Seiten

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ◆ Mechvane   Datei ▾  │ 3D-Modell │ Skizze │ Prüfen │ Baugruppe │ Ansicht │   ? │
├────────────────────────────────────────────────────────────────────────────────┤
│ [Skizze erstellen] │ [Extrusion] [Drehung] [Bohrung] │ [Rundung] [Fase] │ [Rechteckig]│
│                    │                                 │                  │ [Spiegeln]  │
├──────────────┬──────────────────────────────────────────────┬─────────────────┤
│ Modell ▾     │                                              │ Eigenschaften   │
│ ▾ Bauteil1   │                                              │ ─────────────── │
│   Ursprung   │              3D-Ansicht (three.js)           │ Extrusion1      │
│ ▾ Extrusion1 │                                              │ Abstand  [10 mm]│
│     Skizze1  │                                     ViewCube │ Richtung [ ⇅ ]  │
│ ▸ Bohrung1   │                                              │ Vorgang  [Neu ▾]│
│ ▸ Rundung1   │                                              │ [OK] [Abbrechen]│
│ ─ Bauteilende│                                              │ ─────────────── │
│              │                                              │ Befunde (2)  ⚠  │
│ Parameter    │                                              │ Chat mit Agent 🎤│
├──────────────┴──────────────────────────────────────────────┴─────────────────┤
│ Bereit · Bauteil1.solidcraft · Kern: SolidCraft 0.25.1 · Check: OK            │
└────────────────────────────────────────────────────────────────────────────────┘
```

- **Multifunktionsleiste** mit Inventor-Registern und -Befehlsnamen (Grundsatz 10), Tastenkürzel nach
  der Abgleichliste (E Extrusion, H Bohrung, F Rundung, S Skizze, F6 Startansicht).
- **Links** der Modellbaum mit Bauteilende (Rollback ist Stufe 2+), darunter Parameter.
- **Rechts** ein Bereich für den aktiven Dialog (Eigenschaften), darunter Befunde und Chat als
  aufklappbare Abschnitte. Prüfen ist kein eigener Modus mehr, sondern läuft nach jedem Schritt.
  Das Mikrofon für Point and speak gehört in den Chat-Bereich, neben das Eingabefeld (Nutzer 2026-10-31).
- **Statusleiste** zeigt dauerhaft „Kern: SolidCraft 0.25.1“ (mit Link zu SolidCraft), dazu „Über Mechvane“.
  Grund: Entscheidung des Nutzers 2026-10-28, SolidCraft bleibt in der App, der README und allen
  öffentlichen Texten ausdrücklich genannt, auch wenn man seine Oberfläche nicht mehr sieht.
- Dunkles Farbschema als Standard, ruhig und modern (Grundsatz 10).
- `index.html` wird der Arbeitsbereich; `model.html` bleibt als **Expertenmodus** („In SolidCraft öffnen“)
  im Menü Datei erreichbar, für alles, was es in Mechvane noch nicht gibt.

### 2. Befehle über den Server, nicht über die eingebettete App

Neuer Endpunkt `POST /api/feature {command, params, preview}`: führt einen SolidCraft-Befehl in der
Sitzung des offenen Dokuments aus (dieselbe wie Agent und Prüfung), speichert, gibt Netz, Baum und
Befunde zurück. Eine Liste erlaubter Befehle (Whitelist) begrenzt, was die UI senden darf.
- **Vorschau:** `preview: true` führt den Befehl aus, liefert das Netz und macht ihn gleich wieder
  rückgängig (`undo` der Sitzung), ohne zu speichern. Kein Live-Ziehen in Stufe 1/2: Vorschau beim
  Ändern eines Werts mit kurzer Verzögerung (~300 ms).
- **Rückgängig/Wiederholen:** derselbe Verlauf wie für Agenten-Züge (`Snapshot` je Schritt), damit
  Hand- und Agentenschritte in einer Liste stehen (Grundsatz 6: gleiches Modell für Mensch und Agent).
- **Feature bearbeiten:** Doppelklick im Baum öffnet denselben Dialog mit den Werten aus
  `timeline.inspect`, OK schickt `timeline.edit` bzw. den passenden Bearbeiten-Befehl.
- **Live-Demo** (ohne Server): dieselbe Schnittstelle in JS (`kernel.execute`), dort an die versteckt
  eingebettete Web-App (`app.execute`), wie der Pyodide-Prototyp #35 für die Prüfung. Die UI kennt nur
  `kernel`, nicht den Weg dahinter.

### 3. Auswahl in der eigenen Ansicht

Flächen, Kanten und Punkte werden in der three.js-Ansicht gewählt (Hover-Hervorhebung, Klick, Strg
für mehrere, Filter je Dialog: „nur Kanten“ bei Rundung/Fase, „Fläche oder Ebene“ bei Skizze). Die
Auswahl geht als Punkte auf Kante/Fläche an SolidCraft (wie die Befehle sie erwarten) und zusätzlich
mit Mechvane-Namen an den Agenten (ADR 0003). Fangradius je Eingabegerät wie beim Messen.

### 4. Stufen

| Stufe | Inhalt | Ergebnis zum Zeigen |
|---|---|---|
| 1 Arbeitsbereich | Layout oben, Multifunktionsleiste (Knöpfe ohne Funktion ausgegraut), Baum, Eigenschaften, Statusleiste, Prüfen/Chat rechts, Expertenmodus | Mechvane sieht wie ein eigenes CAD aus |
| 2 Feature-Dialoge | `/api/feature` mit Vorschau und Rückgängig; Extrusion und Drehung (auf bestehender Skizze), Bohrung (mit Gewinde/Senkung, Normtabellen von Mechvane), Rundung, Fase, Rechteckig/Kreisförmig Muster, Spiegeln, Parameter; Feature bearbeiten und löschen | Ein Teil ohne SolidCraft-Oberfläche weiterbauen |
| 3 Skizzierer | Skizze auf Ebene/Fläche, Linie, Rechteck, Kreis, Bogen, Bemaßung (mit Parametern), Abhängigkeiten horizontal/vertikal/koinzident/tangential, Profilerkennung | Ein Teil von null an in Mechvane |
| danach | Baugruppe (Platzieren, Abhängigkeiten über `add_joint`), Bauteilende ziehen, Kontextmenüs, Mini-Werkzeugleiste | |

v0.1 enthält Stufe 1 und 2; Stufe 3 so weit wie möglich, sonst direkt nach v0.1. Bis dahin öffnet
„Skizze erstellen“ die Skizze im Expertenmodus.

### 5. Arbeitsteilung

Claude: dieses ADR, Schnittstellen (`/api/feature`, `kernel`), Prüfung und Praxistest. Argon: große
UI-Pakete nach festem Auftrag (Layout, Dialoge), je mit Tests (`tests/mechvane/check.py`,
`tools/ui_smoke.py`, Node-Tests für JS). Flash: Begriffe, Symbole, Tastenkürzel aus den Abgleichlisten.

## Folgen

- Positiv: Mechvane wirkt als eigenes Produkt; Hand und Agent arbeiten auf derselben Sitzung und
  demselben Verlauf; die Demo kann (mit #35) dasselbe zeigen.
- Negativ: v0.1 wird größer, Ende Dezember wird knapp; Point and speak auf Geräten wartet etwas.
  Ohne Live-Ziehen fühlt sich die Vorschau langsamer an als in Inventor (Ausgleich: schnelle
  Netzübertragung, nur geänderte Körper).
- Risiko: Befehle, deren Parameter in SolidCraft anders heißen als in Inventor; Abhilfe: Abgleichliste,
  Übersetzung in den Dialogen, nicht im Kern.

## Offen (vor Stufe 2 klären)

1. Wie schnell ist ein Zyklus Befehl → Netz → Anzeige für ein typisches Teil (Ziel < 0,5 s)? Messen,
   bevor die Dialoge gebaut werden. *Gemessen 2026-11-02 (Winkel, Rundung):* Befehl 23 ms, Netz 40–80 ms,
   Zurücknehmen 1 ms, also ~65 ms je Vorschau ohne die 300 ms Verzögerung; nur der erste Befehl einer
   Sitzung braucht ~1 s (Kern wärmt auf). Speichern 0,1 s, Befunde 0,2 s. Kein Teil-Netz nötig.
2. Kann `timeline.edit` alle Feature-Parameter ändern, oder muss Bearbeiten löschen und neu anlegen?
   *Geklärt 2026-11-02:* `timeline.edit {feature, set}` ändert alle Felder der Definition aus `timeline.inspect`,
   auch die Kanten; ein Wert, der nicht passt, wirft einen Fehler und ändert nichts. Bearbeiten löscht also nicht.

**Umgesetzt 2026-11-02 (Stufe 2, erster Schnitt):** `POST /api/feature {command, params, preview}` mit Liste
erlaubter Befehle (`FEATURE_COMMANDS` in `ui/server.py`), Ausführen über `modeling.run_commands` (derselbe Weg
wie das MCP-Werkzeug `run`: alles oder nichts, Skizzenregel, Zustandsbericht, erklärte Fehler). Vorschau:
`edit.checkpoint` → Befehl → Netz → `edit.restore_checkpoint` (Achtung: `forget: true` allein geht *nicht*
zurück, es verwirft nur den Checkpoint). Handschritte (Dialoge, Parameterformular) laufen über
`AgentTurns.hand_step` in dieselbe Rückgängig-Liste wie die Agentenzüge, der Agent erfährt davon mit der
nächsten Nachricht; ein neuer Schritt nach einem Rückgängig verwirft das Wiederholen. Rückgängig/Wiederholen in
der Titelleiste und mit Strg+Z/Strg+Y. Kantenwahl in der Ansicht (`viewtools.startEdgePick`): Punkte exakt auf
der Kante (Gerade projiziert, Kreis auf den wahren Radius, nicht die Sehne); SolidCraft folgt tangentialen
Kanten selbst, ein Punkt rundet die ganze Bohrungskante. Dialoge Rundung und Fase (`features.js`).
Bearbeiten wie Inventor: Doppelklick im Modellbaum, `GET /api/feature?name=` liefert die Werte und das Netz vor dem
Feature (`timeline.roll_to` im Checkpoint), dort sind die verbrauchten Kanten wieder wählbar; OK schickt
`timeline.edit` (Liste `EDITABLE`), ein Bearbeiten, nach dem ein Feature fehlschlägt, wird zurückgenommen.
Löschen über Rechtsklick oder Entf (`POST /api/feature/delete`, wie `delete_feature` des Agenten mit der eigenen
Skizze); fehlschlagende spätere Features meldet die Statusleiste, Strg+Z holt alles zurück.
Bohrung: Fläche anklicken (Punkt auf 0,1 mm gerundet und in der Ebene gehalten, Richtung gegen die Normale der
angeklickten Seite), Maße aus `GET /api/hole_sizes` (ISO 273, DIN 336, DIN 974-1, DIN 74-F). Angelegt wird mit
expliziten Durchmessern (`solid.hole` braucht Senkungsmaße), bearbeitet in der Form der Definition (`hole: {type, …}`,
`null` entfernt Tiefe oder Gewinde). Beim Öffnen erkennt der Dialog Durchgangslöcher über die Tabelle wieder.
Muster und Spiegeln: Features im Modellbaum anklicken (`pickFeature`), Richtung/Achse aus X/Y/Z oder einer angeklickten
Kante (Kreis: ihre Achse, beim Anlegen `{edge: Punkt}`, beim Bearbeiten `axis`+`origin`+`axis_ref`), Ebene aus
XY/XZ/YZ oder einer angeklickten Fläche (beim Bearbeiten `custom` mit `x_dir`/`y_dir`). `timeline.edit` will Anzahl
und Abstand eines Musters als Text. Muster rechnen in SolidCraft 2–7 s (Boolean retry bei koplanaren Werkzeugen),
gleiche Werte kommen aus dem Cache; der Dialog zeigt „Computing preview…“ und schickt nie mehr als eine Vorschau
gleichzeitig (nur den neuesten Stand nach).
Extrusion und Drehung: Skizze aus `GET /api/sketches` (mit Nutzern, Vorschlag: neueste unbenutzte), Operation
ausdrücklich (auf einer Flächenskizze wäre SolidCraft-Standard ein neuer Körper, Inventor fügt an; „Cut“ schlägt
Richtung 2 vor). Anlegen mit `operation: new`, Definition und Bearbeiten mit `new_body`; `extent.through_all`
wird mit `false` ausgeschaltet (nicht `null`), die Skizze geht beim Bearbeiten als ID. Drehachse X/Y/Z
(`{type: world, axis}`) oder angeklickte Kante.
Live-Demo (`demo_kernel.js`): beantwortet dieselben `api/*`-Anfragen wie der Server im Browser, über die versteckte
Web-App (startet beim ersten Dialog, ~11 s mit Download). Netz: `file.export` 3mf-tagged nach `/opfs/`, die Datei ist
erst nach ~0,5 s vollständig (auf die gemeldete Byte-Zahl warten), Zip und XML im Browser gelesen. Baum aus
`document.inspect` und `timeline.inspect`, Prüfung per Pyodide. Rückgängig über `edit.undo`/`edit.redo` (jeder
Handschritt ist dort genau ein Befehl; Checkpoints taugen nicht: Rückspringen verwirft spätere). Löschen nimmt in der
Demo nur das Feature, nicht seine Skizze.
Skizzierer, erster Schnitt (Stufe 3): `mechvane.sketch {plane, shapes}` führt `sketch.create`, je Form Rechteck oder Kreis
(`connect: false`, sonst setzt SolidCraft am Ursprung eine Koinzidenz und die Lagebemaßung wäre doppelt) und
Bemaßungen (Länge, Durchmesser, `distance_x/y` zum `origin`) Schritt für Schritt aus, weil die IDs aus den Antworten
kommen; alles oder nichts über einen Checkpoint. `GET /api/sketch_plane` liefert den Rahmen der Ebene (Skizze im
Checkpoint anlegen, `sketch.inspect`, zurück); der Dialog zeichnet darauf selbst und klickt per Strahl gegen die Ebene
(`viewtools.startPlanePick`). In der Demo ist die Skizze mehrere App-Schritte: der Rückgängig-Verlauf wird dort geleert.
3. Schriften und Symbole: eigene Icons (SVG) im Inventor-Stil, ohne Autodesk-Grafiken (Marken, #33).

## Nachtrag 2026-11-02: Skizzierumgebung wie Inventor und Fusion (Nutzer)

Der erste Skizzierer (ein Dialog, der Ebene und Formen zusammen abfragt und gleich zur Extrusion springt) passt nicht:
Skizze **anlegen** und Skizze **mit Geometrie füllen** sind in Inventor und Fusion getrennte Vorgänge. Neuer Ablauf:

1. **Skizze erstellen** (S, Register 3D-Modell): Ebene XY/XZ/YZ oder ebene Fläche anklicken, sonst nichts. Mechvane
   legt die Skizze an und **betritt die Skizzierumgebung**: Register „Skizze“ wird aktiv, Ansicht dreht auf die Ebene
   („Look At“), der Rest des Modells tritt zurück, im Browser ist die Skizze als aktiv markiert, die Statusleiste zeigt
   „Sketch1 · 4 Freiheitsgrade“ bzw. „voll bestimmt“.
2. **Zeichnen mit eigenen Werkzeugen** im Register „Skizze“: Linie (L), Rechteck (zwei Punkte, Mittelpunkt), Kreis (C),
   Bogen, Punkt; jedes Werkzeug bleibt aktiv, bis Esc oder ein anderes gewählt wird. Klicks auf der Ebene mit
   Gummiband-Vorschau, Eingabefelder am Cursor (Länge/Winkel bzw. Durchmesser, Tab wechselt, Enter setzt; wie die
   Dynamic Input in Inventor/Fusion). Fangen: End- und Mittelpunkte, Ursprung, horizontal/vertikal; daraus entstehen
   Abhängigkeiten automatisch (SolidCraft `connect`, `sketch.constraint.*`).
3. **Bemaßen** (D) als eigenes Werkzeug: Geometrie anklicken, Maß platzieren, Wert eingeben (auch `name = Ausdruck`
   für einen Parameter). Abhängigkeiten als Werkzeuge (horizontal, vertikal, parallel, senkrecht, tangential,
   koinzident, gleich, fest). Voll bestimmte Geometrie wird anders gefärbt; Konflikte rot (Constraint-Manager-Idee).
4. **Skizze fertig stellen** (Knopf rechts im Register, Rechtsklick, Enter ohne Werkzeug): zurück ins Register
   3D-Modell, vorherige Ansicht. **Keine** automatische Extrusion; Extrudieren ist ein eigener Schritt und nimmt die
   neueste unbenutzte Skizze vor (Inventor wählt das Profil vor, wenn es nur eines gibt).
5. **Skizze bearbeiten**: Doppelklick auf die Skizze im Browser betritt die Umgebung erneut (Inventor: „Skizze
   bearbeiten“), danach rechnen die Features neu.

Umsetzung:
- Server: Skizzensitzung auf der Dokument-Sitzung: `POST /api/sketch/begin {plane|face|edit}`, `POST /api/sketch/cmd
  {command, params}` (nur `sketch.*`), `GET /api/sketch/state` (`sketch.inspect`: Punkte, Kurven, Bemaßungen,
  Abhängigkeiten, Freiheitsgrade, Profile), `POST /api/sketch/finish`, `POST /api/sketch/cancel`. Die ganze Sitzung
  ist **ein** Schritt im gemeinsamen Rückgängig (Snapshot bei begin, Eintrag bei finish); innerhalb der Skizze
  Rückgängig über `edit.undo`. Der Agent ist währenddessen gesperrt (wie bei einem Handschritt).
- Ansicht: Skizzengeometrie aus `sketch/state` auf dem Ebenenrahmen gezeichnet (Linien, Bögen, Punkte, Maßtexte als
  HTML-Überlagerung), Werkzeug-Zustandsmaschine im Browser (`sketcher.js`), Klick auf der Ebene per
  `viewtools.startPlanePick` (gibt es schon), Fangen im Browser aus dem Zustand.
- Demo: derselbe Weg über `demo_kernel.js`.
- Der Dialog `mechvane.sketch` (Rechteck/Kreis voll bemaßt) entfällt als Bedienweg; Rechteck und Kreis werden Werkzeuge.

Reihenfolge: (a) Umgebung betreten/verlassen, Linie, Rechteck, Kreis mit Fangen und Eingabefeldern; (b) Bemaßen und
Freiheitsgrade; (c) Abhängigkeiten, Bogen, Skizze bearbeiten; (d) Stutzen, Versatz, Projizieren, Konfliktanzeige.

*Stand 2026-11-05:* Server-Teil von (a) fertig: `mechvane/ui/sketch_session.py` mit `POST /api/sketch/begin {plane|edit}`,
`/cmd {command, params}` (nur `sketch.*` außer create/edit/finish), `/undo` (ein Befehl zurück, Sicherungspunkt je
Befehl), `/finish`, `/cancel`, `GET /api/sketch/state`. Die Sitzung ist ein Handschritt über mehrere Anfragen
(`AgentSession.begin_hand`/`end_hand`), der Agent und andere Dialoge sind solange gesperrt. Test
`sketch_session_checks`. Offen für (a): `sketcher.js` (Register Skizze, Look At, Werkzeuge, Gummiband, Fangen,
Eingabefelder am Cursor).

*Stand 2026-11-06:* Schritt (a) fertig: `mechvane/ui/static/sketcher.js` (Fangradien 8/7 px wie SolidCraft, Recherche #53),
Eingabefelder am Cursor über `sketch.draw.dimensioned` (Rollen length/angle, width/height, diameter), Mittelpunkt-Fang
hält per `sketch.constraint.midpoint`. Noch nicht in der Live-Demo (braucht `demo_kernel.js`).
Schritt (b) fertig: Bemaßen (D) über `sketch.dimension` (`type: length` für eine Linie, sonst `auto` mit `text_at`),
Ändern per `parameters.change` (in der Skizzensitzung zusätzlich erlaubt), `name = Ausdruck` beim Setzen (ein Schritt
zurück, dann neu mit Wert). Das erste Längenmaß skaliert die Skizze (SolidCraft `scale_sketch`, wie Inventor).
