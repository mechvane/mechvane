# Phase 0: SolidCraft zum Laufen bringen und per MCP testen

Stand 2026-10-19, SolidCraft v0.16.2 (Release vom selben Tag). Selbst getestet
auf dem Steuer-Container (x86_64, 2 Kerne, 6 GB RAM, keine GPU). Testskripte,
Ergebnisdateien und Bilder liegen unter
[`2026-10-phase0-solidcraft/`](2026-10-phase0-solidcraft/).

## Kurzfassung

- **Kein eigener Build nötig.** Jedes Release bringt fertige Pakete für Linux
  (x86_64/aarch64: tar.gz, AppImage, deb, rpm, flatpak, snap), Windows, macOS
  und FreeBSD mit, dazu die Web-App als ZIP. `solidcraft-cli` ist bis auf libc
  statisch gelinkt und läuft auf dem Steuer-Container sofort.
- **Headless-MCP funktioniert ohne GPU.** Screenshots rendert die CLI über
  Mesa llvmpipe (`renderer: gpu-software`), 20–500 ms pro Bild.
- **Referenzflansch in einem einzigen `batch`-Aufruf** (12 Befehle, 336 ms)
  gebaut. Das Volumen weicht 0,0007 % vom selbst gerechneten Wert ab, die
  Parameteränderungen rechnen korrekt nach und lassen sich exakt zurückdrehen.
- **Die Fehlermeldungen sind für Agenten sehr gut** (konkret, mit Abhilfe,
  teilweise mit Grenzwert). Schwachstellen: das undokumentierte
  Selektionsformat von `measure items` und eine Undo-Falle (siehe unten).
- **Runde 2:** Druckgehäuse, Blechwinkel und Scharnier-Baugruppe ebenfalls
  auf Anhieb maßhaltig; daraus ist der Korpus `tests/reference/` entstanden.
  Ein Bugkandidat in der schnellen Kollisionsprüfung (siehe unten).
- **Neustart-Test:** Die in Claude Code eingebundenen `mcp__solidcraft__*`-Tools
  bauen und messen den Flansch genauso wie der eigene Client. Einzige neue
  Hürde: `screenshot` schreibt nur in freigegebene Ordner (`--allow-path`).
- Bewertung für die ADR 0001: Die MCP-Schnittstelle erfüllt Grundsatz 3 der
  Roadmap (Agenten-Schnittstelle zuerst) schon weitgehend. Option A
  (Plugin-/Erweiterungsprojekt) bleibt nach diesem Test klar vorn.

## Schritt 1: Bezugsquellen

| Weg | Ergebnis |
|---|---|
| Release-Binaries | `gh release download v0.16.2 -R tangency-labs/solidcraft -p 'solidcraft-0.16.2-linux-x86_64.tar.gz'`, SHA256 gegen `SHA256SUMS.txt` geprüft. Enthält `solidcraft` (Desktop-GUI, 101 MB), `solidcraft-cli` (67 MB), `solvecraft-cli` (Kompatibilitäts-Wrapper unter dem alten Namen). |
| Installation | Nach `~/.local/opt/solidcraft-0.16.2-linux-x86_64/`, Symlink `~/.local/bin/solidcraft-cli`. Keine Systempakete, kein Root-Eingriff. |
| Web-App | https://solidcraft.io/app leitet auf https://docs.solidcraft.io/app weiter (WASM, WebGPU/WebGL2). Seite liefert aus, im Browser noch nicht bedient. Das Release enthält sie auch zum Selbsthosten (`solidcraft-web-0.16.2.zip`, 18 MB). |
| Desktop-GUI | Auf dem Steuer-Container ohne Display nicht getestet. Für Sichtprüfung: Windows-Paket auf win-cad oder die Web-App, `solidcraft --control 7878` plus `solidcraft-cli mcp --connect 127.0.0.1:7878`, dann sieht man dem Agenten beim Modellieren zu. |
| Eigener Build | Nicht nötig. Falls später nötig (eigene Patches, Upstream-Beiträge): auf apps-lxc oder einmalig in Colab-CPU, nicht auf dem Steuer-Container. |

Releasetempo: 30 reguläre Releases plus Nightlies, allein am 2026-10-17/18 vier
Versionen (0.15.0 bis 0.16.2). 100+ Contributors, ~800 Forks,
~1400 offene Issues. Das Repo unter `tangency-labs` ist auf 2026-10-07 datiert
(Umzug von `bherbruck/solidcraft`, die alte URL leitet weiter). Für die
Governance-Frage heißt das: Die API kann sich wöchentlich ändern, eine Version
sollte festgehalten werden (Testskripte prüfen gegen 0.16.2).

