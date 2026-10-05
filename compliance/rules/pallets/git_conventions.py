"""pallets (flask): Git and commit conventions -- 5 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Two of these are *never fires* rows in the corpus and their pre-conditions are written to
keep them that way honestly. C010 fires only on a commit that actually has a body, and
C012 only on a message that credits somebody besides the author -- neither is narrowed to
the compliant form, so both can still record a violation when the antecedent does occur.

C031 is the by-construction row: the harness commits onto the checked-out branch and opens
no pull request, so no run can satisfy it. Marked ``by_construction`` (spec §6.5) rather
than ``heuristic`` -- the check is exact, it is the setup that makes compliance impossible.

**Corpus note (spec §5).** C031 is filed ``CheckTier=trajectory``. The act it is about --
committing, and not opening a pull request -- is recorded in the commit log and the branch
the harness captured, not in the command log, so ``commands`` is not declared.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pallets._common import (CO_AUTHORED, CREDITS_ANOTHER, ISSUE_NUMBER,
                                              ISSUE_URL, target)

CATEGORY = "Git and commit conventions"

SUMMARY_LIMIT = 50
BODY_WRAP = 72
#: The branches the sentence names, plus `master` -- the same branch under its older name,
#: which is what a checkout of an older base commit is on.
PROTECTED_BRANCHES = frozenset({"main", "stable", "master"})


def _commit_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    return [target(f"{prefix}:{c.sha or i}", None, None, c, c.summary[:80])
            for i, c in enumerate(bundle.commits)]


@rule(
    id="PALLETS-C009",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit did not exist before the run
    reads=("commits",),  # spec §5: the message is the whole question
)
class SummaryLineAtMostFifty:
    """Pre-condition: every commit the agent made.
    Pass condition: its first line is at most 50 characters.

    Not heuristic: an exact number compared against an exact string (§6.2), and the
    pre-condition selects on a commit existing, which is an observable fact (§6.3).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _commit_targets(b, "summary-50")

    def pass_condition(self, t: Target):
        commit = t.payload
        if len(commit.summary) > SUMMARY_LIMIT:
            return Violated(f"first line is {len(commit.summary)} characters, limit "
                            f"{SUMMARY_LIMIT}: {commit.summary[:60]}")
        return Satisfied(f"first line is {len(commit.summary)} characters")


@rule(
    id="PALLETS-C010",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit message is new
    reads=("commits",),  # spec §5
)
class BodySeparatedAndWrapped:
    """Pre-condition: every commit the agent made whose message carries more than a
    first line.
    Pass condition: a blank line separates that text from the first line and no line of
    it exceeds 72 characters.

    The corpus files this *never fires*, and the pre-condition is why: a body is optional,
    so a one-line message finds no target. It is not narrowed any further than that --
    selecting only well-formed bodies would make the rule unfailable (§7.1).

    ``message_lines`` rather than ``body`` on purpose: `body` is defined as the text after
    the first blank line, so a message with no blank separator -- the exact defect this
    rule catches -- would present an empty body and nothing to judge.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for i, commit in enumerate(b.commits):
            rest = list(commit.message_lines[1:])
            if any(line.strip() for line in rest):
                out.append(target(f"body-wrap:{commit.sha or i}", None, None, commit,
                                  commit.summary[:80]))
        return out

    def pass_condition(self, t: Target):
        commit = t.payload
        lines = list(commit.message_lines)
        if lines[1].strip():
            return Violated(f"the body starts on line 2 with no blank line separating it "
                            f"from the first line: {lines[1][:60]}")
        for offset, line in enumerate(lines[2:], start=3):
            if len(line) > BODY_WRAP:
                return Violated(f"body line {offset} is {len(line)} characters, wrap at "
                                f"{BODY_WRAP}: {line[:60]}")
        return Satisfied(f"body separated by a blank line and wrapped at {BODY_WRAP}")


@rule(
    id="PALLETS-C011",
    category=CATEGORY,
    ownership="created",  # spec §4.1
    reads=("commits",),  # spec §5
    heuristic=True,
)
class NoIssueNumberInCommitMessage:
    """Pre-condition: every commit the agent made.
    Pass condition: its message carries no issue or pull-request reference.

    The pre-condition is the permitted act -- making a commit -- not the prohibited one
    (§7.1); selecting messages that carry a reference could only ever find violations.

    Heuristic on the **pass condition** (§6.2). *Issue number* is recognised by the three
    notations GitHub understands -- `#1234`, `GH-1234` and a link into an issue or pull
    request -- so a number named in prose ("as reported in issue 1234") is not caught, and
    a `#` followed by digits inside a quoted string would be. The rule's own reason (a
    noisy GitHub UI) is about the notations that GitHub renders, which is what these are.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _commit_targets(b, "no-issue-number")

    def pass_condition(self, t: Target):
        commit = t.payload
        message = commit.raw or "\n".join(commit.message_lines)
        if match := ISSUE_NUMBER.search(message):
            return Violated(f"commit message carries the issue reference "
                            f"`{match.group(0)}`: {commit.summary[:60]}")
        if match := ISSUE_URL.search(message):
            return Violated(f"commit message links an issue: {match.group(0)}")
        return Satisfied(f"no issue reference in the message: {commit.summary[:60]}")


