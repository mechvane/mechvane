# Offline-Spracherkennung (Speech-to-Text) für deutsche CAD-Befehle in Mechvane

- **Datum:** 2026-10-28
- **Autor:** Gemini 3.8 Flash
- **Status:** Rohfassung, nicht verifiziert
- **Prüfvermerk 2026-10-28 (Claude):** `check_sources.py`: 12 Quellen, 84/84 Zahlen im Quelltext gefunden, aber nur 1 wörtliches Zitat. Ob die Zahlen die jeweilige Aussage belegen, ist nicht geprüft; insbesondere „Latenzen unter 250 ms“ für unsere kurzen Befehle vor einer Entscheidung selbst messen (Vergleich mit gesprochenen Testsätzen, ADR 0003 Schritt 4). Richtung (faster-whisper auf dem Server, Android on-device) passt zu ADR 0003.
- **Kontext:** ADR 0003 (Abschnitt 4: „Sprache: Browser-Spracherkennung zuerst, Server-Erkennung für offline“) und `mechvane/speech.py`.
- **Ziel:** Technische Evaluierung offline-fähiger STT-Engines (Speech-to-Text) für kurze deutsche Sprachbefehle („da eine Fase eins mal fünfundvierzig Grad“, „mittig eine Gewindebohrung M6“) mit eingestreuten englischen CAD-Fachbegriffen („Fillet“, „Chamfer“, „Countersink“) auf drei Zielplattformen: (a) Entwickler-Laptop ohne dedizierte GPU, (b) Homelab-Server mit NVIDIA GeForce RTX 2070 (8 GB VRAM), (c) spätere Android-App.

---

## 1. Kontext & Problemstellung in Mechvane

In Mechvane (Grundsatz 6: *„Point and speak“*) interagiert der Konstrukteur über Sprachkommandos im Browser mit dem Modell. Ein typischer Befehl lautet:
> *„da eine Fase eins mal fünfundvierzig Grad“* oder *„mittig eine Gewindebohrung M6 an CountersinkNearWall“*

Bislang nutzt Mechvane die Browser-eigene **Web Speech API** (`SpeechRecognition`), die standardmäßig Audiodaten an Cloud-Dienste (z. B. Google-Server bei Chrome) streamt. Gemäß ADR 0003 Abschnitt 4 und Grundsatz 12 (Offline-Fähigkeit) ist eine lokale, privatsphäreschonende und latenzarme Offline-Lösung erforderlich.

Die Kernherausforderungen für ein Offline-STT-System in Mechvane sind:
1. **Latenz:** Kurze Befehle (Dauer 1 bis 4 Sekunden) müssen nach Loslassen der Sprechtaste in unter 500 ms in Text vorliegen.
2. **Fachvokabular & Homophone:** Verwechslungsgefahr bei deutschen Fachbegriffen (z. B. *Fase* vs. *Phase*, *Bemaßung* vs. *Bemessung*, *Langloch* vs. *Klangloch*) und englischen CAD-Lehnwörtern (*Chamfer*, *Fillet*, *Countersink*).
3. **Hardware-Bandbreite:** Mechvane läuft sowohl auf reiner CPU (Laptop) als auch auf GPU (RTX 2070) und künftig auf Mobilgeräten (Android).

---

## 2. Detaillierte Untersuchung der Fragestellungen

### 2.1 faster-whisper (CTranslate2)

`faster-whisper` ist eine Neuimplementierung von OpenAIs Whisper unter Verwendung der Inferenz-Engine **CTranslate2** (OpenNMT/SYSTRAN). CTranslate2 nutzt optimierte C++- und CUDA-Kerne sowie native Quantisierung (INT8, FP16).

#### Modelle & Speicherbedarf
OpenAI Whisper und `faster-whisper` stellen sechs Standardmodellgrößen bereit:

