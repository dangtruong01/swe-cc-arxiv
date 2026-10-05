#!/usr/bin/env python3
"""Compact a directory of scored runs into the released results.

    python scripts/export_results.py --runs <runs-dir> [--out results] [--jobs 8]

<runs-dir> is laid out as the sweep scripts write it:

    <runs-dir>/<project-slug>/<scaffold>/<model>/<instance_id>/<naive|guided>/attempt1/
        trajectory.json  patch.diff  rows.jsonl  eval_report.json  run.log  probe.txt ...

Writes three files, which are all `scripts/summarize.py` and `paper/make_tables.py` read:

    results/runs.csv          one line per run: resolve verdict, evaluation gap, retrieval
    results/verdicts.csv.gz   one line per (run, policy): pass | fail | withheld | not_triggered
    results/policies.csv      one line per policy: project, category, evidence type, exact

Only rows of the run's own project are kept. Retrieval (Table 5) is read from the
trajectory, so this step needs the full runs; everything downstream needs only these files.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compliance import naming  # noqa: E402


# Causes of a missing functional verdict, read from run.log; first match wins (Figure 6).
LOG_CAUSES = [
    ("Agent did not finish", r"got stuck"),                     # OpenHands loop detector
    ("Agent did not finish", r"timed out after 3600"),          # run cap
    ("Environment & other", r"ghcr\.io|failed to become healthy|apt|name resolution|build failed"),
    ("Provider error", r"ended with error|Server disconnected"),
]


def policy_table() -> list[dict]:
    """Every scored policy with the metadata the tables group by."""
    import importlib

    from compliance import cli
    from compliance.core import registry

    for modules in cli.RULE_MODULES.values():
        for m in modules:
            importlib.import_module(m)
    checkers = {r.id: r for r in registry.registered()}
    out = []
    for slug in sorted(naming.PROJECTS):
        corpus = registry.load_corpus(registry.corpus_path_for(slug))
        for pid in registry.in_batch(corpus):
            p, c = corpus[pid], checkers[pid]
            out.append({
                "policy_id": pid,
                "project": naming.PROJECTS[slug],
                "category": p.shared_category,
                "evidence_type": naming.EVIDENCE_TYPES[p.check_tier],
                "check": "approximate" if c.heuristic else "exact",
                "human_in_the_loop": int(c.by_construction),
                "policy": p.atomic_rule,
            })
    return out


def gap_cause(run_dir: Path, instance: str) -> str:
    """Why a run has no functional verdict (Appendix C.1, Figure 6)."""
    patch = run_dir / "patch.diff"
    size = patch.stat().st_size if patch.exists() else -1
    if instance == "psf__requests-1142" and size > 1:
        return "Malformed output"        # build output in the patch clashes with the test patch
    if 0 <= size <= 1:
        return "Empty patch"
    if size < 0:
        log = (run_dir / "run.log").read_text(errors="ignore") if (run_dir / "run.log").exists() else ""
        for label, pattern in LOG_CAUSES:
            if re.search(pattern, log):
                return label
        return "Empty patch"
    return "Environment & other"


def retrieval(run_dir: Path, slug: str, condition: str) -> dict:
    """Table 5: did the policies reach the model's context?"""
    from compliance.bundle.builder import build_bundle
    from compliance.core import registry
    from compliance.core.retrieval import analyse, analyse_rules_file, source_urls_from_corpus

    traj = run_dir / "trajectory.json"
    out = {"attempted": "", "retrieved": "", "opened": "", "delivered": ""}
    if not traj.exists():
        return out
    bundle = build_bundle(traj)
    if condition == "naive":
        urls = source_urls_from_corpus(registry.load_corpus(registry.corpus_path_for(slug)))
        r = analyse(bundle, urls)
        out["attempted"], out["retrieved"] = int(r.fetch_succeeded), int(r.rules_obtained)
    else:
        g = analyse_rules_file(bundle)
        # Delivered is unknown, not 0%, when the run did not record the file's size.
        out["opened"] = int(g.opened)
        out["delivered"] = round(g.coverage, 4) if g.opened and g.file_chars else ""
    return out


def one_run(args: tuple) -> tuple[dict, list[tuple[str, str]]]:
    slug, scaffold, model, instance, condition, run_dir = args
    run_dir = Path(run_dir)
    rows = []
    rows_file = run_dir / "rows.jsonl"
    parse_error = False
    if rows_file.exists():
        for line in rows_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            # Keep the run's own project only: a batch scorer that does not clear the
            # registry between projects adds other projects' policies to a run.
            if row["rule_id"].rsplit("-C", 1)[0].lower() != slug:
                continue
            parse_error |= row.get("status") == "parse_error"
            rows.append((row["rule_id"], naming.outcome(row)))

    resolved, verdict = 0, 0
    report = run_dir / "eval_report.json"
    if report.exists():
        try:
            v = next(iter(json.loads(report.read_text()).values()), {})
            verdict, resolved = 1, int(bool(v.get("resolved")))
        except (json.JSONDecodeError, StopIteration):
            pass
    if not verdict:
        gap = gap_cause(run_dir, instance)
    elif parse_error:
        gap = "Malformed output"
    else:
        gap = ""

    run = {
        "project": naming.PROJECTS[slug], "scaffold": scaffold, "model": model,
        "instance_id": instance, "setting": naming.SETTINGS[condition],
        "resolved": resolved, "functional_verdict": verdict,
        "compliance_withheld_unparsed": int(parse_error), "evaluation_gap": gap,
        **retrieval(run_dir, slug, condition),
    }
    return run, rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", required=True, type=Path)
    ap.add_argument("--out", default=ROOT / "results", type=Path)
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()

    cells = []
    for slug in sorted(naming.PROJECTS):
        for model_dir in sorted((args.runs / slug).glob("*/*")):
            scaffold, model = model_dir.parent.name, model_dir.name
            for inst_dir in sorted(model_dir.glob("*")):
                for condition in ("naive", "guided"):
                    d = inst_dir / condition / "attempt1"
                    if d.is_dir():
                        cells.append((slug, scaffold, model, inst_dir.name, condition, str(d)))
    print(f"{len(cells)} runs", file=sys.stderr)

    args.out.mkdir(parents=True, exist_ok=True)
    policies = policy_table()
    with (args.out / "policies.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(policies[0]))
        w.writeheader()
        w.writerows(policies)

    with ProcessPoolExecutor(args.jobs) as pool:
        results = list(pool.map(one_run, cells, chunksize=16))

    with (args.out / "runs.csv").open("w", newline="") as fh, \
            gzip.open(args.out / "verdicts.csv.gz", "wt", newline="") as gz:
        w = csv.DictWriter(fh, fieldnames=["run", *results[0][0]])
        w.writeheader()
        v = csv.writer(gz)
        v.writerow(["run", "policy_id", "outcome"])
        for i, (run, rows) in enumerate(results):
            w.writerow({"run": i, **run})
            v.writerows((i, pid, o) for pid, o in rows)
    print(f"wrote {args.out}/runs.csv, verdicts.csv.gz, policies.csv", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
