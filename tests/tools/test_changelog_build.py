#!/usr/bin/env python3
"""Offline unit tests for tools/changelog_build.py.

Tests:
  - two snippets with different rubrics -> --preview contains both in fixed order.
  - existing entries in CHANGELOG.md under ## [Unreleased] are preserved before snippet entries.
  - --release 9.9.9 writes the section with date, preserves older sections unchanged,
    and deletes the snippets while keeping README.md.

Usage:
  python3 tests/tools/test_changelog_build.py
"""

import datetime
from pathlib import Path
import subprocess
import sys
import tempfile

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.changelog_build import (  # noqa: E402
    build_preview,
    collect_entries,
    parse_snippet_text,
    release_version,
)

BUILD_SCRIPT = REPO_ROOT / "tools" / "changelog_build.py"


def test_preview_contains_both_in_fixed_order():
    """Two snippets with different rubrics -> --preview contains both in fixed order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_d = tmp_path / "changelog.d"
        changelog_d.mkdir()

        changelog_file.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-11-01\n",
            encoding="utf-8",
        )

        # Snippet 1 has rubric 'Fixed' (issue 10)
        (changelog_d / "10.md").write_text(
            "Fixed\n- Fixed bug in sketch constraint solver\n",
            encoding="utf-8",
        )
        # Snippet 2 has rubric 'Added' (issue 20)
        (changelog_d / "20.md").write_text(
            "Added\n- Added revolve keyboard shortcut R\n",
            encoding="utf-8",
        )

        # 1. Test via direct Python function
        preview = build_preview(changelog_file, changelog_d)
        assert "## [Unreleased]" in preview, f"Missing Unreleased: {preview}"
        assert "### Added" in preview, f"Missing Added: {preview}"
        assert "### Fixed" in preview, f"Missing Fixed: {preview}"
        assert "- Added revolve keyboard shortcut R" in preview
        assert "- Fixed bug in sketch constraint solver" in preview

        # Verify fixed canonical order: Added must come before Fixed
        idx_added = preview.index("### Added")
        idx_fixed = preview.index("### Fixed")
        assert idx_added < idx_fixed, f"Expected Added before Fixed, got: {preview}"

        # 2. Test via CLI invocation
        res = subprocess.run(
            [
                sys.executable,
                str(BUILD_SCRIPT),
                "--preview",
                "--changelog",
                str(changelog_file),
                "--dir",
                str(changelog_d),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        cli_out = res.stdout
        assert "## [Unreleased]" in cli_out
        assert "### Added" in cli_out
        assert "### Fixed" in cli_out
        assert cli_out.index("### Added") < cli_out.index("### Fixed")
        assert "- Added revolve keyboard shortcut R" in cli_out
        assert "- Fixed bug in sketch constraint solver" in cli_out

        # Snippets must still exist after preview
        assert (changelog_d / "10.md").is_file()
        assert (changelog_d / "20.md").is_file()
    print("✓ test_preview_contains_both_in_fixed_order passed")


def test_preview_preserves_existing_unreleased_entries_before_snippets():
    """Existing entries under ## [Unreleased] in CHANGELOG.md remain before snippet entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_d = tmp_path / "changelog.d"
        changelog_d.mkdir()

        changelog_file.write_text(
            "# Changelog\n\n"
            "## [Unreleased]\n\n"
            "### Added\n\n"
            "- Existing feature alpha\n\n"
            "## [0.1.0] - 2026-11-01\n",
            encoding="utf-8",
        )

        (changelog_d / "75.md").write_text(
            "Added\n- Snippet feature beta\n",
            encoding="utf-8",
        )

        preview = build_preview(changelog_file, changelog_d)
        assert "- Existing feature alpha" in preview
        assert "- Snippet feature beta" in preview
        idx_alpha = preview.index("- Existing feature alpha")
        idx_beta = preview.index("- Snippet feature beta")
        assert idx_alpha < idx_beta, "Existing unreleased entry must appear before snippet entry"
    print("✓ test_preview_preserves_existing_unreleased_entries_before_snippets passed")