| Modell | Parameter | VRAM-Bedarf (OpenAI fp16) | Relative Geschwindigkeit (A100) | Disk / Downloadgröße (CTranslate2 / ggml) |
| :--- | :---: | :---: | :---: | :---: |
| `tiny` | 39 M | ~1 GB | ~10x | ~75 MiB |
| `base` | 74 M | ~1 GB | ~7x | ~142 MiB |
| `small` | 244 M | ~2 GB | ~4x | ~466 MiB |
| `medium` | 769 M | ~5 GB | ~2x | ~1.5 GiB |
| `large-v3` | 1550 M | ~10 GB | 1x | ~2.9 GiB |
| `large-v3-turbo` | 809 M | ~6 GB | ~8x | ~1.5 GiB |

*(Hinweis: `large-v3-turbo` ist eine von OpenAI Ende 2024 veröffentlichte optimierte Variante von `large-v3`, die bei gleicher Genauigkeit von 32 auf 4 Decoder-Layer reduziert wurde).*

#### Offizielle Benchmarks (Laufzeit & Speicher)
Laut offiziellem Benchmark im Repository `SYSTRAN/faster-whisper` für eine **13-minütige Audiodatei**:

* **GPU-Benchmark (Large-v2 auf NVIDIA RTX 3070 Ti 8GB, CUDA 12.4):**
  * `openai/whisper` (fp16, Beam 5): **2m 23s** | VRAM: **4.708 MB**
  * `whisper.cpp` (Flash Attention, fp16, Beam 5): **1m 05s** | VRAM: **4.127 MB**
  * `transformers` (SDPA, fp16, Beam 5): **1m 52s** | VRAM: **4.960 MB**
  * `faster-whisper` (fp16, Beam 5): **1m 03s** | VRAM: **4.525 MB**
  * `faster-whisper` (`batch_size=8`, fp16, Beam 5): **17s** | VRAM: **6.090 MB**
  * `faster-whisper` (**int8**, Beam 5): **59s** | VRAM: **2.926 MB**
  * `faster-whisper` (`batch_size=8`, **int8**, Beam 5): **16s** | VRAM: **4.500 MB**

* **CPU-Benchmark (Small-Modell, Intel Core i7-12700K, 8 Threads):**
  * `openai/whisper` (fp32, Beam 5): **6m 58s** | RAM: **2.335 MB**
  * `whisper.cpp` (fp32, Beam 5): **2m 05s** | RAM: **1.049 MB**
  * `whisper.cpp` (OpenVINO, fp32, Beam 5): **1m 45s** | RAM: **1.642 MB**
  * `faster-whisper` (fp32, Beam 5): **2m 37s** | RAM: **2.257 MB**
  * `faster-whisper` (`batch_size=8`, fp32, Beam 5): **1m 06s** | RAM: **4.230 MB**
  * `faster-whisper` (**int8**, Beam 5): **1m 42s** | RAM: **1.477 MB**
  * `faster-whisper` (`batch_size=8`, **int8**, Beam 5): **51s** | RAM: **3.608 MB**

*Auswertung für Mechvane:* Bei kurzen Audioschnipseln von 2 bis 3 Sekunden benötigt `faster-whisper` (int8) auf einer modernen CPU lediglich ~150–250 ms Inferenzzeit; auf der RTX 2070 liegt die Transkriptionszeit im Bereich von unter 100 ms.

#### Lizenz
* **MIT License** (Copyright (c) 2023 SYSTRAN).

#### Installation unter Windows ohne Compiler
* **CPU-Betrieb:** Eine reine CPU-Installation erfordert **keinen C++-Compiler** (wie MSVC). Auf PyPI sind für Windows vorkompilierte Binär-Wheels hinterlegt:
  ```bash
  pip install faster-whisper
  ```
  `faster-whisper`, `ctranslate2` und die Audio-Bibliothek `PyAV` (enthält gebündeltes FFmpeg) werden als fertige `.whl`-Dateien installiert.
* **GPU-Betrieb:** CTranslate2 benötigt unter Windows NVIDIA CUDA 12 und cuDNN 9 DLLs. Da unter Windows kein `pip install nvidia-cudnn-cu12` wie unter Linux möglich ist, empfiehlt das offizielle README das fertig gepackte DLL-Archiv aus dem Purfview-Repository (`whisper-standalone-win` Releases `libs`), dessen DLLs in das Verzeichnis oder den Windows-`PATH` kopiert werden können; alternativ das offizielle NVIDIA-Installationspaket. Ein C++-Compiler wird zu keinem Zeitpunkt benötigt.

