"""The functional half of a run: what the SWE-bench harness said about the patch.

Layer A -- no knowledge of any particular repository.

This module exists because the same filename held two different things. The harness
writes a **per-instance report**, keyed by instance id and carrying ``tests_status``, and
separately a **run-level summary** carrying only counts. Both are JSON, both are called
something like a report, and one of them was copied into the per-run slot for part of the
corpus. The summary answers "how many resolved"; it cannot answer "which tests changed
state", and it is not even keyed to the run it sits beside -- when the harness run id was
keyed on instance alone, a second condition's grading overwrote the first, so a summary
found in a run directory may be reporting a *different run's* outcome.

So the shape is not a detail to normalise away. ``EvalReport.shape`` names it, and
``tests_status`` is only populated for the per-instance form.

Why the checker cares at all: ``tests_status`` is a before-and-after comparison of test
outcomes, which is exactly what the corpus means by ``CheckTier = differential``. A rule
that needs to know whether a test changed state can be answered from it -- without it,
those rules withhold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from compliance.core.paths import EVAL_REPORT, PATCH, RunDir

Shape = Literal["instance", "summary", "absent", "not_gradeable", "unreadable"]

# The four buckets the harness reports, each split into success/failure.
#
# Read the names carefully, because the obvious reading is wrong and cost a dead rule.
# A bucket name is the transition the **dataset expects**; `success`/`failure` says
# whether that expectation held. So:
#
#   PASS_TO_PASS.success   expected to keep passing, did            fine
#   PASS_TO_PASS.failure   expected to keep passing, does not       THE REGRESSION
#   FAIL_TO_PASS.success   expected to start passing, did           the fix worked
#   FAIL_TO_PASS.failure   expected to start passing, did not       the fix did not work
#   PASS_TO_FAIL.success   expected to break, broke                 anticipated, not a regression
#   FAIL_TO_FAIL.success   expected to keep failing, did            fine
#
# A regression therefore lives in PASS_TO_PASS.**failure**, not in the PASS_TO_FAIL
# bucket, whose name merely looks like it means that.
BUCKETS = ("FAIL_TO_PASS", "PASS_TO_PASS", "FAIL_TO_FAIL", "PASS_TO_FAIL")


@dataclass(frozen=True)
class EvalReport:
    shape: Shape
    resolved: Optional[bool] = None
    instance_id: str = ""
    tests_status: dict[str, dict[str, tuple[str, ...]]] = field(default_factory=dict)
    empty_patch_ids: tuple[str, ...] = ()
    """From a run-level summary: instances the harness saw submit nothing."""
    note: str = ""

    @property
    def usable(self) -> bool:
        """Whether this carries per-test evidence, not merely a resolved count."""
        return self.shape == "instance" and bool(self.tests_status)

    @property
    def n_outcomes(self) -> int:
        return sum(len(v.get("success", ())) + len(v.get("failure", ()))
                   for v in self.tests_status.values())

    def bucket(self, name: str, outcome: str = "success") -> tuple[str, ...]:
        return self.tests_status.get(name, {}).get(outcome, ())

    def newly_passing(self) -> tuple[str, ...]:
        """Tests that failed before the patch and pass after it."""
        return self.bucket("FAIL_TO_PASS", "success")

    def regressions(self) -> tuple[str, ...]:
        """Tests that passed before the change and fail after it.

        Read from ``PASS_TO_PASS.failure`` -- see the note on ``BUCKETS``. Naming this
        ``newly_failing`` and reading ``PASS_TO_FAIL`` instead was wrong, and silently:
        the only run in the pilot with a real regression reported none, so the rule that
        depends on this could never fail.
        """
        return self.bucket("PASS_TO_PASS", "failure")

    def tests_reported(self) -> frozenset[str]:
        """Every test the harness reported on, whatever it concluded about it."""
        return frozenset(
            name
            for bucket in self.tests_status.values()
            for outcome in ("success", "failure")
            for name in bucket.get(outcome, ())
        )

    def broke_nothing(self) -> bool:
        return not self.regressions()


def _buckets(raw: dict) -> dict[str, dict[str, tuple[str, ...]]]:
    out: dict[str, dict[str, tuple[str, ...]]] = {}
    for name in BUCKETS:
        value = raw.get(name)
        if isinstance(value, dict):
            out[name] = {
                key: tuple(value.get(key) or ())
                for key in ("success", "failure")
            }
    return out


def parse(text: str) -> EvalReport:
    """Classify and read one report. Never raises on malformed input."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as exc:
        return EvalReport("unreadable", note=f"not JSON: {exc}")
    if not isinstance(data, dict) or not data:
        return EvalReport("unreadable", note="empty or non-object JSON")

    # The run-level summary is recognised by its own keys, not by elimination: a report
    # we cannot classify must not be silently treated as either form.
    if "total_instances" in data:
        resolved = data.get("resolved_instances")
        empty = tuple(data.get("empty_patch_ids") or ())
        return EvalReport(
            "summary",
            resolved=bool(resolved) if isinstance(resolved, int) else None,
            empty_patch_ids=empty,
            note="run-level summary: resolved counts only, no per-test evidence, and not "
                 "necessarily this run's -- summaries were shared across conditions",
        )

    instance_id = next(iter(data))
    body = data[instance_id]
    if not isinstance(body, dict):
        return EvalReport("unreadable", note=f"unexpected shape under {instance_id!r}")
    status = body.get("tests_status")
    return EvalReport(
        "instance",
        resolved=body.get("resolved") if isinstance(body.get("resolved"), bool) else None,
        instance_id=instance_id,
        tests_status=_buckets(status) if isinstance(status, dict) else {},
        note="" if isinstance(status, dict) else "per-instance report with no tests_status",
    )


