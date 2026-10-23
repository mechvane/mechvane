# Groq Diff Review: `gemini/normteile-fixes`

## Metadaten
- **Branch:** `gemini/normteile-fixes` (`3414a2dac1`)
- **Basis:** `main` (`687054040a`)
- **Modell:** `openai/gpt-oss-120b`
- **Geprüfte Chunks:** 7
- **Befunde gesamt:** 2 (High: 0, Medium: 2, Low: 0)
- **Laufzeit:** 160.6 s
- **Zeitpunkt:** 2026-10-21 18:38:27 UTC

## Befunde

### Medium Severity

#### `tests/inventa/check.py:1005`
- **Befund:** Resource leak: ws (workspace) is not closed at the end of bolted_review_fixes_checks, unlike other test functions that call ws.close_all()
- **Begründung:** The function creates many temporary parts and assemblies but never calls ws.close_all() or otherwise releases the workspace resources. In a long test run this can accumulate open files or processes, leading to exhaustion of resources or interference between tests.

#### `tests/inventa/check.py:1020`
- **Befund:** Premature call to ws.close_all() inside bolted_connection_checks
- **Begründung:** The function bolted_connection_checks closes the workspace with ws.close_all() before returning. In main(), after calling bolted_connection_checks(ws), the code proceeds to call bolted_review_fixes_checks(ws) and edit_in_place_checks(ws) using the same ws object. Since the workspace has already been closed, subsequent operations will likely raise errors or operate on an invalid state, causing test failures or crashes.

## Übersprungene Dateien

- `docs/research/2026-10-21-normteile-fixes-flash.md` (Research document (docs/research/*.md))
