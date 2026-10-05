"""pallets (flask): Documentation and docstrings -- 10 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

The largest category in the pack, and the one where the corpus legislates prose. Four rows
(C041, C044, C046, C047) are style rules over English sentences, and every one of them
grades **one-sidedly**: they detect the wrong form rather than confirm the right one,
because "written in English" and "uses the serial comma" are broader than any pattern can
confirm. Each says so in its own docstring rather than leaving the reader to infer it from
the heuristic flag.

Three rows (C037, C038, C047) turn on the *purpose* of an edit -- fixing a typo, making
things uniform -- which no diff records. Their pre-conditions approximate it from the shape
of the change, a like-for-like word substitution, and are declared heuristic for that
reason and not for how they grade.

None of the docstring or prose rules carries a newness qualifier, so all are ``touched``
per spec §4.3: editing documentation makes the agent answerable for its form. C088 is the
exception and the pack's only ``enclosing`` row -- what decides its verdict is the
definition the agent modified, not the modification.

**Corpus note (spec §5).** C037, C038, C047 and C085 are filed ``CheckTier=differential``.
None needs a tool run: each is decidable from the patch, which is what the corpus's own
Conclusion says for all four ("read straight off the diff", "compares the touched comment
against the code the diff otherwise changes"). The sentence is followed and the divergence
recorded here rather than by editing the workbook (§0).

**C050 exempts `CHANGES.rst`** (spec §7.5). Read literally, its ban on issue references
"anywhere in the codebase" would forbid what C086 and C053 require the agent to write; the
same sentence names the changelog as one of its two exceptions, so the antecedent is
narrowed there rather than either rule being dropped, and a no-target test pins it.
"""

from __future__ import annotations

import difflib
import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.extractors import rst
from compliance.rules.pallets._common import (CHANGELOG, COMMENT_LINE, DOC_ROOT,
                                              ISSUE_NUMBER, ISSUE_URL, OWN_ORG, PACKAGE,
                                              VERSIONCHANGED, added_lines,
                                              documentation_files, is_documentation,
                                              is_tutorial_path, modules, python_files,
                                              removed_lines, shipped_source, target)

CATEGORY = "Documentation and docstrings"

#: First and second person, as the style section names them. `us` is deliberately absent:
#: as a bare word it collides with "US" and with initialisms, and the two pronouns the
#: sentence actually names are covered by their own forms.
_PERSON = re.compile(
    r"\b(you|your|yours|yourself|yourselves|you'(?:re|ll|ve|d)"
    r"|we|our|ours|ourselves|we'(?:re|ll|ve|d))\b", re.I)

#: Scripts that are not the Latin alphabet English is written in. Positive evidence of
#: another language; the absence of one proves nothing, which is why C044 is one-sided.
_NON_LATIN = re.compile(
    r"[Ѐ-ӿ֐-׿؀-ۿऀ-ॿ"
    r"぀-ヿ㐀-䶿一-鿿가-힯]")

#: `a, b and c` -- items separated by a comma, then a conjunction with no comma before it.
_MISSING_SERIAL = re.compile(r",\s+[^,;:]{1,60}?\s+(and|or)\s+\S")
#: `a, b, and c` -- the form the guide prints.
_SERIAL = re.compile(r",\s+(and|or)\s+\S")

#: A reStructuredText section underline, which is not prose.
_UNDERLINE = re.compile(r"^([-=~^\"'`#*+:.])\1{2,}\s*$")

#: How alike two lines have to be before one is read as an edit of the other.
_LINE_SIMILARITY = 0.75
#: How alike two words have to be before the substitution is read as a typo fix rather
#: than a rewrite.
_WORD_SIMILARITY = 0.6
#: How many documentation files a like-for-like sweep has to touch before C047 reports it.
_SWEEP_FILES = 3