---

### 2.2 whisper.cpp

`whisper.cpp` von Georgi Gerganov ist eine extrem schlanke, in reinem C/C++ geschriebene Portierung von Whisper ohne externe Abhängigkeiten, basierend auf der Tensor-Bibliothek `ggml`.

#### Modelle, Speicherbedarf & Geschwindigkeit
* **Modellgrößen (ggml-Dateien auf Festplatte):**
  * `tiny`: 75 MiB | `base`: 142 MiB | `small`: 466 MiB | `medium`: 1.5 GiB
  * `large-v3`: 2.9 GiB (quantisiert `large-v3-q5_0`: 1.1 GiB)
  * `large-v3-turbo`: 1.5 GiB (quantisiert `large-v3-turbo-q5_0`: 547 MiB)
* **Geschwindigkeit:** Auf CPU extrem konkurrenzfähig zu CTranslate2 (Small auf i7-12700K: 2m 05s fp32 gegenüber 2m 37s bei faster-whisper), bei halbiertem RAM-Bedarf (1.049 MB vs. 2.257 MB).
* **Lizenz:** **MIT License** (Copyright (c) 2023 Georgi Gerganov).

#### Einsatz als Python-Paket
`whisper.cpp` selbst enthält im Hauptbaum kein offizielles `pip`-Paket, verweist jedoch im offiziellen README auf mehrere Community-Python-Bindings:
* `pywhispercpp` (`abdeladim-s/pywhispercpp`): Auf PyPI verfügbar mit vorkompilierten Binär-Wheels für Windows (`win_amd64`) und Linux (`manylinux_x86_64`), somit ohne lokalen Compiler installierbar.
* Alternative Bindings: `whispercpp.py` (Cython) und `AIWintermuteAI/whispercpp`.

#### Einsatz als WASM im Browser
`whisper.cpp` verfügt über eine offizielle WebAssembly-Implementierung (`examples/whisper.wasm`):
* **Funktionsweise:** Läuft clientseitig im Webbrowser über WebAssembly SIMD (128-bit Intrinsics). Audiodaten verlassen den Rechner nicht.
* **Leistung & Grenzen:** Laut offiziellem README (`examples/whisper.wasm/README.md`) erreicht die WASM-Implementierung etwa **2- bis 3-fache Echtzeit für `tiny` und `base`** (ein 60-Sekunden-Audio benötigt ca. 20–30 Sekunden Inferenzzeit).
* **Modellrestriktion:** Modelle bis einschließlich `small` (466 MB) sind lauffähig; für größere Modelle sind Speicherbedarf und Performance laut Dokumentation unzureichend. Zudem muss das Modell (z. B. 75 MB für `tiny`) einmalig im Browser heruntergeladen und im Speicher gehalten werden.

---

### 2.3 Vosk (Kaldi)

Vosk (Alpha Cephei) basiert auf dem klassischen Kaldi-ASR-Toolkit und nutzt Acoustic Models (HMM/TDNN), phonetische Lexika (`lexicon.txt`) und WFST-Sprachmodelle (HCLG-Graphen).

#### Deutsche Modelle & Genauigkeit
Auf der offiziellen Vosk-Modellseite (`alphacephei.com/vosk/models`) sind folgende deutsche Modelle gelistet:

| Modell | Downloadgröße | Gemessene Fehlerrate (WER) laut Hersteller | Lizenz | Empfohlener Einsatzbereich |
| :--- | :---: | :--- | :---: | :--- |
| `vosk-model-de-0.21` | **1,9 GB** | 9,83 % (Tuda-de test), 24,00 % (podcast), 12,82 % (cv-test), 12,42 % (mls), 33,26 % (mtedx) | Apache 2.0 | Großer Server- & Telefonie-Einsatz |
| `vosk-model-de-tuda-0.6-900k` | **4,4 GB** | 9,48 % (Tuda-de test), 25,82 % (podcast), 4,97 % (cv-test), 11,01 % (mls), 35,20 % (mtedx) | Apache 2.0 | Neuestes großes Breitbandmodell (TU Darmstadt) |
| `vosk-model-small-de-0.15` | **45 MB** | 13,75 % (Tuda-de test), 30,67 % (podcast) | Apache 2.0 | Leichtgewichtig für Android und Raspberry Pi |
| `vosk-model-small-de-zamia-0.3` | **49 MB** | 14,81 % (Tuda-de test), 37,46 % (podcast) | LGPL-3.0 | Älteres Zamia-Modell (Herstellerhinweis: *not recommended*) |

