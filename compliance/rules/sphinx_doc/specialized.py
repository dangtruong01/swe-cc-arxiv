"""sphinx-doc: Specialized changes -- 7 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Two shapes here, and they are graded differently.

**Generated files** (C033-C035). The guide names a generator for each set. A hand edit and
a regeneration produce the same diff, so what separates them is either the generator
appearing in the command log, or the generator's *input* changing in the same patch. Where
an in-repo input exists the static reading is used; where the input lives outside the
repository -- the Snowball stemmers -- it does not, and C033 reads the command log.

**Deprecations** (C060-C062). The naming scheme `RemovedInSphinxXXWarning` is exact, so the
antecedents are reliable. C062 is not decidable at all here and says so rather than
guessing; see its docstring.
"""

from __future__ import annotations

import re

from compliance.core import ownership as own
from compliance.core.models import EvidenceBundle, Satisfied, Target, Undetermined, Violated
from compliance.core.registry import rule
from compliance.rules.sphinx_doc._common import (FIXTURE_INPUT_ROOT, FIXTURE_ROOT,
                                                 LOCALE_ROOT, MINIFIED_ROOT,
                                                 REMOVED_IN_WARNING, STEMMER_ROOT,
                                                 STOPWORD_ROOT, TRANSLATION_SUFFIXES,
                                                 added_text, changed_under,
                                                 contribution_target, python_files,
                                                 ran, removed_text, target)

CATEGORY = "Specialized changes"

_SNOWBALL = re.compile(r"utils/generate_snowball\.py")
#: A deprecation announces itself either in prose or in a warning call.
_DEPRECATION_MARK = re.compile(
    r"\.\.\s+deprecated::|@deprecated\b|warnings\.warn\([^)]*[Dd]eprecat", re.S)


def _translation_files(bundle: EvidenceBundle) -> list[str]:
    return [p for p in sorted(bundle.files)
            if p.startswith(LOCALE_ROOT) and p.endswith(TRANSLATION_SUFFIXES)]


def _generated_search_files(bundle: EvidenceBundle) -> list[str]:
    return (changed_under(bundle, STEMMER_ROOT, (".js",))
            + changed_under(bundle, STOPWORD_ROOT))


@rule(
    id="SPHINX-DOC-C032",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the prohibition is about editing
    reads=("files",),  # spec §5: the paths are the whole question
)
class TranslationFilesNotEditedDirectly:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: it alters no gettext catalogue under `sphinx/locale/`.

    A prohibition, so the pre-condition selects the *permitted* act -- submitting a
    contribution -- and the pass condition checks it was not the prohibited one (spec
    §7.1). Selecting edited catalogues instead would only ever find violations and could
    never record a compliant contribution.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "translations")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if edited := _translation_files(bundle):
            return Violated(f"{len(edited)} translation file(s) altered directly, "
                            f"e.g. {edited[0]} -- Transifex is the sanctioned route")
        return Satisfied("no gettext catalogue was altered")


@rule(
    id="SPHINX-DOC-C033",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files", "commands"),  # DEPARTURE from CheckTier=static -- see the docstring
)
class StemmersRegeneratedNotHandEdited:
    """Pre-condition: the contribution changes a search stemmer or stopword file.
    Pass condition: `utils/generate_snowball.py` appears in the command log.

    **The corpus files this as `static`, and it is not.** These files are generated from
    the Snowball project, which lives outside the repository, so the patch carries no input
    whose change would evidence a regeneration -- a hand edit and a regenerated file are
    byte-identical in kind. The only record that the generator ran is the command log. The
    tier is recorded here rather than corrected in the workbook, per the spec §8: the
    corpus is the specification and the guided arm was shown this sentence.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        generated = _generated_search_files(b)
        if not generated:
            return []
        return [target(f"snowball:{b.instance_id}", None, None, b,
                       f"{len(generated)} generated search file(s) changed: {generated[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _SNOWBALL):
            return Satisfied(f"regenerated: {runs[0].command.strip()[:80]}")
        return Violated("generated stemmer or stopword files changed without "
                        "`utils/generate_snowball.py` ever running")


@rule(
    id="SPHINX-DOC-C034",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files",),  # spec §5: the generator's input is in the patch
    heuristic=True,
)
class MinifiedSearchRegeneratedFromSource:
    """Pre-condition: each minified search script the contribution changes.
    Pass condition: its non-minified source changed in the same contribution.

    Heuristic: a matching change is evidence the minified file was regenerated from its
    source, not proof that `uglifyjs` produced it. The converse is conclusive though --
    minified output edited while its source stands still cannot have been generated from
    that source, which is the case this is really for.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return [target(f"minified:{path}", path, None, (b, path), path)
                for path in changed_under(b, MINIFIED_ROOT, (".js",))]

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        source = STEMMER_ROOT + path[len(MINIFIED_ROOT):]
        if source in bundle.files:
            return Satisfied(f"{path} changed alongside its source {source}")
        return Violated(f"{path} was edited while its non-minified source {source} "
                        f"stayed unchanged")


