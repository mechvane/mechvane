#!/usr/bin/env python3
"""Automated secondary diff reviewer for AI-agent branches via the Groq API.

Reviews git diffs (<base>...<branch>) against real bugs (logic errors, swallowed exceptions,
weakened/removed tests, tautological tests, resource leaks, security flaws, undocumented API breaks).
Splits large diffs into manageable chunk requests adhering to Groq free-tier rate limits
(8000 tokens/min, ~6500 tokens/request).

Usage:
  python3 tools/review_diff.py <branch> [--base main] [--model openai/gpt-oss-120b] [--out datei.md] [--repo pfad]
"""

import argparse
from dataclasses import dataclass, field
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_BASE = "main"
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_MAX_CHUNK_TOKENS = 4500
DEFAULT_RESPONSE_BUDGET = 1200
MAX_REQUEST_TOKENS = 6500

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

SYSTEM_PROMPT = """You are an experienced, pragmatic senior code reviewer performing a secondary audit on git diffs from AI agents.
Your goal is to identify ONLY real, actionable bugs and regressions.

Report ONLY:
1. Incorrect logic (off-by-one, inverted conditions, broken calculations, corrupted state).
2. Swallowed or mishandled exceptions (bare `except: pass`, masking errors, silently dropping failures).
3. Weakened, altered, or deleted test assertions, or tautological / self-validating tests that pass trivially without verifying real behavior.
4. Resource leaks (unclosed files, subprocesses, sockets, memory leaks, unhandled process reaping / zombie processes).
5. Security vulnerabilities (arbitrary path traversal, unsafe input handling, command injection, insecure temp files).
6. Undocumented behavioral regressions or breaking changes in public interfaces/APIs.

Do NOT report:
- Style, naming, formatting, or linting issues (PEP8, whitespace, line length, variable naming).
- Missing type hints, missing docstrings, or speculative performance optimizations.
- Pre-existing issues not modified by this diff.

Context and Confidence:
- You are reviewing a diff chunk which may have partial context. If you are unsure whether something is a real bug because relevant definitions or callers may exist outside this chunk, either omit it or explicitly state in the "why" field that you are unsure due to partial context.
- High severity: Crash, security hole, data loss, regression in core functionality.
- Medium severity: Bug in secondary logic, edge cases, leaky resource, weakened test.
- Low severity: Minor behavioral flaw or non-critical edge case.

Output Format:
You MUST respond with a JSON array of objects, or [] if no real bugs are found:
[
  {
    "file": "<file path>",
    "line": <integer line number in the new file, or null if unknown>,
    "severity": "high" | "medium" | "low",
    "finding": "<concise summary of the bug>",
    "why": "<detailed explanation of the failure mode and impact; note if unsure due to partial context>"
  }
]
Respond ONLY with the JSON array. Do not include markdown code block backticks, explanatory text, or conversational filler.
"""


@dataclass
class DiffChunk:
    file_path: str
    chunk_index: int
    total_chunks: int
    content: str
    estimated_tokens: int


@dataclass
class Finding:
    file: str
    line: int | None
    severity: str
    finding: str
    why: str


