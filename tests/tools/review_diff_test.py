#!/usr/bin/env python3
"""Offline unit tests for tools/review_diff.py components.

Tests token estimation, duration parsing, JSON extraction (raw, code fenced, text-wrapped),
file skipping rules, diff hunk splitting, and report generation without network or API calls.

Usage:
  python3 tests/tools/review_diff_test.py
"""

import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.review_diff import (
    DiffChunk,
    Finding,
    RateLimiter,
    estimate_tokens,
    format_markdown_report,
    parse_groq_duration,
    parse_review_response,
    severity_rank,
    should_skip_file,
    split_diff_into_chunks,
    split_file_diff,
)


def test_token_estimation():
    assert estimate_tokens("") == 0
    # 4 chars: 4 / 3.5 = 1.14 -> ceil = 2
    assert estimate_tokens("abcd") == 2
    # 7 chars: 7 / 3.5 = 2.0 -> ceil = 2
    assert estimate_tokens("1234567") == 2
    # 8 chars: 8 / 3.5 = 2.28 -> ceil = 3
    assert estimate_tokens("12345678") == 3
    # 3500 chars -> 1000 tokens
    assert estimate_tokens("a" * 3500) == 1000
    print("✓ test_token_estimation passed")


def test_parse_groq_duration():
    assert parse_groq_duration(None) == 0.0
    assert parse_groq_duration("") == 0.0
    assert parse_groq_duration("12.5") == 12.5
    assert abs(parse_groq_duration("982ms") - 0.982) < 1e-4
    assert abs(parse_groq_duration("1.5s") - 1.5) < 1e-4
    assert abs(parse_groq_duration("45s") - 45.0) < 1e-4
    # 1m26.4s = 60 + 26.4 = 86.4
    assert abs(parse_groq_duration("1m26.4s") - 86.4) < 1e-4
    # 2m = 120s
    assert abs(parse_groq_duration("2m") - 120.0) < 1e-4
    print("✓ test_parse_groq_duration passed")


def test_parse_review_response_clean_json():
    raw = """
    [
      {
        "file": "mechvane/server.py",
        "line": 42,
        "severity": "high",
        "finding": "Resource leak in handle_connection",
        "why": "Socket is not closed in finally block."
      }
    ]
    """
    res = parse_review_response(raw)
    assert len(res) == 1
    assert res[0]["file"] == "mechvane/server.py"
    assert res[0]["line"] == 42
    assert res[0]["severity"] == "high"
    assert res[0]["finding"] == "Resource leak in handle_connection"
    assert "Socket is not closed" in res[0]["why"]
    print("✓ test_parse_review_response_clean_json passed")


def test_parse_review_response_code_fence():
    raw = """```json
[
  {
    "file": "mechvane/solidcraft.py",
    "line": "75",
    "severity": "MEDIUM",
    "finding": "Swallowed exception",
    "why": "Except block passes silently."
  }
]
```"""
    res = parse_review_response(raw)
    assert len(res) == 1
    assert res[0]["file"] == "mechvane/solidcraft.py"
    assert res[0]["line"] == 75  # String converted to int
    assert res[0]["severity"] == "medium"  # Normalized to lowercase
    print("✓ test_parse_review_response_code_fence passed")


def test_parse_review_response_surrounding_text():
    raw = """
Here is my evaluation of the diff:
I examined all hunks carefully.

[
  {
    "file": "mechvane/links.py",
    "line": null,
    "severity": "low",
    "finding": "Missing edge case check",
    "why": "When links are empty, return value is unclear."
  }
]

Overall looks mostly fine!
"""
    res = parse_review_response(raw)
    assert len(res) == 1
    assert res[0]["file"] == "mechvane/links.py"
    assert res[0]["line"] is None
    assert res[0]["severity"] == "low"
    print("✓ test_parse_review_response_surrounding_text passed")


def test_parse_review_response_empty_and_invalid():
    assert parse_review_response("") == []
    assert parse_review_response("[]") == []
    assert parse_review_response("```json\n[]\n```") == []
    assert parse_review_response("I found no errors in this diff.") == []
    assert parse_review_response("Not JSON: [something invalid{") == []
    print("✓ test_parse_review_response_empty_and_invalid passed")


def test_should_skip_file():
    # Research docs skipped unless include_docs=True
    skip, _ = should_skip_file("docs/research/2026-10-21-server-fixes-flash.md", include_docs=False)
    assert skip is True
    skip, _ = should_skip_file("docs/research/2026-10-21-server-fixes-flash.md", include_docs=True)
    assert skip is False

    # Data JSON skipped unless include_docs=True
    skip, _ = should_skip_file("tests/reference/scharnier.build.json", include_docs=False)
    assert skip is True
    skip, _ = should_skip_file("tests/reference/scharnier.build.json", include_docs=True)
    assert skip is False

    # Code files never skipped
    skip, _ = should_skip_file("mechvane/server.py", include_docs=False)
    assert skip is False
    skip, _ = should_skip_file("tests/mechvane/check.py", include_docs=False)
    assert skip is False

    # Non-research docs
    skip, _ = should_skip_file("docs/mechvane-mcp.md", include_docs=False)
    assert skip is False
    print("✓ test_should_skip_file passed")


