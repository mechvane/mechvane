# Bericht: Behebung der Server- und Dokumenten-Befunde (1 bis 13)

Datum: 2026-10-21  
Branch: `gemini/server-fixes`  
Basis: Review-Bericht `docs/research/2026-10-21-review-server-documents-flash.md`

---

## 1. Zusammenfassung

Alle 12 fachlichen Befunde aus dem Review-Bericht wurden analysiert, durch vorab fehlschlagende Regressionstests in `tests/inventa/check.py` abgesichert und mit minimalen, sauberen Eingriffen im bestehenden Code-Stil behoben. Befund 13 (Testlücken) wurde durch 24 neue gezielte Prüfungen vollständig geschlossen.

- **Testzahl vorher:** 129 Prüfungen in `tests/inventa/check.py`
- **Testzahl nachher:** 153 Prüfungen in `tests/inventa/check.py` (+24 Prüfungen, 0 failures)
- **Referenztests:** `python3 tests/reference/check.py` unverändert 100 % grün (0 failures)

---

## 2. Details je Befund (1 bis 12) sowie Befund 13

### Befund 1: `Workspace.new()` überschreibt bestehende `.solidcraft`-Dateien stillschweigend
- **Status:** Behoben.
- **Änderung:** In `Workspace.new(self, kind, name, path=None, overwrite=False)` wird nach der Pfadermittlung geprüft, ob `p.exists()`. Falls ja und `not overwrite`, wird ein `FileExistsError` ausgelöst (`"document file ... already exists on disk; use open or pass overwrite=True"`). Die MCP-Werkzeuge `new_part` und `new_assembly` erhielten den optionalen Parameter `overwrite: bool = False` und reichen diesen durch.
- **Dokumentation:** `docs/inventa-mcp.md` aktualisiert.

### Befund 2: Öffnen derselben Datei unter unterschiedlichen Namen führt zu parallelen Sessions
- **Status:** Behoben.
- **Änderung:** In `Workspace.open(self, path, name=None)` wird vor dem Start einer neuen SolidCraft-Sitzung geprüft, ob der aufgelöste Pfad `p` bereits in `self.docs` vorhanden ist (`doc.path.resolve() == p`). Ist dies der Fall und stimmt der Name überein oder wurde weggelassen, wird direkt das bestehende `Document`-Objekt zurückgegeben. Wird versucht, dieselbe Datei unter einem abweichenden Aliasnamen erneut zu öffnen, wird ein verständlicher `ValueError` geworfen (`"document ... is already open under name ..."`).
- **Dokumentation:** `docs/inventa-mcp.md` aktualisiert.

### Befund 3: Fehlgeschlagene `new()`- und `reader()`-Aufrufe lecken dauerhaft Prozesse
- **Status:** Behoben.
- **Änderung:** In `Workspace.new()` wurde der gesamte Initialisierungs-, Metadaten- und Speicherblock in ein `try ... except Exception: s.close(); raise` gekapselt. Auch in `Workspace.open()` wurde der Fehlerabfang von `except SolidCraftError:` auf `except Exception:` erweitert, damit auch unerwartete I/O- oder Subprozess-Fehler die Sitzung sicher schließen. `Workspace.reader()` war bereits mit `try/except` abgesichert. Zudem ruft `Session.__init__()` bei Fehlern während des MCP-Handshakes (`initialize`) im Fehlerpfad `self.close()` auf.

### Befund 4: Pfadtraversal und Validierung von Dokumentnamen
- **Status:** Behoben.
- **Analyse zu echtem Pfadtraversal:**
  Eine empirische Untersuchung zeigte: SolidCraft erzwingt beim Start über den Parameter `--allow-path <root>` eine strikte Sandbox. Versuchte `Workspace.new` oder `open` einen Pfad wie `/escaped.solidcraft` oder `/etc/passwd` anzusprechen, verweigerte SolidCraft den Schreib- oder Lesezugriff mit `SolidCraftError: ... outside the folders this agent may use`. Ein echtes Ausbrechen auf beliebige Systemdateien war daher auf Engine-Ebene blockiert.
  **Aber:** Auf Python-Ebene führte dies zu unbehandelten Fehlern und Lecks, und Python-Operationen wie `p.parent.mkdir()` oder spätere direkte Dateizugriffe hätten außerhalb der Workspace-Grenzen operiert. Ein leerer Name `""` erzeugte zudem `.solidcraft`.