class RateLimiter:
    """Tracks Groq API rate limits and proactively throttles requests to stay within quota."""

    def __init__(self, limit_tokens: int = 8000, limit_requests: int = 1000):
        self.limit_tokens = limit_tokens
        self.limit_requests = limit_requests
        self.remaining_tokens = limit_tokens
        self.remaining_requests = limit_requests
        self.reset_tokens_s = 60.0
        self.reset_requests_s = 60.0
        self.last_response_time = time.monotonic()

    def update_from_headers(self, headers: dict) -> None:
        self.last_response_time = time.monotonic()
        # Header keys in urllib are case-insensitive
        for k, v in headers.items():
            k_lower = k.lower()
            if k_lower == "x-ratelimit-limit-tokens":
                try:
                    self.limit_tokens = int(v)
                except ValueError:
                    pass
            elif k_lower == "x-ratelimit-remaining-tokens":
                try:
                    self.remaining_tokens = int(v)
                except ValueError:
                    pass
            elif k_lower == "x-ratelimit-reset-tokens":
                self.reset_tokens_s = parse_groq_duration(v)
            elif k_lower == "x-ratelimit-limit-requests":
                try:
                    self.limit_requests = int(v)
                except ValueError:
                    pass
            elif k_lower == "x-ratelimit-remaining-requests":
                try:
                    self.remaining_requests = int(v)
                except ValueError:
                    pass
            elif k_lower == "x-ratelimit-reset-requests":
                self.reset_requests_s = parse_groq_duration(v)

    def wait_for_budget(self, needed_tokens: int) -> None:
        """Wait if estimated token usage would exceed remaining Groq token quota."""
        now = time.monotonic()
        elapsed = max(0.0, now - self.last_response_time)

        # Replenish token bucket based on elapsed time (limit_tokens / 60s)
        refill_rate = self.limit_tokens / 60.0
        current_remaining = min(self.limit_tokens, self.remaining_tokens + int(elapsed * refill_rate))

        if current_remaining < needed_tokens:
            deficit = needed_tokens - current_remaining
            sleep_time = (deficit / refill_rate) + 0.8
            sys.stderr.write(
                f"[RateLimit] Throttling: waiting {sleep_time:.1f}s for token bucket "
                f"({current_remaining}/{self.limit_tokens} available, need ~{needed_tokens})...\n"
            )
            time.sleep(sleep_time)
            self.remaining_tokens = min(self.limit_tokens, current_remaining + int(sleep_time * refill_rate))
        else:
            self.remaining_tokens = current_remaining


def estimate_tokens(text: str) -> int:
    """Conservative token estimation (1 token ≈ 3.5 characters)."""
    return math.ceil(len(text) / 3.5)


def parse_groq_duration(val: str | None) -> float:
    """Parse Groq duration string like '982ms', '1.5s', '1m26.4s' or numeric seconds."""
    if not val:
        return 0.0
    val = str(val).strip()
    try:
        return float(val)
    except ValueError:
        pass

    total = 0.0
    m_min = re.search(r"(\d+(?:\.\d+)?)\s*m(?!s)", val)
    if m_min:
        total += float(m_min.group(1)) * 60.0
    m_sec = re.search(r"(\d+(?:\.\d+)?)\s*s", val)
    if m_sec:
        total += float(m_sec.group(1))
    m_ms = re.search(r"(\d+(?:\.\d+)?)\s*ms", val)
    if m_ms:
        total += float(m_ms.group(1)) / 1000.0
    return total


def get_groq_api_key() -> str:
    """Retrieve Groq API key from environment or secrets file without printing/logging it."""
    key = os.environ.get("GROQ_API_KEY")
    if key and key.strip():
        return key.strip()

    search_files = [
        Path.home() / ".secrets" / "groq.env",
        Path.cwd() / ".env",
    ]
    for p in search_files:
        try:
            if p.is_file():
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except OSError:
            pass

    sys.stderr.write("Error: GROQ_API_KEY environment variable is not set.\n")
    sys.exit(1)


