"""Three cases per rule (docs/checker-authoring.md §9) for Django's three shared categories:
Specialized changes, AI-assisted contribution policy, and Code and quality.

One target that satisfies the pass condition, one that violates it, and one input where the
pre-condition finds nothing. The third case is what catches a pre-condition written against
the artefact the rule demands instead of the antecedent that invokes it (§4.2), and it is
the reason the deprecation rules below are all fed a contribution that deprecates something
and documents none of it: every one of them must still fire.

Two of the rules cannot be passed from this bundle at all, and their withheld case is a
first-class test rather than a gap. C082 needs the full suite under `-Wa` plus the warnings
that were already being emitted; C071 and C099 need the complete suite, of which the
SWE-bench harness runs a subset. A rule that failed an agent because we did not run
something would be reporting our missing evidence as the agent's defect (invariant 6).
"""

from __future__ import annotations

import textwrap

import pytest
from conftest import make_bundle, make_file

from compliance.core.evaluation import EvalReport
from compliance.core.lint import Finding, LintReport
from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.django.ai_policy  # noqa: F401  (registers the rules)
import compliance.rules.django.code_quality  # noqa: F401
import compliance.rules.django.specialized  # noqa: F401

RULES = {r.id: r for r in registered()}

SOURCE = "django/utils/text.py"
HELPER = "django/utils/helpers.py"
TIMELINE = "docs/internals/deprecation.txt"
NOTES = "docs/releases/6.0.txt"
REFERENCE = "docs/ref/utils.txt"


@pytest.fixture(scope="module")
def corpus():
    """Django's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("django"))


# --- building bundles ------------------------------------------------------------------


def changed(path, source, authored=None):
    """A changed file carrying its whole post-patch text.

    ``authored`` restricts which lines the agent wrote; left at None it wrote the file. The
    explicit form is how the pre-existing-content tests put text in a file that the agent
    must not be judged for (invariant 5).
    """
    source = textwrap.dedent(source).lstrip("\n")
    lines = source.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    numbers = list(authored) if authored is not None else list(range(1, len(lines) + 1))
    added = [(n, lines[n - 1]) for n in numbers if 1 <= n <= len(lines)]
    return make_file(path, added, head_text=source, is_new=authored is None)


def bundle(*files, commands=(), **overrides):
    return make_bundle(
        files=list(files),
        commands=tuple(Command(index=i, command=c[0], output=c[1] if len(c) > 1 else "")
                       for i, c in enumerate(commands)),
        **overrides,
    )


def verdict(rule_id, b, corpus):
    return run_rule(b, RULES[rule_id], corpus)


def assert_passes(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, f"{rule_id}: vacuous pass, the pre-condition found nothing"
    assert row.verdict == "pass", f"{rule_id}: got {row.verdict} -- {row.notes}"
    return row


def assert_fails(rule_id, b, corpus, phrase):
    row = verdict(rule_id, b, corpus)
    assert row.verdict == "fail", f"{rule_id}: got {row.verdict} -- {row.notes}"
    assert phrase in row.notes, f"{rule_id}: {phrase!r} not in {row.notes!r}"
    return row


def assert_no_targets(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert (row.verdict, row.n_targets) == ("not_applicable", 0), row.notes
    return row


def assert_withheld(rule_id, b, corpus):
    row = verdict(rule_id, b, corpus)
    assert row.n_targets > 0, f"{rule_id}: pre-condition did not fire"
    assert (row.verdict, row.status) == ("not_applicable", "tool_missing"), row.notes
    return row


# --- deprecation fixtures ----------------------------------------------------------------

DEPRECATING_CODE = """
    import warnings

    from django.utils.deprecation import RemovedInDjango60Warning


    def old_helper(value):
        warnings.warn(
            "old_helper() is deprecated; use new_helper() instead.",
            RemovedInDjango60Warning,
            stacklevel=2,
        )
        return new_helper(value)


    def new_helper(value):
        return value