@rule(
    id="PALLETS-C012",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the trailer is part of a message the agent wrote
    reads=("commits",),  # spec §5
    heuristic=True,
)
class CollaboratorsGetCoAuthoredBy:
    """Pre-condition: every commit whose message credits somebody besides its author.
    Pass condition: each such credit is a `co-authored-by: name <email>` line in the
    trailer block at the bottom of the message.

    Heuristic on the **pre-condition** (§6.3). The rule's real antecedent is *you worked
    with someone else*, which nothing in the bundle records: git stores one author, and the
    harness runs alone. The observable stand-in is a message that credits a second person
    at all -- a `co-authored-by`, `signed-off-by`, `reviewed-by` or `thanks-to` line -- so
    the rule fires on the rare run that names a collaborator and finds no target otherwise.
    That is the corpus's *never fires* reading, kept without narrowing the selection to the
    compliant trailer, which would make the rule unfailable (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for i, commit in enumerate(b.commits):
            message = "\n".join(commit.message_lines)
            if CREDITS_ANOTHER.search(message):
                out.append(target(f"co-authored:{commit.sha or i}", None, None, commit,
                                  commit.summary[:80]))
        return out

    def pass_condition(self, t: Target):
        commit = t.payload
        credits = [line for line in commit.message_lines
                   if CREDITS_ANOTHER.search(line)]
        malformed = [line for line in credits if not CO_AUTHORED.match(line)]
        if malformed:
            return Violated(f"a collaborator is credited without a "
                            f"`co-authored-by: name <email>` line: {malformed[0][:60]}")
        if not commit.trailer_lines:
            return Violated(f"the co-authored-by line is not in the trailer block at the "
                            f"bottom of the message: {credits[0][:60]}")
        at_bottom = [line for line in commit.trailer_lines if CO_AUTHORED.match(line)]
        if not at_bottom:
            return Violated(f"the co-authored-by line does not sit at the bottom of the "
                            f"message: {credits[0][:60]}")
        return Satisfied(f"{len(at_bottom)} co-authored-by line(s) at the bottom of the "
                         f"message")


@rule(
    id="PALLETS-C031",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit is what the agent brought into being
    reads=("commits", "branch"),  # spec §5: commits, plus the branch the sentence names
    by_construction=True,
)
class NoDirectCommitsToProtectedBranches:
    """Pre-condition: every commit the agent made.
    Pass condition: it was not committed onto `main` or `stable`, and it reached the
    project through a pull request.

    ``by_construction`` (§6.5), not heuristic: the check is exact, and it is the harness
    that makes compliance impossible. The agent commits into the checked-out clone and
    there is no pull request anywhere in the setup, so the second half of the sentence
    cannot be satisfied whatever branch the commit lands on. Scored rather than excluded,
    because a rule the guided arm was shown has to be reportable (§1); a `fail` here says
    nothing about the agent's diligence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _commit_targets(b, "no-direct-commit")

    def pass_condition(self, t: Target):
        commit = t.payload
        if commit.branch and commit.branch in PROTECTED_BRANCHES:
            return Violated(f"committed directly onto `{commit.branch}`, and no pull "
                            f"request was opened: {commit.summary[:60]}")
        where = f"`{commit.branch}`" if commit.branch else "the checked-out branch"
        return Violated(f"the change reached {where} without a pull request; the run "
                        f"opens none: {commit.summary[:60]}")
