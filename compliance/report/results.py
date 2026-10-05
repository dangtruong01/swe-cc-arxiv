"""Released-results format: read it, and compute the three rates from it.

A results directory, as written by `scripts/export_results.py`, holds

    runs.csv          one line per run
    verdicts.csv.gz   one line per (run, policy): pass | fail | withheld | not_triggered
    policies.csv      one line per policy

Definitions (paper Section 3.5, Appendix C.4). For a set of (run, policy) outcomes:

    triggering rate = (pass + fail + withheld) / all outcomes
    compliance rate = pass / (pass + fail)
    resolve rate    = resolved runs / runs      (a run without a functional verdict is unresolved)

These are the same quantities `compliance.report.aggregate.summarise` computes from rows.
"""

from __future__ import annotations

import csv
import gzip
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Iterable, Optional


def load(results: Path) -> tuple[list[dict], dict[str, dict]]:
    """(runs, policies by id); each run carries its outcomes as [(policy_id, outcome)]."""
    results = Path(results)
    runs = list(csv.DictReader((results / "runs.csv").open()))
    policies = {p["policy_id"]: p for p in csv.DictReader((results / "policies.csv").open())}
    outcomes: dict[int, list[tuple[str, str]]] = defaultdict(list)
    with gzip.open(results / "verdicts.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            outcomes[int(r["run"])].append((r["policy_id"], r["outcome"]))
    for r in runs:
        r["outcomes"] = outcomes[int(r["run"])]
    return runs, policies


def rates(outcomes: Iterable[tuple[str, str]]) -> dict:
    """Triggering and compliance rate (percent) over a set of (policy_id, outcome) pairs."""
    c = Counter(o for _, o in outcomes)
    n, graded = sum(c.values()), c["pass"] + c["fail"]
    return {"triggering": 100 * (graded + c["withheld"]) / n if n else None,
            "compliance": 100 * c["pass"] / graded if graded else None,
            "triggered": graded + c["withheld"], "graded": graded}


def resolve_rate(runs: list[dict]) -> Optional[float]:
    return 100 * sum(r["resolved"] == "1" for r in runs) / len(runs) if runs else None


def cell(runs: list[dict], **match) -> list[dict]:
    """The runs whose fields equal every given value."""
    return [r for r in runs if all(r[k] == v for k, v in match.items())]


def pooled(runs: list[dict], keep: Callable[[str], bool] = lambda pid: True):
    """All outcomes of these runs, optionally restricted to some policies."""
    return [(p, o) for r in runs for p, o in r["outcomes"] if keep(p)]