"""

GENERIC_WARNING_CODE = """
    import warnings


    def old_helper(value):
        warnings.warn("old_helper() is deprecated.", DeprecationWarning, stacklevel=2)
        return value
"""

PLAIN_CODE = """
    def slugify(value):
        return value.lower()
"""

ANNOTATED_DOCS = """
    ``old_helper()``
    ----------------

    .. deprecated:: 6.0

        ``old_helper()`` is deprecated. Use ``new_helper()`` instead, which takes the
        same arguments.
"""

UNANNOTATED_DOCS = """
    ``old_helper()``
    ----------------

    .. deprecated:: 6.0
"""

DIRECTIVE_WITHOUT_UPGRADE_PATH = """
    ``old_helper()``
    ----------------

    .. deprecated:: 6.0

        This function is going away in a future release.
"""

RELEASE_NOTES = """
    Django 6.0 release notes
    ========================

    Features deprecated in 6.0
    ==========================

    * ``old_helper()`` is deprecated. Use ``new_helper()`` instead.

    Bugfixes
    ========

    * Fixed a crash.
"""

RELEASE_NOTES_WITHOUT_UPGRADE_PATH = """
    Django 6.0 release notes
    ========================

    Features deprecated in 6.0
    ==========================

    * ``old_helper()`` is deprecated and will be removed.
"""

RELEASE_NOTES_WRONG_SECTION = """
    Django 6.0 release notes
    ========================

    Bugfixes
    ========

    * ``old_helper()`` is deprecated. Use ``new_helper()`` instead.
"""

TIMELINE_TEXT = """
    .. _deprecation-removed-in-6.0:

    6.0
    ---

    See :ref:`deprecated-features-5.1` for more details.

    * ``django.utils.text.old_helper()`` will be removed.

    .. _deprecation-removed-in-5.1:

    5.1
    ---

    * Something else will be removed.
"""


def deprecating(*extra, code=DEPRECATING_CODE, **overrides):
    """A contribution that deprecates `old_helper()`, plus whatever else a test needs."""
    return bundle(changed(SOURCE, code), *extra, **overrides)


# --- DJANGO-C081: the warning is raised at the point of use ------------------------------


def test_c081_passes_when_the_removal_warning_is_raised(corpus):
    assert_passes("DJANGO-C081", deprecating(), corpus)


def test_c081_fails_when_the_deprecation_raises_a_plain_deprecationwarning(corpus):
    """The near-miss the rule exists for: deprecated, but nobody is told which release
    removes it. The antecedent fires on the `warnings.warn(..., DeprecationWarning)` call,
    not on the artefact the rule demands."""
    b = bundle(changed(SOURCE, GENERIC_WARNING_CODE))
    assert_fails("DJANGO-C081", b, corpus, "plain DeprecationWarning")


def test_c081_fails_when_only_the_documentation_deprecates(corpus):
    """§4.2 in action. A contribution that annotates the docs and changes no code is in the
    antecedent -- it deprecates a feature -- and owes a raise site it never wrote."""
    b = bundle(changed(REFERENCE, ANNOTATED_DOCS))
    assert_fails("DJANGO-C081", b, corpus, "no library code it wrote raises")


def test_c081_does_not_fire_on_a_contribution_that_deprecates_nothing(corpus):
    assert_no_targets("DJANGO-C081", bundle(changed(SOURCE, PLAIN_CODE)), corpus)


def test_c081_does_not_fire_on_a_preexisting_warning_the_agent_did_not_write(corpus):
    """Invariant 5. The warning is in the file the agent edited, on lines it never touched,
    so the deprecation is somebody else's and no rule here may judge it."""
    text = textwrap.dedent(DEPRECATING_CODE).lstrip("\n")
    untouched = next(n for n, line in enumerate(text.split("\n"), start=1)
                     if line.strip() == "return value")
    b = bundle(changed(SOURCE, text, authored=[untouched]))
    assert_no_targets("DJANGO-C081", b, corpus)
    assert_no_targets("DJANGO-C086", b, corpus)
    assert_no_targets("DJANGO-C088", b, corpus)