def run_git(args: list[str], repo: Path) -> str:
    """Execute git command and return stripped stdout."""
    res = subprocess.run(
        ["git", "-C", str(repo)] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def should_skip_file(path: str, include_docs: bool = False) -> tuple[bool, str]:
    """Check if file should be skipped to conserve review quota."""
    if include_docs:
        return False, ""
    norm = path.replace("\\", "/")
    if norm.startswith("docs/research/") and norm.endswith(".md"):
        return True, "Research document (docs/research/*.md)"
    if norm.endswith(".json"):
        return True, "Data JSON (*.json)"
    return False, ""


def split_file_diff(file_diff: str, max_chunk_tokens: int = DEFAULT_MAX_CHUNK_TOKENS) -> list[str]:
    """Split a single file diff into hunk groups under max_chunk_tokens."""
    lines = file_diff.splitlines(keepends=True)
    if not lines:
        return []

    hunk_indices = [i for i, l in enumerate(lines) if l.startswith("@@ ")]
    if not hunk_indices:
        return [file_diff]

    file_header = "".join(lines[:hunk_indices[0]])
    header_tokens = estimate_tokens(file_header)
    effective_max = max(500, max_chunk_tokens - header_tokens)

    raw_hunks = []
    for idx, start in enumerate(hunk_indices):
        end = hunk_indices[idx + 1] if idx + 1 < len(hunk_indices) else len(lines)
        raw_hunks.append(lines[start:end])

    # If any single hunk exceeds effective_max, split its lines into sub-hunks
    hunks = []
    for h in raw_hunks:
        if estimate_tokens("".join(h)) <= effective_max:
            hunks.append(h)
        else:
            h_header = h[0]
            m = re.search(r"\+(\d+)", h_header)
            cur_line = int(m.group(1)) if m else 1

            sub_hunk = []
            sub_tokens = estimate_tokens(h_header)
            part = 1
            part_start_line = cur_line

            for l in h[1:]:
                l_tok = estimate_tokens(l)
                if sub_hunk and (sub_tokens + l_tok > effective_max):
                    sub_header = f"{h_header.strip()} [Part {part}, from line {part_start_line}]\n"
                    hunks.append([sub_header] + sub_hunk)
                    part += 1
                    part_start_line = cur_line
                    sub_hunk = [l]
                    sub_tokens = estimate_tokens(h_header) + l_tok
                else:
                    sub_hunk.append(l)
                    sub_tokens += l_tok

                if l.startswith("+") or l.startswith(" "):
                    cur_line += 1

            if sub_hunk:
                sub_header = f"{h_header.strip()} [Part {part}, from line {part_start_line}]\n"
                hunks.append([sub_header] + sub_hunk)

    # Group hunks into chunks up to max_chunk_tokens
    chunks = []
    cur_group = []
    cur_tokens = header_tokens

    for h in hunks:
        h_tok = estimate_tokens("".join(h))
        if cur_group and (cur_tokens + h_tok > max_chunk_tokens):
            chunk_text = file_header + "".join("".join(x) for x in cur_group)
            chunks.append(chunk_text)
            cur_group = [h]
            cur_tokens = header_tokens + h_tok
        else:
            cur_group.append(h)
            cur_tokens += h_tok

    if cur_group:
        chunk_text = file_header + "".join("".join(x) for x in cur_group)
        chunks.append(chunk_text)

    return chunks


def split_diff_into_chunks(
    diff_text: str,
    max_chunk_tokens: int = DEFAULT_MAX_CHUNK_TOKENS,
    include_docs: bool = False,
) -> tuple[list[DiffChunk], list[tuple[str, str]]]:
    """Parse complete git diff and break it into chunks per file and hunk groups."""
    chunks: list[DiffChunk] = []
    skipped_files: list[tuple[str, str]] = []

    pattern = r"(?m)(?=^diff --git )"
    raw_files = [f for f in re.split(pattern, diff_text) if f.strip()]

    for rf in raw_files:
        lines = rf.splitlines()
        if not lines:
            continue
        first_line = lines[0]
        m = re.match(r"^diff --git a/(.*?) b/(.*)", first_line)
        path = m.group(2) if m else "unknown"

        # Check binary diff
        if "Binary files " in rf or "GIT binary patch" in rf:
            skipped_files.append((path, "Binary file"))
            continue

        # Check doc / data skipping
        skip, reason = should_skip_file(path, include_docs=include_docs)
        if skip:
            skipped_files.append((path, reason))
            continue

        file_tok = estimate_tokens(rf)
        if file_tok <= max_chunk_tokens:
            chunks.append(
                DiffChunk(
                    file_path=path,
                    chunk_index=1,
                    total_chunks=1,
                    content=rf,
                    estimated_tokens=file_tok,
                )
            )
        else:
            sub_chunks = split_file_diff(rf, max_chunk_tokens=max_chunk_tokens)
            total = len(sub_chunks)
            for idx, sc in enumerate(sub_chunks, 1):
                chunks.append(
                    DiffChunk(
                        file_path=path,
                        chunk_index=idx,
                        total_chunks=total,
                        content=sc,
                        estimated_tokens=estimate_tokens(sc),
                    )
                )

    return chunks, skipped_files


def parse_review_response(raw_text: str) -> list[dict]:
    """Extract and validate JSON list of findings from LLM output."""
    if not raw_text or not raw_text.strip():
        return []

    text = raw_text.strip()

    # 1. Search for code fence blocks: ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*(\[\s*[\s\S]*?\])\s*```", text, re.IGNORECASE)
    if fence_match:
        try:
            parsed = json.loads(fence_match.group(1))
            if isinstance(parsed, list):
                return _normalize_findings(parsed)
        except json.JSONDecodeError:
            pass

    # 2. Try direct parsing
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return _normalize_findings(parsed)
    except json.JSONDecodeError:
        pass

    # 3. Search for outermost square brackets [...]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return _normalize_findings(parsed)
        except json.JSONDecodeError:
            pass

    return []


def _normalize_findings(raw_items: list) -> list[dict]:
    """Sanitize and validate finding items."""
    valid = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        file_path = str(item.get("file", "")).strip()
        line = item.get("line")
        if line is not None:
            try:
                line = int(line)
            except (ValueError, TypeError):
                line = None
        severity = str(item.get("severity", "medium")).lower().strip()
        if severity not in ("high", "medium", "low"):
            severity = "medium"
        finding = str(item.get("finding", "")).strip()
        why = str(item.get("why", "")).strip()

        if finding or why:
            valid.append(
                {
                    "file": file_path,
                    "line": line,
                    "severity": severity,
                    "finding": finding,
                    "why": why,
                }
            )
    return valid


def call_groq_api(
    chunk: DiffChunk,
    model: str,
    api_key: str,
    rate_limiter: RateLimiter,
    response_budget: int = DEFAULT_RESPONSE_BUDGET,
    max_retries: int = 5,
) -> list[dict]:
    """Call Groq API with automatic rate-limit throttling and retry backoff."""
    sys_tok = estimate_tokens(SYSTEM_PROMPT)
    req_tokens = chunk.estimated_tokens + sys_tok + response_budget

    # Proactive wait if remaining tokens are insufficient
    rate_limiter.wait_for_budget(req_tokens)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Review the following diff chunk from `{chunk.file_path}` "
                    f"(part {chunk.chunk_index}/{chunk.total_chunks}):\n\n{chunk.content}"
                ),
            },
        ],
        "max_completion_tokens": response_budget,
        "temperature": 0.1,
    }

    req_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(GROQ_API_URL, headers=headers, data=req_data)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                rate_limiter.update_from_headers(dict(resp.headers))
                resp_bytes = resp.read()
                body = json.loads(resp_bytes.decode("utf-8"))
                choices = body.get("choices", [])
                if not choices:
                    return []
                message = choices[0].get("message", {})
                content = message.get("content", "")
                findings = parse_review_response(content)

                # Ensure file path is correctly attributed
                for f in findings:
                    if not f["file"] or f["file"] == Path(chunk.file_path).name:
                        f["file"] = chunk.file_path

                return findings

        except urllib.error.HTTPError as e:
            rate_limiter.update_from_headers(dict(e.headers))
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass

            if e.code == 429:
                retry_after_str = e.headers.get("Retry-After") or e.headers.get("x-ratelimit-reset-tokens")
                wait_s = parse_groq_duration(retry_after_str)
                if wait_s <= 0:
                    wait_s = 15.0 * attempt
                sys.stderr.write(
                    f"[RateLimit] 429 Too Many Requests on attempt {attempt}/{max_retries}. "
                    f"Sleeping {wait_s:.1f}s before retry...\n"
                )
                time.sleep(wait_s)
                continue
            elif e.code in (500, 502, 503, 504):
                wait_s = 5.0 * attempt
                sys.stderr.write(
                    f"[Groq API] HTTP {e.code} on attempt {attempt}/{max_retries}. "
                    f"Sleeping {wait_s:.1f}s before retry...\n"
                )
                time.sleep(wait_s)
                continue
            else:
                sys.stderr.write(f"[Groq API] HTTP {e.code}: {e.reason}\n{err_body}\n")
                raise

        except (urllib.error.URLError, TimeoutError, OSError) as e:
            wait_s = 5.0 * attempt
            sys.stderr.write(
                f"[Groq API] Network error ({e}) on attempt {attempt}/{max_retries}. "
                f"Sleeping {wait_s:.1f}s before retry...\n"
            )
            time.sleep(wait_s)
            continue

    raise RuntimeError(f"Groq API call failed after {max_retries} retries for {chunk.file_path}")


