# Testbericht Mechvane auf dem Surface (Windows 11, Chrome 157), 2026-11-06

Stand: `main` 58e7f85 in `C:\Users\gollu\mechvane-venv` (Python 3.14.10), SolidCraft 0.30.1.
Testprojekt: `projekt\` (Beispiele + `platte.solidcraft` 60 × 40 × 8 an [10, 10, 0] + `winkel.step` aus `bracket`).
Klicktests mit Playwright (eigene venv `pwvenv`) im installierten Chrome, sichtbar, 1400 × 860.

## Kurzfassung

- **Blocker (alle Plattformen, nicht Windows-spezifisch):** Im Ordner-Modus (`mechvane ui <ordner>`) öffnet sich
  **kein Dokument**. `app.js:1464` setzt `document.querySelector('label[for="demo-select"]').textContent`, in
  `index.html:37` steht dort aber `<span class="menu-section-label">Examples</span>`, also `null` → TypeError →
  `initFolder` bricht vor `api/open` ab. Sichtbar: Statusleiste „Connection lost“, Baum ewig „Loading model tree…“,
  `/api/version` liefert alle 2 s 409 „no document open“, im File-Menü fehlt die Dokumentliste. Für die übrigen
  Punkte habe ich das nur **im Testbrowser** umgangen (Playwright schreibt beim Ausliefern das `<span>` in
  `<label for="demo-select">` um). An Mechvane selbst habe ich nichts geändert.
- **Alter Prozess-Befund nachgestellt:** Startet man eine 2. Instanz, während schon ein App-Fenster offen ist (gleiches
  `app-profile`), wird ihr Fenster ans laufende Chrome übergeben („handoff“). Dann ist `stops_with_window` falsch,
  `_watch_closing` startet nie, und nach dem Schließen aller Fenster laufen **2 × `pythonw.exe` + `solidcraft-cli.exe`
  weiter** (Server antwortet weiter). Der normale Einzelstart endet dagegen sauber.
- Sonst läuft das meiste: parallele Ansichten, 6 Normansichten, F6 isometrisch, Ursprung mit Augen und Speicherung,
  Kontextmenü „Create Sketch on …“, Skizze mit L/R/C/A/D/Parallel/O/P, Extrudieren mit Profilwahl, STEP-Import, Touch.
- Weitere Befunde: Stutzen (T) entfernt **keine losen Enden**; Registerleiste nach dem Laden abgeschnitten, mit
  Windows-Scrollleiste; schwache bzw. fehlende Hervorhebung beim Überfahren von Flächen; Diagonale auf der Fläche beim
  Extrudieren; einige kosmetische Punkte (unten).

## Ergebnisse

| Punkt | Ergebnis | Befund |
|---|---|---|
| 0 Start Ordner-Modus | **Fehler (Blocker)** | Kein Dokument öffnet sich, „Connection lost“, Baum „Loading…“ (s. o.). Bilder 00, 02, 03 |
| 1 Ansicht | ok | Parallelprojektion (Front/Top/… zeigen reine Rechtecke), Register View: Front, Top, Right, Back, Left, Bottom korrekt, F6 isometrisch. Bilder 11_views_uebersicht, 12. Nebenbefund Registerleiste s. Windows |
| 2 Ursprung | ok, mit Hinweis | Ebenen, Achsen, Mittelpunkt sichtbar. Augen für einzelne Elemente und den ganzen Ursprung wirken, der Zustand bleibt nach Neuladen. Rechtsklick im **Baum** → „Create Sketch on XZ“ / „Hide“. Im **Ansichtsfenster** öffnet Rechtsklick auf eine Ebene kein Menü (rechte Taste = Schwenken), Überfahren hebt dort außerhalb des Skizzenmodus nichts hervor. Bilder 20–27 |
| 3 Skizze anlegen | überwiegend ok, 1 Fehler | S → Leiste „XY/XZ/YZ/Cancel“. Hervorhebung beim Überfahren einer Ursprungsebene vorhanden, aber schwach (31/32). In der Isoansicht überlappen die Ebenen; ich zielte auf XY und bekam XZ. **Flächen** werden beim Überfahren nicht hervorgehoben (60). L mit getippter Länge 40 → Maß 40 + H (35/36). R, C, A ok (37). D auf Kreis → Eingabefeld sofort, Doppelklick auf Maß ändert Ø12 → Ø16 (38–41). Parallel ok (43). **T: Mittelstück zwischen 2 Schnitten wird entfernt, lose Enden (nur 1 Schnitt) bleiben, mehrfach versucht** (45–51). O ok (53). P: Plattenkante projiziert, mit Anker (55). Enter beendet. Skizze auf Plattenoberseite: Flächenkanten werden automatisch projiziert (61) |
| 4 Unbenutzte Skizze | ok | Sketch1 bleibt nach dem Fertigstellen blau sichtbar (56) |
| 5 Extrudieren | ok, 1 kosmetischer Befund | 2 getrennte Kreise auf der Oberseite → „3 in Sketch2“, keins vorgewählt, OK gesperrt (63). Klick auf Kreis → blau + Vorschau, OK frei (66). OK legt Extrude1 an. Doppelklick im Baum → „1 of 3 profiles selected“, Kreis blau (68). Strg+Z nimmt es zurück (70). **Im Extrudieren-Modus erscheint eine helle Diagonale über der Plattenfläche** (Dreiecksnaht des Restprofils?), Bild 64 |
| 6 Import STEP | ok | File → Import STEP… listet `winkel.step`, Import erzeugt `winkel.solidcraft` (BaseFeature) und öffnet es (81/82). Hinweis: Rückgängig/Wiederholen gelten projektweit; in `winkel` steht „Undo: Sketch Sketch2 in platte“ |
| 7 Fenster und Prozesse | **Befund** | Siehe Abschnitt Prozesse. Nach dem Test ist kein `solidcraft-cli.exe`/`pythonw.exe` von mir übrig |
| 8 Stift/Finger | ok (synthetisch) | Niemand hat mitgemacht. Ersatzweise echte Touch-Ereignisse per CDP: 1 Finger dreht, Spreizen zoomt (kräftig, nicht genau um den Fingermittelpunkt), Antippen eines Registers wirkt (98_touch_uebersicht) |

### Weitere Beobachtungen (kosmetisch)

- XZ-Skizze: Blick von +Y, **Welt-Z zeigt nach unten** (was man oben zeichnet, liegt bei −Z, Bild 56), anders als die
  Front-Ansicht (Z oben). Fusion macht es ähnlich, ein Inventor-Nutzer erwartet Z oben.
- Nach Parallel bleibt die Überfahr-Hervorhebung (gelb) an der **alten** Position der gedrehten Linie, bis die Maus
  sich bewegt (43 vs. 44).
- Beim Versatz (O) liegt das Feld „Distance“ über dem Statusleistentext und schneidet ihn ab; es bleibt danach stehen (53).
- Parameterliste: `d6` (Versatz) zeigt „4.927 mm“ mit Einheit im Feld und ist verrutscht, die anderen nur Zahlen (56).
- Das H-Symbol der Rechteckkante liegt genau auf dem kurzen Überstand einer Linie und fängt den Klick ab (46).

## Prozesse (Punkt 7)

| Fall | Ergebnis |
|---|---|
| `--no-browser`, Ende über File → Quit | sauber: Starter, Server-Python, `solidcraft-cli.exe` weg |
| App-Fenster (`python.exe`), Dokument offen, Fenster schließen (WM_CLOSE) | sauber nach ≤ 5 s |
| App-Fenster über `pythonw.exe` (wie Startmenü-Verknüpfung), schließen | sauber nach ≤ 5 s |
| `--no-browser`, nur die **Starter-PID** beendet (`Stop-Process`) | sauber: Kind-Python und `solidcraft-cli.exe` enden mit (venv-Starter) |
| **2 Instanzen**: A = `ui projekt`, dann B = `ui projekt\bracket.solidcraft`, beide mit App-Fenster; alle Fenster schließen | **A endet, B läuft weiter**: `pythonw.exe` 4340 + 35848 und `solidcraft-cli.exe` 17048, Port 8769 antwortet nach 30 s noch. B hatte kein eigenes Chrome-Kind (Handoff). Mit `/api/quit` beendet |

Ursache laut Code (`ui/server.py:1643–1647`, `appwindow.py:96`): `open_window` gibt bei Handoff `"handoff"` zurück,
`stops_with_window` wird falsch, `_watch_closing` läuft nicht. Die seitenbasierte Erkennung (`closing_at`/`last_seen`)
würde auch bei Handoff funktionieren, wird dort aber nicht gestartet. Vorschlag: `_watch_closing` auch bei
`"handoff"` starten.
Nebenbei: Im `finally` von `serve` steht kein `ws.close_all()`. In meinen Tests endete `solidcraft-cli.exe` trotzdem
immer mit, ich habe es nicht weiter verfolgt.

## Windows-Besonderheiten

- **venv-Starter:** `mechvane-venv\Scripts\python(w).exe` startet ein 2. Python, erst das startet `solidcraft-cli.exe`
  (Kette Starter → Python → CLI). Wer per PID beendet, sollte die Starter-PID nehmen, das reißt alles mit.
- **Registerleiste:** Nach jedem Laden ist die Leiste „3D Model / Sketch / Inspect / Assemble / View“ oben
  abgeschnitten, mit einer klassischen Windows-Scrollleiste (horizontal und Pfeile ▲▼). Nach dem ersten Klick auf
  ein Register sieht sie normal aus, bis auf den Scrollpfeil rechts (00, 22 vs. 12).
- Server-Log: abgebrochene Verbindungen beim Neuladen erscheinen als Traceback `ConnectionResetError [WinError 10054]`
  (2×, harmlos, aber laut).
- F6 wird von der Seite abgefangen (Chrome würde sonst den Fokus in die Adressleiste setzen), funktioniert.

## Bilder (`bilder\`)

00_start, 01_reload, 02_filemenu, 03_nach_api_open (Blocker) · 04_platte_offen (mit Umgehung) · 10_view_tab,
11_view_*.png, 11_views_uebersicht, 12_home_f6 · 20–27 Ursprung · 30–55 Skizze 1 (XZ) · 56 fertige Skizze in 3D ·
60–62 Skizze auf Fläche · 63–70 Extrudieren · 80–82 STEP-Import · 90_nach_quit · 95–98 Touch.

## Testmittel (in diesem Ordner)

`pw_host.py` (hält Chrome offen, CDP 9333, optional Umgehung `MV_PATCH_LABEL`), `pw.py` + `snip\` (Schritte),
`pwvenv\`, `chrome-profil\` (Testprofil), Logs `server*.log`, `app*.log`. Kein Server und kein Browser laufen mehr.