# --- DJANGO-C082: the suite under `-Wa` --------------------------------------------------


def test_c082_is_withheld_because_the_full_suite_was_never_run(corpus):
    """`-Wa` over the full suite, and the warnings already being emitted before the change,
    are both absent from the bundle -- and without the second no warning can be called
    *unintended*. Withheld rather than guessed (invariant 6)."""
    assert_withheld("DJANGO-C082", deprecating(), corpus)


def test_c082_is_still_withheld_when_runtests_was_run(corpus):
    """The command log cannot rescue it. An agent that ran `runtests.py` on one module has
    not produced the full-suite evidence the sentence is about."""
    b = deprecating(commands=[("python -Wa tests/runtests.py utils_tests", "OK")])
    assert_withheld("DJANGO-C082", b, corpus)


def test_c082_does_not_fire_without_a_removal_warning(corpus):
    """Narrower than the rest of the category, and correctly so: the corpus says *after
    adding a RemovedInDjangoXXWarning*, so the warning really is this rule's antecedent."""
    assert_no_targets("DJANGO-C082", bundle(changed(REFERENCE, ANNOTATED_DOCS)), corpus)


# --- DJANGO-C085: code that must be swept up later is marked -----------------------------


MARKED_HELPER = """
    def legacy_path(value):
        # RemovedInDjango60Warning: only reachable from old_helper().
        return value
"""

UNMARKED_HELPER = """
    def legacy_path(value):
        return value
"""


def test_c085_passes_when_the_leftover_code_carries_the_comment(corpus):
    assert_passes("DJANGO-C085", deprecating(changed(HELPER, MARKED_HELPER)), corpus)


def test_c085_fails_when_the_leftover_code_is_unmarked(corpus):
    b = deprecating(changed(HELPER, UNMARKED_HELPER))
    assert_fails("DJANGO-C085", b, corpus, "no `# RemovedInDjangoXXWarning` comment")


def test_c085_does_not_fire_on_the_file_that_raises_the_warning(corpus):
    """The case the rule explicitly excludes: that code *is* referenced by the deprecation
    and will be found when it completes, so it owes no marker."""
    assert_no_targets("DJANGO-C085", deprecating(), corpus)


def test_c085_does_not_fire_without_a_deprecation(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), changed(HELPER, UNMARKED_HELPER))
    assert_no_targets("DJANGO-C085", b, corpus)


# --- DJANGO-C086: the documentation entry is annotated -----------------------------------


def test_c086_passes_on_a_directive_with_version_description_and_upgrade_path(corpus):
    assert_passes("DJANGO-C086", deprecating(changed(REFERENCE, ANNOTATED_DOCS)), corpus)


def test_c086_fails_when_the_deprecation_is_never_annotated(corpus):
    assert_fails("DJANGO-C086", deprecating(), corpus,
                 "adds no `.. deprecated:: A.B` annotation")


def test_c086_fails_on_a_directive_with_no_description(corpus):
    b = deprecating(changed(REFERENCE, UNANNOTATED_DOCS))
    assert_fails("DJANGO-C086", b, corpus, "has no description")


def test_c086_fails_on_a_description_with_no_upgrade_path(corpus):
    b = deprecating(changed(REFERENCE, DIRECTIVE_WITHOUT_UPGRADE_PATH))
    assert_fails("DJANGO-C086", b, corpus, "gives no upgrade path")


def test_c086_does_not_fire_without_a_deprecation(corpus):
    assert_no_targets("DJANGO-C086", bundle(changed(SOURCE, PLAIN_CODE)), corpus)


# --- DJANGO-C087: the release note ------------------------------------------------------


def test_c087_passes_on_an_entry_under_the_deprecation_heading(corpus):
    assert_passes("DJANGO-C087", deprecating(changed(NOTES, RELEASE_NOTES)), corpus)


