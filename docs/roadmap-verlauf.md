# Roadmap-Verlauf Mechvane

Ausgelagerte Verlaufsnotizen, erledigte Zwischenschritte und datierte Detailstände aus [ROADMAP.md](../ROADMAP.md), gesammelt unter denselben Überschriften. Offene Planpunkte und Checkboxen stehen ausschließlich in `ROADMAP.md`.

## Grundsätze

6. **Point and speak:** Ausgangspunkt: SolidCraft hat ein Agent-Chat-Panel (`docs/agent-chat.md`, Claude Code als Agent, nur Desktop). Ob es die Auswahl mitgibt, war offen, Sprache fehlte.
7. **Möglichst viele Dateiformate importieren:** SolidCraft liest schon STEP, IGES, FreeCAD (`.FCStd`), Rhino (`.3dm`, über cadmpeg), 3MF, STL, OBJ und glTF, CADCraft dazu DXF/DWG (2D). **Seit 2026-10-31 (Nutzer): Umstieg ohne Verlust.** Pflicht sind Feature-Verlauf, Skizzen mit Abhängigkeiten, Parameter mit Ausdrücken, Baugruppen-Abhängigkeiten und Eigenschaften; fehlende Feature-Typen bleiben bis zum Nachbau als Platzhalter mit Bericht je Feature.
8. **Renderanbindung an Blender:** SolidCraft hat eigene Render-Bausteine (`docs/render-*.md`), aber keine Blender-Anbindung. Vorhanden im Homelab: Blender headless per Docker auf dem Apps-LXC mit der RTX 2070 (`blender-render.sh`, Skill `homeserver-ops`) und Blender-MCP auf win-cad.
10. **Bedienung am Ende möglichst nah an Inventor:** Heute ist die SolidCraft-Web-App eingebettet (1b), deren Oberfläche eher an Fusion erinnert. Schritte dahin: zuerst Einstellungen und Plugin-Oberflächen von SolidCraft nutzen (#1221, deklarative „surfaces“), dann eigene Mechvane-Oberfläche über dem SolidCraft-Kern, wo das nicht reicht (ADR 0001). Abgleich mit Fusion: [Entscheidungsliste](../docs/research/2026-10-26-fusion-vs-inventor-liste.md) (25 Punkte plus Gegenprobe).
12. **Echte Desktop-App für Windows und Linux:** Die Wahl der Hülle (Tauri, Electron, pywebview, Qt) hängt am Prüfpunkt Sprache und daran, ob die eingebettete SolidCraft-Web-App im jeweiligen Webview läuft (WebGL/WebGPU, unter Linux ist Tauris WebKitGTK die Schwachstelle).

## Phase 0: Erkunden und entscheiden (ca. 2–4 Wochen)

- **SolidCraft praktisch testen:**
  *Stand 2026-10-19:* MCP angebunden (`.mcp.json`), 4 Referenzteile (Flansch, Druckgehäuse, Blechwinkel, Scharnier) gebaut und vermessen. Eingebundene `mcp__solidcraft__*`-Tools nach Neustart geprüft (Flansch, Abweichung 6,6e-6). *Web-App seit 2026-10-25 in Mechvane eingebettet und täglich im Einsatz (1b), damit erledigt (2026-10-31).*
- **Zeichnungen, Baugruppen, Blech, Plugins (#1221):**
  Baugruppen und Blech tragen (Referenzteile). Zeichnungen: M11 zurückgestellt, nur Ansichts-DXF. Plugins: nur Entwurf, kein Code, keine eigene Plugin-UI vorgesehen. Siehe [Bericht](../docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
- **Inventor-artiger Feature-Baum (Grundsatz 5):**
  *Stand 2026-10-19 (aus dem Code):* Die Einstellung `timeline_left` zeigt den Verlauf senkrecht über dem Browser, mit Ordnern und Rollback-Balken, an dem neue Features eingefügt werden. Optisch kommt das nahe, es fehlen Skizzen unter ihrem Feature und ein gemeinsamer Baum.
  *Nachtrag 2026-10-19:* SolidCraft hat **eine** Feature-Liste für das ganze Design (Komponenten nur als Feld `component`), Skizzen sind eigene Einträge, auf die Features per Id zeigen, und Gelenke liegen in `assembly.joints` mit eigenem Browser-Ordner „Joints“. Nötig wären Änderungen im Kern-Crate `doc` (Format, Eval).
  *Nachtrag 2 (Versuche):* Eine Datei je Bauteil liefert den eigenen Verlauf von selbst, Skizzenbesitz geht als Befehlsregel ohne Formatänderung. Lücke: Flächennamen gehen über Verknüpfungen verloren, ein Gelenk sprang still auf die falsche Bohrung ([Dokumentmodell](../docs/research/2026-10-19-dokumentmodell.md)).
  *Abgeschlossen 2026-10-31:* Mechvane zeigt den Baum selbst wie Inventor (Skizze unter ihrem Feature, Prüfseite). Einen echten Baum in der SolidCraft-App nur über Oberflächen-Erweiterungen (#1221) oder Upstream, gehört zu „Eigene Oberfläche“ (Phase 1). Siehe [Bericht](../docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
- **Lizenz- und Governance-Frage:**
  Sehr offen und schnell (Merge im Median 7 h), kein GPL/LGPL/AGPL-Code, keine Automatisierung kommerzieller CAD-Programme für Beiträge ([Bericht](../docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md)).
  *Präzisiert 2026-10-31 (Nutzer):* (1) kein (L/A)GPL-Code **in** Mechvane (bleibt MIT/Apache), (2) GPL-Programme als eigener Prozess sind erlaubt (CuraEngine, später CalculiX/Gmsh), Lizenz prüfen und im Installer nennen, (3) „nicht lesen“ gilt nur für Arbeit, die an SolidCraft oder cadmpeg gehen soll. Regeln in `AGENTS.md`.
- **Gegenprobe (Chili3D, Dune 3D, FreeCAD):**
  [Gemini-Rohfassung mit Prüfnotiz](../docs/research/2026-10-19-plattform-gegenprobe-gemini.md): Chili3D (TypeScript + OCCT-Wasm) und Dune 3D (C++, SolveSpace + OCCT) scheiden aus. FreeCAD (inzwischen 26.x) ist bei Zeichnungen weit vorn; ein FreeCAD-Backend verträgt sich aber nicht mit Beiträgen zu SolidCraft (keine (L)GPL-Code-Kenntnis).

## Phase 1: Agenten-Workflow und erste Inventor-Bausteine (ca. 2–3 Monate)

- **1a. Einstieg für Besucher (Nutzer-OK 2026-10-24):**
  - Live-Demo auf GitHub Pages (`tools/build_demo_site.py`, *gebaut 2026-10-24*, seit 2026-10-25 mit „Modellieren“).
  - Installation in einem Schritt (`pip install git+…`, `mechvane setup`, `mechvane ui --demo`): *unter Linux fertig 2026-10-27* (frische venv mit leerem Cache geprüft).
  - Dateien in der UI öffnen (*fertig 2026-10-26*: `python3 -m mechvane.ui <ordner>`, `/api/project`, `/api/open`, `/api/new`).
  - Windows-Test (*2026-10-27 auf der Windows-11-VM bestanden*: pip, setup, ui --demo, Model by hand, mcp; Surface/ARM noch offen).
  - PyPI: *Alpha `0.1.0a1` seit 2026-10-27* (nur Linux getestet; erster Upload mit Token, danach Trusted Publishing per Tag `v*`).
- **1b. Handbedienung (SolidCraft-Web-App einbetten):**
  *Test bestanden und umgesetzt 2026-10-25* (`/model`, Bauteile und Baugruppen mit verknüpften Teilen). Befund anklicken wählt die Fläche in der App aus (`select.set`, *fertig 2026-10-26*). **Vorgezogen 2026-10-31:** Pyodide-Prototyp #35, `design_rules` gegen `app.execute` der Web-App.
- **3. Parameter im Formular, Messen, Schnitt:**
  *Parameterformular, Messen und Schnitt auf der Prüfseite fertig 2026-10-29* (`/api/params`; Messen/Schnitt im Browser auf dem Netz, `viewtools.js`). *Messen an Kanten fertig 2026-10-30* (Länge, Kreis-Ø, Bogen R/Winkel, Bohrung aus zwei Halbflächen als ein Kreis; zwei Kanten: Winkel, Abstand, koaxial).
- **Baugruppen-Reiter in der Oberfläche (#88):**
  *Stand 2026-11-15:* Place (#89), Joint (#93), Bolted Connection (#94), Update Links, Place Standard Part und Constrain (neun Regeln, MCP `add_constraint`/`edit_constraint`) fertig, Joints und Constraints im Browser löschbar.
  *Stand 2026-11-16:* Stückliste fertig (MCP `bill_of_materials`, CSV, Knopf „BOM“ mit Flat und CSV-Export, #49).
- **Allgemeiner Befehlsdialog und Abdeckungsmatrix:**
  *Versuch fertig 2026-11-15 (#77, [Bericht](../docs/research/2026-11-15-befehlsdialog-versuch.md)):* 572 Befehle mit Schema, 92,3 % der 2667 Parameter lassen sich aus Schema und Name einem Eingabefeld zuordnen; Matrix mit `tools/command_matrix.py` nach `build/befehlsmatrix.json`.
  *Erster Schnitt 2026-11-17 (#128):* Strg+K mit Suche wie SolidCraft, Formular aus dem Schema (`mechvane/command_form.py`: Ausdruck, Zahl, Auswahlliste, Schalter, Text, Punkt, Namensliste, sonst JSON; Befehle ohne Schema als JSON mit SolidCraft-Hilfetext), Vorschau, OK auf die gemeinsame Rückgängig-Liste, lesende Befehle ohne Rückgängig-Schritt. Abdeckung 320 von 622 (36 App-Befehle ausgenommen; zurückgestellt: Skizzierer, Dateipfade, Befehle mit eigener Mechvane-Prüfung, Befehle nur fürs verborgene SolidCraft-Fenster).
  *Schnitt 2a 2026-11-17:* Auswahl in der Ansicht für Kanten, Flächen und Körper (Knopf „Pick“, Schreibform aus dem Schema: Punkt, `{face: …}`, Name; vorbelegt aus der Auswahl).
- **Wissen sichtbar:**
  *Stand 2026-11-16:* Befunde zeigen ihre Quelle (#120; fünf Regeln haben eine, für die übrigen fünf läuft die Recherche, #123).
- **Sehen, was der Agent geändert hat, erste Fassung:**
  *Fertig 2026-11-16 (#121):* Schatten aus dem Netz vor dem Schritt, Signatur je Feature statt `inspect.compare`, Leiste „Last step“ mit Hide; auch in der Live-Demo.
- **Agenten-Wiedergabe in der Live-Demo:**
  *Fertig und veröffentlicht 2026-11-16 (#124):* Aufgezeichnete Sitzung spielt aus dem Sitzungsprotokoll ohne Schlüssel im Browser ab.
- **Eigene Oberfläche ([ADR 0005](../docs/adr/0005-eigene-oberflaeche.md)):**
  *Stufe 1 fertig (#36, gemergt 2026-11-01, veröffentlicht mit 0.1.0a12 und Live-Demo 2026-11-02).*
  *Stufe 2 begonnen 2026-11-02:* `/api/feature` mit Vorschau, gemeinsame Rückgängig-Liste für Hand und Agent (auch das Parameterformular), Kantenwahl in der Ansicht, Dialoge Rundung und Fase, Bearbeiten (Doppelklick) und Löschen (Rechtsklick, Entf), Bohrung (ISO 273, Gewinde, Senkungen), Rechteck-/Kreismuster, Spiegeln, Extrusion und Drehung. Bohrungsposition über Abstände zu ein oder zwei Kanten gemergt 2026-11-05 (#43, SolidCraft `references`). Profilwahl in Extrusion und Drehung fertig 2026-11-05; Profile per Klick in der Ansicht fertig 2026-11-06 (`sketchgeom.js`); Drehung mit zwei Auswahlfeldern (Profile und Axis) fertig 2026-11-07 (#59).
  *Dialoge in der Live-Demo fertig 2026-11-02:* `demo_kernel.js` beantwortet `api/*` im Browser über die versteckte SolidCraft-Web-App (OPFS, Pyodide, `edit.undo/redo`).
  *Stufe 3 begonnen 2026-11-02 / korrigiert:* Skizzendialog öffnete Extrusion; Nutzer 2026-11-02 lehnte Sprung ab → eigene Skizzierumgebung (ADR 0005 Nachtrag 2026-11-02).
  *Skizzierumgebung:* Server-Teil fertig 2026-11-05 (`/api/sketch/*`). Schritt (a) fertig 2026-11-06 (`sketcher.js`, Linie/Rechteck/Kreis/Fangen/`sketch.draw.dimensioned`, `ui_smoke.py`); (b) Bemaßen fertig 2026-11-06 (Werkzeug D, Freiheitsgrade, `parameters.change`); (c) fertig 2026-11-06 (Abhängigkeiten H/V/∥/⊥/T/=, Dreipunktbogen, `sketch.delete`); (d) fertig 2026-11-06 (Stutzen T, Verlängern, Versatz O, Projizieren P, Koinzident, Fest, Konflikte, `tools/sketch_smoke.py`). Befunde aus dem Surface-Test 2026-11-06 umgesetzt (#61); Live-Demo kann skizzieren (2026-11-06, `demo_kernel.js`, `demo_smoke.py`).
- **Lücken aus dem Soll-Abläufe-Abgleich ([2026-11-07](../docs/research/2026-11-07-soll-ablaeufe-abgleich.md)):**
  *Fertig 2026-11-15 (#68):* Umbenennen (F2), Sichtbarkeit (Auge, V), Löschen mit Skizzenfrage, Fensterauswahl, Kürzel R sowie als letzte die automatische Projektion der Flächenkanten beim Skizzieren.
- **Live-Demo prüft nach dem Speichern:**
  *Prototyp gemergt 2026-11-02* (`browser_check.py`, `demo_check.js`, ~5 MB Download, 2 ms je Prüfung). *Fertig und veröffentlicht 2026-11-02 (0.1.0a12):* in Chromium gegen die echte Web-App getestet (6 Befunde wie vorberechnet, nach `parameters.change` live neue Befunde).
- **Point and speak fertig:**
  *Surface ok (Nutzer 2026-11-06);* Auswahl per Klick ohne Werkzeug seit 2026-11-06. *Für v0.1 erledigt (2026-11-10):* Handy folgt mit `app.mechvane.dev`.
- **Öffnen/Neu ohne Browser-Dialoge:**
  *Erledigt 2026-11-01:* `newpart.js`, Fehler im Dialog, Klicktest in `ui_smoke.py`. Zwei `confirm()` im Agenten-Chat bleiben vorerst.
- **Projektordner in der UI wechseln:**
  *Fertig 2026-11-07:* File → Open folder… und Browse… bei Import STEP (Issue #60).
- **Konstruktionsabsicht in Dialogen:**
  *Bohrungsdialog „Middle of face“ an geraden Kanten fertig 2026-11-05, an runden Flächen konzentrisch fertig 2026-11-09 (Issue #71), Bearbeiten mittig gesetzter Bohrungen fertig 2026-11-10 (Issue #72)* (`centred_hole_commands` in `ui/server.py`).
- **STEP als Referenzkörper importieren:**
  *MCP-Werkzeug `import_step` fertig 2026-11-06; File → Import STEP… fertig 2026-11-06 (`/api/import_step`), Browse… außerhalb des Ordners fertig 2026-11-07 (Issue #60); STEP-Baugruppen in einzelne Teile zerlegen fertig 2026-11-11 (Issue #74).*
- **SolidCraft-Fehler für Agent und Nutzer übersetzen:**
  *Stufe 1 fertig 2026-11-02* (#38, `sc_errors.py`: 24 Meldungen mit Erklärung und Vorschlag in `run`).
  *Stufe 2 gemergt 2026-11-05* (#42: Dekorator `sc_errors.explained`, `/api/feature` mit `explanation`/`hint`).
  *Stufe 3 fertig 2026-11-09* (`sc_locate.py`, Test `sc_locate_checks`): `Where: …` mit Mechvane-Flächennamen, Querschnittsmodell für Rundung/Fase (< 3 % Abweichung zu „largest size that fits“) und `feature_errors`.
- **Bauteilende für den Agenten:**
  *Fertig 2026-11-04, #44, MCP-Werkzeug `part_end`, gemergt 2026-11-05;* Speichern im zurückgerollten Zustand erlaubt (Nutzer 2026-11-05), Hinweis in `run`.
- **Zustandsbericht nach jedem Modellschritt:**
  *Fertig 2026-11-02, #37, `state_delta.py`.*
- **Grafik-Overhaul am Ende von v0.1:**
  *Sichtung 2026-11-06:* [Lückenliste P1–P3](../docs/research/2026-11-06-ui-sichtung.md) (Nielsen 23/40); Kontrast Senden-Knopf behoben 2026-11-06. **Entscheidungen Nutzer 2026-11-06:** (1) Agent gleichrangig sichtbar, aber ausblendbar; (2) eigener Stil statt Inventor-Optik; (3) Live-Demo startet mit bestandener Prüfung (Flansch zuerst, erledigt 2026-11-06).
- **Abgleichliste Inventor ↔ SolidCraft ↔ Mechvane:**
  Recherche *fertig 2026-10-30* ([Bericht](../docs/research/2026-10-30-abgleich-inventor-solidcraft-flash.md)).
- **Desktop-App:**
  *Schritt 1 umgesetzt 2026-10-28* (`mechvane/ui/appwindow.py`, `mechvane shortcut`, unter Linux und Windows getestet, Sichtprüfung offen).
- **Eigene Oberfläche, SolidCraft nur noch im Hintergrund:**
  *Geändert 2026-10-31 (Nutzer):* Arbeitsbereich, Feature-Dialoge und Skizzierer vorgezogen ([ADR 0005](../docs/adr/0005-eigene-oberflaeche.md)). SolidCraft-Einbettmodus `?embed&open=` (ab 0.23.0, am 2026-10-28 auf 0.25.1 aktualisiert); Wunsch nach `?embed=viewport&edit` gemeldet als [SolidCraft #8517](https://github.com/tangency-labs/solidcraft/issues/8517) (2026-10-28).
- **Mechvane-Schicht als MCP-Server:**
  *Stand 2026-10-20:* Prototyp läuft ([Doku](../docs/mechvane-mcp.md), 99 Prüfungen grün in `tests/mechvane/check.py`). Praxistest Klappscharnier bestanden (#3330 erkannt und repariert).
- **Konstrukteurs-Agent:**
  *Erster Stand 2026-10-20:* `check_design` mit Profilen `fdm_0.4` und `cnc_alu`, Projekt-Skill `.claude/skills/konstrukteur` ([Bericht](../docs/research/2026-10-20-konstrukteur.md)).
- **Normteile-Generator:**
  *Erster Stand 2026-10-20:* `standard_part` für ISO 4762, ISO 4032, ISO 7089, Ruthex-Einsätze, 6000–6005 ([Bericht](../docs/research/2026-10-20-normteile-gemini.md)).
- **Eigene Web-UI:**
  *Stand 2026-10-24:* Stufe 1 fertig (`python3 -m mechvane.ui <datei>`, Bericht `docs/research/2026-10-24-web-ui-stufe1-argon.md`).
- **Bohrungsassistent mit Verschraubung:**
  *Erster Stand 2026-10-20:* `bolted_connection` für Durchgang (mit Senkung), Sackloch und Ruthex-Einsatz ([Spezifikation](../docs/research/2026-10-20-bohrungsassistent-spec.md)).
  Senkdurchmesser DIN 974-1 (Reihe 1 und 5), ISO 10642 (DIN 74 Form F / ISO 15065) und ISO-286-Passungen (`iso_fit`) sowie Muster seit 2026-10-23 quellengeprüft.
  *Praxistest 6 (2026-10-31, [Bericht](../docs/research/2026-10-31-praxistest-6.md), umgesetzt 2026-11-02, #34):* Ausdehnung „durch alle“ und Kollisionsprüfung vor dem Bohren mit Rollback.
- **Eigener offener Regelkatalog:**
  *Seit 2026-10-23:* Format nach [ADR 0002](../docs/adr/0002-wissenskatalog-format.md) angenommen, `katalog/` mit ersten Einträgen gemergt ([Plan](../docs/research/2026-10-20-wissenskatalog-plan.md)).
- **Werkstoffdatenbank:**
  Runde 1 (16 Werkstoffe) *gemergt 2026-10-29* ([Bericht](../docs/research/2026-10-29-werkstoffe-flash.md), `katalog/eintraege/werkstoffe/`). τ_B je Werkstoff *ergänzt 2026-10-29* (#16); *Bibliothek für SolidCraft seit 2026-10-29* (`tools/katalog_to_solidcraft.py`); Einschraubtiefe in `check_design(material=…)` seit 2026-10-29; `dickenbereiche` mit `katalog.mindestwerte()` seit 2026-11-03 (`docs/research/2026-11-01-randabstand-wandstaerke-flash.md`).
- **Regeln aus Werkstoffkennwerten herleiten:**
  Recherche (Issue #14, gemergt 2026-10-29): [Regeln aus Kennwerten](../docs/research/2026-10-29-regeln-aus-kennwerten-flash.md); Kernformel `m_eff = A_s·R_m / (A_n'·τ_B)`.
- **Material- und Darstellungseditor:**
  Recherche (Issue #15, gemergt 2026-10-29): [Darstellungsformat](../docs/research/2026-10-29-darstellungsformat-flash.md) empfiehlt glTF-PBR. [ADR 0004](../docs/adr/0004-darstellungsformat.md) *angenommen 2026-10-29* (Probe: glTF trägt nach Blender).
- **Referenzteile-Korpus (`tests/reference/`):**
  *Begonnen 2026-10-19:* 7 Teile mit `check.py` (seit 2026-10-23 Welle, Rohrhalter, Rippenplatte).

### Nach v0.1: Harness und Zusammenarbeit

- **Direktbearbeitung wie Inventor:**
  **Grenze SolidCraft 0.25.1 (Nutzertest 2026-11-05):** `solid.offset_face` / `solid.shell` lehnten Körper mit beliebiger Freiformfläche ab.
  *Stand 2026-11-05:* Upstream gemeldet als **#745** (ferne Freiformfläche, Fix-PR #3893 geschlossen) und **#10884** (Freiformfläche selbst versetzen); Kernel-Arbeit pausiert (**#3992**, Prüfung **solidcore**). Anwendungsfall unter #745 kommentiert (2026-11-05, Nutzer-OK). *Nachtrag 2026-11-05:* v0.40.0-rc.1/rc.2 laufen auf solidcore. *Test 2026-11-06:* rc.2 löst #745; weiter offen: Shell mit offener Kreisfläche (status 1001) und #10884 ([Testbericht](../docs/research/2026-11-06-solidcore-testbericht-3992.md)).
  *Stand 2026-11-11:* SolidCraft hat **#745** und **#5353** auf `main` (0.40.0-rc.4) geschlossen.
  *Stand 2026-11-14:* Hinweise in `mechvane/sc_errors.py` und `tests/mechvane/check.py` nachgezogen; Scratch-Ordner (#7836) ab 0.41.0 behoben.
- **Modell je Auftrag wählen:**
  *Seit 2026-11-02:* Im Protokoll (`agent_session`) wird festgehalten, welches Modell lief.

## Phase 2: Fachmodule als Plugins (ca. 4–6 Monate)

- **Native Dateien aller großen CAD-Systeme importieren, mit Feature-Verlauf:**
  **Grundlage cadmpeg** (Fund 2026-10-31): [cadmpeg](https://github.com/cadmpeg/cadmpeg) (Apache-2.0, Clean Room). Arbeitsteilung (2026-11-03): Format-Dekodierung (L4–L6) an cadmpeg, Mechvane übersetzt IR in SolidCraft-Befehle; GPL-Importer wie InventorLoader bleiben tabu.
- **Schweißen:**
  Grundlagen recherchiert (#19): [Schweißen im CAD](../docs/research/2026-10-30-schweissen-grundlagen-flash.md) (Bisher im Testmodell nur als konkave Rundung am Fuß, `tools/build_logo_showcase.py`).
- **Slicer-Modul (grafisch):**
  *Recherche 2026-10-19* ([Gemini mit Prüfnotiz](../docs/research/2026-10-19-slicer-engines-gemini.md)): CuraEngine als klarer Kandidat (`LayerOptimized` über Arcus/Protobuf); Headless-Kette `/opt/cura-headless/` getestet.
  *Upstream 2026-11-17:* Antwort auf unsere Frage vom 19.10. ([Kommentar raykholo](https://github.com/tangency-labs/solidcraft/issues/1221#issuecomment-6962627263)): „Design changed“-Listener für offene Plugin-Panels in RFC 0015 für Phase 3 ([PR #18727](https://github.com/tangency-labs/solidcraft/pull/18727), offen). Unsere Antwort (Nutzer-OK, 2026-11-17, [Kommentar](https://github.com/tangency-labs/solidcraft/issues/1221#issuecomment-6963401344)): nachgefragt, ob das Panel schwere Arbeit über freigegebene Einstiege startet, und an Generator-Fragen erinnert.
- **Eigene Features als Code:**
  *Upstream 2026-11-02:* SolidCraft plant Plugin-Generatoren (WIT + WebAssembly, #1221, #11169, #4980, [Kommentar KyleTryon](https://github.com/tangency-labs/solidcraft/issues/1221#issuecomment-6584580471)). Unser Kommentar (Nutzer-OK, 2026-11-02): [deklarierte Eingaben über die API lesbar, Auswahl/Ergebnis nicht auf einen Körper festlegen](https://github.com/tangency-labs/solidcraft/issues/1221#issuecomment-6585010413).
  *2026-11-08:* PR #4980 übernimmt beide Punkte in Abschnitt 13a ([Antwort](https://github.com/tangency-labs/solidcraft/issues/1221#issuecomment-6725506608)); [nachgefragt](https://github.com/tangency-labs/solidcraft/issues/1221#issuecomment-6726545120) zu Joints und eingefügten Teilen als Ziel.
  *2026-11-11:* #4980 geschlossen, abgelöst durch RFC 0002 (PR #15110, WASM-Plugins); unser Kommentar am RFC ([Antwort raykholo](https://github.com/tangency-labs/solidcraft/pull/15110#issuecomment-6806473533)): lesbare Eingaben und Ziele als Liste in Phase 1, gespeicherte Eingaben/Joints/eingefügte Teile in Phase 3 / Abschnitt 9 ([Notiz](../docs/research/2026-11-11-solidcraft-plugin-rfc-0002.md)).

### Ergänzungen Phase 2

- **FEM:**
  *Stand 2026-11-20:* Vor dem Start [FieldCraft](../docs/research/2026-11-20-fieldcraft.md) prüfen (Tangency Labs 0.8.1, MIT/Apache-2.0, Rust, feste Flächennamen), bevor eigener Löser / CalculiX umgesetzt wird.

## Phase 3: Fertigungszeichnungen (ca. 6–9 Monate)

- **CADCraft-Test:**
  *Baustein 2026-10-20:* [CADCraft](../docs/research/2026-10-20-cadcraft.md) (ArtCraft, 2D, MIT/Apache) als DXF/PDF-Baustein getestet (nur Polylinien statt echter Kreise, ohne 3D-Bezug; exakte Ansichten müssen von SolidCraft #860 kommen).

## Archiv 2026-11-23: Aufräumen nach dem Umschwenk

Aus [ROADMAP.md](../ROADMAP.md) entfernt am 2026-11-23, nachdem der Nutzer den Umschwenk zu Harness und Plugin für SolidCraft
bestätigt und die Schnitt-Fragen entschieden hat (Strategiepapier `docs/strategie/2026-11-18-weg-neben-solidcraft.md`, Abschnitt
„Entscheidung“, Nachtrag vom 2026-11-23). Der Wortlaut steht unverändert unter den Überschriften; Checkboxen hier sind **nicht** mehr
maßgeblich. Die offene Arbeit steht in `ROADMAP.md` („Bis v0.1 fehlt noch:“) und in den Issues.

### Grundsatz 6 (Point and speak), alter Wortlaut

*Ersetzt: Ort ist jetzt die SolidCraft-App und ihre Plugins statt der eigenen Oberfläche (Nutzer 2026-11-23).*

6. **Point and speak** (Nutzerwunsch 2026-10-20, sehr wichtig): Der Claude-Agent sitzt in der Oberfläche;
   markierte Kanten/Flächen mit stabilen Flächennamen und gesprochener Auftrag gehen zusammen an ihn und werden zu
   editierbaren Features im Baum.

### Grundsatz 10 (Bedienung nah an Inventor), alter Wortlaut

*Ersetzt: Weg über Ribbon-Plugins in der SolidCraft-App statt eigener Oberfläche (Nutzer 2026-11-23).*

10. **Bedienung am Ende möglichst nah an Inventor** (Nutzerwunsch 2026-10-26, Endziel der UI), **optisch aber dunkler
    und schicker** (dunkles Farbschema, ruhige Gestaltung): Multifunktionsleiste mit Inventor-Registern, -Befehlen und
    -Kürzeln, Kontextmenüs, Mini-Werkzeugleiste, Modellbrowser links, ViewCube, getrennte Bauteil-/Baugruppen-/Skizzen-
    Umgebungen und passende Dialoge. Weg über SolidCraft-Plugins (#1221) bzw. eigene Oberfläche (ADR 0001);
    Abgleich mit Fusion: [Entscheidungsliste](../docs/research/2026-10-26-fusion-vs-inventor-liste.md).

### Grundsatz 12 (Desktop-App), gestrichen

*Gestrichen am 2026-11-23: keine eigene Desktop-App mehr, die UI ist eingefroren.*

12. **Echte Desktop-App für Windows und Linux** (Nutzerwunsch 2026-10-26, Ziel): eigenes Programm mit Installer,
    Startmenü-Eintrag und eigenem Fenster offline neben der Browser-Variante (v0.1: App-Fenster/WebView2, danach echte
    Desktop-App beim Prüfpunkt Sprache).

### Phase 0, alle Punkte (abgeschlossen)

*Alle erledigt; in der ROADMAP bleibt ein Absatz mit Verweis auf ADR 0001.*

- [x] Build-Umgebung klären: kein eigener Build nötig, fertige
      Release-Binaries (v0.16.2) laufen headless auf dem Steuer-Container
      (*Stand 2026-10-19:* erledigt, [Phase-0-Bericht](../docs/research/2026-10-phase0-solidcraft.md)).
- [x] SolidCraft praktisch testen: Desktop/Web-App, `solidcraft-cli mcp` an
      Claude Code anbinden, 3–5 eigene Referenzteile per Agent konstruieren.
      *Stand 2026-10-31:* Erledigt (MCP-Tools, 4 Referenzteile und eingebettete Web-App im Einsatz).
- [x] Prüfen: Wie gut ist der MCP-Server für Agenten (Fehlermeldungen,
      Topologie-Abfragen, Snapshots)? *Stand 2026-10-19:* Ergebnis im
      [Phase-0-Bericht](../docs/research/2026-10-phase0-solidcraft.md).
- [x] Prüfen: Wie weit sind Zeichnungen (`docs/drawing-foundations.md`),
      Baugruppen, Blech, Plugins (#1221)? *Stand 2026-10-19:* Baugruppen und Blech tragen; Zeichnungen
      zurückgestellt; Plugins nur Entwurf ([Bericht](../docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md)).
- [x] Prüfen: Lässt sich in SolidCraft ein Inventor-artiger Feature-Baum
      statt der Fusion-Timeline umsetzen (Grundsatz 5)? *Stand 2026-10-31:* Mechvane zeigt den Baum selbst; im
      Datenmodell per eigener Dokumentschicht ([Dokumentmodell](../docs/research/2026-10-19-dokumentmodell.md),
      [Bericht](../docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md)).
- [x] Lizenz- und Governance-Frage: Wie offen ist das Projekt für Beiträge,
      wie stabil ist die API? *Stand 2026-10-31:* Sehr offen und schnell (Merge im Median 7 h), kein
      GPL/LGPL/AGPL-Code in Mechvane, GPL-Programme als eigener Prozess erlaubt (`AGENTS.md`,
      [Bericht](../docs/research/2026-10-19-solidcraft-baum-plugins-zeichnungen.md)).
- [x] Gegenprobe: Chili3D (TypeScript + OCCT-Wasm), Dune 3D (C++, SolveSpace
      + OCCT), FreeCAD 1.x als Plattform kurz bewerten. *Stand 2026-10-19:* Chili3D und Dune 3D scheiden aus;
      FreeCAD wegen (L)GPL nicht kompatibel mit SolidCraft-Beiträgen
      ([Gemini-Rohfassung mit Prüfnotiz](../docs/research/2026-10-19-plattform-gegenprobe-gemini.md)).
- [x] **Entscheidung (ADR 0001)** zwischen (*2026-10-20 angenommen:*
      [A+, SolidCraft-Kern unverändert, Mechvane als eigene Schicht](../docs/adr/0001-grundlage-solidcraft.md),
      Bauteil = Design, Baugruppe = Design mit verknüpften Komponenten; Grundlage:
      [Dokumentmodell](../docs/research/2026-10-19-dokumentmodell.md)):
  - **A – Plugin-/Erweiterungsprojekt auf SolidCraft** (bevorzugt, falls Phase 0 trägt): Mechvane liefert die
    Inventor-Schicht als Plugins und trägt Kernfunktionen upstream bei.
  - **B – Fork** von SolidCraft, falls Richtung oder Tempo nicht passen.
  - **C – Eigener Kern** in Rust mit OCCT hinter einem `BRepKernel`-Trait, nur wenn A und B ausscheiden (Aufwand ein Vielfaches).

### Meilenstein v0.1 vom 2026-10-23 (Ziel Ende Dezember 2026) und Fokus vom 2026-10-31

*Ersetzt durch den Schnitt vom 2026-11-22/23; das Zieldatum „Ende Dezember 2026“ entfällt, Neubewertung nach U1 (#181).*

**Meilenstein v0.1 (Ziel Ende Dezember 2026, Nutzer-OK 2026-10-23):** Grundlagen
laufen und eine gute Web-UI für die Arbeit mit dem Agenten (Agent baut, Nutzer sieht,
zeigt, prüft). Danach nur noch Fachmodule. Schätzung bei 10–20 % Wochenbudget:

1. UI Stufe 1: 3D-Ansicht, Modellbaum, Befunde, Neuladen (~1 Woche). *Fertig 2026-10-24.*
1a. Einstieg für Besucher (Nutzer-OK 2026-10-24): Live-Demo (`tools/build_demo_site.py`), 1-Schritt-Installation
   (`mechvane setup`), Ordnerwahl in der UI, Windows-Test und PyPI-Alpha (`0.1.0a1`). *Stand 2026-10-27:* Linux und
   Windows-11-VM bestanden; stabile Version folgt nach v0.1.
1b. Handbedienung: SolidCraft-Web-App einbetten (`/model`, Modi Modellieren/Prüfen, Flächenauswahl per Klick).
   *Stand 2026-10-31:* Umgesetzt (2026-10-25/26); Pyodide-Prüfung in der Demo vorgezogen (#35).
2. UI Stufe 2: Point and speak (Flächenauswahl + Spracheingabe an den Agenten), Rückgängig
   ([ADR 0003](../docs/adr/0003-point-and-speak.md), angenommen 2026-10-28).
3. Parameter im Formular, Öffnen/Speichern, Messen, Schnitt (1–2 Wochen). *Stand 2026-10-30:* Auf der Prüfseite
   fertig (`/api/params`, Netz-Schnitt, Kantenmessen).
4. Praxistests mit dem Nutzer, Fehler beheben, Windows, Installation in einem Schritt (2–3 Wochen).
   *(Nicht in v0.1 bis 2026-10-31, geändert durch „Eigene Oberfläche“ und ADR 0005; Bedienung bleibt Inventor-nah.)*

**Fokus bis v0.1** (Nutzer 2026-10-31): Claude arbeitet an dieser Liste. Gemini bleibt gut ausgelastet, aber
nach Phasen geordnet: Issues mit Label `v0.1` zuerst, danach Füllaufträge aus Phase 1 (#25, #27, #28), deren
Branches erst gesichtet werden, wenn ihr Punkt dran ist. Phase 2 und später tragen `später` und ruhen (#29–#31).
Neue Ideen kommen sofort an ihre Phase in die ROADMAP; umgesetzt werden sie, wenn die Phase dran ist, außer der
Nutzer sagt ausdrücklich „jetzt“.
Der native CAD-Import bleibt Langzeitziel: #32/#33 werden gesichtet, neue Aufträge erst nach v0.1.

### Schnitt von v0.1, Fassung vom 2026-11-22

*Ersetzt am 2026-11-23: U1 + Abnahme-Arbeit + U5 gehören zu v0.1, U2–U4 (Rust) zu v0.2; Verschraubung als „ein Aufruf, ein Aufruf zurück“.*

**Schnitt von v0.1 (Nutzer-OK 2026-11-10, neu gefasst 2026-11-22 nach der Umschwenk-Entscheidung vom 20.11.).**
v0.1 zeigt, dass Mechvane als Maschinenbau-Schicht und Harness an der laufenden SolidCraft-App trägt: Agent und
Nutzer arbeiten am selben Fenster, Befunde haben Quellen, die Installation ist kurz. Die Web-UI ist eingefroren
(nur Live-Demo mit Archiv-Hinweis), Rust-Plugins und Ribbon gehören zu v0.2. Abgenommen wird an vier Prüfungen,
die kein Modell entscheidet (Begründung: `docs/strategie/2026-11-18-weg-neben-solidcraft.md`, Abschnitt „Entscheidung“):
1. **Konstruieren:** eine feste Konstruktionsaufgabe mit Auswerter erreicht über `--connect` (gegen die offene App)
   mindestens 80 von 100 Punkten.
2. **Prüfen am offenen Fenster:** `mechvane check` läuft gegen das offene Fenster, mit Quellen und dem gleichen
   Ergebnis wie ohne Fenster.
3. **Verschraubung:** eine Verschraubung ist ein einziger Rückgängig-Schritt.
4. **Installation:** ein Neuling installiert und baut den Flansch in unter 15 Minuten.

Die frühere Abnahme „Abdeckung“ (jeder Befehl in der Oberfläche) entfällt; `tools/acceptance.py` misst sie nur noch
als Information. 0.1.0a24 war die letzte Alpha der App-Linie (a25 als Ausnahme). Die Etappen sind jetzt U1–U5 des Umschwenks
(Stufe 1 Python-Harness mit `--connect`, Stufe 2 Rust-Plugins erst nach dem Durchstich-Tor) statt Fundament, Vollständig,
Glanz; Fundament ist abgeschlossen (Praxistest 7 entfällt mit der eingefrorenen Web-UI). Stufe 2 und `--connect` auf der Nutzer-App brauchen SolidCraft 0.45
(Plugins, Panel-Signal); die Versionsfrage (Web-UI bleibt auf 0.43) wird bei U1 geklärt. Direktbearbeitung, Upstream-PRs und Spracheingabe folgen nach v0.1.

### „Bis v0.1 fehlt noch“, Liste vom 2026-11-22 (26 Punkte, 14 erledigt)

*Ersetzt durch sechs Punkte (U1, Abnahme 1–4, U5). Die Web-UI-Punkte sind eingefroren (Entscheidung 2026-11-20), die erledigten stehen hier. `verify_view` (Sichtprüfung) ist erledigt (#70, am 2026-11-13 geschlossen), obwohl die Zeile unten noch „Geplant“ sagt.*

- [x] **Wechsel auf SolidCraft 0.40.1** (#91, begonnen 2026-11-12): Stand und offene Fehler in der Übergabe und im Issue; `install.py` erst nach grünen Tests.
      *Fertig:* 0.41.0 am 2026-11-13 (#91), 0.43.0 am 2026-11-16 (#113, Release 0.1.0a21).
- [x] **Upstream-Watch** (#90): wöchentliche Bestandsaufnahme von SolidCraft (Releases, Befehlsdifferenz, beobachtete Issues), ohne Modell.
      *Fertig 2026-11-13:* `tools/upstream_watch.py`, Timer montags, Berichte unter `docs/upstream/`.
- [x] **Baugruppen-Reiter in der Oberfläche** (Nutzer 2026-11-12, #88): Place, Joint, Bolted Connection, Update Links,
      Standard Part, Constrain und Stückliste (BOM/CSV) im Reiter „Assemble“. *Stand 2026-11-16:* Alle Dialoge und
      Browser-Löschen fertig (#89, #93, #94, #49); offen nur Bedien-Reise (#83) als Abnahme.
- [ ] **Allgemeiner Befehlsdialog und Abdeckungsmatrix** (2026-11-10): Befehlssuche (Strg+K), Formular aus
      `describe_command` und Abdeckungsmatrix über alle Befehle. *Stand 2026-11-17 (#128):* Strg+K, Formular
      (`mechvane/command_form.py`, 320/622 Befehle) und Auswahl in der Ansicht fertig, Versuch #77
      ([Bericht](../docs/research/2026-11-15-befehlsdialog-versuch.md)); offen: `sketch.*`, Dateiwahl, Live-Demo, Smoke-Tests.
- [ ] **Wissen sichtbar** (2026-11-10): Prüfungsbefunde mit Regel, Wert, Quelle und Zitat sowie Katalogseite auf
      mechvane.dev. *Stand 2026-11-16:* Quellen in Befunden fertig (#120, Recherche #123 läuft); offen: Katalogseite.
- [x] **Sehen, was der Agent geändert hat, erste Fassung** (2026-11-10): Geistervolumen und Baum-Markierung der letzten
      Agenten-Änderung (Annehmen/Verwerfen nach v0.1). *Fertig 2026-11-16 (#121):* Netz-Schatten, Feature-Signatur,
      Leiste „Last step“ mit Hide, auch in der Live-Demo.
- [x] **Agenten-Wiedergabe in der Live-Demo** (2026-11-10): aufgezeichnete Sitzung spielt ohne Schlüssel im Browser
      ab. *Fertig 2026-11-16 (#124):* Veröffentlicht in der Live-Demo.
- [ ] **„Was kommt“ in der App** (2026-11-10): die nächsten Punkte aus `roadmap.json` und der Knopf „Wunsch äußern“.
- [ ] **Eigene Oberfläche** (Nutzer 2026-10-31, [ADR 0005](../docs/adr/0005-eigene-oberflaeche.md)): Arbeitsbereich wie
      Inventor, Feature-Dialoge über `/api/feature` und Skizzierer (`sketch_constraints`); SolidCraft-App als
      Expertenmodus. *Stand 2026-11-07:* Stufen 1–2, Skizzierumgebung (a–d) und Live-Demo fertig (#36, #43, #59, #61);
      offen: Skizzen-Parameter im Parameterpanel und Bild-Symbole (Overhaul).
- [x] **Lücken aus dem Soll-Abläufe-Abgleich** ([2026-11-07](../docs/research/2026-11-07-soll-ablaeufe-abgleich.md),
      #55–#57): Umbenennen (F2), Sichtbarkeit (V), Löschen mit Skizzenfrage, Flächenkanten projizieren, Fensterauswahl,
      Kürzel R. *Fertig 2026-11-15 (#68);* Weiteres (ViewCube, EOP ziehen, getriebene Maße, HUD) nach v0.1.
- [x] **Live-Demo prüft nach dem Speichern** (1b, erster Eindruck): *Fertig 2026-11-02 (0.1.0a12, Pyodide #35):*
      Live-Befunde nach Änderungen im Browser; Baugruppen bleiben vorberechnet.
- [x] **Point and speak fertig** (2): Spracheingabe auf Surface ok (2026-11-06), Auswahl per Klick ohne Werkzeug
      fertig; *Stand 2026-11-10:* für v0.1 erledigt, Handy folgt mit `app.mechvane.dev`.
- [x] **Öffnen/Neu ohne Browser-Dialoge** (3): eigener Dialog `newpart.js` statt `prompt()`/`alert()`, Klicktest in
      `ui_smoke.py`. *Erledigt 2026-11-01;* zwei `confirm()` im Agenten-Chat bleiben vorerst.
- [x] **Projektordner in der UI wechseln** (3, Nutzer 2026-11-05): eigener Dialog „Open folder…“ mit Server-Listing
      und Einzeldatei-Öffnen. *Fertig 2026-11-07:* File → Open folder… und Browse… (#60).
- [ ] **Konstruktionsabsicht in Dialogen** (3, Nutzerregel 2026-11-05): Beziehungen als Skizzen-Abhängigkeiten bauen.
      *Stand 2026-11-10:* Mittige/konzentrische Bohrung inkl. Bearbeiten fertig (#71, #72); offen: übrige Beziehungen je
      mit Test.
- [x] **STEP als Referenzkörper importieren** (3, Nutzer 2026-11-05): STEP-Import als fester Körper ohne Verlauf für
      Zukaufteile und Messen. *Fertig 2026-11-11:* MCP `import_step`, UI-Import (#60) und Baugruppen-Zerlegen (#74).
- [ ] **SolidCraft-Fehler für Agent und Nutzer übersetzen** (Nutzer 2026-10-31): Fehler mit mechvane-Flächennamen
      lokalisieren und mit Vorschlag erklären. *Stand 2026-11-09:* Stufen 1–3 fertig (`sc_errors.py`, `sc_locate.py`,
      `feature_errors`, #38, #42); offen: Ansicht-Markierung (`location.at`), Baugruppen („lumps“ #34), Skizzenfehler.
- [x] **Bauteilende für den Agenten** (Nutzer 2026-11-01): MCP-Werkzeug `part_end` setzt den Bauteilende-Marker vor
      Fehlerstellen (`timeline.rollback`/`roll_to`). *Fertig 2026-11-05 (#44);* Speichern zurückgerollt erlaubt.
- [x] **Zustandsbericht nach jedem Modellschritt** (Nutzer 2026-11-01): knappes Delta (Hüllquader, Schwerpunkt,
      Volumen/Masse, Körperzahl, Schnitt-Warnung). *Fertig 2026-11-02 (#37, `state_delta.py`).*
- [ ] **Sichtprüfung für den Agenten** (Nutzer 2026-11-01): MCP-Werkzeug `verify_view` liefert Vierfach-Bild (Iso,
      Vorne, Oben, Schnitt) mit Achsen, Maßstab und Fehlerstelle, gezielt eingesetzt. *Stand 2026-11-01:* Geplant auf
      Basis von `screenshot`.
- [x] **Baugruppen wie Inventor**: erstes Teil festlegen (#26, erledigt 2026-11-01), `bolted_connection` durch alle und
      Kollisionsprüfung (#34, erledigt 2026-11-02; „durch alle“ bohrt auch eine zweite Wand desselben Teils dahinter).
- [ ] **Desktop-App Schritt 1**: Sichtprüfung des App-Fensters unter Windows und Linux.
- [ ] **Eigenes Fenster unter Windows, vor 0.1.0** (Nutzer 2026-11-02): pywebview auf WebView2 mit PyInstaller/Inno
      Setup; Linux bleibt beim Chrome-App-Fenster. *Stand 2026-11-10:* Beschlossen; offen: Paket (#7) und Surface-Test.
- [ ] **Praxistests** (4): mindestens zwei weitere Runden mit dem Nutzer, je eine echte Konstruktion von Anfang bis
      Ende (Agent und Handbedienung), Befunde beheben.
- [ ] **Grafik-Overhaul am Ende von v0.1** (Nutzer 2026-11-06): einheitliche eigene SVGs für Ribbon, Baum und Dialoge,
      Skizzenmodus, helles Thema ([Lückenliste P1–P3](../docs/research/2026-11-06-ui-sichtung.md)). *Stand 2026-11-06:*
      Sichtung (23/40) und Nutzer-Entscheidungen (Agent ausblendbar, eigener Stil, Demo mit Flansch) getroffen; offen:
      Symbole und Umsetzung.
- [ ] **Stabile Version** 0.1.0 auf PyPI, wenn alles oben erledigt ist und Linux und Windows laufen.

- [x] Abgleichliste Inventor ↔ SolidCraft ↔ Mechvane (Register, Befehlsnamen, Tastenkürzel, Browser, Dialoge):
      *Stand 2026-10-30:* Recherche fertig ([Bericht](../docs/research/2026-10-30-abgleich-inventor-solidcraft-flash.md)).

### Entscheidung 2026-11-10 und Prüfpunkt Sprache, alter Wortlaut

*Ersetzt durch den Prüfpunkt Sprache vom 2026-11-20 (Umschwenk).*

**Entscheidung 2026-11-10 (Nutzer-OK):** Mechvane bleibt bis v0.2 Python. Neu entschieden wird nicht nach Datum,
sondern sobald SolidCrafts Plugin-Generatoren (#1221) ausgeliefert sind. Die Windows-Hülle für v0.1 ist pywebview auf
WebView2 mit Installer, Linux bleibt beim App-Fenster. Der Absatz darunter ist der Stand davor.

**Prüfpunkt Sprache (nach v0.1, spätestens Januar 2027, Nutzer-OK 2026-10-24):** Mechvane bleibt
bis v0.1 Python (ADR 0001: „Rust, sobald die Schnittstelle steht“). Dann neu entscheiden, früher,
falls das SolidCraft-Plugin-System (#1221, WASM/WIT) fertig ist. Für Rust spricht: Prüfungen
als SolidCraft-Plugin, ein einzelnes Programm ohne Python. Dagegen: Umbau, langsame Builds
auf dem Steuer-Container; ein Paket mit eingebautem Python löst die Installation auch.

### Desktop-App und eigene Oberfläche (Web-UI-Linie)

*Gestrichen bzw. archiviert am 2026-11-23 (Entscheidungen 4 und 2): Desktop-App, private Online-Version `app.mechvane.dev`, „Eigene Oberfläche“ (ADR 0005, abgelöst durch den Umschwenk), native Android-App, Wunsch-Knopf in der App, eigene Web-UI Weg B.*

- [ ] **Desktop-App** (Grundsatz 12): Schritt 1 (offline, App-Fenster `mechvane/ui/appwindow.py`, `mechvane shortcut`)
      *umgesetzt 2026-10-28*, Sichtprüfung offen. Schritt 2 (echte Desktop-App mit Installer) nach v0.1 mit dem
      Prüfpunkt Sprache.
- [ ] **Private Online-Version unter `app.mechvane.dev`** (Nutzerwunsch 2026-10-28): eigene Web-UI und optional
      `mcp.mechvane.dev` im Homelab über Cloudflare Tunnel und Access erreichbar machen (nach UI Stufe 2; `mechvane.dev`
      bleibt Demo). *Stand 2026-10-28:* Vorgeschlagen; offen: LXC/systemd und cf-CLI-Einrichtung.
- [ ] **Eigene Oberfläche, SolidCraft nur noch im Hintergrund** (Entscheidung Nutzer 2026-10-28): vollständige
      Mechvane-Oberfläche über dem SolidCraft-Kern bei ausdrücklicher Nennung von SolidCraft ([ADR 0005](../docs/adr/0005-eigene-oberflaeche.md),
      [SolidCraft #8517](https://github.com/tangency-labs/solidcraft/issues/8517)). *Stand 2026-10-31:* Arbeitsbereich,
      Dialoge und Skizzierer in v0.1 vorgezogen; Kern als Bibliothek hängt am Prüfpunkt Sprache.
- [ ] **Native Android-App** (Nutzerwunsch 2026-10-28): Ansehen, Prüfen und Point and speak per Kotlin/Compose über
      `app.mechvane.dev`/LAN; zuvor Web-UI touch-tauglich machen (Nutzer 2026-11-02). *Stand 2026-11-02:* Konzept steht;
      offen: Access-Anmeldung, Offline-Cache und Umsetzung nach `app.mechvane.dev`.
- [ ] **Funktions- und Modulwünsche direkt aus der App** (Nutzerwunsch 2026-10-28): Knopf „Wunsch äußern“ und
      Chat-Auftrag öffnen vorausgefülltes GitHub-Issue im öffentlichen Repo. *Stand 2026-10-28:* Vorgeschlagen; offen:
      Issue-Vorlage (nach OK) und Umsetzung.
- [ ] **Eigene Web-UI** (Nutzer-OK 2026-10-23, Weg B): Stufe 1 lesend, Stufe 2 Point and speak mit Spracheingabe.
      *Stand 2026-10-24:* Stufe 1 fertig (`docs/research/2026-10-24-web-ui-stufe1-argon.md`); nächster Schritt: Stufe 2.

### Upstream #3330 als „Blocker“, alter Wortlaut

*Ersetzt: Upstream seit 2026-10-24 geschlossen, Bohrungsfall behoben; die Reparatur in `mechvane/links.py` bleibt.*

- [ ] **Upstream: Flächennamen über Verknüpfungen** (Blocker für getrennte Dateien): gemeldet als
      [#3330](https://github.com/tangency-labs/solidcraft/issues/3330) (2026-10-20), Prüfpunkt sechs Wochen (ADR 0001);
      Regressionstest in `tests/mechvane/check.py` aktiv.

### MCP-Server, Konstrukteur, Normteile, Regelkatalog: Stände vom 2026-10-20/23

*Stände in der ROADMAP nachgezogen.*

- [ ] **Mechvane-Schicht als MCP-Server** (nach ADR 0001): Python-MCP für getrennte Dateien, `update_links`,
      Skizzenregel, Unterbaugruppen und semantische Abfragen ([Doku](../docs/mechvane-mcp.md)). *Stand 2026-10-20:*
      Prototyp läuft (99 Prüfungen grün, Klappscharnier bestanden); offen: Modell-Reviews und voller Praxistest.
- [ ] **Konstrukteurs-Agent**: iterativ konstruierender Agent mit Konstruktionsregeln (`.claude/skills/konstrukteur`,
      [Bericht](../docs/research/2026-10-20-konstrukteur.md)). *Stand 2026-10-20:* `check_design` (`fdm_0.4`, `cnc_alu`)
      läuft; offen: Brückenerkennung, wählbare Druckrichtung, genauerer Randabstand.
- [ ] **Normteile-Generator** (prozedural): ISO 4762/DIN 912, ISO 4032, ISO 7089, Gewindeeinsätze, Kugellager 6000er.
      *Stand 2026-10-20:* `standard_part` bis 6005 fertig ([Bericht](../docs/research/2026-10-20-normteile-gemini.md));
      offen: Review durch zweites Modell und weitere Reihen (ISO 10642, ISO 4017).
- [ ] **Eigener offener Regelkatalog** (Nutzerwunsch 2026-10-20): belegte Werte nach [ADR 0002](../docs/adr/0002-wissenskatalog-format.md)
      samt Quellenprüfung und [Plan](../docs/research/2026-10-20-wissenskatalog-plan.md). *Stand 2026-10-23:* `katalog/` gemergt; offen: Abgleich BOLTS/FreeCAD/cq_warehouse.

### Material- und Darstellungseditor, alter Wortlaut

*Ersetzt durch „Werkstoff zuweisen über Katalog und Plugin (v0.2+)“ (Nutzer 2026-11-23).*

- [ ] **Material- und Darstellungseditor** (Nutzerwunsch 2026-10-29): Werkstoff und Aussehen je Bauteil/Fläche ([Darstellungsformat](../docs/research/2026-10-29-darstellungsformat-flash.md)).
      *Stand 2026-10-29:* [ADR 0004](../docs/adr/0004-darstellungsformat.md) (glTF-PBR) angenommen; offen: Editor und Umsetzung.

### Phase 2, Direktbearbeitung, Modell je Auftrag, PR-Mitarbeit: alte Formulierungen

*Umformuliert am 2026-11-23: Dialog (ADR 0005) und ACP-Umschaltung gehörten zur Web-UI; Wahl Python/WASM ist entschieden; `/api/params` und Stückliste.*

- [ ] **Direktbearbeitung wie Inventor** (Nutzer 2026-11-05; nach v0.1, in v0.1 über Befehlsdialog): Flächen verschieben,
      versetzen, drehen, löschen, Bohrungs-Ø ändern (STEP). *Stand 2026-11-14:* #745 ab SolidCraft 0.40 (`solidcore`) behoben;
      offen: STEP-Test, Dialog (ADR 0005), #10884 ([Testbericht](../docs/research/2026-11-06-solidcore-testbericht-3992.md)).
- [ ] **An SolidCraft per PR mitarbeiten** (Nutzer 2026-11-05, [ADR 0001](../docs/adr/0001-grundlage-solidcraft.md)
      Nachtrag): Colab-Pro-Build einrichten (`cargo xtask ci`), kleinen PR außerhalb des Kernels wählen; Kernel-Fälle
      (#745, #10884) nach solidcore (#3992). Jeder PR nur mit Nutzer-OK.
- [ ] **Herkunft von Maßen**: Berechnete Maße (Regelkatalog, Kennwertformeln, `bolted_connection`) schreiben Herleitung
      und Quelle in den Parameterkommentar; Tooltip in der UI.
- [ ] **Modell je Auftrag wählen** (Nutzer 2026-11-02): Regel-Einstufung Haiku/Sonnet/Opus (optional mit Jev),
      Sitzungswechsel über ACP `session/set_model`, Aufstufen bei Fehlschlag. *Stand 2026-11-02:* Modell wird im
      Protokoll (`agent_session`) erfasst; offen: Schwellen messen, Jev-Vergleich und Umschaltung.
      *Stand 2026-11-11:* SolidCraft RFC 0002 (WASM, #1221, PR #15110) in Phase 1; offen: Joints/eingefügte Teile
      (Phase 3), danach Wahl Python vs. WASM-Plugin.
- [ ] **Zentrale Variablen** (Nutzer 2026-11-02, [Onshape-Recherche](../docs/research/2026-11-02-onshape-features-flash.md)):
      gemeinsame Variablentabelle über Dateigrenzen hinweg (`/api/params`, `update_links`).
- [ ] **Explosionsansicht und Stückliste**: interaktive Explosion mit Animation aus Gelenkachsen sowie Stücklisten-Export.

### Risiko „96-MB-wasm“, alter Wortlaut

*Gestrichen: Demo eingefroren, die Wasm wird in Teilen geladen (`wasm-parts.js`).*

| Live-Demo hängt an einer 96-MB-wasm (Limit 100 MB je Datei beim heutigen Hosting) | Größe bei jedem SolidCraft-Wechsel messen; Ausweichort vorher prüfen (Dateigrößen-Limits der Anbieter) |

## Live-Demo vom Netz (2026-11-23, #186)

Die öffentliche Live-Demo (mechvane.dev/demo/) ist nicht mehr veröffentlicht. Aus `roadmap.json` entfielen „Live demo in the browser“ (#20), „Watch an agent session in the live demo“ (#124) und „Live demo checks your changes“ (#35, #96, #109). Der Bau bleibt mit `tools/build_demo_site.py --with-demo` erhalten (für `demo_smoke` und eine mögliche Rückkehr).