## Schritt 2: MCP-Anbindung

- Für künftige Claude-Code-Sessions liegt im Repo-Root `.mcp.json` mit
  `solidcraft-cli mcp` (headless). Projekt-MCP-Server muss der Nutzer beim
  ersten Start bestätigen, danach stehen die Tools (`mcp__solidcraft__*`) zur
  Verfügung.
- In dieser Session wurde der Server über einen kleinen eigenen
  stdio-JSON-RPC-Client angesprochen ([`mcpclient.py`](2026-10-phase0-solidcraft/mcpclient.py)),
  weil neu eingetragene MCP-Server erst nach einem Neustart geladen werden.
  Protokoll und Tool-Aufrufe sind dieselben, die Claude Code schickt.
- Der Server meldet 15 Tools: `list_commands`, `execute`, `batch`,
  `inspect_design`, `measure`, `body_topology`, `set_parameter`, `screenshot`,
  `export`, `crash_reports`, `undo`, `redo`, `new_design`, `open`, `save`.
- Dateizugriff ist standardmäßig eingeschränkt (Ordner des offenen Designs,
  eigener Scratch-Ordner, `--allow-path`). Ein Export nach `/root/` wurde
  korrekt mit Begründung abgelehnt.
- Upstream liefert vier Agent-Skills (`skills/solidcraft-modeling`,
  `-editing`, `-checking`, `-mechanisms`) mit Befehlsformen, Fallen und
  Antwortgrößen. Damit gelang der Flansch ohne einen einzigen
  `list_commands`-Aufruf. Seit 2026-10-19 unverändert in
  `claude-config/skills/` übernommen (Stand upstream a6b44ab), also global
  verfügbar. Abweichung zur Praxis: `solidcraft-modeling` behauptet noch, eine
  Bohrung ins Leere melde Erfolg; v0.16.2 meldet `no face at position`.

## Referenzteil: Flansch 60 × 60 × 8 mm

Vorgabe: Platte 60 × 60 × 8 mm, 4 Durchgangsbohrungen M6 auf Lochkreis 45 mm,
Fase. Umsetzung (Skript: [`flansch_mcp_test.py`](2026-10-phase0-solidcraft/flansch_mcp_test.py)):

- Parameter `A = 60 mm`, `T = 8 mm`, `bcd = 45 mm`, `dh = 6,6 mm`
  (M6 mittel nach ISO 273), `n = 4` (einheitenlos)
- Platte zentriert auf dem Ursprung (Skizze `rectangle.center`, bemaßt auf `A`),
  Extrusion `T`
- Fase 1 mm an den vier oberen Außenkanten (Kantenwahl per Weltpunkt)
- eine Bohrung als `solid.cylinder`-Schnitt bei `bcd/2·cos 45°`, dann
  `solid.pattern.circular` mit `count: "n"`

| Größe | Soll (selbst gerechnet) | SolidCraft |
|---|---|---|
| Volumen | 27 586,55 mm³ | 27 586,73 mm³ (+0,0007 %) |
| Logische Flächen | 14 | 14 (Kernel: 18, Zylinder in Halbschalen) |
| Bohrungsdurchmesser | 6,6 mm | 6,6000 mm (`measure` auf Zylinderfläche) |
| Abstand gegenüberliegender Bohrungsachsen | 45 mm | 45,000 mm (`center_distance`) |
| Bounding-Box | ±30 / ±30 / 0…8 | exakt |
| n = 6 | 27 039,1 mm³ | 27 039,4 mm³ |
| n = 6, T = 10 mm | 33 828,6 mm³ | 33 829,0 mm³ |
| Lochkreis 40 mm, Bohrungsabstand in X | 28,28 mm | ~28,4 mm (aus Draufsicht-Pixeln) |

Alle drei Parameter zurück auf den Ausgangswert ergibt bitgenau das
Ausgangsvolumen. Dieselbe Bohrung als `solid.hole` mit `clearance: "M6"`
(ISO-273-Tabelle eingebaut, `fit` close/normal/loose) ergibt dasselbe Volumen.
Export STEP AP242 (26 KB), 3MF (22 KB) und `.solidcraft` liefen ohne Fehler.
STEP noch nicht in Fusion/FreeCAD gegengeprüft.

Bilder: [Iso](2026-10-phase0-solidcraft/flansch_iso.png),
[Schnitt durch zwei Bohrungen](2026-10-phase0-solidcraft/flansch_schnitt.png),
[n = 6, T = 10](2026-10-phase0-solidcraft/flansch_n6_t10.png).

