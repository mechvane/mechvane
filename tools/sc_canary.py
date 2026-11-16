#!/usr/bin/env python3
"""SolidCraft canary: test reference and Mechvane test suites against the latest pre-release.

(1) Queries GitHub API for the latest pre-release and latest stable version of tangency-labs/solidcraft.
(2) Downloads and unpacks the Linux x86_64 archive into build/canary/<version>/, checking SHA256
    using functions from mechvane/install.py.
(3) Runs tests/reference/check.py and tests/mechvane/check.py with SOLIDCRAFT_CLI=<path>, timeout 1500 each.
(4) Writes build/canary/report.json and build/canary/report.md: version, total/failed checks per suite,
    names of failed checks, comparison to previous report (new red, new green).
    Exits immediately if the version was already checked.
    Exit code 0 even if checks are red; != 0 only on tool errors.
"""

import argparse
import datetime as dt
import json
import os
import re
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mechvane import install  # noqa: E402


def fetch_releases() -> list[dict]:
    """Fetch releases from GitHub API, filtering out drafts."""
    url = "https://api.github.com/repos/tangency-labs/solidcraft/releases?per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "mechvane-canary",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch releases from GitHub: {e}") from e

    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response from GitHub releases API: {data}")
    return [rel for rel in data if not rel.get("draft")]


def release_timestamp(rel: dict) -> str:
    return rel.get("published_at") or rel.get("created_at") or ""


def get_latest_versions(releases: list[dict]) -> tuple[dict | None, dict | None]:
    """Return (latest_prerelease, latest_stable) sorted by publication date descending."""
    sorted_releases = sorted(releases, key=release_timestamp, reverse=True)
    latest_prerelease = next((r for r in sorted_releases if r.get("prerelease")), None)
    latest_stable = next((r for r in sorted_releases if not r.get("prerelease")), None)
    return latest_prerelease, latest_stable


def find_release(releases: list[dict], version_query: str) -> dict:
    """Find release matching version_query (exact tag, with or without leading 'v')."""
    q = version_query.strip()
    candidates = {q, f"v{q}", q.lstrip("v")}
    for rel in releases:
        tag = rel.get("tag_name", "")
        if tag in candidates or tag.lstrip("v") == q.lstrip("v"):
            return rel

    # Fallback to direct API lookup by tag
    tag_to_try = q if q.startswith("v") else f"v{q}"
    url = f"https://api.github.com/repos/tangency-labs/solidcraft/releases/tags/{tag_to_try}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "mechvane-canary",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Could not find SolidCraft release {version_query} on GitHub (HTTP {e.code})") from e
    except Exception as e:
        raise RuntimeError(f"Failed to fetch release {version_query} from GitHub: {e}") from e


def find_linux_asset(release: dict) -> dict:
    """Find the Linux x86_64 tar.gz asset in the release."""
    assets = release.get("assets", [])
    # 1. Exact pattern solidcraft-*-linux-x86_64.tar.gz
    match = next((a for a in assets if a["name"].startswith("solidcraft-") and a["name"].endswith("-linux-x86_64.tar.gz")), None)
    if match:
        return match
    # 2. Match ending with -linux-x86_64.tar.gz or solidcraft-linux-x86_64.tar.gz
    match = next((a for a in assets if a["name"].endswith("-linux-x86_64.tar.gz") or a["name"] == "solidcraft-linux-x86_64.tar.gz"), None)
    if match:
        return match
    # 3. Any tar.gz containing linux-x86_64
    match = next((a for a in assets if "linux-x86_64" in a["name"] and a["name"].endswith(".tar.gz")), None)
    if match:
        return match
    raise RuntimeError(f"No Linux x86_64 .tar.gz asset found in release {release.get('tag_name')}")


