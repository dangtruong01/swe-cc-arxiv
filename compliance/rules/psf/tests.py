"""psf (requests): Tests and test style -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Three of the four are one checklist, in order: run the suite, write failing tests, change
the code, run the whole suite again. That ordering is the rule, so these predicates read
the command log as a *sequence* rather than as a set -- which is why they all rest on
``_common.edits`` and all declare ``heuristic=True``.

**C003 and C005 bind the same window in opposite directions** (spec §7.5). Read loosely,
C003 wants the tests to pass before the change and C005 wants them to fail before the
change. They are not in conflict once each antecedent is narrowed to the window its own
sentence names: C003 is about the untouched checkout, so its window closes at the first
edit of anything; C005 is about the tests the agent has just written, so its window opens
at that first edit and closes at the first edit of something that is not a test. The
windows are disjoint by construction, and ``test_c003_and_c005_read_disjoint_windows``
pins the resolution rather than leaving it to be remembered.

**C004 departs from its CheckTier** (spec §5). The corpus files it ``differential``; both
halves of what is checkable here -- source changed, tests changed -- are in the patch, so
no tool run is needed and none is declared. What a run would add is the part this cannot
see: that the added tests actually exercise the change. Recorded, not corrected.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.psf._common import (added_lines, contribution_target,
                                          first_edit_index, first_source_edit_index,
                                          last_edit_index, python_files, reported_failure,
                                          target, test_files, test_runs)

CATEGORY = "Tests and test style"


@rule(
    id="PSF-C003",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule, one target for the run
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, running is an act
    heuristic=True,
)
class SuiteRunAndPassingBeforeTheChange:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a test-runner invocation appears in the command log before the first
    command that edited a file, and at least one such run reports no failure.

    Fires on the submission, not on the run (§7.1): triggering on the invocation would let
    a contribution that ran nothing collect ``not_applicable`` instead of a violation.

    Heuristic on the **pass condition** (§6.2), twice over. *Before making any change* is
    read as "before the first command whose text looks like an edit", because the bundle
    records commands and not edits; and *confirm it passes* is read from an exit status
    when one was captured and from a failure banner in the output otherwise. When no
    command in the log looks like an edit at all the window is the whole log, which is the
    generous direction and is stated here rather than hidden.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "suite-before-change")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        change = first_edit_index(bundle)
        runs = test_runs(bundle, before=change)
        if not runs:
            return Violated("the test suite was never run before the first edit")
        passing = [c for c in runs if not reported_failure(c)]
        if not passing:
            return Violated(f"every pre-change run reported failures, e.g. "
                            f"{runs[0].command.strip()[:70]}")
        return Satisfied(f"suite run before any edit and reported no failure: "
                         f"{passing[0].command.strip()[:70]}")


@rule(
    id="PSF-C004",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the antecedent is the code change submitted
    reads=("files",),  # DEPARTURE from CheckTier=differential -- both halves are in the patch
    heuristic=True,
)
class TestsAddedForTheChange:
    """Pre-condition: the contribution changes Python source that is not a test.
    Pass condition: it also adds or changes a test file.

    Heuristic on the **pass condition** (§6.2): a changed test file is evidence that tests
    accompany the change, not proof that they demonstrate *it*. Proving the latter needs
    the differential run the corpus files this under, and this pack collects none.

    A documentation-only contribution finds no target rather than being graded, which is
    the reading the checklist's own scope -- *Steps for Submitting Code* -- supports.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = python_files(b, tests=False)
        if not source:
            return []
        return [target(f"tests-added:{b.instance_id}", None, None, b,
                       f"{len(source)} non-test Python file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = test_files(bundle)
        if tests:
            return Satisfied(f"{len(tests)} test file(s) changed alongside the code: "
                             f"{tests[0]}")
        return Violated("Python source changed with no test file in the contribution")


@rule(
    id="PSF-C005",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the run; the tests are the antecedent
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, the failing run is an act
    heuristic=True,
)
class NewTestsSeenToFailFirst:
    """Pre-condition: the contribution adds lines to a test file.
    Pass condition: a test run between that first edit and the first edit of something
    that is not a test reports a failure.

    Heuristic on the **pass condition** (§6.2). *Against the unmodified code* is an
    ordering the bundle does not record, so it is approximated by the window between the
    first edit of any kind and the first edit that does not name a test path -- see the
    module docstring for why that window is disjoint from C003's. A run whose failure is
    an import error rather than the new assertions still counts, which over-reports
    compliance.

    An agent that edits the source before writing its tests finds an empty window and
    fails, which is the intended reading: the checklist fixes the order. When no command
    in the log looks like an edit at all the window is the whole log, the same generous
    fallback C003 takes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        written = [p for p in test_files(b) if added_lines(b, p)]
        if not written:
            return []
        return [target(f"tests-fail-first:{b.instance_id}", None, None, (b, written),
                       f"{len(written)} test file(s) written: {written[0]}")]

    def pass_condition(self, t: Target):
        bundle, written = t.payload
        opened = first_edit_index(bundle)
        closed = first_source_edit_index(bundle)
        runs = test_runs(bundle, after=opened, before=closed)
        if not runs:
            return Violated(f"{written[0]} was written but no test run sits between "
                            f"writing it and changing the code")
        failing = [c for c in runs if reported_failure(c)]
        if not failing:
            return Violated(f"the new tests were run before the change and nothing "
                            f"reported a failure: {runs[0].command.strip()[:70]}")
        return Satisfied(f"the new tests were seen to fail first: "
                         f"{failing[0].command.strip()[:70]}")


@rule(
    id="PSF-C006",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory
    heuristic=True,
)
class EntireSuiteRunAndPassingAfterTheChange:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a test run that selects no particular test appears after the last
    command that edited a file, and no such run reports a failure.

    Heuristic on the **pass condition** (§6.2), on all three of its halves. *Entire* is
    approximated by the absence of a node id, a `-k` filter, a `--last-failed` and a
    single-file argument; *after making the change* by the index of the last command that
    looks like an edit; *every test passes* by exit status or a failure banner. The
    emphasis the source puts on `entire` is what the selectivity filter is for -- a rerun
    of the one new test satisfies neither the sentence nor this check. When no command in
    the log looks like an edit, every run in it counts as after the change -- the same
    generous fallback C003 takes, and stated here rather than hidden.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "suite-after-change")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        runs = test_runs(bundle, after=last_edit_index(bundle), whole_suite=True)
        if not runs:
            return Violated("the entire test suite was never run after the last edit")
        if failing := [c for c in runs if reported_failure(c)]:
            return Violated(f"the post-change suite run reported failures: "
                            f"{failing[0].command.strip()[:70]}")
        return Satisfied(f"entire suite run after the last edit with no reported failure: "
                         f"{runs[0].command.strip()[:70]}")
