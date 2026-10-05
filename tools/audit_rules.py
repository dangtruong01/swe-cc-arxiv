#!/usr/bin/env python3
"""Self-audit gate for a rule corpus. Runs the nine checks in §7 of the extraction prompt.

    python tools/audit_rules.py --repo sphinx-doc

Repo-agnostic: it names no repository and derives the expected ID prefix from the
directory name under `rules/`, which is the same thing `tests/test_registry.py`
selects on. Nothing here duplicates `tools/corpus.py`; check 1 shells out to it.

**Why this exists alongside the gate.** `tools/corpus.py:STRENGTHS` still accepts
`should` and `prohibited`, so a vocabulary leak passes the gate silently. Check 2 is
the only thing that catches it. Likewise `NaiveStrength:` lives inside a free-text
`Notes` cell, so nothing but check 4 notices when the naive reading was never recorded
and the promotion-direction result becomes uncomputable.

Known-good calibration: `--repo django` fails exactly two checks (no `NaiveStrength`
on any row; 11 rows still reading `should`) and passes the other seven.
"""

from __future__ import annotations

import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compliance.core import workbook  # noqa: E402
from compliance.core.registry import RULES_DIR, repo_conf  # noqa: E402

COLUMNS = [
    "ID", "Source", "Original text", "Atomic rule", "Applies to", "Shared Category",
    "Strength", "CheckTier", "Care", "NotCareReason", "Notes",
]
CATEGORIES = {
    "Git and commit conventions", "PR and release metadata", "Tests and test style",
    "Specialized changes", "Documentation and docstrings",
    "AI-assisted contribution policy", "Code and quality",
    "Language and framework style",
}
STRENGTHS = {"must", "maybe"}
BANNED = {"should", "prohibited", "grey"}
TIERS = {"static", "differential", "trajectory", "judgment"}
TRUTHY = {"1", "TRUE", "YES", "T", "Y"}
NAIVE = {"must", "maybe", "prohibited"}

#: Rules per 1,000 words of contribution prose, from the two calibration repos.
#: Used for an order-of-magnitude sanity check only.
DENSITY_LO, DENSITY_HI = 3.0, 40.0


def care(row: dict) -> bool:
    return (row.get("Care") or "").strip().upper() in TRUTHY


def cell(row: dict, key: str) -> str:
    return (row.get(key) or "").strip()


def field(notes: str, name: str) -> str | None:
    """Pull one `Name: value` field out of a pipe-separated Notes cell."""
    for part in notes.split(" | "):
        part = part.strip()
        if part.lower().startswith(name.lower() + ":"):
            return part.split(":", 1)[1].strip()
    return None


def check_gate(slug: str, _rows) -> tuple[bool, list[str]]:
    proc = subprocess.run([sys.executable, str(ROOT / "tools/corpus.py"), "--repo", slug],
                          capture_output=True, text=True, cwd=ROOT)
    if proc.returncode == 0:
        return True, ["tools/corpus.py exits 0"]
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
    return False, [f"tools/corpus.py exit {proc.returncode}"] + tail


def check_schema(_slug: str, rows) -> tuple[bool, list[str]]:
    bad: list[str] = []
    header = list(rows[0].keys())[:len(COLUMNS)]
    if header != COLUMNS:
        bad.append(f"column order is {header}")
    for r in rows:
        rid = cell(r, "ID") or "<no ID>"
        s = cell(r, "Strength").lower()
        if s in BANNED:
            bad.append(f"{rid}: Strength {s!r} is banned vocabulary")
        elif care(r) and s not in STRENGTHS:
            bad.append(f"{rid}: Care row has Strength {s!r}, not must/maybe")
        elif not care(r) and s:
            bad.append(f"{rid}: Not Care row has Strength {s!r}, must be blank")
        ncr = cell(r, "NotCareReason")
        if care(r) and ncr:
            bad.append(f"{rid}: Care row has NotCareReason {ncr!r}, must be blank")
        if not care(r) and not re.match(r"^N[1-4]\b", ncr):
            bad.append(f"{rid}: NotCareReason {ncr!r} does not start with N1-N4")
        if not cell(r, "Source").split(" | ")[0].startswith("http"):
            bad.append(f"{rid}: Source does not start with a URL")
        if cell(r, "Shared Category") not in CATEGORIES:
            bad.append(f"{rid}: Shared Category {cell(r, 'Shared Category')!r} off-taxonomy")
        if cell(r, "CheckTier") not in TIERS:
            bad.append(f"{rid}: CheckTier {cell(r, 'CheckTier')!r} off-list")
    return not bad, bad[:12] or ["11 columns in order; vocabulary, blanks and taxonomy clean"]


def check_prefix(slug: str, rows) -> tuple[bool, list[str]]:
    pattern = re.compile(rf"^{re.escape(slug.upper())}-C\d{{3}}$")
    bad = [cell(r, "ID") for r in rows if not pattern.match(cell(r, "ID"))]
    if bad:
        return False, [f"{len(bad)} ID(s) not matching {pattern.pattern}: {bad[:5]}"]
    return True, [f"all {len(rows)} IDs match {pattern.pattern}"]


def check_judgment(_slug: str, rows) -> tuple[bool, list[str]]:
    bad = [cell(r, "ID") for r in rows
           if cell(r, "CheckTier").lower() == "judgment" and care(r)]
    if bad:
        return False, [f"judgment + Care on {bad}"]
    n = sum(1 for r in rows if cell(r, "CheckTier").lower() == "judgment")
    return True, [f"0 judgment+Care rows ({n} judgment rows, all Not Care)"]