def test_c087_fails_when_the_release_notes_are_untouched(corpus):
    assert_fails("DJANGO-C087", deprecating(), corpus, "touches no `docs/releases/A.B.txt`")


def test_c087_fails_when_the_entry_sits_outside_the_deprecation_section(corpus):
    """Which section a line belongs to is a property of the file, not of the hunk, which is
    why the release-notes file is read whole."""
    b = deprecating(changed(NOTES, RELEASE_NOTES_WRONG_SECTION))
    assert_fails("DJANGO-C087", b, corpus, "none under a")


def test_c087_fails_when_the_entry_gives_no_upgrade_path(corpus):
    b = deprecating(changed(NOTES, RELEASE_NOTES_WITHOUT_UPGRADE_PATH))
    assert_fails("DJANGO-C087", b, corpus, "no upgrade path")


def test_c087_does_not_fire_without_a_deprecation(corpus):
    assert_no_targets("DJANGO-C087", bundle(changed(SOURCE, PLAIN_CODE)), corpus)


# --- DJANGO-C088: the deprecation timeline ------------------------------------------------


def test_c088_passes_when_the_entry_is_filed_under_the_removal_version(corpus):
    b = deprecating(changed(TIMELINE, TIMELINE_TEXT))
    assert_passes("DJANGO-C088", b, corpus)


def test_c088_fails_when_the_timeline_is_never_touched(corpus):
    assert_fails("DJANGO-C088", deprecating(), corpus, "never touches")


def test_c088_fails_when_the_entry_is_filed_under_the_wrong_version(corpus):
    """`RemovedInDjango60Warning` means the 6.0 heading. An entry under 5.1 records the
    deprecation under a release that will not remove it."""
    text = textwrap.dedent(TIMELINE_TEXT).lstrip("\n")
    wrong_line = next(n for n, line in enumerate(text.split("\n"), start=1)
                      if "Something else" in line)
    b = deprecating(changed(TIMELINE, text, authored=[wrong_line]))
    assert_fails("DJANGO-C088", b, corpus, "none under a heading for the removal version")


def test_c088_accepts_both_readings_of_an_ambiguous_tag(corpus):
    """`RemovedInDjango110Warning` spells both 1.10 and 11.0 and the token cannot say which,
    so either heading satisfies the rule. Pinning one would report a correct entry as
    filed in the wrong place."""
    code = DEPRECATING_CODE.replace("RemovedInDjango60Warning", "RemovedInDjango110Warning")
    timeline = """
        1.10
        ----

        * ``django.utils.text.old_helper()`` will be removed.
    """
    b = deprecating(changed(TIMELINE, timeline), code=code)
    assert_passes("DJANGO-C088", b, corpus)


def test_c088_does_not_fire_without_a_deprecation(corpus):
    assert_no_targets("DJANGO-C088", bundle(changed(SOURCE, PLAIN_CODE)), corpus)


# --- DJANGO-C057: disclosing the AI tool and its use --------------------------------------


DISCLOSURE = ("Fixed #12345 -- Corrected slugify().\n\n"
              "This patch was written by an AI coding assistant, which drafted the fix "
              "and the regression test.")
NO_DISCLOSURE = "Fixed #12345 -- Corrected slugify()."
NAMED_BUT_NOT_EXPLAINED = "Fixed #12345.\n\nClaude.\n"


def test_c057_passes_when_the_pull_request_names_the_tool_and_its_use(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=DISCLOSURE)
    assert_passes("DJANGO-C057", b, corpus)


def test_c057_fails_when_nothing_is_disclosed(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=NO_DISCLOSURE)
    assert_fails("DJANGO-C057", b, corpus, "never discloses")


def test_c057_fails_when_the_tool_is_named_but_not_what_it_did(corpus):
    """Both clauses are graded, because they fail for different reasons: silence is one
    thing, a disclosure that stops short of the sentence is another."""
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=NAMED_BUT_NOT_EXPLAINED)
    assert_fails("DJANGO-C057", b, corpus, "not what it was used for")


