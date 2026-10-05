"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C268-C271 all take *a news fragment was added* as their antecedent, so a contribution
without one finds no target in any of them -- that absence is C048's finding, and the
no-target tests below pin the split rather than leaving it to be remembered (§7.5).
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
CODE = make_file("sklearn/linear_model/_base.py", [(10, "x = 1")])
DOC = make_file("doc/modules/svm.rst", [(3, "Support vector machines")])


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def fragment(name="30000.fix.rst", folder="sklearn.linear_model",
             lines=("- Fixed the intercept.",)):
    path = f"doc/whats_new/upcoming_changes/{folder}/{name}"
    return make_file(path, [(n, t) for n, t in enumerate(lines, start=1)], is_new=True)


# --- C042 the PR title is not a bare issue reference ----------------------------------


def test_c042_passes_on_a_descriptive_title(corpus):
    bundle = make_bundle(files=[CODE], pr_text="FIX intercept of LinearRegression")
    assert verdict("SCIKIT-LEARN-C042", bundle, corpus).verdict == "pass"


def test_c042_fails_on_a_bare_fix_reference(corpus):
    bundle = make_bundle(files=[CODE], pr_text="Fix #12345")
    assert verdict("SCIKIT-LEARN-C042", bundle, corpus).verdict == "fail"


def test_c042_finds_no_target_when_no_title_was_recorded(corpus):
    row = verdict("SCIKIT-LEARN-C042", make_bundle(files=[CODE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C048 a changelog fragment is added -----------------------------------------------


def test_c048_passes_when_a_fragment_is_added(corpus):
    bundle = make_bundle(files=[CODE, fragment()])
    assert verdict("SCIKIT-LEARN-C048", bundle, corpus).verdict == "pass"


def test_c048_fails_when_package_code_changes_with_no_fragment(corpus):
    row = verdict("SCIKIT-LEARN-C048", make_bundle(files=[CODE]), corpus)
    assert row.verdict == "fail"


def test_c048_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("SCIKIT-LEARN-C048", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C268 the fragment name -----------------------------------------------------------


def test_c268_passes_on_the_published_shape(corpus):
    bundle = make_bundle(files=[CODE, fragment("30000.fix.rst")])
    assert verdict("SCIKIT-LEARN-C268", bundle, corpus).verdict == "pass"


def test_c268_fails_on_a_free_form_name(corpus):
    bundle = make_bundle(files=[CODE, fragment("intercept-fix.rst")])
    assert verdict("SCIKIT-LEARN-C268", bundle, corpus).verdict == "fail"


def test_c268_finds_no_target_without_a_fragment(corpus):
    row = verdict("SCIKIT-LEARN-C268", make_bundle(files=[CODE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C269 the fragment type -----------------------------------------------------------


def test_c269_passes_on_a_documented_type(corpus):
    bundle = make_bundle(files=[CODE, fragment("30000.enhancement.rst")])
    assert verdict("SCIKIT-LEARN-C269", bundle, corpus).verdict == "pass"


def test_c269_fails_on_an_invented_type(corpus):
    bundle = make_bundle(files=[CODE, fragment("30000.bugfix.rst")])
    assert verdict("SCIKIT-LEARN-C269", bundle, corpus).verdict == "fail"


def test_c269_finds_no_target_when_the_name_carries_no_type(corpus):
    """A name with no type component at all is C268's finding, not this rule's."""
    row = verdict("SCIKIT-LEARN-C269",
                  make_bundle(files=[CODE, fragment("intercept.rst")]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C270 the fragment folder ---------------------------------------------------------


def test_c270_passes_when_the_folder_matches_the_changed_module(corpus):
    bundle = make_bundle(files=[CODE, fragment(folder="sklearn.linear_model")])
    assert verdict("SCIKIT-LEARN-C270", bundle, corpus).verdict == "pass"


def test_c270_fails_when_the_folder_names_another_module(corpus):
    bundle = make_bundle(files=[CODE, fragment(folder="sklearn.tree")])
    assert verdict("SCIKIT-LEARN-C270", bundle, corpus).verdict == "fail"


def test_c270_finds_no_target_when_no_package_module_changed(corpus):
    row = verdict("SCIKIT-LEARN-C270", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C271 the fragment is a single bullet ---------------------------------------------


def test_c271_passes_on_one_bullet(corpus):
    bundle = make_bundle(files=[CODE, fragment()])
    assert verdict("SCIKIT-LEARN-C271", bundle, corpus).verdict == "pass"


def test_c271_fails_on_two_bullets(corpus):
    bundle = make_bundle(files=[CODE, fragment(lines=(
        "- Fixed the intercept.", "- Also fixed the scaler."))])
    assert verdict("SCIKIT-LEARN-C271", bundle, corpus).verdict == "fail"


def test_c271_finds_no_target_without_a_fragment(corpus):
    row = verdict("SCIKIT-LEARN-C271", make_bundle(files=[CODE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
