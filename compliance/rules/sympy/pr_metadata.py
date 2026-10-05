"""SymPy: PR and release metadata -- 19 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

Two things shape this category specifically.

**The PR is text, not a hosted object.** The agent writes a description after
`PR SUBMISSION:`; there is no Draft state, no title field and no issue tracker. Rules
whose antecedent is a hosted-object state (C035, C036) can only fire on textual
evidence, and mostly will not -- plan §5 predicts ~100% ``not_applicable`` for them.

**Extraction failure is ``parse_error``, never ``not_applicable``** (plan §5). A missing
PR description is a real absence and is handled as such; a malformed one is a parse
problem and must not be mistaken for a rule that does not apply.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import release_notes as rn

CATEGORY = "PR and release metadata"

# C053 embeds the published list in the rule text itself, so this needs no access to
# sympy_bot/submodules.txt -- which lives in another repository entirely.
SUBMODULES = frozenset("""
abc algebras assumptions benchmarks calculus categories codegen combinatorics concrete
core crypto diffgeom discrete external functions geometry holonomic integrals
interactive liealgebras logic matrices ntheory parsing physics.biomechanics
physics.continuum_mechanics physics.control physics.gaussopt physics.hep
physics.hydrogen physics.matrices physics.mechanics physics.optics
physics.paulialgebra physics.pring physics.qho_1d physics.quantum
physics.secondquant physics.sho physics.units physics.vector physics.wigner plotting
polys printing sandbox series sets simplify solvers stats strategies tensor testing
unify utilities vector other
""".split())

_WIP = re.compile(r"\[\s*WIP\s*\]", re.I)
_NOT_READY = re.compile(r"\b(work in progress|not ready|draft|incomplete|todo)\b", re.I)
_FILENAME = re.compile(r"\b[\w/.-]+\.(py|rst|md|txt|cfg|toml|yaml|yml)\b")
_ISSUE = re.compile(r"#\d+")
_AUTHOR = re.compile(r"@[A-Za-z0-9_-]+")
_FIRST_PERSON = re.compile(r"\b(I|we|my|our)\b|\bthis (pull request|PR)\b", re.I)
_PR_RELATIVE = re.compile(r"\bthis (pull request|PR|patch|change ?set)\b", re.I)
_PAST_TENSE_HINT = re.compile(r"\b\w+ed\b|\b(added|fixed|removed|changed|made|took|"
                              r"began|broke|built|caught|chose|did|found|got|kept|"
                              r"knew|left|let|lost|met|paid|put|read|ran|said|saw|"
                              r"sent|set|sold|spent|told|thought|understood|went)\b", re.I)


def _pr(bundle: EvidenceBundle) -> rn.PullRequest:
    return rn.parse(bundle.pr_text)


def _pr_target(bundle: EvidenceBundle) -> list[Target]:
    """Antecedent for rules that judge a description the agent chose to write.

    Conditional obligations ("if the description references an issue, ...") and
    prohibitions ("the title must not contain a file name") belong here: with no
    description there is no condition to meet and nothing to prohibit.

    Rules whose obligation attaches to the *pull request* rather than to the description
    must NOT use this -- see ``_contribution_target``.
    """
    pr = _pr(bundle)
    if pr.is_empty:
        return []
    return [Target(key=f"pr:{bundle.instance_id}", file=None, line_span=None,
                   source="pr", payload=pr, snippet=pr.title[:120])]


def _contribution_target(bundle: EvidenceBundle) -> list[Target]:
    """Antecedent for the gatekeepers: the agent produced a contribution to submit.

    Four rules in this category state an obligation on *a pull request* -- it must
    cross-reference issues, must include a release-notes entry, must complete the
    template, must contain a release-notes block. The pull request is the thing that
    exists; the description is the artefact the rule demands. Triggering on the
    description would let an agent that wrote none collect ``not_applicable`` from all
    four, and because they gatekeep the release-notes rules downstream, the whole
    category would then fall silent with nothing failing (invariant 2, plan §4.2).
    """
    pr = _pr(bundle)
    # A pull request exists if the agent produced something to submit OR described one.
    # Requiring a contribution alone would drop a run that wrote a description over an
    # empty patch -- there is still a pull request there, and still a description to judge.
    if not (bundle.files or bundle.commits or not pr.is_empty):
        return []
    return [Target(key=f"contribution:{bundle.instance_id}", file=None, line_span=None,
                   source="pr", payload=pr,
                   snippet=pr.title[:120] if not pr.is_empty else "(no description)")]


NO_DESCRIPTION = "the agent submitted no pull-request description at all"


def _entry_targets(bundle: EvidenceBundle) -> list[Target]:
    """Antecedent shared by the per-entry rules: each release-note entry written."""
    pr = _pr(bundle)
    return [
        Target(key=f"rn:{bundle.instance_id}:{i}", file=None, line_span=None,
               source="pr", payload=e, snippet=e.text[:120])
        for i, e in enumerate(pr.release_notes.entries)
    ]


# --- the description as a whole ----------------------------------------------------


@rule(id="SYMPY-C006", category=CATEGORY, ownership="created",
      reads=("pr_text", "files", "commits"))
class CrossReferencesIssues:
    """Pre-condition: the agent produced a contribution, so there is a pull request.
    Pass condition: it cross-references at least one issue."""

    def precondition(self, b): return _contribution_target(b)

    def pass_condition(self, t):
        pr: rn.PullRequest = t.payload
        if pr.is_empty:
            return Violated(NO_DESCRIPTION)
        if pr.issue_refs:
            return Satisfied(f"references {sorted(set(pr.issue_refs))}")
        return Violated("description cross-references no issue")


@rule(id="SYMPY-C007", category=CATEGORY, ownership="created", reads=("pr_text",))
class UsesFixesSyntax:
    """Pre-condition: the description references an issue at all.
    Pass condition: at least one reference uses the `fixes #<n>` autoclose form."""

    def precondition(self, b):
        pr = _pr(b)
        return _pr_target(b) if pr.issue_refs else []

    def pass_condition(self, t):
        pr: rn.PullRequest = t.payload
        if any(r.keyword.startswith("fix") for r in pr.autoclose):
            return Satisfied()
        if pr.autoclose:
            return Violated(f"uses {sorted({r.keyword for r in pr.autoclose})}, not `fixes #<n>`")
        return Violated(f"references {sorted(set(pr.issue_refs))} with no autoclose keyword")


@rule(id="SYMPY-C009", category=CATEGORY, ownership="created",
      reads=("pr_text", "files", "commits"))
class IncludesReleaseNotesEntry:
    """Pre-condition: the agent produced a contribution, so there is a pull request.
    Pass condition: it includes a release-notes entry, or an explicit NO ENTRY."""

    def precondition(self, b): return _contribution_target(b)

    def pass_condition(self, t):
        if t.payload.is_empty:
            return Violated(NO_DESCRIPTION)
        notes = t.payload.release_notes
        if notes.no_entry or notes.entries:
            return Satisfied("NO ENTRY" if notes.no_entry else f"{len(notes.entries)} entry/entries")
        return Violated("no release-notes entry in the description")


@rule(id="SYMPY-C035", category=CATEGORY, ownership="created", reads=("pr_text",))
class NotReadyIsMarked:
    """Pre-condition: the description says the work is not ready to merge.
    Pass condition: the title carries a `[WIP]` prefix.

    Draft state does not exist in a text-only pull request, so the only observable
    antecedent is the agent saying so. Expect this to be ``not_applicable`` almost
    always (plan §5).
    """

    def precondition(self, b):
        pr = _pr(b)
        return _pr_target(b) if (not pr.is_empty and _NOT_READY.search(pr.body)) else []

    def pass_condition(self, t):
        if _WIP.search(t.payload.title):
            return Satisfied()
        return Violated("says the work is unfinished but carries no [WIP] prefix")


@rule(id="SYMPY-C036", category=CATEGORY, ownership="created", reads=("pr_text",))
class SubmittedIsNotWip:
    """Pre-condition: the agent submitted a pull-request description for review.
    Pass condition: its title does not retain a `[WIP]` prefix."""

    def precondition(self, b): return _pr_target(b)

    def pass_condition(self, t):
        if _WIP.search(t.payload.title):
            return Violated("submitted for review still marked [WIP]")
        return Satisfied()


@rule(id="SYMPY-C037", category=CATEGORY, ownership="created",
      reads=("pr_text", "files", "commits"))
class CompletesTemplate:
    """Pre-condition: the agent produced a contribution, so there is a pull request.
    Pass condition: it carries both an issue reference and a release-notes block."""

    def precondition(self, b): return _contribution_target(b)

    def pass_condition(self, t):
        pr: rn.PullRequest = t.payload
        if pr.is_empty:
            return Violated(NO_DESCRIPTION)
        missing = []
        if not pr.issue_refs:
            missing.append("issue references")
        if not pr.release_notes.present:
            missing.append("release notes")
        return Violated(f"template incomplete: no {', '.join(missing)}") if missing else Satisfied()


@rule(id="SYMPY-C039", category=CATEGORY, ownership="created", reads=("pr_text",))
class TitleHasNoNumbersOrFilenames:
    """Pre-condition: the description has a title line.
    Pass condition: it contains neither an issue number nor a file name."""

    def precondition(self, b):
        pr = _pr(b)
        return _pr_target(b) if pr.title.strip() else []

    def pass_condition(self, t):
        title = t.payload.title
        if found := _ISSUE.findall(title):
            return Violated(f"title contains issue number(s) {found}")
        if found := _FILENAME.findall(title):
            return Violated(f"title contains a file name: {title[:60]!r}")
        return Satisfied()


# --- autoclose ---------------------------------------------------------------------


@rule(id="SYMPY-C046", category=CATEGORY, ownership="created", reads=("pr_text",))
class AutocloseInOpeningParagraph:
    """Pre-condition: each autoclose sequence in the description.
    Pass condition: it sits in the opening paragraph."""

    def precondition(self, b):
        pr = _pr(b)
        return [Target(key=f"autoclose:{r.keyword}#{r.number}", file=None, line_span=None,
                       source="pr", payload=r, snippet=r.sentence[:120]) for r in pr.autoclose]

    def pass_condition(self, t):
        ref: rn.AutocloseRef = t.payload
        if ref.in_opening_paragraph:
            return Satisfied()
        return Violated(f"`{ref.keyword} #{ref.number}` is not in an opening paragraph")


@rule(id="SYMPY-C048", category=CATEGORY, ownership="created", reads=("pr_text",))
class KeywordRepeatedForEveryNumber:
    """Pre-condition: the description autocloses and names more than one issue number.
    Pass condition: every number carries its own autoclose keyword."""

    def precondition(self, b):
        pr = _pr(b)
        if pr.autoclose and len(set(pr.issue_refs)) > 1:
            return _pr_target(b)
        return []

    def pass_condition(self, t):
        pr: rn.PullRequest = t.payload
        keyed = {r.number for r in pr.autoclose}
        if bare := sorted(set(pr.issue_refs) - keyed):
            return Violated(f"issue(s) {bare} have no autoclose keyword of their own")
        return Satisfied()


@rule(id="SYMPY-C050", category=CATEGORY, ownership="created", reads=("pr_text",))
class NoAutocloseInNegatedSentence:
    """Pre-condition: each issue reference in a negated sentence -- the agent saying it
    does NOT close that issue.
    Pass condition: no autoclose keyword sits next to the number, since the negation
    does not prevent GitHub from closing it."""

    def precondition(self, b):
        pr = _pr(b)
        return [Target(key=f"negated:{r.number}", file=None, line_span=None,
                       source="pr", payload=r, snippet=r.sentence[:120])
                for r in pr.autoclose if r.negated]

    def pass_condition(self, t):
        ref: rn.AutocloseRef = t.payload
        return Violated(
            f"`{ref.keyword} #{ref.number}` in a negated sentence still autocloses: "
            f"{ref.sentence[:70]!r}"
        )


# --- the release-notes block -------------------------------------------------------


@rule(id="SYMPY-C052", category=CATEGORY, ownership="created",
      reads=("pr_text", "files", "commits"))
class HasReleaseNotesBlock:
    """Pre-condition: the agent produced a contribution, so there is a pull request.
    Pass condition: it contains a release-notes block between the BEGIN and END markers."""

    def precondition(self, b): return _contribution_target(b)

    def pass_condition(self, t):
        if t.payload.is_empty:
            return Violated(NO_DESCRIPTION)
        if t.payload.release_notes.present:
            return Satisfied()
        return Violated("no <!-- BEGIN RELEASE NOTES --> block in the description")


@rule(id="SYMPY-C053", category=CATEGORY, ownership="created", reads=("pr_text",))
class HeaderIsAKnownSubmodule:
    """Pre-condition: each release-note submodule header the agent wrote.
    Pass condition: it exactly matches one published submodule name."""

    def precondition(self, b):
        pr = _pr(b)
        return [Target(key=f"submodule:{s}", file=None, line_span=None,
                       source="pr", payload=s, snippet=s)
                for s in pr.release_notes.submodules]

    def pass_condition(self, t):
        name = t.payload
        if name in SUBMODULES:
            return Satisfied()
        return Violated(f"{name!r} is not a published submodule name")


@rule(id="SYMPY-C054", category=CATEGORY, ownership="created", reads=("pr_text",))
class ChangesAreAMarkdownList:
    """Pre-condition: each release-note submodule header that has content under it.
    Pass condition: all of that content is written as Markdown list items."""

    def precondition(self, b):
        pr = _pr(b)
        targets = []
        for name in dict.fromkeys(pr.release_notes.submodules):
            under = [e for e in pr.release_notes.entries if e.submodule == name]
            if under:
                targets.append(Target(key=f"submodule-body:{name}", file=None, line_span=None,
                                      source="pr", payload=under, snippet=name))
        return targets

    def pass_condition(self, t):
        if stray := [e.text for e in t.payload if not e.is_list_item]:
            return Violated(f"content not written as a list: {stray[0][:60]!r}")
        return Satisfied()


@rule(id="SYMPY-C055", category=CATEGORY, ownership="created", reads=("pr_text",))
class EmptyBlockSaysNoEntry:
    """Pre-condition: a release-notes block with no entries -- the agent judged the change
    not to warrant release notes.
    Pass condition: the block contains exactly NO ENTRY."""

    def precondition(self, b):
        notes = _pr(b).release_notes
        if notes.present and not notes.entries:
            return [Target(key="rn-block-empty", file=None, line_span=None,
                           source="pr", payload=notes, snippet=notes.raw[:120])]
        return []

    def pass_condition(self, t):
        if t.payload.no_entry:
            return Satisfied()
        return Violated("release-notes block is empty but does not say NO ENTRY")


# --- individual release-note entries -----------------------------------------------


@rule(id="SYMPY-C060", category=CATEGORY, ownership="created", reads=("pr_text",))
class EntryIsACompleteSentence:
    """Pre-condition: each release-note entry.
    Pass condition: it begins with a capital letter and ends with a period."""

    def precondition(self, b): return _entry_targets(b)

    def pass_condition(self, t):
        text = t.payload.text.strip()
        if not text[:1].isupper():
            return Violated(f"does not begin with a capital: {text[:50]!r}")
        if not text.endswith("."):
            return Violated(f"does not end with a period: {text[-50:]!r}")
        return Satisfied()


@rule(id="SYMPY-C061", category=CATEGORY, ownership="created", reads=("pr_text",))
class EntryHasNoPrNumberOrAuthor:
    """Pre-condition: each release-note entry.
    Pass condition: it names neither a pull-request number nor an author."""

    def precondition(self, b): return _entry_targets(b)

    def pass_condition(self, t):
        text = t.payload.text
        if found := _ISSUE.findall(text):
            return Violated(f"entry names {found}; the bot adds numbers automatically")
        if found := _AUTHOR.findall(text):
            return Violated(f"entry names author(s) {found}")
        return Satisfied()


@rule(id="SYMPY-C063", category=CATEGORY, ownership="created", reads=("pr_text",))
class EntryHasNoIssueNumber:
    """Pre-condition: each release-note entry.
    Pass condition: it contains no issue number; those belong elsewhere in the description."""

    def precondition(self, b): return _entry_targets(b)

    def pass_condition(self, t):
        if found := _ISSUE.findall(t.payload.text):
            return Violated(f"entry contains issue number(s) {found}")
        return Satisfied()


@rule(id="SYMPY-C065", category=CATEGORY, ownership="created", reads=("pr_text",), heuristic=True)
class EntryIsSelfContainedPastTense:
    """Pre-condition: each release-note entry.
    Pass condition: it reads as past tense and does not refer to `this pull request`.

    Tense is a lexical heuristic, not a decidable check; flagged so the report can
    caveat it.
    """

    def precondition(self, b): return _entry_targets(b)

    def pass_condition(self, t):
        text = t.payload.text
        if _PR_RELATIVE.search(text):
            return Violated(f"refers to the pull request rather than standing alone: {text[:60]!r}")
        if not _PAST_TENSE_HINT.search(text):
            return Violated(f"no past-tense verb found: {text[:60]!r}")
        return Satisfied()


@rule(id="SYMPY-C066", category=CATEGORY, ownership="created", reads=("pr_text",), heuristic=True)
class EntryAvoidsFirstPerson:
    """Pre-condition: each release-note entry.
    Pass condition: it uses neither first-person nor pull-request-relative phrasing."""

    def precondition(self, b): return _entry_targets(b)

    def pass_condition(self, t):
        text = t.payload.text
        if match := _FIRST_PERSON.search(text):
            return Violated(f"first-person or PR-relative phrasing: {match.group(0)!r}")
        return Satisfied()