def get_expected_sha256(release: dict, asset_name: str) -> str:
    """Find expected SHA256 checksum from SHA256SUMS.txt asset, falling back to mechvane.install.ASSETS."""
    assets = release.get("assets", [])
    sums_asset = next((a for a in assets if a["name"] == "SHA256SUMS.txt"), None)
    if sums_asset:
        sums_url = sums_asset.get("browser_download_url")
        req = urllib.request.Request(sums_url, headers={"User-Agent": "mechvane-canary"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                sums_content = r.read().decode("utf-8")
            for line in sums_content.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1].lstrip("*") == asset_name:
                    return parts[0]
        except Exception as e:
            print(f"Warning: could not fetch or parse SHA256SUMS.txt: {e}")

    # Fallback to hardcoded ASSETS in mechvane.install
    ver = release.get("tag_name", "").lstrip("v")
    if ver == install.VERSION and ("linux", "x86_64") in install.ASSETS:
        return install.ASSETS[("linux", "x86_64")][1]

    raise RuntimeError(f"Could not determine expected SHA256 for asset {asset_name} in release {release.get('tag_name')}")


def ensure_cli(release: dict, version_dir: Path) -> Path:
    """Ensure SolidCraft CLI for this release is unpacked in version_dir and verified."""
    version_dir.mkdir(parents=True, exist_ok=True)
    exe_name = install.exe_name()
    existing_cli = next((p for p in sorted(version_dir.rglob(exe_name)) if p.is_file()), None)
    if existing_cli and os.access(existing_cli, os.X_OK):
        try:
            res = subprocess.run([str(existing_cli), "--version"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                print(f"Found existing SolidCraft CLI: {existing_cli} ({res.stdout.strip()})")
                return existing_cli
        except Exception:
            pass

    asset = find_linux_asset(release)
    asset_name = asset["name"]
    sha256 = get_expected_sha256(release, asset_name)
    download_url = asset["browser_download_url"]

    archive_target = version_dir / asset_name
    print(f"Downloading {asset_name} ({asset.get('size', 0) // (1024 * 1024)} MB)...")
    install._download(download_url, archive_target, sha256, log=print)

    print(f"Extracting {asset_name} into {version_dir}...")
    install._extract(archive_target, version_dir, asset_name)
    archive_target.unlink(missing_ok=True)

    cli_path = next((p for p in sorted(version_dir.rglob(exe_name)) if p.is_file()), None)
    if cli_path is None:
        raise RuntimeError(f"No {exe_name} found in unpacked archive {asset_name}")

    if sys.platform != "win32":
        for f in cli_path.parent.iterdir():
            if f.is_file():
                f.chmod(f.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    res = subprocess.run([str(cli_path), "--version"], capture_output=True, text=True, timeout=10)
    if res.returncode != 0:
        raise RuntimeError(f"{cli_path} failed to run: {res.stderr}")

    print(f"SolidCraft CLI ready: {cli_path} ({res.stdout.strip()})")
    return cli_path


def collect_known_mechvane_labels() -> set[str]:
    """Parse static ok(...) test labels from tests/mechvane/check.py."""
    check_file = ROOT / "tests" / "mechvane" / "check.py"
    labels = set()
    try:
        import ast
        tree = ast.parse(check_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ok":
                if node.args:
                    arg0 = node.args[0]
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        labels.add(arg0.value)
                    elif isinstance(arg0, ast.JoinedStr):
                        prefix = ""
                        for v in arg0.values:
                            if isinstance(v, ast.Constant):
                                prefix += str(v.value)
                            else:
                                break
                        if prefix:
                            labels.add(prefix)
    except Exception as e:
        print(f"Warning: could not parse static labels from check.py: {e}")
    return labels


def extract_mechvane_label(rest: str, known_labels: set[str]) -> str:
    """Extract check label from 'FAIL <label>: <detail>' or 'FAIL <label>'."""
    if rest in known_labels:
        return rest
    # Direct match on known label + ": "
    candidates = [kl for kl in known_labels if rest.startswith(kl + ": ") or rest == kl]
    if candidates:
        return max(candidates, key=len)
    # Match known prefix
    prefix_candidates = [kl for kl in known_labels if rest.startswith(kl)]
    if prefix_candidates:
        matched = max(prefix_candidates, key=len)
        after_prefix = rest[len(matched):]
        if ": " in after_prefix:
            return matched + after_prefix.split(": ", 1)[0]
        return rest
    if ": " in rest:
        return rest.split(": ", 1)[0]
    return rest


def run_reference_suite(cli_path: Path, timeout: int = 1500) -> dict:
    """Run tests/reference/check.py with SOLIDCRAFT_CLI=<cli_path> and timeout."""
    script_path = ROOT / "tests" / "reference" / "check.py"
    env = os.environ.copy()
    env["SOLIDCRAFT_CLI"] = str(cli_path.resolve())

    passed: list[str] = []
    failed: list[str] = []

    print(f"\n--- Running Reference Suite ({script_path}) (timeout {timeout}s) ---")
    proc = subprocess.Popen(
        [sys.executable, str(script_path)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    t0 = time.time()
    try:
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if not line:
                time.sleep(0.05)
                continue
            line_str = line.strip()
            print(f"  [reference] {line_str}")

            m = re.match(r"^(\S+)\s+(ok|FAIL)\s+(.+?):\s+(\S+)\s+=", line_str)
            if m:
                part, status, label, kind = m.group(1), m.group(2), m.group(3), m.group(4)
                check_name = f"{part} {label} ({kind})"
                if status == "ok":
                    passed.append(check_name)
                else:
                    failed.append(check_name)
            elif ": BUILD FAILED" in line_str or line_str.endswith("BUILD FAILED"):
                part = line_str.split(":")[0].strip()
                failed.append(f"{part} (build)")

            if time.time() - t0 > timeout:
                proc.kill()
                failed.append(f"reference suite timed out after {timeout}s")
                break
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()

    ret = proc.returncode
    if ret != 0 and not failed and not passed:
        failed.append(f"reference suite process exited with code {ret}")

    total = len(passed) + len(failed)
    print(f"Reference suite finished: {total} total, {len(failed)} failed, {len(passed)} passed.")
    return {
        "total": total,
        "failed": len(failed),
        "failures": failed,
    }


def run_mechvane_suite(cli_path: Path, timeout: int = 1500) -> dict:
    """Run tests/mechvane/check.py with SOLIDCRAFT_CLI=<cli_path> and timeout."""
    script_path = ROOT / "tests" / "mechvane" / "check.py"
    known_labels = collect_known_mechvane_labels()
    env = os.environ.copy()
    env["SOLIDCRAFT_CLI"] = str(cli_path.resolve())

    passed: list[str] = []
    failed: list[str] = []
    all_lines: list[str] = []
    reported_failures = None

    print(f"\n--- Running Mechvane Suite ({script_path}) (timeout {timeout}s) ---")
    proc = subprocess.Popen(
        [sys.executable, str(script_path)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    t0 = time.time()
    try:
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if not line:
                time.sleep(0.05)
                continue
            line_str = line.strip()
            all_lines.append(line_str)
            print(f"  [mechvane] {line_str}")

            if line_str.startswith("ok   "):
                check_name = line_str[5:].strip()
                passed.append(check_name)
            elif line_str.startswith("FAIL "):
                rest = line_str[5:].strip()
                check_name = extract_mechvane_label(rest, known_labels)
                failed.append(check_name)
            else:
                m = re.search(r"^(\d+)\s+failure\(s\)", line_str)
                if m:
                    reported_failures = int(m.group(1))

            if time.time() - t0 > timeout:
                proc.kill()
                failed.append(f"mechvane suite timed out after {timeout}s")
                break
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()

    ret = proc.returncode
    if ret != 0 and reported_failures is None:
        exc_line = "process exited abnormally"
        for l in reversed(all_lines):
            if l and not l.startswith("File ") and not l.startswith("Traceback") and ("Error" in l or "Exception" in l):
                exc_line = l
                break
            elif l and not l.startswith("File ") and not l.startswith("Traceback") and not l.startswith("main()") and not l.startswith("~"):
                exc_line = l
                break
        failed.append(f"suite crash: {exc_line}")
    elif reported_failures is not None and reported_failures > len(failed):
        diff = reported_failures - len(failed)
        for i in range(diff):
            failed.append(f"unhandled check failure #{i + 1} ({reported_failures} failures reported)")
    elif ret != 0 and not failed and not passed:
        failed.append(f"mechvane suite process exited with code {ret}")

    total = len(passed) + len(failed)
    print(f"Mechvane suite finished: {total} total, {len(failed)} failed, {len(passed)} passed.")
    return {
        "total": total,
        "failed": len(failed),
        "failures": failed,
    }


def generate_reports(
    version_tag: str,
    release: dict,
    latest_stable: dict | None,
    latest_prerelease: dict | None,
    suites: dict,
    canary_dir: Path,
    version_dir: Path,
) -> tuple[dict, str]:
    """Compare with previous report if available and generate report.json and report.md."""
    report_json_path = canary_dir / "report.json"
    prev_report = None
    if report_json_path.is_file():
        try:
            prev_report = json.loads(report_json_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Warning: could not parse existing report.json: {e}")

    prev_version = prev_report.get("version") if prev_report else None

    # Compute comparison
    all_new_red = []
    all_new_green = []
    for s_name, s_data in suites.items():
        prev_failures = set(prev_report.get("suites", {}).get(s_name, {}).get("failures", [])) if prev_report else set()
        curr_failures = set(s_data["failures"])
        new_red = sorted(curr_failures - prev_failures)
        new_green = sorted(prev_failures - curr_failures)
        s_data["new_red"] = new_red
        s_data["new_green"] = new_green
        all_new_red.extend([f"{s_name}: {f}" for f in new_red])
        all_new_green.extend([f"{s_name}: {f}" for f in new_green])

    comparison = {
        "previous_version": prev_version,
        "new_red": all_new_red,
        "new_green": all_new_green,
    }

    report_data = {
        "version": version_tag,
        "latest_stable": latest_stable.get("tag_name") if latest_stable else None,
        "latest_prerelease": latest_prerelease.get("tag_name") if latest_prerelease else None,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "suites": suites,
        "comparison": comparison,
    }

    # Markdown report in German
    lines = [
        f"# SolidCraft-Kanarienvogel-Bericht: {version_tag}",
        "",
        f"- **Geprüfte Version:** {version_tag} ({'Vorabversion' if release.get('prerelease') else 'Stabile Version'})",
        f"- **Neueste stabile Version:** {latest_stable.get('tag_name') if latest_stable else 'unbekannt'}",
        f"- **Neueste Vorabversion:** {latest_prerelease.get('tag_name') if latest_prerelease else 'unbekannt'}",
        f"- **Zeitstempel:** {report_data['timestamp']}",
        f"- **Vergleichsversion:** {prev_version if prev_version else 'keine (erster Bericht)'}",
        "",
        "## Zusammenfassung je Suite",
        "",
        "| Suite | Prüfungen gesamt | Fehlgeschlagen | Bestanden | Neu rot | Neu grün |",
        "|---|---|---|---|---|---|",
    ]

    total_checks = sum(s["total"] for s in suites.values())
    total_failed = sum(s["failed"] for s in suites.values())
    total_passed = total_checks - total_failed

    for s_name, s_data in suites.items():
        s_passed = s_data["total"] - s_data["failed"]
        lines.append(
            f"| {s_name} | {s_data['total']} | {s_data['failed']} | {s_passed} | {len(s_data['new_red'])} | {len(s_data['new_green'])} |"
        )
    lines.append(
        f"| **Gesamt** | {total_checks} | {total_failed} | {total_passed} | {len(all_new_red)} | {len(all_new_green)} |"
    )

    lines.extend([
        "",
        f"## Vergleich zum letzten Bericht ({prev_version if prev_version else 'keiner'})",
        "",
        f"### Neu rot ({len(all_new_red)})",
    ])
    if all_new_red:
        for item in all_new_red:
            lines.append(f"- {item}")
    else:
        lines.append("- (keine)")

    lines.extend([
        "",
        f"### Neu grün ({len(all_new_green)})",
    ])
    if all_new_green:
        for item in all_new_green:
            lines.append(f"- {item}")
    else:
        lines.append("- (keine)")

    lines.extend([
        "",
        "## Fehlgeschlagene Prüfungen je Suite",
    ])
    for s_name, s_data in suites.items():
        lines.extend([
            "",
            f"### Suite: {s_name} ({s_data['failed']})",
        ])
        if s_data["failures"]:
            for item in s_data["failures"]:
                lines.append(f"- {item}")
        else:
            lines.append("- (keine)")

    report_md_content = "\n".join(lines) + "\n"
    return report_data, report_md_content


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SolidCraft Canary: test reference and Mechvane suites against SolidCraft releases."
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="SolidCraft version/tag to test (e.g. v0.30.1). Defaults to the latest pre-release.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run checks even if this version was already checked.",
    )
    args = parser.parse_args()

    canary_dir = ROOT / "build" / "canary"
    canary_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching SolidCraft releases from GitHub...")
    releases = fetch_releases()
    latest_prerelease, latest_stable = get_latest_versions(releases)

    print(f"Latest pre-release: {latest_prerelease.get('tag_name') if latest_prerelease else 'none'}")
    print(f"Latest stable:      {latest_stable.get('tag_name') if latest_stable else 'none'}")

    if args.version:
        target_release = find_release(releases, args.version)
    else:
        if latest_prerelease is None:
            raise RuntimeError("No pre-release found for tangency-labs/solidcraft on GitHub")
        target_release = latest_prerelease

    version_tag = target_release["tag_name"]
    version_dir = canary_dir / version_tag
    print(f"Target version: {version_tag} ({'pre-release' if target_release.get('prerelease') else 'stable'})")

    # Check if already checked
    version_report_path = version_dir / "report.json"
    latest_report_path = canary_dir / "report.json"
    already_checked = False
    if version_report_path.is_file():
        already_checked = True
    elif latest_report_path.is_file():
        try:
            data = json.loads(latest_report_path.read_text(encoding="utf-8"))
            if data.get("version") == version_tag:
                already_checked = True
        except Exception:
            pass

    if already_checked and not args.force:
        print(f"Version {version_tag} has already been checked. Exiting.")
        return 0

    # Ensure SolidCraft CLI binary is available
    cli_path = ensure_cli(target_release, version_dir)

    # Run reference suite and mechvane suite
    ref_results = run_reference_suite(cli_path, timeout=1500)
    mv_results = run_mechvane_suite(cli_path, timeout=1500)

    suites = {
        "reference": ref_results,
        "mechvane": mv_results,
    }

    # Generate and write reports
    report_data, report_md = generate_reports(
        version_tag=version_tag,
        release=target_release,
        latest_stable=latest_stable,
        latest_prerelease=latest_prerelease,
        suites=suites,
        canary_dir=canary_dir,
        version_dir=version_dir,
    )

    report_json_str = json.dumps(report_data, indent=2, ensure_ascii=False) + "\n"
    (canary_dir / "report.json").write_text(report_json_str, encoding="utf-8")
    (canary_dir / "report.md").write_text(report_md, encoding="utf-8")

    (version_dir / "report.json").write_text(report_json_str, encoding="utf-8")
    (version_dir / "report.md").write_text(report_md, encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"Canary check completed for SolidCraft {version_tag}")
    print(f"Reference suite: {ref_results['total']} total, {ref_results['failed']} failed")
    print(f"Mechvane suite:  {mv_results['total']} total, {mv_results['failed']} failed")
    print(f"New red:   {len(report_data['comparison']['new_red'])}")
    print(f"New green: {len(report_data['comparison']['new_green'])}")
    print(f"Report written to:\n  {canary_dir / 'report.json'}\n  {canary_dir / 'report.md'}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"\nCanary tool error: {exc}", file=sys.stderr)
        sys.exit(2)
