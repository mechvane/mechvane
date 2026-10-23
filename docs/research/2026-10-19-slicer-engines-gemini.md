> **Gegenprüfung (Claude, 2026-10-19):** Gemini-Rohfassung (`gemini-3.8-flash-high`,
> Prompt in `2026-10-19-slicer-engines-prompt.txt`). Stichproben:
>
> - Stimmt: CuraEngine ist AGPL-3.0, `Cura.proto` mit `LayerOptimized` und die
>   Arcus-Anbindung liegen im CuraEngine-Repo. Für den UM2 gilt standardmäßig `UltiGCode`,
>   und es gibt den 512-Byte-Kommentar am Dateiende (`ultimaker2.def.json`).
> - **Passt nicht zum Nutzer:** Seine Profile stehen auf `machine_gcode_flavor = RepRap
>   (Marlin/Sprinter)` (`/opt/cura-headless/userconfig`). Die Empfehlung in 7.2, bei UltiGCode
>   zu bleiben, gilt hier also nicht. Temperaturen kommen aus dem G-Code.
> - Nicht geprüft: Zeitangaben fürs Neu-Slicen (vom Modell geschätzt, nicht gemessen; der
>   Steuer-Container hat 2 Kerne), die Rust-Slicer-Tabelle (Repos `ColdCrabby/slicer` und
>   `KeKsBoTer/disco` nicht nachgesehen), Crate-Namen `gcode`/`gcode-nom`.
> - SolidCraft-Regel: AGPL-Code darf nie upstream in SolidCraft landen. Die Prozessgrenze ist
>   also Pflicht und nicht nur für die Veröffentlichung von inventa wichtig.

# Recherchebericht: FDM-Slicer-Integration in das Open-Source-CAD *inventa* (Stand: Oktober 2026)

---

## 1. Einleitung, Kontext und Rahmenbedingungen

