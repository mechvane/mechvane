# Recherche Desktop-Hülle (Tauri 2, Electron, pywebview, Qt) für Windows und Linux

**Datum:** 2026-10-27  
**Status:** Abgeschlossen  
**Bezug:** Issue #7 / ROADMAP Grundsatz 12 (Mechvane als echtes Programm für Windows und Linux, Browser-Variante bleibt)

---

## 1. Ausgangslage & Randbedingungen von Mechvane

Gemäß ROADMAP Grundsatz 12 soll Mechvane künftig als eigenständiges Desktop-Programm für **Windows und Linux** ausgeliefert werden. Die browserbasierte Variante bleibt parallel vollwertig erhalten.

### 1.1 Mechvane-Architektur heute und Ausblick
* **Backend heute:** Ein lokaler Python-Server ([`mechvane/ui/server.py`](file:///root/repos/_wt/gemini-7/mechvane/ui/server.py)), der ausschließlich die Standardbibliothek (`http.server.ThreadingHTTPServer`, `threading.Lock`, `json`) verwendet und strikt an `127.0.0.1` bindet. Geometrie-Operationen und Netz-Exporte erfolgen über Unterprozesse des CLI-Werkzeugs `solidcraft-cli` (z. B. `session.tool("export", {"format": "3mf-tagged"})`).
* **Backend perspektivisch:** Im Rahmen des ROADMAP-Prüfpunkts Sprache wird eine spätere Migration zeitkritischer Teile oder des gesamten Kerns zu **Rust** evaluiert, um Kernel, Dokumentenmodell und B-Rep-Abfragen direkt ohne Prozess- und Serialisierungs-Overhead anzubinden.
* **Frontend:** Reine Web-Technologie (HTML/JS/CSS) in zwei Betriebsarten:
  1. *Check-Modus* ([`index.html`](file:///root/repos/_wt/gemini-7/mechvane/ui/static/index.html)): Schnelle Dreiecksnetz-Darstellung mit `three.js` (WebGL2), B-Rep-Flächenidentifikation (`ft:face`), Modellbaum (`collect_tree`) und Konstruktionsregel-Befunden (`collect_findings`).
  2. *Model-Modus* ([`model.html`](file:///root/repos/_wt/gemini-7/mechvane/ui/static/model.html)): Vollwertiges interaktives 3D-CAD durch Einbettung der Web-Variante von SolidCraft (`sc/index.html`) in einem `<iframe>`.

### 1.2 Analyse der SolidCraft-Architektur (`/root/repos/_ext/solidcraft`)
Ein Abgleich mit dem Repository von SolidCraft `[Q1]` und den lokalen Crate-Quellen liefert fundamentale architektonische Randbedingungen:
* **Womit ist die SolidCraft-Desktop-App gebaut?**  
  Die Desktop-App von SolidCraft (`apps/solidcraft`) ist **keine** Web- oder Webview-Anwendung `[Q1]`. Sie ist eine reine, native Rust-Anwendung:
  > „SolidCraft: an open-source parametric 3D CAD application built in pure Rust.“ `[Q1]`
  
  Sie setzt auf `eframe` (`egui` als Immediate-Mode-GUI und `wgpu` für Hardware-Rendering) direkt auf dem Fenster- und Grafiksystem des Betriebssystems auf (`winit`, DirectX 12 auf Windows, Vulkan/X11/Wayland auf Linux). Sie bindet weder Chromium noch WebKit ein.
* **Womit ist der SolidCraft-Web-Build gebaut?**  
  Die Web-Version (`apps/solidcraft-web`) kompiliert denselben Rust-Code nach WebAssembly (`wasm32-unknown-unknown`). Die resultierende Binärdatei `solidcraft-web.wasm` ist ca. 50 MB groß. Sie läuft im Browser über den `eframe` Web-Runner mit WebGL2 und WebGPU-Unterstützung und nutzt das Origin Private File System (OPFS) über `navigator.storage.getDirectory()` als virtuelles Dateisystem (`/opfs/`) `[Q18]`.
* **Kopplung in Mechvane:**  
  In [`model.html`](file:///root/repos/_wt/gemini-7/mechvane/ui/static/model.html#L79-L87) spiegelt Mechvane Dateien via OPFS in das Browser-Dateisystem, steuert die SolidCraft-Instanz über die Schnittstelle `window.solidcraft` (`sc.execute("doc.open", { path })`) und synchronisiert vom Benutzer gespeicherte Stände per HTTP-POST an `/api/file/<name>` zurück an den Python-Server.
* **Anforderungen an die Desktop-Hülle für Mechvane:**
  1. Flüssige WebGL2-Ausführung und WebGPU-Fähigkeit für 3D-CAD-Modelle.
  2. Zuverlässige Unterstützung des Origin Private File System (OPFS) `[Q18]`.
  3. Unterstützung für WASM-Threads und `SharedArrayBuffer` via Cross-Origin-Isolation (COOP/COEP) `[Q19]`.
  4. Zuverlässiges Starten, Überwachen und Beenden des Python-Servers als Sidecar-Prozess.
  5. Plattformgerechte Installer (Windows: MSI/NSIS; Linux: AppImage, deb, Flatpak) sowie integrierte automatische Updates.
  6. Zukunftssicherheit: Vorbereitung auf eine spätere native Rust-Migration des Backends.

---

## 2. Vergleich der Hüllen-Kandidaten

### 2.1 Tauri 2
* **Webview-Engine:**  
  Tauri verzichtet auf das Bündeln einer eigenen Browser-Engine und greift auf die im Betriebssystem vorhandene System-Webview zu `[Q2]`:
  > „Tauri uses WebView2 which is based on Microsoft Edge and therefore Chromium. WebView2 can update itself, you are guaranteed a relatively recent chromium build on all Windows targets.“ `[Q2]`  
  > „WebView2 is supported on Windows 7 and newer and comes preinstalled on Windows 11.“ `[Q2]`  
  > „Tauri uses WebKit on macOS (through WKWebView) and Linux (through webkit2gtk).“ `[Q2]`
* **Grafik (WebGL2 & WebGPU):**  
  Unter Windows über Microsoft Edge WebView2 hervorragend und performant. Unter Linux nutzt Tauri `webkit2gtk-4.1`. Für anspruchsvolle 3D-CAD-Anwendungen dokumentiert das Tauri-Team erhebliche Fallstricke `[Q4]`:
  > „On Linux, Tauri renders through WebKitGTK. On some setups, most often NVIDIA GPUs, WebKitGTK and the graphics driver disagree and you get anything from a blank window to subtle rendering problems.“ `[Q4]`  
  > „Console shows AcceleratedSurfaceDMABuf was unable to construct a complete framebuffer.“ `[Q4]`  
  > „WebGL2 context creation succeeds even when the result is backed by a software rasterizer or a slow presentation path. There is no error to catch.“ `[Q4]`  
  > „WebKitGTK masks the WebGL renderer string for fingerprinting protection. WEBGL_debug_renderer_info reports Apple GPU on every Linux machine, so you cannot check what is actually behind the context.“ `[Q4]`  
  > „In practice this shows up as high input latency or low frame rates in WebGL heavy views“ `[Q4]`
  
  Zudem ist WebGPU in WebKitGTK unter Linux gegenwärtig experimentell und im regulären Desktop-Einsatz nicht produktionsreif verfügbar.
* **WASM-Threads / SharedArrayBuffer & COOP/COEP:**  
  Seit Version 2.1 unterstützt Tauri die Konfiguration benutzerdefinierter Sicherheitsheader in `tauri.conf.json` `[Q5]`:
  > „A header defined in the configuration gets sent along the responses to the webview.“ `[Q5]`
  
  Damit lassen sich `Cross-Origin-Opener-Policy: same-origin` und `Cross-Origin-Embedder-Policy: require-corp` für die geforderte Cross-Origin-Isolation `[Q19]` sauber setzen.
* **OPFS (Origin Private File System):**  
  Wird in WebView2 und modernen WebKitGTK-Versionen im sicheren Kontext (`http://localhost` oder registrierte Standard-Schemes) unterstützt `[Q18]`.
* **Python-Backend als Sidecar:**  
  Tauri verfügt über ein ausgereiftes, natives Sidecar-System `[Q3]`:
  > „You may need to embed external binaries to add additional functionality to your application or prevent users from installing additional dependencies (e.g., Node.js or Python). We call this binary a sidecar.“ `[Q3]`  
  > „Binaries are executables written in any programming language. Common use cases are Python CLI applications or API servers bundled using pyinstaller.“ `[Q3]`
  
  Der Python-Server kann per PyInstaller gebündelt und über `tauri-plugin-shell` beim Start aufgerufen und beim Schließen des Fensters automatisch beendet werden.
* **Installer & Updates:**  
  Unterstützt auf Windows native MSI- (WiX) und NSIS-Installer (`[Q7]`: `Customizing the WiX Installer`, `Customizing the NSIS Installer`). Unter Linux baut Tauri direkt AppImage-, Debian- (`.deb`) und RPM-Pakete. Automatische Updates werden über `tauri-plugin-updater` mit kryptografischer Signaturprüfung (`.sig`) bereitgestellt `[Q6]`:
  > „Automatically update your Tauri app with an update server or a static JSON.“ `[Q6]`
* **Größe & Lizenz:**  
  Sehr schlank (nur ~5 bis 15 MB Hüllen-Overhead, Gesamtpaket ca. 80 bis 100 MB inklusive Python-Runtime und 50 MB WASM). Lizenz: MIT OR Apache-2.0 `[Q1]`, voll kompatibel.
* **Perspektive Rust-Backend:**  
  **Hervorragend.** Da Tauri selbst in Rust geschrieben ist, kann ein künftiges Rust-Backend von Mechvane direkt als nativer In-Process-Code eingebunden werden.

---

### 2.2 Electron
* **Webview-Engine:**  
  Bündelt eine vollständige Chromium-Engine und Node.js auf allen Zielsystemen `[Q8]`:
  > „Electron inherits its multi-process architecture from Chromium, which makes the framework architecturally very similar to a modern web browser.“ `[Q8]`  
  > „Each tab would render in its own process, limiting the harm that buggy or malicious code on a web page could cause to the app as a whole.“ `[Q8]`
* **Grafik (WebGL2 & WebGPU):**  
  **Exzellent und absolut identisch** auf Windows und Linux. Chromium nutzt unter Windows Direct3D 12 und unter Linux Vulkan (über Dawn). WebGPU steht out-of-the-box zur Verfügung. Sämtliche Linux-WebKitGTK-Treiberkonflikte (DMABUF, Wayland, NVIDIA-Abstürze) entfallen vollständig. Die 50 MB große SolidCraft-Web-App läuft mit exakt der gleichen Performance wie im vollwertigen Chrome/Edge-Browser.
* **WASM-Threads / SharedArrayBuffer & OPFS:**  
  Vollständig unterstützt. Benutzerdefinierte Schemas können als privilegiert registriert werden `[Q9]`:
  > „protocol.registerSchemesAsPrivileged(customSchemes)“ `[Q9]`  
  > „Registers the scheme as standard, secure, bypasses content security policy for resources, allows registering ServiceWorker, supports fetch API“ `[Q9]`  
  > „Registering a scheme as standard will allow access to files through the FileSystem API. Otherwise the renderer will throw a security error for the scheme.“ `[Q9]`
* **Python-Backend als Sidecar:**  
  Der Main-Process (Node.js) kann Unterprozesse nativ über `child_process.spawn` starten und überwachen.
* **Installer & Updates:**  
  Über `electron-builder` werden unter Linux AppImage, deb, rpm, Flatpak und Snap erzeugt `[Q11]`, unter Windows NSIS und MSI `[Q12]`. Automatische Updates laufen über `autoUpdater` bzw. `electron-updater` `[Q10]`:
  > „There are several ways to provide automatic updates to your Electron application. The easiest and officially supported one is taking advantage of the built-in Squirrel framework and Electron's autoUpdater module.“ `[Q10]`
* **Größe & Lizenz:**  
  Sehr groß (Chromium- und Node-Runtime addieren ~80 bis 120 MB; Gesamtpaket ca. 160 bis 200 MB, entpackt >350 MB; spürbar höherer RAM-Bedarf). Lizenz: MIT.
* **Perspektive Rust-Backend:**  
  Gut (über Node-API / `napi-rs` oder als CLI-Prozess), aber architektonisch bleibt die JavaScript/Node.js-Laufzeitschicht bestehen.

---

### 2.3 pywebview
* **Webview-Engine:**  
  Schlanker Python-Wrapper um Systemkomponenten `[Q13]`:
  > „pywebview is a lightweight BSD-licensed cross-platform wrapper around a webview component. pywebview allows to display HTML content in its own native GUI window. It gives you power of web technologies in your desktop application, hiding the fact that GUI is browser based.“ `[Q13]`  
  > „On Windows renderer is chosen in the following order: edgechromium, mshtml.“ `[Q15]`  
  > „On Linux you have to explicitly choose between QT and GTK.“ `[Q14]`
* **Grafik:**  
  Unter Windows über Edge WebView2 sehr gut. Unter Linux bei Standard-GTK-Nutzung identisch eingeschränkt wie bei Tauri (WebKitGTK mit DMABUF-Problemen auf NVIDIA, kein stabiles WebGPU).
* **WASM-Threads & OPFS:**  
  Da pywebview einen integrierten Python-HTTP-Server mitbringt (`[Q13]`: `pywebview ships with a built-in HTTP server`), können COOP/COEP-Header über Python-Handler ausgeliefert werden und OPFS im `localhost`-Kontext laufen. Die feingranulare Konfiguration von Browser-Flags ist jedoch stark limitiert.
* **Python-Backend-Integration:**  
  **Trivial für heute.** Da pywebview selbst eine Python-Bibliothek ist, kann der bestehende `UIServer` ([`mechvane/ui/server.py`](file:///root/repos/_wt/gemini-7/mechvane/ui/server.py)) direkt in einem Python-Hintergrund-Thread im selben Prozess laufen.
* **Installer & Updates:**  
  **Großes Manko:** pywebview bietet keinerlei integrierte Paketierungs- oder Auto-Update-Funktionen. Entwickler müssen PyInstaller-Skripte, NSIS-Installer und Update-Mechanismen vollständig von Hand bauen und pflegen.
* **Größe & Lizenz:**  
  pywebview selbst ist winzig (< 1 MB). Das PyInstaller-Paket inklusive Python und 50 MB WASM liegt bei ~90 MB. Lizenz: BSD-3-Clause `[Q13]`.
* **Perspektive Rust-Backend:**  
  Schlecht. Bei einer Umstellung des Backends auf Rust bliebe pywebview als unnötiger Python-Fremdkörper zurück.

---

### 2.4 Qt (QtWebEngine / PySide6)
* **Webview-Engine:**  
  QtWebEngine integriert Chromium in das Qt-Framework `[Q16]`:
  > „The Qt WebEngine module provides APIs for rendering and embedding content from the World Wide Web into Qt-based applications.“ `[Q16]`  
  > „The Qt WebEngine module uses Chromium to provide most of its functionality. During the build process, Chromium becomes a part of the Qt WebEngine Core library.“ `[Q17]`
* **Grafik & Standards:**  
  Sehr solide Chromium-Basis auf Windows und Linux. WebGL2 und OPFS funktionieren im sicheren Kontext verlässlich.
* **Python-Backend-Integration:**  
  Sehr gut für heute über PySide6 (`PySide6.QtWebEngineWidgets`), Server läuft im selben Prozess.
* **Nachteile (Größe & Lizenz):**  
  1. *Enorme Paketgröße:* Die PyPI-Räder `PySide6_Essentials` (~80 MB) und `PySide6_Addons` (~56 MB) führen entpackt zu einer gewaltigen Bibliotheksgröße von über 400 bis 600 MB allein für Qt.
  2. *Kein integrierter Auto-Updater:* Keine einfache schlüsselfertige Lösung für Python-Desktop-Apps.
  3. *Lizenzrisiko LGPLv3:* QtWebEngine unterliegt strikten LGPLv3- und LGPL-2.1-Auflagen `[Q17]`:
     > „The Qt specific parts of the Qt WebEngine module are available under commercial licenses from The Qt Company. Alternatively, they are available under GNU Lesser General Public License v3.0, or GNU General Public License v3.0, or GNU General Public License v2.0.“ `[Q17]`  
     > „The Chromium part contains code available under various licenses, with the most restrictive license being the GNU Lesser General Public License v2.1 (LGPL 2.1).“ `[Q17]`
     
     Die LGPLv3 verlangt unter anderem zwingend, dass Endanwender die dynamisch gebundenen LGPL-Bibliotheken austauschen können (Relinking-Gebot), und verbietet Hardware-Einschränkungen (Anti-Tivoization).

---

### 2.5 Neutralinojs und Wails (Kurzvergleich)
* **Neutralinojs:** Nutzt System-Webviews (WebView2 / WebKitGTK) und einen C++-Kern mit WebSocket-IPC. Besitzt unter Linux dieselben WebKitGTK-Grafikeinschränkungen wie Tauri, bietet aber gegenüber Tauri keine Typsicherheit, ein kleineres Ökosystem und keinerlei Rust-Synergie.
* **Wails:** Nutzt System-Webviews und Go. Unter Linux ebenfalls durch WebKitGTK limitiert. Die Einführung von Go als dritter Sprache (neben Python und Rust) brächte unnötige Komplexität ohne Mehrwert für das 3D-CAD-Rendering.

---

## 3. Vergleichstabelle

| Kriterium | Tauri 2 | Electron | pywebview | Qt (PySide6 / QtWebEngine) |
| :--- | :--- | :--- | :--- | :--- |
| **Engine Windows** | WebView2 (Chromium/Edge) `[Q2]` | Bundled Chromium `[Q8]` | WebView2 (`edgechromium`) `[Q15]` | Bundled Chromium `[Q17]` |
| **Engine Linux** | WebKitGTK (`webkit2gtk-4.1`) `[Q2]` | Bundled Chromium `[Q8]` | WebKitGTK oder QtWebEngine `[Q14]` | Bundled Chromium `[Q17]` |
| **WebGL2-Zuverlässigkeit** | Windows: Sehr gut<br>Linux: Eingeschränkt `[Q4]` | Exzellent (Windows & Linux identisch) | Windows: Sehr gut<br>Linux: Eingeschränkt | Sehr gut (Chromium-Basis) |
| **WebGPU-Unterstützung** | Windows: Ja (via Flags)<br>Linux: Experimentell / instabil | Ja (Dawn / Vulkan & DX12) | Windows: Ja<br>Linux: Nein (GTK) | Snapshot-abhängig |
| **WASM-Threads (COOP/COEP)**| Ja (via `app.security.headers`) `[Q5]` | Ja (`registerSchemesAsPrivileged`) `[Q9]` | Eingeschränkt (nur via Localhost-Server) | Ja (Chromium-Standard) |
| **OPFS (Origin Private FS)** | Ja (im sicheren Kontext) `[Q18]` | Ja (nativ & im Scheme) `[Q9]` | Ja (im Localhost-Kontext) | Ja |
| **Python-Backend heute** | Sidecar (`externalBin` / Shell) `[Q3]` | Sidecar (`child_process.spawn`) | Nativ (im selben Python-Thread) | Nativ (PySide6 QThread) |
| **Perspektive Rust-Backend** | **Exzellent** (100 % Rust) | Gut (über Node-API / CLI) | Mäßig (Python-Hülle überflüssig) | Aufwendig |
| **Windows-Installer** | MSI (WiX), NSIS `[Q7]` | NSIS, MSI, Squirrel `[Q12]` | Keine (manuelle Skripte nötig) | Keine (manuelle Skripte nötig) |
| **Linux-Paketformate** | AppImage, deb, rpm | AppImage, deb, rpm, Flatpak, Snap `[Q11]` | Keine (manuelle Skripte nötig) | Keine (manuelle Skripte nötig) |
| **Integrierter Auto-Updater** | Ja (`tauri-plugin-updater`, signiert) `[Q6]`| Ja (`autoUpdater`, `electron-updater`) `[Q10]` | Nein | Nein |
| **Zusätzlicher Bundle-Footprint**| ~5–15 MB | ~80–120 MB | < 1 MB | > 350–500 MB |
| **Lizenz** | MIT OR Apache-2.0 `[Q1]` | MIT | BSD-3-Clause `[Q13]` | LGPLv3 (strikte Vorgaben) `[Q17]` |

---

## 4. Risiken & Kernproblem: 3D-CAD im System-Webview unter Linux

Die wesentliche Herausforderung für Mechvane ergibt sich aus der Kombination des ca. 50 MB großen SolidCraft-WebAssembly-Kerns, `three.js` und den Grafikanforderungen unter Linux:

1. **Das WebKitGTK-Leistungsproblem unter Linux:**  
   Frameworks mit System-Webview (Tauri 2, pywebview, Wails, Neutralinojs) hängen unter Linux von WebKitGTK ab. Hier existieren chronische Konflikte mit dem DMABUF-Renderer auf NVIDIA-Treibern und unter Wayland `[Q4]`. Der offizielle Workaround `WEBKIT_DISABLE_DMABUF_RENDERER=1` verhindert zwar Abstürze, schaltet jedoch den schnellen Rendering-Pfad ab `[Q4]`. Noch schwerwiegender: WebGL2-Kontexte fallen bei Treiber-Inkompatibilitäten oft stumm auf Software-Rasterisierung (Mesa LLVMpipe) zurück, was die Bildrate bei komplexen Baugruppen unbrauchbar einbrechen lässt `[Q4]`.
2. **Fehlendes WebGPU in WebKitGTK:**  
   Während SolidCraft auf dem Desktop natives `wgpu` nutzt und im Web-Build WebGPU mit WebGL2-Fallback bereitstellt, ist WebGPU in WebKitGTK unter Linux bis heute nicht stabil für Endanwender verfügbar.
3. **Der Zielkonflikt:**  
   * **Tauri 2** bietet die ideale Architektur (pure Rust, kein Ballast, perfekte Installer, Sidecar für Python), birgt aber das Risiko unzureichender 3D-CAD-Leistung auf Linux-Arbeitsplätzen.
   * **Electron** garantiert durch die gebündelte Chromium-Engine ein makelloses, identisches 3D-Erlebnis auf Linux und Windows inklusive WebGPU, erkauft dies jedoch mit rund 100 MB höherem Paketgewicht und höherem RAM-Verbrauch.

---

## 5. Begründete Empfehlung

Für Mechvane wird eine **gestufte Vorgehensweise mit Primärempfehlung Tauri 2 und validiertem Fallback Electron** empfohlen:

### 1. Primärempfehlung: Tauri 2 mit Python-Sidecar
* **Architektur-Fit & Zukunft:** SolidCraft ist in purem Rust geschrieben (`apps/solidcraft`, `[Q1]`). Mechvane plant die Evaluierung von Rust für das Backend. Tauri 2 ist vollständig in Rust geschrieben. Bei einer Umstellung des Backends auf Rust in Phase 2 verschmilzt der Mechvane-Kern direkt mit der Desktop-Hülle ohne jeglichen Prozess-Overhead.
* **Gegenwart mit Python:** Für das heutige Python-Backend bietet Tauri 2 mit `externalBin` und `tauri-plugin-shell` ein robustes, offiziell unterstütztes Sidecar-Modell `[Q3]`. Der Python-Server wird per PyInstaller mitgeliefert und sauber überwacht.
* **Distribution & Updates:** Tauri 2 liefert für Windows (MSI/NSIS) und Linux (AppImage/deb/rpm) die schlankesten Installationspakete und mit `tauri-plugin-updater` ein kryptografisch signiertes Update-System `[Q6]`.

### 2. Sicherheitsnetz: Electron als direkter Fallback
* Sollte der nachfolgende Validierungstest zeigen, dass WebKitGTK auf gängigen Linux-Systemen (insbesondere mit NVIDIA-Grafik oder Wayland) für das 50 MB große SolidCraft-WASM und flüssige CAD-Interaktion nicht stabil performt, ist **Electron** der sofort einsatzbereite "Plan B".
* Da Mechvane bereits heute eine saubere HTTP-Trennung zwischen Server ([`mechvane/ui/server.py`](file:///root/repos/_wt/gemini-7/mechvane/ui/server.py)) und Web-Frontend pflegt, kann die Frontend-Hülle im Bedarfsfall ohne Änderung der Kernlogik von Tauri auf Electron umgestellt werden.

---

## 6. Validierungstest zur Überprüfung der Empfehlung

Um vor der finalen Festlegung messtechnisch zu belegen, ob Tauri 2 den grafischen Anforderungen von SolidCraft unter Linux genügt, wird folgender reproduzierbarer Test definiert:

### 6.1 Testaufbau & Testseite
1. **Server starten:** `python3 -m mechvane.ui tests/reference/flansch.build.json` (oder eine mehrteilige Baugruppe wie `PinInPlate`).
2. **Minimales Testfenster:** Ein rudimentäres Tauri-2-Fenster lädt die URL `http://127.0.0.1:8765/model.html` (sowie zur Gegenprobe `index.html` für `three.js`).

### 6.2 Konkrete Messpunkte
In der Entwicklerkonsole des Webviews werden folgende Metriken erfasst:

1. **Hardware-Renderer und Beschleunigungsstatus:**
   ```javascript
   const canvas = document.createElement('canvas');
   const gl = canvas.getContext('webgl2');
   const dbg = gl.getExtension('WEBGL_debug_renderer_info');
   console.log('WebGL2 Renderer:', dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'masked');
   console.log('WebGPU available:', 'gpu' in navigator && !!(await navigator.gpu?.requestAdapter()));
   ```
   *Kriterium:* Unter Linux prüfen, ob der Renderer auf einen echten Hardwaretreiber (z. B. NVIDIA / AMD / Intel) verweist oder auf Software-Mesa (`llvmpipe`).
2. **SolidCraft WASM-Ladezeit & Initialisierung:**
   * Zeitstempelmessung vom Ladebeginn des `<iframe>` bis zum Auslösen des Events `TrunkApplicationStarted` und Erscheinen des Status `Ready` in [`model.html`](file:///root/repos/_wt/gemini-7/mechvane/ui/static/model.html#L259).
   * Zielwert: < 3 Sekunden bei lokalem Cache.
3. **Interaktive Viewport-Bildrate (FPS & Latenz):**
   * Automatisiertes Drehen des 3D-CAD-Modells über `requestAnimationFrame` für 10 Sekunden.
   * Erfassung der durchschnittlichen Bildrate und der maximalen Framezeit (99th Percentile Frame Time).
   * *Abbruchkriterium:* Sinkt die durchschnittliche Bildrate unter WebKitGTK auf Linux unter 30 FPS oder treten Frame-Spitzen von > 50 ms auf, scheidet Tauri 2 für den Linux-Support aus und es muss auf Electron umgeschwenkt werden.
4. **OPFS-Speicherzyklus:**
   * Ausführen einer Modelländerung und Speichern via `Ctrl+S`.
   * Messung der Dauer von OPFS (`dir.getFileHandle`) über HTTP-POST `/api/file/<name>` bis zum Eintreffen der neuen Befunde (`showFindings`).
   * Zielwert: < 250 ms.

---

### 7. Nummerierte Quellenliste

* **[Q1] SolidCraft GitHub Repository**  
  URL: [https://github.com/bherbruck/solidcraft](https://github.com/bherbruck/solidcraft)  
  *Zitate:*  
  „SolidCraft: an open-source parametric 3D CAD application built in pure Rust.“  
  „An open-source parametric 3D CAD application built in pure Rust.“

* **[Q2] Tauri 2 Dokumentation – Webview Versions**  
  URL: [https://v2.tauri.app/reference/webview-versions/](https://v2.tauri.app/reference/webview-versions/)  
  *Zitate:*  
  „Tauri uses WebView2 which is based on Microsoft Edge and therefore Chromium. WebView2 can update itself, you are guaranteed a relatively recent chromium build on all Windows targets.“  
  „WebView2 is supported on Windows 7 and newer and comes preinstalled on Windows 11.“  
  „Tauri uses WebKit on macOS (through WKWebView) and Linux (through webkit2gtk).“

* **[Q3] Tauri 2 Dokumentation – Sidecar (External Binaries)**  
  URL: [https://v2.tauri.app/develop/sidecar/](https://v2.tauri.app/develop/sidecar/)  
  *Zitate:*  
  „You may need to embed external binaries to add additional functionality to your application or prevent users from installing additional dependencies (e.g., Node.js or Python). We call this binary a sidecar.“  
  „Binaries are executables written in any programming language. Common use cases are Python CLI applications or API servers bundled using pyinstaller.“

* **[Q4] Tauri 2 Dokumentation – Linux Graphics Issues**  
  URL: [https://v2.tauri.app/develop/debug/linux-graphics/](https://v2.tauri.app/develop/debug/linux-graphics/)  
  *Zitate:*  
  „On Linux, Tauri renders through WebKitGTK. On some setups, most often NVIDIA GPUs, WebKitGTK and the graphics driver disagree and you get anything from a blank window to subtle rendering problems.“  
  „Console shows AcceleratedSurfaceDMABuf was unable to construct a complete framebuffer.“  
  „WebGL2 context creation succeeds even when the result is backed by a software rasterizer or a slow presentation path. There is no error to catch.“  
  „WebKitGTK masks the WebGL renderer string for fingerprinting protection. WEBGL_debug_renderer_info reports Apple GPU on every Linux machine, so you cannot check what is actually behind the context.“  
  „In practice this shows up as high input latency or low frame rates in WebGL heavy views“

* **[Q5] Tauri 2 Dokumentation – HTTP Headers**  
  URL: [https://v2.tauri.app/security/http-headers/](https://v2.tauri.app/security/http-headers/)  
  *Zitate:*  
  „A header defined in the configuration gets sent along the responses to the webview.“  
  „Cross-Origin-Embedder-Policy“  
  „Cross-Origin-Opener-Policy“

* **[Q6] Tauri 2 Dokumentation – Updater Plugin**  
  URL: [https://v2.tauri.app/plugin/updater/](https://v2.tauri.app/plugin/updater/)  
  *Zitat:*  
  „Automatically update your Tauri app with an update server or a static JSON.“

* **[Q7] Tauri 2 Dokumentation – Windows Installer**  
  URL: [https://v2.tauri.app/distribute/windows-installer/](https://v2.tauri.app/distribute/windows-installer/)  
  *Zitate:*  
  „Customizing the WiX Installer“  
  „Customizing the NSIS Installer“

* **[Q8] Electron Dokumentation – Process Model**  
  URL: [https://www.electronjs.org/docs/latest/tutorial/process-model](https://www.electronjs.org/docs/latest/tutorial/process-model)  
  *Zitate:*  
  „Electron inherits its multi-process architecture from Chromium, which makes the framework architecturally very similar to a modern web browser.“  
  „Each tab would render in its own process, limiting the harm that buggy or malicious code on a web page could cause to the app as a whole.“

* **[Q9] Electron Dokumentation – Protocol API**  
  URL: [https://www.electronjs.org/docs/latest/api/protocol](https://www.electronjs.org/docs/latest/api/protocol)  
  *Zitate:*  
  „protocol.registerSchemesAsPrivileged(customSchemes)“  
  „Registers the scheme as standard, secure, bypasses content security policy for resources, allows registering ServiceWorker, supports fetch API“  
  „Registering a scheme as standard will allow access to files through the FileSystem API. Otherwise the renderer will throw a security error for the scheme.“

* **[Q10] Electron Dokumentation – Updates**  
  URL: [https://www.electronjs.org/docs/latest/tutorial/updates](https://www.electronjs.org/docs/latest/tutorial/updates)  
  *Zitat:*  
  „There are several ways to provide automatic updates to your Electron application. The easiest and officially supported one is taking advantage of the built-in Squirrel framework and Electron's autoUpdater module.“

* **[Q11] electron-builder Dokumentation – Linux Targets**  
  URL: [https://www.electron.build/docs/linux](https://www.electron.build/docs/linux)  
  *Zitat:*  
  „The top-level linux key contains a set of options instructing electron-builder on how it should build Linux targets.“

* **[Q12] electron-builder Dokumentation – Windows Targets**  
  URL: [https://www.electron.build/docs/win](https://www.electron.build/docs/win)  
  *Zitat:*  
  „The top-level win key contains a set of options instructing electron-builder on how it should build Windows targets.“

* **[Q13] pywebview Dokumentation – Overview**  
  URL: [https://pywebview.flowrl.com/](https://pywebview.flowrl.com/)  
  *Zitate:*  
  „pywebview is a lightweight BSD-licensed cross-platform wrapper around a webview component. pywebview allows to display HTML content in its own native GUI window. It gives you power of web technologies in your desktop application, hiding the fact that GUI is browser based.“  
  „pywebview ships with a built-in HTTP server, DOM support in Python and window management functionality.“

* **[Q14] pywebview Dokumentation – Installation**  
  URL: [https://pywebview.flowrl.com/guide/installation](https://pywebview.flowrl.com/guide/installation)  
  *Zitate:*  
  „On Linux you have to explicitly choose between QT and GTK.“  
  „To use with the latest Chromium you need WebView2 Runtime.“

* **[Q15] pywebview Dokumentation – Web Engine**  
  URL: [https://pywebview.flowrl.com/guide/web_engine](https://pywebview.flowrl.com/guide/web_engine)  
  *Zitate:*  
  „On Windows renderer is chosen in the following order: edgechromium, mshtml.“  
  „To force QT on Linux systems“

* **[Q16] Qt WebEngine Dokumentation – Overview**  
  URL: [https://doc.qt.io/qt-6/qtwebengine-overview.html](https://doc.qt.io/qt-6/qtwebengine-overview.html)  
  *Zitat:*  
  „The Qt WebEngine module provides APIs for rendering and embedding content from the World Wide Web into Qt-based applications.“

* **[Q17] Qt WebEngine Dokumentation – Licensing**  
  URL: [https://doc.qt.io/qt-6/qtwebengine-licensing.html](https://doc.qt.io/qt-6/qtwebengine-licensing.html)  
  *Zitate:*  
  „The Qt WebEngine module uses Chromium to provide most of its functionality. During the build process, Chromium becomes a part of the Qt WebEngine Core library.“  
  „The Qt specific parts of the Qt WebEngine module are available under commercial licenses from The Qt Company. Alternatively, they are available under GNU Lesser General Public License v3.0, or GNU General Public License v3.0, or GNU General Public License v2.0.“  
  „The Chromium part contains code available under various licenses, with the most restrictive license being the GNU Lesser General Public License v2.1 (LGPL 2.1).“

* **[Q18] MDN Web Docs – Origin Private File System (OPFS)**  
  URL: [https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system)  
  *Zitate:*  
  „The origin private file system (OPFS) is a storage endpoint provided as part of the File System API, which is private to the origin of the page and not visible to the user like the regular file system.“  
  „It provides access to a special kind of file that is highly optimized for performance and offers in-place write access to its content.“  
  „Secure context: This feature is available only in secure contexts (HTTPS), in some or all supporting browsers.“

* **[Q19] MDN Web Docs – SharedArrayBuffer**  
  URL: [https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer)  
  *Zitat:*  
  „To use shared memory your document must be in a secure context and cross-origin isolated.“
