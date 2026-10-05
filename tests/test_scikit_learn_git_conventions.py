"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The third case is what catches a pre-condition written against the artefact the rule
demands instead of the antecedent that invokes it (§4.2). C054's is a code-only
contribution -- the DOC prefix is not asked of one -- and C055's is a run whose commit
messages carry no marker at all, the marker being optional.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.scikit_learn.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

DOC = make_file("doc/modules/svm.rst", [(10, "Support vector machines")])
CODE = make_file("sklearn/svm/_base.py", [(10, "x = 1")])


@pytest.fixture(scope="module")
def corpus():
    """scikit-learn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("scikit-learn"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C054 a documentation title carries the DOC prefix --------------------------------


def test_c054_passes_on_a_doc_prefixed_title(corpus):
    bundle = make_bundle(files=[DOC], pr_text="DOC clarify the SVM kernel table\n\nBody.")
    assert verdict("SCIKIT-LEARN-C054", bundle, corpus).verdict == "pass"


def test_c054_fails_when_the_title_carries_no_prefix(corpus):
    bundle = make_bundle(files=[DOC], pr_text="Clarify the SVM kernel table")
    assert verdict("SCIKIT-LEARN-C054", bundle, corpus).verdict == "fail"


def test_c054_finds_no_target_for_a_code_contribution(corpus):
    row = verdict("SCIKIT-LEARN-C054", make_bundle(files=[CODE, DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c054_falls_back_to_the_commit_summary(corpus):
    bundle = make_bundle(files=[DOC], commits=[make_commit("DOC fix a typo")])
    assert verdict("SCIKIT-LEARN-C054", bundle, corpus).verdict == "pass"


# --- C055 the CI marker is in the latest commit ---------------------------------------


def test_c055_passes_when_the_latest_commit_carries_the_marker(corpus):
    bundle = make_bundle(files=[CODE], commits=[
        make_commit("FIX kernel cache [doc skip]", sha="bbb2222"),
        make_commit("WIP", sha="aaa1111"),
    ])
    assert verdict("SCIKIT-LEARN-C055", bundle, corpus).verdict == "pass"


def test_c055_fails_when_only_an_earlier_commit_carries_it(corpus):
    bundle = make_bundle(files=[CODE], commits=[
        make_commit("FIX kernel cache", sha="bbb2222"),
        make_commit("WIP [ci skip]", sha="aaa1111"),
    ])
    assert verdict("SCIKIT-LEARN-C055", bundle, corpus).verdict == "fail"


def test_c055_finds_no_target_when_no_commit_uses_a_marker(corpus):
    bundle = make_bundle(files=[CODE], commits=[make_commit("FIX kernel cache")])
    row = verdict("SCIKIT-LEARN-C055", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