def severity_rank(sev: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(sev.lower(), 1)


def format_markdown_report(
    branch: str,
    base: str,
    base_commit: str,
    branch_commit: str,
    model: str,
    chunks_count: int,
    runtime_seconds: float,
    findings: list[Finding],
    skipped_files: list[tuple[str, str]],
    preamble: str = "",
) -> str:
    """Format review findings and execution metadata into GitHub Markdown."""
    lines: list[str] = []

    if preamble.strip():
        lines.append(preamble.strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(f"# Groq Diff Review: `{branch}`")
    lines.append("")

    highs = [f for f in findings if f.severity == "high"]
    meds = [f for f in findings if f.severity == "medium"]
    lows = [f for f in findings if f.severity == "low"]

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines.append("## Metadaten")
    lines.append(f"- **Branch:** `{branch}` (`{branch_commit[:10]}`)")
    lines.append(f"- **Basis:** `{base}` (`{base_commit[:10]}`)")
    lines.append(f"- **Modell:** `{model}`")
    lines.append(f"- **Geprüfte Chunks:** {chunks_count}")
    lines.append(f"- **Befunde gesamt:** {len(findings)} (High: {len(highs)}, Medium: {len(meds)}, Low: {len(lows)})")
    lines.append(f"- **Laufzeit:** {runtime_seconds:.1f} s")
    lines.append(f"- **Zeitpunkt:** {timestamp}")
    lines.append("")

    lines.append("## Befunde")
    lines.append("")

    if not findings:
        lines.append("Keine echten Fehler oder Regressionen gefunden (Diff unauffällig).")
        lines.append("")
    else:
        for cat_name, cat_list in [("High Severity", highs), ("Medium Severity", meds), ("Low Severity", lows)]:
            if not cat_list:
                continue
            lines.append(f"### {cat_name}")
            lines.append("")
            for f in cat_list:
                loc = f"`{f.file}:{f.line}`" if f.line is not None else f"`{f.file}`"
                lines.append(f"#### {loc}")
                lines.append(f"- **Befund:** {f.finding}")
                lines.append(f"- **Begründung:** {f.why}")
                lines.append("")

    lines.append("## Übersprungene Dateien")
    lines.append("")
    if not skipped_files:
        lines.append("Keine Dateien übersprungen.")
    else:
        for p, r in skipped_files:
            lines.append(f"- `{p}` ({r})")
    lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated secondary diff reviewer for git branches using the Groq API."
    )
    parser.add_argument("branch", help="Git branch to review")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"Base branch (default: {DEFAULT_BASE})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Groq model (default: {DEFAULT_MODEL})")
    parser.add_argument("--out", help="Write markdown report to specified file path")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Path to git repository (default: repo root)")
    parser.add_argument("--include-docs", action="store_true", help="Include docs/research/*.md and data JSON files")
    parser.add_argument(
        "--max-chunk-tokens",
        type=int,
        default=DEFAULT_MAX_CHUNK_TOKENS,
        help=f"Maximum tokens per chunk (default: {DEFAULT_MAX_CHUNK_TOKENS})",
    )
    parser.add_argument(
        "--response-budget",
        type=int,
        default=DEFAULT_RESPONSE_BUDGET,
        help=f"Completion token budget per request (default: {DEFAULT_RESPONSE_BUDGET})",
    )
    parser.add_argument("--preamble", help="Optional preamble markdown string or path to prepend to the report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_path = Path(args.repo).resolve()

    # Verify git repo
    try:
        branch_commit = run_git(["rev-parse", args.branch], repo_path).strip()
    except subprocess.CalledProcessError:
        sys.stderr.write(f"Error: branch '{args.branch}' not found in repo {repo_path}\n")
        return 1

    try:
        base_commit = run_git(["merge-base", args.base, args.branch], repo_path).strip()
    except subprocess.CalledProcessError:
        try:
            base_commit = run_git(["rev-parse", args.base], repo_path).strip()
        except subprocess.CalledProcessError:
            sys.stderr.write(f"Error: base '{args.base}' not found in repo {repo_path}\n")
            return 1

    # Load API key
    api_key = get_groq_api_key()

    # Get diff
    try:
        diff_text = run_git(["diff", f"{args.base}...{args.branch}"], repo_path)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error getting git diff: {e}\n")
        return 1

    if not diff_text.strip():
        sys.stderr.write(f"Diff between {args.base} and {args.branch} is empty.\n")
        report = format_markdown_report(
            branch=args.branch,
            base=args.base,
            base_commit=base_commit,
            branch_commit=branch_commit,
            model=args.model,
            chunks_count=0,
            runtime_seconds=0.0,
            findings=[],
            skipped_files=[],
            preamble=args.preamble or "",
        )
        if args.out:
            Path(args.out).write_text(report, encoding="utf-8")
        else:
            print(report)
        return 0

    # Chunk diff
    chunks, skipped_files = split_diff_into_chunks(
        diff_text,
        max_chunk_tokens=args.max_chunk_tokens,
        include_docs=args.include_docs,
    )

    sys.stderr.write(
        f"Prepared {len(chunks)} chunks across modified files "
        f"({len(skipped_files)} files skipped, budget: {args.max_chunk_tokens} tokens/chunk).\n"
    )

    rate_limiter = RateLimiter()
    all_findings_raw: list[dict] = []
    start_time = time.monotonic()
    successful_chunks = 0

    for idx, chunk in enumerate(chunks, 1):
        sys.stderr.write(
            f"[{idx}/{len(chunks)}] Reviewing {chunk.file_path} "
            f"(chunk {chunk.chunk_index}/{chunk.total_chunks}, ~{chunk.estimated_tokens} tokens)... "
        )
        sys.stderr.flush()

        try:
            findings = call_groq_api(
                chunk=chunk,
                model=args.model,
                api_key=api_key,
                rate_limiter=rate_limiter,
                response_budget=args.response_budget,
            )
            all_findings_raw.extend(findings)
            successful_chunks += 1
            sys.stderr.write(f"OK ({len(findings)} findings)\n")
        except Exception as e:
            sys.stderr.write(f"FAILED: {e}\n")

    runtime = time.monotonic() - start_time

    if successful_chunks == 0 and chunks:
        sys.stderr.write("Error: All chunks failed during Groq API review.\n")
        return 1

    # Convert to Finding objects and sort
    findings_list = [
        Finding(
            file=f.get("file", ""),
            line=f.get("line"),
            severity=f.get("severity", "medium"),
            finding=f.get("finding", ""),
            why=f.get("why", ""),
        )
        for f in all_findings_raw
    ]

    findings_list.sort(key=lambda f: (severity_rank(f.severity), f.file, f.line or 0))

    # Read preamble if specified as file
    preamble_text = ""
    if args.preamble:
        p_path = Path(args.preamble)
        if p_path.is_file():
            preamble_text = p_path.read_text(encoding="utf-8")
        else:
            preamble_text = args.preamble

    report = format_markdown_report(
        branch=args.branch,
        base=args.base,
        base_commit=base_commit,
        branch_commit=branch_commit,
        model=args.model,
        chunks_count=len(chunks),
        runtime_seconds=runtime,
        findings=findings_list,
        skipped_files=skipped_files,
        preamble=preamble_text,
    )

    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(report, encoding="utf-8")
        sys.stderr.write(f"Report written to {args.out}\n")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
