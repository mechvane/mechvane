#!/usr/bin/env python3
"""Build and manage Keep a Changelog entries from snippets in changelog.d/.

Usage:
    python3 tools/changelog_build.py --preview
    python3 tools/changelog_build.py --release 0.1.0a20
"""

import argparse
import datetime
from pathlib import Path
import re
import sys

# Canonical Keep a Changelog rubrics order
DEFAULT_RUBRICS = [
    "Added",
    "Changed",
    "Deprecated",
    "Removed",
    "Fixed",
    "Security",
]
RUBRIC_MAP = {r.lower(): r for r in DEFAULT_RUBRICS}


def parse_snippet_text(content: str) -> dict[str, list[str]]:
    """Parse snippet content into {rubric: [item1, item2, ...]}.

    First line is typically one of Added/Changed/Fixed/Removed.
    Subsequent lines contain entries as a Markdown list.
    """
    entries: dict[str, list[str]] = {}
    current_rubric: str | None = None
    curr_item: list[str] = []

    def flush_item():
        if current_rubric and curr_item:
            item_text = "\n".join(curr_item).rstrip()
            if item_text:
                if not re.match(r"^[-*]\s+", item_text):
                    item_text = "- " + item_text
                # Normalize * bullet to -
                if item_text.startswith("* "):
                    item_text = "- " + item_text[2:]
                entries.setdefault(current_rubric, []).append(item_text)
            curr_item.clear()

    for line in content.splitlines():
        stripped = line.strip()
        header_cand = stripped.lstrip("#").rstrip(":").strip()
        if header_cand.lower() in RUBRIC_MAP:
            flush_item()
            current_rubric = RUBRIC_MAP[header_cand.lower()]
            continue
        elif stripped.startswith(("### ", "## ")) and len(stripped.split()) == 2:
            flush_item()
            current_rubric = stripped.lstrip("#").strip().title()
            continue

        if re.match(r"^[-*]\s+", line):
            flush_item()
            curr_item.append(line)
        else:
            if curr_item:
                curr_item.append(line)
            elif stripped:
                if current_rubric is not None:
                    curr_item.append(line)

    flush_item()
    return entries


def parse_snippet_file(path: Path) -> dict[str, list[str]]:
    """Parse a single snippet file."""
    content = path.read_text(encoding="utf-8")
    return parse_snippet_text(content)


def get_snippet_files(changelog_d: Path) -> list[Path]:
    """Return all snippet files in changelog.d (excluding README.md)."""
    if not changelog_d.is_dir():
        return []
    files = [p for p in changelog_d.glob("*.md") if p.name.lower() != "readme.md"]
    # Sort numerically if digit stem, otherwise alphabetically
    return sorted(files, key=lambda p: (0, int(p.stem)) if p.stem.isdigit() else (1, p.name))


def parse_existing_unreleased(changelog_content: str) -> tuple[int, int, str, dict[str, list[str]]]:
    """Find and parse the ## [Unreleased] section in CHANGELOG.md.

    Returns:
        (unreleased_header_start, next_section_start, preamble, rubrics_dict)
    """
    m = re.search(r"^##\s+\[Unreleased\]\s*$", changelog_content, flags=re.MULTILINE | re.IGNORECASE)
    if not m:
        return -1, -1, "", {}

    start = m.start()
    after_header = m.end()

    # Find the next release heading: ## [X.Y.Z] or link definitions
    m2 = re.search(r"^##\s+\[(?!Unreleased\])[^\]]+\]", changelog_content[after_header:], flags=re.MULTILINE)
    if m2:
        end = after_header + m2.start()
    else:
        # Check for link definitions at the bottom
        m_links = re.search(r"^\[[^\]]+\]:\s+https?://", changelog_content[after_header:], flags=re.MULTILINE)
        if m_links:
            end = after_header + m_links.start()
        else:
            end = len(changelog_content)

    unreleased_block = changelog_content[after_header:end]

    rubrics: dict[str, list[str]] = {}
    sections = re.split(r"^###\s+([^\n]+)", unreleased_block, flags=re.MULTILINE)
    preamble = sections[0].strip()

    for i in range(1, len(sections), 2):
        rubric_name = sections[i].strip()
        canonical_rubric = RUBRIC_MAP.get(rubric_name.lower(), rubric_name)
        rubric_text = sections[i + 1]

        items: list[str] = []
        curr_item: list[str] = []
        for line in rubric_text.splitlines():
            if re.match(r"^[-*]\s+", line):
                if curr_item:
                    items.append("\n".join(curr_item).rstrip())
                curr_item = [line]
            elif curr_item:
                curr_item.append(line)
        if curr_item:
            items.append("\n".join(curr_item).rstrip())

        rubrics.setdefault(canonical_rubric, []).extend(items)

    return start, end, preamble, rubrics