def test_diff_splitting_small_file():
    sample_diff = """diff --git a/mechvane/tree.py b/mechvane/tree.py
index abc..def 100644
--- a/mechvane/tree.py
+++ b/mechvane/tree.py
@@ -10,4 +10,6 @@ def get_tree():
+    # new node
+    pass
"""
    chunks, skipped = split_diff_into_chunks(sample_diff, max_chunk_tokens=1000)
    assert len(skipped) == 0
    assert len(chunks) == 1
    assert chunks[0].file_path == "mechvane/tree.py"
    assert chunks[0].chunk_index == 1
    assert chunks[0].total_chunks == 1
    print("✓ test_diff_splitting_small_file passed")


def test_diff_splitting_large_file_hunks():
    # Construct a diff with multiple hunks exceeding a tiny chunk budget
    header = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n"
    hunk1 = "@@ -1,5 +1,10 @@\n" + ("+ line_a = 1\n" * 20)
    hunk2 = "@@ -20,5 +25,10 @@\n" + ("+ line_b = 2\n" * 20)
    hunk3 = "@@ -40,5 +50,10 @@\n" + ("+ line_c = 3\n" * 20)
    full_diff = header + hunk1 + hunk2 + hunk3

    # Set max chunk tokens so each chunk can hold header + 1 hunk (~150 tokens)
    chunks, _ = split_diff_into_chunks(full_diff, max_chunk_tokens=150)
    assert len(chunks) > 1
    for c in chunks:
        assert c.file_path == "test.py"
        assert c.content.startswith(header)
    print(f"✓ test_diff_splitting_large_file_hunks passed ({len(chunks)} chunks created)")


def test_diff_splitting_huge_single_hunk():
    # Construct a single hunk with 300 lines that exceeds a small chunk budget
    header = "diff --git a/huge.py b/huge.py\n--- a/huge.py\n+++ b/huge.py\n"
    hunk = "@@ -1,1 +1,300 @@\n" + ("+ x = 42\n" * 300)
    full_diff = header + hunk

    # Each chunk budget ~100 tokens (~350 chars)
    chunks = split_file_diff(full_diff, max_chunk_tokens=150)
    assert len(chunks) > 1
    for c in chunks:
        assert c.startswith(header)
        assert "[Part " in c
    print(f"✓ test_diff_splitting_huge_single_hunk passed ({len(chunks)} chunks from single hunk)")


def test_format_markdown_report():
    findings = [
        Finding(
            file="mechvane/solidcraft.py",
            line=42,
            severity="medium",
            finding="Swallowed OSError",
            why="Errors during close are ignored.",
        ),
        Finding(
            file="mechvane/server.py",
            line=10,
            severity="high",
            finding="Path traversal vulnerability",
            why="Unvalidated user input passed to open().",
        ),
        Finding(
            file="mechvane/geometry.py",
            line=100,
            severity="low",
            finding="Redundant float conversion",
            why="Argument is already float.",
        ),
    ]
    # Sort findings by severity
    findings.sort(key=lambda f: (severity_rank(f.severity), f.file, f.line or 0))

    skipped = [
        ("docs/research/2026-10-21-test.md", "Research document (docs/research/*.md)"),
        ("data/test.json", "Data JSON (*.json)"),
    ]

    report = format_markdown_report(
        branch="gemini/groq-review",
        base="main",
        base_commit="1234567890abcdef",
        branch_commit="abcdef1234567890",
        model="openai/gpt-oss-120b",
        chunks_count=5,
        runtime_seconds=12.3,
        findings=findings,
        skipped_files=skipped,
        preamble="## Test Preamble\nTesting documentation.",
    )

    assert "Test Preamble" in report
    assert "Groq Diff Review: `gemini/groq-review`" in report
    assert "High Severity" in report
    assert "Medium Severity" in report
    assert "Low Severity" in report
    # High severity should appear before Medium severity
    idx_high = report.index("Path traversal vulnerability")
    idx_med = report.index("Swallowed OSError")
    idx_low = report.index("Redundant float conversion")
    assert idx_high < idx_med < idx_low
    assert "docs/research/2026-10-21-test.md" in report
    print("✓ test_format_markdown_report passed")


def test_rate_limiter_logic():
    limiter = RateLimiter(limit_tokens=8000, limit_requests=1000)
    headers = {
        "x-ratelimit-limit-tokens": "8000",
        "x-ratelimit-remaining-tokens": "5000",
        "x-ratelimit-reset-tokens": "22.5s",
        "x-ratelimit-limit-requests": "1000",
        "x-ratelimit-remaining-requests": "995",
        "x-ratelimit-reset-requests": "1m30s",
    }
    limiter.update_from_headers(headers)
    assert limiter.remaining_tokens == 5000
    assert abs(limiter.reset_tokens_s - 22.5) < 1e-4
    assert limiter.remaining_requests == 995
    assert abs(limiter.reset_requests_s - 90.0) < 1e-4
    print("✓ test_rate_limiter_logic passed")


def main():
    test_token_estimation()
    test_parse_groq_duration()
    test_parse_review_response_clean_json()
    test_parse_review_response_code_fence()
    test_parse_review_response_surrounding_text()
    test_parse_review_response_empty_and_invalid()
    test_should_skip_file()
    test_diff_splitting_small_file()
    test_diff_splitting_large_file_hunks()
    test_diff_splitting_huge_single_hunk()
    test_format_markdown_report()
    test_rate_limiter_logic()
    print("\nALL OFFLINE TESTS PASSED.")


if __name__ == "__main__":
    main()
