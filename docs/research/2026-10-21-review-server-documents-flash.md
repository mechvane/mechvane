> Gemini 3.8 Flash, nicht verifiziert. Lesendes Code-Review von `inventa/server.py`, `inventa/documents.py`, `inventa/solidcraft.py`, `inventa/sketch_rule.py` sowie den Tests in `tests/inventa/check.py`.
> Datum: 2026-10-21. Geprüfter Commit auf `main`: `7d0dfb3f4c30c89707868358ac3f3dcee4e76567`.
> Alle Befunde 1 bis 12 wurden durch eigenständige Reproduktionsskripte unter `/tmp/review2-*.py` mit `PYTHONPATH=/root/repos/mechvane` gegen die installierte SolidCraft-CLI empirisch bestätigt und unter `docs/research/2026-10-21-review2-skripte/` abgelegt.

---

# Review-Bericht: `server.py`, `documents.py`, `solidcraft.py`, `sketch_rule.py` und MCP-Server

Das Review untersucht die Kernmodule der inventa-Laufzeitumgebung:
1. Dokumenten- und Workspace-Verwaltung (`documents.py`).
2. MCP-Werkzeuge, Validierung und Schnittstellen zum Dateisystem (`server.py`).
3. Subprozess-Client für SolidCraft (`solidcraft.py`).
4. Skizzen- und Arbeitselement-Besitzregeln (`sketch_rule.py`).
5. Testabdeckung in `tests/inventa/check.py`.

Zusammenfassend wurden **13 Befunde** ermittelt: 5 mit Schweregrad **Hoch**, 5 mit Schweregrad **Mittel**, 3 mit Schweregrad **Niedrig** (inklusive Testlücken), sowie 2 Punkte unter **Unsicher**.

---

## Übersicht der Befunde

