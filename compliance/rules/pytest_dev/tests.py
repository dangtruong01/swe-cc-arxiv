"""pytest-dev: Tests and test style -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**pytest keeps its tests in `testing/`, not `tests/`** -- see ``_common.is_test_path``.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pytest_dev._common import (contribution_target, is_test_path,
                                                 python_files, ran, target)

CATEGORY = "Tests and test style"

_TOX = re.compile(r"\btox\b")


@rule(
    id="PYTEST-DEV-C017",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the rule is about the change submitted
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, running is an act
)
class SuiteRunThroughTox:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a `tox` invocation appears in the command log.

    Deliberately not "the agent ran tox" -- triggering on the tool would let a contribution
    that ran nothing collect ``not_applicable``, which is §7.1 inverted. The hedge in the
    source sentence attaches to *which environments suffice*, not to whether the suite is
    run through tox at all, so the pass condition does not name an environment.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "tox-suite")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _TOX):
            return Satisfied(f"suite run through tox: {runs[0].command.strip()[:80]}")
        return Violated("the contribution was submitted without any tox invocation")


@rule(
    id="PYTEST-DEV-C058",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the antecedent is the code change
    reads=("files",),  # spec §5: both halves are in the patch
    heuristic=True,
)
class TestsIncludedOrUpdated:
    """Pre-condition: the contribution changes non-test Python source.
    Pass condition: it also changes or adds a file under `testing/`.

    Heuristic on the **pre-condition** (§6.3). The checklist item carries its own exception
    -- *when applicable* -- and nothing in the patch settles when a change is exempt. The
    complement is used instead: a change to shipped source is taken as applicable, and a
    documentation-only or changelog-only contribution finds no target. That under-reports
    rather than manufacturing violations against changes the maintainers would exempt.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = python_files(b, tests=False)
        if not source:
            return []
        return [target(f"tests-included:{b.instance_id}", None, None, b,
                       f"{len(source)} source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        tests = [p for p in sorted(bundle.files) if is_test_path(p)]
        if tests:
            return Satisfied(f"{len(tests)} file(s) under testing/ changed alongside the "
                             f"code: {tests[0]}")
        return Violated("shipped source changed with nothing under testing/ in the "
                        "contribution")