## Erfahrungen

### Fehlermeldungen (sehr gut)

| Auslöser | Antwort |
|---|---|
| Fase 20 mm an 8-mm-Platte | `20 mm is too large for this chamfer: it runs past the faces beside the edge into other geometry; the largest size that fits is 7 mm` |
| Parameter `T = 0,8 mm` (Fase 1 mm passt nicht mehr) | `set_parameter` liefert `errors: [{feature: "TopChamfer", error: "... the largest size that fits is 0.8 mm"}]`, das Modell bleibt rechenbar |
| unbekannter Befehl `solid.flange` | `unknown command solid.flange (did you mean sheet.flange?)` |
| unbekannte Skizzen-ID im `batch` | `failed: {index: 1, command, error: "unknown sketch entity p7"}`, `rolled_back: true` |
| Ausdruck mit unbekanntem Namen | `expression: unknown parameter oops` |
| Bohrung unter dem Teil (`position` im Leeren) | `no face at position; give direction` (die Skill-Doku warnt noch, dass so etwas still „erfolgreich“ sei, das ist offenbar behoben) |
| Pfad außerhalb der erlaubten Ordner | Ablehnung mit Liste der erlaubten Ordner |

Fehler kommen als Tool-Ergebnis mit `isError: true`, nicht als
JSON-RPC-Fehler, damit kann der Agent sie lesen und sich korrigieren. `batch`
ist alles oder nichts und stellt Design, aktive Skizze und Undo-Verlauf exakt
wieder her.

### Fallen

- **Undo nach einem Fehler:** Fehlgeschlagene Befehle landen nicht im
  Undo-Verlauf. Ein `undo`, um den Fehlversuch zurückzunehmen, nimmt den letzten
  *erfolgreichen* Schritt zurück (im Test still das Kreismuster). Für den
  Konstrukteurs-Agenten: nach einem Fehler nie `undo`, sondern Zustand mit
  `inspect_design` prüfen.
- **Feature- vs. Körpername:** Das Feature heißt `Plate`, der Körper `Body1`.
  `body_topology {"body":"Plate"}` scheitert. Körper sollten nach der ersten
  Extrusion umbenannt werden, oder der Agent liest `created_bodies`.
- **`measure items` ist kaum dokumentiert:** `docs/mcp.md` sagt nur „wie
  `execute` sie nimmt“. Die Fehlermeldungen nennen jeweils nur das nächste
  fehlende Feld (`type`, dann `body`, dann `index`, dann `point`). Funktioniert
  hat erst `{"type":"face","body":"Body1","index":10,"point":[x,y,z]}`, also
  Index *und* Punkt. Kandidat für eine Upstream-Verbesserung (Doku oder
  Punkt-only-Auswahl).
- **Kantenwahl per Punkt** rastet ohne Fehler auf die *nächste* Kante ein.
  Prüfen geht nur über Flächenzahl und Volumen. Positionen symmetrischer Muster
  zeigt `measure` nicht (Volumen und Schwerpunkt ändern sich bei Lochkreis
  45 → 40 nicht), dafür braucht es Screenshot oder `measure items`.

### Topologie-Abfragen

- `body_topology` (27 KB für den Flansch) liefert je Fläche einen stabilen
  Lineage-Namen, z. B. `F2:top`, `F3:blend:F2:side:l3|F2:top` (Fase zwischen
  Seitenfläche l3 und Deckfläche), `F4:side@F5.2#1` (Bohrungsmantel der
  2. Musterinstanz, Halbschale 1). Dazu Ebenennormale, Fläche, Schwerpunkt, einen
  Punkt auf der Fläche und bei Zylindern Achse, Ursprung und Radius. Kanten haben
  Mittelpunkt, Länge, Endpunkte und Namen aus den angrenzenden Flächen.
- Das ist eine gute Grundlage für das topologische Naming (Roadmap-Grundsatz 2).
  Eine *semantische* Abfrage („alle ebenen Flächen mit Normale +Z“) gibt es
  nicht, der Agent filtert das JSON selbst. Kandidat für eine inventa-Ergänzung.
- `measure items` mit zwei Flächen liefert Mindest- und Höchstabstand,
  Achsabstand und Winkel. Flächeninhalte von Flächen mit Bohrungen sind
  tesselliert gerechnet und weichen leicht ab (Deckfläche: 3227,15 mm² Soll,
  `measure` 3228,14, `body_topology` 3231,04, also bis 0,1 %). Volumina sind
  dagegen sehr genau.

### Snapshots

