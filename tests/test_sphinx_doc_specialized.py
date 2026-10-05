"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C062 has no satisfying case.** It withholds on every target because the bundle carries no
repository version to compare against the deprecation window, so its cases are the withheld
one and the no-target one. See its docstring.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.evaluation import EvalReport
from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.sphinx_doc.specialized  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("sphinx/util/inventory.py", [(1, "x = 1")])


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


def report(pass_to_pass_failures=()):
    return EvalReport(shape="instance", tests_status={
        "FAIL_TO_PASS": {"success": ("tests/test_a.py::test_new",), "failure": ()},
        "PASS_TO_PASS": {"success": ("tests/test_b.py::test_old",),
                         "failure": tuple(pass_to_pass_failures)},
    })


@pytest.fixture(scope="module")
def corpus():
    """sphinx-doc's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("sphinx-doc"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C032 translation catalogues are not edited directly ------------------------------


def test_c032_passes_when_no_catalogue_was_touched(corpus):
    assert verdict("SPHINX-DOC-C032", make_bundle(files=[SOURCE]), corpus).verdict == "pass"


def test_c032_fails_when_a_catalogue_was_edited(corpus):
    po = make_file("sphinx/locale/de/LC_MESSAGES/sphinx.po", [(9, 'msgstr "Suchen"')])
    assert verdict("SPHINX-DOC-C032", make_bundle(files=[SOURCE, po]),
                   corpus).verdict == "fail"


def test_c032_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("SPHINX-DOC-C032", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C033 stemmers are regenerated ----------------------------------------------------


STEMMER = make_file("sphinx/search/non-minified-js/danish-stemmer.js", [(3, "var x;")])


def test_c033_passes_when_the_generator_ran(corpus):
    bundle = make_bundle(files=[STEMMER],
                         commands=cmds("python utils/generate_snowball.py"))
    assert verdict("SPHINX-DOC-C033", bundle, corpus).verdict == "pass"


def test_c033_fails_when_a_generated_file_changed_without_its_generator(corpus):
    bundle = make_bundle(files=[STEMMER], commands=cmds("python -m pytest"))
    assert verdict("SPHINX-DOC-C033", bundle, corpus).verdict == "fail"


def test_c033_finds_no_target_when_no_generated_search_file_changed(corpus):
    row = verdict("SPHINX-DOC-C033", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C034 minified search scripts come from their sources -----------------------------


MINIFIED = make_file("sphinx/search/minified-js/danish-stemmer.js", [(1, "var a=1;")])


def test_c034_passes_when_the_non_minified_source_changed_too(corpus):
    bundle = make_bundle(files=[MINIFIED, STEMMER])
    assert verdict("SPHINX-DOC-C034", bundle, corpus).verdict == "pass"


def test_c034_fails_when_the_minified_file_was_edited_alone(corpus):
    assert verdict("SPHINX-DOC-C034", make_bundle(files=[MINIFIED]),
                   corpus).verdict == "fail"


def test_c034_finds_no_target_without_a_minified_change(corpus):
    row = verdict("SPHINX-DOC-C034", make_bundle(files=[STEMMER]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C035 search fixtures are regenerated ---------------------------------------------


FIXTURE = make_file("tests/js/fixtures/multiterm/searchindex.js", [(1, "Search.setIndex")])
ROOT = make_file("tests/js/roots/multiterm/index.rst", [(4, "New term.")])


def test_c035_passes_when_the_input_project_changed_too(corpus):
    assert verdict("SPHINX-DOC-C035", make_bundle(files=[FIXTURE, ROOT]),
                   corpus).verdict == "pass"


def test_c035_fails_when_the_fixture_was_edited_alone(corpus):
    assert verdict("SPHINX-DOC-C035", make_bundle(files=[FIXTURE]),
                   corpus).verdict == "fail"


def test_c035_finds_no_target_without_a_fixture_change(corpus):
    row = verdict("SPHINX-DOC-C035", make_bundle(files=[ROOT]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C060 a deprecation raises RemovedInSphinxXXWarning -------------------------------


def test_c060_passes_when_the_warning_is_named(corpus):
    deprecating = make_file("sphinx/util/inventory.py", [
        (10, "    .. deprecated:: 8.0"),
        (11, "    warnings.warn('gone', RemovedInSphinx90Warning, stacklevel=2)"),
    ])
    assert verdict("SPHINX-DOC-C060", make_bundle(files=[deprecating]),
                   corpus).verdict == "pass"


def test_c060_fails_when_a_deprecation_names_no_warning(corpus):
    deprecating = make_file("sphinx/util/inventory.py", [(10, "    .. deprecated:: 8.0")])
    assert verdict("SPHINX-DOC-C060", make_bundle(files=[deprecating]),
                   corpus).verdict == "fail"


def test_c060_finds_no_target_without_a_deprecation(corpus):
    row = verdict("SPHINX-DOC-C060", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C061 new deprecation warnings are silenced in the suite --------------------------


RAISING = make_file("sphinx/util/inventory.py", [
    (11, "    warnings.warn('gone', RemovedInSphinx90Warning, stacklevel=2)")])


def test_c061_passes_when_the_suite_still_passes(corpus):
    bundle = make_bundle(files=[RAISING], evaluation=report())
    assert verdict("SPHINX-DOC-C061", bundle, corpus).verdict == "pass"


def test_c061_fails_when_a_previously_passing_test_now_fails(corpus):
    bundle = make_bundle(files=[RAISING],
                         evaluation=report(pass_to_pass_failures=("tests/test_b.py::test_old",)))
    assert verdict("SPHINX-DOC-C061", bundle, corpus).verdict == "fail"


def test_c061_finds_no_target_without_a_new_warning(corpus):
    row = verdict("SPHINX-DOC-C061", make_bundle(files=[SOURCE], evaluation=report()),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C062 a deprecated feature is not removed early -----------------------------------


def test_c062_withholds_because_the_bundle_carries_no_repository_version(corpus):
    removal = make_file(
        "sphinx/util/inventory.py", [],
        removed_lines=("    warnings.warn('gone', RemovedInSphinx90Warning)",),
        deletion_anchors=frozenset({11}))
    row = verdict("SPHINX-DOC-C062", make_bundle(files=[removal]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"
    assert row.n_targets == 1


def test_c062_finds_no_target_when_nothing_deprecated_was_removed(corpus):
    row = verdict("SPHINX-DOC-C062", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
