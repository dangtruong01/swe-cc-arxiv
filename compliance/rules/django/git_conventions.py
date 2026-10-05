"""Django: Git and commit conventions -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

A small category, and both rules sit at opposite ends of the decidability spectrum.

**C046 is where Django differs from almost every other project**, which is why it is worth
stating rather than inheriting. Most style guides ask for an imperative subject line and no
trailing period; Django asks for the exact opposite -- past tense, and a period. A checker
written from habit rather than from the corpus would grade this backwards and report a
compliant commit as a violation, so the corpus sentence is the specification and the tests
pin the reading.

**C044 fires on pushes, not on force-pushes.** The prohibition is *do not force-push*; if
the pre-condition selected force-pushes it would only ever see violations and could never
record a compliant push, which is §4.2 in its purest form. Every ``git push`` is the
antecedent and the force flags are the grading.
"""

from __future__ import annotations

import re

from compliance.core.models import Commit, EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule

CATEGORY = "Git and commit conventions"

_GIT_PUSH = re.compile(r"\bgit\s+(?:-\S+\s+)*push\b")
# Every spelling of a force push git accepts. `--force-with-lease` is included on purpose:
# it is safer than `--force` but it still rewrites published history, which is the thing
# the rule is about. The refspec form `git push origin +main` is the one people forget.
_FORCE_FLAG = re.compile(r"(?:^|\s)(--force-with-lease(?:=\S+)?|--force-if-includes"
                         r"|--force\b|-f\b|-\w*f\w*\b(?=\s|$))")
_FORCE_REFSPEC = re.compile(r"\s\+[^\s:]+:[^\s:]+")

# Django subject lines read "Fixed #12345 -- Added a thing." The graded verb is the first
# word, or the first word after the `--` separator when a ticket prefix comes first.
_TICKET_PREFIX = re.compile(r"^\s*(?:Fixed|Refs|Reverted|Reverted:)\s*#?\d*\s*(?:--)?\s*", re.I)
_SEPARATOR = re.compile(r"\s--\s")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
# `-ed` plus the irregular past-tense verbs a commit subject actually uses. This is a
# proxy for tense, not a tense checker, which is what `heuristic=True` declares.
_IRREGULAR_PAST = frozenset("""
added made took began broke brought built bought caught chose came did drew drove ate fell
felt fought found flew forgot got gave went grew had heard held kept knew left lent let
lost meant met paid put read ran said saw sold sent set showed shut sang sat slept spoke
spent stood taught told thought understood woke wore won wrote became bound bent bet bit
bled blew cast cost cut dealt dug drank fed fit fled flung forbade froze hid hit hung hurt
laid led lit lay quit rid rose rang sank shed shone shot shrank slid slit sought sped spun
split spread sprang stole stuck stung struck swept swam swung threw thrust trod woven wound
withdrew
""".split())


def _commit_targets(bundle: EvidenceBundle) -> list[Target]:
    """Antecedent the commit-message rules share: the agent made a commit."""
    return [
        Target(key=f"commit:{commit.sha or index}", file=None, line_span=None,
               source="commit", payload=commit, snippet=commit.summary)
        for index, commit in enumerate(bundle.commits)
    ]


def _looks_past_tense(word: str) -> bool:
    lowered = word.lower()
    return lowered.endswith("ed") or lowered in _IRREGULAR_PAST


@rule(id="DJANGO-C044", category=CATEGORY, ownership="created", heuristic=True,
      reads=("commands",))
class NoForcePush:
    """Pre-condition: each `git push` the agent ran.
    Pass condition: it was not a force push.

    ``heuristic`` for what it cannot see rather than for what it can. Whether a push rewrote
    *published* history on a *django/django* branch, and whether the team had agreed to it,
    are facts about a remote and a mailing list; neither is in a trajectory. What is decided
    here is the observable half -- a force flag or a `+refspec` on a push -- and it is read
    as the violation the rule names. A force push to the agent's own throwaway fork would be
    graded the same way, which is the direction the proxy errs in.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [
            Target(key=f"push:{command.index}", file=None, line_span=None,
                   source="trajectory", payload=command, snippet=command.command.strip()[:120])
            for command in b.commands
            if _GIT_PUSH.search(command.command)
        ]

    def pass_condition(self, t: Target):
        text = t.payload.command
        if match := _FORCE_FLAG.search(text):
            return Violated(f"force push (`{match.group(1).strip()}`): {text.strip()[:80]}")
        if match := _FORCE_REFSPEC.search(text):
            return Violated(f"force push via refspec (`{match.group(0).strip()}`): "
                            f"{text.strip()[:80]}")
        return Satisfied(f"plain push: {text.strip()[:80]}")


@rule(id="DJANGO-C046", category=CATEGORY, ownership="created", heuristic=True,
      reads=("commits",))
class PastTenseSubjectWithPeriod:
    """Pre-condition: every commit the agent made.
    Pass condition: its subject line is phrased in the past tense and ends with a period.

    Two clauses, graded separately so the reason says which one failed. The period is exact.
    The tense is not: `-ed` plus a list of irregular verbs is a proxy, and it is declared as
    one. It is applied to the leading verb -- the first word, or the first word after the
    `Fixed #12345 --` prefix Django puts in front of a ticket-closing subject -- because that
    is the word the convention is about.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _commit_targets(b)

    def pass_condition(self, t: Target):
        commit: Commit = t.payload
        summary = commit.summary.strip()
        if not summary:
            return Violated("commit has an empty subject line")
        problems = []
        if not summary.endswith("."):
            problems.append("subject does not end with a period")
        if not any(_looks_past_tense(w) for w in _leading_verbs(summary)):
            problems.append(f"subject is not phrased in the past tense: {summary[:60]!r}")
        if problems:
            return Violated("; ".join(problems))
        return Satisfied(summary[:60])


def _leading_verbs(summary: str) -> list[str]:
    """The words that could be the subject's verb: the first, and the one after `--`.

    Django writes `Fixed #12345 -- Added a shortcut.`, where both `Fixed` and `Added` are
    past tense and either establishes compliance. A subject with neither has no past-tense
    verb where the convention puts one.
    """
    candidates = []
    if word := _WORD.search(summary):
        candidates.append(word.group(0))
    stripped = _TICKET_PREFIX.sub("", summary)
    if stripped != summary and (word := _WORD.search(stripped)):
        candidates.append(word.group(0))
    if match := _SEPARATOR.search(summary):
        if word := _WORD.search(summary[match.end():]):
            candidates.append(word.group(0))
    return candidates