def _prose(bundle: EvidenceBundle, path: str) -> list[tuple[int, str]]:
    """Added lines of a documentation file that are prose rather than markup.

    Directives, field lists, doctest prompts, underlines and indented literal blocks are
    dropped: they are not sentences, and reporting a `.. code-block::` line for its
    punctuation would be a false violation.
    """
    out = []
    for lineno, text in added_lines(bundle, path):
        stripped = text.strip()
        if not stripped or text.startswith(("    ", "\t")):
            continue
        if stripped.startswith(("..", ">>>", ":", "|", "```", "~~~", "==")):
            continue
        if _UNDERLINE.match(stripped):
            continue
        out.append((lineno, text))
    return out


def _substitution(old: str, new: str):
    """The single word that changed between two otherwise identical lines, or None.

    The shape of a typo fix, and the only shape of one this instrument can recognise:
    a same-length line whose words line up except in one place, where the two words are
    near-misses rather than different words.
    """
    old_words, new_words = old.split(), new.split()
    if len(old_words) != len(new_words):
        return None
    differing = [(a, b) for a, b in zip(old_words, new_words) if a != b]
    if len(differing) != 1:
        return None
    before, after = differing[0]
    if difflib.SequenceMatcher(None, before, after).ratio() < _WORD_SIMILARITY:
        return None
    stripped = (before.strip(".,;:()`\"'*"), after.strip(".,;:()`\"'*"))
    if not stripped[0] or not stripped[1] or stripped[0] == stripped[1]:
        return None
    return stripped


def _substitutions(bundle: EvidenceBundle, path: str) -> list[tuple[int, str, str]]:
    """(line, old word, new word) for every like-for-like word swap in one file."""
    removed = list(removed_lines(bundle, path))
    out = []
    for lineno, text in added_lines(bundle, path):
        if not text.strip() or not removed:
            continue
        closest = max(removed, key=lambda r: difflib.SequenceMatcher(None, r, text).ratio())
        if difflib.SequenceMatcher(None, closest, text).ratio() < _LINE_SIMILARITY:
            continue
        if pair := _substitution(closest, text):
            out.append((lineno, pair[0], pair[1]))
    return out


def _still_occurs(bundle: EvidenceBundle, word: str) -> list[str]:
    """Where the old spelling survives, in lines the agent did not write.

    Only the changed files can be searched: the bundle carries the contribution, not the
    checkout, so an occurrence in a file the agent never opened is invisible here. That is
    the reason C037 is heuristic on its pass condition as well as its pre-condition.
    """
    pattern = re.compile(rf"(?<!\w){re.escape(word)}(?!\w)")
    found = []
    for path in sorted(bundle.files):
        change = bundle.files[path]
        if change.head_text is None:
            continue
        for number, text in enumerate(change.head_text.split("\n"), start=1):
            if number in change.authored_lines:
                continue
            if pattern.search(text):
                found.append(f"{path}:{number}")
    return found


