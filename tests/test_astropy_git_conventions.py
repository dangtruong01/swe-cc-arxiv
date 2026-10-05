"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The no-target case carries most of the weight in this module. All three rules are
conditional -- *when it fixes an issue*, *when it is not ready for CI*, *when the fix is
trivial* -- so the test that matters is the one showing an ordinary commit is not graded
against a token it must not carry.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("astropy/io/fits/header.py", [(10, "    x = 1")])
DOC = make_file("docs/io/fits/index.rst", [(4, "The header is read lazily.")])


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C059 Closes #<issue> on the second or a later line --------------------------------


def test_c059_passes_with_the_reference_in_the_body(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commits=[make_commit("Fix header parsing\n\nCloses #1234")])
    assert verdict("ASTROPY-C059", bundle, corpus).verdict == "pass"


def test_c059_fails_when_the_reference_is_only_on_the_summary_line(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commits=[make_commit("Fix header parsing, closes #1234")])
    row = verdict("ASTROPY-C059", bundle, corpus)
    assert row.verdict == "fail" and "summary line" in row.notes


def test_c059_fails_without_any_reference(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix header parsing")])
    assert verdict("ASTROPY-C059", bundle, corpus).verdict == "fail"


def test_c059_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("ASTROPY-C059", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C067 [ci skip] on commits not ready for CI ----------------------------------------


def test_c067_passes_when_a_wip_commit_carries_the_token(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commits=[make_commit("WIP: header parsing [ci skip]")])
    assert verdict("ASTROPY-C067", bundle, corpus).verdict == "pass"


def test_c067_passes_on_the_skip_ci_spelling(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commits=[make_commit("WIP: header parsing\n\n[skip ci]")])
    assert verdict("ASTROPY-C067", bundle, corpus).verdict == "pass"


def test_c067_fails_when_a_wip_commit_omits_it(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("WIP: header parsing")])
    assert verdict("ASTROPY-C067", bundle, corpus).verdict == "fail"


def test_c067_finds_no_target_for_an_ordinary_commit(corpus):
    """Most commits are ready for CI, so most must not be graded against the token."""
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix header parsing")])
    row = verdict("ASTROPY-C067", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C216 [ci skip] on a trivial documentation fix -------------------------------------


def test_c216_passes_on_a_typo_fix_carrying_the_token(corpus):
    bundle = make_bundle(files=[DOC], commits=[make_commit("Fix a typo [ci skip]")])
    assert verdict("ASTROPY-C216", bundle, corpus).verdict == "pass"


def test_c216_fails_on_a_typo_fix_without_it(corpus):
    bundle = make_bundle(files=[DOC], commits=[make_commit("Fix a typo")])
    assert verdict("ASTROPY-C216", bundle, corpus).verdict == "fail"


def test_c216_finds_no_target_when_code_changed_too(corpus):
    bundle = make_bundle(files=[DOC, SOURCE], commits=[make_commit("Fix a typo")])
    row = verdict("ASTROPY-C216", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c216_finds_no_target_when_the_change_introduces_markup(corpus):
    """CONTRIBUTING exempts a documentation fix only while it carries no special markup."""
    marked = make_file("docs/io/fits/index.rst", [(4, "See :func:`~astropy.io.fits.open`.")])
    bundle = make_bundle(files=[marked], commits=[make_commit("Document open()")])
    row = verdict("ASTROPY-C216", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