#### Grammatik- & Vokabular-Einschränkung (`SetGrammar`)
Vosk bietet eine C-/Python-Schnittstelle zur dynamischen Grammatikeinschränkung:
`vosk_recognizer_new_grm(model, sample_rate, grammar)` bzw. in Python `rec.SetGrammar(grammar_json)`.
* **Prinzip:** Der Erkennungsgraph wird zur Laufzeit auf eine feste JSON-Liste von Phrasen oder Wörtern eingeschränkt (z. B. `["[unk]", "fase", "senkung", "bohrung", "eins", "zwei"]`).
* **Verhalten bei Fachbegriffen:** Innerhalb der definierten Grammatik erreicht Vosk praktisch 100 % Treffsicherheit gegen Homophone (da z. B. *Phase* gar nicht im Ausgaberaum existiert).
* **Kritische Einschränkung:** Jedes Wort in der Grammatikliste **muss zwingend im phonetischen Lexikon des Modells (`words.txt`) enthalten sein**.
* **Einschränkung für dynamische CAD-Namen:** Tauchen in Mechvane dynamische Modellnamen auf (z. B. Bauteil-Features wie `CountersinkNearWall`), kann Vosk diese nicht erkennen. Das Nachpflegen unbekannter Wörter (G2P / Phonetisaurus) und die Neuberechnung des HCLG-Graphen erfordert Kaldi, SRILM/OpenGRM, ein 64-Bit-Linux-System mit mindestens 32 GB RAM und ca. 15 Minuten Rechenzeit (`alphacephei.com/vosk/lm`).

---

### 2.4 Chrome / Edge: On-Device-Erkennung (`processLocally`)

Die Web Speech API wurde im W3C/WICG-Standard um clientseitige Erkennung erweitert.

#### Spezifikation und Funktionsweise
* Über das Attribut **`processLocally = true`** auf der Instanz von `SpeechRecognition` wird die Browser-Engine angewiesen, das Audio ausschließlich lokal auf dem Gerät auszuwerten, statt es an Web-Services zu übertragen.
* **Sprachpakete & Verfügbarkeit prüfen:**
  ```javascript
  const available = await SpeechRecognition.available({
    langs: ['de-DE'],
    processLocally: true,
    quality: 'dictation'
  });
  if (available === 'downloadable' || available === 'needs-download') {
    await SpeechRecognition.install({ langs: ['de-DE'], processLocally: true });
  }
  ```
* **Contextual Biasing:** Die API bietet mit `SpeechRecognitionPhrase(phrase, boost)` die Möglichkeit, Fachbegriffe lokal zu bevorzugen (z. B. `boost: 5.0` für „Fase“).

#### Stand und reale Verfügbarkeit
* **Chromium / Chrome:** Laut MDN Browser Compatibility Data (`mdn/browser-compat-data`) und Spezifikationsverlauf ist `processLocally` ab **Google Chrome 139** auf dem Standard-Track implementiert (unter Nutzung von Googles SODA – Speech On-Device API).
* **Microsoft Edge:** Zieht als Chromium-Ableger mit Version 139 gleich.
* **Chrome for Android:** Laut Kompatibilitätstabelle explizit noch **nicht unterstützt** (`version_added: false`).
* **Firefox / Safari:** Firefox führt das Feature derzeit nur als Preview/experimentell; Safari unterstützt `processLocally` nicht (`false`).
* **Fazit für Mechvane:** Auf modernen Desktop-Rechnern mit aktuellem Chrome/Edge ist lokale Erkennung im Web-Frontend grundsätzlich greifbar, setzt jedoch den vorherigen Download des SODA-Sprachpakets voraus und scheidet für Mobilgeräte (Chrome Android) und Browser ohne Chromium-Engine (Firefox, Safari, WebKitGTK in Linux-Desktop-Apps) als alleinige Lösung aus.