@rule(
    id="PALLETS-C032",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- no newness qualifier; editing a docstring makes
                          # the agent answerable for its syntax
    reads=("files",),  # spec §5: the docstring text is in the patch
    heuristic=True,
)
class DocstringsAreReStructuredText:
    """Pre-condition: each docstring the agent wrote or edited.
    Pass condition: it carries no Markdown construct.

    Heuristic on the **pass condition** (§6.2), graded one-sidedly. A docstring of one
    plain sentence is perfectly valid reStructuredText, so confirming the syntax is not
    possible; a Markdown heading, fenced block, inline link or `**bold**` written the
    Markdown way is positive evidence of the syntax the page takes back for docstrings.
    The page permits Markdown for documentation *pages* when myst-parser is installed,
    which is why this rule looks only at docstrings.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b):
            for doc in module.docstrings:
                if not doc.text.strip():
                    continue
                if own.owns_span(b, path, doc.span(), "touched"):
                    out.append(target(f"rst-docstring:{path}:{doc.lineno}", path,
                                      doc.span(), (path, doc),
                                      doc.text.strip().split("\n")[0][:80]))
        return out

    def pass_condition(self, t: Target):
        path, doc = t.payload
        if found := rst.markdown_constructs(doc.lines()):
            lineno, text = found[0]
            return Violated(f"{path}:{lineno} writes the docstring in Markdown, not rST: "
                            f"{text.strip()[:60]}")
        return Satisfied(f"{path}:{doc.lineno} carries no Markdown construct")


@rule(
    id="PALLETS-C037",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the documentation files already existed
    reads=("files",),  # spec §5: both the fix and the residue are in the patch
    heuristic=True,
)
class TypoFixedEverywhereItOccurs:
    """Pre-condition: each documentation file in which the agent replaced one word with a
    near-miss of it, which is the shape of a typo fix.
    Pass condition: the old spelling survives nowhere the agent left untouched.

    Heuristic on **both** layers. On the pre-condition (§6.3), *a typo fix* is a purpose
    and the diff records only a substitution, so a deliberate rewording of one word is
    selected too. On the pass condition (§6.2), "everywhere" can only be searched across
    the files the contribution touches: the bundle carries the patch, not the checkout, so
    an occurrence in a file the agent never opened cannot be seen and the rule passes where
    a maintainer with the tree in front of them might not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            for lineno, before, after in _substitutions(b, path):
                out.append(target(f"typo-everywhere:{path}:{lineno}", path,
                                  (lineno, lineno), (b, path, lineno, before, after),
                                  f"{before} -> {after}"))
        return out

    def pass_condition(self, t: Target):
        bundle, path, lineno, before, after = t.payload
        remaining = _still_occurs(bundle, before)
        if remaining:
            extra = (f" and {len(remaining) - 1} other place(s)"
                     if len(remaining) > 1 else "")
            return Violated(f"`{before}` was corrected to `{after}` at {path}:{lineno} "
                            f"but survives at {remaining[0]}{extra}")
        return Satisfied(f"`{before}` no longer occurs in any file the contribution "
                         f"touches")