- **Änderung:** Neue Validierung `_validate_name(name)`: Namen dürfen weder leer sein noch Pfadtrenner (`/`, `\`) oder `..` enthalten. In `Workspace._path(name, path)` werden alle Pfade absolut aufgelöst und strikt mit `p.relative_to(self.root)` gegen die Workspace-Wurzel geprüft; Pfade außerhalb werfen sofort einen klaren `ValueError`.

### Befund 5: `screenshot`-Werkzeug überschreibt Nicht-PNG-Dateien und CAD-Modelle
- **Status:** Behoben.
- **Änderung:** In `server.py:screenshot` wird nun geprüft, dass `target.suffix.lower() == ".png"` gilt. Pfade mit `.solidcraft` oder anderen Endungen werden mit `ValueError` abgewiesen. Existiert die Zieldatei bereits, wird anhand des 8-Byte-PNG-Headers (`\x89PNG\r\n\x1a\n`) geprüft, ob es sich tatsächlich um ein bestehendes PNG handelt; andernfalls wird das Überschreiben verweigert.

### Befund 6: `Session.close()` hinterlässt Zombie-Prozesse (`<defunct>`)
- **Status:** Behoben.
- **Änderung:** In `inventa/solidcraft.py:Session.close()` wird nach `self._p.kill()` nun zwingend `self._p.wait(timeout=5)` aufgerufen, um den Prozessstatus im Kernel abzuholen und den Eintrag aus der Prozesstabelle zu tilgen (`reaping`). Mehrfaches Schließen wird idempotent abgefangen (`_closed`-Flag).

### Befund 7: Fehlende Zeitlimits in `Session._rpc()` führen zum Hängen
- **Status:** Behoben.
- **Änderung:** `Session` besitzt nun einen konfigurierbaren Standard-Timeout (`timeout: float = 300.0`). Alle Aufrufe (`_rpc`, `tool`, `cmd`, `batch`) unterstützen optionale Timeouts. Das Lesen von `stdout` erfolgt über `_readline()` mit `select.select([self._p.stdout.fileno()], ...)` und Pufferung; bei Zeitüberschreitung wird die Sitzung sofort beendet (`self.close()`) und ein aussagekräftiger `SolidCraftError(f"timeout waiting for solidcraft-cli response after {timeout}s")` geworfen. `stderr` wird weiterhin über `DEVNULL` abgeführt, sodass Pipes nicht vollaufen können.

### Befund 8: Fehlende `__del__`-Methode in `Session` leckt Prozesse bei GC
- **Status:** Behoben.
- **Änderung:** `Session` implementiert nun `__del__(self)` (ruft `self.close()` auf, fängt alle Ausnahmen lautlos ab) sowie das Context-Manager-Protokoll (`__enter__` und `__exit__`). Unbeabsichtigt freigegebene Session-Objekte werden vom Garbage Collector sauber beendet.

### Befund 9: `references()` ignoriert `path_sketch` bei `solid.sweep`
- **Status:** Behoben.
- **Änderung:** In `inventa/sketch_rule.py:references()` prüft `walk()` nun `k in ("sketch", "path_sketch")` (sowie `k == "sketches"` als Liste). Dadurch wird bei `solid.sweep` und verwandten Befehlen (`surface.sweep`, `solid.pipe`, `solid.pattern.path`) sowohl die Profilskizze als auch die Pfadskizze erkannt. Beide Skizzen gehören dem Sweep, werden im Verlauf davor platziert und im Modellbrowser unter dem Feature verschachtelt.

### Befund 10: `close_document` verwirft ungespeicherte Änderungen stillschweigend
- **Status:** Behoben.
- **Änderung:** `server.py:close_document(document: str, discard: bool = False)` prüft via `document.inspect` den `dirty`-Status der SolidCraft-Sitzung. Ist die Datei modifiziert und `discard=False`, wird ein `ValueError` ausgelöst mit dem Hinweis, zuerst `save_document` aufzurufen oder `discard=True` zu übergeben.

### Befund 11: `to_part_coords` stürzt bei unvollständigen Koordinaten mit `IndexError` ab
- **Status:** Behoben.
- **Änderung:** Sowohl in `server.py:to_part_coords` als auch in `inplace.py:to_part_coords` wird validiert, dass `point` eine Sequenz aus genau 3 numerischen Werten `[x, y, z]` ist. Bei abweichenden Formaten wird ein sauberer `ValueError` geworfen.

### Befund 12: `server.py:run` hinterlässt nach Fehler in `sketch_rule.enforce` inkonsistenten Zustand
- **Status:** Behoben.
- **Änderung:** In Bauteildokumenten setzt `server.py:run` vor dem Ausführen des Batches einen Checkpoint via `edit.checkpoint`. Gelingt der Batch, schlägt aber `sketch_rule.enforce` fehl, wird über `edit.restore_checkpoint` der exakte Modellzustand von vor dem Batch wiederhergestellt und ein `RuntimeError` gemeldet. Bei fehlerfreiem Ablauf wird der Checkpoint mit `forget=True` verworfen.

### Befund 13: Testlücken in `tests/inventa/check.py`
- **Status:** Vollständig abgedeckt.
- **Änderung:** Neue Testfunktion `server_fixes_checks(tmp, ws)` mit 14 gezielten Prüfungen zu allen Befunden 1 bis 12 direkt am Python-API, sowie 10 neue MCP-Prüfungen in `mcp_server(tmp)` zu `list_documents`, `close_document`, `open_document`, `new_part`-Overwrite-Schutz, `dirty`-Schutz, `delete_feature`, `list_commands` und `command`.

---

## 3. Geänderte Werkzeug-Schnittstellen

| Werkzeug | Parameteränderung | Verhalten |
|---|---|---|
| `new_part` | `overwrite: bool = False` ergänzt | Verhindert unbeabsichtigtes Überschreiben bestehender CAD-Dateien. |
| `new_assembly` | `overwrite: bool = False` ergänzt | Verhindert unbeabsichtigtes Überschreiben bestehender Baugruppendateien. |
| `open_document` | unverändert | Liefert bei bereits geöffnetem Pfad das bestehende Dokument zurück; verbietet abweichende Aliase für denselben Pfad. |
| `close_document` | `discard: bool = False` ergänzt | Verhindert Datenverlust bei ungespeicherten Änderungen (`dirty: True`). |
| `screenshot` | unverändert | Validiert `.png`-Endung und verweigert das Überschreiben fremder Dateitypen. |
| `to_part_coords` | unverändert | Validiert Eingabekoordinaten strikt auf 3D `[x, y, z]`. |
| `run` | unverändert | Transaktionales Rollback der Befehle bei Fehlschlagen der Skizzenregel. |

---

## 4. Unsichere Stellen / Klärungspunkte

1. **`BrokenPipeError` vs. `SolidCraftError`:** In `solidcraft.py:Session._send` werden `OSError` und `BrokenPipeError` nun abgefangen, die Sitzung geschlossen und als `SolidCraftError` mit informativem Fehlertext weitergegeben.
2. **Standardteil-Erzeugung:** `standard_parts.create()` delegiert an `ws.new`. In `bolted.py` war bereits eine Prüfung `if p.is_file(): return p` vorhanden, sodass Standardteile im Verschraubungsassistenten wiederverwendet werden. Direkte manuelle Aufrufe von `ws.new(..., overwrite=False)` schützen nun auch gegen versehentliches Überschreiben existierender Normteile.
3. **Pipe-Deadlocks und Timeouts:** Durch `stderr=subprocess.DEVNULL` und den selektiven Timeout-Pufferleser in `_readline` sind I/O-Puffer-Blockaden und Deadlocks ausgeschlossen.

---

## 5. Nachtrag: Nacharbeiten an Commit `a8e3def`

### 1. UTF-8-Zeichen über Blockgrenzen in `Session._readline`
- **Problem:** Bei `os.read(self._p.stdout.fileno(), 65536)` wurde jeder gelesene Block isoliert per `.decode("utf-8", errors="replace")` decodiert und an einen String-Puffer angehängt. Wurde ein Mehrbyte-Zeichen (wie „Ø“, „°“, „µ“ oder Umlaute) genau auf einer Blockgrenze getrennt, entstanden ungültige Sequenzen an Blockende und Blockanfang, die zu `U+FFFD` („“) verstümmelt wurden.
- **Behebung:** `Session._buf` speichert nun Rohbytes (`bytes`), sucht nach dem Trennzeichen `b"\n"` und dekodiert erst die vollständige Zeile strikt ohne Ersetzung (`line.decode("utf-8")`).
- **Absicherung:** Neuer Test in `tests/inventa/check.py`, der eine JSON-Zeile mit `{"name": "Ø 8 mm"}` über eine Pipe mit zwei getrennten `os.write`-Aufrufen mitten durch das Mehrbyte-Zeichen `Ø` (Byte `0xc3` im ersten, Byte `0x98` im zweiten Schreibvorgang) sendet. Vor dem Fix schlug der Test reproduzierbar fehl; nach dem Fix empfängt `_readline` die Zeichenkette unverändert.

### 2. Prüfung von Befund 6 (Zombie-Prozesse) und Skriptanpassung
- **Befundprüfung:** Das Reproduktionsskript `review2-6-zombie-process.py` testete `Session.close()` nicht, sondern simulierte das fehlerhafte Verhalten an einem rohen `subprocess.Popen`-Objekt ohne `wait()`. Daher meldete das Skript auch nach der Behebung fälschlicherweise weiterhin „CONFIRMED“.
- **Behebung im Skript:** `review2-6-zombie-process.py` ruft nun direkt `Session.close()` auf (unter simulierter `TimeoutExpired`-Ausnahme auf dem ersten `wait(10)`-Aufruf). Da `Session.close()` im Timeout-Pfad nach `kill()` sauber `wait(5)` aufruft und den Prozess abholt, schlägt die Zombie-Assertion im Skript fehl (Prozess wird erfolgreich geerntet, keine Zombie-Prozesse mehr).
- **Zusätzlicher Test:** In `tests/inventa/check.py` wurde die Prüfung zu Befund 6 erweitert: Es wird sowohl der normale Beendigungspfad als auch der Timeout-Pfad (`kill()` + `wait(5)`) von `Session.close()` getestet und über `/proc/<pid>/status` sowie `os.waitpid` verifiziert, dass kein Zombie-Prozess in der Prozesstabelle verbleibt.
