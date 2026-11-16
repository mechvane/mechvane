#!/usr/bin/env python3
"""Parameter fuzzing test for reference parts and assemblies.

Fuzzes parameters of parts and assemblies within +/-30% range over multiple
reproducible rounds to verify model integrity without AI assistance.

Checks per round:
(1) No feature_errors, or the error is explained (explanation present);
(2) Exact same body count as before;
(3) Volume > 0 and continuous (no jump over factor 3 at +/-30%);
(4) For assemblies: update_links reports no joint on another face, check_joints without new error;
(5) Resetting parameters yields the initial volume within 1e-6 relatively.

Usage:
    python3 tests/fuzz/param_fuzz.py [--seed SEED] [--rounds ROUNDS] [--part PART]
"""

import argparse
import json
import os
import random
import sys
import tempfile
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from mechvane import examples, links, modeling, sc_errors  # noqa: E402
from mechvane.documents import ASSEMBLY, PART, Workspace  # noqa: E402
from mechvane.ui.server import collect_params  # noqa: E402

REF_DIR = REPO_ROOT / "tests" / "reference"
BUILD_FUZZ_DIR = REPO_ROOT / "build" / "fuzz"
FINDINGS_PATH = BUILD_FUZZ_DIR / "findings.jsonl"

REFERENCE_PARTS = [
    "blechwinkel",
    "flansch",
    "gehaeuse",
    "rippenplatte",
    "rohrhalter",
    "scharnier",
    "welle",
]

ASSEMBLY_TARGETS = [
    "bolted_plates",
]

ALL_TARGETS = REFERENCE_PARTS + ASSEMBLY_TARGETS


def get_fuzz_pool(doc):
    """Return parameters eligible for fuzzing in a document."""
    all_p = collect_params(doc).get("parameters", [])
    # Prefer explicit user parameters or favorites when available
    user_p = [p for p in all_p if p.get("source") == "user" or p.get("favorite")]
    if user_p:
        candidates = user_p
    else:
        # Otherwise use parameters with numeric values
        candidates = [p for p in all_p if isinstance(p.get("value"), (int, float))]
    # Sort deterministically
    return sorted(candidates, key=lambda p: p["name"])


def format_mutated_expression(param, factor: float) -> str:
    """Format mutated expression value within +/-30%."""
    val = param["value"] * (1.0 + factor)
    unit = (param.get("unit") or "").strip()
    if not unit and float(param.get("value", 0)).is_integer():
        return str(max(1, int(round(val))))
    return f"{val:.4f} {unit}".strip()