@rule(
    id="PALLETS-C038",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the source file already existed
    reads=("files",),  # spec §5: the comment and the code around it are both in the patch
    heuristic=True,
)
class NoDriveByCommentTypoFixes:
    """Pre-condition: each Python file in which the agent replaced one word of a code
    comment with a near-miss of it.
    Pass condition: the agent is also editing that code -- the same file carries a change
    outside its comments.

    The pre-condition is the act the sentence permits under a condition, not the act it
    forbids (§7.1): selecting only comment-only files would find violations and never a
    compliant fix.

    Heuristic on the **pre-condition** (§6.3), twice over. *A typo fix* is a purpose the
    diff does not record, so it is approximated by a like-for-like word substitution; and
    *never appears in the built docs* is approximated by the comment being a `#` comment
    rather than a docstring, since docstrings are what `autodoc` renders and `#` comments
    are what it cannot.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            fixes = [(lineno, before, after)
                     for lineno, before, after in _substitutions(b, path)
                     if COMMENT_LINE.match(dict(added_lines(b, path)).get(lineno, ""))]
            if fixes:
                lineno, before, after = fixes[0]
                out.append(target(f"comment-typo:{path}", path, (lineno, lineno),
                                  (b, path, fixes), f"{before} -> {after}"))
        return out

    def pass_condition(self, t: Target):
        bundle, path, fixes = t.payload
        commented = {lineno for lineno, _, _ in fixes}
        code = [(lineno, text) for lineno, text in added_lines(bundle, path)
                if text.strip() and lineno not in commented
                and not COMMENT_LINE.match(text)]
        if code:
            return Satisfied(f"{path} corrects a comment while its code is being edited "
                             f"({len(code)} non-comment line(s) written)")
        first = fixes[0]
        return Violated(f"{path}:{first[0]} corrects `{first[1]}` to `{first[2]}` in a "
                        f"code comment the built docs never show, in a file whose code "
                        f"is otherwise untouched")


@rule(
    id="PALLETS-C041",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- documentation pages already existed
    reads=("files",),  # spec §5
    heuristic=True,
)
class NoSecondOrFirstPersonOutsideTutorials:
    """Pre-condition: each documentation page outside `docs/tutorial/` that gained prose.
    Pass condition: none of that prose refers to "you" or "we".

    Heuristic on **both** layers. On the pre-condition (§6.3), the exempt genre is
    *tutorials*, which is approximated by the tutorial directory -- a tutorial-style page
    filed elsewhere would be graded. On the pass condition (§6.2), the two pronouns are
    matched with their possessive and contracted forms, and prose is separated from markup
    by shape, so `you` inside a quoted example that is not indented would be reported.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            if is_tutorial_path(path):
                continue
            if prose := _prose(b, path):
                out.append(target(f"no-person:{path}", path, None, (path, prose),
                                  prose[0][1].strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, prose = t.payload
        for lineno, text in prose:
            if match := _PERSON.search(text):
                return Violated(f"{path}:{lineno} addresses the reader as "
                                f"`{match.group(0)}` outside a tutorial: "
                                f"{text.strip()[:60]}")
        return Satisfied(f"{path}: {len(prose)} written line(s) use neither `you` nor "
                         f"`we`")


@rule(
    id="PALLETS-C044",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class DocumentationIsInEnglish:
    """Pre-condition: each documentation page that gained prose.
    Pass condition: that prose is written in the Latin alphabet English uses.

    Heuristic on the **pass condition** (§6.2), and one-sided by construction: a Cyrillic,
    CJK, Devanagari or Arabic character is positive evidence of another language, while
    Latin script is no evidence of English -- French and German would pass. That is the
    honest limit of a check that must not run a language model, and it is stated here
    rather than left for a reader to infer from the flag.

    Tutorials are **not** exempt: the language rule is stated for the documentation as a
    whole, unlike C041's pronoun rule which names its exception.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            if prose := _prose(b, path):
                out.append(target(f"english:{path}", path, None, (path, prose),
                                  prose[0][1].strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, prose = t.payload
        for lineno, text in prose:
            if match := _NON_LATIN.search(text):
                return Violated(f"{path}:{lineno} is not written in English: "
                                f"`{match.group(0)}` in {text.strip()[:60]}")
        return Satisfied(f"{path}: {len(prose)} written line(s) carry no non-Latin script")


@rule(
    id="PALLETS-C046",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files",),  # spec §5
    heuristic=True,
)
class SerialCommaInDocumentationProse:
    """Pre-condition: each written documentation line that lists items separated by commas
    and closed with `and` or `or`.
    Pass condition: a comma precedes that conjunction.

    Heuristic on the **pre-condition** (§6.3). *A list of three or more items* is
    recognised by punctuation, and punctuation is not grammar: "Set the value, and restart
    the server" is two clauses rather than a list, and is selected and reported. Both
    spellings of a list are selected -- with and without the serial comma -- so the rule
    can record a compliant sentence, which selecting only the missing form could not
    (§7.1).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in documentation_files(b):
            for lineno, text in _prose(b, path):
                if _MISSING_SERIAL.search(text) or _SERIAL.search(text):
                    out.append(target(f"serial-comma:{path}:{lineno}", path,
                                      (lineno, lineno), (path, lineno, text),
                                      text.strip()[:80]))
        return out

    def pass_condition(self, t: Target):
        path, lineno, text = t.payload
        if match := _MISSING_SERIAL.search(text):
            return Violated(f"{path}:{lineno} lists items without the serial comma before "
                            f"`{match.group(1)}`: {text.strip()[:70]}")
        return Satisfied(f"{path}:{lineno} uses the serial comma: {text.strip()[:70]}")


@rule(
    id="PALLETS-C047",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the whole contribution is what is submitted
    reads=("files",),  # spec §5: the shape of the diff is the whole question
    heuristic=True,
)
class NoConsistencySweepAcrossExistingDocs:
    """Pre-condition: a contribution that changes documentation.
    Pass condition: it is not a like-for-like spelling or style sweep across pages it has
    no other business in.

    The pre-condition is the permitted act -- contributing to the documentation -- not the
    prohibited one (§7.1).

    Heuristic on the **pass condition** (§6.2). *Purpose* is what the sentence bans, and a
    diff carries none, so the sweep is recognised by its shape: documentation and nothing
    else changed, across three or more pages, with every written line a near-miss
    substitution for a line it replaced and no new content anywhere. A two-page sweep is
    under the threshold and passes; a sweep that also adds a sentence passes. Both err
    towards not reporting, which is the direction §4.5 prefers.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        docs = documentation_files(b)
        if not docs:
            return []
        return [target(f"no-sweep:{b.instance_id}", None, None, (b, docs),
                       f"{len(docs)} documentation file(s) changed")]

    def pass_condition(self, t: Target):
        bundle, docs = t.payload
        others = [p for p in sorted(bundle.files) if p not in docs and p != CHANGELOG]
        if others or len(docs) < _SWEEP_FILES:
            return Satisfied(f"{len(docs)} documentation file(s) changed alongside "
                             f"{len(others)} other file(s) -- not a documentation-wide "
                             f"sweep")
        swept = []
        for path in docs:
            written = [(n, text) for n, text in added_lines(bundle, path) if text.strip()]
            substituted = {n for n, _, _ in _substitutions(bundle, path)}
            if written and all(n in substituted for n, _ in written):
                swept.append(path)
        if len(swept) >= _SWEEP_FILES:
            return Violated(f"{len(swept)} documentation page(s) changed with nothing but "
                            f"like-for-like word substitutions and no new content, which "
                            f"is a consistency sweep: {swept[0]}, {swept[1]}")
        return Satisfied(f"{len(docs)} documentation file(s) changed, {len(swept)} of them "
                         f"by substitution alone -- not a consistency sweep")


@rule(
    id="PALLETS-C050",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- the lines sit in files the agent edited
    reads=("files",),  # spec §5: every line the contribution writes
    heuristic=True,
)
class NoIssueReferencesInTheCodebase:
    """Pre-condition: each file the contribution writes to, other than the changelog.
    Pass condition: none of the lines it wrote carries a GitHub issue or pull-request
    number or link into this project.

    The changelog is excluded because the same sentence names it as one of its two
    exceptions, and because C086 and C053 require the agent to write an entry there
    (§7.5); a no-target test pins that. The other exception -- links to an upstream
    project -- is honoured by matching only links whose owner is this organisation.

    Heuristic on the **pass condition** (§6.2). *Issue number* is recognised by the
    notations GitHub renders, `#1234` and `GH-1234`, so a number named in prose is missed
    and a `#` followed by digits inside a string literal would be reported.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in sorted(b.files):
            if path == CHANGELOG:  # C086/C053 require an entry here -- spec §7.5
                continue
            if written := [(n, text) for n, text in added_lines(b, path) if text.strip()]:
                out.append(target(f"no-issue-ref:{path}", path, None, (path, written),
                                  f"{len(written)} line(s) written"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, text in written:
            if match := ISSUE_NUMBER.search(text):
                return Violated(f"{path}:{lineno} references the issue "
                                f"`{match.group(0)}`: {text.strip()[:60]}")
            if (match := ISSUE_URL.search(text)) and match.group("owner").lower() == OWN_ORG:
                return Violated(f"{path}:{lineno} links a {OWN_ORG} issue or pull "
                                f"request: {match.group(0)}")
        return Satisfied(f"{path}: {len(written)} written line(s) carry no issue or pull "
                         f"request reference")


@rule(
    id="PALLETS-C085",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files",),  # spec §5: both destinations the sentence names are in the patch
    heuristic=True,
)
class DocumentationUpdatedWithTheChange:
    """Pre-condition: the contribution changes shipped source under `src/flask/`.
    Pass condition: it also changes a page under `docs/` or a docstring in the code.

    Heuristic on **both** layers (§6.3, §6.2). The antecedent is *the documentation
    affected by the change*, and which documentation a diff affects is a judgement, so the
    stand-in is a change to shipped source -- a tooling-only or test-only contribution
    finds no target. And *add or update the relevant docs* is graded as either destination
    having been touched at all, not as the documentation matching what changed; the
    sentence names both places and this accepts either, which is the weaker reading it
    licenses.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        source = shipped_source(b)
        if not source:
            return []
        return [target(f"docs-updated:{b.instance_id}", None, None, b,
                       f"{len(source)} shipped source file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        pages = [p for p in sorted(bundle.files) if p.startswith(DOC_ROOT)]
        if pages:
            return Satisfied(f"{len(pages)} documentation page(s) changed with the code: "
                             f"{pages[0]}")
        for path, module in modules(bundle, tests=False):
            for doc in module.docstrings:
                if own.owns_span(bundle, path, doc.span(), "touched"):
                    return Satisfied(f"the docstring at {path}:{doc.lineno} was written "
                                     f"or updated with the code")
        return Violated(f"shipped source changed with nothing under {DOC_ROOT} and no "
                        f"docstring written or updated")


@rule(
    id="PALLETS-C088",
    category=CATEGORY,
    ownership="enclosing",  # spec §4.1 -- what decides the verdict is the definition the
                            # agent modified, not the modification itself
    reads=("files",),  # spec §5: the directive and the change are in the same patch
    heuristic=True,
)
class ChangedBehaviourCarriesVersionchanged:
    """Pre-condition: each public function or method in shipped source whose body the
    agent modified and which existed before the run.
    Pass condition: a `.. versionchanged::` directive was added to its docstring, or to a
    page under `docs/`.

    Heuristic on the **pre-condition** (§6.3). *Changed behaviour of a documented API* is
    approximated by an edit inside an existing public definition: a refactor that changes
    no behaviour is selected and reported, and a behaviour change made entirely in a
    private helper is not selected at all. The alternative -- selecting definitions that
    already carry the directive -- is §7.1 inverted and could never record a violation.

    ``enclosing`` rather than ``touched``: the agent may have edited a single line of the
    body, and what is judged is the whole definition that line sits in.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path, module in modules(b, tests=False):
            if not path.startswith(PACKAGE) or b.files[path].is_new:
                continue
            for func in module.functions:
                if func.name.startswith("_"):
                    continue
                if own.owns_span(b, path, func.span(), "enclosing"):
                    out.append(target(f"versionchanged:{path}:{func.lineno}", path,
                                      func.span(), (b, path, func),
                                      f"def {func.name}"))
        return out

    def pass_condition(self, t: Target):
        bundle, path, func = t.payload
        start, end = func.span()
        for lineno, text in added_lines(bundle, path):
            if start <= lineno <= end and VERSIONCHANGED.match(text):
                return Satisfied(f"{path}:{lineno} documents the change to `{func.name}` "
                                 f"with .. versionchanged::")
        for page in sorted(bundle.files):
            if not page.startswith(DOC_ROOT):
                continue
            for lineno, text in added_lines(bundle, page):
                if VERSIONCHANGED.match(text):
                    return Satisfied(f"{page}:{lineno} adds a .. versionchanged:: "
                                     f"directive for the change to `{func.name}`")
        return Violated(f"{path}:{func.lineno} changes the behaviour of `{func.name}` "
                        f"without a .. versionchanged:: directive in its docstring or "
                        f"under {DOC_ROOT}")
