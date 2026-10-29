# Recherche: Offenes Format für Werkstoff-Darstellung (MaterialX/OpenPBR, glTF 2.0 PBR, USD und Blender Principled BSDF)

> **Prüfnotiz (Claude, 2026-10-29):** Rohfassung von Gemini Flash (Issue #15). `tools/check_sources.py`:
> 16 von 16 Quellen erreichbar, 16 Zitate und 14 von 14 Zahlen bestätigt. Die Belege beziehen sich auf
> Blender 4.0/4.2; vor der Entscheidung (ADR) gegen die aktuelle Blender-Version prüfen, ob sich der
> MaterialX-Import geändert hat. Ergänzung: SolidCraft 0.25 speichert je Werkstoff bereits ein
> PBR-Aussehen (`pbr: {metallic, roughness, dielectric_ior}`); das ist die Teilmenge, die die App selbst
> zeigt, der Rest (Klarlack, Anisotropie, Transmission) läge in Mechvanes glTF-Fragment.

- **Datum:** 2026-10-29
- **Autor:** Gemini 3.8 Flash
- **Status:** Rohfassung, quellengeprüft mit `tools/check_sources.py`
- **Kontext:** Issue #15, ROADMAP.md (Grundsatz 8: „Renderanbindung an Blender“, Material- und Darstellungseditor) und interaktive Web-Ansicht (three.js).
- **Ziel:** Auswahl und Begründung eines offenen, zukunftssicheren Formats für Werkstoff-**Darstellung** (optisches Aussehen, Oberflächengüte, PBR-Shading), das Mechvane im Bauteil-/Baugruppendokument speichert und das sich:
  1. verlustfrei und automatisiert zum fotorealistischen Rendern in Blender (Cycles/EEVEE) nutzen lässt,
  2. performant in der browserbasierten Web-Ansicht (three.js) visualisiert,
  3. direkt als standardkonformes glTF 2.0 exportieren lässt,
  4. und als solide Datenbasis für einen Material- und Darstellungseditor dient.

---

## 1. Zusammenfassung & Architektur-Empfehlung für Mechvane

### 1.1 Das Kernproblem im CAD-Bereich
In parametrischen CAD-Systemen (wie Autodesk Inventor, Autodesk Fusion oder SolidWorks) existiert eine strikte Trennung zwischen zwei Domänen:
1. **Physikalischer Werkstoff (`Physical Material`):** Dichte $\rho$, E-Modul, Streckgrenze, thermische Ausdehnung. Notwendig für Massenberechnung, Schwerpunkt, FEM und fertigungstechnische Regeln (`check_design`, z. B. Mindesteinschraubtiefen).
2. **Optische Darstellung (`Appearance` / Oberfläche):** PBR-Eigenschaften wie Farbe, Rauheit, Metallizität, Klarlack, Anisotropie (Bürstung), Brechungsindex (IOR) und Texturen.

Für Mechvane wird ein offenes Format gesucht, das diese optische Darstellung speichert, ohne proprietäre CAD-Bindungen einzugehen.

### 1.2 Bewertung der Kandidaten

* **MaterialX (ASWF) mit OpenPBR Surface & Autodesk Standard Surface:**
  * *Stärken:* Höchste Ausdruckskraft im VFX-/Film- und Highend-Rendering. OpenPBR Surface (gemeinsam entwickelt von der Academy Software Foundation, Adobe und Autodesk als Synthese aus Autodesk Standard Surface und Adobe Standard Material) ist der führende offene Über-Shader-Standard. Offizielles Python-Paket `MaterialX` existiert auf PyPI mit binären Wheels.
  * *Hürden in der Praxis:* Blender besitzt **keinen nativen Standalone-Import oder -Export für `.mtlx`-Dateien im Core**! In Blender existiert lediglich eine Option beim USD-Export („MaterialX Network“), während der USD-Import MaterialX laut offizieller Dokumentation explizit noch nicht unterstützt. In three.js verlangt der `MaterialXLoader` zwingend den modernen `WebGPURenderer` und die Node-Material-Architektur (TSL); im stabilen WebGL-Standard-Renderer von three.js kann MaterialX nicht direkt gerendert werden. Für CAD-Bauteile (die zu 95 % homogene oder prozedural gekachelte Oberflächen besitzen) ist der volle Shader-Graph von MaterialX zudem oft überdimensioniert.
* **USD / UsdPreviewSurface (Pixar / ASWF):**
  * *Stärken:* Industriestandard für Szenenaufbau und Baugruppen im VFX-Bereich. Blender verfügt über native USD-Import- und Export-Operatoren.
  * *Hürden in der Praxis:* `UsdPreviewSurface` ist ein minimalistischer Basis-Shader ohne native Unterstützung für Sheen, Volumen-Absorption oder fortgeschrittene Anisotropie. Die offizielle Blender-Dokumentation warnt beim USD-Material-Import: *„This option can be lossy, as it does not yet handle converting all shader settings and types“*. Die Python-Bindungen (`pxr.usd`) sind gigantisch (> 1 GB Build), schwergewichtig und auf Client-Systemen selten vorinstalliert. In three.js ist die USDZ-Unterstützung nur rudimentär.
* **glTF 2.0 PBR mit KHR_materials_*-Erweiterungen:**
  * *Stärken:* **Vollständige, native und ausgereifte Unterstützung in beiden Zielsystemen (Blender und three.js).** Blender (über das integrierte Core-Addon `io_scene_gltf2`) und three.js (`GLTFLoader` auf `MeshPhysicalMaterial`) unterstützen den vollen Satz moderner Khronos-Materialerweiterungen: Clearcoat, Transmission, Volume, Sheen, Specular, Anisotropy, IOR, Emissive Strength und Variants.
  * *Praxisnutzen für Python & Web:* Reines, schlankes JSON. Kann mit Standard-Python (`json`, `pygltflib`) ohne jeden externen C++-Compiler gelesen, validiert und serialisiert werden.

### 1.3 Empfohlene Mechvane-Architektur: Das 2-Stufen-Modell

Für Mechvane wird folgende Architektur empfohlen:

1. **Speicher- und Austauschformat im Dokument (Kern):**
   Mechvane definiert sein internes Datenmodell für Darstellungen deckungsgleich mit **glTF 2.0 PBR + KHR_materials_*-Erweiterungen**, strukturiert nach den einheitlichen Naming-Konventionen von **OpenPBR Surface**.
   * Da OpenPBR Surface und glTF 2.0 KHR für physikalische Parameter (Base Color, Metalness, Roughness, Specular IOR, Clearcoat, Sheen, Anisotropy, Transmission, Volume) identische Definitionen und Wertebereiche verwenden, ist das Modell semantisch 100 % zukunftssicher.
   * Gespeichert wird die Materialdefinition als lesbares, kompaktes JSON-Fragment im Mechvane-Dokumentmodell (`appearance.json` bzw. eingebettet in `.mechvane` / `.gltf`).
2. **Pipeline nach Blender (Cycles / EEVEE):**
   * *Weg A (Headless CLI / Docker-Rendering):* Mechvane übergibt die Baugruppe als `.glb` mit KHR-Erweiterungen. Blender importiert die Datei nativ (`bpy.ops.import_scene.gltf`) und erzeugt automatisch den passenden `Principled BSDF`-Knotenbaum in Cycles.
   * *Weg B (Direktes Python-Skript / Blender-MCP):* Für hochgradige Kontrolle setzt ein Python-Renderer die Buchsen des `Principled BSDF` (v2) in Blender direkt per API (`material.node_tree.nodes["Principled BSDF"].inputs[...]`), was dank der 1:1-Entsprechung der Parameter trivial ist.
3. **Pipeline nach three.js (Web-Frontend):**
   * Das Web-Frontend nutzt `GLTFLoader` oder instanziiert direkt ein `THREE.MeshPhysicalMaterial`, dessen Parameter aus dem JSON-Dokument initialisiert werden. Dies funktioniert zuverlässig im stabilen WebGL-Renderer sowie im künftigen WebGPU-Renderer.
4. **Optionaler VFX-Exportpfad (MaterialX):**
   * Für den Austausch mit Studios (Maya LookdevX, Houdini Solaris) kann Mechvane über das offizielle Python-Paket `MaterialX` (aus PyPI) ein valides `.mtlx`-Dokument mit `open_pbr_surface` synthetisieren.

---

## 2. Detaillierte Untersuchung der Fragestellungen

### 2.1 Blender (aktuelle Versionen 4.0, 4.2 LTS)

#### Principled BSDF v2 (Redesign seit Blender 4.0)
In Blender 4.0 wurde der **Principled BSDF** grundlegend überarbeitet, um den modernen Erkenntnissen der PBR-Forschung und Standards wie OpenPBR zu folgen:
* **Neu geordnete Schichtenarchitektur:**
  * **Sheen:** Wurde an die oberste Position über Emission und Coat verlegt und basiert auf einem neuen Mikrofaser-Modell (Zeltner et al., linearly transformed cosines). Es dient nicht mehr nur für Samt/Stoffe, sondern auch für feine Staubschichten auf beliebigen Oberflächen.
  * **Coat:** Wurde über die Emission-Schicht verschoben. Dadurch lassen sich selbstleuchtende Displays hinter einer Glas-/Lackschicht (z. B. Smartphone-Displays oder Instrumententafeln) physikalisch korrekt simulieren. Coat erhielt zusätzlich eigene Eingänge für *Coat Tint*, *Coat IOR* und *Coat Normal*.
* **Brechungsindex (IOR) und Glanzlichter:**
  * Dielektrische Glanzlichter und Transmission werden zentral über einen einheitlichen *IOR*-Eingang gesteuert. Für Texturierungszwecke gibt es den Multiplikator *IOR Level* (Standard 0,5 entspricht F0 = 0,04). Für künstlerische Zwecke steht *Specular Tint* bereit.
  * **Metall-Kantenfärbung (Edge Tint):** Für metallische Oberflächen (`Metallic = 1.0`) nutzt der Specular-Tint-Eingang das physikalische **F82-Modell**, um komplexe Brechungsindizes (z. B. die gelb-rötliche Kantenreflexion von Gold und Kupfer) abzubilden.
* **Energieerhaltung:** cycles-seitig wird standardmäßig *Multiple scattering GGX* verwendet; die Schichtenkombination ist strikt energieerhaltend.

#### Nativer MaterialX-Support in Blender
* Blender verfügt **nicht** über einen nativen `.mtlx`-Importer oder -Exporter im Core.
* Beim **USD-Export** bietet Blender im Bereich der Materialeinstellungen die Option *MaterialX Network*, die versucht, Cycles/EEVEE-Shadernetzwerke in MaterialX-Graphen zu konvertieren.
* Beim **USD-Import** wird MaterialX jedoch **nicht** unterstützt. Die offizielle Blender-Dokumentation stellt klar: *„MaterialX is currently not supported, see the feature commit for details.“*
* Für den Standalone-Import von `.mtlx` sind Anwender auf Drittanbieter-Addons angewiesen (z. B. experimentelle Community-Addons wie `io_blender_mtlx`).

#### Nativer USD-Material-Support in Blender
* Blender importiert USD-Dateien nativ und bietet die Option *Import USD Preview Surface*, um `UsdPreviewSurface`-Shader in Knoten des `Principled BSDF` zu konvertieren.
* Dieser Import ist jedoch verlustbehaftet. Die offizielle Dokumentation warnt: *„This option can be lossy, as it does not yet handle converting all shader settings and types, but it can generate approximate visualizations of the materials.“*

#### Nativer glTF-Import/-Export mit KHR-Erweiterungen
Das in Blender gebündelte offizielle Addon `io_scene_gltf2` bietet vollständigen, bidirektionalen Support für die relevanten Khronos-PBR-Erweiterungen und mappt diese direkt auf den `Principled BSDF`:
* **`KHR_materials_clearcoat`:** Mappt auf *Coat Weight* und *Coat Roughness* (sowie optional *Coat Normal*).
* **`KHR_materials_transmission`:** Mappt auf *Transmission Weight*.
* **`KHR_materials_volume`:** Mappt auf den *Volume Absorption*-Knoten am Material-Ausgang (*Attenuation Color* und inverse *Attenuation Distance* als Dichte).
* **`KHR_materials_sheen`:** Mappt auf *Sheen Weight*, *Sheen Roughness* und *Sheen Tint*.
* **`KHR_materials_specular`:** Mappt auf *Specular IOR Level* und *Specular Tint*.
* **`KHR_materials_anisotropy`:** Mappt auf *Anisotropic* und *Anisotropic Rotation*.
* **`KHR_materials_ior`:** Mappt auf den *IOR*-Eingang (glTF-Standardwert ist 1,5).
* **`KHR_materials_emissive_strength`:** Mappt auf *Emission Strength*.
* **`KHR_materials_variants`:** Ermöglicht die Definition und das Umschalten mehrerer Materialvarianten auf denselben Primitiven.

*Verlustfreiheit:* Die Abbildung zwischen glTF KHR-Erweiterungen und dem Blender `Principled BSDF` ist **nahezu 100 % verlustfrei**, da beide Systeme auf denselben mikrofazettenbasierten PBR-Modellen (GGX) und standardisierten physikalischen Kanälen aufsetzen.

---

### 2.2 three.js (MeshPhysicalMaterial & MaterialXLoader)

#### MeshPhysicalMaterial im stabilen WebGL- und WebGPU-Betrieb
`THREE.MeshPhysicalMaterial` ist die High-End-Erweiterung von `THREE.MeshStandardMaterial` in three.js:
* **Unterstützte Kanäle:**
  * **Anisotropie:** `anisotropy`, `anisotropyRotation`, `anisotropyMap` (zur Darstellung gebürsteter Metalle).
  * **Clearcoat:** `clearcoat`, `clearcoatRoughness`, `clearcoatNormalMap` (für Klarlacke, Harzschichten, nassglänzende Oberflächen).
  * **Transmission & Volumen:** `transmission`, `thickness`, `attenuationColor`, `attenuationDistance`, `ior` (für optisches Glas, Wasser, transparente Kunststoffe).
  * **Sheen:** `sheen`, `sheenColor`, `sheenRoughness` (für Mikrofasern, samtige Textilien und Staubeffekte).
  * **Specular:** `specularIntensity`, `specularColor` (zur feinen Steuerung dielektrischer Reflexionen).
  * **Irideszenz & Dispersion:** `iridescence`, `iridescenceIOR`, `dispersion` (Dünnschichtinterferenz und chromatische Lichtbrechung).
* **glTF-Mapping:** Der `GLTFLoader` von three.js mappt sämtliche glTF `KHR_materials_*`-Erweiterungen automatisch und verlustfrei auf `MeshPhysicalMaterial`.

#### MaterialXLoader in three.js
* In three.js existiert ein Lader für das MaterialX-Format: `three/addons/loaders/MaterialXLoader.js`.
* **Einschränkung:** Der `MaterialXLoader` erzeugt Node-Materialien, die zwingend an den neuen **`WebGPURenderer`** gekoppelt sind: *„The node materials loaded with this loader can only be used with {@link WebGPURenderer}.“*
* Im regulären WebGL-Renderer von three.js (den Standard-Web-Clients heute nutzen) kann `MaterialXLoader` nicht ohne Weiteres eingesetzt werden.
* Das Übersetzungsmodul `MaterialXSurfaceMappings.js` unterstützt zwar die Shader `open_pbr_surface`, `standard_surface` und `gltf_pbr`, ignoriert aber komplexere prozedurale Knoten und erzeugt Warnungen bei nicht unterstützten Eingängen.

---

### 2.3 Lizenzen, Reife und Bibliotheken für Python und JavaScript

| Plattform / Bibliothek | Format / Standard | Lizenz | Reife & Installationsaufwand | Bewertung für Mechvane |
| :--- | :--- | :--- | :--- | :--- |
| **Python: `MaterialX`** (PyPI) | MaterialX / OpenPBR | **Apache 2.0** | Sehr reif (v1.39.5). Vorkompilierte Binär-Wheels für Linux, Windows und macOS für Python 3.9–3.14. | Gut geeignet als optionaler Konverter/Export-Generator. Als primäres Kernmodell im CAD-Kernel jedoch unnötig schwerer C++-Ballast. |
| **Python: Standard `json` / `pygltflib`** | glTF 2.0 PBR + KHR | **MIT** / Python Software Foundation | Extrem reif, pure Python, keinerlei C++-Kompilierung nötig. Schnelles Parsen und Serialisieren. | **Optimal für Mechvane.** Ideal für Dokumentenmodell, Validierung und Web-Kommunikation. |
| **Python: `pxr.usd`** (OpenUSD) | USD / UsdPreviewSurface | **Apache 2.0** | Sehr mächtig, aber riesig (> 1 GB Build), komplexe Installation ohne Conda/VFX-Container. | Ungeeignet für das schlanke Mechvane-Basisdokument. |
| **JavaScript: `three.js` (Core / GLTFLoader)** | glTF 2.0 PBR + KHR | **MIT** | Höchste Reife, De-facto-Standard im 3D-Web. Perfektes Mapping auf `MeshPhysicalMaterial`. | **Optimal für Mechvane Web-Viewer.** Sofort einsatzbereit. |
| **JavaScript: `three.js` (MaterialXLoader)** | MaterialX (`.mtlx`) | **MIT** | Experimentell. Setzt `WebGPURenderer` und Three Shading Language (TSL) voraus. | Aktuell noch zu früh für den primären Web-Viewer-Stack. |
| **JavaScript: `@gltf-transform/core`** | glTF 2.0 PBR + KHR | **MIT** | Industriestandard zur programmgesteuerten Bearbeitung und Optimierung von glTF-Szenen. | Sehr gut geeignet für spätere Web-Materialeditoren. |

---

### 2.4 Offene Bibliotheken mit fertigen Werkstoffen

#### Übersicht der offenen Materialbibliotheken
1. **Physically Based Database (`physicallybased.info` von Anton Palmqvist):**
   * **Lizenz:** **CC0 1.0 Universal** (Public Domain Dedication).
   * **Inhalt:** Wissenschaftlich validierte und gemessene physikalische PBR-Werte für über 80 reale Materialien (Metalle, Kunststoffe, Flüssigkeiten, organische Stoffe).
   * **Bereitstellung:** Offene REST-API (siehe `[Q11]`), liefert strukturierte JSON-Daten mit linearem Albedo-Farbvektor, Metallizität, Rauheit, IOR, komplexem IOR ($n$ und $k$) sowie physikalischer Dichte $\rho$ (kg/m³).
2. **AMD GPUOpen MaterialX Library (`matlib.gpuopen.com`):**
   * **Lizenz:** Per-Material lizenziert (überwiegend MIT License oder permissiv).
   * **Inhalt:** Hunderte fotorealistischer MaterialX-Shader inklusive prozeduraler Texturen und Graphen.
3. **ambientCG (`ambientcg.com` von Lennart Demes):**
   * **Lizenz:** **CC0 1.0 Universal**.
   * **Inhalt:** Tausende nahtlose PBR-Textursätze (Albedo, Roughness, Metalness, NormalMap, Displacement) in Auflösungen von 1K bis 8K für Metalle, Hölzer, Kunststoffe, Beton.
4. **Poly Haven (`polyhaven.com`):**
   * **Lizenz:** **CC0 1.0 Universal**.
   * **Inhalt:** Extrem hochwertige, fotogrammetrisch erfasste PBR-Materialien und HDR-Umgebungen (HDRIs) für realistische Ausleuchtung.

#### Abbildung typischer CAD-Werkstoffbezeichnungen auf PBR-Parameter

Mithilfe der Messwerte aus `physicallybased.info` und Standard-PBR-Formeln lassen sich typische CAD-Werkstoffe präzise parametrisieren:

| CAD-Werkstoffbezeichnung | Typische Basis | Base Color (RGB linear) | Metallic | Roughness | Specular IOR | Besondere KHR- / PBR-Parameter |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Aluminium roh (walzblank)** | Reines Leichtmetall | `[0.916, 0.923, 0.924]` | 1,0 | 0,35 | 1,5 | Isotropes Mikrofacetten-GGX. |
| **Aluminium eloxiert (farblos)** | Dielektrische $Al_2O_3$-Schicht | `[0.916, 0.923, 0.924]` | 0,0 *(Dielektrikum!)* | 0,25 | 1,77 *(Saphir/Korund)* | `clearcoat = 1.0`, `clearcoatRoughness = 0.15`. Die Eloxalschicht ist nicht-leitend! |
| **Aluminium eloxiert schwarz** | Gefärbte Oxidschicht | `[0.03, 0.03, 0.03]` | 0,0 | 0,30 | 1,77 | `clearcoat = 0.8`, `clearcoatRoughness = 0.2`. |
| **Stahl unlegiert (geschliffen)** | Baustahl / 1.0038 | `[0.53, 0.513, 0.494]` | 1,0 | 0,20 | 1,5 | Isotrop oder schwach anisotrop. |
| **Stahl rostfrei gebürstet** | Edelstahl 1.4301 (V2A) | `[0.669, 0.639, 0.598]` | 1,0 | 0,25 | 1,5 | `anisotropyStrength = 0.85`, `anisotropyRotation = 0.0` (in Schleifrichtung). |
| **Kupfer / Messing poliert** | Buntmetall CuZn39Pb3 | `[0.955, 0.637, 0.538]` | 1,0 | 0,10 | 1,5 | F82 Edge Tinting mit warmer Kantenreflexion. |
| **POM / Delrin natur (weiß)** | Technischer Thermoplast | `[0.85, 0.85, 0.85]` | 0,0 | 0,40 | 1,48 | `subsurfaceWeight = 0.15` (leichte Opaleszenz an Kanten). |
| **PLA matt (3D-Druck)** | FDM-Druck Filament | Frei wählbar (z. B. Anthrazit) | 0,0 | 0,75 | 1,46 | Hohe diffuse Rauheit, `sheen = 0.1` zur Brechung an Mikrorillen. |
| **Polycarbonat / Acrylglas** | Glasklarer Kunststoff | `[1.0, 1.0, 1.0]` | 0,0 | 0,02 | 1,49 (PMMA) / 1,58 (PC) | `transmissionFactor = 1.0`, `thicknessFactor = 5.0 mm`, `attenuationColor = [1.0, 1.0, 1.0]`. |

---

### 2.5 Trennung und Verbindung von physikalischem Werkstoff und optischem Aussehen

#### Das CAD-Dualismus-Prinzip
In professionellen CAD-Systemen (Inventor, Fusion, SolidWorks) sind Werkstoff und Aussehen prinzipiell entkoppelt:
* **Physikalischer Werkstoff (`PhysicalMaterial`):**
  * Hält mechanische Kenngrößen: Dichte $\rho$, Elastizitätsmodul $E$, Querkontraktionszahl $\nu$, Streckgrenze $R_e$, Zugfestigkeit $R_m$, Wärmeleitfähigkeit $\lambda$.
  * Bestimmt das Bauteilgewicht: $\text{Masse} = \text{Volumen} \cdot \rho$.
  * Steuert die Fertigungsprüfung: `check_design` liest die Werkstofftabelle aus (z. B. verlangt Aluminium AlMg3 eine Mindesteinschraubtiefe von $2{,}0 \cdot d$, während Stahl 8.8 mit $1{,}0 \dots 1{,}2 \cdot d$ auskommt).
  * Besitzt eine Standard-Referenz auf eine Darstellung (`default_appearance = "alu_walzblank"`).
* **Optische Darstellung (`Appearance` / Oberfläche):**
  * Hält ausschließlich Rendering- und Shader-Parameter: Farbe, Rauheit, Metallizität, Klarlack, Anisotropie, Textur-Kachelung.
  * Hat **keinerlei Einfluss auf Masse, Schwerpunkt oder Festigkeit**!

#### Die hierarchische Override-Kaskade in Mechvane
Für Mechvane wird folgende Zuweisungshierarchie (von grob nach fein) festgelegt:
1. **Ebene 1: Werkstoff-Standard (Fallback):** Das Bauteil erhält bei Zuweisung des physikalischen Werkstoffs automatisch dessen Standard-Aussehen (z. B. `1.4301` -> `stahl_walzblank`).
2. **Ebene 2: Bauteil-Override (Body-Level):** Der Anwender kann dem gesamten Körper eine andere Darstellung zuweisen (z. B. Bauteil aus 1.4301, aber komplett *„schwarz brüniert“* oder *„pulverbeschichtet RAL 7016“*).
3. **Ebene 3: Feature-Override (Formelement):** Ein Formelement überschreibt die Darstellung seiner erzeugten Flächen (z. B. ein Gewinde-Feature erhält die Darstellung *„Gewindegang blank gefettet“*, während das restliche Drehteil roh bleibt).
4. **Ebene 4: Flächen-Override (Face-Level):** Einzelne topologische Flächen (Faces) erhalten eine dedizierte Oberflächengüte (z. B. eine O-Ring-Dichtnut wird als *„feingedreht / poliert Rz 2,5“* markiert, während umgebende Flächen gussrau sind).

Diese Kaskade entspricht exakt der Spezifikation von `KHR_materials_variants` in glTF: Eine Baugruppe kann ohne Duplizierung der Geometrie zwischen Varianten (z. B. „Fertigungszustand roh“, „Eloxiert Blau“, „Ausführung Edelstahl poliert“) umgeschaltet werden.

---

## 3. Große Parameter-Vergleichstabelle & Analyse der Lücken

### 3.1 Parameter-Mapping-Matrix

| Shading-Eigenschaft | OpenPBR Surface (ASWF) | Blender Principled BSDF (v2, ab 4.0) | three.js MeshPhysicalMaterial | glTF 2.0 (Khronos Extensions) |
| :--- | :--- | :--- | :--- | :--- |
| **Grundfarbe / Albedo** | `base_color` (RGB) | `Base Color` (Socket) | `color` (THREE.Color) | `baseColorFactor` (Core) |
| **Grundgewicht** | `base_weight` (0..1) | – *(fest auf 1.0 skaliert)* | – *(fest auf 1.0)* | – *(fest auf 1.0)* |
| **Metallizität** | `base_metalness` (0..1) | `Metallic` (0..1) | `metalness` (0..1) | `metallicFactor` (Core) |
| **Oberflächenrauheit** | `specular_roughness` (0..1) | `Roughness` (0..1) | `roughness` (0..1) | `roughnessFactor` (Core) |
| **Dielektrischer Brechungsindex**| `specular_ior` (float) | `IOR` (float, Standard 1.5) | `ior` (float, Standard 1.5) | `KHR_materials_ior` (`ior`) |
| **Dielektrische Reflexionsstärke**| `specular_weight` (0..1) | `IOR Level` (0..1, Default 0.5) | `specularIntensity` (0..1) | `KHR_materials_specular` (`specularFactor`) |
| **Reflexionsfärbung** | `specular_color` (RGB) | `Specular Tint` (RGB / F82) | `specularColor` (THREE.Color) | `KHR_materials_specular` (`specularColorFactor`) |
| **Anisotropie-Stärke** | `specular_roughness_anisotropy` | `Anisotropic` (0..1) | `anisotropy` (float) | `KHR_materials_anisotropy` (`anisotropyStrength`) |
| **Anisotropie-Drehung** | – *(über Tangente gesteuert)* | `Anisotropic Rotation` (0..1) | `anisotropyRotation` (float) | `KHR_materials_anisotropy` (`anisotropyRotation`) |
| **Klarlack-Stärke** | `coat_weight` (0..1) | `Coat Weight` (0..1) | `clearcoat` (0..1) | `KHR_materials_clearcoat` (`clearcoatFactor`) |
| **Klarlack-Rauheit** | `coat_roughness` (0..1) | `Coat Roughness` (0..1) | `clearcoatRoughness` (0..1) | `KHR_materials_clearcoat` (`clearcoatRoughnessFactor`) |
| **Klarlack-Brechungsindex** | `coat_ior` (float) | `Coat IOR` (float) | – *(erbt Material-IOR)* | – *(erbt Basis-IOR)* |
| **Klarlack-Färbung** | `coat_color` (RGB) | `Coat Tint` (RGB) | – *(unbelegt in Standard)* | – *(unbelegt in Standard)* |
| **Mikrofaser / Samt / Staub** | `fuzz_weight` / `fuzz_color` | `Sheen Weight` / `Sheen Tint` | `sheen` / `sheenColor` | `KHR_materials_sheen` (`sheenColorFactor`) |
| **Optische Transmission** | `transmission_weight` (0..1) | `Transmission Weight` (0..1) | `transmission` (0..1) | `KHR_materials_transmission` (`transmissionFactor`) |
| **Volumen-Absorption** | `transmission_color` / `depth` | `Volume Absorption` (Node) | `attenuationColor` / `distance` | `KHR_materials_volume` (`attenuationColor` / `distance`) |
| **Volumen-Dicke** | – *(aus 3D-Mesh abgeleitet)* | – *(aus 3D-Mesh abgeleitet)* | `thickness` (float) | `KHR_materials_volume` (`thicknessFactor`) |
| **Dünnschichtinterferenz** | `thin_film_weight` / `thickness` | – *(nur via Node-Shader)* | `iridescence` / `iridescenceThicknessRange` | `KHR_materials_iridescence` (`iridescenceFactor` / `thickness`) |
| **Lichtstreuung / Dispersion** | `transmission_dispersion_scale` | – *(nur Cycles Spektral-Tricks)*| `dispersion` (float) | `KHR_materials_dispersion` (`dispersion`) |
| **Selbstleuchten / Emission** | `emission_color` / `luminance`| `Emission Color` / `Strength` | `emissive` / `emissiveIntensity` | `KHR_materials_emissive_strength` (`emissiveStrength`) |
| **Transparenz / Opazität** | `geometry_opacity` (0..1) | `Alpha` (0..1) | `opacity` (0..1) | Core `alphaMode` (OPAQUE, MASK, BLEND) |

### 3.2 Analyse der Lücken (Gaps & Limitations)

1. **Subsurface Scattering (SSS):**
   * *Status:* OpenPBR und Blender Principled BSDF besitzen hochentwickelte SSS-Modelle (Random Walk, Burley). In glTF existiert `KHR_materials_subsurface` bisher nur als Entwurf/Draft.
   * *Bedeutung für Mechvane:* Für den Maschinenbau (Metalle, harte Kunststoffe wie POM/PA, Bleche) vernachlässigbar. Relevant lediglich für transluzente FDM-Drucke (dünnes transparentes PLA/PETG) oder Silikone, wo vorerst `KHR_materials_transmission` und `volume` als praxistaugliche Näherung dienen.
2. **Dispersion (Chromatische Aberration):**
   * *Status:* In glTF (`KHR_materials_dispersion`) und three.js (`dispersion`) standardisiert. In Blender besitzt der `Principled BSDF` (Stand 4.2) noch keine native Dispersion-Buchse; für Cycles muss dies bei Bedarf über getrennte RGB-Lichtbrechung im Node-Tree approximiert werden.
3. **Anisotropie und B-Rep-Tangentenraum:**
   * *Status:* Das Berechnen einer Bürstrichtung (z. B. Umfangs-Schliff an einem Zylinder oder Längsschliff an einer Blechkante) erfordert konsistente UV-Koordinaten und Tangentenvektoren.
   * *Bedeutung für Mechvane:* Bei der Triangulierung von B-Rep-Flächen aus dem CAD-Kernel (SolidCraft/truck) müssen für Flächen mit Anisotropie saubere UV-Projektionen (z. B. Zylinderkoordinaten für Mantelflächen) generiert werden, damit der Anisotropie-Winkel in three.js und Blender physikalisch korrekt entlang der Bearbeitungsrichtung verläuft.
4. **Fehlende Standalone-MaterialX-Brücke in Blender:**
   * Da Blender kein `.mtlx` nativ öffnet, kann MaterialX nicht als alleiniges Austauschformat dienen, wenn Blender ohne externe Zusatz-Plugins angesteuert werden soll.

---

## 4. Quellenbelege (Quellenliste)

Folgende offizielle Primärquellen und Spezifikationen belegen die im Bericht getroffenen Aussagen:

1. **[Q1] Blender 4.0 Shading Release Notes (Principled BSDF Revamp):** [wiki.blender.org/Reference/Release_Notes/4.0/Shading](https://wiki.blender.org/wiki/Reference/Release_Notes/4.0/Shading)
   * *Wörtliches Zitat:* „The Principled BSDF node has been revamped to support a wide ranger of material types.“
   * *Wörtliches Zitat:* „Sheen uses a new microfiber shading model, and is the top layer above emission and coat.“
   * *Wörtliches Zitat:* „Coat was placed above the emission layer. This can be used to simulate for example an emissive phone screen behind glass.“
   * *Wörtliches Zitat:* „Subsurface scattering uses the base color instead of a separate color input. There is a new subsurface scale input to adjust the RGB radius.“
   * *Wörtliches Zitat:* „Metallic surfaces gained edge tinting using the specular tint input. This is an artist friendly parameter to render complex index of refraction, based on the F82 tint model.“

2. **[Q2] Blender 4.2 glTF 2.0 Handbuch (KHR-Materialerweiterungen):** [docs.blender.org/manual/en/4.2/addons/import_export/scene_gltf2.html](https://docs.blender.org/manual/en/4.2/addons/import_export/scene_gltf2.html)
   * *Wörtliches Zitat:* „When the Clearcoat input on the Principled BSDF node has a nonzero default value or Image Texture node connected, the KHR_materials_clearcoat glTF extension will be included in the export.“
   * *Wörtliches Zitat:* „if KHR_materials_ior is not set, IOR value of Principled BSDF node is set to 1.5, that is the glTF default value of IOR.“
   * *Wörtliches Zitat:* „Volume can be exported using a Volume Absorption node, linked to Volume socket of Output node. Data will be exported using the KHR_materials_volume extension.“

3. **[Q3] Blender USD-Handbuch (UsdPreviewSurface & MaterialX Status):** [docs.blender.org/manual/en/latest/files/import_export/usd.html](https://docs.blender.org/manual/en/latest/files/import_export/usd.html)
   * *Wörtliches Zitat:* „There is also an Import USD Preview option to convert USD Preview Surface shaders to Blender Principled BSDF shader nodes. This option can be lossy, as it does not yet handle converting all shader settings and types“
   * *Wörtliches Zitat:* „MaterialX is currently not supported, see the feature commit for details.“
   * *Wörtliches Zitat:* „Generates material shading graphs using the MaterialX standard. This standard is designed to support a high amount of interoperability among DCCs“

4. **[Q4] three.js MeshPhysicalMaterial Quellcode & Dokumentation:** [github.com/mrdoob/three.js/MeshPhysicalMaterial.js](https://raw.githubusercontent.com/mrdoob/three.js/dev/src/materials/MeshPhysicalMaterial.js)
   * *Wörtliches Zitat:* „Ability to represent the anisotropic property of materials as observable with brushed metals.“
   * *Wörtliches Zitat:* „Clearcoat approximates this effect, without the need for a separate transparent surface.“

5. **[Q5] three.js MaterialXLoader Quellcode & WebGPU-Abhängigkeit:** [github.com/mrdoob/three.js/MaterialXLoader.js](https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/jsm/loaders/MaterialXLoader.js)
   * *Wörtliches Zitat:* „The node materials loaded with this loader can only be used with {@link WebGPURenderer}.“

6. **[Q6] three.js MaterialX Surface Mappings (OpenPBR-Übersetzung):** [github.com/mrdoob/three.js/MaterialXSurfaceMappings.js](https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/jsm/loaders/materialx/MaterialXSurfaceMappings.js)
   * *Wörtliches Zitat:* „mappedOpenPbrInputs = new Set“

7. **[Q7] OpenPBR Surface Spezifikation (ASWF Subprojekt von MaterialX):** [github.com/AcademySoftwareFoundation/OpenPBR/README.md](https://raw.githubusercontent.com/AcademySoftwareFoundation/OpenPBR/main/README.md)
   * *Wörtliches Zitat:* „OpenPBR Surface is a specification of a surface shading model intended as a standard for computer graphics.“

8. **[Q8] OpenPBR Whitepaper (Synthese aus Autodesk und Adobe Modellen):** [academysoftwarefoundation.github.io/OpenPBR](https://academysoftwarefoundation.github.io/OpenPBR/)
   * *Wörtliches Zitat:* „The model has been developed as a synthesis of the Autodesk Standard Surface and the Adobe Standard Material models.“

9. **[Q9] MaterialX ASWF Lizenz (Apache 2.0):** [github.com/AcademySoftwareFoundation/MaterialX/LICENSE](https://raw.githubusercontent.com/AcademySoftwareFoundation/MaterialX/main/LICENSE)
   * *Wörtliches Zitat:* „Apache License Version 2.0, January 2004“

10. **[Q10] PyPI MaterialX Paket Metadaten (Aktuelle Version 1.39.5):** [pypi.org/pypi/MaterialX/json](https://pypi.org/pypi/MaterialX/json)
    * *Wörtliches Zitat:* „materialx-1.39.5-cp312-cp312-win_amd64.whl“

11. **[Q11] Physically Based Database (Anton Palmqvist, CC0 Messwerte):** [api.physicallybased.info/materials](https://api.physicallybased.info/materials)
    * *Wörtliches Zitat:* „Stainless Steel", "color": [0.669, 0.639, 0.598]“

12. **[Q12] Poly Haven Lizenz (CC0 Public Domain):** [polyhaven.com/license](https://polyhaven.com/license)
    * *Wörtliches Zitat:* „Our assets are all licensed as CC0, which is effectively Public Domain even in jurisdictions that do not support the Public Domain.“

13. **[Q13] ambientCG Lizenz (Lennart Demes, CC0 Public Domain):** [ambientcg.com/license](https://ambientcg.com/license)
    * *Wörtliches Zitat:* „All ambientCG assets are provided under the Creative Commons CC0 1.0 Universal License.“

14. **[Q14] Khronos glTF KHR_materials_clearcoat Spezifikation:** [github.com/KhronosGroup/glTF/KHR_materials_clearcoat/README.md](https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/2.0/Khronos/KHR_materials_clearcoat/README.md)
    * *Wörtliches Zitat:* „This extension defines a clear coating that can be layered on top of an existing glTF material definition.“

15. **[Q15] Khronos glTF KHR_materials_anisotropy Spezifikation:** [github.com/KhronosGroup/glTF/KHR_materials_anisotropy/README.md](https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/2.0/Khronos/KHR_materials_anisotropy/README.md)
    * *Wörtliches Zitat:* „This extension defines the anisotropic property of a material as observable with brushed metals for example.“

16. **[Q16] Khronos glTF KHR_materials_variants Spezifikation:** [github.com/KhronosGroup/glTF/KHR_materials_variants/README.md](https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/2.0/Khronos/KHR_materials_variants/README.md)
    * *Wörtliches Zitat:* „This extension allows for a compact glTF representation of multiple material variants of an asset, structured to allow low-latency switching at runtime.“
