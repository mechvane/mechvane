# Roadmap Mechvane

Stand 2026-11-23 (Umschwenk zu Harness und Plugin für SolidCraft, entschieden 2026-11-20, präzisiert am 2026-11-23). Ursprüngliche Grundlage: [Gemini-Deep-Research](docs/research/2026-10-19-inventor-funktionsumfang-gemini.md)
(Teil A: Inventor-Funktionsumfang mit Einstufung KERN/HÄUFIG/NISCHE, Teil C:
Architektur, MVP, Risiken). Zeitangaben sind grobe Größenordnungen für ein
Freizeitprojekt mit KI-Unterstützung, keine Zusagen.
Verlaufsnotizen und erledigte Zwischenschritte: [docs/roadmap-verlauf.md](docs/roadmap-verlauf.md).

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
6. **Point and speak** (Nutzerwunsch 2026-10-20, sehr wichtig): Der Claude-Agent sitzt in der SolidCraft-App (Agent-Chat bzw.
   Plugin); markierte Kanten/Flächen mit stabilen Flächennamen und gesprochener Auftrag gehen zusammen an ihn und werden zu
   editierbaren Features im Baum. Der Ort wechselt seit dem Umschwenk (Nutzer 2026-11-23) von der eigenen Oberfläche in die
   SolidCraft-App und ihre Plugins, der Wunsch bleibt.
7. **Möglichst viele Dateiformate importieren** (Nutzerwunsch 2026-10-20; **seit 2026-10-31: Umstieg ohne Verlust**):
   alle gängigen CAD-Systeme editierbar mit Feature-Verlauf, Skizzen, Parametern, Baugruppen-Abhängigkeiten und
   Eigenschaften (SolidCraft-Lizenzregel beachten). Fehlende Feature-Typen werden gebaut; bis dahin bleiben sie als
   Platzhalter mit Originaldaten und Körper erhalten, samt Bericht je Feature.
8. **Renderanbindung an Blender** (Nutzerwunsch 2026-10-20): Bauteil oder Baugruppe mit Materialien und Kamera per
   glTF-/USD-Export und Szenen-Skript als Hintergrundjob an Blender (Cycles) übergeben und das Bild in Mechvane zeigen.

*(Grundsatz 9 fehlt in der Zählung und bleibt unbesetzt; Grundsatz 12 „Desktop-App“ entfiel am 2026-11-23, Wortlaut im [Verlauf](docs/roadmap-verlauf.md).)*