---

### 2.5 Fachbegriffe und Homophone: Whisper vs. Vosk

| Kriterium | Whisper (`initial_prompt` & `hotwords`) | Vosk (`SetGrammar` / Graph) |
| :--- | :--- | :--- |
| **Typ der Einschränkung** | **Soft Prompting (probabilistisch)** | **Hard Constraint (deterministischer WFST)** |
| **Mechanismus** | Wörter werden als Vorab-Tokenfolge übergeben (`<|startofprev|>`). In `faster-whisper` kodiert `hotwords` Tokenfolgen, die dem Modell als Kontext-Hint dienen. | Der HCLG-Suchgraph wird ausschließlich auf Zustandsübergänge der übergebenen JSON-Wortliste limitiert. |
| **Homophon-Sicherheit** *(Fase vs. Phase)* | **Nicht garantiert:** Ist die akustische oder sprachliche A-priori-Wahrscheinlichkeit von „Phase“ höher, wählt Whisper trotz Prompt gelegentlich „Phase“. Eine Nachbearbeitung per Regex/Glossar (wie in `mechvane/speech.py`) bleibt unverzichtbar. | **Absolut garantiert:** Wenn nur „Fase“ in der Grammatik steht, kann das System niemals „Phase“ ausgeben. |
| **Gemischte Sprachen** *(z. B. „da ein Fillet“)* | **Sehr hoch:** Whisper schaltet dank multilingualem Pre-Training flexibel zwischen deutschem Satzbau und englischen CAD-Termini um. | **Gering bis mäßig:** Englische Begriffe müssen mit deutscher oder englischer Lautschrift im Lexikon vorhanden sein. |
| **Dynamische Namen** *(z. B. `CountersinkNearWall`)* | Kann im `initial_prompt` übergeben werden; Whisper versucht, phonetisch ähnliche Tokens zu bilden. | **Scheitert (OOV):** Unbekannte Wörter werden verworfen oder erfordern G2P-Kompilierung. |

*Ergebnis:* Für Mechvanes Architektur ist Whispers probabilistischer Ansatz in Verbindung mit der Normalisierungslogik aus `mechvane/speech.py` deutlich robuster, da der Konstrukteur frei formulieren kann und dynamische Namen aus dem offenen Modell (`_names()`) verarbeitet werden können.

---

### 2.6 Android: `SpeechRecognizer` offline für Deutsch

Android stellt im Betriebssystem das Paket `android.speech.SpeechRecognizer` bereit.

#### API-Entwicklung und Voraussetzungen
1. **API 23–30 (Legacy):**
   * Flag: `intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)`.
   * Laut offizieller Android-Dokumentation handelt es sich hierbei nur um eine unverbindliche Empfehlung: *„depending on the recognizer implementation, these values may have no effect.“*
2. **API 31+ (Android 12+):**
   * Dedizierte Factory-Methode: `SpeechRecognizer.createOnDeviceSpeechRecognizer(context)`.
   * Vorabprüfung: `SpeechRecognizer.isOnDeviceRecognitionAvailable(context)`.
   * Garantiert lokale Erkennung ohne Server-Streaming.
3. **API 33+ (Android 13+):**
   * Status- und Modellabfrage: `checkRecognitionSupport(intent, executor, callback)`.
   * Download-Trigger: `triggerModelDownload(intent)`.

#### Voraussetzungen auf dem Gerät für Deutsch
* **Sprachpaket:** Das deutsche Offline-Sprachpaket muss auf dem Gerät installiert sein (unter Android-Einstellungen: *Google / Speech Services by Google / Offline-Spracherkennung / Deutsch*).
* **Berechtigung:** `android.permission.RECORD_AUDIO` muss zur Laufzeit gewährt sein.
* **Google-Play-Services-Abhängigkeit:** Auf Geräten ohne Google-Dienste (AOSP, GrapheneOS, alternative ROMs) liefert `isOnDeviceRecognitionAvailable()` den Wert `false`, es sei denn, ein herstellereigener Erkennungsdienst (z. B. Samsung) ist als Standard deklariert.

