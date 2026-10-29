# Testsätze für die Spracheingabe (40 Fälle, speech_cases.json) und Analyse

> **Prüfnotiz (Claude, 2026-10-29):** 40 Fälle von Gemini Flash (Issue #21), 11 davon offen. In `speech.py` gelöst:
> Komma-Zahlen mit „ein“, „einhalb“/„zweieinhalb“, Prozent, „Durchmesser acht“ → Ø8, kleines „er“ nur bei Rundungen,
> kleines „m“/„em“ vor Zahlen → M6 (Praxistest Surface), Modellnamen mit Ziffer („hole eins“ → Hole1), „Phase“ → „Fase“
> nur mit Maß oder Kante im Satz. Bewusst nicht: „Rz vier“ → R4 (Rz ist ein Rauheitswert) und „Durchgangsloch“ →
> „Durchgangsbohrung“ (Wortwahl des Nutzers bleibt); beide Fälle erwarten jetzt unveränderten Text. Vier Fälle aus dem
> Surface-Test ergänzt, 44 Fälle, alle grün.

- **Datum:** 2026-10-30
- **Autor:** Gemini 3.8 Flash
- **Status:** Abgeschlossen, verifiziert mit `tests/mechvane/check.py` (0 Fehler)
- **Bezug:** GitHub Issue #21, ADR 0003 (Abschnitt 4: „Point and speak“), Begriffsglossar `docs/research/2026-10-28-abgleich-baugruppe-glossar.md`, STT-Evaluierung `docs/research/2026-10-28-stt-offline-flash.md`
- **Kontext:** Evaluierung und Härtung des Sprachvorverarbeitungsmoduls `mechvane/speech.py` gegen realistische Ausgaben der Browser-Spracherkennung (Web Speech API) und lokaler Offline-STT-Modelle (Whisper).

---

## 1. Ausgangslage & Zielsetzung

In Mechvane (ROADMAP Grundsatz 6: *„Point and speak“*, ADR 0003) spricht der Konstrukteur im Browser oder in der App kurze Arbeitsaufträge, während er Flächen oder Kanten selektiert:
> *„da eine Phase eins mal fünfundvierzig Grad“* oder *„mittig eine Gewindebohrung Em sechs“*

Das Modul `mechvane/speech.py` hat die Aufgabe, die fehleranfällige Transkription der Web Speech API vor der Übergabe an den Agenten deterministisch im Code zu bereinigen:
1. **Zahlwörter → Zahlen:** „eins Komma fünf“ → `1.5`, „zweihundertfünfzig“ → `250`
2. **Einheiten & Symbole:** „Millimeter“ → `mm`, „Grad“ → `°`, Multiplikationswörter „mal“ / „x“ → `×`
3. **CAD-Fachbegriffe & Homophone:** „Phase“ → `Fase`, „Em sechs“ → `M6`, „Er zwei“ → `R2`, „Filet“ → `Fillet`, „Tschämfer“ → `Chamfer`, „Klangloch“ → `Langloch`, „Senkbohrung“ → `Senkung`
4. **Modellnamen:** Einpassen von gesprochenen Wortfolgen auf die tatsächlichen Bezeichner im offenen Dokument (z. B. „countersink near wall“ → `CountersinkNearWall`)

Bislang gab es in `tests/mechvane/check.py` lediglich neun stichprobenartige Fälle in `speech_checks`. Mit Issue #21 wurde ein systematischer Datensatz aus **40 realistischen Testsätzen** in `tests/mechvane/speech_cases.json` geschaffen.

Gemäß Aufgabenstellung wurde `mechvane/speech.py` nicht verändert. Alle 40 Fälle wurden mit `speech.normalize(heard, names)` durchlaufen:
- Fälle, die heute bereits exakt das gewünschte Ergebnis liefern, besitzen `"status": "ok"` (**29 Fälle**).
- Fälle, bei denen die aktuelle Implementierung von `speech.py` an Grenzen stößt oder überkorrigiert, besitzen `"status": "open"` (**11 Fälle**) mit Begründung in `note`.

---

## 2. Übersicht der Testsätze je Kategorie

Die 40 Fälle verteilen sich gleichmäßig auf sieben Kernkategorien:

| Nr. | Kategorie | Fälle gesamt | Status OK | Status Open | Quote OK |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **Zahlen** (Kommazahlen, Hunderter, Bruchzahlen) | 6 | 4 | 2 | 66,7 % |
| 2 | **Einheiten** (mm, cm, Grad, Prozent) | 6 | 4 | 2 | 66,7 % |
| 3 | **Fasen/Rundungen** (Fase, Phase, Radius, R/Er, Chamfer, Fillet) | 6 | 4 | 2 | 66,7 % |
| 4 | **Gewinde und Bohrungen** (M3–M12, Senkung, Langloch, Ø/Durchmesser, Durchgangsbohrung) | 6 | 4 | 2 | 66,7 % |
| 5 | **Bewegen/Ändern** (Translation, Offset, Richtungen, relative Skalierung) | 6 | 5 | 1 | 83,3 % |
| 6 | **Modellnamen** (CamelCase-Mapping, Fuzzy-Matching, Featurenamen) | 5 | 4 | 1 | 80,0 % |
| 7 | **Unverändert** (Vermeidung von Überkorrektur bei Artikeln und Systembefehlen) | 5 | 4 | 1 | 80,0 % |
| **Σ** | **Gesamt** | **40** | **29** | **11** | **72,5 %** |

---

## 3. Detaillierte Analyse der offenen Fälle und Lösungsvorschläge

Die 11 offenen Fälle decken systematische Randfälle und noch nicht implementierte Normalisierungen in `mechvane/speech.py` auf. Nachfolgend werden für jeden offenen Fall der Ist-Zustand, die Ursache im Code und ein konkreter Lösungsvorschlag dokumentiert (nur Vorschlag, nicht umgesetzt).

---

### 3.1 Kategorie Zahlen

#### Fall 5: „ein Komma fünf“ vor Substantiven
- **Gehört (`heard`):** `Plattendicke ein Komma fünf Millimeter`
- **Erwartet (`expected`):** `Plattendicke 1.5 mm`
- **Ist-Zustand heute:** `Plattendicke 1 Komma 5 mm`
- **Code-Ursache in `_numbers()`:**
  In `_numbers()` (Zeilen 54–64) wird das Wort `"ein"` in der Token-Schleife bewusst übersprungen, um unbestimmte Artikel wie „eine Fase“ bzw. „ein Zylinder“ nicht vorzeitig in Ziffern umzuwandeln:
  ```python
  if n is not None and tok.lower().strip(".,;:!?") != "ein":
      out.append(tok.lower().replace(tok.strip(".,;:!?").lower(), str(n)))
  ```
  Die Zusammenführung für Dezimalstellen `re.sub(r"\b(\d+)\s+Komma\s+(\d+)\b", r"\1.\2", s)` sucht jedoch nach `\d+` vor `Komma`. Da `"ein"` noch nicht umgewandelt wurde, greift dieser Regex nicht. Die nachgelagerte Ersetzung `re.sub(r"\bein\s+(?=(?:mal|×|Komma|mm|Grad)\b)", "1 ", s)` wandelt `"ein"` zwar in `"1"` um, aber erst **nach** dem Dezimal-Regex.
- **Lösungsvorschlag für `speech.py`:**
  Vor der Zusammenführung `\b(\d+)\s+Komma\s+(\d+)\b` sollte die Normalisierung von `"ein"` vor `Komma` erfolgen (oder direkt in einem gemeinsamen Regex `r"\b(\d+|ein)\s+Komma\s+(\d+)\b"` mit Lambda-Ersetzung `f"{1 if m.group(1).lower() == 'ein' else m.group(1)}.{m.group(2)}"`).

#### Fall 6: Zusammengesetzte Bruchzahlwörter („zweieinhalb“)
- **Gehört (`heard`):** `Abstand zweieinhalb Millimeter`
- **Erwartet (`expected`):** `Abstand 2.5 mm`
- **Ist-Zustand heute:** `Abstand zweieinhalb mm`
- **Code-Ursache in `_number()`:**
  `_number()` (Zeilen 30–48) unterstützt nur reine Ganzeinheiten bis 999 (`UNITS`, `TEENS`, `TENS`, `hundert`, `und`). Wortbildungen auf `...einhalb` oder `...einviertel` werden nicht erkannt und geben `None` zurück.
- **Lösungsvorschlag für `speech.py`:**
  Erweiterung in `_number()` oder Vorab-Regex in `_numbers()`:
  ```python
  FRACTIONS = {"einhalb": "0.5", "eineinhalb": "1.5", "anderthalb": "1.5",
               "zweieinhalb": "2.5", "dreieinhalb": "3.5", "viereinhalb": "4.5", "fünfeinhalb": "5.5"}
  for word, dec in FRACTIONS.items():
      s = re.sub(rf"\b{word}\b", dec, s, flags=re.I)
  ```

---

### 3.2 Kategorie Einheiten

#### Fall 11 & 12: Einheit Prozent (%)
- **Fall 11:** `Skalierung um fünfzehn Prozent` → Erwartet: `Skalierung um 15 %` (Ist: `Skalierung um 15 Prozent`)
- **Fall 12:** `zehn Prozent Steigung` → Erwartet: `10 % Steigung` (Ist: `10 Prozent Steigung`)
- **Code-Ursache in `_units()`:**
  `_units()` (Zeilen 68–75) normalisiert Multiplikation (`×`), Winkelgrad (`°`), metrische Gewinde (`M...`) und Radien (`R...`). Das Wort `Prozent` ist weder in `TERMS` noch in `_units()` enthalten.
- **Lösungsvorschlag für `speech.py`:**
  Ergänzung in `_units()`:
  ```python
  s = re.sub(r"(\d+(?:\.\d+)?)\s*Prozent\b", r"\1 %", s, flags=re.I)
  ```

---

### 3.3 Kategorie Fasen/Rundungen

#### Fall 17: Case-Sensitivity bei Radien („er fünf“)
- **Gehört (`heard`):** `Rundung er fünf an der Ecke`
- **Erwartet (`expected`):** `Rundung R5 an der Ecke`
- **Ist-Zustand heute:** `Rundung er 5 an der Ecke`
- **Code-Ursache in `_units()`:**
  In Zeile 73 lautet der reguläre Ausdruck:
  ```python
  s = re.sub(r"\b(?:Er|R)\s+(\d+(?:\.\d+)?)\b", r"R\1", s)
  ```
  Es fehlt das Flag `flags=re.I`. Web Speech schreibt kleingesprochene Buchstaben oft als Kleinbuchstaben (`"er"`, `"em"`), wenn sie nicht am Satzanfang stehen. Folglich wird `"er 5"` nicht in `"R5"` umgewandelt. (Gleiches gilt für Zeile 72 bei `(?:Em|M)`).
- **Lösungsvorschlag für `speech.py`:**
  Ergänzung von `flags=re.I`:
  ```python
  s = re.sub(r"\b(?:Er|R)\s+(\d+(?:\.\d+)?)\b", r"R\1", s, flags=re.I)
  s = re.sub(r"\b(?:Em|M)\s*(\d+(?:\.\d+)?)\b", r"M\1", s, flags=re.I)
  ```

#### Fall 18: STT-Homophonverwechslung „Rz“ statt „R“
- **Gehört (`heard`):** `Kante verrunden mit Rz vier`
- **Erwartet (`expected`):** `Kante verrunden mit R4`
- **Ist-Zustand heute:** `Kante verrunden mit Rz 4`
- **Code-Ursache in `speech.py`:**
  Laut Glossar `docs/research/2026-10-28-abgleich-baugruppe-glossar.md` (Zeile 144 und 195) ist die akustische Fehlinterpretation von „Er zwei“ / „R2“ als Oberflächen-Rautiefe „Rz 2“ ein dokumentierter ASR-Standardfehler. `speech.py` besitzt hierfür noch keine Ersetzungsregel in `TERMS`.
- **Lösungsvorschlag für `speech.py`:**
  In `_units()` oder `TERMS` vor `(?:Er|R)`:
  ```python
  s = re.sub(r"\b(?:Rz|RZ)\s*(\d+(?:\.\d+)?)\b", r"R\1", s)
  ```
  (Da Rauheitsangaben im Modellierungskontext für Kantenverrundungen nicht vorkommen, ist die Ersetzung im Kontext von Verrundungsbefehlen eindeutig).

---

### 3.4 Kategorie Gewinde und Bohrungen

#### Fall 23: Durchmesser-Symbol (Ø)
- **Gehört (`heard`):** `Bohrung Durchmesser acht Millimeter`
- **Erwartet (`expected`):** `Bohrung Ø8 mm`
- **Ist-Zustand heute:** `Bohrung Durchmesser 8 mm`
- **Code-Ursache in `speech.py`:**
  Das Wort `Durchmesser` wird heute nicht verkürzt. In technischen Zeichnungen und CAD-Prompts ist das normgerechte Zeichen `Ø` (bzw. `Ø8`) kompakter und vermeidet Mehrdeutigkeiten bei Parameterabfragen.
- **Lösungsvorschlag für `speech.py`:**
  Ergänzung in `_units()`:
  ```python
  s = re.sub(r"\bDurchmesser\s*(\d+(?:\.\d+)?)\b", r"Ø\1", s, flags=re.I)
  ```

#### Fall 24: Umgangssprachliches „Durchgangsloch“
- **Gehört (`heard`):** `ein Durchgangsloch fünf Millimeter`
- **Erwartet (`expected`):** `eine Durchgangsbohrung 5 mm`
- **Ist-Zustand heute:** `ein Durchgangsloch 5 mm`
- **Code-Ursache in `TERMS`:**
  `TERMS` normalisiert zwar `Senkbohrung` → `Senkung` und `Klangloch` → `Langloch`, führt aber für das umgangssprachliche `Durchgangsloch` (Werkstattjargon) keine Überführung auf die Inventor-/Mechvane-Fachbezeichnung `Durchgangsbohrung` (Clearance Hole, Glossar Nr. 47) durch.
- **Lösungsvorschlag für `speech.py`:**
  Aufnahme in `TERMS`:
  ```python
  (r"\b(?:ein\s+)?Durchgangsloch\b", "eine Durchgangsbohrung")
  ```

---

### 3.5 Kategorie Bewegen/Ändern

#### Fall 30: Bruchzahl bei Feinverschiebung („einhalb“)
- **Gehört (`heard`):** `um einhalb Millimeter nach rechts`
- **Erwartet (`expected`):** `um 0.5 mm nach rechts`
- **Ist-Zustand heute:** `um einhalb mm nach rechts`
- **Code-Ursache in `_number()`:**
  Wie in Fall 6 wird das isolierte Bruchwort `einhalb` von `_number()` nicht in die Ziffer `0.5` aufgelöst.
- **Lösungsvorschlag für `speech.py`:**
  Mit der oben vorgeschlagenen `FRACTIONS`-Tabelle in `_numbers()` wird `einhalb mm` automatisch zu `0.5 mm`.

---

### 3.6 Kategorie Modellnamen

#### Fall 35: Modellnamen mit Ziffern („Hole1“)
- **Gehört (`heard`):** `hole eins zwei Millimeter nach links` mit `names=["Hole1"]`
- **Erwartet (`expected`):** `Hole1 2 mm nach links`
- **Ist-Zustand heute:** `hole 1 2 mm nach links`
- **Code-Ursache in `_names()`:**
  In `_names()` (Zeilen 88–90) werden Spans mit Ziffern pauschal verworfen:
  ```python
  # numbers and units never belong to a name
  if any(re.search(r"\d|^(mm|cm|°|×)$", w) for w in words[i:j]):
      continue
  ```
  Da `_numbers()` das gesprochene `"eins"` vor `_names()` bereits in `"1"` umgewandelt hat, enthält die Wortfolge `["hole", "1"]` eine Ziffer. Dadurch überspringt `_names()` diesen Span komplett und kann den Modellnamen `Hole1` (bzw. `Extrude2`, `Fillet1`) niemals zuordnen.
- **Lösungsvorschlag für `speech.py`:**
  Ziffern dürfen nur dann ausgeschlossen werden, wenn der resultierende String nicht exakt einem Schlüssel in `keys` entspricht:
  ```python
  cand = re.sub(r"[^0-9a-zäöüß]", "", "".join(words[i:j]).lower())
  if cand in keys:
      # Exakter Treffer auf Modellnamen erlaubt auch Ziffern
      best = (j, keys[cand])
      break
  if any(re.search(r"^(mm|cm|°|×)$", w) for w in words[i:j]):
      continue
  ```

---

### 3.7 Kategorie Unverändert (Vermeidung von Überkorrektur)

#### Fall 40: Kontextfreie Überkorrektur von „Phase“
- **Gehört (`heard`):** `in dieser Phase des Entwurfs nichts ändern`
- **Erwartet (`expected`):** `in dieser Phase des Entwurfs nichts ändern`
- **Ist-Zustand heute:** `in dieser Fase des Entwurfs nichts ändern`
- **Code-Ursache in `TERMS`:**
  In Zeile 22 ersetzt `TERMS` jedes Vorkommen des Wortes `Phase` oder `Phasen` ausnahmslos durch `Fase` bzw. `Fasen`:
  ```python
  (r"\bPhasen?\b", lambda m: "Fasen" if m.group(0).endswith("n") else "Fase"),
  ```
  In allgemeinsprachlichen Konstruktionssätzen (z. B. *„in dieser Phase des Projekts“*, *„frühe Phase“*) führt dies zu einer sinnentstellenden Überkorrektur.
- **Lösungsvorschlag für `speech.py`:**
  Die Ersetzung sollte an einen CAD-Kontext gekoppelt werden (z. B. vorausgehendes *„eine Phase“*, *„Fase an“*, oder nachfolgende Maßangabe wie *„1 mal 45 Grad“*), oder Signalwörter wie *„in dieser Phase“* bzw. *„Projektphase“* per Negative Lookbehind / Negative Lookahead ausschließen:
  ```python
  (r"(?<!in dieser\s)\bPhasen?\b(?!(\s+des\b))", lambda m: "Fasen" if m.group(0).endswith("n") else "Fase")
  ```

---

## 4. Testintegration und Validierung

Die Überprüfung der 40 Testsätze wurde in die bestehende Testsuite integriert:

1. **Testdaten:** `tests/mechvane/speech_cases.json` mit exakt 40 Einträgen, 7 Kategorien, `heard`, `expected`, `names`, `category`, `status` und `note`.
2. **Testfunktion:** `speech_cases_checks()` in `tests/mechvane/check.py`:
   - Lädt `speech_cases.json`.
   - Filtert alle Fälle mit `"status": "ok"` (29 Fälle) und prüft, ob `speech.normalize(heard, names) == expected`.
   - Zählt die Fälle mit `"status": "open"` (11 Fälle) und gibt das Verhältnis aus (`ok speech cases: 29 ok (11 open, 40 total)`).
   - Schlägt fehl, falls ein `ok`-Fall divergiert oder die Gesamtzahl ungleich 40 ist.
3. **Gesamttestlauf:** `python3 tests/mechvane/check.py` läuft mit **0 Fehlern** durch.