- `screenshot` headless: PNG als Bildblock, Ansichten `iso`/`top`/…,
  freie Orbit-Kamera (`yaw`/`pitch` in Radiant), Größe frei.
  Erster Aufruf ~500 ms, danach 20–150 ms.
- `inspect.section` mit beliebiger Ebene (`{origin, normal}`) plus Screenshot
  liefert brauchbare Schnittbilder mit Schraffur. Der Schnitt diagonal durch zwei
  Bohrungen zeigte korrekt durchgehende Bohrungen.
- Ohne MCP geht dasselbe per CLI: `solidcraft-cli snapshot design --out x.png
  --view iso` (0,4 s), `solidcraft-cli eval design` (Messwerte als JSON).
- Die 4-Ansichten-Übersicht mit Bemaßungslabels aus der Gemini-Recherche gibt es
  so nicht, nur Einzelbilder.

### Dateiformat

`.solidcraft` ist ein ZIP mit `document.json` (2,8 KB) und `container.json`,
also nicht direkt diff-bar. `solidcraft-cli script design --out x.json` gibt die
Historie als lesbares Befehlsskript aus (9 KB), das `eval` wieder abspielt.
Für die git-freundliche Ablage in inventa ist das Skript die bessere Form.

## Weitere Referenzteile (Runde 2, gleicher Tag)

Drei weitere Teile, jeweils für einen anderen Bereich, wieder über den
stdio-MCP-Client gebaut und anschließend als Korpus mit Sollwerten unter
[`tests/reference/`](../../tests/reference/) abgelegt (`check.py`, alle Checks
grün, ~10 s).

| Teil | Ergebnis |
|---|---|
| **Druckgehäuse** 80×50×30, R5, Wand 2, 4 Dome Ø7/Ø3 ([Bild](2026-10-phase0-solidcraft/gehaeuse_iso.png), [L=120, Wand 3](2026-10-phase0-solidcraft/gehaeuse_l120_wand3.png)) | Im ersten Versuch: 22 Befehle in einem `batch`, Skizze dof 0, keine Boolean-Warnungen. Volumen −0,0016 %, Schwerpunkt-Z exakt, auch nach L = 120, Wand 3, Domhöhe 28 und zurück. Kosten: Parameteränderung 0,7–2 s, `measure` 0,35 s. |
| **Blechwinkel** 60×40 + Lasche 30, t 2, R 2, K 0,44, 2× M6 ([Bild](2026-10-phase0-solidcraft/blechwinkel_iso.png), [DXF](2026-10-phase0-solidcraft/blechwinkel.dxf)) | Biegezugabe 4,5239 und Abwickellänge 66,5239 mm exakt nach Formel, Volumen gebogen und abgewickelt auf 1e-5. DXF mit Layern OUTLINE, CUT, BEND_UP, BEND_NOTES. Die Standardregel „Steel (mm)“ hat 2,5 mm, eigene Regel per `sheet.manage_rules`. `flat_pattern` und Biegetabelle sind je ~21 KB groß, weil Bohrungen zusätzlich als Punktlisten kommen. |
| **Scharnier** (Grundplatte fest, Deckel am Drehgelenk) ([Bild 90°](2026-10-phase0-solidcraft/scharnier_90.png)) | Deckel-Schwerpunkt bei 45° und 90° auf 1e-15 genau, dof richtig. Mit Kontaktsatz stoppt das Öffnen bei 180,012° (Soll 180°, Bisektion), Weiterdrehen bewegt nichts. Animiertes GIF per `motion.export_animation` in 1,7 s. |

### Neue Befunde

- **Kollisionsprüfung übersieht Durchdringung (Bugkandidat):** Ohne
  Kontaktsatz auf 210°, 240°, 270° gedreht, durchstößt der Deckel die
  Grundplatte. Die exakte Prüfung `inspect.interference` meldet das
  (Schnittfläche 996 / 575 / 498 mm²), `contact.check` und
  `motion.interference` melden dort **nichts**, nur bei 195° (wo eine Ecke
  in der Platte liegt). Die schnelle Prüfung erkennt offenbar nur Ecken im
  anderen Körper, nicht zwei Platten, die sich kreuzen. Für Agenten heißt das:
  Kollisionen mit `inspect.interference` bestätigen. Gemeldet als
  [#3323](https://github.com/tangency-labs/solidcraft/issues/3323) (2026-10-19,
  auf v0.16.2 nachgebaut: bei 210°/240°/270° meldet `contact.check` nichts,
  Überlappung 720/416/360 mm³).
