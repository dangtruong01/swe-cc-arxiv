#!/usr/bin/env python3
"""What the full matrix is, what is done, and what is left.

    python tools/sweep.py --repo django --models deepseek-v4-flash-0731,kimi-k2.5
    python tools/sweep.py --repo django --models ... --remaining        # ids to run next
    python tools/sweep.py --repo django --models ... --remaining -n 40  # one chunk

A sweep of thousands of runs is interrupted as a matter of course -- a laptop sleeps, a
key expires, a provider returns 500 for ten minutes. The design answer is that **a run is
idempotent**: `run_test.sh` skips any cell whose `trajectory.json` already exists, so
re-issuing the same command continues rather than restarts. This tool is the other half --
it says how far along the sweep is without anyone keeping a tally.

**Disk is the binding constraint, not time or money.** SWE-bench images are ~4.2 GB
nominal but share base layers, so the marginal cost is ~1.4 GB per instance; a few hundred
instances still exceeds a typical laptop. `--remaining -n <chunk>` exists for that: pull a
chunk's images, run the chunk, prune, repeat. Progress survives pruning because it is
computed from `runs/`, never from what Docker happens to hold.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compliance.core.paths import PATCH, RUNS_ROOT, RunDir  # noqa: E402

CONDITIONS = ("naive", "guided")


def instances_from(cases: Path, repo: str) -> list[str]:
    """Instance ids from a case list, filtered to one repository.

    A file rather than the dataset, deliberately: `datasets` lives in the harness venv,
    and this project's venv is stdlib-plus-test-deps by design. The same file drives
    `run_batch.sh`, so the sweep and the runner cannot disagree about what the matrix is.

    `sweeps/instances.txt` lists all 500; `sweeps/smoke.txt` is a one-task smoke test.
    """
    ids = []
    for line in cases.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line.startswith(f"{repo}__"):
            ids.append(line)
    if not ids:
        raise SystemExit(f"{cases} lists no {repo}__ instances")
    return ids


def done(repo: str, framework: str, model: str, instance: str, condition: str) -> bool:
    """A cell counts as done when its `patch.diff` exists.

    **The same marker `run_test.sh` uses**, and they must agree: this tool once counted
    trajectories while the runner counted patches, so it reported 3 instances outstanding
    where 8 really were. A trajectory is written while the agent is still inside the
    container, so a cell killed during collection has one and no patch.

    Deliberately not keyed on `rows.jsonl`: scoring is free and re-runnable, and treating
    an unscored run as unfinished would re-spend money to recover something a re-score
    gives away.
    """
    return RunDir(repo=repo, framework=framework, model=model, instance_id=instance,
                  condition=condition).file(PATCH).exists()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--cases", required=True, type=Path, help="file of instance ids")
    ap.add_argument("--models", required=True, help="comma-separated model slugs")
    ap.add_argument("--framework", default="mini-swe-agent")
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--limit", type=int, help="only the first N instances of the repo")
    ap.add_argument("--remaining", action="store_true",
                    help="print the instance ids still needing work, one per line")
    ap.add_argument("-n", "--chunk", type=int, help="with --remaining, cap the list")
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    instances = instances_from(args.cases, args.repo)
    if args.limit:
        instances = instances[: args.limit]

    todo: list[str] = []
    per_model: dict[str, int] = {m: 0 for m in models}
    for instance in instances:
        outstanding = False
        for model in models:
            for condition in conditions:
                if done(args.repo, args.framework, model, instance, condition):
                    per_model[model] += 1
                else:
                    outstanding = True
        if outstanding:
            todo.append(instance)

    total = len(instances) * len(models) * len(conditions)
    finished = sum(per_model.values())

    if args.remaining:
        for instance in todo[: args.chunk] if args.chunk else todo:
            print(instance)
        return 0

    print(f"\n  {args.repo} / {args.framework}: {len(instances)} instances x "
          f"{len(models)} model(s) x {len(conditions)} condition(s) = {total:,} runs")
    print(f"  done {finished:,} ({finished / total:.0%})   remaining {total - finished:,}")
    print(f"  instances with outstanding work: {len(todo)}\n")
    print(f"  {'model':28}{'done':>8}{'of':>8}")
    for model in models:
        print(f"  {model:28}{per_model[model]:>8}{len(instances) * len(conditions):>8}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