10. **Bedienung am Ende möglichst nah an Inventor** (Nutzerwunsch 2026-10-26, Endziel), **optisch aber dunkler
    und schicker** (dunkles Farbschema, ruhige Gestaltung): Multifunktionsleiste mit Inventor-Registern, -Befehlen und
    -Kürzeln, Kontextmenüs, Mini-Werkzeugleiste, Modellbrowser links, ViewCube, getrennte Bauteil-/Baugruppen-/Skizzen-
    Umgebungen und passende Dialoge. Weg: Ribbon-Plugins in der SolidCraft-App (v0.2, #1221) statt einer eigenen
    Oberfläche (Umschwenk, Nutzer 2026-11-23); Abgleich mit Fusion:
    [Entscheidungsliste](docs/research/2026-10-26-fusion-vs-inventor-liste.md).
11. **Testen an echten Teilen** aus dem eigenen Alltag (Druckteile für den
    Ultimaker, Vorrichtungen, Blechteile), Ergebnisse gegen Fusion/FreeCAD
    vergleichen (Volumen, Schwerpunkt, Bounding-Box).

## Phase 0: Erkunden und entscheiden (abgeschlossen)

Alle Punkte erledigt. Ergebnis: [ADR 0001](docs/adr/0001-grundlage-solidcraft.md) (SolidCraft als Grundlage, Mechvane als eigene
Schicht, kein Fork, kein eigener Kernel); die Einzelpunkte mit Befunden stehen im [Verlauf](docs/roadmap-verlauf.md).

## Phase 1: Agenten-Workflow und erste Inventor-Bausteine (ca. 2–3 Monate)

Seit dem Umschwenk (2026-11-20) liegt der Schwerpunkt auf Harness und Plugins für SolidCraft; die Web-UI ist eingefroren.
Neue Ideen kommen sofort an ihre Phase in die ROADMAP; umgesetzt werden sie, wenn die Phase dran ist, außer der Nutzer sagt
ausdrücklich „jetzt“. Der native CAD-Import bleibt Langzeitziel (#32/#33 gesichtet, neue Aufträge erst nach v0.1).
Der frühere Meilenstein „Ende Dezember 2026“ und der Fokus vom 2026-10-31 stehen im [Verlauf](docs/roadmap-verlauf.md).

**Schnitt von v0.1 (Nutzer-OK 2026-11-10, neu gefasst 2026-11-22 nach der Umschwenk-Entscheidung vom 20.11., präzisiert 2026-11-23).**
v0.1 zeigt, dass Mechvane als Maschinenbau-Schicht und Harness an der laufenden SolidCraft-App trägt: Agent und
Nutzer arbeiten am selben Fenster, Befunde haben Quellen, die Installation ist kurz. Die Web-UI ist eingefroren (die
Live-Demo bleibt unter `/demo/` erreichbar), Rust-Plugins und Ribbon gehören zu v0.2. Begründung und Entscheidungen:
`docs/strategie/2026-11-18-weg-neben-solidcraft.md`, Abschnitt „Entscheidung“ samt Nachtrag vom 2026-11-23.

**v0.1 = U1 (`--connect`, #181) + Abnahme-Arbeit (Prüfen am offenen Fenster #182, Verschraubung #183, Installation #184) +
U5 (Auftritt und Release).** U2–U4 (Plugin-Gerüst, Prüfungen, Verschraubung und Normteile als Rust-Plugin) sind **v0.2**
hinter dem Durchstich-Tor. Die Probe P5 (Lochkreis ohne Sondierschnitte, Opus) kommt nach U1 und vor dem Durchstich-Tor.
Ein Zieldatum gibt es nicht mehr (früher „Ende Dezember 2026“); der Termin wird nach U1 neu bewertet. Abgenommen wird an
vier Prüfungen, die kein Modell entscheidet:
1. **Konstruieren:** eine feste Konstruktionsaufgabe (`winkel_verschraubung`, von Hand gemessen, Vorwert 80 headless am
   2026-11-23) erreicht über `--connect` (gegen die offene App) mindestens 80 von 100 Punkten.
2. **Prüfen am offenen Fenster:** `mechvane check` läuft gegen das offene Fenster, mit Quellen und dem gleichen
   Ergebnis wie ohne Fenster.
3. **Verschraubung:** entsteht in einem Aufruf und lässt sich in einem Aufruf zurücknehmen (Mechvane merkt sich die
   Schritte; Entscheidung 2026-11-23). Der echte Einzelschritt im Rückgängig-Verlauf von SolidCraft als Rust-Plugin ist v0.2.
4. **Installation:** ein Neuling installiert und baut den Flansch in unter 15 Minuten.

Die frühere Abnahme „Abdeckung“ (jeder Befehl in der Oberfläche) entfällt; `tools/acceptance.py` misst sie nur noch
als Information. 0.1.0a24 war die letzte Alpha der App-Linie (a25 als Ausnahme). Welche SolidCraft-Version v0.1 trägt
(0.43 oder 0.47; Plugin-Host und Panel-Signal ab 0.45, die Web-UI bleibt auf 0.43), klärt U1 (#181). Direktbearbeitung,
Upstream-PRs und Spracheingabe folgen nach v0.1.

Bis v0.1 fehlt noch:
- [ ] **U1: `--connect` und Lesemodus „aktives Fenster“** (#181): `Session` hängt sich an die offene SolidCraft-App, Werkzeuge
      ohne Dokumentpfad lesen das offene Design, Skills nachziehen, Versionsfrage 0.43/0.47 klären. Voraussetzung für
      Abnahme 1 und 2.
- [ ] **Abnahme 1 Konstruieren** (nach U1): `winkel_verschraubung` über `--connect` von Hand messen, mindestens 80 von 100.
      *Stand 2026-11-23:* Vorwert 80 headless (A9, Befund #178), noch nicht bestanden.
- [ ] **Abnahme 2 Prüfen am offenen Fenster** (#182): `mechvane check` gegen das offene Fenster, mit Quellen, gleiches
      Ergebnis wie ohne Fenster (`mechvane/cli.py` kennt bisher nur `setup`, `ui`, `shortcut`, `mcp`).
- [ ] **Abnahme 3 Verschraubung** (#183): in einem Aufruf erzeugt und in einem Aufruf zurückgenommen.
- [ ] **Abnahme 4 Installation** (#184): ein Neuling installiert und baut den Flansch in unter 15 Minuten
      (`docs/installation-windows.md` neu schreiben).
- [ ] **U5 Auftritt und Release**: README, Website, Roadmap und Screenshots auf den Umschwenk bringen (Name nur „Mechvane“,
      Namensfrage SolidCraft #20008), stabile Version 0.1.0 auf PyPI, wenn alles oben erledigt ist und Linux und Windows
      laufen (Release-Ablauf in `CLAUDE.md`).

Der Rest der früheren Liste (Web-UI, Befehlsdialog, Praxistests, Grafik-Overhaul, App-Fenster) ist eingefroren oder erledigt und
steht im [Verlauf](docs/roadmap-verlauf.md).

**Prüfpunkt Sprache (entschieden 2026-11-20 durch den Umschwenk):** Stufe 1 bleibt Python (Harness an der App, U1), Stufe 2
sind Rust-Plugins in SolidCraft (v0.2) nach dem Durchstich-Tor. Der frühere Wortlaut (Entscheidung 2026-11-10 und Prüfpunkt
vom 2026-10-24) steht im [Verlauf](docs/roadmap-verlauf.md).

Weitere Bausteine von Phase 1:

- [ ] **Website mechvane.dev** (Nutzerwunsch 2026-10-29): online, Startseite am 2026-11-23 neu (Fokus SolidCraft-Plugin und
      Harness). Offen: Auftritt mit U5, Archiv-Hinweis in `/demo/` (`tools/build_demo_site.py`), Namensfrage #20008
      (`docs/website/ARGON-PROMPT.md`, `docs/website/FAKTEN.md`, `website/`).
- [x] **Mechvane-Schicht als MCP-Server** (nach ADR 0001): Python-MCP für getrennte Dateien, `update_links`,
      Skizzenregel, Unterbaugruppen und semantische Abfragen ([Doku](docs/mechvane-mcp.md)). *Stand 2026-11-23:* Grundbau
      fertig und im Einsatz; `--connect` an die offene App gehört zu U1 (#181).
- [ ] **Flächennamen über Verknüpfungen** (#3330, früher Blocker für getrennte Dateien): Upstream seit 2026-10-24 geschlossen,
      der Bohrungsfall ist seit SolidCraft 0.22 behoben (`tests/mechvane/check.py`, Test „new hole before it“). Die Reparatur
      in `mechvane/links.py` bleibt für Planflächen (Test „Planar face repair“).
- [ ] **Konstrukteurs-Agent**: iterativ konstruierender Agent mit Konstruktionsregeln (`.claude/skills/konstrukteur`,
      [Bericht](docs/research/2026-10-20-konstrukteur.md)). *Stand 2026-11-23:* `check_design` (`fdm_0.4`, `cnc_alu`) mit Quellen
      je Befund (#120) und die Skills `konstrukteur` und `varianten` laufen; offen: Brückenerkennung, wählbare
      Druckrichtung, genauerer Randabstand (#170).
- [ ] **Normteile-Generator** (prozedural): ISO 4762/DIN 912, ISO 4032, ISO 7089, Gewindeeinsätze, Kugellager 6000er.
      *Stand 2026-11-23:* `standard_part` bis 6005 sowie ISO 10642 und ISO 4017 fertig ([Bericht](docs/research/2026-10-20-normteile-gemini.md));
      offen: Review durch zweites Modell und weitere Reihen.
- [x] **Bohrungsassistent mit Verschraubung**: Schraube, Scheibe, Mutter und passende Bohrung
      ([Spezifikation](docs/research/2026-10-20-bohrungsassistent-spec.md)). *Stand 2026-11-02:* Durchgang/Senkung/
      Kegelsenkung, Sackloch, Ruthex, Muster, ISO 286, Kollision (#34, [Praxistest 6](docs/research/2026-10-31-praxistest-6.md)); offen: Passung als Attribut, Lagersitze.
- [ ] **Eigener offener Regelkatalog** (Nutzerwunsch 2026-10-20): belegte Werte nach [ADR 0002](docs/adr/0002-wissenskatalog-format.md)
      samt Quellenprüfung und [Plan](docs/research/2026-10-20-wissenskatalog-plan.md). *Stand 2026-11-23:* `katalog/` gemergt,
      121 Einträge im Wheel 0.1.0a25; der Dauerauftrag (#168, #173, Themenliste `katalog/backlog.md`) liefert nachts neue
      Einträge; offen: Abgleich BOLTS/FreeCAD/cq_warehouse.
- [ ] **Werkstoffdatenbank** (Nutzerwunsch 2026-10-29): Kennwerte unter `katalog/eintraege/werkstoffe/` ([Bericht](docs/research/2026-10-29-werkstoffe-flash.md)).
      *Stand 2026-11-03:* 16 Werkstoffe, τ_B (#16), `tools/katalog_to_solidcraft.py`, `dickenbereiche`; offen: 3× τ_B, alle Regeln, `physical_card`.
- [ ] **Verfahrensregeln ausbauen** (Nutzer 2026-11-01, Gemini-Vorschlag): je Fertigungsprofil weitere Regeln mit Quelle
      (FDM: liegende Bohrungen als Tropfenform, Einpressmuttern; CNC: Mindest-Innenradien, Bohrtiefe, Hinterschnitte).
- [ ] **Regeln aus Werkstoffkennwerten herleiten** (Nutzerwunsch 2026-10-29): Formeln statt Tabellen ([Recherche](docs/research/2026-10-29-regeln-aus-kennwerten-flash.md)).
      *Stand 2026-10-29:* Recherche (#14) mit Kernformel gemergt; offen: Kennwerte (`τ_B`, `Rp0,2`, `p_G`) und Umsetzung.
- [ ] **Werkstoff zuweisen über Katalog und Plugin (v0.2+)** (Nutzerwunsch 2026-10-29, früher „Material- und Darstellungseditor“):
      Werkstoff und Aussehen je Bauteil/Fläche ([Darstellungsformat](docs/research/2026-10-29-darstellungsformat-flash.md)).
      *Stand 2026-11-23:* [ADR 0004](docs/adr/0004-darstellungsformat.md) (glTF-PBR) angenommen; offen: Zuweisung über den Katalog
      bzw. als Plugin in der SolidCraft-App (statt eigenem Editor).
- [ ] Referenzteile-Korpus mit Sollwerten anlegen (`tests/reference/`).
      *Begonnen 2026-10-19:* 7 Teile mit `check.py` (seit 2026-10-23 Welle, Rohrhalter, Rippenplatte), weitere aus dem Alltag
      ergänzen (Druckteile, Vorrichtungen).

### Nach v0.1: Harness und Zusammenarbeit (Nutzer 2026-11-01, [Vorschlag](docs/research/2026-11-01-roadmap-ergaenzungen-harness-ux.md))

- [ ] **Direktbearbeitung wie Inventor** (Nutzer 2026-11-05; nach v0.1): Flächen verschieben,
      versetzen, drehen, löschen, Bohrungs-Ø ändern (STEP). *Stand 2026-11-23:* #745 ab SolidCraft 0.40 (`solidcore`) behoben;
      offen: STEP-Test, Umsetzung als Befehl bzw. Plugin in der SolidCraft-App, #10884 ([Testbericht](docs/research/2026-11-06-solidcore-testbericht-3992.md)).
- [ ] **An SolidCraft per PR mitarbeiten** (Nutzer 2026-11-05, [ADR 0001](docs/adr/0001-grundlage-solidcraft.md)
      Nachtrag): Grenze laut Umschwenk-Entscheidung 5: Schnittstellen-Fragen und Geometrie-Helfer ja, der Katalog nein.
      Colab-Pro-Build einrichten (#63, `cargo xtask ci`), kleinen PR außerhalb des Kernels wählen; Kernel-Fälle
      (#745, #10884) nach solidcore (#3992). Jeder PR nur mit Nutzer-OK.
- [ ] **Nutzersperren**: Parameter, Maße, Features und Funktionsflächen „vom Nutzer festgelegt“ (Schloss im Baum,
      Metadaten); Agent bekommt sprechende Ablehnung, Keep-Out-Flächen schützen.
- [ ] **Herkunft von Maßen**: Berechnete Maße (Regelkatalog, Kennwertformeln, `bolted_connection`) schreiben Herleitung
      und Quelle in den Parameterkommentar; als Hinweis im Befund bzw. in der SolidCraft-App.
- [ ] **3D-Diff bei Agenten-Änderungen**: Geistervolumen, Baum-Markierung, einzelne Änderungen annehmen oder verwerfen
      über `timeline.dependents` und `inspect.compare` (Vorbild Onshape, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)).
- [ ] **Versionen, Branches und Varianten** (Nutzer 2026-11-01): benannte Stände mit 3D-/Feature-Diff, Varianten-Branches
      und Feature-Merge; Vorstufe Parametervarianten (#108, `docs/strategie/2026-11-14-varianten-skill.md`).
- [ ] **Modell je Auftrag wählen** (Nutzer 2026-11-02): Regel-Einstufung Haiku/Sonnet/Opus (optional mit Jev),
      Aufstufen bei Fehlschlag. Der Sitzungswechsel lief über ACP `session/set_model` im Chat der eingefrorenen Web-UI; künftig
      Sache des Agenten-Hosts der SolidCraft-App (offen, wie). *Stand 2026-11-02:* Modell wird im
      Protokoll (`agent_session`) erfasst; offen: Schwellen messen, Jev-Vergleich und Umschaltung.
- [ ] **Kommentare und Aufgaben am Modell** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      Notizen, Befunde und Agenten-Aufträge als Pins an Flächen/Kanten/Features in Mechvane-Metadaten.
- [ ] **Dem Agenten folgen** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      Ansicht folgt live Kamera, Auswahl und Feature des Agenten (abschaltbar).
- [ ] **Mensch und Agent gleichzeitig am Modell** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      Agenten-Änderungen zunächst als Vorschlag auf Kopie, bis der Kern gleichzeitiges Bearbeiten trägt.
- [ ] **Webhooks** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      Ereignisse („Teil gespeichert“, „Prüfung fehlgeschlagen“, „Agent fertig“) an URLs melden.
- [ ] **Fehler übersetzen, Rest** (Nutzer 2026-10-31): Stufen 1–3 sind fertig (`sc_errors.py`, `sc_locate.py`,
      `feature_errors`, #38, #42); offen: Baugruppen („lumps“ #34), Skizzenfehler und die Markierung in der Ansicht
      (`location.at`), die letzte erst mit der SolidCraft-App bzw. dem Plugin.
- [ ] **Katalogseite auf mechvane.dev** (2026-11-10): Befunde zeigen Regel, Wert, Quelle und Zitat schon (#120, #123);
      offen ist die eigene Seite für den Katalog, nach v0.1 passend zum Auftritt.

## Phase 2: Fachmodule als Plugins (ca. 4–6 Monate)

Reihenfolge nach Nutzen für den eigenen Alltag:

- [ ] **Native Dateien aller großen CAD-Systeme importieren, mit Feature-Verlauf** (Nutzerentscheidung 2026-10-31):
      Bauteile/Baugruppen mit Verlauf, Skizzen, Parametern und Abhängigkeiten im Clean Room ohne GPL importieren;
      Platzhalter statt Verlust, Abgleich gegen gespeicherten Körper ([cadmpeg](https://github.com/cadmpeg/cadmpeg)).
      *Stand 2026-11-03:* Zielformate (Inventor, FreeCAD, Solid Edge/Works, Fusion, NX, CATIA, Creo, PMI) und
      cadmpeg-Arbeitsteilung festgelegt; offen: Messlauf #32 und Abbildungsschicht.
- [ ] **Gestell-Generator** für Aluprofile (Item/Bosch 20/30/40er Nut) und Stahlprofile, mit Längenliste.
- [ ] **Schweißen** (Nutzerwunsch 2026-10-29): Schweißnähte als Features, Schweißbaugruppen, ISO-2553-Symbole und
      eigenes Nahtaussehen; Grundlagen recherchiert (#19, [Schweißen im CAD](docs/research/2026-10-30-schweissen-grundlagen-flash.md)).
- [ ] **Blech-Ergänzungen**: Blechregeln-Bibliothek, Abwicklungs-DXF, 3D und Abwicklung live nebeneinander sowie
      Volumenkörper in Blech umwandeln (`sheet_convert`, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)).
- [ ] **Konstruktionsassistenten**: Welle (Absätze, Nuten, Sicherungsringe), Stirnrad, Zahnriemen-Trieb, Passfedern, mit Berechnung.
- [ ] **Slicer-Modul (grafisch)** (Nutzerwunsch 2026-10-19): nahtloser Slicer-Tab (Platzierung, Profile, Schichtvorschau,
      OctoPrint), Engine als getrennter Prozess ([Recherche](docs/research/2026-10-19-slicer-engines-gemini.md)).
      *Stand 2026-11-17:* CuraEngine gewählt (Start `/opt/cura-headless/`); Upstream RFC 0015 (PR #18727) plant „Design changed“-Listener; offen: CLI/Arcus und Plugin-UI (ADR 0001).
- [ ] **Regeln/Konfiguration** (iLogic neu gedacht): lesbares Regel-Skript plus natürlichsprachliche Regeln sowie
      unabhängige Konfigurationstabellen auf SolidCraft `config.*` ([Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)).
- [ ] **Eigene Features als Code** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      Fachfeatures als Code-Generatoren mit Formular, Bearbeiten und Neubau ([Notiz](docs/research/2026-11-11-solidcraft-plugin-rfc-0002.md)).
      *Stand 2026-11-11:* SolidCraft RFC 0002 (WASM, #1221, PR #15110) in Phase 1; offen: Joints/eingefügte Teile
      (Phase 3). Die Wahl Python oder WASM-Plugin ist entschieden (Umschwenk 2026-11-20): Stufe 1 Python-Harness, Stufe 2 Rust-Plugins.

### Ergänzungen Phase 2 (Nutzer 2026-11-01, [Vorschlag](docs/research/2026-11-01-roadmap-ergaenzungen-harness-ux.md))

- [ ] **FEM** (Plan Nutzer 2026-10-31): gemeinsame Bedienung für (1) eigenen linearen Schnellcheck (scikit-fem/SciPy,
      fTetWild/Netgen/Gmsh) und (2) erweiterte Analyse mit CalculiX (GPL, eigener Prozess). *Stand 2026-11-20:* Vor dem
      Start [FieldCraft](docs/research/2026-11-20-fieldcraft.md) prüfen (Tangency Labs 0.8.1, MIT/Apache-2.0, Rust, feste
      Flächennamen; Entscheidung nach Probe).
- [ ] **Benannte Anschlüsse (Ports)**: Features exportieren benannte Bezüge als Fangpunkte und Gelenk-Anker (Mate
      Connectors) samt gekoppelten Gelenken über Motion-Links ([Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)).
- [ ] **Teile vervielfachen** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      eingebaute Teile samt Gelenk über `component_matrix` und `bolted_connection` auf gleiche Stellen setzen.
- [ ] **Zentrale Variablen** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      gemeinsame Variablentabelle über Dateigrenzen hinweg (`update_links`).
- [ ] **Skelett-Modellierung über abgeleitete Geometrie** (Nutzer 2026-11-02, [Onshape-Recherche](docs/research/2026-11-02-onshape-features-flash.md)):
      Skizzen/Flächen/Koordinatensysteme verknüpft aus Skelett-Teil übernehmen (`project.rs`, `component_link.rs`).
- [ ] **Baugruppe auf Kollisionen und Freigang prüfen**: statisch und entlang der Gelenkbereiche (`joint.sweep`, Kontaktsätze).
- [ ] **Explosionsansicht**: interaktive Explosion mit Animation aus Gelenkachsen. Die Stückliste ist fertig
      (`bill_of_materials`, #49).
- [ ] **Adaptive Projektion in Baugruppen**: `project_geometry` speichert semantische `find`-Abfrage (hängt an #3330).
- [ ] **Passungsprüfung über Gelenke**: `check_joints` prüft Nennmaße und `iso_fit`-Passungen gegeneinander.
- [ ] **Slicer-Prüfung für den Agenten** (`check_slicing`): CuraEngine headless mit dem gewählten Profil,
      Befunde für Stützstruktur, kritische Brücken, zu dünne Wände. Gehört zum Slicer-Modul.
- [ ] **Agenten-Heilung beim CAD-Import**: Platzhalter-Features (Grundsatz 7) lässt ein Agent iterativ mit
      SolidCraft-Befehlen nachbauen, bis Volumen, Schwerpunkt, Hüllquader und Flächenzahl zum Soll-Körper passen.

## Phase 3: Fertigungszeichnungen (ca. 6–9 Monate)

Das aufwendigste Modul und Pflicht für Werkstatt-Teile.

*Stand 2026-10-20:* [CADCraft](docs/research/2026-10-20-cadcraft.md) (2D, ISO-Stile, PDF-Plot) als Baustein getestet;
exakte Ansichten müssen von SolidCraft (#860) kommen.

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
| v0.1 wächst schneller, als es schrumpft | fester Schnitt (neu gefasst 2026-11-22/23) mit vier Abnahmeprüfungen; Neues kommt an seine Phase, nicht in v0.1 |
