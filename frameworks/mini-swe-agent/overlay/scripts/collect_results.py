#!/usr/bin/env python3
"""Assemble the per-case deliverables into results/summary.{md,json}.

For every instance in cases.txt this gathers:
  1. Problem ID
  2. Execution trajectory (path + key stats: steps, cost, exit status)
  3. Suggested patch from the agent (also dumped to results/patches/<id>.patch)
  4. Whether the patch passes all tests, and WHICH tests fail if not
     (read from the official harness report.json)

Trajectory paths are resolved via results/instance_map.json (instance_id -> traj
path) rather than a fixed filename pattern, since trajectories in this repo don't
all follow one naming convention.

Run AFTER the agent + evaluate_batch.sh:
    python scripts/collect_results.py

Env overrides: CASES (case list), RESULTS_DIR, RUN_GLOB (run_id glob for locating
harness reports; defaults to RUN_PREFIX + "*").
"""
import glob
import json
import os

CASES = os.environ.get("CASES", "cases.txt")
RESULTS = os.environ.get("RESULTS_DIR", "results")
RUN_GLOB = os.environ.get("RUN_GLOB", os.environ.get("RUN_PREFIX", "") + "*")
PATCH_DIR = os.path.join(RESULTS, "patches")
BUNDLE_DIR = os.path.join(RESULTS, "bundles")
MANIFEST = os.path.join(RESULTS, "instance_map.json")


def load_cases():
    with open(CASES) as f:
        return [ln.strip() for ln in f if ln.strip()]


def load_manifest():
    if not os.path.exists(MANIFEST):
        return {}
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def load_trajectory(inst, manifest):
    path = manifest.get(inst)
    if not path or not os.path.exists(path):
        return path, None
    with open(path, encoding="utf-8") as f:
        return path, json.load(f)


def find_report(inst):
    """Newest harness report.json for this instance, across run_ids."""
    hits = glob.glob(f"logs/run_evaluation/{RUN_GLOB}/*/{inst}/report.json")
    if not hits:
        return None
    newest = max(hits, key=os.path.getmtime)
    with open(newest) as f:
        data = json.load(f)
    # report.json is keyed by instance_id
    return data.get(inst, next(iter(data.values()), {}))


def main():
    os.makedirs(PATCH_DIR, exist_ok=True)
    cases = load_cases()
    manifest = load_manifest()
    rows = []

    for inst in cases:
        traj_path, traj = load_trajectory(inst, manifest)
        rec = {
            "instance_id": inst,
            "trajectory": traj_path,
            "ran": traj is not None,
            "exit_status": None,
            "steps": None,
            "cost_usd": None,
            "patch": "",
            "graded": False,
            "patch_applied": None,
            "resolved": None,
            "fail_to_pass_failures": [],
            "pass_to_pass_failures": [],
        }

        if traj is not None:
            info = traj.get("info", {})
            rec["exit_status"] = info.get("exit_status")
            stats = info.get("model_stats", {})
            rec["steps"] = stats.get("api_calls")
            rec["cost_usd"] = round(stats.get("instance_cost", 0) or 0, 4)
            # Since Phase 0 info.submission is the whole evidence bundle, with the
            # patch in its last section. Pre-Phase-0 trajectories have no marker and
            # their submission IS the patch.
            submission = info.get("submission") or ""
            marker = "===PATCH==="
            patch = submission.split(marker, 1)[1].lstrip("\n") if marker in submission else submission
            rec["patch"] = patch
            if patch:
                with open(os.path.join(PATCH_DIR, f"{inst}.patch"), "w", encoding="utf-8") as f:
                    f.write(patch)
            if marker in submission:
                os.makedirs(BUNDLE_DIR, exist_ok=True)
                with open(os.path.join(BUNDLE_DIR, f"{inst}.bundle.txt"), "w", encoding="utf-8") as f:
                    f.write(submission)

        report = find_report(inst)
        if report:
            rec["graded"] = True
            rec["patch_applied"] = report.get("patch_successfully_applied")
            rec["resolved"] = report.get("resolved")
            ts = report.get("tests_status", {})
            rec["fail_to_pass_failures"] = ts.get("FAIL_TO_PASS", {}).get("failure", [])
            rec["pass_to_pass_failures"] = ts.get("PASS_TO_PASS", {}).get("failure", [])

        rows.append(rec)

    # machine-readable
    with open(os.path.join(RESULTS, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    # human-readable report
    resolved = sum(1 for r in rows if r["resolved"])
    graded = sum(1 for r in rows if r["graded"])
    total = len(rows)
    cost = round(sum(r["cost_usd"] or 0 for r in rows), 4)

    def verdict(r):
        if not r["ran"]:
            return "not run"
        if not r["graded"]:
            return "ungraded"
        return "RESOLVED" if r["resolved"] else "not resolved"

    md = [
        "# Reproduction results — SWE-bench Verified (SymPy) + Gemini 2.5 Flash (openrouter)",
        "",
        f"**Resolved {resolved}/{total}** ({graded} graded) · total agent cost ${cost}",
        "",
        "| # | Problem ID | Verdict | Steps | Cost $ | Patch applied | F2P fails | P2P fails |",
        "|---|-----------|---------|-------|--------|---------------|-----------|-----------|",
    ]
    for i, r in enumerate(rows, 1):
        md.append(
            f"| {i} | {r['instance_id']} | {verdict(r)} | {r['steps'] or '-'} | "
            f"{r['cost_usd'] if r['cost_usd'] is not None else '-'} | "
            f"{r['patch_applied'] if r['patch_applied'] is not None else '-'} | "
            f"{len(r['fail_to_pass_failures'])} | {len(r['pass_to_pass_failures'])} |"
        )

    md += ["", "## Per-case detail", ""]
    for r in rows:
        md.append(f"### {r['instance_id']} — {verdict(r)}")
        md.append("")
        md.append(f"- Trajectory: `{r['trajectory']}` (exit `{r['exit_status']}`, "
                  f"{r['steps']} steps, ${r['cost_usd']})")
        if r["fail_to_pass_failures"]:
            md.append(f"- **FAIL_TO_PASS still failing** ({len(r['fail_to_pass_failures'])}):")
            for t in r["fail_to_pass_failures"]:
                md.append(f"    - {t}")
        if r["pass_to_pass_failures"]:
            md.append(f"- **PASS_TO_PASS regressions** ({len(r['pass_to_pass_failures'])}):")
            for t in r["pass_to_pass_failures"]:
                md.append(f"    - {t}")
        if r["graded"] and not r["fail_to_pass_failures"] and not r["pass_to_pass_failures"]:
            md.append("- All target tests pass.")
        md.append(f"- Patch: `{os.path.join(PATCH_DIR, r['instance_id'] + '.patch')}` "
                  f"({len(r['patch'])} chars)")
        md.append("")

    with open(os.path.join(RESULTS, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"wrote {RESULTS}/summary.md and {RESULTS}/summary.json")
    print(f"resolved {resolved}/{total} (graded {graded}), total cost ${cost}")
    print(f"patches dumped under {PATCH_DIR}/")


if __name__ == "__main__":
    main()