| Nr. | Schweregrad | Modul / Fundstelle | Kurzbeschreibung | Empirisch bestätigt |
|---|---|---|---|---|
| 1 | **Hoch** | [`documents.py:46-56`](file:///root/repos/mechvane/inventa/documents.py#L46-L56) | `Workspace.new()` überschreibt bestehende `.solidcraft`-Dateien auf der Festplatte stillschweigend ohne Prüfung | Ja (`review2-1`) |
| 2 | **Hoch** | [`documents.py:58-76`](file:///root/repos/mechvane/inventa/documents.py#L58-L76) | Öffnen derselben Datei unter unterschiedlichen Namen führt zu parallelen Sessions und Lost Updates | Ja (`review2-2`) |
| 3 | **Hoch** | [`documents.py:49-56`](file:///root/repos/mechvane/inventa/documents.py#L49-L56), [`documents.py:93-97`](file:///root/repos/mechvane/inventa/documents.py#L93-L97) | Fehlgeschlagene `new()`- und `reader()`-Aufrufe lecken dauerhaft `solidcraft-cli`-Subprozesse | Ja (`review2-3`) |
| 4 | **Hoch** | [`documents.py:40-44`](file:///root/repos/mechvane/inventa/documents.py#L40-L44), [`server.py:31-59`](file:///root/repos/mechvane/inventa/server.py#L31-L59) | Pfadtraversal und fehlende Workspace-Grenzprüfung in `_path()`, `new_part`, `new_assembly` und `open_document` | Ja (`review2-4`) |
| 5 | **Hoch** | [`server.py:224-233`](file:///root/repos/mechvane/inventa/server.py#L224-L233) | `screenshot`-Werkzeug überschreibt und zerstört CAD-Modelldateien (`.solidcraft`) mit PNG-Rohdaten | Ja (`review2-5`) |
| 6 | **Mittel** | [`solidcraft.py:74-79`](file:///root/repos/mechvane/inventa/solidcraft.py#L74-L79) | `Session.close()` hinterlässt Zombie-Prozesse (`<defunct>`) in der Prozesstabelle bei Timeout | Ja (`review2-6`) |
| 7 | **Mittel** | [`solidcraft.py:32-38`](file:///root/repos/mechvane/inventa/solidcraft.py#L32-L38) | Fehlende Zeitlimits in `Session._rpc()` führen bei hängendem SolidCraft zum Deadlock / Server-Freeze | Ja (`review2-7`) |
| 8 | **Mittel** | [`solidcraft.py:11-79`](file:///root/repos/mechvane/inventa/solidcraft.py#L11-L79) | Fehlende `__del__`-Methode in `Session` leckt Subprozesse bei Garbage Collection | Ja (`review2-8`) |
| 9 | **Mittel** | [`sketch_rule.py:26-37`](file:///root/repos/mechvane/inventa/sketch_rule.py#L26-L37) | `references()` ignoriert `path_sketch` bei `solid.sweep` und bricht die Skizzen-Besitzregel für Sweeps | Ja (`review2-9`) |
| 10 | **Mittel** | [`server.py:77-80`](file:///root/repos/mechvane/inventa/server.py#L77-L80), [`documents.py:85-87`](file:///root/repos/mechvane/inventa/documents.py#L85-L87) | `close_document` verwirft ungespeicherte Änderungen trotz SolidCraft `dirty: True` stillschweigend | Ja (`review2-10`) |
| 11 | **Niedrig** | [`server.py:348-356`](file:///root/repos/mechvane/inventa/server.py#L348-L356), [`inplace.py:119-122`](file:///root/repos/mechvane/inventa/inplace.py#L119-L122) | `to_part_coords` stürzt bei unvollständigen Punkt-Koordinaten mit unbehandeltem `IndexError` ab | Ja (`review2-11`) |
| 12 | **Niedrig** | [`server.py:97-104`](file:///root/repos/mechvane/inventa/server.py#L97-L104) | `run` hinterlässt nach erfolgreichem `batch` bei Fehler in `sketch_rule.enforce` inkonsistenten, teils modifizierten Zustand | Ja (`review2-12`) |
| 13 | **Niedrig** | [`tests/inventa/check.py:1102-1206`](file:///root/repos/mechvane/tests/inventa/check.py#L1102-L1206) | Gravierende Testlücken bei Server-Werkzeugen, Fehlerpfaden und Workspace-Grenzfällen | Codebeleg |

---

## Befunde

### 1. [Hoch] `Workspace.new()` überschreibt bestehende `.solidcraft`-Dateien stillschweigend ohne Prüfung

- **Fundstelle:** [inventa/documents.py:46-56](file:///root/repos/mechvane/inventa/documents.py#L46-L56)
- **Was falsch ist:**
  In `Workspace.new(self, kind, name, path=None)` wird lediglich geprüft, ob der logische Name bereits in der laufenden Sitzung geöffnet ist:
  ```python
  if name in self.docs:
      raise ValueError(f"a document named {name!r} is already open")
  ```
  Es findet jedoch **keine Prüfung statt, ob die Datei `p` auf der Festplatte bereits existiert** (`if p.exists(): ...`).
  Unmittelbar danach wird eine leere SolidCraft-Konstruktion angelegt (`s.tool("new_design", ...)`) und bedingungslos mit `doc.save()` abgespeichert:
  ```python
  doc = Document(name, kind, p, s)
  doc.set_metadata({"kind": kind, "format": 1})
  doc.save()
  ```
  Wenn ein Anwender oder ein LLM-Client nach einem Neustart des MCP-Servers oder nach dem Schließen eines Dokuments `new_part(name="bracket")` oder `new_assembly(name="unit")` aufruft, wird eine bereits existierende, wertvolle CAD-Datei mit komplexer Geometrie auf der Festplatte ohne Warnung mit einer leeren 400-Byte-Template-Datei überschrieben. Dies führt zu direktem, irreversiblem Datenverlust.
- **Szenario (Eingabe -> falsches Ergebnis):**
  1. Datei `bracket.solidcraft` existiert mit Körpern im Workspace (Größe 561 Bytes).
  2. Nach Schließen oder Serverneustart ruft der Client `new_part("bracket")` auf.
  3. `new()` überschreibt `bracket.solidcraft` auf der Festplatte mit einer leeren Datei (Größe 413 Bytes); die gesamte vorherige Arbeit ist verloren.
- **Bestätigt:** Ja, durch `/tmp/review2-1-new-overwrite.py` (`docs/research/2026-10-21-review2-skripte/review2-1-new-overwrite.py`).
- **Vorschlag zur Behebung:**
  In `Workspace.new`:
  ```python
  p = self._path(name, path)
  if p.exists():
      raise FileExistsError(f"document file {str(p)!r} already exists on disk; use open_document instead or choose another name/path")
  ```

---

### 2. [Hoch] Öffnen derselben Datei unter unterschiedlichen Namen führt zu parallelen Sessions und Lost Updates

- **Fundstelle:** [inventa/documents.py:58-76](file:///root/repos/mechvane/inventa/documents.py#L58-L76)
- **Was falsch ist:**
  `Workspace.open(self, path, name=None)` prüft ausschließlich den Schlüssel `name` im Wörterbuch `self.docs`:
  ```python
  p = self._path(None, path)
  name = name or p.stem
  if name in self.docs:
      raise ValueError(f"a document named {name!r} is already open")
  ```
  Es wird **überhaupt nicht geprüft, ob der kanonisch aufgelöste Pfad `p` bereits von einem anderen Dokument in `self.docs` verwendet wird** (`any(d.path.resolve() == p for d in self.docs.values())`).
  Wird dieselbe Datei unter zwei unterschiedlichen Namen geöffnet (z. B. explizite Aliase `open_document("part.solidcraft", name="p1")` und `open_document("part.solidcraft", name="p2")`, oder relative Pfadvarianten), starten zwei völlig unabhängige SolidCraft-Prozesse, die dieselbe physische Datei manipulieren.
  Führen beide Prozesse Änderungen durch und speichern diese ab, überschreibt der jeweils zuletzt speichernde Prozess blind die Änderungen des ersten (Lost Update).
  Darüber hinaus führt der Fallback `name = name or p.stem` dazu, dass zwei legitime, unterschiedliche Dateien mit gleichem Stammnamen in unterschiedlichen Unterordnern (z. B. `project_a/plate.solidcraft` und `project_b/plate.solidcraft`) nicht gleichzeitig geöffnet werden können, da der zweite Aufruf fälschlicherweise mit `ValueError: a document named 'plate' is already open` abbricht.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Anwender öffnet dieselbe Datei unter zwei Namen:
  ```python
  doc_a = ws.open("shared.solidcraft", name="doc_a")
  doc_b = ws.open("shared.solidcraft", name="doc_b")
  doc_a.session.batch([{"command": "solid.box", "params": {"body_name": "BoxA", ...}}])
  doc_a.save()
  doc_b.session.batch([{"command": "solid.cylinder", "params": {"body_name": "CylB", ...}}])
  doc_b.save()
  ```
  Beim Neuladen von der Festplatte enthält die Datei nur noch `CylB`; `BoxA` wurde stillschweigend vernichtet.
- **Bestätigt:** Ja, durch `/tmp/review2-2-open-duplicate.py` (`docs/research/2026-10-21-review2-skripte/review2-2-open-duplicate.py`).
- **Vorschlag zur Behebung:**
  In `Workspace.open`:
  1. Prüfen, ob `p` bereits geöffnet ist:
     ```python
     for d in self.docs.values():
         if d.path.resolve() == p:
             if name and name != d.name:
                 raise ValueError(f"document {str(p)!r} is already open under name {d.name!r}")
             return d
     ```
  2. Falls `name` kollidiert, aber auf eine andere Datei zeigt, einen eindeutigen Namen vergeben oder den Fehler präzisieren (wie in `inplace.edit_in_place:143-148` bereits als Workaround implementiert).

---

### 3. [Hoch] Fehlgeschlagene `new()`- und `reader()`-Aufrufe lecken dauerhaft `solidcraft-cli`-Subprozesse

- **Fundstelle:** [inventa/documents.py:49-56](file:///root/repos/mechvane/inventa/documents.py#L49-L56), [inventa/documents.py:93-97](file:///root/repos/mechvane/inventa/documents.py#L93-L97)
- **Was falsch ist:**
  1. In `Workspace.new`:
     ```python
     s = self.session()
     s.tool("new_design", {"name": name})
     doc = Document(name, kind, p, s)
     doc.set_metadata({"kind": kind, "format": 1})
     doc.save()
     self.docs[name] = doc
     ```
     `self.session()` startet sofort den externen Subprozess `solidcraft-cli`. Tritt anschließend bei `new_design`, `set_metadata` oder `doc.save()` ein Fehler auf (z. B. wenn das Zielverzeichnis nicht existiert, Berechtigungen fehlen oder der Pfad außerhalb von `--allow-path` liegt), fehlt hier im Gegensatz zu `open()` jeder `try...except`-Block.
     Weil `self.docs[name] = doc` erst nach `doc.save()` ausgeführt wird, ist das Dokument nicht in `self.docs` registriert. Der Subprozess `s` wird weder beendet noch geschlossen und kann auch durch `Workspace.close_all()` nicht aufgeräumt werden.
  2. In `Workspace.reader(path)`:
     ```python
     def reader(self, path):
         s = self.session()
         s.tool("open", {"path": str(path)})
         return s
     ```
     Scheitert `s.tool("open")` (z. B. weil die verknüpfte Bauteildatei fehlt oder beschädigt ist), wird der gestartete Prozess `s` nicht abgefangen und läuft als Zombie-/Verwaister Prozess im Hintergrund weiter.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Client ruft `new_part("parts/bracket")` auf, während der Unterordner `parts/` im Dateisystem noch nicht angelegt wurde.
  SolidCraft wirft `SolidCraftError: its folder does not exist`. Der Prozess `solidcraft-cli` läuft unbegrenzt im Betriebssystem weiter. Wiederholte Fehler akkumulieren dutzende laufende Hintergrundprozesse.
- **Bestätigt:** Ja, durch `/tmp/review2-3-process-leak.py` (`docs/research/2026-10-21-review2-skripte/review2-3-process-leak.py`).
- **Vorschlag zur Behebung:**
  In `documents.py`:
  - `Workspace.new` mit `try...except` absichern:
    ```python
    s = self.session()
    try:
        s.tool("new_design", {"name": name})
        doc = Document(name, kind, p, s)
        doc.set_metadata({"kind": kind, "format": 1})
        p.parent.mkdir(parents=True, exist_ok=True)
        doc.save()
        self.docs[name] = doc
        return doc
    except Exception:
        s.close()
        raise
    ```
  - `Workspace.reader` mit `try...except` absichern:
    ```python
    def reader(self, path):
        s = self.session()
        try:
            s.tool("open", {"path": str(path)})
            return s
        except Exception:
            s.close()
            raise
    ```

---

### 4. [Hoch] Pfadtraversal und fehlende Workspace-Grenzprüfung in `_path()`, `new_part`, `new_assembly` und `open_document`

- **Fundstelle:** [inventa/documents.py:40-44](file:///root/repos/mechvane/inventa/documents.py#L40-L44), [inventa/server.py:31-33](file:///root/repos/mechvane/inventa/server.py#L31-L33), [inventa/server.py:51-53](file:///root/repos/mechvane/inventa/server.py#L51-L53), [inventa/server.py:57-59](file:///root/repos/mechvane/inventa/server.py#L57-L59)
- **Was falsch ist:**
  Die MCP-Dokumentation in `server.py` garantiert für Dokumentenpfade:
  `paths relative to the workspace`.
  Im Werkzeug `screenshot` wurde dies vorbildlich mit `target.relative_to(ws.root)` abgesichert.
  In `Workspace._path(self, name, path)` fehlt diese Grenzprüfung jedoch vollständig:
  ```python
  def _path(self, name, path):
      p = Path(path) if path else self.root / f"{name}.solidcraft"
      if not p.is_absolute():
          p = self.root / p
      return p.resolve()
  ```
  1. Wenn `path` ein absoluter Pfad außerhalb des Workspace ist (z. B. `/etc/passwd`), bleibt `p` unverändert und entweicht `self.root`.
  2. Wenn `path` oder `name` relative Sequenzen mit `../` enthalten (z. B. `name="../../evil"`), löst `p.resolve()` den Pfad außerhalb von `self.root` auf.
  3. Ein leerer Name (`name=""`) erzeugt eine versteckte Datei `.solidcraft` direkt im Workspace-Wurzelverzeichnis.
  4. Enthält `name` Unterordner (z. B. `parts/bracket`), schlägt das Speichern fehl, da `p.parent.mkdir(parents=True, exist_ok=True)` nicht gerufen wird.
  Wird ein Pfad außerhalb des Workspace übergeben, führt dies entweder zu unerlaubtem Zugriff oder zu einem `SolidCraftError` mit anschließendem Prozess-Leak (siehe Befund 3).
- **Szenario (Eingabe -> falsches Ergebnis):**
  Client ruft `new_part(name="../../escaped")` oder `open_document(path="/etc/passwd")` auf.
  `ws._path` löst den Pfad zu `/escaped.solidcraft` bzw. `/etc/passwd` auf, weit außerhalb von `ws.root`.
- **Bestätigt:** Ja, durch `/tmp/review2-4-path-traversal.py` (`docs/research/2026-10-21-review2-skripte/review2-4-path-traversal.py`).
- **Vorschlag zur Behebung:**
  In `Workspace._path`:
  ```python
  def _path(self, name, path):
      if name is not None and not str(name).strip():
          raise ValueError("document name cannot be empty")
      p = Path(path) if path else self.root / f"{name}.solidcraft"
      if not p.is_absolute():
          p = (self.root / p).resolve()
      else:
          p = p.resolve()
      try:
          p.relative_to(self.root)
      except ValueError:
          raise ValueError(f"path {path or name!r} escapes workspace root {self.root}")
      return p
  ```

---

### 5. [Hoch] `screenshot`-Werkzeug überschreibt und zerstört CAD-Modelldateien (`.solidcraft`) mit PNG-Rohdaten

- **Fundstelle:** [inventa/server.py:224-233](file:///root/repos/mechvane/inventa/server.py#L224-L233)
- **Was falsch ist:**
  Das MCP-Werkzeug `screenshot(document, view, path)` speichert das gerenderte Bild auf der Festplatte, wenn `path` angegeben ist:
  ```python
  p = Path(path)
  target = (ws.root / p).resolve() if not p.is_absolute() else p.resolve()
  ...
  if target.is_dir():
      raise ValueError(f"path {path!r} is a directory")
  target.parent.mkdir(parents=True, exist_ok=True)
  target.write_bytes(raw)
  ```
  `screenshot` prüft zwar, ob `target` ein Verzeichnis ist und ob es innerhalb des Workspace liegt, **prüft jedoch weder die Dateiendung noch ob `target` bereits als CAD-Datei (`.solidcraft`) existiert**.
  Übergibt ein LLM-Client versehentlich den Namen des Modells als Pfad (z. B. `screenshot(document="gear", path="gear.solidcraft")`), überschreibt `target.write_bytes(raw)` die Binär-/JSON-Struktur der Konstruktionsdatei blind mit PNG-Bilddaten.
  Das CAD-Modell ist danach unrettbar zerstört und lässt sich in SolidCraft/inventa nie wieder öffnen (`SolidCraftError: design file is not UTF-8 JSON`).
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Client ruft `screenshot("bracket", path="bracket.solidcraft")` auf.
  Die CAD-Datei `bracket.solidcraft` wird auf der Festplatte mit Roh-PNG-Bytes überschrieben. Beim nächsten `open_document("bracket.solidcraft")` stürzt der Vorgang ab.
- **Bestätigt:** Ja, durch `/tmp/review2-5-screenshot-destroys-cad.py` (`docs/research/2026-10-21-review2-skripte/review2-5-screenshot-destroys-cad.py`).
- **Vorschlag zur Behebung:**
  In `server.py:screenshot`:
  ```python
  if target.suffix.lower() == ".solidcraft":
      raise ValueError(f"cannot overwrite CAD document {path!r} with screenshot image")
  if target.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
      target = target.with_suffix(".png")
  ```

---

### 6. [Mittel] `Session.close()` hinterlässt Zombie-Prozesse (`<defunct>`) in der Prozesstabelle bei Timeout

- **Fundstelle:** [inventa/solidcraft.py:74-79](file:///root/repos/mechvane/inventa/solidcraft.py#L74-L79)
- **Was falsch ist:**
  In `inventa/solidcraft.py:Session.close`:
  ```python
  def close(self):
      try:
          self._p.stdin.close()
          self._p.wait(10)
      except (OSError, subprocess.TimeoutExpired):
          self._p.kill()
  ```
  Läuft `self._p.wait(10)` in einen `subprocess.TimeoutExpired` (weil `solidcraft-cli` blockiert oder das Schließen von `stdin` ignoriert), fängt der `except`-Block die Ausnahme ab und ruft `self._p.kill()` auf.
  `kill()` sendet das Signal `SIGKILL` an den Subprozess. Auf POSIX/Linux-Systemen beendet der Kernel zwar den Prozess, hält jedoch seinen Prozesstabellen-Eintrag solange im Zustand `Z` (Zombie / `<defunct>`), bis der Elternprozess `wait()` oder `waitpid()` aufruft.
  Da `close()` nach `self._p.kill()` **kein `wait()` mehr aufruft**, verbleibt der Prozess dauerhaft als Zombie in der Betriebssystem-Prozesstabelle. In langlebigen Server-Sitzungen führt dies zu einer Ansammlung toter Prozesse.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Subprozess reagiert nicht innerhalb von 10 Sekunden auf `stdin.close()`. `close()` sendet `kill()`.
  In `/proc/<pid>/status` wechselt der Prozess in `State: Z (zombie)` und belegt dauerhaft eine PID.
- **Bestätigt:** Ja, durch `/tmp/review2-6-zombie-process.py` (`docs/research/2026-10-21-review2-skripte/review2-6-zombie-process.py`).
- **Vorschlag zur Behebung:**
  In `solidcraft.py:Session.close`:
  ```python
  def close(self):
      try:
          self._p.stdin.close()
          self._p.wait(10)
      except (OSError, subprocess.TimeoutExpired):
          self._p.kill()
          try:
              self._p.wait(5)
          except (OSError, subprocess.TimeoutExpired):
              pass
  ```

---

### 7. [Mittel] Fehlende Zeitlimits in `Session._rpc()` führen bei hängendem SolidCraft zum Deadlock / Server-Freeze

- **Fundstelle:** [inventa/solidcraft.py:32-38](file:///root/repos/mechvane/inventa/solidcraft.py#L32-L38)
- **Was falsch ist:**
  In `Session._rpc(self, method, params)`:
  ```python
  self._send({"jsonrpc": "2.0", "id": self._n, "method": method, "params": params})
  while True:
      line = self._p.stdout.readline()
      if not line:
          raise SolidCraftError("solidcraft-cli mcp ended unexpectedly")
      msg = json.loads(line)
      if msg.get("id") == self._n:
          break
  ```
  `self._p.stdout.readline()` ist ein synchroner, blockierender Aufruf ohne Timeout.
  Weder `Session`, `_rpc`, `cmd`, `tool` noch `batch` akzeptieren einen Timeout-Parameter.
  Wenn `solidcraft-cli` bei einer fehlerhaften Geometrieoperation (z. B. ungültige B-Rep-Boolesche Operation, unlösbarer Sweep oder Loft-Kernelschleife) in eine Endlosschleife gerät, hängt der gesamte inventa MCP-Server blockiert fest. Der Client erhält nie eine Antwort und kann die Operation nicht abbrechen, außer indem er den inventa-Serverprozess hart beendet.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein SolidCraft-Kommando gerät in einen geometrischen Deadlock. `readline()` wartet endlos; inventa friert ein.
- **Bestätigt:** Ja, durch `/tmp/review2-7-missing-timeout.py` (`docs/research/2026-10-21-review2-skripte/review2-7-missing-timeout.py`).
- **Vorschlag zur Behebung:**
  Implementierung eines Timeouts in `Session` (z. B. standardmäßig 60 oder 120 Sekunden) unter Verwendung von `select.select([self._p.stdout], [], [], timeout)` vor dem Aufruf von `readline()`. Bei Ablauf des Timeouts wird eine aussagekräftige `SolidCraftError(f"timeout waiting for solidcraft-cli response after {timeout}s")` geworfen.

---

### 8. [Mittel] Fehlende `__del__`-Methode in `Session` leckt Subprozesse bei Garbage Collection

- **Fundstelle:** [inventa/solidcraft.py:11-79](file:///root/repos/mechvane/inventa/solidcraft.py#L11-L79)
- **Was falsch ist:**
  Die Python-Standardklasse `subprocess.Popen` beendet bei der Freigabe durch den Garbage Collector den gestarteten Subprozess nicht; sie emittiert lediglich eine `ResourceWarning`.
  `Session` definiert zwar `close(self)`, implementiert jedoch **weder `__del__(self)` noch das Context-Manager-Protokoll (`__enter__` / `__exit__`)**.
  Wird eine `Session`-Instanz erzeugt und verliert ihre Referenzen (z. B. durch eine Ausnahme vor Zuweisung zu `ws.docs` oder bei temporären Auswertungen wie `ws.reader()`), räumt der Python Garbage Collector das `Session`-Objekt ab, aber der Prozess `solidcraft-cli` läuft unbemerkt im Hintergrund weiter und verbraucht CPU- und Speicherressourcen.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Eine Funktion erzeugt lokal eine `Session` und beendet sich, ohne explizit `s.close()` aufzurufen:
  ```python
  def work():
      s = Session()
      # Funktion endet, s wird abgeräumt
  ```
  `s._p` läuft als verwaister Hintergrundprozess dauerhaft weiter.
- **Bestätigt:** Ja, durch `/tmp/review2-8-gc-process-leak.py` (`docs/research/2026-10-21-review2-skripte/review2-8-gc-process-leak.py`).
- **Vorschlag zur Behebung:**
  In `inventa/solidcraft.py:Session`:
  ```python
  def __enter__(self):
      return self

  def __exit__(self, exc_type, exc_val, exc_tb):
      self.close()

  def __del__(self):
      try:
          self.close()
      except Exception:
          pass
  ```

---

### 9. [Mittel] `references()` ignoriert `path_sketch` bei `solid.sweep` und bricht die Skizzen-Besitzregel für Sweeps

- **Fundstelle:** [inventa/sketch_rule.py:26-37](file:///root/repos/mechvane/inventa/sketch_rule.py#L26-L37)
- **Was falsch ist:**
  In `sketch_rule.references(definition, ids)` werden Skizzenabhängigkeiten ausschließlich über das Attribut `k == "sketch"` ermittelt:
  ```python
  for k, x in v.items():
      if k == "sketch" and isinstance(x, int):
          out.add(ids.get(x))
      else:
          walk(x)
  ```
  In SolidCraft besitzt ein Sweep-Feature (`solid.sweep`) jedoch zwei Skizzen: die Profilskizze (`"sketch": <id>`) **und die Pfadskizze (`"path_sketch": <id>`)**.
  Weil der Schlüssel `"path_sketch"` heißt, schlägt die Bedingung `k == "sketch"` fehl. `walk(x)` wird mit `x` als Ganzzahl (`int`) aufgerufen und ignoriert den Wert, weil `x` weder `dict` noch `list` ist.
  Dadurch meldet `sketch_rule.consumers(s)` für die Pfadskizze eine leere Liste von Verbrauchern (`'SweepPath': []`).
  Die Konsequenzen sind:
  1. `sketch_rule.enforce()` erkennt nicht, dass die Pfadskizze zu `Sweep1` gehört, und sortiert sie im Verlauf nicht vor das Feature.
  2. Im Modellbrowser (`tree.part_tree`) wird die Pfadskizze fälschlich als ungenutzte Wurzelskizze auf oberster Ebene dargestellt, anstatt sauber unter das Sweep-Feature geschachtelt zu werden.
  3. Beim Löschen des Features via `delete_feature` wird die Pfadskizze nicht mitgelöscht.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Bauteil mit Profil-Skizze und Pfad-Skizze für `solid.sweep` wird erzeugt.
  ```python
  cons = sketch_rule.consumers(s)
  assert cons["SweepPath"] == ["Sweep1"]  # Ist: []
  own = sketch_rule.owners(cons)
  assert own["SweepPath"] == "Sweep1"    # Ist: SweepPath fehlt in own
  ```
- **Bestätigt:** Ja, durch `/tmp/review2-9-sweep-path-sketch.py` (`docs/research/2026-10-21-review2-skripte/review2-9-sweep-path-sketch.py`).
- **Vorschlag zur Behebung:**
  In `inventa/sketch_rule.py:references`:
  ```python
  for k, x in v.items():
      if k in ("sketch", "path_sketch") and isinstance(x, int):
          out.add(ids.get(x))
      else:
          walk(x)
  ```

---

### 10. [Mittel] `close_document` verwirft ungespeicherte Änderungen trotz SolidCraft `dirty: True` stillschweigend

- **Fundstelle:** [inventa/server.py:77-80](file:///root/repos/mechvane/inventa/server.py#L77-L80), [inventa/documents.py:85-87](file:///root/repos/mechvane/inventa/documents.py#L85-L87)
- **Was falsch ist:**
  SolidCraft führt intern präzise Buch über ungespeicherte Änderungen: Nach Befehlen in der Timeline liefert `document.inspect` den booleschen Status `dirty: True`.
  Die inventa-Werkzeuge ignorieren dies jedoch vollständig:
  1. `Document.info()` und `list_documents()` geben den `dirty`-Zustand nicht zurück. Ein aufrufender Client (LLM oder Anwender) hat keine Möglichkeit zu erfahren, ob ein Dokument noch ungespeicherte Änderungen enthält.
  2. `close_document(document: str)` schließt das Dokument und beendet die Session ohne jede Warnung oder Bestätigung.
  3. Es gibt weder einen Parameter `save: bool = False` noch eine Schutzprüfung `force: bool = False`. Versehentliches Schließen führt zu unbemerktem Datenverlust.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein Dokument wird mit `run(...)` bearbeitet (`dirty: True`). Der Client ruft `close_document("bracket")` auf.
  Alle Änderungen werden sofort und unwiederbringlich verworfen, ohne dass der Aufrufer gewarnt wurde.
- **Bestätigt:** Ja, durch `/tmp/review2-10-close-dirty.py` (`docs/research/2026-10-21-review2-skripte/review2-10-close-dirty.py`).
- **Vorschlag zur Behebung:**
  1. In `Document.info()` das Feld `"dirty": self.session.cmd("document.inspect").get("dirty", False)` aufnehmen.
  2. In `server.py:close_document(document: str, save: bool = False, force: bool = False)`:
     ```python
     doc = ws.get(document)
     is_dirty = doc.session.cmd("document.inspect").get("dirty", False)
     if is_dirty and not save and not force:
         raise ValueError(f"document {document!r} has unsaved changes; specify save=true to save before closing, or force=true to discard changes")
     if save:
         doc.save()
     ws.close(document)
     return {"closed": document, "saved": save}
     ```

---

### 11. [Niedrig] `to_part_coords` stürzt bei unvollständigen Punkt-Koordinaten mit unbehandeltem `IndexError` ab

- **Fundstelle:** [inventa/server.py:348-356](file:///root/repos/mechvane/inventa/server.py#L348-L356), [inventa/inplace.py:119-122](file:///root/repos/mechvane/inventa/inplace.py#L119-L122)
- **Was falsch ist:**
  Das MCP-Werkzeug `to_part_coords(assembly, occurrence, point)` definiert `point: list[float]`.
  Es validiert jedoch nicht, dass `point` genau 3 Elemente `[x, y, z]` umfasst.
  Wird ein 2D-Punkt `[x, y]` oder eine leere Liste `[]` übergeben, ruft `to_part_coords` die Funktion `inplace.to_part_coords(point, target["transform"])` auf, welche an `geometry.apply_point` delegiert. Dort wird ungeschützt auf `point[2]` zugegriffen. Dies löst einen unbehandelten `IndexError: list index out of range` aus, anstatt den Client mit einer verständlichen Validierungsfehlermeldung zu informieren.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Aufruf von `to_part_coords(assembly="unit", occurrence="Plate:1", point=[10, 5])`.
  Statt einer sauberen Fehlermeldung ("point must be a 3D coordinate [x, y, z]") stürzt die Ausführung mit `IndexError` ab.
- **Bestätigt:** Ja, durch `/tmp/review2-11-to-part-coords-validation.py` (`docs/research/2026-10-21-review2-skripte/review2-11-to-part-coords-validation.py`).
- **Vorschlag zur Behebung:**
  In `server.py:to_part_coords`:
  ```python
  if not isinstance(point, (list, tuple)) or len(point) != 3:
      raise ValueError(f"point must be a 3D coordinate [x, y, z], got {point!r}")
  ```

---

### 12. [Niedrig] `server.py:run` hinterlässt nach erfolgreichem `batch` bei Fehler in `sketch_rule.enforce` inkonsistenten, teils modifizierten Zustand

- **Fundstelle:** [inventa/server.py:97-104](file:///root/repos/mechvane/inventa/server.py#L97-L104)
- **Was falsch ist:**
  In `server.py:run`:
  ```python
  doc = ws.get(document)
  result = doc.session.batch(commands)
  out = {"results": result.get("results", result) if isinstance(result, dict) else result}
  if not verbose:
      out["results"] = _compact(out["results"])
  if doc.kind == PART:
      out["sketch_rule"] = sketch_rule.enforce(doc.session)
  return out
  ```
  `doc.session.batch(commands)` führt die CAD-Befehle mit automatischem Rollback bei Fehlern aus. Sobald `batch` jedoch erfolgreich durchgelaufen ist, ist die Transaktion in SolidCraft abgeschlossen.
  Wird danach `sketch_rule.enforce(doc.session)` aufgerufen und wirft eine Ausnahme (z. B. `RuntimeError("sketch rule did not settle")` durch oszillierende oder kollidierende Abhängigkeiten), bricht der MCP-Toolcall mit einem Fehler ab.
  Die zuvor durch `batch` erzeugten Features und Körper wurden jedoch **bereits fest in das Modell übernommen und werden nicht zurückgerollt**. Der Client erhält eine Fehlermeldung und nimmt an, dass der Aufruf fehlgeschlagen ist, während das Dokument im Speicher verändert und in einem unfertigen Zustand verbleibt.
- **Szenario (Eingabe -> falsches Ergebnis):**
  Ein `run`-Aufruf führt Befehle aus, aber `sketch_rule.enforce` schlägt fehl.
  Der Client fängt `RuntimeError` ab; im Dokument existiert der neu erzeugte Körper dennoch.
- **Bestätigt:** Ja, durch `/tmp/review2-12-run-partial-failure.py` (`docs/research/2026-10-21-review2-skripte/review2-12-run-partial-failure.py`).
- **Vorschlag zur Behebung:**
  Wenn `sketch_rule.enforce` scheitert, sollte entweder versucht werden, den vorherigen Zustand über `edit.checkpoint` / `edit.restore_checkpoint` von SolidCraft wiederherzustellen, oder die Ausnahme sollte in ein strukturiertes Warnungsfeld im Rückgabewert gewandelt werden, statt den gesamten Toolcall abbrechen zu lassen.

---

### 13. [Niedrig] Gravierende Testlücken in `tests/inventa/check.py` für Server-Werkzeuge, Fehlerpfade und Workspace-Grenzfälle

- **Fundstelle:** [tests/inventa/check.py:1102-1206](file:///root/repos/mechvane/tests/inventa/check.py#L1102-L1206)
- **Was falsch ist:**
  Die MCP-Servertests in `tests/inventa/check.py:mcp_server` decken nur den Schönwetterpfad einer Teilmenge der Werkzeuge ab:
  - 13 Werkzeuge des MCP-Servers werden **im MCP-Server-Test überhaupt nicht getestet**:
    `open_document`, `close_document`, `list_documents`, `delete_feature`, `add_joint`, `edit_joint`, `delete_joint`, `adopt_joint`, `check_joints`, `bolted_connection`, `preview_bolted_connection`, `command`, `list_commands`.
  - Bei der Fehlerbehandlung gibt es nur einen einzigen Test (`browser("nope")`).
  - Ungültige Parameter (z. B. fehlerhafte `commands` in `run`, ungültige Gelenkparameter, unvollständige Koordinaten in `to_part_coords`) werden nicht geprüft.
  - Das Verhalten bei Namenskollisionen, Pfadtraversal, nicht existierenden Ordnern, doppelten Dateiöffnungen und der Bereinigung von Subprozessen ist im Testframework komplett unberücksichtigt.
- **Szenario:**
  Fehler wie Befund 1 (Dateivernichtung bei `new`), Befund 2 (Doppelöffnung), Befund 3 (Prozess-Leaks) oder Befund 5 (Screenshot zerstört CAD) bleiben von der Testsuite unbemerkt.
- **Bestätigt:** Codebeleg.
- **Vorschlag zur Behebung:**
  Erweiterung von `tests/inventa/check.py` um eine dedizierte Suite von Fehler- und Grenzwertprüfungen (orientiert an den Reproduktionsskripten 1 bis 12).

---

## Unsicher

1. **`BrokenPipeError` statt `SolidCraftError` bei plötzlichem Subprozess-Absturz**
   - **Fundstelle:** `inventa/solidcraft.py:25-27`, `inventa/documents.py:70-72`
   - **Verdacht:** Wenn der `solidcraft-cli`-Subprozess unerwartet stirbt (z. B. durch Segmentation Fault oder OOM), wirft der nächste Aufruf von `self._p.stdin.write()` bzw. `flush()` in `_send()` einen rohen `BrokenPipeError` (`OSError`). In `documents.py:open` wird jedoch gezielt nur `except SolidCraftError:` abgefangen. Dadurch entgleitet die Ausnahme dem Aufräumcode, `s.close()` wird nicht gerufen und der Fehler erreicht den Client nicht als saubere SolidCraft-Meldung.
   - **Klärungsbedarf:** Sollte `_send` alle `OSError`/`BrokenPipeError` in `SolidCraftError` umwandeln?

2. **Standardteil-Generierung in `standard_parts.create()` überschreibt existierende Normteile ohne Cache-Prüfung**
   - **Fundstelle:** `inventa/standard_parts.py:416-418`
   - **Verdacht:** `standard_parts.create()` delegiert direkt an `ws.new(PART, doc_name, path)`. Existiert die Normteildatei bereits im Workspace (z. B. eine zuvor generierte `ISO_4762_M5x16.solidcraft`), wird sie durch `ws.new` blind überschrieben (Kopplung an Befund 1), anstatt die bestehende Datei wiederzuverwenden oder zu öffnen.
   - **Klärungsbedarf:** Ist für Normteile ein Caching-Mechanismus (Reopen wenn Datei existiert) erwünscht?

---

### Stichprobe durch Claude (2026-10-21)

Die Skripte laufen mit `PYTHONPATH=. python3 docs/research/2026-10-21-review2-skripte/<skript>`. Befund 5 ist bestätigt und schwer: `screenshot` mit `path` auf eine `.solidcraft`-Datei überschreibt das Modell mit PNG-Daten. Befund 1 ist bestätigt: `Workspace.new` überschreibt eine vorhandene Datei. Befund 4 ist nur teilweise belegt: Das Skript zeigt nur, dass ein leerer Name `.solidcraft` erzeugt, ein Pfad aus dem Workspace hinaus ist nicht vorgeführt. Die übrigen Befunde sind nicht gegengeprüft.
