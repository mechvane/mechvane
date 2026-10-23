# Forschungsbericht & Zweitprüfung: `gemini/server-fixes` via Groq

## Dokumentation: Groq Diff Review (`tools/review_diff.py`)

### Zweck
`tools/review_diff.py` dient als leichtgewichtiger, automatischer Zweitprüfer für Git-Feature-Branches von KI-Agenten über die kostenlose Groq-API (OpenAI-kompatibles Format `https://api.groq.com/openai/v1/chat/completions`). Das Werkzeug prüft ausschließlich auf echte funktionale Defekte:
- Falsche Logik (Berechnungsfehler, Invertierungen, Off-by-One).
- Verschluckte oder maskierte Ausnahmen (`except: pass`).
- Abgeschwächte, entfernte oder sich selbst bestätigende (tautologische) Tests.
- Ressourcenlecks (Dateideskriptoren, Subprozesse, Zombies, Sockets).
- Sicherheitsprobleme (Pfadvalidierung, ungesicherte Dateizugriffe, Befehlsinjektion).
- Undokumentierte Verhaltensänderungen an öffentlichen Schnittstellen.
Stil-, Formatierungs- und Linting-Fragen werden konsequent ignoriert.

### Aufruf
```bash
# Basis-Aufruf gegen main:
python3 tools/review_diff.py <branch>

# Mit Optionen:
python3 tools/review_diff.py <branch> \
  [--base main] \
  [--model openai/gpt-oss-120b] \
  [--out docs/research/bericht.md] \
  [--repo /pfad/zum/repo] \
  [--include-docs]
```

Umgebung: Erfordert `GROQ_API_KEY` (z. B. via `set -a; . ~/.secrets/groq.env; set +a`).

### Grenzen und Ratenlimits (Stand 2026-10-21)
- **Gratis-Kontingent:** 8.000 Tokens pro Minute und 1.000 Anfragen pro Tag (Header `x-ratelimit-*`).
- **Anfragebudget:** Obwohl Modelle wie `openai/gpt-oss-120b` und `qwen/qwen3.8-27b` ein Kontextfenster von 131k Tokens unterstützen, scheitert jede Einzelanfrage über ~7.000 Tokens (Eingabe + `max_completion_tokens`) am Minutenlimit.
- **Diff-Chunking:** Diffs werden dateiweise und bei großen Dateien (wie `tests/inventa/check.py`) hunksweise in Blöcke unter ~4.500 Tokens zerlegt (konservative Schätzung: 1 Token ≈ 3,5 Zeichen).
- **Proaktives Throttling:** Auswertung von `x-ratelimit-remaining-tokens`, `x-ratelimit-reset-tokens` und `Retry-After` mit automatischem Warten vor dem Absenden und Backoff bei HTTP 429.
- **Dateifilter:** `docs/research/*.md` und reine Daten-JSON (`*.json`) werden standardmäßig übersprungen, um Quota zu sparen (mit `--include-docs` aktivierbar).

### Einordnung: Claude vs. Groq im Branch `gemini/server-fixes`
- **Claudes Befund:** Claude fand in `inventa/solidcraft.py` einen kritischen UTF-8-Fehler in `_readline`: Eingehende Chunks wurden einzeln mit `errors="replace"` decodiert. Wenn ein Mehrbyte-Zeichen (z. B. das Durchmesserzeichen „Ø“ / `0xC3 0x98`) auf einer Chunkgrenze getrennt wurde, entstand ein fehlerhaftes Replacement-Zeichen. Dieser Fehler wurde im Branch in Commit `a74c0ea` behoben (Rohbytes werden in `Session._buf` gepuffert und erst nach Eintreffen von `\n` decodiert).
- **Groq-Prüfung:** Der nachfolgende automatische Review wurde mit dem Standardmodell `openai/gpt-oss-120b` auf dem Branch `gemini/server-fixes` (Basis `main`) durchgeführt. Groq prüft die 17 Chunks des verbleibenden Diffs.

---

# Groq Diff Review: `gemini/server-fixes`

## Metadaten
- **Branch:** `gemini/server-fixes` (`a74c0ea26f`)
- **Basis:** `main` (`2e947149ab`)
- **Modell:** `openai/gpt-oss-120b`
- **Geprüfte Chunks:** 17
- **Befunde gesamt:** 2 (High: 0, Medium: 2, Low: 0)
- **Laufzeit:** 404.7 s
- **Zeitpunkt:** 2026-10-21 18:34:43 UTC

## Befunde

### Medium Severity

#### `inventa/tree.py:108`
- **Befund:** Potential KeyError when building tl_map from timeline entries
- **Begründung:** The code builds tl_map with a dict comprehension `{f["name"]: f for f in timeline(s).get("timeline", [])}` assuming every timeline entry has a "name" key. If any entry lacks this key, a KeyError will be raised, causing assembly_tree to crash for inputs that previously succeeded.

#### `tests/inventa/check.py`
- **Befund:** Monkey‑patched session.cmd in test "Probe failure falls back to geometric heuristics" is not restored in a finally block, risking state leakage if an exception occurs before the explicit restoration line.
- **Begründung:** The test replaces doc_err.session.cmd with a mock that raises on "inspect.interference" and later restores the original with `doc_err.session.cmd = orig_cmd`. The restoration occurs after the `with warnings.catch_warnings` block. If any exception propagates out of that block (e.g., from query.find or design_rules.check), the restoration line is skipped, leaving the session in a patched state for subsequent tests, which can cause hidden failures or flaky behavior.

## Übersprungene Dateien

- `docs/research/2026-10-21-achsrichtung-flash.md` (Research document (docs/research/*.md))
- `docs/research/2026-10-21-argon-fixes-2-flash.md` (Research document (docs/research/*.md))
- `docs/research/2026-10-21-argon-fixes-3-flash.md` (Research document (docs/research/*.md))
- `docs/research/2026-10-21-inplace-fixes-flash.md` (Research document (docs/research/*.md))
- `docs/research/2026-10-21-integration-flash.md` (Research document (docs/research/*.md))
- `docs/research/2026-10-21-links-fixes-flash.md` (Research document (docs/research/*.md))
- `docs/research/2026-10-21-server-fixes-flash.md` (Research document (docs/research/*.md))