def test_release_writes_section_preserves_older_and_deletes_snippets():
    """--release 9.9.9 writes the section with date, leaves older sections unchanged, deletes snippets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_d = tmp_path / "changelog.d"
        changelog_d.mkdir()

        older_sections = (
            "## [0.1.0a19] - 2026-11-06\n\n"
            "### Fixed\n\n"
            "- Folder mode check.\n\n"
            "## [0.1.0a18] - 2026-11-06\n\n"
            "### Added\n\n"
            "- Sketch environment.\n\n"
            "[0.1.0a19]: https://example.com/compare/v0.1.0a18...v0.1.0a19\n"
        )
        initial_changelog = (
            "# Changelog\n\n"
            "The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
            "## [Unreleased]\n\n"
            "### Changed\n\n"
            "- Existing change in unreleased\n\n"
            + older_sections
        )
        changelog_file.write_text(initial_changelog, encoding="utf-8")

        # Two snippets with different rubrics
        (changelog_d / "10.md").write_text(
            "Fixed\n- Fixed dialog position on dual monitors\n",
            encoding="utf-8",
        )
        (changelog_d / "20.md").write_text(
            "Added\n- Added STEP import browse button\n",
            encoding="utf-8",
        )
        # README.md must NOT be deleted
        (changelog_d / "README.md").write_text(
            "# Changelog Snippets\nDo not delete me.\n",
            encoding="utf-8",
        )

        # Run --release 9.9.9 via CLI
        res = subprocess.run(
            [
                sys.executable,
                str(BUILD_SCRIPT),
                "--release",
                "9.9.9",
                "--changelog",
                str(changelog_file),
                "--dir",
                str(changelog_d),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        today_str = datetime.date.today().isoformat()
        updated_content = changelog_file.read_text(encoding="utf-8")

        # 1. Contains ## [Unreleased] (now empty)
        assert "## [Unreleased]" in updated_content

        # 2. Contains release section with version and date
        expected_release_header = f"## [9.9.9] - {today_str}"
        assert expected_release_header in updated_content

        # 3. Contains all rubrics and items in fixed order (Added, Changed, Fixed)
        idx_rel = updated_content.index(expected_release_header)
        idx_older = updated_content.index("## [0.1.0a19] - 2026-11-06")
        assert idx_rel < idx_older

        rel_section = updated_content[idx_rel:idx_older]
        assert "### Added" in rel_section
        assert "- Added STEP import browse button" in rel_section
        assert "### Changed" in rel_section
        assert "- Existing change in unreleased" in rel_section
        assert "### Fixed" in rel_section
        assert "- Fixed dialog position on dual monitors" in rel_section

        # Fixed order in release section: Added < Changed < Fixed
        assert rel_section.index("### Added") < rel_section.index("### Changed")
        assert rel_section.index("### Changed") < rel_section.index("### Fixed")

        # 4. Older sections remain byte-for-byte identical
        assert updated_content.endswith(older_sections), "Older sections must be preserved verbatim"

        # 5. Snippets are deleted, README.md is preserved
        assert not (changelog_d / "10.md").exists(), "Snippet 10.md should have been deleted"
        assert not (changelog_d / "20.md").exists(), "Snippet 20.md should have been deleted"
        assert (changelog_d / "README.md").is_file(), "README.md must not be deleted"
    print("✓ test_release_writes_section_preserves_older_and_deletes_snippets passed")


def test_snippet_parsing_variations():
    """Test various snippet header formats, markdown styles, and item indentation."""
    # Heading variations
    parsed1 = parse_snippet_text("### Fixed\n- Fix 1\n  continuation line\n- Fix 2")
    assert parsed1 == {"Fixed": ["- Fix 1\n  continuation line", "- Fix 2"]}

    parsed2 = parse_snippet_text("Changed:\n- Change 1")
    assert parsed2 == {"Changed": ["- Change 1"]}

    # Item without bullet dash
    parsed3 = parse_snippet_text("Removed\nRemoved obsolete command")
    assert parsed3 == {"Removed": ["- Removed obsolete command"]}

    # Asterisk bullet
    parsed4 = parse_snippet_text("Added\n* Star bullet")
    assert parsed4 == {"Added": ["- Star bullet"]}
    print("✓ test_snippet_parsing_variations passed")


def test_release_with_date_and_v_prefix():
    """--release with v-prefix (e.g. v9.9.9) and custom --date."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_d = tmp_path / "changelog.d"
        changelog_d.mkdir()

        changelog_file.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n",
            encoding="utf-8",
        )
        (changelog_d / "42.md").write_text(
            "Fixed\n- Fixed an issue\n",
            encoding="utf-8",
        )

        res = subprocess.run(
            [
                sys.executable,
                str(BUILD_SCRIPT),
                "--release",
                "v2.0.0",
                "--date",
                "2026-12-31",
                "--changelog",
                str(changelog_file),
                "--dir",
                str(changelog_d),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        updated = changelog_file.read_text(encoding="utf-8")
        assert "## [2.0.0] - 2026-12-31" in updated, f"Header missing: {updated}"
        assert not (changelog_d / "42.md").exists()
    print("✓ test_release_with_date_and_v_prefix passed")


def main():
    print("Running changelog_build tests...")
    test_preview_contains_both_in_fixed_order()
    test_preview_preserves_existing_unreleased_entries_before_snippets()
    test_release_writes_section_preserves_older_and_deletes_snippets()
    test_snippet_parsing_variations()
    test_release_with_date_and_v_prefix()
    print("All changelog_build tests passed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
