"""psf (requests): Git and commit conventions -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

One rule, and the whole difficulty is in what "explains why" can be read off a commit
message. The corpus sentence names the failing form exactly -- a message that is no more
than ``Fixes #NNNN`` -- and says nothing mechanical about the satisfying one, so the
predicate grades the floor and declares the rest as approximation (§6.6).
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.psf._common import target

CATEGORY = "Git and commit conventions"

#: `#1234`, `GH-1234`, `gh1234`, and the same preceded by an autoclose keyword.
_ISSUE_REF = re.compile(
    r"(?:\b(?:clos(?:e|es|ed)|fix(?:e[sd])?|resolv(?:e|es|ed))\b[\s:]*)?(?:#|\bGH-?)\d+",
    re.I)
#: The keyword on its own -- `Fixes the redirect loop` has no number after it.
_AUTOCLOSE = re.compile(r"\b(?:clos(?:e|es|ed)|fix(?:e[sd])?|resolv(?:e|es|ed))\b", re.I)
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")

#: How many words a message must carry beyond its issue reference before it counts as
#: saying anything at all. Three is the smallest count that admits a short clause and
#: still rejects every spelling of the form the source quotes as insufficient.
MIN_RESIDUAL_WORDS = 3


def _message_of(commit) -> str:
    """The message the agent wrote, without its trailers.

    ``raw`` is the whole ``git log --pretty=raw`` block -- author line, stat, the lot --
    so counting words in it would score the log format rather than the message.
    """
    lines = list(commit.message_lines) or [commit.summary, *commit.body.split("\n")]
    trailers = set(commit.trailer_lines)
    return "\n".join(line for line in lines if line not in trailers)


@rule(
    id="PSF-C024",
    category=CATEGORY,
    ownership="created",  # spec §4.1 -- the commit did not exist before the run
    reads=("commits",),  # spec §5: the message is the whole question; CheckTier=static agrees
    heuristic=True,
)
class CommitMessageExplainsWhy:
    """Pre-condition: each commit the agent made.
    Pass condition: its message says something beyond the issue it closes -- at least
    three words survive the removal of every issue reference and autoclose keyword.

    Heuristic on the **pass condition** (§6.2). *Explains why* is meaning, and nothing
    reads meaning off a commit message; what is exact is the floor the source quotes --
    a message that is no more than `Fixes #NNNN` -- and a residual word count is the
    proxy for clearing it. The check is therefore sound in the failing direction and weak
    in the passing one: `Fix the redirect loop` clears the floor while still saying what
    rather than why, and is scored as a pass.

    The pre-condition is exact: every commit is judged, because every commit message is
    subject to the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"why:{c.sha or i}", None, None, c, c.summary[:80])
                for i, c in enumerate(b.commits)]

    def pass_condition(self, t: Target):
        commit = t.payload
        message = _message_of(commit)
        residual = _AUTOCLOSE.sub(" ", _ISSUE_REF.sub(" ", message))
        words = _WORD.findall(residual)
        if len(words) < MIN_RESIDUAL_WORDS:
            return Violated(
                f"the commit message says no more than which issue it closes "
                f"({len(words)} word(s) beyond the reference): {commit.summary[:60]!r}")
        return Satisfied(f"{len(words)} word(s) beyond the issue reference: "
                         f"{commit.summary[:60]!r}")