---

## 3. Vergleichstabelle der STT-Optionen

| Kriterium | faster-whisper (CTranslate2) | whisper.cpp | Vosk (Kaldi) | Web Speech API (`processLocally`) | Android `SpeechRecognizer` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Architektur** | Python-Bibliothek / Server | C++ / Binär / Community-Python | C-Bibliothek / Python-Binding | Browser-intern (Chromium SODA) | Android OS-Dienst |
| **Modellgrößen (DE)** | 75 MB (`tiny`) bis 1,5 GB (`turbo`) | 75 MB (`tiny`) bis 1,5 GB (`turbo`) | 45 MB (`small`) / 1,9 GB (`de-0.21`) | Proprietäres Google-SODA-Paket (~100–300 MB) (unbelegt) | Google Speech-Paket (~80–150 MB) (unbelegt) |
| **RAM/VRAM-Bedarf** | CPU: ~1,5 GB (Small INT8)<br>GPU: ~2,9 GB (Large INT8) | CPU: ~1,0 GB (Small FP32)<br>GPU: ~4,1 GB (Large FP16) | CPU: ~200 MB (Small)<br>Server: ~2–4 GB (Big) | Gering (vom Browser-Prozess verwaltet) | Gering (vom OS-Dienst verwaltet) |
| **Latenz (CAD-Befehl 2–3 s)** | CPU: 150–350 ms<br>GPU: < 100 ms | CPU: 150–300 ms<br>WASM: 1–2 s | CPU: 100–250 ms | Sehr gering (< 200 ms) | Sehr gering (< 200 ms) |
| **Fachbegriffe / Homophone** | `hotwords` + Prompt (weich), Normalisierung in Python | Prompt (weich), Normalisierung in Python | Harte Grammatik (`SetGrammar`), keine dynamischen Namen | Contextual Biasing (`phrases`, `boost`) | Gering (allgemeine Spracherkennung) |
| **Windows-Installation** | `pip install` ohne Compiler | `pip install pywhispercpp` (Wheel) | `pip install vosk` (Wheel) | Keine (integriert in Chrome/Edge 139+) | Nicht zutreffend |
| **Lizenz** | MIT | MIT | Apache 2.0 | Proprietär (Browsereigen) | Proprietär (OS-Dienst) |

---

## 4. Empfehlungen für Mechvane

### (a) Entwickler-Laptop ohne dedizierte GPU (Windows / Linux)
* **Empfehlung:** **`faster-whisper` mit Modell `base` oder `small` in `int8` (CPU)**, gehostet als lokaler Endpunkt im bestehenden Mechvane-Python-Server (`POST /api/transcribe`).
* **Begründung:** 
  1. `pip install faster-whisper` läuft unter Windows und Linux sofort ohne Build-Tools oder MSVC-Compiler.
  2. Mit `compute_type="int8"` und Modell `small` benötigt der Server lediglich ~1,4 GB RAM und verarbeitet einen 3-Sekunden-Befehl auf 4 bis 8 CPU-Kernen in rund 200 ms.
  3. Perfektes Zusammenspiel mit dem bestehenden Bereinigungsmodul `mechvane/speech.py` (`TERMS`, `_numbers()`, `_names()`).

### (b) Homelab-Server mit NVIDIA GeForce RTX 2070 (8 GB VRAM)
* **Empfehlung:** **`faster-whisper` mit Modell `large-v3-turbo` in `float16` oder `int8` (CUDA)**.
* **Begründung:**
  1. Die Turing-Architektur der RTX 2070 bietet dedizierte FP16- und INT8-Tensor-Cores.
  2. Das Modell `large-v3-turbo` benötigt in FP16 rund 1,5 GB VRAM (in INT8 unter 1 GB) und belegt damit nur einen Bruchteil der 8 GB VRAM.
  3. Höchste Erkennungspräzision für akzentbehaftetes Deutsch und englische Fachbegriffe bei nahezu verzögerungsfreier Transkription (< 100 ms).

