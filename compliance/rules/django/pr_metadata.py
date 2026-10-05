"""Django: PR and release metadata -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**Django's tracker is Trac, and its ticket references live in the commit message, not in
the pull request.** `Fixed #12345 -- ...` closes a ticket; `Refs #12345` mentions one
without closing it. So two of the four rules here read ``commits`` rather than ``pr_text``,
which is unusual for this category and is what the corpus says.

**C052's antecedent is the hard one, and the reading is stated rather than buried.** The
rule is *"start the commit message with `Fixed #xxxxx` **when the commit closes ticket
xxxxx**"*. Nothing in a patch says which ticket a change closes -- the fact lives in Trac.
What the harness does know is that every run is a task to resolve one reported issue, and
that resolving it is what the agent was asked to do. So the antecedent is taken to be
established by the run itself: a contribution with commits is a contribution that closes
the ticket it was given. That is an assumption, it is the reason the rule is flagged
``heuristic``, and it is deliberately preferred to the alternative -- firing only on
messages that already say `Fixed #`, which would make the rule unable to fail and its rate
a tautology (§4.2).

C053 needs no such assumption: a ticket number in a message that is not the closing one is
directly observable, and both the compliant and the non-compliant spelling of it fire.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.django.tests import (
    _run_target,
    _target,
    changed_source,
    is_doc_path,
    is_release_notes_path,
    modules,
    new_public_definitions,
    owned_files,
)

CATEGORY = "PR and release metadata"

_FIXED_PREFIX = re.compile(r"^\s*Fixed\s+#(\d+)\b")
_TICKET = re.compile(r"#(\d+)\b")
# `Refs #123, #456` -- one keyword can introduce several numbers, so the check looks back
# along the line for the keyword rather than requiring it immediately before each number.
_REFS_BEFORE = re.compile(r"\bRefs\b[^.;\n]*$", re.I)


@rule(id="DJANGO-C052", category=CATEGORY, ownership="created", heuristic=True,
      reads=("commits",))
class ClosingCommitNamesTicket:
    """Pre-condition: the agent committed a contribution resolving the reported issue it
    was given, so one of its commits closes that ticket.
    Pass condition: a commit message starts with `Fixed #xxxxx`.

    Graded across the commit series rather than per commit, because Django's convention
    puts `Fixed #` on the *closing* commit only -- an intermediate commit in a series
    correctly says `Refs #` instead, and failing it here would penalise the convention it
    is meant to enforce. One target for the contribution; it passes when any commit carries
    the closing form.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.commits:
            return []
        return [_run_target(b, "closes", tuple(b.commits),
                            f"{len(b.commits)} commit(s)")]

    def pass_condition(self, t: Target):
        for commit in t.payload:
            if match := _FIXED_PREFIX.match(commit.summary):
                return Satisfied(f"closing commit names ticket #{match.group(1)}")
        summaries = [c.summary.strip()[:50] for c in t.payload]
        return Violated("no commit message starts with `Fixed #xxxxx`, so the ticket the "
                        f"contribution resolves is never closed: {summaries[:3]}")


@rule(id="DJANGO-C053", category=CATEGORY, ownership="created", heuristic=True,
      reads=("commits",))
class NonClosingTicketUsesRefs:
    """Pre-condition: each ticket number in a commit message that is not the one the
    leading `Fixed #xxxxx` closes.
    Pass condition: it is introduced by `Refs`.

    ``heuristic`` for the *"but not closing"* clause only. A number that is not the subject
    line's `Fixed #` is taken to be referenced rather than closed, which is what Django's
    convention implies but not something the patch states -- a message could close two
    tickets. The spelling check itself is exact.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for index, commit in enumerate(b.commits):
            closing = match.group(1) if (match := _FIXED_PREFIX.match(commit.summary)) else None
            for lineno, line in enumerate(commit.message_lines):
                for hit in _TICKET.finditer(line):
                    if hit.group(1) == closing and lineno == 0:
                        continue
                    targets.append(_target(
                        f"refs:{commit.sha or index}:{lineno}:{hit.start()}", None, None,
                        (line, hit), line.strip()[:120]))
        return targets

    def pass_condition(self, t: Target):
        line, hit = t.payload
        if _REFS_BEFORE.search(line[:hit.start()]):
            return Satisfied(f"`Refs #{hit.group(1)}`")
        return Violated(f"ticket #{hit.group(1)} is referenced without `Refs`: "
                        f"{line.strip()[:70]!r}")


@rule(id="DJANGO-C055", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class BehaviourChangeIsDocumented:
    """Pre-condition: the contribution changes library code, so it adds a feature or
    changes existing behaviour.
    Pass condition: it also changes documentation -- a file under `docs/`, or a docstring in
    the code it touched.

    ``heuristic`` because the antecedent is a proxy. A patch cannot say whether a change is
    a feature, a behaviour change, or an internal refactor that is none of the corpus
    sentence's business; "it changes non-test Python that ships to users" is the closest
    observable, and it over-fires on refactors.

    Docstrings count as documentation on purpose. Django documents public API in `docs/`,
    but a behaviour change described in the docstring of the function that changed has been
    documented, and requiring the `docs/` tree specifically would fail contributions that
    did the right thing in the right place.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = changed_source(b)
        if not source:
            return []
        return [_run_target(b, "docschange", b, f"{len(source)} library file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        docs = [p for p, _ in owned_files(bundle, is_doc_path)]
        if docs:
            return Satisfied(f"documentation changed: {docs[:3]}")
        for path, module in modules(bundle, source_only=True):
            if not module.ok:
                continue
            touched = bundle.files[path].modified_lines
            for docstring in module.docstrings:
                lo, hi = docstring.span()
                if bundle.files[path].is_new or (touched & set(range(lo, hi + 1))):
                    return Satisfied(f"docstring of {docstring.owner} in {path} was written")
        return Violated("the contribution changes library behaviour and touches no "
                        "documentation -- no `docs/` file and no docstring")


@rule(id="DJANGO-C079", category=CATEGORY, ownership="created", heuristic=True,
      reads=("files",))
class ReleaseNoteForNewFeature:
    """Pre-condition: each public top-level function or class the agent newly added to
    library code -- a new feature.
    Pass condition: the contribution adds content to a `docs/releases/A.B.txt` file.

    ``heuristic`` on the antecedent: a new public definition is what a new feature looks
    like in a patch, but so does a public helper extracted during a refactor. The pass
    condition is exact -- the rule names the file, and either it gained lines or it did not.

    The release-note entry is not required to name the definition. Django's release notes
    describe features in prose and frequently never spell the function's name, so demanding
    the name would fail correctly written notes.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [
            _target(f"relnote:{path}:{span[0]}", path, span, (b, name), f"{name} in {path}")
            for path, _module, name, span in new_public_definitions(b)
        ]

    def pass_condition(self, t: Target):
        bundle, name = t.payload
        notes = [(p, c) for p, c in owned_files(bundle, is_release_notes_path)]
        written = [p for p, change in notes if change.added_lines or change.is_new]
        if written:
            return Satisfied(f"release note added in {written[0]}")
        if notes:
            return Violated(f"{notes[0][0]} is in the contribution but gained no lines for "
                            f"the new {name}")
        return Violated(f"{name} is a new public API and no `docs/releases/A.B.txt` entry "
                        f"was added for it")
