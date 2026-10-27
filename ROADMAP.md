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
- [ ] SolidCraft praktisch testen: Desktop/Web-App, `solidcraft-cli mcp` an
      Claude Code anbinden, 3–5 eigene Referenzteile per Agent konstruieren.
      *Stand 2026-10-19:* MCP angebunden (`.mcp.json`), 4 Referenzteile
      (Flansch, Druckgehäuse, Blechwinkel, Scharnier) gebaut und vermessen.
      Eingebundene `mcp__solidcraft__*`-Tools nach Neustart geprüft
      (Flansch, Abweichung 6,6e-6). Offen: GUI/Web-App.
- [x] Prüfen: Wie gut ist der MCP-Server für Agenten (Fehlermeldungen,
      Topologie-Abfragen, Snapshots)? Ergebnis im
      [Phase-0-Bericht](docs/research/2026-10-phase0-solidcraft.md).
- [x] Prüfen: Wie weit sind Zeichnungen (`docs/drawing-foundations.md`),
      Baugruppen, Blech, Plugins (#1221)? Baugruppen und Blech tragen
      (Referenzteile). Zeichnungen: M11 zurückgestellt, nur Ansichts-DXF.
      Plugins: nur Entwurf, kein Code, keine eigene Plugin-UI vorgesehen.
      Siehe [Bericht](docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
- [ ] Prüfen: Lässt sich in SolidCraft ein Inventor-artiger Feature-Baum
      statt der Fusion-Timeline umsetzen (Grundsatz 5)? Was zeigt der
      vorhandene Browser, lässt sich die Timeline-Leiste ersetzen, geht das
      als Plugin/UI-Modul oder nur per Fork? Fließt direkt in ADR 0001 ein.
      *Stand 2026-10-19 (aus dem Code):* Die Einstellung `timeline_left`
      zeigt den Verlauf senkrecht über dem Browser, mit Ordnern und
      Rollback-Balken, an dem neue Features eingefügt werden. Optisch kommt
      das nahe, es fehlen Skizzen unter ihrem Feature und ein gemeinsamer
      Baum. Offen: in der laufenden App ansehen.
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
   ui --demo`; *unter Linux fertig 2026-10-27*, frische venv mit leerem Cache geprüft, Windows offen → D), C Dateien in der UI öffnen: Ordner statt einer Datei, Auswahl und „Neues Bauteil“ im
   Modus „Modellieren“ (*fertig 2026-10-26*: `python3 -m mechvane.ui <ordner>`, `/api/project`, `/api/open`, `/api/new`), D Windows-Test auf dem Surface. PyPI: *Alpha `0.1.0a1` seit
   2026-10-27* (Nutzerentscheid, nur Linux getestet; erster Upload mit Token, danach Trusted Publishing
   per Tag `v*`). Stabile Version, wenn B auf Windows und Linux läuft.
1b. Handbedienung: SolidCraft-Web-App (Release-Asset `solidcraft-web-*.zip`) in die UI einbetten,
   Modi „Modellieren“ und „Prüfen“, Speichern zurück an Mechvane (Nutzer-OK 2026-10-24, zuerst Test).
   *Test bestanden und umgesetzt 2026-10-25* (`/model`, Bauteile und Baugruppen mit verknüpften
   Teilen). Befund anklicken wählt die Fläche in der App aus (`select.set`, *fertig 2026-10-26*). Offen: Befunde
   auch in der Demo nach dem Speichern (bräuchte die Prüfungen im Browser).
2. UI Stufe 2: Fläche anklicken, Chatfenster mit dem Agenten **mit Spracheingabe** (Point and speak,
   Grundsatz 6: Auswahl plus gesprochener Auftrag gehen zusammen an den Agenten), Rückgängig
   (2–3 Wochen). Vor dem Umsetzen entwerfen: Anbindung an den Agenten und Spracherkennung
   (Browser-Spracheingabe oder Whisper), Deutsch und Fachbegriffe wie „Fase 1 × 45°“, „M6“
3. Parameter im Formular, Öffnen/Speichern, Messen, Schnitt (1–2 Wochen)
4. Praxistests mit dem Nutzer, Fehler beheben, Windows, Installation in einem
   Schritt (2–3 Wochen)

Nicht in v0.1: ein eigener Skizzierer und eigene Feature-Dialoge (4–6 Monate). Von Hand
modelliert wird in der eingebetteten SolidCraft-App (1b, geht mit Mechvane-Dateien sauber,
2026-10-25). Nach den ersten Praxistests entscheiden, ob mehr nötig ist. Richtung für alle
UI-Stufen: Bedienung möglichst nah an Inventor (Grundsatz 10).

- [ ] Abgleichliste Inventor ↔ SolidCraft ↔ Mechvane (Register, Befehlsnamen, Tastenkürzel,
      Browser, Dialoge), Recherche an Gemini, danach entscheiden, was über SolidCraft-
      Einstellungen/Plugins geht und was eine eigene Oberfläche braucht.

**Prüfpunkt Sprache (nach v0.1, spätestens Januar 2027, Nutzer-OK 2026-10-24):** Mechvane bleibt
bis v0.1 Python (ADR 0001: „Rust, sobald die Schnittstelle steht“). Dann neu entscheiden, früher,
falls das SolidCraft-Plugin-System (#1221, WASM/WIT) fertig ist. Für Rust spricht: Prüfungen
als SolidCraft-Plugin, ein einzelnes Programm ohne Python. Dagegen: Umbau, langsame Builds
auf dem Steuer-Container; ein Paket mit eingebautem Python löst die Installation auch.

- [ ] **Desktop-App** (Grundsatz 12). Schritt 1 für v0.1, zusammen mit 1a B: three.js und alle
      Abhängigkeiten mitliefern (offline), `mechvane ui` öffnet ein eigenes App-Fenster
      (Chrome/Edge `--app=`), Startmenü-Verknüpfung unter Windows. Schritt 2 nach v0.1: echte
      Desktop-App mit Installer für Windows und Linux; vorher Recherche der Hüllen (Gemini) und
      ein Test, ob die SolidCraft-Web-App darin läuft. Entscheidung zusammen mit dem Prüfpunkt
      Sprache (spätestens Januar 2027).

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
- [ ] **Bohrungsassistent mit Verschraubung**: Schraube + Scheibe + Mutter
      + passende Bohrung in allen Bauteilen (Inventor „Verschraubung“).
      [Spezifikation](docs/research/2026-10-20-bohrungsassistent-spec.md).
      *Erster Stand 2026-10-20:* `bolted_connection` für Durchgang (mit
      Senkung), Sackloch und Ruthex-Einsatz. Senkdurchmesser DIN 974-1 (Reihe 1 und 5)
      seit 2026-10-23 an der Quelle geprüft. Muster (Teilkreis, Rechteck), Auflisten, Ändern und Löschen seit 2026-10-23.
      Senkkopfschrauben ISO 10642 mit 90°-Kegelsenkung nach DIN 74 Form F / ISO 15065
      unterstützt (`head="countersunk"`, quellengeprüft 2026-10-23).
      ISO-286-Passungen als `iso_fit` (Grenzabmaße, Spiel/Übermaß) seit 2026-10-23;
      offen: Passung als Attribut an Bohrung und Welle, Lagersitze in `standard_part`.
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
- [ ] Referenzteile-Korpus mit Sollwerten anlegen (`tests/reference/`).
      *Begonnen 2026-10-19:* 7 Teile mit `check.py` (seit 2026-10-23 Welle, Rohrhalter, Rippenplatte), weitere aus dem Alltag
      ergänzen (Druckteile, Vorrichtungen).

## Phase 2: Fachmodule als Plugins (ca. 4–6 Monate)

Reihenfolge nach Nutzen für den eigenen Alltag:

- [ ] **Gestell-Generator** für Aluprofile (Item/Bosch 20/30/40er Nut) und
      Stahlprofile, mit Längenliste.
- [ ] **Blech-Ergänzungen** (falls upstream noch Lücken): Blechregeln-
      Bibliothek, Abwicklungs-DXF für Laser-Dienstleister.
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
      Code übersetzt und testet.

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
- [ ] Schriftfeld DIN EN ISO 7200, Stückliste und Positionsnummern
- [ ] **Agent leitet Zeichnung ab**: fertigungsgerecht bemaßt, prüft auf
      Über- und Unterbemaßung
- [ ] PDF/DXF-Export

## Später / bewusst nicht geplant

Später als Plugin, wenn Bedarf da ist: FEM-Brücke (CalculiX/PrePoMax),
Bewegungssimulation, Rendering (über Blender), CAM-Brücke.
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