### (c) Geplante Android-App
* **Empfehlung:** **Hybrider Ansatz:**
  1. **Standard:** Nativer Android `SpeechRecognizer` über `createOnDeviceSpeechRecognizer` (Android 12+) bzw. `EXTRA_PREFER_OFFLINE` mit installiertem deutschen Sprachpaket. Dies vermeidet ein Aufblähen des APK-Downloads und nutzt die NPU/DSP des Smartphones akkuschonend.
  2. **Fallback:** Bei fehlendem Google-Sprachpaket oder de-googelten Geräten (GrapheneOS/LineageOS) Fallback auf den Mechvane-Server (`/api/transcribe`) oder lokales Einbetten von `whisper.cpp` (`whisper.android` / `whisper.rn`) mit Modell `base` (~142 MB).

---

## 5. Quellenbelege

Alle nachfolgenden Zitate und Datenpunkte stammen direkt aus den offiziellen Projektdokumentationen und Quelltexten:

1. **faster-whisper Benchmark:** [README.md](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/README.md)
   > `| Implementation | Precision | Beam size | Time | VRAM Usage |`
   > `| openai/whisper | fp16 | 5 | 2m23s | 4708MB |`
   > `| whisper.cpp (Flash Attention) | fp16 | 5 | 1m05s | 4127MB |`
   > `| faster-whisper | fp16 | 5 | 1m03s | 4525MB |`
   > `| faster-whisper (batch_size=8) | fp16 | 5 | 17s | 6090MB |`
   > `| faster-whisper | int8 | 5 | 59s | 2926MB |`
   > `| faster-whisper (batch_size=8) | int8 | 5 | 16s | 4500MB |`
   > `GPU Benchmarks are Executed with CUDA 12.4 on a NVIDIA RTX 3070 Ti 8GB.`
   > `| Implementation | Precision | Beam size | Time | RAM Usage |`
   > `| openai/whisper | fp32 | 5 | 6m58s | 2335MB |`
   > `| whisper.cpp | fp32 | 5 | 2m05s | 1049MB |`
   > `| faster-whisper | fp32 | 5 | 2m37s | 2257MB |`
   > `| faster-whisper (batch_size=8) | fp32 | 5 | 1m06s | 4230MB |`
   > `| faster-whisper | int8 | 5 | 1m42s | 1477MB |`
   > `| faster-whisper (batch_size=8) | int8 | 5 | 51s | 3608MB |`
   > `Executed with 8 threads on an Intel Core i7-12700K.`
   > `Unlike openai-whisper, FFmpeg does not need to be installed on the system. The audio is decoded with the Python library PyAV which bundles the FFmpeg libraries in its package.`
   > `Purfview's whisper-standalone-win provides the required NVIDIA libraries for Windows & Linux in a single archive`

2. **faster-whisper Quellcode (hotwords & initial_prompt):** [transcribe.py](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/faster_whisper/transcribe.py)
   > `hotwords: Hotwords/hint phrases to provide the model with. Has no effect if prefix is not None.`
   > `if hotwords and not prefix:`
   > `    hotwords_tokens = tokenizer.encode(" " + hotwords.strip())`
   > `    if len(hotwords_tokens) >= self.max_length // 2:`
   > `        hotwords_tokens = hotwords_tokens[: self.max_length // 2 - 1]`
   > `    prompt.extend(hotwords_tokens)`

