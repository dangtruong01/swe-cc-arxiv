#!/usr/bin/env python3
"""Summarise a results directory: triggering, compliance and resolve rate.

    python scripts/summarize.py [results]              # per scaffold x model x setting
    python scripts/summarize.py results --by category  # also per policy category
    python scripts/summarize.py results --csv out.csv

<results> is what `scripts/export_results.py` writes (default `results/`). Metric
definitions are in `compliance/report/results.py`. Report triggering beside compliance:
an agent that does less work triggers fewer policies and can look more compliant.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compliance.report.results import cell, load, pooled, rates, resolve_rate  # noqa: E402


def fmt(x) -> str:
    return "--" if x is None else f"{x:.1f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", nargs="?", default=ROOT / "results", type=Path)
    ap.add_argument("--by", choices=("category", "project"))
    ap.add_argument("--csv", type=Path, help="also write the summary to this file")
    args = ap.parse_args()

    runs, pol = load(args.results)
    groups = sorted({(r["scaffold"], r["model"], r["setting"]) for r in runs})
    head = ["scaffold", "model", "setting", "runs", "triggering %", "compliance %", "resolve %"]
    body = []
    for s, m, t in groups:
        rs = cell(runs, scaffold=s, model=m, setting=t)
        r = rates(pooled(rs))
        body.append([s, m, t, len(rs), fmt(r["triggering"]), fmt(r["compliance"]),
                     fmt(resolve_rate(rs))])
    if args.by:
        head.insert(3, args.by)
        field = "category" if args.by == "category" else "project"
        values = sorted({p[field] for p in pol.values()})
        body = []
        for s, m, t in groups:
            rs = cell(runs, scaffold=s, model=m, setting=t)
            for v in values:
                keep = lambda pid, v=v: pol[pid][field] == v  # noqa: E731
                r = rates(pooled(rs, keep))
                body.append([s, m, t, v, len(rs), fmt(r["triggering"]), fmt(r["compliance"]),
                             fmt(resolve_rate(rs))])

    widths = [max(len(str(x)) for x in col) for col in zip(head, *body)]
    for line in [head, *body]:
        print("  ".join(str(x).ljust(w) for x, w in zip(line, widths)))
    if args.csv:
        with args.csv.open("w", newline="") as fh:
            csv.writer(fh).writerows([head, *body])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
