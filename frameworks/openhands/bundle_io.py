"""Turning one OpenHands result into the run directory this project stores.

Deliberately imports nothing from OpenHands or its SDK. The layout, the
``===SECTION===`` delimiters and the completion marker are **ours**, shared with the
other framework -- so this is testable in the main suite, which has no agent framework
installed, and a change to it is checked against the same rules that govern
mini-swe-agent's runs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

#: Sections `collect.sh` emits, and the file each is split into beside the trajectory,
#: so a run is inspectable without a JSON parser. Mirrors the other harness's run_test.sh.
SECTION_FILES = {
    "PROBE": "probe.txt",
    "PATCH_COMMITTED": "patch_committed.diff",
    "PATCH": "patch.diff",
}

_MARK = re.compile(r"^===([A-Z_]+)===$", re.M)


def section(bundle: str, name: str) -> str | None:
    """One ``===SECTION===`` of a collect bundle, or None if it is not there."""
    marks = list(_MARK.finditer(bundle))
    for index, mark in enumerate(marks):
        if mark.group(1) != name:
            continue
        end = marks[index + 1].start() if index + 1 < len(marks) else len(bundle)
        return bundle[mark.end():end].strip("\n") + "\n"
    return None


def patch_from_bundle(bundle: str) -> str:
    """The patch bytes. ``===PATCH===`` is last, so everything after it is the patch."""
    return bundle.split("===PATCH===", 1)[1].strip() if "===PATCH===" in bundle else ""


def write_run_dir(result: dict[str, Any], run_dir: Path) -> None:
    """Store one run, with ``patch.diff`` written LAST.

    That ordering is the whole contract. `patch.diff` is the completion marker every
    resume in this project keys on, so a run interrupted part-way through writing must
    not leave one behind: a trajectory with no patch is retried, which is correct, while
    a patch with no trajectory would be counted as done forever.

    An empty patch is not written at all. The agent may genuinely have changed nothing,
    but that is a run to retry rather than to record as complete -- the other harness
    learned this from runs that mangled their submit command and stored a dead
    trajectory that every later sweep skipped.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trajectory.json").write_text(json.dumps(result, indent=1))

    bundle = (result.get("test_result") or {}).get("bundle") or ""
    if not bundle:
        return
    (run_dir / "bundle.txt").write_text(bundle)
    # `collect.txt` as well, for structural parity with the other framework. There it is
    # the container-side copy from the /artifacts bind mount and `bundle.txt` is the
    # submission, so the two can differ when a submission was truncated. Here there is no
    # such mount and both come from the same recovered text -- written anyway so a run
    # directory has the same shape whichever framework produced it, and anything reading
    # the corpus by filename finds what it expects.
    (run_dir / "collect.txt").write_text(bundle)
    for name, filename in SECTION_FILES.items():
        if filename == "patch.diff":
            continue
        if (body := section(bundle, name)) is not None:
            (run_dir / filename).write_text(body)

    if patch := patch_from_bundle(bundle):
        (run_dir / "patch.diff").write_text(patch.rstrip("\n") + "\n")
