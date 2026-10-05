"""Django: Specialized changes -- 6 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

**All six are about one thing: deprecating a feature.** Django's `submitting-patches` page
gives a six-item procedure for it -- raise a `RemovedInDjangoXXWarning` at the point of use,
mark the code that must be swept up later, annotate the documentation, write the release
note, record the removal version in the timeline, and re-run the suite under `-Wa`. Each
item is one row of the corpus, and each row therefore fires on **the deprecation**, never
on the artefact it demands. Selecting on the `.. deprecated::` directive would let an agent
that deprecates something and documents none of it collect ``not_applicable`` across the
whole category -- §4.2, and the failure this module is shaped to avoid.

**What counts as "the contribution deprecates a feature".** Not the raise site: C081's whole
job is to ask whether the raise site is there, so an antecedent built from it could only
ever pass. ``_deprecation_signals`` therefore accepts any of five independent faces -- a
`RemovedInDjangoXXWarning` named on any line the agent wrote (in code, docs, notes or a
comment), a `warnings.warn(..., DeprecationWarning)` call in library code, a
`.. deprecated::` directive added to `docs/`, lines added to the deprecation timeline, or
lines added under a *Features deprecated in A.B* heading. Any one establishes the
antecedent; the rules then ask, separately, whether each of the six obligations was met. An
agent that writes only the release note is in the antecedent and fails the other five,
which is the intended reading.

**The removal version is ambiguous and the code refuses to guess.** `RemovedInDjango110Warning`
names Django 1.10, not 11.0, and nothing in the token says which. ``removal_versions`` in
``tests.py`` returns every reading and C088 accepts any of them, because pinning the wrong
one would report a correct timeline entry as missing.

**C082 is the one withheld rule.** *"`python -Wa runtests.py` produces no unintended
warnings"* needs the full suite run under a warning filter **and** the set of warnings that
were already there, since only the difference can be called unintended. Neither is in the
bundle, so it declares ``full_suite_run`` and returns ``tool_missing``. Its pre-condition
still fires on the added warning, so the row records how often the obligation arose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Optional

from compliance.core.models import (
    EvidenceBundle,
    FileChange,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.django.tests import (
    DEPRECATION_TIMELINE,
    REMOVED_IN_WARNING,
    _owned,
    _owns,
    _target,
    doc_lines,
    is_doc_path,
    is_release_notes_path,
    is_source_path,
    modules,
    owned_files,
    removal_versions,
)

CATEGORY = "Specialized changes"

# --- Django deprecation vocabulary ----------------------------------------------------

# The stdlib call Django deprecates through. `warn_explicit` is included because
# `django/utils/deprecation.py` uses it in `RenameMethodsBase`.
WARN_CALLS = frozenset({"warn", "warn_explicit"})
# A plain DeprecationWarning is the near-miss C081 exists to catch: it deprecates the
# feature without telling anyone which release removes it.
GENERIC_WARNINGS = frozenset({"DeprecationWarning", "PendingDeprecationWarning"})

DEPRECATED_DIRECTIVE = re.compile(r"^\s*\.\.\s+deprecated::\s*(?P<version>\S+)?", re.I)
# Django's release notes put deprecations under exactly this heading.
DEPRECATED_HEADING = re.compile(r"^\s*Features deprecated in\s+(?P<version>\d+(?:\.\d+)+)",
                                re.I)
# A section heading in `docs/internals/deprecation.txt` is a bare version number.
TIMELINE_HEADING = re.compile(r"^(?P<version>\d+(?:\.\d+)+)\s*$")
# An reST underline/overline. Used to tell a heading from a line that merely looks like one.
_ADORNMENT = re.compile(r"^([=\-~\"'`^_*+#:.])\1{2,}\s*$")

# A comment marking code to sweep up when the deprecation completes (C085).
WARNING_COMMENT = re.compile(r"#[^\n]*\bRemovedInDjango(\d{2,3})Warning\b")

# An upgrade path tells the reader what to do instead. Lexical, hence the heuristic flags
# on C086 and C087.
UPGRADE_PATH = re.compile(
    r"\buse\b|\binstead\b|\breplaced?\b|\breplacement\b|\bmigrat|\bswitch to\b"
    r"|\bin (?:its|their) place\b|\bsuperseded\b", re.I)


# --- the shared antecedent -------------------------------------------------------------


@dataclass(frozen=True)
class Deprecation:
    """The contribution's deprecation, as the evidence shows it.

    One per contribution rather than one per deprecated name. A patch deprecating three
    aliases owes the documentation one note apiece, but nothing in the diff separates the
    three obligations from each other, and splitting them would multiply one judgement into
    three copies of itself.
    """

    bundle: EvidenceBundle
    signals: tuple[str, ...]
    """Why we believe a deprecation was introduced -- the faces listed in the module
    docstring, in the order found. Carried so a verdict can say what invoked it."""
    tags: tuple[str, ...]
    """The `XX` of every `RemovedInDjangoXXWarning` the agent named. Empty when the
    deprecation was recognised by something other than the warning class."""

    def versions(self) -> tuple[str, ...]:
        """Every release a named warning could be pointing at, both readings kept."""
        out: list[str] = []
        for tag in self.tags:
            out.extend(v for v in removal_versions(tag) if v not in out)
        return tuple(out)


def _authored_lines(bundle: EvidenceBundle) -> Iterator[tuple[str, int, str]]:
    """Every line the agent added to any file in the contribution, in path then line order."""
    for path in sorted(bundle.files):
        change = bundle.files[path]
        if not _owned(change):
            continue
        for lineno, text in change.added_lines:
            yield path, lineno, text


def _warning_tags(bundle: EvidenceBundle) -> tuple[str, ...]:
    """The `XX` of each `RemovedInDjangoXXWarning` the agent wrote, anywhere."""
    tags: list[str] = []
    for _path, _lineno, text in _authored_lines(bundle):
        for match in REMOVED_IN_WARNING.finditer(text):
            if match.group(1) not in tags:
                tags.append(match.group(1))
    return tuple(tags)


def _generic_deprecation_warned(bundle: EvidenceBundle) -> bool:
    """`warnings.warn(..., DeprecationWarning)` in library code the agent wrote.

    Deliberately part of the antecedent and not of any pass condition: it is a deprecation,
    just not the one Django asks for, and C081 is where that distinction is graded.
    """
    for path, module in modules(bundle, source_only=True):
        if not module.ok:
            continue
        for call in module.calls:
            if call.short not in WARN_CALLS or not _owns(bundle, path, call.span()):
                continue
            if _warning_argument(call, GENERIC_WARNINGS):
                return True
    return False


def _warning_argument(call: pa.CallSite, names: frozenset[str]) -> Optional[str]:
    """The warning class passed to a `warn()` call, when it is one of ``names``."""
    for node in (*call.args, *call.keywords.values()):
        dotted = pa.dotted_name(node)
        short = dotted.split(".")[-1] if dotted else ""
        if short in names:
            return short
    return None


def _removed_in_warning_argument(call: pa.CallSite) -> Optional[str]:
    for node in (*call.args, *call.keywords.values()):
        dotted = pa.dotted_name(node)
        if dotted and REMOVED_IN_WARNING.search(dotted.split(".")[-1]):
            return dotted.split(".")[-1]
    return None


def _added_directives(bundle: EvidenceBundle) -> list[tuple[str, int, str]]:
    """(path, line number, version) for each `.. deprecated::` the agent added to `docs/`."""
    out = []
    for path, change in owned_files(bundle, is_doc_path):
        for lineno, text in change.added_lines:
            if match := DEPRECATED_DIRECTIVE.match(text):
                out.append((path, lineno, (match.group("version") or "").strip()))
    return out


def _added_to(bundle: EvidenceBundle, path: str) -> tuple[tuple[int, str], ...]:
    change = bundle.files.get(path)
    if change is None or not _owned(change):
        return ()
    return change.added_lines


def _release_note_deprecation_lines(bundle: EvidenceBundle) -> list[tuple[str, int, str]]:
    """Lines the agent added under a *Features deprecated in A.B* heading.

    Needs the rebuilt file: which section a line sits in cannot be read off a diff hunk.
    Returns nothing when the release-notes file was never reconstructed; the caller that
    cares about the difference reports it separately.
    """
    out = []
    for path, change in owned_files(bundle, is_release_notes_path):
        lines = doc_lines(change)
        if not lines:
            continue
        section = _section_ranges(lines, DEPRECATED_HEADING)
        for lineno, text in change.added_lines:
            if any(lo <= lineno <= hi for lo, hi, _ in section):
                out.append((path, lineno, text))
    return out


def _section_ranges(lines, heading: re.Pattern) -> list[tuple[int, int, str]]:
    """(first line, last line, captured version) for each section opened by ``heading``.

    A section runs from its heading to the line before the next heading of any kind. A
    heading is a text line with an reST adornment directly under it, which is what separates
    `Features deprecated in 5.1` used as a title from the same words in a sentence.
    """
    numbered = list(lines)
    starts: list[tuple[int, str]] = []
    all_heads: list[int] = []
    for index, (lineno, text) in enumerate(numbered):
        if index + 1 >= len(numbered):
            continue
        if not text.strip() or not _ADORNMENT.match(numbered[index + 1][1]):
            continue
        all_heads.append(lineno)
        if match := heading.match(text):
            starts.append((lineno, (match.groupdict().get("version") or "").strip()))
    out = []
    for lineno, version in starts:
        following = [h for h in all_heads if h > lineno]
        end = (following[0] - 1) if following else numbered[-1][0]
        out.append((lineno, end, version))
    return out


def _deprecation_signals(bundle: EvidenceBundle) -> tuple[str, ...]:
    """Every independent face of *"this contribution deprecates a feature"* in the evidence.

    Five of them, and none is the artefact any rule here demands. See the module docstring
    for why that separation is the whole design.
    """
    signals: list[str] = []
    if _warning_tags(bundle):
        signals.append("names a RemovedInDjangoXXWarning")
    if _generic_deprecation_warned(bundle):
        signals.append("raises a DeprecationWarning in library code")
    if _added_directives(bundle):
        signals.append("adds a `.. deprecated::` directive")
    if _added_to(bundle, DEPRECATION_TIMELINE):
        signals.append(f"adds lines to {DEPRECATION_TIMELINE}")
    if _release_note_deprecation_lines(bundle):
        signals.append("adds a `Features deprecated in A.B` release note")
    return tuple(signals)


def _deprecation_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    """The antecedent all six rules share: the contribution deprecates a feature."""
    signals = _deprecation_signals(bundle)
    if not signals:
        return []
    deprecation = Deprecation(bundle, signals, _warning_tags(bundle))
    return [_target(f"{prefix}:{bundle.instance_id}", None, None, deprecation,
                    "; ".join(signals))]


# --- the raise site --------------------------------------------------------------------


@rule(id="DJANGO-C081", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class RaisesRemovedInDjangoWarning:
    """Pre-condition: the contribution deprecates a feature.
    Pass condition: library code the agent wrote raises a `RemovedInDjangoXXWarning` where
    the deprecated feature is used.

    ``heuristic`` for the antecedent, not for the grading. Whether a patch deprecates
    something is read from five circumstantial faces (module docstring), any of which a
    contribution could show for another reason -- a docs page that merely *mentions* a
    warning class already in the tree puts the rule in scope. The pass condition itself is
    exact: either a `warn()` call the agent wrote passes a `RemovedInDjango<NN>Warning`, or
    none does.

    *"At the point the deprecated feature is used"* is graded as *"in library code, not in
    a test"*. The finer reading -- inside the deprecated callable rather than beside it --
    was considered and dropped: a deprecation shim, a `__getattr__` fallback and a property
    setter all raise correctly from somewhere the AST does not associate with the old name,
    so the stricter check would fail Django's own idioms.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "depr-warn")

    def pass_condition(self, t: Target):
        deprecation: Deprecation = t.payload
        bundle = deprecation.bundle
        for path, module in modules(bundle, source_only=True):
            if not module.ok:
                continue
            for call in module.calls:
                if call.short not in WARN_CALLS or not _owns(bundle, path, call.span()):
                    continue
                if name := _removed_in_warning_argument(call):
                    return Satisfied(f"{path}:{call.lineno} raises {name}")
        if _generic_deprecation_warned(bundle):
            return Violated("the deprecation raises a plain DeprecationWarning, not a "
                            "RemovedInDjangoXXWarning naming the removal release")
        return Violated("the contribution deprecates a feature "
                        f"({deprecation.signals[0]}) but no library code it wrote raises a "
                        "RemovedInDjangoXXWarning at the point of use")