- **Skill-Stand ≠ Release:** `solidcraft-mechanisms` beschreibt `joint.sweep`,
  das es in v0.16.2 nicht gibt (`unknown command`). Die Skills folgen `main`.
  Bei einem Update von SolidCraft also die Skills vom passenden Tag kopieren,
  nicht von `main`.
- `occurrence.properties` liefert den Schwerpunkt pro Körper
  (`bodies[0].center_of_mass`), nicht auf oberster Ebene.
- Ein Kontaktstopp landet bis ~0,01° hinter dem Kontakt, das ergibt eine
  kleine Überschneidung (hier 6,8 mm³, 0,008 mm tief).

### Slicer-Probe

Das Gehäuse lief als STL (`solidcraft-cli run gehaeuse.build.json --out
gehaeuse.stl`) direkt durch die vorhandene Headless-Cura-Kette
(`/opt/cura-headless/cura_slice.py`, Profil 03_Normal, Extrudr PLA NX2):
4:00 h, 30,2 g, 199 Schichten ([Vorschau](2026-10-phase0-solidcraft/gehaeuse_cura_vorschau.png)).
Nicht gedruckt. Gewünscht ist aber ein **grafischer Slicer als Plugin**, den
der Nutzer selbst bedient, siehe ROADMAP Phase 2.

## Neustart-Test: eingebundene MCP-Tools (Session 2, 2026-10-19)

In einer neuen Claude-Code-Session über `.mcp.json` geladen: Die
`mcp__solidcraft__*`-Tools (15 Stück, als „deferred tools“ geladen) laufen
ohne weitere Einrichtung. Der Flansch aus
[`tests/reference/flansch.build.json`](../../tests/reference/flansch.build.json)
wurde unverändert als ein `batch` gebaut ([Bild](2026-10-phase0-solidcraft/flansch-mcp-tools.png)).

| Prüfung | Soll | MCP-Tools |
|---|---|---|
| `batch`, 12 Schritte | ok | ok, 341 ms (davon Kreismuster 241 ms) |
| Volumen | 27 586,55 mm³ | 27 586,73 mm³ (+6,6e-6) |
| Bounding-Box | ±30 × ±30 × 0…8 | exakt |
| Bohrung (`measure items`, Fläche 10) | Ø 6,6 | Ø 6,6000, beide Halbschalen als ein Zylinder erkannt |
| Achsabstand zweier Bohrungen | 45·sin 45° = 31,820 | 31,8198 |
| `screenshot` iso | – | ok, Software-Renderer |

Befunde:

- **`screenshot path` ist eingesperrt:** Pfade außerhalb von
  `~/.local/share/solidcraft/recovery` und einem Temp-Ordner
  `/tmp/solidcraft-mcp-<pid>-…` lehnt der Server ab („outside the folders this
  agent may use; allow another folder with `--allow-path DIR`“). Für Bilder im
  Repo entweder in den Temp-Ordner schreiben und kopieren oder den Ordner
  freigeben. `.mcp.json` gibt jetzt `docs/research` per `--allow-path` frei
  (wirkt ab dem nächsten Neustart des MCP-Servers).
- `measure items` ohne `index` bricht ab („missing field `index`“), der Punkt
  allein reicht nicht (bekannt, siehe oben). Den Index liefert
  `body_topology`, das für den Flansch rund 27 KB kostet. Für Agenten ist ein
  Auswählen nur per Punkt oder Lineage-Namen wünschenswert.
- Das Verhalten ist sonst identisch mit dem eigenen stdio-Client, die Tools
  sind also als Hauptweg für Agenten brauchbar.

## Offen für Phase 0

- STEP-Export in Fusion (win-cad) gegenprüfen: Volumen, Bohrungen als Zylinder
- Zeichnungen (`docs/drawing-foundations.md`), Plugins (#1221) ansehen
- Desktop- oder Web-App mit `--control` bedienen und dem Agenten zusehen,
  dabei den Browser/Feature-Baum ansehen (ROADMAP-Grundsatz 5). SolidCraft
  folgt Fusion mit einer Timeline (`timeline.*`), hat aber auch einen Browser
  (`browser.visibility` mit Ordnern). Optisch kommt der linke Verlauf
  nahe an Inventor, im Datenmodell nicht (eine Feature-Liste fürs ganze
  Design, Skizzen als eigene Einträge), siehe
  [Bericht](2026-10-19-solidcraft-baum-plugins-zeichnungen.md).
- ~~Governance~~ erledigt, siehe
  [Bericht](2026-10-19-solidcraft-baum-plugins-zeichnungen.md). Kollisions-Bug
  gemeldet (#3323), Frage nach Plugin-Panels in #1221 gestellt
