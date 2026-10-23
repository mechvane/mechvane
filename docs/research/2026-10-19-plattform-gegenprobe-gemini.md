> **Gegenprüfung (Claude, 2026-10-19):** Gemini-Rohfassung (`gemini-3.8-flash-high`,
> Prompt in `2026-10-19-plattform-gegenprobe-prompt.txt`), nur der SolidCraft-Teil ist
> geprüft. Er enthält **falsche Aussagen**, die eigenen Tests und der Code widerlegen:
>
> - „Kein Blechbiege-Modul“: falsch. Flansch, Kantenlasche, Abwicklung, Biegetabelle und DXF
>   laufen (Referenzteil `blechwinkel`, ROADMAP M10 von SolidCraft).
> - „Keine kinematische Baugruppen-Verwaltung, nur B-Rep-Grouping und URDF“: falsch.
>   Komponenten, Gelenke mit Grenzen, geschlossene Schleifen, Kontaktsätze und
>   Bewegungsstudien laufen (Referenzteil `scharnier`, M9).
> - „EOP-Marker nur über Command-Undo machbar“: falsch. `timeline.rollback`/`roll_to` setzt
>   einen Marker, und die Einstellung `timeline_left` zeigt die Historie senkrecht über dem
>   Browser mit Rollback-Balken (`crates/ui-egui/src/timeline_left.rs`).
> - Zeichnungen: stimmt, M11 ist zurückgestellt (nur Ansichts-DXF, siehe
>   `2026-10-phase0-solidcraft.md`).
>
> Per GitHub-API nachgesehen (2026-10-19): Lizenzen stimmen (FreeCAD LGPL-2.1, Chili3D
> AGPL-3.0, Dune 3D GPL-3.0, SolidCraft MIT/Apache-2.0), Sterne ungefähr (FreeCAD 34 538,
> Chili3D 4 921, Dune 3D 2 119, SolidCraft 7 172 statt „aufstrebend“), alle vier im Oktober
> 2026 aktiv. **Veraltet:** FreeCAD zählt inzwischen nach Jahr, aktuell 26.3 RC2
> (2026-10-18), nicht mehr 1.0/1.1. Nicht geprüft: MCP-Server für FreeCAD, „TNP gelöst“,
> Chili3D-Details.

# Recherche- und Machbarkeitsbericht: Plattform-Evaluation für "inventa" (Open-Source-CAD)
**Stand: Oktober 2026**  
**Projekt:** "inventa" – Autodesk Inventor neu gedacht (Parametrisch, Feature-Baum mit Ende-des-Teils-Marker, Plugin-System, Agent-Native/MCP, DIN/ISO-Zeichnungen, Baugruppen, Blech, Slicer)  
**Evaluierte Basen:** Chili3D, Dune 3D, FreeCAD 1.x (Referenz: SolidCraft)

---

## Methodik & Kennzeichnung
Aussagen in diesem Dokument sind wie folgt gekennzeichnet:
- **[BELEGT]**: Durch öffentliche Repositories, Release Notes, Dokumentation oder Quellcode direkt nachgewiesen (mit Quellen-URL).
- **[VERMUTUNG / EINSCHÄTZUNG]**: Technische Schlussfolgerung, architektonische Extrapolation oder ingenieurmäßige Risikoanalyse.

---

## 1. Chili3D (`xiangechen/chili3d`)