@rule(id="DJANGO-C085", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class UnreferencedCodeIsMarked:
    """Pre-condition: each library file a deprecating contribution changes that does not
    itself raise the warning -- code linked to the deprecation with nothing to find it by.
    Pass condition: the agent wrote a `# RemovedInDjangoXXWarning` comment in it.

    The narrowing is what makes the rule mean anything. Firing on every changed file would
    demand a marker comment in the file that already raises the warning, which is the case
    the rule explicitly excludes: that code *is* referenced by the deprecation and will be
    found. Firing on the deprecation alone would ask the contribution as a whole for a
    comment it may legitimately not need.

    ``heuristic``, and honestly so: *"unreferenced"* is a property of the whole tree and the
    bundle carries one patch. A file touched during a deprecation to migrate a call site to
    the new API is not code that must be removed later, and it is selected here. The proxy
    errs towards asking for the comment; a contribution that deprecates inside a single file
    finds no target at all, which is the common and correct case.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not _deprecation_signals(b):
            return []
        raising = _files_raising_the_warning(b)
        targets = []
        for path, change in owned_files(b, is_source_path):
            if path in raising:
                continue
            targets.append(_target(f"depr-mark:{path}", path, None, (path, change), path))
        return targets

    def pass_condition(self, t: Target):
        path, change = t.payload
        for lineno, text in change.added_lines:
            if match := WARNING_COMMENT.search(text):
                return Satisfied(f"{path}:{lineno} {match.group(0).strip()}")
        return Violated(f"{path} is changed as part of a deprecation and raises no warning, "
                        f"but carries no `# RemovedInDjangoXXWarning` comment to find it by "
                        f"when the deprecation completes")


def _files_raising_the_warning(bundle: EvidenceBundle) -> set[str]:
    """Library files where the agent's own code raises a RemovedInDjangoXXWarning."""
    raising = set()
    for path, module in modules(bundle, source_only=True):
        if not module.ok:
            continue
        for call in module.calls:
            if call.short in WARN_CALLS and _owns(bundle, path, call.span()) \
                    and _removed_in_warning_argument(call):
                raising.add(path)
    return raising


# --- the suite under a warning filter: withheld -----------------------------------------


@rule(id="DJANGO-C082", category=CATEGORY, ownership="touched",
      reads=("files", "full_suite_run"))
class NoUnintendedWarningsUnderWa:
    """Pre-condition: the contribution adds a `RemovedInDjangoXXWarning`.
    Pass condition: `python -Wa runtests.py` afterwards produces no warning that was not
    intended.

    Withheld, with the missing input named. Two things are needed and the bundle carries
    neither: the full Django suite run under `-Wa`, which is not the subset the SWE-bench
    harness executes, and the warnings that were already being emitted before the change --
    without them no warning in the output can be called *unintended*. Declaring
    ``full_suite_run`` and returning ``tool_missing`` keeps the row's applicability count
    while refusing to invent the verdict (invariant 6).

    Grading it from the command log was considered and rejected. That is the right shape for
    C074, where the corpus asks the contributor to *verify* something and the trajectory
    records what they did. This sentence asks about the suite's *output*, and an agent that
    ran `runtests.py` on one test module has not produced the evidence the sentence is about.

    The pre-condition is narrower than the rest of the category on purpose: the corpus says
    *"after adding a RemovedInDjangoXXWarning"*, so the warning is genuinely the antecedent
    here and firing on it is not the §4.2 bug.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        tags = _warning_tags(b)
        if not tags:
            return []
        return [_target(f"depr-wa:{b.instance_id}", None, None, tags,
                        f"RemovedInDjango{tags[0]}Warning added")]

    def pass_condition(self, t: Target):
        tags = t.payload
        return Undetermined(
            "tool_missing",
            f"`python -Wa runtests.py` was not run over the full suite, and the warnings "
            f"already emitted before RemovedInDjango{tags[0]}Warning was added are unknown, "
            f"so no warning in its output can be called unintended")


# --- what the deprecation owes the documentation ----------------------------------------


@rule(id="DJANGO-C086", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class DocumentationEntryIsAnnotated:
    """Pre-condition: the contribution deprecates a feature.
    Pass condition: it adds a `.. deprecated:: A.B` directive to `docs/` carrying a version,
    a description, and an upgrade path.

    Graded over every directive the contribution adds, not over the first one found: three
    deprecated entries owe three annotations, and passing on the strength of the best of
    them would let the other two through. A contribution that adds none fails, which is the
    case the antecedent exists to keep in scope.

    ``heuristic`` for the last two clauses. A version is exact -- the directive either
    carries an argument or it does not. A *description* is read as any prose in or under the
    directive, and an *upgrade path* as a phrase telling the reader what to do instead
    (``UPGRADE_PATH``). Both are lexical proxies for something written for a human.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "depr-docs")

    def pass_condition(self, t: Target):
        deprecation: Deprecation = t.payload
        bundle = deprecation.bundle
        directives = _added_directives(bundle)
        if not directives:
            return Violated("the contribution deprecates a feature and adds no "
                            "`.. deprecated:: A.B` annotation to the documentation")
        for path, lineno, version in directives:
            if not version:
                return Violated(f"{path}:{lineno} `.. deprecated::` carries no version")
            body = _directive_body(bundle, path, lineno)
            if not body.strip():
                return Violated(f"{path}:{lineno} `.. deprecated:: {version}` has no "
                                f"description")
            if not UPGRADE_PATH.search(body):
                return Violated(f"{path}:{lineno} `.. deprecated:: {version}` describes the "
                                f"deprecation but gives no upgrade path: {body.strip()[:60]!r}")
        return Satisfied(f"{len(directives)} annotated `.. deprecated::` entr(y/ies)")


