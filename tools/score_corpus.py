#!/usr/bin/env python3
"""Score stored runs for compliance, in bulk, writing `rows.jsonl` beside each run.

    python tools/score_corpus.py                        # everything unscored
    python tools/score_corpus.py --repo pylint-dev      # one repo
    python tools/score_corpus.py --framework openhands
    python tools/score_corpus.py --force                # rescore, ignoring existing rows
    python tools/score_corpus.py --dry-run              # list what would be scored

WHY THIS EXISTS. No sweep scores compliance. `run_test.sh` grades FUNCTIONALLY inline
(mini-swe-agent) or not at all (OpenHands), but the compliance half is always a separate
pass -- it is pure and offline, so it can run any time, including while a sweep is in
flight. The stored `rows.jsonl` for django and sympy were written by an ad-hoc pass on
1 Sep 2026; this is that pass made repeatable.

**THE REPO MUST COME FROM THE RUN'S PATH.** `compliance check` defaults `--repo` to sympy.
Scoring a pylint-dev run without it loads SymPy's 142 rules, reports `SYMPY-C276 fail`,
and prints a confident `compliance rate: 34.4%` that means nothing -- a plausible result
rather than an error, which is this project's recurring failure shape. With the right
corpus that same run scores 49 rules at 44.4%.

**THE MODEL LABEL IS INFERRED, NEVER PASSED.** `build_bundle(traj, condition=...)` with no
`model=` lets the builder read the litellm id from the trajectory, which is what the rest
of the corpus carries (`openrouter/deepseek/deepseek-v4-flash-0731`). Passing the path
slug instead writes `deepseek-v4-flash-0731`, and `compliance report` then sees one cell
as two and emits `!! POOLING 2 CELLS` -- a key that is not unique, losing data quietly.

Resumable, and self-healing: a run is skipped only when its `rows.jsonl` is NEWER than
both its trajectory and its patch. A re-run overwrites its attempt directory in place, so
"rows exist" is not evidence that the rows describe the run now stored there.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compliance.core.paths import RUNS_ROOT  # noqa: E402  (honours $RUNS_ROOT)

from compliance.bundle.builder import build_bundle
from compliance.cli import load_rule_modules
from compliance.core import registry
from compliance.core.registry import CHECKER_VERSION
from compliance.core.runner import run_rules


def is_stale(rows: Path, traj: Path) -> bool:
    """Do these rows predate the evidence they claim to score?

    **A RE-RUN OVERWRITES ITS ATTEMPT DIRECTORY.** `run_test.sh` takes
    `attempt="${START_ATTEMPT:-1}"`, so re-issuing a sweep command writes the new
    trajectory and patch into the SAME attemptN directory; the earlier ones are gone.
    A resume rule of "rows exist, so skip" therefore keeps scores computed against
    evidence that no longer exists, and keeps them silently: the run has rows, the pass
    reports `nothing to score`, and the corpus carries a verdict about a patch it no
    longer holds.

    Measured 15 Sep 2026: 101 cells were in exactly that state -- 14 OpenHands (django
    cells re-run during the 13-14 Sep sweep) and 87 mini-swe-agent (the gemini per-repo
    re-runs of 7-8 Sep, stale by 8.6 to 42.8 hours). Every one of them was scored as
    though the cell had failed, in a corpus otherwise treated as complete.

    Comparing mtimes makes the pass self-healing: a re-run's fresher artefacts are
    detected on the next invocation with no flag and no bookkeeping.
    """
    if not rows.exists():
        return True
    rows_mtime = rows.stat().st_mtime
    for artefact in (traj, traj.parent / "patch.diff"):
        if artefact.exists() and artefact.stat().st_mtime > rows_mtime:
            return True
    return False


def discover(repo: str | None, framework: str | None, force: bool):
    """Every stored run, as (repo, framework, trajectory path, rows path)."""
    for traj in sorted(RUNS_ROOT.glob("*/*/*/*/*/attempt*/trajectory.json")):
        rel = traj.relative_to(RUNS_ROOT).parts   # repo/fw/model/instance/cond/attemptN
        r, fw = rel[0], rel[1]
        if repo and r != repo:
            continue
        if framework and fw != framework:
            continue
        rows = traj.parent / "rows.jsonl"
        if not force and not is_stale(rows, traj):
            continue
        yield r, fw, traj, rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo")
    ap.add_argument("--framework")
    ap.add_argument("--force", action="store_true", help="rescore runs that already have rows")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    todo = list(discover(args.repo, args.framework, args.force))
    if not todo:
        print("nothing to score")
        return 0

    by_repo: dict[str, int] = {}
    for r, *_ in todo:
        by_repo[r] = by_repo.get(r, 0) + 1
    print(f"== {len(todo)} run(s) to score")
    for r, n in sorted(by_repo.items()):
        print(f"   {r:<14} {n}")
    if args.dry_run:
        return 0

    # Rule modules and corpora are per-repo and cached, so group by repo and load once.
    loaded: dict[str, tuple] = {}
    ok = failed = 0
    for i, (repo, fw, traj, rows_path) in enumerate(todo, 1):
        try:
            if repo not in loaded:
                # CLEAR THE REGISTRY FIRST. `_REGISTRY` in compliance/core/registry.py is a
                # module-level dict and `load_rule_modules` only ever ADDS to it, so
                # `registered()` returns every pack imported so far in this process, not the
                # pack just loaded. Without the clear, a run is scored against its own rules
                # plus every repository's rules that came before it alphabetically.
                #
                # Measured 16 Sep 2026 over the whole corpus: 1,401 of 4,000 OpenHands runs
                # and 864 of 4,000 mini-swe-agent runs carried foreign rows -- 64% of all
                # OpenHands rows. A seaborn run held 280 rows, of which 111 were astropy's
                # and 167 matplotlib's and 2 its own.
                #
                # It is a quiet failure in both directions: foreign rules mostly do not
                # apply, which inflates the row count and so DEFLATES the triggering rate,
                # and any that do apply produce verdicts about a project whose conventions
                # the agent was never shown. Every affected number looked plausible.
                registry.clear_registry()
                load_rule_modules(repo)
                loaded[repo] = (registry.load_corpus(registry.corpus_path_for(repo)),
                                registry.registered())
                print(f"\n-- {repo}: {len(loaded[repo][1])} rules")
            corpus, rules = loaded[repo]
            # condition and model both inferred from the run; see the docstring.
            bundle = build_bundle(str(traj))
            scored = run_rules(bundle, rules, corpus, checker_version=CHECKER_VERSION)
            with rows_path.open("w") as fh:
                for row in scored:
                    fh.write(json.dumps(row.as_dict(), sort_keys=True) + "\n")
            ok += 1
        except Exception as exc:  # a bad run must not stop the pass
            failed += 1
            print(f"!! {traj.parent.relative_to(RUNS_ROOT)}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            if failed <= 3:
                traceback.print_exc(limit=2, file=sys.stderr)
        if i % 100 == 0:
            print(f"   [{i}/{len(todo)}] ok={ok} failed={failed}")

    print(f"\n== scored {ok}, failed {failed}, of {len(todo)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
