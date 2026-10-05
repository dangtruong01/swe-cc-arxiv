"""astropy: Git and commit conventions -- 3 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

All three are conditional: *when the commit fixes an issue*, *when the commits are not
ready for CI*, *when the fix is a trivial documentation fix*. None of those conditions is
written in the commit, so each pre-condition stands in for one and each says so. The
alternative -- selecting the commits that already carry the token -- is §7.1 inverted and
could never record a violation.

C067's stand-in is the narrowest of the three and is worth stating here as well as in its
docstring: *not ready for CI* is an intention, approximated by the work-in-progress markers
a contributor writes when they hold that intention. It will under-fire, and that direction
is chosen deliberately over grading every commit against a token most commits must not
carry.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.astropy._common import (added_text, is_doc_path, target)

CATEGORY = "Git and commit conventions"

#: The auto-closing form CONTRIBUTING names: ``Closes #123``. GitHub accepts several
#: keywords; the corpus sentence names this one, so this is what is looked for, with the
#: other auto-closing keywords accepted as satisfying the same purpose.
CLOSES = re.compile(r"\b(clos(?:e|es|ed)|fix(?:e[sd])?|resolv(?:e|es|ed))\b\s*:?\s*#\d+",
                    re.I)

#: Both spellings are interchangeable per CONTRIBUTING.md.
CI_SKIP = re.compile(r"\[\s*(ci[ -]skip|skip[ -]ci)\s*\]", re.I)

#: What a contributor writes when a branch is not ready to be tested or merged.
NOT_READY = re.compile(r"\bWIP\b|\bwork in progress\b|\[\s*wip\s*\]|\bdo not merge\b"
                       r"|\bdon'?t merge\b|\bdraft\b|\bscratch\b|\btemp(?:orary)? commit\b",
                       re.I)

#: reStructuredText markup of any kind. CONTRIBUTING exempts a documentation fix from
#: ``[ci skip]`` once it "contains special markup", so a line carrying markup takes the
#: change out of the trivial class.
SPECIAL_MARKUP = re.compile(r"``|:[a-zA-Z:+-]+:`|^\s*\.\.\s|\|[A-Za-z][A-Za-z0-9_]*\|")


def _commit_targets(bundle: EvidenceBundle, prefix: str, payload=None):
    return [target(f"{prefix}:{c.sha or i}", None, None,
                   c if payload is None else (c, payload), c.summary[:80], source="commit")
            for i, c in enumerate(bundle.commits)]


def _message(commit) -> str:
    return commit.raw or "\n".join((commit.summary,) + tuple(commit.body_lines))


@rule(
    id="ASTROPY-C059",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit did not exist before the run
    reads=("commits",),  # spec §5: the message is the whole question
    heuristic=True,
)
class ClosesIssueOnALaterLine:
    """Pre-condition: each commit the agent made, read as a commit that fixes an issue.
    Pass condition: an auto-closing ``Closes #<issue>`` reference appears on the second or
    a later line of its message.

    Heuristic on the **pre-condition** (§6.3). The sentence's antecedent is *the commit
    fixes an issue*, and nothing in the bundle establishes that: the task's provenance is a
    fact about the benchmark, not about the contribution, so every commit is selected and
    the activation rate is pushed up by commits that fix nothing. Narrowing it to commits
    that already carry a reference would be §7.1 inverted.

    The line position is graded exactly. A reference on the summary line alone is a
    violation, because that is what the sentence forbids.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _commit_targets(b, "closes")

    def pass_condition(self, t: Target):
        commit = t.payload
        lines = _message(commit).split("\n")
        for line in lines[1:]:
            if match := CLOSES.search(line):
                return Satisfied(f"commit closes an issue on a later line: {match.group(0)}")
        if lines and CLOSES.search(lines[0]):
            return Violated(f"the issue reference is on the summary line, not the second "
                            f"or a later one: {lines[0][:60]}")
        return Violated(f"no `Closes #<issue>` on the second or a later line: "
                        f"{commit.summary[:60]}")


@rule(
    id="ASTROPY-C067",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit is new
    reads=("commits",),  # spec §5: both the condition's proxy and the token are in the message
    heuristic=True,
)
class CiSkipOnCommitsNotReadyForCi:
    """Pre-condition: each commit the agent marked as work in progress, which is what a
    commit not ready for CI looks like.
    Pass condition: its message also carries ``[ci skip]`` or ``[skip ci]``.

    Heuristic on the **pre-condition** (§6.3): *not ready for CI testing* is an intention,
    and the only trace it leaves is the vocabulary a contributor uses for it -- WIP, draft,
    do not merge. Selecting every commit instead would grade a token that most commits must
    **not** carry, so nearly every compliant run would read as a violation; selecting the
    commits that already carry the token would be §7.1 inverted. Under-firing is the chosen
    direction and it is declared.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"ci-skip:{c.sha or i}", None, None, c, c.summary[:80],
                       source="commit")
                for i, c in enumerate(b.commits) if NOT_READY.search(_message(c))]

    def pass_condition(self, t: Target):
        commit = t.payload
        if match := CI_SKIP.search(_message(commit)):
            return Satisfied(f"work-in-progress commit carries {match.group(0)}")
        return Violated(f"commit is marked as not ready but carries no [ci skip] or "
                        f"[skip ci]: {commit.summary[:60]}")


@rule(
    id="ASTROPY-C216",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit is new; §4.2, the antecedent is the patch
    reads=("commits", "files"),  # spec §5: the token is on the commit, the trigger in the patch
    heuristic=True,
)
class CiSkipOnTrivialDocumentationFix:
    """Pre-condition: each commit of a contribution that changes documentation only and
    introduces no reStructuredText markup, which is what a trivial documentation fix looks
    like.
    Pass condition: its message carries ``[ci skip]``.

    Heuristic on the **pre-condition** (§6.3), but only half of it is a proxy. CONTRIBUTING
    gives three conditions -- typo, spelling or grammar; no special markup; not associated
    with code changes -- and the second and third are decidable from the patch and are
    checked exactly. *Typo, spelling or grammar* is not, so a substantive documentation
    rewrite in plain prose is selected here and should not be.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        paths = sorted(b.files)
        if not b.commits or not paths or not all(is_doc_path(p) for p in paths):
            return []
        if any(SPECIAL_MARKUP.search(added_text(b, p)) for p in paths):
            return []
        return [target(f"doc-ci-skip:{c.sha or i}", None, None, (c, paths),
                       c.summary[:80], source="commit")
                for i, c in enumerate(b.commits)]

    def pass_condition(self, t: Target):
        commit, paths = t.payload
        if match := CI_SKIP.search(_message(commit)):
            return Satisfied(f"trivial documentation fix carries {match.group(0)}")
        return Violated(f"documentation-only change to {paths[0]} with no markup carries "
                        f"no [ci skip]: {commit.summary[:60]}")
