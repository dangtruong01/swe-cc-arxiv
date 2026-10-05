"""pydata (xarray): Git and commit conventions -- 5 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Two of these read evidence no other pack has needed. C018 and C073 are about what the agent
*left behind* -- files modified but not committed, files created but never added -- which
`files_worktree` and `status_entries` carry precisely because deciding what belongs in a
contribution is itself graded behaviour.

C088 is the awkward one and its docstring says why.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pydata._common import (DOC_ROOT, ISSUE_REF, SKIP_CI, TEST_UPSTREAM,
                                             contribution_target, documentation_only,
                                             target)

CATEGORY = "Git and commit conventions"

#: Files whose change plausibly needs the upstream-dev CI: the pinned environments and the
#: workflow definitions themselves.
_UPSTREAM_SENSITIVE = re.compile(r"^ci/|^\.github/workflows/|^pyproject\.toml$")


@rule(
    id="PYDATA-C018",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files", "files_worktree"),  # spec §5: the gap between the two IS the rule
)
class EveryModifiedFileIsCommitted:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: nothing it modified was left out of the commit.

    `files` is what was committed and `files_worktree` is everything in the tree at submit
    time, so the difference between them is exactly what this rule is about. Note the
    direction: a file left uncommitted is a violation here even though SWE-bench would
    still grade it, because the rule is about the commit and not about the fix working.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files and not b.files_worktree:
            return []
        return [target(f"committed:{b.instance_id}", None, None, b,
                       f"{len(b.files)} committed, {len(b.files_worktree)} in the tree")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if left := bundle.uncommitted_paths():
            return Violated(f"{len(left)} modified file(s) never committed, "
                            f"e.g. {left[0]}")
        return Satisfied(f"every one of the {len(bundle.files)} modified file(s) is in the "
                         f"commit")


@rule(
    id="PYDATA-C073",
    category=CATEGORY,
    ownership="touched",  # spec §4.4
    reads=("files", "status"),  # spec §5: `??` entries are what "not added" looks like
)
class EveryNewFileIsAdded:
    """Pre-condition: the agent submitted a contribution and the harness captured
    `git status`.
    Pass condition: no path is left untracked.

    Distinct from C018: a *modified* file that is not committed shows up as a worktree
    difference, whereas a *new* file that was never `git add`-ed shows up as `??` in
    status. Both are ways to leave work out of the commit and the guide names them
    separately.

    Selects nothing when status was not captured, rather than reading an empty capture as
    a clean tree.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files or not b.status_entries:
            return []
        return [target(f"added:{b.instance_id}", None, None, b,
                       f"{len(b.status_entries)} status entr(ies)")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        untracked = [path for code, path in bundle.status_entries if code.strip() == "??"]
        if untracked:
            return Violated(f"{len(untracked)} new file(s) never added to git, "
                            f"e.g. {untracked[0]}")
        return Satisfied("no untracked file left behind")


@rule(
    id="PYDATA-C076",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit did not exist before the run
    reads=("commits",),  # spec §5: the message is the whole question
    heuristic=True,
)
class CommitReferencesTheIssue:
    """Pre-condition: each commit the agent made, read as a change with a relevant issue.
    Pass condition: its message carries `GH1234` or `#1234`.

    Heuristic on the **pre-condition** (§6.3). The rule's real antecedent is *the change
    relates to a GitHub issue*, and nothing in the bundle establishes that -- the task's
    provenance is a fact about the benchmark, not about the contribution. Every commit is
    selected, which over-fires on a change that relates to none and pushes the activation
    rate up. Reported rather than narrowed, because narrowing it would need a harness fact
    the corpus does not license using.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"issue-ref:{c.sha or i}", None, None, c, c.summary[:80])
                for i, c in enumerate(b.commits)]

    def pass_condition(self, t: Target):
        commit = t.payload
        message = commit.raw or f"{commit.summary}\n{commit.body}"
        if match := ISSUE_REF.search(message):
            return Satisfied(f"commit references {match.group(0)}")
        return Violated(f"commit message carries no GH1234 or #1234 reference: "
                        f"{commit.summary[:60]}")


@rule(
    id="PYDATA-C088",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit is new
    reads=("commits", "files"),  # spec §5: the tag is on the commit, the trigger in the patch
    heuristic=True,
)
class UpstreamCiTagWhenTheChangeNeedsIt:
    """Pre-condition: each commit in a contribution that touches the CI configuration or
    the pinned dependencies.
    Pass condition: its first line carries `[test-upstream]`.

    Heuristic on the **pre-condition**, and the weakest rule in this pack. The sentence's
    real antecedent is *you want the upstream development CI to run*, which is an intention
    and appears nowhere in the evidence. Requiring the tag on every commit would be plainly
    wrong -- most changes should not run it -- so the antecedent is approximated by the
    changes for which upstream testing is conventionally wanted: `ci/`, the workflow files,
    and `pyproject.toml`.

    That approximation will both over- and under-fire, and the direction is not predictable.
    It is declared and kept rather than dropped, because the alternative -- selecting only
    commits that already carry the tag -- is §7.1 inverted and could never record a
    violation.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        sensitive = [p for p in sorted(b.files) if _UPSTREAM_SENSITIVE.search(p)]
        if not sensitive or not b.commits:
            return []
        return [target(f"upstream:{c.sha or i}", None, None, (c, sensitive),
                       f"touches {sensitive[0]}")
                for i, c in enumerate(b.commits)]

    def pass_condition(self, t: Target):
        commit, sensitive = t.payload
        if TEST_UPSTREAM.search(commit.summary):
            return Satisfied(f"first line carries [test-upstream]: {commit.summary[:60]}")
        return Violated(f"changes {sensitive[0]} without [test-upstream] on the first "
                        f"line: {commit.summary[:60]}")


@rule(
    id="PYDATA-C089",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("commits", "files"),  # spec §5
)
class SkipCiTagOnDocumentationOnlyCommits:
    """Pre-condition: each commit in a contribution that changes documentation and nothing
    else.
    Pass condition: its first line carries `[skip-ci]`.

    Not heuristic, and worth contrasting with C088. *Documentation-only* is decidable from
    the patch -- every changed path is under `doc/` or is a documentation source -- so the
    antecedent here is exact where C088's is an intention. Same category, same shape of
    sentence, and only one of them is mechanically checkable.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.commits or not documentation_only(b):
            return []
        return [target(f"skip-ci:{c.sha or i}", None, None, c, c.summary[:80])
                for i, c in enumerate(b.commits)]

    def pass_condition(self, t: Target):
        commit = t.payload
        if SKIP_CI.search(commit.summary):
            return Satisfied(f"first line carries [skip-ci]: {commit.summary[:60]}")
        return Violated(f"documentation-only commit without [skip-ci]: "
                        f"{commit.summary[:60]}")