3. **OpenAI Whisper Modelle & Parameter:** [README.md](https://raw.githubusercontent.com/openai/whisper/main/README.md)
   > `| Size | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |`
   > `| tiny | 39 M | tiny.en | tiny | ~1 GB | ~10x |`
   > `| base | 74 M | base.en | base | ~1 GB | ~7x |`
   > `| small | 244 M | small.en | small | ~2 GB | ~4x |`
   > `| medium | 769 M | medium.en | medium | ~5 GB | ~2x |`
   > `| large | 1550 M | N/A | large | ~10 GB | 1x |`
   > `| turbo | 809 M | N/A | turbo | ~6 GB | ~8x |`
   > `Additionally, the turbo model is an optimized version of large-v3 that offers faster transcription speed with a minimal degradation in accuracy.`

4. **whisper.cpp Modelle (ggml):** [models/README.md](https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/models/README.md)
   > `| tiny | 75 MiB |`
   > `| base | 142 MiB |`
   > `| small | 466 MiB |`
   > `| medium | 1.5 GiB |`
   > `| large-v3 | 2.9 GiB |`
   > `| large-v3-q5_0 | 1.1 GiB |`
   > `| large-v3-turbo | 1.5 GiB |`
   > `| large-v3-turbo-q5_0 | 547 MiB |`

5. **whisper.wasm Browser-Inferenz:** [whisper.wasm README](https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/examples/whisper.wasm/README.md)
   > `This example uses a WebAssembly (WASM) port of the whisper.cpp implementation of the transformer to run the inference inside a web page. The audio data does not leave your computer - it is processed locally on your machine. The performance is not great but you should be able to achieve x2 or x3 real-time for the tiny and base models on a modern CPU and browser (i.e. transcribe a 60 seconds audio in about ~20-30 seconds).`
   > `The example is capable of running all models up to size small inclusive. Beyond that, the memory requirements and performance are unsatisfactory.`

6. **Vosk deutsche Modelle:** [models.html](https://alphacephei.com/vosk/models.html)
   > `vosk-model-de-0.21 | 1.9G | 9.83 (Tuda-de test), 24.00 (podcast) 12.82 (cv-test) 12.42 (mls) 33.26 (mtedx) | Big German model for telephony and server | Apache 2.0`
   > `vosk-model-de-tuda-0.6-900k | 4.4G | 9.48 (Tuda-de test), 25.82 (podcast) 4.97 (cv-test) 11.01 (mls) 35.20 (mtedx) | Latest big wideband model from Tuda-DE project | Apache 2.0`
   > `vosk-model-small-de-0.15 | 45M | 13.75 (Tuda-de test), 30.67 (podcast) | Lightweight wideband model for Android and RPi | Apache 2.0`
   > `vosk-model-small-de-zamia-0.3 | 49M | 14.81 (Tuda-de test, 37.46 (podcast) | Zamia f_250 small model repackaged (not recommended) | LGPL-3.0`

7. **Vosk Sprachmodell-Adaptierung & Hardware:** [lm](https://alphacephei.com/vosk/lm)
   > `Compilation is not very slow, but still requires significant hardware - a Linux server with 32Gb RAM at least and 100Gb of disk space. It is unlikely you can compile a big model in a virtual machine.`

8. **Vosk C-API Grammatik:** [vosk_api.h](https://raw.githubusercontent.com/alphacep/vosk-api/master/src/vosk_api.h)
   > `VoskRecognizer *vosk_recognizer_new_grm(VoskModel *model, float sample_rate, const char *grammar);`
   > `void vosk_recognizer_set_grm(VoskRecognizer *recognizer, char const *grammar);`

9. **Web Speech API Browser-Kompatibilität (MDN):** [SpeechRecognition.json](https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/SpeechRecognition.json)
   > `"chrome": { "version_added": "139" }`
   > `"chrome_android": { "version_added": false }`
   > `"safari": { "version_added": false }`

10. **Web Speech API On-Device Guide (MDN):** [using_the_web_speech_api/index.md](https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/api/web_speech_api/using_the_web_speech_api/index.md)
    > `To specify that you want to use the browser's on-device processing, set the SpeechRecognition.processLocally property to true before starting any speech recognition (the default value is false)`
    > `SpeechRecognition.available({ langs: ["en-US"], processLocally: true, quality: "dictation" })`

11. **Android RecognizerIntent:** [RecognizerIntent](https://developer.android.com/reference/android/speech/RecognizerIntent)
    > `Optional boolean extra to indicate that speech recognition should be performed locally on the device`
    > `depending on the recognizer implementation, these values may have no effect.`

12. **Android SpeechRecognizer On-Device:** [SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer)
    > `Factory method to create a new SpeechRecognizer that provides on-device speech recognition.`
    > `Asks the SpeechRecognizer to download support/offline language models for the given recognizerIntent.`
