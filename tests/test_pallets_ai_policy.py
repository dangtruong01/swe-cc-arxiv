"""Three cases per rule (spec §9).

**None of these three rules has a satisfying case**, and that is not an omission. All
three are ``by_construction``: pallets' policy closes an AI-generated contribution on
sight and offers no disclosure route out of it, so the subject under test cannot pass any
of them however it behaves. Following §9's alternative triple, what is pinned instead is
that each fails for the stated reason and that its pre-condition still discriminates --
each rule finds no target on a run that did not produce the thing it is about, so the
activation rates measure something real rather than firing on every run.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pallets.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/flask/app.py", [(10, "    return None")])
DOC = make_file("docs/quickstart.rst", [(9, "New prose about the application object.")])


@pytest.fixture(scope="module")
def corpus():
    """pallets' corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pallets"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C004 no pull request generated with an AI tool ------------------------------------


def test_c004_fails_for_a_pull_request_a_model_produced(corpus):
    bundle = make_bundle(files=[SOURCE], pr_text="Fixes the routing path.",
                         model="openrouter/x")
    row = verdict("PALLETS-C004", bundle, corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c004_finds_no_target_when_the_run_produced_nothing(corpus):
    row = verdict("PALLETS-C004", make_bundle(files=[], pr_text=None), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c004_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PALLETS-C004", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C061 the contribution must not look AI-generated ----------------------------------


def test_c061_fails_for_a_contribution_a_model_wrote(corpus):
    row = verdict("PALLETS-C061", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c061_finds_no_target_when_nothing_was_submitted(corpus):
    """Distinct from C004: this rule is about the code, so a run with only a description
    finds nothing to judge here."""
    bundle = make_bundle(files=[], pr_text="A description and no patch.")
    row = verdict("PALLETS-C061", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c061_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PALLETS-C061", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C062 prose must be the contributor's own words ------------------------------------


def test_c062_fails_when_the_run_wrote_prose(corpus):
    bundle = make_bundle(files=[SOURCE, DOC],
                         commits=[make_commit("fix url matching")],
                         pr_text="Fixes the routing path.")
    row = verdict("PALLETS-C062", bundle, corpus)
    assert row.verdict == "fail" and row.by_construction is True
    assert "commit message" in row.notes


def test_c062_finds_no_target_for_a_contribution_carrying_no_prose(corpus):
    """The pre-condition discriminates: a patch with no commit message, no description
    and no documentation gives this rule nothing to judge."""
    bundle = make_bundle(files=[SOURCE], commits=[], pr_text=None)
    row = verdict("PALLETS-C062", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c062_finds_no_target_when_no_model_was_recorded(corpus):
    bundle = make_bundle(files=[DOC], commits=[make_commit("docs: fix")], model="unknown")
    row = verdict("PALLETS-C062", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