def test_c057_does_not_fire_when_the_run_produced_no_contribution(corpus):
    """Nothing to disclose *about*. Firing here would count an empty run as a policy breach
    on top of everything else it already fails."""
    assert_no_targets("DJANGO-C057", bundle(pr_text=DISCLOSURE), corpus)


def test_c057_does_not_fire_when_no_model_is_recorded(corpus):
    """The antecedent is read from the harness's metadata, never inferred from the prose.
    A bundle with no model cannot establish that an AI tool prepared anything."""
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=NO_DISCLOSURE, model="unknown")
    assert_no_targets("DJANGO-C057", b, corpus)


# --- DJANGO-C059: checked against the contribution checklist -------------------------------


def test_c059_passes_when_the_tests_and_a_style_check_were_run(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE),
               commands=[("python tests/runtests.py utils_tests", "OK"),
                         ("flake8 django/utils/text.py", "")])
    assert_passes("DJANGO-C059", b, corpus)


def test_c059_fails_when_no_style_check_was_run(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE),
               commands=[("python tests/runtests.py utils_tests", "OK")])
    assert_fails("DJANGO-C059", b, corpus, "a code style check")


def test_c059_fails_when_nothing_was_verified(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), commands=[("git commit -m 'Fixed it.'", "")])
    assert_fails("DJANGO-C059", b, corpus, "the test suite")


def test_c059_does_not_fire_without_a_contribution(corpus):
    assert_no_targets("DJANGO-C059", bundle(), corpus)


# --- DJANGO-C063: no fabricated APIs -------------------------------------------------------


REAL_API = """
    from django.utils.encoding import force_str


    def slugify(value):
        return force_str(value).lower()
"""

FABRICATED_API = """
    def slugify(value):
        return normalize_unicode_text(value).lower()
"""

PREEXISTING_FABRICATION = """
    def old(value):
        return already_broken(value)


    def slugify(value):
        return value.lower()
"""


def test_c063_passes_when_every_call_resolves(corpus):
    assert_passes("DJANGO-C063", bundle(changed(SOURCE, REAL_API)), corpus)


def test_c063_fails_on_a_helper_nothing_defines(corpus):
    """The characteristic fabrication: a plausible name that raises NameError the first
    time the line runs."""
    assert_fails("DJANGO-C063", bundle(changed(SOURCE, FABRICATED_API)), corpus,
                 "normalize_unicode_text")


def test_c063_does_not_fire_without_python_in_the_contribution(corpus):
    assert_no_targets("DJANGO-C063", bundle(changed(REFERENCE, ANNOTATED_DOCS)), corpus)


def test_c063_does_not_judge_a_call_the_agent_did_not_write(corpus):
    """Invariant 5. The undefined name is in the file the agent edited, on a line it never
    touched -- somebody else's problem, and not this contribution's non-compliance."""
    text = textwrap.dedent(PREEXISTING_FABRICATION).lstrip("\n")
    slug = next(n for n, line in enumerate(text.split("\n"), start=1)
                if "value.lower()" in line)
    b = bundle(changed(SOURCE, text, authored=[slug]))
    row = verdict("DJANGO-C063", b, corpus)
    assert row.verdict != "fail", row.notes


def test_c063_skips_a_module_with_a_star_import(corpus):
    """A name could come from anywhere, so nothing in the module can be called fabricated.
    Under-firing beats putting a wrong accusation in a results table."""
    source = """
        from django.utils.text import *


        def slugify(value):
            return capfirst(value)
    """
    assert_no_targets("DJANGO-C063", bundle(changed(SOURCE, source)), corpus)


# --- DJANGO-C065: self-reporting questionable output ---------------------------------------


SELF_REPORTED = ("Fixed #12345 -- Corrected slugify().\n\n"
                 "I could not run the full test suite because the sandbox has no database, "
                 "so the regression test is unverified.")