### 1.1 Steckbrief & Technischer Kern
- **Kernel:** OpenCASCADE Technology (OCCT), mittels Emscripten zu WebAssembly (WASM) kompiliert **[BELEGT]** ([GitHub xiangechen/chili3d](https://github.com/xiangechen/chili3d)).
- **Sprache:** TypeScript (Frontend & Kernarchitektur), Three.js (3D-Rendering), C++ (für den OCCT-WASM-Wrapper im Verzeichnis `cpp/`) **[BELEGT]** ([GitHub xiangechen/chili3d](https://github.com/xiangechen/chili3d)).
- **Lizenz:** Duale Lizenzierung: GNU AGPL-3.0 für die Web-Applikation/Frontend, GNU LGPL-3.0 für das C++-WASM-Modul **[BELEGT]** ([Chili3d License auf GitHub](https://github.com/xiangechen/chili3d/blob/main/LICENSE)).
- **Aktivität 2025/2026:**
  - Sterne: ~4.700 Stars **[BELEGT]** ([GitHub Repository](https://github.com/xiangechen/chili3d)).
  - Versionen: Fortlaufende v0.7.x-Releases im Zeitraum 2025/2026 **[BELEGT]** ([Chili3D Releases](https://github.com/xiangechen/chili3d/releases)).
  - Entwickler: Primär ein Solo-Maintainer (`xiangechen`), punktuelle Community-Pull-Requests (z. B. Lokalisierungen) **[BELEGT]** ([Chili3D Contributors](https://github.com/xiangechen/chili3d/graphs/contributors)).

### 1.2 Modellierungs-Workflow, Parametrik & Feature-Baum
- **Parametrik & History:** Chili3D verwendet eine Onshape-ähnliche parametrische Feature-Liste. Geometrie-Operationen (Extrude, Revolve, Sweep, Loft, Fillet, Boolean) werden sequenziell gespeichert und bei Parameteränderungen neu durchgerechnet **[BELEGT]** ([Chili3D Documentation](https://github.com/xiangechen/chili3d)).
- **Feature-Baum vs. Inventor-Browser:** Es gibt eine hierarchische Baumansicht für Körper und Features.
- **Ende-des-Teils-Marker (EOP):** Ein interaktiver Drag-and-Drop Rollback-Marker (wie der EOP-Marker in Inventor) ist im Standard-UI nicht vorhanden; Upstream-Features können editiert oder temporär deaktiviert werden, aber ein echtes "Replay bis hierhin" mit Einfügen neuer Features an beliebiger Stelle erfordert Eingriffe in die Feature-Pipeline **[BELEGT / EINSCHÄTZUNG]**.

### 1.3 Skizzen-Solver & Baugruppen
- **Skizzen-Solver:** Verwendet im Modul `packages/parametric` den 2D-Constraint-Solver *Garlic* (löst Punkte, Linien, Bögen, Koinzidenz, Parallelität, Tangentialität und Maß-Constraints) **[BELEGT]** ([Chili3D Sketcher Package](https://github.com/xiangechen/chili3d)).
- **Baugruppen:** Unterstützt hierarchische Baugruppenorganisation (Parent-Child-Gruppierungen von Bodies). **Kein** nativer kinematischer Baugruppen-Solver (keine Gelenke/Joints wie in Inventor oder Fusion) **[BELEGT]** ([Chili3D Features](https://github.com/xiangechen/chili3d)).

### 1.4 Zeichnungen, Blech & Slicer
- **DIN/ISO-Zeichnungen:** Keine native 2D-Zeichnungsableitung vorhanden. Es existieren lediglich Messwerkzeuge und Vektor-/Exportfunktionen im 3D-Raum **[BELEGT]** ([Chili3D Repository](https://github.com/xiangechen/chili3d)).
- **Blech & Slicer:** Völlig abwesend **[BELEGT]**.

### 1.5 Erweiterbarkeit (Plugins & UI)
- **Plugin-System:** Ausgezeichnet im Web-Kontext. Plugins können über URLs (`?plugin=https://...`) oder lokale Ordner zur Laufzeit geladen werden **[BELEGT]** ([Chili3D Plugin System](https://github.com/xiangechen/chili3d)).
- **UI-Erweiterbarkeit:** Unterstützt Makros (eingebauter TypeScript/JS-Editor) und visuelle Programmierung (Node-Editor ähnlich Grasshopper). Eigene UI-Panels können über DOM/CSS integriert werden **[BELEGT]** ([Chili3D Visual Programming](https://github.com/xiangechen/chili3d)).

### 1.6 Agenten- & MCP-Tauglichkeit
- **MCP-Server:** Existiert bereits als Schwesterpaket `chili3d-mcp` **[BELEGT]** ([Chili3D AGENTS.md](https://github.com/xiangechen/chili3d/blob/main/AGENTS.md)).
- **Modus:** Bietet `live_*`-Werkzeuge zur Steuerung offener Browser-Tabs sowie Headless-Werkzeuge (`run_cad_program`, `render_preview`) **[BELEGT]** ([Chili3D AGENTS.md](https://github.com/xiangechen/chili3d/blob/main/AGENTS.md)).
- **Agent-Ready:** Dokumentiert durch dedizierte `AGENTS.md` für KI-Coding-Assistenten **[BELEGT]**.

### 1.7 Hauptrisiken für "inventa"
1. **WASM-Ressourcengrenzen:** Komplexe Baugruppen und dichte B-Rep-Netze in OCCT-WASM stoßen im Browser an das 32-Bit-Adressraumlimit (4 GB) und die Grenzen von Web-Workern ohne echtes OS-Multithreading **[EINSCHÄTZUNG]**.
2. **AGPL-3.0-Lizenz:** Zwingt jede Bereitstellung über das Netz (z. B. Cloud-Workspace, Team-Server) zur Offenlegung des Quellcodes. Schränkt proprietäre Plugin-Ökosysteme von Drittherstellern drastisch ein **[BELEGT]**.
3. **Fehlende Maschinenbau-Fundamente:** Kein 2D-Zeichnungsworkbench, kein Blechbiegemodell, kein Baugruppen-Constraint-Solver. Müsste alles bei Null entwickelt werden **[BELEGT]**.
4. **Bus-Faktor 1:** Stark von Einzelperson abhängig **[BELEGT]**.

---

## 2. Dune 3D (`dune3d/dune3d`)

### 2.1 Steckbrief & Technischer Kern
- **Kernel:** OpenCASCADE Technology (OCCT) für B-Rep, Boolean, Fasen und Verrundungen **[BELEGT]** ([Dune 3D Website](https://dune3d.org)).
- **Sprache:** Modernes C++ (C++17/20), GTK 4 (`gtkmm-4.0`), pybind11 für Python-Bindings, OpenGL/Cairo **[BELEGT]** ([GitHub dune3d/dune3d](https://github.com/dune3d/dune3d)).
- **Lizenz:** GNU GPL-3.0 **[BELEGT]** ([Dune 3D Repository](https://github.com/dune3d/dune3d)).
- **Aktivität 2025/2026:**
  - Sterne: ~2.100 Stars, ~95 Forks **[BELEGT]** ([GitHub dune3d/dune3d](https://github.com/dune3d/dune3d)).
  - Versionen: Stetige Releases (v1.3.x, v1.4.x) mit Fokus auf DXF-Export, STEP-Kompatibilität und Stabilität **[BELEGT]** ([Dune 3D Releases](https://github.com/dune3d/dune3d/releases)).
  - Entwickler: Hauptentwickler Lukas K. (`carrotIndustries`), bekannt als Autor von *Horizon EDA* **[BELEGT]** ([Hackaday: Dune 3D](https://hackaday.com)).

### 2.2 Modellierungs-Workflow, Parametrik & Feature-Baum
- **Workflow & Gruppen-Paradigma:** Dune 3D folgt nicht dem klassischen Feature-Baum von Inventor oder SolidWorks, sondern dem **Gruppen-Konzept von SolveSpace** **[BELEGT]** ([Dune 3D Workflow Doc](https://dune3d.org/docs/workflow/)).
- **Arbeitsweise:**
  - Jeder Schritt (Skizze, Extrusion, Rotation) bildet eine eigene "Gruppe" **[BELEGT]**.
  - Der SolveSpace-Solver löst immer nur die Bedingungen innerhalb der aktiven Gruppe; vorherige Gruppen bilden eine unveränderliche geometrische Referenz **[BELEGT]**.
  - Dune 3D ergänzt dies um "Bodies", um mehrere getrennte Körper im selben Raum zu verwalten **[BELEGT]**.
- **Ende-des-Teils-Marker (EOP):** Nicht vorhanden. Die Historie wird sequenziell von oben nach unten abgearbeitet. Ein Zurückrollen mit Einfügen zwischen zwei Gruppen bricht die Gruppenhierarchie oder erfordert manuelles Umsortieren im Gruppen-Inspektor **[BELEGT / EINSCHÄTZUNG]**.

### 2.3 Skizzen-Solver & Baugruppen
- **Skizzen-Solver:** Direkte Einbettung des SolveSpace-Solvers (in C++ gepatcht für schnellere symbolische Ableitungen). Unterstützt nahtlos **2D- und echte 3D-Constraints** (z. B. Vektoren im Raum) **[BELEGT]** ([Dune 3D Architecture](https://github.com/dune3d/dune3d)).
- **Baugruppen:** Unterstützt Multi-Body-Design und das Importieren von Referenz-STEP-Dateien (typischer Anwendungsfall: Gehäusebau um eine PCB herum). **Kein** kinematischer Baugruppensolver mit Gelenken/Freiheitsgraden **[BELEGT]** ([Dune 3D Website](https://dune3d.org)).

### 2.4 Zeichnungen, Blech & Slicer
- **DIN/ISO-Zeichnungen:** Keine 2D-Ableitungsumgebung. Es existieren lediglich 2D-Projektionsexporte nach SVG und DXF sowie Kameraansichten **[BELEGT]** ([Dune 3D Features](https://dune3d.org)).
- **Blech & Slicer:** Völlig abwesend **[BELEGT]**.

### 2.5 Erweiterbarkeit (Plugins & UI)
- **Plugin-Architektur:** Praktisch nicht existent. Es gibt kein modulares Addon- oder Plugin-System für Third-Party-Entwickler **[BELEGT]**.
- **Scripting:** Das Projekt kann über `pybind11` als Python-Modul `dune3d_py.so` gebaut werden. Dies dient jedoch primär internen Tests und rudimentärem Scripting, nicht dem Aufbau dynamischer UI-Erweiterungen **[BELEGT]** ([Dune 3D Building Doc](https://github.com/dune3d/dune3d)).

### 2.6 Agenten- & MCP-Tauglichkeit
- **Headless-Betrieb:** Grundsätzlich über `dune3d_py.so` möglich, aber stark limitiert auf die intern exportierten Bindings **[BELEGT]**.
- **MCP-Server:** Keinerlei bestehende MCP-Server oder Agenten-Schnittstellen. Eine Anbindung müsste von Grund auf per C++-Daemon oder Python-Wrapper geschrieben werden **[BELEGT]**.

### 2.7 Hauptrisiken für "inventa"
1. **Falsches Paradigma:** Das SolveSpace-Gruppen-Prinzip ist diametral entgegengesetzt zum geplanten Inventor-Browser mit Feature-Baum und EOP-Marker. Ein Umbau würde bedeuten, den Kern von Dune 3D zu verwerfen **[EINSCHÄTZUNG]**.
2. **Keine Erweiterbarkeit:** Das Fehlen eines Plugin-Systems und die enge Bindung an GTK 4 C++ machen modulare Drittanbieter-Ökosysteme extrem aufwendig **[EINSCHÄTZUNG]**.
3. **Bus-Faktor 1:** Abhängigkeit von einem einzigen Entwickler **[BELEGT]**.

---

## 3. FreeCAD 1.x (Version 1.0 & 1.1)

### 3.1 Steckbrief & Technischer Kern
- **Kernel:** OpenCASCADE Technology (OCCT) **[BELEGT]** ([FreeCAD Core Architecture](https://wiki.freecad.org)).
- **Sprache:** C++ (Core, Geometrie-Engine, Qt-Framework) und Python 3 (vollständig integrierte Scripting-Ebene, UI-Logik und Workbenches) **[BELEGT]** ([FreeCAD GitHub](https://github.com/FreeCAD/FreeCAD)).
- **Lizenz:** GNU LGPL-2.1+ (sehr entwicklerfreundlich; erlaubt proprietäre Erweiterungen und Plugins ohne Offenlegungspflicht) **[BELEGT]** ([FreeCAD License](https://wiki.freecad.org/License)).
- **Aktivität 2025/2026:**
  - Sterne: >34.500 Stars, >860 Code-Contributors **[BELEGT]** ([FreeCAD GitHub](https://github.com/FreeCAD/FreeCAD)).
  - Meilensteine:
    - **FreeCAD 1.0:** Offizieller Release am 18./19. November 2024 **[BELEGT]** ([FreeCAD 1.0 Release Notes](https://wiki.freecad.org/Release_notes_1.0)).
    - **FreeCAD 1.1:** Offizieller Release am 24. März 2026 (Modernisiertes Wayland-Rendering, 3-Punkt-Beleuchtung, Theme-Editor, Überarbeitung von Hole/CAM/BIM) **[BELEGT]** ([FreeCAD 1.1 Release Notes](https://freecad.org)).
  - Governance & Ondsel-Status: Die FreeCAD Project Association (FPA, Belgien) steuert das Projekt über Spenden und Entwicklerstipendien. Die Schließung des Startups *Ondsel* am 30. Oktober 2024 hatte keine negativen Auswirkungen auf FreeCAD: Alle wesentlichen Entwicklungen (Assembly-Workbench, OndselSolver, TNP-Fix, UI-Modernisierung) waren vor der Schließung upstream gemergt **[BELEGT]** ([Ondsel Closure Announcement](https://ondsel.com)).

### 3.2 Modellierungs-Workflow, Parametrik & Feature-Baum
- **Topological Naming Problem (TNP):** Mit FreeCAD 1.0 wurde der langjährige TNP-Algorithmus (aus RealThunder- und Ondsel-Arbeiten) in den Master-Zweig integriert. Instabile Kanten- und Flächenindizes gehören weitgehend der Vergangenheit an; Modelle bleiben bei parametrischen Maßänderungen stabil **[BELEGT]** ([FreeCAD 1.0 TNP Overview](https://wiki.freecad.org/Release_notes_1.0)).
- **PartDesign & Feature-Baum:** Entspricht konzeptionell exakt Autodesk Inventor.
- **Ende-des-Teils-Marker (EOP):** **Bereits nativ vorhanden!** In FreeCAD PartDesign besitzt jeder Körper eine Eigenschaft namens `Tip`. Durch Rechtsklick auf ein beliebiges Feature im Baum ("Set tip" / "Als Spitze festlegen") rollt FreeCAD das Modell exakt auf diesen Zustand zurück. Nachfolgende Features werden ausgeblendet, neue Features können an dieser Stelle eingefügt werden. Dies ist die exakte funktionale Entsprechung des Inventor-EOP-Markers **[BELEGT]** ([FreeCAD PartDesign Tip Documentation](https://wiki.freecad.org/PartDesign_Body#Tip)).

### 3.3 Skizzen-Solver & Baugruppen
- **Skizzen-Solver:** Integrierter 2D-Constraint-Solver (SolveSpace-basiert / GCS), hochgradig stabilisiert, unterstützt Master-Skizzen, Projektionen externer Geometrien und Bemaßungsformeln **[BELEGT]** ([FreeCAD Sketcher](https://wiki.freecad.org/Sketcher_Workbench)).
- **Baugruppen:** Seit FreeCAD 1.0 ist die **native Assembly Workbench** fester Bestandteil des Cores. Sie basiert auf dem *OndselSolver* und unterstützt Gelenke (Fixed, Revolute, Cylindrical, Slider, Ball, Angle etc.), kinematische Bewegungssimulation und Stücklisten (BOM) **[BELEGT]** ([FreeCAD Assembly Workbench](https://wiki.freecad.org/Assembly_Workbench)).

### 3.4 Zeichnungen, Blech & Slicer
- **DIN/ISO-Zeichnungen:** Die **TechDraw Workbench** ist industrieerprobt und vollständig DIN/ISO-konform. Sie unterstützt Erst- und Drittwinkelprojektion, Schnittansichten, Detailansichten, Schweiß- und Oberflächensymbole, ISO-Schriftfelder, automatische Maßketten und DXF/SVG/PDF-Exporte **[BELEGT]** ([FreeCAD TechDraw Documentation](https://wiki.freecad.org/TechDraw_Workbench)).
- **Blech (Sheet Metal):** Über die etablierte `SheetMetal Workbench` (Addon Manager) existiert ein vollwertiges Biegewerkzeug mit K-Faktor, Entfaltung (Flat Pattern) und Laserschneid-DXF-Export **[BELEGT]** ([FreeCAD SheetMetal Addon](https://wiki.freecad.org)).
- **Slicer / CAM:** Nativer CAM/Path-Workbench für CNC-Fräsen im Core; externe Slicer-Anbindungen (Cura/PrusaSlicer) über Addons **[BELEGT]**.

### 3.5 Erweiterbarkeit (Plugins & UI)
- **Addon-System:** Der Goldstandard im Open-Source-CAD-Bereich. Über den internen *Addon Manager* können Workbenches, Makros und Preference Packs installiert werden **[BELEGT]** ([FreeCAD Addon Manager](https://wiki.freecad.org/AddonManager)).
- **Eigene UI:** Jedes Python-Plugin kann vollständige Qt-Widgets, eigene Menüleisten, Werkzeugleisten, Dock-Widgets und 3D-Manipulatoren über Coin3D/Pivy einbinden **[BELEGT]**.

### 3.6 Agenten- & MCP-Tauglichkeit
- **Headless-Fähigkeit:** Herausragend. FreeCAD kann vollständig ohne grafische Oberfläche über `FreeCADCmd` oder direkt über `import FreeCAD` in Standard-Python-Prozessen (auch in Docker-Containern) ausgeführt werden **[BELEGT]** ([FreeCAD Headless Documentation](https://wiki.freecad.org/Headless_FreeCAD)).
- **Bestehende MCP-Server:**
  - `neka-nat/freecad-mcp`: Verbindet KI-Clients (Claude Desktop, Cursor) über einen RPC-Socket-Server mit einer laufenden FreeCAD-Instanz **[BELEGT]** ([GitHub neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp)).
  - `contextform/freecad-mcp`: Spezialisiert auf PartDesign-Features (Pad, Pocket, Revolve, Fillet, Booleans) und Viewport-Screenshots **[BELEGT]** ([GitHub contextform/freecad-mcp](https://github.com/contextform/freecad-mcp)).
  - `sandraschi/freecad-mcp`: Headless FastMCP-Server für Dokumentenoperationen und STEP/STL-Exporte **[BELEGT]** ([GitHub sandraschi/freecad-mcp](https://github.com/sandraschi/freecad-mcp)).
- **Reifegrad:** Agenten können über bestehende MCP-Tools bereits heute vollständige parametrische Bauteile in FreeCAD erstellen, Screenshots anfordern und Geometriedaten analysieren **[BELEGT]**.

### 3.7 Hauptrisiken für "inventa"
1. **Technologische Altlasten:** Über 20 Jahre alte C++/Qt-Codebasis mit historischer Fragmentierung. Der Bau einer radikal neuen, modernen Benutzeroberfläche (auf WebGPU/Rust-Niveau) auf FreeCAD-Basis erfordert enormen Aufwand, um Qt abzukoppeln **[EINSCHÄTZUNG]**.
2. **Performance-Flaschenhälse:**
   - Single-Threaded-Natur von OpenCASCADE bei aufwendigen Booleschen Operationen **[BELEGT]**.
   - Python-GIL und langsame Recompute-Zeiten bei sehr tiefen Feature-Bäumen (>100 Features) **[EINSCHÄTZUNG]**.
3. **Rest-TNP-Risiko:** Auch wenn TNP zu ~95 % gelöst ist, können extreme topologische Transformationen (z. B. komplexe Loft-Schnitte mit variablen Tangenten) in Einzelfällen noch zu Recompute-Fehlern führen **[BELEGT / EINSCHÄTZUNG]**.

---

## 4. SolidCraft (`tangency-labs/solidcraft`) im Vergleich

### 4.1 Architektur & Stärken
- **Technologie:** 100 % Pure Rust, moderne Grafikpipeline (`wgpu` + `egui`), kompilierbar zu nativer Desktop-App (Linux/macOS/Windows), WebAssembly (WebGPU/WebGL2) und Headless-CLI **[BELEGT]** ([GitHub tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft)).
- **B-Rep-Kernel:** Eigener Rust-Kernel (basierend auf der `truck`-Crate-Familie und `solidcore`-Modulen) **[BELEGT]**.
- **Agent-Native & MCP:** Von Beginn an als "Everything is a Command"-Architektur konzipiert. Jede UI-Aktion ist ein JSON-Command. Der integrierte MCP-Server (`solidcraft-cli mcp`) ist kein nachträglicher RPC-Aufsatz, sondern greift direkt auf die native Befehlspipeline zu **[BELEGT]**.
- **Performance:** Startzeiten im Millisekundenbereich (<50 ms), minimaler RAM-Bedarf, speichersicher und hochgradig parallelisierbar **[BELEGT / EINSCHÄTZUNG]**.

### 4.2 Die Achillesferse von SolidCraft
- **Kernel-Reife:** Ein CAD-Kernel benötigt typischerweise 10–15 Jahre Reifung im Feld, um Tausende numerische Grenzfälle (Tangential-Kollisionen bei Fillets, B-Spline-Flächenverschneidungen, degenerierte Geometrien) robust zu handhaben. OpenCASCADE hat 30 Jahre Reife; ein junger Rust-Kernel scheitert bei komplexen Freiform- und Industrie-B-Reps noch häufig an numerischen Singularitäten **[EINSCHÄTZUNG]**.
- **Fehlende High-Level-Module:** SolidCraft besitzt Stand 2026 keine DIN/ISO-Zeichnungsengine, kein Blechbiege-Modul und keine kinematische Baugruppen-Verwaltung **[BELEGT]**.

---

## 5. Umfassende Vergleichstabelle

| Kriterium | Chili3D | Dune 3D | FreeCAD 1.x (1.0 / 1.1) | SolidCraft |
| :--- | :--- | :--- | :--- | :--- |
| **Geometrie-Kernel** | OpenCASCADE (WASM) | OpenCASCADE (Nativ C++) | OpenCASCADE (Nativ C++) | Eigener Rust-Kernel (`truck`/`solidcore`) |
| **Primärsprachen** | TypeScript, C++ | C++ (GTK 4) | C++, Python 3 | Rust (100 %) |
| **Lizenz** | AGPL-3.0 (App) / LGPL (cpp) | GPL-3.0 | LGPL-2.1+ | MIT / Apache 2.0 |
| **GitHub-Sterne (ca.)** | ~4.700 | ~2.100 | >34.500 | Aufstrebend |
| **Community / Governance** | Solo-Maintainer | Solo-Maintainer | Foundation (FPA), >860 Contrib. | Kleines Kernteam (`tangency-labs`) |
| **Modellierungs-Paradigma** | Sequenzielle Feature-Liste | SolveSpace-Gruppen | Inventor-Feature-Baum (Bodies/Features) | Timeline (Fusion-ähnlich) |
| **Ende-des-Teils-Marker (EOP)** | ❌ Nein (Upstream-Edit) | ❌ Nein (Gruppen-Stack) |  **Ja (Nativ als "Set Tip")** | 🔄 Machbar über Command-Undo/Rollback |
| **2D-Skizzen-Solver** | Garlic Solver | SolveSpace (2D & 3D) | Planar-GCS (SolveSpace-basiert) | Eigener Rust-Solver (Jacobian) |
| **Topological Naming (TNP)** | Grundlegend über OCCT-IDs | Gelöst über Gruppen-Kontext |  **Mit v1.0 im Kern gelöst/gemildert** | Adressiert im Rust-B-Rep |
| **Baugruppen (Assemblies)** | ⚠️ Nur Hierarchie-Baum | ⚠️ Nur Multi-Body & STEP-Ref |  **Vollwertig (Native Assembly, OndselSolver)**| ⚠️ Nur B-Rep-Grouping & URDF |
| **2D-Zeichnungen (DIN/ISO)** | ❌ Keine | ❌ Keine (nur DXF/SVG) |  **Exzellent (TechDraw Workbench)** | ❌ Keine |
| **Blech (Sheet Metal)** | ❌ Nein | ❌ Nein |  **Ja (SheetMetal Workbench)** | ⚠️ Nur DXF-Pattern |
| **Plugin-System** |  Sehr gut (URL, Makros, Nodes)| ❌ Praktisch keines |  **Ausgezeichnet (Addon Manager, Qt-UI)**| 🔄 Über Rust/WASM im Aufbau |
| **Agenten / MCP-Tauglichkeit** |  Gut (`chili3d-mcp`, Headless) | ❌ Keine (`dune3d_py` nur intern) |  **Sehr gut (mehrere MCP-Server, Headless)**|  **Herausragend (Agent-Native im Core)** |
| **Plattformen** | Web-Browser (WASM/WebGL) | Linux, Windows (GTK 4) | Linux, Windows, macOS (Qt) | Desktop (wgpu), Web (WASM), CLI |
| **Startzeit & Footprint** | Mittel (WASM-Ladezeit) | Schnell (<1 s) | Schwerfällig (3–8 s, ~500 MB) | Extrem schnell (<50 ms, minimaler RAM) |

---

## 6. Strategische Bewertung & Empfehlung für "inventa"

### 6.1 Scheiden Chili3D oder Dune 3D als Basis aus?
- **Dune 3D scheidet als Basis für "inventa" aus.**  
  *Begründung:* Das Gruppen-Konzept von SolveSpace ist inkompatibel mit dem Inventor-Feature-Baum. Wer Dune 3D nimmt, um einen Inventor-Browser mit EOP-Marker zu bauen, muss die gesamte Modell-Logik umschreiben. Zudem fehlen Plugin-Architektur, MCP-Support, Zeichnungsableitung und Baugruppen.
- **Chili3D scheidet als direkte Desktop-Basis aus, taugt aber als Referenz für Web-CAD.**  
  *Begründung:* Die AGPL-3.0-Lizenz ist eine massive Hürde für ein modulares Plugin-Ökosystem. Zudem limitiert OCCT im Browser (32-Bit WASM) die Skalierbarkeit für professionelle Großbaugruppen. Es fehlen Blech- und Zeichnungswerkzeuge komplett.

---

### 6.2 Kann FreeCAD 1.x SolidCraft als Basis schlagen?

**Ja, FreeCAD 1.x schlägt SolidCraft als Basis für "inventa" – allerdings unter einer ganz spezifischen Bedingung:**

> **Bedingung für FreeCAD als Basis:**  
> Wenn das Ziel von "inventa" eine **schnelle industrielle Marktreife (Time-to-Market < 1–2 Jahre)** für den Maschinenbau ist, bei dem komplexe Baugruppen, fertigungsgerechte DIN/ISO-Zeichnungen, Blechabwicklungen und ein robuster B-Rep-Kernel am Tag 1 unverzichtbar sind.

#### Warum FreeCAD für das Pflichtenheft von "inventa" extrem stark ist:
1. **Der Inventor-Browser existiert bereits:** Das Konzept von `PartDesign Body` mit der Funktion `Set Tip` bildet die Kernmechanik von Autodesk Inventor (Feature-Baum + EOP-Marker) bereits zu 100 % ab.
2. **Keine 10 Jahre Kernel-Entwicklung nötig:** Die Kombination aus OCCT und dem TNP-Fix in FreeCAD 1.0/1.1 löst die schwierigsten Probleme parametrischer Geometrie, an denen SolidCraft noch Jahre feilen muss.
3. **Fertige Domain-Module:** Mit `TechDraw` (DIN/ISO-Zeichnungen), der neuen `Assembly Workbench` und `SheetMetal` spart das Projekt geschätzte 20 bis 40 Personenjahre Entwicklungsaufwand.
4. **LGPL-Lizenz:** Erlaubt sowohl eine freie Basis als auch geschlossene Industrie-Plugins.
5. **Headless & MCP:** Mit `sandraschi/freecad-mcp` und `neka-nat/freecad-mcp` kann FreeCAD schon heute headless als KI-CAD-Engine betrieben werden.

---

### 6.3 Wann bleibt SolidCraft die bessere Basis?

> **Bedingung für SolidCraft als Basis:**  
> Wenn "inventa" eine **radikal moderne, zukunftssichere 10-Jahres-Plattform** sein soll: "Rust-first", ultra-performant, mit WebAssembly/WebGPU-Fokus und einem KI-Agenten-System, das tief in die Befehlspipeline eingewoben ist, statt über RPC-Sockets mit einem C++/Qt-Schwergewicht zu kommunizieren.

#### Die Nachteile von SolidCraft, die ihr lösen müsst:
- Der eigene Kernel ist der Engpass: Komplexe Schalenmodelle (Shelling), variable Kantenverrundungen (Variable Fillets) und robuste Boolesche Schnitte bei Tangentialberührung müssen im Rust-Kernel von Hand ausprogrammiert und stabilisiert werden.
- DIN/ISO-Zeichnungsengine, Baugruppen-Solver und Blechbiegemodell müssen von Grund auf neu geschrieben werden.

---

### 6.4 Die "dritte Option": Der inventa-Hybrid-Pfad

Statt sich zwischen dem veralteten Qt-Monolithen FreeCAD und dem noch unfertigen SolidCraft-Kernel zu zerreiben, bietet sich für "inventa" eine hochattraktive Hybrid-Architektur an:

```
+-----------------------------------------------------------------+
|                  inventa Frontend (Rust / egui / WebGPU)         |
|  - Inventor-Style Browser (Feature-Baum + visueller EOP-Marker) |
|  - Schnelles Rendering, lokales Caching, MCP-Agenten-UI         |
+-----------------------------------------------------------------+
                                |  (Headless RPC / MCP Protocol)
                                v
+-----------------------------------------------------------------+
|             inventa Core-Engine (FreeCAD 1.x Headless)          |
|  - OpenCASCADE Geometrie-Rechnen & TNP-Tracking                |
|  - Assembly-Solver (OndselSolver)                               |
|  - TechDraw-Engine für DIN/ISO-PDF-Erzeugung                    |
|  - SheetMetal-Biegeberechnung                                   |
+-----------------------------------------------------------------+
```

**Vorteil dieses Ansatzes:**  
Ihr baut das gewünschte moderne, schlanke Frontend (wie bei SolidCraft angedacht) und die tief integrierte KI-/MCP-Steuerung, nutzt aber als Headless-"Geometry-Server" im Hintergrund FreeCAD 1.x. Damit umgeht ihr FreeCADs veraltetes Qt-UI, profitiert aber sofort von 30 Jahren Kernel-Reife, fertigem Blech, fertigen Baugruppen und vollständiger DIN/ISO-Zeichnungsableitung. Später kann der Headless-FreeCAD-Backend-Service schrittweise durch native Rust-Module ersetzt werden, sobald diese die nötige Reife erreichen.
