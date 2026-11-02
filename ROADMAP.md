# Roadmap Mechvane

Stand 2026-10-19. Grundlage: [Gemini-Deep-Research](docs/research/2026-10-19-inventor-funktionsumfang-gemini.md)
(Teil A: Inventor-Funktionsumfang mit Einstufung KERN/HÄUFIG/NISCHE, Teil C:
Architektur, MVP, Risiken). Zeitangaben sind grobe Größenordnungen für ein
Freizeitprojekt mit KI-Unterstützung, keine Zusagen.

## Grundsätze

1. **Keinen eigenen B-Rep-Kernel schreiben.** Fillets, Booleans und
   Flächenschnitte kosten Jahrzehnte. Kernel wird eingebunden (SolidCraft/
   truck/SolidCore oder OCCT), nie selbst entwickelt.
2. **Topologisches Naming und Solver-Stabilität von Anfang an**, nicht
   nachträglich. Bricht eine Referenz, gibt es eine klare Fehlermeldung
   statt stillem Raten.
3. **Agenten-Schnittstelle zuerst.** Jede Funktion ist über MCP nutzbar, bevor
   sie eine GUI bekommt. Agenten bekommen semantische Abfragen („alle ebenen
   Flächen mit Normale +Z“), Batch mit Rollback, Messwerte und Snapshots.
4. **Modular.** Kern = Dokument, Parameter, Skizze, Basis-Features,
   Baugruppen, STEP/STL/3MF. Alles andere als Plugin, nur bei Bedarf geladen.
5. **Feature-Baum wie Inventor, keine Fusion-Timeline** (Nutzerwunsch
   2026-10-19, sehr wichtig, **im Datenmodell, nicht nur optisch**):
   - Skizzen gehören dem Feature, das sie verbraucht (im Baum darunter,
     wandern beim Umsortieren mit, Löschen fragt nach der Skizze).
   - Jedes Bauteil hat seinen eigenen Verlauf mit eigenem
     Bauteilende-Marker, keine gemeinsame Zeitleiste über alle Komponenten.
   - **Bauteile und Baugruppen sind getrennte Dateien** wie bei Inventor
     (Entscheidung des Nutzers 2026-10-19): Bauteildatei mit eigenem
     Feature-Baum, Baugruppendatei verweist auf Bauteile und hält die
     Abhängigkeiten. Bearbeiten an Ort und Stelle aus der Baugruppe heraus.
   - **Abhängigkeiten (Constraints/Gelenke) hängen an den Bauteilen**, die sie
     verbinden (unter jeder beteiligten Komponente sichtbar), nicht in einem
     eigenen Ordner „Joints“ wie bei Fusion (Nutzerwunsch 2026-10-19).
   - Vertikaler Modellbrowser als Hauptbedienung, keine horizontale
     Zeitleiste am unteren Rand.
6. **Point and speak** (Nutzerwunsch 2026-10-20, sehr wichtig): Der
   Claude-Agent sitzt in der Oberfläche, und man arbeitet interaktiv mit ihm.
   Kante markieren und sagen „da eine Fase 1 × 45°“, Fläche markieren und
   sagen „mittig eine Gewindebohrung M6“. Eingabe per Sprache. Der Agent
   bekommt die Auswahl mit stabilen Flächennamen und setzt sie in Features
   um, die im Baum stehen und editierbar bleiben. Ausgangspunkt: SolidCraft
   hat ein Agent-Chat-Panel (`docs/agent-chat.md`, Claude Code als Agent,
   nur Desktop). Ob es die Auswahl mitgibt, ist offen, Sprache fehlt.
7. **Möglichst viele Dateiformate importieren** (Nutzerwunsch 2026-10-20):
   alle gängigen CAD-Systeme. SolidCraft liest schon STEP, IGES, FreeCAD
   (`.FCStd`), Rhino (`.3dm`, über cadmpeg), 3MF, STL, OBJ und glTF,
   CADCraft dazu DXF/DWG (2D). Zu prüfen: Parasolid (`.x_t`), ACIS
   (`.sat`), JT, Inventor (`.ipt`/`.iam`), SolidWorks, Fusion (`.f3d`),
   Creo, NX, CATIA. Native Formate meist nur über Fremdbibliotheken oder
   Lizenzen, Lizenzregel von SolidCraft beachten.
   **Seit 2026-10-31 (Nutzer): Umstieg ohne Verlust.** Wer viele eigene Entwicklungen hat, steigt nur um,
   wenn sie editierbar mitkommen. Ein Import nur als Geometrie gilt nicht als fertig. Pflicht sind
   Feature-Verlauf, Skizzen mit Abhängigkeiten, Parameter mit Ausdrücken, Baugruppen-Abhängigkeiten und
   Eigenschaften. Fehlt in SolidCraft ein Feature-Typ, baut Mechvane ihn (eigenes Feature oder Upstream-Beitrag).
   Bis dahin bleibt das Feature als Platzhalter im Verlauf, mit allen Originaldaten und dem Ergebnis-Körper,
   nichts wird verworfen. Der Import endet mit einem Bericht je Feature (übernommen, Platzhalter, Abweichung).
8. **Renderanbindung an Blender** (Nutzerwunsch 2026-10-20): Bauteil oder
   Baugruppe mit Materialien und Kamera an Blender übergeben und
   fotorealistisch rendern (Cycles), ohne Export per Hand. SolidCraft hat
   eigene Render-Bausteine (`docs/render-*.md`), aber keine Blender-Anbindung.
   Vorhanden im Homelab: Blender headless per Docker auf dem Apps-LXC mit der
   RTX 2070 (`blender-render.sh`, Skill `homeserver-ops`) und Blender-MCP
   auf win-cad. Weg vermutlich: glTF- oder USD-Export plus Szenen-Skript,
   Rendern als Hintergrundjob, Bild zurück in Mechvane.
