#!/usr/bin/env python3
"""Reference design-rule baselines: builds reference parts, runs design_rules.check
for FDM and CNC profiles, and compares findings against tests/reference/design_rules/*.json.

Usage:
    python3 tests/reference/check_design_rules.py [--update] [part ...]
Exit code 0 when every check passes, 1 otherwise."""

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
FIXTURE_DIR = HERE / "design_rules"

sys.path.insert(0, str(REPO_ROOT))

from mechvane import design_rules  # noqa: E402
from mechvane.solidcraft import Session  # noqa: E402

PARTS = ("flansch", "gehaeuse", "rippenplatte", "fehlerplatte")
PROFILES = ("fdm_0.4", "cnc_alu")
VAL_TOL = 0.01    # mm (and dimensionless ratios)
COORD_TOL = 0.01  # mm


def normalize_finding(finding: dict) -> dict:
    """Extract canonical comparison fields from a design_rules check finding."""
    loc = finding.get("location") or {}
    pt = loc.get("point")
    src = finding.get("source")
    if isinstance(src, dict):
        source_id = src.get("entry")
    elif isinstance(src, str):
        source_id = src
    else:
        source_id = None
    out = {
        "rule": finding["rule"],
        "status": finding["status"],
        "value": round(float(finding["value"]), 4) if finding.get("value") is not None else None,
        "threshold": round(float(finding["threshold"]), 4) if finding.get("threshold") is not None else None,
        "point": [round(float(x), 4) for x in pt] if pt is not None else None,
        "source": source_id,
    }
    for key in ("face", "edge", "body"):
        if key in loc:
            out[key] = loc[key]
            break
    return out


def normalize_result(part: str, profile: str, result: dict) -> dict:
    """Convert a design_rules.check() result dict into a canonical baseline payload."""
    findings = [normalize_finding(c) for c in result.get("checks", [])]
    findings.sort(key=lambda f: (
        f["rule"],
        f["status"],
        f["value"] if f["value"] is not None else 0.0,
        f["point"] or [],
    ))
    return {
        "part": part,
        "profile": profile,
        "verdict": result["verdict"],
        "findings": findings,
    }


def fixture_path(part: str, profile: str) -> Path:
    return FIXTURE_DIR / f"{part}.{profile}.json"


def _point_dist(a: list[float] | None, b: list[float] | None) -> float:
    if a is None and b is None:
        return 0.0
    if a is None or b is None or len(a) != len(b):
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _num_match(a: float | None, b: float | None, tol: float) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def _point_match(a: list[float] | None, b: list[float] | None, tol: float) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None or len(a) != len(b):
        return False
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def _fmt_pt(pt: list[float] | None) -> str:
    if pt is None:
        return "None"
    return "[" + ", ".join(f"{x:.4f}" for x in pt) + "]"


def compare_baseline(part: str, profile: str, actual: dict, expected: dict) -> list[str]:
    """Compare normalized actual results against expected baseline; return failure lines."""
    errors = []
    if actual["verdict"] != expected["verdict"]:
        errors.append(
            f"{part:12} FAIL {profile}: verdict = {actual['verdict']!r} (expected {expected['verdict']!r})"
        )

    exp_list = expected["findings"]
    act_list = actual["findings"]
    used_act = set()

    for exp in exp_list:
        candidates = [i for i, a in enumerate(act_list) if i not in used_act and a["rule"] == exp["rule"]]
        if not candidates:
            errors.append(
                f"{part:12} FAIL {profile} {exp['rule']} @{_fmt_pt(exp['point'])}: "
                f"missing finding (expected status={exp['status']!r}, value={exp['value']}, "
                f"threshold={exp['threshold']}, source={exp['source']!r})"
            )
            continue

        def match_key(idx: int):
            a = act_list[idx]
            d_pt = _point_dist(a["point"], exp["point"])
            val_diff = abs((a["value"] or 0.0) - (exp["value"] or 0.0)) if (
                a["value"] is not None and exp["value"] is not None
            ) else (0.0 if a["value"] == exp["value"] else float("inf"))
            return (d_pt > COORD_TOL, round(d_pt, 4), val_diff, 0 if a["status"] == exp["status"] else 1)

        best_idx = min(candidates, key=match_key)
        used_act.add(best_idx)
        act = act_list[best_idx]

        diffs = []
        if act["status"] != exp["status"]:
            diffs.append(f"status={act['status']!r} (expected {exp['status']!r})")
        if not _num_match(act["value"], exp["value"], VAL_TOL):
            diffs.append(f"value={act['value']} (expected {exp['value']})")
        if not _num_match(act["threshold"], exp["threshold"], VAL_TOL):
            diffs.append(f"threshold={act['threshold']} (expected {exp['threshold']})")
        if not _point_match(act["point"], exp["point"], COORD_TOL):
            diffs.append(f"point={_fmt_pt(act['point'])} (expected {_fmt_pt(exp['point'])})")
        if act["source"] != exp["source"]:
            diffs.append(f"source={act['source']!r} (expected {exp['source']!r})")

        if diffs:
            if not any(d.startswith("value=") for d in diffs) and act["value"] is not None:
                diffs.append(f"value={act['value']}")
            errors.append(
                f"{part:12} FAIL {profile} {exp['rule']} @{_fmt_pt(exp['point'])}: {', '.join(diffs)}"
            )

    for i, act in enumerate(act_list):
        if i not in used_act:
            errors.append(
                f"{part:12} FAIL {profile} {act['rule']} @{_fmt_pt(act['point'])}: "
                f"unexpected finding (status={act['status']!r}, value={act['value']}, "
                f"threshold={act['threshold']}, source={act['source']!r})"
            )

    return errors


def run_part(part: str, update: bool = False) -> bool:
    build_path = HERE / f"{part}.build.json"
    commands = json.loads(build_path.read_text(encoding="utf-8"))["commands"]
    ok = True
    with Session() as session:
        session.batch(commands)
        for profile in PROFILES:
            result = design_rules.check(session, profile=profile)
            actual = normalize_result(part, profile, result)
            path = fixture_path(part, profile)
            if update:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(actual, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"{part:12} upd  {profile}: {len(actual['findings'])} findings -> {path.relative_to(REPO_ROOT)}")
                continue
            if not path.is_file():
                print(f"{part:12} FAIL {profile}: missing baseline {path.relative_to(REPO_ROOT)} (run with --update)")
                ok = False
                continue
            expected = json.loads(path.read_text(encoding="utf-8"))
            errors = compare_baseline(part, profile, actual, expected)
            if errors:
                ok = False
                for line in errors:
                    print(line)
            else:
                print(f"{part:12} ok   {profile}: verdict={actual['verdict']}, {len(actual['findings'])} findings")
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check design_rules.check against reference baselines.")
    parser.add_argument("--update", action="store_true", help="Write baseline JSON files from current output.")
    parser.add_argument("parts", nargs="*", help=f"Parts to check (default: {', '.join(PARTS)})")
    args = parser.parse_args(argv)

    parts = args.parts or list(PARTS)
    unknown = [p for p in parts if p not in PARTS]
    if unknown:
        print(f"Unknown part(s): {', '.join(unknown)}. Known: {', '.join(PARTS)}", file=sys.stderr)
        return 1

    results = [run_part(p, update=args.update) for p in parts]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