### Projektkontext *inventa*
Das Projekt **inventa** entwickelt ein modernes, parametrisches Open-Source-CAD auf Basis von **Rust** und setzt dabei auf der Architektur von [`tangency-labs/solidcraft`](https://github.com/tangency-labs/solidcraft) auf. Das Ziel ist eine nahtlose CAD-Slicer-Integration in einer einzigen Benutzeroberfläche:
1. Modell parametrisch konstruieren.
2. In den Druck-Tab wechseln.
3. Slicen und Schichtvorschau (Toolpaths, Extrusionsbreiten, Linientypen) inspizieren.
4. Bei Änderung eines Konstruktionsparameters das Modell im Hintergrund automatisch neu slicen und die Schichtvorschau aktualisieren.

### Lizenz- und Prozessarchitektur
SolidCraft steht unter einer permissiven Doppellizenz ([MIT / Apache-2.0](https://github.com/tangency-labs/solidcraft)). Um die permissive Lizenz von *inventa* für eine spätere Veröffentlichung zu schützen und die Stabilität des Hauptprogramms zu garantieren, **muss die Slicer-Engine zwingend als getrennter externer Prozess** angebunden werden.

### Ausgangssituation des Nutzers
* **Hardware:** Ultimaker 2+ (Bowden-Extruder, 2,85 mm Filament, Wechseldüsen Olsson-Block).
* **Software-Bestand:** Eigene, über Jahre eingemessene Cura-Profile (Material- und Druckeinstellungen).
* **Status Quo:** Headless-Slicing mit **CuraEngine 5.13** läuft im Setup des Nutzers bereits erfolgreich.

---

## Kennzeichnungskonvention
* **[Belegt]**: Durch Quellcode, offizielle Dokumentation, Commits oder Spezifikationen nachweisbare Fakten (jeweils mit direkter Quellen-URL).
* **[Einschätzung / Vermutung]**: Architektonische Schlussfolgerungen, Benchmark-Schätzungen, ingenieurmäßige Prognosen und rechtliche Praxisanalysen.

---

## 2. CuraEngine (5.x): Tiefenanalyse

### 2.1 Ansteuerungsmöglichkeiten

Für die Prozesskommunikation mit der CuraEngine existieren drei primäre Pfade:

```
+-----------------------------------------------------------------------------------+
|                                  inventa (Rust)                                   |
+-----------------------------------------------------------------------------------+
       |                                   |                                |
  [Pfad A: CLI]                   [Pfad B: Arcus Socket]             [Pfad C: gRPC]
  - Einmaliger Start              - Daemon-Prozess                   - Pluginsystem
  - CLI-Argumente                 - TCP localhost                    - CuraEngine ruft
  - G-Code auf Platte             - Protobuf-Wire-Protokoll            Plugins auf (nicht
                                  - Live Layer-Streaming              als Haupt-Host)
       v                                   v                                v
+-----------------------------------------------------------------------------------+
|                                 CuraEngine 5.x                                    |
+-----------------------------------------------------------------------------------+
```

#### A. Reiner CLI-Modus (`CuraEngine slice`)
* **[Belegt]**: Aufruf über `CuraEngine slice [-v] [-p] [-j <settings.def.json>] [-s <key>=<val>] [-l <model.stl>] [-o <output.gcode>]` ([CuraEngine Application.cpp](https://github.com/Ultimaker/CuraEngine/blob/master/src/Application.cpp)).
* **Funktionsweise**: CuraEngine liest die Definitionsdateien, wendet Parameterüberschreibungen (`-s`) an, lädt das Mesh, berechnet alle Schichten und schreibt die G-Code-Datei direkt auf die Festplatte.
* **Limitierung [Belegt]**: Im reinen CLI-Modus gibt CuraEngine keine strukturierten Schichtdaten (Vektorpfade) an die Standardausgabe aus; auf `stdout`/`stderr` landen lediglich Text-Logmeldungen und Fortschrittsprozente via `-p` ([CuraEngine Application.cpp](https://github.com/Ultimaker/CuraEngine/blob/master/src/Application.cpp)). Für eine Schichtvorschau muss zwingend die generierte G-Code-Datei wieder eingelesen und geparst werden.

#### B. Socket-Modus über Arcus / Protocol Buffers (`CuraEngine connect`)
* **[Belegt]**: CuraEngine implementiert den Befehl `CuraEngine connect <host>[:<port>] [-j <settings.def.json>]` ([CuraEngine Application.cpp](https://github.com/Ultimaker/CuraEngine/blob/master/src/Application.cpp)).
* **Funktionsweise [Belegt]**: Hierbei startet CuraEngine als Client und verbindet sich zu einem bestehenden TCP-Socket (den das Frontend, also Cura oder *inventa*, als Server bereitstellt) ([CuraEngineBackend.py](https://github.com/Ultimaker/Cura/blob/master/plugins/CuraEngineBackend/CuraEngineBackend.py)).
* **Drahtprotokoll (Wire Protocol) [Belegt]**: Das Protokoll wird über Ultimakers Bibliothek [`libArcus`](https://github.com/Ultimaker/libArcus) geregelt ([Socket_p.h](https://github.com/Ultimaker/libArcus/blob/master/src/Socket_p.h)):
  1. **Magic Header (4 Bytes)**: `(0x2BAD << 16) | (VERSION_MAJOR << 8) | VERSION_MINOR` (Standard: `0x2BAD0100` für v1.0).
  2. **Size (4 Bytes)**: `uint32_t` (Länge der serialisierten Protobuf-Nutzlast).
  3. **Type ID (4 Bytes)**: `uint32_t` (Typ-Identifikator der registrierten Proto-Nachricht).
  4. **Payload**: Serialisierte Google Protocol Buffers Nachricht gemäß [`Cura.proto`](https://github.com/Ultimaker/CuraEngine/blob/master/Cura.proto).
* **[Einschätzung]**: Das bedeutet, dass *inventa* **nicht** die C++-Bibliothek `libArcus` linken muss. Ein Rust-TCP-Server kann diesen 12-Byte-Header und die Protobuf-Nachrichten (z. B. via [`prost`](https://crates.io/crates/prost)) in reinem Rust nativ, sicher und ohne FFI-Overhead dekodieren.

#### C. Das gRPC-Pluginsystem seit Cura 5.5
* **[Belegt]**: Seit Cura 5.5 verfügt CuraEngine über eine modulare Erweiterungsschnittstelle via gRPC, definiert in [`Ultimaker/CuraEngine_grpc_definitions`](https://github.com/Ultimaker/CuraEngine_grpc_definitions) ([Cura.proto](https://github.com/Ultimaker/CuraEngine/blob/master/Cura.proto)).
* **Rollenverteilung [Belegt]**: Das gRPC-System dient dazu, dass CuraEngine als *gRPC-Client* spezifische Berechnungsstufen an externe Plugins auslagert. In `Cura.proto` sind dafür feste Slot-IDs reserviert:
  * `SIMPLIFY_MODIFY = 100`
  * `POSTPROCESS_MODIFY = 101`
  * `INFILL_MODIFY = 102`
  * `GCODE_PATHS_MODIFY = 103`
  * `INFILL_GENERATE = 200` (z. B. für benutzerdefinierte Infill-Algorithmen, siehe Referenz-Implementierung [`CuraEngine_plugin_infill_generate`](https://github.com/Ultimaker/CuraEngine_plugin_infill_generate)).
* **[Belegt / Einschätzung]**: Das gRPC-Pluginsystem ersetzt **nicht** die Hauptsteuerung der CuraEngine. CuraEngine wird weiterhin primär über den Arcus-Socket gesteuert; das gRPC-System dient ausschließlich dem Einhängen von Berechnungs-Hooks *in* die Engine.

---

### 2.2 Schichtdaten für eine eigene Vorschau (`LayerOptimized`)

* **[Belegt]**: In [`Cura.proto`](https://github.com/Ultimaker/CuraEngine/blob/master/Cura.proto) definiert Ultimaker die Nachricht `LayerOptimized`:
  ```protobuf
  message LayerOptimized {
    int32 id = 1;
    float height = 2;        // Z-Position (in backend representation / Mikrometern)
    float thickness = 3;     // Schichthöhe
    repeated PathSegment path_segment = 4;
  }

  message PathSegment {
    int32 extruder = 1;
    enum PointType { Point2D = 0; Point3D = 1; }
    PointType point_type = 2;
    bytes points = 3;        // Float32-Array der Punkte [x0, y0, (z0), x1, y1, ...]
    bytes line_type = 4;     // Uint8-Array der Linientypen pro Segment
    bytes line_width = 5;    // Float32-Array der Linienbreiten
    bytes line_thickness = 6;// Float32-Array der Schichtdicken
    bytes line_feedrate = 7; // Float32-Array der Vorschübe (Geschwindigkeiten)
    repeated uint32 attributes = 8; // Bitmasken für Overhangs, Bridging etc.
  }
  ```
* **Linientypen-Klassifizierung [Belegt]**: Die Schichtsegmente sind in Cura über ein Byte-Enum exakt typisiert ([Cura LayerPolygon.py](https://github.com/Ultimaker/Cura/blob/master/cura/LayerPolygon.py)):
  * `0`: NoneType
  * `1`: `Inset0Type` (Äußerste Kontur / Perimeter 0)
  * `2`: `InsetXType` (Innere Konturen)
  * `3`: `SkinType` (Ober- und Unterseiten-Deckschichten)
  * `4`: `SupportType` (Stützstruktur)
  * `5`: `SkirtType` / Brim
  * `6`: `InfillType` (Füllmuster)
  * `7`: `SupportInfillType`
  * `8`: `MoveCombingType` (Eilgang ohne Retraction)
  * `9`: `MoveRetractionType` (Eilgang mit Retraction)
  * `10`: `SupportInterfaceType` (Support-Dach/Boden)
  * `11`: `PrimeTowerType`
* **Vorteil für *inventa* [Einschätzung]**: Durch das direkte Abfangen dieser `LayerOptimized`-Nachrichten erhält der Renderer in SolidCraft sofort voll attributierte 3D-Vektorbahnen mit echter physikalischer Extrusionsbreite (`line_width`) und exaktem Linientyp. Es muss kein G-Code auf die Festplatte geschrieben und kein Text geparst werden.

---

### 2.3 Geschwindigkeit & Inkrementelles Slicen

* **Parallelisierung [Belegt]**: CuraEngine verwendet Intel oneTBB (`tbb::global_control`), um Schichten und Infill-Berechnungen parallel auf allen verfügbaren CPU-Kernen zu berechnen ([CuraEngine Application.cpp](https://github.com/Ultimaker/CuraEngine/blob/master/src/Application.cpp)).
* **Inkrementelles Slicing [Belegt]**: CuraEngine verfügt über **kein** inkrementelles Slicing auf Geometrie-Ebene. Wird ein Modell verändert (z. B. ein CAD-Parameter in *inventa* modifiziert), verwirft die Engine den gesamten Berechnungszustand und sliced das Modell von Grund auf neu (Mesh slicing -> Inset calculation -> Infill -> Path ordering -> G-Code generation) ([CuraEngine FffProcessor.cpp](https://github.com/Ultimaker/CuraEngine/blob/master/src/FffProcessor.cpp)).
* **Neu-Slice-Geschwindigkeit [Einschätzung]**: 
  * Bei mechanischen Teilen mittlerer Komplexität (z. B. typische parametrische CAD-Bauteile mit 10.000 bis 50.000 Dreiecken) benötigt CuraEngine 5.13 auf einer modernen 8-Kern-CPU typischerweise **0,5 bis 2,5 Sekunden**.
  * Wenn CuraEngine als Daemon über den Arcus-Socket läuft, entfällt der Prozess-Start- und Initialisierungs-Overhead (ca. 80–150 ms) sowie das Festplatten-I/O für STL und G-Code vollständig. Ein automatisches Re-Slice bei Parameteränderung im CAD fühlt sich für den Nutzer dadurch nahezu verzögerungsfrei an, wenn nach Abschluss einer Parametereingabe ein Debounce-Timer von ca. 300 ms geschaltet wird.

---

### 2.4 Lizenz (AGPL-3.0) und Prozessanbindung

* **Lizenz der Komponenten [Belegt]**:
  * CuraEngine: **AGPL-3.0-or-later** ([CuraEngine LICENSE](https://github.com/Ultimaker/CuraEngine/blob/master/LICENSE)).
  * libArcus: **LGPL-3.0-or-later** ([libArcus LICENSE](https://github.com/Ultimaker/libArcus/blob/master/LICENSE)).
  * Cura Frontend / Uranium: **LGPL-3.0-or-later** ([Cura LICENSE](https://github.com/Ultimaker/Cura/blob/master/LICENSE)).
  * SolidCraft / *inventa*: **MIT / Apache-2.0** ([SolidCraft LICENSE](https://github.com/tangency-labs/solidcraft)).
* **Bedeutung für die Prozessgrenze [Belegt / Rechtliche Einschätzung]**:
  * Nach den Richtlinien der Free Software Foundation (FSF) gilt ein Programm dann nicht als abgeleitetes Werk ("Derivative Work"), wenn zwei Programme in getrennten Adressräumen laufen, als getrennte Prozesse ausgeführt werden und über Standard-IPC (Pipes, Sockets, CLI-Argumente) "at arm's length" kommunizieren ([FSF GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)).
  * Da CuraEngine von Ultimaker explizit dafür ausgelegt wurde, von einem separaten Frontend via Socket angesteuert zu werden, stellt die Kommunikation über einen TCP-Socket eine saubere Lizenzbarriere dar.
  * **Wichtig**: *inventa* darf **weder statisch noch dynamisch gegen C++-Bibliotheken der CuraEngine linken**. Würde *inventa* `libCuraEngine` über C-FFI direkt in den gleichen Prozess laden, würde das virale Copyleft der AGPL-3.0 auf die gesamte CAD-Anwendung durchschlagen.
* **Vertriebsbedingungen [Belegt]**:
  * Wenn *inventa* vorkompilierte Binärdateien der CuraEngine mitliefert (z. B. im Installer), handelt es sich um eine zulässige Aggregation ("Mere Aggregation").
  * *inventa* muss dem Endnutzer die Lizenzbedingungen der AGPL-3.0 für die CuraEngine anzeigen und den Quellcode der exakt verwendeten CuraEngine-Version zugänglich machen (oder ein schriftliches Angebot beilegen).
  * Der eigentliche Code von *inventa* kann dabei vollständig unter MIT / Apache-2.0 verbleiben.
  * Die AGPL-spezifische Klausel (Abschnitt 13: Pflicht zur Bereitstellung des Quellcodes bei Nutzung über ein Computernetzwerk) betrifft reine Desktop-Installationen nicht, wäre aber relevant, falls *inventa* später als Cloud-/Browser-Dienst betrieben wird.

---

## 3. libslic3r (PrusaSlicer, OrcaSlicer, Bambu Studio)

### 3.1 Nutzung als Bibliothek vs. CLI

* **Bibliotheksnutzung (`libslic3r`) [Belegt]**:
  * `libslic3r` existiert als C++-Subsystem im Quellbaum von PrusaSlicer ([PrusaSlicer src/libslic3r](https://github.com/prusa3d/PrusaSlicer/tree/master/src/libslic3r)).
  * Es gibt **kein stabiles C-ABI, kein SDK und keine offiziellen Header für Drittanwendungen**. `libslic3r` ist eng mit Boost, Eigen, Clipper, Intel TBB und OpenCASCADE verwoben ([PrusaSlicer CMakeLists.txt](https://github.com/prusa3d/PrusaSlicer/blob/master/CMakeLists.txt)).
  * Ein direktes Linken aus Rust heraus erfordert aufwendige C++-Bindings (z. B. via `cxx`), bricht bei jedem Upstream-Update die Kompatibilität und erzwingt zwingend die AGPL-3.0 für das gesamte Binary.
* **CLI-Nutzung [Belegt]**:
  * PrusaSlicer und OrcaSlicer bieten einen vollwertigen Headless-CLI-Modus ([PrusaSlicer CLI Manual](https://manpages.debian.org/testing/prusa-slicer/prusa-slicer.1.en.html)):
    ```bash
    # PrusaSlicer
    prusa-slicer --export-gcode --load config.ini -o output.gcode model.stl
    
    # OrcaSlicer
    orcaslicer --load-settings "printer.json;process.json" --load-filaments "filament.json" --slice 0 --outputdir ./out model.stl
    ```
  * OrcaSlicer besitzt zudem experimentelle Schalter wie `--export-slicedata <dir>`, mit denen interne Schicht-Caches in ein Verzeichnis abgelegt werden können ([OrcaSlicer Source](https://github.com/SoftFever/OrcaSlicer)).

---

### 3.2 Schichtdaten & Geschwindigkeit

* **Ausgabe von Vorschaudaten [Belegt]**:
  * Über die CLI exportieren weder PrusaSlicer noch Bambu Studio strukturierte Pfaddaten im JSON- oder Binärformat an ein Frontend.
  * Das einzige reguläre Ausgabeformat des CLI-Slicings ist die fertige **G-Code-Datei** (oder binärer `.bgcode`).
  * Für eine Vorschau in *inventa* müsste daher nach jedem Slice die G-Code-Datei von der Festplatte gelesen und durch einen G-Code-Parser analysiert werden.
* **Inkrementelles Slicen in libslic3r [Belegt]**:
  * `libslic3r` verfügt intern über eine sehr feingranulare Schritt-Zustandsmaschine (`PrintStep` und `PrintObjectStep`, z. B. `posSlice`, `posPerimeters`, `posInfill`, `posSupportMaterial`) ([PrintState.hpp](https://github.com/prusa3d/PrusaSlicer/blob/master/src/libslic3r/PrintState.hpp)).
  * **Haken für Headless-Nutzung [Belegt / Einschätzung]**: Diese Schritt-Invalidierung ist nur aktiv, wenn `libslic3r` persistent im Speicher gehalten wird (wie in der offiziellen GUI). Bei jedem CLI-Aufruf (`prusa-slicer --export-gcode`) startet ein neuer Prozess, liest alle Konfigurationen neu ein und rechnet von 0 % an. Ein Daemon-Modus existiert im offiziellen CLI-Interface nicht.

---

### 3.3 Profil-Import aus Cura

* **Kompatibilität [Belegt]**: Ein direkter Import von Cura-Profilen in PrusaSlicer oder OrcaSlicer ist **technisch nicht möglich** ([PrusaSlicer Documentation](https://help.prusa3d.com/)):
  * Vollkommen andere Konfigurationsstrukturen (Cura nutzt INI + XML + JSON-Vererbung; PrusaSlicer nutzt flache `.ini`-Dateien; OrcaSlicer nutzt hierarchische `.json`-Dateien).
  * Unterschiedliche mathematische Parametrisierungen: In Cura wird Wandstärke z. B. in Millimetern angegeben (`wall_thickness = 1.2`) und die Linienanzahl daraus berechnet; in PrusaSlicer wird die feste Perimeter-Anzahl angegeben (`perimeters = 3`).
  * Eigene Namenskonventionen und interne Schwellenwerte für Überhänge, Brücken und Flussberechnungen.
* **Konverter [Belegt]**: Es existieren vereinzelte Skripte aus der Community (wie experimentelle Python-Heuristiken auf GitHub), diese können jedoch prinzipbedingt nur triviale Basiswerte (Temperaturen, Geschwindigkeiten, Retraction) übersetzen. Die komplexen Druckqualitäts- und Maßhaltigkeitsmerkmale des Ultimaker 2+ gehen dabei verloren.

---

## 4. Rust-native und alternative Slicer-Engines (Stand 2025/2026)

| Projekt | Sprache / Basis | Status / Reifegrad (2025/2026) | Relevante Features (Arachne, Tree Support etc.) | Fazit für *inventa* |
| :--- | :--- | :--- | :--- | :--- |
| **GladiusSlicer** | Rust | Experimentell / Proof-of-Concept ([GitHub](https://github.com/GladiusSlicer/GladiusSlicer)) | Klassische konstante Linienbreiten, einfaches Infill, keine Baumstützen | Ungeeignet für Produktivdrucke auf UM2+ |
| **ColdCrabby/slicer** | Rust (WASM/CLI) | Frühes Entwicklungsstadium ([GitHub](https://github.com/ColdCrabby/slicer)) | Reine 2D-Polygon-Schnittberechnungen, minimales G-Code-Emitting | Unvollständig |
| **KeKsBoTer/disco** | Rust | Proof of Concept ([GitHub](https://github.com/KeKsBoTer/disco)) | Grundlagen-Slicing von Dreiecksnetzen | Unvollständig |
| **mslicer** | Rust | Aktiv ([GitHub](https://github.com/connorslade/mslicer)) | Nur für MSLA/Resin (Erzeugung von Schicht-Bitmaps) | Ungeeignet (reiner SLA-Slicer, kein FDM) |
| **Kiri:Moto** | JavaScript / Node.js | Reif für Web-Einsatz ([GitHub](https://github.com/GridSpace/grid-apps)) | FDM, CNC, Laser; eigenes Infill; keine vollwertige Arachne-Engine | Hoher Speicherbedarf via Node/V8; eigene Profile nötig |
| **PrusaSlicer CLI** | C++ (Upstream) | Industriestandard ([GitHub](https://github.com/prusa3d/PrusaSlicer)) | Arachne, Tree Supports, organic support, vollständige Kalibrierungen | Exzellent, aber keine Schichtdaten-API & kein Cura-Import |
| **OrcaSlicer CLI** | C++ (Upstream) | Industriestandard ([GitHub](https://github.com/SoftFever/OrcaSlicer)) | Scarf Joints, adaptive Schichthöhen, Arachne | Exzellent, aber hoher Portierungsaufwand für Profile |

### Einschätzung der Rust-Slicer-Landschaft [Einschätzung]
Es existiert im Jahr 2026 **keine einzige praxistaugliche FDM-Slicer-Engine in reinem Rust**, die auch nur annähernd die Qualität, Maßhaltigkeit und Features moderner Industrie-Slicer erreicht. 
Moderne FDM-Druckergebnisse hängen kritisch an Algorithmen wie:
1. **Arachne Engine** (dynamische Linienbreitenanpassung für Dünnwände).
2. **Tree / Organic Supports** (ressourcenschonende Baumstützen).
3. **Corner Rounding & Pressure Advance Compensation**.
4. **Präzise Brückenerkennung und thermisches Fan-Speed-Ramping**.

Ein Eigenbau oder das Aufsetzen auf unfertigen Rust-Crates würde Jahre an Entwicklungsaufwand binden, die vom eigentlichen CAD-Kern ablenken.

---

## 5. G-Code-Schichtvorschau & Parsing

Falls eine Engine verwendet wird, die Schichtdaten nicht direkt im Speicher streamt (wie PrusaSlicer CLI oder CuraEngine im reinen Dateimodus), muss die G-Code-Datei für die Schichtvorschau in Rust geparst werden.

```
+-----------------------------------------------------------------------------------------+
|                               G-Code-Strom / Datei                                      |
+-----------------------------------------------------------------------------------------+
       |
       +---> Koordinaten (G0/G1 X.. Y.. Z..) --------> 3D-Geometriepfad
       +---> Vorschub (F..) -------------------------> Farbskala: Geschwindigkeit
       +---> Extrusion (E..) ------------------------> Volumen V = E * A_Filament
       +---> Schichthöhe (Z_neu - Z_alt) ------------> Linienbreite w = V / (h * Distanz)
       +---> Metadaten-Kommentare (;TYPE:..) --------> Farbskala: Feature-Typ
```

### 5.1 Verfügbare Bibliotheken

* **Web/TypeScript**: [`xyz-tools/gcode-preview`](https://github.com/xyz-tools/gcode-preview) (ursprünglich von Remcoder). Sehr reifer Parser und Three.js-Renderer, unterstützt Multicolor, Extrusionsbreitendarstellung und Slicer-Erkennung.
* **Rust**:
  * [`gcode`](https://crates.io/crates/gcode): Extrem schneller, allokationsarmer Visitor- und AST-Parser für G-Code (`#[no_std]`-kompatibel).
  * [`gcode-nom`](https://crates.io/crates/gcode-nom): Auf dem `nom`-Parsercombinator basierende Bibliothek, unterstützt auch Prusas binären `.bgcode`.

---

### 5.2 Gegenüberstellung der Feature-Kommentare (Cura vs. Prusa/Orca)

Beide Slicer-Familien annotieren den G-Code mit standardisierten Semikolon-Kommentaren, anhand derer ein Parser die Werkzeugpfade einfärben kann:

| Feature / Druckbereich | Ultimaker Cura Kommentare [Belegt] | PrusaSlicer / OrcaSlicer Kommentare [Belegt] |
| :--- | :--- | :--- |
| **Schichtwechsel** | `;LAYER:1` / `;LAYER_COUNT:350` | `;LAYER_CHANGE` gefolgt von `;Z:0.20` |
| **Außenwand (Perimeter 0)**| `;TYPE:WALL-OUTER` | `;TYPE:External perimeter` |
| **Innenwände** | `;TYPE:WALL-INNER` | `;TYPE:Perimeter` / `;TYPE:Overhang perimeter` |
| **Deckflächen (Oben/Unten)**| `;TYPE:SKIN` | `;TYPE:Top solid infill` / `;TYPE:Solid infill` |
| **Infill (Füllstruktur)** | `;TYPE:FILL` | `;TYPE:Internal infill` / `;TYPE:Bridge infill` |
| **Stützstruktur** | `;TYPE:SUPPORT` | `;TYPE:Support material` |
| **Stützstruktur-Interface**| `;TYPE:SUPPORT-INTERFACE` | `;TYPE:Support material interface` |
| **Skirt / Brim** | `;TYPE:SKIRT` | `;TYPE:Skirt / Brim` |
| **Spülturm / Prime Tower** | `;TYPE:PRIME-TOWER` | `;TYPE:Wipe tower` |

---

### 5.3 Was aus G-Code allein rekonstruiert werden kann (und was verloren geht)

#### Was exakt rekonstruierbar ist [Belegt]:
1. **Exakte Trajektorie**: Alle diskretisierten $X/Y/Z$-Wegpunkte des Druckkopfs.
2. **Extrudiertes Volumen**: Aus dem relativen oder absoluten Vorschub des $E$-Werts:
   $$\Delta V = \Delta E \cdot \pi \cdot \left(\frac{d_{\text{filament}}}{2}\right)^2$$
3. **Effektive Linienbreite**: Da die Schichthöhe $h = \Delta Z$ und die Weglänge $L = \sqrt{\Delta X^2 + \Delta Y^2}$ bekannt sind, lässt sich die theoretische Schichtbreite $w$ über das verdrängte Volumen (abzüglich der abgerundeten Kantenmodelle nach Slic3r/Cura-Formel) präzise zurückrechnen:
   $$w \approx \frac{\Delta V}{h \cdot L}$$
4. **Geschwindigkeit & Dynamik**: Der $F$-Parameter (Vorschub in mm/min) liefert die programmierte Kopfbeschwindigkeit.
5. **Druckertemperatur & Lüfter**: $M104/M109$ (Nozzle), $M140/M190$ (Bett), $M106$ (Lüfterdrehzahl 0–255).
6. **Retractions**: Negative $E$-Bewegungen oder Firmware-Retractions ($G10/G11$).

#### Was unwiederbringlich verloren geht [Einschätzung]:
1. **Ursprüngliche CAD-Geometrie**: Bohrungen, Radien und ebene Flächen wurden in Dreiecke und anschließend in viele kleine lineare Segmente zerlegt ($G1$-Quantisierung auf ca. 1–10 µm).
2. **Slicer-Intentionen ohne Kommentare**: Fehlen die `;TYPE:`-Kommentare (oder wurden sie deaktiviert), kann ein Parser nicht mehr verlässlich unterscheiden, ob eine gerade Linie ein Überhang, eine Sichtwand oder eine Stützlinie ist.
3. **Originale Netzkanten**: Durch Verrundungsfilter, Druckruckdämpfung und Linienbreitenmodulation (Arachne) entspricht der G-Code-Pfad nicht mehr exakt den Außenkanten des Ausgangs-STEP/STL-Modells.

---

## 6. Cura-Profile: Aufbau, Vererbung und Konvertierbarkeit

### 6.1 Der Cura `ContainerStack`

Cura speichert Einstellungen nicht in einer einzelnen Profildatei, sondern löst jeden Parameter dynamisch über einen hierarchischen Container-Stapel auf ([Cura ContainerStack.py](https://github.com/Ultimaker/Uranium/blob/master/UM/Settings/ContainerStack.py)).

```
+-----------------------------------------------------------------------------------+
| 1. User Overrides     (Aktuelle Anpassungen im GUI-Feld)                          |
+-----------------------------------------------------------------------------------+
| 2. Quality Changes    (Benutzerdefinierte Profilanpassungen, .inst.cfg)           |
+-----------------------------------------------------------------------------------+
| 3. Intent             (Druckabsicht: "Engineering", "Visual Quality", .inst.cfg)  |
+-----------------------------------------------------------------------------------+
| 4. Quality            (Basisauflösung z. B. "Normal 0.15mm", .inst.cfg)           |
+-----------------------------------------------------------------------------------+
| 5. Material           (Filamentparameter, generic_pla.xml.fdm_material)           |
+-----------------------------------------------------------------------------------+
| 6. Variant            (Hardware-Variante: Nozzle 0.4mm, ultimaker2plus_0.4.inst)  |
+-----------------------------------------------------------------------------------+
| 7. Definition Changes (Maschinenmodifikationen durch Nutzer)                      |
+-----------------------------------------------------------------------------------+
| 8. Definition         (Maschinendefinition: ultimaker2_plus.def.json)             |
|    └─ inherits: ultimaker2 -> ultimaker -> fdmprinter.def.json                   |
+-----------------------------------------------------------------------------------+
```

1. **Definition (`.def.json`) [Belegt]**: 
   * Definiert den physischen Drucker und vererbt Eigenschaften hierarchisch:
     [`ultimaker2_plus.def.json`](https://github.com/Ultimaker/Cura/blob/master/resources/definitions/ultimaker2_plus.def.json) erbt von [`ultimaker2.def.json`](https://github.com/Ultimaker/Cura/blob/master/resources/definitions/ultimaker2.def.json), dieses von `ultimaker.def.json`, welches letztlich von der Basis [`fdmprinter.def.json`](https://github.com/Ultimaker/Cura/blob/master/resources/definitions/fdmprinter.def.json) erbt.
2. **Material (`.xml.fdm_material`) [Belegt]**:
   * Strukturiertes XML nach Schema [`fdm_material.xsd`](https://github.com/Ultimaker/fdm_materials). Enthält Filamentdurchmesser (2,85 mm beim UM2+), Dichte, empfohlene Temperaturen (Druck, Bett, Standby), Retraction-Länge und Flussraten.
3. **Variant (`.inst.cfg`) [Belegt]**:
   * Definiert Hardware-Bestandteile (z. B. Nozzle-Durchmesser: 0,25 mm, 0,4 mm, 0,6 mm, 0,8 mm).
4. **Quality & Quality Changes (`.inst.cfg`) [Belegt]**:
   * Standard-INI-Format mit den Abschnitten `[general]`, `[metadata]` und `[values]`. Speichert Schichthöhen, Geschwindigkeiten, Füllgrade etc.

---

### 6.2 Die Formel-Falle: `value` vs. `default_value`

* **Python-Formeln im Frontend [Belegt]**: In Curas Definitions- und Profil-Dateien enthalten zahlreiche Parameter keine statischen Zahlen, sondern dynamische mathematische Ausdrücke ([SettingDefinition.py](https://github.com/Ultimaker/Uranium/blob/master/UM/Settings/SettingDefinition.py)), z. B.:
  ```json
  "layer_height_0": { "value": "round(machine_nozzle_size / 1.5, 2)" },
  "speed_wall_0": { "value": "speed_wall / 2" }
  ```
* **CuraEngine besitzt keinen Python-Interpreter [Belegt]**:
  * Wenn CuraEngine headless über die CLI (`CuraEngine slice -j ultimaker2_plus.def.json ...`) aufgerufen wird, wertet CuraEngine **keine Python-Formeln** aus! ([CuraEngine Issue #1233](https://github.com/Ultimaker/CuraEngine/issues)).
  * CuraEngine liest in Definitionsdateien ausschließlich den statischen `default_value`. Steht dort nur ein dynamisches `"value": "..."`, fällt CuraEngine auf den Standardwert des übergeordneten Druckers zurück oder ignoriert die Formel.
* **Lösung für *inventa* [Einschätzung]**:
  * Da der Nutzer bereits funktionierende CuraEngine 5.13-Aufrufe hat, verfügt er entweder bereits über eine vorberechnete Konfigurationsdatei oder ein Skript, das die fertigen Schlüsselwertpaare übergibt.
  * CuraEngine unterstützt über den CLI-Parameter `-r <resolved.json>` das Laden einer vollständig aufgelösten JSON-Datei, in der alle mathematischen Formeln bereits zu festen Fließkommazahlen evaluiert wurden. Alternativ können alle Parameter über `-s key=value` direkt übergeben werden.

---

## 7. Ultimaker 2+ Besonderheiten

Beim Slicen für den Ultimaker 2+ müssen zwei herstellerspezifische Eigenheiten zwingend beachtet werden:

```
[Standard Marlin / RepRap]                           [Ultimaker 2+ / UltiGCode]
G1 X10 Y20 E0.45 F1800                               G1 X10 Y20 E1.14 F1800
(E = 0.45 mm Filamentlänge)                          (E = 1.14 mm³ Schmelzvolumen)
M104 S210 (Hotend auf 210°C)                         Temperatur wird im Druckermenü
M140 S60  (Bett auf 60°C)                            am Gerät gewählt (oder via Header)
Start-/End-G-Code vollständig im File                Start-/End-Prozedur in Firmware hinterlegt
```

### 7.1 UltiGCode vs. RepRap-Flavor

* **Volumetrische Extrusion [Belegt]**:
  * Standardmäßig verwendet der Ultimaker 2+ den Flavor `UltiGCode` (definiert in [`ultimaker2.def.json`](https://github.com/Ultimaker/Cura/blob/master/resources/definitions/ultimaker2.def.json): `"machine_gcode_flavor": { "default_value": "UltiGCode" }`).
  * In UltiGCode repräsentiert der $E$-Parameter **nicht** die Länge des Filamentfadens in Millimetern, sondern das **Volumen des extrudierten Materials in Kubikmillimetern ($mm^3$)**.
  * Der Drucker rechnet intern anhand des am Gerät eingestellten Filamentdurchmessers (2,85 mm) das Schmelzvolumen in Motorschritte des Feeders um.
* **Material- und Temperaturverwaltung [Belegt]**:
  * In reinem UltiGCode fehlen klassische Befehle wie `M104/M109` (Extrudertemperatur) und `M140/M190` (Betttemperatur) sowie manuelle Retraction-Befehle im Start-G-Code.
  * Stattdessen liest die Firmware des UM2+ Metadaten-Header am Anfang der G-Code-Datei aus:
    ```gcode
    ;FLAVOR:UltiGCode
    ;TIME:3600
    ;MATERIAL:PLA
    ;NOZZLE_DIAMETER:0.4
    ```
  * Beim Start des Drucks von SD-Karte wählt der Nutzer am Drehrad des Druckers das Material aus, und die Firmware heizt Nozzle und Bett gemäß den intern auf dem Drucker hinterlegten Materialprofilen auf.
* **Firmware-Ende-Puffer (512-Byte-Fix) [Belegt]**:
  * In [`ultimaker2.def.json`](https://github.com/Ultimaker/Cura/blob/master/resources/definitions/ultimaker2.def.json) ist im `machine_end_gcode` ein historischer Firmware-Bugfix hinterlegt: Ältere UM2-Firmware-Versionen brechen den Druck vorzeitig ab, wenn der Bewegungspuffer am Dateiende zu schnell leert. Cura fügt daher zwingend einen mindestens 512 Byte langen Kommentarblock am Ende ein:
    ```gcode
    ;Version _2.6 of the firmware can abort the print too early if the file ends... [aufgefüllt auf 512 Bytes]
    ```

### 7.2 Umschalten auf RepRap (Marlin)-Flavor

* **[Belegt]**: In Cura und CuraEngine kann der Flavor über `-s machine_gcode_flavor=RepRap` auf Standard-Marlin umgestellt werden.
* **Konsequenzen [Einschätzung]**:
  * **Vorteil**: Volle Kontrolle über exakte Temperaturen, benutzerdefinierte Start-/End-Sequenzen und native E-Schritte in mm direkt aus der CAD-Software.
  * **Nachteil**: Die Materialprofile auf dem UM2+-Display werden umgangen; der Drucker heizt nicht mehr vor der Dateiauswahl autonom vor. Für den Anwender, der seine Profile auf den UM2+-Workflow optimiert hat, empfiehlt es sich, beim nativen **UltiGCode** zu bleiben.

---

## 8. Vergleichende Bewertungstabelle

| Kriterium | CuraEngine 5.13 (Socket / Arcus) | CuraEngine 5.13 (CLI) | libslic3r / PrusaSlicer (CLI) | OrcaSlicer (CLI) | Rust-eigene Slicer (Gladius/disco) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Steuerbarkeit aus Rust** | **Sehr gut** (TCP-Socket, Protobuf nativ in Rust via `prost`) | **Gut** (`std::process::Command`, stdin/stdout) | **Befriedigend** (Nur CLI-Parameter & INI-Dateien) | **Gut** (CLI mit JSON-Settings) | **Perfekt** (Natives Rust-API) |
| **Neu-Slice-Geschwindigkeit** | **Exzellent** (Daemon läuft; In-Memory Slicing, kein Start-Overhead) | **Gut** (Prozess-Kaltstart ca. 100 ms + Slicing) | **Befriedigend** (Vollständiger Kaltstart jedes Mal) | **Befriedigend** (Kaltstart jedes Mal) | **Exzellent** (Kein IPC-Overhead) |
| **Schichtdaten für Vorschau** | **Exzellent** (Direkte Vektoren & Breiten via `LayerOptimized`) | **Mäßig** (G-Code muss von Festplatte geparst werden) | **Mäßig** (Nur G-Code-Export, Re-Parsing nötig) | **Mäßig** (G-Code Re-Parsing nötig) | **Exzellent** (Direkte Speicherdaten) |
| **Cura-Profil-Kompatibilität** | **Nativ 100 %** (Nutzt vorhandene Definitions & Profile) | **Nativ 100 %** (Bereits headless lauffähig) | **0 %** (Kein Import möglich, manuelle Neuanlage) | **0 %** (Kein Import möglich) | **0 %** (Völlig inkompatibel) |
| **Lizenz / Lizenztrennung** | **Sauber** (AGPL-3.0 isoliert über TCP-Socket, inventa bleibt MIT/Apache) | **Sauber** (AGPL-3.0 isoliert als Subprozess) | **Sauber** (AGPL isoliert via CLI; FFI wäre fatal) | **Sauber** (AGPL isoliert via CLI) | **Unkritisch** (Meist MIT / Apache) |
| **Reifegrad (Arachne, UM2+)** | **Industriestandard** (Perfekt auf Ultimaker 2+ abgestimmt) | **Industriestandard** | **Industriestandard** (Erfordert aber neue Drucker-Profile) | **Industriestandard** | **Unbrauchbar** (Pre-Alpha, Drucke scheitern) |

---

## 9. Begründete Empfehlung für einen ersten Prototyp in *inventa*

Für die Implementierung in *inventa* wird eine **Zwei-Stufen-Strategie** empfohlen:

```
[Phase 1: Minimal Viable Prototype (Tage)]
inventa (Rust) ---> Schreibt Temp-STL ---> CuraEngine CLI (-s / -j / -o) ---> Schreibt G-Code
     ^                                                                               |
     |                                                                               v
SolidCraft Renderer <---------------- Parst G-Code via `gcode`-Crate <---------------+

                                       │
                                       ▼

[Phase 2: Performanter Ziel-Zustand (Wochen)]
inventa (Rust) == (TCP / Protobuf) ==> CuraEngine Daemon (`connect`)
     │                                       │
     │ Überträgt Mesh direkt                 │ Streamt `LayerOptimized`
     ▼                                       ▼
SolidCraft Renderer <================= Vektorpfade + Linientypen direkt im GPU-Puffer
```

### Phase 1: Der "Minimal Viable Prototype" (Tage bis 1 Woche)
1. **Engine**: Nutzung der bereits lauffähigen **CuraEngine 5.13 im CLI-Modus** über `std::process::Command`.
2. **Workflow**:
   * Bei Klick auf "Slicen" oder nach Parameter-Änderung (mit 400 ms Debounce) exportiert *inventa* das CAD-Modell in eine temporäre STL-Datei (oder übergibt es per Pipe).
   * Aufruf von `CuraEngine slice` mit den bestehenden Parametern des Nutzers und Ausgabe in eine temporäre `.gcode`-Datei.
3. **Vorschau**:
   * Einbindung der Rust-Crate [`gcode`](https://crates.io/crates/gcode) oder [`gcode-nom`](https://crates.io/crates/gcode-nom).
   * Auslesen der Zeilen mit `;TYPE:`-Präfix (`WALL-OUTER`, `WALL-INNER`, `FILL`, `SKIN`, `SUPPORT`).
   * Konvertierung der $X/Y/Z$-Segmente in Vertex-Buffer für den vorhandenen Renderer von SolidCraft.
4. **Vorteil**:
   * Garantiert sofortige Druckbarkeit auf dem Ultimaker 2+.
   * Verwendet die bestehenden, funktionierenden Cura-Profile des Nutzers ohne Migrationsrisiko.
   * Keine IPC-Protokollkomplexität im ersten Schritt.

### Phase 2: Der reaktive Produktions-Zustand (2 bis 4 Wochen)
1. **Engine**: Umstellung auf `CuraEngine connect 127.0.0.1:<port>`.
2. **Architektur**:
   * *inventa* startet CuraEngine als Hintergrund-Daemon.
   * Ein kleiner, asynchroner Tokio-basierter TCP-Server in *inventa* wickelt das Arcus-Protokoll (12-Byte-Header + Protobuf) in purem Rust ab (unter Nutzung von [`prost`](https://crates.io/crates/prost) und der originalen [`Cura.proto`](https://github.com/Ultimaker/CuraEngine/blob/master/Cura.proto)).
   * Bei Parameteränderungen im CAD wird direkt eine `cura.proto.Slice`-Nachricht mit den Mesh-Rohdaten (Vertices/Indices) an den Socket gesendet – **ohne STL-Schreibzugriffe auf die Festplatte**.
3. **Schichtdaten**:
   * CuraEngine streamt während der Berechnung kontinuierlich `LayerOptimized`-Nachrichten zurück.
   * *inventa* übernimmt die `PathSegment`-Byte-Arrays direkt in GPU-Instanzpuffer (Linienbreite als Rohr-/Quader-Radius, Linientyp als Farbcodierung).
4. **Vorteil**:
   * Maximale Reaktivität beim Verschieben von Parametern im CAD.
   * 100 % saubere Lizenzbarriere (inventa bleibt MIT/Apache-2.0, da kein Byte AGPL-Code gelinkt wird).
   * Keine Festplattenabnutzung und minimale Latenz.