def load(run: RunDir | Path) -> EvalReport:
    """Read one run's functional result.

    Accepts a ``RunDir``, the attempt *directory*, or the report file itself, because all
    three are natural things for a caller to hold and guessing wrong is silent: a
    directory read as a file raises, but a wrong file read as a report returns a shape
    that merely looks unusable.
    """
    directory, path = _resolve(run)
    if path.exists():
        report = parse(path.read_text(encoding="utf-8", errors="replace"))
        # A summary is normally unusable, but one that names this instance as having
        # submitted nothing is saying something true and specific. Only believed when
        # the run directory agrees -- no patch on disk -- because summaries were once
        # shared across conditions and cannot otherwise be trusted to be this run's.
        if (report.shape == "summary" and directory is not None
                and _claims_this_run_was_empty(directory, report)
                and not _has_patch(directory)):
            return EvalReport("not_gradeable", resolved=False,
                              empty_patch_ids=report.empty_patch_ids,
                              note="agent submitted an empty patch: nothing to grade "
                                   "(summary and run directory agree)")
        return report
    if directory is not None and directory.exists() and not _has_patch(directory):
        # The harness writes no per-instance report for an empty patch, so this run has
        # no functional result and never will. Distinguishing it from "never graded"
        # matters: one is a gap to repair, the other is the outcome.
        return EvalReport("not_gradeable", resolved=False,
                          note="agent produced an empty patch: nothing to grade")
    return EvalReport("absent", note="run was never graded")


def _resolve(run: RunDir | Path) -> tuple[Optional[Path], Path]:
    if isinstance(run, RunDir):
        return run.path, run.file(EVAL_REPORT)
    path = Path(run)
    if path.is_dir():
        return path, path / EVAL_REPORT
    return path.parent, path


def _claims_this_run_was_empty(directory: Path, report: EvalReport) -> bool:
    """Whether the summary explicitly says *this* instance submitted nothing.

    Requires a positive claim naming the instance. A summary that makes no empty-patch
    claim tells us nothing about why the per-instance report is missing, and reading
    silence as "empty patch" would convert an ungraded run into a stated outcome -- the
    same conflation of *absent* with *unresolved* these shapes exist to prevent.

    The attempt layout is ``runs/<repo>/<instance>/<condition>/attempt<n>``, so the
    instance sits two levels above the directory.
    """
    if not report.empty_patch_ids:
        return False
    parts = directory.parts
    instance = parts[-3] if len(parts) >= 3 else ""
    return bool(instance) and instance in report.empty_patch_ids


def _has_patch(directory: Path) -> bool:
    patch = directory / PATCH
    return patch.exists() and bool(patch.read_text(encoding="utf-8", errors="replace").strip())


def audit(runs: list[RunDir]) -> list[tuple[RunDir, EvalReport]]:
    """Every run whose functional evidence is missing or unusable *and repairable*.

    The failure this catches is silent: a run directory with a plausible-looking
    ``eval_report.json`` that cannot answer whether a single test changed state, and in
    the summary case may be reporting a different run entirely.

    ``not_gradeable`` is excluded. An empty patch has no functional result to recover,
    so listing it as a gap would send someone to re-run grading that cannot succeed.
    """
    out = []
    for run in runs:
        report = load(run)
        if not report.usable and report.shape != "not_gradeable":
            out.append((run, report))
    return out