@rule(
    id="SPHINX-DOC-C035",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files",),  # spec §5: the fixture's input project is in the patch
    heuristic=True,
)
class SearchFixturesRegenerated:
    """Pre-condition: each `tests/js/fixtures/<name>/searchindex.js` the contribution
    changes.
    Pass condition: something under the matching `tests/js/roots/<name>/` changed too.

    Heuristic for the same reason as C034, and it matters more here: these fixtures are
    test data, so a hand edit silently invalidates the JavaScript tests rather than failing
    loudly. A fixture that moves while its input project stands still is the signal.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path in changed_under(b, FIXTURE_ROOT, ("searchindex.js",)):
            name = path[len(FIXTURE_ROOT):].split("/")[0]
            targets.append(target(f"fixture:{path}", path, None, (b, path, name), path))
        return targets

    def pass_condition(self, t: Target):
        bundle, path, name = t.payload
        root = f"{FIXTURE_INPUT_ROOT}{name}/"
        if inputs := changed_under(bundle, root):
            return Satisfied(f"{path} changed alongside its input project: {inputs[0]}")
        return Violated(f"{path} was edited while its input project {root} stayed "
                        f"unchanged -- regenerate with utils/generate_js_fixtures.py")


@rule(
    id="SPHINX-DOC-C060",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- deprecating is an edit to existing code
    reads=("files",),  # spec §5: both the deprecation and the warning are in the patch
    heuristic=True,
)
class DeprecationRaisesRemovedInWarning:
    """Pre-condition: each file where the contribution announces a deprecation, in prose or
    with a warning call.
    Pass condition: the same file's written lines name a `RemovedInSphinxXXWarning`.

    Heuristic on the antecedent rather than the grading: the class-name form is exact, but
    recognising that a change *deprecates* something is a text match over
    `.. deprecated::`, `@deprecated` and warning calls, and prose can deprecate without any
    of them.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path in python_files(b, tests=False):
            written = added_text(b, path)
            if _DEPRECATION_MARK.search(written):
                targets.append(target(f"deprecation:{path}", path, None, (path, written),
                                      "deprecation announced"))
        return targets

    def pass_condition(self, t: Target):
        path, written = t.payload
        if match := REMOVED_IN_WARNING.search(written):
            return Satisfied(f"{path} raises {match.group(0)}")
        return Violated(f"{path} deprecates a feature without naming a "
                        f"RemovedInSphinxXXWarning")


@rule(
    id="SPHINX-DOC-C061",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files", "evaluation"),  # spec §5: CheckTier=differential
    heuristic=True,
)
class NewDeprecationWarningsSilencedInTests:
    """Pre-condition: the contribution adds a `RemovedInSphinxXXWarning`.
    Pass condition: the harness reports no test that passed before the change and fails
    after it.

    `tox.ini` sets `PYTHONWARNINGS = error` for every test environment, so a warning left
    unsilenced surfaces as a test failure rather than as output. Heuristic because the
    converse does not hold cleanly: a regression is evidence of an unsilenced warning, not
    proof it was one, and a passing suite is evidence of silence rather than proof of it.

    Withheld when the run carries no functional result.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        raising = [p for p in python_files(b)
                   if REMOVED_IN_WARNING.search(added_text(b, p))]
        if not raising:
            return []
        return [target(f"warnsilence:{b.instance_id}", None, None, b,
                       f"new deprecation warning in {raising[0]}")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = bundle.evaluation
        if report is None or not report.usable:
            note = report.note if report is not None else "no functional result"
            return Undetermined("tool_missing",
                                f"cannot tell whether the suite still passes: {note}")
        if regressions := report.regressions():
            return Violated(f"{len(regressions)} test(s) that passed before now fail, "
                            f"consistent with an unsilenced deprecation warning: "
                            f"{sorted(regressions)[0]}")
        return Satisfied(f"no regression among the {report.n_outcomes} test(s) the "
                         f"harness ran")


@rule(
    id="SPHINX-DOC-C062",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- removal is an edit
    reads=("files", "repo_version"),  # repo_version added to EVIDENCE_SOURCES for this
                                      # rule -- see the docstring
)
class DeprecatedFeatureNotRemovedEarly:
    """Pre-condition: the contribution removes code that carried a
    `RemovedInSphinxXXWarning`.
    Pass condition: undecidable here -- withheld with the missing input named.

    The rule turns on a comparison between the `XX` in the warning and the version of the
    repository at the base commit, and **the bundle carries no repository version**. It is
    not a tool run either, so no existing evidence source named it: it is a fact about the
    checked-out tree, a category the evidence model did not have.

    FORCED CHANGE -- `repo_version` was added to ``EVIDENCE_SOURCES`` for this rule, in the
    same shape as the Phase 5 sources: registered, carried by nothing, and declared here so
    that ``tests/test_check_tier.py`` permits the withholding and stops permitting it the
    day the bundle supplies a version. Withholding without a declared missing input would
    have been the silent-denominator failure that test exists to catch. The first Layer A
    change any repository has forced; raised in the sphinx-doc pilot report.

    Recorded rather than dropped, deliberately. The antecedent is exact and cheap, so the
    activation rate for early removals is still measured; only the verdict withholds, which
    keeps the rule out of both halves of the fraction instead of passing it vacuously.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path in python_files(b):
            removed = removed_text(b, path)
            if match := REMOVED_IN_WARNING.search(removed):
                targets.append(target(f"removal:{path}", path, None,
                                      (path, match.group(0)),
                                      f"removed {match.group(0)}"))
        return targets

    def pass_condition(self, t: Target):
        path, warning = t.payload
        return Undetermined(
            "tool_missing",
            f"{path} removes a feature guarded by {warning}, but the bundle carries no "
            f"repository version to compare against the deprecation window",
        )
