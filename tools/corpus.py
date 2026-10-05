#!/usr/bin/env python3
"""Read a rule corpus, check it, and export the CSV the harness reads.

    python tools/corpus.py --repo django

**The workbook IS the corpus.** `repo.conf` names it and `registry.load_corpus` reads it
directly -- there is no export step, because an export step that is skipped leaves the
checker scoring yesterday's corpus with nothing to say so.

This tool does not transform anything. It reads what the harness will read and reports
whether the harness can use it.

Repo-agnostic by construction: it names no repository, reads `.xlsx` or `.csv` with the
same result, and takes the corpus path from `rules/<slug>/repo.conf`. Adding a repository
is a workbook plus a conf, with no change here.

**Why the checks exist.** Schema alignment is the easy half; every check below corresponds
to a convention that was already gotten wrong once, and the expensive ones fail *silently*:

- `Shared Category` outside the taxonomy -- `build_contributing_rules.py` refuses to run.
  Loud, cheap, fixed in minutes.
- `Source` with the URL second -- `retrieval.source_urls_from_corpus` keeps the first
  ` | `-separated field only if it starts with `http`, so the naive arm reports reaching
  0 of 0 pages and looks perfectly healthy while measuring nothing.

The second kind is why this runs in CI rather than living in someone's memory.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compliance.core import workbook  # noqa: E402
from compliance.core.registry import RULES_DIR, repo_conf  # noqa: E402

#: The shared schema. Order matters -- the CSV is written in it.
COLUMNS = [
    "ID", "Source", "Original text", "Atomic rule", "Applies to", "Shared Category",
    "Strength", "CheckTier", "Care", "NotCareReason", "Notes",
]

#: Kept in sync with CATEGORY_ORDER in rules/build_contributing_rules.py.
CATEGORIES = {
    "Git and commit conventions", "PR and release metadata", "Tests and test style",
    "Specialized changes", "Documentation and docstrings",
    "AI-assisted contribution policy", "Code and quality",
    "Language and framework style",
}

STRENGTHS = {"must", "maybe", "should", "prohibited"}
TRUTHY = {"1", "TRUE", "YES", "T", "Y"}
FALSY = {"0", "FALSE", "NO", "F", "N", ""}


def load(path: Path, sheet: str = "Rules") -> list[dict[str, str]]:
    """Corpus rows from `.xlsx` or `.csv` -- the same reader the harness uses."""
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    return workbook.read(path, sheet)


def validate(rows: list[dict[str, str]]) -> list[str]:
    """Every convention the harness depends on. Empty list means the corpus is usable."""
    problems: list[str] = []
    if not rows:
        return ["corpus is empty"]

    missing = [c for c in COLUMNS if c not in rows[0]]
    if missing:
        return [f"missing column(s): {missing}"]

    seen: set[str] = set()
    for row in rows:
        rid = (row.get("ID") or "").strip()
        if not rid:
            problems.append("a row has no ID")
            continue
        if rid in seen:
            problems.append(f"{rid}: duplicate ID")
        seen.add(rid)

        care_raw = (row.get("Care") or "").strip().upper()
        if care_raw not in TRUTHY | FALSY:
            problems.append(f"{rid}: Care is {care_raw!r}, not a boolean")
        care = care_raw in TRUTHY

        category = (row.get("Shared Category") or "").strip()
        if category not in CATEGORIES:
            problems.append(f"{rid}: Shared Category {category!r} is not in the taxonomy")

        strength = (row.get("Strength") or "").strip().lower()
        if care and strength not in STRENGTHS:
            problems.append(f"{rid}: Strength {strength!r} is not one of {sorted(STRENGTHS)}")

        # The silent one. A Source whose first field is not a URL makes the naive-arm
        # retrieval probe report 0 of 0 pages reached -- indistinguishable from success.
        source = (row.get("Source") or "").strip()
        if care and not source.split(" | ")[0].strip().startswith("http"):
            problems.append(f"{rid}: Source must start with the URL ('URL | Section'), got {source[:44]!r}")

        if care and not (row.get("Atomic rule") or "").strip():
            problems.append(f"{rid}: marked Care but has no Atomic rule")
        if not care and not (row.get("NotCareReason") or "").strip():
            problems.append(f"{rid}: not Care but gives no NotCareReason")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="slug, i.e. the directory under rules/")
    ap.add_argument("--source", help="override; default is the CORPUS in repo.conf")
    ap.add_argument("--sheet", default="Rules")
    args = ap.parse_args()

    repo_dir = RULES_DIR / args.repo
    source = Path(args.source) if args.source else repo_dir / repo_conf(args.repo)["CORPUS"]
    if not source.exists():
        raise SystemExit(f"{source} not found")

    rows = load(source, args.sheet)
    problems = validate(rows)

    care = [r for r in rows if (r.get("Care") or "").strip().upper() in TRUTHY]
    batch = [r for r in care if (r.get("Strength") or "").strip().lower() == "must"]
    print(f"\n  {source.name}: {len(rows)} rules, {len(care)} Care, {len(batch)} in the scored batch")

    if problems:
        print(f"\n  {len(problems)} PROBLEM(S):")
        for p in problems[:25]:
            print(f"    - {p}")
        if len(problems) > 25:
            print(f"    ... and {len(problems) - 25} more")
        return 1
    print("  checks: OK\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