10. **Bedienung am Ende möglichst nah an Inventor** (Nutzerwunsch 2026-10-26, Endziel der UI):
   Wer Inventor kennt, soll ohne Umlernen arbeiten können. Gemeint sind Aufbau und Begriffe der
   Oberfläche, nicht nur der Feature-Baum aus Grundsatz 5. **Optisch aber dunkler und schicker
   als Inventor** (Nutzer 2026-10-26): dunkles Farbschema als Standard, moderne, ruhige
   Gestaltung; vertraut ist die Bedienung, nicht das Aussehen.
   - Multifunktionsleiste mit Inventor-Registern und -Befehlsnamen (Skizze erstellen, Extrusion,
     Drehung, Bohrung, Abhängigkeit, Platzieren), Inventor-Tastenkürzel (z. B. E Extrusion,
     D Bemaßung, F6 Startansicht), Kontextmenüs und Mini-Werkzeugleiste.
   - Modellbrowser links, ViewCube, Mausbedienung und Navigationsleiste wie Inventor.
   - Feature- und Abhängigkeitsdialoge mit den Inventor-Optionen und deren Reihenfolge, Bauteil-
     und Baugruppenumgebung getrennt wie bei Inventor (Bauteil-, Baugruppen-, Skizzenumgebung).
   - Weg: Heute ist die SolidCraft-Web-App eingebettet (1b), deren Oberfläche eher an Fusion
     erinnert. Schritte dahin: zuerst Einstellungen und Plugin-Oberflächen von SolidCraft nutzen
     (#1221, deklarative „surfaces“), dann eigene Mechvane-Oberfläche über dem SolidCraft-Kern, wo
     das nicht reicht (ADR 0001: Kern unverändert). Vor dem Umsetzen eine Abgleichliste
     Inventor ↔ SolidCraft ↔ Mechvane anlegen (Register, Befehle, Kürzel, Browser-Einträge), damit
     jede UI-Stufe ein Stück näher rückt.
   - Was Nutzer an Fusion besser finden: [Entscheidungsliste](docs/research/2026-10-26-fusion-vs-inventor-liste.md)
     (25 Punkte plus Gegenprobe, je Punkt später „wie Fusion“ oder „wie Inventor“ entscheiden).
11. **Testen an echten Teilen** aus dem eigenen Alltag (Druckteile für den
   Ultimaker, Vorrichtungen, Blechteile), Ergebnisse gegen Fusion/FreeCAD
   vergleichen (Volumen, Schwerpunkt, Bounding-Box).
12. **Echte Desktop-App für Windows und Linux** (Nutzerwunsch 2026-10-26, Ziel): Mechvane als
   eigenes Programm mit Installer, Startmenü-Eintrag und eigenem Fenster, offline nutzbar. Die
   Browser-Variante (lokaler Server, Live-Demo) bleibt daneben bestehen. Weg in zwei Schritten:
   für v0.1 App-Fenster und Offline-Betrieb über den Browser, danach die echte Desktop-App. Die
   Wahl der Hülle (Tauri, Electron, pywebview, Qt) hängt am Prüfpunkt Sprache und daran, ob die
   eingebettete SolidCraft-Web-App im jeweiligen Webview läuft (WebGL/WebGPU, unter Linux ist
   Tauris WebKitGTK die Schwachstelle).

## Phase 0: Erkunden und entscheiden (ca. 2–4 Wochen)

Ziel: begründete Entscheidung, worauf Mechvane aufbaut.

- [x] Build-Umgebung klären: kein eigener Build nötig, fertige
      Release-Binaries (v0.16.2) laufen headless auf dem Steuer-Container,
      siehe [Phase-0-Bericht](docs/research/2026-10-phase0-solidcraft.md).
- [x] SolidCraft praktisch testen: Desktop/Web-App, `solidcraft-cli mcp` an
      Claude Code anbinden, 3–5 eigene Referenzteile per Agent konstruieren.
      *Stand 2026-10-19:* MCP angebunden (`.mcp.json`), 4 Referenzteile
      (Flansch, Druckgehäuse, Blechwinkel, Scharnier) gebaut und vermessen.
      Eingebundene `mcp__solidcraft__*`-Tools nach Neustart geprüft
      (Flansch, Abweichung 6,6e-6). *Web-App seit 2026-10-25 in Mechvane eingebettet und täglich im Einsatz
      (1b), damit erledigt (2026-10-31).*
- [x] Prüfen: Wie gut ist der MCP-Server für Agenten (Fehlermeldungen,
      Topologie-Abfragen, Snapshots)? Ergebnis im
      [Phase-0-Bericht](docs/research/2026-10-phase0-solidcraft.md).
- [x] Prüfen: Wie weit sind Zeichnungen (`docs/drawing-foundations.md`),
      Baugruppen, Blech, Plugins (#1221)? Baugruppen und Blech tragen
      (Referenzteile). Zeichnungen: M11 zurückgestellt, nur Ansichts-DXF.
      Plugins: nur Entwurf, kein Code, keine eigene Plugin-UI vorgesehen.
      Siehe [Bericht](docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
- [x] Prüfen: Lässt sich in SolidCraft ein Inventor-artiger Feature-Baum
      statt der Fusion-Timeline umsetzen (Grundsatz 5)? Was zeigt der
      vorhandene Browser, lässt sich die Timeline-Leiste ersetzen, geht das
      als Plugin/UI-Modul oder nur per Fork? Fließt direkt in ADR 0001 ein.
      *Stand 2026-10-19 (aus dem Code):* Die Einstellung `timeline_left`
      zeigt den Verlauf senkrecht über dem Browser, mit Ordnern und
      Rollback-Balken, an dem neue Features eingefügt werden. Optisch kommt
      das nahe, es fehlen Skizzen unter ihrem Feature und ein gemeinsamer
      Baum. *Abgeschlossen 2026-10-31:* Mechvane zeigt den Baum selbst wie Inventor (Skizze unter ihrem
      Feature, Prüfseite). Einen echten Baum in der SolidCraft-App nur über Oberflächen-Erweiterungen (#1221)
      oder Upstream, gehört zu „Eigene Oberfläche“ (Phase 1, nach v0.1).
      *Nachtrag 2026-10-19:* Der Nutzer will den Baum auch im Datenmodell.
      Dann reicht UI nicht: SolidCraft hat **eine** Feature-Liste für das
      ganze Design (Komponenten nur als Feld `component`), Skizzen sind
      eigene Einträge, auf die Features per Id zeigen, und Gelenke liegen in
      `assembly.joints` mit eigenem Browser-Ordner „Joints“. Nötig wären
      Änderungen im Kern-Crate `doc` (Format, Eval). Das spricht eher für
      Fork oder eine eigene Dokumentschicht als für reine Upstream-Beiträge.
      *Nachtrag 2 (Versuche):* Eine Datei je Bauteil liefert den eigenen
      Verlauf von selbst, Skizzenbesitz geht als Befehlsregel ohne
      Formatänderung. Lücke: Flächennamen gehen über Verknüpfungen verloren,
      ein Gelenk sprang still auf die falsche Bohrung
      ([Dokumentmodell](docs/research/2026-10-19-dokumentmodell.md)).
      [Bericht](docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
- [x] Lizenz- und Governance-Frage: Wie offen ist das Projekt für Beiträge,
      wie stabil ist die API (Version 0.x, hohe Änderungsrate)? Sehr offen
      und schnell (Merge im Median 7 h), aber: kein GPL/LGPL/AGPL-Code, auch
      nicht lesen, keine Automatisierung kommerzieller CAD-Programme für
      Beiträge. [Bericht](docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
      *Präzisiert 2026-10-31 (Nutzer):* (1) kein (L/A)GPL-Code **in** Mechvane (bleibt MIT/Apache),
      (2) GPL-Programme als eigener Prozess sind erlaubt (CuraEngine, später CalculiX/Gmsh), Lizenz prüfen und
      im Installer nennen, (3) „nicht lesen“ gilt nur für Arbeit, die an SolidCraft oder cadmpeg gehen soll.
      Regeln in `AGENTS.md`.
- [x] Gegenprobe: Chili3D (TypeScript + OCCT-Wasm), Dune 3D (C++, SolveSpace
      + OCCT), FreeCAD 1.x als Plattform kurz bewerten.
      [Gemini-Rohfassung mit Prüfnotiz](docs/research/2026-10-19-plattform-gegenprobe-gemini.md):
      Chili3D und Dune 3D scheiden aus. FreeCAD (inzwischen 26.x) ist bei
      Zeichnungen weit vorn. Ein FreeCAD-Backend verträgt sich aber nicht mit
      Beiträgen zu SolidCraft (keine (L)GPL-Code-Kenntnis).
- [x] **Entscheidung (ADR 0001)** zwischen (*2026-10-20 angenommen:*
      [A+, SolidCraft-Kern unverändert, Mechvane als eigene Schicht](docs/adr/0001-grundlage-solidcraft.md),
      Bauteil = Design, Baugruppe = Design mit verknüpften Komponenten;
      Grundlage:
      [Dokumentmodell](docs/research/2026-10-19-dokumentmodell.md)):
  - **A – Plugin-/Erweiterungsprojekt auf SolidCraft** (bevorzugt, falls
    Phase 0 trägt): Mechvane liefert die Inventor-Schicht als Plugins und
    trägt Kernfunktionen upstream bei.
  - **B – Fork** von SolidCraft, falls Richtung oder Tempo nicht passen.
  - **C – Eigener Kern** in Rust mit OCCT hinter einem `BRepKernel`-Trait,
    nur wenn A und B ausscheiden (Aufwand ein Vielfaches).

## Phase 1: Agenten-Workflow und erste Inventor-Bausteine (ca. 2–3 Monate)

Unabhängig von der Plattformwahl zuerst das, was es woanders noch nicht gibt:

**Meilenstein v0.1 (Ziel Ende Dezember 2026, Nutzer-OK 2026-10-23):** Grundlagen
laufen und eine gute Web-UI für die Arbeit mit dem Agenten (Agent baut, Nutzer sieht,
zeigt, prüft). Danach nur noch Fachmodule. Schätzung bei 10–20 % Wochenbudget:

1. UI Stufe 1: 3D-Ansicht, Modellbaum, Befunde, Neuladen (~1 Woche). *Fertig 2026-10-24.*
1a. Einstieg für Besucher (Nutzer-OK 2026-10-24, vor Stufe 2): A Live-Demo auf GitHub Pages
   (`tools/build_demo_site.py`, *gebaut 2026-10-24*, seit 2026-10-25 mit „Modellieren“), B Installation
   in einem Schritt (`pip install git+…`, `mechvane setup` lädt SolidCraft-CLI und Web-App, `mechvane
   ui --demo`; *unter Linux fertig 2026-10-27*, frische venv mit leerem Cache geprüft, Windows auf der VM geprüft 2026-10-27), C Dateien in der UI öffnen: Ordner statt einer Datei, Auswahl und „Neues Bauteil“ im
   Modus „Modellieren“ (*fertig 2026-10-26*: `python3 -m mechvane.ui <ordner>`, `/api/project`, `/api/open`, `/api/new`), D Windows-Test (*2026-10-27 auf der Windows-11-VM bestanden*: pip, setup, ui --demo, Model by hand, mcp; Surface/ARM noch offen). PyPI: *Alpha `0.1.0a1` seit
   2026-10-27* (Nutzerentscheid, nur Linux getestet; erster Upload mit Token, danach Trusted Publishing
   per Tag `v*`). Stabile Version, wenn B auf Windows und Linux läuft.
1b. Handbedienung: SolidCraft-Web-App (Release-Asset `solidcraft-web-*.zip`) in die UI einbetten,
   Modi „Modellieren“ und „Prüfen“, Speichern zurück an Mechvane (Nutzer-OK 2026-10-24, zuerst Test).
   *Test bestanden und umgesetzt 2026-10-25* (`/model`, Bauteile und Baugruppen mit verknüpften
   Teilen). Befund anklicken wählt die Fläche in der App aus (`select.set`, *fertig 2026-10-26*). Offen: Befunde
   auch in der Demo nach dem Speichern (bräuchte die Prüfungen im Browser). **Vorgezogen 2026-10-31** (Nutzer:
   wichtig für den ersten Eindruck): Pyodide-Prototyp #35, `design_rules` gegen `app.execute` der Web-App.
2. UI Stufe 2: Fläche anklicken, Chatfenster mit dem Agenten **mit Spracheingabe** (Point and speak,
   Grundsatz 6: Auswahl plus gesprochener Auftrag gehen zusammen an den Agenten), Rückgängig
   (2–3 Wochen). Entwurf: [ADR 0003](docs/adr/0003-point-and-speak.md) (angenommen 2026-10-28,
   Argon-Review eingearbeitet). Vor dem Umsetzen entwerfen: Anbindung an den Agenten und Spracherkennung
   (Browser-Spracheingabe oder Whisper), Deutsch und Fachbegriffe wie „Fase 1 × 45°“, „M6“
3. Parameter im Formular, Öffnen/Speichern, Messen, Schnitt (1–2 Wochen). *Parameterformular, Messen und
   Schnitt auf der Prüfseite fertig 2026-10-29* (`/api/params`; Messen/Schnitt im Browser auf dem Netz,
   `viewtools.js`). Bohrungen: Ø, Achse, Achsabstand. *Messen an Kanten fertig 2026-10-30* (Länge, Kreis-Ø,
   Bogen R/Winkel, Bohrung aus zwei Halbflächen als ein Kreis; zwei Kanten: Winkel, Abstand, koaxial).
4. Praxistests mit dem Nutzer, Fehler beheben, Windows, Installation in einem
   Schritt (2–3 Wochen)

Nicht in v0.1 (bis 2026-10-31, jetzt geändert, siehe „Eigene Oberfläche“ unten und ADR 0005): ein eigener
Skizzierer und eigene Feature-Dialoge (4–6 Monate). Von Hand
modelliert wird in der eingebetteten SolidCraft-App (1b, geht mit Mechvane-Dateien sauber,
2026-10-25). Nach den ersten Praxistests entscheiden, ob mehr nötig ist. Richtung für alle
UI-Stufen: Bedienung möglichst nah an Inventor (Grundsatz 10).

**Fokus bis v0.1** (Nutzer 2026-10-31): Claude arbeitet an dieser Liste. Gemini bleibt gut ausgelastet, aber
nach Phasen geordnet: Issues mit Label `v0.1` zuerst, danach Füllaufträge aus Phase 1 (#25, #27, #28), deren
Branches erst gesichtet werden, wenn ihr Punkt dran ist. Phase 2 und später tragen `später` und ruhen (#29–#31).
Neue Ideen kommen sofort an ihre Phase in die ROADMAP; umgesetzt werden sie, wenn die Phase dran ist, außer der
Nutzer sagt ausdrücklich „jetzt“.
Der native CAD-Import bleibt Langzeitziel: #32/#33 werden gesichtet, neue Aufträge erst nach v0.1.
Bis v0.1 fehlt noch:
- [ ] **Eigene Oberfläche** (Nutzer 2026-10-31: „eigene vollständige Oberfläche“, schnell etwas zeigen):
      [ADR 0005](docs/adr/0005-eigene-oberflaeche.md) (angenommen 2026-10-31). Stufe 1 Arbeitsbereich wie Inventor,
      Stufe 2 eigene Feature-Dialoge über `/api/feature`, Stufe 3 Skizzierer (mit Übersicht der Abhängigkeiten und
      farbiger Anzeige von Konflikten und Überbestimmung wie Onshapes Constraint Manager, auf SolidCraft
      `sketch_constraints`; so weit möglich, sonst
      direkt nach v0.1). SolidCraft-App nur noch als Expertenmodus.
      *Stufe 1 fertig (#36, gemergt 2026-11-01, veröffentlicht mit 0.1.0a12 und Live-Demo 2026-11-02).*
      *Stufe 2 begonnen 2026-11-02:* `/api/feature` mit Vorschau, gemeinsame Rückgängig-Liste für Hand und Agent
      (auch das Parameterformular), Kantenwahl in der Ansicht, Dialoge Rundung und Fase (ADR 0005, Abschnitt
      „Umgesetzt“), Rundung und Fase aus dem Baum bearbeiten (Doppelklick) und Features löschen (Rechtsklick, Entf),
      Bohrung (Durchgang nach ISO 273, Gewinde, Senkungen aus Mechvanes Tabellen, durch alle oder Tiefe; auch bearbeiten).
      Rechteck- und Kreismuster, Spiegeln (Features im Baum anklicken, Richtung/Achse/Ebene aus X/Y/Z oder angeklickter
      Kante bzw. Fläche; auch bearbeiten), Extrusion und Drehung auf einer vorhandenen Skizze (Operation, Richtung,
      durch alle; auch bearbeiten). Offen: Bohrungsposition über Abstände zu Kanten, Profilwahl bei mehreren Profilen.*
      *Stufe 3 begonnen 2026-11-02:* Skizze auf XY/XZ/YZ oder Fläche, Rechteck und Kreis per Klick oder Zahl, voll
      bemaßt (`mechvane.sketch`), OK öffnet die Extrusion; auch in der Live-Demo. **Nutzer 2026-11-02: so nicht**,
      Skizze anlegen und füllen müssen getrennt sein wie in Inventor/Fusion: eigene Skizzierumgebung mit Werkzeugen,
      Bemaßen, Fertig stellen, ohne Sprung zur Extrusion. Entwurf ADR 0005, Nachtrag 2026-11-02; ersetzt den Dialog.
      *Dialoge grafisch aufwerten (Nutzer 2026-11-02, später):* kleine Symbole wie in Inventor, etwa Bohrungstyp
      (einfach, Senkung, Kegelsenkung) und Abschluss (durch alle, Abstand) als Bildknöpfe statt Auswahllisten,
      Richtungsknöpfe (Seite 1/2, symmetrisch), Operation (Join/Cut/…) als Symbolreihe, Auswahlfelder mit Pfeil-Symbol
      wie Inventors „Positionen“/„Kanten“. Eigene SVGs ohne Autodesk-Grafiken (ADR 0005, offene Frage 3).
      *Dialoge in der Live-Demo fertig 2026-11-02:* `demo_kernel.js` beantwortet die `api/*`-Anfragen im Browser über die
      versteckte SolidCraft-Web-App (Netz per `file.export` 3mf-tagged in OPFS, Prüfung per Pyodide, Rückgängig über
      `edit.undo/redo`).
- [x] **Live-Demo prüft nach dem Speichern** (1b, erster Eindruck): Pyodide-Prototyp #35, danach einbauen.
      *Prototyp gemergt 2026-11-02* (`browser_check.py`, `demo_check.js`, ~5 MB Download, 2 ms je Prüfung).
      *Fertig und veröffentlicht 2026-11-02 (0.1.0a12, Nutzer: Stufe 1 ausliefern):* in Chromium gegen die echte
      Web-App getestet, unverändert gespeichert gleiche 6 Befunde wie vorberechnet, nach `parameters.change`
      (Grundplatte 1,2 mm) live neue Befunde. Baugruppen in der Demo bleiben vorberechnet.
- [ ] **Point and speak fertig** (2): Spracheingabe auf echten Geräten (Handy, Surface) mit Fachbegriffen
      testen, Fehler beheben.
- [x] **Öffnen/Neu ohne Browser-Dialoge** (3): „New part“ mit eigenem Dialog statt `prompt()`/`alert()`
      (Surface-Test 2026-10-31). *Erledigt 2026-11-01: `newpart.js`, Fehler im Dialog, Klicktest in
      `ui_smoke.py`. Zwei `confirm()` im Agenten-Chat (Undo trotz Konflikt, Einwilligung Spracheingabe) bleiben
      vorerst.*
- [ ] **SolidCraft-Fehler für Agent und Nutzer übersetzen** (Nutzer 2026-10-31, aus einem Gespräch mit Gemini):
      Jeder fehlgeschlagene Befehl (`run`, Mechvane-Werkzeuge, später `/api/feature`) wird abgefangen, das
      Feature und die Stelle lokalisiert (Kante/Fläche mit Mechvane-Namen, Punkt, beteiligte Features) und
      in einem Satz erklärt, was sich berührt oder schneidet, mit Vorschlag (z. B. „Fase 3 trifft Bohrung 1
      bei z = −4,2; Fase ≤ 0,8 mm oder Bohrung versetzen“). Ausgangsfall: „lumps: shell boundaries intersect“
      (Praxistest 6, #34). Häufige SolidCraft-Meldungen sammeln und je eine Übersetzung mit Test.
      *Stufe 1 fertig 2026-11-02* (#38, `sc_errors.py`: 24 Meldungen mit Erklärung und Vorschlag in `run`). Offen:
      Stelle mit Mechvane-Namen lokalisieren, Mechvane-Werkzeuge außer `run`.
- [ ] **Bauteilende für den Agenten** (Nutzer 2026-11-01, vorgezogen zur Fehlerübersetzung): MCP-Werkzeug,
      das den Bauteilende-Marker vor eine Fehlerstelle setzt (SolidCraft `timeline.rollback`/`timeline.roll_to`),
      dort isoliert messen und reparieren, dann schrittweise vorrücken. Regel im Skill `konstrukteur`.
- [x] **Zustandsbericht nach jedem Modellschritt** (*fertig 2026-11-02, #37, `state_delta.py`*) (Nutzer 2026-11-01, zweiter Gemini-Vorschlag): jede Änderung
      über MCP (und später `/api/feature`) liefert ein knappes Delta: Hüllquader und Schwerpunkt vorher/nachher,
      Volumen- und Massendifferenz, Anzahl Körper. Warnt bei Schnitt ohne Wirkung (Volumen unverändert), bei
      großen Sprüngen und wenn ein Teil in mehrere Körper zerfällt. Wenige Zeilen, kein Bild.
- [ ] **Sichtprüfung für den Agenten** (Nutzer 2026-11-01, Idee aus dem Gemini-Gespräch): MCP-Werkzeug
      `verify_view` gibt ein Bild mit vier Feldern zurück (Iso, Vorne, Oben, Schnitt durch Mitte oder gewählte
      Stelle), je mit Achsen, Maßstab und Hüllmaßen; zuletzt geändertes Feature farbig, bei Fehlern die Stelle
      aus der Fehlerübersetzung markiert. Gezielt aufrufen (neues Feature an neuer Stelle, nach Fehlern, vor dem
      Abschluss; Regel im Skill `konstrukteur`), nicht nach jedem Schritt (Kontext). Zahlen bleiben maßgeblich
      (`measure`, `check_design`). Baut auf `screenshot` (headless) auf.
- [x] **Baugruppen wie Inventor**: erstes Teil festlegen (#26, erledigt 2026-11-01), `bolted_connection` durch alle und
      Kollisionsprüfung (#34, erledigt 2026-11-02; „durch alle“ bohrt auch eine zweite Wand desselben Teils dahinter).
- [ ] **Desktop-App Schritt 1**: Sichtprüfung des App-Fensters unter Windows und Linux.
- [ ] **Eigenes Fenster unter Windows, vor 0.1.0** (Nutzer 2026-11-02, Zwischenschritt zu Grundsatz 12, nach
      Skizzierumgebung Schritt a): pywebview auf WebView2 (Edge-Engine, in Windows 11 eingebaut, WebGL/WebGPU) statt
      Chrome-App-Fenster: eigenes Fenster, Symbol und Titel, der Prozess gehört Mechvane (Fenster zu = Mechvane zu).
      Paket mit PyInstaller und Installer (Inno Setup): Python und SolidCraft im Paket, kein `pip`. Linux bleibt vorerst
      beim Chrome-App-Fenster (WebKitGTK). Die endgültige Hülle (Tauri/Electron/Qt) bleibt beim Prüfpunkt Sprache.
      Prüfen auf Surface und win-cad, auch Expertenmodus und Pyodide im WebView2.
- [ ] **Praxistests** (4): mindestens zwei weitere Runden mit dem Nutzer, je eine echte Konstruktion von
      Anfang bis Ende (Agent und Handbedienung), Befunde beheben.
- [ ] **Stabile Version** 0.1.0 auf PyPI, wenn alles oben erledigt ist und Linux und Windows laufen.

- [x] Abgleichliste Inventor ↔ SolidCraft ↔ Mechvane (Register, Befehlsnamen, Tastenkürzel,
      Browser, Dialoge), Recherche an Gemini (*fertig 2026-10-30*,
      [Bericht](docs/research/2026-10-30-abgleich-inventor-solidcraft-flash.md)), danach entscheiden, was über SolidCraft-
      Einstellungen/Plugins geht und was eine eigene Oberfläche braucht.

**Prüfpunkt Sprache (nach v0.1, spätestens Januar 2027, Nutzer-OK 2026-10-24):** Mechvane bleibt
bis v0.1 Python (ADR 0001: „Rust, sobald die Schnittstelle steht“). Dann neu entscheiden, früher,
falls das SolidCraft-Plugin-System (#1221, WASM/WIT) fertig ist. Für Rust spricht: Prüfungen
als SolidCraft-Plugin, ein einzelnes Programm ohne Python. Dagegen: Umbau, langsame Builds
auf dem Steuer-Container; ein Paket mit eingebautem Python löst die Installation auch.

- [ ] **Desktop-App** (Grundsatz 12). Schritt 1 für v0.1, zusammen mit 1a B: three.js und alle
      Abhängigkeiten mitliefern (offline), `mechvane ui` öffnet ein eigenes App-Fenster
      (Chrome/Edge `--app=`), Startmenü-Verknüpfung unter Windows. *Schritt 1 umgesetzt 2026-10-28*
      (`mechvane/ui/appwindow.py`, `mechvane shortcut`, unter Linux und Windows getestet, Sichtprüfung offen). Schritt 2 nach v0.1: echte
      Desktop-App mit Installer für Windows und Linux; vorher Recherche der Hüllen (Gemini) und
      ein Test, ob die SolidCraft-Web-App darin läuft. Entscheidung zusammen mit dem Prüfpunkt
      Sprache (spätestens Januar 2027).

- [ ] **Website mechvane.dev** (Nutzerwunsch 2026-10-29): Startseite mit Leitsatz, Rendering, was heute
      geht, Einstieg und Roadmap-Teaser; Live-Demo zieht nach `/demo/`. Entwurf durch Gemini 4 Argon in der
      Gemini-App nach `docs/website/ARGON-PROMPT.md` (Fakten: `docs/website/FAKTEN.md`), Einbau und Prüfung
      durch Claude (`website/`, `tools/build_demo_site.py`), Veröffentlichung nach Nutzer-OK.
- [ ] **Private Online-Version unter `app.mechvane.dev`** (Nutzerwunsch 2026-10-28, aus der
      Homeserver-Session): die eigene Web-UI aus jedem Browser erreichen, auch ohne Tailscale; nur
      für den Nutzer, kein öffentlicher Dienst. Einordnen **nach Web-UI Stufe 2** (vorher zeigt die
      UI nur an); der MCP-Fernzugang kann früher kommen. Vorschlag:
      - Mechvane läuft im Homelab (eigener kleiner LXC oder Steuer-Container), UI als
        systemd-Dienst, keine Cloud-Kosten.
      - Cloudflare Tunnel (`cloudflared`, nur ausgehend): kein Port am Router, Heim-IP verborgen.
      - Cloudflare Access davor, nur das Google-Konto des Nutzers. Pflicht, weil die UI keinen
        eigenen Login hat und Agent und Dateizugriff (ADR 0003) dahinter liegen.
      - Optional `mcp.mechvane.dev`: Mechvane-MCP über HTTP auf demselben Weg, damit Claude (App,
        Handy) direkt an den Modellen arbeiten kann; Anmeldung für Remote-MCP hinter Access klären.
      - `mechvane.dev` bleibt die öffentliche Demo (GitHub Pages), `www` und `mechvane.com` leiten
        weiter wie bisher.
      - DNS und Access richtet der Nutzer per cf-CLI ein (Befehle vorbereiten), LXC und Dienst die
        Homeserver-Session, die danach auch die Homeserver-Doku nachzieht.

- [ ] **Eigene Oberfläche, SolidCraft nur noch im Hintergrund** (Entscheidung Nutzer 2026-10-28): Am
      Ende sieht man nur die Mechvane-Oberfläche, SolidCraft rechnet und zeichnet darunter. In der App,
      der README und allen öffentlichen Texten bleibt SolidCraft ausdrücklich genannt. Weg in Stufen:
      - *Geändert 2026-10-31 (Nutzer):* Arbeitsbereich und eigene Feature-Dialoge kommen in v0.1, der
        Skizzierer so weit möglich ([ADR 0005](docs/adr/0005-eigene-oberflaeche.md)).
      - Bisher: bis v0.1 eigene Oberfläche für Prüfen und Chat, SolidCraft-Web-App zum Modellieren.
      - Danach eigene Dialoge für die häufigsten Features über den Server (headless `solidcraft-cli`,
        wie Modus „Prüfen“ und Agent); das braucht kein Live-Ziehen.
      - Skizzierer und Live-Vorschau mit dem SolidCraft-Kern im Browser: Web-App eingebettet, ihre
        Oberfläche ausgeblendet. Grundlage ist der Einbettmodus `?embed&open=` (SolidCraft #6252, ab
        0.23.0, nur lesend). Unser Wunsch nach `?embed=viewport&edit` (nur Ansicht, bearbeitbar über
        `window.solidcraft`) und `doc.open {reload}` liegt als
        [SolidCraft #8517](https://github.com/tangency-labs/solidcraft/issues/8517) (2026-10-28).
      - Für Desktop- und Android-App später der Kern als Bibliothek (Rust/WASM), entschieden mit dem
        Prüfpunkt Sprache.
      - SolidCraft auf 0.25.1 aktualisiert (2026-10-28), der Einbettmodus ist damit verfügbar.

- [ ] **Native Android-App** (Nutzerwunsch 2026-10-28): Mechvane unterwegs auf dem Handy, vor allem
      zum Ansehen, Prüfen und für Point and speak (Fläche antippen, Auftrag sprechen). Einordnen nach
      Stufe 2 und `app.mechvane.dev`, denn die App braucht zunächst einen Server: Mechvane läuft in
      Python mit `solidcraft-cli`, beides gibt es für Android nicht. Vorschlag:
      - Kotlin mit Jetpack Compose, Verbindung zum eigenen Mechvane-Server (Homelab über
        `app.mechvane.dev` hinter Cloudflare Access, zu Hause auch LAN/Tailscale).
      - Eigene native Teile: 3D-Ansicht aus `/api/mesh` (z. B. Filament oder SceneView), Modellbaum,
        Befunde, Chat mit dem Agenten über `/api/agent/*`, Spracheingabe über Androids
        `SpeechRecognizer`, der Deutsch auch offline kann (passt zu ADR 0003, Abschnitt 4).
      - Modellieren von Hand bleibt vorerst in der Web-App (WebView mit der SolidCraft-Web-App als
        Notlösung, 50-MB-wasm, auf dem Handy zu prüfen).
      - Vorher klären: Anmeldung gegen Cloudflare Access aus einer App (Service-Token oder
        Browser-Login), Offline-Ansicht zuletzt geladener Modelle.
      - Verteilung zuerst über das eigene F-Droid-Repo im Homelab, Play Store später.
      - Vorher schon die Web-Oberfläche für Touch tauglich machen (Tablet, Stift), Vorbild Onshape (Nutzer 2026-11-02).
      - Später prüfen: SolidCraft-Kern als Android-Bibliothek (Rust), dann ginge mehr ohne Server;
        hängt am Prüfpunkt Sprache.

- [ ] **Funktions- und Modulwünsche direkt aus der App** (Nutzerwunsch 2026-10-28): Knopf
      „Wunsch äußern“ in der Web-UI (beide Modi, auch in der Live-Demo). Vorschlag: Er öffnet ein
      vorausgefülltes GitHub-Issue (`issues/new?template=…&title=…&body=…`) im öffentlichen Repo,
      angemeldet ist der Nutzer selbst, Mechvane braucht kein Token und schickt nichts von allein.
      Vorbefüllt: Art (Funktion, Fachmodul, Normteil, Prüfregel, Fehler), kurze Beschreibung,
      optional Mechvane- und SolidCraft-Version, Betriebssystem, offenes Dokument nur als Name.
      Dazu eine Issue-Vorlage (`.github/ISSUE_TEMPLATE/feature_request.yml`) mit Labels pro Art,
      damit Wünsche sortierbar sind und Gemini-Queue/Tagesplan sie aufgreifen können. Mit Stufe 2:
      „Schreib das als Wunsch auf“ im Chat, der Agent formuliert das Issue, der Nutzer schickt es
      ab. Ohne GitHub-Konto später ggf. ein Formular (offen). Klein (ca. ½ Tag), passt vor v0.1.
      Vorlage im öffentlichen Repo erst nach OK.

- [ ] **Mechvane-Schicht als MCP-Server** (nach ADR 0001): Bauteil- und
      Baugruppendateien öffnen/speichern, Verknüpfungen aktualisieren und
      Gelenk-Frames danach prüfen, Skizzenregel (verbrauchte Skizze direkt
      vor ihrem Feature), semantische Abfragen. Prototyp in Python vor
      `solidcraft-cli mcp`.
      *Stand 2026-10-20:* Prototyp läuft ([Doku](docs/mechvane-mcp.md),
      99 Prüfungen grün in `tests/mechvane/check.py`). Praxistest
      Klappscharnier bestanden (#3330 erkannt und repariert). Dazu: Gelenke
      bearbeiten, löschen und nachträglich aufnehmen, `measure`,
      Arbeitselemente nach der Skizzenregel, Ordneransicht im Browser,
      Besitz aus den Feature-Definitionen, Unterbaugruppen (Mechvane löst sie
      selbst auf, weil SolidCraft sie flachklopft), semantische Abfragen
      (`find`), Bearbeiten an Ort und Stelle (`edit_in_place`,
      `finish_edit`), Reparatur auch an Ebenen. Offen: Reviews der
      Gemini-Bausteine durch ein zweites Modell, Praxistest mit allen neuen
      Werkzeugen.
- [ ] **Upstream: Flächennamen über Verknüpfungen** (Blocker für getrennte
      Dateien), gemeldet als
      [#3330](https://github.com/tangency-labs/solidcraft/issues/3330)
      (2026-10-20). Prüfpunkt sechs Wochen (ADR 0001). Regressionstest in
      `tests/mechvane/check.py` (meldet, falls SolidCraft das Gelenk von
      selbst richtig hält).

- [ ] **Konstrukteurs-Agent**: Claude-Skill bzw. Agent-Vorlage, die
      iterativ konstruiert (Skizze → Feature → messen → Snapshot prüfen →
      korrigieren), mit Konstruktionsregeln (Wandstärken, Randabstände,
      Einschraubtiefe 1,5 × d, Druckbarkeit).
      *Erster Stand 2026-10-20:* `check_design` mit Profilen `fdm_0.4` und
      `cnc_alu`, Projekt-Skill `.claude/skills/konstrukteur`
      ([Bericht](docs/research/2026-10-20-konstrukteur.md)). Offen:
      Brückenerkennung, Druckrichtung wählbar, genauerer Randabstand.
- [ ] **Normteile-Generator** (prozedural statt Inhaltscenter-Datenbank):
      ISO 4762/DIN 912, ISO 4032, ISO 7089, Gewindeeinsätze, Kugellager
      6000er-Reihe.
      *Erster Stand 2026-10-20:* `standard_part` für ISO 4762, ISO 4032,
      ISO 7089, Ruthex-Einsätze, 6000–6005
      ([Bericht](docs/research/2026-10-20-normteile-gemini.md)). Offen:
      Review durch ein zweites Modell, weitere Reihen (ISO 10642, ISO 4017).
- [ ] **Eigene Web-UI** (Nutzer-OK 2026-10-23, Weg B statt SolidCraft-Panels):
      Stufe 1 nur lesend (3D-Ansicht, Modellbaum, Befunde aus `check_design` und
      `check_joints`), Stufe 2 Auswahl an den Agenten (Point and speak), Chatfenster mit Spracheingabe.
      *Stand 2026-10-24:* Stufe 1 fertig (`python3 -m mechvane.ui <datei>`, Bericht
      `docs/research/2026-10-24-web-ui-stufe1-argon.md`). Nächster Schritt: Stufe 2.
- [x] **Bohrungsassistent mit Verschraubung**: Schraube + Scheibe + Mutter
      + passende Bohrung in allen Bauteilen (Inventor „Verschraubung“).
      [Spezifikation](docs/research/2026-10-20-bohrungsassistent-spec.md).
      *Erster Stand 2026-10-20:* `bolted_connection` für Durchgang (mit
      Senkung), Sackloch und Ruthex-Einsatz. Senkdurchmesser DIN 974-1 (Reihe 1 und 5)
      seit 2026-10-23 an der Quelle geprüft. Muster (Teilkreis, Rechteck), Auflisten, Ändern und Löschen seit 2026-10-23.
      Senkkopfschrauben ISO 10642 mit 90°-Kegelsenkung nach DIN 74 Form F / ISO 15065
      unterstützt (`head="countersunk"`, quellengeprüft 2026-10-23).
      ISO-286-Passungen als `iso_fit` (Grenzabmaße, Spiel/Übermaß) seit 2026-10-23;
      offen: Passung als Attribut an Bohrung und Welle, Lagersitze in `standard_part`.
      *Praxistest 6 (2026-10-31, [Bericht](docs/research/2026-10-31-praxistest-6.md), umgesetzt 2026-11-02, #34):*
      Durchgangsbohrungen, Senkungen und Flachsenkungen mit Ausdehnung „durch alle“ (parametrische
      Dicke bleibt Durchgangsbohrung); Kollisionsprüfung vor dem Bohren mit verständlicher
      Meldung (beteiligte Bauteile, Lage, Hüllquader, Volumen, Handlungsanweisung) und Rollback.
- [ ] **Eigener offener Regelkatalog** (Nutzerwunsch 2026-10-20: Werte
      selbst belegen, keine Normen kaufen). *Seit 2026-10-23:* Format nach
      [ADR 0002](docs/adr/0002-wissenskatalog-format.md) angenommen, `katalog/` mit
      ersten Einträgen gemergt. Ein Eintrag pro Wert als Daten
      statt im Code: Wert, Geltungsbereich (Werkstoff, Festigkeitsklasse,
      Größe), Quelle mit URL, wörtlichem Zitat und Seite, Status
      (belegt / hergeleitet / Richtwert / offen), mindestens zwei
      unabhängige Quellen für „belegt“. Automatische Prüfung: PDF laden,
      Zahl im Text suchen (so fiel der Abschreibfehler bei Hanke auf).
      Wo möglich aus öffentlichen Formeln herleiten (Gewindegeometrie nach
      ISO 68-1, Scherfestigkeit nach den VDI-2230-Formeln aus
      Sekundärquellen). Offene Datensätze vorher sichten und Lizenz
      prüfen: BOLTS, FreeCAD-Fasteners-Workbench, cq_warehouse.
      Normtexte nicht abschreiben, nur einzelne Maßwerte mit Quelle.
      Erweitert zum Wissenskatalog mit Best Practice und Graph:
      [Plan](docs/research/2026-10-20-wissenskatalog-plan.md).
- [ ] **Werkstoffdatenbank** (Nutzerwunsch 2026-10-29): umfangreich, Kennwerte (Dichte, E-Modul,
      Rm, Rp0,2, Bruchdehnung, Härte, Wärmeausdehnung, -leitfähigkeit, Gebrauchstemperatur) je
      Werkstoff und Zustand als Katalogeinträge nach ADR 0002 (`katalog/eintraege/werkstoffe/`),
      recherchiert von Gemini Flash wie die Regeln (Quelle, wörtliches Zitat, `check_sources.py`,
      „belegt“ erst mit zwei Quellen). Runde 1 (16 Werkstoffe: Baustahl, Vergütungsstahl, Edelstahl,
      Aluminium, Grauguss, Messing, POM, PA6, PLA, PETG) *gemergt 2026-10-29*
      ([Bericht](docs/research/2026-10-29-werkstoffe-flash.md), `katalog/eintraege/werkstoffe/`). Danach:
      τ_B je Werkstoff *ergänzt 2026-10-29* (#16, meist Richtwerte; drei Werte ungeklärt), *Bibliothek für SolidCraft seit 2026-10-29*
      (`tools/katalog_to_solidcraft.py` → `katalog/werkstoffe.solidcraft-library.json`),
      Werkstoff je Bauteil (SolidCraft-`material` bzw. Mechvane-Metadaten), Masse/Gewicht aus der
      Dichte, und alle Prüfregeln werkstoffabhängig (seit 2026-10-29 die Einschraubtiefe in
      `check_design(material=…)`; Randabstand und Wandstärke hängen bisher nur am Fertigungsprofil).
      Zielformat: SolidCraft-Kennwertkarte (`physical_card`, Schema 1, SI mit Quelle je Wert) in
      eigenen Werkstoffen bzw. Bibliotheken `solidcraft-library/2`; der Katalog bleibt die belegte Quelle.
- [ ] **Verfahrensregeln ausbauen** (Nutzer 2026-11-01, Gemini-Vorschlag): je Fertigungsprofil weitere Regeln
      mit Quelle, z. B. FDM: liegende Bohrungen als Tropfenform, Kerndurchmesser für Einpressmuttern; CNC:
      Mindest-Innenradien für Fräser, Bohrtiefe zu Durchmesser, Hinterschnitte und Werkzeugzugang.
- [ ] **Regeln aus Werkstoffkennwerten herleiten** (Nutzerwunsch 2026-10-29): statt Tabellen je
      Werkstoff („Stahl, M6: ≥ 6 mm“) Formeln aus Kennwerten (Rm/Rp0,2 der Schraube, Scherfestigkeit
      des Bauteilwerkstoffs, Gewindegeometrie nach ISO 68-1), damit jeder Werkstoff der Datenbank
      ohne eigene Tabellenzeile geprüft werden kann. Kandidaten: Einschraubtiefe (Abstreifen des
      Innengewindes, z. B. NASA RP-1228, FED-STD-H28, Alexander/VDI 2230 aus Sekundärquellen),
      Randabstand (Lochleibung), Flächenpressung unter dem Kopf. Tabellenwerte (Bossard) bleiben
      als Gegenprobe. Recherche (Issue #14, gemergt 2026-10-29):
      [Regeln aus Kennwerten](docs/research/2026-10-29-regeln-aus-kennwerten-flash.md); Kernformel
      m_eff = A_s·R_m / (A_n'·τ_B), braucht in der Datenbank τ_B bzw. τ_B/R_m, Rp0,2 und p_G.
- [ ] **Material- und Darstellungseditor** (Nutzerwunsch 2026-10-29): Werkstoff (Kennwerte aus der
      Datenbank) und Aussehen (Farbe, Rauheit, Metall, Klarlack, Transparenz, Textur) je Bauteil
      bzw. Fläche bearbeiten, mit Vorschau in der 3D-Ansicht. Ein Werkstoff, mehrere Oberflächen
      (gebürstet, poliert, eloxiert). Aussehen in einem offenen Format, das sich 1:1 in Blender rendern
      lässt (Kandidaten: MaterialX mit OpenPBR Surface, glTF-PBR mit KHR-Erweiterungen; Blenders
      Principled BSDF als Ziel). Recherche (Issue #15, gemergt 2026-10-29):
      [Darstellungsformat](docs/research/2026-10-29-darstellungsformat-flash.md) empfiehlt glTF-PBR mit
      KHR-Erweiterungen und OpenPBR-Namen (MaterialX: kein direkter Import in Blender, three.js nur mit
      WebGPU). Gegen Blender 5.0–5.2 nachgeprüft: weiter kein MaterialX-Import.
      [ADR 0004](docs/adr/0004-darstellungsformat.md) *angenommen 2026-10-29* (Probe: glTF trägt nach Blender,
      Schliffrichtung per Skript).
- [ ] Referenzteile-Korpus mit Sollwerten anlegen (`tests/reference/`).
      *Begonnen 2026-10-19:* 7 Teile mit `check.py` (seit 2026-10-23 Welle, Rohrhalter, Rippenplatte), weitere aus dem Alltag
      ergänzen (Druckteile, Vorrichtungen).

### Nach v0.1: Harness und Zusammenarbeit (Nutzer 2026-11-01, [Vorschlag](docs/research/2026-11-01-roadmap-ergaenzungen-harness-ux.md))

- [ ] **Nutzersperren**: Parameter, Maße, Features und Funktionsflächen „vom Nutzer festgelegt“ (Schloss im
      Baum, Attribut in den Mechvane-Metadaten); der Agent bekommt bei Änderungen eine sprechende Ablehnung
      mit Vorschlag. Keep-Out-Flächen: Überschneidung nach dem Befehl prüfen und zurücknehmen.
- [ ] **Herkunft von Maßen**: Berechnete Maße (Regelkatalog ADR 0002, Formeln aus Werkstoffkennwerten,
      `bolted_connection`) schreiben Herleitung und Quelle in den Kommentar des Parameters (SolidCraft-
      Parameter haben ein Kommentarfeld); Tooltip in der eigenen Oberfläche.
- [ ] **3D-Diff bei Agenten-Änderungen**: vorheriges Netz als Geistervolumen über dem neuen Stand,
      Markierung im Baum (neu/geändert), einzelne Änderungen annehmen oder verwerfen. Abhängigkeiten aus
      `timeline.dependents`. Vorbild Onshape „Visual Compare“ (entfernt rot, neu blau, Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      SolidCraft hat dafür `inspect.compare`, auch für benannte Stände (Versionen und Varianten).
- [ ] **Versionen und Varianten** (Nutzer 2026-11-01): benannte Stände mit Vergleich (3D nebeneinander,
      Feature-Diff aus `document.json`, Git darunter), danach Varianten-Zweige, besonders für den Agenten
      („Variante A/B“, übernehmen oder verwerfen), zuletzt Zusammenführen auf Feature-Ebene mit
      Konfliktanzeige (Vorbild Onshape).
- [ ] **Kommentare und Aufgaben am Modell** (Nutzer 2026-11-02, Vorbild Onshape, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Notizen und
      Aufgaben an Flächen, Kanten oder Features geheftet, im Baum und in der Ansicht als Pins. Dieselbe Schicht trägt
      Befunde der Prüfseite und Aufträge an den Agenten („diese Fläche 2 mm dicker“), erledigte Aufgaben bleiben
      als Verlauf am Teil. Speichern in den Mechvane-Metadaten, Bezug über Flächennamen.
- [ ] **Dem Agenten folgen** (Nutzer 2026-11-02, Vorbild Onshape Follow Mode, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Die Ansicht zeigt live,
      woran der Agent gerade arbeitet (Kamera, Auswahl, aktuelles Feature), abschaltbar; umgekehrt bekommt der
      Agent bei Point and speak Kamera und Auswahl des Nutzers.
- [ ] **Mensch und Agent gleichzeitig am Modell** (Nutzer 2026-11-02, Vorbild Onshape Simultaneous Editing,
      [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Der Nutzer arbeitet weiter, während der Agent ändert, ohne Sperre des ganzen Dokuments. SolidCraft
      ist ein Prozess für einen Nutzer: zuerst Änderungen des Agenten als Vorschlag auf einer Kopie (siehe 3D-Diff,
      Varianten), echtes gleichzeitiges Bearbeiten erst prüfen, wenn der Kern das hergibt.
- [ ] **Webhooks** (Nutzer 2026-11-02, Vorbild Onshape, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Ereignisse wie „Teil gespeichert“,
      „Prüfung fehlgeschlagen“ oder „Agent fertig“ an eine URL melden (ntfy, Home Assistant, Slicer-Kette).
      Ergänzt die vorhandene HTTP-API `/api/*`.

## Phase 2: Fachmodule als Plugins (ca. 4–6 Monate)

Reihenfolge nach Nutzen für den eigenen Alltag:

- [ ] **Native Dateien aller großen CAD-Systeme importieren, mit Feature-Verlauf** (Nutzerentscheidung 2026-10-31:
      Langzeitziel, egal wie lange es dauert; ohne die Fremdprogramme, Formate per Reverse Engineering im Clean Room,
      kein GPL-Code, jede Formataussage an Beispieldateien belegt). Ziel: Bauteile und Baugruppen mit Verlauf,
      Skizzen, Parametern und Abhängigkeiten als SolidCraft-Befehle neu aufbauen, ohne Verlust (Grundsatz 7).
      Nicht abbildbare Features werden Platzhalter mit Originaldaten, bis Mechvane sie kann. Prüfung je Datei:
      Der in der Datei mitgespeicherte Körper ist das Soll für den neu aufgebauten Verlauf (Volumen, Hüllquader,
      Flächenzahl). Kennzahl je Format: Anteil der Features, die in einem Korpus echter Teile ohne Platzhalter
      ankommen. Je Format drei Stufen: (1) Container, Eigenschaften, B-Rep,
      Parameter, Feature-Namen, (2) Features dekodieren, (3) Abbildung auf SolidCraft. Gemeinsame Bausteine:
      OLE-Container-Leser, ACIS/ShapeManager- und Parasolid-B-Rep-Leser, Abbildungsschicht Feature → SolidCraft.
      - **Grundlage cadmpeg** (Fund 2026-10-31): [cadmpeg](https://github.com/cadmpeg/cadmpeg), Apache-2.0, Clean Room,
        liest Inventor, SolidWorks, CATIA V5 schon bis L3 (B-Rep), Fusion/FreeCAD L5, Inventor-Features teilweise
        (Parameter, Skizzen, Extrusion, Bohrung, Rundung, Fase). SolidCraft nutzt cadmpeg nur für offene Formate.
        Arbeitsteilung: Format-Dekodierung (Features, L4–L6) als Beiträge zu cadmpeg, Mechvane übersetzt die
        cadmpeg-IR in SolidCraft-Befehle. Öffentliche Beiträge nur mit Nutzer-OK.
      - **Inventor** `.ipt`/`.iam`: zuerst. #32 (Argon) misst cadmpeg an den eigenen Daten, Wege und Rechtslage #31. Testkorpus aus
        eigenen Inventor-Daten (2015–2025), privat und nicht im Repo.
      - **FreeCAD** `.FCStd` (offen, ZIP + XML, Verlauf lesbar): billiger Testfall für die Abbildungsschicht.
      - **Solid Edge** `.par`/`.asm` und ältere **SolidWorks** `.sldprt`/`.sldasm` (OLE wie Inventor, Parasolid-B-Rep).
      - **Fusion** `.f3d` (ZIP, ShapeManager-B-Rep wie Inventor).
      - Neuere **SolidWorks**, **Siemens NX** `.prt` (Parasolid), **CATIA V5** `.CATPart`/`.CATProduct`,
        **Creo/Pro/E** `.prt`/`.asm`.
      - Dazu neutrale Formate mit PMI (STEP AP242, Parasolid `.x_t`, JT), falls SolidCraft sie nicht schon liest.
- [ ] **Gestell-Generator** für Aluprofile (Item/Bosch 20/30/40er Nut) und
      Stahlprofile, mit Längenliste.
- [ ] **Schweißen** (Nutzerwunsch 2026-10-29): Schweißnähte als eigene Features (Kehlnaht, Stumpfnaht,
      Nahtdicke a, Länge, umlaufend), Schweißbaugruppen, Nahtsymbole nach ISO 2553 in der Zeichnung,
      eigenes Aussehen der Naht. Bisher im Testmodell nur als konkave Rundung am Fuß
      (`tools/build_logo_showcase.py`). Grundlagen recherchiert (#19):
      [Schweißen im CAD](docs/research/2026-10-30-schweissen-grundlagen-flash.md) mit Vorschlag fürs Datenmodell
      (Vorbereitung, Nähte, Nachbearbeitung wie Inventor; Naht als Volumen oder kosmetisch).
- [ ] **Blech-Ergänzungen** (falls upstream noch Lücken): Blechregeln-
      Bibliothek, Abwicklungs-DXF für Laser-Dienstleister. **3D und Abwicklung nebeneinander**, beide live beim
      Bearbeiten (Vorbild Onshape, Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)); SolidCraft rechnet die Abwicklung schon.
      **Volumenkörper in Blech umwandeln** (Vorbild Onshape Convert & Rip, Nutzer 2026-11-02): Biegekanten und
      Trennkanten wählen, der Rest wird Blech; SolidCraft hat dafür `sheet_convert`, Mechvane braucht Dialog und
      Agenten-Werkzeug.
- [ ] **Konstruktionsassistenten**: Welle (Absätze, Nuten, Sicherungsringe),
      Stirnrad, Zahnriemen-Trieb, Passfedern, mit Berechnung.
- [ ] **Slicer-Modul (grafisch)** (Nutzerwunsch 2026-10-19): Plugin, das
      der Nutzer selbst bedient, nicht nur eine Skript-Brücke. Teil aufs Bett
      legen und drehen, Profil/Material wählen, Einstellungen ändern,
      Schichtvorschau, G-Code an OctoPrint (Ultimaker 2+). Muss nicht Cura
      sein. **Nahtlos:** Slicen ist ein Arbeitsbereich in Mechvane selbst
      (eigener Tab im selben Fenster), kein Export/Import, keine zweite
      Anwendung. Das aktuelle Modell geht direkt in die Slicer-Ansicht,
      Parameteränderungen am Teil lösen ein neues Slicen aus, Druckzeit und
      Material stehen sofort da. Ob die Engine dahinter als eigener Prozess
      läuft, ist ein unsichtbares Implementierungsdetail (so arbeitet auch
      Cura mit CuraEngine). Erst recherchieren: CuraEngine, PrusaSlicer/OrcaSlicer (libslic3r)
      und Rust-eigene Slicer vergleichen. Engine als getrennten Prozess
      anbinden (Teil rein, G-Code raus), damit eine spätere Veröffentlichung
      möglich bleibt: die großen Engines sind AGPL-3.0, für den reinen
      Eigenbedarf (privates Repo) wäre auch Einlinken zulässig.
      Vorhanden als Startpunkt: Headless-Kette `/opt/cura-headless/`
      (Skill `3d-druck`) mit den Cura-Profilen des Nutzers, mit einem
      SolidCraft-Export schon erfolgreich getestet.
      *Recherche 2026-10-19* ([Gemini mit Prüfnotiz](docs/research/2026-10-19-slicer-engines-gemini.md)):
      CuraEngine ist der klare Kandidat (Cura-Profile laufen unverändert,
      `LayerOptimized` über Arcus/Protobuf liefert Pfade mit Linientyp und
      -breite für eine eigene Vorschau). Ein praxistauglicher Rust-Slicer
      fehlt, libslic3r kann keine Cura-Profile. Vorschlag: erst CLI + G-Code-
      Parsing (`;TYPE:`), dann CuraEngine als Daemon (`connect`) mit eigenem
      Arcus-Client. Hürde: Das geplante SolidCraft-Plugin-System sieht keine
      eigene Plugin-UI vor, der Slicer-Tab braucht also eine
      UI-Erweiterung upstream oder eine Mechvane-eigene Hülle (ADR 0001).
- [ ] **Regeln/Konfiguration** (iLogic neu gedacht): Parameter-Regeln als
      lesbares Skript plus natürlichsprachliche Regeln, die ein Agent in
      Code übersetzt und testet. **Konfigurationstabellen** wie Onshape: je Eigenschaft eine eigene, unabhängige
      Tabelle (Länge × Werkstoff × Befestigung) statt einer großen Variantentabelle (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)),
      auf SolidCraft `config.*` (`config.rs`, `config_rules.rs`).
- [ ] **Eigene Features als Code** (Nutzer 2026-11-02, Vorbild Onshape FeatureScript, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Fachfeatures
      wie `bolted_connection` als Python mit fester Schnittstelle (Parameter, Eingabeauswahl, Erzeugen, Bearbeiten),
      die im Modellbaum als ein Feature stehen, sich bei Änderungen neu rechnen und vom Agenten wie vom Nutzer
      gleich benutzt werden. Grundlage für die Konstruktionsassistenten und Fachmodule.

### Ergänzungen Phase 2 (Nutzer 2026-11-01, [Vorschlag](docs/research/2026-11-01-roadmap-ergaenzungen-harness-ux.md))

- [ ] **FEM** (Plan Nutzer 2026-10-31, Phase 2, nach v0.1), zwei Stufen mit gemeinsamer Bedienung (Lasten und Lager
      per Flächenauswahl in der eigenen Ansicht, Ergebnis eingefärbt, auch für den Agenten: „Hält der Winkel 200 N?“):
      1. **Eigener linearer Schnellcheck:** ein Bauteil, ein Werkstoff, kleine Verformungen; Vergleichsspannung,
         Verformung, Sicherheitsfaktor gegen Rp0,2 aus der Werkstoffdatenbank. Elemente mit scikit-fem, Lösen mit
         SciPy (beide BSD), quadratische Tetraeder. Vernetzen nicht selbst: fTetWild (MPL-2.0) oder Netgen/Gmsh als
         eigener Prozess. Ergebnis gegen ein Lehrbuchbeispiel und CalculiX prüfen.
      2. **Erweiterte Analyse mit CalculiX** (GPL, eigener Prozess, Lizenzregel siehe Phase 0): Kontakt, Plastizität,
         große Verformungen, Eigenfrequenzen, Temperatur.
- [ ] **Benannte Anschlüsse (Ports)**: Features exportieren benannte Bezüge (`motor_mount_face`, `shaft_axis`),
      im UI als Fangpunkte, für Agent und Gelenke als stabile Anker. Baut auf den Mechvane-Flächennamen auf,
      Grundlage für die adaptive Projektion. Vorbild Onshape (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Mate Connectors als
      Anker, an denen Gelenke ohne Flächenwahl entstehen, dazu **gekoppelte Gelenke** (Higher-Order Mates: Zahnrad,
      Zahnstange, Schraube, Riemen) über SolidCraft-Motion-Links.
- [ ] **Teile vervielfachen** (Nutzer 2026-11-02, Vorbild Onshape Replicate, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): ein eingebautes Teil samt
      Gelenk auf alle gleichen Stellen setzen, etwa eine Schraube in jedes Loch eines Lochbilds oder Gleiter in
      jede Nut. Zusammen mit `bolted_connection` (ganze Verschraubung auf alle Löcher), auf SolidCraft
      `component_matrix`.
- [ ] **Zentrale Variablen** (Nutzer 2026-11-02, Vorbild Onshape Variable Studios, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): eine Variablentabelle
      für mehrere Teile und die Baugruppe (Wandstärke, Spaltmaß, Achsabstand), eine Änderung schlägt auf alle
      verknüpften Dateien durch. Erweitert `/api/params` über die Dateigrenze, Aktualisieren über `update_links`.
- [ ] **Skelett-Modellierung über abgeleitete Geometrie** (Nutzer 2026-11-02, Vorbild Onshape Derived Feature,
      [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)): Skizzen, Flächen oder Koordinatensysteme aus einem Skelett-Teil in andere Teile übernehmen, verknüpft
      und nachgeführt. Deckt den Nutzen von Onshapes Mehrteil-Part-Studios ab, ohne Grundsatz 5 (getrennte
      Dateien) aufzugeben. SolidCraft hat Ansätze in `project.rs` und `component_link.rs`; hängt mit der
      adaptiven Projektion zusammen.
- [ ] **Baugruppe auf Kollisionen und Freigang prüfen**: statisch (Durchdringungen, Schraube zu lang für das
      Sackloch) und entlang der Gelenkbereiche (SolidCraft `joint.sweep`, Kontaktsätze), als MCP-Werkzeug und
      Prüflauf im UI.
- [ ] **Explosionsansicht und Stückliste**: Explosionsrichtungen aus Gelenkachsen und Verschraubungen,
      interaktiv im UI, mit Animation (Vorbild Onshape); Stückliste als Export (später auch in der Zeichnung, Phase 3).
- [ ] **Adaptive Projektion in Baugruppen**: `project_geometry` speichert im Zielteil die semantische Abfrage
      der Quellfläche (`find`) statt Koordinaten, Aktualisieren der Baugruppe zieht nach. Hängt an
      Flächennamen über Verknüpfungen (SolidCraft #3330).
- [ ] **Passungsprüfung über Gelenke**: `check_joints` prüft bei Zylinder-/Drehgelenken Nennmaße und
      `iso_fit`-Passungen von Bohrung und Welle gegeneinander und gegen die Gelenkart. Zahlt auf den
      Benchmark „Lagerstelle“ ein.
- [ ] **Slicer-Prüfung für den Agenten** (`check_slicing`): CuraEngine headless mit dem gewählten Profil,
      Befunde für Stützstruktur, kritische Brücken, zu dünne Wände. Gehört zum Slicer-Modul.
- [ ] **Agenten-Heilung beim CAD-Import**: Platzhalter-Features (Grundsatz 7) lässt ein Agent iterativ mit
      SolidCraft-Befehlen nachbauen, bis Volumen, Schwerpunkt, Hüllquader und Flächenzahl zum Soll-Körper passen.

## Phase 3: Fertigungszeichnungen (ca. 6–9 Monate)

Das aufwendigste Modul und Pflicht für Werkstatt-Teile.

*Baustein 2026-10-20:* [CADCraft](docs/research/2026-10-20-cadcraft.md)
(ArtCraft, 2D nach AutoCAD-Art, MIT/Apache, gleiche egui-Version) bringt
Blatt, Bemaßung mit ISO-Stilen, Schraffur, Blöcke für das Schriftfeld und
PDF-Plot mit. Versuch: Ansicht aus SolidCraft als DXF, in CADCraft bemaßt und
als PDF geplottet, geht, aber nur mit Polylinien statt echter Kreise und
ohne Bezug zum 3D-Modell. Die exakten Ansichten müssen von SolidCraft kommen
(#860).

- [ ] Ansichten (Basis, Projektion, Schnitt, Detail) mit Hidden-Line-Removal
- [ ] Bemaßung, Passungen, Gewindedarstellung nach ISO, Oberflächenzeichen,
      Form- und Lagetoleranzen
- [ ] Schriftfeld DIN EN ISO 7200, Stückliste und Positionsnummern. Stückliste live mit dem Modell gekoppelt,
      in beide Richtungen (Vorbild Onshape, Nutzer 2026-11-02): SolidCraft `assembly.bom.get`/`set`.
- [ ] **Agent leitet Zeichnung ab**: fertigungsgerecht bemaßt, prüft auf
      Über- und Unterbemaßung
- [ ] PDF/DXF-Export
- [ ] **Semantische 3D→2D-Vererbung** ([Vorschlag](docs/research/2026-11-01-roadmap-ergaenzungen-harness-ux.md)): projizierte Kanten behalten ihr erzeugendes Feature und dessen
      Daten (Gewinde, Tiefe, Passung, Schweißnaht), damit der Agent fertigungsgerecht bemaßt statt Geometrie
      zu raten.

## Später / bewusst nicht geplant

Später als Plugin, wenn Bedarf da ist: Bewegungssimulation, Rendering (über Blender), CAM-Brücke,
schlanke Freigaben (Revisionsbuchstabe und Status „in Arbeit/freigegeben“ als Git-Tag, Vorbild Onshape Release
Management, Nutzer 2026-11-02).

Nicht geplant: T-Splines, Rohrleitungen, Kabelbaum, BIM/Revit, Vault-artiges PDM
(Git reicht), iParts (ersetzt durch Konfigurationstabellen).

## Größte Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| Plattform (SolidCraft) ändert sich schnell oder stirbt | Phase 0 prüft Governance; eigene Plugins dünn halten, Logik in plattformneutralen Crates |
| Topologisches Naming bricht bei Änderungen | nur Plattformen mit Lineage-Naming; Testkorpus mit Parameteränderungen |
| Zeichnungsmodul unterschätzt | erst DXF-Flächenexport, Zeichnungen erst in Phase 3 |
| Zeit: Freizeitprojekt mit begrenzter Kapazität | kleine, einzeln nutzbare Meilensteine; jeder Phase-1-Baustein hilft schon beim eigenen Konstruieren |
| Angaben aus der Recherche ungenau | Gemini-Recherche ist Rohmaterial; Zahlen und Features vor Entscheidungen selbst prüfen |