def _directive_body(bundle: EvidenceBundle, path: str, lineno: int) -> str:
    """The indented prose belonging to a directive, plus anything on the directive line.

    Read from the rebuilt file when there is one so a description split across the diff's
    context still counts; falls back to the agent's added lines, which is what a
    newly created page gives.
    """
    change = bundle.files.get(path)
    if change is None:
        return ""
    lines = doc_lines(change)
    if not lines:
        lines = tuple(change.added_lines)
    indexed = {n: text for n, text in lines}
    head = indexed.get(lineno, "")
    body = [DEPRECATED_DIRECTIVE.sub("", head, count=1)]
    base = len(head) - len(head.lstrip())
    cursor = lineno + 1
    while cursor in indexed:
        text = indexed[cursor]
        if text.strip() and (len(text) - len(text.lstrip())) <= base:
            break
        body.append(text)
        cursor += 1
    return "\n".join(body)


@rule(id="DJANGO-C087", category=CATEGORY, ownership="touched", heuristic=True,
      reads=("files",))
class ReleaseNotesRecordTheDeprecation:
    """Pre-condition: the contribution deprecates a feature.
    Pass condition: it adds the deprecation and its upgrade path under a
    `Features deprecated in A.B` heading in the release notes.

    Which section a line belongs to is a property of the file, not of the hunk, so the
    release-notes file is read whole and the agent's added lines are then narrowed back to
    the ones inside that section (invariant 5). A release-notes file the harness never
    rebuilt becomes ``Unreadable`` -- the rule applies and cannot be answered, which is not
    the same as it not applying.

    ``heuristic`` for the upgrade path only, on the same lexical proxy as C086. The heading
    itself is exact: Django's release notes spell it one way.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "depr-relnotes")

    def pass_condition(self, t: Target):
        deprecation: Deprecation = t.payload
        bundle = deprecation.bundle
        notes = owned_files(bundle, is_release_notes_path)
        if not notes:
            return Violated("the contribution deprecates a feature and touches no "
                            "`docs/releases/A.B.txt`")
        unreadable = [p for p, change in notes if not doc_lines(change)]
        if unreadable and not _release_note_deprecation_lines(bundle):
            return Undetermined("parse_error",
                                f"{unreadable[0]} was not reconstructed, so which section "
                                f"its added lines sit in cannot be read")
        under_heading = _release_note_deprecation_lines(bundle)
        if not under_heading:
            return Violated(f"{notes[0][0]} gained lines but none under a "
                            f"`Features deprecated in A.B` heading")
        text = "\n".join(t for _p, _n, t in under_heading)
        if not UPGRADE_PATH.search(text):
            return Violated("the `Features deprecated in A.B` entry describes the "
                            f"deprecation but gives no upgrade path: {text.strip()[:70]!r}")
        return Satisfied(f"{len(under_heading)} line(s) under "
                         f"`Features deprecated in` in {under_heading[0][0]}")


@rule(id="DJANGO-C088", category=CATEGORY, ownership="touched", reads=("files",))
class DeprecationTimelineRecordsRemoval:
    """Pre-condition: the contribution deprecates a feature.
    Pass condition: `docs/internals/deprecation.txt` gains an entry under the version that
    will remove it.

    The exact rule of the six. The file is named by the corpus, the heading is a bare
    version number, and the removal version is carried by the warning class the contribution
    added -- so *"under the version it will be removed"* is checkable rather than a proxy.

    `RemovedInDjango110Warning` spells both 1.10 and 11.0 and the token cannot say which,
    so ``removal_versions`` returns both readings and either satisfies the rule. Choosing
    one would report a correct entry as filed under the wrong heading. A deprecation
    recognised by something other than a warning class carries no version at all, and then
    the rule asks only that the file gained an entry.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _deprecation_targets(b, "depr-timeline")

    def pass_condition(self, t: Target):
        deprecation: Deprecation = t.payload
        bundle = deprecation.bundle
        change: Optional[FileChange] = bundle.files.get(DEPRECATION_TIMELINE)
        if change is None or not _owned(change):
            return Violated(f"the contribution deprecates a feature and never touches "
                            f"{DEPRECATION_TIMELINE}")
        added = change.added_lines
        if not added:
            return Violated(f"{DEPRECATION_TIMELINE} is in the contribution but gained "
                            f"no entry")
        expected = deprecation.versions()
        if not expected:
            return Satisfied(f"{len(added)} line(s) added to {DEPRECATION_TIMELINE}; the "
                             f"deprecation names no warning class, so no removal version "
                             f"is checkable")
        lines = doc_lines(change)
        if not lines:
            return Undetermined("parse_error",
                                f"{DEPRECATION_TIMELINE} was not reconstructed, so which "
                                f"version heading its entries sit under cannot be read")
        sections = _section_ranges(lines, TIMELINE_HEADING)
        for lineno, _text in added:
            for lo, hi, version in sections:
                if lo <= lineno <= hi and version in expected:
                    return Satisfied(f"{DEPRECATION_TIMELINE}:{lineno} is filed under "
                                     f"version {version}")
        headings = sorted({v for _lo, _hi, v in sections}) or ["none"]
        return Violated(f"{DEPRECATION_TIMELINE} gained {len(added)} line(s), but none "
                        f"under a heading for the removal version "
                        f"{' or '.join(expected)} (sections present: {headings})")