def collect_entries(
    changelog_path: Path,
    changelog_d: Path,
) -> tuple[dict[str, list[str]], str, list[Path]]:
    """Collect entries from existing CHANGELOG.md unreleased section and snippets.

    Existing entries under 'Unreleased' in CHANGELOG.md are preserved before snippet entries.
    """
    existing_rubrics: dict[str, list[str]] = {}
    preamble = ""

    if changelog_path.is_file():
        content = changelog_path.read_text(encoding="utf-8")
        _, _, preamble, existing_rubrics = parse_existing_unreleased(content)

    snippet_files = get_snippet_files(changelog_d)
    snippet_rubrics: dict[str, list[str]] = {}
    for sf in snippet_files:
        parsed = parse_snippet_file(sf)
        for rubric, items in parsed.items():
            snippet_rubrics.setdefault(rubric, []).extend(items)

    # Combine: existing entries first, then snippet entries
    all_rubrics_set = set(existing_rubrics.keys()) | set(snippet_rubrics.keys())
    combined: dict[str, list[str]] = {}
    for r in all_rubrics_set:
        items = existing_rubrics.get(r, []) + snippet_rubrics.get(r, [])
        if items:
            combined[r] = items

    return combined, preamble, snippet_files


def get_ordered_rubrics(combined: dict[str, list[str]]) -> list[str]:
    """Order rubrics according to Keep a Changelog canonical order."""
    ordered = [r for r in DEFAULT_RUBRICS if r in combined]
    for r in sorted(combined.keys()):
        if r not in ordered:
            ordered.append(r)
    return ordered


def format_section(
    title: str,
    combined: dict[str, list[str]],
    preamble: str = "",
) -> str:
    """Format a Keep a Changelog section with title, rubrics, and entries."""
    lines = [title]
    if preamble.strip():
        lines.append("")
        lines.append(preamble.strip())

    ordered_rubrics = get_ordered_rubrics(combined)
    for rubric in ordered_rubrics:
        items = combined.get(rubric, [])
        if not items:
            continue
        lines.append("")
        lines.append(f"### {rubric}")
        lines.append("")
        for item in items:
            lines.append(item)

    return "\n".join(lines)


def build_preview(changelog_path: Path, changelog_d: Path) -> str:
    """Build preview of the ## [Unreleased] section."""
    combined, preamble, _ = collect_entries(changelog_path, changelog_d)
    return format_section("## [Unreleased]", combined, preamble)


def release_version(
    version: str,
    changelog_path: Path,
    changelog_d: Path,
    release_date: str | None = None,
) -> None:
    """Release version: write section with date into CHANGELOG.md, clear snippets."""
    ver = version.lstrip("v")
    date_str = release_date or datetime.date.today().isoformat()
    release_title = f"## [{ver}] - {date_str}"

    combined, preamble, snippet_files = collect_entries(changelog_path, changelog_d)
    release_block = format_section(release_title, combined, preamble)

    if changelog_path.is_file():
        content = changelog_path.read_text(encoding="utf-8")
        start, end, _, _ = parse_existing_unreleased(content)
        if start != -1:
            before = content[:start].rstrip()
            after = content[end:].lstrip("\r\n")
            parts = []
            if before:
                parts.append(before)
            parts.append("## [Unreleased]")
            parts.append(release_block)
            if after:
                new_content = "\n\n".join(parts) + "\n\n" + after
            else:
                new_content = "\n\n".join(parts) + "\n"
        else:
            # No ## [Unreleased] found; prepend or append
            new_content = f"## [Unreleased]\n\n{release_block}\n\n" + content
    else:
        new_content = f"# Changelog\n\n## [Unreleased]\n\n{release_block}\n"

    changelog_path.write_text(new_content, encoding="utf-8")

    # Delete snippets
    for sf in snippet_files:
        if sf.is_file():
            sf.unlink()


def main():
    repo_root = Path(__file__).resolve().parent.parent
    default_changelog = repo_root / "CHANGELOG.md"
    default_changelog_d = repo_root / "changelog.d"

    parser = argparse.ArgumentParser(
        description="Build and manage Keep a Changelog entries from changelog.d snippets.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--preview",
        action="store_true",
        help="Print the Unreleased section to stdout (combining existing unreleased items and snippets).",
    )
    group.add_argument(
        "--release",
        metavar="VERSION",
        help="Release the specified version (e.g. 9.9.9), update CHANGELOG.md with date, and delete snippets.",
    )

    parser.add_argument(
        "--changelog",
        type=Path,
        default=default_changelog,
        help=f"Path to CHANGELOG.md (default: {default_changelog})",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=default_changelog_d,
        help=f"Path to changelog.d directory (default: {default_changelog_d})",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Release date in YYYY-MM-DD format (defaults to current date)",
    )

    args = parser.parse_args()

    if args.preview:
        preview_text = build_preview(args.changelog, args.dir)
        print(preview_text)
    elif args.release:
        release_version(args.release, args.changelog, args.dir, args.date)


if __name__ == "__main__":
    main()
