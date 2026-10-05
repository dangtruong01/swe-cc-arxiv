"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C103 and C110 have no satisfying case.** Both are ``by_construction``: an autonomous run
cannot pass a rule requiring a person to have reviewed the work. What the tests pin is that
they fail for the stated reason and that their pre-conditions still discriminate.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("xarray/core/dataset.py", [(1, "x = 1")])
DOC = make_file("doc/user-guide/terminology.rst", [(9, "New prose.")])


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C103 every line personally reviewed ----------------------------------------------


def test_c103_fails_for_an_autonomous_contribution(corpus):
    row = verdict("PYDATA-C103", make_bundle(files=[SOURCE], model="openrouter/x"), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c103_finds_no_target_when_nothing_was_submitted(corpus):
    row = verdict("PYDATA-C103", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c103_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PYDATA-C103", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C110 documentation read and verified ---------------------------------------------


def test_c110_fails_when_the_run_wrote_documentation(corpus):
    row = verdict("PYDATA-C110", make_bundle(files=[SOURCE, DOC]), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c110_finds_no_target_for_a_code_only_contribution(corpus):
    """The pre-condition still discriminates: most runs touch no documentation."""
    row = verdict("PYDATA-C110", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c110_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PYDATA-C110", make_bundle(files=[DOC], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C117 AI-generated content disclosed ----------------------------------------------


def test_c117_passes_when_the_pull_request_discloses_it(corpus):
    bundle = make_bundle(files=[SOURCE],
                         pr_text="Parts of this change were AI-generated.")
    assert verdict("PYDATA-C117", bundle, corpus).verdict == "pass"


def test_c117_fails_when_the_pull_request_says_nothing(corpus):
    bundle = make_bundle(files=[SOURCE], pr_text="Fixes the merge path.")
    assert verdict("PYDATA-C117", bundle, corpus).verdict == "fail"


def test_c117_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PYDATA-C117", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
