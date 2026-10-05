"""pytest-dev: Code and quality -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Both name one tool and one invocation, so both grade exactly off the command log. Neither
is heuristic: the pass condition is the presence of a named command, which is form rather
than meaning (§6.2).
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pytest_dev._common import contribution_target, ran

CATEGORY = "Code and quality"

_PRE_COMMIT_INSTALL = re.compile(r"\bpre-commit\b[^\n]*\binstall\b")
#: `tox -e linting`, and the combined form `tox -e linting,py313` the guide prints.
_TOX_LINTING = re.compile(r"\btox\b[^\n]*-e\s*[^\s]*\blinting\b")


@rule(
    id="PYTEST-DEV-C015",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the rule is about the checkout being worked in
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory
)
class PreCommitInstalled:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a `pre-commit install` invocation appears in the command log.

    The guide ties the step to style-guide enforcement and offers no alternative, so the
    satisfying state is the named command. Enabling without installing leaves no trace the
    bundle carries, which is a limit of the evidence rather than a reading of the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "pre-commit")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _PRE_COMMIT_INSTALL):
            return Satisfied(f"pre-commit installed: {runs[0].command.strip()[:80]}")
        return Violated("pre-commit was never installed on the checkout")


@rule(
    id="PYTEST-DEV-C018",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory
)
class LintingEnvironmentRun:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a tox invocation naming the `linting` environment appears in the
    command log.

    Separate from C017 on purpose: `tox -e linting,py313` satisfies both, but a run of the
    test environments alone satisfies only C017, and the coding-style checks are what this
    rule is about.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "tox-linting")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _TOX_LINTING):
            return Satisfied(f"linting environment run: {runs[0].command.strip()[:80]}")
        return Violated("the `linting` tox environment was never run")