NO_SELF_REPORT = "Fixed #12345 -- Corrected slugify().\n\nThis changes the lowercasing."
UNEXPLAINED = "Fixed #12345.\n\nThe patch is untested.\n"


def test_c065_passes_on_a_caveat_with_an_explanation(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=SELF_REPORTED)
    assert_passes("DJANGO-C065", b, corpus)


def test_c065_fails_when_nothing_is_reported(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=NO_SELF_REPORT)
    assert_fails("DJANGO-C065", b, corpus, "reports nothing that may fall short")


def test_c065_fails_when_a_shortcoming_is_flagged_but_not_explained(corpus):
    """*"with an explanation"* is half the sentence, so it is half the grading."""
    b = bundle(changed(SOURCE, PLAIN_CODE), pr_text=UNEXPLAINED)
    assert_fails("DJANGO-C065", b, corpus, "not explained")


def test_c065_does_not_fire_without_a_contribution(corpus):
    assert_no_targets("DJANGO-C065", bundle(pr_text=SELF_REPORTED), corpus)


# --- DJANGO-C069: black, blacken-docs, flake8, isort, zizmor -------------------------------


def report(tool, *, findings=(), available=True):
    if not available:
        return {tool: LintReport("tool_missing", tool=tool, note=f"{tool} is not on PATH")}
    return {tool: LintReport("report", tool=tool, n_findings_base=214,
                             n_findings_head=214 + len(findings),
                             new_findings=tuple(findings))}


def test_c069_passes_when_the_checks_report_nothing_new(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), lint=report("flake8"))
    assert_passes("DJANGO-C069", b, corpus)


def test_c069_fails_on_a_new_finding(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE),
               lint=report("flake8", findings=[Finding(SOURCE, "E501", "line too long")]))
    assert_fails("DJANGO-C069", b, corpus, "E501")


def test_c069_fails_on_a_submitted_file_that_will_not_parse(corpus):
    """Registry 0.2.0: no formatter and no linter accepts a syntax error, so this needs no
    tool run to decide."""
    b = bundle(changed(SOURCE, "def slugify(value)\n    return value\n"))
    assert_fails("DJANGO-C069", b, corpus, "not valid Python")


def test_c069_withholds_when_no_lint_report_exists(corpus):
    """The default state of every stored run: nobody has run the sandbox. A tool we do not
    have is missing evidence, never the agent's violation."""
    assert_withheld("DJANGO-C069", bundle(changed(SOURCE, PLAIN_CODE)), corpus)


def test_c069_withholds_when_the_tool_was_not_installed(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), lint=report("black", available=False))
    assert_withheld("DJANGO-C069", b, corpus)


def test_c069_ignores_preexisting_lint_debt(corpus):
    """Baseline subtraction is the whole point: a 2019 checkout under a 2025 formatter
    reports hundreds of findings the agent did not cause."""
    b = bundle(changed(SOURCE, PLAIN_CODE), lint=report("isort"))
    assert_passes("DJANGO-C069", b, corpus)


def test_c069_does_not_fire_on_a_contribution_the_checks_say_nothing_about(corpus):
    b = bundle(make_file("tests/fixtures/data.json", [(1, "{}")], is_new=True))
    assert_no_targets("DJANGO-C069", b, corpus)


# --- DJANGO-C071 and C099: the full suite --------------------------------------------------


def evaluation(*, regressions=()):
    return EvalReport(
        shape="instance", resolved=not regressions, instance_id="django__django-1",
        tests_status={
            "PASS_TO_PASS": {"success": ("utils_tests.test_text.SlugifyTests.test_ascii",),
                             "failure": tuple(regressions)},
            "FAIL_TO_PASS": {"success": ("utils_tests.test_text.SlugifyTests.test_fix",),
                             "failure": ()},
        },
    )


REGRESSION = "utils_tests.test_html.HtmlTests.test_escape"


def test_c071_fails_on_a_test_that_passed_before_and_fails_now(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), evaluation=evaluation(regressions=[REGRESSION]))
    assert_fails("DJANGO-C071", b, corpus, "passed before the change now")


