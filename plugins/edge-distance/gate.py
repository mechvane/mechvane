"""Durchstich-Tor U2 (#220): the plugin's hole_edge_distance findings against the reference baselines.

Builds each reference part (tests/reference/*.build.json) in a headless session, runs the plugin on it and
compares its findings
- with the baselines tests/reference/design_rules/<part>.<profile>.json: face, status, value, threshold, point
  and catalog entry, for both profiles (both use the factor 1.5);
- with design_rules.check in the same session: the whole finding (message, location, source with quote);
  the counter-tests in plugins/edge-distance/tests/ have no baseline and are compared with it only.
Prints the plugin's run time per part.
Run with the SolidCraft target version (env SOLIDCRAFT_CLI):
    SOLIDCRAFT_CLI=<path to solidcraft-cli 0.50.0> python3 plugins/edge-distance/gate.py [part ...]
"""
import json
import time
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from mechvane import design_rules  # noqa: E402
from mechvane.solidcraft import Session  # noqa: E402

PARTS = ("flansch", "gehaeuse", "rippenplatte", "fehlerplatte")
# counter-tests without a baseline, only compared with design_rules.check (plugins/edge-distance/tests/)
EXTRA = ("skizzenloch", "scheibe")
PROFILES = ("fdm_0.4", "cnc_alu")
TOL = 0.01


def close(a, b):
    return len(a) == len(b) and all(abs(x - y) <= TOL for x, y in zip(a, b))


def key(f):
    return (f["face"], f["status"])


def expected(part, profile):
    if part in EXTRA:
        return None
    d = json.loads((ROOT / "tests/reference/design_rules" / f"{part}.{profile}.json").read_text(encoding="utf-8"))
    return sorted((f for f in d["findings"] if f["rule"] == "hole_edge_distance"), key=key)


def run_plugin(session, folder, factor):
    insp = session.cmd("plugin.inspect", {"path": folder})
    t0 = time.perf_counter()
    out = session.cmd("plugin.run", {"path": folder, "approval": insp["approval"], "entry": "hole-edge-distance",
                                     "params": {"factor": factor}})
    ms = (time.perf_counter() - t0) * 1000
    res = out.get("result", out)
    if isinstance(res, str):
        res = json.loads(res)
    flat = [dict(f, face=f["location"]["face"]) for f in res["hole_edge_distance"]["findings"]]
    return sorted(flat, key=key), ms


def same_as_baseline(exp, got):
    return len(exp) == len(got) and all(
        a["face"] == b["face"] and a["status"] == b["status"] and abs(a["value"] - b["value"]) <= TOL
        and abs(a["threshold"] - b["threshold"]) <= TOL
        # the pick point model.faces reports differs between platforms; the baselines are from Linux
        and (not sys.platform.startswith("linux") or close(a["point"], b["location"]["point"]))
        and a.get("source") == (b.get("source") or {}).get("entry")
        for a, b in zip(exp, got))


def same_as_check(ref, got):
    """Whole findings equal, numbers to TOL (Python and Rust may differ in the last float digits)."""
    if len(ref) != len(got):
        return False
    for a, b in zip(ref, got):
        b = {k: v for k, v in b.items() if k != "face"}
        if set(a) != set(b) or a["location"]["face"] != b["location"]["face"]:
            return False
        if not close(a["location"]["point"], b["location"]["point"]):
            return False
        if any(a[k] != b[k] for k in ("rule", "status", "message", "source")):
            return False
        if abs(a["value"] - b["value"]) > TOL or abs(a["threshold"] - b["threshold"]) > TOL:
            return False
    return True


def main(parts):
    pkg_src = HERE / "mechvane-edge-distance"
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / "mechvane-edge-distance"
        shutil.copytree(pkg_src, folder, ignore=shutil.ignore_patterns("*.zip", "tests"))
        for part in parts:
            build = HERE / "tests" / f"{part}.build.json" if part in EXTRA else ROOT / f"tests/reference/{part}.build.json"
            commands = json.loads(build.read_text(encoding="utf-8"))["commands"]
            with Session(allow_paths=[tmp]) as s:
                s.batch(commands)
                runs = {}
                for p in PROFILES:
                    factor = design_rules._get_cfg(p)["hole_edge_distance_factor"]
                    if factor not in runs:
                        runs[factor] = run_plugin(s, str(folder), factor)
                runs = {p: runs[design_rules._get_cfg(p)["hole_edge_distance_factor"]] for p in PROFILES}
                ref = {p: sorted((dict(c, face=c["location"]["face"]) for c in design_rules.check(s, p)["checks"]
                                  if c["rule"] == "hole_edge_distance"), key=key) for p in PROFILES}
            for profile in PROFILES:
                got, ms = runs[profile]
                exp = expected(part, profile)
                live = [{k: v for k, v in c.items() if k != "face"} for c in ref[profile]]
                ok_base, ok_check = exp is None or same_as_baseline(exp, got), same_as_check(live, got)
                print(f"{part:12} {profile:8} {'ok ' if ok_base and ok_check else 'DIFF'} plugin {len(got)} / "
                      f"{'check ' + str(len(live)) if exp is None else 'baseline ' + str(len(exp))}{'' if ok_base else ' (baseline differs)'}"
                      f"{'' if ok_check else ' (design_rules.check differs)'}  {ms:.0f} ms")
                if not (ok_base and ok_check):
                    bad += 1
                    for a in exp or []:
                        print("   baseline", a)
                    for a in live:
                        print("   check   ", a)
                    for b in got:
                        print("   plugin  ", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or PARTS + EXTRA))
