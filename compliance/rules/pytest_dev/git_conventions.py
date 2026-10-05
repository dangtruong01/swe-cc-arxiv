"""pytest-dev: Git and commit conventions -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Both are about ordering or content the commit itself carries, and both are heuristic for
reasons stated in their docstrings rather than because of the check's mechanics.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pytest_dev._common import CLOSES, target

CATEGORY = "Git and commit conventions"

_GIT_COMMIT = re.compile(r"\bgit\s+(?:-\S+\s+)*commit\b")
#: The runners the contributing page names, plus a bare pytest invocation.
_TEST_RUN = re.compile(r"\btox\b|\bpytest\b|\bpython\s+-m\s+pytest\b")
#: What a failing pytest run prints. Positive detection of failure, never a search for
#: success, which unrelated output produces constantly.
_TESTS_FAILED = re.compile(r"=+ (FAILURES|ERRORS) =+|^FAILED|\b\d+ failed\b", re.M)


@rule(
    id="PYTEST-DEV-C031",
    category=CATEGORY,
    ownership="created",  # spec §4 created -- the commit did not exist before the run
    reads=("commands", "commits"),  # spec §5: CheckTier=trajectory, an ordering of acts
    heuristic=True,
)
class CommitOnlyAfterTestsPass:
    """Pre-condition: the agent made at least one commit.
    Pass condition: a test run appears in the command log before the first `git commit`,
    and nothing in its output says the suite failed.

    Heuristic on the **pass condition** (§6.2). The commit log carries no timestamps that
    line up with command indices, so *before* is read as the first `git commit` in the
    command log rather than per commit; and "tests pass" is read from the absence of a
    failure banner in the captured output, because the runner's exit status is not always
    recorded. Both are sound in the failing direction and weak in the passing one.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.commits:
            return []
        return [target(f"commit-after-tests:{b.instance_id}", None, None, b,
                       f"{len(b.commits)} commit(s)")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        first_commit = next((c.index for c in bundle.commands
                             if _GIT_COMMIT.search(c.command)), None)
        runs = [c for c in bundle.commands if _TEST_RUN.search(c.command)
                and (first_commit is None or c.index < first_commit)]
        if not runs:
            return Violated("committed without running the test suite first")
        for command in runs:
            if _TESTS_FAILED.search(command.output or ""):
                return Violated(f"committed after a failing run: "
                                f"{command.command.strip()[:70]}")
        return Satisfied(f"{len(runs)} test run(s) before the first commit, none reporting "
                         f"failure")


@rule(
    id="PYTEST-DEV-C036",
    category=CATEGORY,
    ownership="created",  # spec §4 created -- the message and PR text are both new
    reads=("commits", "pr_text"),  # spec §5: the guide accepts either location
    heuristic=True,
)
class IssueClosedByKeyword:
    """Pre-condition: the agent made a commit, read as a change submitted to fix an issue.
    Pass condition: an autoclose keyword and issue number appear in a commit message or in
    the pull request text.

    Heuristic on the **pre-condition** (§6.3). The rule's real antecedent is *the change
    fixes an issue*, and nothing in the bundle establishes that -- the task's provenance is
    a fact about the benchmark, not about the contribution. Every commit is therefore
    selected, which over-fires on a change that fixes nothing and pushes the activation
    rate up. Reported rather than narrowed, because narrowing it would need a harness fact
    the corpus does not license using.

    The guide names `closes #XYZW` and links GitHub's documentation, which fixes the whole
    keyword family, so `fixes` and `resolves` are accepted rather than reported.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.commits:
            return []
        return [target(f"closes:{b.instance_id}", None, None, b,
                       f"{len(b.commits)} commit(s)")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for commit in bundle.commits:
            if match := CLOSES.search(commit.raw or f"{commit.summary}\n{commit.body}"):
                return Satisfied(f"commit carries `{match.group(0)}`")
        if bundle.pr_text and (match := CLOSES.search(bundle.pr_text)):
            return Satisfied(f"pull request text carries `{match.group(0)}`")
        return Violated("no autoclose keyword and issue number in any commit message or "
                        "in the pull request text")