def test_c071_withholds_when_the_harness_subset_is_clean(corpus):
    """One-sided on purpose. A clean subset does not establish that the *full* suite passes,
    which is what the corpus demands, so the rule never passes vacuously."""
    b = bundle(changed(SOURCE, PLAIN_CODE), evaluation=evaluation())
    assert_withheld("DJANGO-C071", b, corpus)


def test_c071_withholds_when_the_run_carries_no_functional_result(corpus):
    assert_withheld("DJANGO-C071", bundle(changed(SOURCE, PLAIN_CODE)), corpus)


def test_c071_does_not_fire_on_an_empty_contribution(corpus):
    assert_no_targets("DJANGO-C071", bundle(), corpus)


def test_c099_fails_on_a_regression(corpus):
    b = bundle(changed(SOURCE, PLAIN_CODE), evaluation=evaluation(regressions=[REGRESSION]))
    assert_fails("DJANGO-C099", b, corpus, "passed before the change now")


def test_c099_fails_when_documentation_changed_and_was_never_built(corpus):
    """The docs half is decided from the command log, the way C074's is: `make html` either
    ran over the changed documentation or it did not."""
    b = bundle(changed(REFERENCE, ANNOTATED_DOCS), evaluation=evaluation())
    assert_fails("DJANGO-C099", b, corpus, "`make html` was never run")


def test_c099_fails_on_a_noisy_documentation_build(corpus):
    b = bundle(changed(REFERENCE, ANNOTATED_DOCS), evaluation=evaluation(),
               commands=[("make html", "WARNING: undefined label: 'nope'")])
    assert_fails("DJANGO-C099", b, corpus, "did not build cleanly")


def test_c099_withholds_when_both_observable_halves_are_clean(corpus):
    """Same one-sidedness as C071: clearing what is observable is not the same as the full
    suite passing, so the verdict is withheld rather than credited."""
    b = bundle(changed(REFERENCE, ANNOTATED_DOCS), evaluation=evaluation(),
               commands=[("make html", "build succeeded.")])
    assert_withheld("DJANGO-C099", b, corpus)


def test_c099_does_not_fire_on_an_empty_contribution(corpus):
    assert_no_targets("DJANGO-C099", bundle(), corpus)


# --- category-level invariants -------------------------------------------------------------


@pytest.mark.parametrize("category,expected", [
    ("Specialized changes", 6),
    ("AI-assisted contribution policy", 4),
    ("Code and quality", 3),
])
def test_each_category_is_implemented_whole(corpus, category, expected):
    """A partially implemented category would score some rules and not others, making its
    rate meaningless (test_registry.py enforces the same thing pack-wide)."""
    from compliance.core.registry import in_batch

    wanted = {rid for rid in in_batch(corpus) if corpus[rid].shared_category == category}
    got = {r.id for r in registered()
           if r.id.startswith("DJANGO") and r.category == category}
    assert got == wanted
    assert len(wanted) == expected


def test_no_django_rule_in_these_categories_is_by_construction():
    """Unlike SymPy's policy, none of Django's four forbids what an autonomous run *is*.
    An agent can disclose, can run the checklist, can avoid inventing an API, and can flag
    its own shortcomings -- so a failure here is a behavioural result, not a tautology."""
    marked = [r.id for r in registered()
              if r.id.startswith("DJANGO") and r.by_construction]
    assert marked == []


def test_the_withholding_rules_declare_what_they_are_missing():
    """Withholding is invisible by construction, so it is only auditable when the rule names
    the input it lacks (tests/test_check_tier.py)."""
    reads = {r.id: set(r.reads) for r in registered()}
    assert "full_suite_run" in reads["DJANGO-C082"]
    assert "full_suite_run" in reads["DJANGO-C071"]
    assert "full_suite_run" in reads["DJANGO-C099"]
    assert "lint_run" in reads["DJANGO-C069"]
