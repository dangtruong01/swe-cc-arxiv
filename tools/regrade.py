#!/usr/bin/env python3
"""Grade runs that finished but were never graded. No agent run; the patch is stored.

    python tools/regrade.py --repo django              # what would be re-graded
    python tools/regrade.py --repo django --run        # actually do it

A run is complete when `patch.diff` exists — written when the agent finishes and its work
is collected. Grading happens after that and can fail independently: a corrupted shared
file, a Docker refusal, a killed batch. When it does, the cell keeps its compliance score,
counts as complete, and every resume skips it. **The functional half is lost silently**,
which is how 51 of 284 django cells ended up ungraded before anyone counted.

Everything grading needs is already on disk, so this costs Docker time and no model calls.
It is deliberately a separate tool rather than part of the sweep: grading pulls an image
and runs the repository's test suite, so doing it while a sweep holds eight containers
competes for exactly the resource that caused the failures in the first place.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compliance.core.paths import EVAL_REPORT, PATCH, discover  # noqa: E402

HARNESS = Path(__file__).resolve().parents[1] / "mini-swe-agent-run" / "mini-swe-agent"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo")
    ap.add_argument("--model")
    ap.add_argument("--run", action="store_true", help="grade them; otherwise just list")
    args = ap.parse_args()

    todo = [r for r in discover(repo=args.repo, model=args.model)
            if r.file(PATCH).exists() and not r.file(EVAL_REPORT).exists()]
    # INSTANCE-MAJOR, AND THIS IS A DISK BUDGET, NOT TIDINESS. Grading an instance builds
    # or pulls its SWE-bench eval image -- 3.4 to 4.8 GB -- and all 8 cells of an instance
    # (4 models x 2 conditions) share one image. `discover()` yields model-major, so the
    # natural order opens every instance in the repository before finishing any of them:
    # matplotlib's 34 instances meant 34 resident images, ~130 GB, and the image of an
    # instance with cells still outstanding cannot be reclaimed by anything. Measured
    # 15 Sep 2026: the disk fell 10 GB/min and hit 24 GB free with 94 GB of eval images
    # resident and nothing safe to drop.
    #
    # Sorting by instance makes those 8 cells consecutive, so an instance's image goes
    # from built to fully-spent in one pass and the janitor can release it immediately.
    # Resident images become O(workers) rather than O(instances in the repository).
    todo.sort(key=lambda r: (r.repo, r.instance_id, r.model, r.condition))
    if not todo:
        print("\n  nothing ungraded\n")
        return 0

    print(f"\n  {len(todo)} run(s) finished but never graded:")
    for r in todo[:10]:
        print(f"    {r.repo}/{r.model}/{r.instance_id}/{r.condition}")
    if len(todo) > 10:
        print(f"    ... and {len(todo) - 10} more")

    if not args.run:
        print("\n  pass --run to grade them (Docker time, no model calls)\n")
        return 0

    # Serial on purpose. Grading runs the repository's whole test suite -- one django
    # container measured at 3.2 GB -- and running several at once is what corrupted the
    # shared manifest and produced these ungraded runs to begin with.
    ok = 0
    for i, run in enumerate(todo, 1):
        print(f"\n  [{i}/{len(todo)}] {run.instance_id}/{run.condition} ({run.model})")
        result = subprocess.run(
            ["bash", str(HARNESS / "scripts" / "evaluate.sh"), run.instance_id, str(run.path)],
            cwd=HARNESS, capture_output=True, text=True,
            env={**__import__("os").environ,
                 "PATH": f"{HARNESS / '.venv' / 'bin'}:{__import__('os').environ['PATH']}"},
        )
        if run.file(EVAL_REPORT).exists():
            ok += 1
            print("    graded")
        else:
            print(f"    still ungraded: {result.stderr.strip().splitlines()[-1:] or ['(no error)']}")
    print(f"\n  graded {ok} of {len(todo)}\n")
    return 0 if ok == len(todo) else 1


if __name__ == "__main__":
    raise SystemExit(main())