def check_naive(_slug: str, rows) -> tuple[bool, list[str]]:
    missing = [cell(r, "ID") for r in rows
               if (field(cell(r, "Notes"), "NaiveStrength") or "") not in NAIVE]
    if missing:
        return False, [f"{len(missing)}/{len(rows)} rows without a valid NaiveStrength:",
                       f"first: {missing[:5]}"]
    diff = [r for r in rows if care(r)
            and field(cell(r, "Notes"), "NaiveStrength") != cell(r, "Strength")]
    by = collections.Counter(
        f"{field(cell(r, 'Notes'), 'NaiveStrength')} -> {cell(r, 'Strength')}" for r in diff)
    return True, [f"NaiveStrength on 100% of {len(rows)} rows",
                  f"NaiveStrength != Strength on {len(diff)} of "
                  f"{sum(1 for r in rows if care(r))} Care rows: {dict(by)}"]


def check_promotion(_slug: str, rows) -> tuple[bool, list[str]]:
    """Reported, never failed -- the direction is the finding, not a defect."""
    promo = demo = fold = same = 0
    for r in rows:
        if not care(r):
            continue
        naive = field(cell(r, "Notes"), "NaiveStrength")
        final = cell(r, "Strength")
        if naive is None:
            continue
        if naive == final:
            same += 1
        elif naive == "prohibited":
            fold += 1
        elif naive == "maybe" and final == "must":
            promo += 1
        elif naive == "must" and final == "maybe":
            demo += 1
    return True, [f"promotions maybe->must: {promo}; demotions must->maybe: {demo}; "
                  f"prohibited->must folds: {fold}; unchanged: {same}"]


def check_reasoning(_slug: str, rows) -> tuple[bool, list[str]]:
    have = [c for r in rows if (c := field(cell(r, "Notes"), "Conclusion"))]
    dupes = [c for c, n in collections.Counter(have).items() if n > 1]
    coverage = f"{len(have)}/{len(rows)} rows carry a Conclusion:"
    if dupes:
        return False, [f"{len(dupes)} duplicated Conclusion value(s); {coverage}",
                       str(dupes[:2])]
    # Coverage is reported, not failed: the Notes spec is enforced by the composition
    # step, and django -- the format standard -- carries Conclusion on 49 of 143 rows.
    return True, [f"{len(set(have))} distinct Conclusion values; {coverage}"]


def check_nbalance(_slug: str, rows) -> tuple[bool, list[str]]:
    counts = collections.Counter(cell(r, "NotCareReason")[:2] for r in rows if not care(r))
    n1 = counts.get("N1", 0)
    rest = sum(v for k, v in counts.items() if k != "N1")
    return True, [f"N1 {n1} | N2 {counts.get('N2', 0)} | N3 {counts.get('N3', 0)} | "
                  f"N4 {counts.get('N4', 0)}  (N1 vs N2-N4: {n1}/{rest})"]


def check_plausibility(_slug: str, rows, words: int | None) -> tuple[bool, list[str]]:
    if not words:
        return True, [f"{len(rows)} rows; no --words given, density not checked"]
    density = len(rows) / (words / 1000)
    ok = DENSITY_LO <= density <= DENSITY_HI
    return ok, [f"{len(rows)} rows over {words} words = {density:.1f} rules/1k words "
                f"(order-of-magnitude band {DENSITY_LO}-{DENSITY_HI})"]


def check_contiguity(_slug: str, rows) -> tuple[bool, list[str]]:
    nums = [int(m.group(1)) for r in rows
            if (m := re.search(r"-C(\d{3})$", cell(r, "ID")))]
    if len(nums) != len(rows):
        return False, [f"{len(rows) - len(nums)} ID(s) do not end in -Cnnn"]
    dupes = [n for n, c in collections.Counter(nums).items() if c > 1]
    gaps = sorted(set(range(1, max(nums) + 1)) - set(nums)) if nums else []
    if dupes or gaps:
        return False, [f"repeats: {dupes[:5]}", f"gaps: {gaps[:8]}"]
    return True, [f"C001-C{max(nums):03d}, no gaps, no repeats"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="slug, i.e. the directory under rules/")
    ap.add_argument("--words", type=int, help="in-scope word count, for check 8")
    ap.add_argument("--sheet", default="Rules")
    args = ap.parse_args()

    repo_dir = RULES_DIR / args.repo
    source = repo_dir / repo_conf(args.repo)["CORPUS"]
    rows = workbook.read(source, args.sheet)

    results = [
        ("1  Gate (tools/corpus.py)", check_gate(args.repo, rows)),
        ("2  Schema and vocabulary", check_schema(args.repo, rows)),
        ("2b ID prefix", check_prefix(args.repo, rows)),
        ("3  Judgment invariant", check_judgment(args.repo, rows)),
        ("4  NaiveStrength present", check_naive(args.repo, rows)),
        ("5  Promotion direction", check_promotion(args.repo, rows)),
        ("6  Reasoning uniqueness", check_reasoning(args.repo, rows)),
        ("7  N1 vs N2-N4 balance", check_nbalance(args.repo, rows)),
        ("8  Row-count plausibility", check_plausibility(args.repo, rows, args.words)),
        ("9  ID contiguity", check_contiguity(args.repo, rows)),
    ]

    print(f"\n  audit: {source.name}  ({len(rows)} rows)\n")
    width = max(len(name) for name, _ in results)
    failed = 0
    for name, (ok, notes) in results:
        verdict = "PASS" if ok else "FAIL"
        failed += not ok
        print(f"  {name.ljust(width)}  {verdict}  {notes[0]}")
        for extra in notes[1:]:
            print(f"  {' ' * width}        {extra}")
    print(f"\n  {len(results) - failed}/{len(results)} checks pass\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