def run_target_round(target: str, round_idx: int, rng: random.Random, seed: int) -> list[dict]:
    """Execute a single fuzzing round for target, returning any findings."""
    findings = []
    is_assembly = target in ASSEMBLY_TARGETS

    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        if is_assembly:
            if target == "bolted_plates":
                main_doc = examples.bolted_plates(ws)
            else:
                raise ValueError(f"Unknown assembly example: {target}")

            # Collect custom part documents in the assembly (exclude standard parts)
            custom_parts = [
                d for d in ws.docs.values()
                if d.kind == PART and not (d.metadata() or {}).get("standard")
            ]
            custom_parts.sort(key=lambda d: d.name)

            fuzz_pool = []
            for p_doc in custom_parts:
                for p in get_fuzz_pool(p_doc):
                    fuzz_pool.append((p_doc, p))
            fuzz_pool.sort(key=lambda item: (item[0].name, item[1]["name"]))
        else:
            main_doc = ws.new(PART, target)
            build_file = REF_DIR / f"{target}.build.json"
            cmds = json.loads(build_file.read_text(encoding="utf-8"))["commands"]
            main_doc.session.batch(cmds)
            main_doc.save()
            fuzz_pool = [(main_doc, p) for p in get_fuzz_pool(main_doc)]
            fuzz_pool.sort(key=lambda item: item[1]["name"])

        if not fuzz_pool:
            return findings

        # Measure initial state
        insp0 = main_doc.session.cmd("document.inspect", {"measure": True})
        bodies0 = insp0.get("bodies", [])
        v0 = sum(b.get("volume_mm3", 0.0) for b in bodies0)
        n0 = len(bodies0)

        bad_j0 = {}
        if is_assembly:
            j0 = links.check(ws, main_doc)
            bad_j0 = {(j["joint"], j["side"]): j.get("status") for j in j0 if j.get("status") != "ok"}

        # Select 1 to 3 parameters
        k = rng.randint(1, min(3, len(fuzz_pool)))
        chosen = rng.sample(fuzz_pool, k)

        by_doc = {}
        params_record = {}
        for doc, p in chosen:
            factor = rng.uniform(-0.30, 0.30)
            new_expr = format_mutated_expression(p, factor)
            by_doc.setdefault(doc, {})[p["name"]] = (new_expr, p["expression"])
            key = f"{doc.name}.{p['name']}" if is_assembly else p["name"]
            params_record[key] = new_expr

        # (1) Apply mutation and check feature errors
        for doc, changes in by_doc.items():
            mut_dict = {name: pair[0] for name, pair in changes.items()}
            try:
                res = modeling.run_commands(doc, [{"command": "parameters.change", "params": {"changes": mut_dict}}])
                doc.save()
                for fe in res.get("feature_errors") or []:
                    exp = fe.get("explanation") or fe.get("message") or sc_errors.explain(fe.get("error", ""))
                    if not exp:
                        findings.append({
                            "part": target,
                            "seed": seed,
                            "round": round_idx,
                            "params": params_record,
                            "parameters": params_record,
                            "message": f"Unexplained feature error in {fe.get('feature')}: {fe.get('error')}",
                        })
            except Exception as e:
                exp = getattr(e, "explanation", None) or sc_errors.explain(e)
                if not exp:
                    findings.append({
                        "part": target,
                        "seed": seed,
                        "round": round_idx,
                        "params": params_record,
                        "parameters": params_record,
                        "message": f"Unexplained error during parameters.change: {e}",
                    })

        # (4) For assemblies: update_links reports no joint on another face, check_joints without new error
        if is_assembly:
            ul = links.update_links(ws, main_doc, repair_moved=False)
            for j in ul.get("joints", []):
                now_on = j.get("now_on")
                face = j.get("face")
                j_name = j.get("joint")
                if now_on and now_on != face and links._base(now_on) != links._base(face):
                    findings.append({
                        "part": target,
                        "seed": seed,
                        "round": round_idx,
                        "params": params_record,
                        "parameters": params_record,
                        "message": f"update_links: Joint {j_name} moved to different face: {now_on} (was {face})",
                    })

            cj = links.check(ws, main_doc)
            bad_cj = {(j["joint"], j["side"]): j.get("status") for j in cj if j.get("status") != "ok"}
            for jkey, st in bad_cj.items():
                if jkey not in bad_j0:
                    findings.append({
                        "part": target,
                        "seed": seed,
                        "round": round_idx,
                        "params": params_record,
                        "parameters": params_record,
                        "message": f"check_joints: new error for joint {jkey[0]} side {jkey[1]}: status is {st}",
                    })

        # Measure after change
        insp1 = main_doc.session.cmd("document.inspect", {"measure": True})
        bodies1 = insp1.get("bodies", [])
        v1 = sum(b.get("volume_mm3", 0.0) for b in bodies1)
        n1 = len(bodies1)

        # (2) Exactly as many bodies as before
        if n1 != n0:
            findings.append({
                "part": target,
                "seed": seed,
                "round": round_idx,
                "params": params_record,
                "parameters": params_record,
                "message": f"Body count changed from {n0} to {n1}",
            })

        # (3) Volume > 0 and continuous (no jump over factor 3 at +/-30%)
        if v1 <= 0:
            findings.append({
                "part": target,
                "seed": seed,
                "round": round_idx,
                "params": params_record,
                "parameters": params_record,
                "message": f"Volume <= 0 after parameter change: {v1}",
            })
        elif v0 > 0 and (v1 > 3.0 * v0 or v1 < v0 / 3.0):
            findings.append({
                "part": target,
                "seed": seed,
                "round": round_idx,
                "params": params_record,
                "parameters": params_record,
                "message": f"Volume jump factor > 3: initial {v0:.1f}, new {v1:.1f}",
            })

        # (5) Resetting parameters yields initial volume within 1e-6 relatively
        for doc, changes in by_doc.items():
            revert_dict = {name: pair[1] for name, pair in changes.items()}
            try:
                modeling.run_commands(doc, [{"command": "parameters.change", "params": {"changes": revert_dict}}])
                doc.save()
            except Exception as e:
                findings.append({
                    "part": target,
                    "seed": seed,
                    "round": round_idx,
                    "params": params_record,
                    "parameters": params_record,
                    "message": f"Failed to reset parameters in {doc.name}: {e}",
                })

        if is_assembly:
            links.update_links(ws, main_doc, repair_moved=False)

        insp2 = main_doc.session.cmd("document.inspect", {"measure": True})
        bodies2 = insp2.get("bodies", [])
        v2 = sum(b.get("volume_mm3", 0.0) for b in bodies2)
        rel_diff = abs(v2 - v0) / v0 if v0 > 0 else abs(v2 - v0)
        if rel_diff > 1e-6:
            findings.append({
                "part": target,
                "seed": seed,
                "round": round_idx,
                "params": params_record,
                "parameters": params_record,
                "message": f"Reset volume mismatch: initial {v0:.4f}, reset {v2:.4f}, relative diff {rel_diff:.2e} > 1e-6",
            })

    return findings


def main():
    parser = argparse.ArgumentParser(description="Parameter fuzzing test for reference parts and assemblies")
    parser.add_argument("--seed", type=int, default=1, help="Random seed for reproducible fuzzing (default: 1)")
    parser.add_argument("--rounds", type=int, default=20, help="Number of fuzzing rounds per part (default: 20)")
    parser.add_argument("--part", type=str, default=None, help="Specific target to fuzz (default: all targets)")
    args = parser.parse_args()

    if args.part:
        part_name = args.part.replace(".build.json", "").strip()
        if part_name not in ALL_TARGETS:
            print(f"Error: Unknown target {args.part!r}. Available targets: {', '.join(ALL_TARGETS)}", file=sys.stderr)
            sys.exit(2)
        targets = [part_name]
    else:
        targets = list(ALL_TARGETS)

    BUILD_FUZZ_DIR.mkdir(parents=True, exist_ok=True)
    all_findings = []

    with open(FINDINGS_PATH, "w", encoding="utf-8") as findings_file:
        for target in targets:
            rng = random.Random(args.seed)
            for r in range(args.rounds):
                r_findings = run_target_round(target, r, rng, args.seed)
                if r_findings:
                    status = f"FINDING ({len(r_findings)})"
                    for f in r_findings:
                        all_findings.append(f)
                        findings_file.write(json.dumps(f, ensure_ascii=False) + "\n")
                        findings_file.flush()
                        print(f"[{target:14}] round {r}/{args.rounds}: {f['message']} (params: {f['params']})")
                else:
                    print(f"[{target:14}] round {r}/{args.rounds}: ok")

    total_rounds = len(targets) * args.rounds
    print(f"\nCompleted {total_rounds} rounds across {len(targets)} target(s).")
    print(f"Total findings: {len(all_findings)} (written to {FINDINGS_PATH})")

    if all_findings:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
